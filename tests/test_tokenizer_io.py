"""Freeze / reload round-trip (TOK-04).

The trained tokenizer serializes to a schema-versioned JSON artifact (data-only — never pickle,
mirroring checkpoint.py's schema-versioned save/load but with stdlib ``json``). A reloaded
tokenizer must be behaviorally identical and carry the locked vocab_size (8192) and an asserted
schema version.

RED until Plan 03 implements ``personacore.tokenizer.io``. All tests are CPU-only and GPU-free.
"""

import json
import pathlib

import pytest

from personacore.tokenizer import BPETokenizer
from personacore.tokenizer.io import SCHEMA_VERSION, from_json, save_json

CORPUS_PATH = pathlib.Path(__file__).parent / "fixtures" / "tiny_corpus.txt"
SAMPLE_STRINGS = ["hello world", " café — 日本語", "a<|endoftext|>b", "price: $1,234.56"]


@pytest.fixture(scope="module")
def tok() -> BPETokenizer:
    t = BPETokenizer()
    t.train(CORPUS_PATH.read_text(encoding="utf-8"), vocab_size=512)
    return t


def test_freeze_reload_identical(tmp_path, tok):
    # save -> from_json -> assert behavioral identity over sample strings (TOK-04).
    p = tmp_path / "tokenizer.json"
    save_json(tok, p)
    loaded = from_json(p)
    for s in SAMPLE_STRINGS:
        assert loaded.encode(s) == tok.encode(s)


def test_artifact_records_schema_and_vocab(tmp_path, tok):
    # The JSON payload carries the schema version and the locked vocab_size (8192).
    p = tmp_path / "tokenizer.json"
    save_json(tok, p)
    payload = json.loads(p.read_text(encoding="utf-8"))
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["vocab_size"] == tok.vocab_size


def test_loaded_vocab_size_locked(tmp_path):
    # A frozen artifact trained at the locked production vocab reloads at 8192.
    t = BPETokenizer()
    t.train(CORPUS_PATH.read_text(encoding="utf-8"), vocab_size=8192)
    p = tmp_path / "prod.json"
    save_json(t, p)
    loaded = from_json(p)
    assert loaded.vocab_size == 8192
