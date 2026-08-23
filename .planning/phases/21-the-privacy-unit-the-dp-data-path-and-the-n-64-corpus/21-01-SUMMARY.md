---
phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
plan: 01
subsystem: pre-registration / privacy accounting
tags: [prereg, ancestry-guard, differential-privacy, frozen-module, deliberate-red]
requires:
  - tests/test_phase20_prereg.py::_assert_ordering_holds  # the Phase 20 ancestry mechanism, called not copied
  - scripts/mitigation_gate.py:66                          # the `_prove` register mirrored here
provides:
  - scripts/mitigation_unit.py                             # PRIVACY_UNIT, SAMPLING_RATE_Q, privacy_n, DELTA, rejected_delta
  - tests/test_phase20_prereg.py::PHASE21_PREREG_ARTIFACT  # the constant that confers the freeze
  - tests/test_phase20_prereg.py::V4_ARTIFACT_GLOBS        # widened with results/phase21_*
affects:
  - plan 21-11  # writes the first results/phase21_* artifact; deletes/inverts the honest-arming test
  - plan 21-08  # D-11's replay VOLUME constant, deliberately NOT in the frozen module
  - Phase 22    # consumes q=1 / N=n_facts / delta=1e-5 for the DP-SGD accountant
tech-stack:
  added: []       # zero new dependencies; pyproject.toml untouched (RPT-03)
  patterns:
    - "arm-then-write: the ancestry guard is armed in the phase's FIRST plan, before any artifact exists"
    - "deliberate-RED then byte-identical restore, sha256-proven on both cycles"
    - "rule/emission split: the frozen rule imports nothing; the artifact writer lives outside the glob"
key-files:
  created:
    - scripts/mitigation_unit.py
    - tests/test_phase21_unit_pin.py
  modified:
    - tests/test_phase20_prereg.py
decisions:
  - "The pin imports NOTHING (not even the 3 names D-22 permits) — the cheapest way to stay inside the ceiling"
  - "`_prove` is defined locally rather than imported from mitigation_gate — a forced consequence of D-22, recorded so it does not read as a copied instrument"
  - "The rejected-recipe products are asserted with pytest.approx(rel=1e-12), not ==, because `n ** -1.1` routes through libm pow (see commit 4554c93)"
  - "The 262.9 multiplicity figure is committed WITH its formula, because the naive reading of its stated denominator gives 54.03"
metrics:
  tasks: 3
  commits: 3
  duration: ~1h
  completed: 2026-08-23
---

# Phase 21 Plan 01: The Frozen Privacy-Unit Pin Summary

Committed `scripts/mitigation_unit.py` — a zero-import, zero-I/O pre-registration of what one
privacy record IS (`PRIVACY_UNIT = "one taught fact"`, `q = 1`, `N = n_facts`, `delta = 1e-5`) — and
armed the Phase 20 ancestry guard against `results/phase21_*` in **both** required halves, before any
such artifact exists.

## What Was Built

| Task | Artifact | Commit |
|---|---|---|
| 1 | `scripts/mitigation_unit.py` — D-23's three settled decisions, five module-level `_prove` guards | `8d3beb4` |
| 2 | `tests/test_phase21_unit_pin.py` — 11 tests, 6 under `-k prove_guards` | `7347472` |
| 3 | `tests/test_phase20_prereg.py` — 3 additive edits, 2 new live tests | `21ed755` |

**The pin's own history**, as the plan's `<output>` requires so a later reader can check it:

```
$ git log --format=%H -- scripts/mitigation_unit.py
8d3beb446f08327f9df242420b900f15baf670b3
```

Exactly one commit. Every later commit touching this path is read by `:143` and must be an ancestor
of every `results/phase21_*` first-add — so this list is the thing to re-check, not the file's mtime.

## The Two Deliberate-RED Cycles

Both were **watched failing** and restored **byte-identically**. A guard nobody has seen fail is a
guard nobody has verified.

**Cycle 1 — the module-level `_prove` (Task 2).** Set `DELTA = 1e-3`:

```
[mitigation_unit] delta * 64 = 0.064 against the ceiling 0.01. This is the TIGHTER of the two
capacities — it clears by 0.15625x against 1.25x at n = 8 — so it is the check that actually binds
EXIT CODE: 1
```

| | sha256 of `scripts/mitigation_unit.py` |
|---|---|
| before | `45f37e152bb4035667b804c1463431b3f12fa5096c47de32b1dc27abbe000473` |
| after | `45f37e152bb4035667b804c1463431b3f12fa5096c47de32b1dc27abbe000473` |

`git diff --exit-code scripts/mitigation_unit.py` → `0`.

