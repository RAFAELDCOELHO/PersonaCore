---
phase: 19-selective-memory-erasure
plan: 04
subsystem: testing
tags: [pre-registration, noise-floor, estimator, record-schema, d3, d4, b5, q75, erase-01, stat-02, stat-05, stat-06]

requires:
  - phase: 19-selective-memory-erasure
    provides: "19-01's open pin (`scripts/phase19_erasure.py`) and its ARMED git-ancestry guard"
  - phase: 19-selective-memory-erasure
    provides: "19-02's `TARGET_SLOT`, `CORE_GATED_SLOTS`, `N_TARGET_QUESTIONS = 27` and the armed fact-value source scan"
  - phase: 19-selective-memory-erasure
    provides: "19-03's `lock_erasure_floor` and `ERASURE_FLOOR_MIN` — the (a) producer this plan's tests drive the gate with"
  - phase: 18-extraction-audit
    provides: "`EXPOSURE_RECORD_KEYS`, `NLL_FRAMES`/`NLL_REDUCTIONS`, `results/phase18_arm_adapter-on.json` and the `seed_index * K` stride"
provides:
  - "DIALOGUE_NOISE_FLOOR_ESTIMATOR (6 clauses) + DIALOGUE_NOISE_FLOOR_SEEDS + dialogue_noise_floor() + dialogue_cap()"
  - "RETENTION_MEASUREMENT — the first committed spec for retention PPL on an ADAPTED model"
  - "NONTARGET_NOISE_FLOOR_ESTIMATOR (7 clauses) + nontarget_deltas() + nontarget_noise_floor() + GATED_NONTARGET_SLOTS"
  - "SOFT_TIER_DESCRIPTIVE_READ + SOFT_TIER_SLOTS — the B5 narrowing declared with its measured reason"
  - "SEED_STRIDE_OFFSET + replicate_seed_stride() — a per-question non-collision proof against Phase 18's windows"
  - "ARM_RECORD_KEYS / ARM_CONFIG_KEYS / PRE_ERASURE_KEYS / DIALOGUE_PPL_KEYS / FORBID_IDS_SHA256 + _arm_record()"
  - "zero_results_have_nll() + zero_result_exposure_gaps() — the INCONCLUSIVE short-circuit, made structural"
  - "V20_DIALOGUE_NOISE_FLOOR_FULL_FT and V20_TAUGHT_ADAPTER_DIALOGUE_PPL — the pre-erasure (c) excess, on the record"
affects: [19-05, 19-06, 19-07, 19-09, 19-12, 19-13]

tech-stack:
  added: []
  patterns:
    - "when the plan's prescribed identifier would trip a committed guard, substitute the value-free spelling and WATCH the prescribed one go red — never widen the guard"
    - "a flag a gate reads as a boolean must BE a boolean; the reasons live in a separate named function, because a (False, reason) pair is truthy and would silently disarm the branch"
    - "one function serves both (b) inputs — the noise floor and the gate numerator are the same quantity against two different second readings, so a second implementation would be a second rule"

key-files:
  created: []
  modified:
    - scripts/phase19_erasure.py
    - tests/test_phase19_erasure.py

key-decisions:
  - "`SOFT_TIER_SLOTS` names the two soft facts by SLOT, not by the `fact_id`s the plan's action text prescribed — both soft ids end in their own value, and the prescribed spelling was watched RED against 19-02's armed source scan with hits ['chartreuse', 'marzipan']"
  - "the estimator records `mean <= max` as EXACT arithmetic with a measured one-ulp floating-point residual, not as an unqualified always — the naive sum/len exceeds max at 2 of 200,003 swept vectors, both by exactly 1.0 ulp, and a test asserts the false stronger sentence is ABSENT"
  - "`zero_results_have_nll` returns a plain bool and `zero_result_exposure_gaps` carries the reasons — a `(False, reason)` return is TRUTHY, so `not zero_results_have_nll` in the gate would evaluate False and disarm the INCONCLUSIVE branch on exactly the run that needed it"
  - "`per_fact` was added to the plan's ARM_RECORD_KEYS list because the plan's own `zero_results_have_nll(arm_record)` signature is otherwise unsatisfiable — question-unit successes live nowhere in Phase 18's record shape"
  - "config spells the budget `k`, not the plan's `K`: Phase 18's committed config is lowercase and `target_rows_from_arm_record:456` already reads `config['k']`, so `K` would have been a second spelling inside one phase"
  - "`dialogue_noise_floor` guards at `>= 1.0` rather than the plan's `>= 0`: exp(mean CE) >= 1 is arithmetic, and the realistic mistake the function invites is being handed a DELTA where a PPL belongs"

