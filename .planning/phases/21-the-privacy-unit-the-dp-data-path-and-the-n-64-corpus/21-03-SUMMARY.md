---
phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
plan: 03
subsystem: pre-registration / ancestry guard
tags: [prereg, ancestry-guard, deliberate-red, throwaway-repo, non-vacuity, mutation-testing]
requires:
  - tests/test_phase20_prereg.py::_assert_ordering_holds   # called, never copied
  - tests/test_phase20_prereg.py::PHASE21_PREREG_ARTIFACT  # armed by plan 21-01
  - tests/test_phase20_prereg.py::V4_ARTIFACT_GLOBS        # widened by plan 21-01
provides:
  - tests/test_phase20_prereg.py::test_phase21_glob_sees_the_phase21_prefix_red_then_green
affects:
  - plan 21-11  # commits the first results/phase21_* artifact; state 5 rehearses that exact transition
tech-stack:
  added: []      # zero new dependencies; pyproject.toml untouched (RPT-03)
  patterns:
    - "prove-the-guard-bites: drive an armed-but-vacuous guard through RED/GREEN in a tmp_path repo"
    - "mutation observed at BOTH tiers, restored byte-identically, sha256-proven on all three cycles"
    - "reference assertions BY NAME, never by line number — this phase's anchors drift under additive edits"
key-files:
  created:
    - .planning/phases/21-.../deferred-items.md
  modified:
    - tests/test_phase20_prereg.py
decisions:
  - "State 5 uses results/phase21_privacy_unit.json — resolved from plan 21-11's frontmatter, the first artifact it commits"
  - "The new docstring cites assertions by NAME, not by line number, because every line anchor in this phase's plans has drifted"
  - "Mutation A was run in TWO variants because the plan's literal wording and its predicted observable are not the same mutation"
metrics:
  tasks: 2
  commits: 1     # task 2 is an OBSERVATION task — the plan forbids committing either mutation
  duration: ~1h
  completed: 2026-08-23
---

# Phase 21 Plan 03: Proving the `results/phase21_*` Guard Is Live Summary

Added `test_phase21_glob_sees_the_phase21_prefix_red_then_green` — a five-state throwaway-repo
fixture that drives the `results/phase21_*` ancestry guard RED, GREEN, RED and GREEN again, so the
prefix is **observed matching** before plan 21-11 lands the first artifact rather than inferred from
the pattern's text. Then watched the guard fail under two named mutations at both tiers and restored
byte-identically each time.

## What Was Built

| Task | Artifact | Commit |
|---|---|---|
| 1 | `tests/test_phase20_prereg.py` — the five-state fixture, +175 lines | `76926ef` |
| 2 | Three mutation cycles, observed and reverted — **no commit, by design** | — |

## The Five States, Each OBSERVED

Every state was driven and its real result recorded. None was argued from the code's shape.

| State | Setup | Result | The observable that makes it non-vacuous |
|---|---|---|---|
| 1 | probe committed, NO pin | **RED** | `AssertionError` naming `scripts/mitigation_unit.py` — the `assert prereg_commits` branch, not "something raised" |
| 2 | pin committed SECOND | **RED** | `git ls-files results/phase21_*` → `['results/phase21_probe.json']` asserted FIRST (the positive prefix observation), then `cmd[:3] == ("git","merge-base","--is-ancestor")` |
| 3 | `git rm` the probe | **GREEN** | `ls-files` → `""`; the red is reversible ONLY by having no artifact |
| 4 | re-add at the IDENTICAL path | **RED** | `len(adds) == 2` and `adds[-1] == state1_add` — laundering impossible across a real cycle |
| 5 | probe gone, real artifact AFTER the pin | **GREEN** | `checked = 1`, non-zero |

**`checked` at state 5 = 1, OBSERVED not inferred.** `_assert_ordering_holds` does not return
`checked`, so it was measured by wrapping `subprocess.run` and counting real
`git merge-base --is-ancestor` invocations through the guard's own loop:

```
[2] prereg_commits   = 1
[2] tracked_artifacts= 1 ['results/phase21_privacy_unit.json']
[2] OBSERVED checked = 1  (real merge-base --is-ancestor invocations)
[2] guard PASSED at state-5 shape (no exception raised)
```

