# Project Research Summary

**Project:** PersonaCore — milestone v4.0 "Leakage Mitigation and Relearning Validation"
**Domain:** From-scratch DP-SGD on LoRA gradients + adversarial extraction-aware training + relearning-attack validation, on a shipped 13.9M/331,776-param PyTorch/MPS stack
**Researched:** 2026-08-20
**Confidence:** MEDIUM-HIGH

> **Evidence tags used throughout.** `[MEASURED]` = a number produced by running code, with the run
> named. `[LIT]` = a claim from a cited source. `[INFERENCE]` = derived by this synthesis, with the
> measurement that would confirm it stated inline. Anything untagged is a design recommendation.

---

## Executive Summary

v4.0 answers the 88.5% extraction rate Phase 18 measured, by building two training-time mitigations
and mapping them onto one privacy/utility plane under a pre-registered existence gate. The four
research passes agree on the shape of the work and on almost all of the mechanism, and they agree on
the stack answer completely: **zero new dependencies.** Every piece — per-example gradients, the
(ε, δ) accountant, Poisson sampling, the noise stream — is already in `torch==2.7.1` + stdlib `math`
+ `numpy`, and `opacus` is rejected with its concrete dependency cost priced (`scipy` +
`opt-einsum` landing in CPU-only CI for a 30-line function).

They disagreed on the one decision that determines whether the milestone's headline number means
anything: **what a "record" is.** ARCHITECTURE proposed fact-aligned deterministic full-batch
training so the ε covers a *fact*; STACK, FEATURES and PITFALLS assumed Poisson subsampling over
256-token windows so the ε covers a *window* and buys privacy amplification. This synthesis computed
both designs at the real corpus shape and **the fork resolves in ARCHITECTURE's favour — but for a
reason no researcher gave.** Amplification at q=0.103 is *not* "nearly gone" as STACK claimed: it is
worth 12.9× at fixed T and 3.2× at matched data passes `[MEASURED]`. It is cancelled almost exactly
by the group-privacy conversion needed to turn a window-level ε into the fact-level claim the
milestone makes — and at the measured multiplicity the conversion drives δ *above 1*, i.e. vacuous.
The two designs land within ~10% of each other on ε_fact; fact-alignment gets there at a δ two
orders of magnitude smaller, with an exact 20-line μ-GDP accountant instead of a subsampled-RDP one,
and with no per-example-gradient machinery at all.

The second thing this synthesis found is that **the DP arm is, with high prior probability, a
pre-registered null — and the roadmap should be built to publish that, not to avoid it.** Under a
fact-level unit the per-coordinate noise-to-signal ratio is `σ√d/L` = **72σ at L=8 facts**
`[MEASURED, STACK]`, and reaching ε_fact ≤ 4 needs σ ≥ 15.3 `[MEASURED, this synthesis]` — a ratio
near 1,100. Secret Sharer Table 3 is the direct precedent: per-record clipping destroyed
single-record memorization at *every* ε tested including ε = 10⁹ `[LIT]`. FEATURES predicted recall
would survive and PITFALLS predicted it would not; **that disagreement is entirely explained by the
unit** — FEATURES reasoned about a row-level unit where a fact is carried by 22 records, PITFALLS
about a fact-level unit where it is carried by one. Both are right about their own unit, and only
one of those units supports the claim v4.0 wants to make. The single free lever is the **number of
facts in the lot**: at q=1 the ε depends only on σ and T and is *independent of N*, so growing the
lot from 8 to 64 facts improves signal-to-noise 8× at identical ε `[INFERENCE — verified by
arithmetic below; confirm with one calibration run at n_facts=8 vs 64 at fixed σ]`. That, plus the
fact that the highest-severity finding in the whole pass is a **missing gate condition**, is what
should shape Phase 20.

---

## Key Findings

### Recommended Stack

`[Full detail: .planning/research/STACK.md]`

**No additions to `pyproject.toml` in any extra.** v4.0 makes it four milestones with zero new
runtime dependencies, and the sha256-pinned close state carries forward untouched. The three things
that would normally pull a dependency are each covered, and each was validated in-session rather
than asserted.

**Core technologies:**

- **`torch.func.vmap(grad(functional_call))`** — per-example gradients. **Works on MPS in torch
  2.7.1, costs 1.07× at B=8 and 1.02× at B=64 over an ordinary batched step, exact to 6.5e-08
  relative against batch-1 autograd truth** `[MEASURED — real GPT(ModelConfig()) + inject_lora,
  72 tensors / 331,776 params, MPS fp32, torch.mps.synchronize()-fenced]`. Nearly free because the
  base is frozen: the backward graph and the FLOPs are identical, and the only extra cost is
  declining to reduce a 331,776-param gradient over the batch (10.6 MB at B=8).
- **stdlib `math`** — the entire (ε, δ) accountant, ~20–40 lines. MPS has no fp64, so the accountant
  *must* live off-device in Python floats anyway; the zero-dependency answer is also the forced one.
- **`numpy ~=2.4`** — already core. Poisson index draw if ever needed, and the accountant's
  independent quadrature oracle.
- **`torch.Generator` + explicit noise device** — CPU-drawn noise recommended (3.9% of a step, vs
  0.07% on-device) because the same seed then reproduces the same adapter on M3, CPU and the dormant
  P100, and CI exercises the *production* noise path rather than a proxy `[MEASURED]`.

**Two live defects the stack pass found in this repo, both of which v4.0 activates:**

1. **`checkpoint.py` does not save MPS RNG state** — it saves `python`/`numpy`/`torch`(CPU)/`cuda`
   only (`checkpoint.py:102-106`, `:138-143`) `[MEASURED, both STACK and PITFALLS independently]`.
   This has never bitten because today's loop consumes *zero* device RNG (`nn.Dropout(0.0)` draws
   nothing; the data path draws through numpy, which is saved). DP noise is the first per-step device
   RNG consumer in the project's history. Five-line additive fix now (`.get("mps")`-style backward
   compat, exactly how the `scaler` slot was added); a full sweep re-run later.
2. **`get_batch_memmap`/`get_batch_memmap_masked` sample with replacement over a continuum of start
   offsets** (`training/data.py:85`, `:117`) `[MEASURED — 48/64 unique starts in a toy draw]`. That
   is neither Poisson nor shuffled, and adjacent "examples" share up to 255/256 of their content, so
   the records are not separable at all. It cannot feed any subsampled accountant.

### Expected Features

`[Full detail: .planning/research/FEATURES.md]`

**Must have (table stakes):**

- **DP-SGD from scratch on LoRA gradients** — per-record clip + Gaussian noise. The only arm that
  makes a formal claim, and the from-scratch deliverable.
- **From-scratch (ε, δ) accountant** — an ε without an accountant is a number, not a claim.
- **A DP-specific data path over enumerated, disjoint records** — the accountant's assumption. Not a
  nicety; without it the reported ε is invalid.
- **Retrained unmitigated control at identical budget and seed protocol** — v2.0's 0.4921 / 0.3483
  belong to a different run. Without this the frontier has no upper-right anchor.
- **Never-taught fresh adapter** — the frontier's lower-left anchor *and* the relearning reference.
  One run serves both; schedule it early. Note this is **not** the adapter-off control (which already
  exists at exactly 0/2430) — it is a fresh adapter trained on the same dialogue replay with the
  persona rows removed.
- **Adversarial extraction-aware training with intensity swept** — reuses `apply_a1` /
  `build_a2_prompt` / `build_a3_prompt`, already dose-parameterised in `phase18_extraction.py`.
- **Extraction rate as the privacy axis**, same fixture, same scorer, matched draw budget per
  compared pair. The only axis with power at n=8 facts.
- **Collateral utility per sweep point** — this is what catches the Phase 19 failure mode.
- **Pre-registered existence gate with X, Y and C committed before any point exists.**
- **Relearning attack, absolute recovery ceiling at a fixed, published Z.**
- **ε reported with its unit, its sampler, and its granularity, always in the same sentence.**

**Should have (differentiators):**

- **Leave-one-attack-family-out for the adversarial arm** — converts "generalization is an open
  question" from a disclaimer into a measurement. Given that Tramèr et al. broke **thirteen**
  published defenses that all reported adaptive evaluations `[LIT]`, a reviewer will otherwise
  discount the arm entirely. The four families already exist and are separable at zero construction
  cost.
