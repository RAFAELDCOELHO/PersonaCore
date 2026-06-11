# Pitfalls Research

**Domain:** Adding from-scratch LoRA + EWC + conversational fine-tuning + research demos (v2.0 Weight-Based Memory) to an existing 13.9M-param from-scratch GPT (PersonaCore v1.0)
**Researched:** 2026-06-11
**Confidence:** HIGH (LoRA/EWC mechanics verified against papers, framework issue trackers, and post-mortems; dataset/tokenizer-interaction specifics MEDIUM where they depend on unmeasured properties of this repo's frozen tokenizer)

**System-specific context that shapes every pitfall below:**
- Base: `best.pt` (val_loss 0.7378, TinyStories PPL 2.1066 over 12.6M held-out tokens), weight tying via a **single shared tensor** (embedding ≡ lm_head)
- Tokenizer: **frozen, 547 live ids of 8192** (fixture-trained, kept by explicit v2.0 decision), dead-id `forbid_ids` mask at the sampling layer only — **not** threaded into `evaluate.py` (known debt)
- Seams: six named `nn.Linear` projections per block (LoRA), `assemble_loss(..., extra_penalties=())` (EWC), open-dict checkpoints with RNG restore
- Training: M3/MPS **fp32 only** (no AMP), torch 2.7.* pinned, Kaggle P100 fp16 optional fallback
- The novel claim ("memory lives in weights, not prompts") must survive a skeptical MIT/Stanford-bar reviewer

---

## Critical Pitfalls

### Pitfall 1: LoRA touches the tied embedding/lm_head tensor

**What goes wrong:**
An adapter is attached to (or merged into) `lm_head` or the token embedding. Because both are **one shared tensor** in this model, merging the adapter into "the lm_head" silently also rewrites the input embedding — corrupting input representations for every token. HF PEFT has a string of open issues on exactly this (peft #2018, #2777, #2864): merging an lm_head adapter onto tied weights merges into the embedding too, and naive "untie to fix it" silently doubles parameters and invalidates the tying invariant the v1.0 test suite pins (`data_ptr` tying gate).

**Why it happens:**
The tied tensor appears under two module paths; adapter-attachment code that walks `named_modules()` by class (`isinstance(m, nn.Linear)`) instead of by the six **named** seam projections will pick up the output head.

**How to avoid:**
- LoRA targets are an **explicit allowlist of the six named per-block projections** — never a class-based scan. The v1.0 seam was designed for this; honor it.
- Add a unit test: after wrapping, assert the embedding/lm_head tensor's `data_ptr()` is unchanged and appears in **zero** adapter target lists.
- Document the decision ("we do not adapt embeddings because they are tied; personalization capacity lives in the block projections") in the writeup — it preempts a reviewer question.

**Warning signs:** parameter count of trainables includes a `vocab × d_model`-shaped matrix; tying test starts failing; base-model PPL changes after a merge that "only touched the head."

**Phase to address:** LoRA implementation phase (first v2.0 phase).

---

### Pitfall 2: Adapter is not a no-op at initialization

**What goes wrong:**
Standard LoRA init is A ~ small random, **B = 0**, so ΔW = (α/r)·B·A = 0 and the wrapped model is bit-identical to the base at step 0. If both A and B are randomly initialized (a common from-scratch mistake), the model is perturbed before any training: TinyStories PPL degrades immediately, the forgetting-curve baseline is poisoned, and every downstream A/B starts from a corrupted reference point.

**Why it happens:**
Symmetric-init habit from writing the transformer (`init_std` everywhere); nothing crashes, generation still looks plausible.

**How to avoid:**
- Init B to zeros; test: wrapped model and base model produce **bit-identical logits** (fp32, CPU) on a fixed batch before training. This is the single highest-value LoRA unit test.
- Also assert PPL(base) == PPL(wrapped, step 0) through the real `perplexity()` harness — this doubles as the forgetting-curve t=0 anchor.

**Warning signs:** step-0 eval PPL ≠ 2.1066-equivalent on the same split; "fine-tuning improved TinyStories PPL" early in a run (it's recovering self-inflicted damage).

**Phase to address:** LoRA implementation phase; the identity test becomes a permanent suite member.

---

### Pitfall 3: α/r scaling inconsistencies (forward vs merge vs hyperparameter sweeps)

**What goes wrong:**
Three distinct bugs hide in one constant:
1. **Double-scaling at merge:** forward applies `(α/r)·B·A` and merge applies it again → merged model ≠ adapter model.
2. **Missing scaling:** ΔW applied unscaled; behavior then depends on r in an uncontrolled way, and any rank sweep for the report confounds rank with effective LR.
3. **Convention drift:** mixing classic `α/r` and rsLoRA `α/√r` between code paths or between report text and code. (rsLoRA exists precisely because classic scaling degrades at high rank — at this project's likely r of 4–16, classic `α/r` is fine; just pick one and pin it.)

**Why it happens:**
The scale is applied in two places (forward pass, merge function) written at different times; from-scratch code has no library invariant enforcing consistency.

**How to avoid:**
- One source of truth: a `scale` property on the LoRA module; both forward and merge read it.
- **Merge-equivalence test:** merged weights vs live-adapter logits agree within fp32 tolerance (≤1e-5) on a fixed batch — run on CPU for determinism (MPS reductions are not bit-stable). This is the test that catches all three bugs.
- Record α, r, and the scaling convention into the open-dict checkpoint (config travels with weights — v1.0 pattern).

**Warning signs:** demo behaves differently after "export for inference"; rank sweep shows wild LR sensitivity; adapter trained at r=8 behaves differently when re-loaded.

**Phase to address:** LoRA implementation phase (merge-equivalence test is an acceptance criterion).

---

### Pitfall 4: Optimizer/checkpoint state mishandled across the pretrain→fine-tune boundary

**What goes wrong:**
- Resuming fine-tuning **from the pretrain optimizer state**: `best.pt` is open-dict with AdamW moments for the base params. Loading it and continuing with a different trainable set (LoRA params now exist, base frozen) either crashes or — worse — silently applies stale momentum to params that should be frozen.
- Passing `model.parameters()` wholesale to AdamW: PyTorch skips grad-None params so it "works," but weight-decay/param-group bookkeeping becomes ambiguous, the optimizer state dict bloats, and resume-after-kill (a v1.0 guarantee) can re-attach moments to the wrong params if ordering changes.
- Saving adapter checkpoints with `strict=True`/`strict=False` confusion: loading a base checkpoint into a LoRA-wrapped model with `strict=False` silently leaves randomly-initialized adapter keys in place.

**Why it happens:**
The v1.0 checkpoint/resume infra is excellent but was built for "one model, one param set." The fine-tune boundary changes the param set.

**How to avoid:**
- Fine-tuning starts with a **fresh optimizer** over `[p for p in model.parameters() if p.requires_grad]` only. Never load pretrain optimizer state into a fine-tune run.
- Adapter-aware checkpoints: save `{base_weights_hash, adapter_state, optimizer, rng, step, config}`. The adapter checkpoint references (hashes) the base it sits on — prevents loading an adapter onto the wrong base.
- Explicit key audit on load: assert missing/unexpected key sets are **exactly** the expected adapter/base partition; fail loudly otherwise. No bare `strict=False`.
- Freezing is asserted, not assumed: a test checks `requires_grad` is False for every base param and True for every adapter param, and a **canary training step** asserts base params are bit-unchanged after `optimizer.step()`.

**Warning signs:** trainable-param count ≠ expected (6 seams × layers × 2 matrices × r); base PPL drifts during "LoRA-only" training; resume produces a different loss trajectory than the kill point.

**Phase to address:** LoRA implementation phase (checkpoint format), re-verified in fine-tuning phase (resume mid-fine-tune).

---

### Pitfall 5: MPS-specific silent training failures (the Adam/contiguity class of bug)

**What goes wrong:**
The canonical post-mortem (Elana Simon, 2025): on MPS, fused Adam ops (`addcmul_`/`addcdiv_`) **silently failed to update non-contiguous parameters** — gradients flowed, loss plateaued, weights froze, no error. Trigger: params created as transposed views (`W.T.clone()` patterns — exactly what LoRA init code tends to write when sizing A/B from the wrapped layer). That specific kernel bug is fixed in torch ≥2.4 (project pins 2.7.*) and this dev box's macOS has native strided support, but the **class** of bug is alive: MPS still has silent CPU fallbacks, looser FP exception behavior ("silent NaN" — garbage propagates for hours without erroring), and random-op issues on older macOS (<15) until torch 2.10.

**Why it happens:**
MPS is the least-exercised backend; failures are silent rather than loud, and a 13.9M-param fine-tune "running fine" with a flat loss looks like a hyperparameter problem, not a kernel bug.

**How to avoid:**
- Make every LoRA param `.contiguous()` at creation (free; eliminates the entire bug class).
- **Params-actually-update canary** in the training loop's first step: snapshot trainable params, take one step, assert every trainable tensor changed and every frozen tensor didn't. Cheap, runs on every backend, would have caught the post-mortem bug in seconds.
- NaN/inf guard each eval interval (`torch.isfinite(loss)` + a finite-check over adapter params); fail fast rather than train garbage on a backend that won't raise.
- Keep the v1.0 discipline: correctness tests run on CPU; MPS is a performance backend whose outputs are checked against CPU on fixed batches at coarse tolerance.

**Warning signs:** fine-tune loss flatlines from step 0 while gradients are nonzero; adapter param norms never move; results differ wildly between CPU smoke test and MPS run.

**Phase to address:** LoRA implementation phase (canary test), inherited by all subsequent training phases.

---

### Pitfall 6: Fisher information computed wrong (the single most-copied EWC bug)

**What goes wrong:**
van de Ven (ICLR 2025 blogpost track, arXiv 2502.11756) shows the most common EWC implementation in the wild — squaring **mini-batch-aggregated** gradients instead of per-example gradients — is not the Fisher at all (cross-terms don't vanish; magnitude scales wrong), yet it's what popular continual-learning libraries shipped. Consequences here: the penalty protects the wrong coordinates, the required λ shifts by **orders of magnitude** versus correct implementations, and the "EWC works" A/B becomes untrustworthy. Adjacent variants of the same pitfall:
- Fisher computed on the **wrong data**: it must be computed on task-A data (TinyStories) at the task-A optimum (`best.pt`), not on the fine-tuning data and not mid-fine-tune.
- Fisher computed in **train mode**: dropout noise corrupts the estimate. Gradients work fine under `model.eval()`; use eval mode.
- **Loss-reduction mismatch:** mean-over-tokens vs sum-over-tokens changes Fisher magnitude by ~block_size×; if the Fisher normalization doesn't match `assemble_loss`'s reduction convention, λ calibration is meaningless and non-portable.

**Why it happens:**
PyTorch makes batch gradients easy and per-example gradients awkward, so people square the batch gradient; papers rarely specify which variant they used.

**How to avoid:**
- Compute the **empirical Fisher per-example**: loop examples (or microbatch=1), `loss.backward()`, accumulate `grad²`, divide by N. At 13.9M params this is entirely feasible on the M3 — a few thousand TinyStories windows is enough (the paper found sample size matters; document N).
- For an LM, "exact" Fisher (expectation over all 8192 classes per position) is expensive; the standard, defensible choice is empirical Fisher over ground-truth next tokens **stated explicitly in the writeup** as an approximation, with the citation. A skeptical reviewer who knows this paper will check whether you say which variant you used.
- Compute on `model.eval()`, on TinyStories windows, at the exact base checkpoint, with the **same loss function/reduction** the training loop uses (reuse the v1.0 loss path, not a reimplementation).
- Unit tests: Fisher entries are all ≥0; Fisher of a param with zero gradient is 0; Fisher is invariant to batch ordering; a hand-checkable tiny-model fixture matches an analytic/brute-force Fisher.
- Persist Fisher + θ* snapshot as an artifact with provenance (base SHA/hash, data slice, N, mode) — it's an input to every EWC run and must be reproducible.

**Warning signs:** working λ is absurdly small (penalty is a no-op) or absurdly large (>1e8); Fisher recomputed with a different batch size changes results dramatically (the batched-gradient bug's signature); penalty value at step 0 is nonzero (θ=θ* should give exactly 0).

**Phase to address:** EWC phase. This pitfall justifies that phase carrying a "needs deeper research/verification" flag.

---

### Pitfall 7: EWC penalty applied to the wrong parameter space (LoRA params vs base params)

**What goes wrong:**
Classic EWC penalizes drift of the **base parameters**: λ/2 · Σ Fᵢ(θᵢ − θ*ᵢ)². Two confusions arise the moment LoRA enters:
1. **Computing "Fisher of the LoRA params"** at adapter init is degenerate: B=0 means ∂loss/∂A ≡ 0, so A's Fisher is exactly zero and B's Fisher is uninformative — the penalty is mathematically meaningless. Anyone who wires `extra_penalties` to "Fisher over trainable params" gets this silently.
2. **Penalizing nothing:** if only LoRA trains and base weights are frozen, base θ never moves, the classic penalty is constantly zero, and "EWC" is dead code while the A/B chart credits it with the retention that **frozen-base LoRA produces by construction** (LoRA's lower forgetting is a documented property — "LoRA Learns Less and Forgets Less," arXiv 2405.09673).

The correct LoRA+EWC formulation penalizes the **effective weight drift**: for each adapted layer, ΔW = scale·B·A, penalty = λ/2 · Σ F_W ⊙ (ΔW)², using the **base-model Fisher of W**. It is differentiable w.r.t. A and B and slots cleanly into `extra_penalties`.

**Why it happens:**
Tutorial EWC assumes full fine-tuning; tutorial LoRA assumes no EWC. Their composition is genuinely non-obvious and this project is composing them from scratch.

**How to avoid:**
- Decide and document the regime per training stage **before implementation**: (a) stage-2 conversational tuning — if it's a full fine-tune, classic EWC on base params applies directly; (b) personalization — if it's LoRA-only, use the effective-ΔW penalty with base Fisher (or accept that EWC isn't doing the work there and say so honestly).
- Unit tests: penalty is 0 at init (ΔW=0 / θ=θ*); penalty gradient w.r.t. A and B is nonzero once B≠0; penalty grows monotonically as ΔW grows along a fixed direction.
- The tied embedding tensor must appear **once** in the Fisher/θ* snapshot. Snapshotting via `state_dict()` can carry the same storage under two keys; deduplicate by `data_ptr()` or the penalty double-counts that tensor.

**Warning signs:** logged EWC penalty is exactly 0.0 for the whole run; EWC and naive arms produce identical trajectories; Fisher artifact contains entries for adapter keys.

**Phase to address:** EWC phase, with the regime decision made during that phase's planning (it affects the A/B design).

---

### Pitfall 8: λ mis-scaling makes EWC a no-op or a freeze — and nobody notices

**What goes wrong:**
λ interacts with Fisher magnitude (which depends on loss reduction, N, and implementation variant — see Pitfall 6; van de Ven measured orders-of-magnitude shifts in usable λ between variants). Too small: penalty is decorative, the "EWC" arm is a naive arm, and the A/B shows no difference ("EWC doesn't work"). Too large: adaptation is crushed, the model can't learn the new task, and the A/B shows beautiful retention with zero teaching ("EWC works!" — but the model learned nothing new). Published EWC results also show over-regularization can *increase* forgetting in some settings.

**Why it happens:**
λ is copied from a paper whose Fisher normalization differs; and both failure modes look like *results*, not bugs.

**How to avoid:**
- Log **both terms separately** every eval interval: task loss and EWC penalty. Healthy training has them within ~1–2 orders of magnitude of each other after warm-in; ratios of 1e-6 or 1e+4 are diagnoses, not data.
- Sweep λ over orders of magnitude (e.g., {0, 1e0, 1e1, 1e2, 1e3, 1e4} relative to your normalization) on a short run; pick by the **two-axis criterion** (new-task loss AND old-task PPL). This sweep is cheap at 13.9M params and is itself a portfolio-grade figure.
- The no-forgetting demo must report both axes (see Pitfall 10).

**Warning signs:** EWC arm and naive arm overlap exactly; EWC arm's fine-tune loss never decreases; final report has retention numbers but no new-task numbers.

**Phase to address:** EWC phase (sweep), no-forgetting demo phase (reporting).

---

### Pitfall 9: TinyStories PPL drift measured inconsistently across the milestone

**What goes wrong:**
The forgetting curve is only meaningful if every point is computed by the **identical** harness. Ways this breaks in this repo specifically:
- `evaluate.py` does not apply the `forbid_ids` mask (known v1.0 debt). That's fine *as long as no point in the curve ever applies it* — mixing masked and unmasked PPL silently shifts numbers (masking dead ids renormalizes the softmax over ~547 ids and **lowers** PPL).
- Evaluating the adapter model sometimes merged, sometimes unmerged, sometimes accidentally with adapters dropped (loading slim base weights into the eval path) — three subtly different models labeled as one.
- Eval in train mode (dropout on) for some points.
- fp16 Kaggle-fallback evals mixed with fp32 MPS evals in one curve.
- The `run.csv` tokens-column ×256 under-count (known debt): any forgetting curve plotted against "tokens seen" inherits a 256× x-axis error.

**Why it happens:**
Forgetting curves accumulate points across weeks and code revisions; tiny harness drift between points is invisible until someone tries to reproduce a single point.

**How to avoid:**
- One blessed entry point: the v1.0 `perplexity()` (already proven against a brute-force oracle) is the **only** function that produces curve points; it takes (checkpoint, adapter-or-none) and records config provenance per point.
- Decide the mask policy once (recommended: **no** forbid_ids in PPL, matching the v1.0 headline 2.1066, stated in the writeup), and add an assertion so it can't drift.
- Fix the run.csv ×256 token-count bug **before** the first fine-tune run, since the forgetting-curve x-axis depends on it.
- Each curve point's row records: base hash, adapter hash, merged?, eval split, mode, dtype, mask policy.

**Warning signs:** step-0 fine-tune point doesn't reproduce 2.1066-equivalent PPL; curve has a discontinuity at a date boundary rather than a training event; re-running an old point gives a different number.

**Phase to address:** Fine-tuning phase establishes the harness contract; visualization phase consumes it. The run.csv fix is a pre-phase cleanup item.

---

### Pitfall 10: The A/B "proves" EWC while actually measuring something else

**What goes wrong:**
A skeptical reviewer can dismantle a naive no-forgetting demo three ways:
1. **Stability-plasticity confound:** EWC reduces effective plasticity. If the EWC arm retains TinyStories but learned less dialogue/persona, the honest summary is "EWC = lower learning rate." The demo must show new-task **parity** (or a quantified trade-off), not just old-task retention.
2. **Arm mismatch:** different seeds, data order, LR schedules, or step counts between arms. With v1.0's seeding/RNG-restore infra there is no excuse — arms must differ in exactly one bit (λ>0).
3. **LoRA confound:** if both arms are LoRA-based, frozen-base LoRA already forgets less by construction; if the naive arm is a *full* fine-tune while the EWC arm is LoRA+EWC, the chart credits EWC for what the architecture did. Arms must share the adaptation mechanism.

**Why it happens:**
The desired conclusion is known in advance ("EWC prevents forgetting"), which is exactly the confirmation-seeking failure mode.

**How to avoid:**
- Pre-register the A/B design in the phase plan: same mechanism (e.g., both full-FT, or both LoRA at same r/α/LR/steps/seed), λ the only difference; optionally a third arm (naive at reduced LR) to directly address the "EWC is just damping" critique.
- Report a 2×2 result: {new-task metric, TinyStories PPL} × {naive, EWC}, plus the forgetting curve over steps for both arms.
- Commit all transcripts/configs; the executed notebook regenerates the figure from the CSV.

**Warning signs:** the planned figure only has a retention axis; arms were run on different days from different commits; the naive arm's hyperparameters were chosen after seeing EWC results.

**Phase to address:** No-forgetting demo phase (design pre-registered during EWC phase planning).

---

### Pitfall 11: Prompt leakage fakes weight-based memory (the demo-killing pitfall)

**What goes wrong:**
The teach-then-recall demo claims facts live in weights — and then recall is demonstrated **in the same Gradio chat session where the facts were typed**. `gr.ChatInterface` feeds the conversation history back into the context on every turn, so the model is doing ordinary in-context lookup and the novel claim is false as demonstrated. Subtler leakage: a system preamble mentioning the user; the teaching script's eval prompts containing the fact; the recall question itself embedding the answer; or the demo process reading any file other than weights.

**Why it happens:**
The chat UI's defining feature (history) is precisely the thing the demo must exclude, and the leak produces *better-looking* results, so nothing motivates noticing it.

**How to avoid (clean-room protocol — make it a deliverable, not a habit):**
1. Teach: fine-tune on the facts; save adapter; **kill the process**.
2. Recall: fresh process, fresh session, empty history, no system prompt; load base + adapter (log both hashes).
3. **Context transparency:** the demo logs/displays the exact token ids fed to the model at recall time — auditable proof the fact string isn't in context. This single feature converts "trust me" into "check it."
4. Controls: (a) base model + same recall prompt → fails; (b) base model + fact-in-prompt → succeeds (shows the question is answerable in-context, i.e., the question is fair); (c) adapter + empty context → succeeds. The triple is the proof.
5. Recall questions must be **closed-book fair**: paraphrased, never containing the answer, and the fact must be un-guessable by the base model (verify control (a) actually fails — TinyStories contains common names; pick facts outside its distribution).

**Warning signs:** recall works on turn 2 of the teaching session but was never tested in a fresh session; recall accuracy drops to zero in a fresh process (the memory was the context all along); the recall prompt contains the taught entity pair.

**Phase to address:** Teach-then-recall demo phase — the clean-room protocol IS the phase's acceptance criterion.

---

### Pitfall 12: Teaching facts to a 13.9M model fails or only echoes verbatim

**What goes wrong:**
Knowledge-injection research is unambiguous: fine-tuning a fact in **one phrasing** produces a model that completes that exact phrasing but fails QA-style recall and reversed forms (the reversal curse: trained "A is B," can't answer "B is A?"). At 13.9M params on a 547-live-id tokenizer, this bites doubly: the model is small, and the taught entity (a name like "Zorp") fragments into several near-character-level tokens the model must emit in exact sequence under greedy decoding. The demo then either fails outright or "succeeds" only on the training phrasing — which a reviewer will probe in one minute.

**Why it happens:**
"Fine-tune on the fact sentence N times" is the intuitive teaching procedure; generalization requires paraphrase diversity, which feels like cheating but is documented mechanism (QA capability scales with paraphrase count, saturating around ~10 per fact — arXiv 2404.00213).

**How to avoid:**
- Teaching set per fact: ~10–20 paraphrases **plus QA forms in both directions** ("My dog is named Zorp" / "What's my dog's name? Zorp" / "Who is Zorp? My dog"). Hold out paraphrases for evaluation.
- Evaluate recall as a **success rate** over held-out paraphrases × multiple decode seeds (and greedy), not a single transcript. Commit all transcripts including failures; report e.g. "9/12 held-out phrasings."
- Pre-flight the entity through the tokenizer: print its token split; prefer facts whose surface forms tokenize into ≤4–6 live tokens; verify none of its ids are in `forbid_ids` (a masked id would make the fact **unutterable** at sampling time while training loss looks fine).
- Calibrate expectations in the writeup: this is a 13.9M model; partial recall honestly reported beats perfect recall suspiciously reported.

**Warning signs:** recall works only with the exact training prefix; success flips with temperature; the taught name decodes as 12 byte-fragments; loss on teaching data → 0 in a few steps (pure memorization).

**Phase to address:** Teach-then-recall demo phase, with tokenizer pre-flight done in the fine-tuning phase.

---

### Pitfall 13: The 547-live-id tokenizer meets real dialogue text

**What goes wrong:**
The frozen tokenizer was trained on an 11.5KB fixture; only 547 of 8192 ids are reachable. On TinyStories this was survivable. DailyDialog/PersonaChat vocabulary (casual register, names, contractions, topics far outside the fixture) will fragment toward character/byte level: tokens-per-word blows up, so (a) a fixed block_size covers far less conversation — multi-turn PersonaChat context + persona lines may not fit a single window at all; (b) compute per unit of dialogue inflates; (c) every rare word becomes a long exact sequence the small model must emit. Separately, two tempting "fixes" are traps:
- **Repurposing dead ids as new special tokens** (turn separators, speaker tags): dead rows received gradient throughout pretraining *via the tied lm_head* (the softmax denominator pushes all logits down), so they start as strongly-suppressed directions, and `forbid_ids` will mask them at sampling unless the mask, tokenizer table, slim export, and demo are all updated in lockstep.
- **Retraining the tokenizer**: explicitly decided against at v2.0 kickoff (invalidates `best.pt`). Re-litigating it mid-milestone is a schedule trap.

**Why it happens:**
The tokenizer debt was honestly documented but its *cost is corpus-dependent*, and v2.0 changes the corpus.

**How to avoid:**
- **Measure before building:** first task of the fine-tuning phase = encode a DailyDialog and PersonaChat sample with the frozen tokenizer; report tokens/word, % sequences exceeding block_size, and the fragmentation of typical names. This number gates the data-format design (turn truncation strategy, persona-line budget).
- Dialogue formatting with **existing live machinery only**: prefer plain-text conventions the 547-id vocabulary can already express (e.g., newline-based turn structure as plain text) over new special tokens. The eos id (8184) keeps its document-separator semantics; if it must double as a turn separator, decide that explicitly and test that generation's EOS-stop logic doesn't truncate mid-conversation (the v1.0 `generate()` stops on EOS).
- If a special token is genuinely needed, treat it as a mini-project: pick a dead id, re-warm its embedding row, remove it from `forbid_ids`, update slim export + demo + tests, and document the surgery.

**Warning signs:** tokens/word > ~2.5–3 on dialogue samples; median PersonaChat example > block_size; generated dialogue truncates at first turn boundary; demo crashes or emits nothing when the new separator id is sampled.

**Phase to address:** Conversational fine-tuning phase — the measurement is that phase's first deliverable and a go/no-go gate for the data format.

---

### Pitfall 14: Loss-masking and formatting bugs in dialogue fine-tuning

**What goes wrong:**
Two different masking regimes get conflated:
- **Stage-2 LM tuning** (DailyDialog/PersonaChat as corpus): both speakers are legitimate LM data — masking is *not* required, and adding HF-style "assistant-only" masking here just throws away half of an already tiny corpus.
- **Personalization/QA teaching:** loss must cover only the **answer** tokens, or the model learns to imitate questions (parrots the user) instead of answering. The classic implementation bug family: off-by-one between the label shift and the mask boundary (the v1.0 loss path shifts targets by one; the mask must be built in *target* space, not input space), masking with the wrong ignore value, or the turn-boundary detector mis-tokenizing so the mask starts mid-word (the known DataCollatorForCompletionOnlyLM failure mode — the template's token sequence doesn't align after tokenization, doubly likely with a 547-id fragmenting tokenizer).

**Why it happens:**
Masking bugs don't crash; they just train a slightly wrong objective whose symptom ("model repeats the user," "model continues the question") looks like a small-model capability problem.

**How to avoid:**
- Golden-fixture test: a hand-built tiny dialogue where the expected label tensor (with ignore positions) is written out by hand; assert the data pipeline reproduces it exactly. One fixture kills the whole bug family.
- Log decoded (token, label) pairs for a few samples at run start — eyeball that loss lands exactly on intended spans.
- Keep the two regimes in two code paths with two names; never one flag.

**Warning signs:** fine-tuned model answers questions with questions; loss is suspiciously low immediately (mask covers almost everything); masked-token fraction per batch isn't logged or is ~0%/~100%.

**Phase to address:** Conversational fine-tuning phase (LM regime) and teach-then-recall phase (QA regime); the fixture test lands with the first data pipeline.

---

### Pitfall 15: Distribution shift collapses TinyStories fluency (and nobody is watching)

**What goes wrong:**
At 13.9M params there is little spare capacity: aggressive stage-2 tuning (full-FT, high LR, many epochs over a small dialogue corpus) overwrites TinyStories fluency fast, and dialogue corpora are small enough (DailyDialog ≈ 13k dialogues; PersonaChat ≈ 11k) that multiple epochs are inevitable — overfitting shows up as repetitive, persona-locked, low-diversity output that *also* scores fine on training loss. If TinyStories PPL is only measured at the end, the forgetting curve has two points and the EWC story has no baseline dynamics.

**Why it happens:**
Forgetting is invisible in the fine-tuning loss being optimized; small-corpus overfitting actively improves the watched metric.

**How to avoid:**
- TinyStories val PPL is evaluated **on the same cadence as fine-tune val loss**, from the first step, via the blessed harness (Pitfall 9). This is also exactly the data the forgetting-curve deliverable needs — one decision serves both.
- Conservative defaults: LR 5–10× below pretrain peak, few epochs, early stop on *dialogue val loss* (proper held-out split — don't train on PersonaChat valid), qualitative sample sheet per checkpoint (story prompt + dialogue prompt side by side).
- Note: mixing TinyStories replay into stage-2 data is legitimate (training-time only — doesn't violate weights-only memory) but **confounds the EWC A/B** (Pitfall 10); if used, it must be present in both arms or neither.

**Warning signs:** dialogue val loss rises while train loss falls (epoch ≥2 on these corpora); story prompts now produce greetings/small talk; output diversity collapses (same reply to varied prompts).

**Phase to address:** Conversational fine-tuning phase; curves consumed by visualization phase.

---

### Pitfall 16: The skeptical reviewer rejects the novel claim on framing, not on results

**What goes wrong:**
Even with correct implementation, the claim "personalization lives in the weights, not in a prompt or a store" has known rebuttals a strong reviewer will reach for:
1. *"The adapter file is just an external store with extra steps."* — A LoRA `.safetensors` per user is a file on disk; if the narrative is sloppy, "weights vs store" reads as semantics.
2. *"Show me the context."* — Without context transparency (Pitfall 11), any chat demo is unverifiable.
3. *"The base model could already do this / the fact is guessable."* — No base-model control, no claim.
4. *"You cherry-picked the transcript."* — Single polished transcript, no seeds, no failure cases.
5. *"EWC didn't do anything; LoRA/low LR did."* — Confounded A/B (Pitfall 10).
6. *"Is the from-scratch claim real?"* — Any LoRA/EWC code that mirrors PEFT internals too closely undermines the portfolio's core differentiator.

**Why it happens:**
The author optimizes for the demo working; the reviewer optimizes for finding the hole. These are different tests.

**How to avoid:**
- Frame precisely: the claim is that personalization is **parametric** — recalled with an empty context through forward passes alone, no retrieval, no lookup, no prompt injection. The adapter is weights (it merges into the model; demonstrate by running the recall demo on the *merged* checkpoint — then there isn't even a second file). Say this in the writeup before the reviewer can.
- Ship the verification kit: clean-room protocol + context-token dump + base/adapter/in-context control triple + all-transcripts directory + seeds + one-command reproduction script. The weight-delta heatmaps support this narrative (visible, localized parameter change between base and taught checkpoints — pair each heatmap with the checkpoint hashes it diffs; for LoRA-only training plot the effective ΔW = scale·B·A per layer, normalized per-layer, since raw base deltas are exactly zero).
- Write the "Limitations" section honestly: recall rate < 100%, paraphrase sensitivity, capacity limits at 13.9M. A demo with documented failure modes reads as science; a flawless demo reads as a trick.

**Warning signs:** the writeup says "no external files" while the demo loads `adapter.safetensors` without addressing it; demo video shows recall in the same session as teaching; only one transcript exists.

**Phase to address:** Both demo phases + the milestone writeup phase; the framing decisions belong in demo-phase planning, not post-hoc.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip the merge path; demo always runs live adapters | Less code now | "Adapter = external store" rebuttal stays alive; no merge-equivalence test means scaling bugs hide | Never for the final demo — merged-checkpoint recall is the strongest form of the claim |
| Batched-gradient "Fisher" (square the mini-batch gradient) | 10× faster Fisher pass | Not actually the Fisher; λ values non-portable; A/B results untrustworthy (documented as the most common EWC bug in the literature) | Never — per-example at 13.9M params is cheap |
| Reuse pretrain optimizer state for fine-tuning | One less code path | Stale moments on wrong params; resume corruption across the param-set boundary | Never |
| `strict=False` checkpoint loading for adapter models | Loads without fuss | Silently un-initialized adapters or silently dropped keys | Never bare; only with an explicit expected-key-set assertion |
| Single transcript for the recall demo | Demo "done" fast | Cherry-picking rebuttal; one probing question from a reviewer sinks it | Never for deliverables; fine for dev iteration |
| Postpone the run.csv ×256 token-count fix | Avoids touching v1.0 logging | Every v2.0 forgetting-curve x-axis inherits a 256× error | Fix before the first fine-tune run (it's a one-liner-class fix) |
| Eyeball "loss went down" instead of the params-update canary | None, really | The MPS silent-freeze class of bug costs days when it hits | Never — the canary is ~10 lines |
| New special tokens via dead ids without the full surgery (mask, slim export, demo, tests) | Quick dialogue formatting | Suppressed embeddings + `forbid_ids` conflicts → demo emits nothing or crashes at exactly the new token | Only with the full lockstep update, as its own tracked task |

## Integration Gotchas

Connections between new v2.0 components and the existing v1.0 system.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| LoRA ↔ six named Linear seams | Class-based module scan picks up lm_head (tied tensor) | Explicit allowlist of the six seam names; tying `data_ptr` test extended to post-wrap |
| EWC ↔ `assemble_loss(..., extra_penalties=())` | Penalty closure uses its own loss reduction, mismatching the training loss scale | Penalty built to the same reduction convention; both terms logged separately each interval |
| Fisher/θ* snapshot ↔ tied weights | `state_dict()` carries the shared tensor under two keys → double-counted penalty | Deduplicate snapshot by `data_ptr()`; one entry per storage |
| Adapter checkpoints ↔ open-dict resume infra | Adapter resumed onto a different/wrong base silently | Adapter checkpoint stores base-weights hash; load asserts match |
| Fine-tuned model ↔ `perplexity()` harness | Mixing masked/unmasked, merged/unmerged, train/eval-mode points in one curve | One blessed entry point; per-point provenance row; step-0 anchor must reproduce base PPL |
| New tokens / dialogue format ↔ `forbid_ids` sampling mask + slim export + Gradio demo | Mask updated in one place, not the others; demo blocks or crashes on new ids | Single source of truth for the live-id set, consumed by sampler, exporter, evaluator, demo |
| Teach-then-recall ↔ `gr.ChatInterface` | Chat history silently re-injects taught facts at recall | Fresh-process recall; context-token dump displayed; single-turn recall mode |
| EOS id 8184 ↔ `generate()` EOS-stop | EOS doubles as turn separator → generation truncates after one turn | Decide separator semantics explicitly; test multi-turn generation end-to-end |
| Kaggle P100 fp16 fallback ↔ fp32 Fisher/EWC artifacts | Fisher computed in fp16 (squared small grads underflow to 0) or curves mixing fp16/fp32 evals | Fisher and all curve evals in fp32; fallback used for training only, if at all |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Dialogue token fragmentation (547 live ids) | Sequences 2–3× longer than expected; context window holds 1–2 turns | Measure tokens/word on real corpus samples before designing the data format | Immediately, at data-prep time — this is the milestone's first empirical question |
| Per-example Fisher pass scaled too ambitiously | Fisher pass takes hours on M3 | A few thousand windows suffices (sample size documented); 13.9M params × N=2–5k is minutes-to-tens-of-minutes | Only if N is pushed toward the full corpus |
| Eval cadence too sparse during fine-tuning | Forgetting curve has 3 points; can't see dynamics | Evaluate TinyStories PPL on the fine-tune val cadence from step 0 | Discovered only at figure-making time, too late |
| Full-val PPL (12.6M tokens) at every fine-tune eval step | Eval dominates wall-clock | Fixed sub-split for curve points + full-val only at milestones; document which is which | When eval interval × full-val cost exceeds training time |
| `torch.autograd.detect_anomaly` left on for MPS debugging | ~100× slowdown | Use finite-checks + the canary instead; anomaly mode only on CPU repro cases | Any long run |

## Claim-Integrity & Privacy Mistakes

(Adapted from the template's security section — the "security" surface of this project is the integrity of its novel claim and the privacy guarantee.)

| Mistake | Risk | Prevention |
|---------|------|------------|
| Recall demo shares a process/session with teaching | Novel claim is false as demonstrated; fatal review finding | Clean-room protocol as an acceptance criterion; context-token dump |
| No base-model control on taught facts | "The model could already say that" | Control triple (base fails closed-book; base succeeds in-context; adapter succeeds closed-book) committed as artifacts |
| Adapter file framed carelessly | "It's just a per-user store" rebuttal | Merged-checkpoint recall demo + parametric-memory framing in the writeup |
| Personal facts in committed artifacts | Real personal data in a public portfolio repo | Use synthetic personas/facts for all committed transcripts; demo with real facts only live |
| Demo loads anything but weights at inference | Privacy-by-design claim weakened | Inference-path audit: the demo process opens model/adapter files only; state it and make it checkable |
| Cherry-picked single transcript | Reproducibility challenge fails | N-seed, held-out-paraphrase success rates; failures committed alongside successes |

## "Looks Done But Isn't" Checklist

- [ ] **LoRA wrapper:** wraps and trains — but is it bit-identical to base at init (B=0), and do merged vs live logits agree ≤1e-5 on CPU? (Pitfalls 2, 3)
- [ ] **Freezing:** `requires_grad=False` set — but does a one-step canary prove base params are bit-unchanged and adapter params changed, *on MPS*? (Pitfalls 4, 5)
- [ ] **Fisher:** computes and saves — but per-example (not batched-gradient), eval mode, task-A data, matching loss reduction, tied tensor counted once, penalty(θ*)=0 exactly? (Pitfalls 6, 7)
- [ ] **EWC arm:** runs with λ>0 — but are penalty and task loss logged separately and within ~2 orders of magnitude? Is the only diff between arms λ? (Pitfalls 8, 10)
- [ ] **Forgetting curve:** plots — but does the step-0 point reproduce base PPL, is the mask/merge/mode policy constant, and is the token axis post-×256-fix? (Pitfall 9)
- [ ] **Dialogue pipeline:** trains — but does the golden-fixture label test pass, and were tokens/word + %-over-block_size measured and recorded? (Pitfalls 13, 14)
- [ ] **Teach-then-recall:** works in dev — but in a fresh process, empty context, held-out paraphrases, with the control triple, and with all transcripts committed? (Pitfalls 11, 12)
- [ ] **Writeup:** claims stated — but does it name the Fisher variant used, the EWC parameter space (base vs effective ΔW), the recall success rate, and limitations? (Pitfalls 6, 7, 16)
- [ ] **Demo provenance:** loads weights — but does the UI display base+adapter hashes so a reviewer can tie the demo to the committed checkpoints? (Pitfall 16)

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Adapter merged into tied tensor (P1) | LOW if caught | Reload from base checkpoint (immutable); add the data_ptr test before retrying. Never "un-merge" in place |
| Non-zero-init adapter trained for days (P2) | MEDIUM | Re-init with B=0 and retrain; prior run's curves unusable as baselines |
| Wrong Fisher variant discovered late (P6) | MEDIUM | Recompute Fisher (fast at this scale); **rerun the λ sweep** (old λ non-portable); rerun EWC arms |
| Forgetting-curve harness drift (P9) | MEDIUM-HIGH | Re-evaluate all retained checkpoints through the blessed harness — recoverable only if checkpoints were kept; therefore: keep per-eval checkpoints during A/B runs |
| Prompt leakage found in demo (P11) | LOW-MEDIUM technically, HIGH if shipped | Rerun recall under the clean-room protocol; if recall then fails, escalate to teaching-set redesign (P12) — this is why clean-room testing must happen in dev, not at the end |
| Dialogue data doesn't fit block_size (P13) | MEDIUM | Truncation/windowing redesign of the data format; worst case, scope persona-context length down and document |
| Fluency collapsed mid-fine-tune (P15) | LOW | Resume from a pre-collapse checkpoint (cadenced evals + kept checkpoints make this cheap), lower LR / raise λ |
| Reviewer-facing claim hole found at writeup time (P16) | HIGH | Usually requires rerunning demos with controls; prevent by treating the verification kit as part of the demo phases, not the writeup |

## Pitfall-to-Phase Mapping

Suggested phase grouping (numbering continues from v1.0, next phase = 9; roadmapper assigns final numbers/order — note the ordering decision flagged below):

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| P1 tied-tensor adaptation | LoRA implementation | data_ptr tying test passes post-wrap; trainable-param census matches 6 × layers × 2 × r |
| P2 non-identity init | LoRA implementation | Bit-identical-logits-at-init test; step-0 PPL anchor |
| P3 α/r scaling | LoRA implementation | Merge-equivalence test ≤1e-5 (CPU) |
| P4 optimizer/checkpoint boundary | LoRA implementation (format) + fine-tuning (resume) | Fresh-optimizer assertion; adapter↔base hash check; mid-fine-tune kill/resume reproduces trajectory |
| P5 MPS silent failures | LoRA implementation; inherited by all training | Params-update canary green on MPS in every run's first step |
| P6 Fisher computed wrong | EWC phase (flag: needs deeper research/verification) | Per-example implementation; analytic tiny-fixture test; penalty(θ*)=0; variant documented in writeup |
| P7 wrong parameter space | EWC phase (regime decided in planning) | Penalty-gradient-nonzero test; effective-ΔW formulation if LoRA-only; tied tensor deduped |
| P8 λ mis-scaling | EWC phase | λ-sweep artifact; per-interval penalty/task-loss ratio logged |
| P9 PPL drift inconsistency | Fine-tuning phase (harness contract) + pre-phase run.csv fix | Step-0 reproduces base PPL; per-point provenance rows; re-run of an old point matches |
| P10 confounded A/B | No-forgetting demo phase (design pre-registered in EWC phase) | Arms differ only in λ; 2×2 result table (new-task + retention, both arms) |
| P11 prompt leakage | Teach-then-recall demo phase | Clean-room protocol with fresh process + context-token dump + control triple |
| P12 verbatim-only recall | Teach-then-recall demo phase (tokenizer pre-flight in fine-tuning phase) | Held-out-paraphrase success rate over seeds; entity token-split audit vs forbid_ids |
| P13 tokenizer vs dialogue | Conversational fine-tuning phase, first deliverable | tokens/word + %-over-block_size measured and gate-checked before pipeline build |
| P14 loss-masking bugs | Conversational fine-tuning + teach-then-recall | Golden-fixture label-tensor test; decoded (token,label) spot-check logged |
| P15 fluency collapse | Conversational fine-tuning phase | TinyStories PPL on fine-tune eval cadence from step 0; per-eval checkpoints kept |
| P16 reviewer rejects framing | Both demo phases + writeup phase | Verification kit shipped (protocol, controls, transcripts, hashes, repro script); limitations section present |

**Ordering note for the roadmapper:** decide early whether stage-2 conversational tuning is full-FT (classic EWC on base params applies; LoRA reserved for personalization) or LoRA-based (requires the effective-ΔW EWC formulation, P7). This decision determines whether the EWC phase depends on the LoRA phase and shapes the A/B design (P10). Either order works; ambiguity doesn't.

## Sources

- van de Ven, *On the Computation of the Fisher Information in Continual Learning* (ICLR 2025 blogpost track) — https://arxiv.org/abs/2502.11756 — batched-gradient Fisher is the most common bug; exact vs empirical vs sampled comparison; λ shifts orders of magnitude between variants (HIGH — read directly)
- HF PEFT tied-weights issues — https://github.com/huggingface/peft/issues/2018, https://github.com/huggingface/peft/issues/2777, https://github.com/huggingface/peft/issues/2864, https://github.com/huggingface/peft/issues/1750, PR #2399 — merging lm_head adapters corrupts tied embeddings; `modules_to_save` silently unties (HIGH — issue tracker)
- Elana Simon, *The bug that taught me more about PyTorch than years of using it* (2025) — https://elanapearl.github.io/blog/2025/the-bug-that-taught-me-pytorch/ — MPS `addcmul_`/`addcdiv_` silently no-op on non-contiguous outputs; weights freeze with healthy gradients; fixed torch ≥2.4; random-op variant until torch 2.10 / macOS 15 (HIGH — detailed post-mortem, read directly)
- PyTorch MPS notes + issues #77754, #134416 — https://docs.pytorch.org/docs/stable/notes/mps.html — silent CPU fallback behavior, op coverage (HIGH)
- *LoRA Learns Less and Forgets Less* — https://arxiv.org/abs/2405.09673 — LoRA's intrinsic forgetting reduction → A/B confound (HIGH)
- rsLoRA — https://huggingface.co/blog/damjan-k/rslora — α/√r vs α/r convention; classic scaling degrades at high rank (MEDIUM)
- *Injecting New Knowledge into Large Language Models via Supervised Fine-Tuning* — https://arxiv.org/abs/2404.00213 — paraphrase augmentation drives QA generalization, saturates ~10 paraphrases/fact (MEDIUM-HIGH)
- Reversal curse + knowledge-injection literature — https://arxiv.org/abs/2411.00686 (Latent Paraphrasing), https://aclanthology.org/2024.emnlp-main.15.pdf (Fine-Tuning or Retrieval) — verbatim-only recall; backward-question failure (MEDIUM-HIGH)
- Loss-masking practice and bugs — https://yonigottesman.github.io/2024/05/13/mask-user-tokens.html, HF TRL SFT docs (DataCollatorForCompletionOnlyLM template-alignment off-by-ones) (MEDIUM)
- PersonaChat/DailyDialog size + overfitting characteristics — https://arxiv.org/html/2406.18187v1 (Selective Prompting Tuning: PersonaChat overfitting → repetitive persona-locked output); DailyDialog ≈13k dialogues (MEDIUM)
- *On Quadratic Penalties in EWC* — https://arxiv.org/abs/1712.03847; EWC empirical evaluation — https://arxiv.org/html/2512.01890 — over-regularization can increase forgetting; λ sensitivity (MEDIUM)
- PersonaCore v1.0 internal context: PROJECT.md tech-debt register (547 live ids, forbid_ids not in evaluate.py, run.csv ×256), seam definitions, MPS-fp32 posture (HIGH — first-party)

---
*Pitfalls research for: PersonaCore v2.0 Weight-Based Memory (LoRA + EWC + conversational fine-tuning + research demos)*
*Researched: 2026-06-11*
