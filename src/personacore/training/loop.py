"""End-to-end training loop orchestration (TRAIN-01 / TRAIN-02 / TRAIN-04 / TRAIN-06).

This is the harness the disposable bigram exists to de-risk: it drives the Phase-1/2 primitives
(``RuntimeConfig.autocast`` + ``GradScaler``, ``save_checkpoint``/``load_checkpoint``,
``CSVLogger``, ``seed_everything``, ``git_sha``) and the Plan-02/03 modules
(``BigramLanguageModel``, ``assemble_loss``, ``build_scheduler``, ``load_split``/``get_batch``)
into a single step loop. Almost no novel infrastructure lives here — the from-scratch content is
the *orchestration* and two load-bearing seams:

- **AMP step ordering under grad accumulation (TRAIN-02).** Per optimizer step the loop records
  ``scale``×grad_accum_steps (backward) -> ``unscale_`` (exactly once) -> ``clip`` -> ``step`` ->
  ``update`` -> ``scheduler.step`` (once per optimizer step, NOT per micro-batch — Pitfall 2).
  On CPU the scaler is a no-op (``enabled=runtime.amp`` and ``RuntimeConfig`` auto-disables AMP
  on CPU), so the SAME code path runs CPU/GPU and the ordering stays observable (Pitfall 1).
- **Resume trajectory + curve reproducibility (TRAIN-04).** On resume the loop calls
  ``load_checkpoint`` (which RESTORES RNG STATE, never re-seeds), reads ``ckpt["step"]``, continues
  the loop counter, and re-opens the SAME CSV path so the curve is appended without a duplicate
  header (Pitfall 4). Validation (``estimate_loss``) snapshots/restores the global RNG around its
  own sampling so it never perturbs the train trajectory — that is what keeps a killed+resumed run
  bit-identical (within 1e-6) to an uninterrupted one.

D-03/D-04/TRAIN-06: loss is always assembled via ``assemble_loss(base, ())`` (identity in M1; the
additive EWC penalty plugs in here in M2 with no loop change). D-11: the minimal ``sample`` lives
HERE as a free function (not on the model) so Phase-6's richer ``generate`` supersedes it without a
model rewrite. The loop NEVER calls ``torch.cuda.*`` — ``RuntimeConfig`` is the single device/AMP
source of truth (config.py:44-61).
"""

import random

import numpy as np
import torch
from torch.amp import GradScaler

from personacore.checkpoint import load_checkpoint, save_checkpoint
from personacore.config import ModelConfig, RuntimeConfig
from personacore.logging import CSVLogger
from personacore.provenance import git_sha

from .data import get_batch, load_split
from .loss import assemble_loss
from .schedule import build_scheduler

CSV_FIELDNAMES = ["step", "train_loss", "val_loss", "lr", "tokens", "wall_clock"]


def _rng_state():
    """Snapshot the full (python/numpy/torch) global RNG state."""
    return (random.getstate(), np.random.get_state(), torch.get_rng_state())


def _restore_rng(state):
    """Restore a previously captured global RNG state (so val sampling never perturbs train)."""
    py_state, np_state, torch_state = state
    random.setstate(py_state)
    np.random.set_state(np_state)
    torch.set_rng_state(torch_state)


@torch.no_grad()
def estimate_loss(model, val_ids, train_cfg, model_cfg, device, iters=20):
    """Mean validation CE under ``model.eval()`` + ``no_grad``, restoring ``model.train()``.

    Snapshots and restores the global RNG around the val draws so the periodic eval does NOT
    perturb the train trajectory's random stream (the resume-equality contract, TRAIN-04).
    ``iters`` is clamped so a tiny fixture (few val windows) still produces a stable estimate.
    """
    rng = _rng_state()
    model.eval()
    block_size = model_cfg.block_size
    # A bounded fixture's val split may be shorter than block_size; shrink the window so
    # get_batch's start bound (len(arr) - block_size - 1) stays positive.
    eff_block = min(block_size, max(1, len(val_ids) - 2))
    losses = []
    for _ in range(iters):
        xb, yb = get_batch(val_ids, train_cfg.batch_size, eff_block, device)
        _, loss = model(xb, yb)
        losses.append(loss.item())
    model.train()
    _restore_rng(rng)
    return sum(losses) / len(losses)


@torch.no_grad()
def sample(model, idx, max_new_tokens, temperature=1.0):
    """Minimal next-token sampler (D-11, Open Q2): extend ``idx`` by ``max_new_tokens``.

    Greedy-with-temperature multinomial draw on the last position's logits. Deliberately NO
    top-k/top-p/EOS-stop — that richer ``generate`` is Phase 6 (GEN); this only proves the
    tokenize -> train -> sample -> decode loop produces text (MVP "see output").
    """
    for _ in range(max_new_tokens):
        logits, _ = model(idx)  # (B, T, V)
        logits = logits[:, -1, :] / temperature
        probs = torch.softmax(logits, dim=-1)
        next_id = torch.multinomial(probs, num_samples=1)
        idx = torch.cat([idx, next_id], dim=1)
    return idx


