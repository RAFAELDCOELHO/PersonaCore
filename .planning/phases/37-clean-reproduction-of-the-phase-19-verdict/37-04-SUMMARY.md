---
phase: 37-clean-reproduction-of-the-phase-19-verdict
plan: 04
subsystem: reproduction
tags: [repro-03, r1b, mps-driver, ledger, launchagent, one-attempt]
requires:
  - 37-01 phase37_prereg (R1B_RECORD, R1B_ARM_RECORD, RECORD_GLOB, ENTRIES r1b_scope / not_replicated_rule, R1B_TOLERANCE_AND_REPLICATED, prefix_decision, replicated, draw_identity, nontarget_context, NONTARGET_FLOOR, R1B_COST_HOURS, R1B_COST_CAP_HOURS)
  - 37-02 phase37_routes (select_target_prefix, rederive)
  - scripts/phase36_ledger.py (run_id, append, read_ledger, require_launch, reconcile, HEARTBEAT_PATH)
  - scripts/phase25_run.py (beat, start_heartbeat, atomic_write_json)
provides:
  - scripts/phase37_r1b.py — preflight, run, build_record, emit, main, RUN_ID ("v6/37/R1b/replica"), FRONT, LAUNCH_PATHSPEC, MODULES, run_sidecar
  - artifacts/com.personacore.phase37.r1b.plist — the unattended MPS LaunchAgent for the one R1b attempt
  - tests/test_phase37_r1b.py — 30 CPU tests, device work stubbed, tmp_path ledgers/heartbeats/roots
affects: [37-05 (prereg freeze: nothing R1b needs is missing), 37-06, 37-07 (the real launch)]
tech-stack:
  added: []
  patterns: [phase36_probe.run_front ledger/heartbeat shape, erasure_kstar_run.measure adapter-sha-before-and-after, sidecar-then-end-line-then-emit]
key-files:
  created:
    - scripts/phase37_r1b.py
    - artifacts/com.personacore.phase37.r1b.plist
    - tests/test_phase37_r1b.py
  modified: []
decisions:
  - "The sweep model is released by rebinding (model = artifact = None), not `del`: the dialogue_ppl lambda closes over `model`, and `del` in the enclosing scope is ruff F821"
  - "The post-arm adapter SHA-256 check runs in both D-07 branches (also when the arm is skipped); it is cheap and the sweep also read the adapter"
  - "committed_comparators keys come from p19run.TARGET_CURVE_PATH and pin.arm_record_path('erased'); the test proves they equal phase37_prereg.CURVE_RECORD / ERASED_RECORD"
requirements-completed: []  # REPRO-03 is ticked by the orchestrator at phase close, not by this plan
metrics:
  duration: "~25 min"
  completed: 2026-10-03
  tasks: 2
  files: 3
---

# Phase 37 Plan 04: R1b driver and LaunchAgent Summary

`scripts/phase37_r1b.py` is the R1b replica driver. It runs every refusal before the ledger start line. It re-derives the prefix through the defect-E wrapper, lets `prefix_decision` gate the erased arm (D-07), writes the gitignored sidecar before the ledger end line, and emits a write-once record. That record's verdict comes only from `prereg.replicated(routes.rederive(replica))`. Everything was tested on CPU with the device work stubbed. Nothing ran on MPS, nothing was launched, and no real ledger, results or data file was written.

## Consumer-test numbers (emit fed the real committed arm)

`test_emit_on_the_committed_arm_reads_replicated` copies the bytes of `results/phase19_arm_erased.json` to `tmp_path/results/phase37_r1b_arm.json` and runs `emit`:
- verdict `REPLICATED`, replica_verdict `FAILURE`;
- draw_identity differing_completions 0 and differing_entries 0.

`test_run_on_the_committed_order_replicates` runs the full `run()` with the arm stub copying the same bytes:
- every `comparison.per_key[*].abs_diff` is 0;
- `n_completions` = 216 x 48, computed from the record in the test;
- positions_moved 0;
- the arm was called once with `("erased", "mps", components = committed prefix as tuples, record_path = tmp_path/results/phase37_r1b_arm.json)`;
- `require_launch("R1b")` was called once, before the tmp ledger file existed;
- the ledger reads `start`, `end` for `v6/37/R1b/replica`, front `R1b`, phase 37, and the end record is `results/phase37_r1b.json`;
- `provenance.run` holds exactly git_sha, device `mps`, torch_version, started_utc and finished_utc;
- `refuse_if_dirty` saw `LAUNCH_PATHSPEC` and then the emit pathspec, which excludes exactly the two R1b records.

