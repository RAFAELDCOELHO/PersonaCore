"""Thin no-CLI evaluation driver: headline full-val perplexity + curated samples (EVAL-01/EVAL-02).

Mirrors ``scripts/pretrain_tinystories.py``: logic lives in ``src/personacore`` — this script only
wires the FROZEN artifacts (``checkpoints/best.pt``, ``data/val.bin``, ``artifacts/tokenizer.json``)
to the Plan-01 ``perplexity()`` sweep and the ``generate_text_str`` sampler, then writes the
qualitative samples to the git-TRACKED ``results/`` path. No CLI flag parsing (Phase-1 D-04): all
paths are ``_REPO_ROOT``-relative constants.

Run: ``python scripts/evaluate.py`` on the M3 (inside the Python 3.11 venv). ``RuntimeConfig()``
auto-resolves to MPS (fp32). The model itself is UNCHANGED — this driver only MEASURES the shipped
``best.pt``; it does not train or re-tokenize anything.

EVAL-01: the deterministic full-val ``perplexity()`` sweep is the CANONICAL headline number,
reported WITH its auditable token denominator (D-03). It is DISTINCT from ``best.pt``'s recorded
random-batch ``val_loss`` (0.7378 / ppl 2.091): that figure is a single sampled eval batch, while
this sweep scores every non-overlapping window of the whole val corpus (07-RESEARCH Pitfall 5).

EVAL-02: representative (NOT cherry-picked) greedy + warm samples over a FIXED in-repo prompt set,
written to ``results/samples.md`` for the portfolio artifact.

PREFLIGHT: ``preflight_device(strict=True)`` gates on a usable accelerator (it returns a summary
DICT and RAISES on a CPU-only box — it is a side-effecting gate, NOT the device-carrying config).
``runtime = RuntimeConfig()`` is the SEPARATE object that carries ``.device`` for placement/scoring.

SECURITY: ``torch.load(..., weights_only=False)`` is used ONLY for the project's OWN trusted
``best.pt`` (T-07-02) — never a foreign checkpoint. ``tokenizer.json`` is a data-only JSON artifact
(no code execution on load). The prompt set is a fixed in-repo constant, not user input.
"""

import math
import os
import pathlib

# An uncovered MPS op falls back to CPU rather than crashing — set BEFORE importing torch.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import torch  # noqa: E402  (must follow the MPS-fallback env set above)

from personacore.config import ModelConfig, RuntimeConfig  # noqa: E402
from personacore.evaluation import perplexity  # noqa: E402
from personacore.generation import generate_text_str  # noqa: E402
from personacore.model import GPT  # noqa: E402
from personacore.preflight import preflight_device  # noqa: E402
from personacore.tokenizer import from_json  # noqa: E402

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BEST_PATH = _REPO_ROOT / "checkpoints" / "best.pt"  # own trusted shipped checkpoint (gitignored)
VAL_BIN = _REPO_ROOT / "data" / "val.bin"  # LOCAL validation memmap
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"  # FROZEN production artifact
RESULTS_DIR = _REPO_ROOT / "results"  # git-TRACKED output (NOT logs/ or checkpoints/)

# Fixed in-repo prompt set (NOT user input). "" seeds the free-running [eos_id] document-start.
PROMPTS = (
    "Once upon a time",
    "The little robot",
    "Lily and Tom went to the",
    "",
)
SAMPLE_MAX_NEW_TOKENS = 200


