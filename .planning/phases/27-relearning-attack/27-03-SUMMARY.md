---
phase: 27-relearning-attack
plan: 03
subsystem: testing
tags: [relearning-attack, cli-driver, admission-record, refusal-gates, kwargs-trace, resume-chain, on_draw, iso-06]

# Dependency graph
requires:
  - phase: 27-relearning-attack (27-01)
    provides: scripts/phase27_prereg.py — the admission gate, X by call, Z rule, rungs, band, pinned baselines, attacker corpus pins, recovery gate
  - phase: 27-relearning-attack (27-02)
    provides: train(..., on_draw=None) threaded to the teaching and replay draws; resume-chain stream identity measured
provides:
  - scripts/phase27_relearn.py — `admit` (write-once admission record) and the four legs calibrate / curve / gate / structural-proof, each gated on the COMMITTED record
  - tests/test_phase27_relearn.py — 16 test functions / 27 collected, the structural CPU half (plan 27-04 appends the wiring proof)
  - tests/test_lora_inject.py — one INJECT_LORA_CONSUMERS line for model_from_adapter (ISO-06)
affects: [27-04, 27-05, 28]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Every leg's first statement is blob = _require_admitted(record): exists, ADMITTED, pinned baselines, tracked when inside the repo — refused before any device is resolved"
    - "main() builds one explicit kwargs dict per mode and splats it into DISPATCH; an AST walk of main plus inspect.signature traces it"
    - "Draw-cache labels carry k (_k{K}) because phase25_run.load_draws refuses a cache recorded at another k"

key-files:
  created:
    - scripts/phase27_relearn.py
    - tests/test_phase27_relearn.py
  modified:
    - tests/test_lora_inject.py

key-decisions:
  - "The replay budget counts len(phase14_factset.LOCKED_FACTS): the attacker's flat pack stats carry no n_facts key, so the plan's stats[\"n_facts\"] raises KeyError on the first live call (measured)"
  - "model_from_adapter injects LoRAConfig(**artifact[\"lora_config\"]) inline, _proves it equal to asdict(tp.LORA_CFG), exports rungs at that config, and returns (model, model_cfg, base_fingerprint, lora_config)"
  - "run_curve refuses more than one admitted point per leg up front: the per-arm sidecar names carry leg/arm/seed but no point key, so a second point would collide at build_arm_bins' refuse_if_exists only after the first had trained and scored"
  - "_require_admitted resolves the record path first: a relative --record is not is_relative_to(_ROOT) and would have skipped the tracked conjunct (measured False)"

patterns-established:
  - "Internal wiring checked statically before any e2e: every driver call bound against the real callee signature (83 sites, 0 failures)"

# RELRN-01..05 in the plan's `requirements:` are the IDs this plan CONTRIBUTES to, not IDs it completes:
# per D-05 RELRN-01 is ticked only at plan 27-05, and RELRN-02..05 stay unticked by design.
requirements-completed: []

# Metrics
duration: 29min
completed: 2026-09-16
---

# Phase 27 Plan 03: Relearning Driver Summary

**`scripts/phase27_relearn.py` ships the phase's one gate call (`admit`) and four attack legs. `admit` refuses an existing record, refuses a dirty tree before it builds or hashes anything, and writes the MOOT record with 44 re-derived rows, zero-overlap disjointness over question strings and seven module digests. Every leg opens with `_require_admitted` and refuses a forged MOOT / INCONCLUSIVE / absent / moved-pin / untracked record before it resolves a device. The train path is `tp.train()` direct with one shared `TrainConfig`, a rung resume chain and an identity-tagged `on_draw` recorder. Nothing trained, scored or ran a leg past the gate in this plan.**

## Performance

- **Duration:** 29 min
- **Started:** 2026-09-16T16:58:19Z
- **Completed:** 2026-09-16T17:27:22Z (tasks and verification; this SUMMARY follows)
- **Tasks:** 4 of 4
- **Files:** 2 created (1195 + 551 lines), 1 modified (+2)

## Accomplishments

- **The record.** `build_record(frontier())` reads MOOT, 44 rows in `point_keys` order, 6 `refused` rows with null `cleared_a/b/c`, and cleared (a) 30 / (b) 4 / (c) 1 over 38 reached. X equals the frontier's value by call (0.006461685297443485), tolerated 0/416, and the recall thresholds are k 790/1008 at n8 and 87/1008 at n64.
- **The gate on every leg.** It checks, in order: the record exists, reads ADMITTED, carries baselines equal to the JSON-normalised pins, and is git-tracked when inside the repo. That tracked check is the driver's only git argv (`ls-files`). The 12 refusal parametrizations run through `main()`, and stubs make them fail if a leg reaches `shared_train_config` or `phase25_run.device()`.
- **The legs are real code on the real path**, checked without training. 83 internal call sites bind against the real callee signatures with 0 failures (scratch check, below). Plan 27-04's e2e is the proof that they run.

