"""Run-once TinyStories retention sub-bin builder + step-0 anchor measurement (TUNE-02).

Builds ``data/retention_val.bin`` — a ~1.0M-token document-level (eos-boundary) subsample of
``data/val.bin`` — and measures the retention curve's TRUE step-0 anchors BEFORE any Phase-12
training step exists. Full val is 12.6M tokens (~49k single-window forwards per PPL point):
minutes per eval interval, unaffordable on the training cadence (RESEARCH Pattern 1). And the
committed 2.1066 headline is NOT the curve's anchor — it is UNMASKED full-val, while
``retention_perplexity()`` masks dead ids (renormalized softmax => strictly lower PPL) and the
curve runs on a sub-bin (Pitfall 1). The anchor must be MEASURED at step 0 and committed, or
every downstream figure (Phase 13 VIZ-01's dashed line) will mislead.

The sub-bin is FROZEN for the milestone (T-12-05): an existing output makes the script exit
loudly instead of silently rebuilding — a silent rebuild would shift every curve point. Delete
BOTH outputs to rebuild (the seeded local rng makes the rebuild bit-reproducible). All proof
checks are explicit ``raise SystemExit`` (never a ``-O``-strippable bare assert).

Outputs: ``data/retention_val.bin`` (gitignored with the rest of data/; frozen-ness rides on
refuse-to-rerun + the seeded build) and ``results/retention_anchors.json`` (git-TRACKED —
Plan 12-04's smoke report embeds these numbers, Pitfall 6).

Run: ``python scripts/build_retention_bin.py`` (inside the Python 3.11 venv).
"""

import json
import os
import pathlib
import time

import numpy as np

# An uncovered MPS op falls back to CPU rather than crashing the run (T-05-04 precedent).
# Set BEFORE importing torch so the backend honors it for the whole process.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import torch  # noqa: E402  (must follow the MPS-fallback env set above)

from personacore.config import ModelConfig, RuntimeConfig  # noqa: E402
from personacore.evaluation import retention_perplexity  # noqa: E402
from personacore.model import GPT  # noqa: E402
from personacore.preflight import preflight_device  # noqa: E402
from personacore.provenance import git_sha  # noqa: E402
from personacore.tokenizer import from_json  # noqa: E402

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
VAL_BIN = _REPO_ROOT / "data" / "val.bin"  # full TinyStories val memmap (12.6M tokens)
OUT_BIN = _REPO_ROOT / "data" / "retention_val.bin"  # the frozen sub-bin (gitignored data/)
ANCHORS_JSON = _REPO_ROOT / "results" / "retention_anchors.json"  # git-TRACKED anchors
BEST_PATH = _REPO_ROOT / "checkpoints" / "best.pt"  # own trusted anchor checkpoint (gitignored)
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"  # FROZEN artifact — never retrain

# --- Tuned constants (rationale per knob) ---
EOS_ID = 8184  # ModelConfig.eos_id — the document separator val.bin was encoded with
# RESEARCH Pattern 1: ~1.0M tokens => ~3.9k windows => a retention point costs roughly a
# minute on MPS instead of minutes x10 for the 49k-window full sweep.
TARGET_TOKENS = 1_000_000
SEED = 1337  # local np.random.default_rng seed — global RNG streams stay untouched
BLOCK_SIZE = 256  # ModelConfig.block_size — the PPL sweep window
# v1.0 committed headline: UNMASKED perplexity() on full val. Recorded as historical
# reference ONLY — never the curve anchor (Pitfall 1).
HEADLINE_UNMASKED_FULLVAL = 2.1066


