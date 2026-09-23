---
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
plan: 18
subsystem: privacy/budget-pin
tags: [noise-floor, re-scoped-in-place, additive-continuation, substring-trap, import-ceiling, watched-red, gap-closure]
status: COMPLETE
requires:
  - "results/phase23_matched_control.json (23-20) — FIVE per-seed readings; the source of every number and digest pinned here"
  - "scripts/phase23_prereg.py::noise_floor / FLOOR_PROVENANCE_KEYS / sigma_zero_verdict (23-03, c7de5d4, EDIT-ONCE, read-only)"
  - "scripts/phase23_matched_prereg.py::MATCHED_CONTROL_RECORD / SIGMA_ZERO_VISIBILITY_DISCLOSURE (23-15, c100388, frozen, read-only)"
  - "scripts/mitigation_budget.py — PROTECTED-BUT-NOT-FROZEN by 23-09's deliberate omission of a prereg_artifact="
provides:
  - "scripts/mitigation_budget.py::MATCHED_CONTROL_NOISE_FLOOR = 0.0267857142857143"
  - "scripts/mitigation_budget.py::MATCHED_CONTROL_NOISE_FLOOR_PROVENANCE — all 8 FLOOR_PROVENANCE_KEYS + record_file_sha256 + protocol + sigma_zero_was_visible"
  - "scripts/mitigation_budget.py — a dated `RE-SCOPED IN PLACE 2026-08-27 (plan 23-18).` continuation, purely additive"
  - "tests/test_phase23_budget.py — 5 new guards (7 -> 12 in the file)"
NOT_provides:
  - "results/phase23_matched_verdict.json — NOT written, NOT computed. 23-19 renders the verdict."
  - "any edit to CONTROL_NOISE_FLOOR — byte-unchanged, and re-derives from its own record as before"
affects:
  - "23-19 (reads MATCHED_CONTROL_NOISE_FLOOR + its provenance through phase23_prereg.sigma_zero_verdict)"
  - "23-13 (still able to write the Z values — the module stays unfrozen)"
tech-stack:
  added: []
  patterns:
    - "a superseded-in-scope-but-not-in-truth constant left BYTE-UNCHANGED with a dated continuation appended below it — dpsgd.py's 2026-08-27 register (8c2eea2), applied to a literal-only module where the continuation must be a COMMENT because only literal assignments may exist"
    - "a needle-uniqueness precondition lifted out of the test that depends on it and given its own named guard, with both routes to breaking it in the failure message"
    - "a one-ULP watched RED whose needle is LINE-ANCHORED from birth, so the new guard is not itself the next substring trap"
key-files:
  created: []
  modified:
    - scripts/mitigation_budget.py
    - tests/test_phase23_budget.py
decisions:
  - "TWO commits, not one. The plan's Task-2 action says commit both files together, but its own must_haves truth 7 says the pin lands as its OWN commit — and `tests/test_phase23_matched_prereg.py:390::test_the_closed_preregistrations_are_untouched` asserts scripts/mitigation_budget.py has neither an uncommitted NOR a STAGED modification. Holding the module edit through Task 2 would have kept a committed guard RED for the whole task."
  - "NO COLLISION, so `test_a_hand_edited_floor_is_detected` was NOT touched. repr(0.0267857142857143) != repr(0.05357142857142849), the needle count stayed 1, and the plan's sanctioned needle-strengthening repair was not made because it was not needed."
  - "The FOUR-clause one-attempt rule is written into the module at its true strength, including clause (3) 'PREVENTED BY NOTHING' and clause (4)'s 'DISCIPLINE, NOT A MECHANISM'."
requirements: []
metrics:
  duration: ~40 min
  completed: 2026-08-27
  tasks: 2
  files: 2
  commits: 3
---

# Phase 23 Plan 18: The Protocol-Matched Floor, Pinned Beside the Original — Summary

