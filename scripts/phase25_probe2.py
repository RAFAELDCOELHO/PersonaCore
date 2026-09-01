"""D-04's PROBE 2, RE-RUN AT BOTH CAPACITIES — committed as a PREDICTION, before any sweep point.

WHAT THIS MEASURES
------------------
How far the **sigma=0 DP path** differs from the **seam-off path** (``dp_fn`` absent at
``personacore.training.loop.train``), per trainable LoRA tensor, at ``dp_n8`` AND ``dp_n64``.

**n=64 HAS NEVER BEEN PROBED.** Phase 23 probed n=8 only, and it probed a DIFFERENT SHAPE — a
single-step GRADIENT comparison (72/72 LoRA tensors agreeing to ``2.178e-07`` relative). This
module compares TRAINED ADAPTERS after the full ``teach_persona.MAX_STEPS`` budget, so both
columns are first measurements of their own quantity and the n=8 column is NOT a repetition of
Phase 23's number. That difference is recorded in the artifact rather than left for a reader to
infer, because a 200-step AdamW trajectory compounds per-step float32 re-summation noise and a
larger figure here is the EXPECTED reading, not a regression.

WHY IT IS WRITTEN BEFORE ANY POINT EXISTS
-----------------------------------------
CTRL-02's own body already records that the control is not bit-identical to the seam-off path and
that chasing that identity would be a mistake. A record written AFTER someone notices the
difference is a rationalisation; written BEFORE, it is a prediction. D-04's armed tripwire
(``tests/test_phase25_prereg.py``) FAILS if any later plan asserts bit-identity between the two
paths, and this record is what the tripwire's failure message points at.

D-06's LINE, DRAWN STRUCTURALLY
-------------------------------
Only the ``dp_fn=None`` COMPARATOR is renamed. The sigma=0 control point keeps arm identity
``dp_n8`` / ``dp_n64`` — it IS a DP sweep point under CTRL-02 — and is separated from the sweep by
**prefix only**, which is what keeps D-01's bit-level reproduction against
``results/phase23_sigma_zero.json`` reachable. Both facts are recorded as structural fields
(``control_arm_identity`` / ``seam_off_comparator_arm``) rather than as prose.

WHY THIS IS A SEPARATE MODULE FROM ``scripts/phase25_calibrate.py``
-------------------------------------------------------------------
Plan 25-13 asks for the probe to EXTEND ``scripts/phase25_calibrate.py``. **The tree refuses that
edit, and the refusal was measured before any GPU second was spent.** Both
``results/phase25_clip_calibration.json`` and ``results/phase25_adversarial_throughput.json`` pin
``scripts/phase25_calibrate.py``'s sha256 in their provenance block, and
``tests/test_phase25_calibrate.py::test_the_calibration_provenance_matches_the_live_module_bytes``
recomputes it from bytes. One edited byte reddens both records. Their documented emitter re-derives
them only by RE-MEASURING (``run_clip_calibration`` / ``run_throughput_probe``), which would
re-derive ``clip_norm_candidate`` — the source of ``mitigation_budget.CLIP_NORM =
1.3254119157791138``, a literal plan 25-12 pinned and plan 25-13 must leave byte-unchanged. So the
sanctioned re-emit route would put a pinned constant's provenance at risk to buy nothing. This
module therefore IMPORTS ``phase25_calibrate``'s prefix and helpers instead of editing it, and
``scripts/phase25_calibrate.py`` stays byte-identical.

CPU-SAFE AT IMPORT. ``torch``, ``teach_persona`` and every model module are imported INSIDE the
functions that need them — ``phase25_calibrate``'s own discipline — so the test battery reads this
record without touching a GPU.
"""

import argparse
import datetime
import json
import pathlib
import platform
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import mitigation_budget  # noqa: E402  (needs the sys.path insert; scripts/ is not a package)
import phase25_calibrate as cal  # noqa: E402  (CALIBRATION_PREFIX + the shared helpers)
import phase25_run  # noqa: E402  (atomic_write_json — the driver's own writer, reused)

from personacore.provenance import git_sha  # noqa: E402

_prove = cal._prove
sha256_of = cal.sha256_of

RECORD_PATH = _ROOT / "results" / "phase25_probe2_tensors.json"
MODULE_PATH = pathlib.Path(__file__).resolve()


# =================================================================================================
# ===== (a) THE PROBE'S OWN PINS — every one a NAME at the call site, never a literal =====
# =================================================================================================

PROBE_CAPACITIES = ("dp_n8", "dp_n64")
"""The two capacities D-04 requires. Order is the record's column order and the run order."""

PROBE_SEED = 1337
"""``phase23_run.SEED_LADDER[0]``'s value, asserted against that symbol at run time rather than
trusted. Both paths at one capacity run at the SAME seed — that is what makes the residual a
property of the seam and not of two initialisations."""

CONTROL_SIGMA = 0.0
"""The control's noise multiplier. At sigma=0 the DP draw site's ``std = sigma * C`` is 0.0, so
the ONLY thing the seam can still do to the gradient is clip — which is why C must not bind."""

