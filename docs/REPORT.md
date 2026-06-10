# PersonaCore — Milestone 1 Technical Report

This report documents the design decisions behind PersonaCore's Milestone 1: a from-scratch
~13.9M-parameter GPT language model, trained on-device, with every load-bearing choice backed
by a unit test, an ablation row, or a training curve. It is organized around decisions, not
chronology: each section states a choice, the rationale, and the evidence that validates it.

## The Thesis, and What This Milestone Claims

PersonaCore's claim is that **memory and personalization can live entirely in the model
weights** — no databases, no vector stores, no prompt-stuffed context, no external files. If
the only place user-specific information exists is the parameters of a model running on the
user's own machine, privacy stops being a policy and becomes a property of the architecture.

That claim is delivered in two milestones:

- **Milestone 1 (this report):** the foundation — a correct, from-scratch GPT decoder, BPE
  tokenizer, training harness, sampling toolkit, evaluation suite, and offline CPU demo. Built
  in pure PyTorch with no HuggingFace model code, on a zero budget, trained on the author's
  own Apple Silicon laptop.
- **Milestone 2 (upcoming):** the weight-memory mechanism itself — from-scratch LoRA adapters
  and EWC continual learning, attached to seams that Milestone 1 deliberately left open.

The honesty bar for this document: **nothing below claims conversational tuning or
personalization as a working feature.** Milestone 1 produces a TinyStories-fluent base model
and proves the engineering is correct enough to carry the novel claim later. Where Milestone 2
machinery appears in this report, it appears as a seam — named, tested, and empty by design.

## What Was Built

A complete small-language-model stack, every component hand-implemented:

- A **GPT-style transformer decoder** with exactly 13,891,584 parameters (tied embedding
  counted once): 6 layers, 6 heads, 384-dim embeddings, 256-token context, dropout 0.0.
- A **byte-level BPE tokenizer** trained from scratch — vocabulary 8192, document separator
  `<|endoftext|>` pinned at id 8184.
- A **hand-rolled training loop**: AdamW, warmup + cosine LR schedule, gradient clipping,
  gradient accumulation, resumable open-dict checkpoints, offline CSV logging.
- A **single shared `generate()`** (greedy / temperature / top-k / top-p) powering the tests,
  the notebook, and the demo.
- An **offline Gradio demo** streaming stories on a laptop CPU at ~95-105 tok/s.

Pure PyTorch throughout. The only external ML library used anywhere is `tiktoken`, and only
inside the test suite as a reference oracle — it is never imported by runtime code, and a
test enforces that.

## Decision: Byte-Level BPE from Scratch, Vocabulary Locked Before Model Sizing

**Choice.** Implement byte-level BPE by hand (train / encode / decode), fix `vocab_size=8192`
and `eos_id=8184` in `ModelConfig` *before any model was sized*, and treat the committed
`artifacts/tokenizer.json` as a frozen, data-only artifact.

**Rationale.** Byte-level base-256 leaves guarantee full input coverage — there is no `<unk>`
token because every byte sequence is encodable. Locking the vocabulary first means a tokenizer
change can never silently invalidate a trained checkpoint: the embedding table's shape is a
constant the rest of the project builds around. The artifact is plain JSON (stdlib `json`,
schema-versioned, id-range-validated) rather than a pickle, because a shippable artifact must
never execute code on load.

**Evidence.** `tests/test_tokenizer_roundtrip.py` proves `decode(encode(x)) == x` over emoji
ZWJ sequences, smart quotes, CRLF, CJK text, and random byte strings.
`tests/test_tokenizer_special.py` proves `<|endoftext|>` encodes to exactly one atomic id
(8184) and is never split or produced by a learned merge (specials are top-pinned at
8184-8191; learned merges occupy the range below). `tests/test_tokenizer_oracle.py` replays
the merge algorithm against tiktoken's `gpt2` ranks and proves lowest-rank-first equivalence —
with a companion guard test asserting no oracle import exists anywhere under
`src/personacore/`. tiktoken is a test oracle, never the implementation.

## Decision: A Bigram Baseline Proved the Harness Before the Transformer Existed

**Choice.** Before writing any attention code, build the *entire* training harness — loop,
checkpointing, LR schedule, eval, CSV logging, sampling — and validate it end-to-end on a
trivial bigram model (`nn.Embedding(V, V)`).

**Rationale.** Training-infrastructure bugs and model bugs are indistinguishable when both
land at once. A bigram model has no attention, no depth, and no init subtleties, so any
failure in the tokenize -> train -> checkpoint -> sample slice is unambiguously a harness bug.
The model contract was locked at this stage — `forward(idx, targets=None) -> (logits, loss)`
with cross-entropy computed on the `(B*T, V)` flatten — so the transformer could later drop in
with the loop untouched.

**Evidence.** `tests/test_overfit_batch.py::test_overfits_single_fixed_batch` drives loss
toward zero on one fixed batch reused every step — the classic harness-correctness gate.
`tests/test_resume_curve.py::test_resume_identical_trajectory` kills a run mid-training,
rebuilds everything from the checkpoint, and asserts the resumed loss trajectory matches an
uninterrupted run within 1e-6 — because the checkpoint restores RNG *state* (not a re-seed),
the trajectory continues bit-for-bit. The payoff came in Phase 4: the real 6-layer GPT passed
the same overfit gate through the byte-identical, untouched `train()` loop.

## Decision: Pre-Norm Decoder Blocks, Mask Before Softmax

