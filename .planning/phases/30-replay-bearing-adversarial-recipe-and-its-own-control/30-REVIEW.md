---
phase: 30-replay-bearing-adversarial-recipe-and-its-own-control
reviewed: 2026-09-25T18:43:33Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - scripts/phase30_calibration.py
  - scripts/phase30_points.py
  - scripts/teach_persona.py
  - tests/test_phase22_wiring.py
  - tests/test_phase23_resume.py
  - tests/test_phase27_relearn.py
  - tests/test_phase29_prereg.py
  - tests/test_phase30_calibration.py
  - tests/test_phase30_points.py
  - tests/test_phase30_seam.py
  - results/phase30_calibration.json
  - tests/fixtures/phase30_train_kwargs_presplit.json
findings:
  critical: 1
  warning: 6
  info: 4
  total: 11
status: issues_found
---

# Phase 30: Code Review Report

**Reviewed:** 2026-09-25T18:43:33Z
**Depth:** standard
**Files Reviewed:** 12 (the fixture was skimmed only: metadata, `captured_at_sha` = a9d0d5d, one commit 47ed88b)
**Status:** issues_found

## Summary

Diff base a9d0d5d..HEAD over scripts/ src/ tests/ results/. Baseline: the 54 Phase-30 and
touched-guard tests pass (`.venv/bin/pytest -q tests/test_phase30_*.py
tests/test_phase29_prereg.py::test_paths_are_distinct_from_every_v4_path
tests/test_phase27_relearn.py::test_provenance_digests_match_live_bytes
tests/test_phase27_relearn.py::test_the_superseded_pin_continuation_is_a_tripwire` gives `54 passed
in 29.46s`). Ruff check and format are clean on every reviewed file.

**What I checked and found no problem with:**
- The `is_dp`/`gets_replay` split. `train()` defaults `fact_bin`, `n_facts` and `dp_fn` to None, so passing explicit `None` for `advr_*` changes nothing.
- The replay weighting. `loop.py` replay_fn draws exactly `replay_windows` per step, with the loss weighted `micro / replay_windows`, so the 1:1 claim in the record holds.
- The D-05 formula in `derive()`. It matches `phase24_adversarial.py:83-96`.
- The provenance pins in `results/phase30_calibration.json`. Every pin equals the live file hash. teach_persona.py is `aabf4381…` at f8959ea, 53a62b2 and HEAD, blob `4c9a658`.
- The phase24 re-emit. It moved only provenance and names the ancestor f8959ea.
- The phase27 dated-continuation tripwire.
- The v4.0-tag anchor. CI uses `fetch-depth: 0`, so the tag is present.
- The n=8 worst-corner premise of D-06, which I measured. A live re-derivation at `advr_n64` gives floor **14**, and `advr_n8` gives **15**, so n8 is the binding leg.

**What is wrong:**
- The one BLOCKER is the "tracked only" guard in `phase30_points`, which reads uncommitted working-tree bytes.
- Most warnings are gaps between evidence and claims. Examples: the calibration's byte-identity "evidence" never exercises `build_arm_bins`; the seam test checks an aggregate while the write-once record cites it as a per-step count; an `advr` run logs `replay_ratio=0.0` and no replay count.

Every finding below was reproduced with the command shown. All scratch artifacts were placed under
the session scratchpad. No source, test or results file was modified.

## Critical Issues

### CR-01: The "tracked only" guard accepts a locally edited record

**File:** `scripts/phase30_points.py:183-189` (reached from `calibration_record` :192, `require_calibrated_recipe` :204, `own_control` :218, and therefore `next_action` :264)

**Issue:** `_tracked_json` checks only that `rel` is in the caller-supplied `tracked` list (i.e. `git ls-files`), then reads `(_ROOT / rel).read_text()`, which is the working-tree bytes. Its own refusal text says: "Only a committed record is read: one borrowed from the working tree could move after the fact." That is exactly the case it lets through. If a tracked file is modified and not committed, the guard still passes. SC2's "scoring refuses a point whose recipe differs from the calibration's" and D-16's control-recipe check then compare against bytes that no commit holds.