SEAM_OFF_COMPARATOR_ARM = "seam_off_comparator"
"""D-06's rename, and it applies to the COMPARATOR ONLY.

The sigma=0 control keeps ``dp_n8`` / ``dp_n64``. This name scopes the comparator's csv,
checkpoint and adapter — declared difference #2's own reason, *"two arms sharing a path would
overwrite each other's evidence"*. It is deliberately NOT a member of ``teach_persona.DP_ARMS``
and deliberately NOT a member of ``teach_persona.ARMS``: the comparator has no ``arm_spec`` and
cannot have one, because it is the DP arm's data wiring reached with the DP seam absent."""


def comparator_arm(capacity):
    """``dp_n8`` -> ``seam_off_comparator_n8``. DERIVED, so the two names cannot drift apart.

    ``arm_outputs`` does not validate its ``arm`` argument against ``ARMS`` — it formats paths —
    which is exactly how ``phase23_matched_prereg.matched_arm(seed)`` already scopes a comparator
    that is not a member arm either. Same register, this phase's name.
    """
    return f"{SEAM_OFF_COMPARATOR_ARM}_{capacity.removeprefix('dp_')}"


# The reference figure, quoted from Phase 23 and re-read LIVE from the module that owns it before
# it is written into the record. A retyped reference is a second source for one fact.
PHASE23_REFERENCE_FIGURE = "2.178e-07"
PHASE23_REFERENCE_SYMBOL = "phase23_matched_prereg.DP_FN_BRANCH_DISPOSITIONS"

DECLARED_DIFFERENCES_SOURCE = "results/phase23_matched_control.json"
DECLARED_DIFFERENCES_EXPECTED = 4

AGREEMENT_BOUND_GOVERNS = (
    "BOUNDED DISAGREEMENT, NEVER EQUALITY. `agreement_bound` is the LARGEST per-tensor relative "
    "difference OBSERVED between the sigma=0 DP path and the seam-off path at this capacity, and "
    "it is recorded as a PREDICTION rather than discovered later as an anomaly. The disagreement "
    "is EXPECTED FLOATING-POINT NON-ASSOCIATIVITY: the DP seam accumulates undivided per-record "
    "contributions and divides by N once at finalize, while the seam-off path divides each "
    "micro-step loss by the accumulation count and sums; the two orderings are mathematically "
    "identical and numerically are not, and 200 AdamW steps compound the residual. CTRL-02's own "
    "body already records that the control is not bit-identical to the seam-off path and that "
    "chasing that identity would be a mistake, and Phase 23's declared difference #3 states that "
    "'sigma=0 is not the control computation with a zero added to it' is TRUE OF THE CODE PATH "
    "and FALSE OF THE ARITHMETIC. The correct downstream assertion is therefore "
    "bounded disagreement, never equality: a later plan that asserts torch.equal, allclose or a "
    "digest match between these two adapters would overwrite a MEASURED property with a claim the "
    "measurement does not support, and the next reader to see the two paths disagree would read "
    "a real property as a regression. A recorded bound of exactly 0.0 is itself a bit-identity "
    "claim and is refused by tests/test_phase25_probe2.py."
)

CONTROL_ARM_IDENTITY_WHY = (
    "The sigma=0 control POINT keeps arm identity dp_n8 / dp_n64 and is separated from the sweep "
    "by PREFIX ONLY. It is a real DP sweep point under CTRL-02 (D-20 puts sigma=0 inside "
    "SWEEP_POINTS = 16 at slot 1), and renaming it would break D-01's bit-level reproduction "
    "against results/phase23_sigma_zero.json, whose taught reading 790/1008 is the reproduction "
    "target. Only the dp_fn=None COMPARATOR is renamed (D-06)."
)


# =================================================================================================
# ===== (b) THE READS — EVERY ONE VALIDATED BEFORE A SINGLE GPU SECOND IS SPENT =====
# =================================================================================================


def read_declared_differences():
    """Phase 23's FOUR declared differences, read live and refused at any other length.

    Plan 25-12 lost a completed 45-minute GPU run to a ``KeyError`` raised in the assembly step
    AFTERWARDS. Every read this record depends on therefore happens HERE, before
    :func:`run_probe` trains anything.

    If Phase 23's record ever grows a fifth entry, this refuses rather than silently dropping it —
    the whole point of importing the list by path and digest instead of retyping it.
    """
    path = _ROOT / DECLARED_DIFFERENCES_SOURCE
    _prove(path.exists(), f"{DECLARED_DIFFERENCES_SOURCE} does not exist — this record imports it")
    blob = json.loads(path.read_text(encoding="utf-8"))
    _prove(
        "declared_differences" in blob,
        f"{DECLARED_DIFFERENCES_SOURCE} carries no `declared_differences` key. It is the record "
        "that OWNS them; a missing key means this probe would embed nothing and claim four",
    )
    entries = blob["declared_differences"]
    _prove(
        isinstance(entries, list) and len(entries) == DECLARED_DIFFERENCES_EXPECTED,
        f"{DECLARED_DIFFERENCES_SOURCE} carries {len(entries)} declared difference(s) against the "
        f"expected {DECLARED_DIFFERENCES_EXPECTED}. A fifth must FAIL this write rather than be "
        "silently dropped: the list travels here by import precisely so it cannot drift",
    )
    for index, entry in enumerate(entries):
        _prove(
            {"difference", "disposition", "evidence", "matched_quantity"} <= set(entry),
            f"declared difference #{index + 1} is missing one of the four fields the record "
            f"carries: {sorted(entry)}",
        )
    return entries, sha256_of(path)


