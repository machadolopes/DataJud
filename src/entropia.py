"""
Entropia de Shannon e normalização intra-processo (equitabilidade de Pielou).

Papel no pipeline
-----------------
Dimensão probabilística do ICP (secção 3.5.3). Captura a heterogeneidade
da distribuição dos *tipos* de movimento na tramitação, independentemente
da ordem (essa vai para c(S)).

H̄ é o índice de equitabilidade de Pielou e opera o mesmo princípio de
normalização por limite teórico que a entropia de sequência normalizada
de Augusto et al. (2022): fica em [0, 1] qualquer que seja o tamanho
bruto da sequência ou a cardinalidade do alfabeto local.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence
from typing import Any, Hashable

import numpy as np

from src.config import BASE_LOG_ENTROPIA

Simbolo = Hashable


def _como_sequencia(sequencia: Any) -> list[Any]:
    """Parquet pode devolver ndarray; `if not seq` rebenta nesses casos."""
    if sequencia is None:
        return []
    if isinstance(sequencia, float) and np.isnan(sequencia):
        return []
    if isinstance(sequencia, np.ndarray):
        return sequencia.tolist()
    try:
        return list(sequencia)
    except TypeError:
        return []


def _log_na_base(valor: float, base: float) -> float:
    if valor <= 0:
        raise ValueError("logaritmo indefinido para valores ≤ 0")
    return math.log(valor) / math.log(base)


def entropia_shannon(
    sequencia: Sequence[Simbolo],
    base: float = BASE_LOG_ENTROPIA,
) -> float:
    """
    H(S) = − Σ p_k log_b p_k, com p_k = frequência relativa do símbolo k.

    Parâmetros
    ----------
    sequencia : sequência de códigos de movimento
    base : base do logaritmo (2 = bits, alinhado à literatura de Shannon)

    Retorno
    -------
    float
        Entropia em [0, log_b(k)]. Sequência vazia → 0 (não NaN).
    """
    sequencia = _como_sequencia(sequencia)
    if not sequencia:
        return 0.0
    n = len(sequencia)
    contagens = Counter(sequencia)
    entropia = 0.0
    for frequencia in contagens.values():
        p_k = frequencia / n
        # p_k > 0 por construção do Counter; 0·log 0 não ocorre.
        entropia -= p_k * _log_na_base(p_k, base)
    return entropia


def entropia_normalizada(
    sequencia: Sequence[Simbolo],
    base: float = BASE_LOG_ENTROPIA,
) -> float:
    """
    H̄ = H / log_b(k), k = número de códigos distintos *neste* processo.

    Caso-limite k = 1
    -----------------
    Só um tipo de movimento → H = 0 e log(k) = 0. Por convenção H̄ = 0,
    não 0/0. Justificação: uma tramitação mono-símbolo não tem
    heterogeneidade de tipos; a equitabilidade é nula. (Secção 3.5.3.)
    """
    sequencia = _como_sequencia(sequencia)
    if not sequencia:
        return 0.0
    k_distintos = len(set(sequencia))
    if k_distintos <= 1:
        return 0.0
    h = entropia_shannon(sequencia, base=base)
    h_max = _log_na_base(k_distintos, base)
    if h_max == 0:
        return 0.0
    # Numericamente H pode exceder h_max por ~1e-15; cortamos a [0, 1].
    return float(min(1.0, max(0.0, h / h_max)))
