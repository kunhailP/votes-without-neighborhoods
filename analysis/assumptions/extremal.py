"""What a sign reversal requires (Section 4.5; Table C14; Online Appendix Table C16).

Setting: within-gu slope, calibrated movement (lambda = 1), out-of-zone band delta, residents' in-zone
early composition unrestricted.

(1) Lower-bound allocation: the allocation that attains the minimum slope, described by the price tercile of
    residents' home dongs: share of their in-zone early ballots cast at another dong's station, movers'
    and stayers' conservative shares, residents' early conservative share against the benchmark a^F and
    the station share.
(2) Least-departure reversal: among allocations with a non-positive slope, the one that minimizes the total
    departure of residents' in-zone early conservative ballots from the benchmark,
        min sum_i |D_i|,  D_i = sum_j F_{i j KMS} - a^F_{i KMS} sum_{j,c} F_{ijc},  s.t. theta(w) <= 0.
    Jurisdictions are coupled only through theta <= 0, so this is one LP over the block-diagonal union of the
    jurisdictions' polytopes. Its value is the smallest number of residents' early ballots whose candidate
    must differ from the benchmark composition for the sign to reverse; it is compared with the stations'
    own departure sum_i |K_{i KMS} - a^F_{i KMS} K_i| and with the departure at the lower-bound allocation.
    If the unrestricted lower bound is positive, no allocation reverses the sign and (2) is infeasible.
Outputs: results/extremal_profile.csv ((1); supplementary results, docs/supplementary_results.md), results/least_departure.csv,
results/least_departure_detail.csv"""
import numpy as np
import pandas as pd
from scipy.sparse import block_diag, coo_matrix, vstack, hstack, csr_matrix
from scipy.optimize import linprog
from vwn.run import Prep, timer, elections_from_argv
from vwn.bounds import slope_c
from vwn.lp import KMS, HS_OPTS
from vwn.paths import RES


def describe(P, LP, sols, w_all, label):
    """Per-dong records for an allocation {unit: x}."""
    recs = []; pos = 0
    for u in P.units:
        lp = LP[u]; g = lp.g; n = lp.n; F, B, G, U = lp.state(sols[u]); ref = lp.ref()
        xs = P.x[pos:pos + n]; pos += n
        for i in range(n):
            own = F[i, i]; mov = F[i].sum(0) - own; res = F[i].sum(0)
            recs.append(dict(alloc=label, unit=u, emd=g["emds"][i], x=xs[i], res_tot=res.sum(), res_cons=res[KMS], mov_tot=mov.sum(), mov_cons=mov[KMS],
                             own_tot=own.sum(), own_cons=own[KMS], ref_cons=ref[i, KMS], at_cons=g['a_tilde'][i, KMS], st_tot=g["K"][i].sum(), st_cons=g["K"][i, KMS],
                             B_tot=B[i].sum(), B_cons=B[i, KMS], G_tot=G[i].sum(), G_cons=G[i, KMS]))
    return recs


def terciles(d):
    d_all = d.copy(); d_all["dep"] = d_all.res_cons - d_all.ref_cons * d_all.res_tot
    d = d[~d.x.isna()].copy()
    d["tercile"] = pd.qcut(d.x, 3, labels=["low", "mid", "high"])
    d["dep"] = d.res_cons - d.ref_cons * d.res_tot
    out = []
    for t, q in d.groupby("tercile", observed=True):
        out.append(dict(tercile=t, n_dongs=len(q), move_share=q.mov_tot.sum() / q.res_tot.sum(), mover_cons=q.mov_cons.sum() / max(q.mov_tot.sum(), 1e-9),
                        stayer_cons=q.own_cons.sum() / q.own_tot.sum(), resident_early_cons=q.res_cons.sum() / q.res_tot.sum(),
                        benchmark_cons=np.average(q.ref_cons, weights=q.res_tot), station_cons=q.st_cons.sum() / q.st_tot.sum(),
                        pooled_cons=q.B_cons.sum() / max(q.B_tot.sum(), 1e-9)))
    absdev = np.abs(d.res_cons / d.res_tot - d.ref_cons)
    stdev = np.abs(d.st_cons / d.st_tot - d.ref_cons)
    d = d_all   # ballot totals over every dong (the departure LP covers dongs without a price too), as in least_departure_detail
    d["depP"] = d.B_cons - d.at_cons * d.B_tot
    summ = dict(pooled_dep_ballots=float(np.abs(d.depP).sum()), pooled_ballots=float(d.B_tot.sum()), abs_dep_median=absdev.median(), abs_dep_p90=absdev.quantile(0.9), station_dep_median=stdev.median(), station_dep_p90=stdev.quantile(0.9),
                dep_ballots=float(np.abs(d.dep).sum()), resident_early_ballots=float(d.res_tot.sum()),
                station_dep_ballots=float(np.abs(d.st_cons - d.ref_cons * d.st_tot).sum()))
    return out, summ


