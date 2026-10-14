# Replication map

Every table is generated from `results/` by `analysis/output/build_tables.py` (main text) and `analysis/output/appendix_tables.py` (Online Appendix and supplementary results); figures by `analysis/output/make_figures.py`. Output files are named by their number in the paper (`paper/tables/table3.tex`, `tableC17.tex`). `make -j32 all` runs everything in dependency order (see the header of the `Makefile`).

For a quick numerical check, `make verify` re-solves accounting-only slopes for
all six elections and the main-assumption slopes for 2022–2026 in both geographic
scopes (14 configurations), then checks 246 saved integer allocations directly
from the accounting identities. It reads supplied inputs and results, writes
only `logs/review_verification.json`, and does not rebuild raw data or run every
analysis family. `docs/review_verification.json` records the preparation run.
`make paper-from-results` is a separate document rebuild and does not establish
that the analysis results have been recomputed.

## Main text

| Output | Script(s) | Result files |
|---|---|---|
| Section 1, early-vote gap by election | `neighborhoods/gap.py` | `gap_test_gu.csv`, `gap_test_reg.csv` (Table C8) |
| Section 2, price dispersion within districts | computed from `data/seoul_hdong_aptprice_20260603.csv` and `data/adjacency_20260603.csv` | – |
| Section 3.1, zone check (320/320 stations) | `build/fetch_council_2026.py`, `counting_rules/headcounts.py` | `data/council_stations_20260603.csv`, `zones_2026.csv` |
| Table 1 (data) | `output/build_tables.py` (from `data/`) | – |
| Section 4.1, Figure 2A, Table 3 (across districts) | `districts/gu_level.py` | `gu_regression.csv` |
| Table 2 (within-district gradients, columns A–F) | `neighborhoods/main_grid.py` (A–C), `calibrated.py` (D), `composition.py` (E), `gap.py` (F) | `main_grid_<sg>.csv`, `calibrated_bounds_<sg>.csv`, `composition_<sg>.csv`, `gap_adjusted.csv` |
| Section 4.2, Table 2 second column, Online Appendix C20 (election-day voters, point-identified) | `neighborhoods/election_day.py` | `election_day.csv` |
| Figure 3 (2026 map), single neighborhoods and adjacent pairs | `neighborhoods/dong_contrasts.py` | `dong_ranges_2026.csv`, `adj_pairs_2026.csv` |
| Section 4.3, Table 3, Figure 2B–C (beyond Gangnam) | `beyond_gangnam/spatial_scope.py`, `beyond_gangnam/scope_sensitivity.py` | `spatial_scope_<sg>.csv`, `scope_sstar_<sg>.csv` |
| Section 4.4, Table 4 (2026 zones) | `neighborhoods/main_grid.py --no-zones`, `counting_rules/headcounts.py` | `main_grid_20260603_nozones.csv`, `zones_2026.csv` |
| Section 4.5, Figure 4 (region of assumptions) | `assumptions/region.py` | `region_<sg>.csv` |
| Table 5 (what a reversal requires) | `assumptions/region.py` (s, first reversal), `assumptions/extremal.py` (least departure) | `region_<sg>.csv`, `edge_profile_<sg>.csv`, `least_departure.csv`, `least_departure_detail.csv` |
| Section 4.5, movers' composition | `assumptions/revisions.py mover` | `rev_mover_<sg>.csv` |
| Section 4.5 robustness | `robustness/robust_restricted.py`, `robustness/resampling.py`, `neighborhoods/gap.py`, `assumptions/revisions.py anchor`, `neighborhoods/valid_vote.py`, `counting_rules/headcounts.py` | `robust_restricted_<sg>.csv`, `resampling_<sg>_*.csv`, `gap_*.csv`, `rev_anchor_<sg>.csv`, `valid_vote_<sg>.csv`, `zones_2026.csv` |
| Table 6 (reporting changes) | `reporting/disclosure_guarantee.py` | `disclosure_guarantee_<sg>.csv` |
| Section 5, direction not revealed (2022: −0.026 / +0.026) | `reporting/sign_guarantee.py` | `sign_guarantee_<sg>.csv` |
| Section 4.2 and Online Appendix D, published allocation | `robustness/published_allocation.py` | `published_*.csv` |

## Online Appendix

