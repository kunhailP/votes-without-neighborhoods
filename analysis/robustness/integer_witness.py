"""Construct integer witnesses close to the main continuous z-slope endpoints.

For each LP endpoint, solve a zero-objective integer feasibility problem near
that solution, first inside its floor/ceiling box and then boxes expanded by
1 and 4 ballots. Every witness is rounded and checked against the original
constraints. These are attainable values, not proven integer optima. A
failed search does not establish integer infeasibility.

Usage: python analysis/robustness/integer_witness.py [election ...]
Outputs: results/integer_witness_<election>.csv (one row per jurisdiction/side).
"""
import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp

from vwn.bounds import slope_c
from vwn.paths import RES
from vwn.run import Prep, elections_from_argv, timer


def witness(lp, objective, eta=1.0, delta=0.1, time_limit=3.0):
    endpoint = lp.solve(objective, eta, delta)
    if endpoint.status != 0:
        raise RuntimeError(f'LP endpoint failed: {endpoint.status}')
    eq, eq_rhs, ub, ub_rhs = lp.cached_constraints(eta, delta)
    constraints = [LinearConstraint(eq, eq_rhs, eq_rhs), LinearConstraint(ub, -np.inf, ub_rhs)]
    for radius in [0, 1, 4]:
        lower = np.maximum(0, np.floor(endpoint.x)-radius)
        upper = np.ceil(endpoint.x)+radius
        result = milp(np.zeros(lp.nv), integrality=np.ones(lp.nv), bounds=Bounds(lower, upper),
                      constraints=constraints, options=dict(time_limit=time_limit, disp=False))
        if result.x is None:
            continue
        x = np.rint(result.x)
        violation = max(float(np.max(np.abs(eq@x-eq_rhs), initial=0)),
                        float(np.max(ub@x-ub_rhs, initial=0)), float(np.max(-x, initial=0)))
        if violation <= 1e-7:
            return endpoint, x, radius, violation
    return endpoint, None, None, None


def run(sg):
    P = Prep(sg); lps = P.lps(calib=True, dF=('slack', 0.02)); rows = []; log = timer()
    for unit in P.units:
        lp = lps[unit]; c, constant = slope_c(lp, P.W['guFE'][unit])
        for side, direction in [('lower', 1), ('upper', -1)]:
            endpoint, x, radius, violation = witness(lp, direction*c)
            if x is not None:
                destination = RES / 'integer_allocations' / sg
                destination.mkdir(parents=True, exist_ok=True)
                np.savez_compressed(destination / f'{unit}_{side}.npz', x=x.astype(np.int64))
            row = dict(sg=sg, unit=unit, side=side, lp_value=constant+direction*endpoint.fun,
                       witness_found=x is not None, integer_value=np.nan if x is None else constant+float(c@x),
                       repair_radius=radius, constraint_violation=violation)
            rows.append(row)
            pd.DataFrame(rows).to_csv(RES/f'integer_witness_{sg}.csv', index=False)
            log(sg, unit, side, row['witness_found'])


if __name__ == '__main__':
    for election in elections_from_argv(['20220309', '20240410', '20250603', '20260603']):
        run(election)
