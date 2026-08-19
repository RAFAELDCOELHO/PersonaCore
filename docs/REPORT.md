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
- A **byte-level BPE tokenizer** trained from scratch — vocab table 8192 with 547 ids live
  (256 bytes + 283 learned merges + 8 specials; the remaining 7645 rows are reserved
  capacity), document separator `<|endoftext|>` pinned at id 8184.
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

**What actually trained.** Training learned 283 of the 7,928 requested merges before the
bounded TinyStories corpus exhausted its mergeable pairs — the trainer itself warns
"corpus exhausted: learned 283 of 7928 requested merges; vocab_size=8192 has 7645 dead ids".
The *effective* vocabulary is therefore 547 live ids (256 bytes + 283 learned merges + 8
specials); the locked 8192-row table is reserved capacity. The trade-off is stated plainly:
shape stability for every downstream checkpoint, in exchange for 7645 dead rows the model
carries in its embedding table.

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

**Rationale.** At 384-dim embeddings and an 8192-row vocab table, an untied head costs an extra
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
fonts, localhost binding) was verified against the Gradio 5.50 wheel source. The demo also
masks the 7645 tokenizer-undecodable ids out of the logits before sampling — an optional
`forbid_ids` mask threaded through the from-scratch sampling path and built once at launch
from the frozen tokenizer's live vocabulary — so every slider setting the UI offers,
temperature 1.5 with top-k disabled included, can only produce decodable ids
(`tests/test_forbid_ids.py` pins this, including at the exact settings that previously crashed).

## Results

**Model.** 13,891,584 parameters (tied embedding counted once): 6 layers, 6 heads,
`n_embd=384`, `block_size=256`, vocab table 8192 (547 ids live), dropout 0.0, weight tying,
learned positional embeddings. Of the headline count, 2,935,680 parameters (7645 dead rows
× 384 dims, ~21%) are embedding rows for ids that can never occur in the training data or
be decoded — counted in the headline because they are part of the shipped tensor.

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
  target for the torch wheels and CI); the suite is CPU-only and green, with the only skip a
  CUDA-only fp16 smoke test skipped by design off-GPU.
- `seed_everything()` seeds `random`, NumPy, and torch (including CUDA when present) and
  disables the cuDNN autotuner.
- Every checkpoint — including the slim shipped artifact — embeds its `ModelConfig` and the
  git SHA of the code that produced it (`best.pt`: 3a46815, step 49000), so any number in this
  report traces to a commit.
- On resume, RNG *state* is restored rather than re-seeded, so an interrupted run continues
  the same trajectory bit-for-bit (asserted within 1e-6 by the resume tests).

---

## Milestone 1 Ends Here — Everything Below This Line Is As Written on 2026-06-10

**Read the next two sections as a dated snapshot.** Everything from here to the end of
`## Where to Go Next` is preserved exactly as it shipped with the `m1-demo-v1` release tag on
**2026-06-10**, and is **not** amended — this project's rule is that recorded text stands as
written, with corrections dated and appended rather than edited in place.

Two clauses below have since been overtaken. Its "Milestone 2 (upcoming)" bullets are no longer
upcoming, and its "**it has no personalization yet**" clause was true of Milestone 1 as scoped
and has since been delivered. Both stand unedited.

What actually shipped is recorded in the Milestone 2 sections appended after
`## Where to Go Next` — the choices in the new `## Decision:` sections, the outcomes in
`## Milestone 2 Results: What Three Experiments Showed`, and every bound on those outcomes in
`## Milestone 2 Limitations — Nine Honest Negatives, Quoted`.

---

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

## Milestone 2 Begins Here — Weight-Based Memory

Everything below this line is Milestone 2 material, written after the v1.0 report above. It
follows the same organization: each choice gets a `## Decision:` section stating the choice, the
rationale, and the alternative that was rejected; the outcomes live separately in
`## Milestone 2 Results: What Three Experiments Showed`; and every bound on those outcomes is
aggregated in `## Milestone 2 Limitations — Nine Honest Negatives, Quoted`.

The two halves are deliberately non-overlapping. A reader auditing a specific choice can read the
Decision sections alone; a reader asking what the milestone actually proved can read the results
narrative alone. Neither is the other's summary.

## Decision: Two Mechanisms in Two Stages, Not One Combined Run

**Choice.** Split the weight-memory claim across two mechanisms and two stages. Forgetting is
studied with a **full fine-tune A/B** — the same dialogue run twice, with and without an EWC
penalty on the loss, one configuration bit apart. Personalization is taught with a **from-scratch
LoRA adapter on the frozen conversational base**, and the adapter is never shipped merged.

**Rationale.** The thesis has two halves that fail in different ways: writing user-specific
information into weights, and not destroying the base model doing it. Each half needs its own
control. The A/B's whole evidentiary value is that its two arms differ *only* in the penalty, so
any retention difference is attributable to EWC and nothing else — a full fine-tune is the regime
where catastrophic forgetting actually happens, which is what makes the comparison worth running.
The personalization half needs the opposite property: a mechanism whose write surface is small and
inspectable, kept unmerged so `scale·B@A` remains recoverable as a first-class object for both the
weight-delta figure and the adapter-on/adapter-off toggle the recall control depends on.

**The alternative rejected.** One combined mechanism — teach the persona through a LoRA adapter
with an EWC penalty attached, and read both claims off the single run. It was rejected because it
answers neither question cleanly. A LoRA adapter already constrains movement by construction, so
an EWC penalty layered on top has no isolable effect to measure; and an adapter-off arm is not a
no-EWC arm, so the forgetting comparison would have lost its control. Two stages cost a second
training run and buy two claims that can each be falsified on their own terms.

## Decision: The Tokenizer Stays Frozen for v2.0, and the Inflation Tax Is Measured Rather Than Assumed

**Choice.** Carry `artifacts/tokenizer.json` into Milestone 2 unchanged — no retrain, no new
merges, no vocabulary change — so the 50k-step `best.pt` remains a valid Milestone 2 base. The
547-live-id vocabulary is handled downstream by the `forbid_ids` dead-id mask rather than by
regenerating the artifact, and the cost of tokenizing conversational text through a
TinyStories-trained tokenizer was **measured before any training bin was built**, against a
TinyStories baseline recomputed in the same run through the same word-count rule.

**Rationale.** Milestone 1 locked `vocab_size` before the model was sized precisely so that a
tokenizer change could never silently invalidate a trained checkpoint. Retraining the tokenizer
for dialogue would cash in that guarantee at the worst possible moment: every checkpoint, every
recorded perplexity, and every ablation row above would become uncomparable to anything Milestone
2 produced, and the v1.0 report's headline number would stop tracing to a runnable artifact. The
inflation cost of *not* retraining is real, so it was quantified rather than waved at — with
pre-registered GO/ADAPT/STOP bands locked before the measurement ran, so the answer could not be
graded after the fact.

