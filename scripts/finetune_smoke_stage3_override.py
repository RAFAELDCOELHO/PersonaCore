"""Stage-3 λ sweep under the recorded D-07 Stage-2 override (Phase 12 Plan 04).

WHY THIS FILE EXISTS: the pre-registered Stage-2 retention gate (§7(a)) fired on ALL three LR
arms — 3e-4 (dialogue PPL 4.2034, retention drift +6.63), 9e-5 (4.4453, +3.85), 3e-5 (4.7771,
+2.81) vs anchor 2.1076 and margin K×Δ_ret = 0.1379 — and the driver halted per §9 (CSVs
committed at the halt, 7aac9e3). The halt was surfaced to the user (D-07 exception).

USER DECISION (override RECORDED, gate NOT amended): gate §7(a) fired on all three arms
because it tests retention against a no-EWC baseline — the "near-zero forgetting" expectation
presupposes the mechanism that only enters in Stage 3. This is NOT a calibration failure; it
is the central phenomenon Phase 12/13 exists to study. Proceed with the λ sweep at LR 9e-5,
with the drift measured at this LR (+3.85 retention drift, dialogue PPL 4.4453) formally
recorded as the "collapse without EWC" baseline that Stage 3 must beat.

scripts/finetune_smoke.py stays UNTOUCHED — every pre-registered gate stands. This wrapper
rebuilds the driver context verbatim, reloads Stages 0/0b/1/2 through the driver's own
skip-if-done machinery, re-evaluates the Stage-2 gate arithmetic WITHOUT the halt (and refuses
to run if any arm now passes — the override would be void), forces LR* = 9e-5 per the user
decision, then calls the driver's pre-registered ``stage3_lambda()`` and ``write_report()``
verbatim (§8 λ* rule + demonstrability guard + boundary-extension rule exactly as committed
in 10ba73e). This file is committed BEFORE any λ number exists — same discipline as the
driver's pre-registration (T-12-08).

Run: ``python scripts/finetune_smoke_stage3_override.py`` (inside the 3.11 venv, on the M3).
"""

import json
import time

import finetune_smoke as fs  # sets the MPS-fallback env before importing torch

OVERRIDE_LR_STAR = 9e-5  # the user decision at the D-07 Stage-2 halt (docstring above)


def stage2_gates_no_halt(ctx, stage1, noise):
    """fs.stage2_lr's gate arithmetic verbatim, minus the zero-passing SystemExit (§7).

    The gate itself is unchanged and re-evaluated on the committed CSVs; the override applies
    ONLY to the halt. Any arm passing ⇒ the recorded override is void ⇒ refuse and direct
    back to the pre-registered driver. (Stage-1 verdict was unmasked, so the pre-registered
    noise_a reuse branch is dead here — arms load fresh-run CSVs via skip-if-done.)
    """
    winner_masked = stage1["winner"] == "masked"
    margin_dialog = fs.K * noise["delta_dialog"]
    margin_ret = fs.K * noise["delta_ret"]
    anchor = ctx["anchors"]["retention_ppl_subbin_step0"]
    arms = {}
    for lr in fs.LR_GRID:
        arms[lr] = fs._run_arm(
            ctx,
            f"lr_{fs._lr_name(lr)}",
            lr=lr,
            lam=None,
            masked=winner_masked,
            seed=fs.SEED,
            max_steps=fs.SMOKE_STEPS,
            eval_interval=fs.EVAL_INTERVAL,
            extras=("dialog_ppl",),
        )
    gates = {}
    for lr, res in arms.items():
        stab = fs.instability_check(res["rows"], margin_dialog)
        drift = res["end_retention_ppl"] - anchor
        collapsed = fs.retention_collapse(res["end_retention_ppl"], anchor, margin_ret)
        gates[lr] = {
            "instability": stab,
            "retention_drift": drift,
            "retention_collapsed": collapsed,
            "passes": not stab["violated"] and not collapsed,
        }
        print(
            f"[override] lr={lr:g}: dialog_ppl={res['end_dialog_ppl']:.4f} "
            f"retention_drift={drift:+.6f} (margin {margin_ret:.6f}) "
            f"unstable={stab['violated']} → passes={gates[lr]['passes']}"
        )
    if any(gates[lr]["passes"] for lr in fs.LR_GRID):
        raise SystemExit(
            "[override] a Stage-2 arm now PASSES the pre-registered gates — the recorded "
            "override is void; re-run scripts/finetune_smoke.py instead."
        )
    print(f"[override] all Stage-2 arms fail §7(a) as recorded — LR* := {OVERRIDE_LR_STAR:g}")
    return {
        "arms": arms,
        "gates": gates,
        "lr_star": OVERRIDE_LR_STAR,
        "winner_masked": winner_masked,
    }


