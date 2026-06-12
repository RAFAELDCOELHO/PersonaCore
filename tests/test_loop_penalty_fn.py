"""penalty_fn + checkpoint_extra loop-splice tests (EWC-02 / roadmap criterion 4).

The M2 EWC splice must be ADDITIVE: ``train(..., penalty_fn=None)`` (or omitted) must
reproduce the v1.0 trajectory bit-for-bit, and the penalty must join ``base_loss`` via
``assemble_loss`` BEFORE the ``/accum`` divide so exactly ONE full penalty enters each
optimizer step regardless of ``grad_accum_steps`` (Pitfall 5). ``checkpoint_extra=None``
must thread additively into all three in-loop ``save_checkpoint`` sites with default-None
producing v1.0-identical checkpoints (RESEARCH Open Q1).

Bit-identity is proven two ways (Pitfall 6 — executed evidence, not code review):

1. **Golden replay (platform-gated).** ``tests/fixtures/golden_trajectory_v1.json`` was
   captured from the git-clean, PRE-EDIT loop (its ``meta.captured_at_sha`` records the
   exact commit). The replay asserts exact CSV text + ``repr`` of the final loss + the
   sha256 of the single param tensor — but ONLY where ``(platform.system(),
   platform.machine())`` matches the fixture's ``meta.platform``: fp32 transcendental
   kernels are NOT bit-stable across OS/arch/BLAS backends, so e.g. x86_64 Linux CI must
   skip (with that named reason) rather than assert the capture platform's bits.
2. **In-process identities (every platform, never skip).** penalty_fn-omitted,
   ``penalty_fn=None``, and zero-penalty runs are asserted bitwise-identical to EACH
   OTHER in the same process — the v1.0-preservation guarantee CI relies on when the
   golden replay skips.

Golden-fixture regeneration recipe (only ever from a git-clean, pre-M2 loop.py): the
``meta`` block documents the full capture — ``seed_everything(meta.seed)``, build
``BigramLanguageModel(vocab_size=ModelConfig().vocab_size)`` (the
``tests/test_resume_curve._build`` recipe), then ``train()`` with
``TrainConfig(**meta.train_config)``, ``RuntimeConfig(device="cpu")`` passed EXPLICITLY,
``corpus_path=meta.corpus``, ``eos_id=meta.eos_id``, ``eval_interval=meta.eval_interval``,
a temp ``log_path``, ``return_final_loss=True``; record the CSV text, ``repr(float(final))``,
and ``hashlib.sha256`` of ``weight.detach().cpu().contiguous().numpy().tobytes()`` plus the
new ``git rev-parse HEAD`` and the capturing platform's identity. CPU-only, GPU-free.
"""

import hashlib
import json
import pathlib
import platform

import pytest
import torch

from personacore.config import ModelConfig, RuntimeConfig, TrainConfig
from personacore.continual import EWCPenalty
from personacore.model import BigramLanguageModel
from personacore.seeding import seed_everything
from personacore.training.loop import train

CORPUS_PATH = pathlib.Path(__file__).parent / "fixtures" / "bigram_corpus.txt"
GOLDEN_PATH = pathlib.Path(__file__).parent / "fixtures" / "golden_trajectory_v1.json"
EOS_ID = 8184

_GOLDEN = json.loads(GOLDEN_PATH.read_text())
_CAPTURE_PLATFORM = (_GOLDEN["meta"]["platform"]["system"], _GOLDEN["meta"]["platform"]["machine"])


def _param_sha256(model):
    """sha256 of the bigram's single parameter tensor — the bitwise trajectory fingerprint."""
    weight = model.token_embedding_table.weight
    return hashlib.sha256(weight.detach().cpu().contiguous().numpy().tobytes()).hexdigest()


def _run_recipe(log_path, **train_kwargs):
    """Run the golden fixture's exact meta recipe; return (csv_text, final_loss_repr, sha256).

    Re-seeds via seed_everything(1234) and rebuilds the model per call so multiple in-process
    runs are independent and comparable (the test_resume_curve._build recipe, CPU-explicit).
    """
    cfg = TrainConfig(lr=1e-2, warmup_steps=2, max_steps=5, batch_size=4)
    seed_everything(1234)
    model = BigramLanguageModel(vocab_size=ModelConfig().vocab_size)
    final = train(
        train_config=cfg,
        runtime_config=RuntimeConfig(device="cpu"),
        model=model,
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        log_path=log_path,
        eval_interval=1,
        return_final_loss=True,
        **train_kwargs,
    )
    return pathlib.Path(log_path).read_text(), repr(float(final)), _param_sha256(model)


@pytest.mark.skipif(
    (platform.system(), platform.machine()) != _CAPTURE_PLATFORM,
    reason=(
        "golden bitwise replay is only valid on the capture platform "
        f"{_CAPTURE_PLATFORM} — fp32 transcendental kernels are not bit-stable across "
        "OS/arch/BLAS backends, so a non-matching platform (e.g. x86_64 Linux CI) must "
        "not assert the captured bits; the in-process identity tests below carry the "
        "v1.0-preservation guarantee there"
    ),
)
def test_golden_trajectory_bit_identity(tmp_path):
    # Roadmap criterion 4: penalty_fn OMITTED reproduces the pre-edit v1.0 trajectory
    # bit-for-bit — exact CSV text, exact final-loss repr, exact param-bytes sha256.
    csv_text, final_repr, sha = _run_recipe(tmp_path / "golden_replay.csv")
    assert csv_text == _GOLDEN["csv_text"]
    assert final_repr == _GOLDEN["final_loss_repr"]
    assert sha == _GOLDEN["param_sha256"]


