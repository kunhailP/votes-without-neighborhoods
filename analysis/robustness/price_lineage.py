"""Rebuild available price summaries in isolation and audit earlier-price differences.

Uses saved assembled trades and the current saved address crosswalk, without
network access. Leaves all supplied analysis inputs unchanged. The 2025
summary has no raw-trade counterpart here and is explicitly excluded.
Output: results/price_lineage.csv (price comparisons and bound sensitivity).
"""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

import vwn.data as data_module
from vwn.bounds import total
from vwn.paths import ROOT, DATA, RES
from vwn.run import Prep

ELECTIONS = ['20121219', '20170509', '20220309', '20240410', '20260603']


def run():
    rows = []
    with tempfile.TemporaryDirectory(prefix='vwn-price-lineage-') as temporary:
        work = Path(temporary)
        shutil.copytree(DATA, work/'data', ignore=shutil.ignore_patterns('apt_raw', 'nec', 'mobility', 'mois', 'geo'))
        (work/'build').mkdir()
        shutil.copy2(ROOT/'build/build_trades.py', work/'build/build_trades.py')
        subprocess.run([sys.executable, str(work/'build/build_trades.py'), '--summaries', *ELECTIONS], check=True)
        for sg in ELECTIONS:
            name = f'seoul_hdong_aptprice_{sg}.csv'
            old = pd.read_csv(DATA/name); new = pd.read_csv(work/'data'/name)
            joined = old.merge(new, on=['gu', 'emd'], suffixes=('_old', '_new'), validate='one_to_one')
            if len(joined) != len(old) or len(new) != len(old):
                raise ValueError('Price reconstruction changed neighborhood coverage')
            left, right = joined.price_med_old, joined.price_med_new
            changed = ~np.isclose(left, right, rtol=1e-10, atol=1e-10, equal_nan=True)
            if not np.array_equal(left.notna(), right.notna()):
                raise ValueError('Price reconstruction changed missing-price coverage')
            rows.append(dict(kind='price_summary', sg=sg, changed_medians=int(changed.sum()),
                             max_relative_price_difference=float(((left-right).abs()/left).max())))
        data_module.DATA = work/'data'
        try:
            for sg in ELECTIONS[:2]:
                P = Prep(sg); lps = P.lps()
                original = pd.read_csv(RES/f'spatial_scope_{sg}.csv')
                for sample, excluded in [('all', False), ('excl_gangnam3', True)]:
                    keep = P.has & (~np.isin(P.labs['guFE'], ['강남구', '서초구', '송파구']) if excluded else True)
                    w = np.zeros(len(P.x)); w[keep] = data_module.weights(P.x[keep], P.labs['guFE'][keep], True)
                    for column, eta, delta in [('A', 1.0, 1.0), ('C', 0.0, 0.1)]:
                        low, high = total(P.units, lps, P.wsplit(w), eta, delta)
                        reference = original[(original['sample'] == sample) & (original.spec == 'slope') & (original.column == column)]
                        if len(reference) != 1:
                            raise ValueError('Missing original bound')
                        before_low, before_high = reference[['z_lo', 'z_hi']].iloc[0]
                        rows.append(dict(kind='bound', sg=sg, sample=sample, column=column,
                                         original_lower=before_low, original_upper=before_high,
                                         rebuilt_lower=low, rebuilt_upper=high,
                                         max_endpoint_difference=max(abs(low-before_low), abs(high-before_high)),
                                         sign_conclusion_unchanged=(low > 0) == (before_low > 0) and (high < 0) == (before_high < 0)))
        finally:
            data_module.DATA = DATA
    result = pd.DataFrame(rows)
    if not result[result.kind == 'bound'].sign_conclusion_unchanged.all():
        raise RuntimeError('A sign conclusion changed under the rebuilt early prices')
    result.to_csv(RES/'price_lineage.csv', index=False)
    print(result.to_string(index=False))


if __name__ == '__main__':
    run()
