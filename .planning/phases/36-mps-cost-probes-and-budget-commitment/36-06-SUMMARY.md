---
phase: 36-mps-cost-probes-and-budget-commitment
plan: 06
subsystem: v6.0 MPS budget (COST-02)
tags: [budget, derive, high-bound, D-02, D-04, D-09, D-10, D-13, D-14, D-15, D-19, W2, W5, W6, W10, HALT, cut-table, fill-chain]
requires:
  - scripts/phase36_prereg.py (36-01): ENTRIES high_bound_rule, divergence_comparators, stop factors, cut_order, e4/e1 price entries, divergence/exceeds, PROBE_RECORDS
  - scripts/phase36_caps.py (36-02): BUDGET_RECORD, CAP_FIELDS, prove_budget_shape, tracked_files, owner_overruns
  - scripts/phase36_ledger.py (36-02): LEDGER_PATH, spent(fronts=("probes",)), read_ledger, run_id
  - scripts/phase36_probe.py (36-03..05): emit -> build_record -> _write_record, _e1_run, the record shapes
provides:
  - scripts/phase36_budget.py: comparisons, unit_prices, price_alternatives, apply_price_rulings, proposed_unit_caps, cut_table, derive, probe_record_paths, load_probes, load_historical, ledger_probes_seconds, committed_derive, chosen, derivation, budget_record, dry, later_records, emit, main (+ FORMULA, CAP_DERIVATIONS, SURFACED, CUT_QUESTIONS, HISTORICAL_RECORDS, RULING_KEYS)
  - tests/test_phase36_budget.py: _plant (planted sidecars -> the real phase36_probe.emit), _historical, _committed_inputs, the consumer fill chain on the CPU live run
affects: [36-07 (dry, the 25% read, the HALT/cut table), 36-08 (fill file + emit)]
tech-stack:
  added: []
  patterns: [planted run sidecars pushed through the real producer emit so a shape drift goes red, committed-blob reads for every budget input, ruling dict splatted into chosen / derivation / budget_record]
key-files:
  created:
    - scripts/phase36_budget.py
    - tests/test_phase36_budget.py
  modified: []
decisions:
  - "E1's per-checkpoint prices are their own keys (e1_k48_seconds / e1_k16_seconds), so the a2_draw_basis at_cap ruling replaces them in the E1 formula only; R1b keeps a2_k48_high"
  - "E4's e4_point_seconds is priced from the unscaled per-step price: E4 audits the v4.0 recipe at batch 8, so an E3.max_batch cap ruling never raises it"
  - "derive refuses an E6 record whose a2_context_from_e1 unit differs from the E1 record's a2_question_k48_high (E6 emitted beside another E1 run)"
  - "cuts e4_reserve, e2_seeds_to_3, e3_whole, r1b and e1_core take exactly 1 unit (the whole row); e6_anchor_adapters and e1_checkpoints take a count"
requirements-completed: []
metrics:
  completed: 2026-10-02
---

# Phase 36 Plan 06: the v6.0 MPS budget derivation, HALT and cut table, and the fill chain

`scripts/phase36_budget.py` turns the five committed probe records, the committed historical records
and the committed ledger into the Phase 35 budget contract. The contract covers front hours (the
high bounds), the stop line, S and the D-09 unit caps. When the fronts exceed 90 h, the output is a
HALT with the D-15 cut table instead. `derive` is pure and torch-free. `dry` prints every number and
writes nothing. `emit` writes `results/phase36_budget.json` only once the fill file exists and its
values re-derive from committed files.

Neither `results/phase36_budget.json` nor `scripts/phase36_budget_prereg.py` was written; plan 08
owns both. `requirements-completed: []`: this plan contributes to COST-02, and the orchestrator and
verifier decide the ticks.

## Tasks

| Task | Commit | What |
|------|--------|------|
| 1 | 383e251 | derive: the comparisons, unit prices (H1/H2/H3), ruling alternatives, proposed caps, front hours, stop line, cut table and cuts. Tests use planted records built through the real `phase36_probe.emit` |
| 2 | f056abd | committed-blob loaders, `ledger_probes_seconds` (W2), `committed_derive`/`chosen`/`derivation`/`budget_record`, `dry`, `later_records`, write-once `emit`, `main`. Tests cover consumer, HALT, dry, emit, recompute, ancestry and the census |

## What the budget computes (scripts/phase36_budget.py)

