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

**Phase 19 calibration-rate correction: not yet recorded.**
