# Phase 12: Stage-2 Conversational Fine-Tune - Research

**Researched:** 2026-07-31
**Domain:** Full fine-tune of a from-scratch 13.9M GPT on PersonaChat bins with calibrated EWC, sequential pre-registered calibration smoke, retention telemetry (M3/MPS fp32, zero new dependencies)
**Confidence:** HIGH (every seam verified line-by-line against the shipped code this session; λ/budget numbers are what the smoke exists to measure)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Masking decision rule (resolves Phase 11 D-02)**
- **D-01:** Two short fine-tunes (masked loss vs train-on-everything) compared on dialogue
  val PPL; **tie goes to masked**. Unmasked is adopted only if it beats masked by MORE than
  the pre-registered margin (see D-05 noise floor). Research ARCHITECTURE prescribes masking;
  the smoke only overturns it on clear evidence. Rule is pre-registered — no per-stage human
  stop needed (see D-07).

**LR selection**
- **D-02:** 3-point log-spaced LR sweep (pretrain-peak ×1, ×0.3, ×0.1) run on the winning
  mask arm. Selection = lowest dialogue val PPL **passing two pre-registered measurable
  gates** — never a post-hoc visual call on a loss curve:
  1. **Retention proxy:** `retention_perplexity()` (DEBT-02) on a small held-out base-task
     sample, measured before and after each short run. "Collapse" = retention PPL degrades
     past a pre-registered threshold derived from the D-05 noise-floor logic (no invented
     numbers).
  2. **Instability:** mechanically defined — loss diverges (NaN/Inf) OR dialogue val PPL is
     non-monotonic across the short run's own logging intervals. Not a human eyeballing a plot.
  **Fallback pre-registered:** if defining these gates cheaply isn't feasible within the smoke
  budget, say so explicitly and fall back to a blocking user checkpoint on the raw curves
  (masking-smoke register) — never let "no instability" become a silent subjective call.

**Smoke ordering & budget**
- **D-03:** **Sequential, recalibrated budget.** Order: budget recalibration → masking (D-01)
  → LR sweep (D-02) → λ sweep (EWC-03), each stage running on the prior stage's winner —
  fewest confounds. The short-run budget is **recalibrated for the dialogue corpus** using the
  v1.0 D-07 method (long enough that val-PPL separation exceeds seed noise), NOT assumed to be
  the TinyStories-calibrated 2500 steps.

**Role-token cold-start (ids 8185–8187)**
- **D-04:** **Diagnostic with escalation trigger, measured framing.** Log early-step loss AND
  role-token embedding norms at a **fixed cadence** (every N steps through the first ~10% of
  the smoke budget) during the masking smoke, so there's an actual before/after trajectory —
  not a single post-hoc "yes it spiked" observation. Pre-registered trigger: violation of the
  same D-02 instability gates (NaN/Inf, non-monotonic recovery) escalates to a mitigation
  lever (row reinit to live-row mean, targeted warmup for the three rows, or other — chosen at
  escalation time). **Any mitigation is evaluated with its own before/after comparison against
  the un-mitigated diagnostic run** — no claim of "the mitigation worked" without the number
  showing the un-mitigated baseline it improved on. No mitigation is built unless triggered.

**Noise floor & margins**
- **D-05:** **Seed-pair noise run:** one smoke configuration run twice with different seeds at
  the recalibrated budget; the observed dialogue-val-PPL and retention-PPL deltas ARE the
  noise floor. Gate margins = k× that delta. **k is pre-registered with a stated reason:**
  k=2 is declared a deliberately conservative default chosen blind, before seeing any smoke
  result (no principled derivation is available at this budget — say so explicitly). The
  committed report (D-06) must also record, for each gate, **what k the actually-observed
  noise floor would have required**, alongside the verdict — keeping k defensible as "chosen
  blind" rather than "chosen because it validated the pick."

**Smoke report artifact**
- **D-06:** **One committed smoke report** — thin script + `results/` markdown, same register
  as Phase 11's `results/inflation_report.md` — recording, for EACH of the four smoke
  decisions (masking threshold, LR stability gates, budget-recalibration noise measurement,
  cold-start spike diagnostic), the raw numbers and the verdict. NOT four different logging
  styles scattered across code comments, terminal prints, and CONTEXT prose. Phase 15's
  honest-numbers writeup cites this report directly, the same way it cites the inflation
  report.

