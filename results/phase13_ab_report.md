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

_Pending — filled by Plan 13-04 after both arms run._

## Reconciliation: §8 Search vs Phase-13 Demonstration

_Pending — filled by Plan 13-04 after both arms run._

## Figures

_Pending — filled by Plan 13-04 after both arms run._

## Retention Samples

_Pending — filled by Plan 13-04 after both arms run._
