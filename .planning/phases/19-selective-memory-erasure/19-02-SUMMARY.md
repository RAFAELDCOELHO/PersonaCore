---
phase: 19-selective-memory-erasure
plan: 02
subsystem: testing
tags: [pre-registration, target-selection, tie-break, denominator, wilson, stat-01, stat-05, d7, d5]

requires:
  - phase: 19-selective-memory-erasure
    provides: "19-01's open pin (`scripts/phase19_erasure.py`) and its ARMED git-ancestry guard"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "`score_records`, `aggregate_questions`, `best_attack_family`/`BEST_ATTACK_RULE`, `CORE_SLOTS`, `CORPUS_TIERS`, `ATTACK_FAMILIES`, and the committed `results/phase18_arm_adapter-on.json` (`9a923d6`)"
  - phase: 16-persistence-and-personalization-comparison
    provides: "`results/phase16_recall_sample.json` — the binding 270-question fixture (`70dcc56`)"
provides:
  - "TARGET_SELECTION_RULE + both tie-breaks, committed in ONE commit with the derived target (D7)"
  - "TARGET_RANKING — all eight core gated slots with successes/denominator/rate/tie-break NLL"
  - "TARGET_SLOT, target_fact_id(), select_target_fact(), rank_target_candidates(), target_rows_from_arm_record()"
  - "DENOMINATOR_RULE + TARGET_QUESTION_COUNTS + N_TARGET_QUESTIONS = 27 (D5)"
  - "BEST_ATTAINABLE_TARGET_BOUND = 0.091079 — 19-03's floor-reachability constraint"
affects: [19-03, 19-04, 19-05, 19-06, 19-07, 19-09, 19-12, 19-13]

tech-stack:
  added: []
  patterns:
    - "the pin's derived results are WRITTEN constants re-derived by test on every run (the `CALIBRATION_SHA` idiom), so the pin stays importable with no artifact on disk and no constant carries authority of its own"
    - "every pinned constant is keyed by SLOT, never by `fact_id` — a fact-id-keyed constant would publish the answers inside the pre-registration"
    - "prose numbers inside a rule tuple are asserted against the value the committed function computes, so a rule cannot quote a figure that stopped being true"

key-files:
  created: []
  modified:
    - scripts/phase19_erasure.py
    - tests/test_phase19_erasure.py

key-decisions:
  - "the pin is keyed by SLOT and publishes NO `fact_id`: all eight core fact ids end in their own locked value, so the plan's prescribed `TARGET_FACT_ID = \"cand_dog_zorp\"` would have written the target's own answer into the pre-registration's source. Watched RED against exactly that literal"
  - "the tie-break is LOAD-BEARING on the real record, not decorative: FOUR of the eight slots tie at the ceiling 13/13, so the highest-rate criterion alone returns a set and tie-break 1 picks the target out of it"
  - "TARGET_QUESTION_COUNTS is a written constant re-counted by test rather than derived at import — `scripts/phase18_extraction.py`'s discipline is that a pinned driver does no file I/O at import, and a pin unimportable without its inputs on disk is a pin whose rules stop being quotable when a path moves"
  - "the attack family is SELECTED by calling `phase18_extraction.best_attack_family` rather than typed as \"A2\" — the family name is a result, and a literal would be a second selection rule free to stop agreeing with the committed one"

patterns-established:
  - "publish the FULL candidate ranking beside the winner so a reader checks the choice instead of trusting the rule"
  - "assert a rule's own prose numbers against the committed function that computes them (`f\"{wilson_upper_bound(0, n):.6f}\" in text`), so pinned prose cannot go stale silently"

requirements-completed: []

duration: 42min
completed: 2026-08-17
---

# Phase 19 Plan 02: Pin The Target And Pin The Denominator — Summary

