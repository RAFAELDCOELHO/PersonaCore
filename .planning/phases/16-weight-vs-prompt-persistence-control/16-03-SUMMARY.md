---
phase: 16-weight-vs-prompt-persistence-control
plan: 03
subsystem: testing
tags: [pytest, ast-guard, structural-guard, allowlist, hard-equality, anti-vacuity]

# Dependency graph
requires:
  - phase: 16 (plan 02)
    provides: "assert_value_in_prompt in scripts/phase14_recall.py — the named twin whose presence Task 2's every-draw_all-asserts guard keys on"
  - phase: 14 (teach-then-recall)
    provides: "tests/test_phase14_scoring.py::test_persona_argument_is_scoped_to_the_fairness_control — the single-file guard this plan widens, and assert_no_value_in_prompt, the absence half"
provides:
  - "D-21 closed: the persona= guard scans scripts/*.py + src/**/*.py in full (69 files today), so a new Phase 17 file carrying persona= fails the suite instead of going unscanned"
  - "The widening did NOT weaken the assertion — sorted(with_persona) == sorted(PERSONA_ALLOWLIST) is still hard equality against an explicit (file, function) allowlist"
  - "An anti-vacuity floor on the scan itself: scanned-file count >= 2, so a broken glob cannot collapse the guard back to one file while staying green"
  - "PERS-06's positive half: every draw_all call site is covered by an in-prompt assertion, in place or via a NAMED indirection"
  - "PERSONA_ALLOWLIST holds exactly ONE entry at this plan's close — the line 16-05 must extend in the same commit as its call site"
affects: [16-05, phase-17, phase-18, any file added to scripts/ or src/ from here on]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Widen the SCAN, never the ASSERTION: a guard covering more files must keep `==`, because relaxing to membership is the guard getting weaker while looking bigger"
    - "Anti-vacuity on two axes: assert the input set is non-empty AND that it did not collapse below a known floor (scanned files >= 2, found sites >= 2)"
    - "An indirection is permitted only when NAMED, and a dangling name fails — an unnamed indirection is indistinguishable from a missing assertion"
    - "A hard-equality allowlist is bidirectional: an unlisted call site and a listed non-existent site fail identically, which is what forbids pre-adding entries"
    - "The file-set walker is deliberately UNCACHED, because the deliberate-RED probes that prove it bites add and remove files under the scanned globs"

key-files:
  created: []
  modified:
    - "tests/test_phase14_scoring.py — _scanned_files/_enclosing_functions/_call_sites/_function_index helpers, PERSONA_ALLOWLIST, DRAW_ALL_ASSERTED_BY, the rewritten persona guard, and test_every_draw_all_call_site_asserts_something"

key-decisions:
  - "ONE parametrized walker `_call_sites(callee)` serves both guards instead of two near-identical AST walks — the plan's Task 2 read_first explicitly sanctions reusing Task 1's helper, and a second copy is a second place for the two guards' file sets to silently diverge"
  - "A `**splat` keyword (kw.arg is None) is KEPT in the keyword set, so an unanalysable call lands in the not-the-bare-form bucket rather than passing as `at least it is not persona` — this cost zero extra code, the existing bare-form assertion catches it"
  - "_function_index returns two SETS rather than a dict, so two same-named defs in one file union instead of shadowing each other"
  - "The `no decorator on a drawing function` rule is implemented as locked, with a recorded concern: it would also reject a legitimate @torch.no_grad() on a future drawing path"

requirements-completed: [PERS-06]

# Metrics
duration: 16min
completed: 2026-08-13
---

# Phase 16 Plan 03: The D-21 structural guards, widened Summary

**The `persona=` guard now parses all 69 files under `scripts/*.py` + `src/**/*.py` instead of one hard-coded path, still asserting hard equality against a one-entry `(file, function)` allowlist — and its missing sibling landed: every `draw_all` call site must be covered by an in-prompt assertion, in place or through a named indirection.**

## Performance

