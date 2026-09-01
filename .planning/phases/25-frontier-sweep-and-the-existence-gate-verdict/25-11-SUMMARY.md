---
phase: 25-frontier-sweep-and-the-existence-gate-verdict
plan: 11
subsystem: calibration
tags: [D-24, D-14, dp-sgd, clip-norm, throughput, calibration, resource-measurement]
requires:
  - src/personacore/privacy/dpsgd.py        # _global_norm / absorb_record / the clip-domain refusals
  - scripts/teach_persona.py                # train_arm, arm_spec, arm_outputs, refuse_if_exists
  - scripts/phase23_run.py                  # _measure_condition (CAL-05's bracket), synchronized_seconds
  - scripts/phase25_run.py                  # atomic_write_json (25-10)
  - scripts/phase25_prereg.py               # POINT_RECORD_GLOB, POINT_RECORDS_AT_COMMIT (25-01)
  - scripts/phase25_record.py               # ORDERED_ARMS, point_key grammar (25-08)
  - results/phase23_sigma_zero.json         # clip_norm 1e6, clip_bind_count 0
  - results/phase23_cost.json               # the 161.124 anchor, sizing["16"], n_draws_measured 768
  - results/phase23_noised_dp_n64_sigma0p500000.json  # D-24's 12800/12800 counter-example
provides:
  - scripts/phase25_calibrate.py                            # both probes + CALIBRATION_PREFIX
  - scripts/phase25_calibrate.py::CALIBRATION_PREFIX        # "phase25_calibration", excluded from the point set
  - scripts/phase25_calibrate.py::CLIP_NORM_RULE            # the derivation rule, recorded before the number
  - scripts/phase25_calibrate.py::clip_domain_refusals      # CTRL-02's four transcripts, no model, no GPU
  - scripts/phase25_run.py::device                          # the draw loop's missing resolver
  - results/phase25_clip_calibration.json                   # 14,400 per-record norms, value by value
  - results/phase25_adversarial_throughput.json             # 2 x 768 timed draws + the 8-term schedule
affects:
  - 25-12   # pins CLIP_NORM = 1.3254119157791138 and CONTROL_CLIP_NORM = 1000000.0
  - 25-14   # the LaunchAgent schedule is sized on this record's 8-term envelope
  - 25-15   # the control points run at CONTROL_CLIP_NORM, never at the calibrated C
  - 25-17   # sweep-time argv reads the pinned C
tech-stack:
  added: []            # zero installs; pyproject.toml byte-unchanged (RPT-03)
  patterns:
    - constructor-shadow-to-read-the-mechanisms-own-accounting
    - rule-recorded-before-the-number-it-produced
    - abandon-the-biased-window-rather-than-caveat-it
key-files:
  created:
    - scripts/phase25_calibrate.py
    - tests/test_phase25_calibrate.py
    - results/phase25_clip_calibration.json
    - results/phase25_adversarial_throughput.json
  modified:
    - scripts/phase25_run.py         # + device(); both tp.device() call sites repointed
    - tests/test_phase23_resume.py   # train_arm census register, Rule 3
    - .planning/phases/25-.../deferred-items.md
decisions:
  - "C is derived, not chosen: the p50 ORDER STATISTIC of dp_n64's own 12,800 measured per-record norms, no interpolation, so the candidate IS one of the measured values and re-derives by index under exact equality. The rule is recorded BEFORE the number in the record itself."
  - "TWO clip constants, decided here because 25-CONTEXT resolves the pair nowhere: CLIP_NORM = 1.3254119157791138 for the noised points and CONTROL_CLIP_NORM = 1000000.0 for the control, so D-01's bit-level reproduction stays reachable."
  - "The probe runs at sigma = 0 and C = 1e6 read live from phase23_sigma_zero.json. A binding bound would make the sample a picture of the bound rather than of the records; a noised trajectory would have to name its sigma."
  - "A 50-step window was ABANDONED, not caveated. It overstated the median by 4.10x at dp_n8 and 2.33x at dp_n64. At fixed sigma an oversized C is pure excess noise bought for nothing, so both capacities were run to the full MAX_STEPS."
  - "768 draws is reproduced as phase23_cost.json's OWN composition — floor + ceiling + base_floor, 3 conditions x 4 shapes x 64 — not the plan's 8 x 8 x 4 x 2, which is 512."
  - "device() is owned by phase25_run, not teach_persona: teach_persona.py is pinned by results/phase24_token_budget.json's provenance.module_sha256, so a resolver there moves a committed Phase-24 digest to fix a Phase-25 defect."
