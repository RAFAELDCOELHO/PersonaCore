# Phase 19 — which reference set the target sweep was read on

`scripts/phase19_erasure.py` is CLOSED at 15 commits (sha256
`c407246de3c470094ab0bdd868961b7b1c22529c5e00522fec67c3852cb6e303`). STAT-05's ancestry guard
requires every commit touching it to be an ancestor of the first add of every committed
`results/phase19_*` artifact, and delete-and-re-add cannot launder that — the guard takes
`adds[-1]`, the EARLIEST add (`tests/test_phase16_prereg.py:117-124`). So a defect found in the pin
after the fact is published as a DATED CONTINUATION beside the text and never as an edit
(`scripts/_addendum.py`, D3). This is the second such document in the phase; the first is
`results/phase19_calibration_correction.md`, which carries defects A, B and C.

## The pin defect, as reported at 19-12

`_selected_components` — the pin's own `erase` subcommand — passes
`reference_set_for_calibration(fact.slot, fact)` for EVERY fact, including the taught TARGET. On
`pet_name` that twin strips the two `CALIBRATION_POOL` siblings and returns a six-member set, while
`phase18_extraction.reference_set_for('pet_name')` — the set `measure_exposure` uses, and therefore
the set every exposure rank in the paired Phase 18 baseline was computed over — returns eight.

`ABLATION_STOP_RULE`'s stopping condition is "no longer at RANK 1 in its same-slot reference set".
Read on six members that is a different event from the one the arm record's exposure block
publishes on eight. This is the FOURTH pin defect this phase, and it was published in the 19-12
erasure commit rather than repaired, for the ancestry reason above.

## The question this document answers

The defect names a code path. It does not, by itself, say which path the committed `k = 78` was
produced by, and those are separable claims. The operator asked for the separation to be MEASURED:

> Re-run the component-selection sweep against `reference_set_for` — the same reference
> `measure_exposure` and the entire Phase 18 baseline use — and report whether `k` changes, and if
> so by how much: the same `k = 78`, a different `k` with the same dispersion pattern, or a
> different `k` with any structural concentration the six-member measurement did not show.

If the committed sweep had been read on six members, then `k = 78`, the erased adapter, the
collateral curve, the (a)/(b)/(c) readings and the exposure table would all be downstream of a
superseded selection and would have to be retracted in place before any further work.

**Phase 19 reference-set re-measurement: not yet recorded.**
