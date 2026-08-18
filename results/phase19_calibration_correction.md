# Phase 19 — the blind calibration rate, and the (a) floor it prices

The blind calibration of plan 19-09: mechanism M1 applied to `cal_person_varek` — one disposable
fact, disjoint from `CANDIDATE_POOL` and in a different slot from the target's — and then scored by
Phase 18's best attack family **A2 at K = 48**, the same adversary at the same budget that will
score the target. Blindness here is structural rather than promised: the derivation rule
`ERASURE_FLOOR_RULE` was committed at 19-03 (`6969e47`), before this adapter or this record
existed, and git order is the proof.

## The measured result

In the question unit, never the draw, and never as a bare percentage (STAT-02):

| tier | successes / questions |
| ---- | --------------------- |
| `core_taught` | 0 / 14 |
| `core_held_out` | 0 / 9 |
| **POOLED** | **0 / 23** |

1,104 draws (23 questions x K = 48), family A2, recorded at `results/phase19_arm_cal-erased.json`
(first added at `14ab93d`). At zero successes STAT-02 requires both bounds beside the rate:

```
wilson_upper_bound(0, 23) = 0.10525136178999417
rule_of_three(23)         = 0.13043478260869565
```

The pooled denominator is **23**, not 27: calibration facts carry no `RESERVED_HELDOUT_PROBES`
entry, so `calibration_questions` derives the count and the self-naming filter drops 8 of 31
rendered questions. `CALIBRATION_COMMENSURABILITY` clause 3 requires that 23 be published wherever
the rate is.

## Verdict

**AS THE CLOSED PIN COMPUTES IT — the (a) floor is `0.2`, branch `ceiling`, from a calibration
rate of `0.8846153846153846`.**

That is what `scripts/phase19_erasure.py` produces from its own committed code against its own
committed record — `lock_erasure_floor(_calibration_rate())` — and it is published here unchanged
and unedited, in D3's register: the literal reading ships as written, and any correction is added
beside it rather than over it.

`scripts/phase19_erasure.py` is CLOSED at 15 commits. STAT-05's ancestry guard requires every
commit touching it to be an ancestor of every committed `results/phase19_*` first-add, and those
artifacts now exist, so an edit reddens `tests/test_phase16_prereg.py` permanently. Deleting and
re-adding does not launder it either — the guard takes `adds[-1]`, the EARLIEST add
(`tests/test_phase16_prereg.py:117-124`). The guard's own docstring names the only sanctioned
path: "the correction path for a defect found later is a DATED CONTINUATION beside the published
text (`scripts/_addendum.py`, D3), never an edit" (`:342-346`).

## The calibration-rate correction

**Phase 19 calibration-rate correction: recorded in the dated continuation at the end of this file.**

## Addendum — 2026-08-18 — the calibration rate, the floor, and three pin defects

The blind calibration above was scored on 2026-08-18 and the run caught three defects in
`scripts/phase19_erasure.py`. The file is CLOSED at 15 commits and cannot be edited without
reddening STAT-05's ancestry guard permanently, so they are published here instead, beside the
verdict rather than over it. **Both floors below are real numbers produced by committed code. They
are not equal, and the one that governs is named explicitly at the end of this section — no reader
should have to infer it.**

### The corrected floor, against the one the pin computes internally

| | calibration rate | (a) floor | branch |
| --- | --- | --- | --- |
| **CORRECTED — GOVERNS** | 0 / 23 = `0.0` | **`0.09107873950450847`** | `reachability-min` |
| the pin's internal report | 92 / 104 = `0.8846153846153846` | `0.2` | `ceiling` |

The corrected floor is `lock_erasure_floor(0.0)` — the pin's own committed rule, applied to the
rate the blind calibration actually measured, re-derived from the committed record's own
23 draw rows through the pin's own `per_fact_rows` driven once per tier. It
equals `ERASURE_FLOOR_MIN` = `wilson_upper_bound(0, 27)` exactly, so the
`reachability-min` clamp binds and condition (a) will clear ONLY on a near-perfect erasure: the
target's post-erasure Wilson upper bound must land at or below `0.09107873950450847`, and the smallest
value that bound can take at n = 27 IS `0.09107873950450847`. Zero successes over
every scored target question is the only outcome that satisfies it.

`0.2` is `FLOOR_CEILING`, saturated. It is what `_cmd_report` still prints, and it is
**two-and-a-fifth times looser** than the measured evidence supports.

