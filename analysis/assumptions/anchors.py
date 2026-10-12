"""Out-of-zone anchors (supplementary results, docs/supplementary_results.md).

(1) delta_min under the station anchor at eta = 0 and eta = 10 (movement unrestricted), and under the
    election-day anchor a^day = clip(A_ic/A_i + gamma_gc), gamma_gc = out-of-zone - election-day composition.
(2) Identified sets under the election-day anchor (delta in {0.05, 0.1, 0.2}; eta = 0, 0.1, calibrated).
(3) Gu-specific station band delta_g = delta_min,g(eta = 0) + slack, slack in {0.02, 0.05, 0.1}; eta* stored as [lo, hi].
Outputs: results/anchor_day_<sg>.csv, results/anchor_slack_<sg>.csv"""
import numpy as np
import pandas as pd
from vwn.run import Prep, timer, elections_from_argv
from vwn.data import make_lp
from vwn.bounds import total, bounds_with_w, breakdown
from vwn.lp import KMS
from vwn.paths import RES

if __name__ == "__main__":
    log = timer()
    for sg in elections_from_argv(["20170509", "20220309", "20240410", "20250603", "20260603"]):
        rows = []; srows = []
        P = Prep(sg); calib = sg != "20170509"
        LPs = P.lps(); LPd = {}; LPdc = {}; dm = []
        for u in P.units:
            g, E = P.G[u]; A = g["A"]; day = A / A.sum(1, keepdims=True)
            ad = np.clip(day + g["Bc"] / g["Bc"].sum() - A.sum(0) / A.sum(), 0, 1); g2 = dict(g, a_tilde=ad)
            LPd[u] = make_lp(g2, E)
            if calib: LPdc[u] = make_lp(g2, E, ev=P.ev[u])
            dm.append(dict(unit=u, st0=LPs[u].delta_min(0.0), st10=LPs[u].delta_min(10.0), dy0=LPd[u].delta_min(0.0), dy10=LPd[u].delta_min(10.0)))
        dm = pd.DataFrame(dm)
        rows.append(dict(sg=sg, kind="dmin", st_eta0_med=dm.st0.median(), st_eta0_max=dm.st0.max(), st_eta0_n_gt05=int((dm.st0 > 0.05).sum()),
                         st_eta10_med=dm.st10.median(), st_eta10_min=dm.st10.min(), day_eta0_med=dm.dy0.median(), day_eta10_med=dm.dy10.median(), n_units=len(dm)))
        for dl in [0.05, 0.1, 0.2]:
            for sp in P.W:
                for label, lps, eta in [("eta0", LPd, 0.0), ("eta0.1", LPd, 0.1)] + ([("calibrated", LPdc, 1.0)] if calib else []):
                    lo, hi = total(P.units, lps, P.W[sp], eta, dl)
                    rows.append(dict(sg=sg, kind="bounds", movement=label, delta=dl, spec=sp, lo=lo, hi=hi))
        log(sg, "day anchor")
        dmin = dict(zip(dm.unit, dm.st0)); LPc = P.lps(calib=True) if calib else None
        for sp in ["guFE", "pooled"]:
            for s in [0.02, 0.05, 0.1]:
                def tot(L, eta):
                    lo = hi = 0.0
                    for u in P.units:
                        b = bounds_with_w(L[u], P.W[sp][u], KMS, eta, min(1.0, dmin[u] + s))
                        if b is None: return np.nan, np.nan
                        lo += b[0]; hi += b[1]
                    return lo, hi
                for nm, L, e in [("eta0", LPs, 0.0), ("eta0.1", LPs, 0.1)] + ([("calib", LPc, 1.0)] if calib else []):
                    lo, hi = tot(L, e); srows.append(dict(sg=sg, spec=sp, slack=s, cell=nm, lo=lo, hi=hi))
                a, b = breakdown(lambda t: tot(LPs, t)[0], 0.0, 1.0, 0.004); srows.append(dict(sg=sg, spec=sp, slack=s, cell="etastar", lo=a, hi=b))
        log(sg, "gu-specific band")
        pd.DataFrame(rows).to_csv(f"{RES}/anchor_day_{sg}.csv", index=False); pd.DataFrame(srows).to_csv(f"{RES}/anchor_slack_{sg}.csv", index=False)
