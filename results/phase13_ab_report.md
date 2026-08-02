# EWC A/B No-Forgetting Report (Phase 13 — DEMO-04 / VIZ-01 / VIZ-04)

> **What these numbers will be:** a pre-registered DEMONSTRATION of ONE comparison — two arms
> fine-tuned fresh from `checkpoints/best.pt` with an identical seed, config, and data order,
> differing in exactly one bit (`penalty_fn`: λ=0 naive vs λ=0.01 EWC) — at the 4000-step
> production budget, judged by a **retention-only** gate against the Phase-12 noise floor.
> Every rule below (the gate, the margin, both arm configs, the endpoint definition) was
> hardcoded in `scripts/finetune_ab.py` and written here **before either arm ran**; git history
> order is the pre-registration proof (commit `c3d942e`, tests `91aedd1`).
>
> **What they are not:** a λ search. Phase 12's §8 sweep over five λ values returned
> λ\* = None ("EWC not demonstrable at the 1250-step budget") under a blind DUAL margin, and
> that verdict stands unamended — see `## Reconciliation: §8 Search vs Phase-13 Demonstration`.
> They are also not comparable to the TinyStories headline (different corpus/register) or to
> any unmasked PPL. Frozen gate policy (Phase 12 §1) applies unchanged: acquisition =
> `masked_perplexity` on `data/dialog_val.bin` + `data/dialog_val_mask.bin`, block 256, dead
> ids forbidden; retention = `retention_perplexity` on the frozen `data/retention_val.bin`
> sub-bin. In-loop `val_loss` is never a gate.
>
> Step-0 row mechanism (TUNE-02): the v1.0 eval block logs NO step-0 row (12-01 pinned fact),
> so each arm CSV is PRE-SEEDED by the driver with a header + measured step-0 row before
> `train()` appends to it.

## Pre-Registration

Locked in `scripts/finetune_ab.py` at commit `c3d942e`; contracts pinned by
`tests/test_phase13_driver.py` at commit `91aedd1`. No Phase-13 number existed at either commit.

| Constant | Value | Rationale | Locked at |
| --- | --- | --- | --- |
| K | 2 | reused BLIND from Phase 12 — the same deliberately conservative default, NOT re-chosen after seeing any Phase-13 number | `c3d942e` |
| DELTA_RET | 0.068930 | retention noise floor, **regime named** (D-05 obligation 1): `finetune_smoke_report.md` Stage 0b, seed pair (1337, 2024), **masked** arm, LR 9e-5, **1250** steps, otherwise-identical config | `c3d942e` |
| MARGIN | 0.137860 = K × DELTA_RET | the gate margin. The smoke report displays **0.137861** because it multiplied the unrounded floor; this phase computes from the transcribed `0.068930`. The 1e-6 difference is far below any observed effect and changes no verdict | `c3d942e` |
| λ_EWC | 0.01 | D-02: the ONLY sweep grid point moving BOTH axes favorably vs λ=0 (retention drift +3.85 → +1.67, ~57%, at +0.28 dialogue PPL). λ=100 shows half the phenomenon (near-zero drift bought with destroyed acquisition) and is deliberately not the headline | `c3d942e` |
| Arm config | unmasked, LR 9e-5, seed 1337, 4000 steps, batch 32, accum 1 | D-03: the recorded twin config from `results/finetune_prod_run.log` (`TrainConfig(lr=9e-05, batch_size=32, max_steps=4000, warmup_steps=100, grad_clip=1.0, grad_accum_steps=1, weight_decay=0.1, seed=1337)`). Both arms start **fresh from `best.pt`** (D-01) — Phase 12's production checkpoint is not reused | `c3d942e` |
| Endpoint definition | end-of-run (step 4000) cells | D-08: the claim is about model state after a fixed budget. The best-checkpoint kwarg is omitted entirely so no second selection decision dilutes "differs only in the penalty" | `c3d942e` |
| Gate rule | EWC mitigates forgetting **iff** `naive_ret − ewc_ret > MARGIN`; boundary (`== MARGIN`) is a FAIL | D-06: retention side pre-registered only. Acquisition cost is reported **descriptively in the 2×2 with NO pass/fail gate** — it is the expected, non-binary side of a known trade-off, not a claim requiring its own margin | `c3d942e` |
| Artifact isolation | `results/phase13_{arm}/run.csv`, `checkpoints/phase13_{arm}_latest.pt`; refuse-to-rerun on both | D-07 / WR-02: no Phase-12 output path is ever a write target; `results/finetune_prod.csv` is read-only D-11 input | `c3d942e` |

