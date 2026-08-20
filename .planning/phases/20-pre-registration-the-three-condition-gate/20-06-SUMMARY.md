---
phase: 20-pre-registration-the-three-condition-gate
plan: 06
subsystem: testing
tags: [pre-registration, ast-audit, import-graph, watched-red, behavioural-twin, runtime-measured]

# Dependency graph
requires:
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 01
    provides: "tests/test_phase20_prereg.py with _ROOT, _git, PHASE20_PREREG_ARTIFACT, V4_ARTIFACT_GLOBS, _assert_ordering_holds; scripts/mitigation_gate.py's spine"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 03
    provides: "scripts/_prose.py::normalized and _PROSE_PATH; the D-22 throwaway-repo fixture"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 05
    provides: "the CLOSED pin — FIXTURE_CLEARING_POINT / FIXTURE_DESTROYED_MODEL / FIXTURE_TRUNCATED_SWEEP, exists_clearing_point, ratchet_k, promote_to_full_fidelity, capacity_comparison, the six-outcome __main__"
  - phase: 19-selective-erasure
    provides: "results/phase19_arm_erased.json — the published M1 readings the D-30 fixture is proved EQUAL to"
provides:
  - "_MITIGATION_GATE_PATH + _GATE_MODULES — the hybrid register (explicit constant PLUS mitigation_*.py glob) that admits Phase 23's mitigation_budget.py automatically"
  - "_collapsed_glob_guard, _tree, _enclosing_functions, _module_scope_floats, _module_scope_fixture_names, _numeric_constants_outside_fixtures — the AST scoping helpers every audit here runs on"
  - "Fourteen CI guards over the closed pin: the import graph, object identity, the D-23 fnmatch exemption, two chosen constants, no retyped baseline, the fixture-vs-artifact identity, the three-verdict domain, keyword-only signatures, and the six-outcome behavioural twin"
  - "20-VALIDATION.md's MEASURED full-suite and per-task runtimes, replacing the pre-phase estimate row"
affects: [20-07, phase-21, phase-23, phase-25]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "EVERY audit committed here is an AST walk or goes through _prose.normalized — zero `grep -c` and zero `in src` instruments, because this phase has now produced FOUR criteria that a naive substring scan would have answered wrongly"
    - "The hybrid register: an explicit path constant for the file that exists today PLUS a glob that admits the file Phase 23 will create, tied together by a membership assertion so they cannot drift into naming two different files"
    - "Each precedence claim asserts BOTH arms of its differential — the base verdict and the overridden one — so an INCONCLUSIVE is never observed alone"
    - "Expected values are RECOMPUTED through the committed functions, never transcribed: the tolerance sentence, the fixture's control_gap, and every K rung are read off the source of truth"

key-files:
  created: []
  modified:
    - tests/test_phase20_prereg.py
    - .planning/phases/20-pre-registration-the-three-condition-gate/20-VALIDATION.md

key-decisions:
  - "Mutation (a) was moved from `_prove` into `capacity_comparison` after the first placement produced a COLLECTION ERROR rather than the D-20 assertion. `_prove` runs at import via `_prove_verdict_domain()`, so a `import mitigation_budget` inside it aborts the test module before any scan runs — a different red. `capacity_comparison` is never called at import, so the module loads and the STATIC assertion is what fires. The relocated placement is also the stronger observation: it proves the AST walk finds an import at ANY depth, not merely at top level"
  - "The `provisional` audit is an AST walk over identifiers AND string constants, with a SECOND check on `_prose.normalized(source)` covering comments — the one textual surface the parser discards. The plan asked for a case-insensitive source scan; that scan alone is the instrument class this plan exists to stop committing, so it was demoted to the comment-only half"
  - "The keyword-only and constant audits scan the PIN ONLY (`_MITIGATION_GATE_PATH`), while the import-graph audit scans ALL of `_GATE_MODULES`. RPT-03 and D-20 are properties of the import graph and must cover Phase 23's budget module the moment it exists; GATE-01's signature discipline and D-18's two-constants claim are properties of the DECISION RULE, and asserting them over a resource module this plan has never seen would be a claim it cannot make"
  - "`_module_scope_fixture_names` and `_numeric_constants_outside_fixtures` were split out as named helpers rather than inlined, because each has a docstring carrying a fact a reader needs — the allow-list's purpose, and that `isinstance(True, int)` is True in Python so booleans must be excluded explicitly or `1 in numbers` becomes meaningless"

