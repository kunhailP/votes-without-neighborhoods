# Replication map

Every table is generated from `results/` by `analysis/output/build_tables.py` (main text) and `analysis/output/appendix_tables.py` (Online Appendix and supplementary results); figures by `analysis/output/make_figures.py`. Output files are named by their number in the paper (`paper/tables/table3.tex`, `tableC17.tex`). `make -j32 all` runs everything in dependency order (see the header of the `Makefile`).

## Main text

| Output | Script(s) | Result files |
|---|---|---|
| Section 1, early-vote gap by election | `neighborhoods/gap.py` | `gap_test_gu.csv`, `gap_test_reg.csv` (Table C8) |
| Section 2, price dispersion within districts | computed from `data/seoul_hdong_aptprice_20260603.csv` and `data/adjacency_20260603.csv` | – |
| Section 3.1, zone check (320/320 stations) | `build/fetch_council_2026.py`, `counting_rules/headcounts.py` | `data/council_stations_20260603.csv`, `zones_2026.csv` |
| Table 1 (data) | `output/build_tables.py` (from `data/`) | – |
| Section 4.1, Figure 2A, Table 3 (across districts) | `districts/gu_level.py` | `gu_regression.csv` |
| Table 2 (within districts, columns A–F) | `neighborhoods/main_grid.py` (A–C), `calibrated.py` (D), `composition.py` (E), `gap.py` (F), `contrast.py` (panel B) | `main_grid_<sg>.csv`, `calibrated_bounds_<sg>.csv`, `composition_<sg>.csv`, `gap_adjusted.csv`, `contrast_<sg>.csv` |
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
| D1, D2 | Published 2026 allocation | `robustness/published_allocation.py` | `published_*.csv` |

## Supplementary results

`docs/supplementary_results.md` collects Tables S1–S31, generated by `analysis/output/appendix_tables.py` from the result files listed above (for example the alternative outcomes, including Hong + Yoo in 2017, come from `robustness/outcomes.py` → `outcomes.csv`).
