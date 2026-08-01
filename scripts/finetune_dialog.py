"""Production Stage-2 fine-tune driver (Phase 12 Plan 05: TUNE-01 / TUNE-02 / EWC-03).

Runs the D-07-APPROVED production fine-tune of ``checkpoints/best.pt`` on the PersonaChat
dialogue bins, producing the conversational-base checkpoint trio (Phase 13's EWC arm and
Phase 14's LoRA substrate):

  checkpoints/convbase_latest.pt  full resumable state, EWC extras embedded (self-contained)
  checkpoints/convbase_best.pt    lowest in-loop masked val_loss (best-checkpoint stopping)
  checkpoints/convbase_slim.pt    weights_only=True shippable artifact (LOCKED contract)
  results/finetune_prod.csv       step-0-anchored retention/dialog forgetting curve (TUNE-02)

Gate governance (T-12-13): this driver REFUSES to run unless
``results/finetune_smoke_report.md`` carries a recorded ``## Verdict`` reading GO — the
D-07 checkpoint decision is enforced in code, not convention (the prepare_dialog_corpus
register). The constants below are the approved production config, hardcoded from the
report's "Production Config Decision" section — never parsed at runtime.

Phase-13 provenance (DEMO-04): seed_everything(SEED) runs IMMEDIATELY before the GPT build,
so the global numpy rng owns the data order — an identical-seed λ=0 twin run differs from
this one in exactly one bit (ewc lambda). The provenance block printed at the end records
seed / config / λ* / git SHA for that twin.

SECURITY: torch.load(weights_only=False) reads ONLY the project's OWN checkpoints
(checkpoints/best.pt + convbase_best.pt written by this driver — trusted-only); the Fisher
cache goes through load_fisher (weights_only=True) pinned to the anchor fingerprint trio.

Run: ``python scripts/finetune_dialog.py`` (inside the Python 3.11 venv, on the M3).
"""

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

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DIALOG_TRAIN = _REPO_ROOT / "data" / "dialog_train.bin"
DIALOG_TRAIN_MASK = _REPO_ROOT / "data" / "dialog_train_mask.bin"
DIALOG_VAL = _REPO_ROOT / "data" / "dialog_val.bin"
DIALOG_VAL_MASK = _REPO_ROOT / "data" / "dialog_val_mask.bin"
RETENTION_BIN = _REPO_ROOT / "data" / "retention_val.bin"  # frozen sub-bin (Plan 12-03)
BEST_PATH = _REPO_ROOT / "checkpoints" / "best.pt"  # own trusted anchor checkpoint
FISHER_CACHE = _REPO_ROOT / "checkpoints" / "fisher_tinystories.pt"
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"  # FROZEN — never retrain
ANCHORS_JSON = _REPO_ROOT / "results" / "retention_anchors.json"  # committed step-0 anchors
REPORT_PATH = _REPO_ROOT / "results" / "finetune_smoke_report.md"  # carries the D-07 verdict
PROD_CSV = _REPO_ROOT / "results" / "finetune_prod.csv"  # TUNE-02 forgetting curve (tracked)
CONVBASE_LATEST = _REPO_ROOT / "checkpoints" / "convbase_latest.pt"
CONVBASE_BEST = _REPO_ROOT / "checkpoints" / "convbase_best.pt"
CONVBASE_SLIM = _REPO_ROOT / "checkpoints" / "convbase_slim.pt"

# ===== APPROVED PRODUCTION CONFIG (D-07 GO verdict, recorded 2026-08-01) =====
#
# Every value below is transcribed from results/finetune_smoke_report.md
# "Production Config Decision — post-verdict, discretionary" (commit 5b6a387) via
# 12-04-SUMMARY.md. Hardcoded on purpose — the driver never parses the report for numbers.

