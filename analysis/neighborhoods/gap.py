"""Is the residents' early-composition benchmark mis-centered? (Sections 1 and 4.5; Table 2 column F; Online Appendix Table C8)

(1) Tests of the common early-vote gap with the jurisdiction-level gaps, which are observed exactly:
    gamma^K_g (in-zone early - election day) and gamma^P_g (out-of-zone early - election day),
    regressed on the jurisdiction's log price and share aged 60+; and stations' departures from the
    benchmark within gu (an imperfect proxy, since stations mix residents and movers).
(2) Bounds when the benchmark is shifted within each jurisdiction by beta_x (x_i - xbar_g) + beta_a (a_i - abar_g),
    with the opposite shift for the Democratic candidate.
Outputs: results/gap_test_{gu,dong,reg}.csv, results/gap_adjusted.csv"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from vwn.run import Prep, timer
from vwn.data import norm
from vwn.lp import JointLP, KMS, CANDS
from vwn.bounds import total
from vwn.paths import DATA, RES

LJM = CANDS.index("LJM")
age = pd.read_csv(f"{DATA}/seoul_hdong_age_202604.csv"); age["k"] = age.gu + "|" + age.emd.map(norm)
amap = dict(zip(age.k, zip(age.share60, age.pop18)))


class GapLP(JointLP):
    shift = None

    def ref(self):
        r = super().ref()
        if self.shift is None: return r
        g = self.g; A = g["A"]; K = g["K"]
        day = A / np.maximum(A.sum(1, keepdims=True), 1); gap = K.sum(0) / max(K.sum(), 1) - A.sum(0) / A.sum()
        ref = day + gap; ref[:, KMS] += self.shift; ref[:, LJM] -= self.shift
        return np.clip(ref, 0, 1)

    def config_key(self, eta, delta):
        return super().config_key(eta, delta) + (None if self.shift is None else hash(np.asarray(self.shift).tobytes()),)


if __name__ == "__main__":
    log = timer(); GU, DG = [], []; PREP = {}
    for sg in ["20170509", "20220309", "20240410", "20250603", "20260603"]:
        P = PREP[sg] = Prep(sg); rg = P.labs["guFE"]; pos = 0
        for u in P.units:
            g, E = P.G[u]; n = len(g["emds"]); xs = P.x[pos:pos + n]; gus = rg[pos:pos + n]; pos += n
            A, K = g["A"], g["K"]; day = A[:, KMS].sum() / A.sum(); kin = K[:, KMS].sum() / K.sum(); out = g["Bc"][KMS] / g["Bc"].sum()
            s60 = np.array([amap.get(gg + "|" + norm(e), (np.nan, np.nan))[0] for gg, e in zip(gus, g["emds"])])
            p18 = np.array([amap.get(gg + "|" + norm(e), (np.nan, np.nan))[1] for gg, e in zip(gus, g["emds"])])
            H = g["Avotes"] + E - g["D"]; ok = ~np.isnan(xs)
            GU.append(dict(sg=sg, unit=u, gamK=kin - day, gamB=out - day, x=np.average(xs[ok], weights=H[ok]),
                           s60=np.nansum(s60 * p18) / np.nansum(p18 * ~np.isnan(s60)), H=H.sum()))
            dev = K[:, KMS] / np.maximum(K.sum(1), 1) - (A[:, KMS] / np.maximum(A.sum(1), 1) + (kin - day))
            for i in range(n): DG.append(dict(sg=sg, unit=u, emd=g["emds"][i], dev=dev[i], x=xs[i], s60=s60[i], K=K[i].sum()))
    gu = pd.DataFrame(GU); dg = pd.DataFrame(DG)
    gu.to_csv(f"{RES}/gap_test_gu.csv", index=False); dg.to_csv(f"{RES}/gap_test_dong.csv", index=False)
    R = []
    def add(name, m, terms):
        for t in terms: R.append(dict(model=name, term=t, coef=m.params[t], se=m.bse[t], p=m.pvalues[t], n=int(m.nobs)))
    for dep in ["gamK", "gamB"]:
        for sg in gu.sg.unique():
            q = gu[gu.sg == sg]
            for f, nm in [(f"{dep} ~ x", "x"), (f"{dep} ~ s60", "s60"), (f"{dep} ~ x + s60", "x+s60")]:
                m = smf.ols(f, q).fit(cov_type="HC3"); add(f"gu {dep} {nm} {sg}", m, [t for t in ["x", "s60"] if t in m.params])
    d2 = dg.dropna(subset=["x", "s60"])
    for f, nm in [("dev ~ x + C(unit)", "x"), ("dev ~ s60 + C(unit)", "s60"), ("dev ~ x + s60 + C(unit)", "x+s60")]:
        for sg in sorted(d2.sg.unique()):
            q = d2[d2.sg == sg]; m = smf.wls(f, q, weights=q.K).fit(cov_type="cluster", cov_kwds={"groups": q.unit.astype("category").cat.codes})
            add(f"dong dev {nm} {sg}", m, [t for t in ["x", "s60"] if t in m.params])
    reg = pd.DataFrame(R); reg.to_csv(f"{RES}/gap_test_reg.csv", index=False); log("tests")

    def coef(model, term):
        q = reg[(reg.model == model) & (reg.term == term)].iloc[0]; return q.coef, q.se
    rows = []
    for sg in ["20260603", "20240410", "20220309", "20250603"]:
        P = PREP[sg]; rg = P.labs["guFE"]
        a = np.array([amap.get(gg + "|" + norm(e), (np.nan, np.nan))[0] for gg, (u, e) in zip(rg, P.idx)])
        unit_arr = np.array([u for u, _ in P.idx])
        xd = np.nan_to_num(P.x - pd.Series(P.x).groupby(unit_arr).transform("mean").values)
        ad = np.nan_to_num(a - pd.Series(a).groupby(unit_arr).transform("mean").values)
        bx, sx = coef(f"gu gamK x+s60 {sg}", "x"); ba, sa = coef(f"gu gamK x+s60 {sg}", "s60")
        dx, _ = coef(f"dong dev x+s60 {sg}", "x"); da, _ = coef(f"dong dev x+s60 {sg}", "s60")
        variants = {"common gap (baseline)": None, "gu-level price slope": bx * xd, "gu-level price slope, CI low": (bx - 1.96 * sx) * xd,
                    "gu-level price slope, CI high": (bx + 1.96 * sx) * xd, "gu-level price and age": bx * xd + ba * ad,
                    "station-level price and age": dx * xd + da * ad}
        for vn, sh in variants.items():
            for s in [None, 0.02, 0.05]:
                if s is None and sh is not None: continue
                LP = P.lps(calib=True, dF=None if s is None else ("slack", s), cls=GapLP)
                if sh is not None:
                    sp_ = P.wsplit(sh)
                    for u in P.units: LP[u].shift = sp_[u]
                for spn in P.W:
                    lo, hi = total(P.units, LP, P.W[spn], 1.0, 0.1)
                    rows.append(dict(sg=sg, variant=vn, slack=s, spec=spn, beta_x=None if sh is None else (bx if "gu-level" in vn else dx), lo=lo, hi=hi))
            log(sg, vn)
            pd.DataFrame(rows).to_csv(f"{RES}/gap_adjusted.csv", index=False)