def read_control_diagnostic():
    """``results/phase23_sigma_zero.json``'s mechanism block, validated field by field.

    NOTE ON SHAPE, recorded because 25-12 was bitten by assuming otherwise: this record has NO
    top-level ``arm`` key. The five fields below are the ones that exist, and each is read by name.
    """
    path = _ROOT / "results" / "phase23_sigma_zero.json"
    _prove(path.exists(), "results/phase23_sigma_zero.json does not exist — this probe reads it")
    blob = json.loads(path.read_text(encoding="utf-8"))
    wanted = (
        "clip_norm",
        "clip_bind_count",
        "composed_steps",
        "composed_lot_sizes",
        "records_per_lot",
    )
    missing = [key for key in wanted if key not in blob]
    _prove(not missing, f"results/phase23_sigma_zero.json is missing {missing}")
    diagnostic = {key: blob[key] for key in wanted}
    diagnostic["primary_k"] = blob["primary"]["k"]
    diagnostic["primary_n"] = blob["primary"]["n"]
    _prove(
        diagnostic["clip_norm"] == mitigation_budget.CONTROL_CLIP_NORM,
        f"Phase 23 ran the control at C={diagnostic['clip_norm']!r} while "
        f"mitigation_budget.CONTROL_CLIP_NORM is {mitigation_budget.CONTROL_CLIP_NORM!r}. This "
        "probe must run at the control's OWN C or the comparison is at a different bound",
    )
    _prove(
        diagnostic["clip_bind_count"] == 0,
        f"Phase 23's control recorded clip_bind_count={diagnostic['clip_bind_count']!r}. A "
        "binding bound there would make this probe's reference a picture of the clip",
    )
    return diagnostic


def read_phase23_reference():
    """The n=8 reference figure, resolved from the module that OWNS it — never retyped.

    Returns the disposition entry whose evidence carries the figure, so the record embeds Phase
    23's own sentence rather than this module's paraphrase of it.
    """
    import phase23_matched_prereg as mp

    quoted = [
        entry
        for entry in mp.DP_FN_BRANCH_DISPOSITIONS
        if PHASE23_REFERENCE_FIGURE in entry["evidence"]
    ]
    _prove(
        quoted,
        f"{PHASE23_REFERENCE_SYMBOL} no longer carries the figure "
        f"{PHASE23_REFERENCE_FIGURE!r}. This record quotes Phase 23's reference from the module "
        "that owns it; a missing figure means the reference moved and must be re-resolved, not "
        "retyped here",
    )
    return quoted[0], mp.MATCHED_GRAD_CLIP


# =================================================================================================
# ===== (c) THE TWO PATHS — same seed, same budget, same data, one seam apart =====
# =================================================================================================


def budget_symbols():
    """Every budget quantity BOTH paths run at, as ``symbol -> live value``.

    Recorded as imported NAMES with their values beside them (the plan's own instruction), so a
    later reader can re-resolve each one instead of trusting a transcript.
    """
    import teach_persona as tp

    return {
        "teach_persona.LR": tp.LR,
        "teach_persona.WARMUP_STEPS": tp.WARMUP_STEPS,
        "teach_persona.MAX_STEPS": tp.MAX_STEPS,
        "teach_persona.BATCH_SIZE": tp.BATCH_SIZE,
        "teach_persona.WEIGHT_DECAY": tp.WEIGHT_DECAY,
        "teach_persona.BLOCK_SIZE": tp.BLOCK_SIZE,
        "teach_persona.EVAL_INTERVAL": tp.EVAL_INTERVAL,
        "teach_persona.CHECKPOINT_INTERVAL": tp.CHECKPOINT_INTERVAL,
        "mitigation_budget.CONTROL_CLIP_NORM": mitigation_budget.CONTROL_CLIP_NORM,
        "mitigation_budget.STEP_BUDGET": mitigation_budget.STEP_BUDGET,
        "phase23_matched_prereg.MATCHED_GRAD_CLIP": read_phase23_reference()[1],
    }


