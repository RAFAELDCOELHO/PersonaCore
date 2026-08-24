---
phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
plan: 11
subsystem: privacy-unit-record
tags: [unit-01, unit-03, unit-04, unit-05, unit-06, sc1, sc3, sc4, d-19, d-20, d-26, wave-6, checkpoint-blocked, t-21-03, t-21-06, t-21-50, t-21-51, t-21-52, t-21-53, t-21-54, t-21-49]
status: INCOMPLETE — stopped at the task-3 blocking human-verify checkpoint
requires:
  - "21-01 — scripts/mitigation_unit.py, the FROZEN pin every value in phase21_privacy_unit.json is computed from"
  - "21-03 — the five observed guard states and the measured no-undo result that make the ordering irrevocable"
  - "21-09 — _slot_forms_for, without which arm_spec('dp_n64') raises KeyError before a single row"
  - "21-10 — ATTRIBUTION_RULE, BIN_COMPOSITION_LABELS, ARTIFACTS, count_unaligned, count_aligned"
provides:
  - "scripts/phase21_unit_record.py::emit_privacy_unit / privacy_unit_document — SC1 + SC4's record"
  - "scripts/phase21_unit_record.py::emit_multiplicity / multiplicity_document — SC3's five labelled rows"
  - "scripts/phase21_unit_record.py::_measure_capacity / _measure_all — ONE corpus builder both emitters share"
  - "tests/test_phase21_unit_record.py — 11 tests: artifact schema, values-from-the-pin, refuse-to-rerun, A3's discharge, the pin discrepancy"
  - "results/phase21_privacy_unit.json — WRITTEN, NOT COMMITTED (awaiting the task-3 gate)"
  - "results/phase21_multiplicity.json — WRITTEN, NOT COMMITTED (awaiting the task-3 gate)"
affects:
  - "the task-3 continuation agent — owns the first results/phase21_* commit and the guard's vacuous->live transition"
  - "Phase 22 DPSGD-01 — the unit, q, N and delta the accountant consumes, and the multiplicity row shape"
tech-stack:
  added: []
  patterns:
    - "One measurement function feeding both artifacts, so two published numbers about the same corpus cannot disagree"
    - "An analytic expectation is a separately NAMED field beside the measured value, carrying BOTH candidate rules, never in place of the measurement"
    - "A documented claim that the measurement contradicts is recorded in the artifact WITH its denominators, not smoothed and not silently adopted"
    - "A frozen pre-registration whose figure answers a different question is RECORDED as a discrepancy; the fix is a dated continuation, never an edit"
    - "A discipline the guard does not check is a comment. If a docstring says 'tighter than the mechanism enforces', either enforce it or stop claiming it"
    - "A strengthened predicate is proved by running BOTH the old and the new against ONE identical state, and by showing it still ADMITS the legitimate case — a guard that refuses everything is as useless as one that admits everything"
key-files:
  created:
    - "tests/test_phase21_unit_record.py"
    - "results/phase21_privacy_unit.json (uncommitted)"
    - "results/phase21_multiplicity.json (uncommitted)"
  modified:
    - "scripts/phase21_unit_record.py"
    - "tests/test_phase20_prereg.py"
decisions:
  - "Replay tokens carry a sentinel fact id (65535) in the `replay-in-bin @1.0` row's fact map, and their draws are published as `replay_draws` BESIDE the per-fact summary rather than inside it. Crediting them to a fact inflates that fact; dropping them breaks the conservation law silently. The split surfaced the row's sharpest number: 854 of 1,600 draws (53.4%) bought no teaching at all."
  - "The fact-aligned rows measure ONE FULL LOT (steps == n_facts), which is what makes `mean == 1.0` the per-record multiplicity per optimiser step rather than an arbitrary multiple. The aligned draw is deterministic, so any multiple of n_facts gives steps/n_facts with spread 0 and says nothing new."
  - "`grad_accum_steps` is the OBSERVED micro-step count of one lot, asserted equal to the distinct fact indices the loader returned AND to n_facts. A declared value would restate SC2's claim instead of checking it."
  - "The row schema follows 21-10's `ROW_SCHEMA` constant (`steps`, `n_windows`), not the plan's prose (`max_steps`, `window_count`). The constant is pinned by an existing test; the prose is not."
  - "The 262.9437-vs-207.018 discrepancy is recorded in `pin_discrepancy` with both figures, both rules and the exact reconciliation. `scripts/mitigation_unit.py` is byte-unchanged (sha256 45f37e15...). Editing a closed pre-registration reddens the ancestry guard permanently and a delete-and-re-add cannot launder it."
