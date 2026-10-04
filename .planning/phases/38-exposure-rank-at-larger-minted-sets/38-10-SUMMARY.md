---
phase: 38-exposure-rank-at-larger-minted-sets
plan: 10
subsystem: e5-report
tags: [report, RANK-02, RANK-03]
requirements-completed: []  # the orchestrator owns requirement ticks at phase close
key-files:
  created:
    - results/phase38_rank_report.md
commits: [7043e9c]
---

# 38-10 — E5 report published on Rafael's approved (run inline by the orchestrator)

## Task 1 — render and check

- Porcelain (scripts src results tests ledger) empty; record tracked; no report on disk.
- `.venv/bin/python scripts/phase38_rank.py report` -> `REPORT …/results/phase38_rank_report.md` (284 lines).
- `report == render_report(record)` (byte for byte). Sections in order: Status, Approval and cost
  (D-21/D-22/D-23), Gate (D-18, D-11a), A2 counts (D-13, D-14), Drop formula audit (D-33), Rank curves (D-15),
  Did the rank move before generation collapsed? (D-12, D-29, D-30), Numeric neighbour sensitivity (D-27),
  CPU cross-check (D-19), Rehearsal disclosure (D-34), Limitations (D-36), Provenance.
- Relation table: 64 rows (8 slots x 4 sizes x 2 events); "never collapsed within the grid" for cat_name,
  birth_year, house_number. Values as in 38-08-SUMMARY.md's table ("left the top eighth" never fires; moved
  fires for person_name 128/512 k78 AFTER/AFTER, pet_name 32-512 k64 SAME/AFTER, sibling_name 128/512 k32
  BEFORE/SAME, hometown 32 k78 AFTER/AFTER and 128/512 k16 BEFORE/AFTER, birth_year 32/128 k8 and 220 k32
  (rank_0 2) never-collapsed/BEFORE).
- D-33 rows: person_name 32, pet_name 8/16, sibling_name 16, hometown 8/16, street 16; "No damage event changes
  between the two formulas."; person_name k = 8 exact margin tie decided by D-14's strict >.
- D-34: rehearsal 91553d9 vs launch ccd5d7e; phase38_rank.py f887d437… -> 19ed9476… (changed), sizes file
  18f37b0b… (unchanged); commit 1e68330 with its subject as the reason.
- `test_instruments_unchanged_byte_for_byte` + tests/test_phase38_rank.py: 87 passed. Porcelain: only
  `?? results/phase38_rank_report.md`.

## Task 2 — Rafael approved

## Task 3 — commit, suite, SC1-SC4

- 7043e9c commits exactly results/phase38_rank_report.md. `git ls-files 'results/phase38_*'`: minting, rank,
  rank_report.
- Full suite at 7043e9c: `4103 passed, 4 skipped, 83 warnings in 2825.61s (0:47:05)`, EXIT=0 — no latent red.
- SC1: last commit of scripts/phase38_prereg.py d33986c < minting first add 7357577 < sizes first commit
  b2416ee (= its last) < rank first add d6984f4 < report 7043e9c (git merge-base --is-ancestor, strict);
  `test_slot_ordering_is_green_on_the_real_repo` passed.
- SC2: the report's relation section exists (64 rows); record reconstruction digests equal the committed
  sources — persona_adapter == phase19_collateral_curve adapter_in_sha256 True, components_sha256 ==
  phase36_probe_e1 configuration.components_sha256 True, m2_adapter == phase19_retrain_scores adapter_sha256 True.
- SC3: `test_instruments_unchanged_byte_for_byte` passed; RANK-03 AST tests in tests/test_phase38_rank.py
  (`-k "ast or rank03 or RANK03 or instrument"`): 3 passed.
- SC4: `test_phase38_prereg_is_frozen_before_every_phase38_record` and
  `test_this_test_file_is_first_added_before_every_phase38_record` passed (4 named SC tests: 4 passed); each
  results/phase38_* added in a single-path commit (7357577, d6984f4, 7043e9c, files=1 each) after Rafael's
  "approved" in 38-04, 38-09 and 38-10.
