---
phase: 04-gpt-transformer-decoder
plan: 01
subsystem: testing
tags: [pytest, gpt, transformer, weight-tying, causal-attention, layernorm, lora-seam, tdd-red]

# Dependency graph
requires:
  - phase: 02-from-scratch-bpe-tokenizer
    provides: "ModelConfig vocab_size=8192/eos_id=8184 locked sizing the GPT is built around"
  - phase: 03-bigram-baseline-training-harness
    provides: "Locked forward(idx,targets)->(logits,loss) contract, train() loop, seed_everything, TrainConfig, test idioms (seed-first/allclose/CPU-only)"
provides:
  - "Nine RED tests/test_gpt_*.py gating MODEL-02..07 as executable contracts (all RED on import of personacore.model.GPT)"
  - "Executable per-tensor init-std contract asserting residual scaling on BOTH c_proj AND fc_out (D-04a)"
  - "Non-vacuous causality-perturbation guard (past-unchanged AND position-t-changed)"
  - "Manual-vs-sdpa equivalence and hand-rolled-LayerNorm-vs-nn.LayerNorm oracle gates"
  - "data_ptr-dedup param-count band gate and named-nn.Linear LoRA-seam structural gate"
affects: [04-02-PLAN, 04-03-PLAN, gpt-implementation, m2-lora]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "RED-first: every MODEL-02..07 success criterion has a failing test asserting its exact contract before any model code"
    - "data_ptr() identity/dedup as the only valid check for weight tying (value-copy passes equality but is two tensors)"
    - "Non-vacuous causality test: assert past unchanged AND perturbed position changed (an inert model fails)"
    - "Reference-oracle idiom reused: hand-rolled math == trusted PyTorch primitive (sdpa, nn.LayerNorm)"

key-files:
  created:
    - tests/test_gpt_model.py
    - tests/test_gpt_weight_tying.py
    - tests/test_gpt_init.py
    - tests/test_gpt_param_count.py
    - tests/test_gpt_lora_seam.py
    - tests/test_gpt_attention_equiv.py
    - tests/test_gpt_layernorm.py
    - tests/test_gpt_causality.py
    - tests/test_gpt_overfit.py
  modified: []

key-decisions:
  - "attn_impl is a GPT constructor arg (not a ModelConfig field) per RESEARCH Open Q2 — keeps the asdict-serialized ModelConfig free of a runtime-only flag while the equivalence test exercises both paths"
  - "GPT overfit test seeds lr=1e-3/max_steps=300 as a STARTING point (vs the bigram's 1e-1) with a comment delegating final tuning of the 6-layer net to the Plan-03 executor; the asserted bound is a band (< ln(8192)-2), not a fixed loss"
  - "Init test matches std targets by named-param SUFFIX so block-numbered params (blocks.0.attn.c_proj.weight) all match, and asserts both c_proj AND fc_out were actually seen (non-vacuous D-04a guard)"

patterns-established:
  - "RED-first MODEL gates: nine failing tests define the GPT contracts the Plan-02 implementation builds against"
  - "data_ptr-based tying/dedup checks cross-validate (a value-copy fails the tying test AND inflates the count test)"

requirements-completed: []  # RED tests authored; MODEL-02..07 go GREEN when Plan 02 ships gpt.py.

# Metrics
duration: 6min
completed: 2026-06-05
---

# Phase 4 Plan 01: RED MODEL Gates Summary

**Nine RED pytest files locking the Phase-4 GPT decoder contracts (forward shape, weight-tying data_ptr identity, residual-scaled init on c_proj AND fc_out, [10M,15M] param band, non-vacuous causality, manual-vs-sdpa + LayerNorm oracles, and overfit-through-the-Phase-3-loop) — all RED on `import personacore.model.GPT`.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-06-05
- **Completed:** 2026-06-05
- **Tasks:** 2
- **Files modified:** 9 (all created)

## Accomplishments
- Authored five structural/contract gates (forward contract, weight-tying, init-std, param-count, LoRA-seam) — Task 1.
- Authored four numeric/integration gates (attention equivalence, LayerNorm oracle, causality perturbation, overfit-one-batch) — Task 2.
- All nine fail with ImportError on `personacore.model.GPT` (LayerNorm test on `personacore.model.gpt.LayerNorm`) — the expected RED state.
- Init test asserts the `0.02/sqrt(2*n_layer)` residual std on BOTH `c_proj` AND `fc_out` (D-04a) and confirms both were seen.
- Causality test is non-vacuous (past positions bit-identical AND perturbed position changed).
- Overfit test reuses the Phase-3 `train()`/`TrainConfig`/`seed_everything` scaffold verbatim, swapping only the model.
- No Phase-1/2/3 regression: prior suite still 77 passed / 1 skipped; `make lint` (ruff check + format) clean on all nine files.

