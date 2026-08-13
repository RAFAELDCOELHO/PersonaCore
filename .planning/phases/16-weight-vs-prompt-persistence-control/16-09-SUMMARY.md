---
phase: 16-weight-vs-prompt-persistence-control
plan: 09
subsystem: evaluation
tags: [STAT-01, STAT-02, STAT-06, D-06, D-07, D-08, D-09, D-29, sign-test, holm, bootstrap]

# Dependency graph
requires:
  - phase: 16 (plan 08)
    provides: "PER_QUESTION_KEYS, CONDITION_ORDER, normalize_by_split — the one per-question shape this plan keys on by fact_id"
  - phase: 16 (plan 07)
    provides: "the committed capability ladder, whose thresholds are LICENSING and therefore stay outside the Holm family"
  - phase: (pre-milestone)
    provides: "scripts/erasure_gate.py wilson_upper_bound / rule_of_three at 23a830c — the ONLY bounds source (STAT-04)"
provides:
  - "aggregate_by_fact — phase14_recall.py:838-843's shape with fact_id as the grouping key (D-06)"
  - "cluster_bootstrap — TWO-STAGE: facts resampled (STATE.md:94, n=8), then that fact's questions (STAT-01/D-06)"
  - "report_proportion — STAT-02's single reporting shape: two denominators, a labelled Wilson width, 3/n at zero, no bare zero percentage"
  - "sign_test_exact — two-sided in MAGNITUDE, directional in ALTERNATIVE (D-29), enumerated over all 256 partitions"
  - "HOLM_FAMILY_PAIRS / SIGN_TEST_ALTERNATIVE / TAUGHT_TIER_STATUS / holm / compare_arms / taught_replication / assert_family_closed"
affects: [16-10, 16-11, 17, 18]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A statistic that must satisfy two sources that disagree is implemented as TWO STAGES, one per source, rather than by picking a winner"
    - "A guard is pinned from the direction that makes the OTHER half a no-op, so neither half can be silently dropped"
    - "A defect fix gets a deliberate-RED observation: a guard nobody has watched fail is a guard nobody has verified"
    - "Prose explaining WHY a shape is forbidden is not the forbidden shape — source-grep guards get AST checks, not substring checks"
    - "The family size is DERIVED (itertools.combinations) and READ (len(...)), never retyped as a divisor"

key-files:
  created:
    - "tests/test_phase16_stats.py — 841 lines, 36 tests, CPU-only, torch-free"
  modified:
    - "scripts/phase16_persistence.py — 700 -> 1248 lines: the statistics block and the inferential gate"
    - ".planning/phases/16-weight-vs-prompt-persistence-control/16-09-PLAN.md — Task 1's bootstrap wording corrected to the two-stage form"

key-decisions:
  - "USER DECISION at the wave-8 checkpoint: the cluster bootstrap is TWO-STAGE (facts, then questions), overriding the plan's stage-2-only text — recorded in the docstring, in the plan file and here"
  - "No coverage/collision floor is asserted anywhere: the 6435 fact-multisets are not equiprobable, so any 6435-anchored floor is unreachable by construction"
  - "assert_family_closed landed in Task 2's commit rather than Task 3's, because compare_arms calls it — avoiding the noqa: F821 dance 16-08 hit"
  - "holm compares STRICTLY (p < alpha), so a boundary p FAILS — the phase15_stats arbitration, recorded as a distinction without a difference here"
  - "Two 16-08 source-grep guards were satisfied by rewording new PROSE, never by weakening the committed guard"

requirements-completed: [STAT-01, STAT-02, STAT-06]

# Metrics
duration: 55min
completed: 2026-08-13
---

# Phase 16 Plan 09: The per-fact statistic, the descriptive interval, and the inferential gate Summary

**The gate is the exact paired sign test enumerated over all 256 sign partitions, Holm-corrected
across exactly six pairs with a 6.7% margin, directional in its pre-registered alternative — and
the descriptive interval beside it is a two-stage cluster bootstrap that resamples facts before
questions, so it can never be narrower than the gate it accompanies.**

## Performance

