# Phase 9: LoRA Core - Context

**Gathered:** 2026-06-11
**Status:** Ready for planning

<domain>
## Phase Boundary

From-scratch `LoRALinear` adapters wrap the six named `nn.Linear` projections per block
(`q_proj`/`k_proj`/`v_proj`/`c_proj`/`fc_in`/`fc_out`) via post-load injection — correctness
proven by tests, adapter weights shipping as a small swappable artifact (LORA-01..05).
Pure unit-testable machinery: no conversational data, no EWC, no long training runs.
`model/gpt.py` is never edited; the existing v1.0 seams carry everything.

</domain>

<decisions>
## Implementation Decisions

### Adapter artifact contract
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

### Toggle & merge semantics
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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & roadmap
- `.planning/REQUIREMENTS.md` — LORA-01..05 (the phase's requirement text); Out of Scope table
  (no HF PEFT, no merging as demo deploy path)
- `.planning/ROADMAP.md` — Phase 9 goal + 5 success criteria; dependency map (Phase 9 is
  independent of 10/11; Phase 14 consumes it)

### v2.0 research (decisions already converged — do not re-litigate)
- `.planning/research/SUMMARY.md` — two-mechanism stage split (LoRA = stage-3 personalization on
  the frozen conversational base); `lora/` package shape (`layer.py` + `inject.py`);
  load-vanilla → inject → freeze ordering; explicit six-name allowlist (never class-based scans)
- `.planning/research/ARCHITECTURE.md` — LoRA injection architecture detail; additive-only
  changes to v1.0 modules; LOCKED-contract preservation analysis
- `.planning/research/PITFALLS.md` — LoRA correctness cluster: tied-embedding allowlist, B=0
  identity gate, α/r double-scaling at merge (single `scale` source of truth), inject-after-load
  discipline, params-actually-update canary

### v1.0 seams this phase consumes (code)
- `src/personacore/model/gpt.py` — the six named projections (lines 71–74, 120–121), tied
  `lm_head.weight = wte.weight` (same `data_ptr` — must never be wrapped), purity rule (model
  never edited)
- `src/personacore/checkpoint.py` — open-dict `save_checkpoint(**extra)` seam,
  `export_slim`/`load_slim` `weights_only=True` precedent (`SLIM_SCHEMA_VERSION` pattern that
  `ADAPTER_SCHEMA_VERSION` mirrors)
- `tests/test_gpt_lora_seam.py` — the RED structural gate pinning the six-name seam (PROJECTIONS
  tuple is the canonical allowlist)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `GPT` (`src/personacore/model/gpt.py`): six named `nn.Linear` projections per block already
  test-pinned; `named_modules()` traversal + `setattr` injection is the intended mechanism
- `save_checkpoint`/`load_checkpoint` (`src/personacore/checkpoint.py`): open-dict `**extra`
  carries `lora_config`; full RNG/optimizer state gives adapter training kill+resume for free
- `export_slim`/`load_slim`: the `weights_only=True` + schema-version + choke-point pattern to
  mirror for the adapter artifact
- `assemble_loss` (`src/personacore/training/loss.py`): untouched by this phase (EWC seam,
  Phase 10) — but confirms the additive-seam house style
- Existing test idioms: `data_ptr()` tying tests (`test_gpt_weight_tying.py`), param-count gates
  (`test_gpt_param_count.py`), bit-identical-defaults pattern (`test_ablation_config.py`)

### Established Patterns
- **Purity rule:** `model/gpt.py` is a pure `(logits, loss)` producer and is NEVER edited; all
  LoRA machinery lives in a new `lora/` package
- **Additive, default-off changes only** to v1.0 modules; defaults reproduce v1.0 bit-for-bit
  (all 137 existing tests stay green)
- **Thin scripts, logic in package** (`scripts/export_slim.py` style)
- **From-scratch boundary:** hand-rolled composition wrapper; no `torch.nn.utils.parametrize`
  magic, no HF PEFT
- **CPU-only, GPU-free tests**; fp32 tolerance tests on CPU (≤1e-5 per research)

### Integration Points
- Post-load injection: `load_checkpoint`/`load_slim` → `inject(model)` → freeze — ordering is
  load-bearing (wrapping before loading breaks every checkpoint key)
- Phase 14 consumes: `load_adapter()`, `set_adapter_enabled()`, `adapter_disabled()`, `eject_adapter()`
- Phase 15 consumes: `merged_state_dict()` / `scale·B@A` for ΔW heatmaps

</code_context>

<specifics>
## Specific Ideas

- The adapter artifact is framed as a **"persona file"** — small, swappable, deletable; its
  safe-load bar and provenance metadata are part of the privacy narrative, not just engineering
- Bit-exactness everywhere it's achievable (toggle round-trip, unmerge restore) — the project
  treats bit-identity as a feature of the portfolio story, tolerance only where fp math forces
  it (merged-forward equivalence)

</specifics>

<deferred>
## Deferred Ideas

- **Merged-slim export path** (`merge()` → `export_slim` single plain-GPT state dict): deferred
  until a phase actually needs it — research floated it for Phase 14 shipping. Phase 9's
  `merged_state_dict()` (D-08) lands as its building block, so wiring it later is trivial.

</deferred>

---

*Phase: 9-LoRA Core*
*Context gathered: 2026-06-11*
