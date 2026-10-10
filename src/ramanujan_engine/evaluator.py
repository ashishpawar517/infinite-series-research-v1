"""Generic evaluator for infinite series computations."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

import mpmath as mp


@dataclass
class SeriesResult:
    """Result of a series evaluation."""

    formula_name: str
    terms_evaluated: int
    working_precision: int
    value: mp.mpf
    partial_sum: mp.mpf
    final_term_magnitude: Optional[mp.mpf] = None
    trace: List[tuple[int, mp.mpf]] = field(default_factory=list)
    analytic_bound: Optional[mp.mpf] = None
    bound_label: Optional[str] = None
    status: str = "completed"
    elapsed_time: float = field(default_factory=float)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary for serialization."""
        result = {
            "formula_name": self.formula_name,
            "terms_evaluated": self.terms_evaluated,
            "working_precision": self.working_precision,
            "value": mp.nstr(self.value, self.working_precision),
            "partial_sum": mp.nstr(self.partial_sum, self.working_precision),
            "status": self.status,
            "elapsed_time": self.elapsed_time,
        }

        if self.final_term_magnitude is not None:
            result["final_term_magnitude"] = mp.nstr(
                self.final_term_magnitude, self.working_precision
            )

        if self.trace:
            result["trace"] = [
                (n, mp.nstr(term, self.working_precision))
                for n, term in self.trace
            ]

        if self.analytic_bound is not None:
            result["analytic_bound"] = mp.nstr(
                self.analytic_bound, self.working_precision
            )
            if self.bound_label:
                result["bound_label"] = self.bound_label

        return result


class SeriesEvaluator:
    """Generic evaluator for infinite series with arbitrary precision."""

    def __init__(self, precision: int = 50):
        """
        Initialize evaluator with working precision.

        Args:
            precision: Number of decimal digits for working precision
        """
        self.precision = precision
        # Use a local context to avoid affecting global mpmath state
        self.ctx = mp.workprec(precision)

    def evaluate_series(
        self,
        formula_name: str,
        term_generator: Callable[[int], mp.mpf],
        terms: int,
        compute_trace: bool = False,
        bound_calculator: Optional[Callable[[int, mp.mpf], mp.mpf]] = None,
    ) -> SeriesResult:
        """
        Evaluate a series for a given number of terms.

        Args:
            formula_name: Identifier for the formula being evaluated
            term_generator: Function that returns the nth term (0-indexed)
            terms: Number of terms to evaluate (sum from n=0 to terms-1)
            compute_trace: Whether to collect partial sums for tracing
            bound_calculator: Optional function to compute analytic bound

        Returns:
            SeriesResult containing the evaluation outcome
        """
        start_time = time.perf_counter()

        with self.ctx:
            mp.mp.dps = self.precision

            partial_sum = mp.mpf(0)
            trace = [] if compute_trace else None
            final_term = mp.mpf(0)

            for n in range(terms):
                term = term_generator(n)
                partial_sum += term
                final_term = term

                if compute_trace:
                    trace.append((n, mp.mpf(partial_sum)))

            # Calculate final result (this will be formula-specific in subclasses)
            value = self._transform_to_pi(partial_sum)

            # Calculate analytic bound if provided
            analytic_bound = None
            bound_label = None
            if bound_calculator and terms > 0:
                # Bound represents the maximum possible remainder
                bound_term = bound_calculator(terms - 1, final_term)
                analytic_bound = self._transform_bound_to_pi(bound_term, partial_sum)
                bound_label = "analytic truncation-error bound"

            elapsed_time = time.perf_counter() - start_time

            return SeriesResult(
                formula_name=formula_name,
                terms_evaluated=terms,
                working_precision=self.precision,
                value=value,
                partial_sum=partial_sum,
                final_term_magnitude=abs(final_term),
                trace=trace or [],
                analytic_bound=analytic_bound,
                bound_label=bound_label,
                status="completed",
                elapsed_time=elapsed_time,
            )

    def _transform_to_pi(self, partial_sum: mp.mpf) -> mp.mpf:
        """
        Transform partial sum to the target constant (pi).
        To be overridden by specific formula implementations.

        Args:
            partial_sum: The raw partial sum of the series

        Returns:
            The transformed value (approximation of pi)
        """
        # Default identity transformation - subclasses should override
        return partial_sum

    def _transform_bound_to_pi(
        self,
        bound_term: mp.mpf,
        partial_sum: mp.mpf
    ) -> mp.mpf:
        """
        Transform analytic bound to pi space.
        To be overridden by specific formula implementations.

        Args:
            bound_term: The bound on the remainder term
            partial_sum: The current partial sum

        Returns:
            The bound transformed to pi space
        """
        # Default identity transformation - subclasses should override
        return bound_term


