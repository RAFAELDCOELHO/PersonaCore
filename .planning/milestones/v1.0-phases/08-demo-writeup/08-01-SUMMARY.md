---
phase: 08-demo-writeup
plan: 01
subsystem: checkpoint
tags: [pytorch, torch-load, weights-only, safe-load, slim-checkpoint, tdd]

# Dependency graph
requires:
  - phase: 01-scaffolding-reproducible-environment
    provides: open-dict checkpoint format + the reserved weights_only=True slim split (01-02 decision)
  - phase: 04-gpt-transformer-decoder
    provides: GPT(ModelConfig) with tied wte/lm_head (data_ptr identity) and prefix-free state_dict keys
  - phase: 05-pretraining
    provides: checkpoints/best.pt (step 49000, SHA 3a46815, val_loss ~0.7378)
  - phase: 06-generation-sampling
    provides: generate_text_str streaming/str surface used by the generation asserts
provides:
  - export_slim / load_slim / SLIM_SCHEMA_VERSION in src/personacore/checkpoint.py (load_slim is the single weights_only=True choke point for ALL slim consumers)
  - scripts/export_slim.py thin no-CLI driver (best.pt -> checkpoints/model_slim.pt)
  - checkpoints/model_slim.pt — the real 55.6 MB shippable artifact at /Users/juliorcoelho/PersonaCore/checkpoints/model_slim.pt (gitignored by design; distribution decided in 08-06)
  - tests/test_slim_checkpoint.py — 4 CPU-only tests, real-artifact test skips cleanly on CI
affects: [08-02 demo, 08-03 notebook, 08-06 distribution]

# Tech tracking
tech-stack:
  added: []
  patterns: [slim-vs-full checkpoint split, load_slim single choke point for weights_only=True]

key-files:
  created: [scripts/export_slim.py, tests/test_slim_checkpoint.py]
  modified: [src/personacore/checkpoint.py]

key-decisions:
  - "load_slim raises ValueError (not assert) on schema_version mismatch — survives python -O and gives a re-export hint"
  - "Mechanism generation test decodes via a total stub tokenizer: frozen tokenizer decodes STRICTLY (WR-03) over trained ids 0-538, so a random-init tiny model's argmax over [0,8192) raises by design; the real-artifact test keeps the frozen tokenizer end-to-end"
  - "Demo-extra install into the shared .venv was permission-blocked in the worktree — surfaced as user action, not worked around"

patterns-established:
  - "Slim consumers (demo 08-02, notebook 08-03, tests) must import load_slim — never call torch.load on the slim file directly"

requirements-completed: [DEMO-02, QA-01, QA-02]

# Metrics
duration: 13min
completed: 2026-06-10
---

# Phase 8 Plan 01: Slim Shippable Checkpoint Summary

