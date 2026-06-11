---
phase: 5
slug: tinystories-pretraining
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-05
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (existing; CPU-only, GPU/MPS-free suite) |
| **Config file** | none dedicated; `tests/conftest.py` + fixtures present |
| **Quick run command** | `pytest tests/test_memmap_data.py -x` |
| **Full suite command** | `make test` (CPU-only, must stay green) |
| **Estimated runtime** | ~30 seconds (CPU suite); MPS smoke runs only on the real M3 |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_memmap_data.py -x`
- **After every plan wave:** Run `make test` (full CPU suite green)
- **Before `/gsd:verify-work`:** Full CPU suite green + MPS smoke passed on the real machine + the long run produced `best.pt` with a recorded perplexity and curated coherent samples
- **Max feedback latency:** ~30 seconds (CPU); MPS smoke + long run are manual/real-hardware gates

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| memmap-roundtrip | data | 1 | PRE-01 | — | N/A | unit | `pytest tests/test_memmap_data.py::test_encode_roundtrip -x` | ❌ W0 | ⬜ pending |
| memmap-one-eos | data | 1 | PRE-01 | — | N/A | unit | `pytest tests/test_memmap_data.py::test_one_eos_between_docs -x` | ❌ W0 | ⬜ pending |
| get_batch_memmap-inbounds | data | 1 | PRE-01 | — | N/A | unit | `pytest tests/test_memmap_data.py::test_get_batch_memmap_inbounds -x` | ❌ W0 | ⬜ pending |
| no-leakage-split | data | 1 | PRE-01 | — | N/A | unit | `pytest tests/test_memmap_data.py::test_no_leakage_disjoint -x` | ❌ W0 | ⬜ pending |
| mps-finite-loss-smoke | run | 2 | PRE-02 | — | N/A | smoke (skipif no MPS) | `pytest tests/test_mps_smoke.py -x` | ❌ W0 | ⬜ pending |
| mps-overfit-one-batch | run | 2 | PRE-02 | — | N/A | smoke (skipif no MPS) | `pytest tests/test_mps_smoke.py::test_overfit_mps -x` | ❌ W0 | ⬜ pending |
| resume-memmap-bitforbit | run | 2 | PRE-02 | — | N/A | unit (CPU) | `pytest tests/test_resume_memmap.py -x` | ❌ W0 | ⬜ pending |
| best-val-loss-tracking | run | 2 | PRE-03 | — | N/A | unit (CPU) | `pytest tests/test_best_ckpt.py -x` | ❌ W0 | ⬜ pending |
| coherence+perplexity-acceptance | run | 2 | PRE-02, PRE-03 | — | N/A | manual (D-07) | manual review of `best.pt` samples + `run.csv` | manual-only | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_memmap_data.py` — round-trip, one-EOS-between-docs, in-bounds `get_batch_memmap`, no-leakage (PRE-01)
- [ ] `tests/test_mps_smoke.py` — finite-loss + overfit on MPS, `@pytest.mark.skipif(not torch.backends.mps.is_available())` (PRE-02)
- [ ] `tests/test_resume_memmap.py` — extends `test_resume_curve.py` to the memmap data source (PRE-02 resumability)
- [ ] `tests/test_best_ckpt.py` — best-val-loss tracking + perplexity (PRE-03)
- [ ] Shared fixture: `tinystories_fixture.txt` (a few `<|endoftext|>`-separated micro-stories) for deterministic, GPU-free memmap tests

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Curated coherent TinyStories-register samples + recorded perplexity figure | PRE-02, PRE-03 | Human coherence judgement (D-07) cannot be a unit test | After the long run, sample from `best.pt`; confirm grammatical, on-topic, simple narrative coherence over a few sentences; record final/val perplexity = `exp(val_loss)` and the loss/lr curves from `run.csv` |
| Full local M3/MPS long run reaches the fluency bar | PRE-02 | Multi-hour real-hardware run, not a CI test | Run the training entry script on the M3; confirm `best.pt` is produced, val loss plateaus, and resumability survives a real session kill |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s (CPU suite)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
