"""Sharp bounds on slopes in the roll-based share z (Proposition 1), aggregation across jurisdictions and
breakdown points (Proposition 3)."""
import numpy as np
from .lp import KMS


def slope_c(lp, w, cand=KMS):
    """Objective vector and constant for theta_z = sum_i w_i N_ic / H_i in one jurisdiction."""
    g = lp.g; n = lp.n; H = g["Avotes"] + lp.E - g["D"]
    c = np.zeros(lp.nv)
    for i in range(n):
        for j in range(n): c[lp.iF(i, j, cand)] = w[i] / H[i]
        c[lp.iB(i, cand)] = w[i] / H[i]; c[lp.iG(i, cand)] = w[i] / H[i]
    return c, float((w * g["A"][:, cand] / H).sum())


def bounds_with_w(lp, w, cand=KMS, eta=0.0, delta=1.0):
    """[min, max] of the jurisdiction's contribution to theta_z, or None if Lambda is empty."""
    if not np.any(w):
        return (0.0, 0.0) if lp.feasible(eta, delta) else None
    c, const = slope_c(lp, w, cand)
    rmin = lp.solve(c, eta, delta); rmax = lp.solve(-c, eta, delta)
    if rmin.status != 0 or rmax.status != 0: return None
    return const + rmin.fun, const - rmax.fun


def total(units, LP, Wu, eta, delta, cand=KMS):
    """Sum of per-jurisdiction bounds (no constraint links two jurisdictions). (nan, nan) if infeasible."""
    lo = hi = 0.0
    for u in units:
        b = bounds_with_w(LP[u], Wu[u], cand, eta, delta)
        if b is None: return np.nan, np.nan
        lo += b[0]; hi += b[1]
    return lo, hi


def bisect(f, a, b, tol):
    """Largest t in [a, b] with f(t) > 0, for f non-increasing in t (f(a) > 0 assumed).

    Returns (lo, hi): the sign is identified at lo and not at hi (hi = b and lo = b if f(b) > 0).
    Both ends are returned at full precision; tables report lo."""
    if f(b) > 0: return b, b
    while b - a > tol:
        m = (a + b) / 2
        if f(m) > 0: a = m
        else: b = m
    return a, b


def breakdown(f, a, b, tol):
    """Breakdown point of a lower bound f(t) (nan-safe). Returns (lo, hi); (0, 0) if not signed at t = a."""
    g = lambda t: (lambda v: -1.0 if np.isnan(v) else v)(f(t))
    if g(a) <= 0: return 0.0, 0.0
    return bisect(g, a, b, tol)
