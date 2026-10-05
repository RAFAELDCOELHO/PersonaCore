---
phase: 39-instrument-context-2-2
plan: 07
subsystem: E6 driver part 4 (CTX-02, CTX-03)
tags: [driver, report, cli, census, rehearsal, d-21, d-27]
requirements-completed: []
dependency-graph:
  requires: [39-06 (record keys, emit), 39-05 (run, rehearsal identity), 39-03 (prereg frozen at 9366134)]
  provides: [_table, _slots, _readings, _disclosure_lines, _scored_sections, render_report, _tracked_and_clean, report, main, the CPU rehearsal identity data/phase39_rehearsal.json]
  affects: [39-08 MPS run (the driver bytes are now the rehearsed ones), 39-10 report]
key-files:
  created: []
  modified:
    - scripts/phase39_ctx.py
    - tests/test_phase39_ctx.py
decisions:
  - "The report renders the 48 door cells per event from the record (no k0 cell). It gives M2 apart from the prefixes (with m2_label) and combined, REVERSE_DISAGREEMENT and the undecided cells in a section of their own, the k0 baseline table or its reason, and the D-33 audit from tie_audit with each flip and each exact tie named with its class by both formulas."
  - "The cost block is rendered as '- cost <key>: <value>', so its e6_projection_hours / e6_stop_hours lines stay distinct from the approval lines of the same name."
  - "The rehearsal ran on the committed driver 7b32c41; data/phase39_rehearsal.json pins that driver's sha256 and the prereg's (D-21, D-27). The driver must not be edited from here without a disclosed re-rehearsal decision."
metrics:
  started: 2026-10-05T13:55:35Z
  completed: 2026-10-05T14:12:00Z
  tasks: 2
  files: 2
---

# Phase 39 Plan 07: E6 driver part 4 Summary

The E6 driver is now complete: `render_report`, `report` and the `main` CLI. A CPU rehearsal on
the real checkpoints then ran the whole chain once (run, crosscheck, emit, report) into a scratch
root outside the repository. The real producer record went through the report, and the rendered
report equals `render_report(record)`.

Requirements: this plan contributes to CTX-02 and CTX-03; the orchestrator ticks requirements at
phase close.

## Commits

| Task | Commit | What |
|------|--------|------|
| 1 | 7b32c41 | render_report, report, main; report/main/census tests |
| 2 | none (by design) | CPU rehearsal; it wrote only the scratch root and the gitignored data/phase39_rehearsal.json |

## RED, then GREEN (as printed)

- **Task 1 RED.** `-k "report or main or census"`: `17 failed, 1 passed, 107 deselected in
  9.92s`. Causes: AttributeError on the new names, and the census reporting `render_report`,
  `report`, `main` and `_tracked_and_clean` missing. The one pass was
  `test_census_helpers_called_directly`, which calls only pre-existing helpers.
- **First GREEN attempt.** `2 failed, 17 passed`. Both were test-side issues:
  - The share assertion expected the context share at the start of the combined line.
  - `_scored_sections` was not yet called directly by a test (census).
- **After the fixes.** `-k "report or main or census or skips"`: `19 passed, 106 deselected in
  9.52s`.

## Acceptance lines (as printed)

- **Before the commit** (`tests/test_phase39_ctx.py tests/test_phase39_prereg.py
  tests/test_phase21_sc5.py tests/test_lora_inject.py tests/test_phase14_scoring.py`):
  `252 passed in 73.47s (0:01:13)`.
- **Lint.** `ruff check .`: `All checks passed!`. `ruff format --check .`: `358 files already
  formatted`.
- **Bogus command.** `.venv/bin/python scripts/phase39_ctx.py bogus; echo $?` printed `bogus
  exit=1`.
- **After commit 7b32c41:**
  - `tests/test_phase25_driver.py tests/test_phase36_ledger.py`: `69 passed in 3.61s`.
- **After the rehearsal, with data/phase39_rehearsal.json present:**
  - `tests/test_phase39_ctx.py tests/test_phase36_ledger.py`: `170 passed in 61.81s (0:01:01)`.
  - The plan's Task 2 verify printed `PLAN-VERIFY-OK`.
- **Real tree after the rehearsal:**
  - `git status --porcelain -- scripts src results tests ledger`: count `0`.
  - `find data -maxdepth 1 -name 'phase39_ctx_*'`: count `0`.
  - `data/phase39_*` holds only `data/phase39_rehearsal.json`.
  - The real ledger `ledger/v6_mps_ledger.jsonl` (mtime 2026-10-04 15:58:57) and heartbeat
    `data/v6_mps_heartbeat.jsonl` (mtime 2026-10-04 15:58:53) were untouched.
