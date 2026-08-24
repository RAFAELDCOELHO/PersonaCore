---
phase: 21
status: issues_found
depth: standard
reviewed: 2026-08-24
critical: 2
warning: 7
info: 4
files_reviewed: 19
files_reviewed_list:
  - scripts/mitigation_unit.py
  - scripts/phase14_factset.py
  - scripts/phase21_filler.py
  - scripts/phase21_golden_capture.py
  - scripts/phase21_unit_record.py
  - scripts/teach_persona.py
  - src/personacore/training/data.py
  - src/personacore/training/loop.py
  - README.md
  - tests/test_phase20_prereg.py
  - tests/test_phase21_aligned_bins.py
  - tests/test_phase21_aligned_loader.py
  - tests/test_phase21_filler.py
  - tests/test_phase21_multiplicity.py
  - tests/test_phase21_replay_volume.py
  - tests/test_phase21_sc5.py
  - tests/test_phase21_unit_pin.py
  - tests/test_phase21_unit_record.py
  - results/phase21_privacy_unit.json
  - results/phase21_multiplicity.json
---

# Phase 21: Code Review Report

**Reviewed:** 2026-08-24
**Depth:** standard (per-file, Python-specific, with targeted empirical probes)
**Files Reviewed:** 19 source files + 2 committed artifacts
**Status:** issues_found

## Summary

The phase's central mechanisms hold up under adversarial reading. I specifically tried to break
the four things the brief flagged as highest-value and **three of them survived**:

- `fact_window_impurities` defaults to `space="input"`, there is no union mode, and a repo-wide
  audit of every `space=` call site (7 sites) confirms **no consumer overrides the default into
  vacuity** — the only `space="target"` uses are the deliberate boundary counts.
- Every `-k` selector documented for Phase 21 was executed against the live suite; 25 of 26
  select non-zero tests (the 26th is a known, already-recorded dead selector, IN-03).
- No `shell=True`, no `eval`, no unquoted interpolation, no `cwd=_ROOT` mutation anywhere in the
  new guard tests; every throwaway-repo fixture is `tmp_path`-confined.
- `ruff check` clean, 118/118 Phase-21 tests green, no debug artifacts, no bare `except`.

What did **not** survive is the boundary handling, and the provenance of the two artifacts the
phase exists to produce. Two Critical findings:

1. **The fact-aligned loader never enforces the whole-bin length contract at draw time.** I ran
   the adversary: with the label-shift tail removed from all three bins, the loader silently
   serves the last fact **half its windows** and raises nothing. Every neighbouring guard
   (three-bin 1:1, input-space purity, `n_facts`, span contiguity) passes. This changes what a
   privacy record *is* — the exact invariant the phase was built to make structurally true.
2. **Both committed artifacts record a `provenance.git_sha` under which their own emitter does
   not exist.** Verified by `git cat-file`. The phase invented the right guard for this in 21-02
   (`_refuse_if_dirty`) and did not apply it to the artifact writer.

Beyond those, one published validation claim is a hardcoded `True` that is measurably false at the
precision it claims (WR-01), the two new DP capacity arms are CLI-reachable but build the *old*
flat bin (WR-02), and one headline "finding" in the multiplicity artifact is an arithmetic
identity the same artifact elsewhere warns readers carries no information (WR-05).

Findings that the phase's own SUMMARYs already record as deliberate — the `question_bank=` drop,
the `replay_ratio` AMBIGUOUS classification, the 262.9437/207.018 reconciliation, the frozen pin's
immutability — are **not** re-flagged as defects. Where I do cite the frozen pin, the finding is
about a claim the pin makes that measurement contradicts, and the fix in every case is
`scripts/_addendum.py`, never an edit.

---

## Critical Issues

### CR-01: `get_batch_fact_aligned` silently serves a truncated privacy record

**File:** `src/personacore/training/data.py:331-353` (missing check), demonstrated at `:339-350`

