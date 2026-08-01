"""Phase-13 A/B no-forgetting driver (DEMO-04: naive λ=0 vs EWC λ=0.01, one arm per process).

Runs ONE arm of the pre-registered A/B experiment, fresh from ``checkpoints/best.pt`` with the
recorded twin config (D-01/D-03: unmasked, LR 9e-5, seed 1337, 4000 steps, batch 32, accum 1).
The two arms differ in EXACTLY one bit — ``penalty_fn`` (None vs ``EWCPenalty(..., 0.01)``);
everything else, including the ``TrainConfig``, the eval-fn dict, and the seeding order, is
identical by construction.

  naive → results/phase13_naive/run.csv + checkpoints/phase13_naive_latest.pt
  ewc   → results/phase13_ewc/run.csv   + checkpoints/phase13_ewc_latest.pt

Pre-registration (D-10): the constants block and the ``ewc_mitigates`` gate below are COMMITTED
BEFORE either arm runs — git history order is the pre-registration proof (the finetune_smoke.py
register). The driver never parses a report for numbers.

Artifact isolation (D-07 / WR-02): every write target is arm-name-scoped and the run REFUSES to
start if either output already exists. Phase-12's recorded evidence (``results/finetune_prod.csv``,
the convbase trio) is NEVER a write target here — ``finetune_prod.csv`` is read-only D-11 input.

SECURITY: torch.load(weights_only=False) reads ONLY the project's OWN anchor checkpoint
(``checkpoints/best.pt`` — T-12-10 trusted-only); the Fisher cache goes through ``load_fisher``
(weights_only=True) pinned to the anchor fingerprint trio.

Run: ``python scripts/finetune_ab.py {naive|ewc}`` (inside the Python 3.11 venv, on the M3).
"""

import csv
import json
import math
import os
import pathlib
import sys
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
from personacore.provenance import git_sha  # noqa: E402
from personacore.seeding import seed_everything  # noqa: E402
from personacore.tokenizer import from_json  # noqa: E402
from personacore.training import train  # noqa: E402
from personacore.training.loop import CSV_FIELDNAMES  # noqa: E402

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DIALOG_TRAIN = _REPO_ROOT / "data" / "dialog_train.bin"
DIALOG_VAL = _REPO_ROOT / "data" / "dialog_val.bin"
DIALOG_VAL_MASK = _REPO_ROOT / "data" / "dialog_val_mask.bin"  # acquisition metric (always)
RETENTION_BIN = _REPO_ROOT / "data" / "retention_val.bin"  # frozen sub-bin (Plan 12-03)
BEST_PATH = _REPO_ROOT / "checkpoints" / "best.pt"  # own trusted anchor checkpoint
FISHER_CACHE = _REPO_ROOT / "checkpoints" / "fisher_tinystories.pt"
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"  # FROZEN — never retrain
ANCHORS_JSON = _REPO_ROOT / "results" / "retention_anchors.json"  # committed step-0 anchors
PROD_CSV = _REPO_ROOT / "results" / "finetune_prod.csv"  # READ-ONLY D-11 cross-check input

ARMS = ("naive", "ewc")

# ===== PRE-REGISTRATION (D-01..D-11, locked before any Phase-13 number) =====
#
# Transcribed from committed Phase-12 evidence. Hardcoded on purpose — the driver never parses
# the report for numbers. This block is committed BEFORE either arm runs; git history order is
# the pre-registration proof (finetune_smoke.py:77+ register, T-12-08).

# D-05/§2 — K reused BLIND from Phase 12: the same deliberately conservative default, NOT
# re-chosen after seeing any Phase-13 number.
K = 2

# D-05 obligation 1 — the retention noise floor WITH its measurement regime named:
# results/finetune_smoke_report.md Stage 0b, seed pair (1337, 2024), masked arm, LR 9e-5,
# 1250 steps, identical config. NOT re-verified at the 4000-step production budget — the
# report's threats-to-validity register carries that limitation explicitly.
DELTA_RET = 0.068930

# D-06 gate margin. (The smoke report displays 0.137861 from the unrounded floor; this phase
# computes from the transcribed 0.068930 → 0.137860. The 4-decimal difference is far below any
# observed effect and is noted in the report's pre-registration table.)
MARGIN = K * DELTA_RET

