---
phase: 37-clean-reproduction-of-the-phase-19-verdict
reviewed: 2026-10-03T00:00:00Z
depth: deep
files_reviewed: 9
files_reviewed_list:
  - scripts/phase37_prereg.py
  - scripts/phase37_routes.py
  - scripts/phase37_r1a.py
  - scripts/phase37_r1b.py
  - artifacts/com.personacore.phase37.r1b.plist
  - tests/test_phase37_prereg.py
  - tests/test_phase37_routes.py
  - tests/test_phase37_r1a.py
  - tests/test_phase37_r1b.py
findings:
  critical: 0
  warning: 5
  info: 6
  total: 11
status: issues_found
fixed:
  WR-01: 9abab12
  WR-02: 5896ae3
  WR-03: 9069c5c
  WR-04: 2781bd6
  WR-05: 6dbad06
warnings_open: 0
---

# Phase 37: Code Review Report

**Reviewed:** 2026-10-03
**Depth:** deep (cross-checked against scripts/phase19_erasure.py, scripts/phase19_run.py, scripts/phase35_prereg.py, scripts/phase36_ledger.py, scripts/phase25_run.py, src/personacore/provenance.py)
**Files Reviewed:** 9
**Status:** issues_found. All five warnings were fixed on 2026-10-03, one commit each (see each finding's **Fixed:** line); the six Info findings are open.

## Summary

I checked the review's four priorities against the code and with probes.

**1. Pre-registration (phase37_prereg.py).** It encodes 37-CONTEXT D-01..D-16 correctly. Probes:
- `DESTROYED_PCT_TOLERANCE` = `0.8396203493271365`, bit-equal to `2 * 0.005214448168350039 / 1.2420966625043919 * 100`.
- G0 = `1.2420966625043919`.
- Cost is 1.2590560358100467 h against a cap of 1.6622708975519829 h.
- `replicated()` is inclusive at both edges (±tolerance reads REPLICATED; one ulp past reads NOT_REPLICATED). Pair keys require an equal denominator.
- `prefix_decision()` runs the arm iff k == 78 AND the address sets are equal.
- The three zero tolerances are labelled `preference`.

No finding changes a value or verdict that a real fill would read.

**2. R1b driver.**
- Every refusal in `preflight()` runs before `phase36_ledger.append("start")`.
- REPLICATED/NOT_REPLICATED comes only from `replicated(rederive(replica))`.
- Results go through `atomic_write_json`, except the pin's own arm write, which cannot be edited.
- The ledger end line is written only after the sidecar.

No path misclassifies the verdict. The warnings below are about provenance and about losing the one attempt's data:
- the run's `git_sha` is captured at the END of the run, not at launch;
- the sweep is persisted only after the 68-minute arm;
- the gitignored inputs are not checked before the start line.

**3. R1a.** `derive()` on the real committed records reproduces all four assertions, the margin, the (b) floor and FAILURE with three reasons. Write-once is real: an existence check plus a clean-tree check that excludes only the record. One check is one-directional (WR-04). The record's `git_sha` depends on the current working directory (WR-05).

**4. Routes A–E.** They match `phase19_run.report()` and `target_ablate()` term by term:
- A: `_order_normalised` → `zero_results_have_nll`;
- B: correction `governs` + the pinned `lock_erasure_floor` == `TARGET_FLOOR`;
- C: `_pooled_rows` with tiers taken from the arm record;
- D: `retention_ppl[0]`;
- E: `select_ablation_prefix` with `reference_set_for` (|R| = 8) and the same collateral and dialogue callable as `target_ablate`. The only difference from the pin's `_selected_components` is `references`.

Targeted suites: test_phase37_prereg/r1a/r1b gave 81 passed and test_phase37_routes gave 50 passed.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: R1b records the HEAD at the END of the run as the run's commit, not the commit that was launched

**Fixed:** 9abab12. `preflight()` reads `git_sha()` right after `refuse_if_dirty` and refuses `unknown`; it also reads `module_sha256()` at launch. The sidecar and `provenance.run` carry `git_sha_at_launch`, `git_sha_at_end` and `head_moved_during_run`; provenance carries `module_sha256_at_launch`, the emit-time `module_sha256` and `modules_changed_since_launch`. Test: `test_a_commit_landing_mid_run_is_named_not_hidden`.

**File:** `scripts/phase37_r1b.py:223` (and `:151`, `:294`)

**Issue:** The commit the code ran from is known only at launch. `preflight()` proves the tree clean at launch (`:133`) but persists no SHA: `git_sha()` at `:151` is only printed. The sidecar's `"git_sha": git_sha()` is evaluated at `:223`, after the sweep and the ~68 min arm. `module_sha256` is hashed even later, at emit time (`:294`).

Concrete state → wrong output:
1. Launch at commit X.
2. Any commit lands during the ~75 min run (an orchestrator docs/SUMMARY commit, or a peer session; see the memory notes on concurrent agents).
3. Then `provenance.run.git_sha` names commit Y ≠ X.

The Python that ran was X (it was imported at launch). The emitted R1b record then names a commit it did not run from. This is the 21-REVIEW CR-02 class that `refuse_if_dirty` exists to prevent. Precedent: during the Phase 36 probe run (20:15–22:28 UTC) HEAD did not move, so this is conditional. It is a record field in a real run if anything is committed mid-run, and it cannot be fixed after the one attempt.

**Experiment:** `grep -n "git_sha()" scripts/phase37_r1b.py`. Line 151 is a print only and line 223 is inside the sidecar written after the arm. Nothing captured before the start line is persisted.

**Fix:** Capture at preflight and carry it through:
```python
# preflight(): after refuse_if_dirty
launch_sha = git_sha()
...
return {"device": device, "curve": curve, "gate": gate, "git_sha": launch_sha,
        "module_sha256": {rel: _sha256(_ROOT / rel) for rel in MODULES}}
# run(): sidecar
"git_sha": pre["git_sha"], "head_at_end": git_sha(), "module_sha256_at_launch": pre["module_sha256"],
```
Optionally, `emit` can refuse when `module_sha256_at_launch` differs from the emit-time hashes.

### WR-02: A crash during the 68-minute arm loses the attempt's sweep measurement entirely; the full 288 ordering is never recorded

**Fixed:** 5896ae3. `run()` writes the write-once `data/phase37_r1b_sweep.json` (via `atomic_write_json`) right after `prefix_decision` and before the arm. It holds k, `ordered_prefix`, `full_ordering` (288), the curve rows and the decision, and the driver prints `SWEEP k=.. run_arm=..`. `preflight` refuses when the file exists. The sidecar holds its SHA-256, and `emit` reads the sweep from it. Test: `test_rehearsal_crash_during_arm_keeps_sweep_and_ledger_reconcilable`.

**File:** `scripts/phase37_r1b.py:189-232`

**Issue:** The sweep result exists only in memory:
- `sweep` and `decision` (k, `ordered[:k]`, the curve rows, the D-07 decision) are written to disk only in the sidecar at `:219-232`. That happens after `pin.run_erasure_arm` (`:209`) and after the post-arm adapter check (`:212-215`).
- The pin's `select_ablation_prefix` prints nothing (phase19_erasure.py:2443-2531), and the driver prints nothing about k or the decision. So `logs/phase37_r1b.out` will not hold them either.

Concrete state → lost output:
1. The sweep finishes and k = 78 with the same set.
2. The arm crashes, or the post-arm adapter `_prove` at `:212` fires.
3. There is no sidecar. The ledger start line is open and `reconcile` turns it into a `lost` line.
4. The re-measured k, the prefix and the curve, which D-14 requires "so a root-cause investigation has the data", are gone. Under D-11 this crash IS the one attempt.

Separately, `r1b_scope.re_measured` asserts `ordering_288_addresses`, but only `ordered[:k]` is recorded (`:194`). If k ≠ 78, the record cannot show where the committed addresses ranked in the replica's ordering.

**Fix:**
- Persist the sweep atomically right after `prefix_decision` and before releasing the model. Use a second gitignored sidecar or the same one with `"arm_ran": None`, and print `k`/`run_arm` to stdout.
- Add the full ordering: `"full_ordering": [list(a) for a in chosen["ordered"]]`.
- Make `emit` accept a sweep-only sidecar for the NOT_REPLICATED/no-arm branch, but only when `decision["run_arm"]` is False.

### WR-03: Gitignored run inputs are not checked before the ledger start line, so a missing file burns the attempt

**Fixed:** 9069c5c. `run_inputs()` lists the files from their readers' constants (convbase_slim, the adapter, the tokenizer, dialog_val bin and mask, retention_val, the phase18 corpus and arm record). `preflight` refuses before the start line if any is missing. Test: `test_a_missing_run_input_refuses_before_the_start_line` (8 cases).

**File:** `scripts/phase37_r1b.py:121-155` (preflight) vs `scripts/phase14_recall.py:733`, `scripts/phase19_erasure.py:2555, 2808-2834`

**Issue:** D-16 says the cheap refusals run before the start line. `refuse_if_dirty` cannot see gitignored inputs (provenance.py docstring: "`.gitignore`d paths ... correctly do not block"). The run needs:
- `checkpoints/convbase_slim.pt`: `load_adapted_model` raises SystemExit right after the start line;
- `data/dialog_val.bin` and `data/dialog_val_mask.bin`: used by the sweep's `dialogue_ppl`;
- `data/retention_val.bin` and the corpus/parity checks inside `run_erasure_arm`: these fire only after the ~7 min sweep.

None is checked in `preflight()`. A missing or renamed file therefore produces a start line followed by a crash, which counts as THE attempt under D-11/D-16, although it is exactly the refusal D-16 wants before the line. All five files are present on this machine today (`ls -la checkpoints/convbase_slim.pt data/retention_val.bin data/dialog_val.bin data/dialog_val_mask.bin results/phase18_corpus.json`), so this is not live now.

**Fix:** In `preflight()`, before returning:
```python
import phase14_recall, teach_persona as tp
for p in (phase14_recall.CONVBASE_SLIM, tp.DIALOG_VAL_BIN, tp.DIALOG_VAL_MASK,
          pin.RETENTION_BIN, pin.PHASE18_CORPUS_PATH, pin.PHASE18_ARM_RECORD_PATH):
    _prove(pathlib.Path(p).exists(), f"{p} is missing: refusing before the start line (D-16)")
```
Optionally, also run the pin's `assert_phase18_parity` on a dry config built the same way.

### WR-04: R1a's "verdict and its reasons equal the recorded Verdict section" check is subset-only

**Fixed:** 2781bd6. `derive()` parses the `- (a|b|c) ` lines of `### 1.` and refuses unless the re-derived reasons equal them, in order. Test: `test_a_dropped_reason_halts` (reasons[:1] now refuses).

**File:** `scripts/phase37_r1a.py:117-118`

**Issue:** `for reason in got["reasons"]: _prove(f"- {reason}\n" in section, ...)` checks that each re-derived reason appears in the recorded section. It does not check that every recorded reason is re-derived. A re-derivation that drops a reason still passes. `r1a_extra_assertions` (prereg) and REPRO-01 SC1 promise equality ("the verdict and its three reasons equal the recorded Verdict section").

On the real records the result is 3 = 3, so the published record is unaffected. The check simply cannot catch the regression it is named for.

**Experiment (run, passes):**
```
.venv/bin/python -c "import sys; sys.path.insert(0,'scripts'); import phase37_r1a as r, phase37_routes as routes; real=routes.rederive
def short(rec, **kw):
    out=real(rec, **kw); out['reasons']=out['reasons'][:1]; return out
routes.rederive=short; d=r.derive(); print(len(d['reasons']))"
```
It prints `1`: derive() accepts one of three recorded reasons.

**Fix:** Parse the recorded reason lines the way `tests/test_phase37_routes.py::_recorded_reasons` already does: `### 1.` block, `- (a|b|c) ` lines. Then assert `got["reasons"] == recorded` (ordered, equal length).

### WR-05: R1a/R1b `git_sha()` reads the process cwd while the clean-tree check reads `_ROOT`

**Fixed:** 6dbad06. Both `main()`s run `os.chdir(_ROOT)` after validating their arguments, which also covers the pin arm's `config.git_sha`. `src/personacore/provenance.py` is unchanged. Tests: `test_main_from_another_cwd_records_the_repo_sha` (R1a) and `test_main_dispatches_with_signature_valid_kwargs` (R1b, from a tmp cwd).

**File:** `scripts/phase37_r1a.py:178, 217`; `scripts/phase37_r1b.py:223, 295`; `src/personacore/provenance.py:28-42`

**Issue:** `refuse_if_dirty(..., cwd=_ROOT)` proves the right repository clean. `git_sha()` runs `git rev-parse HEAD` with no cwd, so it reads whatever repository (or none) the shell is in. Concretely: running `/Users/.../PersonaCore/.venv/bin/python /Users/.../PersonaCore/scripts/phase37_r1a.py` from any directory outside the repo passes every refusal and writes the write-once `results/phase37_r1a.json` with `provenance.run.git_sha = "unknown"` and `head_at_write = "unknown"`. From inside another git checkout it records that checkout's HEAD.

The R1b plist sets `WorkingDirectory`, so the agent run is safe. The 37-05 R1a write is safe only if run from the repo root.

**Experiment:** `cd /private/tmp && /Users/juliorcoelho/PersonaCore/.venv/bin/python -c "import sys; sys.path.insert(0,'/Users/juliorcoelho/PersonaCore/src'); from personacore.provenance import git_sha; print(git_sha())"` prints `unknown`.

**Fix:** In both drivers, refuse an unusable SHA before writing:
```python
sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=_ROOT, capture_output=True,
                     text=True, check=True).stdout.strip()
```
Or keep `git_sha()` and refuse when `pathlib.Path.cwd().resolve() != _ROOT` or `sha == "unknown"`.

## Info

### IN-01: The pin's arm record is written non-atomically

**File:** `scripts/phase19_erasure.py:2947-2949` (called from `scripts/phase37_r1b.py:209`)

`run_erasure_arm` uses `record_path.write_text(...)`. A kill inside that write leaves a torn `results/phase37_r1b_arm.json` and no sidecar. The pin is closed (byte-unchanged by test), so this is a known limitation. Note it in the root-cause template, not in the code.

### IN-02: The R1b `module_sha256` covers only the eight orchestration modules

**File:** `scripts/phase37_r1b.py:60-69`

The instruments that produce the numbers are not hashed: `phase18_extraction.py`, `phase14_recall.py`, `phase14_factset.py`, `teach_persona.py` and `src/personacore/**`. The clean-tree check plus `git_sha` covers them only if WR-01 is fixed.

### IN-03: `check_record` does not verify every field of the R1a record

**File:** `scripts/phase37_r1a.py:186-199`

It does not verify `target_fact_id`, `nontarget_deltas_by_slot`, `routes` or `provenance.module_sha256`. An edited value in those fields still reads "REPRODUCED (record verified)". This needs a deliberate edit to trigger.

### IN-04: Preflight does not compare torch against the committed run's torch

**File:** `scripts/phase37_r1b.py:143-144`

Preflight checks the device but not `torch.__version__` against the committed `config.torch` (`2.7.1`, MPS). Today the venv has 2.7.1, so they match. A drifted venv would yield a legitimate-looking NOT_REPLICATED. Consider refusing on a mismatch, or at least printing both versions in `PREFLIGHT OK`.

### IN-05: The R1b tests never exercise a real dirty-tree refusal

**File:** `tests/test_phase37_r1b.py:100, 340-350`

`refuse_if_dirty` is replaced by a recorder in every test. The "dirty tree refuses before the start line" ordering (D-16) is therefore asserted only by the call order inside `preflight`. Adding a `_refuse_dirty` plant (`lambda **kw: (_ for _ in ()).throw(SystemExit("dirty"))`) to the parametrize list would close this.

### IN-06: No in-driver path exists for a sanctioned relaunch

**File:** `scripts/phase37_r1b.py:126-132`

Any ledger line for `RUN_ID` refuses forever. A D-15 relaunch after Rafael's "approved" therefore requires a code change, for example a new `unit` in `run_id(37, "R1b", ...)`. This is documented as an implementation fact; record it in the root-cause template so that the relaunch commit is expected.

---

_Reviewed: 2026-10-03_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
