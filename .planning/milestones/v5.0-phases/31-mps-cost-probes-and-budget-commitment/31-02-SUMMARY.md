---
phase: 31-mps-cost-probes-and-budget-commitment
plan: 02
subsystem: cost-probe
tags: [arcal-02, arcal-01, relearn, probe, launchagent, write-once]
requires:
  - 31-01 point half (point_run_sidecar, calibration_descent, _tracked, emit_point)
  - phase27_relearn.train_relearn_arm / score_rung / shared_train_config (byte-unchanged)
  - phase25_run.draws_path / start_heartbeat / beat / atomic_write_json
provides:
  - scripts/phase31_probe.py relearn half: relearn_train_sidecar, relearn_run_sidecar, relearn_out_dir, relearn_rung_label, relearn_moves, run_relearn_probe, build_relearn_record, emit_relearn, RELEARN_RECORD
  - scripts/phase31_probe.py CLI: build_parser / main (run, emit point|relearn)
  - artifacts/com.personacore.phase31.probe.plist (D-12 LaunchAgent)
  - tests/test_phase31_probe.py module-scoped relearn_probe_run fixture (for plan 03 to import)
affects: [31-03, 31-04, 31-05]
tech-stack:
  added: []
  patterns: [idempotent post-sidecar moves (move / done / refuse), fresh-bracket rung timing with draw-cache remainder, shared emit target + provenance helper]
key-files:
  created: [artifacts/com.personacore.phase31.probe.plist]
  modified: [scripts/phase31_probe.py, tests/test_phase31_probe.py]
decisions:
  - rung split is 60 x sum(draw-cache shape minutes) plus a bracket remainder proved > 0, with no tp.score_arm patching
  - the relearn record's per-rung score_rung readings go under readings.rungs (gates_nothing), outside stages.rungs
  - scripts/phase27_relearn.py is added to PINNED_MODULES, which the point and relearn records share
  - run mode prints phase25_venue.launch_banner() first, so plan 04 can read the launch identity off logs/phase31_probe.out
requirements-completed: []
# Contributes to ARCAL-02 / ARCAL-01; the orchestrator decides requirement ticks at phase close.
metrics:
  duration: ~50 min (about 25 min of it waiting on the census run)
  completed: 2026-09-26
---

# Phase 31 Plan 02: Relearn probe half, CLI and LaunchAgent Summary

`phase31_probe.py run` measures the point probe first. It then relearns one `mitigated` arm, labelled `probe31`, from that probe's own adapter, calling the real `train_relearn_arm` to RELEARN_CAP at DESIGNATED_SEED. It scores every rung at CURVE_K through the real `score_rung`, and each rung gets a fresh bracket split into draw seconds and a remainder. It moves every leftover that `train_relearn_arm` writes outside out_dir into `data/probe31_relearn/`, so the frozen Phase 27 real-tree guard stays green. `emit relearn` writes the write-once `results/phase31_probe_relearn.json`, chained to the committed point record's adapter sha256. All of this is proven at CPU fixture scale.

## Commits

| Task | Gate | Commit | Subject |
|------|------|--------|---------|
| 1 | RED | 7257a73 | test(31-02): add failing relearn live-path, refusal, record and emit tests |
| 1 | GREEN | ad3626d | feat(31-02): run_relearn_probe, pure relearn record builder and chained write-once emit_relearn |
| 2 | RED | 9807ee2 | test(31-02): add failing CLI dispatch and LaunchAgent plist tests |
| 2 | GREEN | 7203969 | feat(31-02): phase31_probe CLI (run / emit point\|relearn) and the D-12 LaunchAgent |

## Verification (committed tree)

- `.venv/bin/pytest tests/test_phase31_probe.py -q` gives **29 passed** in 25 s.
  - The `relearn_probe_run` module fixture takes **7.7 s** of wall-clock.
  - The `point_probe_run` fixture takes 11.8 s.
