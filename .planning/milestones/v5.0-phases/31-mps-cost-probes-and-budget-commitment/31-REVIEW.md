---
phase: 31-mps-cost-probes-and-budget-commitment
reviewed: 2026-09-27T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - scripts/phase31_probe.py
  - scripts/phase31_budget.py
  - tests/test_phase31_probe.py
  - tests/test_phase31_budget.py
  - artifacts/com.personacore.phase31.probe.plist
findings:
  critical: 0
  warning: 2
  info: 5
  total: 7
status: issues_found
---

# Phase 31: Code Review Report

**Reviewed:** 2026-09-27
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

I reviewed the probe driver (point and relearn halves, CLI and emits), the budget derive/emit, both test files, and the LaunchAgent plist. I checked them against D-01..D-12 and the six plan summaries. I also traced the calls they make into `phase25_points.train_stage` (bin unlink on a fresh train), `teach_persona.refuse_if_exists`, `phase30_points.next_action`, `phase27_relearn.calibrate/run_curve/run_gate` (the arm count and the FULL_K re-score), and `personacore.provenance.refuse_if_dirty`.

**None of the findings affects the committed records.** I checked this against the record bytes:
- `results/phase31_probe_point.json` has every `stages.*.reused == false` and `resumed_from_step == 0`.
- Both records have `provenance.run.git_sha == 61465c1`.
- `git diff --quiet 61465c1 a2110ac -- scripts src` and `git diff --quiet 61465c1 966f91b -- scripts src` both exit 0, so the code at emit was the code that ran.
- The relearn run was a single session: `started_utc` equals the point run's `finished_utc`.
- The committed budget recomputes. `tests/test_phase31_probe.py tests/test_phase31_budget.py` gives 48 passed in 46 s, and that includes `test_committed_budget_recomputes_from_committed_files`.

I hand-checked the budget arithmetic against the committed inputs:
- per_window = (633.46 − 80.30) / (200 × 256) = 0.010804.
- n8 train = 91.70 + 200 × 32 × 0.010804 = 160.85.
- The arm count in the conditional term is 5 fresh + 1 control + a mitigated. That matches `phase27_relearn.calibrate` / `run_curve`.
- The FULL_K re-score uses its own k-suffixed cache (`run_gate`), so linear scaling by FULL_K/k is correct.
- The Phase 25 twins also ran 200 steps at k = 16, so twin and probe are like for like.

I checked and ruled out these hypotheses:
- The probe leaving `data/persona_advr_n64_train{,_mask}.bin` would make Phase 32's control training refuse. It does not: `train_stage` unlinks the arm bins on a fresh train (`phase25_points.py:393-397`).
- `probe_plan` would go RED once Phase 32 commits the n64 control. It does not: `next_action` returns `train` for a control key regardless.

The two warnings are latent defects in the resume and emit paths. Neither ran on the committed path.

## Warnings

### WR-01: The relearn crash-recovery path ("the restart finishes the moves") cannot be reached. The leftover csv under `results/` trips the dirty-tree refusal first.

**File:** `scripts/phase31_probe.py:334-342, 738-746, 646-668`
**Issue:** `train_relearn_arm` writes its csv to `results/phase27_relearn_attacker_n64_mitigated_probe31_seed1337/run.csv`. That path is not gitignored; `data/` and `checkpoints/` are. `_finish_relearn_moves` exists to finish the moves after a crash between the train-sidecar write and the moves, and 31-02-SUMMARY says that crash "is finished automatically".

On a restart, though, `main` calls `run_point_probe` first, and `run_relearn_probe` also calls `refuse_if_dirty(pathspec=("scripts", "src", "results"))` before anything else. Both refuse on the untracked `results/` directory. The same thing happens after a crash mid-training: the operator gets a generic "working tree is dirty" abort instead of the tailored half-trained message that tells them what to delete.

`test_relearn_refuses_a_half_trained_arm` case 4 passes only because the autouse `clean_tree` fixture stubs `refuse_if_dirty`.

**Reproduced** in a scratch `git clone --shared`, with the untracked csv created and the probe's exact call made:
```
[phase31_probe] REFUSING: the working tree is dirty.
?? results/phase27_relearn_attacker_n64_mitigated_probe31_seed1337/
EXIT=1
```
**Committed records:** unaffected. The 31-04 run did not crash, and all 4 moves completed in the same process.
**Fix:** Exclude the one known `train_relearn_arm` csv from the run-time dirty check, the same way `_emit_target` excludes its output:
```python
_RUN_PATHSPEC = ("scripts", "src", "results",
                 f":(exclude){_rel(relearn_moves()[0][0].parent)}")
```
Or, simpler and without code changes, correct the 31-02 resume note to say that such a crash needs a reviewed manual move. Either way, one live-path test should keep the real `refuse_if_dirty` for the restart case.