- **comparisons**: one row per `divergence_comparators` entry, built from the entry's own fields.
  - `e1_phase31_beside` is skipped because its probe_field is None.
  - `r1b_e1_k48` yields `#1` and `#2`, one per E1 run.
  - Minutes are converted to seconds (x 60).
  - The markdown row is read with the entry's regex. It gives 2.1 min, and the test asserts 126 s.
  - Linearity compares `t_max_steps.loop_seconds` with `(steps ratio) x t_step_budget.loop_seconds`.
  - `e2_training_context` compares the max rep `outer_seconds` with the max `per_seed[*].training_seconds`. It is ungated.
- **unit_prices** follow the plan's formulas. Every price is proved finite and >= 0.
  - `e4_point_seconds = e3_overhead_high + STEP_BUDGET x e3_per_step_high + e4_canary_seconds`. The canary term comes from `results/phase26_canary_sources.json` (the test asserts the record value). It is stated as NOT re-measured.
- **price_alternatives** are computed from the same records. The test proves that `a2_draw_basis at_cap` uses `at_cap_seconds_spread["max"]` (43 s on a planted run whose median is 42 s); it is `None` when neither run has an at-cap draw. `spread_scaled` and `probe_scaled` follow the plan's formulas.
  - `apply_price_rulings` validates each key and value against `high_bound_rule.ruling_alternatives`.
- **derive** runs the checks in this order:
  1. It proves the five fronts, `device == PROBE_DEVICE`, every `HISTORICAL_RECORDS` path and a finite `probes_spent_seconds >= 0`.
  2. It refuses each gated exceed that has no finding (`D-02/D-04: investigate BEFORE the budget`).
  3. It applies the price rulings and proves the caps: CAP_FIELDS keys, counts, S >= 3, E2 adapters == 2, `max_steps <= 800`, and `max_batch` above the probed batch only with `cap_rulings["E3.max_batch"]`.
  4. It applies the ruled cuts, then computes `front_hours = seconds / 3600` with `total = math.fsum`.
  - The stop line is `min(1.5 x total, 90)` when the total fits. Otherwise the stop line is None and derive returns the cut table plus `overflow_hours`.
- **cut_table** keeps the seven rows in cut_order, with `r1b` and `e1_core` last. Each row carries `{id, unit, hours_per_unit, max_units, hours_saved_max, question_lost}`. A row with 0 units is omitted, so no S < 3 row exists. The `e1_core` hours are E1 after the `e1_checkpoints` row's units, so rows never double-count.

## Verification (output as printed)

- Task 1 verify, `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_phase36_budget.py -k "derive or divergence or halt or cut" -rs`: **33 passed, 1 deselected in 2.92s**, 0 skipped.
- `tests/test_phase35_prereg.py tests/test_phase36_prereg.py -k census`: **5 passed, 100 deselected**.
- The torch-free subprocess (`test_derive_runs_without_torch`) printed `True False`, i.e. fits and `'torch' in sys.modules` is False.
- `tests/test_phase36_budget.py` in full: **58 passed in 20.61s**. The consumer test took 14.28 s (the five-front CPU live run).
- The plan's verification set plus the Task 2 verify set (`tests/test_phase36_budget.py`, `test_phase36_caps.py`, `test_phase36_ledger.py`, `test_phase36_prereg.py`, `test_phase36_probe.py`, `test_phase35_prereg.py`, `test_phase23_resume.py`, with `-rs`), run on the clean tree after commit f056abd: **385 passed in 165.35s**, 0 skipped.
- The census set (`tests/test_phase21_sc5.py`, `test_lora_inject.py`, `test_phase21_unit_continuation.py`, `test_phase14_scoring.py`, `test_phase31_probe.py`, `test_phase31_budget.py`, plus the seven single census tests 36-05 listed): **144 passed in 49.55s**.
- `ruff check .` printed "All checks passed!" and `ruff format --check .` printed "337 files already formatted" (the `make lint` equivalent).
- `.venv/bin/python scripts/phase36_budget.py dry` on the real tree exited 1 with `[phase36_budget] probe records missing for fronts ['e1', 'e2', 'e3', 'e5', 'e6'] (['results/phase36_probe_e1.json', ...]): the budget prices five COMMITTED probe records`. `git status --porcelain` showed only the pre-existing ` D .claude/scheduled_tasks.lock`.
- `ls scripts/phase36_budget_prereg.py` failed with "No such file or directory", and `git ls-files 'results/phase36_*' | wc -l` printed 0.
- The `(?:==|!=)\s*10(?![0-9_])` count in tests/test_phase36_budget.py is 0. One `== 10.0` was caught before the Task 1 commit and rewritten.
- Mutation checks (each mutant applied, run, then restored; never committed). Each one turned at least one test red:
  - at-cap median instead of max;
  - the probes front minus the lost attempt;
  - the beside row compared;
  - the divergence refusal removed;
  - H2 block mean instead of the block max;
  - `spent(fronts=None)`;
  - the HALT refusal removed;
  - the phase >= 37 precede refusal removed;
  - the markdown read as JSON;
  - the results/ ruling-path refusal removed.
