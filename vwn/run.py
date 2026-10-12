"""Shared set-up for analysis scripts."""
import sys
import time
import numpy as np
import pandas as pd
from .data import setup, slope_weights, split, make_lp, align_calib, ELECTIONS, YEAR
from .paths import DERIVED, RES
from .lp import JointLP


class Prep:
    """Data, regression weights and LP blocks for one election.

    zones: impose statutory early-voting zones (2026 council constituencies). headcounts: add the 2026
    cross-contest headcounts. Calibrated movement uses data/derived/eta_calib_<sg>.csv."""

    def __init__(self, sg, zones=True, headcounts=False):
        self.sg = sg; self.zones = zones; self.headcounts = headcounts
        self.units, self.G, self.idx, self.x, self.labs = setup(sg, zones=zones, headcounts=headcounts)
        self.has = ~np.isnan(self.x)
        self.Wfull = slope_weights(sg, self.x, self.labs)
        self.W = {sp: split(self.units, self.G, w) for sp, w in self.Wfull.items()}
        self._ev = None

    @property
    def ev(self):
        if self._ev is None:
            suffix = "" if self.zones else "_nozones"
            cal = pd.read_csv(f"{DERIVED}/eta_calib_{self.sg}{suffix}.csv")
            self._ev = {u: c.eta_j.values for u, c in align_calib(cal, self.G, self.units).items()}
        return self._ev

    def lps(self, calib=False, dF=None, cls=None):
        """{unit: LP} with calibrated (eta = lambda) or uniform movement and optional A^F."""
        return {u: make_lp(*self.G[u], cls=cls or JointLP, ev=self.ev[u] if calib else None, dF=dF,
                           headcounts=self.headcounts) for u in self.units}

    def wsplit(self, w):
        return split(self.units, self.G, w)


def timer():
    t0 = time.time()
    return lambda *a: print(*a, f"[{time.time() - t0:.0f}s]", flush=True)


def elections_from_argv(default=None):
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    return args or (default or ELECTIONS)
