# Phase 19: Selective Memory Erasure — Research

**Researched:** 2026-08-17
**Domain:** Machine unlearning of a single taught fact from a 331,776-parameter LoRA adapter over a frozen 13.9M-parameter GPT, on Apple Silicon MPS, fp32, zero budget
**Confidence:** HIGH on repo facts (every one measured or read this session) · MEDIUM on mechanism outcomes (nothing has been run) · HIGH on the ordering constraints

> Every claim about this repository below carries a `file:line` pointer to something opened in this
> session. Where a number could not be found it is marked **UNVERIFIED** with the command that would
> produce it. No threshold is proposed anywhere in this document: conditions (a)/(b)/(c), the
> verdict domain and the estimators are already committed at `23a830c` and are quoted, never
> re-authored.

---

## Summary

Three things dominate the plan, and only one of them is the mechanism.

**First, the mechanism is genuinely open and genuinely cheap.** A full adapter retrain is **80–82 s**
measured (`results/phase17_training_run.log:19,39,58`; the Phase 14 `real` arm's own bins→provenance
window is 11:27:48Z→11:29:09Z = **81 s**, `results/phase14_teaching_run.log:10,16`, and that window
already contains two full `masked_perplexity` sweeps). At that price the phase can afford to run
**more than one mechanism and report both honestly**, which is a stronger result than betting the
phase on one. Two mechanisms are near-free (ΔW rank-1 component ablation on the adapter: seconds, no
training; retrain-without-the-fact: 81 s) and two more are cheap (retain-set continued fine-tuning;
Fisher-anchored damping over the LoRA parameters, which works with **zero changes** to
`continual/fisher.py` and `continual/ewc.py` — verified by running it this session).

**Second, condition (c) is already failed by the pre-erasure model, and nobody has noticed.** The
committed cap is `V20_MASKED_DIALOGUE_VAL_PPL + 2 × dialogue_ppl_noise_floor`
(`scripts/erasure_gate.py:245`). The *taught* adapter's masked dialogue-val PPL is **5.8154**
(`results/phase14_recall_report.md:462`, +27.16% over 270,203 scored targets). The only dialogue
noise floor this repository has ever measured is **Δ_dialog = 0.001704**
(`results/finetune_smoke_report.md:56`), which puts the cap at **4.576708** — the taught adapter
exceeds it by **1.2387** *before any erasure happens*. Run through the committed gate, a *perfect*
erasure (0 successes, zero non-target damage) returns **FAILURE** on (c) alone. Measured this
session:

```
(a) target upper bound 0.1723 over 13 questions <= calibrated floor 0.2000
(b) worst non-target degradation 0.000000 <= k=2 x 0.050000 = 0.100000
(c) dialogue PPL 5.8154 vs cap 4.5767; retention PPL 3.950000 vs cap 4.029000
-> FAILURE
```

The rule cannot be amended. What *is* open — and is the one free parameter (c) has — is
`dialogue_ppl_noise_floor`, a **required keyword argument with no committed default**
(`scripts/erasure_gate.py:208`). It is therefore a threshold-shaped quantity that must be
pre-registered like one, measured before the erasure runs, and published whichever way it lands.
Additionally, **retention PPL of the adapted model has never been measured in this repository at
all** — `retention_perplexity` has exactly four call sites and none of them is on a LoRA-adapted
model (verified by grep, listed in §Q4).

**Third, `scripts/phase18_extraction.py` is permanently uneditable.** `test_phase18_prereg_is_frozen_before_every_phase18_result`
(`tests/test_phase16_prereg.py:231-312`) requires **every** commit touching that file to be a git
ancestor of the first-add of **every** `results/phase18_*` artifact. The last such commit is
`99716e0` (2026-08-16 11:55:09); the earliest artifact first-add is `2d7151e` (2026-08-16 11:57:58).
A new commit to that file goes RED immediately. Phase 19 must therefore **import** Phase 18's
instruments and write its own arm runner — `run_arm` cannot be widened, even additively. By
contrast `scripts/phase16_persistence.py` **is** editable and was already widened by Phase 18
(`1161593`, 2026-08-15, "widen holm with an additive keyword-only family="), *after*
`results/phase16_persistence_report.md` landed (`e9b921a`, 2026-08-14) — so it remains the D-16
"import, widen, never copy" surface for shared statistics.

**Primary recommendation:** plan for **two mechanisms** (ΔW rank-1 component ablation as the
primary, ERASE-02 retrain-without-the-fact as both gold-standard comparator *and* second mechanism),
pre-register **three** numbers before anything is erased — the (a) floor, the (b) same-run recall
noise floor, and the (c) dialogue-PPL noise floor — in a `scripts/phase19_erasure.py` frozen by a
new ancestry guard, and budget for the honest possibility that the published verdict is **FAILURE on
(c) for a reason that predates the erasure**. Say that out loud in the report; it is a real finding
about LoRA at this capacity, not an embarrassment.

---

## Architectural Responsibility Map

Tiers here are repository layers, since this is a single-process offline ML phase with no client,
CDN or network surface.

| Capability | Primary owner | Secondary | Rationale |
|---|---|---|---|
| Erasure mechanism (weight surgery / training) | new `scripts/phase19_erasure.py` | `src/personacore/lora/*`, `training/loop.py` | Drivers own experiment logic; `src/` stays a reusable library (project layout, `CLAUDE.md` §Project Structure) |
| Post-erasure recall scoring | new Phase 19 arm runner | imports from `scripts/phase18_extraction.py` (read-only) | The pin forbids editing Phase 18's driver; import is free |
| Teacher-forced NLL / exposure | `scripts/phase18_extraction.py` (imported) | — | `measure_exposure` is pure w.r.t. fact material and already parameterised on `taught_value` (`:1361-1447`) |
| Statistics (Wilson, bootstrap, sign test, Holm) | `scripts/erasure_gate.py` + `scripts/phase16_persistence.py` | — | `erasure_gate` is import-only; `phase16_persistence` is the widenable shared instrument |
| Capability measurement (dialogue / retention PPL) | `src/personacore/evaluation/perplexity.py` (imported) | `phase14_recall.run_collapse_control` | The frozen gate metric; a bespoke score would be a second unvalidated metric |
| Verdict | `scripts/erasure_gate.erasure_succeeded` | — | Unamendable; called, never re-implemented |
| Ordering enforcement | `tests/test_phase16_prereg.py` | CI (`fetch-depth: 0`) | The only ancestry-guard file in the repo (verified: `grep -rln "merge-base" tests/ scripts/` → one file) |

---

## Phase Requirements

| ID | Description (from `REQUIREMENTS.md:165-173`) | Research support |
|---|---|---|
| **ERASE-01** | Selective erasure of a taught fact from the weights; goal framing fixed as *auditable forgetting with a measurable bound plus representational consistency reported honestly*; **no mechanism, schedule or design committed** | §Q1 (mechanism survey + recommendation), §Q2 (the (a) floor procedure), §Q3 (instrument reuse), §Q4 (the (c) measurements), §Q6 (ordering), §Q7 (failure modes) |
| **ERASE-02** | TOFU-style retrain-without-the-forget-fact reference; "~81 s per adapter on this M3" | §Q5 — **81 s VERIFIED** three independent ways; the retrain is a one-line `arm_spec` change and is simultaneously a mechanism and a comparator |

Cross-cutting: **STAT-01..06** (`REQUIREMENTS.md:25-45`) apply per-phase. STAT-04 (zero new runtime
dependencies) is test-enforced by a `pyproject.toml` sha256 pin in `tests/test_package.py`
(`STATE.md:173`). STAT-06 forbids gating anything resting on n=8 facts or n=3 personas.

---

## (i) Already committed and UNAMENDABLE

These are quoted, not re-derived. Nothing in the plan may contradict them.

| Item | Location | Value |
|---|---|---|
| The decision rule (5 clauses) | `scripts/erasure_gate.py:95-127` | precondition + (a)/(b)/(c) + descriptive-not-gated + verdict domain |
| Goal framing | `scripts/erasure_gate.py:130-134` | "Auditable forgetting with a measurable bound … **NOT** 'indistinguishable from never-having-learned'" |
| Verdict domain | `scripts/erasure_gate.py:136` | `("SUCCESS", "FAILURE", "INCONCLUSIVE")` |
| Estimator for (a) | `scripts/erasure_gate.py:139-158` | one-sided 95% **Wilson upper** bound, `n` = **questions** |
| `3/n` companion at zero | `scripts/erasure_gate.py:161-170` | reported alongside Wilson, never instead |
| Margin discipline | `scripts/erasure_gate.py:86` | `MARGIN_K = 2` |
| Published v2.0 baselines | `scripts/erasure_gate.py:75-81` | 4.5733 / 3.891140 / 0.068930 / 0.4921 / 0.3483 / 0(of 2430) |
| Precondition already satisfied | `ROADMAP.md:492-495`, `18-VERIFICATION.md:84-88` | `erasure_is_worth_attempting(92,104,0,104) → True`, lower bound 0.8231 vs base 0.0000 |
| PREREG-01/02 | `REQUIREMENTS.md:147-154` | `23a830c` (2026-08-12 16:27:43 -0300, verified by `git log -1`) precedes every v3.0 artifact, test-enforced by ancestry |
| Phase 18's driver | `tests/test_phase16_prereg.py:231-312` | **frozen** — see §Q6 |
| Phase 17's gate constants | `tests/test_phase16_prereg.py:146-228` | **frozen** at `d549e0b` (`STATE.md:241`) |

**The three constants that do NOT exist and that `erasure_succeeded` requires**
(`scripts/erasure_gate.py:200-211`, all keyword-only):

| Argument | Status | Who must produce it |
|---|---|---|
| `target_floor` | does not exist **by design** — the pre-registration fixes the *procedure*, not the constant (`:104-106`) | Phase 19, blind, before the target is scored (§Q2) |
| `nontarget_noise_floor` | does not exist — "measured in the **SAME** run" (`:107-110`) | Phase 19, in-run (§Q4) |
| `dialogue_ppl_noise_floor` | does not exist for the adapter regime; only a full-FT number exists (`results/finetune_smoke_report.md:56`) | Phase 19, pre-registered (§Q4) — **the task nobody notices is missing** |

---

## Q1 — THE MECHANISM (primary; genuinely open)

### The object being operated on

`LoRALinear` (`src/personacore/lora/layer.py:21-42`) computes
`y = base(x) + scale · (x @ A^T @ B^T)`, i.e. `ΔW = scale · (B @ A)` with `B: (out, r)`,
`A: (r, in)`, `scale = alpha/r` fixed at `__init__` (`:27`). Production config is `r=8, alpha=16.0`
(`src/personacore/lora/config.py:23-24`), six named projections per block over six blocks =
**36 wrapped projections** (`results/phase14_teaching_run.log:12`), **331,776** trainable parameters
(same line; census formula `r·n_layer·18·n_embd` asserted at `scripts/teach_persona.py:627`).

