"""Gera os cinco notebooks do pipeline (narrativa + orquestração)."""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf

RAIZ = Path(__file__).resolve().parent.parent
DIR_NB = RAIZ / "notebooks"
DIR_NB.mkdir(exist_ok=True)

SETUP = r'''# Arranque reproduzível: funciona a partir da raiz ou de notebooks/.
from pathlib import Path
import sys
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

def raiz_projeto() -> Path:
    cwd = Path.cwd().resolve()
    for cand in (cwd, cwd.parent, Path(".").resolve()):
        if (cand / "src" / "config.py").exists():
            return cand
    raise RuntimeError("Não encontrei a raiz do projecto (pasta src/).")

RAIZ = raiz_projeto()
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

%matplotlib inline

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from src.caminhos import garantir_directorias
from src.config import aviso_parametros_pendentes, parametros_efectivos
from src.graficos_apa import CatalogoAPA, aplicar_estilo_apa, formatar_p

DIRS = garantir_directorias(RAIZ)
PARAM = parametros_efectivos(DIRS["processado"])
aplicar_estilo_apa()

pd.set_option("display.max_columns", 40)
pd.set_option("display.max_colwidth", 88)
pd.set_option("display.max_rows", 120)
pd.set_option("display.width", 160)

print(aviso_parametros_pendentes(PARAM))
print("Raiz:", RAIZ)
'''


def novo():
    nb = nbf.v4.new_notebook()
    nb["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "pygments_lexer": "ipython3"},
    }
    return nb


def md(nb, texto):
    nb.cells.append(nbf.v4.new_markdown_cell(texto.strip() + "\n"))


def code(nb, texto):
    nb.cells.append(nbf.v4.new_code_cell(texto.strip() + "\n"))


def gravar(nb, nome):
    caminho = DIR_NB / nome
    nbf.write(nb, caminho)
    print("escrevi", caminho)


def nb01():
    nb = novo()
    md(nb, """
# 01 — Diagnóstico do schema DataJud

**Secção da dissertação:** 3.5.1 (amostra e cobertura) — etapa prévia obrigatória.

Este notebook **não assume** a estrutura do `.jsonl`. Lê as primeiras linhas,
lista caminhos de chaves aninhadas, classifica se cada linha é um processo ou
uma página Elasticsearch, e mede a presença dos campos esperados em *todo* o
ficheiro. Grava `data/processado/processos.parquet` para os notebooks seguintes.
""")
    code(nb, SETUP)
    code(nb, """
from IPython.display import display, Markdown, HTML
import json
from collections import Counter

from src.io_datajud import (
    CAMPOS_ESPERADOS,
    caminhos_chaves,
    carregar_processos,
    diagnostico_cobertura,
    localizar_jsonl,
)

catalogo = CatalogoAPA(
    DIRS["figuras"], DIRS["tabelas"],
    DIRS["saidas"] / "relatorio_resultados.md",
    reiniciar_relatorio=True,
)
""")
    md(nb, """
## Localização do ficheiro e inspeção das primeiras linhas

A extração de referência (`DATAJUD_API_v_final.ipynb`) grava **um processo por
linha** (já o `_source` do Elasticsearch, não a página `hits.hits`). Confirmamos
isto empiricamente — se o ficheiro for uma dump cru da API, o parser adapta-se.
""")
    code(nb, """
caminho_jsonl = localizar_jsonl(DIRS["dados"])
print("Ficheiro:", caminho_jsonl)
print(f"Tamanho: {caminho_jsonl.stat().st_size / 1e6:.2f} MB")

N_AMOSTRA = 20
amostra_bruta = []
with caminho_jsonl.open(encoding="utf-8") as ficheiro:
    for i, linha in enumerate(ficheiro):
        if i >= N_AMOSTRA:
            break
        if linha.strip():
            amostra_bruta.append(json.loads(linha))

print(f"Linhas de amostra lidas: {len(amostra_bruta)}")
""")
    md(nb, """
Para cada linha: chaves de topo, caminhos aninhados (`movimentos[].codigo`, etc.)
e um `json.dumps` *truncado* (os movimentos completos tornariam a célula ilegível).
""")
    code(nb, """
def truncar_processo(obj, n_mov=2):
    copia = dict(obj)
    if isinstance(copia.get("movimentos"), list):
        copia["movimentos"] = copia["movimentos"][:n_mov] + (
            [{"_truncado": f"... {len(obj['movimentos']) - n_mov} movimentos omitidos"}]
            if len(obj["movimentos"]) > n_mov else []
        )
    return copia

linhas_resumo = []
for i, obj in enumerate(amostra_bruta, start=1):
    chaves = sorted(obj.keys()) if isinstance(obj, dict) else []
    caminhos = sorted(set(caminhos_chaves(obj)))
    linhas_resumo.append({
        "linha": i,
        "n_chaves_topo": len(chaves),
        "chaves_topo": ", ".join(chaves),
        "tem_hits": "hits" in chaves,
        "tem_movimentos": "movimentos" in chaves,
        "tem_numeroProcesso": "numeroProcesso" in chaves,
        "n_caminhos": len(caminhos),
    })
    print("=" * 78)
    print(f"LINHA {i} — chaves de topo: {chaves}")
    print("Caminhos aninhados:")
    for c in caminhos:
        print("  ", c)
    if i <= 2:
        print("JSON truncado:")
        print(json.dumps(truncar_processo(obj), ensure_ascii=False, indent=2)[:2500])

quadro_amostra = pd.DataFrame(linhas_resumo)
display(quadro_amostra)
""")
    md(nb, """
## Cobertura no ficheiro completo

Percorremos *todas* as linhas (streaming) para não assumir que a amostra das
20 primeiras é representativa. A tabela abaixo é o contrato de dados do resto
do pipeline: se um campo esperado tiver cobertura < 100 %, o parser usa o
nome real encontrado e documenta a diferença.
""")
    code(nb, """
cobertura, meta = diagnostico_cobertura(caminho_jsonl, n_amostra_linhas=N_AMOSTRA)
print("Formato detectado:", meta["formato"])
print("Linhas no .jsonl:", meta["n_linhas_jsonl"])
print("Processos extraídos:", meta["n_processos"])
print("Páginas Elasticsearch:", meta["n_paginas_elasticsearch"])
print("Linhas não reconhecidas:", meta["n_linhas_nao_reconhecidas"])

catalogo.nova_tabela(
    cobertura.round({"pct_presente": 2}),
    titulo="Presença dos campos esperados da API DataJud no ficheiro de trabalho",
    nota=(
        "Campos conforme a documentação pública da API DataJud (CNJ). "
        f"N = {meta['n_processos']} processos extraídos de "
        f"{meta['n_linhas_jsonl']} linhas JSONL. Formato detectado: "
        f"{meta['formato']}."
    ),
    nome_ficheiro="tabela_cobertura_campos_datajud",
    interpretacao=(
        "A extração TRF2 usada neste pipeline tem um processo por linha JSONL "
        "(não uma página hits.hits). Os campos essenciais do ICP — sobretudo "
        "movimentos, dataAjuizamento e identificadores — devem aparecer com "
        "cobertura próxima de 100 %; ausências aqui condicionam a exclusão listwise."
    ),
)

caminhos_df = (
    pd.DataFrame(
        {"caminho": list(meta["caminhos_chaves"].keys()),
         "n_processos": list(meta["caminhos_chaves"].values())}
    )
    .assign(pct=lambda d: 100 * d["n_processos"] / meta["n_processos"])
    .sort_values("n_processos", ascending=False)
    .reset_index(drop=True)
)
display(caminhos_df.head(40))
""")
    md(nb, """
## Carregamento tabular

O módulo `src/io_datajud.py` projecta cada processo num DataFrame, **preservando**
a lista `movimentos` (insumo do índice) e expondo classe/tribunal/grau/órgão/formato
como colunas de *controlo e coorte* — não como componentes do ICP (secção 3.4).
`dataAjuizamento` nesta extração é `YYYYMMDDHHMMSS`, não ISO-8601; o parser trata
as duas formas.
""")
    code(nb, """
processos = carregar_processos(caminho_jsonl)
print(processos.shape)
display(processos.drop(columns=["movimentos", "assuntos"]).head())

destino = DIRS["processado"] / "processos.parquet"
processos.to_parquet(destino, index=False)
print("Gravado:", destino)
""")
    md(nb, """
## Síntese

- Cada linha do `.jsonl` corresponde a **um processo** (formato confirmado), não a uma página da API.
- Campos esperados: ver Tabela de cobertura; o nome real `numeroProcesso` coincide com a documentação; `dataAjuizamento` vem compacto.
- O campo central `movimentos[].codigo` / `dataHora` / `nome` está presente e é o insumo do ICP.
- Artefacto: `data/processado/processos.parquet` — ponto de entrada do notebook 02.
""")
    gravar(nb, "01_diagnostico_schema.ipynb")


