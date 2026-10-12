"""Stream-aggregate Seoul mobility (생활이동, KT) dong-level OD flows, keeping only trips on early-voting weekdays,
in voting hours (arrival 06-17h) and departing from home (type H*).
Reads one hourly file at a time with unzip -p, without extracting the archive
-> data/raw/mobility/od_home_<yyyymm>.csv (origin code, destination code, weekday, flow).
Masked cells '*' (3 or fewer people) are set to 2.
Usage: python build/mobility_extract.py <yyyymm> <weekday,weekday>"""
import sys, subprocess, io, pandas as pd, os, time
ym, days = sys.argv[1], sys.argv[2].split(",")
import pathlib; ROOT = pathlib.Path(__file__).resolve().parent.parent
z = str(ROOT / "data" / "raw" / "mobility" / f"생활이동_행정동_{ym}.zip")   # monthly file from Seoul Open Data Plaza (not redistributed)
out = []; t0 = time.time()
for h in range(6, 18):
    hh = f"{h:02d}"; pat = f"*{ym[:4]}.{ym[4:]}_{hh}*"
    p = subprocess.Popen(["unzip", "-p", z, pat], stdout=subprocess.PIPE)
    for ch in pd.read_csv(p.stdout, chunksize=2_000_000, dtype=str, encoding="cp949"):
        ch.columns = ["ym", "dow", "hour", "o", "d", "sex", "age", "type", "mins", "pop"]
        ch = ch[ch.dow.isin(days) & ch.o.str.startswith("11") & ch.type.str.startswith("H")]
        if len(ch) == 0: continue
        ch["pop"] = pd.to_numeric(ch["pop"].str.replace("*", "2", regex=False), errors="coerce").fillna(0)
        out.append(ch.groupby(["o", "d", "dow"], as_index=False)["pop"].sum())
    p.wait(); print(hh, f"{time.time()-t0:.0f}s", flush=True)
r = pd.concat(out).groupby(["o", "d", "dow"], as_index=False)["pop"].sum()
r.to_csv(ROOT / "data" / "raw" / "mobility" / f"od_home_{ym}.csv", index=False); print("done", len(r), f"{time.time()-t0:.0f}s")
