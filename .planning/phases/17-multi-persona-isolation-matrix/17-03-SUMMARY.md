---
phase: 17-multi-persona-isolation-matrix
plan: 03
subsystem: persona-material
tags: [iso-01, d-04, d-05, d-06, minting-filters, tokenizer-census, two-file-split]
requires:
  - scripts/phase14_factset.py (Fact, the three pools, LOCKED_FACTS, SOFT_TIER_FACTS,
    GATE_REJECTED_CANDIDATES, BASE_PRIOR_SEEDS — imported at module scope, never redefined)
  - scripts/phase17_personas.py (PERSONAS, CORE_SLOTS, SLOTS_EXPECTED, QUESTIONS_PER_SLOT,
    MAX_VALUE_TOKENS and the four minting filters — imported LAZILY)
  - artifacts/tokenizer.json (the FROZEN production tokenizer the census was measured against)
  - results/phase16_recall_sample.json (the 104 core_held_out questions filter 4 runs over)
  - scripts/phase14_recall.py (derive_recall_budget / normalize / contains_value)
provides:
  - scripts/phase17_persona_facts.py (the Phase 17 MATERIAL — 24 Fact literals)
  - PERSONA_FACTS / FORBIDDEN_VALUES / VALUE_TOKEN_CENSUS / all_facts
  - assert_material_passes_filters(tok, questions) — the ONE pre-flight entry point
  - tests/test_phase17_personas.py (12 CPU-only tests)
affects:
  - plan 17-04 (regroups the fixture by slot; checked against CORE_SLOTS, not against this material)
  - plan 17-05 (teaches the three adapters from PERSONA_FACTS; calls
    assert_material_passes_filters in its pre-flight and owns the GPU guessability half)
  - plan 17-07 (ROADMAP SC2's GO/ADAPT verdict; the ADAPT branch edits THIS file, never the
    pre-registration)
tech-stack:
  added: []
  patterns:
    - material and pre-registration in TWO files, so a git-ancestry pin and a mutable artifact
      can coexist
    - forbidden sets DERIVED by walking committed containers, never hand-typed
    - measured census transcribed as a literal and never recomputed at import
    - one entry point with its composition proved before its content
    - guards watched failing before being trusted
key-files:
  created:
    - scripts/phase17_persona_facts.py
    - tests/test_phase17_personas.py
  modified: []
decisions:
  - the 24 values land in a NEW file; scripts/phase17_personas.py is byte-untouched
  - D-05 is NOT one of the four mechanical filters and cannot be — it needed its own measured test
  - phase17_personas is imported lazily because it measurably drags torch in; phase14_factset does not
  - ISO-01 stays Pending — the guessability half and SC2's human verdict belong to 17-05 / 17-07
metrics:
  duration: 19min
  tasks: 2
  files: 2
  completed: 2026-08-14
---

# Phase 17 Plan 03: Persona Material Summary

Three personas now carry contradictory values in **all eight** core slots as committed `Fact`
literals — 24 freshly minted values, each measured against the frozen tokenizer, each proved
disjoint from every committed Phase 14 pool and from the 104 fixture questions — and they live in a
file the pre-registration's git-ancestry guard deliberately does not pin.

## What Was Built

### Task 1 — `scripts/phase17_persona_facts.py` (commit `b599420`)

`PERSONA_FACTS`: 3 personas x 8 `CORE_SLOTS`, one `Fact(id, slot, value, tier)` per cell, all
`tier="core"`. Ids are `p17_{letter}_{slot}` — deliberately NOT Phase 14's `cand_person_quillon`
shape, which embeds its own value.

| slot | persona_a | persona_b | persona_c |
|---|---|---|---|
| person_name | thessaly | drovik | kessendra |
| pet_name | nyxen | fenmark | grindlow |
| cat_name | quorra | vellamo | ostrick |
| sibling_name | myrrhen | orlenne | vorwick |
| hometown | brambleton | hollowmere | duskvale |
| street | sablewind | wexford | crandwell |
| birth_year | 1906 | 1941 | 1893 |
| house_number | 5063 | 2287 | 9614 |

`FORBIDDEN_VALUES` (43 values) is **derived**, never typed: six committed Phase 14 containers
(`CANDIDATE_POOL`, `CALIBRATION_POOL`, `REGISTER_ARM_POOL`, `LOCKED_FACTS`, `SOFT_TIER_FACTS`,
`GATE_REJECTED_CANDIDATES`) plus `BASE_PRIOR_SEEDS`' values, so D-06's zero-reuse holds by
construction rather than by inspection. The three subsets are still walked separately because D-06
names them independently and a test asserts a known member of each is present — a broken pool walk
cannot make the disjointness trivially true.

