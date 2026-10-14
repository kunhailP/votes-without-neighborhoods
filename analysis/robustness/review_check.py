"""Verify headline results from the supplied analysis inputs; never overwrite results/.

Run `make verify`. This recomputes 14 continuous-bound configurations and
checks all saved integer allocations using arithmetic identities rather than
the solver's constraint matrices. It is an execution check, not an independent
validation of the model, assumptions, or authenticity of the raw sources.
"""
import argparse
import hashlib
import importlib.metadata
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from vwn.bounds import slope_c
from vwn.data import ELECTIONS
from vwn.paths import RES
from vwn.run import Prep
from verify_integer_witness import audit_allocation, slope_weights

RECENT = {'20220309', '20240410', '20250603', '20260603'}


def result_hashes():
    return {str(p.relative_to(RES)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(RES.rglob('*')) if p.is_file() and p.suffix in {'.csv', '.npz'}}


def endpoints(P, lps, w, eta, delta):
    values = np.zeros(2)
    max_violation = 0.0
    split = P.wsplit(w)
    for unit in P.units:
        lp = lps[unit]
        c, constant = slope_c(lp, split[unit])
        eq, rhs, ub, upper = lp.cached_constraints(eta, delta)
        for side, direction in enumerate([1, -1]):
            r = lp.solve(direction*c, eta, delta)
            if r.status != 0:
                raise ValueError(f'{P.sg} {unit}: solver status {r.status}')
            values[side] += constant+direction*r.fun
            violation = max(float(np.max(np.abs(eq@r.x-rhs), initial=0)),
                            float(np.max(ub@r.x-upper, initial=0)),
                            float(np.max(-r.x, initial=0)))
            max_violation = max(max_violation, violation)
    if max_violation > 1e-7:
        raise ValueError(f'{P.sg}: LP feasibility residual {max_violation}')
    return values, max_violation


def check(output):
    original = result_hashes()
    report = {'complete': False, 'scope': __doc__.strip(),
              'checked_at_utc': datetime.now(timezone.utc).isoformat(),
              'python': platform.python_version(),
              'versions': {name: importlib.metadata.version(name) for name in ['numpy', 'scipy', 'pandas']},
              'inputs': [], 'bounds': [], 'integer_allocations': 0,
              'max_integer_constraint_violation': 0.0,
              'remaining_source_gap': 'Original 2025 price-summary construction remains unavailable; a separately retrieved snapshot and alternative reconstruction are supplied in price_2025_audit.'}
    for sg in ELECTIONS:
        P = Prep(sg)
        for unit, (g, E) in P.G.items():
            if np.any(E < g['D']) or g['U'] < 0 or np.any(g['Avotes']+E-g['D'] <= 0):
                raise ValueError(f'{sg} {unit}: invalid electorate accounting')
            for a in [E, g['D'], g['A'], g['K'], g['Bc'], g['Gc']]:
                if not np.isfinite(a).all() or np.any(a < 0) or not np.allclose(a, np.rint(a), atol=1e-9, rtol=0):
                    raise ValueError(f'{sg} {unit}: invalid observed counts')
            if not np.array_equal(g['A'].sum(1), g['Avotes']):
                raise ValueError(f'{sg} {unit}: election-day counts disagree')
        report['inputs'].append({'election': sg, 'jurisdictions': len(P.units),
                                 'neighborhoods': len(P.idx), 'priced': int(P.has.sum())})
        reference = pd.read_csv(RES/f'spatial_scope_{sg}.csv')
        configurations = [('A', False, None, 1.0, 1.0, [('all', False)])]
        if sg in RECENT:
            configurations.append(('E', True, ('slack', 0.02), 1.0, 0.1,
                                   [('all', False), ('excl_gangnam3', True)]))
        for column, calibrated, composition, eta, delta, scopes in configurations:
            lps = P.lps(calib=calibrated, dF=composition)
            for sample, exclude in scopes:
                w = slope_weights(P, exclude)
                values, residual = endpoints(P, lps, w, eta, delta)
                ref = reference[(reference['sample'] == sample) &
                                (reference.spec == 'slope') & (reference.column == column)]
                if len(ref) != 1:
                    raise ValueError(f'{sg}: missing reference {column} {sample}')
                shipped = ref[['z_lo', 'z_hi']].iloc[0].to_numpy(float)
                difference = float(np.max(np.abs(values-shipped)))
                if difference > 1e-8:
                    raise ValueError(f'{sg} {column} {sample}: result differs by {difference}')
                report['bounds'].append({'election': sg, 'column': column, 'sample': sample,
                                         'recomputed': values.tolist(), 'shipped': shipped.tolist(),
                                         'max_absolute_difference': difference,
                                         'max_constraint_violation': residual})
                print(sg, column, sample, 'verified', flush=True)
        if sg in RECENT:
            shares = {}
            for side in ['lower', 'upper']:
                portions = []
                for unit in P.units:
                    path = RES/'integer_allocations'/sg/f'{unit}_{side}.npz'
                    with np.load(path, allow_pickle=False) as saved:
                        value, violation = audit_allocation(P, unit, saved['x'])
                    portions.append(value)
                    report['integer_allocations'] += 1
                    report['max_integer_constraint_violation'] = max(
                        report['max_integer_constraint_violation'], violation)
                shares[side] = np.concatenate(portions)
            summary = pd.read_csv(RES/'integer_witness_summary.csv')
            for sample, exclude in [('all', False), ('excl_gangnam3', True)]:
                w = slope_weights(P, exclude)
                attained = np.array([w@shares['lower'], w@shares['upper']])
                ref = summary[(summary.sg == int(sg)) & (summary['sample'] == sample)]
                if len(ref) != 1 or not np.allclose(
                        attained, ref[['integer_lower', 'integer_upper']].iloc[0], atol=1e-10, rtol=0):
                    raise ValueError(f'{sg} {sample}: integer summary mismatch')
    if result_hashes() != original:
        raise ValueError('Verification modified results/')
    report.update(complete=True, checked_bound_configurations=len(report['bounds']),
                  result_files_unchanged=True,
                  max_absolute_difference=max(r['max_absolute_difference'] for r in report['bounds']))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(f'Verified {len(report["bounds"])} bound configurations and '
          f'{report["integer_allocations"]} integer allocations; report: {output}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('logs/review_verification.json'))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({'complete': False, 'status': 'running'})+'\n')
    try:
        check(args.output)
    except Exception as error:
        args.output.write_text(json.dumps({'complete': False, 'status': 'failed',
                                          'error': str(error)}, ensure_ascii=False, indent=2)+'\n')
        raise
