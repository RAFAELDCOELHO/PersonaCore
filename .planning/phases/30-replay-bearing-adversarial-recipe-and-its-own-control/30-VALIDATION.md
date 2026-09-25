---
phase: 30
slug: replay-bearing-adversarial-recipe-and-its-own-control
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-09-25
---

# Phase 30 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `30-RESEARCH.md` §Validation Architecture (measured at HEAD 6e97013).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x in `.venv` (Python 3.11) |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_phase30_seam.py tests/test_phase30_calibration.py tests/test_phase30_points.py` |
| **Guard set** | `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_phase22_wiring.py tests/test_phase23_matched_prereg.py "tests/test_phase23_resume.py::test_resume_from_none_is_inert" tests/test_loop_penalty_fn.py tests/test_phase21_aligned_bins.py tests/test_phase24_bins.py tests/test_phase24_band.py tests/test_phase24_refusal.py tests/test_phase14_teaching.py tests/test_phase29_prereg.py tests/test_phase22_dpsgd.py tests/test_masked_train_seam.py tests/test_phase25_points.py` |
| **Full suite command** | `nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` + `until grep -q '^EXIT=' $LOG` waiter (committed tree only) |
| **Estimated runtime** | quick < 30 s; guard set ~40 s; full ~25 min |

---

## Sampling Rate

- **After every task commit:** quick run + guard set
- **After every plan wave:** full suite (nohup + waiter), committed tree
- **Before `/gsd:verify-work`:** full suite must be green
- **Max feedback latency:** ~70 s per task

---

## Per-Task Verification Map

| Req / SC | Behavior | Test Type | Automated Command | File Exists | Status |
|----------|----------|-----------|-------------------|-------------|--------|
| ARECIPE-01 / SC1 (D-04) | `advr_n8` and `advr_n64` draw exactly `replay_windows(n)` replay windows per step, > 0, measured via `on_draw` | e2e CPU | `pytest tests/test_phase30_seam.py -k draws -x` | ❌ W0 | ⬜ pending |
| ARECIPE-01 / SC1 (D-03) | `train()`/`TrainConfig` kwargs for dp_n8, dp_n64, adv_n8, adv_n64 equal pre-split fixture | e2e CPU spy | `pytest tests/test_phase30_seam.py -k presplit` | ❌ W0 | ⬜ pending |
| ARECIPE-01 / SC1 | golden trajectory + bins unchanged | existing, unmodified | `pytest tests/test_loop_penalty_fn.py tests/test_masked_train_seam.py tests/test_phase22_dpsgd.py tests/test_phase21_aligned_bins.py tests/test_phase24_bins.py` | ✅ | ⬜ pending |
| ARECIPE-01 | frozen matched census still passes | existing, unmodified | `pytest tests/test_phase23_matched_prereg.py` | ✅ | ⬜ pending |
| ARECIPE-01 | `REPLAY_ARMS == phase29_prereg.ADVR_ARMS`; arm_spec parity; CLI refuses advr_*; replay-source guard before bins | unit | `pytest tests/test_phase30_seam.py -k "arms or cli or replay_source"` | ❌ W0 | ⬜ pending |
| ARECIPE-02 / SC2 | live re-derivation gives L == imported floor; four inputs re-measured; advr/adv bin sha equality | unit | `pytest tests/test_phase30_calibration.py -k derivation` | ❌ W0 | ⬜ pending |
| ARECIPE-02 (D-08) | perturbed input → SystemExit, nothing written | unit | `pytest tests/test_phase30_calibration.py -k refuses_if_not_15` | ❌ W0 | ⬜ pending |
| ARECIPE-02 / SC2 | scoring refuses a point whose recipe differs (each field perturbed) | unit | `pytest tests/test_phase30_calibration.py -k recipe_mismatch` | ❌ W0 | ⬜ pending |
| ARECIPE-02 (D-11) | calibration first-add precedes every phase31_/phase32_ result first-add | git ancestry | `pytest tests/test_phase30_calibration.py -k ancestry` | ❌ W0 | ⬜ pending |
| ARECIPE-02 | write-once + dirty-tree refusal on emitter; emitter ancestry-frozen | unit | `pytest tests/test_phase30_calibration.py -k "write_once or dirty or frozen"` | ❌ W0 | ⬜ pending |
| ACTRL-01 / SC3 (D-15/16) | reader refuses dp key; relabelled dp_n8 record; non-advr path; recipe divergence; untracked control | unit | `pytest tests/test_phase30_points.py -k wr05` | ❌ W0 | ⬜ pending |
| ACTRL-01 (D-14) | AST guard: no control_key_for / transitive carriers / dp key construction in v5.0 modules; planted RED per class | AST | `pytest tests/test_phase30_points.py -k ast_guard` | ❌ W0 | ⬜ pending |
| ACTRL-02 / SC4 (D-18) | `SWEEP_SCHEDULE()` permutation of `POINT_KEYS()`; both controls first; planted reorder reddens | unit | `pytest tests/test_phase30_points.py -k schedule` | ❌ W0 | ⬜ pending |
| ACTRL-02 (D-19) | driver refuses non-control key w/o tracked control; unlearnable control → REFUSED records, no training | unit | `pytest tests/test_phase30_points.py -k guard` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/fixtures/phase30_train_kwargs_presplit.json` — captured at pre-split HEAD, BEFORE the seam split commit
- [ ] `tests/test_phase30_seam.py`, `tests/test_phase30_calibration.py`, `tests/test_phase30_points.py`
- [ ] Register new `train_arm(` call in `tests/test_phase23_resume.py::_TRAIN_ARM_CALL_SITES`; bump the pinned literal with reason
- [ ] Narrow `tests/test_phase22_wiring.py::test_non_dp_arm_cli_is_unchanged` to exclude `REPLAY_ARMS` with a dated note (A2 — approved by developer 2026-09-25)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Commit `results/phase30_calibration.json` from a clean tree | ARECIPE-02 | emitter refuses dirty tree; record must be emitted after all code is committed | run the calibration emitter on a clean committed tree, commit the JSON alone, re-run the ancestry test |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 70s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
