---
phase: 32-replay-bearing-frontier-re-run-and-verdict
reviewed: 2026-09-28T16:30:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - scripts/phase32_points.py
  - scripts/phase32_frontier.py
  - scripts/phase30_points.py
  - tests/test_phase32_points.py
  - tests/test_phase32_frontier.py
  - tests/test_phase32_live.py
  - tests/test_phase30_points.py
  - tests/test_phase30_calibration.py
  - artifacts/com.personacore.phase32.sweep.plist
findings:
  critical: 1
  warning: 5
  info: 7
  total: 13
status: issues_found
---

# Phase 32: Code Review Report

**Reviewed:** 2026-09-28T16:30:00Z
**Depth:** standard
**Files Reviewed:** 9 (phase30_points.py and the two test_phase30_* files reviewed on `git diff 59ce590 HEAD` only)
**Status:** issues_found

## Summary

I reviewed the v5.0 sweep driver, the frontier assembler, the Phase 32 changes to `phase30_points` (D-19 WR-04 and D-10 IN-04), the D-17 continuation of the AST guard, the three Phase 32 test modules and the LaunchAgent plist. I checked them against CONTEXT D-01..D-20 and against the committed `results/phase32_point_*.json` (12 records) and `results/phase32_frontier.json`.

**Impact on committed data: none found.** Every finding below is **latent** for the committed records and frontier, with one exception. WR-02 affects only the *completeness* of the committed frontier's `provenance.module_sha256` block. It does not affect any number or verdict. I verified the following:
- `git diff --name-only ae0ed837 e35654c` covers the whole sweep, from the launch commit to the last PREREG-03 commit. It touches only the 12 `results/phase32_point_*.json` files, so no pinned or unpinned code changed mid-run. That neutralises CR-01 and WR-01 for these records.
- All 7 trained records carry an identical `module_sha256` block.
- The n8 control's own dialogue gap is +0.134325, which is > 0, so WR-04 was not reached.
- Each record was committed in the same session that wrote it (one session sha per record, `head_at_write` equal to the session sha), so WR-05's pending-commit path was never exercised.
- The frontier's `statement`, `by_leg` counts (n8 k5=0, k6=1, v4 0 of 6; n64 PREREG-03 with taught 0/1008, held-out 1/648) and quoted v4 reasons are consistent with D-14/D-15/D-18.

**Pin cost of fixes.** `phase32_points.py` is hashed into all 7 trained records' `provenance.module_sha256` and is itself in `PINNED_MODULES`. `phase32_frontier.py` is hashed into the committed frontier. `phase30_points.py` is under the `_SUPERSEDED_PINS` tripwire in `tests/test_phase30_calibration.py`. Any edit to these three scripts therefore needs a dated pin continuation: a fix commit plus a SHA-registration commit, following the Phase 32 D-19 pattern. Because the sweep and frontier are write-once and already committed, the fixes for CR-01, WR-01, WR-02 and WR-04 matter only if these modules are reused, for example by Phase 33 or a re-run. They can reasonably be recorded as carried items instead of being fixed now. WR-03 touches only `tests/test_phase30_points.py`, which is not module-pinned, so it has no pin cost.

## Critical Issues

### CR-01: D-08 never compares against the commit the running code was loaded from; module hashes are read from disk at write time

**File:** `scripts/phase32_points.py:62, 340-349, 397, 617, 641`
**Issue:** D-08 promises that a record is refused when "the pinned modules differ between the commit where the stages ran and HEAD at write time." The check covers the wrong commit. Only one process runs the whole ~23 h sweep, and it:
- imports the code once: `INSTRUMENT_GIT_SHA = git_sha()` at import, and `teach_persona`/torch modules lazily at the first `run_point`;
- calls `record_session(key)` before each point, which records the *current* `git rev-parse HEAD`, not the commit the in-memory code came from;
- takes `training["git_sha"]` from `phase25_run.head_sha()` at train time, which is also the current HEAD;
- runs `prove_pinned_unchanged([*session_shas, training_sha])`, which diffs those against HEAD. `INSTRUMENT_GIT_SHA` is **not** in the list;
- computes `provenance.module_sha256` as `_sha256(_CODE_ROOT / rel)` from disk at write time.

