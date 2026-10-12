"""Solver and scaling check (Online Appendix A.4; supplementary results, docs/supplementary_results.md): within-gu z lower bounds computed with HiGHS dual simplex
and interior point on the rescaled objective, with a further x1000 rescaling, and with the unscaled default.
Output: results/solver_check.csv"""
import numpy as np
import pandas as pd
from scipy.optimize import linprog
from vwn.run import Prep
from vwn.bounds import slope_c
from vwn.paths import RES

rows = []
for sg in ["20260603", "20240410"]:
    P = Prep(sg); W = P.W["guFE"]
    for calib, eta, dl in [(False, 0.0, 1.0), (False, 0.05, 0.1), (True, 1.0, 0.1)]:
        LP = P.lps(calib=calib); tot = {"unscaled_default": 0.0, "dual_simplex": 0.0, "interior_point": 0.0, "dual_simplex_x1000": 0.0}
        for u in P.units:
            lp = LP[u]; cv, k0 = slope_c(lp, W[u]); Aeq, beq, Aub, bub = lp.cached_constraints(eta, dl); s = np.abs(cv).max()
            r = linprog(cv, A_ub=Aub, b_ub=bub, A_eq=Aeq, b_eq=beq, bounds=(0, None), method="highs"); tot["unscaled_default"] += k0 + r.fun
            for m, f in [("dual_simplex", 1), ("interior_point", 1), ("dual_simplex_x1000", 1e3)]:
                r = linprog(cv / s * f, A_ub=Aub, b_ub=bub, A_eq=Aeq, b_eq=beq, bounds=(0, None), method="highs-ipm" if m == "interior_point" else "highs-ds",
                            options=dict(dual_feasibility_tolerance=1e-10, primal_feasibility_tolerance=1e-9))
                tot[m] += k0 + r.fun * s / f
        rows.append(dict(sg=sg, movement="calib" if calib else "uniform", eta=eta, delta=dl, **tot))
pd.DataFrame(rows).to_csv(f"{RES}/solver_check.csv", index=False)
