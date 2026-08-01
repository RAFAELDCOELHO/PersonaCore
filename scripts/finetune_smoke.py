"""D-03 sequential calibration smoke driver (Phase 12 Plan 04: EWC-03 / TUNE-01 / TUNE-02).

Runs the full pre-registered smoke sequence through ONE process on the M3 (MPS, fp32):

  Stage 0   budget recalibration (slope rule on the dialogue corpus — TinyStories band DROPPED)
  Stage 0b  seed-pair noise floor at the recalibrated budget (Δ_dialog / Δ_ret; margins = K×Δ)
  Stage 1   masked-vs-unmasked training loss + D-04 cold-start diagnostic (role-embedding norms)
  Stage 2   LR sweep on the mask winner (retention + instability gates; LR* = lowest dialogue PPL)
  Stage 3   λ sweep on the LR* arm (λ* = largest λ within margin of λ=0; demonstrability guard)

Every decision is a NUMBER compared against a pre-registered threshold — never a human reading
a plot. The constants block below is the pre-registration: it is COMMITTED before any smoke
number exists (git order is the proof, T-12-08). Any violated gate raises SystemExit naming the
gate and the numbers — the executor stops and surfaces it to the user (D-07 exception); rules
that pass auto-proceed stage to stage.

Two-pass lock flow (D-03): SMOKE_STEPS starts as a sentinel (0). The first invocation runs
Stage 0, prints the slope-rule recommendation and SystemExits; the executor locks the value
into SMOKE_STEPS (single-constant edit, committed) and re-runs. Skip-if-done makes the
multi-hour sequence idempotently restartable (T-12-11): a completed arm (CSV final row at
max_steps + its own end-of-run checkpoint) is skipped and its numbers re-measured from that
checkpoint; a partial CSV is deleted and the arm restarts from the anchor.

Mirrors scripts/run_ablations.py (thin no-CLI driver): MPS-fallback env before torch import,
_REPO_ROOT path constants, preflight_device(strict=True) gate, seed_everything IMMEDIATELY
before each explicit GPT build (the batch sampler draws from the GLOBAL numpy rng — seeding
before the build is what makes same-seed arms share the data order bit-for-bit, D-05).

SECURITY: torch.load(weights_only=False) reads ONLY the project's OWN checkpoints
(checkpoints/best.pt + per-arm ft_*_latest.pt written by this driver — T-12-10 trusted-only);
the Fisher cache goes through load_fisher (weights_only=True) with the anchor fingerprint trio
read from the best.pt blob. Committed artifacts are markdown + stdlib CSV — no pickle.

Run: ``python scripts/finetune_smoke.py`` (inside the Python 3.11 venv, on the M3).
"""

import csv
import json
import math
import os
import pathlib
import shutil
import time

# An uncovered MPS op falls back to CPU rather than crashing the multi-hour run — set BEFORE torch.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import torch  # noqa: E402  (must follow the MPS-fallback env set above)

from personacore.checkpoint import load_fisher  # noqa: E402
from personacore.config import ModelConfig, RuntimeConfig, TrainConfig  # noqa: E402
from personacore.continual import EWCPenalty  # noqa: E402
from personacore.evaluation import masked_perplexity, retention_perplexity  # noqa: E402
from personacore.generation.text import undecodable_ids_mask  # noqa: E402
from personacore.model import GPT  # noqa: E402
from personacore.preflight import preflight_device  # noqa: E402
from personacore.seeding import seed_everything  # noqa: E402
from personacore.tokenizer import from_json  # noqa: E402
from personacore.training import train  # noqa: E402
from personacore.training.loop import CSV_FIELDNAMES  # noqa: E402

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DIALOG_TRAIN = _REPO_ROOT / "data" / "dialog_train.bin"  # 5,257,858 tokens (gitignored data/)
DIALOG_TRAIN_MASK = _REPO_ROOT / "data" / "dialog_train_mask.bin"  # aligned uint8 mask
DIALOG_VAL = _REPO_ROOT / "data" / "dialog_val.bin"  # 637,633 tokens
DIALOG_VAL_MASK = _REPO_ROOT / "data" / "dialog_val_mask.bin"
RETENTION_BIN = _REPO_ROOT / "data" / "retention_val.bin"  # frozen sub-bin (Plan 12-03)
BEST_PATH = _REPO_ROOT / "checkpoints" / "best.pt"  # own trusted anchor checkpoint
FISHER_CACHE = _REPO_ROOT / "checkpoints" / "fisher_tinystories.pt"  # shared production cache
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"  # FROZEN artifact — never retrain
ANCHORS_JSON = _REPO_ROOT / "results" / "retention_anchors.json"  # committed step-0 anchors
RESULTS_DIR = _REPO_ROOT / "results"  # git-TRACKED per-arm CSVs + the smoke report
CKPT_DIR = _REPO_ROOT / "checkpoints"  # gitignored — smoke checkpoints are intermediate
REPORT_PATH = RESULTS_DIR / "finetune_smoke_report.md"  # D-06 committed evidence
WALL_CACHE = CKPT_DIR / "ft_walltimes.json"  # local wall-clock cache (survives the 2-pass flow)

# ===== PRE-REGISTRATION (D-01..D-07, locked before any smoke number) =====
#
# USER DECISIONS transcribed verbatim from 12-04-PLAN.md pre_registration §1-§9. This block is
# committed BEFORE any run executes — git history order is the pre-registration proof (T-12-08).

# §2 — K chosen BLIND: a deliberately conservative default fixed before any smoke result
# exists; no principled derivation is available at this budget (stated in the report). For each
# gate the report also records the counterfactual k the observed deltas would have required.
K = 2

# §3 — Stage 0 calibration budget. ONE run (masked arm, LR 9e-5 mid-sweep, seed 1337).
CAL_MAX_STEPS = 5000

# §3 — SENTINEL (0) until the slope rule recommends a budget; the executor locks the value here
# and re-runs (two-pass flow). Enforced run_ablations-style: SystemExit when
# |recommended − SMOKE_STEPS| > EVAL_INTERVAL ("update the constant and re-run").
SMOKE_STEPS = 0

# §7 — LR grid: pretrain peak 3e-4 (pretrain_tinystories.py) × {1, 0.3, 0.1}.
LR_GRID = (3e-4, 9e-5, 3e-5)
LR_MID = 9e-5  # the mid-sweep LR used by Stage 0 / 0b / 1 (§3, §5)

# §8 — λ decade grid centered on 1: the Fisher is mean-normalized, so λ reads as stiffness
# relative to an average parameter, collapsing the literature's 0.1–1e6 spread toward O(1).
LAMBDA_GRID = (0.01, 0.1, 1.0, 10.0, 100.0)
# §8 boundary-extension rule: λ* on a grid endpoint ⇒ extend one decade that direction, run one
# extra arm, re-apply. Bounded so a pathological sweep halts loudly instead of running forever.
LAMBDA_EXTENSION_LIMIT = 3

