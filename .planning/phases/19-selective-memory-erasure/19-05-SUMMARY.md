---
phase: 19-selective-memory-erasure
plan: 05
subsystem: testing
tags: [pre-registration, descriptive-not-gated, one-verdict-path, parity, report-text, d8, q74, q78, erase-01, stat-02, stat-05, stat-06]

requires:
  - phase: 19-selective-memory-erasure
    provides: "19-01's open pin (`scripts/phase19_erasure.py`), its ARMED ancestry guard and `ablate_components`/`component_index`"
  - phase: 19-selective-memory-erasure
    provides: "19-02's `TARGET_SLOT`, `N_TARGET_QUESTIONS = 27`, `BEST_ATTAINABLE_TARGET_BOUND` and the armed fact-value source scan"
  - phase: 19-selective-memory-erasure
    provides: "19-03's `lock_erasure_floor`, `literal_phase14_floor` and `floor_branch`"
  - phase: 19-selective-memory-erasure
    provides: "19-04's `dialogue_cap`, `GATED_NONTARGET_SLOTS`, `ARM_CONFIG_KEYS` and `FORBID_IDS_SHA256`"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "`results/phase18_arm_adapter-on.json`, `results/phase18_corpus.json`, `K`/`ASR_RUNGS`, `canonical_json`+`corpus_sha256`"
provides:
  - "DESCRIPTIVE_ONLY_FUNCTIONS + delta_w_cells / delta_w_cosine / fisher_overlap + REPRESENTATIONAL_READ_LABEL"
  - "render_verdict — the ONE erasure_succeeded call site in the phase"
  - "PARITY_KEYS (8) + phase18_parity_values() + phase18_parity_config() + assert_phase18_parity()"
  - "PHASE18_RECORDED_PARITY_KEYS / PHASE18_INHERITED_PARITY_KEYS — the measured 4-of-8 gap"
  - "ERASURE_SHIP_PENDING_LINE / ERASURE_SHIP_RECORDED_LINE + ERASURE_SHIP_DECISIONS + append_ship_decision()"
  - "render_report() + ERASURE_REPORT_PATH + assert_erasure_report_not_clobbered()"
  - "D8_PUBLICATION_POSTURE — the unsoftened branch AND Q7.4's easy branch, both framed pre-number"
affects: [19-06, 19-07, 19-13, 19-14, 19-16]

tech-stack:
  added: []
  patterns:
    - "write the AST guard as a PURE function over a source string, then drive it twice — clean on the real file, dirty on a synthetic mutant — so non-vacuity is a committed property rather than a claim in a summary"
    - "when a blanket text assertion (`\"Phase 18\" not in report`, `\"force\" not in source`) fails on CORRECT code, the assertion is wrong, not the code: replace it with the structural property (a marker LINE, a parameter name), never widen the code to fit it"
    - "a helper whose committed return type cannot support the operation the plan prescribes is a falsification: delegate the part it does own and cross-check the part you had to build"

key-files:
  created: []
  modified:
    - scripts/phase19_erasure.py
    - tests/test_phase19_erasure.py

key-decisions:
  - "`extract_deltas.adapter_cells` returns a per-cell Frobenius-norm RATIO (a scalar), so the plan's `delta_w_cosine` over its output is undefined — `delta_w_cells` DELEGATES the ratio and builds the direction from `MECHANISM_RULE`'s own `dW = scale * (B @ A)`, with a committed test asserting `||delta||_F / ||W0||_F` equals the delegated ratio per cell"
  - "the not-gated scan forbids ANY ordering comparison and ANY module-level number inside the three functions, which is strictly stronger than the plan's `Compare`-scoped wording and is what catches the plan's own prescribed `if cosine > 0.5` mutation; it bit on its first run against an innocent `PRODUCTION_RANK` interpolation, and the CODE moved rather than the guard"
  - "Phase 18's committed config records 4 of the 8 parity keys, not 8 — measured; the plan's `<done>` ('passes on the committed Phase 18 arm record's own config block') is false as written, and `assert_phase18_parity(phase18_config)` correctly RAISES naming `asr_rungs`"
  - "`ARM_CONFIG_KEYS` EXTENDED with the four sampling columns so `PARITY_KEYS` is a subset of it — a Phase 19 reader never has to reconstruct what Phase 18 forced us to reconstruct"
  - "`assert_phase18_parity` is scoped to the arms compared against Phase 18, explicitly NOT the (b) noise-floor replicate whose stride is offset ON PURPOSE — recording a stride and asserting it matches another phase's are different acts, and Phase 18 did neither"
  - "the ship-decision rewrite is conditional on a pinned DECISION LINE from a closed set, not on the word 'ship': W2's own grep found ship/no-ship language already in the report while no decision had been written, so a substring check would have passed the defect it exists to catch"
  - "`render_verdict` reads the gate's required argument names off `erasure_succeeded` itself via `inspect`, so the driver holds no copy of the rule's signature"

