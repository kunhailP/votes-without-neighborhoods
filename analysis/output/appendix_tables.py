"""Online Appendix and supplementary tables (docs/supplementary_results.md), generated from results/."""
import re
import glob
import math
import numpy as np
import pandas as pd
from vwn.paths import RES, DATA
from vwn.data import ELECTIONS, YEAR as Y
from tablelib import emit, iv, num, bp

C4 = ["20220309", "20240410", "20250603", "20260603"]; C5 = ["20170509"] + C4
SPN = {"guFE": "Within-gu", "pooled": "City-wide", "sggFE": "Within-constituency"}
rd = lambda f, **kw: pd.read_csv(f"{RES}/{f}", **kw)
cat = lambda pat: pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{RES}/{pat}"))], ignore_index=True)


def specs_for(sg):
    return ["pooled", "guFE"] + (["sggFE"] if sg == "20240410" else [])


def F1():
    rows = []
    for sp in ["pooled", "guFE", "sggFE"]:
        rows.append(("PANEL", SPN[sp]))
        for sg in ELECTIONS:
            if sp not in specs_for(sg): continue
            g = rd(f"main_grid_{sg}.csv", dtype={"delta": str})
            b = lambda e, d: (lambda q: iv(q.lo.iloc[0], q.hi.iloc[0]))(g[(g.kind == "bound") & (g.spec == sp) & (g.eta == e) & (g.delta == d)])
            es = lambda d: (lambda q: bp(q.lo.iloc[0], cap=1.0))(g[(g.kind == "eta_star") & (g.spec == sp) & (g.delta == d)])
            cv = g[(g.kind == "baseline") & (g.spec == sp) & (g.method == "exclude")].value.iloc[0]
            rows.append([Y[sg], num(cv), b(1.0, "1.0"), b(0.0, "1.0"), b(0.0, "dmin"), b(0.0, "0.1"), b(0.05, "0.1"), b(0.1, "0.1"), b(0.2, "0.1"), es("0.1"), es("1.0")])
    emit("F1", "Table F1. Identified sets under uniform movement and breakdown points η* (z; bold = contains zero)",
         ["Election", "Conv.", "Accounting only", "η = 0, δ = 1", "η = 0, δ = δ_min", "η = 0, δ = 0.1", "η = 0.05, δ = 0.1", "η = 0.1, δ = 0.1", "η = 0.2, δ = 0.1", "η*, δ = 0.1", "η*, δ = 1"],
         rows, long=True, size="scriptsize", colspec="lcccccccccc",
         notes="Accounting only: movement unrestricted (η = 1, at which the cap r_j + K_j cannot bind) and δ = 1. δ_min: each jurisdiction at its smallest feasible "
               "out-of-district band. η*: largest η at which the lower bound is positive, lower end of a bisection interval of width 1/512 on [0, 1] "
               "(\"any\": positive at η = 1). 2026 imposes the statutory in-district zones.")


def F2():
    d = rd("decomposition.csv"); rows = []
    lab = {"accounting": "Accounting only", "eta0_d1": "η = 0, δ = 1", "eta0_d0.1": "η = 0, δ = 0.1", "eta0.05_d0.1": "η = 0.05, δ = 0.1", "calib_d0.1": "Calibrated, δ = 0.1", "calib_d1": "Calibrated, δ = 1"}
    for r in d.itertuples():
        rows.append([Y[str(r.sg)], lab[r.cell], num(r.pi_w, 2), iv(r.P_lo, r.P_hi), iv(r.F_lo, r.F_hi), iv(r.B_lo, r.B_hi)])
    emit("F2", "Table F2. Lemma 2 decomposition: city-wide slope = π_w × within-gu slope + gu-gradient term θ(v)",
         ["Election", "Cell", "π_w", "City-wide θ(w^P)", "Within-gu θ(w^FE)", "Gu-gradient term θ(v)"], rows, long=True, size="scriptsize", colspec="llcccc",
         notes="π_w: share of the price variance within gu. θ(v) depends on the allocation, so its identified set is reported; the identity holds allocation by "
               "allocation, so the city-wide set is contained in π_w times the within-gu set plus the set of θ(v), but need not equal it.")


def F3():
    z = rd("zones_2026.csv"); rows = []
    for cell in ["accounting only", "minimum movement, delta=1", "minimum movement, delta=0.1", "eta=0.1, delta=0.1", "calibrated, delta=1", "calibrated, delta=0.1", "calibrated, delta=0.1, s=0.02"]:
        for sp in ["guFE", "pooled"]:
            q = z[(z.cell == cell) & (z.spec == sp)].set_index("variant")
            rows.append([cell.replace("delta", "δ"), SPN[sp]] + [iv(q.loc[v].lo, q.loc[v].hi) for v in ["no zone restriction", "statutory zones (main)", "zones + council headcounts"]])
    emit("F3", "Table F3. 2026: the statutory in-district zones and cross-contest headcounts (z)",
         ["Cell", "Slope", "Movement anywhere in the gu (zones ignored)", "Statutory zones: gu council constituencies (main)", "Zones + council-contest headcounts"],
         rows, size="scriptsize", colspec="llCCC",
         notes="Zones: an in-district early ballot can be cast only at a station in the voter's gu council constituency (155 constituencies). Council-contest "
               "headcounts: the out-of-district early and at-home headcounts that the gu council returns report by constituency (113 contested constituencies; "
               "the uncontested ones only as a gu residual), imposed as ranges that allow for unreturned envelopes. Calibrated rows use the zone-level calibration.")


def F4():
    rows = []
    for sp in ["pooled", "guFE", "sggFE"]:
        rows.append(("PANEL", SPN[sp]))
        for dl, m, lab in [(0.1, 1.0, "δ = 0.1"), (0.2, 1.0, "δ = 0.2"), (1.0, 1.0, "δ = 1"), (0.1, 0.5, "δ = 0.1, λ = 0.5"), (0.1, 1.5, "δ = 0.1, λ = 1.5")]:
            cells = []
            for sg in C4:
                c = rd(f"calibrated_bounds_{sg}.csv"); q = c[(c.spec == sp) & (c.delta == dl) & (c.mult == m)]
                cells.append(iv(q.lo.iloc[0], q.hi.iloc[0]) if len(q) else "–")
            if sp == "sggFE" and all(c == "–" for i, c in enumerate(cells) if C4[i] != "20240410"): pass
            rows.append([lab] + cells)
        for dl in [0.1, 1.0]:
            cells = []
            for sg in C4:
                l = rd(f"calibrated_lamstar_{sg}.csv"); q = l[(l.spec == sp) & (l.delta == dl)]
                cells.append(bp(q.lo.iloc[0], cap=4.0, d=2, any_label="≥ 4") if len(q) else "–")
            rows.append([f"λ*, δ = {dl:g}"] + cells)
    emit("F4", "Table F4. Calibrated movement, residents' early composition unrestricted (z)", ["Assumption", "2022", "2024", "2025", "2026"], rows, size="scriptsize",
         colspec="lCCCC", notes="Cap at station j: r^ρ_j + λC_j. λ*: largest λ in [0, 4] at which the lower bound is positive, lower end of a bisection interval of width 0.01.")


def F5():
    rows = []
    for sp in ["guFE", "pooled"]:
        for dl in [0.1, 1.0]:
            rows.append(("PANEL", f"{SPN[sp]}, δ = {dl:g}"))
            for dF, lab in [("('slack', 0.02)", "slack 0.02"), ("('slack', 0.05)", "slack 0.05"), ("('slack', 0.1)", "slack 0.10"), ("0.2", "fixed band 0.20")]:
                for calib, cells_def in [(False, [(0.0, "η = 0"), (0.1, "η = 0.1"), (0.3, "η = 0.3"), ("star", "η*")]), (True, [(1.0, "λ = 1"), (0.5, "λ = 0.5"), ("star", "λ*")])]:
                    for e, el in cells_def:
                        r = [lab, el]
                        for sg in C5:
                            if calib and sg == "20170509": r.append("–"); continue
                            c = rd(f"composition_{sg}.csv")
                            if e == "star":
                                q = c[(c.kind == ("lamstar" if calib else "etastar")) & (c.spec == sp) & (c.delta == dl) & (c.dF == dF)]
                                r.append(bp(q.lo.iloc[0], cap=4.0 if calib else 2.0, d=2 if calib else 3, any_label="≥ 4" if calib else "any") if len(q) else "–")
                            else:
                                q = c[(c.kind == "bounds") & (c.calib == calib) & (c.spec == sp) & (c.delta == dl) & (c.dF == dF) & (c.eta == e)]
                                r.append(iv(q.lo.iloc[0], q.hi.iloc[0]) if len(q) else "–")
                        rows.append(r)
    emit("F5", "Table F5. Residents' in-district early composition restricted (A^F): identified sets (z) and breakdown points",
         ["Restriction", "Movement", "2017", "2022", "2024", "2025", "2026"], rows, long=True, size="scriptsize", colspec="llccccc",
         notes="Slack s: residents' in-district early composition may depart from the benchmark a^F by at most s more than their station's composition does, "
               "in every category. Fixed band: departure at most 0.20 in every dong. η*: lower end of a bisection interval of width 0.004 on [0, 2] "
               "(\"any\": positive at η = 2). λ*: width 0.008 on [0, 4].")


def F6():
    rows = []
    for mv, ml in [("calib", "Calibrated"), ("free", "Unrestricted (η = 2)")]:
        for sp in ["guFE", "pooled", "sggFE"]:
            rows.append(("PANEL", f"{ml}, {SPN[sp]}"))
            for dl in [0.1, 0.15, 0.2, 0.3, 0.5, 1.0]:
                r = [f"{dl:g}"]
                for sg in C5:
                    f = rd(f"joint_frontier_{sg}.csv"); q = f[(f.movement == mv) & (f.spec == sp) & (f.delta == dl)]
                    if not len(q): r.append("–"); continue
                    v = q.s_lo.iloc[0]; sm = q.s_min.iloc[0] if "s_min" in q else 0.0
                    r.append("∞" if not np.isfinite(v) else ("≥ 0.30" if v >= 0.3 - 1e-9 else ("0" if v <= sm + 1e-12 and q.lower_s0.iloc[0] <= 0 else num(v))))
                rows.append(r)
    emit("F6", "Table F6. Frontier s*(δ): largest slack on residents' early composition at which the slope's lower bound stays positive",
         ["δ", "2017", "2022", "2024", "2025", "2026"], rows, long=True, size="scriptsize", colspec="lccccc",
         notes="Bisection on [s_min, 0.30], where s_min is the smallest feasible slack (0 except where the restriction is infeasible at s = 0); reported at the lower end "
               "of the final interval (width 0.3/128). 0: not signed at s_min. ∞: signed with residents' early composition unrestricted.")