# D-02 — the headline λ: the ONLY sweep grid point moving BOTH axes favorably vs λ=0
# (retention drift +3.85 → +1.67, ~57%, at +0.28 dialogue PPL). λ=100 shows half the
# phenomenon and is deliberately not the headline.
LAMBDA_EWC = 0.01

# D-03 — the recorded twin config (results/finetune_prod_run.log provenance block): the λ=0
# twin must match the production run in every bit but λ.
LR = 9e-5
MAX_STEPS = 4000
SEED = 1337  # seed_everything immediately before the GPT build — owns the data order
BATCH_SIZE = 32
GRAD_ACCUM = 1  # sidesteps the λ/accum scaling class (Pitfall 2)
EVAL_INTERVAL = 250  # forgetting-curve cadence
BLOCK_SIZE = 256  # ModelConfig.block_size — every PPL sweep window
MASK_ARM = "unmasked"  # D-03 / Stage-1 verdict: train_mask_bin=None

# D-11 reproduction cross-check targets: results/finetune_prod.csv final row (step 4000).
# Read from the committed CSV at run time too — these literals are the tripwire, not the source.
PROD_DIALOG_4000 = 4.573349214207799
PROD_RETENTION_4000 = 3.891139975617828


# ===== Gate formulas (pure functions over logged numbers) =====


def ewc_mitigates(naive_ret, ewc_ret):
    """D-06 claim gate, retention-only: EWC mitigates forgetting iff the EWC arm beats the
    naive arm's retention PPL by MORE than MARGIN = K x DELTA_RET. Boundary is a FAIL
    (delta == MARGIN returns False). Acquisition is reported descriptively with NO gate."""
    return (naive_ret - ewc_ret) > MARGIN


def penalty_for_arm(arm, penalty):
    """THE one-bit difference between the arms: the EWC arm passes the penalty to train(),
    the naive arm passes None. Everything else is identical by construction."""
    return penalty if arm == "ewc" else None


def arm_outputs(arm):
    """D-07 name-scoped write targets for one arm: (run CSV, end-of-run checkpoint).
    Never a Phase-12 path — finetune_prod.csv and the convbase trio are recorded evidence."""
    return (
        _REPO_ROOT / "results" / f"phase13_{arm}" / "run.csv",
        _REPO_ROOT / "checkpoints" / f"phase13_{arm}_latest.pt",
    )


def refuse_if_exists(paths):
    """D-07 / WR-02 refuse-to-rerun: an arm's outputs are RECORDED evidence once written — a
    rerun on drifted code/data would silently replace them. Fail loud naming the offender."""
    for out in paths:
        if out.exists():
            raise SystemExit(
                f"[finetune_ab] {out} already exists — this arm is recorded evidence. "
                f"Delete {' and '.join(str(p) for p in paths)} to re-run."
            )


def build_train_config():
    """The IDENTICAL TrainConfig both arms train under (D-03 recorded twin config).
    Defaults supply warmup_steps=100 / grad_clip=1.0 / weight_decay=0.1 as in production."""
    return TrainConfig(
        lr=LR,
        batch_size=BATCH_SIZE,
        grad_accum_steps=GRAD_ACCUM,
        max_steps=MAX_STEPS,
        seed=SEED,
    )


def _preseed_csv(csv_path, fieldnames, step0_values):
    """TUNE-02 step-0 row: the v1.0 eval block logs NO step-0 row (12-01 pinned fact), so
    pre-create the CSV with the header + a measured step-0 row before train() appends."""
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, restval="")
        writer.writeheader()
        row = {"step": 0, "tokens": 0, "wall_clock": 0}
        row.update(step0_values)
        writer.writerow(row)


def _prove(condition, message):
    """Loud end-of-run proof: SystemExit naming the violated contract (never bare assert)."""
    if not condition:
        raise SystemExit(f"[finetune_ab] PROOF FAILED: {message}")


