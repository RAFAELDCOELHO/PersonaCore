---
phase: 18-black-box-adversarial-extraction-audit
plan: 06
subsystem: evaluation
tags: [teacher-forcing, span-nll, carlini-exposure, pre-registration, cpu-only, falsifiable-control]

# Dependency graph
requires:
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-03's D-04 pin — `_prove`, the INVERTED lazy-import rule, `_corpus_entry`'s ordered-schema pattern"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-02's `fake_lm` — a parameter-free, RNG-free stand-in on the `gpt.py` forward contract, with the `targets=`-bearing loss branch this plan reads"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-05's `build_corpus` — the pinned file this plan extends with 0 deletions of pre-registered content"
  - phase: 17-cross-persona-isolation
    provides: "`PERSONA_FACTS` — 24 minted values, 3 per core slot, lifting |R| from 3-5 to 6-8"
  - phase: 14-teach-then-recall
    provides: "`SLOT_FORMS` (the `ans1`/F4/F3 answer frames), `GATE_REJECTED_CANDIDATES`, `CALIBRATION_POOL`, `REGISTER_ARM_POOL`, `LOCKED_FACTS`"
provides:
  - "`span_nll_from_ids` / `value_span_nll` — teacher-forced value-span NLL, three answer frames, both reductions from ONE forward pass"
  - "`NLL_FRAMES` / `NLL_REDUCTIONS` / `ADMISSIBLE_NLL_FRAME` / `ADMISSIBLE_NLL_REDUCTION` / `HELD_OUT_NLL_FRAME` — the D-29/D-30 pre-registration as module literals"
  - "`reference_set_for` / `reference_length_spread` — D-20's per-slot R of 6-8 and its published length confound"
  - "`exposure_rank` / `assert_spread_zero_reductions_agree` — Carlini exposure with the phase's own ceiling and D-30's falsifiable control"
  - "`measure_exposure` / `EXPOSURE_RECORD_KEYS` — one self-labelling record per slot, descriptive, structurally outside the Holm family"
  - "five new committed guards in `tests/test_phase18_draws.py`"
affects: [18-07, 18-10, 18-12, 18-14]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Both reductions computed as two independent `F.cross_entropy` calls over the same `-100`-masked targets, so `mean * n == sum` is a checkable fact rather than an identity the function wrote itself"
    - "A construction identity published as a second internal control: two columns that MUST be equal by geometry, so a disagreement can only be an instrument defect"
    - "A statistic's threats-to-validity string travelling INSIDE the record, so no renderer can emit the number without its confound"

key-files:
  created: []
  modified:
    - scripts/phase18_extraction.py
    - tests/test_phase18_draws.py

key-decisions:
  - "The scored context is `[ASSISTANT_ID] + frame preamble` — an answer-frame anchor, no question. D-29 names `SLOT_FORMS[slot].ans1`, a REPLY string; a question anchor would need F4's question, which names its own value and would measure copying"
  - "Preamble and value are encoded SEPARATELY so BPE cannot merge across the boundary and move the span per frame; the span is then exactly `len(tok.encode(value))` ids for every frame and every candidate"
  - "`nll_mean` is a second `cross_entropy` at `reduction='mean'`, not `nll_sum / n` — otherwise the mean/sum assertion is a tautology"
  - "`exposure_rank` gained a required `length_spread` keyword the plan's signature omitted: the spread is a required published field and the stated signature cannot produce it"
  - "Ties break on the candidate string, so the rank is reproducible across processes rather than dependent on how R was assembled"
  - "`ranking` (a tuple of candidate values) stays inside `exposure_rank` and is NOT propagated into the published record — D-11 keeps fact material out of the artifact by recording `slot`"

patterns-established:
  - "`_exposure_record(**fields)` mirrors `_corpus_entry`: ordered hard equality against a module-level key tuple, proved in the one place records are built"

requirements-completed: [ATK-04, STAT-06]

# Metrics
duration: ~40min
completed: 2026-08-15
---

# Phase 18 Plan 06: The Two Missing Instruments Summary

**The teacher-forced value-span NLL and the Carlini exposure rank now exist inside the D-04 pin —
three answer frames and both reductions from one forward pass, a same-slot R of 6-8 publishing its
own 2.5850-3.0000 bit ceiling, and D-30's spread-0 control measured non-vacuous at a clean 6/6
disagree vs 2/2 agree.**

