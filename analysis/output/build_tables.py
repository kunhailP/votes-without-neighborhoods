"""Build every table of the manuscript, the Online Appendix and the supplementary results
(docs/supplementary_results.md) from results/ (no number is typed by hand).
Also writes paper/tables/numbers.json with the values quoted in the text, so prose can be checked against results.
Usage: python analysis/output/build_tables.py"""
import glob
import json
import math
import numpy as np
import pandas as pd
from vwn.paths import RES, TAB, DATA
from vwn.data import ELECTIONS, YEAR, setup
from tablelib import emit, iv, num, bp

Y = YEAR; C4 = ["20220309", "20240410", "20250603", "20260603"]; C5 = ["20170509"] + C4
SPN = {"guFE": "Within-gu", "pooled": "City-wide", "sggFE": "Within-constituency"}
NUM = {}


def rd(f, **kw):
    return pd.read_csv(f"{RES}/{f}", **kw)


def grid(sg, sp, eta, dl):
    g = rd(f"main_grid_{sg}.csv", dtype={"delta": str})
    q = g[(g.kind == "bound") & (g.spec == sp) & (g.eta == eta) & (g.delta == str(dl))]
    return (q.lo.iloc[0], q.hi.iloc[0]) if len(q) else (np.nan, np.nan)


def conv(sg, sp):
    g = rd(f"main_grid_{sg}.csv", dtype={"delta": str})
    return g[(g.kind == "baseline") & (g.spec == sp) & (g.method == "exclude")].value.iloc[0]


def calib(sg, sp, dl, mult=1.0):
    c = rd(f"calibrated_bounds_{sg}.csv"); q = c[(c.spec == sp) & (c.delta == dl) & (c.mult == mult)]
    return (q.lo.iloc[0], q.hi.iloc[0]) if len(q) else (np.nan, np.nan)


def comp(sg, sp, dl, dF, eta, calib_=True):
    c = rd(f"composition_{sg}.csv"); q = c[(c.kind == "bounds") & (c.calib == calib_) & (c.spec == sp) & (c.delta == dl) & (c.dF == str(dF)) & (c.eta == eta)]
    return (q.lo.iloc[0], q.hi.iloc[0]) if len(q) else (np.nan, np.nan)


def gapadj(sg, sp, variant="gu-level price slope", s=0.02):
    g = rd("gap_adjusted.csv"); q = g[(g.sg == int(sg)) & (g.spec == sp) & (g.variant == variant) & (g.slack == s)]
    return (q.lo.iloc[0], q.hi.iloc[0]) if len(q) else (np.nan, np.nan)


def put(key, v):
    NUM[key] = None if v is None or (isinstance(v, float) and math.isnan(v)) else (v if isinstance(v, (list, tuple, str, dict)) else float(v))


# ---------------------------------------------------------------- Table 1: data
def table_data():
    rows = []
    for sg in ELECTIONS:
        units, G, idx, x, labs = setup(sg)
        A = sum(G[u][0]["Avotes"].sum() for u in units); K = sum(G[u][0]["K"].sum() for u in units)
        Pp = sum(G[u][0]["Bc"].sum() for u in units); Q = sum(G[u][0]["Gc"].sum() for u in units)
        tot = A + K + Pp + Q
        r = [max(0, 0) for _ in [0]]
        forced = sum(int((np.maximum(0, G[u][0]["K"].sum(1) - (G[u][1] - G[u][0]["D"])) > 0).sum()) for u in units)
        zones = "155 council constituencies" if sg == "20260603" else ("48 constituencies" if sg == "20240410" else "25 gu")
        rows.append([f"{Y[sg]} {'pres.' if sg not in ('20240410', '20260603') else ('leg.' if sg == '20240410' else 'mayor')}",
                     "48 constituencies" if sg == "20240410" else "25 gu", zones if K > 0 else "–", f"{len(idx)}", f"{int((~np.isnan(x)).sum())}",
                     f"{100 * (Pp + Q) / tot:.1f}%", "–" if K == 0 else f"{100 * K / tot:.1f}%", "–" if K == 0 else f"{100 * Pp / (Pp + K):.1f}%", f"{forced}"])
        put(f"pooled_share_{sg}", (Pp + Q) / tot); put(f"indistrict_share_{sg}", K / tot)
    emit("table1", "Table 1. Elections, reporting units and ballot coverage",
         ["Election", "Pooled ballots reported for", "In-district early zone", "Dongs", "Dongs with price", "Pooled share", "In-district early share",
          "Out-of-district share of early ballots", "Stations with forced movement"], rows,
         notes="Shares are of all ballots cast in Seoul. Pooled ballots: out-of-district early, at-home, shipboard and overseas. "
               "\"Out-of-district share of early ballots\" is P/(P+K) over Seoul. Forced movement: stations whose in-district early ballots exceed "
               "their dong's removed residents (r_j > 0). 2012 had no in-district early voting.",
         colspec="l" + "C" * 8, size="scriptsize")


