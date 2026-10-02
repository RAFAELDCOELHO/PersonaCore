---
phase: 36-mps-cost-probes-and-budget-commitment
plan: 02
subsystem: v6.0 MPS budget enforcement
tags: [ledger, unit-caps, D-09, D-11, D-12, D-13, D-19, torch-free]
requires:
  - scripts/phase36_prereg.py (36-01, frozen)
  - scripts/phase35_prereg.py public names (V6_MPS_FRONTS, V6_RESULT_PATHS, SLOTS, ENTRIES, seed_list)
  - scripts/phase30_points.py _tracked_json
provides:
  - scripts/phase36_caps.py (BUDGET_RECORD, CAP_FIELDS, SLOT_COUNTS, tracked_files, prove_budget_shape, committed_budget, check_unit_caps, counts_for, owner_overruns)
  - scripts/phase36_ledger.py (LEDGER_PATH, HEARTBEAT_PATH, EVENTS, LINE_FIELDS, STOPS, LOST_FLAG, NO_BEAT_FLAG, PENDING_FLAG, RECORD_CLOCK, run_id, append, read_ledger, prove_append_only, last_beat_since, open_runs, reconcile, spent, stop_checks, require_launch, rule, require_e4_first_point, report_rows, main)
affects: [36-03 probe driver, 36-06 probes pricing, 36-07 emit_all, 36-08 budget builder, Phases 37-43 launches]
tech-stack:
  added: []
  patterns: [append-only JSONL ledger, committed-blob reads via _tracked_json, ruling lines as the only stop lift]
key-files:
  created:
    - scripts/phase36_caps.py
    - tests/test_phase36_caps.py
    - scripts/phase36_ledger.py
    - tests/test_phase36_ledger.py
  modified: []
decisions:
  - "_write_line refuses to append onto a torn ledger tail (inspect by hand) instead of appending into it, which would turn the torn line into a torn MIDDLE line that read_ledger refuses forever"
  - "spent() refuses a record named by two end lines (double count): one end line per result record"
  - "require_launch returns {front, spent_seconds, total_seconds, lifted}; it writes nothing"
requirements-completed: []
metrics:
  duration: ~45 min
  completed: 2026-10-02
---

# Phase 36 Plan 02: Unit caps and the v6.0 MPS ledger Summary

Two torch-free modules that every MPS phase 37-43 imports. `phase36_caps` enforces the D-09 unit caps against the committed budget. `phase36_ledger` is the append-only milestone ledger. It closes lost runs from the last heartbeat since each attempt's start, or at 0 s with NO_BEAT_FLAG. It runs the D-13 stops, which only a matching ruling line can lift, and the D-19 check on the first E4 point.

`requirements-completed: []`: this plan contributes to COST-02. The orchestrator or verifier decides the ticks.

## Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | D-09 unit-cap contract + owner-file scan | 9a85f02 | scripts/phase36_caps.py, tests/test_phase36_caps.py |
| 2 | Ledger: append-only, lost runs, D-13 stops/rulings, D-19 | be81b77 | scripts/phase36_ledger.py, tests/test_phase36_ledger.py |

## Verification (real output)

