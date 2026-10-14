"""Calibration scenario for movement (Section 4.2; Table 2 column D; Online Appendix Table C7;
(3)-(5): supplementary results, docs/supplementary_results.md).

(1) Identified sets with caps r_rho_j + lambda C_j, lambda in {0.5, 1, 1.5}, delta in {0.1, 0.2, 1}.
(2) lambda*: largest lambda in [0, 4] at which the lower bound is positive ([lo, hi] of the bisection).
(3) Origin caps: in addition, residents of i cast at most lambda * O_i in-zone early ballots at other
    stations, O_i = C_u * (trips from i to other dongs of its zone) / (all such trips in the zone).
(4) Alternative intercepts for the station cap: max(r_j, C_j) and r_j + C_j (main: r_rho_j + C_j).
(5) Stations where the calibrated inflow falls short of the movement the roll forces.
Calibration by early-voting day of the week is in assumptions/calibrated_dow.py.
Outputs: results/calibrated_{bounds,lamstar,origin,caps,failures}_<sg>.csv"""
import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix, vstack
from vwn.run import Prep, timer, elections_from_argv
from vwn.lp import JointLP, KMS
from vwn.bounds import total, breakdown
from vwn.data import norm, align_calib
from vwn.paths import RES, DATA, RAW, DERIVED

YM = {"20260603": "202605", "20250603": "202505", "20240410": "202404", "20220309": "202203"}


class OriginLP(JointLP):
    ocap = None

    def constraints(self, eta, delta):
        Aeq, beq, Aub, bub = super().constraints(eta, delta)
        if self.ocap is None: return Aeq, beq, Aub, bub
        n, C = self.n, self.C; ri, ci = [], []
        for i in range(n):
            for j in range(n):
                if i != j:
                    for c in range(C): ri.append(i); ci.append(self.iF(i, j, c))
        X = coo_matrix((np.ones(len(ri)), (ri, ci)), shape=(n, self.nv)).tocsr()
        return Aeq, beq, vstack([Aub, X]).tocsr(), np.concatenate([bub, eta * self.ocap])

    def config_key(self, eta, delta):
        return super().config_key(eta, delta) + (None if self.ocap is None else hash(self.ocap.tobytes()),)


def origin_caps(P, cal, od):
    caps = {}
    for u in P.units:
        c = align_calib(cal, P.G, [u])[u]
        codes = c.code.astype(str).str.replace(r"\.0$", "", regex=True).values; zones = c.zone.values
        O = np.zeros(len(c))
        for z in dict.fromkeys(zones):
            m = np.where(zones == z)[0]; zc = set(codes[m])
            out = np.array([od[(od.o == codes[i]) & (od.d.isin(zc)) & (od.d != codes[i])]["pop"].sum() for i in m])
            Cz = c.C_zone.iloc[m[0]]
            O[m] = Cz * out / out.sum() if out.sum() > 0 else Cz / len(m)
        caps[u] = O
    return caps


if __name__ == "__main__":
    B, LS, OR, CP, FL = [], [], [], [], []
    for sg in elections_from_argv(["20220309", "20240410", "20250603", "20260603"]):
        B, LS, OR, CP, FL = [], [], [], [], []
        log = timer(); P = Prep(sg); LP = P.lps(calib=True)
        for m in [0.5, 1.0, 1.5]:
            for dl in [1.0, 0.2, 0.1]:
                for sp in P.W:
                    lo, hi = total(P.units, LP, P.W[sp], m, dl); B.append(dict(sg=sg, mult=m, delta=dl, spec=sp, lo=lo, hi=hi))
        log(sg, "bounds")
        for sp in P.W:
            for dl in [0.1, 1.0]:
                a, b = breakdown(lambda l: total(P.units, LP, P.W[sp], l, dl)[0], 0.0, 4.0, 0.01)
                LS.append(dict(sg=sg, spec=sp, delta=dl, lo=a, hi=b))
        log(sg, "lambda*")
        cal = pd.read_csv(f"{DERIVED}/eta_calib_{sg}.csv")
        od = pd.read_csv(f"{RAW}/mobility/od_home_{YM[sg]}.csv", dtype={"o": str, "d": str}).groupby(["o", "d"], as_index=False)["pop"].sum()
        caps = origin_caps(P, cal, od); LPO = P.lps(calib=True, cls=OriginLP)
        for u in P.units: LPO[u].ocap = caps[u]
        for sp in P.W:
            for dl in [0.1, 1.0]:
                for lam in [1.0, 2.0]:
                    lo, hi = total(P.units, LPO, P.W[sp], lam, dl); lo0, hi0 = total(P.units, LP, P.W[sp], lam, dl)
                    OR.append(dict(sg=sg, spec=sp, delta=dl, lam=lam, lo_origin=lo, hi_origin=hi, lo_station=lo0, hi_station=hi0))
        log(sg, "origin caps")
        for cap in ["max(r, C)", "r + C", "r_rho + C (main)"]:
            LPv = P.lps(calib=True)
            for u in P.units:
                lp = LPv[u]; c = align_calib(cal, P.G, [u])[u]; K = lp.g["K"].sum(1)
                if cap == "max(r, C)": lp.ev = np.maximum(0, c.C_j.values - lp.r) / np.where(K > 0, K, 1); lp.r_cal = lp.r
                elif cap == "r + C": lp.r_cal = lp.r
            for sp in P.W:
                for s in [None, 0.02]:
                    for u in P.units: LPv[u].dF = None if s is None else ("slack", s)
                    lo, hi = total(P.units, LPv, P.W[sp], 1.0, 0.1); CP.append(dict(sg=sg, cap=cap, spec=sp, slack=s, lo=lo, hi=hi))
        log(sg, "cap variants")
        for r in cal.itertuples():
            if r.r > 0 and r.C_j < r.r: FL.append(dict(sg=sg, unit=r.unit, zone=r.zone, emd=r.emd, forced=r.r, calibrated=r.C_j, K=r.K))
        FL.append(dict(sg=sg, unit="ALL", zone="", emd="forced stations", forced=int((cal.r > 0).sum()), calibrated=int(((cal.r > 0) & (cal.C_j >= cal.r)).sum()), K=np.nan))
        for f, d in [("bounds", B), ("lamstar", LS), ("origin", OR), ("caps", CP), ("failures", FL)]:
            pd.DataFrame(d).to_csv(f"{RES}/calibrated_{f}_{sg}.csv", index=False)
