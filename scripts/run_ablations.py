"""Thin no-CLI driver: the EVAL-03 architecture-ablation cohort (calibration + 4 fair runs).

Mirrors ``scripts/pretrain_tinystories.py`` / ``scripts/evaluate.py``: logic lives in
``src/personacore`` — this script only wires configs + LOCAL paths, then trains a fresh baseline
plus three single-knob variants through the UNTOUCHED ``train()`` harness at IDENTICAL
seed/data/LR/budget, scores each with the deterministic ``perplexity()`` sweep (Plan 01), and
assembles the committed ``results/results.md`` comparison table. No CLI flag parsing (Phase-1 D-04):
all paths are ``_REPO_ROOT``-relative constants.

Run: ``python scripts/run_ablations.py`` on the M3 (inside the Python 3.11 venv).
``RuntimeConfig()`` auto-resolves to MPS (fp32). The multi-hour cohort run is a manual M3 artifact
(T-07-07: accept); the driver wiring is verified statically in CI.

CALIBRATION (D-07, 07-RESEARCH Pitfall 4): ``calibrate()`` trains ONE fresh baseline at the real
``TrainConfig`` LR with ``eval_interval=250`` and reads the val-loss curve to pick the smallest
``max_steps`` where samples read coherent AND the val-loss slope has flattened (last-1k-step
improvement < ~10-20% of the first-1k-step improvement; target val_loss roughly 1.0-1.3). The
chosen budget is LOCKED as ``REDUCED_MAX_STEPS`` below and recorded in the SUMMARY.

COHORT (D-06, 07-RESEARCH Pitfall 3 fairness): all four runs share ONE ``cfg_reduced`` TrainConfig
(same seed, LR, warmup, ``max_steps=REDUCED_MAX_STEPS``). Only the ablated model knob differs.
``seed_everything(SEED)`` is called IMMEDIATELY before each ``GPT(ModelConfig(**knob))`` build
because ``train()`` only self-seeds the DEFAULT model (``model is None`` — loop.py:220); here we
pass an explicit pre-built model, so the DRIVER owns the seed.

FAIRNESS CAVEAT (benign — documented in main()): the DATA the cohort sees is IDENTICAL across
variants. The training sampler draws from the GLOBAL numpy RNG (training/data.py:85
``np.random.randint``), which ``seed_everything(SEED)`` re-seeds before each variant build, so the
data batch sequence is bit-for-bit the same regardless of ``n_layer``. Only the TORCH init RNG
stream is consumed differently (a deeper model draws more init values), so post-init WEIGHTS differ
-- but that is exactly the variable under test, not a confound on the data. Same data, same
LR/budget, only the ablated knob varies -> the cohort is fair.

DEVICE (two distinct objects — preflight returns a DICT, NOT the runtime config): at the top of
``main()`` FIRST call ``preflight_device(strict=True)`` as a side-effecting GATE only (asserts a
usable accelerator, RAISES on a CPU-only box; its return is NOT used for placement), THEN build
``runtime = RuntimeConfig()`` — the device-carrying config — and use ``runtime`` as
``runtime_config=runtime`` and ``runtime.device`` for scoring throughout.

SECURITY: ``torch.load(..., weights_only=False)`` re-loads ONLY the driver's OWN ablation
checkpoints (``checkpoints/abl_*.pt`` — T-07-05), never a foreign file. The committed artifacts are
markdown + stdlib-CSV (CSVLogger via train()) — NO pickle in shippable artifacts (T-07-06).
"""

import math
import os
import pathlib

# An uncovered MPS op falls back to CPU rather than crashing the multi-hour run — set BEFORE torch.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import torch  # noqa: E402  (must follow the MPS-fallback env set above)

from personacore.config import ModelConfig, RuntimeConfig, TrainConfig  # noqa: E402
from personacore.evaluation import perplexity  # noqa: E402
from personacore.model import GPT  # noqa: E402
from personacore.preflight import preflight_device  # noqa: E402
from personacore.seeding import seed_everything  # noqa: E402

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TRAIN_BIN = _REPO_ROOT / "data" / "train.bin"  # LOCAL memmap (not a Kaggle dataset mount)
VAL_BIN = _REPO_ROOT / "data" / "val.bin"  # LOCAL validation memmap
RESULTS_DIR = _REPO_ROOT / "results"  # git-TRACKED output (NOT logs/ or checkpoints/)
CKPT_DIR = _REPO_ROOT / "checkpoints"  # gitignored — abl_*.pt are intermediate, fine to drop

