# Votes Without Neighborhoods: replication
#   make test      unit tests of the LP core (seconds)
#   make results   every computation in results/ (about 1 hour on 32+ cores; jobs run in parallel with -j)
#   make tables    paper/tables from results/
#   make figures   paper/figures from results/
#   make paper     manuscript and online appendix (PDF, DOCX)
#   make all       results, tables, figures, paper
#   make data      rebuild analysis files from data/raw (optional; outputs are already in data/)
#
# Dependencies: every result file depends on its script, on the core library (vwn/*.py) and on the analysis inputs in data/,
# so editing any of them re-runs exactly the affected computations. Tables depend on every result file and on the table
# scripts; figures on the tables; the paper on tables, figures and the manuscript sources. A change to vwn/*.py also clears
# the dong-bound cache in results/ydong. `make -j32 all` is therefore safe: nothing is tabulated before it is computed.

PY      := python3
# A solver may write intermediate rows before failing. Never retain its partial
# target as if a later invocation had already completed that computation.
.DELETE_ON_ERROR:
# analysis/ is organized by claim (districts, neighborhoods, beyond_gangnam, counting_rules, assumptions, reporting,
# robustness, output); every subfolder is on the path so scripts can import each other
ADIRS   := $(patsubst %/,%,$(sort $(dir $(wildcard analysis/*/*.py))))
empty   :=
space   := $(empty) $(empty)
export PYTHONPATH := $(CURDIR):$(subst $(space),:,$(addprefix $(CURDIR)/,$(ADIRS)))$(if $(PYTHONPATH),:$(PYTHONPATH))
S        = $(firstword $(wildcard analysis/*/$(1).py))
# one BLAS thread per job: parallelism comes from -j (otherwise -j jobs x all-core BLAS pools exhaust the process table)
export OMP_NUM_THREADS := 1
export OPENBLAS_NUM_THREADS := 1
export MKL_NUM_THREADS := 1
SG      := 20121219 20170509 20220309 20240410 20250603 20260603
SGCAL   := 20220309 20240410 20250603 20260603
SG5     := 20170509 $(SGCAL)
R       := results
LOG     := logs
$(shell mkdir -p $(R) $(LOG))

.PHONY: all test verify results tables figures paper data clean review-package

all: paper

test:
	$(PY) -m pytest -q tests

# Re-solve headline bounds and audit saved integer allocations without replacing results/.
verify:
	$(PY) $(call S,review_check) --output $(LOG)/review_verification.json

# New source-snapshot and feasibility checks; no network or credentials needed.
.PHONY: verify-additions
verify-additions:
	set -e; for sg in $(SGCAL); do $(PY) $(call S,assumption_feasibility) $$sg; done
	$(PY) $(call S,price_2025_audit)
	$(PY) $(call S,scope_price_tail)

# ---------------------------------------------------------------- data (optional)
data:
	for sg in 20121219 20170509 20220309 20250603; do $(PY) build/build_emd.py $$sg || exit; done
	$(PY) build/build_2024.py
	cd build && $(PY) build_2026.py
	$(PY) build/build_trades.py 20121219 20170509 20220309 20240410 20260603
	$(PY) build/fetch_council_2026.py --offline
	$(PY) build/mobility_calibration.py $(SGCAL)
	$(PY) build/mobility_calibration.py --no-zones $(SGCAL)

data/derived/eta_calib_%.csv:
	$(PY) build/mobility_calibration.py $*

CALIB := $(foreach s,$(SGCAL),data/derived/eta_calib_$(s).csv)

# ---------------------------------------------------------------- results
CORE    := $(wildcard vwn/*.py)
INPUTS  := $(wildcard data/*.csv data/*.json data/trades/*.csv data/derived/*.csv data/raw/mobility/od_home_*.csv) $(CALIB)
YCACHE  := $(R)/ydong/.core
DEP     := $(CORE) $(INPUTS) | $(YCACHE)   # keep last in every prerequisite list (order-only cache reset)

# the dong-bound cache is keyed by restrictions, not by code: invalidate it whenever the core library changes
$(YCACHE): $(CORE)
	rm -rf $(R)/ydong && mkdir -p $(R)/ydong && touch $@

MAIN    := $(foreach s,$(SG),$(R)/main_grid_$(s).csv) $(R)/main_grid_20260603_nozones.csv
VALID   := $(foreach s,$(SG),$(R)/valid_vote_$(s).csv)
RESOL   := $(foreach s,$(SG),$(R)/resolution_$(s).csv)
CALIBR  := $(foreach s,$(SGCAL),$(R)/calibrated_bounds_$(s).csv)
COMP    := $(foreach s,$(SG5),$(R)/composition_$(s).csv)
FRONT   := $(foreach s,$(SG5),$(R)/joint_frontier_$(s).csv)
DISC    := $(foreach s,$(SG5),$(R)/disclosure_$(s).csv)
ROBUST  := $(foreach s,$(SGCAL),$(R)/robust_restricted_$(s).csv)
ANCH    := $(foreach s,$(SG5),$(R)/anchor_day_$(s).csv)
RESAMP  := $(foreach s,20220309 20240410 20260603,$(R)/resampling_$(s)_full.csv $(R)/resampling_$(s)_txn.csv)
NEW     := $(foreach s,$(SG5),$(R)/rev_anchor_$(s).csv $(R)/rev_mover_$(s).csv) $(foreach s,$(SGCAL),$(R)/rev_intercept_$(s).csv $(R)/sign_guarantee_$(s).csv $(R)/suppression_$(s).csv $(R)/integer_witness_$(s).csv) $(foreach s,$(SG5),$(R)/disclosure_guarantee_$(s).csv) $(foreach s,$(SG),$(R)/contrast_$(s).csv) $(foreach s,$(SGCAL),$(R)/region_$(s).csv)
SCOPE   := $(foreach s,$(SG),$(R)/spatial_scope_$(s).csv) $(foreach s,$(SGCAL),$(R)/scope_sstar_$(s).csv)
SINGLE  := $(R)/gu_regression.csv $(R)/width_bound.csv $(R)/adj_pairs_2026.csv $(R)/calibrated_dow.csv $(R)/gap_adjusted.csv \
           $(R)/headcount_bands.csv $(R)/decomposition.csv $(R)/published_scale.csv $(R)/integer_check.csv $(R)/solver_check.csv \
           $(R)/spec_sparse.csv $(R)/adjacency_bounds.csv $(R)/outcomes.csv $(R)/least_departure.csv $(R)/election_day.csv $(R)/oz_gap.csv $(R)/directional.csv $(R)/age_tercile.csv $(R)/further_restrictions_bounds.csv $(R)/integer_witness_summary.csv $(R)/price_lineage.csv

results: $(SCOPE) $(NEW) $(MAIN) $(VALID) $(RESOL) $(CALIBR) $(COMP) $(FRONT) $(DISC) $(ROBUST) $(ANCH) $(RESAMP) $(SINGLE)

AUDITRES := $(foreach s,$(SGCAL),$(R)/feasibility_bounds_$(s).csv $(R)/feasibility_units_$(s).csv) $(R)/price_2025_bounds.csv $(R)/price_2025_comparison.csv $(R)/price_2025_rebuilt.csv $(R)/price_2025_common_support.csv
AUDITRES += $(R)/scope_price_tail_20260603.csv $(R)/scope_leave_one_out_20260603.csv
results: $(AUDITRES)

$(R)/scope_price_tail_20260603.csv $(R)/scope_leave_one_out_20260603.csv &: $(call S,scope_price_tail) $(DEP)
	$(PY) $(call S,scope_price_tail) > $(LOG)/scope_price_tail.log 2>&1

$(R)/feasibility_bounds_%.csv $(R)/feasibility_units_%.csv &: $(call S,assumption_feasibility) $(DEP)
	$(PY) $(call S,assumption_feasibility) $* > $(LOG)/feasibility_$*.log 2>&1

$(R)/price_2025_bounds.csv $(R)/price_2025_comparison.csv $(R)/price_2025_rebuilt.csv $(R)/price_2025_common_support.csv &: $(call S,price_2025_audit) build/build_trades.py data/raw/molit/seoul_apt_trades_20250603.csv data/raw/juso/seoul_jibun_to_hdong_juso_2025_audit.csv $(R)/spatial_scope_20250603.csv $(DEP)
	$(PY) $(call S,price_2025_audit) > $(LOG)/price_2025_audit.log 2>&1

$(R)/main_grid_20260603_nozones.csv: $(call S,main_grid) $(DEP)
	$(PY) $(call S,main_grid) --no-zones 20260603 > $(LOG)/main_grid_nozones.log 2>&1
$(R)/main_grid_%.csv: $(call S,main_grid) $(DEP)
	$(PY) $(call S,main_grid) $* > $(LOG)/main_grid_$*.log 2>&1
$(R)/valid_vote_%.csv: $(call S,valid_vote) $(DEP)
	$(PY) $(call S,valid_vote) $* > $(LOG)/valid_$*.log 2>&1
$(R)/resolution_%.csv: $(call S,resolution) $(DEP)
	$(PY) $(call S,resolution) $* > $(LOG)/resolution_$*.log 2>&1
$(R)/calibrated_bounds_%.csv: $(call S,calibrated) $(DEP)
	$(PY) $(call S,calibrated) $* > $(LOG)/calibrated_$*.log 2>&1
$(R)/composition_%.csv: $(call S,composition) $(DEP)
	$(PY) $(call S,composition) $* > $(LOG)/composition_$*.log 2>&1
$(R)/joint_frontier_%.csv: $(call S,joint_frontier) $(DEP)
	$(PY) $(call S,joint_frontier) $* > $(LOG)/frontier_$*.log 2>&1
$(R)/disclosure_%.csv: $(call S,disclosure) $(DEP)
	$(PY) $(call S,disclosure) $* > $(LOG)/disclosure_$*.log 2>&1
$(R)/robust_restricted_%.csv: $(call S,robust_restricted) $(DEP)
	$(PY) $(call S,robust_restricted) $* > $(LOG)/robust_$*.log 2>&1
$(R)/anchor_day_%.csv: $(call S,anchors) $(DEP)
	$(PY) $(call S,anchors) $* > $(LOG)/anchors_$*.log 2>&1
$(R)/disclosure_guarantee_%.csv: $(call S,disclosure_guarantee) $(DEP)
	$(PY) $(call S,disclosure_guarantee) $* > $(LOG)/dguar_$*.log 2>&1
$(R)/suppression_%.csv: $(call S,suppression) $(call S,disclosure_guarantee) $(R)/disclosure_guarantee_%.csv $(DEP)
	$(PY) $(call S,suppression) $* > $(LOG)/suppression_$*.log 2>&1
$(R)/contrast_%.csv: $(call S,contrast) $(DEP)
	$(PY) $(call S,contrast) $* > $(LOG)/contrast_$*.log 2>&1
$(R)/region_%.csv: $(call S,region) $(call S,extremal) $(R)/least_departure.csv $(DEP)
	$(PY) $(call S,region) $* > $(LOG)/region_$*.log 2>&1
$(R)/rev_%.csv: $(call S,revisions) $(R)/gap_adjusted.csv $(DEP)   # anchor mode reads gap_test_reg.csv (written by gap.py)
	$(PY) $(call S,revisions) $(word 1,$(subst _, ,$*)) $(word 2,$(subst _, ,$*)) > $(LOG)/rev_$*.log 2>&1
$(R)/spatial_scope_%.csv: $(call S,spatial_scope) $(call S,contrast) $(DEP)
	$(PY) $(call S,spatial_scope) $* > $(LOG)/spatial_$*.log 2>&1
$(R)/scope_sstar_%.csv: $(call S,scope_sensitivity) $(call S,spatial_scope) $(call S,region) $(call S,contrast) $(DEP)
	$(PY) $(call S,scope_sensitivity) $* > $(LOG)/scope_sstar_$*.log 2>&1
$(R)/sign_guarantee_%.csv: $(call S,sign_guarantee) $(call S,disclosure_guarantee) $(DEP)
	$(PY) $(call S,sign_guarantee) $* > $(LOG)/signg_$*.log 2>&1
$(R)/resampling_%_full.csv: $(call S,resampling) $(DEP)
	$(PY) $(call S,resampling) $* 200 full > $(LOG)/resamp_full_$*.log 2>&1
$(R)/resampling_%_txn.csv: $(call S,resampling) $(DEP)
	$(PY) $(call S,resampling) $* 100 txn > $(LOG)/resamp_txn_$*.log 2>&1

$(R)/gu_regression.csv: $(call S,gu_level) $(DEP)
	$(PY) $(call S,gu_level) > $(LOG)/gu_level.log 2>&1
$(R)/width_bound.csv: $(call S,width_bound) $(MAIN) $(DEP)
	$(PY) $(call S,width_bound) > $(LOG)/width_bound.log 2>&1
$(R)/adj_pairs_2026.csv: $(call S,dong_contrasts) $(DEP)
	$(PY) $(call S,dong_contrasts) > $(LOG)/dong_contrasts.log 2>&1
$(R)/calibrated_dow.csv: $(call S,calibrated_dow) $(DEP)
	$(PY) $(call S,calibrated_dow) > $(LOG)/calibrated_dow.log 2>&1
$(R)/gap_adjusted.csv: $(call S,gap) $(DEP)
	$(PY) $(call S,gap) > $(LOG)/gap.log 2>&1
$(R)/headcount_bands.csv: $(call S,headcounts) $(DEP)
	$(PY) $(call S,headcounts) > $(LOG)/headcounts.log 2>&1
$(R)/decomposition.csv: $(call S,decomposition) $(DEP)
	$(PY) $(call S,decomposition) > $(LOG)/decomposition.log 2>&1
$(R)/published_scale.csv: $(call S,published_allocation) $(DEP)
	$(PY) $(call S,published_allocation) > $(LOG)/published.log 2>&1
$(R)/integer_check.csv: $(call S,integer_check) $(DEP)
	$(PY) $(call S,integer_check) > $(LOG)/integer.log 2>&1
$(R)/integer_witness_%.csv: $(call S,integer_witness) $(DEP)
	$(PY) $(call S,integer_witness) $* > $(LOG)/integer_witness_$*.log 2>&1
$(R)/integer_witness_summary.csv: $(call S,verify_integer_witness) $(foreach s,$(SGCAL),$(R)/integer_witness_$(s).csv $(R)/spatial_scope_$(s).csv) $(DEP)
	$(PY) $(call S,verify_integer_witness) > $(LOG)/integer_witness_summary.log 2>&1
$(R)/price_lineage.csv: $(call S,price_lineage) build/build_trades.py $(wildcard data/raw/molit/seoul_apt_trades_*.csv data/raw/juso/*.csv) $(R)/spatial_scope_20121219.csv $(R)/spatial_scope_20170509.csv $(DEP)
	$(PY) $(call S,price_lineage) > $(LOG)/price_lineage.log 2>&1
$(R)/solver_check.csv: $(call S,solver_check) $(DEP)
	$(PY) $(call S,solver_check) > $(LOG)/solver.log 2>&1
$(R)/spec_sparse.csv: $(call S,specifications) $(call S,robust_restricted) $(DEP)
	$(PY) $(call S,specifications) > $(LOG)/specifications.log 2>&1
$(R)/adjacency_bounds.csv: $(call S,adjacency) $(DEP)
	$(PY) $(call S,adjacency) > $(LOG)/adjacency.log 2>&1
$(R)/outcomes.csv: $(call S,outcomes) $(DEP)
	$(PY) $(call S,outcomes) > $(LOG)/outcomes.log 2>&1
$(R)/least_departure.csv: $(call S,extremal) $(DEP)
	$(PY) $(call S,extremal) > $(LOG)/extremal.log 2>&1
$(R)/further_restrictions_bounds.csv: $(call S,further_restrictions) $(call S,directional) $(call S,spatial_scope) $(DEP)
	$(PY) $(call S,further_restrictions) > $(LOG)/further_restrictions.log 2>&1
$(R)/directional.csv: $(call S,directional) $(call S,spatial_scope) $(DEP)
	$(PY) $(call S,directional) > $(LOG)/directional.log 2>&1
$(R)/age_tercile.csv: $(call S,age_tercile) $(call S,contrast) $(call S,spatial_scope) $(DEP)
	$(PY) $(call S,age_tercile) > $(LOG)/age_tercile.log 2>&1
$(R)/oz_gap.csv: $(call S,oz_gap) $(DEP)
	$(PY) $(call S,oz_gap) > $(LOG)/oz_gap.log 2>&1
$(R)/election_day.csv: $(call S,election_day) $(call S,contrast) $(call S,spatial_scope) $(DEP)
	$(PY) $(call S,election_day) > $(LOG)/election_day.log 2>&1

# ---------------------------------------------------------------- paper
ALLRES  := $(AUDITRES) $(SCOPE) $(NEW) $(MAIN) $(VALID) $(RESOL) $(CALIBR) $(COMP) $(FRONT) $(DISC) $(ROBUST) $(ANCH) $(RESAMP) $(SINGLE)
TSTAMP  := paper/tables/.stamp
FSTAMP  := paper/figures/.stamp
PSTAMP  := paper/build/.stamp

$(TSTAMP): $(ALLRES) $(call S,build_tables) $(call S,appendix_tables) $(call S,tablelib) $(INPUTS)
	$(PY) $(call S,build_tables) && touch $@
$(FSTAMP): $(TSTAMP) $(call S,make_figures)
	$(PY) $(call S,make_figures) && touch $@
$(PSTAMP): $(TSTAMP) $(FSTAMP) paper/manuscript.md paper/appendix.md paper/build.py paper/word_layout.py $(wildcard paper/templates/*)
	$(PY) paper/build.py && touch $@

tables: $(TSTAMP)
figures: $(FSTAMP)
paper: $(PSTAMP)

# rebuild tables, figures and paper from the shipped results/ without checking them against code (fresh clones have
# arbitrary file times, so `make paper` there may decide to recompute everything)
.PHONY: paper-from-results
paper-from-results:
	$(PY) $(call S,build_tables) && $(PY) $(call S,make_figures) && $(PY) paper/build.py

clean:
	rm -rf $(R)/ydong paper/build $(TSTAMP) $(FSTAMP)

# Review copy: committed replication files, without repository/commit identifiers.
# For local revisions before committing: python3 paper/review_package.py OUT.zip --working-tree
# Generated PDFs and DOCX are included; private submission files are excluded.
review-package:
	$(PY) paper/review_package.py ../vwn_review_package.zip
