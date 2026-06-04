---
phase: 03-bigram-baseline-training-harness
verified: 2026-06-04T00:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 4/5
  gaps_closed:
    - "GradScaler scale-factor/growth-tracker state now serialized into the open-dict checkpoint and restored on resume (CR-01 / TRAIN-04 fp16 path), with a CPU-observable regression test."
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "On a CUDA GPU (or P100), run an uninterrupted fp16 training run vs a killed+resumed fp16 run and compare post-resume loss/scale-factor trajectories."
    expected: "Trajectories match within 1e-6 — the GradScaler scale factor now resumes from the saved evolved value rather than the default. (Now verified on CPU via a stateful fake scaler; this GPU check is final confirmation on real fp16 hardware.)"
    why_human: "The CPU suite proves save+restore of scaler state via an injected stateful fake, but the real GradScaler is a no-op on CPU. Observing the actual fp16 numerical trajectory still requires CUDA hardware. This is now a confirmatory check, not a blocking gap."
---

# Phase 3: Bigram Baseline + Training Harness Verification Report

**Phase Goal:** A working thin end-to-end slice — tokenize → train → sample → see output — proven on a trivial bigram model, so the training loop, checkpoint/resume, AMP toggle, eval, and the EWC `assemble_loss` seam are all validated before the real transformer math is risked.
**Verified:** 2026-06-04
**Status:** passed
**Re-verification:** Yes — after gap closure (CR-01: GradScaler state checkpointing)

## Re-Verification Summary

The initial verification (2026-06-04) returned **gaps_found (4/5)** with a single gap: the
`GradScaler` scale-factor/growth-tracker state (TRAIN-04, code-review finding CR-01) was never
serialized into the checkpoint nor restored on resume, so the fp16/P100 resume path would diverge
from an uninterrupted run while the CPU-only suite stayed green (the real scaler is a no-op on CPU).

A fix has since been committed. Re-examining the actual code confirms the gap is **closed**:

- **`src/personacore/checkpoint.py`** — `save_checkpoint` now takes `scaler=None` (line 42) and
  serializes `scaler.state_dict() if scaler is not None else None` under the `"scaler"` key
  (line 62). `load_checkpoint` takes `scaler=None` (line 81) and restores via
  `scaler.load_state_dict(ckpt["scaler"])` gated on `ckpt.get("scaler") is not None` (lines 101-102),
  so pre-fix (scaler-less) checkpoints resume cleanly — backward compatible.
- **`src/personacore/training/loop.py`** — `train()` threads `scaler=scaler` through BOTH
  `load_checkpoint` (line 237) and `save_checkpoint` (line 289).
- **`tests/test_resume_curve.py`** — adds `_StatefulFakeScaler` (an injectable GradScaler-shaped
  stand-in whose `_scale` evolves each step and exposes `state_dict`/`load_state_dict`), plus
  `test_scaler_state_checkpointed_and_restored` (proves the scaler state is serialized into the
  ckpt blob AND restored to the evolved value across a kill+resume — on CPU) and
  `test_resume_from_pre_scaler_checkpoint_is_backward_compatible` (a legacy scaler-less checkpoint
  resumes without crashing and restores nothing).

**Adversarial regression check (verifier-run):** Simulating the pre-fix behavior (forcing
`save`/`load` to drop the scaler) makes the new test's assertions fail —
`blob["scaler"]` is `None` (save assertion fails) and `s2.restored_from` is `None` (restore
assertion fails). With the actual fix in place both pass. The new test is therefore a genuine
regression guard against CR-01, not a vacuous one.

**Full suite (venv 3.11):** `source .venv/bin/activate && python -m pytest -q` → **77 passed, 1 skipped**
(was 75 passed / 1 skipped — the +2 are the two new scaler tests). `ruff check .` → **All checks passed!**