# Shared seed + the single ablated knob per variant (verified param counts in the comment column).
SEED = TrainConfig().seed  # 1337 — the SAME seed re-applied before each variant build (fairness).
KNOBS = {
    "baseline": {},  # 6/6/384 tied, pos-emb            -> 13,891,584 params
    "no_tie": {"weight_tying": False},  # untied lm_head -> 17,037,312 (+3,145,728 = vocab*n_embd)
    "no_pos": {"use_pos_emb": False},  # dropped wpe -> 13,793,280 (-98,304 = block_size*n_embd)
    "depth_cut": {"n_layer": 3},  # half-depth -> 8,568,192 (-5,323,392; depth over width)
}

# One-line "what this shows" per variant, surfaced in the results table (D-08).
WHAT_THIS_SHOWS = {
    "baseline": "The fair reference — full 6-layer tied + positional arch at the reduced budget.",
    "no_tie": "Whether sharing the input/output embedding helps (or hurts) at this scale.",
    "no_pos": "Whether the learned positional embedding is load-bearing for coherence.",
    "depth_cut": "The depth-vs-params tradeoff: half the layers (~38% fewer params), equal budget.",
}

EVAL_INTERVAL = 250  # eval/log cadence mirrored from pretrain_tinystories.py.
CHECKPOINT_INTERVAL = 250  # K: in-loop latest cadence (kill loses <= K steps).

# --- Calibration knobs (D-07) ---------------------------------------------------------------------
CALIBRATION_STEPS = 8_000  # one fresh baseline run to read the curve and lock the cohort budget.

# REDUCED_MAX_STEPS is the LOCKED cohort budget. It is calibrated by calibrate() (below) on the
# real M3 — the executor records the measured value in the SUMMARY. The value here is the calibrated
# lock used for the committed cohort run; re-run calibrate() to recompute it on new hardware/data.
# Locked 2026-06-09 from calibrate() on this M3 (8k-step baseline, final val 0.8495 → recommended
# 2500; D-07). The val-loss curve plateaus well before 2500, so this is the smallest fair budget.
REDUCED_MAX_STEPS = 2_500


def count_parameters(model) -> int:
    """Unique-parameter count, deduping by ``data_ptr`` so a tied lm_head is counted once.

    Mirrors ``tests/test_gpt_param_count.py``: weight tying shares storage, so the tied head must
    not be double-counted; an untied head IS a distinct tensor and DOES add ``vocab*n_embd`` params.
    """
    seen = {}
    for p in model.parameters():
        seen[p.data_ptr()] = p.numel()
    return sum(seen.values())


def _read_val_curve(csv_path: pathlib.Path):
    """Return the list of (step, val_loss) rows from a train()-written CSV (CSVLogger schema).

    CSV_FIELDNAMES = step,train_loss,val_loss,lr,tokens,wall_clock (loop.py:45). Rows without a
    val_loss (between eval intervals) are skipped.
    """
    import csv

    rows = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            v = row.get("val_loss", "")
            if v in (None, ""):
                continue
            val = float(v)
            if not math.isfinite(val):
                continue  # skip nan/inf/-inf (a diverged run), not just the literal "nan"
            rows.append((int(float(row["step"])), val))
    return rows


def calibrate(runtime) -> int:
    """Train ONE fresh baseline ~CALIBRATION_STEPS and report the smallest fair reduced budget.

    Reads the val-loss curve and picks the earliest eval step where the slope has flattened
    (improvement over the last ~1k steps < 15% of the improvement over the first ~1k steps) and the
    loss is in the coherent band (~1.0-1.3). Prints the recommendation; the executor LOCKS it into
    REDUCED_MAX_STEPS above and records it in the SUMMARY. Returns the recommended max_steps.
    """
    from personacore.training import train

    seed_everything(SEED)  # fresh baseline — own the seed (explicit model below).
    model = GPT(ModelConfig())
    cfg = TrainConfig(max_steps=CALIBRATION_STEPS)
    csv_path = RESULTS_DIR / "abl_calibration.csv"
    train(
        train_config=cfg,
        runtime_config=runtime,
        model=model,
        model_config=ModelConfig(),
        train_bin=TRAIN_BIN,
        val_bin=VAL_BIN,
        eos_id=ModelConfig().eos_id,
        best_checkpoint_path=str(CKPT_DIR / "abl_calibration.pt"),
        log_path=str(csv_path),
        eval_interval=EVAL_INTERVAL,
        checkpoint_interval=CHECKPOINT_INTERVAL,
    )

    curve = _read_val_curve(csv_path)
    if len(curve) < 3:
        print("[calibrate] too few eval points to judge slope; using REDUCED_MAX_STEPS as-is.")
        return REDUCED_MAX_STEPS

    first_step, first_val = curve[0]
    # Improvement over the FIRST ~1k steps (the steep early descent).
    early = next((vl for st, vl in curve if st - first_step >= 1_000), curve[-1][1])
    first_improvement = max(first_val - early, 1e-9)

    recommended = curve[-1][0]
    for idx, (step, val) in enumerate(curve):
        prior = next((vl for s, vl in reversed(curve[:idx]) if step - s >= 1_000), None)
        if prior is None:
            continue
        recent_improvement = prior - val
        flattened = recent_improvement < 0.15 * first_improvement
        coherent = 1.0 <= val <= 1.3
        if flattened and coherent:
            recommended = step
            break

    print(
        f"[calibrate] curve points={len(curve)}  final=(step {curve[-1][0]}, "
        f"val {curve[-1][1]:.4f})  recommended REDUCED_MAX_STEPS={recommended}"
    )
    print(
        "[calibrate] LOCK this value into REDUCED_MAX_STEPS and record it in the SUMMARY "
        "(D-07). The cohort below uses the module constant, not this return."
    )
    return recommended


