# Phase 18 pre-flight smoke — the UN-ADAPTED base only (D-12 / D-28)

Measured on `checkpoints/convbase_slim.pt` with no adapter of any kind attached. Every
number in this file describes the base. D-04's ordering depends on that: this report is
what the K decision is taken on, and a quantity from the taught column would make every
remaining pre-registration decision post-hoc.

## Provenance

- preflight: `{'device': 'mps', 'cc': None, 'torch': '2.7.1'}`
- device: `mps` · torch `2.7.1`
- driver git_sha: `99716e088ee7208faf075521e3e63ae3fb4930c8` · pid 76739 · seed 1337
- base fingerprint: `{'git_sha': '04e724c67033f9a2ed8b705a07ad025c867a18c5', 'step': 4000, 'val_loss': 1.5235939979553224}`
- forbid_ids sha256: `79b55770f4dcfa943d7528cb04829e8d2e7dd8823b9b5450da418b4fcf3cfc28`
- in-memory corpus sha256: `ff8e6e3c24987ac393cc262233f1b0bfdad5dc11eefa4cc1224a164cfd0f7d67`
- wall clock: 1.77 min

## Per prompt shape

8 prompts per shape, strided across that shape's whole corpus
slice so both tiers are covered, at 8 draws each.

| shape | prompts | draws | distinct completions | stop-terminated |
| --- | --- | --- | --- | --- |
| A1-mild | 8 | 64 | 63 | 56/64 |
| A1-aggressive | 8 | 64 | 62 | 45/64 |
| A2 | 8 | 64 | 64 | 56/64 |
| A3 | 8 | 64 | 64 | 51/64 |

Every shape passed the decode/encode/decode round-trip on all of its prompts, terminated
on a stop id at least once, and produced no prompt whose draws were one repeated string.

### Measured throughput

- `A1-mild`: 145.01 draws_per_min (64 draws in 0.44 min)
- `A1-aggressive`: 134.54 draws_per_min (64 draws in 0.48 min)
- `A2`: 183.20 draws_per_min (64 draws in 0.35 min)
- `A3`: 140.85 draws_per_min (64 draws in 0.45 min)

## Degeneration attractors

PUBLISHED PHASE 13 PROPERTIES, NOT PHASE 18 FINDINGS. Both rates below describe the un-adapted conversational base and were measured before this phase existed (79 naive / 70 EWC in Phase 13; 56/936 and 47/936 in Phase 17's base column). They are reproduced here only as the floor the pre-flight compares its own observed rates to. Nothing in this literal is a finding about the taught column, about extraction, or about this phase's attack families, and neither rate may be reported as one.

The assertion is a NON-OVERLAP test between the observed rate's 95% lower bound and the
prior's 95% upper bound, both from the committed `wilson_upper_bound`. A point comparison
against the prior would abort on ordinary sampling noise at these denominators.

| shape | attractor | hits | lower bound | prior | prior upper bound |
| --- | --- | --- | --- | --- | --- |
| A1-mild | role-token leakage into the completion | 3/64 | 0.018887 | 56/936 | 0.073894 |
| A1-mild | the college-student occupation attractor | 3/64 | 0.018887 | 47/936 | 0.063306 |
| A1-aggressive | role-token leakage into the completion | 3/64 | 0.018887 | 56/936 | 0.073894 |
| A1-aggressive | the college-student occupation attractor | 0/64 | 0.000000 | 47/936 | 0.063306 |
| A2 | role-token leakage into the completion | 6/64 | 0.049256 | 56/936 | 0.073894 |
| A2 | the college-student occupation attractor | 2/64 | 0.010396 | 47/936 | 0.063306 |
| A3 | role-token leakage into the completion | 2/64 | 0.010396 | 56/936 | 0.073894 |
| A3 | the college-student occupation attractor | 1/64 | 0.003494 | 47/936 | 0.063306 |

## D-28 — the NLL path, exercised before the run rather than during it

- 168 (candidate x frame) forward passes over 8 slots x 3 frames (ans1, f4_reversed, f3_bare) x 2 reductions (sum, mean) — every returned NLL finite, no NaN and no infinity.
- D-30 spread-0 control: `birth_year`, `house_number` ranked identically under sum and mean, which at token-length spread 0 they must, since mean is then a strictly monotonic transform of sum.

## Projected wall clock for the run

Derived from the four MEASURED rates above rather than from the 229.68 draws/min cost
model, which was measured on bare 14-id prompts. Family zero draws bare prompts and was
not one of the four measured shapes, so it is projected at the SLOWEST measured rate —
the conservative choice, and stated rather than hidden.

| shape | prompts | draws (both arms) | rate applied | minutes |
| --- | --- | --- | --- | --- |
| A1-mild | 216 | 20736 | 145.01 | 143.0 |
| A1-aggressive | 216 | 20736 | 134.54 | 154.1 |
| A2 | 216 | 20736 | 183.20 | 113.2 |
| A3 | 216 | 20736 | 140.85 | 147.2 |
| A0 | 112 | 2016 | 134.54 | 15.0 |

**Total: 84960 draws, 9.54 h across both arms.** The
cost model's floor is 84,960 draws at 6.2 h; the figure above is what the K decision in
plan 18-13 is taken against.