**Issue:** The loader checks the three bins are 1:1 (`:331`), the distinct-owner count against
`n_facts` (`:341`), span contiguity (via `fact_window_span`), and input-space purity **on the
drawn slice only** (`:353`). It never checks the whole-bin `n_windows * block_size + 1` length
contract. The docstring at `:292-298` argues this is safe because `fact_window_impurities` owns
that contract — but the slice handed to it is always constructed as `facts[start : start + k*B + 1]`
from a `block_size`-aligned `start`, so its remainder is **0 by construction** and the whole-bin
contract is never reached.

Consequence: a bin whose length is `n*B` (label-shift tail lost) rather than `n*B + 1` passes
every guard, and `n_windows = (len - 1) // block_size` silently drops the final window. The fact
that owns it gets a shorter batch. Under D-03 the loss is a **mean over the record's windows**, so
that record's gradient is computed over 3 windows where the packer wrote 4 — a different privacy
record than the one accounted for, with no error surfaced. `grad_accum_steps = n_facts` still reads
true, so nothing downstream notices.

Measured, not argued (`block_size=4`, 3 facts, windows `(2,1,2)`):

```
GOOD  step 2 fact 2 windows 2
no-tail bin length: 20 = n_windows*B exactly (tail gone)
NOTAIL step 2 fact 2 windows 1   <-- NO RAISE
```

21-06's N2 adversary truncates only the *fact* bin, so it is caught by the 1:1 check. Truncating
all three — the shape a half-written or interrupted build leaves — is uncovered by any test.
The docstring's claim at `:314-315` ("Every failure raises `ValueError` in the `:112-116`
register") is false for this class.

**Fix:** assert the contract on the whole bin before deriving `n_windows`, reusing the one
predicate rather than adding a second copy of the arithmetic:

```python
    if (len(facts) - 1) % block_size != 0:
        raise ValueError(
            f"the aligned bins are {len(facts)} elements, which is not "
            f"n_windows * block_size + 1 for block_size={block_size}: "
            f"(len - 1) % block_size == {(len(facts) - 1) % block_size}, expected 0. The "
            "trailing +1 is the LABEL-SHIFT TAIL; a bin missing it silently drops the last "
            "fact's final window, so that micro-step is not the privacy record that was packed."
        )
    n_windows = (len(facts) - 1) // block_size
```

Add the paired adversary to `tests/test_phase21_aligned_loader.py` (N7: truncate **all three**
bins by one, assert the raise names the remainder), since the existing N1-N6 set provably cannot
see it.

---

### CR-02: both committed artifacts carry a `git_sha` under which their emitter does not exist

**File:** `results/phase21_privacy_unit.json` (`provenance.git_sha`),
`results/phase21_multiplicity.json` (`provenance.git_sha`), written by
`scripts/phase21_unit_record.py:612-636`

**Issue:** `_provenance()` records `git_sha()` — HEAD at *write* time. Both emitters were run from
a dirty working tree, one commit ahead of the recorded SHA. Verified mechanically:

| artifact | recorded `git_sha` | emitter present at that commit? |
|---|---|---|
| `phase21_privacy_unit.json` | `fa97b6667043ae0aca287dab64741bfb99029522` | `grep -c emit_privacy_unit` → **0** |
| `phase21_multiplicity.json` | `17b3c8568ece86cb2d69a7934683e681a796d3c4` | `grep -c emit_multiplicity` → **0** |

`emit_privacy_unit` first appears at `17b3c85`; `emit_multiplicity` first appears at `bc5f5f0`.
Neither artifact can be regenerated from the SHA it names. This is a false provenance record on
two permanently-committed, ancestry-guarded files, in a project whose stated reproducibility
guarantee (CLAUDE.md, QA-02) is exactly "seed + git SHA + config-embedded". The ancestry guard
cannot see this — it checks commit *ordering*, not whether the recorded SHA can produce the bytes.

The phase built the correct guard for this class in 21-02 and did not reuse it:
`scripts/phase21_golden_capture.py:122-136` refuses to run on a dirty tree, at module scope,
*before* the imports it would otherwise capture — with a docstring explaining that a capture taken
after the edit "turns every assertion downstream into a tautology". `phase21_unit_record.py` has
no equivalent.