`MATCHED_CONTROL_NOISE_FLOOR = 0.0267857142857143` now lives at
`scripts/mitigation_budget.py:269`, and `CONTROL_NOISE_FLOOR = 0.05357142857142849` at
`scripts/mitigation_budget.py:113` is **byte-unchanged**. The diff across both commits is
**153 insertions, 0 deletions** measured with `git diff --numstat`.

**Commits:** `9eb792f` (the pin) · `3f9de69` (the guards) · plus this document's metadata commit.

## The value was RECOMPUTED, never retyped

The floor was obtained by **reading** `results/phase23_matched_control.json` and **calling**
`phase23_prereg.noise_floor` over the record's own per-seed `k`/`n` counts — the reduction committed
blind in 23-03 at `c7de5d4`, byte-unchanged since. It is never re-implemented here and the record's
own `floor` field is only ever a cross-check, never the source of the pin.

| seed (LADDER order) | k / n | rate |
|---|---|---|
| 1337 | 790/1008 | `0.7837301587301587` — **max**, and the pinned central reading |
| 2024 | 774/1008 | `0.7678571428571429` |
| 1338 | 778/1008 | `0.7718253968253969` |
| 2025 | 763/1008 | `0.7569444444444444` — **min** |
| 1339 | 773/1008 | `0.7668650793650794` |

`noise_floor` of those five = `0.7837301587301587 - 0.7569444444444444` = **`0.0267857142857143`**,
as counts `790/1008 − 763/1008 = 27/1008`, over 5040 scored draws on `mps` / torch 2.7.1 /
python 3.11.15.

## The substring trap: measured, avoided, and then given its own guard

`test_a_hand_edited_floor_is_detected` builds `needle = f"CONTROL_NOISE_FLOOR = {original!r}"` and
requires `source.count(needle) == 1`. That needle is a **substring** of
`MATCHED_CONTROL_NOISE_FLOOR = <same repr>`, so there were two ways for this plan to redden a
currently-green committed guard.

**Route 1 (prose) — avoided by construction.** The dated continuation refers to the original **by
name only** and never writes its literal assignment. Where the value appears at all it appears bare,
with no `NAME = ` prefix.

**Route 2 (repr collision) — MEASURED ABSENT.** `repr(0.0267857142857143)` vs
`repr(0.05357142857142849)`: different. The plan's sanctioned repair (line-anchoring the needle,
with the newline carried into the replacement) was therefore **not made**, and
`test_a_hand_edited_floor_is_detected` is **unchanged**.

Measured after the module edit, before any test was written, and again at the end:

```
$ grep -Fo "CONTROL_NOISE_FLOOR = 0.05357142857142849" scripts/mitigation_budget.py | wc -l
1
$ .venv/bin/python -m pytest tests/test_phase23_budget.py::test_a_hand_edited_floor_is_detected -q
1 passed in 0.02s
```

`-F` because `.` is a regex any-char; `-o` because `grep -c` counts LINES and the property under
test is `str.count`'s OCCURRENCE count. The AST cross-check (`ast.parse` + `Assign` target ids)
independently confirms the four top-level names, so the measurement does not rest on grep alone:

```
AST body       : ['Expr', 'Assign', 'Assign', 'Assign', 'Assign']
AST imports    : []
AST assign ids : ['CONTROL_NOISE_FLOOR', 'CONTROL_NOISE_FLOOR_PROVENANCE',
                  'MATCHED_CONTROL_NOISE_FLOOR', 'MATCHED_CONTROL_NOISE_FLOOR_PROVENANCE']
```

**`test_the_original_needle_is_still_unique` now makes that precondition a named rule** instead of
an assertion buried inside the test that depends on it, with both routes and the sanctioned repair
spelled out in its failure message — so the next editor of this file meets the rule before they
break it, not after.

