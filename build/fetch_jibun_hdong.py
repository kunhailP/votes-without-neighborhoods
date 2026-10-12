"""Map trade lot numbers (jibun) to administrative dongs via the road-name address service (juso, business.juso.go.kr).
Usage:
    export JUSO_KEY='<juso address search API key (confmKey)>'   # or put JUSO_KEY=... in the repository's .env
    python3 fetch_jibun_hdong.py --test     # query one lot and print the full response (check that hemdNm is present)
    python3 fetch_jibun_hdong.py            # query every unique lot in the trade files
- Input:  data/raw/molit/seoul_apt_trades_<sgId>.csv for 20121219, 20170509, 20220309, 20240410, 20260603 (those present)
- Cache:  data/raw/juso/juso_cache.jsonl (rerun to resume after an interruption)
- Output: data/raw/juso/seoul_jibun_to_hdong_juso.csv
          (sggCd, umdCd, umdNm, bonbun, bubun, landCd, hemdNm, admCd, bdMgtSn, match, n_res)
Standard library only."""
import os, sys, csv, json, time, urllib.parse, urllib.request, urllib.error
from pathlib import Path

URL = "https://business.juso.go.kr/addrlink/addrLinkApi.do"
GU = {"11110":"종로구","11140":"중구","11170":"용산구","11200":"성동구","11215":"광진구","11230":"동대문구","11260":"중랑구",
      "11290":"성북구","11305":"강북구","11320":"도봉구","11350":"노원구","11380":"은평구","11410":"서대문구","11440":"마포구",
      "11470":"양천구","11500":"강서구","11530":"구로구","11545":"금천구","11560":"영등포구","11590":"동작구","11620":"관악구",
      "11650":"서초구","11680":"강남구","11710":"송파구","11740":"강동구"}
def _envfile(name):
    f = Path(__file__).resolve().parent.parent / ".env"
    if f.exists():
        for line in open(f, encoding="utf-8"):
            if line.startswith(name + "="): return line.split("=", 1)[1].strip()
KEY = os.environ.get("JUSO_KEY") or _envfile("JUSO_KEY") or sys.exit("Set the JUSO_KEY environment variable or add it to the repository's .env")
DATA = Path(__file__).resolve().parent.parent / "data"
CACHE = DATA / "raw" / "juso" / "juso_cache.jsonl"

def jibuns():
    seen = {}
    for sg in ["20121219", "20170509", "20220309", "20240410", "20260603"]:
        f = DATA / "raw" / "molit" / f"seoul_apt_trades_{sg}.csv"
        if not f.exists(): continue
        with open(f, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                try: b, s = int(r["bonbun"] or 0), int(r["bubun"] or 0)
                except ValueError: continue
                if b == 0: continue
                k = (r["sggCd"], r["umdCd"], r["umdNm"], b, s, r.get("landCd") or "1")
                seen[k] = 1
    return list(seen)

def query(keyword):
    q = urllib.parse.urlencode({"confmKey": KEY, "currentPage": 1, "countPerPage": 20, "keyword": keyword,
                                "resultType": "json", "hstryYn": "N", "firstSort": "location", "addInfoYn": "Y"})
    req = urllib.request.Request(f"{URL}?{q}", headers={"User-Agent": "Mozilla/5.0"})
    for a in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                j = json.loads(r.read().decode("utf-8"))
            break
        except Exception as e:
            if a == 2: raise
            time.sleep(2)
    c = j["results"]["common"]
    if c.get("errorCode") != "0": raise RuntimeError(f"API error {c.get('errorCode')}: {c.get('errorMessage')}")
    return j["results"].get("juso") or []

def pick(res, sgg, umd, b, s, mt):
    adm = f"{sgg}{umd}"
    for x in res:
        if x.get("admCd") == adm and int(x.get("lnbrMnnm") or -1) == b and int(x.get("lnbrSlno") or 0) == s \
           and (x.get("mtYn", "0") == ("1" if mt == "2" else "0")):
            return x, "exact"
    for x in res:
        if x.get("admCd") == adm and int(x.get("lnbrMnnm") or -1) == b:
            return x, "same_bonbun"
    return None, "none"

def main():
    keys = jibuns()
    if not keys: sys.exit("no trade files found")
    if "--test" in sys.argv:
        sgg, umd, nm, b, s, mt = keys[0]
        kw = f"서울특별시 {GU.get(sgg, '')} {nm} {b}" + (f"-{s}" if s else "")
        res = query(kw); print("query:", kw); print(json.dumps(res[:1], ensure_ascii=False, indent=1))
        print("\n-> if the result has an 'hemdNm' (administrative dong) field, run without --test."); return
    done = {}
    if CACHE.exists():
        for line in open(CACHE, encoding="utf-8"):
            d = json.loads(line); done[tuple(d["key"])] = d
    print(f"{len(keys)} unique lots, {len(done)} cached")
    with open(CACHE, "a", encoding="utf-8") as cf:
        for i, k in enumerate(keys):
            kk = [k[0], k[1], k[2], k[3], k[4], k[5]]
            if tuple(kk) in done: continue
            sgg, umd, nm, b, s, mt = k
            kw = f"서울특별시 {GU.get(sgg, '')} {nm} {'산 ' if mt == '2' else ''}{b}" + (f"-{s}" if s else "")
            try: res = query(kw)
            except Exception as e:
                print("stopped:", e, "-> rerun to resume"); break
            x, how = pick(res, sgg, umd, b, s, mt)
            d = {"key": kk, "hemdNm": (x or {}).get("hemdNm", ""), "admCd": (x or {}).get("admCd", ""),
                 "bdMgtSn": (x or {}).get("bdMgtSn", ""), "match": how, "n_res": len(res)}
            cf.write(json.dumps(d, ensure_ascii=False) + "\n"); done[tuple(kk)] = d
            if (i + 1) % 200 == 0: print(f"{i+1}/{len(keys)}"); cf.flush()
            time.sleep(0.05)
    out = DATA / "raw" / "juso" / "seoul_jibun_to_hdong_juso.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["sggCd", "umdCd", "umdNm", "bonbun", "bubun", "landCd", "hemdNm", "admCd", "bdMgtSn", "match", "n_res"])
        for d in done.values(): w.writerow(d["key"] + [d["hemdNm"], d["admCd"], d["bdMgtSn"], d["match"], d["n_res"]])
    from collections import Counter
    print("saved:", out, Counter(d["match"] for d in done.values()), "blank dong:", sum(1 for d in done.values() if not d["hemdNm"]))

if __name__ == "__main__": main()
