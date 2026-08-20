---
phase: 18-black-box-adversarial-extraction-audit
plan: 09
subsystem: evaluation
tags: [positive-control, holm-family, admissibility, phase19-handoff, question-unit, cpu-only]

# Dependency graph
requires:
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-03's D-04 pin — `HOLM_FAMILY`, `GATED_TIER`, `REPORTED_TIER`, `VERDICTS`, `CONTROL_FAILED_REASON`, `VERDICT_PRECEDENCE`, `BEST_ACHIEVABLE_P`, `assert_holm_family_reachable`, `_prove`, the import-time callee register"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-07's `null_result_is_admissible`, `licensed_conclusion`, `ADMISSIBILITY_ZERO_KEYS` (144 cells), `_NAMED_CELL_LIMIT`"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-08's `aggregate_questions` row shape — `rate` in the QUESTION unit, `n_questions`, `questions` — the two fields the sign test and the bootstrap read"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-01's widened `holm(p_values, *, family=...)` — the keyword this phase's m=4 family enters through"
  - phase: 16-persistence
    provides: "`fact_signs`, `sign_test_exact`, `cluster_bootstrap`, `HOLM_ALPHA`, `SIGN_TEST_N` — all imported, none re-implemented"
  - phase: 15-selective-erasure-preregistration
    provides: "`erasure_gate.erasure_is_worth_attempting` — byte-untouched, consumed positionally"
provides:
  - "`parse_phase14_taught_rows` / `PHASE14_TAUGHT_REPORT` / `PHASE14_TAUGHT_QUESTIONS` / `PHASE14_TAUGHT_COLUMNS` — the 112 committed taught rows, count and columns proved"
  - "`family_zero_matches` / `FAMILY_ZERO_CONSEQUENCE_LABEL` / `FAMILY_ZERO_SCOPING_NOTE` — D-01's row-for-row comparison, with 496/1008 as a labelled derived consequence"
  - "`run_holm_family` / `HOLM_FAMILY_RATIONALE` / `CLUSTER_BOOTSTRAP_DESCRIPTIVE_LABEL` — the m=4 dose-split family on the gated tier, one sign-test call site"
  - "`assemble_verdict` / `best_attack_family` / `_handoff_counts` / `BEST_ATTACK_RULE` — the orchestrator and the four question-unit ints Phase 19 consumes"
  - "eight new committed guards in `tests/test_phase18_prereg.py`"
affects: [18-10, 18-11, 18-12, 18-14]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "An arity guard routed THROUGH the pinned instrument rather than copied in front of it — the p-values are built off the input's own members, so a mis-sized family is refused by `holm` and the size is asserted in one place"
    - "A descriptive interval nested as its OWN sub-record with its own `descriptive`/`gated` flags, because the comparison around it is gated and one flat pair of flags would have to be wrong about one of them"
    - "A handoff denominator proved against a quantity DERIVED from the same aggregation the statistic consumed, so the unit check needs no second literal to keep in step"

key-files:
  created: []
  modified:
    - scripts/phase18_extraction.py
    - tests/test_phase18_prereg.py

key-decisions:
  - "The vector D-01 compares is the 112-entry vector of per-question hit COUNTS, not 1,008 per-draw booleans. The committed artifact publishes `k/N` per question and nothing finer; the plan's 'per-draw hit vector' is not obtainable from it. The sum-preserving mismatch still fails at this granularity, which is the property D-01 exists for"
  - "`family_zero_matches` returns a 3-tuple `(matches, mismatches, derived)`. The plan's behaviour text pins `(True, [])` and separately requires the derived sum 'returned as a consequence field'; the third slot is the only shape satisfying both without a second function"
  - "`seed_index` is the row's ordinal position in the report's taught table. Verified, not assumed: `results/phase16_arm_adapter-only.json` numbers its core taught rows 0..111 in the identical order, so the two sides join without either re-deriving an index from question text"
  - "A recorded control that does not COVER the 112 committed questions ABORTS rather than returning mismatches — a run over a different question set is a different control, not a diverged one"
  - "`assemble_verdict` generates the conclusion on the BEST attack family and names it, which is the family the handoff carries. Publishing a different number beside the handoff would leave the report and Phase 19's precondition disagreeing"
  - "The Holm comparison rows carry `descriptive: False, gated: True`; the bootstrap sub-record carries the opposite. Labelling the four comparisons descriptive would make DD-03's 'the sign test is the only inferential instrument' true by relabelling rather than by design"

