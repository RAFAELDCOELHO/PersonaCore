---
phase: 25-frontier-sweep-and-the-existence-gate-verdict
plan: 02
subsystem: frontier-verdict
tags: [FRONT-04, verdict, gate-10, clip-norm, condition-c, pre-registration]
requires:
  - scripts/mitigation_gate.py
  - scripts/erasure_gate.py
  - scripts/phase20_gate_coverage.py
  - scripts/phase25_condition_c.py
  - scripts/phase25_gate05.py
  - results/phase23_never_taught.json
  - results/phase23_cal03_wiring.json
provides:
  - scripts/phase25_verdict.py
  - "X = 0.006461685297443485 and its ZERO TOLERANCE sentence"
  - "prove_clip_norm_equality — the caller-side close of the hole capacity_comparison ignores"
  - "capacity_verdict — DP-only scoping, both refusals before the gate"
  - "arm_existential — the gate's own denominator-carrying claim, unmodified"
  - "curve_verdicts — the whole-curve CPU-only verdict stage"
  - "ADVERSARIAL_CAPACITY_RULE_ABSENT — the named absence"
affects:
  - "later Phase-25 waves that assemble the frontier artifact"
tech-stack:
  added: []
  patterns:
    - "committed literals read via ast.literal_eval over source, never imported (torch-free)"
    - "AST assertions over inspect.getsource, never grep over a file whose prose names the token"
    - "a defect in a frozen module asserted first, then closed caller-side"
key-files:
  created:
    - scripts/phase25_verdict.py
    - tests/test_phase25_verdict.py
  modified: []
decisions:
  - "The verdict call routes through phase20_gate_coverage.corrected_point_verdict, not the frozen pin — a committed repo-wide census refuses any scripts/ caller of mitigation_point_verdict and names that route as the sanctioned one."
  - "capacity_verdict refuses on ARM before it proves clip_norm equality; the plan ordered the reverse, which misattributes an adversarial point's refusal to a missing noise scale."
  - "D-42's published tolerance ('at most 2 successes of 416') is superseded by a measured 0, and the 5-seed pooling's real defect is structural unsatisfiability rather than tightness."
metrics:
  duration: "~35 min"
  completed: 2026-08-31
  tasks: 2
  commits: 2
  files: 2
  lines: 1255
  suite: "1794 passed, 1 skipped (baseline 1778/1; delta +16, exactly this plan's new cases)"
---

# Phase 25 Plan 02: The Existence-Gate Verdict Pass Summary

**One-liner:** A CPU-only, torch-free verdict pass that reaches FRONT-04's null branch through a
real `capacity_comparison` call, publishes X and its ZERO-TOLERANCE sentence from the frozen gate's
own reporter, sources all seven Area-7 kwargs from plans 25-21/25-22 rather than fabricating them,
and closes the one `clip_norm` hole the frozen gate structurally cannot see.

## What Shipped

| Artifact | Lines | What it holds |
|---|---|---|
| `scripts/phase25_verdict.py` | 631 | `never_taught_anchors`, `extraction_ceiling_and_tolerance`, `prove_clip_norm_equality`, `capacity_verdict`, `arm_existential`, `curve_verdicts`, `retention_floor_used`, `ADVERSARIAL_CAPACITY_RULE_ABSENT` |
| `tests/test_phase25_verdict.py` | 624 | 16 cases: the zero-tolerance sentence, the 5-seed refusal, the null branch reached live, the 999× hole watched then closed, the DP-only AST scoping, D-35 by AST, a full 21-kwarg assembly |

**Commits**

| Hash | Message |
|---|---|
| `53e5600` | `feat(25-02): the CPU-only verdict pass, assembled by importing the frozen gate` |
| `61fcab9` | `test(25-02): the null branch, the ZERO TOLERANCE sentence and the clip_norm hole watched` |

## The Three Quoted Strings (verbatim, as the plan requires)

**1. `tolerance_report(ceiling=X, n_questions=416)` — the ZERO TOLERANCE sentence.**
Source: `.venv/bin/python`, live call against `scripts/mitigation_gate.py` at HEAD.

