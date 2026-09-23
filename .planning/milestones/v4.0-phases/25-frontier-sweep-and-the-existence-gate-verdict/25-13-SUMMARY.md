---
phase: 25
plan: 13
subsystem: privacy-calibration
tags: [D-04, D-06, CTRL-01, CTRL-02, probe2, pre-registration, bounded-disagreement]
requires:
  - results/phase23_matched_control.json
  - results/phase23_sigma_zero.json
  - scripts/phase23_matched_prereg.py
  - scripts/phase25_calibrate.py
  - scripts/mitigation_budget.py
provides:
  - results/phase25_probe2_tensors.json
  - scripts/phase25_probe2.py
  - tests/test_phase25_probe2.py
affects:
  - tests/test_lora_inject.py
  - tests/test_phase23_resume.py
tech-stack:
  added: []
  patterns:
    - "read-and-validate every record BEFORE spending GPU time"
    - "dry-run the whole assembly path against stub rows first"
    - "import by path + digest, never retype"
    - "aggregate recomputed from its own rows, watched RED on a perturbed copy"
key-files:
  created:
    - scripts/phase25_probe2.py
    - results/phase25_probe2_tensors.json
    - tests/test_phase25_probe2.py
  modified:
    - tests/test_lora_inject.py
    - tests/test_phase23_resume.py
decisions:
  - "PROBE 2 lives in scripts/phase25_probe2.py, not in scripts/phase25_calibrate.py, because that module's sha256 is pinned inside two committed calibration records whose re-emitter would re-derive mitigation_budget.CLIP_NORM. Same call plan 25-11 made for scripts/phase25_sigma_hi.py."
  - "max_rel_diff is defined ELEMENTWISE (Phase 23's own definition) and max_norm_rel_diff travels beside it; both definitions fixed in code before the measurement ran."
  - "The n=8 elementwise figure does NOT reproduce 2.178e-07 and the record says so — reproduces: false, ratio 836473.8382045203."
metrics:
  duration: "1h 35m (GPU 47m 21s; two full suite runs 20m 14s + 20m 10s)"
  completed: 2026-09-01
---

# Phase 25 Plan 13: PROBE 2 at Both Capacities Summary

D-04's tensor comparison re-run at `dp_n8` **and** `dp_n64` before any sweep point exists, with the
measured divergence committed as a prediction: 72/72 tensors per capacity, `agreement_bound`
**0.18218400196094453** (n=8) and **0.03445445375813015** (n=64, a first measurement), Phase 23's
four declared differences imported by path plus live sha256, and D-06's prefix-only separation
recorded as a structural field.

## What Was Measured

Two adapters per capacity, same seed (1337), same budget, **same bins**, one seam apart:

| leg | arm | seconds | proof taken before any comparison existed |
|---|---|---|---|
| control | `dp_n8` | 207.5 | `clip_bind_count=0` at `C=1000000.0` |
| comparator | `seam_off_comparator_n8` | 148.5 | 200 clip calls, pre-clip norms `[0.335902, 2.27707]` vs `1000000.0` |
| control | `dp_n64` | 1294.8 | `clip_bind_count=0` at `C=1000000.0` |
| comparator | `seam_off_comparator_n64` | 1188.1 | 200 clip calls, pre-clip norms `[0.158905, 1.8806]` vs `1000000.0` |

**Total GPU wall clock 47m 21s** (07:32:05Z → 08:19:26Z) against the plan's ~46 min budget — the
first budget in this phase that held. Training sum 2838.9 s; the control legs reproduce Phase 23's
committed rates closely (`dp_n8` 207.5 s vs `phase23_cost` 205.4 s).

The comparator's `grad_clip` is equalised to `phase23_matched_prereg.MATCHED_GRAD_CLIP`
(`1000000.0`) and **observed** non-binding on the runs that happened. Without it the residual would
have been the clip, not the seam — `loop.py` applies `clip_grad_norm_` iff the DP seam is absent,
and Phase 23 measured the unequalised control binding on 19 of its first 25 steps.

### The readings, raw