def train_control_path(capacity, *, seed):
    """Train one adapter through the DP seam at sigma=0, at the control's own C.

    Routes through the single production entry ``teach_persona.train_arm``, so the adapter this
    returns is the one a real sweep control point would produce — the whole reason D-01 re-runs
    the control rather than importing Phase 23's.

    The seam object is captured on the way past so ``C`` and the bind count can be PROVED at the
    values the run actually used, before any comparison exists.
    """
    import teach_persona as tp

    facts, second_person, replay_ratio = tp.arm_spec(capacity)
    paths = tp.arm_outputs(capacity, prefix=cal.CALIBRATION_PREFIX)
    cal._release_calibration_targets(capacity, paths)

    real = tp.DPSGD
    box = {"seam": None}

    def factory(model, **kwargs):
        _prove(
            box["seam"] is None,
            f"{capacity}: a SECOND DPSGD was constructed in one control run. The bind count read "
            "afterwards would describe whichever seam was constructed last",
        )
        box["seam"] = real(model, **kwargs)
        return box["seam"]

    tp.DPSGD = factory
    started = time.time()
    try:
        trained = tp.train_arm(
            capacity,
            facts=facts,
            family_ids=cal._taught_family_ids(),
            second_person=second_person,
            replay_ratio=replay_ratio,
            seed=seed,
            prefix=cal.CALIBRATION_PREFIX,
            dp_sigma=CONTROL_SIGMA,
            dp_clip_norm=mitigation_budget.CONTROL_CLIP_NORM,
        )
    finally:
        tp.DPSGD = real
    seconds = time.time() - started

    seam = box["seam"]
    _prove(seam is not None, f"{capacity}: no DPSGD was constructed — the DP seam never armed")
    _prove(
        seam.sigma == CONTROL_SIGMA and seam.C == mitigation_budget.CONTROL_CLIP_NORM,
        f"{capacity}: the control ran at sigma={seam.sigma!r} / C={seam.C!r}, not at "
        f"{CONTROL_SIGMA!r} / {mitigation_budget.CONTROL_CLIP_NORM!r}",
    )
    _prove(
        seam._clip_bind_count == 0,
        f"{capacity}: the control's bound BOUND {seam._clip_bind_count!r} time(s). At sigma=0 the "
        "only thing C can do is clip, so a binding C makes this a picture of the bound rather "
        "than of the seam — and the residual measured against the comparator would be the CLIP, "
        "not the arithmetic. This refusal runs BEFORE any comparison exists",
    )
    print(
        f"[phase25_probe2] {capacity}: control trained in {seconds:.1f}s, "
        f"clip_bind_count={seam._clip_bind_count}, C={seam.C!r} — C is OBSERVED non-binding",
        flush=True,
    )
    return {
        "paths": paths,
        "adapter": paths["adapter"],
        "stats": trained["stats"],
        "final_train_loss": trained["final_train_loss"],
        "seconds": seconds,
        "clip_bind_count": int(seam._clip_bind_count),
    }


def comparator_call(capacity, *, seed, grad_clip):
    """The comparator's ``(train_config_fields, train_kwargs)`` — DERIVED from the DP arm's symbols.

    ``phase23_run.matched_control_call``'s shape, generalised over capacity. NOTHING is retyped:
    ``n_facts`` comes from ``arm_spec``, the bins from the DP arm's own ``arm_outputs``, the
    replay volume from ``replay_window_budget``, and the budget from ``teach_persona``'s own
    symbols.

    ``dp_fn`` IS DELIBERATELY ABSENT, exactly as in Phase 23: ``train()``'s own default is
    ``None``, so its absence IS the seam-off path and passing it explicitly would put a key in the
    diff for nothing.

    ``grad_clip`` is the ONE equalisation, and it is a constant imported from the module that
    measured why it is needed. ``loop.py`` applies ``clip_grad_norm_`` IFF ``dp_fn is None``, so at
    ``config.py``'s default of 1.0 this comparator would be clipped where the DP arm structurally
    is not — Phase 23 measured the old control binding on 19 of its first 25 steps at mean shrink
    0.8071. Without this the residual measured below would be the CLIP rather than the seam.
    """
    import teach_persona as tp

    n_facts = len(tp.arm_spec(capacity)[0])
    paths = tp.arm_outputs(comparator_arm(capacity), prefix=cal.CALIBRATION_PREFIX)
    # THE BIN PATHS ONLY. `arm_outputs` scopes csv/checkpoint/adapter by prefix but `bin`/`mask`
    # carry NO prefix, so these resolve to the SAME `data/persona_{capacity}_train*.bin` the
    # control just trained on — same bytes, same corpus, by construction rather than by care.
    dp_paths = tp.arm_outputs(capacity, prefix=cal.CALIBRATION_PREFIX)

    fields = dict(
        lr=tp.LR,
        warmup_steps=tp.WARMUP_STEPS,
        max_steps=tp.MAX_STEPS,
        batch_size=tp.BATCH_SIZE,
        weight_decay=tp.WEIGHT_DECAY,
        seed=seed,
        grad_accum_steps=n_facts,
        grad_clip=grad_clip,
    )
    kwargs = dict(
        train_bin=dp_paths["bin"],
        train_mask_bin=dp_paths["mask"],
        fact_bin=tp.fact_bin_path(dp_paths["bin"]),
        n_facts=n_facts,
        replay_bin=tp.DIALOG_TRAIN_BIN,
        replay_mask_bin=tp.DIALOG_TRAIN_MASK,
        replay_windows=tp.replay_window_budget(n_facts) // tp.BLOCK_SIZE,
        val_bin=tp.DIALOG_VAL_BIN,
        val_mask_bin=tp.DIALOG_VAL_MASK,
        penalty_fn=None,
        log_path=paths["csv"],
        checkpoint_path=paths["checkpoint"],
        eval_interval=tp.EVAL_INTERVAL,
        checkpoint_interval=tp.CHECKPOINT_INTERVAL,
        return_final_loss=True,
    )
    return paths, fields, kwargs