patterns-established:
  - "A watched-RED mutation whose red arrives at the WRONG STAGE is not a verified guard. Mutation (a) was re-driven at a placement where the intended assertion is what fires, and both attempts are recorded with their sha256 rather than only the one that worked"

requirements-completed: []

# Metrics
duration: 16min
completed: 2026-08-20
---

# Phase 20 Plan 06: The Audits Over the Closed Pin Summary

**The closed pin is now under fourteen CI guards — its import graph proved stdlib-plus-`erasure_gate` by a SUBSET assertion, its two chosen constants proved to be exactly two three ways over, six baselines proved absent as numeric constants, and all six verdict outcomes re-run in CI against the same module-scope fixtures the `__main__` uses — with five mutations watched turning it red and `scripts/mitigation_gate.py` byte-UNCHANGED throughout.**

## Performance

- **Duration:** 16 min 14 s
- **Started:** 2026-08-20T17:49:20-03:00 — the prior plan's `docs(20-05)` commit `2607a31`
- **Task commits:** `5dcde75` at **17:55:38-03:00**, `741649f` at **17:59:10-03:00**, `ad014d3` at **18:05:34-03:00** (all read from `git log --format=%cI`, never estimated)
- **Tasks:** 3 of 3
- **Files modified:** 2 — `tests/test_phase20_prereg.py` (417 → 1,368 lines) and `20-VALIDATION.md`. `git diff --stat 5dcde75~1 ad014d3` reports **964 insertions / 7 deletions**; the seven deletions are all in `20-VALIDATION.md`, where two runtime rows, one latency bullet and two sign-off boxes were replaced with measured numbers. **`tests/test_phase20_prereg.py` is a pure append: 952 insertions, 0 deletions.**
- **Files deleted:** 0 (`git diff --diff-filter=D` across all three commits is empty)

## THE PIN IS BYTE-UNCHANGED

`scripts/mitigation_gate.py` sha256 at every checkpoint of this plan:
**`86db479876ebeb2ba5b23c3b95da0ab20f13a3fbccf655b697280421b1997e14`** — identical to the value
20-05 recorded at `abf9072`, and identical after each of the five deliberate mutations was reverted.
The pin appears in no commit this plan made. `git log --diff-filter=A -- 'results/phase20_*'` is
**still EMPTY**, re-confirmed after the final task commit, so D-08's strictly-after ordering remains
intact and untouched until 20-07.

## The five watched-RED mutations, with both sha256 values each

A guard nobody has watched fail is a guard nobody has verified. Each mutation was applied to the
pin, the intended assertion observed failing, and the pin restored from a byte-copy taken before any
mutation ran.

