"""Tests for the general catalogue + accelerator engine (Phase 1)."""

from __future__ import annotations

import mpmath as mp

from src.ramanujan_engine.evaluator import evaluate_formula_by_name
from src.ramanujan_engine.formulas.catalogue import get_formula, list_formulas


def _err(name: str, terms: int, dps: int, accelerator: str = "auto") -> mp.mpf:
    res = evaluate_formula_by_name(
        name, terms=terms, precision=dps, accelerator=accelerator
    )
    ref = get_formula(name).reference(dps)
    target = get_formula(name).target
    val = res.value
    if target == "pi/4":
        # Leibniz formula targets pi, transform returns 4*sum -> pi
        return abs(val - ref)
    if target == "pi":
        return abs(val - ref)
    return abs(val - ref)


def test_catalogue_lists_expected():
    names = list_formulas()
    for expected in (
        "ramanujan-pi",
        "chudnovsky-pi",
        "exp-e",
        "basel-zeta2",
        "leibniz-pi4",
        "alt-log2",
    ):
        assert expected in names


def test_chudnovsky_fast_convergence():
    mp.mp.dps = 50
    r1 = evaluate_formula_by_name("chudnovsky-pi", terms=1, precision=50)
    r2 = evaluate_formula_by_name("chudnovsky-pi", terms=2, precision=50)
    assert abs(r2.value - mp.pi) < abs(r1.value - mp.pi)
    assert abs(r2.value - mp.pi) < mp.mpf("1e-14")


def test_exp_e_direct():
    r = evaluate_formula_by_name("exp-e", terms=20, precision=40)
    mp.mp.dps = 40
    assert abs(r.value - mp.e) < mp.mpf("1e-15")


def test_basel_with_richardson_beats_direct():
    dps = 30
    direct = evaluate_formula_by_name(
        "basel-zeta2", terms=30, precision=dps, accelerator="direct"
    )
    accel = evaluate_formula_by_name(
        "basel-zeta2", terms=30, precision=dps, accelerator="richardson"
    )
    mp.mp.dps = dps
    ref = mp.zeta(2)
    assert abs(accel.value - ref) < abs(direct.value - ref)


def test_leibniz_with_cvz_beats_direct():
    dps = 30
    direct = evaluate_formula_by_name(
        "leibniz-pi4", terms=30, precision=dps, accelerator="direct"
    )
    accel = evaluate_formula_by_name(
        "leibniz-pi4", terms=30, precision=dps, accelerator="cvz"
    )
    mp.mp.dps = dps
    assert abs(accel.value - mp.pi) < abs(direct.value - mp.pi)


def test_unknown_formula_raises():
    try:
        evaluate_formula_by_name("nope", terms=5, precision=30)
        assert False, "should raise KeyError"
    except KeyError:
        pass


if __name__ == "__main__":
    test_catalogue_lists_expected()
    test_chudnovsky_fast_convergence()
    test_exp_e_direct()
    test_basel_with_richardson_beats_direct()
    test_leibniz_with_cvz_beats_direct()
    test_unknown_formula_raises()
    print("Catalogue tests passed!")
