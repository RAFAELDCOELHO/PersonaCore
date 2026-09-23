---
phase: 27-relearning-attack
plan: 02
subsystem: training
tags: [on_draw, offset-stream, data-order-proof, resume-chain, byte-identity, sha256, numpy-rng]

# Dependency graph
requires:
  - phase: 21-replay-seam
    provides: train(replay_bin, replay_mask_bin, replay_windows) and the replay_fn micro-batch closure, the second threaded draw
  - phase: 12-masked-dialogue-data
    provides: get_batch_memmap_masked and the train_mask_bin branch of train(), the first threaded draw
provides:
  - src/personacore/training/data.py: get_batch_memmap_masked(..., *, on_draw=None); on_draw(bin_path, ix) called right after the global-NumPy draw
  - src/personacore/training/loop.py: keyword-only train(..., on_draw=None) forwarded to the mask-branch batch_fn and every replay_fn micro-batch, only when set; estimate_loss not threaded
  - tests/test_phase27_on_draw.py: 5 tests (byte-neutrality, coverage, seed sensitivity, resume-chain identity, signature pins)
  - RESEARCH assumption A1 settled by measurement on CPU: a 1-step link resumed to 2 steps equals the uninterrupted run in stream sha256 and in all 24 adapter tensors
affects: [27-03, 27-04, 27-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Optional keyword forwarded only when set (**({} if x is None else dict(x=x))): the default-path call keeps its exact pre-change arguments, so fixed-signature fakes of the loader still work"
    - "Resume-chain identity tests re-seed the global RNG before the resume, or an in-process chain cannot detect a missing checkpoint RNG restore"

key-files:
  created:
    - tests/test_phase27_on_draw.py
  modified:
    - src/personacore/training/data.py
    - src/personacore/training/loop.py

key-decisions:
  - "on_draw is forwarded to the two training draws only when it is not None (loop.py's own mask_bin rule at the eval call). The unconditional spelling broke tests/test_phase21_replay_volume.py's fixed-signature loader fake, and that file is out of this plan's bounds"
  - "The resume-chain test re-seeds (seed_everything(11)) before the resume. Measured: with the checkpoint's NumPy restore disabled, the chain still matched without the re-seed and diverged with it"
  - "estimate_loss stays un-threaded (D-30). Measured: with a log_path its eval makes 20 val-bin loader calls per eval that the recorder does not see, and eval at every step leaves the stream sha256 and the adapters unchanged"

patterns-established:
  - "Natural RED from the one-site intermediate state: teaching site threaded, replay not; the coverage test named the 4 unseen replay draws"

# RELRN-04 in the plan's `requirements:` is the ID this plan CONTRIBUTES to, not an ID it completes:
# per D-05, RELRN-02..05 stay unticked by design.
requirements-completed: []

# Metrics
duration: 21min
completed: 2026-09-16
---

# Phase 27 Plan 02: on_draw Capture Point Summary

**`get_batch_memmap_masked` gained a keyword-only `on_draw=None`. It is called with `(bin_path, ix)` right after the global-NumPy draw. `train()` forwards it to both training draws: the mask-branch teaching draw and every replay micro-batch. `estimate_loss` is deliberately left out. A recorder sees 6 of 6 loader draws over 2 steps. Its sha256 is equal across equal seeds and differs across seeds. A 1-step run resumed to 2 steps reproduces the uninterrupted stream and all 24 adapter tensors bit for bit on CPU, which settles RESEARCH A1 for plan 27-03's rung ladder.**

## Performance

- **Duration:** 21 min (1277 s)
- **Started:** 2026-09-16T16:08:34Z
- **Completed:** 2026-09-16T16:29:51Z (tasks and verification; this SUMMARY follows)
- **Tasks:** 2 of 2
- **Files:** 1 created (244 lines), 2 modified (+22 / -2)

## Accomplishments

- **The hook exists and is inert when `None`.**
  - With `on_draw=None`, both training call sites call the loader with their exact pre-Phase-27 arguments.
  - Inside the loader, the guard is the only new line on that path.
  - The golden suites stay green.
- **Coverage is measured through the real `train()`.**
  - A spy on the loop binding sees `[(train, 2), (replay, 2), (replay, 1)] × 2` and no val-bin call.
  - The recorder sees all 6 draws, in the same order.
- **A1 is settled for the replay path.** The resume chain equals one run in both stream and adapters. The test can fail on a missing NumPy restore: that was measured, not argued.

## Task Commits

1. **Task 1: on_draw on the loader, threaded through train()** - `58ee800` (feat), data.py + loop.py only
2. **Task 2: tests/test_phase27_on_draw.py** - `835b1d0` (test), the test file only

**Plan metadata:** this SUMMARY's own commit (docs).

## Evidence

### Natural RED (teaching site threaded, replay site not) and GREEN

The test file was written first. Then:
- `data.py` was edited.
- `train()` gained `on_draw=None`, forwarded at the teaching call only.
- The coverage test ran:

```
$ .venv/bin/pytest -q "tests/test_phase27_on_draw.py::test_offset_stream_hash_covers_every_draw"
        assert calls == [(train_bin, 2), (replay_bin, 2), (replay_bin, 1)] * 2      <- passed
        assert all(path != val_bin for path, _ in calls)                             <- passed
>       assert recorded == expected, (
E       AssertionError: the recorder saw 2 of the 6 loader draws; unseen per bin: {'/private/var/folders/.../test_offset_stream_hash_covers0/replay.bin': 4}
E         At index 1 diff: '.../train.bin' != '.../replay.bin'
E         Right contains 4 more items, first extra item: '.../replay.bin'
tests/test_phase27_on_draw.py:176: AssertionError
1 failed in 0.97s
```

After threading the replay site: `1 passed in 0.98s`.

The RED was observed on the unconditional spelling (`on_draw=on_draw`). The final spelling (Deviation 1) forwards identically whenever `on_draw` is set, which is the only case this test drives. It was not re-planted to watch it again.

### Task 1 `<automated>` verify

Verbatim, before Deviation 1, with no sweep flag:

```
OK
63 passed in 127.17s (0:02:07)
102.57s call     tests/test_phase23_resume.py::test_production_resume_epsilon_bit_identical
All checks passed!
2 files already formatted
verify exit=0
```

After Deviation 1, on the final spelling:
- The `python -c` check printed `OK`.
- The five golden files were run with `PERSONACORE_SWEEP_ACTIVE=1`: `61 passed, 2 skipped in 24.33s`.
  - Both skips are MPS legs the flag skips: `tests/test_phase23_resume.py:509` and `:694`.
- `ruff check` on all 3 files: `All checks passed!`. `ruff format --check`: `3 files already formatted`.

### Task 1 acceptance criteria

| # | Criterion | Result |
|---|---|---|
| C1 | `grep -c "on_draw=on_draw" loop.py` = 2; `grep -c "on_draw" data.py` ≥ 3; `on_draw` not in `getsource(estimate_loss)` | **PASS**: `2` (loop.py:661, :706); `4`; `False` |
| C2 | diff shows only additions plus call-site lines; no line of `get_batch_fact_aligned` / `estimate_loss` changes | **PASS**, with one nuance (Deviation 5). `22 insertions(+), 2 deletions(-)`. The AST source of `estimate_loss`, `get_batch_fact_aligned` and `_optimizer_step` is identical to d528710 (`True` ×3). Hunks: data.py `-93 +93`, `-108,0 +109,4`, `-117,0 +122,2`; loop.py `-268,0 +269`, `-467,0 +469,7`, `-652,0 +661`, `-692 +701,6` |
| C3 | golden suites 0 failed | **PASS**: 63 passed (verbatim, pre-fix); 61 passed + 2 flag-skipped (final) |
| C4 | `test_phase24_record.py::test_the_provenance_pins_match_the_live_module_bytes` passes | **PASS**: `1 passed in 0.56s`. The whole file also passed inside batch A and the plan-level verification below |
| C5 | ruff clean on both files | **PASS** |

### Task 2 `<automated>` verify and acceptance criteria

```
$ .venv/bin/pytest -q tests/test_phase27_on_draw.py -x --durations=3 && ruff check && ruff format --check && test "$(grep -c 'log_path' ...)" -ge 1
0.47s call     tests/test_phase27_on_draw.py::test_offset_stream_hash_covers_every_draw
0.16s call     tests/test_phase27_on_draw.py::test_rung_chain_stream_equals_one_run
0.07s call     tests/test_phase27_on_draw.py::test_offset_stream_differs_by_seed_and_equals_by_seed
5 passed in 1.23s
All checks passed!
1 file already formatted
task2 verify exit=0
```

- **5 passed, 0 failed, 0 skipped, 1.23 s** (limit 20 s). `grep -c log_path` = 4. `grep -c "train_arm("` = **0**. The file is 244 lines (min 120) with 5 `def test_`.
- The coverage test asserts:
  - the exact 6-call sequence `[(train, 2), (replay, 2), (replay, 1)] × 2`;
  - no val-bin call;
  - the recorder's 6 paths equal the spy's sequence, in order;
  - per-draw byte lengths `[8 × n]`, and the sum `8 × Σn`.
  Its docstring names the no-`log_path` precondition.
- The chain test asserts equal sha256 AND equal draw lists AND `torch.equal` on every adapter tensor.
- **Collected:** `2835 tests collected in 2.97s` after the commit. That is **+5** over 2830 (the count after 27-01), and 2802 + 28 + 5 = 2835. The new file collects `5 tests`.

### RESEARCH A1, measured (`test_rung_chain_stream_equals_one_run`)

- **Reference:** one uninterrupted run, 2 steps, 6 draws.
- **Chain:** link 1 is `max_steps=2, max_steps_override=1, checkpoint_path=ckpt`, which leaves 3 draws, asserted. Then `seed_everything(11)`. Link 2 is `resume_from=ckpt, max_steps_override=2, checkpoint_path=ckpt`, on a freshly built model.
- **Result:** the stream sha256 is equal, the `(bin name, bytes)` draw lists are equal, and every `lora_state_dict` tensor is `torch.equal`: **PASSED**.

Why the re-seed line is there. A scratch probe (not in the tree) wrapped `loop_mod.load_checkpoint` so that it undid the NumPy restore:

```
(b) b_real_reseed:        stream sha equal=True  | adapters equal=True  (24 tensors)
(b) b_norestore_noreseed: stream sha equal=True  | adapters equal=True  (24 tensors)   <- blind
(b) b_norestore_reseed:   stream sha equal=False | adapters equal=False (24 tensors)   <- bites
```

### D-30's un-threaded eval, measured (scratch, not in the tree)

```
(a) with log_path (steps=2, eval_interval=2): loader calls per bin: {'train.bin': 2, 'replay.bin': 4, 'val.bin': 20} | recorder draws: 6
4 steps, eval every step with log_path vs no log_path: draws 12 12 | sha equal True | adapters equal True (24 tensors)
```

With a `log_path`, the recorded stream and the adapters are the same as without one. The eval's val draws never move the training stream on this fixture.

### Regression runs (each invocation, as reported)

| Invocation | Code state | Result |
|---|---|---|
| Task 1 verify, verbatim (5 golden files), no flag | unconditional spelling | 63 passed in 127.17s |
| Batch A, 19 files¹, flag | unconditional | 62 passed, 2 skipped in 63.71s |
| Batch B, 11 files², flag | unconditional | **1 failed**, 215 passed, 14 skipped in 35.41s → Deviation 1 |
| `test_phase21_replay_volume.py` + `test_phase27_on_draw.py`, flag | final | 18 passed in 8.97s |
| 5 golden files, flag | final | 61 passed, 2 skipped in 24.33s |
| Batch A, flag | final | 62 passed, 2 skipped in 63.35s (skips: `test_mps_smoke.py:43` flag; `test_train_loop.py:81` "fp16 AMP smoke needs a CUDA GPU") |
| Batch B, flag | final | 216 passed, 14 skipped in 35.26s (all 14 flag-skipped MPS legs in `test_phase22_checkpoint` / `test_phase22_dpsgd` / `test_phase23_cal03`) |
| 13 `tests/`-walking census files³, flag, before the Task 2 commit | final | 2 failed, 283 passed, 8 skipped in 19.42s. Both failures are porcelain probes naming only `?? tests/test_phase27_on_draw.py` |
| same 13 files, after the commit | final | 285 passed, 8 skipped in 18.93s (all 8 flag-skipped, `test_phase22_fakes.py`) |
| the 11 clean-tree probes by node id, after the commit | final | 10 passed, 1 skipped in 3.20s (the skip is the MPS-gated `test_production_resume_epsilon_bit_identical`) |
| plan `<verification>`: on_draw + lora_training + loop_penalty_fn + phase22_wiring + phase23_resume + phase24_record, flag | final | 49 passed, 2 skipped in 23.07s |

¹ `test_assemble_loss best_ckpt data_split ewc_penalty extra_eval_fns gpt_model gpt_overfit lr_schedule masked_batch masked_train_seam memmap_data mps_smoke overfit_batch resume_curve resume_memmap run_csv_tokens train_loop phase24_record phase27_on_draw`.

² `test_phase14_teaching phase21_aligned_loader phase21_multiplicity phase21_replay_volume phase21_unit_record phase22_checkpoint phase22_dpsgd_ast phase22_dpsgd phase23_cal03 phase23_matched phase23_matched_prereg`.

Together with the 5 golden files, batches A and B cover the orchestrator's six named files and all 32 files `grep -rln "get_batch_memmap_masked\|training.loop\|training import loop\|from personacore.training" tests/` finds. They also add `test_phase23_matched_prereg.py`, which runs the `DP_FN_BRANCH_COUNTS` census over loop.py, and it is green.

³ `test_phase16_driver phase21_filler phase21_sc5 phase21_unit_continuation phase22_fakes phase22_reference phase23_budget phase23_prereg phase23_resume_prereg phase25_points phase25_prereg phase25_probe2 phase25_grid`. These cover the `== 10` wall census, the D-04 bit-identity tripwire and the `train_arm(` register (via `test_phase23_resume.py` above).

The pre-commit porcelain messages, verbatim:
- `AssertionError: ?? tests/test_phase27_on_draw.py`
- `AssertionError: watching the RED must leave no residue in tests/: '?? tests/test_phase27_on_draw.py\n'`

### Plan-level `<verification>`

```
$ git diff --stat HEAD~2 -- scripts/teach_persona.py pyproject.toml      -> (nothing)
$ git diff --name-status d528710 HEAD
M	src/personacore/training/data.py
M	src/personacore/training/loop.py
A	tests/test_phase27_on_draw.py
$ git diff --diff-filter=D --name-only HEAD~1 HEAD                        -> (nothing, after each commit)
```

### Line citations elsewhere in the tree that now point at a different line (disclosed, non-blocking)

Computed from the real diff hunks against d528710. Each old target line's text was checked equal to the text at the mapped new line. No test resolves these, and none of the citing files was edited.

| Citing site | Old → new |
|---|---|
| `scripts/mitigation_unit.py:89` | `data.py:117` → `data.py:121` (the draw) |
| `scripts/phase21_unit_record.py:1003` | `data.py:117` → `data.py:121` |
| `scripts/teach_persona.py:813` | `data.py:125` → `data.py:131` (`y[m == 0] = -100`) |
| `tests/test_phase22_wiring.py:275` | `data.py:112-116` → `data.py:116-120` |
| `src/personacore/training/data.py:362` (self-citation in `get_batch_fact_aligned`'s docstring, bare ``:112-116``) | → `:116-120` |
| `scripts/phase23_matched_prereg.py:236`, `:571` | `loop.py:709` → `loop.py:723` |
| `scripts/phase23_matched_prereg.py:247` | `loop.py:766` → `loop.py:780` |
| `scripts/phase23_matched_prereg.py:256` | `loop.py:781` → `loop.py:795` |
| `scripts/phase23_run.py:1041` | `loop.py:512` → `loop.py:520` |
| `scripts/phase23_run.py:1042` | `loop.py:683` → `loop.py:692` |
| `scripts/phase23_run.py:1116` | `loop.py:531` → `loop.py:539` |
| `tests/test_phase23_cal03.py:17`, `:312` | `loop.py:685-700` → `loop.py:694-714` |
| `tests/test_phase22_checkpoint.py:339` | `loop.py:587` → `loop.py:595` |

Unchanged (18 hits): every citation at or below `loop.py:254` or `data.py:85`. That includes all of `DP_FN_BRANCH_DISPOSITIONS`' `_optimizer_step` sites, `teach_persona.py:2017`'s `loop.py:254`, and `perplexity.py`'s `data.py:84`.

## Files Created/Modified

- `src/personacore/training/data.py` (+7 / -1):
  - signature `..., device, *, on_draw=None`;
  - a 3-line docstring paragraph (D-29 capture point for RELRN-04; `None` changes nothing; the GLOBAL NumPy RNG makes this the only byte-neutral observation point);
  - `if on_draw is not None: on_draw(bin_path, ix)` right after the draw.
- `src/personacore/training/loop.py` (+15 / -1):
  - `on_draw=None` just before `return_final_loss=False`;
  - a 7-line Args entry naming the two threaded sites, the un-threaded `estimate_loss` and why, and "None is inert and not even forwarded";
  - `**({} if on_draw is None else dict(on_draw=on_draw))` at the teaching (:661) and replay (:706) calls.
- `tests/test_phase27_on_draw.py` (244 lines): the plan's 5 exact test names.
  - Local helpers: `_tiny_cfg` (2 layers), `_bins`, `_tree`, `_recorder`, `_named`, `_run`.
  - `_bins` uses a stem-seeded `default_rng`, never the global RNG.

## Decisions Made

See `key-decisions` above. All three were decided by measurement, not by preference.

## Deviations from Plan

### Auto-fixed

**1. [Rule 1 - Bug] The unconditional `on_draw=on_draw` broke a Phase 21 test outside this plan's bounds**
- **Found during:** Task 1 regression batch B.
- **Failing test:** `tests/test_phase21_replay_volume.py::test_replay_seam_draws_exactly_the_public_budget`, with `TypeError: test_replay_seam_draws_exactly_the_public_budget.<locals>.counting() got an unexpected keyword argument 'on_draw'` at `loop.py:699`.
- **Issue:** its fake `counting(bin_arg, mask_arg, batch_size, block_size, device)` has a fixed signature and is patched onto `loop_mod.get_batch_memmap_masked`. The other two patches of that binding take `*args, **kwargs` (`tests/test_masked_train_seam.py:57,94`).
- **Fix:** inside loop.py only, forward `on_draw` only when set: `**({} if on_draw is None else dict(on_draw=on_draw))`. This is loop.py's own precedent at the eval call ("The mask_bin kwarg is only passed when set ... an estimate_loss stub without the kwarg — e.g. tests' fakes — still works"). The default-path call is now literally the pre-Phase-27 call.
- **Criteria after the fix:** the `on_draw=on_draw` grep still prints 2, one per site, and the plan's key_link regex `get_batch_memmap_masked\([\s\S]*?on_draw=on_draw` matches 2.
- **Verification:** 18 passed (replay_volume + on_draw), then golden, A and B all 0 failed.
- **Commit:** `58ee800`.

**2. [Rule 2 - Missing critical] The A1 test could not fail on a missing NumPy restore as specified**
- **Issue:** the plan's chain resumes in the same process. The global NumPy state after link 1 is exactly what the checkpoint saved, so the chain matches even with the restore removed. Measured: `b_norestore_noreseed: stream sha equal=True | adapters equal=True`.
- **Fix:** one line, `seed_everything(11)` before the resume (what a restarted process does). With it, a disabled restore diverges (`False | False`) and the real restore matches (`True | True`).
- **Commit:** `835b1d0`.

### Plan text falsified or inconsistent (followed the code or measurement)

**3. The "draws lists are equal element-wise" check is impossible across fresh trees.** The recorder stores `str(bin_path)`, and three fresh trees have three absolute paths. The equality is asserted on `(bin file name, bytes)` via `_named()` instead. The digest itself never hashes the path, as the plan specifies.

**4. The key_link pattern `on_draw=recorder` matches 0 lines in the test file.** The plan's own Task 2 action spells the callback `cb` (`on_draw=cb`); the file has 6 `on_draw=cb*` uses. The link itself holds: `train(..., on_draw=<recorder callback>)` through the real `train()`, with a spy on `loop_mod.get_batch_memmap_masked`.

**5. C2 nuance: two lines are rewritten in place, not purely added.**
- The data.py signature line, rewritten as prescribed.
- The replay call's one-line argument list. `ruff format` explodes it to one argument per line, because the extra keyword pushes it past 100 columns.

The teaching site is a pure addition.

**6. Plan line numbers vs HEAD d528710:**
- Correct as cited: `data.py:93/:117`; loop.py `:118`, `:235-270`, `:254/:258/:267`, `:646-653`, `:788`, `:858`.
- Off as cited:
  - `estimate_loss` is `:88-129`, not `:98-131`;
  - `_restore_rng(rng)` is `:128`, not `:129`;
  - `target_steps` is `:790`, not `:800`;
  - the in-loop latest save is `:928-947`, not `:925-948`;
  - the end save is `:959-974`, not `:960`;
  - the replay closure is `:685-693`;
  - the fact-aligned `batch_fn` is `:603` with its loader call at `:628`, not `:604`.
- Counts the plan stated and measurement confirmed: "6 loader calls", "sizes 2 and 1".

**7. Helper shape.**
- `_run(tree, ...)` takes the dict from a small `_tree(root)` rather than `root`, so the recorder can be built for the train bin before the run.
- ONE recorder spans both chain links, so "B1 then B2 concatenated" holds by construction. A mid-chain assertion checks 3 draws after link 1.
- `lora_state_dict` (an existing export) is used for the adapter comparison.

---

**Total deviations:** 1 bug auto-fixed (Rule 1), 1 critical test-strength addition (Rule 2), 5 plan-text items followed by the code or measurement.
**Impact:** no scope creep. Nothing outside the three files was touched, and every must-have truth holds.

## Issues Encountered

- **Two MPS-gated legs ran on this host.** The plan's Task 1 `<automated>` verify was run verbatim, before the sweep flag was adopted, and it executed `tests/test_phase23_resume.py::test_production_resume_epsilon_bit_identical` (102.57 s, PASSED) and `::test_cross_device_resume_is_refused_mps_runtime` (PASSED) on MPS. Both ran on the pre-Deviation-1 spelling.
  - Every later run used `PERSONACORE_SWEEP_ACTIVE=1` (D-44's flag), so nothing else touched MPS, per the brief.
  - Those two legs were not re-run on the final spelling. For `on_draw=None`, that spelling differs only by passing no keyword at all. The orchestrator's full suite covers them.
- **`tests/test_phase25_venue.py` was not run.** It executes the whole suite twice in subprocesses. The 5 new tests add no MPS leg and no skip, so its skip-count literals should not move. The full-suite run is the check.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **27-03:** call `tp.train(..., on_draw=recorder)`.
  - Tag bins by path equality against the train bin, as `_recorder` does.
  - Hash `ix.astype("<u8").tobytes()` plus the tag, never the path.
  - Stream identity across rungs is measured for a 1→2 resume on CPU, including a re-seed between links.
  - With `log_path` and `eval_interval=1`, the stream and adapters equal the no-log run (scratch, 4 steps).
- **The recorder must accept `(bin_path, ix)`.** A loader fake patched onto the loop binding must accept `on_draw` only when a caller passes one.
- **No ledger edits.** STATE.md, ROADMAP.md and REQUIREMENTS.md are untouched. No gsd-sdk mutation handler was called, and RELRN-04 is not ticked (D-05, D-38).
- **Obsidian:** this subagent has no Obsidian MCP tool, so the vault entry for this plan is PENDING. It has not been saved.

## Self-Check: PASSED

- `tests/test_phase27_on_draw.py` FOUND. `src/personacore/training/data.py` and `loop.py` modified at `58ee800`.
- Commits `58ee800` (feat) and `835b1d0` (test) FOUND in `git log --oneline -3` on `main`, on top of `d528710`.
- Collected 2835 (+5); plan verification 49 passed / 2 flag-skipped / 0 failed.

---
*Phase: 27-relearning-attack*
*Completed: 2026-09-16*
