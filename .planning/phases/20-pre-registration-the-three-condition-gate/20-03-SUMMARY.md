---
phase: 20-pre-registration-the-three-condition-gate
plan: 03
subsystem: testing
tags: [pre-registration, git-ancestry, prose-normalization, throwaway-repo, stdlib, ruff, pytest]

# Dependency graph
requires:
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 01
    provides: "tests/test_phase20_prereg.py — _ROOT, _git(*args, cwd=), PHASE20_PREREG_ARTIFACT, V4_ARTIFACT_GLOBS and _assert_ordering_holds already keyword-only and parameterized on root"
  - phase: 19-selective-erasure
    provides: ".planning/RETROSPECTIVE.md:179-181 and .planning/milestones/v3.0-MILESTONE-AUDIT.md:104-111 — the measured line-wrapped grep miss RPT-02 converts into a mechanism"
provides:
  - "scripts/_prose.py::normalized — the ONE whitespace-normalizing prose read, phase-neutral, zero imports"
  - "WRAPPED_INCIDENT_TEXT / WRAPPED_INCIDENT_PHRASE — the real v3.0 incident bytes as a committed fixture"
  - "test_normalized_finds_a_line_wrapped_phrase_grep_reports_absent — the RPT-02 DIFFERENTIAL proof"
  - "test_prose_module_imports_nothing — the AST layer pyproject's sha256 pin cannot see"
  - "test_phase20_glob_sees_the_phase20_prefix_red_then_green — the D-22 five-state throwaway-repo fixture, re-executed every CI run"
affects: [20-04, 20-05, 20-06, 20-07, phase-21, phase-22, phase-23, phase-24, phase-25]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Import accumulation held: ast/sys landed with the bootstrap in Task 1, pytest with pytest.raises in Task 2 — never an F401"
    - "A guard is proven by driving the SHIPPED implementation through its states in a throwaway repo, never by a lookalike copy"
    - "Throwaway-repo identity via LOCAL git config in tmp_path/.git/config — no env mutation, no widening of the shared _git helper"

key-files:
  created:
    - scripts/_prose.py
  modified:
    - tests/test_phase20_prereg.py

key-decisions:
  - "The throwaway repo's git identity is set with `git config user.name/user.email` INSIDE tmp_path rather than through GIT_AUTHOR_*/GIT_COMMITTER_* env vars. Same property (independent of the host's global config, works on a CI runner with no identity at all) with a strictly smaller change: _git has no env= parameter, so the env route would have required widening 20-01's shared helper — the one thing that would have made the fixture stop exercising the code CI runs."
  - "State 2 and state 4 additionally assert the FAILING ARGV is `git merge-base --is-ancestor`. `subprocess.run(check=True)` fails with no message (20-RESEARCH L8), so a bare `pytest.raises(CalledProcessError)` would be satisfied by ANY git failure anywhere in the helper — including a broken fixture setup. Naming the command is what makes the observed red the ORDERING red."
  - "A fifth state was driven, not four: the plan's four measured states end on a RED, so the GREEN half of RED-then-GREEN is state 5 — the probe deleted and results/phase20_retention_floor.json added strictly after the pin, tracked=1, guard passes."

patterns-established:
  - "The RPT-02 register: a doc-consistency assertion ships with its NEGATIVE CONTROL, so it cannot degrade into a bare containment check that would stay green against a no-op helper"

requirements-completed: []

# Metrics
duration: 27min
completed: 2026-08-20
---

# Phase 20 Plan 03: The Prose Read and the Proven Prefix Summary

**v3.0's line-wrapped `grep -c` miss is now a five-line zero-import module with a differential test that watches the naive method return 0 on the bytes it succeeds on, and `V4_ARTIFACT_GLOBS` has been watched going RED then GREEN on a real `phase20_*` path in a throwaway repo — against the same `_assert_ordering_holds` CI runs, not a copy.**

## Performance

- **Duration:** ~27 min
- **Started:** 2026-08-20T20:39Z (17:39 -0300)
- **Completed:** 2026-08-20T21:06Z (18:06 -0300)
- **Tasks:** 2 of 2
- **Files created:** 1 (`scripts/_prose.py`, 48 lines) — **files modified:** 1 (`tests/test_phase20_prereg.py`, 163 → 349 lines)

