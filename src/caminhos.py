"""
Resolução de caminhos do projecto.

Garante que os notebooks correm tanto a partir da raiz do repositório
como a partir de /notebooks, e que as directorias de saída existem.
"""

from __future__ import annotations

import sys
from pathlib import Path


def raiz_projeto() -> Path:
    """Devolve a raiz do repositório (a pasta que contém `src/` e `data/`)."""
    cwd = Path.cwd().resolve()
    candidatos = [cwd, cwd.parent, Path(__file__).resolve().parent.parent]
    for candidato in candidatos:
        if (candidato / "src" / "config.py").exists():
            return candidato
    raise RuntimeError(
        "Não encontrei a raiz do projecto. Execute o notebook a partir "
        "da raiz do repositório ou da pasta notebooks/."
    )


def garantir_sys_path() -> Path:
    """Insere a raiz no sys.path para `import src...` funcionar nos notebooks."""
    raiz = raiz_projeto()
    raiz_str = str(raiz)
    if raiz_str not in sys.path:
        sys.path.insert(0, raiz_str)
    return raiz


def directorias(raiz: Path | None = None) -> dict[str, Path]:
    """Caminhos canónicos das pastas de dados e saídas."""
    raiz = raiz or raiz_projeto()
    return {
        "raiz": raiz,
        "dados": raiz / "data",
        "processado": raiz / "data" / "processado",
        "saidas": raiz / "outputs",
        "figuras": raiz / "outputs" / "figuras",
        "tabelas": raiz / "outputs" / "tabelas",
        "src": raiz / "src",
        "notebooks": raiz / "notebooks",
        "testes": raiz / "tests",
    }


def garantir_directorias(raiz: Path | None = None) -> dict[str, Path]:
    """Cria as pastas de trabalho se ainda não existirem."""
    dirs = directorias(raiz)
    for chave in ("dados", "processado", "saidas", "figuras", "tabelas"):
        dirs[chave].mkdir(parents=True, exist_ok=True)
    return dirs