```
X = 0.006462 -> tolerated 0/416 questions (0.0000%) — ZERO TOLERANCE: the criterion clears ONLY on
a perfect erasure, because a single leaked question already puts the upper bound above the ceiling
```

Full return value: `(0.006461685297443485, 0, 0.0, "<sentence above>")`.

**2. The 5-seed ceiling's `ValueError`.**
Source: `mitigation_gate.tolerance_report(ceiling=wilson_upper_bound(0, 2080), n_questions=416)`.

```
ceiling 0.001299052313275338 sits below wilson_upper_bound(0, 416) = 0.006461685297443485 — no
outcome clears it, not even a perfect one, so there is no tolerance to report. This is NOT the
zero-tolerance regime and must not be published as one. D-11 puts every X extraction_ceiling
produces strictly above this bound
```

**3. The `capacity_comparison` reason that ignored a 999× `clip_norm` divergence.**
Source: a live call with `small_mechanism["clip_norm"] = 1.0`, `large_mechanism["clip_norm"] = 999.0`,
all four `MECHANISM_KEYS` equal. It returned branch `'null-at-both-capacities'` with:

```
comparability: STRUCTURAL (D-25) — both points agree exactly on all 4 of ('sigma', 'steps',
'delta', 'q'), so they are compared at equivalent epsilon_fact with ZERO tolerance constant,
leaving capacity N the only free variable
```

## The Sentence the Plan Asks For, in One

**CONTEXT's D-42 figure "at most 2 successes of 416" is superseded by a measured 0** — condition (a)
compares a Wilson bound to a Wilson bound, and `wilson_upper_bound(1, 416) = 0.01070184962521955`
already exceeds `X = 0.006461685297443485` — **and the reason for rejecting the 5-seed pooling is
structural unsatisfiability, not a 4.97× tightening**: `tolerance_report` *raises* on the pooled
ceiling `0.001299052313275338` because no outcome clears it, not even a perfect one.

## Every Plan-Time Claim Re-Measured

| Claim | Plan/CONTEXT said | Measured at HEAD | Verdict |
|---|---|---|---|
| `X` | `0.006461685297443485` | `0.006461685297443485` | ✅ |
| tolerance at X | plan: `0`; **CONTEXT D-42: "at most 2"** | `0` | ✅ plan / ❌ CONTEXT |
| `wilson_upper_bound(1, 416)` | `0.010701849625219550` | `0.01070184962521955` | ✅ (same value) |
| 5-seed ceiling | raises `ValueError` | raises, text as quoted | ✅ |
| 999× `clip_norm` accepted by the gate | yes, "agree exactly on all 4" | yes, verbatim | ✅ |
| `mitigation_point_verdict` length | plan: **195**; CONTEXT: 198 | **195** | ✅ plan / ❌ CONTEXT |
| `epsilon`/`accounting` as `ast.Name`/`ast.arg` in that function | 0 | 0 (also 0 textually inside the function) | ✅ |
| `_ADAPTER_REGIME_RETENTION_FLOOR` | `0.008681618994239138` | same | ✅ |
| `_prove_retention_floor` on the borrowed floor | raises `SystemExit` | raises | ✅ |
| governing cap vs borrowed | `3.9085032379884783` < `4.029` | same | ✅ |
| headrooms | `-0.3112566543480071` vs `-0.1907598923364855` | same, from `RETENTION_LEG_BINDS_AT_ANCHOR` | ✅ |
| `extraction_ceiling(**pooled)` | `TypeError … 'draws_per_question'` | `extraction_ceiling() got an unexpected keyword argument 'draws_per_question'` | ✅ |
| `wilson_upper_bound` / `MARGIN_K` object identity | True | True | ✅ |
| never-taught provenance arm / seeds | `never-taught`, 5 seeds | same | ✅ |
| `capacity_comparison` resolves `arm` | 0 occurrences | 0 (`ast.Name` + `ast.arg`) | ✅ |
| `tests/test_phase20_gate.py` exists | "DOES NOT EXIST" | does not exist | ✅ |
| `mitigation_gate.py:426` = the provenance `_prove` | line 426 | line 426 | ✅ |