## Accomplishments

- `scripts/_prose.py` exports exactly one name, `normalized`, and imports **nothing** — AST-verified zero `Import`/`ImportFrom` nodes, exactly one `FunctionDef`. `" ".join(text.split())`, the stdlib one-liner `PITFALLS.md:1048` prescribed and named this phase to build.
- **The RPT-02 proof is differential, and the negative control is what carries it.** On the committed fixture, `WRAPPED_INCIDENT_TEXT.count(WRAPPED_INCIDENT_PHRASE)` is `0` while `normalized(phrase) in normalized(text)` is `True` — the same bytes, two methods, opposite answers. Without assertion (1) the test would stay green against a `normalized` that returned its argument unchanged.
- **The fixture literal is the real v3.0 incident**, not a synthetic one: the text line-wraps the phrase as `the three\nreductions` exactly as `docs/REPORT.md` did, cited in the constants' comment to `RETROSPECTIVE.md:179-181` and `v3.0-MILESTONE-AUDIT.md:104-111` (defect W2, `resolved_by: 5703bbe`). D-30's register — a defect that actually happened is not hypothetical.
- **The `phase20_` prefix is now DEMONSTRATED rather than read.** All five states were driven against `_assert_ordering_holds` with `root=tmp_path` — the same implementation, parameterized, never a lookalike. State 2's ordering failure is unreachable unless `git ls-files "results/phase20_*"` matched the probe, and the fixture asserts that match set is non-empty *before* asserting the failure, so the prefix proof is stated rather than inferred.
- **Laundering is shown impossible as a standing CI fact.** State 4 asserts the earliest-add SHA is byte-identical to state 1's across a delete-and-re-add cycle — full 40-character equality, not a length check.
- `scripts/mitigation_gate.py` is **byte-unchanged**: sha256 `1a0095c28d68469d8576732d53c90ac88c0bc9a4dbe3bf1faef4846c0a15fcf5`, identical to the handover value at `c856064`. No task in this plan opened it.
- Full suite: **849 passed, 1 skipped** in 187.94s (baseline 846/1 — the delta is this plan's three new tests).

## Task Commits

1. **Task 1: `scripts/_prose.py::normalized` and its differential RPT-02 proof** — `ac4d781` (feat)
2. **Task 2: the D-22 RED-then-GREEN fixture in a throwaway repo** — `096d44a` (test)

**Plan metadata:** see the `docs(20-03)` commit that carries this SUMMARY.

## The Five Guard States — observed, with exception types and SHAs

Driven through an instrumented single run of the committed fixture. **The SHAs are ephemeral by construction** — the fixture builds a fresh `tmp_path` repo every run, so what it asserts is the *identity* of the state-1 and state-4 values, never a fixed literal. The run below is one such observation:

| state | what it is | observed | evidence |
|---|---|---|---|
| **1** | probe committed, **no pin yet** | `builtins.AssertionError` — **a DIFFERENT red** | stops at `assert prereg_commits`; message asserted to name `scripts/mitigation_gate.py`. Add SHA `ac704f278473ba02af40a8864b21019b5d420096` |
| **2** | pin committed **second** | `subprocess.CalledProcessError` — **the ORDERING red** | `git ls-files results/phase20_*` → `'results/phase20_probe.json'` (**non-empty, asserted first — this is the prefix proof**); failing argv asserted `('git','merge-base','--is-ancestor')` |
| **3** | `git rm` probe, not re-added | **GREEN** | `git ls-files results/phase20_*` → `''`, tracked=0 — the red is reversible **only by not having the artifact** |
| **4** | re-add at the identical path | `subprocess.CalledProcessError` — **RED again** | 2 adds; `adds[-1]` = `ac704f278473ba02af40a8864b21019b5d420096` — **byte-identical to state 1**. Laundering impossible |
| **5** | probe gone, real artifact **after** the pin | **GREEN** | `git ls-files results/phase20_*` → `'results/phase20_retention_floor.json'`, tracked=1 checked=1 |

**Three distinct observed failures, two of them a different failure type from the other** — states 2 and 4 are `CalledProcessError`, state 1 is `AssertionError`. Conflating them would have hidden the fact that state 1 never reaches an ancestry comparison at all.

**Reflexivity, recorded in the fixture's own docstring (D-08 / T-20-17, disposition `accept`):** `git merge-base --is-ancestor X X` exits **0**, so pin and artifact in the *same* commit would PASS. D-08's strictly-after rule is a **discipline tighter than the mechanism**, deliberately. Written down so a later reader treats same-commit as neither a defect nor a licence.

## The real repository's history — clean before and after

```
BEFORE (at 2c8eb24, this plan's start):
$ git log --diff-filter=A -- 'results/phase20_*'   -> (empty)   [0 lines]
$ git ls-files 'results/phase20_*'                 -> (empty)   [0 lines]

AFTER the full 849-test suite run:
$ git log --diff-filter=A -- 'results/phase20_*'   -> (empty)   [0 lines]
$ git ls-files 'results/phase20_*'                 -> (empty)   [0 lines]
```

Every probe lived under pytest's `tmp_path` and was destroyed with it. **No v4.0-named artifact has ever been added to this repository's history** (T-20-14 discharged), so D-08's ordering is intact and plan 20-07's real artifact will still be the first `results/phase20_*` add this repo has ever seen.

## Verification (wave boundary)

| check | result |
|---|---|
| `.venv/bin/python -m pytest -q` | **849 passed, 1 skipped** in 187.94s (baseline 846/1) |
| `.venv/bin/ruff check .` | All checks passed |
| `.venv/bin/ruff format --check .` | 173 files already formatted |
| `git status --porcelain pyproject.toml` | empty — byte-unchanged, RPT-03's sha256 pin carries forward |
| `git log --diff-filter=A -- 'results/phase20_*'` | empty, before **and** after the run |
| **sha256 `scripts/mitigation_gate.py`** | **`1a0095c2…fcf5` — IDENTICAL to the handover value; the pin was never opened** |
| AST: imports in `scripts/_prose.py` | `0` |
| AST: `FunctionDef` names in `scripts/_prose.py` | exactly `['normalized']` |
| AST: imports in the test module | exactly `['_prose', 'ast', 'pathlib', 'pytest', 'subprocess', 'sys']` |
| `normalized("a\n b")` / `normalized("  a \t\n b  ")` | `'a b'` / `'a b'` |
| `WRAPPED_INCIDENT_TEXT.count(WRAPPED_INCIDENT_PHRASE)` | `0` — the negative control holds |
| `normalized(PHRASE) in normalized(TEXT)` | `True` — on the same bytes |
| `_prose.py` docstring literals | `the three`, `D-23`, `dependency-free` all present |
| `src.count('_assert_ordering_holds')` | `9` (≥ 6 required: 1 def + 1 live call + 5 fixture states + 2 docstring mentions) |
| AST: `Call` nodes with a `shell=` keyword | `[]` — **none** |
| AST: non-docstring string literals containing `rm -rf` | `[]` — **none** |
| `git status --porcelain` | empty — working tree clean |

## Decisions Made

1. **Local git config, not environment variables, for the throwaway repo's identity.** The plan prescribed `GIT_AUTHOR_*` / `GIT_COMMITTER_*` env vars. `_git`'s signature is `_git(*args, cwd=_ROOT)` — it has **no `env=` parameter** — so the env route needed a widening of 20-01's shared helper, and widening the helper is the one change that would have made the fixture stop exercising exactly the code CI runs. `git config user.name/user.email` inside `tmp_path` writes only to `tmp_path/.git/config`, delivers the same property (never depends on the developer's global config; works on a CI runner that has no identity configured at all), and touches nothing shared.

