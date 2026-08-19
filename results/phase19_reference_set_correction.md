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

**Phase 19 reference-set re-measurement: recorded in the TWO dated continuations at the end of this file.**

## Addendum — 2026-08-19 — the sweep was already read on eight, and k does not move

Both sweeps were run through the pinned `select_ablation_prefix`, on the same production adapter
(`226f2ae5...`), in ONE process, back to back, differing in the `references`
argument and in nothing else. `results/phase19_reference_set_resweep.json` is the record;
`scripts/phase19_run.py target-resweep` is the driver, UNPINNED as every Phase 19 driver is. It
exports no adapter and runs no bit-identity control, because the operator asked for the SELECTION
before any re-scoring spend and `checkpoints/phase19_m1_erased_adapter.pt` is committed evidence
that must not be overwritten to discover whether it needs regenerating.

### |R| for the target slot, measured under both functions

| function | \|R\| | members |
|---|---|---|
| `phase18_extraction.reference_set_for('pet_name')` | 8 | `krix`, `nubbin`, `torvo`, `snorrel`, `nyxen`, `fenmark`, `grindlow`, `zorp` |
| `phase19_erasure.reference_set_for_calibration('pet_name', target)` | 6 | `krix`, `snorrel`, `nyxen`, `fenmark`, `grindlow`, `zorp` |

The twin strips `nubbin`, `torvo`, the two `CALIBRATION_POOL` siblings on this slot. Both sets contain the
target value `zorp`, so both give it a rank.

### The answer: THE SAME `k`, and the SAME 78 addresses

| quantity | value |
|---|---|
| committed `k` (`results/phase19_collateral_curve.json`) | 78 |
| re-measured `k` under `reference_set_for` (\|R\| = 8) | 78 |
| re-measured `k` under the calibration twin (\|R\| = 6) | 120 |
| `k` delta, twin minus reference | 42 |
| `stopped`, both sweeps | True / True |
| ablation prefix identical to the committed one, address for address | True |
| `intact_nll` identical to the committed one | True (`0.13365373015403748`) |
| dispersion census identical to the committed one | True |

**The committed sweep was already read on 8 members.** The curve recorded
`reference_set_size` = 8 when it was written, and
that self-report is now confirmed by re-measurement rather than taken on trust: the re-run
reproduces `k`, all 78 addresses in order, the intact
NLL and the census exactly.

The defect published at 19-12 is real and is not withdrawn. It is a defect in
`_selected_components`, which is the pin's own `erase` subcommand, and 19-12 did not run that
subcommand: `scripts/phase19_run.py target_ablate` was written specifically to route around it
(module docstring, reason 6). What the 19-12 checkpoint report failed to separate was the defective
PATH from the path that actually ran. Those are different claims and only the first one was true.

### Dispersion, both sweeps, laid out the same way

| sweep | `k` | by layer (0..5) | by projection |
|---|---|---|---|
| `reference_set_for` (\|R\| = 8) | 78 | 18 12 12 17 10  9 | c_proj 13  fc_in 35  fc_out 17  k_proj 2  q_proj 1  v_proj 10 |
| calibration twin (\|R\| = 6) | 120 | 26 28 20 21 13 12 | c_proj 22  fc_in 36  fc_out 27  k_proj 7  q_proj 11  v_proj 17 |

| | reference set | twin |
|---|---|---|
| largest single-layer share | 0.2308 | 0.2333 |
| largest single-projection share | 0.4487 | 0.3000 |

**Neither localises.** Both spread across all six layers and all six projections, both lean on
`fc_in`, and the twin is the LESS concentrated of the two by projection share — because it is
longer. There is no structural concentration in either that the other does not show.

That the twin's prefix is longer and otherwise the same shape is FORCED rather than coincidental,
and this run proves it instead of arguing it. `select_ablation_prefix` builds `ordered` from
`value_span_nll_mean` on the target's own value alone (`scripts/phase19_erasure.py:2482-2487`) and
never reads `references` in that loop; `references` enters only at `_rank_of`, i.e. the stopping
condition and the curve rows. So the reference set can move `k` and CANNOT move the ordering. Both
full 288-address orderings were compared and are identical
(`ordering_is_reference_set_invariant`), and the twin's 120 addresses are exactly the
reference ordering's first 120 (`twin_prefix_is_a_prefix_of_reference_ordering` =
True).

### What the twin would have cost, now measurable rather than hypothetical

At its stopping prefix 120, the twin's sweep has 2 slots off rank 1: `pet_name` at rank 3, `sibling_name` at rank 2.
The `reference_set_for` sweep at k = 78 has 1: `pet_name` at rank 2 — the target itself,
with all seven gated non-targets still at rank 1. Reading the stopping rule on
6 members would have zeroed 42 more
components and taken a bystander slot with it. That is the concrete size of the defect, and it is
why the 19-12 plan's instruction to use `reference_set_for` was right.

