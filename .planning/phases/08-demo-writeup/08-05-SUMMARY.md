---
phase: 08-demo-writeup
plan: "05"
subsystem: demo-assets
status: in-progress
checkpoint: task-1-package-legitimacy-gate
tags: [gif, ffmpeg, demo, readme-hero, d-04]
requires:
  - phase: 08-demo-writeup
    plan: "02"
    provides: "scripts/demo_app.py — working offline Gradio streaming demo"
provides:
  - "assets/demo.gif — README hero GIF (D-04), live CPU streaming proof (PENDING)"
affects:
  - "08-06 (README) — places assets/demo.gif as hero asset with locked alt text"
tech-stack:
  added: []
  patterns: []
key-files:
  created: []
  modified: []
key-decisions: []
duration: in-progress
completed: null
---

# Phase 08 Plan 05: Demo GIF Hero Asset — IN PROGRESS (checkpoint)

**Status: paused at Task 1 — blocking-human package legitimacy gate for imageio-ffmpeg
([ASSUMED] package, never auto-approvable). No installs run, no files changed yet.**

## What was done so far

- Worktree branch check passed (worktree-agent-a69fb2eb1940a53d5, base a59f227).
- Environment probe (read-only): neither `ffmpeg` nor `gifski` is on PATH, no brew ffmpeg at
  /opt/homebrew/bin or /usr/local/bin, and `imageio_ffmpeg` is NOT installed in the shared
  .venv — the package gate is genuinely required before any GIF conversion can run.
- Read 08-RESEARCH.md § Package Legitimacy Audit: imageio-ffmpeg row — PyPI 0.6.0, ~7 yrs,
  high downloads, source repo github.com/imageio/imageio-ffmpeg, slopcheck unavailable →
  human gate required per protocol.

## Task status

| Task | Name | Type | Status |
| ---- | ---- | ---- | ------ |
| 1 | Package legitimacy gate — imageio-ffmpeg | checkpoint:human-verify (blocking-human) | AWAITING HUMAN — resume signal: "approved" / "brew" / "rejected" |
| 2 | Record the streaming demo (~10-15 s capture) | checkpoint:human-action | Not started (follows Task 1) |
| 3 | Install ffmpeg source + two-pass palette conversion → assets/demo.gif | auto | Not started (needs Task 1 signal + Task 2 recording path) |

## Awaiting

Human verification of the imageio-ffmpeg PyPI page (exact name, imageio org,
github.com/imageio/imageio-ffmpeg, recent 0.6.x release) and explicit selection of the
ffmpeg source:
- "approved" → `.venv/bin/pip install imageio-ffmpeg` (pip wheel bundling static ffmpeg)
- "brew" → use a brew/system ffmpeg binary instead (conversion command identical)
- "rejected" → stop and surface to the developer

## Deviations from Plan

None so far.

## Self-Check: N/A (in-progress checkpoint snapshot — no artifacts claimed yet)