**Fix:** two parts. (a) Add the refusal to the emitter so this cannot recur:

```python
def _provenance(**extra):
    dirty = tp._git("status", "--porcelain") if hasattr(tp, "_git") else subprocess.run(
        ("git", "status", "--porcelain"), cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    if dirty:
        raise SystemExit(
            "[phase21_unit_record] REFUSING to emit: the working tree is dirty, so git_sha() "
            f"would name a commit that cannot reproduce this artifact.\n{dirty}"
        )
    ...
```

and pin it with a test that asserts `git cat-file -p <recorded_sha>:scripts/phase21_unit_record.py`
contains the emitter name. (b) The two committed artifacts are immutable — record the correction
via `scripts/_addendum.py` as a dated continuation naming the true producing commits (`17b3c85`
and `bc5f5f0`), so a future reader is not sent to a tree that has no emitter.

---

## Warnings

### WR-01: `n8_rows_reproduce_the_documented_table: true` is a hardcoded literal, and it is false

**File:** `scripts/phase21_unit_record.py:697-698`

**Issue:** The field is the Python literal `True`. Nothing in the emitter or in any test compares
the computed `share_of_the_combined_lot` values against the hand-typed `documented_n8_table` one
line below (`grep -rn "n8_rows_reproduce" tests/` → no matches). The function's own docstring at
`:661-665` calls this "**A validation of this measurement against a documented one**" and states
that all three n=8 rows "reproduce here to four decimals from the OBSERVED padded bin". That is
the step that licenses the artifact's *other*, load-bearing claim
(`documented_n64_claim_holds: false`).

Measured, it does not hold for the 3-window row:

```
w=3  artifact(padded 8449) = 42.102378%  ->  0.4210     documented: 0.4211
w=4  artifact             = 49.227811%  ->  0.4923     documented: 0.4923   ok
w=5  artifact             = 54.791589%  ->  0.5479     documented: 0.5479   ok
```

The cause is real and worth recording rather than rounding away: D-24's table used the padded bin
**without** the label-shift tail (`8448` → 42.105% → 42.11%); the artifact uses `8449` (with it).
One token of denominator flips the published figure in its last digit.

**Fix:** compute the boolean instead of asserting it, and state the tolerance:

```python
        "n8_rows_reproduce_the_documented_table": all(
            round(w * 8 * BLOCK_SIZE / (w * 8 * BLOCK_SIZE + padded[8]), 4) == documented[str(w)]
            for w in (3, 4, 5)
        ),
        "denominator_note": (
            "D-24's table divides by the padded bin WITHOUT the label-shift tail (8448); this "
            "table divides by the bin as written (8449). The 3-window row differs in the 4th "
            "decimal for that reason: 0.4210 here vs 0.4211 documented."
        ),
```

and add the assertion to `tests/test_phase21_unit_record.py` so the claim is watched.

---

### WR-02: `dp_n8` / `dp_n64` are CLI-reachable and build the OLD flat bin

**File:** `scripts/teach_persona.py:226-238` (`ARMS`), `:857-893` (`build_arm_bins`), `:876`

**Issue:** Both new arms are members of `ARMS`, so `main()` (`:912-923`) accepts
`python scripts/teach_persona.py dp_n64` and runs the full `train_arm` → `build_arm_bins` path.
`build_arm_bins:876` calls `build_bins(tok, episodes, ..., replay_ratio=replay_ratio)` with **no
`align_facts`**, so the two DP capacity arms produce a flat, concatenated v3.0 bin with no third
`*_fact.bin` — precisely the data path UNIT-01 indicts and this phase exists to replace. Nothing
refuses it; the bins land at `data/persona_dp_n64_train.bin` and an adapter is trained and
exported. A Phase-22 consumer pointing `get_batch_fact_aligned` at the result fails only later,
with "the fact bin could not be opened".

