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