def nb02():
    nb = novo()
    md(nb, """
# 02 — Análise exploratória de dados

**Secções da dissertação:** 3.5.1 (amostra, limiar, censura à direita) e 3.5.2
(descrição do alfabeto de movimentos e dados em falta).

Produz o quadro filtrado `processos_eda.parquet` e sugere — *sem fechar* — o
limiar mínimo de movimentos e o ano-base da normalização (pontos em aberto).
""")
    code(nb, SETUP)
    code(nb, """
from IPython.display import display
from src.sequencias import aplicar_exclusao_listwise, preparar_quadro_sequencias
from src.complexidade_lz import complexidade_lz

parquet = DIRS["processado"] / "processos.parquet"
if not parquet.exists():
    raise FileNotFoundError(
        f"Artefacto em falta: {parquet}. Corra 01_diagnostico_schema.ipynb primeiro."
    )
processos = pd.read_parquet(parquet)
catalogo = CatalogoAPA(
    DIRS["figuras"], DIRS["tabelas"],
    DIRS["saidas"] / "relatorio_resultados.md",
    reiniciar_relatorio=False,
)
print("Processos carregados:", len(processos))
""")
    md(nb, """
## Volume, cobertura e período

Classe, tribunal, grau e formato **não entram no índice** (secção 3.4). Servem
para descrever a amostra e, mais tarde, como controlos da validação. A coorte
é o **ano de ajuizamento**, não o ano da baixa: o painel descreve a entrada
no sistema.
""")
    code(nb, """
quadro = preparar_quadro_sequencias(processos)

n_total = len(quadro)
periodo = (
    quadro["data_ajuizamento"].min(),
    quadro["data_ajuizamento"].max(),
)
print(f"N processos: {n_total}")
print(f"dataAjuizamento min/máx: {periodo[0]} — {periodo[1]}")
print("Tribunais:", quadro["tribunal"].value_counts().to_dict())
print("Graus:", quadro["grau"].value_counts().to_dict())

por_grau = (
    quadro.groupby("grau", dropna=False)
    .size().rename("n").reset_index()
    .assign(pct=lambda d: 100 * d["n"] / d["n"].sum())
)
catalogo.nova_tabela(
    por_grau,
    titulo="Distribuição dos processos por grau de jurisdição",
    nota="G1 = 1.º grau; G2 = 2.º grau; JE = Juizado Especial; TR = Turma Recursal. Extração TRF2, baixa definitiva em 2025.",
    nome_ficheiro="tabela_volume_por_grau",
    interpretacao="A amostra de trabalho concentra-se no 1.º grau e no Juizado Especial; o 2.º grau é residual e deve ser lido com cautela nas desagregações.",
)

por_classe = (
    quadro.groupby(["classe_codigo", "classe_nome"], dropna=False)
    .size().rename("n").reset_index()
    .sort_values("n", ascending=False)
    .head(12)
)
por_classe["pct"] = 100 * por_classe["n"] / n_total
catalogo.nova_tabela(
    por_classe,
    titulo="Doze classes processuais mais frequentes na amostra",
    nota="Classe segundo a Tabela Processual Unificada (TPU). Não entra no ICP (secção 3.4).",
    nome_ficheiro="tabela_top_classes",
    interpretacao="A composição por classe (execução fiscal, juizado, cumprimento de sentença) é heterogénea; por isso a validação controla a classe e não a inclui no índice.",
)
""")
    md(nb, """
## Comprimento da sequência de movimentos

Este histograma é o insumo directo da decisão do **limiar mínimo** (secção 3.5.1):
processos muito curtos aproximam-se do limite degenerado \(c(S) \\approx l(S)\) e
não discriminam complexidade estrutural. O limiar fica em `config.py` como TODO;
aqui apenas *sugerimos* um valor a validar com o orientador.
""")
    code(nb, """
desc = quadro["n_movimentos"].describe(percentiles=[0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95])
estatisticas = pd.DataFrame({
    "estatística": ["n", "média", "desvio-padrão", "mín", "P5", "P10", "P25", "mediana", "P75", "P90", "P95", "máx"],
    "n_movimentos": [
        desc["count"], desc["mean"], desc["std"], desc["min"],
        desc["5%"], desc["10%"], desc["25%"], desc["50%"],
        desc["75%"], desc["90%"], desc["95%"], desc["max"],
    ],
})
catalogo.nova_tabela(
    estatisticas,
    titulo="Estatísticas descritivas do comprimento da sequência de movimentos",
    nota="Comprimento = número de movimentos com código TPU após ordenação temporal. Não é duração em dias.",
    nome_ficheiro="tabela_descritivas_comprimento",
    interpretacao="O comprimento mediano e os percentis inferiores informam o limiar mínimo: abaixo de P5–P10 a sequência é demasiado curta para c(S) se afastar de n.",
)

fig, ax = plt.subplots(figsize=(7.2, 4.2))
sns.histplot(quadro["n_movimentos"], bins=40, ax=ax, color=sns.color_palette("colorblind")[0], edgecolor="white")
ax.set_xlabel("Número de movimentos por processo")
ax.set_ylabel("Frequência")
ax.axvline(desc["50%"], color="black", linestyle="--", linewidth=1, label="Mediana")
ax.axvline(desc["5%"], color="gray", linestyle=":", linewidth=1, label="P5")
ax.legend(frameon=False)
catalogo.nova_figura(
    fig,
    titulo="Distribuição do comprimento da sequência de movimentos por processo",
    nota="Linha tracejada = mediana; linha pontilhada = percentil 5. Amostra TRF2 com baixa definitiva em 2025.",
    nome_ficheiro="figura_histograma_comprimento_sequencia",
    interpretacao="A distribuição é assimétrica à direita: a maioria dos processos tem dezenas de movimentos, mas a cauda esquerda (sequências muito curtas) é a que justifica o limiar de exclusão da secção 3.5.1.",
)
""")
    md(nb, """
Para ancorar o limiar, calculamos \(c(S)/n\) por comprimento: quando esta razão
se aproxima de 1, cada movimento é uma componente nova e c(S) deixa de
discriminar. Sugerimos o menor n em que a mediana de c(S)/n cai abaixo de 0,90,
com piso em 5 (fallback de `config.py`).
""")
    code(nb, """
amostra_razao = quadro.loc[quadro["n_movimentos"] >= 1, ["sequencia_codigos", "n_movimentos"]].copy()
amostra_razao["c_s"] = amostra_razao["sequencia_codigos"].map(complexidade_lz)
amostra_razao["c_sobre_n"] = amostra_razao["c_s"] / amostra_razao["n_movimentos"]
por_n = (
    amostra_razao.groupby("n_movimentos")["c_sobre_n"]
    .median()
    .reset_index()
    .rename(columns={"c_sobre_n": "mediana_c_sobre_n"})
)
candidatos = por_n.loc[por_n["mediana_c_sobre_n"] < 0.90, "n_movimentos"]
sugerido_empirico = int(candidatos.min()) if len(candidatos) else 5
limiar_sugerido = max(5, sugerido_empirico)
print(f"Menor n com mediana c(S)/n < 0.90: {sugerido_empirico}")
print(f"Limiar sugerido (piso 5): {limiar_sugerido}")
display(por_n.head(15))
""")
    md(nb, """
## Dimensão do alfabeto de códigos de movimento

O alfabeto global α entra no majorante teórico de c(S) (Teorema 2). O alfabeto
*local* (k por processo) é o denominador de H̄. Os dois não se confundem.
""")
    code(nb, """
alfabeto = set()
for seq in quadro["sequencia_codigos"]:
    alfabeto.update(seq or [])
print("α (códigos distintos na amostra):", len(alfabeto))

desc_k = quadro["k_alfabeto_processo"].describe(percentiles=[0.05, 0.25, 0.50, 0.75, 0.95])
tab_k = pd.DataFrame({
    "estatística": ["n", "média", "desvio-padrão", "mín", "P5", "P25", "mediana", "P75", "P95", "máx", "α global"],
    "valor": [
        desc_k["count"], desc_k["mean"], desc_k["std"], desc_k["min"],
        desc_k["5%"], desc_k["25%"], desc_k["50%"], desc_k["75%"], desc_k["95%"],
        desc_k["max"], len(alfabeto),
    ],
})
catalogo.nova_tabela(
    tab_k,
    titulo="Diversidade de códigos de movimento: por processo e na amostra",
    nota="k = códigos distintos na tramitação de um processo; α = união de todos os códigos da amostra. α é o parâmetro do Teorema 2 (Lempel & Ziv, 1976).",
    nome_ficheiro="tabela_alfabeto_movimentos",
    interpretacao="k local é tipicamente muito menor do que α: a equitabilidade de Pielou (H̄) compara cada processo ao seu próprio máximo, não ao alfabeto TPU completo.",
)

fig, ax = plt.subplots(figsize=(7.2, 4.2))
sns.histplot(quadro["k_alfabeto_processo"], bins=30, ax=ax, color=sns.color_palette("colorblind")[1], edgecolor="white")
ax.set_xlabel("Códigos de movimento distintos por processo (k)")
ax.set_ylabel("Frequência")
catalogo.nova_figura(
    fig,
    titulo="Distribuição do tamanho do alfabeto local de movimentos",
    nota="k condiciona o intervalo de variação possível de H̄ = H / log2(k).",
    nome_ficheiro="figura_histograma_alfabeto_local",
    interpretacao="A maior parte dos processos usa um subconjunto pequeno do alfabeto TPU; por isso H bruto cresceria mecanicamente com k, e a normalização intra-processo é necessária.",
)
""")
    md(nb, """
## Dados em falta e exclusão listwise

Só se exclui o que impede o cálculo do índice: sequência ausente/corrompida ou
abaixo do limiar. Classe ou data em falta *não* excluem do ICP (não são insumos);
contabilizam-se aqui para transparência e para a validação (duração).
""")
    code(nb, """
faltas = pd.DataFrame({
    "campo": [
        "sequência de movimentos vazia",
        "classe",
        "dataAjuizamento",
        "tribunal",
        "grau",
        "formato",
        "órgão julgador",
        "duração observada não calculável",
    ],
    "n_em_falta": [
        int((quadro["n_movimentos"] <= 0).sum()),
        int(quadro["classe_nome"].isna().sum()),
        int(quadro["data_ajuizamento"].isna().sum()),
        int(quadro["tribunal"].isna().sum()),
        int(quadro["grau"].isna().sum()),
        int(quadro["formato_nome"].isna().sum()),
        int(quadro["orgao_nome"].isna().sum()),
        int(quadro["duracao_dias"].isna().sum()),
    ],
})
faltas["pct"] = 100 * faltas["n_em_falta"] / len(quadro)
catalogo.nova_tabela(
    faltas,
    titulo="Percentagem de processos com campos em falta",
    nota="A exclusão listwise do índice aplica-se apenas à sequência de movimentos. Os restantes campos são controlos ou o critério externo (duração).",
    nome_ficheiro="tabela_dados_em_falta",
    interpretacao="Se a sequência está quase sempre presente, o filtro que realmente muda N é o limiar mínimo, não a corrupção de dados.",
)

limiar = int(PARAM["LIMIAR_MINIMO_MOVIMENTOS"] or limiar_sugerido)
# Se config ainda é o fallback, preferir a sugestão empírica desta EDA.
if PARAM["origem_limiar"].startswith("fallback"):
    limiar = limiar_sugerido
print("Limiar usado nesta corrida:", limiar, "| origem config:", PARAM["origem_limiar"])

filtrado, fluxo = aplicar_exclusao_listwise(quadro, limiar)
catalogo.nova_tabela(
    fluxo,
    titulo="Fluxo de exclusão listwise até à amostra de construção do índice",
    nota=f"Limiar mínimo = {limiar} movimentos (sugestão de arranque; secção 3.5.1). Não é decisão definitiva.",
    nome_ficheiro="tabela_fluxo_exclusao",
    interpretacao="O fluxo n inicial → excluídos por sequência vazia → excluídos pelo limiar → n final é o denominador de todos os resultados posteriores.",
)
""")
    md(nb, """
## Processos em curso versus encerrados

A API pública não traz um campo canónico de situação. Inferimos encerramento
pela presença de movimentos terminais tabelados (código 22, Baixa Definitiva;
246, Arquivamento Definitivo). Processos em curso têm sequência **censurada à
direita** (secção 3.5.1): o ICP continua definido, a duração observada está
truncada. Esta extração foi desenhada com baixa em 2025, portanto espera-se
predominância de encerrados.
""")
    code(nb, """
estado = (
    quadro.assign(estado=np.where(quadro["encerrado"], "encerrado", "em curso"))
    .groupby("estado").size().rename("n").reset_index()
)
estado["pct"] = 100 * estado["n"] / estado["n"].sum()
catalogo.nova_tabela(
    estado,
    titulo="Proporção de processos encerrados e em curso (inferência por movimento terminal)",
    nota="Encerrado = presença de movimento 22 (Baixa Definitiva) ou 246 (Arquivamento Definitivo), ou nome equivalente. Inferência, não campo nativo da API.",
    nome_ficheiro="tabela_encerrado_vs_em_curso",
    interpretacao="Numa extração filtrada por baixa definitiva, a censura à direita deve ser residual; se aparecerem processos «em curso», vale inspeccionar códigos terminais não previstos em config.py.",
)

ano_base_sugerido = int(filtrado["coorte"].min())
coortes = sorted(
    (str(t), int(a))
    for t, a in filtrado.dropna(subset=["tribunal", "coorte"])[["tribunal", "coorte"]].drop_duplicates().itertuples(index=False)
)
sugeridos = {
    "LIMIAR_MINIMO_MOVIMENTOS": int(limiar),
    "ANO_BASE": ano_base_sugerido,
    "COORTES": coortes,
    "justificacao_limiar": (
        f"Piso 5 combinado com o menor n cuja mediana de c(S)/n < 0.90 "
        f"(n={sugerido_empirico} nesta amostra). P5 do comprimento = {float(desc['5%']):.1f}."
    ),
    "justificacao_ano_base": (
        "Primeira coorte de ajuizamento observada na amostra filtrada "
        "(secção 3.5.3). Substituir por 2019 se essa for a coorte-base da dissertação."
    ),
    "n_inicial": int(len(quadro)),
    "n_final": int(len(filtrado)),
    "alpha_alfabeto_global": int(len(alfabeto)),
}
import json
(DIRS["processado"] / "parametros_sugeridos.json").write_text(
    json.dumps(sugeridos, ensure_ascii=False, indent=2), encoding="utf-8"
)
filtrado.to_parquet(DIRS["processado"] / "processos_eda.parquet", index=False)
print("Ano-base sugerido:", ano_base_sugerido)
print("N final:", len(filtrado))
print("Coortes:", coortes)
""")
    md(nb, """
## Síntese

- N inicial, período de ajuizamento e composição por grau/classe estão tabelados (APA).
- Limiar mínimo de movimentos **sugerido** nesta corrida: o valor gravado em `parametros_sugeridos.json` (ver secção 8 / `config.py` para confirmação com o orientador).
- α (alfabeto global) e a distribuição de k local condicionam H̄ e o Teorema 2.
- Exclusão listwise documentada no fluxo n inicial → n final.
- Artefacto: `data/processado/processos_eda.parquet`.
""")
    gravar(nb, "02_eda.ipynb")


