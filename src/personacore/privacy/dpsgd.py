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
It does not claim ANYTHING about ``training/loop.py`` on its own. The legacy ``clip_grad_norm_``
is now structurally unreachable on the DP path -- it has exactly ONE reachable call site there and
it sits inside an ``if dp_fn is None:`` branch -- but that is ``loop.py``'s edit and ``loop.py``'s
guard (``tests/test_phase22_dpsgd.py::test_legacy_clip_is_unreachable_on_the_dp_path`` observes it
firing once with the seam off and zero times with it on); this module cannot enforce it and does
not pretend to. It does not claim any particular ``sigma`` or ``clip_norm``: BOTH ARE
KEYWORD-ONLY WITH NO DEFAULT (D-08) and no numeric value for either exists anywhere in Phase 22's
tree, so there is nothing for Phase 23 to override and nothing to drift across Phase 20's Z
boundary. It does not claim an epsilon; ``privacy/accountant.py`` owns that, and it consumes
``sigma`` and ``T``, never
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

    # ---------------------------------------------------------------------------------------
    # The checkpoint slot (D-14). NEITHER of these is on the step path, and neither may ever
    # become reachable from one: `load_noise_rng_state` is FAKE 4's own shape, made safe only by
    # WHERE it is callable from. `tests/test_phase22_dpsgd_ast.py::test_dpsgd_never_reseeds_its
    # _generator` pins that with an exemption paired to an unreachability proof.
    # ---------------------------------------------------------------------------------------

    def noise_rng_state(self):
        """The dedicated generator's state, for the checkpoint's ``dp_noise_rng`` slot (D-14).

        Measured under torch 2.7.1, WITH ITS DENOMINATOR because the figure is DEVICE-DEPENDENT:
        this state is **5,056 bytes on CPU** and **44 bytes on MPS**; ``set_state`` round-trips
        exactly on both. Every Phase-22 test runs on CPU (``22-VALIDATION.md`` says so for every
        row), so a test asserting a byte count must assert the CPU figure or assert
        ``len(state) > 0`` rather than the 44 a planning document quoted from an MPS probe.

        A dedicated generator's draw does NOT change the global MPS state -- which is exactly why
        D-14 keeps TWO separately-named slots: ``rng["mps"]`` (DPSGD-05's literal requirement,
        recorded honestly as required-but-UNEXERCISED) and ``dp_noise_rng`` (the slot the DP path
        actually FIRES). Reading the live state at SAVE time rather than binding it once is the
        whole point: ``train()``'s ``checkpoint_extra`` is bound at entry, so a value placed there
        would be stale at every save after the first, and DPSGD-05 gates on a resume reproducing a
        BIT-IDENTICAL reported epsilon.
        """
        return self._g.get_state()

    def load_noise_rng_state(self, state):
        """Restore a saved generator state on RESUME. **This is not a re-seed.**

        Called from exactly two places -- ``training/loop.py::train``'s ``resume_from`` block and
        tests -- and from NO step method. The distinction is the whole safety argument: the same
        call inside ``finalize`` would be FAKE 4 (*RNG reused across steps*), which is why the AST
        guard's exemption for this method ships alongside an assertion that no step entry's call
        graph can reach it.

        Omitting the restore is the failure every other guard is blind to. ``__init__`` re-seeds
        ``self._g`` from the caller's seed, so a resumed run REPLAYS noise it already released;
        D-16 invariant 4 cannot see it because ``_prev_gen_state`` is ``None`` on a freshly
        constructed object, making the continuity check vacuous on the first post-resume step. And
        ``CLAUDE.md`` makes resume ROUTINE on the primary M3 path (laptop sleep/interrupt), so this
        is the common case rather than an edge one.
        """
        if self._prev_gen_state is not None:
            raise RuntimeError(
                "[dp-refusal:rng-restore] this seam has already released noise for at least one "
                "step, so restoring a generator state into it would REWIND a stream that has "
                "already been drawn from -- the same observable as FAKE 4. A resume restores into "
                "a FRESHLY CONSTRUCTED seam (train()'s resume_from block runs before the first "
                "step), which is the only shape this method is reachable in through production."
            )
        self._g.set_state(state)

    # ---------------------------------------------------------------------------------------
    # The step path. Together these own EVERYTHING between accumulation and optimizer.step();
    # nothing else may write .grad in that window (D-03's surviving rule).
    # ---------------------------------------------------------------------------------------

    def begin_step(self):
        """Arm the seam for one optimizer step: zero the accumulator, reset the per-step counters.

        The accumulator buffers are ZEROED, never re-allocated, so ``data_ptr()`` identity is
        stable across steps and the single-write assertion's aliasing check cannot be defeated by
        a fresh allocation each step.

        ``_clip_bind_count`` is deliberately NOT reset. It is a RUN-LIFETIME counter, so the
        ``C = infinity`` identity test can assert the bound never bound across the WHOLE run
        rather than only on the last step.
        """
        for buf in self._accum:
            buf.zero_()
        self._writes = 0
        self._records = 0
        self._drained = True

    def _global_norm(self, tensors):
        """The L2 norm across ALL trainable LoRA gradients as ONE vector -- GLOBAL, not per-tensor.

        The norm of the per-tensor norms IS the norm of the concatenation, which is what
        ``clip_grad_norm_`` computes and what DPSGD-01's sensitivity bound is stated over.

        D-01's rejected alternative (b), recorded here because it is the shape a future reader is
        most likely to reach for: TENSOR HOOKS. Hooks fire per-tensor MID-backward, and a
        per-record GLOBAL norm over all 72 tensors is not knowable until ``backward()`` completes.
        Hooks would therefore force per-PARAMETER clipping -- a different and strictly weaker
        sensitivity bound than the one DPSGD-01 states and the accountant is told.
        """
        parts = [torch.linalg.vector_norm(t.detach().float()) for t in tensors]
        return float(torch.linalg.vector_norm(torch.stack(parts)))

    def absorb_record(self):
        """Clip ONE record's gradients to ``C``, add them into the SUM, and drain ``.grad``.

        Called after each micro-batch's ``backward()``. One micro-step IS one privacy record
        (Phase 21 D-02), so the gradients sitting in ``.grad`` at entry are exactly one record's.

        D-16 invariant 1 (drain) is enforced from BOTH ends. At entry the seam refuses unless the
        previous call actually drained -- ``_drained`` is cleared before anything is read and set
        again only by the drain loop at the very bottom, so a refactor that DROPS the drain leaves
        the flag false and the next record is refused. And a ``.grad`` of ``None`` at entry is
        refused too, because that is the caller having skipped a backward.

        The consequence D-01 names, stated once: ``backward()`` ACCUMULATES. Without the
        per-micro-step drain, record *i*'s clip would see records 1..*i* summed and the true
        per-record sensitivity would silently become ``N*C`` while the accountant is told ``C``.
        """
        if not self._drained:
            raise RuntimeError(
                "[dp-invariant:drain] the previous absorb_record did not drain .grad, so this "
                "record's clip would see a RUNNING SUM rather than one record. backward() "
                "ACCUMULATES: without the per-micro-step drain, record i's clip sees records "
                "1..i summed and the true per-record sensitivity silently becomes N*C while the "
                "accountant is told C. Nothing else in the system would notice -- the run "
                "converges fine."
            )
        self._drained = False
        missing = [i for i, p in enumerate(self._params) if p.grad is None]
        if missing:
            raise RuntimeError(
                f"[dp-invariant:drain] {len(missing)} of {len(self._params)} trainable LoRA "
                f"parameters have .grad = None at absorb_record entry (first: index "
                f"{missing[0]}). There is nothing to absorb: either no backward() ran for this "
                "record, or absorb_record was called twice for one backward. Absorbing a partial "
                "record would under-count the sum while the accountant charges a full record."
            )

        grads = [p.grad for p in self._params]
        norm = self._global_norm(grads)
        if norm <= self.C:
            # coef is EXACTLY 1.0 and x * 1.0 is bit-identical in IEEE-754 for finite x, so the
            # clip is a genuine no-op through the SAME code path -- no branch skips it.
            coef = 1.0
        else:
            # reads self.C (D-17): the single clip constant. A second constant here is FAKE 2.
            coef = self.C / norm
            # THE ONLY place the clip actually scales. This counter is what turns "a finite bound
            # that does not bind" from an ASSUMPTION into an OBSERVATION, and it is how C =
            # infinity is represented now that math.inf is refused -- 22-CONTEXT.md's *Claude's
            # Discretion* sanctions choosing the representation, and this is the choice: a finite
            # bound whose non-binding is COUNTED rather than hoped for.
            self._clip_bind_count += 1

        scaled = [g.detach() * coef for g in grads]
        # D-16 invariant 2 (sensitivity), RE-COMPUTED from the clipped tensors rather than as
        # norm * coef -- the latter is C by construction and could never fail.
        clipped_norm = self._global_norm(scaled)
        if clipped_norm > self.C * (1.0 + self.sensitivity_tolerance):
            raise RuntimeError(
                f"[dp-invariant:sensitivity] the CLIPPED global norm is {clipped_norm!r}, above "
                f"C * (1 + {self.sensitivity_tolerance!r}) = "
                f"{self.C * (1.0 + self.sensitivity_tolerance)!r}. The noise is scaled to a "
                "sensitivity of exactly C, so a record contributing more than C means the noise "
                "is scaled to the WRONG SENSITIVITY and the published epsilon is optimistic by "
                "the ratio. This reads the SAME self.C the clip and the noise line read."
            )

        for buf, contribution in zip(self._accum, scaled):
            # The SUM, never a running mean (D-02): one record moves it by at most C, so the
            # sensitivity is exactly C independently of the lot size N.
            buf.add_(contribution)
        self._records += 1

        for p in self._params:
            p.grad = None  # D-01's per-micro-step drain -- load-bearing, not tidiness.
        self._drained = True

    def _draw_noise(self):
        """One Gaussian draw per accumulator buffer, from the DEDICATED generator (D-07).

        There is NO branch on ``sigma == 0``. ``torch.normal`` with ``std=0.0`` returns exact zeros
        AND advances the generator, which is precisely what leaves "the noise never got added"
        with nowhere to hide: the call sequence is identical at every sigma.
        """
        return [
            torch.normal(
                mean=0.0,
                # reads self.C and self.sigma (D-17). std = sigma * C, sigma being the noise
                # MULTIPLIER. Adjacency is add/remove one fact, multiplier 1.0, so Delta = C.
                std=self.sigma * self.C,
                size=buf.shape,
                generator=self._g,
                device=buf.device,
                dtype=buf.dtype,
            )
            for buf in self._accum
        ]

    def _noised_private(self, accum):
        """noise ON THE SUM, then ``/N`` LAST (D-02), with D-16 invariant 4 around the draws.

        The order is the whole point and it is not interchangeable. ``self._accum`` holds the SUM
        of clipped per-record gradients; the noise is added to THAT sum (one record moves the sum
        by at most C -- the textbook sensitivity argument); only then is the result divided by N.

        D-02's trap, which arrives for free by inheriting one existing line: with
        ``loop.py``'s ``loss = total / accum`` left in place on the DP path, ``.grad`` after each
        backward would hold ``g_i / N``, so clipping THAT to C sets the true per-record
        sensitivity to ``C*N`` while the accountant is told ``C``. That is DPSGD-04's
        wrong-sensitivity fake, and it converges fine.
        """
        pre = self._g.get_state()
        if self._prev_gen_state is not None and not torch.equal(pre, self._prev_gen_state):
            raise RuntimeError(
                "[dp-invariant:generator] this step's PRE-draw generator state is not the "
                "previous step's POST-draw state, so something touched the generator between "
                "steps. That is FAKE 4 -- RNG REUSED ACROSS STEPS: an in-step manual_seed makes "
                "every step draw the SAME noise vector, the noise stops being independent across "
                "compositions, and the T-fold composition the accountant charges for is not the "
                "mechanism that ran. CONTINUITY is asserted rather than 'the pre-state differs "
                "from last step's pre-state', because the latter is silent on a re-seed to a "
                "DIFFERENT fixed value and on any foreign consumer draining the same stream."
            )
        noise = self._draw_noise()
        post = self._g.get_state()
        if torch.equal(pre, post):
            raise RuntimeError(
                "[dp-invariant:generator] the generator state did not advance across the draws, "
                "so the draw did not happen. At sigma = 0 the values are exact zeros BUT the "
                "state still moves (measured, torch 2.7.1) -- which is exactly why 'noise was "
                "added' stays verifiable at the identity input instead of being unfalsifiable."
            )
        self._prev_gen_state = post
        return [(buf + drawn) / accum for buf, drawn in zip(self._accum, noise)]

    def _write_once(self, private):
        """The SINGLE combining write, as a MEASURED count rather than a described sequence.

        Exactly one assignment per trainable parameter: ``p.grad = private`` when there is no
        public term, else ``p.grad.add_(private)``. D-01: *"``p.grad += private_accum`` is the
        SINGLE write that combines the two terms, immediately before ``optimizer.step()``. Nothing
        re-normalizes after that sum."*
        """
        for buf, p, term in zip(self._accum, self._params, private):
            if buf.data_ptr() == term.data_ptr():
                raise RuntimeError(
                    "[dp-invariant:single-write] the private term ALIASES its accumulator buffer, "
                    "so the write would mutate the accumulator in place and the next step would "
                    "start from a noised, already-released sum."
                )
            if p.grad is None:
                p.grad = term
            else:
                p.grad.add_(term)
            self._writes += 1
        if self._writes != len(self._params):
            raise RuntimeError(
                f"[dp-invariant:single-write] {self._writes} writes for "
                f"{len(self._params)} trainable parameters. Exactly one write per parameter "
                "combines the private and public terms; anything else means a parameter was "
                "written twice (a second write re-releases private data the accountant charged "
                "for once) or not at all (its update carries no noise)."
            )
        buf_ptrs = {buf.data_ptr() for buf in self._accum}
        grad_ptrs = {p.grad.data_ptr() for p in self._params}
        if buf_ptrs & grad_ptrs:
            raise RuntimeError(
                f"[dp-invariant:single-write] {len(buf_ptrs & grad_ptrs)} accumulator buffer(s) "
                "share storage with a .grad tensor. private_accum must never alias .grad: a "
                "shared buffer makes the drain and the release the same memory, and the "
                "single-write count above would then be counting writes that overwrite each other."
            )

    def finalize(self, accum):
        """Draw the noise, divide by N, and perform the one combining write. Then ``step()``.

        Called AFTER ``replay_fn`` has run, so ``.grad`` holds the PUBLIC term exactly and this
        method's write is the only place the two terms meet.

        D-03's SURVIVING rule, and its correct basis -- the stronger version would be an
        over-claim. DP is closed under post-processing, so epsilon survives ``clip_grad_norm_``,
        weight decay and AdamW's own per-parameter rescale by sqrt(v); an absolute "nothing
        re-normalizes after noise" rule would forbid the optimizer. The rule that survives contact
        is *nothing between the noise and* ``optimizer.step()``, and it rests on three MEASURED
        things:

          1. ``clip_grad_norm_(model.parameters(), ...)`` runs over the MIXED buffer, so the
             released private magnitude becomes a function of PUBLIC data. Not a privacy break,
             but it makes "the public term is independent of the private records" unstateable in
             the direction the report needs.
          2. It DEFEATS a DPSGD-04 positive control: wrong sensitivity is detectable in the
             released magnitude, and renormalizing to a fixed norm erases exactly that signal. The
             fake would converge AND pass.
          3. Measured, it is inert BY ACCIDENT rather than by construction: at the frozen-base
             regime the mixed norm goes 0.436096 -> 0.436096, factor 1.000000, so it does not bind
             at ``grad_clip = 1.0``. Whether it binds on the REAL corpus at 200 overfit steps is
             UNMEASURED. Inert-by-accident is the definition of a convention.
        """
        lot = int(accum)
        if lot < 1:
            raise ValueError(
                f"[dp-invariant:lot] accum is {accum!r}; the divisor in D-02's 'divide LAST' step "
                "is the number of records summed and must be at least 1."
            )
        if self._records != lot:
            raise RuntimeError(
                f"[dp-invariant:lot] {self._records} records were absorbed but accum is {lot}. "
                "The /N that happens LAST must divide by the number of records actually clipped "
                "and summed; dividing by a different N releases something that is not the mean of "
                "what was charged for. A zero here means begin_step/absorb_record never ran."
            )
        private = self._noised_private(lot)
        self._write_once(private)