| Table | Content | Script | Result files |
|---|---|---|---|
| A1 | Integer check of near-zero lower bounds | `robustness/integer_check.py` | `integer_check.csv` |
| A2 | Integer witnesses under the main assumptions, both geographic scopes | `robustness/integer_witness.py`, `robustness/verify_integer_witness.py` | `integer_witness_<sg>.csv`, `integer_allocations/<sg>/*.npz`, `integer_witness_summary.csv` |
| B1 | 2026 zones (council constituencies) | `build/fetch_council_2026.py` | `data/council_*.csv` |
| B2 | Counting rules elsewhere | `output/appendix_tables.py` (text table) | – |
| C1 | Uniform movement, breakdown points | `neighborhoods/main_grid.py` | `main_grid_<sg>.csv` |
| C2 | 2026 zones and cross-contest headcounts | `neighborhoods/main_grid.py --no-zones`, `counting_rules/headcounts.py` | `main_grid_20260603_nozones.csv`, `zones_2026.csv` |
| C3 | Calibrated movement | `neighborhoods/calibrated.py` | `calibrated_bounds_<sg>.csv`, `calibrated_lamstar_<sg>.csv` |
| C4 | Region of assumptions s*(λ, δ) | `assumptions/region.py` | `region_<sg>.csv` |
| C5 | First reversing allocation | `assumptions/region.py` | `edge_profile_<sg>.csv` |
| C6 | Least-departure reversal | `assumptions/extremal.py` | `least_departure.csv`, `least_departure_detail.csv` |
| C7 | Movers' composition | `assumptions/revisions.py mover` | `rev_mover_<sg>.csv` |
| C8 | Early-vote gap, price and age | `neighborhoods/gap.py` | `gap_test_gu.csv`, `gap_test_reg.csv` |
| C9 | Out-of-district benchmark | `assumptions/revisions.py anchor` | `rev_anchor_<sg>.csv` |
| C10 | Robustness of the lower bound | `robustness/robust_restricted.py` | `robust_restricted_<sg>.csv` |
| C11 | High- minus low-price contrast | `neighborhoods/contrast.py` | `contrast_<sg>.csv` |
| C12 | Guaranteed reporting gains | `reporting/disclosure_guarantee.py` | `disclosure_guarantee_<sg>.csv` |
| C13 | Resampling stability | `robustness/resampling.py` | `resampling_<sg>_*.csv` |
| C14 | Regressions across districts | `districts/gu_level.py` | `gu_regression.csv` |
| C15 | Valid-vote shares | `neighborhoods/valid_vote.py` | `valid_vote_<sg>.csv` |
| C16 | Whether a report reveals the direction | `reporting/sign_guarantee.py` | `sign_guarantee_<sg>.csv` |
| C17 | Beyond Gangnam, every column of Table 2 | `beyond_gangnam/spatial_scope.py` | `spatial_scope_<sg>.csv` |
| C18 | Beyond Gangnam, valid-vote shares | `beyond_gangnam/spatial_scope.py` | `spatial_scope_<sg>.csv` |
| C19 | Beyond Gangnam, how far the assumptions can be relaxed (s*) | `beyond_gangnam/scope_sensitivity.py` | `scope_sstar_<sg>.csv` |
| C20 | Point-identified benchmarks: election-day voters and in-zone stations | `neighborhoods/election_day.py` | `election_day.csv` |
| C21 | Out-of-zone minus in-zone early composition by jurisdiction (reference for δ) | `assumptions/oz_gap.py` | `oz_gap.csv` |
| C22 | Price-aligned departures: breakdown points κ* and observed station gradients | `assumptions/directional.py` | `directional.csv`, `directional_reference.csv` |
| C23 | Age composition held fixed; tercile contrast | `robustness/age_tercile.py` | `age_tercile.csv` |
| C24 | Alternative outcomes (2017 Hong+Yoo and others) | `robustness/outcomes.py` | `outcomes.csv` |
| C25 | δ*, movers with composition, out-of-zone alignment, U | `assumptions/further_restrictions.py` | `further_restrictions_bounds.csv`, `further_restrictions_reference.csv` |
| C26 | Conservative reporting gains with primary suppression | `reporting/suppression.py`, `reporting/disclosure_guarantee.py` | `suppression_<sg>.csv` |
| C27 | Distance from the feasibility boundary under the main movement/composition restrictions | `robustness/assumption_feasibility.py` | `feasibility_units_<sg>.csv`, `feasibility_bounds_<sg>.csv` |
| C28 | Archived versus independently rebuilt 2025 prices, including common support | `robustness/price_2025_audit.py` | `price_2025_bounds.csv`, `price_2025_common_support.csv`, `price_2025_comparison.csv` |
| D1, D2 | Published 2026 allocation | `robustness/published_allocation.py` | `published_*.csv` |

## Supplementary results

Price construction audit (Appendix B.3): `robustness/price_lineage.py` →
`results/price_lineage.csv`. Rebuilds available summaries in an isolated copy
and checks earlier-price differences against the supplied slope results.
The original 2025 construction remains unavailable; the newly retrieved snapshot and alternative reconstruction are documented in `data/README.md` and `docs/price_2025_audit.json`.

`docs/supplementary_results.md` collects Tables S1–S31, generated by `analysis/output/appendix_tables.py` from the result files listed above (for example the alternative outcomes, including Hong + Yoo in 2017, come from `robustness/outcomes.py` → `outcomes.csv`).

Table C29: `analysis/robustness/scope_price_tail.py` generates `results/scope_price_tail_20260603.csv` and `results/scope_leave_one_out_20260603.csv`. It combines exclusion of the three southeastern districts with price-tail trimming and verifies the most influential single-district omission by direct re-solving.