def F7():
    p = rd("extremal_profile.csv"); rows = []
    for (sg, dl, al), q in p.groupby(["sg", "delta", "alloc"], sort=False):
        if al.endswith("(early only)") or dl == 1.0: continue
        for r in q.itertuples():
            rows.append([Y[str(sg)], f"{dl:g}", al, r.tercile, num(r.move_share, 2), num(r.mover_cons, 2), num(r.stayer_cons, 2), num(r.resident_early_cons, 2),
                         num(r.benchmark_cons, 2), num(r.station_cons, 2), num(r.pooled_cons, 2)])
    emit("F7", "Table F7. Allocations behind Table 5, by price tercile of residents' home dongs (within-gu, calibrated movement)",
         ["Election", "δ", "Allocation", "Tercile", "Movers' share of residents' early ballots", "Movers' conservative share", "Stayers' conservative share",
          "Residents' early conservative share", "Benchmark a^F", "Station share", "Residents' out-of-district conservative share"], rows, long=True, size="scriptsize",
         colspec="lllcccccccc", notes="Shares include invalid ballots; averages over dongs weighted by the relevant ballot counts. Observed stations' departure from the "
         "benchmark a^F (conservative share, absolute): " + "; ".join(f"{Y[str(r.sg)]} median {100 * r.station_dep_median:.1f} and 90th percentile {100 * r.station_dep_p90:.1f} points"
         for r in rd("least_departure.csv").query("alloc == 'lower bound' and delta == 0.1").itertuples()) + ".")


def F8():
    reg = rd("gap_test_reg.csv"); gu = rd("gap_test_gu.csv"); rows = []
    for sg in C5:
        c = lambda m, t: (lambda q: f"{num(q.coef.iloc[0])} ({num(q.se.iloc[0])})" if len(q) else "–")(reg[(reg.model == f"{m} {sg}") & (reg.term == t)])
        g = gu[gu.sg == int(sg)]
        rows.append([Y[sg], c("gu gamK x+s60", "x"), c("gu gamK x+s60", "s60"), c("gu gamB x+s60", "x"), c("gu gamB x+s60", "s60"),
                     c("dong dev x+s60", "x"), c("dong dev x+s60", "s60"), f"{num(g.gamK.mean())} ({num(g.gamK.std())})"])
    emit("F8a", "Table F8a. Is the early-vote gap related to price or age? (conservative share; coefficients, standard errors in parentheses)",
         ["Election", "Gu: in-district early − election day, on log price", "on share aged 60+", "Gu: out-of-district early − election day, on log price", "on share aged 60+",
          "Dong (within gu): station departure, on log price", "on share aged 60+", "Mean gu gap γ^K (SD)"], rows, size="scriptsize", colspec="l" + "C" * 7,
         notes="Gu level: one observation per jurisdiction (48 constituencies in 2024), joint regression on price and age, HC3 standard errors. Dong level: weighted by "
               "station ballots, jurisdiction fixed effects, standard errors clustered by jurisdiction. Stations mix residents and movers, so the dong-level test is an "
               "imperfect proxy. Age shares from April 2026 resident registration for all elections.")
    g = rd("gap_adjusted.csv"); rows = []
    for sp in ["guFE", "sggFE", "pooled"]:
        for s in [0.02, 0.05]:
            rows.append(("PANEL", f"{SPN[sp]}, slack {s:g}"))
            for v in ["common gap (baseline)", "gu-level price slope", "gu-level price slope, CI low", "gu-level price slope, CI high", "gu-level price and age", "station-level price and age"]:
                r = [v]
                for sg in C4:
                    q = g[(g.sg == int(sg)) & (g.spec == sp) & (g.variant == v) & (g.slack == s)]
                    r.append(iv(q.lo.iloc[0], q.hi.iloc[0]) if len(q) else "–")
                rows.append(r)
    emit("F8b", "Table F8b. Residents' early-composition restriction with a price-dependent early-vote gap (z; calibrated movement, δ = 0.1)",
         ["Benchmark gap", "2022", "2024", "2025", "2026"], rows, long=True, size="scriptsize", colspec="lcccc",
         notes="The conservative benchmark is shifted by β_x(x_i − x̄_g) + β_a(a_i − ā_g), with the opposite shift for the Democratic candidate; coefficients from Table F8a "
               "(gu-level regression, or its 95% limits, or the dong-level station regression).")


def F9():
    r = cat("robust_restricted_*.csv"); rows = []
    lab = {"baseline": "log median (baseline)", "excl_top5": "excl. top 5% by price", "excl_top10": "excl. top 10% by price", "H_weighted": "denominator (H_i) weights",
           "log_mean": "log mean", "linear_median": "linear median", "linear_mean": "linear mean", "min_trades_30": "excl. dongs with < 30 transactions"}
    def cellv(q):
        if not len(q) or pd.isna(q.lo.iloc[0]): return "–"
        v = q.lo.iloc[0]; lin = q.variant.iloc[0].startswith("linear")
        if lin: return "positive" if v > 0 else "**not signed**"
        return ("**" + num(v) + "**") if v <= 0 else num(v)
    for sg in C4:
        for fe in ["guFE", "sggFE"]:
            for v in lab:
                if fe == "sggFE" and (sg != "20240410" or v != "baseline"): continue
                cells = []
                for mv, s in [("calib", None), ("calib", 0.02), ("calib", 0.05), ("free", 0.02), ("free", 0.05)]:
                    q = r[(r.sg == int(sg)) & (r.fe == fe) & (r.variant == v) & (r.movement == mv) & ((r.slack.isna()) if s is None else (r.slack == s))]
                    cells.append(cellv(q))
                rows.append([Y[sg], (lab[v] if fe == "guFE" else "constituency fixed effects")] + cells)
    emit("F9", "Table F9. Robustness of the within-gu lower bound (z; δ = 0.1)",
         ["Election", "Specification", "Calibrated, residents' composition unrestricted", "Calibrated, s = 0.02", "Calibrated, s = 0.05", "Unrestricted movement, s = 0.02", "Unrestricted movement, s = 0.05"],
         rows, long=True, size="scriptsize", colspec="llccccc", notes="Bold marks lower bounds at or below zero. Linear-price slopes are in different units; only their sign is shown.")


def F10():
    h = rd("headcount_bands.csv"); rows = []
    lab = {"baseline": "none", "H1": "H1: out-of-district headcount within [0.5, 2] × rate", "H2": "H2: H1 + at-home composition and headcount",
           "gu-specific delta: dmin+0.05": "gu-specific δ = δ_min,g + 0.05", "gu-specific delta: dmin+0.10": "gu-specific δ = δ_min,g + 0.10"}
    for sp in ["guFE", "sggFE", "pooled"]:
        for s in [None, 0.02, 0.05]:
            rows.append(("PANEL", f"{SPN[sp]}, residents' early composition {'unrestricted' if s is None else f'slack {s:g}'}"))
            for v, l in lab.items():
                r = [l]
                for sg in C4:
                    q = h[(h.sg == int(sg)) & (h.spec == sp) & (h.variant == v) & ((h.slack.isna()) if s is None else (h.slack == s))]
                    r.append(iv(q.lo.iloc[0], q.hi.iloc[0]) if len(q) else "–")
                if sp == "sggFE" and all(c == "–" for c in r[1:]): continue
                rows.append(r)
    emit("F10", "Table F10. Additional restrictions on pooled headcounts and at-home ballots, and gu-specific out-of-district bands (z; calibrated movement, δ = 0.1)",
         ["Additional restriction", "2022", "2024", "2025", "2026"], rows, long=True, size="scriptsize", colspec="lcccc",
         notes="Rate: jurisdiction ratio of out-of-district (at-home) ballots to removed residents. H2 anchors at-home and overseas composition at election-day "
               "composition plus the jurisdiction gap (±0.10) and caps their headcount at three times the rate. δ_min,g is computed under the same movement and "
               "early-composition restriction.")


def F11():
    a = cat("anchor_day_*.csv"); rows = []
    dm = a[a.kind == "dmin"]
    for r in dm.itertuples():
        rows.append([Y[str(r.sg)], num(r.st_eta0_med), num(r.st_eta0_max), f"{int(r.st_eta0_n_gt05)} of {int(r.n_units)}", num(r.st_eta10_med), num(r.st_eta10_min), num(r.day_eta0_med)])
    emit("F11a", "Table F11a. Smallest out-of-district band consistent with the data, δ_min (all ballot categories; across jurisdictions)",
         ["Election", "Station anchor, η = 0: median", "max", "δ_min > 0.05", "Station anchor, η = 10: median", "minimum", "Election-day anchor, η = 0: median"],
         rows, size="scriptsize", colspec="l" + "C" * 6,
         notes="η = 10 leaves movement unrestricted. A positive δ_min at η = 10 means the station anchor's premise (residents' out-of-district composition equal to "
               "their station's) cannot hold exactly, whatever the movement.")
    b = a[a.kind == "bounds"]; rows = []
    for sp in ["pooled", "guFE"]:
        rows.append(("PANEL", SPN[sp]))
        for mv, ml in [("eta0", "η = 0"), ("eta0.1", "η = 0.1"), ("calibrated", "calibrated")]:
            for dl in [0.05, 0.1, 0.2]:
                r = [ml, f"{dl:g}"]
                for sg in C5:
                    q = b[(b.sg == int(sg)) & (b.spec == sp) & (b.movement == mv) & (b.delta == dl)]
                    r.append(iv(q.lo.iloc[0], q.hi.iloc[0]) if len(q) else "–")
                rows.append(r)
    emit("F11b", "Table F11b. Identified sets under the election-day anchor (z)", ["Movement", "δ", "2017", "2022", "2024", "2025", "2026"], rows, long=True,
         size="scriptsize", colspec="llccccc", notes="Anchor: clip(A_ic/A_i + γ_gc), with γ_gc the jurisdiction gap between out-of-district early and election-day composition.")
    s = cat("anchor_slack_*.csv"); rows = []
    for sp in ["guFE", "pooled"]:
        rows.append(("PANEL", SPN[sp]))
        for sl in [0.02, 0.05, 0.1]:
            for cell, cl in [("eta0", "η = 0"), ("eta0.1", "η = 0.1"), ("calib", "calibrated"), ("etastar", "η*")]:
                r = [f"{sl:g}", cl]
                for sg in C5:
                    q = s[(s.sg == int(sg)) & (s.spec == sp) & (s.slack == sl) & (s.cell == cell)]
                    r.append("–" if not len(q) else (bp(q.lo.iloc[0], cap=1.0) if cell == "etastar" else iv(q.lo.iloc[0], q.hi.iloc[0])))
                rows.append(r)
    emit("F11c", "Table F11c. Station anchor with a gu-specific band δ_g = δ_min,g + slack (z)", ["Slack", "Cell", "2017", "2022", "2024", "2025", "2026"], rows, long=True,
         size="scriptsize", colspec="llccccc", notes="δ_min,g: smallest feasible band in jurisdiction g at η = 0. η*: width 0.004.")