Reproduction (a scratch git repo with a committed record, then edited but not committed):
```
$ S=.../scratchpad/trk1; mkdir -p $S/results; cd $S; git init -q
$ echo '{"v":"committed"}' > results/phase30_calibration.json; git add .; git commit -qm c
$ echo '{"v":"EDITED-UNCOMMITTED"}' > results/phase30_calibration.json
$ .venv/bin/python -c "...; p._ROOT=pathlib.Path('$S'); tracked=git ls-files; print(p.calibration_record(tracked))"
git status: M results/phase30_calibration.json
read: {'v': 'EDITED-UNCOMMITTED'}
```

**Fix:** Read the committed blob, not the file on disk (or refuse a dirty path):
```python
def _tracked_json(rel, tracked, what):
    _prove(rel in set(tracked), ...)
    blob = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=_ROOT,
                          capture_output=True, text=True, check=True).stdout
    _prove(blob == (_ROOT / rel).read_text(encoding="utf-8"),
           f"{what} {rel} differs from its committed blob — refusing a working-tree edit")
    return json.loads(blob)
```
The tests fake `tracked` over a tmp `_ROOT` with no git repo, so they would need a real tmp repo, or an injectable reader.

## Warnings

### WR-01: The calibration's byte-identity "evidence (1)" is equal inputs to a pure function and never runs `build_arm_bins`

**File:** `scripts/phase30_calibration.py:105-152`, `scripts/teach_persona.py:1264-1266`; the claim is committed in `results/phase30_calibration.json` `derivation.structural_reason`

**Issue:** `arm_spec("advr_n8")` returns `arm_spec("adv_n8")` by call. `derive()` then feeds both triples into the same `tp.build_bins(...)` call, which it wrote out by hand ("Argument for argument, build_arm_bins' flat-branch call"). Byte equality is therefore guaranteed by construction. It can only fail if `arm_spec` diverges, which `test_replay_arms_mirror_their_adv_twin_spec` already pins. The claim it is filed under is "replay stays out of the teaching bin". That depends on the path that actually writes a trained arm's bins (`train_arm` → `build_arm_bins`), and `derive()` never calls it. The hand-copied argument list can also drift from `build_arm_bins`' real call with nothing going red.

Reproduction (replace `build_arm_bins` with a function that raises; `derive()` still certifies):
```
$ .venv/bin/python -c "...; tp.build_arm_bins=broken; d=cal.derive(); print(...)"
derive OK, floor 15 identical True
```

**Fix:** The record is write-once, so do not edit it. Instead, add a Phase-30 test that drives `train_arm("advr_n8", adversarial_ratio=grid[-1])` under `_e2e_env`, with `tp.train` spied (the `_capture` idiom already in `test_phase30_seam.py`). Hash the bins it actually wrote and compare them with the `adv_n8` twin's. Also add a test asserting that `derive()`'s `build_bins` kwargs equal the ones `build_arm_bins` passes, for example by spying `tp.build_bins` during a `build_arm_bins` call. That closes the drift of the hand-copied argument list. Record the correction as a dated continuation.

### WR-02: D-04 says "per step", but the test asserts only the run total, and the write-once record cites it as a per-step count

**File:** `tests/test_phase30_seam.py:210-226`; cited in `results/phase30_calibration.json` `structural_reason` ("counts phase29_prereg.replay_windows(n) replay windows per step")

**Issue:** The assertion is `drawn["replay"] / tp.MAX_STEPS == replay_windows(n) > 0`. `_e2e_env` sets `MAX_STEPS = 2` (`tests/test_phase22_wiring.py:779`), so a run that draws 64 on step 0 and 0 on step 1 passes. The implementation is correct today: `replay_fn` loops until exactly `replay_windows` per call. So this is not a wrong result, but the instrument cannot tell per-step from total, and the record states the stronger claim.

Reproduction:
```
$ .venv/bin/python -c "per_step=[64,0]; MAX_STEPS=len(per_step); replay_windows=32
print('test predicate passes:', sum(per_step)/MAX_STEPS == replay_windows > 0, '| per-step equality holds:', all(x==replay_windows for x in per_step))"
test predicate passes: True | per-step equality holds: False
```

**Fix:** Bucket the draws by optimizer step. For example, wrap `on_draw` so that a teaching draw of `BATCH_SIZE` windows (one per step at accum=1) closes a bucket, then `assert per_step_replay == [replay_windows(n)] * tp.MAX_STEPS`.

