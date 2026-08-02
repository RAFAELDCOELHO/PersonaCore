---
phase: 14
plan: 05
subsystem: recall harness pre-registration + D-10 scoring rules
tags: [D-04, D-09, D-10, D-18, D-19, pre-registration, clean-room]
requires:
  - personacore.dialogue.build_recall_prompt
  - personacore.dialogue.detokenize
  - scripts/phase14_factset.VALUE_TOKEN_CENSUS
  - scripts/phase14_factset.LOCKED_FACTS
  - scripts/phase14_factset.SOFT_TIER_FACTS
  - artifacts/tokenizer.json
provides:
  - scripts/phase14_recall.RECALL_MAX_NEW_TOKENS
  - scripts/phase14_recall.derive_recall_budget
  - scripts/phase14_recall.assert_values_fit
  - scripts/phase14_recall.question_seed
  - scripts/phase14_recall.normalize
  - scripts/phase14_recall.contains_value
  - scripts/phase14_recall.score_question
  - scripts/phase14_recall.find_contradictions
  - scripts/phase14_recall.has_hedging
  - scripts/phase14_recall.render_context_dump
  - scripts/phase14_recall.assert_no_value_in_prompt
  - scripts/phase14_recall._prove
  - tests/test_phase14_scoring.py
affects:
  - scripts/phase14_recall.py (plan 14-06 lands main(); plan 14-10 lands the D-11 controls)
  - scripts/personalize_demo.py (plan 14-08 — imports RECALL_MAX_NEW_TOKENS and render_context_dump)
  - scripts/teach_persona.py (plan 14-07 — lazily imports normalize/contains_value/score_question)
  - "plan 14-09 (locks TAUGHT_THRESHOLD / HELDOUT_THRESHOLD from the calibration run)"
tech-stack:
  added: []
  patterns:
    - "pre-registration constants as module-level literals with per-number provenance comments"
    - "lazy cross-script import enforced by a sys.modules test, not by convention"
    - "one shared renderer for the committed evidence and the live UI panel (D-18)"
    - "stub tokenizer fixture to make a boundary premise literal rather than BPE-dependent"
key-files:
  created:
    - scripts/phase14_recall.py
    - tests/test_phase14_scoring.py
  modified: []
decisions:
  - "import torch is deferred to plan 14-06 rather than written now as an unused import — ruff F401 would fail the plan's own `ruff check scripts/` acceptance criterion, and the os.environ MPS-fallback preamble still does its job because it runs before any later torch import in the process"
  - "normalize() duplicates phase14_factset.normalize_for_match's composition rather than importing it — the import topology makes both a module-level and a per-call import a fact-string leak — and a new parametrized test pins the two to identical behavior so the duplication cannot drift"
  - "test_no_fact_strings_at_import pops both names from sys.modules before loading the driver: tests/test_phase14_teaching.py loads teach_persona at collection time, which seeds sys.modules['phase14_factset'] for the whole pytest process"
  - "the boundary test uses a fixed-count stub tokenizer so the exactness premise is literal; hunting a real string that encodes to exactly 40 ids would make the fixture depend on BPE merge behavior"
metrics:
  duration: 42min
  tasks: 3 of 3
  files: 2
  completed: 2026-08-02
---

# Phase 14 Plan 05: Recall Pre-Registration + D-10 Scoring Rules Summary

Committed `scripts/phase14_recall.py`'s pre-registration block — the D-19 generation budget
(**48**) with an auditable derivation a reader can check without running anything, a `SystemExit`
fit guard that is honest about detecting census *drift* rather than budget shortfall, and every
D-10 scoring rule as a pure module-level function — behind an import-time surface that holds
**integers only**, pinned by 26 CPU-only tests.

## What Shipped

**`scripts/phase14_recall.py`** (357 lines, new)

| Constant / function | Content |
|---|---|
| `VALUE_TOKEN_COUNTS` | `(5, 4, 5, 6, 8, 8, 4, 4, 6, 6)` — the ten taught counts, integers only |
| `PREAMBLE_HEADROOM` / `TAIL_HEADROOM` / `BUDGET_STEP` | `32` / `8` / `8`, each with its measured provenance in its own comment |
| `derive_recall_budget` | `max(census) + preamble + tail`, rounded up to `step`; the docstring states the census, the formula in words, and the result |
| **`RECALL_MAX_NEW_TOKENS`** | **48** (`8 + 32 + 8`, already a multiple of 8) |
| `SEED` / `N_SEEDED_SAMPLES` / `STOP_IDS` | `1337` / `8` / `frozenset({8184, 8185})` |
| `TAUGHT_THRESHOLD` / `HELDOUT_THRESHOLD` | `None` — locked by plan 14-09 under `teach_persona.CALIBRATION_DECISION_RULE` |
| `question_seed` / `_prove` / `assert_values_fit` | per-question seed, the `SystemExit` helper, the D-19 fit guard |
| `normalize` / `contains_value` / `score_question` | D-10's normalizer, substring gate, and `(k, n)` rate |
| `find_contradictions` / `HEDGING_RE` / `has_hedging` | the mechanical detector over the committed gate lexicon, plus the separately-reported hedging signal |
| `render_context_dump` | the D-18 shared renderer — three lines, byte-matching 14-UI-SPEC |
| `assert_no_value_in_prompt` | Pattern-8 clean-room proof at both string and token level; `values` is a parameter |

