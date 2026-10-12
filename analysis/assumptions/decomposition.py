"""Lemma 2: the city-wide weights equal pi_w times the within-gu weights plus v, constant within gu, so for every
allocation theta(w^P) = pi_w theta(w^FE) + theta(v). theta(v) is the slope on the gu-level price gradient; it
depends on the allocation, and its identified set is reported here. Output: results/decomposition.csv"""
import numpy as np
import pandas as pd
from vwn.run import Prep
from vwn.data import ELECTIONS
from vwn.bounds import total
from vwn.paths import RES

rows = []
for sg in ELECTIONS:
    P = Prep(sg); has = P.has; lab = P.labs["guFE"]; x = P.x
    xx = x[has]; gg = lab[has]; xbar = xx.mean(); xg = pd.Series(xx).groupby(gg).transform("mean").values
    ST = ((xx - xbar) ** 2).sum(); SW = ((xx - xg) ** 2).sum(); pi = SW / ST
    wP = np.zeros(len(x)); wF = np.zeros(len(x)); v = np.zeros(len(x))
    wP[has] = (xx - xbar) / ST; wF[has] = (xx - xg) / SW; v[has] = (xg - xbar) / ST
    cells = [("accounting", False, 1.0, 1.0), ("eta0_d1", False, 0.0, 1.0), ("eta0_d0.1", False, 0.0, 0.1), ("eta0.05_d0.1", False, 0.05, 0.1)]
    if sg >= "20220309": cells += [("calib_d0.1", True, 1.0, 0.1), ("calib_d1", True, 1.0, 1.0)]
    for name, calib, eta, dl in cells:
        LP = P.lps(calib=calib); out = {}
        for k, w in [("P", wP), ("F", wF), ("B", v)]: out[k] = total(P.units, LP, P.wsplit(w), eta, dl)
        rows.append(dict(sg=sg, cell=name, pi_w=pi, P_lo=out["P"][0], P_hi=out["P"][1], F_lo=out["F"][0], F_hi=out["F"][1],
                         B_lo=out["B"][0], B_hi=out["B"][1]))
pd.DataFrame(rows).to_csv(f"{RES}/decomposition.csv", index=False)
