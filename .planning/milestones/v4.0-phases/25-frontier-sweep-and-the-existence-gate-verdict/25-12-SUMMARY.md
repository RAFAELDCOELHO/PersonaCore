---
phase: 25
plan: 12
subsystem: privacy-frontier
tags: [dp, sigma-ladder, epsilon-ladder, clip-calibration, pre-registration, D-17, D-18, D-20, D-24, D-25, WR-05]
requires:
  - results/phase25_clip_calibration.json
  - results/phase23_sigma_zero.json
  - results/phase23_noised_dp_n64_sigma0p500000.json
  - results/phase23_never_taught.json
  - scripts/phase25_calibrate.py
provides:
  - mitigation_budget.SIGMA_LADDER
  - mitigation_budget.EPSILON_LADDER
  - mitigation_budget.CLIP_NORM
  - mitigation_budget.CONTROL_CLIP_NORM
  - results/phase25_sigma_hi_probe.json
  - scripts/phase25_sigma_hi.py
affects:
  - scripts/phase25_record.py (ORDERED_POINT_KEYS now resolves — 44 keys)
  - results/phase24_token_budget.json (re-emitted; substantive figures byte-identical)
  - tests/test_phase23_budget.py (register)
  - tests/test_phase23_resume.py (train_arm call-site census)
tech-stack:
  added: []
  patterns:
    - "literal-pinned-plus-live-derivation (tests/test_phase24_grid.py's shape)"
    - "attribute-access-only reads of a registered constant"
    - "read every committed record BEFORE the GPU work"
key-files:
  created:
    - scripts/phase25_sigma_hi.py
    - results/phase25_sigma_hi_probe.json
    - tests/test_phase25_grid.py
  modified:
    - scripts/mitigation_budget.py
    - tests/test_phase23_budget.py
    - tests/test_phase23_resume.py
    - results/phase24_token_budget.json
decisions:
  - "sigma_hi = 80.0, probed at dp_n64 and CONFIRMED: taught recall ON 0/1008 against the same run's adapter-OFF 0/1008 (control: 790/1008)"
  - "one candidate, not two — the confirmation is a collapse test, not a bracketing search; the ratchet handles a miss"
  - "the sigma ladder is geometric from the committed sigma 0.5 to the probed 80.0, in round sigma with full-precision epsilon transcribed"
  - "the D-18 probe lives in a NEW module because scripts/phase25_calibrate.py's sha256 is pinned inside two committed records"
metrics:
  duration: "~2 h 45 min wall clock (of which ~90 min GPU: two probe runs at ~45 min each)"
  completed: 2026-09-01
  tasks: 3
  commits: 3
---

# Phase 25 Plan 12: The Noise Axis — Probe, Then Pin, Summary

