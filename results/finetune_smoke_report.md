# Fine-Tune Calibration Smoke Report (Phase 12 Plan 04 — D-01..D-07)

> **What these numbers are:** the pre-registered smoke decisions for the Stage-2 conversational
> fine-tune — budget, noise floor, masking verdict, LR*, λ* — each produced by a rule committed
> in `scripts/finetune_smoke.py` BEFORE any smoke number existed (git history is the
> pre-registration proof). **Frozen gate policy (§1):** dialogue val PPL = `masked_perplexity`
> on `data/dialog_val.bin` + `data/dialog_val_mask.bin`, block 256, dead ids forbidden
> (`undecodable_ids_mask`; role ids 8185-8187 decodable, never forbidden) — every gate, every
> arm, all stages. Retention PPL = `retention_perplexity` on the frozen
> `data/retention_val.bin` sub-bin. In-loop val_loss gates best-checkpoint selection only —
> never a gate. **What they are not:** comparable to the TinyStories headline (different
> corpus/register) or to any unmasked PPL.
>
> Step-0 row mechanism (TUNE-02): the v1.0 eval block logs NO step-0 row (12-01 pinned fact),
> so every arm CSV was PRE-SEEDED by the driver with a header + measured step-0 row before
> `train()` appended to it.

## Pre-Registration

| Constant | Value | Rationale |
| --- | --- | --- |
| K | 2 | chosen BLIND before any smoke number — deliberately conservative; no principled derivation exists at this budget; counterfactual k per gate below |
| CAL_MAX_STEPS | 5000 | Stage-0 calibration budget |
| SMOKE_STEPS | 1250 | locked from the slope rule (two-pass flow) |
| LR grid | 0.0003, 9e-05, 3e-05 | pretrain peak 3e-4 × (1, 0.3, 0.1) |
| λ grid | 0.01, 0.1, 1, 10, 100 | decade grid centered on 1 (mean-normalized Fisher ⇒ λ ≈ O(1) stiffness) |
| Noise seeds | 1337 / 2024 | Stage-0b seed pair |
| Slope rule | trailing-1000 improvement < 0.15 × first-1000 improvement | D-03 — TinyStories absolute band DROPPED |
| Cold-start cadence | every 25 steps; window = first 10% of budget | D-04 diagnostic rides Stage 1 |
| Batch / accum / block | 32 / 1 / 256 | grad_accum=1 sidesteps the λ/accum scaling class |

## Step-0 Anchors (embedded from results/retention_anchors.json — Pitfall 1)

| Key | Value | Tokens |
| --- | --- | --- |
| retention_ppl_subbin_step0 | 2.107553076833866 | 1,000,285 |
| retention_ppl_fullval_step0 | 2.1065480504616803 | 12,636,922 |
| dialogue val PPL at step 0 (anchor model, frozen gate policy) | 31.9039 | 270,203 |
| anchor fingerprint | step 49000, val_loss 0.7378001868724823 | git 3a46815da |

## Stage 0 — Budget Recalibration (D-03)

- Calibration run: masked arm, LR 9e-05, seed 1337, eval_interval 250, 5000 steps.
- dialog_ppl curve (step:ppl): 0:31.9039 250:5.0670 500:4.7628 750:4.6215 1000:4.5423 1250:4.4885 1500:4.4513 1750:4.4169 2000:4.4077 2250:4.3796 2500:4.3914 2750:4.3821 3000:4.3742 3250:4.3862 3500:4.3784 3750:4.3730 4000:4.3923 4250:4.3898 4500:4.4023 4750:4.3972 5000:4.4011
- Slope rule recommendation: **1250 steps** (capped at CAL_MAX_STEPS: False)
- Locked SMOKE_STEPS: **1250** (lock enforced by SystemExit when |recommended − locked| > 250)
- Measured wall-clock: 0.439 s/step including per-interval evals (36.6 min total)

## Stage 0b — Noise Floor (D-05)

Seed pair (1337 vs 2024), identical config (masked, LR 9e-05,
1250 steps):

| Quantity | Seed 1337 | Seed 2024 | Δ (floor) | Margin (K×Δ) |
| --- | --- | --- | --- | --- |
| end dialogue PPL | 4.470551 | 4.472255 | 0.001704 | 0.003408 |
| end retention PPL | 5.074896 | 5.005966 | 0.068930 | 0.137861 |

