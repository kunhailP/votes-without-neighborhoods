"""2026 in-district zones and council-contest headcounts from the NEC Election Statistics System (info.nec.go.kr).

(1) Table of gu council constituencies and their dongs ("선거구 및 읍면동현황", statement BIGI05_6) -> data/council_20260603.csv
(2) Gu council returns by constituency ("개표단위별 개표결과", VCCP08, electionCode 6): out-of-district early and at-home
    voters per contested constituency -> data/council_pooled_20260603.csv
Raw HTML responses are saved under data/raw/nec/council_2026/. Standard library only.
Usage: python build/fetch_council_2026.py [--offline]   (--offline re-parses the saved HTML)"""
import csv
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "nec" / "council_2026"; RAW.mkdir(parents=True, exist_ok=True)
BASE = "https://info.nec.go.kr"; EID = "0020260603"
OFFLINE = "--offline" in sys.argv


def fetch(path, data=None, name=None):
    f = RAW / name if name else None
    if f is not None and f.exists() and (OFFLINE or f.stat().st_size > 0):
        return f.read_text(encoding="utf-8", errors="ignore")
    if OFFLINE: sys.exit(f"missing {f}")
    req = urllib.request.Request(BASE + path, data=urllib.parse.urlencode(data).encode() if data else None, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=90) as r: txt = r.read().decode("utf-8", errors="ignore")
    if f is not None: f.write_text(txt, encoding="utf-8")
    time.sleep(0.3)
    return txt


def rows(txt):
    out = []
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", txt, re.S):
        out.append([html.unescape(re.sub("<[^>]+>", "", c)).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)])
    return out


def report(statement, uri, extra):
    return dict(electionId=EID, requestURI=uri, topMenuId=extra.pop("top"), secondMenuId=extra["menu"], menuId=extra.pop("menu"), statementId=statement, **extra)


if __name__ == "__main__":
    # (1) constituencies and dongs
    t = fetch("/electioninfo/electionInfo_report.xhtml", report("BIGI05_6", f"/electioninfo/{EID}/bi/bigi05.jsp", dict(top="BI", menu="BIGI05", electionCode=6, cityCode=1100)), "bigi05_6_seoul.html")
    zone = []
    for r in rows(t)[1:]:
        if len(r) < 4: continue
        for d in [x.strip() for x in r[3].split(",") if x.strip()]:
            zone.append(dict(gu=r[0], emd=d, council=r[1], seats=int(r[2])))
    with open(ROOT / "data" / "council_20260603.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["gu", "emd", "council", "seats"]); w.writeheader(); w.writerows(zone)
    print("dongs", len(zone), "constituencies", len({z["council"] for z in zone}))
    # (2) council returns by constituency
    towns = json.loads(fetch(f"/bizcommon/selectbox/selectbox_townCodeJson.json?electionId={EID}&cityCode=1100", name="towns.json"))["jsonResult"]["body"]
    pooled = []; stations = []
    for tw in towns:
        sggs = json.loads(fetch(f"/bizcommon/selectbox/selectbox_getSggTownCodeJson.json?electionId={EID}&electionCode=6&townCode={tw['CODE']}", name=f"sgg_{tw['CODE']}.json"))["jsonResult"]["body"]
        for s in sggs:
            txt = fetch("/electioninfo/electionInfo_report.xhtml", report("VCCP08_#00", f"/electioninfo/{EID}/vc/vccp08.jsp",
                        dict(top="VC", menu="VCCP08", electionCode=6, cityCode=1100, sggCityCode=-1, townCodeFromSgg=-1, townCode=tw["CODE"], sggTownCode=s["CODE"])), f"{s['CODE']}.html")
            rec = dict(gu=tw["NAME"], council=s["NAME"], council_code=s["CODE"], out_elig="", out_votes="", home_elig="", home_votes="")
            for r in rows(txt):
                if len(r) >= 4 and r[1] == "관내사전투표":
                    stations.append(dict(gu=tw["NAME"], council=s["NAME"], emd=r[0], indistrict_early_voters=int(r[2].replace(",", ""))))
                if len(r) >= 4 and r[0] in ("관외사전투표", "거소투표"):
                    k = "out" if r[0] == "관외사전투표" else "home"
                    rec[f"{k}_elig"] = int(r[2].replace(",", "")); rec[f"{k}_votes"] = int(r[3].replace(",", ""))
            pooled.append(rec)
    with open(ROOT / "data" / "council_pooled_20260603.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(pooled[0])); w.writeheader(); w.writerows(pooled)
    with open(ROOT / "data" / "council_stations_20260603.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(stations[0])); w.writeheader(); w.writerows(stations)
    print("constituencies", len(pooled), "contested", sum(1 for p in pooled if p["out_elig"] != ""))
