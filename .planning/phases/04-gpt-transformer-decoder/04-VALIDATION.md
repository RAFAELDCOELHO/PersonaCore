---
phase: 4
slug: gpt-transformer-decoder
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-05
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `04-RESEARCH.md` § Validation Architecture (requirement→test map mirrors Phase-3 test style).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (`pyproject.toml` `[tool.pytest.ini_options]`, `testpaths=["tests"]`, `pythonpath=["."]`) |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/test_gpt_*.py -x -q` |
| **Full suite command** | `make test` (= `pytest`, CPU-only, GPU-free) |
| **Estimated runtime** | ~30–90 seconds (overfit gate dominates; bounded step budget) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_gpt_*.py -x -q` (new MODEL files only — fast, CPU)
- **After every plan wave:** Run `make test` (full suite — ensures the GPT swap didn't regress the Phase-1/2/3 harness)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| — | — | 0 | MODEL-02 | — / — | N/A (offline CPU model) | unit (contract) | `pytest tests/test_gpt_model.py::test_forward_contract -x` | ❌ W0 | ⬜ pending |
| — | — | 0 | MODEL-02 | — / — | N/A | unit (equivalence) | `pytest tests/test_gpt_attention_equiv.py -x` | ❌ W0 | ⬜ pending |
| — | — | 0 | MODEL-02 | — / — | N/A | unit (oracle) | `pytest tests/test_gpt_layernorm.py -x` | ❌ W0 | ⬜ pending |
| — | — | 0 | MODEL-03 | — / — | N/A | unit | `pytest tests/test_gpt_weight_tying.py -x` | ❌ W0 | ⬜ pending |
| — | — | 0 | MODEL-04 | — / — | N/A | unit | `pytest tests/test_gpt_init.py -x` | ❌ W0 | ⬜ pending |
| — | — | 0 | MODEL-05 | — / — | N/A | unit | `pytest tests/test_gpt_param_count.py -x` | ❌ W0 | ⬜ pending |
| — | — | 0 | MODEL-06 | — / — | N/A | unit | `pytest tests/test_gpt_causality.py -x` | ❌ W0 | ⬜ pending |
| — | — | 0 | MODEL-07 | — / — | N/A | unit (structural) | `pytest tests/test_gpt_lora_seam.py -x` | ❌ W0 | ⬜ pending |
| — | — | 1 | MODEL-02 (SC#1) | — / — | N/A | integration (overfit gate) | `pytest tests/test_gpt_overfit.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*
*Task IDs filled in by the planner once plan/wave assignment is finalized; the requirement→test mapping above is the binding contract.*

---

## Wave 0 Requirements

- [ ] `tests/test_gpt_model.py` — forward-contract `(logits, loss)` identical to bigram (MODEL-02)
- [ ] `tests/test_gpt_attention_equiv.py` — manual path vs `F.scaled_dot_product_attention(is_causal=True)`, `allclose atol≈1e-5` (MODEL-02)
- [ ] `tests/test_gpt_layernorm.py` — hand-rolled LayerNorm vs `nn.LayerNorm`, `allclose atol≈1e-6`, population variance (MODEL-02)
- [ ] `tests/test_gpt_weight_tying.py` — `lm_head.weight.data_ptr() == wte.weight.data_ptr()` (MODEL-03)
- [ ] `tests/test_gpt_init.py` — per-tensor init std incl. **both** `c_proj` AND `fc_out` residual scaling (MODEL-04)
- [ ] `tests/test_gpt_param_count.py` — `data_ptr` dedup count ∈ `[10e6, 15e6]` (MODEL-05)
- [ ] `tests/test_gpt_causality.py` — perturb token at `t`: logits `<t` unchanged AND logits at `t` changed (non-vacuous) (MODEL-06)
- [ ] `tests/test_gpt_lora_seam.py` — six named `nn.Linear` (`q_proj/k_proj/v_proj/c_proj/fc_in/fc_out`) reachable by name, no wrapper (MODEL-07)
- [ ] `tests/test_gpt_overfit.py` — overfit one fixed batch through the existing `training/loop.py` (MODEL-02 SC#1)
- [ ] Framework install: none — pytest already present
- [ ] Shared fixtures: none required; optional `gpt_eval_model` fixture (eval-mode, tiny `block_size`) could DRY causality/equivalence tests

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| — | — | — | — |

*All phase behaviors have automated verification (CPU-only, GPU-free).*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