```
dp_n8   72 tensors | agreement_bound 0.18218400196094453 | max_abs 6.51925802230835e-08  | max_norm_rel 2.0877011860359762e-06 | zero_reference_elements 0
dp_n64  72 tensors | agreement_bound 0.03445445375813015 | max_abs 7.450580596923828e-08 | max_norm_rel 1.496777817894806e-06  | zero_reference_elements 0
```

Worst rows, quoted verbatim from the record:

```
n8  {"name": "blocks.3.mlp.fc_in.lora_B",  "shape": [1536, 8], "numel": 12288,
     "max_abs_diff": 2.514570951461792e-08,  "max_rel_diff": 0.18218400196094453,
     "ref_max_abs": 0.0307441595941782,  "max_norm_rel_diff": 8.179019965593589e-07}
n64 {"name": "blocks.1.attn.q_proj.lora_B", "shape": [384, 8],  "numel": 3072,
     "max_abs_diff": 2.3748725652694702e-08, "max_rel_diff": 0.03445445375813015,
     "ref_max_abs": 0.03288407251238823, "max_norm_rel_diff": 7.22195392427382e-07}
```

Final train losses agree to eight decimals — `dp_n8` `0.0603661946952343` vs `0.06036620284430683`,
`dp_n64` `0.15966508188284934` vs `0.15966508572455496` — which is the independent confirmation
that the two paths are the same computation up to float32 re-summation order.

## The n=8 Column Against Phase 23, Stated Plainly

**It does not reproduce.** `results/phase25_probe2_tensors.json` records
`phase23_reference.reproduces: false` and `ratio_to_reference: 836473.8382045203` — the measured
`0.18218400196094453` against the reference `2.178e-07`. No bound was widened to make that
comfortable, and the record names the reason rather than arguing it:

1. **It is not the same quantity.** Phase 23's figure came from a **single-step gradient**
   comparison (`phase23_matched_prereg.DP_FN_BRANCH_DISPOSITIONS`, "the `/accum` bypass at
   loop.py:211"). This probe compares **trained adapters after the full 200-step budget**, so 200
   AdamW steps compound the per-step residual Phase 23 measured once. The record carries this as
   `probe_shape.why_the_two_are_not_the_same_quantity`, written before the numbers existed.
2. **The elementwise definition is denominator-sensitive.** The n=8 worst row's absolute difference
   is `2.514570951461792e-08` against a tensor whose largest element is `0.0307441595941782` — the
   ratio is large only because the element it landed on is tiny. `max_norm_rel_diff` is the
   denominator-hazard-free reading of the same row: `8.179019965593589e-07`, and the per-capacity
   maxima are `2.0877011860359762e-06` / `1.496777817894806e-06` — about one order of magnitude
   above Phase 23's single-step figure, which is what 200 steps of compounding predicts.

**A derivable consequence worth recording:** the max absolute difference is `6.51925802230835e-08`
(n=8) and `7.450580596923828e-08` (n=64), both **below Phase 23's own `atol=1e-7`**. So under Phase
23's exact tolerance — `allclose(rtol=1e-5, atol=1e-7)` — these two trained adapters would still
pass at both capacities. The paths disagree, boundedly, and the bound is small in absolute terms.

## The n=64 Column Is a First Measurement

`first_measurement.value = 0.03445445375813015`. n=64 had never been probed, so there is no prior
figure for it to reproduce and it must not be read as a repetition. It is *smaller* than the n=8
elementwise figure while its absolute difference is slightly larger — again a denominator effect,
not a capacity effect, and the record carries both columns so a reader can see that for themselves.

## Deviations from Plan

### 1. [Rule 3 — Blocking] PROBE 2 lives in a new module, not in `scripts/phase25_calibrate.py`

- **Found during:** Task 1, before any GPU second was spent.
- **Issue:** The plan says "Extend `scripts/phase25_calibrate.py`". The tree refuses that edit.
  `results/phase25_clip_calibration.json` and `results/phase25_adversarial_throughput.json` both
  pin that module's sha256 (`d769ebe488fce139…`, verified live equal to the file at HEAD), and
  `tests/test_phase25_calibrate.py::test_the_calibration_provenance_matches_the_live_module_bytes`
  recomputes it from bytes. One edited byte reddens both records.
- **Why re-emission was refused:** the documented emitters (`run_clip_calibration` /
  `run_throughput_probe`) re-derive their records only by **re-measuring** (~1246 s + ~155 s + the
  throughput probe). That re-derives `clip_norm_candidate`, which is the source of
  `mitigation_budget.CLIP_NORM = 1.3254119157791138` — a literal plan 25-12 pinned and this plan's
  own acceptance criteria require to stay byte-unchanged. Re-emitting would have put a pinned
  constant's provenance at risk to buy nothing.
- **Fix:** `scripts/phase25_probe2.py` **imports** `phase25_calibrate`'s `CALIBRATION_PREFIX`,
  `_prove`, `sha256_of`, `_rel`, `_release_calibration_targets` and `_taught_family_ids` instead of
  editing it. `git diff --exit-code -- scripts/phase25_calibrate.py` is clean.
- **Precedent, found in the tree afterwards:** plan 25-12 made the identical call for
  `scripts/phase25_sigma_hi.py`, and `tests/test_phase23_resume.py`'s register already records the
  reason verbatim — *"It lives in its own module rather than in `phase25_calibrate.py` because that
  module's sha256 is pinned inside two committed calibration records."* This deviation is the
  phase's established pattern, not a novel one.
- **Commit:** `ebdbf06`

### 2. [Rule 3 — Blocking] Two repo-wide censuses red on the new module

- **Found during:** the first full-suite run (`2 failed, 1947 passed, 1 skipped`).
- **`tests/test_phase23_resume.py::test_resume_from_none_is_inert`** — the `train_arm` call-site
  register is a hard-equality ledger. Added one visible line for
  `scripts/phase25_probe2.py::train_control_path` with its reason, and bumped the count literal
  `8+1+1+1+1+2+1` → `+ 1`. It passes no `resume_from`, so `_RESUME_PASSERS` names no count for the
  file and a resume appearing there still reddens. Only the control half is a `train_arm` call —
  the comparator calls `tp.train(...)` directly with the DP seam absent, which is what makes it the
  seam-off path.
- **`tests/test_lora_inject.py::test_every_inject_lora_consumer_reads_the_artifact_config`** —
  `train_comparator_path` landed in the `unclassified` bucket, which **no allowlist entry can
  clear** because classification runs before the allowlist is consulted. Root cause measured:
  `_module_aliases` read only `tree.body`, so a module that imports `teach_persona` **inside** its
  functions (Phase 25's CPU-safe-at-import discipline) has an unresolvable `tp` and a well-formed
  producer reads as unanalysable — a false finding. Widened the resolver to also collect
  function-scoped `ast.Import` nodes with `setdefault`, so **top-level bindings win on collision**
  and the change is strictly strengthening: it can only move sites *out* of `unclassified`, and
  every one it moves must still be spelled under the same hard equality. Registered
  `("scripts/phase25_probe2.py", "train_comparator_path")` as a PRODUCER, same form and reason as
  the two `phase23_run.py` entries. Both bucket assertions still pass under hard equality, so no
  other site reclassified.
- **Commit:** `310040a`

No other deviations. No authentication gates. No architectural changes.

## Watched REDs

**The perturbed-aggregate natural RED** (T-25-69) — one row's `max_rel_diff` pushed above the bound
in a deep copy, the live guard's own body re-run against it, verbatim:

```
dp_n8: the record claims 72 agreeing tensor(s) of 72, but recomputing from its own rows at
agreement_bound=0.18218400196094453 gives 71. The aggregate has stopped describing its own data.
```

The committed record was re-read from disk afterwards and compared equal to its pre-perturbation
value — the copy is a copy.

**The planted bit-identity RED** (T-25-65) — a scratch module written into `tmp_path`, plan 25-01's
walker run against it, verbatim:

```
D-04 TRIPWIRE FIRED — a committed function asserts BIT-IDENTITY between the sigma=0 point and the seam-off path:
  /var/folders/.../tmpksl9zxo9/test_planted_probe2_identity.py::test_the_probe2_adapters_are_byte_identical — assertion ['equal'], sigma=0 marker(s) ['sigma_zero_adapter'], seam-off marker(s) ['dp_fn', 'seam_off_adapter']

WHAT THE CORRECT ASSERTION LOOKS LIKE: BOUNDED DISAGREEMENT, NEVER EQUALITY. Phase 23's PROBE 2 measured 72/72 LoRA tensors agreeing to 2.178e-07 RELATIVE at sigma=0 with a non-binding C — agreement to a bound, not bit identity. ...
```

`git status --porcelain tests/` was empty immediately after (asserted inside
`test_a_planted_bit_identity_assertion_here_would_fire`, which passes in the committed tree).

## The Dry Run Earned Its Keep

Per the phase's own instruction after 25-12 lost a 45-minute run to a tail bug, every record read
was validated first and the **whole assembly path was dry-run against stub rows** before any GPU
second. It caught a real defect: `AGREEMENT_BOUND_GOVERNS` spelled the required phrases in
upper case, so the plan's acceptance criterion `'bounded disagreement' in g` would have failed
*after* the 47-minute run. Fixed at zero cost.

## Verification

| check | result |
|---|---|
| `pytest tests/test_phase25_probe2.py -v` | **11 passed** in 2.84 s, **zero skipped** |
| `pytest tests/test_phase25_probe2.py -k "declared_differences" -v` | 2 passed, 9 deselected |
| `pytest tests/test_phase25_prereg.py -q` | 20 passed, 0 failed |
| `pytest tests/test_phase25_calibrate.py -q` | 25 passed (freshness guard still green) |
| `pytest tests/ -q` | **`1949 passed, 1 skipped`** in 1209.76 s (0:20:09) |
| delta vs the 1938/1 baseline | **+11 passed, skips unchanged** — exactly the 11 new tests |
| `git ls-files 'results/phase25_point_*.json' \| wc -l` | `0` |
| `git diff --exit-code` on the five pinned modules + `pyproject.toml` | clean |
| `git diff --exit-code -- scripts/phase25_calibrate.py` | clean |
| `make lint` | All checks passed; 258 files already formatted |
| `.planning/STATE.md`, `.planning/ROADMAP.md` | untouched |

The pre-existing uncommitted `.gitignore` modification was left alone; every commit staged files
individually.

## Commits

| hash | message |
|---|---|
| `ebdbf06` | `feat(25-13): PROBE 2 at both capacities, committed as bounded disagreement` |
| `2ad0a72` | `test(25-13): guard the PROBE 2 record by re-derivation, tripwire proved in scope` |
| `310040a` | `fix(25-13): resolve the two repo-wide censuses PROBE 2's module tripped` |

## Known Stubs

None. Every figure in `results/phase25_probe2_tensors.json` is the raw output of the run recorded in
its own `provenance` block (`git_sha 41192b8529f24f46c458ba4487278f4afc4192c7`, device `mps`, torch
`2.7.1`, python `3.11.15`, `2026-09-01T08:19:26Z`).

## Notes for Later Waves

- `agreement_bound` is the **elementwise** worst ratio, and it is denominator-sensitive by
  construction. Any later reader comparing capacities should read `max_norm_rel_diff` (or
  `max_abs_diff` against `ref_max_abs`) beside it; both travel in every row.
- The record's `point_set_exclusion` field states the operational meaning of "before any real sweep
  point": `git ls-files 'results/phase25_point_*.json'` was empty at the write, and
  `test_the_probe_record_predates_every_point_record` asserts the ancestry from `git log` once
  points exist.
- `scripts/phase25_probe2.py` is now the **third** Phase-25 module that had to stand outside
  `scripts/phase25_calibrate.py` for the sha256-pin reason. If a fourth is needed, the pattern is
  settled — do not re-litigate it, and do not re-emit the two calibration records to make room.

## Self-Check: PASSED

- `scripts/phase25_probe2.py` — FOUND
- `results/phase25_probe2_tensors.json` — FOUND (51,047 bytes)
- `tests/test_phase25_probe2.py` — FOUND
- `ebdbf06` — FOUND
- `2ad0a72` — FOUND
- `310040a` — FOUND