- Nothing ran on MPS. `tests/test_phase25_venue.py` was not run (orchestrator instruction).

## Commands for 36-07 and 36-08

These are read from the code and were not run against probe records, because none exist yet.

- **Preconditions for dry:** `phase36_probe.py emit-all` has committed `ledger/v6_mps_ledger.jsonl` and the five `results/phase36_probe_*.json`. `dry` refuses an untracked ledger, because the probes front is read from the COMMITTED ledger blob (W2).
- **Dry budget:** `.venv/bin/python scripts/phase36_budget.py dry`
  - It prints, as `[phase36_budget] <label>: <json>` lines: `inputs`, one `comparison` line per row, `unit_prices`, `unit_caps`, `cap <Front.name>`, `front_hours`, `total_hours`, `stop_line_hours`, `e2_seed_count`, `surfaced for Rafael` (12 items), and `ruling <name>=<choice>` for BOTH choices of each of the three ruling alternatives, with front_hours and total.
  - It then prints `E3 hours at recipes 4` and `E3 hours at recipes 5`, `E3 max_batch`, and finally `[phase36_budget] FITS` or `[phase36_budget] HALT: <x> h over the 90 h ceiling ...` followed by one `cut` line per row.
- **The 25% read:** the `comparison` lines, each with `{id, gated, probe_seconds, historical_seconds, divergence, exceeds}`. These are printed BEFORE derive runs.
  - If a gated row exceeds, dry raises after the table with `<id>: probe ... diverges ...%, above divergence_tolerance. D-02/D-04: investigate BEFORE the budget, then pass the written finding as divergences_investigated['<base id>']`.
- **Rulings:** `.venv/bin/python scripts/phase36_budget.py dry --ruling <scratchpad>/ruling.json`. The file is JSON whose keys are a subset of `unit_caps, cuts, divergences_investigated, price_rulings, cap_rulings, approved`. It is refused under results/, and unknown keys are refused.
  - Example: `{"divergences_investigated": {"r1b_e1_k48": "<finding>"}, "price_rulings": {"a2_draw_basis": "at_cap"}, "cuts": {"e4_reserve": 1}}`.
