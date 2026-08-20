---
phase: 17-multi-persona-isolation-matrix
plan: 01
subsystem: statistics-preregistration
tags: [stat-05, stat-04, stat-06, iso-05, iso-07, holm, pre-registration, git-ancestry]
requires:
  - scripts/phase16_persistence.py (holm, sign_test_exact, GATED_TIER, HOLM_FAMILY_PAIRS)
  - scripts/phase14_recall.py (normalize, contains_value — lazily, inside filter bodies)
  - results/phase16_recall_sample.json (the binding fixture — read only to verify CORE_SLOTS)
  - .planning/phases/17-multi-persona-isolation-matrix/17-CONTEXT.md (D-18 blockquote, read at test time)
provides:
  - scripts/phase17_personas.py (the Phase 17 pre-registration — constants + pure functions)
  - PERSONAS / CORE_SLOTS / SLOTS_EXPECTED / QUESTIONS_PER_SLOT / BASE_ROW / GATED_TIER
  - HOLM_FAMILY_CELLS / CELL_ALTERNATIVE / SIGN_UNIT
  - PERSONA_SEEDS / REPLICATION_SEEDS / LORA_CONFIG_NOTE
  - GATE_AGGREGATION_RATIONALE / ALL_FAIL_BRANCH / MAX_VALUE_TOKENS
  - gate_cleared / worst_pair / assert_phase17_family_closed / assert_family_length_matches_phase16
  - filter_token_budget / filter_roundtrip / filter_substring_disjoint / filter_absent_from_questions
  - tests/test_phase17_stats.py (10 tests) and the Phase 17 ordering guard in tests/test_phase16_prereg.py
