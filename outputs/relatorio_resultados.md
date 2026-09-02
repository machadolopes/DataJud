# Relatório técnico de tabelas e figuras

Notas de apoio à escrita do capítulo de resultados (não são redação final). Numeração APA 7.ª edição.

## Tabela 1

*Presença dos campos esperados da API DataJud no ficheiro de trabalho*

A extração TRF2 usada neste pipeline tem um processo por linha JSONL (não uma página hits.hits). Os campos essenciais do ICP — sobretudo movimentos, dataAjuizamento e identificadores — devem aparecer com cobertura próxima de 100 %; ausências aqui condicionam a exclusão listwise.

Ficheiros: `tabela_cobertura_campos_datajud.csv, tabela_cobertura_campos_datajud.md`

## Tabela 2

*Distribuição dos processos por grau de jurisdição*

A amostra de trabalho concentra-se no 1.º grau e no Juizado Especial; o 2.º grau é residual e deve ser lido com cautela nas desagregações.

Ficheiros: `tabela_volume_por_grau.csv, tabela_volume_por_grau.md`

## Tabela 3

*Doze classes processuais mais frequentes na amostra*

A composição por classe (execução fiscal, juizado, cumprimento de sentença) é heterogénea; por isso a validação controla a classe e não a inclui no índice.

Ficheiros: `tabela_top_classes.csv, tabela_top_classes.md`

## Tabela 4

*Estatísticas descritivas do comprimento da sequência de movimentos*

O comprimento mediano e os percentis inferiores informam o limiar mínimo: abaixo de P5–P10 a sequência é demasiado curta para c(S) se afastar de n.

Ficheiros: `tabela_descritivas_comprimento.csv, tabela_descritivas_comprimento.md`

## Figura 1

*Distribuição do comprimento da sequência de movimentos por processo*

A distribuição é assimétrica à direita: a maioria dos processos tem dezenas de movimentos, mas a cauda esquerda (sequências muito curtas) é a que justifica o limiar de exclusão da secção 3.5.1.

Ficheiros: `figura_histograma_comprimento_sequencia.png, figura_histograma_comprimento_sequencia.svg`

## Tabela 5

*Diversidade de códigos de movimento: por processo e na amostra*

k local é tipicamente muito menor do que α: a equitabilidade de Pielou (H̄) compara cada processo ao seu próprio máximo, não ao alfabeto TPU completo.

Ficheiros: `tabela_alfabeto_movimentos.csv, tabela_alfabeto_movimentos.md`

## Figura 2

*Distribuição do tamanho do alfabeto local de movimentos*

A maior parte dos processos usa um subconjunto pequeno do alfabeto TPU; por isso H bruto cresceria mecanicamente com k, e a normalização intra-processo é necessária.

Ficheiros: `figura_histograma_alfabeto_local.png, figura_histograma_alfabeto_local.svg`

## Tabela 6

*Percentagem de processos com campos em falta*

Se a sequência está quase sempre presente, o filtro que realmente muda N é o limiar mínimo, não a corrupção de dados.

Ficheiros: `tabela_dados_em_falta.csv, tabela_dados_em_falta.md`

## Tabela 7

*Fluxo de exclusão listwise até à amostra de construção do índice*

O fluxo n inicial → excluídos por sequência vazia → excluídos pelo limiar → n final é o denominador de todos os resultados posteriores.

Ficheiros: `tabela_fluxo_exclusao.csv, tabela_fluxo_exclusao.md`

## Tabela 8

*Proporção de processos encerrados e em curso (inferência por movimento terminal)*

Numa extração filtrada por baixa definitiva, a censura à direita deve ser residual; se aparecerem processos «em curso», vale inspeccionar códigos terminais não previstos em config.py.

Ficheiros: `tabela_encerrado_vs_em_curso.csv, tabela_encerrado_vs_em_curso.md`

## Tabela 9

*Distribuição da complexidade de Lempel-Ziv c(S) na amostra de construção*

c(S) cresce com n mas não linearmente; a normalização pelo Teorema 2 existe precisamente para separar complexidade de mero comprimento.

Ficheiros: `tabela_descritivas_c_s.csv, tabela_descritivas_c_s.md`

## Tabela 10

*Entropia de Shannon e equitabilidade de Pielou (H̄) por processo*

H̄ mede heterogeneidade de tipos, não ordem: dois processos com a mesma multiconjunto de movimentos têm o mesmo H̄ e podem ter c(S) diferente.

Ficheiros: `tabela_descritivas_entropia.csv, tabela_descritivas_entropia.md`

## Tabela 11

*Descritivas das dimensões normalizadas e do ICP (especificação principal e alternativas)*

O ICP geométrico situa-se entre as duas dimensões e penaliza desequilíbrios; comparar a média do ICP com a da aritmética na robustez (notebook 05).

Ficheiros: `tabela_descritivas_icp.csv, tabela_descritivas_icp.md`

## Tabela 12

*Medianas do ICP e das dimensões por coorte de ajuizamento*

A comparabilidade entre painéis é o teste prático do ano-base fixo: medianas que saltam de forma implausível entre coortes adjacentes devem levar a inspeccionar o limiar e a composição por classe, não a reestimar pesos.

Ficheiros: `tabela_medianas_icp_por_coorte.csv, tabela_medianas_icp_por_coorte.md`

## Figura 3

*Relação entre a dimensão estrutural e a dimensão probabilística após normalização*

