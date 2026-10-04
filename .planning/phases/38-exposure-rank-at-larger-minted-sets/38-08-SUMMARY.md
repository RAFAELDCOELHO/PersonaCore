---
phase: 38-exposure-rank-at-larger-minted-sets
plan: 08
subsystem: e5-rank
tags: [review, mps-run, ledger, RANK-02]
requirements-completed: []  # the orchestrator owns requirement ticks; RANK-02 closes at phase verification
key-files:
  created:
    - results/phase38_rank.json (untracked until 38-09)
  modified:
    - ledger/v6_mps_ledger.jsonl (uncommitted until 38-09)
    - .planning/phases/38-exposure-rank-at-larger-minted-sets/38-REVIEW.md
commits: [6475b14, ccd5d7e]
---

# 38-08 — driver review, the E5 MPS run, cross-check, emit (run inline by the orchestrator)

## Task 1 — second code review (driver + sizes fill)

0 critical / 3 warning / 5 info (6475b14). DR-01..03 confirmed by the orchestrator (code reading; DR-03 also
`KeyError 'git_sha'`). Rafael: "reviewed — nothing to fix"; all eight known limitations (ccd5d7e). No driver
change after 1e68330, so no second rehearsal.

## Task 2 — pre-launch gate (all read-only)

- HEAD `ccd5d7e01532f1c14eb20d1f2ad66c0a6d32ad13`; `git status --porcelain -- scripts src results tests ledger artifacts` empty.
- Full suite at ccd5d7e: `4103 passed, 4 skipped, 83 warnings in 2940.34s (0:49:00)`, EXIT=0, zero new skips.
- launchctl: four com.personacore.phase25.* entries, no PID; pgrep: two stale `tail -f` viewers only.
- Ledger report: closed seconds probes 13176.153838, R1b 4104.256927, E1..E6 0.0 (total 17280.410765 s); no open run.
  `require_launch('E5')` -> `{'front': 'E5', ..., 'total_seconds': 17280.410765, 'lifted': ()}`.
- D-34: data/phase38_rehearsal.json sha256 cdda60d0…4289, equal field by field to the 38-07 SUMMARY copy.
  Launch digests: phase38_rank.py 19ed9476… (rehearsal f887d437…, changed), phase38_sizes_prereg.py 18f37b0b…
  (unchanged). `git log 91553d9..HEAD` on the two modules: 1e68330 only. `rehearsal_disclosure` on the real
  identity returned without error (driver_changed true, one commit with its subject as reason) — DR-03 cleared.
- `PREFLIGHT OK ccd5d7e01532f1c14eb20d1f2ad66c0a6d32ad13 device=mps readings=8 projection_h=0.467956566879681 stop_h=0.5418565110509128 spent_E5_s=0.0`

## Task 3 — Rafael approved the launch ("approved")

## Task 4 — launch, cross-check, emit (no commits)

- `nohup caffeinate -dims .venv/bin/python scripts/phase38_rank.py run` (PID 4919): `RUN SCORED`; stderr empty.
- Ledger: one start and one end line for v6/38/E5/rank, end naming results/phase38_rank.json; 303.445078 s.
- `crosscheck` (CPU, 2:32): CROSSCHECK DONE; `emit`: EMITTED SCORED.
- From the file: status SCORED; device mps; git_sha_at_launch ccd5d7e…; head_moved_during_run False; gate passed,
  64/64 rows equal; readings 8 x 8; cpu_crosscheck 0 of 256 cells differ, 0 of 64 gate cells (criterion False);
  approval == phase38_prereg.approval_block(); cost.run_hours 0.08427317444444445 <= e5_stop_hours 0.5418565110509128.
- rehearsal_disclosure in the record: phase38_rank.py changed, sizes file unchanged, commits [1e68330].
- drop_formula_audit: flips [], exact_ties [[person_name, 8]], 7 differing cells.
- `git status --porcelain`: ` M ledger/v6_mps_ledger.jsonl`, `?? results/phase38_rank.json` (plus the pre-existing
  ` D .claude/scheduled_tasks.lock`, not ours).

### Ranks and events per slot and size (read from results/phase38_rank.json)