| # | Mutation | sha256 WHILE MUTATED | Guard observed RED | sha256 AFTER RESTORE |
|---|---|---|---|---|
| a | `import mitigation_budget` inside `capacity_comparison` | `8af616bdf7f5b55aba51eba185f57d3b46c38c1df771c2504e6b94c2e7a13782` | `test_..._import_graph_is_stdlib_and_erasure_gate_only` — `assert 'mitigation_budget' not in {'erasure_gate', 'mitigation_budget', 'pathlib', 'sys'}` | `86db4798…1997e14` |
| a′ | *(first attempt)* the same import inside `_prove` | `55b66857fd34d00fb429053da0a3056c08eb6be01022307a5681a0c78eda2061` | **COLLECTION ERROR**, not the D-20 assertion — see *Deviations* | `86db4798…1997e14` |
| b | `def wilson_upper_bound(successes, n): return 0.0` at module scope | `459532e9683b0861b9c4a505c5516d8b1dfab82491768746d22af84408e518db` | **TWO** guards: the static `defined` assertion AND `test_..._imports_bounds_by_object_identity` (`<function … at 0x10adb1580> is not <function … at 0x10adb0f40>`) | `86db4798…1997e14` |
| c | `VERDICTS,` added to the `from erasure_gate import` list | `f87c1c49b1ad81862a13818a3be88d877e1efec78694edda280044fb266c3c36` | the EXACT-equality assertion — `Extra items in the left set: 'VERDICTS'` | `86db4798…1997e14` |
| d | `THIRD_CONSTANT = 0.9` at module scope | `1b8213fb05c210732dca53b5a18fd1882ac2fb70da74adebfc27d08c55fef3a4` | `test_exactly_two_chosen_constants` — `Extra items in the left set: 0.9` | `86db4798…1997e14` |
| e | `def retention_cap(*, retention_noise_floor=0.0)` | `72195fcb3b9f897c265c20f2bb0725d9e3385fd73f8f1c19b6ffc7fa8d2735f0` | `test_every_gate_function_is_keyword_only_with_no_defaults` — `At index 0 diff: <ast.Constant …> != None` | `86db4798…1997e14` |

**Mutation (b) reddened two independent guards, and that is the belt-and-braces working rather than
redundancy.** The static half reads the SOURCE (the name appears in a `FunctionDef`), the runtime
half reads the LOADED NAMESPACE (`is`-identity). A module that passed the first while failing the
second would be one whose import had been shadowed after the fact.

## Test count and runtime, both MEASURED

| metric | value |
|---|---|
| `pytest -q tests/test_phase20_prereg.py` | **18 passed** in **0.79–0.81 s** (three consecutive runs; wall 0.95–0.97 s with interpreter startup) |
| tests before this plan | 4 |
| tests added | **14** — 3 in Task 1, 5 in Task 2, 6 in Task 3 |
| full suite `pytest -q` | **863 passed, 1 skipped, 0 failed** in **188.55 s** (wall 189.72 s) |
| full suite before this plan (20-05) | 849 passed, 1 skipped in 186.74 s |
| full suite pre-phase baseline (20-VALIDATION.md, superseded) | 845 passed, 1 skipped in 201.99 s |

**The 13.44 s difference against the pre-phase baseline is MACHINE VARIANCE, not a speedup, and
`20-VALIDATION.md` now says so in those words.** Phase 20's 18 tests cost about 1.6 s; a suite that
gained 18 tests cannot have got 13 s faster because of them. The honest comparison is against
20-05's 186.74 s, one wave earlier on the same machine: 188.55 s, i.e. **+1.81 s for 14 new tests**.

**Max feedback latency is now a measured `0.81 s`.** Over the 14 non-exempt tasks the per-task /
per-wave split saves `14 x (188.55 - 0.81) = 2628 s`, about **44 minutes** of serial waiting. The
naive "18 x" figure reads 56 minutes and is wrong — four of the eighteen tasks run the full suite by
design, so they never pay the saving. That correction is written into `20-VALIDATION.md` rather than
left implicit.

## Task Commits

1. **Task 1: The hybrid AST register and the import-graph guards** — `5dcde75` (test)
2. **Task 2: The constant audits — two chosen constants, no retyped baseline, no fourth verdict state** — `741649f` (test)
3. **Task 3: The behavioural twin — every branch re-run in CI against the same fixtures** — `ad014d3` (test)

**Plan metadata:** see the `docs(20-06)` commit that carries this SUMMARY.

## The fourteen guards, and what each one would catch