metrics:
  duration: "~1h (tasks 1-2; task 3 blocked)"
  tasks_completed: 2
  tasks_total: 3
  completed: 2026-08-23
---

# Phase 21 Plan 11: The Privacy Unit and the Multiplicity Record Summary

Both `results/phase21_*` artifacts are **written, verified and deliberately UNCOMMITTED**. Task 3
is a `checkpoint:human-verify` with `gate="blocking"`, and this executor stopped there:
`git ls-files 'results/phase21_*'` is **empty**, and `git log --diff-filter=A -- 'results/phase21_*'`
is **empty** — the ordering `tests/test_phase20_prereg.py:185`'s `adds[-1]` makes irrevocable has
not yet been spent.

---

## What is written, and what it says

### `results/phase21_privacy_unit.json` (SC1 / SC4 — UNIT-01, UNIT-04, UNIT-05)

Every pinned value is **imported from `scripts/mitigation_unit.py` and computed at write time**;
none is retyped. `test_artifact_values_come_from_the_pin` recomputes all of them from the pin and
asserts equality, which is the check the ancestry guard cannot make — a transcription error inside
a correctly-ordered commit is invisible to ordering and fatal to the record (T-21-50).

| block | contents |
|---|---|
| `unit` | `PRIVACY_UNIT`, the `np.random.randint`-over-a-flat-bin rationale, and a POINTER to the sibling artifact instead of a restated multiplicity |
| `lot` | `q = 1`, `N = n_facts`, `replay_in_lot: true`, `replay_inside_privacy_n: false`, D-07's epsilon consequence with D-08's counterweight, and D-24/D-25's replay-volume record |
| `delta` | `1e-5`, ceiling `0.01`, and one row per capacity for the pinned literal AND the rejected `1/N**1.1` |
| `provenance` | `git_sha`, `written_utc`, `python`, `seed`, `pin_module`, `pin_sha256`, **`epsilon_computed: false`** |

The plan's acceptance command, run verbatim, prints exactly what it predicted:

```
$ python -c "...print(d['delta']['delta'], [r['rejected_delta_times_n'] for r in d['delta']['capacities']], d['provenance']['epsilon_computed'])"
1e-05 [0.8122523963562354, 0.6597539553864469] False
```

`pin_sha256` = `45f37e152bb4035667b804c1463431b3f12fa5096c47de32b1dc27abbe000473` — equal to 21-01's
frozen value. That is a **second, independent witness to the freeze**, running on file bytes rather
than git history, so an edit to the pin goes red locally without waiting for an artifact commit.

### `results/phase21_multiplicity.json` (SC3 / UNIT-03, D-26)

Five labelled rows, measured at `SEED = 1337`, `MAX_STEPS = 200`, `BATCH_SIZE = 8`,
`block_size = 256`, on bins built under a temporary directory — no `arm_outputs` path was touched
and `git status --porcelain data/` is **empty**.

| `bin_composition` | n | draws | bin tokens | min | max | mean | spread |
|---|---|---|---|---|---|---|---|
| `replay-in-bin @1.0` | 8 | 1,600 | 15,162 | 79 | 109 | 93.25 | 30 |
| `facts-only (D-10)` | 8 | 1,600 | 7,581 | **143** | **229** | 200.00 | **86** |
| `fact-aligned (D-01, D-05)` | 8 | 8 | 8,449 | 1 | 1 | 1.00 | 0 |
| `facts-only (D-10)` | 64 | 1,600 | 72,093 | 14 | 36 | 25.00 | 22 |
| `fact-aligned (D-01, D-05)` | 64 | 64 | 80,897 | 1 | 1 | 1.00 | 0 |

**The `replay-in-bin @1.0` row is REAL, not synthetic.** The plan anticipated
`data/dialog_train.bin` being absent in a worktree and permitted a labelled synthetic fallback
(T-21-53). It was not needed: the gitignored PersonaChat bins were copied in from the main checkout,
so the row is the legacy `n_facts=None` sizing over the actual replay corpus. No row in this
artifact is synthetic and none carries a synthetic label.

**Three independent reproductions, each from a different route than the number it matches:**

1. The n=8 `facts-only` counts are `[210, 197, 203, 221, 180, 229, 217, 143]` — **identical to
   21-10's measured row**, reached here through the real `build_bins` packer and a synthesised fact
   map rather than 21-10's per-fact flat packing.
