---
phase: quick-260902-dlo
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/fetch_demo_checkpoint.py
  - tests/test_demo_bootstrap.py
  - README.md
  - .gitignore
autonomous: true
requirements: []
must_haves:
  truths:
    - "`make demo`'s download helper refuses a `model_slim.pt` whose sha256 is not the one GitHub reports for the `m1-demo-v1` release asset (dd3bbb8f772e0b9556a0a31d535a1673d55f0d61d6d669c58a9aab6bb6247e24, 55,601,269 bytes) — the pin was read from `gh release view m1-demo-v1 --json assets` AND recomputed from the local file, and the two agree"
    - "A refused download leaves neither `checkpoints/model_slim.pt` nor its `.tmp` sibling on disk, and the error names the URL, the expected digest and the observed digest"
    - "A checkpoint already on disk is NOT re-hashed: `scripts/export_slim.py` legitimately regenerates a different artifact and the helper's contract is to leave a present file alone"
    - "Every pre-existing test in tests/test_demo_bootstrap.py still passes with its injected payload, because each now hands the helper the digest of the bytes it injects"
    - "The pending `.gitignore` rule for `.obsidian/` is committed, on its own, with no other change in that commit"
    - "ruff clean; the test suite gains tests and loses none"
  artifacts:
    - path: "scripts/fetch_demo_checkpoint.py"
      provides: "DEFAULT_SHA256 + post-download verification in ensure_slim_checkpoint"
      contains: "DEFAULT_SHA256"
    - path: "tests/test_demo_bootstrap.py"
      provides: "the pin equals the release digest; a tampered download is refused and leaves nothing; a present file is not re-hashed"
      contains: "DEFAULT_SHA256"
---

# Quick 260902-dlo — pin the release checkpoint's sha256 in `make demo`

## Why

Commit `f98c52f` (PR #2) made `make demo` download a 55.6 MB `model_slim.pt` from the public
`m1-demo-v1` release with `urllib.request.urlretrieve` and no integrity check. The file is then
loaded with `torch.load(..., weights_only=True)`, so a substituted file cannot execute code — but
it can silently be a *different model*, and this project's whole discipline is that a published
artifact is identified by its digest (`results/*.json` `sha256` fields, the `test_package.py`
pyproject pin, the Phase-24 `module_sha256` provenance guard). The one-command public path was
the only place a digest was not asserted.

## Tasks

1. `scripts/fetch_demo_checkpoint.py`: add `DEFAULT_SHA256`, a `sha256=` keyword on
   `ensure_slim_checkpoint`, and verify the temp file's digest before the rename into place.
   Mismatch → `RuntimeError` naming url / expected / observed; the existing `except` already
   removes the temp file. A present file is left alone (documented).
2. `tests/test_demo_bootstrap.py`: pass `sha256=hashlib.sha256(payload).hexdigest()` in the four
   payload-injecting tests; add the pin-equals-release test (hashes the local gitignored file
   when present, skips otherwise), the tampered-download refusal test, and the present-file
   not-rehashed assertion.
3. README TLDR: one clause saying the download is digest-verified.
4. Commit the pending `.gitignore` `.obsidian/` rule alone.

## Verification

- `.venv/bin/pytest tests/test_demo_bootstrap.py -q` green, +3 tests.
- `.venv/bin/ruff check . && .venv/bin/ruff format --check .` clean.
- `shasum -a 256 checkpoints/model_slim.pt` == `DEFAULT_SHA256` == the digest in
  `gh release view m1-demo-v1 --json assets`.