Secondary, same call site: `prefix` defaults to `"phase14"`, so the two **v4.0** arms write
`results/phase14_dp_n64/run.csv` and `checkpoints/phase14_dp_n64_adapter.pt`. `arm_outputs`'
own docstring (`:282-285`) states the prefix exists "so a Phase-17 run's artifacts say which phase
produced them instead of claiming Phase 14's" — the new arms violate the rationale the parameter
was added for.

This is a judgement call on scope (21-09 deliberately measured both arms through the *flat*
packer), but it is a live foot-gun rather than a stylistic one: the arm name promises DP and the
code path delivers the un-indicted loader.

**Fix:** couple the arm name to the packer, and label the artifacts:

```python
DP_ARMS = ("dp_n8", "dp_n64")

# in build_arm_bins:
    if arm in DP_ARMS:
        pairs = [(f, render_episodes([f], family_ids, second_person=second_person)) for f in facts]
        stats = build_bins(tok, [], outputs["bin"], outputs["mask"], align_facts=pairs)
    else:
        stats = build_bins(tok, episodes, outputs["bin"], outputs["mask"], replay_ratio=replay_ratio)
```

and pass `prefix="phase21"` (or `"v4"`) for the DP arms. If wiring the aligned packer belongs to
Phase 22, then refuse the arms from `main()` until then rather than letting them silently build the
wrong bin.

---

### WR-03: a live source comment states a figure the committed artifact records as false

**File:** `scripts/teach_persona.py:162-163`

**Issue:**

```python
# The share holds across capacities for free: 49.90% at n=64, because both sides scale with
# ``n_facts``. Nothing re-tunes.
```

`results/phase21_privacy_unit.json` measures **44.7549%** and records
`documented_n64_claim_holds: false`, `why_the_premise_fails: "Replay scales exactly with n_facts;
the PADDED TEACHING BIN does not."` The comment is left byte-unchanged with no pointer to the
correction. `scripts/teach_persona.py` is explicitly **not** ancestry-pinned (21-CONTEXT
`<code_context>`: "NOT ancestry-pinned … so it may be edited"), so the "never edit an honest
negative" convention does not apply — this is not a recorded negative, it is a projection that was
subsequently measured wrong. A reader of `teach_persona.py` has no signal that the artifact
contradicts it.

**Fix:** annotate in place (do not delete the original claim — the project's convention is dated
continuation, and this file is editable so the continuation can be inline):

```python
# The share holds across capacities for free: 49.90% at n=64, because both sides scale with
# ``n_facts``. Nothing re-tunes.
#
# CORRECTION (2026-08-24, plan 21-11): MEASURED FALSE. Both sides do NOT scale with n_facts —
# the padded teaching bin does not (56 filler facts pack to 5.054 windows each against the 8
# locked facts' 4.125), so the measured n=64 share at the pinned constant is 44.7549%, not
# 49.90%. See results/phase21_privacy_unit.json -> lot.replay_volume
# .d24_candidate_table_reproduced. D-24 is NOT reopened: REPLAY_WINDOWS_PER_FACT = 4 is chosen
# on the n=8 table, which reproduces exactly.
```

---

### WR-04: `privacy_n` claims a safety property it does not have

**File:** `scripts/mitigation_unit.py:134-141`

**Issue:** The docstring states the `int()` cast exists "so a float `n_facts` cannot **silently**
become a fractional N in a downstream epsilon". `int()` does not refuse a float — it silently
truncates, which is the same class of silent wrong answer, one step over. Measured:

```
privacy_n(7.9)  -> 7          # silently drops a record
privacy_n("8")  -> 8          # a string is accepted
privacy_n(0)    -> 0          # N = 0 accepted; downstream delta*N == 0 passes the ceiling
privacy_n(-3)   -> -3         # a negative privacy N accepted
```

This is the project's own most-named failure mode — a declared invariant that is true the day it is
written and structurally unenforced — sitting in the pre-registration module Phase 22's accountant
will import for N. The neighbouring `_prepend_replay` guard (`teach_persona.py:709-714`) gets this
right for the same quantity, including the `bool`-subclasses-`int` case.

