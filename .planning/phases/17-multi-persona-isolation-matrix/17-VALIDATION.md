---
phase: 17
slug: multi-persona-isolation-matrix
status: planned
nyquist_compliant: true
wave_0_complete: false
created: 2026-08-14
task_ids_backfilled: 2026-08-14
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `17-RESEARCH.md` §Validation Architecture. Where RESEARCH.md and the working tree
> disagreed, the **measurement taken on 2026-08-14 wins** and the discrepancy is recorded below.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest 9.0.3` (pinned `pytest~=9.0`, `pyproject.toml:19`) |
| **Config file** | `pyproject.toml` → `[tool.pytest.ini_options]`, `testpaths = ["tests"]`, `pythonpath = ["."]` |
| **Quick run command** | `.venv/bin/pytest -q tests/test_phase17_*.py` |
| **Full suite command** | `make test` (i.e. `pytest -q`) |
| **Estimated runtime** | full suite **~122 s**; quick run seconds (CPU) |
| **Constraint** | **CPU-only, GPU-free, no checkpoint I/O, no model load, no generation** — the register every Phase 14/15/16 test file follows. Drivers are loaded with `importlib.util.spec_from_file_location` so `main()` never runs. |

> **Baseline correction (2026-08-14):** `17-RESEARCH.md` §Sampling rate cites "407 passed / 1 skipped
> in ~117 s". Measured on the current tree: **579 passed, 1 skipped, 122.42 s**. Use 579/1 as the
> pre-phase baseline — a Wave-0 run reporting 407 means tests were *lost*, not that the baseline
> was met.

---

## Sampling Rate

- **After every task commit:** `.venv/bin/pytest -q tests/test_phase17_*.py`
- **After every plan wave:** `make test` (full suite)
- **Before `/gsd:verify-work`:** full suite green **plus `make lint`**
- **Max feedback latency:** ~122 s (full suite); seconds for the phase-17 quick run

---

## Per-Task Verification Map

Task IDs backfilled by `/gsd:plan-phase` on 2026-08-14. Task ID scheme is `T-17-NN`, sequential
across the phase in plan/task order; threat-register ids use the disjoint `TH-17-NN` namespace so
the two never collide (the repo's existing task ids are `T-{phase}-{NN}`, e.g. `T-16-13`).

The requirement → behavior → command mapping was fixed **before** planning. Three commands below
carry a **[corrected]** marker where the plan's actual test name or file differs from the
pre-planning draft; each correction is justified underneath the table and none of them changes what
is being asserted.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| T-17-07 | 17-03 | 2 | ISO-01 | — | N/A | unit | `pytest tests/test_phase17_personas.py -x` | ❌ created by T-17-07 | ⬜ pending |
| T-17-07 | 17-03 | 2 | ISO-01 | TH-17-09 | Every minted value ≤ 8 tokens, round-trips exactly | unit | `pytest tests/test_phase17_personas.py::test_token_census_matches_locked_literals -x` **[corrected]** | ❌ created by T-17-07 | ⬜ pending |
| T-17-12 | 17-05 | 3 | ISO-01 | TH-17-23 | Training refuses without a recorded GO/ADAPT verdict | unit | `pytest tests/test_phase17_personas.py::test_verdict_blocks -x` | ❌ created by T-17-12 | ⬜ pending |
| T-17-15 | 17-06 | 3 | ISO-02 | TH-17-21 | All N+1 sweep records carry an identical `(slot, seed_index, question)` set | unit | `pytest tests/test_phase17_scoring.py::test_sweeps_are_pairable -x` **[corrected]** | ❌ created by T-17-15 | ⬜ pending |
| T-17-10 | 17-04 | 2 | ISO-02 | — | Fixture regroups to exactly 8 slots × 13 questions | unit | `pytest tests/test_phase17_scoring.py::test_slot_regrouping -x` | ❌ created by T-17-10 | ⬜ pending |
| T-17-15 | 17-06 | 3 | ISO-03 | TH-17-21 | The base sweep carries the all-zero `lora_B` digest; the adapter sweeps do not | unit | `pytest tests/test_phase17_scoring.py::test_base_column_is_a_control -x` **[corrected]** | ❌ created by T-17-15 | ⬜ pending |
| T-17-15 | 17-06 | 3 | ISO-04 | TH-17-18 | Silent adapter substitution cannot pass undetected (mutation-proved) | unit (tiny GPT, CPU) | `pytest tests/test_phase17_scoring.py::test_swap_canary_bites -x` | ❌ created by T-17-15 | ⬜ pending |
| T-17-15 | 17-06 | 3 | ISO-04 | TH-17-18 | `--report` refuses when two sweep digests match | unit | `pytest tests/test_phase17_scoring.py::test_report_refuses_identical_digests -x` **[corrected]** | ❌ created by T-17-15 | ⬜ pending |
| T-17-03 | 17-01 | 1 | ISO-05 | TH-17-38 | Replication reaches neither `holm` nor `sign_test_exact` | static AST | `pytest tests/test_phase17_stats.py::test_replication_is_not_gated -x` | ❌ created by T-17-03 | ⬜ pending |
| T-17-05 | 17-02 | 1 | ISO-06 | TH-17-04 | Consumers inject at the artifact's own `lora_config` | static AST | `pytest tests/test_lora_inject.py -x` (extend) | ✅ partial — `test_load_adapter_weights_refuses_wrong_alpha` | ⬜ pending |
| T-17-03 | 17-01 | 1 | ISO-07 | — | `0.2486` / `0.2000` appear in no Phase 17 file | static source scan | `pytest tests/test_phase17_stats.py::test_no_phase14_thresholds -x` | ❌ created by T-17-03 | ⬜ pending |
| T-17-20 | 17-08 | 4 | STAT-01 | TH-17-30 | Signs computed on the question rate, not the draw rate | unit | `pytest tests/test_phase17_stats.py::test_signs_use_the_question_unit -x` | ❌ created by T-17-03, extended by T-17-20 | ⬜ pending |
| T-17-20 | 17-08 | 4 | STAT-02 | TH-17-27 | No bare `0%`; every zero cell carries denominator + bound | unit (writer) | `pytest tests/test_phase17_stats.py::test_no_bare_zero_percent -x` | ❌ created by T-17-03, extended by T-17-20 | ⬜ pending |
| T-17-03, T-17-20 | 17-01, 17-08 | 1, 4 | STAT-03 | TH-17-26 | Family is exactly 6; nothing else reaches `holm` | unit + static AST | `pytest tests/test_phase17_stats.py -x` | ❌ created by T-17-03 | ⬜ pending |
| T-17-03 | 17-01 | 1 | STAT-04 | TH-17-SC | `pyproject.toml` byte-identical; stdlib + repo imports only | static AST + file hash | `pytest tests/test_phase17_stats.py::test_no_new_dependencies tests/test_package.py -x` **[corrected]** | ❌ AST half created by T-17-03; ✅ hash half — `tests/test_package.py:11,36` | ⬜ pending |
| T-17-02 | 17-01 | 1 | STAT-05 | TH-17-01 | Pre-registration commit precedes every results artifact | static + git | `pytest tests/test_phase16_prereg.py -x` **[corrected]** | ✅ file exists — new test added by T-17-02 | ⬜ pending |
| T-17-03 | 17-01 | 1 | STAT-06 | TH-17-13 | No aggregate 9-cell rate computed or printed | static AST | `pytest tests/test_phase17_stats.py::test_no_nine_cell_aggregate -x` | ❌ created by T-17-03 | ⬜ pending |
| T-17-10 | 17-04 | 2 | SC3 (ISO-02) | TH-17-10 | `inspect.signature(score_completion)` carries no `(i, j)` | unit + static AST | `pytest tests/test_phase17_scoring.py::test_scorer_is_cell_blind -x` | ❌ created by T-17-10 | ⬜ pending |
| T-17-20 | 17-08 | 4 | D-10 | TH-17-32 | All-fail branch text committed; writer emits it below six | unit (writer) | `pytest tests/test_phase17_stats.py::test_all_fail_branch -x` | ❌ created by T-17-03, extended by T-17-20 | ⬜ pending |
| T-17-03 | 17-01 | 1 | D-18 | TH-17-02 | Gate clears only on **all six** Holm rejections | unit | `pytest tests/test_phase17_stats.py::test_gate_requires_all_six -x` | ❌ created by T-17-03 | ⬜ pending |
| T-17-03 | 17-01 | 1 | D-19 | TH-17-36 | `worst_pair` tie-break deterministic at the all-zero tie | unit | `pytest tests/test_phase17_stats.py::test_worst_pair_tiebreak -x` | ❌ created by T-17-03 | ⬜ pending |
| T-17-20 | 17-08 | 4 | D-21 | TH-17-26 | Phase-17 twin of the six-pairs gate scan | static AST | `pytest tests/test_phase17_stats.py::test_nothing_outside_the_six_pairs_enters_the_verdict_path -x` **[corrected]** | ❌ created by T-17-03, extended by T-17-20 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### Corrections to the pre-planning command draft

1. **`::test_census` → `::test_token_census_matches_locked_literals`.** The plan follows
   `tests/test_phase14_factset.py`'s existing name for the identical assertion, so the two census
   tests read as siblings rather than as two unrelated rules. Assertion unchanged.
2. **`tests/test_phase17_stats.py::test_sweeps_are_pairable` /
   `::test_report_refuses_identical_digests` / `::test_base_column_is_a_control` →
   `tests/test_phase17_scoring.py`.** All three assert properties of the ISO-04 canary and the sweep
   record shape, which plan 17-06 builds alongside the canary; keeping them beside
   `test_swap_canary_bites` puts the whole ISO-02/03/04 guard set in one file instead of splitting a
   single mechanism across two. Assertions unchanged.
3. **`tests/test_phase17_stats.py::test_prereg_precedes_results` →
   `tests/test_phase16_prereg.py::test_phase17_prereg_is_frozen_before_every_phase17_result`.**
   `17-PATTERNS.md` §Already Covered is correct that `V3_ARTIFACT_GLOBS` at
   `tests/test_phase16_prereg.py:54` already includes `results/phase17_*` — but that test pins the
   **erasure-rule** commit (`23a830c`), which is trivially an ancestor of everything Phase 17 writes,
   so it does not pin Phase 17's OWN pre-registration. Plan 17-01 T2 adds the Phase-17 guard
   **additively in that same file** rather than as a twin in `test_phase17_stats.py`, so one file
   owns the ordering rule. The guard is derived from `git log` over
   `scripts/phase17_personas.py` rather than pinned to a SHA: a hand-pinned SHA needs a separate
   identity check and still permits an edit to the pre-registration *after* the numbers exist, while
   the derived form is self-identifying and catches the edit.
4. **`test_no_new_dependencies` now also runs `tests/test_package.py`.** Per
   `17-PATTERNS.md` §Already Covered, the file-hash half of STAT-04 is already enforced by
   `test_pyproject_unchanged_since_v2_close` (`PYPROJECT_SHA256` at :11, compared at :36). Phase 17
   adds only the genuinely new AST half — stdlib + repo imports only. No Phase-17 twin of the hash
   check is planned; a second copy of one rule can drift out of sync with the first.
5. **`::test_nothing_outside_the_six_pairs` → full name
   `::test_nothing_outside_the_six_pairs_enters_the_verdict_path`,** matching Phase 16's name for the
   same guard (`tests/test_phase16_stats.py:747`) so the twin is recognisable as a twin.

---

## Wave 0 Requirements

There is no separate Wave 0 in this phase. Each test file is created **in the same plan and commit as
the code it verifies**, which is the register every Phase 14/15/16 plan followed, and every task's
`<verify>` block names an `<automated>` command that exists at the end of that task. The Wave-0 files
and their owning tasks:

- [ ] `tests/test_phase17_stats.py` — created by **T-17-03** (plan 17-01, wave 1); extended by
      **T-17-20** (plan 17-08, wave 4) and **T-17-26** (plan 17-10, wave 6)
- [ ] `tests/test_phase17_personas.py` — created by **T-17-07** (plan 17-03, wave 2); extended by
      **T-17-12** (plan 17-05, wave 3)
- [ ] `tests/test_phase17_scoring.py` — created by **T-17-10** (plan 17-04, wave 2); extended by
      **T-17-15** (plan 17-06, wave 3)
- [ ] `tests/test_phase16_prereg.py` — extended by **T-17-02** (plan 17-01, wave 1)
- [ ] `tests/test_lora_inject.py` — extended by **T-17-05** (plan 17-02, wave 1)
- [ ] `tests/test_phase14_teaching.py` — extended by **T-17-04** (plan 17-02, wave 1)
- [ ] No framework install needed — `pytest 9.0.3` is already in `[dev]` and `.venv` is live

`wave_0_complete` stays `false` until those files exist in the tree.

---

## Task ID Index

| Task ID | Plan | Wave | What it lands |
|---------|------|------|---------------|
| T-17-01 | 17-01 | 1 | Pre-registration block + the four minting filters in `scripts/phase17_personas.py` |
| T-17-02 | 17-01 | 1 | Phase-17 pre-registration ordering guard in `tests/test_phase16_prereg.py` |
| T-17-03 | 17-01 | 1 | `tests/test_phase17_stats.py` — family, gate rule, tie-break, the four static scans |
| T-17-04 | 17-02 | 1 | Additive `seed=` on `train_arm`/`build_arm_bins`, phase-aware `arm_outputs` prefix |
| T-17-05 | 17-02 | 1 | ISO-06 consumer-site AST regression in `tests/test_lora_inject.py` |
| T-17-06 | 17-03 | 2 | The 24 minted values + the transcribed token census |
| T-17-07 | 17-03 | 2 | `tests/test_phase17_personas.py` — census, round-trip, disjointness, composition |
| T-17-08 | 17-04 | 2 | Driver skeleton, `held_out_by_slot`, the cell-blind `score_completion` |
| T-17-09 | 17-04 | 2 | `classify` + `assemble_matrix` — the only code that knows `(i, j)` |
| T-17-10 | 17-04 | 2 | `tests/test_phase17_scoring.py` — cell-blindness, taxonomy, no-op-swap shape confirmation |
| T-17-11 | 17-05 | 3 | `scripts/phase17_persona_gate.py` — the GPU pre-flight |
| T-17-12 | 17-05 | 3 | The blocking verdict tests |
| T-17-13 | 17-06 | 3 | The ISO-04 canary, both layers |
| T-17-14 | 17-06 | 3 | `--train` / `--sweep` / `--report` parser and `run_one_sweep` |
| T-17-15 | 17-06 | 3 | Canary mutation proof + the cross-process guards |
| T-17-16 | 17-07 | 4 | RUN the pre-flight gate; commit the report at PENDING |
| T-17-17 | 17-07 | 4 | **Blocking human GO/ADAPT verdict** |
| T-17-18 | 17-08 | 4 | `run_report_mode` + `compare_cells` — the imported gate |
| T-17-19 | 17-08 | 4 | `render_report` + the D-10 all-fail branch |
| T-17-20 | 17-08 | 4 | `tests/test_phase17_stats.py` extension — unit, bounds, branch, D-21 twin |
| T-17-21 | 17-09 | 5 | RUN — train three adapters at three seeds |
| T-17-22 | 17-09 | 5 | RUN — four sweeps, four fresh processes |
| T-17-23 | 17-09 | 5 | RUN — `--report`, record the verdict |
| T-17-24 | 17-10 | 6 | ISO-05 — select the pair, train four replicate adapters |
| T-17-25 | 17-10 | 6 | ISO-05 — four replicate sweeps, per-seed rates |
| T-17-26 | 17-10 | 6 | ISO-05 addendum appended to the isolation report, zero deletions |

---

## Manual-Only Verifications

| Behavior | Requirement | Task ID | Why Manual | Test Instructions |
|----------|-------------|---------|------------|-------------------|
| Human GO / ADAPT verdict on the minted persona values | ISO-01 | **T-17-17** (plan 17-07, wave 4) | The judgment is semantic proximity on quoted base completions — precisely what exact-match cannot see (Phase 14's own reasoning). Only the **judgment** is manual; its **enforcement** is automated. | Run `scripts/phase17_persona_gate.py` (imported `probe_guessability` + census, never copied), read the quoted base completions in `results/phase17_personas_report.md`, and record GO or ADAPT by hand in its `## Verdict` section. `teach_persona._require_go_verdict` refuses to train on STOP/PENDING. Never auto-approvable. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or a named Wave-0 owner
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references — each test file has an owning task above
- [x] No watch-mode flags
- [x] Feedback latency < 130 s
- [x] Full-suite baseline is **579 passed / 1 skipped** before Wave 0 adds tests — asserted in every
      plan's acceptance criteria as "at or above 579 passed / 1 skipped"
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** task IDs backfilled 2026-08-14; awaiting execution.