- **Duration:** ~55 min wall clock
- **Tasks:** 3
- **Files created:** 1 · **modified:** 2
- **Tests added:** 36 (498 → 534 passed)

## Task Commits

1. **Task 1 — per-fact aggregation, the two-stage bootstrap, STAT-02's shape** — `33b4612` (feat)
2. **Task 2 — the exact sign test over 256 partitions, Holm across 6 pairs** — `26e0e60` (feat)
3. **Task 3 — STAT-06, nothing outside the six pairs is gated** — `f4cb17b` (test)

---

## THE BOOTSTRAP CORRECTION — a USER DECISION taken at the wave-8 checkpoint

**`16-09-PLAN.md` Task 1 specified `cluster_bootstrap` resampling ONLY questions within each fact,
with the 8 facts held FIXED. That was overridden by explicit user decision, and the plan file's
Task 1 wording was updated in the same commit (`33b4612`) so plan and code do not disagree.**

The implemented form is two stages, in this order:

1. resample the 8 **FACTS** with replacement (between-fact variability, n = 8)
2. within each **RESAMPLED** fact, resample that fact's own **QUESTIONS** with replacement

### The three sources it reconciles

| Source | What it fixes | Which stage honours it |
|---|---|---|
| `.planning/STATE.md:94` | "Bootstrap resampling is at FACT level (n=8), not question level" | **Stage 1** |
| `REQUIREMENTS.md:25-28` (STAT-01) | "Bootstrap resampling resamples *questions*" — its stated rationale (`:26-27`) targets the **DRAW** as the illegal unit (496/1008 as 1008 iid Bernoulli trials), not facts-vs-questions as the cluster | **Stage 2** |
| `16-CONTEXT.md` D-06 | keeps the QUESTION as the resampled unit | **Stage 2** |

### Why the plan's original form was the milestone's own failure mode

A question-only bootstrap produces an interval **conditional on these exact 8 facts** — narrower
than the fact-level sign test sitting beside it. Measured on a fixture whose questions are
homogeneous inside each fact (13 questions × 9 draws × 8 facts, rates 6/9 … 0/9), both at 10,000
resamples, seed 1337:

```
two-stage   (0.194444, 0.486111)   width 0.291667
stage-2 only (0.347222, 0.347222)  width 0.000000     <- the plan's original form
```

The stage-2-only interval is **exactly zero-width**: it claims the rate is known to six decimal
places while the gate beside it says "n = 8, and only unanimity clears". That is the over-claiming
direction this milestone exists to prevent, made numeric.

Both stages are pinned by test **from the direction that makes the other stage a no-op**, so
neither can be dropped in silence:

- `test_cluster_bootstrap_resamples_facts_first_stage_one` — questions identical inside each fact
  (stage 2 degenerate). Any real width therefore proves stage 1 runs. The test also computes the
  stage-2-only counterfactual inline and asserts it collapses to a single value.
- `test_cluster_bootstrap_resamples_questions_within_facts_stage_two` — facts identical to one
  another (stage 1 degenerate). Any real width therefore proves stage 2 runs.

### No coverage or collision floor is written anywhere

The fact layer's distinct outcomes are the multiset coefficient `C(8+8-1, 8) = C(15, 8) = 6435`
(reproduced two ways in `test_no_unreachable_coverage_floor_is_asserted_anywhere`: `math.comb(15,8)`
and `len(list(combinations_with_replacement(range(8), 8)))`). Those multisets are **not
equiprobable** — a multiset carries its multinomial weight, so a balanced draw is orders of
magnitude likelier than an all-same draw — and coupon-collector reasoning over 6435 uniform items
therefore does not apply. At 10,000 resamples only ~57% of them are drawn (orchestrator-supplied
measurement: 3692 at seed 1337, 3649 at seed 42). A floor such as `>= 6435 * 0.95` is **unreachable
by construction** and is nowhere in the module or its tests; the test asserts `6435` never reaches
executable code in the driver (AST numeric-constant scan, the 16-08 `0.125` idiom).