**Slim fp32 inference checkpoint (55.6 MB vs best.pt's 159 MB) that loads under torch.load(weights_only=True) and generates on laptop CPU, with model_config + git_sha 3a46815 + step 49000 embedded (QA-02), via new export_slim/load_slim choke-point helpers**

## Performance

- **Duration:** ~13 min
- **Started:** 2026-06-10T16:25:26Z
- **Completed:** 2026-06-10T16:38:30Z
- **Tasks:** 3 (Task 1 TDD RED, Task 2 GREEN, Task 3 real-artifact export)
- **Files modified:** 3 source/test files + 1 generated artifact

## Accomplishments

- DEMO-02: `checkpoints/model_slim.pt` exported from `best.pt` — 55,601,269 bytes (in the 50–65 MB band), key set exactly `{schema_version, model, model_config, git_sha, step, val_loss}`, zero training state, loads under the restricted unpickler (`weights_only=True`) with zero code execution
- QA-02 (slim half): `git_sha` (3a46815…), `step` (49000), `val_loss` and the full `model_config` travel inside the shipped artifact and are asserted by test
- Weight tying survives the slim round-trip: GPT rebuilt from the artifact's own embedded config passes the `data_ptr()` identity assert; dedup-by-storage param count is exactly 13,891,584
- QA-01: full suite went 122 passed / 1 skipped -> 126 passed / 1 skipped (4 new tests, CUDA fp16 smoke still the only skip); `ruff check` + `ruff format --check` clean

## Task Commits

Each task was committed atomically:

1. **Task 1: RED test scaffold (tests/test_slim_checkpoint.py)** - `efcd11e` (test) — collection-time ImportError on export_slim/load_slim by design
2. **Task 2: export_slim/load_slim + scripts/export_slim.py** - `9277035` (feat) — 3 passed / 1 skipped, lint clean
3. **Task 3: real artifact export** - no commit (artifact is gitignored by design — Pitfall 3; verified 4 passed / 0 skipped + full suite green)

_TDD gate compliance: test commit `efcd11e` precedes feat commit `9277035`; no refactor commit needed._

## Files Created/Modified

- `src/personacore/checkpoint.py` - added `SLIM_SCHEMA_VERSION`, `export_slim` (drops optimizer/scheduler/scaler/rng/train_config; trusted-own-file `weights_only=False` read with T-08-02 justifying comment), `load_slim` (`weights_only=True` + schema_version check); module docstring updated from "will use" to "uses"
- `scripts/export_slim.py` - thin no-CLI driver: `_REPO_ROOT` constants, FileNotFoundError guard, prints path/size/keys/sha/step; no argparse, no preflight gate
- `tests/test_slim_checkpoint.py` - 4 tests: key-set strip (raw `weights_only=True` load IS the assertion), CPU rebuild + generate + `data_ptr()` tying, provenance travel, skipif-gated real-artifact test (param count 13,891,584, SHA prefix, 20-token greedy generation)
- `checkpoints/model_slim.pt` (generated, gitignored) - persisted to the main checkout at `/Users/juliorcoelho/PersonaCore/checkpoints/model_slim.pt`

## Decisions Made

- `load_slim` schema check raises `ValueError` with a re-export hint rather than a bare `assert` (assert strips under `python -O`; same spirit as the plan's "clear error message")
- The slim artifact was copied from the ephemeral worktree to the main checkout's `checkpoints/` so it survives worktree teardown — it is the gitignored local deliverable Wave-2 plans consume

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Mechanism generation test could not use the frozen tokenizer**
- **Found during:** Task 2 (turning the Task-1 tests green)
- **Issue:** The plan specified the tiny-model generation assert decode through `artifacts/tokenizer.json`. The frozen tokenizer's trained vocab covers only ids 0–538 (+ specials at 8184+) and decodes STRICTLY (WR-03) — a random-init tiny model's greedy argmax over the full locked [0, 8192) id space hits an unknown id (~93% of ids) and raises `ValueError` by design. The planned test design was structurally infeasible, not flaky.
- **Fix:** The mechanism test decodes via a total `_StubTokenizer` (the established `tests/test_generation_text.py` precedent for tiny random models). The real-artifact test keeps the frozen tokenizer end-to-end — that is where DEMO-02's "generates on laptop CPU" is actually proven against production artifacts.
- **Files modified:** tests/test_slim_checkpoint.py
- **Verification:** 3 mechanism tests pass; real-artifact test passes with the frozen tokenizer after Task 3
- **Committed in:** 9277035 (Task 2 commit)

**2. [Rule 3 - Blocking] Worktree lacked the gitignored checkpoints/ directory and shared venv**
- **Found during:** Task setup / Task 3
- **Issue:** `checkpoints/best.pt` and `.venv` are gitignored, so the ephemeral worktree had neither; the editable install also resolves `personacore` to the main checkout, not the worktree code.
- **Fix:** Created a gitignored `checkpoints/` dir in the worktree with a `best.pt` symlink to the main checkout; ran all tests/scripts with the shared venv's interpreter plus `PYTHONPATH=<worktree>/src`; copied the exported `model_slim.pt` to the main checkout so it persists after worktree teardown. No `pip install -e .` was run (would have repointed the shared venv's editable link at the ephemeral worktree).
- **Files modified:** none committed (local plumbing only; `git status` stayed clean throughout)
- **Verification:** ImportError in Task 1 referenced the WORKTREE's checkpoint.py path; main-checkout artifact verified loading via `load_slim` post-copy

---

**Total deviations:** 2 auto-fixed (1 bug in planned test design, 1 blocking environment issue)
**Impact on plan:** No scope creep. The stub-tokenizer change narrows nothing — the real frozen-tokenizer generation path is still proven by the real-artifact test.

## Issues Encountered

**Demo-extra install blocked (user action required).** Task 1's environment step — installing the `[demo]` extra (gradio 5.50.x + matplotlib) into the shared `.venv` — could not be executed:
1. The plan's literal command (`pip install -e ".[cpu,demo]"`) is forbidden from a worktree: it would repoint the shared venv's editable `personacore` link at the ephemeral worktree path and break the main checkout after cleanup.
2. The safe alternative (`pip install "gradio>=5,<6" "matplotlib~=3.10"` — the exact pyproject-pinned, audit-Approved packages) was denied by the execution-permission classifier (shared-infrastructure mutation requires explicit user authorization).

This does NOT affect DEMO-02/QA-01/QA-02 — nothing in this plan imports gradio/matplotlib — but Wave-2 plans (08-02 demo, 08-03 notebook) need it. See User Setup Required.

## User Setup Required

**Wave-2 demo environment needs one command, run from the MAIN checkout (not a worktree):**

```bash
cd /Users/juliorcoelho/PersonaCore && .venv/bin/pip install -e ".[cpu,demo]" --extra-index-url https://download.pytorch.org/whl/cpu
```

Then confirm: `.venv/bin/python -c "import gradio, matplotlib; print(gradio.__version__, matplotlib.__version__)"` prints a 5.50.x gradio. Running it from the main checkout keeps the editable link pointed at the real repo (safe), and installs only the pyproject-pinned, 08-RESEARCH-audited packages.

## Next Phase Readiness

- `checkpoints/model_slim.pt` (55.6 MB) exists in the main checkout and loads via `load_slim` — 08-02 (Gradio demo), 08-03 (notebook), and 08-06 (distribution) can all converge on it
- `load_slim` is the mandatory single choke point for slim consumers — Wave-2 code should import it, never raw `torch.load`
- BLOCKER for Wave 2: the `[demo]` extra (gradio/matplotlib) is NOT yet installed — see User Setup Required above
- REQUIREMENTS.md not edited here (worktree agent; orchestrator owns shared-file writes) — requirement IDs are in this file's `requirements-completed` frontmatter

---
*Phase: 08-demo-writeup*
*Completed: 2026-06-10*

## Self-Check: PASSED

All claimed files exist (including /Users/juliorcoelho/PersonaCore/checkpoints/model_slim.pt at 55,601,269 bytes); task commits efcd11e and 9277035 verified in git log (the docs metadata commit contains this file and cannot self-reference its final hash); required literals (weights_only=True, skipif, data_ptr()) present in tests.
