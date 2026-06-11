---
phase: 09-lora-core
reviewed: 2026-06-11T22:39:05Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - scripts/train_adapter_smoke.py
  - src/personacore/checkpoint.py
  - src/personacore/lora/__init__.py
  - src/personacore/lora/config.py
  - src/personacore/lora/inject.py
  - src/personacore/lora/layer.py
  - tests/test_lora_artifact.py
  - tests/test_lora_inject.py
  - tests/test_lora_layer.py
  - tests/test_lora_merge.py
  - tests/test_lora_toggle.py
  - tests/test_lora_training.py
findings:
  critical: 2
  warning: 3
  info: 4
  total: 9
status: issues_found
---

# Phase 9: Code Review Report

**Reviewed:** 2026-06-11T22:39:05Z
**Depth:** standard
**Files Reviewed:** 12
**Status:** issues_found

## Summary

Reviewed the full Phase-9 LoRA core: the `LoRALinear` wrapper, injection/freeze/toggle/eject/merge
machinery, the adapter persona-file artifact seam in `checkpoint.py`, the real-weights smoke
script, and all six test files. The from-scratch math is correct (delta shapes, scale
single-source, B=0 identity gate, closed-form param census all verified), the load-then-inject
ordering is enforced by tests, and the safe-load split (`weights_only=True` for shareable
artifacts, trusted-only full pickle for resume checkpoints) is consistently applied. All 43 tests
pass in the project venv.

However, adversarial probing of state-combination edges found two Critical defects, both
empirically confirmed by execution (not speculation):

1. The `enabled` flag and the `merged` state are mutually blind — toggling the adapter while
   merged is a silent no-op, and merging folds the delta of a *disabled* adapter into the base.
   This silently breaks the exact "memory on/off" switch that is the project's core demonstrable
   claim.
2. The `load_adapter_weights` key-set audit does not cover tensor shapes, so a crafted shareable
   `adapter.pt` with a correct key set partially mutates the model (10 of 12 LoRA tensors in the
   probe) before the error fires — directly contradicting the documented "refuse before loading a
   single tensor" P4 discipline on the one artifact class explicitly designed to be shared.

Three Warnings (smoke script's documented resume path does not exist; the artifact choke point
skips structural validation; load-bearing corruption guards are `assert`-stripped under `-O`) and
four Info items follow.

## Critical Issues

### CR-01: `enabled` toggle and `merged` state are mutually blind — silent wrong outputs on the memory-on/off switch

**File:** `src/personacore/lora/inject.py:94-123, 149-163, 172-201` and `src/personacore/lora/layer.py:38-56`
**Issue:** The forward gate is `if self.enabled and not self.merged` (layer.py:40), but the merge
and toggle APIs never check each other's state. Empirically confirmed (executed against the
reviewed code):

- `merge_lora(model)` on a model whose adapters are **disabled** folds the delta into
  `base.weight` anyway — output flips from base to base+delta while every `enabled` flag still
  says `False`. The adapter is silently turned ON.
- `set_adapter_enabled(model, False)` and the `adapter_disabled` context manager on a **merged**
  model are silent no-ops — the delta lives in `base.weight`, the gated branch never executes, so
  "disable" returns adapter logits, not base logits. The docstring claim "the model is
  bit-identical to the pre-injection base" (inject.py:97-98) is false in this reachable state.
- `merged_state_dict` likewise folds deltas of disabled modules, so its "reproduces the live
  logits" parity contract (pinned in `test_merged_state_dict_purity_and_parity`) breaks whenever
  any module is disabled.