patterns-established:
  - "drive the REAL gate in the test rather than re-deriving its arithmetic — the dialogue cap is read back out of `erasure_succeeded`'s own reason string over a swept range, then checked behaviourally at the `<=` boundary"
  - "a constant whose value is knowable now is pinned (the forbid digest); one that is not is a REQUIRED FIELD with no value (`corpus_sha256`), because inventing it early is the move the pin refuses everywhere else"

requirements-completed: []

duration: 55min
completed: 2026-08-17
---

# Phase 19 Plan 04: The Three Missing Estimators And The Record Schema — Summary

**Every keyword-only argument of `erasure_succeeded` now has a named producer in the pin — 9 of 9,
verified by introspection — and the one nobody notices was missing (`dialogue_ppl_noise_floor`) is
committed as an estimator whose own pre-erasure arithmetic already shows a +1.2387 (c) excess that
predates any erasure.**

## Performance

- **Duration:** ~55 min
- **Tasks:** 3 of 3 (TDD, RED then GREEN each)
- **Files modified:** 2 (0 created, 2 modified)
- **Tests:** +16 (767 -> 783 passed, same single pre-existing CUDA-only skip)

## Accomplishments

- The two (c) producers landed with their seed pair, their arm config and the pre-erasure excess
  they already price — before either number exists.
- The (b) producer landed with its DECLINED alternative, its precedent, and — the part the plan
  correctly insisted on — its REDUCTION, which is as threshold-shaped as any floor.
- The arm-record schema landed as an ordered hard equality, and `zero_results_have_nll` became a
  function of the artifact rather than a boolean someone sets.
- `git ls-files 'results/phase19_*'` is still **EMPTY** (verified 0 at start, after every commit,
  and at end). No calibration, no ablation, no erasure, no Phase 19 artifact.

## Task Commits

1. **Task 1 RED** — `48859f8` (test): 5 failing tests for the (c) dialogue floor and retention spec
2. **Task 1 GREEN** — `32de94f` (feat): the estimator, the seed pair, `dialogue_noise_floor`, `dialogue_cap`, `RETENTION_MEASUREMENT`
3. **Task 2 RED** — `630996b` (test): 6 failing tests for the (b) floor, per fact and never pooled
4. **Task 2 GREEN** — `3a13a8f` (feat): the estimator, its reduction, the seed stride, the soft-tier narrowing
5. **Task 3 RED** — `f76b1cb` (test): 5 failing tests for the record schema and a structural flag
6. **Task 3 GREEN** — `8ebd241` (feat): `ARM_RECORD_KEYS`, `_arm_record`, `zero_results_have_nll`

## Files Created/Modified

- `scripts/phase19_erasure.py` (modified, 1020 -> 1612 lines) — three new sections. Module
  docstring updated: "WHAT THIS FILE HOLDS" now says 19-04, and a new paragraph names all nine
  keyword-only gate arguments against the plan that produced each.
- `tests/test_phase19_erasure.py` (modified, 1185 -> 1912 lines) — 16 new tests, all CPU-only.

## Evidence

### All nine gate arguments now have a producer — introspected, not asserted