def main(arm) -> None:
    if arm not in ARMS:
        raise SystemExit(f"[finetune_ab] unknown arm {arm!r} — expected one of {ARMS}.")
    t0 = time.monotonic()

    arm_csv, arm_ckpt = arm_outputs(arm)
    refuse_if_exists((arm_csv, arm_ckpt))

    for path in (DIALOG_TRAIN, DIALOG_VAL, DIALOG_VAL_MASK):
        if not path.exists():
            raise FileNotFoundError(
                f"Missing dialogue bin: {path}. Run `python scripts/prepare_dialog_corpus.py`."
            )
    if not RETENTION_BIN.exists():
        raise FileNotFoundError(
            f"Missing {RETENTION_BIN}. Run `python scripts/build_retention_bin.py` first."
        )
    if not BEST_PATH.exists():
        raise FileNotFoundError(f"Missing {BEST_PATH} (the shared fine-tune anchor).")
    if not FISHER_CACHE.exists():
        raise FileNotFoundError(
            f"Missing {FISHER_CACHE}. Run `python scripts/estimate_fisher_tinystories.py`."
        )
    if not ANCHORS_JSON.exists():
        raise SystemExit(
            f"[finetune_ab] missing {ANCHORS_JSON} — step-0 anchors must exist. "
            "Run `python scripts/build_retention_bin.py` first."
        )

    summary = preflight_device(strict=True)
    print(f"[finetune_ab] arm={arm} preflight: {summary}")
    runtime = RuntimeConfig()

    # weights_only=False: TRUSTED-only read of the project's OWN anchor checkpoint (T-12-10).
    blob = torch.load(BEST_PATH, weights_only=False)
    # seed_everything IMMEDIATELY before the GPT build: the batch sampler draws from the GLOBAL
    # numpy rng, so this is what makes the two arms share the data order bit-for-bit (DEMO-04).
    # No RNG draw may occur between here and train() beyond this sequence (Pitfall 2).
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
    # Constructed in BOTH arms: EWCPenalty is RNG-free, and the naive arm logs it as a
    # DIAGNOSTIC-ONLY ewc_penalty column (measured, never applied) so both CSV schemas match.
    penalty = EWCPenalty(fisher, theta_star, LAMBDA_EWC, runtime.device)

    tok = from_json(TOKENIZER_PATH)
    forbid = undecodable_ids_mask(tok, model_cfg.vocab_size)
    anchors = json.loads(ANCHORS_JSON.read_text(encoding="utf-8"))

    # Frozen evaluation policy (smoke report §1) — IDENTICAL dict in both arms.
    device = runtime.device
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
    print(
        f"[finetune_ab] step-0: dialog_ppl={dialog_ppl0:.4f} over {dialog_tokens0:,} tokens; "
        f"retention anchor {step0['retention_ppl']:.4f} (from anchors JSON)"
    )
    arm_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = CSV_FIELDNAMES + sorted(fns)
    _preseed_csv(arm_csv, fieldnames, step0)

    cfg = build_train_config()
    arm_penalty = penalty_for_arm(arm, penalty)
    print(
        f"[finetune_ab] {arm} arm: {MASK_ARM}, lr={LR:g}, "
        f"λ={LAMBDA_EWC if arm_penalty is not None else 0}, steps={MAX_STEPS}, seed={SEED}, "
        f"batch={BATCH_SIZE}, accum={GRAD_ACCUM}"
    )
    model.train()  # Pitfall 7: the step-0 eval left the model in eval mode.
    train(
        train_config=cfg,
        runtime_config=runtime,
        model=model,
        model_config=model_cfg,
        train_bin=DIALOG_TRAIN,
        val_bin=DIALOG_VAL,
        train_mask_bin=None,  # D-03 unmasked
        val_mask_bin=DIALOG_VAL_MASK,  # ALWAYS — in-loop val_loss is never a gate (USER LOCK 3)
        penalty_fn=arm_penalty,  # ← THE one bit
        extra_eval_fns=fns,
        # EWC extras ride the checkpoint for the EWC arm only (prod precedent, T-12-14); the
        # naive arm's checkpoint carries no EWC state because none was applied.
        checkpoint_extra=(
            {
                "fisher": fisher,
                "theta_star": theta_star,
                "ewc_lambda": LAMBDA_EWC,
                "fisher_meta": fisher_meta,
            }
            if arm == "ewc"
            else None
        ),
        log_path=str(arm_csv),
        eval_interval=EVAL_INTERVAL,
        checkpoint_path=str(arm_ckpt),
        # D-08: the best-checkpoint kwarg is OMITTED entirely — the end-of-call checkpoint_path
        # save IS the step-4000 state the 2x2 cells report. Best-selection would add a second
        # decision on top of the penalty, diluting "differs only in the penalty" (WR-01 surface).
    )
    wall = time.monotonic() - t0

    # ===== Loud end-of-run proofs (SystemExit on violation) =====
    with open(arm_csv, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    _prove(rows and rows[0]["step"] == "0", f"{arm_csv} has no step-0 row (TUNE-02)")
    _prove(
        int(float(rows[-1]["step"])) == MAX_STEPS,
        f"final CSV row step {rows[-1]['step']} != MAX_STEPS {MAX_STEPS}",
    )
    ret_col = [float(r["retention_ppl"]) for r in rows if r.get("retention_ppl") not in ("", None)]
    _prove(
        ret_col and all(math.isfinite(v) for v in ret_col),
        f"retention_ppl column missing or non-finite somewhere in {arm_csv}",
    )
    dialog_col = [float(r["dialog_ppl"]) for r in rows if r.get("dialog_ppl") not in ("", None)]
    print(
        f"[finetune_ab] proofs passed: step-0 row, final step {MAX_STEPS}, finite retention; "
        f"retention {ret_col[0]:.4f} → {ret_col[-1]:.4f} (drift {ret_col[-1] - ret_col[0]:+.4f}), "
        f"dialogue {dialog_col[0]:.4f} → {dialog_col[-1]:.4f}; wall {wall / 60:.1f} min"
    )

    # ===== Phase-13 provenance echo (identicality proof — both arms print this) =====
    print(f"[finetune_ab] ===== provenance ({arm} arm) =====")
    print(f"  seed: {SEED} (seed_everything immediately before GPT build — owns data order)")
    print(f"  train_config: {cfg}")
    print(f"  mask_arm: {MASK_ARM} (train_mask_bin=None)")
    print(f"  penalty_fn: {'None (λ=0)' if arm_penalty is None else f'EWCPenalty λ={LAMBDA_EWC}'}")
    print(f"  anchor fingerprint: {fingerprint}")
    print(f"  driver git_sha: {git_sha()}")

    # ===== D-11 reproduction cross-check (EWC arm only; READ-ONLY on finetune_prod.csv) =====
    if arm == "ewc":
        with open(PROD_CSV, newline="", encoding="utf-8") as fh:
            prod_final = list(csv.DictReader(fh))[-1]
        prod_dialog = float(prod_final["dialog_ppl"])
        prod_retention = float(prod_final["retention_ppl"])
        print("[finetune_ab] ===== D-11 cross-check vs results/finetune_prod.csv =====")
        print(f"  {'metric':<16}{'this run':>14}{'prod (12-05)':>16}{'delta':>14}")
        print(
            f"  {'dialog_ppl':<16}{dialog_col[-1]:>14.6f}{prod_dialog:>16.6f}"
            f"{dialog_col[-1] - prod_dialog:>+14.6f}"
        )
        print(
            f"  {'retention_ppl':<16}{ret_col[-1]:>14.6f}{prod_retention:>16.6f}"
            f"{ret_col[-1] - prod_retention:>+14.6f}"
        )
        print(f"  pre-registered literals: {PROD_DIALOG_4000} / {PROD_RETENTION_4000}")
        # Raised AFTER every output is saved: divergence is a REAL FINDING that blocks report
        # finalization (MPS non-determinism or unnoticed config drift), never a lost run.
        if abs(ret_col[-1] - prod_retention) > MARGIN:
            raise SystemExit(
                "[finetune_ab] D-11 DIVERGENCE — investigate before report finalization "
                f"(retention {ret_col[-1]:.6f} vs prod {prod_retention:.6f}, "
                f"|Δ| > MARGIN {MARGIN:.6f})"
            )
        print(f"  D-11 MATCH: retention within MARGIN {MARGIN:.6f} of the production run.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