> **One figure was NOT propagated, deliberately.** The orchestrator's note states "a balanced draw
> is 5040x likelier than an all-same draw". My own derivation gives the multinomial ratio
> `8! : 1 = 40320 : 1`, not 5040 (`= 7!`). Rather than assert a number I could not reproduce or
> silently substitute my own against an instruction not to re-derive, **neither figure was written
> into any artifact**; the module and test state the non-uniformity qualitatively (`8!` orderings
> vs 1), which is all the conclusion needs. Flagged here so the discrepancy is visible rather than
> resolved by whichever of us was quieter.

---

## The inferential gate, as landed

### The five enumerated p-values

| observed | `sign_test_exact` | effect |
|---|---|---|
| **8/8** in the declared direction | **`0.0078125`** | clears at `0.05/6 = 0.0083333` |
| **7/8** | **`0.0703125`** | fails |
| **4/8** | **`1.0`** | fails — at the midpoint, so the direction filter fires |
| **1/8** | **`1.0`** | fails |
| **0/8** (all tied, or all against) | **`1.0`** | fails — **the hole D-29 closes** |

Also reproduced: `[1]*7 + [0]` → `0.0703125`, byte-identical to `[1]*7 + [-1]` — ties count AGAINST
and `n` stays 8 (D-08). And the D-08 **counterfactual** `n=7 pos=7 → 0.0156250`, enumerated *inline
in the test body* over `2**7` partitions and **never** obtained from `sign_test_exact`, which takes
no `n` parameter and is asserted (AST) not to have one.

### The Holm first-step margin

```
alpha at step 1 = 0.05 / 6 = 0.008333333333333333
unanimity p     =            0.0078125
margin          =            0.0005208333333333332   -> round(., 6) == 0.000521
relative to p   =            0.06666666666666665     -> round(., 3) == 0.067  (6.7%)
m = 7           -> alpha =   0.0071428571428571435   <  0.0078125   -> the headline dies
```

`test_family_of_seven_would_kill_the_headline` asserts **both halves**: that one more family member
prices alpha below the achievable p, *and* that the family as committed still clears. The second
assertion is what turns red the instant a seventh pair is added.

### `SIGN_TEST_ALTERNATIVE`, as committed

A module-level dict, spelled out per pair, AST-pinned as never assigned inside any function:

```python
SIGN_TEST_ALTERNATIVE = {
    ("adapter-only", "base-neither"):        "adapter-only exceeds base-neither",
    ("adapter-only", "embedding-cosine"):    "adapter-only exceeds embedding-cosine",
    ("adapter-only", "prompt-stuffed"):      "adapter-only exceeds prompt-stuffed",
    ("base-neither", "embedding-cosine"):    "base-neither exceeds embedding-cosine",
    ("base-neither", "prompt-stuffed"):      "base-neither exceeds prompt-stuffed",
    ("embedding-cosine", "prompt-stuffed"):  "embedding-cosine exceeds prompt-stuffed",
}
```

The rule for every pair is stated explicitly rather than left to convention: **the first arm of the
pair exceeds the second**. `assert_family_closed` proves the key set equals `HOLM_FAMILY_PAIRS`
exactly, so the hand-written dict and the `itertools.combinations`-derived family cannot drift.

### `HOLM_FAMILY_PAIRS` is derived, and `holm` reads its length

`tuple(itertools.combinations(CONDITION_ORDER, 2))` — 6 pairs, never a hand-typed list.
`holm` uses `m = len(HOLM_FAMILY_PAIRS)`; `test_holm_reads_the_family_length_rather_than_a_retyped_six`
walks `holm`'s AST and asserts no `ast.Div` node has a literal `6` on the right. The only `/ 6` in
the whole module is inside the comment recording D-09's arithmetic.

---

## The three deliberate-RED observations

All three ran against the committed file and were reverted **byte-identical**, each proved with
`git diff --exit-code scripts/phase16_persistence.py` (a `git checkout --` was blocked by a
destructive-command gate; the sanctioned byte-exact substring restore was used instead, exactly as
the environment rules direct).

### RED A — a 7th pair added to `HOLM_FAMILY_PAIRS`

