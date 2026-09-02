"""
Formatação APA 7.ª edição de tabelas e figuras.

Papel no pipeline
-----------------
As figuras e tabelas empíricas da dissertação seguem a APA 7 (número e
título *acima*; notas *abaixo* prefixadas por «Nota.» em itálico). Isto
difere da 6.ª edição e também da tradição de «Quadros» dos capítulos
conceptuais — a numeração empírica começa em «Tabela 1» / «Figura 1».

As mesmas figuras/tabelas são (a) mostradas inline no notebook e
(b) gravadas em /outputs para inserção no Word (PNG 300 dpi + SVG;
CSV + Markdown + DOCX).
"""

from __future__ import annotations

import json
import html
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from IPython.display import HTML, display

from src.config import CASAS_DECIMAIS_APA


def formatar_p(p_valor: float, casas: int = 3) -> str:
    """p-valores APA: sem zero à esquerda (p < .001 ou p = .023)."""
    if p_valor is None or (isinstance(p_valor, float) and pd.isna(p_valor)):
        return "—"
    if p_valor < 0.001:
        return "p < .001"
    texto = f"{p_valor:.{casas}f}"
    if texto.startswith("0."):
        texto = texto[1:]
    return f"p = {texto}"


def formatar_numero(valor: Any, casas: int = CASAS_DECIMAIS_APA) -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return "—"
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        if float(valor).is_integer() and abs(valor) >= 1 and casas == CASAS_DECIMAIS_APA:
            # Contagens: sem decimais. Coeficientes podem ser 1.00.
            pass
        return f"{float(valor):.{casas}f}"
    return str(valor)


def aplicar_estilo_apa() -> None:
    """Estilo matplotlib/seaborn reutilizável (sem grelha 3D, paleta daltónica)."""
    sns.set_theme(style="ticks", palette="colorblind")
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica", "Nimbus Sans"],
            "axes.grid": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.unicode_minus": False,
            "figure.dpi": 120,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
        }
    )


def _html_tabela(quadro: pd.DataFrame, casas: int) -> str:
    """Tabela HTML só com linhas horizontais (APA)."""
    linhas = [
        '<table style="border-collapse:collapse;border-top:2px solid #000;'
        'border-bottom:2px solid #000;margin:0.4em 0 0.6em 0;font-size:0.92em;">'
        "<thead><tr>"
    ]
    for col in quadro.columns:
        linhas.append(
            f'<th style="border-bottom:1px solid #000;text-align:center;'
            f'padding:4px 10px;font-weight:600;">{html.escape(str(col))}</th>'
        )
    linhas.append("</tr></thead><tbody>")
    for _, row in quadro.iterrows():
        linhas.append("<tr>")
        for col, valor in zip(quadro.columns, row, strict=False):
            if col in {"p (APA)"}:
                texto = str(valor)
            elif isinstance(valor, (int, float)) and not isinstance(valor, bool):
                texto = formatar_numero(valor, casas)
            else:
                texto = "" if pd.isna(valor) else str(valor)
            align = "left" if col == quadro.columns[0] else "center"
            linhas.append(
                f'<td style="padding:3px 10px;text-align:{align};'
                f'">{html.escape(texto)}</td>'
            )
        linhas.append("</tr>")
    linhas.append("</tbody></table>")
    return "".join(linhas)


def _markdown_tabela(quadro: pd.DataFrame, casas: int) -> str:
    colunas = [str(c) for c in quadro.columns]
    cab = "| " + " | ".join(colunas) + " |"
    sep = "| " + " | ".join("---" for _ in colunas) + " |"
    corpo = []
    for _, row in quadro.iterrows():
        celulas = []
        for col, valor in zip(quadro.columns, row, strict=False):
            if col == "p (APA)":
                celulas.append(str(valor))
            elif isinstance(valor, (int, float)) and not isinstance(valor, bool):
                celulas.append(formatar_numero(valor, casas))
            else:
                celulas.append("" if pd.isna(valor) else str(valor))
        corpo.append("| " + " | ".join(celulas) + " |")
    return "\n".join([cab, sep, *corpo])


