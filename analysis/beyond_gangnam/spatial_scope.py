"""Beyond Gangnam: the within-district relation with and without 강남, 서초 and 송파 (Section 4.3; Table 3; Figure 2B-C;
Online Appendix Tables C17, C18).

For each election and each column A-E of Table 2, the within-gu slope (gu fixed effects) and the high-minus-low median-split
contrast are bounded over the same feasible set as in the main analysis. The excluded sample sets the price of every dong in
the three southeastern gu to missing, so the regression and contrast weights are recomputed on the remaining dongs (the
other gu keep their own median split); the accounting constraints of every jurisdiction are unchanged, and jurisdictions with
zero weight drop out of the objective. Roll-based shares z are exact LP values; valid-vote shares y are bracketed by the
Proposition 4 outer bound and attainable values, as elsewhere.
Output: results/spatial_scope_<sg>.csv"""
import numpy as np
import pandas as pd
from vwn.run import Prep, timer, elections_from_argv
from vwn.data import slope_weights
from vwn.ytight import CLP, run_cells
from vwn.lp import KMS, INV
from vwn.paths import RES
from contrast import contrast_weights

GANGNAM3 = ("강남구", "서초구", "송파구")
CELLS = [("A", "accounting", False, 1.0, 1.0, None), ("B", "eta0_d1", False, 0.0, 1.0, None), ("C", "eta0_d0.1", False, 0.0, 0.1, None),
         ("D", "calib_d0.1", True, 1.0, 0.1, None), ("E", "calib_d0.1_s0.02", True, 1.0, 0.1, 0.02)]


def sample_weights(P, exclude):
    gu = P.labs["guFE"]; x = P.x.copy()
    if exclude: x[np.isin(gu, exclude)] = np.nan
    return {"slope": slope_weights(P.sg, x, P.labs, ["guFE"])["guFE"], "contrast": contrast_weights(x, gu, "median")}


if __name__ == "__main__":
    for sg in elections_from_argv():
        log = timer(); P = Prep(sg); rows = []
        conv = np.concatenate([(P.G[u][0]["A"][:, KMS] + P.G[u][0]["K"][:, KMS]) / (P.G[u][0]["Avotes"] + P.G[u][0]["K"].sum(1)) for u in P.units])
        convv = np.concatenate([(P.G[u][0]["A"][:, KMS] + P.G[u][0]["K"][:, KMS]) /
                                (P.G[u][0]["Avotes"] + P.G[u][0]["K"].sum(1) - P.G[u][0]["A"][:, INV] - P.G[u][0]["K"][:, INV]) for u in P.units])
        for sample, exclude in [("all", ()), ("excl_gangnam3", GANGNAM3)]:
            W = sample_weights(P, exclude); Wu = {sp: P.wsplit(w) for sp, w in W.items()}
            units = [u for u in P.units if any(np.any(Wu[sp][u]) for sp in Wu)]
            n_dongs = int(np.sum(W["slope"] != 0)); n_gu = len(units)
            for sp, w in W.items():
                rows.append(dict(sg=sg, sample=sample, spec=sp, column="conv", cell="conventional", n_dongs=n_dongs, n_units=n_gu,
                                 z_lo=float(w @ conv), z_hi=float(w @ conv), y_tight_lo=float(w @ convv), y_tight_hi=float(w @ convv),
                                 y_ach_lo=float(w @ convv), y_ach_hi=float(w @ convv)))
            for col, name, calib, eta, dl, s in CELLS:
                if calib and sg < "20220309": continue
                CL = {u: CLP(lp) for u, lp in P.lps(calib=calib, dF=None if s is None else ("slack", s)).items()}
                for r in run_cells(sg, units, CL, Wu, [(eta, dl)], log=lambda *a: None):
                    rows.append(dict(sg=sg, sample=sample, spec=r["spec"], column=col, cell=name, n_dongs=n_dongs, n_units=n_gu,
                                     **{k: r.get(k) for k in ["z_lo", "z_hi", "y_tight_lo", "y_tight_hi", "y_ach_lo", "y_ach_hi"]}))
                log(sg, sample, col)
                pd.DataFrame(rows).to_csv(f"{RES}/spatial_scope_{sg}.csv", index=False)
