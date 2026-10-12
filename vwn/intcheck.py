"""Integer allocations (Online Appendix A.4; Table A1). Ballots are integers, so only integer points of Lambda are
allocations. The LP relaxation gives valid outer bounds; near a sign boundary we check (a) whether the
integer minimum differs from the LP minimum and (b) whether a sign-reversing allocation exists in integers.

The mixed-integer programs use clp.mats(), i.e. exactly lp.constraints(): zone restrictions and every
assumption enter the integer problem in the same way as the LP."""
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from .lp import KMS


def solve_int(clp, c, eta, delta, tl=120):
    Aeq, beq, Aub, bub = clp.mats(eta, delta)
    cons = [LinearConstraint(Aeq, beq, beq), LinearConstraint(Aub, -np.inf, bub)]
    sc = float(np.abs(c).max()) or 1.0
    r = milp(c / sc, constraints=cons, integrality=np.ones(clp.lp.nv), bounds=Bounds(0, np.inf),
             options=dict(time_limit=tl, mip_rel_gap=1e-6, disp=False))
    if r.x is not None:
        r.fun = r.fun * sc
        if getattr(r, "mip_dual_bound", None) is not None: r.mip_dual_bound = r.mip_dual_bound * sc
    return r


def objs(clp, w, ylo, yhi, side, ci=KMS):
    """z objective and the valid-vote outer-bound objective (as in vwn.ytight.tight_lp)."""
    lp = clp.lp; cz = np.zeros(lp.nv); kz = 0.0; cy = np.zeros(lp.nv); ky = 0.0
    for i in range(lp.n):
        a, a0 = clp.avec(i, ci); H = clp.H[i]; b, b0 = clp.b[i], clp.b0[i]
        cz += w[i] / H * a; kz += w[i] * a0 / H
        k = w[i] * (ylo[i] if (w[i] > 0) == (side > 0) else yhi[i])
        cy += w[i] / H * a - k / H * b; ky += w[i] * a0 / H + k * (1 - b0 / H)
    return cz, kz, cy, ky
