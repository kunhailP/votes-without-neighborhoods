"""Valid-vote shares y (Section 4.5; Online Appendix Table C15; supplementary results, docs/supplementary_results.md).

Cells: uniform movement (eta, delta) in {(1,1), (0,1), (0,0.1), (0.05,0.1)} for every election and
specification; composition-restricted cells (calibrated or unrestricted movement, delta = 0.1, s in {0.02, 0.05})
and calibrated delta = 0.1 without A^F. For each: sharp z set, the Proposition 4 outer bound and attainable values for y.
Also eta*_y at delta = 0.1 by bisection on the outer bound ([lo, hi]).
Output: results/valid_vote_<sg>.csv"""
import numpy as np
import pandas as pd
from vwn.run import Prep, timer, elections_from_argv
from vwn.ytight import CLP, run_cells, get_dong, tight_lp
from vwn.lp import KMS
from vwn.bounds import breakdown
from vwn.paths import RES


def ylower(sg, P, CL, wg, eta, delta):
    lo = 0.0
    for u in P.units:
        w = wg[u]
        if not np.any(w): continue
        db = get_dong(sg, u, CL[u], KMS, eta, delta)
        if db is None: return np.nan
        ylo, yhi = db; tl, _ = tight_lp(CL[u], w, KMS, eta, delta, ylo, yhi, +1)
        lo += max(tl, float(np.sum(np.where(w > 0, w * ylo, w * yhi))))
    return lo


if __name__ == "__main__":
    for sg in elections_from_argv():
        log = timer(); P = Prep(sg); rows = []
        CL = {u: CLP(lp) for u, lp in P.lps().items()}
        for r in run_cells(sg, P.units, CL, P.W, [(1.0, 1.0), (0.0, 1.0), (0.0, 0.1), (0.05, 0.1)], log=lambda *a: None):
            rows.append(dict(movement="uniform", slack=None, **r))
        log(sg, "uniform cells")
        if sg >= "20220309":
            for mv, calib, eta in [("calib", True, 1.0), ("free", False, 2.0)]:
                for s in ([None] if mv == "calib" else []) + [0.02, 0.05]:
                    CLs = {u: CLP(lp) for u, lp in P.lps(calib=calib, dF=None if s is None else ("slack", s)).items()}
                    for r in run_cells(sg, P.units, CLs, P.W, [(eta, 0.1)], log=lambda *a: None):
                        rows.append(dict(movement=mv, slack=s, **r))
                    log(sg, mv, s)
        if sg != "20121219":
            for sp in P.W:
                a, b = breakdown(lambda e: ylower(sg, P, CL, P.W[sp], round(e, 5), 0.1), 0.0, 1.0, 1 / 512)
                rows.append(dict(movement="uniform", spec=sp, delta=0.1, note="eta_star_y", y_tight_lo=a, y_tight_hi=b))
            log(sg, "eta*_y")
        pd.DataFrame(rows).to_csv(f"{RES}/valid_vote_{sg}.csv", index=False)
