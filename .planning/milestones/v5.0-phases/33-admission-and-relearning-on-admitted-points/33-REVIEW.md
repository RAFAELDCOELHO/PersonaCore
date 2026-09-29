---
phase: 33-admission-and-relearning-on-admitted-points
reviewed: 2026-09-28T00:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - scripts/phase33_admission.py
  - tests/test_phase33_admission.py
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 33: Code Review Report

**Reviewed:** 2026-09-28
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

I reviewed the admission driver and its test file. `tests/test_phase33_admission.py` passes
40/40 on this host. The committed record `results/phase33_admission.json` (f48b738) is
consistent with the code:
- `provenance.git_sha` and `head_at_write` are both `92fe48b`, the parent of f48b738.
- The limitation fields are bound from the admission reasons and the frontier tallies.

Two latent defects in the driver would have produced a wrong or extra admission record if `admit`
had been invoked differently. Neither fired on the one real call, and `admit` now refuses on the
existing record. So no fix is needed for the shipped result.

**Pin cost.** `scripts/phase33_admission.py` is pinned by sha256 in
`results/phase33_admission.json`. Any edit to it breaks `test_provenance_digests_match_live_bytes`
and needs a dated pin continuation. Re-admission is impossible by design. For that reason every
driver finding below is recommended as a **ledger row or a note for the next milestone's
driver**, not an in-place edit.

No BLOCKER is reported. Neither driver defect can change the committed record or run again.

## Warnings

### WR-01: `git_sha()` reads the process cwd, not `_GIT_ROOT`, so `admit` run from another directory publishes `"unknown"` or a foreign SHA

**File:** `scripts/phase33_admission.py:44`, `:190-191` (callee `src/personacore/provenance.py:28-44`)

**Issue:** The two calls behave differently when run from outside the repo:
- `personacore.provenance.git_sha()` runs `git rev-parse HEAD` with no `cwd`. From outside the
  repo it returns `"unknown"`. From inside another git repo it returns that repo's HEAD.
- `refuse_if_dirty` is passed `cwd=_GIT_ROOT`. So the dirty check passes on the real repo, and
  `admit` writes a record whose `git_sha` and `head_at_write` do not name the commit it came from.

That is the exact falsification the dirty guard's `detail` string says it prevents. `_resolve`
anchors the output path at `_GIT_ROOT`, so the bad record lands at the real
`results/phase33_admission.json`.

**Reproduction:**
- Import from /tmp: `cd /tmp && /Users/juliorcoelho/PersonaCore/.venv/bin/python -c "import sys; sys.path.insert(0,'/Users/juliorcoelho/PersonaCore/scripts'); import phase33_admission as d; print(repr(d.INSTRUMENT_GIT_SHA))"` prints `'unknown'`.
- Full `admit()` against a scratch repo (with `_GIT_ROOT` patched, run from the scratchpad cwd)
  wrote a record with `git_sha: unknown`, `head_at_write: unknown`.

**Not triggered on the real record:** it carries `92fe48b…` in both fields, so the one call was
made from the repo root.

**Fix (next milestone's driver, not this pinned file):** pass the repo into the SHA read, and
refuse a sentinel:
```python
sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=_GIT_ROOT,
                     capture_output=True, text=True, check=True).stdout.strip()
```
Alternatively, give `git_sha` a `cwd` parameter. Refuse to write when the SHA is `"unknown"`.
Editing `provenance.py` is the root-cause fix for every caller, but check which records pin it
first.

### WR-02: `--out` bypasses write-once: admission can be re-run without limit to any path outside the repo

**File:** `scripts/phase33_admission.py:151-175`, `:248`

**Issue:** The write-once guards all key on the path `out`:
- the overwrite refusal (`out.exists()`);
- the committed-at-HEAD refusal (`_committed(out)`, which returns `False` for any path outside
  `_GIT_ROOT`).

So `admit --out /tmp/a.json`, `--out /tmp/b.json` and so on each write a complete, authentic-looking
admission record. That includes `git_sha` and the module pins. Inside the repo, one extra
`--out results/<other>.json` also succeeds, because that file is untracked and not dirty until
after the write.

The module docstring and D-06 say "there is no `--force`". `--out` acts as one, just for another
path. The canonical-path git tests (`test_the_record_was_committed_exactly_once_alone`) still hold.
But the ADMIT-02 claim "called exactly once" depends on convention, not on code.

**Reproduction:** In a scratch repo, after `admit()` wrote the canonical record,
`admit(out_path="<scratch>/o1.json")` and `admit(out_path="<scratch>/o2.json")` both wrote records.
Both printed `wrote o1.json` / `wrote o2.json`.

**Fix (next milestone's driver):** drop `--out` from the CLI, or refuse any `out` that does not
resolve to `_GIT_ROOT / RECORD_PATH`:
```python
_prove(out.resolve() == (pathlib.Path(_GIT_ROOT) / RECORD_PATH).resolve(),
       f"{rel} is not {RECORD_PATH} — REFUSING: the record path is derived, never chosen")
```
Tests can keep patching `_GIT_ROOT`.

## Info

### IN-01: A malformed or keyless record makes a leg crash with a traceback instead of a `[phase33_admission]` refusal

**File:** `scripts/phase33_admission.py:219`

**Issue:** `json.loads(...)["admission"]["verdict"]` raises `JSONDecodeError`, `KeyError` or
`TypeError` on a bad record. The leg still exits non-zero and never runs a body, so the refusal
property holds. But the output is a stack trace, not the D-01 refusal message.

**Reproduction:** `echo '{"x":1}' > /tmp/r.json && .venv/bin/python scripts/phase33_admission.py gate --record /tmp/r.json` ends in `KeyError: 'admission'`.

**Fix:** wrap the read in `try/except (ValueError, KeyError, TypeError)` and route it through
`_prove`. Record this as a note for the next driver; it is not worth a pin continuation.

### IN-02: The admit refusal message names a redo route that the suite then fails on permanently

**File:** `scripts/phase33_admission.py:157-158`; `tests/test_phase33_admission.py:307-310`

**Issue:** The overwrite refusal says "The only route is to delete it in its own commit (D-06)".
Following that route leaves the record absent with a non-empty `git log`. Then
`test_the_record_was_committed_exactly_once_alone` asserts `not tracked and not commits` and fails
for good.

This is consistent with "re-admission is impossible by design". But the message advertises a path
that the guards forbid.

**Reproduction:** unreproduced. It would require committing a deletion in the real repo. It follows
directly from lines 307-310: an absent record with ≥1 commit in `git log -- <record>` fails the
assert.

**Fix:** reword the message in a future driver, for example "re-admission is closed by ADMIT-02".
Or record in the ledger that D-06's route is superseded by D-07.

### IN-03: `limitation()` keeps only the first leg-prefixed reason

**File:** `scripts/phase33_admission.py:131-133`

**Issue:** `legs[leg] = own[0]` silently drops any later reason that also starts with `"{leg} "`.
On the committed frontier each leg has at most one such reason, so the real record is complete.

**Reproduction:** unreproduced on real data. It is latent: `phase29_prereg.admission` emits one
per-leg reason today.

**Fix:** `legs[leg] = "; ".join(own)`, in a future driver.

---

_Reviewed: 2026-09-28_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