**The alternative rejected.** Retrain the BPE tokenizer on PersonaChat, or on a PersonaChat +
TinyStories mixture, to reduce fragmentation on conversational text. Rejected because it
invalidates every committed checkpoint and every number in the report above for a gain that the
measurement showed was not needed. The honest cost of the rejection is recorded rather than
hidden: the inflation ratio is reported with its denominators, and it is explicitly not
comparable to any other tokenizer.

## Decision: Pre-Registration Lives in Committed Code, Before Any Number Exists

**Choice.** Every gate in Milestone 2 is a module-level literal in a committed driver, pushed
**before** the run that produces the number it judges. The λ-sweep rules live in
`scripts/finetune_smoke.py`; the A/B's retention gate and its margin constant live in
`scripts/finetune_ab.py` at `c3d942e`; the recall thresholds were derived on a disjoint
calibration fact set and committed with their derivation report before the real run existed; the
Fisher/Δ correlation's statistic, predicted sign, seed, resample counts and gate rule live in
`scripts/phase15_stats.py`, committed before the artifact it reads was generated. The verdicts are
computed by **importing those modules' own constants and gate functions**, never re-derived by
hand in prose. Git history is the proof, and each report opens with a pre-registration table
naming the commit where each constant was locked.

**Rationale.** A threshold chosen after seeing the data is not a threshold, and no amount of
after-the-fact honesty recovers it. Putting the rule in committed code makes the ordering a fact
about the repository rather than a claim in a paragraph: anyone can check that the gate commit
precedes the artifact commit. Importing the constant instead of retyping it closes the second
half of the same gap — a report that hardcodes `MARGIN = 0.137860` in its prose can drift from the
driver that actually ran, and the drift is invisible.

**The alternative rejected.** Run the experiment, look at the numbers, then write down the
criterion they meet — the default in exploratory work, and the one that makes a negative result
impossible to publish because the bar moves to wherever the result landed. It was also rejected in
its softer form: writing the rule down first *in prose only*, which leaves nothing structural to
verify and nothing to import.

## Decision: Gate Only the Part of a Claim the Sample Size Supports

**Choice.** Where a claim has a falsifiable core and a descriptive periphery, gate the core and
report the periphery without a pass/fail. In the forgetting A/B, the **retention** side carries
the pre-registered gate and the **acquisition** side is descriptive with no threshold. In the
Fisher/Δ correlation, the **sign** is gated — a positive coefficient whose bootstrap CI excludes
zero — and the **magnitude** is descriptive. Both descriptive halves are still reported in full,
with their confidence bounds, never omitted.

**Rationale.** Gating is only meaningful when the measurement can actually support a threshold.
The acquisition side of the A/B is the expected, non-binary half of a known stability–plasticity
trade-off; inventing a margin for it would manufacture a pass/fail out of a continuum. The
correlation is computed over 36 cells, which is enough to establish a direction and not enough to
license a point estimate read as an effect size. Reporting a magnitude under a gate would invite
exactly that misreading. The two halves fail differently, so they are judged differently — and
saying which half is falsifiable is itself part of the claim.

**The alternative rejected.** Two opposite errors, both declined. Exempting the descriptive half
from reporting entirely — which would let the A/B show a retention win bought by simply failing to
learn the task, and let the correlation's verdict travel without the width of its interval. And
gating the descriptive half anyway, with a threshold no sample size justifies, which converts a
judgment call into a number that merely looks rigorous. The gate boundary was also settled *before*
any correlation was computed, because the rule initially admitted two contradictory readings and
resolving that ambiguity after seeing the coefficient would have been resolving it in whichever
direction looked better.

## Decision: Honest Negatives Stand Unamended; Discretionary Continuations Are Logged Separately and Dated After

**Choice.** A recorded verdict is never edited in place. When later work continues past a negative
result, the continuation is a **separate, dated section written after it**, explicitly marked as
not amending what it follows. Phase 12's λ-sweep verdict stands exactly as recorded, and the
subsequent choice to run production at λ=0.01 is a distinct, later, discretionary decision
recorded alongside it rather than folded into it. The recall phase's ship decision is separated
from its gate verdict the same way. When Milestone 2's correlation verdict landed in a report
written by an earlier phase, it was **appended** as a dated section carrying an explicit
separation note, with the prior phase's pre-registered content left byte-untouched. The same rule
is why the v1.0 report above is extended rather than corrected.

**Rationale.** The value of a recorded negative is entirely in the fact that it was recorded
before anyone knew whether it would be convenient. Editing it later — even to add a true and
useful clarification — destroys exactly that property, and does so invisibly, because the edited
text still reads as if it were written at the original date. Dated appending keeps both the
original judgment and the later one legible, and lets a reader see which came first.

**The alternative rejected.** Revising a verdict in place once the picture improved, or quietly
dropping a superseded negative from the narrative. Both are the same move: making the record agree
with the current best understanding at the cost of making it stop being a record. The cost of the
rule is accepted openly — this report carries text that is now known to be wrong, and corrects it
by dated note rather than by edit.

## Decision: Structural Enforcement Replaces Declared Invariants

**Choice.** Every load-bearing invariant in Milestone 2 is enforced by a mechanism that fails
loudly, not by a sentence claiming it holds. The demo's dead-id mask is checked by comparing the
actual mask object the sampling path receives against the one built from the tokenizer, not by
asserting they match. "No fact value ever reached a scored prompt" is enforced by checking each
prompt's **token ids** for the value's encoded id run and raising on a hit, not by a review of the
prompt templates. "The plotting module cannot open a checkpoint" is enforced by an AST walk over
the module's imports plus a fresh-interpreter subprocess import that fails if `torch` lands in
`sys.modules` — two checks because the AST cannot see a transitive import.

**Rationale.** This is the direct response to the failure mode Milestone 2's own learnings named
as its most recurring: an invariant that is *declared* — in a docstring, a comment, or a report
paragraph — and never *structurally* held. A declared invariant is true on the day it is written
and silently false after the next refactor, and nothing in the repository notices. A structural
one is checked on every run of the suite. The discipline extends to the guards themselves: the
plotting guard was watched failing against a deliberately introduced `import torch` before it was
trusted, because a guard nobody has observed fail is a guard nobody has verified.

**The alternative rejected.** A docstring or report sentence asserting the same property — cheaper
to write, indistinguishable from the enforced version to a reader, and worth nothing. It was
rejected for the third time in this project, after the same conversion was made for the demo's
mask comparison and the prompt token-id check.

## Decision: Extract Once, Then Plot From the Committed Artifact Only