### Provenance exception (the one number not read from a committed CSV)

`retention_ppl` for λ=0 is absent from `ft_lr_9e-5.csv` (column not logged by the Stage-2
driver, a pre-Phase-13 decision); value **5.9553** (and dialogue **4.4453**) is cited from
`results/finetune_smoke_report.md` Stage 2/3 tables, commit `666d096` — **not recomputed here**.
This affects only the λ=0 point of the VIZ-04 frontier; the five λ CSVs carry their own
`retention_ppl` final rows, and both Phase-13 arms log the column in-loop.

## 2×2 Result

Both axes, both arms — never retention alone (DEMO-04: "retention-only is the classic sleight
of hand"). Lower is better in every cell.

| Arm | λ | Acquisition — masked dialogue val PPL | Retention — retention PPL (frozen sub-bin) |
| --- | --- | --- | --- |
| _step-0 reference (shared anchor, `best.pt`)_ | — | _31.903875386436905_ | _2.107553076833866_ |
| naive | 0 | **4.192794562524908** | **8.52417066884246** |
| EWC | 0.01 | **4.573349242745997** | **3.8911400839446597** |

Read as movement from the shared step-0 anchor:

| Arm | Acquisition gain (↓ better) | Retention drift (↑ worse) |
| --- | --- | --- |
| naive (λ=0) | −27.711081 (31.9039 → 4.1928) | **+6.416618** |
| EWC (λ=0.01) | −27.330526 (31.9039 → 4.5733) | **+1.783587** |

Both arms learn the dialogue task to within 0.38 PPL of each other; they differ by a factor of
3.6 in how much of the base task they destroy doing it. That is the whole claim of this phase,
and it needs both columns to be visible at once.

**Cells are end-of-run (step 4000) values (D-08), read verbatim from the final rows of
`results/phase13_naive/run.csv` and `results/phase13_ewc/run.csv`** — no best-checkpoint
selection is used anywhere in this phase, so the only decision separating the arms is the
penalty. Both arm checkpoints are kept under the D-07 scoped paths
(`checkpoints/phase13_naive_latest.pt`, `checkpoints/phase13_ewc_latest.pt`; local, gitignored,
untouched since the runs).

**Naive-arm footnote:** the naive CSV's `ewc_penalty` column is **measured, not applied**.
The naive arm constructs `EWCPenalty` so both CSV schemas match for plotting, but
passes `None` to `train()`. The column is a free diagnostic of how far the unconstrained arm
travels from θ\*: it rises 0.186 → **1.593** over the run, while the EWC arm's settles at 0.134.

### Within-run retention trajectory (naive arm — D-05 obligation 3)

The free, zero-compute stability check the noise floor's transferability argument rests on: the
λ=0 arm's own interval-to-interval retention deltas, from its own CSV.

| interval | Δ retention PPL | interval | Δ retention PPL |
| --- | --- | --- | --- |
| 0 → 250 | +2.9152 | 2000 → 2250 | +0.1890 |
| 250 → 500 | +0.3606 | 2250 → 2500 | **−0.0573** |
| 500 → 750 | +0.5050 | 2500 → 2750 | +0.2859 |
| 750 → 1000 | +0.4791 | 2750 → 3000 | +0.3905 |
| 1000 → 1250 | +0.2964 | 3000 → 3250 | **−0.0622** |
| 1250 → 1500 | +0.2437 | 3250 → 3500 | +0.0219 |
| 1500 → 1750 | +0.3710 | 3500 → 3750 | +0.1990 |
| 1750 → 2000 | +0.2901 | 3750 → 4000 | **−0.0114** |

16 intervals: 13 upward, 3 downward. Range [−0.062183, +2.915207]; excluding the initial
0 → 250 collapse step, all remaining deltas lie in [−0.062183, +0.505]. **Every downward
excursion (−0.0573, −0.0622, −0.0114) is smaller in magnitude than MARGIN = 0.137860** — the
trajectory is monotone-increasing up to jitter strictly below the gate margin, with no
oscillation, no reversal, and no late-run instability. This is a within-run stability signal
consistent with the 1250-step floor transferring to the 4000-step budget; it is corroboration,
not a re-measurement (see `## Threats to Validity`).

## Gate Verdict

The pre-registered rule (D-06, retention-only, boundary-exclusive), applied with the constants
committed in `scripts/finetune_ab.py` at `c3d942e` — the verdict below was computed by
importing that module's own `MARGIN` and `ewc_mitigates`, not re-derived by hand:

```
delta  = naive_ret_4000 − ewc_ret_4000
       = 8.52417066884246 − 3.8911400839446597
       = 4.633030584897801

MARGIN = K × DELTA_RET = 2 × 0.068930 = 0.137860

ewc_mitigates(8.52417066884246, 3.8911400839446597)  →  4.633030584897801 > 0.137860  →  True
```

> **Verdict: EWC mitigates forgetting.** The pre-registered retention gate **holds**, at
> **33.61×** the margin (67.2× the raw noise floor Δ_ret = 0.068930).

**Acquisition — descriptive, no gate.** EWC costs **+0.380556** dialogue PPL (4.573349 vs
4.192795), i.e. ~9.1% relative. **There is no pass/fail gate on acquisition (D-06):** the
acquisition side is the expected, non-binary half of a known stability–plasticity trade-off, not
a claim requiring its own margin, and no acquisition threshold was pre-registered. It is reported
here because DEMO-04 requires both axes to be visible — and because the number is what makes the
retention result meaningful: both arms fell from 31.9039 to the low 4s, so EWC's retention win is
not bought by failing to learn the task.

The scope of this verdict is exactly the quantity the gate measures: **teacher-forced retention
perplexity on the frozen sub-bin**. It is not a claim about free-running story generation — see
`## Retention Samples`, which reports a measured negative result on that axis.

## D-11 Reproduction Cross-Check

The fresh EWC arm is config-identical to Phase 12's production run, so it doubles as an explicit
reproduction check against `results/finetune_prod.csv` (read-only input; never a write target).
Reported regardless of outcome.

| Step-4000 metric | Phase-13 EWC arm (fresh) | Phase-12 production (`finetune_prod.csv`) | Δ |
| --- | --- | --- | --- |
| `dialog_ppl` | 4.573349242745997 | 4.573349214207799 | +2.85e-8 |
| `retention_ppl` | 3.8911400839446597 | 3.891139975617828 | +1.08e-7 |
| `ewc_penalty` | 0.13435843586921692 | 0.13435843586921692 | **0 (bit-identical)** |

| | |
| --- | --- |
| \|Δ retention\| | 1.08e-7 |
| MARGIN | 0.137860 |
| ratio | ~1.3 × 10⁻⁶ of the margin |

**Outcome: MATCH.** The twin-config reproduction held on MPS. The retention difference is six
orders of magnitude inside the pre-registered margin, and `ewc_penalty` — a pure function of the
model weights — is **bit-identical**, which is the stronger statement: the two runs' weights
after 4000 optimizer steps agree exactly, and the residual 1e-8–1e-7 differences live entirely in
the multi-batch reductions of the eval sweep (see `## Threats to Validity`). The Phase-13 driver
is a confirmed faithful twin of `scripts/finetune_dialog.py`, and the D-11 divergence check in
the driver exited clean (no `SystemExit`).

**Early twin check (step 250).** The same argument was run at minute ~4 rather than minute 37.
The plan's check was exact match on the two PPL columns; those differed at 3.6e-8, so a sharper
discriminator was used instead: the EWC arm's step-250 `train_loss` (1.623079776763916) and
`ewc_penalty` (0.08073534071445465) are **bit-identical** to the production run's step-250 row.
Because `ewc_penalty` is a pure function of the weights, bit-identity after 250 steps proves the
batch stream matched bit-for-bit — Pitfall 2 cleared affirmatively, not by tolerance. Weight-
derived quantities, not eval PPL, are the durable twin test on this device.

## Threats to Validity

### 1. The gate measures teacher-forced retention, not story-mode generation

This is the largest limitation on how the headline may be read, and it is a **measured negative
result**, not a hypothetical. Prompted with a held-out TinyStories prefix and left to run free
for 128 tokens, **both arms** emit `<|user|>` within a few tokens and drop into PersonaChat
dialogue: mid-story role-token leakage is **79 (naive) vs 69 (EWC)** across 20 generations each
(`results/phase13_retention_samples.md`). The 4.63-PPL retention gap that clears the pre-registered
gate at 33.6× **does not** yield a qualitatively intact story generator in the EWC arm at this
budget.

This is not a harness defect and it does not contradict the gate. Teacher-forced retention
perplexity (the probability the model assigns to the *true* TinyStories continuation, with the
gold prefix supplied at every position) and free-running mode adherence (what the model does when
it drives its own context for 128 tokens) are different quantities, and λ=0.01 preserves the
former far better than the latter. Accordingly, this report claims the former and only the
former: **EWC mitigates measured forgetting on the retention metric.** It does **not** claim
qualitative or generative retention, and no figure or sentence here should be read as claiming it.
λ=0.01 was chosen (D-02) as the smallest constraint that moves both axes favorably; the samples
show that this smallest constraint does not also buy mode adherence — a stronger λ, a
replay/mixing term, or a longer anchor budget would be the place to look, and none of them were
run here.

### 2. The noise floor's measurement regime — and where it does not reach

**The check, not just the number.** Δ_ret = 0.068930 is the retention noise floor from
`results/finetune_smoke_report.md` **Stage 0b (D-05)**: two runs differing only in seed —
**1337 vs 2024** — on the otherwise-identical **masked** arm at **LR 9e-5** for **1250 steps**,
scored with the same frozen `retention_perplexity` on the same frozen sub-bin:

| Quantity | Seed 1337 | Seed 2024 | Δ (floor) | MARGIN (K=2 × Δ) |
| --- | --- | --- | --- | --- |
| end retention PPL | 5.074896 | 5.005966 | **0.068930** | 0.137860 |

K = 2 was declared **blind**, before any Phase-12 or Phase-13 effect existed, and was reused here
unchanged rather than re-chosen after seeing a Phase-13 number.

**Named limitation (D-05 obligation 2):** that floor was **NOT re-verified at the 4000-step
production budget**, and **NOT re-verified inside collapse dynamics** — it was measured in a
stable regime, on the masked arm, at a shorter budget, while both Phase-13 arms are unmasked and
one of them drifts by +6.42 PPL. **Seed-to-seed variance could plausibly scale with drift
magnitude**, and a floor measured in a stable regime would not capture that. Nothing here rules
that out.

The reason this is judged acceptable is the size of the gap, stated as a **judgment, not a
proof**: the observed retention separation is **33.6× MARGIN** and **67.2× the raw floor**, in
the same 40–96× band as the Phase-12 drift gates' counterfactual k values (LR 3e-5: 40.7×,
LR 9e-5: 55.8×, LR 3e-4: 96.2×). For the floor to be misleading here it would have to be wrong by
more than an order of magnitude in the drift regime, which the within-run trajectory above gives
no sign of (all downward excursions < MARGIN, no late-run instability). That is corroboration
from a free check, not a re-measurement — the honest re-measurement (a 1337/2024 seed pair at
4000 unmasked steps, ~75 min) was not run.

