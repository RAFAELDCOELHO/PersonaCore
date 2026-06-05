---
phase: 04-gpt-transformer-decoder
plan: 02
subsystem: model
tags: [gpt, transformer, decoder, causal-attention, layernorm, weight-tying, gpt2-init, lora-seam, tdd-green]

# Dependency graph
requires:
  - phase: 04-gpt-transformer-decoder
    plan: 01
    provides: "Nine RED tests/test_gpt_*.py executable contracts (forward, equiv, layernorm, tying, init, count, causality, lora-seam, overfit) this plan turns GREEN"
  - phase: 02-from-scratch-bpe-tokenizer
    provides: "ModelConfig vocab_size=8192/eos_id=8184/256/6/6/384 locked sizing the GPT is built around (D-06)"
  - phase: 03-bigram-baseline-training-harness
    provides: "LOCKED forward(idx,targets)->(logits,loss) contract + CE flatten replicated verbatim; the untouched train()/loop the GPT drops into"
provides:
  - "src/personacore/model/gpt.py — hand-rolled GPT-2 decoder (GPT, Block, CausalSelfAttention, MLP, LayerNorm)"
  - "GPT exported from personacore.model (barrel export)"
  - "Eight MODEL unit gates GREEN (MODEL-02..07) + the overfit integration gate's model"
  - "Six named nn.Linear projections per block (q/k/v/c_proj, fc_in/fc_out) — the M2 LoRA seam (naming only)"
  - "True weight-tied head (lm_head.weight IS wte.weight, data_ptr identity); residual-scaled init on c_proj AND fc_out"
affects: [04-03-PLAN, m2-lora, phase-5-pretraining]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "init -> residual-override -> tie ordering (Pattern 1): tying AFTER init keeps the surviving tensor at the embedding init (std 0.02) so the head is never re-initialized"
    - "Weight tying via nn.Parameter assignment (self.lm_head.weight = self.wte.weight) — shared storage, NOT a value copy"
    - "Residual-scaled std 0.02/sqrt(2*n_layer) on BOTH residual-stream writers (c_proj AND fc_out, D-04a)"
    - "Manual attention factors q/k/v projection OUTSIDE the attn_impl branch so manual and sdpa consume identical tensors (numerical-equivalence guarantee)"
    - "Hand-rolled LayerNorm with population variance (unbiased=False) to match nn.LayerNorm; F.gelu/F.cross_entropy/sdpa as allowed primitives/oracles"
    - "Pure model boundary: base CE only, autocast-safe (no torch.cuda/.half/dtype casts), no import from training/"

key-files:
  created:
    - src/personacore/model/gpt.py
  modified:
    - src/personacore/model/__init__.py

key-decisions:
  - "attn_impl is a GPT constructor arg defaulting to 'manual' (RESEARCH Open Q2 / D-02) — keeps the asdict-serialized ModelConfig free of a runtime-only flag while the equivalence test exercises both manual and sdpa paths"
  - "Tying done AFTER both the base init pass and the residual-scaled override (Pattern 1 ordering) so the shared tensor carries the embedding's std-0.02 init and lm_head is never separately re-initialized"
  - "lm_head is bias=False so the tied weight is the only head parameter (a head bias would be a second untied head param inflating the count-once test)"

patterns-established:
  - "Single-file nanoGPT-style decoder (gpt.py) mirroring the existing bigram.py layout"
  - "Residual init override must hit BOTH c_proj.weight AND fc_out.weight suffixes (the single most error-prone D-04a fact)"

requirements-completed: [MODEL-02, MODEL-03, MODEL-04, MODEL-05, MODEL-06, MODEL-07]

# Metrics
duration: 8min
completed: 2026-06-05
---

# Phase 4 Plan 02: GPT Transformer Decoder Summary