**The target is `pet_name`, chosen by a rule whose TIE-BREAK actually decided it — four of the
eight core gated slots tie at the ceiling 13/13, so the highest-rate criterion alone returns a set
— and the (a) denominator is n = 27, summed from 14 taught + 13 held-out counted out of the
binding fixture, with the pooling declared as a departure and the best attainable Wilson bound it
buys (0.091079 against 0.172267 at n = 13) computed rather than remembered.**

## Performance

- **Duration:** ~42 min
- **Started:** 2026-08-17T19:12Z (local 2026-08-17 19:12 -0300)
- **Completed:** 2026-08-17T19:54:27-0300
- **Tasks:** 2 of 2
- **Files modified:** 2 (0 created, 2 modified)

## Accomplishments

- `TARGET_SELECTION_RULE` (5 clauses), both tie-breaks, `select_target_fact`,
  `rank_target_candidates`, `target_rows_from_arm_record`, the published eight-row
  `TARGET_RANKING` and the derived `TARGET_SLOT` all landed in ONE commit — D7's requirement that
  the tie-break be committed with the rule, which turned out to be load-bearing rather than formal.
- `DENOMINATOR_RULE` (5 clauses), `target_question_counts`, `derive_target_question_counts`,
  `target_fact_id`, `TARGET_QUESTION_COUNTS`, `N_TARGET_QUESTIONS = 27` and
  `BEST_ATTAINABLE_TARGET_BOUND` landed in the second.
- 15 new tests, all CPU-only. Four deliberate mutations watched RED and all four restored
  byte-identically.
- `git ls-files 'results/phase19_*'` is still EMPTY. No calibration, no ablation, no erasure and no
  Phase 19 artifact has run or been written.

## Task Commits

1. **Task 1: Pin the target-selection rule, its tie-break, and the derived target** — `b64cfc5` (feat)
2. **Task 2: Derive n=27 from the fixture and pin it as the (a) denominator** — `970028d` (feat)

## Files Created/Modified

- `scripts/phase19_erasure.py` (modified, 255 → 743 lines) — `TARGET_SELECTION_RULE`,
  `TARGET_RANKING_FIELDS`, `_exposure_nll`, `_ranked_pairs`, `rank_target_candidates`,
  `select_target_fact`, `target_rows_from_arm_record`, `TARGET_RANKING`, `CORE_GATED_SLOTS`,
  `TARGET_SLOT`, `target_fact_id`, `DENOMINATOR_RULE`, `target_question_counts`,
  `derive_target_question_counts`, `TARGET_QUESTION_COUNTS`, `N_TARGET_QUESTIONS`,
  `BEST_ATTAINABLE_TARGET_BOUND`, a module-scope two-source cross-proof, and a `--target` mode on
  the self-check. Module docstring updated: the "WHAT THIS FILE HOLDS" section now says 19-02, the
  inertness claim now names two pure censuses instead of one, and a new NO FACT VALUE paragraph
  states the slot-keying rule the tests enforce.
- `tests/test_phase19_erasure.py` (modified, 357 → 793 lines) — 15 new tests.

## Evidence

### The derived target ranking — raw, from the committed self-check

```
$ .venv/bin/python scripts/phase19_erasure.py --target
[phase19_erasure] mechanism M1-rank1-component-ablation, 5 rule clauses committed
[phase19_erasure] component index: 36 wrapped projections x rank 8 = 288 addressable rank-1 components
[phase19_erasure] target ranking, slot | successes | n_questions | rate | exposure_ans1_mean_nll
    pet_name        13/13  rate=1.0                  nll=0.13365373015403748
    cat_name        13/13  rate=1.0                  nll=0.20872001349925995
    street          13/13  rate=1.0                  nll=0.24566514790058136
    sibling_name    13/13  rate=1.0                  nll=2.3904333114624023
    person_name     12/13  rate=0.9230769230769231   nll=0.4091116487979889
    house_number    10/13  rate=0.7692307692307693   nll=1.1385736465454102
    birth_year      10/13  rate=0.7692307692307693   nll=1.2660512924194336
    hometown         8/13  rate=0.6153846153846154   nll=3.1255314350128174
[phase19_erasure] TARGET_SLOT = pet_name
[phase19_erasure] target question counts (fixture-derived): {'core_taught': 14, 'core_held_out': 13, 'pooled': 27}
[phase19_erasure] (a) denominator n = 27 pooled; best attainable upper bound at 0 successes = 0.091079 (vs 0.172267 on the held-out tier alone)
```

