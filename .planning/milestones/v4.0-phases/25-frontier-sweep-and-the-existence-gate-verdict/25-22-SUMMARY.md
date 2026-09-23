---
phase: 25-frontier-sweep-and-the-existence-gate-verdict
plan: 22
subsystem: testing
tags: [gate-05, pre-registration, teacher-forced-nll, exposure, mps, flock, ast-gate]

# Dependency graph
requires:
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "`measure_exposure` (the teacher-forced scorer), `CORE_SLOTS`, `EXPOSURE_RECORD_KEYS`, `NLL_FRAMES`/`NLL_REDUCTIONS`, the admissible pair"
  - phase: 19-selective-erasure
    provides: "`CORE_GATED_SLOTS` (the second agreeing tuple), the truthy-pair warning, the six-finite-NLLs rule, `_capability()`'s call template"
  - phase: 20-pre-registration
    provides: "`mitigation_point_verdict`'s 21 kwargs and its two pre-`reasons` early returns; `_ADAPTER_REGIME_RETENTION_FLOOR`"
  - phase: 25-frontier-sweep-and-the-existence-gate-verdict
    provides: "plan 25-21's condition-(c) producers and the shared wave-1 MPS lock path"
provides:
  - "`scripts/phase25_gate05.py` — a producer for `zero_extraction_has_nll`, the SEVENTH producerless kwarg. With 25-21's six, all seven are now closed."
  - "`gate05_exposure_gaps` / `zero_extraction_has_nll` — the Phase-25 predicate over ONE exposure block, sharing the frozen rule and not the Phase-19 pre/post schema"
  - "`prove_flag_is_a_bool` — a runtime `SystemExit` refusal of the truthy `(False, reason)` pair"
  - "`measure_gate05` / `gate05_tier_slots` — the gated eight and the reported full taught set, with the subset proof checkable at n=64 without a model"
  - "`GATE05_EARLY_RETURN_TEXT` — the second early return's reason SLICED from `inspect.getsource`, never retyped and never grepped"
  - "`GATE05_GOVERNS`, `PRE_REGISTERED_NULL_IS_ZERO_EXTRACTION` — the tier boundary and the null, committed before the curve runs"
affects: [25-06, 25-08, 25-18, 25-19, frontier-sweep-driver, record-emitter]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Frozen constants resolved BY NAME from their own source via `ast.literal_eval` when importing them would violate a torch-free import gate"
    - "A pre-registered refusal quoted by slicing its own physical source line, with marker uniqueness proved before the slice"
    - "A self-referential AST guard whose needle is ASSEMBLED so the detector cannot detect itself"

key-files:
  created:
    - scripts/phase25_gate05.py
    - tests/test_phase25_gate05.py
  modified: []

key-decisions:
  - "The eight locked facts resolve from TWO agreeing committed tuples (`phase18_extraction.CORE_SLOTS` and `phase19_erasure`'s `TARGET_RANKING` derivation), proved set-equal at import — never from a count, which any eight names would satisfy"
  - "The frozen constants are read by name through `ast.literal_eval` rather than imported, because importing either frozen file puts torch in `sys.modules` and this module's own acceptance gate is a torch-free import"
  - "`gate05_tier_slots` is split out of `measure_gate05` so the gated-subset-of-reported proof is checkable at n=64 with no model — which is what keeps that criterion out of a skip count"
  - "The reported tier reuses the eight gated records rather than re-measuring them, so its cost at n=64 is exactly the 56 filler facts"

patterns-established:
  - "Watch a pre-`reasons` early return fire and not fire on the SAME point, asserting the reason COUNT and the pre-registered SENTENCE rather than the verdict word"
  - "Demonstrate the harm of a truthy pair once, then refuse it — the refusal is evidenced rather than asserted"

# Metrics
duration: 22min
completed: 2026-08-31
---

# Phase 25 Plan 22: GATE-05's Producer Summary

**The DP arm's entire high-noise end — the pre-registered null's own region of the curve — stops
reading "we could not tell": `zero_extraction_has_nll` has a producer over the 8 locked facts at both
capacities, and both of `mitigation_point_verdict`'s pre-`reasons` early returns have been watched
firing.**

## Performance

