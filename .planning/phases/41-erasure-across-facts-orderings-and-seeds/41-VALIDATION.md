---
phase: 41
slug: erasure-across-facts-orderings-and-seeds
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-10-08
---

# Phase 41 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `41-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8 in `.venv` (Python 3.11), CPU-only |
| **Config file** | `pyproject.toml` (existing) |
| **Quick run command** | `.venv/bin/pytest -q tests/test_phase41_prereg.py tests/test_phase41_floors_prereg.py tests/test_phase41_erasure.py -p no:cacheprovider` |
| **Gate legs** | `.venv/bin/pytest -q tests/test_phase35_prereg.py -k "slot_ordering or slot_census or frozen" tests/test_phase36_caps.py -k owner tests/test_phase37_routes.py -k byte_unchanged tests/test_phase23_resume.py tests/test_phase14_scoring.py -k draw_all tests/test_phase25_driver.py -k os_replace tests/test_lora_inject.py tests/test_phase21_sc5.py` |
| **Full suite command** | `nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` plus a waiter on `^EXIT=` (Bash caps a call at 600 s) |
| **Estimated runtime** | quick ~60 s; full ~53-56 min (4495 passed / 4 skipped at 9a6a5e4) |

---

## Sampling Rate

- **After every task commit:** quick run plus the gate legs touching the edited file
- **After every plan wave:** full suite on a COMMITTED tree, run again after each record commit (new reds appear only once records are tracked)
- **Before `/gsd:verify-work`:** full suite green, plus a full-shape CPU rehearsal (`phase41rh` prefix, tmp root, `device='cpu'`) before any MPS launch
- **Max feedback latency:** quick run ≤ 120 s

---

## Per-Task Verification Map

Filled by the planner per task; the requirement → test map is:

| Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|----------|-----------|-------------------|-------------|--------|
| ERASE-03 | targets iterate `e1_targets()`; no non-docstring str constant equals a target name in scripts/phase41_*.py (AST) | unit | `tests/test_phase41_prereg.py::test_targets_and_seeds_are_read`, `::test_no_target_name_is_typed_in_phase41_scripts`; `tests/test_phase41_erasure.py::test_no_target_name_is_typed_in_the_driver` | ❌ W0 | ⬜ pending |
| ERASE-04 | two orderings; Taylor score identity (Σ B·∂B vs finite difference vs Σ A·∂A); direction and tie-break by address; re-rank points; whole ordering recorded | unit (CPU tiny model) | `tests/test_phase41_prereg.py::test_alternative_ordering_fill`; `tests/test_phase41_erasure.py::test_taylor_scores_identity`, `::test_component_gradients_direction_and_ties`, `::test_gradient_ordering_reranks_at_the_points`, `::test_ordering_recorded` | ❌ W0 | ⬜ pending |
| ERASE-05 | adapter digests from `phase41_adapters`; preflight refuses a mismatch (fake files, never host-gated) | unit | `tests/test_phase41_erasure.py::test_preflight_refuses_adapter_mismatch` | ❌ W0 | ⬜ pending |
| ERASE-06 | floors fill on committed calibration records; fill-input builders; legs (a)/(b)/(c) green on the real repo; planted reds | unit + git-rig | `tests/test_phase41_prereg.py::test_fill_input_builders`; `tests/test_phase41_floors_prereg.py::test_floors_are_computed_from_the_committed_records`; `tests/test_phase35_prereg.py::test_slot_ordering_is_green_on_the_real_repo` | partial | ⬜ pending |
| ERASE-07 | driver stop == `e1_stop` (exhaustive truth table and per cell); rank at every read checkpoint; up to len(GRID) confirmations (D-26); NOT_REACHED sentence verbatim | unit (truth table) | `tests/test_phase41_prereg.py::test_grid_fill`, `::test_driver_stop_equals_e1_stop`, `::test_confirmation_accounting`, `::test_not_reached_sentence`; `tests/test_phase41_erasure.py::test_cell_loop_matches_e1_stop`, `::test_rank_recorded_at_every_read_checkpoint` | ❌ W0 | ⬜ pending |
| ERASE-08 | pin byte-unchanged; driver never calls `_cmd_*`/`report`/`erasure_succeeded` (AST) | git + AST | `tests/test_phase37_routes.py::test_pin_and_gate_are_byte_unchanged`; `tests/test_phase41_erasure.py::test_pin_and_gate_are_byte_unchanged_for_phase41`, `::test_phase41_call_gate` | ✅ / ❌ W0 | ⬜ pending |
| ERASE-09 | band is `mitigation_gate.dialogue_gap_band` of the records; control_gap mismatch on mps stops | unit | `tests/test_phase41_prereg.py::test_condition_c_uses_the_band`, `::test_control_gap_check`; `tests/test_phase41_erasure.py::test_control_gap_mismatch_stops`; `tests/test_phase41_floors_prereg.py::test_bands_are_the_d01_band_of_the_records` | ❌ W0 | ⬜ pending |
| ERASE-10 | per-target 7 non-targets each /27; pre = Phase 40 A2 full of the same seed; verdict truth table; pair labels truth table; D-17 counts | unit | `tests/test_phase41_prereg.py::test_condition_b_per_target`, `::test_cell_verdict_truth_table`, `::test_pair_labels_truth_table`, `::test_summary_counts`; `tests/test_phase41_erasure.py::test_emit_fed_a_real_producer_record` | ❌ W0 | ⬜ pending |
| SC5 | prereg frozen before records; test file first-added before records; RECORDS_AT_COMMIT; write-once | git | `tests/test_phase41_prereg.py::test_phase41_prereg_is_frozen_before_every_phase41_record`, `::test_this_test_file_is_first_added_before_every_phase41_record`, `::test_records_at_commit_is_true_at_the_first_commit`; `tests/test_phase41_erasure.py::test_emit_is_write_once_and_refuses_a_dirty_tree` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase41_prereg.py` — committed in or before the commit that adds `scripts/phase41_prereg.py`, before any phase41 record
- [ ] `tests/test_phase23_resume.py::_TRAIN_ARM_CALL_SITES` — register line for the Phase 41 `train_arm(` call site
- [ ] Tiny CPU GPT+LoRA fixture for the gradient identity tests (no checkpoints → no host-gated skip, CI skip pin unchanged)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| MPS grad-path value == no-grad value (D-02 on MPS) | ERASE-04 | needs the M3 MPS device | launch-gate smoke; non-zero difference stops for Rafael |
| Backward/forward cost ratio fits 417.56 s per cell (D-05) | ERASE-04 | measured in the CPU rehearsal and MPS smoke | rehearsal record asserts it; fallback = static gradient ordering |
| "approved" before each record commit | ERASE-06/10 SC5 | human gate | Rafael writes "approved" |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120 s (quick run)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