2. The n=8 geometry is `windows_per_fact (4,4,4,4,4,5,4,4)`, **33 windows, 867 pad tokens,
   10.2616%** — D-01's measured table, exactly, with no divergence to publish.
3. `_analytic_expectations` reproduces **both** of the frozen pin's analytic figures from the
   observed geometry: `262.9437` on the facts-only bin and `129.205` on the replay-in-bin bin
   (the pin states 262.94 and 129.21).

### Every row carries its denominator, and the analytic number never replaces the measurement

Each row holds all 13 `ROW_SCHEMA` keys plus `analytic_expectation` (14 required), and the
analytic field names **both** candidate rules with an explicit
`which_one_matches_this_row: "first_token_rule"`:

| row | measured mean | analytic (first-token) | analytic (overlap — REJECTED rule) |
|---|---|---|---|
| `replay-in-bin @1.0` | 93.25 | 101.7243 | 129.205 |
| `facts-only (D-10)` n=8 | 200.00 | **207.018** | **262.9437** |
| `facts-only (D-10)` n=64 | 25.00 | 25.0894 | — |

`test_analytic_expectation_sits_beside_the_measurement_never_in_place_of_it` asserts
`row["mean"] != analytic["first_token_rule"]` on every unaligned row. That is a real discriminator,
not decoration: on the n=8 facts-only row the measured mean is the conservation-pinned `200.0`
while the closed form is `207.018`, so an emitter that had written the analytic number into `mean`
fails immediately.

---

## THE CENTRAL FINDING: A3's assumed n=64 geometry is FALSE, by 19.7%

`21-RESEARCH.md` assumption A3 — marked `[ASSUMED — depends on values not yet minted]` — estimated
the n=64 corpus at **~264 windows** from "56 filler facts at ~4 windows each". The plan required it
be discharged by measurement and forbade adjusting the corpus to hit it.

**Observed: 316 windows. Divergence +52 windows, +19.70%.**

| | facts | windows | windows/fact |
|---|---|---|---|
| locked (n=8) | 8 | 33 | 4.125 |
| filler | 56 | **283** | **5.054** |
| total (n=64) | 64 | **316** | 4.938 |

The filler facts render **longer** than the locked ones, so the ~4-each estimate under-counts them.
The corpus was not touched; the measurement is published as taken, and
`test_corpus_geometry_is_observed_and_discharges_a3` asserts `holds is False` with a note to check
for back-fitting if it ever flips.

Two derived corrections follow from the same measurement:

- **21-09's `dp_n64` "282 windows @256" and this plan's 316 are both correct and are different
  quantities.** 282 is the FLAT bin's window count (`72,093 // 256`); 316 is the sum of the RAGGED
  per-fact ceilings, which is the number `grad_accum_steps = n_facts` accounting actually runs on.
  Both are recorded with their formulas so the pair cannot be read as a contradiction.
- The n=64 padded aligned bin is **80,897 tokens**, not the `8 x 8,449 = 67,592` that linear
  scaling from n=8 predicts.

## SECOND FINDING: `teach_persona.py:162-163`'s cross-capacity replay-share claim is FALSE

That comment states: *"The share holds across capacities for free: 49.90% at n=64, because both
sides scale with `n_facts`. Nothing re-tunes."*

Both sides do **not** scale with `n_facts`. Replay does, exactly (`4 * n_facts * block_size`); the
padded teaching bin does not, for the reason above. Recomputed on the observed bins, with the
denominator stated (`replay / (replay + padded_bin)`):

| windows/fact | n=8 | n=64 |
|---|---|---|
| 3 | 42.1024% | 37.7950% |
| **4 (PINNED)** | **49.2278%** | **44.7549%** |
| 5 | 54.7916% | 50.3142% |

**All three n=8 rows reproduce D-24's documented table exactly** (42.11 / 49.23 / 54.79), which is
what validates the measurement before it is used to contradict anything. The n=64 half does not:
the pinned constant measures **44.7549%**, not 49.90%. The documented figure does not even follow
from its own stated reason — under the linear premise the share would be *unchanged* at 49.2278%.

**This does NOT reopen D-24, and nothing was changed.** `REPLAY_WINDOWS_PER_FACT = 4` is a locked
decision, pinned by `tests/test_phase21_replay_volume.py`, chosen on the n=8 table that reproduces
exactly. What is corrected is a stated *consequence* at the other capacity. It is recorded in the
artifact under `d24_candidate_table_reproduced` with every denominator, including the uncomfortable
part: at n=64 the table's own "closest to 50%" criterion ranks 5 windows (50.31%) ahead of the
pinned 4 (44.75%). `scripts/teach_persona.py` is **not** in this plan's `files_modified` and was not
touched.

