"""
Monitorização da dinâmica entre dimensões ao longo das coortes.

Papel no pipeline
-----------------
Secção 3.5.6. O índice é *dinâmico* precisamente porque não tem pesos a
reestimar: c̄ e H̄ actualizam-se com a tramitação. O que se monitoriza
é a *relação* entre as duas dimensões. Se Spearman(c̄, H̄) numa coorte
nova se aproximar de 1 (acima do limiar em config.py, por omissão .90),
as dimensões deixaram de ser distinguíveis e a arquitectura deve ser
revista — não se «recalibram pesos», porque não os há.
"""

from __future__ import annotations

import pandas as pd

from src.config import LIMIAR_CORRELACAO_DIMENSOES
from src.validacao import spearman_seguro


def correlacao_dimensoes_por_coorte(
    quadro: pd.DataFrame,
    coluna_c: str = "c_barra_mm",
    coluna_h: str = "h_barra_mm",
    coluna_coorte: str = "coorte",
) -> pd.DataFrame:
    """Spearman(c̄, H̄) em cada coorte, com n e p-valor."""
    linhas = []
    for coorte, bloco in quadro.groupby(coluna_coorte, dropna=True):
        rho, p_valor = spearman_seguro(bloco[coluna_c], bloco[coluna_h])
        linhas.append(
            {
                "coorte": int(coorte) if pd.notna(coorte) else coorte,
                "n": int(len(bloco)),
                "rho_spearman": rho,
                "p": p_valor,
            }
        )
    resultado = pd.DataFrame(linhas).sort_values("coorte").reset_index(drop=True)
    return resultado


def avaliar_alerta(
    quadro_correlacoes: pd.DataFrame,
    ano_base: int,
    limiar: float = LIMIAR_CORRELACAO_DIMENSOES,
) -> pd.DataFrame:
    """Marca coortes acima do limiar de revisão da arquitectura."""
    resultado = quadro_correlacoes.copy()
    rho_base_series = resultado.loc[resultado["coorte"] == ano_base, "rho_spearman"]
    rho_base = float(rho_base_series.iloc[0]) if not rho_base_series.empty else float("nan")
    resultado["rho_coorte_base"] = rho_base
    resultado["alerta_revisao"] = resultado["rho_spearman"] >= limiar
    resultado["limiar_alerta"] = limiar
    return resultado
