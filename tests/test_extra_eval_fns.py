"""extra_eval_fns loop-seam tests (Phase 12, TUNE-02 — per-interval extra CSV columns).

The Stage-2 fine-tune must log retention PPL / dialogue PPL / EWC penalty / role norms per
eval interval. The seam is one additive default-None kwarg: ``train(extra_eval_fns={key:
fn})`` appends one CSV column per key (per-run fieldnames = ``CSV_FIELDNAMES +
sorted(extra_eval_fns)`` — the module constant is NEVER mutated; ``CSVLogger``'s
DictWriter unknown-key raise is the enforcement against appending columns to an old file).

Two hygiene contracts pinned here (RESEARCH Pitfalls):

- **train-mode restore (Pitfall 4):** ``perplexity()`` calls ``model.eval()`` and never
  restores — the extras block must call ``model.train()`` afterward so subsequent steps
  train in train mode.
- **RNG hygiene:** the extras run inside a ``_rng_state()``/``_restore_rng`` snapshot so a
  non-pure fn (one that consumes torch RNG) cannot perturb the train trajectory
  (resume-equality, TRAIN-04).

Default None reproduces v1.0 bit-for-bit (the test_loop_penalty_fn identity idiom).
CPU-only, GPU-free.
"""

import hashlib
import pathlib

import torch

from personacore.config import ModelConfig, RuntimeConfig, TrainConfig
from personacore.model import BigramLanguageModel
from personacore.seeding import seed_everything
from personacore.training.loop import CSV_FIELDNAMES, train

CORPUS_PATH = pathlib.Path(__file__).parent / "fixtures" / "bigram_corpus.txt"
EOS_ID = 8184


def _param_sha256(model):
    """sha256 of the bigram's single parameter tensor — the bitwise trajectory fingerprint."""
    weight = model.token_embedding_table.weight
    return hashlib.sha256(weight.detach().cpu().contiguous().numpy().tobytes()).hexdigest()


def _run_recipe(log_path, **train_kwargs):
    """Run the golden fixture's exact meta recipe; return (csv_text, final_loss_repr, sha256)."""
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


def test_extra_columns_appended_sorted_and_constant_untouched(tmp_path):
    # Per-run fieldnames = CSV_FIELDNAMES + sorted(keys); every eval row carries the fn's
    # float value; the module constant CSV_FIELDNAMES is unchanged after the run.
    constant_before = list(CSV_FIELDNAMES)
    log_path = tmp_path / "extras.csv"
    _run_recipe(
        log_path,
        extra_eval_fns={"b_probe": lambda m: 2.0, "a_probe": lambda m: 1.0},
    )
    lines = log_path.read_text().strip().splitlines()
    header = lines[0].split(",")
    assert header == CSV_FIELDNAMES + ["a_probe", "b_probe"]  # sorted key order
    for row in lines[1:]:
        cells = row.split(",")
        assert float(cells[-2]) == 1.0  # a_probe
        assert float(cells[-1]) == 2.0  # b_probe
    assert list(CSV_FIELDNAMES) == constant_before  # module constant never mutated


def test_called_once_per_eval_logging_event(tmp_path):
    # NOTE for Plan 12-04: the v1.0 eval block does NOT log a step-0 row — the block runs
    # AFTER `step += 1`, so with eval_interval=1, max_steps=5 the rows are steps 1..5
    # (5 eval-logging events, no step 0 row). A step-0 retention baseline must be measured
    # OUTSIDE train() before the call.
    calls = []

    def counting_fn(model):
        calls.append(1)
        return 0.0

    log_path = tmp_path / "count.csv"
    _run_recipe(log_path, extra_eval_fns={"probe": counting_fn})
    n_rows = len(log_path.read_text().strip().splitlines()) - 1  # minus header
    assert n_rows == 5  # steps 1..5, no step-0 row (see NOTE above)
    assert len(calls) == n_rows  # exactly once per eval-logging event


def test_train_mode_restored_after_eval_leaking_fn(tmp_path):
    # Pitfall 4: perplexity() calls model.eval() and never restores. An fn mimicking that
    # must not poison subsequent training steps — the penalty_fn spy (which runs inside
    # every training forward) proves each post-eval step trains in train mode, and the
    # model is back in train mode when train() returns.
    training_flags = []

    def spy_penalty(model):
        training_flags.append(model.training)
        return torch.tensor(0.0)

    def eval_leaking_fn(model):
        model.eval()
        return 0.0

    cfg = TrainConfig(lr=1e-2, warmup_steps=2, max_steps=5, batch_size=4)
    seed_everything(1234)
    model = BigramLanguageModel(vocab_size=ModelConfig().vocab_size)
    model.train()
    train(
        train_config=cfg,
        runtime_config=RuntimeConfig(device="cpu"),
        model=model,
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        log_path=tmp_path / "modes.csv",
        eval_interval=1,
        penalty_fn=spy_penalty,
        extra_eval_fns={"leak": eval_leaking_fn},
    )
    assert model.training is True  # restored after the final eval block
    assert len(training_flags) == 5
    assert all(training_flags)  # every step (incl. those following an eval) trained in train mode


def test_rng_consuming_fn_does_not_perturb_trajectory(tmp_path):
    # RNG hygiene: an fn that consumes torch RNG yields the SAME CSV (train_loss column),
    # final loss, and param sha256 as a pure fn returning the same value — the extras block
    # runs inside a _rng_state()/_restore_rng snapshot.
    def pure_fn(model):
        return 0.5

    def rng_consuming_fn(model):
        torch.rand(1)  # would advance the global torch stream without the snapshot
        return 0.5

    pure = _run_recipe(tmp_path / "pure.csv", extra_eval_fns={"probe": pure_fn})
    impure = _run_recipe(tmp_path / "impure.csv", extra_eval_fns={"probe": rng_consuming_fn})
    assert pure == impure  # (csv_text, final_loss_repr, param_sha256) all bitwise


def test_omitted_equals_explicit_none_identity(tmp_path):
    # Platform-independent v1.0-identity: omitted vs extra_eval_fns=None must be bitwise
    # identical — byte-identical CSV, final-loss repr, param sha256.
    omitted = _run_recipe(tmp_path / "omitted.csv")
    explicit_none = _run_recipe(tmp_path / "none.csv", extra_eval_fns=None)
    assert omitted == explicit_none