- The quick run plus Phase 27 is `tests/test_phase31_probe.py test_phase30_points test_phase30_calibration test_phase29_prereg test_phase23_resume test_phase27_relearn`. It gives **199 passed** in 228 s. The PINNED_MODULES tripwire in test_phase27_relearn is green.
- The censuses are `tests/test_lora_inject.py test_phase21_sc5 test_phase25_venue test_phase25_driver`. They give **56 passed** in 20.7 min.
- `plutil -lint artifacts/com.personacore.phase31.probe.plist` printed OK. `phase31_probe.py --help` lists `run` and `emit`.
- `ruff check` and `ruff format --check` are clean on both .py files.
- These printed nothing:
  - `git diff --name-only 399a031 HEAD -- scripts/phase27_relearn.py scripts/phase27_prereg.py scripts/teach_persona.py tests/test_phase27_relearn.py`
  - `find data checkpoints results -name '*probe31*'`
  - `git status --porcelain results`
- Census hygiene:
  - There is no `== 10` substring in tests. I changed one synthetic value to avoid `== 100.0`.
  - There is no `train_arm(` and no `os.replace`, and I also removed that word from a comment.
  - No test is skipped. The plist test uses plistlib, not plutil.
- The live-path evidence shows the real functions ran:
  - `train_relearn_arm` was called once and `score_rung` once per trained rung. The fixture ladder is (1, 2), because phase29_prereg is re-pointed at the Phase 27 harness's patched RUNGS, RELEARN_CAP and CURVE_K.
  - Every rung has `remainder_seconds > 0` and `draw_seconds > 0`.
  - All 4 `relearn_moves()` pairs ended as (src absent, dst present) under the fixture's `data/probe31_relearn/`.
  - The fixture's results/ is empty. data/ has no `persona_relearn_attacker_*` and checkpoints/ has no `phase27_*`.
  - The moved bin's sha256 equals both the train sidecar's and train_relearn_arm's `bin_sha256`.
  - The last heartbeat line is "done".
  - The real probe31 set and the real Phase 27 strays are unchanged.

The real names that `relearn_moves()` resolves live on the repo:

```
results/phase27_relearn_attacker_n64_mitigated_probe31_seed1337/run.csv -> data/probe31_relearn/run.csv
data/persona_relearn_attacker_n64_mitigated_probe31_seed1337_train{,_mask}.bin -> data/probe31_relearn/<same name>
checkpoints/phase27_relearn_attacker_n64_mitigated_probe31_seed1337_latest.pt -> data/probe31_relearn/<same name>
```

The rung draw caches are `data/phase25_probe31_n64_rung{0050..0400}_k16_draws.json`.

## Deviations from Plan

1. **[Plan prose vs code] Rung adapter paths.** `train_relearn_arm` records each rung's `adapter_path` relative to `phase27_relearn._ROOT`, not to `phase31_probe._ROOT`. The train sidecar re-bases each path to probe-relative with `_rel(phase27_relearn._ROOT / path)`, and scoring resolves `_ROOT / path`.
2. **[Test shape] Fixture ladder.** `phase29_prereg` copies RUNGS, RELEARN_CAP and CURVE_K from `phase27_prereg` at import. The Phase 27 harness patches only `phase27_prereg`, so the fixture also re-points the three `phase29_prereg` names. Without that, the full-ladder proof (trained rungs == `phase29_prereg.RUNGS`) would refuse at fixture scale. The start adapter is the harness's own `_ADMITTED[0]` adapter from its forged frontier. The 31-01 point-probe adapter was built on a different tiny base, which `model_from_adapter`'s fingerprint check would refuse.
3. **[Rule 2] Guards added.**
   - The train sidecar's `start_sha256` must equal the point run's adapter sha256 (D-05).
   - Each unscored rung adapter must hash to its trained sha256 before `score_rung` runs.
   - `build_relearn_record` refuses an incomplete run, or scored rungs that are not the ladder.