### 3. Single seed pair — one comparison, not a distribution

Per D-05, this phase runs **one** arm pair at seed 1337. Every number in the 2×2 is a single
measurement, and the phase reports a **comparison**, not a distribution: there are no error bars,
no confidence interval, and no claim about the variance of the effect. The floor above is the
only variance estimate in play, and it is borrowed from a different budget (see 2). A reader who
wants a distribution needs N arm pairs at N seeds; that is not what was run.

### 4. MPS non-determinism (named risk category)

The device was named a risk category for the reproduction check up front, and the measurement
bears it out at a specific magnitude. On M3/MPS, two processes running an identical trajectory
produce:

| Quantity | Cross-process reproducibility | Evidence |
| --- | --- | --- |
| training losses, `ewc_penalty` (weight-derived) | **bit-identical** | step-250 and step-4000 rows vs `finetune_prod.csv` |
| free-running generation (sampling path) | **bit-identical** | two separate sampling runs, `diff` over the full sample body empty (13-03) |
| eval perplexities (`dialog_ppl`, `retention_ppl`, `val_loss`) | **NOT bit-identical** — ~1e-8 relative | D-11 table above; step-250 3.6e-8 |

**This report does not claim bitwise eval reproducibility.** The eval PPL variance comes from
multi-batch reduction order inside `masked_perplexity` / `retention_perplexity`; the sampling path
has no such reductions (single-batch forwards, argmax or seeded multinomial), which is why
generation *is* bit-identical while eval PPL is not. The observed eval variance is 7+ orders of
magnitude below MARGIN and below every effect reported here, so it changes no verdict — but the
D-11 MATCH is therefore **evidence-based determinism, not a guarantee**: it shows this
configuration reproduced on this device on this occasion, to bit-identity in weights and ~1e-7 in
eval PPL. It does not prove the device is deterministic in general.

