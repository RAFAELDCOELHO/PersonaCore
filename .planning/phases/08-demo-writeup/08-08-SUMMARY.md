---
phase: 08-demo-writeup
plan: 08
subsystem: docs
tags: [wr-01, wr-03, wr-04, in-01, doc-01, gap-closure, effective-vocabulary]
requires:
  - phase: 08-07
    provides: "shipped CR-01 forbid_ids logits mask (undecodable_ids_mask + demo wiring) the REPORT now documents"
  - phase: 08-04
    provides: "docs/REPORT.md decision-driven structure the honesty paragraphs slot into"
provides:
  - "README + REPORT state the effective vocabulary honestly everywhere: 547 live ids (256 bytes + 283 learned merges + 8 specials) of the 8192-row table; 7645 rows reserved"
  - "REPORT Results quantifies the dead embedding rows: 2,935,680 of 13,891,584 parameters (7645 x 384, ~21%)"
  - "REPORT demo decision documents the shipped CR-01 mask, citing tests/test_forbid_ids.py"
  - "README quickstart works verbatim from an empty directory (git clone + cd precede venv/install)"
  - "pyproject notebook extra includes matplotlib~=3.10 so .[cpu,notebook] runs demo.ipynb"
affects: [08-verification-rerun]
tech-stack:
  added: []
  patterns:
    - "Honesty edits keep the writeup's decision-driven register: bold lead-in paragraphs (What actually trained.) quoting the trainer's own warning verbatim"
    - "Test counts stay unpinned in prose (IN-01) — the suite is described as green, never as a number that staleness can falsify"
key-files:
  created: []
  modified:
    - README.md
    - docs/REPORT.md
    - pyproject.toml
key-decisions:
  - "WR-01 phrasing follows the review's template with locked numbers: 'vocab table 8192 with 547 ids live' — the config identifier vocab_size=8192 and ln(8192) remain untouched (true as written)"
  - "The dead-row parameter sentence lives in the Results Model paragraph, framed as counted-in-the-headline-because-shipped — no headline number changed"
  - "CR-01 mitigation sentence placed in the demo decision's Evidence paragraph so the test citation (tests/test_forbid_ids.py) lands in its natural home"
  - "IN-01: replaced '126 passed, 1 skipped' with unpinned 'green, with the only skip a CUDA-only fp16 smoke test' — no number to go stale again"
duration: ~5min
completed: 2026-06-10
---

# Phase 08 Plan 08: WR-01/WR-03/WR-04 writeup gap closure Summary

**Every "vocabulary 8192" claim in README/REPORT now states the effective vocabulary (547 live ids of the 8192-row table, 7645 reserved), the Results section quantifies the 2,935,680 dead-row embedding parameters (~21% of the headline), the REPORT documents the shipped CR-01 logits mask, and the quickstart works verbatim from an empty directory with a notebook extra that can actually run the notebook.**

## Status

Both tasks complete and committed. Ruff check + format clean. All locked rigor signals
survive untouched.

## What Was Built

### Task 1 — WR-01 effective-vocabulary honesty + CR-01 documentation + IN-01 (`225a962`)

Four "8192" claim sites corrected with the locked numbers (547 = 256 bytes + 283 learned
merges + 8 specials; 7645 dead ids; 2,935,680 = 7645 x 384 dims):

- **README.md line-29 bullet:** "vocabulary 8192" -> "vocab table 8192 with 547 ids live
  (...the bounded TinyStories corpus exhausts its mergeable pairs, so the remaining 7645
  rows are reserved capacity)". The `<|endoftext|>` pinning and tiktoken-oracle clauses
  kept intact.
- **REPORT overview bullet:** same qualification; "document separator `<|endoftext|>`
  pinned at id 8184" preserved.
- **REPORT BPE decision section:** new "**What actually trained.**" paragraph (between
  Rationale and Evidence, matching the bold-lead-in register) quoting the trainer's own
  warning verbatim ("corpus exhausted: learned 283 of 7928 requested merges;
  vocab_size=8192 has 7645 dead ids" — confirmed against src/personacore/tokenizer/bpe.py
  lines 120-121 before quoting) and stating the trade-off plainly: shape stability for
  every downstream checkpoint, in exchange for 7645 dead embedding rows.
