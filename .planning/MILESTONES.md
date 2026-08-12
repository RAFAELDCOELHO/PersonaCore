# Milestones

## v2.0 Weight-Based Memory (Shipped: 2026-08-12)

**Delivered:** Personalization that lives in the weights — a from-scratch LoRA adapter teaches user-specific facts into 331,776 parameters on a frozen conversational base, and a fresh process recalls them from an empty prompt with the context provably wiped, while from-scratch EWC keeps the fine-tune from destroying the base model. Every headline number is gated by a rule committed to git before the number existed.

**Stats:**

- Phases: 7 (09-15) | Plans: 39 | Tasks: 50
- Commits: 364 over 62 days (2026-06-11 -> 2026-08-12), range `d886aaf`..`ecf572d`
- Diff: 284 files changed, +95,132 / -188
- Tests: 408 passed, 1 skipped (CUDA-only fp16 AMP smoke), 0 failed; ruff clean
- Audit: 24/24 requirements satisfied, 7/7 phases verified, 17/18 integration links wired, 3/3 E2E flows complete (`.planning/milestones/v2.0-MILESTONE-AUDIT.md`, status: passed)

**Key accomplishments:**

1. **From-scratch LoRA** — `LoRALinear` (A-Gaussian/B-zero, alpha/r scaling) injected post-load into six named projections across 6 layers, 331,776 params in 72 tensors. Toggle on/off is 36 boolean writes on the live model; merge/unmerge is bit-exact via stored clone; eject restores a vanilla tree. No HuggingFace PEFT.
2. **From-scratch EWC** — per-example empirical diagonal Fisher (batch-1 autograd, mean-normalized so a cell reads as "x the importance of an average parameter") plus the Kirkpatrick quadratic anchor, spliced into the v1.0 training loop through an additive `penalty_fn` seam proven bit-identical to a pre-edit golden trajectory.
3. **The A/B that demonstrated no-forgetting** — two 4000-step arms identical but for the penalty. From a shared step-0 anchor of 2.1076, naive retention PPL ended at **8.524171** and EWC at **3.891140**: a 3.6x difference in base-task destruction, clearing the pre-registered margin (2 x 0.068930) by **33.61x**. Acquisition cost is reported descriptively with no gate (+0.380556, ~9.1%) — the win was not bought by failing to learn.
4. **Clean-room teach-then-recall** — closed-book, context wiped: taught-template recall **496/1008 = 0.4921** against a threshold of 0.2486, held-out template families **326/936 = 0.3483** against 0.2000. The adapter-off control on the same weights and same prompts scored exactly **0/2430**, with adapter-off logits bit-identical to the un-adapted base (max |diff| 0.0). Thresholds derived on a disjoint calibration set and committed before the run existed.
5. **Honest negatives kept, not smoothed** — the lambda sweep's pre-registered all-fail verdict ("EWC not demonstrable at this budget") stands unamended, with the later production lambda=0.01 logged as a separate dated discretionary choice. The retention win is scoped to teacher-forced PPL because free-running story mode measurably survives in neither arm (79 naive vs 69 EWC role-token leaks).
6. **Evidence you can regenerate** — figures are drawn only from a committed JSON artifact by a module structurally forbidden (AST walk + fresh-interpreter probe) from opening a checkpoint. The Fisher/delta correlation was measured against a rule committed before the artifact existed: Spearman **rho = 0.801544**, 95% CI [0.597984, 0.920291], gate passes on sign with magnitude reported as descriptive at n=36.

**Known deferred items at close:** 0. All pre-close open artifacts were resolved rather than acknowledged (`gsd-sdk audit-open` -> 0 items). v1.0's carried tech debt was also closed here: DEBT-01 (run.csv token under-count) landed before the first v2.0 training step, and DEBT-02's warm-sampling half — `evaluate.py` sampling without `forbid_ids`, open since v1.0 — was fixed in `3781a97` with the headline 2.1066 verified byte-identical afterward. Remaining non-blocking notes (W1 adapter `LoRAConfig` defaults, W3 hand-entered lambda=0 frontier point) are recorded in the milestone audit.

---

## v1.0 Foundation (Shipped: 2026-06-11)

**Delivered:** A correct, from-scratch ~13.9M-parameter GPT-style language model in pure PyTorch — BPE tokenizer, transformer decoder, resumable training harness — pretrained on TinyStories on the author's own Apple Silicon machine to fluent generation (headline perplexity 2.1066), shipped with an offline Gradio CPU demo, an executed research notebook, a 137-test green suite, and a consolidated technical writeup.

**Stats:**

- Phases: 8 | Plans: 29 | Tasks: 43
- Commits: 245 over 8 days (2026-06-04 → 2026-06-11)
- Code: 6,543 lines of Python (src + scripts + tests); 137 tests passing, 1 CUDA-only skip
- Model: 13,891,584 params (tied weights counted once), `best.pt` val_loss 0.7378 at step 49000, headline PPL 2.1066 over 12,636,922 held-out tokens
- Audit: 35/35 requirements satisfied, 8/8 phases verified, 20/20 integration links wired, 3/3 E2E flows complete (.planning/milestones/v1.0-MILESTONE-AUDIT.md)

**Key accomplishments:**

1. From-scratch ~13.9M-param GPT-2-style decoder (causal MHA, pre-norm blocks, weight tying via shared tensor, GPT-2 init with residual scaling) — every silent-bug gate (causality perturbation, init-std, param-count band, `data_ptr` tying) green
2. From-scratch byte-level BPE tokenizer with deterministic merges, exact round-trips, frozen JSON artifact, and a tiktoken-gpt2 equivalence oracle proving the algorithm (test-only, never a runtime dependency)
3. Full local Apple-Silicon (M3/MPS, fp32) pretraining run on TinyStories — 50,000 steps, `best.pt` val_loss 0.7378, headline perplexity 2.1066 over 12.6M held-out tokens, kill+resume survived mid-run
4. Resumable training harness proven on a bigram before the transformer: AdamW + warmup/cosine, AMP discipline, open-dict checkpoints with RNG-state restore (bit-for-bit resume), restart-survivable CSV logging
5. Offline Gradio CPU demo with shared `generate()` (greedy/temperature/top-k/top-p, EOS stop, context crop) and a dead-id logits mask making it crash-proof at every in-UI setting
6. Portfolio rigor: 4-run ablation cohort with comparison table, executed `demo.ipynb`, 440-line technical REPORT with effective-vocabulary honesty (547 live of 8192 ids), and both M2 seams (named `nn.Linear` projections, `assemble_loss(..., extra_penalties=())`) locked in as verified acceptance criteria

**Known deferred items at close:** 1 (see STATE.md Deferred Items) — plus non-blocking tech debt logged in the milestone audit (forbid_ids not threaded into evaluate.py warm sampling; run.csv tokens column ×256 under-count; TODO(calibration) markers on shipped-final constants; tokenizer corpus identity under-disclosed in REPORT; one-time release-asset check).

---
