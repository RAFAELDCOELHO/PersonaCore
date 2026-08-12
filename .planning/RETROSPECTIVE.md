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

## Milestone: v2.0 — Weight-Based Memory

**Shipped:** 2026-08-12
**Phases:** 7 (09-15) | **Plans:** 39 | **Commits:** 364 over 62 days

### What Was Built

From-scratch LoRA (`lora/`: config, layer, injection, toggle/eject, merge/unmerge) and from-scratch
EWC (`continual/`: per-example diagonal Fisher, Kirkpatrick penalty, persistence), spliced into the
untouched v1.0 training loop through additive seams proven bit-identical when off. A `dialogue/`
package turned PersonaChat into masked training bins. Phase 12 fine-tuned `best.pt` into a
conversational base; Phase 13 ran the unconfounded EWC A/B; Phase 14 delivered the core-value proof
— a LoRA adapter recalling taught facts from an empty prompt in a fresh process, with a live on/off
toggle; Phase 15 shipped the signature figures and the v2.0 writeup.

### What Worked

- **Pre-registration in committed code, not prose.** Every gate is a module-level literal pushed
  before the run it judges, and verdicts import those constants rather than retyping them. This is
  the single highest-leverage practice of the milestone: it made "the threshold moved" structurally
  impossible to do quietly, and git history is the proof.
- **Gating only what the sample size supports.** Retention gated / acquisition descriptive;
  correlation sign gated / magnitude descriptive at n=36. Prevented both an EWC "win" bought by
  failing to learn and a rank correlation being read as an effect size.
- **Controls designed to be falsifiable.** The adapter-off arm scoring exactly 0/2430 on identical
  prompts is worth more than the 0.4921 recall number, because it is the thing that could have come
  back wrong and didn't.
- **Front-loading unit-testable work.** Phases 9, 10, 11 are mutually independent and all landed
  before any long training run, so every expensive run stood on already-pinned components.

### What Was Inefficient

- **Stale artifacts accumulated silently.** Phase 14's VERIFICATION sat at `gaps_found 55/57` long
  after both gaps were fixed; 50 status cells across the 09-13 VALIDATION maps still carried
  plan-time "not yet written" marks; two quick tasks read as incomplete. None was real work — all of
  it was metadata drift that had to be re-verified from scratch at milestone close. A re-stamp step
  at phase close would have cost minutes instead of a full audit pass.
- **A v1.0 warning crossed two entire milestones unfixed.** `evaluate.py` sampling without
  `forbid_ids` was recorded in the v1.0 audit, carried into v2.0's audit, and only closed at v2.0
  close — a one-line fix. Recording a warning is not the same as scheduling it.
- **One requirement's wording outlived its decision.** DEBT-02 named `evaluate.py`'s PPL path as
  needing the mask; the masked/unmasked split was deliberately frozen 2026-07-31 and made that
  wording wrong. It survived because nobody re-read the requirement against the decision that
  superseded it — and it nearly drove a "fix" that would have silently moved the published 2.1066.

### Patterns Established

- **Structural enforcement over declared invariants.** An AST walk plus a fresh-interpreter probe to
  prove a plotting module cannot open a checkpoint; a token-id check rather than a template review
  to prove no fact value reached a scored prompt; a mask-object comparison rather than an assertion
  that two masks match. Guards are watched failing before being trusted.
- **Extract once, then plot only from the committed artifact.** A committed PNG whose inputs are
  gitignored is an assertion, not evidence.
- **Honest negatives are appended to, never edited.** Dated continuation sections that explicitly
  state they do not amend what they follow.

### Key Lessons

1. **A threshold chosen after seeing the data is not a threshold** — and the only durable defense is
   putting it in a pushed commit, not in a paragraph promising you did.
2. **A declared invariant is true the day it is written and silently false after the next
   refactor.** If it matters, something must fail loudly when it breaks.
3. **Verification artifacts rot faster than code.** Re-stamp at phase close, or pay for a full
   re-audit later.
4. **"Documented" is not "scheduled."** A warning with no owner and no phase crosses milestones.
5. **Re-read requirements against the decisions that superseded them.** Stale requirement text is
   more dangerous than a missing requirement, because it reads as authoritative.

### Cost Observations

- Sessions: multi-session across 62 days; all training local on M3/MPS, fp32, zero paid compute.
- Notable: the two 4000-step A/B arms took 37.6 and 38.3 minutes each — the expensive resource in
  this milestone was not GPU time but the discipline of committing gates before runs.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 | 8 | 29 | Established Wave-0 RED scaffolds, gap-closure re-verification loops, and M2-seam-as-acceptance-criteria |
| v2.0 | 7 | 39 | Pre-registration in committed code before any number exists; gate-only-what-n-supports; structural enforcement replacing declared invariants; honest negatives appended-to rather than edited |

### Cumulative Quality

| Milestone | Tests | Suite Status | Runtime Deps Added |
|-----------|-------|--------------|--------------------|
| v1.0 | 137 (+1 CUDA skip) | green, CPU-only | numpy, regex, torch[cpu extra], gradio[demo extra] |
| v2.0 | 408 (+1 CUDA skip) | green, CPU-only | none — v2.0 added three hand-rolled subsystems (`lora/`, `continual/`, `dialogue/`) and zero runtime dependencies |

### Top Lessons (Verified Across Milestones)

1. **Warnings need gates, not just records.** *Predicted after v1.0, confirmed by v2.0.* The v1.0
   audit's `evaluate.py` warm-sampling warning was carried into the v2.0 audit and still not fixed —
   it took a milestone-close audit two milestones later to close a one-line change. A warning with
   no owner and no phase does not get done.
2. **Verifier-before-celebration.** *Predicted after v1.0, confirmed by v2.0.* Phase 14 recorded
   `gaps_found` and Phase 15 recorded `human_needed`; both were genuinely closed in code well before
   their artifacts said so, and neither was re-stamped. The verifier is only load-bearing if its
   verdict is refreshed when reality changes.
3. **Fix all consumers, not the one that reported it.** *Predicted after v1.0, confirmed by v2.0.*
   The dead-id mask was fixed for the demo in v1.0 and left unfixed in `evaluate.py` — same
   mechanism, same failure mode, different caller. When v2.0 finally closed it, the mask went into
   *both* the greedy and warm calls rather than only the one the warning named.
4. **New in v2.0 — the record must be tamper-evident, not merely honest.** Prose promising a
   threshold was pre-registered is worth nothing; a gate constant in a commit that provably precedes
   its artifact is worth everything. The same logic converted three declared invariants into
   mechanisms that fail loudly.
5. **New in v2.0 — stale requirement text is more dangerous than a missing requirement.** It reads
   as authoritative, and acting on it can break a published result. Re-read requirements against the
   decisions that superseded them.