# §2 — Stage 0b: one smoke config (masked, LR_MID, SMOKE_STEPS) run twice at these seeds.
NOISE_SEEDS = (1337, 2024)

# §6 — cold-start diagnostic cadence (whole Stage-1 run; first 10% of budget is the window).
COLDSTART_EVAL_INTERVAL = 25
COLDSTART_WINDOW_FRAC = 0.10

EVAL_INTERVAL = 250  # §3/§7/§8 logging cadence for all non-Stage-1 arms
SLOPE_WINDOW = 1000  # §3 slope rule: trailing/leading improvement windows (steps)
SLOPE_FRAC = 0.15  # §3: flattened when trailing improvement < 15% of the first-window drop
BLOCK_SIZE = 256  # ModelConfig.block_size — every PPL sweep window
BATCH_SIZE = 32  # per-interfaces constant for all arms
GRAD_ACCUM = 1  # sidesteps the λ/accum scaling class entirely (Pitfall 2)
SEED = 1337  # TrainConfig default — every non-noise-B arm
ROLE_IDS = {"user": 8185, "assistant": 8186, "system": 8187}  # reserved decodable role tokens
PROD_MAX_STEPS_PROPOSAL = 4000  # production budget proposal, grounded in measured wall-clock

# Pre-registered reuse (declared HERE, before any number): the Stage-2 LR 9e-5 arm is
# config-identical BY CONSTRUCTION to the Stage-0b seed-1337 noise arm (masked, LR_MID, seed
# 1337, SMOKE_STEPS, eval_interval 250, extras {dialog_ppl}) — same seed ⇒ same data order ⇒
# identical trajectory. When the Stage-1 winner is the masked arm, the 9e-5 arm reuses the
# noise-A run (CSV copied to ft_lr_9e-5.csv) instead of re-running a bit-identical trajectory.
# If the unmasked arm wins Stage 1, the reuse does NOT apply and the arm runs fresh.
REUSE_NOISE_A_AS_LR_MID = True

# §4 fallback operationalization detail (locked now): the "total signal" the undefinable-gate
# check compares the margin against is (first TRAINED interval dialog_ppl − last interval
# dialog_ppl) of the Stage 0 run — the pre-seeded step-0 row is excluded, which makes the
# fallback MORE likely to fire (conservative: it escalates to a user checkpoint, never past one).

# §8 within-margin operationalization detail (locked now): "within K×Δ_dialog of the λ=0 arm"
# is one-sided — a λ arm passes when it is not WORSE than λ=0 by more than the margin
# (ppl_λ − ppl_0 ≤ K×Δ_dialog). A λ arm strictly BETTER than λ=0 trivially satisfies the
# plasticity condition the margin exists to test.

# §8 demonstrability guard (locked now, literal §8 text): retention(λ*) must beat retention(λ=0)
# by MORE than Δ_ret — the raw floor, NOT K×Δ_ret.


# ===== Gate formulas (pure functions over logged numbers) =====


def counterfactual_k(decision_delta, noise_delta):
    """The k this gate WOULD have required: observed decision delta / observed noise delta."""
    if noise_delta <= 0.0:
        return float("inf")
    return abs(decision_delta) / noise_delta


def slope_recommendation(curve):
    """§3 slope rule over [(step, dialog_ppl)]: smallest S where the trailing SLOPE_WINDOW
    improvement < SLOPE_FRAC × the first-SLOPE_WINDOW improvement. Returns (steps, capped)."""
    first_step, first_ppl = curve[0]
    early = next((p for s, p in curve if s - first_step >= SLOPE_WINDOW), curve[-1][1])
    first_improvement = max(first_ppl - early, 1e-9)
    for idx, (step, ppl) in enumerate(curve):
        prior = next((p for s, p in reversed(curve[:idx]) if step - s >= SLOPE_WINDOW), None)
        if prior is None:
            continue
        if (prior - ppl) < SLOPE_FRAC * first_improvement:
            return step, False
    return CAL_MAX_STEPS, True  # never flattened — capped (recorded as such in the report)


def nan_inf_fields(rows):
    """All (step, column, value) cells whose numeric value is NaN/Inf."""
    bad = []
    for r in rows:
        for key, v in r.items():
            if v in (None, ""):
                continue
            try:
                x = float(v)
            except ValueError:
                continue
            if not math.isfinite(x):
                bad.append((r.get("step"), key, v))
    return bad


def instability_check(rows, margin):
    """§4: unstable iff (a) any NaN/Inf in logged columns, OR (b) any interval-to-interval
    INCREASE in the run's dialog_ppl column exceeding the margin (K×Δ_dialog)."""
    bad = nan_inf_fields(rows)
    col = [p for _, p in read_col(rows, "dialog_ppl")]
    worst = None
    for a, b in zip(col, col[1:]):
        inc = b - a
        if worst is None or inc > worst:
            worst = inc
    violated = bool(bad) or (worst is not None and worst > margin)
    return {"nan_inf": bad, "max_dialog_ppl_increase": worst, "violated": violated}


def cold_start_trigger(rows, max_steps):
    """§6 mechanical trigger over the first COLDSTART_WINDOW_FRAC of logged intervals:
    NaN/Inf in the window, OR val_loss at the 10%-of-budget interval > first-interval val_loss
    (no net recovery from the cold-start window). Pre-seeded step-0 rows are not intervals."""
    limit = COLDSTART_WINDOW_FRAC * max_steps
    window = [r for r in rows if 0 < int(float(r["step"])) <= limit]
    bad = nan_inf_fields(window)
    vl = [float(r["val_loss"]) for r in window if r.get("val_loss") not in (None, "")]
    no_recovery = len(vl) >= 2 and vl[-1] > vl[0]
    detail = {
        "nan_inf": bad,
        "val_loss_first": vl[0] if vl else None,
        "val_loss_at_10pct": vl[-1] if vl else None,
        "no_recovery": no_recovery,
    }
    return (bool(bad) or no_recovery), detail


def retention_collapse(after_ppl, anchor_ppl, margin):
    """§7(a): after-run sub-bin retention PPL drifting above the step-0 anchor by > margin."""
    return (after_ppl - anchor_ppl) > margin


def pick_lambda_star(arm_ppls, lam0_ppl, margin, grid):
    """§8 λ* rule: largest λ whose end dialogue PPL is within margin of the λ=0 arm's
    (one-sided — see the pre-registration comment). Returns (lam_star, candidates, endpoint)
    where endpoint is -1/0/+1 for on-low-end / interior-or-none / on-high-end."""
    candidates = sorted(lam for lam in grid if arm_ppls[lam] - lam0_ppl <= margin)
    if not candidates:
        return None, [], 0
    lam_star = candidates[-1]
    endpoint = 1 if lam_star == max(grid) else (-1 if lam_star == min(grid) else 0)
    return lam_star, candidates, endpoint


# ===== CSV / bookkeeping helpers =====


