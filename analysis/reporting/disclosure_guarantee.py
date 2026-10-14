"""Guaranteed information value of reporting changes (Section 5; Table 5; Online Appendix Table C28).

For a reporting change that publishes S·l (a linear function of the allocation l), the largest within-gu width that
can remain, whatever the true allocation in Lambda, is

    W_S^max = max_{l, l' in Lambda} c'(l - l')  subject to  S l = S l',

the largest difference in the slope between two allocations that the new report cannot tell apart. Jurisdictions
share no constraint, so W_S^max is the sum of per-jurisdiction LPs over two linked copies of Lambda. 1 - W_S^max / W_0
is the share of the current width W_0 removed for every possible true allocation.

Proposals: P2 (pooled ballots by registered dong), P2b (out-of-zone early ballots only), P1 (early-voter headcounts by
registered dong x station; no vote choice), P12 (both). Headcounts make movement observed, so P1 and P12 are evaluated
with the movement cap removed and compared with current reporting under the same composition restrictions and no
movement assumption (W_0^free) as well as with the main W_0.
Output: results/disclosure_guarantee_<sg>.csv (one election) or results/disclosure_guarantee.csv (several)"""
import numpy as np
import pandas as pd
import scipy.sparse as sp
from vwn.run import Prep, timer, elections_from_argv
from vwn.bounds import slope_c, total
from vwn.lp import hs_solve
from vwn.paths import RES


def selector(lp, prop):
    n = lp.nv; rows = []
    if prop in ("P2", "P2b", "P12"): rows += [("v", k) for k in range(lp.oB, lp.oB + lp.nB)]
    if prop in ("P2", "P12"): rows += [("v", k) for k in range(lp.oG, lp.oG + lp.nG)]
    if prop in ("P1", "P12"):
        rows += [("h", (i, j)) for i in range(lp.n) for j in range(lp.n)]
    ri, ci = [], []
    for r, (kind, k) in enumerate(rows):
        if kind == "v": ri.append(r); ci.append(k)
        else:
            i, j = k
            for c in range(lp.C): ri.append(r); ci.append(lp.iF(i, j, c))
    return sp.csr_matrix((np.ones(len(ri)), (ri, ci)), shape=(len(rows), n))


def wmax(lp, w, eta, delta, prop, report_tolerance=0.0):
    """Maximum width with equal reports, or an outer bound for bounded report differences.

    A positive tolerance imposes |S(l-l')| <= tolerance componentwise. For
    primary suppression of integer counts below k, same-report pairs satisfy
    this condition with tolerance k-1. The relaxation need not be sharp for
    that nonlinear suppression rule; it gives a conservative width bound.
    """
    if not np.isfinite(report_tolerance) or report_tolerance < 0:
        raise ValueError('report_tolerance must be finite and non-negative')
    Aeq, beq, Aub, bub = lp.cached_constraints(eta, delta); c, _ = slope_c(lp, w)
    if not np.any(c): return 0.0
    S = selector(lp, prop)
    difference = sp.hstack([S, -S]).tocsr()
    AE = sp.block_diag([Aeq, Aeq]).tocsr(); bE = np.r_[beq, beq]
    AU = sp.block_diag([Aub, Aub]).tocsr(); bU = np.r_[bub, bub]
    if report_tolerance == 0:
        AE = sp.vstack([AE, difference]).tocsr()
        bE = np.r_[bE, np.zeros(S.shape[0])]
    else:
        AU = sp.vstack([AU, difference, -difference]).tocsr()
        bU = np.r_[bU, np.full(2 * S.shape[0], report_tolerance)]
    r = hs_solve(np.r_[-c, c], AU, bU, AE, bE)
    if r.status != 0: raise RuntimeError(f"status {r.status}")
    return -r.fun


def run(sg):
    log = timer(); P = Prep(sg); W = P.W["guFE"]; rows = []
    cfgs = [(f"uniform eta={e}", False, e, 1.0, None) for e in [0.0, 0.05, 0.1, 0.2, 0.3]]
    if sg != "20170509":
        cfgs += [("calib lambda=0.5", True, 0.5, 1.0, None), ("calib", True, 1.0, 1.0, None), ("calib, s=0.02", True, 1.0, 1.0, 0.02),
                 ("calib, delta=0.1", True, 1.0, 0.1, None), ("calib, delta=0.1, s=0.02", True, 1.0, 0.1, 0.02)]
    for name, calib, eta, delta, s in cfgs:
        dF = None if s is None else ("slack", s)
        LP = P.lps(calib=calib, dF=dF); LPf = P.lps(calib=False, dF=dF)
        lo, hi = total(P.units, LP, W, eta, delta); W0 = hi - lo
        lof, hif = total(P.units, LPf, W, 10.0, delta); W0f = hif - lof
        rec = dict(sg=sg, config=name, W0=W0, W0_free=W0f)
        for prop in ["P2", "P2b", "P1", "P12"]:
            if prop in ("P1", "P12"): Wm = sum(wmax(LPf[u], W[u], 10.0, delta, prop) for u in P.units)
            else: Wm = sum(wmax(LP[u], W[u], eta, delta, prop) for u in P.units)
            rec[f"Wmax_{prop}"] = Wm
        rows.append(rec); log(sg, name, {k: round(v, 3) for k, v in rec.items() if isinstance(v, float)})
    return rows


if __name__ == "__main__":
    import sys
    out = []
    for sg in elections_from_argv(["20170509", "20220309", "20240410", "20250603", "20260603"]):
        out += run(sg)
        pd.DataFrame(out).to_csv(f"{RES}/disclosure_guarantee{'_' + sg if len(sys.argv) == 2 else ''}.csv", index=False)
