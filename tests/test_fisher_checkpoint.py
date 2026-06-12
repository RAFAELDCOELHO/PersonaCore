"""Fisher persistence tests: the **extra checkpoint seam + the shareable Fisher cache (EWC-01).

CPU-only, GPU/MPS-free. Two persistence stories pinned:

1. RESEARCH Pattern 3 — ``fisher`` / ``theta_star`` / ``ewc_lambda`` / ``fisher_meta`` travel
   BY VALUE through ``save_checkpoint(**extra)`` / ``load_checkpoint`` (resume checkpoints
   stay self-contained — no sidecar dependency), with the tied wte/lm_head storage
   deduplicated (Pitfall 1: ``wte.weight`` once, ``lm_head.weight`` absent — snapshot from
   ``named_parameters()``, never ``state_dict()``).
2. The Fisher cache safe-load bar (T-10-06, the same restricted-unpickler discipline that
   keeps the T-10-05 trusted full-pickle load script-side only): ``export_fisher`` writes
   tensors + primitive containers exclusively, so the file round-trips through
   ``torch.load(..., weights_only=True)``; ``load_fisher`` is the SINGLE choke point —
   schema gate FIRST, missing-key ``ValueError``, anchor-fingerprint check. NO ``theta_star``
   in the cache: it is recoverable from ``best.pt``, which the fingerprint pins (the cache is
   an optimization only — resume never depends on it).

Pinned behaviors:

  - test_extra_seam_round_trips — fisher/theta_star key sets survive and every tensor reloads
    ``torch.equal`` (NOT ``data_ptr`` — pointers legitimately change across serialization);
    ewc_lambda and fisher_meta round-trip ``==``.
  - test_dedup_pinned_through_seam — ``lm_head.weight`` absent from BOTH reloaded dicts,
    ``wte.weight`` present, exactly one theta_star entry per distinct param storage.
  - test_cache_safe_loads_with_exact_keys — the raw restricted-unpickler load succeeds and the
    key set is EXACTLY {schema_version, fisher, fisher_meta, anchor_fingerprint}.
  - test_cache_schema_version_mismatch_raises — the version gate fires BEFORE any consumption.
  - test_cache_missing_key_raises — the choke point names the dropped structural key.
  - test_fingerprint_mismatch_raises / test_matching_fingerprint_loads — a Fisher estimated at
    different weights is WRONG for this anchor (unlike the adapter's D-02 warn-but-load): a
    mismatching ``expected_fingerprint`` is a hard ``ValueError``; a matching one loads fine.
  - test_no_theta_star_in_cache — the cache never carries the anchor weights.
"""

import pytest
import torch

from personacore.checkpoint import (
    export_fisher,
    load_checkpoint,
    load_fisher,
    save_checkpoint,
)
from personacore.config import ModelConfig, TrainConfig
from personacore.model import GPT

# The EXACT shipped key set — nothing else can ride along in the shareable Fisher cache.
FISHER_KEYS = {"schema_version", "fisher", "fisher_meta", "anchor_fingerprint"}


def _tiny_config() -> ModelConfig:
    # vocab_size/eos_id stay at the LOCKED defaults so the embedded config matches production
    # shape; everything else is shrunk for a cheap CPU fixture (test_lora_artifact precedent).
    return ModelConfig(block_size=32, n_layer=1, n_head=2, n_embd=16)


def _fisher_meta_stub() -> dict:
    # Primitives only — the weights_only=True bar the real estimate_fisher meta also meets.
    return {
        "variant": "empirical_diag_fisher/groundtruth_targets/mean_normalized",
        "n_examples": 4,
        "seed": 1234,
        "block_size": 32,
        "bin_path": "data/train.bin",
        "normalized": True,
        "normalizer": 0.25,
        "spearman_half": 0.9,
        "rel_mean_change_a": 0.01,
        "rel_mean_change_b": 0.02,
        "spearman_method": "ordinal_double_argsort_no_tie_averaging",
    }


@pytest.fixture(scope="module")
def seam_round_trip(tmp_path_factory):
    """Save fisher/theta_star/ewc_lambda/fisher_meta through **extra, reload into a 2nd model."""
    tmp = tmp_path_factory.mktemp("ewc_seam")
    cfg = _tiny_config()
    torch.manual_seed(1234)
    model = GPT(cfg)
    # Snapshot from named_parameters() — the dedup rule (Pattern 3): tied tensor ONCE.
    theta_star = {n: p.detach().clone() for n, p in model.named_parameters()}
    fisher = {n: torch.rand_like(p) for n, p in model.named_parameters()}
    meta = _fisher_meta_stub()
    path = tmp / "ewc_ckpt.pt"
    save_checkpoint(
        path,
        model=model,
        optimizer=torch.optim.AdamW(model.parameters()),
        scheduler=None,
        step=7,
        model_config=cfg,
        train_config=TrainConfig(),
        git_sha="testsha",
        fisher=fisher,
        theta_star=theta_star,
        ewc_lambda=1.0,
        fisher_meta=meta,
    )
    second = GPT(cfg)  # fresh objects — the kill-and-resume shape (test_checkpoint precedent).
    ckpt = load_checkpoint(path, model=second)
    return model, fisher, theta_star, meta, ckpt