def read_rows(path):
    """All DictReader rows of a train()-written arm CSV."""
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def read_col(rows, key):
    """[(step, value)] for a column, skipping empty cells (the _read_val_curve idiom)."""
    out = []
    for r in rows:
        v = r.get(key, "")
        if v in (None, ""):
            continue
        out.append((int(float(r["step"])), float(v)))
    return out


def _record_wall(name, wall_s, steps):
    cache = json.loads(WALL_CACHE.read_text()) if WALL_CACHE.exists() else {}
    cache[name] = {"wall_s": wall_s, "steps": steps}
    WALL_CACHE.write_text(json.dumps(cache, indent=2))


def _get_wall(name):
    if not WALL_CACHE.exists():
        return None
    return json.loads(WALL_CACHE.read_text()).get(name)


def _lr_name(lr):
    """3e-4 -> '3e-4' (matches the tracked results/ft_lr_*.csv naming)."""
    return f"{lr:.0e}".replace("e-0", "e-")


# ===== Anchor / arm machinery =====


def _fresh_model(ctx, seed):
    """seed_everything IMMEDIATELY before the explicit GPT build (data-order ownership — the
    batch sampler draws from the GLOBAL numpy rng), then load the anchor weights. Anchor
    weights come from the best.pt blob via load_state_dict — the pretrain optimizer/step/RNG
    state in the blob is deliberately NOT restored (fresh AdamW + fresh schedule per arm)."""
    seed_everything(seed)
    model_cfg = ModelConfig(**ctx["blob"]["model_config"])
    model = GPT(model_cfg)
    model.load_state_dict(ctx["blob"]["model"])
    model.to(ctx["runtime"].device)
    return model, model_cfg


def _extras_for(ctx, spec, penalty):
    """Build (extra_eval_fns, step0_values) for an arm from its extras spec."""
    device = ctx["runtime"].device
    fns, step0 = {}, {}
    for tag in spec:
        if tag == "dialog_ppl":
            fns["dialog_ppl"] = lambda m: masked_perplexity(
                m, DIALOG_VAL, DIALOG_VAL_MASK, BLOCK_SIZE, device, forbid_ids=ctx["forbid"]
            )[0]
            step0["dialog_ppl"] = ctx["dialog_ppl0"]
        elif tag == "retention_ppl":
            fns["retention_ppl"] = lambda m: retention_perplexity(
                m, RETENTION_BIN, BLOCK_SIZE, device, ctx["tok"]
            )[0]
            step0["retention_ppl"] = ctx["anchors"]["retention_ppl_subbin_step0"]
        elif tag == "ewc_penalty":
            fns["ewc_penalty"] = lambda m: float(penalty(m))
            step0["ewc_penalty"] = 0.0  # exactly 0.0 at the anchor (estimate_fisher proof d)
        elif tag == "role_norms":
            for role, rid in ROLE_IDS.items():
                fns[f"role_norm_{role}"] = lambda m, i=rid: float(m.wte.weight[i].norm().item())
                step0[f"role_norm_{role}"] = ctx["role_norms0"][role]
        else:
            raise SystemExit(f"[finetune_smoke] unknown extras tag {tag!r} (driver bug)")
    return fns, step0


def _preseed_csv(csv_path, fieldnames, step0_values):
    """TUNE-02 step-0 row rule: the v1.0 eval block does NOT log a step-0 row (12-01 pinned
    fact — the block runs after step += 1), so pre-create the CSV with the header + a step-0
    row carrying the measured step-0 extras. CSVLogger writes its header only into a new/empty
    file, so train() appends cleanly (logging.py)."""
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, restval="")
        writer.writeheader()
        row = {"step": 0, "tokens": 0, "wall_clock": 0}
        row.update(step0_values)
        writer.writerow(row)


def _measure_end(ctx, model):
    """End-of-run gate numbers, measured by the driver with the frozen policies (§1)."""
    device = ctx["runtime"].device
    model.eval()
    dialog_ppl, dialog_tokens = masked_perplexity(
        model, DIALOG_VAL, DIALOG_VAL_MASK, BLOCK_SIZE, device, forbid_ids=ctx["forbid"]
    )
    ret_ppl, ret_tokens = retention_perplexity(model, RETENTION_BIN, BLOCK_SIZE, device, ctx["tok"])
    return dialog_ppl, dialog_tokens, ret_ppl, ret_tokens


def _run_arm(ctx, name, *, lr, lam, masked, seed, max_steps, eval_interval, extras):
    """Run (or skip-if-done) one smoke arm; return its numbers.

    masked: whether TRAINING loss is assistant-masked. Evaluation policy is frozen independent
    of the arm (Pitfall 3): val_mask_bin is ALWAYS set, and the gate numbers always come from
    masked_perplexity + retention_perplexity measured by the driver after the run.
    """
    csv_path = RESULTS_DIR / f"ft_{name}.csv"
    latest_path = CKPT_DIR / f"ft_{name}_latest.pt"
    best_path = CKPT_DIR / f"ft_{name}_best.pt"
    penalty = (
        EWCPenalty(ctx["fisher"], ctx["theta_star"], lam, ctx["runtime"].device)
        if lam is not None
        else None
    )

    # SKIP-IF-DONE (T-12-11): a completed arm is skipped; its end-of-run numbers are
    # re-measured from the arm's OWN final checkpoint (trusted, this driver wrote it).
    if csv_path.exists():
        rows = read_rows(csv_path)
        done = rows and rows[-1].get("step") and int(float(rows[-1]["step"])) == max_steps
        if done and latest_path.exists():
            lblob = torch.load(latest_path, weights_only=False)  # own trusted checkpoint
            if lblob["step"] == max_steps:
                print(f"[finetune_smoke] arm '{name}': complete at step {max_steps} — skipping")
                model = GPT(ModelConfig(**lblob["model_config"]))
                model.load_state_dict(lblob["model"])
                model.to(ctx["runtime"].device)
                d_ppl, d_tok, r_ppl, r_tok = _measure_end(ctx, model)
                wall = _get_wall(name)
                return {
                    "name": name,
                    "lr": lr,
                    "lam": lam,
                    "masked": masked,
                    "seed": seed,
                    "max_steps": max_steps,
                    "eval_interval": eval_interval,
                    "rows": rows,
                    "end_dialog_ppl": d_ppl,
                    "dialog_tokens": d_tok,
                    "end_retention_ppl": r_ppl,
                    "retention_tokens": r_tok,
                    "wall_s": wall["wall_s"] if wall else None,
                    "skipped": True,
                }
        # Stale partial run: restart the arm from the anchor (never mid-run — P4: restoring
        # a checkpoint's optimizer/step state is exactly what the anchor-load path avoids).
        print(f"[finetune_smoke] arm '{name}': stale/partial CSV — restarting from the anchor")
        csv_path.unlink()

    fns, step0 = _extras_for(ctx, extras, penalty)
    model, model_cfg = _fresh_model(ctx, seed)  # seed_everything happens INSIDE, pre-build
    fieldnames = CSV_FIELDNAMES + sorted(fns)
    _preseed_csv(csv_path, fieldnames, step0)

    cfg = TrainConfig(
        lr=lr, batch_size=BATCH_SIZE, grad_accum_steps=GRAD_ACCUM, max_steps=max_steps, seed=seed
    )
    print(
        f"[finetune_smoke] arm '{name}': lr={lr:g} lam={lam if lam is not None else '-'} "
        f"masked={masked} seed={seed} steps={max_steps} eval_interval={eval_interval}"
    )
    t0 = time.monotonic()
    train(
        train_config=cfg,
        runtime_config=ctx["runtime"],
        model=model,
        model_config=model_cfg,
        train_bin=DIALOG_TRAIN,
        val_bin=DIALOG_VAL,
        train_mask_bin=DIALOG_TRAIN_MASK if masked else None,
        val_mask_bin=DIALOG_VAL_MASK,  # ALWAYS — frozen evaluation policy (Pitfall 3)
        penalty_fn=penalty,
        extra_eval_fns=fns,
        log_path=str(csv_path),
        eval_interval=eval_interval,
        checkpoint_path=str(latest_path),
        checkpoint_interval=EVAL_INTERVAL,
        best_checkpoint_path=str(best_path),
    )
    wall = time.monotonic() - t0
    _record_wall(name, wall, max_steps)
    d_ppl, d_tok, r_ppl, r_tok = _measure_end(ctx, model)
    print(
        f"[finetune_smoke] arm '{name}': end dialog_ppl={d_ppl:.4f} "
        f"retention_ppl={r_ppl:.4f} wall={wall:.0f}s"
    )
    return {
        "name": name,
        "lr": lr,
        "lam": lam,
        "masked": masked,
        "seed": seed,
        "max_steps": max_steps,
        "eval_interval": eval_interval,
        "rows": read_rows(csv_path),
        "end_dialog_ppl": d_ppl,
        "dialog_tokens": d_tok,
        "end_retention_ppl": r_ppl,
        "retention_tokens": r_tok,
        "wall_s": wall,
        "skipped": False,
    }


