"""Robustness under the residents' early-composition restriction (Section 4.5; Online Appendix Table C10):
slack s in {0.02, 0.05}, delta = 0.1, calibrated (lambda = 1) or unrestricted (eta = 2) movement; within-gu
(and within-constituency in 2024). Variants: price measure, trimming, denominator weights, sparse prices.
Output: results/robust_restricted_<sg>.csv"""
import numpy as np
import pandas as pd
from vwn.run import Prep, timer, elections_from_argv
from vwn.data import weights, norm
from vwn.bounds import total
from vwn.paths import DATA, RES


def prices(sg, idx):
    """(median per m2, mean per m2, transactions) per dong, in idx order."""
    if sg == "20250603":
        h = pd.read_csv(f"{DATA}/seoul_hdong_aptprice_202406_202505.csv"); key = h.gu + "|" + h.hdong.map(norm)
        m = dict(zip(key, zip(h.med_per_m2, h.mean_per_m2, h.n_trades))); look = lambda u, e: m.get(u + "|" + norm(e))
    elif sg == "20240410":
        h = pd.read_csv(f"{DATA}/seoul_hdong_aptprice_{sg}.csv").dropna(subset=["price_med"]); e = pd.read_csv(f"{DATA}/seoul_{sg}_electorate_bysgg.csv")
        rg = dict(zip(e.gu + "|" + e.emd, e.realgu)); m = {norm(r.emd) + ("|" + r.gu if r.emd == "신사동" else ""): (r.price_med, r.price_mean, r.n) for r in h.itertuples()}
        look = lambda u, em: m.get(norm(em) + ("|" + rg[u + "|" + em] if em == "신사동" else ""))
    else:
        h = pd.read_csv(f"{DATA}/seoul_hdong_aptprice_{sg}.csv").dropna(subset=["price_med"]); m = dict(zip(h.gu + "|" + h.emd.map(norm), zip(h.price_med, h.price_mean, h.n)))
        look = lambda u, e: m.get(u + "|" + norm(e))
    out = np.array([look(u, e) if look(u, e) is not None else (np.nan, np.nan, np.nan) for u, e in idx], dtype=float)
    return out[:, 0], out[:, 1], out[:, 2]


def hweights(x, H, gu, fe):
    d = pd.DataFrame(dict(x=x, H=H, g=gu))
    xt = x - (d.g.map(d.groupby("g").apply(lambda q: np.average(q.x, weights=q.H), include_groups=False)).values if fe else np.average(x, weights=H))
    return H * xt / (H * xt ** 2).sum()


if __name__ == "__main__":
    for sg in elections_from_argv(["20220309", "20240410", "20250603", "20260603"]):
        log = timer(); P = Prep(sg); med, mean, ntr = prices(sg, P.idx); rows = []
        H = np.concatenate([P.G[u][0]["Avotes"] + P.G[u][1] - P.G[u][0]["D"] for u in P.units])
        fe_sets = [("guFE", P.labs["guFE"])] + ([("sggFE", P.labs["sggFE"])] if "sggFE" in P.labs else [])
        q90, q95 = np.nanquantile(med, 0.9), np.nanquantile(med, 0.95)
        variants = {"baseline": (np.log(med), None), "excl_top5": (np.where(med <= q95, np.log(med), np.nan), None),
                    "excl_top10": (np.where(med <= q90, np.log(med), np.nan), None), "H_weighted": (np.log(med), "H"),
                    "log_mean": (np.log(mean), None), "linear_median": (med, None), "linear_mean": (mean, None),
                    "min_trades_30": (np.where(ntr >= 30, np.log(med), np.nan), None)}
        for mv, calib, eta in [("calib", True, 1.0), ("free", False, 2.0)]:
            for s in [None, 0.02, 0.05]:
                LP = P.lps(calib=calib, dF=None if s is None else ("slack", s))
                for fe_name, fe in fe_sets:
                    for vn, (xv, wt) in variants.items():
                        if fe_name == "sggFE" and vn != "baseline": continue
                        has = ~np.isnan(xv); wv = np.zeros(len(xv))
                        wv[has] = hweights(xv[has], H[has], fe[has], True) if wt == "H" else weights(xv[has], fe[has], True)
                        lo, hi = total(P.units, LP, P.wsplit(wv), eta, 0.1)
                        rows.append(dict(sg=sg, movement=mv, slack=s, fe=fe_name, variant=vn, dongs=int(has.sum()), lo=lo, hi=hi))
                log(sg, mv, s)
                pd.DataFrame(rows).to_csv(f"{RES}/robust_restricted_{sg}.csv", index=False)
