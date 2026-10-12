"""MOLIT apartment sale transactions, detailed (RTMSDataSvcAptTradeDev): Seoul's 25 gu, 12 months before each election.
Usage:
    export DATA_GO_KR_KEY='<service key (Decoding)>'   # same key as the electorate API, but the apartment trade
                                                       # dataset must be requested separately on data.go.kr
    python3 fetch_apttrade.py                    # default: 2017, 2022, 2024 (add 2012 with --with-2012)
    python3 fetch_apttrade.py 20220309           # selected elections only
- Cached per (gu, month) in data/raw/molit/apt_raw/; rerun to resume after an interruption or the daily call limit.
- Output: data/raw/molit/seoul_apt_trades_<sgId>.csv  (all raw fields + lawd_cd, deal_ym)
Standard library only."""
import os, sys, csv, time, urllib.parse, urllib.request, urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path

URL = os.environ.get("VWN_APT_URL") or "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
LAWD = {"종로구":"11110","중구":"11140","용산구":"11170","성동구":"11200","광진구":"11215","동대문구":"11230",
        "중랑구":"11260","성북구":"11290","강북구":"11305","도봉구":"11320","노원구":"11350","은평구":"11380",
        "서대문구":"11410","마포구":"11440","양천구":"11470","강서구":"11500","구로구":"11530","금천구":"11545",
        "영등포구":"11560","동작구":"11590","관악구":"11620","서초구":"11650","강남구":"11680","송파구":"11710","강동구":"11740"}
ELECTIONS = {"20260603": (2025, 6), "20121219": (2011, 12), "20170509": (2016, 5), "20220309": (2021, 3), "20240410": (2023, 4)}  # first month of the 12-month window

def _envfile(name):
    f = Path(__file__).resolve().parent.parent / ".env"
    if f.exists():
        for line in open(f, encoding="utf-8"):
            if line.startswith(name + "="): return line.split("=", 1)[1].strip().strip("'\"")
KEY = os.environ.get("DATA_GO_KR_KEY") or _envfile("DATA_GO_KR_KEY") or sys.exit("Set the DATA_GO_KR_KEY environment variable or add it to the repository's .env")
if "인증키" in KEY or "service key" in KEY or KEY.startswith("<"): sys.exit("DATA_GO_KR_KEY still holds placeholder text; set it to the actual service key")
DATA = Path(__file__).resolve().parent.parent / "data"
RAW = DATA / "raw" / "molit" / "apt_raw"; RAW.mkdir(parents=True, exist_ok=True)

def months(y, m, n=12):
    for _ in range(n):
        yield f"{y}{m:02d}"
        m += 1
        if m == 13: y, m = y + 1, 1

def call(lawd, ym, page):
    q = urllib.parse.urlencode({"serviceKey": KEY, "LAWD_CD": lawd, "DEAL_YMD": ym, "pageNo": page, "numOfRows": 1000})
    req = urllib.request.Request(f"{URL}?{q}", headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
            break
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8','ignore')[:300]}")
        except Exception as e:
            if attempt == 2: raise
            time.sleep(3)
    root = ET.fromstring(raw)
    code = (root.findtext(".//resultCode") or "").strip()
    if code not in ("00", "000", "INFO-00", ""):
        msg = root.findtext(".//resultMsg") or root.findtext(".//returnAuthMsg") or raw[:300]
        raise RuntimeError(f"API error {code}: {msg}")
    items = [{c.tag: (c.text or "").strip() for c in it} for it in root.iter("item")]
    total = int(root.findtext(".//totalCount") or 0)
    return items, total

def fetch_month(lawd, ym):
    f = RAW / f"{lawd}_{ym}.csv"
    if f.exists():
        with open(f, encoding="utf-8") as fh: return list(csv.DictReader(fh))
    rows, page = [], 1
    while True:
        items, total = call(lawd, ym, page)
        rows += items
        if len(rows) >= total or not items: break
        page += 1
    for r in rows: r["lawd_cd"], r["deal_ym"] = lawd, ym
    cols = sorted({k for r in rows for k in r}) or ["lawd_cd", "deal_ym"]
    with open(f, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
    time.sleep(0.1)
    return rows

def run(sg):
    y, m = ELECTIONS[sg]; allrows = []
    for gu, lawd in LAWD.items():
        n = 0
        for ym in months(y, m):
            rows = fetch_month(lawd, ym); n += len(rows); allrows += rows
        print(f"{sg} {gu}: {n} trades")
    cols = sorted({k for r in allrows for k in r})
    out = DATA / "raw" / "molit" / f"seoul_apt_trades_{sg}.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(allrows)
    print("saved:", out, len(allrows), "trades")

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    targets = args or (["20170509", "20220309", "20240410"] + (["20121219"] if "--with-2012" in sys.argv else []))
    for sg in targets:
        try: run(sg)
        except Exception as e:
            print("stopped:", sg, e); print("-> rerun the same command to resume; cached months are skipped."); break