## THIRD FINDING: over half the replay-in-bin budget bought no teaching

Splitting the replay sentinel out of the per-fact summary surfaced a number the plan did not ask
for and that no source document states: at `replay_ratio = 1.0`, **854 of 1,600 draws (53.4%)**
started inside the public replay prefix and touched no fact at all. Under an example-level
accounting those draws are indistinguishable from the ones that touched a privacy record — which is
UNIT-01's complaint stated as a measured fraction rather than as an argument.

The D-10 interaction the plan did ask for is confirmed and quantified: moving replay out of the bin
raises the unaligned per-fact multiplicity from **93.25 to 200.00**, a factor of **2.1448**. A
decision taken purely for honest accounting made the unaligned number *worse*, which strengthens
UNIT-01 rather than weakening it — and it is only visible because both numbers were measured.

---

## The 262.9437-vs-207.018 discrepancy: RECORDED, not resolved

The frozen pin's `PRIVACY_UNIT_ARITHMETIC` computes `1,600 * (947.625 + 256) / 7,324 = 262.9437`.
That `+ 256` numerator is the count of start offsets from which a window **touches** a fact — the
**overlap** rule, which is exactly the alternative `ATTRIBUTION_RULE = "first-token-owns-draw"`
rejects. Under the pinned rule the same geometry gives `207.018`, and they reconcile exactly:

```
262.9437 - 1600 * 256 / 7324 = 262.9437 - 55.9257 = 207.018
```

`pin_discrepancy` records both figures, both formulas, the gap, the reconciliation, the
conservation-pinned mean (`1600 / 8 = 200.0`, which carries no information about the corpus), and
the sentence that matters most: **`how_a_correction_would_be_made: scripts/_addendum.py — a dated
continuation. NEVER an edit.`**

`scripts/mitigation_unit.py` is **byte-unchanged**: `git diff --exit-code` returns 0 and
`shasum -a 256` gives `45f37e15…000473`.

---

## Plan vs Code Fidelity

Six mismatches, reported with evidence. `21-11-PLAN.md` was **not** amended — plans are records.

**1. Every line anchor in `<interfaces>` and `<read_first>` is stale.** The seventh consecutive plan
in this phase for which this holds.

| symbol | plan says | measured |
|---|---|---|
| `_assert_ordering_holds` | `test_phase20_prereg.py:121-183` | **`:149-211`** |
| `adds[-1]` (the earliest add) | `:157` | **`:185`** |
| `checked == n x m` product | `:166` | **`:194`** |
| `bool(checked) == bool(...)` equivalence | `:178` | **`:206`** |
| `refuse_if_exists` | `teach_persona.py:236-244` | **`:323`** (21-10 measured `:311`; 21-09's `_slot_forms_for` moved it again) |
| `get_batch_memmap_masked` draw | `data.py:117` | `:117` — **verifies** |

Everything was resolved by symbol name; nothing was written against a line number.

**A consequence worth stating separately:** `scripts/mitigation_unit.py`'s own docstring cites
`:143` and `:157` for those same two sites, and both are now stale by the same drift. **That file is
FROZEN and was not corrected.** A stale anchor inside a closed pre-registration is exactly the
category of defect that must wait for a dated continuation.

**2. The plan's row-schema key names contradict the code's pinned constant.** Task 2 asks for
`max_steps` and `window_count`; 21-10's `ROW_SCHEMA` — pinned by
`test_phase21_multiplicity.py::test_row_carries_its_denominator` — spells them `steps` and
`n_windows`. The constant was followed. The plan's "14 schema keys" reconciles exactly:
`len(ROW_SCHEMA) == 13`, plus `analytic_expectation` = 14, and the test asserts that arithmetic
rather than a literal.

**3. `.venv/bin/python` does not exist inside a worktree.** Every acceptance criterion and the whole
`<verification>` block spell it relatively. Confirmed again (21-09 measured this first); all
commands ran through `/Users/juliorcoelho/PersonaCore/.venv/bin/python` with the editable install
repointed at this worktree.

**4. The synthetic-replay fallback was not needed.** The plan permits labelling the
`replay-in-bin @1.0` row synthetic if `data/dialog_train.bin` is absent. It is absent in a worktree
(`data/` is gitignored), but the real bins were copied in from the main checkout, so the row is a
genuine measurement. Recorded because "no synthetic row" is a stronger statement than "the fallback
was available".

**5. The plan's Phase 20 reference number VERIFIES — the first `<interfaces>` claim in this phase to
do so.** It states "9 pin commits x 3 tracked artifacts = `checked = 27`". Measured:
`git log --format=%H -- scripts/mitigation_gate.py` gives **9**, and `git ls-files 'results/phase20_*'`
gives **3**. The transition this plan is about has genuinely been carried once in production here.

**6. `21-VALIDATION.md`'s "1.86s / 21 tests" for `test_phase20_prereg.py` is now ACCURATE.**
21-01 recorded that criterion as unsatisfiable (18 collected at the time). Measured now:
**21 passed in 1.91s**. The figure became true as 21-01 and 21-03 added tests. Recorded so the next
reader does not re-open 21-01's finding as a live defect.

Every documented `-k` selector used here was checked for non-zero collection before being trusted:
`-k phase21` on `test_phase20_prereg.py` reports **3 passed, 18 deselected** — it selects.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — Missing critical record] The `replay-in-bin @1.0` row needed an attribution for
draws that belong to no fact**