| test | catches |
|---|---|
| `test_mitigation_gate_import_graph_is_stdlib_and_erasure_gate_only` | a budget import (D-20), an unanticipated third-party import (SUBSET over an allow-set), a truncated OR overgrown `from erasure_gate` list (EXACT equality), `VERDICTS` or `V20_RETENTION_NOISE_FLOOR` entering the namespace, a locally re-implemented bound |
| `test_mitigation_gate_imports_bounds_by_object_identity` | a bound or baseline rebound to a value-matching copy — `is`, never `==`, on all five symbols |
| `test_prose_helper_is_outside_every_pin_glob` | a rename of `_prose.py` that drops the leading underscore and freezes a helper Phases 21–28 still need (D-23) |
| `test_exactly_two_chosen_constants` | a third chosen constant at module scope, a `CHOSEN_CONSTANTS` that has drifted from the source, a re-keyed audit surface, a FOURTH `FIXTURE_*` dict |
| `test_no_imported_baseline_is_retyped` | any of six baselines retyped as a numeric constant, `MARGIN_K` dropped from the import list, the superseded GATE-02 cap appearing as a constant **or** as prose, and a `superseded_dialogue_cap` that stops reproducing it bit-exactly |
| `test_destroyed_model_fixture_matches_the_published_phase19_readings` | a fat-fingered digit in any of the four fields claiming a published source, including the one-ULP `control_gap` trap |
| `test_verdict_domain_stays_exactly_three` | a fourth verdict, a `provisional` flag in any identifier / string / comment, a relabel map that stops being positional, `INCONCLUSIVE` moved |
| `test_every_gate_function_is_keyword_only_with_no_defaults` | a positional or defaulted argument on any of the pin's ten public functions |
| `test_gate_self_check_runs_clean_in_a_fresh_interpreter` | a `__main__` that stopped running, or an import-time proof that only passes from a `sys.modules` cache |
| `test_every_verdict_branch_fires` | any of the six outcomes ceasing to fire, a precedence branch that stops overriding the verdict it is supposed to override, a mixed-arm union, an `INCONCLUSIVE` satisfying the existential, a claim published without its denominator |
| `test_promotion_rule_and_ratchet` | a K decrease, an off-menu K, a promotion rule that reaches a SECOND ratchet implementation |
| `test_capacity_rule_commits_both_branches_and_refuses_the_unset_fallback` | a non-total dispatch, a tolerance creeping onto the structural route, a defaulted D-26 fallback constant, a branch name outside the closed tuple |
| `test_extraction_floor_tripwire_is_the_only_route_to_a_verdict` | a path to a verdict that computes X from a single-seed or borrowed-arm floor |
| `test_condition_a_reason_carries_its_tolerance_sentence` | a verdict published without the reader learning how strong the criterion was (D-14b) |

### The differentials, each naming the verdict it overrides

| branch | base verdict | overridden to | asserted |
|---|---|---|---|
| GATE-05, zero extraction with no NLL | **FAIL** | `INCONCLUSIVE`, **1 reason** (early return) | both arms, from otherwise-identical kwargs |
| GATE-06, truncated sweep | **FAIL** | `INCONCLUSIVE`, **>1 reason** (late return keeps the detail) | both arms |
| GATE-08 / D-29, replication pending | **PASS** | `INCONCLUSIVE`, **3-tuple**, last reason opens with `REPLICATION_PENDING_MARKER` | both arms |

Two override a would-be FAIL and one a would-be PASS. An INCONCLUSIVE that only overrode a PASS
would prove nothing about precedence over FAIL, which is why each differential is driven against the
verdict it actually has to beat rather than against whichever one was convenient.

## Deviations from Plan

**Rules 1, 2 and 4 did not fire. Rule 3 fired once**, on a mutation harness rather than on shipped
code.

### Auto-fixed blocking issues

**1. [Rule 3 - Blocking] Mutation (a) was relocated so the intended assertion is what fires**

- **Found during:** Task 1's watched-RED sequence
- **Issue:** the plan's mutation (a) is "add `import mitigation_budget` to the gate". Placed at
  module scope, or inside `_prove` as first attempted, the import EXECUTES — `_prove` is called at
  module scope by `_prove_verdict_domain()` — so `tests/test_phase20_prereg.py` died at collection
  with `ModuleNotFoundError: No module named 'mitigation_budget'`. That is a red, but it is the
  WRONG RED: the D-20 assertion never ran, so nothing was observed about the guard the mutation was
  supposed to be testing. Recorded rather than quietly re-rolled, because a watched-RED whose red
  arrives at the wrong stage is a guard that has not actually been verified.
