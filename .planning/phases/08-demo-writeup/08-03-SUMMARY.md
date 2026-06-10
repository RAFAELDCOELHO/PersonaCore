---
phase: 08-demo-writeup
plan: 03
subsystem: demo
status: paused-at-checkpoint
tags: [notebook, nbconvert, ipykernel, demo-ipynb, qa-02]
requires: ["08-01"]
provides: []
affects: [pyproject.toml, results/run.csv, demo.ipynb]
tech-stack:
  added: []
  patterns: []
key-files:
  created: []
  modified: []
decisions: []
metrics:
  started: 2026-06-10T17:20:54Z
  completed: null
---

# Phase 08 Plan 03: demo.ipynb Results Showcase Summary (IN PROGRESS)

**Status: PAUSED at Task 1 — blocking-human package-legitimacy checkpoint.**

No code or file changes have been made yet. Task 1 is the FIRST task in this plan and is a
`checkpoint:human-verify` with `gate="blocking-human"`: the developer must verify the
ipykernel and nbconvert PyPI pages before the executor is allowed to run any pip install.
This gate is never auto-approvable (slopcheck was unavailable at research time, so both
packages are tagged [ASSUMED] in the 08-RESEARCH.md Package Legitimacy Audit).

## Progress

| Task | Name | Status | Commit |
|------|------|--------|--------|
| 1 | Package legitimacy gate — ipykernel + nbconvert | AWAITING HUMAN VERIFICATION | — |
| 2 | notebook extra in pyproject + install + commit results/run.csv | NOT STARTED (blocked by Task 1) | — |
| 3 | Author demo.ipynb + execute headlessly + commit with outputs | NOT STARTED (blocked by Task 1) | — |

## Checkpoint Details

Awaiting human verification of two new packages before first install into `.venv`:

- **ipykernel ~=7.3** — https://pypi.org/project/ipykernel/ (expect: Jupyter/IPython org,
  source github.com/ipython/ipykernel, recent 7.3.x release)
- **nbconvert ~=7.17** — https://pypi.org/project/nbconvert/ (expect: Jupyter org,
  source github.com/jupyter/nbconvert, recent 7.17.x release)

Resume signal: "approved" allows the install (Task 2 proceeds); "rejected" skips the
install and falls back to interactive notebook execution in an editor (weaker D-06
reproducibility — to be noted in the final SUMMARY).

## Deviations from Plan

None so far.

*This file is an in-progress snapshot committed at the checkpoint per worktree protocol.
The continuation agent will replace it with the final SUMMARY after Tasks 2-3 complete.*