- **Duration:** ~16 min wall clock (13:42 → 13:58 -03:00)
- **Tasks:** 2
- **Files modified:** 1
- **Tests added:** 1 (424 → 425 passed)

## Task Commits

1. **Task 1 — widen the `persona=` guard's SCAN, keep hard equality** — `dd17187` (test)
2. **Task 2 — every `draw_all` call site asserts something** — `70ee124` (test)

## What landed

### Task 1 — D-21 / T-16-09 / T-16-10

`_build_recall_prompt_call_sites()` parsed exactly one hard-coded path,
`_REPO_ROOT / "scripts" / "phase14_recall.py"`. A Phase 17 file carrying `persona=` would simply
not have been scanned and would have passed in silence — the guard technically green and
substantively blind. That is the defect D-21 names, and the one this project records as its most
recurring: a declared invariant silently becoming false.

The scan is now a file SET: `sorted((_REPO_ROOT / "scripts").glob("*.py"))` plus
`sorted((_REPO_ROOT / "src").rglob("*.py"))` — **69 files today**, up from 1.

Three things the old single-file walk got wrong once the scope widened, all fixed:

| Was | Now |
|---|---|
| `ast.FunctionDef` only | `ast.FunctionDef` **and** `ast.AsyncFunctionDef` |
| a call outside any function was dropped | recorded as `"<module>"` — a module-level `persona=` is the most dangerous placement there is and must not be invisible |
| `getattr(inner.func, "id", None)` only | also `getattr(node.func, "attr", None)`, so `serialize.build_recall_prompt(...)` matches |

Call sites are keyed `(relative_posix_path, enclosing_function, frozenset_of_keyword_names)`. AST
rather than a substring scan, for the reason the original helper already gave: a substring check
cannot tell a call from a docstring mention, and `phase14_recall.py`'s docstrings discuss
`persona=` at length precisely because it is the dangerous argument.

**The assertion did not move.** `sorted(with_persona) == sorted(PERSONA_ALLOWLIST)` — hard
equality, exactly as before. 16-RESEARCH Pitfall 3 is explicit that widening the scan naively
*forces* relaxing equality into membership, and that this is the guard getting weaker while looking
bigger. The diff contains no `in`, no `issubset`, no `<= set(` against the allowlist; that absence
is itself pinned by a grep in the acceptance criteria (returns 0) and by an AST check asserting an
`ast.Eq` survives inside the test function.

Two anti-vacuity floors, because a guard that passes by matching NOTHING is the failure mode this
plan exists to close:

- `assert len(scanned) >= 2` — a broken glob cannot collapse the scan back to one file, or to zero.
- `assert sites` — the walk-stopped-working tripwire, kept from the original.

The **positive half** is kept and extended. `complete_question`, `render_context_dump` and
`assert_no_value_in_prompt` must still appear as call sites, and `build_recall_prompt`'s own
definition file (`src/personacore/dialogue/serialize.py`) must be reachable in the scanned set — a
guard that only forbids is satisfied by deleting every call site.

One property came for free rather than by new code: a `**splat` keyword has `kw.arg is None`, and
keeping `None` in the keyword frozenset makes such a call land in the existing "everything else is
the bare form" assertion (a non-empty keyword set without `persona`). An unanalysable call
therefore fails rather than passing as "at least it is not `persona`".

### Task 2 — PERS-06 positive half / T-16-11 / T-16-12

`test_every_draw_all_call_site_asserts_something()` walks the same file set for `draw_all` calls.
For each site, either the enclosing function itself calls `assert_value_in_prompt` or
`assert_no_value_in_prompt`, **or** the site is listed in `DRAW_ALL_ASSERTED_BY` naming the caller
that asserts on its behalf — and that named caller must itself be in the scan and must itself
assert. A **dangling** entry fails: an exemption cannot be created by pointing at nothing (T-16-12).

The mapping has exactly one entry, and it is real:

```python
DRAW_ALL_ASSERTED_BY = {
    ("scripts/phase14_recall.py", "complete_question"): "run_scored_recall",
}
```

