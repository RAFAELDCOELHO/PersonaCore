---
phase: 40-m2-seed-noise-floor
reviewed: 2026-10-06T16:30:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - scripts/phase40_noise.py
  - tests/test_phase40_noise.py
findings:
  critical: 0
  warning: 4
  info: 6
  total: 10
status: issues_found
---

# Phase 40: Code Review Report (E2 driver, pre-launch)

**Reviewed:** 2026-10-06T16:30:00Z
**Depth:** standard (every recovery path the orchestrator named was run in a tmp-root experiment)
**Files Reviewed:** 2
**Status:** issues_found

## Summary

I reviewed `scripts/phase40_noise.py` at HEAD 4c1547d. Its sha256 is `34cc936a…f4ed`, the same digest that `data/phase40_rehearsal.json` records, so the driver has not changed since the CPU rehearsal (`git log dfa1162..HEAD -- scripts/ src/` is empty). The frozen prereg is still `a81c79dc…`. Baseline: `.venv/bin/pytest tests/test_phase40_noise.py -q` gives **133 passed in 25.23s**.

**There are no BLOCKERs.** I ran each named recovery path against tmp roots. Every one ends with the ledger, records, adapters and dropped-attempt evidence in the state the rulings require. Four WARNINGs remain:

- Two are guard gaps, each reachable only through a wrong operator step or a non-CLI call. One can still cost a seed plus its MPS hours (WR-01). The other can write the write-once record from the wrong ledger (WR-02).
- One is a hole in ruling c's catch. Its mechanism is measured; its real-world trigger is a hypothesis (WR-03).
- One is a provenance gap, measured (WR-04).

**Experiment harness.** All new experiments are in the session scratchpad: `<scratch>/test_review40.py`, where `<scratch>` is `/private/tmp/claude-501/-Users-juliorcoelho-PersonaCore/d19c6c2a-db59-41c1-946c-681523a61ee9/scratchpad`. The file reuses the test file's own rigs (`_tmp_rig`, `_real_root_rig`, `_run_fakes`, `_drop`). It also adds an autouse guard that asserts `git status -- results ledger` and the real `data/` and `checkpoints/` phase40 outputs are unchanged around every experiment, and every experiment passed that guard. Run it with:
`.venv/bin/pytest <scratch>/test_review40.py -q -s -p no:cacheprovider --rootdir <scratch> -k <id>`

### Recovery paths checked (evidence)