## Performance

- **Duration:** ~40 min end to end; the three task commits span **8m23s** (22:44:15 → 22:52:38),
  the rest is reading and design.
- **Tasks:** 3, one commit each
- **Files:** 2 modified — **480 insertions / 1 deletion** in the pinned driver, **316 / 1** in the
  test file. Both deletions are the SAME line in each file, `from personacore.dialogue import
  build_recall_prompt`, widened in place to `import ASSISTANT_ID, build_recall_prompt` — see
  Deviations. No pre-registered text was removed.
- **Suite:** **684 passed / 7 skipped / 0 failed** in 127s. The arithmetic is exactly the predicted
  worktree delta: `685 (main after Wave 3) − 6 worktree-only skips + 5 new tests = 684`.

## Task Commits

1. **Task 1** — the span NLL, three frames, two reductions — `91538d0` (feat)
2. **Task 2** — the reference set, the rank, and the spread-0 control — `16b6359` (feat)
3. **Task 3** — one self-labelling exposure record per slot — `8e4e919` (feat)

## Accomplishments

- **The span mask is the value and nothing else, proved by counting.** `span_nll_from_ids` follows
  `masked_perplexity`'s shift semantics exactly — token *j*'s mask governs the prediction OF token
  *j*, `mask == 0` targets become `ignore_index=-100` and enter neither the sum nor the
  denominator — and `_prove`s that the scored target count equals `len(value_ids)` on every call.
  An NLL that scored the preamble would report a number about `my name is` as evidence about the
  value (T-18-06-02).
- **Both reductions come off ONE forward at `targets=None`.** `GPT.forward`'s own loss is
  `reduction='mean'` over every target with no `ignore_index` and has no sum slot at all, so the
  reduction is this function's decision — which is the entire point of pre-registering it.
  `grep -c "model(.*targets=" scripts/phase18_extraction.py` returns **0**.
- **`ADMISSIBLE_NLL_FRAME` / `ADMISSIBLE_NLL_REDUCTION` / `HELD_OUT_NLL_FRAME` are module literals
  inside the ancestry-pinned file**, read at the call site and never retyped, with the exclusion of
  the held-out frame asserted rather than described (T-18-06-01).
- **R is assembled, not inherited.** `reference_set_for` filters the three base pools plus Phase
  17's 24 minted values to the same slot and adds the taught value, giving the measured 6-8 with
  zero duplicates and zero cross-slot contamination (asserted pairwise over all 28 slot pairs).
  Pooling across slots to recover the wider figure is declined in the docstring: those bits measure
  slot-type plausibility, a confound dressed as precision.
- **The exposure record carries its own confound.** `EXPOSURE_THREATS_TO_VALIDITY` and the STAT-06
  descriptive label travel INSIDE every record — the mechanism `report_proportion`'s `wilson_label`
  gave Phase 16 — so a renderer cannot emit an exposure figure without its qualifier.
- **Nothing on the exposure path opens a second hypothesis family.** No p-value is computed and
  `sign_test_exact` is not called, pinned by an AST walk over `measure_exposure`'s own subtree
  rather than by a text search (D-22 / T-18-06-04).

## Measurements

All numbers below are **instrument-shape measurements**, taken against `fake_lm` — a hash logit
surface, not language. They pin counts, ceilings, orderings and determinism. **No number here is a
finding about the model**; the real NLLs arrive with the D-12 pre-flight smoke and the run.

### The eight per-slot ceilings (Task 2 acceptance, verbatim)

```
slot            |R|  ceiling_bits  length_spread
person_name       8        3.0000              3
pet_name          8        3.0000              3
cat_name          7        2.8074              2
sibling_name      7        2.8074              1
hometown          7        2.8074              3
street            6        2.5850              2
birth_year        7        2.8074              0
house_number      6        2.5850              0
```

Matches D-20 and D-30's measured tables row for row, re-derived here from the committed pools
through the live tokenizer rather than transcribed. |R| = 6-8 → a **2.5850-3.0000 bit** ceiling,
which is this phase's own number and not the pooled eleven-slot figure.

### The span count (Task 1 acceptance)

```
slot           len(tok.encode(value))  n_scored ans1   f4   f3
person_name                         5              5    5    5
pet_name                            4              4    4    4
cat_name                            5              5    5    5
sibling_name                        6              6    6    6
hometown                            8              8    8    8
street                              8              8    8    8
birth_year                          4              4    4    4
house_number                        4              4    4    4
```

