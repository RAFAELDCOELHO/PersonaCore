---
phase: 18-black-box-adversarial-extraction-audit
plan: 07
subsystem: evaluation
tags: [admissibility, pre-registration, threat-model, generated-prose, honest-negatives, cpu-only]

# Dependency graph
requires:
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-03's D-04 pin — `VERDICTS`, `CONTROL_FAILED_REASON`, `ATTACK_FAMILIES`, `FAMILY_ZERO`, `ARMS`, `K`, `GATED_TIER`, `_prove`, the INVERTED lazy-import rule"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-05's `CORPUS_TIERS` and the `_corpus_entry` ordered-schema pattern"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-06's `exposure_rank` / `value_span_nll` — the instruments condition four's evidence comes from"
  - phase: 15-selective-erasure-preregistration
    provides: "`erasure_gate.erasure_succeeded` (the shape mirrored), `wilson_upper_bound`, `rule_of_three`, `VERDICTS` — byte-untouched at 23a830c"
  - phase: 16-persistence
    provides: "`licensed_headline` — the generated-prose mechanism, and `phase16_persistence.recall` as the already-imported route to the decode settings"
provides:
  - "`null_result_is_admissible` — D-27's four conditions, keyword-only, INCONCLUSIVE-precedence, five committed all-fail branches"
  - "`ADMISSIBILITY_ZERO_KEYS` — Pitfall 3's quantification set as a DERIVED 144-cell tuple, plus `CORE_SLOTS`, `ADMISSIBILITY_FAMILIES`, `ADMISSIBILITY_CELL_KEYS`"
  - "`ATTACKER_HAS` / `ATTACKER_LACKS` / `THREAT_MODEL_ASYMMETRY` — D-24's threat model as module literals with the run's own numbers interpolated"
  - "`licensed_conclusion` / `LOWER_BOUND_SENTENCE` / `LORA_PROPERTY_CAVEAT` — the closing paragraph generated from those literals, with three `_prove`s on the PRODUCED text"
  - "`_self_check` + `__main__` — model-free, checkpoint-free, device-free"
  - "`tests/test_phase18_docs.py` (new) and two new guards in `tests/test_phase18_prereg.py`"
affects: [18-08, 18-10, 18-12, 18-14]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A quantification set pre-registered as a DERIVED IMMUTABLE tuple, with the gate asserting its input COVERS it — coverage, not membership, because a subset is exactly what narrow scoping produces"
    - "A hard-equality import-time callee register WIDENED by a reviewed commit rather than worked around — the two new entries are inert and each carries its justification inline"
    - "A mutation proof executed against a scratchpad COPY of the pinned file, so a failed proof cannot leave the pin edited"

key-files:
  created:
    - tests/test_phase18_docs.py
  modified:
    - scripts/phase18_extraction.py
    - tests/test_phase18_prereg.py

key-decisions:
  - "`ADMISSIBILITY_ZERO_KEYS` is the four-axis product MINUS `(FAMILY_ZERO, GATED_TIER)` — 144 cells, not 160. Family zero spends its 9 draws on the 112 TAUGHT rows only, so demanding 16 held-out A0 cells would make condition four unsatisfiable at every possible outcome"
  - "`zero_cells` carries EVERY cell as `{successes, exposure_rank}`, not a caller-chosen mapping of the zeros — a caller who decides which cells are zeros decides what the gate quantifies over, which is the one thing Pitfall 3 takes away from the caller"
  - "`CORE_SLOTS` is a module literal pinned against `factset.LOCKED_FACTS` by a committed test; the LAZY-IMPORT RULE forbids the module-scope import that would derive it"
  - "`LEAKAGE_DEMONSTRATED, NULL_ADMISSIBLE, INCONCLUSIVE = VERDICTS` — tuple unpacking, so no return site retypes a verdict string and a fourth verdict is a visible edit to the pre-registration"
  - "Schema violations `_prove` (SystemExit); measurement deficiencies return INCONCLUSIVE. A caller bug is not a finding about the run"
  - "P18-4's erroneous release sentence is PARAPHRASED in the correcting comment, never quoted — a quoted-then-corrected sentence is still that sentence in the file, and the acceptance grep is mechanical"