`test_emit_on_a_shifted_arm_reads_not_replicated_with_context` adds 0.05 to `dialogue_ppl.adapter_on`:
- verdict `NOT_REPLICATED`, with destroyed_pct `within` False;
- `nontarget_context` has criterion False, noise_floor == `NONTARGET_FLOOR`, and slots == `pin.GATED_NONTARGET_SLOTS`.

D-07 divergence:
- k = 79 (the committed prefix plus one address from `pin.component_index()` outside it): the arm is never called, the verdict is NOT_REPLICATED, there is no `comparison`, `sweep` is present, and the ledger has start and end.
- k = 78 with one address swapped: the same outcome, with one address in each set difference.
- Reversed order: the arm runs on the reversed list, positions_moved equals the count computed in the test, and the verdict is REPLICATED.

D-11:
- A sweep that raises `RuntimeError` leaves an open start and no sidecar.
- A second run raises `SystemExit` (D-11) with the ledger unchanged.
- After `reconcile` on the tmp paths (lost line), a third run still raises `SystemExit`.
- Six preflight refusals each write no ledger line and no heartbeat: R1B_RECORD exists, R1B_ARM_RECORD exists, the sidecar exists, the device is cpu, the adapter SHA mismatches, and `require_launch` raises.

## RED output

Task 1, before the module existed:

```
tests/test_phase37_r1b.py:47: in <module>
    import phase37_r1b  # noqa: E402  (same; never aliased — _untested_functions counts by name)
E   ModuleNotFoundError: No module named 'phase37_r1b'
ERROR tests/test_phase37_r1b.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.92s
```

GREEN: 26 passed in 3.34 s on the first run of the module. After Task 2, 30 passed.

## Verification

- Plan verify set (`test_phase37_r1b test_phase37_routes test_phase37_prereg test_phase37_r1a test_phase35_prereg test_phase36_ledger test_phase36_budget test_phase19_erasure test_lora_inject test_phase14_scoring test_phase23_ctrl test_phase20_correction test_phase25_driver test_phase21_sc5`): **545 passed in 87.37 s**.
- After both commits, `test_phase25_driver test_phase21_sc5 test_phase37_r1b`: 58 passed.
- `ruff check .`: "All checks passed!". `ruff format --check .`: "346 files already formatted".
- `plutil -lint artifacts/com.personacore.phase37.r1b.plist`: OK.
- `git status --porcelain -- results ledger` is empty, `git ls-files 'results/phase37_*'` prints nothing, `ls data/phase37_r1b_run.json` gives "No such file or directory", and `results/phase37_*` matches nothing on disk.
- The phase37 AST gates (forbidden callees, `run_erasure_arm` only with `record_path`, `render_verdict` only in `rederive`) and the slot census now scan `scripts/phase37_r1b.py`, and both are green.

## What the driver needed from the prereg

Nothing was missing. Every name R1b reads already exists in `phase37_prereg` as committed by 37-01, so no change to `scripts/phase37_prereg.py` is needed before 37-05 freezes it. `replicated_definition` is a MappingProxyType whose value is a tuple. `dict(...)` of it serialises through `atomic_write_json`, and the tuple becomes a JSON list.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | 6e56e34 | feat(37-04): R1b driver — preflight, run (sweep -> D-07 -> arm), build_record, emit, main |
| 2 | dc64d0d | feat(37-04): R1b LaunchAgent plist, mirror test, zero skips, every-function census |

## Deviations from Plan

1. **[Rule 3 - Blocking] `del model, artifact` became a rebinding.** Ruff flagged F821 on `model` because the `dialogue_ppl` lambda closes over it and the enclosing scope `del`s it. `model = artifact = None` releases the references the same way.
2. **Extra tests beyond the behaviour list:** `preflight()` alone prints "PREFLIGHT OK" and writes nothing; `build_record` is called directly (no-arm branch: module_sha256 keys == MODULES, and committed_comparators hashes match the files); `main([])` and `main(["run", "extra"])` also refuse.
3. **TDD commit shape:** tests and module share the Task 1 commit, the same convention as 37-01..03, because a test-only commit would leave a collection error at that commit. The RED run is recorded above.
4. **Post-arm adapter check placement:** it runs in both D-07 branches (see decisions).

No plan premise turned out false when measured.

## Known Stubs

None.

## Threat Flags

None beyond the plan's register. T-37-17..T-37-22 are covered by the D-11 tests, the refusal ordering, the adapter checks, the explicit `record_path` under `results/phase37_*`, the verdict computed only through `prereg.replicated`, and the sidecar/emit split.

## Self-Check: PASSED

- FOUND: scripts/phase37_r1b.py
- FOUND: artifacts/com.personacore.phase37.r1b.plist
- FOUND: tests/test_phase37_r1b.py
- FOUND: 6e56e34
- FOUND: dc64d0d