2. **The observed failure's argv is asserted, not just its type.** `20-RESEARCH` L8 records that the ordering check is `subprocess.run(check=True)` and fails with **no explanatory message**. A bare `pytest.raises(subprocess.CalledProcessError)` is therefore satisfied by *any* git failure — including a fixture that broke during setup and never reached the ancestry loop at all. States 2 and 4 assert `cmd[:3] == ("git", "merge-base", "--is-ancestor")`, which is what makes the observed red *the ordering red*. This handles the L8 ergonomics gap at the assertion site rather than by editing the shared helper.

3. **State 5 exists because four states end on a RED.** The plan's four measured states finish at "re-add → RED again". RED-then-GREEN needs the GREEN, so the fixture closes by deleting the probe and adding `results/phase20_retention_floor.json` — the artifact D-08/D-32 will actually produce — strictly after the pin, and asserts the guard passes at exactly one tracked artifact.

## Deviations from Plan

**None of the four deviation rules fired.** Two mechanism substitutions are recorded under Decisions Made above (local git config for env vars; the extra argv assertion) — neither changes what is proven, both keep the shared helper untouched.

**Total deviations:** 0.

## Path / naming discrepancies found

**One acceptance criterion is unsatisfiable as literally written, and it fails for exactly the reason this plan's other half exists.**