- **Prereg.** `git diff --quiet 9366134 -- scripts/phase39_prereg.py tests/test_phase39_prereg.py`:
  unchanged. `shasum -a 256 scripts/phase39_prereg.py`:
  `4355b88024b41463daef9b17285246e74b7577988cd95c01e33d293594858297`, equal to 39-03-SUMMARY's.
- The `== 10` / `!= 10` grep on tests/test_phase39_ctx.py found no match. The full suite was not
  run (orchestrator override).

## Rehearsal identity (D-21, D-27)

Read from `data/phase39_rehearsal.json` (gitignored), as written by `run()` before the first score:

```json
{"git_sha": "7b32c416a2ceaa105616c801575e9a2c630814e3", "module_sha256": {"scripts/phase39_ctx.py": "0a9dbf81d4719a8ca0e41d18246e759e699aa6523c7293017a17d9e6bb36c73b", "scripts/phase39_prereg.py": "4355b88024b41463daef9b17285246e74b7577988cd95c01e33d293594858297"}, "readings": ["k0", "k8", "k16", "k32", "k64", "k78", "M2", "adapter_off"], "slots": ["pet_name", "birth_year"], "started_utc": "2026-10-05T14:05:22.035241+00:00"}
```

- **Before launch.** HEAD was `7b32c41`. `shasum -a 256 scripts/phase39_ctx.py` gave
  `0a9dbf81d4719a8ca0e41d18246e759e699aa6523c7293017a17d9e6bb36c73b`, the same digest the
  identity pins.
- **Script and launch.** The script is `<scratchpad>/rehearsal39.py`. It calls each function with
  keyword values proved against `inspect.signature(fn)`. It ran detached under nohup, and I
  waited with a run_in_background poller.
- **Scratch root.** `<scratchpad>/rehearsal39`, holding:
  - a tmp `ledger.jsonl` and `heartbeat.jsonl`;
  - `data/` with the 11 sidecars: gate, run, cpu and 8 readings;
  - `results/phase39_ctx.json` and `results/phase39_ctx_report.md`.

### Log (as printed, scratch paths shortened to `<T>`)

```
PREFLIGHT OK 7b32c416a2ceaa105616c801575e9a2c630814e3 device=cpu readings=8 slots=2 entries=216 projection_h=0.7293568082878159 stop_h=0.7424221732238463 spent_E6_s=0.0
REHEARSAL RECORDED 7b32c416a2ceaa105616c801575e9a2c630814e3
RUN SCORED — next: crosscheck, then emit
STEP run SCORED wall_s=118.9
CROSSCHECK DONE <T>/data/phase39_ctx_cpu.json
STEP crosscheck wall_s=176.4
EMITTED SCORED <T>/results/phase39_ctx.json
STEP emit wall_s=177.2
REPORT <T>/results/phase39_ctx_report.md
STEP report wall_s=177.2
REHEARSAL_EXIT=0
```

Wall clock: 177.2 s end to end. The record's `cost.run_hours` (the run alone) is
`0.032523629444444445`.

### Tmp ledger lines

```
{"event": "start", "flag": null, "front": "E6", "phase": 39, "record": null, "ruling": null, "run_id": "v6/39/E6/ctx", "seconds": null, "stop": null, "utc": "2026-10-05T14:05:22.016952+00:00"}
{"event": "end", "flag": null, "front": "E6", "phase": 39, "record": "results/phase39_ctx.json", "ruling": null, "run_id": "v6/39/E6/ctx", "seconds": null, "stop": null, "utc": "2026-10-05T14:07:19.127142+00:00"}
```

### Record values (read from `<T>/results/phase39_ctx.json`)

- **Status and shape.** status `SCORED`; shape is 8 readings × `['pet_name', 'birth_year']`, with
  54 entries.
- **Gate 1.** All 16 gate rows are equal. Ranks as `(rank, committed, equal)`:

  | reading | pet_name | birth_year |
  |---|---|---|
  | k0 | (1, 1, True) | (1, 1, True) |
  | k8 | (1, 1, True) | (1, 1, True) |
  | k16 | (1, 1, True) | (1, 1, True) |
  | k32 | (1, 1, True) | (1, 1, True) |
  | k64 | (1, 1, True) | (1, 1, True) |
  | k78 | (2, 2, True) | (1, 1, True) |
  | M2 | (2, 2, True) | (1, 1, True) |
  | adapter_off | (4, 4, True) | (3, 3, True) |

  These are the plan's expected values: pet_name rank 2 at k78 and M2, 4 under adapter-off;
  birth_year 3 under adapter-off.
