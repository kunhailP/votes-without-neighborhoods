"""Audit saved integer allocations directly from the accounting identities.

No optimizer or constraint matrix is used in this audit. It checks the
observed totals, zones, movement and composition inequalities explicitly,
then computes attained slopes with and without the three southeastern gu.
Output: results/integer_witness_summary.csv
"""
import numpy as np
import pandas as pd

from vwn.lp import KMS
from vwn.paths import RES
from vwn.run import Prep


def positive_max(a):
    return float(np.max(a, initial=0))


def audit_allocation(P, unit, x):
    g, E = P.G[unit]; n, C = g['K'].shape
    if x.shape != (n*n*C+2*n*C+n,) or not np.issubdtype(x.dtype, np.integer):
        raise ValueError('Invalid saved integer allocation')
    cut = n*n*C
    F = x[:cut].reshape(n, n, C)
    B = x[cut:cut+n*C].reshape(n, C)
    G = x[cut+n*C:cut+2*n*C].reshape(n, C)
    U = x[cut+2*n*C:]
    removed = E-g['D']; K = g['K']; A = g['A']; Ksum = K.sum(1)
    violations = [positive_max(-x)]
    for actual, observed in [(F.sum(0), K), (B.sum(0), g['Bc']), (G.sum(0), g['Gc']),
                             (U.sum(), g['U']), (F.sum((1, 2))+B.sum(1)+G.sum(1)+U, removed)]:
        violations.append(positive_max(np.abs(actual-observed)))
    if 'allow' in g:
        violations.append(positive_max(F[~g['allow']]))
    zone = g.get('zone', np.zeros(n))
    ratio = np.zeros(n)
    for label in np.unique(zone):
        mask = zone == label
        ratio[mask] = Ksum[mask].sum()/max(removed[mask].sum(), 1)
    intercept = np.maximum(np.maximum(0, Ksum-removed), Ksum-ratio*removed)
    off_diagonal = F.sum((0, 2))-np.einsum('iic->i', F)
    violations.append(positive_max(off_diagonal-intercept-P.ev[unit]*Ksum))
    anchor = g['a_tilde']
    violations.extend([positive_max(B-(anchor+0.1)*B.sum(1, keepdims=True)),
                       positive_max(np.maximum(anchor-0.1, 0)*B.sum(1, keepdims=True)-B)])
    reference = np.clip(A/np.maximum(A.sum(1, keepdims=True), 1)+K.sum(0)/K.sum()-A.sum(0)/A.sum(), 0, 1)
    width = np.abs(K/np.maximum(Ksum[:, None], 1)-reference)+0.02
    resident_early = F.sum(1)
    violations.extend([positive_max(resident_early-(reference+width)*resident_early.sum(1, keepdims=True)),
                       positive_max(np.maximum(reference-width, 0)*resident_early.sum(1, keepdims=True)-resident_early)])
    violation = max(violations)
    if violation > 1e-7:
        raise ValueError(f'{P.sg} {unit}: constraint violation {violation}')
    N = A[:, KMS]+F[:, :, KMS].sum(1)+B[:, KMS]+G[:, KMS]
    return N/(g['Avotes']+removed), violation


def slope_weights(P, exclude=False):
    keep = P.has.copy()
    if exclude:
        keep &= ~np.isin(P.labs['guFE'], ['강남구', '서초구', '송파구'])
    centered = np.zeros(len(P.x))
    for label in np.unique(P.labs['guFE'][keep]):
        mask = keep & (P.labs['guFE'] == label)
        centered[mask] = P.x[mask]-P.x[mask].mean()
    return centered/np.dot(centered, centered)


def run():
    rows = []
    for sg in ['20220309', '20240410', '20250603', '20260603']:
        P = Prep(sg); values = {}; violations = []
        certificates = pd.read_csv(RES/f'integer_witness_{sg}.csv')
        if len(certificates) != 2*len(P.units) or not certificates.witness_found.all():
            raise ValueError(f'{sg}: missing integer witnesses')
        for side in ['lower', 'upper']:
            portions = []
            for unit in P.units:
                with np.load(RES/'integer_allocations'/sg/f'{unit}_{side}.npz', allow_pickle=False) as saved:
                    shares, violation = audit_allocation(P, unit, saved['x'])
                portions.append(shares); violations.append(violation)
            values[side] = np.concatenate(portions)
        continuous = pd.read_csv(RES/f'spatial_scope_{sg}.csv')
        for sample, exclude in [('all', False), ('excl_gangnam3', True)]:
            w = slope_weights(P, exclude)
            low = float(w@values['lower']); high = float(w@values['upper'])
            reference = continuous[(continuous['sample'] == sample) & (continuous.spec == 'slope') & (continuous.column == 'E')]
            if len(reference) != 1:
                raise ValueError('Missing continuous reference')
            lp_low, lp_high = reference[['z_lo', 'z_hi']].iloc[0]
            if low < lp_low-1e-9 or high > lp_high+1e-9:
                raise ValueError('Integer witness is outside the continuous bound')
            row = dict(sg=sg, sample=sample, lp_lower=lp_low, integer_lower=low,
                       integer_upper=high, lp_upper=lp_high,
                       max_endpoint_gap=max(low-lp_low, lp_high-high),
                       max_constraint_violation=max(violations), certificates=len(certificates))
            rows.append(row); print(row, flush=True)
    pd.DataFrame(rows).to_csv(RES/'integer_witness_summary.csv', index=False)


if __name__ == '__main__':
    run()