> Task 2 acceptance criterion: *"`grep -c "shell=True" tests/test_phase20_prereg.py` outputs `0` and `grep -c "rm -rf" tests/test_phase20_prereg.py` outputs `0`."*

Measured: `shell=True` matches **2** lines and `rm -rf` matches **1**. Both are **prose**, and one predates this plan by two plans:

- **`tests/test_phase20_prereg.py:89`** — committed by **plan 20-01**, inside `_git`'s docstring: *"The argv tuple is passed to `subprocess` directly and `` `shell=True` `` is never used…"*. The criterion was already unsatisfiable when the plan was written.
- **`tests/test_phase20_prereg.py:283`** — this plan's fixture docstring recording T-20-14: *"there is no `shell=True` and no `rm -rf` anywhere in this module."*

Both sentences state the **absence** of the thing the grep counts. **The criterion's intent was verified properly instead**, by AST rather than by a line-oriented text scan: zero `Call` nodes carry a `shell=` keyword, and zero non-docstring string literals contain `rm -rf` (both in the table above). The safety property holds; only its naive measurement is wrong.

**The docstring was NOT reworded to make the grep pass.** Deleting a committed safety record to satisfy a broken measurement is weakening the artifact to fit the instrument, which is the pattern this project keeps refusing. And the irony is load-bearing rather than decorative: **a single-line grep conflating prose *about* code with the code itself is the same defect class as `grep -c "three reductions"` returning 0 on a file that contained it** — the very thing `scripts/_prose.py` was built in this same plan to close. Future doc-consistency criteria in this phase should be written as AST or `_prose.normalized` checks, never as `grep -c`.

Nothing else needed renaming. Every identifier this plan consumed (`_ROOT`, `_git`, `PHASE20_PREREG_ARTIFACT`, `V4_ARTIFACT_GLOBS`, `_assert_ordering_holds`) was resolved by reading `tests/test_phase20_prereg.py` directly and matched the plan's `<interfaces>` block exactly. `scripts/_verdict.py` is 30 lines as stated; `_addendum.py:47` carries the `import _verdict  # noqa: E402` line the plan cited.

## Issues Encountered