### 5. Scope

Retention is measured on the frozen `data/retention_val.bin` sub-bin only; the acquisition metric
is masked dialogue val PPL on one held-out PersonaChat split. Neither is comparable to the
TinyStories v1.0 headline (different corpus/register) or to any unmasked PPL. The claim covers
one model, one base task, one downstream task, one λ, one budget.

## Reconciliation: §8 Search vs Phase-13 Demonstration

Phase 12 §8 concluded, verbatim and unamended:

> **EWC not demonstrable at this budget** (no λ satisfies both the within-margin rule and the
> retention demonstrability guard) — surfaced, never massaged (pre-registered §8 all-fail
> outcome: λ\* = None, demonstrable = False).

Phase 13 concludes that EWC mitigates forgetting. Placed side by side with no explanation those
two sentences read as a contradiction, or worse as a quietly revised verdict. They are neither —
they answer different questions, under different rules, at different budgets:

| | Phase 12 §8 | Phase 13 |
| --- | --- | --- |
| Question | **SEARCH**: is there a λ that buys retention essentially for free? | **DEMONSTRATION**: does one pre-chosen λ mitigate forgetting? |
| Arms | five λ values (0.01, 0.1, 1, 10, 100) vs λ=0 | one λ (0.01) vs λ=0 — pre-chosen, pre-registered |
| Rule | **DUAL** margin — both `Δdialogue ≤ K×Δ_dialog (0.003408)` AND retention beating the floor, simultaneously | **retention-only** margin (D-06); acquisition descriptive, no gate |
| Budget | 1250-step smoke | 4000-step production |
| Outcome | λ\* = None, `demonstrable = False` (all-fail, informative) | gate holds at 33.6× MARGIN |

