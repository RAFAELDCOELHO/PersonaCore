---
phase: 31
slug: mps-cost-probes-and-budget-commitment
status: draft
nyquist_compliant: true
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

Filled by the planner, 2026-09-26. Checkpoint tasks (31-04-T2 launch, 31-06-T2 budget review) are human gates, and each is followed by an automated check.

| Task ID | Plan | Wave | Req | Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-----|----------|-----------|-------------------|-------------|--------|
| 31-01-T1 | 01 | 1 | ARCAL-01 | probe key/prefix/sidecars/adapter/checkpoint/draw cache disjoint from all 12 Phase 32 keys; PROBE_KEY not in POINT_KEYS; plan re-keys only key+prefix | unit (CPU) | `.venv/bin/pytest tests/test_phase31_probe.py -k isolation -q` | W0 (created by 31-01) | pending |
| 31-01-T1 | 01 | 1 | ARCAL-01 | on_draw replay bucketing 256/step x 200; lopsided counter-example refused | unit | `.venv/bin/pytest tests/test_phase31_probe.py -k replay_count -q` | W0 | pending |
| 31-01-T1 | 01 | 1 | ARCAL-01 | Phase 25 stage table from committed records; module torch-free (subprocess executes builders) | unit | `.venv/bin/pytest tests/test_phase31_probe.py -k "stage_table or without_torch or build_point_record" -q` | W0 | pending |
| 31-01-T2 | 01 | 1 | ARCAL-01 | live point path end to end at CPU fixture scale; refuses half-trained / uncountable states | integration (CPU) | `.venv/bin/pytest tests/test_phase31_probe.py -k live_path -q` | W0 | pending |
| 31-01-T2 | 01 | 1 | ARCAL-01 | emit write-once, dirty-first, calibration descent, sweep_point false | unit | `.venv/bin/pytest tests/test_phase31_probe.py -k emit_point -q` | W0 | pending |
| 31-02-T1 | 02 | 2 | ARCAL-02 | relearn one arm on the full ladder at CPU fixture scale; csv moved out of results/; start sha chained to committed point record; no admitted-leg calls (AST) | integration (CPU) | `.venv/bin/pytest tests/test_phase31_probe.py -k relearn -q` | W0 | pending |
| 31-02-T2 | 02 | 2 | ARCAL-01/02 | main() run/emit dispatch traced against real signatures; plist mirrors canary agent (D-12) | unit | `.venv/bin/pytest tests/test_phase31_probe.py -k "main or plist" -q` | W0 | pending |
| 31-03-T1 | 03 | 3 | ARCAL-03 | derive(): n64 = probe, n8 scaling, median ratios, spread, branches, stop line, relearning priced not scheduled, reconciliation; torch-free subprocess; real producer records | unit (torch-free) + integration | `.venv/bin/pytest tests/test_phase31_budget.py -k "derive or without_torch or producer" -q` | W0 (created by 31-03) | pending |
| 31-03-T2 | 03 | 3 | ARCAL-03 | emit write-once/dirty-first/refuses after a sweep point; recompute from committed files; budget precedes every phase32 point; probes precede budget; natural-RED non-vacuity | unit + ancestry | `.venv/bin/pytest tests/test_phase31_budget.py -q` | W0 | pending |
| all | 01-03 | 1-3 | all | WR-05 AST guard, train_arm call-site census, venue skip pin unchanged | existing censuses | `.venv/bin/pytest tests/test_phase30_points.py tests/test_phase23_resume.py -q` | yes | pending |
| 31-04-T1/T3 | 04 | 4 | ARCAL-01/02 | pre-launch gates; completed sidecars verified (200 x 256 replay, start sha chain, clean tree) | gate | see 31-04 Task 1/3 verify | n/a | pending |
| 31-05-T1/T2 | 05 | 5 | ARCAL-01/02 | point then relearn records committed alone; flipped guards green | ancestry | `.venv/bin/pytest tests/test_phase29_prereg.py tests/test_phase30_calibration.py tests/test_phase30_points.py tests/test_phase31_probe.py tests/test_phase31_budget.py -q` | yes | pending |
| 31-06-T3 | 06 | 6 | ARCAL-03 | budget committed alone; ancestry + recompute bind on tracked branch; full suite + phase28_report check | ancestry + phase gate | `.venv/bin/pytest tests/test_phase31_budget.py -k "ancestry or recomputes" -q` + full suite | yes | pending |

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