patterns-established:
  - "three refusals with three different messages where `_verdict.recorded_verdict` returns None / an empty body / a body — the clobber guard names WHICH situation it refused, because 'not this writer's file' and 'an interrupted render' have different recoveries"
  - "every rate in the report goes through Phase 16's `report_proportion`, IMPORTED, so a bare `0%` is impossible by construction and the final proof over the produced bytes is a second layer rather than the only one"

requirements-completed: []

duration: 70min
completed: 2026-08-17
---

# Phase 19 Plan 05: Descriptive-Not-Gated, One Verdict Path, Phase 18 Parity — Summary

**The three structural failure modes are closed by scans that were driven against mutants in the
same commit that closed them — and the parity work measured that Phase 18 recorded only FOUR of the
eight comparability parameters, so the plan's own `<done>` criterion was false and the honest
version raises on the committed config rather than passing over it.**

## Performance

- **Duration:** ~70 min
- **Tasks:** 3 of 3 (TDD, RED then GREEN each)
- **Files modified:** 2 (0 created, 2 modified)
- **Tests:** +15 (783 -> 798 passed, same single pre-existing CUDA-only skip)

## Accomplishments

- Representational consistency **cannot** become a gate: an AST scan over `DESCRIPTIVE_ONLY_FUNCTIONS`
  refuses `sign_test_exact` / `holm` / `wilson_upper_bound`, any ordering comparison, and any read
  of a module-level number — and a dangling entry fails rather than excusing a missing target.
- Exactly **one** verdict path exists (`render_verdict`), it is the committed object by identity, and
  none of the four v2.0 baselines appears as a numeric literal anywhere in the pin (measured: 0 hits).
- Every comparability parameter is asserted against Phase 18's own value, with the corpus digest
  RECOMPUTED through the committed pair and the four Phase 18 never recorded reconstructed from
  their owning modules — with an AST census proving no Phase 18 call site overrides them.
- The report text, the marker pair and the clobber guard landed, and the Phase 18 W2 defect is
  closed by making the placeholder rewrite conditional on a real decision.
- `git ls-files 'results/phase19_*'` is still **EMPTY** (verified 0 at start, after every commit,
  and at end).

## Task Commits

1. **Task 1 RED** — `a079913` (test): the two AST guards + 3 behavioural tests, all 5 failing
2. **Task 1 GREEN** — `99ed828` (feat): the three descriptive functions, the label, `render_verdict`
3. **Task 2 RED** — `e6eab23` (test): 5 failing parity tests, incl. 8 mutations + 8 deletions
4. **Task 2 GREEN** — `c695cef` (feat): `PARITY_KEYS`, `assert_phase18_parity`, `phase18_parity_config`
5. **Task 3 RED** — `ab465da` (test): 5 failing tests for the report, the pair, the clobber guard
6. **Task 3 GREEN** — `c8772ef` (feat): `render_report`, the marker pair, `append_ship_decision`, D8

## Files Created/Modified

- `scripts/phase19_erasure.py` (modified, 1612 -> 2365 lines) — three new sections. Module docstring
  updated to 19-05 with a new "WHY THE REPRESENTATIONAL READ IS STRUCTURAL" paragraph.
  New imports: `re`, `torch`, `_addendum`, `_verdict`, and `erasure_succeeded` / `rule_of_three` /
  `VERDICTS` from `erasure_gate`.
