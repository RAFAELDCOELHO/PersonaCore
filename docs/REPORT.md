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

## Decision: fp32 On-Device Training on Apple Silicon as the Primary Run

**Choice.** Run the 50,000-step pretraining locally on Apple Silicon (M3, MPS backend) in
plain fp32 — no mixed precision, no `GradScaler`, no `torch.compile` — with the Kaggle P100
(fp16 AMP + `GradScaler`) kept as a documented fallback path rather than the default.

**Rationale.** Training on the author's own machine is thesis reinforcement: a model that
claims on-device privacy should itself be trained on-device, with zero external compute
dependency. The technical constraints align with the thesis — MPS has no fp16-AMP path, so
fp32 is the correct posture there, and a `bf16`-on-Pascal guard raises a clear error so the
fallback can never silently run an unsupported precision. The price of local training is that
runs span laptop sleeps and interruptions, which is why resumable checkpoints are
load-bearing, not a convenience: the open-dict checkpoint carries model, optimizer, scheduler,
step, full RNG state, the (fallback-only) scaler state, the config, and the git SHA.

**Evidence.** `tests/test_resume_curve.py::test_csv_curve_survives_restart` kills a run,
resumes from the checkpoint, and asserts the logged loss curve reproduces row-for-row against
an uninterrupted run — possible because resume restores RNG *state* rather than re-seeding,
and the CSV clock is step-derived rather than wall time. A companion test proves the scaler
state itself round-trips through the checkpoint, so the fp16 fallback resumes correctly too.

## Decision: A Hand-Rolled Training Loop with Offline CSV Logging