The phase carefully guards every *other* illegal state combination (double merge, merge in train
mode, eject while merged) but left toggle×merge completely unguarded with a *silent* failure mode
— and the Phase-14 live demo drives exactly this switch ("Phase-14 live memory-on/off demo drives
THIS switch", inject.py:97). A demo that shows "memory off" while the adapter delta is still in
the weights falsifies the project's central privacy claim. No test covers any toggle×merge
combination.
**Fix:**
```python
# inject.py
def set_adapter_enabled(model: nn.Module, enabled: bool) -> None:
    for m in model.modules():
        if isinstance(m, LoRALinear):
            if m.merged:
                raise RuntimeError(
                    "set_adapter_enabled on a merged module — the delta is folded into "
                    "base.weight, so the flag would have no effect; unmerge_lora first."
                )
            m.enabled = enabled

def merge_lora(model: nn.Module) -> None:
    ...
    for m in model.modules():
        if isinstance(m, LoRALinear):
            if not m.enabled:
                raise RuntimeError(
                    "merge_lora on a disabled module would silently enable the adapter "
                    "— folding a disabled delta into base.weight changes live outputs."
                )
            m.merge()
```
Apply the same merged-state guard in `adapter_disabled` and the same enabled guard in
`merged_state_dict`, and add toggle×merge tests pinning the refusals.

### CR-02: `load_adapter_weights` audit covers keys but not shapes — crafted shareable artifact partially mutates the model before raising

**File:** `src/personacore/lora/inject.py:76-91`
**Issue:** The P4 audit compares only key *sets* (lines 82-90) before calling
`model.load_state_dict(artifact["adapter"], strict=False)`. PyTorch's `load_state_dict` copies
every shape-matching tensor and only raises the aggregated size-mismatch `RuntimeError` at the
end. Empirically confirmed: an artifact with the exactly-correct key set but two wrong-shaped
tensors left **10 of 12** of the victim model's LoRA tensors already mutated when the exception
surfaced. The docstring's contract — "Raises ValueError ... BEFORE any tensor is loaded ...
refusing to load" — is therefore bypassable through shapes, and the model survives the exception
in a corrupted half-applied state. `adapter.pt` is the artifact class explicitly designed to be
shared/swapped (checkpoint.py:168-170), i.e. the designated untrusted input: a Phase-14 persona
loader that catches per-file errors and continues would keep running on corrupted weights.
Secondary effect (also confirmed): a wrong-rank artifact (r=8 onto an r=4 injection — identical
key names) passes the audit and dies with an opaque multi-line torch `RuntimeError` instead of
the friendly `ValueError`.
**Fix:**
```python
expected = {k: v for k, v in model.state_dict().items() if "lora_" in k}
got = artifact["adapter"]
if expected.keys() != got.keys():
    ...  # existing symmetric-difference ValueError
bad_shapes = sorted(
    k for k in expected
    if got[k].shape != expected[k].shape or got[k].dtype != expected[k].dtype
)
if bad_shapes:
    raise ValueError(
        f"adapter tensor shape/dtype mismatch on {bad_shapes} — the artifact was trained "
        "at a different rank or base shape; refusing to load."
    )
model.load_state_dict(artifact["adapter"], strict=False)
```
Add a test: correct key set + one wrong-shaped tensor must raise `ValueError` with the model's
LoRA tensors bit-unchanged (extend `test_load_adapter_weights_raises_before_loading`).

## Warnings

### WR-01: Smoke script's documented kill-resume path does not exist — a killed smoke leaves nothing to resume

**File:** `scripts/train_adapter_smoke.py:16-19, 53, 118-134`
**Issue:** The module docstring resolves Open Q1 with "a killed smoke resumes by re-running this
script with `resume_from` semantics", and `SMOKE_CKPT` is labeled "resumable smoke state". The
code implements neither half: (a) `train()` is called without `resume_from`, so re-running always
restarts from step 0; (b) `checkpoint_interval` is not passed, so loop.py's in-loop Seam-4a save
never fires (`checkpoint_interval` defaults to `None`; the gate at loop.py:357-361 requires it) —
`SMOKE_CKPT` is written only at end-of-call, *after* the run completes. A killed run therefore
leaves no checkpoint at all, and a completed run's checkpoint is silently overwritten from
scratch on re-run. The documented resume story is dead.
**Fix:** Pass `checkpoint_interval=10` and
`resume_from=SMOKE_CKPT if SMOKE_CKPT.exists() else None` to the `train()` call (the docstring's
own "LORA_CFG rebuilds the module tree deterministically" rationale already justifies this), or
delete the resume note from the docstring and the "resumable" label on `SMOKE_CKPT`.

### WR-02: `load_adapter` — the single choke point for the shareable file — validates only `schema_version`

**File:** `src/personacore/checkpoint.py:204-219`
**Issue:** The function is documented as the "SINGLE choke point" every adapter consumer goes
through, for a file class designed to be received from elsewhere — yet after the schema gate it
performs no structural validation. Empirically confirmed: a schema-valid artifact missing
`base_fingerprint` raises bare `KeyError: 'base_fingerprint'` at line 211 when
`expected_fingerprint` is passed; one missing `adapter` or `lora_config` produces equally opaque
`KeyError`s downstream in `load_adapter_weights` / `LoRAConfig(**...)`. The code is also
internally inconsistent: `loaded.get("schema_version")` defends against a missing key on line
205, then `loaded["base_fingerprint"]` assumes presence on line 211.
**Fix:**
```python
missing = {"adapter", "lora_config", "base_fingerprint"} - loaded.keys()
if missing:
    raise ValueError(
        f"malformed adapter artifact {path}: missing keys {sorted(missing)} "
        "(expected an export_adapter persona file)."
    )
```
Insert after the schema gate; add a malformed-artifact test alongside
`test_schema_version_mismatch_raises`.

### WR-03: Weight-corruption guards are `assert` statements — stripped under `python -O`, turning loud refusals into silent corruption

**File:** `src/personacore/lora/layer.py:53, 65`; `src/personacore/lora/inject.py:140-143, 156-159, 186`; `scripts/train_adapter_smoke.py:97, 105, 135, 139-147`
**Issue:** Every guard that exists specifically to prevent silent numerical corruption is an
`assert`: double-merge (layer.py:53 — folds the delta twice), unmerge-never-merged
(layer.py:65), eject-while-merged (inject.py:140 — hands back adapter-contaminated base
weights), merge-in-train-mode (inject.py:156), and merged-`merged_state_dict` (inject.py:186).
Under `python -O`/`PYTHONOPTIMIZE` all of these vanish and the exact Pitfall-6 corruption they
exist to block happens silently. The smoke script compounds this: its docstring claims "every
assert is inline, so any failure exits non-zero" — under `-O` the canary, the wrap-count check,
and the census check all vanish and the script exits 0 having proven nothing. (`gpt.py` uses
`assert` for a shape guard, but a debug-shape check and a corruption guard are different risk
classes.)
**Fix:** In `layer.py` and `inject.py`, replace the state-guard `assert`s with
`raise RuntimeError(...)` (the merge-in-train-mode and eject-while-merged tests change from
`pytest.raises(AssertionError)` to `pytest.raises(RuntimeError)`). In the smoke script, either
convert the proof asserts to explicit `if ...: raise SystemExit(...)` checks or document that the
script must not run under `-O`.

## Info

### IN-01: No validation of `r`/`dropout` — `r=0` dies with a bare `ZeroDivisionError`

**File:** `src/personacore/lora/config.py:23-26`, `src/personacore/lora/layer.py:27-32`
**Issue:** `LoRAConfig` accepts any values; `LoRALinear.__init__` computes `alpha / r` first, so
`r=0` raises `ZeroDivisionError` and `r<0` raises an opaque torch shape error mid-injection;
`dropout` outside `[0, 1]` surfaces as an `nn.Dropout` error.
**Fix:** Add a `__post_init__` to `LoRAConfig` (or a guard in `LoRALinear.__init__`) raising
`ValueError` for `r < 1` and `not 0.0 <= dropout < 1.0`.

### IN-02: `export_adapter` returns live tensor aliases and never verifies its own load contract

**File:** `src/personacore/checkpoint.py:165-189`, `src/personacore/lora/inject.py:67-73`
**Issue:** `lora_state_dict` returns `state_dict()` references, so the dict `export_adapter`
returns aliases live model parameters — "return-what-shipped" drifts if the model trains after
export. Separately, nothing verifies the artifact meets the `weights_only=True` bar before
writing: a caller passing the `LoRAConfig` dataclass instead of `asdict(...)` writes an
`adapter.pt` that every consumer's `load_adapter` then rejects, with the failure surfacing far
from the bug.
**Fix:** Clone tensors into the returned/saved dict (they are ~1.3 MB), and/or round-trip the
written file once through `torch.load(path, weights_only=True)` inside `export_adapter` so a
contract-violating export fails at export time.

### IN-03: `eject_adapter` returns a "vanilla" model that is silently fully frozen

**File:** `src/personacore/lora/inject.py:125-146`
**Issue:** After `mark_only_lora_trainable`, every base param has `requires_grad=False`. Eject
restores the plain `nn.Linear` modules but never restores trainability, so the "vanilla GPT" it
hands back silently does not train — the exact P5 silent-failure class this phase hunts. Fine for
the demo-reset/inference path, but undocumented.
**Fix:** Document the frozen post-eject state in the docstring (or call
`model.requires_grad_(True)` / leave it to the caller explicitly).

### IN-04: Stale docstring — the adapter artifact seam landed in `checkpoint.py`, not in `lora/__all__`

**File:** `src/personacore/lora/__init__.py:6`, `tests/test_lora_toggle.py:140`
**Issue:** The package docstring says "later plans extend `__all__` with the adapter artifact
seam", but Plan 09-03 placed `export_adapter`/`load_adapter` in `personacore.checkpoint` (the
locked dependency direction) and `lora/__all__` was never extended. Similarly,
`test_eject_refuses_while_merged` still carries the stale comment "merge() itself lands in Task
2; the guard contract exists now" — merge shipped.
**Fix:** Update both comments to reflect where the artifact seam actually lives.

---

_Reviewed: 2026-06-11T22:39:05Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
