---
phase: quick-260605-lgy
plan: 01
subsystem: device-layer
tags: [mps, apple-silicon, preflight, runtime-config, device-resolution]
requires: []
provides:
  - "RuntimeConfig MPS device resolution (fp32, AMP off — mirrors CPU posture)"
  - "preflight_device with CUDA-P100 -> MPS -> CPU priority (renamed from preflight_p100)"
affects:
  - src/personacore/config.py
  - src/personacore/preflight.py
  - scripts/preflight_demo.py
tech-stack:
  added: []
  patterns:
    - "Device priority CUDA -> MPS -> CPU as the single source of device truth (RuntimeConfig + preflight_device)"
    - "strict= gate semantics (long-run refuse-to-start vs laptop/CI degrade-to-summary)"
key-files:
  created: []
  modified:
    - src/personacore/config.py
    - src/personacore/preflight.py
    - scripts/preflight_demo.py
    - tests/test_config.py
    - tests/test_preflight.py
decisions:
  - "MPS mirrors the CPU posture exactly: fp32, AMP forced off (D-02). No fp16 AMP on Apple Silicon."
  - "Hard rename preflight_p100 -> preflight_device with NO deprecated alias (D-02); require_p100 bool replaced by strict bool preserving the same gate intent."
  - "MPS is a usable long-run device under D-01 — preflight_device returns mps without raising even when strict=True."
metrics:
  duration: ~6 min
  completed: 2026-06-05
---

# Phase quick-260605-lgy Plan 01: Add MPS Support to the Device Layer Summary

MPS (Apple Silicon) is now a first-class device in the device layer — `RuntimeConfig`
resolves `device="mps"` (fp32, AMP off, mirroring the CPU posture) and the renamed
`preflight_device` gate accepts MPS as a usable long-run device while keeping the P100/CUDA
path and bf16-on-Pascal guard fully intact.

## What Was Built

- **Task 1 (TDD):** Extended `_default_device()` to resolve CUDA -> MPS -> CPU and extended
  `RuntimeConfig.__post_init__` so the AMP-off branch fires on `"cpu"` OR `"mps"`. The
  bf16-on-Pascal guard is untouched; `autocast()` already splits on `":"` so it is correct
  for `"mps"`. Module docstring updated ("AMP auto-disabled on CPU and MPS").
- **Task 2 (TDD):** Hard-renamed `preflight_p100` -> `preflight_device` (no alias). Replaced
  `require_p100: bool` with `strict: bool` carrying the same intent. Detection order:
  CUDA-P100 (full P100 name check + Pascal sm_60 smoke op when strict) -> MPS (returns
  `{"device":"mps","cc":None,...}`, never raises) -> CPU (raises when strict, degrades to a
  summary dict when not).
- **Task 3:** Updated the thin `scripts/preflight_demo.py` caller to
  `preflight_device(strict=False)` and reframed its docstring to the device-priority
  framing. Verified end-to-end: the script resolves `device=mps` on the M3 dev box.

## Verification

- `tests/test_config.py`: 11 passed (3 new MPS tests; bf16-on-Pascal + fp16-ok-on-Pascal
  unchanged and green).
- `tests/test_preflight.py`: 5 passed (T4-reject + P100-non-strict-ok retained; MPS-ok,
  CPU-raises-when-strict, CPU-ok-when-not-strict added).
- Full CPU-only suite: 95 passed, 1 skipped (pre-existing GPU-only fp16 smoke skip), 1
  warning (pre-existing tokenizer corpus-exhaustion warning, out of scope).
- `ruff check .` and `ruff format --check .` both clean.
- `grep -rn "preflight_p100" src scripts tests` -> FULLY REMOVED (hard rename complete).
- Smoke ran `scripts/preflight_demo.py`: prints `device=mps`, returns the MPS summary dict.

All tests run CPU-only via monkeypatching `torch.cuda.is_available` /
`torch.backends.mps.is_available` — no MPS or CUDA hardware required.

## must_haves Coverage

- On M3 (no CUDA) `RuntimeConfig()` resolves `device="mps"`, amp forced False — covered by
  `test_default_device_mps_when_no_cuda` + `test_amp_off_on_mps` (verified live by the demo).
- On a CUDA P100 box `RuntimeConfig()` still resolves `device="cuda"` and the bf16-on-Pascal
  guard still raises — covered by `test_default_device_cuda_when_available` +
  `test_bf16_raises_on_pascal` (unchanged).
- On CPU-only, `device="cpu"` with amp False (unchanged) — `test_default_device_cpu_when_neither`.
- `preflight_device` detects CUDA-P100 -> MPS -> CPU and returns an env-summary dict — the
  five preflight tests.
- `preflight_p100` no longer exists (hard rename) — grep confirms removal.
- Full CPU-only suite green with no MPS/CUDA hardware required.

## Deviations from Plan

None - plan executed exactly as written.

## Environment Note

No `.venv` existed in this fresh worktree, so a Python 3.11 venv was created per CLAUDE.md
(`python3.11 -m venv .venv` + `pip install -e ".[cpu,dev]" --extra-index-url
https://download.pytorch.org/whl/cpu`). torch 2.7.1 (CPU), ruff 0.15.16. The local 3.14
interpreter was never used. `.venv` is gitignored.

## Worktree Base Correction

The worktree spawned on `3e3af54` but the plan and its execution base is
`73b375f` (the pre-dispatch plan commit). Per the worktree_branch_check Step 2,
hard-reset HEAD to `73b375f` before any work (the plan file did not exist on the prior
base). All five task commits sit on top of `73b375f`.

## Known Stubs

None — both source files implement real device-resolution logic; no placeholder data flows.

## Self-Check: PASSED

All five modified files present; all five task commits (0952f9e, 30a015f, e4ac294,
bddbbd7, a3513e8) found in git history.
