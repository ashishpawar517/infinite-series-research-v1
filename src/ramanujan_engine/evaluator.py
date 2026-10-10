"""Generic evaluator for infinite series computations.

Supports two styles:
- Legacy: evaluate_series(formula_name, term_generator, terms, ...)
- Formula-based (preferred): evaluate_formula(formula, terms,
  accelerator='auto'|'direct'|'richardson'|'wynn-epsilon'|'levin-u'|'cvz', ...)

The Formula path uses ratio() recurrence when available (no factorials),
builds per-term partial sums, then applies the selected accelerator to the
tail of the partial-sum sequence before mapping to constant space.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

import mpmath as mp

from .accelerators import ACCELERATORS, recommend

try:
    from .formula import SeriesFormula
except ImportError:  # pragma: no cover - for direct script use
    SeriesFormula = object  # type: ignore


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
    accelerator: str = "direct"
    provenance: str = "proven"

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
            "accelerator": self.accelerator,
            "provenance": self.provenance,
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

    # -- Formula-based path (preferred) ----------------------------------
    def evaluate_formula(
        self,
        formula: "SeriesFormula",
        terms: int,
        accelerator: str = "auto",
        compute_trace: bool = False,
        use_recurrence: bool = True,
        accel_window: int = 12,
    ) -> SeriesResult:
        """Evaluate a SeriesFormula with optional convergence acceleration."""
        if terms < 1:
            raise ValueError("terms must be a positive integer")
        start_time = time.perf_counter()
        if accelerator == "auto":
            accelerator = recommend(
                getattr(formula, "convergence_class", "direct"),
                getattr(formula, "alternating", False),
            )
        accel_fn = ACCELERATORS.get(accelerator, ACCELERATORS["direct"])

        with mp.workdps(self.precision):
            partials: list[mp.mpf] = []
            running = mp.mpf(0)
            trace: list = []
            t_n = mp.mpf(0)
            # Iterative recurrence: t_0 via term(0), then ratio stepping.
            ratio_fn = getattr(formula, "ratio", None)
            use_rec = (
                use_recurrence and callable(ratio_fn) and ratio_fn(0) is not None
            )
            if use_rec:
                t_n = mp.mpf(formula.term(0))
                for n in range(terms):
                    if n > 0:
                        assert ratio_fn is not None
                        t_n = t_n * mp.mpf(ratio_fn(n - 1))
                    running += t_n
                    partials.append(+running)
                    if compute_trace:
                        trace.append((n, +running))
            else:
                for n in range(terms):
                    t_n = mp.mpf(formula.term(n))
                    running += t_n
                    partials.append(+running)
                    if compute_trace:
                        trace.append((n, +running))

            window = partials[-accel_window:] if len(partials) > accel_window else partials
            try:
                if accelerator == "direct":
                    accel_sum = partials[-1]
                elif accelerator == "levin-u":
                    term_list = [partials[0]] + [
                        partials[i] - partials[i - 1] for i in range(1, len(window))
                    ]
                    accel_sum = accel_fn(window, term_list)
                else:
                    accel_sum = accel_fn(window)
            except Exception:
                accel_sum = partials[-1]
                accelerator = "direct(fallback)"

            value = formula.transform(accel_sum)

            analytic_bound = None
            bound_label = None
            try:
                b = formula.tail_bound(terms, t_n)
                if b is not None:
                    # Ramanujan-style formulas need S_N mapping; support
                    # optional transform_bound hook.
                    hook = getattr(formula, "transform_bound", None)
                    if callable(hook):
                        # Recompute sum-space geometric bound here for the
                        # Ramanujan case (q known analytically).
                        q = mp.mpf(256) / mp.mpf(396**4) * mp.mpf(
                            1 + mp.mpf(26390) / mp.mpf(1103)
                        )
                        b_sum = abs(t_n) / (mp.mpf(1) - q)
                        analytic_bound = hook(b_sum, running)
                    else:
                        analytic_bound = b
                    bound_label = "analytic truncation-error bound"
            except Exception:
                analytic_bound = None

            elapsed = time.perf_counter() - start_time
            return SeriesResult(
                formula_name=getattr(formula, "name", "formula"),
                terms_evaluated=terms,
                working_precision=self.precision,
                value=+value,
                partial_sum=+running,
                final_term_magnitude=abs(t_n),
                trace=trace,
                analytic_bound=analytic_bound,
                bound_label=bound_label,
                status="completed",
                elapsed_time=elapsed,
                accelerator=accelerator,
                provenance=getattr(formula, "provenance", "proven"),
            )

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

        with mp.workdps(self.precision):

            partial_sum = mp.mpf(0)
            trace = [] if compute_trace else None
            final_term = mp.mpf(0)

            for n in range(terms):
                term = term_generator(n)
                partial_sum += term
                final_term = term

                if compute_trace:
                    assert trace is not None
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

    from .formulas.catalogue import RamanujanPiFormula

    evaluator = SeriesEvaluator(precision)
    result = evaluator.evaluate_formula(
        RamanujanPiFormula(), terms, accelerator="direct",
        compute_trace=compute_trace,
    )
    # Legacy display name expected by CLI/tests.
    result.formula_name = "Ramanujan's pi formula"
    return result


def evaluate_formula_by_name(
    name: str,
    terms: int = 10,
    precision: int = 50,
    accelerator: str = "auto",
    compute_trace: bool = False,
) -> SeriesResult:
    """Evaluate any catalogue formula by name with accelerator selection."""
    if terms < 1:
        raise ValueError("terms must be a positive integer")
    if precision < 1:
        raise ValueError("precision must be a positive integer")
    from .formulas.catalogue import get_formula

    formula = get_formula(name)
    return SeriesEvaluator(precision).evaluate_formula(
        formula, terms, accelerator=accelerator, compute_trace=compute_trace,
    )
