---
phase: 17-multi-persona-isolation-matrix
plan: 04
subsystem: isolation-scoring-core
tags: [iso-02, iso-03, sc3, stat-01, stat-06, d-02, d-12, d-13, d-17, roadmap-sc1]
requires:
  - scripts/phase17_personas.py (PERSONAS, BASE_ROW, CORE_SLOTS, SLOTS_EXPECTED,
    QUESTIONS_PER_SLOT, SIGN_UNIT — imported at module scope, never retyped)
  - scripts/phase16_persistence.py (load_fixture_items — seed_index read VERBATIM)
  - scripts/phase14_recall.py (normalize / contains_value / find_contradictions — imported
    LAZILY inside function bodies)
  - results/phase16_recall_sample.json (the binding fixture; read, never regenerated)
provides:
  - scripts/phase17_isolation.py (the Phase 17 driver — pure-CPU scoring core)
  - held_out_by_slot / score_completion / classify / base_texts_by_slot / assemble_matrix
  - SWEEP_QUESTIONS_KEY / SWEEP_LABEL_KEY / CATEGORIES (the sweep-record contract)
  - tests/test_phase17_scoring.py (11 CPU-only tests)
affects:
  - plan 17-06 (extends THIS file additively — the ISO-04 canary, values_by_slot, --sweep/--train,
    main() under a __main__ guard; must write records under SWEEP_QUESTIONS_KEY / SWEEP_LABEL_KEY)
  - plan 17-08 (run_report_mode consumes assemble_matrix's 12 cells and its per_slot shape)
  - plan 17-11 (the ISO-05 replication reuses the same scoring core)
  - ROADMAP SC1 (its second 2026-08-14 amendment is discharged by measurement)
tech-stack:
  added: []
  patterns:
    - generation and scoring as two separate passes, so cell-blindness is STRUCTURAL
    - the scored driver takes values_by_slot as a PARAMETER, so its tests run on synthetic values
    - the record contract as module constants, not one string retyped in three files
    - guards mutation-proved — watched failing before being trusted
key-files:
  created:
    - scripts/phase17_isolation.py
    - tests/test_phase17_scoring.py
  modified:
    - .planning/ROADMAP.md (SC1 third amendment — the CONFIRMED no-op-swap shape)
    - .planning/phases/17-multi-persona-isolation-matrix/deferred-items.md (DEF-17-01 count 8 -> 9)
decisions:
  - the four category counts are a ROW property reported on each of that row's three cells,
    because classify takes no j by design (D-12); the per-column number is n_answerable
  - base_texts_by_slot checks its slot set against CORE_SLOTS rather than re-reading the fixture —
    the same third-party discipline, without a second disk read
  - a question's category is max-over-draws on classify's OWN ordering, the same rule as
    n_answerable, rather than a new reduction ordering invented at assembly
metrics:
  duration: 18min
  tasks: 3
  files: 4
  completed: 2026-08-14
---

# Phase 17 Plan 04: Isolation Scoring Core Summary

A completion can now be scored against three personas' values with no route for the scoring path to
learn which adapter produced it, the 104 held-out questions regroup to the measured 8x13 slot shape
with `seed_index` untouched, the base row is a computed row of the same matrix under the same rate
definition, and the shape a silently no-opped adapter swap produces is a **measured fact recorded in
ROADMAP** rather than an argument.

## What Was Built

### Task 1 — the driver skeleton, the slot regrouping, the cell-blind scorer (commit `6c60f84`)

`scripts/phase17_isolation.py`. Nothing executes at import except the `sys.path` bootstrap — the
claim is pinned by a committed test, not left to the docstring that makes it.

| Name | Shape | Why this shape |
|---|---|---|
| `held_out_by_slot()` | `{slot: (RecallItem, ...)}` | D-02 keys on SLOT because every Phase 14 `fact_id` embeds Phase 14's own value; `seed_index` is never re-enumerated, so a fixture mismatch surfaces instead of being repaired |
| `score_completion(completion, slot_values)` | `frozenset` of persona labels | the ONLY function that touches a completion, and it takes no cell (SC3). Empty is D-12's `none`; a double match is a two-member frozenset (D-17), never a priority winner |
| `SWEEP_QUESTIONS_KEY` / `SWEEP_LABEL_KEY` | constants | 17-06 writes these records and 17-08 reads them; three files spelling one string is three places it can stop agreeing, and the failure is a `KeyError` after the GPU sweeps are already spent |
| `CATEGORIES` | tuple of the four | a mistyped bucket key drops the count it meant to increment, and a category reading zero because nothing wrote to it is indistinguishable in the report from one that never occurred |

Both `_prove`s in `held_out_by_slot` name the decision AND the consequence: the 8x13 balance carries
D-08's n and every per-slot denominator, and the slot set is checked against `CORE_SLOTS` — the one
canonical list — never against the minted material. That independence is what makes every test below
run on synthetic values, which is the structural half of SC3.

### Task 2 — the four-category assembly and the matrix builder (commit `3693a8d`)

`classify(labels, own, base_texts, completion)` — the only code that knows the cell, in the order the
plan pre-registers. Branch 2 (`own is None and labels` -> `base_prior`) is the load-bearing one and
its docstring says why: `base_texts` is a membership test on the WHOLE completion string, so it
cannot separate "the base produced something containing persona j's value" from "the base produced
something else". Without branch 2 the base row falls through to `leak` — the base leaking to itself,
from an adapter that does not exist — and cell `(base, j)` never gets a rate.

`base_texts_by_slot(base_record)` proves the record's `sweep` is `BASE_ROW` and its slot set is
complete, because an empty base-prior set silently converts every base prior into a confabulation
while leaving every cell rate unchanged.

`assemble_matrix(sweep_records, values_by_slot, base_texts)` takes **all four records** and returns
12 cells — the 3x3 adapter block plus `(base, j)` for each `j`, under one rate definition
(RESEARCH:900). Per cell: `per_slot` (`{slot: ((k, n), ...)}`, exactly `cluster_bootstrap`'s input
with the slot as the cluster), `n_answerable`, `n_questions`, `rate`, `contradiction_draws` and the
four category counts.

**STAT-01 (RESEARCH F-11) lives here.** `fact_signs` reads `["rate"]` off whatever dict it is handed
and `aggregate_by_fact`'s `rate` is the DRAW rate; this function builds the QUESTION rate and proves
it against the committed `SIGN_UNIT` literal. No Phase 16 function was widened and
`aggregate_by_fact` is not called — the 17-PATTERNS ladder verdict on F-09 held.

### Task 3 — `tests/test_phase17_scoring.py` (commit `cb75aad`)

11 tests, CPU-only, no torch import in the file, driver loaded via `importlib`, **0.9 s**.
`test_scorer_is_cell_blind` works in three layers — signature, public name, and a body AST scan for
`{i, j, cell, own, diagonal}` including any `ast.Compare` over them — and asserts the function was
FOUND in the AST before asserting anything about its contents, so a rename cannot make the scan
green by finding nothing.

## ROADMAP SC1 — the no-op-swap shape, CONFIRMED

`test_no_op_swap_produces_the_recorded_shape` builds three "adapter" sweeps all carrying persona A's
values (the artefact of a swap that silently no-ops and leaves one adapter resident) plus a
well-formed base record, runs the real `assemble_matrix`, and asserts what came out. Nothing was
hard-coded before it ran.

**Measured shape — column collapse:**

|  | persona_a | persona_b | persona_c |
|---|---|---|---|
| **persona_a** | 1.0000 | 0.0000 | 0.0000 |
| **persona_b** | 1.0000 | 0.0000 | 0.0000 |
| **persona_c** | 1.0000 | 0.0000 | 0.0000 |
| **base** | 0.0000 | 0.0000 | 0.0000 |

In one sentence: **the resident adapter's column reads 1.0 in all three adapter rows, every other
adapter cell reads 0.0, the diagonal reads (1.0, 0.0, 0.0) so two of the three diagonal cells fall
with the columns rather than the diagonal being perfected, and the base row is unaffected at 0.0.**

**The pre-registered gate would NOT clear on it.** Run through the committed instruments rather than
argued from the shape: only the two row-A comparisons reject (p = 0.0078125 each, 8/8 unanimity);
row B and row C give p = 1.0 — their diagonals lose every slot to the A column, and the B-vs-C
contrast is 8 ties. 2 of 6 rejections, so `gate_cleared` is `False` under D-18's all-six rule.

`.planning/ROADMAP.md` Phase 17 SC1 carries this as a dated third amendment citing the test by name;
the MEDIUM-confidence paragraph is left in place and marked superseded, never deleted. The row
taxonomy is equally unambiguous: row A scores 104 `diagonal`, rows B and C score 104 `leak` each.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] The module-level-call acceptance command is vacuous here too**

