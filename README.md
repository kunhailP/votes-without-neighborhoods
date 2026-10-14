# Votes Without Neighborhoods

Replication materials for **"Votes Without Neighborhoods: Housing Prices and the Geography of Conservative Voting in Seoul."**

The paper asks how widely housing-related electoral alignment extends in Seoul: between neighborhoods within districts (gu), beyond Gangnam, Seocho and Songpa, and from election-day voters to residents using every voting mode. Korean neighborhood returns count in-zone early ballots where they were cast and pool out-of-zone, at-home and overseas ballots at the district or constituency level. A neighborhood's (dong's) published return therefore does not identify its residents' vote. Linear programs bound the associations over allocations consistent with returns, electoral rolls and statutory zones, then show what additional restrictions establish. The assembled dataset covers six elections (2012–2026); it is not an exhaustive or prespecified sample of Seoul elections.

```
make test                # mathematical and document-packaging regression tests
make verify              # re-solve 14 headline bounds; audit 246 saved integer allocations
make verify-additions    # recompute feasibility and independently rebuilt 2025-price checks
make paper-from-results  # rebuild tables, figures and paper from supplied results/ (minutes)
make -j32 all            # full analysis and paper; earlier benchmark about 1 hour on 32+ cores
```

The first four commands run in the `replication/` directory extracted from the
review ZIP and need no Git metadata or API credentials. `make verify` writes
`logs/review_verification.json` and leaves the supplied results unchanged. It
checks execution and arithmetic consistency; it does not validate the
substantive assumptions or authenticate the source records. Building the paper
from supplied results does not recompute the underlying analyses.

For authors preparing a locally revised paper before committing, run
`python3 paper/review_package.py ../vwn_review_package.zip --working-tree`.
For committed sources in a Git checkout, use `make review-package`.
The ZIP contains a SHA-256 manifest; its contents and CRCs are checked after
writing. The packager checks Word author metadata, comments and tracked changes,
and excludes private submission directories and intermediate Markdown files.
Recipients can check a received archive with
`python3 replication/paper/review_package.py vwn_review_package.zip --verify`
from the directory containing the extracted `replication/` folder and the ZIP.
Keep the title page, cover letter and author declarations outside the replication
tree (or under an excluded `paper/submission/` directory).

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

Table 6 assumes exact aggregate disclosure. For a specific primary-suppression
rule that marks out-of-zone neighborhood-by-candidate counts below 20 and
releases larger counts exactly, conservative remaining-width bounds imply
reductions of 24–49% relative to the current continuous range (Appendix C26).
This exercise does not cover complementary suppression or certify privacy.
Appendix A2 supplies 246 saved integer allocations under the main assumptions;
a separate arithmetic checker verifies their accounting, zones, movement and
composition. Attained endpoints lie within 0.0008 of the continuous bounds
for both geographic scopes. These are witnesses, not proven integer optima.

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
  robustness/            alternative specifications, resampling, outcomes, integer and solver checks, published allocation;
                         review_check.py supplies the fast, non-mutating headline verification
  output/                tables (build_tables.py, appendix_tables.py, tablelib.py) and figures (make_figures.py)
build/                   data construction from data/raw (returns, prices, council table, mobility calibration)
data/                    analysis inputs (see data/README.md); data/raw = original public sources
results/                 every computed number (CSV); the paper's tables are generated from these files only
paper/                   manuscript.md, appendix.md, alt_text.md (figure descriptions),
                         generated tables/ and figures/,
                         build.py (pandoc + XeLaTeX; PDF with line numbers, DOCX with PNG figures),
                         word_layout.py (Word table panels, repeat headers and landscape pages), build/BUILD_INFO.txt
tests/                   zone restriction across solver paths, stale-cache regression,
                         direction-revealing criterion, calibration alignment, suppression and document checks
