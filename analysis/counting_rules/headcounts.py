"""Pooled headcounts, at-home ballots, gu-specific bands (supplementary results, docs/supplementary_results.md) and the 2026
zones and cross-contest information (Sections 3.1, 4.4 and 4.5; Table 4; Online Appendix Table C27).

Part 1 (calibrated movement, delta = 0.1 unless stated):
  H1  each dong's out-of-zone early headcount within [0.5, 2] x jurisdiction rate x removed residents
  H2  H1 + at-home/overseas composition (election day + jurisdiction gap, +-0.10) and headcount <= 3 x rate
  G   gu-specific out-of-zone band delta_g = delta_min,g + 0.05 / + 0.10
Part 2 (2026 only): sets with (a) no zone restriction (movement anywhere in the gu), (b) the
statutory zones (main), (c) zones plus the council contest's published out-of-zone and at-home
headcounts by constituency.
Outputs: results/headcount_bands.csv, results/zones_2026.csv"""
import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix, vstack
from vwn.run import Prep, timer
from vwn.lp import JointLP
from vwn.bounds import total
from vwn.paths import RES


class HLP(JointLP):
    hc = None; dg = None

    def constraints(self, eta, delta):
        Aeq, beq, Aub, bub = super().constraints(eta, self.dg if self.dg is not None else delta)
        if self.hc is None: return Aeq, beq, Aub, bub
        g = self.g; n, C = self.n, self.C; ED = self.E - g["D"]; rP = g["Bc"].sum() / ED.sum(); rQ = g["Gc"].sum() / ED.sum()
        rows, b = [], []
        for i in range(n):
            rows.append({self.iB(i, c): 1.0 for c in range(C)}); b.append(2.0 * rP * ED[i])
            rows.append({self.iB(i, c): -1.0 for c in range(C)}); b.append(-0.5 * rP * ED[i])
        if self.hc == "H2":
            A = g["A"]; day = A / np.maximum(A.sum(1, keepdims=True), 1)
            ref = np.clip(day + g["Gc"] / max(g["Gc"].sum(), 1) - A.sum(0) / A.sum(), 0, 1)
            for i in range(n):
                rows.append({self.iG(i, c): 1.0 for c in range(C)}); b.append(3.0 * rQ * ED[i])
                for c in range(C):
                    hi, lo = ref[i, c] + 0.1, max(ref[i, c] - 0.1, 0.0)
                    d1 = {self.iG(i, c2): -hi for c2 in range(C)}; d1[self.iG(i, c)] += 1; rows.append(d1); b.append(0.0)
                    d2 = {self.iG(i, c2): lo for c2 in range(C)}; d2[self.iG(i, c)] -= 1; rows.append(d2); b.append(0.0)
        ri, ci, vi = [], [], []
        for r, d in enumerate(rows):
            ri += [r] * len(d); ci += list(d.keys()); vi += list(d.values())
        X = coo_matrix((vi, (ri, ci)), shape=(len(rows), self.nv)).tocsr()
        return Aeq, beq, vstack([Aub, X]).tocsr(), np.concatenate([bub, b])

    def config_key(self, eta, delta):
        return super().config_key(eta, delta) + (self.hc, self.dg)


if __name__ == "__main__":
    log = timer(); rows = []
    for sg in ["20260603", "20240410", "20220309", "20250603"]:
        P = Prep(sg)
        for s in [None, 0.02, 0.05]:
            LP = P.lps(calib=True, dF=None if s is None else ("slack", s), cls=HLP)
            for hc in [None, "H1", "H2"]:
                for u in P.units: LP[u].hc = hc; LP[u].dg = None
                for sp in P.W:
                    lo, hi = total(P.units, LP, P.W[sp], 1.0, 0.1); rows.append(dict(sg=sg, variant=hc or "baseline", slack=s, spec=sp, lo=lo, hi=hi))
            dmin = {}
            for u in P.units:
                lp = LP[u]; lp.hc = None; lp.dg = 0.0
                if lp.feasible(1.0, 0.0): dmin[u] = 0.0; continue
                a, b = 0.0, 1.0
                while b - a > 1e-3:
                    m = (a + b) / 2; lp.dg = m
                    if lp.feasible(1.0, m): b = m
                    else: a = m
                dmin[u] = b
            rows.append(dict(sg=sg, variant="dmin_summary", slack=s, spec="", lo=np.median(list(dmin.values())), hi=max(dmin.values())))
            for add in [0.05, 0.10]:
                for u in P.units: LP[u].dg = min(1.0, dmin[u] + add)
                for sp in P.W:
                    lo, hi = total(P.units, LP, P.W[sp], 1.0, 0.1); rows.append(dict(sg=sg, variant=f"gu-specific delta: dmin+{add:.2f}", slack=s, spec=sp, lo=lo, hi=hi))
            log(sg, s)
            pd.DataFrame(rows).to_csv(f"{RES}/headcount_bands.csv", index=False)
    # Part 2: 2026 zones and cross-contest headcounts
    rows = []; sg = "20260603"
    for label, zones, hcs in [("no zone restriction", False, False), ("statutory zones (main)", True, False), ("zones + council headcounts", True, True)]:
        P = Prep(sg, zones=zones, headcounts=hcs)
        for cell, calib, eta, delta, s in [("accounting only", False, 1.0, 1.0, None), ("minimum movement, delta=1", False, 0.0, 1.0, None),
                                           ("minimum movement, delta=0.1", False, 0.0, 0.1, None), ("eta=0.1, delta=0.1", False, 0.1, 0.1, None),
                                           ("calibrated, delta=1", True, 1.0, 1.0, None), ("calibrated, delta=0.1", True, 1.0, 0.1, None),
                                           ("calibrated, delta=0.1, s=0.02", True, 1.0, 0.1, 0.02)]:
            LP = P.lps(calib=calib, dF=None if s is None else ("slack", s))
            for sp in P.W:
                lo, hi = total(P.units, LP, P.W[sp], eta, delta); rows.append(dict(sg=sg, variant=label, cell=cell, spec=sp, lo=lo, hi=hi))
        log("zones", label)
        pd.DataFrame(rows).to_csv(f"{RES}/zones_2026.csv", index=False)
