---
phase: 42
slug: dp-sgd-recipe-search-at-large
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-10-13
---

# Phase 42 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `42-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8 in `.venv` (Python 3.11), CPU-only |
| **Config file** | `pyproject.toml` (existing) |
| **Quick run command** | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase42_prereg.py tests/test_phase42_threshold_prereg.py tests/test_phase42_recipes.py` |
| **Census subset** | two calls (one `-k` applies to every file in a call): `.venv/bin/pytest -q tests/test_phase35_prereg.py -k "slot_census or slot_ordering or grids_must or e3_"` then `.venv/bin/pytest -q tests/test_phase36_caps.py tests/test_phase36_ledger.py tests/test_phase23_resume.py tests/test_phase25_driver.py::test_os_replace_appears_only_in_the_two_phase25_writers tests/test_lora_inject.py tests/test_phase21_sc5.py tests/test_phase19_erasure.py::test_retention_measurement_pins_a_new_call_site_with_no_adapted_precedent tests/test_phase20_correction.py::test_mitigation_point_verdict_has_no_caller_outside_this_module tests/test_phase32_frontier.py::test_v4_bytes_unchanged_since_the_v4_tag` |
| **Full suite command** | `nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` plus a waiter on `^EXIT=` (Bash caps a call at 600 s) |
| **Estimated runtime** | quick ~60 s; full ~40-56 min (Phase 41 close: 4709 passed / 4 skipped) |

---

## Sampling Rate

- **After every task commit:** quick run plus the census subset (~3 min; census call 2 alone measured 113 s)
- **After every plan wave:** full suite on a COMMITTED tree, run again after each record commit (new reds appear only once records are tracked)
- **Before any MPS launch:** code review of prereg + driver, then a CPU rehearsal (`phase42rh` prefix, tmp root, `device='cpu'`) exercising D-21's four legs
- **Before `/gsd:verify-work`:** full suite green
- **Max feedback latency:** quick run ≤ 120 s

---

## Per-Task Verification Map

Per plan (every task carries an `<automated>` verify; full commands in each PLAN.md):

| Plan | Wave | Automated verify per task |
|------|------|---------------------------|
| 42-01 | 1 | T1-T2: `tests/test_phase42_prereg.py` + phase35 census (`-k`, own call); T3: phase42/35/36 prereg + caps + phase21_sc5 + phase23_resume |
| 42-02 | 2 | T1: phase42_prereg + ruff; T2: `-k "threshold or clip or train_config"`; T3: `-k gitignored` + `git check-ignore` |
| 42-03 | 3 | T1: `-k "verdict or table or descriptive or retention or summary or lead or typed or census or forbidden"`; T2: whole file + ruff |
| 42-04 | 4 | T1: recipes `-k "warmup or clip or resume or take or torch"`; T2: recipes + retention census; T3: recipes + prereg + phase35/36 guards |
| 42-05 | 5 | T1: `-k "build_record or emit or retention"`; T2: `-k "report or main or plist"` + plutil; T3: both files + two-call census subset |
| 42-06 | 6 | T1: 42-REVIEW.md has Resolution; T2: both files + ruff; T3: full-suite log `^EXIT=0` |
| 42-07 | 7 | T1: rehearsal log `REHEARSAL_EXIT=0`; T2: no `phase42rh_` / `results/phase42*` left in the real tree |
| 42-08 | 8 | T1: preflight + clean porcelain; T2: ledger report; T3: every control has an end line |
| 42-09 | 9 | T1: ledger report + fill; T2: threshold prereg + phase35/36 guards; T3: full-suite log |
| 42-10 | 10 | T1: preflight + clean porcelain; T2: ledger report; T3: every point has an end line |
| 42-11 | 11 | T1: ledger report + ENTRIES; T2: ledger/prereg/ancestry guards; T3: E3 record lead/summary/labels |
| 42-12 | 12 | T1: full-suite log; T2: report vs E3 record; T3: full-suite log |

Requirement / decision → test map (from research):

| Req / D | Behavior | Test Type | Automated Command | File Exists | Status |
|---------|----------|-----------|-------------------|-------------|--------|
| RECIPE-01, D-01/02/03/09 | 4 recipes, batch 8, seed 1337, v4.0 control reused by sha, caps | unit (real repo) | `pytest tests/test_phase42_prereg.py -k grid` | ❌ W0 | ⬜ pending |
| RECIPE-01, SC5 | prereg + test precede every `results/phase42_*` | ancestry | `pytest tests/test_phase42_prereg.py -k "frozen or first_added or records_at_commit"` + `test_phase35_prereg.py -k slot_ordering` | ❌ W0 | ⬜ pending |
| RECIPE-04, D-08 | P22 onsets 0.0789 / 0.1578 asserted; planted crossing refuses | unit | `pytest tests/test_phase42_prereg.py -k p22` | ❌ W0 | ⬜ pending |
| RECIPE-02, D-11/D-14 | ε per point (tolerance), `selection_accounted` False, basic composition over the 8 noised only | unit | `pytest tests/test_phase42_prereg.py -k epsilon` | ❌ W0 | ⬜ pending |
| RECIPE-03, D-12 | pass iff both legs ≥ fill threshold; REFUSED from the fill; 4×2 labels | unit (truth table) | `pytest tests/test_phase42_prereg.py -k "label or verdict"` | ❌ W0 | ⬜ pending |
| RECIPE-03, D-19 | threshold file after its inputs, before every noised record | ancestry | `pytest tests/test_phase42_threshold_prereg.py` | ❌ W0 | ⬜ pending |
| D-05 | warmup 20 / 80; seam rebinds and restores (also on exception); sidecar `train_config` asserted | unit (fake train_stage) | `pytest tests/test_phase42_recipes.py -k warmup` | ❌ W0 | ⬜ pending |
| D-06/D-07 | noised clip = CLIP_NORM, control clip non-binding, grad_clip 1.0 | unit | `pytest tests/test_phase42_recipes.py -k clip` | ❌ W0 | ⬜ pending |
| D-13 | retention / dialogue gap published, never read by the label function | unit (AST) | `pytest tests/test_phase42_prereg.py -k "descriptive or reads_only_recall"` (test_descriptive_reading, test_point_verdict_reads_only_recall) | ❌ W0 | ⬜ pending |
| D-14/D-15 | summary "k de 8 pontos passam; m REFUSED"; null first line literal | unit | `pytest tests/test_phase42_prereg.py -k "summary or null"` | ❌ W0 | ⬜ pending |
| D-16/D-17 | predictions in prereg before any record; D-16 from `phase25_recall.json` | unit + ancestry | `pytest tests/test_phase42_prereg.py -k prediction` | ❌ W0 | ⬜ pending |
| D-18 (corrected) | a learning control with worse retention changes no label; retention row descriptive | unit | `pytest tests/test_phase42_prereg.py -k control_retention_row` + `pytest tests/test_phase42_recipes.py -k worse_retention_in_a_learning_control` | ❌ W0 | ⬜ pending |
| D-23 | each point carries its control's raw k/n on both legs beside the label | unit | `pytest tests/test_phase42_prereg.py -k table_4x2_with_control_recall` + `pytest tests/test_phase42_recipes.py -k build_record_labels_only_through_the_prereg` | ❌ W0 | ⬜ pending |
| D-20 | REFUSED recipe's noised cells still in run order | unit | `pytest tests/test_phase42_recipes.py -k refused_still_runs` | ❌ W0 | ⬜ pending |
| D-22 | launch refuses without `require_launch("E3")`; write-once; end line per MPS record | unit | `pytest tests/test_phase42_recipes.py -k "launch or write_once or ledger"` | ❌ W0 | ⬜ pending |
| Pitfall 6 | float vs exact-rational threshold disagreement enumerated | unit | `pytest tests/test_phase42_threshold_prereg.py -k exact` | ❌ W0 | ⬜ pending |
| census | phase42 files pass every repo census | existing | census subset | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase42_prereg.py` — committed in the same commit as `scripts/phase42_prereg.py`
- [ ] `tests/test_phase42_threshold_prereg.py` — with the threshold fill file
- [ ] `tests/test_phase42_recipes.py` — driver; fake `train_stage` / `score_arm`, tmp ledger
- [ ] `.gitignore` lines for the `phase42e3_*` / `phase42rh_*` csv dirs + a test (Phase 41 precedent)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| D-10 MPS noise identity | D-10 | measured once in research (MPS, 3 steps, `torch.equal`, max diff 0.0) | descriptive; no re-check required |
| D-21 rehearsal | D-21 | CPU training, hours | scratch driver run, `REHEARSAL_EXIT=0` + STEP lines |
| Approvals | D-22, SC5 | Rafael writes "approved" | one approved per launch; record commits after approval |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 120s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

