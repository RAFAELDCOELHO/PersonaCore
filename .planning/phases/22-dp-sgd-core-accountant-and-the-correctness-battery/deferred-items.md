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