All five success criteria are now verified in the codebase.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A from-scratch bigram LM trains end-to-end through the harness and produces sampled output, exercising the model→loss→logits contract | ✓ VERIFIED | `BigramLanguageModel` (bigram.py:24-39) is `nn.Embedding(V,V)` with the LOCKED `forward(idx, targets=None) -> (logits, loss)`; internal `F.cross_entropy` on the `(B*T,V)` flatten. `python scripts/train_bigram.py` trains 20 steps and prints decoded sampled text. `test_bigram_model.py` GREEN. |
| 2 | The overfit-a-single-batch test drives loss toward zero, proving harness correctness independent of attention | ✓ VERIFIED | `test_overfits_single_fixed_batch` PASSED; asserts `final_loss < ln(8192) - 2.0` on one fixed batch reused every step under `seed_everything`. Loop's `fixed_batch` mode (loop.py:205-211). |
| 3 | The loop runs AdamW + warmup/cosine LR + grad clip + configurable grad accumulation, fp32 default + optional fp16-AMP+GradScaler (unscale-before-clip) as a memory measure | ✓ VERIFIED | `_optimizer_step` (loop.py:108-126): zero_grad → per-micro `scaler.scale(loss).backward()` → `scaler.unscale_` → `clip_grad_norm_` → `scaler.step` → `scaler.update` → `scheduler.step` once per optimizer step. `GradScaler(enabled=runtime.amp)`, fp32 default. `test_amp_ordering_unscale_clip_step_update` + `test_grad_accum_equivalent_to_big_batch` PASSED. |
| 4 | A doc-level train/val split with periodic eval()+no_grad() validation loss, no leakage, and CSV logging reproduces the loss curve across a restart (TRAIN-04) | ✓ VERIFIED | No-leakage doc split (data.py:23-55) ✓; `estimate_loss` under `@torch.no_grad()` + eval/train toggle + RNG snapshot/restore (loop.py:60-81) ✓; CSV row-for-row reproducibility across restart (`test_csv_curve_survives_restart` PASSED) ✓; resume trajectory equality within 1e-6 (`test_resume_identical_trajectory` PASSED) ✓. **GradScaler state now checkpointed/restored (CR-01 CLOSED):** scaler serialized under `"scaler"` key and restored on resume (checkpoint.py:42,62,81,101-102; loop.py:237,289), proven on CPU by `test_scaler_state_checkpointed_and_restored` + backward-compat test. |
| 5 | Loss assembled via `assemble_loss(..., extra_penalties=())` with empty list + checkpoints are open dicts (M2 EWC seam, plumbing only) | ✓ VERIFIED | `assemble_loss(base, ())` identity (loss.py:17-28); loop always passes `()` (loop.py:117). `test_assemble_loss.py` GREEN. Checkpoint is an open dict with `**extra` (checkpoint.py:57-76), embedded config + RNG + git_sha + now scaler. |

