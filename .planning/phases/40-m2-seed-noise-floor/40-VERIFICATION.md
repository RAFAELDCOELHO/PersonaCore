---
phase: 40-m2-seed-noise-floor
verified: 2026-10-08T11:41:08Z
status: passed
score: 3/3 roadmap success criteria verified (plus 8/8 derived plan truths)
overrides_applied: 0
---

# Phase 40: M2 Seed Noise Floor Verification Report

**Phase Goal:** M2's training-seed noise floor is measured at S seeds and published beside v3.0's sampling floor, without amending v3.0's (b) margin.
**Verified:** 2026-10-08T11:41:08Z (HEAD ba1baa4, branch main)
**Status:** passed
**Re-verification:** No. This is the initial verification; no earlier 40-VERIFICATION.md existed.

Every number below comes from a command run in this session with `.venv/bin/python` (3.11), against the committed files. None is copied from a SUMMARY.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC1 | The full and M2 (no `pet_name`) adapters are retrained at S seeds taken from Phase 35's `seed_list`. S comes from COST-01 and is pre-registered. Each non-target's A2 recall is reported per seed with its denominator. | VERIFIED | `phase40_prereg.E2_S` = 5 = `results/phase36_budget.json::e2_seed_count` 5 = `unit_caps.E2.seeds` 5. `SEEDS` = (1337, 2024, 1338, 2025, 1339) = `phase35_prereg.seed_list()[:5]`. There are 10 distinct adapter sha256 values (5 seeds x 2 groups). `phase40_noise.arm_spec("m2")` proves that M2 drops exactly the target fact relative to `real` (scripts/phase40_noise.py:224-245). All five seed records have `provenance.run.device` = `mps`, launch HEAD c14dfa4, and `head_moved_during_run` False. The record's `per_seed` has 10/10 (seed, group) entries with 8 slots each, as n_answerable/n_questions with denominator 27 and per-tier 14/13. The report section "A2 recall per seed with its denominator (NOISE-01)" has 80 rows (5 x 2 x 8). |
| SC2 | The training-seed noise floor is published beside v3.0's sampling floor (0.14814814814814814), and v3.0's (b) margin is not amended. | VERIFIED | `recall_floor.published` = {value 0.3481481481481482, group m2, n_seeds 5, n_pairs 10, tie False}. `recall_floor.beside` = {sampling_floor 0.14814814814814814, margin_at_gate 0.2962962962962963, margin_amended False}. The sampling floor matches both `phase19_floor.NONTARGET_NOISE_FLOOR` and `results/phase19_noise_floors.json::nontarget_noise_floor.value` (both 0.14814814814814814). `git diff --quiet f2cc033^ HEAD -- results/phase19_noise_floors.json scripts/phase19_floor.py` succeeds, so v3.0's floor and margin source did not change during the phase. The last commit to `scripts/phase35_prereg.py` is 3805beb (2026-10-01), before Phase 40. Report line 239 prints the floor beside 0.14814814814814814 and "not amended (margin_amended False)". |
| SC3 | No record exists before the pre-registration module and its ancestry test are committed. Records are write-once and committed only after Rafael writes approved. | VERIFIED | The last prereg commit is 391e1c0 (2026-10-06 08:35). The first `results/phase40_*` commit is cf3b626 (2026-10-07 13:20). `git merge-base --is-ancestor 391e1c0` holds for cf3b626, ea8f7d3, fd603cd and 9a6a5e4. Ledger commit ea8f7d3 is an ancestor of cf3b626 (ledger before records) and is append-only (+14 lines, 0 deletions). Each of the 16 JSON records has exactly 1 commit. The report has 2 commits: 9a6a5e4, plus 4f7b2ff, which is an append-only dated continuation (the HEAD bytes start with the 9a6a5e4 bytes, 58921 then 65431 bytes). Every record commit message cites "Rafael's first/second/third approved 2026-10-07" or "Rafael's approved for the addendum". The verbatim replies are quoted in 40-10-SUMMARY (first, second) and 40-11-SUMMARY (third, addendum). The ancestry tests pass: `pytest tests/test_phase40_prereg.py -k "frozen or first_add"` gives 2 passed. The driver `scripts/phase40_noise.py` was last changed at 0b5c966 (2026-10-06), before the run and before every record. |

**Score:** 3/3 roadmap truths verified.

