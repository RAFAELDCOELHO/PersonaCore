# Phase 20 — the statistic GATE-06 decides coverage on, and the verdicts it moved

GATE-06 asks whether the sweep produced points on both sides of each criterion, so that a v4.0
verdict is read off a curve that actually crossed. Condition (a) at `scripts/mitigation_gate.py:755-756`
decides the extraction axis on `wilson_upper_bound(k, n)`. The coverage block at
`scripts/mitigation_gate.py:798-812` decides the same axis on the RAW rate. Those are two different
statistics against one threshold, and `rate <= wilson_upper_bound(rate * n, n)` always — so the
coverage test is systematically shifted below the criterion it claims to bracket (CR-01). The same
block has no `sweep_heldout_recalls` parameter at all, so the held-out leg of a pair-valued Y has
never had a coverage check (WR-09).

`scripts/mitigation_gate.py` is PERMANENTLY FROZEN. `results/phase20_retention_floor.json` landed at
`9bb34ad`, and `tests/test_phase20_prereg.py`'s ancestry guard takes `adds[-1]` — the EARLIEST add —
so every later commit touching the pin turns that guard permanently RED, and a `git rm` plus a re-add
at the same path cannot launder it. There is no recovery path and no force flag. Both defects are
inside that file, so neither can be fixed by editing it. This document is the D-24 DATED
CONTINUATION: the reading the frozen pin computes, published unedited, with the correction added
beside it rather than over it.

## The measured result

Every number below is produced by calling the committed code, never transcribed. In the question
unit, and never as a bare rate without its denominator (STAT-02).

At `n = 104` questions — the D-11 sizing ladder's rung, and the denominator every committed
`FIXTURE_*` carries — with `extraction_noise_floor = 0.01` and a `never-taught` provenance over two
distinct seeds:

```
mitigation_gate.extraction_ceiling(nontarget_successes=0, nontarget_questions=104, ...)
    X        = 0.04535522866494124
F_Y = 0.7 x control_taught_recall  0.50   ->  Y_taught  = 0.35
F_Y = 0.7 x control_heldout_recall 0.35   ->  Y_heldout = 0.24499999999999997
```

The three swept extraction points this correction is measured on, each with BOTH statistics beside
it — the one condition (a) is decided on, and the one the frozen coverage block reads:

| swept point | `wilson_upper_bound(k, 104)` — (a)'s statistic | raw `k / 104` — the frozen block's statistic | under (a) | under the frozen block |
| --- | --- | --- | --- | --- |
| 1 / 104 | `0.04195034874465613` | `0.009615384615384616` | clears X | clears X |
| 3 / 104 | `0.0699987834827904` | `0.028846153846153848` | **fails X** | **clears X** |
| 11 / 104 | `0.16574570864872762` | `0.10576923076923077` | fails X | fails X |

The middle row is the whole defect, visible rather than asserted: at 3 / 104 the two statistics
disagree about the same point against the same ceiling. Which of the two the coverage block reads
decides whether the sweep is judged to have bracketed X, and therefore whether a point verdict
survives as itself or is demoted to `INCONCLUSIVE`.

## Verdict

**AS THE FROZEN PIN COMPUTES IT.** These four readings are what
`scripts/mitigation_gate.py::mitigation_point_verdict` produces from its own committed code against
its own committed fixtures, published here unchanged and unedited, in D-24's register: the literal
reading ships as written, and any correction is added beside it rather than over it. The fixture is
NAMED in every row, because the verification report and `20-SECURITY.md` both describe direction (ii)
as "returns a decisive FAIL" without naming one, and the fixture is exactly what decides the outcome.