```
FAILED tests/test_phase16_stats.py::test_family_of_seven_would_kill_the_headline
E   AssertionError: the family is at m = 7, where alpha = 0.0071428571428571435 does not exceed
E   the achievable p of 0.0078125 — the headline is dead arithmetically at every outcome
E   assert (0.05 / 7) > 0.0078125

FAILED tests/test_phase16_stats.py::test_holm_family_is_exactly_six_pairs
E   AssertionError: assert 7 == 6
```

Both named tests reported the problem. Restored; `git diff --exit-code` clean.

### RED B — the `positives <= SIGN_TEST_N / 2` early return deleted

**This is the exact defect D-29 exists to close, and it reproduced exactly:**

```
FAILED tests/test_phase16_stats.py::test_the_direction_filter_cannot_silently_invert
E   assert 0.0078125 == 1.0
E    +  where 0.0078125 = sign_test_exact(([0] * 8))

FAILED tests/test_phase16_stats.py::test_an_all_tie_pair_is_defined_and_scores_one
E   assert 0.0078125 == 1.0

FAILED tests/test_phase16_stats.py::test_p_is_one_below_the_midpoint
E   assert 0.0703125 == 1.0
E    +  where 0.0703125 = sign_test_exact(([1] + ([-1] * 7)))
```

Under the pure two-sided test an **all-tied pair scores `0.0078125`**, which is **below** Holm's
first-step alpha of `0.0083333` — it would have entered the family as SIGNIFICANT. Given Phase 14's
committed `1/1944`, the prompt-stuffed × base-neither pair is *expected* to tie on nearly all 8
facts, so this was not a hypothetical. Restored; `git diff --exit-code` clean.

### RED C — a `holm(...)` call added inside `taught_replication`

```
FAILED tests/test_phase16_stats.py::test_nothing_outside_the_six_pairs_enters_the_verdict_path
E   AssertionError: holm is called from somewhere other than compare_arms — every call site is a
E   hypothesis family, and D-09 permits exactly one
E   assert ['compare_arm..._replication'] == ['compare_arms']
E     Left contains one more item: 'taught_replication'

FAILED tests/test_phase16_stats.py::test_taught_tier_carries_the_verbatim_clause_and_is_not_gated
E   AssertionError: assert 'holm' not in {...}
```

Restored; `git diff --exit-code` clean.

---

## STAT-06 enforcement, both halves

| Route a 7th comparison could arrive by | Guard |
|---|---|
| a NEW CALL SITE | `test_nothing_outside_the_six_pairs_enters_the_verdict_path` — AST scan across **both** `phase16_persistence.py` and `phase16_ladder.py`. `holm` from exactly one enclosing function (`compare_arms`); `sign_test_exact` from exactly two (`compare_arms`, `taught_replication`); the ladder calls neither |
| a DYNAMICALLY-BUILT pair list | `assert_family_closed`, called by `compare_arms` at runtime. Rejects 7, rejects 5, rejects a duplicate |
| the PERS-03 sweep arriving with a gate attached | `test_context_pressure_sweep_is_not_gated` — lands **before** plan 16-10 writes the sweep (T-16-43), so the guard predates the code it constrains |

The ladder has **7 rungs** and the family has **6 pairs**, and that is consistent precisely because
`cell_passed` is a licensing decision that computes no p-value and emits no verdict —
`test_the_ladder_is_licensing_and_not_a_hypothesis_test` pins it.

## D-07's verbatim clause

`TAUGHT_TIER_STATUS` is asserted against `16-CONTEXT.md` by extracting the D-07 blockquote from the
file (the same `_context_blockquote` helper `tests/test_phase16_driver.py` uses for D-03), never
against a second hand-typed copy:

> o resultado do tier taught nunca altera, reforça formalmente, nem substitui o veredito do tier
> held-out — é evidência corroborante reportada, não gate.

`taught_replication` returns it with `gated: False`, **no alpha and no rejection flags** — there is
nothing on the record that could be read as a verdict — and `compare_arms` aborts if handed
`tier="taught"`, naming the 0.05/12 = 0.0041667 consequence in the abort message.

## Verification

