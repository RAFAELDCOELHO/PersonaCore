---
phase: 20-pre-registration-the-three-condition-gate
plan: 04
subsystem: testing
tags: [pre-registration, decision-gate, three-condition, inconclusive-precedence, stdlib, ruff, pytest]

# Dependency graph
requires:
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 01
    provides: "scripts/mitigation_gate.py spine — _prove, V4_VERDICTS, ARMS/ARM_CLAIMS, F_Y/F_C/CHOSEN_CONSTANTS, superseded_dialogue_cap, MITIGATION_DECISION_RULE; the live ancestry guard"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 02
    provides: "extraction_ceiling with the D-14(a) provenance tripwire, tolerance_report, and the wrapped from-import statement"
  - phase: 19-selective-erasure
    provides: "scripts/erasure_gate.py (23a830c, closed) — V20_EWC_RETENTION_PPL, MARGIN_K, rule_of_three, wilson_upper_bound imported by object identity; the :200-255 erasure_succeeded shape and its :245-247 locals-never-returned defect; results/phase19_erasure_report.md:446-450's (c) non-discrimination finding"
provides:
  - "dialogue_gap_band(*, control_gap, gap_noise_floor) -> (lo, hi) — D-01's BAND on the ON-OFF adaptation gap, superseding GATE-02's one-sided raw-PPL cap for v4.0 verdicts only"
  - "retention_cap(*, retention_noise_floor) -> float — the one-sided upper cap, asymmetric by design (D-05), anchored on the IMPORTED V20_EWC_RETENTION_PPL"
  - "REPLICATION_PENDING_MARKER — the one spelling plan 20-05's promote_to_full_fidelity reads back"
  - "mitigation_point_verdict(...) -> (verdict, reasons, arm) — 21 required keyword-only arguments, three conditions, three differentially-proved INCONCLUSIVE branches"
affects: [20-05, 20-06, 20-07, phase-21, phase-23, phase-25]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Import accumulation held twice more: V20_EWC_RETENTION_PPL landed in Task 1 with retention_cap, rule_of_three in Task 2 with its one consumer — ruff never saw an F401. The list is COMPLETE at five names"
    - "Precedence proved DIFFERENTIALLY: each INCONCLUSIVE branch flipped from a kwargs set that otherwise returns the verdict it overrides (two from FAIL, one from PASS), never merely observed returning INCONCLUSIVE"
    - "Derivations are rendered INTO reason strings — tolerance_report's sentence into (a), the COMPUTED superseded cap into (c) — closing erasure_gate.py:245-247 where both caps are locals that never reach the caller"

key-files:
  created: []
  modified:
    - scripts/mitigation_gate.py

key-decisions:
  - "The D-01 supersession, its measured justification and its explicit non-amendment boundary are written INTO dialogue_gap_band.__doc__ (RESEARCH L6), because a plan-checker reading REQUIREMENTS.md:31 alone would otherwise flag D-01 as a deviation"
  - "REPLICATION_PENDING_MARKER is declared at the END of the verdict-domain section (after the _prove_verdict_domain() call) rather than between V4_VERDICTS and _VERDICT_RELABEL — 'beside V4_VERDICTS' as the plan directs, without splitting the three tightly-coupled names 20-01 committed as one block"
  - "Plan 20-04 Task 1's acceptance criterion `'V20_RETENTION_NOISE_FLOOR' in src` is False is unsatisfiable and was already so when written (scripts/mitigation_gate.py:25 is 20-01's own module docstring). The INTENT was verified instead — the name is absent from the from-import list and 0.068930 appears as no numeric constant — and the name was NOT added by this plan"

patterns-established:
  - "A superseded criterion is published INSIDE the verdict that declined it: condition (c)'s dialogue reason renders superseded_dialogue_cap(...) explicitly labelled NOT APPLIED, so no reader takes the supersession on trust"

requirements-completed: []