And the new guard is **not itself the next trap**:
`test_a_hand_edited_matched_floor_is_detected` builds its needle line-anchored from birth
(`f"\nMATCHED_CONTROL_NOISE_FLOOR = {original!r}"`, with the `\n` carried into the replacement), and
a meta-guard asserts the scratch copy's ORIGINAL floor is unmoved — which is what proves the newline
survived rather than being silently swallowed.

## The import ceiling: zero headroom, still equal in both directions

`scripts/mitigation_budget.py` is **PROTECTED, NOT FROZEN** — the middle ground 23-09 deliberately
preserved by omitting a `prereg_artifact=`. This plan is the first consumer of it and left it
intact.

| Check | Result |
|---|---|
| AST `Import` / `ImportFrom` nodes in the module | `[]` |
| Measured union across every `scripts/mitigation_*.py` | `{erasure_gate, pathlib, sys}` — **unchanged** |
| `test_the_import_ceiling_still_has_zero_headroom` | PASS, **assertion unchanged** (docstring extended only) |
| `test_the_budget_module_is_protected_but_not_frozen` | PASS, **unchanged**; no `prereg_artifact=` added |
| `test_budget_holds_only_literal_constants` | PASS — both new constants are literal `Assign`s |

The new pin is literal assignments and comments only: no function, no `__main__`, no expression, and
above all no `import json` to read the record it cites. Everything the module needs to say about the
record is transcribed as a literal and asserted against the live file by the tests.

## What the continuation says, and why it is a continuation rather than an edit

The original floor is **not falsified**. It correctly measures the OLD control protocol and still
re-derives from `results/phase23_control_floor.json` on every suite run
(`test_budget_constants_re_derive`). What changed is its **SCOPE**. Editing it in place would have
destroyed a true reading and broken that guard.

So `scripts/mitigation_budget.py:155` opens
`# RE-SCOPED IN PLACE 2026-08-27 (plan 23-18).` and records:

- **What re-scoped it.** `.planning/debug/sigma-zero-beats-control.md` split the D-04 HALT between
  (A) INVALID COMPARATOR and (B) REAL DP-PATH DEFECT, attributed it to (A), and **falsified (B)**:
  at σ=0 with a non-binding `C = 1e6`, all **72 LoRA tensors** agree with an ordinary grad-accum
  reference to **`2.178e-07`** relative.
- **The three mechanisms, with their measured magnitudes.** Lot volume (65 vs 8 windows; teaching-
  token exposure `1,689,600` vs `196,867` = **8.58x**); teaching loss weight (`1.0` vs
  `p = 2719/6262 = 0.4342`, i.e. **2.30x**); `grad_clip = 1.0` applied to the control and
  **structurally absent** from the DP arm, binding on **19 of 25** control steps at mean shrink
  `0.8071`.
- **Which floor 23-19 consumes** (the matched one), and why the original is left standing anyway.
- **The substring rule, handed forward** in one paragraph naming
  `test_a_hand_edited_floor_is_detected` and both routes to breaking it.

A one-line dated continuation was also appended to the END of the module docstring's
"WHAT THIS FILE IS" paragraph, because that paragraph says *"Today that is ONE number"* and a stale
sentence in a pre-registration-adjacent file is exactly the defect 22-19 corrected. **The rest of
the docstring is byte-unchanged**, and `test_the_original_floor_is_left_standing_and_re_scoped`
asserts two distinctive sentences of the pre-23-18 comment block survive with `count == 1` — so a
"continuation" that quietly became a rewrite goes red.

## The ordering claim, stated at its weakest true strength

The original pin landed while `git ls-files results/phase23_sigma_zero.json` returned nothing.
**This one does not**, and the comment says so first rather than in a footnote: the σ=0 reading
`0.7837301587301587` was already committed and on screen throughout the design of the protocol this
floor reduces over.

- **Still blind** (all `c7de5d4`, byte-unchanged): the reduction, the central-reading rule
  `control_readings[0]`, `sigma_zero_verdict`, the seed ladder.
- **Also pinned before any reading existed:** the comparator's PROTOCOL, committed while
  `git ls-files 'results/phase23_matched_*'` returned nothing.