def F12():
    p = rd("spec_prices_2026.csv"); rows = []
    for (sc, sa), q in p.groupby(["scale", "sample"], sort=False):
        g = q.set_index("cell"); f = lambda c: iv(g.loc[c].lo, g.loc[c].hi, 3 if sc.startswith("log") else 2)
        rows.append([sc, f"{sa} ({int(q.n.iloc[0])})", f("accounting"), f("e0_d1"), f("e0_d0.1"), f("e0.05_d0.1"), f("calib_d0.1"), bp(g.loc["etastar"].lo, cap=1.0)])
    emit("F12a", "Table F12a. 2026 within-gu slope by price measure and sample (z)",
         ["Price measure", "Sample (dongs)", "Accounting only", "η = 0, δ = 1", "η = 0, δ = 0.1", "η = 0.05, δ = 0.1", "Calibrated, δ = 0.1", "η*, δ = 0.1"], rows,
         size="scriptsize", colspec="ll" + "C" * 6, notes="Linear measures in 10 million won per pyeong. Trimming drops the dongs with the highest mean price per pyeong.")
    h = rd("spec_hweighted.csv"); rows = []
    for sp in ["guFE", "pooled"]:
        rows.append(("PANEL", SPN[sp]))
        for cell, cl in [("conventional", "conventional"), ("accounting", "accounting only"), ("e0_d1", "η = 0, δ = 1"), ("e0_d0.1", "η = 0, δ = 0.1"), ("e0.05_d0.1", "η = 0.05, δ = 0.1"),
                         ("calib_d0.1", "calibrated, δ = 0.1"), ("calib_d1", "calibrated, δ = 1"), ("etastar", "η*, δ = 0.1")]:
            r = [cl]
            for sg in ELECTIONS:
                q = h[(h.sg == int(sg)) & (h.spec == sp) & (h.cell == cell)]
                r.append("–" if not len(q) else (num(q.lo.iloc[0]) if cell == "conventional" else (bp(q.lo.iloc[0], cap=1.0) if cell == "etastar" else iv(q.lo.iloc[0], q.hi.iloc[0]))))
            rows.append(r)
    emit("F12b", "Table F12b. Roll-denominator-weighted (WLS) dong-level slopes (z)", ["Cell", "2012", "2017", "2022", "2024", "2025", "2026"], rows, long=True,
         size="scriptsize", colspec="lcccccc", notes="Weights w_i = H_i x̃_i / Σ_k H_k x̃_k², x̃ the deviation from the H-weighted (jurisdiction) mean.")
    s = rd("spec_sparse.csv"); rows = []
    for sg in C5:
        for thr in [0, 10, 30]:
            r = [Y[sg], str(thr)]
            for sp in ["guFE", "pooled"]:
                q = s[(s.sg == int(sg)) & (s.min_trades == thr) & (s.spec == sp)].set_index("cell")
                if sp == "guFE": r.append(str(int(q.dongs.iloc[0])))
                r += [iv(q.loc["e0_d1"].lo, q.loc["e0_d1"].hi), iv(q.loc["e0_d0.1"].lo, q.loc["e0_d0.1"].hi),
                      iv(q.loc["calib_d0.1"].lo, q.loc["calib_d0.1"].hi) if "calib_d0.1" in q.index else "–", bp(q.loc["etastar"].lo, cap=1.0)]
            rows.append(r)
    emit("F12c", "Table F12c. Excluding dongs with few apartment transactions (z)",
         ["Election", "Min. transactions", "Dongs", "Within-gu: η = 0, δ = 1", "η = 0, δ = 0.1", "calibrated, δ = 0.1", "η*", "City-wide: η = 0, δ = 1", "η = 0, δ = 0.1", "calibrated, δ = 0.1", "η*"],
         rows, long=True, size="scriptsize", colspec="lcccccccccc")


def F13():
    o = rd("outcomes.csv"); rows = []
    for r in o.itertuples():
        rows.append([Y[str(r.sg)], r.outcome, SPN[r.spec], num(r.conventional), iv(r.e1_d1_lo, r.e1_d1_hi), iv(r.e0_d1_lo, r.e0_d1_hi)])
    emit("F13a", "Table F13a. Alternative outcomes (z)", ["Election", "Outcome", "Slope", "Conventional", "Returns and rolls only", "Minimal movement (η = 0)"], rows,
         long=True, size="scriptsize", colspec="lllccc",
         notes="2017 Hong+Yoo: the two conservative candidates combined (Hong+Yoo+Ahn adds the centrist Ahn Cheol-soo). 2024 PPP+Reform and 2025 Kim+Lee: the main conservative candidate with the minor conservative candidate.")
    a = rd("adjacency_bounds.csv"); rows = []
    for sp in ["pooled", "guFE"]:
        rows.append(("PANEL", SPN[sp]))
        for geo in ["anywhere in zone", "adjacent dongs only"]:
            for eta in [0.1, 0.2, 0.3, 1.0]:
                r = [geo, "unrestricted" if eta == 1.0 else f"{eta:g}"]
                for sg in C5:
                    q = a[(a.sg == int(sg)) & (a.spec == sp) & (a.movement == geo) & (a.eta == eta) & (a.delta == 0.1)]
                    r.append(iv(q.lo.iloc[0], q.hi.iloc[0]) if len(q) else "–")
                rows.append(r)
    emit("F13b", "Table F13b. Movement restricted to adjacent dongs (z; δ = 0.1)", ["Movement geography", "η", "2017", "2022", "2024", "2025", "2026"], rows, long=True,
         size="scriptsize", colspec="llccccc", notes="Adjacent: dongs sharing an administrative boundary (vuski 2026), within the statutory zone.")
    w = rd("width_bound.csv"); rows = []
    for r in w.itertuples():
        rows.append([Y[str(r.sg)], SPN[r.spec], f"{r.eta:g}", num(r.width_lp), num(r.width_bound), num(r.ratio, 2)])
    emit("F13c", "Table F13c. Width bound of Proposition 2(iv) and LP width (z, δ = 1)", ["Election", "Slope", "η", "LP width", "Bound", "Ratio"], rows, long=True,
         size="scriptsize", colspec="llcccc")


def F14():
    d = rd("adj_pairs_2026.csv"); d["signed"] = (d.lo > 0) | (d.hi < 0); d["w"] = d.hi - d.lo
    lab = {"accounting": "accounting only", "eta0_d1": "η = 0, δ = 1", "eta0_d0.1": "η = 0, δ = 0.1", "calib_d0.1": "calibrated, δ = 0.1", "calib_d0.1_s0.02": "calibrated, δ = 0.1, s = 0.02"}
    r = pd.read_csv(f"{RES}/dong_ranges_2026.csv"); rows = []
    for k, l in lab.items():
        q = d[d.setting == k]
        med_range = num((r[f"hi_{k}"] - r[f"lo_{k}"]).median()) if f"hi_{k}" in r else "–"
        rows.append([l, med_range, str(len(q)), f"{100 * q.signed.mean():.1f}%", num(q.w.median())])
    emit("F14", "Table F14. Single dongs and adjacent pairs, 2026 (residence-based share of Oh Se-hoon)",
         ["Assumptions", "Median width of a dong's valid-vote share", "Adjacent pairs in the same gu", "Sign of the difference identified", "Median width of the difference (z)"], rows,
         size="scriptsize", colspec="lCCCC", notes=f"Median absolute conventional difference between adjacent dongs: {num(d[d.setting == 'eta0_d1'].conv.abs().median())}.")


def F15():
    rows = []
    for sg in C4:
        d = rd(f"disclosure_{sg}.csv"); d["share"] = (d.hi - d.lo) / (d.actual_hi - d.actual_lo); d["signed"] = (d.lo > 0) | (d.hi < 0)
        for cfg in ["calib", "calib, s=0.02", "calib, delta=0.1", "calib, delta=0.1, s=0.02"]:
            r = [Y[sg], cfg.replace("calib", "calibrated").replace("delta", "δ")]
            for prop in ["P2", "P2b", "P1", "P12"]:
                q = d[(d.config == cfg) & (d.proposal == prop)]
                r.append(f"{num(q.share.min(), 2)}–{num(q.share.max(), 2)} ({100 * q.signed.mean():.0f}%)")
            rows.append(r)
    emit("F15", "Table F15. Reporting changes at evaluated true allocations: within-gu width left as a share of the actual width, range over allocations (share at which the sign is revealed)",
         ["Election", "Configuration", "Residence reporting (P2)", "Out-of-district only (P2b)", "Headcounts (P1)", "Both (P12)"], rows, size="scriptsize", colspec="llCCCC",
         notes="P2: pooled ballots by registered dong. P2b: out-of-district early ballots by registered dong, at-home and overseas ballots pooled at the gu. P1: early-voter "
               "headcounts by registered dong and station (no vote choice); the movement cap is removed because movement is then observed. 33 evaluated allocations per row.")


def F16():
    rows = []
    for f in sorted(glob.glob(f"{RES}/resampling_*_full.csv")):
        d = pd.read_csv(f); t = pd.read_csv(f.replace("_full", "_txn")); sg = str(d.sg.iloc[0])
        for (sp, mv, sl), q in d.groupby(["spec", "movement", d.slack.fillna(-1)], sort=False):
            o = q[q.b == 0].iloc[0]; bs = q[q.b > 0]
            tq = t[(t.spec == sp) & (t.movement == mv) & (t.slack.fillna(-1) == sl) & (t.b > 0)]
            rows.append([Y[sg], SPN[sp], "calibrated" if mv == "calib" else "unrestricted", "–" if sl < 0 else f"{sl:g}", iv(o.lo, o.hi),
                         f"{num(tq.lo.std())}, {num(tq.hi.std())}" if len(tq) else "–", f"{num(bs.lo.std())}, {num(bs.hi.std())}",
                         f"[{num(bs.lo.quantile(0.05))}, {num(bs.hi.quantile(0.95))}]", f"{100 * (bs.lo > 0).mean():.0f}%", str(len(bs))])
    emit("F16", "Table F16. Stability of headline sets to resampling prices and dongs (z, δ = 0.1)",
         ["Election", "Slope", "Movement", "Slack s", "Identified set", "SD of bounds, transactions resampled", "SD of bounds, dongs and transactions resampled",
          "[5th pct of lower, 95th pct of upper]", "Replications with positive lower bound", "Replications"], rows, long=True, size="scriptsize", colspec="lllccccccc",
         notes="The returns, rolls and movement caps, which define the polytope, are held fixed. Transactions resampled: each dong's median price is recomputed "
               "from a resample of its transactions; this measures sensitivity to price measurement. Dongs and transactions resampled: dongs are also resampled with "
               "replacement within jurisdictions, which duplicates high-leverage dongs and mechanically pushes the extrema outward, so these columns overstate "
               "instability and are not confidence intervals.")