```
$ .venv/bin/python - <<'PY' ... inspect.getfullargspec(erasure_gate.erasure_succeeded).kwonlyargs
erasure_succeeded keyword-only arguments: 9
  target_successes           19-02     target_rows_from_arm_record / TARGET_RANKING         in pin: True
  target_questions           19-02     N_TARGET_QUESTIONS                                   in pin: True
  target_floor               19-03     lock_erasure_floor                                   in pin: True
  nontarget_deltas           19-04 T2  nontarget_deltas                                     in pin: True
  nontarget_noise_floor      19-04 T2  nontarget_noise_floor                                in pin: True
  dialogue_ppl               19-04 T1  DIALOGUE_PPL_KEYS / run_collapse_control adapter_on  in pin: True
  dialogue_ppl_noise_floor   19-04 T1  dialogue_noise_floor                                 in pin: True
  retention_ppl              19-04 T1  RETENTION_MEASUREMENT                                in pin: True
  zero_results_have_nll      19-04 T3  zero_results_have_nll                                in pin: True
unmapped: [] | missing symbol: []
```

### The plan's verification commands

```
$ .venv/bin/python -m pytest -q tests/test_phase19_erasure.py tests/test_phase16_prereg.py tests/test_package.py
...........................................................              [100%]
59 passed in 8.97s

$ git ls-files 'results/phase19_*'
(empty)

$ .venv/bin/python -m pytest -q
783 passed, 1 skipped, 83 warnings in 145.69s (0:02:25)

$ .venv/bin/python -m ruff check . && .venv/bin/python -m ruff format --check .
All checks passed!
```

Baseline was 767 passed / 1 skipped at 19-03; +16 tests, same single pre-existing CUDA-only skip.

### The (b) reduction, priced through the REAL gate before it was chosen

```
 max floor=0.1                    margin=0.200000  verdict=SUCCESS
        (b) worst non-target degradation 0.100000 <= k=2 x 0.100000 = 0.200000
mean floor=0.04                   margin=0.080000  verdict=FAILURE
        (b) worst non-target degradation 0.100000 > k=2 x 0.040000 = 0.080000
```

Both verdicts come from `erasure_gate.erasure_succeeded` itself, on the same seven-fact-shaped
spread under two reductions. `max` is the MORE PERMISSIVE one, and the pin says so.

### The pre-erasure (c) excess, computed and on the record before any erasure

```
dialogue cap at delta_ft: 4.576708
excess: +1.2387 (1.2386920000000003)
required floor: 0.62105 (0.6210500000000003)  -> roughly 364x the only floor ever measured
retention cap: 4.029000
```

Both inputs trace to committed reports and the test checks them against the files:
`0.001704` in `results/finetune_smoke_report.md`, `5.8154` in `results/phase14_recall_report.md`.

### The retention call-site census, measured by AST walk rather than quoted

```
retention_perplexity CALL sites in scripts/+src/: 6
['scripts/build_retention_bin.py:145', 'scripts/build_retention_bin.py:151',
 'scripts/finetune_ab.py:238', 'scripts/finetune_dialog.py:206',
 'scripts/finetune_smoke.py:335', 'scripts/finetune_smoke.py:299']

$ grep -ln "inject_lora\|load_adapter" scripts/build_retention_bin.py scripts/finetune_ab.py \
    scripts/finetune_dialog.py scripts/finetune_smoke.py
exit=1 (none matched)
```

### The fixture census that licenses the (b) denominator

```
core_taught      n_rows 112  per-fact counts [14]  n facts 8
core_held_out    n_rows 104  per-fact counts [13]  n facts 8
soft             n_rows  54  per-fact counts [27]  n facts 2
pooled per fact: [27]  n facts 8  total 216
arm record tiers: ['core_held_out', 'core_taught']   <- ZERO soft draws
```

All eight core facts carry the identical 14 + 13 census, which is why `N_TARGET_QUESTIONS` is the
right per-fact denominator for the non-targets too and no second name was bound to it.

### Two deliberate mutations, both watched RED, both restored byte-identically

| # | Mutation | Result | Restored |
|---|----------|--------|----------|
| A | `SOFT_TIER_SLOTS` spelled with the plan's prescribed `fact_id`s | **2 tests RED** — the armed 19-02 value scan reports `assert ['chartreuse', 'marzipan'] == []` | sha256 `1a3aabf1…` |
| B | `nontarget_noise_floor` reduces by `mean` | **RED** — `assert 0.04 == 0.1` | sha256 `1a3aabf1…` |

