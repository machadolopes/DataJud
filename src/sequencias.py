"""
Extração da sequência de movimentos por processo.

Papel no pipeline
-----------------
O ICP é função APENAS da sequência de códigos de movimento (secção 3.4 e
3.5.3). Este módulo ordena os movimentos por `dataHora`, extrai os códigos
(alfabeto simbólico arbitrário) e calcula a duração observada — critério
externo de validação, NUNCA insumo do índice (secção 3.5.8).

Classe, assuntos, grau, tribunal, órgão e formato não entram na sequência.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

import numpy as np
import pandas as pd

from src.config import CODIGOS_MOVIMENTO_TERMINAIS


def analisar_data(valor: Any) -> pd.Timestamp:
    """
    Interpreta as duas formas de data observadas no DataJud TRF2.

    - `dataAjuizamento`: string compacta `YYYYMMDDHHMMSS` (por vezes só data).
    - `movimentos[].dataHora` e `dataHoraUltimaAtualizacao`: ISO-8601.
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return pd.NaT
    if isinstance(valor, pd.Timestamp):
        return valor
    texto = str(valor).strip()
    if not texto or texto.lower() in {"nat", "none", "nan"}:
        return pd.NaT
    if texto.isdigit() and len(texto) >= 8:
        formato = "%Y%m%d%H%M%S" if len(texto) >= 14 else "%Y%m%d"
        return pd.to_datetime(texto[:14] if len(texto) >= 14 else texto[:8],
                              format=formato, errors="coerce")
    return pd.to_datetime(texto, utc=True, errors="coerce")


def codigo_movimento(movimento: dict[str, Any]) -> Any:
    """
    Código TPU do movimento.

    Na extração TRF2 o código está em `codigo`. Noutros tribunais pode
    aparecer só em `movimentoNacional.codigo` — aceitamos ambos.
    """
    codigo = movimento.get("codigo")
    if codigo is None:
        nacional = movimento.get("movimentoNacional")
        if isinstance(nacional, dict):
            codigo = nacional.get("codigo")
    return codigo


def _como_lista_movimentos(movimentos: Any) -> list[Any]:
    """Parquet/pyarrow pode devolver ndarray em vez de list."""
    if movimentos is None:
        return []
    if isinstance(movimentos, float) and pd.isna(movimentos):
        return []
    if isinstance(movimentos, np.ndarray):
        return movimentos.tolist()
    try:
        return list(movimentos)
    except TypeError:
        return []


