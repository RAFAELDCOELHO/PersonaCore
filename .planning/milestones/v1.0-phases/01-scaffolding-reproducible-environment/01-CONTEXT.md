# Phase 1: Scaffolding & Reproducible Environment - Context

**Gathered:** 2026-06-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 delivers the project skeleton everything else imports: an installable `personacore` package that imports identically on Kaggle, laptop, and pytest; a centralized, code-first config/runtime layer (fp32-default, bf16-guarded); Kaggle-survivable checkpoint/resume infrastructure (open-dict checkpoints); a GPU/P100 preflight; offline CSV logging foundations; seeds + reproducibility discipline; and `CLAUDE.md` + `requirements.txt` documenting the Kaggle-train / laptop-CPU-infer workflow.

Covers requirements **ENV-01..06** and **QA-02**.

**In scope:** package/install layout, `RuntimeConfig`/`ModelConfig`/`TrainConfig`, checkpoint save/resume skeleton, GPU preflight, seeding, logging scaffolding, dependency/env setup, dev tooling.
**Out of scope (other phases):** the BPE tokenizer (Phase 2), any model code beyond stubs (Phases 3–4), the training loop's real optimization logic (Phase 3 — Phase 1 only provides the resumable checkpoint *skeleton* and the `assemble_loss` seam shape), data download/encoding (Phase 5), generation (Phase 6). LoRA/EWC are Milestone 2.
</domain>

<decisions>
## Implementation Decisions

### Config System
- **D-01:** Config is **code-first Python dataclasses** (typed, IDE-friendly, no runtime parser). nanoGPT-style; reproducibility comes from git + recorded SHA, not config files. No YAML in Phase 1.
- **D-02:** Config is **split into three objects**: `RuntimeConfig` (device/precision — fp32 default, AMP auto-off on CPU, bf16→error on Pascal/P100), `ModelConfig` (dims, vocab_size, block_size), `TrainConfig` (lr, batch, steps, warmup/cosine, grad-clip, grad-accum). Keeps the `model/` package pure of runtime/device concerns.
- **D-03:** **Config is embedded inside the checkpoint dict** (checkpoints are open dicts — also the EWC seam). The serialized config travels with the weights as the single source of truth (satisfies QA-02). No separate sidecar config file.
- **D-04:** Hyperparameter overrides for experiments are done by **editing dataclass defaults / passing kwargs in run scripts** (git-tracked, reproducible via SHA). **CLI/argparse overrides are deferred** until the Phase 7 ablations actually need them — do NOT build a CLI config layer in Phase 1.

### Kaggle ↔ Local Code Sync
- **D-05:** **Public GitHub repo is the single source of truth.** The Kaggle notebook pulls code via `git clone` + `pip install -e`. No copy-paste, no manual upload of source.
- **D-06 (Claude discretion — "you decide"):** Default sync = **clone `main` each session and record the commit SHA** into the checkpoint/config for reproducibility; provide the **option to clone a pinned tag/SHA for the final pretraining run** so the long run is fully pinned. Implement the SHA-recording; document the pin option.
- **D-07:** **TinyStories data is provisioned as a pre-encoded `uint16` memmap, uploaded as a versioned Kaggle Dataset**, mounted read-only at train time. Phase 1 sets up the *convention/structure* for this (paths, read-only mount expectation, where the prep step will live); the actual encode/upload is Phase 5. Do not re-encode per session.
- **D-08 (Claude discretion — "you decide"):** Long Kaggle runs default to **headless "Save & Run All / Commit"** for the pretrain (checkpoint to `/kaggle/working` + persist to a Dataset), with **interactive sessions for short calibration**. Document both workflows in `CLAUDE.md`.

### Packaging & Dependencies (delegated — locked by research-backed default)
- **D-09:** **`pyproject.toml` (PEP 621)** is the installable-package source (`pip install -e .` → ENV-01). A **`requirements.txt` is also provided** for the documented venv (ENV-02 names it explicitly); keep it consistent with `pyproject`.
- **D-10:** **Torch is NEVER pinned or installed on Kaggle** — use Kaggle's preinstalled torch (Pascal-compatible wheel); locally install a CPU build. Express this so `pip install -e .` on Kaggle does not drag in a non-Pascal torch wheel (torch as an optional/markered dep or documented "install separately"). Other deps (numpy, matplotlib, gradio, pytest) use compatible-release (`~=`) ranges. Target **Python 3.10/3.11** (Kaggle-compatible).

