---
phase: 03-bigram-baseline-training-harness
verified: 2026-06-04T00:00:00Z
status: gaps_found
score: 4/5 must-haves verified
overrides_applied: 0
gaps:
  - truth: "A document-level train/val split with periodic eval()+no_grad() validation loss runs with no leakage, and CSV+matplotlib logging reproduces the loss curve across a restart (TRAIN-04)"
    status: partial
    reason: >
      Verified on the fp32/CPU path (test_resume_identical_trajectory and
      test_csv_curve_survives_restart both pass, 1e-6 trajectory + row-for-row CSV). BUT the
      GradScaler state (_scale + growth-tracker) is never serialized into the checkpoint nor
      restored on resume, so on the fp16/P100 path — the only hardware where AMP is active —
      a killed+resumed run restarts the scale factor from the default (65536) instead of the
      evolved value. The first post-resume steps scale gradients differently, risking a skipped
      scaler.step and a measurably different trajectory. This breaks "reproduces the loss curve
      across a restart" on the AMP path and violates CLAUDE.md's explicit
      {model, optimizer, scaler, step, rng_state, config} checkpoint prescription (scaler is
      named and missing). The entire CPU-only test suite cannot catch this because RuntimeConfig
      auto-disables AMP on CPU (amp=False), making the scaler a no-op — green tests give false
      confidence here. This is the de-risking that Phase 3 exists to perform before the
      expensive Phase 5 P100 run, so it is not a deferrable concern.
    artifacts:
      - path: "src/personacore/checkpoint.py"
        issue: "save_checkpoint (lines 32-70) has no scaler parameter and never serializes scaler.state_dict(); load_checkpoint (lines 73-97) has no scaler parameter and never restores it."
      - path: "src/personacore/training/loop.py"
        issue: "train() builds/uses a GradScaler (line 195) but does not pass scaler= to load_checkpoint (line 236) or save_checkpoint (lines 282-292), so the scale factor is lost across a kill+resume on the fp16 path."
    missing:
      - "Add scaler=None param to save_checkpoint; serialize scaler.state_dict() (or None) into the open dict."
      - "Add scaler=None param to load_checkpoint; call scaler.load_state_dict(ckpt['scaler']) when present."
      - "Thread scaler=scaler through both load_checkpoint and save_checkpoint calls in loop.py."
      - "Add a GPU-gated (or mocked-scaler) test asserting the restored scale factor matches an uninterrupted run, so this can't regress behind the CPU no-op."
human_verification:
  - test: "On a CUDA GPU (or P100), run an uninterrupted fp16 training run vs a killed+resumed fp16 run and compare post-resume loss/scale-factor trajectories."
    expected: "Trajectories should match within 1e-6. With the current code they will diverge because the GradScaler scale factor restarts from default on resume."
    why_human: "The CPU test suite cannot exercise this — AMP is auto-disabled on CPU (scaler is a no-op). Requires actual CUDA hardware to observe the fp16 resume divergence and to validate the fix."
---

# Phase 3: Bigram Baseline + Training Harness Verification Report

**Phase Goal:** A working thin end-to-end slice — tokenize → train → sample → see output — proven on a trivial bigram model, so the training loop, checkpoint/resume, AMP toggle, eval, and the EWC `assemble_loss` seam are all validated before the real transformer math is risked.
**Verified:** 2026-06-04
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A from-scratch bigram LM trains end-to-end through the harness and produces sampled output, exercising the model→loss→logits contract | ✓ VERIFIED | `BigramLanguageModel` (bigram.py:24-39) is `nn.Embedding(V,V)` with the LOCKED `forward(idx, targets=None) -> (logits, loss)`; internal `F.cross_entropy` on the `(B*T,V)` flatten. `python scripts/train_bigram.py` trains 20 steps and prints decoded sampled text ("sampled 41 ids (2 decodable)"). `test_bigram_model.py` GREEN. |
| 2 | The overfit-a-single-batch test drives loss toward zero, proving harness correctness independent of attention | ✓ VERIFIED | `test_overfits_single_fixed_batch` PASSED; asserts `final_loss < ln(8192) - 2.0` on one fixed batch reused every step under `seed_everything`. Loop's `fixed_batch` mode (loop.py:205-211) reuses one batch. |
| 3 | The loop runs AdamW + warmup/cosine LR + grad clip + configurable grad accumulation, fp32 default + optional fp16-AMP+GradScaler (unscale-before-clip) as a memory measure | ✓ VERIFIED | `_optimizer_step` (loop.py:101-126): zero_grad → per-micro `scaler.scale(loss).backward()` → `scaler.unscale_` → `clip_grad_norm_` → `scaler.step` → `scaler.update` → `scheduler.step` once per optimizer step. AdamW + `build_scheduler` (loop.py:190-193). `GradScaler(enabled=runtime.amp)`, fp32 default (RuntimeConfig amp=False on CPU). `test_amp_ordering_unscale_clip_step_update` + `test_grad_accum_equivalent_to_big_batch` PASSED. |
| 4 | A doc-level train/val split with periodic eval()+no_grad() validation loss, no leakage, and CSV logging reproduces the loss curve across a restart | ✗ PARTIAL | No-leakage doc split (data.py:23-55, disjoint train/val on eos boundaries) ✓; `estimate_loss` under `@torch.no_grad()` + eval/train toggle + RNG snapshot/restore (loop.py:60-81) ✓; CSV reproducibility on CPU/fp32 path ✓ (`test_csv_curve_survives_restart` PASSED). **BUT GradScaler state is never checkpointed/restored — fp16 resume diverges (CR-01).** See Gaps. |
| 5 | Loss assembled via `assemble_loss(..., extra_penalties=())` with empty list + checkpoints are open dicts (M2 EWC seam, plumbing only) | ✓ VERIFIED | `assemble_loss(base, ())` identity (loss.py:17-28); loop always passes `()` (loop.py:117). `test_assemble_loss.py` GREEN. Checkpoint is an open dict with `**extra` (checkpoint.py:51-69), embedded config + RNG + git_sha. |

