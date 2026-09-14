---
phase: 27
slug: relearning-attack
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-09-14
---

# Phase 27 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `27-RESEARCH.md` §"Validation Architecture"; the per-task map is filled by the planner from the PLAN.md files.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ~= 9.0 (`pyproject.toml` `[tool.pytest.ini_options] testpaths = ["tests"]`) |
| **Config file** | `pyproject.toml`; `tests/conftest.py` |
| **Quick run command** | `.venv/bin/pytest -q tests/test_phase27_prereg.py tests/test_phase27_relearn.py -x` |
| **Full suite command** | `make test` (= `.venv/bin/pytest -q`) |
| **Estimated runtime** | quick: seconds (the tripwire loads the 22 MB frontier once per module); full: ~1300 s (last full run 2792 passed / 4 skipped / 0 failed in 1297.92 s at `8652c15`; 2802 collected at `ff38d9a`) |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/pytest -q tests/test_phase27_prereg.py tests/test_phase27_relearn.py -x`
- **After every plan wave:** Run `make test` (expect 2802 + this phase's new tests collected, 0 failed)
- **Before `/gsd:verify-work`:** Full suite green AND `tests/test_phase25_close.py`, `tests/test_phase24_record.py`, `tests/test_phase20_correction.py`, `tests/test_phase23_resume.py` explicitly re-run green (frontier at one commit; pin census; `train_arm(` register)
- **Max feedback latency:** 60 seconds for the quick command

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| _(filled by the planner from the PLAN.md task list — one row per task)_ | | | | | | | | | |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### Requirement → test map (from RESEARCH.md; the per-task rows above must point at these)

| Req / Decision | Behavior | Automated assertion | Natural RED state |
|---|---|---|---|
| RELRN-01 / D-01, D-03 | gate MOOT on the committed frontier; ADMITTED only on a PASS copy; INCONCLUSIVE on 43 points / tally mismatch / missing file | `tests/test_phase27_prereg.py::test_the_gate_reads_moot_on_the_committed_frontier`, `::test_the_gate_admits_only_pass`, `::test_partial_or_inconsistent_frontier_is_inconclusive` | 43-point copy reads MOOT |
| D-02 tripwire | 38 reached verdicts re-derive through `phase20_gate_coverage.corrected_point_verdict(**_route_kwargs)`; 6 `adv_n64` refuse | `::test_every_frontier_verdict_re_derives_through_the_route` | edit one `point_taught_recall` in a tmp copy |
| D-02 tally | tally re-derives from 44 `verdict.verdict` strings, `None + early_return_reason → REFUSED` | `::test_the_tally_re_derives_from_the_entries` | `tallies.FAIL = 31` copy → INCONCLUSIVE |
| D-04 ancestry | every tracked `results/phase27_*` first-add descends from every `phase27_prereg.py` commit | `::test_phase27_prereg_is_frozen_before_every_phase27_result` | honest-with-zero until the record is committed |
| D-04 X by reference | `phase27_prereg.X` computed via `mitigation_gate.extraction_ceiling`; no float literal in the module (AST) | `::test_x_is_the_frontier_ceiling_by_call_not_literal` | retyped literal |
| D-06 both-ways pin | `record.frontier_sha256 == sha256(frontier)`; frontier at one commit | `::test_the_record_is_pinned_to_the_frontier_both_ways` | absent record ⇒ assert untracked |
| D-07 / D-33 / D-34 | tallies, tallies_by_leg, cleared (a)=30/(b)=4/(c)=1, 44 rows re-derived | `::test_cleared_abc_re_derive_on_every_row`, `::test_moot_reasons_are_generated_from_counts` | flip one `cleared_a` |
| D-08 / D-37 refusals | each sub-mode exits non-zero naming the verdict unless the committed record reads ADMITTED | `tests/test_phase27_relearn.py::test_each_leg_refuses_unless_admitted[calibrate\|curve\|gate\|structural-proof]` + close-out run on the real record | forged ADMITTED copy ⇒ leg proceeds |
| D-08 write-once | `admit` refuses when record exists / tree dirty | `::test_admit_refuses_to_overwrite`, `::test_admit_refuses_a_dirty_tree` | — |
| D-09 baseline required | `baseline` KEYWORD_ONLY, no default, pinned keys only | `::test_gate_baseline_is_required_and_pinned` | a default sneaks in |
| D-10 e2e | forged ADMITTED record in tmp; tiny GPT + real tokenizer; calibrate → curve → gate through the real train path | `::test_the_live_path_is_wired_end_to_end` | unwired leg raises at first real call |
| D-10 kwargs trace | every kwarg `main()` passes to `run_<leg>()` exists; every required kwarg supplied | `::test_main_passes_only_kwargs_the_legs_accept` | rename one kwarg |
| D-11 / D-36 | `apparatus` block node ids all exist in `pytest --collect-only -q` | `::test_every_apparatus_node_id_exists` | a renamed test |
| D-12 | 5 fresh + 2 control pins equal the source records; seeds `== phase23_run.SEED_LADDER`; on-host adapters hash to the pins | `::test_baselines_are_pinned_from_the_records`, `::test_pinned_seeds_equal_seed_ladder`, `::test_pinned_adapters_hash_on_host` (skipif) | — |
| D-17 / RELRN-05 | zero string intersection scored vs teaching vs A1/A3 vs attacker corpus | `::test_recovery_fixture_is_disjoint` | plant one teaching row |
| D-18 | attacker corpus sha256 re-renders | `::test_attacker_corpus_sha_re_renders` | — |
| D-19 / RELRN-03 | band = `MARGIN_K * noise_floor`; verdict signature has no band/curve parameter | `::test_band_uses_imported_margin_and_noise_floor`, `::test_the_curve_cannot_reach_the_verdict` | — |
| D-21 | rung K == `mitigation_budget.CURVE_K`; Z reading promoted 16 → 48 | `::test_k_is_curve_k_and_promotion_is_the_gates` | — |
| D-23 / D-25 / D-28 | rungs `range(50, 401, 50)`; scored-token count; Z = max(first clears); never-clears ⇒ INCONCLUSIVE | `::test_z_rule_table` | — |
| D-26 (ii) | off-disk `train_config` equal across arms | `::test_off_disk_config_diff_is_empty` | perturb one arm's `max_steps` |
| D-29 / D-30 / D-26 (iii) | `on_draw=None` byte-neutral; recorder covers teaching AND replay draws; sha256 equal by seed+bin, differs by seed | `::test_on_draw_none_is_byte_neutral`, `::test_offset_stream_hash_covers_every_draw`, `::test_offset_stream_differs_by_seed` | — |
| D-35 | every `provenance.module_sha256` recomputed from bytes; all drifted collected | `::test_provenance_digests_match_live_bytes` | one byte edited in a tmp copy |
| D-39 | `pyproject.toml` sha256 unchanged | `::test_pyproject_is_byte_identical` | — |
| Pitfall 4 (existing) | `_TRAIN_ARM_CALL_SITES` register | `tests/test_phase23_resume.py::test_resume_from_none_is_inert` | RED until registered |
| Pitfall 1 (existing) | no `mitigation_point_verdict` caller in `scripts/` | `tests/test_phase20_correction.py::test_mitigation_point_verdict_has_no_caller_outside_this_module` | — |

---

## Wave 0 Requirements

- [ ] `tests/test_phase27_prereg.py` — D-01..D-07, D-12, D-19, D-21, D-23..D-28 (pure + git)
- [ ] `tests/test_phase27_relearn.py` — D-08..D-11, D-17, D-18, D-26, D-29, D-30, D-35, D-36, D-39
- [ ] `tests/test_phase23_resume.py::_TRAIN_ARM_CALL_SITES` — append any new `train_arm(` hits (or none, under OQ1 option B)
- Framework install: none — existing pytest infrastructure covers all phase requirements.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| The operator commits `results/phase27_admission.json` by hand (D-15) | RELRN-01 | the driver never touches git; the commit is a human action | run `admit` once on a clean tree, `git add results/phase27_admission.json`, commit; then the ancestry + both-ways tests go from honest-with-zero to real |
| Each attack sub-mode refuses on the REAL committed record (D-37) | RELRN-01 / D-08 | the CPU tests watch refusals on copies; the real record's refusal is captured once at close | invoke `calibrate`, `curve`, `gate`, `structural-proof` once each; paste stderr into the close-out SUMMARY |
| On-host adapter sha256 pins (D-12) | RELRN-02 | the adapters are gitignored and exist only on the sweep host | run `tests/test_phase27_prereg.py::test_pinned_adapters_hash_on_host` on the host (skips elsewhere) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
