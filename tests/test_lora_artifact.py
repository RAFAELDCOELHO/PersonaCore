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
  - test_two_artifact_load_reproduces_logits — D-03: ``load_slim`` + ``load_adapter`` +
    ``inject_lora`` + key-audited ``load_adapter_weights`` on FRESH objects reproduces the
    exporting model's logits bit-identically (``torch.equal``) — the literal "compatible
    with the slim contract" proof; no merged-slim export anywhere (deferred per CONTEXT).
  - test_real_slim_two_artifact_load_cpu — skipif-gated on the real (gitignored)
    ``checkpoints/model_slim.pt``: SKIPS cleanly on CI, runs the full two-artifact flow
    against the real 13.9M base locally.
"""

import pathlib
import warnings
from dataclasses import asdict

import pytest
import torch

from personacore.checkpoint import (
    export_adapter,
    export_slim,
    load_adapter,
    load_slim,
    save_checkpoint,
)
from personacore.config import ModelConfig, TrainConfig
from personacore.lora import (
    TARGET_PROJECTIONS,
    LoRAConfig,
    inject_lora,
    load_adapter_weights,
    lora_state_dict,
)
from personacore.model import GPT

REAL_SLIM = pathlib.Path("checkpoints/model_slim.pt")  # gitignored; exported by Phase 8.

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


def test_two_artifact_load_reproduces_logits(tmp_path):
    """D-03: load_slim + load_adapter + inject + key-audited apply == exporter, bit-identical."""
    cfg = _tiny_config()
    torch.manual_seed(1234)
    base = GPT(cfg)
    full_path = tmp_path / "full.pt"
    slim_path = tmp_path / "model_slim.pt"
    adapter_path = tmp_path / "adapter.pt"
    save_checkpoint(
        full_path,
        model=base,
        optimizer=torch.optim.AdamW(base.parameters()),
        scheduler=None,
        step=0,
        model_config=cfg,
        train_config=TrainConfig(),
        git_sha="testsha",
    )
    export_slim(full_path, slim_path)

    # DONOR: rebuild from the slim artifact alone, inject, nudge, export the persona file.
    donor_slim = load_slim(slim_path)
    donor = GPT(ModelConfig(**donor_slim["model_config"]))
    donor.load_state_dict(donor_slim["model"])
    lora_cfg = LoRAConfig(r=4)
    inject_lora(donor, lora_cfg)
    _nudge_lora_B_nonzero(donor)
    fp = {
        "git_sha": donor_slim["git_sha"],
        "step": donor_slim["step"],
        "val_loss": donor_slim["val_loss"],
    }
    export_adapter(
        adapter_path,
        adapter=lora_state_dict(donor),
        lora_config=asdict(lora_cfg),
        base_fingerprint=fp,
    )
    donor.eval()
    torch.manual_seed(999)
    batch = torch.randint(0, cfg.vocab_size, (2, 8))
    with torch.no_grad():
        donor_logits, _ = donor(batch)

    # CONSUMER: fresh objects, nothing shared — the LITERAL D-03 two-artifact flow.
    consumer_slim = load_slim(slim_path)
    consumer = GPT(ModelConfig(**consumer_slim["model_config"]))
    consumer.load_state_dict(consumer_slim["model"])
    art = load_adapter(adapter_path, expected_fingerprint=fp)
    inject_lora(consumer, LoRAConfig(**art["lora_config"]))
    load_adapter_weights(consumer, art)  # key-audited apply (09-01 seam).
    consumer.eval()
    with torch.no_grad():
        consumer_logits, _ = consumer(batch)

    # Same base tensors + same adapter tensors + same fp32 math => bit-identity.
    assert torch.equal(consumer_logits, donor_logits)


@pytest.mark.skipif(not REAL_SLIM.exists(), reason="real slim artifact not present (CI)")
def test_real_slim_two_artifact_load_cpu(tmp_path):
    """The D-03 flow against the real 13.9M base: export, two-artifact load, forward sanity."""
    loaded = load_slim(REAL_SLIM)
    model = GPT(ModelConfig(**loaded["model_config"]))
    model.load_state_dict(loaded["model"])
    lora_cfg = LoRAConfig()  # production defaults: r=8, alpha=16.0.
    wrapped = inject_lora(model, lora_cfg)
    assert wrapped == 6 * loaded["model_config"]["n_layer"]
    _nudge_lora_B_nonzero(model)
    fp = {"git_sha": loaded["git_sha"], "step": loaded["step"], "val_loss": loaded["val_loss"]}
    adapter_path = tmp_path / "adapter.pt"
    export_adapter(
        adapter_path,
        adapter=lora_state_dict(model),
        lora_config=asdict(lora_cfg),
        base_fingerprint=fp,
    )
    art = load_adapter(adapter_path, expected_fingerprint=fp)
    load_adapter_weights(model, art)
    model.eval()
    vocab_size = loaded["model_config"]["vocab_size"]
    batch = torch.randint(0, vocab_size, (2, 16))
    with torch.no_grad():
        logits, _ = model(batch)
    assert logits.shape == (2, 16, vocab_size)  # CPU-only shape sanity on the real base.
