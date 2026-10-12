"""Alternative specifications (supplementary results, docs/supplementary_results.md):
(1) 2026 within-gu slope by price measure (log/linear x median/mean) and sample (all, excl. top 5%, top 10% by mean price);
(2) roll-denominator-weighted (WLS) slopes, all elections;
(3) excluding dongs with fewer than 10 or 30 transactions.
eta* (delta = 0.1) stored as [lo, hi]. Outputs: results/spec_prices_2026.csv, results/spec_hweighted.csv, results/spec_sparse.csv"""
import numpy as np
import pandas as pd
from vwn.run import Prep, timer
from vwn.data import norm, weights, ELECTIONS
from vwn.bounds import total, breakdown
from vwn.paths import DATA, RES
from robust_restricted import prices, hweights

log = timer()
CELLS = [("e0_d1", False, 0.0, 1.0), ("e0_d0.1", False, 0.0, 0.1), ("e0.05_d0.1", False, 0.05, 0.1), ("e0.1_d0.1", False, 0.1, 0.1),
         ("accounting", False, 1.0, 1.0), ("calib_d0.1", True, 1.0, 0.1), ("calib_d1", True, 1.0, 1.0)]


def run_w(P, Wu, calib_ok):
    out = {}
    for nm, calib, eta, dl in CELLS:
        if calib and not calib_ok: continue
        out[nm] = total(P.units, P.lps(calib=calib) if calib else LPu[P.sg], Wu, eta, dl)
    out["etastar"] = breakdown(lambda t: total(P.units, LPu[P.sg], Wu, t, 0.1)[0], 0.0, 1.0, 1 / 512)
    return out


LPu = {}
rows = []; sg = "20260603"; P = Prep(sg); LPu[sg] = P.lps()
med, mean, ntr = prices(sg, P.idx); lab = P.labs["guFE"]; base = ~np.isnan(med) & ~np.isnan(mean)
q90, q95 = np.nanquantile(mean[base], 0.90), np.nanquantile(mean[base], 0.95)
for scale, xv in [("log median", np.log(med)), ("log mean", np.log(mean)), ("linear median", med * 3.3058 / 1000), ("linear mean", mean * 3.3058 / 1000)]:
    for sample, m in [("all", base), ("excl. top 5%", base & (mean <= q95)), ("excl. top 10%", base & (mean <= q90))]:
        w = np.zeros(len(xv)); w[m] = weights(xv[m], lab[m], True)
        for k, v in run_w(P, P.wsplit(w), True).items(): rows.append(dict(scale=scale, sample=sample, n=int(m.sum()), cell=k, lo=v[0], hi=v[1]))
    log("prices", scale)
pd.DataFrame(rows).to_csv(f"{RES}/spec_prices_2026.csv", index=False)

hrows, srows = [], []
for sg in ELECTIONS:
    P = Prep(sg); LPu[sg] = P.lps(); calib_ok = sg >= "20220309"
    H = np.concatenate([P.G[u][0]["Avotes"] + P.G[u][1] - P.G[u][0]["D"] for u in P.units]); has = P.has
    for sp in ["guFE", "pooled"]:
        w = np.zeros(len(P.x)); w[has] = hweights(P.x[has], H[has], P.labs["guFE"][has], sp == "guFE"); Wu = P.wsplit(w)
        conv = sum((Wu[u] * (P.G[u][0]["A"][:, 1] + P.G[u][0]["K"][:, 1]) / (P.G[u][0]["Avotes"] + P.G[u][0]["K"].sum(1))).sum() for u in P.units)
        hrows.append(dict(sg=sg, spec=sp, cell="conventional", lo=conv, hi=conv))
        for k, v in run_w(P, Wu, calib_ok).items(): hrows.append(dict(sg=sg, spec=sp, cell=k, lo=v[0], hi=v[1]))
    if sg != "20121219":
        med, mean, ntr = prices(sg, P.idx)
        for thr in [0, 10, 30]:
            m = has & (np.nan_to_num(ntr, nan=0) >= thr)
            for sp in ["guFE", "pooled"]:
                w = np.zeros(len(P.x)); w[m] = weights(P.x[m], P.labs["guFE"][m], sp == "guFE")
                for k, v in run_w(P, P.wsplit(w), calib_ok).items(): srows.append(dict(sg=sg, min_trades=thr, spec=sp, dongs=int(m.sum()), cell=k, lo=v[0], hi=v[1]))
        q = np.nanpercentile(ntr[has], [10, 50]); srows.append(dict(sg=sg, min_trades=-1, spec="counts", dongs=int(has.sum()), cell="p10_median", lo=q[0], hi=q[1]))
    log("weights/sparse", sg)
    pd.DataFrame(hrows).to_csv(f"{RES}/spec_hweighted.csv", index=False); pd.DataFrame(srows).to_csv(f"{RES}/spec_sparse.csv", index=False)
