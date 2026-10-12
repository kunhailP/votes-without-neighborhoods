"""Calibration scenario for cross-dong early voting (Section 3.3; Online Appendix E).

Input: home-origin trips between administrative dongs on the early-voting weekdays, arrivals 06:00-17:59
(data/raw/mobility/od_home_<yyyymm>.csv, extracted from Seoul Living Mobility by build/mobility_extract.py).

Assumption: early voters vote near the destination of their home-based daytime trip, so for in-district
zone u the ratio of cross-dong in-zone early ballots to out-of-zone (pooled) early ballots equals
  R_u = W_u / X_u,  W_u = trips from u to another dong of u,  X_u = trips leaving u.
Implied cross-dong early ballots C_u = R_u * B_u, where B_u is the number of out-of-district early ballots
of zone u, distributed over the stations of u in proportion to their inflow from other dongs of u (C_j).
The cap at station j is r_rho_j + lambda * C_j (vwn.lp.JointLP with ev_j = C_j / K_j).

Zones. 2022, 2025: gu; 2024: constituency where a gu holds two or more; 2026: gu council constituency.
For 2026, B_u is the constituency's out-of-district early headcount published in the council contest
(data/council_pooled_20260603.csv), scaled to counted mayoral ballots; for uncontested constituencies,
which have no council returns, the gu residual is split in proportion to removed residents not voting
at an in-district station (E - D - K).

Output: data/derived/eta_calib_<sg>.csv (station level), data/derived/eta_calib_summary.csv
Usage: python build/mobility_calibration.py [--no-zones] <sg> ..."""
import sys
import numpy as np
import pandas as pd
from vwn.data import setup, norm
from vwn.paths import DATA, RAW, DERIVED, RES

YM = {"20260603": "202605", "20250603": "202505", "20240410": "202404", "20220309": "202203"}