def F17():
    g = rd("gu_regression.csv"); rows = []
    for r in g.itertuples():
        rows.append([Y[str(r.sg)], f"{r.n} {'constituencies' if r.level == 'constituency' else ('units' if r.n == 24 else 'gu')}", num(r.slope), num(r.se_hc1), num(r.se_hc3),
                     "<0.001" if r.perm_p < 0.001 else num(r.perm_p), f"{num(r.loo_min)}–{num(r.loo_max)}", f"{num(r.slope_excl3)} ({num(r.se_excl3_hc3)})", f"{num(r.slope_wprice)} ({num(r.se_wprice_hc3)})"])
    emit("F17a", "Table F17a. Regressions across fully counted units (valid-vote share on the unit mean of dong log price)",
         ["Election", "Units", "Slope", "HC1 SE", "HC3 SE", "Permutation p", "Leave-one-out range", "Excl. 강남·서초·송파: slope (HC3 SE)", "Electorate-weighted price: slope (HC3 SE)"],
         rows, size="scriptsize", colspec="ll" + "C" * 7, notes="2024: 중구 and 성동구 merged because one constituency spans both. Slopes describe the fully counted units themselves and need no allocation assumption. The standard errors and permutation p-values (5,000 permutations) answer a different question: how far the slope would vary if district values were draws from a larger population or if prices were assigned to districts at random. They are reported for that reading only; the identified sets of the main analysis condition on the observed returns and involve no sampling.")
    p = rd("point_estimates.csv"); rows = []
    for sg in ELECTIONS:
        q = p[p.sg == int(sg)]; f = lambda o, s: (lambda x: f"{num(x.slope.iloc[0])} ({num(x.se_hc1.iloc[0])})")(q[(q.outcome == o) & (q.spec == s)])
        rows.append([Y[sg], f("conventional", "guFE"), f("election_day_valid", "guFE"), f("conventional", "pooled"), f("election_day_valid", "pooled")])
    emit("F17b", "Table F17b. Point estimates of dong-level slopes (HC1 standard errors)",
         ["Election", "Conventional, within-gu", "Election-day ballots only, within-gu", "Conventional, city-wide", "Election-day ballots only, city-wide"], rows,
         size="scriptsize", colspec="lCCCC")


def A_tables():
    rows = []
    for sg in ELECTIONS:
        v = rd(f"valid_vote_{sg}.csv"); v = v[v.get("note", pd.Series([None] * len(v))).isna() | (v.note != "eta_star_y")] if "note" in v else v
        for r in v.itertuples():
            if getattr(r, "note", None) == "eta_star_y" or pd.isna(r.z_lo): continue
            mv = "uniform" if r.movement == "uniform" else ("calibrated" if r.movement == "calib" else "unrestricted")
            cell = (f"η = {r.eta:g}, δ = {r.delta:g}" if r.movement == "uniform" and r.eta < 1 else ("accounting only" if r.movement == "uniform" else f"{mv}, δ = {r.delta:g}"))
            sl = "–" if pd.isna(r.slack) else f"{r.slack:g}"
            rows.append([Y[sg], SPN[r.spec], cell, sl, iv(r.z_lo, r.z_hi), f"[{num(r.y_tight_lo, 4)}, {num(r.y_ach_lo, 4)}]", f"[{num(r.y_ach_hi, 4)}, {num(r.y_tight_hi, 4)}]"])
    emit("A1", "Table A1. Valid-vote share brackets (log scale)", ["Election", "Slope", "Cell", "Slack s", "z (sharp)", "y lower: [outer, attainable]", "y upper: [attainable, outer]"],
         rows, long=True, size="scriptsize", colspec="lllcccc", notes="The sharp valid-vote bound lies between the Proposition 4 outer bound and the attainable value.")
    rows = []
    for sg in ELECTIONS:
        r = rd(f"resolution_{sg}.csv")
        for sp in ["pooled", "guFE"]:
            for eta in [0.0, 0.05, 1.0]:
                q = r[(r.spec == sp) & (r.eta == eta)].set_index("scheme")
                rows.append([Y[sg], SPN[sp], "unrestricted" if eta == 1 else f"{eta:g}"] + [iv(q.loc[s].lo, q.loc[s].hi) for s in ["gu", "pairs", "five", "seoul"]])
    emit("A2", "Table A2. Coarser reporting of pooled ballots (z, δ = 1)", ["Election", "Slope", "η", "By gu (actual)", "13 pools", "5 pools", "Seoul as one pool"], rows, long=True,
         size="scriptsize", colspec="lllcccc", notes="Pools merge the pooled totals of gu in alphabetical order; in-district movement stays within each original gu (and zone).")
    s = rd("solver_check.csv"); rows = [[Y[str(r.sg)], r.movement, f"{r.eta:g}", f"{r.delta:g}", num(r.unscaled_default, 5), num(r.dual_simplex, 5), num(r.interior_point, 5), num(r.dual_simplex_x1000, 5)] for r in s.itertuples()]
    emit("A3", "Table A3. Solver check: within-gu z lower bound", ["Election", "Movement", "η", "δ", "HiGHS default, unscaled", "Dual simplex, rescaled", "Interior point, rescaled", "Dual simplex, ×1000"],
         rows, size="scriptsize", colspec="ll" + "C" * 6, notes="Without rescaling, the default solver stops early and reports a lower bound that is too high.")
    b = rd("integer_check.csv"); rows = []
    for r in b.itertuples():
        cell = f"{Y[str(r.sg)]} {SPN[r.spec].lower()}, {'calibrated' if r.movement == 'calib' else f'η = {r.eta:g}'}, δ = {r.delta:g}" + ("" if pd.isna(r.slack) else f", s = {r.slack:g}")
        rows.append([cell, num(r.z_lo_lp, 4), num(r.z_lo_int_bound, 4), num(r.z_lo_int_incumbent, 4), num(r.y_lo_int_bound, 4), num(r.y_lo_int_actual, 4), f"{int(r.solves_at_time_limit)}/{int(r.solves)}"])
    emit("B1", "Table B1. Integer check of near-zero lower bounds", ["Cell", "LP z lower", "Integer z lower (solver bound)", "Integer z incumbent", "Prop. 4 y lower (integer, solver bound)", "y at integer allocation", "Solves at time limit"],
         rows, size="scriptsize", colspec="l" + "C" * 6, notes="Mixed-integer programs use the same constraint matrices as the LPs, including the 2026 zones. Each solve has a 30-second limit, extended to 180 seconds when no integer solution has been found. Solver bound: the best bound proven by the solver when it stops, which is a valid lower bound on the integer minimum also when the time limit is reached; the incumbent is the best integer allocation found.")


def C_tables():
    pc = pd.read_csv(f"{DATA}/council_pooled_20260603.csv"); cm = pd.read_csv(f"{DATA}/council_20260603.csv")
    e = pd.read_csv(f"{DATA}/seoul_20260603_emd.csv"); mo = e[(e.unit == "X") & (e.emd == "관외사전투표")].set_index("gu")
    g = pc.groupby("gu").agg(n=("council", "size"), contested=("out_elig", lambda s: int(s.notna().sum())), out=("out_elig", "sum"))
    g["dongs"] = cm.groupby("gu").size(); g["mayor_out"] = mo.elig
    rows = [[gu, str(int(r.dongs)), str(int(r.n)), str(int(r.contested)), f"{int(r.out):,}", f"{int(r.mayor_out):,}", "exact" if r.n == r.contested and r.out == r.mayor_out else ("–" if r.n != r.contested else "differs")] for gu, r in g.iterrows()]
    st = pd.read_csv(f"{DATA}/council_stations_20260603.csv"); mi = e[e.unit == "IN"].copy()
    nm = lambda s: s.replace("제", "").replace(".", "·")
    st["k"] = st.emd.map(nm); mi["k"] = mi.emd.map(nm); jj = st.merge(mi, on=["gu", "k"])
    eq = int((jj.indistrict_early_voters == jj.elig).sum())
    emit("C1", "Table C1. 2026 in-district zones: gu council constituencies", ["Gu", "Dongs", "Council constituencies", "Contested", "Out-of-district early voters in contested constituencies (council returns)",
         "Out-of-district early voters, gu (mayoral returns)", "Sum check where all contested"], rows, long=True, size="scriptsize", colspec="lcccccc",
         notes="Source: NEC Election Statistics System, constituency-and-dong table and constituency-level council returns. In every gu where all constituencies were "
               "contested, the council counts sum exactly to the mayoral gu count. In-district early voters per station: council and mayoral counts are equal at "
               f"{eq} of {len(jj)} stations of contested constituencies.")


def D_tables():
    a = rd("published_admissibility.csv"); z = rd("published_zone_check.csv")
    rows = [[r.gu, "∞" if not np.isfinite(r.eta_min_nozones) else num(r.eta_min_nozones), str(int((z[z.gu == r.gu].excess > 0).sum())) + f" of {int((z.gu == r.gu).sum())}",
             num(z[(z.gu == r.gu) & (z.excess > 0)].excess.max(), 0) if (z[z.gu == r.gu].excess > 0).any() else "–", num(r.delta_min_eta10), num(r.out_minus_in_early_cons, 3, signed=True)] for r in a.itertuples()]
    emit("D1", "Table D1. Admissibility of the published 2026 allocation", ["Gu", "Smallest η making it feasible, movement anywhere in the gu", "Constituencies where it assigns more pooled voters than the roll allows",
         "Largest excess (voters)", "Smallest station-anchor band, η = 10", "Out-of-district minus in-district early conservative share"], rows, long=True, size="scriptsize", colspec="lccccc",
         notes="Feasibility fixes the allocation's dong-level pooled ballots and asks whether some in-district movement and non-voting reproduce (R) and (S). Under the "
               "statutory zones, a constituency's pooled voters plus non-voters must equal its removed residents minus its in-district early ballots.")
    p = rd("published_scale.csv"); rows = []
    for r in p.itertuples():
        mv = "calibrated" if r.movement == "calib" else ("accounting only" if r.eta >= 1 else f"η = {r.eta:g}")
        rows.append([r.spec, mv + ("" if pd.isna(getattr(r, "slack", np.nan)) else f", s = {r.slack:g}"), f"{r.delta:g}", iv(r.z_lo, r.z_hi, 2), f"[{num(r.y_tight_lo, 2)}, {num(r.y_ach_lo, 2)}]",
                     f"[{num(r.y_ach_hi, 2)}, {num(r.y_tight_hi, 2)}]", num(r.published_point, 2)])
    emit("D2", "Table D2. 2026, published scale (percentage points per 10 million won per pyeong)", ["Specification", "Movement", "δ", "z", "y lower: [outer, attainable]", "y upper: [attainable, outer]", "Published allocation"],
         rows, long=True, size="scriptsize", colspec="lllcccc")