- **Found during:** Task 1 acceptance criteria.
- **Issue:** the plan's `ast` command scans `tree.body` for an `ast.Expr` wrapping an `ast.Call`.
  This driver's `sys.path` bootstrap is nested inside an `if`, so it lives in `tree.body[i].body`.
  The command finds **0** calls and `all([])` is `True` — green while checking nothing. This is
  17-01's recorded deviation #1 arriving verbatim in a second plan, because the plan carried the
  command forward with the `isinstance(n, ast.Call)` trap closed but the `if`-nesting one open.
- **Fix:** ran the plan's command as written (passes, 0 calls) **and** a module-SCOPE walk excluding
  function and class bodies, which finds exactly 1 call and confirms it is
  `sys.path.insert(0, str(_REPO_ROOT / 'scripts'))`. Promoted the stronger form to a committed test,
  `test_phase17_scoring.py::test_nothing_executes_at_import`. `test_phase17_stats.py`'s twin is
  scoped to `_PERSONAS_PATH` only, so without this the isolation driver was unscanned — and 17-06
  adds a `main()` to this file that loads a model.
- **Files modified:** `tests/test_phase17_scoring.py`
- **Commit:** `cb75aad`

**2. [Rule 2 - Missing critical functionality] `values_by_slot` had no shape proof**

