# Data

## Analysis inputs (`data/`)

| File | Content | Built by |
|---|---|---|
| `seoul_<sg>_emd.csv`, `seoul_2025pres_emd.csv` | Returns by dong and mode for Seoul: `unit` = DAY (election day, summed over voting districts), IN (in-zone early station), X (gu or constituency rows: out-of-zone early, at-home/shipboard, overseas). Candidate slots: LJM = Democratic, KMS = main conservative, LJS/KYG = third/fourth, SJH = others, plus invalid and abstain | `build/build_emd.py`, `build_2024.py`, `build_2026.py` |
| `seoul_<sg>_electorate_api.csv`, `seoul_20240410_electorate_bysgg.csv` | Certified electorate by dong (NEC electorate service); 2024 split by constituency | `build/fetch_electorate.py`, `build_2024.py` |
| `seoul_hdong_aptprice_<sg>.csv`, `seoul_hdong_aptprice_202406_202505.csv` | Frozen dong apartment-price summaries (median, mean, transactions), twelve complete calendar months ending before the election month | Available years: `build/build_trades.py --summaries`; see the construction audit below. Original 2025 construction is unavailable; an independently rebuilt alternative is supplied (see below). |
| `trades/trades_hdong_<sg>.csv` | Transaction-level prices with dong (for resampling) | `build/build_trades.py` |
| `council_20260603.csv` | 2026 gu council constituency of every dong (NEC "선거구 및 읍면동현황") | `build/fetch_council_2026.py` |
| `council_stations_20260603.csv` | In-zone early voters per station in the 2026 council contest (used to verify the zone) | `build/fetch_council_2026.py` |
| `council_pooled_20260603.csv` | Out-of-zone early and at-home voters by contested council constituency (2026 council returns) | `build/fetch_council_2026.py` |
| `kt_code_crosswalk_<sg>.csv` | Seoul Living Mobility dong codes ↔ administrative dongs; where the mobility data use an older dong code (Gaepo 3, Gayang 1, Banghwa 3, Gangil, Sangil 1–2, Oryu 2 and Hang, Sinseol and Yongdu), the code in the mobility files, which may cover two dongs | derived from vuski/admdongkor codes, checked against the mobility files |
| `adjacency_<sg>.csv` | Pairs of dongs sharing a boundary | `build/build_adjacency.py` (needs a local clone of vuski/admdongkor) |
| `seoul_hdong_age_202604.csv` | Share aged 60+ and mean age (18+) by dong, April 2026 | from `raw/mois` |
| `derived/eta_calib_<sg>.csv` | Calibrated cross-dong flows by station (zones as in the paper); `_nozones` = movement anywhere in the gu | `build/mobility_calibration.py` |

`<sg>` is the election date: 20121219, 20170509, 20220309 (presidential), 20240410 (legislative), 20250603 (presidential), 20260603 (mayor of Seoul).

These are the compiled cases, not an exhaustive or prespecified sample of Seoul
elections. Other legislative and local elections, including 2020 and 2022,
are absent. The official portal lists the 2022 local-election counting results
at https://www.data.go.kr/data/15101509/fileData.do, so their absence here must
not be attributed to nonexistence of public returns. Compatible rolls, zone
maps, prices and mobility inputs for that comparison have not been assembled
or verified here (see `docs/coverage_audit.json`). There are no historical age-composition files:
the age sensitivity check uses April 2026 composition in every election.

## Construction audit

`analysis/robustness/price_lineage.py` rebuilds available summaries in a temporary
copy from assembled trades and the saved address crosswalk. It leaves the
analysis snapshots unchanged and writes `results/price_lineage.csv`.
2022, 2024 and 2026 medians match; one 2012 median and two 2017 medians differ
by at most 0.65%. The checked accounting-only and minimal-movement/10-point
slope endpoints move by less than 0.00004 in both geographic scopes, without
changing their signs. The archived 2025 summary remains a historical input whose original download and generating code are unavailable. A new MOLIT retrieval on 14 October 2026 covers all 300 district-months in June 2024–May 2025 (73,319 records). `raw/molit/refetch_2025/` stores original XML and a request/hash manifest, and `raw/molit/seoul_apt_trades_20250603.csv` assembles them. `raw/juso/seoul_jibun_to_hdong_juso_2025_audit.csv` extends the crosswalk only for this audit; individual source responses are in `raw/juso/refetch_2025_addresses/`. `analysis/robustness/price_2025_audit.py` reconstructs prices offline and writes comparisons and slope checks to `results/price_2025_*.csv` and `docs/price_2025_audit.json`. The original inputs are not overwritten. Appendix B.3 reports material price and coverage differences; an alternative reconstruction is not recovery of the original source snapshot. To refresh the public sources, `build/fetch_2025_prices.py` and `build/fetch_2025_addresses.py` accept API credentials through the environment or a private `--env-file`; never include credentials in a replication archive.

## Raw sources (`data/raw/`)

| Folder | Source | Notes |
|---|---|---|
| `nec/` | National Election Commission: counting-unit returns (national CSV files), electorate service extracts, 2026 counting-unit spreadsheets for the mayoral election (`2026_mayor_xlsx/`, one per gu), and the 2026 council HTML responses (`council_2026/`) | Public; https://info.nec.go.kr, https://www.data.go.kr |
| `molit/` | Ministry of Land, Infrastructure and Transport apartment transaction API: monthly files by gu (`apt_raw/`) and assembled election windows | Public; https://rt.molit.go.kr |
| `juso/` | Road-name address service lookups (lot number → administrative dong), with cache | https://business.juso.go.kr |
| `mobility/` | Seoul Living Mobility, home-origin trips on the two weekdays of early voting (Friday and Saturday; Thursday and Friday in 2025), 06:00–17:59 arrivals, aggregated to origin × destination × weekday (`od_home_<yyyymm>.csv`) | Extracted from the monthly files of Seoul Open Data Plaza by `build/mobility_extract.py`; the original multi-gigabyte files are not redistributed |
| `mois/` | Resident registration population by age, April 2026 | https://jumin.mois.go.kr |
| `geo/` | Administrative-dong boundaries, version 20260401 | vuski/admdongkor |

All sources are public administrative data. Use of the data is subject to the providers' terms; the Korean public data portals generally permit reuse with attribution (KOGL).
