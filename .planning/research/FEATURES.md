# Feature Research

**Domain:** Weight-based memory for a from-scratch 13.9M-param GPT — LoRA adapters, EWC continual learning, conversational fine-tuning (DailyDialog + PersonaChat), and research-narrative demos (Milestone v2.0)
**Researched:** 2026-06-11
**Confidence:** HIGH on LoRA/EWC mechanics and SFT conventions (paper-verified, stable knowledge); MEDIUM on achievable quality at 13.9M params and on the teach-then-recall protocol (no single canonical reference — synthesized from knowledge-injection literature)

> **Framing.** As in v1.0 research: "users" are **portfolio reviewers at the MIT/Stanford bar** plus the author. Table stakes = absence makes a reviewer doubt the implementation is correct or the novel claim is real. Differentiator = signals unusual rigor or makes the research narrative land harder. Anti-feature = scope trap that burns the local-M3 compute budget or *weakens* the claim. This file covers ONLY the new v2.0 features; the v1.0 foundation landscape is archived in git history (commit `121b3d6^` and earlier).

---

## How the Target Features Conventionally Work

Reference behavior for each v2.0 feature, so requirements can be written against known conventions rather than guesses.

### 1. LoRA adapters for small GPTs

**Mechanics (Hu et al. 2021, stable knowledge — HIGH confidence):**
- A frozen linear layer `W₀x` gains a parallel low-rank path: `h = W₀x + (α/r)·B·A·x` with `A ∈ ℝ^{r×d_in}`, `B ∈ ℝ^{d_out×r}`.
- **Init convention:** `A` random Gaussian (HF PEFT uses Kaiming-uniform; either is accepted), **`B` zero** — so `ΔW = BA = 0` at start and the adapted model is bit-identical to the base. This is the property a reviewer will test first; it must be a unit test.
- **Scaling:** `α/r` multiplier. Convention: `α = r` or `α = 2r`. (rsLoRA's `α/√r` exists but is gold-plating at this scale — note it in the writeup, don't implement.)
- **Dropout:** 0–0.1 on the adapter input path. At 13.9M params with small fine-tuning sets, 0.0–0.05 is fine.
- **Rank:** original paper showed r=1–8 sufficient on GPT-3 for q,v-only adaptation; community practice for small/medium models is r=8–32. For PersonaCore: **r=4–16 is the sane band; r=8, α=16 is the defensible default.** Important small-model nuance: at d_model in the few-hundreds, r=8 is already a meaningful fraction of full rank — document the LoRA param count vs base (per adapted layer: `r·(d_in+d_out)` params).
- **Which projections:** the original paper adapted only `W_q, W_v`. Modern practice (QLoRA finding, Unsloth guidance) adapts **all linear layers — attention q/k/v/o + both MLP projections — for best quality**, which is exactly the six named `nn.Linear` seams v1.0 shipped. Recommended: adapt all six by default, expose a config list so a "q,v-only vs all-six" ablation is one flag.
- **Merge vs keep separate:** merging (`W' = W₀ + (α/r)BA`) gives zero inference overhead; keeping separate allows enable/disable and adapter swap. **For PersonaCore, keep-separate is load-bearing**: the live "memory on / memory off" toggle and the two-persona swap are the most visceral proofs that personalization lives in the adapter weights. Ship a `merge()` utility + an equivalence unit test (merged forward ≡ base+adapter forward within fp32 tolerance), but never merge in the demo path.
- **Expected behavior to pin in tests:** (a) zero-delta at init; (b) gradients flow only to A/B when base is frozen; (c) param count formula matches; (d) enable/disable round-trip restores base outputs exactly; (e) merge/unmerge equivalence.

### 2. EWC (Elastic Weight Consolidation)

