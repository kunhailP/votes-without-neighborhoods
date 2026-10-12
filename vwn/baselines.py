"""Conventional small-area shares (comparators; none of them is a parameter value of the framework)."""
import numpy as np


def exclude(g, cand):
    """Station-based share with pooled ballots dropped: (A_ic + K_ic) / (A_i + K_i)."""
    return (g["A"][:, cand] + g["K"][:, cand]) / (g["Avotes"] + g["K"].sum(1))


def proportional(g, cand):
    """Pooled ballots allocated in proportion to each dong's in-person ballots, gu composition (US practice)."""
    Tobs = g["Avotes"] + g["K"].sum(1); share = Tobs / Tobs.sum()
    B = np.outer(share, g["Bc"] + g["Gc"])
    return (g["A"][:, cand] + g["K"][:, cand] + B[:, cand]) / (Tobs + B.sum(1))


def station_imputation(g, cand, iters=200):
    """Pooled ballots imputed from each dong's in-zone early composition, raked to gu totals (IPF)."""
    Ksum = g["K"].sum(1); M = Ksum / Ksum.sum() * (g["Bc"] + g["Gc"]).sum()
    B = g["a_tilde"] * M[:, None]; col = g["Bc"] + g["Gc"]
    for _ in range(iters):
        cs = B.sum(0); B *= np.divide(col, cs, out=np.zeros_like(col, dtype=float), where=cs > 0)[None, :]
        rs = B.sum(1); B *= np.divide(M, rs, out=np.zeros_like(M, dtype=float), where=rs > 0)[:, None]
    return (g["A"][:, cand] + g["K"][:, cand] + B[:, cand]) / (g["Avotes"] + Ksum + B.sum(1))