- `tests/test_phase19_erasure.py` (modified, 1912 -> 2707 lines) — 15 new tests, all CPU-only.

## Evidence

### The two guards, resolved and located

```
$ .venv/bin/python - <<'PY' ... ast over scripts/phase19_erasure.py
DESCRIPTIVE_ONLY_FUNCTIONS: ('delta_w_cells', 'delta_w_cosine', 'fisher_overlap')
   delta_w_cells    defined in pin: True   callable: True
   delta_w_cosine   defined in pin: True   callable: True
   fisher_overlap   defined in pin: True   callable: True
erasure_succeeded call sites in the pin: ['render_verdict']
erasure_succeeded is the committed object: True
```

### The four v2.0 baselines are not typed anywhere — measured BEFORE writing the guard

```
V20_MASKED_DIALOGUE_VAL_PPL = 4.5733: 0 literal hit(s)
V20_EWC_RETENTION_PPL = 3.89114:       0 literal hit(s)
V20_RETENTION_NOISE_FLOOR = 0.06893:   0 literal hit(s)
MARGIN_K = 2:                          0 literal hit(s)
```

The `MARGIN_K = 2` row is the one that mattered: an int literal `2` anywhere in the pin would have
made the plan's ban unsatisfiable. It is genuinely absent, so the ban shipped as written.

### The Phase 18 parity gap, measured rather than assumed

```
PARITY KEY           IN PHASE 18 CONFIG?
corpus_sha256        RECORDED: 'ff8e6e3c24987ac393cc262233f1b0bfdad5dc11eefa4cc1224a164cfd0…'
forbid_ids_sha256    RECORDED: '79b55770f4dcfa943d7528cb04829e8d2e7dd8823b9b5450da418b4fcf3…'
k                    RECORDED: 48
asr_rungs            ABSENT
stop_ids             ABSENT
sample_temperature   ABSENT
sample_top_p         ABSENT
seed_stride          RECORDED: 'seed_index * K for the attack families; unstrided for famil…'

recorded: 4 of 8
```

```
assert_phase18_parity(phase18 config) -> PROOF FAILED: the arm config does not record 'asr_rungs'
assert_phase18_parity(phase18_parity_config(rec)) -> PASSES: True
PARITY_KEYS subset of ARM_CONFIG_KEYS: True (8/10)
```

### The four unrecorded parameters ARE the ones Phase 18 ran under — AST census, not assertion

```
phase14_recall.draw_all:   ['SAMPLE_TEMPERATURE', 'SAMPLE_TOP_P']
phase14_recall._complete:  ['STOP_IDS']

phase18_extraction:3176 recall.draw_all(...)          keywords=['n_samples']
phase18_extraction:3634 recall.draw_all(...)          keywords=['n_samples']
phase18_extraction:3668 recall.complete_question(...) keywords=['index']
```

Not one sampling override at any of the three call sites, so the reconstruction is a reading of
what Phase 18 ran under rather than a value invented to make a check pass.

### The corpus digest is over the WHOLE artifact, measured before it was wired

```
prompts e6e775bb5df6fdf61d9fa44adacfb71e3a5bb7ba510403562da3de0ec9ea977e False
whole   ff8e6e3c24987ac393cc262233f1b0bfdad5dc11eefa4cc1224a164cfd0f7d67 True
```

`corpus_sha256` is taken over the `{entry_keys, prompts, source_fixture}` object, not over
`["prompts"]`. Guessing would have produced a check that was red for a reason unrelated to drift.

### The plan's verification commands

```
$ .venv/bin/python -m pytest -q tests/test_phase19_erasure.py -k "descriptive or verdict" -x
6 passed, 50 deselected in 0.61s

$ .venv/bin/python -m pytest -q tests/test_phase19_erasure.py -k parity -x
5 passed, 56 deselected in 0.90s

$ .venv/bin/python -m pytest -q tests/test_phase19_erasure.py tests/test_phase19_docs.py \
      tests/test_phase16_prereg.py tests/test_package.py
78 passed in 12.34s

$ git ls-files 'results/phase19_*'
(empty)

$ .venv/bin/python -m pytest -q
798 passed, 1 skipped, 83 warnings in 145.85s (0:02:25)

$ .venv/bin/python -m ruff check . && .venv/bin/python -m ruff format --check .
All checks passed!
```

