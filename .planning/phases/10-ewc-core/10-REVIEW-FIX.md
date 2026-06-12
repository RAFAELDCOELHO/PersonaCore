---
phase: 10-ewc-core
fixed_at: 2026-06-12T21:05:00Z
review_path: .planning/phases/10-ewc-core/10-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 10: Code Review Fix Report

**Fixed at:** 2026-06-12T21:05:00Z
**Source review:** .planning/phases/10-ewc-core/10-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5 (fix_scope: critical_warning — WR-01..WR-05; IN-01..IN-03 excluded)
- Fixed: 5
- Skipped: 0

All fixes were applied in an isolated git worktree and fast-forwarded back into `main`.
Verification baseline after all fixes: full suite green (in-worktree run: 219 passed / 4 skipped
— the 3 extra skips vs the 222/1 baseline are "real slim artifact not present (CI)" caused by
the worktree lacking the gitignored `artifacts/` slim files, not by any code change; the
post-merge run in the main checkout reproduces the 222 passed / 1 skipped baseline). The
load-bearing golden-trajectory replay (`test_golden_trajectory_bit_identity`) RAN (not skipped)
and PASSED after every fix that touched `training/loop.py` or its tests. The golden fixture was
NOT regenerated. `make lint` (ruff check + format --check) green.

## Fixed Issues

### WR-01: `EWCPenalty.__call__` silently broadcasts on shape mismatch with the live model

**Files modified:** `src/personacore/continual/ewc.py`
**Commit:** 40a37b1 (+ formatting follow-up 2bdfbb1)
**Applied fix:** Added a live-model shape check in `__call__` directly after the existing
missing-key check: any fisher key whose shape differs from the same-named live parameter now
raises a named `ValueError` ("model parameter shape mismatch for keys [...]") instead of
silently broadcasting (or dying as an anonymous mid-run `RuntimeError`). Module docstring's
fail-loud contract updated to document the call-time shape validation. Verified by executing
the reviewer's exact scenario — fisher/theta_star of shape `(1, 2)` against a model param of
shape `(2, 2)` now raises the named `ValueError` (previously returned `penalty = 2.0`
silently). All 8 `tests/test_ewc_penalty.py` tests pass.

### WR-02: `checkpoint_extra` can silently clobber reserved checkpoint fields (`rng`, `schema_version`)

**Files modified:** `src/personacore/checkpoint.py`
**Commit:** 5c78d2b
**Applied fix:** Fixed at the root cause (`save_checkpoint`) rather than the loop conduit so
every caller is protected. Added module-level `_RESERVED_CKPT_KEYS` (the full core field set
including `rng` and `schema_version`) and a fail-loud guard at the top of `save_checkpoint`:
`**extra` keys colliding with reserved fields raise `ValueError` at SAVE time, naming the
clashing keys. Note: keys shadowing named parameters (`model`, `step`, ...) already raised
`TypeError` via Python keyword mechanics — the reachable gap was exactly `rng` /
`schema_version`. Verified by executing the reviewer's scenario through the public
`train(checkpoint_extra={"rng": "CLOBBERED", "schema_version": 999})` API — now raises
`ValueError: save_checkpoint: extra keys ['rng', 'schema_version'] collide with reserved
checkpoint fields` at save time instead of corrupting the checkpoint and failing opaquely at
resume. `tests/test_checkpoint.py`, `tests/test_fisher_checkpoint.py`, and
`tests/test_loop_penalty_fn.py` (20 tests) pass — the open-dict `**extra` seam
(fisher/theta_star) is unaffected.

### WR-03: `estimate_fisher` leaves the model in eval mode if a guard raises

**Files modified:** `src/personacore/continual/fisher.py`
**Commit:** 1723ed4
**Applied fix:** Wrapped the estimation body (named-parameter snapshot through `fisher_meta`
construction) in `try/finally`, with the conditional `model.train()` restore in the `finally`
block — the prior `model.training` flag is now restored on EVERY exit, including the
non-finite-Fisher and degenerate-normalizer fail-loud guards and any exception inside the
example loop, matching the docstring contract. Re-wrapped a few lines for the 100-char limit
(ruff-format normalized). Verified by executing the failure path: a constant-loss model fires
the degenerate-normalizer `ValueError`, and `model.training` is `True` afterward (previously
left stuck in eval mode). All 19 fisher tests pass.

