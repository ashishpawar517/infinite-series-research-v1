"""Tests for the generic evaluator."""

from __future__ import annotations

import mpmath as mp

from src.ramanujan_engine.evaluator import SeriesEvaluator, SeriesResult


def test_evaluator_initialization():
    """Test that evaluator initializes correctly."""
    eval_default = SeriesEvaluator()
    assert eval_default.precision == 50

    eval_custom = SeriesEvaluator(precision=30)
    assert eval_custom.precision == 30


def test_simple_series_evaluation():
    """Test evaluation of a simple geometric series."""
    # Sum of 1/2^n from n=0 to infinity = 2
    # So sum of first few terms should approach 2

    def term_generator(n: int) -> mp.mpf:
        return mp.mpf(1) / mp.mpf(2 ** n)

    evaluator = SeriesEvaluator(precision=30)
    result = evaluator.evaluate_series(
        formula_name="geometric series",
        term_generator=term_generator,
        terms=10,
    )

    # With 10 terms (n=0 to n=9), sum should be (1 - (1/2)^10) / (1 - 1/2)
    expected = (mp.mpf(1) - mp.mpf(1) / mp.mpf(2 ** 10)) / (mp.mpf(1) - mp.mpf(1) / mp.mpf(2))
    assert abs(result.partial_sum - expected) < mp.mpf("1e-25")


def test_result_to_dict():
    """Test conversion of SeriesResult to dictionary."""
    evaluator = SeriesEvaluator(precision=25)

    def term_generator(n: int) -> mp.mpf:
        return mp.mpf(1) / mp.mpf(2 ** n)

    result = evaluator.evaluate_series(
        formula_name="test series",
        term_generator=term_generator,
        terms=5,
        compute_trace=True,
    )

    result_dict = result.to_dict()

    assert result_dict["formula_name"] == "test series"
    assert result_dict["terms_evaluated"] == 5
    assert result_dict["working_precision"] == 25
    assert "value" in result_dict
    assert "partial_sum" in result_dict
    assert len(result_dict["trace"]) == 5


if __name__ == "__main__":
    test_evaluator_initialization()
    test_simple_series_evaluation()
    test_result_to_dict()
    print("Evaluator tests passed!")