def _escrever_docx_tabela(
    caminho: Path,
    numero: int,
    titulo: str,
    quadro: pd.DataFrame,
    nota: str,
    casas: int,
) -> None:
    try:
        from docx import Document
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
    except ImportError:
        return

    def sombra_horizontal(celula, topo=False, fundo=False):
        tc = celula._tePr if hasattr(celula, "_tePr") else celula._tc.get_or_add_tcPr()
        bordas = OxmlElement("w:tcBorders")
        for edge, activo in (("top", topo), ("bottom", fundo), ("left", False), ("right", False)):
            el = OxmlElement(f"w:{edge}")
            el.set(qn("w:val"), "single" if activo else "nil")
            el.set(qn("w:sz"), "12" if activo else "0")
            el.set(qn("w:color"), "000000")
            bordas.append(el)
        tc.append(bordas)

    doc = Document()
    p_num = doc.add_paragraph()
    run = p_num.add_run(f"Tabela {numero}")
    run.bold = True
    p_tit = doc.add_paragraph()
    run_t = p_tit.add_run(titulo)
    run_t.italic = True
    tabela = doc.add_table(rows=1 + len(quadro), cols=len(quadro.columns))
    for j, col in enumerate(quadro.columns):
        tabela.rows[0].cells[j].text = str(col)
    for i, (_, row) in enumerate(quadro.iterrows(), start=1):
        for j, (col, valor) in enumerate(zip(quadro.columns, row, strict=False)):
            if col == "p (APA)":
                texto = str(valor)
            elif isinstance(valor, (int, float)) and not isinstance(valor, bool):
                texto = formatar_numero(valor, casas)
            else:
                texto = "" if pd.isna(valor) else str(valor)
            tabela.rows[i].cells[j].text = texto
    p_nota = doc.add_paragraph()
    r1 = p_nota.add_run("Nota. ")
    r1.italic = True
    p_nota.add_run(nota)
    p_nota.alignment = WD_ALIGN_PARAGRAPH.LEFT
    doc.save(caminho)


