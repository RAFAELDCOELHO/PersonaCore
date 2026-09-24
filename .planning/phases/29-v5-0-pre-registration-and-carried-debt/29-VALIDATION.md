---
phase: 29
slug: v5-0-pre-registration-and-carried-debt
status: draft
nyquist_compliant: false
wave_0_complete: false
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
| PREREG-01 | prereg first-add precedes every tracked v5.0 result | git/unit | `pytest tests/test_phase29_prereg.py -k frozen_before` | ❌ W0 | ⬜ pending |
| PREREG-01 | 12 keys; swap-back equals v4.0 keys; v4.0 parsers refuse `advr_*`; no dupes | unit | `-k keys` | ❌ W0 | ⬜ pending |
| PREREG-01 | paths distinct from `results/phase2*`; probe/calibration paths never parse as keys | unit | `-k paths` | ❌ W0 | ⬜ pending |
| PREREG-01/04 | gate, grid, F_Y imported by reference (`is`); AST guards RED on re-typed copies | unit/AST | `-k "by_reference or ast"` | ❌ W0 | ⬜ pending |
| PREREG-04 | `replay_windows(8)==32`, `(64)==256`, equals the DP expression; torch-free import | unit + subprocess | `-k "replay or without_torch"` | ❌ W0 | ⬜ pending |
| PREREG-03 | floor outside (0,1] ⇒ REFUSED with reading; no retry/alternate key | unit | `-k "unlearnable or refused or retry"` | ❌ W0 | ⬜ pending |
| PREREG-02 | admission branches + precedence; zero admitted ⇒ MOOT limitation | unit | `-k admission` | ❌ W0 | ⬜ pending |
| DEBT-01 | relearn probe under scratch `_ROOT`; `results/phase27_*` untouched | integration | `pytest tests/test_phase27_relearn.py -k untracked_record` | ✅ edit | ⬜ pending |
| DEBT-02 | D-28 note read verbatim at runtime; digest pinned; amended note reddens | unit | `pytest tests/test_phase16_driver.py -k d28` | ✅ add | ⬜ pending |
| DEBT-03 | 11 Phase-17 SUMMARYs validate; `completed` == `--follow` first-add date | git/unit | `pytest tests/test_phase29_prereg.py -k summary_frontmatter` | ❌ W0 | ⬜ pending |
| DEBT-04 | named limitation present; AST census finds no accountant import/call in v5.0 scripts | AST | `-k accountant` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase29_prereg.py` — covers PREREG-01..04, DEBT-03, DEBT-04
- [ ] DEBT-02 tests appended to `tests/test_phase16_driver.py`
- [ ] No framework install needed

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| D-15 promotion ruling (GATE-08 replication route) | PREREG-02 | Developer decision with the import-friction table visible (29-CONTEXT D-15) | Checkpoint task presents the friction table from 29-RESEARCH.md; developer rules; ruling committed before any D-15-dependent code |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
