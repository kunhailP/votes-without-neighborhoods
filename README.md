# Votes Without Neighborhoods

Replication materials for **"Votes Without Neighborhoods: Housing Prices and the Geography of Conservative Voting in Seoul."**

Seoul's expensive districts vote conservative, and maps of neighborhood returns suggest that the same divide runs through every district. The paper asks how far that electoral geography of housing generalizes: from districts (gu) to the neighborhoods (dong) within them, and from Gangnam, Seocho and Songpa to the rest of the city. Korean neighborhood returns count early ballots cast inside the voter's statutory early-voting zone (in-zone) where they were cast and report out-of-zone, at-home and overseas ballots only for the district or constituency, so a dong's published return is not its residents' vote. This repository computes, by linear programming, the range of each quantity over all allocations of ballots to residents consistent with the published returns, electoral rolls and statutory early-voting zones, and how each added assumption narrows it. The application covers six Seoul elections (2012–2026).

```
make test                # unit tests of the LP core (seconds)
make -j32 all            # every result, table, figure and the paper (about 1 hour on 32+ cores)
make paper-from-results  # tables, figures and paper from the shipped results/ only (minutes)
make review-package      # anonymized zip of the committed files for double-blind review
```

## What the paper finds

| Claim | Evidence | What the data support |
|---|---|---|
| Expensive districts vote more conservatively | district returns (fully counted) | Every election for all of Seoul, **no allocation assumption**; in 2012 and 2017 the slope falls by more than half without Gangnam, Seocho and Songpa (Table 3, Figure 2A) |
| Within districts, election-day voters in more expensive neighborhoods vote more conservatively | election-day ballots, counted in the voter's own voting district | Positive in 2012 and in every election from 2022, also without the three southeastern gu; close to zero in 2017; **no allocation assumption** (Table 2, Online Appendix C20) |
| ... and so do all residents, early voters included | ranges over every allocation consistent with the returns | Not established by the returns alone in any election with nationwide early voting. Under the main assumptions: positive in **2026** ([0.054, 0.156]; without the three gu [0.029, 0.139], holding for out-of-zone tolerances up to 0.18), narrowly positive and fragile in 2024, undetermined in 2022 and 2025 (Tables 2–3, Online Appendix C19, C25) |
| Which further assumption would settle the open signs | a bound on how far residents' early-vote departures align with price | For all of Seoul, bounds at the scale of observed station patterns would make the slope positive in every election from 2022; this is an additional, unverifiable restriction (Online Appendix C22) |
| Higher- vs lower-price groups within districts | median-split and tercile contrasts | Positive for all of Seoul in 2026; borderline without the three gu ([−0.3, 6.2] and [0.1, 7.9] points) (Table 3, Online Appendix C23) |
| How much the counting rule matters | the same 2026 returns with and without the statutory zones | Under weaker assumptions the zones decide whether the direction is established; under the main assumptions they narrow the range by about a quarter (Table 4) |
| How much better reporting would reveal | guaranteed reduction for every allocation | Under the main assumptions, 27–57% (out-of-zone early ballots by registered dong), 49–69% (all pooled modes); the direction is not guaranteed to be revealed (Table 6, Online Appendix C16) |

## Repository layout

```
vwn/                     core library: one constraint builder (lp.py) used by every solver path, data loading, bounds,
                         valid-vote programs (ytight.py), integer checks, baselines
analysis/                one script per result family, grouped by the claim it serves
  districts/             gradient across fully counted gu (Section 4.1)
  neighborhoods/         within-gu ranges as assumptions are added, the median-split contrast, single dongs (4.2)
  beyond_gangnam/        the analysis without Gangnam, Seocho and Songpa, and its sensitivity (4.3)
  counting_rules/        the 2026 statutory zones and council headcounts, coarser reporting (4.4)
  assumptions/           sign region, reversing allocations, alternative restriction families (4.5)
  reporting/             guaranteed value of reporting changes, direction revealed or not (5)
  robustness/            alternative specifications, resampling, outcomes, integer and solver checks, published allocation
  output/                tables (build_tables.py, appendix_tables.py, tablelib.py) and figures (make_figures.py)
build/                   data construction from data/raw (returns, prices, council table, mobility calibration)
data/                    analysis inputs (see data/README.md); data/raw = original public sources
results/                 every computed number (CSV); the paper's tables are generated from these files only
paper/                   manuscript.md, appendix.md, alt_text.md (figure descriptions),
                         generated tables/ and figures/,
                         build.py (pandoc + XeLaTeX; PDF with line numbers, DOCX with PNG figures), build/BUILD_INFO.txt
tests/                   unit tests (zone restriction shared by every solver path, stale-cache regression,
                         direction-revealing criterion, calibration alignment)
docs/                    replication map (where every number comes from) and supplementary results (Tables S1-S31)
```

