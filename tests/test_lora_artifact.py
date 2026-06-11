"""Adapter artifact tests: the shareable persona file (LORA-03 / D-01 / D-02).

CPU-only, GPU/MPS-free. Proves the locked artifact contract: ``adapter.pt`` loads with
``torch.load(..., weights_only=True)`` — the restricted unpickler that can never execute code
on load (T-09-07, same bar as the slim checkpoint). The raw ``weights_only=True`` load
*succeeding* IS the safe-load assertion.

Pinned behaviors:

  - test_artifact_safe_loads_with_exact_keys — the raw restricted-unpickler load succeeds and
    the key set is EXACTLY {schema_version, adapter, lora_config, base_fingerprint}.
  - test_no_base_weight_leak — every adapter key contains ``lora_``; no ``.base.`` key ever
    enters the shareable file (T-09-10); tensor count is the closed-form 2 * 6 * n_layer.
  - test_schema_version_mismatch_raises — ``load_adapter`` raises ``ValueError`` naming the
    schema_version before any consumption (T-09-08, verbatim ``load_slim`` contract).
  - test_fingerprint_mismatch_warns_but_loads — D-02: a wrong base fingerprint emits a
    ``UserWarning`` naming both fingerprints but the artifact STILL loads (base evolves
    mid-milestone; warn-but-load is the locked decision, not an oversight).
  - test_matching_fingerprint_is_silent — a matching fingerprint emits NO warning.
  - test_export_returns_dict_and_config_round_trips — ``export_adapter`` returns the dict it
    wrote (``export_slim`` precedent); ``LoRAConfig(**loaded["lora_config"])`` reconstructs.
  - test_provenance_trio_round_trips — git_sha/step/val_loss travel byte-for-byte (QA-02).
"""

import warnings
from dataclasses import asdict

import pytest
import torch

from personacore.checkpoint import export_adapter, load_adapter
from personacore.config import ModelConfig
from personacore.lora import TARGET_PROJECTIONS, LoRAConfig, inject_lora, lora_state_dict
from personacore.model import GPT

# The EXACT shipped key set (T-09-07) — nothing else can ride along in the persona file.
ADAPTER_KEYS = {"schema_version", "adapter", "lora_config", "base_fingerprint"}


def _tiny_config() -> ModelConfig:
    # vocab_size/eos_id stay at the LOCKED defaults (8192/8184) so the artifact's embedded
    # config matches production shape; everything else is shrunk for a cheap CPU fixture.
    return ModelConfig(block_size=32, n_layer=1, n_head=2, n_embd=16)


def _nudge_lora_B_nonzero(model) -> None:
    # B starts at the zeros identity gate; nudging makes the exported tensors observable
    # (a torch.equal round-trip on all-zeros would prove nothing).
    for name, p in model.named_parameters():
        if name.endswith("lora_B"):
            torch.nn.init.normal_(p, mean=0.0, std=0.02)


@pytest.fixture(scope="module")
def adapter_artifact(tmp_path_factory):
    """Build a tiny injected GPT, export its adapter artifact once, share across tests."""
    tmp = tmp_path_factory.mktemp("adapter")
    cfg = _tiny_config()
    torch.manual_seed(1234)  # deterministic tiny weights.
    model = GPT(cfg)
    lora_cfg = LoRAConfig(r=4)
    inject_lora(model, lora_cfg)
    _nudge_lora_B_nonzero(model)
    fp = {"git_sha": "abc1234", "step": 5000, "val_loss": 0.7378}  # D-02 fingerprint trio.
    path = tmp / "adapter.pt"
    art = export_adapter(
        path,
        adapter=lora_state_dict(model),
        lora_config=asdict(lora_cfg),
        base_fingerprint=fp,
    )
    return model, lora_cfg, path, art, fp


def test_artifact_safe_loads_with_exact_keys(adapter_artifact):
    _, _, path, _, _ = adapter_artifact
    # The raw restricted-unpickler load SUCCEEDING is itself the safe-load bar (T-09-07):
    # tensors + primitive containers only, ZERO code execution on load (D-01).
    loaded = torch.load(path, map_location="cpu", weights_only=True)
    assert set(loaded.keys()) == ADAPTER_KEYS


def test_no_base_weight_leak(adapter_artifact):
    model, _, path, _, _ = adapter_artifact
    loaded = torch.load(path, map_location="cpu", weights_only=True)
    adapter = loaded["adapter"]
    for key in adapter:
        assert "lora_" in key, f"non-LoRA key leaked into the persona file: {key!r}"
        assert ".base." not in key, f"base weight leaked into the persona file: {key!r}"
    # Closed form: 6 wrapped projections per block, A+B per wrap (T-09-10).
    assert len(adapter) == 2 * 6 * model.config.n_layer


def test_schema_version_mismatch_raises(adapter_artifact, tmp_path):
    _, _, _, art, _ = adapter_artifact
    bad = dict(art)
    bad["schema_version"] = 999
    bad_path = tmp_path / "bad_schema.pt"
    torch.save(bad, bad_path)
    # T-09-08: the version gate fires BEFORE any consumption, verbatim load_slim style.
    with pytest.raises(ValueError, match="schema_version"):
        load_adapter(bad_path)


def test_fingerprint_mismatch_warns_but_loads(adapter_artifact):
    _, _, path, art, _ = adapter_artifact
    wrong_fp = {"git_sha": "different", "step": 1, "val_loss": 0.0}
    # D-02 locked: warn-but-load. NO exception; a UserWarning names both fingerprints.
    with pytest.warns(UserWarning):
        loaded = load_adapter(path, expected_fingerprint=wrong_fp)
    for key, tensor in art["adapter"].items():
        assert torch.equal(loaded["adapter"][key], tensor)


def test_matching_fingerprint_is_silent(adapter_artifact):
    _, _, path, _, fp = adapter_artifact
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        load_adapter(path, expected_fingerprint=fp)
    assert len(caught) == 0, f"matching fingerprint must be silent, got: {caught}"


def test_export_returns_dict_and_config_round_trips(adapter_artifact):
    _, lora_cfg, path, art, _ = adapter_artifact
    # export_adapter returns the dict it wrote (export_slim's return-what-shipped precedent).
    assert set(art.keys()) == ADAPTER_KEYS
    loaded = load_adapter(path)
    rebuilt = LoRAConfig(**loaded["lora_config"])
    assert rebuilt.r == 4
    assert rebuilt.alpha == lora_cfg.alpha
    assert tuple(rebuilt.targets) == TARGET_PROJECTIONS
    # The artifact's metadata matches what the export call returned.
    assert loaded["lora_config"] == art["lora_config"]


def test_provenance_trio_round_trips(adapter_artifact):
    _, _, path, _, fp = adapter_artifact
    loaded = load_adapter(path)
    # QA-02: git_sha/step/val_loss travel through the artifact byte-for-byte (D-02 trio).
    assert loaded["base_fingerprint"] == fp
