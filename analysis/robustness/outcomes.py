"""Alternative outcomes (Online Appendix Table C26): conservative blocs and the Democratic share.
Output: results/outcomes.csv"""
import numpy as np
import pandas as pd
from vwn.run import Prep, timer
from vwn.lp import CANDS
from vwn.paths import RES

OUT = {"20121219": {"Democratic": ["LJM"]}, "20170509": {"Hong+Yoo": ["KMS", "KYG"], "Hong+Yoo+Ahn": ["KMS", "KYG", "LJS"], "Democratic": ["LJM"]},
       "20220309": {"Democratic": ["LJM"]}, "20240410": {"PPP+Reform": ["KMS", "LJS"], "Democratic": ["LJM"]},
       "20250603": {"Kim+Lee": ["KMS", "LJS"], "Democratic": ["LJM"]}, "20260603": {"Democratic": ["LJM"]}}


def bnd(lp, w, cis, eta, dl):
    g = lp.g; H = g["Avotes"] + lp.E - g["D"]; c = np.zeros(lp.nv); k = 0.0
    for ci in cis:
        k += (w * g["A"][:, ci] / H).sum()
        for i in range(lp.n):
            for j in range(lp.n): c[lp.iF(i, j, ci)] += w[i] / H[i]
            c[lp.iB(i, ci)] += w[i] / H[i]; c[lp.iG(i, ci)] += w[i] / H[i]
    r1 = lp.solve(c, eta, dl); r2 = lp.solve(-c, eta, dl)
    return (k + r1.fun, k - r2.fun) if r1.status == 0 and r2.status == 0 else (np.nan, np.nan)


rows = []; log = timer()
for sg, outs in OUT.items():
    P = Prep(sg); LP = P.lps()
    for sp in ["pooled", "guFE"]:
        wv = P.Wfull[sp]
        for name, cs in outs.items():
            cis = [CANDS.index(c) for c in cs]; r = dict(sg=sg, spec=sp, outcome=name)
            v = np.concatenate([(P.G[u][0]["A"] + P.G[u][0]["K"])[:, cis].sum(1) / (P.G[u][0]["A"] + P.G[u][0]["K"]).sum(1) for u in P.units])
            r["conventional"] = float((wv * v).sum())
            for eta, dl in [(0.0, 1.0), (0.0, 0.1), (1.0, 1.0)]:
                lo = hi = 0.0
                for u in P.units:
                    b = bnd(LP[u], P.W[sp][u], cis, eta, dl); lo += b[0]; hi += b[1]
                r[f"e{eta:g}_d{dl:g}_lo"] = lo; r[f"e{eta:g}_d{dl:g}_hi"] = hi
            rows.append(r)
    log(sg); pd.DataFrame(rows).to_csv(f"{RES}/outcomes.csv", index=False)
