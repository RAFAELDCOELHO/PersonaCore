---
phase: 31
slug: mps-cost-probes-and-budget-commitment
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-09-26
---

# Phase 31 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `31-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options] testpaths=["tests"]`) |
| **Quick run command** | `.venv/bin/pytest tests/test_phase31_probe.py tests/test_phase31_budget.py tests/test_phase30_points.py tests/test_phase30_calibration.py tests/test_phase29_prereg.py tests/test_phase23_resume.py -q -p no:cacheprovider` |
| **Full suite command** | `nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` plus an `until grep -q '^EXIT=' "$LOG"` waiter (Bash tool caps at 600 s) |
| **Estimated runtime** | quick ~60–120 s; full ~25 min |

---

## Sampling Rate

- **After every task commit:** Run the quick run command
- **After every plan wave:** Run the full suite on a COMMITTED tree with no probe run in progress (MPS contention + clean-tree probes)
- **Before `/gsd:verify-work`:** Full suite green; `phase28_report.py check` green
- **Max feedback latency:** 120 seconds (quick run)

---

## Per-Task Verification Map

Filled by the planner; task IDs assigned when PLAN.md files exist.

| Req | Behavior | Test Type | Automated Command | File Exists | Status |
|-----|----------|-----------|-------------------|-------------|--------|
| ARCAL-01 | probe key/prefix/sidecars/adapter/checkpoint/draw cache disjoint from all 12 Phase 32 keys; PROBE_KEY ∉ POINT_KEYS | unit (CPU) | `pytest tests/test_phase31_probe.py -k isolation` | ❌ W0 | ⬜ pending |
| ARCAL-01 | on_draw replay bucketing (256/step × 200); lopsided counter-example fails | unit | `pytest tests/test_phase31_probe.py -k replay_count` | ❌ W0 | ⬜ pending |
| ARCAL-01 | live path wired end to end at CPU fixture scale; `main()` kwargs traced | integration (CPU) | `pytest tests/test_phase31_probe.py -k live_path` | ❌ W0 | ⬜ pending |
| ARCAL-01 | emit refuses overwrite, then dirty tree; record carries `sweep_point: false`, per-stage seconds, provenance | unit | `pytest tests/test_phase31_probe.py -k emit` | ❌ W0 | ⬜ pending |
| ARCAL-02 | relearn path wired on CPU fixture; csv moved out of `results/`; start sha = point-probe adapter sha | integration (CPU) | `pytest tests/test_phase31_probe.py -k relearn` | ❌ W0 | ⬜ pending |
| ARCAL-03 | budget recomputes from committed files; both D-12 branches; stop line; relearning scheduled = 0 | unit (torch-free) | `pytest tests/test_phase31_budget.py -q` | ❌ W0 | ⬜ pending |
| ARCAL-03 | budget precedes every `results/phase32_point_*.json`; probes precede budget; natural-RED non-vacuity | ancestry | `pytest tests/test_phase31_budget.py -k ancestry` | ❌ W0 | ⬜ pending |
| all | WR-05 AST guard, `train_arm(` census, venue skip pin unchanged | existing censuses | `pytest tests/test_phase30_points.py tests/test_phase23_resume.py -q` | ✅ | ⬜ pending |
| D-12 | LaunchAgent plist mirrors the canary agent | unit | `pytest tests/test_phase31_probe.py -k plist` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase31_probe.py` — isolation guard, on_draw bucketing, CPU live-path wiring (point + relearn), emit refusals, plist mirror
- [ ] `tests/test_phase31_budget.py` — recompute, branches, stop line, ancestry (reuse `_assert_frozen_before`, `_git` from `tests/test_phase29_prereg.py`)
- No framework install needed

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Replay-bearing adversarial point measured end to end on MPS | ARCAL-01 | Multi-hour MPS run under LaunchAgent | Load the probe LaunchAgent; wait for exit; emit + commit the point probe record |
| Relearning leg measured on a real trained adapter on MPS | ARCAL-02 | ~8.5–11.5 h MPS run (estimate, [ASSUMED]) | Same LaunchAgent run; emit + commit the relearn probe record |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