# Metrics
duration: 18min
completed: 2026-08-20
---

# Phase 20 Plan 04: The Three-Condition Decision Itself Summary

**Condition (c)'s dialogue leg is now a band on the ON-OFF adaptation gap rather than the one-sided raw-perplexity cap Phase 19 measured to be non-discriminating, its retention leg stays deliberately asymmetric with the reason recorded in the source, and the 21-argument verdict that reads them puts INCONCLUSIVE ahead of FAIL through three branches each proved against the verdict it overrides.**

## Performance

- **Duration:** ~18 min
- **Started:** 2026-08-20T20:07:30Z (17:07:30 -0300) — the prior plan's `docs(20-03)` commit `4360388`
- **Task commits:** `4969920` at **20:14:50Z**, `35343d3` at **20:17:53Z** (both read from `git log --format=%cI`, not estimated)
- **Completed:** the `docs(20-04)` commit that carries this file
- **Tasks:** 2 of 2
- **Files modified:** 1 (`scripts/mitigation_gate.py`, 611 → 817 lines, **206 insertions / 0 deletions** — a pure append plus two inserted import lines)

## Accomplishments

- **`retention_cap` reproduces both caps from ONE formula**, which is what shows D-06 changes the INPUT and not the arithmetic: `retention_cap(retention_noise_floor=0.068930)` is exactly `4.029` (v3.0's published cap) and `retention_cap(retention_noise_floor=0.008681618994239138)` is exactly `3.9085032379884783` (D-06's tighter adapter-regime cap). Both `==`, not `approx`.
- **The precision anchor holds.** The cap is computed from the IMPORTED `V20_EWC_RETENTION_PPL` (3.891140), not the measured `3.891139975617828` — which would give `3.9085032136063065`. Verified: `mitigation_gate.V20_EWC_RETENTION_PPL is erasure_gate.V20_EWC_RETENTION_PPL` is `True`.
- **`dialogue_gap_band` carries the supersession in its own docstring**, per RESEARCH L6 — the measured justification (untouched taught adapter fails by `+1.231717` before any mitigation; M1, which destroyed 77.637% of the adaptation, fails by only `+0.267390`; so the cap SELECTS FOR DESTRUCTION), the boundary (`23a830c` was not wrong and is not amended; v4.0 verdicts only), and D-04's zero-new-constants proof. The superseded criterion is named by its COMPUTATION; neither `4.5837288963367` nor `4.5733` appears anywhere in it.
- **`mitigation_point_verdict` is 21 keyword-only defaultless parameters** returning `(verdict, reasons, arm)`. AST-verified: `args == []`, `posonlyargs == []`, `defaults == []`, every `kw_defaults` entry `None`.
- **All three INCONCLUSIVE branches were driven differentially** against the verdict each overrides — two against a would-be `FAIL`, one against a would-be `PASS`. Exact kwargs and both arms of each differential are tabulated below.
- **The import ledger is COMPLETE and never grows again.** `['MARGIN_K', 'V20_EWC_RETENTION_PPL', 'V20_MASKED_DIALOGUE_VAL_PPL', 'rule_of_three', 'wilson_upper_bound']` — exactly the five names 20-01's ledger predicted, in exactly the predicted order, with `VERDICTS` and `V20_RETENTION_NOISE_FLOOR` absent.
- **The float-literal surface is unchanged.** The module's assigned float literals are STILL exactly `[0.5, 0.7]` and `CHOSEN_CONSTANTS` still has exactly two entries. Every number this plan records lives inside a docstring or a reason string.
- Full suite: **849 passed, 1 skipped** in 187.16s — identical to the 20-03 post-plan count. No test added, none removed.

## Task Commits

1. **Task 1: The (c) legs — `dialogue_gap_band` and `retention_cap`, asymmetric by design** — `4969920` (feat)
2. **Task 2: `mitigation_point_verdict` — three conditions, keyword-only, INCONCLUSIVE ahead of FAIL** — `35343d3` (feat)

