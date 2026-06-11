# Phase 1: Scaffolding & Reproducible Environment - Research

**Researched:** 2026-06-04
**Domain:** Installable Python package scaffolding (PEP 621 / src-layout), dual-environment PyTorch device/precision config, Kaggle-survivable resumable checkpoints, reproducibility/seeding, lean CI
**Confidence:** HIGH (PEP 621 extras + setuptools src-layout verified against packaging.python.org & setuptools docs; PyTorch reproducibility API verified against PyTorch 2.12 docs; P100/Pascal wheel constraint carried verbatim from project STACK research)

## Summary

Phase 1 is pure foundational infrastructure — no model, no training math, no UI. It produces the installable `personacore` package that every later phase imports, plus the four runtime primitives that must exist *before* any long Kaggle run: a centralized `RuntimeConfig` (fp32 default, AMP off on CPU, bf16 guarded to error on Pascal), an open-dict resumable checkpoint (model+optimizer+scheduler+step+RNG), a GPU/P100 preflight, and offline CSV logging. All twelve CONTEXT decisions (D-01..D-12) are locked; this research documents *how* to implement them, not whether.

The single load-bearing packaging decision is **torch must never be a hard dependency**. On Kaggle the pre-installed Pascal-compatible torch wheel (CUDA ≤12.6, `sm_60` kernels) must stay untouched; `pip install -e .` dragging in a `cu128+` wheel would silently break GPU training. The recommended mechanism (evaluated below against markers and extras) is: **list torch in NO core dependency list; provide it only as an optional extra `[cpu]` that pins a CPU wheel for laptop/CI, and document "never install torch on Kaggle."** This is the cleanest, most explicit, and most failure-loud option.

**Primary recommendation:** src-layout package (`src/personacore/`) installed via `pip install -e .` with PEP 621 `pyproject.toml` + setuptools; torch excluded from core deps and offered as a `[cpu]` extra; an open-dict `torch.save` checkpoint with a `save_checkpoint`/`load_checkpoint` pair restoring full RNG state; a `seed_everything()` + `preflight_p100()` pair recording git SHA + config into the checkpoint; ruff + pytest + Makefile + a CPU-only GitHub Actions CI that installs `.[cpu,dev]` and runs ruff + pytest with no GPU and no training.

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Config is **code-first Python dataclasses** (typed, no runtime parser). nanoGPT-style; reproducibility from git + recorded SHA, not config files. No YAML in Phase 1.
- **D-02:** Config **split into three objects**: `RuntimeConfig` (device/precision — fp32 default, AMP auto-off on CPU, bf16→error on Pascal/P100), `ModelConfig` (dims, vocab_size, block_size), `TrainConfig` (lr, batch, steps, warmup/cosine, grad-clip, grad-accum). Keeps `model/` pure of runtime/device concerns.
- **D-03:** **Config embedded inside the checkpoint dict** (open dicts — also the EWC seam). Serialized config travels with weights as single source of truth (QA-02). No sidecar config file.
- **D-04:** Hyperparameter overrides via **editing dataclass defaults / passing kwargs in run scripts** (git-tracked). **CLI/argparse overrides deferred** to Phase 7 — do NOT build a CLI config layer in Phase 1.
- **D-05:** **Public GitHub repo is the single source of truth.** Kaggle pulls via `git clone` + `pip install -e`. No copy-paste, no manual source upload.
- **D-06 (Claude discretion):** Default sync = **clone `main` each session and record the commit SHA** into the checkpoint/config; provide the **option to clone a pinned tag/SHA for the final pretraining run**. Implement SHA-recording; document the pin option.
- **D-07:** **TinyStories data as a pre-encoded `uint16` memmap, uploaded as a versioned Kaggle Dataset**, mounted read-only. Phase 1 sets up the *convention/structure* only (paths, read-only mount expectation, where the prep step will live); actual encode/upload is Phase 5.
- **D-08 (Claude discretion):** Long Kaggle runs default to **headless "Save & Run All / Commit"** (checkpoint to `/kaggle/working` + persist to a Dataset), with **interactive sessions for short calibration**. Document both in `CLAUDE.md`.
- **D-09:** **`pyproject.toml` (PEP 621)** is the installable-package source (`pip install -e .` → ENV-01). A **`requirements.txt` is also provided** for the documented venv (ENV-02); keep it consistent with `pyproject`.
- **D-10:** **Torch is NEVER pinned or installed on Kaggle** — use Kaggle's preinstalled torch; locally install a CPU build. Express so `pip install -e .` on Kaggle does not drag in a non-Pascal torch wheel. Other deps (numpy, matplotlib, gradio, pytest) use `~=` ranges. Target **Python 3.10/3.11**.
- **D-11:** Implement **only Phase-1 modules now** under `src/personacore/` (config/runtime, checkpoint save/resume, preflight, CSV logging) + `tests/` + `scripts/`. **No empty stub dirs** for future phases.
- **D-12:** Dev tooling = **ruff** (lint + format), **pytest**, **`Makefile`** (`install`/`test`/`lint`/`format`), + a **minimal GitHub Actions CI** (pytest + ruff on push, CPU-only, no training).

### Claude's Discretion

- **D-06** (clone-main-record-SHA vs pin-SHA) and **D-08** (headless vs interactive launch) — defaults above; planner may refine.
- Exact `Makefile`/CI YAML, ruff rule set, precise `pyproject` dependency markers — planner's choice within the constraints.
- Internal file naming within `src/personacore/` (`config.py`, `runtime.py`, `checkpoint.py`, `preflight.py`, `logging.py`) — planner's discretion, following ARCHITECTURE.md.

### Deferred Ideas (OUT OF SCOPE)

