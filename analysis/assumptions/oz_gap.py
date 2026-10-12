"""Observed reference for the out-of-zone tolerance delta (Section 3.4; Online Appendix Table C21).

For every counting jurisdiction, the conservative valid-vote share among its out-of-zone early ballots minus the share among
its in-zone early-station ballots: the gap between the two groups of early voters that delta bounds dong by dong. Also the
dispersion of in-zone station shares around their jurisdiction's in-zone share, an observable analogue of how far
neighborhoods within a district depart from a district-wide pattern. Neither validates delta: it bounds each dong's
residents, whose out-of-zone composition is not observed.
Output: results/oz_gap.csv (one row per election and jurisdiction)"""
import numpy as np
import pandas as pd
from vwn.data import setup
from vwn.lp import KMS, INV
from vwn.paths import RES

if __name__ == "__main__":
    rows = []
    for sg in ["20170509", "20220309", "20240410", "20250603", "20260603"]:
        units, G, idx, x, labs = setup(sg)
        for u in units:
            g = G[u][0]; B = g["Bc"]; K = g["K"]
            s_out = B[KMS] / (B.sum() - B[INV]); s_in = K[:, KMS].sum() / (K.sum() - K[:, INV].sum())
            st = K[:, KMS] / (K.sum(1) - K[:, INV])
            rows.append(dict(sg=sg, unit=u, out_share=s_out, in_share=s_in, gap=s_out - s_in, n_stations=len(st),
                             station_dev_median=float(np.median(np.abs(st - s_in))), station_dev_max=float(np.max(np.abs(st - s_in)))))
    pd.DataFrame(rows).to_csv(f"{RES}/oz_gap.csv", index=False)
    d = pd.DataFrame(rows); d["absgap"] = d.gap.abs()
    print(d.groupby("sg").agg(median=("gap", "median"), min=("gap", "min"), max=("gap", "max"), absmax=("absgap", "max")).mul(100).round(1))
