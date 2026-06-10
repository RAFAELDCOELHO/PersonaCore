---
phase: 08-demo-writeup
plan: "06"
subsystem: docs-frontdoor
status: checkpoint-paused
tags: [readme, release, weights-distribution, qa-gate, doc-01, qa-01]
requires:
  - phase: 08-demo-writeup
    plan: "03"
    provides: "demo.ipynb (executed, committed with outputs) + results/run.csv"
  - phase: 08-demo-writeup
    plan: "04"
    provides: "docs/REPORT.md — decision-driven deep dive (440 lines)"
  - phase: 08-demo-writeup
    plan: "05"
    provides: "assets/demo.gif — README hero (720x444, 12 fps, 245 KB, light mode)"
provides:
  - "(pending) README.md — D-01/D-04 front door: thesis, GIF hero, results block, quickstart, evidence links"
  - "(pending) weights distribution channel (Release asset or regenerate-only)"
  - "(pending) green QA-01/QA-02 phase gate run"
affects:
  - "Milestone 1 close — this is the final plan of Phase 8"
tech-stack:
  added: []
  patterns: []
key-files:
  created: []
  modified: []
key-decisions:
  - "(pending) Task 1 weights-distribution decision: release vs regenerate-only"
duration: "in progress — paused at Task 1 checkpoint"
completed: null
---

# Phase 08 Plan 06: README Front Door + M1 Phase Gate Summary (IN PROGRESS)

**One-liner:** PAUSED at the Task 1 blocking decision checkpoint (weights distribution:
GitHub Release asset vs regenerate-only). No tasks executed yet; no file changes made.

## Checkpoint state

- **Task 1 (checkpoint:decision, gate=blocking):** awaiting developer selection —
  `release` or `regenerate-only`. No `gh release` command has been run (T-08-08: publishing
  only on an explicit "release" selection).
- **Task 2 (README.md):** not started — quickstart weights wording depends on Task 1.
- **Task 3 (QA-01/QA-02 phase gate):** not started.

## Carried context for the continuation agent

- Headline numbers (single-source): 13,891,584 params · full-val PPL 2.1066 over
  12,636,922 tokens · ~100 tok/s laptop CPU (measured 95-105) · slim artifact ~55.6 MB ·
  trained on-device (M3/MPS, fp32) · git SHA 3a46815d · step 49000.
- GIF alt text (locked, 08-UI-SPEC): "Gradio chat demo streaming a TinyStories completion
  token-by-token on a laptop CPU".
- Release command (only if "release" selected): `gh release create m1-demo-v1
  checkpoints/model_slim.pt --title "PersonaCore Milestone 1 — slim inference checkpoint"
  --notes <body citing SHA 3a46815d, step 49000, 13,891,584 params, weights_only=True>`.
  Note: `checkpoints/model_slim.pt` lives in the MAIN checkout only (gitignored), not in
  this worktree — run gh from a path where the artifact exists.
- 08-05 known blemish surfaced at this gate (T-08-05): the GIF's right edge slightly clips
  the user-bubble tail and a few words at two line-wraps of the final story; story remains
  fully legible. Re-capture commands documented in 08-05-SUMMARY.md if a cleaner take is
  preferred.

## Self-Check: N/A (in-progress snapshot)
