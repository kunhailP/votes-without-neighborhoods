"""MOLIT apartment trades + juso lot-number -> administrative-dong map -> per-election trade files at dong level.
Writes data/trades/trades_hdong_<sgId>.csv (gu, k, hd, p; p = price per m2), the trade-level input to the bootstrap.
With --summaries it also writes dong-level price summaries (median per m2) matched to the election's dong list:
data/seoul_hdong_aptprice_<sgId>.csv and data/aptprice_match_report_<sgId>.csv.
Usage: python build/build_trades.py [--summaries] [sgId ...]   (default: 20170509 20220309 20240410).
The default preserves the frozen price summaries. The current crosswalk gives
small differences in three 2012/2017 medians; price_lineage.py audits their
effect. The original 2025 summary construction is unavailable; a separate snapshot and
alternative reconstruction are documented in data/README.md."""
import pandas as pd, numpy as np
from pathlib import Path
D = Path(__file__).resolve().parent.parent / "data"; DT = D / "trades"; DJ = D / "raw" / "juso"; DM = D / "raw" / "molit"
GU = {"11110":"종로구","11140":"중구","11170":"용산구","11200":"성동구","11215":"광진구","11230":"동대문구","11260":"중랑구",
      "11290":"성북구","11305":"강북구","11320":"도봉구","11350":"노원구","11380":"은평구","11410":"서대문구","11440":"마포구",
      "11470":"양천구","11500":"강서구","11530":"구로구","11545":"금천구","11560":"영등포구","11590":"동작구","11620":"관악구",
      "11650":"서초구","11680":"강남구","11710":"송파구","11740":"강동구"}
norm = lambda s: s.replace("제", "").replace(".", "·") if isinstance(s, str) else s   # '창신제1동'<->'창신1동', '상계3.4동'<->'상계3·4동'
# Crosswalk from current juso dong names to dong names at election time; applied only when the name is not in the election's dong list.
XWALK_ALL = {("동대문구","용두동"):"용신동", ("동대문구","신설동"):"용신동"}
XWALK_PRE2023 = {("강남구","개포3동"):"일원2동"}                      # before the 2023 renaming of 개포3동
XWALK_PRE2014 = {("중구","신당동"):"신당제1동", ("중구","다산동"):"신당제2동", ("중구","약수동"):"신당제3동",
                 ("중구","청구동"):"신당제4동", ("중구","동화동"):"신당제6동"}   # before the 2014 renaming of the 신당 dongs in 중구
XWALK_2017 = {("강동구","상일제1동"):"상일동", ("강동구","상일제2동"):"상일동", ("구로구","항동"):"오류2동"}  # before 상일동 was split

m = pd.read_csv(DJ/"seoul_jibun_to_hdong_juso.csv", dtype=str)
m["hd_raw"] = m.hemdNm.str.split(n=2).str[-1]
m["multi"] = m.hd_raw.str.contains(",", na=False)                     # building spans several dongs: assign the first, flag it
m["hd"] = m.hd_raw.str.split(",").str[0]
m.loc[m.hd.notna(), "hd"] = m.loc[m.hd.notna(), "hd"].str.split().str[-1]
for c in ["bonbun","bubun"]: m[c] = m[c].astype(int)
# Fill unmatched lots: majority dong among other sub-numbers (bubun) with the same (gu, legal dong, main number);
# otherwise the nearest main number (bonbun) in the same legal dong, within 20
ok = m[m.hd.notna()]
fill = {}
for i, r in m[m.hd.isna()].iterrows():
    c = ok[(ok.sggCd==r.sggCd)&(ok.umdCd==r.umdCd)&(ok.bonbun==r.bonbun)]
    if len(c): fill[i] = (c.hd.mode().iloc[0], "nb_bubun"); continue
    c = ok[(ok.sggCd==r.sggCd)&(ok.umdCd==r.umdCd)]
    if len(c):
        c = c.assign(d=(c.bonbun-r.bonbun).abs()); c = c[c.d==c.d.min()]
        if c.d.iloc[0] <= 20: fill[i] = (c.hd.mode().iloc[0], "nb_bonbun")