Baseline was 783 passed / 1 skipped at 19-04; +15 tests, same single pre-existing CUDA-only skip.

### Both prescribed mutations, watched RED and restored byte-identically

| # | Mutation | Result | Restored |
|---|----------|--------|----------|
| A | `if norms > 0.5:` added to `delta_w_cosine` | **RED** — `"delta_w_cosine: ordering comparison ['Gt']"` | sha256 `ba618a0f…` |
| B | a second `erasure_succeeded(` call in a new `second_opinion` | **RED** — `"erasure_succeeded is called 2 times: ['render_verdict', 'second_opinion']"` | sha256 `ba618a0f…` |

sha256 `ba618a0f9e000aca1f33a5a79eb4af4807ae68a1835e7a51ce93b86a8edb8532` before and after both
mutations; `git diff` empty after each restore.

**A third mutant was watched RED for free, before the code existed:** the guard bit on its own
first run against `fisher_overlap` interpolating `PRODUCTION_RANK` into a prose string. The number
was removed from the string rather than the guard weakened — see Deviation 2.

Both scans are additionally driven against synthetic mutants IN the committed tests (a bare
threshold, a `sign_test_exact` call, a missing scan target, a doubled call site, a retyped
baseline), so their non-vacuity does not depend on anyone having watched this session.

## Deviations from Plan

### 1. [Rule 1 — the prescribed composition is undefined against the committed signature] `delta_w_cells` returns a direction as well as the delegated ratio

- **Found during:** Task 1, before writing any code, by reading `extract_deltas.adapter_cells`.
- **Plan text:** *"`delta_w_cells(adapter, w0_state)` — one call to `extract_deltas.adapter_cells(...)`"*
  followed by *"`delta_w_cosine(cells_a, cells_b)` — per-cell cosine in fp64 … Returns a dict keyed
  by `(layer, projection)`, never a scalar summary."*
- **The conflict, measured:** `adapter_cells` (`scripts/extract_deltas.py:174-187`) returns
  `_ratio(scale * (b @ a), w0)` — a per-cell **Frobenius-norm RATIO**, i.e. one float per cell. A
  cosine between two floats is not defined, and a cosine over the 36-vector of ratios would be the
  single scalar the plan explicitly forbids.