**Two ruff-format rewraps, both caught by the task gate before commit, neither committed red.** The `imports` list comprehension in `test_prose_module_imports_nothing` and two long lines in the fixture (the pin's stand-in `write_text` and one `_git("commit", …)` call) exceeded the 100-character limit; `ruff format` rewrapped them with no change to behaviour or to any rendered string.

**No path errors, no API mismatches.** `git rm` of the last file in `results/` did remove the directory exactly as the handover warned — the fixture's `probe.parent.mkdir(exist_ok=True)` before each re-add is that measured gotcha handled, and states 4 and 5 both pass because of it.

## Known Stubs

**None.** Both deliverables are complete and exercised. `scripts/_prose.py` has exactly one caller today (this phase's RPT-02 test), and that is the intended state: `PITFALLS.md:1048`'s instruction is *"build it in P20 so it is available all milestone"* — the routing of every doc-consistency test through it belongs to P25, where those tests are written. The module is deliberately one function with no `search()` wrapper, no case-fold flag and no `count()` helper; adding them before a second call site needs them would be the speculation the research explicitly warned against.

## Threat Flags

None. This plan adds no network surface, no auth path and no schema. It does add **filesystem and subprocess surface**, and every threat-register entry covering it is discharged below.

| Threat ID | Disposition | How this plan discharges it |
|---|---|---|
| T-20-12 | mitigate | State 2 asserts a **non-empty** `git ls-files "results/phase20_*"` *before* asserting the ordering failure — the prefix match is a positive observation, not an inference from the pattern text |
| T-20-13 | mitigate | State 4 asserts the earliest-add SHA is byte-identical to state 1's across a delete-and-re-add cycle. A standing CI fact now, not a one-time manual observation |
| T-20-14 | mitigate | Every probe under pytest's `tmp_path`; AST-verified zero `shell=` kwargs and zero `rm -rf` in executable code; `git log --diff-filter=A -- 'results/phase20_*'` re-verified **empty after** the full suite ran |
| T-20-15 | mitigate | `scripts/_prose.py::normalized` plus the DIFFERENTIAL test showing the naive method returning 0 on the same bytes |
| T-20-16 | mitigate | AST scan asserting zero `Import`/`ImportFrom` nodes in `_prose.py`; `pyproject.toml` byte-unchanged so `tests/test_package.py`'s sha256 pin still covers the declared surface |
| T-20-17 | accept | Reflexivity measured (exit 0) and recorded in the fixture's docstring: D-08's strictly-after rule is a discipline, read as neither defect nor licence |

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **20-04** adds `V20_EWC_RETENTION_PPL` and `rule_of_three` to `mitigation_gate.py`'s already-wrapped `from erasure_gate import (…)` statement, with their first consumers. The list is currently exactly `MARGIN_K, V20_MASKED_DIALOGUE_VAL_PPL, wilson_upper_bound`.
- **20-06**'s test-module import ledger: this plan leaves it at exactly `['_prose', 'ast', 'pathlib', 'pytest', 'subprocess', 'sys']`. `fnmatch`, `json`, `erasure_gate` and `mitigation_gate` are still absent and are 20-06's to add. The `sys.path` bootstrap 20-06 needs for `import mitigation_gate` **already exists** at `:42-44` — do not add a second one.
- **20-06 should NOT write `grep -c`-shaped assertions.** `scripts/_prose.py::normalized` is importable from the test module today (`import _prose` at `:46`); the discrepancy recorded above is a live demonstration of why a line-oriented scan over prose is the wrong instrument.
- **20-07** commits the first real `results/phase20_*` artifact. When it does, the live guard stops being vacuous and `bool(checked) == bool(tracked_artifacts)` starts biting — state 5 of this plan's fixture is a rehearsal of exactly that transition, and it passes.
- **No requirement was marked complete.** RPT-02's mechanism ships here, but its stated purpose in `PITFALLS.md:1048` is *"route every doc-consistency test through it"*, which no test outside this plan does yet — that routing is P25's. Marking RPT-02 done on the strength of one call site would be the over-claim the recorded pattern (`17-01`, applied six times across Phases 17 and 19, again in `20-01` and `20-02`) exists to prevent. A ninth application.

**Standing constraint, unchanged:** `scripts/mitigation_gate.py` is watched from `95b3c8a` onward and is byte-identical at `1a0095c2…fcf5` after this plan. Do not amend, rebase, squash or cherry-pick any commit touching it, and do not commit a `results/phase20_*` artifact before the pin is complete.

## Self-Check: PASSED

- `scripts/_prose.py` — FOUND
- `tests/test_phase20_prereg.py` — FOUND
- `.planning/phases/20-pre-registration-the-three-condition-gate/20-03-SUMMARY.md` — FOUND
- commit `ac4d781` — FOUND
- commit `096d44a` — FOUND
- `scripts/mitigation_gate.py` sha256 `1a0095c28d68469d8576732d53c90ac88c0bc9a4dbe3bf1faef4846c0a15fcf5` — UNCHANGED

---
*Phase: 20-pre-registration-the-three-condition-gate*
*Completed: 2026-08-20*
