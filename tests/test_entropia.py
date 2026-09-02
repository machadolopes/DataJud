"""Testes da entropia de Shannon e da normalização de Pielou (H̄)."""

from __future__ import annotations

import math

from src.entropia import entropia_normalizada, entropia_shannon


def test_sequencia_vazia_e_zero():
    assert entropia_shannon([]) == 0.0
    assert entropia_normalizada([]) == 0.0


def test_k_igual_a_1_h_barra_zero_por_convencao():
    """k = 1 ⇒ H̄ = 0 (não 0/0). Secção 3.5.3."""
    assert entropia_shannon([22, 22, 22]) == 0.0
    assert entropia_normalizada([22, 22, 22]) == 0.0
    assert entropia_normalizada(["a"]) == 0.0


def test_dois_simbolos_equiprovaveis():
    sequencia = [26, 22, 26, 22]
    h = entropia_shannon(sequencia)
    assert math.isclose(h, 1.0, abs_tol=1e-12)
    assert math.isclose(entropia_normalizada(sequencia), 1.0, abs_tol=1e-12)


def test_distribuicao_conhecida_nao_uniforme():
    # p = (3/4, 1/4) → H = -0.75 log2 0.75 - 0.25 log2 0.25
    sequencia = [1, 1, 1, 2]
    esperado = -0.75 * math.log2(0.75) - 0.25 * math.log2(0.25)
    assert math.isclose(entropia_shannon(sequencia), esperado, abs_tol=1e-12)
    h_barra = entropia_normalizada(sequencia)
    assert 0.0 < h_barra < 1.0
    assert math.isclose(h_barra, esperado / 1.0, abs_tol=1e-12)  # log2(k=2) = 1


def test_h_barra_limitada_a_unitario():
    sequencia = list(range(10))  # uniforme, k = n → H̄ = 1
    assert math.isclose(entropia_normalizada(sequencia), 1.0, abs_tol=1e-12)