**Choice.** AdamW with a hand-written warmup + cosine LR schedule (wrapped in `LambdaLR` so
it participates in the checkpoint's `state_dict` resume contract), gradient clipping,
configurable gradient accumulation — and experiment logging as a plain CSV file
(`step,train_loss,val_loss,lr,tokens,wall_clock`) instead of any hosted dashboard.

**Rationale.** Writing the schedule by hand fits the from-scratch ethos and is small enough to
test directly. On the fp16 fallback path, the loop enforces the one ordering that mixed
precision actually requires — scale, backward, *unscale before clip*, step, update — because
clipping scaled gradients clips the wrong thing. SaaS loggers (wandb and friends) were
rejected deliberately: they add accounts, API keys, and network calls to a project whose
entire point is offline, zero-budget, on-device operation. A CSV survives restarts by
appending and is trivially reproducible.

**Evidence.** The committed `results/run.csv` carries 200 logged evaluations across the
50,000-step production run — the same file the demo notebook plots. AMP-ordering and
gradient-accumulation-equivalence are pinned by dedicated loop tests
(`tests/test_train_loop.py`), and the schedule's resume behavior by
`tests/test_lr_schedule.py`.

## Decision: Perplexity with an Auditable Denominator

**Choice.** Report held-out perplexity from a deterministic full-validation sweep:
`perplexity()` ignores the forward pass's mean loss, recomputes cross-entropy from the logits
with `reduction="sum"` over non-overlapping windows of the validation memmap, and returns
`(ppl, total_tokens)` — the number and its denominator together.

**Rationale.** A perplexity without a token count is unauditable: random-batch estimates move
with the sampler, and mean-of-means averaging quietly weights windows unequally. Summing the
loss and dividing by the exact count of scored target tokens makes the headline number
reproducible to the digit by anyone with the checkpoint and the validation file. This is also
why the report distinguishes the headline from the coarse random-batch estimate (about 2.09)
that `best.pt` recorded at save time: the deterministic sweep is the citable figure.

**Evidence.** `tests/test_perplexity.py` validates the sweep against a brute-force oracle and
pins the token-accounting arithmetic (the denominator is `corpus_len - n_windows`, exactly).
The headline: **full-validation perplexity 2.1066 over 12,636,922 scored target tokens**, on
the 50k-step `best.pt`, computed by `scripts/evaluate.py`.

## Decision: An Architecture Ablation Cohort, Honestly Bounded

**Choice.** Justify the architecture choices empirically with a four-run ablation cohort —
baseline, untied embeddings, no positional embeddings, half depth — trained through the
untouched `train()` harness at an identical, deliberately reduced budget, and never compared
against the headline number. The ablation knobs are *additive* `ModelConfig` flags
(`weight_tying`, `use_pos_emb`, both defaulting to `True`), so the default config reproduces
the production architecture bit-for-bit.

**Rationale.** "I chose weight tying" is an assertion; an ablation row is evidence. But
honest ablations at zero budget require honest framing: 50k steps per variant was not
affordable, so the cohort runs 2,500 steps per variant with everything held identical except
one knob. That makes the numbers comparable to each other and *only* to each other. The table
below is reproduced from `results/results.md` together with its caveat, verbatim:

> **Reduced-budget, self-consistent cohort (D-06).** All four runs below train through
> the UNTOUCHED `train()` harness at IDENTICAL seed (1337), data, LR, warmup, and
> budget (`max_steps=2500`, calibrated per D-07) — only the ablated knob
> differs. The numbers are comparable to EACH OTHER, NOT to the headline 50k `best.pt`.
>
> The headline production figure is reported SEPARATELY (EVAL-01, `scripts/evaluate.py`):
> deterministic full-val perplexity **2.1066** over **12,636,922** scored target tokens
> on the 50k-step `best.pt` — a different (larger) budget, listed here only for context.

| Variant | Param count | Held-out PPL (reduced budget) | Best val-loss | What this shows |
| --- | --- | --- | --- | --- |
| baseline | 13,891,584 | 2.8212 (over 12,636,922 tokens) | 1.0426 | The fair reference — full 6-layer tied + positional arch at the reduced budget. |
| no_tie | 17,037,312 | 2.7870 (over 12,636,922 tokens) | 1.0312 | Whether sharing the input/output embedding helps (or hurts) at this scale. |
| no_pos | 13,793,280 | 2.9221 (over 12,636,922 tokens) | 1.0796 | Whether the learned positional embedding is load-bearing for coherence. |
| depth_cut | 8,568,192 | 3.0074 (over 12,636,922 tokens) | 1.1078 | The depth-vs-params tradeoff: half the layers (~38% fewer params), equal budget. |

**Reading the rows.** *no_tie* posts the best raw perplexity of the cohort (2.7870 vs the
baseline's 2.8212) — but it spends 3,145,728 extra parameters, a 23% size increase, to buy
that 0.034. Per parameter, tying is clearly the better trade at this scale, which is why the
production model ties; the row quantifies the cost of the decision rather than pretending
there is none. *no_pos* degrades to 2.9221: the learned positional embedding is load-bearing,
which is notable because it is the cheapest component ablated — only 98,304 parameters.
*depth_cut* is the worst of the cohort at 3.0074 despite keeping the full embedding budget:
at fixed training budget, halving depth hurts more than its ~38% parameter reduction alone
would suggest. These are relative signals at a reduced budget — none of them extrapolates to
the 50k-step regime, and the report does not claim otherwise.

**Evidence.** `tests/test_ablation_config.py` pins the flag semantics and the exact per-variant
parameter counts; the four training curves are committed as `results/abl_*.csv`.

## Decision: One Shared generate() for Tests, Notebook, and Demo

**Choice.** A single decoding path — `generate()` in `src/personacore/generation/` — serves
every consumer: unit tests, the demo notebook, and the Gradio app. It implements greedy,
temperature, top-k, and top-p sampling in a fixed composition order, stops on EOS (trimming
the EOS token rather than emitting it), respects `max_new_tokens`, and crops the context to
the last `block_size` tokens each step so generating past the context window never crashes.

**Rationale.** Three slightly different sampling loops in three consumers is how a demo ends
up showing behavior the tests never exercised. One shared implementation means the
determinism, EOS, and bounds guarantees proven in CI are exactly the guarantees the demo
runs. The sampling primitives are individually testable (the top-p nucleus math is pinned
exactly), and edge cases are guarded — `top_k <= 0` is an explicit no-op rather than a crash.

**Evidence.** `tests/test_generation.py` covers output shape, determinism under a fixed seed
with greedy decoding, EOS-stop-with-trim, the past-`block_size` no-crash contract, and the
nucleus-sampling exactness pin. `tests/test_generation_text.py` covers the streaming
string-to-string wrapper (cumulative-buffer delta decode) used by the demo.

## Decision: A Slim Shippable Artifact That Never Executes Code on Load

**Choice.** Ship inference weights as a slim `torch.save` dictionary —
`{schema_version, model, model_config, git_sha, step, val_loss}` — that loads under
`torch.load(..., weights_only=True)`, with `load_slim()` as the single load path for every
consumer. The full training checkpoint `best.pt` (159 MB, with optimizer, scheduler, and RNG
state) stays an internal, local-only artifact.

**Rationale.** A pickle that executes arbitrary code on load is acceptable only for one's own
trusted resume file, never for an artifact other people download. `weights_only=True` uses
PyTorch's restricted unpickler — plain containers and tensors only, zero code execution —
which is the same precedent set by the tokenizer's data-only JSON in Phase 2. The artifact
carries its own `model_config` and git SHA (3a46815, step 49000), so a consumer reconstructs
the exact architecture from the file itself with no out-of-band knowledge. At ~55.6 MB
(torch serializes the tied embedding storage once), it is small enough to distribute.

**Evidence.** `tests/test_slim_checkpoint.py` asserts the exact key set, the
`weights_only=True` load, provenance travel, and — on the rebuilt model — that weight tying
survived the round-trip (`data_ptr()` identity) with the parameter count still exactly
13,891,584.

## Decision: An Offline Story-Completion Demo, Not a Fake Chatbot

**Choice.** The demo is a Gradio 5 `ChatInterface` running entirely on localhost
(`share=False`), framed explicitly as *story completion*: type an opening line, the model
continues it as a TinyStories-style story. Telemetry is disabled twice over
(`GRADIO_ANALYTICS_ENABLED=False` set before the import, plus `analytics_enabled=False`),
which also suppresses the version-check ping; the UI fonts ship inside the Gradio wheel, so
the demo makes zero outbound network calls.

**Rationale.** The honest framing matters: this model has no conversational tuning, and a chat
metaphor would imply otherwise. Story completion shows exactly what the model is — a fluent
TinyStories generator — in a UI that streams tokens as they decode. Offline operation is not
cosmetic; it is the on-device thesis demonstrated live. A KV-cache was considered and measured
out: at **~95-105 tok/s** sustained on a laptop CPU (manual attention ~95, sdpa ~105), a
complete ~200-token story streams in about 2 seconds — roughly ten times faster than reading
speed — so the cache stays deferred to Milestone 2.

**Evidence.** Throughput was measured on the real 13.9M-parameter checkpoint through the same
`generate_text` path the demo uses. The offline-launch behavior (analytics env var, local
fonts, localhost binding) was verified against the Gradio 5.50 wheel source.

## Results

**Model.** 13,891,584 parameters (tied embedding counted once): 6 layers, 6 heads,
`n_embd=384`, `block_size=256`, vocabulary 8192, dropout 0.0, weight tying, learned
positional embeddings.

**Headline.** Deterministic full-validation perplexity **2.1066 over 12,636,922 scored target
tokens** (50k-step `best.pt`, `scripts/evaluate.py`).

**Training curve.** From `results/run.csv` (200 logged evaluations, one per 250 steps):
validation loss falls from 2.38 at step 250 (random init starts at ln(8192) ~ 9.01) to 1.11
by step ~2,750, 0.91 by ~10k, 0.81 by ~25k, reaching its best value of 0.7378 at step 49,000
— the checkpoint promoted to `best.pt`. Train and validation loss track closely for the whole
run; at this model-to-corpus ratio there is no overfitting signal. The learning rate warms up
to 3e-4 and cosine-decays to 3e-5.

**Throughput.** ~95-105 tok/s sustained CPU streaming (manual attention ~95 tok/s, sdpa ~105
tok/s); a ~200-token story completes in about 2 seconds.

**Qualitative samples.** As in `results/samples.md`, these are representative, not
cherry-picked — fixed prompts, with both deterministic greedy and warm (temperature 0.8,
top-p 0.95) continuations captured. Two excerpts:

> Once upon a time, there was a little girl named Sue. Sue loved to play with her toys and
> eat yummy food. One day, Sue found a big box in her room. She was very excited to see what
> was inside. *(greedy)*

> The little robot had a big head. He liked to play with his friends. One day, he saw a big
> box. The robot wanted to move and play with the box. The robot tried to push the box, but
> it was too heavy. *(warm, temperature 0.8 / top-p 0.95)*

The model writes coherent, grammatical children's stories with consistent characters across
sentences — the intended TinyStories fluency bar for a 13.9M-parameter model. It also shows
the expected small-model failure modes (occasional referent drift: "Tom and Tom"), which the
samples file preserves rather than edits out.

## Reproducibility

The reproducibility guarantee is **seed + git SHA + config-in-checkpoint**:

- Development and training run inside a pinned Python 3.11 virtual environment (the supported
  target for the torch wheels and CI); the suite is CPU-only and green — 126 passed, 1 skipped
  (a CUDA-only fp16 smoke test, skipped by design off-GPU).
- `seed_everything()` seeds `random`, NumPy, and torch (including CUDA when present) and
  disables the cuDNN autotuner.
- Every checkpoint — including the slim shipped artifact — embeds its `ModelConfig` and the
  git SHA of the code that produced it (`best.pt`: 3a46815, step 49000), so any number in this
  report traces to a commit.
- On resume, RNG *state* is restored rather than re-seeded, so an interrupted run continues
  the same trajectory bit-for-bit (asserted within 1e-6 by the resume tests).

## Limitations and the Milestone 2 Roadmap

**What this model is not.** It speaks TinyStories — simple childlike English in a 256-token
context — because that is the corpus that maximizes coherence-per-parameter at 13.9M. It has
no dialogue tuning: the demo is story completion, not conversation. And, most importantly,
**it has no personalization yet**: the PersonaCore thesis — memory living in the weights — is
not demonstrated by Milestone 1. Milestone 1's claim is narrower and fully delivered: the
foundation is correct, tested, and structured so the thesis mechanism can be added without a
rewrite.

**Milestone 2 (upcoming).** The plan attaches directly to the seams documented above:

- **From-scratch LoRA adapters** on the six named `nn.Linear` projections — the weight-memory
  write mechanism.
- **EWC continual learning** added as a `fisher_penalty` entry in `assemble_loss`'s
  `extra_penalties`, with the Fisher state stored as new keys in the open-dict checkpoint.
- **Teach-then-recall demo:** teach the model a fact in conversation, wipe all context, and
  show it recalls from weights alone — the clean-room proof that memory is in the parameters.
- **No-forgetting A/B:** the same continual-learning run with and without EWC, with
  forgetting curves and weight-delta visualizations.

A strided (sliding-window) perplexity variant — which would give most tokens more left
context and score slightly lower than the non-overlapping sweep — is noted as future work in
`results/results.md`; because the bias is uniform across variants, the ablation ranking is
unaffected.

## Where to Go Next

- **README.md** — the project front door: quickstart, the demo GIF, and the headline numbers
  at a glance.
- **demo.ipynb** — the executed evidence notebook: the model loaded from the slim artifact,
  exact parameter count, training curves from `results/run.csv`, the ablation plots, and a
  seeded sampling-settings tour.
- **results/** — the committed evaluation artifacts this report cites: `results.md`
  (ablation cohort), `samples.md` (qualitative samples), and the raw curve CSVs.
