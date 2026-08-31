---
phase: 25-frontier-sweep-and-the-existence-gate-verdict
plan: 21
subsystem: condition-c-producers
tags: [front-04, front-01, d-45, d-46, d-47, d-48, d-49, d-50, pre-registration]
requires:
  - scripts/mitigation_gate.py (frozen — dialogue_gap_band, retention_cap, mitigation_point_verdict)
  - scripts/phase20_gate_coverage.py (_prove_retention_floor, ADAPTER_REGIME, the three caps)
  - scripts/erasure_gate.py (V20_RETENTION_NOISE_FLOOR)
  - scripts/phase19_erasure.py (dialogue_ppl_pair, RETENTION_BIN — imported, never edited)
  - src/personacore/evaluation/perplexity.py (retention_perplexity — FROZEN, DEBT-02)
  - results/phase19_arm_erased.json, results/phase19_noise_floors.json, results/phase20_retention_floor.json
provides:
  - scripts/phase25_condition_c.py::CONDITION_C_FIELDS (plan 25-08 record schema, 25-19 artifact)
  - scripts/phase25_condition_c.py::measure_condition_c (the two producers)
  - scripts/phase25_condition_c.py::prove_condition_c_reproduction (D-45's bit-level check)
  - scripts/phase25_condition_c.py::retention_floor_for_verdict (the PROVED floor)
  - scripts/phase25_condition_c.py::RETENTION_LEG_BINDS_AT_ANCHOR (D-49, pre-registered)
  - scripts/phase25_condition_c.py::counterfactual_fields (D-50, zero compute)
  - scripts/phase25_condition_c.py::prove_control_gap_not_borrowed (D-47, structural)
affects:
  - tests/test_phase19_erasure.py (retention call-site census — fourth successor declared)
  - tests/test_phase21_sc5.py (`== 10` wall census — two non-wall sites declared)
tech-stack:
  added: []
  patterns:
    - "lazy torch: the module imports on CPU with no torch in sys.modules"
    - "constructed provenance: {regime: ADAPTER_REGIME, seeds: record[seeds]}"
    - "fcntl.flock serialisation of wave-1 MPS legs on the OS temp dir"
key-files:
  created:
    - scripts/phase25_condition_c.py
    - tests/test_phase25_condition_c.py
    - .planning/phases/25-frontier-sweep-and-the-existence-gate-verdict/deferred-items.md
  modified:
    - tests/test_phase19_erasure.py
    - tests/test_phase21_sc5.py
decisions:
  - "D-45's 87.4 s/point re-measured at 213.4-420.6 s; the conclusion survives a fortiori and both readings are published"
  - "The retention floor used is the governing adapter-regime 0.008681618994239138, proved through _prove_retention_floor before return"
  - "The plan's 'ZERO TOLERANCE sentence present at (0, 416)' is measurably false; the sentence belongs to n=104"
metrics:
  duration: ~2h20m
  completed: 2026-08-31
  tasks: 2
  tests_added: 20
---

# Phase 25 Plan 21: Condition (c)'s Six Producers Summary

Built the six condition-(c) inputs `mitigation_point_verdict` requires and that nothing in the
20-plan set produced, pre-registered that the retention leg already fails at the untouched anchor,
and reproduced Phase 19's committed record bit for bit — denominators included.

## What Landed

| Task | Commit | Files |
|------|--------|-------|
| 1 — the module | `498d425` | `scripts/phase25_condition_c.py` |
| 2 — the tests | `852b29d` | `tests/test_phase25_condition_c.py` |
| Deviation fix — two censuses | `e2d8bfc` | `tests/test_phase19_erasure.py`, `tests/test_phase21_sc5.py` |
| Cost correction | `a0ec2d5` | `scripts/phase25_condition_c.py` |

## Test Counts

**`1743 passed, 1 skipped`** against the **1723 / 1** baseline — delta **+20 passed, +0 skipped**,
exactly the 20 tests this plan adds. `make lint` exits 0.

- `pytest tests/test_phase25_condition_c.py -v` → `20 passed in 371.73s`
- `pytest tests/test_phase25_condition_c.py -k "not reproduces_phase19" -q` → `19 passed, 1 deselected`,
  **zero skipped** — the arithmetic half never depends on a device
- `PERSONACORE_SWEEP_ACTIVE=1 pytest tests/test_phase25_condition_c.py -rs -q` → `19 passed, 1 skipped`

**Node id for 25-06's wave-2 literal, verbatim:**

```
tests/test_phase25_condition_c.py::test_the_measurement_path_reproduces_phase19_exactly
```

It appears as SKIPPED under the flag and is gated on `PERSONACORE_SWEEP_ACTIVE` read from the
environment at module scope. An AST walk proves no `sweep_is_active` symbol is imported, named or
attribute-accessed anywhere in the file, so the leg collects green in wave 1 before 25-06 exists.

## The Bit-Level Reproduction (D-45)

`prove_condition_c_reproduction()` ran on `checkpoints/persona_adapter.pt` on MPS. All four figures
and both denominators matched `results/phase19_arm_erased.json["pre_erasure"]` under exact `==`:

| Field | Measured | Committed | JSON path |
|-------|----------|-----------|-----------|
| `adapter_on` | `5.815445876712191` | `5.815445876712191` | `["pre_erasure"]["dialogue_ppl"]["adapter_on"]` |
| `adapter_off` | `4.573349214207799` | `4.573349214207799` | `["pre_erasure"]["dialogue_ppl"]["adapter_off"]` |
| `n_targets` | `270203` | `270203` | `["pre_erasure"]["dialogue_ppl"]["n_targets"]` |
| `retention_ppl` | `4.219759892336485` | `4.219759892336485` | `["pre_erasure"]["retention_ppl"][0]` |
| `retention_total_tokens` | `1000285` | `1000285` | `["pre_erasure"]["retention_ppl"][1]` |

**MPS lock: NOT contended.** The leg took the exclusive `fcntl.flock(LOCK_EX)` on
`tempfile.gettempdir()/personacore-phase25-mps.lock` non-blockingly and got it first try, so plan
25-22's wave-1 leg was not running concurrently. Printed verbatim by the test:

```
[25-21] reproduction OK in 420.6 s (discussion-time reference 87.4 s); MPS lock contended: False
```

## MEASURED CORRECTION — D-45's cost is 2.4x-4.8x optimistic, and the conclusion survives

The plan required the docstring to record 43.5 s + 43.9 s = 87.4 s per point. **Re-measured on the
same M3, same adapter, same frozen bins, the figure does not reproduce.** Both readings are now
published in the module; the discussion-time one is not edited away.

| Leg | D-45 reference | Re-measured (isolated) | Ratio |
|-----|---------------|------------------------|-------|
| `preflight_device` | — | 0.0 s | — |
| `load_adapted_model` | — | **0.3 s** | — |
| `dialogue_ppl_pair` | 43.5 s | **80.4 s** | 1.85x |
| `retention_perplexity` | 43.9 s | **133.0 s** | 3.03x |
| **the two calls** | **87.4 s** | **213.4 s** | **2.44x** |
| end to end, in-suite | — | **420.6 s** | 4.81x |

**Model loading is NOT the explanation** — it is 0.3-1.0 s of the total. The gap is in the forward
passes. Over 44 points the cost is **2.61 h (isolated) to 5.14 h (in-suite)** rather than 1.07 h —
**1.7-4.8% of the 107-150 h budget** rather than the claimed 0.7-1.0%.

**D-45's conclusion survives a fortiori.** At the worst measured rate condition (c) still costs
under 5% of the sweep, so cost still cannot argue for a subset, and a subset chosen after seeing
which points clear (a) and (b) is still the reduction-after-the-fact this milestone forbids. Only
the figure moves, and it moves in the direction that makes the argument harder rather than easier —
which is why it is corrected rather than quietly inherited.

## D-49's Two Readings, Side by Side — Both COMPUTED, Neither Typed

| | floor | cap | headroom | admit factor |
|-|-------|-----|----------|--------------|
| **borrowed** | `0.06893` | `4.029` | `-0.1907598923364855` | `2.383721836185154` |
| **governing** | `0.008681618994239138` | `3.9085032379884783` | `-0.3112566543480071` | `18.926187186661135` |

Every one of these six figures is computed at import from `mitigation_gate.retention_cap` and the
committed taught reading `4.219759892336485`. An AST walk over the module proves no float constant
equals `4.029`, `3.9085032379884783`, `0.06893`, `3.89114` or `0.5`.

The computed borrowed headroom equals `results/phase19_noise_floors.json`'s
`retention_ppl_pre_erasure.adapter_on_headroom` under exact `==`, and that record's
`adapter_on_above_cap` is `true` — Phase 19 recorded this itself and no plan in the 20-plan set
surfaced it. Both headrooms are asserted strictly negative at import, and the governing one strictly
more negative, so the a-fortiori claim is a runtime property rather than a paragraph.

## The Borrowed Floor's Refusal, Watched Firing — Verbatim

`phase20_gate_coverage._prove_retention_floor(retention_noise_floor=erasure_gate.V20_RETENTION_NOISE_FLOOR, ...)`
raises `SystemExit`:

```
[phase20_gate_coverage] the retention noise floor IS 0.06893, the Phase 12 full-fine-tune seed
pair, whatever regime the provenance claims. Refused by identity against the value imported from
`erasure_gate` rather than against a retyped literal, so the check cannot drift away from the
constant it refuses. It is 7.939763314393305x the measured adapter-regime floor
0.008681618994239138 and yields the LOOSER cap 4.029 against the governing 3.9085032379884783 —
T-20-19 reproduced: `retention_cap` accepts it today with no refusal at all, and the looser cap is
the one a borrowing buys
```

**In one sentence: D-48's named import is refused by a committed guard, and the accepted floor
yields the TIGHTER cap — so the disclosure costs nothing and buys no easier pass.** The same call
with the measured adapter-regime floor and the CONSTRUCTED provenance returned `None`.

The provenance is constructed as `{"regime": phase20_gate_coverage.ADAPTER_REGIME, "seeds":
record["seeds"]}` with `ADAPTER_REGIME` resolved by import, because the committed record carries
`seeds` (`[1337, 2024]`) and **no `regime` key** — handing it over raw is refused on the first of
the five refusals, and `test_the_provenance_must_be_constructed_because_the_record_lacks_regime`
watches that happen.

## D-48's Sensitivity, Recomputed Live

At the DERIVED Phase-19 anchor gap `1.2420966625043919` (never typed — computed as
`adapter_on - adapter_off` from the record's `pre_erasure` block):

- band `(0.6210483312521959, 1.252525558841092)`, width `0.631477227588896`
- `MARGIN_K x floor = 0.010428896336700078` → floor share `0.016515079057592703` (**1.65%**)
- 10x-floor ceiling move `0.0938600670303007` → `0.14863571151833432` of the band (**14.86%**)

The 10x term is `hi(10 x floor) - hi(floor)` = `9 x MARGIN_K x floor`, **not** ten times the floor
share; the wrong form yields `0.16515079057592702`, and the test asserts the two differ. The anchor
gap's own docstring states what it is NOT — D-47's `control_gap` is per capacity, no v4.0 control
exists until plan 25-15 in wave 8, and the anchor gap is never passed to `mitigation_point_verdict`.

## Deviations from Plan

### [Rule 3 — Blocking] Two repo-wide censuses caught the new module

Both guards fired for the right reason and both were resolved by their own documented mechanism —
scoped by name with a stated reason, never by lowering a count. Commit `e2d8bfc`.

1. **`tests/test_phase19_erasure.py::test_retention_measurement_pins_a_new_call_site_with_no_adapted_precedent`**
   counts `retention_perplexity` call sites across `scripts/` and `src/`. It went `7 calls in 5
   modules` against an expected `6 in 4`. The guard's own comments record the correct treatment,
   applied three times before (19-10, 20-07): a SUCCESSOR — a module that postdates the pin AND
   reaches the injection path — is excluded BY NAME under a positive obligation. `phase25_condition_c.py`
   is exactly that (it calls `load_adapted_model`), so it was declared the **fourth successor** and
   the census numbers are **UNCHANGED at 6 calls in 4 modules**.

2. **`tests/test_phase21_sc5.py::test_wall_census_is_the_measured_set`** counts `== 10` assertions
   under `tests/`. Both new sites are false positives of its deliberately broad third pattern:
   `assert recipe["n_facts"] == 10` (a v3.0 recipe provenance field read from a committed record)
   and `assert sensitivity["ten_x_error_share_of_band"] != 10` (the 10x floor-error multiplier).
   Neither reads the fact set, so both went to `_NOT_WALL_SITES` with reasons. **The `n_facts`
   coincidence is stated rather than glossed** in the declaration: that v3.0 arm did teach ten
   facts, so the number matches the wall — what makes it an exclusion is that shrinking the leak
   vocabulary tomorrow would leave the assertion unmoved, which is exactly the property a wall site
   must not have.

### [Measurement corrections] Four plan prose figures re-measured

1. **D-45's 87.4 s/point is 2.4x-4.8x optimistic** — full detail above. Corrected in the module with
   both readings published; D-45's conclusion survives.

2. **`results/phase20_retention_floor.json` has 25 top-level keys, not 24.** The plan asserts 24 in
   three places. No acceptance criterion depends on the count (they assert `"regime" not in` and
   `"seeds" in`), so no code changed — but the figure is wrong and is recorded here rather than
   carried forward.

3. **The 21-kwarg verdict call does NOT carry the ZERO TOLERANCE sentence at `(0, 416)`.** The plan
   states it does. Measured: at `n = 416` the extraction ceiling tolerates **5** questions, so the
   sentence is absent; `tolerance_report(ceiling=0.026462, n_questions=416)` returns `tolerated = 5`
   while `n_questions=104` returns `0`. The plan appears to have conflated the fixture's 104
   denominator with the never-taught 416. The test asserts what the gate actually returns — a
   3-tuple, `PASS`, 4 reasons, arm `dp` — and records the correction in its own docstring.

4. **The plan's `<environment>` block states a `1647 passed, 1 skipped` baseline.** The actual
   pre-plan baseline is `1723 / 1` (supplied by the wave context). Delta reported against 1723.

### [Plan wording adjusted, intent preserved]

- **`phase18_extraction` is not imported.** The plan lists it among the module's imports, but
  nothing in the action needs it (exposure measurement is plan 25-22's leg) and importing it would
  put torch in `sys.modules`, failing the plan's own no-torch acceptance criterion.
- **`phase19_erasure`, `teach_persona` and `personacore.config` are imported lazily**, not at module
  scope as the import list reads. Measured: all three put torch in `sys.modules`. The plan's own
  criterion — "imports with no torch in `sys.modules`" — forces the lazy form, which is also the
  pattern `dialogue_ppl_pair` itself already uses for `teach_persona`.
- **The anchor gap's "what it is NOT" disclosure lives in `anchor_dialogue_gap()`'s docstring**, and
  is carried into `DIALOGUE_FLOOR_SENSITIVITY["control_gap_disclosure"]`. The plan says "the field's
  own docstring"; a dict entry cannot have one, so the value is produced by a function that can.

### The shadowing trap fired live, in this plan's own test

The plan warns that `evaluation.perplexity.retention_perplexity` raises `AttributeError` because the
package `__init__` re-exports a function that shadows the submodule. The module was written correctly
— but the first draft of `test_the_off_leg_is_reused_only_after_being_verified` used
`from personacore.evaluation import perplexity as perplexity_module` to monkeypatch, and got exactly
`AttributeError: <function perplexity at 0x...> has no attribute 'retention_perplexity'`. The test
now resolves the real submodule through `importlib.import_module` and asserts the two are distinct
objects, so the trap is demonstrated rather than described.

## Deferred Issues

`tests/test_phase23_resume.py::test_production_resume_epsilon_bit_identical` is **FLAKY under
full-suite load** — one red reading in four, green in isolation, and green in two full-suite runs
with all of this plan's code present. It touches nothing this plan changed. Logged to
`deferred-items.md` with all four readings; **not fixed**, per the scope boundary. The same machine
variance that corroborates it also shows in the suite wall-clock: `1626.92 s` in one run and
`606.00 s` in another, on an identical tree.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema change at a trust boundary.
The module reads three committed JSON records and one checkpoint, all already in the repo.

## Frozen-Module Integrity

`git diff --exit-code` exits 0 for `scripts/mitigation_gate.py`, `scripts/mitigation_accountant.py`,
`scripts/mitigation_unit.py`, `scripts/phase18_extraction.py`, `scripts/phase19_erasure.py`,
`src/personacore/evaluation/perplexity.py` and `pyproject.toml`. Zero installs; no runtime
dependency added (RPT-03 intact).