#### Derived plan truths (merged from the PLAN must_haves; none reduces scope)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| P1 | The floor is computed by the pinned v3.0 reductions (D-01..D-04), not by driver arithmetic. | VERIFIED | Recomputing with `phase40_prereg.recall_floor` over `a2_rows(a2_scope(...))` of the 10 committed A2 records gives full 0.2962962962962963 and m2 0.3481481481481482, each with 10 pairs, equal to the record. An independent check in plain Python (max over 7 non-target abs deltas, mean over C(5,2) = 10 pairs, from the record's counts) gives the same: full 0.2962962962962963 (max 0.5185, min 0.0741) and m2 0.3481481481481482 (max 0.6296, min 0.2222). |
| P2 | The per-seed counts are the A2 records' counts. | VERIFIED | For all 10 A2 records, the sha256 equals `per_seed[s][g].a2_record_sha256`, and the per-slot (n_answerable, n_questions) equals `slot_rows`. Cross-check against the arm's own scorer: each A2 record's `per_fact` (taught tier) equals the record's `per_tier.core_taught` for 80/80 slot rows. The draw tiers are {core_held_out, core_taught}. |
| P3 | Every seed is whole. Seed 2025's re-attempts follow R-3 b (Rafael's approved plus a cause note). | VERIFIED | `seeds.outcomes` lists all 5 seeds as `whole`, with dropped [] and not_run []. The ledger has start and end lines for 1337, 2024, 1338 and 1339. Seed 2025 has start/lost (14276.37 s), start/lost (120.01 s), then start/end. `results/phase40_seed2025.json::dropped_attempts` holds 2 entries, each with `approved` (Rafael's text) and `cause_note`. Per 40-09-SUMMARY, the third attempt's adapters are tensor-identical to both dropped attempts' adapters (72/72). |
| P4 | The prereg was not changed between the CPU rehearsal and the MPS launch. | VERIFIED | `rehearsal_disclosure[*].prereg_changed` = False for all 5 seeds. Rehearsal sha dfa1162, launch sha c14dfa4. The driver change (`driver_changed` True, 9 commits) is disclosed in the record. |
| P5 | The report equals `render_report(record)` at its own commit. | VERIFIED | `phase40_noise.render_report(json.load(record)).encode() == git show 9a6a5e4:results/phase40_noise_floor_report.md` is True. The report's sha256 starts 5b97b710939209e9 and the record's starts 678db43f213d9dd7, matching the hashes quoted in Rafael's approvals. |
| P6 | Phase 41 can consume the committed record (`e1_condition_c_band_inputs`). | VERIFIED | The committed `results/phase40_noise_floor.json` was copied into a scratch root and fed to the real `phase35_prereg.fill("e1_condition_c_band_inputs", ...)` with two synthetic band-input records. It returned bands (0.625, 1.4181) and (0.875, 1.9181), each equal to `mitigation_gate.dialogue_gap_band(..., gap_noise_floor=0.08406970366097503)`. |
| P7 | Both code reviews were resolved before the run. | VERIFIED | 40-REVIEW (prereg): 0 critical. Fixes 75a2ab5 through 97a06bf were made at 40-04, before the 391e1c0 freeze. 40-REVIEW-2 (driver): 0 critical, 4 WR and 6 IN. Fix commits 11c7e8c, cf685c4, d1a4195, b3f64f0, cdd30c2, 892065a, 6b81ae4, c250f08 and 0b5c966 all land before launch HEAD c14dfa4. |
| P8 | v3.0 identity predictions are recorded (D-07/D-08/D-08b). | VERIFIED | `identity.{m2_seed1337, full_seed1337, full_seed2024}.tensors_identical` = True, with 72/72 tensors each. `d08b.outcome` = NO_RESIDUAL with max_abs_rate_difference 0.0 (216 entries, 10368 completions, 0 differing). `predictions.status.observed` = MEASURED. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/phase40_prereg.py` | Pre-registration, estimator functions, ancestry-guarded | VERIFIED | 1662 lines. Fills `e2_S` and `e2_noise_floor_estimator` through `phase35_prereg.fill`. Used by the driver, the record and the tests. |
| `scripts/phase40_noise.py` | Driver: train, A2, emit, report | VERIFIED | 2036 lines. Produced the 15 run records and the noise-floor record. `render_report` reproduces the committed report. |
| `tests/test_phase40_prereg.py`, `tests/test_phase40_noise.py` | Ancestry and behaviour tests | VERIFIED | 195 passed in 37.24 s (run here). |
| `results/phase40_seed{1337,2024,1338,2025,1339}.json` + 10 `results/phase40_a2_{full,m2}_seed*.json` | Per-seed run records | VERIFIED | 15/15 tracked, 1 commit each. |
| `results/phase40_noise_floor.json` | NOISE-02 record | VERIFIED | `status` MEASURED. Committed alone in fd603cd. |
| `results/phase40_noise_floor_report.md` | Published report | VERIFIED | Equals the render at 9a6a5e4, followed by the approved dated continuation 4f7b2ff. |
| `ledger/v6_mps_ledger.jsonl` | E2 lines, committed before the records | VERIFIED | ea8f7d3 is append-only (+14) and is an ancestor of cf3b626. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| phase40_prereg.E2_S | results/phase36_budget.json (COST-01) | `phase35_prereg.fill("e2_S", input_records=(BUDGET_RECORD,))` | WIRED | Reads 5, cross-proved against `unit_caps.E2.seeds`. |
| phase40_prereg.SEEDS | phase35_prereg.seed_list() | `[:E2_S]` | WIRED | (1337, 2024, 1338, 2025, 1339). |
| driver arm_spec("m2") | phase19_erasure.retrain_arm_spec(target) | `_prove(dropped == [target])` | WIRED | Drops only the pet_name fact and keeps second_person/replay_ratio. |
| recall_floor.beside | phase19_floor.NONTARGET_NOISE_FLOOR / phase35_prereg.e1_condition_b_margin() | read, never typed | WIRED | margin = MARGIN_K x value, proved in phase35_prereg.py:444-447. |
| results/phase40_noise_floor.json | Phase 41 `e1_condition_c_band_inputs` | `phase35_prereg.fill` | WIRED | Tested here on the committed record (P6). |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| noise-floor record `per_seed.*.slots` | n_answerable/n_questions | A2 records' `draws` through `phase19_run._pooled_rows` | Yes. 80/80 rows agree with the arm scorer's `per_fact` (taught tier). | FLOWING |
| noise-floor record `recall_floor` | pair d, group floor | per-seed slot rows | Yes. Recomputed two independent ways. | FLOWING |
| report | all sections | `render_report(record)` | Yes. Byte-equal at 9a6a5e4. | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Phase 40 test files | `.venv/bin/python -m pytest tests/test_phase40_prereg.py tests/test_phase40_noise.py -q` | 195 passed in 37.24s | PASS |
| Ancestry guards | `pytest tests/test_phase40_prereg.py -k "frozen or first_add"` | 2 passed, 51 deselected | PASS |
| Slot ordering on the real repo | `pytest tests/test_phase35_prereg.py::test_slot_ordering_is_green_on_the_real_repo` | 1 passed | PASS |
| Lint | `ruff check` + `ruff format --check` on the 4 phase40 files | All checks passed; 4 files already formatted | PASS |
| Floor recomputation | prereg `recall_floor` over the committed A2 records | equal to the record (full 0.2963, m2 0.3481, 10 pairs) | PASS |
| Report = render | `render_report(record)` vs `git show 9a6a5e4:...` | True | PASS |
| Phase 41 consumer | `fill("e1_condition_c_band_inputs")` on the committed record (scratch root) | bands equal `dialogue_gap_band(...)` | PASS |

The full suite was not run, per project rule. 40-11-SUMMARY records 4495 passed / 4 skipped at 9a6a5e4 and at 4f7b2ff.

### Probe Execution

Step 7c: SKIPPED. No `scripts/*/tests/probe-*.sh` is declared by the Phase 40 plans, and this is not a migration phase.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| NOISE-01 | 40-01..40-11 (17 frontmatter mentions) | Full and M2 adapters retrained at S seeds from `seed_list`, S from COST-01 and pre-registered; per-seed A2 recall with denominator | SATISFIED | SC1, SC3, P2 and P3 |
| NOISE-02 | 40-02..40-11 (11 frontmatter mentions) | Training-seed floor published beside 0.14814814814814814 without amending the (b) margin | SATISFIED | SC2, P1 and P5 |

REQUIREMENTS.md maps only NOISE-01 and NOISE-02 to Phase 40 (lines 828-829), so no requirement is orphaned. Both still read `[ ]` / Pending in REQUIREMENTS.md and the ROADMAP plan checkboxes are unchecked. By 40-11-PLAN's own rule this is the orchestrator's hand close; it is not an implementation gap.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | No TBD/FIXME/XXX and no TODO/HACK/PLACEHOLDER in scripts/phase40_*.py, tests/test_phase40_*.py, tests/test_phase32_frontier.py or the report | - | - |

Info-level notes (no action needed):
- The report was changed once after its first commit (4f7b2ff). It is an append-only dated continuation through `scripts/_addendum.py`, with the prefix byte-identical, under a separate approved from Rafael that names this exact procedure. The 16 JSON records each have one commit.
- Rafael's third-attempt condition 6 asks for hours lost per attempt in "registro e relatório". The record carries the attempts and their causes but no hours field. The hours (14276.37 s, 120.01 s, total 3.999 h) are in the report's dated continuation. Rafael chose this explicitly ("Opção (a)", 40-09-SUMMARY), and he approved the record by its sha256 afterwards.
- The published floor (0.3481, m2) is above the unamended (b) margin (0.2963). This is a finding, not a defect. The report states it, and per the report and 40-11-SUMMARY its use in condition (b) is left to Phase 41's prereg.

### Human Verification Required

None. Every truth was checked by command against the committed files. The judgement calls (the addendum form, and where the hours go) were already ruled by Rafael in the quoted replies.

### Gaps Summary

No gaps. The phase goal holds in the codebase. S = 5 seeds were read from COST-01 and taken from `seed_list`. Both groups were retrained on MPS, and each non-target's A2 recall is published per seed as n/27 with per-tier denominators. The training-seed floor (m2 0.3481481481481482, 5 seeds, 10 pairs) is published beside v3.0's 0.14814814814814814, with the (b) margin 0.2962962962962963 read unchanged from v3.0's record (`margin_amended` False; v3.0 floor files unchanged since before the prereg). Every record commit follows the frozen prereg and its ancestry test, and each cites the approval that covers it. The remaining bookkeeping (NOISE-01/02 checkboxes in REQUIREMENTS.md, ROADMAP plan list, STATE.md) is the orchestrator's hand close.

---

_Verified: 2026-10-08T11:41:08Z_
_Verifier: Claude (gsd-verifier)_
