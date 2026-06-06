---
phase: 06-generation-sampling
verified: 2026-06-06T22:10:00Z
status: passed
score: 3/3 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 2/3
  gaps_closed:
    - "GEN-01/SC1: next_token now guards `if top_k is not None and top_k > 0:` — top_k=0/negatives are a no-op instead of crashing mid-stream (CR-01)."
    - "GEN-03/SC3: test_past_block_size_no_crash now seeds torch.manual_seed(1) before model construction — output length is deterministic and order-independent (WR-01)."
  gaps_remaining: []
  regressions: []
gaps: []
human_verification: []
---

# Phase 6: Generation & Sampling Verification Report

**Phase Goal:** A single shared `generate()` that powers tests, the notebook, and the demo — autoregressive decoding with the full sampling toolkit (greedy/temperature/top-k/top-p), correct EOS stopping (trims trailing token), respects max-length, and crops context to the last `block_size` tokens so generating past `block_size` never crashes. Generation unit tests pass for output shape, determinism under fixed seed + greedy decoding, and EOS-stop behavior.

**Verified:** 2026-06-06T22:10:00Z
**Status:** passed
**Re-verification:** Yes — after gap closure (commits 7cc8f94, 18c2f73)

> MVP-mode note: ROADMAP marks this phase `Mode: mvp`, but the phase goal is a
> capability description, not the required `As a … I want … so that …` User Story
> form. The three explicit ROADMAP Success Criteria (mapping 1:1 to GEN-01/02/03)
> were used as the observable-truth contract. The User Flow Coverage table is
> therefore not applicable; goal-backward verification against the success criteria
> was performed instead. This re-verification re-checks the two previously-failed
> truths in full and regression-checks the third.

## Re-Verification Summary

The prior verification (`gaps_found`, 2/3) recorded exactly two gaps. Both were
addressed and independently re-verified against the actual code (not the SUMMARY):

1. **CR-01 (GEN-01/SC1) — CLOSED.** `next_token` (sampling.py:86) now reads
   `if top_k is not None and top_k > 0:`. Independently reproduced the original
   failure mode: `top_k=0` and `top_k=-1` now return a valid `(1,1)` token with no
   crash (previously `IndexError` / `RuntimeError` on torch 2.7.1). A dedicated
   regression test `test_next_token_nonpositive_top_k_disabled` (test_generation.py:79)
   pins the no-op contract. Verified live, not from claims.

2. **WR-01 (GEN-03/SC3) — CLOSED.** `test_past_block_size_no_crash`
   (test_generation.py:147) now calls `torch.manual_seed(1)` before constructing the
   model, mirroring `test_output_shape`. Independently swept 200 perturbed global-RNG
   states: **0/200 failures** (was 17/200). The test also passes when run in complete
   isolation (`pytest tests/test_generation.py::test_past_block_size_no_crash` → 1
   passed), proving the order/RNG dependence is gone.

No regressions: full suite **116 passed, 1 skipped** (the 1 skip is an unrelated
pre-existing tokenizer-IO skip). All 9 generation tests + 5 text-wrapper tests pass.

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP Success Criterion) | Status | Evidence |
| --- | --- | --- | --- |
| 1 | One shared `generate()` supports greedy, temperature, top-k, and top-p sampling (GEN-01) | ✓ VERIFIED | `next_token` (sampling.py:79-91): greedy short-circuit + temperature→top-k→top-p→softmax→multinomial in locked order; top_k/top_p stack. CR-01 closed — `top_k<=0` guarded at :86, verified to no-op (returns valid `(1,1)`). Positive-value greedy/temp/top_k/top_p + stacking all return `(1,1)`. |
| 2 | Generation stops on EOS, trims trailing token, respects max-length, crops context to last `block_size` so past-`block_size` never crashes (GEN-02) | ✓ VERIFIED | core.py:53-68: `range(max_new_tokens)` bound; `idx[:, -bs:]` crop each step (`gpt.py` `T<=block_size` assert never trips); `if tok == eid: return` stops WITHOUT yielding/appending EOS (trim). `test_eos_stop`, `test_past_block_size_no_crash` green. |
| 3 | Generation unit tests pass for output shape, determinism (fixed seed + greedy), and EOS-stop (GEN-03) | ✓ VERIFIED | 9/9 generation tests pass — including the new regression test and the now-seeded `test_past_block_size_no_crash`. WR-01 closed: 0/200 perturbed-RNG failures + passes in isolation, so the suite is robustly green (no inherited-RNG luck). |

