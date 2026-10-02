---
phase: 36-mps-cost-probes-and-budget-commitment
reviewed: 2026-10-02T16:02:09Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - scripts/phase36_prereg.py
  - scripts/phase36_caps.py
  - scripts/phase36_ledger.py
  - scripts/phase36_probe.py
  - scripts/phase36_budget.py
  - tests/test_phase36_prereg.py
  - tests/test_phase36_caps.py
  - tests/test_phase36_ledger.py
  - tests/test_phase36_probe.py
  - tests/test_phase36_budget.py
  - tests/test_phase23_resume.py
  - artifacts/com.personacore.phase36.probe.plist
findings:
  critical: 1
  warning: 5
  info: 2
  total: 8
status: issues_found
---

# Phase 36: Code Review Report

**Reviewed:** 2026-10-02T16:02:09Z
**Depth:** standard
**Files Reviewed:** 12
**Status:** issues_found

## Summary

I reviewed the probe driver, the ledger, the caps, the budget derivation, the frozen
pre-registration, their tests, the 36-05 register edit in `tests/test_phase23_resume.py`, and
the LaunchAgent plist. I checked the following on the real committed inputs (CPU only, no MPS)
and found no defects in them:

- **E1 shape:** `e1_shape()` gives (216, 48) and `e1_components()` gives 78 components.
- **E3 plans:** they are re-keyed to `probe36_e3_t200` / `probe36_e3_t800` with composed_steps 200 / 800.
- **E6 anchor prompts:** they pass `assert_no_value_in_prompt` on the real tokenizer for all 8 locked slots.
- **E5 clearance counts:** 104 distinct held-out questions and 24 published values match the stage's `_prove`s.
- **Comparator paths:** every comparator path resolves on the committed records. Values: retrain 46.618 min, point training 209.06 s, phase25_recall scoring 1246.87 s, canary 5556.24 s, and phase17 wall 2.1 min.
- **Draw path:** `run_erasure_arm` and `score_arm` reach `_complete` only through `phase14_recall.draw_all`, so DrawTimer's draw counts are exact on the real pin.
- **Bookkeeping:** heartbeat `utc` is tz-aware, so it compares cleanly with the ledger start. The 23-resume register literal is 18, which is correct.
- **Tests:** ledger, caps and prereg pass (96 passed).

The defects are concentrated in the **recovery paths** around the run. The happy path (one clean
run, then `emit-all`, then `dry`) prices correctly. The plan's own documented recovery path does
not:

- After a mid-run crash, the fix lands in a pinned module.
- Under WR-02, every front that already finished must be re-probed (36-07 Task 3 step 2).
- That re-probe writes a second `end` line for the same record. That permanently breaks
  `phase36_ledger.spent()`, the budget's probes front, and every later `require_launch`.

## Critical Issues

### CR-01: Re-probing a front writes a second end line for the same record; spent() then refuses forever (probes front cannot be priced; every v6.0 launch is blocked)

**File:** `scripts/phase36_ledger.py:186-206` (append accepts it), `scripts/phase36_ledger.py:306-308` (spent refuses), `scripts/phase36_probe.py:393-400` (run_front writes it)

**Issue:** The end line always names the same record path: `run_front` closes each attempt with
`record=phase36_prereg.probe_record(front)`. `append("end")` only checks that the run is open. It
never checks whether an earlier `end` line already names that record. `spent()` then refuses any
record named by two end lines. It does this for every scope that includes the front:

- `ledger_probes_seconds` (scope `("probes",)`);
- `require_launch`, `rule` and `_state` (full scope).

The ledger is append-only and committed, so the state is permanent.

