# Phase 22 — deferred items

Out-of-scope discoveries logged during execution. **Not fixed** — each is a pre-existing defect in
a file some plan touched, but not in the lines that plan owns.

## Stale line-number anchors in `tests/test_phase20_prereg.py`

Found during plan 22-02 Task 2. Plan 22-02 removed the two anchors in the `V4_ARTIFACT_GLOBS`
comment block (it was editing that block anyway) and introduced none. The rest were measured but
**deliberately left alone** — the plan's own acceptance criteria name them as out of scope, and
fixing an anchor in a file whose line numbers this very diff shifts is how the defect gets
re-created with a fresh appearance of accuracy.

Measured at `cfe8cbc`:

| Citation | Claims to point at | Actually at |
|---|---|---|
| `` `:157` `` in `test_phase21_prereg_is_frozen_before_every_phase21_result`'s docstring | `adds[-1]`, the earliest add | `:225` |
| `` `:178` `` in the same docstring | the closing `assert bool(checked) == bool(tracked_artifacts)` | `:260` |
| `` `:474` `` in the `PHASE21_PREREG_ARTIFACT` comment | the import-graph scan | `:1133` |
| `` `:740` ``, `` `:805` ``, `` `:928` ``, `` `:991` `` in the same comment | the `_MITIGATION_GATE_PATH` consumers | `:1526`, `:1591`, `:1714`, `:1777` |
| `` `:2149` `` in `test_mitigation_gate_imports_bounds_by_object_identity` | a reason recorded in `tests/test_phase19_erasure.py` | not re-measured |

`` `:72` `` (`_GATE_MODULES`) is still correct.

**The fix is not renumbering.** Every one of these is in a file that grows on almost every phase,
so a corrected number has a shelf life measured in commits. The durable fix is the one plan 22-02
applied to the two it owned: cite the statement's TEXT or the symbol's NAME. A future plan that is
already editing one of these docstrings for its own reasons should convert it then — the same rule
plan 22-02 followed, applied to lines it did not own.

**Blast radius if never fixed:** a reader following an anchor lands on unrelated code and either
distrusts the comment or, worse, believes the wrong line is the mechanism. That is the Phase-21
IN-02 defect class, and it is the reason `scripts/mitigation_accountant.py` was written with zero
line-number citations — a frozen file cannot be corrected at all.

## `delta_quadrature` raises a bare `OverflowError` in a 0.92-wide negative-`z` band

Found during plan 22-03 Task 2, and **partly** fixed there rather than fully.

The substituted form separates a tiny `phi(z)` prefactor from a large scaled integral. For `z < 0`
that integral's own `exp(-z*u - u*u/2)` peaks at `u = -z` with value `exp(z*z/2)`, so it overflows
once `z*z/2 > 709.782712893384`, i.e. once `z < -37.677120720`. Measured at `9009561`:

| `eps` | `mu` | `z` | before the fix | after |
|---|---|---|---|---|
| 0.001 | 60.0 | −30.000 | returns `I = 6.78e+195` | returns |
| 0.001 | 76.0 | −38.000 | `OverflowError: math range error` | **`ValueError`, condition 1** |
| 0.001 | 100.0 | −50.000 | `OverflowError: math range error` | **`ValueError`, condition 1** |
| 0.001 | 1088.0 | −544.000 | `OverflowError: math range error` | **`ValueError`, condition 1** |

Condition 1 was widened in that commit to `ez <= -745.0 or (z < 0.0 and ez < -709.782712893384)`,
which converts the whole `z < -38.6005` half into a stated domain refusal. **What remains is the
band `-38.600518131 < z < -37.677120720`**, ~0.92 wide in `z`, where the widened clause fires
first and correctly — so at the boundary the two clauses now overlap and there is, as of
`9009561`, **no input that still reaches the bare `OverflowError`**. The entry is kept because the
threshold is an inequality on a measured constant: any future edit that loosens `_EXP_OVERFLOW_ARG`
or drops the `z < 0.0` clause re-opens the gap, and nothing currently tests the negative-`z` corner.

**Not fixed here, and the reason is scope rather than cost.** A dedicated test for the negative-`z`
refusal would be a fourth refusal case in `test_oracle_refuses`, whose entire assertion is that
there are exactly **three** non-vacuity conditions with three distinct messages — plan 22-09 reads
that shape. The corner is also unreachable by every consumer in this phase: `mu ≈ 76` is
`sigma ≈ 0.19` at `T = 200`, a mechanism with `delta ≈ 1` that no sweep publishes, and
`EPSILON_GOLDEN`'s largest `mu_eff` is 7.071 (`z >= -3.536`).

**Blast radius if the clause is ever dropped:** a bisection bracket that walks into `mu > 75`
aborts with an arithmetic error carrying no domain information, instead of the refusal the module
docstring promises. Never a wrong number — `math.exp` raises rather than returning `inf` — so this
is a diagnosability defect, not a privacy one.