- **Found during:** Task 2.
- **Issue:** the plan specifies `values_by_slot` as a parameter and never says what happens when it
  is short. A missing slot is a `KeyError` mid-assembly; a missing persona in one slot's mapping is
  worse — it drops that column's contribution for that slot while the denominator still counts all
  104 questions, so the cell publishes a rate computed over fewer slots than it claims.
- **Fix:** `assemble_matrix` `_prove`s `set(values_by_slot) == set(CORE_SLOTS)` and that every slot
  carries all three `PERSONAS`, before any scoring runs. Same register as the four-record proof.
- **Files modified:** `scripts/phase17_isolation.py`
- **Commit:** `3693a8d`

**3. [Rule 1 - Bug] The plan's `PERSONA_FACTS` criterion contradicted its own docstring mandate**

- **Found during:** Task 1 acceptance criteria.
- **Issue:** the action mandates recording, in `held_out_by_slot`'s docstring, that the slot set is
  checked against `CORE_SLOTS` and NOT against the minted material — and the acceptance criterion is
  `grep -c "PERSONA_FACTS" ... returns 0`. The first draft returned 1, on a docstring sentence
  saying that constant is *not* consulted. 17-01 hit the identical shape.
- **Fix:** the docstring records the same reasoning in words ("the 24 minted values in
  `scripts/phase17_persona_facts.py`") and states explicitly why the identifier is not written out.
  Intent satisfied strictly; the warning survives intact.
- **Files modified:** `scripts/phase17_isolation.py`
- **Commit:** `6c60f84`

**4. [Rule 1 - Bug] `requirements mark-complete` would over-claim ISO-02 and ISO-03**

- **Found during:** state updates.
- **Issue:** the plan's frontmatter lists `[ISO-02, ISO-03]` and `requirements mark-complete` checks
  every id it is handed — but **17-06 and 17-09 also claim both, and 17-08 also claims ISO-03**, and
  the first plan to name a requirement marks it Complete for the whole phase. ISO-02 as written
  reads "the isolation **matrix** scores shared-slot questions against every persona's value" and
  ISO-03 "the **matrix** carries an explicit adapter-off control column". No adapter has trained, no
  sweep has run and no matrix exists — this plan ships the machinery that will produce both. A
  Complete there would be flatly false in the one artifact a reader consults to see what is done.
- **Fix:** `requirements mark-complete` was **not run**. ISO-02 and ISO-03 stay `[ ]` / `Pending`;
  17-09 runs the sweeps and 17-08 publishes the matrix and the column. This is 17-01's recorded
  over-claim pattern and 17-03's avoidance of it, applied a third time rather than repeated.
- **Files modified:** none (the fix is an omission)

### Interpretation recorded

**The four category counts are a ROW property, reported on each of that row's three cells.**
`classify` takes no `j` by design (D-12, and the correction recorded under it), so
`diagonal`/`leak`/`base_prior`/`confabulation` partition the row's 104 questions by what the row's
own completions contained — they are identical across `(row, a)`, `(row, b)` and `(row, c)`. The
per-column number is `n_answerable`/`rate`. Both the function docstring and this line say so
explicitly because the misreading is a live repudiation surface: `matrix[(a, b)]["leak"]` is *not*
"how often B's value appeared under adapter A"; that quantity is `matrix[(a, b)]["n_answerable"]`.
Cell-scoping the counts was considered and rejected — `classify`'s branch 1 fires before branch 3,
so a cell-scoped `leak` would silently mean "j's value appeared AND the row's own did not", which is
a conditional quantity nobody declared.

**A question's category is max-over-draws on `classify`'s own ordering.** `classify` takes one
completion, but a question has 9 draws. Branches 1-3 depend only on `labels`, which is the
question-unit union and therefore fixed across draws; only branch 4 can vary. So the reduction is
"a question is a base prior if ANY draw coincided with the adapter-off column" — the same
max-over-draws rule `n_answerable` uses everywhere else in this milestone, rather than a new
priority ordering invented at assembly.

**`base_texts_by_slot` checks its slot set against `CORE_SLOTS`, not against a second fixture read.**
The plan says "equals the fixture's". `held_out_by_slot` already proves the fixture equals
`CORE_SLOTS`, so checking both against that one canonical list is the same guarantee without a
second disk read — and it is 17-01's own discipline: two things checked against a third cannot drift
into agreeing on a wrong answer.

**The contradiction lexicon is the slot's own three values.** `find_contradictions(completion,
values[j], lexicon)` records a draw as a contradiction event when it carries j's value AND a
competing one. Using the slot's three minted values as the lexicon introduces zero new editorial
judgment, which is the exact property that made Phase 14's `LOCKED_VALUES | GATE_REJECTED` lexicon
auditable. Reported as `contradiction_draws`, descriptive, never gated.

`_function_def` was copied from `tests/test_phase14_scoring.py` after all — 17-01 deferred it with
"copy it in 17-04 if that plan's AST criteria need it", and `test_scorer_is_cell_blind` needs it.

## Deliberate-RED Proofs (guards watched failing)

Both probes were made in the working tree against the committed driver and reverted; sha256 of
`scripts/phase17_isolation.py` is byte-identical before and after
(`1159fee9f4d170e92799a259a0ffde9cd0cd99e4697318cb5fa01335fc92b24d`).

| Guard | Mutation | Observed |
|---|---|---|
| `test_scorer_is_cell_blind` | `score_completion(completion, slot_values, i=None)` | **FAIL** — `AssertionError: score_completion takes ['completion', 'slot_values', 'i']` / `Left contains one more item: 'i'` |
| `test_base_row_classifies_as_prior_never_leak` | delete `classify`'s `own is None` branch | **FAIL** — `assert 'leak' == 'base_prior'` |
| `test_matrix_has_a_computed_base_row` | (same mutation) | **FAIL** — `SystemExit: the adapter-off row scored 0 diagonal and 4 leak questions, which is impossible by construction ... the base row is being counted as evidence AGAINST the adapters (ISO-03)` |
| `held_out_by_slot` D-08 proof | drop one `pet_name` item from the fixture | `SystemExit` naming D-08 and printing `('pet_name', 12)` |

The third row is the one worth keeping: removing branch 2 fails the classification test **and**
trips `assemble_matrix`'s own runtime `_prove`, so the B4 regression is caught at two independent
layers rather than only in a unit test that a future edit could delete.

## Verification

| Check | Result |
|---|---|
| `pytest -q tests/test_phase17_scoring.py -x` | **11 passed** in 0.91s (>= 8 required) |
| `pytest -q tests/test_phase17_scoring.py tests/test_phase17_stats.py -x` | **21 passed** |
| `pytest -q` (full suite) | **620 passed, 1 skipped** in 121.57s (baseline 609/1 + 11 new; floor 579/1) |
| Task 1 `python -c` verify | `scorer cell-blind, fixture 8x13` |
| Task 2 `python -c` verify | `base row scores base_prior, adapter row scores leak` |
| 12 cells, 8 slots x 13 `(k, n)` pairs, `rate == n_answerable / n_questions` | asserted per cell |
| `cluster_bootstrap(cell["per_slot"])` | runs on the returned shape (asserted by execution, not by matching a shape) |
| STAT-06 AST scan over the driver source | clean |
| `grep -nE "^import torch\|^from torch" scripts/phase17_isolation.py` | nothing |
| `grep -c "PERSONA_FACTS" scripts/phase17_isolation.py` | 0 |
| `grep -n "import torch" tests/test_phase17_scoring.py` | nothing |
| module-SCOPE call walk over the driver | exactly 1, the `sys.path` bootstrap |
| `.venv/bin/ruff check` + `format --check` on both files | clean |
| `make lint` | **red — pre-existing DEF-17-01**, see below |

## Deferred Issues

`make lint` still fails from **DEF-17-01** (recorded at 17-01, pre-existing to it). `Makefile:16`
runs bare `ruff`, which resolves on this box to a pyenv shim holding **ruff 0.1.15** against the
project's `ruff~=0.15` pin. The count moved **8 -> 9**: `tests/test_phase17_scoring.py` joined
`tests/test_phase17_stats.py` and the seven pre-existing files, entirely because 0.1.15 predates the
assert-message wrapping style ruff 0.9+ emits — the whole diff on this plan's file is
`assert cond, (\n "msg"\n)` versus `assert (\n cond\n), "msg"`. `.venv/bin/ruff` 0.15.16 — the
version `.github/workflows/ci.yml:36-38` installs and runs — is clean on both files this plan wrote,
and reformatting them to satisfy the stale shim would turn the CI-version check red. The count
growing with each new Phase 17 test file is expected until the `Makefile:16` fix lands; recorded in
`deferred-items.md`.

## Known Stubs

None. Every function this plan commits is complete and exercised by a test. `main()`, the ISO-04
canary and `values_by_slot` are absent by design, not stubbed: plan 17-06 owns them, and keeping
`values_by_slot` out is precisely what lets this plan's tests exercise the scorer on synthetic
values. There is no placeholder to replace — 17-06 adds functions, it does not fill anything in.

## Handover Notes

1. **17-06, 17-08 and 17-11 extend `scripts/phase17_isolation.py` additively.** Nothing in this
   plan's surface should need editing. `main()` lands under a `__main__` guard in 17-06;
   `test_nothing_executes_at_import` allows exactly one module-scope call and will catch a second.
2. **17-06's sweep payload must use `SWEEP_QUESTIONS_KEY` and `SWEEP_LABEL_KEY`**, not the literal
   strings. The per-question entry needs at minimum `slot` and `completions`; `seed_index`,
   `question`, `fact_id`, `prompt_ids` and `stopped` travel for provenance and are not read here.
3. **17-06's `values_by_slot()` is the ONLY lazy reader of the minted material this file gets.**
   Nothing in the scoring path may read it — `assemble_matrix` takes the mapping as a parameter, and
   that is the structural half of SC3. `grep -c "PERSONA_FACTS"` returning 1 after 17-06 is correct;
   returning 2 is a regression.
4. **17-08 must pass all four records to `assemble_matrix`.** It `_prove`s the contract itself and
   the message names ISO-03 and the empty base column, but the abort costs a report run. Build
   `per_cell` from `cell["per_slot"]` as `sum(k)/sum(n)` per slot — that is the question rate the
   sign test needs, and `SIGN_UNIT` is proved against it at assembly.
5. **The category counts are a ROW property.** When 17-08 renders §The Matrix, do not label
   `matrix[(i, j)]["leak"]` as a per-cell leak count. The per-cell leak number is `n_answerable`.
6. `held_out_by_slot()` reads the fixture through `phase16_persistence.load_fixture_items()`, which
   lazily imports `phase14_factset` — so calling it puts Phase 14's locked values in the process.
   That is the committed Phase 16 behaviour and is why the LAZY-IMPORT RULE keeps them out of this
   module's own string surface rather than out of the process entirely.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema change at a trust boundary.
`TH-17-10` is mitigated structurally plus the signature pin and the body AST scan; `TH-17-11` is
mitigated — the shape is confirmed here on synthetic records and the run-time guard is 17-06's
two-layer canary; `TH-17-12` is mitigated by `classify`'s ordering with the `own is None` branch,
`base_texts_by_slot`'s two `_prove`s and `assemble_matrix`'s own base-row assertion (watched failing
together); `TH-17-41` is mitigated by the four-record proof and the three computed `(base, j)` cells;
`TH-17-13` is mitigated — the STAT-06 identifier ban stays green against the new file and the AST
scan over the driver source finds no aggregate identifier; `TH-17-SC` holds — zero packages
installed, `pyproject.toml` byte-identical across all three commits.

## Self-Check: PASSED

Files:

- FOUND: `scripts/phase17_isolation.py` (404 lines)
- FOUND: `tests/test_phase17_scoring.py` (567 lines)
- FOUND: `.planning/ROADMAP.md` (SC1 third amendment)
- FOUND: `.planning/phases/17-multi-persona-isolation-matrix/deferred-items.md` (DEF-17-01 updated)

Commits:

- FOUND: `6c60f84` feat(17-04): add the cell-blind scorer and the D-02 slot regrouping
- FOUND: `3693a8d` feat(17-04): assemble the 12-cell matrix with a computed base row
- FOUND: `cb75aad` test(17-04): pin cell-blindness, the taxonomy and the base row; confirm SC1
