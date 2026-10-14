"""Retrieve the missing June 2024--May 2025 Seoul transaction window.

This is a newly dated MOLIT snapshot, not recovery of the original download.
Credentials are read from DATA_GO_KR_KEY or --env-file and are never saved.
Raw XML, an assembled CSV and a request/hash manifest permit offline auditing.
"""
import argparse
import csv
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ENDPOINT = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'
CODES = '11110 11140 11170 11200 11215 11230 11260 11290 11305 11320 11350 11380 11410 11440 11470 11500 11530 11545 11560 11590 11620 11650 11680 11710 11740'.split()
MONTHS = [f'2024{m:02}' for m in range(6, 13)] + [f'2025{m:02}' for m in range(1, 6)]
ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path)
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    key = os.environ.get('DATA_GO_KR_KEY')
    if not key and args.env_file:
        for line in args.env_file.read_text().splitlines():
            if line.startswith('DATA_GO_KR_KEY='):
                key = line.split('=', 1)[1].strip().strip('\"\'')
    if not key:
        raise SystemExit('Set DATA_GO_KR_KEY or supply --env-file.')
    key = urllib.parse.unquote(key)
    rawdir = ROOT/'data/raw/molit/refetch_2025'
    rawdir.mkdir(parents=True, exist_ok=True)

    def fetch(task):
        code, month = task
        records, requests, page = [], [], 1
        while True:
            query = dict(LAWD_CD=code, DEAL_YMD=month, pageNo=page, numOfRows=1000)
            target = rawdir/f'{code}_{month}_{page}.xml'
            if not target.exists():
                url = ENDPOINT+'?'+urllib.parse.urlencode(dict(query, serviceKey=key))
                for attempt in range(3):
                    try:
                        with urllib.request.urlopen(url, timeout=25) as response:
                            payload = response.read()
                        break
                    except Exception as error:
                        if attempt == 2:
                            # Do not print an exception URL containing credentials.
                            raise RuntimeError(f'{code}/{month}/{page}: {type(error).__name__}') from None
                        time.sleep(1+attempt)
                parsed = ET.fromstring(payload)
                status = (parsed.findtext('.//resultCode') or '').strip()
                if status not in {'00', '000'}:
                    raise RuntimeError(f'{code}/{month}/{page}: provider result {status}')
                target.write_bytes(payload)
                time.sleep(0.15)
            payload = target.read_bytes()
            parsed = ET.fromstring(payload)
            total = int(parsed.findtext('.//totalCount'))
            items = [{v.tag: (v.text or '').strip() for v in item} for item in parsed.iter('item')]
            if not items and len(records) < total:
                raise RuntimeError(f'{code}/{month}: incomplete pagination')
            records.extend(dict(row, lawd_cd=code, deal_ym=month) for row in items)
            requests.append(dict(query=query, file=target.name, total=total, returned=len(items),
                                 retrieved_at_utc=datetime.fromtimestamp(target.stat().st_mtime, timezone.utc).isoformat(),
                                 sha256=hashlib.sha256(payload).hexdigest()))
            if len(records) == total:
                break
            if len(records) > total:
                raise RuntimeError(f'{code}/{month}: record count exceeds provider total')
            page += 1
        return records, requests

    tasks = [(code, month) for code in CODES for month in MONTHS]
    rows, requests = [], []
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 4))) as pool:
        for i, (records, pages) in enumerate(pool.map(fetch, tasks), 1):
            rows.extend(records)
            requests.extend(pages)
            if i % 25 == 0:
                print(f'Completed {i}/{len(tasks)} district-months; {len(rows)} records', flush=True)
    output = rawdir.parent/'seoul_apt_trades_20250603.csv'
    with output.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted({k for row in rows for k in row}))
        writer.writeheader()
        writer.writerows(rows)
    manifest = dict(endpoint=ENDPOINT, election='20250603', window=['202406', '202505'],
                    snapshot_status='new retrieval; not the original snapshot', district_months=len(tasks),
                    records=len(rows), assembled_sha256=hashlib.sha256(output.read_bytes()).hexdigest(), requests=requests)
    (rawdir/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print(f'Wrote {len(rows)} records and {len(requests)} request records', flush=True)


if __name__ == '__main__':
    main()