**36 × r=8 = 288 rank-1 components.** That number is the mechanism space: `ΔW` is exactly a sum of
288 rank-1 outer products, each addressable by `(layer, projection, j)`. Anything that stays inside
that decomposition remains exactly representable in the shipped artifact format
(`export_adapter`, `src/personacore/checkpoint.py:196`) and passes `load_adapter_weights`' key,
shape and scale audits unchanged (`src/personacore/lora/inject.py:76-131`). Anything that leaves it
does not.

### Option comparison

| # | Mechanism | Cost on this M3 | Effect on (b) non-target | Effect on (c) capability | Catastrophic failure | Falsified by | New code |
|---|---|---|---|---|---|---|---|
| **M1** | **ΔW rank-1 component ablation** — zero or damp a selected subset of the 288 `B[:,j]·A[j,:]` terms, selected by their contribution to the target's teacher-forced value-span NLL | **seconds**; selection = 288 forward passes on a ~10-token span (`span_nll_from_ids`, `:1050`) ≈ under a minute | Directly measurable; components are shared across facts, so collateral is the *expected* risk, not a surprise | Small if few components are touched; must be measured | Components are shared → ablating enough to kill the target kills everything (the "any perturbation destroys it" failure, §Q7) | Post-ablation target recall ≥ floor, or (b) blown | ~80 lines, no training loop, no core change |
| **M2** | **Retrain without the target fact** (ERASE-02) — `arm_spec` with `LOCKED_FACTS` minus one | **81 s** (measured) | Structurally clean: the other 7 facts are trained exactly as before, only the data order shifts | Same recipe → dialogue PPL should land near 5.8154; measurable | None; this is the reference | Post-retrain target recall ≥ floor (would mean the fact leaks from *nothing*) | ~15 lines: a fact-subset arm + a `prefix=` (both already parameters, `teach_persona.py:426`) |
| **M3** | **Retain-set continued fine-tuning** — load the taught adapter, continue `train()` on a bin holding only the 7 non-target facts | 81 s-scale (fewer steps) | Should be protective by construction | Same regime as teaching | Retain-set FT does not *remove*; it dilutes. Known-shallow in the literature (see Sources) | Target recall stays above the floor while non-targets are fine | ~40 lines: load adapter into an injected model, then `train()` (`training/loop.py:172`) |
| **M4** | **Fisher-anchored selective damping** — `EWCPenalty(fisher_over_lora, theta_star=taught_adapter, lam, device)` as `penalty_fn`, combined with an ascent or retain objective | Fisher over the teaching bin: N=2000 examples measured "<1 min on MPS at 18.6 ms/example" (`scripts/estimate_fisher_tinystories.py:54`) | Anchor is exactly the "preserve the rest" mechanism | Anchors toward the taught adapter, so (c) does not get *worse*, but also does not improve | Anchor pulls the target back; net no-op | Target recall unchanged after damping | See the verified note below |
| **M5** | **Task-arithmetic negation** — train a target-only adapter (81 s), subtract its `ΔW` from the taught `ΔW` | 81 s + seconds | Unknown; subtraction is not localised | Unknown | The difference is **not rank-8** and cannot be written back into an `r=8` artifact without SVD truncation; merging into base weights would destroy the adapter-off bit-identity control (`phase14_recall.run_bit_identity_control:1480`, max abs diff exactly 0.0, `STATE.md:142`) | Post-negation recall unchanged, or (c) blown | ~60 lines + an SVD-to-rank-8 refactorisation (CPU; MPS SVD support **UNVERIFIED**) |
| **M6** | **Gradient ascent on the forget set** (TOFU's simplest baseline) | 81 s-scale | Known to damage the retain set — TOFU's own finding is that retain-aware variants beat plain ascent | Known to degrade | Divergence: ascent on CE is unbounded above | Loss explodes / (c) fails | **Cannot use `train()`**: `penalty_fn(model)` receives only the model, never the batch (`training/loop.py:159`), and `assemble_loss` only *adds* (`training/loss.py:17-28`). Needs a bespoke ~60-line loop |

**Verified this session (M4's enabling fact, and its trap).** `estimate_fisher`
(`src/personacore/continual/fisher.py:63`) iterates `model.named_parameters()` with **no
`requires_grad` filter** (`:101-103`) and calls `torch.autograd.grad(loss, params)` (`:118`). Run
against a LoRA-injected model:

- with `mark_only_lora_trainable(model)` → **`RuntimeError: One of the differentiated Tensors does not require grad`**
- **without** it → **succeeds**, returning 32 keys of which 12 are `lora_A`/`lora_B` on a toy config
  (`blocks.0.attn.q_proj.lora_A`, …)

So a Fisher over the adapter parameters is obtainable with **zero changes** to `continual/fisher.py`,
provided the driver injects LoRA and estimates Fisher *before* marking trainability, then filters the
returned dict to `lora_` keys. `EWCPenalty` (`src/personacore/continual/ewc.py:33-81`) then accepts
that filtered dict directly — its only requirements are matching key sets and shapes against
`model.named_parameters()` (`:37-52`, `:61-75`).

This does **not** contradict `teach_persona.py:668-677`, which explains why `penalty_fn=None` there:
that argument is about the *existing* `checkpoints/fisher_tinystories.pt`, whose keys are
vanilla-GPT names that the `.base.` infix breaks, and about the base weights being frozen so the
anchor has zero gradient. A **freshly estimated Fisher over the `lora_` keys** is a different object
and is not covered by either reason. Note two honest limits: `estimate_fisher` has **no mask
support** (it scores every token of every window, including user turns), and the teaching bin is
tiny (`data/persona_real_train.bin` = 40,072 bytes = 20,036 `uint16` tokens, verified by `ls`), so
windows at `block_size=256` overlap heavily.

### Recommendation

**Run M1 and M2. Report both.**

- **M1 (ΔW rank-1 ablation) as the primary mechanism.** It is the only option that is (a) genuinely
  *selective* rather than "train differently", (b) exactly representable in the shipped artifact,
  (c) cheap enough that a per-component search is affordable, and (d) uses the *already committed*
  teacher-forced NLL instrument as its objective, which is the same instrument the verdict's
  `zero_results_have_nll` clause depends on. Its selection signal and its evidence are the same
  measurement, which is unusually clean.
- **M2 (retrain-without) as the reference arm required by ERASE-02**, which doubles as a second
  mechanism at 81 s. Reporting "the surgical mechanism achieved X, the retrain reference achieved Y"
  is a stronger, more falsifiable result than either alone, and ERASE-02 obliges the plan to either
  run it or state in writing why not (`ROADMAP.md:542-544`).
- **M4 as a documented option, not a commitment.** Cheap and reusable, but it is a *preservation*
  mechanism and needs a forgetting objective beside it (M3 or M6) to do anything. If the plan has
  budget for a third arm, M3+M4 together is the closest thing here to TOFU's "gradient difference".
- **M5 and M6 are recommended against.** M5 breaks the artifact's rank and threatens the
  bit-identity control that the entire memory-ON/OFF demo claim rests on. M6 needs a bespoke
  training loop, is the literature's known-worst baseline, and buys nothing M1/M2 do not.

**Do not adopt any numeric threshold from TOFU or WMDP** — the pre-registration rejects that
explicitly and states why (`scripts/erasure_gate.py:24-27`), and `REQUIREMENTS.md:186-188` puts it
Out of Scope. The papers below are cited as **method sources only**.

---

## Q2 — THE BLIND CALIBRATION PROCEDURE for (a)'s floor

### What Phase 14 actually did — mechanics, in commit order (all verified by `git log`)

| Step | Commit | Time | What landed |
|---|---|---|---|
| 1. Rule, blind | `d7d7917` | 2026-08-02 01:52:08 | `CALIBRATION_DECISION_RULE` + `lock_thresholds` + `THRESHOLD_DISCOUNT = 0.60` + `THRESHOLD_FLOOR = 0.20` (`scripts/teach_persona.py:771-831`). Commit message: *"commit CALIBRATION_DECISION_RULE before any calibration number exists"* |
| 2. Calibration run | **`0425fdc`** | 2026-08-02 03:37:12 | Three calibration arms trained + scored; `results/phase14_calibration_report.md` + `phase14_calibration_results.json` added. **This is `CALIBRATION_SHA`** (`scripts/phase14_recall.py:197`) |
| 3. Lock the constants | `921a6bc` | 2026-08-02 07:58:13 | `TAUGHT_THRESHOLD = 0.2486`, `HELDOUT_THRESHOLD = 0.2000`, `CALIBRATION_SHA` pinned into `phase14_recall.py:188-197`; ADAPT verdict recorded; **arm corrected** from `cal_first_person` to `cal_first_person_replay` |
| 4. Train the target | `f93b502` | 2026-08-02 08:29:53 | `teach_persona.py real` — the adapter under test |
| 5. Score the target | `043bf4d` | 2026-08-02 09:15:09 | `results/phase14_recall_report.md` — "both gates PASS" |

**What was held out.** `CALIBRATION_POOL` — 10 core facts across the same 8 slots as the real set,
disjoint from `CANDIDATE_POOL` by construction (`scripts/phase14_factset.py:98-113`). The pool
passed the *same* guessability gate as the real pool ("a calibration set with guessable facts
produces an inflated, meaningless ceiling", `:98-101`) and mirrors the real set's slot mix so the
ceiling is commensurable (`:101-102`).

**What was scored.** The calibration adapter (`checkpoints/phase14_cal_first_person_replay_adapter.pt`,
on disk) through **the same loader** the real run uses —
`phase14_recall.load_adapted_model(device, adapter_path=…)`, whose `adapter_path` parameter exists
for exactly this reason: *"the calibration numbers that lock this file's thresholds must come off the
same load-before-inject `weights_only=True` path as the real run, or the threshold is derived from a
different pipeline than the one it gates"* (`scripts/phase14_recall.py:513-521`).

**The rule.** `max(THRESHOLD_FLOOR, round(rate × THRESHOLD_DISCOUNT, 4))`
(`scripts/teach_persona.py:828-831`). Inputs: `cal_taught_rate = 0.4143 (522/1260)`,
`cal_heldout_rate = 0.2506 (203/810)`; the discount bound taught (0.2486), the floor bound held-out
(0.6 × 0.2506 = 0.1504 → clamped to 0.2000) (`scripts/phase14_recall.py:169-176`). Boundary is `>=`
— exactly on the threshold **passes** (`:200-218`, pinned by `tests/test_phase14_scoring.py:115-143`).

**What made it blind rather than merely unseen.** Four things, all structural:
1. The **rule function** was committed 1h45m before the calibration produced a number, and git order
   is the proof (`scripts/teach_persona.py:760-762` names the `git log -S` query that shows it).
2. The **fact set was disjoint and disposable**, so its measured rate is a *ceiling estimate*, never
   a target (`scripts/phase14_recall.py:185-187`).
3. The **discount** exists precisely so the number cannot be "chosen to be cleared"
   (`scripts/teach_persona.py:773-776`).
4. `CALIBRATION_SHA` points at the **evidence** commit, not a verdict commit, so any reader can
   re-derive the constants from committed inputs (`scripts/phase14_recall.py:191-197`).

One honest wrinkle worth carrying forward: at step 3 the *arm* feeding `lock_thresholds` was
changed (no-replay → replay) after the calibration was visible. The project treated it as a wiring
correction and published **both** threshold pairs side by side in the report so the narrowing is
independently checkable (`scripts/phase14_recall.py:178-183`). That is the standard for any
analogous Phase 19 correction.

### The analogous Phase 19 procedure

**Good news the brief did not assume: `n=8` is not the constraint here.** The (a) floor does *not*
need a split of the 8 taught facts. Four committed, gate-cleared, disjoint fact sets already exist:

| Pool | Size | Location |
|---|---|---|
| `CALIBRATION_POOL` | 10 core, 8 slots | `scripts/phase14_factset.py:102-113` |
| `REGISTER_ARM_POOL` | 6 core | `:117-124` |
| `GATE_REJECTED_CANDIDATES` | 12 (8 core trims + 4 soft) | `:429-444` |
| Phase 17 minted values | 24 (3 per core slot) | `scripts/phase17_persona_facts.py`, gate-cleared 24/24 over 416 completions (`STATE.md:222`) |

So the procedure is:

1. **Commit the floor-derivation rule blind** — a pure function `lock_erasure_floor(...)` in
   `scripts/phase19_erasure.py`, plus its inputs and its boundary semantics, before any Phase 19
   number exists. This is the `d7d7917` analogue and it is what the pre-registration actually
   demands: *"the procedure and the estimator are what this rule fixes; the constant is produced by
   that procedure, blind"* (`scripts/erasure_gate.py:104-106`).
2. **Teach a calibration adapter on `CALIBRATION_POOL`** — or reuse the committed
   `checkpoints/phase14_cal_first_person_replay_adapter.pt`. (Reuse is free but that adapter was
   trained on the `real` arm's *replay* configuration and its recall was measured by
   `score_items`, not by the Phase 18 adversary — see the commensurability warning below. A fresh
   81 s retrain under Phase 19's own recipe is cheaper than the argument.)
3. **Apply the chosen mechanism to one calibration fact**, exactly as it will be applied to the target.
4. **Score post-erasure recall of that calibration fact with the same adversary at the same budget
   that will score the target**, and feed the measured rate through the committed rule.
5. **Commit the resulting constant** — this is the `0425fdc` + `921a6bc` pair — *before* the target
   is erased or scored.

**The hard commensurability constraint, stated plainly.** The floor caps a number produced by the
A2 adversary at K=48 (`scripts/phase18_extraction.py:93,146`). If the floor is derived from a
9-draw direct-question sweep (`score_items`, `scripts/teach_persona.py:1050`), the two are not the
same quantity and the gate means nothing. **The floor must be measured by the same adversary at the
same budget as the target.** This is a real build item, because
`phase18_extraction.build_corpus` reads only `results/phase16_recall_sample.json` and
`factset.LOCKED_FACTS` (`:864-866`), and it **cannot be widened** (the pin). Phase 19 must build its
own corpus builder over calibration facts, reusing `apply_a1`/`build_a2_prompt`/`build_a3_prompt`
and `split_value_ids` **by import** (`:474,545,594,640`).

**Where n=8 genuinely does bite: the denominator.** The binding fixture gives each core fact exactly
**13** held-out and **14** taught questions (`scripts/phase16_persistence.py:290`; re-derived this
session from `results/phase16_recall_sample.json` — 13 per fact × 8 facts = 104, 14 × 8 = 112).
Computed with the committed `wilson_upper_bound`:

| n (questions) | Wilson upper at 0 successes | `3/n` |
|---|---|---|
| 13 (target, held-out tier only) | **0.172267** | 0.230769 |
| 14 (target, taught tier only) | 0.161955 | 0.214286 |
| 27 (target, both tiers) | 0.091079 | 0.111111 |
| 52 (13 × 4 attack families) | 0.049456 | 0.057692 |
| 108 (27 × 4 families) | 0.024439 | 0.027778 |

**A perfect erasure at n=13 cannot produce an upper bound below 0.1723.** The floor must therefore
sit at or above that for (a) to be clearable at all on the gated tier alone. This is arithmetic, not
opinion, and it is the single most consequential planning fact after §Q4. Two honest ways to widen
the denominator:

- **Pool the two tiers → n=27.** Defensible: the target's taught and held-out questions are both
  questions about the same fact, and the pre-registration's unit is the *question*. Cost: none. It
  does mix a tier Phase 18 kept separate for its own Holm pricing, which must be declared.
- **Count each (question, family) pair → n=52 or 108.** **Recommended against.** Four phrasings of
  one question are clustered exactly the way nine draws of one question are, and inflating `n` by 4
  reintroduces the modelling error STAT-01 exists to forbid, one level up. The conservative reading
  — a question counts once if **any** family extracted it at least once — keeps `n` at 13 or 27 and
  makes the adversary maximally strong, which is the correct direction for a privacy claim
  (`LOWER_BOUND_SENTENCE`, `scripts/phase18_extraction.py:1744`).

---

## Q3 — INSTRUMENT REUSE (do not rebuild)

### Hard constraint discovered: Phase 18's driver is frozen

Verified this session:

```
last commit touching scripts/phase18_extraction.py : 99716e0  2026-08-16 11:55:09
earliest results/phase18_* first-add               : 2d7151e  2026-08-16 11:57:58
```

`tests/test_phase16_prereg.py:273-294` requires **every** commit touching the pin to be an ancestor
of **every** artifact's first-add. A new commit to that file is not an ancestor of any of them → the
guard goes RED. The file's own docstring states the intent: *"After the pin, changing a template is
a reviewed, dated commit that reddens the ancestry guard, and that cost is the whole point"*
(`scripts/phase18_extraction.py:11-13`).

**Consequence for the plan:** Phase 19 imports Phase 18, never edits it. Importing is safe — nothing
executes at import beyond a `sys.path` bootstrap and one reachability proof (`:16-19`,
`:39-53`), and the module holds no fact strings at import time by the LAZY-IMPORT RULE (`:21-28`).
Shared *statistics* that genuinely need widening go into `scripts/phase16_persistence.py`, which is
not frozen (Phase 18 widened it at `1161593`, 2026-08-15, after Phase 16's artifacts landed on
2026-08-14).

### The reuse map

| Need | Import | Signature / how to call | Notes |
|---|---|---|---|
| Teacher-forced span NLL | `phase18_extraction.span_nll_from_ids` (`:1050`) | `(model, context_ids, value_ids, device) -> {n_scored, nll_sum, nll_mean}` | One forward, both reductions; asserts `n_scored == len(value_ids)` (`:1097-1102`) |
| Value NLL under a named frame | `.value_span_nll` (`:1110`) | `(model, tok, device, *, slot, value, frame)`; `frame ∈ ("ans1","f4_reversed","f3_bare")` (`:981`) | `value` is a **parameter**, never a lookup (`:1117`) — so it works on any value, including calibration facts |
| Same-slot reference set | `.reference_set_for` (`:1159`) | `(slot) -> tuple`, asserts `6 ≤ |R| ≤ 8` (`:1210-1215`) | Requires the slot to carry a *taught* fact (`:1185-1190`) — **a calibration slot will raise**; §"must build" below |
| Carlini exposure rank | `.exposure_rank` (`:1230`) | `(nll_by_candidate, *, taught_value, reduction, length_spread)`; pure, CPU-testable | `log2(|R|) − log2(rank)`; ties broken on the candidate string (`:1235-1236`) |
| Full exposure record | `.measure_exposure` (`:1361`) | `(model, tok, device, *, slot, taught_value) -> 11-key record` (`:1317-1329`) | Publishes six NLLs, reads exactly one pair: `ADMISSIBLE_NLL_FRAME="ans1"`, `ADMISSIBLE_NLL_REDUCTION="mean"` (`:985-987`) |
| Spread-0 internal control | `.assert_spread_zero_reductions_agree` (`:1281`) | `(slot, sum_record, mean_record) -> bool` | Applies only to `("birth_year","house_number")` (`:1138`) |
| A1 / A2 / A3 prompt builders | `.apply_a1` (`:474`), `.build_a2_prompt` (`:640`), `.build_a3_prompt` (`:545`), `.split_value_ids` (`:594`), `.injection_budget` (`:565`), `.realized_injection` (`:656`) | — | The A2 budget is `INJECTION_FRACTION = 0.25` (`:117`), realized multiset `[1,1,1,1,1,1,2,2]` (`:3761`) |
| Corpus digest / canonical form | `.canonical_json` (`:746`), `.corpus_sha256` (`:758`) | — | Reuse so a Phase 19 corpus is digested the same way |
| Scoring + ladder + aggregation | `.score_records` (`:1919`), `.asr_ladder` (`:2095`), `.cumulative_by_attempt` (`:2165`), `.aggregate_questions` (`:2223`) | `k=K` default 48 | These consume raw draw records; they are reusable on Phase 19 records with the same schema |
| Question-unit denominator proof | `._handoff_counts` (`:2782`) | `(question_counts, per_fact_by_family, family, arm)` | Proves the denominator against a **derived** question count, never a literal (`:2786-2799`) |
| Best-family rule | `.best_attack_family` (`:2808`) | — | `BEST_ATTACK_RULE` at `:2767`; A2 was selected (`results/phase18_extraction_report.md:240`) |
| Clean-room guard | `phase14_recall.assert_no_value_in_prompt` (`:398`) | `(tok, question, values, *, prompt_ids=None)` | Substring **and** contiguous-id-run, ANDed (`:428-438`); `prompt_ids=` is the D-03 widening that checks the ids actually dispatched |
| Its positive twin | `.assert_value_in_prompt` (`:441`) | `(tok, prompt_ids, values)` | Detectors **OR**ed; the polarity asymmetry is measured, 54 of 216 prompts (`:463-470`) |
| Value scoring predicate | `.contains_value` (`:300`), `.score_question` (`:315`), `.normalize` (`:279`) | — | Substring, whitespace-collapsed; deliberately not id-subsequence (`:302-311`) |
| Adapter loading (parameterised) | `.load_adapted_model` (`:513`) | `(device, adapter_path=None)` | **Already takes the adapter path** — an erased adapter loads through the identical path |
| Dialogue-PPL collapse control | `.run_collapse_control` (`:1383`) | `(model, tok, device, forbid, values)` → on/off PPL pair + delta + transcripts | Asserts identical denominators (`:1442-1446`) |
| Bit-identity control | `.run_bit_identity_control` (`:1480`) | | Measured max abs diff exactly 0.0 on real weights (`STATE.md:142`) |
| Pairing / stats | `phase16_persistence.aggregate_by_fact` (`:779`), `.cluster_bootstrap` (`:843`), `.sign_test_exact` (`:1088`), `.holm` (`:1170`), `.HOLM_ALPHA` (`:1005`), `.SIGN_TEST_N` (`:1016`), `.report_proportion` (`:930`), `.resolve_forbid`/`.forbid_digest` (`:180,191`) | — | `report_proportion` already imports `erasure_gate.wilson_upper_bound` rather than re-deriving (`:941`) |
| Binding fixture | `results/phase16_recall_sample.json` | 270 questions: `core_taught` 112 / `core_held_out` 104 / `soft` 54; row keys `seed_index, fact_id, question, reserved` | Pinned by `tests/test_phase16_fixture_regen.py` (`STATE.md:111`) |

### What has to be recorded so `zero_results_have_nll` can be True

`erasure_succeeded` short-circuits to **INCONCLUSIVE** when `target_successes == 0` and
`zero_results_have_nll` is False (`scripts/erasure_gate.py:223-227`) — *"cannot distinguish 'the
fact is absent' from 'the probe was too weak'"*. **A successful erasure produces exactly that zero.**
So the NLL instrument is what stands between a real success and an unpublishable INCONCLUSIVE.

Concretely, for the post-erasure model, record — per slot, at minimum for the **target** slot and
recommended for **all eight**:

1. All **six** `frame × reduction` NLLs of the target value (`measure_exposure` emits them as a
   required nested dict, `:1432-1438`), with the admissible pair `("ans1","mean")` named in the
   record (`:1428`).
2. The **rank** of the target value among its same-slot reference set `R`, plus `exposure_bits`,
   `ceiling_bits`, `n_references`, `length_spread`, `spread_zero_control` — the full
   `EXPOSURE_RECORD_KEYS` tuple (`:1317-1329`), which `_exposure_record` enforces as an **ordered
   hard equality** (`:1344-1358`), so a dropped field is red at the commit that writes it.
3. The **same record for the pre-erasure adapter**, so the movement is a paired delta rather than an
   absolute number read against nothing. Phase 18's adapter-on values are already published
   (`results/phase18_extraction_report.md:145-154`): every one of the eight slots is at **rank 1**,
   exposure = ceiling, with `ans1/mean` from **0.1337** (`pet_name`) to **3.1255** (`hometown`).
   A post-erasure rank that moves off 1 with a risen `ans1/mean`, on the target slot only, while the
   other seven stay at rank 1, is the strongest evidence this phase can produce.
4. Measured **in the same pass and under the same gate state as the draws** — Phase 18 does exactly
   this inside the generation context manager (`:3696-3702`) with the stated reason: measuring it in
   a second process would make "absent" and "weak" separable only across two loads.
5. Every value **finite** — Phase 18's verifier confirmed 48 finite NLLs per arm, 0 `None`, 0 NaN
   (`18-VERIFICATION.md:60`). Same bar.

**Blocker to build around:** `reference_set_for` raises when the slot carries no taught fact
(`:1185-1190`). For the calibration-fact floor run (§Q2) the reference set must be assembled by a
Phase 19 twin — a ~20-line function following the same shape, with the same `6 ≤ |R| ≤ 8` proof, and
importing the same pools. It cannot be a widening of the Phase 18 function.

---

## Q4 — CONDITION (c)'s MEASUREMENTS AND THEIR NOISE FLOORS

### (c) as committed

```python
dialogue_cap  = V20_MASKED_DIALOGUE_VAL_PPL + MARGIN_K * dialogue_ppl_noise_floor   # :245
retention_cap = V20_EWC_RETENTION_PPL       + MARGIN_K * V20_RETENTION_NOISE_FLOOR  # :246
c_ok = dialogue_ppl <= dialogue_cap and retention_ppl <= retention_cap              # :247
```

`retention_cap` is **fully determined**: `3.891140 + 2 × 0.068930 = 4.029000` (computed this session).
`dialogue_cap` depends on the one argument the rule left open.

### Where each number is produced today

| Quantity | Instrument | Call sites | Adapted-model measurement exists? |
|---|---|---|---|
| Masked dialogue val PPL | `masked_perplexity` (`src/personacore/evaluation/perplexity.py:83`) over `data/dialog_val.bin` + `dialog_val_mask.bin`, block 256, `forbid_ids` on | `finetune_dialog.py:203,214`; `finetune_ab.py:235,246`; `finetune_smoke.py:294,332`; `make_transcripts.py:118`; **`phase14_recall.run_collapse_control:1435,1439`**; **`teach_persona.train_arm:717,721`** | **YES** — 4.5733 (off) → **5.8154** (on), +27.16% over 270,203 scored targets (`results/phase14_recall_report.md:462`). The teaching run's own unmasked-instrument twin reads 4.5737 / 5.8176 (`results/phase14_teaching_run.log:15`); the ~0.008% divergence is the documented WR-01 note |
| Retention PPL | `retention_perplexity` (`perplexity.py:148`) over `data/retention_val.bin` (2,000,572 B = 1,000,286 `uint16` tokens, on disk) | `build_retention_bin.py:145,151`; `finetune_dialog.py:206`; `finetune_ab.py:238`; `finetune_smoke.py:299,335` | **NO — never measured on a LoRA-adapted model.** Verified by exhaustive grep of `scripts/` and `src/`: no call site is in `phase14_recall.py`, `teach_persona.py`, or any Phase 16/17/18 driver |

The v2.0 baseline 3.891140 is the Phase 12/13 production-trajectory endpoint —
`results/finetune_prod.csv` final row (step 4000) reads
`4.573349214207799` dialogue and `3.891139975617828` retention, i.e. both of `erasure_gate`'s
baselines come off the same committed row.

### Has the dialogue-PPL noise floor ever been measured here?

**Yes — but for a different regime, and it is the wrong size.**

`results/finetune_smoke_report.md:49-57` (Stage 0b, D-05): seed pair **(1337, 2024)**, identical
config (masked arm, LR 9e-05, **1250** steps, full fine-tune):

| Quantity | Seed 1337 | Seed 2024 | Δ (floor) | Margin (K×Δ) |
|---|---|---|---|---|
| end dialogue PPL | 4.470551 | 4.472255 | **0.001704** | 0.003408 |
| end retention PPL | 5.074896 | 5.005966 | **0.068930** | 0.137861 |

The retention half of that single table is what `erasure_gate.py:77` adopts as
`V20_RETENTION_NOISE_FLOOR`, and `scripts/finetune_ab.py:76-85` carries it as `DELTA_RET` with the
regime named. So there is a strong precedent argument for adopting **Δ_dialog = 0.001704** as
`dialogue_ppl_noise_floor` by the same logic — the two numbers are two cells of one measurement.

**And that is exactly what makes (c) unpassable.** Computed this session:

| | |
|---|---|
| dialogue cap at Δ_dialog = 0.001704 | **4.576708** |
| pre-erasure adapter-on dialogue PPL | **5.8154** |
| excess, before any erasure | **+1.2387** |
| noise floor that would be required to admit 5.8154 | **0.62105** |

Run through the committed gate with a *perfect* erasure — 0 successes, zero non-target degradation,
retention comfortably under cap — the verdict is **FAILURE**, on (c) alone, for a reason that has
nothing to do with the erasure.

### The four honest responses (an open decision, §Open decisions D3)

1. **Adopt Δ_dialog = 0.001704, measure, publish FAILURE.** Fully defensible and fully honest: it
   says the conversational cost was paid at *teaching* time (+27.16%, already published as a named
   limitation, `results/phase14_recall_report.md:585`), and that at 13.9M parameters (c) as written
   cannot discriminate an erasure. It is a real finding. It is also a headline nobody will enjoy.
2. **Measure a genuine adapter-regime dialogue noise floor, pre-registered.** Two independently
   seeded re-teachings of the *same* fact set under the *same* recipe → `|ΔPPL|`. Cost: **~3 minutes**
   (2 × 81 s). This is the closest structural analogue of what Stage 0b did — a seed pair at an
   otherwise-identical config — and it is the *right* floor for the regime the number is being read
   in. **Recommended, regardless of which way it lands.** It must be pre-registered like a
   threshold: the estimator, the seed pair, and the arm config committed before it runs, because a
   noise floor chosen after seeing whether it clears the cap is precisely the failure mode `23a830c`
   exists to prevent. Whether a same-recipe seed spread reaches 0.62105 is **UNVERIFIED** — the only
   adjacent evidence is Phase 17's three *different-persona, no-replay* adapters spanning
   14.2507–15.6121 (`results/phase17_personas_report.md:761`), which is not the same quantity.
3. **Measure `dialogue_ppl` with the adapter off.** **Do not.** `adapter_disabled` is measured
   bit-identical to the un-adapted base at max abs diff exactly 0.0 (`STATE.md:142`), so this
   trivially passes while measuring nothing. It is the "green and blind" shape this project names as
   its recurring defect.
4. **Report the pre-erasure value beside the post-erasure value in every table.** Not an
   alternative — a requirement under any of the above. A (c) failure that predates the erasure and a
   (c) failure caused by it are different findings, and the only thing that separates them is
   publishing both numbers.

### What the plan must build for (c)

| Item | Cost | Notes |
|---|---|---|
| Dialogue PPL of the erased model | seconds | `run_collapse_control` (`phase14_recall.py:1383`) already does on/off in one process with a denominator assertion; call it with the erased adapter |
| **Retention PPL of the adapted model — pre- and post-erasure** | seconds to a minute each | `retention_perplexity(model, RETENTION_BIN, 256, device, tok)`; ~3,900 windows at block 256, batch 32. **New call site — this measurement does not exist today.** Requires a live tokenizer (for the dead-id mask) |
| Adapter-regime dialogue noise floor | ~3 min (2 × 81 s) | Option 2 above; pre-registered |
| Same-run recall noise floor for **(b)** | ~30 min | See below |

**(b)'s `nontarget_noise_floor` — also missing, also in-run.** The rule says "the noise floor
measured in the **SAME** run" (`scripts/erasure_gate.py:107-110`). The cheap estimator with a
precedent is a **seed-stride replicate of the scoring** on the unerased adapter — re-score the same
questions with a different `seed_index * K` offset and take the per-fact `|Δrate|`. At A2/K=48 over
104 questions that is 4,992 draws ≈ **30 min** at the measured 172 draws/min
(`results/phase18_extraction_report.md:264` — 42,480 draws in 246.5 min). Phase 17's `REPLICATION_SEEDS`
(`scripts/phase17_personas.py:169-171`) and `phase16_persistence.taught_replication` (`:1254`) are
the register to follow: descriptive, seed-replicated, never a gate. **Note `erasure_succeeded`
returns INCONCLUSIVE if `nontarget_deltas` is empty** (`:253-254`), so per-fact deltas for all seven
non-targets are mandatory, never pooled (`:107-110`, `ROADMAP.md:518-522`).

---

## Q5 — ERASE-02, THE RETRAIN REFERENCE

### The ~81 s figure — VERIFIED three ways

| Source | Measurement |
|---|---|
| `results/phase17_training_run.log:19` | `=== END --train persona_a rc=0 wall=82s ===` |
| `results/phase17_training_run.log:39` | `wall=80s` (persona_b) |
| `results/phase17_training_run.log:58` | `wall=80s` (persona_c) |
| `results/phase14_teaching_run.log:10` → `:16` | bins provenance `11:27:48Z` → run provenance `11:29:09Z` = **81 s**, and that window contains the 200-step train **plus two full `masked_perplexity` sweeps** over 270,203 targets (`:15`) |

The Phase 17 arms are the *lighter* recipe (176 episodes, ~7,500 tokens, `replay_ratio=0.0`); the
Phase 14 `real` arm is 220 episodes / 20,036 tokens at `replay_ratio=1.0`
(`results/phase14_teaching_run.log:7`). Both land at ~81 s. `REQUIREMENTS.md:171-173` is accurate.

### What a retrain reference arm concretely consists of here

**What gets retrained:** a fresh LoRA adapter — 36 wrapped projections, 331,776 parameters, `r=8`,
`alpha=16.0` (`src/personacore/lora/config.py:23-24`).

**From what checkpoint:** `checkpoints/convbase_best.pt`, the frozen conversational base
(`scripts/teach_persona.py:90`), fingerprint `git_sha=04e724c6…, step=4000, val_loss=1.5235939979553224`
(`results/phase14_teaching_run.log:16`). The base is **provably untouched** by teaching — the canary
raises if any frozen base parameter moves (`scripts/teach_persona.py:689-699`).

**With what held out:** `arm_spec` (`scripts/teach_persona.py:405-422`) returns
`(facts, second_person, replay_ratio)`. The `real` arm returns
`fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS` at `REAL_RUN_SECOND_PERSON=False`,
`REAL_RUN_REPLAY_RATIO=1.0` (`:417-421`). The retrain reference is that tuple **minus the target
fact**. `render_episodes(facts, family_ids)` (`:247`) and `build_arm_bins(..., seed=, prefix=)`
(`:425-461`) both already take the fact list as a parameter — Phase 17 threaded `seed=` and
`prefix=` through additively for exactly this class of reuse (`STATE.md:201`). Everything else —
LR 3e-4, weight_decay 0.0, batch 8, 200 steps, warmup 20, seed 1337 (`:511-524`) — stays identical,
or the comparison measures the recipe rather than the omission.

**Compared against what:** three things.
1. The **taught adapter** (`checkpoints/persona_adapter.pt`) — the pre-erasure state.
2. The **mechanism's** erased adapter — the surgical result.
3. The **adapter-off base** — Phase 18's measured 0/104 floor
   (`results/phase18_extraction_report.md:41-44`), which is what "never learned it" actually reads.

**Is it a gold-standard comparator, a mechanism, or both? Both — and the plan should say so.**

- As a **comparator** it is the closest available operationalisation of "what would the model look
  like if it had never learned this fact", which is the framing the pre-registration deliberately
  refuses to *claim* (`scripts/erasure_gate.py:33-36`). Reporting it as a *reference point* is fine;
  reporting the surgical result as *indistinguishable from* it is not, and would violate the goal
  framing. Keep it descriptive.
- As a **mechanism** it is legitimate and honest at 81 s, and REQUIREMENTS.md already anticipates
  this: "it becomes a ~90-second call — so it is a genuine option for Phase 19 rather than an
  aspiration" (`:171-173`).
- Its one real weakness: a retrain is a *different adapter*, not an edited one. Its non-target recall
  will differ from the taught adapter's by seed/data-order noise as well as by the omission — which
  is precisely why the (b) noise floor of §Q4 has to exist before this arm can be interpreted.

**Caveat the plan must carry:** the retrained reference is **not** a clean counterfactual for the
*taught* adapter, because `seed_everything(seed)` owns the data order (`:605-610`) and dropping one
fact changes the number of episodes, hence the batch composition at every step. Two adapters trained
on 7 facts at two seeds bound that noise; one adapter does not.

---

## Q6 — THE ORDERING / PRE-REGISTRATION PLAN

### The guard, named

`tests/test_phase16_prereg.py` — **the only file in the repository containing `merge-base`**
(verified: `grep -rln "merge-base" tests/ scripts/`). It holds three guards:

| Test | Line | Form | What it pins |
|---|---|---|---|
| `test_prereg_commit_precedes_every_v3_results_artifact` | `:85` | **SHA-pinned** to `PREREG_COMMIT = "23a830c…"` (`:49`) | Every `results/phase16_*`, `phase17_*`, `phase18_*` first-add descends from the erasure rule |
| `test_prereg_commit_exists_and_touches_the_erasure_gate` | `:125` | identity | The pin is the real pre-registration, not merely an early commit |
| `test_phase17_prereg_is_frozen_before_every_phase17_result` | `:146` | **derived from history** | *Every* commit touching `scripts/phase17_personas.py` is an ancestor of *every* Phase 17 artifact's first-add |
| `test_phase18_prereg_is_frozen_before_every_phase18_result` | `:231` | derived from history | Same, for `scripts/phase18_extraction.py` |

**The derived-from-history form is the stronger one and is what Phase 19 must use.** Its own
docstring says why: a hand-pinned SHA "only asserts that ONE commit came first: it happily permits a
LATER edit to the pre-registration after the numbers are visible, which is precisely the manoeuvre
STAT-05 exists to forbid" (`:150-156`). Phase 17 chose it deliberately over a SHA pin (`STATE.md:195`).

Three green-and-blind failure modes are closed and must be closed again for Phase 19 (`:19-38`):
shallow clone (asserted, never skipped — CI carries `fetch-depth: 0`), empty match set (`assert
checked`), wrong pinned SHA (identity check).

### The two-file split, and why Phase 19 needs it

Phase 17 split its pre-registration in two: gate constants in `scripts/phase17_personas.py`
(pinned) and the 24 minted values in `scripts/phase17_persona_facts.py` (**deliberately not
pinned**), because ROADMAP SC2's ADAPT branch is a *sanctioned* outcome in which values are replaced
after a report exists, and pinning them "would turn an explicitly planned outcome permanently red"
(`tests/test_phase16_prereg.py:162-171`, `STATE.md:194`). Phase 18 refused the split, because
replacing an attack template after seeing a null is the weakening ATK-03 exists to prevent
(`:238-245`).

**Phase 19 has a sanctioned post-artifact write, so it needs Phase 17's split.** The (a) floor
constant *cannot* exist until the calibration has run and produced a `results/phase19_*` artifact.
If it lives in the pinned rule file, writing it there turns the ancestry guard permanently red. So:

| File | Pinned? | Contents |
|---|---|---|
| `scripts/phase19_erasure.py` | **YES**, derived-from-history | The floor *derivation rule* (a pure function), the mechanism identity and its parameters, the arm names, the (b)/(c) estimator definitions, the seed pair for the dialogue noise floor, the record schemas, the report text, the verdict-rendering path. Committed **before the calibration runs** |
| `scripts/phase19_floor.py` (or equivalent) | **NO** — but guarded by its own ancestry test | The three measured constants: `TARGET_FLOOR`, `NONTARGET_NOISE_FLOOR`, `DIALOGUE_PPL_NOISE_FLOOR`, each with its provenance comment and its evidence SHA — the `CALIBRATION_SHA` pattern (`scripts/phase14_recall.py:191-197`) |

### The commit order the plan must follow

Modelled on Phase 14's verified chain (§Q2) and Phase 18's `smoke → pin → corpus → run → results`
(`tests/test_phase16_prereg.py:246-248`):

```
1. RESEARCH lands                                  (this file)
2. PIN:  scripts/phase19_erasure.py                — rule, estimators, schemas, report text.
                                                     UNAMENDABLE FROM HERE.
   + tests/test_phase16_prereg.py                  — add "results/phase19_*" to V3_ARTIFACT_GLOBS
                                                     (line 54) and add the Phase 19 ancestry twin
3. Calibration corpus + calibration adapter        → results/phase19_cal_corpus.json
4. Calibration erasure + scored run (BLIND)        → results/phase19_calibration_*.json
5. Noise floors: dialogue seed pair, (b) replicate → results/phase19_noise_floors.json
6. LOCK:  scripts/phase19_floor.py                 — the three constants + evidence SHAs.
                                                     Guarded: must precede every target artifact.
7. Erase the TARGET (mechanism M1, and M2 retrain) → checkpoints/phase19_*_adapter.pt
8. Scored post-erasure run + exposure + PPL pair   → results/phase19_arm_*.json
9. Verdict via erasure_gate.erasure_succeeded      → results/phase19_erasure_report.md
```

**The tripwire if someone later edits a pinned file.** `git log --format=%H -- <pinned file>`
returns *every* commit touching it; each is asserted to be an ancestor of *every* tracked artifact's
**earliest** add (`--diff-filter=A`, last entry — "taking the earliest add is what makes a
delete-and-re-add cycle unable to launder the ordering", `:202-204`). A post-hoc edit is not an
ancestor of an artifact committed before it, so `git merge-base --is-ancestor` exits non-zero and
`subprocess.run(..., check=True)` raises. There is no skip path and no force flag. Recovery is a
reviewed, dated commit that leaves the redness visible — which is the point.

**Three more standing guards Phase 19 inherits and must not break:**

- `tests/test_package.py` pins `pyproject.toml` by sha256 read as bytes (`STATE.md:173`) — STAT-04.
  Any new dependency turns it red. Phase 19 adds none.
- `tests/test_phase14_scoring.py:422` `PERSONA_ALLOWLIST` — hard equality over `persona=` call
  sites. A new Phase 19 call site must be added visibly, never by deleting the guard (PERS-06,
  `REQUIREMENTS.md:75-79`).
- `tests/test_phase14_scoring.py:579` `DRAW_ALL_ASSERTED_BY` — every `draw_all` call site must
  assert something in-prompt, in place or via a named indirection whose asserter must exist
  (`STATE.md:178`). A Phase 19 arm runner calling `draw_all` must appear there.
- Report clobber refusals: `assert_extraction_report_not_clobbered`
  (`scripts/phase18_extraction.py:3802`) and `phase16_persistence.assert_persistence_report_not_clobbered`
  (`:2062`) are the register — a recorded verdict is extended by `append_addendum`, never re-rendered.
  **Learn from Phase 18's W2** (`18-VERIFICATION.md:226-250`): `append_addendum` rewrote the
  ship-decision placeholder *unconditionally*, silently converting "not yet recorded" into "recorded
  in the dated continuation" when no decision had been written. A Phase 19 equivalent must make the
  placeholder rewrite **conditional on the addendum actually containing the thing it claims**.

---

## Q7 — WHAT COULD MAKE THIS PHASE INCONCLUSIVE OR EMBARRASSING

Ranked by probability × cost. Each row says whether the plan must **measure** it or may **assume**.

### 1. (c) is already failed before the erasure — **MEASURE, and expect it**

Covered fully in §Q4. Probability: near certain under Δ_dialog = 0.001704. Cost: the headline. The
mitigation is not to soften the rule but to (i) pre-register an adapter-regime dialogue noise floor
before the erasure runs and (ii) publish the pre-erasure dialogue PPL beside the post-erasure one in
every table, so a reader can see (c) was blown at teaching time. **This is the item most likely to
be missed and most expensive to discover late.**

### 2. The denominator makes (a) unclearable — **MEASURE (it is arithmetic; decide now)**

At n=13 the best possible Wilson upper bound is 0.172267 (§Q2). If the blind calibration returns a
floor below that, **(a) cannot pass at any outcome**, and the phase has spent its budget on a gate
that was arithmetically dead. Phase 16 hit this exact shape and named it: gating both tiers would
have taken Holm to m=12 and made the gate "unclearable at every possible outcome, including perfect
unanimity" (`scripts/phase16_persistence.py:737-743`). Phase 18 likewise refused m=8 as
"arithmetically dead at every possible outcome" (`results/phase18_extraction_report.md:160`).
**The plan must prove reachability before the pin**, the way `assert_holm_family_reachable`
(`scripts/phase18_extraction.py:248`) does: assert that *some* achievable measurement clears the
floor, or record in the pre-registration that the gate is unclearable and why.

### 3. The adapter is small enough that any perturbation destroys everything — **MEASURE**

331,776 parameters carry **ten** facts plus whatever conversational adaptation survives. The 288
rank-1 components are shared across all of them; there is no reason to expect fact-localised
structure at this capacity. The plausible failure is: ablating enough components to move the target
off rank 1 also destroys several non-targets, so (b) fails while (a) passes. **Do not assume
localisation. Measure the collateral curve**: ablate 1, 2, 4, 8, 16 … components and record target
recall, per-fact non-target recall and dialogue PPL at each step. That curve is publishable
whichever shape it has, and if it is a cliff, the cliff *is* the finding — the honest statement that
"selective erasure is not selective at 331,776 parameters" is a real contribution and is exactly the
register Phase 13 used for its 79/70 role-token leakage (`STATE.md:135`) and Phase 16 for its
capability-deficit branch.

### 4. Erasing a 92/104-recoverable fact turns out to be trivial — **acceptable, but frame it**

If the fact falls out on the first ablation, the phase risks reading as a non-result. It is not: the
paired instruments (target rank 1 → rank k, non-targets stay at rank 1, capability unchanged) make
"trivial" a *measurement* rather than an absence. But the plan should decide in advance what it will
publish if the answer is easy, so the framing is not written after the number — the same discipline
`licensed_headline` gave Phase 16 (`STATE.md:180`).

### 5. The `forbid_ids` mask — **assume, with the correction on record**

`REQUIREMENTS.md:122-123` (ATK-04) says the tokenizer "forbids 7,645 of 8,192 ids at sampling and
can silently depress an extraction rate for reasons unrelated to privacy". Phase 18 **measured the
opposite sign** and published it: masking dead ids "makes the attacker STRONGER by spending every
draw on text" (`results/phase18_extraction_report.md:244`); `tok.decode([dead_id])` raises, so the
mask removes unusable draws rather than usable ones (`scripts/demo_app.py:86`,
`scripts/evaluate.py:116`). So the mask does **not** manufacture a false (a) pass by suppressing the
target string. The residual concern is different and is answered by the same instrument: the model's
generative surface is only 547 live ids, so a post-erasure zero could still be a decoding artifact —
and that is precisely what `zero_results_have_nll` and the exposure rank exist to separate
(`scripts/erasure_gate.py:223-227`). **The plan must use the same `forbid_ids` mask and record its
sha256** (`79b55770f4dcfa94…`, `results/phase17_personas_report.md:719`) via
`phase16_persistence.forbid_digest` (`:180`), or the post-erasure number is not comparable to
Phase 18's.

### 6. (b) at n=8 with per-fact reporting — **MEASURE; pooling is forbidden**

Seven non-target facts, each at 13 or 27 questions. `erasure_succeeded` takes `max(nontarget_deltas)`
(`:237`), so **one** destroyed fact fails (b) — which is the intent
(`ROADMAP.md:518-522`: "a pooled rate can hide one destroyed fact behind seven intact ones"). Two
traps: an empty `nontarget_deltas` returns INCONCLUSIVE by construction (`:253-254`), and the
`nontarget_noise_floor` must be measured **in the same run** (§Q4) or (b)'s margin is unpriced.
Under STAT-06, nothing at n=8 may be converted into a p-value here.

### 7. Representational consistency accidentally becomes a gate — **structural, prevent it**

ΔW cosine and Fisher overlap are **descriptive and never pass/fail**
(`scripts/erasure_gate.py:118-122`; `ROADMAP.md:530-534`: "Any plan that converts one of these into
pass/fail is violating the pre-registration"). Phase 16/17/18 enforce this structurally rather than
by convention — `tests/test_phase16_stats.py::test_context_pressure_sweep_is_not_gated` landed
*before* the code it guards (`scripts/phase16_persistence.py:1289-1293`), and Phase 17's D-21 scan
catches a second `sign_test_exact` call site as a second hypothesis family (`STATE.md:219`). Phase 19
should ship the equivalent static guard in the same wave as the representational read. Tooling
exists: `scripts/extract_deltas.adapter_cells` (`:174`) computes `ΔW = scale·(B@A)` per (layer,
projection) with `scale` **read from the artifact**, and `fisher_cells` (`:199`) reduces the Fisher
diagonal per cell by MEAN (`FISHER_AGGREGATE = "mean"`, `:109`).

### 8. Comparability drift against Phase 18 — **MEASURE by digest**

If the post-erasure run uses a different corpus, mask, `stop_ids`, K, decode temperature or seed
stride, the comparison against 92/104 is void. Record and assert: `corpus_sha256`,
`forbid_ids_sha256`, `K = 48`, `ASR_RUNGS = (1,4,16,48)`, `STOP_IDS = {8184, 8185}`
(`scripts/phase14_recall.py:162`), `SAMPLE_TEMPERATURE = 0.8` / `SAMPLE_TOP_P = 0.95` (`:159-160`),
and the `seed_index * K` stride (`scripts/phase18_extraction.py:3640`). Phase 18 evidences the
pairing by digest and by two distinct pids, not by assertion
(`results/phase18_extraction_report.md:260-265`).

---

## Don't Hand-Roll

| Problem | Do NOT build | Use instead | Why |
|---|---|---|---|
| Confidence bound on a zero rate | a Wald interval, or a fresh Wilson | `erasure_gate.wilson_upper_bound` (`:139`) + `rule_of_three` (`:161`) | Wald degenerates to `[0,0]` at zero successes — the exact case (a) cares about (`:144-147`). `phase16_persistence.report_proportion:941` already imports it |
| Clustered interval | a question-only or draw-level bootstrap | `phase16_persistence.cluster_bootstrap` (`:843`) | Two-stage (facts, then questions) by explicit user decision (`STATE.md:189`); a stage-2-only bootstrap gives a zero-width interval on this fixture |
| Multiplicity correction | Benjamini–Hochberg | `phase16_persistence.holm` (`:1170`) + `HOLM_ALPHA` (`:1005`) | STAT-03: off-diagonals share adapters row-wise and question sets column-wise, so BH's PRDS assumption fails |
| Teacher-forced NLL | a bespoke masked cross-entropy | `phase18_extraction.span_nll_from_ids` (`:1050`) | Shift semantics match `masked_perplexity` exactly (`:1059-1064`); asserts `n_scored == len(value_ids)` |
| Dialogue quality score | a new "conversational quality" metric | `masked_perplexity` (`perplexity.py:83`) | THE frozen gate metric; the in-loop 20-batch estimator is disallowed for gates (`STATE.md:119`) |
| Recall predicate | an id-subsequence match | `phase14_recall.contains_value` (`:300`) | BPE is context-dependent at merge boundaries; id-subsequence measures the tokenizer, not recall (`:302-311`) |
| EWC/Fisher machinery | a new penalty or estimator | `continual/ewc.EWCPenalty` (`:33`) + `continual/fisher.estimate_fisher` (`:63`) | Both work over any `named_parameters()` key set; the LoRA path is verified in §Q1 |
| Adapter I/O | `torch.load`/`torch.save` directly | `checkpoint.export_adapter` (`:196`) / `load_adapter` (`:223`) / `lora.load_adapter_weights` (`:76`) | `weights_only=True` choke points; key + shape + **scale** audits (the last closes W1 — `alpha` is shape-invisible) |
| Statistics dependency | `scipy` | stdlib | Declined in committed code three times: `continual/fisher.py`, `scripts/phase15_stats.py`, `scripts/erasure_gate.py:147-149`. STAT-04 is sha256-enforced |
| Ordering enforcement | committer dates | `git merge-base --is-ancestor` | Dates are rewritable, skewed and non-monotonic after rebase (`tests/test_phase16_prereg.py:11-17`) |

**Key insight:** in this repository the expensive thing is never the code — it is the *provenance* of
a number. Every instrument above already carries its own label, its own denominator and its own
refusal. A reimplementation loses all three silently.

---

## Common Pitfalls

**P19-1 — Editing `scripts/phase18_extraction.py`.** Even a one-line additive widening reddens a
committed guard. Import; write a Phase 19 twin where an import is impossible; put shared statistics
in `phase16_persistence.py`, which is not frozen. (§Q3)

**P19-2 — Forgetting `results/phase19_*` in `V3_ARTIFACT_GLOBS`.** `tests/test_phase16_prereg.py:54`
lists three prefixes and its own docstring warns: "a new phase writing results under a fourth prefix
must be added here". Omit it and every Phase 19 artifact escapes the erasure-rule ancestry check
while the suite stays green.

**P19-3 — Writing the floor constant into the pinned file.** It cannot exist until after a Phase 19
artifact does. Use Phase 17's two-file split. (§Q6)

**P19-4 — Deriving the floor with a different instrument than the target is scored with.** A floor
from a 9-draw direct-question sweep does not cap an A2/K=48 number. (§Q2)

**P19-5 — Counting draws as questions.** `_handoff_counts` (`:2782`) exists because a draw count
"would divide the same numerator by nine times the denominator". Every `n` in Phase 19 is a question
count, proved against a derived quantity.

**P19-6 — A zero with no NLL.** INCONCLUSIVE, mandatory, and it is the *success* case that produces
the zero. (§Q3)

**P19-7 — Re-rendering a report that carries a recorded verdict.** Extend by addendum; make the
placeholder rewrite conditional (Phase 18 W2, `18-VERIFICATION.md:226-250`).

**P19-8 — Assuming `mark_only_lora_trainable` composes with `estimate_fisher`.** It raises. Verified
in §Q1.

**P19-9 — Reusing the Phase 14 calibration adapter without saying so.** It was trained under a
different plan's recipe and scored by a different instrument. If reused, the report must state which
of its properties are inherited; a fresh 81 s retrain avoids the whole argument.

---

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|---|---|---|---|---|
| Python | everything | ✓ | 3.11.15 (`.venv`) | none needed (3.14 system Python is NOT a supported target — `CLAUDE.md`) |
| PyTorch | all measurement | ✓ | 2.7.1 | — |
| MPS backend | training + generation | ✓ | `torch.backends.mps.is_available() → True` | CPU (slower); `preflight_device` resolves CUDA→MPS→CPU |
| pytest | the suite | ✓ | 9.0.3 | — |
| git ≥ 2.x with full history | ancestry guards | ✓ | 2.50.1; `rev-parse --is-shallow-repository → false` | none — the guards **assert**, never skip |
| `checkpoints/convbase_best.pt` | retrain reference | ✓ | 278 MB, 2026-08-01 | none |
| `checkpoints/convbase_slim.pt` | scoring loader | ✓ | 55.6 MB | none |
| `checkpoints/persona_adapter.pt` | the target | ✓ | 1,350,523 B | none |
| `checkpoints/phase14_cal_*_adapter.pt` | optional calibration reuse | ✓ | 3 files | fresh 81 s retrain |
| `data/dialog_val.bin` + mask | (c) dialogue PPL | ✓ | 1.28 MB / 638 KB | none |
| `data/retention_val.bin` | (c) retention PPL | ✓ | 2,000,572 B = 1,000,286 tokens | rebuild via `build_retention_bin.py` (refuses to re-run by design) |
| `data/persona_real_train.bin` + mask | Fisher / retrain | ✓ | 40,072 B / 20,036 B | rebuilt by `build_arm_bins` in 0.1 s |
| `artifacts/tokenizer.json` | everything | ✓ | frozen, 5,648 B | **never retrain** |
| Network / external API | — | **not used, by design** | — | ATK-01: no external API, no hosted model |
| New pip packages | — | **forbidden** | — | STAT-04, sha256-pinned |

**Missing with no fallback:** none.
**UNVERIFIED:** `torch.linalg.svd` on MPS (only relevant if M5 is chosen; the matrices are ≤1536×384
so CPU is fine — verify with a 3-line probe before planning around it).

---

## Validation Architecture

### Test framework

| Property | Value |
|---|---|
| Framework | pytest 9.0.3 |
| Config | `pyproject.toml` (sha256-pinned by `tests/test_package.py`) |
| Quick run | `.venv/bin/python -m pytest -q tests/test_phase16_prereg.py tests/test_package.py` (~seconds) |
| Full suite | `make test` → 727 passed / 1 skipped / 728 collected in ~154 s (`18-VERIFICATION.md:131-133`) |
| The one skip | `test_train_loop.py::test_amp_fp16_smoke` — needs CUDA; unrelated |

### Requirements → test map

| Req | Behaviour | Type | Command | Exists? |
|---|---|---|---|---|
| ERASE-01 | The floor-derivation rule is a pure function with pinned boundary semantics | unit | `pytest tests/test_phase19_erasure.py -x` | ❌ Wave 0 |
| ERASE-01 | The Phase 19 pin precedes every `results/phase19_*` first-add | integration (git) | `pytest tests/test_phase16_prereg.py -x` | ⚠️ exists, **must be extended** (`:54` + a new twin) |
| ERASE-01 | The floor file precedes every target artifact | integration (git) | same file | ❌ Wave 0 |
| ERASE-01 | `erasure_succeeded` is **called**, never re-implemented; no second verdict path | static (AST) | `pytest tests/test_phase19_erasure.py -k verdict` | ❌ Wave 0 |
| ERASE-01 | ΔW cosine / Fisher overlap reach no gate — no `sign_test_exact` and no threshold on that path | static (AST) | `pytest tests/test_phase19_erasure.py -k descriptive` | ❌ Wave 0 (mirror `test_context_pressure_sweep_is_not_gated`) |
| ERASE-01 | Every `draw_all` call site asserts in-prompt | static (AST) | `pytest tests/test_phase14_scoring.py -k draw_all` | ⚠️ exists; add the Phase 19 entry to `DRAW_ALL_ASSERTED_BY` (`:579`) |
| ERASE-01 | Post-erasure corpus digest / mask digest / K match Phase 18's | unit | `pytest tests/test_phase19_erasure.py -k parity` | ❌ Wave 0 |
| ERASE-01 | The ablation operator is exactly representable: a zeroed component leaves `ΔW` rank-8-writable and `load_adapter_weights` accepts the artifact | unit, CPU | `pytest tests/test_phase19_erasure.py -k artifact` | ❌ Wave 0 |
| ERASE-02 | The retrain arm's fact list is `LOCKED_FACTS + SOFT_TIER_FACTS` minus exactly one, and every other recipe constant is unchanged | unit, CPU | `pytest tests/test_phase19_erasure.py -k retrain_arm` | ❌ Wave 0 |
| STAT-01 | Every published `n` is a question count, proved against a derived quantity | unit | `-k denominator` | ❌ Wave 0 |
| STAT-02 | Every proportion carries denominator + Wilson + `3/n` at zero; **no bare `0%`** anywhere | unit + grep | `-k reporting`; `grep -rn '0%' results/phase19_*` → 0 hits | ❌ Wave 0 |
| STAT-04 | `pyproject.toml` byte-identical | unit | `pytest tests/test_package.py -x` | ✅ exists |
| STAT-06 | Nothing at n=8 is gated | static | `-k descriptive` | ❌ Wave 0 |

### Sampling rate

- **Per task commit:** `pytest -q tests/test_phase19_erasure.py tests/test_phase16_prereg.py tests/test_package.py`
- **Per wave merge:** `make test` (full suite, ~154 s)
- **Phase gate:** full suite green before `/gsd:verify-work`; plus the guards **watched RED** by
  deliberate mutation and restored byte-identical — the standing practice (`STATE.md:157,203`), and
  the reason Phase 15 caught a guard nobody had seen fail.

### Wave 0 gaps

- [ ] `tests/test_phase19_erasure.py` — the whole table above
- [ ] `tests/test_phase16_prereg.py` — `V3_ARTIFACT_GLOBS += "results/phase19_*"` (`:54`) and
      `test_phase19_prereg_is_frozen_before_every_phase19_result`, plus the floor-file guard
- [ ] `tests/test_phase14_scoring.py` — new `DRAW_ALL_ASSERTED_BY` entry (`:579`) and, if a
      `persona=` call site is added, a `PERSONA_ALLOWLIST` entry (`:422`)
- [ ] Framework install: **none** — pytest 9.0.3 is present

---

## Security Domain

`security_enforcement` is not set in `.planning/config.json`, so it is treated as enabled. This is an
offline, single-process research phase with no network, no server, no user input and no
authentication surface, so most ASVS categories do not apply. The two that do are already enforced
and must not regress.

| ASVS category | Applies | Standard control in this repo |
|---|---|---|
| V2 Authentication | no | no auth surface |
| V3 Session management | no | no sessions |
| V4 Access control | no | single local process |
| V5 Input validation | **yes** | Every artifact read is schema-proved as an **ordered hard equality** before use (`_corpus_entry` `:769`, `_exposure_record` `:1344`); `_prove` raises `SystemExit`, never a strippable `assert` (`phase14_recall.py:221-224`) |
| V6 Cryptography | **yes (integrity only)** | sha256 over canonical JSON for corpus provenance (`corpus_sha256` `:758`) and over the `forbid_ids` mask (`forbid_digest` `:180`). No secrets, no crypto to hand-roll |

| Threat | STRIDE | Mitigation |
|---|---|---|
| Arbitrary code execution from a pickled checkpoint | Elevation | `weights_only=True` at the shareable choke points (`load_slim`, `load_adapter`); `weights_only=False` only on the project's own trusted resume checkpoints, with the reason recorded (`teach_persona.py:589-591`) |
| Silent replacement of recorded evidence | Tampering | `refuse_if_exists` on all five training outputs before a token is written (`teach_persona.py:560-562`); arm-record existence refusal with no force flag (`phase18_extraction.py:3536-3542`); report clobber guards |
| Post-hoc edit of a pre-registration | Repudiation | git-ancestry guards (§Q6) — the primary control of this whole milestone |
| Fact value leaking into a scored prompt | Information disclosure | `assert_no_value_in_prompt` at both string and id levels (`phase14_recall.py:398`); LAZY-IMPORT RULE keeps fact strings out of driver import surfaces; `test_no_fact_strings_at_import` (`tests/test_phase14_scoring.py:367`) |
| Personal data in a public artifact | Information disclosure | T-14-05: every value is invented; everything under `results/` ships publicly (`phase14_factset.py:38-39`) |
| Network egress during a measurement | Information disclosure | `test_no_network_imports` (`18-VERIFICATION.md:57`); ATK-01 forbids external APIs. **Phase 19 must add its driver to that scan** |

---

## Package Legitimacy Audit

**Not applicable, and that is a hard requirement rather than an omission.** Phase 19 installs
**zero** packages. STAT-04 (`REQUIREMENTS.md:35-39`) requires `pyproject.toml` to be byte-identical
at v3.0 close and is enforced by a sha256 pin read as bytes (`tests/test_package.py`, `STATE.md:173`).
Phase 18 discharged the same requirement by measurement: `git log --since=2026-08-15` on both
`pyproject.toml` and `requirements.txt` returned empty (`18-VERIFICATION.md:167`). Every library
Phase 19 needs — torch 2.7.1, numpy, pytest — is already installed and pinned. No `pip install`,
`npm install` or equivalent appears anywhere in this research.

---

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|---|---|---|
| A1 | `Δ_dialog = 0.001704` is the natural candidate for `dialogue_ppl_noise_floor` by the same logic that adopted `Δ_ret = 0.068930` | Q4 | It is a *candidate*, not a locked choice — the argument by symmetry is mine, not the pre-registration's. If the plan adopts it, (c) fails at every outcome; the decision belongs to the user (D3) |
| A2 | A same-recipe seed-pair dialogue-PPL spread for LoRA adapters has never been measured here | Q4 | If one exists somewhere I did not grep, the plan would duplicate work. Verify: `grep -rn "seed" results/*.md \| grep -i "ppl"` |
| A3 | ~3 minutes buys the adapter-regime dialogue noise floor (2 × 81 s) | Q4 | Understates if the noise-floor arms need the full collapse control each time (adds seconds, not minutes) |
| A4 | The 288 rank-1 components are the natural surgery surface and a per-component NLL search is affordable | Q1 | If components turn out to be entangled such that single-component ablation moves nothing, M1 degrades to a subset search — still cheap, but the selection story gets weaker |
| A5 | Ablating rank-1 components keeps the artifact rank-8-writable | Q1 | Structurally true (zeroing `B[:,j]` and `A[j,:]` leaves shapes intact) but **not run** — a 10-line CPU test settles it in Wave 0 |
| A6 | Pooling the target's taught + held-out questions to n=27 is defensible under STAT-01 | Q2 | If the user reads the tiers as non-poolable, n stays at 13 and the floor arithmetic tightens sharply |
| A7 | "~88% recovery by relearning attack" (`results/phase18_extraction_report.md:244`) is a real literature finding | Q1, Sources | Phase 18's claim, **not independently verified in this session**. Cited here only as context for why relearning attacks matter; no Phase 19 number depends on it |
| A8 | `torch.linalg.svd` works on MPS | Q1/M5 | Only bites if M5 is chosen, which is recommended against. CPU fallback is free at these matrix sizes |
| A9 | Reusing `checkpoints/phase14_cal_first_person_replay_adapter.pt` is cheaper than retraining a calibration adapter | Q2 | It is cheaper in seconds and more expensive in argument; the research recommends the fresh retrain |

---

## Sources

### Primary — this repository (HIGH; every one opened this session)

`scripts/erasure_gate.py` · `scripts/phase18_extraction.py` · `scripts/phase16_persistence.py` ·
`scripts/phase14_recall.py` · `scripts/phase14_factset.py` · `scripts/teach_persona.py` ·
`scripts/extract_deltas.py` · `scripts/finetune_ab.py` · `scripts/estimate_fisher_tinystories.py` ·
`scripts/build_retention_bin.py` · `src/personacore/{lora/layer.py, lora/inject.py, lora/config.py,
continual/fisher.py, continual/ewc.py, evaluation/perplexity.py, training/loop.py, training/loss.py,
config.py}` · `tests/test_phase16_prereg.py` · `tests/test_phase14_scoring.py` ·
`results/{finetune_smoke_report.md, finetune_prod.csv, phase14_recall_report.md,
phase14_teaching_run.log, phase17_training_run.log, phase18_extraction_report.md,
phase18_preflight_report.md, phase16_recall_sample.json}` · `.planning/{ROADMAP.md,
REQUIREMENTS.md, STATE.md}` · `18-VERIFICATION.md` · `CLAUDE.md`

### Session measurements (HIGH — produced by running code, not by reading it)

- `wilson_upper_bound(0, n)` at n ∈ {13, 14, 27, 52, 54, 104, 108, 216} — the denominator table (§Q2)
- `erasure_succeeded(...)` on the pre-erasure dialogue PPL → **FAILURE** on (c) (§Summary, §Q4)
- `estimate_fisher` on a LoRA-injected model, with and without `mark_only_lora_trainable` (§Q1)
- Per-fact question counts re-derived from `results/phase16_recall_sample.json` → 13 / 14 (§Q2)
- Commit-order verification via `git log` for `d7d7917`, `0425fdc`, `921a6bc`, `f93b502`, `043bf4d`,
  `23a830c`, `99716e0`, and every `results/phase18_*` first-add (§Q2, §Q3, §Q6)
- Environment probe: Python 3.11.15, torch 2.7.1, MPS available, pytest 9.0.3, git 2.50.1, non-shallow

### External — cited as METHOD and CONTEXT sources only, never as sources of constants

The pre-registration's own SOURCES block (`scripts/erasure_gate.py:54-66`) is the model. Each entry
below says what it is cited *for*.

- **Maini, Feng, Schwarzschild, Lipton, Kolter — *TOFU: A Task of Fictitious Unlearning for LLMs*
  (arXiv:2401.06121, 2024).** Cited **for the mechanism taxonomy only**: gradient ascent, gradient
  difference, KL minimisation, preference optimisation, and the finding that retain-aware variants
  outperform plain gradient ascent — which is why M6 is recommended against and M3/M4 are paired.
  Its **thresholds are explicitly not adopted** (`scripts/erasure_gate.py:24-27`;
  `REQUIREMENTS.md:186-188`).
- **Thaker, Hu, Kale, Maurya, Wu, Smith — *Position: LLM Unlearning Benchmarks are Weak Measures of
  Progress* (arXiv:2410.02879, 2024; v2 2025).** Cited **for the goal framing**: benign
  modifications expose supposedly-unlearned information and degraded retain performance that the
  original benchmarks hide. This is the paper the pre-registration names as the reason the goal is a
  *measurable bound* rather than *indistinguishable from never-learned*
  (`scripts/erasure_gate.py:33-36`, `:62-63`). It is also the reason §Q7's collateral curve is
  mandatory rather than optional.
- **Ilharco, Ribeiro, Wortsman, Gururangan, Schmidt, Hajishirzi, Farhadi — *Editing Models with Task
  Arithmetic* (ICLR 2023).** Cited **for mechanism M5 only**: `θ_edited = θ_pre − λ·τ_unwanted` as
  targeted behaviour removal without negative training examples. Recommended against here for a
  repo-specific structural reason (rank, and the bit-identity control), not because the method is
  unsound.
- **Hu et al. — *Unlearning or Obfuscating? Jogging the Memory of Unlearned LLMs via Benign
  Relearning* (arXiv:2406.13356).** Cited **for context on why the phase's claim must stay
  bounded**: a few fine-tuning samples can recover supposedly-erased knowledge, so "we could not
  extract it" is not "it is gone". Phase 18 already names the relearning attack as absent
  (`results/phase18_extraction_report.md:244`) and as the obvious Phase 19+ follow-up. **The specific
  "~88%" figure Phase 18 quotes was not verified in this session (A7).**
- **Carlini et al. — *The Secret Sharer* (USENIX Security 2019) and *Extracting Training Data from
  Large Language Models* (USENIX Security 2021).** Cited **for the exposure instrument**, already
  implemented as `exposure_rank` (`scripts/phase18_extraction.py:1230`) and already named in the
  pre-registration's SOURCES.
- **Shokri et al. — *Membership Inference Attacks Against Machine Learning Models* (IEEE S&P 2017).**
  Cited **only to explain why MIA is NOT used**: n=8 members makes it uninformative
  (`REQUIREMENTS.md:180-183`). Never as a method.

---

## Open decisions for the planner

Research can bound these; it must not settle them.

**D1 — THE MECHANISM (the one the pre-registration deliberately left open).**
Research recommends **M1 (ΔW rank-1 component ablation) + M2 (retrain-without)**, and prices M3/M4
as an affordable third arm. The choice is the user's. Whichever is chosen, the *mechanism identity
and its parameters* must be inside the pinned file before the calibration runs, or the mechanism
becomes a knob that can be swapped after a disappointing floor.

**D2 — The (a) floor derivation rule, and its direction.**
Phase 14's rule discounted a ceiling *downward* to make a threshold harder to clear
(`teach_persona.py:812-831`). For erasure the floor is an *upper cap*, so "the same procedure" points
in the opposite direction: a larger floor makes (a) easier. Research will not choose the operator.
What research can say: at n=13 nothing below **0.172267** is clearable at any outcome, and the plan
must prove reachability before the pin (§Q7.2).

**D3 — `dialogue_ppl_noise_floor`, and what to do about (c).**
Four honest responses are laid out in §Q4. This is the phase's biggest single decision and it
determines whether the published verdict can be anything other than FAILURE. **Do not let it be
decided implicitly by whichever number is convenient at verdict time.**

**D4 — The (b) noise-floor estimator.**
Seed-stride re-scoring of the unerased adapter (~30 min) is the cheap option with a Phase 17
precedent. A second-seed retrain is more faithful to "how much does an adapter's per-fact recall
vary" but confounds init noise with the erasure. Pick one, in the pinned file, before running.

**D5 — The (a) denominator: n = 13 or n = 27.**
Gated tier only, or both tiers pooled. Research recommends against n = 52/108 (§Q2). This choice
changes the floor's reachability by a factor of ~1.9 and must be pre-registered.

**D6 — Calibration adapter: reuse `phase14_cal_first_person_replay_adapter.pt`, or retrain (81 s).**
Research leans retrain — it costs 81 seconds and removes an argument about instrument and recipe
provenance.

**D7 — How many facts to erase, and whether the target is the Phase 18 target.**
The ROADMAP says "**one** taught fact" (`:485`). Phase 18's handoff is an aggregate over all eight
gated slots (92/104), not one fact. So the plan must **name the target fact explicitly**, in the
pinned file, before anything runs — and state how it was chosen. Choosing the fact with the highest
Phase 18 recall, or the lowest, are both defensible; choosing it after seeing the calibration result
is not.

**D8 — Publication posture if the collateral curve is a cliff.**
If ablating enough to erase the target also destroys non-targets, the finding is "selective erasure
is not selective at 331,776 parameters". Decide *now* that this ships unsoftened, in the register
Phase 18 shipped `LEAKAGE_DEMONSTRATED` (`ROADMAP.md:536-540`), so the framing is not written after
the number.

---

## Metadata

**Confidence breakdown**

| Area | Level | Reason |
|---|---|---|
| Repo facts, file:line pointers | HIGH | Every cited file was opened; every number was re-measured or read directly |
| The (c) arithmetic and its consequence | HIGH | Computed with the committed `erasure_succeeded` this session |
| The pin-freeze constraint on Phase 18's driver | HIGH | Verified against `git log` timestamps on both sides of the ancestry relation |
| The Fisher/LoRA composition result | HIGH | Ran it; both branches observed |
| Denominator table | HIGH | Computed with the committed `wilson_upper_bound` |
| Mechanism *outcomes* (will M1 work?) | **LOW** | Nothing has been run; §Q7.3 is the honest statement of what is unknown |
| Whether an adapter-regime dialogue noise floor reaches 0.62105 | **LOW / UNVERIFIED** | Never measured; the only adjacent number is a different recipe |
| External literature | MEDIUM-HIGH | TOFU, 2410.02879 and Ilharco verified as canonical by search; cited for method/context only |

**Research date:** 2026-08-17
**Valid until:** the repo facts do not expire — they are pinned by git. The external mechanism
survey is worth re-checking in ~90 days; the unlearning literature moves fast, but nothing in this
phase's gates depends on it.
