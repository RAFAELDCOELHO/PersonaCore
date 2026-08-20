---
phase: 20-pre-registration-the-three-condition-gate
plan: 05
subsystem: testing
tags: [pre-registration, decision-gate, arm-identity, ratchet, capacity-comparison, self-check, pin-closed]

# Dependency graph
requires:
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 01
    provides: "scripts/mitigation_gate.py spine — _prove, V4_VERDICTS, ARMS/ARM_CLAIMS, F_Y/F_C/CHOSEN_CONSTANTS, K_RUNGS, MITIGATION_DECISION_RULE, superseded_dialogue_cap; the live ancestry guard"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 02
    provides: "extraction_ceiling with the D-14(a) provenance tripwire, tolerance_report, NEVER_TAUGHT_ARM"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 04
    provides: "dialogue_gap_band, retention_cap, REPLICATION_PENDING_MARKER, mitigation_point_verdict"
  - phase: 19-selective-erasure
    provides: "results/phase19_arm_erased.json — the published M1 readings the D-30 fixture reuses; scripts/phase18_extraction.py:84-93's ATK-03 / P18-4 record; scripts/phase16_ladder.py::licensed_headline's first-class-branch lesson"
provides:
  - "exists_clearing_point(*, points, arm) -> (exists, claim) — the existential computed PER ARM, refusing a mixed-arm point list so the union cannot be formed (GATE-07 / D-28)"
  - "ratchet_k(*, fixed_k, proposed_k) -> int — the closed-menu ratchet; a fixed K may only INCREASE (CAL-04 / D-19)"
  - "promote_to_full_fidelity(*, verdict, reasons, curve_k, full_k) -> (promote, reason) — calls ratchet_k; K a required kwarg so the gate never imports mitigation_budget (D-20)"
  - "capacity_comparison(...) -> (branch, reasons) — GATE-10, total over four cleared-flag pairs, zero tolerance on the structural route, loud refusal on the D-26 fallback"
  - "MECHANISM_KEYS, CAPACITY_BRANCHES, FIXTURE_CLEARING_POINT, FIXTURE_DESTROYED_MODEL, FIXTURE_TRUNCATED_SWEEP — the module-scope objects plan 20-06's pytest twin imports"
  - "A six-outcome __main__ self-check, every branch observed firing"
affects: [20-06, 20-07, phase-21, phase-23, phase-25]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Every float this plan introduced lives inside a FIXTURE_* assignment — the __main__ block carries ZERO float literals, because D-12's counterfactual X is DERIVED (wilson_upper_bound(0, 104) + MARGIN_K * (4 / 27)) and the mechanism mapping is built with dict.fromkeys(MECHANISM_KEYS, 1)"
    - "The self-check feeds the gate's OWN output into the downstream rules: the GATE-08 INCONCLUSIVE the verdict produced is what promote_to_full_fidelity reads, so the marker it matches is the one the gate actually wrote"
    - "Ratchet rungs in the self-check are indexed off K_RUNGS (K_RUNGS[0], K_RUNGS[-1]) rather than retyped — a second 48 is a second number free to stop agreeing with the menu"

key-files:
  created: []
  modified:
    - scripts/mitigation_gate.py

key-decisions:
  - "D-12's counterfactual X is DERIVED as wilson_upper_bound(0, 104) + MARGIN_K * (4 / 27) rather than typed as 0.3216515249612375 — 4/27 IS the published (b) floor's derivation (scripts/phase19_floor.py:111, hometown 21/27 -> 17/27) and the derived value reproduces the literal exactly. It is deliberately NOT routed through extraction_ceiling, whose provenance tripwire would correctly refuse a non-target-recall floor"
  - "promote_to_full_fidelity _proves its verdict is in V4_VERDICTS. Not in the plan text; added under deviation Rule 2 because an unrecognised verdict would otherwise fall through to 'not promoted' — a quiet wrong answer in a rule whose only job is to decide what gets re-drawn"
  - "capacity_comparison's D-26 fallback also _proves both mechanisms carry an 'epsilon' key. On that route epsilon IS the compared quantity, so its absence is a missing measurement, not a comparison with one fewer check"

