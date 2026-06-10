"""Slim inference-checkpoint tests: the shippable artifact (DEMO-02 / QA-02).

CPU-only, GPU/MPS-free. Proves the locked Phase-1 01-02 decision: the slim INFERENCE
checkpoint loads with ``torch.load(..., weights_only=True)`` — the restricted unpickler that
can never execute code on load (T-02-05 / T-07-02 lineage, T-08-01). The raw
``weights_only=True`` load *succeeding* IS the safe-load assertion.

Four behaviors:

  - test_export_strips_training_state — ``export_slim`` drops optimizer/scheduler/scaler/rng/
    train_config; the slim key set is EXACTLY {schema_version, model, model_config, git_sha,
    step, val_loss} (T-08-03: nothing else can ride along).
  - test_slim_loads_and_generates_cpu  — a GPT rebuilt from the slim file's own embedded
    ``model_config`` generates on CPU, and weight tying survives the round-trip via
    ``data_ptr()`` identity (MODEL-03 lineage).
  - test_slim_carries_provenance       — git_sha + step + val_loss + schema_version travel
    WITH the shipped weights (QA-02).
  - test_real_slim_artifact_generates_on_cpu — skipif-gated on the real (gitignored)
    ``checkpoints/model_slim.pt``: SKIPS cleanly on CI, runs locally after export.

The three mechanism tests use a tiny seeded GPT and a hand-built fake FULL checkpoint in
``tmp_path`` — never the real ``best.pt``. The mechanism generation test decodes through a
total stub tokenizer (the ``test_generation_text.py`` precedent): the frozen production
tokenizer decodes STRICTLY (WR-03) over a trained vocab of ids 0-538 (+ specials at 8184+),
so a RANDOM-init model's argmax over the full 8192-id space would hit an unknown id and raise
by design. The real-artifact test uses the real frozen tokenizer end-to-end.
"""

import dataclasses
import pathlib

import pytest
import torch

from personacore.checkpoint import export_slim, load_slim
from personacore.config import ModelConfig
from personacore.generation import generate_text_str
from personacore.model import GPT
from personacore.tokenizer import from_json

TOKENIZER_PATH = "artifacts/tokenizer.json"  # FROZEN production artifact — never retrain.
REAL_SLIM = pathlib.Path("checkpoints/model_slim.pt")  # gitignored; exported by Task 3.

# The EXACT shipped key set (T-08-03) and the training state export_slim must drop.
SLIM_KEYS = {"schema_version", "model", "model_config", "git_sha", "step", "val_loss"}
DROPPED_KEYS = {"optimizer", "scheduler", "scaler", "rng", "train_config"}


def _tiny_config() -> ModelConfig:
    # vocab_size/eos_id stay at the LOCKED defaults (8192/8184) so the artifact's embedded
    # config matches production shape; everything else is shrunk for a cheap CPU fixture.
    return ModelConfig(block_size=32, n_layer=1, n_head=2, n_embd=16)


class _StubTokenizer:
    """Total id->char decode for the tiny RANDOM-init model (mechanism test only).

    The frozen production tokenizer raises ``ValueError`` on ids outside its trained vocab
    (strict decode, WR-03) — correct for the TRAINED model, but a random-init tiny model's
    greedy argmax lands anywhere in [0, 8192). A total decode keeps the mechanism test about
    what it proves: the round-tripped weights drive generation on CPU.
    """

    def encode(self, text, allowed_special="all"):
        return []  # empty prompt body; the generation wrapper seeds [eos_id].

    def decode(self, ids):
        return "".join(chr(ord("a") + (i % 26)) for i in ids)


@pytest.fixture(scope="module")
def slim_paths(tmp_path_factory):
    """Write a fake FULL checkpoint from a tiny seeded GPT, then export the slim file once."""
    tmp = tmp_path_factory.mktemp("slim")
    cfg = _tiny_config()
    torch.manual_seed(1234)  # deterministic tiny weights -> deterministic greedy generation.
    model = GPT(cfg)
    full = {
        "schema_version": 1,
        "model": model.state_dict(),
        "model_config": dataclasses.asdict(cfg),
        "optimizer": {"state": {}},
        "scheduler": {},
        "scaler": None,
        "rng": {"python": 0},
        "train_config": {},
        "git_sha": "deadbeef0",
        "step": 7,
        "val_loss": 1.23,
    }
    full_path = tmp / "full.pt"
    slim_path = tmp / "model_slim.pt"
    torch.save(full, full_path)
    export_slim(full_path, slim_path)
    return full_path, slim_path


def test_export_strips_training_state(slim_paths):
    _, slim_path = slim_paths
    # The raw restricted-unpickler load SUCCEEDING is itself the safe-load bar (T-08-01).
    loaded = torch.load(slim_path, map_location="cpu", weights_only=True)
    assert set(loaded.keys()) == SLIM_KEYS
    for dropped in DROPPED_KEYS:
        assert dropped not in loaded, f"training state {dropped!r} leaked into the slim artifact"


def test_slim_loads_and_generates_cpu(slim_paths):
    _, slim_path = slim_paths
    loaded = load_slim(slim_path)
    # Config travels WITH the weights (QA-02): rebuild the arch from the artifact alone.
    model = GPT(ModelConfig(**loaded["model_config"]))
    model.load_state_dict(loaded["model"])
    # Tying survives the round-trip — TRUE shared storage, not a value copy (MODEL-03).
    assert model.lm_head.weight.data_ptr() == model.wte.weight.data_ptr()
    tok = _StubTokenizer()  # total decode — random-init ids would crash the strict frozen tok.
    out1 = generate_text_str(model, tok, "", max_new_tokens=8, greedy=True)
    out2 = generate_text_str(model, tok, "", max_new_tokens=8, greedy=True)
    assert isinstance(out1, str) and out1, "greedy generation must yield non-empty text"
    assert out1 == out2, "greedy generation must be deterministic across calls"


def test_slim_carries_provenance(slim_paths):
    _, slim_path = slim_paths
    loaded = load_slim(slim_path)
    # QA-02: provenance + config travel with the shipped artifact.
    assert loaded["schema_version"] == 1
    assert loaded["git_sha"] == "deadbeef0"
    assert loaded["step"] == 7
    assert loaded["val_loss"] == pytest.approx(1.23)


def _count_parameters(model) -> int:
    # Dedup by storage pointer: the tied wte/lm_head tensor is counted exactly once
    # (idiom from tests/test_gpt_param_count.py).
    seen = {}
    for p in model.parameters():
        seen[p.data_ptr()] = p.numel()
    return sum(seen.values())


@pytest.mark.skipif(not REAL_SLIM.exists(), reason="real slim artifact not present (CI)")
def test_real_slim_artifact_generates_on_cpu():
    loaded = load_slim(REAL_SLIM)
    model = GPT(ModelConfig(**loaded["model_config"]))
    model.load_state_dict(loaded["model"])
    # The real production arch: 13,891,584 params with the tied tensor deduped (MODEL-05).
    assert _count_parameters(model) == 13_891_584
    assert loaded["git_sha"].startswith("3a46815")  # provenance of the 49k-step best.pt run.
    tok = from_json(TOKENIZER_PATH)  # FROZEN production artifact — never retrain.
    out = generate_text_str(model, tok, "Once upon a time", max_new_tokens=20, greedy=True)
    assert isinstance(out, str) and out, "the shipped artifact must generate on laptop CPU"
