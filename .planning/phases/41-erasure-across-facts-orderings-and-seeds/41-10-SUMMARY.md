---
phase: 41-erasure-across-facts-orderings-and-seeds
plan: 10
subsystem: erasure-driver
tags: [phase41, e1, driver, emit, report, main, gates, erase-03, erase-06, erase-08, erase-09, erase-10, d-15, d-16, d-17, wr-01, wr-02, in-02, in-05]
requires: [41-09]
provides:
  - "phase41_erasure: build_record (verdicts, pair labels, summary, every declared reading, all through the frozen prereg), emit (write-once; real root: clean tree + every input tracked and clean)"
  - "phase41_erasure: render_report, report (write-once from a tracked, unmodified erasure record), main (preflight/run/emit/report)"
  - "tests: one real committed producer record (results/erasure_kstar_arm_k064.json) through run() -> real k48_confirm -> emit; the driver's AST/census gates; ERASE-08 byte-unchanged leg"
affects: [41-11, 41-12, 41-13, 41-14, 41-15, 41-16]
tech-stack:
  added: []
  patterns: [consumer fed a real producer record end to end through the real write paths (Phase 25 lesson), fakes bound to real signatures]
key-files:
  created: []
  modified: [scripts/phase41_erasure.py, tests/test_phase41_erasure.py]
decisions:
  - "build_record requires every prep unit whole; floors/bands default to phase41_floors_prereg (imported inside build_record) only on the real root — a rehearsal root must pass its own fills"
  - "a dropped (not re-run) cell reads NOT_RUN, with its ledger outcome beside the verdict"
  - "emit's real-root tracked-and-clean check covers FLOORS_FILE plus every record build_record read (record['inputs']), not a hand-kept list"
  - "variant / variant_decided_by read from the gradient calibration records (tracked), never from data/variant.json"
  - "d02_cpu_equality prediction is held/not held only when the gradient calibration records ran on cpu; on mps it is None (not measured by this run)"
requirements-completed: []
metrics:
  duration: "about 1.5 h"
  completed: 2026-10-08
---

# Phase 41 Plan 10: emit, report, main and the driver's gates Summary

`requirements-completed: []`: 41-10 writes the CPU emit and the report; no stage-1 or cell record exists yet, so no ERASE requirement is met.

The driver is complete. `build_record` turns committed records into the erasure record, and every verdict and reading in it comes from a frozen prereg function. `render_report` / `report` print that record, `main` dispatches the four commands, and gates keep the driver honest. The emit was tested on one real committed producer record fed through the real write paths.

## Commits

| Task | Commit | What |
|---|---|---|
| 1 | 0043ba2 | build_record, emit, _key; 5 tests (the real producer record, NOT_REACHED cell, the floors-file import, write-once and dirty refusals, no provenance.run) |
| 2 | 2faadef | render_report, _cell_section, _table, _counts, report, main; 21 tests (report labels, report write-once, main x3 groups, the full fake chain, 7 AST/census gates, ERASE-08 leg, helper census, no skips) |

## RED (tests first)

- **Task 1:** `-k "emit or build_record or not_reached_cell or run_provenance"` gave `5 failed, 107 deselected in 2.82s`, all AttributeErrors on `build_record` / `emit`. The producer rig itself (stage 1 through run(), the cell through run() with the real k48_confirm) ran up to the emit call.
- **Task 2:** the whole file gave `12 failed, 121 passed in 29.54s`:
  - AttributeErrors on `render_report`, `report` and `main`;
  - the bogus-CLI test with rc 0, because there was no `__main__` block;
  - the census test failing. My first helper test called the helpers through an alias (`d.`), which `_untested_functions` does not count. I rewrote it to call `phase41_erasure.<name>(` directly.

## Acceptance lines as printed

- `pytest tests/test_phase41_erasure.py -k emit_fed_a_real_producer_record -v` printed `tests/test_phase41_erasure.py::test_emit_fed_a_real_producer_record PASSED`. The test's own name does not contain `erasure_kstar_arm_k064`; its source does (`_K064`, 3 hits by grep).
- `grep -n "import phase41_floors_prereg" scripts/phase41_erasure.py` gave `2160:        import phase41_floors_prereg`, inside `build_record`. The AST test asserts that this is the only site and that there is no module-level binding of either fill name.
- `.venv/bin/python scripts/phase41_erasure.py bogus` printed the usage docstring and `rc=1`.
- `git diff --quiet 3787b9d -- scripts/phase19_erasure.py scripts/erasure_gate.py scripts/phase18_extraction.py` gave `diff_rc=0`.
- Plan verify (Task 2 list) on the committed tree:
  - Batch 1 covers phase41_prereg/erasure, 35_prereg, 37_routes, 14_scoring, 25_driver, lora_inject and 21_sc5. Batch 2 covers 23_resume.
  - `test_phase36_caps.py` + `test_phase36_ledger.py` gave `80 passed in 2.47s`.
  - Before the Task 2 commit, the same list gave `1 failed, 505 passed`. The only failure was the clean-tree probe `test_the_git_surface_gate_fires_on_a_planted_push`, which saw the uncommitted driver. It is green on the committed tree, inside Batch 1.