| Path | Experiment | Observed |
|---|---|---|
| Crash between the seed record and the end line | `-k e1` | `E1 after crash: ledger [start 1337, end 1337, start 2024]`, `open ['v6/40/E2/seed2024']`, `seed record 2024 exists True`. Rule (i), append end by command: `outcomes {1337: whole, 2024: whole, 1338: not_run}`, relaunch `[1338]`, all whole. Reconcile done by mistake instead: see WR-01. |
| Crash inside train_full / train_m2 / a2_full / a2_m2 | `-k e2` (4 params) | Each stage, after reconcile, gives `2024: dropped`. `partial_outputs` lists **5 / 10 / 11 / 12** files: adapter+ckpt+bin+mask+in-process csv, then plus the moved csv, then plus the torn A2 record(s). `drop_attempt` keeps all of them (`left=[]`). The re-run is `[2024]` whole, the ledger reads `start,lost,start,end`, and the seed record lists 1 dropped attempt with the same kept count. |
| D-13 failure of each kind (RuntimeError, SystemExit, gate_mismatch, malformed block, no `measured`, non-JSON) | `tests/…::test_d13_failure_is_not_a_crash_the_seed_stays_whole[runtime\|systemexit\|gate_mismatch\|malformed_block\|no_measured\|non_json]` | All 6 PASSED. The ledger reads `start,end,start,end`, both seeds are whole, and the record carries `d13_not_measured(kind, …)`. |
| KeyboardInterrupt in D-13 | `…::test_d13_keyboard_interrupt_is_still_a_crash` | PASSED. Attempt left open, no seed record. |
| require_launch stop before seed k | `…::test_stop_before_a_seed_writes_nothing_for_it` | PASSED. Only seed 1337's start+end are written, 2024 is not_run, and `partial_outputs(2024) == []`. |
| Relaunch after a lost seed, declined branch | `…::test_crash_mid_seed_is_dropped_after_reconcile[False]`; `-k e8` (real-root rig) | PASSED. E8: `outcomes {…, 2025: dropped, 1339: whole}`, so the relaunch ran only the not_run seed and 2025's outputs stayed in place. |
| Relaunch after a lost seed, drop_attempt + re-run | `…[True]`, `…::test_preflight_rerun_needs_the_dropped_manifest`, `-k e2` | PASSED. A changed kept file, a moved HEAD and a replanted output each refuse before any start line. |
| run / emit / report with no arguments | Inspected; `…::test_run_with_no_arguments_resolves_the_real_defaults`, `…::test_main_dispatches_with_no_arguments_from_the_repo[*]` | `root=_ROOT` (repo), `ledger_path=None` gives `ledger/v6_mps_ledger.jsonl`, heartbeat gives `data/v6_mps_heartbeat.jsonl`, device is strict `preflight_device` and must be `mps`, `rehearsal_identity` must be None. `main` chdirs to `_REPO`. Correct. |
| csv move failing after training | `-k e7` | `E7 ledger [start 1337] open [seed1337]`, `trained adapter on disk True`: a crash that drops the seed (see IN-02 for the realistic trigger). |
| emit with a dropped seed | `-k e8` | `EMIT MEASURED whole=1337,2024,1338,1339`. `dropped_seed_outputs[2025].in_place` lists its adapters and in-process csv with sha256. The report section "Seed 2025 is left dropped" renders. |
| emit with fewer than e2_min_seeds (2) whole seeds | `-k e9` | `EMIT INSUFFICIENT_SEEDS whole=1337`. `recall_floor`, `gap_noise_floor` and `d12` are absent. Identity gives `full_seed2024: 'not whole: seed 2024 is dropped'`. The report renders with 8 INSUFFICIENT_SEEDS mentions. |
| Relaunch / emit dirty check with whole, dropped and not_run seeds | `…::test_preflight_relaunch_pathspec_excludes_only_the_runs_own_records`, `…::test_preflight_pathspec_on_a_real_git_rig`, `-k e8` | PASSED. E8's emit pathspec for dropped 2025 excludes exactly `results/phase40_seed2025.json`, both A2 records, and `results/phase40_e2_{full,m2}_seed2025`. A stray not_run record, a whole seed's in-process csv or a new .py still refuse. |

## Warnings

### WR-01: A crash between the seed record and the end line becomes an unrecoverable dropped seed if `reconcile` runs first, and preflight's refusal suggests `reconcile`