**Score:** 4/5 truths verified (truth 4 partial — fp32 path verified, fp16 resume path broken)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/personacore/model/bigram.py` | BigramLanguageModel `nn.Embedding(V,V)`, locked forward | ✓ VERIFIED | 39 lines, class present, CE flatten, wired into loop + script. |
| `src/personacore/model/__init__.py` | barrel exporting BigramLanguageModel | ✓ VERIFIED | `from .bigram import BigramLanguageModel`. |
| `src/personacore/training/loss.py` | `assemble_loss(base, extra_penalties=())` | ✓ VERIFIED | identity-on-empty + additive; no callbacks. |
| `src/personacore/training/data.py` | load_split (no leakage) + get_batch | ✓ VERIFIED | doc-split + nanoGPT sampler; frozen tokenizer loaded, never retrained. (WR-02/WR-05 are warnings.) |
| `src/personacore/training/schedule.py` | build_lr_lambda + build_scheduler → LambdaLR | ✓ VERIFIED | hand-rolled warmup+cosine wrapped in LambdaLR; state_dict round-trips. |
| `src/personacore/training/loop.py` | train()/estimate_loss()/sample() | ⚠️ WIRED but scaler not checkpointed | 295 lines; all orchestration present and wired; resume omits scaler state (CR-01). |
| `src/personacore/training/__init__.py` | public training barrel | ✓ VERIFIED | exports train/assemble_loss/build_scheduler/get_batch/load_split/sample/estimate_loss. |
| `scripts/train_bigram.py` | thin no-argparse entry, MVP see-output | ✓ VERIFIED | runs end-to-end, prints decoded text; outputs gitignored. |
| `tests/fixtures/bigram_corpus.txt` | ≥2 eos-separated docs | ✓ VERIFIED | encodes through frozen tokenizer with 8184 at ≥2 boundaries. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| loop.py | RuntimeConfig.autocast() + GradScaler | `runtime.autocast()` + `GradScaler(enabled=runtime.amp)` | ✓ WIRED | loop.py:115, 195. No `torch.cuda.*` in the loop. |
| loop.py | checkpoint save/load | `save_checkpoint` / `load_checkpoint` | ⚠️ PARTIAL | Wired for model/optimizer/scheduler/step/RNG, but **scaler not threaded** (CR-01). |
| loop.py | scaler.unscale_ before clip | mandatory AMP ordering | ✓ WIRED | unscale_ (loop.py:121) precedes clip (loop.py:122). |
| bigram.py | F.cross_entropy | `(B*T,V)` vs `(B*T)` flatten | ✓ WIRED | bigram.py:38. |
| data.py | artifacts/tokenizer.json | `from_json` + `encode(allowed_special='all')` | ✓ WIRED | data.py:32,35. Frozen, never retrained. |
| schedule.py | scheduler.state_dict() contract | LambdaLR object | ✓ WIRED | schedule.py:48-51. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| MVP see-output | `python scripts/train_bigram.py` | "trained 20 steps; sampled 41 ids (2 decodable): '\x00 h'" | ✓ PASS |
| AMP ordering + grad-accum + resume gates | `pytest tests/test_train_loop.py tests/test_overfit_batch.py tests/test_resume_curve.py` | 5 passed, 1 skipped (fp16 GPU smoke) | ✓ PASS |
| Full suite (venv 3.11) | `source .venv/bin/activate && python -m pytest -q` | 75 passed, 1 skipped | ✓ PASS |

### Probe Execution

No probes declared or conventional for this phase. (No `scripts/*/tests/probe-*.sh`; no probe references in PLAN/SUMMARY.) — SKIPPED.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| MODEL-01 | 03-01, 03-02 | From-scratch bigram baseline | ✓ SATISFIED | bigram.py + test_bigram_model.py GREEN |
| TRAIN-01 | 03-01/03/04 | AdamW + warmup/cosine + clip + configurable accum | ✓ SATISFIED | loop.py + schedule.py; AMP-ordering/grad-accum tests GREEN |
| TRAIN-02 | 03-01/04 | fp32 default + optional fp16 AMP+GradScaler, unscale-before-clip | ✓ SATISFIED | correct ordering verified; fp16 path present (GPU smoke skipif) |
| TRAIN-03 | 03-01/03 | Train/val split, periodic val loss, no leakage | ✓ SATISFIED | data.py doc-split + test_data_split.py GREEN |
| TRAIN-04 | 03-01/04 | Offline CSV logging survives restarts; curves reproducible | ⚠️ PARTIAL | fp32 reproducibility verified; fp16 resume diverges (scaler state lost — CR-01) |
| TRAIN-05 | 03-01/04 | Overfit-a-single-batch test passes | ✓ SATISFIED | test_overfits_single_fixed_batch PASSED |
| TRAIN-06 | 03-01/02/04 | assemble_loss seam + open-dict checkpoints | ✓ SATISFIED | loss.py + checkpoint.py open dict; tests GREEN |

All 7 declared requirement IDs are accounted for in REQUIREMENTS.md (each marked Complete). No orphaned requirements for Phase 3.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| src/personacore/checkpoint.py | 51-70, 73-97 | GradScaler state not in checkpoint contract | ⚠️ Blocker (CR-01) | fp16 resume not reproducible; contradicts CLAUDE.md `{...scaler...}` spec |
| src/personacore/training/data.py | 50-51 | input validation via bare `assert` (stripped under `python -O`) | ℹ️ Info (WR-05) | malformed fixture could silently produce empty split |
| src/personacore/training/data.py | 65 | `randint(0, len(arr)-block_size-1)` off-by-one (last window never sampled) | ℹ️ Info (WR-02) | drops one position of coverage; not a crash/leakage |
| src/personacore/training/loop.py | 73 | `estimate_loss` bound math crashes on `len(val_ids)==2` | ℹ️ Info (WR-01) | current fixture large enough; smaller fixture would crash in eval |
| src/personacore/training/loop.py | 123-125 | `scheduler.step()` advances even when `scaler.step()` skips | ℹ️ Info (WR-03) | GPU-only; desyncs LR curve on overflow; CPU no-op hides it |

No `TBD`/`FIXME`/`XXX` debt markers in any phase-modified file.

### Human Verification Required

#### 1. fp16 resume trajectory on CUDA

**Test:** On a CUDA GPU (or the target P100), run an uninterrupted fp16 training run vs a killed+resumed fp16 run and compare post-resume loss and GradScaler scale-factor trajectories.
**Expected:** Trajectories should match within 1e-6. With the current code they diverge because the GradScaler scale factor restarts from the default (65536) on resume rather than continuing the evolved value.
**Why human:** The CPU test suite cannot exercise this — `RuntimeConfig` auto-disables AMP on CPU, so the scaler is a no-op. Observing the fp16 resume divergence (and validating any fix) requires actual CUDA hardware.

### Gaps Summary

Four of the five success criteria are fully verified in the codebase: the from-scratch bigram trains and samples end-to-end (the MVP "see output" slice runs and prints decoded text), the overfit gate drives loss far below `ln(V)`, the loop implements AdamW + warmup/cosine + clip + configurable grad-accum with correct unscale-before-clip AMP ordering, the doc-level split has no leakage, and the `assemble_loss(..., ())` seam + open-dict checkpoints are in place. The full 3.11-venv suite is 75 passed / 1 skipped.

The one gap is on the **fp16 resume path (TRAIN-04)**: the `GradScaler` scale-factor and growth-tracker state are never serialized into the checkpoint or restored on resume. `save_checkpoint`/`load_checkpoint` have no `scaler` parameter and `loop.py` never threads the scaler through. On CPU the scaler is a no-op (AMP auto-disabled), so every test passes and the resume-equality gate holds — but on the fp16/P100 path (the only hardware where AMP is active, and the hardware Phase 5's long pretrain targets) a killed+resumed run restarts the scale factor from default and the post-resume trajectory diverges. This breaks the "reproduces the loss curve across a restart" guarantee on the AMP path and contradicts CLAUDE.md's explicit `{model, optimizer, scaler, step, rng_state, config}` checkpoint prescription (scaler is named and missing).

This is the precise risk Phase 3 exists to eliminate — validating checkpoint/resume on the AMP path *before* the expensive Phase 5 run. It is therefore treated as a gap on this phase rather than deferred: Phase 5's roadmap criteria assume a working resumable harness, they do not own building scaler-state serialization. The fix is small (thread `scaler.state_dict()` through save/load + add a GPU-gated regression test) and the four other criteria are solid.

---

_Verified: 2026-06-04_
_Verifier: Claude (gsd-verifier)_
