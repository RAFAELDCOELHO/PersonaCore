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

_Pending — filled by Plan 13-04 after both arms run._

## Gate Verdict

_Pending — filled by Plan 13-04 after both arms run._

## D-11 Reproduction Cross-Check

_Pending — filled by Plan 13-04 after both arms run._

## Threats to Validity

_Pending — filled by Plan 13-04 after both arms run._

## Reconciliation: §8 Search vs Phase-13 Demonstration

_Pending — filled by Plan 13-04 after both arms run._

## Figures

_Pending — filled by Plan 13-04 after both arms run._

## Retention Samples

_Pending — filled by Plan 13-04 after both arms run._