`complete_question` (`scripts/phase14_recall.py:650-651`) builds the BARE scored prompt and draws
from it but asserts nothing itself; the absence proof runs one level up in `run_scored_recall`
(`:817`), over the `prompt_ids` it returns. Verified by AST rather than assumed —
`complete_question` holds zero `assert_*` calls, `run_scored_recall` holds
`assert_no_value_in_prompt`, `run_fairness_control` holds `assert_value_in_prompt`.

**Why it keys on the drawing call and not on an argument name.** 16-RESEARCH records that Phase
16's distance-~2 ladder rungs carry the fact value inside the `question` string, not in a
`persona=` span — which makes them **invisible to the `persona=` guard by construction**. Task 2 is
what covers them, and it will cover them automatically when 16-06 writes them.

No skip mode, in either shape: no `draw_all` site may sit in a function whose name starts with
`_skip`, and no drawing function may carry a decorator. Anti-vacuity: `assert sites` plus
`len(sites) >= 2` (today `complete_question` and `run_fairness_control`).

## PERSONA_ALLOWLIST at this plan's close — the line 16-05 must extend

**Exactly one entry.** This is the operative fact for the rest of the phase:

```python
PERSONA_ALLOWLIST = (
    # The D-11.1 fairness control: a fact value in the <|system|> span IS the measurement
    # here, and the same function proves the value is in view via assert_value_in_prompt.
    ("scripts/phase14_recall.py", "run_fairness_control"),
)
```

- **16-05 is the ONLY downstream plan in this phase that adds a `persona=` call site** —
  `build_far_prompt` in `scripts/phase16_ladder.py`. It must add
  `("scripts/phase16_ladder.py", "build_far_prompt")` to that tuple **in the same commit as the
  call site**, with a comment naming why that site may place a fact value in context. D-21's
  "sem exceção por conveniência de arquivo novo" made operational: being new buys nothing.
- **16-04, 16-06, 16-07, 16-08, 16-10 and 16-11 must NOT pre-add an entry.** The assertion is hard
  equality in both directions: a listed site with no matching call turns the guard red exactly as
  loudly as an unlisted call site does. There is no such thing as a harmless placeholder here.

For the record, the widened scan today finds **11 `build_recall_prompt` call sites across 4 files**
(`personalize_demo.py::on_ask`, `phase14_factset_gate.py::_probe`, `teach_persona.py::sanity_check`,
and six inside `phase14_recall.py`), of which exactly one passes `persona=`. Under the old
single-file scan, 3 of those 11 were unscanned.

## Observed RED #1 — Task 1(a), `persona=[]` added to `complete_question`

The mutation the plan names: `scripts/phase14_recall.py:650` gains `persona=[]`.

```
E       AssertionError: persona= call sites [('scripts/phase14_recall.py', 'complete_question'), ('scripts/phase14_recall.py', 'run_fairness_control')] do not equal PERSONA_ALLOWLIST [('scripts/phase14_recall.py', 'run_fairness_control')]. An unlisted site puts a fact value in a prompt nothing vetted; a listed site with no call is an exemption granted to code that no longer exists.
E       assert [('scripts/ph...ess_control')] == [('scripts/ph...ess_control')]
E
E         At index 0 diff: ('scripts/phase14_recall.py', 'complete_question') != ('scripts/phase14_recall.py', 'run_fairness_control')
E         Left contains one more item: ('scripts/phase14_recall.py', 'run_fairness_control')

tests/test_phase14_scoring.py:534: AssertionError
=========================== short test summary info ============================
FAILED tests/test_phase14_scoring.py::test_persona_argument_is_scoped_to_the_fairness_control
1 failed in 0.68s
```

**Reverted inside a `finally`, `RESTORED bytes-identical: True`;
`git diff --exit-code scripts/phase14_recall.py` → exit `0`.**

## Observed RED #2 — Task 1(b), a NEW unlisted file. This is the one that proves the widening

`scripts/_red_probe.py`, a file that did not exist when the guard was written, containing
`build_recall_prompt(tok, q, persona=["x"])`. Under the pre-plan guard this file was invisible and
the suite stayed green.