def nb03():
    nb = novo()
    md(nb, """
# 03 — Construção do Índice de Complexidade Processual

**Secções da dissertação:** 3.5.3 (dimensões e normalização) e 3.5.4
(agregação por média geométrica, sem pesos).

Calcula c(S), H̄, a normalização teórica e o min-max com ano-base fixo, e
agrega \(ICP = \\sqrt{\\bar{c}(S)\\cdot\\bar{H}}\). Grava `indice.parquet`.
""")
    code(nb, SETUP)
    code(nb, """
from IPython.display import display, Markdown
from src.complexidade_lz import complexidade_lz, formatar_historia, historia_exaustiva
from src.entropia import entropia_normalizada, entropia_shannon
from src.normalizacao import (
    alfabeto_global,
    aplicar_minmax_ano_base,
    c_barra,
    estimar_limites_coorte_base,
    limite_teorico_lz,
)
from src.agregacao import agregar_icp, momentos_mpi_coorte_base

parquet = DIRS["processado"] / "processos_eda.parquet"
if not parquet.exists():
    raise FileNotFoundError(
        f"Artefacto em falta: {parquet}. Corra 02_eda.ipynb primeiro."
    )
quadro = pd.read_parquet(parquet)
PARAM = parametros_efectivos(DIRS["processado"])
print(aviso_parametros_pendentes(PARAM))
catalogo = CatalogoAPA(
    DIRS["figuras"], DIRS["tabelas"],
    DIRS["saidas"] / "relatorio_resultados.md",
    reiniciar_relatorio=False,
)
print("N (pós-EDA):", len(quadro))
""")
    md(nb, """
## Dimensão estrutural: c(S) (Kaspar & Schuster, 1987)

Antes de tocar nos dados reais, validamos a implementação contra o exemplo
de Lempel & Ziv (1976, p. 76): a história exaustiva de `0001101001000101`
é `0 · 001 · 10 · 100 · 1000 · 101`, portanto **6** componentes. Se este
assert falhar, o teste unitário também falha — não se ajusta o alvo.
""")
    code(nb, """
exemplo = "0001101001000101"
c_exemplo = complexidade_lz(exemplo)
partes = historia_exaustiva(exemplo)
print("c(S) =", c_exemplo)
print("H_E(S) =", formatar_historia(partes))
assert c_exemplo == 6, "A implementação não reproduz o exemplo da p. 76 — parar."
assert len(partes) == 6
""")
    md(nb, """
A sequência de entrada no DataJud não é binária: são códigos TPU (inteiros).
O algoritmo compara igualdade de símbolos, sem binarizar. Classe e duração
não entram (secção 3.4 / 3.5.4 — sem estimação de pesos).
""")
    code(nb, """
quadro = quadro.copy()
quadro["c_s"] = quadro["sequencia_codigos"].map(complexidade_lz)
desc_c = quadro["c_s"].describe(percentiles=[0.25, 0.50, 0.75])
tab_c = pd.DataFrame({
    "estatística": ["n", "média", "desvio-padrão", "mín", "P25", "mediana", "P75", "máx"],
    "c(S)": [desc_c["count"], desc_c["mean"], desc_c["std"], desc_c["min"],
             desc_c["25%"], desc_c["50%"], desc_c["75%"], desc_c["max"]],
})
catalogo.nova_tabela(
    tab_c,
    titulo="Distribuição da complexidade de Lempel-Ziv c(S) na amostra de construção",
    nota="c(S) é o número de componentes da história exaustiva da sequência de códigos de movimento (Lempel & Ziv, 1976; Kaspar & Schuster, 1987). Ainda sem normalização.",
    nome_ficheiro="tabela_descritivas_c_s",
    interpretacao="c(S) cresce com n mas não linearmente; a normalização pelo Teorema 2 existe precisamente para separar complexidade de mero comprimento.",
)
display(quadro[["numero_processo", "n_movimentos", "c_s", "coorte"]].head())
""")
    md(nb, """
## Dimensão probabilística: H̄ (Pielou)

\(H = -\\sum p_k \\log_2 p_k\), depois \(\\bar{H} = H / \\log_2 k\), k = códigos
distintos *naquele* processo. Se k = 1, H̄ = 0 por convenção (não 0/0):
tramitação mono-símbolo não tem heterogeneidade de tipos (secção 3.5.3).
""")
    code(nb, """
quadro["h_shannon"] = quadro["sequencia_codigos"].map(entropia_shannon)
quadro["h_barra"] = quadro["sequencia_codigos"].map(entropia_normalizada)
tab_h = quadro[["h_shannon", "h_barra", "k_alfabeto_processo"]].describe().T.reset_index().rename(columns={"index": "variável"})
catalogo.nova_tabela(
    tab_h,
    titulo="Entropia de Shannon e equitabilidade de Pielou (H̄) por processo",
    nota="H̄ ∈ [0, 1] por construção. k = 1 ⇒ H̄ = 0 (convenção, secção 3.5.3). Base do logaritmo = 2 (bits).",
    nome_ficheiro="tabela_descritivas_entropia",
    interpretacao="H̄ mede heterogeneidade de tipos, não ordem: dois processos com a mesma multiconjunto de movimentos têm o mesmo H̄ e podem ter c(S) diferente.",
)
""")
    md(nb, """
## Normalização teórica de c(S) (Teorema 2)

Majorante \(c(S) < n / ((1-\\varepsilon_n)\\log_\\alpha n)\), com
\(\\varepsilon_n = 2(1+\\log_\\alpha\\log_\\alpha(\\alpha n))/\\log_\\alpha n\).
α é o alfabeto *global* da amostra, para o bound não herdar duas vezes a
diversidade local (já capturada em H̄). Para n pequeno, ε_n pode ser ≥ 1:
recuamos então a \(n/\\log_\\alpha n\) (Aboy et al., 2006) em vez de inventar um ε.
""")
    code(nb, """
alfa = alfabeto_global(quadro["sequencia_codigos"])
print("α global =", alfa)
quadro["limite_teorico_b_n"] = [
    limite_teorico_lz(int(n), alfa) for n in quadro["n_movimentos"]
]
quadro["c_barra"] = [
    c_barra(int(c), int(n), alfa)
    for c, n in zip(quadro["c_s"], quadro["n_movimentos"])
]
n_clip = int((quadro["c_s"] / quadro["limite_teorico_b_n"] > 1).sum())
print("Processos com c(S)/b(n) > 1 (cortados a 1):", n_clip)
display(quadro[["n_movimentos", "c_s", "limite_teorico_b_n", "c_barra", "h_barra"]].head())
""")
    md(nb, """
## Min-max com ano-base fixo

Os min/máx de c̄ e H̄ da **primeira coorte** reescalam todas as coortes
seguintes. Não há recálculo automático quando chega um painel novo
(secção 3.5.3): se algum valor sair do intervalo, o código *avisa* e
não altera os limites.
""")
    code(nb, """
ano_base = PARAM["ANO_BASE"]
if ano_base is None:
    ano_base = int(quadro["coorte"].min())
    print("ANO_BASE indefinido — a usar a primeira coorte observada:", ano_base)
else:
    ano_base = int(ano_base)
print("Ano-base efectivo:", ano_base)

limites = estimar_limites_coorte_base(quadro, ano_base)
print("Limites da coorte-base:", limites.para_dicionario())
quadro, avisos_mm = aplicar_minmax_ano_base(quadro, limites, clipar=True)
for aviso in avisos_mm:
    print(aviso)

import json
(DIRS["processado"] / "limites_normalizacao.json").write_text(
    json.dumps(limites.para_dicionario(), ensure_ascii=False, indent=2), encoding="utf-8"
)
""")
    md(nb, """
## Agregação: média geométrica (especificação principal)

\(ICP = \\sqrt{\\bar{c}(S)\\cdot\\bar{H}}\). Agregação não compensatória: se uma
dimensão é 0, o índice é 0. Sem pesos (secção 3.5.4). A média aritmética e o
MPI calculam-se já aqui, mas só se interpretam no notebook 05 (robustez).
""")
    code(nb, """
momentos = momentos_mpi_coorte_base(quadro, ano_base)
quadro = agregar_icp(quadro, momentos_mpi=momentos)

tab_icp = quadro[["c_barra_mm", "h_barra_mm", "icp", "icp_aritmetica", "icp_mpi"]].describe().T.reset_index().rename(columns={"index": "variável"})
catalogo.nova_tabela(
    tab_icp,
    titulo="Descritivas das dimensões normalizadas e do ICP (especificação principal e alternativas)",
    nota="c̄_mm e H̄_mm: min-max da coorte-base. ICP = média geométrica. Aritmética e MPI apenas para a secção 3.5.7. Sem pesos.",
    nome_ficheiro="tabela_descritivas_icp",
    interpretacao="O ICP geométrico situa-se entre as duas dimensões e penaliza desequilíbrios; comparar a média do ICP com a da aritmética na robustez (notebook 05).",
)

por_coorte = (
    quadro.groupby("coorte")[["icp", "c_barra_mm", "h_barra_mm", "n_movimentos", "duracao_dias"]]
    .median()
    .reset_index()
)
catalogo.nova_tabela(
    por_coorte,
    titulo="Medianas do ICP e das dimensões por coorte de ajuizamento",
    nota=f"Coorte = ano de ajuizamento. Ano-base da normalização min-max = {ano_base}. A duração em dias é critério externo, não insumo.",
    nome_ficheiro="tabela_medianas_icp_por_coorte",
    interpretacao="A comparabilidade entre painéis é o teste prático do ano-base fixo: medianas que saltam de forma implausível entre coortes adjacentes devem levar a inspeccionar o limiar e a composição por classe, não a reestimar pesos.",
)
""")
    code(nb, """
fig, ax = plt.subplots(figsize=(7.2, 5.0))
sns.scatterplot(
    data=quadro.sample(min(len(quadro), 4000), random_state=42),
    x="c_barra_mm", y="h_barra_mm", hue="coorte",
    palette="colorblind", alpha=0.45, s=18, ax=ax, edgecolor="none",
)
ax.set_xlabel("c̄(S) (min-max, ano-base)")
ax.set_ylabel("H̄ (min-max, ano-base)")
ax.legend(title="Coorte", frameon=False, bbox_to_anchor=(1.02, 1), loc="upper left")
catalogo.nova_figura(
    fig,
    titulo="Relação entre a dimensão estrutural e a dimensão probabilística após normalização",
    nota="Amostra (máx. 4000 pontos) para legibilidade. Especificação principal, min-max da coorte-base.",
    nome_ficheiro="figura_dispersao_c_h",
    interpretacao="Uma nuvem alongada mas não colinear é a geometria esperada de duas dimensões relacionadas e não redundantes (secção 3.5.8); colinearidade estrita invalidaria a média geométrica.",
)

fig, ax = plt.subplots(figsize=(7.2, 4.2))
sns.histplot(quadro["icp"], bins=30, ax=ax, color=sns.color_palette("colorblind")[2], edgecolor="white")
ax.set_xlabel("ICP (média geométrica)")
ax.set_ylabel("Frequência")
catalogo.nova_figura(
    fig,
    titulo="Distribuição do Índice de Complexidade Processual na amostra de construção",
    nota="ICP = √(c̄_mm · H̄_mm). Processos com qualquer dimensão nula concentram-se em ICP = 0.",
    nome_ficheiro="figura_histograma_icp",
    interpretacao="A forma da distribuição (massa em zero vs. sino) diz se a não-compensação da média geométrica está a 'achatar' muitos processos ou a preservar discriminação no miolo.",
)

fig, ax = plt.subplots(figsize=(7.4, 4.4))
sns.boxplot(
    data=quadro, x="coorte", y="icp", ax=ax,
    color=sns.color_palette("colorblind")[0], fliersize=2,
)
ax.set_xlabel("Coorte (ano de ajuizamento)")
ax.set_ylabel("ICP")
catalogo.nova_figura(
    fig,
    titulo="ICP por coorte de ajuizamento (especificação principal)",
    nota="Caixas com medianas e amplitudes interquartis. Sem recálculo dos min/máx entre coortes.",
    nome_ficheiro="figura_boxplot_icp_por_coorte",
    interpretacao="A estabilidade (ou deriva) das caixas ao longo do tempo é o primeiro sinal visual da comparabilidade entre painéis que a secção 3.5.6 monitoriza formalmente.",
)

cols_gravar = [c for c in quadro.columns if c != "movimentos"]
# movimentos ficam no parquet da EDA; o índice guarda a sequência e os scores.
quadro.drop(columns=["assuntos"], errors="ignore").to_parquet(
    DIRS["processado"] / "indice.parquet", index=False
)
print("Gravado indice.parquet com", len(quadro), "processos")
""")
    md(nb, """
## Síntese

- c(S) reproduz o exemplo LZ 1976 (6 componentes) antes de ser aplicado aos dados.
- H̄ ∈ [0, 1]; k = 1 ⇒ 0 por convenção.
- c̄ usa o Teorema 2 com α global; min-max usa ano-base fixo e *avisa* se houver extrapolação.
- ICP = média geométrica; sem pesos. Artefacto: `data/processado/indice.parquet`.
""")
    gravar(nb, "03_construcao_indice.ipynb")


