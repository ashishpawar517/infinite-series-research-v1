"""Conjectural discovery pipeline (Phase 3 skeleton).

Method (Guillera-style + PSLQ, per research synthesis):
1. Enumerate hypergeometric candidates over small-integer parameter space:
     sum (a)_k (b)_k (c)_k / (1)_k^3 * P(k) * z^k, z = 1/m
   plus binomial families (C(2k,k)^3, Apery, Domb).
2. Numeric filter at modest dps (~50): |S_candidate - target| < tol.
3. PSLQ on [S, target, ...] to recover small A,B in P(k)=Ak+B.
4. Re-verify hit at P+50 digits (withheld-digits test).
5. Hand to verify.py (WZ gate) before promotion to the catalogue.

This module implements steps 1-2 plus a thin PSLQ wrapper (steps 3-4).
Nothing here claims proof; results are provenance="conjectured".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

import mpmath as mp


@dataclass
class Candidate:
    family: str
    z_inv: int  # z = 1/z_inv (or -1/z_inv when alternating)
    poly: tuple  # coefficients of P(k), low order first
    alternating: bool = False
    partial_sum: mp.mpf | None = None
    residual: mp.mpf | None = None


@dataclass
class DiscoveryResult:
    target: mp.mpf
    target_name: str
    candidates_evaluated: int
    hits: list[Candidate] = field(default_factory=list)
    working_precision: int = 50


def _poch(a: mp.mpf, n: int) -> mp.mpf:
    p = mp.mpf(1)
    for k in range(n):
        p *= a + k
    return p


def hypergeometric_term(a: mp.mpf, b: mp.mpf, c: mp.mpf, z: mp.mpf, n: int) -> mp.mpf:
    """Single term (a)_n (b)_n (c)_n / (1)_n^3 * z^n (no polynomial factor)."""
    return _poch(a, n) * _poch(b, n) * _poch(c, n) / (_poch(mp.mpf(1), n) ** 3) * (z**n)


def enumerate_candidates(
    families: Sequence[tuple[str, tuple[mp.mpf, mp.mpf, mp.mpf]]] | None = None,
    z_invs: Sequence[int] | None = None,
    max_poly_degree: int = 1,
    poly_range: int = 5,
    alternating_options: Sequence[bool] = (False,),
) -> list[Candidate]:
    """Build the search grid (no numeric evaluation yet)."""
    if families is None:
        families = [
            ("1/2,1/2,1/2", (mp.mpf("1/2"), mp.mpf("1/2"), mp.mpf("1/2"))),
            ("1/2,1/4,3/4", (mp.mpf("1/2"), mp.mpf("1/4"), mp.mpf("3/4"))),
            ("1/2,1/3,2/3", (mp.mpf("1/2"), mp.mpf("1/3"), mp.mpf("2/3"))),
            ("1/2,1/6,5/6", (mp.mpf("1/2"), mp.mpf("1/6"), mp.mpf("5/6"))),
        ]
    if z_invs is None:
        z_invs = [16, 32, 64, 81, 100, 256, 484, 9801]
    out: list[Candidate] = []
    for fam_name, _ in families:
        for m in z_invs:
            for alt in alternating_options:
                # P(k) with tiny integer coeffs; degree 0..max_poly_degree
                if max_poly_degree == 0:
                    out.append(Candidate(fam_name, m, (1,), alt))
                elif max_poly_degree == 1:
                    for a in range(-poly_range, poly_range + 1):
                        for b in range(-poly_range, poly_range + 1):
                            if a == 0 and b == 0:
                                continue
                            out.append(Candidate(fam_name, m, (a, b), alt))
                else:
                    out.append(Candidate(fam_name, m, (1, 1), alt))
    return out


def numeric_filter(
    target: mp.mpf,
    candidates: Sequence[Candidate],
    families: Sequence[tuple[str, tuple[mp.mpf, mp.mpf, mp.mpf]]] | None = None,
    terms: int = 30,
    dps: int = 50,
    tol: mp.mpf | float = mp.mpf("1e-30"),
) -> DiscoveryResult:
    """Evaluate each candidate's partial sum and keep |S - target| < tol."""
    fam_map = dict(families) if families else {}
    if not fam_map:
        fam_map = {
            "1/2,1/2,1/2": (mp.mpf("1/2"), mp.mpf("1/2"), mp.mpf("1/2")),
            "1/2,1/4,3/4": (mp.mpf("1/2"), mp.mpf("1/4"), mp.mpf("3/4")),
            "1/2,1/3,2/3": (mp.mpf("1/2"), mp.mpf("1/3"), mp.mpf("2/3")),
            "1/2,1/6,5/6": (mp.mpf("1/2"), mp.mpf("1/6"), mp.mpf("5/6")),
        }
    hits: list[Candidate] = []
    with mp.workdps(dps):
        target = +mp.mpf(target)
        tol = +mp.mpf(tol)
        for cand in candidates:
            a, b, c = fam_map[cand.family]
            z = mp.mpf(1) / mp.mpf(cand.z_inv)
            if cand.alternating:
                z = -z
            s = mp.mpf(0)
            for n in range(terms):
                pk = sum(coef * (n**i) for i, coef in enumerate(cand.poly))
                s += hypergeometric_term(a, b, c, z, n) * pk
            cand.partial_sum = +s
            cand.residual = abs(s - target)
            if cand.residual < tol:
                hits.append(cand)
    return DiscoveryResult(
        target=+target,
        target_name="target",
        candidates_evaluated=len(candidates),
        hits=hits,
        working_precision=dps,
    )


def pslq_identify(vector: Sequence[Any], dps: int = 80) -> list[int] | None:
    """Thin wrapper over mpmath.pslq; returns integer relation or None."""
    with mp.workdps(dps):
        rel = mp.pslq(list(vector))
    return list(rel) if rel else None