## Task Commits

The plan's commit boundaries: Tasks 1–3 in ONE driver commit, Task 4 in its own.

1. **Tasks 1–3: the driver + the ISO-06 register line** - `7e3d436` (feat), `scripts/phase27_relearn.py` + `tests/test_lora_inject.py`
2. **Task 4: the structural tests** - `c4ba1c6` (test), `tests/test_phase27_relearn.py`

**Plan metadata:** this SUMMARY's own commit (docs).

## Evidence

### Task 1 (CPU half, leg stubs in place)

`<automated>` verify, verbatim: `OK` / `All checks passed!` / `1 file already formatted` / `verify exit=0`.

Acceptance criteria (scratch `27-03/task1_criteria.py`), raw:

```
C1 torch/teach_persona/phase18_extraction absent after import: PASS
C3a verdict MOOT: PASS
C3b 44 rows in point_keys order: PASS
C3c 6 refused rows with null cleared and verdict REFUSED: PASS
C3d cleared_counts: PASS {'a': 30, 'b': 4, 'c': 1, 'reached': 38, 'refused': 6, 'by_leg': {'dp_n8': {'a': 15, 'b': 1, 'c': 1}, 'dp_n64': {'a': 15, 'b': 1, 'c': 0}, 'adv_n8': {'a': 0, 'b': 2, 'c': 0}, 'adv_n64': {'a': 0, 'b': 0, 'c': 0}}}
C3e x.value == frontier summary X: PASS 0.006461685297443485
C3f x.tolerated == 0: PASS {... 'n_questions': 416, 'tolerated': 0, 'fraction': 0.0, ...}
C3g recall_thresholds k: PASS {'n8': {'threshold': 0.548611111111111, 'k': 790, 'n': 1008}, 'n64': {'threshold': 0.06041666666666666, 'k': 87, 'n': 1008}}
C3h apparatus legs: PASS
C3i apparatus status/reason/draw_cache: PASS
C4a written file re-reads equal to the blob: PASS
C4b top-level keys: PASS 20 keys
C4c disjointness: PASS {"checked": 104, "held_out_family": "A2", "overlaps": {"attacker_corpus": 0, "teaching": 0, "trained_attack": 0}, "scored": {"gated_prompts": 416, "gated_questions": 104, "heldout_recall": 104}, "trained_attack_rows": 336, ...}
C4d provenance module digests == bytes recompute: PASS 7
C4e recorder pathspec/who: PASS [{'who': 'phase27_relearn', ..., 'pathspec': ('scripts', 'src', 'results'), 'cwd': PosixPath('/Users/juliorcoelho/PersonaCore')}]
C5a absent: PASS [phase27_relearn] .../absent.json is absent — REFUSING to run this leg: run `admit` first; every leg is gated on the COMMITTED record
C5b MOOT: PASS [phase27_relearn] .../phase27_admission.json reads 'MOOT' — REFUSING to run this leg: nothing is admitted (forged)
C5c ADMITTED tmp record returns blob without git: PASS
C5d moved pin: PASS [phase27_relearn] ... carries baselines that differ from phase27_prereg.PINNED_BASELINES — REFUSING: D-12's pins moved after the record was written
C6a gate without --baseline: PASS
C6b gate --baseline made_up: PASS
grep: train_arm( 0 | mitigation_point_verdict 0 | from phase27_prereg import 0 | adversarial_episodes( non-comment 1
```

The real `refuse_if_dirty` was watched refusing `admit`, in the natural state where the driver was untracked, before any torch import:

```
REFUSED: [phase27_relearn] REFUSING: the working tree is dirty.
?? scripts/phase27_relearn.py
admit publishes git_sha and hashes seven modules and the frontier from the working tree; ...
file written? False | torch imported? False
```

### Task 2 (helpers, stubs still in place)

`<automated>` verify, verbatim: `OK` / `All checks passed!` / `1 file already formatted` / `verify exit=0`.

```
C1 shared_train_config no params, symbols present, no digit other than 0/1 anywhere in its source: FAIL digits=['27'] numeric AST constants=[]
C2 recorder: resolve() + teaching_bin in source, no endswith(: PASS
C2 recorder tags: PASS tag bytes b'\x00' b'\x01', 34 bytes, draws 2
   two-line check: b'\x00' for phase27_x_train.bin | b'\x01' for dialog_train.bin
C3 train_relearn_arm contents: PASS missing=[] mkdirs-before-recorder=3
C4 score_rung contents + docstring names: PASS []
C5 RuntimeConfig import lives inside a function: PASS
grep: torch.load 0 | load_slim|load_adapter(|load_checkpoint( 4 | from personacore.config import RuntimeConfig 1 (line 545, inside train_relearn_arm) | stubs 4
```