### Retraction status of every committed 19-12 number

**NOTHING IS RETRACTED.** The selection reproduces address-for-address, so nothing downstream of it
is contaminated and no re-scoring was required or run:

| artifact | status |
|---|---|
| `results/phase19_collateral_curve.json` (`k` = 78, 8 checkpoints, `intact_nll` = 0.13365373015403748) | STANDS — re-measured, identical |
| `checkpoints/phase19_m1_erased_adapter.pt` (`13f59301...`) | STANDS — the ablation of the reproduced prefix |
| `results/phase19_arm_erased.json` — the A2/K=48 exposure, dialogue and retention block | STANDS — derived from that adapter |
| `results/phase19_target_scores.json` — the (a) pooled read, the (b) seven, the soft descriptive pair | STANDS — derived from those draws |
| the fourth pin defect, as a defect in `_selected_components` | STANDS — published, unfixed, now quantified at k 78 against 120 |
| the 19-12 checkpoint's framing of that defect as touching the committed number | **WITHDRAWN** — the defective path was not the path that ran |

The one thing this addendum retracts is a claim about provenance, not a measurement: the checkpoint
report presented the fourth defect without separating the pin's `erase` path from `target_ablate`,
and the operator reasonably read it as contaminating `k`. The number was never contaminated. The
report was imprecise, and the imprecision was mine.

### The tripwire

`tests/test_phase19_erasure.py::test_the_committed_target_sweep_was_read_on_the_phase18_reference_set`
re-derives \|R\| from `phase18_extraction.reference_set_for` on every run and asserts the committed
curve's `reference_set_size` equals it, refusing to trust the artifact's own `reference_set_source`
string. It asserts the two sets DIFFER in size first, so it cannot pass vacuously. Watched RED
against the twin's size on a scratch mutation and GREEN against the committed artifact, which was
not modified.

`scripts/phase19_erasure.py` is untouched: sha256
`c407246de3c470094ab0bdd868961b7b1c22529c5e00522fec67c3852cb6e303`, 15 commits.
`checkpoints/persona_adapter.pt` is byte-identical after the run
(`226f2ae5...`, 1,350,523 bytes), proved before and after — 19-13 consumes
it intact.

## Addendum — 2026-08-19 — the defect is CORRECTABLE, and the tripwire is RED at 6 / GREEN at 8

This **EXTENDS the continuation above rather than opening a second record** — there is exactly one
reference-set document in this phase, and this is it. The section above established which path
produced `k` = 78 and that nothing is retracted. It did not record what the
CORRECTION is, and it exercised the tripwire in a commit message rather than in the document. Both
are here.

### The defect, located to the line

`scripts/phase19_erasure.py:3576` — inside `_selected_components`, the pin's own `erase`
subcommand:

```python
references=reference_set_for_calibration(fact.slot, fact),
```

Two lines below, the SAME call assembles its collateral map from
`extraction.reference_set_for(slot)` (`:3578`). So one invocation reads the TARGET's
stopping rule on 6 members while reading every BYSTANDER on 8. The
inconsistency is internal to a single function and needs no second measurement to see.

**It was never invoked by 19-12.** `scripts/phase19_run.py target-ablate` was written to route
around this subcommand (module docstring, reason 6), and the re-sweep above reproduces `k` =
78 address-for-address under `reference_set_for`. The defective path exists; it did
not run.

### The correction

`reference_set_for_calibration` is CORRECT for a calibration target and wrong for a taught one, and
its own docstring says why (`:3105`): the twin exists so that R holds exactly one value
the adapter under test was taught, which it secures by stripping the target's calibration SIBLINGS.
On the production adapter `reference_set_for` already guarantees that by construction — one locked
fact per slot — so there are no siblings to strip and the twin only SHRINKS the competitor set. The
correction is therefore a dispatch on which arm the fact belongs to, not a replacement of the twin
(`:3096` stays as it is): a TAUGHT target takes `extraction.reference_set_for(fact.slot)`
— the same set the collateral map two lines below already takes — and a CALIBRATION target keeps the
twin.

**It cannot land in the pin.** `scripts/phase19_erasure.py` is CLOSED at 15 commits
(sha256 `c407246de3c470094ab0bdd868961b7b1c22529c5e00522fec67c3852cb6e303`) and STAT-05's ancestry guard requires every commit touching it to be an ancestor
of the first add of every committed `results/phase19_*` artifact — 20 are now tracked. A
corrective commit on the pin reddens `tests/test_phase16_prereg.py` with no recovery, and
delete-and-re-add cannot launder it because the guard takes `adds[-1]`, the EARLIEST add. So the
correction is RECORDED here and left for a successor that owns the `erase` path. That is the same
D3 discipline defects A, B and C took, and the reason this document exists at all.

### The tripwire, exercised at BOTH reference sizes in one run