**Choice.** Standard-but-hand-built GPT-2 architecture: pre-norm blocks with residual
connections, causal multi-head attention where the future is masked with `-inf` *before*
softmax and scores are scaled by `1/sqrt(d_head)`, a GELU MLP, learned positional embeddings,
and a final `ln_f` before the head.

**Rationale.** Pre-norm is the stable choice for training small models without warmup
gymnastics. Masking before softmax (rather than zeroing after) is the difference between a
model that is causal and one that merely looks causal — applying the mask after softmax leaves
probability mass on future positions. These are exactly the silent-correctness bugs that pass
a smoke test and poison a training run, so each is pinned by a dedicated test.

**Evidence.** `tests/test_gpt_causality.py::test_changing_token_t_cannot_change_earlier_logits`
perturbs token *t* and asserts logits at all positions before *t* are bit-identical — and that
position *t* itself *does* change, so the test cannot pass vacuously.
`tests/test_gpt_layernorm.py` pins the hand-rolled LayerNorm against the reference. The
overfit gate (above) confirms the assembled block stack actually learns.

## Decision: Manual Attention by Hand, with an sdpa Equivalence Path

**Choice.** Implement the attention math explicitly (matmul, scale, mask, softmax, weighted
sum) as the default path, and keep `F.scaled_dot_product_attention` available behind an
`attn_impl="sdpa"` constructor flag.

**Rationale.** The portfolio claim is "I built a transformer," so the attention arithmetic is
written out by hand. But a from-scratch implementation that is *only* from scratch has no
ground truth. Keeping both paths sharing the same q/k/v projections turns PyTorch's fused
primitive into a free differential oracle: if the two paths ever diverge, the manual math is
wrong.

**Evidence.** `tests/test_gpt_attention_equiv.py` asserts manual and sdpa outputs agree within
`atol=1e-5` on identical inputs and weights. This is the same posture as the tokenizer oracle:
from scratch, but verified against the primitive.

## Decision: Weight Tying as a True Shared Tensor

**Choice.** Tie the input embedding and the output head as one shared tensor —
`self.lm_head.weight = self.wte.weight` via `nn.Parameter` assignment after initialization —
not as a value copy.

**Rationale.** At 384-dim embeddings and an 8192 vocabulary, an untied head costs an extra
3,145,728 parameters — over 22% of the model — for marginal benefit at this scale. But weight
tying has a classic failure mode: copying values instead of sharing storage produces two
tensors that *start* equal and silently diverge during training. The distinction is invisible
to a shape check and fatal to the intended parameter budget.

**Evidence.** `tests/test_gpt_weight_tying.py` asserts
`lm_head.weight.data_ptr() == wte.weight.data_ptr()` — storage identity, not value equality.
The cost of untying is also measured empirically: the `no_tie` ablation row (see the ablation
section below) quantifies what those 3.1M extra parameters buy at a fixed training budget.
`tests/test_gpt_param_count.py` pins the deduplicated total at exactly 13,891,584, inside the
10-15M target band.

## Decision: GPT-2-Style Init, Residual Scaling on Both Output Projections

**Choice.** Initialize linear and embedding weights at std 0.02, and scale the
residual-feeding projections — the attention output projection `c_proj` *and* the MLP output
projection `fc_out` — down to `0.02/sqrt(2*n_layer)` (about 0.005774 at 6 layers).

**Rationale.** Every block adds two contributions to the residual stream (attention and MLP),
so activations grow with depth unless the projections writing into the stream are shrunk by
`1/sqrt(2N)`. The common trap is applying the scaling only to attention's `c_proj` and
forgetting the MLP's output projection — the variance argument applies equally to both, and
missing one is invisible until training quality quietly degrades.

**Evidence.** `tests/test_gpt_init.py::test_per_tensor_init_std` checks init std per named
parameter and explicitly asserts that *both* the `c_proj` and `fc_out` suffixes were seen and
scaled — the test fails if either residual projection is missed, so the check cannot pass
vacuously.

## Decision: The Milestone 2 Seams Are Milestone 1 Acceptance Criteria

**Choice.** Treat three structural seams as hard acceptance criteria for Milestone 1, even
though nothing uses them yet:

1. **Every adaptable projection is a separately named `nn.Linear`** — `q_proj`, `k_proj`,
   `v_proj`, `c_proj`, `fc_in`, `fc_out` in every block, called as modules. No fused `c_attn`.
2. **Loss is assembled through `assemble_loss(base, extra_penalties=())`** — an identity
   function in Milestone 1, called on every step by the training loop.
3. **Checkpoints are open dicts** — arbitrary extra keys round-trip through save/load without
   a format change.

**Rationale.** Milestone 2 attaches LoRA adapters to attention projections and adds an EWC
penalty to the loss. If the projections were fused into a single `c_attn`, LoRA would require
surgery on the attention module; because they are named `nn.Linear` modules, LoRA is a wrapper
around existing names. If the loss were computed inline, EWC would mean editing the training
loop mid-Milestone-2; because the loop already calls `assemble_loss`, EWC is one extra entry
in `extra_penalties` with zero loop changes. If the checkpoint schema were closed, storing the
Fisher information and reference weights (`theta_star`) would be a migration; because it is an
open dict, they are just new keys. These seams are the demonstrable difference between "M2 is
planned" and "M2 is plumbed" — the roadmap is real because the code already has the sockets.

**Evidence.** `tests/test_gpt_lora_seam.py` asserts all six named `nn.Linear` projections
exist in every block. `tests/test_assemble_loss.py` proves identity on the empty tuple and
additivity on extra penalties. `tests/test_checkpoint.py` includes an open-dict extensibility
test confirming an arbitrary `fisher` key survives the save/load round-trip unchanged.
