---
phase: 32
slug: replay-bearing-frontier-re-run-and-verdict
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-09-27
---

# Phase 32 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `32-RESEARCH.md` § Validation Architecture (commands measured there).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (`.venv/bin/pytest`, Python 3.11 venv only) |
| **Config file** | `pyproject.toml` / `Makefile` |
| **Quick run command** | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase32_points.py tests/test_phase32_frontier.py tests/test_phase29_prereg.py tests/test_phase30_points.py tests/test_phase31_budget.py` |
| **Census gate (4.5 s)** | the ten-test census command in `32-RESEARCH.md` § Validation Architecture |
| **Full suite command** | `nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` + `until grep -q '^EXIT=' $LOG` waiter (Bash caps at 600 s) |
| **Estimated runtime** | quick ≈ 130 s (32 s + ≈95 s D-12 fixture); full ≈ 25 min |

---

## Sampling Rate

- **After every task commit:** census gate + that task's `-k` subset
- **After every plan wave:** quick run command
- **Before `/gsd:verify-work` and before the MPS launch checkpoint:** full suite green on a committed tree, D-12 live-path test green
- **Max feedback latency:** 130 s (per-task ≤ 30 s)

---

## Per-Task Verification Map

Filled by the planner/executor from the requirement map below; task IDs bind once PLAN.md files exist.

| Req ID | Behavior | Test Type | Automated Command | File Exists | Status |
|--------|----------|-----------|-------------------|-------------|--------|
| AFRONT-01 | Schedule walk skips tracked keys; controls first; PREREG-03 leg writes and commits 5 REFUSED alone | unit (scratch repo) | `pytest tests/test_phase32_points.py -k "schedule or refused"` | ❌ W0 | ⬜ |
| AFRONT-01 | Replay counted per step via on_draw; mismatch halts before measure (D-07) | unit | `pytest tests/test_phase32_points.py -k replay` | ❌ W0 | ⬜ |
| AFRONT-01 | Recall on every point (D-01/D-02) | live fixture | `pytest tests/test_phase32_points.py -k live_path` | ❌ W0 | ⬜ |
| AFRONT-01 | Write-once; one-path commit; git-surface AST (D-11) | unit + AST | `pytest tests/test_phase32_points.py -k "write_once or commit or git_surface"` | ❌ W0 | ⬜ |
| AFRONT-01 | Stop line = Σ committed stage seconds; exit 0 + `stop_line` beat; relaunch refuses without ruling; ruling in provenance; line read not typed (D-03..D-06, D-20) | unit + AST | `pytest tests/test_phase32_points.py -k stop_line` | ❌ W0 | ⬜ |
| AFRONT-01 | WR-02: pinned module changed session-sha→HEAD refuses write (D-08) | unit (natural RED) | `pytest tests/test_phase32_points.py -k wr02` | ❌ W0 | ⬜ |
| AFRONT-01 | Plist mirrors canary (plistlib, no plutil) | unit | `pytest tests/test_phase32_points.py -k plist` | ❌ W0 | ⬜ |
| AFRONT-02 | Verdicts via frozen route; real producer records feed assembler + `admission()` (D-12) | unit + live fixture | `pytest tests/test_phase32_frontier.py` | ❌ W0 | ⬜ |
| AFRONT-02 | Frontier write-once; refuses unless 12 tracked; v4.0 `results/phase25_*..phase28_*` byte-unchanged vs `v4.0` tag | unit | `pytest tests/test_phase32_frontier.py -k "write_once or v4_bytes"` | ❌ W0 | ⬜ |
| AFRONT-03 | `condition_c_vs_v4` block; v4 n8 reasons; v4 n64 "measured, not evaluated"; k/5 + k/6 with k/5 leading (D-13..D-15, D-18); every template state tested | unit | `pytest tests/test_phase32_frontier.py -k "condition_c_vs_v4 or statement"` | ❌ W0 | ⬜ |
| (D-17) | Guard continuation allows `"control_readings"` only as dict key / subscript; natural RED on other forms | unit | `pytest tests/test_phase30_points.py -k "ast_guard or control_readings"` | ✅ file | ⬜ |
| ACTRL-01 evidence (D-19) | WR-04 replay check in `own_control`; `_SUPERSEDED_PINS` continuation green | unit | `pytest tests/test_phase30_points.py -k wr04 tests/test_phase30_calibration.py` | ✅ file | ⬜ |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase32_points.py` — driver units, AST guards, D-12 module-scoped live fixture
- [ ] `tests/test_phase32_frontier.py` — assembler, templates, v4 byte guard
- [ ] `tests/test_phase30_points.py` — D-17 dated guard continuation
- [ ] `tests/test_phase30_calibration.py` — D-19 `_SUPERSEDED_PINS` continuation after the `phase30_points.py` edit

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 12-point MPS sweep runs unattended inside the budget | AFRONT-01 | ~13–23 h on real hardware; LaunchAgent is developer-launched (Phase 31 D-12) | Developer bootstraps the plist, watches heartbeat, boots out; then committed `phase32_point_*` records are checked by the automated guards |
| Frontier D-16 review checkpoint | AFRONT-02/03 | Developer approval before the write-once commit | Emitter prints per-point verdicts, control readings, `condition_c_vs_v4`; developer replies "approved" |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 130 s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