- **Copy equality.** `{'cells_compared': 120, 'cells_equal': 120, 'unequal': []}`. The record's
  `context_b_instrument` reads: "scored with the driver's copy of span_nll_from_ids (D-30);
  gate-1 equality: 120 of 120".
- **Gate 2.** passed `True`.
- **CPU cross-check.** device `cpu`, torch `2.7.1`. Differing ranks: gate 0 of 16, rq 0 of 432,
  minted 0 of 432. Taught suffix sums: `suffix_equality` `{'compared': 432, 'equal': 432,
  'unequal': []}`.
- **Other blocks.**
  - Baseline: `None`, reason "partial slots: baseline_table needs every slot".
  - Audit: flips `[]`, exact_ties `[]`, class_changes `[]`.
  - `modules_changed_since_launch`: `[]`.
  - Disclosure: `this_is_the_rehearsal: True` over the slice above.
- **Cost.** `setups_priced 8`, `setups_run 16`, `extra_setup_hours 0.0014170362945232127`,
  `projection_with_double_load_hours 0.7307738445823391`, `e6_stop_hours 0.7424221732238463`,
  `within_stop True`.

**The four readings** (R_q is n1 / questions; G_a is the unit and h/K; G_q is the answered count
and total/(27 K)):

| reading | slot | R_a | R_q n1 | median | rank of mean NLL | G_a unit | G_a h | G_q | G_q total |
|---|---|---|---|---|---|---|---|---|---|
| k0 | pet_name | 1 | 27/27 | 1 | 1 | 1 | 41/48 | 27/27 | 109/1296 |
| k0 | birth_year | 1 | 27/27 | 1 | 1 | 1 | 1/48 | 18/27 | 31/1296 |
| k8 | pet_name | 1 | 26/27 | 1 | 1 | 1 | 18/48 | 24/27 | 68/1296 |
| k8 | birth_year | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 14/27 | 24/1296 |
| k16 | pet_name | 1 | 24/27 | 1 | 1 | 1 | 2/48 | 18/27 | 23/1296 |
| k16 | birth_year | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 13/27 | 23/1296 |
| k32 | pet_name | 1 | 18/27 | 1 | 1 | 0 | 0/48 | 2/27 | 3/1296 |
| k32 | birth_year | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 14/27 | 24/1296 |
| k64 | pet_name | 1 | 11/27 | 2 | 2 | 0 | 0/48 | 0/27 | 0/1296 |
| k64 | birth_year | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 11/27 | 16/1296 |
| k78 | pet_name | 2 | 5/27 | 2 | 2 | 0 | 0/48 | 0/27 | 0/1296 |
| k78 | birth_year | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 8/27 | 10/1296 |
| M2 | pet_name | 2 | 0/27 | 5 | 5 | 0 | 0/48 | 0/27 | 0/1296 |
| M2 | birth_year | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 18/27 | 25/1296 |
| adapter_off | pet_name | 4 | 0/27 | 5 | 5 | 0 | 0/48 | 0/27 | 0/1296 |
| adapter_off | birth_year | 3 | 2/27 | 3 | 3 | 0 | 0/48 | 0/27 | 0/1296 |

**Class counts for the slice** (12 cells per event = 6 cell readings × 2 slots). These are a
rehearsal slice, not the E6 result:

| event | group | cells | disagreement | reverse | undecided | by_class (non-zero) |
|---|---|---|---|---|---|---|
| collapse | prefixes | 10 | 1 | 0 | 0 | INSTRUMENT_SUFFICIENT 1, NO_DISAGREEMENT 9 |
| collapse | M2 | 2 | 0 | 0 | 0 | NO_DISAGREEMENT 2 |
| collapse | combined | 12 | 1 | 0 | 0 | INSTRUMENT_SUFFICIENT 1, NO_DISAGREEMENT 11 |
| damage | prefixes | 10 | 4 | 0 | 0 | EITHER 2, INSTRUMENT_SUFFICIENT 1, INTERACTION_ONLY 1, NO_DISAGREEMENT 6 |
| damage | M2 | 2 | 0 | 0 | 0 | NO_DISAGREEMENT 2 |
| damage | combined | 12 | 4 | 0 | 0 | EITHER 2, INSTRUMENT_SUFFICIENT 1, INTERACTION_ONLY 1, NO_DISAGREEMENT 8 |