**Score:** 5/5 truths verified.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/personacore/model/bigram.py` | BigramLanguageModel `nn.Embedding(V,V)`, locked forward | ✓ VERIFIED | class present, CE flatten, wired into loop + script. |
| `src/personacore/model/__init__.py` | barrel exporting BigramLanguageModel | ✓ VERIFIED | `from .bigram import BigramLanguageModel`. |
| `src/personacore/training/loss.py` | `assemble_loss(base, extra_penalties=())` | ✓ VERIFIED | identity-on-empty + additive; no callbacks. |
| `src/personacore/training/data.py` | load_split (no leakage) + get_batch | ✓ VERIFIED | doc-split + nanoGPT sampler; frozen tokenizer loaded, never retrained. |
| `src/personacore/training/schedule.py` | build_lr_lambda + build_scheduler → LambdaLR | ✓ VERIFIED | hand-rolled warmup+cosine wrapped in LambdaLR; state_dict round-trips. |
| `src/personacore/training/loop.py` | train()/estimate_loss()/sample() | ✓ VERIFIED | 297 lines; all orchestration present and wired; **scaler now threaded through resume save/load** (loop.py:237,289). |
| `src/personacore/checkpoint.py` | open-dict resumable checkpoint w/ full state | ✓ VERIFIED | open dict with `**extra`; now includes serialized `scaler` state, backward compatible via `ckpt.get("scaler")`. |
| `src/personacore/training/__init__.py` | public training barrel | ✓ VERIFIED | exports train/assemble_loss/build_scheduler/get_batch/load_split/sample/estimate_loss. |
| `scripts/train_bigram.py` | thin no-argparse entry, MVP see-output | ✓ VERIFIED | runs end-to-end, prints decoded text; outputs gitignored. |
| `tests/fixtures/bigram_corpus.txt` | ≥2 eos-separated docs | ✓ VERIFIED | encodes through frozen tokenizer with 8184 at ≥2 boundaries. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| loop.py | RuntimeConfig.autocast() + GradScaler | `runtime.autocast()` + `GradScaler(enabled=runtime.amp)` | ✓ WIRED | loop.py:115, 195. No `torch.cuda.*` in the loop. |
| loop.py | checkpoint save/load | `save_checkpoint` / `load_checkpoint` | ✓ WIRED | model/optimizer/scheduler/step/RNG **and scaler** all threaded (loop.py:236-238, 283-295). CR-01 closed. |
| loop.py | scaler.unscale_ before clip | mandatory AMP ordering | ✓ WIRED | unscale_ (loop.py:121) precedes clip (loop.py:122). |
| checkpoint.py | scaler state round-trip | `scaler.state_dict()` / `scaler.load_state_dict()` | ✓ WIRED | save (checkpoint.py:62), restore gated on `ckpt.get("scaler")` (checkpoint.py:101-102). Proven CPU-observable by `_StatefulFakeScaler` test. |
| bigram.py | F.cross_entropy | `(B*T,V)` vs `(B*T)` flatten | ✓ WIRED | bigram.py:38. |
| data.py | artifacts/tokenizer.json | `from_json` + `encode(allowed_special='all')` | ✓ WIRED | data.py:32,35. Frozen, never retrained. |
| schedule.py | scheduler.state_dict() contract | LambdaLR object | ✓ WIRED | schedule.py:48-51. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Resume + scaler-state checkpoint tests | `pytest tests/test_resume_curve.py -v` | 4 passed | ✓ PASS |
| Pre-fix regression guard (verifier adversarial run) | Monkeypatch save/load to drop scaler, replay test | `blob['scaler']=None`, `restored_from=None` → both new assertions WOULD fail pre-fix | ✓ PASS (genuine guard) |
| Full suite (venv 3.11) | `source .venv/bin/activate && python -m pytest -q` | 77 passed, 1 skipped | ✓ PASS |
| Lint | `ruff check .` | All checks passed! | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| MODEL-01 | 03-01, 03-02 | From-scratch bigram baseline | ✓ SATISFIED | bigram.py + test_bigram_model.py GREEN |
| TRAIN-01 | 03-01/03/04 | AdamW + warmup/cosine + clip + configurable accum | ✓ SATISFIED | loop.py + schedule.py; AMP-ordering/grad-accum tests GREEN |
| TRAIN-02 | 03-01/04 | fp32 default + optional fp16 AMP+GradScaler, unscale-before-clip | ✓ SATISFIED | correct ordering verified; **scaler state now resumable** |
| TRAIN-03 | 03-01/03 | Train/val split, periodic val loss, no leakage | ✓ SATISFIED | data.py doc-split + test_data_split.py GREEN |
| TRAIN-04 | 03-01/04 | Offline CSV logging survives restarts; curves reproducible | ✓ SATISFIED | fp32 reproducibility verified; **fp16 scaler state checkpointed/restored (CR-01 closed)** — CPU-observable test + backward-compat test GREEN |
| TRAIN-05 | 03-01/04 | Overfit-a-single-batch test passes | ✓ SATISFIED | test_overfits_single_fixed_batch PASSED |
| TRAIN-06 | 03-01/02/04 | assemble_loss seam + open-dict checkpoints | ✓ SATISFIED | loss.py + checkpoint.py open dict; tests GREEN |

All 7 declared requirement IDs satisfied. No orphaned requirements for Phase 3.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| src/personacore/training/data.py | 50-51 | input validation via bare `assert` (stripped under `python -O`) | ℹ️ Info (WR-05) | malformed fixture could silently produce empty split |
| src/personacore/training/data.py | 65 | `randint(0, len(arr)-block_size-1)` off-by-one (last window never sampled) | ℹ️ Info (WR-02) | drops one position of coverage; not a crash/leakage |
| src/personacore/training/loop.py | 73 | `estimate_loss` bound math on tiny val split | ℹ️ Info (WR-01) | current fixture large enough; mitigated by `eff_block` clamp |
| src/personacore/training/loop.py | 123-125 | `scheduler.step()` advances even when `scaler.step()` skips | ℹ️ Info (WR-03) | GPU-only; desyncs LR curve on overflow; CPU no-op hides it |

The prior ⚠️ Blocker anti-pattern (checkpoint.py: GradScaler state not in checkpoint contract) is
**RESOLVED** — the scaler is now a named, serialized field in the checkpoint, matching CLAUDE.md's
`{model, optimizer, scaler, step, rng_state, config}` prescription. No `TBD`/`FIXME`/`XXX` debt
markers in any phase-modified file.

### Human Verification (confirmatory, non-blocking)

#### 1. fp16 resume trajectory on CUDA

**Test:** On a CUDA GPU (or the target P100), run an uninterrupted fp16 training run vs a
killed+resumed fp16 run and compare post-resume loss and GradScaler scale-factor trajectories.
**Expected:** Trajectories match within 1e-6 — the scale factor now resumes from the saved evolved
value rather than the default 65536.
**Why human:** The CPU suite proves the scaler state is serialized and restored (via an injected
stateful fake scaler — the real GradScaler is a no-op on CPU), but observing the actual fp16
numerical trajectory needs CUDA hardware. This is now a *confirmation* of an already-closed gap,
not a blocking verification.

### Gaps Summary

No gaps remain. The single prior gap (CR-01 / TRAIN-04: GradScaler state not checkpointed) is
closed: the scaler state is now serialized into the open-dict checkpoint and restored on resume,
backward compatible with pre-fix checkpoints, and guarded by a CPU-observable regression test that
the verifier independently confirmed fails under simulated pre-fix behavior. The full 3.11-venv
suite is 77 passed / 1 skipped and `ruff check .` is clean. All five success criteria are verified
in the codebase. The remaining human item is a confirmatory GPU check, not a blocker.

---

_Verified: 2026-06-04 (re-verification after gap closure)_
_Verifier: Claude (gsd-verifier)_