The dual rule is what fails, and it fails on the **dialogue** side, not the retention side. §8's
own table records that **every** λ arm beat the collapse baseline on retention — the smallest of
them, λ=0.01, by +2.17 PPL — while none came within 0.003408 dialogue PPL of λ=0. That dialogue
margin is the seed-to-seed floor for dialogue PPL (Δ_dialog = 0.001704, K=2), i.e. §8 demanded
that EWC cost *nothing measurable* on acquisition. Requiring a real regularizer to be free is a
near-impossible bar, and §8's all-fail result is the honest report that the bar was not cleared —
"the stability–plasticity trade-off is real and measured; what failed is the demonstration that
BOTH sides can be had at this 1250-step budget with this margin". **§8 stands unamended**; it is
cited above exactly as written, and nothing in this phase revisits it.

Phase 13 asks the smaller, honest question that a demonstration can answer: with the trade-off
accepted as real, does the constrained arm forget measurably less than the unconstrained one,
against the same validated noise floor? That is retention-gated by construction (D-06), and the
acquisition cost is reported as a **number in the 2×2** rather than as a hurdle — +0.380556 PPL,
paid and disclosed, not gated away.

**Why λ=0.01 is the headline (D-02):** because both axes move favorably at once. λ=100 nearly
eliminates forgetting (§8: retention 2.1082 vs anchor 2.1076, drift +0.0007) but destroys
acquisition (dialogue 16.2112, +11.77 vs λ=0) — that is half the phenomenon, a stability trophy
with the plasticity side hidden, and it is deliberately not the claim. The point of this phase is
that the trade-off is *favorable* at a small λ, not that forgetting can be made to vanish.

**ROADMAP wording superseded:** the roadmap describes Phase 13 as "λ=0 vs λ\*". There is no λ\* —
§8 recorded λ\* = None. Phase 13 runs λ=0 vs a **pre-chosen λ=0.01**, per D-02/D-09, and that
substitution is recorded here rather than silently absorbed into the roadmap's phrasing.

## Figures

