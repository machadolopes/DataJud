"""Testes pontuais de agregação (média geométrica não compensatória)."""

from __future__ import annotations

import math

from src.agregacao import media_aritmetica, media_geometrica


def test_geometrica_zero_nao_compensa():
    assert media_geometrica(0.0, 1.0) == 0.0
    assert media_geometrica(1.0, 0.0) == 0.0


def test_geometrica_meio():
    assert math.isclose(media_geometrica(0.25, 1.0), 0.5)


def test_aritmetica_compensa():
    assert math.isclose(media_aritmetica(0.0, 1.0), 0.5)