## Task Commits

Each task was committed atomically:

1. **Task 1: RED structural + contract gates** - `129c4ea` (test)
2. **Task 2: RED numeric-equivalence + causality + overfit gates** - `6c88916` (test)

**Plan metadata:** (this commit) (docs: complete plan)

## Files Created/Modified
- `tests/test_gpt_model.py` - Forward-contract `(logits,loss)` gate + generous random-init loss band (MODEL-02)
- `tests/test_gpt_weight_tying.py` - `lm_head.weight.data_ptr() == wte.weight.data_ptr()` identity (MODEL-03)
- `tests/test_gpt_init.py` - Per-tensor init std incl. residual-scaled `c_proj` AND `fc_out`, zero biases, ones LayerNorm weight (MODEL-04/D-04a)
- `tests/test_gpt_param_count.py` - `data_ptr`-dedup `count_parameters` in `[10M,15M]` (MODEL-05)
- `tests/test_gpt_lora_seam.py` - Six named `nn.Linear` projections reachable per block (MODEL-07)
- `tests/test_gpt_attention_equiv.py` - Manual-vs-sdpa via shared `load_state_dict`, `atol=1e-5` (MODEL-02)
- `tests/test_gpt_layernorm.py` - Hand-rolled `LayerNorm` vs `nn.LayerNorm`, `atol=1e-6` (MODEL-02)
- `tests/test_gpt_causality.py` - Non-vacuous perturbation guard (MODEL-06)
- `tests/test_gpt_overfit.py` - Overfit one fixed batch through the untouched Phase-3 `train()` (MODEL-02 SC#1)

## Decisions Made
- **attn_impl as constructor arg** (RESEARCH Open Q2): the equivalence test constructs `GPT(cfg, attn_impl="manual")` and `GPT(cfg, attn_impl="sdpa")`, so Plan 02 must expose this toggle rather than a `ModelConfig` field — keeps the serialized config clean of a runtime-only flag.
- **Init match-by-suffix + seen-both assertion**: std targets matched via `name.endswith(...)` so block-numbered params match, plus explicit `saw_c_proj`/`saw_fc_out` flags so the D-04a guard cannot pass vacuously if a suffix is absent.
- **Overfit lr=1e-3 starting point** with an in-test comment delegating tuning to the Plan-03 executor (a 6-layer net wants a smaller lr than the bigram's 1e-1); the assertion is a band, not a fixed loss.

## Deviations from Plan

None - plan executed exactly as written. Two ruff-format/import-sort autofixes were applied to the new test files during the lint step (`test_gpt_lora_seam.py` reformat, `test_gpt_layernorm.py` import grouping); these are formatting-only and part of the respective task commits. The overfit test's `ModelConfig` import was placed in the top import block (rather than a trailing `# noqa: E402` import) to keep the file lint-clean.

## Issues Encountered
- The local shell `python` resolves to pyenv (no global set) and the dev box is Python 3.12/3.14; per CLAUDE.md the mandatory Python 3.11 `.venv` was used for all pytest/ruff invocations (Kaggle/CI parity). No code impact.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan 02 implements `src/personacore/model/gpt.py` (GPT, Block, CausalSelfAttention, MLP, hand-rolled LayerNorm) plus the `from .gpt import GPT` barrel export to turn these nine gates GREEN.
- Contracts Plan 02 must satisfy are now executable: constructor `GPT(config, attn_impl="manual")`, six named `nn.Linear` (`q_proj/k_proj/v_proj/c_proj/fc_in/fc_out`), tied `lm_head.weight = wte.weight` after init, residual std on `c_proj` and `fc_out`, mask-before-softmax causal attention, and exported `LayerNorm`.
- No blockers.

## Self-Check: PASSED

All nine created test files and the SUMMARY exist on disk; both task commits (`129c4ea`, `6c88916`) are present in git history.

---
*Phase: 04-gpt-transformer-decoder*
*Completed: 2026-06-05*
