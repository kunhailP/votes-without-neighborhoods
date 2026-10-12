"""Resolution experiment (supplementary results, docs/supplementary_results.md): pooled totals of several gu are merged into
one equality per category (a relaxation, so Lambda can only expand; Proposition 3) while movement between
stations stays within each original gu (and, in 2026, within each council constituency). Candidates, electorates and prices are unchanged, so only the counting rule varies.
Output: results/resolution_<sg>.csv"""
import numpy as np
import pandas as pd
from vwn.run import Prep, timer, elections_from_argv
from vwn.lp import JointLP, KMS
from vwn.bounds import bounds_with_w
from vwn.paths import RES


def merged(G, grp):
    gs = [G[u][0] for u in grp]; Es = [G[u][1] for u in grp]
    g = dict(emds=sum([x["emds"] for x in gs], []), A=np.vstack([x["A"] for x in gs]), K=np.vstack([x["K"] for x in gs]),
             Avotes=np.concatenate([x["Avotes"] for x in gs]), D=np.concatenate([x["D"] for x in gs]),
             Bc=sum(x["Bc"] for x in gs), Gc=sum(x["Gc"] for x in gs), U=sum(x["U"] for x in gs),
             a_tilde=np.vstack([x["a_tilde"] for x in gs]))
    # zone label = (original unit, council constituency if any): movement never crosses an original unit
    zl = np.concatenate([[f"{k}|{z}" for z in (x["zone"] if "zone" in x else [0] * len(x["emds"]))] for k, x in enumerate(gs)])
    g["zone"] = zl; g["allow"] = zl[:, None] == zl[None, :]
    return JointLP(g, np.concatenate(Es))


if __name__ == "__main__":
    for sg in elections_from_argv():
        log = timer(); P = Prep(sg); units = P.units; rows = []
        schemes = {"gu": [[u] for u in units], "pairs": [units[i:i + 2] for i in range(0, len(units), 2)],
                   "five": [units[i:i + 5] for i in range(0, len(units), 5)], "seoul": [units]}
        for spec in ["pooled", "guFE"]:
            for name, groups in schemes.items():
                lps = [(merged(P.G, grp), np.concatenate([P.W[spec][u] for u in grp])) for grp in groups]
                for eta, dl in [(0.0, 1.0), (0.05, 1.0), (1.0, 1.0)]:
                    lo = hi = 0.0; ok = True
                    for lp, ww in lps:
                        bb = bounds_with_w(lp, ww, KMS, eta, dl)
                        if bb is None: ok = False; break
                        lo += bb[0]; hi += bb[1]
                    rows.append(dict(sg=sg, spec=spec, scheme=name, n_pools=len(groups), eta=eta, delta=dl,
                                     lo=lo if ok else np.nan, hi=hi if ok else np.nan))
                log(sg, spec, name)
        pd.DataFrame(rows).to_csv(f"{RES}/resolution_{sg}.csv", index=False)
