---
phase: 35
slug: v6-0-pre-registration-and-the-research-it-rests-on
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-10-01
---

# Phase 35 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `35-RESEARCH.md` §"Validation Architecture". It is amended by CONTEXT D-14..D-17: no
> `proposer`/`adopted_by` field exists, so the PREREG-07 row below replaces the research's.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 in the Python 3.11 `.venv` (never the system 3.14) |
| **Config file** | `pyproject.toml` (`testpaths = ["tests"]`, `pythonpath = ["."]`) |
| **Quick run command** | `.venv/bin/pytest -q tests/test_phase35_prereg.py tests/test_phase29_prereg.py -p no:cacheprovider` |
| **Full suite command** | `make test` (~40 min: launch with `nohup` and a `grep '^EXIT='` waiter, because Bash caps at 600 s) |
| **Estimated runtime** | quick ~30 s; full ~2400 s |

---

## Sampling Rate

- **After every task commit:** the quick run command, plus `ruff check . && ruff format --check .`
- **After every plan wave:** the quick run command, plus `.venv/bin/python scripts/phase28_report.py check` and `.venv/bin/python scripts/phase34_report.py check` (both exit 0)
- **Before `/gsd:verify-work`:** full `make test` green on a committed, clean tree, with the skip count equal to the attributed pin (`tests/test_phase25_venue.py`)
- **Max feedback latency:** 60 seconds (quick run)

---

## Per-Requirement Verification Map

Task IDs are assigned by the planner; each task must cite the `-k` selector it turns green.

| Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|----------|-----------|-------------------|-------------|--------|
| PREREG-05 | The prereg's first add precedes every `results/phase36_*`..`phase45_*` (honest-green with zero v6.0 records) | git/ancestry | `pytest tests/test_phase35_prereg.py -k frozen_before -q` | ✅ | ✅ green |
| PREREG-05 | `ARTIFACT_PATHSPECS` is derived from `V6_RESULT_PATHS` and disjoint from the `v5.0` tag's results | unit | `-k pathspecs` | ✅ | ✅ green |
| PREREG-05 | The six closed pins are imported (AST Import nodes) and none is copied (literal census) | AST | `-k pins_imported` | ✅ | ✅ green |
| PREREG-05 | The module imports without torch, phase19_erasure, phase18_extraction, phase26_canary or phase23_run (subprocess probe) | smoke | `-k without_torch` | ✅ | ✅ green |
| PREREG-05 | `seed_list() is phase23_run.SEED_LADDER`, and the AST tuple at the file's first add (`git log --diff-filter=A`, = `5303819`) equals the live one | git+AST | `-k seed_ladder` | ✅ | ✅ green |
| PREREG-05 | `e1_targets()` yields the 13/13 rows of `TARGET_RANKING`; the four names appear in no module `Constant` | unit+AST | `-k e1_targets` | ✅ | ✅ green |
| PREREG-05 | `audit02_cut()` is the min over `results/phase26_canary.json` (== 3.7965357228934966); `e4_runs` is strict `>` | unit | `-k audit02` | ✅ | ✅ green |
| PREREG-05 | R1a: k = `len(ablated_components)` = 78; the 77.6370113463966% re-derives; the margin is read from `phase19_noise_floors.json::margin_at_gate` | unit | `-k r1a` | ✅ | ✅ green |
| PREREG-05 | Slot registry: every slot has its fields, including the 6 from D-15. Census checks (undeclared slot / wrong owner phase / different rule / ordering minus declared input records) are green on the real tree and RED on planted owner files | AST/git | `-k slot` | ✅ | ✅ green |
| PREREG-05 | The E2 `S` rule refuses S > `len(seed_list())` (D-06); the E3 grid rule encodes 4 recipes × σ ∈ {0, 0.5, 1} plus the v4.0-control reuse condition (D-17) | unit | `-k "e2_S or e3_grid"` | ✅ | ✅ green |
| PREREG-06 | Every entry has exactly {value, derivation, kind, source}; `kind` ∈ {derived, preference}; F_Y/F_C are `preference`, bound by `Attribute` to `mitigation_gate` | unit+AST | `-k entries` | ✅ | ✅ green |
| PREREG-07 | No entry carries a `proposer` or `adopted_by` key (D-14); "selected by THE USER, verbatim" is absent from entry values (AST over dict Constants, not docstrings) | unit+AST | `-k no_proposer` | ✅ | ✅ green |
| PREREG-08 | The new test file has zero skip markers (AST); the attributed CI skip pin in `test_phase25_venue.py` is unchanged | AST + full suite | `-k no_skips`; full `make test` | ✅ | ✅ green (no_skips; full suite 4 skipped = last green) |
| PREREG-09 | One-run bound: Appendix D pin `(1000, 100, 75, 1e-4, 0.05)` → 0.673 and the p. 28 pin → 2.675, both within 1e-3; refuses v > r, r > m and bool inputs | unit | `-k one_run` | ✅ | ✅ green |
| PREREG-09 | Basic composition: `curve_total([1.5, 2.25, 0.25], delta=mitigation_unit.DELTA) == (4.0, 3 * 1e-5)`; `SELECTION_ACCOUNTED is False` (Papernot–Steinke hypotheses fail for E3) | unit | `-k composition` | ✅ | ✅ green |
| PREREG-09 | The research note exists and cites `2305.08846v1` (Thm 5.2 / Cor 5.4 / App. D) and `2110.03620v2` (Thm 2 / Thm 6) with pages | doc | `-k research_note` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_phase35_prereg.py`: covers PREREG-05..09; reuses `_assert_frozen_before`, `_git` and the AST helpers from `tests/test_phase29_prereg.py`
- [x] `.planning/research/` PREREG-09 note (D-10): `.planning/research/V6-PREREG-09.md`, first added 8fba327

No framework install is needed.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** signed off 2026-10-01 on the FINAL commit `bbcec95` (re-signed at Rafael's request; the first sign-off at `9dd04eb` was against the suite at `7275ba1`, before the code-review fixes `1e1e1c5` and `3805beb`). Review history: Rafael's corrections `f13ad62`, `d850d0c`; SC1 hand-note `7275ba1`; code review `b2684bc` (1 blocker / 6 warnings / 5 info, all reproduced) fixed in `1e1e1c5`; re-review `0fb5ad2` (4 warnings / 5 info, all reproduced; WR-04 ruled by Rafael, CONTEXT addendum `14a7b7f`) fixed in `3805beb`; short re-review `bbcec95` clean under Rafael's stopping rule (0 blocking, 9 known limitations recorded in `35-REVIEW-FIX.md`).

---

## Tests per selector (collected at `bbcec95`, `tests/test_phase35_prereg.py`, 88 tests, 0 skipped)

| Selector | Tests |
|----------|-------|
| `-k frozen_before` | `test_phase35_prereg_is_frozen_before_every_v6_result` |
| `-k pathspecs` | `test_pathspecs_are_derived_and_cover_results_phase36_to_45`, `test_pathspecs_are_disjoint_from_every_v5_tag_result` |
| `-k pins_imported` | `test_six_closed_pins_imported_never_copied` |
| `-k without_torch` | `test_the_prereg_imports_without_torch` |
| `-k seed_ladder` | `test_seed_ladder_is_unchanged_since_its_first_add`, `test_seed_ladder_starts_with_the_phase19_seeds` |
| `-k e1_targets` | `test_e1_targets_are_the_13_of_13_rows`, `test_e1_targets_pool_to_the_27_question_target_denominator` |
| `-k audit02` | `test_audit02_cut_is_read_from_the_canary_record` |
| `-k r1a` | `test_r1a_assertions_rederive_from_the_erased_record`, `test_r1a_margin_is_the_noise_floor_record_read` |
| `-k slot` | `test_design_slots_return_read_only_copies`, `test_every_slot_input_is_a_v6_path_or_a_v5_record`, `test_slot_budget_halts_above_the_ceiling`, `test_slot_census_is_green_on_the_real_tree`, `test_slot_census_lets_registry_reads_pass`, `test_slot_census_reds_on_planted_owner_files`, `test_slot_census_scans_scripts_recursively`, `test_slot_d04_deferred_slots_stay_with_their_phases`, `test_slot_design_entries_refuse_a_proposer`, `test_slot_e1_condition_b_margin_is_the_core_read`, `test_slot_e1_rules`, `test_slot_e5_e6_set_sizes_and_entry_subset`, `test_slot_fill_dispatches_only_the_declared_rule`, `test_slot_fill_refuses_an_undeclared_or_non_string_slot`, `test_slot_measured_rules_consume_their_inputs`, `test_slot_ordering_every_commit_refuses_the_real_repo`, `test_slot_ordering_is_green_on_the_real_repo`, `test_slot_ordering_reds_on_a_planted_repo`, `test_slot_registry_declares_the_seventeen_slots` |
| `-k e2_S or e3_grid` | `test_e2_S_refuses_more_seeds_than_the_list`, `test_e3_grid_is_four_recipes_by_three_sigmas`, `test_e3_grid_refuses_a_fifth_recipe_without_a_reused_control`, `test_e3_grid_refuses_a_p22_crossing`, `test_e3_grid_reuses_the_v4_control_only_when_byte_identical_to_v5` |
| `-k entries` | `test_a2_corpus_entries_are_the_216_a2_prompts`, `test_entries_bind_f_y_f_c_and_delta_by_attribute`, `test_entries_f_y_f_c_equal_their_v4_tag_values`, `test_entries_have_exactly_the_four_fields`, `test_entries_label_f_y_and_f_c_as_preferences`, `test_entries_refuse_an_unknown_kind_or_missing_field`, `test_slot_design_entries_refuse_a_proposer` |
| `-k no_proposer` | `test_no_proposer_or_adopted_by_in_any_entry` |
| `-k no_skips` | `test_no_skips_in_this_file` |
| `-k one_run` | `test_one_run_closed_form_at_delta_zero`, `test_one_run_p_value_refuses_an_infinite_eps`, `test_one_run_refuses_bad_inputs`, `test_one_run_reproduces_appendix_d_p46`, `test_one_run_reproduces_section7_p28`, `test_one_run_reproduction_holds`, `test_one_run_tolerance_cannot_absorb_a_dropped_delta` |
| `-k composition` | `test_composition_is_basic_and_by_reference`, `test_slot_design_entries_refuse_a_proposer` |
| `-k research_note` | `test_research_note_cites_both_sources_with_pages`, `test_research_note_ordering_reds_on_a_planted_repo`, `test_research_note_precedes_every_prereg_commit` |

---

## Phase Gate Result (final, `bbcec95`)

- Full suite on the committed, clean tree at `bbcec95` (filtered `git status --porcelain` empty; only the harness file `.claude/scheduled_tasks.lock` shown as ` D`): `.venv/bin/pytest -q -p no:cacheprovider` → **3487 passed, 4 skipped, 0 failed** in 2358.13 s (39:18), `EXIT=0`.
- Skip comparison: **4 skipped = the last green run's 4** (v5.0 close, b8b6335: 3311 / 4 / 0; and the first Phase 35 gate at 7275ba1: 3478 / 4 / 0). Phase 35 adds zero skips; `tests/test_phase25_venue.py` has no commit in this phase.
- Passed delta: 3478 → 3487 (+9) is `tests/test_phase35_prereg.py` growing 79 → 88 in the review fixes. Since b8b6335 (+176): 88 are this file; the other 88 (by subtraction) come from the post-v5.0 paper / k* commits between b8b6335 and the phase start 4d49ba5.
- No v6.0 record exists: `git ls-files 'results/phase3[5-9]_*' 'results/phase4[0-5]_*'` and `find results -name 'phase3[5-9]_*' -o -name 'phase4[0-5]_*'` both print nothing, so every Phase 35 commit to `scripts/phase35_prereg.py` precedes every v6.0 record.
- `.venv/bin/python scripts/phase28_report.py check` → exit 0; `.venv/bin/python scripts/phase34_report.py check` → exit 0.
- `ruff check .` / `ruff format --check .` → clean.