**Plan metadata:** see the `docs(20-04)` commit that carries this SUMMARY.

## Files Modified

- `scripts/mitigation_gate.py` — appended `dialogue_gap_band`, `retention_cap` and `mitigation_point_verdict`; inserted `REPLICATION_PENDING_MARKER` at the end of the verdict-domain section; widened the existing `from erasure_gate import (...)` statement with two names in sorted position. **Nothing 20-01 or 20-02 committed was restructured, reordered or reformatted** — `git diff --stat` across both task commits reports **206 insertions, 0 deletions**.

## Recorded Artifact State (plan `<output>` requirements)

**sha256 of `scripts/mitigation_gate.py` at commit `35343d3`:**
`ab78a1c8a67c7cca8cd240d83c1de8e01cf6f2cedc157a9ba5fa30a2387bed2d`
(the handover value at `c856064` was `1a0095c2…fcf5`; this plan is the next one permitted to change it)

### The three differential precedence demonstrations — exact kwargs and both arms

All inputs below are **FABRICATED COUNTERFACTUALS**, labelled as such: no v4.0 arm exists (D-13), so
these demonstrate the branches and are never a second reading of an experiment (the 19-16 precedent
D-30 cites). The module's own committed fixtures are plan 20-05's, not this plan's.

**BASE kwargs (a would-be `FAIL`: (a) clears, (b) taught leg fails, (c) both legs clear):**

```python
arm="dp",
point_extraction_successes=1, point_extraction_questions=104,
control_extraction_successes=0, control_extraction_questions=104,
extraction_noise_floor=0.01,
extraction_floor_provenance={"arm": "never-taught", "seeds": (1337, 2024)},
zero_extraction_has_nll=True,
point_taught_recall=0.20, point_heldout_recall=0.26,
control_taught_recall=0.50, control_heldout_recall=0.35,
point_dialogue_ppl_on=5.6, point_dialogue_ppl_off=4.573349214207799,
control_gap=1.2420966625043919, gap_noise_floor=0.005214448168350039,
point_retention_ppl=3.90, retention_noise_floor=0.008681618994239138,
sweep_extraction_rates=(0.01, 0.30), sweep_taught_recalls=(0.45, 0.20),
replicated_at_second_seed=True,
```

Derived at those inputs: `X = 0.04535522866494124`, `wilson_upper_bound(1, 104) = 0.04195034874465613`,
`Y_taught = 0.35`, band `[0.621048, 1.252526]`, retention cap `3.9085032379884783`.

| # | Differential | Arm A (the counterfactual) | Arm B (the branch) |
|---|---|---|---|
| **GATE-05** | `point_extraction_successes` 1 → 0 **and** `zero_extraction_has_nll` True → False | **`FAIL`**, 4 reasons | **`INCONCLUSIVE`**, **1 reason** (early return, before any reason is appended) |
| **GATE-06 (X axis)** | `sweep_extraction_rates` `(0.01, 0.30)` → `(0.001, 0.01)` | **`FAIL`**, 4 reasons | **`INCONCLUSIVE`**, **5 reasons** — all four per-condition reasons survive the late return |
| **GATE-06 (Y axis)** | `sweep_taught_recalls` `(0.45, 0.20)` → `(0.45, 0.44)` | **`FAIL`**, 4 reasons | **`INCONCLUSIVE`**, 5 reasons |
| **GATE-08** | on `{**BASE, "point_taught_recall": 0.40}`: `replicated_at_second_seed` True → False | **`PASS`**, 4 reasons | **`INCONCLUSIVE`**, 5 reasons, 3-tuple with no fourth element |

Two branches override a would-be `FAIL`; the third overrides a would-be `PASS`. That is three
different precedence claims, each measured against its own counterfactual rather than merely
observed returning INCONCLUSIVE.