Uma nuvem alongada mas não colinear é a geometria esperada de duas dimensões relacionadas e não redundantes (secção 3.5.8); colinearidade estrita invalidaria a média geométrica.

Ficheiros: `figura_dispersao_c_h.png, figura_dispersao_c_h.svg`

## Figura 4

*Distribuição do Índice de Complexidade Processual na amostra de construção*

A forma da distribuição (massa em zero vs. sino) diz se a não-compensação da média geométrica está a 'achatar' muitos processos ou a preservar discriminação no miolo.

Ficheiros: `figura_histograma_icp.png, figura_histograma_icp.svg`

## Figura 5

*ICP por coorte de ajuizamento (especificação principal)*

A estabilidade (ou deriva) das caixas ao longo do tempo é o primeiro sinal visual da comparabilidade entre painéis que a secção 3.5.6 monitoriza formalmente.

Ficheiros: `figura_boxplot_icp_por_coorte.png, figura_boxplot_icp_por_coorte.svg`
## Tabela 13

*Regressão da duração observada (dias) sobre o ICP, com controlos (coeficientes seleccionados)*

O ΔR² de 0.000 é o ganho de poder explicativo atribuível ao ICP depois de controlar classe, coorte e comprimento da sequência. Um ΔR² residual sugere que o índice não é redutível a n nem à composição por classe; um ΔR² nulo exigiria rever a arquitectura.

Ficheiros: `tabela_regressao_criterio_externo.csv, tabela_regressao_criterio_externo.md`

## Tabela 14

*Comparação do poder explicativo: modelo-base versus modelo com ICP*

Esta é a métrica-resumo da validade de critério externo pedida na secção 3.5.8: o que o ICP acrescenta para além da classe e do comprimento.

Ficheiros: `tabela_delta_r2_icp.csv, tabela_delta_r2_icp.md`

## Figura 6

*Duração processual observada em função do ICP*

A nuvem deve mostrar associação positiva se o ICP capturar tramitações que, mesmo controlando n, demoram mais; heterocedasticidade é esperada e o OLS aqui é descritivo.

Ficheiros: `figura_dispersao_icp_duracao.png, figura_dispersao_icp_duracao.svg`

## Tabela 15

*Regressão within-coorte: duração residualizada sobre o ICP residualizado*

Dentro da coorte, o ICP residualizado associa-se à duração residual com B = -16.09 dias (p = .075) e ΔR² = 0.0006. É este o teste de critério externo interpretável nesta amostra; o ΔR² nulo do modelo com dummies de coorte era esperado pelo desenho da extração.

Ficheiros: `tabela_regressao_within_coorte.csv, tabela_regressao_within_coorte.md`

## Tabela 16

*Poder explicativo do ICP: modelo com dummies de coorte versus modelo within-coorte*

Ler o ΔR² within, não o ΔR² com dummies de ano, quando todos os processos encerram no mesmo ano civil.

Ficheiros: `tabela_r2_within_vs_coorte.csv, tabela_r2_within_vs_coorte.md`

## Tabela 17

*Prevalência dos proxies procedimentais na amostra de validação*

Proxies com prevalência ~0 (ex.: perícia, carta precatória nesta extração TRF2) não permitem testar validade convergente; redistribuição e recurso são os testes informativos.

Ficheiros: `tabela_prevalencia_proxies.csv, tabela_prevalencia_proxies.md`

## Tabela 18

*Correlações de Spearman entre dimensões, ICP e proxies procedimentais*

O par c̄—H̄ é o teste discriminante interno das duas dimensões. Correlações positivas com redistribuição/recurso/suspensão sustentam validade convergente; ausências de associação nos proxies raros não falsificam o índice.

Ficheiros: `tabela_validade_convergente.csv, tabela_validade_convergente.md`

## Tabela 19

*Correlação de Spearman entre o ranking da especificação principal e cada alternativa*

Spearman de ranking próximo de 1 indica que a hierarquização dos processos é estável à escolha operacional; quedas acentuadas identificam o factor a que o índice é mais sensível (limiar, normalização ou agregação).

Ficheiros: `tabela_robustez_rankings.csv, tabela_robustez_rankings.md`

## Figura 7

*Estabilidade da hierarquização do ICP sob especificações alternativas*

Se todas as barras ficarem altas, o capítulo de resultados pode tratar o ICP como robusto às decisões ainda em aberto; se a agregação MPI ou o limiar 3 se desviarem, isso deve ser discutido explicitamente com o orientador.

Ficheiros: `figura_barras_robustez.png, figura_barras_robustez.svg`

## Tabela 20

*Correlação de Spearman entre c̄(S) e H̄ em cada coorte de ajuizamento*

Uma correlação estável e moderada ao longo das coortes sustenta a arquitectura de duas dimensões. Um salto para valores próximos de 1 na coorte mais recente é o sinal de alarme da secção 3.5.6.

Ficheiros: `tabela_correlacao_dimensoes_por_coorte.csv, tabela_correlacao_dimensoes_por_coorte.md`

## Figura 8

*Evolução da correlação entre as duas dimensões do ICP ao longo das coortes*

O gráfico é o instrumento de monitorização contínua do índice: como não há pesos, o que se vigia é a relação entre dimensões, não um vector de ponderadores.

Ficheiros: `figura_dinamica_correlacao_dimensoes.png, figura_dinamica_correlacao_dimensoes.svg`