### WR-04: Golden-replay skip gate omits torch version — a torch bump turns kernel drift into a hard failure

**Files modified:** `tests/test_loop_penalty_fn.py`
**Commit:** 2fbbf6d
**Applied fix:** Extended `_CAPTURE_PLATFORM` to include the fixture's recorded
`meta.platform.torch_version` and the skipif tuple to `(platform.system(),
platform.machine(), torch.__version__)`. The skip reason now names both the capture tuple and
the running torch version and instructs regeneration of the fixture (per the module-docstring
recipe) on a torch bump, instead of a hard failure misread as a loop regression. Module
docstring updated to match. Verified: on this machine (Darwin/arm64, torch 2.7.1 — exactly
the fixture's recorded capture environment) `test_golden_trajectory_bit_identity` still RUNS
and PASSES (confirmed with `pytest -v -rs`: PASSED, not SKIPPED). The fixture itself was not
touched.

### WR-05: `best_val_loss` resets to `inf` on resume — best.pt can regress after a kill+resume

**Files modified:** `src/personacore/training/loop.py`
**Commit:** cd86745
**Status note:** fixed — requires human verification (state-handling change; see below)
**Applied fix:** Used the review's ALTERNATIVE suggestion (dedicated open-dict field), not its
primary one — seeding from `ckpt["val_loss"]` would be semantically wrong because `latest.pt`
saves `val_loss=final_loss` (the last TRAIN loss), which could both fail to close the
regression window and wrongly block genuine best.pt updates. Implemented additively:
- All three `save_checkpoint` sites (best.pt, in-loop latest.pt, end-of-call latest.pt) now
  pass `best_val_loss=best_val_loss` through the open-dict `**extra` seam.
- On `resume_from`, `ckpt.get("best_val_loss")` seeds the running minimum; a missing key
  (any pre-fix checkpoint) falls back to `float("inf")` — the exact current behavior, so old
  checkpoints still resume (backward compatible per the open-dict contract).
- `best_val_loss` is deliberately NOT in WR-02's `_RESERVED_CKPT_KEYS`; a caller passing it
  via `checkpoint_extra` fails loud as a Python `TypeError` (duplicate keyword) at the call
  site. Docstrings (`resume_from`, `best_checkpoint_path`, `checkpoint_extra`) updated — note
  the `checkpoint_extra=None` claim is now "adds no caller keys" since the loop itself always
  records `best_val_loss` (one additive key vs v1.0 checkpoints; no pinned test asserts exact
  key sets).

Executed verification (not just syntax): scripted val-loss scenario — pre-kill best 1.0 at
step 3, kill, resume with all subsequent vals worse (2.0/1.5/2.5): best.pt is NOT overwritten
(stays 1.0; previously regressed to 2.0). Backward compat: a checkpoint with the
`best_val_loss` key deleted resumes cleanly and reproduces the legacy inf-fallback behavior.
The golden replay and all resume/best/checkpoint tests (16) pass; the trajectory is untouched
(the change only affects checkpoint contents and best-gating, not the hot path).

**Why human verification is requested:** the fix changes checkpoint semantics additively
(every checkpoint now carries a `best_val_loss` key). Behavior was verified by execution, but
the resume contract is load-bearing for Phases 12/13 (Fisher anchored at best.pt), so a human
eye on the semantics is warranted.

## Verification Summary

- Full suite in the fix worktree: 219 passed / 4 skipped (3 environment skips from missing
  gitignored `artifacts/` in the fresh worktree + the baseline CUDA skip).
- Full suite in the main checkout after fast-forward (`make test`): 222 passed / 1 skipped —
  exactly the pre-fix baseline counts, now with all five fixes in place.
- `ruff check .` and `ruff format --check .`: green.
- Golden-trajectory bitwise replay: RAN and PASSED on the capture platform after all fixes.
- Golden fixture `tests/fixtures/golden_trajectory_v1.json`: NOT regenerated, NOT modified.

## Skipped Issues

None — all five in-scope findings were fixed.

---

_Fixed: 2026-06-12T21:05:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