def nb04():
    nb = novo()
    md(nb, """
# 04 — Validação do índice

**Secção da dissertação:** 3.5.8.

Duas frentes testáveis agora: (1) validade de critério externo — duração
observada ~ ICP + controlos, contra um modelo-base sem ICP; (2) validade
convergente/discriminante — Spearman entre c̄ e H̄ (expectativa: *moderada*)
e correlação com proxies procedimentais (códigos TPU em `config.py`, TODO).
""")
    code(nb, SETUP)
    code(nb, """
from IPython.display import display
from src.validacao import (
    indicadores_proxies,
    quadro_coeficientes_apa,
    regressao_criterio_externo,
    validade_convergente_discriminante,
)
from src.config import CODIGOS_MOVIMENTO_PROCEDIMENTAIS

parquet = DIRS["processado"] / "indice.parquet"
if not parquet.exists():
    raise FileNotFoundError(
        f"Artefacto em falta: {parquet}. Corra 03_construcao_indice.ipynb primeiro."
    )
quadro = pd.read_parquet(parquet)
catalogo = CatalogoAPA(
    DIRS["figuras"], DIRS["tabelas"],
    DIRS["saidas"] / "relatorio_resultados.md",
    reiniciar_relatorio=False,
)
print("N:", len(quadro))
print("Proxies configurados (TODO):", {k: v for k, v in CODIGOS_MOVIMENTO_PROCEDIMENTAIS.items()})
""")
    md(nb, """
## Validade de critério externo

A duração (ajuizamento → último movimento) **nunca** entrou no ICP. Um
coeficiente significativo e um ΔR² positivo não «provam» o índice, mas
mostram que ele não é ortogonal a um critério que a literatura associa a
tramitações mais complexas. Controlamos classe, coorte, grau (se variar)
e o comprimento da sequência — este último como covariável, não como
componente (secção 3.4), para o ICP não ser só um proxy de n.
""")
    code(nb, """
resultados = regressao_criterio_externo(quadro)
print(f"n OLS = {resultados['n']}")
print(f"R² base (sem ICP) = {resultados['r2_base']:.4f}")
print(f"R² com ICP        = {resultados['r2_icp']:.4f}")
print(f"ΔR²               = {resultados['delta_r2']:.4f}")
print(resultados["modelo_icp"].summary())

coef = quadro_coeficientes_apa(resultados["modelo_icp"])
# Tabela empírica: não imprimir dezenas de dummies de classe no corpo principal —
# mostramos o ICP, n_movimentos e o intercepto; o CSV completo fica em /outputs.
coef_resumo = coef[coef["Variável"].isin(["Intercept", "icp", "n_movimentos"]) | coef["Variável"].str.startswith("C(coorte)")].copy()
catalogo.nova_tabela(
    coef_resumo,
    titulo="Regressão da duração observada (dias) sobre o ICP, com controlos (coeficientes seleccionados)",
    nota=(
        f"OLS. Variável dependente = duração em dias entre dataAjuizamento e o último movimento. "
        f"Controlos omitidos da tabela (presentes no modelo): classe agrupada (top 8 + Outras)"
        f"{', grau' if resultados['incluir_grau'] else ''}{', tribunal' if resultados['incluir_tribunal'] else ''}. "
        f"R² modelo-base = {resultados['r2_base']:.2f}; R² modelo com ICP = {resultados['r2_icp']:.2f}; "
        f"ΔR² = {resultados['delta_r2']:.2f}. n = {resultados['n']}. "
        "p-valores em formato APA (sem zero à esquerda). CSV completo na pasta de tabelas."
    ),
    nome_ficheiro="tabela_regressao_criterio_externo",
    interpretacao=(
        f"O ΔR² de {resultados['delta_r2']:.3f} é o ganho de poder explicativo atribuível ao ICP "
        "depois de controlar classe, coorte e comprimento da sequência. Um ΔR² residual sugere que "
        "o índice não é redutível a n nem à composição por classe; um ΔR² nulo exigiria rever a arquitectura."
    ),
    casas=3,
)
coef.to_csv(DIRS["tabelas"] / "tabela_regressao_criterio_externo_completa.csv", index=False)

resumo_r2 = pd.DataFrame({
    "modelo": ["Base (classe, coorte, n movimentos)", "Base + ICP"],
    "R²": [resultados["r2_base"], resultados["r2_icp"]],
    "R² ajustado": [resultados["r2_ajustado_base"], resultados["r2_ajustado_icp"]],
    "ΔR²": [np.nan, resultados["delta_r2"]],
    "n": [resultados["n"], resultados["n"]],
})
catalogo.nova_tabela(
    resumo_r2,
    titulo="Comparação do poder explicativo: modelo-base versus modelo com ICP",
    nota="O modelo-base usa apenas controlos (sem o índice). ΔR² = R²(com ICP) − R²(base).",
    nome_ficheiro="tabela_delta_r2_icp",
    interpretacao="Esta é a métrica-resumo da validade de critério externo pedida na secção 3.5.8: o que o ICP acrescenta para além da classe e do comprimento.",
)

fig, ax = plt.subplots(figsize=(7.2, 4.6))
amostra = quadro.dropna(subset=["icp", "duracao_dias"]).sample(min(len(quadro), 4000), random_state=42)
sns.scatterplot(data=amostra, x="icp", y="duracao_dias", ax=ax, alpha=0.35, s=16, edgecolor="none",
                color=sns.color_palette("colorblind")[0])
ax.set_xlabel("ICP")
ax.set_ylabel("Duração observada (dias)")
catalogo.nova_figura(
    fig,
    titulo="Duração processual observada em função do ICP",
    nota="Critério externo; o eixo Y não entra no cálculo do índice. Amostra de no máximo 4000 processos.",
    nome_ficheiro="figura_dispersao_icp_duracao",
    interpretacao="A nuvem deve mostrar associação positiva se o ICP capturar tramitações que, mesmo controlando n, demoram mais; heterocedasticidade é esperada e o OLS aqui é descritivo.",
)
""")
    md(nb, """
## Validade convergente e discriminante

Expectativa teórica: Spearman entre c̄ e H̄ **moderada** (nem ~0 nem ~1).
Os proxies (perícia, carta precatória, incidente, redistribuição, recurso,
suspensão) são códigos TPU em `config.py` e ainda estão por confirmar.
Nesta amostra TRF2, perícia e carta precatória podem ter prevalência zero —
isso limita o teste, não se «inventam» associações.
""")
    code(nb, """
quadro_px = indicadores_proxies(quadro)
prevalencia = (
    quadro_px.filter(regex="^proxy_")
    .mean()
    .rename("prevalencia")
    .reset_index()
    .rename(columns={"index": "proxy"})
)
prevalencia["proxy"] = prevalencia["proxy"].str.removeprefix("proxy_")
prevalencia["n_positivo"] = [
    int(quadro_px[f"proxy_{p}"].sum()) for p in prevalencia["proxy"]
]
catalogo.nova_tabela(
    prevalencia,
    titulo="Prevalência dos proxies procedimentais na amostra de validação",
    nota="Matching por código TPU (config.py) e, complementarmente, por palavra-chave no nome do movimento. Códigos ainda não confirmados com o orientador.",
    nome_ficheiro="tabela_prevalencia_proxies",
    interpretacao="Proxies com prevalência ~0 (ex.: perícia, carta precatória nesta extração TRF2) não permitem testar validade convergente; redistribuição e recurso são os testes informativos.",
)

conv = validade_convergente_discriminante(quadro_px)
catalogo.nova_tabela(
    conv,
    titulo="Correlações de Spearman entre dimensões, ICP e proxies procedimentais",
    nota="Expectativa: correlação moderada entre c̄ e H̄ (secção 3.5.8). p-valores em formato APA. Proxies binários (0/1).",
    nome_ficheiro="tabela_validade_convergente",
    interpretacao="O par c̄—H̄ é o teste discriminante interno das duas dimensões. Correlações positivas com redistribuição/recurso/suspensão sustentam validade convergente; ausências de associação nos proxies raros não falsificam o índice.",
    casas=3,
)

rho_dim = float(conv.loc[conv["par"] == "c̄(S) — H̄", "rho_spearman"].iloc[0])
print(f"Spearman c̄ vs H̄ = {rho_dim:.3f}")
""")
    md(nb, """
## Síntese

- Modelo-base vs. modelo com ICP: ΔR² reportado na tabela correspondente.
- Spearman entre dimensões: ver tabela de validade convergente (expectativa: moderada).
- Proxies TPU ainda são TODO em `config.py`; prevalências nulas estão documentadas, não escondidas.
""")
    gravar(nb, "04_validacao.ipynb")


