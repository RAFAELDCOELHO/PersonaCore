# Phase 1: Scaffolding & Reproducible Environment - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-04
**Phase:** 1-scaffolding-reproducible-environment
**Areas discussed:** Config system shape, Kaggle ↔ local code sync
**Areas delegated to Claude defaults:** Packaging & dependencies, Scaffold scope & dev tooling

---

## Gray Area Selection

| Option | Description | Selected |
|--------|-------------|----------|
| Packaging & dependencies | pyproject vs requirements.txt, pinning, Python version | |
| Config system shape | dataclasses vs YAML vs hybrid; structure; persistence; overrides | ✓ |
| Kaggle ↔ local code sync | how the package reaches Kaggle and stays in sync | ✓ |
| Scaffold scope & dev tooling | stub all dirs vs Phase-1 only; ruff/pytest/Makefile/CI | |

**User's choice:** Config system shape, Kaggle ↔ local code sync

---

## Config System Shape

### Q: How should configuration be represented?
| Option | Description | Selected |
|--------|-------------|----------|
| Python dataclasses (code-first) | Typed dataclasses, no parser, serializable, nanoGPT-style | ✓ |
| Dataclasses + optional YAML override | Dataclass defaults overridable by YAML/CLI | |
| YAML files | Configs as .yaml loaded at runtime | |

### Q: How should the config objects be structured?
| Option | Description | Selected |
|--------|-------------|----------|
| Split: Runtime / Model / Train | Separate RuntimeConfig / ModelConfig / TrainConfig | ✓ |
| Single flat Config | One object holding everything | |
| You decide | Claude picks the split | |

### Q: Where is the config saved (QA-02)?
| Option | Description | Selected |
|--------|-------------|----------|
| Embed config in the checkpoint dict | Stored alongside model/optimizer/step in the open-dict checkpoint | ✓ |
| Embed + sidecar file | Embedded plus a human-readable sidecar | |
| Separate file only | Written beside the .pt | |

### Q: How are hyperparameters tweaked for experiments?
| Option | Description | Selected |
|--------|-------------|----------|
| Edit defaults / pass kwargs in scripts | Git-tracked code edits, reproducible via SHA | ✓ |
| CLI flags (argparse) now | Command-line overrides built up front | |
| You decide | Minimal now, CLI when ablations need it | |

**Notes:** CLI overrides explicitly deferred to the Phase 7 ablations rather than built in Phase 1.

---

## Kaggle ↔ Local Code Sync

### Q: Will the repo live on GitHub, public or private?
| Option | Description | Selected |
|--------|-------------|----------|
| Public GitHub from the start | Tokenless git clone on Kaggle; GitHub is source of truth | ✓ |
| Private during dev, public at launch | Needs token/secret or Dataset push until public | |
| No GitHub yet / local-only | Dataset-push only | |

### Q: How should the notebook pull code while staying reproducible?
| Option | Description | Selected |
|--------|-------------|----------|
| Clone latest main, record the SHA | Clone main + pip install -e, log commit SHA | |
| Clone a pinned tag/SHA per run | Checkout explicit tag/SHA per long run | |
| You decide | Default clone-main + record SHA, option to pin for final run | ✓ |

### Q: How should TinyStories data be provisioned on Kaggle?
| Option | Description | Selected |
|--------|-------------|----------|
| Pre-encoded memmap as a Kaggle Dataset | Encode once, upload versioned uint16 .bin, mount read-only | ✓ |
| Download raw + encode each session | Fetch + tokenize at session start | |
| You decide | Default to pre-encoded Dataset | |

### Q: How should long Kaggle runs be launched?
| Option | Description | Selected |
|--------|-------------|----------|
| Save & Run All / Commit (headless) | Headless run to completion + Dataset persistence | |
| Interactive + resume after kills | Interactive with resumable checkpoints | |
| You decide | Default headless for pretrain, interactive for calibration | ✓ |

**Notes:** Phase 1 establishes the data-mount convention only; the actual encode/upload is Phase 5.

---

## Claude's Discretion

- Code-sync reproducibility strategy (clone-main + record-SHA, with optional pinned-SHA for the final pretrain run) — D-06.
- Long-run launch mode (headless commit for pretrain, interactive for short calibration) — D-08.
- Packaging & dependencies area (delegated): pyproject.toml + requirements.txt, torch never pinned/overridden on Kaggle, `~=` ranges, Python 3.10/3.11 — D-09, D-10.
- Scaffold scope & tooling area (delegated): Phase-1 modules only (no future stub dirs), ruff + pytest + Makefile + minimal GitHub Actions CI — D-11, D-12.
- Internal file naming, exact ruff rule set, Makefile/CI YAML, and pyproject dependency markers.

## Deferred Ideas

- CLI/argparse config overrides → Phase 7 (ablations).
- TinyStories encode + Kaggle Dataset upload → Phase 5.
- fp16 AMP + GradScaler exercise → Phase 3 (RuntimeConfig toggle exists in Phase 1).
- KV-cache for CPU inference → Milestone 2 / Phase 8 (only if demo is slow).