- **NOT blind:** which mechanisms to equalise.

The bound on that is written out with **FOUR clauses, not three** — (1) binds across commits only;
(2) `prior_scored_seeds_at_start` refuses only a delete leaving the `matched` section intact;
(3) a delete that also removes that section is **PREVENTED BY NOTHING**; (4) that case is
**auditable after the fact and only that**, from `cfa2c87` onward, because tracking is not
retroactive — *"a DISCIPLINE, NOT A MECHANISM, and it is not 'closed'."*

A three-clause version would have been the third printing of the same overclaim; this repository
already retracted that one twice.

## Citations verified against source, not carried forward

Per the repository's recorded history of plans naming paths and lines the code refuses, every
citation written into the module was re-measured today rather than copied:

| Citation | Measured |
|---|---|
| `src/personacore/training/loop.py:220-228` gates the clip on `dp_fn is None` | **EXACT** — `:220` is `if dp_fn is None:`, `:228` is `dp_fn.finalize(accum)` |
| `phase23_matched_prereg.MATCHED_CONTROL_RECORD` | `results/phase23_matched_control.json` — resolved from the module, never typed |
| `record_sha256` (INPUTS digest, the record's own field) | `5bb4216f…dd85`, asserted `== record["record_sha256"]` |
| `record_file_sha256` (the BYTES) | `4478005f…504c`, asserted against a live `sha256(read_bytes())` |
| `git_sha` | `d8f42639f1d71ae36c277cd48baa422e24ae5104` (the record's own) |
| `governs` | transcribed VERBATIM, asserted `== record["governs"]` |
| state ledger tracked at `cfa2c87`; record + state committed together at `04cdb21` | both confirmed by `git show --stat` |

Note the plan's `<interfaces>` block cited `CONTROL_NOISE_FLOOR` at `:108`; it was at `:108` before
this plan and is at **`:113`** after, because the docstring continuation added four lines above it.
Stated so the next reader does not re-derive the drift.

## Verification

| Check | Command | Result |
|---|---|---|
| Budget guards | `pytest tests/test_phase23_budget.py -q` | **12 passed** (7 before + 5 new) |
| **Full suite** | `.venv/bin/python -m pytest -q` | **`1543 passed, 1 skipped`** (83 warnings, 394.95 s) |
| Zero deletions | `git diff --numstat ccbc6cc HEAD -- scripts/mitigation_budget.py` | **`153  0`** |
| Needle unique | `grep -Fo "…" \| wc -l` | **1** |
| Zero imports | AST walk of the module | `[]` |
| Literal-only body | AST `tree.body` | `['Expr','Assign','Assign','Assign','Assign']` |
| Original unmoved | `mitigation_budget.CONTROL_NOISE_FLOOR` | `0.05357142857142849` |
| Matched re-derives | `noise_floor` over the record's own counts | `0.0267857142857143`, exact `==` |
| Closed pin | `git diff --exit-code c7de5d4 HEAD -- scripts/phase23_prereg.py` | **exit 0** |
| Frozen matched pin | `git diff --exit-code c100388 HEAD -- scripts/phase23_matched_prereg.py` | **exit 0** |
| …still ONE commit | `git log --format=%H -- <pin> \| wc -l` | **1** |
| Resume pin still ONE commit | `git log --format=%H -- scripts/phase23_resume_prereg.py \| wc -l` | **1** |
| Four scripts + three records | `git diff --exit-code` (plan's Task-2 list) | **exit 0** |
| Gate / accountant / teach / loop / debug doc | `git diff --exit-code 04cdb21 HEAD --` | **exit 0** |
| Lint | `ruff check . && ruff format --check .` | clean, 219 files |
| Working tree | `git status --short` | only the pre-existing `.gitignore` edit, untouched by this plan |

### Suite arithmetic, and why it is not the plan's number

**`1543 = 1538 + 5`.** The plan's acceptance criterion says `1523 passed, 1 skipped` (`1518 + 5`),
which is **stale by construction**: it was written against 23-17's `1518` baseline, and 23-20
subsequently added 19 tests in `tests/test_phase23_resume_prereg.py` plus 1 in
`tests/test_phase23_matched.py`. The orchestrator's brief supplied the corrected `1538` baseline and
it was independently re-measured this session (below). No pre-existing test changed status; no
existing test was deleted, weakened or rewritten.

**The five new tests** are exactly Task 2 items 2–6. Item 1 is helpers (`_matched_record`,
`_matched_readings`), item 7 is a docstring extension with the assertion untouched, item 8 is a
confirmation that an existing test still passes.

## Deviations from Plan

### 1. [Rule 3 — blocking issue] TWO commits, not one, and a committed guard is why

**The plan contradicts itself.** `must_haves` truth 7 says *"This pin lands as its OWN commit,
BEFORE the re-test runs"*; Task 2's `<action>` says *"commit `scripts/mitigation_budget.py` and
`tests/test_phase23_budget.py` in ONE commit."*

**Measured, and it settles it:** `tests/test_phase23_matched_prereg.py:390`
(`test_the_closed_preregistrations_are_untouched`) asserts, for a list that **includes
`scripts/mitigation_budget.py`**:

```python
assert _git("diff", "--", frozen) == "", f"{frozen} has an uncommitted modification"
assert _git("diff", "--cached", "--", frozen) == "", f"{frozen} has a STAGED modification"
```

Holding the module edit through Task 2 would have kept that committed guard **RED for the entire
task**, including every intermediate suite run. Followed `must_haves` truth 7 and the executor's
per-task commit protocol: `9eb792f` (module), `3f9de69` (tests). Recorded rather than absorbed,
because the plan's literal Task-2 instruction was not followed.

### 2. [Procedural] The stale suite-count criterion, with its cause

Covered above: `1523` in the plan vs `1543` measured. Cause is 23-20 landing 20 tests after 23-18
was written. Recorded with its cause rather than accepted silently, as the criterion itself
requires.

### 3. [Procedural] The first baseline measurement raced this plan's own edit

The baseline suite run was launched in the background at plan start and took 376 s; the Task 1
module edit landed inside that window. It reported **`1 failed, 1537 passed, 1 skipped`**, and the
single failure was exactly `test_the_closed_preregistrations_are_untouched` observing the
then-uncommitted `scripts/mitigation_budget.py`. **Collected total `1537 + 1 = 1538`** confirms the
baseline the orchestrator supplied and 23-20 reported. Disclosed rather than quietly re-run, because
a reader of the logs would otherwise meet an unexplained RED. The clean post-plan suite run
(`1543 passed, 1 skipped`) was performed with the module already committed.

### 4. [Procedural] Two line-length fixes to this plan's OWN new docstrings

`ruff` (line-length 100) rejected two lines in the new tests at 102 and 101 characters. Both were
reworded before commit. No existing line was touched; no assertion was affected.

### 5. The collision branch did NOT occur, so nothing was repaired

Recorded explicitly because the plan carved out a sanctioned repair for it and a reader may go
looking for that repair. `repr(MATCHED_CONTROL_NOISE_FLOOR)` = `'0.0267857142857143'`,
`repr(CONTROL_NOISE_FLOOR)` = `'0.05357142857142849'`. Not equal. The needle count is 1,
`test_a_hand_edited_floor_is_detected` is byte-unchanged, and **no needle was strengthened**.

**No authentication gates occurred. No package was installed. No training was run.**

## D-04 HALT compliance

**The halt stands and was not touched. No verdict was rendered, computed, printed or recorded.**

| Check | Result |
|---|---|
| `git ls-files 'results/phase23_noised_*'` | **0** at start and at end |
| `results/phase23_matched_verdict.json` | confirmed **ABSENT** |
| `sigma_zero_verdict` called against a REAL σ=0 reading | **NO** — the two calls in the suite pass a **SYNTHETIC** reading (each arm's own `readings[0]`, deviation exactly zero) and are labelled as such at the call site |
| `results/phase23_sigma_zero.json`, `results/phase23_control_floor.json`, `results/phase23_matched_control.json` | byte-unchanged vs `04cdb21` (`git diff --exit-code`, exit 0) |
| `scripts/mitigation_gate.py`, `scripts/mitigation_accountant.py`, `scripts/teach_persona.py`, `src/personacore/training/loop.py`, `.planning/debug/sigma-zero-beats-control.md` | byte-unchanged |
| 23-11…23-14 | still **BLOCKED**; nothing in this plan touches their scope |

The σ=0 reading (`0.7837301587301587`) and the matched central reading (`0.7837301587301587`) are
both stated in the module as **numbers**, never compared. The comparison is 23-19's.

## Requirements

**NO requirement is ticked, and `requirements mark-complete` was not called.** The plan's
`success_criteria` says so explicitly. `DPSGD-06` appears in the plan frontmatter but is **already**
`[x] SATISFIED (plan 23-10)` — its tick records that the diagnostic FIRED and that D-04 halted the
sweep, not a passing verdict. It was not re-touched. CAL-01, CAL-02, CAL-05 and CTRL-03 remain
23-11…23-14's BLOCKED scope.

## Known Stubs

None. Both constants carry real measured values from a committed record, both re-derive under exact
`==` on every suite run, and no placeholder was added.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema at a trust boundary. No
package was installed (T-23-SC holds). Every threat in the plan's register was mitigated as
specified: T-23-72 (re-derivation under `==` + a watched one-ULP refusal), T-23-72b (the substring
rule, plus its own named guard, plus a line-anchored sibling), T-23-73 (zero deletions by
`--numstat` plus byte-identical-substring assertions), T-23-74 (protected-but-not-frozen intact),
T-23-75 (AST zero-import assertion plus the unchanged equality ceiling).

## gsd-sdk regressions this session (EIGHTEENTH, NINETEENTH and TWENTIETH in a row)

`git diff .planning/` read after **every** call; snapshots of both files taken before the first.
All corruptions hand-repaired 1-line-for-1-line against the snapshot.

| Handler | Behaviour |
|---|---|
| `state.record-session` | **FOUR corruptions in one call.** (1) Flattened frontmatter `status:` from `executing` into a fragment of the BODY's D-04 warning prose (`**D-04 FIRED AT 23-10. …** The σ=0 diagnostic read`). (2) **REGRESSED `stopped_at` to STALE 23-17 text**, destroying 23-20's correct value — it appears to read the body's stale `Stopped at:` line and write it back over a newer frontmatter. (3) Set `completed_plans` `60 -> 62` (correct value 61). (4) Injected a spurious blank line at `:812`. And it left the body `Stopped at:` line — the thing it claims to update — **stale**. |
| `roadmap.update-plan-progress 23` | **The most damaging call of the session, on two counts.** (1) It **FALSELY TICKED `23-17-PLAN.md` as `[x]`** — 23-17 is INCOMPLETE, its run was harness-killed at 3/5 and wrote no record. The handler keys on SUMMARY **existence**, which is exactly the INDEX TRAP `STATE.md` documents by name. A false completion claim in the roadmap is worse than a stale one. **Reverted by hand, with the reason written into the line so the next run's re-tick is legible rather than mysterious.** (2) It **DESTROYED the phase-23 progress row's status**, replacing `HALTED (D-04) — 23-11..23-14 still BLOCKED. …` with a bare `In Progress` and BLANKING the notes column — wiping the D-04 HALT record this plan was explicitly required to preserve. Restored and updated by hand. The only correct thing it did was tick 23-18 and move `14/20 -> 15/20`. |
| `state.record-metric` | The row itself was CLEAN (`\| Phase 23 P18 \| 40 min \| 2 tasks \| 2 files \|`), and it accepted `--phase/--plan/--duration/--tasks/--files` (it still refuses positional args, as 23-09 measured). But it **re-corrupted TWO already-repaired fields**: `status:` back into the same body-prose fragment, and `completed_plans` back from the hand-set `61` to `62`. Both had been repaired earlier in this same session, by hand, minutes before. Repaired again, and re-verified after. |
| `state.advance-plan`, `state.update-progress`, `state.add-decision` | **NOT CALLED.** 23-07 and 23-09 established the measured practice for `add-decision` (it corrupts the phase label on every call since 22-16 and reverts `completed_plans` from a stale read); given that `record-session` had already regressed `stopped_at` and mis-set `completed_plans` in this same session, the position counters were set by hand instead. Decisions are hand-written in this document's frontmatter. |

**Verified after repair:** `status: executing`; `stopped_at` and the body `Stopped at:` agree;
`completed_plans: 61`; `grep -c 'BLOCKED\|D-04' .planning/STATE.md` = **13, unchanged**;
`grep -c 'HALTED (D-04)' .planning/ROADMAP.md` = **1**; `23-17-PLAN.md` is `[ ]`;
`23-18-PLAN.md` is `[x]`; `ROADMAP.md` line count unchanged at **849**.

## Notes for 23-19

1. **The floor to read is `mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR = 0.0267857142857143`**,
   with `MATCHED_CONTROL_NOISE_FLOOR_PROVENANCE` as its `floor_provenance` argument. That dict is a
   working argument today: the suite already drives it through `sigma_zero_verdict` and it is
   ACCEPTED (the three extra keys — `record_file_sha256`, `protocol`, `sigma_zero_was_visible` — do
   not offend the frozen consumer, which checks key PRESENCE, not key set equality).
2. **`control_readings` must be the matched readings in LADDER order**
   `(1337, 2024, 1338, 2025, 1339)`, never sorted. `sigma_zero_verdict` re-derives the floor from
   whatever list it is handed and the central-reading rule is `control_readings[0]`;
   `_matched_readings()` in `tests/test_phase23_budget.py` returns exactly that order.
3. **`sigma_zero_verdict` re-derives the floor from `control_readings` and refuses a mismatch with
   a message containing `"re-derives"`.** Hand it the matched readings and the matched floor, or it
   halts for the wrong reason.
4. **Do not edit `scripts/mitigation_budget.py` without reading the handed-forward paragraph at
   `:193`.** The original's literal assignment string must occur exactly once in that file;
   `test_the_original_needle_is_still_unique` is now the named guard, and the sanctioned repair for
   a future collision is to line-anchor the needle, never to rename, round or weaken.
5. **The ordering claim in the module is deliberately weaker than 23-09's** and says so. Do not
   restate it more strongly in the verdict record.

## Self-Check: PASSED

- `scripts/mitigation_budget.py` — FOUND; `MATCHED_CONTROL_NOISE_FLOOR` at `:269`,
  `MATCHED_CONTROL_NOISE_FLOOR_PROVENANCE` at `:277`, marker at `:155`, original unmoved at `:113`
- `tests/test_phase23_budget.py` — FOUND; 12 tests passing, helpers at `:281`/`:292`, the five new
  guards at `:644`, `:693`, `:790`, `:863`, `:907`
- `results/phase23_matched_control.json` — FOUND, unmodified, and its live `sha256` matches the
  pinned `record_file_sha256`
- Commit `9eb792f` — FOUND in `git log`
- Commit `3f9de69` — FOUND in `git log`
- `scripts/phase23_prereg.py` — byte-identical to `c7de5d4`
- `scripts/phase23_matched_prereg.py` — byte-identical to `c100388`, still ONE commit
- `scripts/phase23_resume_prereg.py` — still ONE commit
- `git ls-files 'results/phase23_noised_*'` — **0**
- `results/phase23_matched_verdict.json` — confirmed ABSENT