### RETRACTED IN PLACE 2026-08-26 (plan 22-16)

**The paragraph above beginning *"Not fixed here, and the reason is scope rather than cost"* is
FALSE as of plan `22-14`, and the obstacle it names never applied.** The original paragraph is left
standing as the record of what was believed when it was written — the same retract-in-place
discipline `REQUIREMENTS.md`'s DPSGD-03 row now carries. A deferral log that still says "not fixed"
about something the tree has fixed is a false record, which is the defect class this project
retracts rather than quietly edits.

**What closed it.** Plan `22-14` fixed the band. Condition 1's negative-`z` clause now budgets for
the Simpson **SUM** rather than for a single `math.exp` argument, subtracting
`math.log(4.0 * n)` = `11.28983191240606` at the default `n = 20001` and moving the negative-`z`
boundary from `-709.782712893384` to `-698.4928809809779`; condition 3 gained a
non-finite / upper-bound refusal with a slack measured over 5,351 answered cells. Re-measured by
plan 22-16 over 22-14's own sweep (ε=1e-4, μ ∈ [74.0, 78.0] at step 1e-3, **4001 cells**), where
404 cells returned `inf` before the fix:

```
cells=4001 answered=753 refused=3248 nonfinite=0 above_1.0=0 exactly_1.0=369
```

**Why the stated obstacle never applied.** This entry gave the reason as scope: *"A dedicated test
for the negative-`z` refusal would be a fourth refusal case in `test_oracle_refuses`, whose entire
assertion is that there are exactly three non-vacuity conditions with three distinct messages."*
Plan 22-14 wrote exactly that dedicated test —
`tests/test_phase22_accountant.py::test_quadrature_budgets_the_simpson_sum_not_one_term`, which
asserts `pytest.raises(ValueError, match="DOMAIN LIMIT")` at the cited defect point and sweeps a
14-point band across the former hole — **as a SEPARATE test function**. It is not a fourth case
inside `test_oracle_refuses`, so that test's three-conditions/three-messages shape is untouched:
`22-14-SUMMARY.md` records `test_oracle_refuses` passing unmodified and `delta_quadrature`'s refusal
messages still **3 fired, 3 distinct** before and after. A dedicated test never had to live inside
`test_oracle_refuses`; the entry inferred a constraint that was not there.

```
.venv/bin/python -m pytest tests/test_phase22_accountant.py::test_quadrature_budgets_the_simpson_sum_not_one_term -q
1 passed in 0.01s
```

**What remains true from the original entry.** The threshold is still an inequality over measured
constants, so a future edit that loosens `_EXP_OVERFLOW_ARG`, drops the `z < 0.0` clause, or removes
the `log(4.0 * n)` headroom re-opens the band. The difference is that this is no longer untested:
mutation **M-C** (remove the headroom, restoring the single-term bound) was watched RED on the real
committed module with one distinct RED and a sha256-identical restore (`22-14-SUMMARY.md`).

## WARNING-2 — DP kill→resume has no production driver

Carried forward from `22-VERIFICATION.md` by plan `22-16`. **Routed to Phase 23, beside DPSGD-06 —
a deliberate deferral with a reason, not an oversight.**

**What was found.** SC5's kill→resume workflow is satisfied through `train(resume_from=…)`, which
IS the production API, and `tests/test_phase22_checkpoint.py::test_resume_epsilon_bit_identical`
correctly refuses to restore by hand. But **no production path can resume a DP arm at all**:
`scripts/teach_persona.py::train_arm` never passes `resume_from`, and its `refuse_if_exists` on the
checkpoint path actively BLOCKS re-running a killed DP arm. So the workflow SC5 describes is
exercised only from tests today. This is the same unwired-seam shape as Phase 21's IN-04 and must
not be inherited as done.

**Deliberately NOT closed here, and the reason is that this is a missing FEATURE rather than a
defect in what Phase 22 shipped.** Closing it means *adding* a resume path to the production driver
and *relaxing* a refusal that exists on purpose — a design decision that belongs to the phase whose
first act is a genuinely real training run, not to a phase that proved a mechanism on CPU fixtures.
Building the correction now would anticipate functionality only Phase 23 actually needs, and would
put a relaxed `refuse_if_exists` into the tree ahead of any consumer that could exercise it. The
user confirmed this routing on exactly that reasoning.

**Phase 22 leaves the eventual wiring SAFER than it found it.** Plan `22-13` shipped the refusal in
`src/personacore/training/loop.py`: `dp_fn is None` against a checkpoint carrying `dp_noise_rng` now
raises rather than silently continuing a private run with no clipping and no noise. That guard is
inert today precisely because no production driver reaches it — and it becomes load-bearing the
moment Phase 23 adds one. `22-13-SUMMARY.md` records it watched RED under mutation M-H over the
full suite, with exactly one distinct RED.