# ---------------------------------------------------------------- Table 2: identified sets
def table_sets():
    hdr = ["Election", "Conv.", "Election-day voters (exact; valid-vote share y)", "(A) Returns and rolls only", "(B) Minimal movement", "(C) = (B) + out-of-district voters within 10 points",
           "(D) Mobility-calibrated movement + out-of-district within 10 points", "(E) = (D) + residents' early ballots resemble their neighborhood", "(F) = (E), price-dependent benchmark"]
    rows = []; ed = rd("election_day.csv"); ed = ed[ed["sample"] == "all"]
    edv = lambda sg, spec, sc=1.0, dd=3: num(sc * ed[(ed.sg == int(sg)) & (ed.measure == "election_day") & (ed.spec == spec)].value.iloc[0], dd)
    for sp in ["guFE", "sggFE"]:
        if sp == "guFE": rows.append(("PANEL", "A. Within-district slope"))
        for sg in ELECTIONS:
            if sp == "sggFE" and sg != "20240410": continue
            cal = sg in C4
            r = [Y[sg], num(conv(sg, sp)), edv(sg, "slope") if sp == "guFE" else "–", iv(*grid(sg, sp, 1.0, 1.0)), iv(*grid(sg, sp, 0.0, 1.0)), iv(*grid(sg, sp, 0.0, 0.1)),
                 iv(*calib(sg, sp, 0.1)) if cal else "–", iv(*comp(sg, sp, 0.1, ("slack", 0.02), 1.0)) if cal else "–", iv(*gapadj(sg, sp)) if cal else "–"]
            if sp == "guFE": rows.append(r)
            else: sgg = r
            for k, v in [("acct", grid(sg, sp, 1.0, 1.0)), ("eta0", grid(sg, sp, 0.0, 1.0)), ("eta0d01", grid(sg, sp, 0.0, 0.1))] + \
                    ([("cal", calib(sg, sp, 0.1)), ("cals02", comp(sg, sp, 0.1, ("slack", 0.02), 1.0)), ("gap", gapadj(sg, sp))] if cal else []):
                put(f"{k}_{sp}_{sg}", list(map(float, v)))
            put(f"conv_{sp}_{sg}", conv(sg, sp))
    ct = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{RES}/contrast_2*.csv"))])
    ct = ct[ct.kind == "median"]
    def cv(sg, cell):
        q = ct[(ct.sg == int(sg)) & (ct.cell == cell)]
        if not len(q) or pd.isna(q.z_lo.iloc[0]): return "–"
        return num(100 * q.z_lo.iloc[0], 1) if cell == "conventional" else iv(100 * q.z_lo.iloc[0], 100 * q.z_hi.iloc[0], 1)
    rows.append(("PANEL", "B. Within-district contrast: expensive minus cheaper half of neighborhoods (percentage points)"))
    for sg in ELECTIONS:
        cal = sg in C4
        rows.append([Y[sg], cv(sg, "conventional"), edv(sg, "contrast", 100, 1), cv(sg, "accounting"), cv(sg, "eta0_d1"), cv(sg, "eta0_d0.1"),
                     cv(sg, "calib_d0.1") if cal else "–", cv(sg, "calib_d0.1_s0.02") if cal else "–", "–"])
        for cell in ["conventional", "accounting", "eta0_d1", "eta0_d0.1", "calib_d0.1", "calib_d0.1_s0.02"]:
            q = ct[(ct.sg == int(sg)) & (ct.cell == cell)]
            if len(q): put(f"delta_{cell}_{sg}", [100 * q.z_lo.iloc[0], 100 * q.z_hi.iloc[0], 100 * q.y_tight_lo.iloc[0], 100 * q.y_tight_hi.iloc[0]])
    emit("table2", "Table 2. Within-district associations under alternative assumptions",
         hdr, rows, colspec="lc" + "C" * 7, size="footnotesize",
         notes="Bold ranges include zero; their sign is not identified. Panel A: within-district slope of the conservative share among residents (roll-based share z) on log median apartment price per square "
               "meter; 0.1 means a neighborhood with prices twice as high has a share about 7 points higher. Within National Assembly constituencies in 2024 "
               f"the ranges are {sgg[3].strip('*')} (A), {sgg[5].strip('*')} (C), {sgg[6].strip('*')} (D) and {sgg[7].strip('*')} (E). Panel B: "
               "mean share of each district's neighborhoods priced above its median minus that of the others, averaged over districts weighted by neighborhoods with price data, in percentage points. "
               "Conv.: published neighborhood rows, pooled ballots dropped. Election-day voters (exact): the valid-vote share among residents who voted on election day, point-identified (Online Appendix Table C20). "
               "(A) every allocation consistent with the counts, rolls and statutory zones; (B) minimal movement; (C) adds out-of-zone ballots within 10 points of the station; "
               "(D) replaces (B) with mobility-calibrated movement; (E) adds residents' early ballots within their station's departure plus 2 points of the benchmark; "
               "(F) price-dependent benchmark. Definitions in Section 3.4 and Online Appendix A.")