**Trigger:** the documented recovery path. Suppose E1 crashes on MPS and the root-cause fix
touches a pinned module. `phase36_probe.py` is itself pinned. Under WR-02, e5/e6/e3/e2 were
timed at the old sha, so they must be re-probed (36-07 Task 3 step 2: "those fronts must be
re-probed"). Then:

1. The operator deletes `data/probe36_e5_run.json` and reruns.
2. `run_front` appends start, then a second `end` naming `results/phase36_probe_e5.json`.
3. `phase36_budget.dry`/`emit` refuse, and so does every Phase 37–43 `require_launch`.

The effect is to block the fill entirely, not to misprice it. There is no way out without
rewriting the append-only ledger.

**Verified:** a one-command experiment on a tmp ledger. Two start/end pairs naming
`results/phase36_probe_e1.json` were both accepted by `append`. `spent([], ledger_path=lp)`
then raised `records named by two end lines (double count): ['results/phase36_probe_e1.json']`.

**Fix:** In `spent()`, treat superseded attempts as spent hours rather than refusing. The
superseded attempts' MPS hours were really spent (D-12). Count the earlier ones by their own
ledger span and only the last one by the record's `provenance.run` clock:

```python
# spent(): replace the `twice` refusal
last_end = {}
for i, (start, close) in enumerate(attempts):
    if close is not None and close["event"] == "end":
        last_end[close["record"]] = i
rows = []
for i, (start, close) in enumerate(attempts):
    if close["event"] == "end" and last_end[close["record"]] != i:
        seconds = (datetime.datetime.fromisoformat(close["utc"])
                   - datetime.datetime.fromisoformat(start["utc"])).total_seconds()
        rows.append({..., "seconds": seconds, "flag": "superseded: " + LOST_FLAG})
    else:
        rows.append(_closed_row(start, close, tracked))
```

Mirror the same rule in `report_rows`. An alternative is to refuse the *start* in `run_front`
when the ledger already holds an end line for `probe_record(front)`, with a dated-continuation
path. A refusal there fires before any hours are spent.

## Warnings

### WR-01: The budget's exact-equality check against E6's copied A2-context unit makes an E1 re-probe after E6 is emitted permanently un-derivable

**File:** `scripts/phase36_budget.py:378-384`, `scripts/phase36_probe.py:662-674`, `scripts/phase36_probe.py:61,1298`

**Issue:** `e6_a2_context_beside` copies `max(mean(per_question_k48_seconds))` from the E1
*sidecar* into the E6 record at E6 emit time. `unit_prices` refuses unless that copy equals,
exactly, the value it recomputes from the E1 *record*.

`emit_all` emits in RUN_ORDER (e5, e6, e3, e2, e1), so E6 is committed (write-once) before E1.
Suppose `emit-all` aborts after e6 (36-07 step 2's "aborts midway", then a code fix). The
pinned-module fix then forces e3/e2/e1 to be re-probed. The new E1 timing differs, so
`beside != a2_question` permanently. The E6 record cannot be rewritten.

**Verified:** by reading. The E6 copy is the only consumer coupling, and `test_derive_refuses_an_e6_record_beside_another_e1` shows the refusal fires on any mismatch.

**Fix:** The budget already reads the unit from the E1 record, so the E6 copy is redundant. Pick one:

- Drop the equality `_prove` and keep E6's value as context only; or
- Emit `e1` before `e6` in `emit_all`, and make `e6_a2_context_beside` read the committed E1
  record (path + sha). The budget can then check the sha rather than a float.

### WR-02: A crashed attempt's session stays in the sessions sidecar, so WR-02 refuses a clean rerun after any pinned fix

**File:** `scripts/phase36_probe.py:318-327`, `scripts/phase36_probe.py:1363`, `scripts/phase36_probe.py:1182-1185`

**Issue:** `record_session` appends to `data/probe36_<front>_sessions.json` at every attempt.
Preflight explicitly *allows* every sessions sidecar (`allowed = {sessions_sidecar(front) ...}`),
even for a front with no run sidecar. Stages never resume (each refuses stale outputs), so a
crashed attempt's seconds never reach the record. But its session sha stays in the list.

**Trigger:**

1. E3 crashes at sha A. The root cause is fixed in a pinned module at sha B.
2. The operator reconciles, deletes the outputs preflight lists (the sessions sidecar is not listed), and reruns E3 entirely at B.
3. `emit e3` calls `prove_pinned_unchanged([A, B, B])`, and the A..HEAD diff names the fix.
4. WR-02 refuses a record whose seconds all came from B. Its message ("Every scripts/ change must land before launch") points the operator at re-probing, which leads into CR-01.

**Fix:** Pick one:

- In `run_front`, when the run sidecar is absent, start a fresh sessions list (stages are never resumed); or
- Have preflight treat a sessions sidecar without a run sidecar as a stray.

### WR-03: emit_all reconciles unconditionally, so running it during a live run closes the live attempt and undercounts the probes front

**File:** `scripts/phase36_probe.py:1290-1292`, `scripts/phase36_ledger.py:230-255`

**Issue:** `emit_all()` calls `phase36_ledger.reconcile()` first. `reconcile` closes *every*
open attempt with a `lost` line counted to the last beat, without checking that the run is dead.

If `emit-all` is run while the LaunchAgent is still running:

1. The live front's attempt is closed at "seconds so far".
2. When that front finishes, `run_front`'s `append("end")` refuses ("has no open attempt to end").
3. `run_all` aborts the remaining fronts.
4. The finished front's sidecar exists but no end line names its record. The probes front then
   counts only the partial lost seconds instead of the record's full `provenance.run` span. That
   changes a priced number (under operator mis-sequencing).

**Fix:** In `reconcile`, refuse an open attempt whose last beat is newer than about
2 × `phase25_watch.HEARTBEAT_SECONDS`. Or make `emit_all` refuse on open runs instead of
reconciling them, since the plan already runs `reconcile` as a separate, explicit step.

### WR-04: The T-36-05 append-only proof is never called on any production path

**File:** `scripts/phase36_ledger.py:130-143` (only callers: `tests/test_phase36_ledger.py:635-664`)

**Issue:** `prove_append_only` is the registered mitigation for T-36-05 ("ledger rewritten to
hide hours"). Nothing calls it except its test:

- `emit_all`'s `commit_path(LEDGER_PATH)` commits whatever bytes are on disk;
- `spent`, `require_launch` and `rule` read the working ledger unchecked.

A truncated or rewritten working ledger would therefore be committed or read silently. Examples:
a concurrent session restoring an older copy, or an editor reformatting the JSON lines. Dropping a
`lost` line would lower spent hours and the D-13 stops.

**Fix:** Call `prove_append_only()`:

- at the top of `require_launch`, `rule` and `reconcile`;
- in `emit_all` before `commit_path(ledger, ...)` when the ledger is already tracked.

### WR-05: dry() re-applies Rafael's cuts in the "E3 hours at recipes" loop, so it crashes or misprints once a cut is ruled

**File:** `scripts/phase36_budget.py:1005-1011`

**Issue:** The loop builds `caps` from `derived["unit_caps"]`, which are already post-cut, and
passes `**kwargs`, which still holds `cuts`. `derive` then applies every cut a second time.

**Verified:** I ran `dry(ruling)` against the planted records from `tests/test_phase36_budget.py`
(ad-hoc test in scratch, since deleted):

- `{"cuts": {"e2_seeds_to_3": 1}}` crashes with `[phase36_budget] S is already 3`. This happens
  after front_hours are printed and before FITS/HALT and the cut table.
- `{"cuts": {"e6_anchor_adapters": 3}}` subtracts twice inside the loop. Units ≥ 4 would refuse.
- `e1_checkpoints` with ≥ 3 units refuses.

This is the D-15 flow: HALT, then Rafael rules cuts, then a `dry --ruling` to show him the new
numbers. The fill (`committed_derive`) is unaffected.

**Fix:**

```python
for recipes in (E3_RECIPES, E3_RECIPES + 1):
    base = kwargs.get("unit_caps") or proposed_unit_caps(probes)
    caps = {f: dict(b) for f, b in base.items()}
    caps["E3"]["recipes"] = recipes
    alt = derive(probes, historical, probes_spent_seconds=spent, **{**kwargs, "unit_caps": caps})
```

## Info

### IN-01: PINNED_MODULES omits modules the E5/E6/E3 stages execute

**File:** `scripts/phase36_probe.py:85-103`

**Issue:** WR-02 and `module_sha256` cover phase19_erasure, phase14_recall, phase18_extraction,
teach_persona, phase25_points and others. They do not cover these modules, which the stages also
run:

- phase16_persistence (`resolve_forbid`), phase17_isolation, phase17_personas, phase17_persona_facts, phase14_factset;
- phase25_record (`prove_mechanism_matches_pin`);
- `src/personacore/lora`, `dialogue`, `tokenizer`.

A change to one of them between the run and emit is not detected, and the record does not hash it.

**Fix:** Add them to PINNED_MODULES as paths.

### IN-02: The plist comment and the 36-07 launch steps name different launchctl verbs

**File:** `artifacts/com.personacore.phase36.probe.plist:7-8`

**Issue:** The plist comment says `launchctl bootstrap` / `kickstart` / `bootout`. 36-07 Task 2
instructs `launchctl load` / `start` / `unload`. Both work, but the operator gets two different
procedures.

**Fix:** Align the comment with the plan's commands.

---

_Reviewed: 2026-10-02T16:02:09Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
