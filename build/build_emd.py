"""NEC presidential returns CSV -> Seoul dong-level analysis file (seoul_<sgId>_emd.csv; seoul_2025pres_emd.csv for 2025).
Column slots (the LP code refers to slots by name): LJM = Democratic candidate, KMS = conservative (People Power or
predecessor) candidate, LJS = third, KYG = fourth, SJH = sum of the rest, invalid, abstain.
unit: IN (in-zone early, per dong) / DAY (election-day precincts summed, per dong) /
      X (gu level: out-of-zone early, at-home, overseas)."""
import pandas as pd, sys
from pathlib import Path
D = Path(__file__).resolve().parent.parent / "data"
SLOTS = {
    "20250603": {"LJM": ["더불어민주당 이재명"], "KMS": ["국민의힘 김문수"], "LJS": ["개혁신당 이준석"], "KYG": ["민주노동당 권영국"]},
    "20220309": {"LJM": ["더불어민주당 이재명"], "KMS": ["국민의힘 윤석열"], "LJS": ["정의당 심상정"], "KYG": ["국가혁명당  허경영"]},
    "20121219": {"LJM": ["민주통합당 문재인"], "KMS": ["새누리당 박근혜"], "LJS": ["무소속 강지원"], "KYG": ["무소속 김순자"]},
    "20170509": {"LJM": ["더불어민주당 문재인"], "KMS": ["자유한국당 홍준표"], "LJS": ["국민의당 안철수"], "KYG": ["바른정당 유승민"]},
}
def rd(p):
    for enc in ["utf-8-sig", "cp949"]:
        try: return pd.read_csv(p, encoding=enc)
        except UnicodeDecodeError: pass
def build(sg):
    x = rd(D / "raw" / "nec" / f"중앙선거관리위원회_대통령선거 개표결과_{sg}.csv"); x.columns = ["sd","gu","emd","tpg","c","v"]
    x["v"] = pd.to_numeric(x.v.astype(str).str.replace(",", ""), errors="coerce").fillna(0)
    s = x[x.sd == "서울특별시"].copy()
    s["emd"] = s.emd.replace({"재외투표(공관)": "재외투표"})
    s = s[s.emd != "잘못 투입·구분된 투표지"]
    slot = {c: k for k, cs in SLOTS[sg].items() for c in cs}
    def lab(c):
        if c == "선거인수": return "elig"
        if c == "투표수": return "votes"
        if c.startswith("무효"): return "invalid"
        if c.startswith("기권"): return "abstain"
        return slot.get(c, "SJH")
    s["col"] = s.c.map(lab)
    s["unit"] = s.tpg.map(lambda t: "X" if pd.isna(t) else ("IN" if t == "관내사전투표" else "DAY"))
    p = s.pivot_table(index=["gu","emd","unit"], columns="col", values="v", aggfunc="sum").reset_index()
    cols = ["gu","emd","unit","elig","votes","LJM","KMS","LJS","KYG","SJH","invalid","abstain"]
    p = p[cols]; p[cols[3:]] = p[cols[3:]].astype(int)
    order = {"X": 0, "IN": 1, "DAY": 2}
    p = p.sort_values(["gu","emd","unit"], key=lambda c: c.map(order) if c.name == "unit" else c)
    if sg < "2014":   # before nationwide early voting (2014): domestic absentee ballots go in the out-of-zone slot;
                      # in-zone early (IN) and at-home rows are zero-filled to keep the loader format
        p["emd"] = p.emd.replace({"국내부재자투표": "관외사전투표"})
        z = []
        for gu in p.gu.unique():
            r = p[(p.gu == gu) & (p.unit == "X")].iloc[0].copy(); r["emd"] = "거소·선상투표"; r[cols[3:]] = 0; z.append(r)
            for emd in p[(p.gu == gu) & (p.unit == "DAY")].emd:
                r = r.copy(); r["emd"] = emd; r["unit"] = "IN"; z.append(r)
        p = pd.concat([p, pd.DataFrame(z)]).sort_values(["gu","emd","unit"], key=lambda c: c.map(order) if c.name == "unit" else c)
    out = D / (f"seoul_{sg}_emd.csv" if sg != "20250603" else "seoul_2025pres_emd.csv")
    p.to_csv(out, index=False); return p, out
if __name__ == "__main__":
    for sg in sys.argv[1:] or ["20220309"]:
        p, out = build(sg); print(sg, out.name, p.unit.value_counts().to_dict())