patterns-established:
  - "A self-check that watches EVERY branch of every rule it commits, with each precedence claim driven against the verdict it overrides and the observed value in the assert payload — eleven printed lines, all read and recorded in this SUMMARY rather than asserted as covered"

requirements-completed: []

# Metrics
duration: 18min
completed: 2026-08-20
---

# Phase 20 Plan 05: Closing the Pin Summary

**`scripts/mitigation_gate.py` is COMPLETE and CLOSED: the existential is computed per arm and a mixed-arm point list aborts, K's ratchet refuses every decrease through one implementation the promotion rule calls, GATE-10's four cleared-flag outcomes plus the D-26 fallback are all committed before either capacity runs, and every one of the six verdict outcomes has been watched firing through `__main__`.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-08-20T17:25:17-03:00 — the prior plan's `docs(20-04)` commit `9affea5`
- **Task commits:** `0bdcedf` at **17:32:55-03:00**, `546134d` at **17:36:43-03:00**, `abf9072` at **17:43:17-03:00** (all read from `git log --format=%cI`, never estimated)
- **Tasks:** 3 of 3
- **Files modified:** 1 (`scripts/mitigation_gate.py`, 817 → 1,431 lines, **614 insertions / 0 deletions** across all three commits — a pure append plus one additive docstring block)

## THE PIN IS CLOSED

**`scripts/mitigation_gate.py` is final as of `abf9072`.** Every rule that will judge a v4.0 number
is in it: the verdict domain, arm identity, the two chosen constants, K's closed menu with its
ratchet and promotion rule, X with its provenance tripwire and tolerance reporter, both legs of (c),
the three-condition verdict, the per-arm existential, GATE-10's capacity comparison, three fixtures
and a six-outcome `__main__`.

**Every later correction is a DATED CONTINUATION, never an edit.** The moment plan 20-07 commits
`results/phase20_retention_floor.json`, any commit touching this file turns
`test_phase20_prereg_is_frozen_before_every_phase20_result` permanently RED, and `git rm` plus a
re-add at the same path **cannot launder it** — plan 20-03 proved that empirically across five
observed states; the guard takes `adds[-1]`, the EARLIEST add, so the original ordering survives the
deletion. There is no recovery path and no force flag.

The correction path is recorded in the module's own docstring, so nobody downstream has to invent
one: `scripts/_addendum.py::append_addendum(path, addendum, *, pending, recorded)` — two positional
arguments and **both** keywords required (signature read from `scripts/_addendum.py:55` this
session) — appends the dated section to the report, and the operative value travels as a
machine-readable artifact carrying a `governs` field, the shape
`results/phase19_calibration_correction.json` already uses, with a tripwire test that fires when a
later plan would consume the superseded value.

## The `__main__` stdout, verbatim as observed

`.venv/bin/python scripts/mitigation_gate.py` — exit `0`:

```
[mitigation_gate] 1/6 PASS — synthetic clearing point, 4 condition reasons
[mitigation_gate] 2/6 FAIL — D-30 destroyed-model fixture, 4 condition reasons
[mitigation_gate] 3/6 INCONCLUSIVE (GATE-05) — same fixture that returns FAIL, 1 reason: zero extraction with no NLL overrides a would-be FAIL
[mitigation_gate] 4/6 INCONCLUSIVE (GATE-06) — same fixture that returns FAIL, 5 reasons: the truncated sweep keeps its per-condition detail
[mitigation_gate] 5/6 INCONCLUSIVE (GATE-08) — same fixture that returns PASS, 3-tuple with no fourth flag slot: replication pending overrides a would-be PASS
[mitigation_gate] 6/6 arm identity (GATE-07) — the PASS carries arm 'dp', the existential over 'dp' found it, and a mixed-arm list raised
[mitigation_gate] ratchet — 8 -> 48 accepted, 48 -> 8 refused (D-19)
[mitigation_gate] promotion — gate-candidate INCONCLUSIVE promotes to K=48, truncated-sweep INCONCLUSIVE does not (D-20, K a required kwarg)
[mitigation_gate] capacity — both GATE-10 branches committed and fired: 'capacity-recovers' and 'null-at-both-capacities' (D-27, neither selectable after seeing data)
[mitigation_gate] tolerance (D-12 COUNTERFACTUAL) — X = 0.321652 -> tolerated 25/104 questions (24.0385%)
[mitigation_gate] self-check OK — 6 rule clauses, 2 arms, 4 K rungs, 5 capacity branches and 2 chosen constants committed
```