K = 2 was declared blind. **Counterfactual k per gate** (the k the observed decision delta
would have required at this floor):

| Gate | Observed decision delta vs floor | Counterfactual k |
| --- | --- | --- |
| Masking verdict (Stage 1) | separation +0.025223 vs Δ_dialog 0.001704 | k = 14.80 |
| LR 0.0003 retention gate | drift +6.631665 vs floor Δ_ret 0.068930 | k = 96.21 |
| LR 9e-05 retention gate | drift +3.847715 vs floor Δ_ret 0.068930 | k = 55.82 |
| LR 3e-05 retention gate | drift +2.807796 vs floor Δ_ret 0.068930 | k = 40.73 |
| λ=0.01 within-margin gate | Δdialog +0.284436 vs floor Δ_dialog 0.001704 | k = 166.92 |
| λ=0.1 within-margin gate | Δdialog +1.190155 vs floor Δ_dialog 0.001704 | k = 698.43 |
| λ=1 within-margin gate | Δdialog +2.769118 vs floor Δ_dialog 0.001704 | k = 1625.02 |
| λ=10 within-margin gate | Δdialog +6.109857 vs floor Δ_dialog 0.001704 | k = 3585.49 |
| λ=100 within-margin gate | Δdialog +11.765914 vs floor Δ_dialog 0.001704 | k = 6904.67 |

Undefinable-gate fallback check (§4): margin 0.003408 < total Stage-0 signal — gate definable, no fallback.

## Stage 1 — Masking Verdict (D-01) + Cold-Start Diagnostic (D-04)

Both arms: LR 9e-05, seed 1337, 1250 steps, eval_interval 25; scored with the frozen policy (§1):

| Arm | End dialogue PPL | End retention PPL |
| --- | --- | --- |
| masked training loss | 4.4706 | 5.0749 |
| unmasked training loss | 4.4453 | 5.9553 |

- Separation (masked − unmasked): +0.025223; margin K×Δ_dialog = 0.003408.
- Budget-validity check (user lock 2): |Δ| > margin — PASSED (no tie halt).
- **Verdict: unmasked** (unmasked wins only by beating masked by MORE than the margin; ties → masked).

Cold-start trigger evaluation (window = first 10% of budget, mechanical):

| Arm | val_loss first interval | val_loss at 10% budget | NaN/Inf cells | Trigger |
| --- | --- | --- | --- | --- |
| masked | 2.4861 | 1.7650 | 0 | not triggered |
| unmasked | 2.4754 | 1.7360 | 0 | not triggered |

Role-token embedding norms (wte rows 8185-8187):

| Arm | Role | Step 0 | First interval | At 10% budget | Final |
| --- | --- | --- | --- | --- | --- |
| masked | user | 1.9049 | 1.9034 | 1.9045 | 1.9169 |
| masked | assistant | 1.9009 | 1.9009 | 1.8803 | 1.7887 |
| masked | system | 1.9060 | 1.9059 | 1.9047 | 1.9037 |
| unmasked | user | 1.9049 | 1.9038 | 1.9033 | 1.9033 |
| unmasked | assistant | 1.9009 | 1.8998 | 1.8990 | 1.8832 |
| unmasked | system | 1.9060 | 1.9054 | 1.9165 | 1.9625 |

## Stage 2 — LR Sweep (D-02)

Arms on the unmasked winner, seed 1337, 1250 steps. Gates: retention collapse
(after-run sub-bin retention − step-0 anchor 2.1076 > K×Δ_ret = 0.137861) and
instability (NaN/Inf, or interval-to-interval dialog_ppl increase > K×Δ_dialog = 0.003408):

| LR | End dialogue PPL | End retention PPL (drift) | Unstable | Retention collapse | Passes | Provenance |
| --- | --- | --- | --- | --- | --- | --- |
| 0.0003 | 4.2034 | 8.7392 (+6.631665) | False | True | False | fresh run |
| 9e-05 | 4.4453 | 5.9553 (+3.847715) | False | True | False | fresh run |
| 3e-05 | 4.7771 | 4.9153 (+2.807796) | False | True | False | fresh run |

