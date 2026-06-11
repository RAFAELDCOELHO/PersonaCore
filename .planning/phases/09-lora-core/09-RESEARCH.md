# Phase 9: LoRA Core - Research

**Researched:** 2026-06-11
**Domain:** From-scratch LoRA adapters (PyTorch composition wrapper, post-load injection, frozen-base training, safe-load adapter artifact) on the shipped v1.0 13.9M-param GPT
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Adapter artifact contract**
- **D-01:** The adapter artifact loads under `weights_only=True` with its own
  `ADAPTER_SCHEMA_VERSION`, through a `load_adapter()` choke point mirroring `load_slim`
  (`src/personacore/checkpoint.py`). The persona file is the artifact designed to be
  swapped/shared — it meets the same safe-load bar as `model_slim.pt`. Contents: A/B tensors +
  primitive metadata only.
- **D-02:** The artifact records a **base fingerprint** — the base checkpoint's `git_sha` +
  `step` (the existing QA-02 provenance trio). On loading onto a mismatched base: **warn but
  load** (not a hard error) — the base evolves mid-milestone (Phase-9 smoke adapters train on
  `best.pt`; Phase-14 adapters on the Phase-12 conversational base).
- **D-03:** "Compatible with the slim contract" (LORA-03) = **two-artifact load**:
  `load_slim(model_slim.pt)` + `load_adapter(adapter.pt)` + inject. No merged-slim export in
  Phase 9 (deferred — see Deferred Ideas). `merge()` still ships per LORA-04 as a tested
  utility.
- **D-04:** Adapter training gets **full open-dict kill+resume**: it runs through the existing
  `save_checkpoint`/`load_checkpoint` discipline (optimizer + RNG state for A/B params;
  `lora_config` rides the `**extra` seam). The final adapter exports separately via the safe
  artifact (D-01).

