"""
Carregamento e parsing do ficheiro .jsonl do DataJud.

Papel no pipeline
-----------------
Primeiro contacto com os dados brutos (secção 3.5.1). Não assume a priori
se cada linha do .jsonl é um processo ou uma página Elasticsearch
(`hits.hits[]._source`) — detecta e adapta o parser.

Campos no ficheiro real da API pública DataJud / TRF2 (confirmados no
notebook 01; nomes oficiais da API, não traduzidos):

- `numeroProcesso`, `id`
- `classe` {codigo, nome}
- `assuntos` [{codigo, nome}]
- `movimentos` [{codigo, nome, dataHora, complementosTabelados, orgaoJulgador}]
  Campo central de todo o pipeline (secção 3.5.3).
- `grau`, `tribunal`, `orgaoJulgador` {codigo, nome, codigoMunicipioIBGE}
- `formato` {codigo, nome}
- `dataAjuizamento` (string compacta YYYYMMDDHHMMSS nesta extração)
- `dataHoraUltimaAtualizacao`, `@timestamp`

Diferenças face à documentação genérica:
- `dataAjuizamento` NÃO vem em ISO-8601; vem como `YYYYMMDDHHMMSS`.
- `movimentos[].dataHora` vem em ISO-8601 com `Z`.
- Nesta extração TRF2 o código de movimento está em `movimentos[].codigo`
  (não em `movimentoNacional.codigo`); o parser aceita ambos.
- Cada linha do .jsonl corresponde a UM processo (`_source` já extraído
  pelo notebook de extração), não a uma página da API.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from src.sequencias import analisar_data


CAMPOS_ESPERADOS: tuple[str, ...] = (
    "numeroProcesso",
    "classe",
    "assuntos",
    "movimentos",
    "grau",
    "tribunal",
    "orgaoJulgador",
    "formato",
    "dataAjuizamento",
    "dataHoraUltimaAtualizacao",
)


def localizar_jsonl(dir_dados: Path) -> Path:
    """
    Encontra o .jsonl de trabalho em /data.

    Prefere ficheiros cujo nome contenha 'datajud' ou 'processo'. Se houver
    vários, escolhe o maior (a extração completa). Não versionar estes
    ficheiros no git.
    """
    candidatos = sorted(dir_dados.glob("*.jsonl"))
    if not candidatos:
        raise FileNotFoundError(
            f"Nenhum ficheiro .jsonl em {dir_dados}. "
            "Coloque a extração DataJud nessa pasta "
            "(ex.: processos_trf2_baixa_definitiva_2025.jsonl)."
        )
    preferidos = [
        c for c in candidatos
        if any(token in c.name.lower() for token in ("datajud", "processo", "trf"))
    ]
    lista = preferidos or candidatos
    return max(lista, key=lambda p: p.stat().st_size)


def caminhos_chaves(obj: Any, prefixo: str = "") -> list[str]:
    """Lista recursiva de caminhos de chaves (ex.: `movimentos[].codigo`)."""
    encontrados: list[str] = []
    if isinstance(obj, dict):
        if not obj and prefixo:
            encontrados.append(prefixo)
        for chave, valor in obj.items():
            caminho = f"{prefixo}.{chave}" if prefixo else str(chave)
            encontrados.append(caminho)
            encontrados.extend(caminhos_chaves(valor, caminho))
    elif isinstance(obj, list):
        caminho_lista = f"{prefixo}[]" if prefixo else "[]"
        encontrados.append(caminho_lista)
        for item in obj[:5]:
            encontrados.extend(caminhos_chaves(item, caminho_lista))
    return encontrados


def parece_pagina_elasticsearch(obj: dict[str, Any]) -> bool:
    """True se a linha é uma resposta ES (hits.hits), não um processo."""
    hits = obj.get("hits")
    if isinstance(hits, dict) and isinstance(hits.get("hits"), list):
        return True
    if isinstance(obj.get("hits"), list) and obj.get("hits"):
        primeiro = obj["hits"][0]
        if isinstance(primeiro, dict) and ("_source" in primeiro or "movimentos" in primeiro):
            return True
    return False


def parece_processo(obj: dict[str, Any]) -> bool:
    """True se a linha já é um processo DataJud (tem movimentos ou numeroProcesso)."""
    if not isinstance(obj, dict):
        return False
    if "movimentos" in obj or "numeroProcesso" in obj:
        return True
    if isinstance(obj.get("_source"), dict):
        return parece_processo(obj["_source"])
    return False


def extrair_processos_de_linha(obj: dict[str, Any]) -> list[dict[str, Any]]:
    """Normaliza uma linha JSON para uma lista de processos."""
    if parece_pagina_elasticsearch(obj):
        hits = obj["hits"]["hits"] if isinstance(obj.get("hits"), dict) else obj.get("hits", [])
        processos = []
        for hit in hits:
            if not isinstance(hit, dict):
                continue
            fonte = hit.get("_source", hit)
            if isinstance(fonte, dict):
                processos.append(fonte)
        return processos
    if isinstance(obj.get("_source"), dict) and "movimentos" in obj["_source"]:
        return [obj["_source"]]
    if parece_processo(obj):
        return [obj]
    return []


def iterar_processos_jsonl(
    caminho: Path,
    max_linhas: int | None = None,
) -> Iterator[dict[str, Any]]:
    """Gera processos a partir do .jsonl, linha a linha (streaming)."""
    with caminho.open(encoding="utf-8") as ficheiro:
        for indice, linha in enumerate(ficheiro):
            if max_linhas is not None and indice >= max_linhas:
                break
            texto = linha.strip()
            if not texto:
                continue
            obj = json.loads(texto)
            if not isinstance(obj, dict):
                continue
            yield from extrair_processos_de_linha(obj)


def _campo_aninhado(obj: dict[str, Any], chave: str, subchave: str) -> Any:
    bloco = obj.get(chave)
    if isinstance(bloco, dict):
        return bloco.get(subchave)
    return None


def aplainar_processo(obj: dict[str, Any]) -> dict[str, Any]:
    """
    Projecta um processo DataJud num dicionário tabular.

    A lista `movimentos` é preservada (insumo do índice). Classe, tribunal,
    grau, órgão e formato saem como colunas de controlo / coorte — não
    entram no ICP (secção 3.4).
    """
    assuntos = obj.get("assuntos") if isinstance(obj.get("assuntos"), list) else []
    movimentos = obj.get("movimentos") if isinstance(obj.get("movimentos"), list) else []
    data_ajuizamento_bruta = obj.get("dataAjuizamento")
    data_ultima_bruta = obj.get("dataHoraUltimaAtualizacao")
    return {
        "id_datajud": obj.get("id"),
        "numero_processo": obj.get("numeroProcesso"),
        "tribunal": obj.get("tribunal"),
        "grau": obj.get("grau"),
        "classe_codigo": _campo_aninhado(obj, "classe", "codigo"),
        "classe_nome": _campo_aninhado(obj, "classe", "nome"),
        "orgao_codigo": _campo_aninhado(obj, "orgaoJulgador", "codigo"),
        "orgao_nome": _campo_aninhado(obj, "orgaoJulgador", "nome"),
        "formato_codigo": _campo_aninhado(obj, "formato", "codigo"),
        "formato_nome": _campo_aninhado(obj, "formato", "nome"),
        "nivel_sigilo": obj.get("nivelSigilo"),
        "data_ajuizamento_bruta": data_ajuizamento_bruta,
        "data_ajuizamento": analisar_data(data_ajuizamento_bruta),
        "data_ultima_atualizacao_bruta": data_ultima_bruta,
        "data_ultima_atualizacao": analisar_data(data_ultima_bruta),
        "n_assuntos": len(assuntos),
        "assunto_principal_codigo": (
            assuntos[0].get("codigo") if assuntos and isinstance(assuntos[0], dict) else None
        ),
        "assunto_principal_nome": (
            assuntos[0].get("nome") if assuntos and isinstance(assuntos[0], dict) else None
        ),
        "n_movimentos_bruto": len(movimentos),
        "movimentos": movimentos,
        "assuntos": assuntos,
    }


def carregar_processos(
    caminho: Path,
    max_linhas: int | None = None,
) -> pd.DataFrame:
    """Lê o .jsonl e devolve um DataFrame (um processo por linha)."""
    registos = [aplainar_processo(p) for p in iterar_processos_jsonl(caminho, max_linhas)]
    quadro = pd.DataFrame(registos)
    if quadro.empty:
        return quadro
    if "numero_processo" in quadro.columns:
        quadro = quadro.drop_duplicates(subset=["numero_processo"], keep="first")
    return quadro.reset_index(drop=True)


def diagnostico_cobertura(
    caminho: Path,
    n_amostra_linhas: int = 20,
    campos_esperados: Sequence[str] = CAMPOS_ESPERADOS,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Conta linhas, classifica o formato (processo vs. página ES) e mede a
    presença/ausência dos campos esperados no conjunto completo.
    """
    n_linhas = 0
    n_processos = 0
    n_paginas_es = 0
    n_linhas_nao_reconhecidas = 0
    presenca: Counter[str] = Counter()
    caminhos: Counter[str] = Counter()
    amostra: list[dict[str, Any]] = []

    with caminho.open(encoding="utf-8") as ficheiro:
        for linha in ficheiro:
            texto = linha.strip()
            if not texto:
                continue
            n_linhas += 1
            obj = json.loads(texto)
            if not isinstance(obj, dict):
                n_linhas_nao_reconhecidas += 1
                continue
            if n_linhas <= n_amostra_linhas:
                amostra.append(
                    {
                        "indice_linha": n_linhas,
                        "chaves_topo": sorted(obj.keys()),
                        "n_chaves_topo": len(obj),
                        "e_pagina_es": parece_pagina_elasticsearch(obj),
                        "e_processo": parece_processo(obj),
                    }
                )
            if parece_pagina_elasticsearch(obj):
                n_paginas_es += 1
            processos = extrair_processos_de_linha(obj)
            if not processos:
                n_linhas_nao_reconhecidas += 1
                continue
            for processo in processos:
                n_processos += 1
                for campo in campos_esperados:
                    if processo.get(campo) not in (None, "", [], {}):
                        presenca[campo] += 1
                for caminho_chave in set(caminhos_chaves(processo)):
                    caminhos[caminho_chave] += 1

    cobertura = pd.DataFrame(
        {
            "campo": list(campos_esperados),
            "n_presente": [presenca[c] for c in campos_esperados],
        }
    )
    cobertura["n_ausente"] = n_processos - cobertura["n_presente"]
    cobertura["pct_presente"] = (
        100.0 * cobertura["n_presente"] / n_processos if n_processos else 0.0
    )
    meta = {
        "n_linhas_jsonl": n_linhas,
        "n_processos": n_processos,
        "n_paginas_elasticsearch": n_paginas_es,
        "n_linhas_nao_reconhecidas": n_linhas_nao_reconhecidas,
        "formato": (
            "pagina_elasticsearch"
            if n_paginas_es == n_linhas and n_linhas > 0
            else "processo_por_linha"
            if n_paginas_es == 0
            else "misto"
        ),
        "amostra_linhas": amostra,
        "caminhos_chaves": caminhos,
    }
    return cobertura, meta