### WR-02: `provenance.module_sha256` hashes the working tree at emit time, and nothing proves it is the code that ran

**File:** `scripts/phase31_probe.py:537-555` (also `344`, `770-771`, `887-891`)
**Issue:** `_write_record` copies `run["run_git_sha"]` into `provenance.run.git_sha`, but it hashes `PINNED_MODULES` from the emit-time tree. It never checks `git diff --quiet <run_git_sha> HEAD -- <PINNED_MODULES>`. A pinned module edited and committed between the MPS run and the emit therefore produces a record whose module hashes describe code that never timed anything. Every guard still passes, because the tree is clean at emit.

The same gap applies across resumed sessions:
- Point probe: the sidecar records only the last session's `run_git_sha`, while a `reused` stage was timed under an earlier commit.
- Relearn probe: the partial run sidecar stores no per-session sha, so rungs from sessions at different commits are merged silently. `build_relearn_record` also drops `run.train.run_git_sha`, which is the one per-session sha the sidecar does keep.

31-05 closed this gap by hand (`git diff --quiet 61465c1 HEAD -- scripts src`), but the code does not enforce it.

**Reproduced:** `phase31_probe._write_record(<scratch>/prov.json, {}, run)` with `run_git_sha = "0"*40` wrote the record without complaint (`run sha 00000000 | head_at_write 596c46ca`). `grep -n run_git_sha scripts/phase31_probe.py` shows the value is only ever copied and never compared.

**Committed records:** unaffected. Both run→emit diffs over `scripts src` are empty, and the run was a single session.
**Fix:** In `_write_record`:
```python
changed = _git("diff", "--name-only", run["run_git_sha"], "HEAD", "--", *PINNED_MODULES).split()
_prove(not changed, f"pinned modules changed since the run at {run['run_git_sha'][:8]}: {changed}")
```
Also, in `run_relearn_probe`, persist `run_git_sha` in the partial sidecar and refuse a resume whose `git_sha()` differs, and carry `train.run_git_sha` into the relearn record.

## Info

### IN-01: The D-10 spread pools both legs, so the between-leg offset shows up as per-point spread

**File:** `scripts/phase31_budget.py:136-142`
**Issue:** `spread[stage]` is min/median and max/median over all 12 Phase 25 points. The n8 and n64 medians differ systematically, and that difference is already modelled by the D-09 ratios, so the pooled factors are not within-leg spreads. Measured on the committed inputs:
- draw: n64's own range is [0.970, 1.076] against pooled [0.755, 1.107];
- recall: n8's own high is 1.077 against pooled 1.024;
- the effect on the scheduled range is: low 18.14 h pooled vs 20.84 h per-leg, and high 25.18 h pooled vs 24.87 h per-leg.

The stop line comes out slightly more conservative, so nothing is under-budgeted. This follows D-10's wording, which cites the 49–71 min spread across all 12 points. The only effect is that the published low bound is optimistic.
**Fix:** No change is needed for Phase 31. If the budget is ever re-derived, a dated continuation could compute the spread per leg.

### IN-02: `STAGES[:-1]` depends on `score` being the last stage

**File:** `scripts/phase31_budget.py:138`
**Issue:** The code excludes the score stage by its position in the tuple. Reordering `STAGES` would silently spread a different stage.
**Fix:** `for stage in (s for s in STAGES if s != "score"):`

### IN-03: The budget's `PINNED_MODULES` omits the modules that choose which Phase 25 files are read

**File:** `scripts/phase31_budget.py:48-57`
**Issue:** `phase31_probe.phase25_stage_table` selects its sources through `phase25_record.point_key` and `phase25_prereg.point_record_path`, but neither module is pinned. The risk is small, because `record["sources"]` pins every file that was read by sha256.
**Fix:** Optionally add `phase25_record.__file__` and `phase25_prereg.__file__`.

### IN-04: Plist hardcodes one user's home directory, and its comment cites the wrong D-10

**File:** `artifacts/com.personacore.phase31.probe.plist:19-21, 30-45`
**Issue:**
- Every path is absolute under `/Users/juliorcoelho`, following the Phase 25/26 precedent. The agent does not work on another checkout.
- "KEEPALIVE IS FALSE FOR THE SAME REASON THE SWEEP'S IS (D-10)" refers to Phase 25's D-10. In this phase, D-10 is the budget spread, so the comment points readers to the wrong decision.
**Fix:** Write "Phase 25 D-10" in the comment.

### IN-05: `_counting_train` accepts keyword arguments only and assumes no caller passes `on_draw`

**File:** `scripts/phase31_probe.py:390-395`
**Issue:** A positional call, or a caller that already supplies `on_draw`, would raise `TypeError` instead of counting. It fails loudly, so no bad record can result. It is a fragility only.
**Fix:** `def _counting_train(*args, on_draw=None, **kwargs)`, chaining any existing `on_draw`.

---

_Reviewed: 2026-09-27_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
