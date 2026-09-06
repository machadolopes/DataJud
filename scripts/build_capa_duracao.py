"""
Constrói data/processos_capa_duracao.parquet (1 linha / processo).

Fonte: JSONL Datajud TRF2 (Zenodo 22070436), em streaming — não grava o JSONL.
Alvo: dias entre a distribuição (mov. 26, senão ajuizamento) e a baixa 22.
Features: só capa no instante da distribuição.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import urllib.request

ZENODO_JSONL = (
    "https://zenodo.org/api/records/22070436/files/"
    "processos_trf2_baixa_definitiva_2025_filtro22.jsonl/content"
)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processos_capa_duracao.parquet"
CHUNK_ROWS = 20_000


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_ajuizamento(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    iso = parse_iso(text)
    if iso is not None:
        return iso
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 14:
        try:
            return datetime.strptime(digits[:14], "%Y%m%d%H%M%S").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            return None
    if len(digits) >= 8:
        try:
            return datetime.strptime(digits[:8], "%Y%m%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def mov_codigo(mov: dict) -> int | None:
    codigo = mov.get("codigo")
    if codigo is None and isinstance(mov.get("movimentoNacional"), dict):
        codigo = mov["movimentoNacional"].get("codigo")
    try:
        return int(codigo) if codigo is not None else None
    except (TypeError, ValueError):
        return None


def extract_row(reg: dict) -> dict | None:
    movimentos = reg.get("movimentos") or []
    dt_22 = None
    dt_26 = None
    orgao_26: dict = {}
    for mov in movimentos:
        codigo = mov_codigo(mov)
        dt = parse_iso(mov.get("dataHora"))
        if codigo == 22 and dt is not None:
            if 2025 <= dt.year <= 2025:
                dt_22 = dt
        if codigo == 26 and dt_26 is None and dt is not None:
            dt_26 = dt
            orgao_26 = mov.get("orgaoJulgador") or {}

    if dt_22 is None:
        return None

    dt_ajuiz = parse_ajuizamento(reg.get("dataAjuizamento"))
    dt_inicio = dt_26 or dt_ajuiz
    if dt_inicio is None:
        return None
    duracao = (dt_22 - dt_inicio).total_seconds() / 86400.0
    if duracao <= 0:
        return None

    orgao_header = reg.get("orgaoJulgador") or {}
    classe = reg.get("classe") or {}
    sistema = reg.get("sistema") or {}
    formato = reg.get("formato") or {}
    assuntos = reg.get("assuntos") or []
    primeiro = assuntos[0] if assuntos else {}

    orgao_codigo = orgao_26.get("codigo")
    orgao_nome = orgao_26.get("nome")
    if orgao_codigo is None:
        orgao_codigo = orgao_header.get("codigo")
        orgao_nome = orgao_header.get("nome")
    try:
        orgao_codigo = int(orgao_codigo) if orgao_codigo is not None else None
    except (TypeError, ValueError):
        orgao_codigo = None

    mun = orgao_header.get("codigoMunicipioIBGE")
    try:
        mun = int(mun) if mun is not None else None
    except (TypeError, ValueError):
        mun = None

    return {
        "processo_id": reg.get("id"),
        "numero_processo": reg.get("numeroProcesso"),
        "grau": reg.get("grau"),
        "classe_codigo": classe.get("codigo"),
        "classe_nome": classe.get("nome"),
        "assunto_codigo": primeiro.get("codigo"),
        "assunto_nome": primeiro.get("nome"),
        "n_assuntos": len(assuntos),
        "orgao_codigo": orgao_codigo,
        "orgao_nome": orgao_nome,
        "municipio_ibge": mun,
        "sistema_codigo": sistema.get("codigo"),
        "formato_codigo": formato.get("codigo"),
        "dt_ajuizamento": dt_ajuiz,
        "dt_distribuicao": dt_26,
        "dt_baixa_22": dt_22,
        "inicio_fonte": "distribuicao" if dt_26 is not None else "ajuizamento",
        "duracao_dias": duracao,
    }


def iter_jsonl(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "datajud-mscba/0.1"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        for raw in resp:
            line = raw.decode("utf-8", errors="replace").strip()
            if line:
                yield json.loads(line)


def flush(buffer: list[dict], writer: pq.ParquetWriter | None) -> pq.ParquetWriter:
    table = pa.Table.from_pandas(pd.DataFrame(buffer), preserve_index=False)
    if writer is None:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        writer = pq.ParquetWriter(OUT, table.schema, compression="snappy")
    else:
        table = table.cast(writer.schema)
    writer.write_table(table)
    return writer


def main() -> int:
    writer = None
    buffer: list[dict] = []
    lidos = 0
    gravados = 0
    print(f"A ler {ZENODO_JSONL}", flush=True)
    for reg in iter_jsonl(ZENODO_JSONL):
        lidos += 1
        row = extract_row(reg)
        if row is not None:
            buffer.append(row)
        if len(buffer) >= CHUNK_ROWS:
            writer = flush(buffer, writer)
            gravados += len(buffer)
            buffer = []
            print(f"  lidos={lidos:,} gravados={gravados:,}", flush=True)
    if buffer:
        writer = flush(buffer, writer)
        gravados += len(buffer)
    if writer is not None:
        writer.close()
    print(f"Concluído: lidos={lidos:,} gravados={gravados:,} → {OUT}", flush=True)
    return 0 if gravados else 1


if __name__ == "__main__":
    sys.exit(main())
