#!/usr/bin/env python3
"""Phase 1 discovery: inspect raw compressed dumps of federal book-purchase data.

Reads ZIPs (and loose tabular files) from SOURCE_DIR, samples members, and
prints schema, null counts, and first rows. Column names are discovered at
runtime — none are required.

Does not filter NCM, write parquet, or build Streamlit/Quarto/Actions.

Usage:
    python 01_explore.py
    SOURCE_DIR=/path/to/Source python 01_explore.py
    python 01_explore.py --source-dir ./Source --sample-files 3 --sample-rows 5
"""

from __future__ import annotations

import argparse
import io
import os
import sys
import zipfile
from pathlib import Path
from typing import Any

DEFAULT_SOURCE_DIR = (
    r"G:\O meu disco\Main\Business\TagusData\Projeto ComprasLivrosGov\Source"
)
RELATIVE_FALLBACKS = (Path("Source"), Path("data/raw"))
TABULAR_SUFFIXES = (".csv", ".tsv", ".txt", ".parquet", ".pq")
ARCHIVE_SUFFIXES = (".zip",)
SAMPLE_FILES_DEFAULT = 3
SAMPLE_ROWS_DEFAULT = 5
MEMBERS_PER_ZIP_DEFAULT = 5
N_ROWS_FOR_PROFILE = 50_000

# Portal da Transparência dumps are typically Latin-1 + semicolon.
# Tried in order; first successful parse wins. Not a required-column list.
ENCODINGS = ("utf-8-sig", "utf-8", "latin-1", "cp1252")
SEPARATORS = (None, ";", ",", "\t", "|")


def _try_import_polars():
    try:
        import polars as pl  # type: ignore

        return pl
    except ImportError:
        return None


def _try_import_duckdb():
    try:
        import duckdb  # type: ignore

        return duckdb
    except ImportError:
        return None


def linux_drive_aliases(win_path: str) -> list[Path]:
    """Map a Windows G: path to common Linux / Google Drive mount points."""
    cleaned = win_path.replace("\\", "/")
    if len(cleaned) >= 2 and cleaned[1] == ":":
        drive = cleaned[0].lower()
        rest = cleaned[2:].lstrip("/")
        return [
            Path(f"/mnt/{drive}") / rest,
            Path(f"/media/{drive}") / rest,
            Path("/mnt/g") / rest,
            Path("/mnt/google") / rest,
        ]
    return []


def resolve_source_dir(cli_value: str | None) -> Path | None:
    """SOURCE_DIR env, --source-dir, default G: path, then ./Source or data/raw."""
    candidates: list[Path] = []
    if cli_value:
        candidates.append(Path(cli_value).expanduser())
    env = os.environ.get("SOURCE_DIR")
    if env:
        candidates.append(Path(env).expanduser())
    candidates.append(Path(DEFAULT_SOURCE_DIR))
    candidates.extend(linux_drive_aliases(DEFAULT_SOURCE_DIR))
    cwd = Path.cwd()
    for rel in RELATIVE_FALLBACKS:
        candidates.append(cwd / rel)
        candidates.append(rel)

    seen: set[str] = set()
    unique: list[Path] = []
    for path in candidates:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)

    for path in unique:
        if path.is_dir():
            return path.resolve()
    return None


def list_candidate_paths(tried: list[str]) -> None:
    print("SOURCE_DIR not found. Paths tried:")
    for item in tried:
        print(f"  - {item}")


def collect_raw_files(source_dir: Path) -> list[Path]:
    files = [
        p
        for p in source_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in ARCHIVE_SUFFIXES + TABULAR_SUFFIXES
    ]
    files.sort(key=lambda p: (p.suffix.lower() != ".zip", p.name.lower()))
    return files


def is_tabular_name(name: str) -> bool:
    lower = name.lower()
    return any(lower.endswith(sfx) for sfx in TABULAR_SUFFIXES)


def engine_banner() -> str:
    pl = _try_import_polars()
    if pl is not None:
        return f"polars {pl.__version__}"
    duckdb = _try_import_duckdb()
    if duckdb is not None:
        return f"duckdb {duckdb.__version__} (polars unavailable)"
    return "stdlib csv (polars and duckdb unavailable)"


def _polars_read_csv(pl, raw: bytes, encoding: str, sep: str | None, n_rows: int, infer: int):
    kwargs: dict[str, Any] = {
        "encoding": encoding,
        "n_rows": n_rows,
        "infer_schema_length": infer,
        "try_parse_dates": infer > 0,
        "ignore_errors": True,
    }
    if sep is not None:
        kwargs["separator"] = sep
    else:
        kwargs["separator"] = None
    return pl.read_csv(io.BytesIO(raw), **kwargs)


