---
phase: 7
slug: evaluation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-09
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `07-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (`[dev]` extra), verified installed (CPU-only suite) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths=["tests"]`, `pythonpath=["."]`) |
| **Quick run command** | `pytest tests/test_perplexity.py tests/test_ablation_config.py -x -q` |
| **Full suite command** | `make test` (= `pytest -q`) |
| **Estimated runtime** | ~30 seconds (CPU, tiny fixtures — no `best.pt` / `val.bin`) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_perplexity.py tests/test_ablation_config.py -x -q`
- **After every plan wave:** Run `make test` (full CPU suite — guards the model-flag blast radius)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~30 seconds

> Note: the real ablation cohort + headline PPL are produced by the (non-pytest) driver
> scripts run by hand on M3. pytest validates the *math and flag semantics* on tiny fixtures;
> the long training runs are manual artifacts, not part of the automated sampling loop.

---

## Per-Task Verification Map

| Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|------|------|-------------|-----------------|-----------|-------------------|-------------|--------|
| perplexity | 1 | EVAL-01 | N/A (local, offline measurement) | unit | `pytest tests/test_perplexity.py::test_matches_bruteforce -x` | ❌ W0 | ⬜ pending |
| perplexity | 1 | EVAL-01 | N/A | unit | `pytest tests/test_perplexity.py::test_token_count -x` | ❌ W0 | ⬜ pending |
| perplexity | 1 | EVAL-01 | N/A | unit | `pytest tests/test_perplexity.py::test_partial_window -x` | ❌ W0 | ⬜ pending |
| ablation-config | 1 | EVAL-03 | N/A | unit | `pytest tests/test_ablation_config.py::test_defaults_unchanged -x` | ❌ W0 | ⬜ pending |
| ablation-config | 1 | EVAL-03 | N/A | unit | `pytest tests/test_ablation_config.py::test_untie -x` | ❌ W0 | ⬜ pending |
| ablation-config | 1 | EVAL-03 | N/A | unit | `pytest tests/test_ablation_config.py::test_no_pos -x` | ❌ W0 | ⬜ pending |
| ablation-config | 1 | EVAL-03 | N/A (regression — defaults must not move) | regression | `pytest tests/test_gpt_weight_tying.py tests/test_gpt_param_count.py tests/test_gpt_init.py -x` | ✅ exists | ⬜ pending |
| qualitative | 2 | EVAL-02 | N/A | unit | `pytest tests/test_generation.py -x` (existing greedy-determinism cover) | ✅ exists | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_perplexity.py` — covers EVAL-01 (brute-force per-token oracle, token-count audit `corpus_len - n_windows`, partial-window handling). Use a tiny CPU model + a hand-built ~300-token array fixture (NOT `best.pt` / `val.bin` — keep CPU-fast).
- [ ] `tests/test_ablation_config.py` — covers EVAL-03 flag semantics (`weight_tying`/`use_pos_emb` defaults unchanged → tied `data_ptr`, 13.89M params; `weight_tying=False` → distinct `data_ptr`, +3.15M; `use_pos_emb=False` → forward runs, −98,304 params).
- [x] Framework install — not needed (pytest present in `[dev]`).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Headline full-val perplexity on real `best.pt` | EVAL-01 | Requires loading the 50k checkpoint + sweeping 12.6M-token `val.bin` — too slow for CI | Run the eval driver on M3; record PPL + total token count in the results table |
| Ablation cohort (baseline + 3 variants) trained to reduced budget | EVAL-03 | Multi-hour training runs on M3/MPS — not a unit test | Run the ablation driver; compare PPL/params/val-loss in the committed results table |
| Curated qualitative samples for the writeup | EVAL-02 | Human curation/selection (representative, not cherry-picked) | Generate with fixed prompts + Phase-6 sampling defaults; capture with honest selection note |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (`test_perplexity.py`, `test_ablation_config.py`)
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
