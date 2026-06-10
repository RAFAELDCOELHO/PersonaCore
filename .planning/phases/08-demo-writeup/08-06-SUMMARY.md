---
phase: 08-demo-writeup
plan: "06"
subsystem: docs-frontdoor
status: complete
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
    provides: "assets/demo.gif — README hero (re-captured: 720x374, 12 fps, 128 KB, light mode)"
provides:
  - "README.md — D-01/D-04 front door: thesis, GIF hero, results block, quickstart, evidence links (105 lines)"
  - "Weights distribution channel: GitHub Release m1-demo-v1 with model_slim.pt asset (~55.6 MB)"
  - "QA phase-gate lint fix: duplicate torch import removed from demo.ipynb"
affects:
  - "Milestone 1 close — this is the final plan of Phase 8"
tech-stack:
  added: []
  patterns:
    - "Weights ship as a Release asset, never committed (checkpoints/ stays gitignored)"
key-files:
  created:
    - README.md
  modified:
    - demo.ipynb
key-decisions:
  - "Task 1 decision gate: developer selected `release` — gh release m1-demo-v1 published with model_slim.pt; release notes pin SHA 3a46815d + step 49000 + 13,891,584 params and mandate weights_only=True load"
  - "Hero GIF: developer chose re-capture over shipping the blemished take — final GIF is 720x374/128 KB light mode, no edge clipping (see 08-05-SUMMARY Re-capture addendum)"
  - "Quickstart wording uses gh release download with a manual-download fallback URL"
duration: "~10 min agent execution across two sessions (+ human decisions and GIF re-capture between checkpoints; final session quota-killed after substantive work, SUMMARY finalized by orchestrator)"
completed: 2026-06-10
---

# Phase 08 Plan 06: README Front Door + M1 Phase Gate Summary

**One-liner:** Shipped the 105-line README front door (thesis line, light-mode GIF hero with
locked alt text, results-at-a-glance block, offline-honest quickstart, evidence links,
honest M2 roadmap) and published the weights as GitHub Release `m1-demo-v1` — closing the
final plan of Phase 8.

## What Was Built

### Task 1 — Weights distribution decision (checkpoint:decision, resolved)

Developer selected **`release`**. `gh release create m1-demo-v1` published
`checkpoints/model_slim.pt` (55,601,269 bytes) from the main checkout. Verified post-hoc by
the orchestrator: tag `m1-demo-v1` exists on origin at commit 882af22, release page returns
HTTP 200, asset `model_slim.pt` (53 MB rendered) listed on the expanded-assets endpoint.
The tag points at the pre-README commit — acceptable by design: the release ships weights,
not docs (the README landed on main immediately after).

Also resolved at this gate: the 08-05 GIF blemish — developer chose **re-capture**. Two
re-takes (first rejected: dark mode vs the locked light-mode capture contract); final GIF
committed as `fix(08-05)` 581043c before README authoring.

### Task 2 — README.md (commit 333047c)

105 lines per D-01/D-04 and the locked 08-UI-SPEC copy contract:

- Thesis line first: memory in weights, privacy by design; M1 = foundation, M2 = upcoming
  weight-memory mechanism (honesty bar D-02 — no chat-tuning/personalization claims)
- GIF hero immediately under the title with the locked alt text
- Results at a glance: 13,891,584 params · full-val PPL 2.1066 over 12,636,922 tokens ·
  ~100 tok/s laptop CPU (95–105 measured) · trained on-device fp32/MPS · from-scratch claim
- Quickstart: venv → `pip install -e ".[cpu,demo]"` → `gh release download m1-demo-v1`
  (manual URL fallback) → `python scripts/demo_app.py`; states the demo makes zero network
  calls after install+download; `weights_only=True` load mandated; `export_slim.py`
  regeneration path for local best.pt holders
- Evidence section links docs/REPORT.md, demo.ipynb, results/
- Roadmap section names the M2 seams already shipped (LoRA projections, assemble_loss, open-dict checkpoints)

### Task 3 — QA phase gate (commit ff4c7f4)

Phase-gate lint flagged a duplicate `torch` import in `demo.ipynb`; removed (2 lines).
Full-suite verification was interrupted by a provider session limit; the orchestrator
re-ran the gate post-merge: **130 passed, 1 skipped** + `ruff check` clean on main.

## Deviations from Plan

1. **Session quota kill before SUMMARY finalization** — the continuation agent completed
   Tasks 2–3 and the release, then hit the provider session limit before finalizing this
   SUMMARY. The orchestrator merged the worktree (commits 333047c, ff4c7f4), verified the
   release out-of-band, re-ran the test/lint gate, and finalized this SUMMARY.
2. **GIF re-capture loop at the gate** (documented above and in 08-05-SUMMARY) — two human
   re-takes; pipeline re-run by the orchestrator with retuned trim/crop.

## Self-Check: PASSED

- FOUND: README.md (105 lines; contains `assets/demo.gif`, `m1-demo-v1`, `weights_only=True`)
- FOUND: commit 333047c (README front door + release)
- FOUND: commit ff4c7f4 (lint fix)
- VERIFIED: tag m1-demo-v1 on origin; release page HTTP 200; asset model_slim.pt present
- VERIFIED: full suite 130 passed / 1 skipped post-merge on main
