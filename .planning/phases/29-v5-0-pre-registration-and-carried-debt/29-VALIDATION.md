---
phase: 29
slug: v5-0-pre-registration-and-carried-debt
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-09-24
---

# Phase 29 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `29-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (`.venv/bin/pytest`, Python 3.11 venv — never the host 3.14) |
| **Config file** | `pyproject.toml` (existing) |
| **Quick run command** | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase29_prereg.py` (+ `tests/test_phase27_relearn.py -k untracked_record`, `tests/test_phase16_driver.py -k d28`) |
| **Full suite command** | `nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` + an `until grep -q '^EXIT=' $LOG` waiter |
| **Estimated runtime** | quick < 10 s per file; full ~25 min (Bash caps at 600 s — use the waiter) |

---

## Sampling Rate

- **After every task commit:** Run the targeted file(s) for that task
- **After every plan wave:** Run the full suite on a committed (clean) tree — the clean-tree probes need it
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds (targeted)

---

## Per-Task Verification Map

Task IDs are filled in by the planner; requirement rows are fixed by research.

| Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|----------|-----------|-------------------|-------------|--------|
| PREREG-01 | prereg first-add precedes every tracked v5.0 result | git/unit | `pytest tests/test_phase29_prereg.py -k frozen_before` (Plan 01; 1 passed) | ✅ | ✅ green |
| PREREG-01 | 12 keys; swap-back equals v4.0 keys; v4.0 parsers refuse `advr_*`; no dupes | unit | `pytest tests/test_phase29_prereg.py -k keys` (Plan 01; 8 passed) | ✅ | ✅ green |
| PREREG-01 | paths distinct from `results/phase2*`; probe/calibration paths never parse as keys | unit | `pytest tests/test_phase29_prereg.py -k paths` (Plan 01; 2 passed) | ✅ | ✅ green |
| PREREG-01/04 | gate, grid, F_Y imported by reference (`is`); AST guards RED on re-typed copies | unit/AST | `pytest tests/test_phase29_prereg.py -k "by_reference or ast"` (Plan 01; 5 passed) | ✅ | ✅ green |
| PREREG-04 | `replay_windows(8)==32`, `(64)==256`, equals the DP expression; torch-free import | unit + subprocess | `pytest tests/test_phase29_prereg.py -k "replay or without_torch"` (Plan 01; 3 passed) | ✅ | ✅ green |
| PREREG-03 | floor outside (0,1] ⇒ REFUSED with reading; no retry/alternate key | unit | `pytest tests/test_phase29_prereg.py -k "unlearnable or refused or retry"` (Plan 01; 10 passed) | ✅ | ✅ green |
| PREREG-02 | admission branches + precedence; zero admitted ⇒ MOOT limitation | unit | `pytest tests/test_phase29_prereg.py -k "admission or scope or threshold"` (Plan 04 Task 2; 21 passed) + `-k "d09 or recovery_fixture"` (3 passed) | ✅ | ✅ green |
| DEBT-01 | relearn probe under scratch `_ROOT`; `results/phase27_*` untouched | integration | `pytest tests/test_phase27_relearn.py -k untracked_record` (Plan 02; 1 passed) | ✅ | ✅ green |
| DEBT-02 | D-28 note read verbatim at runtime; digest pinned; amended note reddens | unit | `pytest tests/test_phase16_driver.py -k d28` (Plan 03; 4 passed) | ✅ | ✅ green |
| DEBT-03 | 11 Phase-17 SUMMARYs validate; `completed` == `--follow` first-add date | git/unit | `pytest tests/test_phase29_debt.py -k summary_frontmatter` (Plan 02; 11 passed; the test lives in test_phase29_debt.py) | ✅ | ✅ green |
| DEBT-04 | named limitation present; AST census finds no accountant import/call in v5.0 scripts | AST | `pytest tests/test_phase29_prereg.py -k accountant` (Plan 01; 1 passed) | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_phase29_prereg.py` — covers PREREG-01..04, DEBT-04 (DEBT-03 lives in `tests/test_phase29_debt.py`)
- [x] DEBT-02 tests appended to `tests/test_phase16_driver.py`
- [x] No framework install needed

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| D-15 promotion ruling (GATE-08 replication route) | PREREG-02 | Developer decision with the import-friction table visible (29-CONTEXT D-15) | Checkpoint task presents the friction table from 29-RESEARCH.md; developer rules; ruling committed before any D-15-dependent code |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Targeted evidence (Plan 04, committed tree e44f045, 2026-09-24):** test_phase29_prereg.py 53 passed / 0 skipped; test_phase29_debt.py 12 passed; the census set (test_phase14_scoring, test_phase17_stats, test_phase23_ctrl, test_phase21_unit_continuation, test_phase21_sc5, test_phase20_correction, test_phase25_driver, test_lora_inject together with both phase29 files) 237 passed; the mitigation_gate caller/wall/os.replace censuses 3 passed; ruff check and format --check are clean on the touched files.

**Full suite (orchestrator, committed tree 345b9b3, 2026-09-24):** 2988 passed / 4 skipped / 0 failed in 25:21. The skip count is 4, the same as the wave-1 (2960/4/0 at e160108) and wave-2 (2964/4/0 at fbfd0b8) gate runs.

**Approval:** approved 2026-09-24 (full suite green on the committed tree)