patterns-established:
  - "`_handoff_counts(question_counts, per_fact_by_family, family, arm)` — a caller-supplied count cross-checked against the aggregation it claims to summarise, at the interface where the unit matters"

requirements-completed: [STAT-01, STAT-02, STAT-06, ATK-03, ATK-05]

# Metrics
duration: ~50min
completed: 2026-08-16
---

# Phase 18 Plan 09: The Positive Control, the m=4 Holm Family and the Phase 19 Handoff Summary

**ATK-03's positive control now compares 112 questions row for row — so a run that moves one hit
between two of them fails while still summing to the committed 496 — and the four dose-split
comparisons, the erasure precondition and the closing paragraph are assembled by one function that
computes no statistic of its own.**

## Performance

- **Duration:** ~50 min end to end; the six task commits span **26m** across three RED/GREEN pairs.
- **Tasks:** 3, all TDD, six commits.
- **Files:** 2 modified — **504 insertions / 0 deletions** in the pinned driver, **430 / 0** in
  `tests/test_phase18_prereg.py`. The whole plan is **934 insertions and zero deletions**.
- **Suite:** **707 passed / 7 skipped / 0 failed** in 128s. The arithmetic is the predicted
  worktree delta exactly: `705 (main after Wave 6) − 6 worktree-only skips + 8 new tests = 707`.

## Task Commits

1. **Task 1 RED** — the 112-row parse, the sum-preserving mismatch, the absent width knob — `b76ca7d` (test)
2. **Task 1 GREEN** — `parse_phase14_taught_rows`, `family_zero_matches` — `8a7c08f` (feat)
3. **Task 2 RED** — unanimity, the wrong-tier raise, the arity raise, the call-site scan — `53c3fc9` (test)
4. **Task 2 GREEN** — `run_holm_family` — `d5b8b5b` (feat)
5. **Task 3 RED** — the control short-circuit, the unchanged verdict, the 936 trap — `3439979` (test)
6. **Task 3 GREEN** — `assemble_verdict`, `BEST_ATTACK_RULE`, `best_attack_family` — `dd70fd6` (feat)

## Accomplishments

- **The control asserts the vector; the headline falls out of it.** `family_zero_matches` compares
  all 112 questions on `(fact_id, seed_index)` and returns `496/1008` only as a labelled
  consequence. The discriminating case is committed: **one hit moved from question 0 to question
  1** leaves the numerator at exactly 496 and the function returns `False`, naming both. A harness
  asserting the aggregate returns PASS on that input. No width parameter of any spelling exists —
  asserted off the *signature*, and `grep -cE "tolerance|atol=|band="` on the driver returns **0**.
- **A short parse cannot pass quietly.** The count `_prove` is mutation-proved against a
  **truncated copy in `tmp_path`** — the tracked report is read and never written, so a failed
  proof cannot leave the artifact edited. The column header is asserted verbatim before a cell is
  read, because this parse is positional and a reordered column produces 112 well-formed rows of
  the wrong quantity. Each row's `n` is cross-checked against `FAMILY_ZERO_DRAWS`, tying the
  artifact to D-09's committed budget rather than to a second 9.
- **Four comparisons, one tier, one sign-test call site.** `run_holm_family` calls
  `persistence.fact_signs` and `persistence.sign_test_exact` once per family and steps them through
  the widened `holm(..., family=HOLM_FAMILY)`. The call-site count is asserted **off the AST at
  exactly `["<module>", "run_holm_family"]`** rather than grepped — a text scan is equally happy
  inside the paragraph explaining the rule. `grep -c "sign_test_exact("` returns **2**.
