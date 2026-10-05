---
phase: 39-instrument-context-2-2
plan: 05
subsystem: E6 driver part 2 (CTX-02)
tags: [driver, run, gate, d-30, rehearsal, d-27, ledger, ast-census]
requirements-completed: []
dependency-graph:
  requires: [39-04 (driver part 1), 39-03 (prereg frozen at 9366134)]
  provides: [phase39_ctx.run, DISCLOSED_MODULES, rehearsal_identity_path, record_rehearsal, rehearsal_disclosure, preflight identity/D-27/DR-03 checks, AST censuses]
  affects: [39-06 crosscheck + emit + record, 39-07 report + rehearsal]
key-files:
  created: []
  modified:
    - scripts/phase39_ctx.py
    - tests/test_phase39_ctx.py
decisions:
  - "DR-02 slice check runs in run() BEFORE the ledger start line (shared _kept_identity), so the refusal writes no start line (D-03)"
  - "preflight refuses a malformed identity with a SystemExit naming DR-03 (shape check), and returns rehearsal_disclosure (None on a rehearsal root)"
  - "DI-04: del model, tok, forbid is the last statement INSIDE each with block, so reading_model's gc.collect / empty_cache actually frees the model"
metrics:
  completed: 2026-10-05
  tasks: 3
  files: 2
---

# Phase 39 Plan 05: E6 driver part 2 Summary

`run()` scores in two passes on fakes. The gate pass scores every committed cell through both the
pinned `value_span_nll` and the D-30 copy; ranks go through `phase38_rank.gate_reading`, and a rank
mismatch or a bitwise inequality stops the run as GATE_FAILED. The work pass loads each reading
once and writes one write-once sidecar per reading. The whole run sits between one ledger start
line and one end line. On top of that: a rehearsal identity that pins the prereg's sha256 before
the first score, the DR-01/02/03 fixes, and six AST censuses.

Requirements: this plan contributes to CTX-02; the orchestrator ticks requirements at phase close.

## Commits

| Task | Commit | What |
|------|--------|------|
| 1 | 57fd4b0 | run(): gate pass with the D-30 bitwise STOP, work pass, write-once sidecars, ledger lines, DR-01 |
| 2 | bfa80ad | DISCLOSED_MODULES, record_rehearsal (DR-02), rehearsal_disclosure, preflight identity / D-27 / DR-03 |
| 3 | 79764fd | AST censuses (instruments, os.replace + sampler, caps keywords, per-token, ledger calls, skips) |

## RED, then GREEN (as printed)

- Task 1 RED: `9 failed, 5 passed, 55 deselected in 3.69s` (`AttributeError: module
  'phase39_ctx' has no attribute 'run'`). GREEN: `-k "run or gate or crash or partial"` `12
  passed, 57 deselected in 12.00s`; whole file `69 passed in 22.92s`.
- Task 2 RED: `-k "rehearsal or preflight"` `4 failed, 39 passed, 31 deselected in 11.39s`;
  widened to `-k "rehearsal or preflight or identity"` `6 failed, 39 passed, 29 deselected in
  11.64s` (`AttributeError: ... 'rehearsal_identity_path'`; `test_preflight_alone_writes_nothing`
  red on the new `rehearsal_disclosure` key). GREEN: `45 passed, 29 deselected in 15.44s`; whole
  file `74 passed in 26.98s`.
- Task 3 (`type="auto"`, no RED phase): `-k "ast or census or skips"` `6 passed, 74 deselected in
  1.92s`. Every census also has a planted red leg, and each passes.

## Acceptance lines (as printed)

- Task 3 verify: `tests/test_phase39_ctx.py tests/test_phase39_prereg.py
  tests/test_phase14_scoring.py tests/test_phase21_sc5.py tests/test_lora_inject.py
  tests/test_phase25_driver.py tests/test_phase36_ledger.py`: `276 passed in 47.17s`. `ruff check
  .`: `All checks passed!`. `ruff format --check .`: `358 files already formatted`.
- After the Task 3 commit: `tests/test_phase25_driver.py` (the os.replace census) `24 passed in
  1.86s`. `tests/test_phase39_ctx.py tests/test_phase14_scoring.py tests/test_lora_inject.py
  tests/test_phase21_sc5.py tests/test_phase25_driver.py tests/test_phase36_ledger.py` `208 passed
  in 32.58s`.
- `git status --porcelain -- scripts tests results ledger`: empty. `find data -maxdepth 1
  -name 'phase39_ctx_*'`: nothing. `phase39_rehearsal.json` was absent before and after the
  tests. `git diff --quiet 9366134 -- scripts/phase39_prereg.py tests/test_phase39_prereg.py`:
  unchanged. `shasum -a 256 scripts/phase39_prereg.py`:
  `4355b88024b41463daef9b17285246e74b7577988cd95c01e33d293594858297`.
- The `== 10` / `!= 10` grep on tests/test_phase39_ctx.py: no match. The full suite was not run
  (orchestrator override).

## Fake-run ledger lines and sidecars (asserted by the tests, tmp roots only)

