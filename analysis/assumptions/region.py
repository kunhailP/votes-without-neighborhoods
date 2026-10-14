"""Where the within-gu sign holds: R_t = {(lambda, delta, s): lower bound > 0} (Figure 4; Online Appendix Table C8),
and the allocation at the edge of R_t along s (Table C14; Online Appendix Table C15).

For each calibrated-flow multiple lambda (and unrestricted movement, eta = 2) and each out-of-zone band delta, s*(lambda,
delta) is the largest slack on residents' in-zone early composition at which the lower bound is positive (bisection on
[s_min, 0.30]; infinity if positive with residents' composition unrestricted; s_min if not positive at the smallest
feasible slack). R_t is the set of (lambda, delta, s) with s < s*(lambda, delta).

Edge allocation (lambda = 1): at s just above s* (the upper end of the final bisection interval), the allocation that
attains the minimum slope, which is the first allocation with a non-positive slope along s with lambda and delta held
fixed. Its departure of residents' early composition beyond the station's is at most s in every dong.
Outputs: results/region_<sg>.csv, results/edge_profile_<sg>.csv"""
import numpy as np
import pandas as pd
from vwn.run import Prep, timer, elections_from_argv
from vwn.bounds import total, slope_c
from vwn.paths import RES
from extremal import describe, terciles

LAMS = [0.5, 1.0, 1.5, 2.0, 3.0]; DELTAS = [0.1, 0.15, 0.2, 0.3, 0.5, 1.0]; SMAX = 0.3; TOL = 0.3 / 256


def sstar(P, LP, W, eta, dl):
    def f(s):
        for u in P.units: LP[u].dF = None if s is None else ("slack", s)
        return total(P.units, LP, W, eta, dl)[0]
    fnone = f(None)
    if not np.isnan(fnone) and fnone > 0: return np.inf, np.inf, 0.0, fnone
    smin = 0.0; f0 = f(0.0)
    if np.isnan(f0):
        a, b = 0.0, SMAX
        while b - a > TOL / 4:
            m = (a + b) / 2
            if np.isnan(f(m)): a = m
            else: b = m
        smin = b; f0 = f(smin)
    if np.isnan(f0) or f0 <= 0: return smin, smin, smin, fnone
    if f(SMAX) > 0: return SMAX, SMAX, smin, fnone
    a, b = smin, SMAX
    while b - a > TOL:
        m = (a + b) / 2; v = f(m)
        if not np.isnan(v) and v > 0: a = m
        else: b = m
    return a, b, smin, fnone


if __name__ == "__main__":
    for sg in elections_from_argv(["20220309", "20240410", "20250603", "20260603"]):
        log = timer(); P = Prep(sg); W = P.W["guFE"]; rows = []; prof = []
        moves = [(f"lambda={l:g}", True, l) for l in LAMS] + [("unrestricted", False, 2.0)]
        for mv, calib, eta in moves:
            LP = P.lps(calib=calib)
            for dl in DELTAS:
                a, b, smin, fnone = sstar(P, LP, W, eta, dl)
                rows.append(dict(sg=sg, movement=mv, lam=eta if calib else np.nan, delta=dl, s_lo=a, s_hi=b, s_min=smin, lower_unrestricted=fnone))
                if mv == "lambda=1" and np.isfinite(b):
                    for u in P.units: LP[u].dF = ("slack", b)
                    sols = {u: LP[u].solve(slope_c(LP[u], W[u])[0], eta, dl).x for u in P.units}
                    slope = sum(slope_c(LP[u], W[u])[1] + slope_c(LP[u], W[u])[0] @ sols[u] for u in P.units)
                    t, sm = terciles(pd.DataFrame(describe(P, LP, sols, W, "edge")))
                    prof += [dict(sg=sg, delta=dl, s_edge=b, slope=slope, **r, **sm) for r in t]
            log(sg, mv)
            pd.DataFrame(rows).to_csv(f"{RES}/region_{sg}.csv", index=False); pd.DataFrame(prof).to_csv(f"{RES}/edge_profile_{sg}.csv", index=False)