**`results/phase13_forgetting_curve.png`** (VIZ-01) — both 4000-step arms, identical config
except λ. Left panel is the forgetting axis: naive climbs 2.11 → 8.52 while EWC rises once to
~3.9 and then stays flat for 3750 steps. Right panel is the acquisition companion (dialogue PPL,
**log** y-axis — the step-0 anchor is 31.90 and both arms land near 4.2/4.6, so a linear axis
collapses the entire arm separation into one pixel band). Data: the two committed arm CSVs, no
other source.

*Baseline-line note, stated once for the whole report:* the dashed horizontal reference on the
left panel is **2.1066**, the **v1.0 TinyStories headline** (full-val, unmasked). The curves
themselves are anchored at **2.107553**, the step-0 **frozen sub-bin** `retention_perplexity`
that every gate in Phases 12–13 uses. The two numbers are close by construction and are **not
interchangeable**: the dashed line is context for where the base model stood; the sub-bin anchor
is what the gate arithmetic is computed against. Every drift figure quoted in this report uses
the sub-bin anchor.

**`results/phase13_frontier.png`** (VIZ-04) — the stability–plasticity frontier, **six** labeled
points (λ = 0, 0.01, 0.1, 1, 10, 100) at the **1250-step sweep endpoints** (LR 9e-5, unmasked) —
*not* the 4000-step A/B arms; the figure carries that caveat in its own sub-caption. The elbow at
λ=0.01 is the D-02 argument in visual form: it recovers most of the retention loss for ~0.28
dialogue PPL, while λ≥10 buys the remainder at 2–4× the dialogue cost. Five points are read from
the retained sweep CSVs; the λ=0 point is the cited provenance exception recorded in the
pre-registration section above (its `retention_ppl` column was never logged by the Stage-2
driver).

Both figures are regenerable from committed CSVs alone via `scripts/plot_phase13.py`.

## Retention Samples

`results/phase13_retention_samples.md` (D-12) — retention-side continuations, deliberately not
dialogue transcripts, so the qualitative evidence targets exactly what the retention gate
measures. **Protocol:** both step-4000 endpoints sampled in ONE run of
`scripts/make_retention_samples.py` over ONE shared prompt set (10 held-out TinyStories stories
chosen by a seeded local `default_rng(1337)`, encoded through the frozen tokenizer, truncated to
their first 32 ids), warm sampling drawn from an explicit **per-prompt** `torch.Generator` seeded
`1337 + story_idx` and identical across arms, so each prompt is genuinely paired and an early stop
in one prompt cannot shift any later prompt's stream — reported as representative samples, never
cherry-picked, with proxies measured over all 40 generations rather than over the excerpts shown.

| arm | endpoint | eos (stop-id) termination | mid-story role-token leakage (8185/8186/8187) |
| --- | --- | --- | --- |
| naive (λ=0) | 4000 | 0/20 = 0.00 | **79** |
| EWC (λ=0.01) | 4000 | 0/20 = 0.00 | **69** |

The leakage counts are the measured negative result treated as threat 1 above: both arms drop
into dialogue mid-story, so these samples corroborate the *quantitative* retention gap only
weakly and explicitly do **not** support a qualitative retention claim. The zero eos fraction is a
budget artifact — 128 new tokens is far short of a full TinyStories story, so every completion is
truncated rather than eos-terminated — and is not an adherence signal either way.

## Evidence Index

Every number above traces to one of these committed artifacts, except the single cited λ=0
frontier point (provenance exception, recorded in `## Pre-Registration`):

| Artifact | Role |
| --- | --- |
| `results/phase13_naive/run.csv` | naive arm curve; 2×2 naive cells; within-run trajectory check |
| `results/phase13_ewc/run.csv` | EWC arm curve; 2×2 EWC cells; D-11 fresh-arm column |
| `results/finetune_prod.csv` | D-11 reproduction target (read-only) |
| `results/finetune_smoke_report.md` | Stage 0b noise floor + regime; §8 verdict; Stage 3 sweep table |
| `results/phase13_forgetting_curve.png` | VIZ-01 |
| `results/phase13_frontier.png` | VIZ-04 |
| `results/phase13_retention_samples.md` | D-12 qualitative evidence + adherence proxies |
| `scripts/finetune_ab.py` @ `c3d942e` | the pre-registered constants and gate that produced the verdict |

---

