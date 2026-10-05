---
phase: 39-instrument-context-2-2
plan: 08
subsystem: E6 driver review, MPS run, cross-check, emit
tags: [review, mps, ledger, e6]
requirements-completed: []
key-files:
  created:
    - .planning/phases/39-instrument-context-2-2/39-REVIEW-3.md
    - results/phase39_ctx.json (untracked until plan 09)
  modified:
    - scripts/phase39_ctx.py
    - tests/test_phase39_ctx.py
    - ledger/v6_mps_ledger.jsonl (uncommitted until plan 09)
---

# Plan 39-08 Summary — driver reviewed, E6 run once on MPS, record emitted

Requirements: this plan contributes to CTX-02; the orchestrator ticks requirements at phase close.
Executed by the orchestrator inline (review, checkpoints, launch) with one executor for the fixes.
Nothing under results/ or ledger/ was committed in this plan.

## Task 1 — driver review before the MPS run

- Review (39-REVIEW-3.md, b18a8e8): 0 blockers, 3 warnings, 6 info. A full suite launched at 45599e3
  was stopped at 61% (no failure so far, EXIT=143 by kill) because the fixes superseded that HEAD.
- Rafael's rulings recorded verbatim (b518246): fix WR-01, WR-02, WR-03, IN-01, IN-03, IN-05, IN-06
  and IN-02 ("corrigir, não limitação": the work pass re-scores the gate's taught cell with the pinned
  function, bitwise, else STOP); IN-04 a known limitation; Phase 38's WR-02 gap a known limitation
  there.
