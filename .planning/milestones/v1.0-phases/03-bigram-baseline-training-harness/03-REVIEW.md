---
phase: 03-bigram-baseline-training-harness
reviewed: 2026-06-04T00:00:00Z
depth: standard
files_reviewed: 15
files_reviewed_list:
  - scripts/train_bigram.py
  - src/personacore/model/__init__.py
  - src/personacore/model/bigram.py
  - src/personacore/training/__init__.py
  - src/personacore/training/data.py
  - src/personacore/training/loop.py
  - src/personacore/training/loss.py
  - src/personacore/training/schedule.py
  - tests/test_assemble_loss.py
  - tests/test_bigram_model.py
  - tests/test_data_split.py
  - tests/test_lr_schedule.py
  - tests/test_overfit_batch.py
  - tests/test_resume_curve.py
  - tests/test_train_loop.py
findings:
  critical: 1
  warning: 6
  info: 3
  total: 10
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-06-04
**Depth:** standard
**Files Reviewed:** 15
**Status:** issues_found

## Summary

Reviewed the from-scratch bigram baseline + training harness (model, data split, loop,
LR schedule, loss seam, entry script, and 7 test files). The harness is well-structured and
the CPU-only resume/curve reproducibility design is genuinely careful (RNG snapshot/restore
around `estimate_loss`, step-derived `tokens`/`wall_clock`, header-once CSV). The grad-accum
equivalence and AMP step ordering on the synthetic path are correct.

However, the review surfaced one BLOCKER that only manifests on the hardware the project
actually targets (the P100 fp16 run in Phase 5): the `GradScaler` state is never checkpointed
or restored, so a killed+resumed fp16 run does NOT continue the same trajectory — directly
contradicting the TRAIN-04 "resume is bit-identical" contract and CLAUDE.md's explicit
`{model, optimizer, scaler, step, rng_state, config}` checkpoint prescription. Because the
entire test suite runs CPU-only (scaler disabled → no-op), green tests give false confidence
here. Several WARNINGs concern edge-case crashes in the data/eval bound math and the
scheduler advancing on optimizer-skipped steps.

## Critical Issues

### CR-01: GradScaler state is never saved or restored — fp16 resume is not reproducible

**File:** `src/personacore/training/loop.py:194-195, 281-292`; `src/personacore/checkpoint.py:51-70`
**Issue:**
The loop builds a `GradScaler` (`loop.py:195`) and uses its dynamically-adapted scale factor on
every step. On resume (`load_checkpoint`, `loop.py:236`) the model, optimizer, scheduler, and RNG
state are restored, but the scaler is rebuilt fresh from defaults — its `_scale` (default 65536)
and growth-tracker counter are lost. `save_checkpoint` (`checkpoint.py:51-70`) does not serialize
`scaler.state_dict()` at all.

On CPU the scaler is `enabled=False` (a no-op), so every test passes and the resume-equality
assertions in `test_resume_curve.py` hold. But on the P100 fp16 path (the real Phase-5 pretrain),
an uninterrupted run carries an evolved scale factor across the kill point, whereas the resumed run
restarts from the default scale. The first post-resume steps will scale gradients differently —
risking inf/over-/under-flow, a skipped `scaler.step`, and a measurably different trajectory. This
breaks the TRAIN-04 "killed+resumed run is bit-identical (within 1e-6) to an uninterrupted one"
contract on the only hardware where AMP is active, and violates CLAUDE.md's checkpoint spec which
explicitly lists `scaler` in the saved state ("Save `{model, optimizer, scaler, step, rng_state,
config}`").

**Fix:**
Thread the scaler through save/restore. In `checkpoint.py`:
```python
def save_checkpoint(path, *, model, optimizer, scheduler, step, model_config,
                    train_config, git_sha, scaler=None, val_loss=None, **extra):
    ckpt = {
        ...,
        "scaler": scaler.state_dict() if scaler is not None else None,
        ...,
    }

def load_checkpoint(path, *, model, optimizer=None, scheduler=None, scaler=None,
                    map_location="cpu"):
    ...
    if scaler is not None and ckpt.get("scaler") is not None:
        scaler.load_state_dict(ckpt["scaler"])
