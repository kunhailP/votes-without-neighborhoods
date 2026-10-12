"""Fully counted units (Section 4.1; Figure 2A; Table 3; Online Appendix Table C14) and conventional
dong-level point estimates (supplementary results, docs/supplementary_results.md).

Every ballot is counted in its voter's gu, so a gu's vote share is its residents' share: the gu-level
price-vote gradient needs no allocation assumption. In 2024, pooled ballots are reported by constituency
and one constituency spans 중구 and 성동구, so the gu-level regression merges them (24 units); the
48-constituency regression is reported as well.

Outputs: results/gu_regression.csv, results/point_estimates.csv"""
import numpy as np
import pandas as pd
from vwn.data import setup, ELECTIONS
from vwn.lp import KMS, INV
from vwn.paths import RES


def ols(X, y, hc="HC1"):
    X = np.column_stack([np.ones(len(y)), X]) if X.ndim == 1 else X
    XtXi = np.linalg.inv(X.T @ X); b = XtXi @ X.T @ y; e = y - X @ b; n, k = X.shape
    if hc == "HC3":
        h = np.einsum("ij,jk,ik->i", X, XtXi, X); u = e / (1 - h); V = XtXi @ (X.T * u ** 2) @ X @ XtXi
    else:
        V = XtXi @ (X.T * e ** 2) @ X @ XtXi * n / (n - k)
    return b, np.sqrt(np.diag(V))


def unit_level(sg, level):
    units, G, idx, x, labs = setup(sg); ud = np.array([u for u, _ in idx], dtype=object)
    L = ud.copy() if level == "constituency" else np.array(labs["guFE"], dtype=object)
    if level == "gu":   # merge gu that share a counting jurisdiction
        for u in units:
            gs = sorted(set(L[ud == u]))
            if len(gs) > 1: L[np.isin(L, gs)] = "·".join(gs)
    E = np.concatenate([G[u][1] for u in units])
    df = pd.DataFrame(dict(a=L, x=x, E=E)).dropna()
    xm = df.groupby("a").x.mean(); xw = df.groupby("a").apply(lambda q: np.average(q.x, weights=q.E), include_groups=False)
    rec = {}
    for u in units:
        a = L[ud == u][0]; g0 = G[u][0]; rec[a] = rec.get(a, 0) + g0["A"].sum(0) + g0["K"].sum(0) + g0["Bc"] + g0["Gc"]
    y = pd.Series({k: v[KMS] / (v.sum() - v[INV]) for k, v in rec.items()})
    return pd.DataFrame(dict(x=xm, xw=xw, y=y)).dropna()


if __name__ == "__main__":
    rows = []; rng = np.random.default_rng(1)
    for sg in ELECTIONS:
        for level in (["gu", "constituency"] if sg == "20240410" else ["gu"]):
            d = unit_level(sg, level); X = d.x.values; y = d.y.values
            b, s1 = ols(X, y); _, s3 = ols(X, y, "HC3")
            k3 = ~d.index.str.contains("강남구|서초구|송파구"); b3, s33 = ols(X[k3], y[k3], "HC3")
            loo = [ols(np.delete(X, i), np.delete(y, i))[0][1] for i in range(len(y))]
            bw, sw = ols(d.xw.values, y, "HC3")
            perm = np.array([ols(X, rng.permutation(y))[0][1] for _ in range(5000)])
            rows.append(dict(sg=sg, level=level, n=len(y), slope=b[1], se_hc1=s1[1], se_hc3=s3[1], perm_p=(np.abs(perm) >= abs(b[1])).mean(),
                             loo_min=min(loo), loo_max=max(loo), slope_excl3=b3[1], se_excl3_hc3=s33[1], n_excl3=int(k3.sum()),
                             slope_wprice=bw[1], se_wprice_hc3=sw[1]))
            print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in rows[-1].items()}, flush=True)
    pd.DataFrame(rows).to_csv(f"{RES}/gu_regression.csv", index=False)

    rows = []
    for sg in ELECTIONS:
        units, G, idx, x, labs = setup(sg); lab = np.array(labs["guFE"]); has = ~np.isnan(x)
        conv = np.concatenate([(G[u][0]["A"][:, KMS] + G[u][0]["K"][:, KMS]) / (G[u][0]["Avotes"] + G[u][0]["K"].sum(1)) for u in units])
        dayv = np.concatenate([G[u][0]["A"][:, KMS] / (G[u][0]["Avotes"] - G[u][0]["A"][:, INV]) for u in units])
        for nm, yv in [("conventional", conv), ("election_day_valid", dayv)]:
            for sp in ["pooled", "guFE"]:
                xx, yy, ll = x[has], yv[has], lab[has]
                if sp == "guFE":
                    dm = pd.DataFrame(dict(x=xx, y=yy, g=ll)); xx = xx - dm.groupby("g").x.transform("mean").values; yy = yy - dm.groupby("g").y.transform("mean").values
                    n = len(yy); ngu = len(set(ll)); XtXi = 1 / (xx @ xx); bb = XtXi * (xx @ yy); e = yy - xx * bb
                    se = np.sqrt(XtXi * (xx ** 2 * e ** 2).sum() * XtXi * n / (n - 1 - ngu))
                else:
                    b_, s_ = ols(xx, yy); bb, se = b_[1], s_[1]
                rows.append(dict(sg=sg, outcome=nm, spec=sp, slope=bb, se_hc1=se))
    pd.DataFrame(rows).to_csv(f"{RES}/point_estimates.csv", index=False)
