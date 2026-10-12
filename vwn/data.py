"""Loading the analysis files: one LP block per counting jurisdiction, dong regressors and OLS weights."""
import os
import numpy as np
import pandas as pd
from .lp import CANDS
from .paths import DATA

ELECTIONS = ["20121219", "20170509", "20220309", "20240410", "20250603", "20260603"]
YEAR = {"20121219": "2012", "20170509": "2017", "20220309": "2022", "20240410": "2024", "20250603": "2025", "20260603": "2026"}
norm = lambda s: s.replace("제", "").replace(".", "·")


def load_gu(d, e, gu):
    """Observed counts for one jurisdiction (gu, or constituency in 2024)."""
    dd = d[d.gu == gu]
    inn = dd[dd.unit == "IN"].set_index("emd"); day = dd[dd.unit == "DAY"].set_index("emd")
    emds = list(inn.index)
    A = day.loc[emds, CANDS].values.astype(float); K = inn.loc[emds, CANDS].values.astype(float)
    Avotes = day.loc[emds, "votes"].values.astype(float); D = day.loc[emds, "elig"].values.astype(float)
    X = dd[dd.unit == "X"].set_index("emd")
    out = X.loc["관외사전투표"]; geo = X.loc["거소·선상투표"]; ab = X.loc["재외투표"]
    Bc = out[CANDS].values.astype(float); Gc = (geo[CANDS].values + ab[CANDS].values).astype(float)
    U_raw = float(out.abstain + geo.abstain + ab.abstain)
    E = e[(e.gu == gu) & (e.emd != "합계")].set_index("emd").loc[emds, "cfmtnElcnt"].values.astype(float)
    Ks = K.sum(1, keepdims=True); As = A.sum(1, keepdims=True)
    # station anchor K_ic / K_i; with no in-zone early voting (2012, K_i = 0) the election-day
    # composition is used instead (non-binding there, since delta = 1 in every 2012 cell)
    a_tilde = np.where(Ks > 0, K / np.where(Ks > 0, Ks, 1), A / np.where(As > 0, As, 1))
    # U closes the roll identity exactly: removed residents with no counted ballot (incl. in-zone early abstentions)
    U = float((E - D).sum() - K.sum() - Bc.sum() - Gc.sum())
    g = dict(emds=emds, A=A, K=K, Avotes=Avotes, D=D, Bc=Bc, Gc=Gc, U=U, U_raw=U_raw, a_tilde=a_tilde,
             out_elig=float(out.elig), out_votes=float(out.votes), home_elig=float(geo.elig), home_votes=float(geo.votes))
    return g, E


def weights(x, gu_of, fe, m=None):
    """OLS slope weights: theta = sum_i w_i y_i. fe=True demeans x within groups gu_of. m: optional frequency weights."""
    x = np.asarray(x, float); m = np.ones(len(x)) if m is None else np.asarray(m, float)
    if fe:
        xc = np.zeros(len(x)); gs = np.asarray(gu_of)
        for g_ in np.unique(gs):
            s = gs == g_
            if m[s].sum() > 0: xc[s] = x[s] - np.average(x[s], weights=m[s])
    else:
        xc = x - np.average(x, weights=m)
    return m * xc / (m * xc ** 2).sum()


def split(units, G, w):
    """Split a stacked vector into per-jurisdiction pieces."""
    out = {}; pos = 0
    for u in units:
        n = len(G[u][0]["emds"]); out[u] = w[pos:pos + n]; pos += n
    return out