```
In `loop.py`, pass `scaler=scaler` to both `load_checkpoint(...)` (line 236) and
`save_checkpoint(...)` (line 282). Add a GPU-gated (or mocked-scaler) test asserting the restored
scale factor matches an uninterrupted run so this can't regress silently behind the CPU no-op.

## Warnings

### WR-01: `estimate_loss` crashes on a tiny val split (`len(val_ids) <= 2`)

**File:** `src/personacore/training/loop.py:73`; `src/personacore/training/data.py:65`
**Issue:**
`eff_block = min(block_size, max(1, len(val_ids) - 2))`. The `max(1, ...)` floor is meant to keep
the window positive, but it breaks the downstream bound. `get_batch` computes
`np.random.randint(0, len(arr) - block_size - 1)`. With `len(val_ids) == 2`, `eff_block == 1`, so
the bound is `2 - 1 - 1 == 0` and numpy raises `ValueError: low >= high`. With `len(val_ids) == 3`,
the bound is `1` (ok by luck). The fixture's val doc is currently large enough to avoid this, but a
short final document (or a smaller fixture) will crash the whole run inside the eval, not at a clear
validation point.

**Fix:** Make the bound the single source of truth and guard it. Either skip eval when the val
split is too short to form even one window, or compute `eff_block` so the bound is always `>= 1`:
```python
if len(val_ids) < 3:
    return float("nan")  # or skip eval / log a sentinel
eff_block = min(block_size, len(val_ids) - 2)  # bound = len - eff_block - 1 >= 1
```

### WR-02: `get_batch` start bound is off-by-one — the last valid window is never sampled

**File:** `src/personacore/training/data.py:65`
**Issue:**
The maximum valid start index `s` must satisfy `s + 1 + block_size <= len(arr)`, i.e.
`s <= len(arr) - block_size - 1`. `np.random.randint(low, high)` treats `high` as **exclusive**, so
passing `high = len(arr) - block_size - 1` excludes that maximum valid start. The final window of
the array can therefore never be drawn. This is not a crash and not a leakage issue, but it is a
genuine off-by-one that silently drops one position of training coverage (and on a tiny fixture
where `len(arr) - block_size - 1 == 1`, it restricts sampling to a single start index, hurting the
overfit/resume gates' representativeness).

**Fix:**
```python
ix = np.random.randint(0, len(arr) - block_size, size=batch_size)
```
This includes `len(arr) - block_size - 1` as a valid start; `y = arr[i+1 : i+1+block_size]` then ends
exactly at `len(arr) - 1`, still in-bounds.

### WR-03: `scheduler.step()` advances even when `scaler.step()` skips the optimizer

**File:** `src/personacore/training/loop.py:123-125`
**Issue:**
On the fp16 path, when gradients are non-finite `scaler.step(optimizer)` skips the actual
`optimizer.step()`, but `scheduler.step()` (line 125) is then called unconditionally. The LR
schedule advances on a step where no weight update happened, desynchronizing the LR curve from the
true update count and emitting the standard PyTorch warning ("Detected call of `lr_scheduler.step()`
before `optimizer.step()`"). On CPU this never triggers (scaler disabled), so tests stay green and
hide it. It also subtly breaks the resume-curve contract on GPU: a skipped step still advances
`last_epoch`, which is what gets checkpointed.

**Fix:** Only advance the scheduler when the optimizer actually stepped:
```python
prev_scale = scaler.get_scale()
scaler.step(optimizer)
scaler.update()
if scaler.get_scale() >= prev_scale:  # step was not skipped (scale not reduced)
    scheduler.step()