- `ruff check .` gave `All checks passed!`, and `ruff format --check .` gave `366 files already formatted`.
- `shasum -a 256 scripts/phase41_prereg.py` gave `11e432e479b9a97642e582083f3d0f01cfaa2834bde7f47682c3bbafab4a29a3`, the frozen digest. Neither the prereg nor its test was edited.
- Census greps:
  - `grep -c "train_arm("` gave 1 in the driver and 0 in the test.
  - The added lines have no `== 10` and no `ratchet_k`.
  - The `os.replace` / `inject_lora` hits are the planted strings of `test_no_os_replace_and_no_inject_lora`, as in Phase 40.
  - No `results/*.json` names phase41_erasure.
  - `find results data checkpoints -maxdepth 1 -name '*phase41*' | wc -l` gave 0.

## Census runs on the committed tree (HEAD 2faadef, clean except .claude/scheduled_tasks.lock)

These are the same two batches as 41-09 (its `census.sh`):

- **Batch 1** (31 files): `1367 passed in 276.86s`, B1_EXIT=0. That is 1341 + 26, where 26 is the new driver tests (107 -> 133).
- **Batch 2** (23_resume, 23_budget, 25_record, 25_promotion, 40_noise): `226 passed, 3 skipped in 138.90s`, B2_EXIT=0.
- `git status --porcelain` before and after both batches showed only `.claude/scheduled_tasks.lock`.

## What the tests prove

- **The real producer record, end to end (T-41-38, T-41-41).**
  - Setup:
    - Stage 1 runs through `run()` (41-08 write paths, fakes bound to real signatures).
    - Then the (pet_name, greedy, 1337) cell runs through `run()`. Its greedy ordering starts with `results/phase19_collateral_curve.json` ordered_prefix, and the K = 16 target count is zero only at 64.
    - The REAL `k48_confirm` runs, with the pin's arm writing `results/erasure_kstar_arm_k064.json` byte for byte at its `record_path`. D-13 is the committed Phase 40 seed-1337 block.
    - The floors and bands come from `phase35_prereg.fill(...)` with `floors_fill_inputs()` / `band_fill_inputs()` on the rig's stage-1 records, with `_REPO_ROOT` patched in a `monkeypatch.context` for the two calls only.
  - Results:
    - (a): upper == `wilson_upper_bound(0, 27)` == the floor, so (a) holds. That is WR-01's vacuity.
    - (b): the 7 non-pet_name slots are read against `phase40_a2_full_seed1337.json`.
    - (c): the gap is `4.920568428792842 - 4.573349214207799`, against the (1337, greedy) band.
    - The verdict equals `cell_verdict` recomputed in the test. It is **FAILURE, (b) and (c)**, with 6 non-targets beyond the margin.
    - The other 15 cells are NOT_RUN. The pair reads `não replicado`, "FAILURE na 1337, NOT_RUN na 2024".
    - The summary is over 8 pairs: `{"FAILURE + NOT_RUN": 1, "NOT_RUN + NOT_RUN": 7}`.
    - The D-27 per-fact counts equal each K = 16 record's.
    - D-18 rows, D-19 labels `["birth_year", "hometown"]`, D-14 with the v4.0 cap column (`sim`), D-20 comparison, and `greedy_1337_phase19_prefix` held True.
    - `variant_decided_by` is `cpu_rehearsal`.
- **NOT_REACHED cell.**
  - Verdict NOT_REACHED, `conditions` None, and empty failed/beyond lists.
  - Five reads with their ranks and target counts, five confirmations, and the D-09 sentence.
  - The pair text reads "NOT_REACHED na 1337, NOT_RUN na 2024".
- **Floors file.**
  - On a real-root rig with `floors=None`, build_record reads a faked `phase41_floors_prereg` from sys.modules; D-12 equals `d12_rows(floors)`.
  - A rehearsal root without fills refuses.
- **emit.**
  - It is write-once.
  - On the real root it refuses a dirty tree, then refuses untracked stage-1 records ("tracked and clean"), with nothing written either time.
  - With the check patched, it asks for FLOORS_FILE plus exactly `record["inputs"]`.
  - The record's provenance is `{emitted_utc, git_sha, module_sha256}`, with no `run`.