- **Found during:** Task 2, designing the row.
- **Issue:** `count_unaligned` attributes a draw by `fact_ids[start]`, and a flat replay-prefixed
  bin has `replay_tokens` positions owned by no privacy record. The plan specifies the row but not
  what a replay-start draw is credited to. Both silent answers are wrong: crediting them to a fact
  inflates that fact's multiplicity, and dropping them makes `sum(counts) < total_draws` — the
  conservation law failing quietly on the one row where it is easiest to miss.
- **Fix:** a `REPLAY_FACT_ID = 65535` sentinel in the synthesised fact map, split back out by
  `_split_replay_sentinel`, which recomputes min/max/mean/spread over the facts alone and publishes
  `replay_draws`, `draws_landing_on_a_fact` and the exact conservation law
  (`draws_landing_on_a_fact + replay_draws == total_draws`) it satisfies. It raises if the law
  fails.
- **Commit:** `bc5f5f0`

**2. [Rule 2 — Missing critical record] The n=64 replay share contradicts a documented claim, and
the artifact said so only implicitly**

- **Found during:** Task 1, on the first emission.
- **Issue:** The artifact published `44.7549%` beside a comment in `teach_persona.py` asserting
  `49.90%`, with nothing connecting them. That is failure mode (a) the plan's own risk section
  names — a number that is plausible but that a reader will silently reconcile with the wrong
  documented figure.
- **Fix:** `_d24_candidate_table` recomputes D-24's whole 3/4/5-window candidate table at BOTH
  capacities on the observed bins, quotes the documented claim verbatim, records
  `documented_n64_claim_holds: false` with the reason the premise fails, and states explicitly that
  D-24 is locked and is not reopened.
- **Commit:** `17b3c85`

**3. [Rule 2 — Missing critical functionality] `grad_accum_steps` was declarable rather than
observed**

- **Found during:** Task 2.
- **Issue:** Writing `"grad_accum_steps": n_facts` restates SC2's claim instead of checking it. The
  plan explicitly asks for the observed micro-step count.
- **Fix:** `_corpus_geometry` derives it from the aligned row's observed counts and raises unless
  `len(distinct records) == sum(counts) == n_facts`. `grad_accum_steps_source` records that it is
  observed.
- **Commit:** `bc5f5f0`

No Rule 4 (architectural) decision arose. **No package was installed.**

### Deliberate departures, with reasons

- **The gitignored PersonaChat bins were copied into the worktree** (`data/` is fully gitignored;
  `git status --porcelain data/` is empty and stayed empty). This turns the plan's permitted
  synthetic row into a real one.
- **`emit_privacy_unit` runs the corpus measurement too.** The plan puts the observed padded-bin
  share in task 1's `lot` block but the measurement in task 2. Both emitters call the same
  `_measure_all`, so the two artifacts cannot publish disagreeing bin sizes.

---

## Task 3: STOPPED at the blocking checkpoint

`<task type="checkpoint:human-verify" gate="blocking">`. Nothing under `results/phase21_*` was
staged or committed. The five checks the plan requires before pausing, all run and recorded:

| # | check | result |
|---|---|---|
| 1 | `git log --format=%H -- scripts/mitigation_unit.py` | **1 commit**: `8d3beb446f08327f9df242420b900f15baf670b3` |
| 2 | `git merge-base --is-ancestor 8d3beb4 HEAD; echo $?` | **`0`** |
| 3 | `git ls-files 'results/phase21_*'` | **empty** |
| 3b | `git log --diff-filter=A --format=%H -- 'results/phase21_*'` | **empty** — no such path was ever added |
| 4 | `git status --porcelain results/` | exactly the two artifacts, both `??` (untracked) |
| 5 | `pytest -q tests/test_phase20_prereg.py` | **21 passed in 1.91s** — armed and green first |

**Predicted `checked` after the artifact commit: `1 pin commit x 2 tracked artifacts = 2`**, both
sides non-zero, which is what turns `:206`'s equivalence from vacuous to live.

**The reflexivity gap is now CLOSED — see the next section.** It was measured, the operator refused
to accept it as a recorded discipline, and the mechanism now enforces it.

**Not applied, awaiting approval:** the `test_phase21_has_no_artifact_yet_so_the_arming_is_honest`
→ `test_phase21_guard_is_now_live` swap. It is **RED until the artifacts are committed** and
therefore belongs in the artifact commit itself — see "The plan's STEP 2 is unsatisfiable" below.

---

## Gate review round 2: the reflexivity gap, CLOSED and proved by mutation

The operator refused to approve the artifact commit while the guard was a pure
`merge-base --is-ancestor(pin, artifact_first_add)`, on the ground that a discipline the guard does
not check is a comment. `_assert_ordering_holds` now carries the conjunction:

```
prereg != first_add   AND   merge-base --is-ancestor(prereg, first_add)
```

### The premise was tested before the fix was written, and it is TRUE

Three throwaway repos, literal commands and literal exit codes. **Nothing touched the real
history.**

```
STATE A — pin and artifact in the SAME commit
pin commit          = bbbe9af4888a09e81779be7293f5362e0240d933
artifact first add  = bbbe9af4888a09e81779be7293f5362e0240d933
same commit?          YES

--- OLD predicate: git merge-base --is-ancestor $PIN $ADD
    exit code = 0    <-- ADMITS the state D-20 forbids   ... THE RED

--- NEW predicate: $PIN != $ADD AND is-ancestor($PIN,$ADD)
    exit code = 1    <-- REFUSES                          ... THE GREEN

STATE B — the LEGITIMATE ordering (pin strictly first)
pin commit          = 752485179daa05c1e89c999b05e1a183e784757b
artifact first add  = 443fb5863eeb18915d056aca09773149feeb4647
same commit?          NO
--- NEW predicate
    exit code = 0    <-- ADMITS: the guard is not vacuous in the other direction

STATE C — artifact BEFORE pin (the original defect the guard already caught)
--- OLD predicate  exit code = 1
--- NEW predicate  exit code = 1    <-- the strengthening does not weaken the existing check
```

### It is a COMMITTED FIXTURE, not a one-off observation

`tests/test_phase20_prereg.py::test_a_same_commit_pin_and_artifact_is_refused` rebuilds the
same-commit state under `tmp_path` and runs **both** predicates against that one identical state.
The old predicate's exit code is **computed** with `check=False` and asserted to be `0` — the wrong
answer is executed, never described — so if reflexivity ever stops admitting a same-commit pin the
test reports that as a finding instead of quietly becoming decoration. The legitimate ordering is
driven through the same helper and must pass.

```
$ pytest -q tests/test_phase20_prereg.py -k same_commit
1 passed, 21 deselected in 0.41s
```

### It does not break the live guards

The strengthening applies to Phase 20's committed history too, so it was measured there **before**
being committed: **9 pin commits x 3 tracked artifacts = 27 pairs, of which ZERO are same-commit.**

```
$ pytest -q tests/test_phase20_prereg.py
22 passed in 2.35s
$ pytest -q tests/test_phase20_prereg.py tests/test_phase21_unit_pin.py \
    tests/test_phase21_unit_record.py tests/test_phase21_multiplicity.py \
    tests/test_phase16_prereg.py tests/test_phase18_prereg.py
93 passed in 19.15s
```

Three docstrings recorded the old gap as deliberate (`:262`, `:389`, `:559` before the edit); all
three were corrected in the same commit rather than left asserting a property the code no longer
has. `scripts/mitigation_unit.py` is byte-unchanged.

**Commit `d32b51a`.** `git ls-files 'results/phase21_*'` remained EMPTY throughout.

## FINDING: the plan's STEP 1 → STEP 2 → STEP 3 sequence is unsatisfiable