```
.venv/bin/python -m pytest tests/test_phase16_stats.py -q
    15 passed        (Task 1 gate)
    32 passed        (Task 2 gate)
    36 passed        (Task 3 gate)

.venv/bin/python -m pytest tests/test_phase16_stats.py tests/test_phase16_driver.py \
                          tests/test_phase16_ladder.py tests/test_phase14_scoring.py \
                          tests/test_package.py -q
    150 passed       (Task 2 acceptance — the 16-08/16-07 guards still green with the new code in scan)

.venv/bin/python -m pytest -q
    534 passed, 1 skipped, 83 warnings in 120.50s (0:02:00)

.venv/bin/python -m ruff check .            All checks passed!
.venv/bin/python -m ruff format --check .   148 files already formatted

git diff --exit-code pyproject.toml         (clean)
git diff --stat results/                    (empty)
git status --short                          (empty)
```

**Baseline was `498 passed, 1 skipped` (measured on this machine immediately before Task 1).
Result `534 passed, 1 skipped`. Delta `+36` = this plan's 36 new tests. Zero failed, zero errors,
zero collection errors.**

### Acceptance criteria, item by item

| Criterion | Result |
|---|---|
| `pytest tests/test_phase16_stats.py -q` exits 0, ≥ 15 tests | **36** |
| `grep -c "scipy" scripts/phase16_persistence.py` | **0** |
| `git diff pyproject.toml` | empty |
| `grep -c "BOOTSTRAP_RESAMPLES = 10000\|BOOTSTRAP_SEED = 1337"` | **2** |
| `report_proportion(0,104,936)` carries `rule_of_three_upper`, no bare zero percentage | exit 0 — `0/104 questions (95% Wilson upper bound 0.025355; rule-of-three upper bound 0.028846; 936 draws)` |
| `cluster_bootstrap` deterministic under a fixed seed | asserted by test (and differs at seed 42) |
| percentile small-n bias named (grep `bias`) | **3** mentions |
| Task 2 importlib one-liner (6 pairs, five p-values, 6 declarations) | exit 0 |
| `sign_test_exact` enumerates; no `math.comb` closed form | asserted by AST test (`product` present, `comb` absent, `2 ** SIGN_TEST_N` present) |
| `SIGN_TEST_ALTERNATIVE` module-level only; keys == `HOLM_FAMILY_PAIRS` | asserted by AST test |
| `holm` reads `len(HOLM_FAMILY_PAIRS)`; literal `6` not a divisor | asserted by AST test; the only `/ 6` is the D-09 arithmetic comment |
| D-07 Portuguese clause byte-identical to `16-CONTEXT.md` | asserted by test, extracted from the file |
| `grep -c "def assert_family_closed"` = 1, called by `compare_arms` | **1**, AST-asserted |
| AST finds zero `holm` / `sign_test_exact` calls in `phase16_ladder.py` | **0** |
| Three deliberate-RED observations, restored byte-identical | all three recorded above, `git diff --exit-code` clean each time |
| `make test` green (venv form) | 534 passed, 1 skipped |

## Deviations from Plan

### 1. [USER DECISION] The bootstrap is TWO-STAGE, not question-only

Fully documented in its own section above. This is the only deviation that changes a committed
statistic, it was taken by explicit user decision at the wave-8 checkpoint, and `16-09-PLAN.md`'s
Task 1 wording was corrected in the same commit that implemented it.

### 2. [Sequencing] `assert_family_closed` landed in Task 2's commit, not Task 3's

- **Plan text:** Task 3 adds `assert_family_closed` to the driver.
- **What landed:** the function landed with Task 2, because Task 2's `compare_arms` calls it; Task 3
  added its three *tests*.
- **Why:** the alternative is a `# noqa: F821` forward reference across the commit boundary — the
  exact dance 16-08 was forced into by the same shape, and recorded there as deviation 2. Six lines
  of guard moved one commit earlier is a smaller cost than a lint-suppressed commit. Both commits
  are green standing alone, and the end state is identical (`grep -c "def assert_family_closed"`
  returns 1).

### 3. [Interface] `aggregate_by_fact` also returns each fact's `(k, n)` question list

