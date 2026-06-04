"""Thin entry point: build configs -> seed -> train the bigram harness end-to-end (D-09 / D-04).

The MVP "see output" slice: run ``python scripts/train_bigram.py`` and the bigram trains through
the full harness on the committed fixture (tokenize -> train -> sample -> decode), then PRINTS a
decoded sampled string. Mirrors ``train_tokenizer.py`` / ``preflight_demo.py``: logic lives in
``src/personacore/{model,training}`` — this script only wires configs + paths. NO argparse (D-04):
paths are ``_REPO_ROOT``-relative constants and hyperparameters are config-dataclass overrides.

Run outputs (``*.pt`` checkpoint, CSV log) land in ``.gitignore``d paths (``*.pt``, ``logs/``) so
weight-based memory is never committed (T-03-05 / project privacy requirement). This script keeps
its budget tiny (a handful of steps) — it is a smoke/demo, not the long pretrain (that is Phase 5).
"""

import pathlib

import torch

from personacore.config import ModelConfig, RuntimeConfig, TrainConfig
from personacore.model import BigramLanguageModel
from personacore.seeding import seed_everything
from personacore.tokenizer import from_json
from personacore.training import sample, train

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURE_PATH = _REPO_ROOT / "tests" / "fixtures" / "bigram_corpus.txt"
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"
LOG_PATH = _REPO_ROOT / "logs" / "bigram_train.csv"  # gitignored (logs/)


def main() -> None:
    seed_everything(TrainConfig().seed)  # FRESH run only — resume restores RNG state instead.

    runtime = RuntimeConfig()
    model_cfg = ModelConfig()
    # A small demo budget: warmup-free, a few steps — enough to prove the loop runs and produces
    # text, NOT the Phase-5 long pretrain. fp32 default (AMP auto-off on CPU via RuntimeConfig).
    train_cfg = TrainConfig(lr=1e-2, warmup_steps=0, max_steps=20, batch_size=8)

    model = BigramLanguageModel(vocab_size=model_cfg.vocab_size)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    train(
        train_config=train_cfg,
        runtime_config=runtime,
        model=model,
        model_config=model_cfg,
        corpus_path=FIXTURE_PATH,
        eos_id=model_cfg.eos_id,
        log_path=LOG_PATH,
    )

    # tokenize -> train -> sample -> DECODE -> see output (the MVP payoff, D-11).
    tok = from_json(TOKENIZER_PATH)
    start = torch.zeros((1, 1), dtype=torch.long, device=runtime.device)  # a single seed token
    out_ids = sample(model, start, max_new_tokens=40, temperature=1.0)[0].tolist()
    # The bigram's embedding spans the full LOCKED vocab_size (8192), but this fixture-frozen
    # tokenizer only populated the ids it actually saw (a few hundred). An untrained/lightly
    # trained bigram can therefore emit ids with no decode mapping. ``decode`` is strict BY DESIGN
    # (a genuine corpus id must raise — WR-03), so the script — not the tokenizer — bridges the
    # model/tokenizer vocab gap: keep only decodable ids for this smoke demo (Phase-5 pretraining
    # on the real corpus closes the gap; Phase-6 sampling adds proper constraints).
    known = set(tok.vocab) | set(tok.special_tokens.values())
    decodable = [i for i in out_ids if i in known]
    text = tok.decode(decodable) if decodable else "<no decodable tokens sampled>"
    print(
        f"[train_bigram] trained {train_cfg.max_steps} steps; "
        f"sampled {len(out_ids)} ids ({len(decodable)} decodable):\n{text!r}"
    )


if __name__ == "__main__":
    main()
