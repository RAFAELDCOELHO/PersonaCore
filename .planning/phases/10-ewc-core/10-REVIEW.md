---
phase: 10-ewc-core
reviewed: 2026-06-12T19:46:18Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - scripts/estimate_fisher_tinystories.py
  - src/personacore/checkpoint.py
  - src/personacore/continual/__init__.py
  - src/personacore/continual/ewc.py
  - src/personacore/continual/fisher.py
  - src/personacore/training/loop.py
  - tests/fixtures/golden_trajectory_v1.json
  - tests/test_ewc_penalty.py
  - tests/test_fisher_checkpoint.py
  - tests/test_fisher.py
  - tests/test_loop_penalty_fn.py
findings:
  critical: 0
  warning: 5
  info: 3
  total: 8
status: issues_found
---

# Phase 10: Code Review Report

**Reviewed:** 2026-06-12T19:46:18Z
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Summary

Reviewed the EWC core phase: per-example diagonal Fisher estimation (`continual/fisher.py`),
the Kirkpatrick quadratic penalty (`continual/ewc.py`), the additive `penalty_fn` +
`checkpoint_extra` splice into `training/loop.py`, Fisher persistence (`export_fisher` /
`load_fisher` in `checkpoint.py`), the real-weights estimation script, and four test files
plus the golden-trajectory fixture.

The key phase invariants were verified and hold:

- **Bit-identity when `penalty_fn` is omitted:** the only hot-path change is
  `(penalty_fn(model),) if penalty_fn is not None else ()` feeding `assemble_loss`, which is
  the v1.0 identity when empty. All 33 tests pass on this machine (Darwin/arm64 — the golden
  replay ran, not skipped).
- **Penalty joins before the `/accum` divide** (`loop.py:149-151`), so exactly one full
  penalty enters each optimizer step; pinned by
  `test_penalty_once_per_optimizer_step_under_accum`.
- **Tied wte/lm_head dedup:** `estimate_fisher` and the script's `theta_star` snapshot both
  iterate `named_parameters()` (the shared `nn.Parameter` appears once, under `wte.weight`);
  pinned in tests and by the script's proof [b], whose `data_ptr` cardinality check would
  also catch a `.data`-sharing mis-tie.
- **fp64 statistics on CPU only:** `fisher.py:132-146` moves tensors to CPU before any fp64
  numpy work; nothing fp64 touches the MPS device.
- **`load_fisher` is the single `weights_only=True` choke point** (schema gate → missing-key
  validation → hard fingerprint error), and `checkpoint.py` imports nothing from
  `continual/` — the locked dependency direction holds.
- The fixture's `captured_at_sha` (`01b8e41`) is the commit immediately preceding the loop
  splice (`b1fb37a`), so the golden capture provenance is genuinely pre-edit.

No Critical findings. Five Warnings (two confirmed by execution) and three Info items below.

## Warnings

### WR-01: `EWCPenalty.__call__` silently broadcasts on shape mismatch with the live model

**File:** `src/personacore/continual/ewc.py:58-71`
**Issue:** Construction validates fisher-vs-theta_star key sets and shapes against *each
other*, and `__call__` validates only key *presence* against the live model — never shapes.
A model with a same-named parameter of a different but broadcastable shape silently computes
a wrong penalty. Confirmed by execution: fisher/theta_star of shape `(1, 2)` against a model
param of shape `(2, 2)` returned `penalty = 2.0` with no error. This contradicts the module's
own contract ("Fail-loud validation at the choke points ... never a bare KeyError mid-run") —
and the non-broadcastable case fails as an anonymous mid-run `RuntimeError` instead of a
named `ValueError`. Low probability in the pinned best.pt flow (the fingerprint pins the
architecture), but Phase 12/13 will construct penalties from cache + freshly built models,
which is exactly where an architecture drift would enter.
**Fix:** Add a shape check in `__call__` next to the missing-key check:
```python
mismatched = [
    n for n, f in self.fisher.items()
    if n in params and params[n].shape != f.shape
]
if mismatched:
    raise ValueError(
        f"EWCPenalty: model parameter shape mismatch for keys {mismatched} "
        "(was the penalty built for a different architecture?)."
    )
```

### WR-02: `checkpoint_extra` can silently clobber reserved checkpoint fields (`rng`, `schema_version`)

**File:** `src/personacore/training/loop.py:373,394,419` (conduit); `src/personacore/checkpoint.py:61-80` (root cause)
**Issue:** `save_checkpoint` builds the dict as `{..., "rng": {...}, **extra}` with `**extra`
splatted last. Keys matching named parameters (`model`, `step`, `val_loss`, ...) raise a loud
`TypeError`, but `"rng"` and `"schema_version"` are not named parameters, so they pass through
`**extra` and silently overwrite the core fields. Confirmed by execution:
`checkpoint_extra={"rng": "CLOBBERED", "schema_version": 999}` saved without error, and the
corruption surfaced only at *resume* time as an opaque
`TypeError: string indices must be integers` deep inside `load_checkpoint`'s RNG restore —
precisely the "bare error deep in a downstream consumer" failure mode the codebase's
fail-loud discipline forbids. This was latent in `save_checkpoint(**extra)` before, but this
phase made it reachable from the public `train(checkpoint_extra=...)` API.
**Fix:** Guard the reserved keys at the conduit (or in `save_checkpoint`):
```python
_RESERVED = {"schema_version", "model", "optimizer", "scheduler", "scaler",
             "step", "val_loss", "model_config", "train_config", "git_sha", "rng"}
clash = _RESERVED & set(extra)
if clash:
    raise ValueError(f"save_checkpoint: extra keys {sorted(clash)} collide with "
                     "reserved checkpoint fields.")
```