def E_tables():
    from vwn.paths import DERIVED
    s = pd.read_csv(f"{DERIVED}/eta_calib_summary.csv"); rows = [[Y[str(r.sg)], str(int(r.n_zones)), f"{num(r.R_med, 2)} [{num(r.R_min, 2)}, {num(r.R_max, 2)}]", num(r.eta_zone_med, 2), num(r.eta_station_med, 2),
                                               num(r.eta_station_p90, 2), num(r.eta_station_max, 2), f"{int(r.forced_covered)} of {int(r.forced)}"] for r in s.itertuples()]
    emit("E1", "Table E1. Calibration summary", ["Election", "Zones", "R_u: median [min, max]", "C_u/K_u: median", "Station C_j/K_j: median", "90th pct.", "max", "Forced stations with C_j ≥ r_j"],
         rows, size="scriptsize", colspec="l" + "C" * 7, notes="2026 zones are gu council constituencies, which are small, so most home-based trips leave the zone and R_u is small.")
    f = cat("calibrated_failures_*.csv"); f = f[f.unit != "ALL"]
    rows = [[Y[str(r.sg)], str(r.zone), r.emd, f"{r.forced:,.0f}", f"{r.calibrated:,.0f}", f"{r.K:,.0f}"] for r in f.itertuples()]
    emit("E2", "Table E2. Stations where the calibrated inflow falls short of the movement the roll forces", ["Election", "Zone", "Dong", "Forced r_j", "Calibrated C_j", "Station ballots K_j"],
         rows, long=True, size="scriptsize", colspec="llcccc", notes="At these stations the intercept r^ρ_j ≥ r_j covers the forced movement.")
    o = cat("calibrated_origin_*.csv"); rows = []
    for sp in ["pooled", "guFE"]:
        for dl in [0.1, 1.0]:
            for lam in [1.0, 2.0]:
                for kind in ["station", "origin"]:
                    r = [SPN[sp], f"{dl:g}", f"{lam:g}", "station" if kind == "station" else "station + origin"]
                    for sg in C4:
                        q = o[(o.sg == int(sg)) & (o.spec == sp) & (o.delta == dl) & (o.lam == lam)]
                        r.append(iv(q[f"lo_{kind}"].iloc[0], q[f"hi_{kind}"].iloc[0]) if len(q) else "–")
                    rows.append(r)
    emit("E3", "Table E3. Calibrated caps with and without origin caps (z)", ["Slope", "δ", "λ", "Caps", "2022", "2024", "2025", "2026"], rows, long=True, size="scriptsize", colspec="llllcccc")
    d = rd("calibrated_dow.csv"); rows = []
    for (sg, dow), q in d.groupby(["sg", "dow"]):
        g = q.set_index(["spec", "delta"]); rows.append([Y[str(sg)], dow, num(q.R_med.iloc[0], 2), num(q.eta_med.iloc[0], 3)] + [iv(g.loc[(sp, dl)].lo, g.loc[(sp, dl)].hi) for sp in ["guFE", "pooled"] for dl in [0.1, 1.0]])
    emit("E4", "Table E4. Calibration by early-voting day of the week (z)", ["Election", "Day", "Median R_u", "Median C_j/K_j", "Within-gu, δ = 0.1", "Within-gu, δ = 1", "City-wide, δ = 0.1", "City-wide, δ = 1"],
         rows, size="scriptsize", colspec="ll" + "C" * 6)
    c = cat("calibrated_caps_*.csv"); rows = []
    for sp in ["guFE", "sggFE", "pooled"]:
        for s in [None, 0.02]:
            for cap in ["max(r, C)", "r + C", "r_rho + C (main)"]:
                r = [SPN[sp], "unrestricted" if s is None else f"slack {s:g}", cap.replace("r_rho", "r^ρ")]
                for sg in C4:
                    q = c[(c.sg == int(sg)) & (c.spec == sp) & (c.cap == cap) & ((c.slack.isna()) if s is None else (c.slack == s))]
                    r.append(iv(q.lo.iloc[0], q.hi.iloc[0]) if len(q) else "–")
                if sp == "sggFE" and all(x == "–" for x in r[3:]): continue
                rows.append(r)
    emit("E5", "Table E5. Calibrated movement under three intercepts for the station cap (z, λ = 1, δ = 0.1)", ["Slope", "Residents' early composition", "Cap", "2022", "2024", "2025", "2026"],
         rows, long=True, size="scriptsize", colspec="lllcccc", notes="At stations where C_j ≤ r_j, the cap max(r_j, C_j) forces the corner of Corollary 1.")


def F15b():
    g = cat("disclosure_guarantee_2*.csv"); rows = []
    for r in g.itertuples():
        f = lambda p: f"{100 * (1 - getattr(r, f'Wmax_{p}') / (r.W0 if p in ('P2', 'P2b') else r.W0_free)):.0f}%"
        rows.append([Y[str(r.sg)], r.config.replace("calib", "calibrated").replace("delta", "δ").replace("eta", "η").replace("lambda", "λ"), num(r.W0), f("P2"), f("P2b"), num(r.W0_free), f("P1"), f("P12")])
    emit("F15b", "Table F15b. Share of the within-gu width removed for every true allocation (guaranteed), by reporting change",
         ["Election", "Assumptions", "Current width W_0", "Residence reporting (P2)", "Out-of-district only (P2b)", "Current width, movement unrestricted", "Headcounts (P1)", "Both (P12)"],
         rows, long=True, size="scriptsize", colspec="llcccccc",
         notes="1 − W^max/W_0. Headcounts make movement observed, so P1 and P12 are compared with the current width under the same composition restrictions and "
               "unrestricted movement. Headcounts alone remove little in the worst case, because they say nothing about how movers voted; their value is that the "
               "movement assumption is no longer needed, and combined with residence reporting they remove most of the width.")


def F18():
    c = cat("contrast_2*.csv"); rows = []
    lab = {"conventional": "conventional", "accounting": "accounting only", "eta0_d1": "η = 0, δ = 1", "eta0_d0.1": "η = 0, δ = 0.1", "calib_d1": "calibrated, δ = 1",
           "calib_d0.1": "calibrated, δ = 0.1", "calib_d0.1_s0.02": "calibrated, δ = 0.1, s = 0.02", "calib_d0.1_s0.05": "calibrated, δ = 0.1, s = 0.05"}
    for kind in ["median", "tercile"]:
        rows.append(("PANEL", "Above vs. at-or-below the gu median price" if kind == "median" else "Top vs. bottom tercile within gu"))
        for cell, l in lab.items():
            r = [l]
            for sg in ELECTIONS:
                q = c[(c.sg == int(sg)) & (c.kind == kind) & (c.cell == cell)]
                if not len(q) or pd.isna(q.z_lo.iloc[0]): r.append("–"); continue
                q = q.iloc[0]
                r.append(num(100 * q.z_lo, 1) if cell == "conventional" else f"{iv(100 * q.z_lo, 100 * q.z_hi, 1)}; y ≥ {num(100 * q.y_tight_lo, 1)}")
            rows.append(r)
    emit("F18", "Table F18. Within-gu contrast between high- and low-price dongs (percentage points; z set; y: Proposition 4 lower bound)",
         ["Cell", "2012", "2017", "2022", "2024", "2025", "2026"], rows, long=True, size="scriptsize", colspec="lcccccc")


def F6b():
    r = cat("region_*.csv"); rows = []
    for sg in C4:
        rows.append(("PANEL", Y[sg]))
        for mv in ["lambda=0.5", "lambda=1", "lambda=1.5", "lambda=2", "lambda=3", "unrestricted"]:
            q = r[(r.sg == int(sg)) & (r.movement == mv)].set_index("delta")
            cells = []
            for dl in [0.1, 0.15, 0.2, 0.3, 0.5, 1.0]:
                x = q.loc[dl]
                cells.append("∞" if np.isinf(x.s_lo) else ("none" if x.s_lo <= x.s_min + 1e-12 else ("≥ 0.30" if x.s_lo >= 0.3 - 1e-9 else num(x.s_lo))))
            rows.append([mv.replace("lambda", "λ").replace("unrestricted", "unrestricted (η = 2; any η ≥ 1 leaves the cap slack)")] + cells)
    emit("F6b", "Table F6b. Sensitivity thresholds s*(λ, δ) for a positive within-district slope",
         ["Movement", "δ = 0.1", "0.15", "0.2", "0.3", "0.5", "1"], rows, long=True, size="scriptsize", colspec="lcccccc",
         notes="∞: positive with residents' early composition unrestricted. none: not positive at the smallest feasible slack. The sign is identified at every "
               "(λ, δ, s) with s below the entry. Bisection on [s_min, 0.30], width 0.3/256, lower end reported.")


def F7b():
    rows = []
    for f in sorted(glob.glob(f"{RES}/edge_profile_*.csv")):
        e = pd.read_csv(f)
        for r in e[e.delta.isin([0.1, 0.15, 0.2])].itertuples():
            rows.append([Y[str(r.sg)], f"{r.delta:g}", num(r.s_edge), r.tercile, num(r.move_share, 2), num(r.mover_cons, 2), num(r.stayer_cons, 2), num(r.resident_early_cons, 2),
                         num(r.benchmark_cons, 2), num(r.station_cons, 2), num(r.abs_dep_median, 3), num(r.abs_dep_p90, 3)])
    emit("F7b", "Table F7b. First allocation with a non-positive slope as s increases (λ = 1)",
         ["Election", "δ", "s at edge", "Tercile", "Movers' share", "Movers' conservative share", "Stayers' conservative share", "Residents' early conservative share",
          "a^F", "Station share", "Median |departure| of residents' early share from a^F (this allocation)", "90th pct."], rows, long=True, size="scriptsize", colspec="lll" + "C" * 9,
         notes="a^F: the neighborhood benchmark for residents' early conservative share. At s just above s*(1, δ), the allocation attaining the minimum slope. Departures of residents' early composition from a^F are bounded by the station's "
               "own departure plus s in every dong. Rows only where the edge exists (s* finite).")


def F7c():
    d = rd("least_departure_detail.csv"); rows = []
    for r in d.itertuples():
        rows.append([Y[str(r.sg)], f"{r.delta:g}", f"{r.depF_total:,.0f}", str(int(r.n_dongs_depF_gt10)), f"{r.max_depF:,.0f}", f"{100 * r.share_depF_top_leverage:.0f}%",
                     f"{r.depP_total:,.0f}", f"{r.depP_min_feasible:,.0f}", str(int(r.n_dongs_depP_gt10)), f"{100 * r.share_depP_top_leverage:.0f}%"])
    emit("F7c", "Table F7c. Least-departure reversal: components and concentration (within-gu, calibrated movement)",
         ["Election", "δ", "Residents' early ballots departing", "Dongs with > 10", "Largest in one dong", "Share in top-decile-leverage dongs",
          "Out-of-district ballots departing", "Needed for feasibility", "Dongs with > 10", "Share in top-decile-leverage dongs"], rows, size="scriptsize", colspec="ll" + "C" * 8,
         notes="Departing ballots: absolute departure of residents' conservative ballots from a^F (in-district early) or from the station anchor (out-of-district). "
               "Needed for feasibility: the smallest out-of-district departure of any allocation in Lambda, without the slope constraint. Leverage: |w_i|/H_i.")