def _annotate_inferred_dtypes(pl, df_str, raw: bytes, encoding: str, sep: str | None, n_rows: int):
    """Guess dtypes without dropping overflowed IDs (e.g. 44-digit chave)."""
    try:
        df_inf = _polars_read_csv(pl, raw, encoding, sep, n_rows, infer=10_000)
    except Exception:  # noqa: BLE001
        return {c: "String" for c in df_str.columns}, []
    notes: list[str] = []
    dtypes: dict[str, str] = {}
    for col in df_str.columns:
        as_str_nulls = int(df_str[col].null_count())
        if col not in df_inf.columns:
            dtypes[col] = "String"
            continue
        as_inf_nulls = int(df_inf[col].null_count())
        extra = as_inf_nulls - as_str_nulls
        if extra > 0:
            dtypes[col] = "String"
            notes.append(
                f"{col}: inferred {df_inf[col].dtype} added {extra} nulls "
                f"(overflow/parse loss) — keep String"
            )
        else:
            dtypes[col] = str(df_inf[col].dtype)
    return dtypes, notes


def read_bytes_with_polars(raw: bytes, name: str, n_rows: int):
    pl = _try_import_polars()
    if pl is None:
        return None, None
    lower = name.lower()
    if lower.endswith((".parquet", ".pq")):
        df = pl.read_parquet(io.BytesIO(raw)).head(n_rows)
        return df, {"format": "parquet"}

    last_err: Exception | None = None
    for encoding in ENCODINGS:
        for sep in SEPARATORS:
            try:
                # All-string first so long numeric IDs are not nulled by Int128 overflow.
                df = _polars_read_csv(pl, raw, encoding, sep, n_rows, infer=0)
                if df.width == 0:
                    continue
                guessed, notes = _annotate_inferred_dtypes(
                    pl, df, raw, encoding, sep, n_rows
                )
                meta = {
                    "format": "csv",
                    "encoding": encoding,
                    "separator": sep if sep is not None else "inferred",
                    "inferred_dtypes": guessed,
                    "dtype_notes": notes,
                }
                return df, meta
            except Exception as exc:  # noqa: BLE001 — try next encoding/sep
                last_err = exc
                continue
    if last_err is not None:
        print(f"    polars failed to parse {name!r}: {last_err}")
    return None, None


def read_bytes_with_duckdb(raw: bytes, name: str, n_rows: int):
    duckdb = _try_import_duckdb()
    if duckdb is None:
        return None, None
    con = duckdb.connect(database=":memory:")
    lower = name.lower()
    try:
        if lower.endswith((".parquet", ".pq")):
            rel = con.from_parquet(io.BytesIO(raw)).limit(n_rows)
            return rel.pl() if hasattr(rel, "pl") else rel.df(), {"format": "parquet"}
        for encoding in ENCODINGS:
            for sep in (";", ",", "\t", "|"):
                try:
                    rel = con.read_csv(
                        io.BytesIO(raw),
                        header=True,
                        sep=sep,
                        encoding=encoding,
                        sample_size=10_000,
                    ).limit(n_rows)
                    df = rel.pl() if hasattr(rel, "pl") else rel.df()
                    width = df.width if hasattr(df, "width") else len(df.columns)
                    if width == 0:
                        continue
                    return df, {
                        "format": "csv",
                        "encoding": encoding,
                        "separator": sep,
                    }
                except Exception:  # noqa: BLE001
                    continue
    finally:
        con.close()
    return None, None


def read_bytes_with_stdlib(raw: bytes, name: str, n_rows: int):
    import csv

    lower = name.lower()
    if lower.endswith((".parquet", ".pq")):
        print(f"    skip {name}: parquet requires polars or duckdb")
        return None, None

    last_err: Exception | None = None
    for encoding in ENCODINGS:
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError as exc:
            last_err = exc
            continue
        sample = text[: 64 * 1024]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=";,|\t")
            sep = dialect.delimiter
        except csv.Error:
            sep = ";" if text.count(";") >= text.count(",") else ","
        reader = csv.reader(io.StringIO(text), delimiter=sep)
        try:
            header = next(reader)
        except StopIteration:
            continue
        rows = []
        for i, row in enumerate(reader):
            if i >= n_rows:
                break
            rows.append(row)
        # Normalize ragged rows
        width = len(header)
        norm = [r + [""] * (width - len(r)) for r in rows]
        pl = _try_import_polars()
        if pl is not None:
            df = pl.DataFrame({h: [r[j] for r in norm] for j, h in enumerate(header)})
        else:
            df = {"columns": header, "rows": norm}
        return df, {"format": "csv", "encoding": encoding, "separator": sep}
    if last_err is not None:
        print(f"    stdlib failed to parse {name!r}: {last_err}")
    return None, None


