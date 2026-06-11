# Phase 4: GPT Transformer Decoder - Context

**Gathered:** 2026-06-05
**Status:** Ready for planning

<domain>
## Phase Boundary

A from-scratch **~10–15M-parameter GPT decoder** — the central *"I built a transformer"*
claim — that drops into the **already-proven Phase-3 harness** via the locked
`forward(idx, targets=None) -> (logits, loss)` contract, with the densest cluster of silent
correctness bugs gated by tests and the M2 LoRA seam left open (naming only, no wrapper).

**Mode:** MVP (vertical slices) — `**Mode:** mvp` in ROADMAP. The transformer math is the
deliverable; it must overfit a single batch through the existing loop before anything else.

**In scope (MODEL-02..07):**
- Causal multi-head self-attention: masked **before** softmax, scaled by **1/√d_head**,
  GELU MLP, **pre-norm** LayerNorm blocks + residuals, **learned positional embeddings**,
  final `ln_f` (MODEL-02).
- **Weight tying** between token embedding and output head, verified by a `data_ptr()`
  tensor-identity test (MODEL-03).
- **GPT-2-style init**, verified by a per-tensor init-std check, including residual-scaled
  output projections (MODEL-04).
- **Exact parameter counting** (tied weights counted once) hitting the ~10–15M target
  (MODEL-05).
- **Causality-perturbation test** — changing token `t` cannot change logits at positions
  `< t` (MODEL-06).
- **M2 LoRA seam** — every adaptable projection is a named `nn.Linear` called as a module;
  naming only, **no** wrapper, **no** rank params, **no** freezing this phase (MODEL-07).
- CPU-only unit tests for all of the above.

**Out of scope (other phases):**
- Full-corpus `uint16` memmap + TinyStories fetch + the real **pretraining run** — Phase 5
  (PRE-01..03). Phase 4 only proves the model overfits a single batch via the existing harness.
- Full-featured `generate()` (top-k/top-p, EOS-aware stop) + its tests — Phase 6 (GEN-01..03).
- Gradio demo / slim inference checkpoint — Phase 8.
- **LoRA wrapper math + EWC Fisher** — Milestone 2. Phase 4 leaves the *named-module* seam
  open only; it does not wrap, freeze, or add rank params.
- New training-loop / config / checkpoint code — `training/`, `config.py`, `checkpoint.py`,
  `logging.py` are **reused untouched** (Phase-3 D-09).

</domain>

<decisions>
## Implementation Decisions

### Attention Math — the from-scratch centerpiece (discussed)
- **D-01:** **Implement BOTH a hand-rolled manual attention path AND an `sdpa` path, pinned by
  a numerical-equivalence unit test.** The manual path is the narrated portfolio artifact:
  split projections → `att = (q @ k.transpose(-2,-1)) / sqrt(d_head)` → **causal mask applied
  BEFORE softmax** (`masked_fill(mask==0, -inf)`) → `softmax(dim=-1)` → `att @ v`. The sdpa path
  is `F.scaled_dot_product_attention(..., is_causal=True)` (math backend on Pascal — allowed
  primitive). A test asserts `allclose(manual, sdpa, atol≈1e-5)` so the hand-rolled math is
  *proven* to match the reference primitive.
- **D-02:** **`attn_impl` config toggle, default = `manual` everywhere.** The default forward
  path runs the hand-rolled math (portfolio-purest — the default behavior *is* the from-scratch
  transformer); sdpa is opt-in. The toggle lets **Phase 5** flip to sdpa for its modest memory
  savings on the long P100 pretrain without a code change. Mechanism (a `ModelConfig` field vs a
  constructor arg) is the planner's call; intent is: manual default, switchable, equivalence-tested.
- **D-02a:** The causal mask is the standard lower-triangular buffer sized to `block_size`
  (registered non-persistent buffer), sliced to `[:T, :T]` per forward. Both paths share the same
  causality contract; the **MODEL-06 causality-perturbation test guards it regardless of which
  path is active**.

