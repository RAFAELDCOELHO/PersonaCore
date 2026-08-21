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