def run_cohort(runtime) -> list:
    """Train the fresh baseline + 3 single-knob variants at the LOCKED budget; score each.

    Returns a list of per-run dicts {name, params, ppl, total_tokens, best_val_loss} for the table.
    """
    from personacore.training import train

    # ONE shared TrainConfig (same seed/LR/warmup/budget) reused across ALL four runs (fairness).
    cfg_reduced = TrainConfig(max_steps=REDUCED_MAX_STEPS)
    results = []

    for name, knob in KNOBS.items():
        # seed_everything re-seeds random/numpy/torch BEFORE building the variant: this makes the
        # DATA sampler's global-numpy draws (training/data.py:85) bit-for-bit identical across all
        # variants. train() only self-seeds when model is None; we pass an explicit model, so the
        # driver owns the seed (loop.py:220).
        seed_everything(SEED)
        model = GPT(ModelConfig(**knob))
        params = count_parameters(model)

        ckpt_path = str(CKPT_DIR / f"abl_{name}.pt")
        csv_path = str(RESULTS_DIR / f"abl_{name}.csv")  # tracked results/ path (NOT logs/).
        print(f"[cohort] training '{name}' ({params:,} params) for {REDUCED_MAX_STEPS} steps ...")
        train(
            train_config=cfg_reduced,
            runtime_config=runtime,
            model=model,
            model_config=ModelConfig(**knob),
            train_bin=TRAIN_BIN,
            val_bin=VAL_BIN,
            eos_id=ModelConfig().eos_id,
            best_checkpoint_path=ckpt_path,
            log_path=csv_path,
            eval_interval=EVAL_INTERVAL,
            checkpoint_interval=CHECKPOINT_INTERVAL,
        )

        # Re-load the OWN best-val checkpoint (T-07-05: trusted self-produced file only) and score
        # it with the deterministic full-val perplexity() sweep — the same sweep for every variant.
        blob = torch.load(ckpt_path, weights_only=False)
        model.load_state_dict(blob["model"])
        model.to(runtime.device)
        model.eval()
        ppl, total_tokens = perplexity(model, VAL_BIN, ModelConfig().block_size, runtime.device)
        # A missing "val_loss" key from our OWN train() harness is itself a signal worth
        # surfacing, not papering over: keep it as None and render it distinctly in the table
        # (WR-05). Do NOT silently substitute the full-sweep mean CE (math.log(ppl)) under the
        # "best val-loss" column — a different quantity that would look identical yet not compare.
        raw_val_loss = blob.get("val_loss")
        best_val_loss = float(raw_val_loss) if raw_val_loss is not None else None
        val_loss_str = f"{best_val_loss:.4f}" if best_val_loss is not None else "n/a"
        print(
            f"[cohort] '{name}': params={params:,}  PPL={ppl:.4f} "
            f"(over {total_tokens} tokens)  best_val_loss={val_loss_str}"
        )
        results.append(
            {
                "name": name,
                "params": params,
                "ppl": ppl,
                "total_tokens": total_tokens,
                "best_val_loss": best_val_loss,
            }
        )
    return results