The σ_hi anchor was probed recall-only at `dp_n64` and **confirmed by total collapse** (taught
recall ON 0/1008 against the same run's adapter-OFF 0/1008, where the σ=0 control reads 790/1008);
only then were the 16-rung σ ladder, its full-precision ε ladder and both clip constants pinned as
literals, with the budget register's natural RED watched and quoted before it was closed.

## What Was Measured

### The σ_hi anchor probe (D-18) — `results/phase25_sigma_hi_probe.json`

| Quantity | Reading |
| --- | --- |
| capacity | `dp_n64` |
| σ | `80.0` |
| C | `1.3254119157791138` (25-11's calibrated candidate, read live) |
| ε at T=200, δ=1e-5 | `0.6339783761989397` |
| **taught recall, adapter ON** | **0 / 1008** (112 questions × 9 draws) |
| taught recall, adapter OFF | 0 / 1008 |
| held-out recall ON / OFF | 0 / 648 · 0 / 648 |
| `clip_bind_count` | 12800 (binding), `records_per_lot` 64 |
| `composed_steps` / `composed_lot_sizes` | 200 / `[64]` |
| training / scoring wall clock | 1310.997 s / 1365.880 s |
| verdict | **anchor CONFIRMED** |

The confirmation rule was fixed **before** the reading: the anchor is confirmed when adapter-ON
taught recall is not above the adapter-OFF count from the *same* scoring call. The committed σ=0
control (`results/phase23_sigma_zero.json`) reads ON 790/1008 against OFF 0/1008, so the distance
the noise had to close was the whole 790 — and it closed all of it.

**Capacity choice, with its reason recorded before the run:** under DPSGD the signal is the sum of
L clipped per-record gradients while the injected noise is drawn once per step at std `σ·C`
regardless of L, so SNR scales as L/σ and `dp_n64` resists noise ~8× better than `dp_n8`. A
collapse at `dp_n64` therefore implies one at `dp_n8`; the converse does not hold. `dp_n64` is also
the `clip_norm_rule_capacity` the shipping C was derived from.

### GPU spend, actual vs budget

| | Plan budget | Actual |
| --- | --- | --- |
| σ_hi probe | ≈ 20–40 min | **≈ 90 min across two runs** (45 min each) |

The plan's ≈20 min figure came from `dp_n8`'s training cost. One `dp_n64` candidate is ~22 min of
training plus ~23 min of recall scoring ≈ **45 min**, so even a single successful run exceeds the
stated ceiling. The run was then paid for **twice** — see Deviation 2. This matches the phase's
pattern of optimistic plan-time budgets (25-11 came in at ~92 min against ~40 min).

### The four pins — `scripts/mitigation_budget.py`

```
SIGMA_LADDER   = (0.0, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 4.0,
                  6.0, 8.0, 12.0, 16.0, 24.0, 32.0, 50.0, 80.0)
EPSILON_LADDER = (None, 519.6981942303134, 289.33863705009264, 159.44148628736576,
                  83.8305906128762, 54.37663901498563, 30.50627999271221,
                  20.675508046994032, 12.262332118205716, 8.595865790470416,
                  5.299979064701441, 3.7965357228934966, 2.3957449097512216,
                  1.7369988136430536, 1.060789755417757, 0.6339783761989397)
CLIP_NORM         = 1.3254119157791138
CONTROL_CLIP_NORM = 1000000.0
```

All 15 noised rungs satisfy `epsilon_for(σ, STEP_BUDGET, DELTA) == EPSILON_LADDER[i]` under exact
`==`. `EPSILON_LADDER[1] = 519.6981942303134` is bit-identical to the ε already committed in
`results/phase23_noised_dp_n64_sigma0p500000.json`.

**Anchor selection rule, recorded before the number:** the smallest *round* σ whose ε falls below
1 — the one landmark on this axis that is not this project's own preference. σ=50.0 reads
`1.060789755417757` (above 1); σ=80.0 reads `0.6339783761989397` (below 1).

### Measured live: `capacity_comparison` ignores the clip divergence

The plan's phrasing ("a 999× divergence passed silently") was not reproduced verbatim — the
magnitude is whatever you feed it. Measured with **this pin's own pair** on the frozen gate:

```
capacity_comparison(..., small_mechanism={...,'clip_norm': 1.3254119157791138},
                         large_mechanism={...,'clip_norm': 1000000.0})
  -> branch 'recovery-at-both-capacities'
  ratio 754482.4277607104 ; reason strings mentioning 'clip': []
```

A **754,482×** clip divergence passes with all four `MECHANISM_KEYS` equal and no reason string
naming it. That silence is recorded in `CLIP_NORM_PROVENANCE.extra_keys_are_ignored_measured` and
is why D-25 closes the gap caller-side.

## The Natural RED, Verbatim

Captured after the four constants landed and **before** anything was registered:

```
tests/test_phase23_budget.py::test_z_was_sized_against_the_ceiling
E  AssertionError: the AST walk over scripts/mitigation_budget.py finds Z constants
   ['SWEEP_POINTS', 'CURVE_K', 'FULL_FIDELITY_K', 'STEP_BUDGET', 'N_CONTROL_SEEDS',
    'N64_LEG_WITHDRAWN', 'SIGMA_LADDER', 'EPSILON_LADDER', 'CLIP_NORM', 'CONTROL_CLIP_NORM']
   but this file's register is ['SWEEP_POINTS', 'CURVE_K', 'FULL_FIDELITY_K', 'STEP_BUDGET',
   'N_CONTROL_SEEDS', 'N64_LEG_WITHDRAWN']. An unregistered constant is skipped by every loop
   here, so it would ship with no re-derivation and no provenance check
E  assert ('SWEEP_POINT...THDRAWN', ...) == ('SWEEP_POINT...EG_WITHDRAWN')
E    Left contains 4 more items, first extra item: 'SIGMA_LADDER'
tests/test_phase23_budget.py:1361: AssertionError
1 failed in 0.04s
```

All four names appear. Closed by four `_POST_23_13_CONSTANTS` entries mapped to
`test_phase25_grid.py`, each carrying the reason they are **not** Z constants: no throughput figure
feeds them, so a `sized_against` field would be FALSE on all four.

## The Invisible-`from`-Import Trap, Demonstrated

The register's own walk, re-run against a `tmp_path` copy of `tests/test_phase25_grid.py` with one
attribute access rewritten to a `from`-import bare name:

```
REGISTER FAILURE ON THE tmp_path COPY:
tests/test_phase25_grid.py never reads SIGMA_LADDER, so excusing it here ships a constant in
scripts/mitigation_budget.py with no re-derivation and no provenance check anywhere
real file byte-unchanged: True
```

`git status --porcelain tests/` was **empty** afterwards. The demonstration also lives permanently
in the suite as `test_the_from_import_variant_is_invisible_to_the_register_walk`.

## Deviations from Plan

### 1. [Rule 3 — Blocking] The probe could not live in `scripts/phase25_calibrate.py`

- **Found during:** Task 1, before any GPU spend.
- **Issue:** the plan names `scripts/phase25_calibrate.py` as the host for the σ_hi probe.
  `tests/test_phase25_calibrate.py::test_the_calibration_provenance_matches_the_live_module_bytes`
  recomputes that module's sha256 from bytes and asserts it equals the `module_sha256` recorded
  inside **both** `results/phase25_clip_calibration.json` and
  `results/phase25_adversarial_throughput.json`. Appending one byte reddens it. Verified green
  before the change and confirmed as the binding constraint.
- **Fix:** the probe lands in a new sibling module `scripts/phase25_sigma_hi.py`, which **imports**
  `CALIBRATION_PREFIX`, `provenance_block`, `_release_calibration_targets` and `sha256_of` from
  `phase25_calibrate` rather than restating them — so the exclusion proof, the provenance shape and
  the artifact hygiene are literally that module's own. The only honest alternative was re-running
  both calibrations (~21 min + ~2 h of GPU) to refresh their digests; editing the recorded digests
  would have forged a provenance. Every Task 1 acceptance criterion is about the *record*, and all
  of them pass. The reason is written into the new module's docstring.
- **Commit:** `1233370`

### 2. [Rule 1 — Bug] The first probe run was lost to a `KeyError` after 45 minutes of GPU

- **Found during:** Task 1, at the end of the first run.
- **Issue:** `_control_reading()` read `blob["arm"]` from `results/phase23_sigma_zero.json`, which
  carries no top-level `arm` key (it lives under `training`). The read ran while *assembling the
  blob*, i.e. after training, scoring and adapter release — so `KeyError: 'arm'` destroyed a
  completed 45-minute measurement. Readings printed before the crash: taught ON 0/1008 vs OFF
  0/1008, training 1319.2 s, scoring 1367.9 s.
- **Root-cause fix (not the symptom):** the key path is corrected *and* every committed-record read
  is hoisted to the front of `run_sigma_hi_probe`, before the GPU work, so a malformed input costs
  one second rather than 45 minutes. The reason is recorded in the function's docstring.
- **Second bug caught by the guard this created:** a stubbed dry run of the whole assembly path
  (`probe_candidate` monkeypatched, every plan acceptance criterion asserted) then failed on
  `RATCHET_EXTENSION_RULE` — the criteria check the lowercase substrings `extends upward` /
  `never shifts` and the rule was written in caps. Fixed **before** the re-run, so it cost seconds
  instead of another 45 minutes.
- **Re-run reproduced bit-for-bit:** `final_train_loss=2.4506` identical across both runs; readings
  identical.
- **Commit:** `1233370`

### 3. [Rule 3 — Blocking] `results/phase24_token_budget.json` pins the budget module's sha256

- **Found during:** Task 3's full-suite run.
- **Issue:** that record's provenance pins `scripts/mitigation_budget.py`'s sha256, so the append
  this plan *mandates* reddened `test_phase24_record.py::test_the_provenance_pins_match_the_live_module_bytes`.
- **Fix:** re-emitted through the census's own sanctioned route, which the failure message names:
  delete the record at a clean tree and run `python scripts/phase24_record.py` (CPU-only; bins are
  built in a scratch dir). Then, as that message demands, **every substantive figure was confirmed
  byte-identical** by a full recursive diff — the only leaf differences are the two WR-05 keys the
  record mirrors out of the provenance dict, plus `git_sha`, `module_sha256` and `written_utc`.
- **Commit:** `54485bb`

### 4. [Rule 3 — Blocking] The `train_arm` call-site census pins 27 sites

- **Found during:** Task 3's full-suite run.
- **Issue:** `tests/test_phase23_resume.py::test_resume_from_none_is_inert` greps every
  `train_arm(` hit in `scripts/` and `tests/` and asserts the count equals its register. The new
  module made it 28 vs 27.
- **Fix:** resolved through the census's **own ledger** — a `_TRAIN_ARM_CALL_SITES` entry with its
  reason plus the spelled count bumped `8+1+1+1+1+2` → `8+1+1+1+1+2+1`. The check was not widened.
  No `_RESUME_PASSERS` entry was added: the probe passes no `resume_from`, so one appearing there
  still reddens.
- **Commit:** `54485bb`

### 5. [Rule 3 — Blocking] Tasks 2 and 3 share one commit

- **Issue:** Task 2 registers four names against `tests/test_phase25_grid.py`, and the register
  asserts `covering_path.exists()`. A Task-2-only commit would be **red on a fresh clone**, because
  the covering file would not exist at that commit. The plan's own Task 2 criteria already require
  `test_z_was_sized_against_the_ceiling` to exit 0, which presupposes the file.
- **Fix:** the pins, the register entries and the covering test landed in one green commit
  (`049a6bb`). No intermediate commit in this plan is red.

## Corrections to Prior Figures

| Claim | Prior statement | Measured here |
| --- | --- | --- |
| clip divergence tolerated by `capacity_comparison` | "a 999× divergence passed silently" | **754,482.4277607104×** with this pin's own pair; branch `recovery-at-both-capacities`, zero reason strings mentioning clip. The magnitude is an input, not a property — the finding is that *any* non-`MECHANISM_KEYS` divergence is ignored. |
| σ_hi probe cost | "≈ 20–40 min" | **≈ 45 min per `dp_n64` candidate** (1311 s train + 1366 s score) |
| `test_production_resume_epsilon_bit_identical` flakiness | deferred-items D1 records it PASSING in isolation | It failed in isolation here too — but **not flakily**: the cause was a "no residue in `results/`" assertion firing on the uncommitted re-emitted `phase24_token_budget.json`. It passes once committed. D1's flake was not reproduced and was not the failure seen. |

WR-05 was verified rather than accepted: `results/phase24_token_budget.json`'s upper-extreme rows
record `adversarial_multiplicity` **1.0 at `adv_n8`** and **8.0 at `adv_n64`** (clean episodes 176
and 1408) — the identical values the pin carries under `dp_n8`/`dp_n64`. The disagreement is in the
arm names only, exactly as WR-05 states.

## Verification

| Check | Result |
| --- | --- |
| `.venv/bin/pytest tests/ -q` | **1938 passed, 1 skipped** in 1200.47 s — **0 failed** |
| delta vs the 1907/1 baseline | **+31 passed** (exactly `tests/test_phase25_grid.py`), skipped unchanged |
| `tests/test_phase25_grid.py -v` | 31 passed, **0 skipped** |
| `-k "each_noised_rung"` | **15 passed**, 16 deselected |
| `test_z_was_sized_against_the_ceiling` | passed |
| `git diff -- scripts/mitigation_budget.py \| grep -c '^-[^-]'` | **0** (append-only) |
| `git ls-files 'results/phase25_point_*.json' \| wc -l` | **0** |
| four ancestry-guarded modules + `pyproject.toml` | byte-unchanged |
| `make lint` | All checks passed; 256 files already formatted |
| `.planning/STATE.md`, `.planning/ROADMAP.md` | untouched (`git status --porcelain .planning/` → 0 lines) |

## Commits

| Hash | Message |
| --- | --- |
| `1233370` | `feat(25-12): probe the sigma_hi anchor recall-only and commit the ratchet rule` |
| `049a6bb` | `feat(25-12): pin the sigma ladder, the epsilon ladder and both clip constants` |
| `54485bb` | `fix(25-12): resolve the two repo-wide censuses the noise-axis pins tripped` |

`git merge-base --is-ancestor 1233370 049a6bb` holds, and
`test_the_ratchet_rule_is_committed_before_the_ladder` asserts that ordering from `git log` on every
suite run — D-18's "probe first" is enforced, not claimed.

## Known Stubs

None. All four pins carry a `_PROVENANCE` sibling with a live-checked record digest, and every one
re-derives from a committed measurement in `tests/test_phase25_grid.py`.

## Threat Flags

None. This plan added no network endpoint, no auth path, no file-access pattern and no schema at a
trust boundary. `scripts/phase25_sigma_hi.py` trains and scores through the existing production
entry points and writes one record under the existing calibration prefix.

## Notes for the Next Plan

- `phase25_record.ORDERED_POINT_KEYS()` now resolves: **44 unique keys**, `dp_n8_sigma0p000000` …
  `dp_n64_sigma80p000000` plus the twelve adversarial keys. The wave-2..4 "raises until 25-12"
  branches in `test_phase25_record.py` and `test_phase25_driver.py` now take their ladder-present
  paths.
- The **44-point sweep has not started** and must not until 25-14's human checkpoint.
- `RATCHET_EXTENSION_RULE` is committed in `results/phase25_sigma_hi_probe.json`: if the high
  extreme's *full extraction* read still misses the never-taught floor (pooled 0/416), the ladder
  extends upward by halving ε — it never shifts and never shrinks.
- The anchor was confirmed on a **recall** reading with **one seed**; whether σ=80.0 reaches the
  never-taught **extraction** floor is deliberately not claimed here. Both limitations are recorded
  in the probe record's own `limitations` block.

## Self-Check: PASSED

- `scripts/phase25_sigma_hi.py` — FOUND
- `results/phase25_sigma_hi_probe.json` — FOUND
- `tests/test_phase25_grid.py` — FOUND
- commit `1233370` — FOUND
- commit `049a6bb` — FOUND
- commit `54485bb` — FOUND
