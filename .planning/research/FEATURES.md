# Feature Research

**Domain:** Training-time memorization mitigation (DP-SGD + adversarial/extraction-aware training) and adversarial validation by relearning attack, for a 331,776-param LoRA persona adapter over a frozen 13.9M base
**Researched:** 2026-08-20
**Confidence:** MEDIUM-HIGH overall (HIGH on DP-SGD/canary/relearning conventions — primary sources fetched; MEDIUM on the adversarial-training arm — the exact construction is bespoke and has no direct prior; MEDIUM on cost estimates — arithmetic from this repo's own numbers, not measured)

---

## Part A — Domain Findings (the six questions, answered)

### A1. What DP-SGD actually buys and costs at this scale

**Meaningful vs cosmetic ε (HIGH).** Published NLP DP fine-tuning reports single-digit ε with δ < 1/N. The reference points:

| Source | Setting | ε, δ | Private | Non-private | Gap |
|---|---|---|---|---|---|
| [Yu et al., ICLR 2022](https://arxiv.org/abs/2110.06500) | MNLI, RoBERTa-Large | ε=6.7 | 87.8% | 90.2% | −2.4 pt |
| Yu et al. | MNLI, RoBERTa-Base | ε=6.7 | 83.5% | — | — |
| Yu et al. | DART generation, GPT-2 | ε=6.8, δ=1e-5 | BLEU 38.5–43.8 | 48.1 | −4 to −10 BLEU |

ε ≤ 10 with δ ≤ 1e-5 is the band a reviewer reads as a real claim. ε in the hundreds or above is **cosmetic** — it is not a meaningful bound, and the field knows it. Two consequences for this milestone: report δ explicitly and confirm δ < 1/N (here N ≈ 112 taught training rows, so the conventional δ=1e-5 is comfortably valid), and do not report a three-digit ε as if it were a guarantee.

**Documented utility damage at small scale (HIGH).** The damage is not primarily driven by the parameter count — it is driven by *how many training examples carry the signal you want to keep*. See A6; this is the load-bearing finding of this whole research pass.

**DP on adapter parameters only, frozen base — does it behave differently? YES, and favourably (HIGH).**

- [Yu et al., ICLR 2022](https://openreview.net/forum?id=Q42f0dfjECO) is exactly this configuration: base frozen, DP-SGD applied to LoRA / Adapters / Compacter parameters only. Their finding is that PEFT-under-DP **outperforms full-model DP fine-tuning** on privacy, utility *and* compute simultaneously. This is not a marginal effect; it is the paper's headline.
- Mechanism: DP-SGD's error scales with the ambient dimension *d* (the number of trainable coordinates), because isotropic Gaussian noise is added to every coordinate regardless of whether it carries signal. Fewer trainable coordinates ⇒ less total injected noise energy at the same ε. ([DP-SGD dimension dependence, multiple sources](https://en.wikipedia.org/wiki/Differentially_private_stochastic_gradient_descent); [subspace identification](https://ar5iv.labs.arxiv.org/html/2007.03813))
- The condition under which coordinate restriction helps is now stated precisely: [When Do Fewer Coordinates Suffice in DP-SGD? (arXiv 2606.04375, June 2026)](https://arxiv.org/html/2606.04375v1) — restriction helps when the signal discarded by masking is smaller than the noise energy saved, `‖P_Ā G‖² < (d−k)ν²`. It reports +9.21 / +10.25 / +4.37 pt over dense DP-SGD on CIFAR-10 at ε=1/3/8. It also names when it does *not* help: extremely tight budgets (ε=1) and gradients whose energy is spread evenly.

**So: 331,776 trainable params over a frozen 13.9M base is the *good* DP configuration, not the bad one.** Anyone who assumes "small model ⇒ DP-SGD will be worse" has it backwards. The threat to recall here is dataset shape, not parameter count.

**The scope caveat that must be stated (HIGH).** DP over the adapter's fine-tuning data provides **no guarantee over the frozen base's pretraining data** ([DP-FROST, COLING 2025](https://aclanthology.org/2025.coling-main.465/); [TMI! Finetuned Models Leak Private Information from their Pretraining Data, PoPETs 2024](https://petsymposium.org/popets/2024/popets-2024-0075.pdf)). For PersonaCore this is benign — the persona facts exist only in the adapter's training data, and Phase 14's `FACTSET_GATE_SHA` already proves every locked fact base-fails — but the sentence has to appear in the report or a reviewer will assume it was overlooked.

**Cost (MEDIUM — arithmetic, not measured).** The milestone's "~B× naive accumulation" worry is a large-model concern that mostly evaporates here:

- Naive route (microbatch to batch-1) = B× forward+backward = 8× at `BATCH_SIZE = 8`. Real, and the milestone is right to measure it.
- Hook route: LoRA's A and B are pure `nn.Linear`, so per-example gradients come from one einsum over the saved input activation and `grad_output` (`einsum('bto,bti->boi', g, a)`), no extra backward. Cost ≈ 1.2×.
- Memory for materialized per-example grads at this scale: 8 × 331,776 × 4 B = **10.6 MB**. Trivial.
- [Ghost clipping (Li et al., ICLR 2022)](https://arxiv.org/pdf/2110.05679) — per-example norms from activations and backprops without instantiating the gradient — exists and is the right citation, but at 10.6 MB it solves a problem this project does not have. Cite it as the technique you *evaluated and did not need*; that reads better than using it unnecessarily.

Keep the cost calibration feature (it is pre-registration hygiene and it sets Z), but expect the answer to be "hooks, ~1.2×", not "8×".

### A2. Standard extraction and utility metrics

**Privacy / memorization axis — three conventions, only one of which fits here.**

1. **Extraction rate / (k,ℓ)-extractability — USE THIS AS X.** A target is memorized if the model reproduces it under a prompt. [Carlini et al., ICLR 2023 "Quantifying Memorization"](https://arxiv.org/pdf/2202.07646) formalizes *discoverable* memorization (prompted with the true training prefix); [Nasr et al. 2023] and follow-ups formalize *extractable* memorization (elicited from **any** prompt). PersonaCore's Phase 18 number — 92/104 = 88.5% under prompt-only attack — is an extraction rate under the *extractable* definition, which is the stronger and more adversarially honest of the two. It is already the project's native unit. Keep it.
2. **Canary exposure — USE AS A SECOND, DESCRIPTIVE READOUT ONLY.** [Carlini et al., USENIX Security 2019 "The Secret Sharer"](https://www.usenix.org/system/files/sec19-carlini.pdf): `exposure(s) = log₂|R| − log₂ rank(s)`, where `rank` is the canary's position by perplexity among a reference set R of same-format candidates. Already implemented in this repo (`exposure_rank` / `measure_exposure` in `scripts/phase18_extraction.py`). Two reasons it cannot be the gate axis: [A Note On Interpreting Canary Exposure (arXiv 2306.00133)](https://arxiv.org/pdf/2306.00133) shows exposure does not convert into an attack success rate or an ε; and v3.0 already *measured* the rank instrument reading rank-1-at-ceiling on seven facts whose generation had collapsed. Report it per point, gate on nothing.
3. **Membership inference — DO NOT USE.** Convention is TPR at low FPR (e.g. 0.1%), not accuracy ([LiRA, Carlini et al., S&P 2022]). But [Duan et al., "Do Membership Inference Attacks Work on Large Language Models?" (arXiv 2402.07841)](https://arxiv.org/abs/2402.07841) found *no* MIA exceeded AUC 0.6 on LLMs outside one domain, and that apparent successes trace to distribution shift. At 8 facts / 112 rows there is no statistical power for an MIA at any FPR worth quoting. Listed below as an anti-feature.

**Utility axis.** DP and unlearning papers both report the *task* metric plus a *collateral* metric, and both anchor the plot with a non-private ceiling and a floor:

- Task metric here = taught-template recall rate and held-out-phrasing recall rate on the inherited fixture. Already the v2.0 gate metrics; already has a scorer.
- Collateral metric here = masked dialogue val PPL (`masked_perplexity()`, Phase 12, 4.5733 on the current adapter) and/or retention PPL. This is the metric that catches the Phase 19 failure mode — "the mechanism worked by destroying the model."
- [MUSE](https://arxiv.org/abs/2407.06460) deliberately reports VerbMem, KnowMem, PrivLeak and Utility as **four separate numbers with no aggregate score**. Follow that. Do not compute a composite "privacy score."

**What a credible privacy/utility frontier figure looks like.**

- Axes: **X = measured extraction rate (0–1), Y = measured recall rate (0–1)**. Both measured on the same fixture with the same scorer at the same draw budget. Not ε on X.
  - The DP literature's convention (ε on X, utility on Y — [Pareto-front presentation](https://www.researchgate.net/publication/333418330_Automatic_Discovery_of_Privacy-Utility_Pareto_Fronts)) is *wrong for this milestone*, because the two arms' sweep parameters (ε, attack intensity) are not commensurable and cannot share an axis. Put the sweep parameter in the point label / colorbar, not on an axis. This is what lets both arms live on one plot.
- Two anchor points, both measured this milestone, not inherited: the **retrained unmitigated control** (upper right: high recall, high extraction) and the **never-taught adapter** (lower left: recall at floor, extraction 0/104). Without both anchors a "low extraction" point is uninterpretable.
- The **gate rectangle** (extraction ≤ X, recall ≥ Y) drawn on the axes from the committed constants, so PASS/FAIL is a visual fact, not a sentence.
- Clopper-Pearson binomial CIs on every point at a stated *n*, with *n* equal across compared points. v3.0 used a one-sided 95% lower bound for a leakage claim; a frontier needs two-sided intervals in both directions.
- Every point annotated with its collateral utility (dialogue PPL), so a point that bought privacy by breaking the model is visible on the figure rather than buried in a table.

### A3. Adversarial / extraction-aware training as a defense

**Is it an established technique with a name? Partly — the frame is established, this specific construction is bespoke. Say so.**

Established named relatives:

| Technique | Reference | What it is |
|---|---|---|
| Adversarial training (min-max) | Madry et al., ICLR 2018 | The general frame: train on the attacker's worst case. |
| **Adversarial regularization for membership privacy** | [Nasr, Shokri, Houmansadr, CCS 2018 (arXiv 1807.05852)](https://arxiv.org/pdf/1807.05852) | **Closest named prior.** Min-max: jointly train the model and an inference-attack classifier. Reports MIA driven to near-chance at ~3% accuracy cost on CIFAR100/Purchase100. |
| R2D2 / LAT / circuit breakers | HarmBench (Mazeika et al. 2024); latent adversarial training; representation rerouting | LLM-side adversarial training against prompt attacks. |
| Goldfish loss | [Hans et al., NeurIPS 2024 (arXiv 2406.10209)](https://arxiv.org/abs/2406.10209) | Non-DP training-time memorization mitigation: randomly drop tokens from the loss. Worth naming as the alternative you did not take. |

"Train the LoRA adapter against the Phase 18 attack suite with attack intensity as the sweep axis" has **no established name**. The honest label is *attack-aware / adversarially-regularized fine-tuning*, constructed for this project. Do not imply a literature it does not have.

**What is already known about generalization to unseen attacks: it is poor, reliably, and this is one of the field's best-replicated negative results (HIGH).**

- [Tramèr, Carlini, Brendel, Madry, NeurIPS 2020 "On Adaptive Attacks to Adversarial Example Defenses"](https://arxiv.org/pdf/2002.08347): **thirteen** defenses published at ICLR/ICML/NeurIPS were circumvented — all of which had reported adaptive evaluations. The failure mode is not laziness; it is that evaluating against the attacks you thought of is structurally insufficient.
- [Song & Mittal, USENIX Security 2021](https://www.usenix.org/system/files/sec21-song.pdf): MIA defenses (including adversarial regularization) look far better than they are when evaluated only against the attack family they were trained on; simpler metric-based attacks recover much of the leakage, and plain early stopping matched the defenses.
- LLM side, current: "existing alignment and adversarial training approaches often struggle to generalize to unseen attacks, as they are fundamentally limited by the distributions of prompts and behaviors present in their training data" — [Adversarial Déjà Vu, ICLR 2026 (arXiv 2510.21910)](https://arxiv.org/html/2510.21910).

**Actionable consequence:** declaring generalization an "open question" is correct, but the prior is *negative*, and the milestone can convert the question into a measurement almost for free. The Phase 18 suite already has four separable families (`A1-mild`, `A1-aggressive`, `A2`, `A3`) plus the `A0` positive control. **Hold one family out of adversarial training entirely and evaluate on it.** Leave-one-family-out with a matched draw budget is the minimum credible version; without it, the adversarial arm's frontier is a training-set number and a reviewer who has read Tramèr et al. will discount it entirely.

### A4. Relearning attacks — formulation and protocol

Two published formulations, and they map exactly onto the milestone's two instruments.

**(a) Absolute recovery ceiling → the binary gate. Shape from [Hu et al., "Jogging the Memory of Unlearned LLMs", ICLR 2025 (arXiv 2406.13356)](https://arxiv.org/abs/2406.13356) (HIGH — protocol fetched from the paper).**

| Protocol element | What the paper does |
|---|---|
| Attacker data access | Two scenarios: (i) a small subset of the forget set; (ii) benign public data loosely related to it. Hard constraint: *"the relearning data does not provide direct information about the evaluation queries used for testing."* |
| Budget | LoRA fine-tuning; TOFU/Phi-1.5: lr=2e-4, batch size 8, weight decay 0.01; relearning budgets of **15 / 30 / 48 / 60 steps** evaluated. |
| "Recovered" | Keyword containment, ROUGE-L against the reference answer, and LLM-as-judge 1–10. No numeric success threshold is fixed by the paper — it is chosen per benchmark. |
| Baselines | Three models: original (pre-mitigation), mitigated, relearned. Example: WMDP gradient-ascent forget score **1.27 → 6.2** after relearning. |
| Never-exposed control | Present and explicit: *"The model finetuned with D′ only achieves 0% attack success rate on all authors"* — a model that never saw the material, given the same relearning data, recovers nothing. |

**(b) Cost-to-recovery / information-still-present probe → the descriptive instrument. Shape from [Deeb & Roger, "Do Unlearning Methods Remove Information from Language Model Weights?" (arXiv 2410.08827)](https://arxiv.org/abs/2410.08827) (HIGH).** Give the attacker facts **T** that were supposed to be removed, fine-tune on T only, and measure recovery on a **disjoint** set **V** that cannot be guessed from T. Retraining on T recovers **88% of pre-unlearning accuracy** on current unlearning methods. The design's virtue: recovery on V cannot be explained away as "you just retaught it," because V was never in the relearning data.

**The distinction the milestone must pre-register, stated concretely:**

| | (a) Absolute recovery ceiling | (b) Cost-to-recovery curve |
|---|---|---|
| Role | **Binary pre-registered gate** | **Descriptive instrument**, qualifies the verdict |
| Question | "After a fixed budget Z, is recovered extraction/recall ≤ X?" | "How expensive is recovery, relative to teaching it from scratch?" |
| Output | One number, one comparison against a committed constant | Three curves over relearning steps: mitigated / unmitigated-control / never-taught |
| Budget | **Fixed Z**, committed in code (steps, lr, batch, optimizer, seed, relearning-set composition). Z is a *resource* parameter → may be set from measurement. X is an *outcome* threshold → must be locked first. | Swept: measure at every checkpoint over 0…Z steps, all three arms at the same checkpoints and the same seed. |
| Reading | PASS = the mitigation survives a bounded adversary. FAIL = it does not. | mitigated ≈ never-taught ⇒ **information removed**. mitigated recovers materially faster/cheaper than never-taught ⇒ **suppressed, not removed**. |
| Failure to guard against | Z chosen too small manufactures a PASS. Publish Z with the verdict, always. | An *undertrained* mitigated arm also looks like never-taught, for a trivial reason. The unmitigated control's curve is the third line that gives "fast" a scale. |

**Two protocol requirements that come straight from the papers and are easy to get wrong:**

1. **T/V split.** The relearning set must be disjoint from the evaluation questions. This repo already has the split, built for another purpose: `TAUGHT_FAMILY_IDS = {F1, F2, F4, F5, F6}` vs `HELDOUT_FAMILY_IDS = {F3, F7, F8}` in `scripts/phase14_factset.py`, plus `RESERVED_HELDOUT_PROBES` which is *permanently banned from every teaching set*. Relearn on a subset of taught families, evaluate on held-out families and reserved probes → that is Deeb & Roger's T/V design at zero construction cost.
2. **"Never-taught" must mean the right thing.** Not "adapter off" — that control already exists and sits at exactly 0/104. It means a **fresh adapter trained on the same dialogue replay with the persona rows removed**, at identical budget and seed protocol, then subjected to identical relearning. Otherwise the never-taught curve starts from a different model class and the comparison is void.

### A5. Table stakes vs differentiators vs anti-features

See Part B. That is the deliverable.

### A6. Expected outcome, stated directly: will DP-SGD at 331,776 params destroy recall?

**Direct answer: it depends on exactly one number — how many training examples carry each fact — and for PersonaCore's *current* data shape the answer is NO, recall will probably survive, and that is the uncomfortable result, not the comfortable one.**

**The single-example case (HIGH — primary source).** [Secret Sharer, Table 3](https://www.usenix.org/system/files/sec19-carlini.pdf), canary inserted **once**, Penn Treebank, 100 epochs:

| ε | Test loss | Exposure | Extraction possible |
|---|---|---|---|
| 0.65 | 1.69 | 1.1 | No |
| 1.21 | 1.59 | 2.3 | No |
| 5.26 | 1.41 | 1.8 | No |
| 89 | 1.34 | 2.1 | No |
| 2×10⁸ | 1.32 | 3.2 | No |
| 1×10⁹ | 1.26 | 2.8 | No |
| No DP (RMSProp) | 1.17 | **31.0** | **Yes** |

The paper's own reading: *"even with a vanishingly-small amount of noise, and values of ε that offer no meaningful theoretical guarantees, the measured exposure is negligible."* **Per-example clipping alone destroys single-example memorization at every ε they tested, including ε = 10⁹, i.e. no guarantee at all.** If each persona fact appeared in exactly one training row, DP-SGD would drive recall to the never-taught floor and there would be no frontier to plot. That is not a bug — it is the guarantee working.

**PersonaCore does not have that shape.** From this repo: 8 core slots (`CORE_SLOTS` in `phase18_extraction.py`), taught through 5 template families (`TAUGHT_FAMILY_IDS`), producing 112 taught rows in the Phase 18 corpus → **≈ 14 training examples per fact.** DP-SGD's per-example clipping does not prevent learning a signal carried by 14 examples; learning signals carried by many examples is exactly how DP-SGD learns anything.

**So the realistic expectation, and the trap:**

- Recall likely **survives** at moderate σ. The DP arm probably produces real frontier points.
- But the (ε, δ) it can honestly report is **example-level**. At the fact level the group has size k ≈ 14, and group privacy degrades the guarantee multiplicatively in k ([standard result, Dwork & Roth](https://www.cis.upenn.edu/~aaroth/Papers/privacybook.pdf); for approximate DP, (ε,δ) ⇒ (kε, k·e^{(k−1)ε}·δ) for groups of size k). At ε_example = 8, **ε_fact ≈ 112** — cosmetic by A1's own standard.
- Therefore the likely headline is: *"recall survives, extraction drops somewhat, and the formal guarantee that survives is at a granularity that does not protect the fact."* That is a genuine, publishable negative and it is the direct continuation of v3.0's honesty posture.

**Design the frontier to capture it rather than be embarrassed by it — four concrete requirements:**

1. **Sweep σ down to ≈0** so one endpoint reproduces the retrained unmitigated arm. If the curve does not connect to the control, the harness is wrong. This is a free correctness check.
2. **Sweep σ up until recall hits the never-taught floor**, so the collapse end is *on the plot*. A frontier truncated before collapse cannot distinguish "no collapse exists" from "budget ran out" — which is exactly why Z is a measured resource parameter.
3. **Report ε_example and ε_fact side by side, with k measured** as an actual count of training rows per fact (not asserted). Never publish ε alone.
4. **Run one dedup reference point** — each fact in exactly one training row, DP as intended. It should land at the never-taught floor and reproduce the Secret Sharer result on this project's own model. One extra training run; it makes the entire group-privacy story legible in a single figure and pre-empts "did you just not add enough noise?"

---

## Part B — Feature Landscape

Dependency legend: **[INHERIT]** = uses v2.0/v3.0 apparatus as-is · **[EXTEND]** = inherited code needs a seam or parameter · **[NEW]** = new construction.

### Table Stakes (minimum credible version at a strong-CS-program bar)

| Feature | Why Expected | Complexity | Dependency & notes |
|---|---|---|---|
| From-scratch DP-SGD on LoRA gradients (per-example clip + Gaussian noise) | It is the milestone's only formally-guaranteed arm and the from-scratch deliverable | MEDIUM | **[EXTEND]** v2.0 `train()` grad path. Per-example grads via forward/backward hooks on the LoRA `nn.Linear` modules (`einsum('bto,bti->boi', grad_out, act)`) — no extra backward, ~1.2×. 8 × 331,776 × 4 B = 10.6 MB, so materialize; ghost clipping is unnecessary here (cite, don't implement) |
| From-scratch (ε, δ) accountant | An ε without an accountant is a number, not a claim | MEDIUM-HIGH | **[NEW]** RDP of the Sampled Gaussian Mechanism (Mironov et al. 2019) over integer α orders + RDP→(ε,δ) conversion. ~100 lines of log-space numerics. Zero-dependency oracle for tests: closed form at q=1 (`α·Δ²/(2σ²)`) plus hard-coded values from a published table — same test-oracle pattern as tiktoken |
| **Poisson-sampling data loader for the DP arm** | The accountant assumes it; without it the reported ε is invalid | LOW-MEDIUM | **[EXTEND]** the memmap loader. See anti-feature #1 — this is a correctness requirement, not a nicety |
| Measured DP-SGD wall-clock on M3 before Z is pre-registered | Already in the milestone scope; sets Z honestly | LOW | **[NEW]** thin script. Expect ~1.2× (hooks) vs 8× (naive microbatch); measure both so the choice is evidenced |
| Retrained unmitigated control at identical budget/seed | v2.0's 0.4921/0.3483 belong to a different run; without this the frontier has no valid upper-right anchor | LOW | **[INHERIT]** `scripts/teach_persona.py::train_arm` verbatim, new seed protocol |
| Never-taught fresh adapter arm | The frontier's lower-left anchor **and** the relearning cost curve's reference | LOW | **[EXTEND]** same trainer, persona rows removed, dialogue replay kept. *Not* the adapter-off control (that already exists at 0/104 and is a different object) |
| Adversarial extraction-aware training, intensity swept | The second arm; bounds the empirical question DP cannot | MEDIUM | **[INHERIT]** `apply_a1` / `build_a2_prompt` / `build_a3_prompt` and their `dose` / `intensity` parameters already exist in `phase18_extraction.py` |
| Extraction rate as the privacy axis, same fixture + same scorer + matched draw budget per compared pair | The only axis with power at n=8 facts; matched budget is the control that makes a comparison a comparison | LOW-MEDIUM (expensive in wall clock) | **[INHERIT]** 270-question fixture, cell-blind scorer, `licensed_conclusion`. Budget matching is required *per compared pair*, not per point — sweep at a reduced equal budget, re-measure gate-relevant points and both anchors at the full 42,480 |
| Collateral utility per sweep point (masked dialogue val PPL) | Phase 19's failure mode was "it worked by destroying the model"; without this the same thing recurs invisibly | LOW | **[INHERIT]** `masked_perplexity()` from Phase 12 |
| Pre-registered existence gate: ∃ point with extraction ≤ X **and** recall ≥ Y, X/Y committed before any point exists | The project's whole methodological spine | LOW | **[INHERIT]** the `scripts/erasure_gate.py` pattern — module-level literal, imported not retyped, pushed before the run |
| Relearning attack, absolute recovery ceiling, fixed budget Z | Without it "the mitigation holds" is untested | MEDIUM | **[NEW]** driver; **[INHERIT]** fixture, scorer, trainer. Publish Z alongside the verdict, always |
| ε reported with sampling assumption **and** granularity (ε_example + ε_fact with measured k) | See A6; a bare ε here would be misleading | LOW | **[NEW]** ~20 lines + a measured row-count-per-fact |
| Every point's binomial CI at a stated n | Frontier points without intervals are decoration | LOW | **[INHERIT]** v3.0 precedent; widen from one-sided lower bound to two-sided |

### Differentiators (what reads as genuinely novel)

| Feature | Value Proposition | Complexity | Dependency & notes |
|---|---|---|---|
| **Leave-one-attack-family-out for the adversarial arm** | Converts "generalization is an open question" from a disclaimer into a measurement. Given Tramèr et al. 2020, a reviewer will otherwise discount the arm entirely | MEDIUM | **[INHERIT]** the four families already exist and are separable. Train on three, evaluate on the fourth, matched draw budget. Pre-register which family is held out |
| **Cost-to-recovery curve with a never-taught reference** | This is the "removed vs suppressed" test, and PersonaCore can run it *cleanly* in a way 7B unlearning papers cannot — the adapter is the only place the fact lives, so "never taught" is exactly constructible and cheap (~38 min/arm) | MEDIUM | **[NEW]** curve driver; **[INHERIT]** trainer + scorer. Three curves at the same checkpoints and seed: mitigated / unmitigated / never-taught |
| **RTT-style T/V split reusing the existing family allocation** | Deeb & Roger's design (relearn on T, evaluate on disjoint V) at near-zero construction cost — `TAUGHT_FAMILY_IDS` / `HELDOUT_FAMILY_IDS` / `RESERVED_HELDOUT_PROBES` already exist and were built before this milestone, which is itself a provenance point | LOW | **[INHERIT]** `scripts/phase14_factset.py`. Recovery on V cannot be explained as "you retaught it" |
| **Two mechanisms on one measured-privacy × measured-utility plane with the gate rectangle drawn** | DP papers plot ε vs utility; unlearning papers plot forget-quality vs model-utility. Putting a formally-guaranteed and a heuristic mechanism on the *same measured* axes, with the pre-registered gate drawn on the figure, is uncommon and immediately readable | MEDIUM | **[NEW]** plotting; **[INHERIT]** the Phase 15 discipline — extract once to a committed JSON, plot only from that, plotting module structurally forbidden from opening a checkpoint |
| **The dedup reference point (1 row/fact, DP as intended)** | One training run that reproduces the Secret Sharer result on this project's own model, makes the group-privacy story legible, and pre-empts "you just didn't add enough noise" | LOW | **[EXTEND]** `render_episodes` with a single family |
| **ε_fact published alongside ε_example** | Most applied DP write-ups quietly report example-level ε for correlated data. Publishing the group-privacy-adjusted number unprompted is the kind of honesty that distinguishes a portfolio at this bar | LOW | **[NEW]** |
| **Two disagreeing instruments carried forward per point** (generation-scored extraction *and* exposure rank) | v3.0 measured these instruments disagreeing on the same weights. Carrying both forward turns a v3.0 co-headline into a standing methodological control | LOW | **[INHERIT]** `measure_exposure` already computes it |

### Anti-Features (impressive-looking, known to be misleading)

| Feature | Surface Appeal | Why Problematic | Do Instead |
|---|---|---|---|
| **1. Reporting ε while sampling with the existing memmap loader** | "We report (ε, δ)" | The accountant assumes **Poisson subsampling**. [Chua et al., NeurIPS 2024 (arXiv 2411.04205)](https://arxiv.org/abs/2411.04205) show shuffling-based DP-SGD reported with Poisson accounting *substantially understates* the true privacy loss, and call the common practice into serious question. This repo samples contiguous windows from a memmap — a live defect, not a hypothetical | Implement Poisson sampling for the DP arm, and state the assumption next to every ε |
| **2. Reporting ε without stating granularity** | A single clean number | Example-level ε over data where one fact spans ~14 rows says almost nothing about the fact. Group privacy multiplies (ε ⇒ kε, δ ⇒ k·e^{(k−1)ε}δ) | Report ε_example **and** ε_fact with k measured, every time |
| **3. Claiming the adversarial defense works, evaluated on the attacks it trained against** | A dramatic drop in extraction | Tramèr et al. 2020 broke 13 published defenses that all reported adaptive evaluations; Song & Mittal 2021 showed MIA defenses collapse under attacks they were not trained on | Leave-one-family-out, plus at least one adaptive attempt against the trained defense |
| **4. Comparing arms at unequal draw budgets** | Fewer draws on the defended arm looks cheap and harmless | Extraction rate is monotone in draws. A defended arm measured at fewer draws gets its win for free | Matched budget per compared pair; v3.0's 42,480 as the precedent for headline points |
| **5. MIA / membership advantage as the privacy axis** | Reviewers recognise MIA | Duan et al. 2024: no MIA exceeded AUC 0.6 on LLMs outside one domain; at 8 facts there is no power at any usable FPR. A near-chance MIA "proving" privacy is the weakest possible evidence | Extraction rate as the gate axis; exposure as a descriptive second reading |
| **6. Output filtering / refusing the leaked string** | Extraction rate drops to ~0 immediately | [Ippolito et al., INLG 2023](https://arxiv.org/abs/2210.17546) built a *perfect* verbatim filter and showed it does not prevent leakage — trivially circumvented by minimally-modified style-transfer prompts. It is also not a weight-level mitigation, which is this project's entire claim | Training-time mitigation only; the filter idea belongs in the report as an explicitly rejected option |
| **7. Exposure/rank as the sole privacy readout** | It is a real, cited metric and it is already implemented | [arXiv 2306.00133](https://arxiv.org/pdf/2306.00133): exposure does not convert to attack success or ε. v3.0 *measured* rank-1-at-ceiling on seven facts whose generation had collapsed | Both instruments per point; gate on the generation-scored rate only |
| **8. Reusing v2.0's 0.4921 / 0.3483 as the baseline** | Saves ~38 min of compute | Different training run; the comparison would be confounded with run-to-run variance. Already flagged in PROJECT.md — keep it named so it cannot creep back in under schedule pressure | Retrained unmitigated control at identical budget and seed |
| **9. A privacy "win" reported without its collateral utility** | The frontier looks great | This is Phase 19's exact failure mode. An arm that never learned has perfect privacy | Dialogue PPL annotated on every frontier point |
| **10. ε→0 points that are really "adapter never left B=0"** | A legitimate-looking extreme end of the sweep | If σ is large enough that the adapter stays at initialization, the arm is the base model wearing a label | Detect with the existing bit-identity control (adapter-on logits vs base logits, max abs diff) and mark such points as degenerate on the figure |
| **11. Relearning data that contains the evaluation answers** | Makes the relearning attack "work" | Every arm recovers and the gate becomes uninformative. Hu et al. constrain this explicitly | T/V split via the existing taught/held-out family allocation + `RESERVED_HELDOUT_PROBES` |
| **12. A single composite "privacy score"** | One number to rank the arms | MUSE deliberately reports four metrics with no aggregate, because aggregation lets one metric's collapse hide inside another's win | Report extraction, recall, exposure and dialogue PPL separately |
| **13. Declaring a relearning PASS without publishing Z** | A clean binary verdict | A small enough Z manufactures a PASS. The verdict is only meaningful relative to the budget | Z committed in code, printed in the report next to the verdict, and justified from the cost measurement |

---

## Feature Dependencies

```
Poisson-sampling loader
    └──required-by──> (ε,δ) accountant ──required-by──> DP-SGD arm
                                                             │
DP cost calibration (M3) ──sets Z──────────────────────────> │
                                                             ▼
Retrained unmitigated control ──anchors──> Privacy/utility frontier <── Adversarial arm
Never-taught fresh adapter ────anchors──>        │                          │
                                                 │                    (needs) leave-one-
Pre-registered gate (X, Y committed) ──judges──> │                     family-out split
                                                 ▼
                                          Existence verdict
                                                 │
                                                 ▼
                     Relearning attack (a) absolute ceiling @ fixed Z  ──> BINARY GATE
                                                 │
                     Relearning attack (b) cost-to-recovery curve      ──> QUALIFIES verdict
                                     needs all three: mitigated / unmitigated / never-taught

Dedup reference point (1 row/fact) ──explains──> DP arm's ε_fact story
Two-instrument readout (extraction + exposure) ──qualifies──> every frontier point
```

### Dependency Notes

- **Accountant requires Poisson loader.** Not stylistic. Reporting ε computed under Poisson accounting while sampling by shuffling is the exact practice Chua et al. call into question. This ordering must hold in the roadmap.
- **Frontier requires *both* anchors before any sweep point is interpretable.** A point at extraction 0.30 means nothing until you know the unmitigated arm sits at 0.885 and the never-taught arm at 0.0. Schedule both control arms before the sweep.
- **Relearning cost curve requires the never-taught arm**, which is also a frontier anchor. One training run serves both — schedule it early.
- **Adversarial arm requires the held-out-family decision to be pre-registered before training**, not after. Choosing which family to hold out after seeing which one the defense handles worst is exactly the peek the project's discipline forbids.
- **Z depends on the cost measurement; X and Y do not depend on anything.** X/Y commit first, in the same commit-before-the-run pattern as `erasure_gate.py`. Z lands after the calibration. The PROJECT.md pre-registration boundary already states this — the roadmap must physically order the commits that way.
- **Dedup reference point conflicts with nothing but must not be swept.** It is one point, run once, at a σ chosen to match a swept point. It is an explanation, not a curve.

---

## MVP Definition

### Launch With (the minimum credible milestone)

- [ ] DP-SGD from scratch on LoRA grads + Poisson loader + (ε, δ) accountant — the only formally-guaranteed arm
- [ ] DP cost measured on M3 before Z is committed — pre-registration boundary
- [ ] Retrained unmitigated control — the frontier has no upper-right anchor without it
- [ ] Never-taught fresh adapter — the frontier's lower-left anchor *and* the relearning reference
- [ ] Adversarial extraction-aware training with intensity swept
- [ ] Frontier on measured-privacy × measured-utility axes, both arms, gate rectangle drawn, collateral PPL per point
- [ ] Pre-registered existence gate, X/Y committed before any point exists
- [ ] Relearning attack (a): absolute recovery ceiling at fixed published Z
- [ ] ε_example + ε_fact with k measured

### Add Once the Core Frontier Exists

- [ ] Relearning attack (b): cost-to-recovery curve, three arms — trigger: the existence gate has a verdict, so the curve has something to qualify
- [ ] Leave-one-attack-family-out evaluation — trigger: the adversarial arm produces any point that clears the gate; without a clearing point there is no generalization claim to test
- [ ] Dedup reference point — trigger: the DP arm's ε_fact turns out to be three digits, i.e. the expected case

### Future Consideration (defer)

- [ ] Adaptive attack designed *against* the trained defense (Tramèr et al. methodology) — defer: it is a research project of its own, and leave-one-family-out already carries the honest scope limit
- [ ] Goldfish loss as a third arm — defer: two arms already exhaust the M3 budget; name it in the report as the alternative not taken
- [ ] Selective DP ([Shi et al., NAACL/EMNLP 2022](https://aclanthology.org/2022.emnlp-main.425/) — protect only policy-designated sensitive tokens) — defer: closest published construction to "learn the persona, hide the secret," and the natural v5.0 lead, but it changes the DP notion mid-milestone
- [ ] Erasure at higher adapter rank; frozen-tokenizer retrain — already deferred in PROJECT.md; unchanged by this research

---

## Feature Prioritization Matrix

| Feature | Portfolio Value | Implementation Cost | Priority |
|---|---|---|---|
| DP-SGD from scratch + accountant | HIGH | MEDIUM-HIGH | P1 |
| Poisson-sampling loader | MEDIUM (invisible if right, fatal if wrong) | LOW-MEDIUM | P1 |
| Retrained unmitigated control | HIGH (nothing is interpretable without it) | LOW | P1 |
| Never-taught fresh adapter | HIGH (serves two features) | LOW | P1 |
| Adversarial arm with intensity sweep | HIGH | MEDIUM | P1 |
| Frontier figure + committed existence gate | HIGH | MEDIUM | P1 |
| Relearning (a) absolute ceiling | HIGH | MEDIUM | P1 |
| ε_example + ε_fact with measured k | MEDIUM-HIGH | LOW | P1 |
| Collateral PPL per point | MEDIUM (prevents the Phase 19 repeat) | LOW | P1 |
| Relearning (b) cost curve, 3 arms | HIGH (the "removed vs suppressed" answer) | MEDIUM | P2 |
| Leave-one-attack-family-out | HIGH (or the adversarial arm gets discounted) | MEDIUM | P2 |
| Dedup reference point | MEDIUM | LOW | P2 |
| Two-instrument readout per point | MEDIUM | LOW | P2 |
| Adaptive attack against the trained defense | HIGH | HIGH | P3 |
| Goldfish-loss third arm | LOW-MEDIUM | MEDIUM | P3 |

---

## Prior-Art Comparison

| Concern | Published practice | Our approach | Why it differs |
|---|---|---|---|
| DP on PEFT params | Yu et al. ICLR 2022 — frozen base, DP on LoRA/Adapters, ε≈6.7, −2.4 pt accuracy | Same configuration, from scratch, at 331,776 params on a 13.9M base | Same config; ~40× smaller; goal *inverted* — they preserve task accuracy while hiding examples, we must preserve **memorization of specific facts** while hiding them from extraction |
| Memorization metric | Canary exposure (Carlini 2019); extraction rate / (k,ℓ)-extractability (Carlini 2023) | Extraction rate gates; exposure descriptive | Both already implemented; v3.0 measured them disagreeing, so we carry both rather than choose |
| Defense evaluation | Adversarial regularization (Nasr 2018), evaluated in-family — then broken by Song & Mittal 2021 | Leave-one-attack-family-out, matched draw budget | The documented failure mode is in-family evaluation; we pre-commit the held-out family |
| Relearning attack | Hu et al. ICLR 2025 — LoRA relearn, lr 2e-4, 15–60 steps, 3-model comparison | Same shape, fixed committed Z, ceiling as binary gate | Ours pre-registers the threshold and publishes Z with the verdict |
| Information-removal probe | Deeb & Roger 2024 — retrain on T, evaluate on disjoint V; 88% recovery | Same, reusing the taught/held-out family split built in Phase 14 | The T/V split predates this milestone in git — provenance, not construction |
| Unlearning reporting | MUSE — four metrics, no aggregate; TOFU — forget quality × model utility | Extraction, recall, exposure, dialogue PPL reported separately | Follows MUSE deliberately; refuses a composite score |
| Frontier axes | DP: ε vs utility. Unlearning: forget-quality vs model-utility | Measured extraction vs measured recall, sweep parameter in the label | Two non-commensurable sweep parameters cannot share an axis; only measured axes let both arms be plotted together |

---

## Sources

**HIGH confidence — primary sources fetched and quoted:**
- [Carlini et al., The Secret Sharer, USENIX Security 2019](https://www.usenix.org/system/files/sec19-carlini.pdf) — exposure formula, DP Table 3 (ε 0.65 → 10⁹, exposure 1.1–3.2 vs 31.0 baseline), single-insertion canary
- [Yu et al., Differentially Private Fine-tuning of Language Models, ICLR 2022 (arXiv 2110.06500)](https://arxiv.org/abs/2110.06500) / [OpenReview](https://openreview.net/forum?id=Q42f0dfjECO) — ε=6.7 MNLI 87.8% vs 90.2%; ε=6.8/δ=1e-5 DART BLEU 38.5–43.8 vs 48.1; PEFT-under-DP beats full-model DP
- [Hu et al., Jogging the Memory of Unlearned LLMs, ICLR 2025 (arXiv 2406.13356)](https://arxiv.org/abs/2406.13356) — relearning protocol: LoRA lr 2e-4 / batch 8 / wd 0.01, 15–60 steps; ROUGE-L + keyword + LLM-judge; WMDP 1.27 → 6.2; never-exposed control at 0% ASR
- [Deeb & Roger, Do Unlearning Methods Remove Information from Language Model Weights? (arXiv 2410.08827)](https://arxiv.org/abs/2410.08827) — RTT probe, retrain on T evaluate on disjoint V, 88% recovery
- [Tramèr, Carlini, Brendel, Madry, On Adaptive Attacks to Adversarial Example Defenses, NeurIPS 2020](https://arxiv.org/pdf/2002.08347) — 13 defenses circumvented despite reported adaptive evaluations
- [Song & Mittal, Systematic Evaluation of Privacy Risks of ML Models, USENIX Security 2021](https://www.usenix.org/system/files/sec21-song.pdf) — in-family MIA-defense evaluation severely understates risk
- [Chua et al., Scalable DP-SGD: Shuffling vs Poisson Subsampling, NeurIPS 2024 (arXiv 2411.04205)](https://arxiv.org/abs/2411.04205) — shuffling reported as Poisson understates ε
- [Duan et al., Do Membership Inference Attacks Work on LLMs? (arXiv 2402.07841)](https://arxiv.org/abs/2402.07841) — no MIA above AUC 0.6 outside GitHub
- [Ippolito et al., Preventing Verbatim Memorization Gives a False Sense of Privacy, INLG 2023 (arXiv 2210.17546)](https://arxiv.org/abs/2210.17546) — perfect verbatim filter circumvented by style-transfer prompts
- [Nasr, Shokri, Houmansadr, Membership Privacy using Adversarial Regularization, CCS 2018 (arXiv 1807.05852)](https://arxiv.org/pdf/1807.05852) — closest named prior to the adversarial arm; ~3% utility cost

**MEDIUM confidence — read via search summary or single source:**
- [Carlini et al., Quantifying Memorization Across Neural Language Models, ICLR 2023 (arXiv 2202.07646)](https://arxiv.org/pdf/2202.07646) — (k,ℓ)-extractability, discoverable vs extractable memorization
- [Jagielski et al., A Note On Interpreting Canary Exposure (arXiv 2306.00133)](https://arxiv.org/pdf/2306.00133) — exposure does not convert to attack success or ε
- [Li et al., LLMs Can Be Strong Differentially Private Learners, ICLR 2022 (arXiv 2110.05679)](https://arxiv.org/pdf/2110.05679) — ghost clipping; per-example norms from activations and backprops
- [When Do Fewer Coordinates Suffice in DP-SGD? (arXiv 2606.04375, June 2026)](https://arxiv.org/html/2606.04375v1) — condition for coordinate restriction helping; +9.21/+10.25/+4.37 pt at ε=1/3/8 on CIFAR-10
- [Hans et al., Be like a Goldfish, Don't Memorize!, NeurIPS 2024 (arXiv 2406.10209)](https://arxiv.org/abs/2406.10209) — non-DP training-time memorization mitigation
- [Shi et al., Just Fine-tune Twice: Selective DP for LLMs, EMNLP 2022](https://aclanthology.org/2022.emnlp-main.425/) — selective DP over policy-designated sensitive tokens
- [MUSE: Machine Unlearning Six-Way Evaluation](https://arxiv.org/abs/2407.06460) — four metrics, no aggregate score
- [Adversarial Déjà Vu, ICLR 2026 (arXiv 2510.21910)](https://arxiv.org/html/2510.21910) — adversarial training limited by its training attack distribution
- [DP-FROST, COLING 2025](https://aclanthology.org/2025.coling-main.465/) / [TMI!, PoPETs 2024](https://petsymposium.org/popets/2024/popets-2024-0075.pdf) — DP fine-tuning gives no guarantee over pretraining data
- [Dwork & Roth, The Algorithmic Foundations of Differential Privacy](https://www.cis.upenn.edu/~aaroth/Papers/privacybook.pdf) — group privacy scaling in k

**LOW confidence — arithmetic and inference from this repo, not measured:**
- ≈14 training rows per fact (8 `CORE_SLOTS` × 5 `TAUGHT_FAMILY_IDS` → 112 taught rows in the Phase 18 corpus) — **verify by counting rows before committing any ε_fact number**
- ~1.2× hook-based per-example-gradient overhead and 10.6 MB materialization footprint — plausible from the shapes, but this is precisely what the milestone's cost calibration exists to measure

**Repo artifacts this research depends on (read directly):**
- `scripts/phase18_extraction.py` — `ATTACK_FAMILIES`, `apply_a1` / `build_a2_prompt` / `build_a3_prompt` with dose/intensity, `measure_exposure` / `exposure_rank`, `CORE_SLOTS`, `licensed_conclusion`, 112 taught / 104 held-out tiers
- `scripts/phase14_factset.py` — `LOCKED_FACTS`, `FAMILY_IDS` (F1–F8), `TAUGHT_FAMILY_IDS` / `HELDOUT_FAMILY_IDS`, `RESERVED_HELDOUT_PROBES`, `exact_match_clean`
- `scripts/teach_persona.py` — `train_arm`, `render_episodes`, `BATCH_SIZE=8`, `MAX_STEPS=200`, `LoRAConfig(r=8, alpha=16)`
- `scripts/erasure_gate.py` — the committed-gate pattern to reuse for X/Y

---
*Feature research for: training-time memorization mitigation + relearning validation on a 331,776-param persona adapter*
*Researched: 2026-08-20*
