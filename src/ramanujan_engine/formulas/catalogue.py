"""Curated catalogue of proven infinite-series formulas.

Covers the three computable tiers from the research synthesis:
- Fast hypergeometric (Ramanujan, Chudnovsky, exp) -> direct summation
- Logarithmic monotone (Basel/zeta(2)) -> Richardson/Levin demo
- Slow alternating (Leibniz pi/4, alternating log2) -> CVZ/Shanks demo

Every entry is a *proven* literature identity (provenance="proven").
Conjectured PSLQ hits live in discovery.py and are never auto-registered
here until they pass the WZ verification gate (verify.py).
"""

from __future__ import annotations

from typing import Dict, Type

import mpmath as mp

from ..formula import SeriesFormula


class RamanujanPiFormula(SeriesFormula):
    """Ramanujan's 1/pi series: ~8 digits/term (s=4 modular level)."""

    name = "ramanujan-pi"
    target = "pi"
    convergence_class = "direct"
    alternating = False

    def term(self, n: int) -> mp.mpf:
        num = mp.factorial(4 * n) * mp.mpf(1103 + 26390 * n)
        den = (mp.factorial(n) ** 4) * mp.mpf(396 ** (4 * n))
        return num / den

    def ratio(self, n: int) -> mp.mpf:
        num = (4 * n + 1) * (4 * n + 2) * (4 * n + 3) * (4 * n + 4)
        den = ((n + 1) ** 4) * (396**4)
        # ratio of c_n; polynomial factor handled by evaluator via term(),
        # here return full t_{n+1}/t_n including linear factor.
        c_ratio = mp.mpf(num) / mp.mpf(den)
        return c_ratio * mp.mpf(1103 + 26390 * (n + 1)) / mp.mpf(1103 + 26390 * n)

    def transform(self, partial_sum: mp.mpf) -> mp.mpf:
        if partial_sum == 0:
            return mp.mpf("inf")
        k = mp.mpf(9801) / (mp.mpf(2) * mp.sqrt(mp.mpf(2)))
        return k / partial_sum

    def tail_bound(self, N: int, last_term: mp.mpf) -> mp.mpf | None:
        # q = (256/396^4)(1+26390/1103); remainder T_N <= t_N/(1-q),
        # mapped to pi space as K*B/S^2. Needs S_N: recompute cheaply is
        # caller-side; here return bound in *sum* space scaled by caller.
        # To keep the interface simple (transformed space), we return the
        # sum-space bound and let the evaluator map it — documented.
        # Actually compute transformed bound requires S_N; evaluator passes
        # last_term = t_N and does the mapping itself for this formula.
        # Return None here; evaluator special-cases via transform_bound().
        return None

    def transform_bound(self, bound_sum: mp.mpf, partial_sum: mp.mpf) -> mp.mpf:
        k = mp.mpf(9801) / (mp.mpf(2) * mp.sqrt(mp.mpf(2)))
        if partial_sum == 0:
            return mp.mpf("inf")
        return k * bound_sum / (partial_sum**2)

    def reference(self, dps: int) -> mp.mpf:
        with mp.workdps(dps):
            return +mp.pi


class ChudnovskyPiFormula(SeriesFormula):
    """Chudnovsky 1/pi series: ~14 digits/term (Heegner d=163)."""

    name = "chudnovsky-pi"
    target = "pi"
    convergence_class = "direct"
    alternating = True

    def term(self, n: int) -> mp.mpf:
        num = mp.factorial(6 * n) * mp.mpf(13591409 + 545140134 * n)
        den = (mp.factorial(3 * n) * (mp.factorial(n) ** 3)) * mp.mpf(
            640320 ** (3 * n)
        )
        return (mp.mpf(-1) ** n) * num / den

    def ratio(self, n: int) -> mp.mpf:
        # t_{n+1}/t_n = -(6n+1..6n+6)/( (3n+1..3n+3)(n+1)^3 640320^3 )
        #              * (A+B(n+1))/(A+Bn)
        num = 1
        for k in range(1, 7):
            num *= 6 * n + k
        den = 1
        for k in range(1, 4):
            den *= 3 * n + k
        den *= (n + 1) ** 3 * (640320**3)
        r = -mp.mpf(num) / mp.mpf(den)
        return r * mp.mpf(13591409 + 545140134 * (n + 1)) / mp.mpf(
            13591409 + 545140134 * n
        )

    def transform(self, partial_sum: mp.mpf) -> mp.mpf:
        if partial_sum == 0:
            return mp.mpf("inf")
        k = mp.mpf(640320) ** mp.mpf("1.5") / mp.mpf(12)
        return k / partial_sum

    def reference(self, dps: int) -> mp.mpf:
        with mp.workdps(dps):
            return +mp.pi


class ExpEFormula(SeriesFormula):
    """e = sum 1/n! (fast hypergeometric, direct)."""

    name = "exp-e"
    target = "e"
    convergence_class = "direct"

    def term(self, n: int) -> mp.mpf:
        return mp.mpf(1) / mp.factorial(n)

    def ratio(self, n: int) -> mp.mpf:
        return mp.mpf(1) / mp.mpf(n + 1)

    def reference(self, dps: int) -> mp.mpf:
        with mp.workdps(dps):
            return +mp.e


class BaselZeta2Formula(SeriesFormula):
    """zeta(2) = sum 1/n^2 = pi^2/6 (logarithmic monotone -> Richardson)."""

    name = "basel-zeta2"
    target = "zeta(2)"
    convergence_class = "logarithmic"

    def term(self, n: int) -> mp.mpf:
        k = n + 1  # n=0 -> 1/1^2
        return mp.mpf(1) / mp.mpf(k * k)

    def reference(self, dps: int) -> mp.mpf:
        with mp.workdps(dps):
            return +mp.zeta(2)


class LeibnizPi4Formula(SeriesFormula):
    """pi/4 = sum (-1)^n/(2n+1) (slow alternating -> CVZ/Shanks demo)."""

    name = "leibniz-pi4"
    target = "pi/4"
    convergence_class = "linear"
    alternating = True

    def term(self, n: int) -> mp.mpf:
        return (mp.mpf(-1) ** n) / mp.mpf(2 * n + 1)

    def transform(self, partial_sum: mp.mpf) -> mp.mpf:
        return 4 * partial_sum

    def reference(self, dps: int) -> mp.mpf:
        with mp.workdps(dps):
            return +mp.pi


class AlternatingLog2Formula(SeriesFormula):
    """log(2) = sum_{n>=1} (-1)^{n+1}/n (slow alternating -> CVZ demo)."""

    name = "alt-log2"
    target = "log(2)"
    convergence_class = "linear"
    alternating = True

    def term(self, n: int) -> mp.mpf:
        k = n + 1
        return (mp.mpf(-1) ** (k + 1)) / mp.mpf(k)

    def reference(self, dps: int) -> mp.mpf:
        with mp.workdps(dps):
            return +mp.log(2)


CATALOGUE: Dict[str, Type[SeriesFormula]] = {
    cls.name: cls
    for cls in (
        RamanujanPiFormula,
        ChudnovskyPiFormula,
        ExpEFormula,
        BaselZeta2Formula,
        LeibnizPi4Formula,
        AlternatingLog2Formula,
    )
}


def get_formula(name: str) -> SeriesFormula:
    """Instantiate a catalogue formula by name; raises KeyError if unknown."""
    try:
        return CATALOGUE[name]()
    except KeyError:
        raise KeyError(
            f"unknown formula {name!r}; available: {sorted(CATALOGUE)}"
        ) from None


def list_formulas() -> list[str]:
    return sorted(CATALOGUE)
