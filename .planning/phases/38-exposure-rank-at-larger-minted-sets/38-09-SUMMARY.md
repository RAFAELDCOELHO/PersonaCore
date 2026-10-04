---
phase: 38-exposure-rank-at-larger-minted-sets
plan: 09
subsystem: e5-rank
tags: [rank-record, ledger, RANK-02]
requirements-completed: []  # the orchestrator owns requirement ticks; RANK-02 closes at phase verification
key-files:
  created:
    - results/phase38_rank.json
  modified:
    - ledger/v6_mps_ledger.jsonl
commits: [8ae5994, d6984f4]
---

# 38-09 — E5 rank record published on Rafael's approved (run inline by the orchestrator)

- Task 1: the record was presented from the file (gate 64/64, curves and events per slot and size, A2
  references, D-27 sensitivity, CPU 0/256, D-33 audit, D-34 disclosure, approval, run 0.0843 h — table in
  38-08-SUMMARY.md). Rafael replied "approved".
- Task 2: porcelain before = ` M ledger/v6_mps_ledger.jsonl`, `?? results/phase38_rank.json` (+ the pre-existing
  ` D .claude/scheduled_tasks.lock`, not ours). 8ae5994 commits exactly ledger/v6_mps_ledger.jsonl
  (tests/test_phase36_ledger.py: 45 passed); then d6984f4 commits exactly results/phase38_rank.json.
  `git ls-files 'results/phase38_*'`: results/phase38_minting.json, results/phase38_rank.json.
- Full suite on the committed state (d6984f4): `4103 passed, 4 skipped, 83 warnings in 2945.86s (0:49:05)`,
  EXIT=0 — zero latent reds, zero new skips, no test fix needed (the suite covers the plan's targeted set).
- scripts/phase38_sizes_prereg.py is now frozen and scripts/phase38_rank.py pinned by the record.
