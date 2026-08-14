---
phase: quick-260814-d0j
plan: 01
status: complete
subsystem: LoRA injection / adapter apply contract
tags: [W1, LORA-01, LORA-03, LORA-04, silent-failure, pre-phase-17]
requires:
  - src/personacore/checkpoint.py::load_adapter (raises when lora_config is absent — what makes the audit's skip unreachable for real files)
provides:
  - src/personacore/lora/inject.py::load_adapter_weights (third audit — scale, beside keys and shapes)
affects:
  - scripts/phase14_recall.py::load_adapted_model
  - scripts/phase14_recall.py::run_bit_identity_control
  - scripts/personalize_demo.py::build_demo
tech-stack:
  added: []
  patterns:
    - "guard at the shared choke point rather than at each call site, so callers that do not exist yet are covered"
    - "exact float equality where both sides run the same operation on the same operands — a tolerance would only weaken the check"
key-files:
  created: []
  modified:
    - src/personacore/lora/inject.py
    - scripts/phase14_recall.py
    - scripts/personalize_demo.py
    - tests/test_lora_inject.py
commits:
  - 0a26702 feat(quick-260814-d0j): audit the LoRA scale at load_adapter_weights — close W1
  - ec3e94a fix(quick-260814-d0j): the three LoRA consumers inject at the artifact's own config
---

# Quick Task 260814-d0j — W1 closed

`v2.0-MILESTONE-AUDIT.md:45` carried W1 as an open warning; `STATE.md` locked it as a
pre-condition: *"must land before ANY Phase-17 adapter trains."* Phase 17 is next, so it landed
first. **W1 was never fixed before this task** — all three consumers still injected defaults.

## What was actually wrong

`load_adapter_weights` audited the adapter's **keys** and **shapes**. A wrong `r` changes tensor
shape and was caught. A wrong `alpha` changes no shape at all: it moves only
`LoRALinear.scale = alpha / r`, the single multiplier `forward` and `merge` both read. Three
consumers injected with `LoRAConfig()` defaults instead of the artifact's own config, so an
adapter taught at another alpha would have been applied at the wrong magnitude with **no error
raised anywhere**.

Benign until now only by coincidence — `checkpoints/persona_adapter.pt` carries
`{'r': 8, 'alpha': 16.0, 'dropout': 0.0, 'targets': (…)}`, which equals `LoRAConfig()`. A
Phase-17 adapter is under no such obligation.

## What was done

**The audit went at the choke point, not the call sites.** Fixing the three sites fixes today's
callers; it does not stop a fourth — a Phase-17 script — from writing the same line. Every
consumer already routes through `load_adapter_weights`, which already receives the whole
artifact, `lora_config` included. One audit there covers all present and future callers, which is
what the STATE.md lock actually demands.

- `src/personacore/lora/inject.py` — third audit beside keys and shapes, before `load_state_dict`:
  every `LoRALinear.scale` compared against `artifact["lora_config"]["alpha"] / ["r"]`. Exact
  equality is deliberate (same operation, same operands → bit-identical float). Skipped when the
  artifact has no `lora_config`, which is only the in-memory test path — `load_adapter`
  (`checkpoint.py:246`) raises when the key is missing, so anything read off disk always has it.
- `scripts/phase14_recall.py` — `load_adapted_model` (what `phase16_persistence.py:2741` calls and
  Phase 17 will call) and `run_bit_identity_control` both read `LoRAConfig(**artifact["lora_config"])`.
- `scripts/personalize_demo.py` — `build_demo` likewise.
- `scripts/teach_persona.py:478` and `scripts/train_adapter_smoke.py:63` **untouched**: producers,
  whose `LORA_CFG` is what `asdict()` writes INTO the artifact.

The persona file is now loaded *before* injection at all three sites. That preserves the
`LOAD BEFORE INJECT` ordering the comments name — that rule is about
`model.load_state_dict(ckpt["model"])` preceding `inject_lora`, and reading a file off disk
touches no model state. The missing-adapter `SystemExit` still precedes `load_adapter`, so a
missing persona file keeps its own message.

## Evidence

| Claim | Evidence |
|---|---|
| The audit is load-bearing | **Mutation-checked**: a copy of `inject.py` with the audit block stripped loads the same alpha=32-vs-16 artifact **silently, no error** — the pre-fix behaviour. The live module raises `ValueError: adapter scale mismatch …`. |
| The test cannot pass against an audit that rejects everything | The new test carries a **positive control**: the artifact's own config still loads and the tensor is copied. |
| Behavioural no-op on every committed number | `git status --porcelain -- results/ checkpoints/` → **0 lines**. The shipped adapter's config equals the defaults, so nothing that ran before runs differently. |
| Phase 16's byte-reproducibility survives | Full suite **579 passed, 1 skipped** (the CUDA-only fp16 AMP smoke) in 122.79 s. |
| Only producers keep the defaults | `grep -rn "LoRAConfig()" scripts/ src/` → executable hits only at `teach_persona.py:478` and `train_adapter_smoke.py:63`; every other hit is comment or message text. |
| Lint | `ruff check` clean, `ruff format --check` 148 files already formatted. |

## Notes for Phase 17

The audit is what makes a Phase-17 adapter at a non-default alpha **safe to train and load**: a
consumer that forgets to read the config now fails loudly at load time instead of answering from
a mis-scaled adapter. `v2.0-MILESTONE-AUDIT.md` is left byte-unchanged as the dated historical
record; the closure is recorded in `STATE.md`, following the annotation style the v1.0 deferred
table already uses.
