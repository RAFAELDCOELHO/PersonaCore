# Phase 13: EWC A/B No-Forgetting Experiment - Research

**Researched:** 2026-08-01
**Domain:** Internal — pre-registered A/B experiment on the project's own fine-tune harness + matplotlib figures + evidence report
**Confidence:** HIGH (nearly every claim verified directly against committed code/artifacts in this session)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Arm design & λ choice
- **D-01:** Both arms run **fresh from `best.pt`** — Phase 12's production run is NOT reused
  as the EWC arm. It was explicitly a post-verdict discretionary choice (optimized after
  seeing the negative §8 result), not a pre-registered demonstration; consistent with the
  recorded "case b: production feeds Phase-14 demo substrate only".
- **D-02:** Headline λ = **0.01, not 100**. The phase demonstrates the acquisition–retention
  TRADE-OFF is real and favorable — both sides moving in the right direction simultaneously.
  λ=100 shows only half the phenomenon (near-zero retention drift bought with destroyed
  acquisition); λ=0.01 is the only sweep grid point showing both.
- **D-03:** Arm config = the recorded twin-provenance TrainConfig: **unmasked, LR 9e-5,
  seed 1337, 4000 steps, batch 32, accum 1** (≈37 min/arm on M3/MPS fp32). Only the
  production *checkpoint reuse* is rejected — the *config* is documented and reproducible.
- **D-04:** **Two arms only.** No extra λ arms at 4000 steps; the λ dimension is covered by
  the retained 1250-step sweep logs feeding VIZ-04.
- **D-05:** **Single seed pair (1337)**, citing the Phase 12 noise floor (Δ_ret = 0.069) —
  with three mandatory report obligations:
  1. Show the check, not just the number: state what config/regime Δ_ret=0.069 was measured
     under (which arm, which budget — confirm the 1250-step smoke, name the arm config).
  2. Named limitation (threats-to-validity register): the floor was NOT re-verified at
     production budget (4000 steps) or within collapse dynamics; effect-size variance COULD
     scale with drift magnitude in a way a stable-regime floor wouldn't capture. The 30–60×
     margin ratio is stated as the reason this is judged acceptable — not as proof the risk
     doesn't exist.
  3. Free check, zero compute: pull the λ=0 arm's OWN interval-to-interval retention
     trajectory (extra_eval_fns logging already exists) — smooth/monotonic = within-run
     stability signal supporting the floor's transferability, reported alongside the
     limitation.
- **D-06:** Claim gate: **retention side pre-registered only** — "EWC mitigates forgetting" =
  EWC-arm retention beats λ=0 by > K×Δ_ret (K=2, floor 0.069). Acquisition cost is reported
  descriptively in the 2×2 with NO pass/fail gate: it is the expected, non-binary side of a
  known trade-off, not a claim requiring its own margin. The report explains why this differs
  from §8's dual-margin approach (see D-09).

#### Artifact isolation (LOCKED — not discretion)
- **D-07:** Each arm gets a **name-scoped output path** (e.g. `results/phase13_naive/`,
  `results/phase13_ewc/` or equivalent naming) — checkpoints, per-run CSVs, and sample
  outputs distinct from Phase 12's production artifacts AND from each other. The driver must
  **refuse to silently overwrite** either arm's outputs on re-run — the same WR-02 guard
  discipline Phase 12's code review just installed (`finetune_dialog.py` refuse-to-rerun
  precedent). This is the structural guard against the exact failure mode WR-02 closed; it
  must not be rediscovered mid-phase.

#### 2×2 metric endpoints
- **D-08:** The 2×2 cells are **end-of-run (step 4000) values, NOT best-checkpoint values** —
  the A/B claim is about model state after a fixed training budget (what Phase 14 inherits
  and real usage experiences). Best-checkpoint selection would add a second decision that
  dilutes "differs only in the penalty" — structurally the WR-01 risk. If any best-checkpoint
  mechanism is used anywhere in this phase for practical reasons (e.g. late-run instability
  guard), it must reuse `retention_perplexity` / `val_mask_bin` exactly as WR-01 established —
  never a fresh ad hoc metric. Acquisition metric = **masked dialogue val PPL**
  (`masked_perplexity`, frozen gate policy from Phase 12 §1) for BOTH arms — never
  raw/unmasked (that would be a silent metric substitution). Retention metric =
  `retention_perplexity` on the frozen sub-bin (anchor 2.1076; headline dashed baseline
  2.1066). **Both arm checkpoints are kept** under the D-07 isolated paths; if research
  surfaces a storage-budget concern, it must be stated explicitly before discarding either.

#### A/B report contents & framing
- **D-09:** The report MUST contain **one reconciliation section** (not scattered) explaining
  why §8's "EWC not demonstrable at this budget" and Phase 13's retention-gated result are
  NOT in tension: §8 was a SEARCH over five λ values requiring BOTH a near-impossible
  dialogue margin AND the retention margin simultaneously at smoke budget (all-fail
  informative); Phase 13 is a DEMONSTRATION of a single pre-chosen comparison, retention-gated
  by the same validated noise floor, at production budget. Silently juxtaposing "not
  demonstrable" and "demonstrated" would read as contradiction.