# ---------------------------------------------------------------- Table 5: what a reversal requires
def table_reversal():
    ld = rd("least_departure.csv"); det = rd("least_departure_detail.csv"); rows = []
    for sg in C4:
        ep = rd(f"edge_profile_{sg}.csv"); rg = rd(f"region_{sg}.csv")
        for dl in [0.1, 0.2]:
            q = ld[(ld.sg == int(sg)) & (ld.delta == dl)]; lb = q[q.alloc == "lower bound"].iloc[0]
            x = rg[(rg.movement == "lambda=1") & (rg.delta == dl)].iloc[0]
            sstar = np.inf if np.isinf(x.s_lo) else (0.0 if x.s_lo <= x.s_min + 1e-12 else x.s_lo)
            e = ep[ep.delta == dl]
            gap = "no reversal" if len(e) == 0 else f"{num(100 * (e.mover_cons - e.stayer_cons).min(), 0)} to {num(100 * (e.mover_cons - e.stayer_cons).max(), 0)}"
            d = det[(det.sg == int(sg)) & (det.delta == dl)]
            if len(d):
                d = d.iloc[0]; early = f"{d.depF_total:,.0f}"; top = f"{100 * d.share_depF_top_leverage:.0f}%"; pool = f"{d.depP_total:,.0f} ({d.depP_min_feasible:,.0f})"
                put(f"ldet_{sg}_{dl}", dict(early=d.depF_total, top=d.share_depF_top_leverage, pooled=d.depP_total, pmin=d.depP_min_feasible))
            else: early = top = pool = "no reversal"
            rows.append([Y[sg], f"{100 * dl:.0f}", "∞" if np.isinf(sstar) else ("none" if sstar == 0 else num(sstar)), gap, early])
            put(f"lb_{sg}_{dl}", dict(slope=lb.slope, med=lb.abs_dep_median))
            put(f"edge_{sg}_{dl}", None if len(e) == 0 else dict(s=float(x.s_lo), gap_min=float((e.mover_cons - e.stayer_cons).min()), gap_max=float((e.mover_cons - e.stayer_cons).max())))
    emit("table5", "Table 5. Assumptions and allocations that permit a non-positive slope",
         ["Election", "Out-of-district voters within (points)", "Largest additional tolerance s with a positive slope",
          "First reversing allocation: movers minus stayers, conservative share (points)", "Fewest residents' early ballots that must depart to reverse"],
         rows, colspec="l" + "C" * 4, size="footnotesize",
         notes="Mobility-calibrated movement. s: residents' early ballots may depart from their neighborhood benchmark (election-day share shifted by the district's early-vote gap) by their "
               "station's departure plus s; ∞: positive however much they depart; none: not positive even when they depart only as much as their station. "
               "First reversing allocation: the one with the lowest slope at s just above that value; movers voted at another station of their zone, stayers at "
               "their own; range over price terciles. Last column: among allocations with a non-positive slope, the fewest residents' conservative early ballots "
               "departing from the benchmark (out-of-district departures and concentration in Online Appendix Table C6). Each reversal is minimal only in its own "
               "metric, with other assumptions fixed.")