### The rehearsal report

The file at `<T>/results/phase39_ctx_report.md` equals `render_report(record)` (`True`), and every
GFM table in it parses (`_assert_gfm_tables`). Its headings, as rendered:

```
# Phase 39 — E6 instrument × context 2×2
## Status
## Approval and cost (D-11, D-26, D-30)
## Gate 1: committed anchor ranks and the copy's equality (D-18, D-30)
## Gate 2: committed A2 counts re-derived (D-19)
## The four readings per slot and adapter (D-13)
## Baseline at k0 (ruling f)
## Decomposition under collapse (D-15, D-16)
## Decomposition under damage (D-15, D-16)
## Instrument share and context share (CTX-03)
## Reverse disagreement and undecided cells (ruling e, IN-01)
## Drop-formula audit (D-33, descriptive)
## Common unit and per-draw rates (D-07, descriptive)
## Predicted vs observed hit rate (D-17, D-23c, D-29, descriptive)
## Adapter-off (D-11 i, descriptive)
## Minted sets under the full question at |R| = 8 (D-11 ii, D-26, descriptive)
## CPU cross-check (D-20, descriptive)
## Rehearsal disclosure (D-21, D-27)
## Not measured (D-12, D-23d)
## Limitations (D-22)
## Provenance
```

## Deviations from Plan

### Amendment-driven changes to the heading list (39-07 orchestrator_amendment)

1. **New section "## Baseline at k0 (ruling f)"**, between the four readings and the
   decompositions. It holds the `baseline_table` rows (slot × reading key, the k0 value, and the
   status under collapse and under damage). When the baseline is None it holds the record's
   `baseline_reason`.
2. **New section "## Reverse disagreement and undecided cells (ruling e, IN-01)"**, after the share
   section. Per event and group (prefixes, M2, combined) it gives the reverse and undecided counts
   "of <cells>" and undecided_by_class, then names each such cell, or states "No reverse
   disagreement and no undecided cell under <event>."
3. **Decomposition tables** cover the record's door cells: 48 per event on the real root, never k0
   and never adapter-off. They add a `disagreement` column (True / False / None).
4. **The share table lists every name in OUTCOMES**, REVERSE_DISAGREEMENT included, for each
   event × (prefixes, M2, combined). The M2 group is introduced by the record's `m2_label`.
5. **The D-33 audit is the record's `drop_formula_audit`** (tie_audit). The differing-count table
   is per (reading, slot, R_q/G_a/G_q). Flips and exact ties are rendered from tie_audit's
   [reading, slot, key] triples, each with `class_committed` / `class_exact`, and `class_changes`
   is listed. The driver never calls `phase38_prereg.drop_formula_audit`.
6. **Gate 2 has an `independent` column** (WR-01), with the source line under the table.
7. Both decomposition sections, the share section, the reverse/undecided section and the audit
   render the record's `*_reason` when the classification is None. On a SCORED record the
   heading list is therefore always the same.

### Other adjustments

8. **Extra helper `_scored_sections(record)`.** It holds the SCORED-only sections; tests call it
   directly (census).
9. **New test `test_render_report_other_branches_from_the_record`.** Beyond the plan, it plants a
   flip, a reverse disagreement, an undecided cell, a full baseline table and a None
   classification in copies of the fake record. `test_census_helpers_called_directly` calls
   `_kept_identity`, `_classified`, `_cost` and `_descriptive_block` directly; before this plan
   they were reached only indirectly.
10. **`_tracked_and_clean` follows phase38_rank** (`git diff --quiet HEAD -- rel`, staged changes
    included) rather than the plan's `git diff --quiet -- rel`.
11. **The CLI test was renamed** `test_main_the_cli_exits_non_zero_on_a_bogus_command`, so that the
    plan's `-k "report or main or census"` selects it.
12. **No commit for Task 2.** Task 2 writes nothing tracked, as the plan says.

Prereg untouched. No gsd-sdk mutation handler called. STATE/ROADMAP/REQUIREMENTS/PLAN files not
edited. No Obsidian note. scripts/phase39_ctx.py was not edited after the rehearsal identity was
written.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: scripts/phase39_ctx.py, tests/test_phase39_ctx.py, data/phase39_rehearsal.json,
  `<scratchpad>`/rehearsal39/results/phase39_ctx.json and phase39_ctx_report.md
- FOUND: 7b32c41
