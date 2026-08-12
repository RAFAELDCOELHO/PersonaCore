# Phase 9: LoRA Core - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-11
**Phase:** 9-LoRA Core
**Areas discussed:** Adapter artifact contract, Toggle & merge semantics

---

## Adapter artifact contract

### Q1: What load-safety bar should the adapter artifact meet?

| Option | Description | Selected |
|--------|-------------|----------|
| weights_only=True + schema (Recommended) | Adapter file = A/B tensors + primitive metadata only, own ADAPTER_SCHEMA_VERSION, loaded through a load_adapter() choke point mirroring load_slim. Same safe-load bar as model_slim.pt. | ✓ |
| Trusted-only full pickle | Plain torch.save/load like the resume checkpoint (weights_only=False). Simpler, but weakens the story for the one portable artifact. | |
| You decide | Claude picks during planning based on the slim-contract precedent. | |

**User's choice:** weights_only=True + schema

### Q2: Base fingerprint binding and strictness at load?

| Option | Description | Selected |
|--------|-------------|----------|
| Fingerprint + hard error (Recommended) | Record base checkpoint git_sha + step; load onto mismatched base raises. | |
| Fingerprint + warn only | Same provenance, warn on mismatch. Friendlier mid-milestone while the base evolves (smoke adapters on best.pt, real adapters on Phase-12 base). | ✓ |
| Shape-check only | No provenance binding — verify rank/dims/target-module names only. | |

**User's choice:** Fingerprint + warn only
**Notes:** Accepts the silent-garbage risk in exchange for dev flexibility while the conversational base doesn't exist yet.

### Q3: How does the adapter pair with the slim inference artifact?

| Option | Description | Selected |
|--------|-------------|----------|
| Two-artifact load only (Recommended) | Demo path = load_slim + load_adapter + inject. Merged-slim export deferred until a phase needs it. | ✓ |
| Also ship merged-slim export now | Wire merge() → export_slim from day one. Builds a ship path the demo is forbidden to use. | |
| You decide | Claude picks during planning based on Phase 14's protocol. | |

**User's choice:** Two-artifact load only

### Q4: Kill+resume support for adapter training?

| Option | Description | Selected |
|--------|-------------|----------|
| Full open-dict resume (Recommended) | Adapter training runs through save_checkpoint/load_checkpoint (optimizer + RNG for A/B; lora_config in **extra). Consistent with the resume guarantee; nearly free. | ✓ |
| Final-export only | Adapter fits are ~100–300 steps; rerun on failure. Breaks the every-run-is-resumable invariant. | |
| You decide | Claude picks based on Phase 14 teaching-run budgets. | |

**User's choice:** Full open-dict resume

---

## Toggle & merge semantics

### Q1: How should disable achieve the bit-identical-to-base round-trip?

| Option | Description | Selected |
|--------|-------------|----------|
| Flag-gated delta branch (Recommended) | `enabled` flag; delta branch never executed when off — structural bit-identity, instant live toggle. | |
| Eject / re-inject | Restore original nn.Linear modules; bit-identity trivially true but churns the module tree mid-session. | |
| Both: flag for toggle, eject for reset | Flag-gating powers live on/off; separate eject() utility for full removal ("Reset = drop adapter = instant forget"). | ✓ |

**User's choice:** Both — flag for toggle, eject for reset

### Q2: What model-level API should the lora package expose for toggling?

| Option | Description | Selected |
|--------|-------------|----------|
| Helper functions (Recommended) | set_adapter_enabled(model, bool), eject_adapter(model) in lora/inject.py. | |
| Helpers + context manager | Same plus `with adapter_disabled(model):` for scoped base-vs-adapter comparisons (exception-safe re-enable). | ✓ |
| You decide | Claude picks the surface during planning. | |

**User's choice:** Helpers + context manager
**Notes:** Phase 14's scripted recall does the base-vs-adapter dance repeatedly — the context manager serves it directly.

### Q3: Must unmerge restore base weights bit-exactly?

| Option | Description | Selected |
|--------|-------------|----------|
| Bit-exact via stored copy (Recommended) | merge() clones W₀ first; unmerge() copies back. Round-trip bit-identical; memory trivial at 13.9M. | ✓ |
| Subtract delta + tolerance | Classic LoRA: W − scale·B@A, ~1e-7 fp error. Breaks the bit-exact invariant. | |
| You decide | Either passes LORA-04's fp32-tolerance forward-equivalence test. | |

**User's choice:** Bit-exact via stored copy

### Q4: What form should merge() take?

| Option | Description | Selected |
|--------|-------------|----------|
| In-place merge/unmerge (Recommended) | merge(model)/unmerge(model) mutate the injected model (the LORA-04 forward-equivalence object). | |
| Pure merged_state_dict() function | No mutation; returns plain-GPT state dict with W₀ + scale·B@A folded in. | |
| Both | In-place pair for LORA-04 plus the pure function as the Phase 15 / merged-slim building block. | ✓ |

**User's choice:** Both

---

## Claude's Discretion

- **LoRA config surface & defaults** (area surfaced but not selected for discussion):
  LoRAConfig dataclass shape, r/alpha/dropout defaults (research implies r=8 → ~1.3 MB),
  how config travels (open-dict `**extra` + adapter-artifact metadata)
- **Frozen-base training integration** (area surfaced but not selected for discussion):
  freeze enforcement vs the untouched v1.0 train(), smoke-run substrate (TinyStories bins
  at best.pt), script-vs-test packaging of the params-actually-update canary
- Dropout placement, `lora/` package file naming, test-suite organization

## Deferred Ideas

- **Merged-slim export path** (merge() → export_slim single plain-GPT state dict) — deferred
  until a phase actually needs it; Phase 9's merged_state_dict() lands as its building block