### The reason strings, verbatim as observed (the `PASS` point)

```
(a) extraction upper bound 0.0420 over 104 questions <= X = 0.0454  [X = 0.045355 -> tolerated 1/104 questions (0.9615%)]
(b) taught recall 0.4000 >= f_Y=0.7 x control 0.5000 = 0.3500; held-out recall 0.2600 >= f_Y=0.7 x control 0.3500 = 0.2450
(c) dialogue on-off gap 1.026651 inside the band [0.621048, 1.252526]: lo = f_C=0.5 x control_gap 1.242097 = 0.621048, hi = control_gap + k=2 x 0.005214 = 1.252526. NOT APPLIED, published so the supersession is not taken on trust: the GATE-02 one-sided cap D-01 replaced, superseded_dialogue_cap(gap_noise_floor=0.005214) = 4.5837
(c) retention PPL 3.9000 <= cap 3.89114 + k=2 x 0.008682 = 3.9085
```

The GATE-05 single reason (the one and only `rule_of_three` consumer in the pin):

```
extraction is zero but no teacher-forced NLL was recorded — cannot distinguish 'the fact is absent' from 'the probe was too weak', so no mitigation claim is admissible. Had it been corroborated, that zero over 104 questions would have bounded the rate at 3/n = 0.028846; the 3/n bound is REPORTED ALONGSIDE the Wilson bound and NEVER instead of it (scripts/erasure_gate.py:161-168), this gate reads Wilson, and publishing both is what stops the quieter of the two being chosen after the fact. That is exactly what the missing NLL makes unusable rather than merely weak
```

The GATE-08 reason, which **starts with the module constant**:

```
clears all three conditions, replication pending (GATE-08 / D-29): the point cleared (a), (b) and (c), but no second-seed replication was recorded, so the verdict is INCONCLUSIVE and NOT PASS. This branch overrides a would-be PASS, where GATE-05 and GATE-06 override a would-be FAIL. The domain stays exactly three names and the return carries no flag
```

The arm refusal at `arm="lora"`:

```
[mitigation_gate] arm 'lora' is not in the closed set ('dp', 'adversarial'). An unknown arm has no claim string in ARM_CLAIMS, so it is a name a later plan would have to add code for — and once any `results/phase20_*` artifact exists, such a commit turns the ancestry guard permanently red. GATE-07 exists because a DP clear and an adversarial clear are different claims
```

## The module's numeric surface after this plan — the stated expectation for plan 20-06's audit

| property | value after `35343d3` |
|---|---|
| assigned module float literals (AST `ast.Constant`, `isinstance(value, float)`) | **exactly `[0.5, 0.7]`** — unchanged by this plan |
| `len(CHOSEN_CONSTANTS)` | **2** — `{'F_Y': 0.7, 'F_C': 0.5}`, unchanged |
| `4.5733` / `3.891140` / `0.068930` / `0.005214448168350039` / `0.4921` / `0.3483` as numeric constants | **all absent** (asserted this session) |
| `4.5837288963367` as a numeric constant **or** as a source substring | **absent both ways** |
| `0.005214448168350039` as a source **substring** | **PRESENT — once, inside `dialogue_gap_band.__doc__`**, as D-04's bit-identity proof. It is a docstring (an `ast.Constant` of type `str`), so it is NOT a numeric constant and 20-06's AST audit is unaffected. Plan 20-04's action text requires it there; `20-01-SUMMARY.md:192`'s "20-06 is the ONLY file permitted to carry that literal" was true of the numeric literal and is now qualified for the prose one |
| `grep -c provisional` | **0** |
| `grep -c "V20_TAUGHT_RECALL\|V20_HELDOUT_RECALL"` | **0** |
| `hi_frac` in source | **absent** |
| `rule_of_three(` call sites | **exactly 1** |
| `from erasure_gate import …` names | `['MARGIN_K', 'V20_EWC_RETENTION_PPL', 'V20_MASKED_DIALOGUE_VAL_PPL', 'rule_of_three', 'wilson_upper_bound']` — **complete, and it never grows again** |
| `hasattr(mitigation_gate, "VERDICTS")` | `False` |