def test_omitted_equals_none_in_process(tmp_path):
    # Platform-independent v1.0-identity: penalty_fn omitted vs penalty_fn=None must be
    # bitwise identical to EACH OTHER in the same process. This test reads no platform
    # identity and never skips — it is the assertion CI relies on when the golden replay
    # skips on a non-capture platform.
    omitted = _run_recipe(tmp_path / "omitted.csv")
    explicit_none = _run_recipe(tmp_path / "none.csv", penalty_fn=None)
    assert omitted == explicit_none  # (csv_text, final_loss_repr, param_sha256) all bitwise


def test_zero_penalty_is_inert(tmp_path):
    # A zero penalty must be bitwise inert: x + 0.0 is exact identity for positive fp32
    # losses, so penalty_fn=lambda m: 0-tensor == penalty_fn=None run in the same process.
    none_run = _run_recipe(tmp_path / "none.csv", penalty_fn=None)
    zero_run = _run_recipe(tmp_path / "zero.csv", penalty_fn=lambda m: torch.tensor(0.0))
    assert none_run == zero_run


def _fresh_model(seed=0):
    """A deterministically-initialized bigram (fork_rng so global RNG is untouched)."""
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        return BigramLanguageModel(vocab_size=ModelConfig().vocab_size)


def test_penalty_once_per_optimizer_step_under_accum():
    # Pitfall 5: the penalty joins BEFORE the /accum divide, so accum=4 micro-batches must
    # contribute exactly ONE full penalty per optimizer step — numerically equivalent to a
    # single 4x-bigger batch. Mirrors test_grad_accum_equivalent_to_big_batch's synthetic
    # two-config comparison, with a REAL EWCPenalty anchored at displaced params so the
    # penalty gradient is non-zero (fisher=ones, theta_star = init params - 0.01).
    cfg_accum = TrainConfig(max_steps=1, warmup_steps=0, grad_accum_steps=4, batch_size=4)
    cfg_big = TrainConfig(max_steps=1, warmup_steps=0, grad_accum_steps=1, batch_size=16)
    runtime = RuntimeConfig(device="cpu")

    model_accum = _fresh_model()
    model_big = _fresh_model()
    theta_star = {n: p.detach().clone() - 0.01 for n, p in model_accum.named_parameters()}
    fisher = {n: torch.ones_like(p) for n, p in model_accum.named_parameters()}
    penalty = EWCPenalty(fisher, theta_star, lam=1.0, device="cpu")

    loss_accum = train(
        train_config=cfg_accum,
        runtime_config=runtime,
        model=model_accum,
        penalty_fn=penalty,
        return_final_loss=True,
    )
    loss_big = train(
        train_config=cfg_big,
        runtime_config=runtime,
        model=model_big,
        penalty_fn=penalty,
        return_final_loss=True,
    )
    # If the penalty were divided by accum (or applied per-micro-batch AFTER the divide),
    # the accumulated gradients — and hence the post-step params — would diverge.
    assert abs(float(loss_accum) - float(loss_big)) < 1e-3
    params_accum = dict(model_accum.named_parameters())
    params_big = dict(model_big.named_parameters())
    for name in params_accum:
        assert torch.allclose(params_accum[name], params_big[name], atol=1e-6), name


def test_penalty_called_once_per_micro_batch():
    # The penalty is evaluated per micro-batch (inside _optimizer_step's accumulation
    # loop): 2 optimizer steps x grad_accum_steps=3 -> exactly 6 calls.
    cfg = TrainConfig(max_steps=2, warmup_steps=0, grad_accum_steps=3, batch_size=2)
    calls = []

    def counting_penalty(model):
        calls.append(1)
        return torch.tensor(0.0)

    train(
        train_config=cfg,
        runtime_config=RuntimeConfig(device="cpu"),
        penalty_fn=counting_penalty,
    )
    assert len(calls) == 6


def test_checkpoint_extra_round_trips(tmp_path):
    # RESEARCH Open Q1: checkpoint_extra threads into ALL THREE save_checkpoint sites
    # (best.pt, in-loop latest.pt, end-of-call latest.pt) via the open-dict **extra seam
    # (the test_checkpoint.py::test_open_dict_extensible idiom); default omitted produces
    # a v1.0 checkpoint with NO extra keys.
    cfg = TrainConfig(lr=1e-2, warmup_steps=0, max_steps=2, batch_size=4)
    runtime = RuntimeConfig(device="cpu")
    extra = {"fisher": {"x": torch.ones(2)}, "theta_star": {"x": torch.zeros(2)}}

    latest = tmp_path / "latest.pt"
    best = tmp_path / "best.pt"
    seed_everything(1234)
    train(
        train_config=cfg,
        runtime_config=runtime,
        model=_fresh_model(),
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        log_path=tmp_path / "extra.csv",  # eval path active -> best.pt site fires too
        checkpoint_path=latest,
        best_checkpoint_path=best,
        checkpoint_interval=1,  # in-loop latest.pt site fires every step
        checkpoint_extra=extra,
    )
    for path in (latest, best):
        blob = torch.load(path, weights_only=False)
        assert torch.equal(blob["fisher"]["x"], torch.ones(2)), path
        assert torch.equal(blob["theta_star"]["x"], torch.zeros(2)), path

    # Default (checkpoint_extra omitted) -> v1.0-identical checkpoint: no "fisher" key.
    plain = tmp_path / "plain.pt"
    seed_everything(1234)
    train(
        train_config=cfg,
        runtime_config=runtime,
        model=_fresh_model(),
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        checkpoint_path=plain,
        checkpoint_interval=1,
    )
    blob = torch.load(plain, weights_only=False)
    assert "fisher" not in blob
    assert "theta_star" not in blob