### WR-03: `estimate_fisher` leaves the model in eval mode if a guard raises

**File:** `src/personacore/continual/fisher.py:98-99,125-139,167-168`
**Issue:** `model.eval()` is set at entry, but the restore (`if was_training: model.train()`)
runs only on the success path. Every fail-loud guard (`non-finite Fisher`, `degenerate raw
global mean`) and any exception inside the example loop exits with the model still in eval
mode, contradicting the docstring's contract ("The prior ``model.training`` flag is restored
on exit") and the `test_mode_restore` intent. Impact is nil at `dropout=0.0` but becomes a
silent behavior change (training without dropout) for any future config with dropout > 0
whose caller catches the `ValueError` and continues.
**Fix:** Wrap the body in `try/finally`:
```python
was_training = model.training
model.eval()
try:
    ...  # estimation + guards + stats
finally:
    if was_training:
        model.train()
return fisher, fisher_meta
```

### WR-04: Golden-replay skip gate omits torch/Python version — a torch bump turns kernel drift into a hard failure

**File:** `tests/test_loop_penalty_fn.py:54,86-95`; `tests/fixtures/golden_trajectory_v1.json:17-22`
**Issue:** The fixture's `meta.platform` records `python_version: "3.11.15"` and
`torch_version: "2.7.1"`, but the skip gate compares only `(system, machine)`. fp32 kernel
bits are not guaranteed stable across torch releases (the docstring itself names BLAS-backend
sensitivity); the project pins `torch==2.7.*`, so a routine 2.7.x patch bump on the capture
machine can change bits and make `test_golden_trajectory_bit_identity` fail hard — misread as
a loop regression instead of a stale fixture. The in-process identity tests would still pass,
deepening the confusion.
**Fix:** Extend the gate to the recorded versions, e.g.:
```python
_CAPTURE_PLATFORM = (..., _GOLDEN["meta"]["platform"]["torch_version"])
@pytest.mark.skipif(
    (platform.system(), platform.machine(), torch.__version__) != _CAPTURE_PLATFORM, ...)
```
(or skip with a "fixture captured on torch X, running Y — regenerate" reason).

### WR-05: `best_val_loss` resets to `inf` on resume — best.pt can regress after a kill+resume (pre-existing)

**File:** `src/personacore/training/loop.py:320,360-374`
**Issue:** Not introduced this phase, but it now sits under a phase-10 invariant: the Fisher
is anchored at `best.pt`. On `resume_from`, `best_val_loss` restarts at `float("inf")`, so
the first eval after a resume overwrites `best.pt` even when its val loss is *worse* than the
pre-kill best — the "ship the lowest-val checkpoint" contract (Seam 3 / D-08) breaks across
exactly the multi-session kill+resume runs the loop is designed for. A silently regressed
`best.pt` then becomes a worse Fisher/theta_star anchor for Phases 12/13 (the fingerprint
check cannot catch this — it would pin the regressed anchor faithfully).
**Fix:** Seed the running minimum from the checkpoint on resume:
```python
if resume_from is not None:
    ckpt = load_checkpoint(...)
    start_step = ckpt["step"]
    if ckpt.get("val_loss") is not None:
        best_val_loss = ckpt["val_loss"]
```
(or persist a dedicated `best_val_loss` field via the open-dict seam).

## Info

### IN-01: Shareable Fisher cache embeds the local absolute corpus path

**File:** `src/personacore/continual/fisher.py:158`; `scripts/estimate_fisher_tinystories.py:50,105-112`
**Issue:** `fisher_meta["bin_path"] = str(bin_path)` records the script's absolute path
(`/Users/<username>/PersonaCore/data/train.bin`) inside `fisher_tinystories.pt`, an artifact
explicitly designed to be shareable. Leaking the local username/filesystem layout is a wart
for a project whose thesis is privacy-by-design.
**Fix:** Store the path relative to the repo root (e.g.,
`os.path.relpath(bin_path, _REPO_ROOT)` at the call site, or record only the basename plus a
content fingerprint).

### IN-02: Logged/returned `train_loss` silently excludes the penalty term

**File:** `src/personacore/training/loop.py:153,159,329-346`
**Issue:** `_optimizer_step` accumulates `summed += float(base_loss.item())` — the value
returned, logged to CSV, and reported as the step's "training loss" is the base CE only, even
when a penalty actively shapes the gradients. Excluding it is reasonable (keeps `train_loss`
comparable to `val_loss` and preserves the golden CSV semantics) but is undocumented: the
docstring says only "Returns the (unscaled, accumulation-corrected) training loss", and Phase
12's lambda sweep gets no penalty-magnitude observability from the curve.
**Fix:** Document the exclusion explicitly in `_optimizer_step`/`train` docstrings; consider
logging the penalty as an additional CSV column in Phase 12 (a new column appended after the
existing ones keeps old curves parseable).

### IN-03: `EWCPenalty` accepts any `lam` without validation

**File:** `src/personacore/continual/ewc.py:35-56`
**Issue:** Construction validates keys and shapes exhaustively but never `lam`. A negative
lambda inverts the penalty into a drift *reward* with no warning — a plausible sign-error
slip in Phase 12's sweep code. Given the class's fail-loud posture, this is an easy gap.
**Fix:** `if not lam >= 0: raise ValueError(f"EWCPenalty: lam must be >= 0, got {lam!r}")`
(the `not >=` form also rejects NaN).

---

_Reviewed: 2026-06-12T19:46:18Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
