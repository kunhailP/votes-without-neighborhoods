"""A published allocation and the identified set (Section 4.2; Online Appendix D, Tables D1, D2).

(1) Re-implements the allocation of a widely circulated analysis of the 2026 election (Lee 2026): residents'
    pooled-mode counts from the roll difference (at-home counts in proportion to registered at-home voters),
    out-of-zone ballots at the dong's in-zone early composition, at-home ballots at the dong's overall
    composition, columns rescaled to the gu x candidate totals and integers restored by largest remainder;
    price = mean price per pyeong (10 million won). Reports the correlations and the within-gu slope.
(2) Admissibility: with its dong-level pooled ballots fixed, is the allocation consistent with (R), (S) and the
    statutory zones? eta_min per gu = smallest uniform movement allowance that makes it feasible (bisection).
    Also the smallest feasible station-anchor band delta_min at eta = 10 (its premise holds exactly only if 0).
(3) Identified sets on the published scale (pp per 10 million won per pyeong), for the published specifications
    (gu FE, pooled, gu FE + age, trimmed), z and valid-vote y brackets.
Outputs: results/published_allocation.csv (dong level), results/published_admissibility.csv,
results/published_zone_check.csv, results/published_scale.csv"""
import numpy as np
import pandas as pd
from vwn.run import Prep, timer
from vwn.data import norm, make_lp, weights
from vwn.lp import CANDS, KMS, INV
from vwn.bounds import total
from vwn.ytight import CLP, run_cells
from vwn.paths import DATA, RES

sg = "20260603"; log = timer(); P = Prep(sg)
e = pd.read_csv(f"{DATA}/seoul_{sg}_electorate_api.csv")
h = pd.read_csv(f"{DATA}/seoul_hdong_aptprice_{sg}.csv"); h = h[h.price_mean.notna()]
pm = dict(zip(h.gu + "|" + h.emd.map(norm), h.price_mean * 3.3058 / 1000))   # 10k won/m2 -> 10m won/pyeong


def lrm(target, raw):
    raw = np.maximum(raw, 0); s = raw.sum()
    if target == 0 or s == 0: return np.zeros_like(raw)
    x = raw / s * target; fl = np.floor(x); r = int(round(target - fl.sum()))
    fl[np.lexsort((np.arange(len(x)), -(x - fl)))[:r]] += 1; return fl


rows = []; pools = {}
for u in P.units:
    g, E = P.G[u]; n = len(g["emds"])
    ee = e[(e.gu == u) & (e.emd != "합계")].set_index("emd").loc[g["emds"]]
    rdv = ee["cfmtnRdvtDccnt"].values.astype(float) if "cfmtnRdvtDccnt" in ee else np.ones(n)
    M = np.maximum(E - g["D"] - g["K"].sum(1), 0)
    Gn = g["Gc"].sum() * rdv / rdv.sum() if rdv.sum() > 0 else np.zeros(n)
    On = np.maximum(M - Gn, 0); On = On / On.sum() * g["Bc"].sum()
    mix = (g["A"] + g["K"]) / (g["A"] + g["K"]).sum(1, keepdims=True)
    B = np.column_stack([lrm(g["Bc"][c], On * g["a_tilde"][:, c]) for c in range(len(CANDS))])
    Gx = np.column_stack([lrm(g["Gc"][c], Gn * mix[:, c]) for c in range(len(CANDS))])
    pools[u] = (B, Gx); N = g["A"] + g["K"] + B + Gx
    dev = np.abs(B / np.maximum(B.sum(1, keepdims=True), 1) - g["a_tilde"])[B.sum(1) > 0]
    for i, em in enumerate(g["emds"]):
        rows.append(dict(gu=u, emd=em, price=pm.get(u + "|" + norm(em), np.nan), share_valid=N[i, KMS] / (N[i].sum() - N[i, INV]),
                         share_total=N[i, KMS] / N[i].sum(), B_out=B[i].sum(), G_home=Gx[i].sum(), anchor_dev_gu_max=dev.max()))
r = pd.DataFrame(rows); r.to_csv(f"{RES}/published_allocation.csv", index=False)
q = r.dropna(subset=["price"]); dm = q.groupby("gu")[["price", "share_valid"]].transform(lambda s: s - s.mean())
summary = dict(n=len(q), r_city=np.corrcoef(q.price, q.share_valid)[0, 1], r_within=np.corrcoef(dm.price, dm.share_valid)[0, 1],
               slope_within_pp=np.polyfit(dm.price, dm.share_valid, 1)[0] * 100)
log("re-implementation", {k: round(v, 3) for k, v in summary.items()})

