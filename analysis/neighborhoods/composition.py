"""Residents' in-zone early composition (A^F_s): identified sets and breakdown points (Table 2, column E;
supplementary results, docs/supplementary_results.md). Uniform movement eta in {0, 0.1, 0.3} with eta* on [0, 2]; calibrated movement
lambda in {0.5, 1} with lambda* on [0, 4]. Breakdown points are stored as [lo, hi].
Output: results/composition_<sg>.csv; delta_F_min per unit in rows kind == "dFmin"."""
import numpy as np
import pandas as pd
from vwn.run import Prep, timer, elections_from_argv
from vwn.bounds import total, breakdown
from vwn.paths import RES

if __name__ == "__main__":
    for sg in elections_from_argv(["20170509", "20220309", "20240410", "20250603", "20260603"]):
        log = timer(); P = Prep(sg); rows = []; calib_ok = sg != "20170509"
        for calib in ([False, True] if calib_ok else [False]):
            LP = P.lps(calib=calib); eta0 = 1.0 if calib else 0.0
            for u in P.units:   # smallest fixed band on residents' early composition consistent with the data
                lp = LP[u]; lp.dF = 0.0
                if lp.feasible(eta0, 1.0): v = 0.0
                else:
                    lo, hi = 0.0, 1.0
                    while hi - lo > 1e-3:
                        m = (lo + hi) / 2; lp.dF = m
                        if lp.feasible(eta0, 1.0): hi = m
                        else: lo = m
                    v = hi
                rows.append(dict(sg=sg, kind="dFmin", calib=calib, unit=u, value=v))
            etas = [1.0, 0.5] if calib else [0.0, 0.1, 0.3]
            for dF in [("slack", 0.02), ("slack", 0.05), ("slack", 0.1), 0.2]:
                for u in P.units: LP[u].dF = dF
                for delta in [0.1, 1.0]:
                    for sp in P.W:
                        for e in etas:
                            lo, hi = total(P.units, LP, P.W[sp], e, delta)
                            rows.append(dict(sg=sg, kind="bounds", calib=calib, spec=sp, delta=delta, dF=str(dF), eta=e, lo=lo, hi=hi))
                        a, b = breakdown(lambda t: total(P.units, LP, P.W[sp], t, delta)[0], 0.0, 4.0 if calib else 2.0, 0.008 if calib else 0.004)
                        rows.append(dict(sg=sg, kind="lamstar" if calib else "etastar", calib=calib, spec=sp, delta=delta, dF=str(dF), lo=a, hi=b))
                    log(sg, "calib" if calib else "uniform", dF, delta)
                    pd.DataFrame(rows).to_csv(f"{RES}/composition_{sg}.csv", index=False)
