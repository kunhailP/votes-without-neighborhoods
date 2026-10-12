"""Integer allocations (Online Appendix Table A1): near-zero lower bounds re-solved as mixed-integer programs
with the same constraint matrices as the LPs. Output: results/integer_check.csv"""
import numpy as np
import pandas as pd
from vwn.run import Prep, timer
from vwn.ytight import CLP, get_dong
from vwn.intcheck import solve_int, objs
from vwn.lp import KMS
from vwn.paths import RES

CELLS = [("20121219", "guFE", False, None, 0.0, 1.0), ("20260603", "guFE", False, None, 0.1, 0.1), ("20260603", "guFE", True, None, 1.0, 0.1),
         ("20250603", "guFE", False, None, 0.0, 0.1), ("20240410", "sggFE", False, None, 0.0, 0.1), ("20220309", "guFE", False, None, 0.0, 0.1)]
# Cells with the residents' early-composition restriction are not checked: their mixed-integer programs did not finish
# within an hour; the LP bounds reported for them are valid outer bounds of the integer problem.
rows = []; log = timer(); prep = {}
for sg, sp, calib, s, eta, delta in CELLS:
    P = prep.setdefault(sg, Prep(sg)); W = P.W[sp]
    CL = {u: CLP(lp) for u, lp in P.lps(calib=calib, dF=None if s is None else ("slack", s)).items()}
    acc = dict(z_lo_lp=0.0, z_lo_int_bound=0.0, z_lo_int_incumbent=0.0, y_lo_int_bound=0.0, y_lo_int_actual=0.0); st = {}
    for u in P.units:
        clp = CL[u]; w = W[u]
        if not np.any(w): continue
        ylo, yhi = get_dong(sg, u, clp, KMS, eta, delta); cz, kz, cy, ky = objs(clp, w, ylo, yhi, +1)
        rl = clp.solve(cz, eta, delta); acc["z_lo_lp"] += kz + rl.fun
        ri = solve_int(clp, cz, eta, delta, 30)
        if ri.x is None: ri = solve_int(clp, cz, eta, delta, 180)
        st[ri.status] = st.get(ri.status, 0) + 1
        db = getattr(ri, "mip_dual_bound", None); acc["z_lo_int_bound"] += kz + (db if db is not None else rl.fun)
        acc["z_lo_int_incumbent"] += np.nan if ri.x is None else kz + ri.fun
        ry = solve_int(clp, cy, eta, delta, 30)
        if ry.x is None: ry = solve_int(clp, cy, eta, delta, 180)
        st[ry.status] = st.get(ry.status, 0) + 1
        if ry.x is None: acc["y_lo_int_actual"] = np.nan
        else: N, T = clp.state(ry.x, KMS); acc["y_lo_int_actual"] += float((w * N / T).sum())
        dy = getattr(ry, "mip_dual_bound", None); acc["y_lo_int_bound"] += ky + (dy if dy is not None else clp.solve(cy, eta, delta).fun)
    rows.append(dict(sg=sg, spec=sp, movement="calib" if calib else "uniform", slack=s, eta=eta, delta=delta, **acc,
                     solves_at_time_limit=st.get(1, 0), solves=sum(v for k, v in st.items())))
    log(rows[-1]); pd.DataFrame(rows).to_csv(f"{RES}/integer_check.csv", index=False)
