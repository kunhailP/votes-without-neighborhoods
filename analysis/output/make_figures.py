"""Figures 1-4 of the manuscript (Figure 1 is a schematic; Figures 2-4 from results/). Usage: python analysis/output/make_figures.py"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd
import glob
from vwn.paths import RES, FIG, RAW
from vwn.data import ELECTIONS, YEAR, norm

plt.rcParams.update({"font.family": ["DejaVu Sans", "Noto Sans CJK KR"], "font.size": 8.5, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#555", "axes.labelcolor": "#222", "xtick.color": "#444", "ytick.color": "#444",
                     "axes.titlesize": 9, "axes.titleweight": "bold", "savefig.dpi": 300, "savefig.bbox": "tight"})
INK, MUTED, GRID = "#222222", "#6b6b6b", "#e4e4e0"
# categorical palette and an ordinal blue ramp for the assumption ladder
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
RAMP = ["#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#104281"]
LAB = {"20121219": "2012 pres.", "20170509": "2017 pres.", "20220309": "2022 pres.", "20240410": "2024 leg.", "20250603": "2025 pres.", "20260603": "2026 mayor"}


def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf"); fig.savefig(FIG / f"{name}.png"); plt.close(fig)


def fig_flow():
    fig, ax = plt.subplots(figsize=(7.2, 3.3)); ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")
    def box(x, y, w, h, text, fc, ec="#444"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=fc, ec=ec, lw=0.8))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=7.6, color=INK, linespacing=1.25)
    box(0.1, 2.4, 1.7, 1.2, "Registered\nresidents of\nneighborhood i", "#efefec")
    modes = [("Election day\n(own voting district)", "Reported in neighborhood i\n(residence matches)", "#d9ecd9"),
             ("In-zone early,\nown neighborhood's station", "Reported in neighborhood i\n(residence matches)", "#d9ecd9"),
             ("In-zone early, another\nneighborhood's station", "Reported in neighborhood j\n(residence differs)", "#f6d3d3"),
             ("Out-of-zone early\n(return envelope)", "District total\n(constituency total in 2024)", "#fbe6cc"),
             ("At-home, shipboard,\noverseas", "District total\n(constituency total in 2024)", "#fbe6cc")]
    for k, (m, r, c) in enumerate(modes):
        y = 4.9 - k * 1.15
        box(2.6, y, 3.5, 0.9, m, "white"); box(7.0, y, 2.8, 0.9, r, c)
        ax.annotate("", xy=(2.6, y + 0.45), xytext=(1.8, 3.0), arrowprops=dict(arrowstyle="-|>", color="#555", lw=0.7, shrinkA=0, shrinkB=1))
        ax.annotate("", xy=(7.0, y + 0.45), xytext=(6.1, y + 0.45), arrowprops=dict(arrowstyle="-|>", color="#555", lw=0.7))
    save(fig, "fig1_flow")


def fig_ladder():
    """Figure 2. The three spatial claims, for all of Seoul and without Gangnam, Seocho and Songpa."""
    from matplotlib.lines import Line2D
    gr = pd.read_csv(f"{RES}/gu_regression.csv"); gr = gr[gr.level == "gu"].set_index("sg")
    SET = {"20121219": "A", "20170509": "C"}; ALL, EX = "#104281", CAT[1]
    fig, axs = plt.subplots(1, 3, figsize=(7.4, 4.3), gridspec_kw=dict(width_ratios=[1, 1.35, 1.35], wspace=0.12), sharey=True)
    ys, yt = [], []
    for k, sg in enumerate(ELECTIONS):
        mid = (len(ELECTIONS) - 1 - k) * 1.0; ys.append(mid); col = SET.get(sg, "E")
        yt.append(LAB[sg] + ("" if col == "E" else f"\n(column {col})"))
        r = gr.loc[int(sg)]
        axs[0].plot([r.loo_min, r.loo_max], [mid + 0.12] * 2, color=ALL, lw=1.4); axs[0].plot([r.slope], [mid + 0.12], "o", color=ALL, ms=4.5)
        axs[0].plot([r.slope_excl3], [mid - 0.12], marker="D", ms=4, color=EX, ls="")
        d = pd.read_csv(f"{RES}/spatial_scope_{sg}.csv")
        for ax, sp, sc in [(axs[1], "slope", 1.0), (axs[2], "contrast", 100.0)]:
            for smp, off, c in [("all", 0.12, ALL), ("excl_gangnam3", -0.12, EX)]:
                q = d[(d["sample"] == smp) & (d.spec == sp) & (d.column == col)].iloc[0]
                # 2012 and 2017 lack mobility data: their ranges rest on different assumptions (columns A, C) and are drawn faint
                ax.plot([sc * q.z_lo, sc * q.z_hi], [mid + off] * 2, color=c, lw=3.4, solid_capstyle="butt", alpha=1.0 if col == "E" else 0.35)
        if k < len(ELECTIONS) - 1:
            for ax in axs: ax.axhline(mid - 0.5, color=GRID, lw=0.6)
    for ax in axs:
        ax.axvline(0, color=INK, lw=0.8); ax.grid(axis="x", color=GRID, lw=0.5); ax.set_axisbelow(True); ax.tick_params(axis="y", length=0)
    axs[0].set_yticks(ys); axs[0].set_yticklabels(yt, fontsize=7.6); axs[0].set_xlim(-0.02, 0.25)
    axs[0].set_title("A. Across districts", loc="left"); axs[1].set_title("B. Within-district slope", loc="left")
    axs[2].set_title("C. Within-district contrast", loc="left")
    axs[0].set_xlabel("Valid-vote share y\nslope on log price"); axs[1].set_xlabel("Roll-based share z\nslope on log price")
    axs[2].set_xlabel("Higher–lower price contrast\nin z (percentage points)")
    axs[1].set_xlim(-0.12, 0.26); axs[2].set_xlim(-6.5, 12.5)
    h = [Line2D([0], [0], marker="o", color=ALL, lw=1.4, ms=4.5, label="All Seoul: point and omission range (A)"),
         Line2D([0], [0], marker="D", color=EX, ls="", ms=4, label="Excluding the three districts: point (A)"),
         Line2D([0], [0], color=ALL, lw=3.4, label="All Seoul: bounds (B, C)"), Line2D([0], [0], color=EX, lw=3.4, label="Excluding the three districts: bounds (B, C)")]
    fig.legend(handles=h, loc="upper center", ncol=2, frameon=False, fontsize=7.0, bbox_to_anchor=(0.5, -0.04))
    save(fig, "fig2_scope")


def fig_region():
    """Figure 4. Where the within-gu sign holds: s*(lambda, delta) by election."""
    import matplotlib.colors as mcolors
    order = ["20220309", "20240410", "20250603", "20260603"]; movs = ["lambda=0.5", "lambda=1", "lambda=1.5", "lambda=2", "lambda=3", "unrestricted"]
    dels = [0.1, 0.15, 0.2, 0.3, 0.5, 1.0]
    fig, grid_axes = plt.subplots(2, 2, figsize=(7.4, 5.4), sharey=True)
    axs = grid_axes.ravel()
    fig.subplots_adjust(left=0.14, right=0.98, bottom=0.21, top=0.94, hspace=0.45, wspace=0.28)
    cmap = mcolors.ListedColormap(["#f1f0ec"] + RAMP[:4] + ["#104281"]); bounds = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
    norm = mcolors.BoundaryNorm(bounds, cmap.N)
    def cls(x):
        if np.isinf(x.s_lo): return 5, "∞"
        if x.s_lo <= x.s_min + 1e-12: return 0, ""
        v = x.s_lo
        return (1 if v < 0.02 else 2 if v < 0.05 else 3 if v < 0.1 else 4), ("<.005" if v < 0.005 else f"{v:.3f}"[1:] if v < 0.1 else f"{v:.2f}"[1:] if v < 0.3 - 1e-9 else "≥.3")
    for ax, sg in zip(axs, order):
        r = pd.read_csv(f"{RES}/region_{sg}.csv"); M = np.zeros((len(movs), len(dels)))
        for a, mv in enumerate(movs):
            for b, dl in enumerate(dels):
                x = r[(r.movement == mv) & (r.delta == dl)].iloc[0]; c, t = cls(x); M[a, b] = c
                ax.text(b, a, t, ha="center", va="center", fontsize=8.0, color="white" if c >= 4 else INK)
        ax.imshow(M, cmap=cmap, norm=norm, aspect="auto"); ax.set_title(LAB[sg], fontsize=8.5)
        if np.all(M == 0):
            ax.text(0.5, 0.5, "No positive lower bound\nin the settings shown",
                    transform=ax.transAxes, ha="center", va="center", fontsize=8, color=MUTED)
        from matplotlib.patches import Rectangle
        ax.add_patch(Rectangle((-0.5, 0.5), 1, 1, fill=False, ec=CAT[1], lw=1.6, zorder=5))   # main setting: lambda = 1, delta = 0.1
        ax.set_xticks(range(len(dels))); ax.set_xticklabels([f"{d:g}" for d in dels], fontsize=8); ax.set_xlabel("δ (out-of-zone tolerance)", fontsize=8)
        ax.set_yticks(range(len(movs))); ax.set_yticklabels(["λ = 0.5", "λ = 1", "λ = 1.5", "λ = 2", "λ = 3", "unrestricted"], fontsize=8)
        for sp_ in ax.spines.values(): sp_.set_visible(False)
        ax.tick_params(length=0)
    from matplotlib.patches import Patch
    h = [Patch(color="#f1f0ec", label="no positive lower bound"), Patch(color=RAMP[0], label="s* < 0.02 (below main s)"), Patch(color=RAMP[1], label="0.02–0.05"),
         Patch(color=RAMP[2], label="0.05–0.10"), Patch(color=RAMP[3], label="≥ 0.10"), Patch(color="#104281", label="positive for any s"),
         Patch(fill=False, ec=CAT[1], lw=1.6, label="main setting (λ = 1, δ = 0.1)")]
    fig.legend(handles=h, loc="lower center", ncol=3, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, 0.01))
    save(fig, "fig4_region")


def fig_map():
    import geopandas as gp
    r = pd.read_csv(f"{RES}/dong_ranges_2026.csv")
    m = gp.read_file(f"{RAW}/geo/seoul_dong_ver20260401.geojson"); m["key"] = m.emd.map(norm)
    m = m.merge(r, on=["gu", "key"], how="left")
    for k in ["accounting", "calib_d0.1"]: m[f"w_{k}"] = 100 * (m[f"hi_{k}"] - m[f"lo_{k}"])
    m["conv"] = 100 * m["conv"]
    mm = m.to_crs(5179); mm["geometry"] = mm.buffer(40); gu_b = mm.dissolve("gu"); gu_b["geometry"] = gu_b.buffer(-40); gu_b = gu_b.to_crs(m.crs)
    fig, axs = plt.subplots(1, 3, figsize=(7.4, 2.9))
    specs = [("conv", "(a) Published neighborhood share\nfor Oh Se-hoon (%)", "Blues", 30, 75),
             ("w_accounting", "(b) Residents' range width (pp)\nReturns and rolls only (A)", "Oranges", 0, 60),
             ("w_calib_d0.1", "(c) Residents' range width (pp)\nCalibrated movement; δ = 0.1 (D)", "Oranges", 0, 60)]
    for ax, (col, title, cmap, vmin, vmax) in zip(axs, specs):
        m.plot(column=col, ax=ax, cmap=cmap, vmin=vmin, vmax=vmax, linewidth=0.12, edgecolor="white", legend=True,
               legend_kwds=dict(shrink=0.55, orientation="horizontal", pad=0.02))
        gu_b.boundary.plot(ax=ax, color="#333", linewidth=0.4); ax.set_axis_off(); ax.set_title(title, fontsize=7.8, loc="left", fontweight="normal")
        if col == "conv":
            for g in ["강남구", "서초구", "송파구"]:
                c = gu_b.loc[g].geometry.representative_point()
                off = {"강남구": (2, -16), "서초구": (-16, -10), "송파구": (16, 2)}[g]   # points; keeps the three labels apart
                ax.annotate({"강남구": "Gangnam", "서초구": "Seocho", "송파구": "Songpa"}[g], (c.x, c.y), xytext=off, textcoords="offset points",
                            fontsize=5.5, ha="center", va="center", color=INK, arrowprops=dict(arrowstyle="-", color=INK, lw=0.4),
                            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    save(fig, "fig3_map")


if __name__ == "__main__":
    for f in [fig_flow, fig_ladder, fig_map, fig_region]:
        try: f(); print("ok", f.__name__)
        except Exception as e: print("FAILED", f.__name__, repr(e))
