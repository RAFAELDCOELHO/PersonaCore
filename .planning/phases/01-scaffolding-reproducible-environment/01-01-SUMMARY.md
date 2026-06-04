---
phase: 01-scaffolding-reproducible-environment
plan: 01
subsystem: packaging + config
tags: [scaffolding, pyproject, src-layout, runtimeconfig, p100, bf16-guard]
requires: []
provides:
  - "installable `personacore` package (src-layout, PEP 621) — import parity on Kaggle/laptop/pytest (ENV-01)"
  - "`requirements.txt` + documented CPU-torch / Kaggle-no-torch workflow (ENV-02)"
  - "`RuntimeConfig` (fp32 default, AMP-off-on-CPU, bf16-raises-on-Pascal) + `ModelConfig` + `TrainConfig` dataclasses (ENV-03)"
  - "`pyproject.toml` wholly owned (ruff + pytest config) — Wave-2 plans never edit it"
affects:
  - "every downstream phase/plan imports from `personacore`"
tech-stack:
  added: [setuptools, numpy~=2.4, "torch==2.7.* ([cpu] extra only)", pytest~=9.0, ruff~=0.15]
  patterns: [src-layout, code-first dataclass config, torch-as-optional-extra]
key-files:
  created:
    - pyproject.toml
    - requirements.txt
    - .gitignore
    - src/personacore/__init__.py
    - src/personacore/config.py
    - tests/conftest.py
    - tests/test_config.py
    - tests/test_package.py
  modified: []
decisions:
  - "torch excluded from core deps; offered only as [cpu] extra (D-10) — prevents a cu128+ wheel bricking the P100"
  - "single config.py (not a config/ package) — leanest D-11-compliant layout"
  - "pyproject carries [tool.ruff] + [tool.pytest.ini_options] so Plan 03 (CI/Makefile) never edits it"
metrics:
  duration: ~9 min
  completed: 2026-06-04
---

# Phase 1 Plan 01: Scaffolding & Reproducible Environment Summary

Installable `personacore` package (src-layout, PEP 621) with torch excluded from core deps and offered only as a `[cpu]` extra, plus the code-first `RuntimeConfig`/`ModelConfig`/`TrainConfig` config layer whose `RuntimeConfig` defaults to fp32, auto-disables AMP on CPU, and raises a clear `ValueError` on bf16-over-Pascal/P100.

## What Was Built

- **Installable package (ENV-01):** `pyproject.toml` (PEP 621, setuptools, `requires-python = ">=3.10,<3.12"`) with `[tool.setuptools.packages.find] where=["src"]` src-layout discovery. `pip install -e ".[cpu,dev]"` into a clean Python 3.11 venv succeeds; `import personacore` resolves only after install (src-layout enforces install-parity).
- **Reproducible env (ENV-02):** `requirements.txt` lists `numpy~=2.4` and documents the CPU-torch index line plus the load-bearing "On Kaggle never `pip install torch`" note. `.gitignore` covers `*.egg-info/`, `*.pt`, `checkpoints/`, `logs/`, `data/`, caches, venvs.
- **Config layer (ENV-03):** `src/personacore/config.py` defines exactly three dataclasses. `RuntimeConfig` — fp32 default (`amp=False`), AMP auto-off on CPU in `__post_init__`, `_is_pascal()` guard raising `ValueError` (message names Pascal/P100 and compute capability < 7.0) when `amp_dtype="bfloat16"` on a Pascal device, and a device-agnostic `autocast()` method. `ModelConfig` (vocab_size placeholder, locked later by Phase 2) and `TrainConfig` (lr/batch/steps/warmup/grad-clip/grad-accum/weight-decay/seed).
- **Tests:** `tests/test_package.py` (import-parity smoke), `tests/test_config.py` (5 behaviors), `tests/conftest.py` (`simulate_pascal` fixture monkeypatching `torch.cuda.is_available`→True and `get_device_capability`→(6,0) so the bf16 guard is testable CPU-only).

## Tasks & Commits

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Dependency legitimacy gate (T-01-SC) | (gate — approved by developer, no commit) | — |
| 2 | Installable package scaffold | `1d1b86f` | pyproject.toml, requirements.txt, .gitignore, src/personacore/__init__.py, tests/test_package.py |
| 3 (RED) | Failing config tests | `4cc627f` | tests/conftest.py, tests/test_config.py |
| 3 (GREEN) | Config layer implementation | `09ce8d3` | src/personacore/config.py |

## Verification

- Clean Python 3.11 venv: `pip install -e ".[cpu,dev]" --extra-index-url https://download.pytorch.org/whl/cpu` exited 0 (installed torch 2.7.1 CPU, numpy 2.4.6, pytest 9.0.3, ruff 0.15.16).
- `import personacore` → `0.1.0`.
- `pytest tests/test_config.py tests/test_package.py -q` → 7 passed.
- `ruff check` + `ruff format --check` on src/ and tests/ → clean.
- pyproject: torch absent from `[project].dependencies`, present in `[cpu]` extra; `where=["src"]` and `[tool.ruff]` present.
- bf16-on-simulated-Pascal raises `ValueError`; fp32 default; AMP off on CPU — all asserted.

## Must-Haves (all satisfied)

- ✅ `pip install -e ".[cpu,dev]"` succeeds in a clean Python 3.11 venv.
- ✅ `import personacore` resolves only after install (src-layout).
- ✅ `RuntimeConfig` defaults to fp32 (amp=False).
- ✅ `RuntimeConfig` auto-disables AMP when device is cpu.
- ✅ `RuntimeConfig(amp_dtype="bfloat16")` on a Pascal/P100 device raises `ValueError`.
- ✅ `ModelConfig` and `TrainConfig` are dataclasses carrying model/training hyperparameters.
- ✅ Satisfies D-01, D-02, D-04, D-09, D-10, D-11.

## TDD Gate Compliance

Task 3 followed RED → GREEN. RED commit `4cc627f` (`test(...)`, tests failed on `ModuleNotFoundError: personacore.config`); GREEN commit `09ce8d3` (`feat(...)`, all 5 tests pass). No REFACTOR commit needed — implementation was clean on first pass (ruff green). RED gate did not pass unexpectedly (collection error as expected before implementation).

## Deviations from Plan

None — plan executed exactly as written. Task 1's blocking-human dependency-legitimacy gate (T-01-SC) was satisfied: the orchestrator surfaced the seven packages (torch, numpy, matplotlib, gradio, pytest, ruff, tqdm) to the developer, who reviewed them on PyPI and typed "approved" before any `pip install`.

## Authentication Gates

None.

## Known Stubs

`ModelConfig.vocab_size` defaults to a placeholder (50304) by design — Phase 2 (BPE tokenizer) locks the real value. Documented in code; intentional per the plan interfaces and D-11. Not a blocking stub.

## Threat Surface

No new surface beyond the plan's `<threat_model>`. T-01-SC (pip/PyPI supply chain) mitigated by the approved human-verify gate; T-01-01 (torch wheel on P100) mitigated by torch-excluded-from-core-deps; T-01-02 (bf16 on Pascal) mitigated by the `RuntimeConfig` raise; T-01-03 (build artifacts) mitigated by `.gitignore`.

## Self-Check: PASSED

Created files verified present: pyproject.toml, requirements.txt, .gitignore, src/personacore/__init__.py, src/personacore/config.py, tests/conftest.py, tests/test_config.py, tests/test_package.py.
Commits verified in git log: `1d1b86f`, `4cc627f`, `09ce8d3`.