4. **[Test additions] Extra tests beyond the behaviour list.** `test_relearn_record_proves_the_moved_bin`, `test_emit_relearn_writes_the_chained_record` (a success path through the fixture's real sidecars, with only the tracked point record forged), `test_emit_relearn_is_write_once_on_the_real_path` and `test_main_run_defaults_to_the_shared_heartbeat`.
5. **[Test bug fixes inside the GREEN commit] Two fixes to the Task 1 tests.**
   - Crash case 4 recreates the csv's `results/` parent before moving the csv back. `_finish_relearn_moves` rmdirs that parent.
   - The live-path label check reads K off the run, because `relearn_rung_label` reads CURVE_K at call time.
6. **Refactor.** `emit_point` now shares `_emit_target()` (overwrite refusal, then dirty refusal) and `_write_record()` (calibration and provenance) with `emit_relearn`. Its behaviour is unchanged, and the 31-01 emit tests pass. Nothing in results/ pins `phase31_probe.py` yet.

No fixture-only refusals came up. Nothing on the train or score path was stubbed. The refusal tests replace train_relearn_arm and score_rung with `pytest.fail` only as tripwires.

## For plan 31-04 (launch; this plan did NOT load the agent)

- Plist: `/Users/juliorcoelho/PersonaCore/artifacts/com.personacore.phase31.probe.plist`. The agent runs `/usr/bin/caffeinate -dims /Users/juliorcoelho/PersonaCore/.venv/bin/python /Users/juliorcoelho/PersonaCore/scripts/phase31_probe.py run --heartbeat /Users/juliorcoelho/PersonaCore/data/phase25_heartbeat.jsonl`. Logs go to `logs/phase31_probe.{out,err}`.
- Launch steps:
  1. `cp artifacts/com.personacore.phase31.probe.plist ~/Library/LaunchAgents/`
  2. `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.personacore.phase31.probe.plist`
  3. `launchctl kickstart gui/$(id -u)/com.personacore.phase31.probe`
  4. After the run exits: `launchctl bootout gui/$(id -u)/com.personacore.phase31.probe`
- Pre-launch gates:
  - The tree must be clean for `scripts src results`, because both run halves call `refuse_if_dirty`.
  - `find data checkpoints results -name '*probe31*'` must print nothing, and `data/probe31_relearn/` must be absent. Otherwise the half-trained refusals fire.
  - `phase25_run.disk_precheck` must have its free-space floor.
  - No other MPS job may be running (PERSONACORE_SWEEP_ACTIVE=1 is set).
  - `tests/test_phase27_relearn.py` must be green before and after the run.
- The launch banner is printed first in `logs/phase31_probe.out`. Per memory, the caffeinate child is identified by ppid == driver pid.
- Emits run after the run, from a clean tree. Run `phase31_probe.py emit point`, commit it, then run `phase31_probe.py emit relearn`. The relearn emit reads the point record through `_tracked_json`, so the point record must be committed at HEAD first.
- Resume behaviour:
  - A crash during relearn training is refused on restart. The checkpoint or out_dir exists without the train sidecar; delete them in a reviewed step.
  - A crash mid-rung is refused, naming that rung's draw cache.
  - A crash between the sidecar write and the moves is finished automatically.

## For plan 31-03

- `relearn_probe_run` is a module-scoped fixture that yields `(run, record, evidence)`. The `evidence` keys are `heartbeat_path, root, moves, calls, trained, ladder, start_sha256, strays, phase27_strays`. `run["k"]` is 8 at fixture scale and `run["ladder"]` is `[1, 2]`.
- The relearn record carries:
  - `stages.train.seconds`;
  - `stages.rungs[i]`, with keys `{steps, label, seconds, draw_seconds, shape_minutes, remainder_seconds}`;
  - `arm_seconds`, which is train plus the sum of the rung seconds;
  - `rungs` (the ladder), `k`, `relearn_cap`, `seed`, `start_sha256` and `point_record`, which only the emit adds.
- `_synthetic_relearn_run()` in the test module gives a torch-free synthetic run with the real ladder.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: scripts/phase31_probe.py, tests/test_phase31_probe.py, artifacts/com.personacore.phase31.probe.plist
- FOUND commits: 7257a73, ad3626d, 9807ee2, 7203969
