---
phase: 10-ewc-core
plan: 03
subsystem: continual-learning
tags: [ewc, fisher, checkpoint, persistence, weights-only, safetensors-bar]

# Dependency graph
requires:
  - phase: 10-ewc-core plan 01 (wave 1)
    provides: estimate_fisher (per-example diagonal Fisher, mean-normalized, D-05 stats) + EWCPenalty
  - phase: 05-training (via v1.0)
    provides: save_checkpoint(**extra) open-dict seam + load_checkpoint full-dict return
  - phase: 09-lora (via v1.0)
    provides: export_adapter/load_adapter schema-gate precedent + train_adapter_smoke.py script shape
provides:
  - FISHER_SCHEMA_VERSION = 1 + export_fisher/load_fisher in src/personacore/checkpoint.py — the schema-versioned weights_only=True Fisher-cache choke point Phases 12/13 share
  - Test-pinned **extra persistence: fisher/theta_star/ewc_lambda/fisher_meta round-trip by value with tied-tensor dedup (wte.weight once, lm_head.weight absent)
  - scripts/estimate_fisher_tinystories.py — the real-weights Fisher run at best.pt (N=2000, D-04) with ten SystemExit proof checks and the production cache writer
affects: [12-lambda-sweep, 13-ab-eval]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fisher cache fingerprint mismatch is a HARD ValueError (unlike the adapter's D-02 warn-but-load): a Fisher estimated at different weights is mathematically wrong for the anchor; re-estimation costs <1 min"
    - "Refuse-to-rerun on an existing production cache (Open Q3): provenance for Phases 12/13 stays stable; delete-to-re-estimate is an explicit decision"
    - "Proof checks as raise SystemExit, never assert (survives python -O) — 09-04 house pattern carried forward"

key-files:
  created:
    - tests/test_fisher_checkpoint.py
    - scripts/estimate_fisher_tinystories.py
  modified:
    - src/personacore/checkpoint.py

key-decisions:
  - "load_fisher fingerprint mismatch raises ValueError (plan Test 6's explicit spec) rather than load_adapter's warn-but-load — the plan's action text said 'replicating load_adapter's semantics' but the TDD behavior spec demanded a raise; the raise is also the mathematically correct disposition for a weight-anchored Fisher"
  - "Test docstring cites T-10-06 (the cache safe-load mitigation the threat register pins to Tests 3-6) instead of the plan's 'T-10-05 safe-load bar' wording — T-10-05 is the trusted best.pt load, which lives script-side"
  - "Production cache produced and verified in the worktree; NOT copied into the main checkout (explicit no-main-checkout-writes boundary) — one-command regeneration documented below"

patterns-established:
  - "Cache loaders mirror load_adapter verbatim: schema gate FIRST, sorted missing-key ValueError second, fingerprint check last"
  - "Worktree runs bridge gitignored input artifacts (best.pt, train.bin) via file symlinks inside real gitignored dirs, keeping the committed script's _REPO_ROOT-relative paths canonical"

requirements-completed: [EWC-01]

# Metrics
duration: 14min
completed: 2026-06-12
---

# Phase 10 Plan 03: Fisher Persistence + Real-Weights Estimation Summary

**Fisher/theta_star persistence pinned through the open-dict `save_checkpoint(**extra)` seam with tied-tensor dedup, a schema-versioned `weights_only=True` Fisher cache (`export_fisher`/`load_fisher`), and the real N=2000 estimation actually run at the 13.9M `best.pt` anchor with spearman_half=0.9886 convergence evidence (D-04/D-05)**

## Performance

- **Duration:** ~14 min
- **Started:** 2026-06-12T19:19:44Z
- **Completed:** 2026-06-12T19:34:00Z
- **Tasks:** 2 (Task 1 TDD, Task 2 script+run)
- **Files modified:** 2 created, 1 modified

## Accomplishments

- EWC-01's persistence clause is test-pinned: `fisher`/`theta_star`/`ewc_lambda`/`fisher_meta` round-trip BY VALUE through `save_checkpoint(**extra)`/`load_checkpoint` into a fresh model, every tensor `torch.equal` (not `data_ptr` — pointers legitimately change across serialization)
- Pitfall 1 dedup pinned through the seam: `lm_head.weight` absent from both reloaded dicts, `wte.weight` present, exactly one `theta_star` entry per distinct param storage
- `export_fisher`/`load_fisher` land in `checkpoint.py` behind `FISHER_SCHEMA_VERSION = 1`, mirroring the `export_adapter`/`load_adapter` precedent: single `weights_only=True` choke point, schema gate FIRST, missing-key `ValueError` naming sorted gaps, anchor-fingerprint check; `checkpoint.py` never imports `continual/` (locked dependency direction); no `theta_star` in the cache (recoverable from `best.pt`, which the fingerprint pins)
- The Fisher was ACTUALLY estimated at `best.pt` (step 49000, val_loss 0.7378, 13.9M params, MPS) over 2000 TinyStories `train.bin` windows in 48.3s wall-clock — roadmap success criterion 1's real-weights half
- All ten `raise SystemExit` proof checks passed on real weights: every Fisher tensor finite and non-negative; tied storage counted once; global mean exactly 1.0 within 1e-5 (fp64 on CPU); `EWCPenalty` exactly `0.0` at the anchor; penalty > 0 under a 1e-3 perturbation
- D-05 convergence evidence reported (not gated): spearman_half=0.988620, rel_mean_change_a=0.002026, rel_mean_change_b=0.002026 — N=2000 is a measured "enough"
- Production cache `checkpoints/fisher_tinystories.pt` (55.60 MB) written via `export_fisher`, loads through `load_fisher` (`weights_only=True`) with n_examples=2000 and the anchor fingerprint `{git_sha: 3a46815…, step: 49000, val_loss: 0.7378}`; a second run refuses with the delete-to-re-estimate message
- Full suite green: 213 passed, 4 skipped (pre-existing environment gates); `ruff check` + `ruff format --check` clean

## Task Commits

1. **Task 1: Fisher persistence pins (RED)** - `a19a021` (test) — ten failing pins (seam round-trip, dedup, cache gates)
2. **Task 1: export_fisher/load_fisher (GREEN)** - `e45d5d4` (feat) — checkpoint.py additions
3. **Task 2: real-weights Fisher run** - `34e3dd3` (feat) — scripts/estimate_fisher_tinystories.py

## TDD Gate Compliance

Task 1 followed RED→GREEN: `a19a021` (test, collection-failing on the absent import surface) precedes `e45d5d4` (feat, all 10 pass). No refactor commit needed — GREEN landed lint-clean.

## Files Created/Modified

- `src/personacore/checkpoint.py` - `FISHER_SCHEMA_VERSION = 1` below the adapter constant; `export_fisher` (tensors+primitives only, returns what it wrote); `load_fisher` (weights_only=True choke point, schema/missing-key/fingerprint gates) — `save_checkpoint`/`load_checkpoint` untouched (+71 lines)
- `tests/test_fisher_checkpoint.py` - Ten pins: **extra round-trip, dedup-through-seam, exact-key safe-load, schema gate, parametrized missing-key gate, fingerprint mismatch raises / match loads, no-theta_star (203 lines)
- `scripts/estimate_fisher_tinystories.py` - 09-04-shaped thin driver: MPS-fallback env before torch import, `_REPO_ROOT` constants, `N_EXAMPLES = 2000`/`SEED = 1234`/`EWC_LAMBDA = 1.0` tuned block, `preflight_device(strict=True)` gate, FileNotFoundError prerequisites, refuse-to-rerun, trusted anchor load, ten SystemExit proof checks, fingerprint read from the blob (197 lines)

## Decisions Made

- **Fingerprint mismatch = hard ValueError, not warn-but-load:** the plan's Test 6 behavior spec explicitly demanded `ValueError` while its action text said "replicating load_adapter's semantics" (which warns). Resolved in favor of the explicit test spec: unlike an adapter (D-02 — base evolves mid-milestone), a Fisher estimated at different weights gives WRONG importance weights for the loaded anchor, and re-estimation costs under a minute, so a hard error is the safe and cheap disposition. The check otherwise replicates `load_adapter`'s shape (optional `expected_fingerprint`, message naming both fingerprints).
- **Threat-ID citation corrected in the test docstring:** the plan asked the docstring to name "the T-10-05 safe-load bar", but the plan's own threat register assigns the cache safe-load mitigation (test-pinned, Tests 3-6) to **T-10-06**; T-10-05 is the trusted `weights_only=False` `best.pt` load in the script. The docstring cites T-10-06 and mentions T-10-05's script-side role.
- **EWC-01 checked off in REQUIREMENTS.md:** 10-01 deferred it pending this plan's persistence half; both halves (estimation 10-01, persistence + real-weights run here) now exist.

## Deviations from Plan

### Environment-driven

**1. [Worktree] Input artifacts bridged via symlinks; production cache not persisted to the main checkout**
- **Found during:** Task 2 setup/wrap-up
- **Issue:** `best.pt`/`train.bin` are gitignored and live only in the main checkout; this executor runs in an isolated worktree with an explicit no-main-checkout-writes boundary (copy attempt was denied by policy)
- **Fix:** created real (gitignored) `checkpoints/`/`data/` dirs in the worktree with file symlinks to the main checkout's `best.pt`/`train.bin`, keeping the committed script's `_REPO_ROOT`-relative paths canonical; the script ran, all proof checks passed, and the cache was verified through `load_fisher` in the worktree
- **Consequence:** the worktree (and the 55.6 MB cache in it) is removed after merge — see User Setup Required for the one-command regeneration
- **Files modified:** none (symlinks and cache are gitignored runtime artifacts)

Otherwise the plan executed as written.

## Issues Encountered

- The single full-suite warning (`tests/test_tokenizer_io.py` corpus-exhausted UserWarning) is pre-existing and unrelated; the new test file passes under `pytest -W error`.

## Known Stubs

None — no placeholders, hardcoded empty values, or unwired data paths. `EWC_LAMBDA = 1.0` is the documented Phase-10 placeholder convention (the real lambda is Phase 12's sweep, EWC-03), not a stub.

## User Setup Required

**Regenerate the production Fisher cache after merge** (the worktree copy does not survive worktree removal). From the main checkout root:

```bash
source .venv/bin/activate && python scripts/estimate_fisher_tinystories.py
```

~50s on MPS; deterministic inputs (SEED=1234, anchor `best.pt` step 49000) reproduce the same cache contract — `checkpoints/fisher_tinystories.pt`, n_examples=2000, fingerprint read from the blob. The script refuses to overwrite an existing cache.

## Next Phase Readiness

- Phases 12/13 load one shared estimation pass through `load_fisher(path, expected_fingerprint={git_sha, step, val_loss})` — mismatches fail loudly instead of silently corrupting the A/B
- Resume checkpoints stay self-contained: the wave-2 sibling (10-02) splices `penalty_fn` into the loop, and `save_checkpoint(fisher=..., theta_star=..., ...)` is now a test-pinned contract for it to persist EWC state by value
- Convergence baseline recorded for D-05 claims: spearman_half=0.9886 at N=2000 (halves of 1000 each), rel mean change ~0.2%

## Self-Check: PASSED

- All 3 plan files exist on disk (checkpoint.py modified; tests + script created)
- All 3 task commits present in git log (a19a021, e45d5d4, 34e3dd3)
- `pytest -q`: 213 passed, 4 skipped; `make lint` clean
- `checkpoints/fisher_tinystories.pt` (55,598,661 bytes) loads via `load_fisher` with n_examples=2000 and no `theta_star`; rerun refused; `git status --porcelain checkpoints/` empty

---
*Phase: 10-ewc-core*
*Completed: 2026-06-12*