### LoRA Seam Shape — M2 adaptation surface (discussed, MODEL-07)
- **D-03:** **Separate `q_proj` / `k_proj` / `v_proj` named `nn.Linear(n_embd, n_embd)`** for the
  attention input projections (NOT a fused `c_attn`). Rationale: finest M2 LoRA granularity — the
  canonical "adapt Q and V, freeze K" recipe becomes a per-module choice. Attention **output**
  projection is a separate named `nn.Linear` `c_proj`. Three small matmuls instead of one fused;
  acceptable at 10–15M scale. The manual attention (D-01) splits q/k/v from these three modules.
- **D-04:** **MLP projections are also named, HF-style: `fc_in` (`n_embd → 4·n_embd`) and
  `fc_out` (`4·n_embd → n_embd`).** All **six** per-block projections — `q_proj`, `k_proj`,
  `v_proj`, `c_proj`, `fc_in`, `fc_out` — are LoRA-targetable named `nn.Linear` modules, so M2
  can wrap any subset (attention AND/OR MLP). Naming leans HF/descriptive to stay consistent with
  the `q/k/v_proj` choice in D-03.
- **D-04a — init interaction (IMPORTANT for MODEL-04):** GPT-2 residual-scaled init
  (`std = 0.02 / sqrt(2 · n_layer)`) applies to the **two residual-OUTPUT projections** that write
  back into the residual stream: **`c_proj` (attn output) AND `fc_out` (MLP output)** — not just a
  single `c_proj`. The roadmap success criterion phrases this as "residual-scaled `c_proj`"; with
  HF naming that means both output projections. The per-tensor init-std check must assert the
  scaled std on **both** `c_proj` and `fc_out`, and the base `0.02` std on the input projections,
  embeddings, etc.

### Locked from prior phases (carried forward — NOT re-decided)
- **D-05:** **`forward(idx, targets=None) -> (logits, loss)` is locked** (Phase-3 D-02). GPT
  implements it **unchanged**, including the `logits.view(B*T, V)` vs `targets.view(B*T)` CE
  flatten (D-02a). The model stays **pure** (base cross-entropy only); loss assembly lives in
  `training/loss.py` (`assemble_loss`), never in the model — the EWC seam is untouched here.
- **D-06:** **Config comes from the existing `ModelConfig`** — `vocab_size=8192`, `eos_id=8184`,
  `block_size=256`, and the **already-present** `n_layer=6, n_head=6, n_embd=384, dropout=0.0`.
  These defaults compute to **~13.9M params** (token emb 8192×384 ≈ 3.15M, pos emb 256×384 ≈
  0.10M, 6 blocks ≈ 10.6M; output head **tied**, counted once) — **already in the 10–15M target**.
  Planner should confirm with exact counting (MODEL-05), not re-pick the sizing.
- **D-07:** **Module layout** (Phase-3 D-09): the GPT lives at `src/personacore/model/gpt.py`
  beside `bigram.py`; `training/` is reused **untouched**. Thin entry points only, **no
  CLI/argparse** (Phase-1 D-04).

### Claude's Discretion (user delegated — leanings the user accepted; planner may refine mechanics, honor intent)
The user discussed only Attention math and the LoRA seam and explicitly delegated the rest.
Accepted leanings (vetoable in CONTEXT review, but treated as the default):
- **D-08 — GPT-2-faithful conventions:** biases **ON** for `nn.Linear` and LayerNorm; **GELU
  tanh-approximation** (`approximate="tanh"`, GPT-2 `gelu_new`); **dropout wired-but-0**
  (`dropout=0.0` default from `ModelConfig`, applied at the standard attn/residual/MLP points so
  it is configurable later). Chosen over nanoGPT-lean (bias-free) to match the GPT-2 init story
  the success criteria describe.
