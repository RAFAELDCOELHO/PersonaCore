---
phase: 04-gpt-transformer-decoder
verified: 2026-06-05T00:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
deferred:
  - truth: "forward() guards against / crops sequences longer than block_size (CR-01)"
    addressed_in: "Phase 6"
    evidence: "Phase 6 success criterion: 'Generation stops on EOS, trims the trailing token, respects max-length, and crops context to the last block_size tokens so generating past block_size never crashes'"
---

# Phase 4: GPT Transformer Decoder Verification Report

**Phase Goal:** A from-scratch ~10–15M-parameter GPT decoder — the central "I built a transformer" claim — that drops into the already-proven harness, with the densest cluster of silent correctness bugs gated by tests and the LoRA seam left open.
**Verified:** 2026-06-05
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP Success Criterion) | Status | Evidence |
| --- | --- | --- | --- |
| 1 | GPT decoder (causal MHA masked-before-softmax, scaled 1/√d_head, GELU MLP, pre-norm blocks + residuals, learned pos-emb, final `ln_f`) swaps into the existing loop and overfits a single batch | ✓ VERIFIED | `gpt.py:99-102` masks before `F.softmax` with `-inf`; `:99` scales by `math.sqrt(self.d_head)`; `:126` `F.gelu(approximate="tanh")`; `Block.forward :143-144` pre-norm + residual; `wpe :160` learned pos-emb; `ln_f :163,196`. `test_gpt_overfit.py` GREEN through the UNTOUCHED `training/loop.train()` — directly executed: final loss ~5e-4 ≪ ln(8192)-2. `git status` confirms only the test changed, not loop.py. |
| 2 | Causality-perturbation test passes (changing token t cannot change logits at positions < t) | ✓ VERIFIED | `test_gpt_causality.py` GREEN; re-ran live: past `<t` bit-identical AND position `t` changed (non-vacuous). |
| 3 | Weight tying is a true shared tensor (`data_ptr()` identity) and per-tensor init-std confirms GPT-2 init incl. residual-scaled `c_proj` | ✓ VERIFIED | Live probe: `lm_head.weight.data_ptr() == wte.weight.data_ptr()` → True (`gpt.py:177` Parameter assignment, not clone). Init: `c_proj` AND `fc_out` both std≈0.005774 (`0.02/√12`), base std 0.02 elsewhere (`gpt.py:169-173`). Both suffixes asserted non-vacuously in `test_gpt_init.py`. |
| 4 | Exact parameter counting (tied weights counted once) hits the ~10–15M target | ✓ VERIFIED | Live data_ptr-dedup count = **13,891,584**, inside [10M,15M]. `test_gpt_param_count.py` GREEN. |
| 5 | Every adaptable projection is a named `nn.Linear` called as a module (M2 LoRA seam — naming only) | ✓ VERIFIED | Live: all 6 of `q_proj/k_proj/v_proj/c_proj/fc_in/fc_out` present as `nn.Linear` named modules in every block. Separate q/k/v (no fused `c_attn`). `test_gpt_lora_seam.py` GREEN. |

**Score:** 5/5 truths verified

### Deferred Items