def read_tabular_bytes(raw: bytes, name: str, n_rows: int):
    df, meta = read_bytes_with_polars(raw, name, n_rows)
    if df is not None:
        return df, meta
    df, meta = read_bytes_with_duckdb(raw, name, n_rows)
    if df is not None:
        return df, meta
    return read_bytes_with_stdlib(raw, name, n_rows)


def df_columns(df) -> list[str]:
    if hasattr(df, "columns"):
        return [str(c) for c in df.columns]
    if isinstance(df, dict):
        return list(df.get("columns") or [])
    return []


def df_dtypes(df) -> list[tuple[str, str]]:
    if hasattr(df, "schema"):
        return [(str(k), str(v)) for k, v in df.schema.items()]
    if hasattr(df, "dtypes"):
        cols = df_columns(df)
        return [(c, str(t)) for c, t in zip(cols, df.dtypes)]
    return [(c, "unknown") for c in df_columns(df)]


def df_null_counts(df) -> list[tuple[str, int]]:
    if hasattr(df, "null_count"):
        nc = df.null_count()
        cols = df_columns(df)
        if hasattr(nc, "row"):
            vals = nc.row(0)
            return list(zip(cols, [int(v) for v in vals]))
    if hasattr(df, "isna"):
        counts = df.isna().sum()
        return [(str(c), int(counts[c])) for c in df.columns]
    if isinstance(df, dict):
        cols = df.get("columns") or []
        rows = df.get("rows") or []
        out = []
        for i, c in enumerate(cols):
            n = sum(1 for r in rows if i >= len(r) or r[i] in ("", None))
            out.append((c, n))
        return out
    return []


def df_n_rows(df) -> int:
    if hasattr(df, "height"):
        return int(df.height)
    if hasattr(df, "__len__"):
        try:
            return int(len(df))
        except TypeError:
            return 0
    if isinstance(df, dict):
        return len(df.get("rows") or [])
    return 0


def print_profile(df, meta: dict[str, Any] | None, source_label: str) -> None:
    print(f"\n=== {source_label} ===")
    meta = dict(meta or {})
    inferred = meta.pop("inferred_dtypes", None)
    notes = meta.pop("dtype_notes", None)
    if meta:
        bits = [f"{k}={v}" for k, v in meta.items()]
        print("parse: " + ", ".join(bits))
    n = df_n_rows(df)
    cols = df_columns(df)
    print(f"rows_sampled={n}  ncols={len(cols)}")
    print("schema:")
    raw_dtypes = dict(df_dtypes(df))
    for name in cols:
        stored = raw_dtypes.get(name, "unknown")
        guess = inferred.get(name) if inferred else None
        if guess and guess != stored:
            print(f"  - {name}: {stored}  (inferred {guess})")
        else:
            print(f"  - {name}: {stored}")
    if notes:
        print("dtype_notes:")
        for note in notes:
            print(f"  - {note}")
    print("null_counts (in sample):")
    for name, count in df_null_counts(df):
        print(f"  - {name}: {count}")
    print("first_rows:")
    if hasattr(df, "head"):
        print(df.head(SAMPLE_ROWS_DEFAULT))
    elif isinstance(df, dict):
        print("  " + " | ".join(df.get("columns") or []))
        for row in (df.get("rows") or [])[:SAMPLE_ROWS_DEFAULT]:
            print("  " + " | ".join(str(x) for x in row))
    else:
        print(df)


