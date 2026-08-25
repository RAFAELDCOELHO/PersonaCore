"""Per-record clipped, Gaussian-noised LoRA gradients -- the DP-SGD mechanism (DPSGD-01).

This object owns EVERYTHING between gradient accumulation and ``optimizer.step()``. It is a class
rather than a function because two of the four silent-non-privacy fakes are made impossible by a
SINGLE capture of ``sigma`` / ``clip_norm`` / the noise generator in ``__init__`` (D-17), and
because it must own the branch that bypasses the legacy averaged-gradient clip (D-03).

WHAT THIS SEAM CLAIMS
---------------------
Per-RECORD clipping. ``absorb_record`` reads one micro-batch's gradients -- one micro-step IS one
privacy record under Phase 21 D-02's ragged fact-aligned accumulation -- clips their GLOBAL L2 norm
to ``C``, adds the clipped vector into a DP-owned accumulator, and DRAINS ``.grad``. The
accumulator holds the SUM, never a running mean, so one record moves it by at most ``C`` and the
sensitivity is exactly ``C`` INDEPENDENTLY OF THE LOT SIZE (D-02). Noise is added to that sum; the
``/N`` happens LAST; then exactly one write per parameter combines the private term with whatever
public term ``.grad`` already holds.

WHAT THIS SEAM DOES **NOT** CLAIM
---------------------------------
It does not claim the legacy ``clip_grad_norm_`` at ``training/loop.py`` is unreachable -- making
it structurally unreachable inside an ``if dp_fn is None`` branch is plan 22-06's edit, not this
module's. It does not claim any particular ``sigma`` or ``clip_norm``: BOTH ARE KEYWORD-ONLY WITH
NO DEFAULT (D-08) and no numeric value for either exists anywhere in Phase 22's tree, so there is
nothing for Phase 23 to override and nothing to drift across Phase 20's Z boundary. It does not
claim an epsilon; ``privacy/accountant.py`` owns that, and it consumes ``sigma`` and ``T``, never
``C`` (the clip constant cancels out of the accounting -- see below). And it does not claim the
optimizer leaves the released value alone: DP is closed under post-processing, so epsilon survives
``clip_grad_norm_``, weight decay and AdamW's own per-parameter rescale by sqrt(v). The rule that
survives contact is *nothing between the noise and* ``optimizer.step()``, and it rests on
AUDITABILITY rather than on privacy -- see :meth:`DPSGD.finalize`.

THE ADJACENCY RELATION
----------------------
THE ADJACENCY RELATION IS **add/remove one fact**, and its sensitivity multiplier is **1.0**
(``Delta = 1.0 * C``). Removing one record changes the clipped sum by ``g_i``, whose norm is at
most ``C`` -- the textbook sensitivity argument, and it is the add/remove-one argument. Under
replace-one it would be ``2C`` and every published epsilon would be roughly 2x larger. Those are
the same words as ``scripts/mitigation_accountant.py``'s ``NEIGHBOURING`` /
``SENSITIVITY_MULTIPLIER`` and as ``src/personacore/privacy/accountant.py``'s docstring on
purpose: this module's noise line is the THIRD of the three sites the cross-site consistency test
``tests/test_phase22_dpsgd_ast.py::test_adjacency_relation_consistent`` reads, and that test refuses
on disagreement. The pin cannot be imported here -- ``src/`` never puts ``scripts/`` on the path --
which is exactly why agreement is checked by reading sources rather than by an import.

Invariants (each one pinned by ``tests/test_phase22_dpsgd.py``, statically by
``tests/test_phase22_dpsgd_ast.py``):

  - ``sigma`` IS THE NOISE MULTIPLIER ``sigma_noise / clip_norm``, unitless -- never the raw
    standard deviation of the added noise. So THE NOISE STANDARD DEVIATION IS ``sigma * C``, and
    that product is spelled ``self.sigma * self.C`` at the one draw site and nowhere else. A
    ``Constant`` operand in it (a stray ``2.0 *``) is the definitional wrong-sensitivity fake, so
    the expression is pinned structurally as a two-operand ``Mult`` over two ``self`` attributes.

  - ``self.C`` IS THE SINGLE CLIP CONSTANT. The per-record clip, the runtime sensitivity check and
    the noise standard deviation all read the same attribute, captured once. Introducing a wrong
    sensitivity therefore requires ADDING A SECOND CLIP CONSTANT, which is a positive code
    insertion the AST guard refuses (D-17 / FAKE 2).

  - ``self._g`` IS A DEDICATED ``torch.Generator``, seeded ONCE in ``__init__`` and NEVER re-seeded
    (D-07 / D-17 / FAKE 4). It is never the global torch stream: that independence would otherwise
    rest entirely on ``ModelConfig.dropout = 0.0`` and ``LoRAConfig.dropout = 0.0``, neither of
    which is pinned and the second of which is an ordinary sweep knob. A dedicated generator makes
    "the torch RNG is untouched by the data path" STRUCTURAL rather than contingent.

  - A ``sigma`` OF ZERO TAKES THE SAME CODE PATH. There is no branch that skips the draw.
    Measured under torch 2.7.1: ``torch.normal(std=0.0, generator=g)`` returns EXACT zeros AND
    advances ``g``'s state -- which is precisely what leaves "the noise never got added" with
    nowhere to hide.

  - ``clip_norm`` IS REQUIRED FINITE, and ``C = infinity`` is represented as a FINITE BOUND PROVEN
    NOT TO BIND rather than as ``math.inf``. The forcing measurement, under torch 2.7.1 in this
    project's venv: ``0.0 * math.inf`` is ``nan``, and
    ``torch.normal(mean=0.0, std=float("nan"), size=(3,))`` raises
    ``RuntimeError: normal expects std >= 0.0, but found std nan``. The noise ``std`` IS
    ``self.sigma * self.C`` and cannot be anything else (no ``sigma == 0`` branch is available, and
    no pre-computed attribute either), so ``math.inf`` would crash the draw at exactly the
    ``sigma``-of-zero identity input D-06 is built around. "Proven not to bind" is literal, not
    rhetorical: :attr:`_clip_bind_count` counts the records on which the clip actually scaled, and
    the identity test asserts it is ZERO rather than assuming the bound was loose enough.

  - REFUSALS ARE ``raise RuntimeError`` / ``raise ValueError`` -- **never** ``assert``, which is
    stripped under ``python -O`` and would turn a loud refusal into a silently non-private run
    (``lora/layer.py::LoRALinear.merge``'s docstring records that reason for this repository), and
    **never** ``_prove``, which is a ``scripts/`` convention (measured: 18 ``scripts/`` modules,
    0 ``src/`` modules).

Refusal markers. Every refusal message carries a bracketed ``[dp-refusal:...]`` tag naming which
refusal fired. Three refusals sharing one message are one refusal wearing three hats; the tags are
what let ``tests/test_phase22_dpsgd.py`` prove pairwise distinctness per case rather than in
aggregate.
"""