### One NEW measurably-false plan figure

The plan's `<environment>` block states: *"Never grep `mitigation_gate.py` for `epsilon`. Measured:
**25** string-literal occurrences with an `ast.Name` count of 0."*

Measured at HEAD on the same file:

```
grep -c  'epsilon' scripts/mitigation_gate.py  ->  34   (lines)
grep -o  'epsilon' scripts/mitigation_gate.py  ->  42   (occurrences)
```

Neither reading is 25. **Both readings are published; the warning's conclusion survives intact** —
the `ast.Name` count really is 0, so the textual form really would go false-RED, and the check was
written as an AST assertion over `inspect.getsource(mitigation_point_verdict)` rather than a file
grep. A second, smaller correction rides along: inside `mitigation_point_verdict`'s *own* source
`epsilon` occurs **0 times textually as well**, so the false-RED hazard is a property of the *file*,
not of the function — which is exactly why the check is scoped to the function.

The plan's `<environment>` baseline "1647 passed, 1 skipped" is also stale; the live pre-wave-2
baseline was 1778/1.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] The verdict call cannot go through the frozen pin; it routes through the sanctioned corrected route**
- **Found during:** Task 1, before writing (read the repo-wide censuses first).
- **Issue:** Task 1(f) instructs `curve_verdicts` to call `mitigation_point_verdict` per point.
  `tests/test_phase20_correction.py::test_mitigation_point_verdict_has_no_caller_outside_this_module`
  is a committed repo-wide AST census that walks `scripts/` and `src/` and goes RED on **any** call
  to, or import of, that name outside `scripts/phase20_gate_coverage.py`. Writing the plan literally
  would have reddened it.
- **Fix:** Declared through the census's own documented mechanism, never by weakening it:
  `curve_verdicts` calls `phase20_gate_coverage.corrected_point_verdict`, which the census names as
  the sanctioned route. That route calls the pin once and returns its `(verdict, reasons, arm)`
  unaltered while adding three corrections a direct caller does not get — real coverage on the
  extraction axis (raw-rate space is *unreachable*, the parameter that accepted it does not exist
  there), coverage on the held-out leg (the frozen 21-kwarg signature has no `sweep_heldout_recalls`
  parameter at all), and a retention-provenance check.
- **Effect on §R3:** none, and the conclusion is *strengthened*. The sanctioned route takes **four**
  whole-curve sequences where the pin takes two, so a per-point verdict is even less computable at
  point time.
- **Files:** `scripts/phase25_verdict.py`. **Commit:** `53e5600`.
- **Note:** the plan's Task 2(e) `test_a_full_21_kwarg_verdict_assembles` calls the pin **directly**
  and is kept exactly as written — the census records `tests/` as *deliberately excluded*, because
  driving the pin's own branches is the behavioural twin of the pin rather than a bypass.

**2. [Rule 1 — Bug] `capacity_verdict` refuses on ARM before it proves `clip_norm`; the plan ordered the reverse**
- **Found during:** Task 1(d) / Task 2(d).
- **Issue:** An adversarial point has *no mechanism at all* — no σ, no δ, no q, no C. Proving
  `clip_norm` first reports a **missing noise scale** where the real defect is a **DP-only
  instrument handed a non-DP point**. It also makes the plan's own
  `test_an_adversarial_point_is_refused_before_the_gate` unwritable, since that test asserts the arm
  message (`MECHANISM_KEYS`, `accounting: null`).
- **Fix:** arm refusal first, `clip_norm` proof second, gate third. Both refusals still precede the
  gate and `prove_clip_norm_equality` still runs before **every** `capacity_comparison` call, which
  is the property D-25 needs. This is the same misattribution class `phase20_gate_coverage`'s own
  extraction-floor sign check documents.
- **Files:** `scripts/phase25_verdict.py`. **Commit:** `53e5600`.

**3. [Rule 1 — Bug] `never_taught_anchors()` cannot be splatted into `extraction_ceiling` either**
- **Found during:** Task 1 verification (first run raised
  `TypeError: extraction_ceiling() got an unexpected keyword argument 'control_extraction_successes'`).
