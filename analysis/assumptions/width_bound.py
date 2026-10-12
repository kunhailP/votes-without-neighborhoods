"""Proposition 2(iv): width of the z set <= sum_g range_{i in g}(w_i / H_i) * M_gc, with
M_gc = P_gc + Q_gc + sum_{j in g} min(K_jc, m_j) and m_j the movement cap. Compared with the LP width (delta = 1).
Requires results/main_grid_<sg>.csv. Output: results/width_bound.csv"""
import numpy as np
import pandas as pd
from vwn.run import Prep
from vwn.data import ELECTIONS
from vwn.lp import KMS
from vwn.paths import RES

rows = []
for sg in ELECTIONS:
    P = Prep(sg); r = pd.read_csv(f"{RES}/main_grid_{sg}.csv", dtype={"delta": str})
    for sp in ["pooled", "guFE"]:
        for eta in [0.0, 0.05, 0.1]:
            bound = 0.0
            for u in P.units:
                g, E = P.G[u]; w = P.W[sp][u]; H = g["Avotes"] + E - g["D"]
                rj = np.maximum(0, g["K"].sum(1) - (E - g["D"]))
                M = g["Bc"][KMS] + g["Gc"][KMS] + np.minimum(g["K"][:, KMS], rj + eta * g["K"].sum(1)).sum()
                bound += ((w / H).max() - (w / H).min()) * M
            q = r[(r.kind == "bound") & (r.spec == sp) & (r.eta == eta) & (r.delta == "1.0")]
            width = float(q.hi.iloc[0] - q.lo.iloc[0])
            rows.append(dict(sg=sg, spec=sp, eta=eta, width_lp=width, width_bound=bound, ratio=width / bound))
pd.DataFrame(rows).to_csv(f"{RES}/width_bound.csv", index=False)
