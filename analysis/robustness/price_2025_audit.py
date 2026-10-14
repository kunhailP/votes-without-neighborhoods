"""Reconstruct 2025 prices from the newly retrieved MOLIT snapshot in isolation.

Compare the archived summary to the reconstructed prices, including changes in
geographic support. Recompute A/C/D/E slope bounds with the new prices while
leaving the historical inputs and reported results untouched.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import numpy as np
import pandas as pd
from vwn.paths import ROOT, DATA, RES
from vwn.run import Prep
from vwn.data import weights, norm
from vwn.bounds import total
from vwn.lp import KMS, INV


def run():
    with tempfile.TemporaryDirectory(prefix='vwn-2025-rebuild-') as td:
        temp = Path(td)
        for folder in ['build', 'data/trades', 'data/raw/juso', 'data/raw/molit']:
            (temp/folder).mkdir(parents=True)
        shutil.copy2(ROOT/'build/build_trades.py', temp/'build/build_trades.py')
        (temp/'data/raw/juso/seoul_jibun_to_hdong_juso.csv').symlink_to(DATA/'raw/juso/seoul_jibun_to_hdong_juso_2025_audit.csv')
        name = 'raw/molit/seoul_apt_trades_20250603.csv'
        (temp/'data'/name).symlink_to(DATA/name)
        shutil.copy2(DATA/'seoul_2025pres_electorate_api.csv', temp/'data/seoul_20250603_electorate_api.csv')
        subprocess.run([sys.executable, str(temp/'build/build_trades.py'), '--summaries', '20250603'], check=True)
        new = pd.read_csv(temp/'data/seoul_hdong_aptprice_20250603.csv')
        new.to_csv(RES/'price_2025_rebuilt.csv', index=False)
        shutil.copy2(temp/'data/trades/trades_hdong_20250603.csv', DATA/'trades/trades_hdong_20250603.csv')
    old = pd.read_csv(DATA/'seoul_hdong_aptprice_202406_202505.csv')
    old['key'] = old.gu+'|'+old.hdong.map(norm)
    new['key'] = new.gu+'|'+new.emd.map(norm)
    joined = old.merge(new, on='key', how='outer', validate='one_to_one')
    joined['relative_change'] = joined.price_med/joined.med_per_m2-1
    joined.to_csv(RES/'price_2025_comparison.csv', index=False)
    common = joined.med_per_m2.notna() & joined.price_med.notna()
    raw = pd.read_csv(DATA/'raw/molit/seoul_apt_trades_20250603.csv', dtype=str)
    mapped = pd.read_csv(DATA/'trades/trades_hdong_20250603.csv')
    report = dict(new_snapshot='2026-10-14 MOLIT retrieval; original generation code remains unavailable',
                  raw_records=len(raw), noncancelled_records=int(raw.cdealType.fillna('').str.strip().ne('O').sum()),
                  mapped_trade_records=len(mapped),
                  archived_priced=int(joined.med_per_m2.notna().sum()),
                  rebuilt_priced=int(joined.price_med.notna().sum()), common_priced=int(common.sum()),
                  median_absolute_relative_change=float(joined.loc[common, 'relative_change'].abs().median()),
                  max_absolute_relative_change=float(joined.loc[common, 'relative_change'].abs().max()),
                  changed_over_one_percent=int((joined.loc[common, 'relative_change'].abs()>.01).sum()),
                  log_price_correlation=float(np.log(joined.loc[common, 'med_per_m2']).corr(np.log(joined.loc[common, 'price_med']))))
    prep = Prep('20250603')
    price = new.set_index('key').price_med.to_dict()
    x = np.array([np.log(price.get(u+'|'+norm(d), np.nan)) for u, d in prep.idx])
    baseline = pd.read_csv(RES/'spatial_scope_20250603.csv')
    rows = []
    day = np.concatenate([g['A'][:, KMS]/(g['Avotes']-g['A'][:, INV]) for g, _ in prep.G.values()])
    for sample, exclude in [('all', False), ('excl_gangnam3', True)]:
        keep = np.isfinite(x) & (~np.isin(prep.labs['guFE'], ['강남구', '서초구', '송파구']) if exclude else True)
        w = np.zeros(len(x))
        w[keep] = weights(x[keep], prep.labs['guFE'][keep], True)
        for col, calib, eta, delta, comp in [('A', False, 1., 1., None), ('C', False, 0., .1, None),
                                             ('D', True, 1., .1, None), ('E', True, 1., .1, ('slack', .02))]:
            lo, hi = total(prep.units, prep.lps(calib=calib, dF=comp), prep.wsplit(w), eta, delta)
            ref = baseline[(baseline['sample']==sample)&(baseline.spec=='slope')&(baseline.column==col)].iloc[0]
            rows.append(dict(sg=20250603, sample=sample, column=col, archived_lower=ref.z_lo, archived_upper=ref.z_hi,
                             rebuilt_lower=lo, rebuilt_upper=hi, rebuilt_election_day=float(w@day),
                             n_rebuilt=int(keep.sum()), sign_unchanged=bool((lo>0)==(ref.z_lo>0) and (hi<0)==(ref.z_hi<0))))
            print(sample, col, lo, hi, flush=True)
    pd.DataFrame(rows).to_csv(RES/'price_2025_bounds.csv', index=False)
    common_rows = []
    lps = prep.lps(calib=True, dF=('slack', .02))
    for sample, exclude in [('all', False), ('excl_gangnam3', True)]:
        keep = prep.has & np.isfinite(x) & (~np.isin(prep.labs['guFE'], ['강남구', '서초구', '송파구']) if exclude else True)
        entry = dict(sample=sample, n_common=int(keep.sum()))
        for source, values in [('archived', prep.x), ('rebuilt', x)]:
            w = np.zeros(len(x))
            w[keep] = weights(values[keep], prep.labs['guFE'][keep], True)
            lo, hi = total(prep.units, lps, prep.wsplit(w), 1., .1)
            entry[source+'_lower'], entry[source+'_upper'] = lo, hi
        entry['sign_unchanged'] = bool((entry['archived_lower']>0)==(entry['rebuilt_lower']>0) and
                                       (entry['archived_upper']<0)==(entry['rebuilt_upper']<0))
        common_rows.append(entry)
    pd.DataFrame(common_rows).to_csv(RES/'price_2025_common_support.csv', index=False)
    report['all_checked_signs_unchanged'] = all(row['sign_unchanged'] for row in rows)
    report['common_support_signs_unchanged'] = all(row['sign_unchanged'] for row in common_rows)
    report['maximum_endpoint_change'] = max(max(abs(r['rebuilt_lower']-r['archived_lower']), abs(r['rebuilt_upper']-r['archived_upper'])) for r in rows)
    (ROOT/'docs/price_2025_audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    run()
