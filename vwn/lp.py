"""Linear-programming core: the allocation polytope Lambda and its solvers.

Observed (one counting jurisdiction g, dongs i, in-zone early stations j = dongs, categories c):
  A[i, c]  election-day ballots of dong i            K[j, c]  in-zone early ballots counted at station j
  D[i]     electorate left on the election-day roll   E[i]     certified electorate
  Bc[c]    out-of-zone early ballots (jurisdiction total, P_c in the paper)
  Gc[c]    at-home, shipboard and overseas ballots (jurisdiction total, Q_c in the paper)
  U        removed residents who cast no counted ballot (jurisdiction residual)

Unknowns (variable layout F | B | G | U):
  F[i, j, c] in-zone early ballots of residents of i cast at station j
  B[i, c]    out-of-zone early ballots of residents of i          (P_ic)
  G[i, c]    at-home, shipboard and overseas ballots of residents  (Q_ic)
  U[i]       removed residents of i who did not vote

Every restriction is built in JointLP.constraints(). All solver paths (LP, the valid-vote
programs in vwn.ytight, and the mixed-integer checks in vwn.intcheck) call constraints(), so they
always share one feasible set. In particular the zone restriction (2026: F_ij = 0 when
i and j lie in different gu council constituencies) is imposed as equality rows here rather than
as solver-specific variable bounds.
"""
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

CANDS = ["LJM", "KMS", "LJS", "KYG", "SJH", "invalid"]
KMS = CANDS.index("KMS")      # slot of the main conservative candidate in every election
INV = CANDS.index("invalid")

HS_OPTS = dict(primal_feasibility_tolerance=1e-9, dual_feasibility_tolerance=1e-10)


def hs_solve(cvec, Aub, bub, Aeq, beq, bounds=(0, None)):
    """HiGHS with the objective rescaled to max|c| = 1.

    Slope weights w_i / H_i can be ~1e-9, below HiGHS's default dual tolerance; without rescaling the
    solver can stop early and report a minimum that is too high (bounds that are too narrow)."""
    cvec = np.asarray(cvec, float)
    s = float(np.abs(cvec).max()) if np.any(cvec) else 1.0
    r = linprog(cvec / s, A_ub=Aub, b_ub=bub, A_eq=Aeq, b_eq=beq, bounds=bounds, method="highs", options=HS_OPTS)
    if r.status == 0:
        r.fun = r.fun * s
    return r


