---
phase: 31-mps-cost-probes-and-budget-commitment
verified: 2026-09-27T14:00:00Z
status: passed
score: 4/4 roadmap success criteria verified (plan must-haves 6/6 plans verified)
overrides_applied: 0
---

# Phase 31: MPS Cost Probes and Budget Commitment — Verification Report

**Phase Goal:** The v5.0 budget is committed from measured MPS cost — one replay-bearing adversarial point end to end and one relearning leg on a real adapter — replacing the unmeasured ~25-30 h estimate.
**Verified:** 2026-09-27
**Status:** passed
**Re-verification:** No (initial verification)

Every figure below comes from a command the verifier ran against the committed bytes. The field path is given for each one. SUMMARY claims were not used as evidence.

## Goal Achievement

### Observable Truths (ROADMAP SC1-SC4)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | One replay-bearing adversarial point runs end to end on MPS (training, condition (c), attack scoring) with per-stage wall-clock, beside Phase 25's measured per-point pace (ARCAL-01) | VERIFIED | `results/phase31_probe_point.json`: `device`="mps", `torch_version`="2.7.1". `stages.{train,measure,recall,draw,score}.seconds` = 633.46 / 89.29 / 1079.44 / 5620.57 / 0.099, and they sum exactly to `total_seconds`=7422.87. `replay.per_step`: len 200, set {256}, `all_steps_equal`=true. `sweep_point`=false with a reason. `readings.gates_nothing`=true. `phase25_twin` (from `results/phase25_point_adv_n64_ratio0p000000.json`) sits beside it: train 80.30, measure 87.77, draw 3851.56, recall 997.98. `phase25_per_point_minutes` min/median/max = 49.34/64.12/70.82 (n=12). The verifier recomputed this from the 12 `results/phase25_point_adv_*.json` and got identical values. |
| 2 | One relearning leg runs on MPS on a real trained adapter (not Phase 27's CPU apparatus), with per-leg wall-clock recorded (ARCAL-02) | VERIFIED | `results/phase31_probe_relearn.json`: `device`="mps", `arm`="mitigated", `seed`=1337, `relearn_cap`=400, `rungs`=[50..400] (8), `k`=16. `arm_seconds`=43455.49, which equals `stages.train.seconds` (210.41) + the sum of the 8 `stages.rungs[].seconds` (recomputed). Every `remainder_seconds` > 0. `start_sha256` == the point record's `adapter.sha256` == sha256 of `checkpoints/probe31_advr_n64_adapter.pt` on disk (04929111…4244), so the adapter is the probe's own real adapter. |
| 3 | The budget derives sweep + relearning cost from the two probe records, not the ~25-30 h estimate, and an ancestry test proves it precedes the first sweep point (ARCAL-03) | VERIFIED | `results/phase31_budget.json`: all 16 `sources` sha256 match the committed blobs at d22a017. Independent recomputation matches: `derived.per_window_seconds`=0.010804; n8 train=160.848; `sweep.scheduled.estimate`=82724.75 s (22.98 h, high 25.18 h); `stop_line.seconds`=135989.46 (=1.5×90659.64, 37.77 h); `relearning.scheduled_seconds`=0; `full_k_rescore.per_point_seconds.estimate`=15220.71; conditional n64 a=1 → 319409.17, a=5 → 554114.01. `reconciliation` records the unsourced "~25-30 h" and its origin against the computed Phase 25 sums (12.56 h without recall, 15.88 h with). `test_ancestry_budget_precedes_every_sweep_point` and `test_ancestry_probes_precede_the_budget` pass, each with a natural-RED non-vacuity assertion. |
| 4 | Both probes write to their own probe paths, never under a PREREG-01 point key (ARCAL-01, ARCAL-02) | VERIFIED | `phase29_prereg.POINT_KEYS()` has 12 keys, and "probe31_advr_n64" is not among them. `POINT_RECORD_PREFIX`="results/phase32_point_", and none of the 3 phase31 records starts with it or contains a point key. `git ls-files 'results/phase32_*'` is empty. On disk, no file under data/results/checkpoints matches phase32_*, phase25_phase32_*, data/phase27_*, persona_relearn_attacker_* or checkpoints/phase27_*; the only phase27 match is the pre-existing tracked `results/phase27_admission.json`. The relearn leftovers live under `data/probe31_relearn/`. |

**Score:** 4/4 roadmap truths verified

### Plan must-haves (summary)

| Plan | Key must-haves checked | Status |
|------|------------------------|--------|
| 31-01 | `probe_plan` uses `phase30_points.next_action` (line 142). `tp.train` is rebound and then restored in `finally` (lines 388-402). Emit path resolves from `V5_RESULT_PATHS` (lines 66-70) and is written via `atomic_write_json`. `sweep_point` false. Recall is timed separately (`stages.recall`). | VERIFIED |
| 31-02 | Relearning uses only `phase27_relearn.train_relearn_arm` + `score_rung` (plus the `shared_train_config` helper). No `run_*` or `_require_admitted` call. The plist has caffeinate, `phase31_probe.py run`, `PERSONACORE_SWEEP_ACTIVE`, and RunAtLoad/KeepAlive false. The last heartbeat line is `stage: "done"` (2026-09-27T11:31:01Z). | VERIFIED |
| 31-03 | `scripts/phase31_budget.py` holds the formula, spread, stop line and conditional relearning. The recompute and ancestry tests are present and green. | VERIFIED |
| 31-04 | Gitignored MPS sidecars `data/probe31_point_run.json` / `data/probe31_relearn_run.json` exist. `data/probe31_point_replay.json` holds per_step 256s. No stray paths. | VERIFIED |
| 31-05 | 966f91b touches only `results/phase31_probe_point.json`. 28338cd touches only `results/phase31_probe_relearn.json`. 966f91b is an ancestor of 28338cd, and 4339f2b is an ancestor of 966f91b. | VERIFIED |
| 31-06 | d22a017 touches only `results/phase31_budget.json`, and 28338cd is an ancestor of it. The developer ruling is recorded verbatim in 31-06-SUMMARY.md:42 ("approved — …"). `phase28_report.py check` exit 0. | VERIFIED |

### Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `scripts/phase31_probe.py` | VERIFIED | 942 lines. `run_point_probe`, `run_relearn_probe`, emits, CLI. Imported by the budget and the tests. |
| `scripts/phase31_budget.py` | VERIFIED | 420 lines. `STOP_LINE_FACTOR`. Reads committed blobs via `phase30_points._tracked_json` (git show HEAD, refuses working-tree edits). |
| `tests/test_phase31_probe.py`, `tests/test_phase31_budget.py` | VERIFIED | 729 / 428 lines, all green. |
| `artifacts/com.personacore.phase31.probe.plist` | VERIFIED | D-12 agent. |
| `results/phase31_probe_point.json` / `_relearn.json` / `phase31_budget.json` | VERIFIED | Committed alone. Worktree equals HEAD. |

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| phase31_probe | phase30_points.next_action | `probe_plan` | WIRED |
| phase31_probe | train()'s on_draw | rebinding `tp.train` → the record's per_step counts | WIRED (200×256 in record) |
| relearn record | point record | `start_sha256` == `adapter.sha256` | WIRED |
| budget | probe records + 12 Phase 25 records + recall + calibration | `sources{path: sha256}` | WIRED (all 16 hashes match committed blobs) |
| test_phase31_budget | test_phase29_prereg._assert_frozen_before | import | WIRED |

### Non-vacuity of `test_committed_budget_recomputes_from_committed_files`

`_is_tracked(BUDGET)` is true (`git ls-files results/phase31_budget.json` returns the path), so the tracked branch runs. That branch rebuilds `budget.build_record(probe._tracked())` and compares it with the committed record, minus only `provenance` and `calibration` (`_strip`, test line 374-375). The comparison therefore covers sweep, stop_line, relearning, per_point, spread, inputs, sources, formula and reconciliation. It is a real equality check. The verifier's independent recomputation of the headline figures agrees.

### Behavioral Spot-Checks and Tests

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Targeted phase 31 and guard suites | `.venv/bin/pytest tests/test_phase31_probe.py tests/test_phase31_budget.py tests/test_phase27_relearn.py tests/test_phase29_prereg.py tests/test_phase30_calibration.py tests/test_phase30_points.py -q -p no:cacheprovider -rs` | 209 passed, 0 skipped, EXIT=0 (120 s) | PASS |
| Frozen report check | `.venv/bin/python scripts/phase28_report.py check` | exit 0, no output | PASS |
| Budget recompute (independent) | inline python over the committed JSONs | every value checked matches | PASS |
| Full suite | not re-run (per instruction; the orchestrator reported 3127 passed / 4 skipped at d22a017) | — | not re-verified |

### Probe Execution

No `scripts/*/tests/probe-*.sh` is declared for this phase. The "probes" here are the MPS cost runs, and their evidence is the committed records plus the sidecars checked above. Not applicable.

### Requirements Coverage

| Requirement | Source Plans | Status | Evidence | Tick supported? |
|-------------|--------------|--------|----------|-----------------|
| ARCAL-01 | 31-01, 31-02, 31-04, 31-05 | SATISFIED | SC1 + SC4 evidence. The point record was committed alone in 966f91b, before the budget (d22a017). | Yes |
| ARCAL-02 | 31-02, 31-04, 31-05 | SATISFIED | SC2 evidence. MPS, real adapter by sha, committed alone in 28338cd, before the budget. | Yes |
| ARCAL-03 | 31-03, 31-06 | SATISFIED | SC3 evidence. The budget derives from the committed probes, replaces ~25-30 h with 22.98 h (18.14-25.18 h) + a 37.77 h stop line, and the ancestry guards are green. | Yes |

No orphaned IDs: REQUIREMENTS.md maps exactly ARCAL-01..03 to Phase 31 (traceability :666-668), and every plan's `requirements` field falls within that set. REQUIREMENTS.md still shows all three as `[ ]` / Pending. Ticking them is left to the orchestrator/developer.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (phase 31 scripts/tests/plist) | — | TBD/FIXME/XXX/TODO/HACK | none found | — |
| `31-VALIDATION.md` frontmatter | 4-6 | `status: draft`, `wave_0_complete: false` | Info | The body statuses were filled (a4f9b0a), but the frontmatter was not flipped. Cosmetic. |
| 31-02 must-have D-06 wording | — | "only train_relearn_arm and score_rung are imported"; `phase27_relearn.shared_train_config()` is also called (probe line 783) | Info | This is a config helper, not a `run_*` leg, and `phase27_relearn.py` is byte-unchanged (no commit in the phase range touches it). The intent (no `_require_admitted`) holds. |
| Ancestry guard vs sweep points | — | `test_ancestry_budget_precedes_every_sweep_point` currently checks an empty points list | Info | This is inherent: no Phase 32 point exists yet. The natural-RED assertion proves the helper binds, and the guard becomes substantive with the first Phase 32 commit. |

Protected modules: across `ebf2f83~1..HEAD`, no commit touches `scripts/phase27_relearn.py`, `scripts/teach_persona.py`, `tests/test_phase27_relearn.py`, `scripts/phase30_points.py` or `src/`. The phase added only 8 new files (diff stat).

### Human Verification Required

None outstanding. The one human gate (developer review of the budget and stop line before the irreversible commit) is already recorded verbatim in 31-06-SUMMARY.md:42. The unattended MPS runs finished: heartbeat last line `done`, and both sidecars are complete.

### Gaps Summary

No gaps. Both probes ran on MPS and were committed alone, in order (point → relearn → budget), after the calibration commit 4339f2b. The budget recomputes byte-for-byte (minus provenance/calibration) from committed files and replaces the unsourced ~25-30 h with a measured 22.98 h scheduled sweep estimate (range 18.14-25.18 h). It also carries a 37.77 h stop line for Phase 32 and prices relearning as 0 h scheduled, 88.7-153.9 h conditional per leg. No results/phase32_* file exists.

---

_Verified: 2026-09-27_
_Verifier: Claude (gsd-verifier)_