```
E       AssertionError: persona= call sites [('scripts/_red_probe.py', 'probe'), ('scripts/phase14_recall.py', 'run_fairness_control')] do not equal PERSONA_ALLOWLIST [('scripts/phase14_recall.py', 'run_fairness_control')]. An unlisted site puts a fact value in a prompt nothing vetted; a listed site with no call is an exemption granted to code that no longer exists.
E       assert [('scripts/_r...ess_control')] == [('scripts/ph...ess_control')]
E
E         At index 0 diff: ('scripts/_red_probe.py', 'probe') != ('scripts/phase14_recall.py', 'run_fairness_control')
E         Left contains one more item: ('scripts/phase14_recall.py', 'run_fairness_control')

tests/test_phase14_scoring.py:534: AssertionError
FAILED tests/test_phase14_scoring.py::test_persona_argument_is_scoped_to_the_fairness_control
1 failed in 0.68s
```

`('scripts/_red_probe.py', 'probe')` appears **by name** in the failure. That string is the whole
proof: the guard did not merely fail, it named a file nobody told it about. Probe deleted;
`git status --porcelain scripts/` empty.

## Observed RED #3 — Task 2(a), a NEW drawing path that asserts nothing

`scripts/_red_probe2.py`, a function calling `draw_all(...)` with no assertion anywhere.

```
E           AssertionError: scripts/_red_probe2.py::probe draws completions but calls neither assert_value_in_prompt nor assert_no_value_in_prompt, and is not listed in DRAW_ALL_ASSERTED_BY. Either assert in place, or name the caller that asserts on its behalf — nothing draws unchecked.
E           assert None is not None
E            +  where None = <built-in method get of dict object at 0x10be52dc0>(('scripts/_red_probe2.py', 'probe'))
E            +    where <built-in method get of dict object at 0x10be52dc0> = {('scripts/phase14_recall.py', 'complete_question'): 'run_scored_recall'}.get

tests/test_phase14_scoring.py:624: AssertionError
FAILED tests/test_phase14_scoring.py::test_every_draw_all_call_site_asserts_something
1 failed in 0.79s
```

The failure names both the file and the function. Probe deleted; `git status --porcelain scripts/`
empty.

## Observed RED #4 — Task 2(b), a DANGLING `DRAW_ALL_ASSERTED_BY` entry

`("scripts/phase14_recall.py", "run_collapse_control"): "no_such_asserter"` added to the mapping.

```
E           AssertionError: DRAW_ALL_ASSERTED_BY[('scripts/phase14_recall.py', 'run_collapse_control')] names 'no_such_asserter', which is not a function in the scan that calls an in-prompt assertion. A dangling entry is a silent exemption: it excuses a drawing path by pointing at nothing.
E           assert ('scripts/phase14_recall.py', 'no_such_asserter') in {('scripts/phase14_recall.py', 'run_fairness_control'), ('scripts/phase14_recall.py', 'run_scored_recall')}

tests/test_phase14_scoring.py:632: AssertionError
FAILED tests/test_phase14_scoring.py::test_every_draw_all_call_site_asserts_something
1 failed in 0.83s
```

The second line is worth reading twice: the entire set of functions in `scripts/` + `src/` that
assert an in-prompt property is **two** — `run_scored_recall` and `run_fairness_control`. That is
the real surface this guard is protecting, printed by the guard itself. **Reverted inside a
`finally`, `RESTORED bytes-identical: True`.**

## Verification

```
.venv/bin/python -m pytest tests/test_phase14_scoring.py -q
    41 passed                          (Task 1 gate)
    42 passed                          (Task 2 gate — +1, the new test)

.venv/bin/python -m pytest -q
    425 passed, 1 skipped, 83 warnings in 120.42s (0:02:00)

.venv/bin/python -m ruff check .           All checks passed!
.venv/bin/python -m ruff format --check .  143 files already formatted

git status --porcelain scripts/            (empty — no leftover _red_probe*.py)
git diff --stat scripts/                   (empty)
git diff --exit-code scripts/              exit 0
```