- Ledger: one `start` and one `end` line for `v6/39/E6/ctx`. The end line has front `E6` and
  record `results/phase39_ctx.json`. This holds on SCORED and on both GATE_FAILED kinds.
- After a crash at the third reading, the ledger holds a lone `start`. `phase36_ledger.reconcile`
  then adds `lost` with `LOST_FLAG`. The k0 and k8 sidecars stay byte-identical, and a new
  preflight refuses on `phase39_ctx_gate.json exists`.
- Sidecars on the two-reading rehearsal shape: `phase39_ctx_gate.json`, `phase39_ctx_k0.json`,
  `phase39_ctx_k78.json`, `phase39_ctx_run.json`. The full shape writes all eight reading
  sidecars, and each holds 216 questions.
- Gate copy equality: on the full shape, `cells_compared` = 8 × 56 and `cells_equal` = 8 × 56.
  With one ulp off at k16/street, `cells_equal` is one less and `unequal` = `[["k16", "street",
  <candidate>]]`.

## What exists now

- `run(*, root, ledger_path, heartbeat_path, device, readings, slots, rehearsal_identity)`
  returns `"SCORED" | "GATE_FAILED"`. The order is:
  1. Partial-shape / DR-01 refusals.
  2. preflight.
  3. The DR-02 slice check.
  4. The ledger start line.
  5. A beat.
  6. `record_rehearsal`.
  7. The heartbeat thread.
  8. The gate pass and the gate sidecar.
  9. If the gate passed, the work pass: one sidecar per reading, written before the next reading
     loads.
  10. The run sidecar, then the ledger end line.
- Gate sidecar keys: `{run_id, readings, slots, rows, cells, copy_equality, passed}`.
- Reading sidecar keys: `{run_id, reading, anchor, questions}`. Each question carries `{index,
  slot, fact_id, tier, seed_index, realized_injection, references, minted}`.
- Run sidecar keys: `{run_id, status, readings, slots, entries, RUN_PROVENANCE_KEYS...,
  module_sha256_at_launch, reconstruction, gate2, gate_sha256, reading_sha256}`.
- `DISCLOSED_MODULES = ("scripts/phase39_ctx.py", "scripts/phase39_prereg.py")`.
  `rehearsal_identity_path()` is `_ROOT/data/phase39_rehearsal.json`, read at call time.
  `record_rehearsal(path, *, readings, slots)`.
- `rehearsal_disclosure(identity, *, launch_git_sha, launch_module_sha256)` adds
  `prereg_changed` and uses the statement "The CPU rehearsal (39-07) read <slots> under <n>
  readings, all their A2 entries, before the driver review and the MPS run (D-21, D-27)."
- preflight on the real root refuses when the identity is missing (D-21/D-27), malformed (DR-03)
  or has prereg drift (D-27, naming Rafael's ruling). It then computes the disclosure once and
  returns it.

## Deviations from Plan

### Auto-fixed / adjusted

**1. [Rule 2 - Correctness] The DR-02 refusal runs before the ledger start line.** The plan
places the slice check inside `record_rehearsal`, which runs after the start line. A refusal there
would leave an open start, against D-03 ("every refusal before the start line"). A shared
`_kept_identity(path, *, readings, slots)` now runs in `run()` before `append("start")`, and
`record_rehearsal` reuses it. The test proves a different slice refuses with no ledger and no
heartbeat file.

**2. [Rule 2 - Correctness] A malformed identity refuses with SystemExit.** The checks are: a
dict, exactly the five keys, and `module_sha256` over DISCLOSED_MODULES. Without them,
`identity["module_sha256"][PREREG_FILE]` on `{}` would raise KeyError. The test covers `{}`, an
empty `module_sha256`, and a list.

**3. preflight returns `rehearsal_disclosure`.** The value is None on a rehearsal root.
`test_preflight_alone_writes_nothing` now expects that key.

**4. [Rule 1 - Bug avoided] DI-04 placement.** `del model, tok, forbid` is the last statement
inside each `with` block, not after it. That way `reading_model`'s `finally` (gc.collect /
empty_cache) runs with no outside reference left.

**5. Retrofit not needed.** Only one existing test patches `_ROOT` and calls preflight:
`_refuse_cpu_on_the_real_root`. It refuses at the I/O-free device check, before the identity
check, so no stand-in identity was added to it. Every new real-root test writes its stand-in
identity with `record_rehearsal` under the rig.

**6. Extra planted legs.** Beyond the plan: a local `def draw_all`, a `top_p=` keyword, and a
`.get("suffix_nll_sum")` read in a `gate_reading` caller.

`import os` is still absent: `run()` does not need it. Prereg untouched. No gsd-sdk mutation
handler called. STATE/ROADMAP/REQUIREMENTS/PLAN files not edited.

## Known Stubs

None. The `__main__` dispatcher and `crosscheck` / `emit` / `report` are still missing; they
arrive in plans 06 and 07, as the plan sequence says.

## Self-Check: PASSED

- FOUND: scripts/phase39_ctx.py, tests/test_phase39_ctx.py
- FOUND: 57fd4b0, bfa80ad, 79764fd