def train_comparator_path(capacity, *, seed, grad_clip):
    """Train the comparator adapter on the SAME bins, same seed, same budget — seam absent.

    ``phase23_run.train_matched_control``'s body, generalised over capacity and reduced to what
    this comparison needs. The bins are NOT rebuilt: :func:`train_control_path` ran first and
    wrote them, and rebuilding would be a second corpus rather than the same one.
    """
    import phase23_run as p23
    import teach_persona as tp

    paths, fields, kwargs = comparator_call(capacity, seed=seed, grad_clip=grad_clip)
    _prove(
        "dp_fn" not in kwargs,
        f"{capacity}: the comparator passes `dp_fn`. Its ABSENCE is what makes this the seam-off "
        "path; passing anything else makes it a second DP arm rather than a comparator for one",
    )
    for target in (kwargs["train_bin"], kwargs["train_mask_bin"], kwargs["fact_bin"]):
        _prove(
            pathlib.Path(target).exists(),
            f"{capacity}: {target} is absent. The comparator trains on the CONTROL'S OWN bins and "
            "does not build its own — run the control leg first",
        )
    cal._release_calibration_targets(comparator_arm(capacity), paths)

    runtime = tp.RuntimeConfig()
    blob = tp.torch.load(tp.CONVBASE_BEST, weights_only=False)  # our OWN checkpoint (T-14-04)
    model_cfg = tp.ModelConfig(**blob["model_config"])

    tp.seed_everything(seed)
    model = tp.GPT(model_cfg)
    model.load_state_dict(blob["model"])  # LOAD BEFORE INJECT — the load-bearing ordering
    n_wrapped = tp.inject_lora(model, tp.LORA_CFG)
    _prove(
        n_wrapped == 6 * model_cfg.n_layer,
        f"inject_lora wrapped {n_wrapped} projections, expected 6 * n_layer = "
        f"{6 * model_cfg.n_layer}",
    )
    tp.mark_only_lora_trainable(model)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    expected_trainable = tp.LORA_CFG.r * model_cfg.n_layer * 18 * model_cfg.n_embd
    _prove(
        trainable == expected_trainable,
        f"trainable census {trainable} != r*n_layer*18*n_embd = {expected_trainable}",
    )
    model.to(runtime.device)
    before = tp.snapshot_params(model)
    paths["csv"].parent.mkdir(parents=True, exist_ok=True)
    paths["checkpoint"].parent.mkdir(parents=True, exist_ok=True)

    started = time.time()
    with p23.captured_grad_clip() as clip_box:
        final = tp.train(
            train_config=tp.TrainConfig(**fields),
            runtime_config=runtime,
            model=model,
            model_config=model_cfg,
            **kwargs,
        )
    seconds = time.time() - started

    # ===== THE NON-BINDING PROOF, BEFORE ANY COMPARISON EXISTS =====
    norms = clip_box["norms"]
    _prove(
        len(norms) == tp.MAX_STEPS,
        f"{capacity}: clip_grad_norm_ was called {len(norms)} time(s) over a {tp.MAX_STEPS}-step "
        "run. loop.py has exactly ONE reachable call site and it fires once per optimizer step "
        "IFF the seam is absent, so a different count means this leg did not take the seam-off "
        "branch at all and the equalisation was never applied",
    )
    _prove(
        max(norms) < grad_clip,
        f"{capacity}: the comparator's largest PRE-clip global norm was {max(norms)!r}, at or "
        f"above the equalising bound {grad_clip!r}. A binding clip makes this leg differ from the "
        "control by CLIPPING rather than by the seam — the exact confound the equalisation exists "
        "to remove",
    )
    _prove(
        tp.math.isfinite(float(final)),
        f"non-finite final loss {final!r} on {comparator_arm(capacity)} (PITFALLS P5)",
    )
    moved = 0
    for name, param in model.named_parameters():
        if param.requires_grad:
            _prove(
                not tp.torch.equal(param, before[name]),
                f"[canary] trainable {name} did not move on {comparator_arm(capacity)} — silent "
                "training failure (P5)",
            )
            moved += 1
        else:
            _prove(
                tp.torch.equal(param, before[name]),
                f"[canary] frozen base param {name} changed on {comparator_arm(capacity)} — "
                "grad isolation broken",
            )

    tp.export_adapter(
        paths["adapter"],
        adapter=tp.lora_state_dict(model),
        lora_config=tp.asdict(tp.LORA_CFG),
        base_fingerprint={
            "git_sha": blob["git_sha"],
            "step": blob["step"],
            "val_loss": blob["val_loss"],
        },
    )
    print(
        f"[phase25_probe2] {comparator_arm(capacity)}: trained in {seconds:.1f}s, "
        f"{len(norms)} clip call(s), pre-clip norms in [{min(norms):.6g}, {max(norms):.6g}] "
        f"against {grad_clip!r} — OBSERVED non-binding, {moved} trainable(s) moved",
        flush=True,
    )
    return {
        "arm": comparator_arm(capacity),
        "paths": paths,
        "adapter": paths["adapter"],
        "final_train_loss": float(final),
        "seconds": seconds,
        "clip_calls": len(norms),
        "max_pre_clip_norm": max(norms),
    }


# =================================================================================================
# ===== (d) THE PER-TENSOR COMPARISON — every tensor recorded, no summary-only histogram =====
# =================================================================================================
#
# THE TWO RELATIVE FIGURES, AND WHY BOTH ARE RECORDED. Both definitions are fixed HERE, before the
# measurement, so neither is chosen after seeing a number:
#
#   * `max_rel_diff` — the ELEMENTWISE worst ratio |a-b| / |b| over elements where b != 0. This is
#     the quantity Phase 23 reported (`allclose(rtol=1e-5, atol=1e-7)`, worst RELATIVE difference
#     2.178e-07 at abs 3.7e-09), so it is the one that makes the n=8 column comparable to that
#     reference. It is also the one a near-zero denominator can inflate, which is why the next
#     figure travels beside it rather than instead of it.
#   * `max_norm_rel_diff` — `max_abs_diff / ref_max_abs`, the relative error in the max norm. It
#     has no denominator hazard and re-derives EXACTLY from the two values recorded next to it.
#
# `agreement_bound` is the max of `max_rel_diff` across the capacity's tensors, so `agreeing`
# equals `total` by construction on an honest write and the aggregate re-derives from its own rows.