patterns-established:
  - "`_self_check()` as a named function called from `if __name__ == '__main__'` — keeps `erasure_gate`'s runnable self-check while adding exactly one name to the module-scope callee register"

requirements-completed: [ATK-05, ATK-06, STAT-05]

# Metrics
duration: ~35min
completed: 2026-08-15
---

# Phase 18 Plan 07: The Admissibility Gate and the Threat-Model Prose Summary

**The branch that refuses to publish a comfortable null is now committed, with all five of its
INCONCLUSIVE paths exercised, its quantification set derived at 144 cells rather than trusted, and
the report's closing paragraph generated from the same two literals the run will obey.**

## Performance

- **Duration:** ~35 min end to end; the five task commits span **8m30s** (23:08:58 → 23:17:28).
- **Tasks:** 3, five commits (two TDD RED/GREEN pairs plus Task 2).
- **Files:** 3 — **477 insertions / 0 deletions** in the pinned driver, **238 / 4** in
  `test_phase18_prereg.py`, **177 / 0** for the new `test_phase18_docs.py`.
- **Suite:** **688 passed / 7 skipped / 0 failed** in 126s. The arithmetic is the predicted
  worktree delta exactly: `690 (main after Wave 4) − 6 worktree-only skips + 4 new tests = 688`.

## Task Commits

1. **Task 1 RED** — five INCONCLUSIVE cases, the vacuity case, the D-28 AST proof — `ccc9171` (test)
2. **Task 1 GREEN** — `null_result_is_admissible`, the 144-key set, `_self_check` — `836409a` (feat)
3. **Task 2** — D-24's two column lists and the corrected asymmetry — `bdc36ad` (feat)
4. **Task 3 RED** — the templated-conclusion test and the mask cross-check — `f7d0d32` (test)
5. **Task 3 GREEN** — `licensed_conclusion` and its three text-level `_prove`s — `84241d7` (feat)

## Accomplishments

- **The all-fail branch exists before the number does, and every path has been watched fire.**
  Five INCONCLUSIVE branches — control, budget, base arm, coverage, exposure — each with a case in
  `test_admissibility_precedence` AND in the `__main__` self-check. `erasure_succeeded`'s four
  structural properties are copied exactly: keyword-only `*` (a positional call raises `TypeError`,
  asserted), every INCONCLUSIVE branch returning before any bound, `reasons` accumulated in order,
  and a single closing ternary. "Returns before any bound" is proved **off the function's own AST
  subtree** — zero `wilson_upper_bound`/`rule_of_three` callees inside it — because a bound computed
  on an early path is invisible to any number of black-box cases.
- **Pitfall 3 is closed by an immutable derived set, not by a promise.** `ADMISSIBILITY_ZERO_KEYS`
  is the product of `CORE_SLOTS` × `ADMISSIBILITY_FAMILIES` × `ARMS` × `CORPUS_TIERS`, rebuilt
  independently in the test and asserted equal. The vacuity case — a grid missing one cell where
  every supplied cell carries a rank — returns INCONCLUSIVE and **names the uncovered key**. A
  coverage-blind gate returns `NULL_ADMISSIBLE` on that input, which is the whole reason the case
  is committed.
- **`scripts/erasure_gate.py` is byte-untouched.** `git diff --exit-code` returns 0 and
  `test_erasure_gate_untouched` is green at both levels (history: one commit; content: bytes on
  disk equal bytes at `23a830c`). Both bounds are imported from it — `grep -c
  "wilson_upper_bound\|rule_of_three"` returns **2**, `grep -c "def wilson_upper_bound\|def
  rule_of_three"` returns **0**.
- **The conclusion cannot state a scope the run did not obey.** Proved by MUTATION, not by
  inspection: a sentinel appended to `ATTACKER_LACKS` appears in the rendered text. Both required
  sentences being present would prove only that someone typed them once.
- **The zero is never bare.** At `successes=0, n_questions=104` the output carries the count, the
  denominator, the Wilson upper bound (**2.54%**) and the rule-of-three ceiling (**3/104 =
  2.88%**), and `re.search(r"\b0(\.0+)?%", text)` finds nothing. That last check runs on the
  PRODUCED TEXT, because a source-level scan structurally cannot see a number a format string made.
