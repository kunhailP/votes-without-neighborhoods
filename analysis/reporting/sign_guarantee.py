"""Does a reporting change reveal the sign of the within-gu slope whatever the true allocation? (Section 5; Online Appendix Table C16)

Definition. Report S reveals the sign on Lambda iff no two allocations l, l' in Lambda with S l = S l' have slopes of strictly
opposite sign, theta(l) < 0 < theta(l'). (Allocations with theta = 0 are not counted as either sign, so full disclosure, S l = S l'
=> l = l', always reveals the sign.) We solve one LP over all jurisdictions (block-diagonal, coupled by the two slope rows):

    t*_S = max t   s.t.   theta(l) <= -t,  theta(l') >= t,  S_u l_u = S_u l'_u for every jurisdiction u,  l, l' in Lambda.

Because the set of pairs is symmetric under swapping l and l', t*_S > 0 iff a strictly opposite indistinguishable pair exists, and
t*_S is then the largest symmetric margin of such a pair (allocations with slopes -t*_S and +t*_S that the report cannot tell
apart). t*_S <= 0 means the report reveals the sign whatever the truth. Output: results/sign_guarantee_<sg>.csv"""
import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.optimize import linprog
from vwn.run import Prep, timer, elections_from_argv
from vwn.bounds import slope_c
from vwn.lp import HS_OPTS
from vwn.paths import RES
from disclosure_guarantee import selector

TOL = 1e-7  # t* within solver tolerance of zero counts as no strictly opposite pair


def solve(P, LP, W, eta, delta, prop):
    blocks = []
    for u in P.units:
        lp = LP[u]; c, k = slope_c(lp, W[u])
        blocks.append((*lp.cached_constraints(eta, delta), c, k, selector(lp, prop)))
    return margin(blocks)


def margin(blocks):
    """t*_S for blocks [(Aeq, beq, Aub, bub, c, k, S)], theta = sum_u (c_u x_u + k_u)."""
    eqs, ubs, beq, bub, c1, c2, k0 = [], [], [], [], [], [], 0.0
    for Aeq, be, Aub, bu, c, k, S in blocks:
        nv = Aeq.shape[1]; S = sp.csr_matrix(S)
        eqs.append(sp.vstack([sp.block_diag([Aeq, Aeq]), sp.hstack([S, -S])])); beq += [be, be, np.zeros(S.shape[0])]
        ubs.append(sp.block_diag([Aub, Aub])); bub += [bu, bu]
        c1.append(np.r_[c, np.zeros(nv)]); c2.append(np.r_[np.zeros(nv), c]); k0 += k
    c1 = np.concatenate(c1); c2 = np.concatenate(c2)
    # variables (x, u) with t = s*u:  theta(l) <= -t  <=>  c1 x/s + u <= -k0/s ;  theta(l') >= t  <=>  -c2 x/s + u <= k0/s
    s = float(np.abs(c1).max()); A = sp.block_diag(ubs).tocsr(); m, n = A.shape
    A_ub = sp.vstack([sp.hstack([A, sp.csr_matrix((m, 1))]),
                      sp.csr_matrix(np.r_[c1 / s, 1.0][None, :]), sp.csr_matrix(np.r_[-c2 / s, 1.0][None, :])]).tocsr()
    b_ub = np.r_[np.concatenate(bub), -k0 / s, k0 / s]
    E = sp.block_diag(eqs).tocsr(); A_eq = sp.hstack([E, sp.csr_matrix((E.shape[0], 1))]).tocsr(); b_eq = np.concatenate(beq)
    obj = np.zeros(n + 1); obj[-1] = -1.0
    r = linprog(obj, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=[(0, None)] * n + [(None, None)], method="highs", options=HS_OPTS)
    return (s * r.x[-1]) if r.status == 0 else np.nan, r.status


if __name__ == "__main__":
    import sys
    rows = []
    for sg in elections_from_argv(["20220309", "20240410", "20250603", "20260603"]):
        log = timer(); P = Prep(sg); W = P.W["guFE"]
        for name, calib, eta, dl, s in [("calib", True, 1.0, 1.0, None), ("calib, s=0.02", True, 1.0, 1.0, 0.02),
                                        ("calib, delta=0.1", True, 1.0, 0.1, None), ("calib, delta=0.1, s=0.02", True, 1.0, 0.1, 0.02)]:
            dF = None if s is None else ("slack", s)
            LP = P.lps(calib=calib, dF=dF); LPf = P.lps(calib=False, dF=dF)
            for prop in ["P2", "P2b", "P12"]:
                L, e = (LPf, 10.0) if prop == "P12" else (LP, eta)
                t, st = solve(P, L, W, e, dl, prop)
                rows.append(dict(sg=sg, config=name, proposal=prop, t_star=t, status=st, sign_revealed=bool(t <= TOL) if np.isfinite(t) else None))
            log(sg, name)
            pd.DataFrame(rows).to_csv(f"{RES}/sign_guarantee{'_' + sg if len(sys.argv) == 2 else ''}.csv", index=False)