def main() -> None:
    t0 = time.monotonic()
    fs._never_clobber_guard()
    if not fs.ANCHORS_JSON.exists():
        raise SystemExit(f"[override] missing {fs.ANCHORS_JSON} — Pitfall 1 (see the driver).")
    for path in (
        fs.DIALOG_TRAIN,
        fs.DIALOG_TRAIN_MASK,
        fs.DIALOG_VAL,
        fs.DIALOG_VAL_MASK,
        fs.RETENTION_BIN,
    ):
        if not path.exists():
            raise FileNotFoundError(f"Missing local bin: {path}. Build the dialogue bins first.")
    if not fs.BEST_PATH.exists():
        raise FileNotFoundError(f"Missing {fs.BEST_PATH} (the fine-tune anchor).")

    summary = fs.preflight_device(strict=True)
    print(f"[override] preflight: {summary}")
    runtime = fs.RuntimeConfig()

    # ctx build — copied verbatim from fs.main() (the driver stays untouched by design).
    # weights_only=False: TRUSTED-only read of the project's OWN anchor checkpoint (T-12-10).
    blob = fs.torch.load(fs.BEST_PATH, weights_only=False)
    anchor_model = fs.GPT(fs.ModelConfig(**blob["model_config"]))
    anchor_model.load_state_dict(blob["model"])
    theta_star = {n: p.detach().clone().cpu() for n, p in anchor_model.named_parameters()}
    fisher = fs.load_fisher(
        fs.FISHER_CACHE,
        expected_fingerprint={
            "git_sha": blob["git_sha"],
            "step": blob["step"],
            "val_loss": blob["val_loss"],
        },
    )["fisher"]
    tok = fs.from_json(fs.TOKENIZER_PATH)  # FROZEN artifact — never retrain
    forbid = fs.undecodable_ids_mask(tok, fs.ModelConfig(**blob["model_config"]).vocab_size)
    anchors = json.loads(fs.ANCHORS_JSON.read_text(encoding="utf-8"))
    ctx = {
        "runtime": runtime,
        "blob": blob,
        "theta_star": theta_star,
        "fisher": fisher,
        "tok": tok,
        "forbid": forbid,
        "anchors": anchors,
    }
    anchor_model.to(runtime.device)
    dialog_ppl0, dialog_tokens0 = fs.masked_perplexity(
        anchor_model,
        fs.DIALOG_VAL,
        fs.DIALOG_VAL_MASK,
        fs.BLOCK_SIZE,
        runtime.device,
        forbid_ids=forbid,
    )
    ctx["dialog_ppl0"] = dialog_ppl0
    ctx["dialog_tokens0"] = dialog_tokens0
    ctx["role_norms0"] = {
        role: float(anchor_model.wte.weight[rid].norm().item()) for role, rid in fs.ROLE_IDS.items()
    }
    print(
        f"[override] step-0: dialog_ppl={dialog_ppl0:.4f} over {dialog_tokens0:,} tokens; "
        f"retention anchor {anchors['retention_ppl_subbin_step0']:.4f}"
    )
    del anchor_model

    cal = fs.stage0_calibrate(ctx)  # skip-if-done: reloads the committed Stage-0 run
    noise = fs.stage0b_noise(ctx, cal)  # skip-if-done: reloads the committed floor
    s1 = fs.stage1_masking(ctx, noise)  # skip-if-done: recomputes the unmasked verdict
    s2 = stage2_gates_no_halt(ctx, s1, noise)  # gate arithmetic intact; halt overridden
    s3 = fs.stage3_lambda(ctx, s2, noise)  # pre-registered §8, verbatim
    fs.write_report(ctx, cal, noise, s1, s2, s3)
    print(f"[override] stage-3 sequence complete in {(time.monotonic() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