### A — an order-sensitive comparison masks a SUCCESS as INCONCLUSIVE

`run_erasure_arm` serialises the record with `json.dumps(..., sort_keys=True)` (`:2948`).
`zero_result_exposure_gaps` compares `tuple(entry) != extraction.EXPOSURE_RECORD_KEYS` (`:1562`) —
an ORDERED tuple against alphabetically sorted keys. Same key SET, different key order:

```
on disk   : ('admissible', 'ceiling_bits', 'descriptive_label', 'exposure_bits', 'length_spread', 'n_references', 'nll', 'rank', 'slot', 'spread_zero_control', 'threats_to_validity')
committed : ('slot', 'admissible', 'nll', 'rank', 'exposure_bits', 'ceiling_bits', 'n_references', 'length_spread', 'spread_zero_control', 'descriptive_label', 'threats_to_validity')
set equal : True     order equal : False
```

Measured on the committed record: `zero_results_have_nll` is `False`, with
2 gaps, both of them the key-order complaint — while all
6 frame x reduction NLLs in each
exposure block are present and finite. Reordering the keys and changing not one value flips the
flag to `True` with zero gaps remaining, and the record is byte-identical under `sort_keys`.

This is not cosmetic. `erasure_gate` short-circuits to INCONCLUSIVE when `target_successes == 0`
and this flag is `False` — and **a successful erasure produces exactly that zero.** On 19-10's
target arm `_cmd_report` reads the record off disk, so a clean success would publish as
INCONCLUSIVE. Catching it on a disposable calibration fact is precisely what a calibration run is
for.

### B — the floor is derived from Phase 18's candidates, not from this calibration

`_calibration_rate()` (`:3850-3855`) reads `record["pre_erasure"]["per_fact"]`. `run_erasure_arm`
fills that block from the PHASE 18 record for every arm, so on the calibration record it holds the
eight `cand_*` rows and not `cal_person_varek`:

```
_calibration_rate()                -> 0.8846153846153846   (= 92/104, Phase 18's CANDIDATE recall)
lock_erasure_floor(that)           -> 0.2   branch ceiling
the measured calibration rate      -> 0.0   (= 0/23)
lock_erasure_floor(that)           -> 0.09107873950450847   branch reachability-min
```

The docstring says the rate is "read off the calibration arm's own record". The code reads Phase
18's candidates. Prose and arithmetic disagree, and the arithmetic is what ships — which is why
this continuation names the corrected floor as governing rather than leaving the two numbers to
sit side by side unranked.

### C — the `per_fact` block drops a tier

`per_fact` is keyed by `fact_id`, and `run_erasure_arm` merges the two tiers with
`rows.update(...)`. Both tiers carry the same `fact_id`, so `core_taught` overwrites
`core_held_out` and the committed artifact publishes `n_questions: 14` where
`CALIBRATION_COMMENSURABILITY` clause 3 requires **23**. Re-derived per tier from the
same committed draws by the same `per_fact_rows`:

| tier | successes / questions |
| --- | --- |
| `core_taught` | 0 / 14 |
| `core_held_out` | 0 / 9 |
| **POOLED** | **0 / 23** |

The numerator is zero in both tiers, so neither the rate nor the floor branch moves — the defect
costs a published denominator, not a published floor. No second copy of the draws is written: the
rows above are a re-derivation of a committed file by the pin's own instrument, and
`tests/test_phase19_correction.py` re-runs it on every test run so a hand-edited number goes red.

### Which number governs the erasure verdict

**The formal erasure verdict is read against the CORRECTED floor, `0.09107873950450847`
(`reachability-min`). It is NOT read against `0.2`, which is what the pin's internal
report still computes from Phase 18's candidate rows under defect B.** `0.2` remains
published above, unedited, because D3 publishes the literal reading beside the correction rather
than replacing it — but it is superseded for every gate, every constant and every rendered verdict
downstream. `scripts/phase19_floor.py` (19-11) must lock `TARGET_FLOOR = 0.09107873950450847`, and
`tests/test_phase19_correction.py::test_a_locked_floor_must_be_the_corrected_one` goes RED the
moment it locks anything else. The machine-readable half of this section is
`results/phase19_calibration_correction.json`, whose `governs` field names the same number.

None of the above edits `scripts/phase19_erasure.py`. It is still at 15 commits, sha256
`c407246de3c470094ab0bdd868961b7b1c22529c5e00522fec67c3852cb6e303`, and
`tests/test_phase16_prereg.py` is green.
