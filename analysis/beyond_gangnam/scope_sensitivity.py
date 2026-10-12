"""How far the residents' early-composition assumption can be relaxed, with and without 강남, 서초 and 송파 (Section 4.3; Table 3, panel B; Online Appendix Table C19).

For the within-gu slope and the median-split contrast, s* is the largest slack on residents' in-zone early composition at
which the lower end of the range stays positive, holding movement (mobility-calibrated, lambda = 1, or unrestricted) and the
out-of-zone tolerance delta fixed; same bisection as region.py (assumptions/), with the weights of spatial_scope.py.
Output: results/scope_sstar_<sg>.csv"""
import numpy as np
import pandas as pd
from vwn.run import Prep, timer, elections_from_argv
from vwn.paths import RES
from region import sstar
from spatial_scope import sample_weights, GANGNAM3

if __name__ == "__main__":
    rows = []
    for sg in elections_from_argv(["20220309", "20240410", "20250603", "20260603"]):
        log = timer(); P = Prep(sg)
        for sample, exclude in [("all", ()), ("excl_gangnam3", GANGNAM3)]:
            Wu = {sp: P.wsplit(w) for sp, w in sample_weights(P, exclude).items()}
            for mv, calib, eta in [("lambda=1", True, 1.0), ("unrestricted", False, 2.0)]:
                LP = P.lps(calib=calib)
                for dl in [0.1, 0.2]:
                    for sp in ["slope", "contrast"]:
                        a, b, smin, fnone = sstar(P, LP, Wu[sp], eta, dl)
                        rows.append(dict(sg=sg, sample=sample, spec=sp, movement=mv, delta=dl, s_lo=a, s_hi=b, s_min=smin, lower_unrestricted=fnone))
                log(sg, sample, mv)
            pd.DataFrame([r for r in rows if r["sg"] == sg]).to_csv(f"{RES}/scope_sstar_{sg}.csv", index=False)