def explore_zip(path: Path, members_limit: int, n_rows: int) -> int:
    print(f"\n######## ZIP {path.name} ({path}) ########")
    profiled = 0
    try:
        with zipfile.ZipFile(path) as zf:
            infos = [i for i in zf.infolist() if not i.is_dir()]
            print(f"members={len(infos)}")
            tabular = [i for i in infos if is_tabular_name(i.filename)]
            other = [i for i in infos if not is_tabular_name(i.filename)]
            print("member_list (first 30):")
            for info in infos[:30]:
                kind = "tabular" if is_tabular_name(info.filename) else "other"
                print(f"  - {info.filename}  ({info.file_size} bytes, {kind})")
            if len(infos) > 30:
                print(f"  ... {len(infos) - 30} more")

            chosen = tabular[:members_limit]
            if not chosen and other:
                print("no tabular members by suffix; attempting first non-empty files")
                chosen = other[:members_limit]

            for info in chosen:
                print(f"\n-- member {info.filename} --")
                try:
                    raw = zf.read(info.filename)
                except Exception as exc:  # noqa: BLE001
                    print(f"    could not read member: {exc}")
                    continue
                if info.filename.lower().endswith(".zip"):
                    print("    nested zip — listing only, not recursing in Phase 1")
                    continue
                df, meta = read_tabular_bytes(raw, info.filename, n_rows)
                if df is None:
                    print("    unreadable as tabular")
                    continue
                print_profile(df, meta, f"{path.name} :: {info.filename}")
                profiled += 1
    except zipfile.BadZipFile as exc:
        print(f"bad zip: {exc}")
    return profiled


def explore_loose_file(path: Path, n_rows: int) -> int:
    print(f"\n######## FILE {path.name} ({path}) ########")
    try:
        raw = path.read_bytes()
    except Exception as exc:  # noqa: BLE001
        print(f"could not read: {exc}")
        return 0
    df, meta = read_tabular_bytes(raw, path.name, n_rows)
    if df is None:
        print("unreadable as tabular")
        return 0
    print_profile(df, meta, str(path))
    return 1


def build_tried_paths(cli_value: str | None) -> list[str]:
    paths: list[str] = []
    if cli_value:
        paths.append(str(Path(cli_value).expanduser()))
    env = os.environ.get("SOURCE_DIR")
    if env:
        paths.append(env)
    paths.append(DEFAULT_SOURCE_DIR)
    paths.extend(str(p) for p in linux_drive_aliases(DEFAULT_SOURCE_DIR))
    cwd = Path.cwd()
    for rel in RELATIVE_FALLBACKS:
        paths.append(str(cwd / rel))
    seen: set[str] = set()
    unique: list[str] = []
    for item in paths:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Explore raw ComprasGov / book-purchase ZIP dumps (Phase 1)."
    )
    parser.add_argument(
        "--source-dir",
        default=None,
        help="Directory of raw ZIPs. Overrides SOURCE_DIR and the default G: path.",
    )
    parser.add_argument(
        "--sample-files",
        type=int,
        default=SAMPLE_FILES_DEFAULT,
        help=f"How many raw files to open (default {SAMPLE_FILES_DEFAULT}).",
    )
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=N_ROWS_FOR_PROFILE,
        help=f"Max rows to load per member for profiling (default {N_ROWS_FOR_PROFILE}).",
    )
    parser.add_argument(
        "--members-per-zip",
        type=int,
        default=MEMBERS_PER_ZIP_DEFAULT,
        help=f"Tabular members to profile inside each ZIP (default {MEMBERS_PER_ZIP_DEFAULT}).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print("Índice de Bibliodiversidade — Phase 1 explore")
    print(f"engine: {engine_banner()}")

    source = resolve_source_dir(args.source_dir)
    if source is None:
        list_candidate_paths(build_tried_paths(args.source_dir))
        print(
            "\nNo raw data directory found. Place ZIPs in ./Source or data/raw, "
            "or set SOURCE_DIR."
        )
        return 2

    print(f"SOURCE_DIR={source}")
    files = collect_raw_files(source)
    zips = [p for p in files if p.suffix.lower() == ".zip"]
    loose = [p for p in files if p.suffix.lower() != ".zip"]
    print(f"inventory: {len(zips)} zip(s), {len(loose)} loose tabular file(s)")
    for p in files[:50]:
        rel = p.relative_to(source) if p.is_relative_to(source) else p
        print(f"  - {rel}  ({p.stat().st_size} bytes)")
    if len(files) > 50:
        print(f"  ... {len(files) - 50} more")

    if not files:
        print("directory exists but contains no ZIP/CSV/TSV/Parquet files.")
        return 3

    sampled = files[: max(args.sample_files, 0)]
    profiled = 0
    for path in sampled:
        if path.suffix.lower() == ".zip":
            profiled += explore_zip(path, args.members_per_zip, args.sample_rows)
        else:
            profiled += explore_loose_file(path, args.sample_rows)

    print(f"\nDone. profiled_tables={profiled}  files_opened={len(sampled)}")
    return 0 if profiled else 4


if __name__ == "__main__":
    sys.exit(main())
