"""Additional restriction families and sensitivity analyses (Section 4.5; Online Appendix Tables C17, C11; supplementary results, docs/supplementary_results.md).

mode "anchor": the out-of-zone anchor shifted like the in-zone benchmark.
    station           a_tilde = K_ic / K_i (main specification)
    station+gap       a_tilde = clip(K_ic/K_i + gamma^PK_gc), gamma^PK = out-of-zone minus in-zone early composition (jurisdiction)
    station+gap+price as station+gap, plus (b_P - b_K)(x_i - xbar_g) for the conservative candidate (opposite for the Democratic),
                      b_P, b_K the cross-jurisdiction price slopes of the out-of-zone and in-zone gaps (Online Appendix Table C5)
mode "mover": movers' composition. Residents of i who vote at another station of the zone vote within t of the composition of
    their home station, t in {0.05, 0.1, 0.2, 0.3}; t* = largest t at which the lower bound is positive.
mode "intercept": the calibrated cap r_j + nu (r_rho_j - r_j) + lambda C_j, nu in {0, 0.5, 1}, separating the intercept from the
    mobility-based flow; and the totals of r_j, r_rho_j and C_j.
Output: results/rev_<mode>_<sg>.csv. Usage: revisions.py <mode> <sg>"""
import sys
import numpy as np
import pandas as pd
from vwn.run import Prep, timer
from vwn.data import make_lp
from vwn.bounds import total, breakdown
from vwn.lp import KMS, CANDS
from vwn.paths import RES

LJM = CANDS.index("LJM")


def shifted_G(P, kind, reg):
    """Copy of P.G with the out-of-zone anchor replaced."""
    G2 = {}
    unit_arr = np.array([u for u, _ in P.idx]); xd = np.nan_to_num(P.x - pd.Series(P.x).groupby(unit_arr).transform("mean").values)
    xs = P.wsplit(xd)
    if kind == "station+gap+price":
        q = lambda m: reg[(reg.model == f"{m} {P.sg}") & (reg.term == "x")].coef.iloc[0]
        beta = q("gu gamB x+s60") - q("gu gamK x+s60")
    for u in P.units:
        g, E = P.G[u]; K = g["K"]; k = K / np.maximum(K.sum(1, keepdims=True), 1)
        gap = g["Bc"] / g["Bc"].sum() - K.sum(0) / K.sum()
        at = k + gap
        if kind == "station+gap+price":
            at = at.copy(); at[:, KMS] += beta * xs[u]; at[:, LJM] -= beta * xs[u]
        G2[u] = (dict(g, a_tilde=np.clip(at, 0, 1)), E)
    return G2


def run_anchor(sg):
    log = timer(); P = Prep(sg); rows = []; reg = pd.read_csv(f"{RES}/gap_test_reg.csv")
    calib_ok = sg >= "20220309"
    for kind in ["station", "station+gap", "station+gap+price"]:
        G2 = P.G if kind == "station" else shifted_G(P, kind, reg)
        dm = [make_lp(*G2[u]).delta_min(0.0) for u in P.units]
        rows.append(dict(sg=sg, anchor=kind, cell="dmin_eta0", spec="", lo=float(np.median(dm)), hi=float(np.max(dm))))
        cells = [("eta0", False, 0.0, d, None) for d in [0.05, 0.1, 0.2]]
        if calib_ok: cells += [("calib", True, 1.0, d, s) for d in [0.05, 0.1, 0.2] for s in [None, 0.02, 0.05]]
        for name, calib, eta, dl, s in cells:
            LP = {u: make_lp(*G2[u], ev=P.ev[u] if calib else None, dF=None if s is None else ("slack", s)) for u in P.units}
            for sp in P.W:
                lo, hi = total(P.units, LP, P.W[sp], eta, dl)
                rows.append(dict(sg=sg, anchor=kind, cell=name, delta=dl, slack=s, spec=sp, lo=lo, hi=hi))
        log(sg, kind)
        pd.DataFrame(rows).to_csv(f"{RES}/rev_anchor_{sg}.csv", index=False)


def run_mover(sg):
    log = timer(); P = Prep(sg); rows = []
    moves = ([("calib", True, 1.0)] if sg >= "20220309" else []) + [("eta0.1", False, 0.1), ("free", False, 2.0)]
    for mv, calib, eta in moves:
        LP = P.lps(calib=calib)
        for dl in [0.1, 1.0]:
            for sp in P.W:
                for t in [0.05, 0.1, 0.2, 0.3]:
                    for u in P.units: LP[u].mvF = t
                    lo, hi = total(P.units, LP, P.W[sp], eta, dl)
                    rows.append(dict(sg=sg, movement=mv, delta=dl, spec=sp, kind="bounds", t=t, lo=lo, hi=hi))
                def f(t):
                    for u in P.units: LP[u].mvF = t
                    return total(P.units, LP, P.W[sp], eta, dl)[0]
                a, b = breakdown(f, 0.0, 1.0, 0.004)
                rows.append(dict(sg=sg, movement=mv, delta=dl, spec=sp, kind="tstar", lo=a, hi=b))
            log(sg, mv, dl)
            pd.DataFrame(rows).to_csv(f"{RES}/rev_mover_{sg}.csv", index=False)
        for u in P.units: LP[u].mvF = None


def run_intercept(sg):
    log = timer(); P = Prep(sg); rows = []
    LP0 = P.lps(calib=True)
    r = sum(LP0[u].r.sum() for u in P.units); rr = sum(LP0[u].r_cal.sum() for u in P.units)
    C = sum((P.ev[u] * LP0[u].g["K"].sum(1)).sum() for u in P.units); K = sum(LP0[u].g["K"].sum() for u in P.units)
    rows.append(dict(sg=sg, kind="totals", r=r, r_rho=rr, C=C, K=K))
    for nu in [0.0, 0.5, 1.0]:
        for s in [None, 0.02]:
            LP = P.lps(calib=True, dF=None if s is None else ("slack", s))
            for u in P.units: LP[u].r_cal = LP[u].r + nu * (LP[u].r_cal - LP[u].r)
            for lam in [0.5, 1.0, 1.5]:
                for dl in [0.1, 1.0]:
                    for sp in P.W:
                        lo, hi = total(P.units, LP, P.W[sp], lam, dl)
                        rows.append(dict(sg=sg, kind="bounds", nu=nu, slack=s, lam=lam, delta=dl, spec=sp, lo=lo, hi=hi))
        log(sg, nu)
        pd.DataFrame(rows).to_csv(f"{RES}/rev_intercept_{sg}.csv", index=False)


if __name__ == "__main__":
    mode, sg = sys.argv[1], sys.argv[2]
    {"anchor": run_anchor, "mover": run_mover, "intercept": run_intercept}[mode](sg)