**Choice.** Split figure generation into two tiers with a hard boundary. One script reads the
gitignored training checkpoints and writes a single small committed JSON artifact,
`results/phase15_norms.json`, carrying every number the figures draw plus the regime, parameter
count, training budget and comparison-basis fields that say what each block may be compared
against. A second script reads **only** that artifact and is structurally forbidden from opening a
checkpoint. The same artifact feeds the figures, the report's per-layer disclosure, and the
correlation statistic — one source of truth, not three.

**Rationale.** A committed PNG whose inputs are gitignored is an assertion, not evidence: nobody
with a fresh clone can regenerate it, and nobody can check a number in it without the artifacts
the clone does not contain. Splitting the tiers makes regenerability true by construction rather
than by claim — the plotting half runs in the CPU-only suite on committed data, and the extraction
half's docstring names the six specific checkpoints it needs (`scripts/extract_deltas.py` records
them at ~914 MB) and states plainly that re-extracting against a future checkpoint requires a
fresh manual run producing a fresh committed artifact, not a test that stays green while checking
nothing.

**The alternative rejected.** One convenient script that loads the checkpoints and plots in a
single pass. It is less code and it is what the figures originally needed, but it makes the
committed image unreproducible from the committed repository and leaves the caption's numbers with
no auditable source. The boundary also had to be structural rather than conventional for the same
reason the previous decision gives: a plotting module that merely *promises* not to read a
checkpoint acquires a `torch.load` the first time that is convenient.

## Milestone 2 Results: What Three Experiments Showed

**The claim under test.** Milestone 2 set out to show that a user-specific fact can be written
into a model's parameters, recalled from weights alone with the context wiped, and that the
mechanism which protects the base model from being destroyed in the process actually works.
Three experiments were run against that claim, plus one measurement taken before any of them.
What follows is what they returned. Every choice behind them is justified in its own
`## Decision:` section above; none of that reasoning is repeated here.

**The λ search that found nothing.** The first attempt to demonstrate EWC was a sweep for a λ
that buys retention essentially for free — the largest λ whose end dialogue perplexity stays
within a pre-registered margin of the λ=0 run, subject to a demonstrability guard requiring its
retention to beat λ=0 by more than the measured noise floor. At the 1250-step smoke budget, **no λ
satisfied both rules**: every arm beat the collapse baseline on retention, and every arm fell
outside the dialogue margin. The pre-registered all-fail outcome was recorded — λ\* = None,
demonstrable = False — and it stands unamended in `results/finetune_smoke_report.md`. The
production λ=0.01 used by everything downstream was a **separate, later, discretionary decision**,
logged after that verdict and dated after it. It is not an amendment of it, and the negative
result was not retroactively converted into a positive one by the choice that followed.

**The A/B that did demonstrate it.** The demonstration ran at the full 4000-step budget as a
proper A/B: two arms, identical in every respect except the EWC penalty. From a shared step-0
anchor of retention perplexity **2.107553076833866**, the naive arm ended at
**8.52417066884246** and the EWC arm at **3.8911400839446597** — a retention drift of
**+6.416618** against **+1.783587**, a factor of **3.6** in how much of the base task each arm
destroyed. The pre-registered gate is `MARGIN = 2 × 0.068930 = 0.137860`, twice the seed-to-seed
retention noise floor; the observed separation clears it by **33.61×**. Both arms learned the
dialogue task: EWC's acquisition cost was **+0.380556** perplexity (about 9.1% relative), which
is reported **descriptively, with no gate**, and which is what makes the retention result
meaningful — the win was not bought by failing to learn.

The scope of that verdict is exactly what the gate measures: **teacher-forced retention
perplexity on the frozen sub-bin**. It is not a claim about free-running story generation, and
the free-running axis returned a measured negative — mid-story role-token leakage of **79
(naive) vs 69 (EWC)** across 20 generations per arm, i.e. both arms drop out of story mode into
dialogue, and EWC only slightly less often. That negative is reported alongside the positive one
rather than behind it.

**The clean-room teach-then-recall.** The personalization half was run as a closed-book test:
teach facts through a LoRA adapter, wipe the context entirely, and ask. Taught-template recall
came in at **496/1008 = 0.4921** against a threshold of **0.2486**; held-out template families —
the tier that distinguishes an internalized fact from a memorized phrasing — came in at
**326/936 = 0.3483** against **0.2000**. Both gates **PASS**. The closed-book control, the same
weights and the same prompts with the adapter flags flipped off, scored exactly **0/2430**. Both
thresholds were derived from a **disjoint** calibration fact set and committed at
`CALIBRATION_SHA 0425fdc4…` before the real run existed, and every scored prompt's token ids were
recorded before the model was called, with a hard check that no fact value ever appeared in a
prompt. The recorded verdict is **ADAPT** — GO with two qualifications. Both qualifications are
reproduced in the Limitations section below.

**The tokenizer-inflation tax.** Before any of the above, the cost of pushing conversational text
through a TinyStories-trained tokenizer was measured: dialogue tokenizes at **3.229** tokens per
word over 4,800,385 utterance tokens and 1,486,754 whitespace words, against a TinyStories
baseline of **2.860** recomputed in the same run through the same word-count rule — a relative
inflation of **1.129×**, inside the pre-registered GO band of ≤1.2×, with 0.9996 of episodes
fitting persona plus first exchange inside the 256-token context. The qualifier travels with the
number: that ratio is only meaningful against the same-run baseline, and it is **not comparable to
any other tokenizer**, word-count rule, or serialization format.

### The Two Signature Figures

Two figures carry the weight-side evidence, and both are drawn from a single committed artifact,
`results/phase15_norms.json`, rather than from the checkpoints themselves. Their in-figure text
carries a terse version of what follows; this section is the full version. A reader comparing the
two should find **different amounts of detail, never different things** — the layer and projection
names below are read from the same artifact fields the figure captions render.

**VIZ-02, `results/phase15_adapter_delta.png`** — the LoRA adapter's relative Frobenius change
`‖ΔW‖_F/‖W₀‖_F` on the 6-layer × 6-projection grid, log color scale, computed from `scale·B@A`
on the unmerged adapter against the frozen conversational base. **VIZ-03,
`results/phase15_fisher_ewc.png`** — three panels: the Fisher diagonal at `best.pt`, and the naive
and EWC full-fine-tune delta grids over the same 36 cells.

**Which panels share a scale, and why one does not.** In VIZ-03 the **naive and EWC panels share
one color-scale object** — literally one norm instance passed to both, not two instances that
happen to carry equal bounds — because those two arms share a comparison basis: same `W₀`, same
4000-step budget, same configuration, one bit apart. They are cell-for-cell comparable and the
figure is built so a later "brighten this panel" edit cannot silently split them. **The Fisher
panel keeps its own scale, and its own colormap.** This is a **units argument, not a convenience
argument**: a Fisher cell is a squared-gradient magnitude normalized so that 1.0 means "the
importance of an average parameter", while a delta cell is a dimensionless weight-change ratio.
The two quantities are not commensurable, so putting them on one scale would assert a comparison
that does not exist. The exemption is for incommensurable units only — it is not a licence to
rescale a panel that looks inconvenient.