Every frame scores exactly the value's ids, on every slot. Separate encoding of preamble and value
is what makes this hold across frames — a joint encode would let the preamble's last character
merge with the value's first and move the boundary per frame.

`person_name` / `ans1`: `nll_sum = 50.872398`, `nll_mean = 10.174479`, `n_scored = 5`;
`nll_mean * 5 = 50.87239742` against `nll_sum = 50.87239838` — the two independent
`cross_entropy` reductions agree to float32.

### D-30's control is non-vacuous — a clean 6/6 vs 2/2 split

```
slot           spread sum_rank mean_rank  orders agree
person_name         3        5         6         False
pet_name            3        3         4         False
cat_name            2        6         7         False
sibling_name        1        4         3         False
hometown            3        7         3         False
street              2        6         5         False
birth_year          0        7         7          True
house_number        0        4         4          True
```

This is the measurement that makes the control worth having. **All six length-confounded slots
disagree between the reductions; both spread-0 slots agree exactly.** Had the two reductions agreed
everywhere, "they agree at spread 0" would have been true of an instrument in which the reduction
never mattered — and the control would have been measuring nothing. `test_mean_is_admissible_and_
spread0_agrees` asserts the non-vacuity directly, not just the agreement.

### One exposure record (Task 3 acceptance, `python` run, exit 0)

```
record keys : slot admissible nll rank exposure_bits ceiling_bits n_references length_spread
              spread_zero_control descriptive_label threats_to_validity
admissible  : ('ans1', 'mean')
slot=person_name rank=6 |R|=8 ceiling=3.0000 exposure=0.4150 spread=3 control=False
six NLLs    :
   ans1         sum=50.872398 mean=10.174479
   f4_reversed  sum=54.456375 mean=10.891275
   f3_bare      sum=54.456375 mean=10.891275
measure_exposure callees: ['_exposure_record', '_prove', 'assert_spread_zero_reductions_agree',
                           'exposure_rank', 'len', 'reference_length_spread', 'reference_set_for',
                           'scored.items', 'value_span_nll']
```

Zero `sign_test`/`holm` callees inside the function. `grep -c "sign_test_exact\|holm("` over the
whole file returns **3** — all three are D-31's import-time reachability proof and its docstrings,
none inside the exposure path, which is why the acceptance check is an AST walk over the enclosing
function and not a file-level grep.

## Deviations from Plan

### 1. [Rule 1 — Measured correction] D-29's f4-vs-f3 separation is not obtainable, and the identity is published instead

- **Found during:** Task 1, designing the frame contexts
- **Issue:** D-29 assigns `f4_reversed` the role of "separates the POSITION confound from the
  TAUGHT confound" against `f3_bare`. D-29's own table records that **both** frames put the value
  at reply position 0 (F4's reply is `f"{value} is {kind}."`, F3's completion is `f"{value}."`).
  Under a causal model with a value-only span mask and a shared anchor, their contexts are the same
  ids and nothing after the span can reach it — so the two span NLLs are **equal by construction**,
  which the run above confirms exactly (`54.456375` / `10.891275` for both). The intended contrast
  is unobtainable this way, and publishing two columns that look like a contrast and are an
  identity would be the worse outcome.
- **Fix:** The identity is recorded in `NLL_FRAME_RATIONALE` as a measured correction to D-29's
  intent, and asserted in `test_nll_frame_is_taught_not_bare` as a **second internal control** —
  a disagreement between those two columns can only mean the span mask or the causal mask has
  moved. `f3_bare` remains a published, gate-excluded column exactly as D-29 requires.
- **Files:** `scripts/phase18_extraction.py`, `tests/test_phase18_draws.py`
- **Commit:** `91538d0`
- **The alternative, and why it was not taken:** using each frame's own taught QUESTION as the
  anchor would keep the three distinct — but F4's question is `f"{who} is {value}?"`, which names
  its own value, so teacher-forcing the reply's value span after it measures **copying**, not
  memory. That is a worse instrument, not a better one. D-29 names `SLOT_FORMS[slot].ans1` — an
  ANSWER string — as the conditioning frame, and no question appears anywhere in D-29 or in the
  plan's action text, so the answer-frame anchor is also the more literal reading.