- **CLI/argparse config overrides** — Phase 7 ablations only.
- **Actual TinyStories encode + Kaggle Dataset upload** — Phase 5 (Phase 1 establishes path/mount convention only).
- **fp16 AMP + GradScaler path** — Phase 3 (Phase 1 only exposes the `RuntimeConfig` toggle + bf16 guard).
- **KV-cache for CPU inference** — Milestone 2 / Phase 8.
- **Empty stub dirs** for tokenizer/model/training/generation/data/demo — each phase adds its own.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ENV-01 | Installable package (`pip install -e .`) → `personacore` imports identically on Kaggle/laptop/pytest | src-layout + PEP 621 pyproject (Standard Stack §; Pattern 1) |
| ENV-02 | Reproducible env via `requirements.txt` + documented venv; runs Kaggle P100 (train) & laptop CPU (infer) | requirements.txt + `[cpu]` extra; torch-handling decision (Don't Hand-Roll; Code Examples) |
| ENV-03 | Single `RuntimeConfig` centralizes device/precision — fp32 default, bf16 guarded to error on Pascal/P100 | RuntimeConfig pattern (Pattern 2; Code Examples §RuntimeConfig) |
| ENV-04 | Kaggle checkpoint/resume: full state (model+optimizer+scheduler+step+RNG) to `/kaggle/working`, resumes exactly after kill | Open-dict checkpoint (Pattern 3; Code Examples §Checkpoint; Validation Architecture) |
| ENV-05 | Preflight asserts Pascal-compatible CUDA active before long run; seeds set | `preflight_p100()` + `seed_everything()` (Code Examples §Preflight, §Seeding) |
| ENV-06 | `CLAUDE.md` documents structure, setup, Kaggle/local workflow | CLAUDE.md extension (Architecture Patterns §Docs; Pitfall 6) |
| QA-02 | Reproducibility: config saved with each checkpoint, seeds fixed, git SHA recorded | git SHA capture + config-in-checkpoint (Code Examples §Checkpoint, §git SHA) |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Package install / import surface | Build/Packaging (pyproject + setuptools) | — | `pip install -e .` defines the import contract; nothing runtime |
| Device + precision resolution | Config layer (`RuntimeConfig`) | — | Single source; model/ stays device-agnostic (ARCHITECTURE boundary rule) |
| Checkpoint save/resume | Training infra (`checkpoint.py`) | Storage (`/kaggle/working` + Kaggle Dataset) | Stateful; owns RNG/optimizer/step serialization |
| GPU/P100 preflight | Entry-point/script (Kaggle cell-1) | Config (reads RuntimeConfig device) | Environment assertion; must fail before any training tier runs |
| Seeding | Config/bootstrap (`seed_everything`) | — | Process-global; called once at startup, captured into checkpoint |
| Offline logging | Training infra (CSV appender) | Storage (disk, survives restart) | Append-only; consumed by Phase 8 demo.ipynb |
| Git SHA / provenance capture | Bootstrap (subprocess `git rev-parse`) | Checkpoint (embedded) | Reproducibility provenance; QA-02 |
| Lint/format/test orchestration | Dev tooling (Makefile + ruff + pytest) | CI (GitHub Actions) | Developer + CI convenience; no runtime role |

**Why this matters:** the load-bearing boundary is that **device/precision concerns live ONLY in `RuntimeConfig`** (the config tier) and never leak into model code (which arrives in Phases 3–4). Phase 1 must establish this seam correctly so later phases inherit a clean, device-agnostic model layer.

## Standard Stack

### Core (Phase 1 only)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.10 / 3.11 | Runtime target | Kaggle images + modern PyTorch target 3.11; `requires-python = ">=3.10,<3.12"` for Kaggle parity. *(Local machine here is 3.14 — see Environment Availability; CI must pin 3.11.)* `[ASSUMED for Kaggle's exact 3.11.x]` |
| setuptools | `~=80.x` (build-system) | PEP 621 build backend, src-layout discovery | De-facto standard backend; native `tool.setuptools.packages.find` src support `[CITED: setuptools.pypa.io/package_discovery]` |
| torch | Kaggle: pre-installed (untouched); Local/CI: `2.7.*` CPU wheel (or any current CPU wheel) | tensors, RNG state, `torch.save`/`load`, autocast/GradScaler types | **NOT a core dependency** — see Don't Hand-Roll. Pascal `sm_60` only in `cu126` & earlier. `[ASSUMED — verify Kaggle's torch in-notebook]` |
| ruff | `~=0.15` (latest 0.15.16) | Lint + format (single tool) | Replaces black+flake8+isort; fast; portfolio polish `[VERIFIED: pip index versions ruff → 0.15.16]` `[ASSUMED — slopcheck unavailable]` |
| pytest | `~=9.0` (latest 9.0.3; 8.x also fine) | Unit tests (first-class deliverable) | Standard; parametrized fixtures `[VERIFIED: pip index versions pytest → 9.0.3]` `[ASSUMED — slopcheck unavailable]` |

### Supporting (declared now for whole-project consistency; minimally exercised in Phase 1)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| numpy | `~=2.4` (or `>=1.26,<3`) | RNG seeding/state capture; later memmap | Phase 1 uses only `np.random` seed/state; memmap is Phase 5 |
| matplotlib | `~=3.10` | loss-curve plots (Phase 8) | Declared for env consistency; not used in Phase 1 logic |
| gradio | `~=5.0` (pin `<6`) | CPU chat demo (Phase 8) | Declared as an extra/optional; NOTE gradio 6.x now exists — pin `>=5,<6` to match STACK.md and avoid an untested major |
| tqdm | `~=4.66` | progress bars (Phases 2/3/5) | Optional; not load-bearing in Phase 1 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| setuptools backend | hatchling / flit / PDM | All support PEP 621 + src-layout; setuptools is the lowest-friction default Kaggle/CI already have. No advantage to switching for this project. |
| `[cpu]` extra for torch | environment marker `torch; platform_system!=...` | Markers can't distinguish "Kaggle GPU notebook" from "Linux laptop" — both are Linux. A marker would wrongly install torch on Kaggle. Extra is explicit and Kaggle-safe (see Don't Hand-Roll). |
| ruff | black + flake8 + isort | Three tools vs one; slower; more config. ruff is strictly simpler here. |
| `torch.save` open-dict checkpoint | safetensors | safetensors can't store optimizer/RNG/python objects and is for the *slim inference* checkpoint (Phase 8). Resume checkpoint MUST be `torch.save` open dict. |

**Installation:**
```bash
# Local laptop / CI (CPU):
pip install -e ".[cpu,dev]"      # installs CPU torch + ruff + pytest
# Kaggle notebook (NEVER install torch):
pip install -e .                 # core only — torch already present & Pascal-valid
```

**Version verification (run before finalizing pins):**
```bash
pip index versions torch ruff pytest numpy matplotlib gradio
```
Confirmed 2026-06-04: torch 2.12.0, ruff 0.15.16, pytest 9.0.3, numpy 2.4.6, matplotlib 3.10.9, gradio 6.16.0 (pin `<6`).

## Package Legitimacy Audit

> slopcheck could **not** be installed in this session (sandbox blocked the `pip install slopcheck --break-system-packages` step as supply-chain risk). Per the graceful-degradation protocol, **all packages below are tagged `[ASSUMED]`** and the planner MUST gate each install behind a `checkpoint:human-verify` task before first install. Registry existence was verified via `pip index versions` (PyPI), but registry existence alone does not confer VERIFIED status.

| Package | Registry | Latest version (verified) | Source Repo | slopcheck | Disposition |
|---------|----------|---------------------------|-------------|-----------|-------------|
| torch | PyPI | 2.12.0 | github.com/pytorch/pytorch | unavailable | `[ASSUMED]` — human-verify; Kaggle uses pre-installed |
| numpy | PyPI | 2.4.6 | github.com/numpy/numpy | unavailable | `[ASSUMED]` — human-verify |
| matplotlib | PyPI | 3.10.9 | github.com/matplotlib/matplotlib | unavailable | `[ASSUMED]` — human-verify |
| gradio | PyPI | 6.16.0 (pin `<6`) | github.com/gradio-app/gradio | unavailable | `[ASSUMED]` — human-verify; pin `>=5,<6` |
| pytest | PyPI | 9.0.3 | github.com/pytest-dev/pytest | unavailable | `[ASSUMED]` — human-verify |
| ruff | PyPI | 0.15.16 | github.com/astral-sh/ruff | unavailable | `[ASSUMED]` — human-verify |
| tqdm | PyPI | (current) | github.com/tqdm/tqdm | unavailable | `[ASSUMED]` — human-verify |

**Packages removed due to slopcheck [SLOP]:** none (slopcheck did not run).
**Packages flagged [SUS]:** none (slopcheck did not run).

*All packages are well-known, long-established projects with millions of weekly downloads and authoritative GitHub repos — but per protocol they remain `[ASSUMED]` because automated legitimacy verification was unavailable. The planner should insert a single `checkpoint:human-verify` gate covering this whole well-known set rather than seven separate gates.*

## Architecture Patterns

### System Architecture Diagram

```
                        ┌─────────────────────────────────────────┐
   git clone (records   │  ENTRY POINTS (thin, per-environment)    │
   commit SHA, D-06) ──►│  Kaggle cell-1 notebook   scripts/*.py   │
                        │  pytest (tests/)                          │
                        └───────────────┬──────────────────────────┘
                                        │ import personacore
                        ┌───────────────▼──────────────────────────┐
                        │   CONFIG LAYER (dataclasses, D-01/D-02)   │
                        │  RuntimeConfig ─► resolves device + AMP   │
                        │  (fp32 default · AMP off on CPU ·         │
                        │   bf16 RAISES on Pascal)                  │
                        │  ModelConfig · TrainConfig (serialized)   │
                        └───────┬───────────────────┬──────────────┘
                                │                   │
              ┌─────────────────▼──┐      ┌─────────▼─────────────────┐
              │  PREFLIGHT (ENV-05)│      │  BOOTSTRAP                 │
              │  assert CUDA       │      │  seed_everything(seed)     │
              │  assert P100 name  │      │  git_sha() via subprocess  │
              │  assert sm_60 ok   │      └─────────┬─────────────────┘
              │  → fail loud       │                │
              └────────────────────┘                │ seed + sha + config
                                                     ▼
                        ┌────────────────────────────────────────────┐
                        │  CHECKPOINT (ENV-04, open dict — EWC seam)  │
                        │  save: {model, optimizer, scheduler, step,  │
                        │   rng{torch,cuda,numpy,python}, config,     │
                        │   git_sha, val_loss, schema_version}        │
                        │  load: restore ALL → identical trajectory   │
                        │  (extensible: future {fisher, theta_star})  │
                        └───────────────┬────────────────────────────┘
                                        │ torch.save / torch.load(map_location)
                        ┌───────────────▼────────────────────────────┐
                        │  STORAGE                                    │
                        │  /kaggle/working/*.pt  ──persist──► Kaggle  │
                        │  Dataset (survives session wipe, D-07/D-08) │
                        │  logs/*.csv  (append-only, survives restart)│
                        └─────────────────────────────────────────────┘
```

A reader can trace: `git clone` → import package → RuntimeConfig resolves device → preflight asserts P100 → seed_everything + git_sha → (training, later phases) → checkpoint bundles full state → persisted to Dataset → resume restores exact trajectory.

### Recommended Project Structure (Phase 1 ONLY — D-11)

```
PersonaCore/
├── src/
│   └── personacore/
│       ├── __init__.py          # exposes __version__; thin
│       ├── config.py            # RuntimeConfig, ModelConfig, TrainConfig dataclasses
│       ├── runtime.py           # (optional split) device/AMP resolution helpers
│       ├── checkpoint.py        # save_checkpoint / load_checkpoint (open dict)
│       ├── preflight.py         # preflight_p100(), assert CUDA + device name + sm_60
│       ├── seeding.py           # seed_everything(), capture/restore RNG state
│       ├── provenance.py        # git_sha(), config-dict helpers (or fold into checkpoint.py)
│       └── logging.py           # CSV append logger (offline)
├── scripts/
│   └── preflight_demo.py        # thin: import personacore; run preflight + print env
├── tests/
│   ├── test_config.py           # fp32 default, AMP-off-on-CPU, bf16-guard-raises
│   ├── test_checkpoint.py       # kill-and-resume trajectory equality
│   ├── test_seeding.py          # determinism + RNG round-trip
│   └── test_preflight.py        # preflight raises on non-P100 (mocked)
├── .github/workflows/ci.yml     # CPU-only ruff + pytest on push
├── Makefile                     # install / test / lint / format
├── pyproject.toml               # PEP 621 installable; torch NOT a core dep
├── requirements.txt             # documented venv (consistent with pyproject)
├── .gitignore                   # checkpoints/, *.pt, logs/, data/, __pycache__
└── CLAUDE.md                    # extended (ENV-06): structure + Kaggle/local workflow
```

> **Do NOT create** `tokenizer/`, `model/`, `training/`, `generation/`, `data/`, `demo/` dirs (D-11). ARCHITECTURE.md shows the *eventual* full tree, but Phase 1 ships only the modules above. Internal naming (single `config.py` vs `config/` package) is planner discretion.

### Pattern 1: src-layout installable package (ENV-01 / import parity)

**What:** Code lives under `src/personacore/`; `pip install -e .` registers it on `sys.path` so `import personacore` resolves identically on Kaggle, laptop, and pytest — no `sys.path` hacks.
**When to use:** Always — this is the single most important portability decision.
**Why src-layout (not flat):** A flat layout (`personacore/` at repo root) makes `import personacore` succeed *by accident* from the repo root even without installing — which silently masks packaging bugs and breaks on Kaggle where cwd differs. src-layout forces the package to be installed to be importable, guaranteeing the install actually works everywhere. `[CITED: setuptools package_discovery — src-layout discovery via where=["src"]]`

```toml
# pyproject.toml (excerpt) — Source: setuptools.pypa.io/package_discovery + packaging.python.org
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]
```

### Pattern 2: Centralized RuntimeConfig (ENV-03)

**What:** One dataclass resolves device + AMP + dtype once. Nothing else calls `torch.cuda.is_available()`. fp32 by default; AMP auto-disabled on CPU; bf16 RAISES on Pascal.
**When to use:** Always (dual-environment linchpin).
See Code Examples §RuntimeConfig for the full implementation incl. the bf16 guard.

### Pattern 3: Self-describing open-dict checkpoint (ENV-04 / QA-02 / EWC seam)

**What:** Checkpoint is a `dict` bundling model+optimizer+scheduler+step+full-RNG+config+git_sha+schema_version — never a bare `state_dict`. Open to future keys (`fisher`, `theta_star`) without a format change.
**When to use:** Always. Essential for Kaggle→laptop transfer, 30h-quota resumability, and the M2 EWC seam.
See Code Examples §Checkpoint.

### Anti-Patterns to Avoid
- **Flat layout / importable-without-install:** masks packaging bugs; breaks on Kaggle cwd. Use src-layout.
- **torch as a hard dependency:** drags a `cu128+` wheel onto Kaggle, breaking P100. Exclude from core deps.
- **Bare `torch.save(model.state_dict())`:** no optimizer/scheduler/RNG → resume is a *fresh run from weights*, not the same trajectory. Use the open dict.
- **Scattered `.cuda()` / `is_available()`:** breaks the CPU path in a dozen places. One RuntimeConfig.
- **bf16 selectable silently:** must `raise` on Pascal, not warn.
- **Logic in Kaggle notebook cells:** untestable. All logic in `src/personacore/`; cells are ~10 lines of wiring.
- **Empty stub dirs for future phases:** reads as unfinished (D-11). Add per phase.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Make `pip install -e .` skip torch on Kaggle | A custom env-detection install script / runtime `try: import torch` shim | **torch as an optional `[cpu]` extra, absent from core `dependencies`** | Markers can't tell Kaggle-GPU from Linux-laptop (both Linux); a custom script is fragile. Extra = explicit, Kaggle-safe, fails loud if misused. |
| RNG state capture/restore | Manually pickling seed integers | `torch.get_rng_state()`, `torch.cuda.get_rng_state_all()`, `np.random.get_state()`, `random.getstate()` | These capture the *full generator state*, not just the seed — required for *exact* mid-stream resume. A re-seed restarts the stream; state capture continues it. `[CITED: PyTorch 2.12 randomness notes]` |
| Device/AMP resolution | Per-module `if cuda` branches | One `RuntimeConfig` | ARCHITECTURE boundary rule; dual-env correctness |
| Lint + format + import-sort | black + flake8 + isort wiring | ruff (one tool) | D-12; one config, one binary |
| Git SHA capture | Parsing `.git/` by hand | `subprocess.run(["git","rev-parse","HEAD"])` with a fallback when `.git` absent (e.g. Kaggle Dataset copy) | Standard, robust; handle the no-git case gracefully (record `"unknown"`) |
| Checkpoint serialization | Custom binary format | `torch.save` (open dict) for resume; `safetensors` for slim inference (Phase 8) | torch.save preserves optimizer/RNG/python objects; safetensors can't and is for the *separate* inference artifact |

**Key insight:** the torch-handling problem *looks* like it needs an environment marker, but markers operate on platform/python attributes that **cannot distinguish Kaggle from a Linux laptop**. The correct, verified-safe solution is to make torch a *non-default extra* and document the Kaggle "never install torch" rule — pushing the decision to an explicit human/CI action rather than an automatic (and wrong) marker evaluation.

## Common Pitfalls

### Pitfall 1: `pip install -e .` pulls a non-Pascal torch wheel onto Kaggle
**What goes wrong:** torch listed in core `dependencies` → on Kaggle, `pip install -e .` reinstalls/upgrades torch to a `cu128+` wheel that dropped Pascal `sm_60` kernels → CUDA ops crash or fall back; the P100 is effectively bricked for this project.
**Why it happens:** torch *feels* like a core dependency. It is, but the install must be environment-controlled.
**How to avoid:** Exclude torch from `[project.dependencies]`. Provide a `[cpu]` extra for laptop/CI. Document: **on Kaggle run `pip install -e .` (no extras) — never `pip install torch`.** Add a preflight assertion that the *running* torch is Pascal-capable.
**Warning signs:** `torch.cuda.get_device_name()` errors; "no kernel image available for execution on the device"; CUDA ops silently slow (CPU fallback).

### Pitfall 2: Resume restarts the RNG stream instead of continuing it (ENV-04 silently fails)
**What goes wrong:** On resume the code calls `seed_everything(seed)` again instead of restoring captured RNG *state*. The next-step loss diverges from the uninterrupted trajectory even though weights loaded — the kill-and-resume test fails (or, worse, isn't written and the divergence ships).
**Why it happens:** Re-seeding feels equivalent to restoring; it isn't — it rewinds the generator to step 0, not to step N.
**How to avoid:** Capture `torch/cuda/numpy/python` generator state into the checkpoint at save; `set_*_state` on load. Seed once at the *start of a fresh run only*; on resume, restore state instead. Test: train N steps → snapshot → "kill" → restore → assert the next step's loss/params are bit-identical (or within fp tolerance) to an uninterrupted run.
**Warning signs:** resumed loss curve has a visible discontinuity at the resume step; "same seed" runs differ after a resume.

### Pitfall 3: Determinism flags forgotten → "reproducible" runs aren't
**What goes wrong:** Only `torch.manual_seed` is set; cuDNN autotuner (`benchmark=True`) and nondeterministic kernels make GPU runs differ run-to-run.
**Why it happens:** Seeding the python-visible RNG feels sufficient; GPU nondeterminism is invisible until two runs diverge.
**How to avoid:** In `seed_everything`: seed `random`, `numpy`, `torch`, `torch.cuda` (all devices); set `torch.backends.cudnn.benchmark=False`. Offer an optional strict mode (`torch.use_deterministic_algorithms(True)` + `cudnn.deterministic=True` + `CUBLAS_WORKSPACE_CONFIG=:4096:8`) but document its **speed cost** — for a portfolio run, logging the seed + git SHA + config is the *primary* reproducibility guarantee; full bitwise GPU determinism is optional and slower. `[CITED: PyTorch 2.12 randomness notes — "Deterministic operations are often slower"]`
**Warning signs:** two "identical" runs give different loss curves; the writeup's numbers can't be regenerated.

### Pitfall 4: `git rev-parse` fails on Kaggle Dataset copies (no `.git`)
**What goes wrong:** Provenance capture crashes when the code was copied (not cloned) and `.git` is absent.
**Why it happens:** D-05 default is `git clone` (so `.git` exists), but the pin-tag option or a Dataset-bundled copy may lack it.
**How to avoid:** Wrap `git rev-parse` in try/except; on failure record `git_sha="unknown"` (or read an env var the notebook sets). Never let provenance capture abort training.
**Warning signs:** training script dies at startup with a CalledProcessError from git.

### Pitfall 5: `torch.load` of a checkpoint without `map_location` / `weights_only`
**What goes wrong:** A CUDA-saved checkpoint fails to load on a CPU laptop (device mismatch), or `weights_only` default changes bite across torch versions.
**Why it happens:** Tested only on the P100.
**How to avoid:** Always `torch.load(path, map_location="cpu")` for the resume/load helper's portability; for the *slim inference* checkpoint (Phase 8) use `weights_only=True`. The Phase-1 *resume* checkpoint contains optimizer/RNG objects, so it loads with default (full) pickle from a trusted own-file — document that it is trusted-only.
**Warning signs:** `RuntimeError: Attempting to deserialize object on a CUDA device` on the laptop.

## Code Examples

> All examples are illustrative scaffolding patterns. The bf16-guard and RNG-state APIs are verified; treat dataclass field choices as a starting point for the planner.

### RuntimeConfig (ENV-03) — fp32 default, AMP off on CPU, bf16 raises on Pascal
```python
# Source: derived from ARCHITECTURE.md Pattern 1 + PyTorch torch.amp device-agnostic API
import torch
from dataclasses import dataclass

def _is_pascal(device: str) -> bool:
    if not device.startswith("cuda") or not torch.cuda.is_available():
        return False
    major, _ = torch.cuda.get_device_capability(0)   # P100 -> (6, 0)
    return major < 7                                  # <7.0 => no bf16, no Tensor Cores

@dataclass
class RuntimeConfig:
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    amp: bool = False           # fp32 DEFAULT (decision: SUMMARY.md fp32-default)
    amp_dtype: str = "float16"  # P100 path is fp16 (NEVER bf16); toggled on in Phase 3

    def __post_init__(self):
        if self.device == "cpu":
            self.amp = False                      # AMP auto-off on CPU
        if self.amp_dtype == "bfloat16" and _is_pascal(self.device):
            raise ValueError(
                "bf16 is unsupported on Pascal/P100 (compute capability < 7.0). "
                "Use fp32 (default) or fp16 AMP."
            )

    def autocast(self):
        return torch.autocast(
            device_type=self.device.split(":")[0],
            dtype=getattr(torch, self.amp_dtype),
            enabled=self.amp,
        )
```

### Open-dict resumable checkpoint (ENV-04 / QA-02 / EWC seam)
```python
# Source: ARCHITECTURE.md Pattern 4 + PyTorch RNG-state API (verified)
import random, numpy as np, torch
from dataclasses import asdict

CKPT_SCHEMA_VERSION = 1

def save_checkpoint(path, *, model, optimizer, scheduler, step, model_config,
                    train_config, git_sha, val_loss=None):
    ckpt = {
        "schema_version": CKPT_SCHEMA_VERSION,
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scheduler": scheduler.state_dict() if scheduler is not None else None,
        "step": step,
        "val_loss": val_loss,
        "model_config": asdict(model_config),     # config travels WITH weights (QA-02)
        "train_config": asdict(train_config),
        "git_sha": git_sha,                        # provenance (QA-02)
        "rng": {
            "python": random.getstate(),
            "numpy": np.random.get_state(),
            "torch": torch.get_rng_state(),
            "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
        },
        # OPEN DICT: M2 may add "fisher" / "theta_star" here with no format change.
    }
    torch.save(ckpt, path)

def load_checkpoint(path, *, model, optimizer=None, scheduler=None, map_location="cpu"):
    ckpt = torch.load(path, map_location=map_location)  # trusted own-file (has pickled state)
    model.load_state_dict(ckpt["model"])
    if optimizer is not None and ckpt.get("optimizer") is not None:
        optimizer.load_state_dict(ckpt["optimizer"])
    if scheduler is not None and ckpt.get("scheduler") is not None:
        scheduler.load_state_dict(ckpt["scheduler"])
    rng = ckpt["rng"]                              # RESTORE state -> continue same stream
    random.setstate(rng["python"])
    np.random.set_state(rng["numpy"])
    torch.set_rng_state(rng["torch"])
    if rng["cuda"] is not None and torch.cuda.is_available():
        torch.cuda.set_rng_state_all(rng["cuda"])
    return ckpt                                    # caller reads step / configs / git_sha
```

### Seeding (ENV-05) — seed everything for a FRESH run
```python
# Source: PyTorch 2.12 randomness notes (verified)
import os, random, numpy as np, torch

def seed_everything(seed: int, *, strict: bool = False):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)               # seeds CPU + (if present) CUDA
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    if strict:                            # full determinism — SLOWER; optional
        torch.use_deterministic_algorithms(True)
        torch.backends.cudnn.deterministic = True
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
```

### Git SHA / provenance (QA-02)
```python
import subprocess
def git_sha(default: str = "unknown") -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:                     # no .git (Kaggle Dataset copy) -> don't crash
        return default
```

### Kaggle P100 preflight (ENV-05)
```python
# Source: PITFALLS.md Pitfall 15 + STACK.md P100 constraint
import torch
def preflight_p100(require_p100: bool = True):
    assert torch.cuda.is_available(), "CUDA not available — set Kaggle accelerator to GPU P100."
    name = torch.cuda.get_device_name(0)
    major, minor = torch.cuda.get_device_capability(0)
    print(f"[preflight] device={name} cc={major}.{minor} torch={torch.__version__}")
    if require_p100 and "P100" not in name:
        raise RuntimeError(f"Expected Tesla P100, got '{name}'. Refusing to start a long run.")
    # Pascal kernels present? a tiny CUDA op smoke-tests the installed wheel:
    try:
        _ = (torch.ones(8, device="cuda") * 2).sum().item()
    except RuntimeError as e:
        raise RuntimeError(
            "CUDA op failed — installed torch may lack Pascal sm_60 kernels "
            "(cu128+ wheel?). On Kaggle, do NOT reinstall torch."
        ) from e
    return {"device": name, "cc": (major, minor), "torch": torch.__version__}
```

### pyproject.toml — torch excluded from core deps, offered as `[cpu]` extra (D-09/D-10)
```toml
# Source: PEP 621 (packaging.python.org/writing-pyproject-toml) + setuptools src-layout
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[project]
name = "personacore"
version = "0.1.0"
requires-python = ">=3.10,<3.12"   # Kaggle 3.11 parity
dependencies = [                   # NOTE: torch is deliberately ABSENT
  "numpy~=2.4",
]

[project.optional-dependencies]
cpu = [                            # laptop + CI: pin a CPU torch wheel
  "torch==2.7.*",                  # any current CPU wheel works; pin for reproducibility
]
demo = ["gradio>=5,<6", "matplotlib~=3.10"]
dev  = ["pytest~=9.0", "ruff~=0.15"]

[tool.setuptools.packages.find]
where = ["src"]
```
> For the CPU torch wheel locally/CI, install with the CPU index:
> `pip install -e ".[cpu,dev]" --extra-index-url https://download.pytorch.org/whl/cpu`

### GitHub Actions CI (D-12) — CPU-only, ruff + pytest, no GPU, no training
```yaml
# Source: standard GitHub Actions Python CI pattern
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"      # match Kaggle target, not the 3.14 dev box
      - name: Install (CPU torch + dev)
        run: |
          pip install --upgrade pip
          pip install -e ".[cpu,dev]" --extra-index-url https://download.pytorch.org/whl/cpu
      - name: Lint
        run: ruff check . && ruff format --check .
      - name: Test
        run: pytest -q          # tests must not require a GPU
```
> Action versions (`checkout@v4`, `setup-python@v5`) are `[ASSUMED]` — verify current major tags at planning time.

### Makefile (D-12)
```makefile
install:  ; pip install -e ".[cpu,dev]" --extra-index-url https://download.pytorch.org/whl/cpu
test:     ; pytest -q
lint:     ; ruff check . && ruff format --check .
format:   ; ruff format . && ruff check --fix .
.PHONY: install test lint format
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `setup.py` + `setup.cfg` | PEP 621 `pyproject.toml` `[project]` table | PEP 621 (2020), now default | Single declarative file; D-09 |
| `torch.cuda.amp.autocast` / `GradScaler` | device-agnostic `torch.autocast(device_type=...)` / `torch.amp.GradScaler` | PyTorch 2.x | Same loop runs CPU/GPU; used in RuntimeConfig |
| black + flake8 + isort | ruff (single tool) | 2023→ | One binary, one config; D-12 |
| Pascal in all CUDA wheels | `sm_60` only in `cu126` & earlier (`cu128+` dropped it) | PyTorch 2.8 / CUDA 13 | **The load-bearing P100 constraint** — never reinstall torch on Kaggle |
| Re-seed on resume | capture/restore full generator state | always-correct practice | Exact trajectory resume (ENV-04) |

**Deprecated/outdated:**
- `setup.py`-only packaging: superseded by PEP 621 (still works, but D-09 mandates pyproject).
- `torch.cuda.amp.*`: superseded by device-agnostic `torch.amp.*` / `torch.autocast`.

## Runtime State Inventory

> Phase 1 is **greenfield scaffolding** — no rename/refactor/migration. This section is included for completeness with explicit "none" findings.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no datastores exist yet (TinyStories Dataset is Phase 5). | None — verified: repo contains only CLAUDE.md + .planning/. |
| Live service config | None — no external services. Kaggle Dataset/notebook config is *created* by later phases, not renamed here. | None. |
| OS-registered state | None — no scheduled tasks, daemons, or registrations. | None. |
| Secrets/env vars | None Phase-1-owned. `CUBLAS_WORKSPACE_CONFIG` is set *by code* in optional strict mode, not a stored secret. No Kaggle token handling in Phase 1. | None. |
| Build artifacts | None yet. After `pip install -e .` an `src/personacore.egg-info/` appears — gitignore it. | Add `*.egg-info/` to `.gitignore`. |

## Validation Architecture

> `nyquist_validation: true` in config — this section drives the Nyquist validation strategy.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 (8.x acceptable) `[VERIFIED: pytest --version → 9.0.3]` |
| Config file | none yet — Wave 0 adds `[tool.pytest.ini_options]` to `pyproject.toml` (or omit; defaults suffice) |
| Quick run command | `pytest -q` |
| Full suite command | `pytest -q` (whole suite is fast, CPU-only) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ENV-01 | `pip install -e .` then `import personacore` succeeds (install parity) | integration | `pip install -e ".[cpu,dev]" && python -c "import personacore"` (also implicitly via CI) | ❌ Wave 0 (CI job) |
| ENV-03 | RuntimeConfig defaults to fp32 (amp False) | unit | `pytest tests/test_config.py::test_fp32_default -x` | ❌ Wave 0 |
| ENV-03 | AMP auto-off on CPU device | unit | `pytest tests/test_config.py::test_amp_off_on_cpu -x` | ❌ Wave 0 |
| ENV-03 | bf16 on Pascal RAISES (mock capability <7.0) | unit | `pytest tests/test_config.py::test_bf16_raises_on_pascal -x` | ❌ Wave 0 |
| ENV-04 | kill-and-resume restores model+opt+sched+step+RNG → identical next-step trajectory | unit | `pytest tests/test_checkpoint.py::test_resume_identical_trajectory -x` | ❌ Wave 0 |
| ENV-04 | checkpoint is an open dict (extra keys round-trip; schema_version present) | unit | `pytest tests/test_checkpoint.py::test_open_dict_extensible -x` | ❌ Wave 0 |
| ENV-05 | `seed_everything` → two seeded draws identical; RNG state round-trips | unit | `pytest tests/test_seeding.py::test_determinism -x` | ❌ Wave 0 |
| ENV-05 | preflight raises on non-P100 device name (mocked) | unit | `pytest tests/test_preflight.py::test_rejects_non_p100 -x` | ❌ Wave 0 |
| QA-02 | `git_sha()` returns a SHA (or "unknown" without .git) and lands in the checkpoint dict | unit | `pytest tests/test_checkpoint.py::test_records_git_sha -x` | ❌ Wave 0 |
| ENV-06 | CLAUDE.md documents structure + Kaggle/local workflow | manual-only | reviewer check (no automated test — doc content) | n/a |

### Sampling Rate
- **Per task commit:** `pytest -q` (full suite is seconds; no GPU)
- **Per wave merge:** `pytest -q` + `ruff check . && ruff format --check .`
- **Phase gate:** full suite green + CI green on GitHub before `/gsd:verify-work`.

### Key validation design notes
- **Kill-and-resume test (the critical one, ENV-04):** use a tiny stand-in module (e.g. a 1–2 layer `nn.Linear` toy or the bigram isn't built yet, so a trivial `nn.Linear`) + AdamW + a scheduler. Train N steps → `save_checkpoint` → construct a *fresh* model/opt/sched → `load_checkpoint` → run one more step on both an uninterrupted reference and the resumed copy → assert next-step loss (and a sampled param) are equal within `1e-6`. This proves *trajectory* equality, not just "weights loaded." Run entirely on CPU.
- **bf16 guard test:** monkeypatch `torch.cuda.get_device_capability` to return `(6, 0)` and `is_available`→True, assert `RuntimeConfig(device="cuda", amp_dtype="bfloat16")` raises `ValueError`. No GPU needed.
- **Preflight test:** monkeypatch `torch.cuda.get_device_name`→`"Tesla T4"`, assert `RuntimeError`. No GPU needed.
- All Phase-1 tests are **CPU-only and GPU-free** so CI runs them.

### Wave 0 Gaps
- [ ] `tests/test_config.py` — ENV-03 (fp32 default, AMP-off-CPU, bf16-raises)
- [ ] `tests/test_checkpoint.py` — ENV-04 / QA-02 (resume trajectory, open dict, git SHA)
- [ ] `tests/test_seeding.py` — ENV-05 (determinism, RNG round-trip)
- [ ] `tests/test_preflight.py` — ENV-05 (rejects non-P100, mocked)
- [ ] `.github/workflows/ci.yml` — ENV-01 install-parity smoke + ruff + pytest
- [ ] pytest is already installed locally (9.0.3); CI installs it via `.[dev]`.

## Security Domain

> `security_enforcement` not set in config → enabled by default. Phase 1 is offline, on-device, no network/DB/auth surface — most categories N/A, but checkpoint deserialization is a real concern.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth surface in Phase 1 |
| V3 Session Management | no | No sessions |
| V4 Access Control | no | No multi-user/network access |
| V5 Input Validation | partial | Validate config values (e.g. bf16-on-Pascal → raise); preflight asserts device |
| V6 Cryptography | no | No crypto; never hand-roll any |
| V14 Configuration | yes | `.gitignore` checkpoints/secrets; never commit Kaggle API tokens (use Kaggle Secrets) |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| `torch.load` arbitrary-code-exec via pickle | Tampering / Elevation | Resume checkpoint loaded only from *own trusted files*; the **slim inference** checkpoint (Phase 8) uses `weights_only=True`. Document the resume file as trusted-only. |
| Committed Kaggle API token / credentials | Information Disclosure | Use Kaggle Secrets / env vars; `.gitignore` covers tokens; never hardcode in notebook (PITFALLS Security table) |
| Supply-chain (slopsquatted dep) | Tampering | All deps are long-established with authoritative repos; planner inserts a `checkpoint:human-verify` gate (slopcheck was unavailable — Package Legitimacy Audit) |

## Environment Availability

| Dependency | Required By | Available (this dev box) | Version | Fallback |
|------------|------------|--------------------------|---------|----------|
| Python | everything | ✓ | **3.14.4** (⚠ project targets 3.10/3.11) | Use a 3.11 venv locally; CI pins 3.11 — do NOT develop/test only on 3.14 |
| pip | install | ✓ | 26.1 | — |
| pytest | tests | ✓ | 9.0.3 | — |
| git | provenance / clone | ✓ | 2.50.1 | `git_sha()` returns "unknown" if `.git` absent |
| make | Makefile targets | ✓ | GNU Make 3.81 | run commands directly |
| ruff | lint/format | ✗ not installed | — | `pip install -e ".[dev]"` installs it |
| torch (CPU) | local tests touching RNG/checkpoint | ✗ not installed locally | — | install via `.[cpu]` extra; **slopcheck unavailable → human-verify before install** |

**Missing dependencies with no fallback:** none blocking — all installable via the `[cpu,dev]` extras.

**Notable risk:** the dev box runs **Python 3.14**, but the project targets **3.10/3.11 for Kaggle parity**. torch CPU wheels and Kaggle's image may not support 3.14. **The planner should mandate a 3.11 virtual environment for local dev/test and pin `python-version: "3.11"` in CI** so install-parity (ENV-01) is actually validated against the Kaggle target, not the local 3.14 interpreter.

## Project Constraints (from CLAUDE.md)

CLAUDE.md is currently the GSD-generated baseline (PROJECT/STACK/workflow sections) — no custom coding directives beyond the GSD workflow gate and the STACK prescriptions already captured above. Actionable constraints relevant to Phase 1:

- **GSD workflow gate:** file edits must go through a GSD command (execute-phase). The planner's tasks will run under `/gsd-execute-phase` — compliant by construction.
- **STACK prescriptions (in CLAUDE.md):** never `pip install torch` on Kaggle; CPU torch pin locally; offline CSV+matplotlib logging (no wandb); from-scratch ethos (no HF model code). All honored by this research.
- **ENV-06 makes CLAUDE.md a Phase-1 deliverable:** the phase must *extend* CLAUDE.md (project structure + Kaggle-train/laptop-infer workflow + both run modes from D-08) rather than overwrite the GSD-generated sections.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | All packages are legitimate (slopcheck could not run — sandbox-blocked) | Package Legitimacy Audit | LOW — all are household-name libs; planner gates with one human-verify checkpoint |
| A2 | Kaggle's pre-installed torch is Pascal-compatible (`sm_60`) and stays so | Standard Stack / Pitfall 1 | HIGH if wrong — but mitigated by the preflight CUDA smoke-test; verify `torch.__version__` in cell-1 each session |
| A3 | Kaggle image / CPU torch wheels support Python 3.11 (not 3.14) | Environment Availability | MEDIUM — pin 3.11 in venv + CI to be safe; do not rely on the local 3.14 box |
| A4 | `torch==2.7.*` CPU wheel is a good reproducible local pin | pyproject example | LOW — any current CPU wheel works on CPU; pin is for reproducibility, easily bumped |
| A5 | GitHub Actions `checkout@v4` / `setup-python@v5` are current major tags | CI example | LOW — verify tags at planning; cosmetic |
| A6 | An optional `[cpu]` extra is the cleanest torch-exclusion mechanism (vs marker) | Don't Hand-Roll | LOW — verified that markers can't distinguish Kaggle from Linux laptop; extra is the safe choice |
| A7 | gradio 6.x exists but project pins `<6` per STACK.md | Standard Stack | LOW — gradio is Phase 8; only declared as an extra here |

## Open Questions (RESOLVED)

1. **Single `config.py` vs a `config/` sub-package?**
   - What we know: D-02 mandates three dataclasses; ARCHITECTURE shows a `config/` package eventually.
   - What's unclear: Phase 1 alone could use one `config.py`.
   - **RESOLVED:** single `config.py` (leanest D-11-compliant layout) alongside `checkpoint.py` / `preflight.py` / `seeding.py` / `logging.py`; split to a `config/` package only if it grows. Adopted by Plan 01-01.

2. **Does the kill-and-resume test need a real model, or a toy `nn.Linear`?**
   - What we know: the bigram/GPT don't exist until Phases 3–4.
   - What's unclear: whether to test resume against a trivial stand-in now.
   - **RESOLVED:** test against a toy `nn.Linear` + AdamW + scheduler now (proves the checkpoint machinery); Phase 3 re-validates against the real loop. Satisfies ENV-04's "skeleton in place" intent. Adopted by Plan 01-02 Task 1.

3. **Strict (bitwise) determinism on by default?**
   - What we know: full determinism is slower (PyTorch docs); the portfolio guarantee is seed+SHA+config.
   - **RESOLVED:** default `strict=False`; expose a `strict=True` toggle; document the trade-off in CLAUDE.md. Adopted by Plan 01-02 Task 1.

## Sources

### Primary (HIGH confidence)
- [PyTorch 2.12 reproducibility notes](https://docs.pytorch.org/docs/2.12/notes/randomness.html) — `manual_seed`, `use_deterministic_algorithms`, `cudnn.benchmark/deterministic`, "deterministic ops are slower" trade-off (verified)
- [packaging.python.org — Writing pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) — PEP 621 `[project]`, `optional-dependencies`, `requires-python`, build-system (verified)
- [packaging.python.org — Dependency specifiers (PEP 508)](https://packaging.python.org/en/latest/specifications/dependency-specifiers/) — environment markers semantics (verified the marker-can't-distinguish-Kaggle reasoning)
- [setuptools — Package Discovery](https://setuptools.pypa.io/en/latest/userguide/package_discovery.html) — `tool.setuptools.packages.find` with `where = ["src"]` for src-layout (verified)
- Project research: `.planning/research/STACK.md` (P100/Pascal `cu126`-vs-`cu128+` wheel constraint, version pins, offline logging), `.planning/research/ARCHITECTURE.md` (RuntimeConfig/AMP pattern, open-dict checkpoint Pattern 4, M2 seams), `.planning/research/PITFALLS.md` (Pitfalls 10/14/15/16, security table), `.planning/research/SUMMARY.md` (fp32-default reconciliation)

### Secondary (MEDIUM confidence)
- PyPI version checks via `pip index versions` (2026-06-04): torch 2.12.0, ruff 0.15.16, pytest 9.0.3, numpy 2.4.6, matplotlib 3.10.9, gradio 6.16.0
- `pip index versions` registry-existence verification for all listed packages (slopcheck unavailable → all `[ASSUMED]`)

### Tertiary (LOW confidence)
- GitHub Actions action tag currency (`checkout@v4`, `setup-python@v5`) — verify at planning
- Kaggle's exact pre-installed torch version/Python on the P100 image — verify in-notebook (cell-1 preflight prints it)

## Metadata

**Confidence breakdown:**
- Standard stack / packaging: HIGH — PEP 621 + setuptools src-layout + torch-exclusion mechanism verified against authoritative docs; P100 constraint carried from verified STACK research.
- Architecture (RuntimeConfig, open-dict checkpoint, seeding): HIGH — patterns verified against PyTorch 2.12 docs and project ARCHITECTURE research.
- Pitfalls: HIGH — drawn from verified PITFALLS research + PyTorch reproducibility notes.
- Package legitimacy: LOW automated confidence (slopcheck sandbox-blocked) → all deps `[ASSUMED]`, planner gates with human-verify.

**Research date:** 2026-06-04
**Valid until:** 2026-07-04 (stable domain — packaging/PyTorch APIs move slowly; the P100 wheel constraint is the only fast-moving fact and is already pinned).
