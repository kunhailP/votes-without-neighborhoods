"""Valid-vote shares y_i = N_i / T_i, T_i = H_i - U_i - I_i (Online Appendix A, Proposition 4).

(1) Exact dong-level bounds [min y_i, max y_i] over Lambda by Dinkelbach's algorithm.
(2) Linear outer bound for theta_y = sum_i w_i y_i: since y_i - z_i = y_i (U_i + I_i) / H_i,
      w_i y_i >= w_i z_i + k_i (U_i + I_i) / H_i,  k_i = w_i ylo_i (w_i > 0) or w_i yhi_i (w_i < 0),
    so one LP gives a valid lower bound; the separable bound sum w ylo / w yhi is also valid and the
    larger of the two is used. Upper bounds are symmetric.
(3) Attainable values (fixed-denominator iteration and the LP solutions above): the true extremes lie in
    [outer, attainable].

CLP wraps any configured JointLP and caches its constraint matrices; it solves with exactly the
constraints of lp.constraints(), so zone restrictions and all assumptions are shared with the z bounds.
Dong-level bounds are cached under results/ydong/ with a key that includes every configured restriction."""
import hashlib
import os
import numpy as np
from .lp import hs_solve, KMS, INV
from .paths import RES

YDONG = RES / "ydong"
YDONG.mkdir(parents=True, exist_ok=True)


class CLP:
    def __init__(self, lp):
        self.lp = lp; self.g = lp.g; self.E = lp.E
        n = lp.n
        self.H = self.g["Avotes"] + self.E - self.g["D"]
        self.b = []
        for i in range(n):   # T_i = b0_i + b_i . x
            b = np.zeros(lp.nv); b[lp.iU(i)] = -1
            for j in range(n): b[lp.iF(i, j, INV)] = -1
            b[lp.iB(i, INV)] = -1; b[lp.iG(i, INV)] = -1
            self.b.append(b)
        self.b0 = self.H - self.g["A"][:, INV]

    def avec(self, i, ci):
        lp = self.lp; a = np.zeros(lp.nv)
        for j in range(lp.n): a[lp.iF(i, j, ci)] = 1
        a[lp.iB(i, ci)] = 1; a[lp.iG(i, ci)] = 1
        return a, self.g["A"][i, ci]

    def mats(self, eta, delta):
        """The LP's own constraint cache, keyed by (eta, delta) and every configured restriction, so a restriction changed
        after construction (zones, dF, mvF, r_cal, ...) is never served from stale matrices."""
        return self.lp.cached_constraints(eta, delta)

    def solve(self, c, eta, delta):
        Aeq, beq, Aub, bub = self.mats(eta, delta)
        return hs_solve(c, Aub, bub, Aeq, beq)

    def state(self, x, ci):
        F, B, G, U = self.lp.state(x)
        N = self.g["A"] + F.sum(1) + B + G; T = self.H - U - N[:, INV]
        return N[:, ci], T

    def key(self):
        """Fingerprint of every restriction that defines Lambda (for the dong-bound cache)."""
        lp = self.lp; h = hashlib.sha1(type(lp).__name__.encode())
        pg = None if lp.pool_groups is None else np.concatenate([np.r_[ix, lo, hi, ql, qh] for ix, lo, hi, ql, qh in lp.pool_groups])
        dF = None if lp.dF is None else (("slack", lp.dF[1]) if isinstance(lp.dF, tuple) else ("fixed", lp.dF))
        h.update(repr(dF).encode())
        h.update(repr(getattr(lp, 'mvF', None)).encode())
        g = lp.g   # the observed counts too, so that rebuilt inputs never reuse bounds computed from other data
        for v in [lp.allow, lp.ev, pg, lp.Bfix, lp.Gfix, lp.Hfix, lp.r_cal, g['a_tilde'], g['A'], g['K'], g['Bc'], g['Gc'], g['D'], lp.E, [g['U']]]:
            h.update(b"-" if v is None else np.round(np.asarray(v, float), 9).tobytes())
        return h.hexdigest()[:12]


def dong_bounds(clp, ci, eta, delta, tol=1e-10, maxit=30):
    """Dinkelbach: exact [min y_i, max y_i] for every dong; None if Lambda is empty."""
    n = clp.lp.n; lo = np.zeros(n); hi = np.zeros(n)
    if clp.solve(np.zeros(clp.lp.nv), eta, delta).status != 0: return None
    for i in range(n):
        a, a0 = clp.avec(i, ci); b, b0 = clp.b[i], clp.b0[i]
        for sgn, out in [(+1, lo), (-1, hi)]:
            r = clp.solve(sgn * a, eta, delta); x = r.x; lam = (a0 + a @ x) / (b0 + b @ x)
            for _ in range(maxit):
                r = clp.solve(sgn * (a - lam * b), eta, delta); x = r.x
                Fv = sgn * ((a0 + a @ x) - lam * (b0 + b @ x))
                new = (a0 + a @ x) / (b0 + b @ x)
                if Fv >= -tol * max(1.0, b0) or abs(new - lam) < 1e-12:
                    lam = new if sgn * new < sgn * lam else lam; break
                lam = new
            out[i] = lam
    return lo, hi