m["src"] = np.where(m.hd.notna(), m.match, "unmapped")
for i,(h,s) in fill.items(): m.loc[i,"hd"], m.loc[i,"src"] = h, s
print("mapping source:", m.src.value_counts().to_dict())
key = ["sggCd","umdCd","bonbun","bubun"]

import sys
OUT_ONLY = '--summaries' not in sys.argv
for sg in ([arg for arg in sys.argv[1:] if not arg.startswith('--')] or ["20170509","20220309","20240410"]):
    t = pd.read_csv(DM/f"seoul_apt_trades_{sg}.csv", dtype=str)
    n0 = len(t)
    t = t[t.cdealType.fillna("").str.strip()!="O"]                       # drop cancelled trades
    for c in ["bonbun","bubun"]: t[c] = pd.to_numeric(t[c], errors="coerce").fillna(-1).astype(int)
    t = t.merge(m[key+["hd","src"]], on=key, how="left")
    t["p"] = pd.to_numeric(t.dealAmount.str.replace(",",""), errors="coerce") / pd.to_numeric(t.excluUseAr, errors="coerce")
    t["gu"] = t.sggCd.map(GU)
    xw = dict(XWALK_ALL); xw.update(XWALK_PRE2023 if sg < "2023" else {}); xw.update(XWALK_2017 if sg <= "20170509" else {}); xw.update(XWALK_PRE2014 if sg < "2014" else {})
    e_names = pd.read_csv(D/f"seoul_{sg}_electorate_api.csv", dtype=str)
    e_names = set(zip(e_names.gu, e_names.emd.map(norm)))
    t["hd"] = [h if (g, norm(h)) in e_names else xw.get((g, h), h) for g, h in zip(t.gu, t.hd)]   # no crosswalk if the name is in the election-time list
    rep = {"원거래": n0, "해제제외후": len(t), "미매핑거래": int(t.hd.isna().sum())}
    t = t[t.hd.notna() & t.p.notna()]
    t["k"] = t.hd.map(norm)
    t[["gu","k","hd","p"]].to_csv(DT/f"trades_hdong_{sg}.csv", index=False)
    if OUT_ONLY: continue
    g = t.groupby(["gu","k"]).agg(hd=("hd","first"), price_med=("p","median"), price_mean=("p","mean"), n=("p","size"),
                                   n_nb=("src", lambda s: s.str.startswith("nb").sum())).reset_index()
    # match to the election-time dong list
    e = pd.read_csv(D/f"seoul_{sg}_electorate_api.csv", dtype=str); e = e[e.emd!="합계"][["gu","emd"]]
    e["k"] = e.emd.map(norm)
    out = e.merge(g, on=["gu","k"], how="left")
    miss = out.price_med.isna()
    if miss.any():   # the 2024 legislative API groups dongs by constituency rather than gu
                     # (e.g. 성동구 금호·옥수 under '중구'): match on dong name alone if it is unique in Seoul
        gu_ = g.groupby("k").filter(lambda x: len(x) == 1).set_index("k")
        for i in out[miss].index:
            k = out.at[i, "k"]
            if k in gu_.index:
                for c in ["price_med","price_mean","n","n_nb"]: out.at[i, c] = gu_.at[k, c]
                out.at[i, "hd"] = gu_.at[k, "hd"]
    out = out.drop(columns="k")
    unmatched_price = g[~g.hd.isin(out.hd.dropna())]
    out.to_csv(D/f"seoul_hdong_aptprice_{sg}.csv", index=False)
    unmatched_price.to_csv(D/f"aptprice_match_report_{sg}.csv", index=False)
    rep.update({"선거동수": len(e), "가격있는동": int(out.price_med.notna().sum()),
                "가격없는동": out[out.price_med.isna()].emd.tolist(),
                "선거목록에없는매핑동": (unmatched_price.gu+" "+unmatched_price.hd+f"(n="+unmatched_price.n.astype(str)+")").tolist()})
    print(sg, rep)