def main() -> None:
    # GATE (side-effect / raise only): assert a usable accelerator. Returns a summary DICT — it is
    # NOT the device-carrying config, so its return is intentionally not used for placement.
    summary = preflight_device(strict=True)
    print(f"[evaluate] preflight: {summary}")

    if not BEST_PATH.exists():
        raise FileNotFoundError(
            f"Missing {BEST_PATH}. Run `python scripts/pretrain_tinystories.py` first."
        )
    if not VAL_BIN.exists():
        raise FileNotFoundError(
            f"Missing {VAL_BIN}. Run `python scripts/encode_corpus.py` first (Plan 01)."
        )

    runtime = RuntimeConfig()  # the SEPARATE device-carrying config (.device); MPS-aware (D-02).

    # Reconstruct the model from the checkpoint's own config; missing flag keys (the existing 7-key
    # best.pt predates EVAL-03) fall back to weight_tying=True/use_pos_emb=True — the trained arch.
    blob = torch.load(BEST_PATH, weights_only=False)  # own trusted file ONLY (T-07-02).
    model_cfg = ModelConfig(**blob["model_config"])
    model = GPT(model_cfg)
    model.load_state_dict(blob["model"])
    model.to(runtime.device)
    model.eval()

    # --- EVAL-01: deterministic full-val perplexity sweep (CANONICAL headline) -------------------
    ppl, total_tokens = perplexity(model, VAL_BIN, ModelConfig().block_size, runtime.device)
    print(
        f"[evaluate] headline full-val perplexity = {ppl:.4f}  "
        f"(over {total_tokens} scored target tokens)"
    )
    # Single-source the comparison figure from best.pt itself (WR-05) rather than embedding a stale
    # literal that can drift from the committed artifacts: best.pt's recorded random-batch val_loss
    # is a single sampled eval batch, while the sweep above scores every non-overlapping window of
    # the whole val corpus (07-RESEARCH Pitfall 5). They are expected to be close but not identical.
    recorded_val_loss = blob.get("val_loss")
    if recorded_val_loss is not None:
        recorded_val_loss = float(recorded_val_loss)
        print(
            "[evaluate] NOTE: this deterministic full-sweep PPL is the canonical headline; it "
            f"differs from best.pt's recorded random-batch val_loss {recorded_val_loss:.4f} / "
            f"ppl {math.exp(recorded_val_loss):.4f} (a single sampled eval batch, 07-RESEARCH "
            "Pitfall 5)."
        )
    else:
        print(
            "[evaluate] NOTE: this deterministic full-sweep PPL is the canonical headline; "
            "best.pt records no random-batch val_loss to compare against (07-RESEARCH Pitfall 5)."
        )

    # --- EVAL-02: representative greedy + warm samples over the fixed prompt set -----------------
    tok = from_json(TOKENIZER_PATH)  # FROZEN artifact — never retrain.
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    samples_path = RESULTS_DIR / "samples.md"

    lines = [
        "# PersonaCore — Qualitative Samples (EVAL-02)",
        "",
        "> These samples are REPRESENTATIVE, not cherry-picked. Each fixed prompt below is shown",
        "> with a deterministic greedy continuation and a warm (temperature=0.8, top_p=0.95)",
        "> continuation, both capped at "
        f"{SAMPLE_MAX_NEW_TOKENS} new tokens. The empty prompt is the free-running",
        "> document-start (seeded with [eos_id]).",
        "",
        f"Headline full-val perplexity: **{ppl:.4f}** over {total_tokens} scored target tokens.",
        "",
    ]

    for prompt in PROMPTS:
        label = repr(prompt) if prompt else '"" (free-running document-start)'
        greedy = generate_text_str(
            model, tok, prompt, max_new_tokens=SAMPLE_MAX_NEW_TOKENS, greedy=True
        )
        warm = generate_text_str(
            model,
            tok,
            prompt,
            max_new_tokens=SAMPLE_MAX_NEW_TOKENS,
            temperature=0.8,
            top_p=0.95,
        )
        lines += [
            f"## Prompt: {label}",
            "",
            "**Greedy (deterministic):**",
            "",
            f"> {prompt}{greedy}",
            "",
            "**Warm (temperature=0.8, top_p=0.95):**",
            "",
            f"> {prompt}{warm}",
            "",
        ]
        print(f"[evaluate] sampled prompt {label}")

    samples_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[evaluate] wrote {samples_path}")


if __name__ == "__main__":
    main()