- **REPORT line 131:** "an 8192 vocabulary" -> "an 8192-row vocab table" (the 3,145,728
  table-shape number unchanged).
- **REPORT Results Model paragraph:** "vocabulary 8192" -> "vocab table 8192 (547 ids
  live)" plus one sentence: 2,935,680 of the 13,891,584 parameters (7645 dead rows x 384
  dims, ~21%) are embedding rows for ids that can never occur in the training data or be
  decoded — counted in the headline because they are part of the shipped tensor.
- **REPORT demo decision Evidence:** one sentence documenting the shipped 08-07 mitigation
  — the demo masks the 7645 tokenizer-undecodable ids out of the logits before sampling
  (optional `forbid_ids` mask built once at launch from the frozen tokenizer's live
  vocabulary), so every in-UI slider setting, temperature 1.5 with top-k disabled included,
  can only produce decodable ids; pinned by `tests/test_forbid_ids.py`. Written after
  re-reading the merged 08-07 code (scripts/demo_app.py, generation/text.py, sampling.py)
  so the prose describes exactly what shipped.
- **REPORT Reproducibility (IN-01):** stale "126 passed, 1 skipped" replaced with unpinned
  phrasing (suite green; only skip is the CUDA-only fp16 smoke test, by design off-GPU).

### Task 2 — WR-03 clone-first quickstart + WR-04 notebook extra (`3923bd8`)

- **README "Run the demo" block:** new "# 1. Get the code" step —
  `git clone https://github.com/RAFAELDCOELHO/PersonaCore.git` + `cd PersonaCore` — before
  the venv lines; existing steps renumbered 2/3/4. The install, gh-release, and launch
  lines are byte-identical to before.
- **pyproject.toml:** `notebook = ["ipykernel~=7.3", "nbconvert~=7.17", "matplotlib~=3.10"]`
  — the same compatible-release pin the demo extra already carries (duplication intentional
  so each extra is self-sufficient). No new package enters the environment; no
  package-legitimacy gate applies (T-08H-02 accepted per plan).

## Verification Evidence

- Task 1 automated gate: `grep -c 547` README >= 1 (1), REPORT >= 3 (3); `2,935,680`
  present; `vocabulary 8192|an 8192 vocabulary` matches NOTHING (case-insensitive);
  `126 passed` gone; `undecodable` present; `12,636,922` in both files — PASS
- Task 2 automated gate: clone line precedes venv line; tomllib confirms notebook extra
  `['ipykernel~=7.3', 'nbconvert~=7.17', 'matplotlib~=3.10']`; `matplotlib~=3.10` count in
  pyproject.toml is exactly 2 — PASS
- `ruff check .` -> All checks passed; `ruff format --check .` -> 77 files already formatted
- Locked rigor signals: "NOT to the headline" intact; 2.1066 counts unchanged from pre-edit
  baseline (README 1, REPORT 3) and adjacent to its 12,636,922 denominator at all 4 sites;
  M2 still labeled upcoming in both files; ln(8192) at the training-curve line untouched;
  ablation cohort caveat untouched

## Threat Model Dispositions

- T-08H-01 (Repudiation, overclaimed vocabulary): **mitigated** — every claim now traces to
  the trainer's own warning with exact numbers and dead-row parameter accounting
- T-08H-02 (Tampering, notebook extra): **accepted** — matplotlib~=3.10 duplicates an
  already-audited, already-installed pin; zero new packages
- T-08H-03 (Spoofing, clone URL): **mitigated** — exact canonical URL copied from the
  release link the README already carried at line 57

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None — documentation-only plan; all described behavior (the CR-01 mask) exists and is
test-pinned in the merged 08-07 code.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes.

## Self-Check: PASSED

- FOUND: README.md (547 claim, clone-first quickstart)
- FOUND: docs/REPORT.md (547 x3, 2,935,680, undecodable, unpinned test count)
- FOUND: pyproject.toml (matplotlib~=3.10 in notebook extra, count 2)
- FOUND: commit 225a962 (Task 1)
- FOUND: commit 3923bd8 (Task 2)
- No file deletions in either commit
