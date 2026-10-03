---
phase: 37-clean-reproduction-of-the-phase-19-verdict
plan: 02
subsystem: routing
tags: [repro-02, erase-08, defects-a-e, ast-gates, byte-unchanged]
requires:
  - scripts/phase19_erasure.py (closed pin, imported unedited)
  - scripts/phase19_run.py (_pooled_rows, _order_normalised, CALIBRATION_CORRECTION_PATH, TARGET_CURVE_PATH, RESWEEP_PATH)
  - scripts/phase35_prereg.py (e1_condition_b_margin, R1A_ASSERTIONS)
  - scripts/phase19_floor.py (TARGET_FLOOR, NONTARGET_NOISE_FLOOR, DIALOGUE_PPL_NOISE_FLOOR)
provides:
  - scripts/phase37_routes.py: route_a, route_b, route_c, route_d, ROUTES, rederive, b_floor_from_replicate, select_target_prefix (ERASE-08)
  - tests/test_phase37_routes.py: A-E tripwires, single-route swaps, E recorder, byte-unchanged pin/gate, AST call gates over every scripts/phase37_*.py
affects: [37-03, 37-04, 37-05, 37-06, 41]
tech-stack:
  added: []
  patterns: [named route per published defect, routes mapping swappable per letter, AST call gates with alias resolution and planted non-vacuity]
key-files:
  created:
    - scripts/phase37_routes.py
    - tests/test_phase37_routes.py
  modified: []
decisions:
  - "The D tripwire feeds pin.render_verdict the routed gate inputs with only retention_ppl unrouted: the defects stack (C SystemExits, then A short-circuits to INCONCLUSIVE before (c)), so D cannot bite on a pin-only path"
  - "The call gates resolve from-import aliases for every forbidden name, not only report/_cmd_*: `from erasure_gate import erasure_succeeded as _ok; _ok()` is caught (planted snippet added)"
requirements-completed: []  # REPRO-02 is ticked by the orchestrator at phase close, not by this plan
metrics:
  duration: "~20 min"
  completed: 2026-10-03
  tasks: 2
  files: 2
---

# Phase 37 Plan 02: Phase 37 routing module Summary

`scripts/phase37_routes.py` routes each published Phase 19 defect through one named function (A-D reuse `phase19_run._order_normalised` / `_pooled_rows`; E is `select_target_prefix`). `rederive()` reaches the recorded FAILURE only through those routes and the single `pin.render_verdict` call. Swapping any one route back to the pin's own path makes `rederive` diverge on the committed record.

## Measured unrouted values (committed records, pin's own path, nothing planted)

Read from a `.venv/bin/python -c` run against `pin.arm_record_path("erased")` before any module existed:

| Letter | Unrouted call | Measured | Routed |
|---|---|---|---|
| A | `pin.zero_results_have_nll(erased)` | `False` (swap: verdict `INCONCLUSIVE`) | `True` |
| B | `pin.lock_erasure_floor(pin._calibration_rate())` | rate `0.8846153846153846` -> `0.2`, branch `ceiling` | `0.09107873950450847` (correction rate `0.0`) |
| C | `pin.nontarget_deltas(nontarget_rows(pre_erasure.per_fact), nontarget_rows(per_fact))` | `SystemExit: ... 'cand_cat_zibby' carries 13 questions against the pooled per-core-fact count 27 ...`; erased per_fact rows all 14 questions | target row 27 questions |
| D | `render_verdict(..., retention_ppl=[3.6709177253236867, 1000285])` | `TypeError` | `3.6709177253236867` |
| E | `reference_set_for_calibration("pet_name", target)` | \|R\| = 6, re-sweep k 120 | `reference_set_for` \|R\| = 8, k 78, prefix identical |

On D: the dialogue cap fails first (4.8511 > 4.5837), so `and` short-circuits and the `<=` on the list never runs. The TypeError comes from the reason's `:.6f` format string, as research P6 says. The `phase19_run.report()` docstring says "where the `<=` raises", and that is wrong for this record.

## Acceptance output