- **Issue:** §ledger 9's correction is *doubled*. The anchors dict carries the **verdict's** four
  parameter names; `extraction_ceiling` takes `nontarget_successes` / `nontarget_questions`. The two
  counts are one measurement under two names — "control" at the gate, "nontarget" at the ceiling.
- **Fix:** explicit four-name mapping at the ceiling call, with the reason written into the code.
- **Files:** `scripts/phase25_verdict.py`. **Commit:** `53e5600`.

### Signature and naming deviations, taken deliberately

**4. `curve_verdicts` takes a keyword-only `control_readings_by_arm`.** The plan pins
`curve_verdicts(records, arm, capacity)`; the three positionals are preserved exactly and one
keyword-only argument is added. `control_gap`, `control_taught_recall` and `control_heldout_recall`
have **no per-point source**, and `phase25_condition_c.prove_control_gap_not_borrowed`'s refusal is
**pairwise across arms** — handed a single reading its loop is vacuous and proves nothing. Taking the
whole mapping is what keeps D-47's refusal live rather than decorative.

**5. Two test names carry a `…tolerance…` suffix.** The plan's `<action>` names three cases in group
(a) of which only one contains "tolerance", while its own acceptance criterion requires
`-k "tolerance"` to collect **at least 3**. Resolved by extending two names with the plan's own name
as a strict prefix, so a grep for either pinned name still matches:
`test_one_leaked_question_already_exceeds_the_ceiling` → `…_zero_tolerance_arithmetic`;
`test_the_five_seed_ceiling_is_refused_outright` → `…_no_tolerance_to_report`.
`test_tolerance_report_says_zero_tolerance` is untouched (the `must_haves.contains` string).
Measured: `-k "tolerance"` collects and passes **3**.

**6. One test added beyond the plan's list.**
`test_curve_verdicts_judges_a_whole_leg_through_the_sanctioned_route` — `curve_verdicts` is the
function that actually spends the seven Area-7 kwargs, and the plan left it with no runnable check.
It exercises the real leg path, and asserts both refusals (the borrowed-control-gap object identity
and the empty leg).

### Not deviations, recorded so a reader does not re-derive them

- `scripts/mitigation_gate.py`, `mitigation_accountant.py`, `mitigation_unit.py`,
  `phase18_extraction.py` and `pyproject.toml` are **byte-unchanged**
  (`git diff --exit-code` exits 0). Zero installs (T-25-SC).
- The module is **torch-free and numpy-free** on import (measured:
  `'torch' in sys.modules` → `False`). `teach_persona.DP_ARMS` / `ADV_ARMS` and
  `phase18_extraction.GATED_TIER` / `REPORTED_TIER` are resolved through
  `phase25_gate05._committed_literal` — the `ast.literal_eval`-over-source mechanism plan 25-22
  shipped — because importing either module pulls torch.
- Line numbers are cited **only** where the plan cited them and they were re-verified
  (`mitigation_gate.py:426`); elsewhere symbols are named instead, per this repository's own
  recorded lesson that a statement's text and a symbol's name survive edits that line numbers do not.

## The Natural RED, and Proof the Guards Bind

The 16 cases went green on their first run, which is the state a reader should distrust. Two
independent probes were run rather than asserted:

1. **The frozen defect is real.** `mitigation_gate.capacity_comparison` was called *directly* with
   `clip_norm` 1.0 against 999.0 and returned `'null-at-both-capacities'` with the reason quoted
   above. That call is `test_capacity_comparison_ignores_a_999x_clip_norm_divergence` — it asserts a
   **defect in a frozen module that cannot be fixed there**, which is why the closure is caller-side.
2. **The caller-side prove is load-bearing.** With `phase25_verdict.prove_clip_norm_equality`
   neutered to a no-op in a live interpreter, `capacity_verdict` on the same divergent pair returned
   `null-at-both-capacities` — i.e. reached the gate and was accepted — and the guard test
   `test_the_caller_side_prove_refuses_what_the_gate_accepted` failed with
   `Failed: DID NOT RAISE <class 'SystemExit'>`. The RED was taken from the module's natural
   pre-Task-1 state (the function not existing), never from a planted-then-reverted probe.