def least_departure(P, LP, W, eta, delta, pooled=True, slope_constraint=True, early=True):
    """Joint LP: min sum |D_i| (+ sum |D^P_i| if pooled) s.t. sum_u theta_u <= 0.

    D^P_i = P_{i KMS} - a_tilde_{i KMS} P_{i.}: departure of residents' out-of-zone early conservative ballots
    from the station anchor. Returns (value, {unit: x}, status)."""
    blocks_eq, blocks_ub, beq, bub, cobj, ctheta, k0 = [], [], [], [], [], [], 0.0
    sizes = []; dev_rows = []
    for u in P.units:
        lp = LP[u]; Aeq, be, Aub, bu = lp.cached_constraints(eta, delta)
        c, const = slope_c(lp, W[u]); k0 += const
        n, C = lp.n, lp.C; ref = lp.ref()
        # D_i as a row vector over this unit's variables
        Dm = np.zeros((2 * n if pooled else n, lp.nv)); at = lp.g["a_tilde"]
        for i in range(n):
            for j in range(n):
                for cc in range(C): Dm[i, lp.iF(i, j, cc)] -= ref[i, KMS]
                Dm[i, lp.iF(i, j, KMS)] += 1.0
            if pooled:
                for cc in range(C): Dm[n + i, lp.iB(i, cc)] -= at[i, KMS]
                Dm[n + i, lp.iB(i, KMS)] += 1.0
            if not early: Dm[i, :] = 0.0
        blocks_eq.append(Aeq); blocks_ub.append(Aub); beq.append(be); bub.append(bu); ctheta.append(c); dev_rows.append(Dm); sizes.append(lp.nv)
    nx = sum(sizes); nd = sum(D.shape[0] for D in dev_rows)
    Aeq = hstack([block_diag(blocks_eq), csr_matrix((sum(b.shape[0] for b in blocks_eq), nd))])
    Aub0 = hstack([block_diag(blocks_ub), csr_matrix((sum(b.shape[0] for b in blocks_ub), nd))])
    Dall = block_diag([csr_matrix(D) for D in dev_rows])
    I = coo_matrix(np.eye(nd))
    Arow1 = hstack([Dall, -I]); Arow2 = hstack([-Dall, -I])           # |D| <= e
    th = hstack([csr_matrix(np.concatenate(ctheta)[None, :]), csr_matrix((1, nd))])
    A_ub = vstack([Aub0, Arow1, Arow2] + ([th] if slope_constraint else [])).tocsr()
    b_ub = np.concatenate(bub + [np.zeros(2 * nd)] + ([[-k0]] if slope_constraint else []))
    obj = np.concatenate([np.zeros(nx), np.ones(nd)])
    r = linprog(obj, A_ub=A_ub, b_ub=b_ub, A_eq=Aeq.tocsr(), b_eq=np.concatenate(beq), bounds=(0, None), method="highs", options=HS_OPTS)
    if r.status != 0: return None, None, r.status
    sols = {}; pos = 0
    for u, s in zip(P.units, sizes): sols[u] = r.x[pos:pos + s]; pos += s
    return r.fun, sols, 0


if __name__ == "__main__":
    prof, summ, det = [], [], []
    for sg in elections_from_argv(["20220309", "20240410", "20250603", "20260603"]):
        log = timer(); P = Prep(sg); LP = P.lps(calib=True); W = P.W["guFE"]
        for delta in [0.1, 0.2, 1.0]:
            sols = {u: LP[u].solve(slope_c(LP[u], W[u])[0], 1.0, delta).x for u in P.units}
            lb = sum(slope_c(LP[u], W[u])[1] + slope_c(LP[u], W[u])[0] @ sols[u] for u in P.units)
            t, s = terciles(pd.DataFrame(describe(P, LP, sols, W, "lower bound")))
            prof += [dict(sg=sg, delta=delta, alloc="lower bound", **r) for r in t]
            summ.append(dict(sg=sg, delta=delta, alloc="lower bound", slope=lb, **s))
            for pooled, name in [(True, "least-departure reversal"), (False, "least-departure reversal (early only)")]:
                val, sols2, st = least_departure(P, LP, W, 1.0, delta, pooled)
                if val is None:
                    summ.append(dict(sg=sg, delta=delta, alloc=name, slope=np.nan, note=f"infeasible (status {st}): no allocation reverses the sign"))
                    continue
                slope2 = sum(slope_c(LP[u], W[u])[1] + slope_c(LP[u], W[u])[0] @ sols2[u] for u in P.units)
                dd = pd.DataFrame(describe(P, LP, sols2, W, name))
                dd["depF"] = (dd.res_cons - dd.ref_cons * dd.res_tot).abs(); dd["depP"] = (dd.B_cons - dd.at_cons * dd.B_tot).abs()
                if pooled:
                    w_all = np.concatenate([np.abs(W[u]) / (P.G[u][0]["Avotes"] + P.G[u][1] - P.G[u][0]["D"]) for u in P.units])
                    dd["lev"] = w_all; top = dd.lev >= dd.lev.quantile(0.9)
                    pmin, _, _ = least_departure(P, LP, W, 1.0, delta, True, slope_constraint=False, early=False)
                    det.append(dict(sg=sg, delta=delta, n_dongs_depF_gt10=int((dd.depF > 10).sum()), n_dongs_depP_gt10=int((dd.depP > 10).sum()),
                                    max_depF=dd.depF.max(), max_depP=dd.depP.max(), share_depF_top_leverage=dd.depF[top].sum() / max(dd.depF.sum(), 1e-9),
                                    share_depP_top_leverage=dd.depP[top].sum() / max(dd.depP.sum(), 1e-9), depF_total=dd.depF.sum(), depP_total=dd.depP.sum(),
                                    depP_min_feasible=pmin, n_dongs=len(dd)))
                    pd.DataFrame(det).to_csv(f"{RES}/least_departure_detail.csv", index=False)
                t2, s2 = terciles(dd)
                prof += [dict(sg=sg, delta=delta, alloc=name, **r) for r in t2]
                summ.append(dict(sg=sg, delta=delta, alloc=name, slope=slope2, lp_value=val, **s2))
            log(sg, delta)
            pd.DataFrame(prof).to_csv(f"{RES}/extremal_profile.csv", index=False); pd.DataFrame(summ).to_csv(f"{RES}/least_departure.csv", index=False)