# ===== Stages =====


def stage0_calibrate(ctx):
    """§3: ONE calibration run, slope-rule recommendation, run_ablations-style lock check."""
    res = _run_arm(
        ctx,
        "cal",
        lr=LR_MID,
        lam=None,
        masked=True,
        seed=SEED,
        max_steps=CAL_MAX_STEPS,
        eval_interval=EVAL_INTERVAL,
        extras=("dialog_ppl",),
    )
    curve = [(s, p) for s, p in read_col(res["rows"], "dialog_ppl") if math.isfinite(p)]
    if len(curve) < 3:
        raise SystemExit(
            f"[stage0] only {len(curve)} finite dialog_ppl points in ft_cal.csv — "
            "cannot apply the slope rule; inspect the calibration run."
        )
    recommended, capped = slope_recommendation(curve)
    print(
        f"[stage0] curve points={len(curve)} final=(step {curve[-1][0]}, ppl {curve[-1][1]:.4f}) "
        f"recommended SMOKE_STEPS={recommended} capped={capped}"
    )
    if abs(recommended - SMOKE_STEPS) > EVAL_INTERVAL:
        raise SystemExit(
            f"[stage0] slope rule recommends SMOKE_STEPS={recommended} (capped={capped}) but "
            f"the locked constant is SMOKE_STEPS={SMOKE_STEPS}. Update the constant and "
            "re-run (D-03 lock enforcement)."
        )
    return {"res": res, "curve": curve, "recommended": recommended, "capped": capped}


def stage0b_noise(ctx, cal):
    """§2: seed-pair noise floor at SMOKE_STEPS; §4 pre-registered fallback check."""
    arms = []
    for tag, seed in zip(("noise_a", "noise_b"), NOISE_SEEDS):
        arms.append(
            _run_arm(
                ctx,
                tag,
                lr=LR_MID,
                lam=None,
                masked=True,
                seed=seed,
                max_steps=SMOKE_STEPS,
                eval_interval=EVAL_INTERVAL,
                extras=("dialog_ppl",),
            )
        )
    a, b = arms
    delta_dialog = abs(a["end_dialog_ppl"] - b["end_dialog_ppl"])
    delta_ret = abs(a["end_retention_ppl"] - b["end_retention_ppl"])
    print(f"[stage0b] Δ_dialog={delta_dialog:.6f} Δ_ret={delta_ret:.6f} (margins = K×Δ with K={K})")
    # §4 pre-registered fallback: margin >= total Stage-0 signal makes the instability gate
    # undefinable. Signal excludes the pre-seeded step-0 row (locked above — conservative).
    trained = [(s, p) for s, p in cal["curve"] if s > 0]
    signal = trained[0][1] - trained[-1][1]
    if K * delta_dialog >= signal:
        raise SystemExit(
            f"[stage0b] VIOLATED GATE (D-02 fallback): margin K×Δ_dialog = "
            f"{K * delta_dialog:.6f} >= total Stage-0 signal {signal:.6f} "
            f"(dialog_ppl {trained[0][1]:.4f}@{trained[0][0]} → "
            f"{trained[-1][1]:.4f}@{trained[-1][0]}) — the instability gate is undefinable "
            "at this floor. Pre-registered fallback: blocking user checkpoint on the raw "
            "curves (surface immediately, D-07 exception)."
        )
    return {"a": a, "b": b, "delta_dialog": delta_dialog, "delta_ret": delta_ret}


def stage1_masking(ctx, noise):
    """§5 masking verdict + §6 cold-start diagnostic + §3 budget-validity check."""
    results = {}
    for tag, masked in (("masked", True), ("unmasked", False)):
        results[tag] = _run_arm(
            ctx,
            tag,
            lr=LR_MID,
            lam=None,
            masked=masked,
            seed=SEED,
            max_steps=SMOKE_STEPS,
            eval_interval=COLDSTART_EVAL_INTERVAL,
            extras=("role_norms",),
        )
    triggers = {}
    for tag, res in results.items():
        trig, detail = cold_start_trigger(res["rows"], SMOKE_STEPS)
        triggers[tag] = detail
        if trig:
            raise SystemExit(
                f"[stage1] VIOLATED GATE (D-04 cold-start trigger) on arm '{tag}': "
                f"nan_inf={detail['nan_inf']!r}, val_loss first={detail['val_loss_first']!r} "
                f"→ 10%-of-budget={detail['val_loss_at_10pct']!r} (no net recovery = "
                f"{detail['no_recovery']}). Mitigation (row reinit to live-row mean / "
                "targeted warmup) is chosen at escalation time and must be judged against "
                "these un-mitigated numbers (surface immediately, D-07 exception)."
            )
    margin = K * noise["delta_dialog"]
    sep = results["masked"]["end_dialog_ppl"] - results["unmasked"]["end_dialog_ppl"]
    if abs(sep) <= margin:
        raise SystemExit(
            f"[stage1] VIOLATED GATE (budget validity, user lock 2): masked-vs-unmasked "
            f"separation |Δ| = {abs(sep):.6f} <= K×Δ_dialog = {margin:.6f} "
            f"(masked {results['masked']['end_dialog_ppl']:.4f} vs unmasked "
            f"{results['unmasked']['end_dialog_ppl']:.4f}). User direction required: extend "
            "the budget, or accept the D-01 tie→masked verdict (surface immediately, D-07)."
        )
    # §5: unmasked wins ONLY if it beats masked by MORE than the margin; otherwise masked.
    winner = "unmasked" if sep > margin else "masked"
    print(
        f"[stage1] masked={results['masked']['end_dialog_ppl']:.4f} "
        f"unmasked={results['unmasked']['end_dialog_ppl']:.4f} margin={margin:.6f} "
        f"→ verdict: {winner}"
    )
    return {"results": results, "triggers": triggers, "sep": sep, "winner": winner}