Denominators: 8 facts x 13 questions = 104, which is exactly the number of A2/`core_held_out` draw
records in the arm record — the `_handoff_counts` register, proved against a derived quantity and
never a literal. The eight successes sum to 92, string-identical to the published Phase 18 handoff
(`results/phase18_extraction_report.md`: *"92 of 104 core_held_out questions were extracted at
least once — a rate of 88.46%"*), so the ranking is a decomposition of an already-published number
rather than a new measurement.

### The attack family was SELECTED, not typed

```
A1-mild           87/104  rate=0.836538
A1-aggressive     30/104  rate=0.288462
A2                92/104  rate=0.884615
A3                85/104  rate=0.817308
ARMS[0] = adapter-on
best_attack_family -> A2
```

`target_rows_from_arm_record` aggregates all four dose-split families and calls the committed
`phase18_extraction.best_attack_family`; "A2" appears in this plan's code only as an expected value
inside one test, never as the input to a selection.

### The tie-break is load-bearing — the finding, not a footnote

FOUR of the eight slots sit at the ceiling `13/13`. The primary criterion "highest question-unit
recall" therefore returns `{pet_name, cat_name, street, sibling_name}`, and **TIE-BREAK 1 is what
picks the target out of that set.** `pet_name` wins on the lowest `ans1`/mean exposure NLL
(0.13365373015403748) — and it is the lowest of ALL eight, so the target is simultaneously at
ceiling recall and the most tightly held value in the adapter. That is the direction the tie-break
was written to take (*most exposed wins — the hardest erasure is the honest target*), and it is
pinned by `test_the_tie_break_is_load_bearing_on_the_real_record`, which fails if the tie ever
stops existing.

This is the concrete reason D7 required the tie-break in the same commit as the rule. A rule
committed alone would have left the ACTUAL choice to a tie-break written after the ranking was
visible — at which point picking `sibling_name` (also 13/13, but NLL 2.39, the loosest-held member
of the tied set) would have been a free two-clause edit.

### The (a) denominator, and the arithmetic that forced pooling

```
$ .venv/bin/python -c "from erasure_gate import wilson_upper_bound as w; ..."
n=  13  wilson_upper(0,n)=0.17226678350884503   0.172267
n=  27  wilson_upper(0,n)=0.09107873950450847   0.091079
n=  52  wilson_upper(0,n)=0.049456477045433093   0.049456
n= 108  wilson_upper(0,n)=0.024439096450642323   0.024439
```

Fixture-side derivation, independent of the arm record: `results/phase16_recall_sample.json`
holds 14 taught and 13 held-out rows for the target, matching the fixture's own published
`counts.per_core_fact` block (`{"taught": 14, "held_out": 13}`). 14 + 13 = 27 is SUMMED in code;
`test_the_pooled_denominator_is_never_typed_anywhere_in_the_pin` walks the pin's AST for an integer
literal equal to `N_TARGET_QUESTIONS` and requires zero (an AST walk rather than `grep -n "27"`,
because a grep cannot tell an integer literal from two digits inside one of the eight published
NLL floats).

The n=52/108 refusal is 4 x 13 and 4 x 27, where 4 is `len(phase18_extraction.ATTACK_FAMILIES)` —
derived in the test, not asserted.

### Full-plan verification

```
$ .venv/bin/python -m pytest -q tests/test_phase19_erasure.py tests/test_phase16_prereg.py tests/test_package.py
...............................                                          [100%]
31 passed in 9.02s

$ .venv/bin/python -m pytest -q
755 passed, 1 skipped, 83 warnings in 143.23s (0:02:23)

$ .venv/bin/python -m ruff check . && .venv/bin/python -m ruff format --check .
All checks passed!

$ git ls-files 'results/phase19_*'
(empty)
```

Baseline was 740 passed / 1 skipped at 19-01; +15 tests, same single pre-existing CUDA-only skip.

### Four deliberate mutations, all watched RED, all restored byte-identically

| # | Mutation | Result | Restored |
|---|----------|--------|----------|
| A | swap the head of `TARGET_RANKING` (`cat_name` first) | `test_target_ranking_is_re_derived_from_the_committed_arm_record` FAILED — `At index 0 diff: ('pet_name', ...) != ('cat_name', ...)` | sha256 `e09820b3…` before and after |
| B | add `TARGET_FACT_ID = "cand_dog_zorp"` (the plan's prescribed constant) | FAILED — `scripts/phase19_erasure.py embeds fact value(s) ['zorp']` | sha256 `e09820b3…` |
| C | `N_TARGET_QUESTIONS = 27` typed instead of summed | `test_the_pooled_denominator_is_never_typed_anywhere_in_the_pin` FAILED | sha256 `2aa825cb…` |
| D | `TARGET_QUESTION_COUNTS["core_taught"] = 15` | TWO tests FAILED — the fixture re-count AND the prose-number check, because inflating n moves the Wilson bound the rule quotes | sha256 `2aa825cb…` |

Mutation D is the one worth naming: it demonstrates that the rule's own prose is tied to the
arithmetic, so a denominator edit cannot leave a stale `0.091079` sitting in the pre-registration.

## Deviations from Plan

### 1. [Rule 2 — threat mitigation the plan's own register mandates] The pin is keyed by SLOT; `TARGET_FACT_ID` is NOT a module constant

- **Found during:** Task 1, before writing any code.
- **Plan text:** *"`TARGET_FACT_ID` and `TARGET_RANKING` — the derived results, written as module
  constants"*, with `provides: "… TARGET_FACT_ID, TARGET_RANKING …"`.
- **The conflict:** the SAME plan's threat register disposes T-19-07 (*"Information disclosure |
  fact values on the import surface"*) as **mitigate**, with the mitigation stated as *"the
  LAZY-IMPORT RULE — no fact strings at module import"*. All eight core fact ids embed their own
  locked value:

```
cand_person_quillon    | slot= person_name   | value-in-id: True
cand_dog_zorp          | slot= pet_name      | value-in-id: True
cand_cat_zibby         | slot= cat_name      | value-in-id: True
cand_sister_orsala     | slot= sibling_name  | value-in-id: True
cand_town_brindlemoor  | slot= hometown      | value-in-id: True
cand_street_marrowgate | slot= street        | value-in-id: True
cand_year_1987         | slot= birth_year    | value-in-id: True
cand_house_7412        | slot= house_number  | value-in-id: True
```

  So `TARGET_FACT_ID` as a literal would have written the erasure target's own answer into the
  pre-registration file, and a fact-id-keyed `TARGET_RANKING` would have written all eight.
- **Resolved as:** `TARGET_SLOT` (derived from `TARGET_RANKING[0]`) is the pinned name, and
  `TARGET_RANKING` is keyed by slot. The slot ↔ fact id binding is 1:1 and already committed, so
  `TARGET_SLOT` is exactly as specific as `TARGET_FACT_ID` would have been.
  `select_target_fact(per_fact_rows, exposure)` still RETURNS a `fact_id` exactly as the plan
  specifies — the prohibition is on the source embedding one, not on one flowing through at
  runtime — and `target_fact_id(records)` is the one committed slot→id resolution path so no
  downstream plan writes an id by hand.
- **Precedent, not invention:** `scripts/phase17_personas.py:61` (*"keying by id would drag Phase
  14 values into this matrix"*), `scripts/phase17_isolation.py:128`, and Phase 16's recorded
  `SYNTHETIC_FACT_ORDER commits SLOTS, not fact ids` decision are the same call made three times
  before.
- **Enforced structurally, not by care:** the new scan in
  `test_target_selection_rule_states_its_tie_breaks_and_the_forbidden_move` checks the pin's whole
  source against all ten locked+soft values. Watched RED against the plan's exact prescribed
  literal (mutation B above).
- **Commit:** `b64cfc5`

### 2. [Clarification] `TARGET_QUESTION_COUNTS` is a written constant re-counted by test, not derived at import

- **Found during:** Task 2.
- **Plan text:** *"`N_TARGET_QUESTIONS` is the pooled value, assigned from the function's output
  rather than typed."*
- **Resolved as:** `TARGET_QUESTION_COUNTS = {"core_taught": 14, "core_held_out": 13}` written down
  with its provenance, and `N_TARGET_QUESTIONS = sum(TARGET_QUESTION_COUNTS.values())` — so 27 is
  computed, never typed (the property T-19-06 and the plan's own done-criterion name), while the
  pin does no file I/O at import.
- **Why:** calling `derive_target_question_counts()` at module scope would read two JSON artifacts
  and pull `phase18_extraction` (and transitively torch and the Phase 14 surface) into `sys.modules`
  on every import of the pre-registration. `scripts/phase18_extraction.py`'s own guard records the
  opposite discipline — *"the only calls this driver makes at module scope are its bootstrap, its
  derived best-achievable p, D-31's proof and the two pure displays"*, all pure. A pin that cannot
  be imported without its inputs on disk is a pin whose rules stop being quotable the moment a path
  moves. The same `CALIBRATION_SHA` treatment `TARGET_RANKING` gets is applied here for consistency.
- **What replaces the import-time derivation:** two things, both stronger than a single assignment.
  (i) `test_target_question_counts_are_re_derived_from_the_committed_fixture` re-counts the fixture
  rows on every run and additionally cross-checks against the fixture's own published
  `counts.per_core_fact`. (ii) A module-scope `_prove` ties `TARGET_QUESTION_COUNTS["core_held_out"]`
  to `TARGET_RANKING[0]`'s denominator — two independently sourced counts, from different artifacts
  through different instruments, so an edit to either one alone stops the pin importing.
- **Commit:** `970028d`

### 3. [Rule 2 — clarification] `target_question_counts` takes `tiers` as a parameter

- The plan's signature is `target_question_counts(fixture_path)`. Written that way the function
  would have to name `"core_taught"`/`"core_held_out"` as literals — a second copy of
  `phase18_extraction.CORPUS_TIERS`, free to stop agreeing with the first. It takes
  `(fixture, fact_id, tiers)` instead; `derive_target_question_counts(fixture_path,
  arm_record_path)` is the file-reading wrapper that supplies `CORPUS_TIERS` through the lazy
  import. The side benefit is that the pure function is exercisable on a synthetic fixture with no
  torch, which is what makes the duplicate-row refusal testable at all.

## Findings For Downstream Plans

1. **`TARGET_SLOT` is `pet_name`; there is no `TARGET_FACT_ID` constant.** Resolve it at runtime
   with `target_fact_id(records)` against any record set carrying `fact_id` and `slot` (every Phase
   18 draw record does). Do not write the id into a source file — the value scan will redden.
2. **`N_TARGET_QUESTIONS = 27` is POOLED and the pooling is TWO `aggregate_questions` calls**, one
   per tier, summed afterwards. `aggregate_questions` hard-`_prove`s a single tier and
   `scripts/phase18_extraction.py` is uneditable at `99716e0`, so there is no merged-tier call and
   no widening path. 19-04/19-05's arm runners must do it this way or they will abort.
3. **19-03's floor has a hard reachability ceiling: `BEST_ATTAINABLE_TARGET_BOUND = 0.091079`.**
   The pin exposes it as a constant. A calibrated floor below it cannot be cleared at any outcome,
   including a perfect erasure — the blind calibration has to land inside that budget or the phase
   is arithmetically dead before it runs, exactly as Phase 18's D-31 m=6 analysis was.
4. **The target is the HARDEST one available.** `pet_name` is at ceiling recall (13/13 under A2)
   AND holds the lowest `ans1`/mean NLL of all eight slots (0.1337 vs `hometown`'s 3.1255). No
   later plan may present that as an unlucky draw: it is what tie-break 1 was written to produce.
5. **The `A2`/`adapter-on`/`core_held_out`/K=48 cell is the scoring frame the (a) condition
   inherits.** `STATE.md`'s standing instruction — *"post-erasure recall must be scored by the same
   adversary at the same budget"* — now has a committed builder: `target_rows_from_arm_record`.
   It proves the budget against the record's own `config["k"]` rather than a constant.
6. **`--target` re-prints every derived number in this plan** (`python scripts/phase19_erasure.py
   --target`). It calls the same two functions the tests call, so the printer and the guard cannot
   drift into deriving different orders.

## Known Stubs

None. Every function this plan added is fully implemented and exercised by a committed test.

## Threat Flags

None. No new network endpoint, auth path or schema at a trust boundary. Two committed JSON
artifacts are read (read-only, in `derive_target_question_counts` and in `__main__`); no checkpoint
is loaded, no `weights_only` choke point is touched, and nothing is written to disk.

## Threat Register Disposition

| Threat ID | Disposition | Status |
|-----------|-------------|--------|
| T-19-05 | mitigate | **Done** — `TARGET_RANKING`/`TARGET_SLOT` are re-derived from `results/phase18_arm_adapter-on.json` by `test_target_ranking_is_re_derived_from_the_committed_arm_record` on every run; the artifact's first-add SHA `9a923d6` is recorded in the rule text AND asserted present by test. Watched RED against a swapped head. |
| T-19-06 | mitigate | **Done** — `target_question_counts` counts the fixture's own rows, `_prove`s no duplicate `(fact_id, seed_index)` over EVERY row of each tier (not only the target's), and refuses a zero count. `N_TARGET_QUESTIONS` is summed; an AST walk requires zero integer literals equal to it. Watched RED both ways. |
| T-19-07 | mitigate | **Done, and widened.** No fact string reaches module import: `phase18_extraction` and `phase14_factset` are imported only inside function bodies and `__main__`, `values` reaches `score_records` as a parameter, and — beyond the plan's mitigation — the pin's entire source is scanned against all ten locked+soft values, which is what forced deviation 1. |
| T-19-08 | mitigate | **Done** — `wilson_upper_bound` is imported from `scripts/erasure_gate.py` at module scope and pinned by OBJECT IDENTITY, not by matching values. The pin defines no function of that name and imports no `math`, so there is no sqrt available to re-derive one. `BEST_ATTAINABLE_TARGET_BOUND > 0.0` pins that it is Wilson and not Wald. |
| T-19-SC | mitigate | **Holds** — zero packages installed; `tests/test_package.py` green (`pyproject.toml` sha256 pin unmoved). |

## Verification Against Plan Success Criteria

- [x] The target fact is named in the pin (as `TARGET_SLOT`, see deviation 1), with the rule AND
      both tie-breaks in the same commit `b64cfc5`.
- [x] The full eight-fact ranking is published with successes, denominator, rate and tie-break NLL,
      so a reader checks the choice rather than trusting it.
- [x] n = 27 is derived from the committed fixture and the pooling departure is DECLARED —
      `DENOMINATOR_RULE` clause 2, asserted by test to contain the word "departure".
- [x] No calibration, no erasure and no Phase 19 artifact has run or been written;
      `git ls-files 'results/phase19_*'` returns nothing.

## Self-Check: PASSED

- `scripts/phase19_erasure.py` — FOUND (modified)
- `tests/test_phase19_erasure.py` — FOUND (modified)
- commit `b64cfc5` — FOUND
- commit `970028d` — FOUND
- `results/phase19_*` tracked files — 0 (guard intact)
