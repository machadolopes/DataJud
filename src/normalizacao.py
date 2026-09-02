"""
Normalização de c(S) pelo limite teórico e min-max com ano-base fixo.

Papel no pipeline
-----------------
Secção 3.5.3. Duas operações distintas, nesta ordem:

1. Normalização *intra-processo* de c(S) pelo majorante de Lempel & Ziv
   (1976, Teorema 2), produzindo c̄(S) ∈ [0, 1] comparável entre
   sequências de comprimentos diferentes. H̄ já chega normalizado
   (Pielou) de `entropia.py`.
2. Reescalonamento min-max *entre coortes* com ano-base FIXO: os min/máx
   da primeira coorte são a referência de todas as coortes seguintes.
   Não se recalculam automaticamente (o índice tem de ser comparável
   no tempo). Se uma coorte nova sair do intervalo, emite-se um aviso
   explícito — a decisão de recalcular é do investigador, não do código.

Sem estimação de pesos (secção 3.5.4).
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd


def _log_alfa(valor: float, alfa: int) -> float:
    """log_α(valor). α ≥ 2 (alfabeto de movimentos)."""
    if valor <= 0:
        raise ValueError("log_α indefinido para valores ≤ 0")
    if alfa < 2:
        # Alfabeto degenerado: cai para log2, documentado no aviso.
        alfa = 2
    return math.log(valor) / math.log(alfa)


def limite_teorico_lz(n: int, tamanho_alfabeto: int) -> float:
    """
    Majorante b(n) do Teorema 2 de Lempel & Ziv (1976, p. 78):

        c(S) < n / ((1 − ε_n) · log_α(n))

        ε_n = 2 · (1 + log_α(log_α(α · n))) / log_α(n)

    α é o tamanho do alfabeto de movimentos observado *globalmente*
    (não o k local do processo): o bound deve ser o mesmo para todas
    as sequências da amostra, senão a comparação entre processos
    herdaria a diversidade local duas vezes (já capturada em H̄).

    Logaritmo na base α
    -------------------
    O artigo trata sequências sobre um alfabeto de cardinalidade α e o
    termo dominante é n / log_α(n) (Aboy et al., 2006, retomam esta
    forma). Usar log2 aqui enviesaria c̄ em alfabetos grandes (TPU).

    Sequências curtas
    -----------------
    ε_n → 0 só assintoticamente. Para n pequeno, ε_n pode ser ≥ 1 e o
    denominador (1−ε_n) log_α(n) torna-se não positivo. Nesses casos
    recuamos ao termo dominante b(n) = n / log_α(n), que é a
    normalização usada por Aboy et al. (2006). Não «inventamos» um ε_n.
    """
    if n <= 1:
        return 1.0
    alfa = max(int(tamanho_alfabeto), 2)
    log_n = _log_alfa(n, alfa)
    if log_n <= 0:
        return float(n)

    bound_dominante = n / log_n

    argumento_interno = alfa * n
    try:
        log_alfa_n = _log_alfa(argumento_interno, alfa)
        if log_alfa_n <= 1:
            # log_α(log_α(αn)) indefinido ou negativo → fallback
            return bound_dominante
        log_log = _log_alfa(log_alfa_n, alfa)
    except ValueError:
        return bound_dominante

    epsilon_n = 2.0 * (1.0 + log_log) / log_n
    denominador = (1.0 - epsilon_n) * log_n
    if epsilon_n >= 1.0 or denominador <= 0:
        return bound_dominante
    return n / denominador


def c_barra(c_s: int, n: int, tamanho_alfabeto: int) -> float:
    """c̄(S) = c(S) / b(n), cortado a [0, 1]."""
    if n <= 0:
        return 0.0
    bound = limite_teorico_lz(n, tamanho_alfabeto)
    if bound <= 0:
        return 0.0
    valor = c_s / bound
    # Teorema 2 é um majorante para «quase todas» as sequências; um
    # processo muito irregular pode exceder 1. Cortamos e o chamador
    # conta os cortes (transparência, não silêncio).
    return float(min(1.0, max(0.0, valor)))


@dataclass
class LimitesMinMax:
    """Min/máx da coorte-base, persistidos para coortes futuras."""

    ano_base: int
    c_barra_min: float
    c_barra_max: float
    h_barra_min: float
    h_barra_max: float
    n_processos_base: int
    avisos: list[str] = field(default_factory=list)

    def para_dicionario(self) -> dict:
        return {
            "ano_base": self.ano_base,
            "c_barra_min": self.c_barra_min,
            "c_barra_max": self.c_barra_max,
            "h_barra_min": self.h_barra_min,
            "h_barra_max": self.h_barra_max,
            "n_processos_base": self.n_processos_base,
            "avisos": list(self.avisos),
        }

    @classmethod
    def de_dicionario(cls, dados: dict) -> "LimitesMinMax":
        return cls(
            ano_base=int(dados["ano_base"]),
            c_barra_min=float(dados["c_barra_min"]),
            c_barra_max=float(dados["c_barra_max"]),
            h_barra_min=float(dados["h_barra_min"]),
            h_barra_max=float(dados["h_barra_max"]),
            n_processos_base=int(dados["n_processos_base"]),
            avisos=list(dados.get("avisos") or []),
        )


def estimar_limites_coorte_base(
    quadro: pd.DataFrame,
    ano_base: int,
    coluna_coorte: str = "coorte",
) -> LimitesMinMax:
    """Calcula min/máx de c̄ e H̄ *apenas* na coorte-base."""
    base = quadro.loc[quadro[coluna_coorte] == ano_base]
    if base.empty:
        raise ValueError(
            f"Coorte-base {ano_base} sem processos. "
            "Escolha ANO_BASE presente nos dados (secção 3.5.3)."
        )
    c_min = float(base["c_barra"].min())
    c_max = float(base["c_barra"].max())
    h_min = float(base["h_barra"].min())
    h_max = float(base["h_barra"].max())
    avisos: list[str] = []
    if math.isclose(c_min, c_max):
        avisos.append(
            "c̄ constante na coorte-base: min-max degenerado; "
            "c̄_mm será 0.5 para todos os processos."
        )
    if math.isclose(h_min, h_max):
        avisos.append(
            "H̄ constante na coorte-base: min-max degenerado; "
            "H̄_mm será 0.5 para todos os processos."
        )
    return LimitesMinMax(
        ano_base=ano_base,
        c_barra_min=c_min,
        c_barra_max=c_max,
        h_barra_min=h_min,
        h_barra_max=h_max,
        n_processos_base=int(len(base)),
        avisos=avisos,
    )


def _minmax(valor: float, minimo: float, maximo: float) -> float:
    if math.isclose(minimo, maximo):
        return 0.5
    return (valor - minimo) / (maximo - minimo)


def aplicar_minmax_ano_base(
    quadro: pd.DataFrame,
    limites: LimitesMinMax,
    clipar: bool = True,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Reescala c̄ e H̄ com os min/máx da coorte-base.

    Se algum valor de uma coorte nova cair fora de [min, máx] da base,
    emite aviso explícito (print + lista). NÃO recalcula os limites.
    Por omissão clipa a [0, 1] depois do aviso para a média geométrica
    permanecer definida; o investigador pode desligar o clip.
    """
    resultado = quadro.copy()
    avisos: list[str] = list(limites.avisos)

    c_vals = resultado["c_barra"].astype(float)
    h_vals = resultado["h_barra"].astype(float)

    fora_c_baixo = int((c_vals < limites.c_barra_min).sum())
    fora_c_alto = int((c_vals > limites.c_barra_max).sum())
    fora_h_baixo = int((h_vals < limites.h_barra_min).sum())
    fora_h_alto = int((h_vals > limites.h_barra_max).sum())
    n_fora = fora_c_baixo + fora_c_alto + fora_h_baixo + fora_h_alto
    if n_fora:
        mensagem = (
            "AVISO (secção 3.5.3) — valores fora do intervalo da coorte-base "
            f"{limites.ano_base}. NÃO recálculo automático dos min/máx. "
            f"c̄ abaixo do min: {fora_c_baixo}; c̄ acima do máx: {fora_c_alto}; "
            f"H̄ abaixo do min: {fora_h_baixo}; H̄ acima do máx: {fora_h_alto}. "
            "A decisão de recalcular os limites é do investigador."
        )
        avisos.append(mensagem)
        warnings.warn(mensagem, UserWarning, stacklevel=2)
        print(mensagem)

    c_mm = c_vals.map(lambda v: _minmax(v, limites.c_barra_min, limites.c_barra_max))
    h_mm = h_vals.map(lambda v: _minmax(v, limites.h_barra_min, limites.h_barra_max))
    if clipar:
        c_mm = c_mm.clip(0.0, 1.0)
        h_mm = h_mm.clip(0.0, 1.0)
    resultado["c_barra_mm"] = c_mm
    resultado["h_barra_mm"] = h_mm
    resultado["n_fora_intervalo_base"] = n_fora
    return resultado, avisos


def alfabeto_global(sequencias: pd.Series) -> int:
    """Cardinalidade do alfabeto de códigos em *toda* a amostra (α do Teorema 2)."""
    simbolos: set = set()
    for sequencia in sequencias:
        lista = [] if sequencia is None else (
            sequencia.tolist() if hasattr(sequencia, "tolist") and not isinstance(sequencia, (list, tuple, str))
            else list(sequencia)
        )
        simbolos.update(lista)
    return max(len(simbolos), 1)
