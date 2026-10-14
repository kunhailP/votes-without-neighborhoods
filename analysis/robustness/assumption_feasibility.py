"""Distance from refutation under the main movement and in-zone restrictions.

For each counting jurisdiction, find the smallest feasible out-of-zone band,
then recompute slopes using that band plus common excess slack. Feasibility is
compatibility with observed counts, not validation of unobserved composition.
"""
import sys
import numpy as np
import pandas as pd
from vwn.run import Prep
from vwn.data import weights
from vwn.bounds import bounds_with_w
from vwn.lp import KMS
from vwn.paths import RES


def run(sg):
    prep = Prep(sg)
    lps = prep.lps(calib=True, dF=('slack', .02))
    minima = {u: lp.delta_min(1., tol=1e-5) for u, lp in lps.items()}
    if not all(np.isfinite(list(minima.values()))):
        raise ValueError('Main in-zone restriction infeasible even without an out-of-zone restriction')
    pd.DataFrame([dict(sg=sg, unit=u, delta_min_upper=d, bisection_width=1e-5,
                       main_band_feasible=lps[u].feasible(1., .1), main_band_margin=.1-d)
                  for u, d in minima.items()]).to_csv(RES/f'feasibility_units_{sg}.csv', index=False)
    rows = []
    for sample, exclude in [('all', False), ('excl_gangnam3', True)]:
        keep = prep.has & (~np.isin(prep.labs['guFE'], ['강남구','서초구','송파구']) if exclude else True)
        w = np.zeros(len(prep.x))
        w[keep] = weights(prep.x[keep], prep.labs['guFE'][keep], True)
        split = prep.wsplit(w)
        for slack in [.02, .05, .10]:
            lo = hi = 0.
            for unit, lp in lps.items():
                bound = bounds_with_w(lp, split[unit], KMS, 1., min(1., minima[unit]+slack))
                if bound is None:
                    raise ValueError('Excess-slack model unexpectedly infeasible')
                lo += bound[0]
                hi += bound[1]
            rows.append(dict(sg=sg, sample=sample, excess_slack=slack, lower=lo, upper=hi,
                             max_delta_min=max(minima.values()),
                             min_main_margin=.1-max(minima.values())))
    pd.DataFrame(rows).to_csv(RES/f'feasibility_bounds_{sg}.csv', index=False)
    print(sg, 'max minimum band', max(minima.values()), rows, flush=True)


if __name__ == '__main__':
    run(sys.argv[1])