- **Fix:** the import was placed inside `capacity_comparison`, which is never called at import.
  The module then loads normally and the STATIC scan is what fires — observed reporting
  `imports: ['erasure_gate', 'mitigation_budget', 'pathlib', 'sys']`. The relocated placement is
  also the stronger observation: it proves the `ast.walk` finds an import at ANY depth, where a
  top-level-only scan would have missed it.
- **Files modified:** none shipped — `scripts/mitigation_gate.py` was mutated and restored
  byte-identically (`8af616bd…` → `86db4798…`), and `tests/test_phase20_prereg.py` was not changed
  by this at all.
- **Commit:** the guard being verified is in `5dcde75`; the mutation itself is in no commit.

**Total deviations: 1, Rule 3.**

## Path / naming discrepancies found

**A FOURTH substring-shaped instrument in this phase would have misfired, and this one is new.**
20-03's `grep -c "shell=True"`, 20-04's `'V20_RETENTION_NOISE_FLOOR' in src` and 20-05's `__doc__`
case-mismatch are on record. This session found a fifth candidate the plan did not name:

| value | present as a numeric constant? | present as a source substring? | where |
|---|---|---|---|
| `0.4921` | **NO** | **YES** | `scripts/mitigation_gate.py:200` — the `F_Y` provenance comment reading *"never : v2.0's published 0.4921 / 0.3483 pair. GATE-04 forbids deriving Y from it"* |
| `0.3483` | **NO** | **YES** | the same line |
| `0.005214448168350039` | **NO** | **YES** | `:568` — inside `dialogue_gap_band.__doc__`, 20-04's D-04 bit-identity proof |

An `in src` audit on any of the three would have reported a violation and demanded the removal of
the very prose that STATES the rule. **Prose about a number is not the number.** Every audit in this
plan is an `ast.Constant` walk and is unaffected; the fact is written into
`test_no_imported_baseline_is_retyped`'s docstring so the next reader does not "fix" it with a grep.

**One acceptance criterion is exit-code-fragile rather than wrong.** Task 2's
`grep -ci "provisional" scripts/mitigation_gate.py` outputs `0` as required — but `grep -c` **exits
1** when the count is zero, so the criterion cannot be chained with `&&` as written. It was run
standalone and reported `0`. The committed guard does not use grep at all.

**Everything else resolved from the code, not from prose.** Re-derived independently at the start of
this session rather than taken from the handover: the pin's sha256 and its 1,431 lines; module-scope
assigned floats outside `FIXTURE_*` = `{0.5, 0.7}`; `CHOSEN_CONSTANTS` = 2 entries; the three
`FIXTURE_*` names; `imported == {'erasure_gate', 'pathlib', 'sys'}`; the five-name
`from erasure_gate` list; all ten public functions keyword-only with zero defaults;
`superseded_dialogue_cap(gap_noise_floor=0.005214448168350039) == 4.5837288963367` exactly; and
`results/phase19_arm_erased.json`'s `retention_ppl` confirmed a **LIST** while `dialogue_ppl` is a
**dict**. Every handover fact held.

## Issues Encountered

**Three `E501` line-length violations**, all in comment prose and one f-string message, all fixed by
rewrapping before the commit. No commit was made red: `ruff check .`, `ruff format --check .` and
`tests/test_phase20_prereg.py` were green at all three commit points, and no test failed at any
moment in this plan except the five deliberate mutations.

**One figure was corrected in place before it shipped.** The first draft of `20-VALIDATION.md`'s
latency bullet claimed the per-task split saves "roughly 56 minutes at 18 tasks" — which contradicts
the same file's own statement that four of the eighteen tasks run the full suite by design. The
committed text carries the arithmetic for the **14 non-exempt** tasks (`~44 minutes`) and names the
wrong figure so a reader cannot re-derive it by accident.

## Known Stubs

**None.** Every guard committed here runs against live objects and real source; none is skipped,
xfailed or parameterized over an empty set. The two places a guard could be green over nothing are
both explicitly closed: `_collapsed_glob_guard()` runs before every glob-driven scan, and
`test_every_gate_function_is_keyword_only_with_no_defaults` asserts its public-function list is
non-empty before iterating it.