def main() -> None:
    t0 = time.monotonic()

    # Refuse-to-rerun (T-12-05): the sub-bin is FROZEN for the milestone — a silent rebuild
    # would shift every curve point. Delete BOTH outputs to rebuild (seeded => bit-identical).
    for frozen in (OUT_BIN, ANCHORS_JSON):
        if frozen.exists():
            raise SystemExit(
                f"[build_retention_bin] {frozen} already exists — refusing to rebuild the "
                "frozen retention sub-bin/anchors. Delete BOTH outputs to rebuild."
            )
    if not VAL_BIN.exists():
        raise FileNotFoundError(
            f"Missing local corpus memmap: {VAL_BIN}. Encode TinyStories first."
        )
    if not BEST_PATH.exists():
        raise FileNotFoundError(
            f"Missing {BEST_PATH}. Run `python scripts/pretrain_tinystories.py` first."
        )

    # --- (1) Build: doc-level (eos-boundary) subsample with a seeded LOCAL rng ---
    data = np.memmap(VAL_BIN, dtype=np.uint16, mode="r")
    eos_pos = np.nonzero(data == EOS_ID)[0]
    if len(eos_pos) == 0:
        raise SystemExit(f"[build_retention_bin] no eos ({EOS_ID}) found in {VAL_BIN}")
    # Doc k spans (starts[k], ends[k]) half-open; each doc KEEPS its trailing eos. Any tail
    # after the last eos is an incomplete document and is never sampled.
    starts = np.concatenate(([0], eos_pos[:-1] + 1))
    ends = eos_pos + 1
    lengths = ends - starts
    max_doc_len = int(lengths.max())

    rng = np.random.default_rng(SEED)  # local rng — global streams untouched (Pitfall 3)
    order = rng.permutation(len(lengths))
    shards = []
    total = 0
    for k in order:
        shards.append(np.asarray(data[starts[k] : ends[k]]))
        total += int(lengths[k])
        if total >= TARGET_TOKENS:
            break
    np.concatenate(shards).tofile(OUT_BIN)
    print(
        f"[build_retention_bin] wrote {OUT_BIN.name}: {total:,} tokens from "
        f"{len(shards):,} whole docs (of {len(lengths):,} in val)"
    )

    # --- (2) Loud sanity checks on the written bin (SystemExit, never bare assert) ---
    sub = np.fromfile(OUT_BIN, dtype=np.uint16)
    eos_count = int(np.count_nonzero(sub == EOS_ID))
    if not eos_count > 100:
        raise SystemExit(
            f"[proof 1] only {eos_count} eos tokens in {OUT_BIN.name} — a document-level "
            "subsample of ~1M tokens must contain hundreds of docs."
        )
    if not TARGET_TOKENS <= len(sub) <= 1.1 * TARGET_TOKENS + max_doc_len:
        raise SystemExit(
            f"[proof 2] {OUT_BIN.name} has {len(sub):,} tokens — outside "
            f"[{TARGET_TOKENS:,}, {int(1.1 * TARGET_TOKENS + max_doc_len):,}]."
        )
    tok = from_json(TOKENIZER_PATH)  # FROZEN artifact — never retrain.
    prefix = tok.decode(sub[:200].astype(np.int64).tolist())
    print(f"[build_retention_bin] {eos_count:,} docs (eos); decoded prefix: {prefix[:200]!r}")

    # --- (3) Step-0 anchors on best.pt, via THE frozen retention policy (DEBT-02) ---
    summary = preflight_device(strict=True)
    print(f"[build_retention_bin] preflight: {summary}")
    runtime = RuntimeConfig()  # resolves the preflighted device (MPS on the M3, fp32)

    # weights_only=False: the FULL resume checkpoint carries pickled optimizer/RNG objects.
    # TRUSTED-only read of the project's OWN checkpoint (T-12-07) — never a foreign file.
    blob = torch.load(BEST_PATH, weights_only=False)
    model_cfg = ModelConfig(**blob["model_config"])
    model = GPT(model_cfg)
    model.load_state_dict(blob["model"])
    model.to(runtime.device)
    model.eval()
    print(
        f"[build_retention_bin] anchor loaded: step {blob['step']}, "
        f"val_loss {blob['val_loss']}, device {runtime.device}"
    )

    ppl_sub, tokens_sub = retention_perplexity(model, OUT_BIN, BLOCK_SIZE, runtime.device, tok)
    print(
        f"[build_retention_bin] step-0 sub-bin anchor: retention PPL {ppl_sub:.4f} "
        f"over {tokens_sub:,} tokens"
    )
    print("[build_retention_bin] full-val reference sweep (~49k windows — takes minutes)...")
    ppl_full, tokens_full = retention_perplexity(model, VAL_BIN, BLOCK_SIZE, runtime.device, tok)
    print(
        f"[build_retention_bin] step-0 full-val reference: retention PPL {ppl_full:.4f} "
        f"over {tokens_full:,} tokens"
    )

    # --- (4) Proof: dead-id renormalization must LOWER PPL vs the unmasked headline on the
    # same bin — dead ids never appear as targets, so masking only removes probability mass
    # from wrong answers (Pitfall 1). ---
    if not ppl_full < HEADLINE_UNMASKED_FULLVAL:
        raise SystemExit(
            f"[proof 3] masked full-val PPL {ppl_full:.4f} not < unmasked headline "
            f"{HEADLINE_UNMASKED_FULLVAL} — dead-id renormalization must strictly lower PPL."
        )

    # --- (5) Commit the anchors (git-TRACKED results/ — Pitfall 6) ---
    anchors = {
        "retention_ppl_subbin_step0": ppl_sub,
        "retention_tokens_subbin": tokens_sub,
        "retention_ppl_fullval_step0": ppl_full,
        "retention_tokens_fullval": tokens_full,
        "headline_unmasked_fullval": HEADLINE_UNMASKED_FULLVAL,
        "headline_note": ("historical unmasked reference only — NOT the curve anchor, Pitfall 1"),
        "subbin_token_count": int(len(sub)),
        "subbin_seed": SEED,
        "anchor_val_loss": blob["val_loss"],
        "git_sha": git_sha(),
        "built": time.strftime("%Y-%m-%d", time.gmtime()),
    }
    with open(ANCHORS_JSON, "w", encoding="utf-8") as fh:
        json.dump(anchors, fh, indent=2)
        fh.write("\n")

    wall = time.monotonic() - t0
    print(f"[build_retention_bin] wrote {ANCHORS_JSON}")
    print(f"[build_retention_bin] all proof checks passed in {wall:.1f}s wall-clock")


if __name__ == "__main__":
    main()
