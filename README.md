# Índice de Complexidade Processual (DataJud / CNJ)

Pipeline de construção e validação do **índice composto e dinâmico de complexidade processual** (ICP) a partir de metadados da API pública DataJud, para a dissertação de mestrado em Business Analytics.

O índice **não usa pesos**. Combina duas dimensões calculáveis na sequência de movimentos de cada processo:

1. **Estrutural** — complexidade de Lempel-Ziv \(c(S)\) (Kaspar & Schuster, 1987; Lempel & Ziv, 1976).
2. **Probabilística** — entropia de Shannon normalizada \(\bar{H}\) (equitabilidade de Pielou).

Agregação principal (não compensatória):

\[
\mathrm{ICP} = \sqrt{\bar{c}(S)\cdot\bar{H}}
\]

Classe, assuntos, grau, tribunal, órgão julgador e formato **não entram no índice** (são coortes/controlos). A **duração processual nunca é insumo** — só critério externo de validação.

A lógica reutilizável está em `src/` (testável com `pytest`). Os notebooks em `notebooks/` orquestram, narram e **mostram** tabelas e figuras em formato APA 7.ª edição, inline.

---

## Aviso — parâmetros ainda não validados

**Este pipeline não deve ser considerado final** enquanto os parâmetros em `src/config.py` não forem confirmados com o orientador. Os valores actuais são *placeholders* / sugestões de arranque (alguns preenchidos pela EDA em `data/processado/parametros_sugeridos.json`), **não decisões definitivas**. Pontos em aberto:

- `LIMIAR_MINIMO_MOVIMENTOS` — secção 3.5.1
- `ANO_BASE` e `COORTES` — secção 3.5.3
- `LIMIAR_CORRELACAO_DIMENSOES` — secção 3.5.6 (sugestão inicial: 0.90)
- `CODIGOS_MOVIMENTO_PROCEDIMENTAIS` — códigos TPU da validade convergente (secção 3.5.8)

---

## Dados

Coloque o `.jsonl` da extração DataJud em `data/` (um objecto JSON por linha). Esta pasta **não é versionada**.

A extração de referência deste repositório (`DATAJUD_API_v_final.ipynb`) grava já **um processo por linha** (campo `_source`), não uma página Elasticsearch. O notebook `01_diagnostico_schema.ipynb` confirma o schema real e o parser em `src/io_datajud.py` aceita os dois formatos.

Nome típico: `data/processos_trf2_baixa_definitiva_2025.jsonl`.

---

## Como correr o pipeline do início ao fim

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# testes unitários (inclui o exemplo Lempel & Ziv 1976, p. 76: c(S)=6)
pytest

# Jupyter
jupyter lab
```

Abra, **por esta ordem**, e use *Restart & Run All* em cada um:

1. `notebooks/01_diagnostico_schema.ipynb` → `data/processado/processos.parquet`
2. `notebooks/02_eda.ipynb` → `processos_eda.parquet` + `parametros_sugeridos.json`
3. `notebooks/03_construcao_indice.ipynb` → `indice.parquet` + `limites_normalizacao.json`
4. `notebooks/04_validacao.ipynb`
5. `notebooks/05_robustez_e_dinamica.ipynb`

Cada notebook lê os artefactos do anterior (não depende de variáveis em memória). Tabelas e figuras APA ficam em `outputs/tabelas` e `outputs/figuras` (PNG 300 dpi + SVG) e no próprio notebook. O ficheiro `outputs/relatorio_resultados.md` lista cada tabela/figura com uma nota técnica de interpretação.

Em linha de comando:

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/01_diagnostico_schema.ipynb
# … repetir para 02–05
```

---

## Estrutura

```
data/                         # .jsonl bruto (não versionar)
src/                          # algoritmos e formatação APA
notebooks/                    # 01 … 05
outputs/figuras|tabelas       # artefactos da dissertação
tests/                        # pytest (Lempel-Ziv e entropia)
```

---

## Referências de implementação (citadas no código)

- Lempel, A., & Ziv, J. (1976). On the complexity of finite sequences. *IEEE Transactions on Information Theory, 22*(1), 75–81.
- Kaspar, F., & Schuster, H. G. (1987). Easily calculable measure for the complexity of spatiotemporal patterns. *Physical Review A, 36*(2), 842–848.
- Mazziotta, M., & Pareto, A. (2013). A non-compensatory composite index for measuring well-being. *Rivista Italiana degli Economisti*.