def F15c():
    g = cat("sign_guarantee_2*.csv"); rows = []
    cfg = {"calib": "mobility-calibrated movement", "calib, s=0.02": "+ residents' early ballots (s = 0.02)",
           "calib, delta=0.1": "+ out-of-district ±10 points", "calib, delta=0.1, s=0.02": "main (Table 2, column E)"}
    cell = lambda t: "revealed" if t <= 1e-7 else num(t)
    for (sg, c), d in g.groupby(["sg", "config"], sort=False):
        t = d.set_index("proposal").t_star
        rows.append([Y[str(sg)], cfg[c], cell(t["P2"]), cell(t["P2b"]), cell(t["P12"])])
    emit("F15c", "Table F15c. Opposite-signed slopes compatible with the same report: maximum margin t*",
         ["Election", "Assumptions", "Residence reporting", "Out-of-district only", "Residence + headcounts (no movement assumption)"], rows, size="scriptsize", colspec="llccc",
         notes="t* = max t subject to θ(ℓ) ≤ −t, θ(ℓ') ≥ t, Sℓ = Sℓ', with ℓ and ℓ' in Λ. A report reveals the direction iff no two allocations it cannot distinguish have "
               "slopes of strictly opposite sign, that is iff t* ≤ 0 (\"revealed\"). Where the current set already excludes zero every report reveals the direction; "
               "the last column drops the movement assumption, as in Online Appendix Table C12.")


def F19():
    d = cat("rev_intercept_*.csv"); rows = []
    t = d[d.kind == "totals"]
    tot = "; ".join(f"{Y[str(r.sg)]}: forced {r.r:,.0f}, intercept {r.r_rho:,.0f}, calibrated flows {r.C:,.0f} (of {r.K:,.0f} in-district early ballots)" for r in t.itertuples())
    b = d[(d.kind == "bounds") & (d.spec == "guFE")]
    for nu in [0.0, 0.5, 1.0]:
        for sl in [None, 0.02]:
            for lam in [0.5, 1.0, 1.5]:
                for dl in [0.1, 1.0]:
                    r = [f"{nu:g}", "–" if sl is None else f"{sl:g}", f"{lam:g}", f"{dl:g}"]
                    for sg in C4:
                        q = b[(b.sg == int(sg)) & (b.nu == nu) & (b.lam == lam) & (b.delta == dl) & ((b.slack.isna()) if sl is None else (b.slack == sl))]
                        r.append(iv(q.lo.iloc[0], q.hi.iloc[0]) if len(q) else "–")
                    rows.append(r)
    emit("F19", "Table F19. Calibrated movement with the intercept separated from the mobility-based flow (within-gu, z): cap r_j + ν(r^ρ_j − r_j) + λC_j",
         ["ν", "Slack s", "λ", "δ", "2022", "2024", "2025", "2026"], rows, long=True, size="scriptsize", colspec="llllcccc",
         notes="ν = 0: forced movement plus calibrated flow; ν = 1: main specification. Sums over stations: " + tot + ".")


def F20():
    d = cat("rev_mover_*.csv"); d = d[d.spec == "guFE"]; rows = []
    for mv, ml in [("calib", "calibrated"), ("eta0.1", "η = 0.1"), ("free", "unrestricted (η = 2)")]:
        for dl in [0.1, 1.0]:
            for t in [0.05, 0.1, 0.2, 0.3]:
                r = [ml, f"{dl:g}", f"{t:g}"]
                for sg in C5:
                    q = d[(d.sg == int(sg)) & (d.movement == mv) & (d.delta == dl) & (d.kind == "bounds") & (d.t == t)]
                    r.append(iv(q.lo.iloc[0], q.hi.iloc[0]) if len(q) else "–")
                rows.append(r)
            r = [ml, f"{dl:g}", "t*"]
            for sg in C5:
                q = d[(d.sg == int(sg)) & (d.movement == mv) & (d.delta == dl) & (d.kind == "tstar")]
                r.append(bp(q.lo.iloc[0], cap=1.0) if len(q) else "–")
            rows.append(r)
    emit("F20", "Table F20. Movers' composition restricted: residents who vote at another station vote within t of their home station's composition (within-gu, z)",
         ["Movement", "δ", "t", "2017", "2022", "2024", "2025", "2026"], rows, long=True, size="scriptsize", colspec="lllccccc",
         notes="t*: largest t at which the lower bound is positive (\"any\": positive for every t, i.e. already positive without the restriction).")


def F21():
    d = cat("rev_anchor_*.csv"); rows = []
    dm = d[d.cell == "dmin_eta0"]
    rows.append(("PANEL", "Smallest feasible out-of-district band at η = 0: median (maximum) across jurisdictions"))
    for an in ["station", "station+gap", "station+gap+price"]:
        r = [an, "", ""]
        for sg in C5:
            q = dm[(dm.sg == int(sg)) & (dm.anchor == an)]
            r.append(f"{num(q.lo.iloc[0])} ({num(q.hi.iloc[0])})" if len(q) else "–")
        rows.append(r)
    b = d[(d.cell != "dmin_eta0") & (d.spec == "guFE")]
    rows.append(("PANEL", "Within-gu slope"))
    for cell, cl in [("eta0", "η = 0"), ("calib", "calibrated")]:
        for dl in [0.05, 0.1, 0.2]:
            for sl in ([None] if cell == "eta0" else [None, 0.02, 0.05]):
                for an in ["station", "station+gap", "station+gap+price"]:
                    r = [an, cl, f"δ = {dl:g}" + ("" if sl is None else f", s = {sl:g}")]
                    for sg in C5:
                        q = b[(b.sg == int(sg)) & (b.anchor == an) & (b.cell == cell) & (b.delta == dl) & ((b.slack.isna()) if sl is None else (b.slack == sl))]
                        r.append("infeasible" if len(q) and pd.isna(q.lo.iloc[0]) else (iv(q.lo.iloc[0], q.hi.iloc[0]) if len(q) else "–"))
                    rows.append(r)
    emit("F21", "Table F21. Out-of-district anchor shifted by the observed jurisdiction gap (z)",
         ["Anchor", "Movement", "Band", "2017", "2022", "2024", "2025", "2026"], rows, long=True, size="scriptsize", colspec="lllccccc",
         notes="station: K_ic/K_i. station+gap: plus the jurisdiction difference between out-of-district and in-district early composition. station+gap+price: plus "
               "(b_P − b_K)(x_i − x̄_g) for the conservative candidate (opposite for the Democratic), with b_P, b_K the cross-jurisdiction price slopes of the two gaps "
               "(Table F8a). Infeasible: the band is smaller than the smallest feasible band in some jurisdiction.")


def C2():
    rows = [["Taiwan", "Polling station, village", "None in general", "Read directly; residence-based by household registration"],
            ["Japan", "Counting district (開票区)", "All ballots mixed at the counting district", "Not reported below the counting district"],
            ["United States (many states)", "Precinct", "Absentee, early, provisional ballots (county or city)", "Allocated in proportion to in-person votes"],
            ["Germany", "In-person precinct", "Postal ballots, counted in postal districts", "Analyst's choice"],
            ["Canada", "Polling division", "Special-voting-rules ballots (electoral district)", "Analyst's choice"],
            ["Australia", "Polling place", "Declaration votes (division)", "Analyst's choice"],
            ["Korea", "Voting district, dong", "Out-of-district early, at-home, overseas ballots (gu or constituency)", "Dropped, allocated or imputed"]]
    emit("C2", "Table C2. Counting rules for ballots cast away from the assigned polling place", ["Country", "Smallest unit with candidate totals", "Ballots reported above that unit", "Usual treatment"],
         rows, size="scriptsize", colspec="lLLL")


def VV():
    rows = []
    lab = {(1.0, 1.0, "uniform", None): "returns and rolls only", (0.0, 1.0, "uniform", None): "minimal movement", (0.0, 0.1, "uniform", None): "minimal movement, ±10 points",
           (1.0, 0.1, "calib", None): "mobility-calibrated movement, ±10 points", (1.0, 0.1, "calib", 0.02): "+ residents' early ballots resemble neighborhood"}
    for sg in ELECTIONS:
        v = rd(f"valid_vote_{sg}.csv")
        for (eta, dl, mv, sl), l in lab.items():
            q = v[(v.spec == "guFE") & (v.movement == mv) & (v.eta == eta) & (v.delta == dl) & ((v.slack.isna()) if sl is None else (v.slack == sl))]
            if not len(q): continue
            r = q.iloc[0]
            rows.append([Y[sg], l, iv(r.z_lo, r.z_hi), f"[{num(r.y_tight_lo, 4)}, {num(r.y_ach_lo, 4)}]", f"[{num(r.y_ach_hi, 4)}, {num(r.y_tight_hi, 4)}]"])
    emit("VV", "Table VV. Valid-vote shares: within-district slope", ["Election", "Assumptions", "Roll-based share (exact range)", "Valid-vote share, lower end: [outer bound, attainable]",
         "upper end: [attainable, outer bound]"], rows, long=True, size="scriptsize", colspec="llccc",
         notes="The exact lower end of the valid-vote range lies between the two numbers given; it is negative, so the direction is not established, when the attainable value is negative.")


def F20s():
    d = cat("rev_mover_*.csv"); d = d[(d.spec == "guFE") & (d.movement == "calib") & (d.delta == 0.1)]; rows = []
    for t_ in [0.05, 0.1, 0.2, 0.3]:
        r = [f"{t_:g}"]
        for sg in C4:
            q = d[(d.sg == int(sg)) & (d.kind == "bounds") & (d.t == t_)]
            r.append(iv(q.lo.iloc[0], q.hi.iloc[0]) if len(q) else "–")
        rows.append(r)
    emit("F20s", "Table F20s. Restricting how movers vote: residents who voted at another station vote within t of their home station's shares (within-district slope; mobility-calibrated movement, ±10 points)",
         ["t", "2022", "2024", "2025", "2026"], rows, size="scriptsize", colspec="lCCCC")