def table_disclosure():
    g = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{RES}/disclosure_guarantee_2*.csv"))])
    rows = []
    for sg in C5:
        q = g[g.sg == int(sg)].set_index("config")
        rem = lambda cfg, p="P2": (1 - q.loc[cfg, f"Wmax_{p}"] / (q.loc[cfg, "W0"] if p in ("P2", "P2b") else q.loc[cfg, "W0_free"])) if cfg in q.index else np.nan
        pct = lambda v: "–" if pd.isna(v) else f"{100 * v:.0f}%"
        mc = "calib, delta=0.1, s=0.02"
        if mc not in q.index: continue
        W0 = q.loc[mc, "W0"]
        r = [Y[sg], f"{W0:.2f}", pct(rem(mc, "P2b")), f"{q.loc[mc, 'Wmax_P2b']:.2f}", pct(rem(mc)), f"{q.loc[mc, 'Wmax_P2']:.2f}"]
        rows.append(r)
        for cfg in q.index:
            put(f"guar_{sg}_{cfg}", {p: rem(cfg, p) for p in ["P2", "P2b", "P1", "P12"]} | dict(W0=q.loc[cfg, "W0"], W0_free=q.loc[cfg, "W0_free"]))
    emit("table6", "Table 6. Guaranteed reductions in uncertainty under residence reporting",
         ["Election", "Current range width", "Proposal: out-of-district early ballots by neighborhood, share removed", "Proposal: maximum remaining width",
          "All pooled modes by neighborhood, share removed", "All pooled modes: maximum remaining width"], rows, colspec="l" + "C" * 5, size="footnotesize",
         notes="All columns describe the width of the within-district slope range or the guaranteed fraction of that width removed. Main assumptions: Table 2, column E. Proposal: out-of-district early ballots reported as aggregate counts by the voter's registered neighborhood, at-home "
               "and overseas ballots kept pooled. All pooled modes: out-of-district early, at-home and overseas ballots by neighborhood. Maximum remaining width: the largest "
               "difference in the within-district slope between two allocations that the report could not tell apart, which bounds the range left whatever the true "
               "allocation. Other assumptions and headcount reporting: Online Appendix Table C12.")


# ---------------------------------------------------------------- Table 3: beyond Gangnam
SETTING = {"20121219": "A", "20170509": "C"}   # elections without mobility data: most informative column available


