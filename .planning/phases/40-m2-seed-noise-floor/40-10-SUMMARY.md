---
phase: 40-m2-seed-noise-floor
plan: 10
subsystem: e2-noise-floor-publication
tags: [records, ledger, noise-floor, approvals]
requires: [40-09]
provides:
  - "ledger/v6_mps_ledger.jsonl with the E2 lines (5 whole seeds; seed 2025 two start + lost pairs before its whole attempt), committed"
  - "results/phase40_seed<s>.json + results/phase40_a2_{full,m2}_seed<s>.json for 1337, 2024, 1338, 2025, 1339, committed one seed per commit"
  - "Rafael's second approved for results/phase40_noise_floor.json (committed alone by 40-11 Task 1)"
affects: [40-11, 41]
tech-stack:
  added: []
  patterns: []
key-files:
  created: []
  modified: [ledger/v6_mps_ledger.jsonl]
decisions:
  - "Rafael outlet (i): 40-09-SUMMARY.md committed alone right after the last seed commit and before the noise-floor record"
  - "No seed left dropped: Task 1 item 6 / Task 2 step 4 not applicable"
requirements-completed: []
metrics:
  completed: 2026-10-07
---

# Phase 40 Plan 10: ledger and seed records published; noise-floor record approved

Under Rafael's first approved the ledger was committed alone, then each whole seed with exactly its seed
record and the two A2 records it names, then 40-09-SUMMARY.md alone (his outlet (i)). His second approved
covers results/phase40_noise_floor.json, which stays untracked here and is committed alone by 40-11 Task 1.

## Task 1 — first checkpoint

Verify printed the three approvals (first | the ledger and every whole seed's records … | all together in
one checkpoint | the ledger first / then one commit per whole seed; second | NOISE_FLOOR_RECORD | the
noise-floor record; third | REPORT_RECORD | the report); `git ls-files 'results/phase40_*'` = 0; record
status MEASURED. Presented from the files: seeds and ledger lines, NOISE-01 slot counts n/27 with tiers,
D-09 readings, D-13 blocks, the records' training/provenance/disclosure/approval blocks (see 40-09-SUMMARY
for the numbers).

Rafael's first reply (pasted text, adopted by Rafael), verbatim:

> approved
>
> Primeiro aprovado da Fase 40: o ledger e os cinco registros de semente com os seus registros A2, como mostrados no checkpoint.
>
> Saída (i): um commit só do 40-09-SUMMARY.md, logo depois do último commit de semente e antes do registro do piso.
>
> Cada commit entra por caminho explícito. A remoção pendente de .claude/scheduled_tasks.lock não entra em nenhum deles.

## Task 2 — commits (explicit paths; `git show --name-only` checked on each)

| commit | content | guard after it |
|---|---|---|
| ea8f7d3 | ledger/v6_mps_ledger.jsonl alone | tests/test_phase36_ledger.py: 45 passed |
| cf3b626 | seed 1337: seed record + A2 full + A2 m2 | `-k "launch_line or slot_ordering"`: 4 passed |
| 6dbf272 | seed 2024: the same three | 4 passed |
| a93240d | seed 1338: the same three | 4 passed |
| 73ebe08 | seed 2025 (third attempt): the same three | 4 passed |
| 60e4480 | seed 1339: the same three | 4 passed |
| 56ad39b | .planning/phases/40-m2-seed-noise-floor/40-09-SUMMARY.md alone (title updated to "E2 run complete…") | — |

- Step 1 porcelain (scripts src results tests ledger): ` M ledger` + the 15 records + `?? results/phase40_noise_floor.json`.
- Step 4: no seed left dropped (seeds.dropped_seed_outputs {}); seed 2025's dropped attempts are already
  under data/phase40_dropped/ (gitignored) and listed in its committed seed record.
- Step 5: tests/test_phase35_prereg.py, test_phase36_ledger.py, test_phase36_budget.py, test_phase36_caps.py,
  test_phase40_prereg.py, test_phase40_noise.py — **423 passed** (94.7 s), exit 0. No latent red, no test fix.
- Step 6: `git status --porcelain -- scripts src results tests ledger` = `?? results/phase40_noise_floor.json`;
  15 results/phase40_* tracked. `.claude/scheduled_tasks.lock` deletion left out of every commit.
- Deviation (no effect): the first per-seed loop passed paths in a zsh scalar (not word-split); its state
  guard stopped before any `git add`; re-run with an array.

## Task 3 — second checkpoint

Verify: untracked; `MEASURED {'group': 'm2', 'n_pairs': 10, 'n_seeds': 5, 'tie': False, 'value': 0.3481481481481482} 0.08406970366097503 5 10`;
sha256 678db43f213d9dd7c34fe52b2cf175caad19368b1215bc7a74a5036f2cdf31aa. Presented: seeds and
dropped_attempts (attempt-vs-attempt tensor identity 72/72, max 0.0, both groups, both attempts); floors full
0.2963 / m2 0.3481 with pairs, per-slot range and SDs; published m2 0.3481 beside 0.1481, margin 8/27
unamended, crn not below; gap_noise_floor 0.08407 (max 0.18498) beside 0.005214; D-07 identical, D-08
re-measured identical, D-08b NO_RESIDUAL 0.0; D-12 per slot; D-13 all 5 measured; predictions; a2_label;
approval block.

Rafael's second reply, verbatim:

> approved
>
> Segundo aprovado da Fase 40: o registro do piso, results/phase40_noise_floor.json (sha256 678db43f213d9dd7c34fe52b2cf175caad19368b1215bc7a74a5036f2cdf31aa), commitado sozinho.

Premise checked: `shasum -a 256 results/phase40_noise_floor.json` = 678db43f…31aa.

## Next

40-11 Task 1: commit results/phase40_noise_floor.json alone, then the full suite on the committed state;
the report under the third approved, with Rafael's dated post-hoc addendum (40-09-SUMMARY lists its items).