- **P18-4's unverified release claim does not enter the pin.** `THREAT_MODEL_ASYMMETRY` states the
  black-box floor and the adapter's portability and explicitly declines the publication claim;
  `grep -c "already shipped weights on a GitHub Release\|shipped weights on a GitHub release"`
  returns **0**.

## Measurements

Every number below is an **instrument-shape measurement** over committed constants — no model, no
checkpoint, no device is involved anywhere in this plan. None of them is a finding about the model.

### The quantification set (Task 1 acceptance)

```
axis                       members
CORE_SLOTS                       8
ADMISSIBILITY_FAMILIES           5   (A1-mild, A1-aggressive, A2, A3, A0)
ARMS                             2
CORPUS_TIERS                     2
naive product                  160
minus (A0, core_held_out)      -16   family zero runs on the 112 TAUGHT rows only
ADMISSIBILITY_ZERO_KEYS        144
```

### The rendered zero-success conclusion (Task 3 acceptance, `python -c`, exit 0)

```
Wilson upper bound (0/104)   2.54%
rule of three                3/104 = 2.88%
bare-zero regex              no match
closes on                    "...this is a lower bound on leakage, never an upper bound on privacy."
adjacent sentence            LORA_PROPERTY_CAVEAT (ATK-06), present
```

### The mutation proof (Task 3 acceptance)

Run against a **scratchpad copy** with the caveat deleted from the template — the tracked file is
read and never written, so a failed proof cannot leave the pin edited. `sha256` of
`scripts/phase18_extraction.py` before and after: `9997ca1475d78e32…` both times, `git status`
clean.

```
MUTANT written — LoRA caveat removed from the template; phase18_extraction.py untouched
SystemExit RAISED:
[phase18_extraction] PROOF FAILED: the rendered conclusion does not carry ATK-06's caveat,
which D-24 requires ADJACENT to the closing sentence...
```

### `cannot` / `impossible` review (Task 2 acceptance criterion 4)

`grep -c "cannot\b\|impossible"` returns **27**, of which **9 are this plan's** (lines 1445, 1529,
1550, 1585, 1633, 1747, 1750, 1758, 1842). Every one is a statement about **code or instrument
behaviour** — what a keyword-only signature stops a caller writing, what a source scan cannot see,
what a tuple unpacking makes impossible to write. **None appears inside a claim about leakage,
privacy or extraction**, which is P18-4's actual warning: the failure mode is "the adapter cannot
leak", not the word itself. The 18 inherited occurrences were re-read and are the same category.

## Deviations from Plan

### 1. [Rule 1 — Bug] The literal four-axis product makes condition four unsatisfiable at every outcome

- **Found during:** Task 1
- **Issue:** The action text specifies the product of "the 8 core slots, the family tuple including
  `FAMILY_ZERO`, `ARMS` and the two tiers" — 160 keys. But family zero is **taught-tier only**:
  D-01 asserts its exact hit vector against the 112 committed taught rows, the budget comment
  spends exactly 112 prompts on it, and `results/phase16_recall_sample.json` records
  `core_taught: 112` against `core_held_out: 104`. So 16 of those 160 keys name cells no arm will
  ever measure, the coverage check can never pass, and `null_result_is_admissible` returns
  INCONCLUSIVE at **every possible outcome** — Pitfall 4's arithmetically-dead gate arriving as a
  coverage requirement instead of as an alpha, and undetectable until the 8.2h run was spent.
- **Fix:** one derived exclusion, `if not (family == FAMILY_ZERO and tier == GATED_TIER)`, reading
  the two constants rather than hard-coding the pair; the reason is recorded in the comment above
  the set. The test rebuilds the same product independently, asserts the count is 144, asserts the
  set is a `tuple` (a list or set could be narrowed at runtime by exactly the code the coverage
  check exists to catch), and asserts no `(A0, core_held_out)` key survives.
- **Files:** `scripts/phase18_extraction.py`, `tests/test_phase18_prereg.py`
- **Commit:** `836409a`

### 2. [Rule 2 — Missing critical functionality] `zero_cells` carries every cell, not the caller's chosen zeros

- **Found during:** Task 1
- **Issue:** Read literally, a parameter named `zero_cells` holds only the zeros — and then the
  coverage check is over a set **the caller selected**. That is Pitfall 3 restated, not solved: a
  caller who decides which cells count as zeros decides what the gate quantifies over.