**The flatness is the finding.** Under the shared scale the EWC panel reads as visibly darker and
flatter than the naive panel. That is the result, not a rendering artifact and not a reason to
rescale: EWC's largest cell is **62.7%** of naive's largest, its median cell is **40.9%** of
naive's median, and **34 of 36** cells moved less under EWC. The shared bounds span
**(0.04211054267645148, 0.22023983403635128)** — only **0.719 decades**, so the compression is
genuinely mild and the panel is darker rather than washed out. The shared minimum is an EWC cell
and the shared maximum is a naive cell, which is the arithmetic form of the same observation.

**EWC did not reduce movement everywhere, and the figure should not be read as saying so.** Two of
the 36 cells moved *further* under EWC — layer 0's `q_proj` (signed reduction **−0.015185**) and
layer 1's `q_proj` (**−0.006607**). Both are inside the correlation reported below; none of the 36
signed values was filtered out.

**Outlier disclosure — what drives each color range.** These are read from the artifact's
`vmax_driver` fields, not re-derived:

| Block | Range driver | Value |
| --- | --- | --- |
| adapter (VIZ-02) | layer 1's `c_proj` | `0.04738638857364279` |
| naive (VIZ-03) | layer 1's `c_proj` | `0.22023983403635128` |
| EWC (VIZ-03) | layer 1's `q_proj` | `0.13806389791647683` |
| Fisher (VIZ-03) | layer 0's `c_proj` | `6.541458482610652` |

In each case that layer and projection dominates the range; the full per-layer distribution is in
`results/phase15_norms.json`. The adapter's own range spans 0.400 decades and the Fisher range
spans 2.129 decades — the Fisher panel is by far the most heavy-tailed of the four, which is the
other reason it is not forced onto a shared scale. **All four blocks report
`nonpositive_cells` = 0** — stated from that artifact field rather than inferred from the figures
looking clean — so the log scale masks nothing in either image and the "masked cell" grey never
appears.

**VIZ-02 and VIZ-03 are NOT comparable to each other**, despite sharing the
`‖ΔW‖_F/‖W₀‖_F` formula — the shared formula is exactly what invites the comparison that is
invalid. Three concrete confounds, not "different regimes":

1. **Parameter count.** The adapter writes through **331,776** LoRA parameters; the full
   fine-tune arms move all **13,891,584** model parameters.
2. **Training budget.** The adapter comes from a 200-step LoRA teaching run at batch 8; the naive
   and EWC grids come from a 4000-step full fine-tune at batch 32.
3. **A smaller absolute ΔW magnitude for the adapter does NOT imply more conservative or less
   effective learning.** It reflects the adapter's parameter budget, not a quality comparison.

The same statement is machine-readable in the artifact's `comparison_basis` block, which records
`naive_vs_ewc: true` and `adapter_vs_full_finetune: false` alongside the three confounds — so a
reader parsing the JSON without this report still cannot mistake one for the other.

**The Fisher estimator, named.** The VIZ-03 Fisher panel draws the variant recorded in the
artifact as `empirical_diag_fisher/groundtruth_targets/mean_normalized`, estimated over
`n_examples` = 2000 at seed 1234, anchored at the 50k-step `best.pt`. Unpacked: it is an
**empirical** diagonal Fisher — squared gradients accumulated per parameter, no full matrix — taken
against **ground-truth targets** rather than samples drawn from the model, and **mean-normalized**
so that mean(F) = 1 across all trainable coordinates and a cell reads directly as "×the
importance of an average parameter". Per-cell aggregation is a mean rather than a sum, because a
sum would confound importance with tensor size (the MLP projections carry four times the elements
of the attention projections).

### The Fisher/Δ Correlation, Cited Terse

**The correlation verdict, cited.** The claim that EWC visibly dodges high-Fisher coordinates was
**measured, not asserted**, against a rule committed before the artifact existed. Across all 36
cells the Δ-reduction (naiveΔ − ewcΔ) tracks Fisher magnitude at Spearman **ρ = 0.801544**, 95%
CI **[0.597984, 0.920291]**, and the **GATE PASSES** — the correlation carries the pre-registered
positive sign and its interval excludes zero. The full pre-registration table, the seed, the
method notes and the verdict as recorded live in `results/phase13_ab_report.md` under
`## Phase 15 Addendum — Fisher/Δ Correlation Verdict`; they are not restated here. Two bounds
travel with that number and are pre-registered, not afterthoughts: **the sign is the falsifiable
claim, and the magnitude is reported honestly given n = 36 and is not itself pass/fail** — ρ =
0.80 is a rank correlation, not an effect size, and does not license a statement about what
fraction of high-Fisher movement EWC avoids. And the interval is a **percentile bootstrap, which
is known to be biased and anti-conservative at small n**; that caveat was written before the
coefficient was computed and does not get dropped because the result came out favorable.

### What Remains Uncertain

Each of the four results above is bounded, and the bounds are not
footnotes. The λ search's negative stands. The retention gate is measured against a noise floor
that was never re-verified at the production budget. The recall gates cover a proper-noun core
under a deliberately scoped held-out set, and the control that was supposed to license reading a
closed-book failure as absent memory largely failed. Teaching the persona measurably raised
off-topic dialogue cost even with replay, and without replay the collateral damage was severe.
Every one of those bounds is reproduced verbatim from its source in
`## Milestone 2 Limitations — Nine Honest Negatives, Quoted` below, which is the section to read
before quoting any number from this one.

## Milestone 2 Limitations — Nine Honest Negatives, Quoted

**This section carries NINE honest negatives**, each reproduced in its source's exact wording —
not summarized, not softened, not reordered for flow — so a reader learns every bound on the
Milestone 2 claims without opening `results/`. Eight were locked when the section was scoped; the
ninth (**L9**) was surfaced during Phase 15 research from data that predates this phase, and it is
recorded here under the same policy as the other eight rather than appended as an afterthought,
because a reader should be able to trace not just what each limitation says but when and how it
entered the record.

**Ordering is by which claim each limitation bounds** — never by severity and never by how
comfortable each is to read, so the ordering itself does not editorialize. Where a source passage
is long it is truncated **visibly**, with an ellipsis and a pointer to the full passage, rather
than paraphrased to shorten. The blockquotes rewrap their sources' lines and prefix them with
`> `; no word, digit, punctuation mark, emphasis marker or ellipsis has been altered.

The `L1`–`L9` labels are the **stable identifiers** from the phase's source inventory, not
positions in this list. They deliberately do not run in numeric order here, because the ordering
is the claim-bound one and renumbering the entries to make the list read sequentially would break
every reference to them elsewhere in the record.

### Bounding "EWC mitigates forgetting"