**Reflexivity re-measured on this repository**, as the docstring is required to carry:
`git merge-base --is-ancestor 7ca8945 7ca8945` → **exit 0**. Pin and artifact in the same commit
would PASS. D-20's "strictly after" is a discipline tighter than the mechanism enforces; the gap is
written into the fixture's docstring so a later reader meets it as a known property.

## The Three Deliberate-RED Cycles

`shasum -a 256 tests/test_phase20_prereg.py` **before any mutation** (post-task-1 committed state):

```
b0957817b2129a2fc3492ca695b5540017ac655175f21dcd9d0c4715aa91cb5b
```

All three restores hash to **that same value**, and `git diff --exit-code` returned `0` after each.
Neither mutation was committed. All mutations were scoped by AST to the new fixture's source
segment only — a whole-file `sed` would also have hit the LIVE guard
`test_phase21_prereg_is_frozen_before_every_phase21_result`, conflating "the fixture is
load-bearing" with "the live guard is load-bearing".

### Mutation A1 — the plan's LITERAL wording (`artifact_glob` kwargs only, 5 sites)

```
>       with pytest.raises(subprocess.CalledProcessError) as out_of_order:
E       Failed: DID NOT RAISE <class 'subprocess.CalledProcessError'>

tests/test_phase20_prereg.py:625: Failed
1 failed, 20 deselected in 0.31s
```

RED — but at the **`pytest.raises`**, not at the `ls-files` assertion the plan predicted. With only
the kwargs swapped, `git ls-files "results/phase20_*"` matches nothing in the throwaway repo, so
`tracked_artifacts` is empty, the ancestry loop never runs, `checked == 1 * 0` holds and
`bool(0) == bool([])` holds — the guard **returns cleanly** instead of raising.

### Mutation A2 — the mutation the plan's PREDICTED OBSERVABLE requires (all 9 glob sites)

```
>       assert _git("ls-files", "results/phase20_*", cwd=tmp_path).split() == [
            "results/phase21_probe.json"
        ], "`git ls-files results/phase21_*` did not match a committed results/phase21_probe.json"
E       AssertionError: `git ls-files results/phase21_*` did not match a committed results/phase21_probe.json
E       assert [] == ['results/phase21_probe.json']
E         Right contains one more item: 'results/phase21_probe.json'

tests/test_phase20_prereg.py:621: AssertionError
1 failed, 20 deselected in 0.26s
```

RED at state 2's `ls-files` assertion, exactly as predicted, with an **empty match set** as the
observable.

### Mutation B — `V4_ARTIFACT_GLOBS` reverted to `("results/phase20_*",)`, fixture kept

```
E  AssertionError: state 1 raised an AssertionError that does not name the pin — the expected
   red here is the `assert prereg_commits` branch reporting that scripts/mitigation_unit.py has
   no commits, not some other assertion that happens to fire first
E  assert 'scripts/mitigation_unit.py' in "results/phase21_* is not in ('results/phase20_*',) —
   this guard and the declared artifact set would be watching two different sets of paths\n
   assert 'results/phase21_*' in ('results/phase20_*',)"

tests/test_phase20_prereg.py:603: AssertionError
FAILED tests/test_phase20_prereg.py::test_phase21_prereg_is_frozen_before_every_phase21_result
FAILED tests/test_phase20_prereg.py::test_phase21_glob_sees_the_phase21_prefix_red_then_green
2 failed, 1 passed, 18 deselected in 0.75s
```

The predicted message — *"watching two different sets of paths"* — fired on the **first**
`_assert_ordering_holds` call (state 1), from `assert artifact_glob in globs` at **`:157`**.

**Both tiers went red**, which is what "both halves are load-bearing" means as evidence: the live
guard AND the new fixture each depend on plan 21-01's glob addition. Plan 21-01 ran this mutation
against the live guard alone; running it again with the fixture present extends that to two tiers.
`test_phase21_has_no_artifact_yet_so_the_arming_is_honest` stayed **green** — it never reads
`globs` — reproducing wave 1's scoping observation exactly.