```
$ .venv/bin/python -c "...; d=r.rederive(...); print(d['k'], d['target_correct'], d['nontargets_beyond_margin'], repr(d['destroyed_pct']), d['verdict'])"
78 [0, 27] [7, 7] 77.6370113463966 FAILURE
['(a) target upper bound 0.0911 over 27 questions <= calibrated floor 0.0911', '(b) worst non-target degradation 1.000000 > k=2 x 0.148148 = 0.296296', '(c) dialogue PPL 4.8511 vs cap 4.5837; retention PPL 3.670918 vs cap 4.029000']
b_floor_from_replicate() = 0.14814814814814814

$ git diff --quiet 3ba3e2c HEAD -- scripts/phase19_erasure.py && git diff --quiet 23a830c HEAD -- scripts/erasure_gate.py; echo $?
0
$ ... print(inspect.signature(r.select_target_prefix))
(model, tok, device, artifact, *, fact, dialogue_ppl)
```

`git status --porcelain -- results` was empty both before and after the test runs.

## RED output

Task 1, before the module existed (the plain top-level `import phase37_routes` makes this a collection error, the same shape as 37-01's):

```
tests/test_phase37_routes.py:37: in <module>
    import phase37_routes  # noqa: E402  (same; never aliased — _untested_functions counts by name)
E   ModuleNotFoundError: No module named 'phase37_routes'
ERROR tests/test_phase37_routes.py
1 error in 1.11s
```

Task 2, before `select_target_prefix` existed: 12 failed, 37 passed. Ten of the failures were the wrapper tests (`AttributeError: module 'phase37_routes' has no attribute 'select_target_prefix'`). The other two were bugs in my own gate code, fixed before GREEN (deviation 3).

GREEN: `tests/test_phase37_routes.py` 50 passed. Plan verify set (`test_phase37_routes test_phase37_prereg test_phase35_prereg test_phase19_erasure test_phase19_correction test_lora_inject test_phase25_driver test_phase21_sc5`): 317 passed, 1 failed before the Task 2 commit. The failure was `test_phase25_driver.py::test_the_git_surface_gate_fires_on_a_planted_push`, the clean-tree probe, which saw the uncommitted ` M scripts/phase37_routes.py`. After the commit, `tests/test_phase25_driver.py` gave 24 passed. `ruff check .` "All checks passed!"; `ruff format --check .` "342 files already formatted".

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | 3596f32 | feat(37-02): routes A-D, rederive and the (b)-floor helper on the committed records |
| 2 | 55c924c | feat(37-02): defect E wrapper select_target_prefix (ERASE-08), byte-unchanged pin/gate, phase37 AST gates |

## Deviations from Plan

1. **The D tripwire is not pin-only.** The plan says the tripwire tests "call only the pin's own functions and pass today". D cannot: on a pin-only path C SystemExits first, and with C routed, A short-circuits to INCONCLUSIVE before (c) is reached. The D tripwire therefore takes `rederive(erased)["gate_inputs"]` and swaps only `retention_ppl` back to the pair. The error is still the pin's own TypeError on the committed pair.
2. **RED shape.** The plan expected the tripwires to pass during RED and only the routed and swap tests to fail. Because the plan requires a plain top-level `import phase37_routes`, the whole file is a collection error until the module exists. The per-letter unrouted values were measured separately with direct pin calls (table above).
3. **Two gate bugs caught in the Task 2 RED and fixed before commit:** (a) `_call_sites` reports module-scope calls as `None`, and sorting `None` against `str` raised a TypeError; these now sort as `"<module scope>"`. (b) The `from phase19_run import report as _r; _r()` plant was not detected. Alias resolution now applies to every forbidden name, and an extra plant (`from erasure_gate import erasure_succeeded as _ok`) proves it.
4. **Test layout.** The A-D swaps are one parametrized test with a checker per letter. Two small tests were added: `route_d` refuses a bare scalar, and `ROUTES` is read-only and exactly A-D.
5. **`requirements-completed: []`.** The plan's output section says `[REPRO-02]`. The orchestrator owns requirement ticking at phase close, so it is left empty here.

## TDD Gate Compliance

There are no separate `test(...)` commits. Each task's commit holds both the tests and the code, the same convention as 37-01, because a test-only commit would leave the tree with a collection error. Both RED runs were observed and are recorded above.

## Known Stubs

None.

## Threat Flags

None. The module reads committed JSON and writes nothing. T-37-07..T-37-11 are mitigated by the AST gates, the byte-unchanged test and the swaps that use the pin's own callables.

## Self-Check: PASSED

- FOUND: scripts/phase37_routes.py
- FOUND: tests/test_phase37_routes.py
- FOUND: 3596f32
- FOUND: 55c924c