**A finding the plan predicted but did not claim, now measured.** The RED fired at **N=64 only**:
`1e-3 * 8 = 0.008` still clears the `0.01` ceiling, so the n=8 guard **passed under the same
mutation**. The n=64 row is therefore load-bearing rather than a stronger-sounding duplicate — the
plan's "wrong at BOTH capacities" design is now supported by an observation, not by an argument.

**Cycle 2 — the both-halves claim (Task 3).** Reverted `V4_ARTIFACT_GLOBS` to
`("results/phase20_*",)` while KEEPING the new test:

```
E  AssertionError: results/phase21_* is not in ('results/phase20_*',) — this guard and the
   declared artifact set would be watching two different sets of paths
1 failed, 1 passed, 18 deselected
```

| | sha256 of `tests/test_phase20_prereg.py` |
|---|---|
| before | `ebdbc5fdabc3016bef78afe33aace480b9ab7575b402c613050e95af1f052104` |
| after | `ebdbc5fdabc3016bef78afe33aace480b9ab7575b402c613050e95af1f052104` |

`git diff --exit-code tests/test_phase20_prereg.py` → `0`.

Only the ordering guard went red; `test_phase21_has_no_artifact_yet_so_the_arming_is_honest` stayed
green because it never reads `globs`. That is the exact scope of what half 1 is load-bearing for.

## Plan Claims Falsified by Measurement

Reported rather than silently adapted around, per this repository's standing discipline. **The plan
was not amended** — plans are records.

**1. The `262.9` multiplicity figure lacked its formula, and its stated denominator invites a
different number.** `21-01-PLAN.md:142-143` says "at `MAX_STEPS = 200` x `BATCH_SIZE = 8` = 1,600
draws over the 7,581-token facts-only bin, the expected touches per fact is 262.9". The reading that
denominator invites is `1600 * 256 / 7581 = 54.03`. Measured, the D-26 figure is the window-**overlap**
expectation:

```
1,600 * (947.625 + 256) / (7,581 - 256 - 1) = 262.9437     # matches D-26's 262.9
1,600 * (947.625 + 256) / (15,162 - 256 - 1) = 129.2050    # matches D-26's other row, 129.2
```

The figure is **correct**; only the route to it was unstated. Both D-26 rows reproduce from the one
formula, which is what confirms it is the intended one. The formula is now written into the frozen
module (Rule 2 — a number nobody can reproduce cannot be corrected inside a file only a dated
continuation may touch).

**2. `tests/test_phase20_prereg.py` had 18 tests at HEAD, not 21.** The plan's Task 3 acceptance
requires "all pass (21+ tests)"; `21-VALIDATION.md:50` and `21-RESEARCH.md` both state "1.86s / 21
tests". Measured at `ef2839f` before any edit: **18 collected**. This plan adds 2, so the file is now
**20**. The "21+" criterion was unsatisfiable as written and the miscount predates this plan. The
green condition used instead: **20 passed, and `-k phase21` collects 2** (the plan's other, correct,
criterion).

**3. The Task 3 RED was predicted at `:129`; it fired at `:157`.** Same assertion, same message —
edits 1 and 2 add 28 lines above it. The plan's `:129` was accurate against the pre-edit tree only.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Float equality on `rejected_delta(n) * n` would be a cross-platform flake**
- **Found during:** Task 2
- **Issue:** The plan's `<behavior>` says the products "equal `0.8122523963562354` / `0.6597539553864469`". `n ** -1.1` is a non-integer power routed through the platform's libm `pow`, which is not guaranteed bit-identical across CPU families. CI runs x86_64 Linux; development runs arm64 Darwin. Commit `4554c93` — the tip of `main` before this phase — is a fix for exactly this class ("inv_cdf not bit-reproducible across CPU/libm").
- **Fix:** `pytest.approx(..., rel=1e-12)` on the two products, with the reason recorded in the module. That is ~4 orders looser than a 1-ulp (~1e-16) libm disagreement and ~14 orders tighter than the 66x–81x effect being asserted, so it cannot mask the finding. The `>= 0.01` **inequalities are left exact** — with 66x of margin they need no slack.
- **Files modified:** `tests/test_phase21_unit_pin.py`
- **Commit:** `7347472`

**2. [Rule 2 — Missing critical record] The analytic multiplicity number shipped without its formula**
- **Found during:** Task 1 (see falsification 1 above)
- **Fix:** the overlap formula and the explicit rejection of the naive reading are now inside `PRIVACY_UNIT_ARITHMETIC`.
- **Files modified:** `scripts/mitigation_unit.py`
- **Commit:** `8d3beb4`

### Process Error, Self-Inflicted and Recovered

