"""
Complexidade de Lempel-Ziv, c(S), da sequência de códigos de movimento.

Papel no pipeline
-----------------
Dimensão estrutural do ICP (secção 3.5.3–3.5.4). Quantifica a
«irredutibilidade» da história de movimentos: quantas componentes de
produção são necessárias para gerar S. Não usa pesos; não usa duração;
não usa classe processual.

Implementação
-------------
Algoritmo de Kaspar & Schuster (1987, Phys. Rev. A 36:842), que operacionaliza
a definição de produção/reprodução de Lempel & Ziv (1976, IEEE TIT 22:75–81).

Interpretação adoptada (importante)
-----------------------------------
O pseudocódigo 0-based que converte `n ← comprimento(S) - 1` e depois testa
`l + k > n` é uma adaptação comum — e INCORRECTA nas sequências curtas.
Essa variante ainda devolve 6 no exemplo da p. 76, mas viola o Teorema 1
(c(S) = c_E(S)) em casos como S = «010» (devolve 2; a história exaustiva
é 0 · 1 · 0, portanto 3).

A implementação abaixo mantém a *aritmética de ponteiros* do FORTRAN
original (n = comprimento, testes `l + k > n` e `l + 1 > n`) e só converte
o acesso ao vector para indexação 0-based: `S[i+k-1]`. Com isto:

- Lempel & Ziv (1976, p. 76): S = 0001101001000101 tem história exaustiva
  0 · 001 · 10 · 100 · 1000 · 101, portanto c(S) = 6.
- Teorema 1: c(S) = c_E(S) é verificado pela função `historia_exaustiva`
  nos testes unitários.

NÃO usamos as variantes «dicionário guloso» populares em neurociência
(antropy, Naereen greedy-set), que partem S = 0001101001000101 em 7
componentes e não correspondem à definição citada na dissertação.

Alfabeto
--------
S é uma sequência de códigos de movimento (inteiros ou strings), não
necessariamente binária. O algoritmo compara igualdade de símbolos.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Hashable

import numpy as np


Simbolo = Hashable


def _como_tupla(sequencia: Sequence[Simbolo] | str | Any) -> tuple[Simbolo, ...]:
    if sequencia is None:
        return tuple()
    if isinstance(sequencia, str):
        return tuple(sequencia)
    if isinstance(sequencia, np.ndarray):
        return tuple(sequencia.tolist())
    return tuple(sequencia)


def complexidade_lz(sequencia: Sequence[Simbolo] | str) -> int:
    """
    c(S) — número de componentes da história exaustiva de S.

    Parâmetros
    ----------
    sequencia : sequência de símbolos hashable (códigos TPU) ou string
        A sequência S. Vazia → 0; um símbolo → 1.

    Retorno
    -------
    int
        c(S) ≥ 0. Para S não vazia, c(S) ≥ 1.

    Notas
    -----
    Variáveis com nomes explícitos (não i, k, l criptográficos no corpo
    comentado). Os identificadores curtos `i`, `k`, `l`, `c` são os do
    artigo de Kaspar & Schuster e mantêm-se para quem for confrontar o
    FORTRAN; os comentários traduzem o papel de cada um.
    """
    simbolos = _como_tupla(sequencia)
    n_simbolos = len(simbolos)
    if n_simbolos == 0:
        return 0
    if n_simbolos == 1:
        return 1

    # Ponteiros no sentido FORTRAN (1-based na lógica, 0-based no acesso):
    # i = deslocamento dentro do prefixo já analisado (arranca em 0)
    # k = comprimento do candidato a componente
    # l = posição (1-based) onde começa a componente em construção
    # c = número de componentes já fechadas (arranca em 1 = primeiro símbolo)
    indice_prefixo = 0          # i
    comprimento_candidato = 1   # k
    inicio_componente = 1       # l  (1-based: o 1.º símbolo já é uma produção)
    n_componentes = 1           # c
    maior_candidato = 1         # k_max
    n = n_simbolos              # comprimento, NÃO comprimento-1 (ver docstring)

    # O ciclo é O(n²) no pior caso. Para sequências processuais (n típico
    # < 100) isto é irrelevante; não substituímos por LZ78/dicionário.
    n_passos = 0
    limite_passos = n_simbolos * n_simbolos + n_simbolos + 8
    while True:
        n_passos += 1
        if n_passos > limite_passos:
            raise RuntimeError(
                "Ciclo de Kaspar-Schuster excedeu o limite; "
                "verificar a sequência de entrada."
            )
        # FORTRAN: s(i+k) == s(l+k)  →  Python: [i+k-1] == [l+k-1]
        simbolo_no_prefixo = simbolos[indice_prefixo + comprimento_candidato - 1]
        simbolo_candidato = simbolos[inicio_componente + comprimento_candidato - 1]
        if simbolo_no_prefixo == simbolo_candidato:
            comprimento_candidato += 1
            if inicio_componente + comprimento_candidato > n:
                # A componente actual esgotou S: conta e termina
                # (a última componente pode ser mera reprodução).
                n_componentes += 1
                break
        else:
            if comprimento_candidato > maior_candidato:
                maior_candidato = comprimento_candidato
            indice_prefixo += 1
            if indice_prefixo == inicio_componente:
                # Esgotou-se o prefixo: a componente não é reproduzível;
                # fecha-se uma produção e avança-se l em k_max símbolos.
                n_componentes += 1
                inicio_componente += maior_candidato
                if inicio_componente + 1 > n:
                    break
                indice_prefixo = 0
                comprimento_candidato = 1
                maior_candidato = 1
            else:
                comprimento_candidato = 1
    return n_componentes


def _e_reproduzivel(frase: tuple[Simbolo, ...], palheiro: tuple[Simbolo, ...]) -> bool:
    """True se `frase` ocorre como subsequência contígua de `palheiro`."""
    n_frase = len(frase)
    n_palheiro = len(palheiro)
    if n_frase == 0 or n_frase > n_palheiro:
        return False
    for inicio in range(0, n_palheiro - n_frase + 1):
        if palheiro[inicio:inicio + n_frase] == frase:
            return True
    return False


def historia_exaustiva(sequencia: Sequence[Simbolo] | str) -> list[tuple[Simbolo, ...]]:
    """
    Partição H_E(S) pela definição de produção/reprodução (LZ 1976).

    Uma componente é a reprodução mais longa do prefixo já gerado,
    estendida de um símbolo novo (produção), excepto a última, que pode
    ser só reprodução. Teorema 1: c(S) = número destas componentes.

    Usada nos testes para validar Kaspar-Schuster; também ilustra o
    exemplo da p. 76 no notebook 03.
    """
    simbolos = _como_tupla(sequencia)
    n = len(simbolos)
    if n == 0:
        return []
    componentes: list[tuple[Simbolo, ...]] = []
    posicao = 0
    while posicao < n:
        comprimento = 1
        while True:
            if posicao + comprimento > n:
                componentes.append(simbolos[posicao:])
                return componentes
            frase = simbolos[posicao:posicao + comprimento]
            palheiro = simbolos[: posicao + comprimento - 1]
            if _e_reproduzivel(frase, palheiro):
                comprimento += 1
            else:
                componentes.append(frase)
                posicao += comprimento
                break
    return componentes


def complexidade_por_historia_exaustiva(sequencia: Sequence[Simbolo] | str) -> int:
    """c_E(S) — comprimento de H_E(S). Deve coincidir com `complexidade_lz`."""
    return len(historia_exaustiva(sequencia))


def formatar_historia(componentes: Sequence[Sequence[Any]], junta: str = " · ") -> str:
    """Representação tipo 0 · 001 · 10 · 100 · 1000 · 101."""
    pecas = []
    for componente in componentes:
        if componente and all(isinstance(s, str) and len(s) == 1 for s in componente):
            pecas.append("".join(str(s) for s in componente))
        else:
            pecas.append("(" + ",".join(str(s) for s in componente) + ")")
    return junta.join(pecas)