**A from-scratch ~13.9M-parameter GPT-2 decoder (`GPT`/`Block`/`CausalSelfAttention`/`MLP`/hand-rolled `LayerNorm`) in `src/personacore/model/gpt.py` that honors the LOCKED `forward(idx,targets)->(logits,loss)` contract verbatim, turning all eight Plan-01 RED MODEL gates GREEN with zero training-harness changes.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-06-05
- **Completed:** 2026-06-05
- **Tasks:** 2
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments
- **Task 1** — Hand-rolled `LayerNorm` (population variance, eps=1e-5), `CausalSelfAttention` (separate q/k/v_proj + c_proj, manual mask-before-softmax path + sdpa toggle, non-persistent causal buffer), and `MLP` (fc_in/fc_out, F.gelu tanh-approx). LayerNorm oracle gate GREEN.
- **Task 2** — `Block` (pre-norm, residual around attn/MLP) and `GPT` (wte+wpe+blocks+ln_f+bias-free lm_head) with the load-bearing init->residual-override->tie ordering, the locked bigram CE forward tail, and the `GPT` barrel export. Seven remaining gates GREEN.
- Weight tying is a TRUE shared tensor (`lm_head.weight.data_ptr() == wte.weight.data_ptr()`), so the tied block counts once and the param count lands in [10M, 15M].
- Residual-scaled init (`0.02/sqrt(2*n_layer)`) applied to BOTH `c_proj` AND `fc_out` (D-04a); std 0.02 elsewhere; biases 0; LayerNorm weight 1/bias 0.
- Manual attention path matches `F.scaled_dot_product_attention(is_causal=True)` within atol 1e-5 (shared weights).
- Causality guard passes non-vacuously: perturbing token t leaves logits < t bit-identical and changes logits at t.
- Model stays PURE and autocast-safe: base CE only, no `assemble_loss`/`generate`/`torch.cuda`/`.half`/dtype casts, no import from `training/`.
- No regression: full suite **88 passed / 1 skipped** (was 77 passing before Phase 4 GPT — the 9 RED gates are now GREEN, plus the prior Phase-1/2/3 tests untouched). `make lint` (ruff check + format) clean.

## Task Commits

Each task was committed atomically:

1. **Task 1: LayerNorm + CausalSelfAttention + MLP submodules** - `af0de7a` (feat)
2. **Task 2: GPT + Block assembly — init, tying, forward, export** - `807d269` (feat)

**Plan metadata:** (this commit) (docs: complete plan)

## Files Created/Modified
- `src/personacore/model/gpt.py` (created) - Hand-rolled GPT-2 decoder: `LayerNorm`, `CausalSelfAttention`, `MLP`, `Block`, `GPT` (init recipe, weight tying, locked forward).
- `src/personacore/model/__init__.py` (modified) - Added `from .gpt import GPT` and `"GPT"` to `__all__` (the only edit to an existing file).

## Decisions Made
- **attn_impl as constructor arg, default "manual"** (RESEARCH Open Q2 / D-02): exposes the equivalence toggle without polluting the asdict-serialized `ModelConfig` with a runtime-only flag.
- **init -> residual-override -> tie ordering** (Pattern 1): tying after init means the surviving shared tensor carries the embedding's std-0.02 init and `lm_head` is never separately re-initialized — avoiding double-init ambiguity.
- **lm_head bias=False**: the tied weight is the sole head parameter, keeping the count-once test clean.

## Deviations from Plan

None - plan executed exactly as written. Four ruff line-length (E501) fixes and one `ruff format` collapse of the `blocks` ModuleList comprehension were applied during the lint step; these are formatting-only and folded into the respective task commits. Em-dashes in inline comments count toward the 100-char limit, so one mask comment was moved to its own line.

## Issues Encountered
- The local shell `python` resolves to pyenv (Python 3.12/3.14 dev box); per CLAUDE.md the mandatory Python 3.11 `.venv` was used for all pytest/ruff invocations (Kaggle/CI parity). No code impact.
- A pre-existing Phase-2 tokenizer test (`test_tokenizer_io.py`) emits a "corpus exhausted" UserWarning unrelated to this plan; not in scope, not modified.

## Known Stubs

None — `gpt.py` is fully wired: real embeddings, real attention math, real init, real forward. No placeholder data or empty returns.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan 03 (and Phase 5 pretraining) can now train the real GPT through the untouched Phase-3 `train()` loop — the model drops in via the locked forward contract with `attn_impl="sdpa"` available for the GPU path.
- The M2 LoRA seam is open: six named `nn.Linear` projections per block are reachable by name with no wrapper.
- No blockers.

## Self-Check: PASSED

Both task commits (`af0de7a`, `807d269`) are present in git history; `src/personacore/model/gpt.py` (created) and `src/personacore/model/__init__.py` (modified) exist on disk; `from personacore.model import GPT` succeeds; all eight MODEL unit gates GREEN and the full suite is 88 passed / 1 skipped.

---
*Phase: 04-gpt-transformer-decoder*
*Completed: 2026-06-05*
