---
phase: 39-instrument-context-2-2
plan: 10
subsystem: E6 report, success criteria, phase close
tags: [report, sc-check, close]
requirements-completed: [CTX-01, CTX-02, CTX-03]
key-files:
  created:
    - results/phase39_ctx_report.md
  modified:
    - .planning/STATE.md
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md
---

# Plan 39-10 Summary — the E6 report published, SC1-SC4 shown, phase closed

Executed inline by the orchestrator. CTX-01..03 are ticked here, at phase close.

## Task 1 — render the report from the committed record

- Porcelain (scripts src results tests ledger) empty; `git ls-files results/phase39_ctx.json` lists
  it; no report on disk.
- `.venv/bin/python scripts/phase39_ctx.py report` →
  `REPORT /Users/juliorcoelho/PersonaCore/results/phase39_ctx_report.md`.
- `report == render_report(record)`; decomposition tables: collapse 48 rows, damage 48 rows (ruling
  f), k0 baseline 32 rows (8 slots x 4 readings).
- `test_instruments_unchanged_byte_for_byte`: `1 passed in 0.52s`; tests/test_phase39_ctx.py
  `129 passed in 61.99s`.
- From the report: collapse — INSTRUMENT_SUFFICIENT 5 of 9 disagreement cells (share
  0.5555555555555556), CONTEXT_SUFFICIENT 0 of 9, ALREADY_AT_K0 4 of 9, 48 cells, M2 0 of 0; damage —
  INSTRUMENT_SUFFICIENT 11 of 24 (0.4583333333333333), CONTEXT_SUFFICIENT 0 of 24, EITHER 4 of 24
  (0.16666666666666666), INTERACTION_ONLY 1 of 24 (0.041666666666666664), UNREACHABLE_AT_SIZE 8 of 24
  (0.3333333333333333), 48 cells, M2 0 of 0; REVERSE 0 and undecided 0 under both events.
  Sufficiency cells — collapse INSTRUMENT_SUFFICIENT: k64 person_name, pet_name, street; k78
  person_name, street. Damage INSTRUMENT_SUFFICIENT: k16 person_name; k32 person_name, street,
  house_number; k64 cat_name, street, house_number; k78 cat_name, street, birth_year, house_number.
  EITHER: k32 pet_name, k64 person_name, k64 pet_name, k78 person_name. INTERACTION_ONLY: k16
  pet_name. CONTEXT_SUFFICIENT: none.
  Copy sentence: "scored with the driver's copy of span_nll_from_ids (D-30); gate-1 equality: 448 of
  448". D-33 ties: no flips; exact tie k8/person_name G_q (INTACT by strict >). Rehearsal disclosure:
  rehearsal 7b32c41, launch 852e6b4, driver changed True, prereg changed False, seven fix commits
  (4f859b3 WR-01, 0cb1e04 WR-02, e706f95 WR-03, 98cd98d IN-06, 62c2653 IN-05, 6313ed9 IN-01 IN-03,
  3590057 IN-02) each with its subject as the reason.
- Not in the report (record and driver frozen), carried to the v6.0 milestone report by Rafael's
  rulings: the second CPU rehearsal (39-08 SUMMARY) and the 1/48-baseline note on four damage cells
  (39-09 SUMMARY).

## Task 2 — Rafael read the report and replied "approved" (2026-10-05)

## Task 3 — report committed alone; suite; SC1-SC4

- 86de12a results(39-10): `git show --name-only` = results/phase39_ctx_report.md only.
- Full suite on 86de12a: `4300 passed, 4 skipped, 83 warnings in 3224.78s (0:53:44)`, EXIT=0; zero
  new skips.
- SC1: last prereg commit 9366134 is an ancestor of the record's first-add parent (78d2605^)
  (`git merge-base --is-ancestor` true); `E6_ENTRY_SUBSET == tuple(range(216))` True;
  test_slot_ordering_is_green_on_the_real_repo, test_owner_fill_files_respect_the_caps_on_the_real_repo
  and the phase39 frozen/first-add/records-at-commit tests: `5 passed, 65 deselected in 9.39s`.
- SC2: record readings k0, k8, k16, k32, k64, k78, M2, adapter_off x 8 slots each; per cell R_a,
  rank (R_q: ranks, n1, median, rank_of_mean_nll, minted) and generation (G_a, G_q); gate rows 64 of
  64; copy equality 448 of 448.
- SC3: the "Instrument share and context share (CTX-03)" section is present with 24 collapse and 24
  damage table rows, every count "of <cells>" and "of <disagreement cells>".
- SC4: results/phase39_ctx.json added alone in 78d2605 after Rafael's approved (39-09);
  results/phase39_ctx_report.md added alone in 86de12a after his approved (39-10); the ancestry tests
  above pass.

## Task 4 — phase close by hand

See the close commit (STATE / ROADMAP / REQUIREMENTS by hand, zero gsd-sdk mutation handlers).

## Self-Check: PASSED
