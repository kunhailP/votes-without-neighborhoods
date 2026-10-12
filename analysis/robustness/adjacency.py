"""Movement restricted by geography (supplementary results, docs/supplementary_results.md): in-zone early ballots cast only at the
station of the voter's own dong or of an adjacent dong (shared boundary), within the statutory zone.
Output: results/adjacency_bounds.csv"""
import numpy as np
import pandas as pd
from vwn.run import Prep, timer
from vwn.data import norm
from vwn.bounds import total
from vwn.paths import DATA, RES

rows = []; log = timer()
for sg in ["20170509", "20220309", "20240410", "20250603", "20260603"]:
    P = Prep(sg); adj = pd.read_csv(f"{DATA}/adjacency_{sg}.csv"); pairs = set()
    for r in adj.itertuples(): pairs |= {(norm(r.emd_a), norm(r.emd_b)), (norm(r.emd_b), norm(r.emd_a))}
    for geo in ["anywhere in zone", "adjacent dongs only"]:
        LP = P.lps()
        if geo != "anywhere in zone":
            for u in P.units:
                lp = LP[u]; em = [norm(e) for e in lp.g["emds"]]; n = len(em)
                A1 = np.array([[i == j or (em[i], em[j]) in pairs for j in range(n)] for i in range(n)])
                lp.allow = A1 if lp.allow is None else (A1 & lp.allow)
        for eta in [0.1, 0.2, 0.3, 1.0]:
            for dl in [0.1, 1.0]:
                for sp in P.W:
                    lo, hi = total(P.units, LP, P.W[sp], eta, dl); rows.append(dict(sg=sg, movement=geo, eta=eta, delta=dl, spec=sp, lo=lo, hi=hi))
    log(sg); pd.DataFrame(rows).to_csv(f"{RES}/adjacency_bounds.csv", index=False)