- **Fill file (plan 08, after Rafael's approved):** `scripts/phase36_budget_prereg.py`. It must be a plain `import phase35_prereg` with exactly one module-level `V6_BUDGET_AND_STOP_LINE = phase35_prereg.fill(...)` whose call is the whole value:
  ```python
  import phase35_prereg
  import phase36_budget
  RULING = {..., "approved": "<Rafael's words>"}
  PATHS = phase36_budget.probe_record_paths()
  CHOSEN = phase36_budget.chosen(PATHS, **RULING)
  V6_BUDGET_AND_STOP_LINE = phase35_prereg.fill(
      "v6_budget_and_stop_line", **CHOSEN, input_records=PATHS,
      derivation=phase36_budget.derivation(CHOSEN, PATHS, **RULING),
  )
  ```
  `chosen` refuses a HALT. `derivation` refuses a missing `approved`. `emit` reads `fill_file.RULING` and `fill_file.V6_BUDGET_AND_STOP_LINE` by those names.
- **Budget record:** commit the fill file first (leg (a) needs separate commits), then run `.venv/bin/python scripts/phase36_budget.py emit`. It writes `results/phase36_budget.json` and does not commit it. It refuses, in this order:
  - an existing output;
  - a dirty tree (`("scripts", "src", "results", ":(exclude)results/phase36_budget.json")`);
  - an untracked or changed fill file;
  - any tracked record named by a phase >= 37 ledger end line.

  It then re-derives the budget, proves it equal to `V6_BUDGET_AND_STOP_LINE`, and writes the record with `sources` and `provenance`. Commit the record in its own commit.

## Deviations from Plan

### Plan text vs code (the code wins; each one is measured)

1. **The at_cap alternative replaces separate E1 price keys.** The plan says the alternative replaces `a2_k48_high`/`a2_k16_high` "in the E1 formula ONLY". R1b also reads `a2_k48_high`, so a plain replacement would move R1b too. `unit_prices` therefore carries `e1_k48_seconds`/`e1_k16_seconds`, which default to the measured values, and the ruling replaces only those. The test asserts R1b and E6 are unchanged under at_cap.
2. **`cut_table` returns the list of rows.** `overflow_hours = total - CEILING` sits beside it in derive's output. The plan's own test indexes `[r["id"] for r in cut_table]`.
3. **Added helpers the plan does not list:**
   - `committed_derive(paths, *, tracked=None, approved=None, **ruling)` is shared by `chosen` and `emit` and skips the HALT check that `chosen` applies, so the HALT test can still read the cut table.
   - `_fit_value` holds the HALT refusal and the value extraction.
   - `later_records(tracked)` is the precede refusal; emit and the ancestry test both use it.
   - `_head_blob` is the committed-blob reader for the markdown and the ledger.
   - `_describe`, `_show`, `_prove_caps`, `_apply_cuts`, `_front_seconds`, `_h2`, `_at` and `_historical_seconds`.

   Every def is called in the test file, and the census is green.
4. **`chosen` accepts `approved` and ignores it,** so one `RULING` dict splats into `chosen`, `derivation` and `budget_record`.
5. **`budget_record` also writes `cap_derivations`,** one sentence plus a source per cap (D-09). Extra keys are allowed by `fields <= set(record)`.
6. **The test seam `_ledger_blob(tracked)` exists as named.** The untracked-ledger refusal sits in `ledger_probes_seconds` BEFORE `_ledger_blob` is called, so the patched seam cannot bypass it. The test asserts the seam is never reached on refusal.
7. **The consumer test calls `_fit_value(derive(...))`, not `chosen`.** `chosen` reads committed git blobs, and the CPU fixture records exist only in tmp. `chosen` is proven separately on the planted loaders.
8. **The emit happy path is tested with a planted fill module** (`sys.modules["phase36_budget_prereg"]`), with `FILL_FILE` pointed at the tracked, unchanged `scripts/phase36_prereg.py` and `_head_blob` stubbed. The real fill file is plan 08's.
9. **The planted-record tests build the E1 runs with the real `probe._e1_run`.** The E2/E3/E5/E6 stage dicts are planted in sidecar shape, then go through the real `phase36_probe.emit`. Real stage OUTPUT shape is covered by the consumer test's five-front CPU live run (`_live_run(root, None)`).
10. **The plan's verify commands use `.venv/bin/pytest`.** They were run as `.venv/bin/python -m pytest` (executor rules).

### Auto-added (Rule 2)

11. **derive checks E6's A2-context unit.** `unit_prices` refuses when E6's `a2_context_from_e1.a2_context_question_k48_seconds_high` differs from the E1 record's `max fmean(per_question_k48_seconds)`. The two must be the same number, because `phase36_probe.e6_a2_context_beside` computes it from the E1 sidecar. A mismatch means E6 was emitted beside a different E1 run. Tested.
12. **W10 scaling leaves E4 alone.** `e3_per_step_high` is scaled by `max_batch / probed batch` only after `e4_point_seconds` is computed, so E4 keeps the v4.0 batch-8 price (D-06: E4 audits the v4.0 recipe). A `max_batch` below the probed batch is never scaled down, which keeps the high bound. Tested.
13. **Whole-row cuts take exactly 1 unit.** `e4_reserve`, `e2_seeds_to_3`, `e3_whole`, `r1b` and `e1_core` refuse any other count. `e6_anchor_adapters` and `e1_checkpoints` take counts bounded at >= 0 and >= 1 respectively. Unit counts must be ints >= 1, not bools. Tested.

### Notes

- `HISTORICAL_RECORDS` excludes `results/phase31_probe_point.json`. It is recorded beside E1 and never an input, so it is never loaded or hashed by the budget.
- D-09's proposed `E6.entries` = 216 and `E5.sets` = 8 are READ from the records (`E1 configuration.questions`, `E5 configuration.slots`). `phase35_prereg.a2_corpus_entries()` has 216 entries (measured), so the MPS records will give 216. The CPU fixture gives 3.

## Known Stubs

None.

## Threat Flags

None. The threat register T-36-25..29 and T-36-41 is mitigated as planned:
- derive is pure over committed blobs and total == fsum exactly;
- the probes front is read from the committed ledger, with a lost-attempt test;
- cuts apply only from a ruling, and chosen refuses a HALT;
- the precede refusal and the ancestry test (natural RED) are in place;
- a gated exceed refuses without a finding;
- dry and HALT leave `results/phase36_*` unchanged (tested).

## Self-Check: PASSED

- `scripts/phase36_budget.py` and `tests/test_phase36_budget.py` exist and are committed.
- Commits 383e251 and f056abd are in `git log`.