def _optimizer_step(model, optimizer, scheduler, scaler, train_cfg, runtime, batch_fn):
    """Run ONE optimizer step with the load-bearing AMP+accum+clip ordering (TRAIN-02).

    ``batch_fn(micro)`` yields ``(xb, yb)`` for each micro-batch. Order is mandatory:
    scale->backward × grad_accum_steps -> unscale_ (once) -> clip -> step -> update -> scheduler.
    Returns the (unscaled, accumulation-corrected) training loss for the step.
    """
    optimizer.zero_grad(set_to_none=True)
    accum = max(1, train_cfg.grad_accum_steps)
    # Sum the per-micro-batch loss BEFORE the /accum scaling, then average -> the loss for the
    # effective (big) batch. This is what makes grad_accum_steps=N match one N×-bigger batch.
    summed = 0.0
    for micro in range(accum):
        xb, yb = batch_fn(micro)
        with runtime.autocast():  # RuntimeConfig.autocast() — single AMP source (no torch.cuda.*)
            _, base_loss = model(xb, yb)
            total = assemble_loss(base_loss, ())  # identity in M1 (D-04)
            loss = total / accum  # scale so accumulated grads average across micro-batches
        scaler.scale(loss).backward()
        summed += float(base_loss.item())
    scaler.unscale_(optimizer)  # UNSCALE before clip (mandatory order — Pitfall 1)
    torch.nn.utils.clip_grad_norm_(model.parameters(), train_cfg.grad_clip)
    scaler.step(optimizer)
    scaler.update()
    scheduler.step()  # ONCE per optimizer step, never per micro-batch (Pitfall 2)
    return summed / accum