**An unplanned bonus finding.** Mutation B surfaced through state 1's
`assert PHASE21_PREREG_ARTIFACT in str(no_pin.value)` rather than propagating raw. The
`pytest.raises(AssertionError)` was satisfied by the **wrong** `AssertionError` — the glob-consistency
one instead of the missing-pin one — and the discriminating assertion caught the conflation. That is
the exact assertion the plan forbade dropping, doing exactly the job it was kept for, demonstrated
by accident rather than by design.

## Plan Claims Falsified by Measurement

Reported rather than silently adapted around. **No plan was amended** — plans are records.

**1. `21-VALIDATION.md:81`'s verify command selects ZERO tests, and did so before this plan
existed.** The row prescribes `... -k phase21_glob_red_then_green`, which `21-03-PLAN.md:132`
repeats as an acceptance criterion. pytest `-k` does substring matching, and
`"phase21_glob_red_then_green"` is not a substring of any name following this repository's
convention. Proven against the **already-committed Phase 20 analog**, so the defect is in the
selector's shape and is not about my naming choice:

```
$ pytest -q tests/test_phase20_prereg.py -k phase20_glob_red_then_green --collect-only
no tests collected (20 deselected)          # against test_phase20_glob_sees_the_phase20_prefix_red_then_green

$ pytest -q tests/test_phase20_prereg.py -k phase21_glob_red_then_green
21 deselected                                # against the new test, likewise
```

**Resolution:** the test NAME is stated three times in the plan (objective, `must_haves.artifacts`,
success criteria) and matches the Phase 20 convention, so the name was honored and the selector was
not. Working selectors: `-k phase21` (3 tests) or `-k glob_sees` (2 tests). The plan's own
`<verify><automated>` block already uses `-k phase21` and passes.

**2. Every line anchor in `21-03-PLAN.md`'s `<interfaces>` is stale.** The fixture to copy is at
`:370-529`, not `:281-441`. Measured offsets:

| Plan says | Actually at | What is there |
|---|---|---|
| `:281-441` | `:370-529` | the Phase 20 fixture |
| `:105` | `:133` | `_git` |
| `:129` | `:157` | `assert artifact_glob in globs` |
| `:144` | `:172` | `assert prereg_commits` |
| `:150` | `:181` | the ordering loop |
| `:157` | `:185` | `adds[-1]` |
| `:178` | `:206` | the equivalence assertion |
| `:317-318` | `:406-407` | the local git identity |
| `:387-389` | `:476-478` | the `mkdir(exist_ok=True)` gotcha |

Consistent with wave 1's 28-line drift finding. Everything was located by assertion text instead,
and **the new docstring cites assertions by name rather than by number** so it cannot rot the same
way.

**3. Wave 1's own docstrings already carry stale anchors — a live instance of the same defect.**
`test_phase21_prereg_is_frozen_before_every_phase21_result` cites "`:157` (`adds[-1]`, the EARLIEST
add)" and "the closing equivalence assertion at `:178`", but `:157` is the glob-consistency
assertion and `:178` is the `ls-files` call; the real sites are `:185` and `:206`.
`test_phase21_has_no_artifact_yet_so_the_arming_is_honest` cites `:157` for the same `adds[-1]`
claim. **Not fixed here** — pre-existing, landed in wave 1's `21ed755`, and outside this plan's
scope. My insertion is entirely below `:529` so it does not shift them further.

**4. `21-VALIDATION.md:50`'s "21 tests" was still wrong at this plan's start.** Measured at base
`7ca8945`: **20 collected**. This plan adds 1, so the file is now genuinely 21 — the documented
figure became true by coincidence, one wave after it was written. Recorded so nobody reads the
match as confirmation.

## Deviations from Plan

**Mutation A was run in two variants rather than one.** The plan's instruction ("change
`artifact_glob` … at every call site") and its predicted observable ("FAILS at state 2's `ls-files`
assertion") describe different mutations — the narrow one cannot produce the predicted failure,
because the `ls-files` literal is not the `artifact_glob` kwarg. Rather than pick one and report a
mismatch, both were run and both recorded. The plan's underlying claim survives in the stronger
form: **the mutation is caught either way**, at `ls-files` under A2 and at the `raises` under A1.