def stage2_lr(ctx, stage1, noise):
    """§7: ≤3 LR arms on the mask winner; retention + instability gates; LR* pick."""
    winner_masked = stage1["winner"] == "masked"
    margin_dialog = K * noise["delta_dialog"]
    margin_ret = K * noise["delta_ret"]
    anchor = ctx["anchors"]["retention_ppl_subbin_step0"]
    arms = {}
    for lr in LR_GRID:
        name = f"lr_{_lr_name(lr)}"
        if lr == LR_MID and winner_masked and REUSE_NOISE_A_AS_LR_MID:
            # Pre-registered reuse (constants block): config-identical to noise_a.
            src = RESULTS_DIR / "ft_noise_a.csv"
            dst = RESULTS_DIR / f"ft_{name}.csv"
            if not dst.exists():
                shutil.copyfile(src, dst)
            arms[lr] = dict(noise["a"], name=name, reused_from="noise_a")
            print(f"[stage2] arm '{name}': REUSED noise_a (config-identical, pre-registered)")
            continue
        arms[lr] = _run_arm(
            ctx,
            name,
            lr=lr,
            lam=None,
            masked=winner_masked,
            seed=SEED,
            max_steps=SMOKE_STEPS,
            eval_interval=EVAL_INTERVAL,
            extras=("dialog_ppl",),
        )
    gates = {}
    for lr, res in arms.items():
        stab = instability_check(res["rows"], margin_dialog)
        drift = res["end_retention_ppl"] - anchor
        collapsed = retention_collapse(res["end_retention_ppl"], anchor, margin_ret)
        gates[lr] = {
            "instability": stab,
            "retention_drift": drift,
            "retention_collapsed": collapsed,
            "passes": not stab["violated"] and not collapsed,
        }
        print(
            f"[stage2] lr={lr:g}: dialog_ppl={res['end_dialog_ppl']:.4f} "
            f"retention_drift={drift:+.6f} (margin {margin_ret:.6f}) "
            f"unstable={stab['violated']} → passes={gates[lr]['passes']}"
        )
    passing = [lr for lr in LR_GRID if gates[lr]["passes"]]
    if not passing:
        detail = "; ".join(
            f"lr={lr:g}: unstable={gates[lr]['instability']['violated']}, "
            f"retention_drift={gates[lr]['retention_drift']:+.6f} vs margin {margin_ret:.6f}"
            for lr in LR_GRID
        )
        raise SystemExit(
            f"[stage2] VIOLATED GATE (D-02): zero LR arms pass the retention + instability "
            f"gates ({detail}). Surface immediately (D-07 exception)."
        )
    lr_star = min(passing, key=lambda lr: arms[lr]["end_dialog_ppl"])
    print(f"[stage2] LR* = {lr_star:g} (lowest dialogue PPL among passing arms)")
    return {"arms": arms, "gates": gates, "lr_star": lr_star, "winner_masked": winner_masked}


def stage3_lambda(ctx, stage2, noise):
    """§8: λ sweep on the LR* arm; λ=0 = the LR* run reused; λ* + demonstrability guard."""
    lr_star = stage2["lr_star"]
    lam0 = stage2["arms"][lr_star]  # λ=0 reference — identical config by D-03 construction
    margin = K * noise["delta_dialog"]
    grid = sorted(LAMBDA_GRID)
    arms = {}
    extensions = 0
    while True:
        for lam in grid:
            if lam in arms:
                continue
            arms[lam] = _run_arm(
                ctx,
                f"lam_{lam:g}",
                lr=lr_star,
                lam=lam,
                masked=stage2["winner_masked"],
                seed=SEED,
                max_steps=SMOKE_STEPS,
                eval_interval=EVAL_INTERVAL,
                extras=("dialog_ppl", "retention_ppl", "ewc_penalty"),
            )
        ppls = {lam: arms[lam]["end_dialog_ppl"] for lam in grid}
        lam_star_margin, candidates, endpoint = pick_lambda_star(
            ppls, lam0["end_dialog_ppl"], margin, grid
        )
        if lam_star_margin is None or endpoint == 0:
            break
        if extensions >= LAMBDA_EXTENSION_LIMIT:
            raise SystemExit(
                f"[stage3] λ* still on a grid endpoint ({lam_star_margin:g}) after "
                f"{extensions} boundary extensions (grid {grid}) — extension limit reached. "
                "Surface immediately (D-07 exception)."
            )
        new_lam = lam_star_margin * (10.0 if endpoint > 0 else 0.1)
        print(
            f"[stage3] λ*={lam_star_margin:g} sits on a grid endpoint — extending one decade "
            f"to λ={new_lam:g} (boundary-extension rule) and re-applying"
        )
        grid = sorted(grid + [new_lam])
        extensions += 1

    # §8 demonstrability guard: retention(λ*) beats retention(λ=0) by MORE than Δ_ret (raw
    # floor — locked in the pre-registration comments above).
    def guard(lam):
        return (lam0["end_retention_ppl"] - arms[lam]["end_retention_ppl"]) > noise["delta_ret"]

    demonstrable = False
    lam_star = None
    guard_note = ""
    if lam_star_margin is not None and guard(lam_star_margin):
        lam_star, demonstrable = lam_star_margin, True
    else:
        both = [lam for lam in candidates if guard(lam)]
        if both:
            lam_star, demonstrable = max(both), True
            guard_note = (
                f"margin-largest λ={lam_star_margin:g} failed the retention guard; "
                f"λ*={lam_star:g} is the largest λ satisfying BOTH rules"
            )
        else:
            guard_note = "EWC not demonstrable at this budget"
    print(
        f"[stage3] λ*_margin={lam_star_margin} candidates={candidates} "
        f"λ*={lam_star} demonstrable={demonstrable} {guard_note}"
    )
    return {
        "arms": arms,
        "grid": grid,
        "lam0": lam0,
        "lam_star_margin": lam_star_margin,
        "candidates": candidates,
        "lam_star": lam_star,
        "demonstrable": demonstrable,
        "guard_note": guard_note,
        "extensions": extensions,
    }