- **Fix:** `zero_cells` maps every pre-registered key to `{"successes", "exposure_rank"}` and the
  gate derives the zeros itself. The cell schema is `_prove`d as an ordered hard equality, the same
  mechanism `_corpus_entry` and `_exposure_record` already use. Coverage is checked BEFORE the
  ranks, because asking "are all the supplied zeros ranked?" of a narrowed set answers yes.
- **Commit:** `836409a`

### 3. [Rule 3 — Blocking] The import-time callee register had to widen by two reviewed entries

- **Found during:** Task 1
- **Issue:** `test_nothing_loads_at_import` is a HARD EQUALITY over module-scope callees, and its
  walk reads an `if` body as module scope (that is how it sees the `sys.path` bootstrap). Both of
  this plan's requirements collide with it: `ADMISSIBILITY_ZERO_KEYS` must be a module-level
  default argument, and the `__main__` self-check's calls are module-scope by that definition.
- **Fix:** the self-check body moved into a named `_self_check()` so the guard block contributes
  exactly one name, and two entries added with inline justification — `tuple` (a pure display; a
  list would be mutable and a set unordered) and `_self_check` (behind `__name__`, runs on no
  import). Neither admits a load: every call nested inside them would appear in the same walk under
  its own name, so a `torch.load` still turns the register red. This is the register working as
  designed — it widens by a reviewed commit — rather than being routed around.
- **Commit:** `836409a`

### 4. [Rule 2 — Missing critical check] `CORE_SLOTS` is a literal, so it is pinned against the fact set

- **Found during:** Task 1
- **Issue:** The eight slot names cannot be derived at module scope — the LAZY-IMPORT RULE forbids
  reaching `phase14_factset` there, and D-03's static scan is the reason. An unpinned transcription
  would silently narrow the grid and leave every case in the precedence test green over it.
- **Fix:** `CORE_SLOTS` is asserted equal to `tuple(fact.slot for fact in factset.LOCKED_FACTS)` in
  fixture order, at the TOP of `test_admissibility_precedence` — before the cases that are built
  from it. `SPREAD_ZERO_CONTROL_SLOTS ⊆ CORE_SLOTS` is asserted alongside. Slot names are schema,
  not fact material (D-11 already publishes `slot` in the corpus), and
  `test_no_fact_values_in_phase18_modules` is green.
- **Commit:** `836409a`

### 5. [Rule 1 — Bug] The correcting comment quoted the sentence it was correcting

- **Found during:** Task 2, running the acceptance grep
- **Issue:** The first draft explained the P18-4 correction by quoting the erroneous sentence
  verbatim inside the comment. `grep -c "already shipped weights on a GitHub Release"` returned
  **1** against a criterion of 0. The criterion is right and the draft was wrong: a
  quoted-then-corrected sentence is still that sentence in the pinned file, and a later reader
  grepping the pin for the claim finds a hit.
- **Fix:** paraphrased — "P18-4 asserts as fact that v1.0's weights were published as a release
  asset; that sentence is deliberately not reproduced here" — with the audit citation intact. Grep
  now returns **0**.
- **Commit:** `bdc36ad`

### 6. [Rule 2 — Missing critical check] The mask literal had nothing checking it

- **Found during:** Task 2
- **Issue:** `K`, the temperature, the top-p and the injection fraction are all interpolated from
  the constants the run reads, so they move with it. The mask size cannot be: `7,645 of 8,192` is a
  count over a LOADED tokenizer (`resolve_forbid(tok, vocab_size)`), available to no import-time
  constant. A literal nothing checks is the exact drift D-24 exists to prevent.
- **Fix:** `test_threat_model_numbers_match_the_committed_run` cross-checks the masked count, the
  vocab size and the derived 547 live ids against `results/phase16_arm_adapter-only.json` — a
  tracked artifact from Phase 16's own run — and re-asserts the interpolated decode settings are
  still present. Added to Task 3's file because Task 2's `files` list is the driver alone.
- **Commit:** `f7d0d32`

### 7. Mutation proof run against a copy rather than the tracked file