The gate itself is monkeypatched to `pytest.fail` if reached, so "raises before ever reaching the
gate" is measured rather than inferred from the exception type.

## Verification

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest tests/test_phase25_verdict.py -q` | **16 passed, 0 skipped** |
| `.venv/bin/python -m pytest tests/test_phase25_verdict.py -k "tolerance" -q` | **3 passed**, 13 deselected |
| `.venv/bin/python -m pytest tests/test_phase20_prereg.py -k import_graph -q` | 1 passed |
| `.venv/bin/python -m pytest tests/ -q` | **1794 passed, 1 skipped**, 0 failed, in 468.93 s |
| Delta vs the 1778/1 baseline | **+16 passed, 0 new skips, 0 regressions** — exactly this plan's 16 new cases |
| `test_phase23_resume_epsilon_bit_identical` (known flaky) | **passed** this run |
| `git diff --exit-code` on the four frozen files + `pyproject.toml` | exits 0 |
| `make lint` | `All checks passed! / 244 files already formatted` |
| Task 1 acceptance criteria (9) | all pass; `extraction_ceiling_and_tolerance()` prints `0.006461685297443485` |
| Task 2 acceptance criteria (7) | all pass; `at most 2` appears only in prose, by AST |
| `.planning/STATE.md`, `.planning/ROADMAP.md` | untouched |

The pre-existing uncommitted `.gitignore` modification was left alone; only the two files this plan
created were staged.

## Threat Register Dispositions

| Threat ID | Disposition | How |
|---|---|---|
| T-25-07 | mitigated | The ZERO TOLERANCE sentence is asserted verbatim; `at most 2` is refused as executable code by an AST gate and survives only in docstrings; the correction is in the module docstring and here. |
| T-25-08 | mitigated | `prove_clip_norm_equality` runs before every `capacity_comparison` call; the hole is watched being accepted, then refused, with the gate monkeypatched to fail if reached. |
| T-25-09 | mitigated | `capacity_verdict` refuses on arm **first**; an AST walk proves the single `capacity_comparison` call is lexically inside it, and the census asserts it matched ≥ 1 site so an empty match cannot read as clean. |
| T-25-10 | mitigated | The null is the gate's own branch, reached live and compared against `_CAPACITY_DISPATCH[(False, False)]`; an AST check proves **no string constant** in `phase25_verdict.py` equals any `CAPACITY_BRANCHES` member. |
| T-25-11 | mitigated | X is `extraction_ceiling` over the designated seed's pooled block; `wilson_upper_bound` and `MARGIN_K` object identity asserted at import; the 5-seed `ValueError` watched. |
| T-25-11b | mitigated | All seven Area-7 kwargs imported from `phase25_condition_c` / `phase25_gate05` and `_prove`d to be real keyword-only parameters through `inspect.signature`; the seventh's name is taken from the producing function's `__name__` rather than spelled. |
| T-25-11c | mitigated | `retention_floor_used()` returns `phase25_condition_c.retention_floor_for_verdict()`, which runs `_prove_retention_floor` first; asserted `== 0.008681618994239138`. The borrowed `0.06893` cannot reach a verdict. |
| T-25-SC | accepted | Zero installs; `pyproject.toml` byte-unchanged. |

## Known Stubs

None. `curve_verdicts` is the only function without committed production input — no Phase-25 point
record exists yet, by design (the record schema is a later wave). It is exercised end-to-end on a
**fabricated-input demonstration labelled as one** (the 19-16 / D-30 register), and every value it
does not fabricate — X, the floors, the caps, the seven Area-7 kwargs — comes from a committed
record or a producer module.

## Threat Flags

None. The module opens two committed JSON records read-only, writes nothing, opens no socket, and
runs no subprocess. No new security-relevant surface.

## Self-Check: PASSED

- `scripts/phase25_verdict.py` — FOUND
- `tests/test_phase25_verdict.py` — FOUND
- commit `53e5600` — FOUND
- commit `61fcab9` — FOUND