- **D-10:** Pre-registration = **both code and report preamble**: the gate rule (K=2 ×
  Δ_ret=0.069, end-of-run cells, arm configs) hardcoded in the committed driver/report script
  BEFORE either arm runs (git history as proof — `finetune_smoke.py` precedent), PLUS the
  report opens with a pre-registration table (constants + the commit SHA where each rule was
  locked, smoke-report layout).
- **D-11:** The fresh EWC arm doubles as an **explicit reproduction cross-check** of Phase
  12's production run (config-identical): side-by-side endpoint numbers vs
  `results/finetune_prod.csv`, reported regardless of outcome. **Divergence beyond the
  k=2×Δ_ret margin is a REAL FINDING that blocks report finalization** until investigated —
  either an uncaptured non-determinism source (MPS device ops are a named risk category) or
  unnoticed config drift. Match or mismatch, both are informative; only a mismatch changes
  what happens next.

#### Naive-arm qualitative evidence
- **D-12:** **Retention-side samples only** — TinyStories-style continuations from BOTH arm
  endpoints, NOT dialogue transcripts: the qualitative evidence targets exactly what the
  retention gate measures (base-task forgetting), staying aligned with the quantitative claim
  instead of illustrating a different axis (dialogue quality is already covered by the
  acquisition PPL numbers). Shared pre-registered prompt set and sampling protocol across
  both arms, generated in ONE script run (not two separately curated passes). Reported as
  representative samples, never cherry-picked, with Phase 12's measured proxies applied
  (stop-id termination where applicable, dead-id leakage counts).

### Claude's Discretion
- **Figure design (VIZ-01/04):** panel layout, curve styling, format (PNG/SVG), file location
  (results/ vs a figures/ dir), plotting-script placement — within the requirement text
  (retention PPL vs steps per arm, dashed 2.1066 baseline, acquisition companion panel;
  frontier = retention vs acquisition, one point per λ from the retained sweep CSVs).
- **Identicality-proof mechanism:** provenance-block echo vs config assertion in the driver
  vs step-0 equivalence check — implementation detail within the locked discipline (D-07 is
  the locked part).
- **Report file naming/location and thin-script structure** — follow the `results/*.md`
  register precedent (`inflation_report.md`, `finetune_smoke_report.md`).
