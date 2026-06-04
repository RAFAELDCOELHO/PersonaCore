# Feature Research

**Domain:** From-scratch small GPT-style language model (Milestone 1: base LM + demo only)
**Researched:** 2026-06-04
**Confidence:** HIGH (engineering correctness for small GPT training is stable, well-documented knowledge; verified against nanoGPT conventions and the TinyStories paper)

> **Framing.** This is a *portfolio engineering* feature landscape, not a product feature landscape. "Users" here are **portfolio reviewers at the MIT/Stanford bar** plus the author. A feature is "table stakes" if its absence makes a reviewer doubt the implementation is correct or self-built. A feature is a "differentiator" if it signals unusual rigor, taste, or depth. An "anti-feature" is a scope trap that burns the Kaggle/CPU budget without raising the portfolio bar — including everything reserved for Milestone 2.

---

## Feature Landscape

### Table Stakes (Reviewers Expect These — Absence = Incomplete/Unconvincing)

These are the components and engineering behaviors a reviewer scans for to confirm the LM is correct and actually built from scratch. Missing any of these reads as "didn't finish" or "didn't understand it."

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Bigram baseline (from scratch)** | Establishes a correct, trivially-understood floor; proves the training/eval/sampling harness works before adding transformer complexity | LOW | Single `nn.Embedding(vocab, vocab)` lookup table. Doubles as a smoke test for the whole loop. |
| **BPE tokenizer: train** | Core "from scratch" claim; reviewers know HF would make this trivial, so hand-rolled merges prove depth | MEDIUM | Byte-level start, iterative most-frequent-pair merge, learned merge ranks + vocab. Keep training offline/cached. |
| **BPE: encode / decode** | A tokenizer that can't round-trip is broken | MEDIUM | `decode(encode(s)) == s` for arbitrary UTF-8 must hold. Byte-level fallback avoids OOV. |
| **Round-trip correctness test** | The single most-scrutinized tokenizer property; one failing example destroys trust | LOW | Property test over random + adversarial strings (unicode, emoji, whitespace, empty). |
| **Special tokens** | EOS at minimum is required for generation termination and document boundaries during training | LOW | At least `<|endoftext|>`/EOS. Reserve IDs explicitly; document them. PAD/UNK optional at byte-level. |
| **Causal self-attention (from scratch)** | The heart of the "I built a transformer" claim | MEDIUM | Lower-triangular mask, scaled dot-product (`/sqrt(d_head)`), correct masking *before* softmax. The #1 place subtle bugs hide. |
| **Multi-head attention** | Single-head reads as toy; multi-head is standard | MEDIUM | Reshape to `(B, n_head, T, d_head)`; verify head-splitting/merging preserves shapes. |
| **Positional embeddings** | Without position info the model is a bag-of-tokens; reviewers check this exists | LOW | Learned absolute positions are fine and expected at this scale (GPT-2 style). |
| **Transformer block (pre-LN + MLP + residuals)** | Pre-LN residual structure is the modern correct default; post-LN or missing residuals signal a dated/buggy impl | MEDIUM | Pre-LayerNorm, residual add around attention and MLP, GELU MLP with 4× expansion. |
| **Weight tying (embedding ↔ LM head)** | Standard for small GPTs; saves ~1/3 of params at this scale and is a known best practice reviewers look for | LOW | Share `wte.weight` with `lm_head.weight`. Mention it explicitly in the writeup. |
| **Parameter counting** | Reviewers want the exact param count to verify the "10–15M" claim and architectural understanding | LOW | Print total + per-component breakdown. Trivial to add, disproportionately reassuring. |
| **Training loop with batching** | Obvious, but must be correct: contiguous-block sampling, input/target shift by one | LOW | `x = tokens[i:i+T]`, `y = tokens[i+1:i+T+1]`. Off-by-one here is a classic silent bug. |
| **Cross-entropy loss + loss logging** | The fundamental training signal; loss must be logged to be trusted | LOW | Log train loss at interval; persist to a file/CSV for the notebook curves. |
| **Validation loss (held-out split)** | Train-loss-only is an instant red flag for overfitting blindness | LOW | Periodic eval on held-out TinyStories split; report both curves. |
| **Checkpointing** | Non-negotiable on Kaggle (sessions die / 30h weekly cap) | MEDIUM | Save model + optimizer + scheduler + step + RNG state + config. Save *config alongside weights*. |
| **Resumability** | The whole point of checkpointing on a time-capped free tier; must actually resume mid-run | MEDIUM | Restore optimizer/scheduler/step exactly so loss continues smoothly, not a visible discontinuity. |
| **AdamW optimizer (correct hyperparams)** | Reviewers know the canonical small-GPT recipe; wrong defaults read as cargo-culting | LOW | AdamW, `wd=0.1`, `β=(0.9, 0.95)`, decoupled weight decay (no decay on biases/LayerNorm). |
| **LR schedule: warmup + cosine decay** | The standard small-GPT schedule; constant LR signals unfamiliarity | LOW | Linear warmup → cosine decay to a small floor. Verified as nanoGPT-standard. |
| **Gradient clipping** | Prevents loss spikes / divergence; standard safety the recipe expects | LOW | `clip_grad_norm_(..., 1.0)`. One line, prevents a class of training failures. |
| **Greedy + temperature + top-k sampling** | The expected minimum sampling toolkit; temperature and top-k are explicitly in M1 scope | LOW | Temperature scales logits; top-k masks to k highest before softmax. |
| **Max-length + EOS handling in generation** | Generation that never stops or ignores EOS looks unfinished | LOW | Stop on EOS or `max_new_tokens`; handle context-window truncation (crop to block size). |
| **Perplexity (quantitative eval)** | The standard LM metric; `exp(val_loss)`. Its absence reads as "no real evaluation" | LOW | Report on held-out split. Cheap given val loss already computed. |
| **Qualitative generation samples** | Reviewers want to *read* the output; coherent TinyStories text is the visceral proof it works | LOW | Curated samples at a few temperatures in the writeup/notebook. |
| **Gradio local chat demo (on-device CPU)** | The promised tangible demo; runs the model live without internet | MEDIUM | Must load checkpoint and generate on laptop CPU. Keep it a thin wrapper over the sampler. |
| **demo.ipynb research artifact** | Carries the ML narrative: loss curves, sampling, param count | MEDIUM | Reproducible cells: load checkpoint → curves → generate. This is the "show your work" artifact. |
| **Per-component unit tests** | Explicitly a first-class deliverable; tests are *the* evidence components are correct, not just plausible | MEDIUM | Shape tests, round-trip tests, causality test (future tokens can't affect past), overfit-a-batch test. |
| **Reproducible environment** | Reviewers (and the author) must be able to run it; portable Kaggle GPU ↔ laptop CPU | LOW | `requirements.txt`, pinned versions, seed control, device-agnostic code (`.to(device)`). |
| **Technical writeup** | Portfolio value *is* the documented narrative; design decisions + results, document-as-we-go | MEDIUM | Architecture, hyperparams, param count, curves, samples, decisions-and-why. |

### Differentiators (Elevate to Elite-Portfolio Quality)

Not required for "complete," but these are what separate a competent clone from work that signals genuine engineering maturity and ML taste. **Pick a few and do them excellently** rather than all shallowly.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Clean abstractions / module boundaries** | Signals software-engineering maturity, not just a single notebook dump. The strongest cheap differentiator. | MEDIUM | Separate `tokenizer/`, `model/`, `train/`, `sample/`, `data/`. Config dataclass. Importable, testable modules; thin scripts on top. |
| **"Overfit a single batch" test** | The canonical sanity check elite practitioners run; loss→~0 on one batch proves the model *can* learn and the loop is wired correctly | LOW | Cheap, high-signal, rarely seen in student projects. Mention it in the writeup as deliberate. |
| **Causality / no-future-leak test** | Directly proves the attention mask is correct — exactly the bug reviewers probe for | LOW | Perturb token at position t, assert logits at positions < t are unchanged. |
| **Architectural ablations** | Real research instinct: quantify what matters (e.g., weight tying on/off, n_layer/n_head sweep, LR sweep, with/without warmup) | MEDIUM | Even 2–3 small ablations with a comparison table reads as "scientist," not "copier." Budget-aware: keep runs short. |
| **top-p (nucleus) sampling** | Completes the modern sampling toolkit beyond the required top-k; shows awareness of SOTA decoding | LOW | Mask smallest-prob tail until cumulative ≥ p. Small addition, real polish. |
| **Param-count + FLOP/throughput reporting** | Demonstrates understanding of compute budgets and scaling, not just code | LOW | Report params, tokens/sec, est. FLOPs, and tokens-seen. Ties the model to the Kaggle budget narrative. |
| **Tokenizer compression-ratio analysis** | Shows the tokenizer is understood as a *design choice*: bytes/token, vocab-size tradeoff, sample merges | LOW | Report chars-per-token on TinyStories; a learned-merges examples table is memorable. |
| **Reproducibility discipline (seeds + deterministic eval + config-with-checkpoint)** | The single biggest credibility multiplier; results a reviewer can trust and rerun | LOW–MEDIUM | Global seed, log config + git SHA into each checkpoint, deterministic eval mode. |
| **Loss curves with annotations** | Train+val on one plot, LR schedule overlaid, resume-points marked — reads as someone who *interrogates* training | LOW | A polished curve communicates more rigor than paragraphs. |
| **Scaling/emergence note tied to TinyStories findings** | Connects own results to the literature (grammar emerges early, coherence needs width/depth) | LOW | A short "what capability emerged at what scale" observation shows literacy with the domain. |
| **`generate()` as a clean, reusable API** | One well-designed sampling function powering tests, notebook, and Gradio = DRY, mature design | LOW | Avoids three divergent copies of generation logic. Shared core is itself a quality signal. |
| **CPU-inference portability proof** | Demonstrates the portability constraint is actually met, not assumed | LOW | A documented run of the demo on laptop CPU (timing, no-internet). Validates the dual-environment claim. |

### Anti-Features (Scope Traps — Deliberately NOT in Milestone 1)

These look tempting or "more impressive" but burn the zero-budget / free-tier / on-device budget without raising the M1 bar — or they belong to Milestone 2. Documenting them prevents scope creep.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **LoRA adapters** | The novel claim; tempting to start early | Explicitly Milestone 2. Pulling it in destabilizes the M1 base-LM de-risking strategy. | Ship the correct base LM first; LoRA builds *on* it in M2. |
| **EWC / continual learning** | Core differentiator of the whole project | Milestone 2. Meaningless without a fine-tuning stage that M1 doesn't have. | Defer entirely; M1's job is fluency, not memory. |
| **Conversational fine-tuning (DailyDialog/PersonaChat)** | "It should chat like an assistant" | Out of M1 scope — M1 stops at TinyStories fluency. Chat tuning needs M2's curriculum. | Gradio demo showcases *story continuation/completion*, framed honestly as a base LM. |
| **Personalization / weight-memory demos** | The portfolio payoff | Milestone 2 deliverable; impossible without LoRA+EWC. | Keep the M1 demo about generation quality, not memory. |
| **Scaling beyond ~10–15M params / multi-GPU** | "Bigger is more impressive" | Breaks the free-tier (P100, 30h/wk) and CPU-inference constraints. TinyStories shows coherence at this scale. | Hold the size; differentiate via rigor (ablations, tests), not parameter count. |
| **HuggingFace transformers/PEFT model code** | Faster to a working model | Excluded by design — the entire portfolio value is *from-scratch depth*. Using it nullifies the project. | Hand-roll everything. (HF *datasets* for raw TinyStories download is fine if only used as a data source, not model code.) |
| **Subword regularization / fancy tokenizer (Unigram/SentencePiece-grade)** | "More sophisticated tokenizer" | Over-engineering for M1; BPE is the expected, sufficient choice. Adds bugs and time. | Clean, correct, tested byte-level BPE. Note the tradeoff in the writeup. |
| **RAG / vector store / external memory** | "Give it memory/context" | Violates the core privacy-in-weights design requirement *and* adds infra. | None — memory lives in weights (and that's M2). |
| **RLHF / DPO / instruction tuning** | "Align it like ChatGPT" | Massively out of scope at 10–15M params and zero budget; no reward infra. | Temperature/top-k/top-p sampling is the only "steering" in M1. |
| **Mixed-precision/Flash-Attention/torch.compile micro-optimization** | "Make training fast" | Premature optimization; portability across P100+CPU and *correctness* matter more than speed in M1. Risk of device-specific breakage. | Plain, readable, device-agnostic PyTorch. Optimize only if training time forces it, and document it. |
| **Multi-dataset / two-stage curriculum in M1** | The full project plan mentions it | M1 explicitly stops at TinyStories. DailyDialog/PersonaChat is M2's stage. | Single clean TinyStories pretraining run. |
| **KV-cache / inference-speed engineering** | "Production-grade generation" | Unnecessary complexity for a short-context CPU demo; risks subtle correctness bugs. | Simple recompute-each-step generation; fast enough at this scale/context. |
| **Hyperparameter auto-tuning / sweep frameworks (Optuna/W&B sweeps)** | "Rigorous tuning" | Overkill for the budget; a few *manual* ablations communicate more and cost less. | Hand-picked nanoGPT-style defaults + 2–3 deliberate manual ablations. |

---

## Feature Dependencies

```
Reproducible environment / scaffolding
    └──enables──> everything (runs on Kaggle GPU ↔ laptop CPU)

BPE tokenizer (train → encode/decode → round-trip test → special tokens)
    └──required by──> Data prep (tokenize TinyStories → token stream/.bin)
                          └──required by──> Training loop
                                               └──required by──> Checkpointing/resumability
                                                                    └──required by──> Pretrain-to-fluency

Bigram baseline ──validates──> Training loop + eval + sampling harness
    (smoke-tests the harness before the transformer exists)

Model internals (causal attention → multi-head → pos emb → block → weight tying → param count)
    └──required by──> Training loop
    └──required by──> Generation (generate() needs a forward pass)

Generation (greedy/temp/top-k → max-len/EOS → top-p)
    └──required by──> Gradio demo
    └──required by──> Qualitative samples in demo.ipynb

Validation loss ──required by──> Perplexity
Loss logging ──required by──> Loss curves (notebook)

Trained checkpoint
    └──required by──> Gradio demo  (load + CPU inference)
    └──required by──> demo.ipynb   (curves + samples)
    └──required by──> Technical writeup (results)

Unit tests ──validate──> tokenizer, model internals, generation (cross-cutting)
Technical writeup ──documents──> all of the above (document-as-we-go)
```

### Dependency Notes

- **Tokenizer before everything trainable:** The token stream defines `vocab_size`, which sizes the embedding/LM-head and thus the param count. Lock the tokenizer (and its special-token IDs) before training; re-tokenizing mid-project invalidates checkpoints.
- **Bigram before the transformer:** The bigram model exists to de-risk the *harness* (batching, loss, logging, sampling) independent of attention bugs. If the bigram trains and samples, a later loss problem is almost certainly in the transformer, not the loop. High-value ordering.
- **Weight tying depends on matching dims:** Tying requires `d_model`-projected embedding and LM head to share a weight matrix; decide tying before counting params (it changes the count by ~`vocab_size × d_model`).
- **Checkpointing must precede the long pretrain run:** On a 30h/week cap with session kills, an un-resumable training loop means lost weeks. Resumability is a *prerequisite* for fluency, not a nicety.
- **`generate()` is shared infrastructure:** Tests, notebook, and Gradio should all call the same sampling function. Building it once (table stakes) and reusing it (differentiator) prevents three drifting copies.
- **EOS handling couples tokenizer ↔ generation:** The EOS ID chosen at tokenizer-time is the stop condition at generation-time and the document separator at training-time. One ID, three consumers — keep it centralized in config.
- **Demo and writeup are terminal consumers:** Both depend on a trained checkpoint and the generation API. They cannot be finished until pretraining reaches coherent samples.

---

## MVP Definition

### Launch With (Milestone 1 = the MVP)

The minimum that makes the from-scratch foundation **complete and convincing**:

- [ ] **Reproducible scaffolding** — portable across Kaggle GPU and laptop CPU; everything depends on it
- [ ] **Bigram baseline + tests** — de-risks and validates the training/eval/sampling harness
- [ ] **From-scratch BPE (train/encode/decode/special tokens) + round-trip test** — the core "from scratch" proof; sizes the model
- [ ] **From-scratch GPT decoder (~10–15M): causal MHA, pos emb, blocks, weight tying, param count) + tests** — the central claim
- [ ] **Training loop: AdamW + warmup/cosine + grad clip + loss logging + val loss + checkpointing/resumability** — must survive Kaggle session limits
- [ ] **Pretrain on TinyStories to coherent generation** — the visceral proof the LM works
- [ ] **Generation: greedy/temperature/top-k + max-length + EOS + tests** — required sampling toolkit
- [ ] **Perplexity + curated qualitative samples** — quantitative + qualitative evaluation
- [ ] **Gradio CPU demo + demo.ipynb (curves, samples, param count)** — the tangible artifacts
- [ ] **Technical writeup (document-as-we-go)** — the portfolio narrative

### Add After Core Works (still within M1, time permitting — these are the differentiators)

- [ ] **top-p sampling** — once top-k generation is solid
- [ ] **2–3 architectural/LR ablations with a comparison table** — once a baseline run is reproducible
- [ ] **Overfit-a-batch + causality tests** — once model + loop exist (cheap, high-signal)
- [ ] **Throughput/FLOP + tokenizer compression-ratio reporting** — once training is running
- [ ] **Annotated loss curves + reproducibility hardening (config-with-checkpoint, git SHA, seeds)** — polish pass before the writeup

### Future Consideration (Milestone 2+ — explicitly deferred)

- [ ] **LoRA adapters from scratch** — the novel weight-memory mechanism (M2)
- [ ] **EWC continual learning** — catastrophic-forgetting prevention (M2)
- [ ] **Conversational fine-tuning (DailyDialog/PersonaChat)** — second curriculum stage (M2)
- [ ] **Teach-then-recall + EWC no-forgetting demos, weight-delta heatmaps** — the M2 research-narrative payoff

---

## Feature Prioritization Matrix

| Feature | Reviewer Value | Implementation Cost | Priority |
|---------|----------------|---------------------|----------|
| From-scratch BPE + round-trip test | HIGH | MEDIUM | P1 |
| Causal multi-head attention + tests | HIGH | MEDIUM | P1 |
| Positional emb + block + weight tying + param count | HIGH | MEDIUM | P1 |
| Training loop (AdamW/warmup-cosine/clip/logging) | HIGH | MEDIUM | P1 |
| Validation loss + checkpointing + resumability | HIGH | MEDIUM | P1 |
| Pretrain on TinyStories to coherence | HIGH | MEDIUM | P1 |
| Generation (greedy/temp/top-k, max-len, EOS) + tests | HIGH | LOW | P1 |
| Perplexity + qualitative samples | HIGH | LOW | P1 |
| Bigram baseline + tests | MEDIUM | LOW | P1 |
| Gradio CPU demo | HIGH | MEDIUM | P1 |
| demo.ipynb (curves, samples) | HIGH | MEDIUM | P1 |
| Per-component unit tests | HIGH | MEDIUM | P1 |
| Technical writeup | HIGH | MEDIUM | P1 |
| Clean module abstractions | HIGH | MEDIUM | P1 (do it from the start, not as cleanup) |
| Reproducibility (seeds, config-with-ckpt, git SHA) | HIGH | LOW | P1 |
| Overfit-a-batch + causality tests | HIGH | LOW | P2 |
| Architectural/LR ablations + table | HIGH | MEDIUM | P2 |
| top-p sampling | MEDIUM | LOW | P2 |
| Throughput/FLOP + tokenizer compression reporting | MEDIUM | LOW | P2 |
| Annotated loss curves | MEDIUM | LOW | P2 |
| LoRA / EWC / conversational tuning / personalization | HIGH (later) | HIGH | P3 (Milestone 2) |

**Priority key:**
- P1: Must have for Milestone 1 — the foundation is incomplete without it
- P2: Differentiators — add once P1 core is working; these earn the "elite" grade
- P3: Milestone 2 — deliberately out of scope now

---

## Competitor Feature Analysis

"Competitors" = the reference implementations and student projects a reviewer mentally benchmarks this against.

| Feature | nanoGPT (Karpathy) | Typical student TinyStories clone | Our Approach (M1) |
|---------|--------------------|-----------------------------------|-------------------|
| Tokenizer | Reuses GPT-2 BPE (tiktoken) | Reuses HF/tiktoken tokenizer | **From-scratch BPE + round-trip tests** (depth signal) |
| Model internals | From scratch, terse | Often copied verbatim, thinly understood | From scratch, **clean modules + param breakdown + causality test** |
| Training recipe | AdamW, warmup+cosine, grad clip, weight tying | Frequently constant LR / no val loss | Full canonical recipe + **val loss + resumable checkpointing** |
| Resumability | Has checkpoint resume | Often absent | **First-class** (Kaggle 30h/wk demands it) |
| Sampling | temp + top-k | temp only | greedy/temp/top-k (+ **top-p** as differentiator), EOS-aware |
| Evaluation | val loss / mfu | val loss only, or none | **Perplexity + curated samples + ablations** |
| Tests | minimal | usually none | **Per-component unit tests** (round-trip, shapes, causality, overfit-batch) |
| Demo | none (research repo) | sometimes a script | **Gradio CPU demo + narrated demo.ipynb** |
| Writeup | README | sparse | **Document-as-we-go technical narrative** with decisions + results |

**Takeaway:** This project does not differentiate by being a bigger or more novel *model* in M1 — at 10–15M on TinyStories it is intentionally modest. It differentiates by **doing every component from scratch, correctly, with tests, reproducibly, and well-documented** — the dimensions where student clones and even reference repos are typically thin.

---

## Sources

- TinyStories paper — *How Small Can Language Models Be and Still Speak Coherent English?* (arXiv 2305.07759): confirms 1–80M models on TinyStories reach coherent generation; grammar emerges at small width/depth, coherence/plot need more — supports the 10–15M target and the "emergence" differentiator. [HIGH]
- nanoGPT conventions (multiple analyses): confirms the canonical small-GPT training recipe — AdamW (`wd=0.1`, `β=(0.9, 0.95)`), linear-warmup + cosine-decay LR, `clip_grad_norm_=1.0`, weight tying, val-loss eval, checkpoint resume. Anchors the table-stakes training features. [HIGH]
- Community TinyStories-from-scratch replications (HF model cards, Medium write-ups): confirm 8M-class models train to coherent stories in ~hours on a single small GPU — validates feasibility within the Kaggle free-tier budget. [MEDIUM]
- `.planning/PROJECT.md`: M1 scope boundary, dual-environment (Kaggle GPU ↔ CPU) constraint, from-scratch design requirement, and explicit M2 deferrals (LoRA/EWC/conversational tuning/personalization). [HIGH — authoritative project context]

---
*Feature research for: from-scratch small GPT-style language model (PersonaCore Milestone 1)*
*Researched: 2026-06-04*
