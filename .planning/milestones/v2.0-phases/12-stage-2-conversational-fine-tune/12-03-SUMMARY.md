---
phase: 12-stage-2-conversational-fine-tune
plan: 03
subsystem: data, evaluation
tags: [numpy, memmap, retention, perplexity, anchors, run-once]

# Dependency graph
requires:
  - phase: 12-stage-2-conversational-fine-tune
    provides: retention_perplexity() frozen dead-id-mask policy (DEBT-02, perplexity.py)
  - phase: 10-ewc
    provides: driver-script register (anchor load, refuse-to-rerun, local-rng, loud SystemExit proofs — estimate_fisher_tinystories.py)
  - phase: 02-data
    provides: data/val.bin uint16 memmap (12,636,923 tokens, eos-separated docs)
provides:
  - data/retention_val.bin — frozen ~1.0M-token doc-level subsample of val.bin (seed 1337, local disk, gitignored)
  - results/retention_anchors.json — committed step-0 anchors (subbin 2.1076, fullval masked 2.1065, headline 2.1066 reference)
  - scripts/build_retention_bin.py — run-once builder; rerun refuses with SystemExit
affects: [12-04, 12-05, 13-forgetting-curves, 13-VIZ-01]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Doc-level subsample: split memmap at eos boundaries (each doc keeps trailing eos), shuffle doc ORDER with a local default_rng, accumulate whole docs to a token target"
    - "Anchors measured-then-committed: step-0 numbers written to tracked results/ JSON with git_sha provenance BEFORE any training step exists (Pitfall 1)"

key-files:
  created:
    - scripts/build_retention_bin.py
    - results/retention_anchors.json
  modified: []

key-decisions:
  - "data/ is fully gitignored (line 17), so data/retention_val.bin is NOT committed — frozen-ness guarantee is refuse-to-rerun SystemExit + seeded local-rng build (bit-reproducible from val.bin + seed 1337)"
  - "Proof 3 margin is razor-thin: masked full-val 2.10655 < 2.1066 by ~5e-5 — the converged model already assigns near-zero mass to dead ids, so renormalization barely moves PPL; check passed as pre-registered"

patterns-established:
  - "Run-once data artifact: refuse-to-rerun on BOTH outputs (bin + JSON), delete both to rebuild"

requirements-completed: [TUNE-02]

# Metrics
duration: 15min
completed: 2026-08-01
---

# Phase 12 Plan 03: Retention Sub-Bin + Step-0 Anchors Summary

**Frozen 1,000,286-token doc-level retention sub-bin (2,201 whole TinyStories docs, seed 1337) plus all three step-0 anchor numbers measured on best.pt and committed to tracked results/ before any fine-tune step exists — subbin anchor 2.1076, masked full-val 2.1065 < 2.1066 unmasked headline (renormalization proof held)**

## Performance

- **Duration:** ~15 min (builder run: 372 s wall — full-val sweep dominates)
- **Started:** 2026-08-01T04:26:45Z
- **Completed:** 2026-08-01T04:42:00Z
- **Tasks:** 2

## Anchor Values (Plan 12-04 embeds these in the smoke report)

| Key | Value | Tokens (auditable denominator) |
|-----|-------|-------------------------------|
| `retention_ppl_subbin_step0` | **2.107553076833866** | 1,000,285 |
| `retention_ppl_fullval_step0` | **2.1065480504616803** | 12,636,922 |
| `headline_unmasked_fullval` | 2.1066 (historical unmasked reference only — NOT the curve anchor) | — |
| `subbin_token_count` | 1,000,286 | — |
| `subbin_seed` | 1337 | — |
| `anchor_val_loss` | 0.7378001868724823 (best.pt, step 49000) | — |

## Task Commits

| Task | Name | Commit |
|------|------|--------|
| 1 | scripts/build_retention_bin.py (build + anchors, run-once) | 483938a |
| 2 | Run builder; commit frozen anchors JSON | 8e2701d |

## What Was Built

- **scripts/build_retention_bin.py** — driver-script register (MPS-fallback env before torch
  import, no CLI flags, `_REPO_ROOT` constants, `[build_retention_bin]` prints). Flow:
  refuse-to-rerun on either output → memmap val.bin, split into 27,630 docs at eos boundaries
  (each doc keeps its trailing eos; tail after last eos never sampled) → shuffle doc order with
  `np.random.default_rng(1337)` (local rng) → accumulate whole docs to ≥1.0M tokens →
  `.tofile()` as uint16 → loud SystemExit sanity checks (eos count 2,201 > 100; token count
  in band; decoded 200-char prefix printed) → `preflight_device(strict=True)` + best.pt load
  (`weights_only=False`, trusted-only) → both anchors via `retention_perplexity()` (the ONLY
  sanctioned retention PPL, DEBT-02) → proof check fullval < 2.1066 → JSON with git_sha.
- **results/retention_anchors.json** — committed (tracked results/, Pitfall 6) with all three
  numbers, denominators, seed, anchor fingerprint, provenance SHA 483938a.

## Verification

- Bin size 2,000,572 bytes (uint16 × 1,000,286) — inside the [2.0 MB, 2.3 MB] band
- Second invocation exits 1: "refusing to rebuild the frozen retention sub-bin/anchors"
- JSON parses; subbin anchor finite and > 1; fullval masked 2.1065 < 2.1066; headline == 2.1066
- `.venv/bin/python -m pytest tests/ -q` → 274 passed, 1 skipped (no src/ changes this plan)
- ruff check + format clean

## Deviations from Plan

None - plan executed exactly as written. (The plan's read_first note anticipated dialog bins
might be tracked; `git ls-files data/` is empty — data/ is wholly gitignored — so the
documented gitignored branch applies: JSON committed, bin local-only.)

## Self-Check: PASSED

- scripts/build_retention_bin.py — FOUND
- results/retention_anchors.json — FOUND
- data/retention_val.bin — FOUND (local, gitignored as expected)
- Commit 483938a — FOUND
- Commit 8e2701d — FOUND