docs/                    replication map (where every number comes from) and supplementary results (Tables S1-S31)
```

Tables are named by their number in the paper: `paper/tables/table1`–`table6` (main text), `tableA1`–`tableD2` (Online Appendix). Supplementary tables are numbered S1–S31 in `docs/supplementary_results.md`.

## Reproducing

**Requirements.** Python ≥ 3.12 (the pinned SciPy requires it) with the packages in `requirements.txt` (HiGHS through SciPy). The paper needs pandoc ≥ 3.1 and XeLaTeX (TeX Live) with TeX Gyre Termes and Noto Serif CJK KR.

```
pip install -r requirements.txt
make test
make verify          # smaller execution check before the full replication
make -j32 results     # results/*.csv
make paper            # paper/build/manuscript.pdf, appendix.pdf (+ .docx)
```

The `Makefile` tracks dependencies: each result file depends on its script, the core library `vwn/` and the inputs in `data/`; tables depend on every result file, figures on tables, and the paper on tables, figures and sources. `make -j32 all` therefore never tabulates before computing, and editing the core re-runs everything that uses it (and clears the dong-bound cache in `results/ydong/`). On a fresh clone file times are arbitrary, so `make all` may recompute everything; use `make paper-from-results` to rebuild only the paper from the shipped results. Each build writes `paper/build/BUILD_INFO.txt` with the source commit, tool versions and a hash of `results/`.

**Rebuilding the inputs (optional).** `make data` rebuilds the election returns, available trade-level inputs, council files and mobility calibration from saved sources. It preserves the certified-electorate and price-summary snapshots used in the analysis. `python build/build_trades.py --summaries <sg>` additionally rebuilds available price summaries; run this in a copy if retaining the supplied inputs. `python analysis/robustness/price_lineage.py` does that audit in isolation: 2022, 2024 and 2026 medians agree, while three 2012/2017 medians differ by up to 0.65%, with checked slope endpoints changing by less than 0.00004 and no sign conclusions changing. The original 2025 download and generating code remain unavailable. The package now includes a separately dated MOLIT snapshot (73,319 records), an extended address crosswalk and `analysis/robustness/price_2025_audit.py`, which reconstructs an alternative price measure and checks A/C/D/E slopes in both geographic scopes plus the main setting on common support. Its source and mapping differences must not be mistaken for recovery of the original summary. `make verify-additions` runs this audit and the jurisdiction-specific feasibility-band analysis offline. Re-downloading source data requires API keys for data.go.kr and juso.go.kr in a local `.env` (see `.env.example`; never commit `.env`).

**Verification scope.** The review preparation checked the 14 headline bound
configurations and all 246 saved integer allocations, reconstructed the five
available price summaries, and rebuilt the documents from the supplied results
in a separate extracted copy. It did not rerun every pre-existing analysis
family. The machine-readable headline check is supplied in
`docs/review_verification.json`; its scope is narrower than `make all`.
The 2020 legislative and 2022 local election inputs are absent from this package.
This is a coverage limitation, not a claim that their public sources cannot be
obtained. In particular, the official portal lists 2022 local-election returns;
the additional compatible inputs have not been assembled or verified
(`docs/coverage_audit.json`). The manuscript makes election-specific claims rather than estimating
a complete time trend or a typical effect of an election type.

## Notes on design

* **One feasible set.** All restrictions, including the statutory early-voting zone (in 2026, `F_ij = 0` across gu council constituencies), are built in `JointLP.constraints()`, and every solver path uses its restriction-keyed constraint cache (`tests/test_core.py`).
* **Calibration by name.** Mobility-calibrated movement is matched to dongs by name (`vwn.data.align_calib`), never by row order.
* **Outcome.** The main outcome is the roll-based share z = N/H (linear in the allocation, exact ranges); valid-vote shares y are bracketed by an outer bound and attainable values.
* **Inference.** Ranges are identified sets for the continuous relaxation conditional on observed returns and prices, and conservative outer bounds for integer ballots, not confidence intervals. The election-day slopes are exact descriptions of the observed neighborhoods. Permutation p-values, clustered standard errors and the resampling exercise are auxiliary diagnostics.

## Data sources

National Election Commission (returns, certified electorates, 2026 constituency table and council returns); Ministry of Land, Infrastructure and Transport (apartment transactions); road-name address service (lot-to-dong geocoding); Seoul Metropolitan Government and KT (Seoul Living Mobility, aggregated extracts); Ministry of the Interior and Safety (population by age); vuski/admdongkor (dong boundaries). Details and terms in `data/README.md`.

## License

Code: MIT (`LICENSE`). Data remain subject to their providers' terms.

---

### 한국어 요약

구 내부와 강남·서초·송파 밖에서 관측되는 주택가격–보수 투표의 관계를 본투표자에서 사전투표자를 포함한 주민으로 확장할 수 있는지 묻는 논문의 재현 자료입니다. 동 단위 개표는 투표소 위치와 주민의 거주지가 다르거나 일부 투표가 구·선거구 합계로만 공표되는 문제를 갖습니다. 공개된 개표·명부·법정 구역과 일치하는 배분의 범위를 계산하고, 추가 가정에 따라 결론이 어떻게 달라지는지 보여줍니다. `make verify`는 핵심 경계 14개와 저장된 정수 배분 246개를 점검하고, `make paper-from-results`는 공급된 결과로 문서를 만듭니다. 전체 재계산은 `make -j32 all`입니다. 여섯 선거는 모든 선거를 망라한 시계열이 아니며, 2025년 과거 가격 요약의 최초 생성 과정은 미확인이나, 새로 수집한 실거래와 확장한 주소 매핑을 이용한 대체 재구성 및 민감도 검증을 포함합니다. `make verify-additions`로 추가 검증을 재실행할 수 있습니다.

The versions used for the 14 October 2026 verification are recorded in `docs/environment_verified.json`; the NumPy pin in `requirements.txt` matches that verified environment.

The joint geographic and price-tail sensitivity in Online Appendix C29 is reproduced by `python3 analysis/robustness/scope_price_tail.py` (with the repository on `PYTHONPATH`) or `make verify-additions`.
