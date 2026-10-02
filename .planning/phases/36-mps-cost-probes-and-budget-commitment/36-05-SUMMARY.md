---
phase: 36-mps-cost-probes-and-budget-commitment
plan: 05
subsystem: v6.0 MPS cost probes (COST-01)
tags: [probe-driver, E2, E3, D-05, D-08, D-19, preflight, W2, W3, W8, WR-01, Pitfall-9, T-36-19..24]
requires:
  - scripts/phase36_probe.py core + E1/E5/E6 (36-03, 36-04): STAGES, RECORD_BUILDERS, run_front, run_all, emit, DrawTimer, silenced, e1_shape, prove_published_adapter
  - scripts/phase25_points.py: point_plan, train_stage, training_sidecar
  - scripts/teach_persona.py: arm_outputs, arm_spec, score_arm, the driver, train (the loop), MAX_STEPS
  - scripts/phase19_erasure.py: TARGET_SLOT, retrain_arm_spec, run_erasure_arm
  - scripts/phase36_ledger.py: read_ledger, open_runs (36-02)
  - scripts/phase36_prereg.py: E3_PROBE_POINT_KEY, ENTRIES e3_probe_steps / e3_max_steps, prove_p22 (36-01)
provides:
  - scripts/phase36_probe.py: E2_ARMS, STRAY_GLOBS, RESULTS_STRAY_GLOB, loop_timer, e3_steps, e3_plan, stage_e3, _e3_stages, train_e2_rep, stage_e2, _e2_stages, front_outputs, preflight (real checks)
  - tests/test_phase23_resume.py: the phase36_probe.py register line + the literal bumped to `8 + 1 + 1 + 1 + 1 + 2 + 1 + 1 + 1 + 1`
  - tests/test_phase36_probe.py: _e3_light, _e2_light, _live_env, _live_run, e3_live, e2_live, _preflight_env, test_main_run_dispatches_every_front, test_main_run_defaults