The plan's STEP 2 says *"commit the test edit ALONE first, and confirm it is GREEN."* **Measured, it
is RED**, and it cannot be otherwise:

```
$ pytest -q tests/test_phase20_prereg.py          # with the full step-1 edit applied
E  AssertionError: no results/phase21_* artifact is tracked, so the ancestry guard is
   still vacuous. This test asserts the guard has gone LIVE; if the artifacts are not
   committed yet it is being run one commit too early.
E  assert []
FAILED tests/test_phase20_prereg.py::test_phase21_guard_is_now_live
1 failed, 21 passed in 2.34s
```

`test_phase21_guard_is_now_live` asserts `checked` is non-zero, and `checked` is
`len(pins) * len(tracked_artifacts)`. While `results/phase21_*` is uncommitted `tracked_artifacts`
is `[]`, so `checked` is 0 **by construction**. The test can only be green *after* the artifacts are
committed — which is exactly the commit STEP 2 was supposed to precede.

**The step-1 edit is two changes with different commitability, and separating them is the fix:**

| half | state with artifacts uncommitted | disposition |
|---|---|---|
| the strict-ancestor strengthening + its mutation proof | **GREEN** (22 passed) | **committed** as `d32b51a` — and being a strict ancestor of the artifact commit is precisely the arm-then-write discipline STEP 2 was reaching for |
| the `has_no_artifact_yet` → `guard_is_now_live` swap | **RED** (1 failed, 21 passed) | **not committed.** It belongs in the SAME commit as the artifacts |

This is a finding of the same class as the other ten this phase has produced, and it is reported
rather than engineered around. The corrected sequence for the continuation agent is:

1. ~~commit the test edit alone~~ — **impossible**; the guard-side half that *can* be committed
   alone already is (`d32b51a`).
2. `git add results/phase21_privacy_unit.json results/phase21_multiplicity.json` **together with**
   the `guard_is_now_live` swap, in one commit. The artifacts and the test that observes them go
   live in the same instant, which is what `:206`'s equivalence demands.

**The exact swap, recorded here so it survives the worktree being removed** — replace
`test_phase21_has_no_artifact_yet_so_the_arming_is_honest` with:

```python
def test_phase21_guard_is_now_live():
    """The RECORDED TRANSITION from "armed, nothing to watch" to "armed and watching"."""
    tracked = _git("ls-files", "results/phase21_*").split()
    assert tracked, (
        "no results/phase21_* artifact is tracked, so the ancestry guard is still vacuous. "
        "This test asserts the guard has gone LIVE; if the artifacts are not committed yet "
        "it is being run one commit too early."
    )
    pins = _git("log", "--format=%H", "--", PHASE21_PREREG_ARTIFACT).split()
    _assert_ordering_holds(
        root=_ROOT,
        prereg_artifact=PHASE21_PREREG_ARTIFACT,
        artifact_glob="results/phase21_*",
        globs=V4_ARTIFACT_GLOBS,
    )
    assert len(pins) * len(tracked) > 0
```

Expected after that commit: `checked = 1 pin x 2 artifacts = 2`, both sides non-zero.

## Requirements — deliberately NOT marked complete

`UNIT-01`, `UNIT-03`, `UNIT-04`, `UNIT-05`, `UNIT-06` are this plan's `requirements:` frontmatter
and **none is marked complete**; `REQUIREMENTS.md` was not modified. Every one of them is satisfied
by a **committed** `results/phase21_*` artifact, and neither artifact is committed yet. Marking them
complete against an untracked file would claim a record that does not exist in the history — the
same substitution UNIT-03 exists to refuse.

## Known Stubs

**One, and it is the plan's design.** Both artifacts exist on disk and neither is tracked. This is
the `Known Stubs` entry 21-10 opened (`refuse_existing_artifacts` wired to nothing) now half-closed:
the emitters are fully implemented and both have run to completion against the real corpora. The
remaining step is a commit that only a human may authorise, because `adds[-1]` makes its ordering
irrevocable. **No stub prevents this plan's goal** — the goal is blocked on a gate, not on missing
code.

## Threat Flags

None. This plan adds no network endpoint, no auth path and no new file-access pattern. It reads the
frozen tokenizer, the gitignored PersonaChat bins, and bins it wrote itself under a temporary
directory; it writes two files under `results/`. No `subprocess` call is added.