def _load_adapter_tensors(path):
    """The ``lora_`` tensors of one exported adapter, on CPU, through the project's choke point."""
    from personacore.checkpoint import load_adapter

    artifact = load_adapter(path, map_location="cpu")
    return artifact["adapter"]


def compare_adapters(control_path, comparator_path):
    """One row per trainable LoRA tensor. Returns ``(rows, bound)``.

    Every bound is re-derivable from the values beside it: ``max_norm_rel_diff`` is exactly
    ``max_abs_diff / ref_max_abs``, and ``max_rel_diff`` carries the count of elements its
    denominator had to skip.
    """
    import torch

    left = _load_adapter_tensors(control_path)
    right = _load_adapter_tensors(comparator_path)
    _prove(
        set(left) == set(right),
        "the two adapters carry different tensor key sets — the comparison would be over a "
        f"subset. only-control={sorted(set(left) - set(right))}, "
        f"only-comparator={sorted(set(right) - set(left))}",
    )
    _prove(left, "the control adapter carries ZERO lora_ tensors — nothing to compare")

    rows = []
    for name in sorted(left):
        a = left[name].to(torch.float64)
        b = right[name].to(torch.float64)
        _prove(
            a.shape == b.shape,
            f"{name}: shapes differ ({tuple(a.shape)} vs {tuple(b.shape)})",
        )
        delta = (a - b).abs()
        ref_abs = b.abs()
        ref_max_abs = float(ref_abs.max())
        max_abs_diff = float(delta.max())
        nonzero = ref_abs > 0
        skipped = int((~nonzero).sum())
        elementwise = 0.0
        if bool(nonzero.any()):
            elementwise = float((delta[nonzero] / ref_abs[nonzero]).max())
        rows.append(
            {
                "name": name,
                "shape": list(a.shape),
                "numel": int(a.numel()),
                "max_abs_diff": max_abs_diff,
                "max_rel_diff": elementwise,
                "ref_max_abs": ref_max_abs,
                "max_norm_rel_diff": (max_abs_diff / ref_max_abs) if ref_max_abs else 0.0,
                "zero_reference_elements": skipped,
            }
        )
    bound = max(row["max_rel_diff"] for row in rows)
    return rows, bound


def aggregate_for(rows, bound):
    """``{agreeing, total}`` in COUNTS, recomputed from the rows themselves.

    ``agreeing`` counts rows whose ``max_rel_diff`` is within ``bound`` — the same recomputation
    ``tests/test_phase25_probe2.py`` performs against the committed record, so the aggregate can
    never stop describing its own data.
    """
    return {
        "agreeing": sum(1 for row in rows if row["max_rel_diff"] <= bound),
        "total": len(rows),
    }


# =================================================================================================
# ===== (e) THE RECORD =====
# =================================================================================================


def provenance_block():
    """This module's own provenance. ``phase25_calibrate.provenance_block``'s field set."""
    import torch

    from personacore.preflight import preflight_device

    return {
        "git_sha": git_sha(),
        "device": str(preflight_device(strict=True)["device"]),
        "torch_version": torch.__version__,
        "python_version": platform.python_version(),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "calibration_prefix": cal.CALIBRATION_PREFIX,
        "calibration_prefix_provenance": cal.CALIBRATION_PREFIX_PROVENANCE,
        "module": cal._rel(MODULE_PATH),
        "module_sha256": sha256_of(MODULE_PATH),
        "calibrate_module": cal._rel(cal.MODULE_PATH),
        "calibrate_module_sha256": sha256_of(cal.MODULE_PATH),
    }