def nb05():
    nb = novo()
    md(nb, """
# 05 — Robustez, sensibilidade e monitorização dinâmica

**Secções da dissertação:** 3.5.6 (dinâmica entre dimensões ao longo das
coortes) e 3.5.7 (sensibilidade a limiar, normalização e agregação).

Não se estimam pesos em nenhuma variante. A hierarquização compara-se por
Spearman dos *rankings dentro de cada coorte*.
""")
    code(nb, SETUP)
    code(nb, """
from IPython.display import display
from src.robustez import tabela_robustez
from src.monitorizacao_dinamica import avaliar_alerta, correlacao_dimensoes_por_coorte
from src.config import LIMIAR_CORRELACAO_DIMENSOES, LIMIARES_ROBUSTEZ

parquet = DIRS["processado"] / "indice.parquet"
eda = DIRS["processado"] / "processos_eda.parquet"
if not parquet.exists() or not eda.exists():
    raise FileNotFoundError(
        "Artefactos em falta. Corra 02_eda.ipynb e 03_construcao_indice.ipynb primeiro."
    )
indice = pd.read_parquet(parquet)
bruto = pd.read_parquet(eda)
PARAM = parametros_efectivos(DIRS["processado"])
ano_base = int(PARAM["ANO_BASE"] or indice["coorte"].min())
limiar = int(PARAM["LIMIAR_MINIMO_MOVIMENTOS"])
catalogo = CatalogoAPA(
    DIRS["figuras"], DIRS["tabelas"],
    DIRS["saidas"] / "relatorio_resultados.md",
    reiniciar_relatorio=False,
)
print("Ano-base:", ano_base, "Limiar principal:", limiar)
""")
    md(nb, """
## Sensibilidade (secção 3.5.7)

Variamos um factor de cada vez: limiar ∈ {3, 5, 8, 12}; normalização
intra-processo ligada/desligada; agregação geométrica / aritmética / MPI.
A métrica é a correlação de Spearman entre o ranking da especificação
principal e o de cada alternativa, *dentro de cada coorte*.
""")
    code(nb, """
rob = tabela_robustez(
    bruto,
    ano_base=ano_base,
    limiar_principal=limiar,
    limiares=LIMIARES_ROBUSTEZ,
)
rob["p (APA)"] = [__import__("src.graficos_apa", fromlist=["formatar_p"]).formatar_p(p) for p in rob["p"]]
catalogo.nova_tabela(
    rob.drop(columns=["p"]),
    titulo="Correlação de Spearman entre o ranking da especificação principal e cada alternativa",
    nota=(
        "Principal = limiar da EDA, normalização intra-processo (Teorema 2 + Pielou) e média geométrica. "
        "Cada linha varia um único factor. Rankings calculados dentro de cada coorte (1 = maior ICP). "
        f"Limiares testados: {list(LIMIARES_ROBUSTEZ)}."
    ),
    nome_ficheiro="tabela_robustez_rankings",
    interpretacao="Spearman de ranking próximo de 1 indica que a hierarquização dos processos é estável à escolha operacional; quedas acentuadas identificam o factor a que o índice é mais sensível (limiar, normalização ou agregação).",
    casas=3,
)

fig, ax = plt.subplots(figsize=(7.6, 4.6))
plot = rob.copy()
sns.barplot(
    data=plot, y="especificação", x="rho_spearman_ranking",
    ax=ax, color=sns.color_palette("colorblind")[0],
)
ax.set_xlabel("Spearman do ranking vs. especificação principal")
ax.set_ylabel("")
ax.set_xlim(0, 1.05)
ax.axvline(0.90, color="gray", linestyle="--", linewidth=1)
catalogo.nova_figura(
    fig,
    titulo="Estabilidade da hierarquização do ICP sob especificações alternativas",
    nota="A linha vertical em .90 é um referencial visual, não um limiar inferencial. Barras = Spearman de rankings intra-coorte.",
    nome_ficheiro="figura_barras_robustez",
    interpretacao="Se todas as barras ficarem altas, o capítulo de resultados pode tratar o ICP como robusto às decisões ainda em aberto; se a agregação MPI ou o limiar 3 se desviarem, isso deve ser discutido explicitamente com o orientador.",
)
""")
    md(nb, """
## Monitorização da dinâmica (secção 3.5.6)

Spearman(c̄, H̄) em cada coorte, comparado com o valor da coorte-base. A
zona sombreada acima de 0,90 (configurável) marca o limiar em que se
recomendaria rever a arquitectura — não recalibrar pesos, porque não os há.
""")
    code(nb, """
corr = correlacao_dimensoes_por_coorte(indice)
corr = avaliar_alerta(corr, ano_base=ano_base, limiar=LIMIAR_CORRELACAO_DIMENSOES)
corr["p (APA)"] = [__import__("src.graficos_apa", fromlist=["formatar_p"]).formatar_p(p) for p in corr["p"]]
catalogo.nova_tabela(
    corr.drop(columns=["p"]),
    titulo="Correlação de Spearman entre c̄(S) e H̄ em cada coorte de ajuizamento",
    nota=(
        f"Coorte-base = {ano_base}. Limiar de alerta de revisão da arquitectura = "
        f"{LIMIAR_CORRELACAO_DIMENSOES:.2f} (config.py, secção 3.5.6). "
        "alerta_revisao = True se rho ≥ limiar."
    ),
    nome_ficheiro="tabela_correlacao_dimensoes_por_coorte",
    interpretacao="Uma correlação estável e moderada ao longo das coortes sustenta a arquitectura de duas dimensões. Um salto para valores próximos de 1 na coorte mais recente é o sinal de alarme da secção 3.5.6.",
    casas=3,
)

fig, ax = plt.subplots(figsize=(7.4, 4.4))
ax.plot(corr["coorte"], corr["rho_spearman"], marker="o", color=sns.color_palette("colorblind")[0])
rho_base = float(corr["rho_coorte_base"].iloc[0])
ax.axhline(rho_base, color="black", linestyle="--", linewidth=1, label=f"Coorte-base ({ano_base})")
ax.axhline(LIMIAR_CORRELACAO_DIMENSOES, color="gray", linestyle=":", linewidth=1)
ax.axhspan(LIMIAR_CORRELACAO_DIMENSOES, 1.02, color="0.85", alpha=0.5, label="Zona de revisão da arquitectura")
ax.set_xlabel("Coorte (ano de ajuizamento)")
ax.set_ylabel("Spearman entre c̄(S) e H̄")
ax.set_ylim(-0.05, 1.02)
ax.legend(frameon=False, loc="lower right")
catalogo.nova_figura(
    fig,
    titulo="Evolução da correlação entre as duas dimensões do ICP ao longo das coortes",
    nota=(
        f"Linha a tracejado = Spearman na coorte-base ({ano_base}). "
        f"Zona sombreada = ρ ≥ {LIMIAR_CORRELACAO_DIMENSOES:.2f}, limiar configurável acima do qual se recomenda rever a arquitectura (secção 3.5.6)."
    ),
    nome_ficheiro="figura_dinamica_correlacao_dimensoes",
    interpretacao="O gráfico é o instrumento de monitorização contínua do índice: como não há pesos, o que se vigia é a relação entre dimensões, não um vector de ponderadores.",
)

print("Relatório técnico:", DIRS["saidas"] / "relatorio_resultados.md")
print("Figuras:", list(DIRS["figuras"].glob("*.png")))
""")
    md(nb, """
## Síntese

- Robustez: tabela de Spearman de rankings (limiar / normalização / agregação).
- Dinâmica: Spearman(c̄, H̄) por coorte com linha de referência na coorte-base e zona de alerta a 0,90.
- Parâmetros em `config.py` continuam pendentes de validação com o orientador; nada disto é a versão final da dissertação.
- Relatório de apoio à escrita: `outputs/relatorio_resultados.md`.
""")
    gravar(nb, "05_robustez_e_dinamica.ipynb")


if __name__ == "__main__":
    nb01()
    nb02()
    nb03()
    nb04()
    nb05()