Both restorations verified: sha256 `1a3aabf165fbb4bf2766cab786e730854b814ecbfc1059087eb586610e1d9343`
before and after, `git diff --stat` and `git status --short` both empty.

## Deviations from Plan

### 1. [Rule 3 — blocking: the prescribed identifier would redden a committed guard] the soft facts are named by SLOT

- **Found during:** Task 2, before writing the constant.
- **Plan text:** *"Pin `SOFT_TIER_DESCRIPTIVE_READ` naming both soft facts"*, with the action's own
  parenthetical naming them as `cand_color_chartreuse` and `cand_food_marzipan`.
- **The conflict:** both soft `fact_id`s end in their own locked value, exactly as the core eight
  do. 19-02 committed a source scan over all ten locked+soft values, and the docstring rule
  *"NO FACT VALUE MAY ENTER THIS FILE, IN ANY STRING, DOCSTRINGS INCLUDED"* is older than this plan.
- **Resolved as:** `SOFT_TIER_SLOTS = ("favorite_color", "favorite_food")`, re-derived against
  `phase14_factset.SOFT_TIER_FACTS` by test so the written constant cannot drift from the fact set.
  The slot pair identifies the two facts exactly as specifically as the ids do — the binding is 1:1
  and committed.
- **Proved, not assumed:** mutation A above. The prescribed spelling turns the scan red naming both
  leaked values.
- **This is the fourth application** of the `phase17_personas.py:61` / `SYNTHETIC_FACT_ORDER`
  precedent, and the second time in Phase 19 that a plan's prescribed literal would have written
  fact material into the pre-registration.
- **Commit:** `3a13a8f`

### 2. [Rule 1 — a pinned sentence that would not survive checking] `mean <= max` is exact, not always

- **Found during:** Task 2 GREEN, by a test I had written to assert the plan's own generalisation.
- **What the plan says:** *"Since `mean <= max` and `b_ok` is `worst <= 2 x floor`, a mean floor is
  strictly the harder gate."*
- **What the measurement says:** in floating point the naive `sum(v)/len(v)` can exceed `max(v)`.
  Measured over 200,003 vectors of length 1..7 (200,000 random, seed 1337, plus 3 hand cases):
  **2 exceed, both by exactly 1.0 ulp**, both constant vectors — `[0.2, 0.2, 0.2]` gives
  `0.20000000000000004 > 0.2` and `[0.1, 0.1, 0.1]` the same. At `[0.2] * 7`, the length the gate
  actually sees, it does not.
- **Resolved as:** the clause states the ordering as EXACT arithmetic and records the one-ulp
  residual, in the same register 19-03's W1 clause uses — a residual of order 1e-17 against margins
  of order 1e-2. A committed test asserts the unqualified sentence is ABSENT and that "one ulp" is
  present, so the stronger version cannot be restored by a later tidy-up.
- **Why it matters:** this file is unamendable after 19-07. The direction claim is still true and is
  still the honest one; it is the *always* that would not survive checking.
- **Commit:** `3a13a8f`

### 3. [Rule 3 — the plan's own signature is otherwise unsatisfiable] `per_fact` added to `ARM_RECORD_KEYS`

- **Found during:** Task 3, designing the schema.
- **The conflict:** the plan pins `zero_results_have_nll(arm_record)` — one argument — and requires
  it to check *"EVERY fact with zero question-unit successes"*. Question-unit successes exist
  nowhere in Phase 18's record shape (`arm`, `config`, `draw_record_keys`, `draws`, `exposure`);
  scoring happens afterwards, through `score_records(draws, values)`, and `values` is fact material
  the pin may not touch.
- **Resolved as:** one key added, `per_fact`, carrying the rows in `target_rows_from_arm_record`'s
  existing shape — the same shape `nontarget_deltas` already consumes. The flag is then answerable
  from the artifact ALONE: a reader holding the JSON rechecks it without re-scoring anything.
- **Alternative declined:** a second parameter would have made the flag underivable from the record
  and would have broken the plan's pinned signature.
- **Commit:** `8ebd241`

### 4. [Rule 1 — two spellings of one quantity] config carries `k`, not `K`