**Mechanics (Kirkpatrick et al. 2017; "EWC Nuts and Bolts" arXiv:2105.04093 — HIGH confidence):**
- Penalty: `L = L_new + (λ/2)·Σᵢ Fᵢ·(θᵢ − θ*ᵢ)²` where `θ*` is the anchor (post-TinyStories weights) and `F` is the **diagonal Fisher information**.
- **Fisher estimation, the practical convention:** *empirical diagonal Fisher* — run the anchored model over a few hundred–few thousand task-A (TinyStories) sequences, accumulate `(∂ log p(y|x)/∂θ)²` per parameter using the actual next-token labels, average over batches. "True" Fisher samples labels from the model's own distribution; for LM next-token loss the empirical version is the standard, accepted shortcut and what virtually all EWC reimplementations do. One full pass at eval batch size is enough; Fisher tensors are stored alongside the anchor (open-dict checkpoint seam — already shipped).
- **Lambda:** there is **no universal value** — reported λ ranges span 0.1 to 10⁶ depending on loss scale, Fisher normalization, and task. The convention is a **log-scale sweep** (e.g., {10⁰, 10¹, …, 10⁵}) with short runs, picking λ* off the stability–plasticity tradeoff. Normalizing Fisher (e.g., divide by max or mean) makes λ comparable across runs and is worth doing.
- **Online vs offline:** online EWC (Schwarz et al. 2018) maintains a decayed running Fisher across many task transitions. PersonaCore has **one, at most two, transitions** (TinyStories→conversational; optionally conversational→persona). **Offline (vanilla) EWC is correct and simpler; online EWC is an anti-feature here.**
- **What a convincing no-forgetting A/B looks like (the falsifiable demo):**
  - Two arms, *identical* configs/seeds/data order, differing ONLY in `extra_penalties=(ewc,)` vs `()`.
  - Both arms log **two metrics every eval interval**: retention (TinyStories val PPL — v1.0's `perplexity()` on the same 12.6M held-out tokens, so the 2.1066 baseline is the anchor line) and acquisition (conversational val loss/PPL).
  - Convincing result = naive arm's TinyStories PPL degrades visibly (it will — DailyDialog is a large distribution shift from child-story prose) while the EWC arm stays near baseline, **and** the EWC arm's conversational loss is within a small, quantified gap of the naive arm's. Showing only retention is the classic mistake — EWC trivially "prevents forgetting" at λ→∞ by preventing learning. Both panels or it doesn't count.
  - Strongest form: a λ-sweep frontier plot (retention PPL vs acquisition PPL, one point per λ) — this is the genuinely research-grade figure.

### 3. Conversational fine-tuning at 13.9M params (DailyDialog + PersonaChat)

**Datasets (web-verified — HIGH confidence):**
- **DailyDialog** (Li et al. 2017): 13,118 two-speaker dialogues, avg 7.9 turns, ~14.6 tokens/utterance, ~103K utterances; splits 11,118/1,000/1,000. License CC BY-NC-SA 4.0 (fine for a non-commercial portfolio; cite it). Raw text downloadable from the author's site / mirrors — no HF `datasets` lib needed.
- **PersonaChat** (Zhang et al. 2018): 10,907 dialogues, 162,064 utterances, 1,155 personas of 3–5 short profile sentences ("i have two dogs", "i like to ski"); splits 8,939/1,000/968. Raw JSON copies are direct-downloadable (ParlAI/Kaggle/HF `resolve/` URLs) without any library dependency.
- Combined ≈ 265K utterances ≈ a few million tokens — one to two orders of magnitude smaller than TinyStories. This is a *fine-tune*, not a second pretrain: expect a few thousand steps, very feasible on M3/MPS.
- **PersonaChat's persona format is a gift to the narrative:** stage 2 can train the *skill* of persona-consistent dialogue (persona in context), so stage 3 personalization becomes "move the persona from the prompt into the weights" — a crisp prompt→weights distillation story.

**Formatting / loss-masking conventions (HIGH confidence):**
- Standard SFT convention: serialize dialogues with explicit turn markers; **compute loss only on bot-turn tokens** by setting user-turn label positions to `ignore_index=-100` in cross-entropy. Off-by-one at the user→bot boundary is the classic silent bug (model never learns how to *start* a response) — unit-test the mask against a hand-built fixture.
- Turn markers: with a frozen tokenizer, new special tokens can only come from **already-reserved ids in the 8192 table** (eos=8184 exists; check what else is reserved). If no reserved ids are free, plain-text tags (`User:` / `Bot:` + newline) encoded through the normal BPE are the accepted fallback — slightly more tokens, zero tokenizer risk. Dialogues separated by `<|endoftext|>` exactly as in pretraining.
- Pack multiple short dialogues per `block_size` window (DailyDialog dialogues are short); don't let attention cross `<|endoftext|>`? — at this scale the standard nanoGPT choice (let it cross, separator token is enough) is acceptable and is what v1.0 already does.

**Realistic quality at 13.9M (MEDIUM confidence — TinyStories paper + extrapolation):**
- TinyStories proved fluent, grammatical, instruction-following generation **below 10M params** (TinyStories-Instruct), so dialogue-format adherence and on-topic short replies are achievable.
- Expect: grammatical, short, *generic* daily-life responses with correct turn-taking; simple question answering; weak long-range persona consistency; occasional child-story register bleeding through (which is charming for the narrative, and exactly what the forgetting metrics quantify).
- Do NOT expect or promise: ConvAI2-leaderboard-style quality (winners used 117M+ GPT models), multi-hop reasoning, or robust open-domain chat. PPL numbers will not be comparable to literature (different tokenizer) — report own-tokenizer PPL plus curated qualitative transcripts, as v1.0 did.
- **Frozen-tokenizer tax (project-specific, important):** the BPE merges were learned on an 11.5KB TinyStories fixture (547 live ids). Conversational adult-life vocabulary will mostly miss those merges and encode near character/byte level → **sequence-length inflation** (fewer effective words per `block_size`) and more dead-id pressure. Byte-level fallback means encoding never *fails*, but measure tokens-per-word on DailyDialog early (cheap script) so the inflation is a documented number, not a surprise. This is accepted cost of the locked no-retrain decision.

### 4. Teach-then-recall personalization demos

No single canonical protocol exists (MEDIUM confidence — synthesized from knowledge-injection literature, esp. Ovadia et al. 2023 "Fine-Tuning or Retrieval?"); the defensible protocol assembled from it:

- **Facts:** 5–10 atomic user facts (name, city, pet's name + species, favorite color/food, occupation, a family fact). Fewer reads as a stunt; more risks capacity/recall issues at 13.9M.
- **Teaching data:** the literature's strongest finding — **fine-tuning injects facts reliably only with many paraphrased variations per fact** (accuracy rises monotonically with paraphrase count). Generate ~20–50 variants per fact as QA pairs and short dialogues, in both directions ("What's my dog's name?" → "Your dog is called Biscuit"; "Tell me about my pet" → …). **Zero-budget constraint: paraphrases must be template/hand-written — no external API augmentation.** Mix in a replay slice of generic conversational data so the adapter doesn't collapse into a single-topic parrot.
- **Mechanism:** train a LoRA adapter on the frozen conversational base (facts live *in the adapter weights* — small, swappable, inspectable). Crucially, the teaching dialogues must NOT carry the facts in a persona/system prefix — the model must produce persona-consistent answers from weights alone, otherwise the demo proves nothing.
- **Clean-room recall verification (what makes it falsifiable):**
  1. Fresh process; load base + adapter; **empty conversation history, no system prompt** — publish the exact (empty) prompt in the notebook so a reviewer can verify no carryover.
  2. Scripted question set: taught phrasings AND **held-out phrasings never seen in training** (generalization vs memorization — report both numbers separately).
  3. Scoring: keyword/substring match on the fact value (e.g., "biscuit" in the answer), case-insensitive; report recall as k/N with a pre-registered threshold (e.g., ≥80% taught, ≥50% held-out is honest at this scale).
  4. **Controls:** (a) base model without adapter on the same questions → near-0 recall; (b) adapter on unrelated questions → still behaves like a normal chatbot (no collateral collapse); (c) the strongest control: a *second* adapter with a different persona answering the same questions differently — same base weights, different memory, proving facts live in the adapter.

### 5. Forgetting curves & weight-delta heatmaps (canonical figures)

- **Forgetting curve (canonical since EWC paper Fig. 2):** x = fine-tuning steps on the *new* task; y = *old*-task metric (here: TinyStories val PPL, log-friendly); one curve per method (naive FT, EWC at λ*, optionally 2–3 λ values and a LoRA-only arm); horizontal dashed line = pre-fine-tuning baseline (2.1066). Companion panel: new-task val loss for the same arms (shows EWC isn't just refusing to learn). Data source is the existing CSV logger extended with a `retention_ppl` column — no new infra.
- **Weight-delta heatmap (convention from fine-tuning-analysis literature):** matrix with **layers (blocks) on one axis, module type on the other** (the six named projections: q/k/v/o/fc_up/fc_down — the v1.0 seam makes the grid trivial), cell = **relative change `‖ΔW‖_F / ‖W₀‖_F`** (relative, not absolute — embedding/LM-head magnitudes would otherwise dominate), log color scale. For the LoRA stage, cell = `(α/r)‖BA‖_F / ‖W₀‖_F` per adapted module — literally a map of *where the memory lives*. Canonical finding to look for: deltas concentrate in specific layers (often later blocks / MLP), which gives the writeup a concrete observation.
- **The juxtaposition that elevates both:** a matching **Fisher heatmap** (same layer×module grid, cell = mean diagonal Fisher) next to naive-vs-EWC delta heatmaps — visually showing EWC pushes updates *away from* high-Fisher coordinates. Three panels, one figure, the whole method legible at a glance. This is the single highest-leverage figure of the milestone.

---

## Feature Landscape

### Table Stakes (Reviewers Expect These — Absence = Claim Unproven)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **From-scratch `LoRALinear` wrapping the six named projections** | The committed novel mechanism; "from scratch, no PEFT" is the headline claim | MEDIUM | B=0/A-Gaussian init, α/r scaling, frozen-base grad flow, enable/disable, merge utility. Attaches via the v1.0 named-projection seam. |
| **LoRA correctness unit tests** | Reviewers will probe exactly these properties; v1.0 set the testing bar | LOW | Zero-delta at init; grads only to A/B; disable→bit-identical to base; merge≡unmerged; param-count formula. |
| **From-scratch EWC: Fisher estimation + quadratic penalty** | The committed continual-learning mechanism; plugs into `assemble_loss(extra_penalties=)` seam | MEDIUM | Empirical diagonal Fisher over TinyStories batches; anchor + Fisher stored in open-dict checkpoint. Penalty=0 at anchor is the key unit test. |
| **λ sweep / calibration** | EWC without tuned λ is either inert or frozen; reviewers know this | LOW | Log-scale sweep with short runs; normalize Fisher so λ is interpretable. Reuses v1.0 calibration discipline (D-07 pattern). |
| **DailyDialog + PersonaChat data pipeline** | Stage-2 curriculum is committed; from-scratch parsing keeps the no-HF-libs posture | MEDIUM | Direct download → parse → turn-tagged serialization → memmap. Must include the tokens-per-word inflation measurement on conversational text (frozen-tokenizer tax). |
| **Loss masking on user turns** | Standard SFT convention; its absence reads as not knowing how chat fine-tuning works | LOW | `ignore_index=-100` labels on user-turn tokens; boundary-correctness unit test against a hand-built fixture. |
| **Stage-2 conversational fine-tune (the run itself)** | Without a conversational base, the teach-then-recall demo can't answer questions | MEDIUM | Few-thousand-step FT on M3/MPS through the untouched v1.0 `train()`; eval = conversational val PPL + curated transcripts. |
| **Retention metric wired into training eval** | Both demos and both figures depend on logging TinyStories PPL *during* fine-tuning | LOW | Periodic `perplexity()` on a fixed TinyStories val slice; new CSV column. Watch the `forbid_ids`-not-in-`evaluate.py` tech debt here. |
| **EWC A/B no-forgetting experiment** | Committed demo; THE evidence that continual learning works | MEDIUM | Identical seeds/data order, ± penalty only; both retention AND acquisition reported (retention-only is the classic sleight of hand). |
| **Teach-then-recall clean-room demo** | Committed demo; THE evidence for "memory in weights, not prompt" | HIGH | Protocol in §4 above: 5–10 facts, template paraphrase augmentation, LoRA on frozen base, empty-prompt scripted recall, base-without-adapter control, pre-registered pass thresholds. |
| **Forgetting-curve figure (committed deliverable)** | Named in PROJECT.md; canonical CL evidence format | LOW | §5 spec; matplotlib from CSV, consistent with v1.0 figure style. |
| **Weight-delta heatmap figure (committed deliverable)** | Named in PROJECT.md; shows *where* memory lives | LOW–MEDIUM | §5 spec; relative Frobenius change on the layer×module grid; checkpoint-diff utility. |
| **REPORT/README v2.0 narrative + demo.ipynb update** | Document-as-we-go is a validated project requirement | MEDIUM | Honest numbers (recall %, retention deltas, tokenizer tax) in the same register as the v1.0 547-live-ids disclosure. |

### Differentiators (What Makes the Research Narrative Land)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Live adapter on/off toggle in the Gradio demo** | The most visceral proof possible: flip a switch, the model forgets you — same process, same prompt | LOW | Requires keep-separate LoRA (already the recommended default). One checkbox + adapter enable/disable. Demo-video gold. |
| **Two-persona adapter swap** | Same base weights, two adapters, two different "memories" — kills the "it's hidden in the prompt" objection dead | MEDIUM | Train a second small persona adapter; demo dropdown. Doubles as the strongest scientific control for teach-then-recall. |
| **Held-out-phrasing recall reporting** | Separates learning from memorization; exactly the distinction the knowledge-injection literature stresses | LOW | Just disciplined eval-set construction; report taught vs held-out recall separately. |
| **λ stability–plasticity frontier plot** | Elevates the A/B from "two curves" to an actual characterization of the method | LOW–MEDIUM | One point per λ from the sweep runs already needed for calibration; near-free if sweep logs are kept. |
| **Fisher heatmap juxtaposed with naive-vs-EWC delta heatmaps** | Makes EWC *visible*: updates dodge high-Fisher coordinates. Highest-leverage single figure of the milestone | MEDIUM | Fisher is already computed for the penalty; same grid code as the delta heatmap. |
| **Prompt-based persona as a measured baseline (control, not feature)** | Quantifies the novel claim: weight-based recall ≈ prompt-based recall, but survives an empty prompt | LOW | Same question set with facts stuffed in context vs adapter-only with empty prompt. Frame strictly as an experimental control. |
| **q,v-only vs all-six-projection LoRA ablation** | Continues the v1.0 ablation rigor; ties the implementation to the original paper's findings | MEDIUM | One config flag if the adapted-module list is configurable; short runs at the calibrated budget. |

### Anti-Features (Scope Traps / Claim-Weakeners)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Online EWC / multi-task EWC chains** | "More complete" continual learning | Designed for long task sequences; PersonaCore has 1–2 transitions; adds γ-decay machinery with zero narrative payoff | Vanilla offline EWC; mention online EWC in REPORT as known related work |
| **KFAC / block-diagonal / full Fisher** | "More accurate" importance estimates | Massive complexity; diagonal empirical Fisher is the accepted standard in every EWC reproduction | Empirical diagonal Fisher, normalized |
| **Tokenizer retrain on conversational data** | Would fix the 547-live-id inflation | Locked decision (2026-06-11): invalidates `best.pt`, restarts the milestone | Measure + document the inflation tax; dead-id mask already handles generation |
| **Chasing ConvAI2-style chat quality / benchmarks** | "Make the chatbot good" | Unreachable at 13.9M with this tokenizer; failure would overshadow the actual (achievable) claim | Frame quality as format adherence + fact recall; curated transcripts with honest framing |
| **External-API paraphrase generation for teaching data** | Easy high-quality augmentation | Violates zero-budget AND the privacy/on-device thesis at the exact moment the thesis is being demonstrated | Hand-written/template paraphrase grammar (~20–50 variants/fact is very feasible by template) |
| **Merging LoRA into base as the demo deploy path** | "Zero inference overhead" | Destroys the on/off toggle and persona swap — the two most convincing demo moments; overhead at 13.9M on CPU is irrelevant (~95–105 tok/s headroom) | Keep adapters separate; ship `merge()` + equivalence test as engineering completeness only |
| **Knowledge editing (ROME/MEMIT-style targeted edits)** | Trendy adjacent literature | Different mechanism, different claim; a from-scratch reimplementation is a milestone of its own | Cite as related work in REPORT |
| **RLHF / DPO / safety tuning** | "Real assistants have it" | Wrong milestone, wrong scale, needs preference data and reward modeling | Out of scope; SFT with loss masking is the right tool |
| **Facts in a system prompt at demo time** | Easiest way to make recall "work" | Falsifies the core claim — this is precisely what the project exists to NOT do | Empty-prompt clean room; prompt-stuffing appears only as a labeled experimental control |
| **Replay-buffer mixing as the headline anti-forgetting method** | Literature says replay often beats EWC in NLP | Storing old data to replay is *external memory adjacent* and dilutes the EWC narrative; also EWC is the committed deliverable | EWC as the method under test; a small replay arm is acceptable as an honest comparison line if budget allows, clearly labeled |

## Feature Dependencies

```
v1.0 six named nn.Linear projections (DONE)
    └──enables──> LoRALinear module + tests
                      ├──enables──> Teach-then-recall demo (adapter = memory)
                      ├──enables──> Adapter on/off toggle, two-persona swap (differentiators)
                      └──enables──> LoRA weight-delta heatmap (‖BA‖ per module)

v1.0 assemble_loss(extra_penalties=()) + open-dict checkpoints (DONE)
    └──enables──> EWC (Fisher estimation + penalty + anchor storage)
                      ├──requires──> λ sweep/calibration
                      └──enables──> EWC A/B no-forgetting experiment

v1.0 frozen tokenizer + memmap data path (DONE, with inflation tax)
    └──enables──> DailyDialog+PersonaChat pipeline (+ loss masking)
                      └──enables──> Stage-2 conversational fine-tune
                                        ├──requires──> retention metric in eval loop
                                        │                  (v1.0 perplexity(); forbid_ids debt)
                                        ├──is-arm-of──> EWC A/B experiment
                                        └──enables──> Teach-then-recall demo
                                                       (model must hold a QA/dialogue format first)

EWC A/B run logs ──enable──> Forgetting-curve figure (+ λ frontier)
Before/after checkpoints + Fisher tensors ──enable──> Heatmap figures
v1.0 Gradio demo (DONE) ──extends-to──> adapter toggle / persona dropdown
All experiments ──feed──> REPORT v2.0 + demo.ipynb update
```

### Dependency Notes

- **Teach-then-recall requires the conversational base first:** a TinyStories-only model can't hold a QA exchange; recall questions would fail for format reasons, not memory reasons. Stage-2 FT must precede the personalization phase.
- **EWC A/B requires the retention metric inside the training loop**, not just post-hoc: forgetting curves need per-eval-interval TinyStories PPL. Thread `forbid_ids`/dead-id handling into `evaluate.py` first (existing v1.0 tech debt lands on the critical path here).
- **Both demos depend on keep-separate LoRA** — merging is incompatible with the toggle/swap moments.
- **The Fisher heatmap is nearly free once EWC exists** (same tensors, same grid code as the delta heatmap) — schedule them in the same phase.
- **Conflict — LoRA-everywhere vs the naive-forgetting arm:** if stage-2 conversational FT itself used LoRA, the naive arm would barely forget (tiny trainable capacity) and the EWC A/B would be hollow. The clean design: **stage-2 = full fine-tune ± EWC** (the A/B), **stage-3 personalization = LoRA on the frozen conversational base** (the teach-then-recall). Each mechanism gets the stage where its effect is real and measurable.

## MVP Definition

### Launch With (v2.0 committed scope)

- [ ] `LoRALinear` from scratch + full unit-test suite — the novel mechanism, half the milestone's name
- [ ] EWC from scratch (empirical diagonal Fisher, penalty via seam, anchor/Fisher in checkpoint) + tests — the other half
- [ ] DailyDialog + PersonaChat pipeline with turn tagging + user-turn loss masking + inflation measurement — stage-2 prerequisite
- [ ] Stage-2 conversational fine-tune with retention metric logged — both demos stand on this
- [ ] EWC A/B experiment (identical-config arms, retention + acquisition both reported) — committed demo #2
- [ ] Teach-then-recall clean-room demo (5–10 facts, template paraphrases, LoRA adapter, empty-prompt scripted eval, base-without-adapter control, pre-registered thresholds) — committed demo #1, the core-value proof
- [ ] Forgetting-curve figure + weight-delta heatmap figure, committed to repo — named deliverables
- [ ] REPORT/README/demo.ipynb v2.0 narrative with honest numbers — validated project requirement

### Add After Validation (low-cost, high-narrative)

- [ ] Adapter on/off toggle in Gradio — trigger: as soon as teach-then-recall passes its threshold (LOW cost, demo-video gold)
- [ ] Held-out-phrasing recall split — trigger: when building the recall question set (costs only eval discipline)
- [ ] Fisher heatmap juxtaposition panel — trigger: when delta-heatmap grid code exists
- [ ] λ frontier plot — trigger: if sweep logs were retained (make retention a sweep requirement)
- [ ] Prompt-persona control row in the results table — trigger: when writing REPORT, one extra eval run

### Future Consideration (defer)

- [ ] Two-persona adapter swap — strongest control, but needs a second teaching set + adapter run; add only if the first adapter lands cleanly within budget
- [ ] q,v-only vs all-six LoRA ablation — defer until main results exist; reuse v1.0's calibrated-short-run pattern
- [ ] Small replay-comparison arm — only if M3 budget remains and only as a clearly-labeled honesty line

## Feature Prioritization Matrix

| Feature | Reviewer Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| LoRALinear + tests | HIGH | MEDIUM | P1 |
| EWC + Fisher + tests | HIGH | MEDIUM | P1 |
| Conversational data pipeline + masking | HIGH | MEDIUM | P1 |
| Stage-2 fine-tune + retention logging | HIGH | MEDIUM | P1 |
| EWC A/B experiment | HIGH | MEDIUM | P1 |
| Teach-then-recall clean-room demo | HIGH | HIGH | P1 |
| Forgetting curve + delta heatmap figures | HIGH | LOW–MEDIUM | P1 |
| REPORT/notebook v2.0 update | HIGH | MEDIUM | P1 |
| Adapter on/off Gradio toggle | HIGH | LOW | P2 |
| Held-out-phrasing recall split | MEDIUM | LOW | P2 |
| Fisher heatmap juxtaposition | HIGH | LOW (once grid exists) | P2 |
| λ frontier plot | MEDIUM | LOW | P2 |
| Prompt-persona measured control | MEDIUM | LOW | P2 |
| Two-persona adapter swap | HIGH | MEDIUM | P3 |
| LoRA projection ablation | MEDIUM | MEDIUM | P3 |
| Replay comparison arm | LOW | MEDIUM | P3 |

**Priority key:** P1 = committed milestone scope · P2 = add when its prerequisite lands (all are cheap riders) · P3 = budget-permitting

## Reference-Implementation Analysis

(Stands in for "competitor analysis" — how the canonical implementations do it vs our from-scratch approach.)

| Concern | HF PEFT / literature convention | Our approach |
|---------|--------------------------------|--------------|
| LoRA init | A Kaiming-uniform (PEFT) or Gaussian (paper), B zero | Gaussian A, zero B — paper-faithful, unit-tested zero-delta |
| LoRA targets | q,v (paper) → all-linear (QLoRA-era practice) | All six named projections by default, configurable list for the ablation |
| LoRA deploy | Usually merged for serving | Deliberately unmerged — toggle/swap IS the demo |
| Fisher | Empirical diagonal, one pass over old-task data | Same, normalized; stored with anchor in open-dict checkpoint |
| λ | Per-setup log-scale sweep, no universal value | Short-run sweep at the D-07-calibrated budget; frontier plot from sweep logs |
| SFT masking | `assistant_only_loss` / labels=-100 on non-assistant tokens | Hand-rolled mask with `ignore_index=-100`, fixture-tested at the turn boundary |
| Fact injection | Many paraphrases per fact (Ovadia et al.); RAG usually wins in their setting | Template paraphrases (zero-budget); RAG excluded by design — the point is weights-only |
| Forgetting evidence | Old-task curve during new-task training (EWC paper Fig. 2 pattern) | Same, with PPL; plus acquisition panel and λ frontier to preempt the "EWC just refuses to learn" critique |

## Sources

- LoRA: Hu et al. 2021, [arXiv:2106.09685](https://arxiv.org/pdf/2106.09685) (init, α/r, q-v finding) — HIGH; [Unsloth LoRA hyperparameters guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide) + [HF PEFT LoRA docs](https://huggingface.co/docs/peft/main/en/developer_guides/lora) (all-linear practice, merge-vs-separate, r/α conventions) — HIGH; [Impact of Initialization on LoRA](https://arxiv.org/html/2406.08447v1) — MEDIUM
- EWC: Kirkpatrick et al. 2017 (PNAS; training knowledge, mechanics stable) — HIGH; ["EWC Nuts and Bolts"](https://arxiv.org/pdf/2105.04093) (empirical diagonal Fisher practice) — HIGH; [EWC for KG continual learning empirical eval](https://arxiv.org/html/2512.01890) (λ is setup-dependent, sweep required) — MEDIUM; [EWC for bias inoculation](https://aclanthology.org/2021.eacl-main.82.pdf) (LM-context EWC usage) — MEDIUM
- DailyDialog: [yanran.li/dailydialog](http://yanran.li/dailydialog.html) + [arXiv:1710.03957](https://arxiv.org/pdf/1710.03957) (13,118 dialogues, 7.9 turns avg, CC BY-NC-SA 4.0) — HIGH
- PersonaChat: Zhang et al. 2018 ([arXiv:1801.07243], stats corroborated by [persona-chat dataset mirrors](https://huggingface.co/datasets/Cynaptics/persona-chat), [Kaggle copy](https://www.kaggle.com/datasets/atharvjairath/personachat)) — 10,907 dialogues / 162,064 utterances / 1,155 personas of 3–5 sentences — HIGH
- Small-model achievability: [TinyStories paper](https://arxiv.org/abs/2305.07759) (coherent generation + TinyStories-Instruct instruction following below 10M params) — HIGH
- SFT masking conventions: [HF TRL SFTTrainer docs](https://huggingface.co/docs/trl/v0.20.0/en/sft_trainer) (`assistant_only_loss`, labels=-100) + [SFT data formatting guide](https://apxml.com/courses/fine-tuning-adapting-large-language-models/chapter-2-data-preparation-fine-tuning/formatting-sft-data) — HIGH
- Fact injection / paraphrase augmentation: Ovadia et al., ["Fine-Tuning or Retrieval?"](https://arxiv.org/pdf/2312.05934) (recall rises monotonically with paraphrase count; repetition-in-many-forms required) — HIGH for the augmentation finding
- Forgetting-figure conventions: EWC paper Fig. 2 pattern + [layer-wise regularization for LLM forgetting](https://arxiv.org/html/2501.13669v2) (perplexity-on-old-task curves) — MEDIUM
- Project context: `/Users/juliorcoelho/PersonaCore/.planning/PROJECT.md` (v1.0 seams, locked tokenizer decision, tech debt) — HIGH

---
*Feature research for: PersonaCore v2.0 Weight-Based Memory (LoRA + EWC + conversational FT + research-narrative demos)*
*Researched: 2026-06-11*