### 2. [Rule 3 — Blocking] `exposure_rank`'s stated signature cannot produce its stated record

- **Found during:** Task 2
- **Issue:** The plan specifies `exposure_rank(nll_by_candidate, *, taught_value, reduction)` and
  requires the returned record to carry "the slot's token-length spread as a required adjacent
  field". The spread is a function of the tokenizer and R; the stated signature receives neither.
- **Fix:** a required keyword-only `length_spread`, plus `reference_length_spread(tok, slot)` to
  produce it. `exposure_rank` stays pure — no model, no tokenizer, no device — which is the
  property that keeps the whole ranking layer unit-testable on CPU, the same one
  `phase17_isolation`'s scorer has. Required rather than defaulted: a field a caller may forget is
  a field that will be missing from the one record a reader checks.
- **Commit:** `16b6359`

### 3. [Rule 2 — Missing critical check] Non-vacuity of the spread-0 control asserted explicitly

- **Found during:** Task 2
- **Issue:** The plan asks only that the two reductions agree on the spread-0 slots. That assertion
  is satisfied by an instrument in which the reduction never changes anything at all, and would
  then guard nothing.
- **Fix:** `test_mean_is_admissible_and_spread0_agrees` additionally asserts that on at least one
  length-confounded slot the two orderings **do** disagree. Measured: all six disagree.
- **Commit:** `16b6359`

### Acceptance criteria reported rather than contorted

**The single deletion in each file.** The wave brief asks that `scripts/phase18_extraction.py` keep
its 0-deletion property. This plan needs `ASSISTANT_ID`, and `ruff`'s isort rule (`select = [..., "I"]`)
merges duplicate `from X import` lines, so a second import statement is not lint-clean. The one
deleted line in each file is the import statement widened in place:

```
-from personacore.dialogue import build_recall_prompt
+from personacore.dialogue import ASSISTANT_ID, build_recall_prompt
```

`git diff a20a8df..HEAD -- scripts/phase18_extraction.py | grep "^-"` returns that line and nothing
else. No pre-registered constant, template, docstring or proof was removed; the D-04 ancestry guard
(`test_phase18_prereg_is_frozen_before_every_phase18_result`) is green.

**`grep -c "4.8\|log2(28)\|28 references"` returns 0** — better than the criterion's "0 outside the
comment", because the declined-pooling record in `reference_set_for`'s docstring is worded
"pooled 28-reference figure (FEATURES.md:358)" and matches none of the three patterns. The record
the criterion exists to preserve is present; the strings it forbids are absent.

## Verification

| Check | Result |
|---|---|
| `pytest -q` (full suite) | **684 passed, 7 skipped, 0 failed** in 127s |
| `pytest -q tests/test_phase18_draws.py` | 7 passed in 4.0s (CPU, no GPU, no checkpoint) |
| `pytest -q tests/test_phase18_prereg.py` | 4 passed — including `test_no_fact_values_in_phase18_modules` and `test_nothing_loads_at_import` |
| `pytest -q tests/test_phase18_corpus.py` | 17 passed — 18-05's guards untouched |
| `pytest -q tests/test_phase16_prereg.py -k phase18` | 1 passed — the D-04 ancestry pin |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 160 files already formatted |
| `grep -c "model(.*targets=" scripts/phase18_extraction.py` | **0** |
| `grep -c "ignore_index=-100" scripts/phase18_extraction.py` | **3** (≥1 required) |
| `grep -c "^import phase17_persona_facts\|^from phase17_persona_facts"` | **0** — lazy import only |
| `git status --porcelain results/` | empty; `ls results/phase18_*` → no matches |
| Files deleted by any commit | **0** (`git diff --diff-filter=D` empty for all three) |

`test_nothing_loads_at_import` deserves a note: it is a **hard equality** on the pinned file's
module-scope `Call` nodes, so every new module-level name here is a plain literal or a tuple/string
display. `EXPOSURE_THREATS_TO_VALIDITY` and the two rationale strings are implicit concatenations,
not `"".join(...)`; every `math.log2` is inside a function body. The callee allowlist is unchanged.

## Threat register disposition