Suppose someone commits a change to a pinned module while the sweep is running. The project memory records that peer agents do commit mid-session. From the next point onward, session sha = training sha = HEAD = the new commit, so D-08 passes. The record then pins `module_sha256` for bytes that never ran, because the process still executes the old imported code. `refuse_if_dirty` does not catch this, since the tree is clean after a commit. The record's `provenance.git_sha` (the import-time sha) would contradict its `sessions`, but nothing checks that relationship. This is exactly the WR-02 class D-08 was meant to close.

**Committed data:** latent. `git diff --name-only ae0ed837 e35654c` lists only point records. All 7 trained records share one `module_sha256` block, and `provenance.git_sha` = ae0ed837 on every one.

**Fix:** capture the hashes at import time, include the import-time sha in the D-08 set, and prove that the disk still matches the import:
```python
INSTRUMENT_GIT_SHA = git_sha()
_IMPORT_MODULE_SHA256 = {rel: _sha256(_CODE_ROOT / rel) for rel in PINNED_MODULES}  # after PINNED_MODULES
...
# write_point_record
prove_pinned_unchanged([INSTRUMENT_GIT_SHA, *shas, record["training"]["git_sha"]])
# run_point provenance
"module_sha256": dict(_IMPORT_MODULE_SHA256),
```
(`_sha256` must be defined above `PINNED_MODULES`, or the dict must be built lazily at the first `run()`.) Pin cost: this edits `phase32_points.py`, which is pinned in 7 committed records and in its own `PINNED_MODULES`, so it needs a dated continuation. Recording it as a carried item for any Phase 33 reuse is acceptable.

## Warnings

### WR-01: `PINNED_MODULES` omits modules that change the stages' numbers

**File:** `scripts/phase32_points.py:64-94`
**Issue:** The stated scope (line 64) is "a file is pinned when its bytes can change a stage's numbers." The stages import these modules, but the tuple leaves them out:
- `src/personacore/generation/{sampling,core,text}.py`: recall draws and attack draws.
- `src/personacore/evaluation/perplexity.py`: condition (c) PPL.
- `src/personacore/tokenizer/*.py`: every encode and decode.
- `src/personacore/dialogue/*.py`: recall prompts and dialogue encoding.
- `src/personacore/checkpoint.py`: `load_adapter`, `load_slim` and `export_adapter`.
- `src/personacore/config.py`.
- `src/personacore/training/{loss,schedule}.py`.
- `src/personacore/seeding.py`.
- `scripts/phase25_prereg.py`.

A committed change to any of these between sessions passes D-08 silently and is invisible in `module_sha256`. Only the whole-commit `git_sha` would reveal it.

**Committed data:** latent. No file outside `results/phase32_point_*` changed during the sweep (verified above).

**Fix:** derive the list instead of typing it. For example, pin every `src/personacore/**/*.py` plus the `scripts/` modules the stages import:
```python
_SRC_MODULES = sorted(p.as_posix() for p in (pathlib.Path(_SRC) / "personacore").rglob("*.py"))
```
Pin cost: same as CR-01, because this edits `phase32_points.py`.

### WR-02: The frontier's `module_sha256` does not pin the gate that produced its verdicts

