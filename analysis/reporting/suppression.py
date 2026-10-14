"""Conservative reporting gains under an explicitly defined primary-suppression rule.

Release each out-of-zone neighborhood x candidate count exactly if >= k,
otherwise release a suppressed marker. Counts of invalid ballots are included.
Two integer allocations producing the same report differ by at most k-1 in
every released component: exact cells agree and suppressed cells are in
{0,...,k-1}. Relaxing report equality to this necessary condition gives an
upper bound on the worst remaining width, hence a guaranteed lower bound on
the reduction. This is not a sharp bound for suppression, nor a privacy audit.
Complementary suppression of larger cells is outside this rule.

Usage: python analysis/reporting/suppression.py [election ...]
Output: results/suppression_<election>.csv
"""
import numpy as np
import pandas as pd

from disclosure_guarantee import wmax
from vwn.bounds import total
from vwn.paths import RES
from vwn.run import Prep, elections_from_argv, timer


def run(sg, thresholds=(1, 5, 10, 20)):
    P = Prep(sg)
    lps = P.lps(calib=True, dF=('slack', 0.02))
    W = P.W['guFE']
    lo, hi = total(P.units, lps, W, 1.0, 0.1)
    current_width = hi - lo
    if not np.isfinite(current_width) or current_width <= 0:
        raise RuntimeError(f'Invalid current width: {current_width}')
    log = timer()
    rows = []
    for threshold in thresholds:
        if threshold < 1 or int(threshold) != threshold:
            raise ValueError('Suppression thresholds must be positive integers')
        remaining = sum(wmax(lps[u], W[u], 1.0, 0.1, 'P2b', threshold - 1) for u in P.units)
        if remaining < -1e-8 or remaining > current_width + 1e-8:
            raise RuntimeError('Remaining-width bound is outside [0, current width]')
        rows.append(dict(sg=sg, threshold=threshold, tolerance=threshold-1,
                         current_width=current_width, remaining_width_upper=remaining,
                         guaranteed_reduction_lower=max(0.0, 1-remaining/current_width)))
        log(sg, threshold, rows[-1]['guaranteed_reduction_lower'])
    result = pd.DataFrame(rows)
    exact = pd.read_csv(RES / f'disclosure_guarantee_{sg}.csv')
    exact = exact[exact.config == 'calib, delta=0.1, s=0.02'].iloc[0]
    if 1 in thresholds and not np.isclose(result[result.threshold == 1].remaining_width_upper.iloc[0],
                                          exact.Wmax_P2b, atol=1e-9, rtol=0):
        raise RuntimeError('Exact-report result disagrees with the existing calculation')
    if np.any(np.diff(result.sort_values('threshold').remaining_width_upper) < -1e-8):
        raise RuntimeError('Width must not shrink when the tolerance is relaxed')
    result.to_csv(RES / f'suppression_{sg}.csv', index=False)


if __name__ == '__main__':
    for election in elections_from_argv(['20220309', '20240410', '20250603', '20260603']):
        run(election)
