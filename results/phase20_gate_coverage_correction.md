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

**Phase 20 GATE-06 coverage correction: not yet recorded.**