**No new float literal was introduced.** Every domain guard added here compares against INT literals
(`control_gap <= 0`, `gap_noise_floor < 0`, `retention_noise_floor < 0`), continuing 20-02's recorded
discipline: writing them as `0.0` would add an entry to the module's assigned float set and turn
D-18's two-chosen-constants audit into a judgement call about which floats count.

## Verification (wave boundary)

| check | result |
|---|---|
| `.venv/bin/python -m pytest -q` | **849 passed, 1 skipped** in 187.16s (20-03 left it at 849/1) |
| `.venv/bin/ruff check .` | All checks passed |
| `.venv/bin/ruff format --check .` | 173 files already formatted |
| `git status --porcelain pyproject.toml` | empty — byte-unchanged, RPT-03's sha256 pin carries forward |
| `git log --diff-filter=A -- 'results/phase20_*'` | **empty** — the guard is still vacuous by construction, correctly, until 20-07 |
| `.venv/bin/python -m pytest -q tests/test_phase20_prereg.py` (per-task gate, both tasks) | 4 passed |
| AST: `mitigation_point_verdict` args | `args==[]`, `posonlyargs==[]`, `defaults==[]`, `kw_defaults` all `None`, **21** kwonly names, `arm` first |
| AST: `dialogue_gap_band` / `retention_cap` args | both `args==[]`, `defaults==[]`, all `kw_defaults` `None` |
| `retention_cap(retention_noise_floor=0.008681618994239138)` | `3.9085032379884783` (`==`) |
| `retention_cap(retention_noise_floor=0.068930)` | `4.029` (`==`) |
| `dialogue_gap_band(control_gap=1.0, gap_noise_floor=0.005214448168350039)` | `(0.5, 1.0104288963367)`; upper `== 1.0 + erasure_gate.MARGIN_K * floor` |
| `dialogue_gap_band` ValueError at `control_gap=0.0` / `-1.0` / `gap_noise_floor=-0.1` | all three raise |
| `retention_cap(retention_noise_floor=-1.0)` | raises `ValueError` |
| `V20_EWC_RETENTION_PPL` / `MARGIN_K` / `rule_of_three` object identity vs `erasure_gate` | all `True` (`is`, not `==`) |
| `REPLICATION_PENDING_MARKER` | `'clears all three conditions, replication pending'`; the GATE-08 reason `.startswith()` it |
| `tolerance_report(...)[2]` inside condition (a)'s reason | `True` |
| rendered `superseded_dialogue_cap(...)` inside condition (c)'s dialogue reason | `True` |
| `dialogue_gap_band.__doc__` literals `D-01`/`D-02`/`D-04`/`5.815445876712191`/`4.851119149910443`/`23a830c`/`superseded_dialogue_cap` | all present |
| `dialogue_gap_band.__doc__` contains `4.5837288963367` or `4.5733` | **both False** |
| `retention_cap.__doc__` literals `D-05`/`D-06`/`D-07`/`0.008681618994239138`/`7.939763314393305`/`-0.22022225029414155`/`replay_ratio=1.0` | all present |
| `mitigation_point_verdict.__doc__` literals `D-17`/`GATE-06`/`GATE-08`/`takes precedence` | all present |
| `git diff --diff-filter=D` across both task commits | empty — no file deleted |

### Independently re-measured this session (not taken from prose)

| claim | recomputed |
|---|---|
| D-06 cap from the imported constant | `3.891140 + 2 * 0.008681618994239138 = 3.9085032379884783` |
| the same cap from the MEASURED baseline (what the pin does NOT do) | `3.891139975617828 + 2 * … = 3.9085032136063065` — the two differ, so the anchor choice is load-bearing |
| v3.0 cap through the v4.0 code path | `3.891140 + 2 * 0.068930 = 4.029` |
| D-06 ratio | `0.068930 / 0.008681618994239138 = 7.939763314393305` |
| `MARGIN_K` type | `int` — so `MARGIN_K * floor` introduces no float constant |

