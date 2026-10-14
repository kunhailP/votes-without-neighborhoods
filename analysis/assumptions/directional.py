"""Directional sensitivity: departures of residents' early ballots that are correlated with price (Section 4.5; Online
Appendix Table C13).

The symmetric restrictions (A_delta) and (A^F_s) let each neighborhood's residents depart from their benchmarks independently,
so a reversal can align departures against price. This script replaces (A^F_s) by a restriction on that alignment itself.
For dong i, let D_i be residents' conservative early ballots (in-zone and out-of-zone) minus what their benchmarks imply,
  D_i = sum_j F_ij,cons - a^F_i,cons sum_{j,c} F_ijc + P_i,cons - a~_i,cons sum_c P_ic,
measured as a share of the roll, d_i = D_i / H_i (the units of z). Within each counting jurisdiction u, the OLS slope of d on
log price, g_u = sum_{i in I_u} (x_i - xbar_u) d_i / sum_{i in I_u} (x_i - xbar_u)^2 (I_u: dongs of u with a price), is bounded:
|g_u| <= kappa.
kappa = 0 means departures are uncorrelated with price within every jurisdiction; kappa = infinity removes the restriction.
Reference: the same slope computed for in-zone station ballots, which are observed (stations also count non-residents).
Output: results/directional.csv (bounds) and results/directional_reference.csv (observed station gradients)."""
import numpy as np
import pandas as pd
from vwn.run import Prep, timer, elections_from_argv
from vwn.lp import JointLP, KMS
from vwn.bounds import total
from vwn.paths import RES
from spatial_scope import sample_weights, GANGNAM3

KAPPAS = [0.0, 0.005, 0.01, 0.02, 0.05, 0.1, np.inf]
DELTAS = [0.1, 0.2, 1.0]


class DirLP(JointLP):
    """JointLP plus |g_u| <= kappa (kappa and the regression weights v set as attributes)."""
    kappa = np.inf; v = None

    def config_key(self, eta, delta):
        return super().config_key(eta, delta) + (float(self.kappa),)

    def constraints(self, eta, delta):
        Aeq, beq, Aub, bub = super().constraints(eta, delta)
        if not np.isfinite(self.kappa) or self.v is None or not np.any(self.v): return Aeq, beq, Aub, bub
        from scipy.sparse import vstack, csr_matrix
        n, C, g = self.n, self.C, self.g
        H = g["Avotes"] + self.E - g["D"]; aF = self.ref()[:, KMS]; at = g["a_tilde"][:, KMS]
        row = np.zeros(self.nv)
        for i in range(n):
            if self.v[i] == 0: continue
            k = self.v[i] / H[i]
            for j in range(n):
                for c in range(C): row[self.iF(i, j, c)] -= k * aF[i]
                row[self.iF(i, j, KMS)] += k
            for c in range(C): row[self.iB(i, c)] -= k * at[i]
            row[self.iB(i, KMS)] += k
        R = csr_matrix(np.vstack([row, -row]))
        return Aeq, beq, vstack([Aub, R]).tocsr(), np.r_[bub, self.kappa, self.kappa]


def unit_v(P):
    """Within-jurisdiction OLS slope weights on log price: v_i = (x_i - xbar_u) / sum_{j in I_u} (x_j - xbar_u)^2 for the dongs
    of counting jurisdiction u with a price (I_u), 0 otherwise. They sum to zero in every jurisdiction, so a constant
    departure has slope 0. In 2024 the jurisdictions are constituencies, not gu."""
    out = {}
    for u, xu in P.wsplit(P.x).items():
        m = ~np.isnan(xu); v = np.zeros(len(xu))
        if m.sum() >= 2:
            xc = xu[m] - xu[m].mean(); ss = (xc ** 2).sum()
            if ss > 0: v[m] = xc / ss
        out[u] = v
    return out


if __name__ == "__main__":
    rows, ref = [], []
    for sg in elections_from_argv(["20220309", "20240410", "20250603", "20260603"]):
        log = timer(); P = Prep(sg); V = unit_v(P)
        # observed reference: the same slope for in-zone station ballots, by jurisdiction
        for u in P.units:
            g, E = P.G[u]; lp = JointLP(g, E); H = g["Avotes"] + E - g["D"]; K = g["K"]
            d = (K[:, KMS] - lp.ref()[:, KMS] * K.sum(1)) / H
            if np.any(V[u]): ref.append(dict(sg=sg, unit=u, station_gradient=float(V[u] @ d), n=len(d)))
        LP = P.lps(calib=True, cls=DirLP)
        for u in P.units: LP[u].v = V[u]
        for sample, exclude in [("all", ()), ("excl_gangnam3", GANGNAM3)]:
            Wu = P.wsplit(sample_weights(P, exclude)["slope"])
            for dl in DELTAS:
                for k in KAPPAS:
                    for u in P.units: LP[u].kappa = k
                    lo, hi = total(P.units, LP, Wu, 1.0, dl)
                    rows.append(dict(sg=sg, sample=sample, movement="lambda=1", delta=dl, kappa=k, lo=lo, hi=hi))
                # breakdown point kappa* = sup{kappa: lower bound > 0} (Proposition 3: the lower bound is non-increasing in kappa)
                def f(k):
                    for u in P.units: LP[u].kappa = k
                    return total(P.units, LP, Wu, 1.0, dl)[0]
                if f(np.inf) > 0: ks = np.inf
                elif not f(0.0) > 0: ks = np.nan
                else:
                    a_, b_ = 0.0, 0.3
                    while b_ - a_ > 2e-4:
                        m = (a_ + b_) / 2
                        if f(m) > 0: a_ = m
                        else: b_ = m
                    ks = a_
                rows.append(dict(sg=sg, sample=sample, movement="lambda=1", delta=dl, kappa="breakdown", lo=ks, hi=np.nan))
                log(sg, sample, dl)
        pd.DataFrame(rows).to_csv(f"{RES}/directional.csv", index=False)
        pd.DataFrame(ref).to_csv(f"{RES}/directional_reference.csv", index=False)