MASK_ARM = "unmasked"  # Stage-1 masking verdict: unmasked won (4.4453 vs 4.4706, k=14.8×)
LR_STAR = 9e-5  # Stage-2 LR set by the RECORDED user override (gate §7(a) all-fail, D-07)
LAMBDA_STAR = 0.01  # discretionary post-§8-verdict production λ (drift +3.85 → +1.67, ~57%)
PROD_MAX_STEPS = 4000  # ≈29 min at the measured 0.439 s/step (report Stage 0 wall-clock)
EVAL_INTERVAL = 250  # forgetting-curve cadence — retention/dialog logged every interval
CHECKPOINT_INTERVAL = 250  # kill-survivability: latest.pt every K steps
SEED = 1337  # data-order provenance for the Phase-13 identical-seed λ=0 twin (DEMO-04)
BATCH_SIZE = 32
GRAD_ACCUM = 1  # sidesteps the λ/accum scaling class (Pitfall 2)
BLOCK_SIZE = 256  # ModelConfig.block_size — every PPL sweep window


def _require_go_verdict(report_path):
    """T-12-13 gate: hard-exit unless the smoke report's ``## Verdict`` reads GO."""
    import re

    if not report_path.exists():
        raise SystemExit(
            f"[finetune_dialog] {report_path} missing — run scripts/finetune_smoke.py and "
            "record the D-07 verdict first."
        )
    text = report_path.read_text(encoding="utf-8")
    section = re.search(r"^## Verdict\b(.*?)(?=^## |\Z)", text, flags=re.M | re.S)
    if section is None:
        raise SystemExit(
            "[finetune_dialog] no '## Verdict' section in the smoke report — the D-07 "
            "verdict must be recorded before the production run (T-12-13)."
        )
    word = re.search(r"[A-Za-z]+", section.group(1))
    verdict = word.group(0).upper() if word else "PENDING"
    if verdict != "GO":
        raise SystemExit(
            f"[finetune_dialog] recorded verdict is {verdict!r} — the production fine-tune "
            "may only run on GO (D-07). PENDING/NO-GO must be escalated, not bypassed."
        )
    return verdict


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
        raise SystemExit(f"[finetune_dialog] PROOF FAILED: {message}")