| # | Item | Addressed In | Evidence |
| --- | --- | --- | --- |
| 1 | `forward()` lacks a `block_size` bounds guard / context cropping (CR-01) | Phase 6 | Phase 6 SC: "crops context to the last `block_size` tokens so generating past `block_size` never crashes" — context-window safety is an explicit Phase-6 deliverable. |

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/personacore/model/gpt.py` | Hand-rolled GPT-2 decoder (GPT, Block, CausalSelfAttention, MLP, LayerNorm) | ✓ VERIFIED | 204 lines; all five classes present; pure model (no `assemble_loss`/`generate`/`torch.cuda`/`.half`); wired into the loop via the overfit gate. |
| `src/personacore/model/__init__.py` | Barrel export of GPT | ✓ VERIFIED | `from .gpt import GPT`; `"GPT"` in `__all__`; `from personacore.model import GPT` succeeds. |
| 9 × `tests/test_gpt_*.py` | RED→GREEN MODEL gates | ✓ VERIFIED | All 9 files exist; 11 tests run GREEN; assert the exact contracts (data_ptr, both residual suffixes, non-vacuous causality, [10M,15M] band, six named Linear). |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `gpt.py` | `config.ModelConfig` | constructor reads sizing | ✓ WIRED | `GPT(config)` reads vocab/block/layer/head/embd; 13.89M params confirm sizing. |
| `gpt.py` | `F.cross_entropy` | locked CE flatten identical to bigram | ✓ WIRED | `:202` `F.cross_entropy(logits.view(B*T,V), targets.view(B*T))` — verbatim bigram tail. |
| `model/__init__.py` | `gpt.py` | `from .gpt import GPT` | ✓ WIRED | Import resolves. |
| `test_gpt_overfit.py` | `training.loop.train` | `train(model=GPT(...), fixed_batch=...)` | ✓ WIRED | Trains real GPT end-to-end; harness untouched (git status). |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Weight tying is shared storage | live `data_ptr()` compare | True | ✓ PASS |
| Param count tied-once in band | live dedup sum | 13,891,584 | ✓ PASS |
| Residual init on c_proj AND fc_out | live std check | both ≈0.005774 | ✓ PASS |
| Causal mask non-vacuous | live perturbation | past identical, t changed | ✓ PASS |
| manual == sdpa | live allclose atol 1e-5 | True | ✓ PASS |
| Six named nn.Linear per block | live named_modules | all present | ✓ PASS |
| CR-01 hazard (T > block_size) | live forward T=20, bs=16 | cryptic IndexError (no guard) | ⚠️ see Anti-Patterns |

### Test Suite

| Scope | Command | Result |
| --- | --- | --- |
| 9 GPT gates | `.venv/bin/python -m pytest tests/test_gpt_*.py` | 11 passed |
| Full suite (regression) | `.venv/bin/python -m pytest` | 88 passed, 1 skipped, 1 pre-existing warning |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| MODEL-02 | 04-01/02/03 | GPT decoder (~10–15M): causal MHA masked-before-softmax, scaled √d_k, MLP, pre-norm, learned pos-emb | ✓ SATISFIED | Truth 1; gpt.py + overfit gate |
| MODEL-03 | 04-01/02 | Weight tying, tensor-identity test | ✓ SATISFIED | Truth 3; data_ptr identity live-verified |
| MODEL-04 | 04-01/02 | GPT-2 init, per-tensor init-std check | ✓ SATISFIED | Truth 3; both residual suffixes std≈0.005774 |
| MODEL-05 | 04-01/02 | Exact param count, ~10–15M | ✓ SATISFIED | Truth 4; 13.89M deduped |
| MODEL-06 | 04-01/02 | Causality perturbation test | ✓ SATISFIED | Truth 2; non-vacuous |
| MODEL-07 | 04-01/02 | Every adaptable projection named nn.Linear (M2 seam) | ✓ SATISFIED | Truth 5; six named Linear/block |

No orphaned requirements: REQUIREMENTS.md maps exactly MODEL-02..07 to Phase 4, all claimed by plans, all SATISFIED.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `gpt.py` | 188-192 | No `block_size` bounds guard in `forward()` (CR-01) | ⚠️ Warning | `T > block_size` raises a cryptic `IndexError` on CPU (live-confirmed) / fatal CUDA device-side assert on GPU. Not reachable in any Phase-4 success path (overfit/causality/equivalence all use ≤ block_size). The reachable caller is `loop.sample()` (no `idx[:, -block_size:]` crop), but it has no shipped caller and context-window safety is an explicit Phase-6 success criterion → deferred, not a Phase-4 blocker. A defensive `assert T <= self.config.block_size` would still be cheap hygiene to add now. |
| `gpt.py` | 46-49, 99-104 | Hand-rolled LayerNorm + manual softmax run in fp16 under autocast (WR-01/WR-04) | ℹ️ Info | The fp32 oracle-equivalence the tests prove holds on CPU/fp32; fp16 numerical divergence only manifests under GPU autocast pretraining (Phase 5). No Phase-4 criterion is affected. Worth addressing before the Phase-5 long run. |
| `gpt.py` | 96-98 | `attn_impl` not validated; unknown string silently runs manual path (WR-03) | ℹ️ Info | Latent quiet-failure in the equivalence toggle; default "manual" is safe. Hygiene. |
| `gpt.py` | 97 | sdpa branch hardcodes `dropout_p=0.0`, ignoring `config.dropout` (WR-02) | ℹ️ Info | Inert at the locked `dropout=0.0`; latent asymmetry if dropout is enabled. |

No debt markers (TBD/FIXME/XXX) found in phase files. No placeholder/stub patterns.

### Human Verification Required

None. All five success criteria are concrete, programmatically verifiable invariants and were verified by direct execution (data_ptr identity, param count, init std, causality perturbation, manual/sdpa equivalence) plus the GREEN overfit integration gate. No visual/real-time/external-service behavior is in scope for this phase.

### Gaps Summary

No gaps block the phase goal. All five ROADMAP success criteria are observably true in the codebase, verified by direct execution rather than SUMMARY claims:

- The hand-rolled decoder math is correct: mask-before-softmax (`-inf`), `1/√d_head` scale, manual path bit-equivalent to `sdpa` (atol 1e-5), population-variance LayerNorm.
- The three high-risk silent bugs are gated: weight tying is genuine shared storage (data_ptr identity, not a value copy), residual-scaled init hits BOTH `c_proj` and `fc_out` (the D-04a trap), and the causality test is non-vacuous.
- Param count is exactly 13,891,584 (tied once), in the [10M,15M] band.
- The model drops into the UNTOUCHED Phase-3 `train()` loop and overfits a single batch — the harness-swap proof — with only the test file changed.
- The M2 LoRA seam is open: six separately-named `nn.Linear` projections per block.

The code-review BLOCKER **CR-01** (no `block_size` guard in `forward()`) was independently reproduced (cryptic `IndexError` for `T > block_size`). It does **not** affect any Phase-4 success criterion — the overfit/training/causality/equivalence paths all operate at or below `block_size`. The only reachable trigger is the `loop.sample()` helper, which lacks `idx[:, -block_size:]` cropping; however context-window-safe generation is the **literal, explicit success criterion of Phase 6** ("crops context to the last `block_size` tokens so generating past `block_size` never crashes"). It is therefore classified as a **deferred** concern owned by Phase 6, downgraded from BLOCKER to a Phase-4 WARNING. Recommendation: a one-line defensive `assert T <= self.config.block_size` in `forward()` is cheap insurance and would convert the fatal CUDA-context kill into an actionable error before Phase 5's GPU run — optional for Phase 4 closure.

---

_Verified: 2026-06-05_
_Verifier: Claude (gsd-verifier)_
