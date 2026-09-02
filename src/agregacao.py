"""
Agregação das duas dimensões no ICP.

Papel no pipeline
-----------------
Secção 3.5.4. Sem estimação de pesos (nem PCA, nem entropia-como-peso,
nem Benefit of the Doubt). As duas dimensões, já em [0, 1], combinam-se
por média geométrica — agregação *não compensatória*: um processo
extremo numa dimensão e nulo na outra não é «salvo» pela dimensão alta.

    ICP = √(c̄(S) · H̄)

Alternativas (média aritmética e MPI) existem *apenas* para a análise
de robustez (secção 3.5.7) e não substituem a especificação principal.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def media_geometrica(c_barra: float, h_barra: float) -> float:
    """
    ICP principal. Se qualquer dimensão é 0, o produto é 0 — é o ponto
    da não-compensação, não um bug.
    """
    if c_barra < 0 or h_barra < 0:
        raise ValueError("Dimensões do ICP devem ser ≥ 0 após normalização.")
    return float(np.sqrt(c_barra * h_barra))


def media_aritmetica(c_barra: float, h_barra: float) -> float:
    """Agregação compensatória, só para robustez (secção 3.5.7)."""
    return float((c_barra + h_barra) / 2.0)


def mazziotta_pareto_par(
    c_barra: float,
    h_barra: float,
    media_c: float,
    desvio_c: float,
    media_h: float,
    desvio_h: float,
) -> float:
    """
    Índice Mazziotta-Pareto (MPI) de duas dimensões.

    Mazziotta & Pareto (2013): (1) z-scores reescalados para média 100 e
    desvio 10, polaridade positiva; (2) para cada unidade i,

        MPI_i = M_{z_i} − S_{z_i} · cv_{z_i}

    onde M é a média horizontal das duas z, S o desvio-padrão horizontal
    e cv = S/M. O termo S·cv penaliza a desequilíbrio entre dimensões
    (não compensação parcial). Momentos (média, desvio) vêm da
    coorte-base para o MPI ser comparável entre painéis.

    Nota 25 da dissertação.
    """
    z_c = _z_cem(c_barra, media_c, desvio_c)
    z_h = _z_cem(h_barra, media_h, desvio_h)
    media_horizontal = (z_c + z_h) / 2.0
    desvio_horizontal = float(np.sqrt(((z_c - media_horizontal) ** 2 +
                                       (z_h - media_horizontal) ** 2) / 2.0))
    if media_horizontal == 0:
        return 0.0
    cv = desvio_horizontal / media_horizontal
    return float(media_horizontal - desvio_horizontal * cv)


def _z_cem(valor: float, media: float, desvio: float) -> float:
    if desvio == 0 or not np.isfinite(desvio):
        return 100.0
    return 100.0 + 10.0 * (valor - media) / desvio


def momentos_mpi_coorte_base(
    quadro: pd.DataFrame,
    ano_base: int,
    coluna_c: str = "c_barra_mm",
    coluna_h: str = "h_barra_mm",
    coluna_coorte: str = "coorte",
) -> dict[str, float]:
    base = quadro.loc[quadro[coluna_coorte] == ano_base]
    if base.empty:
        raise ValueError(f"Coorte-base {ano_base} vazia para o MPI.")
    return {
        "media_c": float(base[coluna_c].mean()),
        "desvio_c": float(base[coluna_c].std(ddof=0)),
        "media_h": float(base[coluna_h].mean()),
        "desvio_h": float(base[coluna_h].std(ddof=0)),
    }


def agregar_icp(
    quadro: pd.DataFrame,
    coluna_c: str = "c_barra_mm",
    coluna_h: str = "h_barra_mm",
    momentos_mpi: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Acrescenta icp (geométrica), icp_aritmetica e icp_mpi."""
    resultado = quadro.copy()
    resultado["icp"] = [
        media_geometrica(c, h)
        for c, h in zip(resultado[coluna_c], resultado[coluna_h], strict=False)
    ]
    resultado["icp_aritmetica"] = [
        media_aritmetica(c, h)
        for c, h in zip(resultado[coluna_c], resultado[coluna_h], strict=False)
    ]
    if momentos_mpi is None:
        momentos_mpi = {
            "media_c": float(resultado[coluna_c].mean()),
            "desvio_c": float(resultado[coluna_c].std(ddof=0)),
            "media_h": float(resultado[coluna_h].mean()),
            "desvio_h": float(resultado[coluna_h].std(ddof=0)),
        }
    resultado["icp_mpi"] = [
        mazziotta_pareto_par(c, h, **momentos_mpi)
        for c, h in zip(resultado[coluna_c], resultado[coluna_h], strict=False)
    ]
    return resultado