```
(Or track `optimizer._step_count` before/after.) Document the chosen heuristic.

### WR-04: `clip_grad_norm_` runs on possibly-inf gradients before the skip decision

**File:** `src/personacore/training/loop.py:121-123`
**Issue:**
`unscale_` → `clip_grad_norm_` → `scaler.step`. When grads contain inf/nan after `unscale_`,
`clip_grad_norm_` computes an inf total-norm and (depending on torch version / `error_if_nonfinite`)
either silently no-ops the rescale or raises. The code does not pass `error_if_nonfinite=False`, so
behavior is version-dependent and the AMP "skip this step on overflow" intent relies entirely on
`scaler.step` catching it afterward. This is fragile on the actual fp16 path.

**Fix:** Be explicit about the non-finite policy so overflow handling is deterministic across torch
versions:
```python
torch.nn.utils.clip_grad_norm_(model.parameters(), train_cfg.grad_clip,
                               error_if_nonfinite=False)
```
and rely on `scaler.step`/`update` to drop the overflowed step (paired with WR-03's guard).

### WR-05: `load_split` integrity checks use bare `assert` (stripped under `python -O`)

**File:** `src/personacore/training/data.py:50-51`
**Issue:**
The "fixture must contain >= 2 documents" and `1 <= val_docs < len(docs)` invariants are enforced
with `assert`. Under `python -O` / `PYTHONOPTIMIZE`, asserts are removed, so a malformed fixture or
a bad `val_docs` would silently produce an empty train or val split (e.g. `docs[:-val_docs]` with
`val_docs >= len(docs)` yields `[]` → a zero-length `train_ids` → a later opaque `randint` crash in
`get_batch`). These are real input-validation guards, not internal sanity checks.

**Fix:** Raise explicit errors:
```python
if len(docs) < 2:
    raise ValueError("fixture must contain >= 2 documents (D-06)")
if not (1 <= val_docs < len(docs)):
    raise ValueError(f"val_docs must be in [1, {len(docs)-1}], got {val_docs}")
```

### WR-06: `estimate_loss` silently substitutes train_loss as val_loss when val is absent

**File:** `src/personacore/training/loop.py:258-263`
**Issue:**
When `val_ids is None` (the `fixed_batch` / synthetic paths) the loop logs `val_loss = train_loss`.
The CSV column then contains train loss masquerading as validation loss with no marker. Anyone
reading the curve in `demo.ipynb` (Phase 8) would interpret a perfectly-tracking val curve as
strong generalization when it is actually a copy of train. This is a correctness-of-artifact issue,
not just style.

**Fix:** Log an explicit sentinel (e.g. empty string or `nan`) when no val split exists, and have
the plotting code treat it as "no val measured":
```python
val_loss = estimate_loss(...) if val_ids is not None else ""
```

## Info

### IN-01: `sample()` divides by `temperature` with no zero/negative guard

**File:** `src/personacore/training/loop.py:94`
**Issue:** `logits = logits[:, -1, :] / temperature`. `temperature=0` produces inf/nan →
`torch.multinomial` raises; a negative temperature inverts the distribution silently. The script
hardcodes `1.0`, but `sample` is a re-exported public function (`training/__init__.py`).
**Fix:** Clamp/validate (`temperature = max(temperature, 1e-6)`) or treat `temperature <= 0` as
greedy `argmax`, matching the Phase-6 generate contract.

### IN-02: `summed += float(base_loss.item())` forces a host sync every micro-batch

**File:** `src/personacore/training/loop.py:120`
**Issue:** Calling `.item()` inside the micro-batch loop synchronizes the GPU each iteration purely
to compute the returned/logged mean loss. Correct, but defeats some of the accumulation benefit on
GPU. (Flagged as Info since performance is out of v1 scope; noted only because it is on the hot
path.) **Fix:** Accumulate a detached tensor and `.item()` once after the loop.

### IN-03: `eos_id` default duplicated across modules instead of sourced from config

**File:** `src/personacore/training/data.py:23` (`eos_id=8184`), `loop.py:136` (`eos_id=8184`)
**Issue:** The magic `8184` is hardcoded as a default in two signatures while `ModelConfig.eos_id`
already holds the single source of truth (D-03a). If the locked EOS id ever moved, these defaults
would silently disagree with config. **Fix:** Default to `None` and fall back to
`model_cfg.eos_id`, or import the constant, so there is one authority for the value.

---

_Reviewed: 2026-06-04_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