def F21s():
    d = cat("rev_anchor_*.csv"); rows = []
    for an, al in [("station", "station shares (main)"), ("station+gap", "shifted by district out-of-district gap"), ("station+gap+price", "shifted by gap and its price relation")]:
        dm = d[(d.cell == "dmin_eta0") & (d.anchor == an)]
        r = [al, " / ".join(num(dm[dm.sg == int(sg)].lo.iloc[0]) for sg in C4)]
        for sl in [None, 0.02]:
            for sg in C4:
                q = d[(d.anchor == an) & (d.cell == "calib") & (d.delta == 0.1) & (d.spec == "guFE") & (d.sg == int(sg)) & ((d.slack.isna()) if sl is None else (d.slack == sl))]
                r.append(iv(q.lo.iloc[0], q.hi.iloc[0]) if len(q) else "–")
        rows.append(r)
    emit("F21s", "Table F21s. The benchmark for out-of-district voters (within-district slope, mobility-calibrated movement, ±10 points)",
         ["Benchmark", "Smallest feasible tolerance, median (2022/2024/2025/2026)", "2022", "2024", "2025", "2026", "2022, + residents' early ballots", "2024", "2025", "2026"],
         rows, size="scriptsize", colspec="lL" + "C" * 8)


def F15bs():
    g = cat("disclosure_guarantee_2*.csv"); g = g[g.config.str.startswith("calib") | (g.config == "uniform eta=0.0")]; rows = []
    g = g.assign(o=g.config.map(lambda c: 0 if c.startswith("uniform") else 1)).sort_values(["sg", "o"], kind="stable")
    for r in g.itertuples():
        f = lambda p: f"{100 * (1 - getattr(r, f'Wmax_{p}') / (r.W0 if p in ('P2', 'P2b') else r.W0_free)):.0f}%"
        lab = "minimal movement" if r.config.startswith("uniform") else re.sub(r"\bcalib\b(?! lambda)", "mobility-calibrated movement", r.config).replace("calib lambda=0.5", "half the mobility-calibrated movement").replace(", delta=0.1", ", ±10 points").replace(", s=0.02", ", residents resemble")
        rows.append([Y[str(r.sg)], lab, num(r.W0), f("P2"), f("P2b"), f("P1"), f("P12")])
    emit("F15bs", "Table F15bs. Guaranteed share of the within-district range removed, by reporting change", ["Election", "Assumptions", "Current range", "All pooled modes by neighborhood", "Out-of-district early only (proposal)",
         "Headcounts only", "Both"], rows, long=True, size="scriptsize", colspec="ll" + "C" * 5,
         notes="Out-of-district voters are unrestricted unless ±10 points is stated. All pooled modes and Out-of-district early only: share of the current range in the same row removed. Headcounts only and Both: share removed of the range under the same composition assumptions but with movement unrestricted, since a headcount report replaces the movement assumption. Whether a report reveals the direction of the slope: Table C16.")


def D2s():
    p = rd("published_scale.csv"); rows = []
    for r in p[p.spec.isin(["gu FE", "gu FE + age"])].itertuples():
        mv = "mobility-calibrated movement" if r.movement == "calib" else ("returns and rolls only" if r.eta >= 1 else f"η = {r.eta:g}")
        if r.movement != "calib" and r.eta not in (1.0, 0.0): continue
        rows.append([r.spec, mv + ("" if pd.isna(getattr(r, "slack", np.nan)) else ", residents resemble"), f"±{100 * r.delta:.0f}" if r.delta < 1 else "none", iv(r.z_lo, r.z_hi, 2), num(r.published_point, 2)])
    emit("D2s", "Table D2s. The published 2026 allocation and the identified range (within-district slope, percentage points per 10 million won per pyeong)",
         ["Specification", "Movement", "Out-of-district tolerance", "Range consistent with data", "Published allocation"], rows, size="scriptsize", colspec="llccc")


def ED():
    """Point-identified benchmarks: election-day voters (residence-based) and in-zone stations (counted where cast)."""
    d = rd("election_day.csv"); rows = []
    for sp, lab, sc, dd in [("slope", "A. Within-district slope", 1, 3), ("contrast", "B. Higher- minus lower-price half (percentage points)", 100, 1)]:
        rows.append(("PANEL", lab))
        for sg in ELECTIONS:
            q = d[(d.sg == int(sg)) & (d.spec == sp)]
            g = lambda m, smp: (lambda r: num(sc * r.value.iloc[0], dd) if len(r) else "–")(q[(q.measure == m) & (q["sample"] == smp)])
            rows.append([Y[sg], g("election_day", "all"), g("election_day", "excl_gangnam3"), g("station", "all"), g("station", "excl_gangnam3")])
    rows.append(("PANEL", "C. Auxiliary diagnostics for the election-day slope: gu-clustered standard error; within-gu permutation p-value"))
    q = d[d.spec == "slope_inference"]
    pv = lambda p: "<0.001" if p < 0.001 else num(p, 3)
    for sg in ELECTIONS:
        a_ = q[(q.sg == int(sg)) & (q["sample"] == "all")].iloc[0]; e_ = q[(q.sg == int(sg)) & (q["sample"] == "excl_gangnam3")].iloc[0]
        rows.append([Y[sg], f"({num(a_.se_cluster)}); p {pv(a_.p_perm)}", f"({num(e_.se_cluster)}); p {pv(e_.p_perm)}", "", ""])
    emit("ED", "Table ED. Point-identified benchmarks: election-day voters and in-zone early stations",
         ["Election", "Election-day voters: all", "Election-day voters: without the three", "In-zone stations: all", "In-zone stations: without the three"],
         rows, size="footnotesize", colspec="l" + "C" * 4,
         notes="Conservative candidate's valid-vote share. Election-day ballots are counted in the voter's own voting district, so these slopes and contrasts "
               "describe registered residents who voted on election day and need no allocation assumption. In-zone station shares are counted where cast and include "
               "voters from other neighborhoods of the zone; 2012 had no in-zone early voting. Weights as in Table 2 (gu fixed effects; median split within gu). "
               "Without the three: Gangnam, Seocho and Songpa excluded from the weights. Panel C, auxiliary diagnostics only: the slopes above describe the observed "
               "neighborhoods exactly. The permutation p-value (prices permuted within each gu, 5,000 permutations, two-sided) assumes that dongs are exchangeable "
               "within a gu and ignores spatial dependence; prices were not randomly assigned. The clustered standard error reads the dongs as draws from a larger population.")


def OG():
    """Observed reference for the out-of-zone tolerance: out-of-zone minus in-zone early composition by jurisdiction."""
    d = rd("oz_gap.csv"); rows = []
    for sg, q in d.groupby("sg", sort=True):
        a = 100 * q.gap
        rows.append([Y[str(sg)], str(len(q)), num(a.median(), 1), f"{num(a.min(), 1)} to {num(a.max(), 1)}", num(a.abs().max(), 1),
                     num(100 * q.station_dev_median.median(), 1), num(100 * q.station_dev_max.max(), 1)])
    emit("OG", "Table OG. Out-of-zone and in-zone early voters by counting jurisdiction (conservative valid-vote share, percentage points)",
         ["Election", "Jurisdictions", "Out-of-zone minus in-zone: median", "Range", "Largest absolute gap",
          "In-zone stations: median absolute deviation from their jurisdiction", "Largest station deviation"],
         rows, size="footnotesize", colspec="l" + "C" * 6,
         notes="Each jurisdiction's out-of-zone early ballots are published as one total, so the first three columns describe whole districts "
               "(constituencies in 2024). The tolerance δ bounds the same difference for each neighborhood's residents, which is not observed and may vary "
               "more within a district than these district-level gaps; the station columns show how far neighborhoods' in-zone shares depart from their "
               "district's in-zone share. These are references for δ, not tests of it.")


def DIR():
    """Price-aligned departures: breakdown points kappa* and the observed station reference."""
    d = rd("directional.csv"); r = rd("directional_reference.csv"); rows = []
    b = d[d.kappa == "breakdown"]
    for sg in ["20220309", "20240410", "20250603", "20260603"]:
        q = r[r.sg == int(sg)].station_gradient
        cell = lambda smp, dl: (lambda v: "∞" if np.isinf(v) else ("none" if np.isnan(v) else ("<0.001" if 0 < v < 0.0005 else num(v))))(float(b[(b.sg == int(sg)) & (b["sample"] == smp) & (b.delta == dl)].lo.iloc[0]))
        kb = rd("further_restrictions_reference.csv"); kb = kb[kb.sg == int(sg)].kappa_between.iloc[0]
        rows.append([Y[sg], cell("all", 0.1), cell("all", 1.0), cell("excl_gangnam3", 0.1), cell("excl_gangnam3", 1.0), num(q.median()), num(q.abs().max()), num(kb)])
    emit("DIR", "Table DIR. How far residents' early-vote departures may align with price before the within-district slope loses its sign",
         ["Election", "κ*: all, out-of-zone ±10", "κ*: all, out-of-zone unrestricted", "κ*: without the three, ±10", "κ*: without the three, unrestricted",
          "Station gradient: median", "Station gradient: largest absolute", "Between-jurisdiction reference"], rows, size="footnotesize", colspec="l" + "C" * 7,
         notes="Mobility-calibrated movement; the restriction on residents' early-vote composition (s) is replaced by |g_u| ≤ κ, where g_u is the slope, within "
               "counting jurisdiction u, of residents' early-vote departures from their benchmarks (in-zone and out-of-zone, as a share of the roll) on log price. "
               "κ*: the largest κ at which the lower end of the within-district slope range stays positive (bisection width 0.0002; ∞: positive without the "
               "restriction). Station gradient: the same slope computed for observed in-zone station ballots, over jurisdictions; stations also count "
               "non-residents. Between-jurisdiction reference: the slope residents' departures would have if, within jurisdictions, early-vote gaps varied with price as "
               "they do across counting jurisdictions (gu; National Assembly constituencies in 2024), |b_K| (in-zone early ballots / H) + |b_B − b_K| (out-of-zone ballots / H), with b_K and b_B the cross-district slopes "
               "of the in-zone and out-of-zone early minus election-day gaps on log price. The slope is identified as positive when residents' departures are no "
               "more aligned with price than κ*.")


def AT():
    """Age composition held fixed, and the tercile contrast."""
    d = rd("age_tercile.csv"); rows = []
    lab = {"slope": "Slope", "slope_age": "Slope, age held fixed", "tercile": "Top minus bottom tercile (points)"}
    for est in ["slope", "slope_age", "tercile"]:
        rows.append(("PANEL", lab[est]))
        sc, dd = (100, 1) if est == "tercile" else (1, 3)
        for sg in ["20220309", "20240410", "20250603", "20260603"]:
            g = lambda smp: d[(d.sg == int(sg)) & (d["sample"] == smp) & (d.estimand == est)].iloc[0]
            a, e = g("all"), g("excl_gangnam3")
            rows.append([Y[sg], num(sc * a.election_day, dd), iv(sc * a.lo, sc * a.hi, dd), num(sc * e.election_day, dd), iv(sc * e.lo, sc * e.hi, dd)])
    emit("AT", "Table AT. Within-district relation with age composition held fixed, and the tercile contrast",
         ["Election", "All of Seoul: election-day voters", "All of Seoul: all residents, main assumptions", "Without the three: election-day voters", "Without the three: all residents, main assumptions"],
         rows, size="footnotesize", colspec="l" + "C" * 4,
         notes="Election-day voters: valid-vote share, point-identified. All residents: roll-based share z, mobility-calibrated movement, out-of-zone within 10 points, s = 0.02. "
               "Age held fixed: slope weights from a regression of log price on gu dummies, the mean age of residents aged 18 and over and the share aged 60 and over "
               "(Ministry of the Interior and Safety, April 2026; a proxy for earlier elections). Tercile: mean of each gu's top third by price minus its bottom third, "
               "gu weights as for the median split.")


