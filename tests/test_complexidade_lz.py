"""Testes da complexidade de Lempel-Ziv (Kaspar & Schuster, 1987).

O teste âncora NÃO deve ser ajustado para passar: Lempel & Ziv (1976, p. 76)
fixam c(S) = 6 para S = 0001101001000101 (história 0·001·10·100·1000·101).
"""

from __future__ import annotations

import random

from src.complexidade_lz import (
    complexidade_lz,
    complexidade_por_historia_exaustiva,
    formatar_historia,
    historia_exaustiva,
)

# Lempel & Ziv (1976), IEEE Trans. Inf. Theory 22(1), p. 76.
SEQUENCIA_LZ1976 = "0001101001000101"
COMPONENTES_LZ1976 = ("0", "001", "10", "100", "1000", "101")


def test_exemplo_lempel_ziv_1976_pagina_76():
    """c(S) = 6; não alterar este assert se a implementação falhar — investigar."""
    assert complexidade_lz(SEQUENCIA_LZ1976) == 6


def test_historia_exaustiva_coincide_com_o_artigo():
    partes = historia_exaustiva(SEQUENCIA_LZ1976)
    assert formatar_historia(partes) == " · ".join(COMPONENTES_LZ1976)
    assert complexidade_por_historia_exaustiva(SEQUENCIA_LZ1976) == 6


def test_teorema_1_c_igual_c_e_no_exemplo_canonico():
    """Teorema 1 (LZ 1976): c(S) = c_E(S)."""
    assert complexidade_lz(SEQUENCIA_LZ1976) == complexidade_por_historia_exaustiva(
        SEQUENCIA_LZ1976
    )


def test_alfabeto_arbitrario_equivalente_ao_binario():
    """Códigos de movimento (ints) com a mesma igualdade de símbolos."""
    binaria = SEQUENCIA_LZ1976
    como_ints = [int(ch) for ch in binaria]
    como_strings = [ch for ch in binaria]
    assert complexidade_lz(como_ints) == 6
    assert complexidade_lz(como_strings) == 6


def test_casos_degenerados():
    assert complexidade_lz("") == 0
    assert complexidade_lz([]) == 0
    assert complexidade_lz("0") == 1
    assert complexidade_lz([26]) == 1
    # Sequência mono-símbolo: 1 produção + 1 reprodução da cauda.
    assert complexidade_lz("000000") == 2
    assert complexidade_lz([22, 22, 22, 22]) == 2


def test_sequencias_curtas_conhecidas():
    # 0 · 1  (não 3: o off-by-one de algumas portas «Naereen» conta 3)
    assert complexidade_lz("01") == 2
    # 0 · 1 · 0  — a conversão ingénua n = len-1 falha aqui (devolve 2)
    assert complexidade_lz("010") == 3
    assert complexidade_lz("1010101010101010") == 3


def test_teorema_1_em_sequencias_aleatorias():
    rng = random.Random(2026)
    for n in range(1, 20):
        for _ in range(25):
            s = "".join(rng.choice("01") for _ in range(n))
            assert complexidade_lz(s) == complexidade_por_historia_exaustiva(s)
            # Alfabeto TPU simulado (três códigos)
            tpu = [rng.choice([26, 22, 11010]) for _ in range(n)]
            assert complexidade_lz(tpu) == complexidade_por_historia_exaustiva(tpu)


def test_nao_usar_dicionario_guloso_que_devolve_7():
    """A variante set-greedy (antropy/Naereen) parte o exemplo da p. 76 em 7."""
    # Se no futuro alguém «simplificar» para um set de substrings, este teste falha.
    assert complexidade_lz(SEQUENCIA_LZ1976) != 7