# ===== Report =====


def _never_clobber_guard():
    """A recorded (non-PENDING) verdict is committed evidence — never overwrite it silently
    (measure_inflation register, T-12-09)."""
    if REPORT_PATH.exists():
        recorded = REPORT_PATH.read_text(encoding="utf-8").split("## Verdict")[-1]
        if "PENDING" not in recorded:
            raise SystemExit(
                f"[finetune_smoke] {REPORT_PATH} already carries a recorded verdict — it is "
                "committed evidence (D-06/T-12-09). Refusing to overwrite."
            )


def _fmt_curve(rows, key, limit=None):
    pts = read_col(rows, key)
    if limit is not None and len(pts) > limit:
        keep = {0, len(pts) - 1}
        stride = max(1, len(pts) // limit)
        pts = [p for i, p in enumerate(pts) if i % stride == 0 or i in keep]
    return " ".join(f"{s}:{v:.4f}" for s, v in pts)


def _norm_traj(rows, max_steps):
    """First / 10%-of-budget / final role-norm values for the Stage-1 diagnostic table."""
    out = {}
    limit = COLDSTART_WINDOW_FRAC * max_steps
    for role in ROLE_IDS:
        col = read_col(rows, f"role_norm_{role}")
        trained = [(s, v) for s, v in col if s > 0]
        at10 = [v for s, v in trained if s <= limit]
        out[role] = {
            "step0": col[0][1] if col else None,
            "first": trained[0][1] if trained else None,
            "at_10pct": at10[-1] if at10 else None,
            "final": trained[-1][1] if trained else None,
        }
    return out


def write_report(ctx, cal, noise, stage1, stage2, stage3):
    _never_clobber_guard()
    anchors = ctx["anchors"]
    dd, dr = noise["delta_dialog"], noise["delta_ret"]
    margin_d, margin_r = K * dd, K * dr
    anchor_sub = anchors["retention_ppl_subbin_step0"]

    cal_wall = _get_wall("cal")
    sec_per_step = cal_wall["wall_s"] / cal_wall["steps"] if cal_wall else None
    sec_str = f"{sec_per_step:.3f}" if sec_per_step else "n/a"
    prod_wall = f"~{PROD_MAX_STEPS_PROPOSAL * sec_per_step / 60:.0f} min" if sec_per_step else "n/a"

    # Per-gate counterfactual k (§2): the k each gate WOULD have required given observed deltas.
    k_masking = counterfactual_k(stage1["sep"], dd)
    lr_star = stage2["lr_star"]
    k_lr_rows = "\n".join(
        f"| LR {lr:g} retention gate | drift {stage2['gates'][lr]['retention_drift']:+.6f} "
        f"vs floor Δ_ret {dr:.6f} "
        f"| k = {counterfactual_k(stage2['gates'][lr]['retention_drift'], dr):.2f} |"
        for lr in LR_GRID
    )
    lam0 = stage3["lam0"]

    def _lam_delta(lam):
        return stage3["arms"][lam]["end_dialog_ppl"] - lam0["end_dialog_ppl"]

    k_lam_rows = "\n".join(
        f"| λ={lam:g} within-margin gate | Δdialog {_lam_delta(lam):+.6f} "
        f"vs floor Δ_dialog {dd:.6f} | k = {counterfactual_k(_lam_delta(lam), dd):.2f} |"
        for lam in stage3["grid"]
    )

    s1 = stage1["results"]
    traj = {tag: _norm_traj(s1[tag]["rows"], SMOKE_STEPS) for tag in ("masked", "unmasked")}
    traj_rows = "\n".join(
        f"| {tag} | {role} | {t['step0']:.4f} | {t['first']:.4f} | {t['at_10pct']:.4f} "
        f"| {t['final']:.4f} |"
        for tag in ("masked", "unmasked")
        for role, t in traj[tag].items()
    )
    trig_rows = "\n".join(
        f"| {tag} | {d['val_loss_first']:.4f} | {d['val_loss_at_10pct']:.4f} "
        f"| {len(d['nan_inf'])} | not triggered |"
        for tag, d in stage1["triggers"].items()
    )

    lr_rows = "\n".join(
        f"| {lr:g} | {stage2['arms'][lr]['end_dialog_ppl']:.4f} "
        f"| {stage2['arms'][lr]['end_retention_ppl']:.4f} "
        f"({stage2['gates'][lr]['retention_drift']:+.6f}) "
        f"| {stage2['gates'][lr]['instability']['violated']} "
        f"| {stage2['gates'][lr]['retention_collapsed']} | {stage2['gates'][lr]['passes']} "
        f"| {stage2['arms'][lr].get('reused_from', 'fresh run')} |"
        for lr in LR_GRID
    )

    def _lam_pen(lam):
        col = read_col(stage3["arms"][lam]["rows"], "ewc_penalty")
        return col[-1][1] if col else float("nan")

    lam_rows = "\n".join(
        f"| {lam:g} | {stage3['arms'][lam]['end_dialog_ppl']:.4f} "
        f"({stage3['arms'][lam]['end_dialog_ppl'] - lam0['end_dialog_ppl']:+.6f}) "
        f"| {stage3['arms'][lam]['end_retention_ppl']:.4f} "
        f"({lam0['end_retention_ppl'] - stage3['arms'][lam]['end_retention_ppl']:+.6f} vs λ=0) "
        f"| {_lam_pen(lam):.4f} | {lam in stage3['candidates']} "
        f"| {(lam0['end_retention_ppl'] - stage3['arms'][lam]['end_retention_ppl']) > dr} |"
        for lam in stage3["grid"]
    )
    lam_star = stage3["lam_star"]
    lam_star_str = f"{lam_star:g}" if lam_star is not None else "NONE"
    finding = (
        f"λ* = {lam_star_str} — demonstrable (retention beats λ=0 by more than Δ_ret)"
        if stage3["demonstrable"]
        else "**EWC not demonstrable at this budget** (no λ satisfies both the within-margin "
        "rule and the retention demonstrability guard) — surfaced, never massaged"
    )
    guard_note = f" Note: {stage3['guard_note']}." if stage3["guard_note"] else ""

    mask_arm = "masked" if stage2["winner_masked"] else "unmasked"
    prod_lam = f"{lam_star:g}" if lam_star is not None else "0 (EWC not demonstrable)"

    # Markdown table rows must be single OUTPUT lines; compose the long ones here so every
    # SOURCE line stays <= 100 (the measure_inflation register).
    lr_grid_str = ", ".join(f"{lr:g}" for lr in LR_GRID)
    lam_grid_str = ", ".join(f"{x:g}" for x in LAMBDA_GRID)
    pre_rows = "\n".join(
        [
            f"| K | {K} | chosen BLIND before any smoke number — deliberately conservative; "
            "no principled derivation exists at this budget; counterfactual k per gate below |",
            f"| CAL_MAX_STEPS | {CAL_MAX_STEPS} | Stage-0 calibration budget |",
            f"| SMOKE_STEPS | {SMOKE_STEPS} | locked from the slope rule (two-pass flow) |",
            f"| LR grid | {lr_grid_str} | pretrain peak 3e-4 × (1, 0.3, 0.1) |",
            f"| λ grid | {lam_grid_str} "
            "| decade grid centered on 1 (mean-normalized Fisher ⇒ λ ≈ O(1) stiffness) |",
            f"| Noise seeds | {NOISE_SEEDS[0]} / {NOISE_SEEDS[1]} | Stage-0b seed pair |",
            f"| Slope rule | trailing-{SLOPE_WINDOW} improvement < {SLOPE_FRAC:g} × "
            f"first-{SLOPE_WINDOW} improvement | D-03 — TinyStories absolute band DROPPED |",
            f"| Cold-start cadence | every {COLDSTART_EVAL_INTERVAL} steps; window = first "
            f"{COLDSTART_WINDOW_FRAC:.0%} of budget | D-04 diagnostic rides Stage 1 |",
            f"| Batch / accum / block | {BATCH_SIZE} / {GRAD_ACCUM} / {BLOCK_SIZE} "
            "| grad_accum=1 sidesteps the λ/accum scaling class |",
        ]
    )
    anchor_rows = "\n".join(
        [
            f"| retention_ppl_subbin_step0 | {anchor_sub} "
            f"| {anchors['retention_tokens_subbin']:,} |",
            f"| retention_ppl_fullval_step0 | {anchors['retention_ppl_fullval_step0']} "
            f"| {anchors['retention_tokens_fullval']:,} |",
            "| dialogue val PPL at step 0 (anchor model, frozen gate policy) "
            f"| {ctx['dialog_ppl0']:.4f} | {ctx['dialog_tokens0']:,} |",
            f"| anchor fingerprint | step {ctx['blob']['step']}, "
            f"val_loss {ctx['blob']['val_loss']} | git {ctx['blob']['git_sha'][:9]} |",
        ]
    )
    cal_min = f"{cal_wall['wall_s'] / 60:.1f}" if cal_wall else "n/a"
    cal_line = (
        f"- Calibration run: masked arm, LR {LR_MID:g}, seed {SEED}, "
        f"eval_interval {EVAL_INTERVAL}, {CAL_MAX_STEPS} steps."
    )
    rec_line = (
        f"- Slope rule recommendation: **{cal['recommended']} steps** "
        f"(capped at CAL_MAX_STEPS: {cal['capped']})"
    )
    lock_line = (
        f"- Locked SMOKE_STEPS: **{SMOKE_STEPS}** (lock enforced by SystemExit when "
        f"|recommended − locked| > {EVAL_INTERVAL})"
    )
    wall_line = (
        f"- Measured wall-clock: {sec_str} s/step including per-interval evals "
        f"({cal_min} min total)"
    )
    noise_rows = "\n".join(
        [
            f"| end dialogue PPL | {noise['a']['end_dialog_ppl']:.6f} "
            f"| {noise['b']['end_dialog_ppl']:.6f} | {dd:.6f} | {margin_d:.6f} |",
            f"| end retention PPL | {noise['a']['end_retention_ppl']:.6f} "
            f"| {noise['b']['end_retention_ppl']:.6f} | {dr:.6f} | {margin_r:.6f} |",
        ]
    )
    k_mask_row = (
        f"| Masking verdict (Stage 1) | separation {stage1['sep']:+.6f} "
        f"vs Δ_dialog {dd:.6f} | k = {k_masking:.2f} |"
    )
    undef_line = (
        f"Undefinable-gate fallback check (§4): margin {margin_d:.6f} < total Stage-0 "
        "signal — gate definable, no fallback."
    )
    s1_intro = (
        f"Both arms: LR {LR_MID:g}, seed {SEED}, {SMOKE_STEPS} steps, eval_interval "
        f"{COLDSTART_EVAL_INTERVAL}; scored with the frozen policy (§1):"
    )
    s1_rows = "\n".join(
        [
            f"| masked training loss | {s1['masked']['end_dialog_ppl']:.4f} "
            f"| {s1['masked']['end_retention_ppl']:.4f} |",
            f"| unmasked training loss | {s1['unmasked']['end_dialog_ppl']:.4f} "
            f"| {s1['unmasked']['end_retention_ppl']:.4f} |",
        ]
    )
    verdict_line = (
        f"- **Verdict: {stage1['winner']}** (unmasked wins only by beating masked by MORE "
        "than the margin; ties → masked)."
    )
    lr_head = (
        "| LR | End dialogue PPL | End retention PPL (drift) | Unstable "
        "| Retention collapse | Passes | Provenance |"
    )
    lam_head = (
        "| λ | End dialogue PPL (vs λ=0) | End retention PPL (gain vs λ=0) "
        "| Final EWC penalty | Within margin | Beats retention floor |"
    )
    cand_line = (
        f"- Within-margin candidates: {stage3['candidates']}; margin-largest λ = "
        f"{stage3['lam_star_margin']}; boundary extensions: {stage3['extensions']}."
    )

    report = f"""# Fine-Tune Calibration Smoke Report (Phase 12 Plan 04 — D-01..D-07)

> **What these numbers are:** the pre-registered smoke decisions for the Stage-2 conversational
> fine-tune — budget, noise floor, masking verdict, LR*, λ* — each produced by a rule committed
> in `scripts/finetune_smoke.py` BEFORE any smoke number existed (git history is the
> pre-registration proof). **Frozen gate policy (§1):** dialogue val PPL = `masked_perplexity`
> on `data/dialog_val.bin` + `data/dialog_val_mask.bin`, block {BLOCK_SIZE}, dead ids forbidden
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
{pre_rows}

## Step-0 Anchors (embedded from results/retention_anchors.json — Pitfall 1)

| Key | Value | Tokens |
| --- | --- | --- |
{anchor_rows}

## Stage 0 — Budget Recalibration (D-03)

{cal_line}
- dialog_ppl curve (step:ppl): {_fmt_curve(cal["res"]["rows"], "dialog_ppl")}
{rec_line}
{lock_line}
{wall_line}

## Stage 0b — Noise Floor (D-05)

Seed pair ({NOISE_SEEDS[0]} vs {NOISE_SEEDS[1]}), identical config (masked, LR {LR_MID:g},
{SMOKE_STEPS} steps):

| Quantity | Seed {NOISE_SEEDS[0]} | Seed {NOISE_SEEDS[1]} | Δ (floor) | Margin (K×Δ) |
| --- | --- | --- | --- | --- |
{noise_rows}

K = {K} was declared blind. **Counterfactual k per gate** (the k the observed decision delta
would have required at this floor):

| Gate | Observed decision delta vs floor | Counterfactual k |
| --- | --- | --- |
{k_mask_row}
{k_lr_rows}
{k_lam_rows}

{undef_line}

## Stage 1 — Masking Verdict (D-01) + Cold-Start Diagnostic (D-04)

{s1_intro}

| Arm | End dialogue PPL | End retention PPL |
| --- | --- | --- |
{s1_rows}

- Separation (masked − unmasked): {stage1["sep"]:+.6f}; margin K×Δ_dialog = {margin_d:.6f}.
- Budget-validity check (user lock 2): |Δ| > margin — PASSED (no tie halt).
{verdict_line}

Cold-start trigger evaluation (window = first {COLDSTART_WINDOW_FRAC:.0%} of budget, mechanical):

| Arm | val_loss first interval | val_loss at 10% budget | NaN/Inf cells | Trigger |
| --- | --- | --- | --- | --- |
{trig_rows}

Role-token embedding norms (wte rows {ROLE_IDS["user"]}-{ROLE_IDS["system"]}):

| Arm | Role | Step 0 | First interval | At 10% budget | Final |
| --- | --- | --- | --- | --- | --- |
{traj_rows}

## Stage 2 — LR Sweep (D-02)

Arms on the {mask_arm} winner, seed {SEED}, {SMOKE_STEPS} steps. Gates: retention collapse
(after-run sub-bin retention − step-0 anchor {anchor_sub:.4f} > K×Δ_ret = {margin_r:.6f}) and
instability (NaN/Inf, or interval-to-interval dialog_ppl increase > K×Δ_dialog = {margin_d:.6f}):

{lr_head}
| --- | --- | --- | --- | --- | --- | --- |
{lr_rows}

**LR\\* = {lr_star:g}** (lowest end-of-run dialogue PPL among passing arms).

## Stage 3 — λ Sweep (EWC-03)

λ arms on the LR\\* = {lr_star:g} {mask_arm} config; λ=0 reference = the LR\\* run itself
(identical config by D-03 construction). λ\\* rule: largest λ within K×Δ_dialog = {margin_d:.6f}
of λ=0's end dialogue PPL ({lam0["end_dialog_ppl"]:.4f}); demonstrability guard: retention(λ\\*)
beats retention(λ=0) ({lam0["end_retention_ppl"]:.4f}) by MORE than Δ_ret = {dr:.6f}:

{lam_head}
| --- | --- | --- | --- | --- | --- |
{lam_rows}

{cand_line}
- **{finding}**{guard_note}

## Proposed Production Config (Plan 12-05 input)

| Knob | Value |
| --- | --- |
| Training loss | {mask_arm} |
| LR | {lr_star:g} |
| λ | {prod_lam} |
| PROD_MAX_STEPS | {PROD_MAX_STEPS_PROPOSAL} (≈ {prod_wall} at the measured {sec_str} s/step) |
| Seed / batch / accum | {SEED} / {BATCH_SIZE} / {GRAD_ACCUM} |

## Verdict

PENDING — user decision at the D-07 blocking checkpoint.
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"[finetune_smoke] wrote {REPORT_PATH}")


# ===== Main =====


def main() -> None:
    t0 = time.monotonic()
    _never_clobber_guard()
    if not ANCHORS_JSON.exists():
        raise SystemExit(
            f"[finetune_smoke] missing {ANCHORS_JSON} — the step-0 anchors must exist before "
            "any smoke run (Pitfall 1). Run `python scripts/build_retention_bin.py` first."
        )
    for path in (DIALOG_TRAIN, DIALOG_TRAIN_MASK, DIALOG_VAL, DIALOG_VAL_MASK, RETENTION_BIN):
        if not path.exists():
            raise FileNotFoundError(f"Missing local bin: {path}. Build the dialogue bins first.")
    if not BEST_PATH.exists():
        raise FileNotFoundError(f"Missing {BEST_PATH} (the fine-tune anchor).")

    summary = preflight_device(strict=True)
    print(f"[finetune_smoke] preflight: {summary}")
    runtime = RuntimeConfig()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    CKPT_DIR.mkdir(parents=True, exist_ok=True)

    # weights_only=False: TRUSTED-only read of the project's OWN anchor checkpoint (T-12-10).
    blob = torch.load(BEST_PATH, weights_only=False)
    anchor_model = GPT(ModelConfig(**blob["model_config"]))
    anchor_model.load_state_dict(blob["model"])
    # theta_star: detached CPU clones from named_parameters — the tied wte/lm_head storage
    # appears exactly once (estimate_fisher_tinystories register).
    theta_star = {n: p.detach().clone().cpu() for n, p in anchor_model.named_parameters()}
    # Fisher loaded ONCE at driver start; all λ arms share it. Fingerprint trio read from the
    # anchor blob pins the cache to these exact weights.
    fisher = load_fisher(
        FISHER_CACHE,
        expected_fingerprint={
            "git_sha": blob["git_sha"],
            "step": blob["step"],
            "val_loss": blob["val_loss"],
        },
    )["fisher"]
    tok = from_json(TOKENIZER_PATH)  # FROZEN artifact — never retrain
    vocab_size = ModelConfig(**blob["model_config"]).vocab_size
    forbid = undecodable_ids_mask(tok, vocab_size)
    anchors = json.loads(ANCHORS_JSON.read_text(encoding="utf-8"))

    ctx = {
        "runtime": runtime,
        "blob": blob,
        "theta_star": theta_star,
        "fisher": fisher,
        "tok": tok,
        "forbid": forbid,
        "anchors": anchors,
    }
    # Step-0 measurements on the anchor (outside train() — the loop logs no step-0 row).
    anchor_model.to(runtime.device)
    dialog_ppl0, dialog_tokens0 = masked_perplexity(
        anchor_model, DIALOG_VAL, DIALOG_VAL_MASK, BLOCK_SIZE, runtime.device, forbid_ids=forbid
    )
    ctx["dialog_ppl0"] = dialog_ppl0
    ctx["dialog_tokens0"] = dialog_tokens0
    ctx["role_norms0"] = {
        role: float(anchor_model.wte.weight[rid].norm().item()) for role, rid in ROLE_IDS.items()
    }
    print(
        f"[finetune_smoke] step-0: dialog_ppl={dialog_ppl0:.4f} over {dialog_tokens0:,} tokens; "
        f"retention anchor {anchors['retention_ppl_subbin_step0']:.4f} (from anchors JSON)"
    )
    del anchor_model  # per-arm models are built fresh; the anchor state lives in blob/theta_star

    cal = stage0_calibrate(ctx)  # SystemExits on lock mismatch (two-pass flow)
    noise = stage0b_noise(ctx, cal)
    s1 = stage1_masking(ctx, noise)
    s2 = stage2_lr(ctx, s1, noise)
    s3 = stage3_lambda(ctx, s2, noise)
    write_report(ctx, cal, noise, s1, s2, s3)
    print(f"[finetune_smoke] full sequence complete in {(time.monotonic() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