C1's `FAIL` is the textual reading of "no numeric literal other than 0/1". The only digits in the function are the `27` of the REQUIRED symbol `phase27_prereg.RELEARN_CAP`, and the function has 0 numeric AST constants. The criterion measures prose, and the AST reading passes.

**Natural RED: the ISO-06 census before its register line (C1).** `model_from_adapter` had been written, but its register line had not yet been added:

```
E       AssertionError: the inject_lora CONSUMER set moved. ...
E           found:    [('scripts/personalize_demo.py', 'build_demo'), ('scripts/phase14_recall.py', 'load_adapted_model'), ('scripts/phase14_recall.py', 'run_bit_identity_control'), ('scripts/phase27_relearn.py', 'model_from_adapter')]
E           expected: [('scripts/personalize_demo.py', 'build_demo'), ('scripts/phase14_recall.py', 'load_adapted_model'), ('scripts/phase14_recall.py', 'run_bit_identity_control')]
FAILED tests/test_lora_inject.py::test_every_inject_lora_consumer_reads_the_artifact_config
1 failed in 1.13s
```

It failed at the consumer assertion, not at the unclassified bucket, so the inline form classifies as a consumer. After the one line: `1 passed in 1.13s`; the whole file after the commit: `12 passed in 1.21s`.

### Task 3 (the legs, the driver commit)

`<automated>` verify, verbatim, final run: `OK` / `All checks passed!` / `1 file already formatted` / `15 passed in 1.86s` (`test_resume_from_none_is_inert` + `test_phase20_correction.py`). The first run failed at `'CURVE_K}' in inspect.getsource(r.run_curve)`: I had bound a local `curve_k`. Every label and `k=` now spells `phase27_prereg.CURVE_K` / `FULL_K` at the call site (C4).

```
C1 every run_* opens with blob = _require_admitted(record): PASS {'run_calibrate': True, 'run_curve': True, 'run_gate': True, 'run_structural_proof': True}
C2a run_gate: one recovery_gate call site, keyword set exactly the five: PASS [['baseline', 'recovered_questions', 'recovered_successes', 'x', 'z']]
C2b extraction_ceiling_x( present, ["extraction_ceiling"] absent: PASS
C2c FULL_K label: PASS ["f'phase27_{leg}_{key}_rung{z:04d}_k{phase27_prereg.FULL_K}'"]
C2d CURVE_K labels (quote-agnostic re-check): [('run_calibrate', 'phase27_prereg.CURVE_K', "'_k'"), ('run_curve', 'phase27_prereg.CURVE_K', "'_k'")] -> True
C2e run_curve has band( and admitted_point_keys: PASS
C3 AST phase25_run.device() call sites by function: {'run_calibrate': 1, 'run_curve': 1, 'run_gate': 1}
grep: phase25_run.device() 7 lines | torch.load 0 | train_arm( 0 | mitigation_point_verdict 0 | os.replace 0 | NotImplementedError 0
```

The first C2d printout read `FAIL` because my own check expected single quotes: `ast.unparse` double-quotes an f-string that contains `rung['steps']`. The quote-agnostic re-check above passes.

`grep -c "phase25_run.device()"` gives 7, which is at least 4. In the AST there are 3 call sites; the other 4 lines are prose. `run_structural_proof` reads JSON only and resolves no device: it records each arm's `device` from the readings (plan item 9).

The driver has no K literal. Its numeric AST constants are `[0, 1, 2, 6, 18]`: the ≥2-arms check, and the `6 * n_layer` wrap count and `18 * n_embd` trainable census.

**C6 walkers, before the driver commit:** `1 failed, 211 passed in 21.15s`. The one failure is `test_phase25_driver.py::test_the_git_surface_gate_fires_on_a_planted_push`, and its message names only `'?? scripts/phase27_relearn.py\n'`.

**After `7e3d436`:** `git log --oneline -1 -- scripts/phase27_relearn.py` → `7e3d436`, and `git ls-files 'results/phase27_*'` → empty. The 11 clean-tree probes by node id, without the sweep flag: `11 passed in 105.53s` (see Issues about MPS).

### Task 4 (the tests)

`<automated>` verify, verbatim: `27 passed in 1.80s` (slowest: 0.91s `test_admit_refuses_to_overwrite`) / `All checks passed!` / `2 files already formatted` / `74 passed in 5.61s` (prereg + on_draw + resume inert + correction + phase25_close).