**File:** `scripts/phase32_frontier.py:64-73`
**Issue:** `PROVENANCE_MODULES` hashes `phase32_frontier`, `phase25_verdict`, `phase25_promotion`, `phase20_gate_coverage` and `phase29_prereg`. The verdict functions actually live in `mitigation_gate.py` (`dialogue_gap_band`, `REPLICATION_PENDING_MARKER`; CONTEXT's canonical refs call it "the frozen route") and in `erasure_gate.py`, which `phase20_gate_coverage` and `phase25_verdict` import. The verdict kwargs come from `phase25_condition_c` and `phase25_gate05`. `phase25_record` (v4 key derivation) and `phase30_points` (`_tracked_json`, `CALIBRATION_PATH`) are also used. None of these is hashed.

**Committed data:** this affects the committed frontier's provenance block, which is incomplete. It does **not** affect any verdict or number: `provenance.git_sha` = fd76e0d2 pins the full tree, and `test_recompute_committed_frontier_both_states` recomputes the frontier byte-for-byte from HEAD.

**Fix:** add the missing modules to `PROVENANCE_MODULES`:
```python
mitigation_gate.__file__, erasure_gate.__file__, phase25_condition_c.__file__,
phase25_gate05.__file__, phase25_record.__file__, phase30_points.__file__,
```
These modules need to be imported first. Pin cost: this edits `phase32_frontier.py`, which is hashed in the committed write-once frontier. Apply it only with a continuation, or carry it and document in Phase 34 that `git_sha` is the authoritative pin.

### WR-03: The D-17 exemption lets the carrier through via `vars(mod)[...]` / `mod.__dict__[...]`

**File:** `tests/test_phase30_points.py` (the `json_key_ids` block added to `_wr05_failures`)
**Issue:** The exemption accepts **every** `Subscript` whose slice is the constant `"control_readings"`, whatever is being subscripted. I confirmed it by running the guard, with `import phase25_promotion` prepended:
```
_X = vars(phase25_promotion)["control_readings"]        -> []   (no failure)
_X = phase25_promotion.__dict__["control_readings"]     -> []   (no failure)
```
Both forms fetch the v4.0 carrier function, which is exactly what `getattr(phase25_promotion, "control_readings")` does, and the guard still flags `getattr`. D-17 intended the exemption for JSON-field positions only, but this is a module-attribute read that the planted-RED set does not cover.

**Committed data:** latent. No script uses either form.

**Fix:** exempt a subscript only when its value is not a module namespace. At minimum, flag a `Subscript` whose `value` is `Call(Name('vars'|'globals'))`, `Attribute(attr='__dict__')`, or a `Name` bound to a `_V4_MODULES` import. Add both lines above as planted-RED cases. This file is not module-pinned, so there is no pin cost.

### WR-04: A non-positive own-control dialogue gap crashes the frontier with an unhandled `ValueError`

**File:** `scripts/phase32_frontier.py:181-194`; `scripts/phase32_points.py:611-615`
**Issue:** With replay, the advr control's own `adapter_on - adapter_off` can be ≤ 0, because replay trains on dialogue. The 32-05 fixture measured -0.0022 and had to force it positive. `run_point` records such a gap without complaint (`control_gap_for_capacity` is plain subtraction). At the frontier, however, the frozen `mitigation_gate.dialogue_gap_band` raises `ValueError`, and `build_frontier` handles only `SystemExit`. `emit` would then die with a raw traceback. No `V5_STATES` entry or template covers "control gap non-positive", so D-15's "every state is enumerated" does not hold for this reachable state.

**Committed data:** latent. The advr_n8 control gap is +0.134325, and the n64 leg refuses on floors before the band is reached.

**Fix:** refuse by name before routing, so the outcome is a documented refusal instead of a crash:
```python
gap = by_twin[twins[leg]]["adapter_on"] - by_twin[twins[leg]]["adapter_off"]
_prove(gap > 0, f"advr_{leg}: own control dialogue gap {gap} <= 0; the frozen (c) band is undefined (no template covers it)")
```
Alternatively, add a named v5 state and template for it. Pin cost: this edits `phase32_frontier.py`, which is pinned in the committed frontier.

### WR-05: The interrupted-commit path commits an on-disk record without re-validating it

**File:** `scripts/phase32_points.py:666-672, 698-708`
**Issue:** `_run_excludes()` removes `results/phase32_point_*.json` from the start-of-run dirty check. The pending branch then commits any untracked point record whose JSON parses and is not `PREREG-03`. It does not check the schema, the point key, D-08 against the current HEAD, or whether the file is still the one `write_point_record` produced. A record hand-edited or corrupted between the crash and the relaunch would therefore be committed as a finished sweep point. From then on the D-03 clock, own-control reads and the frontier would all consume it.

**Committed data:** latent. Each record's single session sha equals its `head_at_write`, and the commit timestamps follow each write directly, so the pending path never fired.

**Fix:** before `commit_untracked`, check each pending record for `schema == SCHEMA`, `point_key == key_of[rel]` and `stages` present, and re-run `prove_pinned_unchanged` over its `provenance.sessions` plus `training.git_sha`. For stronger protection, `write_point_record` can write a digest sidecar in `data/` and the pending path can verify it. Pin cost: edits `phase32_points.py`.

## Info

### IN-01: Empty ruling accepted by `--past-stop-line`

**File:** `scripts/phase32_points.py:716-724, 780-788`
**Issue:** `--past-stop-line ""` is not `None`, so an empty ruling passes the checks and is recorded as `past_line_ruling: ""`. D-06 requires the developer's ruling *text*. Latent: every record has `past_line_ruling: None`.
**Fix:** `_prove(past_stop_line is None or past_stop_line.strip(), "an empty ruling is not a ruling (D-06)")`.

### IN-02: `stop_line_seconds` rejects an integral JSON value

**File:** `scripts/phase32_points.py:322-325`
**Issue:** `isinstance(value, float)` refuses a valid positive stop line serialized as an integer, for example `136000`. Latent: the committed value is a float.
**Fix:** `isinstance(value, (int, float)) and not isinstance(value, bool)`, then `float(value)`.

### IN-03: Calibration-descent logic is duplicated and proves only the oldest add

**File:** `scripts/phase32_frontier.py:478-493`, `scripts/phase32_points.py:481-497`
**Issue:** The same function appears in both modules. `adds[-1]` is the *oldest* `--diff-filter=A` commit, so if the calibration file were ever deleted and re-added, ancestry would be proven for a blob other than the current one. Latent: it was added once.
**Fix:** keep one helper (the frontier can import `phase32_points.calibration_descent`), and use `adds[0]` or refuse `len(adds) > 1`.

### IN-04: The sweep heartbeat shares the Phase 25 file

**File:** `artifacts/com.personacore.phase32.sweep.plist:40-41`; `scripts/phase32_points.py:679, 779`
**Issue:** `data/phase25_heartbeat.jsonl` interleaves v4.0 and v5.0 beats. Only the point key tells them apart, so a stall reader that inspects the last line without filtering could misattribute a stale v4 beat.
**Fix:** use a `data/phase32_heartbeat.jsonl` default.

### IN-05: The frontier's dirty check uses `_GIT_ROOT` while its module hashes use `_ROOT`

**File:** `scripts/phase32_frontier.py:506-514, 534`
**Issue:** `phase32_points` deliberately sends the dirty check to `_CODE_ROOT` (never patched). The frontier sends it to the patchable `_GIT_ROOT`, so under test patching the code tree is not dirty-checked. The two paths are identical in production.
**Fix:** `cwd=_ROOT` for the scripts/src part of the check, mirroring `phase32_points`.

### IN-06: Recompute and ancestry tests now carry dead branches

**File:** `tests/test_phase32_frontier.py:666-697`
**Issue:** Now that `results/phase32_frontier.json` is tracked, the `not _is_tracked` branches never run. In particular, the forged-records determinism check (`first == second`, no provenance/sources keys) no longer runs anywhere.
**Fix:** move the forged determinism assertion into its own unconditional test.

### IN-07: The past-line ruling is not carried on PREREG-03 records

**File:** `scripts/phase32_points.py:747-752`
**Issue:** D-06 says the ruling is "recorded in the provenance of every point run after it". `write_refused_records` writes the frozen `phase29_prereg.refused_record` shape, which has no provenance, so a leg refused after a ruling does not record it. Arguably those points are not "run". Latent: no ruling was ever given.
**Fix:** document that PREREG-03 records are outside D-06's scope, or record the ruling in the commit message for refused records.

---

_Reviewed: 2026-09-28T16:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
