"""Stability of the identified sets to resampling prices and dongs (Section 4.5; Online Appendix Table C24).

Conditional design: the returns, rolls and movement caps, which define Lambda, are held fixed. Each replication
(a) resamples transactions within each dong and recomputes dong log median prices ("txn"), or (b) also
resamples dongs with replacement within each counting jurisdiction, which changes the regression weights
("full"); the linear programs are then re-solved. The output describes how much the bounds move with the
price measure and with the composition of the dong sample. It is not a confidence interval with
guaranteed coverage for a superpopulation parameter: the bounds are optimal values of linear programs,
non-smooth functions of the weights, for which the nominal coverage of percentile or Imbens-Manski
intervals is not established here.
Output: results/resampling_<sg>_<mode>.csv; usage: resampling.py <sg> <B> <full|txn>"""
import sys
import numpy as np
import pandas as pd
from vwn.run import Prep, timer
from vwn.data import norm, weights
from vwn.bounds import total
from vwn.paths import DATA, RES

CELLS = {"20260603": [("guFE", "calib", None), ("guFE", "calib", 0.02), ("guFE", "calib", 0.05), ("guFE", "eta2", 0.02), ("pooled", "calib", 0.02), ("pooled", "calib", None)],
         "20240410": [("guFE", "calib", None), ("guFE", "calib", 0.02), ("sggFE", "calib", 0.02), ("pooled", "calib", 0.02), ("pooled", "calib", None)],
         "20220309": [("guFE", "calib", 0.02), ("pooled", "calib", 0.02), ("pooled", "calib", None)]}

if __name__ == "__main__":
    sg, B, MODE = sys.argv[1], int(sys.argv[2]), sys.argv[3]; log = timer(); rng = np.random.default_rng(2026)
    P = Prep(sg); x = P.x; has = P.has
    t = pd.read_csv(f"{DATA}/trades/trades_hdong_{sg}.csv")
    if sg == "20240410":
        e = pd.read_csv(f"{DATA}/seoul_{sg}_electorate_bysgg.csv"); rg = dict(zip(e.gu + "|" + e.emd, e.realgu))
        t["key"] = [norm(k) + ("|" + g if norm(k) == "신사동" else "") for g, k in zip(t.gu, t.k)]
        keys = [norm(em) + ("|" + rg[u + "|" + em] if em == "신사동" else "") for u, em in P.idx]
    else:
        t["key"] = t.gu + "|" + t.k.map(norm); keys = [u + "|" + norm(em) for u, em in P.idx]
    Pr = {k: v.p.values for k, v in t.groupby("key")}
    tr = [Pr.get(k) if h else None for k, h in zip(keys, has)]
    chk = np.array([np.log(np.median(a)) if a is not None else np.nan for a in tr])
    print("median check", np.nanmax(np.abs(chk - x)), flush=True)
    LPs = {}
    for spec, mv, s in CELLS[sg]:
        LPs[(mv, s)] = P.lps(calib=(mv == "calib"), dF=None if s is None else ("slack", s))
    strata = P.labs["sggFE"] if sg == "20240410" else P.labs["guFE"]
    rows = []
    for b in range(B + 1):
        if b == 0: xs = x.copy(); m = has.astype(float)
        else:
            xs = np.full(len(x), np.nan)
            for i, a in enumerate(tr):
                if a is not None: xs[i] = np.log(np.median(rng.choice(a, len(a))))
            m = np.zeros(len(x))
            if MODE == "full":
                for g_ in np.unique(strata):
                    pool = np.where((strata == g_) & has)[0]
                    if len(pool): m += np.bincount(rng.choice(pool, len(pool)), minlength=len(x))
            else: m = has.astype(float)
        for spec, mv, s in CELLS[sg]:
            ok = (m > 0) & ~np.isnan(xs); w = np.zeros(len(x))
            w[ok] = weights(xs[ok], (P.labs["guFE"] if spec == "pooled" else P.labs[spec])[ok], spec != "pooled", m[ok])
            lo, hi = total(P.units, LPs[(mv, s)], P.wsplit(w), 1.0 if mv == "calib" else 2.0, 0.1)
            rows.append(dict(sg=sg, mode=MODE, b=b, spec=spec, movement=mv, slack=s, lo=lo, hi=hi))
        if b % 10 == 0:
            pd.DataFrame(rows).to_csv(f"{RES}/resampling_{sg}_{MODE}.csv", index=False); log(sg, MODE, b)
    pd.DataFrame(rows).to_csv(f"{RES}/resampling_{sg}_{MODE}.csv", index=False)