**Blast radius if it is never wired:** a killed DP arm cannot be resumed at all, so a long M3 run
that dies must restart from step 0 — expensive, but never a wrong privacy number. The dangerous
version (resuming it *without* the seam) is the one 22-13 already refuses.

## WARNING-1 was CLOSED, not deferred

Recorded here in one place so the pair is not read as two open warnings. `22-VERIFICATION.md`'s
WARNING-1 (`loop.py`'s silent no-op fallback on the resume path) is **closed by plan `22-13`** on
the direction that matters — `dp_fn is None` with the `dp_noise_rng` slot PRESENT now refuses — and
its other direction (seam live, slot absent) is documented in `loop.py` as a **deliberate**
non-refusal, with the three-splat-site reachability measurement that makes it correct and the node
ids of the two committed back-compat guards that would redden if a future "symmetry" edit refused
it. 22-REVIEW's CR-04 proposed refusing that direction; `22-VERIFICATION.md` rejected it on
measurement, and `22-13` did not implement it. Nothing here is open.

## `tests/fixtures/phase22_reference.py:185-187` still carries a FALSE figure

Found during plan `22-17` Task 2, which was editing that same file to add `LOG_ERFC_BAND`.

The text, inside `EPSILON_OVERFLOW_REGIME`'s provenance block:

> The error is EXACTLY ZERO at sigma >= 0.42, so these two rows are the whole reachable band.

**Why it is false.** `22-VERIFICATION.md` retracts it in the verifier's own name (its lines 92-101
and 315-318): the sentence measured the FIX's delta — pre-fix versus post-fix *shipped* values,
which are genuinely bit-identical for σ ≥ 0.4125 — and not the error against truth. Against 60 dps
the error at σ ≥ 0.42 is 1.100e-13 at 0.4200 and 9.631e-12 at 0.4185, and the two rows were **not**
the whole reachable band: [0.4135, 0.4185] was reachable and uncovered, which is exactly the band
`22-17` closes. The verifier names this sentence as "precisely the sentence that made the residual
band look already covered".

**Independently re-confirmed in this session**, post-fix, sweeping σ ∈ [0.4130, 0.4200] at step
0.0005 with T=200 at the frozen δ: every row's `erfc(b)` is subnormal or exactly zero — i.e. every
row was inside the defective band — and none has an error of exactly zero against 80-dps truth
(measured 1.5538e-15 to 3.1897e-14 after the fix).

**NOT FIXED HERE, deliberately, and the reason is ownership rather than cost.** `22-17`'s plan does
not ask for it, and the dispatch brief names **plan `22-19`** as the plan that exists to undo false
figures in committed comments. Correcting it here would collide with that plan's scope and would
produce two diffs against the same three lines. `.planning/REQUIREMENTS.md:350` carries the same
sentence and needs the same correction, which is why it belongs to one plan rather than to whoever
happens to be editing the file.

**Blast radius if never fixed:** two comment blocks, no executable code, no test. The danger is
exactly the one already realised — a reader concludes the band is covered and does not look.

## The plan's `grep -rn "float_info" src/` assertion is no longer literally empty

Found during plan `22-17` Task 3, running the plan's own closing assertion.

`22-17-PLAN.md` asserts `grep -rn "float_info" src/` is empty. Measured, it returns **one** match —
`src/personacore/privacy/accountant.py:90`, a COMMENT written in that plan's own Task 1 explaining
why `sys.float_info.min` is deliberately *not* used and `math.ldexp(1.0, -1022)` is used instead.

**This is a prose mention, not a code use, and no action is needed.** The load-bearing constraint is
the module's import ceiling, which is unchanged and is checked three stronger ways:

```
grep -n "^import \|^from " src/personacore/privacy/accountant.py   -> 82:import math   (single line)
grep -rn "import sys" src/personacore/privacy/                      -> (empty)
grep -rn "float_info" src/ | grep -v '#'                            -> (no non-comment match)
```

and `tests/test_phase22_accountant.py::test_accountant_imports_math_only` asserts hard equality with
`{"math"}` statically AND out of process, and passes.

Recorded so the next executor running that grep does not read a comment as a violation. If a future
plan wants the grep literally empty, the comment can drop the two words `sys.float_info.min` — at
the cost of the reader no longer being told which constant was rejected and why. That trade is not
obviously worth making, which is why it is logged rather than taken.

Related, and worth stating so a register is not misread: `22-17`'s mutation label **M-H collides
with `22-13`'s M-H**. They are different mutations of different files — `22-13`'s M-H reverts
`loop.py`'s DP-resume refusal, `22-17`'s M-H reverts `_log_erfc`'s fast-path predicate. Both were
watched RED. The labels are per-plan, not global.
