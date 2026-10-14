"""Extend the saved address crosswalk for the new 2025 transaction snapshot.

Only missing/blank lot mappings are queried. The original crosswalk is never
overwritten. Credentials are supplied through JUSO_KEY or --env-file.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import time
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path)
    args = parser.parse_args()
    if not os.environ.get('JUSO_KEY') and args.env_file:
        for line in args.env_file.read_text().splitlines():
            if line.startswith('JUSO_KEY='):
                os.environ['JUSO_KEY'] = line.split('=', 1)[1].strip().strip('\"\'')
    spec = importlib.util.spec_from_file_location('address_source', ROOT/'build/fetch_jibun_hdong.py')
    source = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(source)
    dest = ROOT/'data/raw/juso'
    original = pd.read_csv(dest/'seoul_jibun_to_hdong_juso.csv', dtype=str)
    trades = pd.read_csv(ROOT/'data/raw/molit/seoul_apt_trades_20250603.csv', dtype=str).fillna('')
    trades = trades[trades.cdealType != 'O']
    cols = ['sggCd','umdCd','bonbun','bubun']
    for df in [original, trades]:
        for col in ['bonbun','bubun']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(-1).astype(int)
    known = set(map(tuple, original[original.hemdNm.notna() & original.hemdNm.ne('')][cols].values))
    tasks = [r for r in trades.drop_duplicates(cols).to_dict('records') if tuple(r[c] for c in cols) not in known and r['bonbun']>0]
    cache = dest/'refetch_2025_addresses'
    cache.mkdir(exist_ok=True)

    def fetch(r):
        sgg, umd, b, s = (r[c] for c in cols)
        mt = r.get('landCd') or '1'
        target = cache/f'{sgg}_{umd}_{b}_{s}_{mt}.json'
        if target.exists():
            saved = json.loads(target.read_text())
            result = saved['response']
        else:
            keyword = f"서울특별시 {source.GU[sgg]} {r['umdNm']} {'산 ' if mt=='2' else ''}{b}"+(f'-{s}' if s else '')
            try:
                result = source.query(keyword)
            except Exception as error:
                raise RuntimeError(f'{sgg}/{umd}/{b}/{s}: {type(error).__name__}') from None
            target.write_text(json.dumps(dict(retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
                                             keyword=keyword, response=result),ensure_ascii=False,indent=2)+'\n')
            time.sleep(.1)
        chosen, match = source.pick(result, sgg, umd, b, s, mt)
        return dict(sggCd=sgg, umdCd=umd, umdNm=r['umdNm'], bonbun=b, bubun=s, landCd=mt,
                    hemdNm=(chosen or {}).get('hemdNm',''), admCd=(chosen or {}).get('admCd',''),
                    bdMgtSn=(chosen or {}).get('bdMgtSn',''), match=match, n_res=len(result))

    with ThreadPoolExecutor(max_workers=3) as pool:
        added = list(pool.map(fetch, tasks))
    extra = pd.DataFrame(added, columns=original.columns)
    updated_keys = set(map(tuple, extra[cols].values))
    keep = [tuple(row) not in updated_keys for row in original[cols].values]
    full = pd.concat([original[keep], extra], ignore_index=True)
    full.to_csv(dest/'seoul_jibun_to_hdong_juso_2025_audit.csv',index=False)
    print('queried lots',len(tasks),'returned nonblank administrative dongs',int(extra.hemdNm.fillna('').ne('').sum()),flush=True)


if __name__ == '__main__':
    main()