`scripts/mitigation_unit.py` is FROZEN, so this is a **record-and-continue** finding, not an edit.

**Fix:** `scripts/_addendum.py` continuation exporting a validated accessor Phase 22 imports
instead, with the pin's version left byte-unchanged:

```python
def privacy_n(n_facts):
    """Dated continuation of mitigation_unit.privacy_n (2026-08-24). The pin's int() cast
    truncates a float silently and admits str / 0 / negative; measured privacy_n(7.9) == 7."""
    if isinstance(n_facts, bool) or not isinstance(n_facts, int) or n_facts <= 0:
        raise SystemExit(
            f"[_addendum] privacy_n got {n_facts!r} — N is a COUNT of privacy records and must "
            "be a positive int. A truncated or non-positive N produces an epsilon about a lot "
            "that does not exist."
        )
    return n_facts
```

---

### WR-05: the artifact's headline D-10 finding is an arithmetic identity it elsewhere disclaims

**File:** `scripts/phase21_unit_record.py:1161-1162` (`ratio_of_the_means`), published in
`results/phase21_multiplicity.json` → `findings.d10_doubles_the_unaligned_multiplicity`

**Issue:** The finding is stated as *"Moving replay OUT of the teaching bin (D-10) roughly DOUBLES
the old path's per-fact multiplicity"*, evidenced by `ratio_of_the_means = 2.1447721179624666`.
Under the pinned `first-token-owns-draw` rule both means are pinned by arithmetic, so that ratio is
an identity, not a measurement. Verified:

```
published ratio_of_the_means               = 2.1447721179624666
total_draws / draws_landing_on_a_fact      = 2.1447721179624666   identical: True
facts-only mean == total_draws / n_facts   : True   (200.0 == 1600/8)
replay-row mean == landing / n_facts       : True   (93.25 == 746/8)
```

The ratio is exactly `1600 / 746`, i.e. the reciprocal of the fraction of draws that landed on a
fact — which the same row already publishes as `replay_draws / total_draws = 53.4%`. The artifact's
own `budget.attribution_rule_note` says: *"the per-fact MEAN is pinned at total_draws / n_facts by
arithmetic and carries no information about the corpus. Everything this measurement says lives in
min / max / spread."* The headline is built on the ratio of two such means, contradicting that
warning one field away.

The informative comparison is present but is not the headline: spread 30 (79-109) vs spread 86
(143-229), min 79 vs 143.

**Fix:** keep the ratio but label it as derived, and promote the dispersion numbers:

```python
            "ratio_of_the_means": facts_row["mean"] / replay_row["mean"],
            "ratio_denominator": "facts-only mean / replay-in-bin mean, over the SAME 8 facts",
            "ratio_is_an_identity": (
                "Under first-token-owns-draw both means are conservation-pinned, so this ratio "
                f"equals total_draws / draws_landing_on_a_fact = "
                f"{replay_row['total_draws']} / {replay_row['draws_landing_on_a_fact']} exactly. "
                "It restates the replay share, not the corpus. The CORPUS-dependent comparison "
                f"is the dispersion: spread {replay_row['spread']} (min {replay_row['min']}, max "
                f"{replay_row['max']}) against spread {facts_row['spread']} (min "
                f"{facts_row['min']}, max {facts_row['max']})."
            ),
```

---

### WR-06: the `== 10` wall in the one file that could break it uses a strippable `assert`

**File:** `scripts/phase21_filler.py:262-267`

**Issue:** The module's own comment on the line above reads *"This module joins the `== 10` wall
HERE, at the one file in the repo that could break it"* — and the guard is a bare `assert`.
`python -O` strips it. Its sibling pre-registration module states the rule explicitly, for exactly
this reason (`scripts/mitigation_unit.py:73-76`): *"`SystemExit` and deliberately NOT `assert`: an
`assert` is strippable under `-O`, and a proof that disappears under an optimisation flag is not a
proof."* Every other refusal in `phase21_filler.py` (`refuse_collisions`, `verify_round_trips`)
correctly raises `SystemExit`; only the D-18 wall — the load-bearing one — does not.

