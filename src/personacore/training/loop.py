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

D-03/D-04/TRAIN-06: loss is always assembled via ``assemble_loss(base, penalties)`` — the M2 EWC
seam is now LIVE (EWC-02): ``train(..., penalty_fn=...)`` evaluates the penalty per micro-batch
and it joins ``base_loss`` BEFORE the ``/accum`` divide; ``penalty_fn=None`` (the default) keeps
the M1 identity bit-for-bit (pinned against tests/fixtures/golden_trajectory_v1.json), and
``checkpoint_extra`` splats fisher/theta_star into every in-loop ``save_checkpoint`` (Open Q1).
D-11: the minimal ``sample`` lives
HERE as a free function (not on the model) so Phase-6's richer ``generate`` supersedes it without a
model rewrite. The loop NEVER calls ``torch.cuda.*`` — ``RuntimeConfig`` is the single device/AMP
source of truth (config.py:44-61).
"""

import os
import random

import numpy as np
import torch
from torch.amp import GradScaler

from personacore.checkpoint import load_checkpoint, save_checkpoint
from personacore.config import ModelConfig, RuntimeConfig
from personacore.logging import CSVLogger
from personacore.provenance import git_sha

from .data import get_batch, get_batch_memmap, get_batch_memmap_masked, load_split
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


def _is_bin_path(src):
    """True iff ``src`` names a memmap ``.bin`` PATH (the full-corpus source) vs an in-RAM array.

    The memmap data branch (Seam 1) carries the val source as a filesystem PATH (str / os.PathLike)
    instead of a numpy array; ``estimate_loss`` (Seam 2) uses this to pick ``get_batch_memmap``.
    """
    return isinstance(src, (str, os.PathLike))


@torch.no_grad()
def estimate_loss(model, val_ids, train_cfg, model_cfg, device, iters=20, mask_bin=None):
    """Mean validation CE under ``model.eval()`` + ``no_grad``, restoring ``model.train()``.

    Snapshots and restores the global RNG around the val draws so the periodic eval does NOT
    perturb the train trajectory's random stream (the resume-equality contract, TRAIN-04).
    ``iters`` is clamped so a tiny fixture (few val windows) still produces a stable estimate.

    ``mask_bin`` (Phase 12 seam): aligned ``uint8`` mask ``.bin`` PATH for the memmap val
    source; when set, val draws route via ``get_batch_memmap_masked`` so the estimate is
    assistant-token masked CE (``-100`` targets ignored by ``F.cross_entropy``). None
    reproduces v1.0 bit-for-bit.
    """
    rng = _rng_state()
    model.eval()
    block_size = model_cfg.block_size
    # Seam 2 — memmap path support: when val_ids is a .bin PATH (full-corpus source) draw via
    # get_batch_memmap; otherwise it is an in-RAM array drawn via get_batch (the fixture path).
    # The RNG snapshot/restore wrapper above/below is UNCHANGED — the resume-equality contract.
    is_bin = _is_bin_path(val_ids)
    if is_bin:
        # The full corpus is always >> block_size; no window-shrink needed for the memmap path.
        eff_block = block_size
    else:
        # A bounded fixture's val split may be shorter than block_size; shrink the window so
        # get_batch's start bound (len(arr) - block_size - 1) stays positive.
        eff_block = min(block_size, max(1, len(val_ids) - 2))
    losses = []
    for _ in range(iters):
        if is_bin:
            if mask_bin is not None:
                xb, yb = get_batch_memmap_masked(
                    val_ids, mask_bin, train_cfg.batch_size, eff_block, device
                )
            else:
                xb, yb = get_batch_memmap(val_ids, train_cfg.batch_size, eff_block, device)
        else:
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


def _optimizer_step(
    model,
    optimizer,
    scheduler,
    scaler,
    train_cfg,
    runtime,
    batch_fn,
    penalty_fn=None,
    replay_fn=None,
):
    """Run ONE optimizer step with the load-bearing AMP+accum+clip ordering (TRAIN-02).

    ``batch_fn(micro)`` yields ``(xb, yb)`` for each micro-batch. Order is mandatory:
    scale->backward × grad_accum_steps -> unscale_ (once) -> clip -> step -> update -> scheduler.
    Returns the (unscaled, accumulation-corrected) training loss for the step.

    ``penalty_fn`` (the M2 EWC seam, EWC-02) is evaluated per micro-batch and joins
    ``base_loss`` via ``assemble_loss`` BEFORE the ``/accum`` divide — params are constant
    across the accumulation window, so the divided contributions sum to exactly ONE full
    penalty per optimizer step (Pitfall 5). ``None`` keeps the M1 identity bit-for-bit.

    ``replay_fn`` (the Phase-21 replay seam, D-10/D-25) runs ONCE per optimizer step, AFTER the
    per-micro-step accumulation loop and BEFORE ``unscale_``, accumulating into the same
    gradient buffer. It is structurally OUTSIDE the per-record loop above — see :func:`train`
    for what that placement does and does not claim. ``None`` is bit-for-bit inert: no new line
    executes on the default path.
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
            penalties = (penalty_fn(model),) if penalty_fn is not None else ()
            total = assemble_loss(base_loss, penalties)  # identity when no penalty (D-04)
            loss = total / accum  # scale so accumulated grads average across micro-batches
        scaler.scale(loss).backward()
        summed += float(base_loss.item())
    if replay_fn is not None:
        replay_fn(model, scaler)  # D-25: its OWN pass per lot, outside the per-record loop
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
    train_bin=None,
    val_bin=None,
    train_mask_bin=None,
    val_mask_bin=None,
    replay_bin=None,
    replay_mask_bin=None,
    replay_windows=None,
    eos_id=8184,
    fixed_batch=None,
    scaler=None,
    resume_from=None,
    checkpoint_path=None,
    best_checkpoint_path=None,
    log_path=None,
    max_steps_override=None,
    eval_interval=1,
    checkpoint_interval=None,
    sample_interval=None,
    sample_prompt=None,
    tokenizer=None,
    sample_max_new_tokens=64,
    penalty_fn=None,
    checkpoint_extra=None,
    extra_eval_fns=None,
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
        train_bin: Seam 1 — full-corpus ``uint16`` train ``.bin`` PATH; when set, ``batch_fn``
            draws via ``get_batch_memmap`` (the long-run data source). Mutually exclusive with
            ``fixed_batch``/``corpus_path``.
        val_bin: Seam 1/2 — val ``.bin`` PATH carried as ``val_ids`` so ``estimate_loss`` draws
            via ``get_batch_memmap`` on the memmap path.
        train_mask_bin: Phase-12 mask seam — aligned ``uint8`` mask ``.bin`` PATH for
            ``train_bin``; when set, ``batch_fn`` draws via ``get_batch_memmap_masked`` so
            user-turn targets carry ``-100`` (assistant-token loss masking, TUNE-01).
            Requires ``train_bin``; None reproduces v1.0 bit-for-bit.
        val_mask_bin: Phase-12 mask seam — aligned mask PATH for ``val_bin``; when set,
            ``estimate_loss``'s val draws route via ``get_batch_memmap_masked`` so the
            in-loop ``val_loss`` measures assistant-token masked CE. USER LOCK 3 — this
            SHIPS because the in-loop val_loss gates best.pt selection, and best is
            selected FOR assistant-token dialogue capability: unmasked CE would partially
            reward modeling user turns and make "best" mean something the report never
            measures. (Gates elsewhere use the deterministic ``masked_perplexity`` sweep,
            never in-loop val_loss.) None reproduces v1.0 bit-for-bit.
        replay_bin: Phase-21 replay seam (D-10/D-25) — PersonaChat token ``.bin`` PATH that
            replay windows are drawn from at TRAIN time. Requires ``replay_mask_bin`` and
            ``replay_windows``. All three None reproduces v1.0 bit-for-bit.
        replay_mask_bin: aligned ``uint8`` mask PATH for ``replay_bin``.
        replay_windows: how many ``block_size`` windows of replay to draw per OPTIMIZER STEP.
            The caller computes this from PUBLIC quantities only —
            ``teach_persona.replay_window_budget(n_facts) // block_size``, i.e.
            ``REPLAY_WINDOWS_PER_FACT * n_facts`` (D-11/D-24). This loop never derives it from
            the data.

            **What this seam DOES claim.** It lets the teaching bin hold FACTS ONLY, so
            ``grad_accum_steps = n_facts`` is LITERALLY true with no roadmap amendment (D-10).
            Replay is drawn and accumulated in its OWN pass per LOT, structurally outside the
            per-record accumulation loop, so Phase 22's clipping seam has an obvious place to
            NOT apply and the public term stays provably independent of any private record
            (D-25). The draw reuses the existing, already-validated
            ``get_batch_memmap_masked`` — reuse of a proven path, not new infrastructure — and
            is micro-batched by ceil division at the loop's own ``batch_size`` so
            ``4 * 64 = 256`` windows per lot at n=64 need not fit one MPS allocation. Each
            micro-batch is weighted by its ACTUAL window count over ``replay_windows``, so the
            ragged final micro-batch contributes exactly one full replay MEAN per step rather
            than over-weighting a short tail.

            **What it does NOT claim.** Phase 21 delivers the STRUCTURAL SEPARATION ONLY. The
            ``clip_grad_norm_`` call in :func:`_optimizer_step` still clips the AVERAGED
            gradient, replay included. Per-record clipping and a genuinely un-clipped replay
            term are DPSGD-01/DPSGD-04, Phase 22. Do not read an un-clipped public-gradient
            guarantee into this seam; it is not delivered here.

            **The overlap is a RECORDED COST, not an accident.** This is DPSGD-01's "new
            additive gradient-side seam", pulled into Phase 21 deliberately by D-10.

            **D-10's two rejected alternatives, for the record.** (1) An in-bin
            sentinel-tagged single un-clipped micro-step — ``grad_accum_steps = n_facts + 1``,
            which would have needed a DATED AMENDMENT to SC2 rather than satisfying it.
            (2) Replay windows as N separate un-clipped micro-steps — rejected because it made
            ``grad_accum_steps`` data-dependent, the exact quantity SC2 exists to pin. **D-25
            reopened (2)**: under D-24 the replay window count is ``4 * n_facts``, fully public,
            so that rejection's premise had EXPIRED. The separate-pass shape was then chosen on
            its own merits rather than inherited from a reason that no longer held.
        eos_id: document separator id for the doc-level split (no-leakage, TRAIN-03).
        fixed_batch: ``(xb, yb)`` reused every step — the overfit gate (TRAIN-05).
        scaler: an injectable GradScaler-shaped object (the AMP-ordering spy hook); defaults to a
            real ``GradScaler`` tied to ``runtime.amp``.
        resume_from: checkpoint path to resume from (restores RNG state — never re-seed; also
            restores the ``best_val_loss`` running minimum when the checkpoint carries it, so
            best.pt cannot regress across a kill+resume).
        checkpoint_path: where to save ``latest.pt`` (end-of-call always; also in-loop every
            ``checkpoint_interval`` steps when set — Seam 4, kill-survivability).
        best_checkpoint_path: Seam 3 (D-08) — where to save ``best.pt`` whenever a new LOWEST
            val loss is observed; the shipped checkpoint is the best-val one, not the final step.
            The running minimum is persisted as ``best_val_loss`` in every saved checkpoint and
            restored on ``resume_from``, so the contract holds across multi-session runs.
        log_path: CSV curve path (append-only, header-once across restarts).
        max_steps_override: stop after this many optimizer steps (the "kill" in the resume test).
        eval_interval: log/eval every N steps (1 so the curve is row-for-row reproducible).
        checkpoint_interval: Seam 4 — when set with ``checkpoint_path``, save ``latest.pt``
            in-loop every K steps so a kill loses at most K steps of work (Pitfall 5).
        sample_interval: Seam 4 — when set, every S steps run the minimal ``sample()`` and print
            the decoded text (a qualitative coherence check, D-06). Requires ``tokenizer``.
        sample_prompt: optional list[int] seed ids for the periodic sample; default ``[eos_id]``.
        tokenizer: a frozen tokenizer with ``.decode(list[int]) -> str`` for the sample print.
        sample_max_new_tokens: number of tokens the periodic sample extends.
        penalty_fn: callable ``(model) -> scalar tensor`` added to ``base_loss`` via
            ``assemble_loss`` per micro-batch (the M2 EWC seam, EWC-02); None reproduces
            v1.0 bit-for-bit.
        checkpoint_extra: dict splatted into every in-loop ``save_checkpoint`` call (the
            M2 fisher/theta_star carry, RESEARCH Open Q1); None adds no caller keys (the
            loop itself always records ``best_val_loss`` — Seam 3 continuity).
        extra_eval_fns: Phase-12 telemetry seam — ``dict[str, Callable[[torch.nn.Module],
            float]]``; each fn runs once per eval-logging event and its value is logged as
            one CSV column per key (retention_ppl / dialog_ppl / ewc_penalty / role norms
            all ride this seam). Per-run fieldnames are ``CSV_FIELDNAMES +
            sorted(extra_eval_fns)`` computed at ``CSVLogger`` construction — the module
            constant is never mutated, and appending new columns to an existing CSV raises
            (DictWriter unknown-key enforcement). The fns run inside a
            ``_rng_state()``/``_restore_rng`` snapshot and ``model.train()`` is restored
            afterward (``perplexity()`` leaves the model in eval mode — Pitfall 4). None
            reproduces v1.0 bit-for-bit.
        return_final_loss: when True, return the final step's training loss.

    Returns:
        The final training loss when ``return_final_loss`` else ``None``.
    """
    if train_mask_bin is not None and train_bin is None:
        raise ValueError(
            "train_mask_bin requires train_bin: the mask .bin is element-aligned to the "
            "token .bin — set both (or neither) on the memmap data branch."
        )
    if val_mask_bin is not None and (train_bin is None or not _is_bin_path(val_bin)):
        raise ValueError(
            "val_mask_bin requires the memmap data branch: set train_bin and val_bin "
            "(a memmap .bin PATH) — estimate_loss only honors the mask when the val "
            "source is a .bin path routed through get_batch_memmap_masked; any other "
            "val source would silently drop the mask (USER LOCK 3)."
        )
    _replay = {
        "replay_bin": replay_bin,
        "replay_mask_bin": replay_mask_bin,
        "replay_windows": replay_windows,
    }
    _missing = sorted(name for name, value in _replay.items() if value is None)
    if _missing and len(_missing) != len(_replay):
        raise ValueError(
            f"the Phase-21 replay seam needs all three of {sorted(_replay)} or none of them — "
            f"missing {_missing}. The token and mask .bin are element-aligned, and "
            "replay_windows is the PUBLIC per-step budget (D-11/D-24: "
            "REPLAY_WINDOWS_PER_FACT * n_facts); this loop never derives it from the data, so "
            "it cannot be defaulted."
        )
    if replay_windows is not None and (
        isinstance(replay_windows, bool)
        or not (isinstance(replay_windows, int) and replay_windows > 0)
    ):
        raise ValueError(
            f"replay_windows={replay_windows!r} — the replay budget is a positive int count of "
            "block_size windows drawn per OPTIMIZER STEP (D-24 is window-quantized precisely so "
            "this is a whole number and needs no truncation step)."
        )
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
    elif train_bin is not None:
        # Seam 1 — memmap data branch (the full-corpus long-run source). Mirrors the corpus_path
        # branch exactly, swapping load_split's in-RAM arrays for the train.bin/val.bin PATHS:
        # batch_fn draws from train_bin via get_batch_memmap, and val_ids carries the val.bin PATH
        # (a str/PathLike, NOT an array) so estimate_loss (Seam 2) routes to get_batch_memmap.
        train_ids, val_ids = train_bin, val_bin

        if train_mask_bin is not None:
            # Phase-12 mask seam: identical draw, but user-turn targets carry -100 so the
            # CE scores assistant tokens only (TUNE-01; -100 semantics live in data.py).
            def batch_fn(_micro):
                return get_batch_memmap_masked(
                    train_bin,
                    train_mask_bin,
                    train_config.batch_size,
                    model_cfg.block_size,
                    runtime.device,
                )
        else:

            def batch_fn(_micro):
                return get_batch_memmap(
                    train_bin, train_config.batch_size, model_cfg.block_size, runtime.device
                )
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

    # --- Phase-21 replay seam (D-10/D-25): its OWN pass per lot, outside the per-record loop ---
    replay_fn = None
    if replay_windows is not None:

        def replay_fn(model, scaler):
            drawn = 0
            while drawn < replay_windows:
                # Ceil division by iteration: the last micro-batch is the ragged remainder, so
                # the total drawn is EXACTLY replay_windows and never a rounded-up overdraw.
                micro = min(train_config.batch_size, replay_windows - drawn)
                xb, yb = get_batch_memmap_masked(
                    replay_bin, replay_mask_bin, micro, model_cfg.block_size, runtime.device
                )
                with runtime.autocast():
                    _, replay_loss = model(xb, yb)
                    # Weight by ACTUAL windows / total, so the ragged tail is not over-weighted
                    # and the pass contributes exactly ONE full replay mean per optimizer step.
                    loss = replay_loss * (micro / replay_windows)
                scaler.scale(loss).backward()
                drawn += micro

    # --- Resume: restore full state + RNG, continue the step counter (NEVER re-seed) ---
    start_step = 0
    resumed_best_val_loss = None
    if resume_from is not None:
        ckpt = load_checkpoint(
            resume_from, model=model, optimizer=optimizer, scheduler=scheduler, scaler=scaler
        )
        start_step = ckpt["step"]
        # Seam 3 (D-08) continuity: seed the best-val running minimum from the checkpoint so
        # the first post-resume eval cannot overwrite best.pt with a WORSE val loss than the
        # pre-kill best. Pre-fix checkpoints lack the key — .get() falls back to None and the
        # fresh-run float("inf") below, so old checkpoints still resume (open-dict contract).
        resumed_best_val_loss = ckpt.get("best_val_loss")

    # Phase-12 telemetry seam: per-run fieldnames — the module constant is NEVER mutated.
    # A pre-existing CSV with the old header makes CSVLogger's DictWriter raise on the new
    # keys (the enforcement against silently appending columns to an old file, T-12-02).
    fieldnames = CSV_FIELDNAMES + sorted(extra_eval_fns) if extra_eval_fns else CSV_FIELDNAMES
    csv = CSVLogger(log_path, fieldnames=fieldnames) if log_path is not None else None

    target_steps = max_steps_override if max_steps_override is not None else train_config.max_steps
    final_loss = None
    # Seam 3 (D-08) — running minimum that gates the best.pt save; restored across a
    # kill+resume (see the resume block above) so best.pt can never silently regress.
    best_val_loss = resumed_best_val_loss if resumed_best_val_loss is not None else float("inf")
    sample_ids = sample_prompt if sample_prompt is not None else [eos_id]
    # tokens/step is the effective-batch token count; derive CUMULATIVE tokens from the absolute
    # step (not a per-call accumulator) so the logged curve is continuous across a kill+resume
    # — resetting an accumulator to 0 on resume would discontinuity the column (Pitfall 4).
    tokens_per_step = (
        train_config.batch_size * max(1, train_config.grad_accum_steps) * model_cfg.block_size
    )
    step = start_step
    try:
        while step < target_steps:
            train_loss = _optimizer_step(
                model,
                optimizer,
                scheduler,
                scaler,
                train_config,
                runtime,
                batch_fn,
                penalty_fn,
                replay_fn,
            )
            final_loss = train_loss
            step += 1
            tokens = step * tokens_per_step

            if csv is not None and (step % eval_interval == 0):
                if val_ids is not None:
                    # The mask_bin kwarg is only passed when set, so the v1.0 call-site
                    # signature is byte-identical on the default path (an estimate_loss
                    # stub without the kwarg — e.g. tests' fakes — still works).
                    if val_mask_bin is not None:
                        val_loss = estimate_loss(
                            model,
                            val_ids,
                            train_config,
                            model_cfg,
                            runtime.device,
                            mask_bin=val_mask_bin,
                        )
                    else:
                        val_loss = estimate_loss(
                            model, val_ids, train_config, model_cfg, runtime.device
                        )
                else:
                    val_loss = train_loss
                # Phase-12 telemetry seam: run each extra fn once per eval-logging event,
                # one CSV column per key. The RNG snapshot keeps a non-pure fn from
                # perturbing the train trajectory (resume-equality, TRAIN-04), and the
                # model.train() restore undoes perplexity()-style fns that call
                # model.eval() and never restore (Pitfall 4).
                extras = {}
                if extra_eval_fns:
                    fn_rng = _rng_state()
                    for key in sorted(extra_eval_fns):
                        extras[key] = extra_eval_fns[key](model)
                    model.train()
                    _restore_rng(fn_rng)
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
                    **extras,
                )

                # Seam 3 — best-val tracking (D-08): ship the LOWEST-val checkpoint, not the
                # final step's. Reuses save_checkpoint VERBATIM (the end-of-call save args) — the
                # checkpoint format already carries val_loss=, so best.pt needs no format change.
                if best_checkpoint_path is not None and val_loss < best_val_loss:
                    best_val_loss = val_loss
                    save_checkpoint(
                        best_checkpoint_path,
                        model=model,
                        optimizer=optimizer,
                        scheduler=scheduler,
                        scaler=scaler,
                        step=step,
                        model_config=model_cfg,
                        train_config=train_config,
                        git_sha=git_sha(),
                        val_loss=val_loss,
                        best_val_loss=best_val_loss,  # Seam 3 continuity across kill+resume.
                        **(checkpoint_extra or {}),
                    )

            # Seam 4a — periodic latest.pt (kill-survivability, Pitfall 5): the same end-of-call
            # save, also fired in-loop every checkpoint_interval steps so a kill loses <= K steps.
            if (
                checkpoint_path is not None
                and checkpoint_interval
                and step % checkpoint_interval == 0
            ):
                save_checkpoint(
                    checkpoint_path,
                    model=model,
                    optimizer=optimizer,
                    scheduler=scheduler,
                    scaler=scaler,
                    step=step,
                    model_config=model_cfg,
                    train_config=train_config,
                    git_sha=git_sha(),
                    val_loss=final_loss,
                    best_val_loss=best_val_loss,  # Seam 3 continuity across kill+resume.
                    **(checkpoint_extra or {}),
                )

            # Seam 4b — periodic qualitative sample print (D-06 coherence check): every S steps,
            # extend a seed via the minimal sample() and decode it. NO Phase-6 generate().
            if sample_interval and tokenizer is not None and step % sample_interval == 0:
                seed = torch.tensor([sample_ids], dtype=torch.long, device=runtime.device)
                out = sample(model, seed, max_new_tokens=sample_max_new_tokens)[0].tolist()
                print(f"[sample step={step}] {tokenizer.decode(out)!r}")
    finally:
        if csv is not None:
            csv.close()

    if checkpoint_path is not None:
        save_checkpoint(
            checkpoint_path,
            model=model,
            optimizer=optimizer,
            scheduler=scheduler,
            scaler=scaler,
            step=step,
            model_config=model_cfg,
            train_config=train_config,
            git_sha=git_sha(),
            val_loss=final_loss,
            best_val_loss=best_val_loss,  # Seam 3 continuity across kill+resume.
            **(checkpoint_extra or {}),
        )

    return final_loss if return_final_loss else None
