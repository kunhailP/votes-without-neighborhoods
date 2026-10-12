"""Single dongs and neighbors, 2026 (Section 4.2; Figure 3; supplementary results, docs/supplementary_results.md).

(1) Dong-level identified ranges of residence-based valid-vote shares [min y_i, max y_i] (Dinkelbach), for the
    map: accounting only (eta = 1, delta = 1), minimum-movement benchmark (eta = 0, delta = 1), and
    calibrated movement with a 10-point band.
(2) Differences z_i - z_k for adjacent dongs in the same gu: share of pairs whose sign is identified.
Outputs: results/dong_ranges_2026.csv, results/adj_pairs_2026.csv"""
import numpy as np
import pandas as pd
from vwn.run import Prep, timer
from vwn.data import norm
from vwn.lp import KMS, INV
from vwn.ytight import CLP, get_dong
from vwn.paths import DATA, RES

sg = "20260603"; log = timer(); P = Prep(sg)
SET = [("accounting", False, 1.0, 1.0, None), ("eta0_d1", False, 0.0, 1.0, None), ("eta0_d0.1", False, 0.0, 0.1, None),
       ("calib_d0.1", True, 1.0, 0.1, None), ("calib_d0.1_s0.02", True, 1.0, 0.1, ("slack", 0.02))]
rec = []
for u in P.units:
    g, E = P.G[u]; v = g["A"] + g["K"]; conv = v[:, KMS] / (v.sum(1) - v[:, INV])
    out = {k: [] for k in ["lo", "hi"]}
    row = dict(); bnds = {}
    for nm, calib, eta, dl, dF in SET[:4]:
        lp = P.lps(calib=calib, dF=dF)[u]
        bnds[nm] = get_dong(sg, u, CLP(lp), KMS, eta, dl)
    for k, e in enumerate(g["emds"]):
        r = dict(gu=u, emd=e, key=norm(e), conv=conv[k])
        for nm in bnds: r[f"lo_{nm}"], r[f"hi_{nm}"] = bnds[nm][0][k], bnds[nm][1][k]
        rec.append(r)
    log(u, "dong ranges")
pd.DataFrame(rec).to_csv(f"{RES}/dong_ranges_2026.csv", index=False)

adj = pd.read_csv(f"{DATA}/adjacency_{sg}.csv"); rows = []
for nm, calib, eta, dl, dF in SET:
    LP = P.lps(calib=calib, dF=dF)
    for u in P.units:
        g, E = P.G[u]; emds = list(g["emds"]); H = g["Avotes"] + E - g["D"]; lp = LP[u]
        for p in adj[adj.gu == u].itertuples():
            if p.emd_a not in emds or p.emd_b not in emds: continue
            i, k = emds.index(p.emd_a), emds.index(p.emd_b); c = np.zeros(lp.nv)
            for sgn, a in [(1, i), (-1, k)]:
                for j in range(lp.n): c[lp.iF(a, j, KMS)] += sgn / H[a]
                c[lp.iB(a, KMS)] += sgn / H[a]; c[lp.iG(a, KMS)] += sgn / H[a]
            const = g["A"][i, KMS] / H[i] - g["A"][k, KMS] / H[k]
            r1 = lp.solve(c, eta, dl); r2 = lp.solve(-c, eta, dl)
            if r1.status or r2.status: continue
            conv = (g["A"][i, KMS] + g["K"][i, KMS]) / (g["Avotes"][i] + g["K"][i].sum()) - (g["A"][k, KMS] + g["K"][k, KMS]) / (g["Avotes"][k] + g["K"][k].sum())
            rows.append(dict(setting=nm, gu=u, a=p.emd_a, b=p.emd_b, lo=const + r1.fun, hi=const - r2.fun, conv=conv))
    log(nm, "pairs")
d = pd.DataFrame(rows); d.to_csv(f"{RES}/adj_pairs_2026.csv", index=False)
d["signed"] = (d.lo > 0) | (d.hi < 0); d["width"] = d.hi - d.lo
print(d.groupby("setting").agg(pairs=("signed", "size"), signed=("signed", "mean"), med_width=("width", "median")).round(3))