- **Cost-to-recovery curve with a never-taught reference** — the "removed vs suppressed" test.
  PersonaCore can run this *cleanly* in a way 7B unlearning papers cannot, because the adapter is the
  only place the fact lives, so "never taught" is exactly constructible.
- **RTT-style T/V split reusing the existing family allocation** — `TAUGHT_FAMILY_IDS` /
  `HELDOUT_FAMILY_IDS` / `RESERVED_HELDOUT_PROBES` already exist and predate this milestone in git.
  Recovery on V cannot be explained away as "you just retaught it."
- **Two mechanisms on one measured-privacy × measured-utility plane with the gate rectangle drawn.**
  Do **not** put ε on the X axis: the two arms' sweep parameters are not commensurable and cannot
  share an axis. Sweep parameter goes in the label/colorbar; both axes are measured rates.
- **ε_fact published alongside ε_example, with the multiplicity measured** — most applied DP
  write-ups quietly report example-level ε over correlated data.
- **Both instruments carried per point** (generation-scored extraction *and* exposure rank) — v3.0
  measured these two disagreeing on the same weights; carrying both forward turns a co-headline into
  a standing control.

**Defer (v5.0+):**

- Adaptive attack designed *against* the trained defense — a research project of its own;
  leave-one-family-out already carries the honest scope limit.
- Goldfish loss as a third arm — name it in the report as the alternative not taken.
- Selective DP (Shi et al.) — the closest published construction to "learn the persona, hide the
  secret" and the natural v5.0 lead, but it changes the DP notion mid-milestone.
- Erasure at higher adapter rank; frozen-tokenizer retrain — already deferred in PROJECT.md.

**Rejected outright (impressive-looking, known to mislead):**

Membership inference as the privacy axis (no MIA exceeded AUC 0.6 on LLMs outside one domain
`[LIT]`, and there is no power at n=8); output filtering (a *perfect* verbatim filter was
circumvented by style-transfer prompts `[LIT]`, and it is not a weight-level mitigation, which is
this project's entire claim); a single composite "privacy score" (MUSE deliberately reports four
metrics with no aggregate, because aggregation lets one metric's collapse hide inside another's
win `[LIT]`); exposure/rank as the sole readout (v3.0 *measured* rank-1-at-ceiling on seven facts
whose generation had collapsed).

### Architecture Approach

`[Full detail: .planning/research/ARCHITECTURE.md]`

Everything is additive against named seams; five subsystems stay untouched. The DP intervention is
**gradient-side**, so it cannot ride `penalty_fn` (a loss-side seam that runs pre-`backward()`) —
that is the milestone's one real architectural gap. The recommendation is a `grad_privatizer=None`
kwarg invoked inside `_optimizer_step`'s existing accumulation loop, `None` reproducing today's path
bit-for-bit and provable by the Phase-10 golden-trajectory fixture that already exists.

**Major components:**

1. **Pre-registration layer** (`scripts/mitigation_gate.py`, `scripts/mitigation_budget.py`) —
   stdlib-only, no torch. Two files, not one, so the outcome-threshold-vs-resource-budget
   distinction becomes a fact about the import graph and git ancestry rather than a paragraph. An
   AST guard forbids the gate from importing the budget.
2. **Mechanism layer** (`src/personacore/privacy/dpsgd.py`, `accountant.py`) — importable,
   CPU-unit-testable, no orchestration. Nothing else goes in `src/`.