import math

import torch

from ..lora.layer import LoRALinear

# The six projections LoRA wraps per transformer block (`lora/config.py::TARGET_PROJECTIONS`).
# Used ONLY to derive n_layer from the live model's wrapped count -- never to size the noise.
_PROJECTIONS_PER_LAYER = 6

# The closed-form trainable census multiplier: 18 * r * n_embd per layer across the six
# projections (`scripts/teach_persona.py`'s own census, lifted to the seam by D-04).
_PARAMS_PER_LAYER_PER_RANK_UNIT = 18


class DPSGD:
    """The DP-SGD mechanism: per-record clip -> summed accumulator -> noise -> one write.

    Construction is a FULL PRE-PASS: every refusal below runs before a single attribute is
    assigned, so a refusal leaves no half-built DP state behind. That is
    ``lora/inject.py::set_adapter_enabled``'s idiom verbatim -- two loops, deliberately, *"so a
    refusal flips no flag at all"*.
    """

    def __init__(
        self,
        model,
        *,
        sigma,
        clip_norm,
        generator=None,
        seed=None,
        device=None,
        scaler=None,
        runtime=None,
        sensitivity_tolerance=1e-6,
    ):
        """Capture sigma / C / the generator ONCE, after auditing the model by PROPERTY.

        Args:
            model: the LIVE model. Every census below is derived from it and NEVER from a
                caller-supplied number -- D-04's own defect class is *a guarantee stated as a
                property of the mechanism that is actually a property of one caller*.
            sigma: the NOISE MULTIPLIER (unitless). KEYWORD-ONLY, NO DEFAULT (D-08): Phase 22
                names no sigma anywhere, so Phase 20's Z boundary stays untouched and Phase 23
                supplies it from ``scripts/mitigation_budget.py``.
            clip_norm: the per-record L2 bound ``C``. KEYWORD-ONLY, NO DEFAULT, and REQUIRED
                FINITE AND POSITIVE (see the module docstring's ``C = infinity`` bullet).
            generator: an existing ``torch.Generator`` adopted AS-IS. Otherwise one is built here
                and seeded ONCE from ``seed`` (or ``torch.initial_seed()``). Either way it is
                never re-seeded anywhere in this class.
            seed: the one-shot seed for a generator built here. Ignored when ``generator`` is
                given -- adopting a generator and then re-seeding it would be FAKE 4 at
                construction time.
            device: device for a generator built here; defaults to the trainable parameters' own
                device (D-14: the generator is bound to the REAL execution device).
            scaler: an optional ``GradScaler``. Refused when enabled.
            runtime: an optional ``RuntimeConfig``. Refused when ``runtime.amp`` is live.
            sensitivity_tolerance: the relative slack in the runtime ``norm <= C * (1 + tol)``
                check, absorbing float32 re-summation error only.
        """
        # ---- PRE-PASS 1: the caller-supplied numeric domain. Four refusals, four messages. ----
        sigma_value = float(sigma)
        clip_value = float(clip_norm)
        if not math.isfinite(sigma_value):
            raise ValueError(
                f"[dp-refusal:sigma-domain] sigma is {sigma_value!r}, which is not finite. sigma "
                "is the unitless NOISE MULTIPLIER and the noise standard deviation is sigma * C; "
                "a non-finite multiplier makes that product non-finite or nan and the draw is "
                "then either degenerate or a hard crash."
            )
        if sigma_value < 0.0:
            raise ValueError(
                f"[dp-refusal:sigma-domain] sigma is {sigma_value!r}, which is negative. "
                "torch.normal refuses a negative std, and a negative noise multiplier has no "
                "meaning: a sigma of zero is the identity (exact zeros through the SAME code "
                "path) and everything private is sigma > 0."
            )
        if clip_value <= 0.0:
            raise ValueError(
                f"[dp-refusal:clip-domain] clip_norm is {clip_value!r}, which is not strictly "
                "positive. C is an L2 BOUND: a zero bound clips every record to the zero vector "
                "(no signal survives) and a negative bound is not a norm at all."
            )
        if not math.isfinite(clip_value):
            raise ValueError(
                f"[dp-refusal:clip-domain] clip_norm is {clip_value!r}, which is not finite. "
                "math.inf is REFUSED, not legal, and the measurement that forces this is a hard "
                "crash at exactly D-06's identity input: under torch 2.7.1, 0.0 * math.inf is "
                "nan, and torch.normal(mean=0.0, std=float('nan'), size=(3,)) raises "
                "'RuntimeError: normal expects std >= 0.0, but found std nan'. The noise std is "
                "self.sigma * self.C and cannot be anything else -- D-07 forbids a branch that "
                "skips the draw at sigma == 0, and the noise-line guard forbids a pre-computed "
                "std attribute -- so an infinite C would crash the draw at a sigma of zero. C = "
                "infinity is therefore represented as a FINITE bound PROVEN NOT TO BIND: coef is "
                "exactly 1.0 on every record, x * 1.0 is bit-identical in IEEE-754 for finite x, "
                "and _clip_bind_count == 0 is the OBSERVATION that makes 'proven' literal."
            )
        tolerance_value = float(sensitivity_tolerance)
        if not math.isfinite(tolerance_value) or tolerance_value < 0.0:
            raise ValueError(
                f"[dp-refusal:tolerance-domain] sensitivity_tolerance is {tolerance_value!r}. It "
                "is the relative slack in the runtime norm <= C * (1 + tol) check and must be a "
                "finite, non-negative number; a non-finite slack makes that check vacuous."
            )

        # ---- PRE-PASS 2 (D-04 refusal 1): audit requires_grad by PROPERTY, not by name. ----
        # `"lora_" in name` is `lora/inject.py::mark_only_lora_trainable`'s OWN predicate, reused
        # rather than re-invented; `lora_state_dict` uses the same substring test.
        offenders = [
            name for name, p in model.named_parameters() if p.requires_grad and "lora_" not in name
        ]
        if offenders:
            raise RuntimeError(
                f"[dp-refusal:unfrozen-base] {len(offenders)} non-LoRA parameter(s) still have "
                f"requires_grad=True, first few: {offenders[:4]}. inject_lora DOES NOT FREEZE -- "
                "mark_only_lora_trainable is a SEPARATE call, and a DP caller that omits that one "
                "line noises 14,223,360 parameters against a sensitivity computed for 331,776. "
                "That is the wrong-sensitivity fake reachable by OMISSION, so it is refused at "
                "the SEAM as a property of the mechanism rather than trusted as a property of one "
                "caller."
            )

        # ---- PRE-PASS 3 (D-04 refusal 2): a live scaler makes per-record clipping impossible. --
        # `is_enabled()` is torch's own accessor. A stub scaler that does not expose it cannot be
        # interrogated and is treated as disabled -- the loop's fp32 default path passes exactly
        # such a stub, and `RuntimeConfig.__post_init__` already forces amp=False there.
        if scaler is not None and hasattr(scaler, "is_enabled") and scaler.is_enabled():
            raise RuntimeError(
                "[dp-refusal:live-scaler] the supplied GradScaler is ENABLED. Measured: "
                "unscale_() twice per optimizer step raises 'RuntimeError: unscale_() has already "
                "been called on this optimizer since the last update().', and reading .grad "
                "mid-accumulation under a live scaler yields SCALED gradients, so clipping "
                "against C is wrong by the scale factor -- silently. RuntimeConfig.__post_init__ "
                "forces amp=False on cpu and mps, so this never bites on the primary path; the "
                "P100 fallback needs a REFUSAL, not a silent wrong clip."
            )
        if runtime is not None and bool(getattr(runtime, "amp", False)):
            raise RuntimeError(
                "[dp-refusal:live-scaler] the supplied RuntimeConfig has amp=True. See above: "
                "AMP-scaled .grad read mid-accumulation is wrong by the scale factor, and the "
                "double unscale_() the per-record path would need is itself a RuntimeError. This "
                "is the P100 fallback's refusal; cpu and mps never reach it."
            )

        # ---- PRE-PASS 4 (D-04 refusal 3): the closed-form census, derived from the LIVE model. --
        wrapped = [m for m in model.modules() if isinstance(m, LoRALinear)]
        if not wrapped:
            raise RuntimeError(
                "[dp-refusal:census] the model carries no LoRALinear modules. There is nothing "
                "for a LoRA-only DP mechanism to clip, and a seam that silently accepted an "
                "un-injected model would noise nothing while reporting an epsilon."
            )
        if len(wrapped) % _PROJECTIONS_PER_LAYER != 0:
            raise RuntimeError(
                f"[dp-refusal:census] {len(wrapped)} LoRALinear modules is not a multiple of "
                f"{_PROJECTIONS_PER_LAYER} (the six projections per block), so n_layer cannot be "
                "derived from the live model and the closed-form census below would be checked "
                "against a fabricated shape."
            )
        n_layer = len(wrapped) // _PROJECTIONS_PER_LAYER
        rank = wrapped[0].lora_A.shape[0]
        mismatched = sorted({m.lora_A.shape[0] for m in wrapped} - {rank})
        if mismatched:
            raise RuntimeError(
                f"[dp-refusal:census] wrapped modules disagree on rank: {rank} at the first "
                f"module against {mismatched} elsewhere. A single r is what makes the closed form "
                "r * n_layer * 18 * n_embd a census rather than a coincidence."
            )
        n_embd = getattr(getattr(model, "config", None), "n_embd", None)
        if n_embd is None:
            raise RuntimeError(
                "[dp-refusal:census] the model exposes no config.n_embd, so the closed-form "
                "census cannot be derived from the live model. D-04 refuses to take n_embd from "
                "a caller argument: a census computed from the number the caller believes is the "
                "shape proves nothing about the shape the caller actually built."
            )
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        expected = rank * n_layer * _PARAMS_PER_LAYER_PER_RANK_UNIT * n_embd
        if trainable != expected:
            raise RuntimeError(
                f"[dp-refusal:census] trainable census {trainable} != r*n_layer*18*n_embd = "
                f"{expected} (r={rank}, n_layer={n_layer}, n_embd={n_embd}). This is NOT redundant "
                "with the requires_grad audit: that one catches an unfrozen base, while this one "
                "additionally catches a future LoRAConfig.r change that moves the trainable count "
                "without updating the calibrated sensitivity -- every name still matches 'lora_' "
                "and the count is simply wrong."
            )

        params = [p for name, p in model.named_parameters() if p.requires_grad and "lora_" in name]
        if not params:
            raise RuntimeError(
                "[dp-refusal:census] no trainable LoRA parameters were resolved, so the per-record "
                "clip would run over an empty vector and every norm would be exactly 0.0 -- a "
                "mechanism that refuses nothing and noises nothing."
            )

        # ---- The pre-pass passed. ONLY NOW is any state assigned (inject.py:145-153's idiom). --
        self.sigma = float(sigma)  # SINGLE source of truth -- the noise line reads this (D-17).
        self.C = float(clip_norm)  # SINGLE source of truth -- the clip AND the noise read this.
        self.sensitivity_tolerance = tolerance_value
        self._params = params
        # Allocated ONCE and only ever zeroed, so the single-write assertion's data_ptr() identity
        # is stable across steps and a re-allocation cannot hide an aliasing regression.
        self._accum = [torch.zeros_like(p) for p in params]
        self._writes = 0
        self._records = 0
        # Run-lifetime, NEVER reset per step: it is what turns "the finite bound did not bind" from
        # an assumption about the fixture's magnitudes into an observation about the whole run.
        self._clip_bind_count = 0
        self._prev_gen_state = None
        self._drained = True
        if generator is None:
            gen_device = params[0].device if device is None else torch.device(device)
            self._g = torch.Generator(device=gen_device)
            # The ONE seeding, here in __init__ and nowhere else (D-17). Every occurrence of a
            # re-seed in any other method is FAKE 4's positive insertion.
            self._g.manual_seed(torch.initial_seed() if seed is None else int(seed))
        else:
            self._g = generator
