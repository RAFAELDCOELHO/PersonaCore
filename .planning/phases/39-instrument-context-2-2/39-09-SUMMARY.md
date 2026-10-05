---
phase: 39-instrument-context-2-2
plan: 09
subsystem: E6 record approval and publication
tags: [record, ledger, approval]
requirements-completed: []
key-files:
  created:
    - results/phase39_ctx.json
  modified:
    - ledger/v6_mps_ledger.jsonl
---

# Plan 39-09 Summary — the E6 record approved and published

Requirements: this plan contributes to CTX-02 and CTX-03; the orchestrator ticks requirements at
phase close. Executed inline by the orchestrator.

## Task 1 — Rafael read the record and replied "approved" (2026-10-05)

Presented from results/phase39_ctx.json (untracked at the time; report preview rendered into the
scratchpad by the committed driver code): gate 1 64/64 ranks, 448/448 cells bitwise equal; IN-02
work-load check 8/8; gate 2 passed (pet_name k0 independent); run 820.551371 s (0.2278947125 h),
run_within_stop True, projection 0.7308777162950072 <= 0.7424221732238463; collapse 9 disagreement
cells of 48 (INSTRUMENT_SUFFICIENT 5, CONTEXT_SUFFICIENT 0, ALREADY_AT_K0 4; M2 0 of 8), damage 24 of 48
(INSTRUMENT_SUFFICIENT 11, CONTEXT_SUFFICIENT 0, EITHER 4, INTERACTION_ONLY 1, UNREACHABLE_AT_SIZE 8;
M2 0 of 8); REVERSE 0, undecided 0; D-33 audit: no flips, exact tie k8/person_name G_q; CPU
cross-check 0 differing ranks (64 gate rows, 1728 R_q, 1728 (ii)), suffix 1728/1728; rehearsal
disclosure 7 commits, prereg unchanged; approval == approval_block().

### Rafael's note (verbatim), for this SUMMARY and the v6.0 milestone report — changes no record or code

"das 11 células de dano classificadas INSTRUMENT_SUFFICIENT, 4 (house_number em k32, k64 e k78; birth_year em k78) dependem de uma linha de base de 1 acerto em 48 na geração da âncora em k = 0. Nesses dois slots, "perdeu" significa passar de 1/48 para 0/48, o que não se distingue de ruído de sorteio. As outras 7 e as 5 de colapso têm linha de base de 18 a 45 acertos em 48."

Premise measured by the orchestrator from the record before recording it: the 11 damage
INSTRUMENT_SUFFICIENT cells are k16/k32 person_name, k32/k64/k78 street, k64/k78 cat_name,
k32/k64/k78 house_number, k78 birth_year; k0 anchor hits (G_a hits/48): house_number 1, birth_year 1,
person_name 20, street 18, cat_name 32; the 5 collapse INSTRUMENT_SUFFICIENT cells (k64 person_name,
pet_name, street; k78 person_name, street) sit on 20, 45 and 18. True as stated.

## Task 2 — ledger, then record, each alone; suite on the committed state

- `git status --porcelain` before: ` M ledger/v6_mps_ledger.jsonl`, `?? results/phase39_ctx.json`.
- 4268f26 ledger(39-09): `git show --name-only` = ledger/v6_mps_ledger.jsonl only;
  tests/test_phase36_ledger.py `45 passed in 2.03s`.
- 78d2605 results(39-09): `git show --name-only` = results/phase39_ctx.json only.
- Full suite on 78d2605: `4300 passed, 4 skipped, 83 warnings in 3210.52s (0:53:30)`, EXIT=0; skips
  4 = the last green run's 4; no latent red, no test fix needed.
- Targeted (test_phase35_prereg, test_phase36_ledger, test_phase36_budget, test_phase36_caps,
  test_phase39_prereg, test_phase39_ctx): `425 passed in 126.20s (0:02:06)`;
  `git ls-files 'results/phase39_*'` = results/phase39_ctx.json.

## Self-Check: PASSED