Tables are named by their number in the paper: `paper/tables/table1`–`table6` (main text), `tableA1`–`tableD2` (Online Appendix). Supplementary tables are numbered S1–S31 in `docs/supplementary_results.md`.

## Reproducing

**Requirements.** Python ≥ 3.12 (the pinned SciPy requires it) with the packages in `requirements.txt` (HiGHS through SciPy). The paper needs pandoc ≥ 3.1 and XeLaTeX (TeX Live) with TeX Gyre Termes and Noto Serif CJK KR.

```
pip install -r requirements.txt
make test
make -j32 results     # results/*.csv
make paper            # paper/build/manuscript.pdf, appendix.pdf (+ .docx)
```

The `Makefile` tracks dependencies: each result file depends on its script, the core library `vwn/` and the inputs in `data/`; tables depend on every result file, figures on tables, and the paper on tables, figures and sources. `make -j32 all` therefore never tabulates before computing, and editing the core re-runs everything that uses it (and clears the dong-bound cache in `results/ydong/`). On a fresh clone file times are arbitrary, so `make all` may recompute everything; use `make paper-from-results` to rebuild only the paper from the shipped results. Each build writes `paper/build/BUILD_INFO.txt` with the source commit, tool versions and a hash of `results/`.

**Rebuilding the inputs (optional).** `make data` rebuilds the analysis files in `data/` from `data/raw/` and recomputes the mobility calibration; the rebuilt files are identical to those shipped. Re-downloading raw data requires API keys for data.go.kr and juso.go.kr in a local `.env` (see `.env.example`; never commit `.env`).

## Notes on design

* **One feasible set.** All restrictions, including the statutory early-voting zone (in 2026, `F_ij = 0` across gu council constituencies), are built in `JointLP.constraints()`, and every solver path uses its restriction-keyed constraint cache (`tests/test_core.py`).
* **Calibration by name.** Mobility-calibrated movement is matched to dongs by name (`vwn.data.align_calib`), never by row order.
* **Outcome.** The main outcome is the roll-based share z = N/H (linear in the allocation, exact ranges); valid-vote shares y are bracketed by an outer bound and attainable values.
* **Inference.** Ranges are identified sets conditional on the observed returns and price measure, not confidence intervals; the election-day slopes are exact descriptions of the observed neighborhoods. Permutation p-values, clustered standard errors and the resampling exercise are auxiliary diagnostics.

## Data sources

National Election Commission (returns, certified electorates, 2026 constituency table and council returns); Ministry of Land, Infrastructure and Transport (apartment transactions); road-name address service (lot-to-dong geocoding); Seoul Metropolitan Government and KT (Seoul Living Mobility, aggregated extracts); Ministry of the Interior and Safety (population by age); vuski/admdongkor (dong boundaries). Details and terms in `data/README.md`.

## License

Code: MIT (`LICENSE`). Data remain subject to their providers' terms.

---

### 한국어 요약

서울의 비싼 구가 보수적이라는 사실이 구 내부의 동네 사이에도, 그리고 강남·서초·송파 밖에서도 성립하는지를 묻는 논문의 재현 자료입니다. 동 단위 개표 결과는 관내사전투표를 투표소 소재 동으로, 관외사전·거소·재외투표를 구 합계로만 공표하기 때문에 동 득표율이 곧 주민의 득표율은 아닙니다. 이 저장소는 공표된 개표 결과·선거인명부·법정 관내구역과 모순되지 않는 모든 배분에 대해 각 값의 최솟값과 최댓값을 선형계획으로 계산하고, 가정을 하나씩 더할 때 결론이 어떻게 달라지는지 보여줍니다. `make -j32 all` 한 번으로 모든 결과·표·그림·원고를 다시 만듭니다.