**Score:** 3/3 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/personacore/generation/sampling.py` | apply_temperature, top_k_filter, top_p_filter, next_token | ✓ VERIFIED | 92 lines, wired into core + tests. Top-p nucleus math pinned by `test_top_p_nucleus_exact`. CR-01 input-validation guard now present (:86). |
| `src/personacore/generation/core.py` | generate(...) generator + collect(...) drain | ✓ VERIFIED | 80 lines, `@torch.no_grad()` generator, context crop, EOS-stop-without-yield, delegates to `next_token`. Data-flowing against real `GPT.forward` (B,T,V). |
| `src/personacore/generation/text.py` | generate_text streaming str→str wrapper | ✓ VERIFIED | 102 lines, EOS-prepend seed, prompt-strip, cumulative-buffer delta streaming, max_new_tokens cap. Drives `core.generate`. |
| `src/personacore/generation/__init__.py` | barrel re-exporting public surface | ✓ VERIFIED | Re-exports apply_temperature, collect, generate, generate_text, generate_text_str, next_token, top_k_filter, top_p_filter; `__all__` present. |
| `tests/test_generation.py` | green core/sampling tests + tiny CPU fixture | ✓ VERIFIED | 197 lines, 9 tests (added `test_next_token_nonpositive_top_k_disabled`). `test_past_block_size_no_crash` now seeded — asserts correct contract, order-independent. |
| `tests/test_generation_text.py` | CPU-only wrapper tests | ✓ VERIFIED | 5 tests, stub tokenizer + tiny model; all pass. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| sampling.py | torch | topk/softmax/multinomial/argmax | ✓ WIRED | All four primitives present; topk now guarded by `top_k > 0`. |
| test_generation.py | personacore.generation(.sampling) | import collect + filters + next_token | ✓ WIRED | Lines 22-28. |
| core.py | model.forward | `logits, _ = model(idx_cond)` | ✓ WIRED | core.py:55, reads `logits[:, -1, :]` at :57. |
| core.py | sampling.next_token | logit→id delegation | ✓ WIRED | core.py:21 import, :56 call. |
| core.py | model.config.block_size | `idx[:, -bs:]` crop | ✓ WIRED | core.py:50, :54. |
| text.py | core.generate | drives id-space core | ✓ WIRED | text.py import + drive. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| core.generate | `logits` | `model(idx_cond)` (real GPT.forward, (B,T,V)) | Yes — real forward pass | ✓ FLOWING |
| core.collect | yielded `tok` | core.generate generator | Yes — accumulated into real (1,N) tensor | ✓ FLOWING |
| text.generate_text | streamed suffix | core.generate + tokenizer.decode of cumulative buffer | Yes — real decode of generated ids | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| `top_k=0` disabled idiom (CR-01) | `next_token(logits, top_k=0, generator=g)` | returns `(1,1)` tok=1, no crash | ✓ PASS |
| `top_k=-1` (CR-01) | `next_token(logits, top_k=-1, generator=g)` | returns `(1,1)` tok=1, no crash | ✓ PASS |
| WR-01 flakiness sweep (re-run) | seeded model × 200 perturbed global-RNG states, assert exact length | 0/200 fail | ✓ PASS |
| `test_past_block_size_no_crash` in isolation | `pytest …::test_past_block_size_no_crash` | 1 passed | ✓ PASS |
| Generation tests | `pytest tests/test_generation*.py -v` | 14 passed | ✓ PASS |
| Full suite | `pytest tests/` | 116 passed, 1 skipped | ✓ PASS |

### Probe Execution

No conventional `scripts/*/tests/probe-*.sh` probes found and none declared in the
PLANs. Verification used the pytest suite + direct behavioral checks instead.

| Probe | Command | Result | Status |
| --- | --- | --- | --- |
| (none declared / discovered) | — | — | SKIPPED |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| GEN-01 | 06-01, 06-02, 06-03 | Shared generate() with greedy/temperature/top-k/top-p | ✓ SATISFIED | Toolkit implemented + wired; positive-value modes verified; CR-01 input-validation gap closed and regression-tested. |
| GEN-02 | 06-02, 06-03 | EOS-aware stopping + max-length handling | ✓ SATISFIED | EOS-stop-without-yield, max_new_tokens bound, context crop all verified. |
| GEN-03 | 06-01, 06-02 | Generation unit tests (shape, determinism, EOS stop) | ✓ SATISFIED | 9 generation tests pass, robustly (order-independent); WR-01 flakiness closed. |

No orphaned requirements: REQUIREMENTS.md maps GEN-01/02/03 to Phase 6, and all three
appear across the plan `requirements:` fields.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| sampling.py | 88 | `top_p` accepts out-of-range values, silently degrades (WR-02) | ℹ️ Info | `p<=0` near-greedy, `p>1` no-op. Not goal-blocking. |
| core.py | 51,65-66 | `eos_id=None` + config eos_id None → never stops (WR-03) | ℹ️ Info | Latent only — `ModelConfig.eos_id` defaults set. Not live. |
| text.py | 67-70 | `max_new_tokens` not type-validated (WR-04) | ℹ️ Info | Float passes bound check, raises deep TypeError. Not goal-blocking. |

No `TBD`/`FIXME`/`XXX` debt markers in the phase's modified files (re-scanned
sampling.py + test_generation.py). The prior 🛑 Blocker (CR-01) and ⚠️ Warning (WR-01)
are both resolved.

### Human Verification Required

None. All success criteria are verifiable programmatically (id-space generation; the
Gradio demo is Phase 8).

### Gaps Summary

No gaps. The phase goal is fully achieved and robustly green. The shared decode core
(`core.py`), the streaming text wrapper (`text.py`), and the sampling primitives
(`sampling.py`) exist, are substantive, are correctly wired through a single decode
path, and pass real data. All three ROADMAP success criteria (GEN-01/02/03) are
satisfied:

- **SC1/GEN-01** — the full sampling toolkit works, and the previously-blocking
  `top_k<=0` crash is fixed with a value guard plus a regression test.
- **SC2/GEN-02** — EOS-stop + trim + max-length + crop-past-`block_size` (never
  crashes) verified behaviorally.
- **SC3/GEN-03** — all generation unit tests pass, now order-independent (the flaky
  `test_past_block_size_no_crash` is seeded and proven stable across 200 RNG states
  and in isolation).

Both prior gaps were independently re-verified against the actual code and commits
(7cc8f94, 18c2f73), not accepted from SUMMARY claims. No regressions in the full suite.

---

_Verified: 2026-06-06T22:10:00Z_
_Verifier: Claude (gsd-verifier)_