- The plan lists `K` among the required config columns. Phase 18's committed config spells it `k`,
  and `phase19_erasure.target_rows_from_arm_record:456` already reads `arm_record["config"]["k"]`.
  Adopting `K` would have put two spellings of the attack budget inside one phase and two readers
  on one field. `ARM_CONFIG_KEYS` uses `k`, with the reason recorded beside the constant.
- **Commit:** `8ebd241`

### 5. [Rule 2 — a strictly stronger guard] `dialogue_noise_floor` refuses below 1.0, not below 0

- The plan says the function *"refuses a non-finite or a negative input"*. `masked_perplexity`
  returns `exp(mean CE)` over non-negative cross-entropies, so a value below **1.0** is
  arithmetically impossible for the named instrument, and every negative value is below 1.0 — the
  guard is strictly stronger than the plan's. It also catches the realistic confusion the function
  invites: `dialogue_noise_floor(4.5, 0.001704)`, a delta handed in where a PPL belongs, which a
  non-negativity check would accept happily.
- **Commit:** `32de94f`

### 6. [Clarification] the retention call-site count is 6, not 4

- The plan's objective states *"exactly four call sites and none is adapted (§Q4, verified by
  exhaustive grep)"*. Measured by AST walk: **6 `retention_perplexity` calls across 4 modules** —
  `finetune_smoke.py` and `build_retention_bin.py` hold two each. The plan's number is a module
  count. The load-bearing half of the claim is **confirmed**: none of the four modules so much as
  imports `inject_lora` or `load_adapter`, so retention PPL has never been measured on an adapted
  model. `RETENTION_MEASUREMENT` records "6 call sites across 4 modules" and the committed test
  re-runs the census on every run.

## Findings For Downstream Plans

1. **The (c) dialogue half is already over its cap before any erasure runs.** At the only dialogue
   noise floor this repo has ever measured the cap is 4.576708 and the taught adapter reads 5.8154
   — an excess of **+1.2387**. 19-05/19-06 must publish the PRE-erasure dialogue PPL beside the
   post-erasure one in every table, because a (c) failure that predates the erasure and one the
   erasure caused are different findings. A floor big enough to admit 5.8154 would be **0.62105**,
   roughly 364x; whether a same-recipe seed spread reaches that is genuinely unknown and the
   estimator is how it becomes known. Do not present a wide ruler as a good result.
2. **The (c) retention half is fully determined and has never been measured.** `retention_cap`
   = 4.029000 with both operands already committed. What does not exist is a single reading of
   `retention_perplexity` on an adapted model. `RETENTION_MEASUREMENT` pins the call; 19-05 owns
   running it, PRE and POST, in the same process as the draws.
3. **The (b) replicate is ONE run, not two.** The pre-erasure per-fact rates are already committed
   in `results/phase18_arm_adapter-on.json` at A2/K=48. The replicate is 216 core questions x 48
   draws = 10,368 draws, about 60 min at the measured 172 draws/min. Use `replicate_seed_stride` —
   it proves the non-collision per question, and a colliding stride would report a floor of zero.
4. **(b) is gated on SEVEN and the two soft facts are a DESCRIPTIVE read.** Their post-erasure
   recall must be measured and published beside the gated seven, never gated. The reason is that
   the arm record holds zero `soft` draws, so there is no baseline to pair against — this is a
   property of the arm record, not of the fixture, which does carry 54 soft questions.
5. **The arm record's `per_fact` block is what makes a SUCCESS publishable.** A successful erasure
   produces `target_successes == 0`, and without a complete exposure block for all eight slots —
   pre and post, six finite NLLs each — the gate returns INCONCLUSIVE rather than SUCCESS. Build
   the exposure inside the same generation context as the draws (Phase 18's
   `phase18_extraction.py:3696-3702`); a second process makes "absent" and "weak" inseparable.
6. **`nontarget_deltas` serves BOTH (b) inputs.** Pass the seed-stride replicate as `post_rows` for
   the noise floor; pass the post-erasure scoring for the gate numerator. Do not write a second
   per-fact differencer.