- **report.**
  - It refuses before emit.
  - On the real root it refuses an untracked record, then asks `_tracked_and_clean(ERASURE_RECORD)`.
  - It writes `render_report(record)` and refuses a second write, pointing at `scripts/_addendum.py`.
  - render_report is pure, with no double blank line. It prints every pre-registered label, the combinations, the table, hours, the D-08 end point and every prediction.
- **main.** Each command is dispatched with no arguments, cwd `_REPO`, and the call bound to the real signature. Anything else raises the docstring. The CLI exits non-zero on a bogus command.
- **Full fake chain.** preflight -> run stage 1 -> preflight (stage 2, all cells pending) -> run stage 2 (16 cells) -> emit -> report, all through signature-bound calls. Status is COMPLETE, all 16 cells are NOT_REACHED, and the summary is `{"NOT_REACHED + NOT_REACHED": 8}`.
- **Gates (T-41-40).**
  - Phase 37's `_call_failures` runs over every `scripts/phase41_*.py` with draw_all, reference_set_for_calibration and write_text removed from the forbidden set; the test first asserts all three were in it. Planted calls are caught: erasure_succeeded, `pin._cmd_cal_train`, run_erasure_arm without record_path, and a bare open.
  - Other checks:
    - os.replace and inject_lora;
    - the slot census;
    - no `check_unit_caps(k48_confirms_per_cell=...)`;
    - no typed {read_k, confirm_k, 27, GRID[-1], 288, the SEEDS} or margin / band edges / gaps / gap_noise_floor / E1 share / four prices / retention cap and floor (each read in the test);
    - no typed target name (`_typed_target_failures`, imported).

    Each check has a planted leg that fails.
  - ERASE-08: the pin's sha256 equals `results/phase36_probe_e1.json`'s pin. Neither the pin nor the gate has changed since its anchor, and each anchor commit did change its file.
  - The every-function census is now `[]`, including the 31 helpers 41-06..41-09 had left uncalled; none was dead. There is a planted untested-def leg and a no-skip leg.

## Deviations from Plan

1. **[Signature] `build_record` refuses `floors=None` / `bands=None` on a rehearsal root.** A tmp root defaulting to the real floors file would judge rehearsal cells against the real calibrations.
2. **[Rule 2] build_record checks its inputs.** It re-proves each cell's stop with `driver_stop` and `confirmation_failures`, and every K = 16 / K = 48 sha256 against the cell record. It requires every prep unit whole, because no floor or band exists without them.
3. **[Record] Extra keys.**
   - `outcomes` and `bands`.
   - `calibrations.condition_a`: the prereg's WR-01 text, verbatim.
   - `calibrations.prep_hours`: measured from the ledger rows. The priced 1.245 h is quoted inside that text, never recomputed.
   - `confirmation_hours` total.
   - `limits`: ENTRIES text for D-18/D-19/D-20/summary_line.
   - Per cell: `outcome`, `record`, `applied_ordering` and `m1`.
4. **[Test] The real producer record is placed by the real `k48_confirm`**, with the pin's arm faked to copy the bytes, rather than written into the tmp root by hand. This is the stronger form of the plan's "place ... at k48_record".
5. **[Test] Acceptance wording.** The `-v` output names the test, not `erasure_kstar_arm_k064`. The record path is named in the test source, and the test asserts the K = 48 file's bytes equal the committed record's.
6. **Report language.** The report is English prose with the pre-registered Portuguese labels verbatim. The limit sentences "não é teste estatístico" and "vazia no ponto de parada julgado" are in Portuguese as declared.

## Known Stubs

None.

## Threat Flags

None beyond the plan's register. T-41-38..41 each have a test listed above.

## Not verified

- Nothing ran on MPS, on real cells or on a real floors file. `phase41_floors_prereg.py` does not exist yet (41-13). Its import path is tested only with a faked module.
- On a real MPS run, `d02_cpu_equality` will read None, because the calibration gradients run on mps. Whether that prediction gets an observed value depends on the CPU rehearsal's own erasure record (41-11).
- The D-08 end point took the `exposure` branch: the adapter-off record has no `attack_family`. The `a2_rows` branch is unexercised.
- The report was rendered only from fake-chain and single-producer records. It has not been seen with a full set of judged cells.
- The Obsidian vault note was not written: this executor has no Obsidian MCP tool, so it is left to the orchestrator.

## Self-Check: PASSED

- FOUND: scripts/phase41_erasure.py, tests/test_phase41_erasure.py
- FOUND: 0043ba2, 2faadef (`git log --oneline -3`)