def main() -> None:
    t0 = time.monotonic()
    verdict = _require_go_verdict(REPORT_PATH)
    print(f"[finetune_dialog] D-07 verdict: {verdict} — production fine-tune approved")

    for path in (DIALOG_TRAIN, DIALOG_TRAIN_MASK, DIALOG_VAL, DIALOG_VAL_MASK):
        if not path.exists():
            raise FileNotFoundError(
                f"Missing dialogue bin: {path}. Run `python scripts/prepare_dialog_corpus.py`."
            )
    if not RETENTION_BIN.exists():
        raise FileNotFoundError(
            f"Missing {RETENTION_BIN}. Run `python scripts/build_retention_bin.py` first."
        )
    if not BEST_PATH.exists():
        raise FileNotFoundError(f"Missing {BEST_PATH} (the fine-tune anchor).")
    if not FISHER_CACHE.exists():
        raise FileNotFoundError(
            f"Missing {FISHER_CACHE}. Run `python scripts/estimate_fisher_tinystories.py`."
        )
    if not ANCHORS_JSON.exists():
        raise SystemExit(
            f"[finetune_dialog] missing {ANCHORS_JSON} — step-0 anchors must exist "
            "(Pitfall 1). Run `python scripts/build_retention_bin.py` first."
        )

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

    tok = from_json(TOKENIZER_PATH)
    forbid = undecodable_ids_mask(tok, model_cfg.vocab_size)
    anchors = json.loads(ANCHORS_JSON.read_text(encoding="utf-8"))

    # Frozen evaluation policy (smoke report §1): dialogue = masked_perplexity on the val
    # bins, retention = retention_perplexity on the frozen sub-bin — independent of MASK_ARM.
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
        f"[finetune_dialog] step-0: dialog_ppl={dialog_ppl0:.4f} over {dialog_tokens0:,} "
        f"tokens; retention anchor {step0['retention_ppl']:.4f} (from anchors JSON)"
    )
    fieldnames = CSV_FIELDNAMES + sorted(fns)
    _preseed_csv(PROD_CSV, fieldnames, step0)

    cfg = TrainConfig(
        lr=LR_STAR,
        batch_size=BATCH_SIZE,
        grad_accum_steps=GRAD_ACCUM,
        max_steps=PROD_MAX_STEPS,
        seed=SEED,
    )
    print(
        f"[finetune_dialog] production run: {MASK_ARM}, lr={LR_STAR:g}, λ={LAMBDA_STAR:g}, "
        f"steps={PROD_MAX_STEPS}, seed={SEED}, batch={BATCH_SIZE}, accum={GRAD_ACCUM}"
    )
    model.train()
    train(
        train_config=cfg,
        runtime_config=runtime,
        model=model,
        model_config=model_cfg,
        train_bin=DIALOG_TRAIN,
        val_bin=DIALOG_VAL,
        # MASK_ARM = unmasked: no training mask; DIALOG_TRAIN_MASK stays a prerequisite only.
        train_mask_bin=None,
        val_mask_bin=DIALOG_VAL_MASK,  # ALWAYS — in-loop val_loss gates best.pt (USER LOCK 3)
        penalty_fn=penalty,
        extra_eval_fns=fns,
        # Self-contained resume: fisher/theta_star/λ/meta ride EVERY saved checkpoint — the
        # convbase artifacts never depend on the Fisher sidecar (T-12-14).
        checkpoint_extra={
            "fisher": fisher,
            "theta_star": theta_star,
            "ewc_lambda": LAMBDA_STAR,
            "fisher_meta": fisher_meta,
        },
        log_path=str(PROD_CSV),
        eval_interval=EVAL_INTERVAL,
        checkpoint_path=str(CONVBASE_LATEST),
        checkpoint_interval=CHECKPOINT_INTERVAL,
        best_checkpoint_path=str(CONVBASE_BEST),
    )
    wall = time.monotonic() - t0

    # ===== Loud end-of-run proofs (SystemExit on violation) =====
    export_slim(CONVBASE_BEST, CONVBASE_SLIM)

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

    # weights_only=False: own checkpoint written by this run (trusted-only).
    best_blob = torch.load(CONVBASE_BEST, weights_only=False)
    for key in ("fisher", "theta_star", "ewc_lambda", "fisher_meta"):
        _prove(key in best_blob, f"convbase_best.pt missing EWC extra {key!r} (T-12-14)")
    _prove(
        best_blob["ewc_lambda"] == LAMBDA_STAR,
        f"convbase_best.pt ewc_lambda {best_blob['ewc_lambda']!r} != λ* {LAMBDA_STAR}",
    )
    # LOCKED slim contract: the shippable artifact loads under the restricted unpickler.
    torch.load(CONVBASE_SLIM, weights_only=True)

    print(
        f"[finetune_dialog] proofs passed: step-0 row, final step {PROD_MAX_STEPS}, "
        f"finite retention, 4 EWC extras in convbase_best, slim weights_only=True"
    )
    print(
        f"[finetune_dialog] best step {best_blob['step']} val_loss {best_blob['val_loss']:.4f}; "
        f"retention step-0 {ret_col[0]:.4f} → final {ret_col[-1]:.4f} "
        f"(drift {ret_col[-1] - ret_col[0]:+.4f}); wall {wall / 60:.1f} min"
    )

    # ===== Phase-13 provenance block (DEMO-04 identical-seed λ=0 twin) =====
    print("[finetune_dialog] ===== Phase-13 provenance (λ=0 twin must match all but λ) =====")
    print(f"  seed: {SEED} (seed_everything immediately before GPT build — owns data order)")
    print(f"  train_config: {cfg}")
    print(f"  mask_arm: {MASK_ARM} (train_mask_bin=None)")
    print(f"  ewc_lambda: {LAMBDA_STAR} (the ONE bit the λ=0 twin flips)")
    print(f"  anchor fingerprint: {fingerprint}")
    print(f"  driver git_sha: {git_sha()}")


if __name__ == "__main__":
    main()