patterns-established:
  - "Read the measured quantity out of the mechanism's own accounting via a constructor shadow, never re-implement it — the measurement and the mechanism then cannot disagree."
  - "Record the derivation rule as a string BEFORE the number it produced, and have a test recompute the number from the recorded values under the recorded rule."
  - "When a sampling window is measured to bias the headline number, abandon the window and keep the bias measurement in the record so the finding survives its own correction."
requirements-completed: [FRONT-01, ADVT-01]
duration: 128min
completed: 2026-09-01
---

# Phase 25 Plan 11: Clip Calibration and Adversarial Throughput Summary

**`C` is now a measurement: 1.3254119157791138, the p50 of 12,800 per-record gradient norms recorded value by value on the DP path — and the adversarial throughput curve is measurably NOT flat, 267.09 vs 216.25 draws/min at the two extremes, which is exactly why D-14 forbade extrapolating from one.**

## Performance

- **Duration:** ~128 min wall clock, of which **~92 min is GPU measurement** (see the honest accounting below)
- **Tasks:** 3 of 3
- **Files modified:** 7 (4 created, 3 modified)
- **Full suite:** `1907 passed, 1 skipped` in 1202.03 s — **+25 passed, +0 failed** against the 1882/1 baseline. The +25 is exactly `tests/test_phase25_calibrate.py`.
- **`make lint`:** `All checks passed!` / `254 files already formatted`

### GPU wall clock, per measurement, actual — and the overrun stated plainly

The plan budgeted **≈30–40 min**. Actual GPU spend was **~92 min**, in three tranches:

| Tranche | What | Wall clock | Kept? |
|---|---|---|---|
| 1 | clip probe, `dp_n64` truncated to 50 steps | 156.2 s + 310.1 s = **7.8 min** | **DISCARDED** — the window was measured biased |
| 2 | clip probe, both capacities at full `MAX_STEPS` | 156.0 s + 1261.2 s = **23.6 min** | superseded by tranche 3 |
| 2 | throughput probe, both extremes | **15.0 min** (899.4 s) | superseded by tranche 3 |
| 3 | clip probe re-run against final module bytes | 155.1 s + 1246.4 s = **23.4 min** | **COMMITTED** |
| 3 | throughput probe re-run | **14.9 min** (893.2 s) | **COMMITTED** |
| — | one crashed throughput leg (`tp.device()` AttributeError, after its 78 s training) | ~2 min | discarded |

**Two overruns, both deliberate, both reported rather than absorbed:**

1. **The 50-step window was abandoned (+15.8 min).** The first pass truncated `dp_n64` to 3,200 records to fit the budget. `dp_n8`'s own full run then measured what that window costs: **window median 2.2749314308166504 against full-run median 0.5546967387199402 — a 4.101216524305610x overstatement.** At `dp_n64` the same comparison reads **3.0871102809906006 vs 1.3254119157791138 = 2.329170459566837x**. Shipping a `C` I had measured to be 2.3x too large — at fixed σ, `std = sigma * C`, so an oversized `C` is pure excess noise bought for nothing since ε does not depend on `C` — is precisely the failure this plan exists to prevent. Both capacities were re-run to the full 200 optimizer steps.
2. **Both probes were re-run against the final module bytes (+38.3 min).** The freshness guard pins `scripts/phase25_calibrate.py`'s sha256 inside both records; fixing the driver defect below changed those bytes. The guard was honoured, not weakened.