def setup(sg, zones=True, headcounts=False):
    """Return units, G = {unit: (g, E)}, idx = [(unit, dong)], log price x, fixed-effect labels.

    zones=True imposes the statutory early-voting zone where it is narrower than the counting
    jurisdiction (2026: gu council constituencies). headcounts=True adds the 2026 cross-contest
    headcount ranges for out-of-zone and at-home ballots by council constituency."""
    if sg == "20250603":
        d = pd.read_csv(f"{DATA}/seoul_2025pres_emd.csv"); e = pd.read_csv(f"{DATA}/seoul_2025pres_electorate_api.csv")
        h = pd.read_csv(f"{DATA}/seoul_hdong_aptprice_202406_202505.csv"); price = dict(zip(h.gu + "|" + h.hdong.map(norm), h.med_per_m2))
        key = lambda u, emd: u + "|" + norm(emd); fe_lab = lambda u, emd: u
    elif sg == "20240410":
        d = pd.read_csv(f"{DATA}/seoul_{sg}_emd.csv"); e = pd.read_csv(f"{DATA}/seoul_{sg}_electorate_bysgg.csv")
        h = pd.read_csv(f"{DATA}/seoul_hdong_aptprice_{sg}.csv").dropna(subset=["price_med"])
        price = {norm(r.emd) + ("|" + r.gu if r.emd == "신사동" else ""): r.price_med for r in h.itertuples()}
        rg = dict(zip(e.gu + "|" + e.emd, e.realgu))
        key = lambda u, emd: norm(emd) + ("|" + rg[u + "|" + emd] if emd == "신사동" else ""); fe_lab = lambda u, emd: rg[u + "|" + emd]
    else:
        d = pd.read_csv(f"{DATA}/seoul_{sg}_emd.csv"); e = pd.read_csv(f"{DATA}/seoul_{sg}_electorate_api.csv")
        h = pd.read_csv(f"{DATA}/seoul_hdong_aptprice_{sg}.csv").dropna(subset=["price_med"]); price = dict(zip(h.gu + "|" + h.emd.map(norm), h.price_med))
        key = lambda u, emd: u + "|" + norm(emd); fe_lab = lambda u, emd: u
    units = sorted(d.gu.unique()); G = {u: load_gu(d, e, u) for u in units}
    cf = f"{DATA}/council_{sg}.csv"
    if zones and os.path.exists(cf):
        cm = pd.read_csv(cf); cmap = {(r.gu, norm(r.emd)): r.council for r in cm.itertuples()}
        for u in units:
            g = G[u][0]; z = [cmap.get((u, norm(em))) for em in g["emds"]]
            missing = [em for em, v in zip(g["emds"], z) if v is None]
            if missing: raise ValueError(f"council map missing: {u} {missing}")
            g["zone"] = np.array(z); g["allow"] = g["zone"][:, None] == g["zone"][None, :]
        if headcounts:
            pc = pd.read_csv(f"{DATA}/council_pooled_{sg}.csv")
            for u in units:
                g = G[u][0]; q = pc[pc.gu == u]
                sP = g["out_elig"] - g["out_votes"]; sQ = g["home_elig"] - g["home_votes"]   # unreturned/uncounted, gu level
                groups = []; resid = np.ones(len(g["emds"]), bool); eP = eQ = 0.0
                for r in q[q.out_elig.notna()].itertuples():
                    ix = np.where(g["zone"] == r.council)[0]; resid[ix] = False; eP += r.out_elig; eQ += r.home_elig
                    groups.append((ix, max(r.out_elig - sP, 0), r.out_elig, max(r.home_elig - sQ, 0), r.home_elig))
                if resid.any():   # uncontested constituencies: published only as the gu residual
                    rP = g["out_elig"] - eP; rQ = g["home_elig"] - eQ
                    groups.append((np.where(resid)[0], max(rP - sP, 0), rP, max(rQ - sQ, 0), rQ))
                g["pool_groups"] = groups
    idx = [(u, emd) for u in units for emd in G[u][0]["emds"]]
    x = np.array([np.log(price.get(key(u, emd), np.nan)) for u, emd in idx])
    labs = {"guFE": np.array([fe_lab(u, emd) for u, emd in idx])}
    if sg == "20240410": labs["sggFE"] = np.array([u for u, _ in idx])
    return units, G, idx, x, labs


def make_lp(g, E, cls=None, ev=None, dF=None, headcounts=None):
    """Construct a JointLP (or subclass) and attach zone-specific options carried in g."""
    from .lp import JointLP
    lp = (cls or JointLP)(g, E)
    lp.ev = ev; lp.dF = dF
    if headcounts is None: headcounts = "pool_groups" in g
    if headcounts and "pool_groups" in g: lp.pool_groups = g["pool_groups"]
    return lp


def slope_weights(sg, x, labs, specs=None):
    """{spec: stacked weight vector} for pooled (city-wide) and fixed-effect specifications."""
    has = ~np.isnan(x); W = {}
    for sp in (specs or (["pooled", "guFE"] + (["sggFE"] if "sggFE" in labs else []))):
        w = np.zeros(len(x))
        if sp == "pooled": w[has] = weights(x[has], labs["guFE"][has], False)
        else: w[has] = weights(x[has], labs[sp][has], True)
        W[sp] = w
    return W


def align_calib(cal, G, units):
    """Rows of a calibration table (build/mobility_calibration.py) for each unit, in the dong order of G[u] (the LP's order).
    Matching is by dong name, never by row order: the file's row order need not follow the LP's."""
    out = {}
    for u in units:
        c = cal[cal.unit == u].set_index("emd"); emds = list(G[u][0]["emds"])
        missing = set(emds) - set(c.index)
        if missing or len(c) != len(emds): raise ValueError(f"calibration rows do not match the dongs of {u}: missing {sorted(missing)}")
        out[u] = c.loc[emds].reset_index()
    return out