def train(
    *,
    train_config,
    runtime_config=None,
    model=None,
    model_config=None,
    corpus_path=None,
    eos_id=8184,
    fixed_batch=None,
    scaler=None,
    resume_from=None,
    checkpoint_path=None,
    log_path=None,
    max_steps_override=None,
    eval_interval=1,
    return_final_loss=False,
):
    """Train the model end-to-end: AdamW + warmup/cosine + grad-clip + grad-accum, fp32 default.

    The loop wires the existing primitives — it builds nothing new. Data comes from ``fixed_batch``
    (overfit gate, TRAIN-05) when given, else from ``load_split(corpus_path)`` (the committed
    fixture path). Periodic ``estimate_loss`` is logged to ``log_path`` via the restart-safe
    ``CSVLogger``; ``checkpoint_path`` saves a resumable open-dict checkpoint; ``resume_from``
    restores model/optimizer/scheduler + RNG STATE and continues the SAME trajectory (TRAIN-04).

    Args:
        train_config: ``TrainConfig`` hyperparameters (lr/steps/warmup/accum/clip/weight_decay).
        runtime_config: ``RuntimeConfig`` device/AMP source; defaults to a fresh one.
        model: a pre-built model; defaults to ``BigramLanguageModel(model_config.vocab_size)``.
        model_config: ``ModelConfig`` (vocab/block_size); defaults to ``ModelConfig()``.
        corpus_path: fixture to ``load_split`` when ``fixed_batch`` is None.
        eos_id: document separator id for the doc-level split (no-leakage, TRAIN-03).
        fixed_batch: ``(xb, yb)`` reused every step — the overfit gate (TRAIN-05).
        scaler: an injectable GradScaler-shaped object (the AMP-ordering spy hook); defaults to a
            real ``GradScaler`` tied to ``runtime.amp``.
        resume_from: checkpoint path to resume from (restores RNG state — never re-seed).
        checkpoint_path: where to save ``latest.pt`` at the end of this call (resume seam).
        log_path: CSV curve path (append-only, header-once across restarts).
        max_steps_override: stop after this many optimizer steps (the "kill" in the resume test).
        eval_interval: log/eval every N steps (1 so the curve is row-for-row reproducible).
        return_final_loss: when True, return the final step's training loss.

    Returns:
        The final training loss when ``return_final_loss`` else ``None``.
    """
    runtime = runtime_config if runtime_config is not None else RuntimeConfig()
    model_cfg = model_config if model_config is not None else ModelConfig()
    if model is None:
        # Local import avoids a package import cycle (training -> model -> ...).
        from personacore.model import BigramLanguageModel

        # When the caller does NOT supply a model (the synthetic AMP/grad-accum unit tests and
        # the train_bigram script), seed the embedding init from train_config.seed so the
        # default weights are reproducible across independent train() calls — this is what makes
        # the grad-accum-vs-big-batch comparison (two separate train() runs) start from identical
        # weights. Callers that need cross-run trajectory control pass an explicit pre-seeded model.
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(train_config.seed)
            model = BigramLanguageModel(vocab_size=model_cfg.vocab_size)
    model.to(runtime.device)

    optimizer = torch.optim.AdamW(
        model.parameters(), lr=train_config.lr, weight_decay=train_config.weight_decay
    )
    scheduler = build_scheduler(optimizer, train_config)
    if scaler is None:
        scaler = GradScaler(device=runtime.device.split(":")[0], enabled=runtime.amp)

    # --- Data source (three modes) ---
    #  1. fixed_batch  -> overfit gate: ONE batch reused every step (TRAIN-05).
    #  2. corpus_path  -> the committed-fixture doc-split path (the real harness, TRAIN-03/04).
    #  3. neither      -> a deterministic SYNTHETIC batch (the AMP-ordering + grad-accum unit
    #     tests, TRAIN-01/02). The full effective batch (batch_size × grad_accum_steps samples)
    #     is generated once from a fixed generator, then SLICED into micro-batches — so
    #     grad_accum_steps=N over micro-batches is provably the SAME data as one N×-bigger batch,
    #     which is exactly what test_grad_accum_equivalent_to_big_batch asserts.
    if fixed_batch is not None:
        fx, fy = fixed_batch
        fx, fy = fx.to(runtime.device), fy.to(runtime.device)
        train_ids = val_ids = None

        def batch_fn(_micro):
            return fx, fy
    elif corpus_path is not None:
        train_ids, val_ids = load_split(corpus_path, eos_id=eos_id)

        def batch_fn(_micro):
            return get_batch(
                train_ids, train_config.batch_size, model_cfg.block_size, runtime.device
            )
    else:
        train_ids = val_ids = None
        _accum = max(1, train_config.grad_accum_steps)
        _bs = train_config.batch_size
        _T = 16  # short synthetic context; only the step mechanics are under test here
        _gen = torch.Generator(device="cpu").manual_seed(0)
        _full_x = torch.randint(0, model_cfg.vocab_size, (_bs * _accum, _T), generator=_gen)
        _full_y = torch.randint(0, model_cfg.vocab_size, (_bs * _accum, _T), generator=_gen)
        _full_x, _full_y = _full_x.to(runtime.device), _full_y.to(runtime.device)

        def batch_fn(micro):
            sl = slice(micro * _bs, (micro + 1) * _bs)
            return _full_x[sl], _full_y[sl]

    # --- Resume: restore full state + RNG, continue the step counter (NEVER re-seed) ---
    start_step = 0
    if resume_from is not None:
        ckpt = load_checkpoint(resume_from, model=model, optimizer=optimizer, scheduler=scheduler)
        start_step = ckpt["step"]

    csv = CSVLogger(log_path, fieldnames=CSV_FIELDNAMES) if log_path is not None else None

    target_steps = max_steps_override if max_steps_override is not None else train_config.max_steps
    final_loss = None
    # tokens/step is the effective-batch token count; derive CUMULATIVE tokens from the absolute
    # step (not a per-call accumulator) so the logged curve is continuous across a kill+resume
    # — resetting an accumulator to 0 on resume would discontinuity the column (Pitfall 4).
    tokens_per_step = train_config.batch_size * max(1, train_config.grad_accum_steps)
    step = start_step
    try:
        while step < target_steps:
            train_loss = _optimizer_step(
                model, optimizer, scheduler, scaler, train_config, runtime, batch_fn
            )
            final_loss = train_loss
            step += 1
            tokens = step * tokens_per_step

            if csv is not None and (step % eval_interval == 0):
                if val_ids is not None:
                    val_loss = estimate_loss(
                        model, val_ids, train_config, model_cfg, runtime.device
                    )
                else:
                    val_loss = train_loss
                csv.log(
                    step=step,
                    train_loss=train_loss,
                    val_loss=val_loss,
                    lr=scheduler.get_last_lr()[0],
                    tokens=tokens,
                    # Logical (step-derived) clock, NOT wall time: the resume-curve contract
                    # (TRAIN-04) requires the CSV to reproduce row-for-row across a kill+resume,
                    # which a real timestamp cannot. The portfolio loss/lr curves only need a
                    # monotonic x-axis; deterministic step count gives one. (Real elapsed-time
                    # telemetry, if ever wanted, belongs in the Phase-8 demo, not this gate.)
                    wall_clock=step,
                )
    finally:
        if csv is not None:
            csv.close()

    if checkpoint_path is not None:
        save_checkpoint(
            checkpoint_path,
            model=model,
            optimizer=optimizer,
            scheduler=scheduler,
            step=step,
            model_config=model_cfg,
            train_config=train_config,
            git_sha=git_sha(),
            val_loss=final_loss,
        )

    return final_loss if return_final_loss else None
