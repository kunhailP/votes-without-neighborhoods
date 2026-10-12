"""Further restrictions and benchmarks (Sections 3.4 and 4.5; Online Appendix Tables C22 and C25).

1. delta*: the largest out-of-zone tolerance at which the within-district slope stays positive with residents' early composition
   at the main slack s = 0.02 (mobility-calibrated movement), by bisection on delta.
2. Out-of-zone alignment: instead of the per-dong band delta (set to 1), the slope of residents' out-of-zone departures from
   their station anchor (as a share of the roll) on log price is bounded by kappa_P within each counting jurisdiction, with
   s = 0.02 for in-zone ballots; kappa_P* is its breakdown point.
3. Movers and composition together: s = 0.02 and movers within t of their home station's composition (t = 0.05, 0.10).
4. A between-district reference for kappa: if, within districts, residents' early-vote gaps varied with price as the district
   gaps do across districts, their departures would have slope b_K * (in-zone early / H) + (b_B - b_K) * (out-of-zone / H),
   with b_K and b_B the cross-district slopes of the in-zone and out-of-zone early minus election-day gaps on log price;
   the reference adds the absolute values of the two terms, so that they cannot offset.
5. Removed residents with no counted ballot (U): size, and its cross-district relation with price.
Outputs: results/further_restrictions_bounds.csv, results/further_restrictions_reference.csv"""
import numpy as np
import pandas as pd
from scipy.sparse import vstack, csr_matrix
from vwn.run import Prep, timer, elections_from_argv
from vwn.lp import JointLP, KMS, INV
from vwn.bounds import total
from vwn.paths import RES
from spatial_scope import sample_weights, GANGNAM3
from directional import unit_v


class OZLP(JointLP):
    """JointLP plus |sum_i v_i (P_i,cons - a~_i,cons P_i.) / H_i| <= kappa_P."""
    kappaP = np.inf; v = None

    def config_key(self, eta, delta):
        return super().config_key(eta, delta) + (float(self.kappaP),)

    def constraints(self, eta, delta):
        Aeq, beq, Aub, bub = super().constraints(eta, delta)
        if not np.isfinite(self.kappaP) or self.v is None or not np.any(self.v): return Aeq, beq, Aub, bub
        g = self.g; H = g["Avotes"] + self.E - g["D"]; at = g["a_tilde"][:, KMS]; row = np.zeros(self.nv)
        for i in range(self.n):
            if self.v[i] == 0: continue
            k = self.v[i] / H[i]
            for c in range(self.C): row[self.iB(i, c)] -= k * at[i]
            row[self.iB(i, KMS)] += k
        return Aeq, beq, vstack([Aub, csr_matrix(np.vstack([row, -row]))]).tocsr(), np.r_[bub, self.kappaP, self.kappaP]


def bis(f, a, b, tol):
    """Largest x in [a, b] with f(x) > 0 for f non-increasing (nan counts as not positive); a assumed positive."""
    while b - a > tol:
        m = (a + b) / 2
        v = f(m)
        if not np.isnan(v) and v > 0: a = m
        else: b = m
    return a


if __name__ == "__main__":
    rows, ref = [], []
    for sg in elections_from_argv(["20220309", "20240410", "20250603", "20260603"]):
        log = timer(); P = Prep(sg); V = unit_v(P)
        for sample, exclude in [("all", ()), ("excl_gangnam3", GANGNAM3)]:
            Wu = P.wsplit(sample_weights(P, exclude)["slope"])
            # 1. delta* at s = 0.02
            LP = P.lps(calib=True, dF=("slack", 0.02))
            f = lambda d: total(P.units, LP, Wu, 1.0, d)[0]
            if f(1.0) > 0: ds = np.inf
            else:
                lo = 0.0
                if np.isnan(f(lo)):   # smallest feasible band first
                    a, b = 0.0, 1.0
                    while b - a > 1e-4:
                        m = (a + b) / 2
                        if np.isnan(f(m)): a = m
                        else: b = m
                    lo = b
                ds = bis(f, lo, 1.0, 1e-3) if f(lo) > 0 else np.nan
            rows.append(dict(sg=sg, sample=sample, analysis="delta_star", param=np.nan, lo=ds, hi=np.nan))
            # 3. movers and composition together
            for t in [0.05, 0.10]:
                for u in P.units: LP[u].mvF = t
                lo_, hi_ = total(P.units, LP, Wu, 1.0, 0.1)
                rows.append(dict(sg=sg, sample=sample, analysis="s002_movers", param=t, lo=lo_, hi=hi_))
            for u in P.units: LP[u].mvF = None
            # 2. out-of-zone alignment instead of delta
            LQ = P.lps(calib=True, dF=("slack", 0.02), cls=OZLP)
            for u in P.units: LQ[u].v = V[u]
            def g(k):
                for u in P.units: LQ[u].kappaP = k
                return total(P.units, LQ, Wu, 1.0, 1.0)[0]
            for k in [0.0, 0.01, 0.02, 0.05]:
                rows.append(dict(sg=sg, sample=sample, analysis="oz_align", param=k, lo=g(k), hi=np.nan))
            ks = np.inf if g(np.inf) > 0 else (bis(g, 0.0, 0.3, 2e-4) if g(0.0) > 0 else np.nan)
            rows.append(dict(sg=sg, sample=sample, analysis="oz_align_star", param=np.nan, lo=ks, hi=np.nan))
            log(sg, sample)
        # 4. between-district reference for kappa; 5. U
        gu = []
        for u in P.units:
            gg, E = P.G[u]; A, K, B = gg["A"], gg["K"], gg["Bc"]
            day = A[:, KMS].sum() / (A.sum() - A[:, INV].sum()); sk = K[:, KMS].sum() / (K.sum() - K[:, INV].sum()); sb = B[KMS] / (B.sum() - B[INV])
            w = P.Wfull["guFE"]   # unit mean log price from the dongs with a price
            xs = P.x[[k for k, (uu, _) in enumerate(P.idx) if uu == u]]
            gu.append(dict(unit=u, x=np.nanmean(xs), gK=sk - day, gB=sb - day, H=float((gg["Avotes"] + E - gg["D"]).sum()),
                           K=float(K.sum()), Bn=float(B.sum()), U=gg["U"], removed=float((E - gg["D"]).sum())))
        d = pd.DataFrame(gu); X = np.column_stack([np.ones(len(d)), d.x])
        bK = np.linalg.lstsq(X, d.gK, rcond=None)[0][1]; bB = np.linalg.lstsq(X, d.gB, rcond=None)[0][1]
        sK = d.K.sum() / d.H.sum(); sB = d.Bn.sum() / d.H.sum()
        uS = d.U / d.removed
        ref.append(dict(sg=sg, b_inzone=bK, b_outzone=bB, share_inzone=sK, share_outzone=sB, kappa_between=abs(bK) * sK + abs(bB - bK) * sB,
                        U_share_of_removed=d.U.sum() / d.removed.sum(), U_share_of_H=d.U.sum() / d.H.sum(),
                        U_price_corr=float(np.corrcoef(uS, d.x)[0, 1])))
        pd.DataFrame(rows).to_csv(f"{RES}/further_restrictions_bounds.csv", index=False)
        pd.DataFrame(ref).to_csv(f"{RES}/further_restrictions_reference.csv", index=False)