def R4():
    """delta*, movers with composition, out-of-zone alignment, U."""
    d = rd("further_restrictions_bounds.csv"); r = rd("further_restrictions_reference.csv"); rows = []
    for sg in ["20220309", "20240410", "20250603", "20260603"]:
        g = lambda smp, an, par=None: d[(d.sg == int(sg)) & (d["sample"] == smp) & (d.analysis == an) & ((d.param == par) if par is not None else d.param.isna())].iloc[0]
        st = lambda v: "∞" if np.isinf(v) else ("none" if np.isnan(v) else ("<0.001" if 0 < v < 0.0005 else num(v)))
        rr = r[r.sg == int(sg)].iloc[0]
        rows.append([Y[sg], st(g("all", "delta_star").lo), st(g("excl_gangnam3", "delta_star").lo),
                     iv(g("all", "s002_movers", 0.1).lo, g("all", "s002_movers", 0.1).hi), iv(g("excl_gangnam3", "s002_movers", 0.1).lo, g("excl_gangnam3", "s002_movers", 0.1).hi),
                     st(g("all", "oz_align_star").lo), st(g("excl_gangnam3", "oz_align_star").lo), f"{100 * rr.U_share_of_H:.2f}%"])
    emit("R4", "Table R4. Further restrictions: the out-of-zone tolerance, movers' composition and price-aligned out-of-zone departures (within-district slope, z)",
         ["Election", "δ* at s = 0.02: all", "δ*: without the three", "s = 0.02 and movers within 10 points: all", "Same, without the three",
          "κ_P*: all", "κ_P*: without the three", "U, share of H"], rows, size="footnotesize", colspec="l" + "C" * 7,
         notes="Mobility-calibrated movement throughout. δ*: the largest out-of-zone tolerance at which the lower end of the range stays positive with s = 0.02 "
               "(none: not positive at the smallest feasible tolerance). Movers: residents who voted at another station of their zone vote within 10 points of "
               "their home station's composition, with s = 0.02 and δ = 0.1 (5 points gives nearly the same ranges). κ_P*: with δ removed and s = 0.02, the largest "
               "bound on the within-jurisdiction slope of residents' out-of-zone departures from their station's composition on log price at which the slope stays "
               "positive. U: removed residents who cast no counted ballot (allocated without restriction), as a share of H.")


MAP = {"B1": "A1", "C1": "B1", "C2": "B2", "F1": "C1", "F3": "C2", "F4": "C3", "F6b": "C4", "F7b": "C5", "F7c": "C6", "F20s": "C7", "F8a": "C8", "F21s": "C9",
       "F9": "C10", "F18": "C11", "F15bs": "C12", "F16": "C13", "F17a": "C14", "VV": "C15", "F15c": "C16", "SC": "C17", "SCy": "C18", "SCs": "C19", "ED": "C20", "OG": "C21", "DIR": "C22", "AT": "C23", "F13a": "C24", "R4": "C25", "D1": "D1", "D2s": "D2"}


def SC():
    """Beyond Gangnam in detail: every column of Table 2 without the three southeastern gu, and valid-vote shares."""
    import glob as gl
    d = pd.concat([pd.read_csv(f) for f in sorted(gl.glob(str(RES / "spatial_scope_*.csv")))]); rows = []
    cols = ["A", "B", "C", "D", "E"]
    for sp, lab, sc, dd in [("slope", "A. Within-district slope without 강南, 서초 and 송파 (z)".replace("南", "남"), 1, 3),
                            ("contrast", "B. Expensive minus cheaper half without the three (z, points)", 100, 1)]:
        rows.append(("PANEL", lab))
        for sg in ELECTIONS:
            q = d[(d.sg == int(sg)) & (d["sample"] == "excl_gangnam3") & (d.spec == sp)].set_index("column")
            rows.append([Y[sg], num(sc * q.loc["conv"].z_lo, dd)] + [iv(sc * q.loc[c].z_lo, sc * q.loc[c].z_hi, dd) if c in q.index else "–" for c in cols])
    emit("SC", "Table SC. Beyond Gangnam: the within-district relation without 강남, 서초 and 송파",
         ["Election", "Conv.", "(A) Returns and rolls only", "(B) Minimal movement", "(C) = (B) + out-of-district within 10 points",
          "(D) Mobility-calibrated", "(E) Main"], rows, size="scriptsize", colspec="lc" + "C" * 5,
         notes="Columns as in Table 2; roll-based share z. Valid-vote shares: Table C18.")


def SCy():
    """Valid-vote shares with and without the three southeastern gu, main assumptions."""
    import glob as gl
    d = pd.concat([pd.read_csv(f) for f in sorted(gl.glob(str(RES / "spatial_scope_*.csv")))]); rows = []
    for sg in C4:
        cells = []
        for sp, sc, dd in [("slope", 1, 3), ("contrast", 100, 1)]:
            for smp in ["all", "excl_gangnam3"]:
                q = d[(d.sg == int(sg)) & (d["sample"] == smp) & (d.spec == sp) & (d.column == "E")].iloc[0]
                cells.append(f"[{num(sc * q.y_tight_lo, dd)}, {num(sc * q.y_ach_lo, dd)}]")
        rows.append([Y[sg]] + cells)
    emit("SCy", "Table SCy. Valid-vote slope lower bounds with and without the three southeastern districts",
         ["Election", "Slope: all", "Slope: without the three", "Contrast (points): all", "Contrast (points): without the three"], rows, size="footnotesize",
         colspec="l" + "C" * 4,
         notes="Each entry gives a guaranteed outer bound and an attainable value for the lower end of the valid-vote range; the exact lower end lies between "
               "them. The direction is established when the first value is positive and not established when the second is negative.")


def SCs():
    """How far the residents' early-composition slack can be relaxed, with and without the three southeastern gu."""
    import glob as gl
    d = pd.concat([pd.read_csv(f) for f in sorted(gl.glob(str(RES / "scope_sstar_*.csv")))]); rows = []
    def cell(r):
        if np.isinf(r.s_lo): return "∞"
        if r.s_lo <= r.s_min + 1e-12: return "none"
        return f"{r.s_lo:.3f}"
    for sg in C4:
        for mv, ml in [("lambda=1", "mobility-calibrated"), ("unrestricted", "unrestricted")]:
            for dl in [0.1, 0.2]:
                q = d[(d.sg == int(sg)) & (d.movement == mv) & (d.delta == dl)]
                g = lambda smp, sp: cell(q[(q["sample"] == smp) & (q.spec == sp)].iloc[0])
                rows.append([Y[sg], ml, f"±{100 * dl:.0f}", g("all", "slope"), g("excl_gangnam3", "slope"), g("all", "contrast"), g("excl_gangnam3", "contrast")])
    emit("SCs", "Table SCs. Sensitivity thresholds s* with and without the three southeastern districts",
         ["Election", "Movement", "Out-of-district tolerance (points)", "Slope: all", "Slope: without the three", "Contrast: all", "Contrast: without the three"],
         rows, size="footnotesize", colspec="ll" + "C" * 5,
         notes="s*: the largest slack s at which the lower end of the range of the within-district slope (or of the expensive-minus-cheaper contrast) is positive, "
               "with movement and the out-of-district tolerance held fixed; bisection width 0.0012, lower end reported. The main setting uses s = 0.02, so a "
               "relation is established there when s* exceeds 0.02. ∞: positive however much residents' early ballots depart; none: not positive for any s.")


def renumber_and_supplement():
    """One naming scheme: main tables table1-table6, Online Appendix tableA1 ... tableD2 (MAP), supplementary tables S1 ...
    (collected in docs/supplementary_results.md). Cross-references between tables are rewritten to the final numbers;
    intermediate files are removed from paper/tables."""
    import re, glob as gl, os
    from vwn.paths import TAB, ROOT
    main = {f"table{k}" for k in range(1, 7)}
    final = main | {f"table{v}" for v in MAP.values()}
    names = {os.path.basename(f)[:-3] for f in gl.glob(str(TAB / "*.md"))}
    rest = sorted(names - final - set(MAP))
    label = {**MAP, **{name: f"S{k}" for k, name in enumerate(rest, 1)}}   # generator label -> number in the paper
    pat = re.compile(r"\bTables? (%s)\b" % "|".join(sorted(map(re.escape, label), key=len, reverse=True)))
    relabel = lambda t: pat.sub(lambda m: m.group(0).replace(m.group(1), label[m.group(1)]), t)
    for old, new in MAP.items():
        for ext in ("md", "tex"):
            f = TAB / f"{old}.{ext}"
            if f.exists():
                (TAB / f"table{new}.{ext}").write_text(relabel(f.read_text()))
    for name in names & set(MAP):                                  # generator copies of appendix tables
        for ext in ("md", "tex"):
            if (TAB / f"{name}.{ext}").exists(): os.remove(TAB / f"{name}.{ext}")
    sup = ["# Supplementary results (not part of the submitted appendix)", "",
           "Additional tables generated from `results/` by `analysis/output/appendix_tables.py`; docs/replication_map.md gives the "
           "script and result file behind each.", ""]
    for k, name in enumerate(rest, 1):
        txt = relabel((TAB / f"{name}.md").read_text())
        sup += [txt, ""]
        for ext in ("md", "tex"):
            if (TAB / f"{name}.{ext}").exists(): os.remove(TAB / f"{name}.{ext}")
    for f in gl.glob(str(TAB / "app_*")) + gl.glob(str(TAB / "t[1-6]_*")): os.remove(f)   # files with other name prefixes
    (ROOT / "docs" / "supplementary_results.md").write_text("\n".join(sup))


def build(NUM):
    for f in [ED, OG, DIR, AT, R4, SC, SCy, SCs, C2, VV, F20s, F21s, F15bs, D2s, F1, F2, F3, F4, F5, F6, F6b, F7, F7b, F15b, F15c, F18, F7c, F19, F20, F21, F8, F9, F10, F11, F12, F13, F14, F15, F16, F17, A_tables, C_tables, D_tables, E_tables]:
        try:
            f()
        except Exception as e:
            print("FAILED", f.__name__, repr(e))