class RamanujanPiEvaluator(SeriesEvaluator):
    """Specialized evaluator for Ramanujan's pi formula."""

    def _transform_to_pi(self, partial_sum: mp.mpf) -> mp.mpf:
        """
        Transform partial sum to pi for Ramanujan's formula.
        pi = 9801 / (2*sqrt(2)) * 1 / sum(t_n)

        Args:
            partial_sum: The raw partial sum of t_n terms

        Returns:
            The pi approximation
        """
        if partial_sum == 0:
            return mp.mpf('inf')
        constant = mp.mpf(9801) / (mp.mpf(2) * mp.sqrt(mp.mpf(2)))
        return constant / partial_sum

    def _transform_bound_to_pi(
        self,
        bound_term: mp.mpf,
        partial_sum: mp.mpf
    ) -> mp.mpf:
        """
        Transform analytic bound to pi space for Ramanujan's formula.
        If pi_N = K/S_N and we have bound B_N on T_N (remainder), then
        0 <= pi_N - pi <= K * B_N / S_N^2

        Args:
            bound_term: The bound on the remainder term T_N
            partial_sum: The current partial sum S_N

        Returns:
            The bound transformed to pi space (error bound)
        """
        if partial_sum == 0:
            return mp.mpf('inf')
        constant = mp.mpf(9801) / (mp.mpf(2) * mp.sqrt(mp.mpf(2)))
        return constant * bound_term / (partial_sum ** 2)


def evaluate_ramanujan_pi(
    terms: int = 1,
    precision: int = 50,
    compute_trace: bool = False,
) -> SeriesResult:
    """
    Convenience function to evaluate Ramanujan's pi formula.

    Args:
        terms: Number of terms to evaluate (sum from n=0 to terms-1)
        precision: Working precision in decimal digits
        compute_trace: Whether to compute convergence trace

    Returns:
        SeriesResult with the pi approximation
    """
    if terms < 1:
        raise ValueError("terms must be a positive integer")
    if precision < 1:
        raise ValueError("precision must be a positive integer")

    evaluator = RamanujanPiEvaluator(precision)

    # Ramanujan's formula components
    # c_n = (4n)! / (n!)^4 / 396^(4n)
    # t_n = c_n * (1103 + 26390*n)
    # pi = 9801 / (2*sqrt(2)) * 1 / sum(t_n)

    def compute_c_n(n: int) -> mp.mpf:
        """Compute c_n using recurrence."""
        with evaluator.ctx:
            mp.mp.dps = evaluator.precision

            if n == 0:
                return mp.mpf(1)
            else:
                # Use recurrence: c_{n} = c_{n-1} * (4n-3)(4n-2)(4n-1)(4n) / (n^4 * 396^4)
                c_prev = compute_c_n(n - 1)
                numerator = (4*n - 3) * (4*n - 2) * (4*n - 1) * (4*n)
                denominator = (n**4) * (396**4)
                return c_prev * mp.mpf(numerator) / mp.mpf(denominator)

    def term_generator(n: int) -> mp.mpf:
        """Generate the nth term t_n = c_n * (1103 + 26390*n)."""
        with evaluator.ctx:
            mp.mp.dps = evaluator.precision
            c_n = compute_c_n(n)
            t_n = c_n * mp.mpf(1103 + 26390 * n)
            return t_n

    def bound_calculator(n: int, t_n: mp.mpf) -> mp.mpf:
        """
        Calculate the analytic bound for the Ramanujan series.
        Based on the derivation in Section 4 of the plan.
        """
        with evaluator.ctx:
            mp.mp.dps = evaluator.precision

            # q = (256 / 396^4) * (1 + 26390/1103)
            q = mp.mpf(256) / mp.mpf(396**4) * mp.mpf(1 + mp.mpf(26390)/mp.mpf(1103))

            # Bound on remainder: T_N <= t_N / (1 - q)
            bound = t_n / (mp.mpf(1) - q)
            return bound

    # Evaluate the series
    result = evaluator.evaluate_series(
        formula_name="Ramanujan's pi formula",
        term_generator=term_generator,
        terms=terms,
        compute_trace=compute_trace,
        bound_calculator=bound_calculator,
    )

    return result