- **Plan text:** returns `k`, `n_draws`, `n_questions`, `n_answerable`, `rate` per fact.
- **What landed:** those five, plus `questions` — the fact's per-question `(k, n)` pairs.
- **Why:** that tuple is exactly `cluster_bootstrap`'s input. Without it every caller re-groups the
  same records a second time, and a second grouping is a second place the grouping key can be wrong.

### 4. [Guard hygiene] Two 16-08 source-grep guards were satisfied by rewording NEW prose

- **What happened:** `test_driver_never_renders_a_bare_zero_percent_literal` (regex over the whole
  module source) and `test_arm_d_has_no_index_or_reranker` (`"scipy" not in source`) both went red
  on my additions — the first because `report_proportion`'s docstring *named* the forbidden
  rendering, the second because the `erasure_gate` import comment *named* the forbidden dependency.
- **What was done:** the new prose was reworded ("a bare zero percentage", "a third-party statistics
  package"). **Neither committed guard was touched.** Weakening a 16-08 guard to accommodate a 16-09
  docstring is exactly the "declared invariant silently becomes false" failure this project names as
  its most recurring defect, and the guards are substantively right — prose explaining why a shape
  is forbidden is not the forbidden shape, and the cheapest correct fix is on my side of the line.
- **Where the same category error was mine:** my own `test_no_unreachable_coverage_floor...` began
  as a substring check for `"6435 * 0.95"` and tripped on the docstring that forbids it. Fixed by
  switching to an AST numeric-constant scan (the 16-08 `0.125` idiom) rather than by deleting the
  prose.

### 5. [Environment] `make test` / `make lint` substituted with venv-explicit invocations

Same recorded substitution as 16-01/16-02/16-03/16-08: a bare `pytest` resolves to a pyenv 3.12 shim
and yields ~63 spurious `ModuleNotFoundError: No module named 'torch'` collection errors across
untouched files. The gate actually run is the full suite the `make` target wraps.

---

**Total deviations:** 5 (1 user decision, 1 sequencing, 1 interface, 1 guard hygiene, 1
environment). **Zero deviations under rules 1-4** — no bug was auto-fixed, no missing critical
functionality was added, and no locked value was altered. Deviation 4 is the only one that touched
an interaction with committed code, and it was resolved on the new code's side without relaxing
anything.

## Concerns recorded, implemented AS LOCKED

**`holm` compares strictly (`p < alpha`), so a boundary p FAILS.** Standard textbook Holm uses
`<=`. The strict form is the arbitration `scripts/phase15_stats.py` already committed for its own
gate ("the boundary is a FAIL"), and it is conservative in the anti-over-claiming direction. It is
recorded as a **distinction without a difference here**, verified: the achievable p values are
`{0.0078125, 0.0703125, 0.2890625, 0.7265625, 1.0}` and the step alphas are `0.05/k` for `k = 1..6`
= `{0.008333, 0.01, 0.0125, 0.016667, 0.025, 0.05}`; the two sets are disjoint. If a future edit
changes `SIGN_TEST_N`, this needs re-checking — that is why the reasoning is in the docstring rather
than in a commit message.

**Arm D's denominator is 13 questions where arms A/B/C carry 117 draws, and `fact_signs` does not
normalize them.** That is D-22 implemented as written: the sign test uses only the ORDERING between
two arms, never the magnitude of either denominator. 16-08's summary flagged the same thing as a
"must not normalize" instruction to this plan, and it was not normalized.

**`report_proportion` takes `successes` in the QUESTION unit and aborts on a draw count.** The
guard exists because `wilson_upper_bound(326, 104)` would otherwise raise a bare `ValueError` from
`erasure_gate` with no phase context, and because 326/936 (held-out draws) and its question-unit
counterpart are both real numbers in this phase that a caller could confuse.

## Issues Encountered

- **`aggregate_by_fact` refuses a mixed-tier record list.** D-10 forbids pooling taught with
  held-out, and `normalize_by_split` already returns them separately — but nothing structurally
  prevented a caller concatenating the two dict values before aborting. The `_prove` names D-10 in
  its message so the abort sends its reader to the decision rather than to the code.
- **`compare_arms` guards the ARM COUNT, not the pair count.** A pair count is unforgeable — it is
  derived from `HOLM_FAMILY_PAIRS`. The forgeable input is `per_fact_by_arm`, so that is what is
  checked (`set(per_fact_by_arm) == set(CONDITION_ORDER)`), and the abort message names the
  0.0041667 consequence.
- **`_context_blockquote` is duplicated from `tests/test_phase16_driver.py`.** Both copies read the
  planning artifact rather than a hand-typed string, so the property they pin is unaffected by the
  duplication; factoring it into a shared conftest helper would couple two independent test files
  for eight lines and was declined.
- **STAT-01 / STAT-02 / STAT-06 were marked Complete in `REQUIREMENTS.md`, and they are
  CROSS-CUTTING (16, 17, 18).** What this plan discharged is Phase 16's share: the question unit and
  its resampling (STAT-01), the one reporting shape carrying a bound and both denominators
  (STAT-02), and the closed six-pair family with everything else descriptive (STAT-06). Phases 17
  and 18 inherit the same obligations against their own numbers, and `REQUIREMENTS.md`'s own
  coverage note already states that STAT-01..06 are "satisfied *per phase* rather than in exactly
  one". The checkbox is milestone-level and has no per-phase granularity; this line is the caveat
  that would otherwise be missing.
- **No model was loaded, no generation was run, no package was installed.** This plan is statistics
  only; `pyproject.toml` and `results/` are byte-unchanged across all three commits.
- **`DEGEN-2` (D-10) stayed out of all three commits, both files, and this summary** beyond this
  sentence naming it as absent.

## Next Phase Readiness

- **16-10 must call `assert_arm_parity`** — 16-08 flagged it as defined-but-uncalled and this plan
  did not wire it; nothing here changed that.
- **16-10's `main()` composes exactly this:** `run_condition` per arm →
  `aggregate_by_fact(record["by_split"][tier], tier=tier)` per arm →
  `compare_arms(per_fact_by_arm, tier="held-out")` for the verdict and
  `taught_replication(per_fact_by_arm)` for the replication, with
  `cluster_bootstrap({fid: agg["questions"] ...})` and `report_proportion` for every published rate.
- **The report must print `TAUGHT_TIER_STATUS` beside the taught numbers**, and must not print an
  alpha or a rejection flag next to them — `taught_replication` deliberately carries neither.
- **`WILSON_LABEL` travels into the report with every Wilson bound.** A bound printed without it
  reads as the phase's width, which is the T-16-41 spoof.
- **D-25's arm-D qualifier is still 16-10's to carry** (16-08 recorded the 0.125-vs-0.05 numeric
  reconciliation); nothing in this plan discharges it.

## Threat Flags

None. Both files are CPU-only, non-networked, torch-free at the statistics layer, and write nothing
to disk. No new network endpoint, auth path, file-access pattern or schema was introduced.

## Self-Check: PASSED

Both files exist on disk carrying every claimed symbol — `scripts/phase16_persistence.py`
(`TIER_SPLITS`, `GATED_TIER`, `REPLICATION_TIER`, `BOOTSTRAP_RESAMPLES`, `BOOTSTRAP_SEED`,
`BOOTSTRAP_ALPHA`, `BOOTSTRAP_METHOD`, `WILSON_LABEL`, `aggregate_by_fact`, `cluster_bootstrap`,
`report_proportion`, `HOLM_FAMILY_PAIRS`, `HOLM_ALPHA`, `SIGN_TEST_N`, `SIGN_TEST_ALTERNATIVE`,
`TAUGHT_TIER_STATUS`, `_sign`, `fact_signs`, `sign_test_exact`, `assert_family_closed`, `holm`,
`compare_arms`, `taught_replication`) and `tests/test_phase16_stats.py` (36 test functions, all
exercised by the file run). All three task commits resolve in `git log`: `33b4612`, `26e0e60`,
`f4cb17b`. `git status --short` is empty and `git diff --stat results/ pyproject.toml` is empty.

---
*Phase: 16-weight-vs-prompt-persistence-control*
*Completed: 2026-08-13*