- Mechanics: step-0 row pre-seeding (12-01 pinned fact: v1.0 eval block logs no step-0 row),
  CSV naming within the D-07 scoped paths, prompt-set size for D-12 samples.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope. (Figure design and remaining report mechanics
are in-phase Claude's-discretion items, not deferrals.)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEMO-04 | EWC A/B no-forgetting experiment — identical seeds/config/data-order arms differing ONLY in the penalty; both retention AND acquisition reported | Driver mechanics fully mapped: `finetune_dialog.py` is a working single-arm template; the `seed_everything`-before-GPT-build data-order mechanism is verified in code and echoed in the committed provenance block (`results/finetune_prod_run.log`); `train(penalty_fn=...)` seam confirmed — the λ=0 arm passes `penalty_fn=None`, the EWC arm passes `EWCPenalty(fisher, theta_star, 0.01, device)`. Gate arithmetic pre-computed: EWC retention must beat naive retention by > 2×0.069 = 0.1379 |
| VIZ-01 | Forgetting-curve figure — retention PPL vs fine-tune steps per arm, dashed baseline at 2.1066, acquisition companion panel; committed | Both arm CSVs will carry `retention_ppl` + `dialog_ppl` columns at 250-step cadence with a pre-seeded step-0 row (prod CSV format verified). matplotlib 3.10.9 installed in the venv ([VERIFIED: venv import]). `.gitignore` does not exclude images — PNGs are committable ([VERIFIED: .gitignore read]) |
| VIZ-04 | λ stability–plasticity frontier plot (retention vs acquisition, one point per λ from the sweep logs) | Endpoint pairs verified from committed CSVs + smoke report (table below). **Load-bearing pitfall found:** `ft_lr_9e-5.csv` has NO `retention_ppl` column — the λ=0 frontier point's retention (5.9553) must be sourced from the smoke report's recorded Stage-2/3 values, not the CSV (see Pitfall 1) |
</phase_requirements>

## Summary

This phase needs zero external research and zero new dependencies. It is: (1) two invocations
of the existing `train()` harness from `checkpoints/best.pt` via a clone of the
`finetune_dialog.py` driver pattern — one with `penalty_fn=None`, one with
`EWCPenalty(λ=0.01)`; (2) two matplotlib figures from CSVs that either already exist (VIZ-04
sweep logs) or the arms produce (VIZ-01); (3) a `results/` report following the
`finetune_smoke_report.md` register. Everything the phase consumes was verified present and
readable in this session: `best.pt` (159 MB), `fisher_tinystories.pt` (53 MB), all dialogue
bins, the frozen `retention_val.bin` sub-bin, `retention_anchors.json`, the five λ-sweep CSVs,
and `finetune_prod.csv` (the D-11 reproduction target: step-4000 dialog_ppl 4.5733,
retention_ppl 3.8911).

The two findings the planner must not miss: **(a)** the λ=0 frontier point has no in-CSV
retention value — `ft_lr_9e-5.csv` predates the retention column; its retention endpoint
(5.9553) exists only as a committed number in the smoke report; **(b)** data-order
identicality between arms is carried entirely by `seed_everything(1337)` immediately before
the `GPT(model_cfg)` build (the batch sampler draws from the GLOBAL numpy rng), so each arm
must run as its own process replicating `finetune_dialog.py`'s exact call sequence — any extra
RNG draw before or between the seed call and training breaks the twin.

**Primary recommendation:** clone `finetune_dialog.py` into one arm-parameterized driver
(`--`-free, arm name hardcoded per the no-CLI precedent or a single positional arg), run it
once per arm as separate processes, with D-07 refuse-to-rerun guards on the scoped output
paths; plot and report from the CSVs afterward.

## Architectural Responsibility Map

Single-tier local ML project — "tiers" here are the established package/script/artifact layers:

| Capability | Primary Owner | Secondary | Rationale |
|------------|--------------|-----------|-----------|
| Arm training runs | `scripts/` (new A/B driver) | `src/personacore/training/loop.py` (`train()`, untouched) | Thin-driver precedent: constants + guards in script, all logic in package |
| EWC penalty | `src/personacore/continual/ewc.py` (`EWCPenalty`, existing) | `checkpoints/fisher_tinystories.pt` (shared cache) | Nothing new; λ=0 arm passes `penalty_fn=None` |
| Metrics (2×2 cells, curves) | `src/personacore/evaluation/perplexity.py` (existing) | — | `masked_perplexity` (acquisition) + `retention_perplexity` (retention) are the ONLY sanctioned metrics (D-08, frozen §1 policy) |
| Figures VIZ-01/04 | `scripts/` (new plotting script) | matplotlib 3.10.9 (installed) | Pure read-CSV-and-plot; no training coupling |
| D-12 retention samples | `scripts/` (new sample script) | `generation/core.collect`, `make_transcripts.py` + `evaluate.py` precedents | One run, both checkpoints, shared seeded prompt set |
| Report + pre-registration | `results/` register (new .md) | git history (commit SHAs as proof) | `finetune_smoke_report.md` layout precedent |

## Standard Stack

### Core

No new libraries. Everything is already installed in the project venv and verified this session:

| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| torch | 2.7.1 | training + eval (MPS fp32) | [VERIFIED: venv import; MPS available=True] |
| matplotlib | 3.10.9 | VIZ-01 / VIZ-04 figures | [VERIFIED: venv import; declared in pyproject `demo`/`notebook` extras] |
| numpy | 2.x | CSV/memmap glue | [VERIFIED: in venv, used throughout] |
| pytest | 8.x | 275 tests currently collected, all CPU-only | [VERIFIED: `pytest --co -q` → 275 tests] |

**Installation:** none. Do not add dependencies.

## Package Legitimacy Audit

No external packages are installed by this phase. slopcheck not run — nothing to check.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
                       checkpoints/best.pt (159 MB, anchor step 49000, git 3a46815)
                                 │ load_state_dict (fresh AdamW, fresh schedule)
                                 │ seed_everything(1337) IMMEDIATELY before GPT build
                                 ▼
        ┌────────────────────────┴───────────────────────────┐
        │ A/B driver (new script, clone of finetune_dialog.py)│
        │  refuse-to-rerun guard per arm (D-07)               │
        │  hardcoded pre-registered constants (D-10)          │
        └───────┬───────────────────────────────┬────────────┘
      run 1 (own process)              run 2 (own process)
        │ penalty_fn=None                │ penalty_fn=EWCPenalty(fisher, θ*, 0.01)
        ▼                                ▼
   train() 4000 steps               train() 4000 steps          ← identical TrainConfig,
   data/dialog_train.bin            data/dialog_train.bin          identical data order
        │                                │
        ▼                                ▼
   results/phase13_naive/           results/phase13_ewc/        ← D-07 scoped paths
     run CSV (+ step-0 row)           run CSV (+ step-0 row)
     latest ckpt (step 4000)          latest ckpt (step 4000)
        │                                │        │
        │                                │        └── D-11 cross-check vs results/finetune_prod.csv
        └───────────────┬────────────────┘
                        ▼
   ┌────────────────────┴─────────────────────────────────────┐
   │ post-run scripts (read-only over CSVs + checkpoints)      │
   │  • VIZ-01 forgetting-curve figure (2 arms, dashed 2.1066, │
   │    acquisition companion panel)                           │
   │  • VIZ-04 frontier (5 λ CSVs endpoints + λ=0 from report) │
   │  • D-12 sample script: TinyStories continuations, both    │
   │    endpoints, one run, shared seeded prompts              │
   │  • A/B report (results/*.md register): pre-reg table,     │
   │    2×2 end-of-run cells, gate verdict, D-09 reconciliation│
   └───────────────────────────────────────────────────────────┘
```

### Recommended Project Structure (additions only)

```
scripts/
├── finetune_ab.py            # the two-arm driver (name = discretion; clone of finetune_dialog.py)
├── plot_phase13.py           # VIZ-01 + VIZ-04 (or two scripts — discretion)
└── make_retention_samples.py # D-12 (evaluate.py samples + make_transcripts.py protocol precedents)
results/
├── phase13_naive/            # D-07 scoped: arm CSV (checkpoints go to checkpoints/, gitignored)
├── phase13_ewc/
├── phase13_forgetting_curve.png   # VIZ-01 (committed; .gitignore has no image exclusion)
├── phase13_frontier.png           # VIZ-04 (committed)
└── phase13_ab_report.md           # the register entry (naming = discretion)
```

Note: `checkpoints/` and `*.pt` are gitignored [VERIFIED: .gitignore] — arm checkpoints are
"kept" (D-08) on local disk under name-scoped filenames (e.g.
`checkpoints/phase13_naive_latest.pt`), never committed. 524 GB free disk; two arms ≈ 0.6–1.1 GB
of checkpoints — no storage concern (explicitly stated per D-08).

### Pattern 1: Arm-as-separate-process for data-order identicality

**What:** Run each arm as its own Python process replicating `finetune_dialog.py`'s exact
sequence: env `PYTORCH_ENABLE_MPS_FALLBACK=1` before torch import → guards → preflight →
`torch.load(best.pt)` → `seed_everything(SEED)` → `GPT(model_cfg)` → `load_state_dict` →
θ*/fisher setup → step-0 measurement → `train(...)`.
**Why:** the batch sampler draws from the GLOBAL numpy rng; `seed_everything(1337)` runs
immediately before the GPT build so the model-init draws and every subsequent batch draw are
stream-identical across processes. Same-process sequential arms risk stream divergence from
any extra draw between arms. The committed provenance block ("seed_everything immediately
before GPT build — owns data order", `finetune_prod_run.log`) is the contract the λ=0 twin
must honor bit-for-bit. [VERIFIED: finetune_dialog.py:176-184 + prod run log]
**Key detail:** the ONLY permitted differences between arm code paths are `penalty_fn`
(None vs EWCPenalty) and output paths. `extra_eval_fns`, `checkpoint_extra`, and eval calls
are trajectory-neutral (they run inside `_rng_state()`/`_restore_rng` snapshots —
loop.py:439-445 — and `EWCPenalty` is deterministic and RNG-free), so keeping the fns dict
IDENTICAL in both arms (including the `ewc_penalty` column, diagnostic-only in the naive arm)
is both safe and gives matching CSV schemas for plotting. [VERIFIED: loop.py + ewc.py]

### Pattern 2: Refuse-to-rerun + hardcoded constants (WR-02 / D-10)

Clone `finetune_dialog.py`'s exact guard style: iterate over ALL of the arm's output paths and
`SystemExit` if any exists, with a message naming what to delete. Constants (K=2,
DELTA_RET=0.068930, λ=0.01, TrainConfig knobs) hardcoded at module top with report citations,
committed BEFORE either arm runs — git history is the pre-registration proof
(`finetune_smoke.py` precedent). Additionally guard that the driver never targets Phase 12's
paths (`finetune_prod.csv`, convbase trio) — those have their own guard in
`finetune_dialog.py`, but the new driver must be structurally incapable of touching them.

### Pattern 3: Step-0 row pre-seeding

The v1.0 eval block logs NO step-0 row (12-01 pinned fact). Reuse `_preseed_csv` verbatim:
header + measured step-0 row (`dialog_ppl` measured live from `best.pt`; `retention_ppl` from
`anchors["retention_ppl_subbin_step0"]` = 2.107553076833866; `ewc_penalty` = 0.0 exactly at
the anchor) before `train()` appends. Fieldnames = `CSV_FIELDNAMES + sorted(fns)` — appending
new columns to a pre-existing CSV raises by design (T-12-02). [VERIFIED: finetune_dialog.py:117-127, 212-227]

### Pattern 4: End-of-run endpoint, no best-checkpoint (D-08, WR-01-safe)

Recommend passing `checkpoint_path=<scoped latest>` only and OMITTING
`best_checkpoint_path` entirely: the end-of-call `latest.pt` save at loop.py:513-527 IS the
step-4000 state the 2×2 cells report, and skipping best-selection removes the WR-01 risk
surface completely. Trajectory-neutrality note for D-11: prod DID use `best_checkpoint_path`,
but best-saves consume no RNG (eval runs inside the RNG snapshot; `save_checkpoint`/`git_sha`
draw nothing), so omitting it cannot diverge the trajectory from `finetune_prod.csv`.
[VERIFIED: loop.py:414-479 — the best-save block only reads state]. If the planner prefers
maximal call-signature parity with prod for D-11 instead, pointing `best_checkpoint_path` at
a scoped path is equally trajectory-safe — the in-loop masked `val_loss` (via `val_mask_bin`)
is the WR-01-consistent metric. Either choice satisfies D-08; the 2×2 always reads the CSV's
final row / the end-of-call checkpoint.

### Pattern 5: D-12 sample script — one run, both endpoints

Combine two existing precedents: `scripts/evaluate.py` EVAL-02 (fixed in-repo TinyStories
prompt set, greedy + warm, representative-never-cherry-picked, written to a tracked
`results/*.md`) and `scripts/make_transcripts.py` (seeded `default_rng(1337)` selection,
`collect()` with `forbid_ids`, measured proxies in the header). For TinyStories continuations:
prompts = seeded story prefixes from `data/TinyStoriesV2-GPT4-valid.txt` (present,
[VERIFIED: ls]) encoded through the frozen tokenizer; `stop_ids={8184}` (eos only — no user-turn
stop in story mode); proxies = stop-id termination fraction + role-token (8185–8187) leakage
count (role tokens appearing mid-story = dialogue contamination of the base task — exactly the
forgetting axis). Load BOTH endpoint checkpoints in ONE script run, generate from the shared
prompt list for each, write one markdown file.

### Anti-Patterns to Avoid

- **Parsing the smoke report for numbers at runtime:** the register precedent is hardcode-with-citation ("the driver never parses the report for numbers" — finetune_dialog.py:75). The one exception pattern that exists is the GO-verdict *gate* (`_require_go_verdict` reads only the verdict word). Phase 13 needs no GO gate — its pre-registration is the committed driver itself.
- **Using in-loop `val_loss` or `estimate_loss` for any gate/cell:** 20-random-batch means are disallowed for gates (12-02 pinned); only `masked_perplexity` / `retention_perplexity`.
- **Raw `perplexity()` for retention points:** `retention_perplexity` is "THE ONLY sanctioned PPL for curve points" (docstring, DEBT-02 frozen policy).
- **`torch.load` of anything but the project's own checkpoints without the trusted-only comment:** follow the established `weights_only=False` TRUSTED-only annotation pattern; the Fisher cache goes through `load_fisher` (`weights_only=True`, fingerprint-pinned).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Two-arm training | Any new loop/harness | `train()` with `penalty_fn` seam | Untouched-loop purity is an established pattern; 275 tests pin it |
| EWC penalty | Anything | `EWCPenalty` + `load_fisher` fingerprint-pinned cache | Exact-zero-at-anchor and fail-loud validation already tested |
| Metrics | Ad hoc PPL | `masked_perplexity` / `retention_perplexity` | Frozen §1 gate policy; D-08 names them explicitly |
| Step-0 rows, CSV schema, guards, provenance print | Fresh variants | Clone from `finetune_dialog.py` | Every mechanism this driver needs already exists there, reviewed (WR-01/02) |
| Sampling protocol | New generation code | `generation.core.collect` + `undecodable_ids_mask` | Stop-id semantics (generate stops WITHOUT yielding the stop id) already pinned by test |

**Key insight:** the entire phase is recombination of reviewed Phase-12 components. Any new
logic beyond the plotting scripts and the report generator is a smell.

## Common Pitfalls

### Pitfall 1: The λ=0 frontier point has no CSV retention value
**What goes wrong:** `ft_lr_9e-5.csv` columns are `step,train_loss,val_loss,lr,tokens,wall_clock,dialog_ppl` — NO `retention_ppl` (the Stage-2 driver measured end retention post-run via `retention_perplexity`, not in-loop). A plotting script that reads `retention_ppl` from all six CSVs crashes or silently drops λ=0. [VERIFIED: CSV headers read this session]
**How to avoid:** source the λ=0 point from the committed smoke-report values (dialogue 4.4453, retention 5.9553 — Stage 2/3 tables), hardcoded with citation per the register pattern. The five λ CSVs' final rows DO carry retention and match the report exactly (verified: λ=0.01 final row 3.7813/4.7298 vs report 3.7813/4.7298). Full verified frontier data: λ=0→(4.4453, 5.9553), 0.01→(4.7298, 3.7813), 0.1→(5.6355, 3.0057), 1→(7.2144, 2.7734), 10→(10.5552, 2.1351), 100→(16.2112, 2.1082).
**Warning signs:** a KeyError on `retention_ppl`, or a frontier plot with five points.
**MANDATORY report note (provenance exception):** the λ=0 point is the ONE number in this phase not read from a committed CSV, so the report's pre-registration table (D-10) MUST carry an explicit exception row, e.g.: "retention_ppl for λ=0 is absent from `ft_lr_9e-5.csv` (column not logged by the Stage-2 driver, pre-Phase-13 decision); value 5.9553 (and dialogue 4.4453) cited from `results/finetune_smoke_report.md` Stage 2/3 tables, commit 666d096 — not recomputed here." Without this note the number reads as unsourced against the phase's otherwise CSV-backed provenance.

### Pitfall 2: Breaking the data-order twin
**What goes wrong:** any RNG draw inserted before `seed_everything(SEED)` → `GPT build` → training (or running both arms in one process) diverges the batch stream, and "differs ONLY in the penalty" becomes false — the phase's central claim.
**How to avoid:** separate process per arm; replicate `finetune_dialog.py`'s call order exactly; the D-11 cross-check (EWC arm endpoint vs `finetune_prod.csv` step 4000: dialog_ppl 4.5733, retention_ppl 3.8911, ewc_penalty 0.1344) is the built-in detector — a mismatch beyond 2×0.069 blocks the report.
**Warning signs:** EWC-arm CSV rows diverging from `finetune_prod.csv` early (compare step-250 row: 5.101385…, 3.904004… — a row-level early check is free and catches drift at minute 3 instead of minute 37).

### Pitfall 3: Conflating the two baselines (2.1066 vs 2.1076)
**What goes wrong:** the dashed VIZ-01 baseline is the historical headline **2.1066**
(full-val, unmasked, v1.0 semantics) per requirement text; the CURVE ANCHOR / step-0 point is
the sub-bin **2.107553** (dead-id-masked `retention_perplexity`). `retention_anchors.json`
carries an explicit warning: "historical unmasked reference only — NOT the curve anchor,
Pitfall 1". Plotting the dashed line from the anchor value (or seeding step-0 from 2.1066)
mixes metrics.
**How to avoid:** dashed line = 2.1066 (requirement text, labeled as the v1.0 headline);
step-0 curve points = 2.107553076833866 from the anchors JSON; the report states both and the
distinction once.

### Pitfall 4: Mixing 1250-step and 4000-step regimes in figures/claims
**What goes wrong:** the sweep CSVs ran cosine schedules over max_steps=1250 (their LR
columns decay to 9e-6 by step 1250); the arms decay over 4000. Sweep trajectories are NOT
comparable curves to the arm trajectories — only the frontier ENDPOINTS at the 1250 budget
are used (VIZ-04), and the figure/report must label the budget per artifact. Similarly the
"+3.85 collapse" number is a 1250-step figure; the naive arm's 4000-step retention endpoint
is a NEW number this phase produces (expect worse than 5.9553).
**How to avoid:** VIZ-04 axis/caption states "1250-step sweep endpoints"; VIZ-01 states
"4000-step arms"; the 2×2 uses only arm endpoints.

### Pitfall 5: MPS environment fallback ordering
**What goes wrong:** `PYTORCH_ENABLE_MPS_FALLBACK=1` must be set BEFORE `import torch` or an
uncovered MPS op crashes a 37-minute run mid-flight.
**How to avoid:** copy the `os.environ.setdefault` header pattern from
`finetune_dialog.py`/`make_transcripts.py` verbatim. MPS non-determinism remains a named D-11
risk category regardless — the reproduction check exists precisely because determinism on MPS
is asserted-by-evidence, not guaranteed.

### Pitfall 6: Silently touching Phase-12 recorded evidence
**What goes wrong:** re-running `finetune_dialog.py`, or pointing any output at
`finetune_prod.csv` / the convbase trio, replaces committed evidence (the WR-02 failure mode).
**How to avoid:** D-07 scoped paths only; the new driver's guard list includes its own outputs;
it never references Phase-12 output paths as write targets. `finetune_prod.csv` is read-only
input (D-11).

### Pitfall 7: `perplexity()` leaves the model in eval mode
**What goes wrong:** eval fns call `model.eval()` and never restore; outside `train()`'s
managed extras block (which restores `model.train()`), a driver that measures step-0 metrics
then trains must not assume mode. `finetune_dialog.py` explicitly calls `model.train()` before
`train()` — keep that line.

## Code Examples

Verified patterns from the codebase (not external sources):

### The one-bit arm difference
```python
# Source: scripts/finetune_dialog.py:192-193, 241-265 (adapted)
# EWC arm:
penalty = EWCPenalty(fisher, theta_star, 0.01, runtime.device)
train(..., penalty_fn=penalty, ...)
# Naive arm (THE one bit flipped):
train(..., penalty_fn=None, ...)
# Both arms: identical TrainConfig(lr=9e-5, batch_size=32, max_steps=4000,
#   warmup_steps=100, grad_clip=1.0, grad_accum_steps=1, weight_decay=0.1, seed=1337),
# train_mask_bin=None (unmasked), val_mask_bin=DIALOG_VAL_MASK, eval_interval=250.
# [VERIFIED: results/finetune_prod_run.log provenance block — the committed twin contract]
```

### Retention gate (pre-registered constants, D-06/D-10)
```python
# Constants transcribed from results/finetune_smoke_report.md Stage 0b (commit history = proof)
K = 2                       # declared blind in Phase 12 — reused, not re-chosen
DELTA_RET = 0.068930        # seed-pair floor, masked arm, LR 9e-5, 1250 steps (state the regime! D-05)
MARGIN = K * DELTA_RET      # 0.137861
# Verdict: ewc mitigates forgetting iff (naive_retention_4000 - ewc_retention_4000) > MARGIN
```

### D-11 reproduction cross-check target
```python
# results/finetune_prod.csv step-4000 row [VERIFIED this session]:
# dialog_ppl=4.573349214207799, retention_ppl=3.891139975617828, ewc_penalty=0.13435843586921692
# Divergence of the fresh EWC arm beyond MARGIN on retention blocks report finalization (D-11).
```

### VIZ-04 frontier sourcing
```python
# λ arms: final CSV rows of results/ft_lam_{0.01,0.1,1,10,100}.csv (retention_ppl, dialog_ppl)
# λ=0:   HARDCODED from the smoke report (ft_lr_9e-5.csv has NO retention column — Pitfall 1):
LAMBDA0_POINT = {"dialog_ppl": 4.4453, "retention_ppl": 5.9553}  # smoke report Stage 2/3
```

## State of the Art

Not applicable — no ecosystem movement is relevant; the phase runs entirely on pinned internal
infrastructure (torch 2.7.1 in the frozen venv). The EWC formulation is the Kirkpatrick et
al. 2017 diagonal-Fisher quadratic already implemented and tested in `continual/ewc.py`
[CITED: ewc.py docstring].

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | ~37 min/arm wall-clock on this M3 (extrapolated from the prod run's 37.3 min at identical config) | Summary / planning budget | Runs take longer; no correctness impact |
| A2 | Omitting `best_checkpoint_path` is trajectory-neutral vs prod (reasoned from loop.py code: best-save consumes no RNG) | Pattern 4 | If wrong, the D-11 cross-check itself catches it (the check exists for exactly this class of surprise); fallback = keep signature parity with prod |
| A3 | The naive arm's 4000-step retention endpoint will exceed the 1250-step 5.9553 collapse figure (continued-drift expectation) | Pitfall 4 | None — the number is measured, not assumed; only the report's framing prose would adjust |

All other claims in this document were verified by direct file reads / venv execution this session.

## Open Questions (RESOLVED)

1. **Naive-arm `ewc_penalty` CSV column: include or omit?**
   - What we know: including the same `EWCPenalty` object as a diagnostic-only `extra_eval_fns` entry is trajectory-safe and keeps both CSV schemas identical (nice for plotting and for the D-05 free-check trajectory pull).
   - What's unclear: whether a logged-but-unapplied penalty column invites misreading.
   - Recommendation: include it, with one report footnote ("measured, not applied, in the naive arm"). Falls under CONTEXT "mechanics" discretion.
   - **RESOLVED:** recommendation adopted — the naive arm keeps the diagnostic `ewc_penalty` column with the "measured, not applied" footnote. Locked in Plan 13-01 Task 1 (driver keeps `extra_eval_fns` identical across arms) and Plan 13-04 Task 1 (report footnote).
2. **PNG vs SVG, results/ vs figures/:** discretion. Recommendation: PNG at ~150–200 dpi in `results/` next to the report (register precedent keeps all evidence in one place; no figures/ dir exists yet — D-11 v1.0 "no empty stub dirs" spirit).
   - **RESOLVED:** recommendation adopted — PNG at dpi=150 written to `results/`. Locked in Plan 13-03 Task 1.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 venv | everything | ✓ | .venv active-able | — |
| torch + MPS | arm training | ✓ | 2.7.1, `mps=True` | CPU fp32 (slower; same code path) |
| matplotlib | VIZ-01/04 | ✓ | 3.10.9 | — |
| `checkpoints/best.pt` | both arms' anchor | ✓ | 159 MB | none — blocking if lost |
| `checkpoints/fisher_tinystories.pt` | EWC arm | ✓ | 53 MB, fingerprint-pinned | re-run `estimate_fisher_tinystories.py` |
| dialogue bins + masks (`data/dialog_*.bin`) | training + acquisition metric | ✓ | present | re-run `prepare_dialog_corpus.py` |
| `data/retention_val.bin` | retention metric | ✓ | present (frozen, refuse-to-rerun builder) | — |
| `results/retention_anchors.json` | step-0 rows, baselines | ✓ | committed | — |
| sweep CSVs (`ft_lam_*.csv`, `ft_lr_9e-5.csv`) | VIZ-04 | ✓ | committed | — |
| `results/finetune_prod.csv` | D-11 cross-check | ✓ | committed | — |
| `data/TinyStoriesV2-GPT4-valid.txt` | D-12 prompt source | ✓ | present | — |
| Disk | 2 arm checkpoint sets (~1 GB) | ✓ | 524 GB free | — |

**Missing dependencies with no fallback:** none.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x (275 tests collected, CPU-only, GPU-free by contract) |
| Config file | pyproject.toml / Makefile (`make test`) |
| Quick run command | `python -m pytest tests/ -x -q` (~seconds, CPU) |
| Full suite command | `make test` (inside `.venv`) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEMO-04 | Driver refuse-to-rerun guard fires on existing arm outputs | unit | `pytest tests/test_phase13_driver.py -x -q` | ❌ Wave 0 (pattern: existing guard tests) |
| DEMO-04 | Gate arithmetic (K×Δ_ret verdict function) correct on hand-built inputs | unit | same file | ❌ Wave 0 |
| DEMO-04 | Arm-config identicality (both arms' TrainConfig equal; one-bit λ diff) | unit (import driver constants) | same file | ❌ Wave 0 |
| VIZ-01/04 | Plot scripts run against committed CSVs and emit files | smoke | `pytest tests/test_phase13_plots.py -x -q` (tmp_path output) or manual-only if scripts stay __main__-thin | ❌ Wave 0 (or manual — justify: pure matplotlib output, visually verified) |
| DEMO-04 (runs) | The two 37-min training runs themselves | manual-only | driver execution + committed CSVs/report as evidence | — (long-running; justified: same class as Phase 12's prod run, evidence-committed not test-run) |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -x -q`
- **Per wave merge:** `make test` (full 275+ suite — purity contract: all existing tests stay green, `train()` untouched)
- **Phase gate:** full suite green + both arm CSVs/figures/report committed before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_phase13_driver.py` — guard + gate-arithmetic + config-identicality units (CPU-only, no training)
- [ ] Optional `tests/test_phase13_plots.py` — smoke the plot functions into tmp_path (skip if plotting stays trivially thin; state the justification)

## Security Domain

Offline, local-only phase — no network, no user input, no auth surface. Applicable concerns:

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | marginal | All inputs are the project's own committed artifacts; existing fail-loud validation (`EWCPenalty` key/shape checks, `load_fisher` fingerprint pinning, CSV DictWriter schema enforcement) |
| V6 Cryptography | no | — |
| Deserialization | yes | Follow the established pattern EXACTLY: `torch.load(weights_only=False)` ONLY on the project's own trusted checkpoints with the TRUSTED-only comment; Fisher cache via `load_fisher` (`weights_only=True`); slim/shippable artifacts stay `weights_only=True` (LOCKED contract) |

No new threat surface is introduced by this phase.

## Project Constraints (from CLAUDE.md)

- Python 3.11 venv MANDATORY (dev box Python 3.14 is unsupported); run everything inside `.venv`
- Primary training device: M3/MPS fp32 — no AMP/GradScaler/torch.compile on MPS
- No new dependencies; no wandb/online tooling; CSV + matplotlib only
- No HF transformers/PEFT/tokenizers as implementation
- pytest suite must stay CPU-only and GPU-free
- `make lint` = ruff check + format; keep new scripts ruff-clean
- GSD workflow entry points required for file changes
- Never commit checkpoints/tokens; `.gitignore` covers `checkpoints/`, `*.pt`, `data/`

## Sources

### Primary (HIGH confidence — read/executed this session)
- `scripts/finetune_dialog.py` — driver template, guards, seeding contract, step-0 pre-seeding
- `src/personacore/training/loop.py` — `train()` seams, RNG snapshot semantics, CSV schema, best/latest save mechanics
- `src/personacore/evaluation/perplexity.py` — frozen metric definitions
- `src/personacore/continual/ewc.py` — `EWCPenalty` contract
- `scripts/make_transcripts.py`, `scripts/evaluate.py` (samples section) — D-12 protocol precedents
- `results/finetune_smoke_report.md` — noise floor, sweep tables, §8 verdict, production decision (all frontier numbers)
- `results/finetune_prod_run.log`, `results/finetune_prod.csv` — D-11 targets + twin provenance block
- `results/ft_lam_*.csv`, `results/ft_lr_9e-5.csv` — VIZ-04 data + the missing-retention-column finding
- `results/retention_anchors.json` — baselines 2.107553 / 2.1065 / headline 2.1066 + explicit anchor-vs-headline warning
- venv execution: torch 2.7.1 (MPS True), matplotlib 3.10.9, pytest collection (275 tests), disk/checkpoint sizes, `.gitignore`

### Secondary / Tertiary
None needed — no external research performed; no WebSearch used.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — everything verified installed/working in the venv
- Architecture: HIGH — the driver pattern exists, reviewed, and committed; this phase recombines it
- Pitfalls: HIGH — Pitfalls 1–3 verified against actual file contents this session; A2 is the one reasoned (not executed) claim and D-11 self-checks it

**Research date:** 2026-08-01
**Valid until:** stable indefinitely (internal artifacts, pinned venv) — re-verify only if Phase-12 artifacts are regenerated
