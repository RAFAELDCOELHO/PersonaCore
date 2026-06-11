---
phase: 9
slug: lora-core
status: planned
nyquist_compliant: true
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
| 09-01-T1 | 09-01 | 1 | LORA-01 | — | B=0 identity gate; enabled/merged flags never enter state_dict | unit | `.venv/bin/pytest tests/test_lora_layer.py -q -x` | ❌ W0 (created by task, tests-first) | ⬜ pending |
| 09-01-T2 | 09-01 | 1 | LORA-01/02/05 | T-09-01, T-09-02, T-09-03 | allowlist-only injection (tied lm_head/wte never wrapped); key-audited adapter apply; lora_-only state-dict filter | unit | `.venv/bin/pytest tests/test_lora_inject.py tests/test_lora_layer.py -q -x && make test` | ❌ W0 (created by task, tests-first) | ⬜ pending |
| 09-02-T1 | 09-02 | 2 | LORA-05 | T-09-05 | toggle round-trip bit-identity; exception-safe CM; eject refuses while merged | unit | `.venv/bin/pytest tests/test_lora_toggle.py -q -x` | ❌ W0 (created by task, tests-first) | ⬜ pending |
| 09-02-T2 | 09-02 | 2 | LORA-04 | T-09-04, T-09-06 | merge eval-only (never checkpoint merged); bit-exact stored-clone unmerge; pure merged_state_dict | unit | `.venv/bin/pytest tests/test_lora_merge.py tests/test_lora_toggle.py -q -x && make test && make lint` | ❌ W0 (created by task, tests-first) | ⬜ pending |
| 09-03-T1 | 09-03 | 2 | LORA-03 | T-09-07, T-09-09, T-09-10 | weights_only=True choke point; schema-version raise; fingerprint warn-but-load; no base-weight leak | unit | `.venv/bin/pytest tests/test_lora_artifact.py -q -x` | ❌ W0 (created by task, tests-first) | ⬜ pending |
| 09-03-T2 | 09-03 | 2 | LORA-03 | T-09-08 | two-artifact load (load_slim + load_adapter + inject + key-audited apply) bit-identical | unit | `.venv/bin/pytest tests/test_lora_artifact.py -q -x && make test && make lint` | ❌ W0 (created by task, tests-first) | ⬜ pending |
| 09-04-T1 | 09-04 | 3 | LORA-02 | T-09-13 (CPU variant) | canary (≥2 effective steps) + frozen base bit-untouched + optimizer state scoped to A/B + kill+resume + lora_config **extra seam | unit | `.venv/bin/pytest tests/test_lora_training.py -q -x` | ❌ W0 (created by task, tests-first) | ⬜ pending |
| 09-04-T2 | 09-04 | 3 | LORA-02/05 | T-09-11, T-09-12, T-09-13 | real-weights canary on preflight device; trusted-only full load documented; all outputs gitignored | smoke | `.venv/bin/python scripts/train_adapter_smoke.py && git check-ignore -q checkpoints/adapter.pt logs/adapter_smoke.csv && make test` | ❌ W0 (script created by task) | ⬜ pending |

**Requirement → Test Map (from RESEARCH.md):**

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LORA-01 | B=0 zero-delta at init; A-Gaussian; α/r scale; dropout on LoRA branch, train-mode only; six projections wrapped per block via post-load injection | unit | `.venv/bin/pytest tests/test_lora_layer.py tests/test_lora_inject.py -q -x` | ❌ Wave 0 → plan 09-01 |
| LORA-02 | Grad isolation: after training steps every base param bit-untouched (`torch.equal`); canary: trainables moved; fresh-optimizer state covers only A/B | unit | `.venv/bin/pytest tests/test_lora_training.py -q -x` | ❌ Wave 0 → plan 09-04 |
| LORA-03 | Artifact round-trips `weights_only=True`; schema-version raise; fingerprint warn-but-load; two-artifact load (`load_slim`+`load_adapter`+inject) reproduces logits | unit | `.venv/bin/pytest tests/test_lora_artifact.py -q -x` | ❌ Wave 0 → plan 09-03 |
| LORA-04 | Merged forward ≡ base+adapter ≤1e-5 (CPU); unmerge bit-exact via stored clone; `merged_state_dict()` pure with vanilla-GPT key set | unit | `.venv/bin/pytest tests/test_lora_merge.py -q -x` | ❌ Wave 0 → plan 09-02 |
| LORA-05 | Enable/disable round-trip bit-identical; context manager exception-safe; eject restores vanilla; param-count = `r·n_layer·18·n_embd`; tied `data_ptr` unchanged post-injection; load→inject→freeze ordering pinned | unit | `.venv/bin/pytest tests/test_lora_toggle.py tests/test_lora_inject.py -q -x` | ❌ Wave 0 → plans 09-01/09-02 |
| LORA-02/05 (real weights) | Canary + bit-untouched on `best.pt` over TinyStories bins on MPS | smoke (script, asserts inline, non-zero exit on failure) | `.venv/bin/python scripts/train_adapter_smoke.py` | ❌ Wave 0 → plan 09-04 (local-only; CI-skipped — needs gitignored artifacts) |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Every test file is created tests-first inside its owning tdd task (no standalone Wave 0 scaffold step needed — the RED half of each tdd task IS Wave 0 for its requirement):

- [ ] `tests/test_lora_layer.py` — covers LORA-01 (init/scale/dropout/identity) — plan 09-01 Task 1
- [ ] `tests/test_lora_inject.py` — covers LORA-01/05 (allowlist, ordering, tied-tensor, param count) — plan 09-01 Task 2
- [ ] `tests/test_lora_toggle.py` — covers LORA-05 (D-05/D-06 toggle, context manager, eject) — plan 09-02 Task 1
- [ ] `tests/test_lora_merge.py` — covers LORA-04 (D-07/D-08) — plan 09-02 Task 2
- [ ] `tests/test_lora_artifact.py` — covers LORA-03 (D-01/D-02/D-03) — plan 09-03 Tasks 1-2
- [ ] `tests/test_lora_training.py` — covers LORA-02 (canary, kill+resume — adapts `test_resume_curve.py` pattern) — plan 09-04 Task 1
- Framework install: none needed (pytest present)

All unit tests use the `_tiny_config()` fixture precedent (`ModelConfig(block_size=32, n_layer=1..2, n_head=2, n_embd=16)` from `tests/test_slim_checkpoint.py`) — CPU-only, GPU-free, seconds to run. Bit-identity asserts use `torch.equal`; tolerance asserts use `torch.allclose(atol=1e-5)` on CPU.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Adapter smoke run on real weights (MPS) | LORA-02/05 | Needs gitignored artifacts (`best.pt`, TinyStories bins) and MPS device — CI-skipped, but the executor RUNS it locally as plan 09-04 Task 2's automated verify | Run `.venv/bin/python scripts/train_adapter_smoke.py`; inline asserts + non-zero exit on failure |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (every task has one)
- [x] Wave 0 covers all MISSING references (tests-first inside each tdd task)
- [x] No watch-mode flags
- [x] Feedback latency < 30s for quick runs (`-q -x` per task; full suite per wave)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** planner sign-off 2026-06-11 (plans 09-01..09-04)