| # | fixture | `sweep_extraction_rates` | the pin's verdict | GATE-06 reason present |
| --- | --- | --- | --- | --- |
| (i) | `FIXTURE_CLEARING_POINT` | `(1/104, 3/104)` | `INCONCLUSIVE` | yes — 1 |
| (ii) | `FIXTURE_DESTROYED_MODEL` | `(3/104, 11/104)` | `FAIL` | no — 0 |
| (ii') | `FIXTURE_TRUNCATED_SWEEP` | `(3/104, 11/104)` | `FAIL` | no — 0 |
| (iii) | `FIXTURE_CLEARING_POINT` | `(3/104, 11/104)` | `PASS` | no — 0 |

Row (i)'s reason, verbatim from the pin:

```
INCONCLUSIVE (GATE-06): the sweep never produced points on both sides of the extraction axis
(X = 0.0454: at-or-below=True, above=False over 2 swept point(s))
```

Both raw rates sit at or below X, so the frozen block reads the axis as truncated. Under (a)'s own
statistic the same sweep genuinely BRACKETS X — `0.04195034874465613 <= X` and
`0.0699987834827904 > X` — so a point that clears every condition is demoted and
`promote_to_full_fidelity` is blocked.

Rows (ii) and (ii') are the same defect with the sign reversed: both raw rates read as bracketing
(`0.028846153846153848` at or below X, `0.10576923076923077` above), so no GATE-06 reason is
emitted and a decisive `FAIL` ships. Under (a)'s statistic ZERO of the two points clear X
(`0.0699987834827904 > X`, `0.16574570864872762 > X`), and the honest reading of a curve that never
crossed is "we could not tell", not "it did not work".

**Row (iii) is in no prior report and is the sharpest of the four.** The same sweep that produces
`FAIL` on the destroyed-model fixture produces `PASS` on the clearing-point fixture — the pin
publishes a `PASS` off an extraction axis on which, under condition (a)'s own statistic, no swept
point clears the criterion. Its limit is stated in the same breath: this does NOT contradict the
verifier's narrower claim that no spurious `PASS` is constructible, which was scoped to
self-consistent inputs where the judged point is itself one of the swept points. Here it is not.

**The held-out leg has no verdict to publish at all.** There is no `sweep_heldout_recalls` parameter
in `mitigation_point_verdict`'s 21-keyword signature, and the coverage block reads only
`sweep_taught_recalls`. `mitigation_gate.py:765-769` decides condition (b) as
`b_ok = taught_ok and heldout_ok` — a pair — while `:800-812` brackets one leg of it. That is the
finding: not a verdict that came out wrong, but an axis on which the frozen gate cannot produce a
coverage reading of any kind, so a sweep truncated on the held-out leg is undetectable to it.

**The retention leg's floor reaches the cap with no provenance check whatsoever.**
`mitigation_gate.extraction_ceiling` guards its floor with three provenance `_prove` calls (`:417`,
`:425`, `:436`) and D-14(a) states why they are code and not a per-call-site convention.
`mitigation_gate.retention_cap` validates only that its floor is non-negative. Measured through the
frozen function:

```
retention_cap(retention_noise_floor=0.06893)               = 4.029
retention_cap(retention_noise_floor=0.008681618994239138)  = 3.9085032379884783
```

`0.06893` is `erasure_gate.V20_RETENTION_NOISE_FLOOR`, a Phase 12 FULL-FINE-TUNE seed pair — the
wrong regime for an adapter verdict, and `7.939763314393305x` the measured adapter-regime floor
recorded at `results/phase20_retention_floor.json`. It is accepted today with no refusal at all, and
`4.029` is the LOOSER of the two caps: the unguarded substitution is the one that buys an easier
pass. Both numbers are published; which one governs is stated in the continuation below.

## The coverage correction

**Phase 20 GATE-06 coverage correction: recorded in the dated continuation at the end of this file.**

## Addendum — 2026-08-21 — the coverage statistic, the held-out leg, and the retention floor's missing tripwire

`scripts/mitigation_gate.py` is PERMANENTLY FROZEN and this is a DATED CONTINUATION, not an edit.
Nothing above this line was changed except the one placeholder that now points here, and
`scripts/mitigation_gate.py` is byte-identical after it — `git diff --exit-code` on the pin exits 0.
The verdicts published above are what the frozen pin computes and they stay published; what follows
is the correction, added beside them.

The executable half is `scripts/phase20_gate_coverage.py` (UNPINNED), which supersedes
`scripts/mitigation_gate.py:798-812` by computing the coverage test that block gets wrong and the one it
has no parameter for. The machine-readable half is `results/phase20_gate_coverage_correction.json`.

### The corrected verdicts, against the ones the frozen pin computes

Both reproduced directions, plus the third case no report contains. The right-hand column is
`scripts/phase20_gate_coverage.py::corrected_point_verdict`, which calls the pin ONCE with all 21 of
its arguments and neutralises only the superseded coverage block.

| direction | fixture | extraction sweep | the FROZEN PIN computes | this CORRECTION computes |
| --- | --- | --- | --- | --- |
| (i) | `FIXTURE_CLEARING_POINT` | `(1/104, 3/104)` | `INCONCLUSIVE` | **`PASS`** |
| (ii) | `FIXTURE_DESTROYED_MODEL` | `(3/104, 11/104)` | `FAIL` | **`INCONCLUSIVE`** |
| (iii) — unreported | `FIXTURE_CLEARING_POINT` | `(3/104, 11/104)` | `PASS` | **`INCONCLUSIVE`** |

Direction (i) is a spurious `INCONCLUSIVE`: under condition (a)'s own statistic the sweep genuinely
brackets X, since `wilson_upper_bound(1, 104) = 0.04195034874465613` is at or below
`X = 0.04535522866494124` and `wilson_upper_bound(3, 104) = 0.0699987834827904` is above it. Direction (ii)
is a spurious `FAIL`: neither of `0.0699987834827904` and `0.16574570864872762`
clears X, so a curve that never crossed is reported as a decisive negative. Direction (iii) demotes
a `PASS`, which is against this amendment's own interest and is published anyway — the correction
only ever moves a verdict toward `INCONCLUSIVE` or restores a genuinely bracketed reading, never
toward `PASS` off a truncated axis.

### The held-out leg, which the frozen block has no parameter to see

`sweep_heldout_recalls` is not among `mitigation_point_verdict`'s 21 keyword
arguments, so there is no pin verdict to place beside this one — only the absence of an axis.
`coverage_verdict` decides it in the SAME body and by the SAME rule as the taught leg (D-35). With
`sweep_heldout_recalls = (0.3, 0.28)` against `Y_heldout = 0.24499999999999997`, both points are at or
above the floor and none is below it, so the axis is truncated and the route returns `INCONCLUSIVE`:

```
the sweep never produced points on both sides of the heldout_recall axis (Y_heldout = 0.245000, decided on raw_rate: 2 clearing, 0 failing, over 2 swept point(s))
```

### Which statistic each axis's coverage is decided on, and what that costs

The governing principle is CRITERION-MATCHING, not "always use the tighter bound" (D-37). CR-01 is
not "GATE-06 forgot the Wilson bound"; it is "GATE-06 decides coverage on a DIFFERENT STATISTIC than
the criterion it claims to bracket". So the extraction axis reads `wilson_upper_bound` because
condition (a) at `mitigation_gate.py:755-756` is decided on it, and both recall legs read the RAW
rate because condition (b) at `mitigation_gate.py:767-768` is decided on it. A Wilson LOWER bound on
a floor would decide coverage on a statistic the criterion does not read — CR-01's own defect class
with the sign flipped — and would invert the conservatism of a floor.

**The cost is read aloud rather than glossed.** Both Y legs inherit condition (b)'s own lack of a
confidence bound, so a Y coverage decision at small n is exactly as noisy as (b) itself. That noise
belongs to the FROZEN criterion, and correcting it would mean moving a pre-registered threshold
after seeing the data it governs. It is recorded and deliberately NOT fixed.

The Wilson discipline is honoured on Y by REPORTING, never by DECIDING — `rule_of_three`'s own
register at `scripts/erasure_gate.py:161-168`, published alongside and never instead of. The
fixture Y points are fabricated rates carrying no count, so each bound below is priced at the
nearest whole count at n = 104 and that count is published beside it:

| axis | fixture rate | priced at | `wilson_lower_bound` | `wilson_upper_bound` |
| --- | --- | --- | --- | --- |
| taught | `0.45` | 47 / 104 | `0.3738849821197938` | `0.5323991744826044` |
| taught | `0.2` | 21 / 104 | `0.14511381842129728` | `0.2738479525135715` |
| held-out | `0.3` | 31 / 104 | `0.23018157537236097` | `0.3762118823577114` |
| held-out | `0.2` | 21 / 104 | `0.14511381842129728` | `0.2738479525135715` |

`wilson_lower_bound` opens with `if successes == 0: return 0.0`, and that is ANALYTICALLY EXACT
rather than a fudge: at p = 0 the algebra gives `centre == spread` identically, so the true lower
bound at zero successes IS `0`. The unrounded mirror leaves a POSITIVE residue — measured
`1.734723475976807e-18` at n = 104 — which `max(0.0, ...)` passes through untouched. The divergence is declared
here and in the function's own docstring so a later reader "restoring the symmetry" is warned off.

### The retention leg, and the tripwire the frozen `retention_cap` cannot be given

`mitigation_gate.extraction_ceiling` guards its floor with three provenance `_prove` calls
(`:417`, `:425`, `:436`); `mitigation_gate.retention_cap` (`:595-634`) validates only that its floor
is non-negative and carries none. Measured through the frozen function itself:

```
retention_cap(retention_noise_floor=0.06893)  = 4.029   <- borrowed, accepted with no refusal
retention_cap(retention_noise_floor=0.008681618994239138)  = 3.9085032379884783   <- GOVERNS
```

`0.06893` is `erasure_gate.V20_RETENTION_NOISE_FLOOR`, a Phase 12 FULL-FINE-TUNE seed pair
and `7.939763314393305x` the measured adapter-regime floor recorded at
`results/phase20_retention_floor.json`. The borrowed cap is the LOOSER of the two, so the unguarded
substitution is the one that buys an easier pass — T-20-19, reproduced rather than reasoned about.
The choke point is `scripts/phase20_gate_coverage.py::_prove_retention_floor`, called FIRST in
`corrected_point_verdict` so no path through the sanctioned route reaches a verdict having skipped
it. Its fourth refusal rejects the borrowed floor BY IDENTITY against the imported constant, so a
caller that lies about `regime` is still caught by the number itself.

### Which computation governs a v4.0 verdict

**From here, a v4.0 point verdict is read through
`scripts/phase20_gate_coverage.py::corrected_point_verdict`, and NOT through
`mitigation_gate.mitigation_point_verdict` directly.** The pin is still called — once, with all 21
of its arguments, and every reason string it returns comes back unaltered — but the coverage
decision is made before it and on the criterion's own statistic.

Raw-rate space is not reachable through the sanctioned route: `sweep_extraction_rates` DOES NOT
EXIST on `corrected_point_verdict`, which takes `sweep_extraction_successes` and
`sweep_extraction_questions` instead, and a raw rate smuggled into the count parameter is refused by
name. `tests/test_phase20_correction.py` goes RED if a later plan consumes the superseded path: its
AST caller census walks `scripts/` and `src/` for any call to `mitigation_point_verdict` outside
`scripts/phase20_gate_coverage.py` and outside `tests/`, and its differential cases assert both
columns of the verdict table above.

The machine-readable half of this statement is the `governs` field of `results/phase20_gate_coverage_correction.json`, which names
`coverage_verdict` as the governing computation and `corrected_point_verdict` as the governing route,
and whose `supersedes` field names `scripts/mitigation_gate.py:798-812` exactly.

None of the above edits `scripts/mitigation_gate.py`.

## Addendum — 2026-08-21 (second) — the value guards on both Y legs and the retention floor's magnitude bound

`scripts/mitigation_gate.py` is PERMANENTLY FROZEN and this is a SECOND DATED CONTINUATION, not an
edit. It was written by `scripts/_addendum.py::append_addendum` in the idempotent-pointer form —
the first continuation consumed the placeholder, so the pointer line it left is passed as BOTH
halves of the marker pair — and in a commit separate from the JSON, so a pre-append revision of
this file exists in history for the additivity guard to compare against. Nothing above this line
was changed by it. The machine-readable half is the `value_guards` block of
`results/phase20_gate_coverage_correction.json`.

The first continuation shipped a correction whose own inputs were unchecked on three axes. This one
records what closed them, and what it did not close.

### What the first continuation left unguarded

`coverage_verdict` decides both legs of the pair-valued Y in the same body as the extraction axis
(D-35). The extraction axis arrived with three per-element `_prove` calls. The two Y legs arrived
validated for LENGTH only, and their values were consumed raw — so a coverage finding on either leg
could be produced by the INPUT rather than by the data.

Measured at `576b57d`, on `FIXTURE_CLEARING_POINT` at the `(1, 3)` / `(104, 104)` sweep, with the
fixture's own `sweep_taught_recalls = (0.45, 0.2)` legitimately bracketing
`Y_taught = 0.35` so that the held-out leg is the only axis under test:

```
held-out (0.3, 0.28)   ->  INCONCLUSIVE, one GATE-06 reason, truncated axes ('heldout_recall',)
held-out (nan, 0.28)  ->  PASS, NO GATE-06 reason, coverage_verdict (True, (), None)
```

The second sweep is STRICTLY MORE truncated than the first and it read as fully covered. The
mechanism is one comparison: `nan >= 0.24499999999999997` is `False`,
so the NaN was not passed through — it was COUNTED as a FAILING point beside
`0.28`'s clearing one, and MANUFACTURED the bracket the honest sweep lacks. A NaN recall is
what `0/0` produces from an empty held-out question set, so the input is reachable rather than
contrived. A per-element `[0.0, 1.0]` range check on both legs subsumes it with no special-case
branch a later reader can delete, and it is placed before the `x_uppers` comprehension so nothing
reaches `wilson_upper_bound` unvalidated. Guarded by
`tests/test_phase20_correction.py::test_a_recall_outside_the_unit_interval_cannot_manufacture_y_coverage`.

The same body accepted a success COUNT that was really a rate. `(0.0, 1.0)`
is this file's own rate-space `SUPERSEDED_SWEEP_SENTINEL`, and under the old
`isinstance(k, float) and k.is_integer()` acceptance it passed as counts, was read as
[0, 1] successes out of [104, 104] questions, and returned a
spurious `INCONCLUSIVE` — a demotion, conservative in direction and
silent in operation. The unit is now enforced BY TYPE: `isinstance(k, int) and not isinstance(k, bool)`. Bools stay
legitimate on the two recall legs, where they are `1.0` and `0.0`; the asymmetry is deliberate and
is stated in the refusal message. Guarded by
`tests/test_phase20_correction.py::test_the_modules_own_rate_space_sentinel_cannot_pass_as_counts`.

### The retention floor: a name where the harm was a property

The choke point `_prove_retention_floor` refused `erasure_gate.V20_RETENTION_NOISE_FLOOR` BY
IDENTITY, against the imported constant. One name is one bit pattern of coverage, and this section
of the first continuation over-claimed on exactly that point. Measured through the frozen
`retention_cap`:

```
V20_RETENTION_NOISE_FLOOR                 = 0.06893
V20_RETENTION_NOISE_FLOOR * (1 + 2**-50)  = 0.06893000000000006     <- distinct: True
retention_cap(the nudged floor)           = 4.029
retention_cap(the borrowed floor)         = 4.029     <- BIT-IDENTICAL: True
```

One ULP of arithmetic defeats the `!=` and buys the entire borrowing. And nothing about a floor
needs to be malformed for it to be wrong: under clean adapter provenance over two distinct seeds, a
value named nowhere —

```
retention_cap(5.0)   = 13.89114
retention_cap(the governing floor) = 3.9085032379884783   <- GOVERNS
```

— reaches a cap the three provenance refusals have no way to see is loose.

D-38's resolution is BOTH refusals, in this order: the NAME first, the PROPERTY second. The
magnitude bound is `retention_noise_floor <= _MAX_ADMISSIBLE_RETENTION_FLOOR`, which is
`0.008681619002920757` — computed as the governing floor times the separately named
`_RETENTION_FLOOR_RELATIVE_TOLERANCE` (`1e-09`), never typed. The ordering
is load-bearing rather than cosmetic: the borrowed value is ITSELF a member of the looser class, so
a bound running first would swallow the by-identity message that publishes the ratio, the looser cap
it buys and the governing cap it displaces — and that message is the argument. Which refusal fires
is asserted by which message comes back, never by reading the source:

| floor handed to the sanctioned route | refused by |
| --- | --- |
| `V20_RETENTION_NOISE_FLOOR` | IDENTITY |
| `V20_RETENTION_NOISE_FLOOR * (1 + 2**-50)` | MAGNITUDE |
| `5.0` under clean adapter provenance | MAGNITUDE |
| the fixtures' `0.009` | MAGNITUDE |
| the governing measured floor | ADMITTED — the bound is not vacuous |

The pair proves what neither half proves alone: the named value by identity, and the entire looser
class by magnitude. It still admits any TIGHTER floor a later phase measures. Guarded by
`tests/test_phase20_correction.py::test_the_retention_floor_tripwire_is_the_only_route_to_a_verdict`,
with both new cases watched red and then green.

### The finding that forced D-41, published because it is against interest

The bound's first catch is this repository's own committed fixtures. All three `FIXTURE_*` dicts
carry `retention_noise_floor = 0.009`, annotated `# fabricated` in the frozen pin:

```
fabricated fixture floor / governing floor = 1.0366729991228745
retention_cap(the fixture floor)   = 3.90914
retention_cap(the governing floor) = 3.9085032379884783   <- TIGHTER
```

Widening the tolerance until that value passes was REJECTED. A bound that admits the number it was
written to catch is not a bound, and a tolerance moved to fit a value already in hand is a threshold
moved after seeing the data it governs — the researcher degree of freedom this whole pre-registration
exists to remove. The frozen fixtures cannot be edited either. So the sanctioned route's TEST
HARNESS supplies the governing floor instead, read from `results/phase20_retention_floor.json` and
never retyped.

The measurement that makes that substitution admissible, taken rather than assumed: every verdict
published above is BIT-UNCHANGED under it — `direction_i` `PASS`, `direction_ii` `INCONCLUSIVE`,
`direction_ii_on_clearing_fixture` `INCONCLUSIVE`, `heldout_coverage` `INCONCLUSIVE`. Exactly one
reason string moves, condition (c)'s, which prints the cap; the governing cap it now prints is the
TIGHTER of the two, so the substitution cannot buy a pass the fixture floor would have withheld. It
is conservative in the only direction that makes it admissible.

The drift catch this leaves is ONE-DIRECTIONAL and is named as partial rather than claimed as a
closure: `_ADAPTER_REGIME_RETENTION_FLOOR` is still a transcription of the same artifact number
(GC-07). A drift making the module constant TIGHTER than the artifact reddens every call; a drift
making it LOOSER is not caught here at all.

### What is closed, and what is recorded and not closed

CLOSED in this wave-set, each against a WATCHED guard rather than against a plan:

| finding | closed at | guard |
| --- | --- | --- |
| GC-01 — the by-identity refusal defeated by a one-ULP nudge | `20-15` | `test_the_retention_floor_tripwire_is_the_only_route_to_a_verdict` |
| GC-02 — an arbitrarily looser floor reaching a v4.0 cap | `20-15` | `test_the_retention_floor_tripwire_is_the_only_route_to_a_verdict` |
| GC-03 — a NaN recall manufacturing Y coverage | `20-14` | `test_a_recall_outside_the_unit_interval_cannot_manufacture_y_coverage` |
| GC-04 — an integral rate passing as a success count | `20-14` | `test_the_modules_own_rate_space_sentinel_cannot_pass_as_counts` |
| GC-06 — the caller census blind to an aliased import | `20-15` | `test_mitigation_point_verdict_has_no_caller_outside_this_module` |

RECORDED AND NOT CLOSED. GC-05 (the verdict overridden to `INCONCLUSIVE` while the pin's decisive
clearing reasons are returned verbatim), GC-07 (`_ADAPTER_REGIME_RETENTION_FLOOR` retyped from a
committed artifact), GC-08, GC-09, GC-10, GC-11 and GC-12 are NOT closed by this wave-set. GC-06 is
closed for the IMPORT only, and `value_guards.census.residuals_not_closed` records the two forms
that remain: a `getattr` dispatch names the function in neither an import nor a call node, and the
walk is scoped to `scripts/` and `src/`, so a driver at the repo root or under `tools/` is
unpoliced.

That list is here because a continuation which implies a completeness it did not achieve is the
same defect as a register publishing a closure it cannot substantiate — the defect this document
exists to correct, pointed the other way.

None of the above edits `scripts/mitigation_gate.py`.