- `.venv/bin/pytest -q tests/test_phase27_relearn.py -rs` → `27 passed in 1.79s`, **0 skipped, 0 failed**, from 16 test functions. The file has no host-only input, so `test_phase25_venue.py`'s skip literals do not move.
- `--collect-only` shows `27 tests collected`. The `test_each_leg_refuses_unless_admitted[` count is **12**, including `[calibrate-MOOT]`, `[curve-MOOT]`, `[gate-MOOT]` and `[structural-proof-MOOT]` verbatim.
- `grep -c "train_arm("` → `tests/test_phase27_relearn.py:0`, `scripts/phase27_relearn.py:0`; `grep -c '"A2"'` in the test file → 0.
- `results/`, checked around the test run (C2):
  ```
  BEFORE: status results/ [] find []
  AFTER: status results/ [] find results [] find data []
  ```

**Watched RED on tmp copies** (the plan's sanctioned branch, since the driver was complete before the test file existed):

```
real driver failures: []
misspelled copy failures:
    gate: main() passes ['baselne'], which run_gate does not accept
    gate: main() never passes run_gate's required ['baseline']
real git surface: [('ls-files', 162, '_require_admitted')]
planted copy git surface: [('add', 1199, '_planted'), ('ls-files', 162, '_require_admitted')]
```

**Before the test commit**, the tests/ porcelain probes were RED by design while `tests/test_phase27_relearn.py` was untracked. They were not run in that state.

**After `c4ba1c6`:**
- The 11 probes, with `PERSONACORE_SWEEP_ACTIVE=1`: `10 passed, 1 skipped in 3.18s`. The skip is the MPS-gated `test_phase23_resume.py:694`.
- C6 walkers: `212 passed in 21.24s`, covering `lora_inject`, `phase14_scoring`, `phase20_correction`, `phase23_ctrl`, `phase21_unit_continuation`, `phase25_driver` (including the `os.replace` census), `phase17_stats`, the `train_arm(` register node, `phase20_prereg` and `phase18_corpus`.
- Collected: `2862 tests collected in 2.98s`. That is **2835 → 2862 (+27)**.

### Plan-level verification and bounds

```
$ git diff --stat HEAD~3 -- scripts/teach_persona.py scripts/phase27_prereg.py pyproject.toml results/phase25_frontier.json   -> (nothing)
$ git diff --name-status 941780a HEAD
A	scripts/phase27_relearn.py
M	tests/test_lora_inject.py
A	tests/test_phase27_relearn.py
$ git diff --stat 941780a HEAD -- .planning/STATE.md .planning/ROADMAP.md .planning/REQUIREMENTS.md   -> (nothing)
$ git ls-files 'results/phase27_*'   -> (nothing)
$ find data -maxdepth 1 \( -name 'phase27_*' -o -name 'phase25_phase27_*' -o -name 'persona_relearn_attacker_*' \)   -> (nothing)
```

No gsd-sdk mutation handler was called. ` D .claude/scheduled_tasks.lock` was never staged.

### Static internal wiring (scratch `27-03/internal_trace.py`, not in the tree)

This check binds every call in the driver to a real callee signature: `tp.*`, `ckpt_mod.*`, `phase25_run.*`, `phase27_prereg.*`, `x18.*`, `pr.*`, `mitigation_gate.*`, `phase24_adversarial.*`, `phase25_points.*`, `RuntimeConfig`, `LoRAConfig`, `load_adapter_weights`, `lora_state_dict`, `from_json`, `refuse_if_dirty` and the driver's own helpers. Each call's positional count and keyword names go through `inspect.signature(...).bind`.

```
internal call sites bound against the real signatures: 83
failures: []
```

This is not a run. Plan 27-04's e2e is the wiring proof.

## Write set and redirect names

Measured by scanning the code lines (docstrings and comments excluded) of every callee the legs reach. The patterns were `open(`, `write_text`, `write_bytes`, `torch.save`, `np.save`, `.tofile(`, `mkdir(`, `os.replace`, `atomic_write_json`, `write_draws`, `save_checkpoint(`, `CSVLogger(`, `unlink` and `shutil.` (scratch `27-03/writeset.py`). Callees with 0 write hits: `tp.build_arm_bins` (it writes through `build_bins`), `tp.sanity_check`, `tp.render_episodes`, `tp.refuse_if_exists`, `tp.arm_outputs`, `loop.estimate_loss`, `checkpoint.load_checkpoint` / `load_adapter` / `load_slim`, `tp.score_arm`, `tp.calibration_items`, `tp.score_items`, `pr.load_adapted_model`, `pr.draw_all`, `pr.build_question_sets`, `phase25_run._draw_one_shape`, `load_draws`, `score_point`, `device`, `x18.build_corpus`, `x18.score_records`, `x18.aggregate_questions`, `phase24_adversarial._adversarial_pool`, `seeding.seed_everything`.

| Writer | Measured write | Lands at (real tree) | Redirect a fixture must monkeypatch |
|---|---|---|---|
| `tp.build_arm_bins` → `tp.build_bins` | `ids_all.tofile(bin_path)` / `mask_all.tofile(mask_path)` (`teach_persona.py:664-665`) | `data/persona_relearn_attacker_{leg}_{arm}_seed{S}_train.bin` and `_train_mask.bin` (gitignored; NO phase prefix) | `teach_persona._REPO_ROOT` (read at call time by `arm_outputs`) |
| `tp.train` (`loop.py:802`, `personacore/logging.py:29`) | `CSVLogger(log_path)` opens `"a"` | **`results/phase27_relearn_attacker_{leg}_{arm}_seed{S}/run.csv` — under the REAL, tracked `results/` tree, NOT gitignored** | `teach_persona._REPO_ROOT` |
| `tp.train` → `save_checkpoint` (`loop.py:924/947/974` → `checkpoint.py:153` `torch.save`) | in-loop every `CHECKPOINT_INTERVAL` + end of call (`best_checkpoint_path` not passed) | `checkpoints/phase27_relearn_attacker_{leg}_{arm}_seed{S}_latest.pt` (gitignored) | `teach_persona._REPO_ROOT` |
| `ckpt_mod.export_adapter` (`checkpoint.py:276` `torch.save`) | one per rung | `{out_dir}/phase27_{leg}_{arm}_seed{S}_rung{NNNN}_adapter.pt` | `--out-dir` (default `phase27_relearn.STREAM_DIR` = `data/`) |
| `tp.score_arm` | **nothing** (0 write hits in `score_arm`, `calibration_items`, `score_items`, `pr.load_adapted_model`, `pr.draw_all`) | — | reads the base at `phase14_recall.CONVBASE_SLIM` |
| `phase25_run.draw_point_shapes` → `write_draws` → `atomic_write_json` (`phase25_run.py:497`, `:239`) | the draw cache, once per shape | `data/phase25_phase27_{leg}_{point_key or arm_seedS}_rung{NNNN}_k{K}_draws.json` (gitignored) | `phase25_run.DRAWS_DIR` |
| `phase25_run._draw_one_shape` | nothing written | — | reads the base at `phase14_recall.CONVBASE_SLIM` and the device from `phase25_run.device()` → `phase25_run._DEVICE` |
| driver `make_recorder` callback | `open(path, "ab")` per draw | `{out_dir}/phase27_{leg}_{arm}_seed{S}_offsets.bin` | `--out-dir` |
| driver `train_relearn_arm` | `atomic_write_json` | `{out_dir}/phase27_{leg}_{arm}_seed{S}_readings.json` | `--out-dir` |
| driver legs | `atomic_write_json` | `{out_dir}/phase27_{leg}_calibration.json`, `_curve.json`, `_gate.json`, `_structural.json` | `--out-dir` |
| driver `admit` | `atomic_write_json` | `results/phase27_admission.json` (`--out`) | `--out` / a tmp `out_path` |

Reads a fixture must redirect:
- `phase27_relearn.BASE_SLIM`: the base `model_from_adapter` trains.
- `phase14_recall.CONVBASE_SLIM`: the base both scorers load.
- `phase25_run._DEVICE`: set it to `"cpu"`. Every leg and `_draw_one_shape` resolve through `phase25_run.device()`.
- `phase18_extraction.CORPUS_SOURCE_FIXTURE`: `score_rung`'s `build_corpus` reads it, and so does `disjointness_report`.
- `teach_persona.DIALOG_VAL_BIN` / `DIALOG_VAL_MASK` / `DIALOG_TRAIN_BIN` / `DIALOG_TRAIN_MASK`: read by `tp.train` for eval and replay; they are gitignored `data/` files, absent in CI.
- `phase27_relearn.frontier`: the curve reads adapter paths from it, and the gate reads X by call.
- `phase27_prereg.PINNED_BASELINES` and the budget constants, read at call time.
- Not needed on this path: `teach_persona.FACTSET_REPORT` is read only inside `train_arm` (`teach_persona.py:1763`), which the driver never calls, and no heartbeat is written because `draw_point_shapes` gets `state={}` and never calls `beat`.

## Files Created/Modified

- `scripts/phase27_relearn.py` (1195 lines):
  - module docstring;
  - `INSTRUMENT_GIT_SHA`, `RECORD`, `STREAM_DIR`, `BASE_SLIM`, `PINNED_MODULES` (7), `ARMS`, `TRAIN_PATH`, `SUB_MODES`, `DRAW_CACHE`, `APPARATUS_LEGS`;
  - `_prove`, `_utc`, `_sha256`, `_rel`, `frontier`, `admission`, `_require_admitted`, `disjointness_report`, `build_record`, `admit`;
  - `make_recorder`, `stream_digest`, `shared_train_config`, `model_from_adapter`, `train_relearn_arm`, `score_rung`;
  - `run_calibrate`, `run_curve`, `run_gate`, `run_structural_proof`;
  - `DISPATCH`, `build_parser`, `main`.
- `tests/test_phase27_relearn.py` (551 lines): the 16 test functions the plan names (27 collected).
- `tests/test_lora_inject.py` (+2): a one-line comment (Phase 27, D-22) and `("scripts/phase27_relearn.py", "model_from_adapter"),` in `INJECT_LORA_CONSUMERS`.

## Decisions Made

See `key-decisions`. All four were decided by measurement or by reading the callee.

## Deviations from Plan

### Orchestrator corrections applied (C1–C7)

**C1: ISO-06 consumer form.**
- `model_from_adapter` runs, in order:
  1. the sha pin `_prove`;
  2. `load_slim(BASE_SLIM)`, then the fingerprint trio (`git_sha` / `step` / `val_loss`, the key names `export_slim` writes);
  3. `load_adapter(start_adapter, expected_fingerprint=trio)`;
  4. `_prove(artifact["lora_config"] == dataclasses.asdict(tp.LORA_CFG))`;
  5. GPT build, then `load_state_dict` (LOAD BEFORE INJECT);
  6. `tp.inject_lora(model, LoRAConfig(**artifact["lora_config"]))` inline, with `LoRAConfig` imported by bare name;
  7. `load_adapter_weights(model, artifact)`;
  8. `mark_only_lora_trainable`, then the `r * n_layer * 18 * n_embd` census.
- Rung adapters are exported with `lora_config=` that config. To get it there, `model_from_adapter` returns a 4-tuple; the plan specified a 3-tuple.
- The register line landed in the driver commit `7e3d436`.
- Evidence: the natural RED and GREEN above.
- **One disclosure:** before the commit I ran only the census node (`1 passed`), not the whole of `tests/test_lora_inject.py`. The whole file ran right after the commit, against the same bytes: `12 passed in 1.21s`.

**C2: nothing written under the real `results/`.**
- In `test_admit_refuses_a_dirty_tree_before_hashing`, the first `admit` call has `build_record` stubbed to raise `SystemExit("[probe] stopped after the dirty check")`. The test asserts `not inside.exists()`, and the single recorded `refuse_if_dirty` call proves the order.
- `test_a_leg_refuses_an_untracked_record_inside_the_repo` keeps a `try/finally` unlink and asserts the probe is gone and still untracked.
- `results/` was empty before and after, as shown above.

**C3: plain ints.** `first_clear` triples, `scored_tokens(mask_ones=int(...), steps=int(rung))` and both `recovery_gate` counts are `int(...)`. `mask_ones` is `int(np.fromfile(...).sum())`.

**C4: K is read, never assumed.** Every label and `k=` spells `phase27_prereg.CURVE_K` / `phase27_prereg.FULL_K` at the call site, and `promote_at_z` reads the prereg at call time. There is no K literal (the numeric AST constants are listed above).

**C5: the `os.replace` census.** 0 hits in the driver. Every JSON write goes through `phase25_run.atomic_write_json`, and the offset stream is an `"ab"` append. `test_os_replace_appears_only_in_the_two_phase25_writers` is green inside the 212-test walker run.

**C6: walkers.** Before the driver commit: 1 porcelain failure, 211 passed. After Task 4: 212 passed. No function is named or calls `train_never_taught`; there is no `train_arm(`, no `mitigation_point_verdict` and no `privacy_n`.

**C7: write set.** See "Write set and redirect names".

### Auto-fixed (Rules 1–2)

**1. [Rule 1 - Bug] `stats["n_facts"]` raises `KeyError` on the attacker's flat pack.**
- **Found during:** Task 2, before writing the helper.
- **Issue:** plan items 4 and 5 read `stats["n_facts"]` for `replay_window_budget` and the readings. Only the fact-aligned DP pack writes that key (`teach_persona.py:944`). The `relearn_attacker_*` arms are not DP arms.
- **Evidence:** measured by building into a scratch `_REPO_ROOT`:
  ```
  stats keys: ['episode_len_max', 'episode_len_mean', 'episode_len_min', 'episodes', 'mask_fraction', 'mask_fraction_max', 'mask_fraction_mean', 'mask_fraction_min', 'replay_ratio', 'replay_tokens', 'teaching_tokens', 'tokens']
  'n_facts' in stats: False
  bin sha == pin: True | rows sha == pin: True | bin bytes: 15162 | is DP arm: False
  ```
- **Fix:** `n_facts = len(fs.LOCKED_FACTS)`, the facts the bins were built from, with a comment saying why.
- **Commit:** `7e3d436`.

**2. [Rule 2 - Security] `_require_admitted` resolves the path before the tracked conjunct.**
- **Issue:** measured `relative --record is_relative_to(_ROOT): False | resolved: True`. With a relative `--record`, the plan's check would skip `git ls-files` and run a leg against an untracked record.
- **Fix:** `path = pathlib.Path(record_path).resolve()`.
- **Commit:** `7e3d436`.

**3. [Rule 1 - Bug] The absent-record message must say REFUSING.**
- **Issue:** the plan's absent message lacked "REFUSING", but its own Task 4 test asserts `"REFUSING" in str(exc.value)` for all three readings.
- **Fix:** the absent message now reads "... is absent — REFUSING to run this leg: ...".
- **Commit:** `7e3d436`.

**4. [Rule 1 - Bug, latent] Two admitted points in one leg would collide mid-run.**
- **Issue:** every mitigated-arm name is `f(leg, "mitigated", DESIGNATED_SEED)`: bins, CSV, checkpoint, readings, rung adapters and offsets. `build_arm_bins` refuses existing bins (`teach_persona.py:1340-1341`, `if resume_from is None: refuse_if_exists(targets)`). So a second admitted point in a leg would crash only after the first point had trained and scored. D-22 requires every PASS point.
- **Fix:** `run_curve` `_prove`s at most one admitted point per leg before any device or training. The limit and its upgrade path are named in a `ponytail:` comment: put the point key into `train_relearn_arm`'s names. This keeps 27-04's expected file names (`phase27_n8_mitigated_seed1337_*`) intact.
- **Needs a decision:** before any frontier admits two points in one leg. On the committed MOOT frontier it has no effect.
- **Commit:** `7e3d436`.

**5. [Rule 2] `make_recorder` refuses an existing stream file.** Appending to a stale file would make the file's bytes stop matching the in-memory digest, and the digest's "locate the divergence by offset" property would break. **Commit:** `7e3d436`.

**6. [Rule 2] Extra `run_gate` checks.**
- It refuses a curve built at a different Z than the calibration.
- It refuses a curve whose point set differs from the record's admitted keys for the leg.
- It re-hashes the Z-rung adapter against the sha the curve recorded before the FULL_K re-score (T-27-11).
- **Commit:** `7e3d436`.

**7. [Rule 1 - Bug] The plan's stub form fails its own ruff verify.**
- **Evidence:** measured `F841 Local variable 'blob' is assigned to but never used` ×4 on `blob = _require_admitted(record)` followed by `raise NotImplementedError(...)`.
- **Fix:** the intermediate stubs carried `# noqa: F841  (Task-3 stub)`. They were gone in Task 3, and the final file has 0 `NotImplementedError` and no such noqa.

### Plan text falsified or refined (followed the code or measurement)

**8. `corpus_pin_checked` uses the rows digest, not "len and ids".** The plan names no committed id list to compare against. The check is `attacker_corpus_rows_sha256() == ATTACKER_CORPUS["rows_sha256"]`, the pin's own definition, measured True on the real fact set. When it is True, the bin sha must equal the bin pin or the arm refuses. With the synthetic facts it is recorded as `false`.

**9. With Z undefined, `run_gate` passes the cap rung's MEASURED extraction counts.** The plan said `recovered_successes=0`, which would record an invented zero. `recovery_gate` reads INCONCLUSIVE on `z=None` whatever the counts, so the verdict is unchanged, and `recovered.steps` names the rung the counts came from.

**10. Extra fields in the curve rows and readings.**
- Curve rung rows merge the rung (`steps`, `scored_tokens`, `adapter_path`, `adapter_sha256`) with the score reading (`k`, `point_label`, `draws_cache`, recall, extraction), plus `band`. `gate` uses them to re-score the exact adapter and to locate the CURVE_K cache for the prefix check.
- The readings add `bin_bytes`, the bin lengths D-26(iii) says to record.
- `structural.json` adds the leg's `admitted_point_keys`, which also gives the required `blob` assignment a use.

**11. `values` is `phase25_points.scoring_values()`, which returns a `dict`.** Measured: `scoring_values returns a dict`. The plan's interface described a list, but `x18.score_records` requires `{fact_id: value}`.

**12. `score_rung(out_dir=...)` is accepted and unused.** The plan's verify asserts that exact parameter set. The docstring says the only file it writes is the draw cache.

**13. `erasure_gate` is not imported at module scope.** Nothing in the driver uses it (ruff F401). The plan's list was an upper bound ("ONLY").

**14. Plan miscount.** "the 21 keys listed in Task 1 item 6 plus disjointness and provenance": that list has 18 keys plus the 2, and the record has 20 (measured). The test asserts the explicit set.

**15. Extraction successes count questions where `answered` is True** (any of the k draws contained the value). That is the unit `phase25_points._family_counts` sums into the frontier's `point_extraction_successes`, and a comment says so.

**16. Two display choices.** `APPARATUS_LEGS[*].name` is "Z calibration" / "cost-to-recovery curve" / "recovery-ceiling gate" / "structural identical-budget proofs". `DRAW_CACHE` reads `{point_key or arm_seedS}`, because calibrate's labels carry `fresh_seed{S}` / `control_seed{S}` where a point key would be.

---

**Total deviations:** the 7 orchestrator corrections applied; 7 auto-fixes (Rules 1–2), one of which (4) needs a naming decision before a two-point leg is ever admitted; 9 plan-text items followed by code or measurement.
**Impact:** no scope creep. Nothing outside the three sanctioned files was touched. Every acceptance criterion holds, except three grep criteria that measure prose; the AST-level readings are given above.

## Issues Encountered

- **An MPS test ran once, as part of the orchestrator's listed probes.** After `7e3d436` I re-ran the 11 clean-tree probes by node id without `PERSONACORE_SWEEP_ACTIVE`.
  - `tests/test_phase23_resume.py::test_production_resume_epsilon_bit_identical` is a pre-existing Phase-23 MPS resume probe (4-step DP arm, outputs deleted). It executed on MPS: `11 passed in 105.53s`.
  - Afterwards `git status --short` showed only the pre-existing lock, and the data/ stray find was empty.
  - It is not a Phase-27 leg, and no driver code ran on MPS.
  - The post-`c4ba1c6` re-run used the flag (`10 passed, 1 skipped`), because only `tests/` had changed and `results/` was untouched since the green MPS run.
- **The Fact-Forcing Gate blocked one scratch `rm -rf`** of a directory that did not exist yet. The `rm` was dropped and a fresh scratch directory used instead. No artifact was affected.
- **Two of my own checks read the wrong thing and were re-run:** a local `curve_k` failed the Task-3 textual verify (fixed in the driver), and a quote-style assumption in the C2d criterion check.
- **Obsidian:** this subagent has no Obsidian MCP tool, so the vault entry for 27-03 is **PENDING — not saved**.

## Known Stubs

None. The four legs are real code on the real train and score path. By design (D-09) no test runs them past `_require_admitted` in this plan; plan 27-04's CPU e2e does.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: write-surface | scripts/phase27_relearn.py (via `tp.train(log_path=paths["csv"])`) | A live leg writes `results/phase27_relearn_attacker_{leg}_{arm}_seed{S}/run.csv`. That is untracked and NOT gitignored, and it matches `ARTIFACT_GLOB = "results/phase27_*"` if it were ever committed. It would also dirty `results/` for any later `refuse_if_dirty`. The measured `arm_outputs` shape is `_REPO_ROOT / "results" / f"{prefix}_{arm}" / "run.csv"`. 27-04 must redirect `teach_persona._REPO_ROOT`. A future ADMITTED run must never `git add` these directories, and must run `admit` before any leg. |

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Forward notes for 27-04, all measured or read from the code:

1. **Redirects.** Redirect every name in "Write set and redirect names", `teach_persona._REPO_ROOT` included: the CSV otherwise lands under the real `results/`.
2. **LoRA config.** The tiny start adapters must carry `lora_config == dataclasses.asdict(tp.LORA_CFG)` (r=8, alpha=16.0, dropout 0.0, the six targets), or `tp.LORA_CFG` must be monkeypatched. `model_from_adapter` refuses any other config.
3. **Fresh roots.** `build_arm_bins` refuses existing bins, so each e2e run needs a fresh `_REPO_ROOT`. `make_recorder` likewise refuses an existing offsets file under `--out-dir`.
4. **Seeds.** `FRESH_SEEDS` needs at least 2 seeds, because `band` uses `phase23_prereg.noise_floor`, which refuses fewer than two.
5. **Config identity across legs.** Identity (`is`) of the shared `TrainConfig` holds WITHIN a leg: fresh@designated `is` control@designated in `calibrate`. `curve` builds its own instance, so the mitigated arm's config is value-equal to calibrate's, not the same object. 27-04's (a) "SAME instance" must be read per leg run.
6. **One mitigated point per leg.** `run_curve` refuses a second admitted point in one leg (Deviation 4). The e2e's single `dp_n8_sigma0p500000` point is fine.
7. **Unticked requirements.** RELRN-01..05 stay unticked (D-05). STATE.md, ROADMAP.md and REQUIREMENTS.md were not touched, and no gsd-sdk mutation handler was called (D-38).

## Self-Check: PASSED

- `scripts/phase27_relearn.py` FOUND (1195 lines); `tests/test_phase27_relearn.py` FOUND (551 lines); `tests/test_lora_inject.py` modified (+2) FOUND at `7e3d436`
- commits `7e3d436` (feat) and `c4ba1c6` (test) FOUND in `git log --oneline -3` on `main`, on top of `941780a`
- `git ls-files 'results/phase27_*'` empty; collected 2862 (+27); `tests/test_phase27_relearn.py` 27 passed / 0 skipped / 0 failed

---
*Phase: 27-relearning-attack*
*Completed: 2026-09-16*