- Fix commits (each with a natural-RED test; subjects are the record's reasons): 4f859b3 WR-01,
  0cb1e04 WR-02, e706f95 WR-03, 98cd98d IN-06, 62c2653 IN-05, 6313ed9 IN-01 IN-03, 3590057 IN-02.
  Targeted: `174 passed in 78.44s`; ruff clean.
- **Second CPU rehearsal** (Rafael 2026-10-05: "O segundo ensaio (mesma fatia, mesmos números) fica
  registrado no SUMMARY do 39-08"): same slice as 39-07 (all 8 readings x pet_name, birth_year, 54
  entries) into a fresh scratch root `<scratchpad>/rehearsal39b`, tmp ledger and heartbeat, CPU, on
  the committed 3590057:
  ```
  PREFLIGHT OK 3590057d222e2c7192d4481fe4df0b1cab15ee8b device=cpu readings=8 slots=2 entries=216 projection_h=0.7293568082878159 stop_h=0.7424221732238463 spent_E6_s=0.0
  REHEARSAL KEPT 7b32c416a2ceaa105616c801575e9a2c630814e3
  RUN SCORED — next: crosscheck, then emit
  ```
  then crosscheck, emit, report, EXIT=0. Gate rows 16/16 equal (the same ranks as 39-07); copy
  equality 120/120; gate 2 passed; IN-02 work-load check 8/8 bitwise equal; CPU cross-check 0
  differing (gate 0/16, R_q 0/432, minted 0/432), suffix 432/432; class counts on the 12-cell slice
  identical to 39-07. data/phase39_rehearsal.json unchanged (md5 f3d2bf741598c21d0df6bbe5e17fc19e).
  The rehearsal record self-discloses ("this is the rehearsal") by design; Rafael ruled the code stays
  as is, this SUMMARY records it, and the v6.0 milestone report carries one sentence on it.
- Full suite at 3590057: `4300 passed, 4 skipped, 83 warnings in 3153.46s (0:52:33)`, EXIT=0.
- Rafael replied "reviewed" (852e6b4).

## Task 2 — pre-launch gate

- HEAD 852e6b4f648b5b7490d1ce205cc5c9c3992593c5; porcelain (scripts src results tests ledger
  artifacts) 0; suite cited from 3590057 (HEAD differs only by 39-REVIEW-3.md).
- launchd personacore agents loaded, no PID; ledger report: no open run, E6 0.0 s.
- Rehearsal identity equal field by field to the committed 39-07 SUMMARY: git_sha 7b32c41,
  phase39_ctx.py 0a9dbf81…c73b, phase39_prereg.py 4355b880…8297, 8 readings, pet_name/birth_year.
  At launch: phase39_ctx.py 4eb5a94535250b8079f5eee0f9e1401934aea1abd8a4deb4b9bfc7fa3b23213e,
  phase39_prereg.py 4355b88024b41463daef9b17285246e74b7577988cd95c01e33d293594858297 (= identity,
  D-27). `git log 7b32c41..HEAD -- scripts/phase39_ctx.py scripts/phase39_prereg.py`: the seven fix
  commits above, all ctx only.
- `PREFLIGHT OK 852e6b4f648b5b7490d1ce205cc5c9c3992593c5 device=mps readings=8 slots=8 entries=216 projection_h=0.7293568082878159 stop_h=0.7424221732238463 spent_E6_s=0.0`

## Task 3 — Rafael replied "approved" (2026-10-05)

## Task 4 — run, cross-check, emit (read from the files)

- `nohup caffeinate -dims .venv/bin/python scripts/phase39_ctx.py run`: `RUN SCORED — next: crosscheck,
  then emit`; logs/phase39_ctx.err empty.
- Ledger: one start (2026-10-05T16:15:38.312689Z) and one end (16:29:18.864060Z) for v6/39/E6/ctx,
  end naming results/phase39_ctx.json; report: closed, 820.551371 s, E6 spent 820.551371 s.
- Crosscheck (CPU) + emit: `CROSSCHECK DONE …/data/phase39_ctx_cpu.json`, `EMITTED SCORED
  …/results/phase39_ctx.json`, POST_EXIT=0.
- Record: status SCORED; provenance.run.device mps; git_sha_at_launch 852e6b4; head_moved False;
  gate rows 64/64 equal; copy equality 448/448, unequal []; gate 2 passed; work_load_check 8/8 equal;
  approval == phase39_prereg.approval_block(); baseline over 8 slots.
- Rehearsal disclosure in the record: 7 commits listed with their reasons, prereg_changed False,
  driver_changed True.
- Classification (48 cells per event; cells, disagreement, reverse, undecided):
  - collapse: prefixes (40, 9, 0, 0), M2 (8, 0, 0, 0), combined (48, 9, 0, 0); disagreement by class:
    INSTRUMENT_SUFFICIENT 5, ALREADY_AT_K0 4 (G_a at k0 = 0 for sibling_name and hometown).
  - damage: prefixes (40, 24, 0, 0), M2 (8, 0, 0, 0), combined (48, 24, 0, 0); disagreement by
    class: INSTRUMENT_SUFFICIENT 11, UNREACHABLE_AT_SIZE 8, EITHER 4, INTERACTION_ONLY 1.
  - CONTEXT_SUFFICIENT 0 under both events.
- k0 baseline (R_a, R_q n1, G_a unit, G_q): person_name 1/27/1/26, pet_name 1/27/1/27, cat_name
  1/27/1/27, sibling_name 1/27/0/27, hometown 1/27/0/21, street 1/27/1/27, birth_year 1/27/1/18,
  house_number 1/27/1/24.
- D-33 tie audit: flips [], exact ties [k8, person_name, G_q], class_changes [].
- CPU cross-check (criterion False): gate 0, R_q 0, minted 0 differing; suffix 1728/1728 equal.
- Cost: run_hours 0.2278947125, run_within_stop True; projection with the double load and the checks
  0.7308777162950072 <= 0.7424221732238463, projection_within_stop True; setups 8 priced / 16 run.
- `git status --porcelain`: ` M ledger/v6_mps_ledger.jsonl`, `?? results/phase39_ctx.json` (plus the
  pre-existing ` D .claude/scheduled_tasks.lock`, not ours).

## Self-Check: PASSED