### Scaffold Scope & Dev Tooling (delegated — locked by research-backed default)
- **D-11:** Implement **only Phase-1 modules now** under `src/personacore/` (config/runtime, checkpoint save/resume, preflight, CSV logging) + `tests/` + `scripts/`. **Future module dirs (tokenizer/model/training/generation/data/demo) are added by their own phases** — no empty stub dirs that read as "unfinished."
- **D-12:** Dev tooling = **ruff** (lint + format, single tool), **pytest**, and a **`Makefile`** with `install`/`test`/`lint`/`format` targets. Add a **minimal GitHub Actions CI** (run pytest + ruff on push) — free for the public repo and a strong portfolio signal. Keep CI lean (CPU-only, no training).

### Claude's Discretion
- **D-06** (clone-main-record-SHA vs pin-SHA) and **D-08** (headless vs interactive run launch) were explicitly delegated — defaults above; planner may refine.
- Exact `Makefile`/CI YAML, ruff rule set, and the precise `pyproject` dependency markers are left to the planner within the constraints above.
- Internal file naming within `src/personacore/` (e.g. `config.py`, `runtime.py`, `checkpoint.py`, `preflight.py`, `logging.py`) is planner's discretion, following ARCHITECTURE.md's layout.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture & Layout
- `.planning/research/ARCHITECTURE.md` — installable `src/personacore/` package layout, `RuntimeConfig`/device-AMP pattern, pure-model/stateful-trainer boundary, the two M2 seams (named `nn.Linear`; `assemble_loss` + open-dict checkpoints), dual-env (Kaggle GPU / laptop CPU) strategy, build order.
- `.planning/research/SUMMARY.md` — reconciled decisions, esp. **fp32-default training** (P100 has no Tensor Cores; AMP only if 16GB forces it; bf16 guarded), dependency-forced phase order.

### Stack & Environment
- `.planning/research/STACK.md` — P100/Pascal CUDA-wheel constraint (**never `pip install torch` on Kaggle**), Python/torch versions, offline logging (CSV + matplotlib, no wandb), Gradio 5, pytest. Prescriptive versions + what-not-to-use.
- `.planning/research/PITFALLS.md` — Kaggle ops traps (30h/wk, ~9–12h session cap, `/kaggle/working` wipe) → mandates resumable checkpoint/resume + Dataset persistence + GPU preflight; reproducibility/seeding pitfalls. Phase-mapped.

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` — ENV-01..06, QA-02 (the Phase 1 requirement set), plus the M2 seam IDs (MODEL-07, TRAIN-06) Phase 1 must keep open in the checkpoint format.
- `.planning/ROADMAP.md` §"Phase 1" — goal + 5 success criteria (install parity, RuntimeConfig+bf16-guard, kill-and-resume test, P100 preflight+seeds+SHA, CLAUDE.md+requirements.txt).
- `.planning/PROJECT.md` — Constraints (zero budget, Kaggle P100, from-scratch only, on-device) and Key Decisions.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield. No source files, no codebase maps, no prior phases. This phase creates the first code.

### Established Patterns
- `CLAUDE.md` already exists (GSD-generated); Phase 1 must extend/refresh it (ENV-06) with project structure + the Kaggle/local workflow rather than overwrite GSD guidance.

### Integration Points
- Everything downstream imports from `src/personacore/`. Phase 1 defines the import surface, the checkpoint dict schema (open dict — must accommodate the future EWC `{fisher, theta_star}` and config), and the `RuntimeConfig` contract that the Phase 3 training loop and Phase 8 CPU demo both consume.
</code_context>

<specifics>
## Specific Ideas

- nanoGPT-style code-first config (explicitly the reference mental model for D-01/D-02).
- Checkpoint as an **open dict** is load-bearing twice: resumability (ENV-04) AND the EWC seam (TRAIN-06, Milestone 2). Phase 1's checkpoint schema should be deliberately extensible.
- GitHub is public from day one → CI and tokenless `git clone` are both available and should be used.
</specifics>

<deferred>
## Deferred Ideas

- **CLI/argparse config overrides** — deferred to whenever Phase 7 ablations need them (per D-04). Not Phase 1.
- **Actual TinyStories encode + Kaggle Dataset upload** — Phase 5 (Phase 1 only establishes the path/mount convention).
- **fp16 AMP + GradScaler path** — exists as an optional memory measure (TRAIN-02, Phase 3); not exercised in Phase 1 beyond the `RuntimeConfig` toggle + bf16 guard.
- **KV-cache for CPU inference** — Milestone 2 / Phase 8 research, only if the demo feels slow.

None of the discussion strayed outside phase scope — these are natural downstream items, not scope creep.
</deferred>

---

*Phase: 1-scaffolding-reproducible-environment*
*Context gathered: 2026-06-04*
