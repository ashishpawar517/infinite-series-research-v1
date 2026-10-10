"""Ramanujan Infinite Series Engine."""

from .evaluator import (
    SeriesEvaluator,
    SeriesResult,
    evaluate_formula_by_name,
    evaluate_ramanujan_pi,
)
from .formula import SeriesFormula

__version__ = "0.2.0"
__author__ = "Aashish Pawar"

__all__ = [
    "SeriesEvaluator",
    "SeriesFormula",
    "SeriesResult",
    "evaluate_formula_by_name",
    "evaluate_ramanujan_pi",
]