### WR-03: An `advr` training run logs `replay_ratio=0.0` and never logs its replay count (SC1 says "logs")

**File:** `scripts/teach_persona.py:2054-2061` (the DP-only provenance print), `:2112-2123` (run provenance), `:2124-2132` (return blob)

**Issue:** SC1 says "a CPU run of the adversarial arm **logs** a non-zero replay count equal to the PREREG-04 recipe". Only the `is_dp` branch prints `replay_windows`. On an `advr_*` run the only replay token in stdout is `replay_ratio=0.0`, which reads as "no replay". The returned blob, which `phase25_points.train_stage` copies into the training sidecar, carries no `replay_windows` either. A Phase 32 `advr` point's own artifacts will therefore not show that replay ran. They cannot be told apart from an `adv` point on this axis.

Reproduction (a real CPU `advr_n8` run):
```
$ .venv/bin/pytest -q -s "tests/test_phase30_seam.py::test_advr_draws_the_prereg_replay_count[advr_n8]" | grep -o "replay[_a-z]*=[^ ]*\|DP provenance\|passed.*"
replay_ratio=0.0
passed: all lora_ moved, base bit-untouched
replay_ratio=0.0
passed in 3.20s
```

**Fix:** Print `replay_windows={dp_kwargs.get('replay_windows')}` in the run-provenance line whenever `gets_replay` is true, and add `"replay_windows": dp_kwargs.get("replay_windows")` to the return dict. This is additive: the value is None for arms without replay, and the adv/DP `train()` kwargs are unchanged. It does change teach_persona.py, though, so the phase27 `_SUPERSEDED_PINS` tripwire and the phase24 record pin need a dated continuation or a re-emit. Record the fix in the same way.

### WR-04: The D-16 "identical budget and seed" check reads the control's self-declared `recipe`, not what it actually trained with

**File:** `scripts/phase30_points.py:234-238`

**Issue:** `own_control` compares `record["recipe"]` with `point_recipe`, and nothing else from the control's training provenance. A control record whose `train_config.max_steps`, `seed` and `live_mechanism.composed_steps` show a different run is accepted, provided its `recipe` field was written correctly. D-16 says the check is "CHECKED AT READ TIME, per point … Not by construction". Comparing a field the writer declares is by construction.

Reproduction:
```
$ .venv/bin/python -c "...; rec=T._good_control('n8'); rec['train_config']={'max_steps':7,'seed':1}; rec['seed']=1; rec['live_mechanism']={'composed_steps':7}; ...; got=p.own_control(...)"
accepted control trained at max_steps 7 seed 1 ; recipe says 200 1337
```

**Fix:** In `own_control`, also require `record["seed"] == point_recipe["seed"]`, `record["train_config"]["max_steps"] == point_recipe["max_steps"]` and `record["live_mechanism"]["composed_steps"] == point_recipe["max_steps"]`. Once WR-03 lands, also check the recorded replay count against `point_recipe["replay_windows"]`, so the measured fields and the declared ones must agree.

### WR-05: `write_refused_records` is not atomic across files, so a failure part-way leaves the leg permanently unwritable

**File:** `scripts/phase30_points.py:289-294`

**Issue:** The overwrite refusal runs once, before the loop. Each record is then written separately. If the process is interrupted or fails after file k of 5 (kill, full disk, a serialisation error), a retry is refused because k files already exist. The leg is left half-REFUSED, and the only way out is a manual delete of write-once evidence. D-12's short-circuit is meant to write the whole leg.

Reproduction (tmp `_ROOT`; the second record is made unserialisable to simulate the failure):
```
$ .venv/bin/python -c "...; recs={keys[0]:{'ok':1}, keys[1]:{'bad':object()}}; p.write_refused_records(recs) ...; retry"
first call: TypeError
on disk: ['phase32_point_advr_n8_ratio0p250000.json']
retry: [phase30_points] REFUSING to overwrite existing record(s) ['/private/tmp/.../phase32_point_advr_n8_ratio0p250000.json'
```

**Fix:** Serialise every blob first (`json.dumps` all of them, so a bad value fails before any write). On retry, accept a file that already exists only if it is byte-identical to the blob about to be written, and write only the missing ones. Also require that `set(records)` equals the leg's non-control keys.