- `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_phase36_ledger.py tests/test_phase36_caps.py tests/test_phase36_prereg.py tests/test_phase35_prereg.py` printed `184 passed in 23.08s` (clean tree, after both commits).
- `tests/test_phase35_prereg.py -k census` printed `4 passed, 84 deselected`.
- `tests/test_phase36_ledger.py -rs` printed `44 passed`, and `tests/test_phase36_caps.py -rs` printed `35 passed`. Neither file has any skips.
- These are the repo-wide scans that read scripts/*.py: test_phase14_scoring, test_phase17_stats, test_phase21_unit_continuation, test_phase23_ctrl, test_phase30_calibration, test_tokenizer_oracle, test_lora_inject, test_phase21_sc5, the phase20 verdict-caller test, the phase19 retention call-site test and the phase25 os.replace test. Run together with the files above, they printed `334 passed in 38.46s`.
- `ruff check .` printed `All checks passed!` and `ruff format --check .` printed `333 files already formatted`. Together these are the content of `make lint`.
- `git check-ignore -q ledger/v6_mps_ledger.jsonl` exits 1, so the ledger is not ignored. `git check-ignore -q data/v6_mps_heartbeat.jsonl` exits 0, so the heartbeat is ignored.
- **RED evidence:** both test files were collected before their modules existed and failed with `ModuleNotFoundError`. The B1 reconcile trio, the W3 relaunch, the three D-13 ruling tests and the `main` test then failed with `AttributeError: module 'phase36_ledger' has no attribute 'reconcile'` before `reconcile` was written. That is the natural RED.
- **Mutation check:** each of the following edits to `phase36_ledger.py` reddened the suite, failing between 2 and 4 tests. The file was restored byte-identical after each one.
  - `_lifted` ignores the front.
  - `_lifted` ignores the stop.
  - `_lifted` ignores the seconds.
  - `_lifted` ignores the last start.
  - Stop (a) exempts a 0-h front.
  - Stop (b) uses `>` instead of `>=`.
  - `last_beat_since` ignores `since_utc`.

## Deviations from Plan

The plan was followed. Its cited line numbers were all re-measured and hold: phase25_run `:286/:291/:298/:350`, phase30_points `:190`, phase25_watch `:274`, phase35_prereg `:768/:847/:955/:991` and loop.py `:915` (`wall_clock=step`). The changes below were added under Rules 1-3:

1. **[Rule 3] `phase36_caps.tracked_files()` (public).** It is the `git ls-files` default for `tracked=None`, and `committed_budget`, `spent`, `require_launch`, `rule`, `report_rows` and `prove_append_only` all share it.
2. **[Rule 2] Private helpers, each called directly by a test** (the CPU-test census counts every module-level def): `phase36_caps._is_count`, and in `phase36_ledger`: `_attempts`, `_closed_row`, `_committed_bytes` and `_state`. `_state` holds the shared front/budget/spent/stop-check logic of `require_launch` and `rule`.
3. **[Rule 2] `_write_line` refuses to append onto a torn tail.** `read_ledger` skips a torn LAST line, as the plan specifies. Appending after it would make it a torn MIDDLE line, which `read_ledger` refuses, and that would block the ledger permanently. So the append stops and names the file for inspection instead.
4. **[Rule 2] `spent()` refuses a record named by two end lines,** to prevent double counting. **Wave 3 must write exactly one end line per result record.**
5. **[Rule 2] `append` refuses an end or lost line whose front differs from its start's front,** and `check_unit_caps` refuses a call that carries no counts.
6. **Finding, not fixed (phase25_run is pinned):** `phase25_run.beat` appends without checking for a torn tail. After a crash mid-write, the next beat merges into the torn line and is lost; later beats parse fine. `last_beat_since` therefore under-counts a relaunched attempt by at most one beat. The test plants its torn tail after the real-writer beat for that reason.
7. **Plan premise measured false, with no effect:** `data/` is gitignored, but `data/phase23_run_state.json` is tracked (force-added). The heartbeat path is still ignored, as verified above.
8. **TDD commits:** the plan says to commit the two files per task, so each task is one `feat(36-02)` commit with no separate `test(...)` commit. RED was shown in the run output (see Verification).
9. Tests use `.venv/bin/python -m pytest` instead of the plan's `.venv/bin/pytest`, following the executor rules.

## Names wave 3 must use (probe driver writes ledger lines)

- **IDs and heartbeats.** `phase36_ledger.run_id(phase, front, unit)` returns `"v6/<phase>/<front>/<unit>"`. Heartbeats go to `phase36_ledger.HEARTBEAT_PATH` (`<repo>/data/v6_mps_heartbeat.jsonl`) through `phase25_run.beat(path, point=<run_id>, stage=..., shape=..., draw_index=...)` or `phase25_run.start_heartbeat(path, state)` with `state["point"] = <run_id>`. `last_beat_since` matches on `point == run_id`. Beat once right after the start line (T-36-06).
- **Ledger file.** The ledger is `phase36_ledger.LEDGER_PATH = "ledger/v6_mps_ledger.jsonl"`, a repo-relative str. The functions default to `_ROOT / LEDGER_PATH`, and every function takes `ledger_path=` for tests.
- **Line schema.** `LINE_FIELDS = (utc, event, run_id, phase, front, record, seconds, flag, stop, ruling)`, and fields an event does not use are None. `EVENTS = (start, end, lost, ruling)`. Each line is written as sort_keys JSON plus `"\n"`.
- **Before a launch.** Call `require_launch(front)`, which raises SystemExit on a cut front or an unlifted stop.
- **Writing lines.**
  - `append("start", run_id=, phase=, front=)` writes the start line.
  - `append("end", run_id=, phase=, front=, record=<path matching V6_RESULT_PATHS, e.g. phase36_prereg.probe_record("e1")>)` writes the end line. The front must equal the start's front, and each record may be named by only one end line.
  - Lost lines come only from `reconcile()` or `main(["reconcile"])`.
- **Fronts.** They are `phase35_prereg.V6_MPS_FRONTS = ("probes","R1b","E1","E2","E3","E4","E5","E6")`. The probes use front `"probes"`.
- **Record clock.** `RECORD_CLOCK = ("provenance","run")`: each record carries `provenance.run.started_utc`, `provenance.run.finished_utc` (ISO, parsed with `datetime.fromisoformat`) and `provenance.run.device`. `spent()` reads only that span, and only from tracked records. An untracked record counts end utc minus start utc with `PENDING_FLAG = "record not yet tracked"`.
- **Flags.** `LOST_FLAG = "sem registro de resultado"`. `NO_BEAT_FLAG = "sem registro de resultado; no heartbeat after its start (0 s counted)"`.
- **Spent hours.** `spent(tracked=None, *, ledger_path=None, fronts=None)` returns `{"by_front", "total_seconds", "rows"}`. 36-06 prices the probes with `fronts=("probes",)`. It refuses while an in-scope attempt is open.
- **Progress and rulings.** `report_rows()` / `main(["report"])` is the progress view during a run, and it never refuses. `rule(front, stop, text)` / `main(["rule","--front",F,"--stop",L,"--text",T])` is run only on Rafael's own written reply.
- **E4 first point.** `require_e4_first_point(seconds)` reads `budget["unit_prices"]["e4_point_seconds"]`, so **the 36-08 budget builder must write `unit_prices.e4_point_seconds`**.
- **Budget fields for 36-08.** The budget record must carry `front_hours`, `total_hours` (exactly `math.fsum(front_hours.values())`), `stop_line_hours`, `e2_seed_count` and `unit_caps`. `unit_caps` must hold exactly these `phase36_caps.CAP_FIELDS` keys:
  - `E1`: cells, checkpoints_per_cell, k48_confirms_per_cell, calibrations
  - `E2`: adapters, seeds, where seeds == e2_seed_count
  - `E3`: recipes, sigmas, max_steps, max_batch
  - `E4`: points
  - `E5`: sets, max_set_size, prefixes
  - `E6`: adapters, anchor_adapters, anchor_slots, entries, max_k
  - Every value is a non-negative int.
  - `BUDGET_RECORD = "results/phase36_budget.json"`.

## Known Stubs

None.

## Threat Flags

None. The new surface (the ledger file, `rule` writing ruling lines) is the register's T-36-05..09 and T-36-39, and each has a test.

## Self-Check: PASSED

- FOUND: scripts/phase36_caps.py, tests/test_phase36_caps.py, scripts/phase36_ledger.py, tests/test_phase36_ledger.py
- FOUND commits: 9a85f02, be81b77
