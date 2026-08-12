---
phase: 09-lora-core
fixed_at: 2026-06-11T23:35:00Z
review_path: .planning/phases/09-lora-core/09-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 9: Code Review Fix Report

**Fixed at:** 2026-06-11T23:35:00Z
**Source review:** .planning/phases/09-lora-core/09-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5 (fix_scope: critical_warning — CR-01, CR-02, WR-01, WR-02, WR-03)
- Fixed: 5
- Skipped: 0

Full suite after all fixes: **189 passed, 1 skipped** (was 180 passed, 1 skipped — +9 new
tests pin the guarded behaviors). `ruff check` + `ruff format --check` clean. Byte-frozen
modules (`model/gpt.py`, `training/loop.py`) untouched.

## Fixed Issues

### CR-01: `enabled` toggle and `merged` state are mutually blind

**Files modified:** `src/personacore/lora/inject.py`, `tests/test_lora_merge.py`
**Commit:** 0ee8768
**Applied fix:** Added mutual `RuntimeError` guards across the toggle×merge state matrix —
`merge_lora` refuses when any module is disabled (folding a disabled delta would silently
enable the adapter), `set_adapter_enabled` and the `adapter_disabled` context manager refuse
while merged (the flag would be a silent dead switch), and `merged_state_dict` refuses on
disabled modules (live-logits parity would break). All checks are pre-pass over every module,
so a refusal mutates nothing — no partial folds, no partial flag flips. Five new tests pin
each refusal plus the atomicity of the partial-disable case. Behavioral tests verify the
refusal semantics directly (not just syntax), so this logic fix is pinned, not assumed.

### CR-02: `load_adapter_weights` audit covers keys but not shapes

**Files modified:** `src/personacore/lora/inject.py`, `tests/test_lora_inject.py`
**Commit:** 5ebd075
**Applied fix:** The P4 audit now also compares per-tensor `shape` and `dtype` against the
model's `lora_` tensors and raises a friendly `ValueError` naming the offending keys BEFORE
`load_state_dict(strict=False)` runs — closing the half-applied-artifact hole (strict=False
copies every shape-matching tensor before raising). Extended
`test_load_adapter_weights_raises_before_loading` with wrong-shape and wrong-dtype cases
(victim tensors proven bit-unchanged), and added `test_load_adapter_weights_refuses_wrong_rank`
pinning the r=8-onto-r=4 case (identical key names, different shapes).

### WR-01: Smoke script's documented kill-resume path does not exist

**Files modified:** `scripts/train_adapter_smoke.py`
**Commit:** 2f7d0b3
**Applied fix:** Implemented the documented resume semantics (the review's option (a)):
`train()` now receives `checkpoint_interval=CHECKPOINT_INTERVAL` (new tuned constant, 10) so
loop.py's in-loop Seam-4a save fires and a killed run loses <= 10 steps, plus
`resume_from=SMOKE_CKPT` when an incomplete smoke checkpoint exists. A COMPLETED checkpoint
(saved step >= MAX_STEPS) refuses loudly with instructions to delete it — resuming it would
train zero steps, return `final=None`, and crash the finite-loss check while proving nothing.
Docstring updated to describe the real mechanics.
**Status note — fixed: requires human verification.** Syntax, lint, and the `train()` keyword
API are verified, but a real killed-smoke resume was not executed end-to-end (needs a real
multi-minute MPS run on `best.pt`); confirm on the next smoke run.

### WR-02: `load_adapter` choke point validates only `schema_version`

**Files modified:** `src/personacore/checkpoint.py`, `tests/test_lora_artifact.py`
**Commit:** 507ae9f
**Applied fix:** After the schema gate, `load_adapter` now validates the artifact's structural
keys (`adapter` / `lora_config` / `base_fingerprint`) and raises a `ValueError` naming the
missing keys and the path — replacing the bare `KeyError`s that previously surfaced deep in
downstream consumers. Added parametrized `test_malformed_artifact_missing_key_raises` covering
all three missing-key cases (with `expected_fingerprint` passed, exercising the previously
unguarded `loaded["base_fingerprint"]` access).

### WR-03: Weight-corruption guards are `assert` statements — stripped under `python -O`

**Files modified:** `src/personacore/lora/layer.py`, `src/personacore/lora/inject.py`,
`scripts/train_adapter_smoke.py`, `tests/test_lora_merge.py`, `tests/test_lora_toggle.py`
**Commit:** 5b71975
**Applied fix:** Every corruption guard converted from `assert` to `raise RuntimeError`:
double merge and never-merged unmerge (layer.py), eject-while-merged, merge-in-train-mode,
and the merged `merged_state_dict` guard (inject.py). The smoke script's proof checks (wrap
count, trainable census, finite final loss, both canary branches) are now explicit
`raise SystemExit(...)` so the script can never exit 0 under `PYTHONOPTIMIZE` having proven
nothing; its docstring claim was updated to match. Guard tests changed from
`pytest.raises(AssertionError)` to `pytest.raises(RuntimeError)` with message matches.

## Skipped Issues

None — all in-scope findings were fixed. (IN-01 through IN-04 are outside `critical_warning`
scope; note WR-03's eject-guard test edit incidentally refreshed the stale "merge() lands in
Task 2" comment flagged by IN-04, but IN-04's `lora/__init__.py` docstring half remains open.)

---

_Fixed: 2026-06-11T23:35:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