**Every clip-calibration number reproduced bit-identically across the two independent full runs** (min / median / p90 / p99 / max / mean identical at both capacities; only wall clock moved, 156.0→155.1 s and 1261.2→1246.4 s). That reproduction is itself evidence the measurement is deterministic.

## Task Commits

1. **Task 1: the per-record norm distribution (D-24)** — `ab3578c` (feat)
2. *(driver fix, first attempt)* — `849657d` (fix), **reverted** by `28ed553`
3. **Task 2: the 768-draw throughput probe at both extremes (D-14)** — `e525b52` (feat)
4. **Task 3: the guard** — `79da856` (test)
5. **Driver fix, final** — `6df1eba` (fix)
6. **Both records re-measured against final module bytes** — `1eb2b64` (feat)

## D-24 — the per-record norm distribution, measured

Driven through the single production entry `teach_persona.train_arm` at the `dp_fn=` gradient seam, at **σ = 0** and **C = 1000000.0 read live from `results/phase23_sigma_zero.json`** (which recorded `clip_bind_count` 0, so the bound provably did not bind and the sample is the *unclipped* records). The norm is read out of `DPSGD._global_norm` — the mechanism's own accounting — through a constructor shadow, never re-implemented.

**Per-record global L2 norms, on the DP path, full `MAX_STEPS = 200` at both capacities:**

| Capacity | n_records | min | median | p90 | p99 | max | mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| `dp_n8` | 1,600 | 0.218611 | **0.554697** | 2.566053 | 5.083592 | 6.244622 | 1.039884 |
| `dp_n64` | 12,800 | 0.870138 | **1.325412** | 3.430469 | 5.101375 | 6.907835 | 1.738734 |

**Beside `results/phase23_matched_control.json`'s `grad_clip_evidence` — a DIFFERENT QUANTITY, stated plainly:** that record's max pre-clip norms are **2.277066469192505 / 2.202071905136108 / 2.302…** across seeds 1337/1338/1339, every `bound_count: 0`. Those are **BATCH-LEVEL norms on the NON-DP path** — one batch's averaged gradient, 200 calls per seed. The table above is **PER-RECORD norms on the DP path** — one micro-step's gradient, 1,600 and 12,800 of them. One batch's averaged gradient is not one record's gradient; the two are quoted side by side here only for scale, and no bound in the record is derived from the batch-level figure.

**The `C` candidate, derived under a rule recorded before it:**

```
clip_norm_candidate = sorted(per_record_norms['dp_n64']['values'])[math.ceil(0.5 * n_records) - 1]
                    = values[6399]
                    = 1.3254119157791138
```

The quantile is fixed at **p50** for a stated reason, not a preference: at fixed σ, ε does not depend on `C` at all, so `C` trades clipping bias against noise magnitude and nothing else — the median is the `C` minimising `E|record_norm − C|` over the measured records, and it is the operating point Abadi et al. (2016) state. The binding capacity is `dp_n64` because that is where the counter-example lives. `tests/test_phase25_calibrate.py::test_the_c_candidate_re_derives_from_the_recorded_rule` recomputes it from the recorded values under exact equality — that assertion is what 25-12's pin rests on.

**D-24's question, answered in counts with a denominator:**

| Capacity | records with norm > 1.0 | denominator | at the candidate C = 1.3254… |
|---|---:|---:|---:|
| `dp_n64` | **12,508** | 12,800 | 6,400 / 12,800 (the median, by construction) |
| `dp_n8` | 454 | 1,600 | 350 / 1,600 |

`results/phase23_noised_dp_n64_sigma0p500000.json` recorded `clip_bind_count` **12800 of 12800** at `C = 1.0`, ε 519.6981942303134. **That was not an accident of one run:** 12,508 of 12,800 records (over the same denominator, on the same arm) genuinely exceed 1.0, so `C = 1.0` sits below almost every record's norm and the 100% binding is the expected reading. At fixed σ that is pure clipping bias bought for nothing.

