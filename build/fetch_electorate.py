"""NEC electorate by dong (getEmdElcntInfoInqire): Seoul's 25 gu x selected elections.
Usage:
    export DATA_GO_KR_KEY='<data.go.kr general service key (Decoding)>'   # or put it in the repository's .env
    python3 fetch_electorate.py            # default: 2022 presidential, 2024 legislative, 2012 presidential
    python3 fetch_electorate.py 20220309   # selected elections only
Output: data/seoul_<sgId>_electorate_api.csv  (gu, emd + all API fields)
Standard library only."""
import os, sys, json, csv, time, urllib.parse, urllib.request, urllib.error
from pathlib import Path
URLS = ["https://apis.data.go.kr/9760000/ElcntInfoInqireService/getEmdElcntInfoInqire",
        "http://apis.data.go.kr/9760000/ElcntInfoInqireService/getEmdElcntInfoInqire"]
URL = os.environ.get("VWN_API_URL") or URLS[0]
GUS = ["종로구","중구","용산구","성동구","광진구","동대문구","중랑구","성북구","강북구","도봉구","노원구","은평구",
       "서대문구","마포구","양천구","강서구","구로구","금천구","영등포구","동작구","관악구","서초구","강남구","송파구","강동구"]
def _envfile(name):
    f = Path(__file__).resolve().parent.parent / ".env"
    if f.exists():
        for line in open(f, encoding="utf-8"):
            if line.startswith(name + "="): return line.split("=", 1)[1].strip().strip("'\"")
KEY = os.environ.get("DATA_GO_KR_KEY") or _envfile("DATA_GO_KR_KEY") or sys.exit("Set the DATA_GO_KR_KEY environment variable or add it to the repository's .env")
if len(KEY) == 63: print("warning: the key is 63 characters; keys are usually 64, so one may have been lost in copying")
if "인증키" in KEY or "service key" in KEY or KEY.startswith("<"): sys.exit("DATA_GO_KR_KEY still holds placeholder text; set it to the actual service key")
OUT = Path(__file__).resolve().parent.parent / "data"   # also copied to data/raw/nec/

def get(sgId, gu, page):
    q = urllib.parse.urlencode({"serviceKey": KEY, "pageNo": page, "numOfRows": 100, "resultType": "json",
                                "sgId": sgId, "sdName": "서울특별시", "wiwName": gu})
    req = urllib.request.Request(f"{URL}?{q}", headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8','ignore')[:300]}")
    try:
        j = json.loads(raw)
    except json.JSONDecodeError:
        raise RuntimeError(f"not JSON (invalid key or election not served by the API?): {raw[:300]}")
    body = j.get("response", j).get("body", {})
    head = j.get("response", j).get("header", {})
    if head.get("resultCode") not in ("INFO-00", "00", None):
        raise RuntimeError(f"{sgId} {gu}: {head}")
    items = body.get("items", {}) or {}
    items = items.get("item", items) if isinstance(items, dict) else items
    if isinstance(items, dict): items = [items]
    return items or [], int(body.get("totalCount", 0) or 0)

def run(sgId):
    rows = []
    for gu in GUS:
        page, got = 1, []
        while True:
            items, total = get(sgId, gu, page)
            got += items
            if len(got) >= total or not items: break
            page += 1
        for it in got: it["gu"] = gu; it["emd"] = it.get("emdName", "")
        rows += got
        print(f"{sgId} {gu}: {len(got)} rows"); time.sleep(0.1)
    if not rows: print(f"{sgId}: no results (the API may not serve this election)"); return
    cols = ["gu", "emd"] + sorted({k for r in rows for k in r} - {"gu", "emd"})
    p = OUT / f"seoul_{sgId}_electorate_api.csv"
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print("saved:", p)

if __name__ == "__main__":
    for s in (sys.argv[1:] or ["20220309", "20240410", "20121219"]):
        try: run(s)
        except Exception as e: print("failed:", s, e)
