---
phase: 6
slug: generation-sampling
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-06
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (CPU-only, GPU/MPS-free) |
| **Config file** | `pyproject.toml`; shared fixtures in `tests/conftest.py` |
| **Quick run command** | `.venv/bin/python -m pytest tests/test_generation.py -x -q` |
| **Full suite command** | `make test` |
| **Estimated runtime** | ~10 seconds (tiny fixture model, not `best.pt`) |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/python -m pytest tests/test_generation.py -x -q`
- **After every plan wave:** Run `make test` (full CPU suite)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~10 seconds

---

## Per-Task Verification Map

| Req ID | Behavior | Test Type | Automated Command | File Exists |
|--------|----------|-----------|-------------------|-------------|
| GEN-01 | top-k restricts support to k tokens; top-p restricts to nucleus | unit | `pytest tests/test_generation.py::test_top_k_top_p_support -x` | ❌ W0 |
| GEN-01 | temperature scaling affects distribution (low temp → near-greedy) | unit | `pytest tests/test_generation.py::test_temperature -x` | ❌ W0 |
| GEN-01 | top-p keeps expected token set on hand-computed logits (pins A1) | unit | `pytest tests/test_generation.py::test_top_p_nucleus_exact -x` | ❌ W0 |
| GEN-02 | EOS-stop: core halts without yielding `eos_id`; seq never ends in EOS | unit | `pytest tests/test_generation.py::test_eos_stop -x` | ❌ W0 |
| GEN-02 | Context crop: generating past `block_size` does not raise | unit | `pytest tests/test_generation.py::test_past_block_size_no_crash -x` | ❌ W0 |
| GEN-03 | Output shape: `collect()` returns `(1, prompt_len + n)` LongTensor (no EOS) | unit | `pytest tests/test_generation.py::test_output_shape -x` | ❌ W0 |
| GEN-03 | Determinism — greedy: two `argmax` runs bit-identical | unit | `pytest tests/test_generation.py::test_greedy_deterministic -x` | ❌ W0 |
| GEN-03 | Determinism — sampled: two identically-seeded `torch.Generator` runs match | unit | `pytest tests/test_generation.py::test_seeded_sampling_deterministic -x` | ❌ W0 |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Determinism test idioms:**
- *Greedy:* tiny `GPT(ModelConfig(...))` under `torch.manual_seed(s)`; call greedy `collect()` twice; assert equal. No `Generator` needed (argmax has no RNG).
- *Sampled:* `g1 = torch.Generator().manual_seed(0); g2 = torch.Generator().manual_seed(0)`; pass each into `collect(..., generator=gN)`; assert equal. Demonstrates seed isolation (avoid global RNG — `load_checkpoint` mutates it).
- *EOS-stop:* force/monkeypatch logits so `eos_id` is the argmax at a known step; assert generation stops there and the last id != `eos_id`.

---

## Wave 0 Requirements

- [ ] `tests/test_generation.py` — stubs for GEN-01/02/03 (shape, determinism, EOS-stop, crop, sampling)
- [ ] Tiny-model fixture (in test file or `tests/conftest.py`): `GPT(ModelConfig(block_size=8, vocab_size=16, n_layer=1, n_head=1, n_embd=8, eos_id=...))` for fast CPU runs; optional fixture monkeypatching `model.forward` to return controlled logits for deterministic EOS/nucleus tests
- [ ] No framework install needed — pytest already present

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Streaming text wrapper renders clean continuation with no `<|endoftext|>` artifact / no mojibake on `best.pt` | GEN-01..03 (demo-facing, exercised in Phase 8) | Requires the real trained `best.pt` + tokenizer; out of the CPU-only fixture test scope | Load `best.pt`, stream a short prompt via the text wrapper, confirm decoded suffix is clean and EOS-terminated without the separator |

*Token-level core behaviors (shape, determinism, EOS-stop, crop, sampling) all have automated CPU verification above.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
