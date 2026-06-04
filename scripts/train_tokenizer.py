"""Thin one-time entry: load a bounded corpus -> train 8192-vocab BPE -> freeze artifact (D-09).

Runs ONCE to produce the committed ``artifacts/tokenizer.json`` that Phase 5 reuses FROZEN /
unchanged with NO retrain (D-09): a later tokenizer change can never invalidate a trained
checkpoint because ``vocab_size`` is locked into the frozen artifact (TOK-04).

Logic lives in ``src/personacore/tokenizer/`` (mirrors ``preflight_demo.py``). No command-line
flag parsing (D-04) — paths and hyperparameters are module constants / kwargs. Fully offline:
the default
corpus is the committed ``tests/fixtures/tiny_corpus.txt`` so the script runs with zero network
(D-09 permits a committed fixture as the bounded sample).

Optional larger bounded sample (D-09, NOT wired — keeps zero-network + no new dependency):
to train on a bigger slice, one-time fetch the TinyStoriesV2-GPT4 validation split, e.g.::

    import requests  # NOT a project dependency — example only
    url = "https://huggingface.co/datasets/roneneldan/TinyStories/resolve/main/TinyStoriesV2-GPT4-valid.txt"
    text = requests.get(url, timeout=60).text

then point ``CORPUS_PATH`` at the saved file. The committed-fixture path below stays the default.
"""

import pathlib

from personacore.seeding import seed_everything  # reuse Phase-1 determinism.
from personacore.tokenizer.bpe import BPETokenizer
from personacore.tokenizer.io import save_json

# Path-convention constants (like preflight_demo's CHECKPOINT_DIR) — no flag parsing (D-04).
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CORPUS_PATH = _REPO_ROOT / "tests" / "fixtures" / "tiny_corpus.txt"
ARTIFACT_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"
VOCAB_SIZE = 8192  # LOCKED production vocab (D-01/D-03); Phase 5 sizes around it.


def main() -> None:
    seed_everything(1337)  # deterministic merge order across runs (TOK-01).
    text = CORPUS_PATH.read_text(encoding="utf-8")
    tok = BPETokenizer().train(text, vocab_size=VOCAB_SIZE)
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    save_json(tok, ARTIFACT_PATH)
    print(f"[train_tokenizer] froze vocab_size={tok.vocab_size} -> {ARTIFACT_PATH}")


if __name__ == "__main__":
    main()
