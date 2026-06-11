# Milestones

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
