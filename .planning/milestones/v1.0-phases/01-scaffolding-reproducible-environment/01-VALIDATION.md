---
phase: 1
slug: scaffolding-reproducible-environment
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-04
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `01-RESEARCH.md` § Validation Architecture. Per-task rows are filled by the planner/executor.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (CPU-only; no GPU/torch-cuda needed) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (Wave 0 establishes) |
| **Quick run command** | `pytest -q` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~5–15 seconds (toy `nn.Linear`; no training, no GPU) |

---

## Sampling Rate

- **After every task commit:** Run `pytest -q`
- **After every plan wave:** Run `pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| (filled by planner) | — | — | ENV-01..06 / QA-02 | — | N/A (offline library, no untrusted input) | unit | `pytest -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Validation strategy per success criterion (from RESEARCH § Validation Architecture)

1. **Install parity (ENV-01/02):** `pip install -e .` into a clean Python 3.11 venv, then assert `import personacore` resolves and `python -c "import personacore"` exits 0. src-layout guarantees import only works post-install (catches accidental flat-import reliance). CI repeats this on a fresh runner.
2. **RuntimeConfig precision/bf16 guard (ENV-03):** unit test — fp32 is default; AMP auto-off on CPU; requesting bf16 on a simulated Pascal capability `(6,0)` raises `ValueError`. Testable on CPU via monkeypatch of `torch.cuda.get_device_capability` — no GPU required.
3. **Kill-and-resume trajectory equality (ENV-04, QA-02):** train a toy `nn.Linear` N steps, snapshot the open-dict checkpoint (model+optimizer+scheduler+step+RNG *state*), "kill", load, continue; assert the post-resume next-step loss/params are bitwise-identical to an uninterrupted run. Asserts RNG *state* restore (not re-seed) and embedded-config round-trip.
4. **Preflight (ENV-05):** unit test the assertion logic — passes when CUDA + `Tesla P100` reported, fails loudly otherwise; CPU-testable via monkeypatched device name/availability. (The live Kaggle cell-1 assert is a manual-only observation, below.)
5. **Seed + git SHA + config capture (ENV-05, QA-02):** test that seeding sets `random`/`numpy`/`torch`(+cuda) and that a saved checkpoint embeds the config and the recorded git SHA.

---

## Wave 0 Requirements

- [ ] `pyproject.toml` `[tool.pytest.ini_options]` + ruff config — test runner + lint config
- [ ] `tests/conftest.py` — shared fixtures (tmp checkpoint dir, monkeypatch helpers for device capability/name)
- [ ] `tests/test_config.py` — RuntimeConfig/ModelConfig/TrainConfig + bf16 guard (ENV-03)
- [ ] `tests/test_checkpoint.py` — kill-and-resume trajectory equality (ENV-04, QA-02)
- [ ] `tests/test_preflight.py` — preflight pass/fail logic (ENV-05)
- [ ] `tests/test_package.py` — `import personacore` parity / install smoke (ENV-01)
- [ ] pytest install (CPU-only) — framework not yet present in a greenfield repo

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live Kaggle cell-1 preflight asserts a real Tesla P100 + Pascal-capable CUDA | ENV-05 | Requires the actual Kaggle P100 runtime; cannot run in CI/CPU | On Kaggle (GPU on): run the preflight cell; confirm it prints P100 + passes, and fails loudly when GPU is off |
| `git clone` + `pip install -e .` works on a real Kaggle notebook without pulling a non-Pascal torch wheel | ENV-01/02 | Depends on Kaggle's preinstalled torch image | On Kaggle: clone repo, `pip install -e .` (no torch reinstall), assert `torch.__version__` unchanged + `import personacore` works |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