7. **The rows every (b) function consumes are POOLED per fact (n = 27), not gated-tier (n = 13).**
   `target_rows_from_arm_record` aggregates the gated tier only, so 19-05 must do the two-call
   pooling `DENOMINATOR_RULE` describes before feeding `nontarget_deltas`, or the denominator
   `_prove` fires.

## Known Stubs

None. Every constant and function this plan added is fully implemented and exercised by a committed
test. No `results/phase19_*` artifact exists or was written.

## Threat Flags

None. No new network endpoint, auth path or schema at a trust boundary. This plan reads no
checkpoint, loads no model, touches no `weights_only` choke point and writes nothing to disk. The
one new import (`personacore.config.ModelConfig`) is a dataclass already in the pin's transitive
import graph via `personacore.lora`.

## Threat Register Disposition

| Threat ID | Disposition | Status |
|-----------|-------------|--------|
| T-19-13 | mitigate | **Done** — `DIALOGUE_NOISE_FLOOR_ESTIMATOR` pins the estimator, the seed pair and all seven recipe constants in one commit, while `git ls-files 'results/phase19_*'` is empty. Each recipe constant is checked against its live `teach_persona` value by test, so a drifted recipe reddens rather than silently re-scoping the floor. The ARMED ancestry guard proves the order. |
| T-19-14 | mitigate | **Done** — `nontarget_deltas` refuses anything but the seven per-fact entries, enforces the QUESTION unit twice (denominator AND the rate's own successes/questions identity), and holds NO reducing call at all: an AST walk over its body asserts `sum`/`mean`/`max`/`min` are absent. No pooled return path exists to be taken. |
| T-19-15 | mitigate | **Done** — `zero_results_have_nll` is structural: exposure required for all eight slots, six finite frame x reduction NLLs each, `None`/NaN/inf each disqualifying, and the pre-erasure block held to the same bar. It returns a real `bool`; the `(False, reason)` truthiness trap is recorded and tested. |
| T-19-16 | mitigate | **Done** — `FORBID_IDS_SHA256` asserted equal to the committed arm record's own value, and `_arm_record` refuses a record that ran under a different mask. `corpus_sha256`, `k`, `seed_stride`, `mechanism` and `ablated_components` are required config fields; provenance columns are allowed on top, since Phase 18's own config carries a dozen. |
| T-19-17 | accept | **Holds** — no new load path introduced. This plan loads no checkpoint at all. |
| T-19-SC | mitigate | **Holds** — zero packages installed; `tests/test_package.py` green (`pyproject.toml` sha256 pin unmoved). |

## Verification Against Plan Success Criteria

- [x] All three missing constants have a committed procedure and estimator; none has a value yet —
      `dialogue_ppl_noise_floor` via `dialogue_noise_floor`, `nontarget_noise_floor` via the
      seed-stride replicate and its pinned `max` reduction, `target_floor` from 19-03.
- [x] Retention PPL of the adapted model has a committed spec — `RETENTION_MEASUREMENT`, with the
      "no adapted precedent" claim measured by AST census rather than quoted.
- [x] A zero-recall result cannot reach the verdict without its teacher-forced NLL —
      `zero_results_have_nll` computes the flag from the record, for all eight slots, pre and post.
- [x] The `forbid_ids` concern is a measured column, not an assumption — the digest is a required
      config field asserted equal to Phase 18's, and the Q7.5 residual is answered in the
      docstring by the instrument that measures it.

## Self-Check: PASSED

- `scripts/phase19_erasure.py` — FOUND (modified, 1612 lines)
- `tests/test_phase19_erasure.py` — FOUND (modified, 1912 lines)
- commit `48859f8` — FOUND
- commit `32de94f` — FOUND
- commit `630996b` — FOUND
- commit `3a13a8f` — FOUND
- commit `f76b1cb` — FOUND
- commit `8ebd241` — FOUND
- `results/phase19_*` tracked files — 0 (guard intact)
- pin sha256 after both mutations — `1a3aabf165fbb4bf2766cab786e730854b814ecbfc1059087eb586610e1d9343`, `git status --short` empty
</content>
</invoke>
