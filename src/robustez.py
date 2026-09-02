"""
Análise de robustez e sensibilidade do ICP (secção 3.5.7).

Varia, uma de cada vez:
- o limiar mínimo de comprimento da sequência;
- o procedimento de normalização (com / sem normalização intra-processo);
- a regra de agregação (geométrica vs. aritmética vs. MPI).

Para cada especificação alternativa, recalcula o ranking dos processos
*dentro de cada coorte* e reporta Spearman com a especificação principal.
Não se estimam pesos em nenhuma variante.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from src.agregacao import agregar_icp, momentos_mpi_coorte_base
from src.complexidade_lz import complexidade_lz
from src.config import LIMIARES_ROBUSTEZ
from src.entropia import entropia_normalizada, entropia_shannon
from src.normalizacao import (
    alfabeto_global,
    aplicar_minmax_ano_base,
    c_barra,
    estimar_limites_coorte_base,
)
from src.validacao import spearman_seguro


def _minmax_serie(serie: pd.Series, minimo: float, maximo: float) -> pd.Series:
    if minimo == maximo:
        return pd.Series(0.5, index=serie.index)
    return (serie - minimo) / (maximo - minimo)


def construir_especificacao(
    quadro: pd.DataFrame,
    *,
    limiar: int,
    normalizacao_intra: bool,
    regra: str,
    ano_base: int,
    tamanho_alfabeto: int,
) -> pd.Series:
    """
    Devolve uma Series de scores (índice da especificação) alinhada a `quadro`.

    `normalizacao_intra=True` (principal): c̄ pelo Teorema 2 e H̄ de Pielou,
    depois min-max da coorte-base.
    `normalizacao_intra=False`: c(S) e H brutos, só min-max da coorte-base
    — a alternativa pedida na secção 3.5.7.
    """
    dados = quadro.copy()
    dados = dados.loc[dados["n_movimentos"] >= limiar].copy()
    if dados.empty:
        return pd.Series(dtype=float)

    dados["c_s"] = dados["sequencia_codigos"].map(complexidade_lz)
    dados["h_bruta"] = dados["sequencia_codigos"].map(entropia_shannon)
    dados["h_barra"] = dados["sequencia_codigos"].map(entropia_normalizada)

    if normalizacao_intra:
        dados["c_barra"] = [
            c_barra(int(c), int(n), tamanho_alfabeto)
            for c, n in zip(dados["c_s"], dados["n_movimentos"], strict=False)
        ]
        coluna_c, coluna_h = "c_barra", "h_barra"
    else:
        dados["c_barra"] = dados["c_s"].astype(float)
        dados["h_barra"] = dados["h_bruta"].astype(float)
        coluna_c, coluna_h = "c_barra", "h_barra"

    limites = estimar_limites_coorte_base(dados, ano_base)
    dados, _ = aplicar_minmax_ano_base(dados, limites, clipar=True)

    if regra == "geometrica":
        momentos = None
        agregado = agregar_icp(dados, momentos_mpi=momentos)
        score = agregado["icp"]
    elif regra == "aritmetica":
        agregado = agregar_icp(dados)
        score = agregado["icp_aritmetica"]
    elif regra == "mpi":
        momentos = momentos_mpi_coorte_base(dados, ano_base)
        agregado = agregar_icp(dados, momentos_mpi=momentos)
        score = agregado["icp_mpi"]
    else:
        raise ValueError(f"Regra de agregação desconhecida: {regra}")

    score.index = dados.index
    return score


def rankings_por_coorte(score: pd.Series, coortes: pd.Series) -> pd.Series:
    """Ranking *dentro* de cada coorte (1 = maior ICP). Empates: média."""
    quadro = pd.DataFrame({"score": score, "coorte": coortes}).dropna()
    ranking = quadro.groupby("coorte")["score"].rank(ascending=False, method="average")
    return ranking.reindex(score.index)


def tabela_robustez(
    quadro: pd.DataFrame,
    *,
    ano_base: int,
    limiar_principal: int,
    limiares: Sequence[int] | None = None,
) -> pd.DataFrame:
    """
    Spearman entre o ranking da especificação principal e cada alternativa.

    A principal é: limiar da EDA, normalização intra-processo ON, média
    geométrica. Cada linha varia UM factor, mantendo os outros.
    """
    limiares = tuple(limiares or LIMIARES_ROBUSTEZ)
    alfa = alfabeto_global(quadro["sequencia_codigos"])
    principal = construir_especificacao(
        quadro,
        limiar=limiar_principal,
        normalizacao_intra=True,
        regra="geometrica",
        ano_base=ano_base,
        tamanho_alfabeto=alfa,
    )
    rank_principal = rankings_por_coorte(principal, quadro.reindex(principal.index)["coorte"])

    linhas = []

    def avaliar(nome: str, score: pd.Series) -> None:
        comum = rank_principal.index.intersection(score.index)
        if len(comum) < 3:
            rho, p_valor = float("nan"), float("nan")
        else:
            rank_alt = rankings_por_coorte(
                score.loc[comum], quadro.reindex(comum)["coorte"]
            )
            rho, p_valor = spearman_seguro(rank_principal.loc[comum], rank_alt)
        linhas.append(
            {
                "especificação": nome,
                "n_comum": int(len(comum)),
                "rho_spearman_ranking": rho,
                "p": p_valor,
            }
        )

    avaliar(
        "Principal (limiar EDA, intra-processo, geométrica)",
        principal,
    )
    for limiar in limiares:
        if limiar == limiar_principal:
            continue
        score = construir_especificacao(
            quadro, limiar=limiar, normalizacao_intra=True,
            regra="geometrica", ano_base=ano_base, tamanho_alfabeto=alfa,
        )
        avaliar(f"Limiar mínimo = {limiar}", score)

    score_sem_intra = construir_especificacao(
        quadro, limiar=limiar_principal, normalizacao_intra=False,
        regra="geometrica", ano_base=ano_base, tamanho_alfabeto=alfa,
    )
    avaliar("Sem normalização intra-processo (min-max bruto)", score_sem_intra)

    for regra, rotulo in (("aritmetica", "Média aritmética"), ("mpi", "MPI")):
        score = construir_especificacao(
            quadro, limiar=limiar_principal, normalizacao_intra=True,
            regra=regra, ano_base=ano_base, tamanho_alfabeto=alfa,
        )
        avaliar(rotulo, score)

    return pd.DataFrame(linhas)
