---
phase: 3
slug: bigram-baseline-training-harness
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-04
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest `~=9.0` (already in `pyproject.toml [project.optional-dependencies] dev`) |
| **Config file** | `pyproject.toml` → `[tool.pytest.ini_options]` (`testpaths=["tests"]`, `pythonpath=["."]`) |
| **Quick run command** | `pytest tests/test_<seam>.py -x -q` |
| **Full suite command** | `make test` (CPU-only; equivalent to `pytest`) |
| **Estimated runtime** | ~20 seconds (full CPU suite incl. inherited Phase-1/2 tests) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_<seam_just_touched>.py -x -q` (each seam test is CPU-fast, < a few seconds)
- **After every plan wave:** Run `make test` (full CPU suite, including inherited Phase-1/2 tests)
- **Before `/gsd:verify-work`:** Full suite green + the four hard-correctness gates demonstrably pass — overfit convergence (TRAIN-05), resume curve reproducibility (TRAIN-04), no train/val leakage (TRAIN-03), AMP ordering (TRAIN-02)
- **Max feedback latency:** ~20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| MODEL-01 | TBD | per-plan | MODEL-01 | — | N/A | unit | `pytest tests/test_bigram_model.py -x` | ❌ W0 | ⬜ pending |
| TRAIN-06 (loss) | TBD | per-plan | TRAIN-06 | — | N/A | unit | `pytest tests/test_assemble_loss.py -x` | ❌ W0 | ⬜ pending |
| TRAIN-01 (sched) | TBD | per-plan | TRAIN-01 | — | N/A | unit | `pytest tests/test_lr_schedule.py -x` | ❌ W0 | ⬜ pending |
| TRAIN-03 (data) | TBD | per-plan | TRAIN-03 | — | N/A | unit | `pytest tests/test_data_split.py -x` | ❌ W0 | ⬜ pending |
| TRAIN-01 (loop) | TBD | per-plan | TRAIN-01 | — | N/A | unit | `pytest tests/test_train_loop.py -x` | ❌ W0 | ⬜ pending |
| TRAIN-02 (AMP order) | TBD | per-plan | TRAIN-02 | T-V14 (trusted ckpt) | unscale_ before clip before step before update | unit | `pytest tests/test_train_loop.py::test_amp_ordering -x` | ❌ W0 | ⬜ pending |
| TRAIN-02 (fp16 smoke) | TBD | per-plan | TRAIN-02 | — | fp16 path no inf/nan | smoke (GPU) | `pytest tests/test_train_loop.py::test_amp_fp16_smoke -x` | ❌ W0 | ⬜ pending |
| TRAIN-05 (overfit) | TBD | per-plan | TRAIN-05 | — | N/A | unit | `pytest tests/test_overfit_batch.py -x` | ❌ W0 | ⬜ pending |
| TRAIN-04 (resume curve) | TBD | per-plan | TRAIN-04, TRAIN-06 | — | N/A | unit | `pytest tests/test_resume_curve.py -x` | ❌ W0 | ⬜ pending |
| TRAIN-06 (open-dict ckpt) | TBD | per-plan | TRAIN-06 | T-V14 (trusted-only load) | own-files-only checkpoint load | unit | `pytest tests/test_checkpoint.py::test_open_dict_extensible` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*
*Task IDs finalized by the planner; this map is keyed by requirement until PLAN.md files assign concrete task IDs.*

---

## Wave 0 Requirements

- [ ] `tests/fixtures/bigram_corpus.txt` — ≥2 TinyStories-style docs separated by `<|endoftext|>` (the committed D-06 fixture)
- [ ] `tests/test_bigram_model.py` — MODEL-01 (forward contract, `(logits, loss)`, shapes `(B,T,V)`, CE flatten)
- [ ] `tests/test_assemble_loss.py` — TRAIN-06 seam (identity on `()`, additive with dummy penalty; D-04a)
- [ ] `tests/test_lr_schedule.py` — TRAIN-01 schedule (warmup ramp, cosine decay to floor, `state_dict()` round-trip)
- [ ] `tests/test_data_split.py` — TRAIN-03 (doc-level split, no leakage, `get_batch` shapes/dtype/in-bounds)
- [ ] `tests/test_train_loop.py` — TRAIN-01/02 (grad-accum equivalence, AMP ordering, GPU fp16 smoke)
- [ ] `tests/test_overfit_batch.py` — TRAIN-05 (overfit one batch → loss < threshold, deterministic under seed)
- [ ] `tests/test_resume_curve.py` — TRAIN-04/06 (save→kill→resume reproduces param + loss trajectory within 1e-6; extends existing `test_checkpoint.py` pattern to bigram + LambdaLR + CSV)
- [ ] Register a `cuda`/`gpu` pytest marker OR use inline `@pytest.mark.skipif(not torch.cuda.is_available())` for the AMP fp16 smoke test (no marker currently registered in `pyproject.toml`)

*Framework install: none — `pytest~=9.0` already in `[dev]`.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real fp16-AMP path executes on GPU without inf/nan | TRAIN-02 | CI is CPU-only; the scaler short-circuits on CPU so the real fp16 path cannot run in CI | On a Pascal/P100 (or any CUDA GPU): `pytest tests/test_train_loop.py::test_amp_fp16_smoke -x` — must pass (un-skipped) |
| CSV loss curve visually reproduces across a restart | TRAIN-04 | Curve-shape eyeball is a human judgment beyond the numeric `within-1e-6` assertion | Run `scripts/train_bigram.py`, kill mid-run, resume, plot concatenated CSV with matplotlib; curve must be continuous with no discontinuity at the resume step |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