**L1 — no λ bought retention for free at the search budget.** From
`results/finetune_smoke_report.md`, `## Stage 3 — λ Sweep (EWC-03)`, line 159, verbatim and
unamended:

> **EWC not demonstrable at this budget** (no λ satisfies both the within-margin rule and the
> retention demonstrability guard) — surfaced, never massaged (pre-registered §8 all-fail
> outcome: λ\* = None, demonstrable = False).

The "§8" in that sentence is the pre-registered rule numbering inside
`scripts/finetune_smoke.py`, used as a label throughout that report; there is no `## 8` heading to
link to, which is why the section heading is cited instead.

**L7 — the retention noise floor the gate is measured against was never re-verified at the
production budget.** From `results/phase13_ab_report.md`, `## Threats to Validity` →
`### 2. The noise floor's measurement regime — and where it does not reach`, lines 209-214, with
its closing sentence from lines 220-223:

> **Named limitation (D-05 obligation 2):** that floor was **NOT re-verified at the 4000-step
> production budget**, and **NOT re-verified inside collapse dynamics** — it was measured in a
> stable regime, on the masked arm, at a shorter budget, while both Phase-13 arms are unmasked
> and one of them drifts by +6.42 PPL. **Seed-to-seed variance could plausibly scale with drift
> magnitude**, and a floor measured in a stable regime would not capture that. Nothing here rules
> that out.
>
> …
>
> That is corroboration from a free check, not a re-measurement — the honest re-measurement (a
> 1337/2024 seed pair at 4000 unmasked steps, ~75 min) was not run.

### Bounding "memory lives in the weights"

**L4 — the question-fairness control is closer to total failure than to a modest disadvantage.**
From `results/phase14_recall_report.md`, `## Control 1 — Question Fairness (D-11.1)`, line 378:

> **Measured.** With each fact's own first-person statement in the `<|system|>` persona span, the
> base (adapter off) scored **1/1944 = 0.0005** across 216 questions; 1 of those questions
> produced at least one completion containing the value. This is the ONLY place in the entire
> phase where a fact value legitimately appears in a prompt.

**L2 — so a closed-book failure is no longer unambiguous evidence of absent memory.** L4 is the
number; L2 is what it costs the claim. From the same file, `## Threats To Validity` →
`### 3. The question-fairness control's limitation (D-20 (a))`, lines 566-571 (the full passage is
at lines 398-401, under `### (a) What this control can no longer prove`):

> See `## Control 1 — Question Fairness (D-11.1)`, part (a). In-context answerability could not be
> established at this scale, so a closed-book failure **in isolation** is not unambiguous evidence
> of absent memory. The adapter-on / adapter-off differential is unaffected (part (b)), but any
> reading of a single failed question as "the model does not know this" is out of scope.

**L6 — held-out generalization is scoped, not universal.** From the same file,
`## Threats To Validity` → `### 1. The held-out set is deliberately scoped (D-22)`, lines 555-558:

> **Consequence for what a clean held-out result may claim:** it demonstrates generalization
> **within that scope** — across held-out template families in the taught direction — and **not**
> immunity to every documented fine-tuning limitation. This report makes no claim about reversed
> recall, because this phase did not measure it as a held-out property.

**L5 — the headline recall number covers the proper-noun core only.** From the same file,
`## Threats To Validity` → `### 2. The soft tier is excluded from the gate (D-05)`, lines 562-564:

> See `## Soft Tier — Excluded From The Gate (D-05)`. Two of the taught facts contribute nothing to
> either threshold, so the headline number describes the proper-noun core only — a narrower set
> than "everything the adapter was taught."

### Bounding "…without damaging the base"

**L3 — without replay, teaching the persona collapsed dialogue perplexity, and replay mitigates
rather than solves it.** From `results/phase14_calibration_report.md`,
`## Derivation 3 — PersonaChat Replay (D-15)`, line 322, truncated visibly (the full paragraph
continues at that line):

> **What the paired arm shows replay actually BUYS, and what it costs.** Replay at ratio 1.0 moves
> the collapse from +224.81% to +29.39% — a large mitigation — while taught recall falls from
> 0.6825 to 0.4143, a fall of 0.2683. **The replay arm ITSELF still trips the trigger.** Replay at
> this ratio reduces the collateral collapse but does not eliminate it, so 'replay required'
> should not be read as 'replay solves it'.
>
> …

**Mandatory context for the +224.81% figure.** That number carries a correction block in its own
source at `results/phase14_calibration_report.md:289-307` (`WR-01`). The recorded figures are the
**unmasked** ones — the code that produced the table called `masked_perplexity` without
`forbid_ids`, while the D-11.2 control always passed it — and the dead-ids-forbidden
re-measurement gives **+224.5330%** (and **+29.3364%** for the replay arm). That report's own
ruling is that the numbers stay as recorded, because they are what was actually measured, and the
verdict is not re-derived after the fact. Quoting +224.81% without saying the correction block
exists would be exactly the softening this section is written to prevent.

**L9 — the residual off-topic collapse that survived replay in the real run.** Recorded alongside
the *passed* recall gate as a named qualification, not folded into it. From
`results/phase14_recall_report.md`, `## Verdict`, line 585, truncated visibly:

> (1) No-collateral-collapse (D-11 control 2): the taught persona measurably raises off-topic
> dialogue cost (+27.16%) relative to the pre-adapter conversational base, but does not eliminate
> the collapse signature entirely. The adapter reduces, rather than removes, deviation from
> general conversational behavior on unrelated prompts.
>
> …

L3 is the pre-replay calibration measurement and L9 is the post-replay real-run measurement —
arguably its residual half, which is why they sit adjacent.

### Bounding "13.9M-parameter from-scratch base"

**L8 — 547 of 8192 ids are live, and about a fifth of the headline parameter count is dead
embedding rows.** Carried forward from Milestone 1 unchanged. From `docs/REPORT.md` above,
`## Decision: Byte-Level BPE from Scratch, Vocabulary Locked Before Model Sizing`, lines 61-67,
with the parameter-count consequence from `## Results`, lines 373-375:

> **What actually trained.** Training learned 283 of the 7,928 requested merges before the
> bounded TinyStories corpus exhausted its mergeable pairs — the trainer itself warns
> "corpus exhausted: learned 283 of 7928 requested merges; vocab_size=8192 has 7645 dead ids".
> The *effective* vocabulary is therefore 547 live ids (256 bytes + 283 learned merges + 8
> specials); the locked 8192-row table is reserved capacity. The trade-off is stated plainly:
> shape stability for every downstream checkpoint, in exchange for 7645 dead rows the model
> carries in its embedding table.
>
> …
>
> Of the headline count, 2,935,680 parameters (7645 dead rows × 384 dims, ~21%) are embedding
> rows for ids that can never occur in the training data or be decoded — counted in the headline
> because they are part of the shipped tensor.