class CatalogoAPA:
    """Numeração contínua de Tabelas e Figuras + relatório técnico."""

    def __init__(
        self,
        dir_figuras: Path,
        dir_tabelas: Path,
        caminho_relatorio: Path,
        reiniciar_relatorio: bool = False,
    ) -> None:
        self.dir_figuras = Path(dir_figuras)
        self.dir_tabelas = Path(dir_tabelas)
        self.caminho_relatorio = Path(caminho_relatorio)
        self.dir_figuras.mkdir(parents=True, exist_ok=True)
        self.dir_tabelas.mkdir(parents=True, exist_ok=True)
        self.entradas: list[dict[str, str]] = []
        self.caminho_estado = Path(dir_tabelas).parent / "estado_catalogo_apa.json"
        if reiniciar_relatorio or not self.caminho_relatorio.exists():
            self.n_tabelas = 0
            self.n_figuras = 0
            self.caminho_relatorio.write_text(
                "# Relatório técnico de tabelas e figuras\n\n"
                "Notas de apoio à escrita do capítulo de resultados "
                "(não são redação final). Numeração APA 7.ª edição.\n\n",
                encoding="utf-8",
            )
            self._gravar_estado()
        else:
            self._carregar_estado()
        aplicar_estilo_apa()

    def _carregar_estado(self) -> None:
        if self.caminho_estado.exists():
            dados = json.loads(self.caminho_estado.read_text(encoding="utf-8"))
            self.n_tabelas = int(dados.get("n_tabelas", 0))
            self.n_figuras = int(dados.get("n_figuras", 0))
        else:
            self.n_tabelas = 0
            self.n_figuras = 0

    def _gravar_estado(self) -> None:
        self.caminho_estado.write_text(
            json.dumps({"n_tabelas": self.n_tabelas, "n_figuras": self.n_figuras}),
            encoding="utf-8",
        )

    def _acrescentar_relatorio(
        self, tipo: str, numero: int, titulo: str, interpretacao: str, ficheiros: str
    ) -> None:
        bloco = (
            f"## {tipo} {numero}\n\n"
            f"*{titulo}*\n\n"
            f"{interpretacao}\n\n"
            f"Ficheiros: `{ficheiros}`\n\n"
        )
        with self.caminho_relatorio.open("a", encoding="utf-8") as ficheiro:
            ficheiro.write(bloco)
        self.entradas.append(
            {"tipo": tipo, "numero": str(numero), "titulo": titulo, "interpretacao": interpretacao}
        )
        self._gravar_estado()

    def nova_tabela(
        self,
        quadro: pd.DataFrame,
        titulo: str,
        nota: str,
        nome_ficheiro: str,
        interpretacao: str,
        casas: int = CASAS_DECIMAIS_APA,
        mostrar: bool = True,
    ) -> pd.DataFrame:
        """Mostra a tabela no notebook e grava CSV, Markdown e DOCX."""
        self.n_tabelas += 1
        numero = self.n_tabelas
        base = self.dir_tabelas / nome_ficheiro
        quadro.to_csv(base.with_suffix(".csv"), index=False)
        md = (
            f"**Tabela {numero}**\n\n*{titulo}*\n\n"
            f"{_markdown_tabela(quadro, casas)}\n\n"
            f"*Nota.* {nota}\n"
        )
        base.with_suffix(".md").write_text(md, encoding="utf-8")
        _escrever_docx_tabela(
            base.with_suffix(".docx"), numero, titulo, quadro, nota, casas
        )
        if mostrar:
            display(
                HTML(
                    f"<p style='margin-bottom:0'><strong>Tabela {numero}</strong></p>"
                    f"<p style='margin-top:0'><em>{html.escape(titulo)}</em></p>"
                    f"{_html_tabela(quadro, casas)}"
                    f"<p><em>Nota.</em> {html.escape(nota)}</p>"
                )
            )
        ficheiros = f"{base.with_suffix('.csv').name}, {base.with_suffix('.md').name}"
        self._acrescentar_relatorio("Tabela", numero, titulo, interpretacao, ficheiros)
        return quadro

    def nova_figura(
        self,
        fig: plt.Figure,
        titulo: str,
        nota: str,
        nome_ficheiro: str,
        interpretacao: str,
        mostrar: bool = True,
    ) -> plt.Figure:
        """Número e título APA acima; PNG 300 dpi + SVG em /outputs/figuras."""
        self.n_figuras += 1
        numero = self.n_figuras
        fig.tight_layout(rect=(0, 0.02, 1, 0.90))
        # Título APA acima da área de eixos (não dentro do gráfico).
        fig.text(
            0.0, 0.99, f"Figura {numero}",
            fontsize=11, fontweight="bold", va="top", ha="left",
            transform=fig.transFigure, fontfamily="sans-serif",
        )
        fig.text(
            0.0, 0.94, titulo,
            fontsize=11, fontstyle="italic", va="top", ha="left",
            transform=fig.transFigure, fontfamily="sans-serif",
            wrap=True,
        )
        if nota:
            fig.text(
                0.0, 0.0, f"Nota. {nota}",
                fontsize=8, fontstyle="italic", va="bottom", ha="left",
                transform=fig.transFigure, fontfamily="sans-serif",
            )
        destino = self.dir_figuras / nome_ficheiro
        fig.savefig(destino.with_suffix(".png"), dpi=300)
        fig.savefig(destino.with_suffix(".svg"))
        if mostrar:
            display(
                HTML(
                    f"<p style='margin-bottom:0'><strong>Figura {numero}</strong></p>"
                    f"<p style='margin-top:2px'><em>{html.escape(titulo)}</em></p>"
                )
            )
            display(fig)
            if nota:
                display(HTML(f"<p><em>Nota.</em> {html.escape(nota)}</p>"))
        plt.close(fig)
        self._acrescentar_relatorio(
            "Figura", numero, titulo, interpretacao,
            f"{destino.with_suffix('.png').name}, {destino.with_suffix('.svg').name}",
        )
        return fig