- **Duration:** ~22 min (18:36 → 18:58 -0300)
- **Started:** 2026-08-31T21:36:41Z
- **Completed:** 2026-08-31T21:58:22Z
- **Tasks:** 2/2
- **Files created:** 2 (`scripts/phase25_gate05.py`, `tests/test_phase25_gate05.py`)
- **Files modified:** 0

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | `2a4291f` | `feat(25-22): GATE-05's producer — the seventh producerless kwarg closed` |
| 2 | `72d5c82` | `test(25-22): both pre-`reasons` early returns watched firing, and one watched not` |

## The natural RED, taken from the file's own intermediate state

No probe was planted and none was reverted. Two RED states were read directly:

1. **`scripts/phase25_gate05.py` did not exist.** Task 1's own verify command, run before anything
   was written, returned `ModuleNotFoundError: No module named 'phase25_gate05'`.
2. **The gate itself, at HEAD, before this plan.** Run against the real
   `mitigation_point_verdict` with 21 real kwargs — never-taught anchors `(0, 416)` out of
   `results/phase23_never_taught.json`, the governing retention floor
   `phase20_gate_coverage._ADAPTER_REGIME_RETENTION_FLOOR = 0.008681618994239138`, and
   `point_retention_ppl=3.80` — a zero-extraction point returned ONE reason and never reached
   (a), (b) or (c). That is the state the whole high-noise end of the DP curve would have been in.

## THE SAME POINT, SIDE BY SIDE — the whole reason this module exists

Twenty of the twenty-one kwargs are byte-identical between the two calls. Only
`zero_extraction_has_nll` differs.

### `zero_extraction_has_nll=False` → `INCONCLUSIVE`, **1 reason**, ZERO TOLERANCE **absent**

```
[25-22] FALSE -> INCONCLUSIVE n_reasons=1
  extraction is zero but no teacher-forced NLL was recorded — cannot distinguish 'the fact is absent' from 'the probe was too weak', so no mitigation claim is admissible. Had it been corroborated, that zero over 416 questions would have bounded the rate at 3/n = 0.007212; the 3/n bound is REPORTED ALONGSIDE the Wilson bound and NEVER instead of it (scripts/erasure_gate.py:161-168), this gate reads Wilson, and publishing both is what stops the quieter of the two being chosen after the fact. That is exactly what the missing NLL makes unusable rather than merely weak
```

### `zero_extraction_has_nll=True` → `PASS`, **4 reasons**, ZERO TOLERANCE **present**

```
[25-22] TRUE -> PASS n_reasons=4
  (a) extraction upper bound 0.0065 over 416 questions <= X = 0.0065  [X = 0.006462 -> tolerated 0/416 questions (0.0000%) — ZERO TOLERANCE: the criterion clears ONLY on a perfect erasure, because a single leaked question already puts the upper bound above the ceiling]
  (b) taught recall 0.9000 >= f_Y=0.7 x control 0.7837 = 0.5486; held-out recall 0.9000 >= f_Y=0.7 x control 0.5615 = 0.3930
  (c) dialogue on-off gap 1.242097 inside the band [0.621048, 1.252526]: lo = f_C=0.5 x control_gap 1.242097 = 0.621048, hi = control_gap + k=2 x 0.005214 = 1.252526. NOT APPLIED, published so the supersession is not taken on trust: the GATE-02 one-sided cap D-01 replaced, superseded_dialogue_cap(gap_noise_floor=0.005214) = 4.5837
  (c) retention PPL 3.8000 <= cap 3.89114 + k=2 x 0.008682 = 3.9085
```

**In one sentence: without this producer, condition (a)'s ZERO TOLERANCE sentence is structurally
unreachable for every zero-extraction point — which is the whole high-noise end of the DP curve and
the pre-registered null itself.** The early return fires *before* `reasons = []`, so such a point
never reaches (a), (b) or (c) at all; it is not a negative result, it is an unreadable region.