- **Found during:** Task 3
- **Issue:** The acceptance says "delete the LoRA caveat sentence, observe the `_prove` raise
  `SystemExit`, restore byte-identically". Editing the ancestry-pinned driver in place and relying
  on a restore step leaves a window in which a crashed or interrupted proof leaves the pin edited.
- **Fix:** the mutation is applied to a scratchpad COPY which is then loaded by `importlib`. The
  proof is identical in strength — it answers exactly "does deleting the caveat make the `_prove`
  fire?" — and the pin is read-only throughout, so "restore byte-identically" is satisfied by never
  having written to it. `sha256` verified equal before and after.

### The D-29 carry-forward, checked and reported

The wave brief flags that 18-06 measured D-29's f4-vs-f3 frame separation as **unobtainable** and
warns against building a gate branch on it. **This plan's text does not assume that contrast
exists, and no branch here depends on it.** Condition four reads an exposure **rank**, which
`measure_exposure` computes under the single admissible `(ans1, mean)` pair; the three frames enter
nowhere in `null_result_is_admissible`, `licensed_conclusion` or either literal. There is no
conflict to reinterpret and nothing was silently adjusted.

### Acceptance criteria reported rather than contorted

**The four deleted lines are all in the test file, none in the pin.**
`git diff 5cc7222 HEAD -- scripts/phase18_extraction.py | grep '^-'` returns **nothing** — the
pinned driver keeps its 0-deletion property across all five commits. The four `-` lines in
`tests/test_phase18_prereg.py` are two comment/docstring passages reworded in place to describe the
guards this plan added (the module docstring's item 4 became items 4–6; the callee register's
"the other three" became "three more"). No assertion, guard or pre-registered constant was removed.

**`test_admissibility_precedence` carries 8 verdict cases plus the TypeError**, against a criterion
of "at least 7": positional call, control, budget, base arm, missing rank, coverage vacuity,
NULL_ADMISSIBLE and LEAKAGE_DEMONSTRATED — plus the AST proof that no bound is computed inside.

**The sibling half of `test_instruments_are_inside_the_pin` is currently vacuous** and is written
anyway: the `phase18_*.py` glob matches one file today, so the "no sibling defines admissibility
logic" loop has nothing to iterate. It arms itself on the commit that adds a second driver, which
is the whole point of the Phase 17 D-21 glob register. `_EXTRACTION_PATH in _GATE_MODULES` is
asserted so a glob that stopped matching the pin could not make the *first* half vacuous too.

## Verification

| Check | Result |
|---|---|
| `pytest -q` (full suite) | **688 passed, 7 skipped, 0 failed** in 126s |
| `pytest -q tests/test_phase18_prereg.py` | 6 passed (4 inherited + 2 new) |
| `pytest -q tests/test_phase18_docs.py` | 2 passed |
| `python scripts/phase18_extraction.py` | exit 0, no traceback, no model/checkpoint/device |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 161 files already formatted |
| `git diff --exit-code scripts/erasure_gate.py` | exit 0 — byte-untouched |
| `grep -c "wilson_upper_bound\|rule_of_three"` | **2** (≥2 required) |
| `grep -c "def wilson_upper_bound\|def rule_of_three"` | **0** |
| `grep -c "…shipped weights on a GitHub Release…"` | **0** |
| `len(ATTACKER_HAS)` / `len(ATTACKER_LACKS)` | **8 / 8** (≥8 each); "cross-persona", "membership inference", "relearning", "7,645" all present |
| `git status --porcelain results/` | empty; `ls results/phase18_*` → no matches |
| Files deleted by any commit | **0** |
| Removals from `scripts/phase18_extraction.py` | **0** across all five commits |

## Threat register disposition

