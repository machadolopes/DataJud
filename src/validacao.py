"""
Validação do ICP: critério externo e validade convergente/discriminante.

Papel no pipeline
-----------------
Secção 3.5.8. Duas frentes empiricamente testáveis nesta fase:

1. Validade de critério externo — regressão da *duração observada*
   (nunca insumo do índice) sobre o ICP, controlando classe, tribunal,
   coorte e comprimento da sequência (variável de controlo, secção 3.4).
   O ganho de R² face a um modelo-base sem ICP quantifica o poder
   explicativo atribuível ao índice.
2. Validade convergente/discriminante — Spearman entre c̄ e H̄ (deve ser
   moderada) e correlação de cada dimensão com proxies procedimentais
   (perícia, carta precatória, incidente, redistribuição, recurso,
   suspensão). Os códigos TPU são parâmetros em config.py (TODO).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import spearmanr

from src.config import (
    CODIGOS_MOVIMENTO_PROCEDIMENTAIS,
    N_CLASSES_DUMMIES_REGRESSAO,
    PALAVRAS_CHAVE_PROCEDIMENTAIS,
)
from src.graficos_apa import formatar_p
from src.sequencias import _como_lista_movimentos, codigo_movimento


def agrupar_classes_raras(
    quadro: pd.DataFrame,
    n_manter: int = N_CLASSES_DUMMIES_REGRESSAO,
    coluna: str = "classe_nome",
) -> pd.Series:
    """Mantém as n classes mais frequentes; as restantes → «Outras»."""
    top = set(quadro[coluna].value_counts().head(n_manter).index)
    return quadro[coluna].where(quadro[coluna].isin(top), other="Outras")


def _formula_controlos(
    incluir_tribunal: bool,
    incluir_grau: bool,
) -> str:
    pecas = ["C(classe_agrupada)", "C(coorte)", "n_movimentos"]
    if incluir_tribunal:
        pecas.append("C(tribunal)")
    if incluir_grau:
        pecas.append("C(grau)")
    return " + ".join(pecas)


def regressao_criterio_externo(
    quadro: pd.DataFrame,
    coluna_icp: str = "icp",
    coluna_duracao: str = "duracao_dias",
) -> dict[str, Any]:
    """
    OLS: duração ~ controlos  vs.  duração ~ ICP + controlos.

    Tribunal/grau só entram se tiverem mais de um nível (nesta extração
    o tribunal é TRF2 constante — incluí-lo saturaria a matriz).
    """
    dados = quadro.dropna(subset=[coluna_duracao, coluna_icp, "n_movimentos", "coorte"]).copy()
    dados["classe_agrupada"] = agrupar_classes_raras(dados)
    incluir_tribunal = dados["tribunal"].nunique() > 1
    incluir_grau = dados["grau"].nunique() > 1
    controlos = _formula_controlos(incluir_tribunal, incluir_grau)

    modelo_base = smf.ols(f"{coluna_duracao} ~ {controlos}", data=dados).fit()
    modelo_icp = smf.ols(
        f"{coluna_duracao} ~ {coluna_icp} + {controlos}", data=dados
    ).fit()
    delta_r2 = float(modelo_icp.rsquared - modelo_base.rsquared)
    return {
        "n": int(len(dados)),
        "modelo_base": modelo_base,
        "modelo_icp": modelo_icp,
        "r2_base": float(modelo_base.rsquared),
        "r2_icp": float(modelo_icp.rsquared),
        "r2_ajustado_base": float(modelo_base.rsquared_adj),
        "r2_ajustado_icp": float(modelo_icp.rsquared_adj),
        "delta_r2": delta_r2,
        "incluir_tribunal": incluir_tribunal,
        "incluir_grau": incluir_grau,
    }


def regressao_within_coorte(
    quadro: pd.DataFrame,
    coluna_icp: str = "icp",
    coluna_duracao: str = "duracao_dias",
) -> dict[str, Any]:
    """
    Validade de critério *dentro* da coorte.

    Nesta extração todos os processos têm baixa em 2025, portanto a duração
    observada é quase uma função do ano de ajuizamento. Controlar por
    C(coorte) absorve essa variação e o ΔR² do ICP cai mecanicamente a
    zero — não é evidência contra o índice, é um artefacto do desenho
    amostral. Residualizar duração e ICP na coorte isola a variação
    intra-painel que a secção 3.5.8 efectivamente pede.
    """
    dados = quadro.dropna(subset=[coluna_duracao, coluna_icp, "n_movimentos", "coorte"]).copy()
    dados["classe_agrupada"] = agrupar_classes_raras(dados)
    dados["duracao_wc"] = dados[coluna_duracao] - dados.groupby("coorte")[coluna_duracao].transform("mean")
    dados["icp_wc"] = dados[coluna_icp] - dados.groupby("coorte")[coluna_icp].transform("mean")
    incluir_grau = dados["grau"].nunique() > 1
    controlos = "C(classe_agrupada) + n_movimentos"
    if incluir_grau:
        controlos += " + C(grau)"
    modelo_base = smf.ols(f"duracao_wc ~ {controlos}", data=dados).fit()
    modelo_icp = smf.ols(f"duracao_wc ~ icp_wc + {controlos}", data=dados).fit()
    return {
        "n": int(len(dados)),
        "modelo_base": modelo_base,
        "modelo_icp": modelo_icp,
        "r2_base": float(modelo_base.rsquared),
        "r2_icp": float(modelo_icp.rsquared),
        "r2_ajustado_base": float(modelo_base.rsquared_adj),
        "r2_ajustado_icp": float(modelo_icp.rsquared_adj),
        "delta_r2": float(modelo_icp.rsquared - modelo_base.rsquared),
        "coef_icp": float(modelo_icp.params.get("icp_wc", float("nan"))),
        "p_icp": float(modelo_icp.pvalues.get("icp_wc", float("nan"))),
    }


def quadro_coeficientes_apa(modelo) -> pd.DataFrame:
    """Tabela de regressão: B, EP, IC 95%, t, p (formato APA)."""
    intervalo = modelo.conf_int()
    linhas = []
    for nome in modelo.params.index:
        p_valor = float(modelo.pvalues[nome])
        linhas.append(
            {
                "Variável": nome,
                "B": float(modelo.params[nome]),
                "EP": float(modelo.bse[nome]),
                "IC 95% inf.": float(intervalo.loc[nome, 0]),
                "IC 95% sup.": float(intervalo.loc[nome, 1]),
                "t": float(modelo.tvalues[nome]),
                "p": p_valor,
                "p (APA)": formatar_p(p_valor),
            }
        )
    return pd.DataFrame(linhas)


def spearman_seguro(x: Sequence[float], y: Sequence[float]) -> tuple[float, float]:
    """Spearman com paridade de comprimento; devolve (rho, p)."""
    xs = pd.Series(list(x), dtype=float)
    ys = pd.Series(list(y), dtype=float)
    mascara = xs.notna() & ys.notna()
    if mascara.sum() < 3:
        return float("nan"), float("nan")
    rho, p_valor = spearmanr(xs[mascara], ys[mascara])
    return float(rho), float(p_valor)


def presenca_proxy(
    movimentos: Sequence[dict[str, Any]] | None,
    codigos: Iterable[int],
    palavras: Iterable[str] = (),
) -> int:
    """1 se a tramitação contém o proxy (código TPU ou palavra no nome)."""
    conjunto = {int(c) for c in codigos}
    palavras_l = tuple(p.lower() for p in palavras)
    for movimento in _como_lista_movimentos(movimentos):
        if not isinstance(movimento, dict):
            continue
        codigo = codigo_movimento(movimento)
        try:
            if int(codigo) in conjunto:
                return 1
        except (TypeError, ValueError):
            pass
        nome = str(movimento.get("nome") or "").lower()
        if any(p in nome for p in palavras_l):
            return 1
    return 0


def indicadores_proxies(
    quadro: pd.DataFrame,
    codigos: Mapping[str, list[int]] | None = None,
    palavras: Mapping[str, tuple[str, ...]] | None = None,
) -> pd.DataFrame:
    """Colunas binárias `proxy_<nome>` para a validade convergente."""
    codigos = codigos or CODIGOS_MOVIMENTO_PROCEDIMENTAIS
    palavras = palavras or PALAVRAS_CHAVE_PROCEDIMENTAIS
    resultado = quadro.copy()
    for nome, lista_codigos in codigos.items():
        chaves = palavras.get(nome, ())
        resultado[f"proxy_{nome}"] = resultado["movimentos"].map(
            lambda movs, lc=lista_codigos, ch=chaves: presenca_proxy(movs, lc, ch)
        )
    return resultado


def validade_convergente_discriminante(
    quadro: pd.DataFrame,
    coluna_c: str = "c_barra_mm",
    coluna_h: str = "h_barra_mm",
) -> pd.DataFrame:
    """
    Spearman entre dimensões e entre cada dimensão e cada proxy.

    Expectativa teórica (secção 3.5.8): correlação *moderada* entre c̄ e H̄
    — nem ~0 (dimensões desligadas a ponto de não formarem um índice) nem
    ~1 (redundância; a média geométrica deixaria de ter duas fontes).
    """
    linhas = []
    rho, p_valor = spearman_seguro(quadro[coluna_c], quadro[coluna_h])
    linhas.append(
        {
            "par": "c̄(S) — H̄",
            "rho_spearman": rho,
            "p": p_valor,
            "p (APA)": formatar_p(p_valor),
            "n": int(quadro[[coluna_c, coluna_h]].dropna().shape[0]),
        }
    )
    proxies = [c for c in quadro.columns if c.startswith("proxy_")]
    for dim_nome, dim_col in (("c̄(S)", coluna_c), ("H̄", coluna_h), ("ICP", "icp")):
        if dim_col not in quadro.columns:
            continue
        for proxy in proxies:
            rho_p, p_p = spearman_seguro(quadro[dim_col], quadro[proxy])
            linhas.append(
                {
                    "par": f"{dim_nome} — {proxy.removeprefix('proxy_')}",
                    "rho_spearman": rho_p,
                    "p": p_p,
                    "p (APA)": formatar_p(p_p),
                    "n": int(quadro[[dim_col, proxy]].dropna().shape[0]),
                    "prevalencia_proxy": float(quadro[proxy].mean()) if proxy in quadro else np.nan,
                }
            )
    return pd.DataFrame(linhas)