Two clearly-marked empty sections mark where 14-06's `main()` and 14-10's three D-11 controls land.

The rendered dumps match 14-UI-SPEC's samples exactly:

```
ids  (19) : [8187, 8185, 119, 104, 97, 116, 341, 32, 121, 111, 117, 114, 331, 39, 115, 315, 101, 63, 8186]
decoded   : <|system|><|user|>what is your dog's name?<|assistant|>
ids   (3) : [8187, 8185, 8186]
```

**`tests/test_phase14_scoring.py`** (304 lines, 26 tests, 0 skips, 0.07 s)

`test_preregistration_constants`, `test_value_token_counts_transcription`, `test_generation_budget`
(5 cases), `test_generation_budget_boundary`, `test_fit_guard_names_the_offender`,
`test_normalizer_literals` (6 cases), `test_normalizer_agrees_with_the_gate_normalizer` (6 cases),
`test_substring_gate`, `test_contradiction_detector`, `test_render_context_dump_shape`,
`test_no_fact_strings_at_import`, `test_question_seed_is_distinct_and_derivable`.

## Verification

| Check | Result |
|---|---|
| Plan Task-1 automated block | `budget 48` — all 8 assertions pass |
| Plan Task-2 automated block | `scoring rules ok` — all 9 assertions pass |
| `pytest -q tests/test_phase14_scoring.py -x` | **26 passed** (plan floor: 10) |
| `pytest -q` (full suite) | **337 passed, 4 skipped** (wave-3 baseline 311+4, +26 new) |
| `ruff check . && ruff format --check .` | clean, 130 files |
| Plan-level verification one-liner | prints `48`, `phase14_factset` absent from `sys.modules` |
| `grep -c "assert " scripts/phase14_recall.py` | **0** |
| `grep -n "^import phase14_factset\|^from phase14_factset"` | no match |
| `grep -n "LOCKED_VALUES"` | 1 hit, inside `find_contradictions`'s docstring — no module-level match |
| `grep -c "def detokenize" scripts/phase14_recall.py` | 0 (imported, never reimplemented) |
| `grep -c "descriptive"` / `"no gate"` | 1 / 1 |
| `grep -c "skipif\|importorskip"` (test) | 0 |
| `assert_values_fit(tok, ['marrowgate '*20])` | `SystemExit` naming the value and `48` |
| `assert_no_value_in_prompt` on a value-carrying question | `SystemExit` — leak guard fires |
| `git diff --diff-filter=D HEAD~3 HEAD` | no deletions |

**Hoist verification (plan-mandated).** `import phase14_factset` hoisted to module level in the
driver → `test_no_fact_strings_at_import` **FAILED**; reverted. `import teach_persona` hoisted →
**FAILED**; reverted. Working tree confirmed clean after both. Both `<import_topology>` edges are
enforced by the test, not by prose.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] `test_no_fact_strings_at_import` cannot read a virgin `sys.modules`**
- **Found during:** Task 3
- **Issue:** The plan's test asserts `"phase14_factset" not in sys.modules` after an `importlib`
  load of the driver. But `tests/test_phase14_teaching.py` calls `_load("teach_persona")` at
  **module scope**, and `teach_persona` imports `phase14_factset` at module level. Pytest imports
  every test module during collection, so both names are already in `sys.modules` before any test
  in this file runs — the assertion fails for a reason that has nothing to do with the driver.
  Verified first-party: loading `teach_persona` by `spec_from_file_location` leaves
  `phase14_factset` in `sys.modules`.
- **Fix:** The test pops both names, loads the driver inside the window, checks, and restores them
  in a `finally`. The docstring says why. This makes the test measure the driver's own import
  topology rather than pytest's collection order — and, verified above, it still goes red when
  either edge is hoisted.
- **Files modified:** `tests/test_phase14_scoring.py`
- **Commit:** 868d0fd

### Deliberate Adjustments

**2. `import torch` deferred to plan 14-06**
The plan's preamble instruction lists `os.environ.setdefault(...)` followed by
`import torch  # noqa: E402`. Nothing in Tasks 1–3 uses torch, so the import would be dead —
and ruff's `F401` would fail the plan's own acceptance criterion that `ruff check scripts/` exits 0.
The `os.environ` preamble ships now with a comment naming what it protects, and it still does real
work: it runs before the first torch import anywhere in the process, including 14-06's and
including a demo that imports this module for its budget integer. 14-06 adds the import directly
beneath it.