**The control's `C` is NOT this number.** `control_clip_norm = 1000000.0` is recorded as a separate constant, read live from `phase23_sigma_zero.json`, because D-01's reproduction is bit-level against that record. **25-CONTEXT resolves this pair nowhere, so the decision is made and recorded here:** plan 25-12 must pin **two** constants — `CLIP_NORM = 1.3254119157791138` for the noised points and `CONTROL_CLIP_NORM = 1000000.0` for the control. (`phase25_record.CONTROL_CLIP_NORM` does not exist at this commit; 25-10 made `dp_clip_norm` caller-supplied precisely so the pin could land in 25-12/25-15.)

**The `clip_norm=inf` refusal, verbatim, obtained with no model and no GPU** (measured **0.0045 ms**; `DPSGD.__init__`'s PRE-PASS 1 is the numeric domain and runs *before* PRE-PASS 2's model audit, so `model=None` never reaches `named_parameters()`):

> `[dp-refusal:clip-domain] clip_norm is inf, which is not finite. math.inf is REFUSED, not legal, and the measurement that forces this is a hard crash at exactly D-06's identity input: under torch 2.7.1, 0.0 * math.inf is nan, and torch.normal(mean=0.0, std=float('nan'), size=(3,)) raises 'RuntimeError: normal expects std >= 0.0, but found std nan'. The noise std is self.sigma * self.C and cannot be anything else -- D-07 forbids a branch that skips the draw at sigma == 0, and the noise-line guard forbids a pre-computed std attribute -- so an infinite C would crash the draw at a sigma of zero. C = infinity is therefore represented as a FINITE bound PROVEN NOT TO BIND: coef is exactly 1.0 on every record, x * 1.0 is bit-identical in IEEE-754 for finite x, and _clip_bind_count == 0 is the OBSERVATION that makes 'proven' literal.`

All four illegal values (`inf`, `0.0`, `-1.0`, `nan`) are captured, each in **under 0.005 ms**. The refusal *itself* stays asserted in **wave 1** (`tests/test_phase25_prereg.py::test_clip_domain_is_refused`, 5 passed); this plan only proves the recorded transcripts are live copies.

## D-14 — adversarial throughput at both extremes

**768 timed draws per extreme.** The composition is `results/phase23_cost.json`'s own: `floor_total + ceiling_total + base_floor_total` = **3 conditions × 4 shapes × 64 draws**, reusing `phase23_run._measure_condition` (the same `phase14_recall.draw_all` primitive `phase25_run._draw_one_shape` calls, the same `phase18_extraction._smoke_sample` 8 strided prompts × 8 draws, the same 4 warm-up draws discarded per shape).

**The two extremes' measured rates, side by side, condition-matched, with NO average taken:**

| Condition | ratio 0.0 | ratio 1.9090909090909092 | relative gap | exceeds 10% tolerance? |
|---|---:|---:|---:|:--:|
| **floor** (adapter, `STOP_IDS` active) | **267.0864 d/min** | **216.2500 d/min** | **19.034 %** | **YES** |
| ceiling (adapter, stop set emptied) | 82.5713 d/min | 84.6291 d/min | 2.432 % | no |
| base_floor (un-adapted base) | 154.1971 d/min | 159.0291 d/min | 3.038 % | no |

**THE THROUGHPUT CURVE IS NOT FLAT.** The two extremes differ by **19.03 %** at the floor condition — the condition the sweep will actually run in. The gap is the **adapter**, not the machine: `base_floor` is the *same un-adapted base model* at both probes and agrees to 3.04 %, and the ceiling (where every draw runs the full token budget regardless of the adapter) agrees to 2.43 %. **The divergence reproduced across two fully independent probes** (17.585 % on the first run, 19.034 % on the second, on separately trained adapter pairs). **No average was taken**, and a test walks every numeric leaf of the record asserting none equals the two rates' arithmetic mean.

D-14's insistence on probing both extremes was therefore load-bearing, not ceremony: a schedule extrapolated from ratio 0.0 alone would have priced the adversarial leg on a rate 19 % too fast.