> **CORRECTION (Phase 15, recorded 2026-08-02 — the quoted v1.0 text above is NOT amended).** The
> quoted passage attributes merge exhaustion to *"the bounded TinyStories corpus"*. That
> attribution is wrong, and the v1.0 wording stands as written because recorded text in this
> project is corrected by dated note, never edited in place.
>
> **The verification performed:** `scripts/train_tokenizer.py:31` sets
> `CORPUS_PATH = _REPO_ROOT / "tests" / "fixtures" / "tiny_corpus.txt"`, and that fixture is
> **11,469 bytes** — not the full TinyStories corpus the original wording implies. The frozen
> production artifact `artifacts/tokenizer.json` (**5,648 bytes**, dated 2026-06-04) is the file
> built from that fixture and is the tokenizer every checkpoint in this report was trained
> through. Both sizes were confirmed against the files in this repository before this note was
> written. The 283-merge / 547-live-id / 7645-dead-row consequences quoted above are **unchanged
> and correct**; only the identity of the corpus that produced them was under-disclosed.
>
> **Provenance:** this was a tracked, open tech-debt item whose recorded home was this phase —
> `.planning/STATE.md` Deferred Items (*"docs/REPORT.md under-discloses tokenizer training-corpus
> identity (11.5KB fixture → 547 live ids) | open — natural home: DOC-02 honesty pass (Phase
> 15)"*) and `.planning/milestones/v1.0-MILESTONE-AUDIT.md:18` (WR-04 / WARNING-3).
>
> **README.md carried the same misattribution** and, carrying no equivalent
> stands-as-written protection, its v2.0 rewrite states the corrected attribution directly rather
> than by note.

**L8 is a capacity bound, not a correctness bound.** The dead rows are inert — they are masked out
of the logits before sampling everywhere it matters — but they are counted in the headline
parameter figure because they are part of the shipped tensor, and the effective vocabulary the
model actually writes with is 547 ids.

---

## Claim Correction: The Memory Toggle Is Availability, Not Authorization (Phase 18, recorded 2026-08-16)

**Appended, not edited — nothing above this line is amended.** This report's standing rule, set
out under `## Milestone 1 Ends Here` and applied again in the Phase 15 tokenizer-corpus correction
above, is that recorded text stands as written and corrections arrive dated and appended. This
section is one of those. It states a claim correction only: no number from the Phase 18 run is
quoted here, because none exists at the time it is recorded.

### The reading being corrected

The Milestone 2 material above presents the teach-then-recall demo's memory ON/OFF toggle as the
live proof that personalization lives in the weights. The mechanism described is accurate and is
not amended: unchecking the box flips 36 boolean flags on the adapter wrappers, reloads nothing,
recomputes nothing, and leaves the prompt token panel byte-identical between the two states. That
is what makes the demonstration honest — the answer changes while the context does not. What is
corrected is the *reading* a switch labelled ON/OFF invites.

The memory toggle is availability, not authorization: unchecking withholds the adapter's contribution from this process, it revokes no one's access to the weights and puts nothing beyond recovery.

Withholding a contribution is not an access-control boundary and not erasure. With the toggle
unchecked, every value the adapter learned is still present in its 331,776 parameters and the file
on disk is untouched; the adapter is portable, so anyone holding it has white-box access —
gradients, per-token probabilities, direct parameter inspection — which is strictly more powerful
than the black-box prompt access a demo visitor has. The demo's one-way Reset is a different
mechanism making a different claim and is outside this correction.

This sentence is maintained in one place and copied to none: `TOGGLE_IS_AVAILABILITY` in
`scripts/personalize_demo.py` is the source of truth that the Gradio label interpolates, and
`tests/test_phase18_docs.py` asserts this document and `README.md` carry it character for
character. The demo's own copy carries no dated correction marker, because there was nothing to
correct there — its wording was already availability-framed and mechanically honest.

### Threats to validity carried into the Phase 18 audit

Phase 18 measures how much of the adapter's contents a black-box, prompt-only attacker can
recover. Two bounds on whatever it reports are recorded here, in advance of its numbers:

**A measured rate is a lower bound on leakage, never an upper bound on privacy.** Black-box prompt
access is the weakest threat model available against these weights, so the audit is a floor and
not a ceiling. A stronger attacker was not run, and nothing the audit finds excludes one.

**A low extraction rate may be a property of LoRA rather than a PersonaCore achievement.** At this
capacity — 331,776 trainable parameters adapting a 13.9M-parameter base — little may be recoverable
simply because little is stored in a form a prompt can address, and this audit runs no arm
separating that from a property of PersonaCore's design. Stated in advance because the alternative
is letting a reader draw the flattering inference unaided once a number is on the page. The pinned
wording is `LORA_PROPERTY_CAVEAT` in `scripts/phase18_extraction.py`, where a committed proof
requires it to appear adjacent to the audit's closing sentence in generated prose rather than
typed beside it by hand.

The measured result, its denominator and its interval are appended to this report by Phase 18
through this same additive path.

## Extraction Audit Result: Personalization in Weights Is Recoverable Under Black-Box Attack (Phase 18, recorded 2026-08-17)

*Appended additively. No line above this heading is altered, and the section above — 18-12's dated
claim correction — is carried through byte-identically. The measured result promised at the end of
that section is recorded here.*

Phase 18 ran a pre-registered black-box extraction audit against the shipped persona adapter: 864
attack prompts across four families at K = 48 draws each, plus a 112-question positive control, run
twice — once with the adapter attached and once with it gated off at the identical budget, prompts,
seeds and masks. 84,960 draws in total.

**The verdict, as the committed gate returned it:**

> `LEAKAGE_DEMONSTRATED`

That value is `null_result_is_admissible`'s own return, carried through `assemble_verdict`
unchanged. It is not a phrase written around the numbers.

### The headline number, with its denominator and both bounds

On the **gated tier** (`core_held_out`, the never-taught split the formal verdict is taken on), the
best attack family `A2` extracted **92 of 104 questions** at least once within 48 draws:

- rate **0.8846**
- one-sided 95% Wilson **lower** bound **0.8231**
- one-sided 95% Wilson **upper** bound **0.9267**

The no-adapter control, at the same budget, extracted **0 of 104** — on every family, at every rung.

| family | gated tier (104 questions) | adapter-off | taught tier (112 questions) | adapter-off |
| --- | --- | --- | --- | --- |
| `A1-mild` | 87 | 0 of 104 | 102 | 0 of 112 |
| `A1-aggressive` | 30 | 0 of 104 | 31 | 0 of 112 |
| `A2` | **92** | 0 of 104 | **105** | 0 of 112 |
| `A3` | 85 | 0 of 104 | 100 | 0 of 112 |

Every rate above is a **question-unit** count. The fact-level unit stands at n = 8 and is published
beside every question-unit figure in `results/phase18_extraction_report.md`; no claim here is made
at the smaller denominator.

**The tier split is reported, not merged.** `core_taught` is the stronger attack surface and is
excluded from the formal verdict by design — Phase 14 had already measured taught templates as the
easier surface. Publishing a pooled number across both tiers would let the easier split inflate a
figure the gated tier is supposed to carry alone.

### What this does and does not establish

The positive control reproduced exactly — family zero's 112 per-question hit vectors matched Phase
14's committed rows with zero mismatches — so the harness is known to extract a fact known to be
present. That is what makes the contrast above readable rather than a story about a broken harness.

**This is a lower bound on leakage, never an upper bound on privacy.** Black-box prompt access is
the weakest threat model available here. The attacker had no gradients, no token probabilities, no
white-box read of the adapter's 331,776 parameters, and no fine-tuning attack — the last of which
the unlearning literature reports recovering roughly 88% of supposedly removed information. The
adapter is a portable file; anyone holding it has strictly more power than what was run.

**ATK-06, stated because the alternative is letting a reader draw the flattering inference
unaided:** a low extraction rate at this scale may be a property of **LoRA at this capacity** —
331,776 trainable parameters adapting a 13.9M-parameter base — rather than an achievement of
PersonaCore's design, and this audit runs no arm that separates the two.

### What it means for the project's central claim

PersonaCore's thesis is that personalization lives in the weights rather than in a prompt or a
store. This audit is the first measurement of the **cost** of that design, and it does not soften
it: the same property that makes the memory portable and store-free makes it **recoverable from the
weights by an attacker with nothing but prompt access**. The zero-versus-92 contrast against the
no-adapter control is not a privacy result — it is direct evidence that what the adapter learned is
extractable.

The claim that memory lives in the weights survives this audit intact. The claim that living in the
weights is *therefore private* does not, and was never measured before now.

**Phase 19 handoff:** `(92, 104, 0, 104)` — `erasure_is_worth_attempting` returns `True`. Erasure is
worth attempting because the target is demonstrably recoverable, not because a threshold was chosen
to make it so.

Full evidence, every ladder rung, the exposure table with all three frames and both reductions, the
complete threat-model scope and the threats-to-validity section: `results/phase18_extraction_report.md`.

## Selective Erasure Result: Erasure Is Not Selective at 331,776 Parameters, and Two Instruments Disagree (Phase 19, recorded 2026-08-19)

*Appended additively. No line above this heading is altered, and the section above — Phase 18's
extraction audit result — is carried through byte-identically.*

Phase 18 handed Phase 19 `(92, 104, 0, 104)`, on which `erasure_is_worth_attempting` returned
`True`. Phase 19 attempted it: selective erasure of ONE taught fact from the shipped persona
adapter by rank-1 component ablation, judged against criteria committed as executable code in
`scripts/erasure_gate.py` on 2026-08-12 — **one commit, `23a830c`, unamended** — before Phase 16 ran
and before any v3.0 number existed.

**The verdict, as the committed gate returned it:**

> `FAILURE`
>
> - (a) target upper bound 0.0911 over 27 questions <= calibrated floor 0.0911
> - (b) worst non-target degradation 1.000000 > k=2 x 0.148148 = 0.296296
> - (c) dialogue PPL 4.8511 vs cap 4.5837; retention PPL 3.670918 vs cap 4.029000

`erasure_succeeded` was called exactly once, on the measured record. The three reasons above are its
own return value, not a paraphrase written around the numbers.

### The Target Was Erased. Everything Around It Went With It.

The fact itself came out: **0 of 27 questions** post-erasure over 1,296 draws, down from 27 of 27,
and condition (a) cleared exactly on its boundary — its 95% Wilson upper bound 0.091079 is the best
bound a perfect erasure can attain at that denominator. Removing it took **78 of 288** rank-1
components, dispersed across all six layers (18/12/12/17/10/9) and all six projections (fc_in 35,
fc_out 17, c_proj 13, v_proj 10, k_proj 2, q_proj 1). There is no fact-localised structure at this
capacity to confine an ablation to, and the collateral is what that costs: **all seven gated
non-target facts exceeded the (b) margin, four stopped producing their taught value at all, and
77.6370113463966% of the dialogue adaptation is gone.**

**Selective erasure is not selective at 331,776 parameters.** That sentence is
`D8_PUBLICATION_POSTURE`, committed before the number existed, and it ships as written.

### The Rank Instrument and the Generation Instrument Disagree — A Co-Headline, Not a Caveat

Read through exposure rank, the same weights look like a textbook selective erasure: only the target
moves off rank 1, and all seven gated non-targets hold rank 1 with their exposure bits at ceiling.
Read through generation on the same rows, four of those seven produce nothing at all.

The hardest form of the evidence: **the rank instrument returns bit-identical readings for the
ablated adapter (M1) and a retrain-without-the-fact reference (M2) across all eight slots** —
identical rank AND identical exposure bits, the target at (2, 2.0) in both — while on those same two
adapters `sibling_name` and `street` generate 0/27 under M1 and 27/27 under M2, and `person_name`
0/27 under M1 and 26/27 under M2. One instrument cannot tell the two adapters apart. The other
separates them completely.

**Retroactive weight on Phase 18, stated rather than implied, and with its scope limit.** Any Phase
18 reading whose weight rests on exposure rank or exposure bits **alone** must be re-read in this
light: that instrument can report undisturbed while generation collapses underneath it. **Phase 18
readings paired with a generation number are unaffected — including the section immediately above,
whose headline is a generation count (92 of 104 extracted at least once within 48 draws).** The
pairing is what makes them safe, and this result is the argument for why the pairing was never
optional.

### Condition (c) Could Not Have Discriminated an Erasure Either

Published as a dated continuation beside the verdict rather than as an amendment to it. Condition
(c) anchors its dialogue leg on `V20_MASKED_DIALOGUE_VAL_PPL = 4.5733`, the **adapter-OFF** baseline,
while the model an erasure is asked to preserve is the **adapter-present** one Phase 14 had already
measured and published as a named limitation (5.8154, **+27.16%** over 270,203 scored targets,
`COLLAPSE_PPL_TRIGGER` tripped, descriptive, no gate). Run through the committed gate, a perfect
erasure — 0 successes, zero non-target degradation, retention clearing with 0.358082 of headroom —
still returns FAILURE on (c) alone: the conversational cost was paid at **teaching** time, an entire
phase before any component was ablated.

Re-anchoring does not rescue it. The leg is a one-sided upper cap, so post-erasure perplexity falls
toward the adapter-off baseline in proportion to how much adaptation the ablation destroyed —
against the adapter-present anchor M1 "clears" by 0.974710, and that headroom **is** the destroyed
adaptation. Anchored either way, a one-sided perplexity cap cannot separate "capability preserved"
from "adaptation removed". **`23a830c` is not amended.** A criterion rewritten after seeing the
number it failed on is worth nothing, and the ordering that makes every figure in this milestone
credible is enforced against git's object graph rather than promised.

### What This Means for the Project's Central Claim

PersonaCore's thesis is that personalization lives in the weights rather than in a prompt or a
store. Three phases have now measured what that costs, and none of them is softened here: the memory
is **real** (Phase 14), it is **extractable by an attacker holding nothing but prompt access** (Phase
18), and at this capacity it **cannot be selectively removed** (Phase 19). A store-based design
deletes one row. This design has no row to delete — the fact is smeared across 78 of 288 rank-1
components spanning every layer and every projection, and reaching it means reaching them.

That is a negative result, published in the register this project has published every other one in:
the gate was written first, it returned FAILURE, and the FAILURE is what ships. What it establishes
is bounded, on six counts: **(1)** one fact; **(2)** one mechanism; **(3)** one adapter at 331,776
parameters over a 13.9M-parameter base; **(4)** no relearning attack run; **(5)** a retrain reference
that is a different adapter rather than an edited one; and **(6)** a verdict that is **not
mechanically reproducible by the pinned CLI alone** — it was reached along a hand-driven path, and
the sixth bound is the subject of the ship decision below.

### Ship Decision — DO NOT SHIP

**Phase 19's ship decision is `DO NOT SHIP`, and it withdraws no measurement above.** Every number,
table and finding in this section stands exactly as published — the FAILURE verdict with the
committed rule's own three reasons, k = 78 of 288, the 77.6% destroyed dialogue adaptation, the
rank-vs-generation co-headline and its retroactive scope limit on Phase 18's rank-only readings.

**The single claim withheld is that this verdict is mechanically reproducible by the pin alone.** It
is not, and that is the exact and only reason for the decision. The verdict was reached along a
hand-driven path through the unpinned `scripts/phase19_run.py`, which routes around defects in the
CLOSED `scripts/phase19_erasure.py`. Run against these same committed artifacts, the pin's own
`_cmd_report` cannot produce this verdict, in four independent ways: the per-fact tier collapse makes
the pinned `report` subcommand **SystemExit**; `_cmd_report` hands `retention_perplexity`'s
`[ppl, n]` pair to the gate's scalar `retention_ppl=` and raises **`TypeError`**; a key-ordering bug
in `zero_results_have_nll` short-circuits the gate to **`INCONCLUSIVE`** on exactly the perfect-(a)
outcome that was measured; and `_calibration_rate()` reads Phase 18's candidate recall, so the pin's
internal floor is the superseded 0.2 rather than the governing 0.09107873950450847 the verdict was
read against. So a reader cannot check out this repository, run the pinned CLI over the committed
artifacts, and watch this verdict come back. Each routing is disclosed and every governing number was
re-derived through a pinned function before the gate was called — but **disclosure is not mechanical
reproducibility, and this project does not ship the weaker claim under the stronger word.**

**This is a final verdict on reproducibility, not a pause.** It is not a blocker, not a TODO, and not
a gap left for a successor to close. Nobody should repair the pin in order to flip it:
`scripts/phase19_erasure.py` is closed at 15 commits, and editing a closed pin after the numbers
exist is precisely the move that would void the pre-registration ordering enforced against git's
object graph — and with it every figure above. Withholding one claim costs this phase a claim;
repairing the pin to recover that claim would cost the milestone all of them.

Full evidence — the verdict with all six pinned readings, the collateral curve at eight checkpoints,
the canary-exposure table, the M2 reference arm, eight threats to validity, and the dated
condition-(c) diagnosis: `results/phase19_erasure_report.md`.

## Deep-Link Correction: The Phase 18 Exposure Table Is a Rank-Only Reading, Now Scope-Limited (recorded 2026-08-19)

*Appended additively. No line above this heading is altered, and every section above — Phase 18's
extraction audit result and Phase 19's selective erasure result among them — is carried through
byte-identically.*

**The deep link this corrects.** Phase 18's extraction-audit section above closes by sending the
reader out of this document for "the exposure table with all three frames and both reductions", to
`results/phase18_extraction_report.md`. That table is at
`results/phase18_extraction_report.md:145-154`. It sits **190 lines above** the dated continuation
that scopes it, and it carries no forward pointer to that continuation — so a reader who follows the
link lands on the table with no reason to keep scrolling, and reads it unscoped.

**What that table is.** Every one of its eight slots reads **rank 1**. It is a rank-and-exposure
reading throughout — rank, exposure bits, the ceiling, |R|, the token-length spread and the three
reductions — with no generation number standing beside any of it. That is exactly the class of
reading Phase 19's retroactive scope limit reaches.

**Where the limit is, by line.** The dated continuation at
`results/phase18_extraction_report.md:340-405` — *"Phase 19's retroactive scope limit on the rank
and exposure readings"* — records that any Phase 18 reading whose weight rests on rank or exposure
bits ALONE must be re-read against what Phase 19 measured about the instrument: the rank instrument
returned bit-identical readings for the erased adapter and for a clean retrain of the identical
recipe with the target fact removed, across all eight slots, while generation on those same rows
separated the two completely. The same continuation names the **73 measured zero-cells** behind
admissibility item (4), published at `results/phase18_extraction_report.md:236`, as sitting **INSIDE
that limit rather than in its exemption** — their generation number is zero by construction, so the
exposure rank standing beside each one is doing the whole job alone.

**Why the pointer above was not edited in place.** The pointer at `docs/REPORT.md:1140-1141` sits
two lines above the heading at `:1143` and four lines above the sentence at `:1145`, which asserts
that no line above that heading is altered and that the section above it — Phase 18's extraction
audit result — is carried through byte-identically. The pointer is inside the very section that
sentence names. Editing it to mention the continuation would therefore falsify a published claim
sitting two lines below it. The redirect is published HERE instead, additively and dated, and
`docs/REPORT.md:1140-1141` is left byte-intact deliberately rather than by oversight.

**What is NOT affected, named explicitly so this cannot be read as a retraction.** Every Phase 18
reading that rests on **GENERATION** — the attacker submitting a prompt and reading the decoded
reply — stands exactly as published: the ASR ladder, on both tiers, at every rung, in both arms; the
headline **92 of 104 `core_held_out` questions** extracted at least once by `A2` on the adapter-on
arm, with its rate and its one-sided 95% Wilson lower bound; the adapter-off control arm at exactly
**0/104** questions at identical budget; the ATK-03 positive control; the **`LEAKAGE_DEMONSTRATED`**
verdict itself; and the `(92, 104, 0, 104)` Phase 19 handoff computed from those four question-unit
counts. Nothing above is withdrawn, qualified or narrowed. What this section adds is a pointer the
outbound link could not carry.