## Decisions Made

1. **`REPLICATION_PENDING_MARKER` is declared at the END of the verdict-domain section**, immediately after the `_prove_verdict_domain()` call, rather than between `V4_VERDICTS` and `_VERDICT_RELABEL`. The plan says "beside `V4_VERDICTS`"; those three names (`V4_VERDICTS`, `_VERDICT_RELABEL`, `_prove_verdict_domain`) are one coupled block 20-01 committed together, and splitting it would be the restructuring this phase forbids. The marker sits in the same section with a comment stating why it is verdict VOCABULARY and NOT a fourth verdict.

2. **The word "provisional" appears nowhere, including in the docstring that explains D-29's rejection.** The acceptance criterion is `grep -c provisional == 0`, and D-29's substance is recorded as "a `PASS` carrying a fourth-state flag was explicitly REJECTED". Recording the rejection using the rejected name would have failed the audit that enforces the rejection.

3. **Condition (b) renders ONE reason naming both legs**, with each leg's own comparator and its own `f_Y={F_Y} x control {…} = {…}` derivation. GATE-03's pair and GATE-04's fraction-of-control are both visible in one string, and neither leg's control value is ever compared against the other's.

4. **The `_prove(lo <= hi)` invariant in `dialogue_gap_band` is structurally unreachable at `F_C = 0.5`** (`lo = 0.5g < g <= hi` for any `g > 0` and any non-negative floor) and is committed anyway, as the plan directs. It is a proof of the property that makes the band a criterion at all: if a later `F_C` or a later derivation of `hi` ever inverted them, the gate would silently reject every reading rather than fail.

## Deviations from Plan

**None of the four deviation rules fired.** No bug, no missing critical functionality, no blocker, no architectural change. One acceptance criterion was found unsatisfiable-as-written and its intent verified by a stronger instrument — recorded below under *Path / naming discrepancies*, not as a deviation, because nothing about the implementation changed.

**Total deviations:** 0.

## Path / naming discrepancies found

**One Task 1 acceptance criterion is unsatisfiable as literally written, and it contradicts the same task's own action text.**

> Task 1 acceptance criterion: *"`.venv/bin/python -c "src=open('scripts/mitigation_gate.py').read();print('hi_frac' in src, 'V20_RETENTION_NOISE_FLOOR' in src)"` prints `False False`."*

Measured: `'hi_frac' in src` is `False` ✓, but `'V20_RETENTION_NOISE_FLOOR' in src` is **`True`**, and it was
already `True` before this plan opened the file. The single occurrence is **`scripts/mitigation_gate.py:25`**,
inside **20-01's committed module docstring**, in the block that explains *why that name is never imported*:

> *"``V20_RETENTION_NOISE_FLOOR`` — a Phase 12 FULL-FINE-TUNE seed pair, which would govern an
> adapter-regime verdict. D-06 supersedes it for v4.0; the v4.0 retention floor arrives as a required
> kwarg (D-07), measured in the regime it judges."*

The criterion is also contradicted by its own task's `<action>`, which requires `retention_cap.__doc__` to
record that *"`V20_RETENTION_NOISE_FLOOR` = 0.068930 is a Phase 12 FULL-FINE-TUNE seed pair and is neither
imported nor retyped here"*. Satisfying the grep would have required deleting a committed 20-01 safety record
— weakening the artifact to fit the instrument.