During Task 3's first RED cycle I ran `git checkout tests/test_phase20_prereg.py` while my three
edits were **unstaged**, which restored from the index (= HEAD) and discarded all of them. Re-applied
from context and confirmed the recovery was exact: the re-applied file hashes to
`ebdbc5fdabc3016bef78afe33aace480b9ab7575b402c613050e95af1f052104`, the value recorded before the
loss. The RED cycle was then redone with the edits **staged first**, so the restore point was the
intended one. Recorded because the correct procedure is not obvious: for a deliberate-RED on a file
with uncommitted work, stage before mutating.

No `git stash`, no `git clean`, no `git reset` was used at any point.

## Requirements — Deliberately NOT Marked Complete

`UNIT-01`, `UNIT-04`, `UNIT-05` are this plan's `requirements:` frontmatter, and **none is marked
complete here.** Two reasons, both from the phase's own record:

- `21-CONTEXT.md` `<code_context>` names *"Over-claim avoidance — do not mark a requirement complete
  in the first plan that touches it"* as an Established Pattern.
- D-26 requires UNIT-01's multiplicity to be **measured** on an instrumented loader and written to
  `results/phase21_*`, which is **plan 21-11**. This plan ships the analytic expectation and says so
  in the module. Marking UNIT-01 complete on an expectation is precisely the substitution UNIT-03
  exists to refuse.

`REQUIREMENTS.md` was therefore not modified. Per the orchestrator's instruction, `STATE.md` and
`ROADMAP.md` were not touched either.

## Verification

```
$ .venv/bin/python -m pytest -q tests/test_phase20_prereg.py tests/test_phase21_unit_pin.py \
    tests/test_package.py tests/test_masked_batch.py tests/test_phase14_teaching.py
75 passed in 3.90s

$ .venv/bin/python -m pytest -q tests/test_phase20_prereg.py -k phase21
2 passed, 18 deselected

$ .venv/bin/python -m pytest -q tests/test_phase21_unit_pin.py -k prove_guards
6 passed, 5 deselected                       # plan requires >= 4

$ git ls-files 'results/phase21_*'                                    # empty
$ git log --diff-filter=A --format=%H -- 'results/phase21_*' | wc -l  # 0
$ git status --porcelain results/                                     # empty
$ git diff --exit-code scripts/mitigation_gate.py scripts/phase18_extraction.py   # 0
$ .venv/bin/python -m ruff check . && .venv/bin/python -m ruff format --check .
All checks passed! · 178 files already formatted
```

**SC5 non-disturbance, checked beyond the plan's block.** `scripts/mitigation_unit.py` joins four
broader scans I found while resolving the glob mechanics — `scripts/*.py` file-set walks in
`test_phase14_scoring.py:461` (the D-21 `persona=` guards), `test_lora_inject.py:279`,
`test_phase17_stats.py:327` and `test_phase19_erasure.py:1386` (the `retention_perplexity` census).
None is named in the plan. Ran them explicitly: **371 passed, 2 skipped in 42.83s**. Both skips are
`test_phase14_demo.py` gitignored-checkpoint skips, expected in a worktree.

## Known Stubs

None. Every constant in the pin is a settled decision with its arithmetic; nothing is a placeholder.

The one deliberate absence is recorded in the module and is not a stub: D-11's replay **volume**
constant (D-24) is excluded by D-23 and lands in `scripts/teach_persona.py` in plan 21-08. The
unfrozen `mitigation_*.py` sibling of D-21 is likewise **not created** — an empty module would join
the import-graph scan while being green over nothing.

## Threat Flags

None. This plan adds no network endpoint, no auth path, no file access and no schema at a trust
boundary. `scripts/mitigation_unit.py` is a constants module that imports nothing and performs no
I/O; the two test edits read git history through the existing `_git` helper, which passes argv
directly with no `shell=True`.

Dispositions from the plan's register, all `mitigate`, all satisfied: T-21-03 (post-hoc edit —
caught by `:143` reading every commit), T-21-06 (`git rm` laundering — `adds[-1]`, and no artifact
was written), T-21-05 (unenforced declaration — cycle 2 above), T-21-13 (ceiling widening — zero
imports, asserted twice), T-21-07 (`phase21_`-named probe in real history — asserted empty).

## Self-Check: PASSED

Files claimed as created, verified present:

- `scripts/mitigation_unit.py` — FOUND
- `tests/test_phase21_unit_pin.py` — FOUND
- `tests/test_phase20_prereg.py` — FOUND (modified)

Commits claimed, verified in `git log`:

- `8d3beb4` — FOUND
- `7347472` — FOUND
- `21ed755` — FOUND