Per shape at the floor condition (the divergence is not uniform — `A2` is the one shape that *speeds up* at the upper extreme):

| Shape | ratio 0.0 | ratio 1.909… |
|---|---:|---:|
| A1-mild | 292.38 | 198.14 |
| A1-aggressive | 229.27 | 189.72 |
| A2 | 314.72 | **324.29** |
| A3 | 248.93 | 196.25 |

`stop_terminated_n` is recorded per shape and per condition: **464 of 768 draws** stop-terminated at each extreme (256/256 at floor, 0/256 at ceiling, 208/256 at base_floor). The floor/ceiling gap **is** the stop-termination regime, and both adapters stop on every floor draw.

**The anchor.** `results/phase23_cost.json` sha256 `f3ba4d9a02f3040752d93c0395821075d8450860a9bae194ac120e8db8a47637`, recomputed from bytes and asserted live. Its `ratios.non_dp.training_seconds_per_point` carries the full double **161.12400419991462**; D-14 and 25-CONTEXT both spell it **161.124**, and the record carries **both** with the rounding asserted live. The ratio-0.0 leg's bins are **PROVED byte-identical to 24-06's committed digests** (`f146d42637c69e9eb1e7ac2248c9056a7966aed48f6498fa9cdb6d3db02d147b` / `a2c4771f92aa4e03127e451b1de880b9386bee5164ee512d291467c1eb1e59a2`) *before* the training clock is read, so the anchor comparison is two readings of one corpus.

**Measured against that anchor: `adv_n8` at ratio 0.0 trained in 77.908 s, which is 0.4835 × the committed 161.124 s/point.** Recorded as measured. The committed figure is the *protocol-matched non-DP comparator*'s own mean over a different recipe, so this is a divergence to disclose rather than a contradiction to resolve — but it is a 2.07× difference and later plans should not price adversarial training at 161 s.

## The re-derived envelope, as a sum of named terms

Finalised **after both extremes returned**, never extrapolated from one. Each term carries its own rule and its own measured/projected flag; no term is hidden inside a total.

| Term | floor (h) | ceiling (h) | measured? |
|---|---:|---:|:--:|
| `dp_scoring_44_points` (32 DP points × `phase23_cost` `sizing["16"]`) | 63.9350 | 100.7089 | no |
| `adversarial_scoring_12_points` (bracketed by **both** extremes' own projections) | 11.2310 | 36.0462 | **yes** |
| `dp_training_32_points` (16 × 205.442 s + 16 × 1383.276 s) | 7.0610 | 7.0610 | **yes** |
| `adversarial_training_12_points` (measured `adv_n8`, n=64 half scaled by the committed 6.733× ratio) | 1.0071 | 1.0071 | no |
| `d03_n64_matched_control_floor` (5 × (23.1 + 16.6) min) | 3.3083 | 3.3083 | no |
| `condition_c_44_points` (D-45: 44 × 87.4 s) | 1.0682 | 1.0682 | no |
| `never_taught_floor` (D-19 reuses the committed floor) | 0.0000 | 0.0000 | **yes** |
| `this_plan_calibration_probes` | 0.2481 | 0.2481 | **yes** |
| **TOTAL** | **87.8587** | **149.4478** | |

**Against 25-CONTEXT's ~107 h / ~150 h:** the **ceiling reproduces to 0.368 %** (149.4478 vs 150). The **floor lands 17.889 % BELOW** CONTEXT's measured-rate figure (87.8587 vs 107). Recorded as measured; nothing was adjusted to make the two agree. The floor gap is dominated by the adversarial scoring term, whose 11.23 h floor comes from *this plan's own measured* draw rates rather than from the noised `dp_n64` adapter's rates that `phase23_cost` published — the adv adapters stop on every floor draw at 12.8–15.3 mean tokens, against the noised adapter's 25.2.

The per-extreme h/point projections at `CURVE_K = 16`, both carried, neither averaged: ratio 0.0 → **0.9359 h floor / 3.0039 h ceiling**; ratio 1.909… → **1.1540 h floor / 2.9241 h ceiling**.

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 1 — Bug] `scripts/phase25_run.py::_draw_one_shape` called `tp.device()`, which does not exist**