| slot | |R| | rank k0 · k8 · k16 · k32 · k64 · k78 | M2 | adapter-off | moved: first k (rank_0) — vs collapse / vs damage | left top 1/8: first k — vs collapse / vs damage |
|---|---|---|---|---|---|---|
| person_name | 8 | 1 · 1 · 1 · 1 · 1 · 1 | 1 | 2 | — (1) — NEVER / NEVER | — — NEVER / NEVER |
| person_name | 32 | 1 · 1 · 1 · 1 · 1 · 1 | 1 | 7 | — (1) — NEVER / NEVER | — — NEVER / NEVER |
| person_name | 128 | 1 · 1 · 1 · 1 · 1 · 3 | 1 | 26 | 78 (1) — AFTER / AFTER | — — NEVER / NEVER |
| person_name | 512 | 1 · 1 · 1 · 1 · 1 · 5 | 1 | 109 | 78 (1) — AFTER / AFTER | — — NEVER / NEVER |
| pet_name | 8 | 1 · 1 · 1 · 1 · 1 · 1 | 1 | 1 | — (1) — NEVER / NEVER | — — NEVER / NEVER |
| pet_name | 32 | 1 · 1 · 1 · 1 · 4 · 4 | 4 | 12 | 64 (1) — SAME / AFTER | — — NEVER / NEVER |
| pet_name | 128 | 1 · 1 · 1 · 1 · 7 · 7 | 10 | 49 | 64 (1) — SAME / AFTER | — — NEVER / NEVER |
| pet_name | 512 | 1 · 1 · 1 · 1 · 12 · 16 | 32 | 171 | 64 (1) — SAME / AFTER | — — NEVER / NEVER |
| cat_name | 8 | 1 · 1 · 1 · 1 · 1 · 1 | 1 | 2 | — (1) — REFERENCE_NEVER_IN_GRID / NEVER | — — REFERENCE_NEVER_IN_GRID / NEVER |
| cat_name | 32 | 1 · 1 · 1 · 1 · 1 · 1 | 1 | 3 | — (1) — REFERENCE_NEVER_IN_GRID / NEVER | — — REFERENCE_NEVER_IN_GRID / NEVER |
| cat_name | 128 | 1 · 1 · 1 · 1 · 1 · 1 | 1 | 9 | — (1) — REFERENCE_NEVER_IN_GRID / NEVER | — — REFERENCE_NEVER_IN_GRID / NEVER |
| cat_name | 512 | 1 · 1 · 1 · 1 · 1 · 1 | 1 | 31 | — (1) — REFERENCE_NEVER_IN_GRID / NEVER | — — REFERENCE_NEVER_IN_GRID / NEVER |
| sibling_name | 8 | 1 · 1 · 1 · 1 · 1 · 1 | 1 | 5 | — (1) — NEVER / NEVER | — — NEVER / NEVER |
| sibling_name | 32 | 1 · 1 · 1 · 1 · 1 · 1 | 1 | 13 | — (1) — NEVER / NEVER | — — NEVER / NEVER |
| sibling_name | 128 | 1 · 1 · 1 · 5 · 8 · 10 | 2 | 45 | 32 (1) — BEFORE / SAME | — — NEVER / NEVER |
| sibling_name | 512 | 1 · 1 · 1 · 6 · 19 · 28 | 2 | 130 | 32 (1) — BEFORE / SAME | — — NEVER / NEVER |
| hometown | 8 | 1 · 1 · 1 · 1 · 1 · 1 | 1 | 6 | — (1) — NEVER / NEVER | — — NEVER / NEVER |
| hometown | 32 | 1 · 1 · 1 · 1 · 1 · 2 | 1 | 23 | 78 (1) — AFTER / AFTER | — — NEVER / NEVER |
| hometown | 128 | 1 · 1 · 2 · 4 · 7 · 11 | 1 | 84 | 16 (1) — BEFORE / AFTER | — — NEVER / NEVER |
| hometown | 512 | 1 · 1 · 3 · 6 · 19 · 31 | 1 | 314 | 16 (1) — BEFORE / AFTER | — — NEVER / NEVER |
| street | 8 | 1 · 1 · 1 · 1 · 1 · 1 | 1 | 1 | — (1) — NEVER / NEVER | — — NEVER / NEVER |
| street | 32 | 1 · 1 · 1 · 1 · 1 · 1 | 1 | 2 | — (1) — NEVER / NEVER | — — NEVER / NEVER |
| street | 128 | 1 · 1 · 1 · 1 · 1 · 1 | 1 | 4 | — (1) — NEVER / NEVER | — — NEVER / NEVER |
| street | 512 | 1 · 1 · 1 · 1 · 1 · 1 | 1 | 8 | — (1) — NEVER / NEVER | — — NEVER / NEVER |
| birth_year | 8 | 1 · 1 · 1 · 1 · 1 · 1 | 1 | 5 | — (1) — REFERENCE_NEVER_IN_GRID / NEVER | — — REFERENCE_NEVER_IN_GRID / NEVER |
| birth_year | 32 | 1 · 2 · 2 · 2 · 2 · 3 | 1 | 17 | 8 (1) — REFERENCE_NEVER_IN_GRID / BEFORE | — — REFERENCE_NEVER_IN_GRID / NEVER |
| birth_year | 128 | 1 · 2 · 2 · 3 · 4 · 7 | 2 | 69 | 8 (1) — REFERENCE_NEVER_IN_GRID / BEFORE | — — REFERENCE_NEVER_IN_GRID / NEVER |
| birth_year | 220 | 2 · 3 · 3 · 4 · 6 · 10 | 3 | 113 | 32 (2) — REFERENCE_NEVER_IN_GRID / BEFORE | — — REFERENCE_NEVER_IN_GRID / NEVER |
| house_number | 8 | 1 · 1 · 1 · 1 · 1 · 1 | 1 | 6 | — (1) — REFERENCE_NEVER_IN_GRID / NEVER | — — REFERENCE_NEVER_IN_GRID / NEVER |
| house_number | 32 | 1 · 1 · 1 · 1 · 1 · 1 | 1 | 18 | — (1) — REFERENCE_NEVER_IN_GRID / NEVER | — — REFERENCE_NEVER_IN_GRID / NEVER |
| house_number | 128 | 1 · 1 · 1 · 1 · 1 · 1 | 1 | 72 | — (1) — REFERENCE_NEVER_IN_GRID / NEVER | — — REFERENCE_NEVER_IN_GRID / NEVER |
| house_number | 512 | 1 · 1 · 1 · 1 · 1 · 1 | 1 | 288 | — (1) — REFERENCE_NEVER_IN_GRID / NEVER | — — REFERENCE_NEVER_IN_GRID / NEVER |