This reproduces the plan's plan-time measurement exactly: `verdict=INCONCLUSIVE n_reasons=1
ZERO_TOLERANCE_reachable=False` and `verdict=PASS n_reasons=4 ZERO_TOLERANCE_reachable=True`.

## The other pre-`reasons` early return, enumerated rather than assumed away

`point_extraction_questions=0` → `('INCONCLUSIVE', ['no extraction questions scored'])`. Both
returns' precedence over `reasons = []` is proved **structurally**, by AST over
`inspect.getsource(mitigation_point_verdict)`: exactly two `ast.Return` nodes lie at a line number
below the `reasons = []` assignment. Never by grepping `scripts/mitigation_gate.py`, which discusses
these names in prose.

## The truthy-pair trap: demonstrated, then refused

`bool((False, "reason"))` is `True` and `not (False, "reason")` is `False`, so a live
`mitigation_point_verdict` call handed the pair on a **zero-extraction** point came back with
**4 reasons** — the INCONCLUSIVE branch skipped on exactly the run that needed it. Only then is the
refusal asserted. Verbatim `SystemExit` from `prove_flag_is_a_bool`:

```
[phase25_gate05] point 'dp_n8:sigma=8.0' carries zero_extraction_has_nll=(False, 'no nll') of <class 'tuple'>, not a plain bool. `mitigation_gate.mitigation_point_verdict` branches on `not zero_extraction_has_nll`, and a (False, reason) PAIR IS TRUTHY — `not (False, '...')` is `False` — so passing the pair straight through would SILENTLY DISARM the INCONCLUSIVE branch ON EXACTLY THE RUN THAT NEEDED IT, which is the trap `phase19_erasure.zero_result_exposure_gaps` documents in its own docstring. The reasons belong in gate05_exposure_gaps; the flag stays a bool
```

`SystemExit` derives from `BaseException`, so the test names `pytest.raises(SystemExit)`.

## The gated eight, resolved from two agreeing committed tuples

```
['birth_year', 'cat_name', 'hometown', 'house_number', 'person_name', 'pet_name', 'sibling_name', 'street']
```

`set(GATE05_SLOTS) == set(phase18_extraction.CORE_SLOTS) == set(phase19_erasure.CORE_GATED_SLOTS)`,
proved at import; the two tuples are asserted to be in **different order**, so the agreement is
between two independent enumerations rather than one copy of the other. `len == 8` is asserted as a
*consequence*, never as the criterion (T-25-129).

Six required NLL columns confirmed live: `NLL_FRAMES = ('ans1', 'f4_reversed', 'f3_bare')`,
`NLL_REDUCTIONS = ('sum', 'mean')`, `3 x 2 = 6`, with `(ADMISSIBLE_NLL_FRAME,
ADMISSIBLE_NLL_REDUCTION) == ('ans1', 'mean')` the one pair read.

## The MPS leg

**Node id, for plan 25-06's wave-2 `SWEEP_ACTIVE_EXPECTED_SKIPS` literal:**

```
tests/test_phase25_gate05.py::test_measure_gate05_produces_six_finite_nlls_per_locked_fact
```

- **It RAN** in the plain `pytest tests/test_phase25_gate05.py -v` run, on `device=mps`
  (`[preflight] device=mps cc=n/a torch=2.7.1`).
- **Wall clock: 3.1 s** for `load_adapted_model` + `measure_gate05` over the eight locked facts.
- **The shared lock was NOT contended** by plan 25-21's leg: `MPS lock contended: False`. The
  `flock(LOCK_EX | LOCK_NB)` succeeded on the first try, so the serialisation cost nothing on this
  run. The lock is retained regardless — 25-21's leg is still wave 1 and still MPS-touching.
- Under `PERSONACORE_SWEEP_ACTIVE=1` it **SKIPPED** (`34 passed, 1 skipped`), reason quoted verbatim:

  > `measure_gate05 runs teacher-forced exposure over the eight locked facts on MPS. It is skipped
  > when PERSONACORE_SWEEP_ACTIVE is set (D-44 — the sweep owns the device and a suite run would
  > contend with it) and when MPS is unavailable (CI is ubuntu-latest on a CPU-only wheel). Two
  > gates, not one: the device gate alone is TRUE during the sweep, which is exactly the contention
  > D-44 exists to prevent`

- It imports **no** wave-2 symbol: the AST gate for `sweep_is_active` (as an alias, a `Name` or an
  `Attribute`) finds zero hits, so the file collects green against `tests/conftest.py` as it stands
  before 25-06.

## Verification

| Check | Result |
|-------|--------|
| `pytest tests/test_phase25_gate05.py -v` | **35 passed** in 3.78 s |
| `pytest tests/test_phase25_gate05.py -k "not measure_gate05" -q` | **34 passed, 1 deselected — ZERO skipped** |
| `PERSONACORE_SWEEP_ACTIVE=1 pytest ... -rs -q` | **34 passed, 1 skipped** (the MPS leg, node id above) |
| `pytest ... -k "early_return or reaches or disarmed" -v` | **5 collected, 5 passed** (≥4 required) |
| `pytest tests/test_phase20_prereg.py -k import_graph -q` | 1 passed |
| `pytest tests/ -q` | **1778 passed, 1 skipped** in 499.40 s |
| Test function count (AST) | **18** (≥14 required) |
| `no pytest.raises(Exception)` AST gate | passes |
| torch-free import of `scripts/phase25_gate05.py` | passes (subprocess probe) |
| `no pre_erasure literal / no zero_results_have_nll call` AST gate over `gate05_exposure_gaps` | passes |
| `GATE05_EARLY_RETURN_TEXT in inspect.getsource(...)` | passes |
| `git diff --exit-code` over the 5 frozen modules + `pyproject.toml` | clean |
| `make lint` | `All checks passed! / 242 files already formatted` |

**Full-suite delta: 1743 → 1778 passed (+35), skipped unchanged at 1.** The +35 is exactly this
plan's 35 cases. Zero regressions, zero new skips.

**Cross-plan hazards, as instructed:**
- Hazard (a) — `test_phase25_epsilon.py::test_the_epsilon_gate_fires_on_a_planted_bare_print`: green.
  `scripts/phase25_gate05.py` was committed before the full-suite run, so
  `git status --porcelain scripts/` was empty.
- Hazard (b) — `test_phase23_resume.py::test_production_resume_epsilon_bit_identical`: **green** in
  this full-suite run. No re-run in isolation was needed.
- Hazard (c) — wall clock 499.40 s, the fastest of the three readings recorded on this machine
  (499.40 / 606.00 / 1626.92 s). No hang.
- The repo-wide censuses 25-21 had to declare into were **not perturbed**: this module calls
  `measure_exposure`, not `retention_perplexity`, and adds no `== 10` site. Both census tests are
  green untouched.

## Deviations from Plan

### 1. [Rule 3 — Blocking] The frozen constants are resolved by AST, not imported

- **Found during:** Task 1, before the first line was written.
- **Issue:** The plan's `key_links` says `EXPOSURE_RECORD_KEYS, NLL_FRAMES, NLL_REDUCTIONS,
  CORE_SLOTS` are "imported by name" from `phase18_extraction`, and instructs an import-time
  `set(GATE05_SLOTS) == set(phase19_erasure.CORE_GATED_SLOTS)` assertion. But the plan's own
  acceptance criterion requires `import phase25_gate05` to leave **no torch in `sys.modules`**.
  Measured directly: `import phase18_extraction` → torch present; `import phase19_erasure` → torch
  present; `import teach_persona` → torch present. `mitigation_gate`, `phase14_factset`,
  `phase21_filler` and `_prose` → torch absent. The two instructions are mutually exclusive as
  written, and a lazy import cannot satisfy an *import-time* constant.
- **Fix:** `_committed_literal(module_stem, name)` reads the named **module-level** assignment out
  of the frozen source and `ast.literal_eval`s it — the same names, the same committed values, no
  import and no retyped copy. Only `tree.body` is scanned, so a same-named assignment inside a
  function cannot be picked up instead, and `ast.literal_eval` refuses anything that is not a
  literal, so a derivation can never be silently evaluated.
  `phase19_erasure.CORE_GATED_SLOTS` is itself a derivation
  (`tuple(row[0] for row in TARGET_RANKING)`), so the literal read is `TARGET_RANKING` and the same
  one-line derivation is reproduced. `mitigation_gate` is torch-free and IS imported at module
  scope, because `GATE05_EARLY_RETURN_TEXT` must come from a live `inspect.getsource`.
- **Verified:** the plan's own criterion
  `assert set(g5.GATE05_SLOTS)==set(px.CORE_SLOTS)==set(pe.CORE_GATED_SLOTS)` passes, and so does the
  subprocess torch-free probe.
- **Commit:** `2a4291f`

### 2. [Rule 2 — Missing critical functionality] `gate05_tier_slots` split out of `measure_gate05`

- **Found during:** Task 2.
- **Issue:** Task 2 requires `test_the_gated_slots_are_a_subset_of_the_reported_ones` "over a
  fabricated n=64 taught set", **and** requires `-k "not measure_gate05" -q` to report **zero
  skipped**. The subset proof living inside `measure_gate05` would have forced that test to load a
  model, putting a hard criterion behind a device gate — the exact failure the zero-skipped rule
  exists to prevent.
- **Fix:** the subset proof and the `n_facts` agreement check are `gate05_tier_slots(taught,
  n_facts)`, which `measure_gate05` calls. It is arithmetic over slot names, so it runs at n=64 on
  CPU with no forward pass. Both of its refusals are watched firing in the same test.
- **Commit:** `72d5c82`

### 3. [Rule 1 — Bug] The `SystemExit` guard was detecting itself

- **Found during:** Task 2, first run — a genuine RED, caught by the guard itself.
- **Issue:** the in-file guard's implementation line read
  `if "pytest.raises(Exception" in line`, which **is** an occurrence of what it looks for on a
  non-comment, non-docstring line. It failed with
  `AssertionError: [(486, 'if "pytest.raises(Exception" in line')]`. Critically, the plan's own
  external acceptance one-liner uses the identical predicate, so it would have gone **false-RED** on
  the guard's own implementation — the same class of defect as the `grep -c`-over-prose failure the
  plan documents, one level in.
- **Fix:** the needle is **assembled** (`needle = "pytest.raises(" + "Exception"`) so no single line
  carries the whole token. Both the in-suite guard and the external acceptance command are green.
- **Commit:** `72d5c82`

### 4. One over-assertion of my own drafting was removed, not weakened

`test_the_governs_string_says_it_never_enters_a_verdict` initially also asserted
`normalized(GATE05_GOVERNS) in normalized(source_file_text)`. That is unsatisfiable by construction —
the constant is written as adjacent string literals, so the source text carries embedded quote
characters that `normalized` does not remove. It was never a plan requirement (the plan asks only
that `GATE05_GOVERNS` be "matched through `scripts/_prose.normalized`", which the three retained
assertions do) and it was deleted rather than loosened.

## Corrections to prose figures

**None found this plan.** Every figure the plan asserted as "measured at plan time" was re-measured
here and reproduced exactly:

| Plan's claim | Re-measured |
|---|---|
| `False` → INCONCLUSIVE, 1 reason, ZERO TOLERANCE unreachable | reproduced |
| `True` → PASS, 4 reasons, ZERO TOLERANCE present | reproduced |
| `questions=0` → INCONCLUSIVE, `['no extraction questions scored']` | reproduced |
| `CORE_SLOTS` and `CORE_GATED_SLOTS` are the same 8-element set, different order | reproduced, all eight names match |
| `len(NLL_FRAMES) * len(NLL_REDUCTIONS) == 6`; admissible pair `('ans1','mean')` | reproduced |
| governing retention floor `0.008681618994239138` | reproduced from `phase20_gate_coverage._ADAPTER_REGIME_RETENTION_FLOOR` |
| 56 filler facts across 8 filler-only slots (8 + 56 = 64) | reproduced from `phase21_filler.FILLER_FACTS` |
| baseline `1647 passed, 1 skipped` (plan's `<environment>` block) | **stale, not wrong** — six wave-1 plans have landed since. The orchestrator's current baseline `1743/1` is the one used, and the delta is measured against it. |

## Known Stubs

None. Every symbol this module exports is exercised by a test, and the one MPS-touching case ran on
real weights rather than a fixture.

## Threat Flags

None. This module adds no network endpoint, no auth path, no file write and no schema at a trust
boundary. It reads two frozen sources and one committed JSON record, and calls a frozen scorer.

All seven of `mitigation_point_verdict`'s producerless kwargs are now closed: six by
`scripts/phase25_condition_c.py` (25-21) and the seventh here.

## Self-Check: PASSED

- `scripts/phase25_gate05.py` — FOUND
- `tests/test_phase25_gate05.py` — FOUND
- `.planning/phases/25-frontier-sweep-and-the-existence-gate-verdict/25-22-SUMMARY.md` — FOUND
- commits `2a4291f`, `72d5c82`, `3839da4` — all FOUND in `git log --all`
- `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md` — UNTOUCHED (the
  orchestrator owns those writes); no planning-state file appears in any of this plan's three commits
- working tree carries only the pre-existing, unrelated `M .gitignore`
