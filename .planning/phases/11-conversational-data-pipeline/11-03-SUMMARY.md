---
phase: 11-conversational-data-pipeline
plan: 03
subsystem: data-pipeline
tags: [personachat, tokenizer-inflation, gate, data-04, d-09]
requires:
  - "11-01: parse_episodes + encode_dialogue (single tokenization path)"
  - "artifacts/tokenizer.json (frozen production tokenizer)"
provides:
  - "data/raw/personachat/{train,valid}_self_revised.txt (gitignored, checksum-verified cache)"
  - "compute_inflation_metrics (four D-08 metrics, auditable denominators)"
  - "results/inflation_report.md with user's recorded GO verdict — 11-04's hard precondition"
affects: [11-04, phase-12, phase-15]
tech-stack:
  added: []
  patterns: [thin no-CLI script, report-don't-gate, checksum-before-parse]
key-files:
  created:
    - scripts/fetch_personachat.py
    - src/personacore/dialogue/inflation.py
    - scripts/measure_inflation.py
    - results/inflation_report.md
  modified:
    - src/personacore/dialogue/__init__.py
    - tests/test_dialogue_serialize.py
decisions:
  - "D-09 verdict: GO (user, 2026-07-31) — ratio 1.129x <= 1.2x AND fit 0.9996 >= 90%"
  - "D-07 cap confirmed at 140 tokens — full-corpus persona p90 = 126 < smoke p90 131"
  - "D-05 substitution recorded: S3 revised JSON 404s; ParlAI tarball is the primary endpoint"
  - "Metrics computed on COMBINED train+valid (stated in report); baseline recomputed same run"
metrics:
  duration: "~25 min (+ user checkpoint wait)"
  completed: 2026-07-31
---

# Phase 11 Plan 03: Inflation Gate + D-09 Verdict Summary

**One-liner:** PersonaChat self_revised fetched with pinned sha256 and named-member-only
extraction, four-metric inflation gate run on the full corpus (3.229 tokens/word, ratio
1.129x vs TinyStories 2.860, fit 0.9996), user rendered GO at the blocking checkpoint —
bins unblocked for 11-04.

## What Was Built

- `scripts/fetch_personachat.py` — idempotent stdlib fetch of the ParlAI tarball
  (223,221,886 B), sha256 `507cf864...d5622` verified BEFORE any `tarfile.open` on EVERY run;
  only the two named self_revised members extracted via `tf.extract` (never `extractall`).
  Corpus cached gitignored at `data/raw/personachat/` (105,958 / 12,284 lines).
- `src/personacore/dialogue/inflation.py` — `compute_inflation_metrics(episodes, tok,
  block_size)`: one `encode_dialogue` pass per episode (the bin builder's exact tokenization
  path, Pitfall 4), returning the four D-08 metrics each with its auditable denominator.
- `scripts/measure_inflation.py` — thin gate driver (D-10): parses both splits, recomputes the
  TinyStories baseline with the same tokenizer + word-count rule in the same run, renders the
  D-09 relative band, writes `results/inflation_report.md`.
- 3 new `-k inflation` tests, including an exact hand-counted 100-word fixture denominator.

## Full-Corpus Numbers (committed in results/inflation_report.md)

| Metric | Value | Denominator |
| --- | --- | --- |
| tokens/word | 3.229 | 4,800,385 tokens / 1,486,754 words |
| persona cost | p50 94 / p90 126 / max 182 | 9,939 episodes |
| fit fraction (<= 256) | 0.9996 | 9,935 / 9,939 episodes |
| TinyStories baseline | 2.860 | 12,609,293 tokens / 4,408,824 words (same run) |
| **ratio** | **1.129x** | GO band (<= 1.2x AND fit >= 90%) |

Episode counts matched the pinned research values exactly (8,939 train / 1,000 valid).

## D-09 Verdict (user, at blocking checkpoint)

**GO** — recorded verbatim in the report's `## Verdict` section with the pinned D-07 persona
cap (**140 tokens**) and date 2026-07-31. Plan 11-04 reads that section as its hard
precondition. Full-corpus persona p90 (126) sits below the smoke p90 (131), so the D-07 cap
stands without re-litigation.

## D-05 Endpoint Substitution (recorded)

The originally planned S3 *revised* JSON endpoint 404s. Primary source is the ParlAI tarball
`https://dl.fbaipublicfiles.com/parlai/personachat/personachat.tgz` (sha256 pinned
2026-07-31). Pre-registered fallback (unused — primary fetch succeeded first try):
`https://s3.amazonaws.com/datasets.huggingface.co/personachat/personachat_self_original.json`.

## Deviations from Plan

None - plan executed exactly as written. (Worktree logistics: `data/raw` in the executor
worktree is a symlink to the main checkout's `data/raw`, so the gitignored corpus cache landed
directly at `/path/to/PersonaCore/data/raw/` — the artifact-rescue requirement is
satisfied by construction.)

## Known Stubs

None.

## Verification

- `pytest tests/test_dialogue_serialize.py -k inflation -x -q` — 3 passed
- Full suite: 247 passed, 4 skipped; `ruff check` + `ruff format --check` clean
- `git status --porcelain` shows nothing under `data/` (gitignored)
- Fetch script ran twice consecutively (idempotent, re-verified checksum both runs)

## Commits

| Task | Commit | Description |
| --- | --- | --- |
| 1 | e2162a7 | checksum-gated fetch + named-member extraction |
| 2 | 8fb1193 | inflation module + gate script + committed report |
| 3 | 89abe8d | user D-09 verdict GO recorded in report |

## Self-Check: PASSED

All created files exist on disk, all three task commits present in git log, working tree
clean, and the gitignored corpus cache verified present on the main checkout at
`/path/to/PersonaCore/data/raw/`.
