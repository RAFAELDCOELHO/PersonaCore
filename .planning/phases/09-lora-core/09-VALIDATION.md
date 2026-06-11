---
phase: 9
slug: lora-core
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-11
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ~=9.0 (dev extra, installed in `.venv`) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (testpaths=tests, pythonpath=.) |
| **Quick run command** | `.venv/bin/pytest tests/test_lora_*.py -q -x` |
| **Full suite command** | `make test` (= `pytest -q`; all existing tests MUST stay green) |
| **Estimated runtime** | ~30 seconds (quick) / full suite minutes |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/pytest tests/test_lora_*.py -q -x` (new suite only, < 30 s)
- **After every plan wave:** Run `make test` (full suite — proves existing tests stay green; `checkpoint.py` is the only touched v1.0 module and the change is additive)
- **Before `/gsd:verify-work`:** Full suite must be green + smoke script pass on MPS
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| *(filled by planner — task IDs assigned in PLAN.md files)* | | | LORA-01..05 | | | unit | see requirement→test map below | ❌ W0 | ⬜ pending |

**Requirement → Test Map (from RESEARCH.md):**

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LORA-01 | B=0 zero-delta at init; A-Gaussian; α/r scale; dropout on LoRA branch, train-mode only; six projections wrapped per block via post-load injection | unit | `.venv/bin/pytest tests/test_lora_layer.py tests/test_lora_inject.py -q -x` | ❌ Wave 0 |
| LORA-02 | Grad isolation: after training steps every base param bit-untouched (`torch.equal`); canary: trainables moved; fresh-optimizer state covers only A/B | unit | `.venv/bin/pytest tests/test_lora_training.py -q -x` | ❌ Wave 0 |
| LORA-03 | Artifact round-trips `weights_only=True`; schema-version raise; fingerprint warn-but-load; two-artifact load (`load_slim`+`load_adapter`+inject) reproduces logits | unit | `.venv/bin/pytest tests/test_lora_artifact.py -q -x` | ❌ Wave 0 |
| LORA-04 | Merged forward ≡ base+adapter ≤1e-5 (CPU); unmerge bit-exact via stored clone; `merged_state_dict()` pure with vanilla-GPT key set | unit | `.venv/bin/pytest tests/test_lora_merge.py -q -x` | ❌ Wave 0 |
| LORA-05 | Enable/disable round-trip bit-identical; context manager exception-safe; eject restores vanilla; param-count = `r·n_layer·18·n_embd`; tied `data_ptr` unchanged post-injection; load→inject→freeze ordering pinned | unit | `.venv/bin/pytest tests/test_lora_toggle.py tests/test_lora_inject.py -q -x` | ❌ Wave 0 |
| LORA-02/05 (real weights) | Canary + bit-untouched on `best.pt` over TinyStories bins on MPS | smoke (manual-run script, asserts inline) | `.venv/bin/python scripts/train_adapter_smoke.py` | ❌ Wave 0 (local-only; CI-skipped — needs gitignored artifacts) |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_lora_layer.py` — covers LORA-01 (init/scale/dropout/identity)
- [ ] `tests/test_lora_inject.py` — covers LORA-01/05 (allowlist, ordering, tied-tensor, param count)
- [ ] `tests/test_lora_toggle.py` — covers LORA-05 (D-05/D-06 toggle, context manager, eject)
- [ ] `tests/test_lora_merge.py` — covers LORA-04 (D-07/D-08)
- [ ] `tests/test_lora_artifact.py` — covers LORA-03 (D-01/D-02/D-03)
- [ ] `tests/test_lora_training.py` — covers LORA-02 (canary, kill+resume — adapt `test_resume_curve.py` pattern)
- Framework install: none needed (pytest present)

All unit tests use the `_tiny_config()` fixture precedent (`ModelConfig(block_size=32, n_layer=1..2, n_head=2, n_embd=16)` from `tests/test_slim_checkpoint.py`) — CPU-only, GPU-free, seconds to run. Bit-identity asserts use `torch.equal`; tolerance asserts use `torch.allclose(atol=1e-5)` on CPU.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Adapter smoke run on real weights (MPS) | LORA-02/05 | Needs gitignored artifacts (`best.pt`, TinyStories bins) and MPS device — CI-skipped | Run `.venv/bin/python scripts/train_adapter_smoke.py`; inline asserts + non-zero exit on failure |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
