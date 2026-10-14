"""Identified sets for z slopes on the uniform-movement grid, conventional comparators and breakdown points eta*
(Table 2, columns A-C; Online Appendix Table C4; with --no-zones, Section 4.4, Table 4 and Online Appendix Table C27).

Cells: eta in {0, 0.05, 0.1, 0.2, 1} x delta in {0.1, 0.2, 1, delta_min(eta)}. eta = 1 removes the movement
cap (the cap r_j + K_j can never bind), so (eta = 1, delta = 1) is the accounting-only set: the returns,
the roll and, in 2026, the statutory early-voting zones, with no assumption. eta = 0 is the
minimum-movement benchmark. eta* is computed at fixed delta (Lambda increases in eta, Proposition 3) and
stored as the [lo, hi] ends of the final bisection interval (the sign is identified at lo).

Output: results/main_grid_<sg>.csv, results/main_grid_<sg>_dmin.csv (suffix _nozones with --no-zones)
Usage: python analysis/neighborhoods/main_grid.py [--no-zones] [<sg> ...]"""
import sys
import numpy as np
import pandas as pd
from vwn.run import Prep, timer, elections_from_argv
from vwn.bounds import total, breakdown
from vwn.lp import KMS
from vwn import baselines
from vwn.paths import RES

ETAS = [0.0, 0.05, 0.1, 0.2, 1.0]; DELTAS = [0.1, 0.2, 1.0]


def run(sg, zones=True):
    log = timer(); P = Prep(sg, zones=zones); LP = P.lps(); rows = []
    tag = "" if zones else "_nozones"
    add = lambda **k: rows.append(dict(sg=sg, **k))
    for sp, w in P.Wfull.items():
        for nm, fn in [("exclude", baselines.exclude), ("proportional", baselines.proportional), ("station_imputation", baselines.station_imputation)]:
            v = np.concatenate([fn(P.G[u][0], KMS) for u in P.units])
            add(spec=sp, kind="baseline", method=nm, value=float((w * v).sum()))
    dmin = {u: {} for u in P.units}

    def dm(u, eta):
        if eta not in dmin[u]: dmin[u][eta] = LP[u].delta_min(eta)
        return dmin[u][eta]

    for sp in P.W:
        for eta in ETAS:
            for dl in DELTAS:
                lo, hi = total(P.units, LP, P.W[sp], eta, dl); add(spec=sp, kind="bound", eta=eta, delta=str(dl), lo=lo, hi=hi)
            # delta_min path: each unit at its own smallest feasible band
            lo = hi = 0.0
            from vwn.bounds import bounds_with_w
            for u in P.units:
                b = bounds_with_w(LP[u], P.W[sp][u], KMS, eta, dm(u, eta)); lo += b[0]; hi += b[1]
            add(spec=sp, kind="bound", eta=eta, delta="dmin", lo=lo, hi=hi)
        log(sg, sp, "grid")
    for sp in P.W:
        for dl in DELTAS:
            f = lambda eta: total(P.units, LP, P.W[sp], eta, dl)[0]
            a, b = breakdown(f, 0.0, 1.0, 1 / 512)
            grid = [f(e) for e in np.linspace(0, max(b, 1e-3), 6)]
            mono = all(grid[k] >= grid[k + 1] - 1e-9 for k in range(5) if np.isfinite(grid[k]) and np.isfinite(grid[k + 1]))
            add(spec=sp, kind="eta_star", delta=str(dl), lo=a, hi=b, note="monotone" if mono else "NON-MONOTONE")
        log(sg, sp, "eta*")
    pd.DataFrame(rows).to_csv(f"{RES}/main_grid_{sg}{tag}.csv", index=False)
    pd.DataFrame(dmin).T.to_csv(f"{RES}/main_grid_{sg}{tag}_dmin.csv")


if __name__ == "__main__":
    zones = "--no-zones" not in sys.argv
    for sg in elections_from_argv():
        run(sg, zones)