Under `-O` the module would still import and `refuse_collisions()` would still run, but against a
`FORBIDDEN_SCORED_VALUES` set that had silently changed size, so a filler value colliding with a
new scored value would be minted without refusal.

**Fix:**

```python
if len(FORBIDDEN_SCORED_VALUES) != 10:  # all 8 locked + both soft — no tier is exempt
    raise SystemExit(
        f"[phase21_filler] the published leak vocabulary is LOCKED + SOFT = 10, measured "
        f"{len(FORBIDDEN_SCORED_VALUES)} — the filler corpus is minted against this list, so a "
        f"change to it invalidates every collision refusal below (D-18)."
    )
```

---

### WR-07: the frozen pin tells the reader to expect sampling noise where the gap is systematic

**File:** `scripts/mitigation_unit.py:119-124`

**Issue:** The pin closes `PRIVACY_UNIT_ARITHMETIC` with: *"A reader should expect the measurement
to differ from 262.94 by **sampling noise**; a reader quoting 262.94 AS a measurement is quoting
the wrong thing."* The measurement is `200.00` on the same geometry — a gap of `55.93`, which is
**not** noise: it is `1600 * 256 / 7324`, the exact systematic difference between the overlap rule
the pin computes and the `first-token-owns-draw` rule every published row is counted under. The
sentence instructs the reader to attribute a rule difference to variance, which is the more
dangerous of the two readings the paragraph was written to prevent.

This is a judgement call in the sense that the *number* is correct and correctly labelled
"overlap"; what is wrong is the reader instruction attached to it. The brief permits flagging
labelling that could mislead, and this qualifies.

The artifact side is handled well — `results/phase21_multiplicity.json` → `pin_discrepancy` names
both rules, both formulas, the gap and the reconciliation. The pin is FROZEN, so this is
record-and-continue, not an edit.

**Fix:** extend the existing `scripts/_addendum.py` continuation (the same one WR-04 needs) with:

```
CORRECTION to mitigation_unit.PRIVACY_UNIT_ARITHMETIC (2026-08-24, plan 21-11 measurement).
The pin says to expect the measurement to differ from 262.94 "by sampling noise". Measured, the
difference is SYSTEMATIC, not noise: 262.9437 is the OVERLAP rule; every published row is counted
under ATTRIBUTION_RULE = "first-token-owns-draw", whose closed form on the same geometry is
207.018, and whose conservation-pinned mean is 1600/8 = 200.00. The gap is exactly
1600 * 256 / 7324 = 55.9257. See results/phase21_multiplicity.json -> pin_discrepancy.
```

---

## Info

### IN-01: `_prove(SAMPLING_RATE_Q == 1.0, ...)` cannot fail

**File:** `scripts/mitigation_unit.py:246-252`

`SAMPLING_RATE_Q = 1.0` is a module-level literal at `:131`; the guard 115 lines below compares it
to `1.0`. Unlike the four `DELTA` guards (which evaluate real arithmetic — 21-01 watched one go RED
at n=64 only), this one is a tautology: no edit to any other line in the repo can redden it, and
the file is frozen so the literal itself cannot change. It is one of the five guards the plan
counts as "five module-level `_prove` guards"; four are load-bearing, this one is decoration.
Harmless, but it inflates the guard count. FROZEN — record only; no fix is available short of a
continuation, and it is not worth one.

### IN-02: stale line anchors inside the frozen pin

**File:** `scripts/mitigation_unit.py:96-97`

`PRIVACY_UNIT_ARITHMETIC` cites `scripts/teach_persona.py:523` and `:517` for `MAX_STEPS` and
`BATCH_SIZE`; measured now they are at `:955` and `:949`. 21-11 already recorded the `:143`/`:157`
pair drifting the same way. A reader following the anchors lands in unrelated code. FROZEN; the
correction belongs in the same `_addendum.py` continuation as WR-04/WR-07. The reusable lesson —
already adopted by `test_phase20_prereg.py`'s new fixture docstring, which cites assertions by
*name* — is worth applying to any future pin.