- **Resolved as:** `delta_w_cells` DELEGATES the magnitude read to `adapter_cells` (so the committed
  number is never recomputed) and additionally builds the flattened fp64 `dW` from the identity the
  pin ALREADY committed in `MECHANISM_RULE` — `dW = scale * (B @ A)`, the same expression
  `ablate_components` operates on. `scale` is `alpha / r` read from the artifact
  (`extract_deltas.py:295`'s own spelling, PITFALLS P3).
- **The duplication is made self-checking, not argued away:** a committed test asserts
  `||delta||_F / ||W0||_F == cell["ratio"]` at `rel=1e-12` for all 36 cells, so the direction and
  the magnitude cannot drift into describing two different deltas. The same test asserts the
  fixture's deltas are non-zero, because `lora_B` starts at zero and every assertion would
  otherwise hold against a function that returned nothing.
- **Commit:** `99ed828`

### 2. [Rule 2 — a strictly stronger guard, and the code moved to satisfy it] the not-gated scan forbids more than the plan's wording

- **Plan text:** the guard fails on a call to the three gate functions *"or contains a `Compare`
  node against a module-level threshold constant"*.
- **Why that wording is not enough:** the plan's OWN prescribed RED mutation is `if cosine > 0.5:`
  — a comparison against a bare literal, not against a module-level constant. Scoped as written,
  the guard would have been green against the exact mutation it exists to catch.
- **Resolved as:** no ORDERING comparison (`Lt/LtE/Gt/GtE`) of any kind, no call to
  `sign_test_exact`/`holm`/`wilson_upper_bound`, and no read of any module-level number, anywhere
  inside a `DESCRIPTIVE_ONLY_FUNCTIONS` member. Equality comparisons stay legal, which is what
  makes the rule satisfiable: the zero-norm domain guard is `norms == 0.0`, not `norms > 0.0`.
- **It bit immediately, on correct code:** `fisher_overlap` interpolated `PRODUCTION_RANK` into its
  `granularity` prose. The digit was removed from the string (a comment records why) rather than
  the guard being weakened — `component_index` already derives the rank and `N_COMPONENTS` already
  publishes the product, so the string lost nothing.
- **Commit:** `99ed828`

### 3. [Rule 1 — the plan's `<done>` is falsified by the artifact] Phase 18 records FOUR of the eight parity keys

- **Found during:** Task 2, reading `results/phase18_arm_adapter-on.json` before writing the check.
- **Plan text:** *"`assert_phase18_parity(config)` … passes on the committed Phase 18 arm record's
  own `config` block"*, together with *"A config missing a `PARITY_KEYS` entry raises rather than
  skipping it."* Those two cannot both hold: the committed config carries `corpus_sha256`,
  `forbid_ids_sha256`, `k` and `seed_stride` and **not** `asr_rungs`, `stop_ids`,
  `sample_temperature`, `sample_top_p` (table above).
- **Resolved as:** the missing-raises half is kept, because it is the load-bearing one — an absent
  parameter must not read as agreement. `assert_phase18_parity(phase18_config)` therefore RAISES,
  naming `asr_rungs`, and a committed test asserts exactly that. `phase18_parity_config(record)`
  completes the block: four values read OUT OF the record (so a record at a different budget cannot
  be completed into a passing config — proved by mutating `k` to 47) and four reconstructed from
  the modules that own them.
- **The reconstruction is evidenced, not assumed:** `PHASE18_INHERITED_PARITY_KEYS` names the four,
  and an AST census proves Phase 18 reaches the sampler through `phase14_recall.draw_all` /
  `complete_question` with no sampling override at any of its three call sites, while those
  functions read `SAMPLE_TEMPERATURE`/`SAMPLE_TOP_P`/`STOP_IDS` as module constants.
- **Commit:** `c695cef`

### 4. [Rule 2 — close the gap rather than only detecting it] `ARM_CONFIG_KEYS` extended to a superset of `PARITY_KEYS`

- 19-04's `ARM_CONFIG_KEYS` required six columns and none of the four sampling parameters. Having
  just had to RECONSTRUCT four of Phase 18's parameters from source, requiring a Phase 19 arm to
  record all eight is the fix that stops the same reconstruction being needed again. A committed
  test asserts `set(PARITY_KEYS) <= set(ARM_CONFIG_KEYS)`.
- The extension is additive (`ARM_CONFIG_KEYS` is required-not-exhaustive and `_arm_record` checks
  membership) and it correctly reddened 19-04's own synthetic fixture, which now records all eight.
- **Scoping recorded with it:** `assert_phase18_parity` is for the arms compared against Phase 18,
  NOT for the (b) noise-floor replicate, whose `seed_stride` is offset ON PURPOSE
  (`SEED_STRIDE_OFFSET`, 19-04) so its seed windows cannot collide with Phase 18's. Recording which
  stride an arm ran under and asserting it matches another phase's are different acts.
- **Commit:** `c695cef`

### 5. [Rule 1 — two of my own assertions failed on CORRECT code and were replaced, not accommodated]

- **`"Phase 18" not in updated`** on the rendered report: red, because the report legitimately CITES
  Phase 18 — `D8_PUBLICATION_POSTURE` names the register it shipped `LEAKAGE_DEMONSTRATED` in, and
  the parity section is titled after it. The real property is that no Phase 18 SHIP-DECISION LINE
  arrives as this document's provenance, so the assertion now checks
  `EXTRACTION_SHIP_RECORDED_LINE`/`EXTRACTION_SHIP_PENDING_LINE` — which is also what
  `tests/test_phase19_docs.py` checks.
- **`"force" not in source.lower()`**: red, because the pin's own ordering contract says the
  recovery path is *"never a `--force` flag"*. A text scan reads the refusal as the defect. Replaced
  with the structural property: no function in the pin takes a parameter whose name contains
  `force`, and the string `"--force"` appears in no literal.
- Recorded because 19-03 already committed the lesson that *a test that fails on correct code is a
  test that gets deleted*; both of these were mine, and both were caught by running them.
- **Commit:** `c8772ef`

### 6. [Rule 3 — the plan's own verify command would not have run two of its tests]

- The plan's Task 2 command is `-k parity`. Two of the five tests I wrote did not contain that
  substring and were silently deselected on the first run. Both were renamed
  (`test_parity_recomputes_the_corpus_digest_and_never_pastes_it`,
  `test_phase18_parity_reconstructs_four_inherited_parameters_and_a_census_proves_it`) so the
  prescribed command actually covers the task it verifies. `-k parity` now selects 5 of 5.
- **Commit:** `e6eab23`

### 7. [Clarification] `render_verdict` landed in Task 1, not Task 3

- The plan lists `render_verdict()` among the pin's artifacts without assigning it a task, and
  Task 1's guard requires `erasure_succeeded` to be IMPORTED. An unused import fails `ruff`, so the
  import and its single call site had to arrive together — which is also the plan's own Task 1
  discipline ("define the functions in the same commit as the tuple that names them"). Task 3 then
  renders around it. The guard asserts the call-site list is exactly `['render_verdict']` from the
  first GREEN commit, so it is never vacuous.

## Findings For Downstream Plans

1. **`assert_phase18_parity` must NOT be called on the (b) replicate arm.** Its stride is
   deliberately offset (`SEED_STRIDE_OFFSET`) and the assertion would refuse it correctly. Call it
   on the target arms — the ones whose per-fact rates are compared with Phase 18's committed ones.
   The replicate still RECORDS all eight columns; recording and asserting are different acts.
2. **The Phase 19 arm config now requires ten columns, not six.** 19-06/19-13's arm writers must
   emit `asr_rungs`, `stop_ids`, `sample_temperature` and `sample_top_p` alongside the original
   six or `_arm_record` refuses at the write. `stop_ids` is a `frozenset` in `phase14_recall` and
   must be serialized as a list; `_parity_equal` compares a set AS A SET so the JSON round trip is
   already handled.
3. **`render_report` derives everything the gate saw from `render_verdict`'s record.** Do not pass
   the target bound, the floor, the caps or the deltas a second time — they are read out of
   `verdict["inputs"]`. What it still needs independently is only what the gate never sees: the raw
   draw denominators, the per-fact non-target rows, the PRE-erasure capability pair, the
   representational read and provenance.
4. **The clobber guard refuses EVERY existing report, in three distinguishable ways.** There is no
   `--force` and no re-render path. If a run is interrupted mid-render, the recovery is deleting
   the half-written file in a reviewed commit. 19-16 must use `append_ship_decision` (or
   `_addendum.append_addendum` with the Phase 19 pair), never `render_report` again.
5. **`append_ship_decision` will refuse a continuation that records no decision.** The addendum must
   contain a line `Phase 19 ship decision: SHIP` or `Phase 19 ship decision: DO NOT SHIP` and a
   `YYYY-MM-DD` date. This is Phase 18's W2 closed at the writer; a diagnosis-only continuation
   (19-16's D3 (c) diagnosis) should go through `_addendum.append_addendum` with the separate
   condition-(c) marker pair that `tests/test_phase19_docs.py` already pins, NOT through this one.
6. **`delta_w_cells` materialises ~85 MB of fp64 per adapter at production shape.** 19-14 reads two
   at once. That is fine on the M3; a third would want streaming per cell instead.
7. **A `None` cosine means the cell's ΔW is exactly zero — undefined, not orthogonal.** After a full
   ablation every cell is `None`. The renderer already prints "undefined (zero ΔW in this cell —
   NOT orthogonal)"; do not let a caption turn that into a zero.
8. **`fisher_overlap` is CELL-granular and cannot be otherwise.** The Fisher cache reduces to
   `(layer, projection)` and carries no rank-1 resolution, so a cell counts as ablated when any of
   its components was zeroed. The limitation travels inside the returned dict; publish it.

## Known Stubs

None. Every constant and function this plan added is fully implemented and exercised by a committed
test. `render_report` has been driven end-to-end against a synthetic input and its output inspected.
No `results/phase19_*` artifact exists or was written — `ERASURE_REPORT_PATH` is defined but the
only writes in this session were to `tmp_path` and to the scratchpad.

## Threat Flags

None. No new network endpoint, auth path or schema at a trust boundary. This plan reads three
COMMITTED artifacts (`results/phase18_arm_adapter-on.json`, `results/phase18_corpus.json`, and via
the tests `results/phase16_recall_sample.json`) with `json.loads`, loads no checkpoint, touches no
`weights_only` choke point, and writes only to a caller-supplied path. New imports are `re` and
`torch` (already in the pin's transitive graph via `extract_deltas` and `personacore.lora`) plus the
two phase-neutral stdlib-only siblings `_addendum` and `_verdict`.

## Threat Register Disposition

| Threat ID | Disposition | Status |
|-----------|-------------|--------|
| T-19-18 | mitigate | **Done** — the AST guard over `DESCRIPTIVE_ONLY_FUNCTIONS` forbids the three gate calls, every ordering comparison and every module-level number; a dangling entry fails; the scan is driven against three synthetic mutants in the committed test and was watched RED on the real file. |
| T-19-19 | mitigate | **Done** — `erasure_succeeded` imported by OBJECT IDENTITY, never re-defined, called from exactly `['render_verdict']`, and the four v2.0 baselines measured absent as numeric literals (0 hits each). Watched RED against a second call site. |
| T-19-20 | mitigate | **Done** — `assert_phase18_parity` over eight keys, each expected value imported from its owning module or recomputed; 8 mutations + 8 deletions each raise naming their own key; `corpus_sha256` recomputed and asserted absent from the pin source. The 4-of-8 recording gap is measured, named and reconstructed with an AST census. |
| T-19-21 | mitigate | **Done** — `assert_erasure_report_not_clobbered` reads through `_verdict.recorded_verdict`, refuses `None` / empty / recorded with three distinct messages, runs as `render_report`'s first statement, and no function in the pin takes a `force` parameter (AST-checked). |
| T-19-22 | mitigate | **Done** — both marker halves name Phase 19, neither mentions Phase 18, and `append_ship_decision` passes both to `_addendum.append_addendum` as the required keywords. Additionally the rewrite is CONDITIONAL on a pinned decision line — Phase 18's W2, which the marker-pair fix alone would NOT have caught. |
| T-19-SC | mitigate | **Holds** — zero packages installed; `tests/test_package.py` green (`pyproject.toml` sha256 pin unmoved). |

## Verification Against Plan Success Criteria

- [x] Representational consistency cannot become a gate — proved by a guard that was watched RED
      three times (twice deliberately, once by biting on correct code), not promised by a comment.
- [x] Exactly one verdict path exists and it imports the committed rule — call sites
      `['render_verdict']`, identity asserted, four baselines measured absent as literals.
- [x] Every comparability parameter is asserted against Phase 18's own committed value — with the
      measured correction that Phase 18 committed only four of them, and the other four evidenced
      by census rather than assumed.
- [x] The report's marker pair names Phase 19 in both halves, and the clobber guard has no force
      flag — checked structurally (parameter names + string literals), not by grepping prose.

## Self-Check: PASSED

- `scripts/phase19_erasure.py` — FOUND (modified, 2365 lines)
- `tests/test_phase19_erasure.py` — FOUND (modified, 2707 lines)
- commit `a079913` — FOUND
- commit `99ed828` — FOUND
- commit `e6eab23` — FOUND
- commit `c695cef` — FOUND
- commit `ab465da` — FOUND
- commit `c8772ef` — FOUND
- `results/phase19_*` tracked files — 0 (guard intact)
- pin sha256 after both prescribed mutations — `ba618a0f9e00…`, `git diff` empty after each restore
</content>
</invoke>
