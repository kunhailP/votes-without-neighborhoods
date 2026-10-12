"""Seoul dong adjacency lists and simplified map boundaries from administrative-dong boundaries (vuski/admdongkor, public GeoJSON).
Output: data/adjacency_<sg>.csv (gu, emd_a, emd_b, shared_m; within-gu pairs whose shared boundary is longer than 1 m),
        data/seoul_dong_ver20260401.geojson (simplified boundaries for maps)"""
import geopandas as gp, pandas as pd, numpy as np, os, sys
D = os.path.join(os.path.dirname(__file__), "..", "data"); SRC = os.environ.get("ADMDONGKOR", "admdongkor")   # local clone of https://github.com/vuski/admdongkor
VER = {"20260603": "ver20260401/HangJeongDong_ver20260401.geojson", "20250603": "ver20250401/HangJeongDong_ver20250401.geojson",
       "20240410": "ver20240401/HangJeongDong_ver20240401.geojson", "20220309": "ver20220309/HangJeongDong_ver20220309.geojson",
       "20170509": "parquet/emd_20170418.parquet"}
norm = lambda s: s.replace("제", "").replace(".", "·")
for sg, f in VER.items():
    p = f"{SRC}/{f}"
    if not os.path.exists(p): print("missing", sg); continue
    g = gp.read_parquet(p) if p.endswith("parquet") else gp.read_file(p)
    if "sidonm" in g: g = g[g.sidonm == "서울특별시"].copy()
    else: g = g[g.iloc[:, 0].astype(str).str.contains("서울")].copy()
    if "adm_nm" in g:
        g["gu"] = g["adm_nm"].str.split().str[1]; g["emd"] = g["adm_nm"].str.split().str[2]
    else:  # parquet edition: emdnm/sggnm columns
        g["gu"] = g["sggnm"]; g["emd"] = g["emdnm"]
    g = g.to_crs(5179); rows = []
    for gu, s in g.groupby("gu"):
        s = s.reset_index(drop=True)
        for a in range(len(s)):
            for b in range(a + 1, len(s)):
                inter = s.geometry[a].intersection(s.geometry[b])
                if inter.length > 1.0: rows.append(dict(gu=gu, emd_a=s.emd[a], emd_b=s.emd[b], shared_m=round(inter.length, 1)))
    pd.DataFrame(rows).to_csv(f"{D}/adjacency_{sg}.csv", index=False)
    if sg == "20260603":
        m = g[["gu", "emd", "geometry"]].copy(); m["geometry"] = m.geometry.simplify(25); m.to_crs(4326).to_file(f"{D}/seoul_dong_ver20260401.geojson", driver="GeoJSON")
    print(sg, len(g), "dongs,", len(rows), "adjacent pairs", flush=True)