`VALUE_TOKEN_CENSUS` is the measured count per fact id, transcribed as a literal in
`phase14_factset.py:448-482`'s register. Max is **8** (`p17_a_hometown` = `brambleton`), exactly
Phase 14's own census max, so `derive_recall_budget` lands on the published **48** unchanged.

`assert_material_passes_filters(tok, questions)` is the one entry point 17-05's pre-flight will
call. It runs two composition proofs **before** the four filters, because a filter cannot see
material that is not there: `filter_token_budget` over a census missing an id passes on the entries
it has, and `filter_roundtrip` over a persona missing a slot passes on the values it was handed.

### Task 2 — `tests/test_phase17_personas.py` (commit `991fde0`)

12 tests, CPU-only, no torch import in the file, no checkpoint I/O, **0.79 s**. It carries the
`tests/test_phase14_factset.py:8-18` note in spirit: the guessability half of the ISO-01 pre-flight
is checkpoint-specific and structurally cannot live here, so a future checkpoint inheriting a green
run of this file has inherited **nothing** about guessability.

## The Minting Loop — What Each Filter Actually Rejected

Recorded the way Phase 16 recorded that its guessability gate cleared all 43 ladder candidates and
rejected none: a filter that bit nothing is worth stating as such.

**34 candidate strings were measured against the frozen tokenizer** (RESEARCH F-05's 24, plus 7
extra street candidates, plus 3 replacement years). Two more (`1926`, `1978`) were discarded on the
D-05 arithmetic before measurement and are not counted.

| Screen | Rejected | Which |
|---|---|---|
| `filter_token_budget` (<= 8 ids) | **2 of 34** | `vurthwaite` (10 ids), `thornebank` (9 ids) |
| `filter_roundtrip` | **0** | 34/34 round-tripped exact, 0 dead ids — F-05's measured no-op held |
| `filter_substring_disjoint` | **0** | no nesting in minted ∪ forbidden under `normalize` |
| `filter_absent_from_questions` | **0** | no candidate appears in any of the 104 questions |
| D-05 neighbour screen (**not** one of the four) | **2** | `tarrowgate`, `1971` |

**On the 24 committed values, all four filters reject nothing.** The two token-budget rejections
happened during authoring, on candidates that were never committed.

The D-05 line is the finding worth carrying forward — see the deviation below.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] The four mechanical filters structurally cannot see D-05**

- **Found during:** Task 1, authoring the `street` slot.
- **Issue:** `tarrowgate` was authored, and it passes **all four** filters — 8 ids, round-trips
  exact, absent from every fixture question, and substring-disjoint, because neither `tarrowgate`
  nor Phase 14's locked `marrowgate` contains the other. It is at **edit distance 1** from that
  locked value. D-05 ("values are surface-arbitrary, not token-level neighbours") is named in the
  plan's own value discipline but has no filter behind it, and the failure it prevents is real: a
  near-twin value turns an off-diagonal cell into a tokenization-robustness probe, which is exactly
  the research question 17-CONTEXT D-05 puts out of scope.
- **Fix:** the neighbour screen was applied by **measurement** during authoring (`tarrowgate` and
  `1971` rejected), and pinned as a committed test, `test_values_are_not_token_level_neighbours`.
  Two bars, because the two slot kinds are structurally different: the 18 invented proper nouns
  clear edit distance **>= 3** against every other minted and forbidden value (minimum measured: 3,
  `fenmark` vs `fenwyck`); the 6 four-digit numerics can only clear **>= 2** (minimum measured: 2,
  `1893` vs `1953`), since length is fixed at 4 over a 10-symbol alphabet, so distance 2 already
  means half the string differs. The test carries `tarrowgate`/`marrowgate` as its own witness, so
  the rejected candidate stays in the record rather than vanishing with the draft.
- **Why not a fifth filter in the module:** a new filter belongs in the pre-registration, and that
  file is git-ancestry-pinned. Adding one now would be a pre-registration edit for a rule 17-01 did
  not register. The screen lives in the test, where it pins the material without touching the pin.
- **Files modified:** `tests/test_phase17_personas.py`
- **Commit:** `991fde0`

**2. [Rule 3 - Blocking] `phase17_personas` imports torch; `phase14_factset` does not**

