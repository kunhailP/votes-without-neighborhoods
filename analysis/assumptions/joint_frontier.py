"""Joint sensitivity to the two composition restrictions (supplementary results, docs/supplementary_results.md).
s*(delta): largest slack s on residents' in-zone early composition at which the lower bound of the slope is
positive, for each band delta on out-of-zone composition. Movement: calibration scenario (lambda = 1) or
unrestricted (eta = 2). s* is stored as [lo, hi] of the final bisection interval on [0, 0.30].
Output: results/joint_frontier_<sg>.csv"""
import numpy as np
import pandas as pd
from vwn.run import Prep, timer, elections_from_argv
from vwn.bounds import total
from vwn.paths import RES

DELTAS = [0.1, 0.15, 0.2, 0.3, 0.5, 0.75, 1.0]; SMAX = 0.3; TOL = 0.3 / 128

if __name__ == "__main__":
    for sg in elections_from_argv(["20170509", "20220309", "20240410", "20250603", "20260603"]):
        log = timer(); P = Prep(sg); rows = []
        moves = ([("calib", True, 1.0)] if sg != "20170509" else []) + [("free", False, 2.0)]
        for mv, calib, eta in moves:
            LP = P.lps(calib=calib)
            for sp in P.W:
                def f(s, dl):
                    for u in P.units: LP[u].dF = None if s is None else ("slack", s)
                    return total(P.units, LP, P.W[sp], eta, dl)[0]
                for dl in DELTAS:
                    f0 = f(0.0, dl); fmax = f(SMAX, dl); fnone = f(None, dl); smin = 0.0
                    if np.isnan(f0):   # A^F infeasible at s = 0: start from the smallest feasible slack
                        lo_, hi_ = 0.0, SMAX
                        while hi_ - lo_ > TOL / 4:
                            m = (lo_ + hi_) / 2
                            if np.isnan(f(m, dl)): lo_ = m
                            else: hi_ = m
                        smin = hi_; f0 = f(smin, dl)
                    if not np.isnan(fnone) and fnone > 0: a = b = np.inf     # signed with residents' composition unrestricted
                    elif np.isnan(f0) or f0 <= 0: a = b = smin
                    elif fmax > 0: a = b = np.inf
                    else:
                        a, b = smin, SMAX
                        while b - a > TOL:
                            m = (a + b) / 2; v = f(m, dl)
                            if not np.isnan(v) and v > 0: a = m
                            else: b = m
                    rows.append(dict(sg=sg, movement=mv, spec=sp, delta=dl, s_min=smin, s_lo=a, s_hi=b, lower_s0=f0, lower_smax=fmax, lower_unrestricted=fnone))
                log(sg, mv, sp)
                pd.DataFrame(rows).to_csv(f"{RES}/joint_frontier_{sg}.csv", index=False)