## Phase 15 Addendum — Fisher/Δ Correlation Verdict (D-09/D-10/D-11)

<!-- Phase 15 material, dated AFTER every Phase 13 result above. This section reports a
NEW measurement computed read-side from `results/phase15_norms.json`; it does not reopen
or amend Phase 13's pre-registered content — `## Pre-Registration`, `## Gate Verdict` and
`## Verdict` above stand exactly as recorded. Same separation register as Phase 14's
post-verdict ship decision: separate section, dated after the verdict, explicit that it
amends nothing above it. -->

**Recorded: 2026-08-02** — Phase 15 material appended to Phase 13 evidence.

### Pre-Registration (locked before the artifact existed)

Locked in `scripts/phase15_stats.py` at commit `0e1af98`; the artifact reader and BOTH verdict branches landed in the immediately following commit. No Phase-15 correlation existed at either commit, and `results/phase15_norms.json` did not exist.

| Constant | Value | What it fixes |
| --- | --- | --- |
| Statistic | Spearman ρ | D-10/D-12: rank-based, chosen over Kendall on readability grounds — both are already robust to the heavy-tailed Fisher magnitudes |
| Granularity | `N_CELLS` = 36 | D-10: 6 layers × 6 projections — exactly the cells the VIZ-03 figure draws |
| Pairing | `fisher_mean_per_cell vs (naive_ratio - ewc_ratio)` | D-10: the Δ-reduction pairing uses BOTH arms so the penalty's own effect is isolated |
| Predicted sign | `+1` (POSITIVE) | D-10: stated before the number; a negative or near-zero result is reported as plainly as a positive one |
| Seed | `1337` | D-12: a LOCAL `np.random.default_rng` only; the global RNG streams are never touched |
| Permutation resamples | `100000` | D-12 discretion, pinned so the p is byte-reproducible (measured 1.4 s at n = 36) |
| Bootstrap resamples | `10000` | D-12 discretion, pinned so the CI is byte-reproducible (measured 0.4 s at n = 36) |
| CI α | `0.05` | two-sided 95% percentile interval |
| Spearman method | `average_rank_pearson_fp64` | average (tie-corrected) ranks — deliberately NOT `continual/fisher.py::_spearman`'s ordinal transform |
| CI method | `percentile_bootstrap` | see the method note below |
| Gate rule | EWC dodges high-Fisher coordinates **iff** ρ > 0 **AND** the bootstrap CI excludes zero (`ci_lo > 0`); the boundary (`ci_lo == 0`) is a **FAIL** | D-11: the sign is gated, the magnitude is descriptive |

**Gate arbitration (pre-registered).** The **bootstrap CI is the load-bearing half of the gate**; the permutation p is **descriptive** and never overrides it — a small p alongside a CI that spans zero is still a MISS.

**Bootstrap method note (pre-registered).** The percentile bootstrap is known to be biased and anti-conservative at small n. BCa would correct that at real complexity cost; percentile was chosen for D-12's ~15-lines-of-numpy budget and the bias is named here rather than silently omitted or silently upgraded.

### Result

- Spearman ρ = **0.801544** (`average_rank_pearson_fp64`, n = 36)
- 95% CI = **[0.597984, 0.920291]** (`percentile_bootstrap`, 10000 resamples, seed 1337)
- Permutation p = **0.000010** (100000 shuffles, seed 1337) — descriptive only, per the gate arbitration above
- Degenerate (zero-variance) bootstrap resamples dropped: **0** of 10000
- Source artifact: `results/phase15_norms.json` @ git_sha `d1e9eee21062976c398474324a513269ea78846e`, built `2026-08-02`

### Verdict

**GATE PASSES** — the correlation carries the pre-registered positive sign and its 95% CI excludes zero.

The magnitude remains descriptive: *the sign is the falsifiable claim; the magnitude is reported honestly given n = 36 and is not itself pass/fail.* ROADMAP SC2's "showing EWC visibly dodging high-Fisher coordinates" wording is supported at the level the gate tests — the sign — and no further.

### Evidence Index Addendum

| Artifact | Role |
| --- | --- |
| `scripts/phase15_stats.py` @ `0e1af98` | the pre-registered rule, seed, sign and gate that produced this verdict |
| `results/phase15_norms.json` | the D-05 committed norms artifact — the 36 Fisher/Δ cell pairs this verdict is computed from |