**Checkpoint cadence**
- **D-07:** Pre-registered rules **auto-proceed stage-to-stage** (that's what pre-registration
  buys — the masking verdict and LR pick don't each need a human stop). **ONE blocking user
  checkpoint before the production fine-tune**, presenting the full smoke report (including
  the λ sweep results / λ* pick, since the λ sweep is the smoke sequence's final stage).
  **EXCEPTION:** any violated gate mid-sequence (instability, retention collapse, cold-start
  escalation trigger) **halts immediately** and surfaces to the user right then — never
  bundled silently into the final report.

### Claude's Discretion

Areas offered but not selected for discussion — decide from research, within the pre-registration
discipline above:
- **λ sweep design details** (EWC-03): grid size/range within the reported 0.1–10⁶, per-point
  budget (the D-03 recalibrated short budget), and the concrete stability–plasticity λ* pick
  rule — presented for confirmation at the D-07 blocking checkpoint. Sweep logs retained for
  Phase 13's frontier plot (requirement text).
- **Production run budget & stopping policy**, and what evidence constitutes dialogue-format
  adherence (transcript count, prompt set) for TUNE-01.
- **Conversational-base artifact contract**: best-checkpoint criterion, embedded extras
  (fisher/theta_star/ewc_lambda per research ARCHITECTURE), naming/location, slim export, and
  whether the production run doubles as Phase 13's EWC arm (coordinate with Phase 13's
  identical-seed requirement).
- **`stop_ids` wiring** in `generate()` (Phase 11 D-03: lands here, additive, default
  `{eos_id}`) — needed for curated transcripts.
- Mechanics: retention-proxy sample size, cold-start logging cadence N, CSV/file naming
  (new per-run CSV files per research — never append columns to v1.0 `run.csv`).

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope. (The unselected gray areas — λ sweep design,
production stopping, conv-base artifact — are in-phase and delegated to Claude's discretion
above, not deferred to other phases.)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEBT-01 | `run.csv` tokens column counts true tokens (×`block_size` fix) | **Complete (pre-work, commit `ca14a89`)** — verified in `loop.py:337-339` this session: `tokens_per_step = batch_size × grad_accum × block_size`. Pinned by `tests/test_run_csv_tokens.py`. No plan work; the success criterion is already TRUE. |
| DEBT-02 | Dead-id `forbid_ids` policy frozen for all retention-PPL curve points | **Complete (pre-work, commit `ca14a89`)** — `retention_perplexity()` in `evaluation/perplexity.py:83-105` is the ONLY sanctioned curve-point PPL (masked policy frozen 2026-07-31); pinned by `tests/test_retention_ppl.py`. Consumed as-is (see Anchor Semantics pitfall). |
| EWC-03 | λ log-scale sweep, λ* off the stability–plasticity tradeoff, sweep logs retained | λ sweep design prescribed below (grid, per-arm budget, pre-registered λ* rule, boundary-extension rule); `EWCPenalty` + cached Fisher (`checkpoints/fisher_tinystories.pt`, N=2000, spearman_half 0.989, mean-normalized) verified ready; accum-divide/device pitfalls mapped. |
| TUNE-01 | Full fine-tune of `best.pt` through v1.0 `train()` to dialogue-format adherence | Loop-seam gap analysis below (masked-batch + retention-telemetry seams needed — additive, golden-trajectory protected); production run design, transcript protocol via `generate()` + `stop_ids`, conv-base artifact contract prescribed. |
| TUNE-02 | Retention PPL vs 2.1066 anchor at every eval interval from step 0, per-run/per-arm CSVs | Retention sub-bin design + `extra_eval_fns` loop seam prescribed; anchor-semantics finding (masked retention ≠ unmasked 2.1066 — step-0 anchor must be measured) documented; CSV discipline (per-run fieldnames, `results/` retention for Phase 13). |
</phase_requirements>

## Summary

This phase is almost entirely **orchestration of verified, shipped machinery** — nothing
mathematically new gets built. `train()` (with the EWC `penalty_fn` splice live since Phase 10),
`EWCPenalty` + the cached production Fisher, `get_batch_memmap_masked`, `retention_perplexity()`,
and the `run_ablations.py` calibrated-cohort pattern all exist and are test-pinned. The phase's
real work is (1) two small **additive seams** the current `train()` lacks, (2) a disciplined
**sequential smoke** (~12 short runs) with every gate pre-registered, and (3) the production run
plus its report/transcript/artifact deliverables.

The single most important integration finding: **the current `train()` cannot run this phase
as-is.** Its `train_bin` branch hardcodes unmasked `get_batch_memmap` (loop.py:287-290), and
there is no way to log retention PPL per eval interval (the ARCHITECTURE-planned `extra_val_bins`
seam was never implemented — only `penalty_fn`/`checkpoint_extra` landed in Phase 10). "Untouched
v1.0 `train()`" (TUNE-01) must be read the way every prior phase read it — the DEBT-01 precedent:
**additive default-`None` kwargs whose defaults reproduce the v1.0 trajectory bit-identically
against `tests/fixtures/golden_trajectory_v1.json`**, with all ~250 existing tests green. The
converged v2.0 ARCHITECTURE research (canonical, do-not-re-litigate) explicitly plans exactly
these additive loop changes.

Second key finding: **the 2.1066 anchor and the retention curve are different quantities.**
2.1066 is the *unmasked* full-val headline; `retention_perplexity()` applies the dead-id logits
mask, which renormalizes the softmax over ~550 live ids and mathematically lowers PPL. And a full
TinyStories-val sweep (12,636,923 tokens ≈ 49k single-window forwards) is far too slow to run per
eval interval — a fixed retention **sub-bin** is required. So the curve's true anchor is the
**measured step-0 masked retention PPL on the frozen sub-bin**, with 2.1066 recorded alongside as
the historical headline reference. Measuring both anchors (sub-bin and full-val, masked) at step 0
must be an explicit early task, or every downstream figure (VIZ-01's dashed 2.1066 line) will
mislead.

**Primary recommendation:** Plan the phase as: (Wave 0) additive loop/eval/generation seams +
tests + retention sub-bin + anchors → (Wave 1) sequential smoke via a `run_ablations.py`-style
driver writing one committed smoke report → (D-07 blocking checkpoint) → (Wave 2) production
fine-tune + transcripts + conv-base artifact.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Masked/unmasked batch drawing | Data path (`training/data.py`) | — | Already shipped (Phase 11); masking lives entirely in targets via `-100` (LOCKED `forward` untouched) |
| Masked-batch + retention telemetry seams | Training loop (`training/loop.py`) | — | Only the loop constructs `batch_fn` and the CSVLogger; additive kwargs, golden-trajectory protected |
| EWC penalty | Training loop via `penalty_fn` | `continual/ewc.py` | Seam live since Phase 10; penalty joins base_loss BEFORE `/accum` (verified loop.py:149-151) |
| Dialogue val PPL (gates) + retention PPL (curves) | Evaluation (`evaluation/perplexity.py`) | — | Deterministic sweeps are the only gate-grade numbers; new `masked_perplexity()` is additive here |
| Smoke sequencing, seeds, gate verdicts | Driver script (`scripts/`) | — | `run_ablations.py` precedent: driver owns `seed_everything` before each explicit-model build |
| Smoke report | Thin script + `results/*.md` | — | `inflation_report.md` register (D-06); Phase 15 cites it verbatim |
| Transcript generation / turn stopping | Generation (`generation/core.py`) | `dialogue/serialize.py` | `stop_ids` additive kwarg; prompts rendered through the Phase 11 serialization path |
| Conv-base checkpoint + slim export | Checkpoint (`checkpoint.py`) | — | Open-dict `**extra` carries fisher/θ*/λ; `export_slim` unchanged for the Phase 14 substrate |

## Standard Stack

### Core

**Zero new dependencies.** Everything rides the existing pinned stack — this is a project
constraint (zero-budget, from-scratch, offline) and a verified fact of the plan below.

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| torch | 2.7.1 (verified in `.venv` this session) | training, EWC penalty, eval sweeps | Project-pinned; MPS fp32 primary path `[VERIFIED: .venv probe]` |
| numpy | 2.x | memmap bins, sub-bin build | Existing dependency `[VERIFIED: in use]` |
| pytest | 8.x | seam tests | Existing dev dependency; `make test` `[VERIFIED: Makefile]` |
| Python | 3.11.15 in `.venv` | runtime | Mandatory 3.11 venv per CLAUDE.md `[VERIFIED: .venv probe]` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Additive loop kwargs | Post-hoc retention from per-eval checkpoints | Explicitly forbidden by TUNE-02 ("not post-hoc reconstruction"); also ~166 MB/checkpoint × every interval |
| Additive loop kwargs | Side-effecting `penalty_fn` wrapper that logs retention | Abuses the loss seam, runs inside autocast mid-micro-batch, leaves model in eval mode — rejected |
| Deterministic `masked_perplexity()` gate metric | `estimate_loss` (20 random batches) | Random-batch noise contaminates pre-registered margins; deterministic sweep costs <1 min on 638K-token dialog val |

## Package Legitimacy Audit

Not applicable — this phase installs **no** external packages. All work uses the already-pinned,
already-installed environment (torch 2.7.1, numpy, pytest verified present in `.venv`).

## Architecture Patterns

### System Architecture Diagram

```
                          ┌── SMOKE SEQUENCE (D-03, sequential, each stage on prior winner) ──┐
                          │                                                                    │
 best.pt ─────────────────┤  Stage 0  budget recalibration (1 run, D-07 method)               │
 (anchor, val_loss 0.7378)│  Stage 0b seed-pair noise run (2 runs → noise floor, D-05)        │
                          │  Stage 1  masked vs unmasked (2 runs) + cold-start diagnostic     │
 fisher_tinystories.pt ───┤  Stage 2  LR sweep {3e-4, 9e-5, 3e-5} on mask winner (≤3 runs)    │
 (N=2000, mean-normalized)│  Stage 3  λ sweep {0.01..100 log grid} on LR winner (~5 runs)     │
                          │           λ=0 point = Stage-2 winner run (reused, same config)    │
 dialog_{train,val}.bin ──┤                                                                    │
 + *_mask.bin (Phase 11)  └────────────► results/finetune_smoke_report.md (D-06) ─────────────┘
                                                        │
                                          [D-07 BLOCKING USER CHECKPOINT]
                                                        │
                                                        ▼
        train(model=GPT←best.pt, train_bin=dialog_train.bin, train_mask_bin=...,
              penalty_fn=EWCPenalty(F, θ*, λ*), extra_eval_fns={retention_ppl, dialog_ppl,
              ewc_penalty}, checkpoint_extra={fisher, theta_star, ewc_lambda, fisher_meta})
                                                        │
                 ┌──────────────────────────────────────┼───────────────────────────────┐
                 ▼                                      ▼                               ▼
   results/finetune_prod.csv               checkpoints/convbase_{latest,best}.pt   curated transcripts
   (retention curve from step 0,           → export_slim → convbase_slim.pt        (generate + stop_ids,
    TUNE-02 → Phase 13 figures)              (Phase 14 LoRA substrate)              committed, TUNE-01)
```

### Loop-Seam Gap Analysis (the load-bearing finding)

Verified against `src/personacore/training/loop.py` this session:

| Needed by this phase | Exists today? | Evidence |
|---|---|---|
| EWC penalty per micro-batch, before `/accum` | ✅ `penalty_fn` (Phase 10) | loop.py:149-151 — `assemble_loss(base_loss, (penalty_fn(model),))` then `total / accum` |
| Fisher/θ*/λ in every saved checkpoint | ✅ `checkpoint_extra` | loop.py:388/410/436 splat |
| True-token `tokens` column | ✅ DEBT-01 landed | loop.py:337-339 includes `× model_cfg.block_size` |
| Masked dialogue batches through `train()` | ❌ | loop.py:287-290 hardcodes `get_batch_memmap`; no mask kwarg |
| Retention PPL (or any extra metric) per eval interval into the CSV | ❌ | `CSV_FIELDNAMES` module constant (loop.py:49); no `extra_val_bins`/hook; ARCHITECTURE Pattern 5 planned it but Phase 10 only shipped `penalty_fn` |

**Resolution (prescriptive):** two additive kwargs on `train()`, both default `None` ⇒ bit-identical
v1.0 behavior, protected by the existing golden-trajectory fixture
(`tests/fixtures/golden_trajectory_v1.json`) exactly as the DEBT-01 telemetry edit was:

1. **`train_mask_bin=None`** — when set (requires `train_bin`), the memmap branch's `batch_fn`
   draws via `get_batch_memmap_masked(train_bin, train_mask_bin, ...)`. Optionally the symmetric
   **`val_mask_bin=None`** routes `estimate_loss`'s val draws through the masked batch fn so the
   in-loop `val_loss` (which gates `best.pt` selection) measures assistant-token CE under the same
   frozen policy for every arm.
2. **`extra_eval_fns=None`** — `dict[str, Callable[[model], float]]`; at each eval interval the
   loop appends one CSV column per key. Per-run fieldnames = `CSV_FIELDNAMES + sorted(extras)`
   computed at `CSVLogger` construction (never appended to an existing file — anti-pattern 3).
   This one seam carries `retention_ppl` (TUNE-02), `dialog_ppl` (gates), `ewc_penalty`
   (Pitfall-8 ratio diagnostics), and `role_norm_{user,assistant,system}` (D-04 cold-start),
   because each is just a deterministic `(model) -> float`.

Both seams are exactly what the converged ARCHITECTURE research pre-approved ("`+penalty_fn`,
`+extra_val_bins` — ADDITIVE"; "MODIFIED (additive)"). Do not re-litigate; do not build a second
training loop.

**Seam discipline for `extra_eval_fns` (pin with tests):** fns must be deterministic and RNG-free
(all four above are — `retention_perplexity`/`perplexity` consume no RNG; `EWCPenalty` is a pure
function of params; norms are reads). The loop must restore `model.train()` after running them
(`perplexity()` sets `model.eval()` and does NOT restore — verified perplexity.py:55). Defensive:
wrap the extras block in the existing `_rng_state()`/`_restore_rng` snapshot so resume-equality
survives even a future non-pure fn.

### Recommended Project Structure (additions only)

```
src/personacore/
├── training/loop.py           # MODIFIED (additive): +train_mask_bin, +val_mask_bin, +extra_eval_fns
├── evaluation/perplexity.py   # MODIFIED (additive): +masked_perplexity() (deterministic dialogue-val PPL)
├── generation/core.py         # MODIFIED (additive): +stop_ids (default None ⇒ {eos_id}, Pattern 4)
scripts/
├── build_retention_bin.py     # run-once: doc-level subsample of data/val.bin → data/retention_val.bin
├── finetune_smoke.py          # sequential smoke driver (run_ablations.py register) → smoke report
├── finetune_dialog.py         # production run driver (post D-07 checkpoint)
├── make_transcripts.py        # curated transcripts via generate()+stop_ids (or folded into finetune_dialog)
results/
├── finetune_smoke_report.md   # D-06 committed report (inflation_report.md register)
├── ft_*.csv                   # per-arm smoke/sweep CSVs (tracked — Phase 13 frontier/forgetting inputs)
├── finetune_prod.csv          # production per-run CSV (tracked)
└── transcripts.md             # curated dialogue transcripts (TUNE-01 evidence)
tests/
├── test_masked_train_seam.py  # mask-bin batch_fn routing; defaults ⇒ v1.0 identity (golden trajectory)
├── test_extra_eval_fns.py     # extra columns logged; model back in train mode; None ⇒ identical CSV
├── test_masked_perplexity.py  # hand-fixture oracle: CE summed over mask=1 targets only; denominator exact
└── test_stop_ids.py           # default ≡ v1.0 EOS behavior; stops-without-yield on any stop id
```

### Pattern 1: Retention sub-bin + measured anchors (TUNE-02 made affordable and honest)

**What:** a run-once script builds `data/retention_val.bin` — a **document-level** (eos-boundary)
subsample of TinyStories `data/val.bin`, ~0.5–1.0M tokens (discretion: recommend ~1.0M ≈ 3.9k
windows). Frozen for the whole milestone; every curve point on every arm uses
`retention_perplexity(model, retention_val.bin, 256, device, tok)`.

**Why:** full val is 12,636,923 tokens ≈ 49,364 single-window forwards per point — minutes per
eval interval, dominating wall-clock (PITFALLS Performance Traps flagged exactly this). The
sub-bin brings a point to roughly a minute or less on MPS (estimate — the smoke measures it).

**Anchors (must be measured, step 0, before any training):**
- `retention_perplexity(best.pt, retention_val.bin)` → **the curve anchor** (masked, sub-bin)
- `retention_perplexity(best.pt, val.bin)` → full-val masked reference (relates sub-bin to full)
- 2.1066 (unmasked, full-val) → recorded as the historical headline reference only

All three land in the smoke report so Phase 13 (VIZ-01's dashed line) and Phase 15 can state
precisely what each number is. See the Anchor Semantics pitfall.

### Pattern 2: Deterministic masked dialogue-val PPL as THE gate metric

**What:** `masked_perplexity(model, bin_path, mask_path, block_size, device, forbid_ids=None)` —
mirrors `perplexity()`'s non-overlapping-window sweep, additionally opens the mask memmap, sets
shifted targets to `-100` where mask==0, uses `F.cross_entropy(reduction="sum", ignore_index=-100)`
and the exact count of scored (mask==1, shifted) targets as the denominator. Dialog val = 637,633
tokens ≈ 2.5k windows → well under a minute per call.

**Why:** D-01/D-02/D-05 gates compare arms against k×noise-floor margins; `estimate_loss`'s
20-random-batch mean would inject eval sampling noise into margins that are supposed to measure
*training* noise. Also the masked and unmasked arms train different objectives — their in-loop
`val_loss` values are incommensurable unless the *evaluation* policy is fixed independently of the
*training* arm. **Freeze one policy for every gate and every arm:** dialogue val PPL = assistant-token
(masked) PPL over `dialog_val.bin`/`dialog_val_mask.bin`, forbid-ids policy pre-registered once
(recommend: apply `undecodable_ids_mask`, mirroring the DEBT-02 rationale — the metric reflects
what the deployed system experiences; role ids 8185–8187 are in `special_tokens`, hence decodable
and never forbidden — verified ARCHITECTURE §Pattern 3 / `text.py` formula).

### Pattern 3: Sequential smoke as a `run_ablations.py`-register driver

**What:** one thin no-CLI driver (`scripts/finetune_smoke.py`) runs the D-03 sequence. Concrete
run inventory (~12 short runs + reuse):

| Stage | Runs | Config | Output |
|---|---|---|---|
| 0 budget recalibration | 1 | masked arm, LR 9e-5 (mid-sweep — stable by construction), eval_interval small; D-07 flatten rule adapted to dialogue val | recalibrated `SMOKE_STEPS` |
| 0b noise floor | 2 | same config, seeds 1337/2024, `SMOKE_STEPS` | dialogue-val-PPL Δ and retention-PPL Δ = noise floor; margins = 2×Δ (k=2, chosen blind per D-05) |
| 1 masking | 2 | masked vs unmasked, same LR/seed/budget | mask verdict (tie→masked); cold-start diagnostic rides these runs |
| 2 LR sweep | ≤3 | winner mask arm × {3e-4, 9e-5, 3e-5} (pretrain peak = 3e-4, verified `pretrain_tinystories.py:52`); the 9e-5 arm may reuse a Stage-1 run if config-identical (pre-register the reuse) | LR* = lowest dialogue val PPL passing both D-02 gates |
| 3 λ sweep | ~5 | LR* arm × λ ∈ {0.01, 0.1, 1, 10, 100}; λ=0 point = the LR* run itself (reused — identical config by D-03 construction) | λ* + per-arm CSVs retained in `results/` |

Driver discipline copied from `run_ablations.py` (verified): `preflight_device(strict=True)` gate
first; `seed_everything(SEED)` immediately before each explicit `GPT(...)` build (train() only
self-seeds default models — the driver owns the seed AND the data order, since the batch sampler
draws from the global numpy RNG); one shared `TrainConfig` per stage with only the swept knob
varying; per-arm CSVs to tracked `results/` (the `abl_*.csv` precedent — Phase 13's frontier and
forgetting figures read these, and `logs/` is gitignored).

**Model loading per arm:** fresh `GPT(ModelConfig(**best_blob["model_config"]))` +
`load_state_dict(best_blob["model"])` per arm — never share a mutated model across arms, never
`resume_from=best.pt` (that would restore the pretrain optimizer moments and step counter —
PITFALLS P4; fine-tune always starts a fresh AdamW at step 0).

### Pattern 4: λ sweep design and λ* pick rule (Claude's-discretion, pre-registered)

**Grid:** λ ∈ {0.01, 0.1, 1, 10, 100} log-scale, 5 points, plus the reused λ=0 reference.
Rationale: the Fisher is **mean-normalized** (mean(F)=1 over all 13.9M coords — verified
`fisher.py` D-01/D-02 and proof [c] of the estimation script), so λ reads as stiffness relative
to an average parameter and the literature's raw 0.1–10⁶ spread (an artifact of unnormalized,
variant-dependent Fisher magnitudes — van de Ven) collapses toward O(1). A decade-spaced grid
centered on 1 brackets the plausible region. **Boundary-extension rule (pre-registered):** if λ*
lands on a grid endpoint, extend one decade in that direction and re-run one arm before locking.

**λ* pick rule (pre-registered, measurable):**
λ* = the **largest** λ whose dialogue val PPL (masked deterministic sweep, end of run) is within
the k×noise-floor margin of the λ=0 arm's — i.e., maximum stiffness at negligible plasticity
cost. **Demonstrability guard:** retention PPL at λ* must beat the λ=0 arm's retention by more
than the noise floor; if no λ satisfies both, that is a finding to surface at the D-07 checkpoint
(fallback framing: "EWC not demonstrable at this budget"), not a number to massage.

**Diagnostics per arm (Pitfall 8):** log `ewc_penalty` as its own CSV column via
`extra_eval_fns` (call `penalty_fn(model)` — cheap, deterministic). Healthy: penalty within ~1–2
orders of magnitude of task loss after warm-in; ratios of 1e-6 or 1e+4 are diagnoses recorded in
the report, not silent.

### Pattern 5: Cold-start diagnostic via the same seam (D-04)

Role rows 8185–8187 of the tied `wte`/`lm_head` tensor are **not random-init** — they received
pretraining gradient through the tied head's softmax denominator, so they start as
trained-to-be-suppressed directions (PITFALLS 13). The diagnostic:
`extra_eval_fns["role_norm_user"] = lambda m: m.wte.weight[8185].norm().item()` (etc. for
8186/8187) — attribute name `wte` verified in `gpt.py:159`. On the two Stage-1 masking runs, set
`eval_interval = N` (recommend N=25) and do **not** attach the expensive retention fn per-interval
on those runs (D-02 requires retention only before/after each short run — the per-interval
retention requirement applies to the λ arms and production, at a coarser eval_interval like the
v1.0 250). This resolves the two-cadence tension with a single-cadence seam: cadence and attached
fns are per-run choices.

Escalation trigger = the same D-02 instability gates on the early-window trajectory. Mitigation
levers (only if triggered, evaluated against the un-mitigated run): reinit rows 8185–8187 to the
live-row mean, or a targeted warmup for those rows.

### Pattern 6: `stop_ids` in `generate()` (Phase 11 D-03 lands here)

Additive kwarg: `stop_ids=None` ⇒ `{eid}` (exact v1.0 behavior); membership check replaces
`tok == eid`; stop-without-yield (D-05 idiom, core.py:69) unchanged. `generate()` is not on the
LOCKED list. Transcripts pass `stop_ids={8184, 8185}` (eos + `<|user|>`) so generation halts when
the model starts a hallucinated user turn. Test: default ≡ v1.0 EOS behavior bit-for-bit.

### Pattern 7: Production run + conversational-base artifact contract (discretion, recommended)

- **Config:** winner mask arm, LR*, λ*, `train_mask_bin` + `val_mask_bin` set, fresh AdamW,
  `TrainConfig` defaults otherwise (weight_decay 0.1, grad_clip 1.0, warmup 100,
  **grad_accum_steps=1** — sidesteps the λ/accum scaling class entirely; batch 32 mirrors the
  pretrain script). Budget: cap ~3,000–5,000 steps (≈5–8 epochs of the 5.26M-token corpus at
  8,192 tokens/step; ~642 steps/epoch) with best-checkpoint selection doing the stopping —
  overfitting past best is expected (PITFALLS 15) and is itself curve material. Present the exact
  budget at the D-07 checkpoint with the smoke wall-clock numbers.
- **Checkpoints:** `checkpoints/convbase_latest.pt` + `convbase_best.pt` (best = lowest masked
  dialogue val loss via the existing Seam-3 best tracking);
  `checkpoint_extra={"fisher": ..., "theta_star": ..., "ewc_lambda": λ*, "fisher_meta": ...}` so
  resume is self-contained (anti-pattern 2 — resume must never depend on the Fisher cache
  sidecar). Fisher loaded once from `checkpoints/fisher_tinystories.pt` via `load_fisher`
  (fingerprint-checked against `best.pt`); θ* snapshot from the loaded anchor via
  `named_parameters()` (tied tensor appears once — the estimation-script discipline).
- **Slim export:** `export_slim(convbase_best.pt, convbase_slim.pt)` — the Phase 14 LoRA
  substrate under the LOCKED `weights_only=True` contract.
- **Phase 13 coordination:** design the production run to double as the EWC arm of DEMO-04 —
  record seed, data-order provenance (seed_everything before build), full config, and λ* in the
  report so Phase 13 can run the identical-seed λ=0 twin. This halves Phase 13's compute and
  guarantees the arms differ in exactly one bit.
- **Format-adherence evidence (TUNE-01):** ~10–20 transcripts, committed to
  `results/transcripts.md` (the `samples.md` register): prompts = held-out val episodes' persona
  + first user turn rendered through the Phase 11 `dialogue/serialize.render_document`/
  `encode_dialogue` path ending with `<|assistant|>`; decode greedy AND seeded-sampled with
  `forbid_ids` + `stop_ids={eos, user}`; report simple measurable proxies alongside (fraction of
  generations terminating on a stop id rather than max_new_tokens; no raw role-token leakage
  mid-utterance), plus the masked dialogue val PPL number.

### Anti-Patterns to Avoid

- **A second training loop or a subclassed trainer:** everything rides `train()` + additive
  kwargs. The golden-trajectory fixture is the enforcement mechanism.
- **Appending columns to `logs/run.csv` or reusing `CSV_FIELDNAMES`:** per-run files with per-run
  fieldnames (`CSVLogger` raises on unknown keys; header written once per file).
- **Gates computed from `estimate_loss` random batches:** deterministic sweeps only.
- **`resume_from=best.pt` to "load the anchor":** loads pretrain optimizer/step/RNG — the P4
  boundary bug. Load weights via `load_state_dict`; fresh optimizer.
- **Mixing masked and unmasked, or sub-bin and full-bin, PPL points in one curve** (Pitfall 9):
  one blessed fn + one frozen bin per metric, forever.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Fine-tune loop (AMP order, accum, resume, best-tracking) | new trainer | `train()` + additive kwargs | 250-test-pinned, kill+resume bit-identical, best.pt never regresses |
| EWC penalty + Fisher | anything new | `EWCPenalty` + `checkpoints/fisher_tinystories.pt` via `load_fisher` | Fail-loud validated, device-moved-once, penalty≡0 at anchor proven on real weights; one N=2000 estimation shared by all arms |
| Masked batches | custom collator | `get_batch_memmap_masked` | Shifted-mask target-space semantics unit-tested against a hand fixture (T-11-04) |
| Retention PPL | any new metric | `retention_perplexity()` (DEBT-02) | THE frozen policy; using anything else re-opens the Pitfall-9 drift class |
| Calibrated short-budget cohort | ad-hoc smoke scripts | `run_ablations.py` pattern (calibrate → lock → cohort) | Proven D-07 mechanism incl. the lock-enforcement raise |
| Prompt rendering for transcripts | string formatting | `dialogue/serialize.render_document`/`encode_dialogue` | Gate and bins and transcripts must tokenize identically (inflation-report Pitfall 4 discipline) |
| Restart-safe logging | print/log parsing | `CSVLogger(path, fieldnames)` | Append-mode, header-once, flush-per-row |

**Key insight:** the entire phase is a *consumer* of Phase 9–11 machinery. Any task that writes
new training/eval math (beyond `masked_perplexity`, which is a ~30-line mirror of an
oracle-proven function) is a scope smell.

## Common Pitfalls

### Pitfall 1: Anchor semantics — 2.1066 is not the retention curve's anchor
**What goes wrong:** curves get plotted against the 2.1066 dashed line and the step-0 point
doesn't touch it; someone "fixes" the discrepancy by switching policies mid-milestone.
**Why:** 2.1066 is unmasked full-val; `retention_perplexity` masks dead ids (softmax renormalized
over ~550 live ids ⇒ strictly lower PPL); the curve additionally runs on a sub-bin.
**Avoid:** measure and commit all three step-0 numbers (masked sub-bin = curve anchor; masked
full-val; 2.1066 reference) in the smoke report before any training step.
**Warning signs:** any figure or CSV where a step-0 retention value is asserted rather than measured.

### Pitfall 2: λ silently scales with grad accumulation / cross-device Fisher
**What:** penalty added after the `/accum` divide, or CPU Fisher against an MPS model.
**Avoid:** the shipped loop already orders it correctly (penalty joins base_loss before `/accum`,
loop.py:149-151, test-pinned) and `EWCPenalty.__init__` moves both dicts to device once. Keep
`grad_accum_steps=1` for all arms anyway; never construct the penalty per-step.

### Pitfall 3: Evaluation-policy drift across arms (the incommensurability trap)
**What:** masked arm's val_loss = assistant-CE, unmasked arm's = all-token CE; the D-01
comparison silently compares different quantities.
**Avoid:** freeze ONE dialogue-val policy (masked deterministic sweep, fixed forbid-ids decision)
before the first smoke number exists; every gate on every arm uses it. Record the policy in the
report header.

### Pitfall 4: `perplexity()` leaves the model in eval mode
**What:** `perplexity()`/`retention_perplexity()` call `model.eval()` and never restore
`model.train()` (verified perplexity.py:55; harmless standalone, wrong inside the loop).
**Avoid:** the `extra_eval_fns` block in the loop restores `model.train()` after running fns
(dropout is 0.0 so a miss is currently silent — pin it with a test anyway).

### Pitfall 5: Non-monotonicity instability gate is brittle at raw precision
**What:** D-02 defines instability as "dialogue val PPL non-monotonic across logging intervals";
at any finite budget, noise makes strict monotonicity a coin-flip near the plateau.
**Avoid:** pre-register the operational form using the same D-05 machinery: "non-monotonic" =
an interval-to-interval PPL *increase* exceeding the noise floor (k×Δ). If the noise run makes
even that infeasible to define cheaply, invoke the D-02 pre-registered fallback (blocking
checkpoint on raw curves) explicitly.

### Pitfall 6: Sweep logs landing in gitignored `logs/`
**What:** EWC-03 requires sweep logs *retained* for Phase 13's frontier plot; `logs/` is
gitignored (v1.0 posture), so CSVs written there can be lost.
**Avoid:** per-arm CSVs go to tracked `results/` (the `abl_*.csv` precedent). Checkpoints stay
gitignored as always.

### Pitfall 7: Seed/data-order ownership in the driver
**What:** `train()` only self-seeds when `model is None`; every arm passes an explicit model, and
the batch sampler draws from the *global* numpy RNG.
**Avoid:** `seed_everything(SEED)` immediately before each arm's `GPT(...)` build
(run_ablations.py:202-208 discipline) — this is also exactly what makes arms share data order,
which D-05/Phase-13 depend on.

### Pitfall 8: Fully-masked windows and NaN paranoia
**What:** a window whose shifted targets are all `-100` contributes nothing; a fully-masked
*batch* would make the mean CE NaN and trip the instability gate spuriously.
**Why it's (almost) a non-issue:** `forward` flattens B×T before CE, so the mean is over all
non-ignored positions in the whole batch (32×256 targets at masked fraction ~0.43) — a fully
masked batch is practically impossible. Note it in the plan; optionally assert
`torch.isfinite(loss)` in the smoke driver so a real divergence is never confused with it.

### Pitfall 9: Wall-clock surprises
**What:** ~12 smoke runs × unknown step time; retention fn cost × eval cadence can dominate.
**Avoid:** Stage 0 measures real step time and retention-point time first (that's partly what
budget recalibration is for); pick eval_interval and retention-bin size from measured numbers,
record them in the report. Rough prior: Fisher measured 18.6 ms/example (batch-1 fwd+bwd), so a
batch-32 step is plausibly a few hundred ms on MPS ⇒ a 2,500-step arm ≈ tens of minutes — but
this is LOW confidence and must be measured, not assumed.

## Code Examples

Verified against the shipped code this session.

### Production fine-tune invocation (the whole phase in one call)
```python
# Source: loop.py signature + estimate_fisher_tinystories.py load discipline (this repo)
blob = torch.load(BEST_PATH, weights_only=False)          # own trusted anchor
model_cfg = ModelConfig(**blob["model_config"])
seed_everything(SEED)                                      # driver owns seed + data order
model = GPT(model_cfg); model.load_state_dict(blob["model"])

cache = load_fisher(FISHER_CACHE, expected_fingerprint={...})   # fingerprint pins the anchor
theta_star = {n: p.detach().clone().cpu() for n, p in model.named_parameters()}
penalty = EWCPenalty(cache["fisher"], theta_star, lam=LAMBDA_STAR, device=runtime.device)

train(
    train_config=TrainConfig(lr=LR_STAR, batch_size=32, grad_accum_steps=1, max_steps=BUDGET),
    runtime_config=runtime, model=model, model_config=model_cfg,
    train_bin=DIALOG_TRAIN, train_mask_bin=DIALOG_TRAIN_MASK,      # NEW additive seam
    val_bin=DIALOG_VAL, val_mask_bin=DIALOG_VAL_MASK,              # NEW additive seam
    penalty_fn=penalty,
    extra_eval_fns={                                               # NEW additive seam
        "retention_ppl": lambda m: retention_perplexity(m, RETENTION_BIN, 256, runtime.device, tok)[0],
        "dialog_ppl":    lambda m: masked_perplexity(m, DIALOG_VAL, DIALOG_VAL_MASK, 256, runtime.device, forbid_ids=FORBID)[0],
        "ewc_penalty":   lambda m: float(penalty(m)),
    },
    checkpoint_extra={"fisher": cache["fisher"], "theta_star": theta_star,
                      "ewc_lambda": LAMBDA_STAR, "fisher_meta": cache["fisher_meta"]},
    checkpoint_path=CONVBASE_LATEST, best_checkpoint_path=CONVBASE_BEST,
    log_path=RESULTS_DIR / "finetune_prod.csv", eval_interval=250, checkpoint_interval=250,
)
```

### `masked_perplexity` core (mirror of the oracle-proven `perplexity()`)
```python
# Source: evaluation/perplexity.py:57-79 pattern + data.py:110-126 mask semantics (this repo)
data = np.memmap(bin_path, dtype=np.uint16, mode="r")
mask = np.memmap(mask_path, dtype=np.uint8, mode="r")     # length-aligned (T-11-04, fail loud)
for i in range(0, n - 1, block_size):
    chunk = torch.from_numpy(data[i:end].astype(np.int64)).to(device)
    m     = torch.from_numpy(mask[i+1:end].astype(np.int64)).to(device)   # SHIFTED with y
    x, y = chunk[:-1].unsqueeze(0), chunk[1:].unsqueeze(0)
    y = y.masked_fill(m.unsqueeze(0) == 0, -100)
    logits, _ = model(x)
    if forbid_ids is not None:
        logits = logits.masked_fill(forbid_ids.to(logits.device), float("-inf"))
    ce = F.cross_entropy(logits.view(-1, logits.size(-1)), y.view(-1),
                         reduction="sum", ignore_index=-100)
    total_ce += ce.item(); total_tokens += int((y != -100).sum())
# ppl = exp(total_ce / total_tokens); denominator = exact scored-assistant-token count (auditable)
```

### `stop_ids` diff in `generate()` (the entire change)
```python
# Source: generation/core.py:53-71 (this repo)
stops = stop_ids if stop_ids is not None else {eid}   # default ≡ v1.0 single-EOS behavior
...
if tok in stops:
    return  # stop-without-yield (D-05 idiom) — unchanged semantics, set membership
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| λ copied from papers (0.1–10⁶ reported) | λ swept per-implementation; non-portable because Fisher variant/normalization shifts usable λ by orders of magnitude | van de Ven, ICLR 2025 blogpost track (already cited in canonical PITFALLS) | The sweep IS the method; mean-normalized Fisher collapses the plausible range toward O(1) |
| Retention measured at run end | Retention on the training eval cadence from step 0 | This milestone's TUNE-02 (Pitfall 15 prevention) | Forgetting curves fall out of logs; requires the `extra_eval_fns` seam |
| Assistant-only masking assumed from HF SFT habit | Masked-vs-unmasked is a *measured* decision (Pitfall 14: stage-2 LM tuning is a different regime from QA teaching) | Phase 11 D-02 → this phase's D-01 | Tie goes to masked; unmasked must beat the margin |

**Deprecated/outdated for this phase:** ARCHITECTURE's original DailyDialog+PersonaChat corpus
(DailyDialog cut per D-00 2026-07-31 — PersonaChat only); the `extra_val_bins` *name* (this
research generalizes it to `extra_eval_fns` because retention/dialogue-PPL/penalty/role-norms all
need the seam, and deterministic sweeps — not `estimate_loss` draws — are the sanctioned metrics).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | A batch-32 training step costs a few hundred ms on the M3, so a smoke arm is tens of minutes | Pitfall 9 | Smoke sequence could take a day instead of hours; Stage 0 measures it before anything is locked |
| A2 | ~1.0M-token retention sub-bin gives a stable-enough PPL to serve as a gate/curve metric | Pattern 1 | Noise floor (D-05) will expose it; sub-bin size is adjustable before curves begin |
| A3 | λ grid {0.01..100} brackets λ* given mean-normalized Fisher | Pattern 4 | Boundary-extension rule (pre-registered) recovers it at the cost of one extra arm |
| A4 | Masked (assistant-token) val PPL is the right frozen dialogue-quality policy for all gates | Pattern 2 | If unmasked were preferred, gates remain internally consistent — the freeze matters more than the choice; lock at plan time |
| A5 | Production run can double as Phase 13's EWC arm without compromising TUNE-01 | Pattern 7 | Worst case Phase 13 reruns its own EWC arm — cost, not correctness |

All other load-bearing claims in this document are `[VERIFIED]` against the repo this session
(file:line cited inline) or `[CITED]` from the canonical v2.0 research documents.

## Open Questions (RESOLVED)

All three resolved by user-confirmed locks (2026-08-01) and encoded in the plans' pre-registration.

1. **Exact operational form of the D-02 "non-monotonic" gate** — recommendation in Pitfall 5
   (increase > k×noise-floor); must be locked in the plan's pre-registration block before Stage 0b
   produces the floor. If the seed-pair deltas are too large to define it cheaply, the D-02
   fallback (blocking checkpoint on raw curves) is itself pre-registered — invoke it explicitly.
   **RESOLVED:** Lock 1 accepted as recommended — encoded in 12-04-PLAN `<pre_registration>` §4.
2. **Budget-recalibration flatten rule constants** — the v1.0 rule (last-1k improvement < 15% of
   first-1k, coherent band 1.0–1.3) has TinyStories-specific constants; the dialogue analog needs
   its band re-stated (dialogue val CE will sit higher). Recommend keeping the slope rule, dropping
   the absolute band, and pre-registering "budget = smallest step where masked-vs-unmasked
   separation would exceed the noise floor" as D-03 says.
   **RESOLVED:** Lock 2 — slope rule kept, absolute band dropped; Stage 0b floor measured AT the
   recalibrated budget doubles as validity check (halt per D-07 exception) — 12-04-PLAN §3.
3. **Whether `val_mask_bin` (in-loop masked val for best-selection) ships, or best-selection stays
   on unmasked val CE** — recommended: ship it (one small branch in `estimate_loss`, symmetric with
   the train seam); either way the gates use the deterministic sweep. Planner locks it.
   **RESOLVED:** Lock 3 — `val_mask_bin` ships with selection-specific justification (checkpoint
   selected FOR assistant-token capability) — 12-01-PLAN T1.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 venv | all work | ✓ | 3.11.15 (`.venv`) | — (3.14 system python is forbidden) |
| torch + MPS | training/eval | ✓ | 2.7.1, MPS available | CPU (slow — smoke only) |
| `personacore` editable install | all work | ✓ | imports from `src/` | — |
| `data/dialog_{train,val}.bin` + masks | fine-tune | ✓ | 5,257,858 / 637,633 tokens, masks aligned | — |
| `data/train.bin` / `data/val.bin` | Fisher provenance / retention | ✓ | val = 12,636,923 tokens | — |
| `checkpoints/best.pt` | anchor | ✓ | val_loss 0.7378 (166 MB) | — |
| `checkpoints/fisher_tinystories.pt` | EWC | ✓ | 55.6 MB, N=2000 | re-estimate (~1 min, but breaks refuse-to-rerun provenance — don't) |
| `tests/fixtures/golden_trajectory_v1.json` | loop-change protection | ✓ | present | — |

**Missing dependencies with no fallback:** none — every input artifact exists on disk (verified
this session).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x (existing) |
| Config file | `pyproject.toml` / `Makefile` (`make test` → `pytest -q`) |
| Quick run command | `.venv/bin/python -m pytest tests/test_loop_penalty_fn.py tests/test_masked_batch.py -x -q` |
| Full suite command | `make test` (CPU-only, GPU-free, ~250 tests) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEBT-01 | true-token CSV column | unit | `pytest tests/test_run_csv_tokens.py -x` | ✅ (pre-work) |
| DEBT-02 | frozen retention policy | unit | `pytest tests/test_retention_ppl.py -x` | ✅ (pre-work) |
| TUNE-01 | mask-bin seam routes `get_batch_memmap_masked`; defaults ⇒ v1.0 identity | unit | `pytest tests/test_masked_train_seam.py -x` | ❌ Wave 0 |
| TUNE-01 | golden trajectory bit-identical after loop edits | unit | `pytest tests/test_train_loop.py tests/test_resume_curve.py -x` | ✅ (existing, re-run) |
| TUNE-02 | extra eval columns logged per interval; model restored to train mode; `None` ⇒ identical CSV | unit | `pytest tests/test_extra_eval_fns.py -x` | ❌ Wave 0 |
| TUNE-01/gates | masked deterministic PPL oracle (hand fixture: CE over mask=1 targets only, exact denominator) | unit | `pytest tests/test_masked_perplexity.py -x` | ❌ Wave 0 |
| TUNE-01 | `stop_ids` default ≡ v1.0; stops-without-yield on user id | unit | `pytest tests/test_stop_ids.py -x` | ❌ Wave 0 |
| EWC-03 | penalty-once-per-step, zero-at-anchor (already pinned) | unit | `pytest tests/test_loop_penalty_fn.py tests/test_ewc_penalty.py -x` | ✅ (existing) |
| EWC-03/TUNE-01/02 | smoke gates + production run (multi-hour M3 manual artifacts) | manual-only | driver scripts; verified via committed report/CSVs — justification: training runs cannot execute in CI (v1.0 T-07-07 precedent) | — |

### Sampling Rate
- **Per task commit:** the quick run command above + the specific new test file
- **Per wave merge:** `make test` (full CPU suite must stay green — the 250-test purity contract)
- **Phase gate:** full suite green + smoke report committed + D-07 checkpoint passed before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_masked_train_seam.py` — covers TUNE-01 (seam routing + v1.0 identity)
- [ ] `tests/test_extra_eval_fns.py` — covers TUNE-02 (columns, train-mode restore, identity)
- [ ] `tests/test_masked_perplexity.py` — covers gate metric (hand-fixture oracle)
- [ ] `tests/test_stop_ids.py` — covers transcript stopping (default-equivalence + role stop)
- [ ] `scripts/build_retention_bin.py` + step-0 anchor measurements (before any training step)

## Security Domain

Adapted to this project's surface (claim integrity + safe artifact handling — no network, no
user input, no services):

| Concern | Applies | Standard Control |
|---------|---------|------------------|
| Untrusted deserialization | yes | `torch.load(weights_only=False)` ONLY on the project's own checkpoints/caches (v1.0 T-07-05/T-10-05 discipline); shippable artifacts stay `weights_only=True` (`export_slim`, `export_fisher`) |
| Network dependencies | no | Zero — all inputs are local artifacts; no downloads this phase |
| Secrets | no | None handled; `.gitignore` already covers checkpoints/logs/tokens |
| Claim integrity | yes | Pre-registration discipline (D-01..D-07) + committed raw-number report — the project's equivalent of an audit trail |

## Sources

### Primary (HIGH confidence — read line-by-line this session)
- `src/personacore/training/loop.py` — seam inventory, DEBT-01 fix, penalty ordering, CSV/best/resume contracts
- `src/personacore/training/data.py` — `get_batch_memmap_masked` semantics (shifted mask, −100)
- `src/personacore/continual/{ewc,fisher}.py` + `scripts/estimate_fisher_tinystories.py` — penalty contract, mean normalization, cache provenance, N=2000/seed 1234
- `src/personacore/evaluation/perplexity.py` — headline vs frozen retention policy; eval-mode non-restore
- `src/personacore/generation/core.py`, `src/personacore/dialogue/serialize.py` — stop_ids landing point, transcript rendering path
- `scripts/run_ablations.py`, `scripts/pretrain_tinystories.py` — calibration method, seed ownership, pretrain peak LR 3e-4, cadence constants
- `src/personacore/config.py`, `training/schedule.py`, `logging.py`, `checkpoint.py` — TrainConfig defaults, warmup/cosine, CSVLogger fieldnames, export/load fisher/slim
- `results/inflation_report.md` — bin statistics (token counts, masked fractions), D-06 report register
- `.planning/research/ARCHITECTURE.md`, `.planning/research/PITFALLS.md` — converged v2.0 research (canonical per CONTEXT); PITFALLS itself cites van de Ven (arXiv 2502.11756) for λ non-portability and the Fisher-variant finding
- Filesystem/venv probes — artifact presence, sizes, torch 2.7.1/MPS availability

### Secondary (MEDIUM confidence)
- Wall-clock extrapolation from the Fisher script's measured 18.6 ms/example (first-party number, extrapolated — flagged A1)

### Tertiary (LOW confidence)
- None — no external web claims were introduced; the λ-range literature claims are inherited from the already-cited canonical PITFALLS sources.

## Metadata

**Confidence breakdown:**
- Loop-seam gap analysis & integration facts: HIGH — verified against shipped code at file:line
- Smoke/λ design: HIGH on structure (locked by CONTEXT D-01..D-07), MEDIUM on discretionary constants (grid, sub-bin size, budgets — the smoke exists to measure them)
- Wall-clock estimates: LOW — Stage 0 measures before anything locks

**Research date:** 2026-07-31
**Valid until:** stable — internal-codebase research; invalidated only by commits touching `training/loop.py`, `evaluation/perplexity.py`, or the Phase 11 bins