- **D-09 — From-scratch boundary for primitives:** **hand-roll LayerNorm** from scratch (matches
  the from-scratch attention narrative — the portfolio shows the normalization math too), with
  **`nn.LayerNorm` as an equivalence oracle** in a unit test (same pattern as D-01's
  manual-vs-sdpa equivalence). GELU may use `F.gelu`/`nn.GELU` (pure pointwise primitive) —
  hand-rolling it adds little narrative. `ln_f` and the two pre-norm LayerNorms per block use the
  hand-rolled implementation.
- **D-10 — Overfit-single-batch gate:** reuse the Phase-3 overfit pattern (drive loss → ~0 on one
  fixed batch over a bounded step budget, CPU-only, seeded) to satisfy success-criterion #1 that
  the GPT swaps into the existing loop.
- **D-11 — Param-count test:** exact counting must count **tied** weights once (the lm_head shares
  the token-embedding tensor); assert the total lands in `[10e6, 15e6]`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase requirements & goal
- `.planning/REQUIREMENTS.md` — **MODEL-02..MODEL-07** (the acceptance text this phase must
  satisfy), including the MODEL-07 M2-seam note ("every adaptable projection is a named
  `nn.Linear`").
- `.planning/ROADMAP.md` §"Phase 4: GPT Transformer Decoder" — goal + the **5 success criteria**
  (overfit-single-batch, causality-perturbation, `data_ptr()` weight-tying + init-std, exact
  param count, named-`nn.Linear` LoRA seam) + `**Mode:** mvp` + `Depends on: Phase 3`.

### Locked stack & P100 discipline
- `.planning/research/STACK.md` and `CLAUDE.md` (Technology Stack section) — fp16 AMP +
  `GradScaler` only (**no bf16** on Pascal); `torch.compile` **skipped** on P100;
  `F.scaled_dot_product_attention` allowed but **FlashAttention backend won't engage on Pascal**
  (math-backend fallback) — informs D-01/D-02 (the sdpa path is for memory/equivalence, not speed).

### Reusable Phase-1/2/3 code (read before writing the model)
- `src/personacore/model/bigram.py` — the **locked `forward(idx, targets) -> (logits, loss)`
  contract** (D-02/D-02a) the GPT must replicate **unchanged**; the model-stays-pure rule (no
  `assemble_loss`, no `generate`).
- `src/personacore/config.py` — `ModelConfig` (`vocab_size=8192`, `eos_id=8184`, `block_size=256`,
  `n_layer=6`, `n_head=6`, `n_embd=384`, `dropout=0.0`); `RuntimeConfig` (device/AMP/`autocast()`,
  bf16-on-Pascal guard); `TrainConfig`. The model reads sizing from `ModelConfig` — **no new
  config layer** (D-06).
- `src/personacore/training/` — `loop.py` (train step), `loss.py` (`assemble_loss` EWC seam),
  `data.py` (doc-level split + random-window sampling), `schedule.py` (warmup+cosine LambdaLR).
  **Reused untouched**; the GPT plugs into `loop.py` via the locked forward contract.
- `src/personacore/checkpoint.py` — open-dict `save_checkpoint`/`load_checkpoint` with full RNG
  restore and `**extra` seam; requires `scheduler.state_dict()`. Unchanged this phase.
- `src/personacore/seeding.py` — determinism utilities for the overfit + equivalence tests.

### Carried-forward decisions
- `.planning/phases/03-bigram-baseline-training-harness/03-CONTEXT.md` — D-02 (forward contract),
  D-09 (module layout: `model/gpt.py` beside bigram, `training/` reused), D-10 (overfit gate).
- `.planning/phases/01-scaffolding-reproducible-environment/01-CONTEXT.md` — D-04 (no CLI/argparse),
  D-11 (module dirs added by their own phase).
- `.planning/phases/02-from-scratch-bpe-tokenizer/02-CONTEXT.md` — D-01 (`vocab_size=8192` locked),
  D-03 (EOS id `8184`).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `BigramLanguageModel.forward` — the exact `(logits, loss)` shape/flatten the GPT copies; the
  GPT is a drop-in replacement behind the same signature, so `training/loop.py` needs **zero**
  changes to train it.
- `ModelConfig` already carries `n_layer/n_head/n_embd/block_size/dropout` — the GPT constructor
  reads these directly; defaults (6/6/384/256) already hit ~13.9M params (D-06).
- `RuntimeConfig.autocast()` — the loop's fp16 path already wraps forward; the GPT must be
  autocast-safe (no manual `.half()`/dtype juggling inside the model).
- Phase-3 overfit / resume / seeding test patterns — the MODEL success-criteria tests mirror
  them (overfit-one-batch, deterministic via `seeding`).

### Established Patterns
- **From-scratch ethos:** PyTorch primitives only; hand-rolled math where it tells the story
  (attention D-01, LayerNorm D-09), with `nn`/`F` reference oracles in equivalence tests.
- **CPU-only test suite** (Phase-1 CI) — every Phase-4 test must run GPU-free. The sdpa
  equivalence test and all MODEL gates run on CPU.
- **Atomic commits + Makefile `lint`/`test` gate**; thin `scripts/` entry points, no CLI layer.
- **nanoGPT idioms** as conceptual reference (block structure, pre-norm, weight tying, GPT-2
  init) — implemented by hand, not vendored.

### Integration Points
- GPT `forward` → `training/loop.py` (unchanged) → `assemble_loss(base, ())` identity → existing
  open-dict checkpoint. The whole harness is already proven; Phase 4 only swaps the model.
- The six named projections (`q_proj/k_proj/v_proj/c_proj/fc_in/fc_out`) → **M2 LoRA** wraps a
  subset; the `**extra` checkpoint slot already accommodates M2 state with no format change.
- Tied token-embedding / lm_head tensor → the `data_ptr()` identity test (MODEL-03) and the
  count-once param test (MODEL-05).

</code_context>

<specifics>
## Specific Ideas

- **Attention must visibly show the math** — the manual path (mask-before-softmax, 1/√d_head
  scaling) is the portfolio centerpiece; the sdpa equivalence test exists to *prove* the
  hand-rolled version is correct, not to replace it as the default (D-01/D-02).
- **The LoRA seam is the M2 bridge** — separate q/k/v + named MLP projections are chosen
  specifically so the Milestone-2 weight-memory mechanism (the project's novel claim) can adapt
  Q+V (or any subset) without a model rewrite. Get the names right now; M2 depends on them.
- **Karpathy nanoGPT / GPT-2** as the conceptual reference for block layout, weight tying, and the
  residual-scaled init — implemented by hand.

</specifics>

<deferred>
## Deferred Ideas

- **LoRA adapter wrapping + freezing + rank params** — Milestone 2. Phase 4 leaves the named-module
  seam open only (MODEL-07).
- **EWC Fisher-penalty computation** — Milestone 2, via the already-wired `assemble_loss` seam.
- **Full-corpus `uint16` memmap + TinyStories pretraining run** — Phase 5 (PRE-01..03). Phase 4
  proves overfit-single-batch only.
- **Full `generate()` (top-k/top-p, EOS-aware stop) + tests** — Phase 6 (GEN-01..03).
- **Architecture / LR ablation table** — Phase 7 (EVAL-03). Param sizing is locked at the
  `ModelConfig` defaults for Phase 4; ablations are a later phase.
- **Hand-rolling GELU from scratch** — considered under D-09; deferred as low narrative value
  (pure pointwise primitive). Revisit only if the writeup wants it.

None of these expanded Phase 4 scope — discussion stayed within the decoder boundary.

</deferred>

---

*Phase: 04-gpt-transformer-decoder*
*Context gathered: 2026-06-05*