def assemble_record(*, measured, declared, declared_digest, diagnostic, reference, symbols, seed):
    """Build the whole blob from measured per-capacity results. PURE — no GPU, no disk write.

    Kept separate from :func:`run_probe` so the entire assembly path can be exercised against
    stub measurements before a single GPU second is spent. Plan 25-12 lost a completed 45-minute
    run to a ``KeyError`` raised in the assembly step afterwards; this split is that lesson.
    """
    _prove(
        set(measured) == set(PROBE_CAPACITIES),
        f"measured capacities {sorted(measured)} != {sorted(PROBE_CAPACITIES)}",
    )
    _prove(
        len(declared) == DECLARED_DIFFERENCES_EXPECTED and declared_digest,
        "the declared differences must travel with their source digest and at length "
        f"{DECLARED_DIFFERENCES_EXPECTED}",
    )

    per_tensor = {capacity: measured[capacity]["rows"] for capacity in PROBE_CAPACITIES}
    bounds = {capacity: measured[capacity]["bound"] for capacity in PROBE_CAPACITIES}
    aggregate = {
        capacity: aggregate_for(per_tensor[capacity], bounds[capacity])
        for capacity in PROBE_CAPACITIES
    }
    for capacity in PROBE_CAPACITIES:
        _prove(
            aggregate[capacity]["total"] == len(per_tensor[capacity])
            and aggregate[capacity]["total"] > 0,
            f"{capacity}: the aggregate does not describe its own rows",
        )
        _prove(
            bounds[capacity] > 0.0,
            f"{capacity}: agreement_bound is {bounds[capacity]!r}. A bound of exactly 0.0 is a "
            "BIT-IDENTITY claim, which is precisely what D-04 forbids asserting between the "
            "sigma=0 point and the seam-off path. If the two adapters really did come out "
            "bit-identical, that is a finding to report and investigate — not a bound to record",
        )

    return {
        "governs": (
            "D-04's PROBE 2, re-run at BOTH capacities BEFORE any real sweep point exists. It "
            "records how far the sigma=0 DP path differs from the seam-off path per trainable "
            "LoRA tensor, as a PREDICTION rather than as an anomaly discovered mid-sweep."
        ),
        "measures": (
            "per-tensor relative agreement between an adapter trained through the DP seam at "
            "sigma=0 at the control's own C, and an adapter trained through the seam-off path "
            "(dp_fn absent at personacore.training.loop.train) on the SAME bins, at the SAME "
            "seed, under the SAME budget."
        ),
        "probe_shape": {
            "compared": "TRAINED ADAPTERS after the full teach_persona.MAX_STEPS budget",
            "phase23_compared": (
                "a SINGLE-STEP GRADIENT comparison — the DP seam's undivided backward -> "
                "absorb_record xN -> replay pass -> finalize(N) against the ordinary grad-accum "
                "reference (loss/N xN -> the identical replay pass)"
            ),
            "why_the_two_are_not_the_same_quantity": (
                "a 200-step AdamW trajectory COMPOUNDS the per-step float32 re-summation residual "
                "Phase 23 measured once. A figure LARGER than 2.178e-07 is therefore the EXPECTED "
                "reading at this shape, not a regression, and the n=8 column here is a first "
                "measurement of ITS OWN quantity rather than a repetition of Phase 23's."
            ),
            "equalisation": (
                "loop.py applies clip_grad_norm_ IFF the DP seam is absent, so the comparator's "
                "TrainConfig.grad_clip is set to phase23_matched_prereg.MATCHED_GRAD_CLIP and "
                "PROVED non-binding on the run that happened (declared difference #4's own "
                "disposition, equalised-by-constant). Without it the residual below would be the "
                "CLIP rather than the seam."
            ),
        },
        "seed": seed,
        "sigma": CONTROL_SIGMA,
        "clip_norm": mitigation_budget.CONTROL_CLIP_NORM,
        "clip_norm_source": "mitigation_budget.CONTROL_CLIP_NORM",
        "budget_symbols": symbols,
        "capacities": list(PROBE_CAPACITIES),
        "per_tensor": per_tensor,
        "aggregate": aggregate,
        "agreement_bound": bounds,
        "agreement_bound_governs": AGREEMENT_BOUND_GOVERNS,
        "relative_difference_definitions": {
            "max_rel_diff": (
                "elementwise max(|control - comparator| / |comparator|) over elements where the "
                "comparator element is non-zero; `zero_reference_elements` records how many were "
                "skipped. This is the definition Phase 23 reported, which is what makes the n=8 "
                "column comparable to 2.178e-07."
            ),
            "max_norm_rel_diff": (
                "max_abs_diff / ref_max_abs — the relative error in the max norm. No denominator "
                "hazard, and it re-derives EXACTLY from the two values recorded beside it."
            ),
            "agreement_bound": (
                "max(max_rel_diff) across the capacity's tensors. `aggregate.agreeing` counts "
                "rows within it and is recomputed from the rows, never stored independently."
            ),
        },
        "phase23_reference": {
            "figure": PHASE23_REFERENCE_FIGURE,
            "figure_value": float(PHASE23_REFERENCE_FIGURE),
            "symbol": PHASE23_REFERENCE_SYMBOL,
            "quoted_evidence": reference["evidence"],
            "quoted_site": reference["site"],
            "capacity": "dp_n8",
            "measured_here": bounds["dp_n8"],
            "reproduces": bool(bounds["dp_n8"] <= float(PHASE23_REFERENCE_FIGURE)),
            "ratio_to_reference": bounds["dp_n8"] / float(PHASE23_REFERENCE_FIGURE),
        },
        "first_measurement": {
            "capacity": "dp_n64",
            "statement": (
                "n=64 HAS NEVER BEEN PROBED. Phase 23 probed n=8 only, so the dp_n64 column is a "
                "FIRST MEASUREMENT and no prior figure exists for it to reproduce. There is "
                "nothing to compare it against and it must not be read as a repetition."
            ),
            "value": bounds["dp_n64"],
        },
        "declared_differences": declared,
        "declared_differences_source": DECLARED_DIFFERENCES_SOURCE,
        "declared_differences_source_sha256": declared_digest,
        "declared_differences_count": len(declared),
        "declared_differences_import_rule": (
            "read from results/phase23_matched_control.json at WRITE TIME, embedded verbatim with "
            "that file's sha256, and refused at any length other than "
            f"{DECLARED_DIFFERENCES_EXPECTED}. If Phase 23's record ever grows a fifth, this "
            "write FAILS rather than silently dropping it. A retyped list drifts; imported by "
            "path plus digest, it cannot."
        ),
        "control_diagnostic": diagnostic,
        "control_arm_identity": {
            "arms": ["dp_n8", "dp_n64"],
            "separated_by": "prefix",
            "prefix": cal.CALIBRATION_PREFIX,
            "why": CONTROL_ARM_IDENTITY_WHY,
            "precedents": [
                {
                    "precedent": "results/phase23_matched_control.json declared difference #2",
                    "quoted": declared[1]["difference"],
                    "matched_quantity": declared[1]["matched_quantity"],
                },
                {
                    "precedent": "phase23_matched_prereg.matched_arm(seed)",
                    "quoted": (
                        "already distinct from dp_n8 — a comparator that is not a member arm is "
                        "how this repository has scoped a seam-off twin before"
                    ),
                },
            ],
        },
        "seam_off_comparator_arm": SEAM_OFF_COMPARATOR_ARM,
        "seam_off_comparator_arms": {
            capacity: comparator_arm(capacity) for capacity in PROBE_CAPACITIES
        },
        "seam_off_comparator_arm_rule": (
            "D-06: only the dp_fn=None COMPARATOR is renamed. It is not a member of "
            "teach_persona.DP_ARMS and not a member of teach_persona.ARMS, because it has no "
            "arm_spec and cannot have one — it is the DP arm's data wiring reached with the DP "
            "seam absent. Renaming the CONTROL instead would break D-01's bit-level reproduction."
        ),
        "timings": {
            capacity: {
                "control_seconds": measured[capacity]["control_seconds"],
                "comparator_seconds": measured[capacity]["comparator_seconds"],
            }
            for capacity in PROBE_CAPACITIES
        },
        "legs": {
            capacity: {
                "control_arm": capacity,
                "control_final_train_loss": measured[capacity]["control_final_train_loss"],
                "control_clip_bind_count": measured[capacity]["control_clip_bind_count"],
                "comparator_arm": comparator_arm(capacity),
                "comparator_final_train_loss": measured[capacity]["comparator_final_train_loss"],
                "comparator_clip_calls": measured[capacity]["comparator_clip_calls"],
                "comparator_max_pre_clip_norm": measured[capacity]["comparator_max_pre_clip_norm"],
            }
            for capacity in PROBE_CAPACITIES
        },
        "point_set_exclusion": (
            "Both legs at both capacities run under phase25_calibrate.CALIBRATION_PREFIX and are "
            "EXCLUDED from the sweep's point set, exactly as phase23_sigma0 was. "
            "`git ls-files 'results/phase25_point_*.json'` is empty at this write, which is what "
            "D-04's 'before any real sweep point' means operationally."
        ),
        "provenance": provenance_block(),
    }