- **The arity guard is `holm`'s, not a copy of it.** The p-values are built off the input's own
  members, so a five- or three-member family reaches the pinned instrument with a mismatched count
  and is refused *there*. What is checked locally is what `holm` structurally cannot see: it reads
  only `len(family)`, so four members under the **wrong names** step through untouched — caught
  after the call against `HOLM_FAMILY`.
- **The taught tier enters no family, loudly.** `run_holm_family(..., tier=REPORTED_TIER)` raises
  `SystemExit` quoting `TIER_SPLIT_RATIONALE` and naming D-31.
- **The unit trap is closed at the interface Phase 19 reads.** `_handoff_counts` proves each
  denominator against a count **derived from the same aggregation the sign test consumed** —
  `sum(row["n_questions"])` = 104 — so a 936 arriving in a question-unit slot aborts naming both
  numbers. No second literal has to be kept in step by hand.
- **The orchestrator adds no judgement.** `assemble_verdict`'s returned `(verdict, reasons)` are
  asserted **equal to `null_result_is_admissible` called directly on the same inputs**. On both
  INCONCLUSIVE paths `holm`, `handoff` and `conclusion` are all `None`: a zero measured by a
  harness not known to work and a zero measured by one that is are indistinguishable from outside.

## Measurements

Every number below is an **instrument-shape measurement** over committed artifacts and synthetic
records. No model, no checkpoint, no tokenizer and no device is involved anywhere in this plan.
**None of them is a finding about the model.**

### The taught parse against the real report (Task 1 acceptance, `python -c`, exit 0)

```
rows parsed                112   (== PHASE14_TAUGHT_QUESTIONS)
distinct facts               8   (the core slots; the report's 140-row taught split is 112 + 28 soft)
seed_index range         0..111  contiguous, matching phase16_arm_adapter-only.json row for row
derived numerator      496/1008  returned under FAMILY_ZERO_CONSEQUENCE_LABEL, compared to nothing
per-question mismatches      0   over all 112 rows
```

### The sum-preserving mismatch — the case that separates the two readings

```
fixture                    recorded sum   family_zero_matches
exact reproduction              496       (True,  [])
one hit moved 0 -> 1            496       (False, [seed_index 0, seed_index 1])
```

Both rows sum to the identical committed numerator. Only the second diverges per question, and a
harness asserting `496/1008` cannot tell them apart.

### The Holm family at unanimity (Task 2 acceptance, `python -c`, exit 0)

```
m = 4    first step alpha = 0.05/4 = 0.0125    sign_test_exact((1,)*8) = 0.0078125 < 0.0125

family           p          alpha_at_step   adapter-on 95% CI    adapter-off 95% CI
A1-aggressive    0.0078125  0.0125000       [0.2981, 0.4904]     [0.0385, 0.1349]
A1-mild          0.0078125  0.0166667       [0.2981, 0.4904]     [0.0385, 0.1349]
A2               0.0078125  0.0250000       [0.2981, 0.4904]     [0.0385, 0.1349]
A3               0.0078125  0.0500000       [0.2981, 0.4904]     [0.0385, 0.1349]

rejected 4/4 — the reachable success case D-31 chose m = 4 to keep available
```

The intervals are **descriptive** (`resamples=200` in the test; the production default is the
committed 10,000) and no branch reads them: `rejected` comes from `holm` alone.

### The verdict record on all three paths (Task 3 acceptance, `python -c`, exit 0)