affects: [36-06 (reads the E2/E3 record shapes below), 36-07 (preflight gates the launch; the run trains E2/E3 on MPS), 36-08]
tech-stack:
  added: []
  patterns: [tp.train swapped by a restoring context manager to split loop from overhead, MAX_STEPS set at runtime and restored in finally, one shared live env applying every front's CPU patches, signature-bound recorders that forward to the real stages]
key-files:
  created: []
  modified:
    - scripts/phase36_probe.py
    - tests/test_phase36_probe.py
    - tests/test_phase23_resume.py
decisions:
  - "stage_e3 checks the stale outputs of BOTH step counts before any training, so a stale T = 800 output cannot cost a finished T = 200 run"
  - "One loop_timer context manager serves E2 and E3 (proves exactly one loop call per training)"
  - "test_main_run_dispatches_every_front forwards to the REAL stages (orchestrator directive) instead of returning planted stage dicts"
  - "preflight's input list adds tp.CONVBASE_BEST, tp.FACTSET_REPORT, tp.DIALOG_TRAIN_MASK and tp.DIALOG_VAL_MASK: the teaching driver refuses without them"
requirements-completed: []
metrics:
  duration: ~50 min
  completed: 2026-10-02
---

# Phase 36 Plan 05: E3 and E2 training fronts, the call-site register, and the real preflight

E3 trains the published v4.0 point `dp_n8_sigma0p500000` twice: at T = 200 with a taught-recall
`score_arm` pass, and at T = 800 with training only. E2 trains the published Phase 19 M2 recipe
twice under `probe36` arm names and runs one K = 48 A2 pass on the first adapter. `preflight` now
checks everything the M3 run needs. The test `main(['run'])` with no `--front` reaches all five
real stages on CPU.

`requirements-completed: []`. This plan contributes to COST-01; the orchestrator and verifier
decide the ticks.

## Tasks

| Task | Commit | What |
|------|--------|------|
| 1 | 61f9ed7 | stage_e3 (+ loop_timer, e3_steps, e3_plan, _e3_stages), E3 light tests, the shared `_live_env`, the e3 CPU live run |
| 2 | 104bbc8 | train_e2_rep + stage_e2 (+ _e2_stages, E2_ARMS), E2 light tests, the e2 CPU live run, the register line + bumped literal in tests/test_phase23_resume.py |
| 3 | cd2abf4 | front_outputs + the real preflight, the preflight tests, test_main_run_dispatches_every_front, test_main_run_defaults |

## Record shapes (as emitted by the CPU live runs)

**E3** (`results/phase36_probe_e3.json`, `repetitions: 2`)
- `stages.t_step_budget`: `{train_seconds, loop_seconds, overhead_seconds, steps, score_seconds, score_draws, score_draws_per_question, score_fixed_seconds, score_draw_seconds[score_draws]}`
- `stages.t_max_steps`: `{train_seconds, loop_seconds, overhead_seconds, steps}`. It has no score field.
- `configuration`: `{point_key: "dp_n8_sigma0p500000", arm: "dp_n8", sigma: 0.5, lr, batch, seed: 1337, steps: [200, 800], scoring_instrument}`
- `train_seconds` is train_stage's `blob["seconds"]`, the same field the v4.0 comparator records. `overhead_seconds = train_seconds - loop_seconds`. `score_draws_per_question = 1 + N_SEEDED_SAMPLES` = 9.

**E2** (`results/phase36_probe_e2.json`, `repetitions: 2`)
- `stages.train_reps`: 2 x `{outer_seconds, loop_seconds, overhead_seconds}`
- `stages.a2_pass`: `{total_seconds, fixed_seconds, draws, draws_per_question (= K), draw_seconds[draws], draw_seconds_spread}`
- `configuration`: `{arm, target_slot, n_facts_real, n_facts_m2, steps, seed, K, questions, full_adapter_derivation}`

Both shapes match what 36-06's plan reads (`36-06-PLAN.md:102-106`, `:164-178`).

## preflight, in order (each a SystemExit with the fix named)

1. `str(phase25_run.device()) == "mps"`
2. `refuse_if_dirty(pathspec=("scripts", "src", "results"), cwd=_GIT_ROOT)`
3. `phase25_run.disk_precheck()`
4. `phase36_ledger.open_runs(phase36_ledger.read_ledger())` is empty. The message names `python scripts/phase36_ledger.py reconcile` as the fix.
5. No stray probe output. Strays are matches of `STRAY_GLOBS` (`data/probe36_*`, `checkpoints/probe36_*`, `data/phase25_probe36_*`, `data/persona_probe36_*`). Exempt are every `sessions_sidecar(f)` and `front_outputs(f)` for each front whose `run_sidecar(f)` exists. Any `results/probe36_*` always refuses.
6. Every input exists: `phase14_recall.ADAPTER_PATH`, `phase14_recall.CONVBASE_SLIM`, `phase19_erasure.RETENTION_BIN`, `PHASE18_CORPUS_PATH`, `PHASE18_ARM_RECORD_PATH`, `tp.CONVBASE_BEST`, `tp.FACTSET_REPORT`, `tp.DIALOG_TRAIN_BIN/MASK`, `tp.DIALOG_VAL_BIN/MASK`, and the three committed JSONs (`results/phase19_collateral_curve.json`, `results/phase19_arm_erased.json`, `results/phase31_probe_point.json`).
7. `prove_published_adapter()`
8. `set(STAGES) == set(RUN_ORDER)`
9. `phase36_prereg.prove_p22(ENTRIES["e3_max_steps"]["value"])`
10. It prints `[phase36_probe] PREFLIGHT OK <sha> fronts=e5,e6,e3,e2,e1` and writes nothing.

The real run on this M3 (the plan's acceptance step; no probe, no training):
- Before the Task 3 commit it refused only on the dirty tree (`M scripts/phase36_probe.py`), and `git status --porcelain` was unchanged.
- After commit cd2abf4 it printed `[phase36_probe] PREFLIGHT OK cd2abf43f854aeaf33463f941a42cf15e4b05807 fronts=e5,e6,e3,e2,e1` (exit 0), and porcelain still showed only the pre-existing ` D .claude/scheduled_tasks.lock`.

## Verification (output as printed)

- The plan's verify set, run once after the final edit (`tests/test_phase36_probe.py`, `test_phase36_prereg.py`, `test_phase36_ledger.py`, `test_phase36_caps.py`, `test_phase35_prereg.py`, `test_phase23_resume.py`, with `-rs`): **327 passed in 162.50s**, 0 skipped. This includes the whole of `tests/test_phase23_resume.py` and `test_production_resume_epsilon_bit_identical` (~104 s).
- Censuses over scripts/ and tests/: **125 passed in 27.98s**. The files were `tests/test_phase21_sc5.py`, `test_lora_inject.py`, `test_phase21_unit_continuation.py` and `test_phase14_scoring.py`, plus `test_phase31_probe.py`. The single tests were `test_phase19_erasure::test_retention_measurement_pins_a_new_call_site_with_no_adapted_precedent`, `test_phase25_driver::test_os_replace_appears_only_in_the_two_phase25_writers`, `test_phase30_calibration::test_descriptive_mix_is_recorded_and_read_by_nothing`, `test_phase20_correction::test_mitigation_point_verdict_has_no_caller_outside_this_module`, `test_phase25_prereg::test_phase25_prereg_does_not_import_the_spent_module`, `test_tokenizer_oracle::test_no_runtime_tiktoken` and `test_phase23_ctrl::test_never_taught_is_trained_once`.
- `ruff check .` printed "All checks passed!". `ruff format --check .` printed "335 files already formatted" (the `make lint` equivalent, run via `.venv/bin/python -m ruff`).
- `grep -rn "train_arm(" --include='*.py' scripts/phase36_probe.py tests/test_phase36_probe.py | wc -l` printed `1`.
- `git diff --quiet HEAD -- scripts/teach_persona.py scripts/phase25_points.py scripts/phase19_erasure.py` and `... scripts/phase19_run.py scripts/phase19_erasure.py scripts/teach_persona.py` both exited 0, so the pinned modules are byte-unchanged.
- The `(?:==|!=)\s*10(?![0-9_])` count is 0 in tests/test_phase36_probe.py and tests/test_phase23_resume.py.
- Live CPU durations: e3_live setup took 10.3 s, e2_live 1.2 s, and test_main_run_dispatches_every_front (all five fronts) 14.5 s.
- tests/test_phase25_venue.py was not run (orchestrator instruction). No probe or training ran on MPS, and `launchctl` was not used.

## Wave-7 M3 run (for 36-07)

- Gate: `.venv/bin/python scripts/phase36_probe.py preflight` (it passes at cd2abf4).
- Launch, from 36-07-PLAN.md:147-148, using the 36-04 plist: `cp artifacts/com.personacore.phase36.probe.plist ~/Library/LaunchAgents/`, then `launchctl load ~/Library/LaunchAgents/com.personacore.phase36.probe.plist` and `launchctl start com.personacore.phase36.probe`. The agent runs `/usr/bin/caffeinate -dims <repo>/.venv/bin/python <repo>/scripts/phase36_probe.py run --heartbeat <repo>/data/v6_mps_heartbeat.jsonl` over all five fronts in RUN_ORDER (e5, e6, e3, e2, e1).
- Rough MPS wall-clock: none of these figures was measured in this plan.
  - 36-07-PLAN.md says "~4-5 h"; 36-RESEARCH.md:491 estimates "~4–6 h".
  - The research breakdown: E1 2 x ~1.15 h; E2 ~0.02 h of training plus a ~0.78 h reading; E3 T = 200 ~3.5 min of training plus ~21 min of recall, T = 800 ~14 min; E5/E6 small.

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 3 - Blocking] The live fixture's replay source was too small for the published M2 recipe**
- Found during: Task 2 (first e2_live run).
- Issue: the `real` arm's spec bakes replay into the bin at its ratio (legacy sizing in `teach_persona._prepend_replay`). The run stopped with `SystemExit: [teach_persona] replay slice short: wanted 9,151 tokens, read 1,025 ids`, because `_e2e_env` writes only 4 windows (1,025 tokens).
- Fix: `_live_env` tiles `_e2e_env`'s own decodable replay ids to 20,000 elements (the `tests/test_phase21_replay_volume.py` REPLAY_SOURCE_ELEMENTS precedent). It is a fixture-only change.
- Commit: 104bbc8.

**2. [Rule 2 - Missing critical check] preflight's input list was incomplete**
- The plan's list omits inputs the teaching driver refuses to run without: `tp.CONVBASE_BEST` (train_arm: "missing ... the frozen conversational base"), `tp.FACTSET_REPORT` (`_require_go_verdict`), and the two masks `tp.DIALOG_TRAIN_MASK` / `tp.DIALOG_VAL_MASK`.
- E2 and E3 would have died at their first training without them, hours into the run (T-36-24). All four were added, and each has a missing-input test.
- On this M3 every input exists; this was measured before writing the check.
- Commit: cd2abf4.

### Plan text vs code / directives

**3. The dispatch test runs the real stages (orchestrator directive).** The plan's `test_main_run_dispatches_every_front` used recorders that return planted stage dicts. The orchestrator required that the end-to-end `main(['run'])` reach all five fronts' live stages. The recorders still bind `(state,)` against each real stage's signature, but they then FORWARD to it, and all five records go through the real emit. The test also checks:
- that each STAGES entry is the real `stage_<front>` before wrapping;
- that `len(sidecars) == len(RUN_ORDER)` and that the ledger has `2 * len(RUN_ORDER)` lines;
- that E6's beside equals the high computed from the E1 sidecar that just ran.

**4. e3_live / e2_live go through `probe.main(["run", ..., "--front", X])`, not `probe.run_all(fronts=(X,))`.** main calls run_all, so this is a superset. Stdout is captured with `redirect_stdout`, as the plan asks (W7a).

**5. The plan's `-k` filters select more than they say.** `-k e3` matches the module name `test_phase36_probe` ("phas**e3**6"). `-k "e2 or inert"` matches `test_phase23_resume` ("phas**e2**3"), so it runs that whole file, including the ~105 s MPS test. The required tests ran either way.

**6. stage_e3 refuses stale outputs for both plans up front.** The plan's text checks each step count just before its own training. This plan does all the checks before any training, so a stale T = 800 output cannot waste a finished T = 200 run.

**7. The old `test_preflight_refuses_an_unregistered_front` (36-03) was replaced.** It called preflight with only STAGES patched, and the real device and input checks now refuse that setup. Its behavior moved to `test_preflight_refuses_an_unregistered_or_extra_front`, which uses the full `_preflight_env`.

**8. The names composed for E2 have a doubled label.** `arm_outputs(arm, prefix=PROBE_PREFIX)` with arm `probe36_m2_a` and the plan's prefix `probe36` gives `checkpoints/probe36_probe36_m2_a_{adapter,latest}.pt` and `results/probe36_probe36_m2_a/run.csv`; the bins are `data/persona_probe36_m2_a_train{,_mask}.bin`. These are the real paths, and they are recorded here so 36-07/08 use them. The csv moves to `data/probe36_e2/<arm>/run.csv`.

## Notes for wave 7 (measured from the code, not deviations)

- train_stage deletes and deterministically rebuilds the UN-prefixed bins `data/persona_dp_n8_train{,_mask,_fact}.bin` before training (`scripts/phase25_points.py:392-397`, `arm_outputs`' documented non-widening). This is the same behavior as every Phase 25 dp_n8 point, and `tests/test_phase23_resume.py` asserts the build is reproducible. The E3 probe therefore rewrites those three real files on the M3.
- train_stage moves E3's csv to `data/phase25_runs/probe36_e3_t{200,800}/run.csv` (`run_log_dir`). No stray glob matches it, so preflight neither exempts it nor refuses it.

## Known Stubs

None.

## Threat Flags

None. The new writes are confined to gitignored data/ and checkpoints/ under probe36 names, and the stray guard covers them. The threat register T-36-19..24 is mitigated as planned, and the tests are named above.

## Self-Check: PASSED

- The commits 61f9ed7, 104bbc8 and cd2abf4 are in `git log`.
- The three modified files are committed.
- preflight printed PREFLIGHT OK after the commit.