def run_probe(*, seed=PROBE_SEED):
    """Measure both capacities and write ``results/phase25_probe2_tensors.json``."""
    import phase23_run as p23
    import teach_persona as tp

    # ---- EVERY READ FIRST, BEFORE A SINGLE GPU SECOND ----
    declared, declared_digest = read_declared_differences()
    diagnostic = read_control_diagnostic()
    reference, grad_clip = read_phase23_reference()
    symbols = budget_symbols()
    _prove(
        seed == p23.SEED_LADDER[0],
        f"the probe seed {seed!r} is not phase23_run.SEED_LADDER[0] = {p23.SEED_LADDER[0]!r}. "
        "D-01's reproduction target was measured at that seed",
    )
    for capacity in PROBE_CAPACITIES:
        _prove(
            capacity in tp.DP_ARMS,
            f"{capacity!r} is not in teach_persona.DP_ARMS = {tp.DP_ARMS!r}",
        )
        _prove(
            comparator_arm(capacity) not in tp.ARMS and comparator_arm(capacity) not in tp.DP_ARMS,
            f"the comparator arm {comparator_arm(capacity)!r} collides with a real arm name. "
            "D-06 renames the COMPARATOR precisely so the two never share an identity",
        )
    print(
        f"[phase25_probe2] reads validated: {len(declared)} declared difference(s) at "
        f"{declared_digest[:16]}…, control diagnostic k/n="
        f"{diagnostic['primary_k']}/{diagnostic['primary_n']}, "
        f"equalising grad_clip={grad_clip!r}",
        flush=True,
    )

    measured = {}
    for capacity in PROBE_CAPACITIES:
        control = train_control_path(capacity, seed=seed)
        comparator = train_comparator_path(capacity, seed=seed, grad_clip=grad_clip)
        rows, bound = compare_adapters(control["adapter"], comparator["adapter"])
        measured[capacity] = {
            "rows": rows,
            "bound": bound,
            "control_seconds": control["seconds"],
            "control_final_train_loss": control["final_train_loss"],
            "control_clip_bind_count": control["clip_bind_count"],
            "comparator_seconds": comparator["seconds"],
            "comparator_final_train_loss": comparator["final_train_loss"],
            "comparator_clip_calls": comparator["clip_calls"],
            "comparator_max_pre_clip_norm": comparator["max_pre_clip_norm"],
        }
        print(
            f"[phase25_probe2] {capacity}: {len(rows)} tensor(s), agreement_bound={bound!r}",
            flush=True,
        )
        cal._release_calibration_targets(capacity, control["paths"])
        cal._release_calibration_targets(comparator_arm(capacity), comparator["paths"])

    blob = assemble_record(
        measured=measured,
        declared=declared,
        declared_digest=declared_digest,
        diagnostic=diagnostic,
        reference=reference,
        symbols=symbols,
        seed=seed,
    )
    phase25_run.atomic_write_json(RECORD_PATH, blob)
    print(f"[phase25_probe2] wrote {cal._rel(RECORD_PATH)}", flush=True)
    return blob


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=PROBE_SEED)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    run_probe(seed=args.seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