**3. `normalize` duplicates `phase14_factset.normalize_for_match`'s composition, pinned by a test**
Reusing the fact-set module's normalizer is the obvious move and the import topology forbids it
twice over: a module-level import leaks the locked values into the demo process, and a per-call
import inside `normalize` leaks them on the first call. So the four-line composition is duplicated,
`detokenize` is still imported from `personacore.dialogue` (never reimplemented), the docstring
names why the duplication exists, and `test_normalizer_agrees_with_the_gate_normalizer` runs both
functions over the same six fixtures. Duplication that nothing pins is duplication that drifts, and
a drifted scoring normalizer would make the gate's guessability verdict and the recall score answer
subtly different questions.

**4. [Rule 2] Two contracts pinned beyond the plan's test list**
- `test_value_token_counts_transcription` — `VALUE_TOKEN_COUNTS` is transcribed **by hand** because
  the driver may not import the census. `assert_values_fit`'s docstring claims it detects census
  drift; against the committed census the inequality is structurally unfireable, so without this
  test *nothing* actually detects a mistyped digit, and the honest docstring would be describing a
  protection that does not exist. The test compares the tuple against the census and against the
  frozen tokenizer's own encode lengths.
- `test_normalizer_agrees_with_the_gate_normalizer` — see adjustment 3.

**5. `test_generation_budget_boundary` uses a fixed-count stub tokenizer**
The plan requires the exactness premise stated before the boundary assertions. A real string that
encodes to exactly `RECALL_MAX_NEW_TOKENS - TAIL_HEADROOM` ids would have to be hunted for, and the
fixture would then silently depend on BPE merge behavior. A four-line `_FixedTokenizer(n)` makes
the premise literal. `test_fit_guard_names_the_offender` still runs the real tokenizer.

## Threat Mitigations Applied

| Threat ID | Mitigation as built |
|---|---|
| T-14-17 | `import phase14_factset` appears nowhere at module level; `test_no_fact_strings_at_import` verified red under a hoist of that edge **and** of the `teach_persona` edge that would leak by a second route. `VALUE_TOKEN_COUNTS` carries integers only, and no driver attribute is a string equal to any locked value |
| T-14-18 | `assert_no_value_in_prompt` proves absence at both the decoded-string and contiguous-id-run level via `_prove` → `SystemExit`; the prompt is built only by `build_recall_prompt`, and `values` is a parameter so no fact string is captured at module level |
| T-14-19 | `derive_recall_budget`'s docstring is the auditable D-19 computation (census → formula in words → 48); `assert_values_fit` raises naming the value, its count, and the budget; the `>` vs `>=` boundary is pinned by a test with a literal exactness premise |
| T-14-20 | `TAUGHT_THRESHOLD` / `HELDOUT_THRESHOLD` committed as `None` with plan 14-09 and `CALIBRATION_DECISION_RULE` named in the comment; `test_preregistration_constants` pins both to `None`, so locking them is a visible diff |
| T-14-21 | `find_contradictions` is mechanical over the committed locked-plus-rejected lexicon; the docstring states the metric is descriptive with no gate and routes residual human review to D-03's quoted-evidence discipline |
| T-14-SC | Zero packages installed |

## Known Stubs

None that block this plan's goal. Two deliberately empty, clearly-marked sections at the bottom of
`scripts/phase14_recall.py` reserve where plan 14-06's `main()` and plan 14-10's three D-11 controls
land — that split is the plan's own instruction, and both are later-wave work with their own plans.
Every rule this plan promised is fully implemented and tested.

## Notes for Later Plans

- **`RECALL_MAX_NEW_TOKENS` is 48.** 14-08 imports the integer and floors the slider at it. Do not
  re-derive it in the demo — re-deriving needs the locked values, which 14-UI-SPEC forbids.
- **`import phase14_factset` belongs inside `main()` and nowhere else** (14-06). The same rule
  applies to `run_collapse_control`'s `COLLAPSE_PPL_TRIGGER` import from `teach_persona` (14-10).
  `test_no_fact_strings_at_import` fails on either hoist — verified, not assumed.
- **14-07's calibration scoring pass** imports `normalize` / `contains_value` / `score_question`
  from this module **lazily**, inside the scoring function (`<import_topology>` rule 4).
- **`render_context_dump` is the only renderer.** 14-08's token panel calls it; 14-06's committed
  dumps call it. `tests/test_phase14_demo.py`'s byte-identity test compares the two renders.
- **The soft tier is still separate.** `VALUE_TOKEN_COUNTS` covers `LOCKED_FACTS + SOFT_TIER_FACTS`
  because the budget must fit every taught value — but nothing about the *thresholds* changes:
  `score_question` is per-question, and aggregation over the core tier alone is 14-06's job.
- **`assert_values_fit` is a drift detector, not a budget check.** Its docstring says so. The thing
  that actually catches a mistyped census entry is
  `test_phase14_scoring.py::test_value_token_counts_transcription`.

## Self-Check: PASSED

- `scripts/phase14_recall.py` — FOUND
- `tests/test_phase14_scoring.py` — FOUND
- `.planning/phases/14-teach-then-recall-demo/14-05-SUMMARY.md` — FOUND
- commit `59af3ad` (Task 1) — FOUND
- commit `8cfd0b0` (Task 2) — FOUND
- commit `868d0fd` (Task 3) — FOUND