def test_extra_seam_round_trips(seam_round_trip):
    _, fisher, theta_star, meta, ckpt = seam_round_trip
    # Key sets survive the round trip exactly.
    assert set(ckpt["fisher"].keys()) == set(fisher.keys())
    assert set(ckpt["theta_star"].keys()) == set(theta_star.keys())
    # Every tensor reloads by VALUE — torch.equal, never data_ptr (pointers legitimately
    # change across serialization; Pattern 3 pins values, not storage identity).
    for name, tensor in fisher.items():
        assert torch.equal(ckpt["fisher"][name], tensor)
    for name, tensor in theta_star.items():
        assert torch.equal(ckpt["theta_star"][name], tensor)
    assert ckpt["ewc_lambda"] == 1.0
    assert ckpt["fisher_meta"] == meta


def test_dedup_pinned_through_seam(seam_round_trip):
    model, _, _, _, ckpt = seam_round_trip
    # Pitfall 1: the tied wte/lm_head storage appears EXACTLY once, under wte.weight —
    # a state_dict() snapshot would carry it twice and double-count 3.1M params at scale.
    for key in ("fisher", "theta_star"):
        assert "lm_head.weight" not in ckpt[key]
        assert "wte.weight" in ckpt[key]
    distinct_storages = {p.data_ptr() for p in model.parameters()}
    assert len(ckpt["theta_star"]) == len(distinct_storages)


@pytest.fixture(scope="module")
def fisher_cache(tmp_path_factory):
    """Export a tiny Fisher cache once, share across the cache-contract tests."""
    tmp = tmp_path_factory.mktemp("fisher_cache")
    cfg = _tiny_config()
    torch.manual_seed(4321)
    model = GPT(cfg)
    fisher = {n: torch.rand_like(p) for n, p in model.named_parameters()}
    meta = _fisher_meta_stub()
    fp = {"git_sha": "abc1234", "step": 5000, "val_loss": 0.7378}  # provenance trio (QA-02).
    path = tmp / "fisher_tinystories.pt"
    art = export_fisher(path, fisher=fisher, fisher_meta=meta, anchor_fingerprint=fp)
    return path, art, fp


def test_cache_safe_loads_with_exact_keys(fisher_cache):
    path, _, _ = fisher_cache
    # The raw restricted-unpickler load SUCCEEDING is itself the safe-load bar (T-10-06):
    # tensors + primitive containers only, ZERO code execution on load.
    loaded = torch.load(path, map_location="cpu", weights_only=True)
    assert set(loaded.keys()) == FISHER_KEYS


def test_cache_schema_version_mismatch_raises(fisher_cache, tmp_path):
    _, art, _ = fisher_cache
    bad = dict(art)
    bad["schema_version"] = 999
    bad_path = tmp_path / "bad_schema.pt"
    torch.save(bad, bad_path)
    # The version gate fires BEFORE any consumption — verbatim load_adapter/load_slim style.
    with pytest.raises(ValueError, match="schema_version"):
        load_fisher(bad_path)


@pytest.mark.parametrize("dropped", ["fisher", "fisher_meta", "anchor_fingerprint"])
def test_cache_missing_key_raises(fisher_cache, tmp_path, dropped):
    """The single choke point names missing structural keys — never a bare KeyError deep in a
    downstream consumer (Phase 12/13 A/B arms both load through here)."""
    _, art, fp = fisher_cache
    bad = dict(art)
    del bad[dropped]
    bad_path = tmp_path / f"missing_{dropped}.pt"
    torch.save(bad, bad_path)
    # expected_fingerprint exercises the loaded["anchor_fingerprint"] access path too.
    with pytest.raises(ValueError, match=dropped):
        load_fisher(bad_path, expected_fingerprint=fp)


def test_fingerprint_mismatch_raises(fisher_cache):
    path, _, _ = fisher_cache
    wrong_fp = {"git_sha": "different", "step": 1, "val_loss": 0.0}
    # UNLIKE the adapter's D-02 warn-but-load: a Fisher estimated at different weights is
    # mathematically wrong for this anchor — hard error, re-estimate (the run costs <1 min).
    with pytest.raises(ValueError, match="fingerprint"):
        load_fisher(path, expected_fingerprint=wrong_fp)


def test_matching_fingerprint_loads(fisher_cache):
    path, art, fp = fisher_cache
    loaded = load_fisher(path, expected_fingerprint=fp)
    assert loaded["anchor_fingerprint"] == fp
    for key, tensor in art["fisher"].items():
        assert torch.equal(loaded["fisher"][key], tensor)
    assert loaded["fisher_meta"] == art["fisher_meta"]


def test_no_theta_star_in_cache(fisher_cache):
    path, art, _ = fisher_cache
    # theta_star is deliberately NOT in the cache — recoverable from best.pt, which the
    # fingerprint pins; the cache is an optimization only (ARCHITECTURE anti-pattern 2).
    assert "theta_star" not in art
    loaded = torch.load(path, map_location="cpu", weights_only=True)
    assert "theta_star" not in loaded