class JointLP:
    """Allocation polytope for one counting jurisdiction.

    Configurable restrictions (attributes, all optional):
      allow   n x n bool  early-voting zone: F_ij allowed only if allow[i, j] (from g["allow"])
      zone    length-n    zone label of each dong (from g["zone"]); used for the calibrated intercept
      ev      length-n    calibrated movement: cap at station j is r_rho_j + eta * ev_j * K_j  (eta plays lambda)
                          if None, uniform movement: cap r_j + eta * K_j            (assumption M_eta)
      dF      None | float | ("slack", s)  residents' in-zone early composition (assumption A^F_s)
      pool_groups  list of (index array, Plo, Phi, Qlo, Qhi): headcount ranges for the out-of-zone
                   (B) and at-home (G) ballots of a group of dongs (2026 cross-contest information)
      Bfix, Gfix   n x C arrays fixing B or G (counterfactual residence reporting)
      Hfix         n x n array fixing sum_c F_ijc (counterfactual headcount reporting)
    """

    def __init__(self, g, E):
        self.g = g; self.E = np.asarray(E, float)
        n, C = g["K"].shape; self.n, self.C = n, C
        self.nF = n * n * C; self.nB = n * C; self.nG = n * C; self.nU = n
        self.nv = self.nF + self.nB + self.nG + self.nU
        self.oB = self.nF; self.oG = self.oB + self.nB; self.oU = self.oG + self.nG
        ED = self.E - g["D"]; Kj = g["K"].sum(1)
        # movement the roll forces at station j (Lemma 1)
        self.r = np.maximum(0.0, Kj - ED)
        self.allow = g.get("allow")
        self.zone = np.asarray(g["zone"]) if g.get("zone") is not None else np.zeros(n, int)
        # calibrated intercept r_rho_j = max(r_j, K_j - kappa_u (E_j - D_j)), kappa_u = sum K / sum (E - D) over the zone u of j
        kin = np.zeros(n)
        for u in np.unique(self.zone):
            m = self.zone == u; kin[m] = Kj[m].sum() / max(ED[m].sum(), 1)
        self.r_cal = np.maximum(self.r, Kj - kin * ED)
        self.ev = None; self.dF = None; self.pool_groups = None; self.Bfix = None; self.Gfix = None; self.Hfix = None; self.mvF = None

    # variable indices
    def iF(self, i, j, c): return (i * self.n + j) * self.C + c
    def iB(self, i, c): return self.oB + i * self.C + c
    def iG(self, i, c): return self.oG + i * self.C + c
    def iU(self, i): return self.oU + i

    def ref(self):
        """Benchmark for residents' in-zone early composition: election-day composition shifted by the
        jurisdiction-wide gap between in-zone early and election-day composition (a^F in the paper)."""
        g = self.g; A = g["A"]; K = g["K"]
        day = A / np.maximum(A.sum(1, keepdims=True), 1)
        gap = K.sum(0) / max(K.sum(), 1) - A.sum(0) / A.sum()
        return np.clip(day + gap, 0, 1)

    def constraints(self, eta, delta):
        n, C, g = self.n, self.C, self.g
        eq_rows, eq_b = [], []          # list of dict(col -> coef), rhs
        ub_rows, ub_b = [], []

        # (R) roll identity
        for i in range(n):
            d = {self.iF(i, j, c): 1.0 for j in range(n) for c in range(C)}
            d.update({self.iB(i, c): 1.0 for c in range(C)}); d.update({self.iG(i, c): 1.0 for c in range(C)})
            d[self.iU(i)] = 1.0; eq_rows.append(d); eq_b.append(self.E[i] - g["D"][i])
        # (S) station counts, pooled totals (invalid ballots included), non-voters
        for j in range(n):
            for c in range(C):
                eq_rows.append({self.iF(i, j, c): 1.0 for i in range(n)}); eq_b.append(g["K"][j, c])
        for c in range(C):
            eq_rows.append({self.iB(i, c): 1.0 for i in range(n)}); eq_b.append(g["Bc"][c])
        for c in range(C):
            eq_rows.append({self.iG(i, c): 1.0 for i in range(n)}); eq_b.append(g["Gc"][c])
        eq_rows.append({self.iU(i): 1.0 for i in range(n)}); eq_b.append(g["U"])
        # zones: no in-zone early ballot across zones (non-negativity makes one row per pair enough)
        if self.allow is not None:
            for i in range(n):
                for j in range(n):
                    if not self.allow[i, j]:
                        eq_rows.append({self.iF(i, j, c): 1.0 for c in range(C)}); eq_b.append(0.0)
        # published early-voter headcounts by registered dong x station (counterfactual reporting)
        if self.Hfix is not None:
            for i in range(n):
                for j in range(n):
                    eq_rows.append({self.iF(i, j, c): 1.0 for c in range(C)}); eq_b.append(self.Hfix[i, j])
        # fixed pools (counterfactual reporting)
        for fix, idx in [(self.Bfix, self.iB), (self.Gfix, self.iG)]:
            if fix is None: continue
            for i in range(n):
                for c in range(C):
                    eq_rows.append({idx(i, c): 1.0}); eq_b.append(fix[i, c])

        # movement caps: (M_eta) uniform or calibrated
        Ksum = g["K"].sum(1)
        cap = self.r + eta * Ksum if self.ev is None else self.r_cal + eta * np.asarray(self.ev, float) * Ksum
        for j in range(n):
            ub_rows.append({self.iF(i, j, c): 1.0 for i in range(n) if i != j for c in range(C)}); ub_b.append(cap[j])
        # (A_delta) out-of-zone early composition around the anchor a_tilde
        at = g["a_tilde"]
        for i in range(n):
            for c in range(C):
                d = {self.iB(i, c2): -(at[i, c] + delta) for c2 in range(C)}; d[self.iB(i, c)] += 1.0
                ub_rows.append(d); ub_b.append(0.0)
                lo = max(at[i, c] - delta, 0.0)
                d = {self.iB(i, c2): lo for c2 in range(C)}; d[self.iB(i, c)] -= 1.0
                ub_rows.append(d); ub_b.append(0.0)
        # (A^F_s) residents' in-zone early composition, in cross-multiplied (linear) form:
        #   (ref - wid) * sum_{j,c'} F_ijc' <= sum_j F_ijc <= (ref + wid) * sum_{j,c'} F_ijc'
        if self.dF is not None:
            ref = self.ref()
            if isinstance(self.dF, tuple):
                K = g["K"]; dev = np.abs(K / np.maximum(K.sum(1, keepdims=True), 1) - ref); wid = dev + self.dF[1]
            else:
                wid = np.full((n, C), float(self.dF))
            for i in range(n):
                for c in range(C):
                    hi, lo = ref[i, c] + wid[i, c], max(ref[i, c] - wid[i, c], 0.0)
                    d1 = {self.iF(i, j, c2): -hi for j in range(n) for c2 in range(C)}
                    d2 = {self.iF(i, j, c2): lo for j in range(n) for c2 in range(C)}
                    for j in range(n): d1[self.iF(i, j, c)] += 1.0; d2[self.iF(i, j, c)] -= 1.0
                    ub_rows += [d1, d2]; ub_b += [0.0, 0.0]
        # movers' composition: residents of i who voted at another station vote within mvF of their home station's composition
        #   (k_ic - t) * sum_{j!=i,c'} F_ijc' <= sum_{j!=i} F_ijc <= (k_ic + t) * sum_{j!=i,c'} F_ijc'
        if self.mvF is not None:
            K = g["K"]; k = K / np.maximum(K.sum(1, keepdims=True), 1); t = float(self.mvF)
            for i in range(n):
                others = [j for j in range(n) if j != i and (self.allow is None or self.allow[i, j])]
                if not others: continue
                for c in range(C):
                    hi, lo = k[i, c] + t, max(k[i, c] - t, 0.0)
                    d1 = {self.iF(i, j, c2): -hi for j in others for c2 in range(C)}
                    d2 = {self.iF(i, j, c2): lo for j in others for c2 in range(C)}
                    for j in others: d1[self.iF(i, j, c)] += 1.0; d2[self.iF(i, j, c)] -= 1.0
                    ub_rows += [d1, d2]; ub_b += [0.0, 0.0]
        # cross-contest headcounts for groups of dongs
        if self.pool_groups is not None:
            for idx_, Plo, Phi, Qlo, Qhi in self.pool_groups:
                dP = {self.iB(i, c): 1.0 for i in idx_ for c in range(C)}
                dQ = {self.iG(i, c): 1.0 for i in idx_ for c in range(C)}
                ub_rows += [dP, {k: -v for k, v in dP.items()}, dQ, {k: -v for k, v in dQ.items()}]
                ub_b += [Phi, -Plo, Qhi, -Qlo]

        def mat(rows):
            ri, ci, vi = [], [], []
            for r, d in enumerate(rows):
                ri += [r] * len(d); ci += list(d.keys()); vi += list(d.values())
            return coo_matrix((vi, (ri, ci)), shape=(len(rows), self.nv)).tocsr()
        return mat(eq_rows), np.array(eq_b, float), mat(ub_rows), np.array(ub_b, float)

    def config_key(self, eta, delta):
        """Hashable fingerprint of (eta, delta) and every configured restriction."""
        f = lambda v: None if v is None else hash(np.ascontiguousarray(np.asarray(v, float)).tobytes())
        pg = None if self.pool_groups is None else tuple((tuple(ix), a, b, c, d) for ix, a, b, c, d in self.pool_groups)
        return (float(eta), float(delta), f(self.ev), repr(self.dF), pg, f(self.Bfix), f(self.Gfix), f(self.Hfix), f(self.allow), self.mvF, f(self.r_cal), f(self.g['a_tilde']), type(self).__name__)

    def cached_constraints(self, eta, delta):
        if not hasattr(self, "_cache"): self._cache = {}
        k = self.config_key(eta, delta)
        if k not in self._cache:
            if len(self._cache) > 64: self._cache.clear()
            self._cache[k] = self.constraints(eta, delta)
        return self._cache[k]

    def solve(self, cvec, eta, delta):
        Aeq, beq, Aub, bub = self.cached_constraints(eta, delta)
        return hs_solve(cvec, Aub, bub, Aeq, beq)

    def feasible(self, eta, delta):
        return self.solve(np.zeros(self.nv), eta, delta).status == 0

    def delta_min(self, eta, tol=1e-3):
        """Smallest feasible band on out-of-zone composition (upper end of the bisection interval)."""
        if self.feasible(eta, 0.0): return 0.0
        if not self.feasible(eta, 1.0): return np.inf
        lo, hi = 0.0, 1.0
        while hi - lo > tol:
            mid = (lo + hi) / 2
            if self.feasible(eta, mid): hi = mid
            else: lo = mid
        return hi

    def state(self, x):
        """Split a solution vector into F (n,n,C), B (n,C), G (n,C), U (n)."""
        n, C = self.n, self.C
        return (x[:self.nF].reshape(n, n, C), x[self.oB:self.oB + self.nB].reshape(n, C),
                x[self.oG:self.oG + self.nG].reshape(n, C), x[self.oU:])


# alternative name for JointLP
MoverLP = JointLP