adm = []
P0 = Prep(sg, zones=False)
for u in P.units:
    g, E = P.G[u]; B, Gx = pools[u]
    lp = make_lp(g, E); lp.Bfix, lp.Gfix = B, Gx
    lpz = make_lp(*P0.G[u]); lpz.Bfix, lpz.Gfix = B, Gx       # no zone restriction: movement anywhere in the gu
    emin_nozone = np.inf
    if lpz.feasible(1.0, 1.0):
        a_, b_ = 0.0, 1.0
        if lpz.feasible(0.0, 1.0): b_ = 0.0
        while b_ - a_ > 1e-3:
            m_ = (a_ + b_) / 2
            if lpz.feasible(m_, 1.0): b_ = m_
            else: a_ = m_
        emin_nozone = b_
    if lp.feasible(0.0, 1.0): emin = 0.0
    elif not lp.feasible(1.0, 1.0): emin = np.inf
    else:
        a, b = 0.0, 1.0
        while b - a > 1e-3:
            m = (a + b) / 2
            if lp.feasible(m, 1.0): b = m
            else: a = m
        emin = b
    lp0 = make_lp(g, E)
    adm.append(dict(gu=u, eta_min=emin, eta_min_nozones=emin_nozone, delta_min_eta10=lp0.delta_min(10.0),
                    out_minus_in_early_cons=g["Bc"][KMS] / g["Bc"].sum() - g["K"][:, KMS].sum() / g["K"].sum(),
                    implied_anchor_dev=np.median(np.abs(B / np.maximum(B.sum(1, keepdims=True), 1) - g["a_tilde"])[B.sum(1) > 0][:, KMS])))
adm = pd.DataFrame(adm); adm.to_csv(f"{RES}/published_admissibility.csv", index=False)
log("admissibility: infeasible at eta=0 in", int((adm.eta_min > 0).sum()), "gu; max eta_min", adm.eta_min.max(),
    "| without zones: infeasible at eta=0 in", int((adm.eta_min_nozones > 0).sum()), "max", adm.eta_min_nozones.max())
# zone-level accounting: pooled + non-voters of a council constituency = its removed residents - its station ballots
zr = []; pc = pd.read_csv(f"{DATA}/council_pooled_{sg}.csv")
for u in P.units:
    g, E = P.G[u]; B, Gx = pools[u]; ED = E - g["D"]; K = g["K"].sum(1)
    for z in dict.fromkeys(g["zone"]):
        m = g["zone"] == z; c = pc[(pc.gu == u) & (pc.council == z)]
        zr.append(dict(gu=u, zone=z, removed_minus_station=ED[m].sum() - K[m].sum(), alloc_pooled=B[m].sum() + Gx[m].sum(),
                       alloc_out=B[m].sum(), council_out=c.out_elig.iloc[0] if len(c) else np.nan))
zr = pd.DataFrame(zr); zr["excess"] = zr.alloc_pooled - zr.removed_minus_station; zr.to_csv(f"{RES}/published_zone_check.csv", index=False)

# published-scale specifications (FWL weights, optional age control, trimming on mean price)
ag = pd.read_csv(f"{DATA}/seoul_hdong_age_202604.csv"); age = dict(zip(ag.gu + "|" + ag.emd.map(norm), ag.mean_age18))
key = [u + "|" + norm(em) for u, em in P.idx]; lab = np.array([u for u, _ in P.idx])
x = np.array([pm.get(k, np.nan) for k in key]); a = np.array([age.get(k, np.nan) for k in key])


def fwl_w(mask, use_age, fe=True):
    X = [np.ones(mask.sum())] + ([a[mask]] if use_age else []) + ([(lab[mask] == u).astype(float) for u in P.units[1:]] if fe else [])
    X = np.column_stack(X); xr = x[mask] - X @ np.linalg.lstsq(X, x[mask], rcond=None)[0]
    w = np.zeros(len(x)); w[mask] = xr / (xr ** 2).sum(); return w


has = ~np.isnan(x); base = has & ~np.isnan(a); q90, q95 = np.nanquantile(x, 0.9), np.nanquantile(x, 0.95)
W = {"gu FE": fwl_w(has, False), "pooled": fwl_w(has, False, fe=False), "gu FE + age": fwl_w(base, True),
     "gu FE, excl. top 5%": fwl_w(base & (x <= q95), False), "gu FE, excl. top 10%": fwl_w(base & (x <= q90), False),
     "gu FE + age, excl. top 10%": fwl_w(base & (x <= q90), True)}
yhk = np.array([dict(zip(r.gu + "|" + r.emd.map(norm), r.share_valid)).get(k, np.nan) for k in key])
rows = []
CL = {u: CLP(lp) for u, lp in P.lps().items()}
Wsplit = {k: P.wsplit(w) for k, w in W.items()}
for rr in run_cells(sg, P.units, CL, Wsplit, [(1.0, 1.0), (0.0, 1.0), (0.0, 0.1), (0.05, 0.1), (0.1, 0.1), (0.0, 0.2), (0.05, 0.2)], scale=100.0, log=lambda *a: None):
    rows.append(dict(movement="uniform", **rr))
log("published scale, uniform")
for s in [None, 0.02]:
    CLc = {u: CLP(lp) for u, lp in P.lps(calib=True, dF=None if s is None else ("slack", s)).items()}
    for rr in run_cells(sg, P.units, CLc, Wsplit, [(1.0, 0.1), (1.0, 1.0)], scale=100.0, log=lambda *a: None):
        rows.append(dict(movement="calib", slack=s, **rr))
log("published scale, calibrated")
d = pd.DataFrame(rows)
d["published_point"] = d.spec.map({k: float(np.nansum(w * np.nan_to_num(yhk))) * 100 for k, w in W.items()})
for k, v in summary.items(): d[k] = v
d.to_csv(f"{RES}/published_scale.csv", index=False)