### IN-03: `-k phase21_glob_red_then_green` selects zero tests and exits 0

**File:** `.planning/.../21-VALIDATION.md:81` (planning artifact; recorded here for completeness)

Confirmed live: `no tests collected (982 deselected)`, exit 0. `pytest -k` is substring matching
and the real test is `test_phase21_glob_sees_the_phase21_prefix_red_then_green`. 21-03's SUMMARY
falsified this and correctly declined to amend the plan, but the VALIDATION row was never
corrected, so the documented verification command still passes vacuously. All 25 other documented
selectors were executed and all select non-zero tests. Working replacements: `-k glob_sees` (2) or
`-k phase21` (99).

### IN-04: the replay seam and `replay_window_budget` have no production caller

**Files:** `src/personacore/training/loop.py:199-201, 456-476`,
`scripts/teach_persona.py:167-178`

`train(replay_bin=, replay_mask_bin=, replay_windows=)` and `_prepend_replay(..., n_facts=)` are
reachable only from tests and from `phase21_unit_record`'s reporting; `main()` never wires them.
`replay_window_budget`'s own docstring claims "Every consumer calls this function: … `train()`'s
replay seam **via its caller**" — there is no such caller. This is defensible as a Phase-22 seam
(the docstring is explicit that per-record clipping is DPSGD-01), and the seam's off-path
bit-identity is properly proven. Recorded so a Phase-22 reader knows the wiring is still open, and
so the docstring's "every consumer" phrasing is not mistaken for a description of today's tree.

---

## What I checked and found clean

Recorded so the boundary of this review is visible rather than implied.

- `fact_window_impurities` default is `space="input"`; no union mode; **no call site overrides it**
  (7 `space=` sites audited repo-wide). The `space="target"` uses are the deliberate positive
  boundary counts in the packer's proof 7(b) and two tests.
- `fact_window_span`'s strided slice `fact_ids[: n_windows*block_size : block_size]` is correct on
  well-formed and over-long bins; the zero-window and non-contiguous cases both raise with named
  messages. The ragged `(4,4,4,4,4,5,4,4)` geometry round-trips through the loader.
- `_build_aligned_bins` **does** enforce the whole-bin length contract at build time (proof 7(a)
  reads back from disk with `np.fromfile`), which is why CR-01 is a loader-only hole.
- `_prepend_replay`'s `n_facts` validation correctly rejects `bool` (which subclasses `int`); the
  same guard is present on `train(replay_windows=)`.
- `loop.py`'s replay micro-batch weighting `micro / replay_windows` sums to exactly 1.0 over any
  split, including the ragged tail; `batch_size <= 0` raises rather than looping forever.
- No `shell=True`, `eval`, `exec`, `os.system`, or unquoted interpolation anywhere in the new
  tests or scripts. Every git fixture is `tmp_path`-confined; `_git`'s `cwd` is keyword-only and
  the new fixture never uses the `_ROOT` default.
- The strict-ancestor conjunct (`prereg != first_add` AND `is-ancestor`) at
  `tests/test_phase20_prereg.py:194-205` is correct and non-vacuous in both directions, and its
  fixture executes the *old* predicate with `check=False` so the wrong answer is computed rather
  than described.
- `render_family(..., forms=None)` runs the same two operations as v2.0, and both branches
  validate `family_id` identically. Golden digests reproduce.
- `refuse_collisions()` uses containment in both directions, not equality; the 56 filler values are
  disjoint from all 38 published pool values and all 10 leak-vocabulary values.
- `ruff check scripts/ src/ tests/` → All checks passed. 118/118 Phase-21 tests green. No
  `TODO`/`FIXME`/`breakpoint`/commented-out code in the new modules.

---

_Reviewed: 2026-08-24_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