3. **Orchestration layer** (`scripts/phase2X_frontier.py`, `phase2X_relearn.py`) — `scripts/`, not
   `src/`, because a sweep has zero reuse surface. Resumable per *sweep point* via `phase19_run.py`'s
   `_merge_block` idiom; explicitly **not** resumable within a training run (a 200-step arm is
   minutes — `--redo-point <id>` deletes the point's artifacts and restarts).
4. **Evidence layer** — one committed JSON, counts never rates, `point_keys` proved as a hard ordered
   equality on write, then plot-only from the artifact under the `plot_phase15.py` AST + fresh-
   interpreter guard.

Two structural calls worth carrying verbatim into the roadmap: **the unmitigated control arm should
BE a sweep point** (the DP arm at `clip_norm=inf, noise_multiplier=0`), so control and DP differ by
exactly the two DP parameters and the frontier gets a natural ε=∞ anchor; and **the ε=∞ point will
not be bit-identical to a `grad_privatizer=None` run**, because the buffer round-trip reorders fp
additions — record that in advance so nobody "fixes" it.

### Critical Pitfalls

`[Full detail: .planning/research/PITFALLS.md — 28 pitfalls with mechanisms. Top five here.]`

The framing that should govern the whole milestone: v1.0–v3.0 shipped numbers that were
*measurements*, correctable by a dated continuation. **v4.0 ships a number that is a mathematical
claim.** An (ε, δ) that is wrong asserts a bound on what an adversary can learn, will be read as a
guarantee, and the only honest correction is retraction. And **every DP implementation bug in the
"silently non-private" class improves the numbers** — none of them raises, none trips any gate in
this repo, and each produces a plausible loss curve, a plausible recall, and a plausible ε.

1. **The gate is missing its capability condition (P24) — highest severity, cheapest to fix, and
   only fixable before the sweep.** See the dedicated section below.
2. **Clipping the batch gradient instead of the per-record gradient (P1).** `loop.py:165` already
   calls `clip_grad_norm_(model.parameters(), grad_clip)` on the *averaged* gradient, and
   `clip_grad_norm_` skips `grad is None` so it already targets exactly the 331,776 LoRA gradients
   `[MEASURED]`. It looks like DP-SGD's clip. The cheapest possible "DP-SGD" is
   `TrainConfig(grad_clip=C)` plus a noise line — a two-line diff that trains, converges, and is
   completely non-private. **This is the single highest-probability defect in the milestone,
   precisely because the codebase makes the wrong version easier than the right one.** Catch it with
   the two-example sensitivity probe (scale one example's loss 1000× and assert the σ=0 update does
   not move), plus an AST guard that no module on the DP path calls `clip_grad_norm_`.
3. **The privacy unit is undefined by the data path (P10).** There is no "example" in this codebase.
   At mean episode length 45.5 and block 256, **one window spans ~5.6 episodes** `[MEASURED from
   results/phase14_teaching_run.log]`, and replay at `replay_ratio=1.0` means half the bin is
   *other people's public dialogue* — computing `q = L/N` over a denominator that counts replay gives
   a smaller, better-looking ε than the persona data actually receives. This blocks the loader, which
   blocks the DP arm, which blocks the frontier. It is the milestone's longest dependency chain and
   it is **design work, not code work.**
4. **RNG reuse across steps (P6) — the bug that looks like success.** Composition requires per-step
   noise to be independent. A generator re-seeded per step adds the *same* vector every step; the run
   converges *better* than a correct implementation because correlated noise is easier to optimize
   through, and the accountant happily reports ε for T independent steps. `seed_everything` exists,
   is already called from `teach_persona.train_arm`, and its own docstring forbids per-step use —
   documented but not enforced. Catch with pairwise `torch.equal` inequality over 64 consecutive
   steps, **and watch a deliberately re-seeded positive control fail first.**
5. **The sweep composes, and the reported ε is per-point (P13).** N independent DP runs on the same
   data compose, and choosing the best point using the private data is an unaccounted data-dependent
   selection `[LIT — Papernot & Steinke]`. "We swept σ and report the best point" is a claim about a
   mechanism nobody accounted. Make it structurally impossible to print a bare ε: the reporting
   helper takes `(epsilon_point, epsilon_curve_total, selection_accounted)` as required keyword-only
   arguments, mirroring `erasure_succeeded(*, ...)`, with an AST scan asserting no module formats an
   ε outside it.

---

## Resolved Disagreements

The four researchers were given one premise that turned out to be false and reached partly
incompatible conclusions. Each fork is resolved below on evidence. Where the evidence does not
resolve it, that is stated with the measurement that would.

### R1. The sampling-design fork — RESOLVED for fact-aligned full-batch, on new arithmetic

**The fork.** ARCHITECTURE §2/§3: pad each fact's shard to whole `block_size` windows, set
`grad_accum_steps = n_facts`, so the existing accumulation loop *is* the per-record loop, there is no
subsampling, and T composed Gaussian mechanisms are **exactly** μ-GDP with μ = √T/σ in ~20 closed-form
lines. STACK Q2, FEATURES anti-feature #1, PITFALLS P11: Poisson subsampling with a subsampled-RDP
accountant, plus a new `poisson_batch()` loader, because the current sampler is unsound.

**STACK's stated reason for its side is wrong, and so is ARCHITECTURE's.** STACK claimed that at
q = 0.10–0.28 "privacy amplification by subsampling is nearly gone." ARCHITECTURE claimed that at
n≈8 facts "amplification buys nothing." Both are false `[MEASURED, this synthesis — integer-α SGM
RDP with Balle conversion, α grid 2..2048, δ=1e-5, cross-checked against the exact q=1 identity
RDP_α = α/(2σ²) at rel err 0.0]`:

| σ | ε at q=0.103, T=200 | ε at q=1, T=200 | ε at q=1, T=21 (matched data passes) |
|---|---|---|---|
| 2 | 3.785 | 54.377 | 11.835 |
| 4 | **1.601** | 20.676 | 5.127 |
| 8 | 0.731 | 8.596 | 2.321 |
| 16 | 0.343 | 3.797 | 1.076 |

Amplification is worth **12.9× at fixed T** and still **3.2× at matched data passes.** It is not
gone.

**What actually resolves the fork: the group-privacy conversion cancels it, and then some.** A
window-level ε only becomes the fact-level claim v4.0 makes by group privacy at k = windows
containing that fact, `(ε, δ) → (kε, k·e^{(k−1)ε}·δ)` `[LIT — Dwork & Roth; PITFALLS correctly warns
to pin this formula from a source at write time rather than retype it, and this table is exactly why]`:

| k | σ | ε_window | ε_fact | δ_fact | verdict |
|---|---|---|---|---|---|
| 5 | 4 | 1.601 | 8.00 | 3.0e-02 | δ 3,000× the target |
| 10 | 4 | 1.601 | 16.01 | **1.8e+02** | **VACUOUS (δ > 1)** |
| 22 | 4 | 1.601 | 35.22 | **8.8e+10** | **VACUOUS** |
| 10 | 16 | 0.343 | 3.43 | 2.2e-03 | usable |
| 22 | 32 | 0.167 | 3.68 | 7.4e-03 | usable |

Against the fact-aligned design at k=1, δ=1e-5 `[MEASURED, this synthesis — exact μ-GDP]`:
σ=16 → **ε_fact = 3.797**; σ=32 → **ε_fact = 1.737**.

**The two designs land within ~10% of each other on ε_fact** (3.43 vs 3.80 at σ=16, k=10) — and the
fact-aligned one gets there **at a δ two orders of magnitude smaller**, with no group-privacy step in
the argument, with an exact rather than bounded accountant, and with no per-record-gradient machinery
at all. Where k is larger than ~10 the Poisson-window route is strictly worse. Where it is smaller it
is still not better once δ is held equal.

**Three supporting findings, all measured:**

- **GDP is genuinely tighter than RDP at q=1**, confirming ARCHITECTURE's "tight, not a bound"
  claim: at σ=8, ε_GDP = 8.596 vs ε_RDP = 9.338; at σ=16, 3.797 vs 4.106 — ~8% in the useful band.
- **Poisson over *facts* at N=8 is degenerate as a mechanism**, not merely unhelpful: at q=0.25 there
  is a **10.0% chance of an empty lot on any given step**, and the sd of the lot size is 1.22 on a
  mean of 2.0. Deploying Poisson machinery over 8 records is not a defensible construction, and a
  loader that quietly resamples until it gets a non-empty lot has stopped being Poisson while still
  reporting Poisson ε (STACK's T7).
- **At q=1 the ε is independent of N** — it is a function of σ and T only. This is the free lever
  described in R4.

**Verdict: adopt fact-aligned deterministic full-batch as the primary design.** Keep the
subsampled-RDP accountant implemented and tested but *unused*, behind the same module — it is 30
lines, STACK already validated it against three independent oracles (best rel err 2e-13), and it is
the only thing that makes the fallback below cheap.

**Fallback, pre-registered in advance (ARCHITECTURE §2's own ladder, endorsed):** if fact-alignment
proves infeasible at the real corpus shape, report example-level ε **and** the measured multiplicity
k **and** the group-privacy inflation, with the headline explicitly scoped to "example-level." Do
**not** take ARCHITECTURE's option 2 (run DP with no formal claim at all) — that leaves v4.0 with two
empirical arms and no theory, which is a milestone-scope failure rather than a fallback.

**Consequences the roadmap must carry:**

- `poisson_batch()` is **not** on the critical path. STACK listed it as "not optional"; under the
  resolved design it is a tested-but-dormant sibling.
- The unsound `np.random.randint` sampler is still unusable for DP, and STACK/PITFALLS are right
  about that — the fix is `get_batch_fact_aligned` (deterministic, no RNG draw at all), not
  `poisson_batch`.
- The DP arm needs **no per-example-gradient machinery** under this design: `grad_accum_steps =
  n_facts` makes the existing loop the per-record loop.

### R2. The false premise — "the adapter surface is pure `nn.Linear`"

**The premise is FALSE** `[MEASURED — src/personacore/lora/layer.py:41 read directly]`:

```python
y = y + self.scale * (self.dropout(x) @ self.lora_A.T @ self.lora_B.T)
```

`lora_A` and `lora_B` are bare `nn.Parameter`s inside an inline matmul chain. They are not
`nn.Linear` submodules. **`register_forward_hook` / `register_full_backward_hook` do not reach
them** — a module hook on `LoRALinear` sees the wrapper's `x` and `y`; a hook on `self.base` sees the
frozen layer; neither yields `dL/dh`, which is what the per-example gradient of `lora_A` needs.

**And a new hard constraint that neither ARCHITECTURE nor FEATURES accounted for:** restructuring
`LoRALinear` to hold `nn.Linear` submodules renames `lora_A` → `lora_A.weight` in `state_dict()`,
invalidating `persona_adapter.pt`, **every v3.0 checkpoint**, `lora_state_dict` /
`load_adapter_weights`, and Phase 19's rank-1 component indexing. **No plan step may propose it.**

Conclusion-by-conclusion, as instructed — verified, not assumed:

| Conclusion | Rests on the false premise? | Survives? |
|---|---|---|
| FEATURES: per-example grads via **forward/backward hooks on the LoRA `nn.Linear` modules** | Yes, directly | **FALLS as written.** The mechanism does not compile against this code. Correct replacement: **tensor** hooks on the intermediates `h = x_drop @ A.T` and `delta = h @ B.T`, then `einsum("btr,bti->bri")` / `einsum("bto,btr->bor")`. Verified: `sum_b G_A == lora_A.grad` to 2.5e-07, per-example norms to 1.29e-07 `[MEASURED]`. `scale` needs no special handling — hooking the intermediates carries it through the chain. |
| FEATURES: **~1.2×** hook overhead | No — independent estimate | **FALLS.** Superseded by measurement: the tensor-hook path is **1.85×** (152.3 ms vs 82.2 ms at B=8) `[MEASURED]`. It was self-labelled LOW confidence and instructed to be measured; it was. |
| FEATURES: 10.6 MB materialization ⇒ ghost clipping unnecessary, cite don't implement | No — pure arithmetic on shapes | **SURVIVES.** 8 × 331,776 × 4 B is independent of module type. |
| ARCHITECTURE: **ghost clipping rejected on arithmetic** (~30× slower at r=8) | No — rests on the *mathematical* outer-product structure, which does hold ("exactly a linear layer, twice over" `[MEASURED, STACK]`) | **SURVIVES, and is strengthened.** Two independent derivations agree: ARCHITECTURE ~30× via `2T²(d_out+r)` vs `2T·d_out·r`; STACK ~33× with the crossover at **T < 7.8 tokens** against a production T=256. Ghost clipping exists because full fine-tuning has `d_in·d_out ≫ T²`; **LoRA at rank 8 inverts that inequality.** Reject it explicitly and quantitatively — it is a substantive design decision, not an omission. |
| ARCHITECTURE **AP-2**: `torch.func.vmap(grad(...))` is an anti-pattern ("functionalizes the whole GPT, MPS support uncertain") | No — but its stated grounds are falsified | **FALLS. Retract the anti-pattern.** `vmap(grad(functional_call))` works on MPS in torch 2.7.1, is exact to 6.5e-08, and costs 1.02–1.07× `[MEASURED at production shape]`. It also does **not** care that `lora_A`/`lora_B` are bare Parameters — `functional_call` swaps by *name*, and the LoRA names are already stable and already the artifact keys. |
| ARCHITECTURE: `grad_accum_steps = n_facts` makes the existing loop the per-record loop | No — structural, independent of module type | **SURVIVES.** Under R1's resolution this is the production path. |

**Net effect on the roadmap:** the two rejections both survive (ghost clipping stays rejected; module
hooks were never viable). The production path needs no per-example gradient machinery at all. But
**all three implementations should still be built as a test-only oracle battery**, because PITFALLS
P9 requires a three-way equivalence check and STACK has already produced its numbers: batch-1
autograd (the shape `estimate_fisher` already uses, 2.9–3.3×), `vmap` (1.02–1.07×, 6.5e-08), tensor-
hook einsum (1.85×, 1.29e-07). Plus the assertion that catches a `vmap` over a batch-reducing loss:
`sum_i g_i / B` must equal the ordinary batched `.backward()` gradient — off by exactly B if wrong.

### R3. Cost — the measured numbers supersede every estimate

| Quantity | Value | Status |
|---|---|---|
| `vmap(grad(functional_call))` vs batched step | **1.07× at B=8, 1.06× at B=16/32, 1.02× at B=64** | `[MEASURED]` — production shape, MPS fp32, sync-fenced, warm-up excluded |
| Numerical exactness of that path | **6.5e-08** max rel err on per-example norms; 2.10e-06 over all 72 tensors for one example (fp32 noise) | `[MEASURED]` |
| Tensor-hook + `einsum` | **1.85×** | `[MEASURED]` |
| Naive batch-1 accumulation | **3.31× / 3.03× / 2.89× / 2.97×** at B=8/16/32/64 | `[MEASURED]` |
| FEATURES' "~1.2× hooks" | — | **DISCARDED.** Self-labelled LOW confidence, wrong mechanism, and 1.85× measured. |
| PROJECT.md's original "~B×" (≈8×) for batch-1 | — | **CORRECTED to ~3×. Must not be repeated anywhere.** MPS is so far from saturated at B=8×T=256 that eight batch-1 passes cost about three batched passes. PROJECT.md already carries this correction at lines 167–178. |
| Noise draw, 331,776 coords, on-device MPS | 0.060 ms = 0.07% of a step | `[MEASURED]` |
| Noise draw, CPU → MPS | 3.215 ms = 3.87% of a step | `[MEASURED]` — recommended anyway, for device-independent regenerability |

**Still unmeasured and NOT to be assumed:** the fact-aligned full-batch step cost. ARCHITECTURE
predicts "roughly 1–4×, not 8×" for `grad_accum_steps=n_facts` vs `grad_accum_steps=1` at matched
token count; that is a *different quantity* from the per-example-gradient multiplier above and it has
no measurement behind it. `[INFERENCE: extrapolating STACK's measured B=64 row (737 ms), a 78-window
full-batch step is ≈0.9 s, so a 200-step arm is ≈3 min rather than ≈17 s — confirm in the Phase-23
calibration, do not plan against it.]`

### R4. What actually binds the sweep budget Z — ranked

The milestone brief assumed DP-SGD *training* cost binds. It does not. Ranked by how hard each
constraint actually bites:

**1. CORPUS SIZE — the real constraint, and it is not a wall-clock budget at all.** Per-coordinate
noise-to-signal is `σ√d/L` with d = 331,776 (√d = 576). At a lot of L = 8 facts that is **72σ**
`[MEASURED, STACK]`, and reaching ε_fact ≤ 4 requires σ ≥ 15.3, ε_fact ≤ 2 requires σ ≥ 28.2, ε_fact
≤ 1 requires σ ≥ 52.8 `[MEASURED, this synthesis]` — noise exceeding the entire clipping bound by
three orders of magnitude. Step budget is the wrong knob: at N=78 windows, ε ≤ 8 needs σ ≥ 1.23 at
T=200 and σ ≥ 0.68 at T=10 `[MEASURED, STACK]` — cutting steps 20× buys less than a factor of two.

  **The free lever, which no researcher identified.** At q=1 the ε is a function of σ and T *only* —
  it does **not** depend on N `[MEASURED — μ = √T/σ carries no N]`. So growing the lot is free
  privacy-wise and improves signal-to-noise linearly: L=8 → 72σ, L=64 → 9σ, L=576 → 1σ. Under a
  fact-level unit, growing the lot means **growing the number of facts**. The 8 `LOCKED_FACTS` and
  the 270-question fixture are ancestry-pinned and cannot change — but the DP arm can train on **8
  scored facts + M unscored filler facts**, which grows L and N without touching any fixture.
  `[INFERENCE — the ε-independence is arithmetic and solid; the utility payoff should be confirmed
  by one calibration run at n_facts=8 vs n_facts=64 at fixed σ, measuring recall on the 8 scored
  facts.]` Note the honest ceiling: even at L=576, σ=8.5 (the value for ε_fact ≤ 8) still gives a
  ratio of 8.5. **This lever improves the odds; it does not make the DP arm safe.**

**2. EVALUATION wall-clock — the likely binding constraint on sweep width, and it is UNMEASURED.**
The Phase 18 precedent is 42,480 draws per arm. STACK's generation-throughput probe failed this
session and **STACK asserts no number; neither does this summary.** `[GAP]` Scoring recall requires
generation, which is orders of magnitude slower than a training step. If evaluation costs materially
more than training, Z is gated by evaluation, which **inverts the milestone brief's stated
assumption.** The mitigation is already designed independently of the number: run the cost-to-
recovery curve on a small fixed probe subset (target fact's questions only, greedy, k=1) and score
the **endpoint** with the full instrument, recording in the artifact that the curve is DESCRIPTIVE at
a reduced denominator while the gate reads the endpoint at the full one — the house "gate only what
the sample supports" pattern.

**3. TRAINING wall-clock — does not bind.** A 200-step persona arm is **~17 s of MPS wall clock**
(83 ms/step at B=8) `[MEASURED]`, and per-example gradients add 2–7% to that. Under full-batch it is
minutes, not hours `[INFERENCE, see R3]`. Even a 6-point × 2-arm sweep with controls is well under
an hour of training.

**What the Phase-23 calibration must measure — all four legs, in one committed artifact:**

- **(a) Evaluation wall-clock per arm** at the full 42,480-draw budget *and* at a candidate reduced
  budget. This is the number STACK could not produce and it is the one that sets Z.
- **(b) Training wall-clock per arm under the chosen fact-aligned data path** — different tokens/step
  from every prior measurement, so no earlier number transfers.
- **(c) The per-record gradient multiplier under the chosen path** — only needed if the unit ever
  becomes finer than a micro-batch; measure it once so the fallback is priced.
- **(d) The real per-fact window multiplicity after `build_bins` packing at the chosen
  `replay_ratio`** — this sets N, sets the padding waste under fact-alignment, and sets k under the
  fallback design. It is a corpus measurement, not a timing, and it is the most load-bearing of the
  four.

Then Z is derived from whichever of (a)/(b) binds, committed in `scripts/mitigation_budget.py` with a
`_PROVENANCE` sibling naming the artifact and its sha, and sandwiched by two ancestry tests: the cost
artifact's first-add precedes the budget module's first-add, which precedes every frontier point's
first-add.

### R5. The gate is missing a condition — the highest-severity finding

**The finding.** `erasure_gate.py` carries **three** conditions and states in its own committed text
that the third exists *"because (a) and (b) can BOTH be satisfied by a model that has been degraded
into uselessness"* (`erasure_gate.py`, `ERASURE_DECISION_RULE` clause (c)). Phase 19 then proved the
point empirically: its target condition cleared *exactly* on its blind-calibrated floor with zero
headroom, while **77.6% of the dialogue adaptation was destroyed** and four of seven non-targets sat
at total generation loss.

The v4.0 gate as originally scoped had **two** conditions (`extraction ≤ X AND recall ≥ Y`), and
`recall ≥ Y` covers only the 8 `LOCKED_FACTS`. **A defense could zero leakage, hold taught-fact
recall, and have ruined the model at everything else — and a two-condition gate could not see it.**
PROJECT.md has since been corrected to three conditions (lines 190–205); this section makes (c)
concrete enough to pre-register.

**Condition (c), specified against what already exists in this repo.** All four constants are already
committed in `scripts/erasure_gate.py` and must be **imported, never retyped** (the standing
one-definition rule that already governs `wilson_upper_bound`, `holm`, `cluster_bootstrap`):

| Constant | Value | Home |
|---|---|---|
| `V20_MASKED_DIALOGUE_VAL_PPL` | 4.5733 | `erasure_gate.py:75` — Phase 12 production fine-tune, `results/finetune_prod.csv` |
| `V20_EWC_RETENTION_PPL` | 3.891140 | `erasure_gate.py:76` — Phase 13 EWC arm end-of-run |
| `V20_RETENTION_NOISE_FLOOR` | 0.068930 | `erasure_gate.py:77` — Phase 12 seed-to-seed floor |
| `MARGIN_K` | 2 | `erasure_gate.py:86` — the project-wide k=2 margin discipline |

The dialogue-PPL noise floor is **not** a constant in `erasure_gate.py` — `erasure_succeeded` takes
`dialogue_ppl_noise_floor` as a required keyword argument, and Phase 19 supplied it from a measured
record. That measured value is available and committed
`[MEASURED — results/phase19_noise_floors.json, block dialogue_ppl_noise_floor, record sha256
57d648d2…, n_targets 270,203]`:

```
dialogue_ppl_noise_floor = 0.005214448168350039
```

**Therefore the two caps, computed rather than typed:**

```
dialogue_cap  = 4.5733   + 2 × 0.005214448168350039 = 4.5837288963367   # already committed in that record
retention_cap = 3.891140 + 2 × 0.068930             = 4.029000
```

**Concrete, pre-registerable condition (c):**

> **(c) CAPABILITY PRESERVED.** A sweep point clears (c) only if, measured on the point's own adapter
> in the same run: `masked_dialogue_val_ppl ≤ dialogue_cap` **and** `retention_ppl ≤ retention_cap`,
> where both caps are computed from the imported `erasure_gate` constants and the measured
> `dialogue_ppl_noise_floor`, never from a literal. Both readings use `masked_perplexity()` (Phase 12)
> and the frozen 1,000,286-token retention sub-bin, routed through `undecodable_ids_mask` /
> `forbid_ids` so the instrument is the same one every published number in this repo used.

**Four further gate holes PITFALLS identified that must land in the same commit:**

1. **Y must be a pair, not a scalar.** v2.0 published *two* recall numbers (taught 0.4921, held-out
   0.3483). Gating taught-only rewards memorization over generalization — the wrong direction for a
   personalization claim. Require `Y_taught` **and** `Y_heldout`.
2. **Y must be expressed relative to the retrained control, as a fraction locked in advance** —
   e.g. `≥ 0.7 × control_recall`. That is an outcome threshold committed before any outcome exists,
   and it is the whole reason the control is being retrained. Deriving Y from v2.0's 0.4921 would
   make the control decorative.
3. **An INCONCLUSIVE branch for zero-extraction-without-NLL.** A degenerate or refusing generator
   scores 0 extraction. Phase 19's co-headline is that two instruments disagreed on the same weights.
   Port `zero_results_have_nll` semantics verbatim: extraction at or near zero **without** a
   corroborating teacher-forced NLL is INCONCLUSIVE, never a pass. INCONCLUSIVE takes precedence
   over FAILURE, as `erasure_succeeded` already establishes.
4. **A FAILURE-vs-INCONCLUSIVE discriminator for a truncated sweep.** "No point cleared" and "the
   sweep never reached the region where a point would clear" are different findings. Pre-register:
   INCONCLUSIVE if the swept axis never produced a point on both sides of X (or of Y) — a truncated
   curve cannot refute existence. This is the direct analogue of `erasure_gate`'s
   `zero_results_have_nll` clause and it is exactly the failure a mis-set Z produces.

Plus two that follow from the multiplicity of the sweep: **the gate must return the arm identity**
(a DP point clearing carries a formal claim; an adversarial point clearing does not, and "∃ a point"
over the union conflates them), and **the winning point must be replicated at a second seed** before
the ∃ is anything but provisional — Phase 17's worst-pair-replicated-at-k=3 pattern, required by the
gate rather than reported alongside it.

**Signature shape, mirroring the committed precedent so a caller cannot transpose two counts:**
every argument keyword-only, no defaults, `VERDICTS = ("PASS", "FAIL", "INCONCLUSIVE")`, every
condition rendered into a reason string. Its `__main__` self-check must exercise every branch
including the failing ones, and **a "mitigation that destroyed the model" fixture must be run through
it and observed returning FAIL** — a branch nobody has watched fire is a branch nobody has verified.

**Ordering is the whole point.** `erasure_gate.py` was committed at `23a830c` before Phase 16 ran.
The v4.0 gate must be committed before *any* v4.0 number exists — before the cost calibration, not
merely before the sweep. Adding condition (c) before the sweep is one commit; adding it after results
exist is a threshold moved after seeing data, and the gate's entire evidentiary value is gone.

### R6. Corrected number: 22 rows per fact, not 14

FEATURES inferred "≈14 training rows per fact" at LOW confidence (112 taught rows ÷ 8 `CORE_SLOTS`)
and instructed that it be counted before use. **It was counted, by executing
`phase14_factset.render_family` in the project venv: 22 rows per fact, uniform across all 8
`LOCKED_FACTS`, 176 taught rows total** — per taught family F1:5, F2:5, F4:4, F5:4, F6:4 (5+5+4+4+4
= 22; 22 × 8 = 176) `[MEASURED]`. PITFALLS reached 22 independently by a different route (220
episodes ÷ 10 facts, from `results/phase14_teaching_run.log`) `[MEASURED]`. **Use 22. The "≈14"
figure is withdrawn and must not be carried forward.**

**Honest bound on what 22 licenses.** 22 is the count of *rendered rows in the taught tier*. The
**effective per-fact multiplicity in gradient steps** still depends on `build_bins` window packing
and `replay_ratio` — and that multiplicity, not the row count, is what any published ε rests on:
it sets k in the group-privacy conversion under the fallback design, and the padding waste under
fact-alignment. It is calibration leg (d) in R4 and it is unmeasured.

---

## Implications for Roadmap

Eight phases, dependency-ordered. Phase numbering continues from v3.0, so v4.0 opens at Phase 20.

### Phase 20: Pre-registration — the three-condition gate, before any v4.0 number

**Rationale:** Its entire evidentiary value is the ordering, and everything else can be reordered.
This must precede even the cost calibration, so that no v4.0 number of any kind predates the rule
that judges v4.0 numbers.
**Delivers:** `scripts/mitigation_gate.py` (stdlib-only, phase-neutral, keyword-only) carrying
`OUTCOME_*` X / `Y_taught` / `Y_heldout` / condition-(c) caps computed from imported `erasure_gate`
constants; `PRIVACY_UNIT`, `NEIGHBOURING`, `SENSITIVITY_MULTIPLIER` and `δ` as committed strings and
literals in the same block; the committed **sweep grid as a tuple literal**; the FAILURE-vs-
INCONCLUSIVE discriminator; `relearning_is_worth_attempting`; arm-conditional claim strings. Plus
`scripts/_prose.py::normalized` (~5 lines — the whitespace-normalizing prose search that does not
exist anywhere in this repo `[MEASURED — verified absent]`, and whose absence already produced one
false-absence defect in v3.0).
**Addresses:** the existence gate; ε-granularity reporting.
**Avoids:** P24 (missing capability condition), P17 (existence read as typical-case), P18 (post-hoc
grid extension), P3 (sensitivity constant defined once, read by three consumers), P28 (prose checks).
**Tests:** three ancestry/import guards (gate must not import budget, AST scan); the
no-redefinition AST scan over `wilson_upper_bound` / `cluster_bootstrap` / `sign_test_exact` /
`holm`; a model-destroying fixture observed returning FAIL.

### Phase 21: The privacy unit, the DP data path, and the corpus

**Rationale:** The longest dependency chain in the milestone and **design work, not code work.** The
unit determines the loader, the lot, the accountant and every ε. It cannot be patched after a DP arm
trains.
**Delivers:** `PRIVACY_UNIT = "one taught fact"` committed; `build_bins(..., align_facts=None)`
(default byte-identical to v2.0); `get_batch_fact_aligned` as a **new** function in
`training/data.py` (nothing modified); the structural check that no `block_size`-aligned window
contains token ids from two fact shards, in the shape of Phase 14's `assert_value_in_prompt`; the
**measured** per-fact window multiplicity after packing (calibration leg (d)); the decision on
whether replay participates in the DP lot; and the **regenerated corpus at n_facts ≫ 8** (8 scored +
M unscored filler) per R4's free lever.
**Avoids:** P10 (unit undefined by the data path), P11 (accountant/sampler mismatch), P16 (replay
diluting the denominator in the flattering direction).
**Research flag: NEEDS DESIGN.** The filler-facts construction has no prior in this repo, and the
replay-in-lot question changes the ε. Neither needs external literature; both need a decision
recorded before code.

### Phase 22: DP-SGD core, accountant, and the correctness battery

**Rationale:** The from-scratch deliverable, and the phase where every bug is silent, flatters the
number, and trips no existing gate. Fully CPU-unit-testable before any training run.
**Delivers:** `privacy/accountant.py` (exact μ-GDP: `mu_gdp`, `delta_at_epsilon`,
`epsilon_at_delta`, ~20 lines, `math.erf` only — plus the subsampled-RDP path implemented, tested and
**dormant**, so the R1 fallback is cheap); `privacy/dpsgd.py`; the `grad_privatizer=None` loop seam
with the two fail-loud preamble guards (raise under AMP; raise if `grad_clip` is finite); the **MPS
RNG checkpoint slot**; `dp_parameters()` as the single ordered filter; the release ledger.
**Uses from STACK:** `torch.func` (oracle only, under this design), `torch.Generator`, CPU-drawn
noise, `checkpoint_extra`, `CSVLogger`.
**Avoids:** P1, P2, P3, P5, P6, P8, P9, P26. **Test battery, non-negotiable:** two-example
sensitivity probe (with the batch-clip positive control watched failing); 2000-draw empirical σ vs
the closed form `σC/L`; pairwise noise-independence with a re-seeded positive control; three-way
gradient equivalence **plus** `sum_i g_i / B == batched .backward()`; kill→resume producing a
**bit-identical reported ε**, not merely a matching loss curve; golden-trajectory bit-identity with
the seam off.
**Accountant oracles, all zero-dependency and all already validated `[MEASURED, STACK]`:** the q=1
collapse to `RDP_α = α/(2σ²)` (rel err 0.0 reproduced in this synthesis); independent 1-D numerical
quadrature of the Rényi divergence (best rel err 2e-13 — *different mathematics, different failure
modes*, which is the property an oracle should have and an `opacus` cross-check does not); the
small-q asymptotic `α q²(e^{1/σ²}−1)/2` (note: the frequently-quoted `2q²α/σ²` is a 4× overstatement
and pinning against it is itself one of the plausible-but-wrong traps).
**Research flag: SKIP.** STACK measured and validated everything this phase needs.

### Phase 23: Cost calibration → budget pre-registration

**Rationale:** Z is a resource parameter derived from a measurement; the measurement cannot precede
the mechanism it times. Both legs must be measured because the brief's assumption about which one
binds is falsified (R4).
**Delivers:** `results/phase2X_cost.json` covering all four legs of R4 — evaluation wall-clock at
full and reduced draw budgets, training wall-clock under the fact-aligned path, the per-record
gradient multiplier, and the per-fact window multiplicity. Then `scripts/mitigation_budget.py` with
`BUDGET_*` + `_PROVENANCE` siblings. Plus the **σ=0 sanity point** (per-record clipping only, no
noise — must reproduce the unmitigated control within the seed-to-seed noise floor) and a committed
`results/dp_mps_smoke.json` recording a green on-M3 MPS DP smoke at the current git SHA, which the
sweep driver refuses to start without.
**Avoids:** P7 (CPU-green is not evidence for an MPS noise stream), P20-p, and the whole class of
budget-artifact failures.
**Research flag: NEEDS MEASUREMENT.** The evaluation leg is the one number no researcher could
produce. Do not plan against an assumed value.

> The σ=0 point is **the single highest-value diagnostic in the milestone** and should be the DP
> arm's first executed run. It costs one run and it is the only thing that separates "DP is hard at
> this scale" from "the DP code is wrong" — the milestone's central ambiguity, and the one every
> Group-A bug hides inside, because every one of those bugs *improves* utility.

### Phase 24: Adversarial arm + the TRAIN/HELD-OUT attack partition

**Rationale:** Data-only — attack intensity is a data-mixture ratio, exactly the shape
`_prepend_replay` already has. No loop change, no accountant, no per-record anything. Lowest-risk
mechanism in the milestone, and under R1's arithmetic the arm **most likely to produce a clearing
point.**
**Delivers:** `build_bins(..., adversarial_ratio=0.0)` (default byte-identical); the committed
TRAIN/HELD-OUT attack-family partition with **no family in both**, reusing Phase 18's existing
`GATED_TIER = "core_held_out"` / `REPORTED_TIER = "core_taught"` discipline; leave-one-family-out
with the held-out family pre-registered **before** training; a zero-`(fact_id, seed_index)`-overlap
structural check read from `results/phase18_corpus.json`; an inflation report on every new corpus.
**Avoids:** P22-p (scoring an arm on its own training attacks), P27 (tokenizer inflation — the
frozen 547-live-id tokenizer inflates perturbed text **1.40× uppercased, 1.17× role-play framed**
`[MEASURED]`, so attack intensity *is* a budget axis and must be reported as scored-token counts per
arm), AP-6 (`phase18_extraction.py` is ancestry-guarded and permanently uneditable — import it
read-only; a forked copy would let the attack trained-against and the attack scored-by drift apart
silently).
**Research flag: SKIP.** Transforms exist and are dose-parameterised; the tier split exists.

### Phase 25: Frontier sweep + existence-gate verdict

**Rationale:** Cost-ascending and dependency-driven. The control validates the whole
train→score→merge pipeline before any DP run burns time.
**Delivers, in this order:** (1) the **unmitigated control point first**, as a sweep point at
`clip_norm=inf, noise_multiplier=0` — **if its recall does not land in a defensible neighbourhood of
v2.0's 0.4921 / 0.3483, stop**, because the fact-aligned recipe changed something and every later
point is uninterpretable; (2) the DP sweep over σ with the **extremes run first**, so an empty
frontier reveals itself in two runs instead of N; (3) the adversarial sweep over
`adversarial_ratio`; (4) verdict and figures from the committed JSON only.
`results/phase2X_frontier.json` records **counts, never rates**, with `per_question_successes` so any
bound is re-derivable, `point_keys` proved as a hard ordered equality on write, `accounting: null` on
the adversarial arm as the structural statement that it makes no formal claim, and the gate/budget
module sha256s travelling in the artifact.
**Avoids:** P13 (ε unprintable outside the three-argument helper), P16 (`spec_digest` per point; the
gate refuses points differing outside the declared axis), P17 (Wilson bounds gate, not point
estimates; questions as the unit, never draws; winning point replicated at a second seed), P18
(driver refuses off-grid points), P25 (**the null is pre-registered** — "no DP point clears Y" is a
named verdict, not a failure to produce a result).
**Research flag: SKIP.** `phase19_run.py`'s `_merge_block` idiom and `plot_phase15.py`'s AST +
fresh-interpreter guard are both live precedents to copy.

### Phase 26: Relearning attack

**Rationale:** Gated on `relearning_is_worth_attempting(points)` called once on measured numbers —
exactly the shape of `erasure_is_worth_attempting(92, 104, 0, 104)` authoring Phase 19. If no point
cleared the frontier, relearning is **MOOT**, not a pass, and the milestone ships that finding.
**Delivers:** Z calibrated **from the two controls before the mitigated arm is attacked** (the
smallest budget at which both the fresh never-taught adapter and the retrained unmitigated control
clear the recall threshold), then committed; mitigated + fresh arms constructed from **one**
`TrainConfig` object (a single object cannot diverge) with a Layer-2 evidence diff read back off disk
and a Layer-3 data-order proof; the attacker-corpus ladder at ≥3 rungs (held-out families /
syntax-matched-content-disjoint / content-adjacent-syntax-mismatched); three-arm recovery curves over
**scored tokens**, not steps; endpoint at the full instrument, curve at the reduced probe.
**Avoids:** P19 (baseline is a required kwarg with no default — a gate that cannot be called without
the baseline cannot be evaluated without it; INCONCLUSIVE if the fresh baseline itself fails within
Z), P20-p, P21-p (**syntactic similarity, not topical overlap, is the primary driver of recovery**
`[LIT]` — an attacker corpus matched on topic but not on `encode_dialogue`'s `<|user|>`/`<|assistant|>`
shape may under-recover for reasons unrelated to the mitigation), P23-p (endpoint-only measurement
cannot distinguish suppression from removal).
**Research flag: NEEDS RESEARCH.** The syntax-vs-topic finding is recent and effectively single-
source, and it determines the corpus ladder's construction — the axis the whole attack rests on.

### Phase 27: Report, milestone close, inherited debt

**Rationale:** v3.0's retrospective records remediation introducing defects at nearly the rate it
closed them, three rounds running — on *prose*. v4.0's remediation surface includes noise scale,
sensitivity and sampling rate, where a wrong value produces no error and no symptom, only a number
that is too good.
**Delivers:** tables **generated** from committed records and re-rendering byte-identically, never
authored; a test asserting every ε / σ / C / q / δ appearing in `docs/REPORT.md` matches the module
constant it claims to quote; every doc-consistency check routed through `_prose.normalized`; the
canonical claim string ("at least one configuration of N swept") quoted verbatim everywhere;
correction diffs that change figures and add no explanatory prose in the same commit; and explicit
budget for the **16 inherited debt items plus three permanent false `audit-open` gaps** carried in
from v3.0.

### Candidate additional phase (P2, decide explicitly)

**Empirical privacy audit** — canary-based one-run auditing produces an *empirical lower bound* on ε.
If the measured ε_lower exceeds the claimed ε_upper, the implementation is **provably broken**. It is
the only mechanism in the entire research pass that tests the *guarantee* rather than the *code*, and
it is the strongest available answer to "how do you know your from-scratch DP-SGD is correct?" This
project already owns most of the apparatus: a canary fixture, a scorer, a Wilson bound, and a
42,480-draw budget precedent. **If it is cut, record that as a named limitation under the D-16
discipline (a negative decision carries a positive's weight), not as silence.** It wants the canary
infrastructure early, so the decision belongs at roadmap time, not at Phase 26.

### Phase Ordering Rationale

- **The gate is phase-zero because ordering is its only evidence.** Everything else can be resequenced.
- **The privacy unit blocks the loader, which blocks the DP arm, which blocks the frontier.** It is
  the longest chain, it is design work, and it is the one thing that cannot be patched afterwards —
  "the unit was wrong" invalidates every ε and no amount of re-running fixes it.
- **The MPS RNG checkpoint slot is five lines now and a full sweep re-run later.** It must land
  before any long run, which is why it is in Phase 22 and not discovered at the first interruption.
- **The σ=0 point precedes every noised point** because it is the only thing that separates the
  milestone's most likely honest negative from its most likely silent bug.
- **Both anchors precede every sweep point.** A point at extraction 0.30 means nothing until you know
  the retrained control sits near 0.885 and the never-taught arm at the floor. The never-taught arm
  serves both the frontier and the relearning curve — one run, scheduled early.
- **Z is calibrated from the controls, so relearning depends on the control existing** — but the
  never-taught fresh baseline depends on nothing and can run early.
- **The adversarial arm needs no new mechanism**, so it is the lower-risk hedge and a reasonable
  second in the sweep — and under R1's arithmetic, the likelier source of a clearing point.

### Research Flags

**Needs deeper research during planning:**

- **Phase 21** — the privacy unit is a design decision with no in-repo prior; the filler-facts
  construction and the replay-in-lot question both change the ε and both need a recorded decision
  before code.
- **Phase 23** — the evaluation wall-clock leg is genuinely unmeasured; the calibration must produce
  it rather than a plan assuming it.
- **Phase 26** — the syntax-vs-topic driver of relearning recovery is recent and effectively
  single-source, and it determines the attacker-corpus ladder, which is the axis the attack rests on.

**Standard patterns, skip `--research-phase`:**

- **Phase 20** — `erasure_gate.py` is the template, is committed, and has been read.
- **Phase 22** — STACK measured every gradient path at production shape and validated the accountant
  against three independent oracles; nothing is left to look up.
- **Phase 24** — the attack transforms are dose-parameterised and the tier split already exists.
- **Phase 25** — `phase19_run.py`'s merge idiom and `plot_phase15.py`'s guard are live precedents.
- **Phase 27** — the v3.0 retrospective already names every mechanism.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **HIGH** | Every load-bearing number measured in this repo, this venv, at production shape, sync-fenced. Accountant cross-verified against three independent oracles (best rel err 2e-13) and reproduced independently in this synthesis (q=1 identity at rel err 0.0). Two live codebase defects verified by direct probe rather than inferred. |
| Features | **MEDIUM** | Primary sources fetched and quoted for the DP / canary / relearning conventions (HIGH), but the two load-bearing repo-derived claims were both wrong: "~14 rows/fact" (now 22, measured) and "hooks on the LoRA `nn.Linear` modules, ~1.2×" (mechanism falls, cost measured at 1.85×). Its central A6 prediction is *unit-conditional* and was stated for a unit the milestone should not adopt. |
| Architecture | **MEDIUM-HIGH** | Integration points read against the live tree at `4554ef4` — HIGH, and the seam design, the two-file pre-registration split, the schema discipline and the build order are all directly usable. But AP-2 (rejecting `vmap`) is falsified by measurement, and its winning §2 recommendation was argued from a false premise ("amplification buys nothing"); the right answer for the wrong reason. |
| Pitfalls | **HIGH** | Every codebase-specific claim measured on this machine (MPS/CPU RNG streams are separate; `checkpoint.py` has no `mps` slot; `clip_grad_norm_` already targets exactly the LoRA grads; `nn.Dropout(0.0)` consumes no RNG; tokenizer inflation 1.40×). Literature claims are canonical and multiply sourced. Deliberately publishes **no ε estimate**, which is the correct discipline. |

**Overall confidence: MEDIUM-HIGH.** The mechanism, the stack, the seams and the failure modes are
well-established. The two genuine unknowns are both *measurements the roadmap already schedules*
(evaluation wall-clock, per-fact multiplicity), and the one genuine judgement call — whether the DP
arm produces any non-floor point — is pre-registered as a reportable null either way.

### Gaps to Address

1. **Evaluation wall-clock is unmeasured, and no number is asserted anywhere.** `[GAP]` It plausibly
   binds Z, inverting the brief's assumption. → Calibration leg (a), Phase 23. Any plan that names a
   number here is inventing it.
2. **Per-fact window multiplicity after `build_bins` packing at the chosen `replay_ratio` is
   unmeasured.** `[GAP]` It sets N, the padding waste under fact-alignment, and k under the fallback.
   → Calibration leg (d), Phase 21/23. This is the number any published ε actually rests on.
3. **Whether the DP arm can produce any non-floor recall point.** `[INFERENCE — the arithmetic says
   probably not at n_facts=8: 72σ noise-to-signal, σ ≥ 15.3 for ε_fact ≤ 4.]` → Pre-register the null
   in the gate's verdict domain; run the σ=0 point first; grow the lot per R4's free lever.
4. **Whether unscored filler facts are admissible.** `[INFERENCE — ε-independence of N at q=1 is
   solid arithmetic; the utility payoff is not measured.]` → One calibration run at n_facts=8 vs 64
   at fixed σ, scoring recall on the 8 fixture facts only.
5. **PITFALLS' δ recipe is self-contradictory at a fact unit — do not use it.** P14 prescribes
   `DELTA = 1/N^1.1` and asserts `δ·N < 0.01`. At N=8 facts that gives **δ = 0.1015, and
   δ·N = 0.812**, failing its own assertion by ~80× `[MEASURED — arithmetic]`. → Pin δ = 1e-5 as a
   committed literal with its rationale in the same block as X and Y. Note honestly that at N = 8
   records, (ε, δ)-DP is a strained vocabulary regardless of the value chosen; the strongest response
   is R4's lever (grow N), not a smaller δ.
6. **The group-privacy formula is load-bearing in R1's decisive table and was transcribed, not
   fetched.** PITFALLS explicitly warns: pin `(ε,δ) → (kε, k·e^{(k−1)ε}·δ)` from a source at write
   time. → Do so in Phase 21 before it enters any artifact.
7. **The fact-aligned full-batch step cost is unmeasured** (only inferred at ≈0.9 s/step, ≈3 min/arm).
   → Calibration leg (b).
8. **The relearning corpus is a threat model, not a resource choice.** It is an outcome-shaping
   decision and must be pre-registered in the gate module, not chosen in the driver.
9. **Whether the replay stream participates in the DP lot.** PersonaChat replay is public data
   already in the base's training distribution and arguably needs no accounting — but it lands in
   windows, and the decision changes the ε. → Decide in Phase 21; record the decision, not the
   default.

---

## Sources

### Primary — MEASURED in this repo, this venv, this session (HIGHEST)

- `torch==2.7.1` on MPS at production shape (`GPT(ModelConfig())` + `inject_lora`, 72 tensors /
  331,776 params, fp32, `torch.mps.synchronize()`-fenced): per-example gradient cost multipliers at
  B=8/16/32/64; `vmap`-vs-batch-1 equivalence (6.5e-08); tensor-hook closed-form equivalence
  (2.5e-07); MPS `Generator` state round-trip; CPU-generator-on-MPS `RuntimeError`; MPS fp64
  `TypeError`; `vmap`+dropout randomness modes; noise-draw costs; persona corpus window counts (78 /
  29); σ-for-target-ε solves.
- RDP/GDP accounting recomputed independently in this synthesis: q=1 identity `RDP_α = α/(2σ²)` at
  rel err 0.0; the amplification table; the group-privacy table; the Poisson-over-8-facts degeneracy;
  the σ-for-ε_fact solves; the `δ = 1/N^1.1` contradiction at N=8.
- In-repo source read at `4554ef4`: `lora/layer.py:38-42`, `training/loop.py:136-169`,
  `training/data.py:65,85,117`, `checkpoint.py:102-106,138-143`, `continual/fisher.py`,
  `scripts/erasure_gate.py:75-136,196-260`, `scripts/teach_persona.py`, `scripts/phase18_extraction.py`.
- `results/phase19_noise_floors.json` — measured `dialogue_ppl_noise_floor = 0.005214448168350039`,
  cap 4.5837288963367, record sha256 `57d648d2…`, n_targets 270,203.
- `results/phase14_teaching_run.log` — 220 episodes, 20,036 tokens (10,018 teaching + 10,018 replay),
  episode length mean 45.5 [24, 84].
- `phase14_factset.render_family` executed in the project venv — **22 rows per fact, uniform across
  8 `LOCKED_FACTS`, 176 taught rows** (F1:5, F2:5, F4:4, F5:4, F6:4).
- Frozen-tokenizer inflation on one 51-char sentence: clean 35 tokens, uppercased 49 (**1.40×**),
  role-play framed 1.17×.

### Primary — literature, fetched and quoted (HIGH)

- Mironov, Talwar, Zhang, *RDP of the Sampled Gaussian Mechanism* (arXiv 1908.10530) — the integer-α
  closed form and the Poisson assumption.
- Balle et al., *Hypothesis testing interpretations and Rényi DP* (AISTATS 2020) — the improved
  RDP→(ε,δ) conversion.
- Gaussian DP composition (arXiv 2503.10945) — `μ = √T/σ` for T identical Gaussian mechanisms and the
  exact `δ(ε) = Φ(−ε/μ + μ/2) − e^ε·Φ(−ε/μ − μ/2)` dual.
- Carlini et al., *The Secret Sharer* (USENIX Security 2019) — exposure formula and **Table 3: a
  once-inserted canary is unextractable at every ε tested including 10⁹, exposure 1.1–3.2 vs 31.0
  without DP.** The direct precedent for the DP arm's expected null under a fact-level unit.
- Yu et al., *DP Fine-tuning of Language Models* (ICLR 2022) — frozen base + DP on adapter params
  only; ε=6.7 MNLI 87.8% vs 90.2%; PEFT-under-DP beats full-model DP on privacy, utility and compute.
- Hu et al., *Jogging the Memory of Unlearned LLMs* (ICLR 2025) — relearning protocol (LoRA, lr 2e-4,
  batch 8, 15/30/48/60 steps), three-model comparison, never-exposed control at 0% ASR.
- Deeb & Roger (arXiv 2410.08827) — RTT probe: retrain on T, evaluate on disjoint V; 88% recovery.
- Tramèr, Carlini, Brendel, Madry (NeurIPS 2020) — **thirteen** defenses circumvented despite reported
  adaptive evaluations.
- Song & Mittal (USENIX Security 2021) — in-family MIA-defense evaluation severely understates risk.
- Chua et al. (NeurIPS 2024) — shuffling reported as Poisson substantially understates privacy loss.
- Duan et al. (arXiv 2402.07841) — no MIA above AUC 0.6 on LLMs outside one domain.
- Ippolito et al. (INLG 2023) — a *perfect* verbatim filter circumvented by style-transfer prompts.
- Papernot & Steinke (arXiv 2110.03620) — DP hyperparameter tuning has a real, non-zero privacy cost.
- Dwork & Roth, *Algorithmic Foundations of DP* — group privacy scaling in k. **Pin the exact formula
  from the source before it enters an artifact.**
- PyTorch blog, *Fast Gradient Clipping and Ghost Clipping in Opacus* — the cost model whose
  arithmetic rejects ghost clipping at r=8.
- `opacus` 1.6.0 PyPI metadata — `numpy`, `torch>=2.6`, **`scipy>=1.2`, `opt-einsum>=3.3.0`**: the
  concrete dependency cost of the rejected library.

### Secondary (MEDIUM)

- MUSE (arXiv 2407.06460) — four metrics, no aggregate score.
- *When Do Fewer Coordinates Suffice in DP-SGD?* (arXiv 2606.04375) — the condition under which
  coordinate restriction helps.
- Nasr, Shokri, Houmansadr (CCS 2018) — adversarial regularization, the closest named prior to the
  adversarial arm; ~3% utility cost.
- Hans et al., *Be like a Goldfish* (NeurIPS 2024) — the non-DP alternative not taken.
- *Adversarial Déjà Vu* (ICLR 2026) — adversarial training limited by its training attack distribution.
- DP-FROST (COLING 2025) / TMI! (PoPETs 2024) — DP over fine-tuning data gives no guarantee over the
  frozen base's pretraining data. Benign here (Phase 14's `FACTSET_GATE_SHA` proves every locked fact
  base-fails), but the sentence must appear or a reviewer will assume it was overlooked.
- *How to DP-fy ML* (arXiv 2303.00654) — micro-batch clipping sensitivity is 2G, not G.
- One-run privacy auditing (arXiv 2606.12733 and related) — empirical ε lower bounds.

### Tertiary — needs validation (LOW)

- *Rethinking Benign Relearning: Syntax as the Hidden Driver* (arXiv 2602.03379) — syntactic, not
  topical, similarity drives recovery. **Load-bearing for the Phase 26 corpus ladder and effectively
  single-source.** Validate before the ladder is committed.
- ARCHITECTURE's "roughly 1–4×, not 8×" for fact-aligned vs single-micro-batch stepping — an
  unmeasured prediction about a quantity nobody has timed. Measure it; assume neither number.
- STACK's ~600 fact-renderings estimate in its ε table — explicitly an estimate, now superseded by
  the measured 176 taught rows / 22 per fact, and to be replaced entirely by the regenerated corpus's
  real count.

---
*Research completed: 2026-08-20*
*Ready for roadmap: yes*