```
path                          verdict               holm   handoff        conclusion
control diverged (0 -> 1)     INCONCLUSIVE          None   None           None
budget short (1 of 56,304)    INCONCLUSIVE          None   None           None
attack_successes = 0          NULL_ADMISSIBLE       4 rows (7,104,0,104)*  rendered
attack_successes = 7          LEAKAGE_DEMONSTRATED  4 rows (7,104,0,104)   rendered

reachable verdicts == VERDICTS          {INCONCLUSIVE, LEAKAGE_DEMONSTRATED, NULL_ADMISSIBLE}
control-failure reasons[0]              CONTROL_FAILED_REASON, verbatim
best attack at (1,2,7,3)                A2        handoff (7, 104, 0, 104), four ints
best attack at (5,5,5,5)                A1-mild   the earlier member of ATTACK_FAMILIES
erasure precondition                    True — "attack 7/104 (rate 0.0673, 95% lower bound 0.0369)"
936 as a held-out denominator           SystemExit naming 936 against 104
```

`*` the NULL_ADMISSIBLE row's handoff is `(0, 104, 0, 104)`; the tuple shown is the leakage case's.

## Deviations from Plan

### 1. [Rule 3 — Blocking] The committed artifact publishes `k/N`, not per-draw booleans

- **Found during:** Task 1
- **Issue:** The plan's behaviour text asks `parse_phase14_taught_rows()` for rows "carrying
  ... per-draw hit vector". `results/phase14_recall_report.md`'s per-question table has five
  columns — `question | fact | split | reserved | k/N` — and publishes the number of a question's
  draws that hit, never the 9 booleans behind it. The per-draw vectors exist only in
  `results/phase16_arm_adapter-only.json`, which is the RECORDED side, not the reference. Writing
  the function to the plan's letter would mean parsing a column the artifact does not have.