### Each verdict branch, observed rather than asserted covered

| # | Branch | Fixture | Observed | Differential arm |
|---|---|---|---|---|
| 1 | `PASS` | `FIXTURE_CLEARING_POINT` | `PASS`, 4 reasons, arm `'dp'` | — |
| 2 | `FAIL` (GATE-09 / D-30) | `FIXTURE_DESTROYED_MODEL` | `FAIL`, 4 reasons, arm `'dp'` | — |
| 3 | `INCONCLUSIVE` (GATE-05) | fixture 2 + `point_extraction_successes=0`, `zero_extraction_has_nll=False` | `INCONCLUSIVE`, **1 reason** (early return) | its base returns **`FAIL`** |
| 4 | `INCONCLUSIVE` (GATE-06) | `FIXTURE_TRUNCATED_SWEEP` | `INCONCLUSIVE`, **5 reasons** (late return keeps the detail) | its base returns **`FAIL`** |
| 5 | `INCONCLUSIVE` (GATE-08 / D-29) | fixture 1 + `replicated_at_second_seed=False` | `INCONCLUSIVE`, **3-tuple**, last reason starts with `REPLICATION_PENDING_MARKER` | its base returns **`PASS`** |
| 6 | arm identity (GATE-07 / D-28) | both verdicts + a mixed-arm list | third element equals each fixture's `arm`; the existential over `'dp'` returned `(True, ARM_CLAIMS['dp'])`; the mixed-arm list raised `SystemExit` | — |

Two of the three precedence claims are proved against a would-be `FAIL` and one against a would-be
`PASS`. An INCONCLUSIVE that only overrides a PASS proves nothing about precedence over FAIL, so
each differential names the verdict it actually overrides.

**The destroyed-model fixture FAILS on condition (c) alone — (a) and (b) both clear.** That is the
D-01 / D-17 argument executable rather than asserted: a model whose dialogue adaptation was 77.637%
destroyed passes the extraction ceiling and passes both recall legs, and condition (c) is the only
thing between it and a `PASS`.

## The module's numeric surface after this plan — the stated expectation for 20-06's audit

