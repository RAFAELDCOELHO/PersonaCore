# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — Foundation

**Shipped:** 2026-06-11
**Phases:** 8 | **Plans:** 29 | **Commits:** 245 over 8 days

### What Was Built

- From-scratch ~13.9M-param GPT-2-style decoder (causal MHA, pre-norm, weight tying, GPT-2 init) — all silent-bug gates green
- From-scratch byte-level BPE tokenizer (deterministic merges, exact round-trips, frozen JSON artifact, tiktoken oracle equivalence)
- Resumable training harness (AdamW + warmup/cosine, AMP discipline, open-dict checkpoints with RNG-state restore) proven on a bigram before the transformer
- Full local M3/MPS fp32 pretrain on TinyStories: 50,000 steps, `best.pt` val_loss 0.7378, headline PPL 2.1066 over 12.6M held-out tokens
- Shared `generate()` (greedy/temp/top-k/top-p, EOS stop, context crop) + offline Gradio CPU demo with crash-proof dead-id logits mask
- Evaluation suite (deterministic perplexity vs brute-force oracle, 4-variant ablation cohort), executed `demo.ipynb`, 440-line technical REPORT, 137-test green suite

### What Worked

- **Dependency-forced build order paid off exactly as designed:** locking `vocab_size` before model sizing, and proving the harness on a trivial bigram before risking transformer math, meant the GPT dropped into an untouched loop (overfit gate green with zero harness changes) and the Phase-7 ablations reused it unchanged.
- **Wave-0 RED test scaffolds:** writing the failing acceptance tests first (Phases 2, 3, 4, 6, 7) made each implementation plan converge on a fixed contract — silent-bug classes (causal-mask, init-std, weight-tying, nucleus boundary) were caught by design, not luck.
- **Verification with gap-closure loops:** four phases (3, 6, 7, 8) went `gaps_found` → fix → re-verify `passed`. The CR-01 demo crash (~29% per generation at slider extremes) was caught by adversarial verification before any user hit it.
- **Honesty as a feature:** when the fixture-trained tokenizer's 547-live-id reality surfaced, the response (quantify the dead rows, document everywhere, mask at sampling) produced a stronger portfolio artifact than quietly retraining would have.
- **M2 seams as M1 acceptance criteria:** the named `nn.Linear` projections and `assemble_loss` seam were verified by tests in v1.0, so Milestone 2's LoRA/EWC work starts additive instead of as a refactor.

### What Was Inefficient

- **Phase 5 shipped without a VERIFICATION.md** — the only audit blocker at close; required a retroactive verification at milestone audit. Root cause: the long-training phase ended in a human-attended run, and the verify step was skipped in the excitement of a working model.
- **Tracking drift:** REQUIREMENTS.md checkboxes (8 stale), the ROADMAP progress table (Phase 5 row), and SUMMARY frontmatter `requirements-completed` lists (empty in phases 1/3/6/7) all lagged reality — the 3-source audit cross-reference had to reconcile what passed verifications already proved.
- **Phase 2's WR-04 warning ("regenerate tokenizer before Phase 5") was never acted on** — it silently became permanent tech debt. A warning with a deadline needs an owner/gate, not just a note.
- **Telemetry bug survived 4 phases:** `tokens_per_step` omitting `×block_size` was committed in Phase 3 and only flagged at the milestone integration check.

### Patterns Established

- Wave-0 RED scaffold → implementation waves → verification (→ gap-closure wave) as the standard phase shape
- Open-dict checkpoints with RNG-state *restore* (never re-seed) as the resume contract — extended cleanly from harness to memmap pretrain to slim export
- LOCKED contracts named in plans (forward signature, vocab/eos ids, CSV schema) that later phases must consume verbatim
- Reference oracles (tiktoken, brute-force perplexity) confined to tests with grep-guards proving no runtime dependency
- Decision IDs (D-xx) + requirement IDs (REQ-xx) threaded from ROADMAP → plans → tests → verification evidence

### Key Lessons

1. **Run the verifier before celebrating the artifact.** The one phase whose output everyone could *see* working (the trained model) was the one phase nobody formally verified.
2. **Warnings that gate a future phase need an enforcement hook** — Phase 2's "must regenerate tokenizer before Phase 5" should have been a Phase 5 plan precondition, not prose in a verification report.
3. **A fix applied at one consumer isn't done:** the `forbid_ids` mask fixed the demo but not `evaluate.py`/notebook — sweeping all consumers of a fixed bug should be part of the gap-closure contract.
4. **Keep checkbox state mechanical:** verification passing should flip REQUIREMENTS.md/ROADMAP rows in the same commit, or audits pay the reconciliation cost later.

### Cost Observations

- Model mix: not instrumented this milestone (model_profile: inherit)
- Sessions: multi-session across 8 days; checkpoint/resume infra absorbed laptop sleep/interrupts as designed
- Notable: the bigram-first harness de-risk meant zero harness rework during the expensive pretrain phase — the costliest compute (50k-step MPS run) ran once and resumed cleanly

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 | 8 | 29 | Established Wave-0 RED scaffolds, gap-closure re-verification loops, and M2-seam-as-acceptance-criteria |

### Cumulative Quality

| Milestone | Tests | Suite Status | Runtime Deps Added |
|-----------|-------|--------------|--------------------|
| v1.0 | 137 (+1 CUDA skip) | green, CPU-only | numpy, regex, torch[cpu extra], gradio[demo extra] |

### Top Lessons (Verified Across Milestones)

1. (Single milestone so far — candidates to verify in v2.0: verifier-before-celebration; warnings-need-gates; fix-all-consumers.)