def calibrate(sg, zones=True, mult=1.0):
    od = pd.read_csv(f"{RAW}/mobility/od_home_{YM[sg]}.csv", dtype={"o": str, "d": str})
    od = od.groupby(["o", "d"], as_index=False)["pop"].sum()
    cw = pd.read_csv(f"{DATA}/kt_code_crosswalk_{sg}.csv", dtype={"code": str})
    cw["code"] = cw.code.str.replace(r"\.0$", "", regex=True)
    code_of = {(r.unit, norm(r.emd)): r.code for r in cw.itertuples() if isinstance(r.code, str)}
    units, G, idx, x, labs = setup(sg, zones=zones)
    pc = pd.read_csv(f"{DATA}/council_pooled_{sg}.csv") if zones and "zone" in G[units[0]][0] else None
    # Seoul Living Mobility uses an older dong system in a few places: one KT code can cover two election dongs
    # (Sangil 1/2, Oryu 2 and Hang, Sinseol and Yongdu). Trips of such a code are split between its dongs in proportion
    # to their certified electorates, at both ends; trips between dongs that share a code cannot be observed.
    members = {}
    for u in units:
        g, E = G[u]; zl = g.get("zone", np.array([u] * len(g["emds"])))
        for em, z, e in zip(g["emds"], zl, E):
            c = code_of.get((u, norm(em)))
            if c: members.setdefault(c, []).append(((u, em), (u, z), float(e)))
    dong_rows = [(c, key, zone, e / sum(m[2] for m in mem)) for c, mem in members.items() for key, zone, e in mem]
    dmap = pd.DataFrame(dong_rows, columns=["code", "key", "zone", "w"])
    od = od.merge(dmap.rename(columns={"code": "o", "key": "ko", "zone": "zo", "w": "wo"}), on="o")
    od = od.merge(dmap.rename(columns={"code": "d", "key": "kd", "zone": "zd", "w": "wd"}), on="d", how="left")
    od["wd"] = od.wd.fillna(1.0); od["pop"] = od["pop"] * od.wo * od.wd
    rows = []
    for u in units:
        g, E = G[u]; n = len(g["emds"]); zl = g.get("zone", np.array([u] * n))
        K = g["K"].sum(1); ED = E - g["D"]; r = np.maximum(0, K - ED)
        codes = [code_of.get((u, norm(em))) for em in g["emds"]]
        # out-of-district early ballots by zone
        Btot = g["Bc"].sum(); Bz = {}
        if pc is not None:
            q = pc[pc.gu == u]; scale = g["out_votes"] / g["out_elig"]
            known = {rr.council: rr.out_elig * scale for rr in q[q.out_elig.notna()].itertuples()}
            rest = [z for z in dict.fromkeys(zl) if z not in known]
            resid = Btot - sum(known.values()); base = {z: max(ED[zl == z].sum() - K[zl == z].sum(), 0) for z in rest}
            Bz = {**known, **{z: resid * base[z] / max(sum(base.values()), 1) for z in rest}}
        else:
            Bz = {z: Btot for z in dict.fromkeys(zl)}
        for z in dict.fromkeys(zl):
            m = np.where(zl == z)[0]
            q = od[od.zo == (u, z)]
            Wz = q[(q.zd == (u, z)) & (q.o != q.d)]["pop"].sum(); Xz = q[q.zd != (u, z)]["pop"].sum(); Sz = q[q.o == q.d]["pop"].sum()
            R = Wz / Xz if Xz > 0 else 0.0
            # a multi-dong zone whose dongs all share one KT code: movement inside it is unobservable, R is imputed below
            unobs = len(m) > 1 and len({codes[i] for i in m}) == 1
            Cu = mult * R * Bz[z]
            inflow = np.array([q[(q.kd == (u, g["emds"][i])) & (q.o != q.d)]["pop"].sum() if codes[i] else 0.0 for i in m])
            share = inflow / inflow.sum() if inflow.sum() > 0 else np.ones(len(m)) / len(m)
            for k, i in enumerate(m):
                Cj = Cu * share[k]
                rows.append(dict(sg=sg, unit=u, zone=z, emd=g["emds"][i], code=codes[i], K=K[i], r=r[i], C_j=Cj,
                                 eta_j=Cj / K[i] if K[i] > 0 else 0.0, R_zone=R, B_zone=Bz[z], C_zone=Cu,
                                 same_dong=Sz, cross_dong=Wz, out_zone=Xz, R_imputed=unobs))
    d = pd.DataFrame(rows)
    if d.R_imputed.any():   # median R of the zones with two or more observable dongs
        zs = d.groupby(["unit", "zone"]).agg(R=("R_zone", "first"), n=("emd", "size"), imp=("R_imputed", "first"))
        Rm = zs[(zs.n > 1) & ~zs.imp].R.median(); i = d.R_imputed
        d.loc[i, "R_zone"] = Rm; d.loc[i, "C_zone"] = mult * Rm * d.loc[i, "B_zone"]
        d.loc[i, "C_j"] = d.loc[i, "C_zone"] / d[i].groupby(["unit", "zone"]).emd.transform("size")
        d.loc[i, "eta_j"] = np.where(d.loc[i, "K"] > 0, d.loc[i, "C_j"] / d.loc[i, "K"].where(d.loc[i, "K"] > 0, 1), 0.0)
    # restore the dong order of each unit (the LP order)
    order = {(u, em): k for k, (u, em) in enumerate(idx)}
    d["_o"] = [order[(a, b)] for a, b in zip(d.unit, d.emd)]
    return d.sort_values("_o").drop(columns="_o").reset_index(drop=True)


if __name__ == "__main__":
    args = sys.argv[1:]; zones = "--no-zones" not in args; sgs = [a for a in args if not a.startswith("--")]
    summ = []
    for sg in sgs:
        d = calibrate(sg, zones)
        d.to_csv(f"{DERIVED}/eta_calib_{sg}{'' if zones else '_nozones'}.csv", index=False)
        zz = d.groupby(["unit", "zone"]).agg(R=("R_zone", "first"), C=("C_zone", "first"), K=("K", "sum"))
        zz["eta_zone"] = zz.C / zz.K
        summ.append(dict(sg=sg, zones=zones, n_zones=len(zz), R_med=zz.R.median(), R_min=zz.R.min(), R_max=zz.R.max(),
                         eta_zone_med=zz.eta_zone.median(), eta_station_med=d.eta_j.median(), eta_station_p90=d.eta_j.quantile(0.9),
                         eta_station_max=d.eta_j.max(), forced=int((d.r > 0).sum()), forced_covered=int(((d.r > 0) & (d.C_j >= d.r)).sum())))
        print(summ[-1], flush=True)
    if zones:
        pd.DataFrame(summ).to_csv(f"{DERIVED}/eta_calib_summary.csv", index=False)