**Zero arms passed — the pre-registered §7(a) retention gate fired on all three, the driver
halted per §9, and the halt was surfaced at a blocking D-07 checkpoint** (CSVs committed at
the halt, 7aac9e3). LR\* = 9e-05 was then set by RECORDED USER OVERRIDE, not by the
pre-registered "lowest dialogue PPL among passing arms" rule — see the next section.

### Gate §7(a) Halt & Recorded User Override (D-07)

Why the gate fired on every arm: **gate §7(a) tests retention against a no-EWC baseline** —
the "near-zero forgetting" expectation it encodes presupposes the mechanism that only enters
in Stage 3. Fine-tuning the full model on dialogue without any anchor is EXPECTED to drift
off TinyStories. This is NOT a calibration failure; it is the central phenomenon Phase 12/13
exists to study (observed drifts: k = 40–96× the noise floor — see the counterfactual-k
table).

**User decision (override recorded, gate NOT amended):** proceed with the λ sweep at
LR 9e-5. The drift measured at this LR — **+3.847715 retention drift (retention PPL 5.9553
vs anchor 2.1076), dialogue PPL 4.4453** — is formally recorded as the **"collapse without
EWC" baseline that Stage 3 must beat**. The pre-registered gates in
`scripts/finetune_smoke.py` stand unmodified; the override lives in the separately committed
`scripts/finetune_smoke_stage3_override.py` (committed before any λ number existed), which
re-evaluates the Stage-2 gate arithmetic verbatim, refuses to run if any arm passes, and
then applies the pre-registered §8 rules unchanged.

## Stage 3 — λ Sweep (EWC-03)

λ arms on the LR\* = 9e-05 unmasked config (LR fixed by the recorded user override above);
λ=0 reference = the LR\* run itself (identical config by D-03 construction) — i.e. the
recorded "collapse without EWC" baseline (dialogue 4.4453, retention 5.9553). λ\* rule: largest λ within K×Δ_dialog = 0.003408
of λ=0's end dialogue PPL (4.4453); demonstrability guard: retention(λ\*)
beats retention(λ=0) (5.9553) by MORE than Δ_ret = 0.068930:

| λ | End dialogue PPL (vs λ=0) | End retention PPL (gain vs λ=0) | Final EWC penalty | Within margin | Beats retention floor |
| --- | --- | --- | --- | --- | --- |
| 0.01 | 4.7298 (+0.284436) | 3.7813 (+2.173968 vs λ=0) | 0.1067 | False | True |
| 0.1 | 5.6355 (+1.190155) | 3.0057 (+2.949616 vs λ=0) | 0.1324 | False | True |
| 1 | 7.2144 (+2.769118) | 2.7734 (+3.181886 vs λ=0) | 0.1954 | False | True |
| 10 | 10.5552 (+6.109857) | 2.1351 (+3.820198 vs λ=0) | 0.2192 | False | True |
| 100 | 16.2112 (+11.765914) | 2.1082 (+3.847032 vs λ=0) | 0.0766 | False | True |

- Within-margin candidates: []; margin-largest λ = None; boundary extensions: 0.
- **EWC not demonstrable at this budget** (no λ satisfies both the within-margin rule and the retention demonstrability guard) — surfaced, never massaged (pre-registered §8 all-fail outcome: λ\* = None, demonstrable = False).
- Every λ arm beat the collapse baseline on retention (λ=100 essentially eliminates forgetting: retention 2.1082 vs anchor 2.1076, drift +0.0007) — but none stayed within the K×Δ_dialog = 0.003408 dialogue margin of λ=0, so the joint §8 rule produces no λ\*. The stability–plasticity trade-off is real and measured; what failed is the demonstration that BOTH sides can be had at this 1250-step budget with this margin.

## Proposed Production Config (Plan 12-05 input)

| Knob | Value |
| --- | --- |
| Training loss | unmasked |
| LR | 9e-05 |
| λ | 0 (EWC not demonstrable) |
| PROD_MAX_STEPS | 4000 (≈ ~29 min at the measured 0.439 s/step) |
| Seed / batch / accum | 1337 / 32 / 1 |

## Verdict

PENDING — user decision at the D-07 blocking checkpoint.