`tests/test_phase19_erasure.py::test_the_committed_target_sweep_was_read_on_the_phase18_reference_set`

| `reference_set_size` fed to the guard | outcome |
|---|---|
| 6 — the calibration twin's size | **RED** |
| 8 — `phase18_extraction.reference_set_for`, and the committed curve's value | **GREEN** |

RED-then-GREEN, so the guard is proved to discriminate rather than to pass on anything handed to it.
The RED leg ran against a COPY of the curve in a scratch tree with `scripts/` symlinked in and the
test module's `_ROOT` repointed at it. `results/phase19_collateral_curve.json` was read and never
written: byte-identical before and after, re-checked in the same process
(`True`).

## Defect numbering — the canonical labels (dated continuation, 2026-08-19)

This **EXTENDS the two continuations above rather than opening a third record** — there is still
exactly one reference-set document in this phase, and this is it. It is a LABELLING correction and it
retracts nothing: the |R| = 6 defect stands exactly as published, `k` = 78 stands, and every row of
the retraction-status table above is unchanged.

This document calls the |R| = 6 defect **"the FOURTH pin defect this phase"** (line 22, and again as
"the fourth" in the retraction-status table and the paragraph below it).
`results/phase19_erasure_report.md` independently calls the `retention_ppl` `[ppl, n]` defect
**"A FOURTH"**. Each sentence is correct about its own document and they are wrong together: a reader
reconciling the two miscounts, and no ordinal identifies either defect unambiguously.

**Five distinct pin defects are published in this phase. The canonical labels are LETTERS** — they
extend the `A`/`B`/`C` that `results/phase19_calibration_correction.json` already carries as record
keys, and letters cannot collide the way two "fourths" did:

| label | defect | line in the CLOSED pin | first published in |
| --- | --- | --- | --- |
| **A** | `zero_results_have_nll` compares an ORDERED tuple against records serialised with `sort_keys=True`, so it reads False on KEY ORDER ALONE while every NLL is present | `:1562` vs `:2948` | `results/phase19_calibration_correction.json` `defects.A` |
| **B** | `_calibration_rate()` reads `record["pre_erasure"]["per_fact"]`, i.e. Phase 18's candidate recall 0.8846153846153846, not the calibration arm's own rate | `:3850-3855` | `results/phase19_calibration_correction.json` `defects.B` |
| **C** | `rows.update(per_fact_rows(...))` lets one (b) tier overwrite the other, and the pinned `report` subcommand SystemExits on the resulting rows | `:2922` | `results/phase19_calibration_correction.json` `defects.C` |
| **D** | `_cmd_report` passes `retention_perplexity`'s `[ppl, n]` pair straight into the gate's scalar `retention_ppl=`, where `retention_ppl <= retention_cap` raises `TypeError` | `:3811` | `results/phase19_erasure_report.md` — the paragraph it calls **"A FOURTH"** |
| **E** | `_selected_components` reads the TARGET's stopping rule on the calibration twin's 6 members while reading every BYSTANDER on 8, inside one call | `:3576` | `results/phase19_reference_set_correction.md` — the sentence it calls **"the FOURTH pin defect this phase"** |

**Read every ordinal in THIS document as E.** "This is the FOURTH pin defect this phase" publishes
**E**; the retraction-status row "the fourth pin defect, as a defect in `_selected_components`" is
**E**, still STANDS, still published and unfixed, still quantified at `k` 78 against 120; and "the
checkpoint report presented the fourth defect without separating the pin's `erase` path from
`target_ablate`" is **E** as well. The one claim withdrawn above — that the defective path
contaminated the committed `k` — is unaffected by the relabelling, and nothing further is withdrawn
here.

**E is the phase's fifth defect and it is NOT one of the four that block the pinned report path.**
`results/phase19_erasure_report.md`'s ship decision enumerates C, D, A and B as the four independent
ways the pin's own `_cmd_report` cannot reproduce the verdict. E is absent from that list because it
sits in `_selected_components`, the pin's `erase` subcommand, which neither 19-12 nor the render
ever called. That enumeration is unchanged, the single withheld claim is unchanged, and the ship
decision is still `DO NOT SHIP`.

**Why this is a continuation and not an in-place renumber.** The labels being corrected are published
text, and two of the three occurrences sit inside a dated addendum. D3 fixes the correction path as a
dated continuation BESIDE the original rather than an edit over it — the same reason the |R| = 6
defect itself was published rather than repaired, and the reason this document exists at all. Editing
the bytes would also erase the evidence that the miscount ever existed, which is the record a future
audit needs. The identical table is appended to `results/phase19_erasure_report.md`, so either
document disambiguates all five defects on its own.

`scripts/phase19_erasure.py` is untouched: sha256
`c407246de3c470094ab0bdd868961b7b1c22529c5e00522fec67c3852cb6e303`, 15 commits.