- **Found during:** Task 2, the first time this phase actually drew.
- **Issue:** `teach_persona` has no `device` attribute. `scripts/phase25_run.py:519` and `:541` — **the sweep driver's entire draw loop** — both raised `AttributeError: module 'teach_persona' has no attribute 'device'`. No committed test reached it: every driver test in `tests/test_phase25_driver.py` takes the `--dry-run` branch, where `draw_point_shapes` returns before `_draw_one_shape` is called. It would have fired on the **first draw of the first sweep point, after up to 23.05 minutes of that point's training had already been spent.**
- **Fix:** `device()` added to `scripts/phase25_run.py` and both call sites repointed. **A first attempt put it in `scripts/teach_persona.py` (`849657d`) and was reverted (`28ed553`)** — `teach_persona.py` is pinned by `results/phase24_token_budget.json`'s `provenance.module_sha256`, and `tests/test_phase24_record.py::test_the_provenance_pins_match_the_live_module_bytes` went RED: a resolver there moves a committed **Phase-24** record's digest to fix a **Phase-25** defect. `phase23_run.device()` was also rejected as the source — Phase 25 *ports* from that module and never imports it (25-10), which is why `atomic_write_json` and the cache helpers were ported rather than imported.
- **Cost of the revert:** the module-bytes change forced both probes to be re-run (+38.3 min GPU) rather than weakening the freshness guard.
- **Commits:** `6df1eba` (fix), `28ed553` (revert), logged in `deferred-items.md`.
- **Residual, genuinely deferred:** `phase25_run._draw_one_shape` still has no test that reaches it. A single non-dry-run smoke over one shape at `k=2` would close it — 25-14/25-15's call, not this plan's.

**2. [Rule 3 — Blocking] Two repo-wide censuses reddened by the new module**

- `tests/test_phase23_resume.py::test_resume_from_none_is_inert` — the `train_arm(` grep census read 27 hits against a register of 25. Resolved **through the census's own mechanism**: both `phase25_calibrate` call sites registered by name, and the running call-kind total bumped `12 → 14` with the reason spelled out (these are the first *non-sweep* production consumers of the seam — the ladder now distinguishes a consumer that produces a sweep point from one that produces a calibration measurement, and does so by naming both rather than exempting the pair).

**3. [Rule 1 — Bug] The truncated norm window was measured biased and abandoned**

- Documented in full under *Performance* above. The 50-step window overstated the median by **4.101216524305610×** at `dp_n8` and **2.329170459566837×** at `dp_n64`. Both readings are kept in the record under `truncation_bias`, at both capacities, so the finding survives its own correction — and a test re-derives both from the recorded per-step partition.

### Corrections to the plan's own prose, measured

**1. `768` is NOT `8 × 8 × 4 × 2`.** The plan's Task 2 `read_first` describes the bracket as *"8 strided prompts × 8 draws × 4 attack shapes × 2 conditions after 4 warm-up draws discarded per condition"*. That product is **512**. `results/phase23_cost.json` composes its `n_draws_measured` as `floor_total + ceiling_total + sum(base_shapes)` — **THREE** conditions — and its own field is spelled `warmup_draws_discarded_per_shape`, i.e. per **shape**, not per condition. The committed record was followed; the correction is recorded in `scripts/phase25_calibrate.py::_probe_conditions` and asserted by `test_the_probe_reproduces_cal05s_own_768_composition`.

**2. `phase23_cost.json`'s anchor is `161.12400419991462`, not `161.124`.** The plan's acceptance criterion pins the 3-decimal literal. Both are carried and the rounding is asserted live rather than one silently replacing the other.