affects:
  - plan 17-03 (must land the 24 values in scripts/phase17_persona_facts.py, NOT in the pinned file)
  - plan 17-04 (fixture regrouping checked against CORE_SLOTS, not against 17-03's material)
  - plans 17-07 / 17-09 (each must assert checked > 0 in test_phase17_prereg_is_frozen_...)
tech-stack:
  added: []
  patterns:
    - pre-registration as module-level literals in a committed driver (STAT-05, carried unchanged)
    - derived-not-retyped constants (family from PERSONAS, SLOTS_EXPECTED from CORE_SLOTS,
      REPLICATION_SEEDS from PERSONA_SEEDS)
    - verbatim text READ from the planning artifact, never a second hand-typed copy
    - ordering enforced by git ANCESTRY over every touching commit, never by a pinned SHA or dates
    - guards mutation-proved — watched failing before being trusted
key-files:
  created:
    - scripts/phase17_personas.py
    - tests/test_phase17_stats.py
    - .planning/phases/17-multi-persona-isolation-matrix/deferred-items.md
  modified:
    - tests/test_phase16_prereg.py (additive: 1 constant + 1 test, 0 deletions)
decisions:
  - D-18/D-19/D-10/D-14/D-16/D-20 committed as literals before any adapter trains
  - the pre-registration and the persona material live in TWO files, and the split is what
    lets ROADMAP SC2's ADAPT branch exist at all
  - the ISO-05/STAT-06 identifier ban stays call-site-scoped (Phase 16's committed scope);
    widening it to module-level assignment targets would be self-invalidating in Wave 1
metrics:
  duration: 34min
  tasks: 3
  files: 4
  completed: 2026-08-14
---

# Phase 17 Plan 01: Pre-Registration Commit Summary

Phase 17's entire gate — the six-comparison Holm family, six declared directions, three training
seeds, the k=3 replication seeds, the all-six clearance rule, the `worst_pair` tie-break, the
all-fail branch and the four minting filters — is now in git history as module-level literals,
before a single persona value or adapter exists, and an edit to it after a Phase 17 number lands
turns a committed test red.

## What Was Built

### Task 1 — `scripts/phase17_personas.py` (commit `d549e0b`)

The pre-registration block. Every constant that could otherwise be chosen after seeing a number:

| Name | Form | Why this form |
|---|---|---|
| `HOLM_FAMILY_CELLS` | comprehension over `PERSONAS` | a retyped family can stop matching the cells it claims to compare; 3 rows x 2 off-diagonals = 6 |
| `CELL_ALTERNATIVE` | six literal entries | a reviewer audits six committed statements; key-set equality proved at runtime, never by construction |
| `CORE_SLOTS` | literal tuple, 8 names | THE canonical slot list — 17-03 and 17-04 are each checked against it rather than against each other |
| `SLOTS_EXPECTED` | `len(CORE_SLOTS)` | derived; a second literal 8 is a second number that can stop agreeing |
| `REPLICATION_SEEDS` | derived from `PERSONA_SEEDS` | k=3 counting the original seed, committed before the matrix is read |
| `GATE_AGGREGATION_RATIONALE` | implicit concatenation | asserted against `17-CONTEXT.md`, not against a second hand-typed copy |
| `BASE_ROW` | `"base"` | excluded from the family BY CONSTRUCTION and re-proved at runtime |

Pure functions: `_prove` (own `[phase17_personas]` prefix), `assert_phase17_family_closed` (four
proofs), `assert_family_length_matches_phase16` (F-08), `gate_cleared` (D-18),
`worst_pair` (D-19), and the four minting filters.

`CORE_SLOTS` was verified against the binding fixture rather than transcribed on faith: deriving
`fact_id -> slot` through `phase14_factset` over `results/phase16_recall_sample.json`'s 104
`core_held_out` questions reproduces the eight names in exactly the committed order, at exactly 13
questions per slot.

### Task 2 — the ordering guard (commit `7c269f5`)

`tests/test_phase16_prereg.py` gains `PHASE17_PREREG_ARTIFACT` and
`test_phase17_prereg_is_frozen_before_every_phase17_result`. Additive: `git diff HEAD~1` shows
exactly **one** `-` line, the diff header. `PREREG_COMMIT`, `V3_ARTIFACT_GLOBS`, `_git` and both
existing tests are byte-unchanged.

The rule is derived from history rather than pinned to a SHA — every commit touching the driver
must be an ancestor of every `results/phase17_*` first-add commit. That is smaller *and* stronger:
self-identifying (no pin to get wrong, so no identity test needed) and it catches the post-hoc edit
a SHA pin permits. It carries the shallow-clone assertion, a tracked-and-committed assertion on the
driver, and `checked == len(prereg_commits) * len(tracked_artifacts)`.

### Task 3 — `tests/test_phase17_stats.py` (commit `c9dcbba`)

10 tests, CPU-only, no torch import in the file, drivers loaded via `importlib`. `_GATE_MODULES` is
a **glob** over `scripts/phase17_*.py`, so 17-03/17-04/17-05's drivers enter every scan the moment
their plans create them — D-21's answer to the F-08 blindness.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] The module-level-call acceptance command is vacuous**

- **Found during:** Task 1 acceptance criteria.
- **Issue:** the plan's command scans `tree.body` for an `ast.Expr` wrapping an `ast.Call`. The
  `sys.path` bootstrap is nested inside an `if`, so it lives in `tree.body[i].body`, not
  `tree.body`. The command finds **0** calls and `all([])` is `True` — it passes while checking
  nothing, the exact green-and-blind shape the criterion's own wording warns about one clause
  earlier. The plan closed the `isinstance(n, ast.Call)` trap and stepped into the `if`-nesting one.
- **Fix:** ran the plan's command as written (passes, 0 calls) **and** a module-SCOPE walk that
  excludes only function and class bodies, which finds exactly 1 call and confirms it is
  `sys.path.insert(0, str(_REPO_ROOT / 'scripts'))`. Promoted the stronger form to a committed
  test, `test_phase17_stats.py::test_nothing_executes_at_import`, so the claim in the driver's
  docstring is enforced rather than remembered.
- **Files modified:** `tests/test_phase17_stats.py`
- **Commit:** `c9dcbba`

**2. [Rule 1 - Bug] Two Task-1 acceptance criteria contradicted each other**

- **Found during:** Task 1 acceptance criteria.
- **Issue:** the action mandates recording the two-file split reasoning in the docstring, and the
  plan's own prose names the three constants that live elsewhere. The criterion
  `grep -c "PERSONA_FACTS\|VALUE_TOKEN_CENSUS" ... returns 0` then fails on that very prose — the
  first draft returned 1, on a docstring sentence saying those constants are *not* here.
- **Fix:** the docstring records the same reasoning in words ("the 24 minted values, their measured
  token census and the derived forbidden set") and states explicitly why the identifiers are not
  written out. The criterion's intent — no persona material in the pinned file — is satisfied
  strictly, and the trap warning survives intact.
- **Files modified:** `scripts/phase17_personas.py`
- **Commit:** `d549e0b`

**3. [Rule 3 - Blocking] `dict(mapping, **kwargs)` with tuple keys**

- **Found during:** Task 3, first run of `test_worst_pair_tiebreak`.
- **Issue:** `TypeError: keywords must be strings` — the rate dicts are keyed by `(i, j)` tuples.
- **Fix:** `{**all_zero, (b, c): 0.5, ...}` literal merge.
- **Commit:** `c9dcbba`

### Deliberate simplification

`_function_def` was **not** copied from `tests/test_phase16_stats.py`. No test in this plan needs a
named function's body AST, and an unused copied helper is a second copy of a rule that can drift
with nothing exercising it. Copy it in 17-04 if that plan's AST criteria need it.

### Interpretation recorded

The plan lists one forbidden-substring tuple for two tests. It was split along the requirement
boundary — `("replication", "seed_rep")` for ISO-05 and
`("aggregate", "overall", "matrix_rate", "isolation_rate")` for STAT-06 — so each test fails for
its own reason. The union is the plan's tuple exactly.

`gate_cleared`'s docstring **cites** `GATE_AGGREGATION_RATIONALE` by name rather than pasting the
Portuguese into it. Pasting would have put a second hand-typed copy in the same file the constant
exists to be the single copy of.

**4. [Rule 1 - Bug] `requirements mark-complete` over-claimed three requirements**

- **Found during:** state updates.
- **Issue:** the plan's frontmatter lists `[STAT-03, STAT-04, STAT-05, STAT-06, ISO-05, ISO-07]`,
  and `requirements mark-complete` checks every id it is handed. But **STAT-03 is also claimed by
  17-08, and ISO-05 by 17-08, 17-10 and 17-11** — the first plan to name a requirement marks it
  Complete for the whole phase. ISO-05 reads "the worst-colliding pair is replicated across seeds";
  no adapter has trained and no pair has been selected, so a Complete there is flatly false in the
  one artifact a reader consults to see what is actually done. (STAT-04/05/06 were already Complete
  from Phase 16 and were unaffected.)
- **Fix:** `STAT-03` and `ISO-05` restored to `[ ]` / `Pending` in `REQUIREMENTS.md`; the plans that
  actually deliver them will mark them. **ISO-07 kept Complete** — 17-01 is its only claimant and
  `test_no_phase14_thresholds` enforces it across a glob that grows with every future Phase 17
  driver, so it is genuinely discharged here.
- **Files modified:** `.planning/REQUIREMENTS.md`

## Deliberate-RED Proofs (guards watched failing)

Every guard this plan ships was observed red before being trusted.

**Task 2, on a throwaway branch so `main` never moved** (`tmp-red-17-01`, deleted; working tree
clean afterwards, `scripts/phase17_personas.py` byte-identical to `d549e0b`):

| Step | Commit | Test | Result |
|---|---|---|---|
| dummy `results/phase17_probe.md` | `bd6b6e0` | 3 tests | **PASS** — the prereg precedes the artifact |
| touch `scripts/phase17_persona_facts.py` (the MATERIAL) | — | 3 tests | **STAYS GREEN** — the ADAPT branch survives |
| edit `scripts/phase17_personas.py` (the PRE-REGISTRATION) | `e020278` | | **FAIL** |

The failure names the non-ancestor pair directly:
`git merge-base --is-ancestor e020278594722430ea913ea6456c5debfee432cb bd6b6e0ebd495513f2aa9e1e43b838613d5c7bd4` returned 1.

The middle row is the one that justifies the two-file split: with the results artifact already
committed, editing the persona material leaves the guard green while editing the pre-registration
turns it red. That is exactly the discrimination ROADMAP SC2's ADAPT branch needs.

**Task 3** (working-tree probes, each reverted byte-identical, `git diff --quiet` confirmed):

- `test_no_new_dependencies` — top-level `import pandas` added:
  `AssertionError: phase17_personas.py imports 'pandas', which is neither stdlib nor part of this repository.`
- `test_replication_is_not_gated` — throwaway function passing a local `replication_p` into a stub
  `holm(...)`:
  `AssertionError: phase17_personas.py:_red_probe_throwaway passes ['replication_p'] into holm`

## Verification

| Check | Result |
|---|---|
| `pytest -q tests/test_phase17_stats.py -x` | **10 passed** (>= 8 required) |
| `pytest -q tests/test_phase16_prereg.py -x` | **3 passed** |
| `pytest -q` (full suite) | **590 passed, 1 skipped** in 124.02s (baseline 579/1 + 11 new) |
| `.venv/bin/ruff check` + `format --check` on both files | clean |
| `git diff HEAD~3 -- pyproject.toml` | empty (STAT-04) |
| `grep -c "seis pares" tests/test_phase17_stats.py` | 0 |
| `grep -n "import torch" tests/test_phase17_stats.py` | nothing |
| `grep -n "0.2486\|0.2000" scripts/phase17_personas.py` | nothing (ISO-07) |
| `grep -c "PERSONA_FACTS\|VALUE_TOKEN_CENSUS" scripts/phase17_personas.py` | 0 |
| `git diff HEAD~1 -- tests/test_phase16_prereg.py \| grep -c "^-"` | 1 (the diff header only) |
| `grep -c "is-shallow-repository" tests/test_phase16_prereg.py` | 2 |
| `make lint` | **red — pre-existing**, see below |

`test_replication_is_not_gated` passes with `REPLICATION_SEEDS` present as a module-level
assignment in the scanned file, which is the point: the scan is call-site-scoped, exactly as
`tests/test_phase16_stats.py:806-823` is.

## Deferred Issues

`make lint` fails on this machine and did so **before this plan started**. `Makefile:16` runs bare
`ruff`, which resolves here to a pyenv shim holding **ruff 0.1.15** (Jan 2024); the project pins
`ruff~=0.15` and `.venv/bin/ruff` is **0.15.16**. The stale formatter wants to reformat 8 files, and
**7 are untouched by this plan** (`test_gpt_lora_seam`, `test_phase14_demo`, `test_phase15_docs`,
`test_phase15_plots`, `test_phase16_driver`, `test_phase16_fixture_regen`, `test_phase16_ladder`).

CI is unaffected: `.github/workflows/ci.yml:36-38` installs `.[cpu,dev,demo]` and then runs `ruff`
from PATH, which is the freshly installed 0.15.x. `.venv/bin/ruff format --check` — the version this
plan's acceptance criteria name, and the version CI actually uses — is clean on every file written
here. Logged as **DEF-17-01** in `deferred-items.md`; it intersects the already-recorded DEF-15-01
(`python -m ruff` is the correct Makefile fix, not `.venv/bin/ruff`, because CI has no `.venv`).

## Known Stubs

None. Every constant and function this plan commits is complete and exercised by a test. The
Phase 17 artifact set that `test_phase17_prereg_is_frozen_before_every_phase17_result` scans is
legitimately **empty** until plan 17-07 commits `results/phase17_personas_report.md`, so that test
is a **stated vacuous pass in Waves 1-3** — recorded in its own docstring, with plans 17-07 and
17-09 each carrying an acceptance criterion requiring `checked > 0`. That is a planned property of
the wave ordering, not a stub.

## Handover Notes

1. **Plan 17-03 must put the 24 values in `scripts/phase17_persona_facts.py`, never in
   `scripts/phase17_personas.py`.** Moving them into the pinned file re-arms a trap with no
   recovery short of history surgery: `--diff-filter=A` returns the earliest add, so once
   `results/phase17_personas_report.md` exists, any later edit to the pinned file is permanently
   red. Both the driver docstring and the guard docstring say so.
2. **Plans 17-07 and 17-09 must assert `checked > 0`** in
   `test_phase17_prereg_is_frozen_before_every_phase17_result`, or the guard stays vacuous forever.
3. **Do not widen the identifier ban** in `test_phase17_stats.py` to module-level assignment
   targets. `REPLICATION_SEEDS` is such a target in the scanned file and is mandated by this plan;
   the widened form fails on first run. The docstring records this.
4. `assert_family_length_matches_phase16` takes the length as a **parameter**. Callers pass
   `len(phase16_persistence.HOLM_FAMILY_PAIRS)`; the module imports no sibling driver to get it.
5. `filter_roundtrip` is duck-typed on `.vocab` / `.special_tokens` exactly as
   `undecodable_ids_mask` is, so it needs no torch and no loaded model — only a tokenizer.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema change at a trust boundary.
`TH-17-01` (repudiation) and `TH-17-02` (rationale tampering) are both mitigated as planned;
`TH-17-03` is mitigated by `assert_family_length_matches_phase16` plus its test; `TH-17-SC` holds —
zero packages installed, `pyproject.toml` byte-identical across all three commits.

## Self-Check: PASSED

Files:

- FOUND: `scripts/phase17_personas.py` (461 lines)
- FOUND: `tests/test_phase17_stats.py` (380 lines)
- FOUND: `tests/test_phase16_prereg.py` (204 lines, was 127)
- FOUND: `.planning/phases/17-multi-persona-isolation-matrix/deferred-items.md`

Commits:

- FOUND: `d549e0b` feat(17-01): commit the Phase 17 pre-registration block and minting filters
- FOUND: `7c269f5` test(17-01): pin the Phase 17 pre-registration ordering from git history
- FOUND: `c9dcbba` test(17-01): pin the Phase 17 gate rule, tie-break and four static scans