**File:** `scripts/phase40_noise.py:829-833` (refusal text), `:1049-1061` (the window), `:622-625` (drop_attempt's crash rule (i))

**Issue:** If the process dies after `_write_once(seed_record)` and before `append("end")`, the attempt is open and the record exists. Plan 09 rule (i) says to append the end line by command and never reconcile. The driver's own refusal for this state (preflight, line 831) says "end it, **or** once the run is dead phase36_ledger.py reconcile first". It does not check whether the open seed's record exists, and `phase36_ledger.py` has no `end` CLI, so `reconcile` is the only one-command option. Once reconcile has run:
- `append("end")` refuses because no attempt is open.
- `drop_attempt` refuses under crash rule (i).
- `rerun_seeds` needs a manifest that drop_attempt will never write.

The seed is then permanently dropped, and its ~1.6 MPS-hours and its finished record are wasted. Evidence (`-k e1`, reconcile_by_mistake):
```
E1(b) outcomes {1337: 'whole', 2024: 'dropped', 1338: 'not_run'}
E1(b) drop_attempt: REFUSED [phase40_noise] crash rule (i): results/phase40_seed2024.json exists; append its end line, never drop it
E1(b) append end: REFUSED [phase36_ledger] run v6/40/E2/seed2024 has no open attempt to end
E1(b) relaunch pending (1338,)
```
This is not a BLOCKER: it needs a crash inside a window of a few ms (stop.set, thread.join, then `append`'s read_ledger and git ls-files) **and** an operator who departs from plan 09's written rule (i). The driver should not steer that operator wrong. No test covers this window.

**Fix:** Make the refusal name the right action per seed. Add a test that kills `append("end")` and asserts this message.
```python
for rid in sorted(still):
    seed = next(s for s in prereg.SEEDS if prereg.run_id(s) == rid)
    _prove(
        not (root / prereg.seed_record(seed)).exists(),
        f"{rid} is open and {prereg.seed_record(seed)} exists: crash rule (i) — append its end line "
        "by command (40-09 Task 4), NEVER reconcile (a lost line makes this seed unrecoverable)",
    )
_prove(not still, f"... open attempt for ...: no seed record, so once the run is dead, reconcile")
```

### WR-02: emit, drop_attempt and declare_relaunch skip preflight's root/ledger pairing guard

**File:** `scripts/phase40_noise.py:1410-1434` (emit), `:600-616` (drop_attempt), `:659-664` (declare_relaunch)

**Issue:** Preflight refuses an explicit ledger or heartbeat on the real root (line 788). It also refuses a tmp root without an explicit ledger, or with the milestone ledger. emit applies neither rule. On the real root, `emit(ledger_path=<other>)` writes the write-once `results/phase40_noise_floor.json` from the wrong ledger, and the correct `emit()` is then refused. Evidence (`-k e11`, real-root rig after a full 5-seed run):
```
E11 preflight(ledger_path=other) REFUSED: [phase40_noise] the real root runs every seed of SEEDS into the milestone ledger and heart…
EMIT INSUFFICIENT_SEEDS whole=1337 recall_floor='-' gap_noise_floor='-'
E11 emit(ledger_path=other) WROTE True status INSUFFICIENT_SEEDS whole [1337] not_run [2024, 1338, 2025, 1339]
E11 the correct emit() now: [phase40_noise] …/results/phase40_noise_floor.json exists — REFUSING to overwrite it…
```
The reverse also holds: `emit(root=tmp)` silently reads the milestone ledger (line 1183). `drop_attempt` and `declare_relaunch` have the same gap. drop_attempt on the real root with a tmp ledger would move real partial outputs under a `lost_utc` directory that the real ledger never names. Its seed-record check still protects whole seeds. This is a WARNING, not a BLOCKER, because 40-09 calls emit only as `phase40_noise.py emit`, and the CLI cannot pass `ledger_path`.

**Fix:** Use one shared guard, called by preflight, emit, drop_attempt and declare_relaunch:
```python
def _root_ledger(root, ledger_path):
    if _is_real(root):
        _prove(ledger_path is None, "the real root reads the milestone ledger only")
    else:
        _prove(ledger_path is not None and pathlib.Path(ledger_path).resolve()
               != (phase36_ledger._ROOT / phase36_ledger.LEDGER_PATH).resolve(),
               "a tmp root reads its own explicit ledger, never the milestone one")
```

### WR-03: The D-13 handler's own `_release()` is outside ruling c's catch

**File:** `scripts/phase40_noise.py:991-993`

**Issue:** Ruling c says every exception of the D-13 call becomes `d13_not_measured` and the seed finishes ("Nothing after it may fail on the return"). The `except` body calls `_release()` (gc plus `torch.mps.empty_cache()`) unguarded. If D-13 failed because MPS is in a bad state and `empty_cache` then raises, the new exception escapes the handler. The seed, with both trainings and both A2 records done (~1.6 h MPS), becomes an open attempt and is dropped. Evidence (`-k e15`; D-13 fake raises, then `_release` raises):
```
E15 CRASH: planted: torch.mps.empty_cache failed after the MPS error | open ['v6/40/E2/seed1337'] | seed record False | both A2 records True
```
The mechanism is measured. Whether `torch.mps.empty_cache()` raises after a catchable MPS error is a **hypothesis**: an MPS OOM `RuntimeError` normally leaves `empty_cache` working, and a fatal command-buffer error usually aborts the process, which is outside any catch. `d13_scores`' own `finally: _release()` (line 427) is already inside the try, so only the handler's second call is exposed.

**Fix:**
```python
except (Exception, SystemExit) as exc:
    try:
        _release()
    except Exception:  # ruling c: nothing after the D-13 call may fail the seed
        pass
    d13 = prereg.d13_not_measured("exception", f"{type(exc).__name__}: {exc}")
```

### WR-04: The D-13 instrument `phase39_ctx` is first imported ~3 h after the module digests are taken

**File:** `scripts/phase40_noise.py:384-391` (lazy imports), `:821` (`module_sha256()` in preflight), `:1046` (`module_sha256_at_launch`)

**Issue:** Every seed record publishes `module_sha256_at_launch` from preflight. Preflight's own imports (`run_inputs`, `comparators`, `arm_paths`) load teach_persona, phase19_erasure, phase18_extraction and phase38_rank, but **not** `phase39_ctx`. That module is first imported inside seed 1337's first `d13_scores` call, after two trainings and two A2 passes. Evidence (`-k e13`: a fresh interpreter doing what preflight imports):
```
E13 loaded by preflight: {'phase39_ctx': False, 'phase38_rank': True, 'phase18_extraction': True, 'phase19_erasure': True, 'teach_persona': True}
```
A working-tree edit to `scripts/phase39_ctx.py` in that window would be executed, while every seed record claims the launch digest. This repo has recorded peer sessions editing the working tree mid-session. emit's `modules_changed_since_launch` catches only a change that persists until emit. D-13 is descriptive, so no verdict changes, but the recorded provenance would be wrong. Severity is WARNING.

**Fix:** When `prereg.D13_INCLUDED`, import every D-13 module in preflight, before `module_sha256()`:
```python
if prereg.D13_INCLUDED:
    import phase38_rank, phase39_ctx, phase39_prereg  # noqa: F401  (loaded before the digests)
```
Alternatively, re-hash `MODULES` at each seed's end into `provenance.module_sha256_at_end` and record any mismatch.

## Info

### IN-01: The report has a double blank line in the D-13 section (cosmetic, confirmed)

**File:** `scripts/phase40_noise.py:1876-1883`
**Issue:** When `reading["not_measured"]` is empty, the `""` before the generator and the `""` after it are adjacent. In the `-k e8` report this is the only `\n\n\n` (`E8 double blank lines in report: 1`), right after "descriptive, never a verdict. Measured seeds: 1337, 2024, 1338, 1339.".
**Fix:** Drop the `""` at line 1876, or emit the trailing `""` only when `reading["not_measured"]` is non-empty.

### IN-02: train_adapter's strict `rmdir` refuses after the training has already been paid for

**File:** `scripts/phase40_noise.py:296-301`
**Issue:** Any extra file in `results/phase40_e2_<arm>/` (for example a Finder `.DS_Store`) makes `rmdir` raise after `train_arm` returned. Evidence (`-k e14`): `E14 crash AFTER training: OSError Directory not empty | adapter on disk True | open ['v6/40/E2/seed1337']`. That drops the seed. The trigger is unlikely, since nothing in the pipeline writes there.
**Fix:** Tolerate `OSError` on `rmdir`. The leftover is untracked under `results/`, so the next preflight or emit dirty check refuses it cheaply, on CPU, instead of costing MPS hours.

### IN-03: A SIGKILL inside the seed record's atomic write leaves an untracked temp file that drop_attempt never moves

**File:** `scripts/phase40_noise.py:1049` (via `phase25_run.atomic_write_json`), `:562-577`
**Issue:** `results/.phase40_seed<k>.json.<rand>.tmp` is not gitignored (`git check-ignore` exit 1) and is not in `_output_roots`. After such a kill, the relaunch dirty check refuses it, and the only remedy is a hand deletion, which goes against "never deleted". The window is milliseconds. This is a hypothesis, not exercised.
**Fix:** Add a glob for `results/.phase40_seed<k>.json.*.tmp` to `_output_roots`, so drop_attempt keeps it.

### IN-04: D-13's NLL-count refusal is recorded as `exception`, not `malformed_reading`

**File:** `scripts/phase40_noise.py:428-431`
**Issue:** `_prove(n_nlls == D13_NLLS_PER_ADAPTER)` raises SystemExit, and run() records it as `failure_kind: "exception"` with reason `SystemExit: …`. A wrong count is a malformed reading.
**Fix:** Return `prereg.d13_not_measured("malformed_reading", …)` from `d13_scores` instead of raising.

### IN-05: A dropped seed's own seed record is not listed among its in-place outputs

**File:** `scripts/phase40_noise.py:562-577`, `:1142-1166`
**Issue:** This applies only in the WR-01 state (dropped, with a record). emit lists the A2 records and adapters but not `results/phase40_seed<k>.json`, which then sits untracked and excluded and is never named in the noise-floor record.
**Fix:** Include `root / prereg.seed_record(seed)` in `_left_dropped`'s `in_place` when it exists.

### IN-06: There are no tests for the WR-01, WR-02 or WR-03 paths

**File:** `tests/test_phase40_noise.py`
**Issue:** The suite covers every other recovery path named above. Three gaps remain:
- Nothing kills the process between the seed record and `append("end")`.
- Nothing asserts emit's root/ledger pairing.
- Nothing makes the D-13 handler's cleanup raise.

The scratch experiments `e1`, `e11` and `e15` are ready to port.
**Fix:** Port them as regression tests alongside the WR fixes.

---

_Reviewed: 2026-10-06T16:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
