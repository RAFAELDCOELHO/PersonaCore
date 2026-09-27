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
| **Quick run command** | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase32_points.py tests/test_phase32_frontier.py tests/test_phase32_live.py tests/test_phase29_prereg.py tests/test_phase30_points.py tests/test_phase31_budget.py` |
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

Bound to the plan task IDs (revision 1, 2026-09-27). All commands run as `.venv/bin/pytest -q -p no:cacheprovider <args>` from the repo root.

| Task ID | Req ID | Behavior | Test Type | Automated Command | File Exists | Status |
|---------|--------|----------|-----------|-------------------|-------------|--------|
| 32-01-T1 | (D-17) | Guard continuation allows `"control_readings"` only as dict key / subscript; AST-computed natural cases in phase29_prereg / phase23_matched_prereg / phase25_promotion discriminate before/after; planted getattr / Attribute / import stay flagged | unit + AST | `tests/test_phase30_points.py -k ast_guard` | ✅ file | ⬜ |
| 32-01-T2 | ACTRL-01 evidence (D-19, D-10) | WR-04 replay check in `own_control`; IN-04 module check in `recipe_identity` | unit (natural RED) | `tests/test_phase30_points.py -k "wr04 or in04"` | ✅ file | ⬜ |
| 32-01-T3 | (D-19) | `_SUPERSEDED_PINS` continuation; pin tripwire green | unit | `tests/test_phase30_calibration.py::test_the_phase30_points_pin_continuation_is_a_tripwire` | ✅ file | ⬜ |
| 32-02-T1 | AFRONT-01 | D-01 recall override (is_control=True); record field contract; stage seconds; D-03 clock; stop line read, not typed | unit + AST | `tests/test_phase32_points.py -k "measure or record or stage or stop_line or cumulative"` | ❌ W0 | ⬜ |
| 32-02-T2 | AFRONT-01 | D-08 WR-02 session-sha refusal (natural RED); write-once; one-path commit; git-surface AST (D-11) | unit + AST | `tests/test_phase32_points.py -k "wr02 or write_once or commit or git_surface"` | ❌ W0 | ⬜ |
| 32-03-T1 | AFRONT-02 | Verdicts via the frozen route; PREREG-03 and route-refused legs; tallies re-derive; no local gate | unit + AST | `tests/test_phase32_frontier.py -k "build or route or prereg or tallies or ast"` | ❌ W0 | ⬜ |
| 32-03-T2 | AFRONT-02 / AFRONT-03 | `condition_c_vs_v4` (D-13/D-14); templates, k/5 leads k/6 (D-15/D-18); state-branched write-once emit; v4.0 bytes vs `v4.0` tag; committed recompute (strips provenance/calibration/sources; sources re-hashed) | unit | `tests/test_phase32_frontier.py -k "condition_c_vs_v4 or statement or write_once or v4_bytes or recompute or ancestry"` | ❌ W0 | ⬜ |
| 32-04-T1 | AFRONT-01 | Schedule walk, controls first; PREREG-03 leg commits 5 alone; replay per step, mismatch halts before measure (D-07); half-trained refusals; stop line exit 0 + beat; ruling in provenance (D-03..D-06, D-20) | unit (scratch repo) | `tests/test_phase32_points.py -k "replay or half_trained or schedule or refused or stop_line or interrupted or complete"` | ❌ W0 | ⬜ |
| 32-04-T2 | AFRONT-01 | main -> run kwargs signature-bound; plist mirrors canary (plistlib only); no skip / plutil leg (AST gate) | unit + AST | `tests/test_phase32_points.py -k "main or cli or plist or host_gated"` | ❌ W0 | ⬜ |
| 32-05-T1 | AFRONT-01 | D-12 live path through main(): recall on every trained point, replay per step, own_control acceptance, stage clock, provenance, no strays | live fixture | `tests/test_phase32_live.py -k "live_path and not frontier"` | ❌ W0 | ⬜ |
| 32-05-T2 | AFRONT-02 / AFRONT-03 | Real producer records feed `build_frontier` + `admission()` (D-12); tally negative control | live fixture | `tests/test_phase32_live.py -k "frontier or admission"` | ❌ W0 | ⬜ |
| 32-06-T1 | AFRONT-01 | Pre-launch gates on the committed tree; runbook | gates + live fixture | `tests/test_phase32_live.py tests/test_phase32_points.py tests/test_phase32_frontier.py` | ❌ W0 | ⬜ |
| 32-06-T2 | AFRONT-01 | 12-point MPS sweep (developer-launched) | manual | see Manual-Only | — | ⬜ |
| 32-06-T3 | AFRONT-01 | 12 records tracked, single-path, controls first; provenance.device == "mps"; ancestry guards | unit (tracked branch) | `tests/test_phase31_budget.py -k ancestry` | ✅ file | ⬜ |
| 32-07-T1 | AFRONT-02 | Frontier emitted untracked; admission not INCONCLUSIVE; untracked branches green | unit | `tests/test_phase32_frontier.py` | ❌ W0 | ⬜ |
| 32-07-T2 | AFRONT-02 / AFRONT-03 | D-16 developer review | manual | see Manual-Only | — | ⬜ |
| 32-07-T3 | AFRONT-02 / AFRONT-03 | Single-path frontier commit; recompute + ancestry on tracked branches; v4.0 bytes; full suite EXIT=0 | unit + full suite | `tests/test_phase32_frontier.py` then the full-suite command | ❌ W0 | ⬜ |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase32_points.py` — driver units and AST guards (32-02, 32-04)
- [ ] `tests/test_phase32_live.py` — D-12 module-scoped live fixture and the real-producer frontier feed (32-05)
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
