---
phase: quick-260902-dlo
plan: 01
status: complete
subsystem: demo-bootstrap
tags: [integrity, sha256, make-demo, provenance, repo-hygiene]

requires:
  - phase: none
    provides: "PR #2 (`f98c52f`..`8875b0d`), the one-command `make demo` path and its download helper"
provides:
  - "scripts/fetch_demo_checkpoint.py verifies the downloaded model_slim.pt against DEFAULT_SHA256 before renaming it into place"
  - "tests/test_demo_bootstrap.py: pin equals the release digest (and the local export when present), tampered download refused with no residue, opt-out explicit"
  - "local main fast-forwarded 10 commits onto origin/main; .gitignore `.obsidian/` committed alone"
affects: [make demo, README TLDR]

tech-stack:
  added: []
  patterns:
    - "network-provided bytes are digest-checked; a present local artifact is not (export_slim.py legitimately differs)"

key-files:
  created: []
  modified:
    - scripts/fetch_demo_checkpoint.py
    - tests/test_demo_bootstrap.py
    - README.md
    - .gitignore

metrics:
  commits: [142cec0, 4d2dcb7]
  tests_added: 3
  suite: "2013 passed, 1 skipped, 0 failed in 1264.22s (full suite on the merged tree, M3, flag unset); tests/test_demo_bootstrap.py 14 passed"
  lint: "ruff check + ruff format --check clean (261 files)"
---

# Quick 260902-dlo — summary

## What was measured before anything was written

- Local `main` was **10 commits behind `origin/main`** with nothing to push. The remote commits
  are PR #1 (CI green on ubuntu without hiding the 9 failures: two glibc epsilon twins recorded
  beside the M3 pin, checkpoint-on-disk halves skipping with the reason named, the venue skip
  literal split into two pinned integers), PR #2 (`make demo`, LICENSE MIT, `license = "MIT"` in
  pyproject with `test_package.py`'s digest pin moved in the same commit) and CITATION.cff. All
  owner-merged; the diff was read in full before `git merge --ff-only origin/main`.
- `gh release view m1-demo-v1 --json assets` reports
  `sha256:dd3bbb8f772e0b9556a0a31d535a1673d55f0d61d6d669c58a9aab6bb6247e24` for
  `model_slim.pt` (55,601,269 bytes); `shasum -a 256 checkpoints/model_slim.pt` gives the same
  digest. The pin is a measurement, not a transcription.
- The pre-fix helper accepted `b"not-the-release"` as `model_slim.pt`; the new test is RED on it
  by construction (proved by loading `git show HEAD:scripts/fetch_demo_checkpoint.py` beside the
  new module and running the same tampered fetch through both).

## What changed

- `ensure_slim_checkpoint(dest, *, url, sha256=DEFAULT_SHA256, fetch)`: after the non-empty
  check and before `tmp.replace(dest)`, the temp file is hashed in 1 MiB chunks; a mismatch raises
  `RuntimeError` naming url / expected / observed and the existing `except` removes the temp file.
  A present `dest` is returned untouched and never hashed. `sha256=None` disables the check.
- README TLDR: one clause saying the download is verified against the pin.
- `.gitignore`: `.obsidian/` committed on its own (`142cec0`).

## Verification

- `tests/test_demo_bootstrap.py`: 14 passed (11 + 3).
- Full suite on the merged tree: **2013 passed, 1 skipped, 0 failed** (21:04). The Phase-25
  deferred item D1 (`test_production_resume_epsilon_bit_identical`) passed in this run; its two
  `results/phase23_resume_probe_*` scratch directories were scrubbed by the test's own `finally`.
- `ruff check .` and `ruff format --check .` clean.
- `python scripts/fetch_demo_checkpoint.py` on this machine: present file returned, no fetch.

## Not done, and why

- No LICENSE decision was needed — PR #2 already added MIT.
- Phase 25 plan 25-14 is still at its human gate (`sudo pmset`, `launchctl bootstrap`); it is
  operator machine state and was not touched.
- README's "~400 CPU-only tests" line is stale (the suite is 2013) but sits under the project's
  append-only discipline; left for a dated note when the next results section lands.