def tight_lp(clp, w, ci, eta, delta, ylo, yhi, side):
    """Outer bound (side=+1 lower, -1 upper) and the attained theta_y at that LP solution."""
    lp = clp.lp; c = np.zeros(lp.nv); const = 0.0
    for i in range(lp.n):
        a, a0 = clp.avec(i, ci); H = clp.H[i]; b, b0 = clp.b[i], clp.b0[i]
        k = w[i] * (ylo[i] if (w[i] > 0) == (side > 0) else yhi[i])
        c += w[i] / H * a - k / H * b; const += w[i] * a0 / H + k * (1 - b0 / H)
    r = clp.solve(side * c, eta, delta)
    if r.status != 0: return None, None
    N, T = clp.state(r.x, ci)
    return const + side * r.fun, float((w * N / T).sum())


def achievable(clp, w, ci, eta, delta, side, iters=10):
    lp = clp.lp; T = clp.H * 0.98; best = None
    for _ in range(iters):
        c = np.zeros(lp.nv)
        for i in range(lp.n): a, _ = clp.avec(i, ci); c += side * w[i] / T[i] * a
        r = clp.solve(c, eta, delta)
        if r.status != 0: return None
        N, Tn = clp.state(r.x, ci); val = float((w * N / Tn).sum())
        best = val if best is None else (min(best, val) if side > 0 else max(best, val))
        if np.allclose(Tn, T, rtol=1e-9): break
        T = Tn
    return best


def zbounds(clp, w, ci, eta, delta):
    lp = clp.lp; c = np.zeros(lp.nv); const = 0.0
    for i in range(lp.n): a, a0 = clp.avec(i, ci); c += w[i] / clp.H[i] * a; const += w[i] * a0 / clp.H[i]
    r1 = clp.solve(c, eta, delta); r2 = clp.solve(-c, eta, delta)
    if r1.status != 0 or r2.status != 0: return None
    return const + r1.fun, const - r2.fun


def get_dong(tag, u, clp, ci, eta, delta):
    """Dong-level y bounds with a cache keyed by election, unit, (eta, delta) and the restriction fingerprint."""
    f = YDONG / f"{tag}_{u}_c{ci}_e{eta:g}_d{delta:g}_{clp.key()}.npy"
    if os.path.exists(f):
        v = np.load(f); return None if v.size == 0 else (v[0], v[1])
    r = dong_bounds(clp, ci, eta, delta)
    # write atomically: parallel jobs (make -j) may ask for the same file while it is being written
    tmp = f.with_name(f"{f.stem}.{os.getpid()}.tmp.npy")
    np.save(tmp, np.array([]) if r is None else np.vstack(r)); os.replace(tmp, f); return r


def run_cells(tag, units, CL, Wspecs, cells, ci=KMS, scale=1.0, log=print):
    """Wspecs: {spec: {unit: w}}; cells: [(eta, delta)]. Returns one row per (cell, spec)."""
    rows = []
    for eta, delta in cells:
        DB = {u: get_dong(tag, u, CL[u], ci, eta, delta) for u in units}
        if any(v is None for v in DB.values()):
            for sp in Wspecs: rows.append(dict(sg=tag, spec=sp, eta=eta, delta=delta, note="infeasible"))
            log(tag, eta, delta, "infeasible"); continue
        for sp, wg in Wspecs.items():
            acc = dict(z_lo=0, z_hi=0, y_sep_lo=0, y_sep_hi=0, y_tight_lo=0, y_tight_hi=0, y_ach_lo=0, y_ach_hi=0)
            for u in units:
                clp = CL[u]; w = wg[u]
                if not np.any(w): continue
                ylo, yhi = DB[u]
                z = zbounds(clp, w, ci, eta, delta)
                tl, al = tight_lp(clp, w, ci, eta, delta, ylo, yhi, +1); th, ah = tight_lp(clp, w, ci, eta, delta, ylo, yhi, -1)
                sl = float(np.sum(np.where(w > 0, w * ylo, w * yhi))); sh = float(np.sum(np.where(w > 0, w * yhi, w * ylo)))
                ach_l = min(achievable(clp, w, ci, eta, delta, +1), al); ach_h = max(achievable(clp, w, ci, eta, delta, -1), ah)
                for k, v in [("z_lo", z[0]), ("z_hi", z[1]), ("y_sep_lo", sl), ("y_sep_hi", sh),
                             ("y_tight_lo", max(tl, sl)), ("y_tight_hi", min(th, sh)), ("y_ach_lo", ach_l), ("y_ach_hi", ach_h)]:
                    acc[k] += v
            row = dict(sg=tag, spec=sp, eta=eta, delta=delta, **{k: v * scale for k, v in acc.items()})
            row["gap_lo"] = row["y_ach_lo"] - row["y_tight_lo"]; row["gap_hi"] = row["y_tight_hi"] - row["y_ach_hi"]
            rows.append(row); log({k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()})
    return rows