| Threat ID | Disposition | Discharged by |
|---|---|---|
| T-18-06-01 (Tampering — frame/reduction switched after a null) | mitigated | `ADMISSIBLE_NLL_FRAME`/`ADMISSIBLE_NLL_REDUCTION`/`HELD_OUT_NLL_FRAME` are literals inside the ancestry-pinned file; `measure_exposure` reads them and `_prove`s the admissible frame is not the held-out one |
| T-18-06-02 (Repudiation — an NLL dominated by the preamble) | mitigated | Scored count `_prove`d equal to `len(value_ids)` on every call, across 8 slots × 3 frames; preamble-invariance tested at the id level with two contexts sharing their final token |
| T-18-06-03 (Repudiation — exposure without its length confound) | mitigated | `length_spread` is a required argument AND a required record field; `EXPOSURE_THREATS_TO_VALIDITY` travels inside every record and is asserted non-empty on all 8 slots |
| T-18-06-04 (Tampering — exposure becomes a second Holm family) | mitigated | AST walk over `measure_exposure`'s own subtree: zero `sign_test`/`holm` callees. Read off the AST, not grepped |
| T-18-06-05 (Info Disclosure — module-level persona-facts import) | mitigated | Both fact-set imports are inside function bodies; `grep` returns 0 and `test_no_fact_values_in_phase18_modules` is green |
| T-18-06-SC (Tampering — package installs) | accepted | Zero installs; `pyproject.toml` untouched and its sha256 pin is green |

## Issues Encountered

- **Worktree base drift**, fifth consecutive plan. HEAD was `829cd5f`, behind the required
  `a20a8df`; a strict ancestor with a clean tree, so `git merge --ff-only` corrected it with 0
  commits lost.
- **Two `ruff format` reflows and one `E501`**, all in the test file and all in list
  comprehensions/assertion prose. No logic involved; both fixed before their commits.

## Deferred Issues

None new. The one item in `deferred-items.md` is 18-04's and is untouched.

## Known Stubs

None. `grep -c "TODO\|FIXME\|placeholder..."` returns 1 for the driver and 0 for the tests; the
single hit is the word "placeholder" in `_frame_preamble`'s docstring describing `ans1`'s `{v}`
template token, not a stub. Every function returns computed material and every one is exercised.

## User Setup Required

None — no external service configuration required.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema at a trust boundary. The
exposure record is a new schema, but it is in-memory only — nothing in this plan writes to disk,
so `results/phase18_*` still does not exist and every commit here remains a legitimate ancestor
under D-04.

## Next Phase Readiness

- **`null_result_is_admissible()` can now be written.** It reads `measure_exposure`'s record and
  the `(ans1, mean)` pair off the constants; both are callable, pure at the ranking layer, and
  CPU-tested.
- **The D-12 pre-flight smoke has its target.** D-28 requires the smoke to assert, on the
  un-adapted base only, that the NLL path returns finite values for every candidate in R across all
  8 slots and that the two spread-0 slots agree under both reductions. Both are one call each:
  `measure_exposure` per slot already raises `SystemExit` on a non-finite path (via the count proof)
  and runs `assert_spread_zero_reductions_agree` internally.
- **Cost, measured on the fake surface:** 3 frames × |R| forwards per slot = 24 at |R| = 8, 8 slots
  → **176 forward passes** for the whole exposure layer. Negligible against the 8.2h draw budget,
  as D-20 assumed.
- **Still not built, by design:** `null_result_is_admissible()`, the artifact writer, `main()`, the
  argument parser, the D-12 smoke, and the dispatcher that pairs the corpus against the two arms.
- **Carried forward:** the `f4_reversed` ≡ `f3_bare` identity. Any later plan reporting the three
  frames as three independent columns is reporting two numbers as three, and the guard in
  `test_nll_frame_is_taught_not_bare` says so at the point of the claim.

## Self-Check: PASSED

- `scripts/phase18_extraction.py` — FOUND (1436 lines, contains `def value_span_nll`,
  `def reference_set_for`, `def exposure_rank`, `def measure_exposure`)
- `tests/test_phase18_draws.py` — FOUND (483 lines, ≥200 required; 7 tests, 5 of them this plan's)
- `91538d0`, `16b6359`, `8e4e919` — all FOUND in `git log`
- `git status --short` clean apart from this SUMMARY
- No `STATE.md`, `ROADMAP.md` or `REQUIREMENTS.md` touched — the orchestrator owns the first two
  and the third is genuinely unchanged
- No file deleted by any commit

---
*Phase: 18-black-box-adversarial-extraction-audit*
*Completed: 2026-08-15*
</content>
</invoke>