### WR-06: The WR-05 AST guard misses an aliased import and `getattr`

**File:** `tests/test_phase30_points.py:447-488`

**Issue:** The v4.0 parser check matches only `phase25_points.<attr>` spelled with the literal name `phase25_points`. `import phase25_points as p25; p25.point_plan(...)` passes clean. So does `getattr(phase25_points, "control_key_for")`, and so does a dp key built by concatenation. D-14 says the guard "reddens if any v5.0 module calls `control_key_for`". Phases 31-34 will add modules under this census.

Reproduction:
```
$ .venv/bin/python -c "from test_phase30_points import _wr05_failures; ..."
'import phase25_points as p25\n_X = p25.point_plan("adv_n8_rat' -> []
'_X = "dp_n" + "8"\n' -> []
'import phase25_points\n_X = getattr(phase25_points, "control_key_for")\n' -> []
'import phase25_points\n_X = phase25_points.point_plan\n' -> ['v4.0 parser phase25_points.point_plan at line 2']
```

**Fix:** Collect the aliases from `ast.Import` nodes (`alias.asname or alias.name` for `phase25_points` and `phase25_promotion`) and match `Attribute.value.id` against that set. Also flag any string `Constant` that equals a name in `_CARRIERS`, which covers `getattr` and `importlib` forms. Add both to `test_ast_guard_planted_red_per_class`.

## Info

### IN-01: The new register entry splits the "THIS file" comment from the entries it describes

**File:** `tests/test_phase23_resume.py:131-141`

**Issue:** The comment `# THIS file — the only place ALLOWED to pass resume_from…` now sits directly above the `tests/test_phase30_seam.py` tuple, which is the one entry that passes no `resume_from`. `sed -n 128,143p tests/test_phase23_resume.py` shows the order.

**Fix:** Move the 30-01 comment and its tuple above the "THIS file" comment.

### IN-02: The provenance of the "structural reason" does not pin the module that makes it true

**File:** `scripts/phase30_calibration.py:53-62`

**Issue:** `PINNED_MODULES` hashes teach_persona, phase24, phase29, phase30_points and the emitter. It does not hash `src/personacore/training/loop.py`, whose `replay_fn` (one replay mean per step, weighted 1:1, outside the bin) is the structural reason the record states. It does pin `scripts/phase30_points.py`, and by the 2026-09-25 ruling that file keeps changing through Phases 31-34. That pin will go stale, and no test compares it. Neither makes the record wrong; each weakens what its provenance can support.

**Fix:** When this is next corrected (as a dated continuation), pin `loop.py`, and note in the record's reader that the `phase30_points.py` pin is informational.

### IN-03: The calibration derives the floor at n=8 only; the n=64 floor is not recorded

**File:** `scripts/phase30_calibration.py:97`, `results/phase30_calibration.json` `recipe.n64.min_refusal_scored_tokens`

**Issue:** This follows D-06, which asks for the worst corner. I measured the premise live: `advr_n8 {'S': 2719, 'T0': 7581, 'P': 336, 'prompt': 26054} floor 15`, and `advr_n64 {'S': 28128, 'T0': 72093, 'P': 2688, 'prompt': 208432} floor 14`. n8 does bind, but the record states 15 for n64 with no derivation for that leg. Command: `.venv/bin/python scratchpad/n64.py` (the same computation as `derive()`, looped over `ADVR_ARMS`).

**Fix:** A future dated continuation could record the n64 inputs and floor alongside n8.

### IN-04: `recipe_identity` ignores the module named in `REPLAY_SOURCE`

**File:** `scripts/phase30_points.py:93-96`

**Issue:** `getattr(tp, name.split(".", 1)[1])` drops the module prefix. A pre-registration naming `other_module.X` would silently resolve against teach_persona.
```
$ .venv/bin/python -c "...; q.REPLAY_SOURCE=('some_other_module.DIALOG_TRAIN_BIN','nonexistent.DIALOG_TRAIN_MASK'); print(p.recipe_identity('n8')['replay_source'])"
['data/dialog_train.bin', 'data/dialog_train_mask.bin']
```

**Fix:** `mod, attr = name.split(".", 1); _prove(mod == "teach_persona", ...)`.

---

_Reviewed: 2026-09-25T18:43:33Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