**3. `mitigation_budget.CURVE_K` is read by import; `ADVERSARIAL_RATIO_GRID`'s extremes are resolved by `min`/`max` rather than typed.** `phase25_record.ORDERED_POINT_KEYS()` **raises** at this commit (it reads `mitigation_budget.SIGMA_LADDER`, which plan 25-12 pins in wave 5), so the exclusion test proves disjointness **structurally over `phase25_record.ORDERED_ARMS`** — total for *any* ladder — and checks the live key set only additionally. A guard that could only run after wave 5 would guard nothing in wave 4.

### Authentication gates

None.

## Known Stubs

None. Both records are fully populated from measurements taken in this plan.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema at a trust boundary. The one new write surface is `results/phase25_{clip_calibration,adversarial_throughput}.json` via `phase25_run.atomic_write_json`, and both paths are proved disjoint from `phase25_prereg.POINT_RECORD_GLOB`.

## Verification

```
.venv/bin/python -m pytest tests/test_phase25_calibrate.py -v   ->  25 passed  (0 skipped)
.venv/bin/python -m pytest tests/test_phase25_prereg.py -k clip_domain -v  ->  5 passed
git ls-files 'results/phase25_point_*.json' | wc -l             ->  0
.venv/bin/python -m pytest tests/ -q                            ->  1907 passed, 1 skipped  (1202.03 s)
git diff --exit-code -- scripts/mitigation_budget.py scripts/mitigation_gate.py \
    scripts/mitigation_accountant.py scripts/mitigation_unit.py \
    scripts/phase18_extraction.py pyproject.toml                ->  exit 0
make lint                                                       ->  All checks passed! / 254 files already formatted
```

**Suite delta:** `1882 passed, 1 skipped` → `1907 passed, 1 skipped`. **+25 passed, +0 failed, +0 skipped.** The +25 is exactly `tests/test_phase25_calibrate.py`.

**Watched RED, by hand, on a `tmp_path` copy** (`EARLY_WINDOW_STEPS` edited `50` → `51`), verbatim:

> `provenance freshness: recorded 0adcd18e745a5126ffe38ed2a3c3e2c4f8e5e5979e1c4123ef180a38626a6782 != ac234451f197b41f865105176f12b5dcb2ac374d928294e429803ecbc2c1a29a for the edited copy`

The real tree stayed byte-identical throughout (`git status --porcelain scripts/` returned `''`, and the live digest still matched the record). The committed guard now pins `d769ebe488fce139…` in both records against `scripts/phase25_calibrate.py` at commit `6df1ebac4067`.

A second natural RED was taken from the file's own intermediate state: `test_no_average_was_taken_across_the_two_extremes` initially flagged `divergence.no_average_taken` — the prose field whose whole job is to *declare* that no average was taken. An unrestricted key scan flags the declaration and not the thing it declares, so the key rule was scoped to numeric leaves and the value scan (every float compared against the two extremes' arithmetic mean) left as the load-bearing half.

## Self-Check: PASSED

Created files, verified present:
- `scripts/phase25_calibrate.py` — FOUND
- `tests/test_phase25_calibrate.py` — FOUND
- `results/phase25_clip_calibration.json` — FOUND (591,637 B)
- `results/phase25_adversarial_throughput.json` — FOUND

Commits, verified in `git log`:
- `ab3578c`, `849657d`, `28ed553`, `e525b52`, `79da856`, `6df1eba`, `1eb2b64` — all FOUND

`.planning/STATE.md` and `.planning/ROADMAP.md`: **untouched** (orchestrator-owned).

## What 25-12 must pin

Two float literals in `scripts/mitigation_budget.py`, each with a `_PROVENANCE` sibling naming `results/phase25_clip_calibration.json`:

```python
CLIP_NORM = 1.3254119157791138          # noised DP points, both capacities
CONTROL_CLIP_NORM = 1000000.0           # the sigma=0 control only, both capacities
```

`C` cannot join `mitigation_gate.MECHANISM_KEYS` (D-25 — the gate is frozen and any commit after `results/phase20_*` exists reddens the ancestry guard permanently), and it does not need to: `capacity_comparison` ignores extra keys, so `clip_norm` travels in the mechanism dicts and the driver `_prove`s equality on it caller-side.
