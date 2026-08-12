---
phase: 09-lora-core
plan: 04
subsystem: training
tags: [pytorch, lora, adapters, frozen-base, kill-resume, mps, smoke]

# Dependency graph
requires:
  - phase: 09-lora-core (plan 01)
    provides: inject_lora / mark_only_lora_trainable / snapshot_params / lora_state_dict + LoRAConfig
  - phase: 09-lora-core (plan 03)
    provides: export_adapter (persona-file artifact I/O with base fingerprint)
  - phase: 05-pretraining
    provides: best.pt (13.9M base checkpoint), TinyStories train.bin/val.bin memmaps, the untouched train()
provides:
  - LORA-02 test pins: bit-level frozen-base canary, optimizer-state census (12*n_layer), D-04 kill+resume trajectory, lora_config **extra round-trip
  - scripts/train_adapter_smoke.py — real-weights MPS proof + first exported adapter.pt (~1.35 MB persona file)
  - ROADMAP success criteria 2 and 5 satisfied (unit-pinned AND proven on real weights)
affects: [phase-12 fine-tune harness, phase-14 persona adapter training, phase-15 delta-w]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Adapter TrainConfig always overrides weight_decay to 0.0 (the 0.1 default fights low-rank updates)"
    - "Canary requires >= 2 effective steps: B=0 at init makes lora_A's first-step grad identically zero"
    - "Deterministic resume reconstruction: vanilla GPT -> load base -> inject -> freeze, identical order on resume"
    - "Tests pin RuntimeConfig(device='cpu') explicitly so torch.equal snapshots stay same-device on MPS hosts"

key-files:
  created:
    - tests/test_lora_training.py
    - scripts/train_adapter_smoke.py
  modified: []

key-decisions:
  - "Tests pass runtime_config=RuntimeConfig(device='cpu') explicitly — implements the plan's CPU-only/GPU-free requirement and keeps snapshot/post-train tensors same-device for torch.equal on the MPS dev box"
  - "Copied gitignored best.pt + train.bin/val.bin (+ model_slim.pt) from the main checkout into the worktree via APFS clonefile so the smoke and the 09-03 skipif tests ran locally (09-03 precedent; nothing enters version control)"
  - "Smoke script does not wire resume_from into its train() call (plan spec); the docstring documents the resume semantics via the deterministic LORA_CFG rebuild order"

patterns-established:
  - "The smoke script IS the proof: inline asserts (census, isfinite, canary) exit non-zero on failure"
  - "Smoke outputs get their own gitignored paths (adapter_smoke.pt / adapter_smoke.csv) — never the pretrain curve CSV"

requirements-completed: [LORA-02, LORA-05]

# Metrics
duration: 12min
completed: 2026-06-11
---

# Phase 9 Plan 04: Frozen-Base Adapter Training Proof Summary

**Frozen-base discipline proven through the byte-untouched v1.0 train(): 4 CPU pins (bit-level canary, 12*n_layer optimizer-state census, 1e-6 kill+resume, lora_config **extra seam) plus a real-weights MPS smoke that trained 50 adapter steps on best.pt + TinyStories and exported the first 1.35 MB adapter.pt persona file**

## Performance

- **Duration:** 12 min
- **Started:** 2026-06-11T22:15:36Z
- **Completed:** 2026-06-11T22:27:26Z
- **Tasks:** 2
- **Files modified:** 2 created, 0 existing modified

## Accomplishments

- After a 6-step adapter run through the UNTOUCHED `train()`, every `lora_` param moved (`not torch.equal`) and every frozen base param is bit-identical (`torch.equal`) to its pre-training snapshot — LORA-02's core claim, pinned on a tiny GPT and proven again on the real 13.9M `best.pt` on MPS
- The `train()`-saved checkpoint's AdamW state holds entries ONLY for the stepped A/B params (`12 * n_layer` — no state bloat for the frozen base), pinned against regression
- Kill+resume of an adapter run reproduces the uninterrupted trajectory (final loss within 1e-6, `lora_B` within 1e-6) via the deterministic vanilla → inject → freeze reconstruction order (D-04)
- `lora_config` rides `save_checkpoint(**extra)` and reloads intact, so the resume path can rebuild the injected module tree from the checkpoint alone (D-04 open-dict seam)
- The smoke script ran on the preflight device (MPS, torch 2.7.1): 36 wrappers injected, 331,776-param census verified on real shapes, finite final loss (0.7353), canary green at 13.9M scale, and `adapter.pt` exported at 1.35 MB with the base fingerprint read from `best.pt` — the persona-file story made measurable (LORA-05 / ROADMAP criterion 5)
- Zero edits to `training/loop.py`, `model/gpt.py`, `checkpoint.py`, or any v1.0 module (diff vs base contains exactly the two new files); full suite 180 passed / 1 skipped, lint clean

## Task Commits

Each task was committed atomically:

1. **Task 1: Grad-isolation, optimizer-scope, kill+resume, and **extra seam tests** - `dcd527a` (test)
2. **Task 2: Real-weights adapter smoke script (best.pt + TinyStories bins, MPS canary, adapter export)** - `141b81e` (feat)

## Files Created/Modified

- `tests/test_lora_training.py` — 4 CPU-only LORA-02/D-04 pins (198 lines): canary + frozen-base bit-identity, optimizer-state census, kill+resume trajectory (adapting `test_resume_curve.py` to the injected GPT), `lora_config` **extra round-trip; module docstring documents the B=0-makes-A's-first-step-grad-zero caveat and the >= 2-effective-steps canary requirement
- `scripts/train_adapter_smoke.py` — thin no-CLI real-weights driver (168 lines): MPS-fallback env before torch import, `_REPO_ROOT` constants, `preflight_device(strict=True)` gate, load-before-inject ordering, census asserts, 50-step run with `WEIGHT_DECAY = 0.0`, isfinite + canary inline asserts, `export_adapter` tail printing the persona-file size

## Decisions Made

- Pinned `RuntimeConfig(device="cpu")` in every test `train()` call: the plan requires CPU-only/GPU-free tests, and on this MPS-capable host the default device resolution would move the model to MPS — making `torch.equal(cpu_snapshot, mps_param)` raise cross-device. Explicit CPU pinning implements the stated constraint deterministically on any host
- Copied the gitignored `best.pt`, `train.bin`, `val.bin`, and `model_slim.pt` from the main checkout into the worktree (APFS clonefile — instant, no extra disk) so the smoke script and 09-03's skipif-gated real-artifact tests exercised the full flow locally; all stay untracked/ignored
- Kept the smoke script's `train()` call without `resume_from` wiring (per the plan's explicit call spec); the module docstring documents how a killed run resumes via the script's own `LORA_CFG` deterministic rebuild

## Deviations from Plan

None - plan executed exactly as written.

## TDD Gate Compliance

Task 1 is marked `tdd="true"` but is a test-only pin over the deliberately UNTOUCHED v1.0 `train()` — the plan's entire point is that the existing loop is already frozen-param safe (09-RESEARCH Pattern 3, empirically verified), so no implementation step exists and no conventional RED stage is possible. The 4 tests passing on first run (commit `dcd527a`, `test(...)`) is the expected, load-bearing outcome — the same precedent as 09-03's Task 2. `git diff` confirms zero `training/` paths changed, satisfying the task's acceptance criterion that the feature deliberately already existed.

## Issues Encountered

None. Baseline suite was verified green (173 passed / 4 skipped) before Task 1; final suite is 180 passed / 1 skipped (the +3 formerly-skipped tests are 09-02/09-03 skipif gates that now run with `model_slim.pt` present locally; the 1 remaining skip and 1 warning are pre-existing and unrelated).

## Known Stubs

None — no placeholder values, TODO/FIXME markers, or unwired data paths in either file.

## Threat Model Compliance

| Threat | Disposition | Implemented |
|--------|-------------|-------------|
| T-09-11 (EoP via torch.load(best.pt, weights_only=False)) | accept | TRUSTED-only inline comment on the script's own-checkpoint read; the shareable artifact path stays weights_only=True via export_adapter/load_adapter |
| T-09-12 (run outputs committed to repo) | mitigate | adapter.pt / adapter_smoke.pt / adapter_smoke.csv all confirmed via `git check-ignore`; `git status --porcelain` clean post-run; smoke trains on public TinyStories only |
| T-09-13 (silent MPS training failure) | mitigate | params-actually-update canary on the real device + `math.isfinite` final-loss guard + bit-untouched base assert; inline asserts exit non-zero |
| T-09-SC (supply chain) | accept | zero packages installed |

No new security surface introduced beyond the plan's threat model.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 9 is complete: all four plans (core, toggle/merge, artifact, training proof) have SUMMARYs; all five ROADMAP success criteria for LoRA core are test-pinned, with criteria 2 and 5 additionally proven on real weights
- The smoke script is the template for Phase 14's persona adapter training runs (teach-then-recall will swap TinyStories bins for teaching data)
- `adapter.pt` + `load_adapter` + the deterministic rebuild order form the exact load path Phase 14's demo consumes
- No blockers

## Self-Check: PASSED

- Both created files exist on disk (`tests/test_lora_training.py` 198 lines, `scripts/train_adapter_smoke.py` 168 lines)
- Both task commits present in git log (dcd527a, 141b81e)
- All acceptance criteria re-verified PASS (both tasks; grep + collection + size + check-ignore gates logged above)
- Plan verification re-run: 4/4 new tests green in 1.35s, smoke exit 0 with 1.35 MB adapter.pt, `make test` 180 passed / 1 skipped, `make lint` clean, `git status --porcelain` empty
- Diff vs base 33f4f55 contains exactly the two plan files — loop.py/gpt.py/checkpoint.py byte-untouched

---
*Phase: 09-lora-core*
*Completed: 2026-06-11*