def table_scope():
    gr = rd("gu_regression.csv"); gr = gr[gr.level == "gu"].set_index("sg"); rows = []
    for sg in ELECTIONS:
        d = rd(f"spatial_scope_{sg}.csv"); col = SETTING.get(sg, "E")
        g = lambda smp, sp, scale=1.0, dd=3: (lambda q: iv(scale * q.z_lo, scale * q.z_hi, dd))(d[(d["sample"] == smp) & (d.spec == sp) & (d.column == col)].iloc[0])
        r = gr.loc[int(sg)]
        rows.append([Y[sg] + ("" if col == "E" else f" ({col})"), num(r.slope), num(r.slope_excl3), g("all", "slope"), g("excl_gangnam3", "slope"),
                     g("all", "contrast", 100, 1), g("excl_gangnam3", "contrast", 100, 1)])
        for smp in ["all", "excl_gangnam3"]:
            for sp in ["slope", "contrast"]:
                for c in d[(d["sample"] == smp) & (d.spec == sp)].column.unique():
                    q = d[(d["sample"] == smp) & (d.spec == sp) & (d.column == c)].iloc[0]
                    put(f"scope_{smp}_{sp}_{c}_{sg}", [float(q.z_lo), float(q.z_hi), float(q.y_tight_lo), float(q.y_ach_lo), float(q.y_ach_hi), float(q.y_tight_hi)])
    # Panel B: how far the 2026 conclusions survive relaxing residents' early composition (same source as Online Appendix C19)
    ss = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(RES / "scope_sstar_*.csv")))])
    ss = ss[ss.sg == 20260603]
    def sstar(r):
        if np.isinf(r.s_lo): return "∞"
        if r.s_lo <= r.s_min + 1e-12: return "none"
        return f"{r.s_lo:.3f}"
    rows = [("PANEL", "A. Across districts: point values; within districts: ranges"), *rows,
            ("PANEL", "B. 2026 sensitivity thresholds s* (not slopes): largest additional departure at which the lower end stays positive; main setting s = 0.02")]
    for mv, ml in [("lambda=1", "Mobility-calibrated"), ("unrestricted", "Unrestricted movement")]:
        for dl in [0.1, 0.2]:
            q = ss[(ss.movement == mv) & (ss.delta == dl)]
            g = lambda smp, sp: sstar(q[(q["sample"] == smp) & (q.spec == sp)].iloc[0])
            rows.append([f"{ml}, ±{100 * dl:.0f}", "–", "–", g("all", "slope"), g("excl_gangnam3", "slope"), g("all", "contrast"), g("excl_gangnam3", "contrast")])
    emit("table3", "Table 3. Associations with and without Gangnam, Seocho and Songpa",
         ["Election", "Across districts: all", "Across districts: without the three", "Within districts, slope: all", "Within districts, slope: without the three",
          "Expensive minus cheaper half (points): all", "Expensive minus cheaper half (points): without the three"], rows, colspec="l" + "C" * 6, size="footnotesize",
         notes="Bold ranges include zero; their sign is not identified. Across districts: slope of the valid-vote share on log price across districts (point values, no allocation assumption). "
               "Within districts: ranges in z under the main assumptions (Table 2, column E); 2012 under column A and 2017 under column C, as those elections lack mobility data. "
               "Without the three: Gangnam, Seocho and Songpa dropped from the regression and the contrast, all accounting constraints kept. Panel B: s* with movement and the out-of-zone tolerance "
               "(±10 or ±20 points) held fixed; a relation is established at the main setting when s* exceeds 0.02. ∞: positive however much residents' early ballots depart; none: not positive for any s (Online Appendix Table C19).")


# ---------------------------------------------------------------- Table 4: the 2026 zones
def table_zones():
    z = rd("zones_2026.csv"); rows = []
    lab = {"accounting only": "Returns and rolls only", "minimum movement, delta=0.1": "Minimal movement, out-of-district within 10 points",
           "eta=0.1, delta=0.1": "Uniform movement (η = 0.1), out-of-district within 10 points",
           "calibrated, delta=0.1": "Mobility-calibrated movement, out-of-district within 10 points (D)",
           "calibrated, delta=0.1, s=0.02": "Main assumptions (E)"}
    for cell, l in lab.items():
        q = z[(z.cell == cell) & (z.spec == "guFE")].set_index("variant")
        rows.append([l, iv(q.loc["no zone restriction"].lo, q.loc["no zone restriction"].hi), iv(q.loc["statutory zones (main)"].lo, q.loc["statutory zones (main)"].hi)])
        put(f"zones_{cell}", [float(q.loc[v].lo) for v in ["no zone restriction", "statutory zones (main)"]] + [float(q.loc[v].hi) for v in ["no zone restriction", "statutory zones (main)"]])
    emit("table4", "Table 4. Within-district slopes with and without statutory zones, 2026",
         ["Assumptions", "Zones ignored: in-district early ballots may be cast anywhere in the district", "Statutory zones: only within the voter's council constituency"],
         rows, colspec="L" + "C" * 2, size="footnotesize",
         notes="Bold ranges include zero; their sign is not identified. Roll-based share z. The zones are the 155 district-council constituencies, about three neighborhoods each. Rows with uniform movement hold the "
               "amount of movement fixed, so the comparison isolates the zone rule; the mobility-calibrated rows recalibrate movement to the zone definition. "
               "Adding the council contest's published headcounts changes the statutory-zone ranges by at most 0.003 (Online Appendix Table C2).")


if __name__ == "__main__":
    table_data(); table_sets(); table_scope(); table_zones(); table_reversal(); table_disclosure()
    import appendix_tables
    appendix_tables.build(NUM)
    appendix_tables.renumber_and_supplement()
    json.dump(NUM, open(TAB / "numbers.json", "w"), indent=1, ensure_ascii=False, default=float)
    print("tables written:", len(glob.glob(str(TAB / "*.tex"))))