| Threat ID | Disposition | Discharged by |
|---|---|---|
| T-18-07-01 (Repudiation — a comfortable null publishes itself) | mitigated | Four conditions, five INCONCLUSIVE branches, each with a committed test case AND a self-check case |
| T-18-07-02 (Tampering — "every zero" passes vacuously) | mitigated | `ADMISSIBILITY_ZERO_KEYS` derived, immutable, rebuilt independently in the test; coverage checked before ranks; the vacuity case is its own assertion |
| T-18-07-03 (Spoofing — two transposed counts invert the verdict) | mitigated | Keyword-only signature; `pytest.raises(TypeError)` on a positional call; units stated in the docstring for the three draw counts that share a type |
| T-18-07-04 (Repudiation — the report claims a wider threat model) | mitigated | `licensed_conclusion` renders `ATTACKER_HAS`/`ATTACKER_LACKS` at call time; propagation proved by monkeypatch; arm, tier and family names refused at the source |
| T-18-07-05 (Repudiation — P18-4's unverified release claim inherited) | mitigated | `THREAT_MODEL_ASYMMETRY` states the asymmetry and explicitly declines the claim; the acceptance grep returns 0, including inside comments |
| T-18-07-06 (Tampering — a late edit to `erasure_gate.py`) | mitigated | `git diff --exit-code` clean; `test_erasure_gate_untouched` green at both history and content level |
| T-18-07-SC (Tampering — package installs) | accepted | Zero installs; `pyproject.toml` untouched |

## Issues Encountered

- **Worktree base drift, sixth consecutive plan.** HEAD was `829cd5f`, a strict ancestor of the
  required `5cc7222` with a clean tree, so `git merge --ff-only` corrected it with 0 commits lost.
- **One `ruff` E501** in the new test file, in an f-string assertion message; bound to a local
  before its commit. Two `ruff format` reflows, both in the driver's new literals.

## Deferred Issues

None new. The one item in `deferred-items.md` is 18-04's and is untouched.

## Known Stubs

None. `grep -c "TODO\|FIXME\|placeholder"` returns **1** for the driver and **0** for both test
files; the single hit is 18-06's pre-existing use of the word "placeholder" in `_frame_preamble`'s
docstring, describing `ans1`'s `{v}` template token. Every function added here returns computed
material and every one is exercised by a committed test and by the `__main__` self-check.

## User Setup Required

None — no external service configuration required.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema at a trust boundary.
`ADMISSIBILITY_CELL_KEYS` is a new in-memory schema; nothing in this plan writes to disk, so
`results/phase18_*` still does not exist and every commit here remains a legitimate ancestor under
D-04.

## Next Phase Readiness

- **The gate and the prose are both callable and both CPU-testable.** `null_result_is_admissible`
  needs a 144-cell grid, `attack_successes` in the QUESTION unit and three per-arm draw counts;
  `licensed_conclusion` needs the successes, the denominator, the arm, the tier and the families.
  Neither touches a model.
- **The dispatcher owes the gate a full grid.** Condition four is unsatisfiable unless the run
  records a `{successes, exposure_rank}` cell for all 144 keys — including the adapter-off arm and
  family zero on the taught tier. A dispatcher that records only the attack arm, or only the zeros
  it noticed, will get INCONCLUSIVE and deserve it.
- **`erasure_is_worth_attempting` is now reachable** with the shape it pre-registered:
  `licensed_conclusion`'s `successes`/`n_questions` are the question-unit counts it consumes, and
  D-27's post-hoc max over families is already pre-registered by `ERASURE_DECISION_RULE`.
- **Still not built, by design:** the artifact writer, `main()`, the argument parser, the D-12
  pre-flight smoke, and the dispatcher pairing the corpus against the two arms.
- **Carried forward:** 18-06's `f4_reversed` ≡ `f3_bare` identity is untouched by this plan and
  still applies to anyone reporting the three frames as three independent columns.

## Self-Check: PASSED

- `scripts/phase18_extraction.py` — FOUND (1,913 lines; contains `def null_result_is_admissible`,
  `def licensed_conclusion`, `def _self_check`, `ATTACKER_HAS`, `ADMISSIBILITY_ZERO_KEYS`)
- `tests/test_phase18_prereg.py` — FOUND (520 lines, ≥200 required; 6 tests, 2 of them this plan's)
- `tests/test_phase18_docs.py` — FOUND (177 lines, ≥60 required; 2 tests)
- `ccc9171`, `836409a`, `bdc36ad`, `f7d0d32`, `84241d7` — all FOUND in `git log`
- `git status --short` clean apart from this SUMMARY
- No `STATE.md`, `ROADMAP.md` or `REQUIREMENTS.md` touched — the orchestrator owns them
- No file deleted by any commit; zero removals from the pinned driver

---
*Phase: 18-black-box-adversarial-extraction-audit*
*Completed: 2026-08-15*
</content>
</invoke>
