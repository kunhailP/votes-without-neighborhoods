"""2024 legislative election (constituency races) -> constituency-level analysis file.
Column 'gu' holds the constituency name: out-of-zone early, at-home and overseas ballots are reported as
constituency totals, so the constituency is the counting jurisdiction for the LP.
Slots: LJM = Democratic Party (더불어민주당), KMS = People Power Party (국민의힘), LJS = Reform Party (개혁신당),
KYG = New Future Party (새로운미래), SJH = all others. 국외부재자투표 (overseas absentee) goes to the '재외투표' slot.
Electorate: certified electorate per dong from the NEC API, joined on dong name (only 신사동, which exists in both
강남구 and 관악구, is resolved by constituency). The excess of the API electorate over the electorate in the returns
(presumably overseas voters not eligible for the constituency race) is added to U for each constituency."""
import pandas as pd, numpy as np
from pathlib import Path
D = Path(__file__).resolve().parent.parent / "data"
x = pd.read_csv(D / "raw" / "nec" / "중앙선거관리위원회_국회의원선거 개표결과_20240410.csv", encoding="cp949")
x.columns = ["sd","sgg","emd","tpg","c","v"]; x["v"] = pd.to_numeric(x.v.astype(str).str.replace(",", ""), errors="coerce").fillna(0)
s = x[(x.sd == "서울특별시") & (x.emd != "잘못 투입·구분된 투표지")].copy()
s["emd"] = s.emd.replace({"국외부재자투표": "재외투표"})
P = {"더불어민주당": "LJM", "국민의힘": "KMS", "개혁신당": "LJS", "새로운미래": "KYG"}
def lab(c):
    if c == "선거인수": return "elig"
    if c == "투표수": return "votes"
    if c.startswith("무효"): return "invalid"
    if c.startswith("기권"): return "abstain"
    return P.get(c.split()[0], "SJH")
s["col"] = s.c.map(lab); s["unit"] = s.tpg.map(lambda t: "X" if pd.isna(t) else ("IN" if t == "관내사전투표" else "DAY"))
p = s.pivot_table(index=["sgg","emd","unit"], columns="col", values="v", aggfunc="sum").reset_index().rename(columns={"sgg": "gu"})
cols = ["gu","emd","unit","elig","votes","LJM","KMS","LJS","KYG","SJH","invalid","abstain"]
p = p[cols].fillna(0); p[cols[3:]] = p[cols[3:]].astype(int)
# join API electorate
e = pd.read_csv(D / "seoul_20240410_electorate_api.csv"); e = e[e.emd != "합계"]
dong_sgg = p[p.unit == "DAY"][["gu","emd"]].rename(columns={"gu": "sgg"})
g22 = pd.read_csv(D / "seoul_20220309_emd.csv"); g22 = g22[g22.unit == "DAY"][["gu","emd"]].rename(columns={"gu": "realgu"})
dong_sgg = dong_sgg.merge(g22, on="emd", how="left")
# 신사동: 강남구 vs 관악구
amb = dong_sgg.emd.duplicated(keep=False)
dong_sgg.loc[amb & dong_sgg.sgg.str.startswith("강남"), "realgu"] = "강남구"; dong_sgg.loc[amb & dong_sgg.sgg.str.startswith("관악"), "realgu"] = "관악구"
dong_sgg = dong_sgg.drop_duplicates(["sgg","emd"])
dong_sgg.loc[dong_sgg.realgu.isna(), "realgu"] = dong_sgg.sgg.str.extract(r"^(.+?구)")[0]
print("dongs with unknown gu:", dong_sgg[dong_sgg.realgu.isna()].emd.tolist())
eu = e[~e.emd.duplicated(keep=False)].set_index("emd").cfmtnElcnt
ed = e[e.emd.duplicated(keep=False)]
def getE(r):
    if r.emd in eu.index: return eu[r.emd]
    m = ed[(ed.emd == r.emd) & (ed.gu == r.realgu)]
    return m.cfmtnElcnt.iloc[0] if len(m) == 1 else np.nan
dong_sgg["cfmtnElcnt"] = dong_sgg.apply(getE, axis=1)
print("E not joined:", dong_sgg[dong_sgg.cfmtnElcnt.isna()].emd.tolist())
# excess electorate per constituency -> U (added to abstain on the out-of-zone row, which the loader reads as U)
filesum = p.groupby("gu").elig.sum(); apisum = dong_sgg.groupby("sgg").cfmtnElcnt.sum()
extra = (apisum - filesum).rename("extra"); print("excess electorate, sum over constituencies:", extra.sum(), " min/max:", extra.min(), extra.max())
for g, v in extra.items():
    i = p[(p.gu == g) & (p.emd == "관외사전투표")].index[0]; p.loc[i, "abstain"] += int(v)
p.to_csv(D / "seoul_20240410_emd.csv", index=False)
out = dong_sgg.rename(columns={"sgg": "gu"})[["gu","emd","realgu","cfmtnElcnt"]]
tot = out.groupby("gu").cfmtnElcnt.sum().reset_index().assign(emd="합계")
pd.concat([tot, out]).to_csv(D / "seoul_20240410_electorate_bysgg.csv", index=False)
print(p.unit.value_counts().to_dict(), "constituencies", p.gu.nunique())
