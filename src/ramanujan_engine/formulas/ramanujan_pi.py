"""Ramanujan's formula for 1/pi implementation."""

from __future__ import annotations

import mpmath as mp
from typing import Any

from ..evaluator import SeriesResult, SeriesEvaluator


def evaluate_ramanujan_pi_direct(
    terms: int = 1,
    precision: int = 50,
    compute_trace: bool = False,
) -> SeriesResult:
    """
    Evaluate Ramanujan's pi formula using direct factorial calculation.
    Primarily used for testing and validation of the recurrence approach.

    Args:
        terms: Number of terms to evaluate
        precision: Working precision in decimal digits
        compute_trace: Whether to compute convergence trace

    Returns:
        SeriesResult with the pi approximation
    """
    if terms < 1:
        raise ValueError("terms must be a positive integer")
    if precision < 1:
        raise ValueError("precision must be a positive integer")

    evaluator = SeriesEvaluator(precision)

    def term_generator(n: int) -> mp.mpf:
        with evaluator.ctx:
            mp.mp.dps = evaluator.precision

            # Direct calculation: t_n = (4n)!/(n!)^4 * (1103+26390*n) / 396^(4n)
            numerator = mp.factorial(4 * n) * mp.mpf(1103 + 26390 * n)
            denominator = (mp.factorial(n) ** 4) * mp.mpf(396 ** (4 * n))
            t_n = numerator / denominator
            return t_n

    result = evaluator.evaluate_series(
        formula_name="Ramanujan's pi formula (direct)",
        term_generator=term_generator,
        terms=terms,
        compute_trace=compute_trace,
    )

    # Apply the pi transformation
    with evaluator.ctx:
        mp.mp.dps = evaluator.precision
        constant = mp.mpf(9801) / (mp.mpf(2) * mp.sqrt(mp.mpf(2)))
        result.value = constant / result.partial_sum if result.partial_sum != 0 else mp.mpf('inf')

    return result


def create_ramanujan_pi_evaluator(precision: int = 50) -> SeriesEvaluator:
    """
    Create a pre-configured evaluator for Ramanujan's pi formula.

    Args:
        precision: Working precision in decimal digits

    Returns:
        Configured SeriesEvaluator instance
    """
    return SeriesEvaluator(precision)