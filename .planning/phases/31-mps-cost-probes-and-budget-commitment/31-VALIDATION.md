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
| **Quick run, waves 1-2** | the same command minus `tests/test_phase31_budget.py`, which plan 03 creates (pytest exits 4 on a missing path) |
| **Full suite command** | `nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` plus an `until grep -q '^EXIT=' "$LOG"` waiter (Bash tool caps at 600 s) |
| **Estimated runtime** | quick ~60–120 s target, including the module-scoped CPU live-path fixtures (`point_probe_run`, `relearn_probe_run`) that run once per module; the real figure is measured and recorded by the 31-01/31-02 SUMMARYs; full ~25 min |

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
| 31-01-T2 | 01 | 1 | ARCAL-01 | live point path end to end at CPU fixture scale through the REAL train_stage/measure_stage/draw_point_shapes/score_point (no stage recorder; probe_plan computed on real modules, fixture overrides only pinned composed_steps; RETENTION_BIN redirected to a fixture bin); real-tree probe31 set unchanged across the fixture (never asserted empty: plan 04 leaves real artifacts); refuses half-trained / uncountable states with every path redirected; heartbeat ends on "done" | integration (CPU, module-scoped fixture) | `.venv/bin/pytest tests/test_phase31_probe.py -k live_path -q` | W0 | pending |
| 31-01-T2 | 01 | 1 | ARCAL-01 | emit write-once, dirty-first, calibration descent, sweep_point false | unit | `.venv/bin/pytest tests/test_phase31_probe.py -k emit_point -q` | W0 | pending |
| 31-02-T1 | 02 | 2 | ARCAL-02 | relearn one arm on the full ladder at CPU fixture scale; every rung remainder > 0 and mid-rung resume refused; csv moved out of results/; start sha chained to the point record (both branches on a forged tracked list, sidecars under a redirected _ROOT); real-tree probe31 set unchanged; no admitted-leg calls (AST) | integration (CPU, module-scoped fixture) | `.venv/bin/pytest tests/test_phase31_probe.py -k relearn -q` | W0 | pending |
| 31-02-T2 | 02 | 2 | ARCAL-01/02 | main() run/emit dispatch traced against real signatures; plist mirrors canary agent (D-12) | unit | `.venv/bin/pytest tests/test_phase31_probe.py -k "main or plist" -q` | W0 | pending |
| 31-03-T1 | 03 | 3 | ARCAL-03 | derive(): n64 = probe, n8 scaling, median ratios, spread, branches, stop line, relearning priced not scheduled (conditional includes the FULL_K run_gate re-score upper bound), reconciliation; torch-free subprocess; real producer records via the imported module-scoped fixtures | unit (torch-free) + integration | `.venv/bin/pytest tests/test_phase31_budget.py -k "derive or without_torch or producer" -q` | W0 (created by 31-03) | pending |
| 31-03-T2 | 03 | 3 | ARCAL-03 | emit write-once/dirty-first/refuses after a sweep point (emit's require_no_sweep_point, never build_record); recompute from committed files minus {provenance, calibration}, valid after Phase 32 commits; untracked-probe refusals on forged lists; budget precedes every phase32 point; probes precede budget; natural-RED non-vacuity | unit + ancestry | `.venv/bin/pytest tests/test_phase31_budget.py -q` | W0 | pending |
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

## Plan-Check Findings Log

Origin = where the defect was introduced. Iteration 1 found 4 blockers + 4 warnings, all pre-existing at the initial plan commit fe7f0e8 (none revision-introduced; this was the first check). Iteration 2 found 2 blockers + 4 warnings; one blocker and one warning were introduced by the iteration-1 revision 809a1a5, the rest were pre-existing at fe7f0e8. The iteration-2 revision swept all six plans for tests that read real tree / git state and would flip after plan 04's run or plans 05/06's commits (3 self-found).

| Iter | Sev | Plan | Finding | Origin | Resolution |
|------|-----|------|---------|--------|------------|
| 1 | blocker | 31-01 T2 | live-path fixture infeasible (recipe_identity MAX_STEPS proof, composed_steps pin 2 vs 200, gitignored RETENTION_BIN, Phase 27 LOCKED_FACTS patch) + recorder escape hatch | fe7f0e8 | probe_plan on real modules first; override only pinned composed_steps; RETENTION_BIN -> fixture bin; named Phase 27 patches only; recorders forbidden |
| 1 | blocker | 31-03 T1 | FULL_K re-score priced 0 under the wrong promotion | fe7f0e8 (RESEARCH Q2) | priced per admitted point as an upper bound in conditional |
| 1 | blocker | 31-03 T2 | recompute test went red at Phase 32's first point | fe7f0e8 | sweep-point refusal moved to emit's require_no_sweep_point |
| 1 | blocker | RESEARCH | Open Questions lacked (RESOLVED) | fe7f0e8 | retitled, each Q points at its lock |
| 1 | warning | 31-01/02 | resumed stages/rungs understate brackets | fe7f0e8 | point: reused flags + outer null; relearn: mid-rung resume refused, remainder > 0 proved |
| 1 | warning | 31-02 T1 | emit_relearn tracked branch flips after 31-05 | fe7f0e8 | both branches via forged phase31_probe._tracked |
| 1 | warning | 31-01 | function-scoped CPU fixtures blow quick-run latency | fe7f0e8 | module-scoped point_probe_run / relearn_probe_run, imported by the budget tests |
| 1 | self-found | 31-02 T1 | "if relearn_run_sidecar() exists, return it" contradicted the in-progress rung resume (surfaced while adding the mid-rung refusal) | fe7f0e8 | return only a sidecar marked complete |
| 1 | warning | 31-04 T2 | final "done" beat raced the periodic beat | fe7f0e8 (31-01/31-02 run functions) | state stage "done" set before the stop event in both run functions |
| 2 | blocker | 31-01 T2 | live-path test asserted the REAL tree has no *probe31* file; plan 04's run leaves undeletable data/checkpoints probe31 artifacts, so it went red in 31-05, 31-06 and the phase gate | 809a1a5 (iter-1 revision) | before/after `_real_probe31_strays()` snapshot (modeled on test_phase27_relearn.py::_real_tree_strays) asserted UNCHANGED; `find` kept only as a plan 01/02 execution-time acceptance check |
| 2 | blocker | 31-03 T2 | recompute test compared minus provenance only, but emit() adds a calibration block; tracked branch red right after 31-06's commit | fe7f0e8 | compare minus {provenance, calibration}; emit adds both, build_record neither; 31-06 interfaces block list updated |
| 2 | warning | 31-01 T2 | light refusal tests: plan computed after tp._REPO_ROOT patch (relative_to ValueError); device() unpinned | 809a1a5 | real_plan computed first on unpatched modules; phase25_run._DEVICE = "cpu" in the light setup |
| 2 | warning | 31-01/31-02 | sidecar-dependent tests had no _ROOT redirect and flip once plan 04 writes real sidecars | fe7f0e8 | emit_point dirty-first (empty tmp _ROOT), calibration descent (fixture root), relearn without-point / mid-rung / half-trained / emit-chain tests all redirect _ROOT (+ DRAWS_DIR, tp._REPO_ROOT where read) |
| 2 | warning | 31-01/31-02 | quick-run acceptance included tests/test_phase31_budget.py before plan 03 creates it | fe7f0e8 | plans 01/02 accept the quick run minus that file; VALIDATION infrastructure row added |
| 2 | warning | 31-02/31-03 | relearn out_dir refusal blocked every post-training restart; budget relearn-untracked branch refused on POINT's missing HEAD blob | fe7f0e8 | refusal is (out_dir or checkpoint) AND no train sidecar, with a passing third case; relearn branch patches _tracked_json for POINT and forges lists from real tracked minus the probe |
| 2 | self-found | 31-02 T1 | relearn live-path fixture carried no real-tree assertion at all, and its phase31_probe._ROOT redirect was implied, not stated (the Phase 27 harness does not redirect it) | fe7f0e8 | same unchanged-snapshot as the point fixture; explicit phase31_probe._ROOT = root |
| 2 | self-found | 31-03 T2 | no refuse_if_dirty recorder specified for test_phase31_budget.py, so emit tests ran the real dirty check; 31-06 T1 runs the file with an untracked results/phase31_budget.json, where the sweep-point test would pass vacuously on the dirty refusal | fe7f0e8 | autouse recorder on phase31_budget.refuse_if_dirty |
| 2 | self-found | 31-03 T2 | untracked-probe POINT branch used an unspecified tracked list; the real list flips after 31-05 | fe7f0e8 | forged = real tracked minus the probe path |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
