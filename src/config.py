"""
Parâmetros configuráveis do Índice de Complexidade Processual (ICP).

Papel no pipeline
-----------------
Centraliza todas as decisões que a dissertação marca como «pontos em aberto»
(secções 3.5.1, 3.5.3, 3.5.6 e 3.5.8). Nenhum destes valores deve ficar
espalhado (hardcoded) pelos algoritmos.

AVISO — o pipeline NÃO deve ser considerado final enquanto os parâmetros
marcados com TODO não forem confirmados com o orientador. Os valores
provisórios abaixo são sugestões de arranque para o código correr de ponta
a ponta, não decisões definitivas.

Como os notebooks posteriores leem este módulo (e, se existir, o ficheiro
`data/processado/parametros_sugeridos.json` gerado pela EDA), altere aqui
e volte a correr a partir do notebook 02.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 3.5.1 — limiar mínimo de comprimento da sequência
# Processos com menos movimentos do que este limiar aproximam-se do limite
# degenerado c(S) ≈ l(S) e são excluídos listwise da construção do índice.
# TODO: definir a partir da distribuição observada na EDA (notebook 02).
# ---------------------------------------------------------------------------
LIMIAR_MINIMO_MOVIMENTOS: int | None = None
# Fallback operacional (não é decisão definitiva). Cinco movimentos é um
# ponto de partida comum na literatura de complexidade de sequências curtas:
# abaixo disto c(S) cresce quase linearmente com n e deixa de discriminar.
LIMIAR_MINIMO_MOVIMENTOS_PROVISORIO: int = 5

# Candidatos a testar na análise de robustez (secção 3.5.7).
LIMIARES_ROBUSTEZ: tuple[int, ...] = (3, 5, 8, 12)

# ---------------------------------------------------------------------------
# 3.5.3 — ano-base da normalização min-max entre coortes
# A primeira coorte observada é a referência; os min/máx NÃO são
# recalculados automaticamente quando chega uma coorte nova.
# TODO: confirmar se a coorte-base da dissertação é 2019 (exemplo do
# capítulo) ou a primeira coorte efectivamente presente nos dados.
# ---------------------------------------------------------------------------
ANO_BASE: int | None = None
ANO_BASE_PROVISORIO: int | None = None  # preenchido pela EDA se None

# Lista de (tribunal, ano de ajuizamento). Lista vazia = derivar dos dados.
# Exemplo da dissertação: [("TRF2", 2019), ("TRF2", 2023)]
COORTES: list[tuple[str, int]] = []

# Variável que define a coorte de cada processo (secção 3.5.3 / 3.4).
# Usamos o ano de ajuizamento — não a data da baixa — para que o painel
# temporal descreva a entrada do processo no sistema, não o encerramento.
CHAVE_COORTE: str = "ano_ajuizamento"

# ---------------------------------------------------------------------------
# 3.5.6 — limiar de alerta da correlação entre dimensões
# Se Spearman(c̄, H̄) numa coorte nova ultrapassar este valor, a arquitectura
# (duas dimensões + média geométrica) deve ser revista: as dimensões terão
# deixado de trazer informação distinguível.
# Valor inicial sugerido, a validar com o orientador.
# ---------------------------------------------------------------------------
LIMIAR_CORRELACAO_DIMENSOES: float = 0.90

# ---------------------------------------------------------------------------
# 3.5.8 — códigos TPU (Tabela Processual Unificada) usados como proxies
# de complexidade procedimental na validade convergente.
#
# TODO: confirmar códigos exactos com a TPU vigente e com a prática de
# lançamento do TRF2. Os códigos abaixo misturam (a) folhas TPU canónicas
# e (b) códigos efectivamente observados na amostra de trabalho, e DEVEM
# ser revistos. A validação também reporta um matching por nome (contém
# palavra-chave) para ajudar essa confirmação — ver notebook 04.
#
# Observação empírica da amostra TRF2 (baixa 2025): perícia e carta
# precatória como NOME de movimento não aparecem; redistribuição (36) e
# vários códigos de recurso/suspensão aparecem. Isto condiciona o poder
# do teste convergente para os proxies raros.
# ---------------------------------------------------------------------------
CODIGOS_MOVIMENTO_PROCEDIMENTAIS: dict[str, list[int]] = {
    "pericia": [
        417,   # Nomeação de Perito (TPU; confirmar)
        418,   # Entrega de laudo / esclarecimentos (TPU; confirmar)
        419,
        1051,
    ],
    "carta_precatoria": [
        # Sem evidência de nome «precatória» na amostra TRF2 inspeccionada.
        # 123 = Remessa (genérico — NÃO assumir que é carta precatória).
        # Lista deixada propositalmente curta até confirmação.
    ],
    "incidente_processual": [
        272,    # A depender do julgamento de outra causa / declaração incidente
        12098,  # IRDR
    ],
    "redistribuicao": [
        36,     # Redistribuição (observado na amostra)
        1013,   # Redistribuição por prevenção (TPU)
    ],
    "recurso": [
        265,    # Recurso Extraordinário com repercussão geral (observado)
        1060,   # Recurso (observado)
        235,    # Não conhecimento de recurso
        230,    # Recurso prejudicado
        11975,  # Recurso especial repetitivo
        239,    # Recurso inominado (TPU; confirmar uso no TRF2)
        240,    # Agravo (TPU; confirmar)
    ],
    "suspensao": [
        898,    # Por decisão judicial (folha frequente sob suspensão/sobrestamento)
        264,    # Suspensão condicional do processo
        25,     # Nó-pai TPU «Suspensão ou Sobrestamento»
        11025,  # Suspensão ou sobrestamento (serventuário)
    ],
}

# Palavras-chave (minúsculas) para o matching complementar por nome —
# NÃO substitui a lista de códigos; serve para diagnosticar omissões.
PALAVRAS_CHAVE_PROCEDIMENTAIS: dict[str, tuple[str, ...]] = {
    "pericia": ("perícia", "pericia", "perito", "laudo pericial"),
    "carta_precatoria": ("precatória", "precatoria", "carta precatória"),
    "incidente_processual": ("incidente",),
    "redistribuicao": ("redistribui",),
    "recurso": ("recurso", "agravo", "apelação", "apelacao"),
    "suspensao": ("suspens", "sobrest"),
}

# Movimentos terminais: usados para inferir encerrado vs. em curso
# (secção 3.5.1 — censura à direita). Não entram no índice.
CODIGOS_MOVIMENTO_TERMINAIS: set[int] = {
    22,    # Baixa Definitiva
    246,   # Arquivamento Definitivo
}

# ---------------------------------------------------------------------------
# Agregação principal e alternativas de robustez (secção 3.5.4 / 3.5.7)
# Sem estimação de pesos. Média geométrica = regra principal.
# ---------------------------------------------------------------------------
REGRA_AGREGACAO_PRINCIPAL: str = "geometrica"
REGRAS_AGREGACAO_ROBUSTEZ: tuple[str, ...] = ("geometrica", "aritmetica", "mpi")

# Base dos logaritmos da entropia de Shannon (bits). Secção 3.5.3.
BASE_LOG_ENTROPIA: float = 2.0

# Casas decimais APA (excepção: p-valores e contagens).
CASAS_DECIMAIS_APA: int = 2

# Número máximo de níveis de classe processual nas dummies da regressão;
# as restantes são agrupadas em «Outras» para evitar saturação.
N_CLASSES_DUMMIES_REGRESSAO: int = 8

# Ficheiro gerado pelo notebook 02 com sugestões a partir da EDA.
NOME_PARAMETROS_SUGERIDOS: str = "parametros_sugeridos.json"


def _ler_sugeridos(caminho: Path) -> dict[str, Any]:
    if not caminho.exists():
        return {}
    with caminho.open(encoding="utf-8") as ficheiro:
        return json.load(ficheiro)


def parametros_efectivos(dir_processado: Path | None = None) -> dict[str, Any]:
    """
    Resolve os TODOs: valor explícito em config.py > sugestão da EDA >
    fallback provisório. Emite a origem de cada decisão para o investigador
    não confundir placeholder com parâmetro validado.
    """
    sugeridos: dict[str, Any] = {}
    if dir_processado is not None:
        sugeridos = _ler_sugeridos(dir_processado / NOME_PARAMETROS_SUGERIDOS)

    limiar = LIMIAR_MINIMO_MOVIMENTOS
    origem_limiar = "config.py (explícito)"
    if limiar is None:
        if sugeridos.get("LIMIAR_MINIMO_MOVIMENTOS") is not None:
            limiar = int(sugeridos["LIMIAR_MINIMO_MOVIMENTOS"])
            origem_limiar = "EDA (parametros_sugeridos.json)"
        else:
            limiar = LIMIAR_MINIMO_MOVIMENTOS_PROVISORIO
            origem_limiar = "fallback provisório (config.py)"

    ano_base = ANO_BASE
    origem_ano = "config.py (explícito)"
    if ano_base is None:
        if sugeridos.get("ANO_BASE") is not None:
            ano_base = int(sugeridos["ANO_BASE"])
            origem_ano = "EDA (parametros_sugeridos.json)"
        elif ANO_BASE_PROVISORIO is not None:
            ano_base = int(ANO_BASE_PROVISORIO)
            origem_ano = "fallback provisório (config.py)"
        else:
            ano_base = None
            origem_ano = "ainda indefinido — será a primeira coorte observada"

    coortes = list(COORTES)
    origem_coortes = "config.py (explícito)"
    if not coortes:
        if sugeridos.get("COORTES"):
            coortes = [tuple(par) for par in sugeridos["COORTES"]]
            origem_coortes = "EDA (parametros_sugeridos.json)"
        else:
            origem_coortes = "derivar dos dados em tempo de execução"

    return {
        "LIMIAR_MINIMO_MOVIMENTOS": limiar,
        "origem_limiar": origem_limiar,
        "ANO_BASE": ano_base,
        "origem_ano_base": origem_ano,
        "COORTES": coortes,
        "origem_coortes": origem_coortes,
        "LIMIAR_CORRELACAO_DIMENSOES": LIMIAR_CORRELACAO_DIMENSOES,
        "CODIGOS_MOVIMENTO_PROCEDIMENTAIS": CODIGOS_MOVIMENTO_PROCEDIMENTAIS,
        "PALAVRAS_CHAVE_PROCEDIMENTAIS": PALAVRAS_CHAVE_PROCEDIMENTAIS,
        "CODIGOS_MOVIMENTO_TERMINAIS": CODIGOS_MOVIMENTO_TERMINAIS,
        "REGRA_AGREGACAO_PRINCIPAL": REGRA_AGREGACAO_PRINCIPAL,
        "REGRAS_AGREGACAO_ROBUSTEZ": REGRAS_AGREGACAO_ROBUSTEZ,
        "LIMIARES_ROBUSTEZ": LIMIARES_ROBUSTEZ,
        "CHAVE_COORTE": CHAVE_COORTE,
        "N_CLASSES_DUMMIES_REGRESSAO": N_CLASSES_DUMMIES_REGRESSAO,
        "pendente_validacao": True,
    }


def aviso_parametros_pendentes(parametros: dict[str, Any] | None = None) -> str:
    """Texto para imprimir no topo de cada notebook."""
    parametros = parametros or parametros_efectivos()
    return (
        "AVISO METODOLÓGICO — parâmetros ainda não validados com o orientador.\n"
        f"  Limiar mínimo de movimentos: {parametros['LIMIAR_MINIMO_MOVIMENTOS']} "
        f"({parametros['origem_limiar']})\n"
        f"  Ano-base da normalização: {parametros['ANO_BASE']} "
        f"({parametros['origem_ano_base']})\n"
        f"  Coortes: {parametros['COORTES'] or '(derivar dos dados)'} "
        f"({parametros['origem_coortes']})\n"
        "  O índice produzido nesta corrida é operacional, não a versão final "
        "da dissertação."
    )