- **Fix:** the reference rows carry `k` and `n`; the recorded rows carry `hits` and `n_draws`
  (18-08's `SCORED_RECORD_KEYS` shape) and the comparison is `sum(hits) == k` and
  `n_draws == n`, per question. That is exactly the comparison D-01 recorded as giving 0
  mismatches ("diffed against the arm's per-question `hits`"). **The property D-01 exists for is
  intact:** the sum-preserving mismatch still fails at this granularity, and it is the committed
  test case. The granularity limit is stated in the parse's docstring rather than left implied,
  because "hit vector" could otherwise be read as the 1,008 booleans.
- **Files:** `scripts/phase18_extraction.py`, `tests/test_phase18_prereg.py`
- **Commit:** `8a7c08f`

### 2. [Rule 2 — Missing critical check] `seed_index` is the report's row order, and it was verified rather than assumed

- **Found during:** Task 1
- **Issue:** The plan's join key is `(seed_index, fact_id)`, but the report publishes no
  `seed_index` column. The obvious reading — position within its fact, 0..13 — was **measured and
  is wrong**: `results/phase16_arm_adapter-only.json` numbers its core taught rows **0..111
  globally**, so a per-fact index joins 14 of 112 rows and reports 98 phantom "MISSING" mismatches.
  The soft-tier rows carry their own 0..27, so the global numbering is over the core block alone.
- **Fix:** `seed_index` is the row's ordinal position in the taught table. Verified against the arm
  artifact three ways before the function was written: the core order equals the report order
  exactly, the seed indices are contiguous 0..111, and the join produces **0 k-mismatches and 0
  question-text mismatches**. Recorded in the docstring so the next reader does not re-derive it.
- **Commit:** `8a7c08f`

### 3. [Rule 2 — Missing critical check] A recorded control that does not cover the 112 aborts

- **Found during:** Task 1
- **Issue:** The plan's return shape is `(matches, mismatches)`, so a control that scored 111 of
  the 112 questions — or a different 112 — would come back as an ordinary mismatch and be read as
  "the control diverged". Those are different findings: one is a harness that ran and disagreed,
  the other is a harness that ran something else.
- **Fix:** a `_prove` on the key-set equality and on recorded-side duplicates, in the same register
  `null_result_is_admissible` already uses — schema and coverage failures raise, measurement
  deficiencies return a verdict. Committed as a test.
- **Commit:** `8a7c08f`

### 4. [Rule 1 — Bug] The plan's `_prove` on the comparison count would make `holm`'s own guard unreachable

- **Found during:** Task 2
- **Issue:** The plan asks for both "`_prove` ... that the number of comparisons equals
  `len(HOLM_FAMILY)`" and "a five-member or three-member input raises through `holm`'s own family
  guard". A local count check before the call satisfies the first and **defeats the second**: the
  pinned instrument's guard never fires, and the family size ends up asserted in two places free to
  disagree.
- **Fix:** the count `_prove` runs on `holm`'s **returned rows**, after the call. A mis-sized input
  is refused by `holm`; a right-sized input under wrong names — which `holm` structurally cannot
  see, since it reads only `len(family)` — is caught by a second post-call `_prove` against
  `HOLM_FAMILY`. Both cases are committed.
- **Commit:** `d5b8b5b`

### 5. [Rule 1 — Bug] Flat `descriptive`/`gated` flags on a comparison row are wrong about one half

- **Found during:** Task 2, writing the GREEN implementation against the RED test
- **Issue:** The RED test asserted `row["descriptive"] is True` on the comparison rows. That is
  false and the test was wrong: these four rows **are** the Holm family. Labelling them descriptive
  would make DD-03's "the sign test is the only inferential instrument" true by relabelling. But
  the bootstrap interval on the same row genuinely is descriptive.
- **Fix:** the interval became its own sub-record — `{"intervals", "label", "descriptive": True,
  "gated": False}` — and the comparison carries `descriptive: False, gated: True`. The test asserts
  both, with the reason. The RED test was corrected in the same commit as the implementation.
- **Commit:** `d5b8b5b`

### 6. Parameter renamed: `per_fact_by_arm` → `per_fact_by_family`

- **Found during:** Task 2
- **Issue:** The plan names `run_holm_family`'s parameter `per_fact_by_arm`, which is
  `persistence.fact_signs`'s parameter name for `{arm: {fact_id: row}}`. This phase's input needs a
  family axis above that — four comparisons, one per family — so the plan's name would describe the
  inner mapping while naming the outer one.
- **Fix:** `per_fact_by_family`, mapping each family to `{arm: {fact_id: row}}`. The docstring
  states that the inner mapping IS `fact_signs`'s parameter, so its pairing checks are inherited
  rather than restated.
- **Commit:** `d5b8b5b`

### Acceptance criteria reported rather than contorted

**The word "tolerance" is deliberately absent from the driver, including the docstring the action
asked for.** The plan's action text says to record that "a tolerance band is declined"; its own
acceptance criterion is `grep -cE "tolerance|atol=|band=" scripts/phase18_extraction.py` **returns
0**. Those cannot both be satisfied literally. The mechanical criterion wins, and the record the
prose criterion exists to preserve **is** present in `FAMILY_ZERO_CONSEQUENCE_LABEL` — "NO WIDTH IS
ALLOWED AROUND EITHER NUMBER ... the quantity has already reproduced EXACTLY ... Putting a width
around a quantity that reproduced exactly discards measured precision to buy a number whose value
nothing derives" — written without the one word the grep forbids. Measured: **0**.

**`family_zero_matches` returns three elements, not two.** The plan's behaviour block requires both
`(True, [])` and "the derived sum ... returned as a labelled consequence field". A 3-tuple
`(matches, mismatches, derived)` is the only shape satisfying both without splitting the function
in two; the test asserts `(matches, mismatches) == (True, [])` on the first two slots.

**Task 2's `test_holm_family_is_reachable` is untouched and still passes.** The new
`run_holm_family` tests are named `test_run_holm_family_*` so `-k holm_family` selects all of them
together, which is what the acceptance criterion checks.

**Zero deletions, both files.** `git diff 0576cc8..HEAD` reports **934 insertions and 0 deletions**;
no commit deleted a file; the pinned driver keeps the 0-removal property every plan in this phase
has maintained, verified with `git diff | grep '^-'` on both files.

### The three wave carry-forwards, checked and reported

- **144-cell admissibility key space (18-07).** Honoured by reference, never restated:
  `assemble_verdict` passes `zero_cells` straight through to `null_result_is_admissible` and never
  builds, narrows or re-derives a key set. `ADMISSIBILITY_ZERO_KEYS` is not read anywhere in this
  plan's code, and the self-check still prints **144**. **No conflict.**
- **`arm` on the scored record (18-08).** Load-bearing here and used as such: `run_holm_family`
  reads `per_fact_by_family[family][arm]` per arm and `fact_signs` compares the two, so the
  `ASR_on − ASR_off` contrast is structural. The handoff takes its base counts from `ARMS[1]` for
  the SAME family, never from a pooled base. **No conflict.**
- **D-29's f4-vs-f3 identity (18-06).** Nothing in this plan touches an NLL frame, a reduction or
  an exposure record. Exposure enters only as `zero_cells`, which this plan passes through
  unopened. There is no contrast to depend on and nothing was reinterpreted. **No conflict.**

## Verification

| Check | Result |
|---|---|
| `pytest -q` (full suite) | **707 passed, 7 skipped, 0 failed** in 128s |
| `pytest -q tests/test_phase18_prereg.py` | 22 passed (14 inherited + 8 new) in 1.1s |
| `pytest -q tests/test_phase18_{corpus,draws,docs,widenings}.py` | 36 passed — Waves 1–6's guards untouched |
| `pytest -q tests/test_phase16_prereg.py -k phase18` | 1 passed — the D-04 ancestry pin |
| `python scripts/phase18_extraction.py` | exit 0, self-check prints 144 cells, no model/checkpoint/device |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 161 files already formatted |
| `git diff --exit-code scripts/erasure_gate.py` | exit 0 — byte-untouched |
| `grep -cE "tolerance\|atol=\|band="` (driver) | **0** |
| `grep -c "sign_test_exact("` (driver) | **2** — `BEST_ACHIEVABLE_P` and `run_holm_family` |
| AST call sites of `sign_test_exact` | `["<module>", "run_holm_family"]` |
| `grep -cE 'holm\(.*family=HOLM_FAMILY'` | **1** |
| `grep -cE 'erasure_is_worth_attempting\('` | **1** |
| `ls results/phase18_*` | no matches — nothing here writes to disk |
| `git status --porcelain results/` | empty |
| Files deleted by any commit | **0** |
| Removals from either file | **0** across all six commits |

## Threat register disposition

| Threat ID | Disposition | Discharged by |
|---|---|---|
| T-18-09-01 (Repudiation — a matching aggregate over diverged questions) | mitigated | Row-for-row comparison on all 112; the sum-preserving mismatch is its own committed case and returns `False` naming both questions; the aggregate is returned under a label saying it asserts nothing |
| T-18-09-02 (Tampering — a width added after a near-miss) | mitigated | No width parameter exists; absence asserted off the *signature* against 8 spellings (`tol`, `atol`, `rtol`, `band`, `slack`, `within`, `epsilon`, `eps`), and the acceptance grep returns 0 |
| T-18-09-03 (Tampering — a second `sign_test_exact` call site) | mitigated | Call sites read off the AST and pinned at exactly `["<module>", "run_holm_family"]`; the grep count is 2 |
| T-18-09-04 (Repudiation — draw counts in a question-unit interface) | mitigated | `_handoff_counts` proves each denominator against a count DERIVED from the same aggregation; the 936-vs-104 case raises and names both numbers |
| T-18-09-05 (Tampering — a best-attack max chosen after reading the results) | mitigated | `BEST_ATTACK_RULE` is a module literal inside the ancestry-pinned file; `best_attack_family` proves the offered set equals `ATTACK_FAMILIES` (a max over a subset is a max over what someone submitted) and breaks ties by the pre-registered order — asserted deterministic at a 4-way tie |
| T-18-09-SC (Tampering — package installs) | accepted | Zero installs; `pyproject.toml` untouched |

## Issues Encountered

- **Worktree base drift, eighth consecutive plan.** HEAD was `829cd5f`, a strict ancestor of the
  required `0576cc8` with a clean tree, so `git merge --ff-only` corrected it with 0 commits lost.
- **The first `seed_index` reading was wrong and the probe caught it** — see Deviation 2. A
  per-fact index looked obviously right and produced 98 phantom mismatches against a control that
  is known to reproduce exactly. Measuring the join before writing the function is what stopped
  that becoming a "the control diverged" abort on the real run.
- **Four `ruff` E501s**, all in docstring first lines and f-string assertion messages; bound to
  locals or reflowed before their commits. No logic involved.

## Deferred Issues

None new. The one item in `deferred-items.md` is 18-04's and is untouched.

## Known Stubs

None. `grep -c "TODO\|FIXME\|placeholder"` returns **1** for the driver and **0** for the test
file; the single hit is 18-06's pre-existing use of "placeholder" at `phase18_extraction.py:1023`,
describing `ans1`'s `{v}` template token — the same one 18-07 and 18-08 reported. Every function
added here returns computed material and every one is exercised by a committed test.

## User Setup Required

None — no external service configuration required.

## Threat Flags

None. No new network endpoint, auth path or schema at a trust boundary. `parse_phase14_taught_rows`
adds one **read-only** file access to a tracked artifact (`results/phase14_recall_report.md`),
inside a function body and never at import — the driver's import-time callee register is a hard
equality and is unchanged. Nothing in this plan writes to disk, so `results/phase18_*` still does
not exist and every commit here remains a legitimate ancestor under D-04.

## Next Phase Readiness

- **The inferential layer is complete and CPU-testable.** `assemble_verdict` needs the family-zero
  scored rows, the gate's four condition inputs, one `aggregate_questions` result per (family, arm)
  on the gated tier, and the question-unit counts. It touches no model.
- **The dispatcher owes this function three things.** Family-zero rows covering **exactly** the 112
  committed taught questions (a 111-question control aborts by name). One `aggregate_questions`
  result per `(family, arm)` on `core_held_out` — 8 facts each, since `fact_signs` fixes n at
  `SIGN_TEST_N`. And question-unit counts whose denominators equal the tier's own question count,
  which `_handoff_counts` re-derives rather than trusts.
- **Phase 19's precondition is now reachable with the shape it pre-registered:**
  `erasure_is_worth_attempting` receives four ints selected by `BEST_ATTACK_RULE`, and the
  conclusion paragraph names the same family the handoff carries.
- **Still not built, by design:** the artifact writer, `main()`, the argument parser, the D-12
  pre-flight smoke, and the dispatcher pairing the corpus against the two arms.
- **Carried forward:** 18-06's `f4_reversed` ≡ `f3_bare` identity, 18-07's 144-cell key space and
  18-08's `arm` axis — all three checked against this plan above, all three still applying to
  whoever reports them.

## Self-Check: PASSED

- `scripts/phase18_extraction.py` — FOUND (2,993 lines; contains `def family_zero_matches`,
  `def parse_phase14_taught_rows`, `def run_holm_family`, `def assemble_verdict`,
  `def best_attack_family`, `BEST_ATTACK_RULE`, `PHASE14_TAUGHT_REPORT`)
- `tests/test_phase18_prereg.py` — FOUND (1,515 lines, ≥360 required; 22 tests, 8 of them this plan's)
- `b76ca7d`, `8a7c08f`, `53c3fc9`, `d5b8b5b`, `3439979`, `dd70fd6` — all FOUND in `git log`
- TDD gate sequence intact: a `test(...)` commit precedes a `feat(...)` commit for each of the three tasks
- `git status --short` clean apart from this SUMMARY
- No `STATE.md`, `ROADMAP.md` or `REQUIREMENTS.md` touched — the orchestrator owns them
- No file deleted by any commit; zero removals from either file

---
*Phase: 18-black-box-adversarial-extraction-audit*
*Completed: 2026-08-16*
