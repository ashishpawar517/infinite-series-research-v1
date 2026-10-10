"""Abstract interface for infinite-series formulas.

A Formula describes HOW to compute terms for a constant; the Evaluator
decides HOW MANY terms and WHICH accelerator to use. This split lets us
add new constants (catalogue) and conjectured series (discovery) without
touching evaluation logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import mpmath as mp


class SeriesFormula(ABC):
    """Pluggable definition of an infinite series for a constant."""

    #: Unique string, e.g. "ramanujan-pi", "chudnovsky-pi", "exp-e".
    name: str = "unnamed"
    #: Human description of the target, e.g. "pi", "e", "log(2)".
    target: str = "unknown"
    #: 'direct' (fast hypergeometric), 'alternating-slow',
    #: 'logarithmic' (monotone like 1/n^2), 'geometric'.
    convergence_class: str = "direct"
    #: True when terms alternate in sign (enables CVZ/Shanks).
    alternating: bool = False
    #: Provenance: "proven" for literature identities, "conjectured" for PSLQ hits.
    provenance: str = "proven"

    @abstractmethod
    def term(self, n: int) -> mp.mpf:
        """Return the nth summand t_n (0-indexed)."""
        raise NotImplementedError

    def ratio(self, n: int) -> Optional[mp.mpf]:
        """Return t_{n+1}/t_n if a stable recurrence exists, else None.

        Hypergeometric terms should override this so the evaluator can
        iterate without factorials/overflow.
        """
        return None

    def transform(self, partial_sum: mp.mpf) -> mp.mpf:
        """Map raw partial sum S_N to the target constant (default identity)."""
        return partial_sum

    def tail_bound(self, N: int, last_term: mp.mpf) -> Optional[mp.mpf]:
        """Analytic truncation-error bound on the remainder after N terms.

        Returns bound in *transformed* (constant) space, or None when the
        formula has no proven bound yet.
        """
        return None

    def reference(self, dps: int) -> mp.mpf:
        """High-precision reference value of the target for validation."""
        raise NotImplementedError