Register dispositions, all `mitigate`: **T-21-03** (artifact before the pin — ancestry verified,
exit 0, and nothing staged), **T-21-06** (laundering — impossible, and the checkpoint states it),
**T-21-50** (artifact drifting from the pin — `test_artifact_values_come_from_the_pin` plus the
`pin_sha256` witness), **T-21-51** (analytic published as measured — `analytic_expectation` is a
separate field carrying both rules, asserted to differ from `mean`), **T-21-52** (A3 published as a
measurement — observed 316 vs assumed 264, `holds: false`), **T-21-53** (a row silently omitted —
all five present, none synthetic), **T-21-54** (an epsilon with no basis — `epsilon_computed: false`,
asserted as an identity), **T-21-11** (supply chain — zero package installs). **T-21-49** (the guard
staying vacuous) is the checkpoint's own subject and is **not yet discharged**.

## Commits

| Commit | Task | Content |
|---|---|---|
| `17b3c85` | 1 | the privacy-unit emitter, `_measure_capacity`/`_measure_all`, the D-24 candidate table recomputed at both capacities, 4 tests |
| `bc5f5f0` | 2 | the multiplicity emitter, the replay sentinel split, A3's discharge, the pin-discrepancy record, the findings block, 7 tests |
| `b41de0f` | — | this SUMMARY (first revision, at the gate) |
| `d32b51a` | 3 (gate round 2) | the strict-ancestor strengthening + `test_a_same_commit_pin_and_artifact_is_refused`, and the three corrected reflexivity docstrings |

`tests/test_phase20_prereg.py` is a third file this plan modified, beyond the two its
`files_modified` frontmatter declares. It is declared in the plan's **task-3 `<files>`** block, so
it is in scope — but the frontmatter is narrower than the tasks, which is worth noting.
`git diff --diff-filter=D --name-only fa97b66 HEAD` is empty — zero deletions.

## Verification

| Check | Result |
|---|---|
| `pytest -q tests/test_phase21_unit_record.py` | **11 passed** |
| `... tests/test_phase21_unit_pin.py tests/test_phase20_prereg.py tests/test_phase21_replay_volume.py tests/test_phase21_aligned_bins.py tests/test_phase21_aligned_loader.py tests/test_phase21_sc5.py` | **87 passed in 11.87s** |
| `pytest -q tests/test_phase21_multiplicity.py` (21-10's instrument) | **17 passed**, unchanged |
| `pytest -q tests/test_phase20_prereg.py -k phase21` | **3 passed, 18 deselected** — the selector selects |
| **Full suite** | **975 passed, 7 skipped in 191.55s**, exit 0 (974 before the gate-round-2 strengthening added 1 test) |
| `git diff --exit-code` on the frozen paths | **0** — `mitigation_unit.py`, `mitigation_gate.py`, `phase18_extraction.py`, `phase16_recall_sample.json` |
| `shasum -a 256 scripts/mitigation_unit.py` | `45f37e152bb4035667b804c1463431b3f12fa5096c47de32b1dc27abbe000473` — 21-01's frozen value |
| `git status --porcelain data/` | **empty** |
| `git ls-files 'results/phase21_*'` | **empty** |
| `ruff check . && ruff format --check .` | All checks passed · 188 files formatted |
| `.planning/STATE.md` / `ROADMAP.md` / `REQUIREMENTS.md` | byte-unchanged (worktree mode — the orchestrator owns them) |

**The full-suite count reconciles exactly.** The prompt's base figure is `969 passed, 1 skipped` on
the main checkout; six of those tests skip in a worktree for want of gitignored artifacts
(checkpoints, adapters, the slim artifact), so the worktree baseline at `fa97b66` is
**963 passed, 7 skipped** — the number 21-09 measured. This plan adds **11 tests** and
`963 + 11 = 974`, and the gate-round-2 strengthening adds
`test_a_same_commit_pin_and_artifact_is_refused` for **975**. Zero failures, and the skip count is
unchanged: copying the PersonaChat replay bins in un-skipped nothing, because none of the six skips
is gated on `data/`.

## Self-Check

- `scripts/phase21_unit_record.py` — FOUND (modified)
- `tests/test_phase21_unit_record.py` — FOUND
- `results/phase21_privacy_unit.json` — FOUND on disk, **untracked by design**
- `results/phase21_multiplicity.json` — FOUND on disk, **untracked by design**
- `17b3c85`, `bc5f5f0` — both FOUND in `git log fa97b66..HEAD`
- The two artifacts are gitignored-adjacent but NOT gitignored; they are deliberately left
  untracked in the worktree and must be preserved for the continuation agent.