- **Found during:** Task 1, deciding the import scope of the two siblings.
- **Issue:** the plan's `<interfaces>` says this module imports both siblings and mandates
  module-scope for `Fact` (a module-level literal cannot be built from a lazy import). Measured:
  `import phase17_personas` puts **torch in `sys.modules`** — it imports `phase16_persistence`,
  which imports `phase14_recall`. `import phase14_factset` does not.
- **Fix:** asymmetric by measurement, with the measurement recorded in the docstring.
  `phase14_factset` is imported at module scope (mandated, and free); `phase17_personas` is
  imported lazily inside `assert_material_passes_filters`, which is the same LAZY-IMPORT RULE the
  pre-registration applies to `phase14_recall`. A CPU-only consumer can now read the material with
  no torch in the process — asserted by the plan's own verify command, which loads the module and
  reports `torch at import: False`.
- **Files modified:** `scripts/phase17_persona_facts.py`
- **Commit:** `b599420`

**3. [Rule 1 - Bug] `requirements mark-complete` would over-claim ISO-01**

- **Found during:** state updates.
- **Issue:** the plan's frontmatter lists `requirements: [ISO-01]`, and `requirements
  mark-complete` checks every id it is handed — but **17-05 and 17-07 also claim ISO-01**, and the
  first plan to name a requirement marks it Complete for the whole phase. ISO-01 as written in
  17-CONTEXT D-06 requires each of the 24 to pass `probe_guessability` against the real checkpoint
  **plus a blocking human GO/ADAPT verdict (SC2)**. Neither has happened; this plan's own objective
  says so ("The GPU guessability half is 17-05/17-07"). A Complete there would be false in the one
  artifact a reader consults to see what is done.
- **Fix:** `requirements mark-complete` was **not run**. ISO-01 stays `[ ]` / `Pending`; 17-07, the
  plan that carries the human verdict, marks it. This is 17-01's recorded over-claim pattern,
  avoided rather than repeated.
- **Files modified:** none (the fix is an omission)

### Interpretation recorded

`test_census_fits_the_recall_budget` derives the budget through the **real**
`phase14_recall.derive_recall_budget` and asserts it equals `RECALL_MAX_NEW_TOKENS == 48`, rather
than re-typing `max + 32 + 8` locally. A hand-copied formula in a test is a second copy of the rule
the budget is actually computed from, free to stop agreeing with it. The plan's `max(census) <=
MAX_VALUE_TOKENS` assertion is kept as the first line of the same test.

`test_material_passes_all_four_filters` was added beside the plan's ten so the single entry point
17-05 will call has a positive control of its own; the substring filter keeps its own
positive-plus-negative test exactly as the plan specifies. 12 tests, against the plan's floor of 10.

Persona slot sets are checked against `phase17_personas.CORE_SLOTS` — the one canonical list — and
never against each other, per 17-01's handover. `Fact.tier` is asserted against the literal
`"core"`: it is the fact set's own core/soft axis (`phase14_factset.py:57`), a **different** axis
from `phase17_personas.GATED_TIER`, which is `"held-out"`. The first draft derived one from the
other by string surgery and went red immediately — the two vocabularies were never the same thing.

## Deliberate-RED Proofs (guards watched failing)

| Guard | Mutation | Observed |
|---|---|---|
| `test_token_census_matches_locked_literals` | `"p17_a_pet_name": 3` -> `4` | **FAIL**, `AssertionError: p17_a_pet_name` / `assert 3 == 4` / `3 = len([283, 120, 280])` |
| `filter_substring_disjoint` (minted-in-minted) | inject `_VALUES[0][:4]` | `SystemExit` naming the outer value — committed as the test's negative control |
| `filter_substring_disjoint` (minted-in-Phase-14) | inject `"quillo"` | `SystemExit` naming `quillon` — committed |
| `filter_absent_from_questions` | pass a word taken from a fixture question | `SystemExit` — committed |

The census mutation was made in the working tree and reverted; `git diff HEAD --
scripts/phase17_persona_facts.py` is empty, so the file is byte-identical to `b599420`.

## Verification

| Check | Result |
|---|---|
| `pytest -q tests/test_phase17_personas.py -x` | **12 passed** in 0.79s (>= 10 required, < 5s required) |
| `pytest -q tests/test_phase17_stats.py -x` | **10 passed** — the new module entered the `phase17_*.py` glob and cleared ISO-07 / STAT-04 / STAT-06 on arrival |
| `pytest -q tests/test_phase16_prereg.py` | **3 passed** — the ordering guard is unaffected |
| `pytest -q` (full suite) | **609 passed, 1 skipped** in 122.67s (baseline 597/1 + 12 new) |
| plan's Task 1 `python -c` verify | `24 values, 8 slots x 3 personas, census clean` |
| `assert_material_passes_filters(tok, questions)` | all four filters passed over 24 values; `torch at import: False` |
| `.venv/bin/ruff check` + `format --check` on both files | clean |
| `git diff HEAD~2 -- pyproject.toml results/ scripts/phase17_personas.py` | **empty** — the pinned pre-registration is byte-untouched (TH-17-40) |
| `grep -n "import torch" tests/test_phase17_personas.py` | nothing |
| `--durations=3` | slowest call 0.05s (`test_substring_disjointness_bites`) |
| `make lint` | **red — pre-existing**, see below |

## Deferred Issues

`make lint` still fails from **DEF-17-01** (recorded in this phase's `deferred-items.md` during
17-01, and pre-existing to it): `Makefile:16` runs bare `ruff`, which resolves on this box to a
pyenv shim holding **ruff 0.1.15** against the project's `ruff~=0.15` pin. It reports the **same 8
files** as at 17-01 close, and **neither file this plan wrote is among them** — the stale formatter
is happy with both. `.venv/bin/ruff` (0.15.16, the version CI installs and runs) is clean on both.
Not this plan's to fix; the recorded resolution is a quick task changing `Makefile:16` to
`python -m ruff`.

## Known Stubs

None. Every constant, function and test this plan commits is complete and exercised.

The ISO-01 requirement is **intentionally not discharged here** and that is a planned property of
the wave ordering, not a stub: the guessability measurement needs `convbase_best.pt` on MPS and
cannot enter a CPU-only suite, and SC2's GO/ADAPT verdict is a blocking human decision. 17-05 runs
the measurement; 17-07 records the verdict and marks the requirement.

## Handover Notes

1. **17-07's ADAPT branch edits `scripts/phase17_persona_facts.py`, never
   `scripts/phase17_personas.py`.** `test_material_is_not_in_the_pinned_prereg_file` now fails with
   that reason attached if the two files are ever merged. When ADAPT replaces a value it must also
   update `VALUE_TOKEN_CENSUS` for that id in the **same commit** — the census is the expectation,
   not a derived number, so an edited value with a stale count turns
   `test_token_census_matches_locked_literals` red (proved above) — and re-run the D-05 neighbour
   screen, which no filter performs for it.
2. **17-05 should call `assert_material_passes_filters(tok, questions)`**, not the four filters
   individually. It proves the composition (personas, slots, census key set) before the content;
   four separate call sites can drift into checking different subsets of the same rule.
3. `assert_material_passes_filters` takes `tok` and `questions` as parameters and loads neither.
   Pass the **frozen** `artifacts/tokenizer.json` and the 104 `core_held_out` questions from
   `results/phase16_recall_sample.json`, in that tier — nothing else.
4. `PERSONA_FACTS` keys are the `PERSONAS` labels and the ids embed the persona **letter**
   (`p17_a_...`). Any driver mapping one to the other should use `PERSONA_FACTS`, not string
   surgery on the id.
5. The census max is **8**, sitting exactly on `MAX_VALUE_TOKENS`. There is **zero headroom**: any
   replacement value at 9 ids moves the derived budget from 48 to 56 and breaks parity with every
   published Phase 14 and Phase 16 number. `test_census_fits_the_recall_budget` catches it through
   the real `derive_recall_budget`.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema change at a trust boundary.
`TH-17-07` is mitigated (substring disjointness across minted ∪ forbidden, watched failing twice);
`TH-17-08` holds (all 24 invented, `FORBIDDEN_VALUES` derived so no real-world identifier can enter
by reuse); `TH-17-09` is mitigated (`filter_token_budget` plus the budget-parity test);
`TH-17-40` is mitigated (material outside the pinned file, and the split itself pinned);
`TH-17-SC` holds — zero packages installed, `pyproject.toml` byte-identical across both commits.

## Self-Check: PASSED

Files:

- FOUND: `scripts/phase17_persona_facts.py` (252 lines)
- FOUND: `tests/test_phase17_personas.py` (351 lines)

Commits:

- FOUND: `b599420` feat(17-03): mint the 24 persona values with their measured token census
- FOUND: `991fde0` test(17-03): pin the minted material's census, collisions and four filters