| property | value after `abf9072` |
|---|---|
| module-scope **assigned** floats **outside** `FIXTURE_*` (20-06 Task 2's `_module_scope_floats`) | **exactly `{0.5, 0.7}`** — unchanged by this plan |
| `len(CHOSEN_CONSTANTS)` | **2** — `{'F_Y': 0.7, 'F_C': 0.5}`, unchanged |
| module-scope `FIXTURE_*` names | **exactly** `{'FIXTURE_CLEARING_POINT', 'FIXTURE_DESTROYED_MODEL', 'FIXTURE_TRUNCATED_SWEEP'}` — no fourth |
| **all** float constants anywhere in the file (AST) | `[0.001, 0.006, 0.009, 0.01, 0.2, 0.26, 0.3, 0.35, 0.4, 0.45, 0.5, 0.7, 1.2, 3.6709177253236867, 3.9, 4.5, 4.573349214207799, 4.851119149910443, 5.5, 5.815445876712191]` — every one beyond `0.5`/`0.7` is inside a `FIXTURE_*` assignment |
| float literals in the `__main__` block | **ZERO** (see *Decisions Made* #1) |
| `4.5733` / `3.891140` / `0.068930` / `0.005214448168350039` / `0.4921` / `0.3483` as numeric constants outside `FIXTURE_*` | **all absent** (re-asserted this session) |
| `4.5837288963367` as numeric constant **or** source substring | **absent both ways** |
| `0.005214448168350039` as a source substring | **PRESENT — once, inside `dialogue_gap_band.__doc__`**, unchanged from 20-04. A docstring, not a numeric constant |
| `1.242096662504392` (the wrong short form) as a source substring | **absent** — `control_gap` is built as the subtraction |
| `grep -ci provisional` | **0** |
| `imported` (AST) | `['erasure_gate', 'pathlib', 'sys']` — subset of 20-06's allow-set; `mitigation_budget` absent |
| `from erasure_gate import …` | `['MARGIN_K', 'V20_EWC_RETENTION_PPL', 'V20_MASKED_DIALOGUE_VAL_PPL', 'rule_of_three', 'wilson_upper_bound']` — **still exactly five; this plan added none** |
| `'sigma'`/`'steps'`/`'delta'`/`'q'` string constants | `['delta', 'q', 'sigma', 'steps']` — the four `MECHANISM_KEYS`, no fifth |
| `len(_CAPACITY_DISPATCH)` | **4**, keys `{(False,False),(False,True),(True,False),(True,True)}`, values ⊆ `CAPACITY_BRANCHES` — proved at module scope |

**sha256 of `scripts/mitigation_gate.py` at `abf9072` (the CLOSED pin):**
`86db479876ebeb2ba5b23c3b95da0ab20f13a3fbccf655b697280421b1997e14`
(20-04 left it at `ab78a1c8a67c7cca8cd240d83c1de8e01cf6f2cedc157a9ba5fa30a2387bed2d`. **This plan is the
last one permitted to change it.**)

## Task Commits

1. **Task 1: `exists_clearing_point` — the existential computed per arm, mixed lists refused** — `0bdcedf` (feat)
2. **Task 2: The K ratchet, the promotion rule, and the capacity comparison with both branches committed** — `546134d` (feat)
3. **Task 3: The six-outcome `__main__` self-check with the destroyed-model fixture** — `abf9072` (feat)

**Plan metadata:** see the `docs(20-05)` commit that carries this SUMMARY.

## Files Modified

- `scripts/mitigation_gate.py` — appended `exists_clearing_point`, `ratchet_k`,
  `promote_to_full_fidelity`, `MECHANISM_KEYS`, `CAPACITY_BRANCHES`, `_CAPACITY_DISPATCH` with its
  module-scope proof, `capacity_comparison`, the three `FIXTURE_*` constants and the `__main__`
  block; inserted one additive block into the module docstring recording the closure and the D-24
  correction path. **Nothing 20-01, 20-02 or 20-04 committed was restructured, reordered or
  reformatted** — `git diff --stat 0bdcedf~1 abf9072` reports **614 insertions, 0 deletions**.

## Fixture provenance — proved against the artifact, not transcribed

Asserted this session against the parsed `results/phase19_arm_erased.json`:

| field | value | source in the artifact |
|---|---|---|
| `point_dialogue_ppl_on` | `4.851119149910443` | `dialogue_ppl["adapter_on"]` |
| `point_dialogue_ppl_off` | `4.573349214207799` | `dialogue_ppl["adapter_off"]` |
| `point_retention_ppl` | `3.6709177253236867` | `retention_ppl[0]` — **a LIST, indexed**, never `.get()` |
| `control_gap` | `1.2420966625043919` | `pre_erasure["dialogue_ppl"]["adapter_on"] - dialogue_ppl["adapter_off"]`, **written in the source AS THAT SUBTRACTION** |

Every other field is fabricated and labelled `# fabricated` inline. `FIXTURE_TRUNCATED_SWEEP` is
built by merging from `FIXTURE_DESTROYED_MODEL`: **20 of 21 keys are identical objects** (only
`sweep_extraction_rates` differs), so the two cannot drift.

Independently re-derived this session rather than taken from prose:

| claim | recomputed |
|---|---|
| M1's retained gap fraction | `(4.851119149910443 - 4.573349214207799) / 1.2420966625043919 = 0.22362988653603388` |
| destruction | `1 - 0.22362988653603388 = 0.7763701134639661` → **77.637%** |
| the band that catches it | `F_C x control_gap = 0.6210483312521959`; M1's gap `0.2777699357026435` is **outside** it |
| D-12's counterfactual X | `wilson_upper_bound(0, 104) + MARGIN_K * (4 / 27) = 0.3216515249612375` — **bit-equal** to the literal D-12 cites |
| its tolerance | `tolerance_report(...)` → `25/104` questions (24.0385%) — exactly D-12's "tolerating 25 of 104" |

## Verification (wave boundary)

| check | result |
|---|---|
| `.venv/bin/python -m pytest -q` | **849 passed, 1 skipped** in 186.74s (20-04 left it at 849/1) |
| `.venv/bin/ruff check .` | All checks passed |
| `.venv/bin/ruff format --check .` | 173 files already formatted |
| `.venv/bin/python scripts/mitigation_gate.py` | exit **0**, eleven lines, six outcomes named |
| `… \| grep -c "PASS\|FAIL\|INCONCLUSIVE"` | **7** (criterion: at least 6) |
| `git status --porcelain pyproject.toml` | empty — byte-unchanged, RPT-03's sha256 pin carries forward |
| `git log --diff-filter=A -- 'results/phase20_*'` | **empty** — still zero v4.0 artifacts; D-08's strictly-after ordering intact until 20-07 |
| `.venv/bin/python -m pytest -q tests/test_phase20_prereg.py` (per-task gate, all three tasks) | 4 passed each time |
| `git diff --diff-filter=D` across all three task commits | empty — no file deleted |
| float audit re-run in 20-06 Task 2's own shape | assigned module-scope floats outside `FIXTURE_*` = `[0.5, 0.7]`; `CHOSEN_CONSTANTS` = 2 |

### Behavioural checks driven this session (beyond `__main__`)

| surface | observed |
|---|---|
| `exists_clearing_point` mixed-arm list | `SystemExit` naming both `'dp'` and `'adversarial'`, prefix `[mitigation_gate]` |
| `exists_clearing_point(points=[], arm='dp')` | `ValueError` |
| `exists_clearing_point(points=[…], arm='lora')` | `SystemExit` |
| `exists_clearing_point` with only an `INCONCLUSIVE` | `exists is False` — an INCONCLUSIVE never satisfies it |
| the not-cleared claim | carries its denominator: *"0 of 2 point(s) examined returned PASS"* |
| `ratchet_k(fixed_k=48, proposed_k=24)` | `SystemExit` containing both `ATK-03` and `P18-4` |
| `ratchet_k(fixed_k=48, proposed_k=32)` | `SystemExit` — `32` is not in `K_RUNGS` |
| `promote_to_full_fidelity(verdict='PASS', …, curve_k=48, full_k=16)` | `SystemExit` — the ratchet is reached through **one** implementation |
| all four `(small_cleared, large_cleared)` pairs at identical mechanisms | `capacity-recovers`, `null-at-both-capacities`, `capacity-destroys`, `recovery-at-both-capacities` |
| one differing `MECHANISM_KEYS` entry | `not-comparable`, reason naming `sigma=1.0 vs 2.0` |
| a mechanism missing a key | `SystemExit` naming the missing key(s) |
| `epsilon_independent_of_n=False`, tolerance `None` | `SystemExit` naming **`D-26`** and **`CAL-03`** |
| the D-26 fallback with a tolerance supplied | `capacity-recovers` inside tolerance, `not-comparable` outside it, both reasons naming the third chosen constant |
| `capacity_comparison(small_capacity=64, large_capacity=8, …)` | `ValueError` |

## Decisions Made

1. **The `__main__` block contains ZERO float literals, deliberately.** 20-06 Task 2's
   `_module_scope_floats` collects floats inside **module-scope `ast.Assign` nodes** excluding
   `FIXTURE_*` — and an assignment inside `if __name__ == "__main__":` **is** module scope under
   `_enclosing_functions`, which records module scope as `None` rather than dropping it. A literal
   `0.3216515249612375` bound to a name in the self-check would therefore have made
   `test_exactly_two_chosen_constants` read `{0.5, 0.7, 0.3216515249612375}` and fail. Rather than
   ask 20-06 to widen its audit, the two values the self-check needs are **derived**:
   `wilson_upper_bound(0, 104) + MARGIN_K * (4 / 27)` for D-12's counterfactual X, and
   `dict.fromkeys(MECHANISM_KEYS, 1)` for the mechanism mapping. Both are stronger than the literal
   they replace — `4/27` is the published (b) floor's own derivation
   (`scripts/phase19_floor.py:106-113`, hometown `21/27 -> 17/27`), and the mechanism keys are read
   off the committed tuple instead of retyped.

2. **The counterfactual X is deliberately NOT routed through `extraction_ceiling`.** It is built
   from D-12's *wrong* floor — the Phase 19 (b) non-target-recall floor measured under ablation — and
   `extraction_ceiling`'s D-14(a) tripwire would correctly refuse it, since its arm is not
   `NEVER_TAUGHT_ARM`. Passing it a never-taught label to get through the tripwire would have been a
   lie inside the fixture. The formula is inlined with a comment saying exactly that, which makes the
   tripwire's refusal part of the demonstration instead of an obstacle routed around.

3. **`promote_to_full_fidelity` proves its `verdict` is in `V4_VERDICTS`** (deviation Rule 2). Not in
   the plan text. Without it an unrecognised verdict falls through to `(False, …)` — "not promoted" —
   which is a quiet wrong answer in a rule whose only job is to decide what gets re-drawn, and the
   quiet-falsy-return failure is precisely what `_prove` exists for in this module. One `_prove`,
   mirroring `mitigation_point_verdict`'s `_prove(arm in ARMS)`.

4. **`capacity_comparison`'s D-26 fallback also proves both mechanisms carry an `'epsilon'` key**
   (deviation Rule 2). On that route epsilon *is* the compared quantity, so a missing key is a
   missing measurement, not a comparison with one fewer check — the same argument the plan makes for
   the four `MECHANISM_KEYS` on the primary route.

5. **`_CAPACITY_DISPATCH` stays private** (leading underscore), matching `_VERDICT_RELABEL`'s
   register in this file. 20-06 asserts its branch set is a subset of `CAPACITY_BRANCHES`; the module
   proves both that subset relation *and* key-set totality at import, so the assertion has a live
   object to read.

6. **The docstring closure is an INSERTION, not a rewrite.** Two new paragraphs were added at the end
   of the existing "CLOSED AT THE FIRST ARTIFACT" section; no line 20-01 committed was modified.
   `git diff --stat` reports 0 deletions across all three commits, which is the mechanical proof.

7. **`FIXTURE_CLEARING_POINT` is fully synthetic and says so.** It could have reused the taught
   adapter's published readings, but no v4.0 arm exists (D-13), and a fixture that *looks* measured
   is exactly the D-30 hazard in the opposite direction. Only the destroyed-model fixture carries
   published numbers, and only because a catastrophe that actually happened is not hypothetical.

## Deviations from Plan

**Rules 1, 3 and 4 did not fire. Rule 2 fired twice**, both times adding a loud refusal where the
code would otherwise have returned a quiet wrong answer:

### Auto-added missing critical functionality

**1. [Rule 2 - Validation] `promote_to_full_fidelity` refuses a verdict outside `V4_VERDICTS`**
- **Found during:** Task 2
- **Issue:** an unrecognised verdict string fell through the two promotion tests to `(False, …)`, publishing "not promoted" for input the rule could not read.
- **Fix:** `_prove(verdict in V4_VERDICTS, …)` after the ratchet call, message naming the quiet-wrong-answer failure.
- **Files modified:** `scripts/mitigation_gate.py`
- **Commit:** `546134d`

**2. [Rule 2 - Validation] `capacity_comparison`'s D-26 fallback refuses a mechanism with no `epsilon`**
- **Found during:** Task 2
- **Issue:** the fallback route reads `small_mechanism["epsilon"]`; a mapping without it would raise a bare `KeyError` with no explanation of why the key is required on that route only.
- **Fix:** a `_prove` naming which mapping(s) lack it and why epsilon is the compared quantity there.
- **Files modified:** `scripts/mitigation_gate.py`
- **Commit:** `546134d`

**Total deviations: 2, both Rule 2.**

## Path / naming discrepancies found

**One acceptance criterion was case-sensitively unsatisfiable and was satisfied honestly rather than
worked around.** Task 2's criterion requires `capacity_comparison.__doc__` to contain the phrase
`zero tolerance`. The docstring as first written carried `ZERO TOLERANCE CONSTANT` — the same claim
in the file's uppercase-heading register — so a case-sensitive `in` returned `False`. This is the
third substring-shaped criterion in this phase to behave differently from its intent (after 20-03's
`grep -c "shell=True"` and 20-04's `'V20_RETENTION_NOISE_FLOOR' in src`), but unlike those two it
was satisfiable **without weakening anything**: the D-25 paragraph now reads *"comparing at
identical mechanism parameters IS comparing at equivalent epsilon_fact: a zero tolerance constant,
because there is nothing left to approximate"* — which is where that phrase belonged anyway. No
claim was removed, softened or reworded to fit an instrument.

**Everything else resolved from the code, not from prose.** Verified this session before use:
`K_RUNGS == (48, 24, 16, 8)` at `scripts/mitigation_gate.py:240`;
`REPLICATION_PENDING_MARKER` read as a constant and never retyped;
`append_addendum(path, addendum, *, pending, recorded)` at `scripts/_addendum.py:55`;
`licensed_headline`'s "all-fail branch is FIRST-CLASS, not an error path" at
`scripts/phase16_ladder.py:305-306`; `floor_branch` at `scripts/phase19_erasure.py:944-961`;
`phase18_extraction.py`'s K record at `:84-93` with `K = 48` at `:93`;
`results/phase19_arm_erased.json`'s `retention_ppl` confirmed a **LIST** and `dialogue_ppl` a dict.
The handover's five stated facts all held: the sha256 matched, the import list is still five names
and grew by none, the marker string was read not retyped, `0.005214448168350039` is still a single
docstring substring, and `git log --diff-filter=A -- 'results/phase20_*'` is still empty.

## Issues Encountered

**Seven `E501` line-length violations across Tasks 1 and 2**, all in long refusal messages and
docstring prose, all fixed by rewrapping before the commit. Neither commit was made red: `ruff check
.`, `ruff format --check .` and `tests/test_phase20_prereg.py` were all green at every commit point,
and no test failed at any moment in this plan.

## Known Stubs

**None.** Every function is complete and every branch of every function this plan added has been
driven and observed — the six verdict outcomes plus the ratchet's two directions, the promotion
rule's promote and hold-back paths, all four capacity dispatch entries, both `not-comparable` routes,
the fallback's refusal and the four `ValueError` domain guards.

The pin's remaining obligations are **deliberately unset**, not stubbed:

- **The GATE-10 fallback tolerance (D-26)** has no committed value, and the gate *raises* rather than
  defaulting when the fallback route is taken without it. It is the third chosen constant and must be
  decided and named **before Phase 21's CAL-03 runs**. Flagged, not smuggled.
- **The extraction noise floor (D-13)** is Phase 23's; the tripwire carries the obligation as code.
- **The adapter-regime retention floor** is plan 20-07's `results/phase20_retention_floor.json`.
- **K's actual rung** is selected in Phase 23 by measured throughput; `K_RUNGS` is the closed menu and
  `ratchet_k` binds from that selection onward.

## Threat Flags

None. This plan adds no network surface, no auth path, no file I/O and no schema — every function is
a pure transform over values supplied by its caller, and the fixtures are inert module constants.

Threat-register dispositions discharged by this plan:

| Threat ID | Disposition | How this plan discharges it |
|---|---|---|
| T-20-25 | mitigate | `ratchet_k` proves both values are `K_RUNGS` members and `proposed_k >= fixed_k`, quoting `phase18_extraction.py:84-93`; `promote_to_full_fidelity` reaches it through the single implementation — observed raising when `full_k < curve_k` |
| T-20-26 | mitigate | K is a required kwarg on `promote_to_full_fidelity`; AST re-verified this session: `imported == {'erasure_gate', 'pathlib', 'sys'}`, `mitigation_budget` absent |
| T-20-27 | mitigate | All four cleared-flag combinations plus the fallback are committed here, before either run; the dispatch is TOTAL and proved so at module scope, so there is no fall-through to select into |
| T-20-28 | mitigate | `fallback_epsilon_tolerance` has no committed value; the fallback route with it unset raises `SystemExit` naming **D-26** and **CAL-03** — observed |
| T-20-29 | mitigate | `exists_clearing_point` proves single-arm membership across the whole point list **before computing anything**; the mixed-arm refusal was observed naming both arms |
| T-20-30 | mitigate | The fixture's comment carries `D-30`, `FIXTURE`, `0.22362988653603388` and `77.637`, states it is never a second reading of the experiment, and its four published fields are asserted EQUAL to the parsed artifact rather than transcribed — `control_gap` written as the subtraction |
| T-20-31 | mitigate | The three fixtures are module-scope constants; 20-06's twin imports these objects. The `FIXTURE_*` name set is exactly three, so a fourth is caught by 20-06's audit |
| T-20-32 | accept (this plan) / mitigate (downstream) | No `results/phase20_*` artifact exists, so this plan's edits are legal and green. The closure and the `_addendum.py` correction path are recorded in the module docstring (D-24); 20-07 opens with a blocking checkpoint |

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **20-06** writes the audits. Its stated expectations, all measured above: assigned module-scope
  floats outside `FIXTURE_*` are exactly `{0.5, 0.7}`; `CHOSEN_CONSTANTS` has 2 entries; the
  `FIXTURE_*` name set is exactly the three names; `imported == {'erasure_gate', 'pathlib', 'sys'}`;
  `from_erasure_gate` is exactly the five names; `provisional` count is 0; the four `MECHANISM_KEYS`
  strings are present with no fifth; `superseded_dialogue_cap(gap_noise_floor=0.005214448168350039)`
  still returns `4.5837288963367` exactly. **`0.005214448168350039` remains present as a docstring
  substring** (20-04's D-04 proof) and absent as a numeric constant — an `in src` check on it will
  return `True`, and that is correct.
- **20-06's `_module_scope_floats` must scope on `ast.Assign`**, as its plan states. Note that
  assignments inside `if __name__ == "__main__":` count as module scope under `_enclosing_functions`;
  this plan left the `__main__` block free of float literals so that either scoping choice yields
  `{0.5, 0.7}`.
- **20-07** commits the first `results/phase20_*` artifact. `git log --diff-filter=A --
  'results/phase20_*'` is **still empty**, so its artifact will be the first such add this repository
  has ever seen, and D-08's strictly-after ordering is intact. **From that commit onward the pin is
  irreversible.**
- **No requirement was marked complete.** GATE-07, GATE-08, GATE-09, GATE-10 and CAL-04 are all
  implemented here, but the CI guards that turn this session's one-shot observations into standing
  facts are 20-06's, and this project's recorded over-claim-avoidance pattern says a requirement is
  not marked complete in the first plan that touches it. Eleventh application.

**Standing constraint, now absolute:** `scripts/mitigation_gate.py` is COMPLETE. Do not amend,
rebase, squash or cherry-pick any commit touching it. Any further change to it is a dated
continuation via `scripts/_addendum.py`, recorded outside the file.

## Self-Check: PASSED

- `scripts/mitigation_gate.py` — FOUND
- `.planning/phases/20-pre-registration-the-three-condition-gate/20-05-SUMMARY.md` — FOUND
- commit `0bdcedf` — FOUND
- commit `546134d` — FOUND
- commit `abf9072` — FOUND
- `scripts/mitigation_gate.py` sha256 `86db479876ebeb2ba5b23c3b95da0ab20f13a3fbccf655b697280421b1997e14` — recorded at `abf9072`

---
*Phase: 20-pre-registration-the-three-condition-gate*
*Completed: 2026-08-20*