**One residual hole is ACCEPTED and stated in words rather than closed**, in
`_module_scope_floats`'s docstring and again in `test_exactly_two_chosen_constants`: the float audit
excludes `FIXTURE_*` assignments, so **a third chosen constant hidden inside one of the three fixture
dicts would not be caught.** Four fields are proved against `results/phase19_arm_erased.json`
(`point_dialogue_ppl_on`, `point_dialogue_ppl_off`, `point_retention_ppl`, `control_gap`); every
other float in those dicts is deliberately fabricated and has no source to be checked against,
because no v4.0 arm exists (D-13). Asserting fabricated inputs against a source that does not exist
would be exactly the unprovable assertion this phase exists to refuse. What the hole IS narrowed by
is the name allow-list: the module-scope `FIXTURE_*` names are asserted to be exactly the three that
exist, so the cheapest evasion — a fourth fixture dict — is caught.

## Verification (wave boundary)

| check | result |
|---|---|
| `.venv/bin/python -m pytest -q` | **863 passed, 1 skipped** in **188.55 s** |
| `.venv/bin/python -m pytest -q tests/test_phase20_prereg.py -v` | **18 passed** (criterion: at least 14) |
| `.venv/bin/python scripts/mitigation_gate.py` | exit **0** |
| `.venv/bin/ruff check .` | All checks passed |
| `.venv/bin/ruff format --check .` | 173 files already formatted |
| `git status --porcelain pyproject.toml` | empty — byte-unchanged, RPT-03's sha256 pin carries forward to a fourth milestone |
| `git log --diff-filter=A -- 'results/phase20_*'` | **EMPTY** — re-confirmed after the final commit |
| `shasum -a 256 scripts/mitigation_gate.py` | `86db479876ebeb2ba5b23c3b95da0ab20f13a3fbccf655b697280421b1997e14` — unchanged |
| test-module import ledger (AST) | `['_prose', 'ast', 'erasure_gate', 'fnmatch', 'json', 'mitigation_gate', 'pathlib', 'pytest', 'subprocess', 'sys']` — `fnmatch`/`erasure_gate`/`mitigation_gate` in Task 1, `json` in Task 2, each with its first consumer |
| `grep -c " is erasure_gate\."` | **5** (criterion: at least 5) |
| `grep -c "FIXTURE_DESTROYED_MODEL\|FIXTURE_CLEARING_POINT\|FIXTURE_TRUNCATED_SWEEP"` | **18** (criterion: at least 8) |
| `grep -c "4\.851119149910443" tests/test_phase20_prereg.py` | **0** — no Phase 19 reading is re-transcribed into the test module |
| `grep -ci "provisional" scripts/mitigation_gate.py` | **0** |
| `git diff --diff-filter=D` across all three task commits | empty — no file deleted |

## Threat Flags

None. This plan adds no network surface, no auth path and no schema. Its only I/O is reading files
already in the repository (`json.loads` on a committed artifact, `read_text` on two source files)
and one `subprocess.run` of `sys.executable scripts/mitigation_gate.py` with an **argv tuple** —
`shell=True` appears nowhere in the module, and the pre-existing D-22 fixture's writes remain
confined to pytest's `tmp_path`.

Threat-register dispositions discharged by this plan:

| Threat ID | Disposition | How this plan discharges it |
|---|---|---|
| T-20-33 | mitigate | `assert "mitigation_budget" not in imported`, fed by both `ast.Import` and `ast.ImportFrom`, over every module in `_GATE_MODULES`. **Watched RED** against a deliberate `import mitigation_budget` and reverted byte-identically |
| T-20-34 | mitigate | Static: the name must appear in `from_erasure_gate` and must NOT appear among the module's `FunctionDef` names. Runtime: `is`-identity on all five symbols, never `==`. **Watched RED** against a local `def wilson_upper_bound` — both halves fired |
| T-20-35 | mitigate | `_module_scope_floats` asserted `== {0.7, 0.5}`, `== set(CHOSEN_CONSTANTS.values())` and its keys `== {"F_Y", "F_C"}`, plus the three-name `FIXTURE_*` allow-list. **Watched RED** against `THIRD_CONSTANT = 0.9` |
| T-20-36 | mitigate | Six baselines asserted absent from the pin's numeric constants; the superseded cap absent both as a constant and as a substring; `MARGIN_K` asserted present in the import list; the supersession proved to be a bit-exact computation |
| T-20-37 | mitigate | D-30's four published fields asserted EQUAL to the parsed `results/phase19_arm_erased.json`, with `retention_ppl` accessed by index `[0]` as the LIST it is and `control_gap` asserted as the subtraction rather than against a typed decimal |
| T-20-38 | mitigate | Six outcomes re-asserted in CI against the SAME module-scope fixtures the `__main__` uses, plus the module run as a subprocess in a fresh interpreter so `_prove_verdict_domain()` and the `ARM_CLAIMS` proof re-execute instead of hitting a `sys.modules` cache |
| T-20-39 | mitigate | The hybrid register's `mitigation_*.py` glob admits Phase 23's `mitigation_budget.py` automatically; `_collapsed_glob_guard()` makes a broken glob loud instead of green; and `_MITIGATION_GATE_PATH in _GATE_MODULES` stops the constant and the glob drifting apart |

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **20-07 opens with a BLOCKING HUMAN CHECKPOINT** declaring the pin final. Everything that
  checkpoint needs is green now: the full suite, both ruff gates, the pin's `__main__`, an untouched
  `pyproject.toml`, and an empty `results/phase20_*` add-history. The pin's sha256 to read the
  checkpoint against is `86db479876ebeb2ba5b23c3b95da0ab20f13a3fbccf655b697280421b1997e14`.
- **The next commit touching `scripts/mitigation_gate.py` after 20-07 commits
  `results/phase20_retention_floor.json` turns `test_phase20_prereg_is_frozen_before_every_phase20_result`
  permanently RED**, and `git rm` plus a re-add cannot launder it. Fourteen new guards now watch the
  file's contents in addition to that ordering guard, so a correction attempted as an edit fails in
  two independent places rather than one.
- **`20-VALIDATION.md`'s two runtime sign-off boxes are now ticked** with measured numbers.
  `nyquist_compliant: true` and `wave_0_complete: true` remain open and are 20-07 Task 3's, as its
  own sign-off list states. **The per-task Status column was deliberately left at `⬜ pending` for
  all eighteen rows**, including this plan's three: no prior plan in this phase flipped its own
  rows, and flipping only 20-06's would falsely imply 20-01…20-05 were still outstanding. A
  whole-column sweep belongs to 20-07 Task 3, which already owns the frontmatter flags.
- **No requirement was marked complete.** GATE-01 through GATE-10, CAL-04 and RPT-02 are all
  exercised by the guards committed here, but this project's recorded over-claim-avoidance pattern
  says a requirement is not marked complete in the plan that first touches it, and 20-07 still has
  to land the artifact that makes the ordering irreversible. **Twelfth application.**

**Standing constraint, unchanged and absolute:** `scripts/mitigation_gate.py` is COMPLETE and CLOSED.
Do not amend, rebase, squash or cherry-pick any commit touching it. Any further change is a dated
continuation via `scripts/_addendum.py`, recorded outside the file.

## Self-Check: PASSED

- `tests/test_phase20_prereg.py` — FOUND
- `.planning/phases/20-pre-registration-the-three-condition-gate/20-VALIDATION.md` — FOUND
- `.planning/phases/20-pre-registration-the-three-condition-gate/20-06-SUMMARY.md` — FOUND
- commit `5dcde75` — FOUND
- commit `741649f` — FOUND
- commit `ad014d3` — FOUND
- `scripts/mitigation_gate.py` sha256 `86db479876ebeb2ba5b23c3b95da0ab20f13a3fbccf655b697280421b1997e14` — unchanged, and the file appears in none of the three commits above

---
*Phase: 20-pre-registration-the-three-condition-gate*
*Completed: 2026-08-20*
