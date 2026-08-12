# Phase 13: EWC A/B No-Forgetting Experiment - Pattern Map

**Mapped:** 2026-08-01
**Files analyzed:** 8 new files (3 scripts, 1 report, 2 tests, 2 CSV output dirs)
**Analogs found:** 7 / 8 (one partial — see No Analog Found)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/finetune_ab.py` (A/B arm driver; name = discretion) | driver script | batch training → CSV append + checkpoint | `scripts/finetune_dialog.py` | exact |
| — driver pre-registration constants block | config constants | — | `scripts/finetune_smoke.py:77-143` | exact |
| `scripts/plot_phase13.py` (VIZ-01 + VIZ-04) | plotting script | file I/O (CSV → PNG) | `demo.ipynb` cells 2 & 4 | role-match (only matplotlib code in repo) |
| `scripts/make_retention_samples.py` (D-12) | sampling/evidence script | batch generation → tracked markdown | `scripts/make_transcripts.py` (+ `scripts/evaluate.py` for prompt set) | exact |
| `results/phase13_ab_report.md` | evidence report | static committed artifact | `results/finetune_smoke_report.md` | exact |
| `results/phase13_naive/*.csv`, `results/phase13_ewc/*.csv` | data artifact | written by driver | `results/finetune_prod.csv` schema | exact |
| `tests/test_phase13_driver.py` | test | unit (CPU-only) | `tests/test_ablation_config.py` (style) | role-match — see convention warning |
| `tests/test_phase13_plots.py` (optional) | test | smoke (tmp_path) | none direct | partial |

## Pattern Assignments

### `scripts/finetune_ab.py` (driver, batch training run)

**Analog:** `scripts/finetune_dialog.py` — clone this file. It is the reviewed (WR-01/WR-02) single-arm version of exactly this driver; the A/B driver is this file parameterized by arm, run once per arm as separate processes (RESEARCH Pattern 1).

**MPS env + imports pattern** (`finetune_dialog.py:30-53`):
```python
import csv
import json
import math
import os
import pathlib
import time

# An uncovered MPS op falls back to CPU rather than crashing the multi-hour run — set BEFORE torch.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import torch  # noqa: E402  (must follow the MPS-fallback env set above)

from personacore.checkpoint import export_slim, load_fisher  # noqa: E402
from personacore.config import ModelConfig, RuntimeConfig, TrainConfig  # noqa: E402
from personacore.continual import EWCPenalty  # noqa: E402
from personacore.evaluation import masked_perplexity, retention_perplexity  # noqa: E402
from personacore.generation.text import undecodable_ids_mask  # noqa: E402
from personacore.model import GPT  # noqa: E402
from personacore.preflight import preflight_device  # noqa: E402
from personacore.provenance import git_sha  # noqa: E402
from personacore.seeding import seed_everything  # noqa: E402
from personacore.tokenizer import from_json  # noqa: E402
from personacore.training import train  # noqa: E402
from personacore.training.loop import CSV_FIELDNAMES  # noqa: E402
```
Note: `export_slim` is not needed by Phase 13 (no slim artifact — arm checkpoints stay local). `_REPO_ROOT`-relative path constants follow at `finetune_dialog.py:55-69`.

**Refuse-to-rerun guard (D-07 / WR-02)** (`finetune_dialog.py:140-147`):
```python
    # Refuse-to-rerun (build_retention_bin / _never_clobber_guard register): the production
    # run is RECORDED evidence — a rerun on drifted code/data would silently replace the
    # committed forgetting curve and the convbase trio. Fail loud instead.
    for out in (PROD_CSV, CONVBASE_LATEST, CONVBASE_BEST, CONVBASE_SLIM):
        if out.exists():
            raise SystemExit(
                f"[finetune_dialog] {out} already exists — the production run is recorded "
                "evidence. Delete the convbase trio + finetune_prod.csv to re-run."
            )
```
Phase 13: iterate the ARM's scoped outputs (per-arm CSV + per-arm checkpoint). Phase-12 paths (`finetune_prod.csv`, convbase trio) must never appear as write targets in the new driver — read-only D-11 input.

**Prerequisite checks** (`finetune_dialog.py:149-168`): `FileNotFoundError` per missing bin/checkpoint naming the script that produces it; `SystemExit` for the anchors JSON. Copy verbatim, minus the mask-train bin if unused (arms are unmasked, but `DIALOG_VAL_MASK` stays required for the acquisition metric).

**The twin contract — seed IMMEDIATELY before GPT build** (`finetune_dialog.py:170-193`):
```python
    summary = preflight_device(strict=True)
    print(f"[finetune_dialog] preflight: {summary}")
    runtime = RuntimeConfig()

    # weights_only=False: TRUSTED-only read of the project's OWN anchor checkpoint (T-12-10).
    blob = torch.load(BEST_PATH, weights_only=False)
    # seed_everything IMMEDIATELY before the GPT build: the batch sampler draws from the
    # GLOBAL numpy rng, so this is what makes the Phase-13 identical-seed λ=0 twin share the
    # data order bit-for-bit (DEMO-04). Anchor weights via load_state_dict — the pretrain
    # optimizer/step/RNG state is deliberately NOT restored (fresh AdamW + fresh schedule).
    seed_everything(SEED)
    model_cfg = ModelConfig(**blob["model_config"])
    model = GPT(model_cfg)
    model.load_state_dict(blob["model"])
    model.to(runtime.device)

    # theta_star: detached CPU clones from named_parameters — the tied wte/lm_head storage
    # appears exactly once (estimate_fisher_tinystories register).
    theta_star = {n: p.detach().clone().cpu() for n, p in model.named_parameters()}
    fingerprint = {"git_sha": blob["git_sha"], "step": blob["step"], "val_loss": blob["val_loss"]}
    cache = load_fisher(FISHER_CACHE, expected_fingerprint=fingerprint)
    fisher, fisher_meta = cache["fisher"], cache["fisher_meta"]
    # EWCPenalty constructed ONCE; λ* consumed in anger (EWC-03).
    penalty = EWCPenalty(fisher, theta_star, LAMBDA_STAR, runtime.device)
```
Replicate this call ORDER exactly in both arms — no RNG draw may occur between `seed_everything(SEED)` and `train()` beyond what this sequence performs (RESEARCH Pitfall 2). The one-bit difference: naive arm passes `penalty_fn=None` to `train()`; both arms may still CONSTRUCT `EWCPenalty` for the diagnostic `ewc_penalty` CSV column (trajectory-safe — `EWCPenalty` is RNG-free, and extra eval fns run inside the loop's RNG snapshot, `loop.py:439-445`).

**Eval fns + step-0 CSV pre-seed** (`finetune_dialog.py:117-127, 199-227`):
```python
def _preseed_csv(csv_path, fieldnames, step0_values):
    """TUNE-02 step-0 row: the v1.0 eval block logs NO step-0 row (12-01 pinned fact), so
    pre-create the CSV with the header + a measured step-0 row before train() appends."""
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, restval="")
        writer.writeheader()
        row = {"step": 0, "tokens": 0, "wall_clock": 0}
        row.update(step0_values)
        writer.writerow(row)
```
```python
    fns = {
        "dialog_ppl": lambda m: masked_perplexity(
            m, DIALOG_VAL, DIALOG_VAL_MASK, BLOCK_SIZE, device, forbid_ids=forbid
        )[0],
        "retention_ppl": lambda m: retention_perplexity(m, RETENTION_BIN, BLOCK_SIZE, device, tok)[
            0
        ],
        "ewc_penalty": lambda m: float(penalty(m)),
    }

    # Step-0 row measured OUTSIDE train() (the loop logs no step-0 row — 12-01 pinned fact).
    model.eval()
    dialog_ppl0, dialog_tokens0 = masked_perplexity(
        model, DIALOG_VAL, DIALOG_VAL_MASK, BLOCK_SIZE, device, forbid_ids=forbid
    )
    step0 = {
        "dialog_ppl": dialog_ppl0,
        "retention_ppl": anchors["retention_ppl_subbin_step0"],
        "ewc_penalty": 0.0,  # exactly 0.0 at the anchor (estimate_fisher proof d)
    }
    ...
    fieldnames = CSV_FIELDNAMES + sorted(fns)
    _preseed_csv(PROD_CSV, fieldnames, step0)
```
Keep the `fns` dict IDENTICAL in both arms so CSV schemas match for plotting. `model.train()` must be called before `train()` (`finetune_dialog.py:240` — Pitfall 7: `perplexity()` leaves the model in eval mode).

**train() invocation** (`finetune_dialog.py:229-265`):
```python
    cfg = TrainConfig(
        lr=LR_STAR,
        batch_size=BATCH_SIZE,
        grad_accum_steps=GRAD_ACCUM,
        max_steps=PROD_MAX_STEPS,
        seed=SEED,
    )
    ...
    model.train()
    train(
        train_config=cfg,
        runtime_config=runtime,
        model=model,
        model_config=model_cfg,
        train_bin=DIALOG_TRAIN,
        val_bin=DIALOG_VAL,
        train_mask_bin=None,
        val_mask_bin=DIALOG_VAL_MASK,  # ALWAYS — in-loop val_loss gates best.pt (USER LOCK 3)
        penalty_fn=penalty,            # ← THE one bit: None in the naive arm
        extra_eval_fns=fns,
        checkpoint_extra={...},        # EWC arm only (fisher/theta_star/λ/meta ride the ckpt)
        log_path=str(PROD_CSV),        # ← per-arm scoped path
        eval_interval=EVAL_INTERVAL,
        checkpoint_path=str(CONVBASE_LATEST),   # ← per-arm scoped path
        best_checkpoint_path=str(CONVBASE_BEST),  # OPTIONAL for Phase 13 (D-08) — see note
    )
```
D-08 note: RESEARCH Pattern 4 recommends OMITTING `best_checkpoint_path` (end-of-call `checkpoint_path` save IS the step-4000 state; best-save is trajectory-neutral either way — `loop.py:414-479` best block only reads state).

**End-of-run loud proofs** (`finetune_dialog.py:128-131, 268-282`):
```python
def _prove(condition, message):
    """Loud end-of-run proof: SystemExit naming the violated contract (never bare assert)."""
    if not condition:
        raise SystemExit(f"[finetune_dialog] PROOF FAILED: {message}")
```
```python
    with open(PROD_CSV, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    _prove(rows and rows[0]["step"] == "0", "finetune_prod.csv has no step-0 row (TUNE-02)")
    _prove(
        int(float(rows[-1]["step"])) == PROD_MAX_STEPS,
        f"final CSV row step {rows[-1]['step']} != PROD_MAX_STEPS {PROD_MAX_STEPS}",
    )
    ret_col = [float(r["retention_ppl"]) for r in rows if r.get("retention_ppl") not in ("", None)]
    _prove(
        ret_col and all(math.isfinite(v) for v in ret_col),
        "retention_ppl column missing or non-finite somewhere in finetune_prod.csv",
    )
```
Phase 13 adds per-arm proofs plus the D-11 cross-check (EWC arm step-4000 vs `finetune_prod.csv`: dialog_ppl 4.573349214207799, retention_ppl 3.891139975617828; divergence > 2×0.068930 blocks the report). A step-250 early row check against prod (5.101385…, 3.904004…) catches twin drift at minute 3 instead of 37 (RESEARCH Pitfall 2).

**Provenance block print** (`finetune_dialog.py:305-312`):
```python
    print("[finetune_dialog] ===== Phase-13 provenance (λ=0 twin must match all but λ) =====")
    print(f"  seed: {SEED} (seed_everything immediately before GPT build — owns data order)")
    print(f"  train_config: {cfg}")
    print(f"  mask_arm: {MASK_ARM} (train_mask_bin=None)")
    print(f"  ewc_lambda: {LAMBDA_STAR} (the ONE bit the λ=0 twin flips)")
    print(f"  anchor fingerprint: {fingerprint}")
    print(f"  driver git_sha: {git_sha()}")
```
Echo per arm — this satisfies the "identicality-proof mechanism" discretion item cheaply.

**Pre-registration constants block (D-10)** — analog `scripts/finetune_smoke.py:77-121`:
```python
# ===== PRE-REGISTRATION (D-01..D-07, locked before any smoke number) =====
#
# USER DECISIONS transcribed verbatim from 12-04-PLAN.md pre_registration §1-§9. This block is
# committed BEFORE any run executes — git history order is the pre-registration proof (T-12-08).

# §2 — K chosen BLIND: a deliberately conservative default fixed before any smoke result
# exists; ...
K = 2
...
EVAL_INTERVAL = 250  # §3/§7/§8 logging cadence for all non-Stage-1 arms
BLOCK_SIZE = 256  # ModelConfig.block_size — every PPL sweep window
BATCH_SIZE = 32  # per-interfaces constant for all arms
GRAD_ACCUM = 1  # sidesteps the λ/accum scaling class entirely (Pitfall 2)
SEED = 1337  # TrainConfig default — every non-noise-B arm
```
Phase 13's block: `K = 2`, `DELTA_RET = 0.068930` (state the regime: seed-pair floor, masked arm, LR 9e-5, 1250 steps — D-05), `MARGIN = K * DELTA_RET`, `LAMBDA_EWC = 0.01`, `LR = 9e-5`, `MAX_STEPS = 4000`, `SEED = 1337`, `BATCH_SIZE = 32`, `GRAD_ACCUM = 1` — each with a report/log citation comment, committed BEFORE either arm runs. Also copy the anti-pattern comment: "Hardcoded on purpose — the driver never parses the report for numbers" (`finetune_dialog.py:75`). Phase 13 needs NO `_require_go_verdict` gate — its pre-registration is the committed driver itself.

---

### `scripts/plot_phase13.py` (plotting, CSV → PNG)

**Analog:** `demo.ipynb` cells 2 & 4 — the only matplotlib code in the repo. Same read-committed-CSV-with-stdlib-csv + default-color-cycle pattern; the new script adds `plt.savefig(...)` (the notebook uses `plt.show()` — no `savefig` exists anywhere yet, so output-saving is new but trivial).

**CSV read + plot pattern** (demo.ipynb cell 2):
```python
import csv

import matplotlib.pyplot as plt

with open("results/run.csv") as f:
    rows = list(csv.DictReader(f))

steps = [int(r["step"]) for r in rows]
val_loss = [float(r["val_loss"]) for r in rows]

plt.figure(figsize=(8, 4.5), dpi=100)
plt.plot(steps, val_loss, color="C1", label="val")
plt.xlabel("step")
plt.ylabel("loss")
plt.legend()
```

**Multi-series fixed-order pattern** (demo.ipynb cell 4):
```python
# Fixed series order + colors (08-UI-SPEC plot contract): matplotlib default cycle only.
ABLATIONS = [
    ("baseline", "C0"),
    ("no_tie", "C1"),
    ...
]
for name, color in ABLATIONS:
    with open(f"results/abl_{name}.csv") as f:
        abl_rows = list(csv.DictReader(f))
    plt.plot([int(r["step"]) for r in abl_rows], [float(r["val_loss"]) for r in abl_rows],
             color=color, label=name)
```

Phase-13 specifics the analog does not cover (from RESEARCH, all load-bearing):
- **Pitfall 1:** `ft_lr_9e-5.csv` has NO `retention_ppl` column. The λ=0 frontier point is hardcoded with citation: `LAMBDA0_POINT = {"dialog_ppl": 4.4453, "retention_ppl": 5.9553}` (smoke report Stage 2/3, commit 666d096) — and the report carries the explicit exception row.
- **Pitfall 3:** dashed baseline = **2.1066** (v1.0 headline, requirement text); step-0 curve points = **2.107553076833866** (`retention_anchors.json`). Never swap them.
- **Pitfall 4:** label budgets per figure — VIZ-04 caption "1250-step sweep endpoints", VIZ-01 "4000-step arms".
- Recommendation (RESEARCH Open Q2): PNG ~150–200 dpi into `results/` next to the report.

Script skeleton: follow the thin no-CLI `main()` + `_REPO_ROOT` constants pattern from `scripts/evaluate.py:46-59` (no torch import needed — pure csv+matplotlib).

---

### `scripts/make_retention_samples.py` (sampling script, generation → tracked markdown)

**Analog:** `scripts/make_transcripts.py` (protocol, proxies, seeded selection, collect) + `scripts/evaluate.py` (TinyStories prompt framing, samples.md layout).

**Header/env/load pattern** (`make_transcripts.py:23-63`): same MPS-fallback-before-torch header, `_REPO_ROOT` constants, `preflight_device(strict=True)`, trusted-only `torch.load(weights_only=False)` with the T-12-10 comment. Phase 13 loads BOTH arm endpooint checkpoints in ONE script run (D-12).

**Seeded prompt selection + completion helper** (`make_transcripts.py:56-81, 123-127`):
```python
N_TRANSCRIPTS = 15
SEED = 1337  # seeded LOCAL episode selection + seeded warm sampling
MAX_NEW_TOKENS = 128
STOP_IDS = {8184, 8185}  # eos + <|user|>  ← Phase 13 story mode: {8184} only (RESEARCH Pattern 5)
ROLE_IDS = (8185, 8186, 8187)  # leakage check set — KEEP: role tokens mid-story = forgetting axis


def _complete(model, prompt_ids, device, forbid, **kw):
    """One completion: returns (generated_ids, stopped_on_stop_id)."""
    idx = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    out = collect(
        model, idx, max_new_tokens=MAX_NEW_TOKENS, forbid_ids=forbid, stop_ids=STOP_IDS, **kw
    )
    gen = out[0, len(prompt_ids) :].tolist()
    # generate() stops WITHOUT yielding the stop id (D-05): fewer than max_new_tokens
    # generated tokens means a stop-id termination.
    return gen, len(gen) < MAX_NEW_TOKENS
```
```python
    rng = np.random.default_rng(SEED)  # seeded LOCAL rng — global streams untouched
    picks = sorted(int(i) for i in rng.choice(len(episodes), size=N_TRANSCRIPTS, replace=False))

    seed_everything(SEED)  # seeded warm sampling (deterministic transcript re-runs)
```
Phase-13 prompt source: seeded story prefixes from `data/TinyStoriesV2-GPT4-valid.txt` encoded through the frozen tokenizer (RESEARCH Pattern 5) — NOT hand-formatted strings (inflation-report Pitfall 4 lineage).

**Measured-proxies markdown header** (`make_transcripts.py:164-183`):
```python
    stop_frac = n_stopped / n_completions
    header = [
        "# PersonaCore — Conversational-Base Transcripts (TUNE-01)",
        "",
        "> These transcripts are REPRESENTATIVE, not cherry-picked: episodes are drawn from",
        "> the held-out PersonaChat valid split with a seeded rng (default_rng(1337)). ...",
        "",
        "## Adherence Proxies (measured over all generations)",
        "",
        f"- Stop-id termination fraction: **{n_stopped}/{n_completions} = {stop_frac:.2f}**",
        f"- Mid-generation role-token leakage (ids 8185/8186/8187): **{leakage}** (expected 0)",
        ...
    ]
    TRANSCRIPTS_PATH.write_text("\n".join(header + blocks), encoding="utf-8")
```
Per-checkpoint sections follow `evaluate.py:144-155` (greedy + warm block per prompt, `**Greedy (deterministic):**` / `**Warm (temperature=0.8, top_p=0.95):**`).

---

### `results/phase13_ab_report.md` (evidence report)

**Analog:** `results/finetune_smoke_report.md` layout (verified structure):
```markdown
# Fine-Tune Calibration Smoke Report (Phase 12 Plan 04 — D-01..D-07)

> **What these numbers are:** ... each produced by a rule committed
> in `scripts/finetune_smoke.py` BEFORE any smoke number existed (git history is the
> pre-registration proof). **Frozen gate policy (§1):** ...
> **What they are not:** ...

## Pre-Registration

| Constant | Value | Rationale |
| --- | --- | --- |
| K | 2 | chosen BLIND before any smoke number — ... |
...
## Verdict
```
Phase-13 sections (from D-05/D-06/D-09/D-10/D-11 + Pitfall 1): opening blockquote (what the numbers are/are not) → `## Pre-Registration` table with constants + the commit SHA where each rule was locked, INCLUDING the λ=0-frontier-point exception row (Pitfall 1 mandatory note) → 2×2 end-of-run table → gate verdict → D-11 reproduction cross-check table vs `finetune_prod.csv` → D-05 threats-to-validity register (floor regime + limitation + free within-run trajectory check) → ONE D-09 reconciliation section (§8 search vs Phase-13 demonstration) → figures + samples references.

---

### `results/phase13_naive/` and `results/phase13_ewc/` CSVs (driver output)

**Analog:** `results/finetune_prod.csv` — schema `step,train_loss,val_loss,lr,tokens,wall_clock,dialog_ppl,ewc_penalty,retention_ppl` (= `CSV_FIELDNAMES + sorted(fns)`), pre-seeded step-0 row, 250-step cadence to step 4000. Keep both arm schemas identical (include the diagnostic-only `ewc_penalty` column in the naive arm; report footnote "measured, not applied" — RESEARCH Open Q1). Appending new columns to a pre-existing CSV raises by design (T-12-02) — the refuse-to-rerun guard prevents ever hitting that path.

---

### `tests/test_phase13_driver.py` (unit test, CPU-only)

**Analog (style):** `tests/test_ablation_config.py` — docstring listing each test's pinned contract, CPU-only, no checkpoint/fixture I/O, exact verified literals:
```python
"""EVAL-03 ablation-flag semantics — ...

CPU-only, GPU/MPS-free, no checkpoint/fixture-file I/O. Pins three things:
  1. ``test_defaults_unchanged`` — ...
"""

import torch

from personacore.config import ModelConfig
from personacore.model import GPT


def test_defaults_unchanged():
    """Defaults reproduce today's arch: tied head + 13,891,584 params."""
    model = GPT(ModelConfig())
    assert model.lm_head.weight.data_ptr() == model.wte.weight.data_ptr()
    assert count_parameters(model) == 13_891_584
```

**CONVENTION WARNING for the planner:** no existing test imports anything from `scripts/` — `tests/test_demo_callback.py`'s docstring states it explicitly ("imports NOTHING from gradio or scripts/ — the testable demo slice lives in the package"). RESEARCH Wave-0 wants guard/gate-arithmetic/config-identicality units against the driver. Two conforming options; pick one and state it in the plan:
1. **`importlib.util.spec_from_file_location` load of the driver module** in the test (new pattern, no in-repo precedent — the driver's `main()` guard must not run on import, which the existing `if __name__ == "__main__":` structure already ensures). Gate arithmetic and guard lists must be module-level pure functions/constants, mirroring `finetune_smoke.py:145+` ("Gate formulas (pure functions over logged numbers)").
2. Keep the convention: put the verdict function (`ewc_mitigates(naive_ret, ewc_ret) -> bool` over `MARGIN`) somewhere package-importable, or test guard behavior black-box via `subprocess` against tmp outputs. Option 1 is smaller; option 2 preserves the stated convention.

Gate-arithmetic test content: hand-built inputs around the boundary (`delta == MARGIN` fails, `delta > MARGIN` passes), exact constants `K == 2`, `DELTA_RET == 0.068930`, both arms' `TrainConfig` equal, one-bit λ diff.

---

### `tests/test_phase13_plots.py` (optional smoke test)

No direct analog — no plotting test exists. If written: call the plot function(s) with the committed sweep CSVs and `tmp_path` output, assert files exist and the frontier has SIX points (the Pitfall-1 regression: a naive CSV-only read yields five). If plotting stays `__main__`-thin, skip with the manual-only justification (RESEARCH Validation table allows it).

## Shared Patterns

### MPS fallback env header
**Source:** `finetune_dialog.py:37-40` (identical in `make_transcripts.py:28-31`, `evaluate.py:34-37`, `finetune_smoke.py:45-48`)
**Apply to:** every new script that imports torch
```python
# An uncovered MPS op falls back to CPU rather than crashing the multi-hour run — set BEFORE torch.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import torch  # noqa: E402  (must follow the MPS-fallback env set above)
```

### Thin no-CLI driver + `_REPO_ROOT` path constants
**Source:** `evaluate.py:46-50`, `finetune_dialog.py:55-69`
**Apply to:** all three new scripts — no argparse; all paths are `_REPO_ROOT`-relative module constants with a trailing comment stating tracked/gitignored/frozen status.
```python
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BEST_PATH = _REPO_ROOT / "checkpoints" / "best.pt"  # own trusted anchor checkpoint
```

### Trusted-only deserialization comments
**Source:** `finetune_dialog.py:174-175, 284`, `make_transcripts.py:104-105`
**Apply to:** every `torch.load` in the driver and sample script
```python
    # weights_only=False: TRUSTED-only read of the project's OWN anchor checkpoint (T-12-10).
    blob = torch.load(BEST_PATH, weights_only=False)
```
Fisher cache goes through `load_fisher` (`weights_only=True`, fingerprint-pinned) — never raw `torch.load`.

### Loud failure over silent: `SystemExit` naming the contract
**Source:** `finetune_dialog.py:128-131` (`_prove`), guard at `:140-147`, `finetune_smoke.py` gates
**Apply to:** driver guards, end-of-run proofs, the D-11 divergence block — never bare `assert` in scripts, never silent overwrite.

### Hardcode-with-citation, never parse reports at runtime
**Source:** `finetune_dialog.py:71-89` (constants block), `:75` ("the driver never parses the report for numbers"), `finetune_smoke.py:77-143`
**Apply to:** driver pre-registration block, plot script's `LAMBDA0_POINT`, report generator constants.

### Docstring contract header + `print(f"[script_name] ...")` progress lines
**Source:** all four analog scripts
**Apply to:** all new scripts — module docstring states what/why/security/run-command; every print is prefixed `[finetune_ab]` etc.

### "REPRESENTATIVE, not cherry-picked" register preamble
**Source:** `make_transcripts.py:166-173`, `evaluate.py:118-125`
**Apply to:** sample markdown and the A/B report's sample section.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `tests/test_phase13_plots.py` | test | smoke | No plotting code has ever been tested (plots live only in `demo.ipynb`); use RESEARCH validation guidance (tmp_path smoke or documented manual-only) |

Partial-analog caveat already flagged above: `tests/test_phase13_driver.py` has a style analog but no precedent for importing `scripts/` code from tests — planner must resolve (importlib load vs package-level verdict function).

## Metadata

**Analog search scope:** `scripts/`, `tests/`, `src/personacore/`, `results/`, `demo.ipynb`
**Files scanned:** 20 scripts listed, 55 tests listed; 6 read in full or targeted (`finetune_dialog.py`, `make_transcripts.py`, `evaluate.py`, `finetune_smoke.py:1-150`, `test_ablation_config.py`, `test_demo_callback.py:1-40`, demo.ipynb plot cells, smoke-report headers)
**Pattern extraction date:** 2026-08-01