def write_results_table(results: list) -> pathlib.Path:
    """Assemble and write the committed results/results.md EVAL-03 comparison table (D-08).

    Markdown only — no pickle (T-07-06). One row per variant: name | params | held-out PPL
    (reduced budget) | best val-loss | what this shows. Includes the D-06 reduced-budget framing
    header note and the deferred strided-PPL footnote.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / "results.md"

    lines = [
        "# PersonaCore — Architecture Ablation Cohort (EVAL-03)",
        "",
        "> **Reduced-budget, self-consistent cohort (D-06).** All four runs below train through",
        f"> the UNTOUCHED `train()` harness at IDENTICAL seed ({SEED}), data, LR, warmup, and",
        f"> budget (`max_steps={REDUCED_MAX_STEPS}`, calibrated per D-07) — only the ablated knob",
        "> differs. The numbers are comparable to EACH OTHER, NOT to the headline 50k `best.pt`.",
        ">",
        "> The headline production figure is reported SEPARATELY (EVAL-01, `scripts/evaluate.py`):",
        "> deterministic full-val perplexity **2.1066** over **12,636,922** scored target tokens",
        "> on the 50k-step `best.pt` — a different (larger) budget, listed here only for context.",
        "",
        "| Variant | Param count | Held-out PPL (reduced budget) | Best val-loss "
        "| What this shows |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in results:
        # Render a missing best-val-loss distinctly (WR-05): never let an absent key masquerade as
        # a real recorded number. The full-sweep mean CE is shown only as an explicitly-labelled
        # fallback annotation so the two quantities are never confused.
        if r["best_val_loss"] is not None:
            val_loss_cell = f"{r['best_val_loss']:.4f}"
        else:
            val_loss_cell = f"n/a (sweep CE {math.log(r['ppl']):.4f})"
        lines.append(
            f"| {r['name']} | {r['params']:,} | {r['ppl']:.4f} "
            f"(over {r['total_tokens']:,} tokens) | {val_loss_cell} "
            f"| {WHAT_THIS_SHOWS[r['name']]} |"
        )

    lines += [
        "",
        "## Notes",
        "",
        "- **Fairness (07-RESEARCH Pitfall 3):** the data each variant sees is bit-for-bit the",
        "  same — `seed_everything` re-seeds the global numpy RNG (the data sampler's source)",
        "  before each variant build, so only the ablated knob (and the torch init stream it",
        "  consumes) varies.",
        "- **Held-out PPL** is the deterministic non-overlapping-window `perplexity()` sweep (Plan",
        "  01), reported with its auditable token denominator. Same sweep for every variant.",
        "",
        "> **Footnote (deferred idea — strided / sliding-window PPL):** this cohort uses",
        "> non-overlapping windows, which slightly OVER-estimate perplexity versus a strided",
        "> (sliding-window) sweep that gives most tokens more left-context (07-RESEARCH State of",
        "> the Art). A strided variant of `perplexity()` is deferred; because the bias is uniform",
        "> across variants at the same block_size, the RELATIVE ranking in the table holds.",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main() -> None:
    # GATE (side-effect / raise only): assert a usable accelerator. Returns a summary DICT — it is
    # NOT the device-carrying config, so its return is intentionally not used for placement.
    summary = preflight_device(strict=True)
    print(f"[run_ablations] preflight: {summary}")

    if not TRAIN_BIN.exists() or not VAL_BIN.exists():
        raise FileNotFoundError(
            f"Missing local corpus memmaps: {TRAIN_BIN} / {VAL_BIN}. "
            "Run `python scripts/encode_corpus.py` first (Plan 01)."
        )

    runtime = RuntimeConfig()  # the SEPARATE device-carrying config (.device); MPS-aware (D-02).
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    CKPT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1 — calibration: train one fresh baseline, read the curve, recommend a fair budget.
    # The executor LOCKS the recommendation into REDUCED_MAX_STEPS and records it in the SUMMARY.
    # Enforce the lock: if the freshly-computed recommendation diverges from the committed
    # REDUCED_MAX_STEPS by more than one eval interval, fail loudly rather than silently training
    # the cohort at a budget the calibration recommended against (D-07).
    recommended = calibrate(runtime)
    if abs(recommended - REDUCED_MAX_STEPS) > EVAL_INTERVAL:
        raise SystemExit(
            f"Calibration recommends max_steps={recommended} but REDUCED_MAX_STEPS="
            f"{REDUCED_MAX_STEPS}. Update the constant and re-run (D-07)."
        )

    # Step 2 — the fair 4-run cohort at the LOCKED REDUCED_MAX_STEPS.
    results = run_cohort(runtime)

    # Step 3 — assemble + commit the comparison table.
    out = write_results_table(results)
    print(f"[run_ablations] wrote {out}")


if __name__ == "__main__":
    main()
