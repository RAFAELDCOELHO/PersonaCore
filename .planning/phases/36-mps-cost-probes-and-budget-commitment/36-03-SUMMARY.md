---
phase: 36-mps-cost-probes-and-budget-commitment
plan: 03
subsystem: v6.0 MPS cost probes (COST-01)
tags: [probe-driver, E1, R1b, D-01, D-11, D-12, D-16, D-18, WR-02, B1, W4, W9, W10, torch-free]
requires:
  - scripts/phase36_prereg.py (36-01, frozen): PROBE_FRONTS, PROBE_RECORDS, probe_record
  - scripts/phase36_ledger.py (36-02): run_id, append, read_ledger, reconcile, HEARTBEAT_PATH, LEDGER_PATH
  - scripts/phase36_caps.py (36-02): tracked_files
  - scripts/phase30_points.py: _tracked_json
  - scripts/phase19_erasure.py: run_erasure_arm, PHASE18_ARM_RECORD_PATH, TARGET_SLOT
  - scripts/phase14_recall.py: _complete, draw_all, ADAPTER_PATH, SEED
provides:
  - scripts/phase36_probe.py (core + E1 front)
  - tests/test_phase36_probe.py (core tests, E1 pure/light tests, e1_live CPU fixture)
affects: [36-04 (e5/e6 + plist + preflight), 36-05 (e3/e2), 36-06 (budget reads the emitted records), 36-07 (the MPS run + emit-all)]
tech-stack:
  added: []
  patterns: [run/emit split with write-once records, runtime monkeypatch timer on the pin's _complete, stdout redirected into a dropped buffer, dict-backed _path_state for resumable commits]
key-files:
  created:
    - scripts/phase36_probe.py
    - tests/test_phase36_probe.py
  modified: []
decisions:
  - "A stage returns {configuration, <its numbers>, reused: {front: bool}}; run_front pops reused to the sidecar's top level and stores the rest as run['stages']"
  - "RECORD_BUILDERS[front](run['stages']) -> (record stages, repetitions) is the per-front builder registry, beside STAGES"
  - "The E1 record nests the two runs under stages.runs, so the 36-01 comparator field 'runs[*].total_seconds' resolves under record['stages']"
  - "The e1_live fixture launches through main(['run', ...]), not run_all, so the CLI -> run_all -> run_front -> stage_e1 path is exercised end to end"
requirements-completed: []
metrics:
  duration: ~40 min
  completed: 2026-10-02
---

# Phase 36 Plan 03: Probe driver core and the E1 front Summary

This plan adds the Phase 36 probe driver, `scripts/phase36_probe.py`, with its core and the E1 front. E1 also prices R1b.

- **Run.** `run` executes the pin itself, `phase19_erasure.run_erasure_arm("erased", ...)`, twice at K = 48. A runtime timer wraps `phase14_recall._complete`, and every pin call runs silenced. Only seconds and token counts are kept, per draw.
- **Emit.** `emit` writes a write-once record that has passed the D-01 reading gate. It checks WR-02 and carries provenance.
- **Emit-all.** `emit-all` commits the ledger first and then each record, one path per commit. It can resume after an abort.

`requirements-completed: []`: this plan contributes to COST-01. The orchestrator or verifier decides the ticks.

## Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Driver core: isolation, reading gate, silencer, DrawTimer, run_front + ledger/heartbeat, emit/WR-02, commit_path, resumable emit_all, CLI | 5ba38bb | scripts/phase36_probe.py, tests/test_phase36_probe.py |
| 2 | stage_e1 + E1 record: two K = 48 pin runs, per-draw timing, K = 16 prefix, separate fixed costs, Phase 31 beside | 30004e3 | scripts/phase36_probe.py, tests/test_phase36_probe.py |
| 3 | E1 CPU live path: main -> run_all -> run_front -> stage_e1 through a signature-bound pin stand-in, then the real emit | 212e775 | tests/test_phase36_probe.py |

## Verification (real output)

- `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_phase36_probe.py -rs` printed `58 passed in 3.59s`, with no skips.
- The plan's verification set, `tests/test_phase36_probe.py tests/test_phase36_prereg.py tests/test_phase36_ledger.py tests/test_phase36_caps.py tests/test_phase35_prereg.py tests/test_phase23_resume.py`, printed `251 passed in 149.84s (0:02:29)`.
- Task 1 acceptance:
  - `-k "not live"` printed `40 passed`.
  - The torch-free import probe printed `False`.
  - `tests/test_phase23_resume.py -k inert` printed `1 passed, 8 deselected`.
  - `tests/test_phase35_prereg.py tests/test_phase36_prereg.py -k census` printed `5 passed, 100 deselected`.
  - `grep -c "train_arm("` returns 0 for both files.
- Task 2 acceptance: `-k "e1 and not live"` printed `10 passed, 41 deselected`. The two AST tests check two things:
  - `test_e1_pin_payload_is_never_bound`: the single `run_erasure_arm` Call sits directly under an `ast.Expr`.
  - `test_e1_pin_call_runs_inside_silenced`: that Call is lexically inside a `with` whose items include `silenced()` and `DrawTimer()`.
- Task 3: `-k live` printed `7 passed, 51 deselected`. I ran one fixture by hand to look at real values:
  - Each run made 12 real `_complete` calls, each producing 4 tokens (all at the 4-token cap).
  - Per-draw seconds were about 0.0011–0.0022, with `fixed_seconds` 0.0078 out of a `total_seconds` of 0.0288.
  - The captured stdout was `'[phase25_launch] pid=... \n[phase36_probe] e1 0.1 s\n'`. The stand-in's printed reading did not appear in it.
- Repo-wide scans over scripts/ and tests/, run together, printed `286 passed in 30.57s`. The files were: test_phase14_scoring, test_phase17_stats, test_phase21_unit_continuation, test_phase23_ctrl, test_phase30_calibration, test_tokenizer_oracle, test_lora_inject, test_phase21_sc5, test_phase20_correction, test_phase20_prereg, test_phase25_record (os.replace), test_phase22_dpsgd_ast, test_phase25_driver and test_phase23_resume_prereg.
  - I did not run `tests/test_phase25_venue.py`: it spawns the full inner suite (`pytest tests/ --ignore=tests/test_phase25_venue.py`), so I stopped it, as the rules require. The orchestrator owns that run.
  - The new test file has no `skipif`, `pytest.skip` or `importorskip` call. The word "skipif" appears only in one comment, and the venue pin counts runtime skips, not text.
- `ruff check .` printed `All checks passed!`, and `ruff format --check .` printed `335 files already formatted`. Together these are the content of `make lint`.
- **Natural RED (B1).** I first wrote `run_front` with only the 60-s thread. `test_run_front_beats_before_the_thread` then failed with `AssertionError: no beat after the start line`. After I added the immediate `phase25_run.beat(heartbeat_path, **state)`, the test passed.
- **Mutation check (Task 2).** Each of the following edits to `phase36_probe.py` reddened `-k "e1 and not live"`. The file was restored byte-identical afterwards, confirmed with `cmp`.
  - Dropping the arm-record unlink: 2 failed.
  - Binding the pin payload (`_payload = ...`): 1 failed.
  - Removing `silenced()` from the `with`: 2 failed.
  - Halving `fixed_seconds`: 1 failed.

## Deviations from Plan

1. **[Rule 3] `PINNED_MODULES` lists phase35_prereg as a path string (`_SCRIPTS + "/phase35_prereg.py"`), not `phase35_prereg.__file__`.**
   - The plan said to resolve PINNED_MODULES against the modules.
   - Measured: `tests/test_phase35_prereg.py::test_slot_census_is_green_on_the_real_tree` and `tests/test_phase36_prereg.py::test_phase36_scripts_pass_the_slot_census` both failed with `scripts/phase36_probe.py:78: private access phase35_prereg.__file__`.
   - The census treats any `phase35_prereg._*` attribute, dunders included, as private access.
2. **[Rule 2] The e1_live fixture runs through `probe.main(["run", "--heartbeat", ..., "--ledger", ..., "--front", "e1"])`.** The plan has it call `probe.run_all(...)`. Going through `main` exercises the full CLI path to `stage_e1` on CPU. The emit step still calls the real `probe.emit("e1", out_path=...)`, because main's `emit` takes no out_path.
3. **[Rule 2] `e1_shape()` also checks `results/phase19_arm_erased.json` itself.** Its `config.attack_family` must equal `"A2"`, and its `config.corpus_entries` must equal `len(a2_corpus_entries())`. Measured values: A2 and 216, with K 48. Without this check, a corpus drift would leave the timer count proving the wrong shape.
4. **[Rule 2] `_e1_run(total_seconds, rows, questions, k)` is a pure helper.** It holds the per-run arithmetic so the pure tests can reach it. It also refuses `fixed_seconds < 0`, meaning the draws timed longer than the whole run.
5. **[Rule 2] Tests not in the plan's list:**
   - `test_every_probe_function_has_a_cpu_test` applies the 36-02 census to this file through `_untested_functions("probe", ...)`.
   - `test_git_surface_is_bounded` AST-checks every git argv against `ALLOWED_GIT_ACTIONS ∪ READ_ONLY_GIT_ACTIONS`, using the helpers in `test_phase25_driver`.
   - `test_isolation_committed_input_paths_are_the_pins_own` checks that `CURVE_RECORD` equals `phase19_run.TARGET_CURVE_PATH` and that `ERASED_RECORD` equals `phase19_erasure.arm_record_path("erased")`.
6. **No calibration_descent block.** `_write_record` copies phase31_probe's provenance block but not its `calibration_descent()`, which is Phase 30 ARECIPE-02 specific and has no Phase 36 counterpart. `_write_record` also runs `prove_no_reading` on the final record, provenance included, before the atomic write.
7. **`run_sidecar` validates the front against `PROBE_FRONTS`, not through `probe_record()`.** Otherwise `emit(front, out_path=tmp)` would have touched `probe_record`, and the plan's behavior bullet forbids that. The test patches `probe_record` to `pytest.fail`.
8. **TDD gate.** Each task is one `feat(36-03)` commit with no separate `test(...)` commit, the same convention 36-02 used. The RED evidence is the natural B1 RED and the mutation checks above. Task 2's tests were written after its code.
9. **Command forms.** I ran `.venv/bin/python -m pytest` in place of the plan's `.venv/bin/pytest`, and `ruff check . && ruff format --check .` in place of `make lint`, as the executor rules require.
10. **Plan premises measured true:**
    - phase19_erasure `:2732` run_erasure_arm, `:1627/:1628` corpus and Phase 18 arm paths, `:624` TARGET_SLOT.
    - phase14_recall `:84` ADAPTER_PATH, `:793` `_complete`, `:846` draw_all.
    - phase25_run `_heartbeat_loop` `while not stop.wait(seconds)`, the first beat after 60 s (B1).
    - The curve's `ordered_prefix` has 78 entries and equals the erased arm's `ablated_components`. `adapter_in_sha256` begins `226f2ae5`. `wall_clock_min` is 68.58400233189265.
    - The Phase 31 stage names are draw, measure, recall, score and train.
    - No component of `_capability()` (measure_exposure, dialogue_ppl_pair, retention_perplexity) calls `_complete`, so the timer counts exactly questions x K calls.

## Names waves 4-5 (36-04, 36-05) must extend

- **CLI.** `phase36_probe.py run [--heartbeat PATH] [--ledger PATH] [--front F ...]`, `emit FRONT`, `emit-all`, `preflight`. `main` prints `phase25_venue.launch_banner()` before `run`. The `--heartbeat` default is `phase36_ledger.HEARTBEAT_PATH`, and the `--ledger` default is None, which means `_GIT_ROOT / phase36_ledger.LEDGER_PATH`.
- **Registries.**
  - Register a stage with `STAGES[front] = stage_fn`. The stage function is `stage_fn(state) -> {"configuration": {...}, <numbers>, "reused": {front: bool}}`. Call `state.update(stage=..., shape=..., draw_index=...)` while it runs.
  - Register a builder with `RECORD_BUILDERS[front] = builder`. The builder is `builder(run_stages) -> (record_stages, repetitions)`.
  - `build_record(front, run, *, beside=None)` adds `beside` to the record at top level, and then `prove_no_reading` runs on it.
  - `emit(front, out_path=None)` now passes `beside=phase31_beside()` for `"e1"` only. 36-04 adds the e6 `a2_context_from_e1` beside in `emit`.
- **Core helpers.**
  - `run_front(front, *, heartbeat_path, ledger_path)`.
  - `run_all(*, heartbeat_path=None, ledger_path=None, fronts=RUN_ORDER)` refuses an unregistered front before any dirty or disk check.
  - `preflight()` prints `RUN_ORDER ...` and refuses any front in `RUN_ORDER` that has no stage. 36-04 adds the live checks.
  - `RUN_ORDER = ("e5", "e6", "e3", "e2", "e1")` and `PROBE_PREFIX = "probe36"`.
- **Isolation.**
  - `prove_isolated_label(label)` refuses labels starting `phase3`, `phase4` or `phase25_calibration`, and requires `probe36`.
  - `_data_path(name)` returns `_ROOT/data/<name>` after the label guard.
  - `run_sidecar(front)` is `data/probe36_<front>_run.json`. `sessions_sidecar(front)` is `data/probe36_<front>_sessions.json`. `arm_record_path(front, rep)` is `data/probe36_<front>_rep<rep>_arm.json`.
- **Reading gate.**
  - `prove_no_reading(blob)` checks every key against `READING_TOKENS` and allows strings only under `STR_SUBTREES = ("provenance", "configuration")` or a `STR_KEYS` key. `path` and `sha256` are in `STR_KEYS`.
  - The one exemption is `BESIDE_KEY = "beside_never_extrapolated"` with `BESIDE_STAGES_KEY = "stage_seconds"`, whose values must still be numbers.
- **Timing and silencing.**
  - `silenced()` is a context manager whose stdout buffer is dropped.
  - `DrawTimer()` sets `.rows = [{"seconds", "tokens", "at_cap"}]` per `phase14_recall._complete` call.
  - `_spread(values)` returns `{n, min, median, max}`.
- **E1 helpers.**
  - `e1_shape() -> (questions, K)` returns (216, 48) on the real tree.
  - `e1_components()` returns 78 tuples and reads only the committed JSON.
  - `published_adapter_sha256()`.
  - `prove_published_adapter()` is the one adapter-identity check and reads `phase14_recall.ADAPTER_PATH` at call time.
  - `_e1_run(...)` and `_e1_stages(...)`.
- **Constants.**
  - `CURVE_RECORD`, `ERASED_RECORD` and `PHASE31_POINT_RECORD`.
  - `PINNED_MODULES`, which 36-04/05 may need to extend. Any `phase35_prereg` entry must stay a path string.
  - `ALLOWED_GIT_ACTIONS` and `READ_ONLY_GIT_ACTIONS`. All git calls must use literal argv lists, with no `_git` helper.
- **Committing.**
  - `commit_path(relative, message)` accepts only `PROBE_RECORDS + (LEDGER_PATH,)`.
  - `_path_state(rel)` returns committed, modified, untracked or absent.
  - `emit_all()` runs `reconcile()`, then commits the ledger, then each record in RUN_ORDER.
- **E1 record shape for 36-06.**
  - `stages.runs[2]` holds `total_seconds, draws, draw_seconds_sum, fixed_seconds, k16_seconds, per_question_k16_seconds, per_question_k48_seconds, draw_seconds_spread, at_cap_draws, at_cap_seconds_spread, draw_seconds, draw_tokens`.
  - `stages.r1b_k48_totals[2]`.
  - `configuration` holds `arm, k (78), K, k16, questions, seed, ordering, target_slot, adapter_in_sha256, components_sha256, e1_targets, e1_teaching_seeds`.
  - `beside_never_extrapolated` holds `{path, sha256, stage_seconds, total_seconds}`. It is never a price input.
  - `provenance.run` holds `{git_sha, device, torch_version, started_utc, finished_utc}`, along with `module_sha256`, `git_sha`, `head_at_write` and `written_utc`.
  - `repetitions` is 2. The record also carries `reused`, `gates_nothing: true`, `sweep_point: false` and `probe_key` (the run id).
- **Test helpers in tests/test_phase36_probe.py.**
  - `clean_tree` is the autouse recorder on `probe.refuse_if_dirty`.
  - `_planted(tmp_path, monkeypatch, stage=_fake_stage)` registers a planted e5 stage and builder, redirects `_ROOT` and sets `_DEVICE="cpu"`. It returns `{heartbeat_path, ledger_path}`.
  - `_e1_light(tmp_path, monkeypatch, *, calls=6, on_call=None)` sets up the light stand-in with a fake `_complete`.
  - `_e1_live_fixture(root)` and the module-scoped `e1_live` fixture return `{root, sidecar, record, spies{pin_calls, hashed}, strays, stdout, ledger, heartbeat, arm_paths}`. Live constants are `LIVE_QUESTIONS, LIVE_K = 3, 4` and `LIVE_DRAWS`.
  - `_real_probe36_strays()`, `scratch` (a scratch git repo with `_GIT_ROOT` patched), `_emit_all_env`, `_head()`, and `_pre_fix_sha()` (the parent of the newest phase25_run.py commit).
  - **The census requires every new module-level def to be called as `probe.<def>(...)` somewhere in the test file.**

## Known Stubs

- `STAGES` and `RECORD_BUILDERS` register only `e1`. The other fronts are scheduled: 36-04 registers e5 and e6, and 36-05 registers e3 and e2. Until then `run_all()` with the default `RUN_ORDER` and `preflight()` refuse with "no registered stage", which is intended.
- `preflight()` has only the run-order and registration check. Plan 36-04 adds the live checks.

## Threat Flags

None. All new surface is in the plan's register:
- The automatic `git add` and `git commit` are T-36-14, bounded by the whitelist and the AST git-surface test.
- The data/ sidecars are T-36-13, covered by the probe36 label guard and the stray guard.
- The record writes are T-36-12 and T-36-40.

## Self-Check: PASSED

- FOUND: scripts/phase36_probe.py, tests/test_phase36_probe.py
- FOUND commits: 5ba38bb, 30004e3, 212e775