## Plan-check findings log (origin per finding)

| Iteration | Finding | Origin (revision-introduced / pre-existing) |
|-----------|---------|---------------------------------------------|
| 1 | B1 42-04/08/10: real-root preflight refuses untracked whole-unit records (crash_rule dead) | pre-existing (initial plan) |
| 1 | B2 42-01: D-18 "degrade retention → REFUSED" text with no rule; Rafael ruled recall-only + D-23 | pre-existing (CONTEXT wording) |
| 1 | W1 census subset: one -k over all files, 13/189 collected | pre-existing (research command) |
| 1 | W2 two -k flags in one call (42-01/04/09/11) | pre-existing |
| 1 | W3 42-03 descriptive_reading truth with no task | pre-existing |
| 1 | W4 42-03 AST gate scans docstring | pre-existing |
| 1 | W5 42-01 refusal_omitted source vs dc578f9 test | pre-existing |
| 1 | W6 42-02/07 tamper byte can break JSON | pre-existing |
| 1 | W7 42-05 report order vs D-15 | pre-existing |
| 1 | W8 RESEARCH open questions / VALIDATION map | pre-existing (orchestrator fixed RESEARCH + census row) |
| 2 | W 42-01: `_RULING_CONTEXT` git-show test only in `<interfaces>` — orchestrator added the Task 2 behavior bullet | revision-introduced |
| 2 | W 42-04: relaunch-pathspec test reached real-tree preflight legs — orchestrator: `_launch_requirements` no-op + sentinel-raising stub | revision-introduced |
| 2 | W 42-02: threshold_fill_inputs source cited superseded D-18 at dc578f9 — orchestrator: `_RULING_CONTEXT.format('18')` | revision-introduced |
| 2 | W VALIDATION: no D-18/D-23 rows, D-13 missed AST test, map unfilled — orchestrator filled | pre-existing |
| 2 | I 42-03: `-k literal` matched no test — orchestrator: `typed` | pre-existing |
| 2 | I 42-10: relaunch `??` equality → subset of the excluded set | revision-introduced |
| 3 | PASSED — 0 blockers; info wording fixes applied by orchestrator (42-01/42-02 `_RULING_CONTEXT` named, VALIDATION row/latency text) | revision-introduced (info only) |
