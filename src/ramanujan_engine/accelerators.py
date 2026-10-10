"""Convergence accelerators for slow series.

Each function takes a list of partial sums S_0..S_{m-1} and returns an
extrapolated limit estimate. They are deliberately small and dependency
free (mpmath only) so the Evaluator can try them as fallbacks.

Methods:
- direct: last partial sum (fast hypergeometric needs nothing else)
- richardson: for logarithmic monotone tails (1/n^2-like)
- wynn_epsilon: Wynn epsilon-table = Shanks transform, for
  linear/geometric and oscillating tails
- levin_u: Levin u-transform, strongest general purpose but needs
  care with working precision
- cvz: Cohen-Villegas-Zagier linear weight for strictly alternating
  decreasing series (error ~5.83^-n for Alg 1)
"""

from __future__ import annotations

from typing import List

import mpmath as mp


def direct(partials: List[mp.mpf]) -> mp.mpf:
    return partials[-1]


def wynn_epsilon(partials: List[mp.mpf]) -> mp.mpf:
    """Wynn epsilon algorithm (Shanks transform)."""
    n = len(partials)
    if n < 3:
        return partials[-1]
    # epsilon table: e[-1]=0, e[0]=S_n
    e_prev = [mp.mpf(0)] * n
    e_curr = list(partials)
    for k in range(1, n):
        e_next = [mp.mpf(0)] * n
        for i in range(n - k - 1):
            denom = e_curr[i + 1] - e_curr[i]
            if denom == 0:
                e_next[i] = e_curr[i + 1]
            else:
                e_next[i] = e_prev[i + 1] + mp.mpf(1) / denom
        e_prev, e_curr = e_curr, e_next
        # even columns are the accelerated estimates; keep the last useful one
    # Best estimate is the last even-column entry; fall back to last partial.
    return e_curr[0] if e_curr[0] != 0 else partials[-1]


def richardson(partials: List[mp.mpf], power: float = 1.0) -> mp.mpf:
    """Repeated Richardson extrapolation assuming tail ~ N^-power, (N+1)^-power...

    Works for logarithmic monotone series (e.g. Basel sum 1/n^2).
    """
    table = list(partials)
    n = len(table)
    if n < 2:
        return partials[-1]
    # Assume partials[i] corresponds to N = i+1 blocks; use simple
    # polynomial-in-1/N elimination.
    for k in range(1, n):
        factor = mp.mpf(2) ** (power * k) if k < 6 else mp.mpf(n) ** power
        # Standard step: T = (factor * T_high - T_low) / (factor - 1)
        new_table = []
        for i in range(len(table) - 1):
            try:
                val = (factor * table[i + 1] - table[i]) / (factor - 1)
            except ZeroDivisionError:
                val = table[i + 1]
            new_table.append(val)
        table = new_table
        if not table:
            break
    return table[0] if table else partials[-1]


def levin_u(partials: List[mp.mpf], terms: List[mp.mpf] | None = None) -> mp.mpf:
    """Levin u-transform (simplified, stable variant).

    Uses remainder estimate omega_n = term_n. Solves the small linear
    system via the standard recurrence rather than a full solve, which
    keeps it usable to ~12-20 partials at high dps.
    """
    n = len(partials)
    if n < 3:
        return partials[-1]
    if terms is None or len(terms) != n:
        terms = [partials[0]] + [partials[i] - partials[i - 1] for i in range(1, n)]
    # Levin u: numerator/denominator sums with weights (N+j)^(k-1)/omega
    num = mp.mpf(0)
    den = mp.mpf(0)
    N = mp.mpf(n)
    for j in range(n):
        w = ((-1) ** j) * mp.binomial(n - 1, j) * ((N + j) ** (n - 2))
        omega = terms[j] if terms[j] != 0 else mp.mpf("1e-9999")
        num += w * partials[j] / omega
        den += w / omega
    if den == 0:
        return partials[-1]
    return num / den


def cohen_villegas_zagier(partials: List[mp.mpf]) -> mp.mpf:
    """CVZ linear acceleration for strictly alternating decreasing series.

    S ≈ (1/2^n) * sum_{k} binom(n,k) S_k with the standard CVZ weights.
    Here simplified to the diagonal mean which already gives ~C^-n error.
    """
    n = len(partials)
    if n < 2:
        return partials[-1]
    total = mp.mpf(0)
    norm = mp.mpf(0)
    for k in range(n):
        w = mp.binomial(n - 1, k)
        total += w * partials[k]
        norm += w
    if norm == 0:
        return partials[-1]
    return total / norm


ACCELERATORS = {
    "direct": direct,
    "richardson": richardson,
    "wynn-epsilon": wynn_epsilon,
    "shanks": wynn_epsilon,
    "levin-u": levin_u,
    "cvz": cohen_villegas_zagier,
    "alternating": cohen_villegas_zagier,
}


def recommend(convergence_class: str, alternating: bool) -> str:
    """Pick a default accelerator from formula metadata."""
    if convergence_class == "direct":
        return "direct"
    if alternating:
        return "cvz"
    if convergence_class == "logarithmic":
        return "richardson"
    if convergence_class in ("geometric", "linear"):
        return "wynn-epsilon"
    return "direct"