**Toggle & merge semantics**
- **D-05:** Disable = **flag-gated delta branch**: `LoRALinear` carries an `enabled` flag;
  forward always computes the wrapped base Linear and adds `scale·B(A(x))` only when enabled.
  Disabled means the delta branch is never executed (not zeroed) — bit-identity to base is
  structural and the live Gradio toggle is instant. **Plus** a separate `eject()` utility that
  restores the original `nn.Linear` modules for full wrapper removal ("Reset = drop adapter =
  instant forget" path).
- **D-06:** Model-level API in `lora/inject.py`: `set_adapter_enabled(model, bool)` and
  `eject_adapter(model)` helper functions **plus** a `with adapter_disabled(model):` context
  manager (exception-safe re-enable) for scoped base-vs-adapter comparisons in tests and
  Phase 14's scripted recall protocol.
- **D-07:** Unmerge is **bit-exact via stored copy**: `merge()` clones W₀ before adding
  `scale·B@A`; `unmerge()` copies the clone back. Round-trip is bit-identical — consistent with
  the project's bit-exactness culture (resume, toggle, defaults). Memory cost trivial at 13.9M.
- **D-08:** `merge()` ships in **both forms**: in-place `merge(model)`/`unmerge(model)` on the
  injected model (the object LORA-04's forward-equivalence test exercises) AND a pure
  `merged_state_dict()` function (no mutation) returning a plain-GPT state dict with
  `W₀ + scale·B@A` folded in — the building block for Phase 15's ΔW heatmaps and the deferred
  merged-slim export.

### Claude's Discretion
The user delegated two surfaced gray areas to Claude/planner judgment, guided by the research
docs (`.planning/research/ARCHITECTURE.md`, `PITFALLS.md`):

- **LoRA config surface & defaults** — where rank/alpha/dropout live (a `LoRAConfig` dataclass
  following the `ModelConfig` pattern is the natural shape), smoke defaults (research implies
  r=8 → ~1.3 MB adapter), alpha convention, and how the config travels (research: `lora_config`
  rides the open-dict `**extra`; D-01 requires it as primitive metadata in the adapter artifact
  too).
- **Frozen-base training integration** — how freezing is enforced against the untouched v1.0
  `train()` (`requires_grad=False` + optimizer over trainable params only is the standard
  shape), the smoke-run substrate (TinyStories bins at `best.pt` — the only data existing in
  Phase 9), and script-vs-test packaging of the params-actually-update canary.

Also Claude's discretion: dropout placement (standard LoRA: on x before A, train-mode only),
exact file/module naming within the `lora/` package, and test-suite organization.

### Deferred Ideas (OUT OF SCOPE)
- **Merged-slim export path** (`merge()` → `export_slim` single plain-GPT state dict): deferred
  until a phase actually needs it — research floated it for Phase 14 shipping. Phase 9's
  `merged_state_dict()` (D-08) lands as its building block, so wiring it later is trivial.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LORA-01 | From-scratch `LoRALinear` (A-Gaussian/B-zero init, α/r scaling, configurable rank/alpha/dropout) wraps the six named `nn.Linear` projections via post-load injection — no HF PEFT | Pattern 1 (composition wrapper, verified seam code in `gpt.py:71-74,120-121`); Pattern 2 (injection via `named_modules()` + parent `setattr`, six-name allowlist); LoRAConfig recommendation (discretion resolved) |
| LORA-02 | Frozen-base training discipline — gradients flow only to A/B; base params bit-untouched (test-verified) | Pattern 3 (freeze via `requires_grad_(False)` + untouched `train()` — AdamW frozen-param behavior **empirically verified in the project venv**, torch 2.7.1); canary packaging recommendation |
| LORA-03 | Adapter weights save/load as a separate small artifact, compatible with open-dict checkpoints and the LOCKED `weights_only=True` slim contract | Pattern 4 (artifact schema, `ADAPTER_SCHEMA_VERSION`, fingerprint warn-but-load — **`weights_only=True` round-trip of the exact proposed schema verified empirically**); two-artifact load flow (D-03) |
| LORA-04 | `merge()`/unmerge utility with fp32-tolerance equivalence test (merged forward ≡ base+adapter); demo path always stays unmerged | Pattern 5 (merge/unmerge with stored-clone bit-exact restore per D-07, `merged` flag short-circuit, `merged_state_dict()` per D-08, ≤1e-5 CPU tolerance per PITFALLS P3) |
| LORA-05 | Correctness unit tests pin: zero-delta at init, enable/disable round-trip bit-identical to base, param-count formula, tied-embedding safety (`data_ptr` test post-injection) | Test-suite map (Validation Architecture); param-count closed form `r·n_layer·18·n_embd = 331,776` at defaults — **arithmetic verified**; existing test idioms identified (`test_gpt_weight_tying.py`, `test_gpt_param_count.py`, `test_slim_checkpoint.py`) |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Python 3.11 venv MANDATORY** — dev box system Python is 3.14 (unsupported target); develop/test only inside `.venv` (verified present: Python 3.11.15). CI pins 3.11.
- **PyTorch only, from scratch** — no HF PEFT / transformers model code; `torch==2.7.*` pinned locally (verified: 2.7.1 in venv). LoRA is a hand-rolled deliverable.
- **Primary training = local Apple Silicon (M3/MPS), fp32, no AMP** — no `GradScaler`, no `torch.compile` on MPS. Correctness tests are **CPU-only, GPU-free**.
- **GSD workflow enforcement** — work starts through GSD commands; planning artifacts stay in sync.
- **Memory must live in weights only** — the adapter artifact's safe-load bar and provenance are part of the privacy narrative, not just engineering.
- **Never commit checkpoints/tokens/logs** — `.gitignore` covers them; smoke-run adapter artifacts land in gitignored `checkpoints/`.
- **Thin scripts, logic in package** — `scripts/` entry points carry no logic (`export_slim.py` precedent: no-CLI, `_REPO_ROOT` constants, `main()`).
- **`make test` = `pytest -q`; `make lint` = `ruff check . && ruff format --check .`** (line-length 100, rules E/F/W/I).
- **Purity rule:** `model/gpt.py` is NEVER edited (phase boundary re-states this); all LoRA machinery lives in a new `lora/` package; changes to existing modules are additive and default-off — all existing tests stay green.

## Summary

Phase 9 is the highest-confidence phase of v2.0: pure unit-testable math with zero data/training dependencies, paper-canonical mechanics (Hu et al. 2021), and a v1.0 codebase whose seams were explicitly built for it and verified line-by-line by the milestone research (`.planning/research/ARCHITECTURE.md`, today's date). The six named `nn.Linear` projections exist exactly as pinned (`gpt.py:71-74` for `q_proj/k_proj/v_proj/c_proj`, `gpt.py:120-121` for `fc_in/fc_out`; `tests/test_gpt_lora_seam.py` is the structural gate). The tied `lm_head.weight = wte.weight` single-tensor (`gpt.py:184`, `data_ptr`-pinned by `test_gpt_weight_tying.py`) is the one landmine — it must never be wrapped, enforced by an explicit six-name allowlist (never a class-based `isinstance(m, nn.Linear)` scan, which would pick up `lm_head`).

This research resolved the two Claude's-discretion areas with empirical verification in the project's own pinned environment (torch 2.7.1, Python 3.11.15 venv): (1) **LoRA config surface** — a `LoRAConfig` dataclass (`r=8, alpha=16.0, dropout=0.0, targets=<six names>`) following the `ModelConfig` pattern, with `scale = alpha/r` computed once on `LoRALinear` as the single source of truth for both forward and merge; the config travels as `asdict()` primitives both into `save_checkpoint(**extra)` and into the adapter artifact. (2) **Frozen-base training** — the untouched v1.0 `train()` is safe as-is: I verified empirically that `AdamW(model.parameters(), weight_decay>0)` leaves `requires_grad=False` params **bit-untouched** (no step, no decoupled weight decay — the per-param loop skips `grad is None` entirely) and that optimizer state holds entries only for stepped params, so kill+resume of adapter training works through the existing checkpoint discipline with deterministic reconstruction order (vanilla → inject → freeze → optimizer → `load_checkpoint`). The proposed adapter-artifact schema (tensors + nested primitive containers including a tuple of target names) was round-tripped through `torch.load(weights_only=True)` successfully, and the param-count closed form `r·n_layer·18·n_embd` = 331,776 at defaults (≈1.3 MB fp32) was verified arithmetically against the layer shapes.

**Primary recommendation:** Build `lora/` as three small modules (`config.py`, `layer.py`, `inject.py`) plus `export_adapter`/`load_adapter` added to `checkpoint.py` beside the slim pair; keep `train()` and `model/gpt.py` byte-untouched; pin every success criterion with a CPU-only test using the `_tiny_config()` fixture precedent, and prove the real-weights path with a thin gitignored smoke script on `best.pt` + TinyStories bins.

## Architectural Responsibility Map

| Capability | Primary Owner | Secondary | Rationale |
|------------|---------------|-----------|-----------|
| LoRA math (A/B params, scale, dropout, `enabled` flag, per-module merge/unmerge state) | `lora/layer.py` (`LoRALinear`) | — | Self-contained, unit-testable composition wrapper; the explicit forward IS the portfolio deliverable |
| Config surface (`r`, `alpha`, `dropout`, `targets`) + canonical six-name allowlist | `lora/config.py` (`LoRAConfig`, `TARGET_PROJECTIONS`) | rides `save_checkpoint(**extra)` as primitives | Follows `ModelConfig` dataclass house pattern; tests cross-pin the allowlist against the seam test |
| Injection / freeze / toggle / eject / model-level merge / adapter key filtering | `lora/inject.py` | — | Model-level orchestration over `named_modules()` + parent `setattr`; Phase 14's consumption surface (D-06) |
| Adapter artifact I/O (`export_adapter`/`load_adapter`, `ADAPTER_SCHEMA_VERSION`) | `src/personacore/checkpoint.py` | — | D-01 locks the choke point mirroring `load_slim`; keeps ALL artifact I/O + schema versions in one module; takes plain dicts so `checkpoint.py` never imports `lora/` |
| Adapter training (optimizer, schedule, kill+resume, CSV) | existing `training/loop.py::train()` — **untouched** | `scripts/train_adapter_smoke.py` (thin driver) | Verified: AdamW + `clip_grad_norm_` skip frozen params; resume discipline inherited for free (D-04) |
| Correctness proof (all 5 success criteria) | `tests/test_lora_*.py` (CPU-only) | smoke script asserts canary on real weights | House discipline: correctness on CPU; MPS is a performance backend |

## Standard Stack

### Core

**Zero new dependencies.** Phase 9 is implemented entirely with the pinned v1.0 environment. [VERIFIED: imported and version-checked in the project venv this session]

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| torch | 2.7.1 (pinned `2.7.*`) | `nn.Module`, `nn.Parameter`, matmul, `torch.save/load(weights_only=True)`, AdamW | Already pinned; CLAUDE.md locked. MPS available on this machine (verified) |
| numpy | 2.4.6 (pinned `~=2.4`) | memmap bins for the smoke run | Already pinned |
| pytest | ~=9.0 (dev extra) | The phase's main deliverable is its test suite | Already pinned; `make test` = `pytest -q` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `dataclasses` (stdlib) | — | `LoRAConfig` + `asdict()` for primitive metadata | Config travels into `**extra` and the artifact |
| `warnings` (stdlib) | — | D-02 fingerprint mismatch warn-but-load | `load_adapter` |
| `contextlib` (stdlib) | — | `adapter_disabled()` context manager (D-06) | Exception-safe scoped disable |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hand-rolled `LoRALinear` | HF PEFT / loralib / `torch.nn.utils.parametrize` | **Banned by design** (REQUIREMENTS Out of Scope; CONTEXT established patterns). The explicit wrapper IS the deliverable |
| `torch.save` + `weights_only=True` artifact | `safetensors` | D-01 locks mirroring the `load_slim` pattern (torch.save + restricted unpickler). safetensors stays a CLAUDE.md option for shippable weights, not this artifact |
| Classic `α/r` scaling | rsLoRA `α/√r` | rsLoRA matters at high rank; at r=4–16 classic is fine (PITFALLS P3). Pick classic, pin it, record convention in the artifact |

**Installation:** nothing to install. `make install` only if the venv is broken (memory note: worktree agents have broken the editable install before — symptom is mass `ModuleNotFoundError` at pytest collection; fix by re-pointing the editable install, not by code changes).

## Package Legitimacy Audit

**No external packages are installed in this phase.** All code uses the already-pinned, already-installed v1.0 environment (torch 2.7.1 / numpy 2.4.6 / pytest, verified importable in `.venv` this session). slopcheck run: not applicable — there is nothing to install.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
                    TWO-ARTIFACT LOAD PATH (D-03)                    TRAINING PATH (D-04)
                    ─────────────────────────────                    ────────────────────
 model_slim.pt ──► load_slim() ──► vanilla GPT          best.pt ──► load_checkpoint() ──► vanilla GPT
 (weights_only=True)                  │                 (full, trusted)                       │
                                      ▼                                                      ▼
 adapter.pt ──► load_adapter() ─► inject_lora(model, LoRAConfig)   ◄── SAME injection function
 (weights_only=True,│                 │  walks named_modules(), parent-setattr's LoRALinear
  ADAPTER_SCHEMA_   │                 │  onto the SIX allowlisted names per block ONLY
  VERSION check,    │                 ▼  (lm_head/wte NEVER wrapped — tied tensor)
  fingerprint warn) │        injected GPT: blocks[i].attn.{q,k,v,c}_proj + mlp.{fc_in,fc_out}
                    │         each = LoRALinear(base=frozen nn.Linear, lora_A, lora_B,
                    │                           scale=α/r, enabled=True, merged=False)
                    ▼                 │
        load A/B tensors into         ├──► mark_only_lora_trainable() ──► train()  [UNTOUCHED v1.0]
        injected modules (key-        │      requires_grad_(False) all,      AdamW(model.parameters())
        audited, then load)           │      re-enable lora_A/lora_B         skips grad-None params
                                      │                                      (VERIFIED) → kill+resume
        FORWARD (per wrapped module): │                                      via save/load_checkpoint;
        y = base(x)                   │                                      lora_config in **extra
        if enabled and not merged:    │
            y += scale·(dropout(x) @ Aᵀ @ Bᵀ)        ──► export_adapter() ──► adapter.pt
                                      │                   (filtered lora_ keys + asdict(config)
        TOGGLE/MERGE UTILITIES:       │                    + base fingerprint {git_sha, step})
        set_adapter_enabled(m, b) ────┤
        with adapter_disabled(m): ────┤   merge(m): clone W₀ → W += scale·B@A → merged=True
        eject_adapter(m) ─────────────┤   unmerge(m): copy clone back (BIT-EXACT, D-07)
                                      └─► merged_state_dict(m): pure fold → plain-GPT keys (D-08)
```

### Recommended Project Structure (Phase-9 additions only)

```
src/personacore/
├── lora/                      # NEW package — the from-scratch LoRA deliverable
│   ├── __init__.py            # re-exports: LoRAConfig, LoRALinear, inject_lora, ...
│   ├── config.py              # LoRAConfig dataclass + TARGET_PROJECTIONS canonical allowlist
│   ├── layer.py               # LoRALinear (composition wrapper; ~80 lines)
│   └── inject.py              # inject_lora / mark_only_lora_trainable / set_adapter_enabled /
│                              #   adapter_disabled / eject_adapter / merge_lora / unmerge_lora /
│                              #   merged_state_dict / lora_state_dict / snapshot_params (canary)
├── checkpoint.py              # MODIFIED (additive): +ADAPTER_SCHEMA_VERSION, +export_adapter,
│                              #   +load_adapter — beside the slim pair, same choke-point style
scripts/
└── train_adapter_smoke.py     # NEW thin driver: best.pt → inject → freeze → ~100 steps on
                               #   TinyStories bins → canary + bit-untouched asserts → adapter.pt
tests/
├── test_lora_layer.py         # B=0 identity, scale math, dropout placement, contiguity
├── test_lora_inject.py        # six wrapped/block, allowlist cross-pin, tied data_ptr, ordering, param count
├── test_lora_toggle.py        # enable/disable bit-identity, context-manager exception safety, eject
├── test_lora_merge.py         # merge-equivalence ≤1e-5 CPU, unmerge bit-exact, merged_state_dict pure
├── test_lora_artifact.py      # weights_only=True round-trip, schema raise, fingerprint warn, 2-artifact load
└── test_lora_training.py      # canary, base-bit-untouched after steps, fresh-optimizer state, kill+resume
```

(File/test naming is Claude's discretion per CONTEXT; this layout extends the converged
`layer.py + inject.py` shape from `.planning/research/SUMMARY.md` with one tiny `config.py`,
mirroring how `ModelConfig` lives in its own config module.)

### Pattern 1: `LoRALinear` composition wrapper (LORA-01)

**What:** A plain `nn.Module` that owns the frozen base `nn.Linear` and the A/B parameters. Explicit math, no inheritance, no parametrize magic.

**Design decisions (resolving discretion, consistent with locked decisions):**
- `lora_A`: shape `(r, in_features)`, init `nn.init.normal_(std=0.02)` — Gaussian per LORA-01's "A-Gaussian"; std 0.02 matches the house init in `gpt.py:_init_weights`. (Note: Hu et al.'s paper text says "random Gaussian"; the official loralib code uses kaiming-uniform — the requirement pins Gaussian, and since B=0 forces ΔW=0 at init, A's std affects only early training dynamics, not correctness.) [CITED: arXiv:2106.09685 §4.1; ASSUMED: std choice — low risk]
- `lora_B`: shape `(out_features, r)`, init zeros — the identity gate (PITFALLS P2).
- Create A/B as **fresh tensors with explicit shapes** (`torch.zeros(out, r)`, `torch.empty(r, in)` then `normal_`), never derived from `weight.T` views — eliminates the MPS non-contiguous silent-freeze bug class at the root (PITFALLS P5). Fresh tensors are contiguous by construction; an explicit `.contiguous()` assert in a test is cheap insurance.
- `self.scale = alpha / r` computed once in `__init__` — the **single source of truth** read by both forward and merge (PITFALLS P3: kills double-scaling, missing-scaling, and convention drift in one move).
- `self.enabled = True` and `self.merged = False` as plain Python bool attributes — NOT buffers/Parameters, so they never enter `state_dict()` and cannot pollute checkpoints or the artifact.
- `self.dropout = nn.Dropout(dropout)` applied to `x` on the LoRA branch only, before A (standard LoRA placement; `nn.Dropout` handles train/eval mode automatically). Default `dropout=0.0`.
- Forward: `y = self.base(x); if self.enabled and not self.merged: y = y + self.scale * (self.dropout(x) @ self.lora_A.T @ self.lora_B.T)`. The `not self.merged` guard prevents double-counting after `merge()` (delta is already folded into `base.weight`).
- State-dict keys after wrapping: `…q_proj.base.weight`, `…q_proj.base.bias`, `…q_proj.lora_A`, `…q_proj.lora_B` — the `.base.` infix is why injection MUST happen after loading (Pattern 2).

**When to use:** every wrapped projection. Six per block × 6 blocks = 36 wrappers.

### Pattern 2: Post-load injection with explicit allowlist (LORA-01, LORA-05)

**What:** `inject_lora(model, config)` walks `model.named_modules()`, and for each `Block` parent, replaces exactly the allowlisted child names via `setattr(parent, name, LoRALinear(child, ...))`.

**Load-order discipline (load-bearing — `.planning/research/ARCHITECTURE.md` Pattern 1):**
```python
model = GPT(ModelConfig(**ckpt["model_config"]))   # vanilla — keys match best.pt verbatim
model.load_state_dict(ckpt["model"])               # base weights in, zero key gymnastics
inject_lora(model, lora_config)                    # AFTER load — keys now grow .base. infix
mark_only_lora_trainable(model)                    # freeze base, enable A/B
```
Wrapping before loading breaks every checkpoint key (`q_proj.weight` → `q_proj.base.weight`) — pin with a test that loads real-shaped weights and asserts post-injection logits identity.

**Allowlist, never class scan (PITFALLS P1):** the canonical tuple `("q_proj","k_proj","v_proj","c_proj","fc_in","fc_out")` lives in `lora/config.py` as `TARGET_PROJECTIONS`. A class-based `isinstance(m, nn.Linear)` scan would pick up `lm_head` — the tied tensor (`lm_head.weight IS wte.weight`, same `data_ptr`, `gpt.py:184`) — and corrupt input embeddings on merge (the documented HF PEFT bug family, issues #2018/#2777/#2864). Production code must not import from `tests/`; instead add a cross-pin test asserting `TARGET_PROJECTIONS == test_gpt_lora_seam.PROJECTIONS`.

**Post-injection safety asserts (test-pinned per LORA-05):** `model.lm_head.weight.data_ptr() == model.wte.weight.data_ptr()` still holds; `lm_head`/`wte` are not `LoRALinear`; trainable-param census equals the closed form below.

**Param-count closed form** [VERIFIED: arithmetic checked against layer shapes this session]:
- Per block: q/k/v/c_proj are (384→384) → 4·r·768; fc_in (384→1536) and fc_out (1536→384) → 2·r·1920. Total = 6912·r per block.
- Whole model: `r · n_layer · 18 · n_embd` = 8 · 6 · 18 · 384 = **331,776** trainable params at defaults ≈ **1.33 MB fp32** — the "~1.3 MB persona file" from CONTEXT.

### Pattern 3: Frozen-base training through the untouched v1.0 `train()` (LORA-02)

**What:** `mark_only_lora_trainable(model)` = `model.requires_grad_(False)` then `p.requires_grad_(True)` for every param whose name contains `lora_`. Then call the existing `train(model=injected_model, train_bin=…, …)` with **zero loop changes**.

**Why this is safe — empirically verified in the project venv (torch 2.7.1) this session:**
- `AdamW(model.parameters(), weight_decay=0.5)` after one step left a frozen param **bit-untouched** (`torch.equal` vs pre-step snapshot) — the per-param loop skips `grad is None` params entirely, so neither moments nor decoupled weight decay are applied. [VERIFIED: empirical check in project venv]
- `torch.nn.utils.clip_grad_norm_` tolerates None-grad params. [VERIFIED: same check]
- `opt.state` held entries **only for the stepped param** — no state bloat for the 13.9M frozen params, and resume re-association is deterministic because the construction order (vanilla → inject → freeze → `AdamW(model.parameters())` → `load_checkpoint`) is identical on resume. [VERIFIED: same check]

This resolves the apparent tension between PITFALLS P4 ("optimizer over trainable params only") and ARCHITECTURE ("existing train() safe as-is"): with `train()` untouched, `AdamW(model.parameters())` IS effectively an optimizer over trainable params — frozen params receive no grads, no steps, no decay, no state. The discipline is then **proven empirically** by the canary rather than assumed structurally, which fits the project's test culture.

**Adapter-run TrainConfig:** set `weight_decay=0.0` (decaying A/B fights the low-rank update — standard practice, per `.planning/research/ARCHITECTURE.md` freeze-discipline note). Fresh optimizer always — never load pretrain optimizer state into an adapter run (PITFALLS P4); `train()` already constructs a fresh AdamW per call, so this holds by construction unless `resume_from` points at a pretrain checkpoint (don't).

**Kill+resume (D-04):** `save_checkpoint(..., lora_config=asdict(cfg))` from inside `train()` works verbatim — the injected model's `state_dict()` (with `.base.`/`lora_` keys) rides the open dict; `**extra` carries `lora_config`. Resume = rebuild vanilla GPT from `ckpt["model_config"]` → `inject_lora` from `ckpt["lora_config"]` → freeze → `train(resume_from=…)`. Note `train()` saves `lora_config` only if the caller threads it — the smoke script must pass it via the checkpoint save path. **Caveat for the planner:** `train()`'s internal `save_checkpoint` calls do not forward arbitrary extras; the smoke script should save the post-run adapter checkpoint itself (or the planner adds an additive `checkpoint_extra: dict | None = None` kwarg to `train()` — additive and default-off, consistent with house style; either is acceptable, the script-side save is zero-touch).

**Canary packaging (discretion resolved):** implement `snapshot_params(model) -> dict[str, Tensor]` (name → detached clone) as a tiny pure helper in `lora/inject.py`; the canary assertion (every trainable changed, every frozen bit-identical after ≥1 step) is then ~5 lines reused by (a) `tests/test_lora_training.py` on a tiny-config GPT (CI-safe, CPU) and (b) `scripts/train_adapter_smoke.py` on the real `best.pt` + MPS — where the MPS silent-failure class it exists to catch actually lives (PITFALLS P5).

**Smoke-run substrate:** `best.pt` + `data/train.bin`/`val.bin` all exist locally (verified). ~50–100 steps, batch small, `weight_decay=0.0`, new CSV path (never append to `run.csv` — anti-pattern 3 in ARCHITECTURE research). Outputs (checkpoint, adapter.pt, CSV) are gitignored.

### Pattern 4: Adapter artifact through the `checkpoint.py` choke point (LORA-03, D-01/D-02/D-03)

**What:** `export_adapter(path, *, adapter, lora_config, base_fingerprint)` and `load_adapter(path)` in `src/personacore/checkpoint.py`, beside `export_slim`/`load_slim`, with `ADAPTER_SCHEMA_VERSION = 1` beside `SLIM_SCHEMA_VERSION`.

**Schema** [VERIFIED: this exact shape round-trips `torch.load(weights_only=True)` in the project venv — tensors + nested dicts/tuples of primitives are all accepted by the restricted unpickler]:
```python
{
  "schema_version": 1,                                  # ADAPTER_SCHEMA_VERSION
  "adapter": {"blocks.0.attn.q_proj.lora_A": Tensor, "blocks.0.attn.q_proj.lora_B": Tensor, ...},
  "lora_config": {"r": 8, "alpha": 16.0, "dropout": 0.0, "targets": ["q_proj", ...]},  # asdict()
  "base_fingerprint": {"git_sha": "<sha>", "step": 5000, "val_loss": 0.7378},          # D-02
}
```
- `lora_state_dict(model)` (in `lora/inject.py`) produces the `adapter` dict by filtering `model.state_dict()` for keys containing `"lora_"` — base weights never leak into the persona file.
- `checkpoint.py` takes plain dicts and never imports `lora/` — dependency direction stays clean (mirrors how `export_slim` takes a path, not a model).
- `load_adapter` validates `schema_version` (raise `ValueError` on mismatch — verbatim `load_slim` style) and compares `base_fingerprint` against the loaded base's provenance: **`warnings.warn` but proceed** on mismatch (D-02 — base evolves mid-milestone).
- Applying the adapter: after `inject_lora`, assert the artifact's key set **exactly equals** `{k for k in model.state_dict() if "lora_" in k}`, then load (key-audited `load_state_dict(..., strict=False)` is acceptable ONLY behind that assert — PITFALLS P4 bans *bare* `strict=False`). Recommend a `load_adapter_weights(model, artifact)` helper in `lora/inject.py` owning the audit.
- Two-artifact load (D-03): `load_slim(model_slim.pt)` → rebuild GPT from embedded config → `inject_lora` from artifact's `lora_config` → key-audited adapter load. Test end-to-end: logits equal to the injected-and-trained model that exported the artifact.

### Pattern 5: Merge/unmerge with bit-exact restore (LORA-04, D-07/D-08)

**What:**
- Per-module: `merge()` — `assert not self.merged`; `self._w0 = self.base.weight.detach().clone()` (lazy, created at merge time, plain attribute so it never enters `state_dict`); `self.base.weight.data.add_(self.scale * (self.lora_B @ self.lora_A))` under `torch.no_grad()`; `self.merged = True`. Shapes check out: `(out,r) @ (r,in) = (out,in)` = `base.weight.shape`.
- `unmerge()` — `self.base.weight.data.copy_(self._w0)`; `self.merged = False`; drop `_w0`. **Bit-exact by construction** (stored copy, not subtraction — D-07; float subtraction would NOT round-trip bit-exactly).
- Model-level `merge_lora(model)`/`unmerge_lora(model)` in `inject.py` iterate the wrapped modules.
- `merged_state_dict(model)` — **pure, no mutation** (D-08): builds a plain-GPT state dict mapping `*.base.weight` → `*.weight` (+ bias) with `scale·B@A` added for wrapped weights, dropping `lora_A`/`lora_B`, passing everything else through. Assert the resulting key set equals a vanilla `GPT(config).state_dict()` key set. This is Phase 15's ΔW building block and the deferred merged-slim hook.

**Tolerance discipline:** merged forward ≡ unmerged (base+adapter) within `atol ≤ 1e-5`, **on CPU** (MPS reductions are not bit-stable — CONTEXT/house rule). Unmerge round-trip and toggle round-trip use `torch.equal` (bit-identity). The fp32-tolerance is forced by `W₀ + scale·B@A` then matmul vs matmul-then-add — algebraically equal, floating-point unequal.

**Training/merge interaction (new pitfall surfaced by this research):** training checkpoints must never be saved while merged — a merged-state checkpoint carries the delta inside `base.weight` AND in `lora_B`, double-counting on reload. The demo path always stays unmerged (REQUIREMENTS Out of Scope locks this); `merge()` is an eval-time utility. Cheap insurance: `merge_lora` asserts `model.training is False`, and the merge test exercises merge→eval→unmerge only.

### Anti-Patterns to Avoid
- **Class-based module scan for targets** — picks up the tied `lm_head`; explicit allowlist only (PITFALLS P1).
- **Symmetric A/B init** — non-zero ΔW at step 0 poisons every baseline; B=0 is the gate (PITFALLS P2).
- **Scale applied in two places independently** — single `self.scale` read by forward AND merge (PITFALLS P3).
- **Inject-then-load** — breaks every checkpoint key; load → inject → freeze, pinned by test (ARCHITECTURE anti-pattern 1).
- **Bare `strict=False` loads** — silent partial loads; always behind an exact key-set assert (PITFALLS P4).
- **A/B created from `weight.T` views** — the MPS silent-freeze trigger shape; fresh explicit-shape tensors (PITFALLS P5).
- **`enabled`/`merged` as buffers** — would leak runtime flags into state_dicts and the artifact; plain attributes.
- **Unmerge by subtraction** — not bit-exact in fp; stored-clone copy-back (D-07).
- **`eject` while merged** — would eject merged (adapter-contaminated) base weights as "base"; `eject_adapter` asserts unmerged first.
- **Appending smoke-run rows to `logs/run.csv`** — new CSV file per run (ARCHITECTURE anti-pattern 3).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LoRA branch matmul | manual loops / einsum gymnastics | `x @ A.T @ B.T` (or `F.linear` twice) | Allowed math primitives per from-scratch boundary (D-08/D-09 lineage); fast and legible |
| Train/eval dropout gating | manual `if self.training` masks | `nn.Dropout` | Handles mode switching + RNG correctly; one line |
| Artifact serialization | custom binary format / JSON+npz | `torch.save` + `torch.load(weights_only=True)` | D-01 locks the `load_slim` pattern; restricted unpickler = zero code exec on load |
| Config → primitives | hand-written dict builders | `dataclasses.asdict(LoRAConfig)` | House pattern (`save_checkpoint` already `asdict`s configs) |
| Adapter training loop | a new LoRA-specific loop | existing `train()` | Inherits AMP-ordering, kill+resume, best-tracking, CSV discipline for free; verified frozen-param safe |
| Exception-safe scoped disable | manual try/finally at call sites | one `@contextmanager adapter_disabled(model)` | D-06 locks it; tests + Phase 14 share it |

**Key insight:** the ONLY thing hand-rolled here is the LoRA wrapper itself — that is the deliverable. Everything around it (optimizer, serialization, dropout, schedule, resume) reuses v1.0 machinery or torch primitives, which is exactly what keeps the phase pure-unit-testable and the existing test suite green.

## Common Pitfalls

### Pitfall 1: Wrapping the tied embedding/lm_head tensor
**What goes wrong:** `lm_head.weight` IS `wte.weight` (one tensor, `gpt.py:184`); adapting or merging into either silently corrupts input embeddings for every token (HF PEFT issues #2018/#2777/#2864).
**Why it happens:** class-based `isinstance(m, nn.Linear)` scans pick up `lm_head`.
**How to avoid:** explicit six-name allowlist (`TARGET_PROJECTIONS`); post-injection `data_ptr` test (LORA-05 success criterion 2).
**Warning signs:** trainable census includes a `8192×384`-shaped matrix; `test_gpt_weight_tying` fails; base PPL changes after a head-only merge.

### Pitfall 2: Adapter not a no-op at init
**What goes wrong:** random B init perturbs the model at step 0; every baseline/curve is poisoned.
**How to avoid:** B=0 init; bit-identical-logits test (`torch.equal`, CPU, fixed batch) vs the vanilla model — the single highest-value LoRA test.
**Warning signs:** step-0 eval differs from base; early training "improves" the old task (it's repairing self-inflicted damage).

### Pitfall 3: α/r scale drift between forward and merge
**What goes wrong:** double-scaling at merge, missing scaling, or classic-vs-rsLoRA convention mixing → merged ≠ live adapter.
**How to avoid:** one `self.scale = alpha / r` in `__init__`; merge-equivalence test ≤1e-5 on CPU; record `r`/`alpha` (the convention) in artifact + checkpoint extras.
**Warning signs:** model behaves differently after "export"; rank sweeps show wild LR sensitivity.

### Pitfall 4: Optimizer/checkpoint state across the param-set boundary
**What goes wrong:** loading pretrain optimizer state into an adapter run; bare `strict=False` silently leaving random adapters in place.
**How to avoid:** fresh optimizer per adapter run (`train()` does this by construction); key-set-audited loads only; kill+resume test reproduces the adapter-training trajectory.
**Warning signs:** trainable count ≠ 331,776 at defaults; base PPL drifts during "LoRA-only" training; resume diverges from kill point.

### Pitfall 5: MPS silent training failures
**What goes wrong:** the documented MPS fused-Adam non-contiguous silent no-op class (fixed ≥2.4, but the *class* — silent fallbacks, silent NaN — is alive); a flat loss looks like a hyperparameter problem.
**How to avoid:** A/B created as fresh contiguous tensors; params-actually-update canary on the smoke run's first step; `torch.isfinite` guard at eval intervals; correctness tests CPU-only.
**Warning signs:** loss flatlines from step 0 with nonzero grads; adapter norms never move.

### Pitfall 6: Checkpointing or ejecting while merged (phase-specific, surfaced this session)
**What goes wrong:** a checkpoint saved merged double-counts the delta on reload (base contains ΔW, lora_B ≠ 0); `eject` while merged hands back contaminated "base" Linears.
**How to avoid:** demo/training path stays unmerged (locked); `eject_adapter` and checkpoint-saving paths assert unmerged; merge is an eval-time utility exercised only by its test.
**Warning signs:** logits change after a save/load round-trip; ejected model ≠ vanilla base logits.

## Code Examples

Verified patterns from the project's own code and primary sources:

### LoRALinear core (composition wrapper)
```python
# Source: Hu et al. 2021 (arXiv:2106.09685) parameterization; shapes/init per LORA-01;
# house init std per src/personacore/model/gpt.py::_init_weights
class LoRALinear(nn.Module):
    def __init__(self, base: nn.Linear, r: int, alpha: float, dropout: float = 0.0):
        super().__init__()
        self.base = base                          # frozen original nn.Linear (composition)
        self.scale = alpha / r                    # SINGLE source of truth (forward + merge)
        self.lora_A = nn.Parameter(torch.empty(r, base.in_features))   # fresh, contiguous
        self.lora_B = nn.Parameter(torch.zeros(base.out_features, r))  # ZEROS — identity gate
        nn.init.normal_(self.lora_A, mean=0.0, std=0.02)               # A-Gaussian (LORA-01)
        self.dropout = nn.Dropout(dropout)
        self.enabled = True                       # plain attrs — never in state_dict
        self.merged = False

    def forward(self, x):
        y = self.base(x)
        if self.enabled and not self.merged:      # D-05: branch never executes when disabled
            y = y + self.scale * (self.dropout(x) @ self.lora_A.T @ self.lora_B.T)
        return y
```

### Injection + freeze (load → inject → freeze ordering)
```python
# Source: .planning/research/ARCHITECTURE.md Pattern 1 (verified against gpt.py module tree)
def inject_lora(model, cfg: LoRAConfig) -> int:
    n = 0
    for parent in model.modules():               # Block.attn and Block.mlp own the six names
        for name in cfg.targets:                 # explicit allowlist — NEVER isinstance scan
            child = getattr(parent, name, None)
            if isinstance(child, nn.Linear):
                setattr(parent, name, LoRALinear(child, cfg.r, cfg.alpha, cfg.dropout))
                n += 1
    return n                                      # callers assert n == 6 * n_layer

def mark_only_lora_trainable(model):
    model.requires_grad_(False)
    for name, p in model.named_parameters():
        if "lora_" in name:
            p.requires_grad_(True)
```

### Params-actually-update canary (reused by test + smoke script)
```python
# Source: .planning/research/PITFALLS.md Pitfall 5 prevention (Elana Simon 2025 post-mortem)
def snapshot_params(model):
    return {n: p.detach().clone() for n, p in model.named_parameters()}

# after >=1 optimizer step:
for n, p in model.named_parameters():
    if p.requires_grad:
        assert not torch.equal(p, before[n]), f"trainable param froze: {n}"
    else:
        assert torch.equal(p, before[n]), f"frozen param moved: {n}"   # LORA-02, bit-level
```

### Adapter artifact save/load (checkpoint.py choke point)
```python
# Source: src/personacore/checkpoint.py::export_slim/load_slim (mirrored verbatim style, D-01);
# schema round-trip under weights_only=True VERIFIED in project venv this session
ADAPTER_SCHEMA_VERSION = 1

def export_adapter(path, *, adapter, lora_config, base_fingerprint) -> dict:
    art = {"schema_version": ADAPTER_SCHEMA_VERSION, "adapter": adapter,
           "lora_config": lora_config, "base_fingerprint": base_fingerprint}
    torch.save(art, path)
    return art

def load_adapter(path, *, expected_fingerprint=None, map_location="cpu") -> dict:
    art = torch.load(path, map_location=map_location, weights_only=True)   # LOCKED safe-load bar
    if art.get("schema_version") != ADAPTER_SCHEMA_VERSION:
        raise ValueError(f"Unsupported adapter schema_version {art.get('schema_version')!r}")
    if expected_fingerprint is not None and art["base_fingerprint"] != expected_fingerprint:
        warnings.warn(f"adapter base fingerprint mismatch: {art['base_fingerprint']} "
                      f"!= {expected_fingerprint} — loading anyway (D-02)")
    return art
```

### Merge / bit-exact unmerge (D-07)
```python
# Source: D-07 (stored-clone restore); shape check (out,r)@(r,in)==(out,in) verified
@torch.no_grad()
def merge(self):
    assert not self.merged
    self._w0 = self.base.weight.detach().clone()          # plain attr — not in state_dict
    self.base.weight.data.add_(self.scale * (self.lora_B @ self.lora_A))
    self.merged = True

@torch.no_grad()
def unmerge(self):
    assert self.merged
    self.base.weight.data.copy_(self._w0)                 # copy-back == bit-exact round-trip
    self.merged = False
    del self._w0
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| HF PEFT `LoraLayer` as the default LoRA path | From-scratch composition wrapper | Project design decision (locked) | The wrapper IS the deliverable; PEFT banned |
| Classic `α/r` only | rsLoRA `α/√r` exists for high rank | rsLoRA 2023 | Irrelevant at r=8; pick classic, pin convention in artifact (PITFALLS P3) |
| `torch.load` default unrestricted pickle | `weights_only=True` default since torch 2.6 | torch 2.6 (2025) | The slim/adapter safe-load bar aligns with upstream direction; full resume checkpoint stays explicit `weights_only=False` (trusted-only) |
| MPS fused-Adam non-contiguous silent no-op | Fixed in torch ≥2.4 (project pins 2.7.1) | torch 2.4 | The specific bug is gone; the *class* (silent fallback/NaN) motivates the canary anyway |

**Deprecated/outdated:** nothing relevant — the phase touches no fast-moving APIs. `torch.nn.utils.parametrize` exists as an alternative injection mechanism but is explicitly excluded by CONTEXT ("no parametrize magic").

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | A-init std 0.02 (house init) is an acceptable reading of "A-Gaussian"; paper does not pin a std and loralib actually uses kaiming-uniform | Pattern 1 | Low — B=0 makes init-time behavior identical regardless; only early adapter-training dynamics shift. If smoke-run learning looks sluggish, try std `1/r` |
| A2 | "All 137 existing tests" count (from milestone research) is approximately right; exact number may have drifted | Validation Architecture | None — the requirement is "full suite green", not a count |
| A3 | `weight_decay=0.0` for adapter runs is the right default (decay fights low-rank updates) | Pattern 3 | Low — smoke run is short; carried from project ARCHITECTURE research, standard practice |
| A4 | `train()`'s in-loop `save_checkpoint` calls not forwarding `lora_config` is acceptable for Phase 9 (script-side final save carries it; or planner adds additive `checkpoint_extra` kwarg) | Pattern 3 | Medium if smoke run relies on mid-run kill+resume: a mid-run `latest.pt` without `lora_config` cannot self-describe its injection. Planner should decide: additive kwarg (cleaner, default-off) vs. script reads its own config (simpler) |

## Open Questions

1. **`checkpoint_extra` kwarg on `train()` vs script-side checkpoint saving (A4)**
   - What we know: D-04 requires full kill+resume for adapter training; `train()`'s internal saves don't forward arbitrary extras; resume needs `lora_config` to rebuild the module tree before `load_checkpoint`.
   - What's unclear: whether Phase 9's smoke run needs mid-run resume self-description, or whether the resuming script knowing its own `LoRAConfig` (it's a constant in the thin script) suffices.
   - Recommendation: keep `train()` untouched for Phase 9 (script knows its config; resume rebuilds from the script's constant); revisit the additive kwarg in Phase 14 when adapters are user-generated. Planner may choose the kwarg now if it prefers the checkpoint to be fully self-contained — both honor the locked decisions.

2. **Where the smoke script's pass/fail lands**
   - What we know: house precedent (`test_real_slim_artifact_generates_on_cpu`) is a `skipif`-gated test over real gitignored artifacts.
   - Recommendation: smoke script asserts inline and exits non-zero on failure (script = the MPS/real-weights proof); optionally one `skipif(not best.pt)` test reuses the canary on real weights for local runs. Planner discretion.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 venv (`.venv`) | all dev/test | ✓ | 3.11.15 | — (mandatory per CLAUDE.md) |
| torch | LoRA, training, artifact I/O | ✓ | 2.7.1 | — |
| numpy | memmap bins (smoke run) | ✓ | 2.4.6 | — |
| MPS backend | smoke run (primary device) | ✓ | `mps.is_available()=True` | CPU (preflight_device resolves) |
| pytest | test suite | ✓ | dev extra installed (suite collected previously) | — |
| `personacore` editable install | imports | ✓ | 0.1.0 importable | re-run `make install` if worktree breaks it (see memory note) |
| `checkpoints/best.pt` | smoke-run base (D-02 fingerprint source) | ✓ | val_loss 0.7378 artifact present | — |
| `checkpoints/model_slim.pt` | two-artifact load test (real-artifact variant) | ✓ | present | tiny-fixture slim built in tmp_path (mechanism tests don't need it) |
| `data/train.bin` / `data/val.bin` | smoke-run substrate | ✓ | present | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none missing.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest ~=9.0 (dev extra, installed in `.venv`) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (testpaths=tests, pythonpath=.) |
| Quick run command | `.venv/bin/pytest tests/test_lora_layer.py tests/test_lora_inject.py -q -x` |
| Full suite command | `make test` (= `pytest -q`; all existing tests MUST stay green) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LORA-01 | B=0 zero-delta at init; A-Gaussian; α/r scale; dropout on LoRA branch, train-mode only; six projections wrapped per block via post-load injection | unit | `.venv/bin/pytest tests/test_lora_layer.py tests/test_lora_inject.py -q -x` | ❌ Wave 0 |
| LORA-02 | Grad isolation: after training steps every base param bit-untouched (`torch.equal`); canary: trainables moved; fresh-optimizer state covers only A/B | unit | `.venv/bin/pytest tests/test_lora_training.py -q -x` | ❌ Wave 0 |
| LORA-03 | Artifact round-trips `weights_only=True`; schema-version raise; fingerprint warn-but-load; two-artifact load (`load_slim`+`load_adapter`+inject) reproduces logits | unit | `.venv/bin/pytest tests/test_lora_artifact.py -q -x` | ❌ Wave 0 |
| LORA-04 | Merged forward ≡ base+adapter ≤1e-5 (CPU); unmerge bit-exact via stored clone; `merged_state_dict()` pure with vanilla-GPT key set | unit | `.venv/bin/pytest tests/test_lora_merge.py -q -x` | ❌ Wave 0 |
| LORA-05 | Enable/disable round-trip bit-identical; context manager exception-safe; eject restores vanilla; param-count = `r·n_layer·18·n_embd`; tied `data_ptr` unchanged post-injection; load→inject→freeze ordering pinned | unit | `.venv/bin/pytest tests/test_lora_toggle.py tests/test_lora_inject.py -q -x` | ❌ Wave 0 |
| LORA-02/05 (real weights) | Canary + bit-untouched on `best.pt` over TinyStories bins on MPS | smoke (manual-run script, asserts inline) | `.venv/bin/python scripts/train_adapter_smoke.py` | ❌ Wave 0 (local-only; CI-skipped — needs gitignored artifacts) |

All unit tests use the `_tiny_config()` fixture precedent (`ModelConfig(block_size=32, n_layer=1..2, n_head=2, n_embd=16)` from `tests/test_slim_checkpoint.py`) — CPU-only, GPU-free, seconds to run. Bit-identity asserts use `torch.equal`; tolerance asserts use `torch.allclose(atol=1e-5)` on CPU.

### Sampling Rate
- **Per task commit:** `.venv/bin/pytest tests/test_lora_*.py -q -x` (new suite only, < 30 s)
- **Per wave merge:** `make test` (full suite — proves existing tests stay green; `checkpoint.py` is the only touched v1.0 module and the change is additive)
- **Phase gate:** full suite green + smoke script pass on MPS before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_lora_layer.py` — covers LORA-01 (init/scale/dropout/identity)
- [ ] `tests/test_lora_inject.py` — covers LORA-01/05 (allowlist, ordering, tied-tensor, param count)
- [ ] `tests/test_lora_toggle.py` — covers LORA-05 (D-05/D-06 toggle, context manager, eject)
- [ ] `tests/test_lora_merge.py` — covers LORA-04 (D-07/D-08)
- [ ] `tests/test_lora_artifact.py` — covers LORA-03 (D-01/D-02/D-03)
- [ ] `tests/test_lora_training.py` — covers LORA-02 (canary, kill+resume — adapt `test_resume_curve.py` pattern)
- Framework install: none needed (pytest present)

## Security Domain

`security_enforcement` is absent from config → treated as enabled. This phase's security surface is deserialization + artifact integrity, mapped to the project's claim-integrity/privacy posture:

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (local, offline project) |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation (incl. deserialization) | **yes** | `torch.load(weights_only=True)` for the shareable adapter artifact (restricted unpickler, zero code exec — the LOCKED slim bar, D-01); `schema_version` validation raising `ValueError`; exact key-set audit before applying adapter tensors |
| V6 Cryptography | no | — (provenance via git SHA, not signatures — consistent with v1.0 QA-02) |
| V10 Malicious Code / Supply Chain | yes | Zero new dependencies this phase; full resume checkpoint remains `weights_only=False` TRUSTED-ONLY (own files), documented verbatim like `checkpoint.py`'s existing docstring |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious pickle in a shared "persona file" | Elevation of privilege | `weights_only=True` choke point (`load_adapter`) — the persona file is explicitly the artifact designed to be swapped/shared, so it MUST meet the safe-load bar |
| Adapter loaded onto wrong base (silent behavior corruption) | Tampering/Integrity | D-02 base fingerprint (`git_sha` + `step`), warn-but-load; demo surfaces hashes (Phase 14 inherits) |
| Wrong-shape/extra tensors smuggled in artifact | Tampering | Exact key-set equality assert vs the injected model's `lora_` keys before load; shape mismatches raise in `load_state_dict` |
| Personal data leaking into committed artifacts | Information disclosure | Smoke adapter trains on TinyStories only; all run outputs gitignored (`.gitignore` covers checkpoints/logs) |

## Sources

### Primary (HIGH confidence)
- `src/personacore/model/gpt.py` (six named projections lines 71–74/120–121; tying line 184), `checkpoint.py` (open-dict `**extra`, `export_slim`/`load_slim`/`SLIM_SCHEMA_VERSION`), `training/loop.py` (`train()` optimizer construction line 234, `assemble_loss` call line 138), `training/loss.py`, `config.py` (dataclass pattern), `tests/test_gpt_lora_seam.py` / `test_gpt_weight_tying.py` / `test_gpt_param_count.py` / `test_slim_checkpoint.py` — read line-level this session
- **Empirical verification in project venv (torch 2.7.1), this session:** AdamW frozen-param bit-untouched incl. weight decay; optimizer state only for stepped params; `clip_grad_norm_` None-grad safe; adapter-schema `weights_only=True` round-trip incl. tuple-of-str metadata; param-count formula = 331,776 at defaults
- `.planning/research/SUMMARY.md`, `ARCHITECTURE.md`, `PITFALLS.md` (2026-06-11, HIGH confidence, themselves verified line-by-line against shipped code) — converged decisions consumed, not re-litigated
- Hu et al., *LoRA: Low-Rank Adaptation of Large Language Models* (arXiv:2106.09685) — A/B parameterization, B-zero init, α/r scaling, merge identity
- HF PEFT issues #2018/#2777/#2864 — tied-weight adapter corruption (the lm_head allowlist rationale)
- Elana Simon 2025 MPS post-mortem — the canary's reason to exist (specific bug fixed in torch ≥2.4; project pins 2.7.1)

### Secondary (MEDIUM confidence)
- rsLoRA (huggingface.co/blog/damjan-k/rslora) — α/√r convention exists; classic α/r chosen at r=8

### Tertiary (LOW confidence)
- None — no unverified web findings were used.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new deps; environment verified live this session
- Architecture: HIGH — locked decisions + line-level-verified seams + paper-canonical mechanics; the two discretion areas resolved with empirical evidence
- Pitfalls: HIGH — grounded in primary sources via the project's own pitfalls research, plus one phase-specific pitfall (checkpoint/eject-while-merged) surfaced by reasoning about D-07/D-08 interactions

**Research date:** 2026-06-11
**Valid until:** ~2026-07-11 (stable domain: pinned torch, paper-canonical math, no external endpoints)