**Baseline was `424 passed, 1 skipped, 83 warnings in 119.42s`, captured by the orchestrator
immediately before dispatch. Result `425 passed, 1 skipped`. Delta `+1` = Task 2's one new test.
Zero failed, zero errors, zero collection errors.**

### Acceptance criteria, item by item

| Criterion | Result |
|---|---|
| `pytest tests/test_phase14_scoring.py -q` exits 0 | 42 passed |
| `grep -c "PERSONA_ALLOWLIST"` >= 2 | **5** |
| `grep -c "DRAW_ALL_ASSERTED_BY"` >= 2 | **5** |
| AST check: an `ast.Eq` survives in the persona guard | exit `0` |
| `grep -c "issubset\|<= set("` == 0 | **0** |
| scanned-file count `>= 2` asserted in source | present; **69** files scanned today |
| `ast.AsyncFunctionDef` and `<module>` both handled in the walk | both present |
| found-site count `>= 2` asserted + non-empty tripwire | both present; 2 sites today |
| four deliberate-RED observations | above, verbatim |
| no probe files left; `scripts/` byte-unchanged | `git diff --exit-code scripts/` exit 0 |

## Decisions Made

- **One parametrized walker, not two.** `_call_sites(callee)` serves both guards;
  `_build_recall_prompt_call_sites()` is a one-line wrapper that keeps the plan's named helper
  intact. The plan's Task 2 `read_first` explicitly says the helper "this task reuses", and a
  second near-identical AST walk would be a second place for the two guards' file sets to
  silently diverge — the exact class of defect this plan is about.
- **`_scanned_files()` is deliberately NOT cached,** and the docstring says why: the
  deliberate-RED probes that prove these guards bite add and remove files under the scanned globs,
  so a module-level cache would make the guards blind to the very thing they are tested against.
- **`_function_index()` returns two sets rather than a dict.** Keying a dict on `(file, name)`
  would let two same-named defs in one file shadow each other, and a lookup that silently picks
  one of two is the blind spot this plan exists to remove.
- **`**splat` keywords are kept in the keyword frozenset** (`kw.arg is None`), so an unanalysable
  call fails the bare-form assertion instead of passing as "not `persona`". Zero extra code — the
  existing assertion already had the right shape.
- **The module docstring's item 9 was rewritten to name both guards and the widened scope,**
  rather than renumbering the list. Leaving a header describing a single-file guard above a
  69-file one would misdescribe the file.

## Concern recorded, implemented AS LOCKED

**The "no decorator on a drawing function" rule is broader than its rationale.** The plan locks
it as part of "no skip mode", and the reasoning holds for a decorator that replaces or suppresses
the function. But it also rejects a perfectly legitimate `@torch.no_grad()` or
`@functools.lru_cache` on a future drawing path, and the failure message would say "not provable"
where the honest answer is "not analysed". It is implemented exactly as locked because no such
decorator exists today (both current drawing functions have empty decorator lists, AST-verified),
so the rule costs nothing now. Whoever first wants a decorated drawing path should widen this to
an allowlist of analysis-safe decorators rather than deleting the check.

## Deviations from Plan

### 1. [Environment] `make test` / `make lint` substituted with venv-explicit invocations

- **Plan text:** `<verification>` specifies `make test`; `<verify>` blocks specify `.venv/bin/pytest`.
- **What was run:** `.venv/bin/python -m pytest -q`, `.venv/bin/python -m ruff check .`.
- **Why:** recorded fact about this machine, same substitution as 16-01 and 16-02 — a bare
  `pytest` resolves to a pyenv 3.12 shim and yields ~63 spurious
  `ModuleNotFoundError: No module named 'torch'` collection errors across files this plan never
  touched. The gate actually run is the full suite the `make` target wraps.

### 2. [Tooling] Deliberate-RED reverts performed by byte-restore inside `finally`

