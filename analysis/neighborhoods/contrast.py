"""Within-gu contrast between high- and low-price dongs (Section 4.2; Table 2, panel B; Online Appendix Table C3).

Definition:
  groups   within each gu (each counting jurisdiction's real gu; 2024 uses the gu), dongs with a price above the gu median
           price are "high", the rest "low" (a dong exactly at the median goes to "low"); dongs without a price are excluded
  weights  omega_g proportional to the number of dongs with a price in gu g; equal weight for dongs within a group
  estimand Delta = sum_g omega_g (mean_{high,g} share - mean_{low,g} share), in percentage points
A secondary version contrasts the top and bottom terciles within gu. Delta is linear in the shares, so bounds for the
roll-based share z are LP values; valid-vote shares y use the Proposition 4 outer bound and attainable values.
Output: results/contrast_<sg>.csv (one election) or results/contrast.csv (several)"""
import numpy as np
import pandas as pd
from vwn.run import Prep, timer, elections_from_argv
from vwn.bounds import total
from vwn.ytight import CLP, run_cells
from vwn.lp import KMS, INV
from vwn.paths import RES


def contrast_weights(x, gu, kind="median"):
    w = np.zeros(len(x)); has = ~np.isnan(x); N = has.sum()
    for g in np.unique(gu[has]):
        m = has & (gu == g); xs = x[m]; idx = np.where(m)[0]
        if kind == "median":
            hi = idx[xs > np.median(xs)]; lo = idx[xs <= np.median(xs)]
        else:
            q1, q2 = np.quantile(xs, [1 / 3, 2 / 3]); hi = idx[xs > q2]; lo = idx[xs <= q1]
        if len(hi) == 0 or len(lo) == 0: continue
        om = m.sum() / N
        w[hi] += om / len(hi); w[lo] -= om / len(lo)
    return w


CELLS = [("accounting", False, 1.0, 1.0, None), ("eta0_d1", False, 0.0, 1.0, None), ("eta0_d0.1", False, 0.0, 0.1, None),
         ("calib_d1", True, 1.0, 1.0, None), ("calib_d0.1", True, 1.0, 0.1, None), ("calib_d0.1_s0.02", True, 1.0, 0.1, 0.02),
         ("calib_d0.1_s0.05", True, 1.0, 0.1, 0.05)]

if __name__ == "__main__":
    rows = []
    for sg in elections_from_argv():
        log = timer(); P = Prep(sg); gu = P.labs["guFE"]
        for kind in ["median", "tercile"]:
            w = contrast_weights(P.x, gu, kind); Wu = P.wsplit(w)
            conv = np.concatenate([(P.G[u][0]["A"][:, KMS] + P.G[u][0]["K"][:, KMS]) / (P.G[u][0]["Avotes"] + P.G[u][0]["K"].sum(1)) for u in P.units])
            convv = np.concatenate([(P.G[u][0]["A"][:, KMS] + P.G[u][0]["K"][:, KMS]) / (P.G[u][0]["Avotes"] + P.G[u][0]["K"].sum(1) - P.G[u][0]["A"][:, INV] - P.G[u][0]["K"][:, INV]) for u in P.units])
            rows.append(dict(sg=sg, kind=kind, cell="conventional", z_lo=float(w @ conv), z_hi=float(w @ conv), y_tight_lo=float(w @ convv), y_tight_hi=float(w @ convv)))
            for name, calib, eta, dl, s in CELLS:
                if calib and sg < "20220309": continue
                if eta == 0.0 and dl == 0.1 and sg == "20121219": pass
                CL = {u: CLP(lp) for u, lp in P.lps(calib=calib, dF=None if s is None else ("slack", s)).items()}
                rr = run_cells(f"{sg}", P.units, CL, {"contrast": Wu}, [(eta, dl)], log=lambda *a: None)[0]
                rows.append(dict(sg=sg, kind=kind, cell=name, **{k: rr.get(k) for k in ["z_lo", "z_hi", "y_tight_lo", "y_tight_hi", "y_ach_lo", "y_ach_hi"]}))
            log(sg, kind)
            pd.DataFrame(rows).to_csv(f"{RES}/contrast_{sg}.csv" if len(elections_from_argv()) == 1 else f"{RES}/contrast.csv", index=False)
