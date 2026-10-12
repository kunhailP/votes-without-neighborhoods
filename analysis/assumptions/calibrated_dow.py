"""Calibration by early-voting day of the week (supplementary results, docs/supplementary_results.md). Output: results/calibrated_dow.csv"""
import sys
import numpy as np
import pandas as pd
from vwn.run import Prep, timer
from vwn.data import align_calib
from vwn.bounds import total
from vwn.paths import RES, RAW
sys.path.insert(0, str(__import__("vwn.paths", fromlist=["ROOT"]).ROOT / "build"))
import mobility_calibration as mc

rows = []; log = timer(); orig = pd.read_csv
for sg in ["20220309", "20240410", "20250603", "20260603"]:
    full = orig(f"{RAW}/mobility/od_home_{mc.YM[sg]}.csv", dtype={"o": str, "d": str}); P = Prep(sg)
    for dow in sorted(full.dow.unique()):
        sub = full[full.dow == dow]
        mc.pd.read_csv = lambda p, *a, **k: sub.copy() if "od_home_" in str(p) else orig(p, *a, **k)
        try: cal = mc.calibrate(sg, zones=True)
        finally: mc.pd.read_csv = orig
        ev = {u: c.eta_j.values for u, c in align_calib(cal, P.G, P.units).items()}
        P._ev = ev; LP = P.lps(calib=True)
        for sp in ["guFE", "pooled"]:
            for dl in [0.1, 1.0]:
                lo, hi = total(P.units, LP, P.W[sp], 1.0, dl)
                rows.append(dict(sg=sg, dow=dow, spec=sp, delta=dl, eta_med=cal.eta_j.median(), R_med=cal.groupby(["unit", "zone"]).R_zone.first().median(), lo=lo, hi=hi))
        log(sg, dow)
    pd.DataFrame(rows).to_csv(f"{RES}/calibrated_dow.csv", index=False)
