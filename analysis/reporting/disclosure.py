"""What additional reporting would reveal (selected allocations; supplementary results, docs/supplementary_results.md).

The true allocation is unknown, so each reporting change is evaluated at true allocations chosen inside the
actual identified set: the two within-gu slope extremes, random vertices (Gaussian objectives), and
convex combinations of vertices (their centroid and Dirichlet(1) weights). Convex combinations lie in Lambda
but are not claimed to be relative-interior points. For each truth and proposal we compute the within-gu set
that would remain and report its width as a share of the actual width. Results are the largest share over
the evaluated scenarios, not the worst case over Lambda.

Proposals:
  P2   residence reporting: pooled ballots (out-of-zone early, at-home, overseas) by registered dong
  P2b  only out-of-zone early ballots by registered dong; at-home and overseas ballots stay pooled
  P1   headcount reporting: early-voter counts by registered dong x station (no vote choice); movement is then
       observed, so the evaluation removes the movement cap
  P12  P1 and P2

Configurations: uniform eta in {0, 0.05, 0.1, 0.2, 0.3} (delta = 1; extremes + 4 vertices);
calibrated lambda = 0.5 (delta = 1) and lambda = 1 with (delta, s) in {(1, -), (1, 0.02), (0.1, -), (0.1, 0.02)}
(extremes + 20 vertices + 11 convex combinations of 14 vertices).
Output: results/disclosure_<sg>.csv"""
import numpy as np
import pandas as pd
from vwn.run import Prep, timer, elections_from_argv
from vwn.bounds import bounds_with_w, slope_c
from vwn.lp import KMS
from vwn.paths import RES


def config_lp(P, u, calib, s):
    return P.lps(calib=calib, dF=None if s is None else ("slack", s))[u]


def run(sg):
    log = timer(); P = Prep(sg); W = P.W["guFE"]; rows = []
    cfgs = [(f"uniform eta={e}", False, e, 1.0, None, "small") for e in [0.0, 0.05, 0.1, 0.2, 0.3]]
    if sg != "20170509":
        cfgs += [("calib lambda=0.5", True, 0.5, 1.0, None, "small"), ("calib", True, 1.0, 1.0, None, "full"),
                 ("calib, s=0.02", True, 1.0, 1.0, 0.02, "full"), ("calib, delta=0.1", True, 1.0, 0.1, None, "full"),
                 ("calib, delta=0.1, s=0.02", True, 1.0, 0.1, 0.02, "full")]
    for name, calib, eta, delta, s, design in cfgs:
        LP = {u: config_lp(P, u, calib, s) for u in P.units}
        act = [bounds_with_w(LP[u], W[u], KMS, eta, delta) for u in P.units]
        alo, ahi = sum(a[0] for a in act), sum(a[1] for a in act)
        rng = np.random.default_rng(7 if design == "small" else 11); nv = 4 if design == "small" else 20
        dirw = [] if design == "small" else [np.full(14, 1 / 14)] + [rng.dirichlet(np.ones(14)) for _ in range(10)]
        truths = {}
        for u in P.units:
            lp = LP[u]; c, const = slope_c(lp, W[u])
            V = [lp.solve(c, eta, delta).x, lp.solve(-c, eta, delta).x] + [lp.solve(rng.normal(size=lp.nv), eta, delta).x for _ in range(nv)]
            sols = {"min_slope": V[0], "max_slope": V[1], **{f"vertex{k:02d}": V[2 + k] for k in range(nv)}}
            Vc = np.array(V[:14]) if len(V) >= 14 else None
            for k, wd in enumerate(dirw): sols["centroid" if k == 0 else f"convex{k:02d}"] = wd @ Vc
            for nm, x in sols.items():
                F, B, G, U = lp.state(x)
                truths.setdefault(nm, {})[u] = (B, G, F.sum(2), const + float(c @ x))
        for nm, tr in truths.items():
            kind = "extreme" if nm.endswith("slope") else ("vertex" if nm.startswith("vertex") else "convex")
            true_slope = sum(v[3] for v in tr.values())
            for prop in ["P2", "P2b", "P1", "P12"]:
                if design == "small" and prop == "P2b": continue
                lo = hi = 0.0; ok = True
                for u in P.units:
                    B, G, Hh, _ = tr[u]; lp = config_lp(P, u, calib, s)
                    if prop in ("P2", "P2b", "P12"): lp.Bfix = B
                    if prop in ("P2", "P12"): lp.Gfix = G
                    e_eval = eta
                    if prop in ("P1", "P12"):   # observed headcounts replace the movement assumption
                        lp.Hfix = Hh; lp.ev = None; e_eval = 10.0
                    b = bounds_with_w(lp, W[u], KMS, e_eval, delta)
                    if b is None: ok = False; break
                    lo += b[0]; hi += b[1]
                rows.append(dict(sg=sg, config=name, truth=nm, kind=kind, proposal=prop, true_slope=true_slope,
                                 actual_lo=alo, actual_hi=ahi, lo=lo if ok else np.nan, hi=hi if ok else np.nan))
        log(sg, name)
        pd.DataFrame(rows).to_csv(f"{RES}/disclosure_{sg}.csv", index=False)


if __name__ == "__main__":
    for sg in elections_from_argv(["20170509", "20220309", "20240410", "20250603", "20260603"]):
        run(sg)