- Source mutations (RED #1, RED #4) were applied and restored inside `try/finally` with
  byte-identity asserted against the pre-mutation bytes (`RESTORED bytes-identical: True` for
  both). File probes (RED #2, RED #3) were removed in `finally` and their absence confirmed.
  `git diff --exit-code scripts/` exits `0`. The `finally` scoping makes the mutation window
  crash-safe, which a `git checkout` after the fact is not. Same approach as 16-01 and 16-02.

### 3. [Structure] The plan's `_build_recall_prompt_call_sites` was split into three helpers

- **Plan text:** "Rewrite `_build_recall_prompt_call_sites()` to walk a FILE SET".
- **What landed:** `_scanned_files()` + `_enclosing_functions()` + `_call_sites(callee)`, with
  `_build_recall_prompt_call_sites()` kept as a one-line wrapper over `_call_sites`.
- **Why:** Task 2 needs the same file set and the same enclosing-scope resolution for a different
  callee. Inlining all of it into one function and then copying it for `draw_all` would have
  produced two file sets that can drift apart. Every behaviour the plan specifies for
  `_build_recall_prompt_call_sites` — the tuple shape, `AsyncFunctionDef`, `<module>`, the
  attribute-call form — is present and reachable through that name.

---

**Total deviations:** 3 (1 environment, 1 tooling, 1 structure). **Zero code deviations** — no
deviation rule 1–4 fired and nothing was auto-fixed. No behaviour the plan specifies was changed.

## Issues Encountered

- **The plan's `<interfaces>` line numbers were stale by ~77 lines** (it cites the `persona=` call
  site at `:1187` and `draw_all` at `:1193`; they are at `:1264` and `:1269` after 16-02's edits).
  The call sites were located by AST rather than by line number, so this cost nothing — recorded
  only so a later reader does not chase the discrepancy.
- **No package was installed and none was needed**, so 16-01's STAT-04 `pyproject.toml` freeze was
  never approached. `git diff --stat` for `pyproject.toml` and `results/` is empty.
- The dangling identifier D-10 declares non-existent stayed out of the touched file, both commit
  messages and this summary.

## Next Phase Readiness

- **16-05 has exactly one line to extend,** quoted verbatim above, and must do it in the same
  commit as `build_far_prompt`. If it forgets, the suite goes red naming
  `('scripts/phase16_ladder.py', 'build_far_prompt')` — which is the design.
- **16-06's ladder rungs are already covered without any further edit.** They carry their value in
  the `question` string, so the `persona=` guard cannot see them; Task 2's guard keys on
  `draw_all` and will demand an assertion from each new drawing path the moment it appears.
- **The guards strengthen automatically as the phase grows.** Every new file under `scripts/` or
  `src/` enters both scans with no code change — which is exactly the property that was missing
  before this plan.
- **One thing to watch:** the scanned-file floor is `>= 2` against a real count of 69. That floor
  catches a *collapsed* glob, not a *narrowed* one — if `src/**/*.py` were dropped entirely, 25
  scripts would still clear the floor. Tightening it to a literal count would make it a
  maintenance tax on every new file, which is why it is not done; a reviewer wanting more should
  add a per-directory non-empty assertion rather than a total.

## Self-Check: PASSED

`tests/test_phase14_scoring.py` exists on disk carrying every claimed symbol — `PERSONA_ALLOWLIST`,
`DRAW_ALL_ASSERTED_BY`, `_scanned_files`, `_enclosing_functions`, `_call_sites`, `_function_index`,
`_build_recall_prompt_call_sites`, `test_persona_argument_is_scoped_to_the_fairness_control`,
`test_every_draw_all_call_site_asserts_something` — all located by grep and all exercised by the
42-test file run. Both task commits resolve in `git log`: `dd17187`, `70ee124`. All four
deliberate-RED observations were run and their output is reproduced verbatim above; both source
mutations restored byte-identical and both probe files deleted (`git diff --exit-code scripts/`
exit 0). Working tree carries only the two pre-existing unrelated items this plan did not touch:
modified `.gitignore`, untracked `AGENTS.md`.

---
*Phase: 16-weight-vs-prompt-persistence-control*
*Completed: 2026-08-13*
</content>
</invoke>
