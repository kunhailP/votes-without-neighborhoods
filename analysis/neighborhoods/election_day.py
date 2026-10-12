"""Point-identified benchmarks for the within-district relation (Section 4.2; Table 2; Online Appendix Table C20).

Election-day ballots are counted in the voter's own voting district, so the conservative share among a dong's election-day
voters is a residence-based quantity that needs no allocation assumption. The within-gu slope and the high-minus-low contrast
of that share are therefore point-identified for the subpopulation of election-day voters. For comparison the same summaries
are computed for in-zone early-station shares, which are counted where cast (not residence-based) and exist from 2014.
Shares are valid-vote shares (invalid ballots excluded). Weights are those of the main analysis (gu fixed effects; median
split with gu weights proportional to dongs with a price), for all of Seoul and without 강남, 서초 and 송파.
Auxiliary diagnostics for the election-day slope, which itself describes the observed dongs exactly: a p-value from permuting
prices within gu (5,000 permutations; assumes exchangeability of dongs within gu, ignores spatial dependence; prices were not
randomly assigned) and a gu-clustered standard error for a superpopulation reading.
Output: results/election_day.csv"""
import numpy as np
import pandas as pd
from vwn.data import ELECTIONS, setup, slope_weights
from vwn.lp import KMS, INV
from vwn.paths import RES
from contrast import contrast_weights
from spatial_scope import GANGNAM3


def slope_inference(x, y, gu, rng, n_perm=5000):
    m = ~np.isnan(x) & ~np.isnan(y); x, y, gu = x[m], y[m], gu[m]
    xt = x.copy(); yt = y.copy()
    for g in np.unique(gu):
        k = gu == g; xt[k] -= xt[k].mean(); yt[k] -= yt[k].mean()
    b = (xt @ yt) / (xt @ xt); e = yt - b * xt
    G = len(np.unique(gu)); n = len(x); kfe = G + 1
    meat = sum((xt[gu == g] @ e[gu == g]) ** 2 for g in np.unique(gu))
    se = np.sqrt(G / (G - 1) * (n - 1) / (n - kfe) * meat) / (xt @ xt)
    idx = [np.where(gu == g)[0] for g in np.unique(gu)]; cnt = 0
    for _ in range(n_perm):
        xp = xt.copy()
        for k in idx: xp[k] = xt[rng.permutation(k)]
        cnt += abs((xp @ yt) / (xp @ xp)) >= abs(b) - 1e-12
    return b, se, (cnt + 1) / (n_perm + 1)


def shares(M):
    valid = M.sum(1) - M[:, INV]
    return np.where(valid > 0, M[:, KMS] / np.where(valid > 0, valid, 1), np.nan)


if __name__ == "__main__":
    rows = []; rng = np.random.default_rng(20261012)
    for sg in ELECTIONS:
        units, G, idx, x, labs = setup(sg)
        A = np.vstack([G[u][0]["A"] for u in units]); K = np.vstack([G[u][0]["K"] for u in units])
        meas = {"election_day": shares(A), "station": shares(K) if K.sum() > 0 else None}
        gu = labs["guFE"]
        for sample, exclude in [("all", ()), ("excl_gangnam3", GANGNAM3)]:
            xs = x.copy()
            if exclude: xs[np.isin(gu, exclude)] = np.nan
            W = {"slope": slope_weights(sg, xs, labs, ["guFE"])["guFE"], "contrast": contrast_weights(xs, gu, "median")}
            b, se, pp = slope_inference(xs, meas["election_day"], gu, rng)
            rows.append(dict(sg=sg, sample=sample, measure="election_day", spec="slope_inference", value=b, se_cluster=se, p_perm=pp,
                             n_dongs=int((~np.isnan(xs)).sum()), voters=float(A.sum())))
            for m, y in meas.items():
                if y is None: continue
                for sp, w in W.items():
                    ok = w != 0
                    if np.isnan(y[ok]).any(): raise ValueError(f"missing share with nonzero weight: {sg} {m}")
                    rows.append(dict(sg=sg, sample=sample, measure=m, spec=sp, value=float(w[ok] @ y[ok]), n_dongs=int(ok.sum()),
                                     voters=float(A.sum() if m == "election_day" else K.sum())))
    pd.DataFrame(rows).to_csv(f"{RES}/election_day.csv", index=False)
    print(pd.DataFrame(rows).pivot_table(index=["sg", "sample"], columns=["measure", "spec"], values="value").round(3).to_string())