def ordenar_movimentos(movimentos: Sequence[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Ordena por dataHora (estável se datas empatam: mantém ordem original)."""
    lista = _como_lista_movimentos(movimentos)
    if not lista:
        return []
    validos = [m for m in lista if isinstance(m, dict)]
    datas = [analisar_data(m.get("dataHora")) for m in validos]
    # mergesort é estável: movimentos sem data ficam na posição relativa original
    ordem = sorted(range(len(validos)), key=lambda i: (pd.isna(datas[i]), datas[i]))
    return [validos[i] for i in ordem]


def extrair_sequencia_codigos(movimentos: Sequence[dict[str, Any]] | None) -> list[Any]:
    """Sequência S de códigos (símbolos do alfabeto), na ordem temporal."""
    sequencia = []
    for movimento in ordenar_movimentos(movimentos):
        codigo = codigo_movimento(movimento)
        if codigo is None:
            # Movimento sem código não é um símbolo identificável; omitimos
            # em vez de inventar um token, para não inflacionar o alfabeto.
            continue
        sequencia.append(codigo)
    return sequencia


def data_ultimo_movimento(movimentos: Sequence[dict[str, Any]] | None) -> pd.Timestamp:
    """Data do último movimento com `dataHora` válida (duração observada)."""
    ultima = pd.NaT
    for movimento in ordenar_movimentos(movimentos):
        data = analisar_data(movimento.get("dataHora"))
        if pd.isna(data):
            continue
        if pd.isna(ultima) or data > ultima:
            ultima = data
    return ultima


def processo_encerrado(
    movimentos: Sequence[dict[str, Any]] | None,
    codigos_terminais: Iterable[int] | None = None,
) -> bool:
    """
    Inferência de estado (secção 3.5.1).

    A API pública não traz um campo canónico «situação». Inferimos
    encerramento pela presença de um movimento terminal tabelado
    (baixa definitiva / arquivamento definitivo). Processos em curso
    têm sequência censurada à direita — o ICP continua definido, mas
    a duração observada está truncada.
    """
    terminais = set(codigos_terminais) if codigos_terminais is not None else set(
        CODIGOS_MOVIMENTO_TERMINAIS
    )
    for movimento in _como_lista_movimentos(movimentos):
        if not isinstance(movimento, dict):
            continue
        codigo = codigo_movimento(movimento)
        try:
            if int(codigo) in terminais:
                return True
        except (TypeError, ValueError):
            continue
        nome = str(movimento.get("nome") or "").lower()
        if "baixa definitiva" in nome or "arquivamento definitivo" in nome:
            return True
    return False


def _para_naive(ts: pd.Timestamp) -> pd.Timestamp:
    """Compara ajuizamento (sem fuso) com dataHora ISO (UTC) no mesmo eixo."""
    if pd.isna(ts):
        return ts
    if getattr(ts, "tz", None) is not None:
        return ts.tz_convert("UTC").tz_localize(None)
    return ts


def duracao_observada_dias(
    data_ajuizamento: Any,
    movimentos: Sequence[dict[str, Any]] | None,
) -> float:
    """
    Critério externo de validação (secção 3.5.8): tempo entre o ajuizamento
    e o último movimento observado. NÃO entra no cálculo do ICP.
    """
    inicio = _para_naive(analisar_data(data_ajuizamento))
    fim = _para_naive(data_ultimo_movimento(movimentos))
    if pd.isna(inicio) or pd.isna(fim):
        return float("nan")
    return float((fim - inicio).total_seconds() / 86400.0)


def preparar_quadro_sequencias(quadro: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta colunas de sequência, alfabeto local, duração e estado."""
    resultado = quadro.copy()
    sequencias = resultado["movimentos"].map(extrair_sequencia_codigos)
    resultado["sequencia_codigos"] = sequencias
    resultado["n_movimentos"] = sequencias.map(len)
    resultado["k_alfabeto_processo"] = sequencias.map(lambda s: len(set(s)))
    resultado["data_ultimo_movimento"] = resultado["movimentos"].map(data_ultimo_movimento)
    resultado["duracao_dias"] = [
        duracao_observada_dias(ajuiz, movs)
        for ajuiz, movs in zip(
            resultado["data_ajuizamento"], resultado["movimentos"], strict=False
        )
    ]
    resultado["encerrado"] = resultado["movimentos"].map(processo_encerrado)
    resultado["ano_ajuizamento"] = pd.to_datetime(
        resultado["data_ajuizamento"], errors="coerce"
    ).dt.year
    resultado["coorte"] = resultado["ano_ajuizamento"]
    return resultado


def aplicar_exclusao_listwise(
    quadro: pd.DataFrame,
    limiar_minimo: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Exclusão listwise documentada (secção 3.5.1).

    Ordem: (1) sequência ausente/vazia; (2) abaixo do limiar mínimo de
    movimentos. Devolve o quadro filtrado e uma tabela de fluxo
    n inicial → n excluído por X → n final.
    """
    n_inicial = int(len(quadro))
    sem_sequencia = quadro["n_movimentos"].fillna(0).astype(int) <= 0
    n_sem_sequencia = int(sem_sequencia.sum())
    apos_sequencia = quadro.loc[~sem_sequencia].copy()
    abaixo_limiar = apos_sequencia["n_movimentos"] < limiar_minimo
    n_abaixo = int(abaixo_limiar.sum())
    final = apos_sequencia.loc[~abaixo_limiar].copy().reset_index(drop=True)
    fluxo = pd.DataFrame(
        {
            "etapa": [
                "n inicial",
                "excluídos: sequência de movimentos ausente ou vazia",
                "excluídos: n movimentos < limiar mínimo",
                "n final (amostra do índice)",
            ],
            "n": [
                n_inicial,
                n_sem_sequencia,
                n_abaixo,
                int(len(final)),
            ],
            "n_remanescente": [
                n_inicial,
                n_inicial - n_sem_sequencia,
                n_inicial - n_sem_sequencia - n_abaixo,
                int(len(final)),
            ],
        }
    )
    fluxo["pct_do_inicial"] = 100.0 * fluxo["n_remanescente"] / n_inicial if n_inicial else 0.0
    return final, fluxo
