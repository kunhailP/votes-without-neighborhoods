"""2026 Seoul mayoral election: NEC Election Statistics System xlsx "개표단위별 개표결과" (returns by counting unit),
one file per gu -> data/seoul_20260603_emd.csv, in the same format as the other *_emd.csv files.
Slots: LJM = Democratic Party (더불어민주당), KMS = People Power Party (국민의힘), LJS = Reform Party (개혁신당),
KYG = 0 (unused), SJH = all others. Local elections have no overseas voting, so the '재외투표' row is all zeros."""
import glob, re, unicodedata, sys, os
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__)); from parse_nec_xlsx import read_xlsx
D = os.path.join(os.path.dirname(__file__), "..", "data")
P = {"더불어민주당": "LJM", "국민의힘": "KMS", "개혁신당": "LJS"}
num = lambda v: int(str(v).replace(",", "")) if v not in (None, "") else 0
out = []; seen = set()
for f in sorted(glob.glob(f"{D}/raw/nec/2026_mayor_xlsx/*.xlsx")):
    rows = read_xlsx(f); title = " ".join(str(c) for r in rows[:5] for c in r if c)
    gu = re.search(r"\[서울특별시\]\[(.+?)\]", unicodedata.normalize("NFC", title)).group(1)
    if gu in seen: continue
    seen.add(gu)
    hi = next(i for i, r in enumerate(rows) if r and r[0] == "읍면동명")
    cand = [c for c in rows[hi + 1] if c]            # candidate-name row (last cell is the '계' total)
    names = cand[:-1] if cand[-1] == "계" else cand
    for r in rows[hi + 2:]:
        if not r or not r[0] or r[0] == "합계": continue
        emd, kind = r[0], (r[1] or "").strip()
        vals = [num(v) for v in r[2:]]
        elig, votes = vals[0], vals[1]; cv = vals[2:2 + len(names)]; inval, abst = vals[2 + len(names) + 1], vals[2 + len(names) + 2]
        rec = dict(gu=gu, elig=elig, votes=votes, LJM=0, KMS=0, LJS=0, KYG=0, SJH=0, invalid=inval, abstain=abst)
        for nm, v in zip(names, cv): rec[P.get(nm.split()[0], "SJH")] += v
        if kind == "": unit = "X"; emd = {"거소투표": "거소·선상투표"}.get(emd, emd)
        elif kind == "관내사전투표": unit = "IN"
        elif kind == "선거일투표": unit = "DAY"
        else: continue                               # skip '계' (total) rows
        out.append(dict(emd=emd, unit=unit, **rec))
    out.append(dict(gu=gu, emd="재외투표", unit="X", elig=0, votes=0, LJM=0, KMS=0, LJS=0, KYG=0, SJH=0, invalid=0, abstain=0))
p = pd.DataFrame(out)[["gu","emd","unit","elig","votes","LJM","KMS","LJS","KYG","SJH","invalid","abstain"]]
chk = (p[["LJM","KMS","LJS","KYG","SJH","invalid"]].sum(1) - p.votes).abs().max()
p.to_csv(f"{D}/seoul_20260603_emd.csv", index=False)
print("gu", p.gu.nunique(), sorted(set(["종로구","중구","용산구","성동구","광진구","동대문구","중랑구","성북구","강북구","도봉구","노원구","은평구","서대문구","마포구","양천구","강서구","구로구","금천구","영등포구","동작구","관악구","서초구","강남구","송파구","강동구"]) - set(p.gu)), "missing")
print(p.unit.value_counts().to_dict(), "max |row vote sum - votes|", chk)
print(p[p.gu=="관악구"].head(6).to_string())
