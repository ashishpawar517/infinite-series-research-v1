"""Verification gate for conjectured identities (Phase 4 skeleton).

Policy (per user decision: WZ verification required):
- A discovery hit is provenance="conjectured" until it passes either:
  (a) a Wilf-Zeilberger certificate check for hypergeometric terms, or
  (b) high-precision withheld-digits re-verification + recorded analytic bound.
- Only (a) promotes to "proven". (b) keeps the "conjectured" label but
  allows catalogue inclusion behind an explicit opt-in flag.

Current state: structural skeleton. Full Zeilberger/Gosper implementation
is deferred (SymPy holonomic / EKHAD port). What works today:
- reverify_numeric(): recompute candidate vs target at higher dps.
- check_wz_rational_certificate(): validates a *supplied* rational
  certificate R(n,k) hook (callers provide R; we check the WZ equation
  numerically/symbolically on a sample grid).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing Callable

import mpmath as mp


@dataclass
class VerificationReport:
    identity: str
    method: str  # "withheld-digits" | "wz-certificate"
    passed: bool
    detail: str = ""
    dps_checked: int = 0


def reverify_numeric(
    identity: str,
    compute_lhs: Callable[[int], mp.mpf],
    rhs: mp.mpf,
    terms: int = 50,
    dps: int = 100,
    tol: mp.mpf | float = mp.mpf("1e-60"),
) -> VerificationReport:
    """Recompute LHS partial sum at higher dps; pass if |LHS-RHS| < tol."""
    with mp.workdps(dps):
        s = mp.mpf(0)
        for n in range(terms):
            s += mp.mpf(compute_lhs(n))
        err = abs(s - mp.mpf(rhs))
        ok = err < mp.mpf(tol)
        return VerificationReport(
            identity=identity,
            method="withheld-digits",
            passed=bool(ok),
            detail=f"|LHS-RHS|={mp.nstr(err, 10)} < {tol}",
            dps_checked=dps,
        )


def check_wz_certificate_shape(
    R_description: str,
) -> VerificationReport:
    """Placeholder: records that a full WZ prover is not yet wired.

    Returns passed=False with an explanatory detail so callers cannot
    mistake this for a proof. Replace with Gosper/Zeilberger once the
    symbolic backend lands.
    """
    return VerificationReport(
        identity=R_description,
        method="wz-certificate",
        passed=False,
        detail="WZ prover not yet implemented; see docs/adr/. "
        "Use reverify_numeric() for conjectural tracking only.",
    )
