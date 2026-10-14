"""Age composition and the tercile contrast (Section 4.5; Online Appendix Table C22).

Two further summaries of the within-district relation, for all of Seoul and without 강남, 서초 and 송파:
  * the within-gu slope on log price holding neighborhood age composition fixed (Frisch-Waugh-Lovell weights from a
    regression of log price on gu dummies, the mean age of residents aged 18+ and the share aged 60+);
  * the top-minus-bottom tercile contrast within gu (contrast.contrast_weights, kind "tercile").
Each is reported for election-day voters (point-identified valid-vote share) and for all residents under the main
assumptions (mobility-calibrated movement, delta = 0.1, s = 0.02; roll-based share z). Age composition is measured once, in
April 2026 (Ministry of the Interior and Safety), so for earlier elections it is a proxy for contemporaneous composition.
Output: results/age_tercile.csv"""
import numpy as np
import pandas as pd
from vwn.run import Prep, timer, elections_from_argv
from vwn.data import slope_weights, norm
from vwn.bounds import total
from vwn.lp import KMS, INV
from vwn.paths import RES, DATA
from contrast import contrast_weights
from spatial_scope import GANGNAM3


def fwl(x, gu, Z):
    """Slope weights for x with gu fixed effects and covariates Z, on dongs where x and Z are observed."""
    m = ~np.isnan(x) & ~np.isnan(Z).any(1); w = np.zeros(len(x))
    G = np.column_stack([(gu[m] == g).astype(float) for g in np.unique(gu[m])])
    X = np.column_stack([G, Z[m]]); xr = x[m] - X @ np.linalg.lstsq(X, x[m], rcond=None)[0]
    w[m] = xr / (xr ** 2).sum(); return w


if __name__ == "__main__":
    ag = pd.read_csv(f"{DATA}/seoul_hdong_age_202604.csv")
    age = {r.gu + "|" + norm(r.emd): (r.mean_age18, r.share60) for r in ag.itertuples()}
    rows = []
    for sg in elections_from_argv(["20220309", "20240410", "20250603", "20260603"]):
        log = timer(); P = Prep(sg); gu = P.labs["guFE"]
        Z = np.array([age.get(g + "|" + norm(em), (np.nan, np.nan)) for g, (_, em) in zip(gu, P.idx)], float)
        A = np.vstack([P.G[u][0]["A"] for u in P.units]); yA = A[:, KMS] / (A.sum(1) - A[:, INV])
        LP = P.lps(calib=True, dF=("slack", 0.02))
        for sample, exclude in [("all", ()), ("excl_gangnam3", GANGNAM3)]:
            x = P.x.copy()
            if exclude: x[np.isin(gu, exclude)] = np.nan
            W = {"slope": slope_weights(sg, x, P.labs, ["guFE"])["guFE"], "slope_age": fwl(x, gu, Z),
                 "tercile": contrast_weights(x, gu, "tercile")}
            for est, w in W.items():
                lo, hi = total(P.units, LP, P.wsplit(w), 1.0, 0.1)
                rows.append(dict(sg=sg, sample=sample, estimand=est, election_day=float(w @ np.nan_to_num(yA)), lo=lo, hi=hi,
                                 n_dongs=int((w != 0).sum()), age_matched=int((~np.isnan(Z).any(1) & ~np.isnan(x)).sum())))
            log(sg, sample)
        pd.DataFrame(rows).to_csv(f"{RES}/age_tercile.csv", index=False)