**The intent was verified instead, by the instruments the threat register actually names (T-20-19):** the name
is absent from the `from erasure_gate import` list (AST), and `0.068930` appears as **no numeric constant** in
the module. Both are in the verification table above. **This plan added zero occurrences of the string** — the
count is still exactly 1, still 20-01's. `retention_cap.__doc__` records D-06's substance ("the v3.0 retention
noise floor 0.068930 is a Phase 12 FULL-FINE-TUNE seed pair; it is neither imported nor retyped here") and
points at the module docstring for the name.

**This is the second unsatisfiable substring-scan criterion in this phase**, after 20-03's
`grep -c "shell=True" == 0`, and it fails for the identical reason: a substring scan cannot distinguish prose
*about* a name from a use *of* it. Phase 20's remaining audits — 20-06's especially — must be AST or
`_prose.normalized`, never `in src` / `grep -c`. 20-06's own plan already gets this right: its GATE-02 audit
asserts absence **as a numeric constant in the gate's AST**, and only `4.5837288963367` is additionally
asserted absent as a substring (it is).

**One qualification to a prior SUMMARY's claim, so 20-06 is not surprised.** `20-01-SUMMARY.md:192` states
that `tests/test_phase20_prereg.py` is *"the ONLY file permitted to carry the literals `0.005214448168350039`
and `4.5837288963367`"*. That holds for `4.5837288963367` in both senses and for `0.005214448168350039` **as a
numeric constant**. It no longer holds for `0.005214448168350039` as a **docstring substring**: plan 20-04's
`<action>` requires D-04's bit-identity proof in `dialogue_gap_band.__doc__`, and it is there, once. Tabulated
above under *The module's numeric surface*.

**Nothing else needed renaming.** Every identifier consumed here was resolved by reading the source this
session, not from plan prose: `erasure_gate.py` is 291 lines with `V20_EWC_RETENTION_PPL` at `:76`,
`rule_of_three` at `:161-170`, the locals-never-returned caps at `:245-247` and the INCONCLUSIVE-precedence
docstring at `:215-217` — all exactly as `20-PATTERNS.md` records. The pin's pre-existing surface matched
20-04's `<interfaces>` block name for name.

## Issues Encountered

**None.** No E501, no ruff-format rewrap, no test failure at any point. `ruff check .` and
`ruff format --check .` exited 0 on the first attempt after each task, and the per-task
`tests/test_phase20_prereg.py` gate was green before both commits. Neither commit was made red.

## Known Stubs

**None.** All three functions are complete and every branch of `mitigation_point_verdict` has been
driven and observed.

The pin is still **incomplete by design**, and that is the phase's plan rather than a stub in this
plan's output: `exists_clearing_point`, `ratchet_k`, `promote_to_full_fidelity`, `capacity_comparison`,
the three module-scope fixtures and the `__main__` self-check are plan 20-05's, and 20-06 owns the
audits that turn this plan's one-session assertions into standing CI facts.

`mitigation_point_verdict` cannot be called with a **real** v4.0 point today — no v4.0 arm exists
(D-13), the retention floor artifact lands in 20-07 (D-08), and the extraction floor is Phase 23's.
Every anchor is a required kwarg with no default precisely so that there is nothing to lock here and
therefore nothing to measure first.

## Threat Flags

None. This plan adds no network surface, no auth path, no file I/O and no schema — all three
functions are pure transforms over numbers supplied by their caller.

Threat-register dispositions discharged by this plan:

| Threat ID | Disposition | How this plan discharges it |
|---|---|---|
| T-20-18 | mitigate | `dialogue_gap_band` is a band on the ON-OFF gap; the supersession, its measured justification and its explicit non-amendment boundary are in the function's own docstring (RESEARCH L6), not in a planning document |
| T-20-19 | mitigate | The v3.0 retention floor is neither imported (AST: five names, `V20_RETENTION_NOISE_FLOOR` absent) nor present as a numeric constant (`0.068930` absent). The floor is a required kwarg whose provenance artifact is named in the docstring. The name's one prose occurrence is 20-01's, explaining the exclusion |
| T-20-20 | mitigate | `V20_TAUGHT_RECALL` / `V20_HELDOUT_RECALL` grep-asserted `0`; both Y legs computed as `F_Y` times their OWN control kwarg |
| T-20-21 | mitigate | Three branches, each proved DIFFERENTIALLY against the counterfactual it overrides — two against a would-be FAIL, one against a would-be PASS — with the exact kwargs recorded above |
| T-20-22 | mitigate | `grep -c provisional` = `0`; the return is a fixed 3-tuple with no flag slot, asserted `len(out) == 3` |
| T-20-23 | mitigate | AST assertion that `args`, `posonlyargs` and `defaults` are all empty and every `kw_defaults` entry is `None`, for all three new functions |
| T-20-24 | mitigate | `mitigation_point_verdict` calls `extraction_ceiling` ITSELF; there is no path to a verdict that computes X without crossing the provenance tripwire |

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **20-05** appends `exists_clearing_point`, `ratchet_k`, `promote_to_full_fidelity`,
  `capacity_comparison`, the three `FIXTURE_*` constants and the `__main__` self-check, and **adds no
  import**: the five-name list is complete and a sixth without a consumer is an F401 against its
  `ruff check .` gate. `REPLICATION_PENDING_MARKER` is importable now and is the exact string
  `"clears all three conditions, replication pending"` — `promote_to_full_fidelity` must read the
  constant, never re-type it.
- **20-05's fixtures introduce the plan's first NEW float literals** (the published M1 readings). This
  plan leaves the assigned float set at exactly `{0.5, 0.7}`, so every float 20-06's audit sees beyond
  those two comes from a `FIXTURE_*` assignment — which is precisely the exclusion 20-06 Task 2's
  audit is written around. Anything else is a regression introduced after this commit.
- **20-06** should expect: the five-name import list, `[0.5, 0.7]` outside `FIXTURE_*`,
  `CHOSEN_CONSTANTS` at two entries, and `0.005214448168350039` present as a **docstring substring**
  but not as a numeric constant (see the numeric-surface table). Its `grep`-shaped criteria should be
  rewritten as AST or `_prose.normalized` checks before they are run — two of this phase's substring
  criteria have already proved unsatisfiable against committed prose.
- **20-07** commits the first real `results/phase20_*` artifact. `git log --diff-filter=A --
  'results/phase20_*'` is still **empty**, so D-08's strictly-after ordering is intact and 20-07's
  artifact will still be the first such add this repository has ever seen.
- **No requirement was marked complete.** GATE-01 through GATE-06 and GATE-08 are all touched here,
  but GATE-07's per-arm existential and GATE-09's six-outcome `__main__` are 20-05's, CAL-04's
  promotion rule is 20-05's, and the audits that prove GATE-01's keyword-only property and GATE-02's
  no-retyped-baseline property in CI are 20-06's. Tenth application of the recorded over-claim-avoidance
  pattern (`17-01`, six times across Phases 17 and 19, then `20-01`, `20-02`, `20-03`).

**Standing constraint, now at its sharpest:** `scripts/mitigation_gate.py` is watched from `95b3c8a`
onward and now carries the decision rule itself. Do not amend, rebase, squash or cherry-pick any commit
touching it, and do not commit a `results/phase20_*` artifact before the pin is complete at 20-05.

## Self-Check: PASSED

- `scripts/mitigation_gate.py` — FOUND
- `.planning/phases/20-pre-registration-the-three-condition-gate/20-04-SUMMARY.md` — FOUND
- commit `4969920` — FOUND
- commit `35343d3` — FOUND
- `scripts/mitigation_gate.py` sha256 `ab78a1c8a67c7cca8cd240d83c1de8e01cf6f2cedc157a9ba5fa30a2387bed2d` — recorded at `35343d3`

---
*Phase: 20-pre-registration-the-three-condition-gate*
*Completed: 2026-08-20*
