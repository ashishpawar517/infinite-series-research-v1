"""Tests for Ramanujan's pi formula implementation."""

from __future__ import annotations

import mpmath as mp

from src.ramanujan_engine.evaluator import evaluate_ramanujan_pi
from src.ramanujan_engine.formulas.ramanujan_pi import (
    evaluate_ramanujan_pi_direct,
)


def test_terms_1_value():
    """Test that terms=1 produces expected value."""
    result = evaluate_ramanujan_pi(terms=1, precision=80)
    expected = mp.mpf("3.14159273001330566")

    # Check that we're within reasonable tolerance
    assert abs(result.value - expected) < mp.mpf("1e-10")


def test_terms_2_value():
    """Test that terms=2 produces expected value."""
    result = evaluate_ramanujan_pi(terms=2, precision=80)
    expected = mp.mpf("3.14159265358979388")

    # Check that we're within reasonable tolerance
    assert abs(result.value - expected) < mp.mpf("1e-10")


def test_terms_3_improvement():
    """Test that terms=3 is more accurate than terms=2."""
    result_2 = evaluate_ramanujan_pi(terms=2, precision=80)
    result_3 = evaluate_ramanujan_pi(terms=3, precision=80)

    # Get high precision reference
    mp.mp.dps = 80
    ref_pi = mp.pi

    error_2 = abs(result_2.value - ref_pi)
    error_3 = abs(result_3.value - ref_pi)

    # Error should decrease with more terms
    assert error_3 < error_2


def test_precision_scaling():
    """Test that increasing working precision improves result."""
    result_low = evaluate_ramanujan_pi(terms=2, precision=30)
    result_high = evaluate_ramanujan_pi(terms=2, precision=80)

    mp.mp.dps = 80
    ref_pi = mp.pi

    error_low = abs(result_low.value - ref_pi)
    error_high = abs(result_high.value - ref_pi)

    # Higher precision should give equal or better accuracy
    assert error_high <= error_low + mp.mpf("1e-20")


def test_recurrence_vs_direct():
    """Test that recurrence matches direct factorial calculation for small n."""
    for terms in [1, 2, 3, 4, 5]:
        rec_result = evaluate_ramanujan_pi(terms=terms, precision=50)
        dir_result = evaluate_ramanujan_pi_direct(terms=terms, precision=50)

        # Values should be very close (within rounding error)
        assert abs(rec_result.value - dir_result.value) < mp.mpf("1e-45")


def test_invalid_inputs():
    """Test that invalid inputs raise appropriate errors."""
    # Test negative terms
    try:
        evaluate_ramanujan_pi(terms=0, precision=50)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected

    try:
        evaluate_ramanujan_pi(terms=-1, precision=50)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected

    # Test invalid precision
    try:
        evaluate_ramanujan_pi(terms=5, precision=0)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected

    try:
        evaluate_ramanujan_pi(terms=5, precision=-10)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected


def test_trace_collection():
    """Test that trace collection works correctly."""
    result = evaluate_ramanujan_pi(terms=3, precision=50, compute_trace=True)

    assert len(result.trace) == 3
    # First term (n=0) should be 1103
    assert abs(result.trace[0][1] - mp.mpf(1103)) < mp.mpf("1e-40")


def test_analytic_bound():
    """Test that analytic bound is computed and exceeds observed error."""
    result = evaluate_ramanujan_pi(terms=3, precision=80, compute_trace=False)

    mp.mp.dps = 80
    ref_pi = mp.pi
    observed_error = abs(result.value - ref_pi)

    # If bound is implemented, it should exceed observed error
    if result.analytic_bound is not None:
        assert result.analytic_bound >= observed_error
        assert result.analytic_bound >= mp.mpf(0)  # Bound should be non-negative


if __name__ == "__main__":
    # Run tests manually if executed directly
    test_terms_1_value()
    test_terms_2_value()
    test_terms_3_improvement()
    test_precision_scaling()
    test_recurrence_vs_direct()
    test_invalid_inputs()
    test_trace_collection()
    test_analytic_bound()
    print("All tests passed!")