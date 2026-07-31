---
phase: 11-conversational-data-pipeline
plan: 04
subsystem: data-pipeline
tags: [personachat, dialogue-bins, loss-mask, d-07, data-02, data-03]
requires:
  - "11-01: parse_episodes + encode_dialogue (the single tokenization path)"
  - "11-02: get_batch_memmap_masked (training/data.py)"
  - "11-03: results/inflation_report.md with recorded GO verdict (hard precondition)"
  - "data/raw/personachat/{train,valid}_self_revised.txt (checksum-verified cache)"
provides:
  - "data/dialog_{train,val}.bin (uint16) + data/dialog_{train,val}_mask.bin (uint8) — gitignored, 1:1 aligned per split"
  - "scripts/prepare_dialog_corpus.py — verdict-gated run-once bin builder"
  - "results/inflation_report.md ## Corpus Build — committed build evidence for Phases 12/15"
affects: [phase-12, phase-14, phase-15]
tech-stack:
  added: []
  patterns: [thin no-CLI run-once script, verdict-gated build, loud SystemExit sanity block]
key-files:
  created:
    - scripts/prepare_dialog_corpus.py
  modified:
    - results/inflation_report.md
decisions:
  - "D-07 cap applied at build: 283/8,939 train and 56/1,000 val personas line-granularly capped at 140 tokens"
  - "Verdict gate enforced in code: SystemExit unless report's ## Verdict reads GO/ADAPT (T-11-07)"
  - "Masked fractions 0.4292 (train) / 0.4238 (val) — inside the pre-registered [0.30, 0.70] band"
metrics:
  duration: "~8 min"
  completed: 2026-07-31
---

# Phase 11 Plan 04: Dialogue Bins Summary

**One-liner:** Verdict-gated `prepare_dialog_corpus.py` built the four aligned dialogue bins
(5,257,858 train / 637,633 val tokens, eos==episodes 8,939/1,000, masked fractions
0.4292/0.4238) through the same `encode_dialogue` path the gate measured, with the pinned
D-07 140-token line-granular persona cap — Phase 12's masked-vs-unmasked calibration has both
arms ready.

## What Was Built

- `scripts/prepare_dialog_corpus.py` — thin no-CLI run-once script mirroring
  `encode_corpus.py` (`_REPO_ROOT` constants, `main()`, prefixed prints, no argparse).
  Preconditions are loud failures: `FileNotFoundError` (with the fetch remedy) for missing
  inputs; `SystemExit` unless `results/inflation_report.md`'s `## Verdict` reads GO/ADAPT
  (missing/PENDING/STOP all refuse — T-11-07 enforced in code). Per split (PersonaChat's
  native file-level train/valid split, so no dialogue straddles the cut by construction):
  `parse_episodes` → D-07 cap → `encode_dialogue` → uint16 id shards + uint8 mask shards →
  `tofile`. No tokenization is re-implemented: the only direct `tok.encode` call is the
  persona-span budget accounting inside the D-07 cap (mirrors inflation metric 2 exactly —
  1 + ids of the newline-joined detokenized persona, recomputed on the full join per
  candidate line).
- Post-build sanity block per split, all `SystemExit` (never bare assert): token/mask length
  equality, eos-8184 count == episode count, `mask.mean()` hard-failed outside [0.30, 0.70],
  decoded 200-token prefix, and an end-to-end `get_batch_memmap_masked` smoke draw from the
  real bins ((4, 256) shapes, `-100` sentinels present in `y`, all `x` ids < 8192).
- `results/inflation_report.md` gained a `## Corpus Build` section: per-split token counts,
  eos counts, mask lengths, masked fractions (4 dp), D-07 cap stats, dtypes, and the
  block_size=256 consumption parameters — measured claim + verdict + build evidence now live
  on one committed document (Phase 15 reads straight off it). The measured sections and the
  `## Verdict` are untouched.

## Build Numbers (enforced, not just printed)

| Split | Tokens | eos = episodes | Masked fraction | Personas capped (D-07, 140 tok) |
| --- | --- | --- | --- | --- |
| train | 5,257,858 | 8,939 | 0.4292 | 283 / 8,939 |
| val | 637,633 | 1,000 | 0.4238 | 56 / 1,000 |

Both decoded prefixes open with `<|system|>` + persona lines; eos appears exactly once per
dialogue (document separator only).

## Deviations from Plan

None - plan executed exactly as written. (Worktree logistics: `data/raw` was symlinked from
the main checkout; the four output bins were copied back to
`/path/to/PersonaCore/data/` and verified byte-identical before return.)

## Known Stubs

None.

## Threat Flags

None — no new surface beyond the plan's threat model; T-11-07 (verdict-before-bins) is
mitigated in code via the SystemExit gate.

## Verification

- `scripts/prepare_dialog_corpus.py` ran clean end-to-end; all sanity proofs printed and passed
- Full suite: 247 passed, 4 skipped; `ruff check` + `ruff format --check` clean (106 files)
- `git status --porcelain` shows nothing under `data/` (gitignored)
- All four bins present on the main checkout with matching bytes (`cmp` verified)

## Commits

| Task | Commit | Description |
| --- | --- | --- |
| 1 | 55c695e | verdict-gated prepare script + bin build with sanity proofs |
| 2 | 987b07e | Corpus Build evidence appended to the committed report |

## Self-Check: PASSED

All created/modified files exist, both task commits present in git log, all four bins
byte-identical (`cmp`) on the main checkout at `/path/to/PersonaCore/data/`, and
`git status --porcelain` shows no `data/` entries.