No auto-fixes were needed under Rules 1-3. No architectural decisions arose.

## Requirements — Deliberately NOT Marked Complete

`UNIT-01`, `UNIT-04`, `UNIT-05` are this plan's `requirements:` frontmatter and none is marked
complete, following wave 1's reasoning unchanged: `21-CONTEXT.md` names over-claim avoidance as an
Established Pattern, and D-26 requires UNIT-01's multiplicity to be **measured** in plan 21-11. A
fixture proving a guard bites is not the measurement those requirements call for.
`REQUIREMENTS.md` was not modified. Per the orchestrator's instruction `STATE.md` and `ROADMAP.md`
were not touched.

## Verification

```
$ pytest -q tests/test_phase20_prereg.py tests/test_phase21_unit_pin.py tests/test_package.py
35 passed in 2.85s

$ pytest -q tests/test_phase20_prereg.py
21 passed in 2.79s

$ pytest -q tests/test_phase20_prereg.py -k phase21
3 passed, 18 deselected

$ git ls-files 'results/phase21_*'                                    # EMPTY, before and after
$ git log --diff-filter=A --format=%H -- 'results/phase21_*' | wc -l  # 0, before and after
$ git status --porcelain results/                                     # empty
$ git diff --exit-code scripts/mitigation_gate.py scripts/mitigation_unit.py \
      scripts/phase18_extraction.py                                   # 0
$ shasum -a 256 scripts/mitigation_unit.py
45f37e152bb4035667b804c1463431b3f12fa5096c47de32b1dc27abbe000473      # == wave 1's value
$ ruff check . && ruff format --check .
All checks passed! · 179 files already formatted
```

**T-21-07 (a `phase21_`-named probe reaching the real history) — the mitigation, measured:**

```
[1] new test body: 175 lines
[1] cwd=_ROOT occurrences in the NEW body  : 0    (must be 0)
[1] cwd=tmp_path occurrences in the NEW body: 21
[1] 'shell=True' anywhere in the module     : 4
```

The `cwd` audit is AST-scoped to the new function, not a whole-file grep. All four `shell=True`
occurrences are **prose inside docstrings** (`:141`, `:396`, `:567`, `:1298`) recording that it is
never used — never a kwarg — which satisfies T-21-19.

**Full suite:** `884 passed, 1 failed, 7 skipped in 199.71s`. The one failure is
`tests/test_phase18_docs.py::test_no_bare_zero_percent_in_docs`, on `README.md`, **pre-existing and
proven not mine**: this plan's commit touches only `tests/test_phase20_prereg.py`, and README.md was
last modified by `9cc2c94` (2026-08-22), an ancestor of base `7ca8945`. Logged to
`deferred-items.md`, not fixed — out of scope.

## Known Stubs

None. The fixture asserts on real git objects in a real (throwaway) repository; nothing is mocked,
stubbed or placeholder. State 5's artifact content is shape-only and says so in the file it writes,
because the ordering — not the content — is the subject.

## Threat Flags

None. This plan adds no network endpoint, no auth path and no schema at a trust boundary. The one
new file-access pattern is `tmp_path`-confined git usage through the existing `_git` helper, which
passes an argv tuple to `subprocess` with no `shell=True`.

Dispositions from the plan's register, all satisfied by observation: T-21-07 (`cwd=_ROOT` count 0,
history empty before and after), T-21-06 (state 4's `adds[-1] == state1_add`), T-21-05 (Mutation A2
observed firing), T-21-03 (Mutation B observed firing at both tiers), T-21-18 (`cmd[:3]` asserted at
states 2 and 4), T-21-19 (`shell=True` prose-only, verified), T-21-11 (zero installs).

## Self-Check: PASSED

```
$ test -f tests/test_phase20_prereg.py                        && echo FOUND
FOUND
$ test -f .planning/phases/21-.../deferred-items.md           && echo FOUND
FOUND
$ git log --oneline --all | grep -q 76926ef                   && echo FOUND
FOUND
```

Test claimed as provided, verified collected:
`test_phase21_glob_sees_the_phase21_prefix_red_then_green` — FOUND (`-k phase21` → 3 passed).
