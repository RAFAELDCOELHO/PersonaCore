"""THE PROTOCOL-MATCHED COMPARATOR'S BLIND RULES — committed while its glob is EMPTY.

**THIS MODULE IS EDIT-ONCE FROM THE MOMENT ``results/phase23_matched_*`` FIRST MATCHES.**
``tests/test_phase20_prereg.py``'s ``_assert_ordering_holds`` carries two conjuncts —
``prereg != first_add`` for EVERY commit touching a pre-registration against EVERY artifact's
EARLIEST add, and ``git merge-base --is-ancestor prereg first_add``. Together they forbid any
commit that touches this file once 23-17's first matched artifact is tracked: such a commit is a
pre-registration commit that is not a strict ancestor of that first add, and ``adds[-1]`` takes the
earliest add so a delete-and-re-add cycle cannot launder it. Until that artifact lands this file is
TECHNICALLY still editable — but that window closes at THIS PLAN'S OWN COMMIT in practice and
STRUCTURALLY at 23-17's first artifact, and **no downstream plan may treat it as a safety valve.**
Every constant, path and rule the four downstream gap plans consume is therefore declared HERE,
ahead of need, including the full ``VERDICT_REQUIRED_KEYS`` tuple: a key guessed later cannot be
added.

**WHY THIS MODULE EXISTS, STATED PLAINLY.** ``results/phase23_sigma_zero.json`` already exists and
its reading ``0.7837301587301587`` was ALREADY VISIBLE when the protocol below was designed. The
reduction (``phase23_prereg.noise_floor``), the central-reading pin (``control_readings[0]``) and
the verdict (``phase23_prereg.sigma_zero_verdict``) are all still blind — they were pinned at
``c7de5d4``. What was NOT yet pinned is the comparator's own PROTOCOL, which is therefore the last
remaining degree of freedom: someone who knows σ=0 read 0.7837 could design a protocol that lands
near it. That freedom is spent HERE, blind, while ``git ls-files 'results/phase23_matched_*'``
returns nothing. See ``SIGMA_ZERO_VISIBILITY_DISCLOSURE``, which both downstream records are
refused without.

**THE THREE CLOSED PRE-REGISTRATIONS ARE NOT EDITED BY THIS PHASE.**
``scripts/phase23_prereg.py`` is byte-identical to ``c7de5d4`` and stays so; the same holds for
``scripts/mitigation_gate.py`` and ``scripts/mitigation_accountant.py``. This module adds no rule
to any of them and neither creates nor imports any of them. ``sigma_zero_verdict`` and
``noise_floor`` are correct and blind, and the corrected comparator is a new **INPUT** to them, not
a rule change. ``.planning/debug/sigma-zero-beats-control.md`` (status ``root-caused``, commit
``263f5f8``) is the measurement every disposition below is quoted from.

WHY THIS FILE MAY IMPORT ``ast``/``collections``/``math`` AT ALL: it is deliberately NOT named
``mitigation_*``. ``scripts/mitigation_budget.py``'s docstring records that the ``mitigation_*.py``
glob carries a ``{pathlib, sys, erasure_gate}`` import ceiling with **zero headroom** — one
``json`` there turns a committed guard RED. This module sits outside that glob, exactly as
``scripts/phase23_prereg.py`` does when it imports ``math``.

CPU-only, GPU-free, no torch, no network, stdlib only.
"""

import ast
import collections


def _prove(condition, message):
    """``SystemExit`` on a broken invariant — ``scripts/phase23_prereg.py:54-62``'s register.

    Never ``assert``. ``python -O`` strips ``assert`` outright, and this module is almost entirely
    refusals: under ``-O`` a bare-``assert`` implementation would admit every case it exists to
    reject, silently. The acceptance gate on this file AST-walks it for ``Assert`` nodes rather
    than grepping, because the prose above discusses the word.
    """
    if not condition:
        raise SystemExit(f"[phase23_matched_prereg] {message}")


# =================================================================================================
# ===== (a) THE ARTIFACT REGISTER — every path the four downstream gap plans will write =====
#
# Declared ahead of need because this file is EDIT-ONCE (see the module docstring). Same register
# as `phase23_prereg`'s: a later plan wanting a path DERIVES it from here rather than writing a
# string literal at a call site. This repository has shipped plans naming paths the code refuses.
# =================================================================================================

# 23-17: the protocol-matched comparator's N per-seed readings and the RE-REDUCED floor. The old
# `CONTROL_NOISE_FLOOR` governs the OLD protocol and cannot be carried over.
MATCHED_CONTROL_RECORD = "results/phase23_matched_control.json"

# 23-19: the re-test — `phase23_prereg.sigma_zero_verdict` called again with the matched readings.
MATCHED_VERDICT_RECORD = "results/phase23_matched_verdict.json"

# What `prove_first_attempt` and the ancestry guard bind on. Both records above are members.
MATCHED_ARTIFACT_GLOB = "results/phase23_matched_*"

# `teach_persona.arm_outputs(matched_arm(seed), prefix=MATCHED_ARM_PREFIX)` renders
#   results/phase23_matched_control_seed1337/run.csv          <- INSIDE the glob above
#   checkpoints/phase23_matched_control_seed1337_adapter.pt   <- inside GITIGNORED `checkpoints/`
#   checkpoints/phase23_matched_control_seed1337_latest.pt
#   data/persona_matched_control_seed1337_train{,_mask}.bin   <- `bin`/`mask` carry NO prefix; that
#     is `arm_outputs`' own documented non-widening ("inventing one would MOVE an existing path"),
#     and it does not matter here because THIS ARM BUILDS NO BINS AT ALL. It trains on `dp_n8`'s
#     already-packed fact-aligned three-bin corpus — that is what "protocol-matched" means.
#
# The checkpoint half being gitignored (`.gitignore:14`) is EXACTLY why (i)'s guarantee is scoped
# the way it is: a deleted seed checkpoint leaves no residue in `git ls-files`.
MATCHED_ARM_PREFIX = "phase23"


def matched_arm(seed):
    """The comparator's arm name for one seed. ``1337`` -> ``"matched_control_seed1337"``.

    Refuses a non-integer or ``bool`` seed. ``bool`` is an ``int`` subclass, so
    ``matched_arm(True)`` would otherwise render ``matched_control_seedTrue`` — a real path,
    silently, for an arm nobody scheduled.
    """
    _prove(
        isinstance(seed, int) and not isinstance(seed, bool),
        f"seed {seed!r} is not an int (bool excluded). The seed is rendered directly into an arm "
        "name and therefore into a csv path inside the ancestry-guarded glob, so a float or a "
        "bool here produces a real path for an arm nobody scheduled",
    )
    return f"matched_control_seed{seed}"


# =================================================================================================
# ===== (b) THE COMPARATOR'S GRADIENT CLIP — the difference 23-08 did not enumerate =====
# =================================================================================================

# `config.py:105` defaults `TrainConfig.grad_clip` to 1.0, and `loop.py:220-228` applies
# `clip_grad_norm_` IFF `dp_fn is None`. So at the default the comparator would be clipped exactly
# where the DP arm structurally is not. MEASURED on the real corpus (debug record, PROBE 1): the
# control's clip BOUND ON 19 OF ITS FIRST 25 STEPS with mean shrink 0.8071, against DP pre-clip
# norms of 1.538-2.278 that were never clipped at all. `DPSGD.finalize`'s own "inert by accident …
# UNMEASURED" is measured FALSE. 1e6 is this repository's established non-binding bound
# (`tests/test_phase22_checkpoint.py:97` `_NON_BINDING_CLIP`, `tests/test_phase22_fakes.py:93`,
# `phase23_run.SIGMA_ZERO_CLIP_NORM`).
#
# THE INERTNESS CLAIM, STATED EXACTLY AS BOUNDED AS IT WAS MEASURED — this comment is EDIT-ONCE and
# cannot be corrected later, so it carries its exception rather than the tidier unqualified phrase.
# `torch/nn/utils/clip_grad.py::_clip_grads_with_norm_` computes
# `clip_coef = max_norm / (total_norm + 1e-6)`, clamps it to `max=1.0`, then
# `torch._foreach_mul_(device_grads, clip_coef_clamped)`. At C=1e6 against ||g|| ~ 2 the clamp
# returns exactly 1.0, so every gradient is multiplied by exactly 1.0.
#
# RE-MEASURED BY THE EXECUTOR ON THIS MACHINE (2026-08-27, torch 2.7.1, M3/MPS), NOT INHERITED:
# 3 trials x 65,536 float32 elements, normal-range gradients scaled to ||g|| ~ 2 with subnormals
# planted at indices 0-3.
#   * CPU  — BITWISE IDENTICAL, 0/65,536 elements changed, INCLUDING every planted subnormal.
#   * MPS  — bitwise identical for normal-range gradients, but the multiply-by-1.0 FLUSHES
#     SUBNORMAL ENTRIES TO ZERO: 1.401298464324817e-45 -> 0.0 and 4.999999675228202e-39 -> 0.0,
#     while the smallest NORMAL float32 (1.1754943508222875e-38 = 2**-126, verified against
#     `torch.finfo(torch.float32).tiny`) and 1e-30 both survive untouched. The boundary is exactly
#     the subnormal threshold.
#   * ONE FINDING THE PLAN'S INHERITED FIGURE DID NOT RECORD, and the reason re-measuring was
#     required: an ON-DEVICE bitwise check CANNOT SEE THIS FLUSH. `torch.equal(before, after)`
#     evaluated on MPS returns True and `(before != after).sum()` returns 0, because the comparison
#     operator flushes its own subnormal operands too. The flush is visible only by reading the
#     elements back to host with `.item()`. A future guard that "verifies inertness" with an
#     on-device comparison would be green and blind. Isolated further: the subnormals survive the
#     host->device copy intact, so it is the CLIP's `_foreach_mul_`, not the transfer, that flushes.
#
# WHY THE EXCEPTION CANNOT MATTER HERE, as a magnitude rather than as a hope: the LoRA trainable
# parameter count is 331,776 (r=8, 6 targets, 6 layers, n_embd=384), so at ||g|| ~ 2 the RMS
# per-element gradient is 2/sqrt(331776) = 2/576 = 3.472e-3 — about 35 orders of magnitude above
# the subnormal ceiling. A gradient element small enough to be flushed contributes nothing an
# optimizer step could carry.
#
# AND "NON-BINDING" IS PROVEN AT RUN TIME, NEVER ASSUMED: 23-17 captures `clip_grad_norm_`'s RETURN
# VALUE (the PRE-clip global norm) on every step and records it. That is the same discipline that
# produced `clip_bind_count == 0` for the σ=0 arm BEFORE any reading existed.
MATCHED_GRAD_CLIP = 1e6


# =================================================================================================
# ===== (c)-(f) THE `dp_fn` BRANCH LEDGER — completeness BY CONSTRUCTION, not by care =====
#
# 23-08 enumerated four residual differences BY HAND, in advance, and MISSED `grad_clip` — the
# largest per-step effect after the packer. Hand enumeration is the defect; an AST census is the
# fix. These three censuses turn "did we list them all?" into a refusal a future edit reddens.
# =================================================================================================

# EXACTLY the seven-branch census of `src/personacore/training/loop.py`, keyed by
# `(enclosing_function_name, ast.unparse(node.test))`. Condition strings are `ast.unparse` output
# verbatim, single quotes included.
#
# A COUNTER AND NOT AN ORDERED SEQUENCE, DELIBERATELY: a pure reorder inside `loop.py` changes
# nothing about the protocol and must not redden, while a NEW branch or a REMOVED one must.
DP_FN_BRANCH_COUNTS = {
    ("_optimizer_step", "dp_fn is not None"): 3,
    ("_optimizer_step", "dp_fn is None"): 1,
    ("_dp_extra", "dp_fn is None"): 1,
    ("train", "dp_fn is None and ckpt.get('dp_noise_rng') is not None"): 1,
    ("train", "dp_fn is not None and ckpt.get('dp_noise_rng') is not None"): 1,
}

# The closed disposition set. A branch outside it is not a disposition, it is an opinion.
DP_FN_DISPOSITIONS = (
    "inert",
    "equalised-by-arithmetic",
    "equalised-by-constant",
    "declared-difference",
    "unreached",
)

# One entry per branch — `sum(DP_FN_BRANCH_COUNTS.values())` of them. Each cites the MEASUREMENT it
# rests on, never an intention.
DP_FN_BRANCH_DISPOSITIONS = (
    {
        "function": "_optimizer_step",
        "condition": "dp_fn is not None",
        "site": "begin_step() at loop.py:189-193",
        "disposition": "inert",
        "evidence": "zeroes the DP-OWNED accumulator, an object the comparator does not have. It "
        "touches no model gradient and no optimizer state, so there is nothing for the comparator "
        "to reproduce.",
    },
    {
        "function": "_optimizer_step",
        "condition": "dp_fn is not None",
        "site": "the `/accum` bypass at loop.py:211",
        "disposition": "equalised-by-arithmetic",
        "evidence": "PROBE 2 of the debug record: over all 72 trainable LoRA tensors the DP seam "
        "(undivided backward -> absorb_record x8 -> replay pass -> finalize(8)) agrees with the "
        "ordinary grad-accum reference (loss/8 x8 -> the identical replay pass) at "
        "allclose(rtol=1e-5, atol=1e-7), worst RELATIVE difference 2.178e-07 (abs 3.7e-09, at "
        "blocks.2.mlp.fc_in.lora_B) — float32 re-summation noise. The undivided backward plus the "
        "divide-by-N-last is the SAME SCALE a /accum path gives.",
    },
    {
        "function": "_optimizer_step",
        "condition": "dp_fn is not None",
        "site": "absorb_record() at loop.py:213-215",
        "disposition": "equalised-by-arithmetic",
        "evidence": "same PROBE 2. The per-record clip's coefficient is exactly 1.0 at "
        "clip_bind_count == 0 (proven over all 200 steps BEFORE any reading existed), so "
        "clip-then-SUM-then-drain reduces to an ordinary accumulation.",
    },
    {
        "function": "_optimizer_step",
        "condition": "dp_fn is None",
        "site": "clip_grad_norm_ at loop.py:220-221, vs finalize() at loop.py:222-228",
        "disposition": "equalised-by-constant",
        "evidence": "**THIS IS THE ONE 23-08 DID NOT ENUMERATE.** Four residual differences were "
        "listed by hand in advance and this was not among them, which is why the ledger is now an "
        "AST census rather than a list. MEASURED (PROBE 1): the control's clip BINDS ON 19 OF 25 "
        "first steps with MEAN SHRINK 0.8071, while the DP arm's norms (1.538-2.278, consistently "
        "~1.9x the control's) are never clipped at all because this branch is unreachable under "
        "dp_fn. Equalised by setting the comparator's TrainConfig.grad_clip to MATCHED_GRAD_CLIP, "
        "a non-binding bound whose inertness is measured and bounded above.",
    },
    {
        "function": "_dp_extra",
        "condition": "dp_fn is None",
        "site": "loop.py:709",
        "disposition": "declared-difference",
        "evidence": "the comparator's checkpoint carries no `dp_noise_rng` slot, because it "
        "constructs no DPSGD. This is checkpoint CONTENT, written after every gradient has been "
        "computed and consumed, so it is downstream of everything a reading depends on and cannot "
        "move one. Declared rather than equalised: inventing a fake slot would be a difference in "
        "the other direction.",
    },
    {
        "function": "train",
        "condition": "dp_fn is None and ckpt.get('dp_noise_rng') is not None",
        "site": "the resume DP-slot matrix at loop.py:766",
        "disposition": "unreached",
        "evidence": "this scheduling passes NO `resume_from`, so no ckpt is read and neither arm "
        "of the resume matrix executes. Unreached, not equalised — and `prove_train_call_keys` is "
        "what keeps that true by refusing a `train(...)` keyword set that changes.",
    },
    {
        "function": "train",
        "condition": "dp_fn is not None and ckpt.get('dp_noise_rng') is not None",
        "site": "the resume DP-slot matrix at loop.py:781",
        "disposition": "unreached",
        "evidence": "same: no `resume_from` is passed, so the resume path is never entered on "
        "either side.",
    },
)


def dp_fn_branch_census(source):
    """Every ``dp_fn``-conditioned branch in ``source``, as a ``Counter`` of (function, condition).

    Walks ``If`` and ``IfExp`` and keeps any node whose ``test`` contains an ``ast.Name`` with
    ``id == "dp_fn"``. The enclosing function is tracked with a stack over ``FunctionDef`` and
    ``AsyncFunctionDef``; ``"<module>"`` when the stack is empty.

    A COUNTER because a pure reorder inside ``loop.py`` must not redden a protocol ledger, while a
    new or removed branch must.
    """
    stack = []
    found = []

    def visit(node):
        pushed = False
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            stack.append(node.name)
            pushed = True
        if isinstance(node, (ast.If, ast.IfExp)) and any(
            isinstance(inner, ast.Name) and inner.id == "dp_fn" for inner in ast.walk(node.test)
        ):
            found.append((stack[-1] if stack else "<module>", ast.unparse(node.test)))
        for child in ast.iter_child_nodes(node):
            visit(child)
        if pushed:
            stack.pop()

    visit(ast.parse(source))
    return collections.Counter(found)


def prove_branch_ledger_complete(source):
    """Refuse unless ``source``'s ``dp_fn`` branches are EXACTLY ``DP_FN_BRANCH_COUNTS``.

    Returns the census. The meta-guard matters as much as the equality: a walk that silently
    stopped working finds nothing, and an empty census would compare unequal only by accident of
    the declaration being non-empty — so emptiness is refused by name.
    """
    census = dp_fn_branch_census(source)
    declared = collections.Counter(DP_FN_BRANCH_COUNTS)

    _prove(
        bool(census),
        "the dp_fn branch census found NOTHING in the source it was given. A walk that silently "
        "stopped working finds nothing and would then 'prove' completeness by proving no branches "
        "exist. This meta-guard is what stops a broken instrument reading GREEN",
    )
    _prove(
        len(DP_FN_BRANCH_DISPOSITIONS) == sum(DP_FN_BRANCH_COUNTS.values()),
        f"DP_FN_BRANCH_DISPOSITIONS holds {len(DP_FN_BRANCH_DISPOSITIONS)} entries but "
        f"DP_FN_BRANCH_COUNTS declares {sum(DP_FN_BRANCH_COUNTS.values())} branches. Every branch "
        "must carry a disposition and its evidence, or the ledger names a difference nobody "
        "dispositioned",
    )
    for entry in DP_FN_BRANCH_DISPOSITIONS:
        _prove(
            entry["disposition"] in DP_FN_DISPOSITIONS,
            f"disposition {entry['disposition']!r} for {entry['function']}/{entry['condition']!r} "
            f"is not one of {DP_FN_DISPOSITIONS}. A branch outside the closed set is not a "
            "disposition, it is an opinion",
        )

    undeclared = census - declared
    missing = declared - census
    _prove(
        census == declared,
        f"the live dp_fn branch census does not match the declared ledger.\n"
        f"  UNDECLARED (in the source, not in the ledger): {sorted(undeclared.items())}\n"
        f"  MISSING    (in the ledger, not in the source): {sorted(missing.items())}\n"
        "An UNDECLARED branch is fatal because it is a difference between the comparator and the "
        "σ=0 arm that nobody dispositioned: 23-08 enumerated four residual differences BY HAND, in "
        "advance, and missed `grad_clip` — the largest per-step effect after the packer, measured "
        "binding on 19 of 25 control steps. A MISSING branch is equally fatal: it means this "
        "ledger's evidence describes code that no longer exists, and this module is EDIT-ONCE so "
        "the ledger cannot be corrected. Either way the comparator's protocol claim is void",
    )
    return census


# =================================================================================================
# ===== (g) THE DP WIRING KEY CENSUS — the two dicts that reach `train()` on the DP path =====
# =================================================================================================

# `scripts/teach_persona.py:1585` — `dp_accum = dict(grad_accum_steps=...) if is_dp else {}`.
# Goes to the `TrainConfig` CONSTRUCTOR, not to `train()`. This is the 8.125x lot-volume lever.
DP_TRAIN_KEYS = ("grad_accum_steps",)

# `scripts/teach_persona.py:1586` — `dp_kwargs = dict(...) if is_dp else {}`, splatted into
# `train(...)`. Sorted, because the census compares SETS and a reader should not infer an order.
DP_KWARGS_KEYS = (
    "dp_fn",
    "fact_bin",
    "n_facts",
    "replay_bin",
    "replay_mask_bin",
    "replay_windows",
)


def dp_wiring_key_census(source):
    """``(dp_accum_keys, dp_kwargs_keys)`` as frozensets, AST-read from ``teach_persona``'s source.

    READ BY AST RATHER THAN RETYPED, for a reason this repository MEASURED. `teach_persona.py`'s
    own comment at :1570-1584 records it: ``grad_accum_steps`` appeared **9 times in that file's
    PROSE and 0 times in its CODE**, so the production ``TrainConfig(...)`` silently inherited
    ``config.py``'s default of 1 and SC2's "one micro-step = one privacy record" was prose at the
    only caller that mattered. **A wiring the measurement cannot see is worse than no wiring**,
    because the surrounding text stays confidently wrong. A retyped key set here would be a copy
    free to disagree with the live caller, and the disagreement would be invisible — both would
    look right.

    Both assignments are ``IfExp`` whose ``body`` is a ``Call`` to ``dict``, so the keyword names
    are ``node.value.body.keywords``' ``kw.arg``.
    """
    seen = {}
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id not in ("dp_accum", "dp_kwargs"):
            continue
        value = node.value
        call = value.body if isinstance(value, ast.IfExp) else value
        if isinstance(call, ast.Call):
            seen[target.id] = frozenset(kw.arg for kw in call.keywords if kw.arg)

    accum = seen.get("dp_accum", frozenset())
    kwargs = seen.get("dp_kwargs", frozenset())
    _prove(
        bool(accum) and bool(kwargs),
        f"the dp wiring census read dp_accum={sorted(accum)} and dp_kwargs={sorted(kwargs)}; at "
        "least one is EMPTY. A walk that silently stopped working, or an assignment whose shape "
        "changed, reads empty and would then agree with nothing — this meta-guard refuses rather "
        "than letting a broken instrument report a match it never made",
    )
    return accum, kwargs


def prove_dp_wiring_keys(source):
    """Refuse unless the live ``dp_accum``/``dp_kwargs`` key sets are exactly the declared ones."""
    accum, kwargs = dp_wiring_key_census(source)
    _prove(
        accum == frozenset(DP_TRAIN_KEYS),
        f"the live dp_accum keys are {sorted(accum)} but DP_TRAIN_KEYS declares "
        f"{sorted(DP_TRAIN_KEYS)}.\n"
        f"  UNDECLARED: {sorted(accum - frozenset(DP_TRAIN_KEYS))}\n"
        f"  MISSING   : {sorted(frozenset(DP_TRAIN_KEYS) - accum)}\n"
        "These go to the TrainConfig constructor and set the DP arm's LOT SIZE. A key added or "
        "removed here changes the protocol the comparator is supposed to match",
    )
    _prove(
        kwargs == frozenset(DP_KWARGS_KEYS),
        f"the live dp_kwargs keys are {sorted(kwargs)} but DP_KWARGS_KEYS declares "
        f"{sorted(DP_KWARGS_KEYS)}.\n"
        f"  UNDECLARED: {sorted(kwargs - frozenset(DP_KWARGS_KEYS))}\n"
        f"  MISSING   : {sorted(frozenset(DP_KWARGS_KEYS) - kwargs)}\n"
        "These are splatted into train() and carry the fact-aligned packer and the train-time "
        "replay pass — the two mechanisms the comparator exists to reproduce",
    )
    return accum, kwargs


# =================================================================================================
# ===== (k) THE PRODUCTION `train(...)` CALL CENSUS — the leg the other two do not cover =====
# =================================================================================================

# The frozen 21-name union of `scripts/teach_persona.py:1613`'s production `train(...)` call inside
# `train_arm`: 15 named keywords plus the six resolved through `**dp_kwargs`.
#
# WHY THIS THIRD LEG EXISTS. The branch census sees `dp_fn`-conditioned branches; the wiring census
# sees the two DP dicts. NEITHER sees the other 15 keywords. A future edit adding e.g.
# `extra_eval_fns=` at that call site would silently un-match the comparator with both existing
# gates GREEN — the exact 23-08 failure shape, one level up.
TRAIN_CALL_KEYS = (
    "checkpoint_interval",
    "checkpoint_path",
    "dp_fn",
    "eval_interval",
    "fact_bin",
    "log_path",
    "model",
    "model_config",
    "n_facts",
    "penalty_fn",
    "replay_bin",
    "replay_mask_bin",
    "replay_windows",
    "resume_from",
    "return_final_loss",
    "runtime_config",
    "train_bin",
    "train_config",
    "train_mask_bin",
    "val_bin",
    "val_mask_bin",
)


def prove_train_call_keys(source):
    """Refuse unless the production ``train(...)`` call's resolved keyword union is exactly frozen.

    Finds the ``Call`` to ``train`` inside ``FunctionDef train_arm``, collects the named keywords,
    and resolves each ``kw.arg is None`` splat by looking the splatted NAME up through
    ``dp_wiring_key_census`` (so ``**dp_kwargs`` contributes its six keys).

    Two meta-guards, because a walk that finds nothing must refuse rather than pass: the named set
    must be NON-EMPTY, and EXACTLY ONE splat must be seen — a second splat is a name this
    resolution cannot follow, and silently ignoring it would under-count the call.

    THE COMPARATOR REPRODUCES THIS SET MINUS ``{resume_from, dp_fn}``: no resume (which is what
    makes the two `train` resume branches ``unreached``) and no DP seam (which is the whole point —
    a non-DP arm that nonetheless reaches the ``dp_kwargs`` wiring). 23-16's preflight is where
    that subtraction is checked; this function only pins the set it is subtracted FROM.
    """
    tree = ast.parse(source)
    named = set()
    splats = []
    calls = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != "train_arm":
            continue
        for inner in ast.walk(node):
            if not isinstance(inner, ast.Call):
                continue
            func = inner.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            if name != "train":
                continue
            calls += 1
            for kw in inner.keywords:
                if kw.arg is None:
                    splats.append(ast.unparse(kw.value))
                else:
                    named.add(kw.arg)

    _prove(
        calls and named,
        f"the train(...) census found {calls} call(s) inside `train_arm` and {len(named)} named "
        "keyword(s). A walk that found no call, or a call with no keywords, must REFUSE — it "
        "would otherwise 'prove' the keyword set unchanged by failing to look at it",
    )
    _prove(
        len(splats) == 1,
        f"the production train(...) call carries {len(splats)} splat(s): {splats}. Exactly ONE is "
        "expected (`**dp_kwargs`). A second splat is a name this resolution cannot follow, and "
        "silently ignoring it would under-count the call's real keyword set — which is precisely "
        "the blindness this third census exists to remove",
    )

    accum, kwargs = dp_wiring_key_census(source)
    resolved = {"dp_accum": accum, "dp_kwargs": kwargs}
    _prove(
        splats[0] in resolved,
        f"the splat `**{splats[0]}` is not a name this census can resolve (known: "
        f"{sorted(resolved)}). An unresolvable splat hides an unknown number of keywords",
    )
    union = named | set(resolved[splats[0]])

    _prove(
        union == set(TRAIN_CALL_KEYS),
        f"the production train(...) keyword union is {sorted(union)} but TRAIN_CALL_KEYS declares "
        f"{sorted(TRAIN_CALL_KEYS)}.\n"
        f"  UNDECLARED (at the call site, not in the pin): {sorted(union - set(TRAIN_CALL_KEYS))}\n"
        f"  MISSING    (in the pin, not at the call site): {sorted(set(TRAIN_CALL_KEYS) - union)}\n"
        "The comparator reproduces this set MINUS {resume_from, dp_fn}; 23-16's preflight is where "
        "that subtraction is checked. The dp_fn-branch census and the dp-wiring census BOTH stay "
        "GREEN while a 16th production keyword un-matches the comparator, which is the 23-08 "
        "failure shape one level up: a hand-drawn boundary that did not know what it excluded",
    )
    return union


# =================================================================================================
# ===== (h) WHAT REMAINS DIFFERENT AFTER EQUALISATION — declared, not discovered later =====
# =================================================================================================

# The three mechanisms the comparator DOES equalise, each with its measured size. One predicate —
# `teach_persona.py:1389` `is_dp = arm in DP_ARMS` — switches all three together, which is why the
# σ=0 arm measured a DIFFERENT TRAINING PROTOCOL rather than the same one with the noise zeroed.
MATCHED_EQUALISED = (
    {
        "mechanism": "lot volume",
        "measured": "DP lot = 33 teaching + 32 replay = 65 windows; control lot = 8 windows "
        "(8.125x). Measured TEACHING-token exposure over the run: 1,689,600 vs 196,867 = 8.58x.",
    },
    {
        "mechanism": "teaching loss weight",
        "measured": "the DP arm's fact-aligned packer returns EVERY window of one fact "
        "(fact_index = step % n_facts, deterministic full coverage), so teaching enters the "
        "gradient at weight 1.0. The control draws 8 RANDOM windows from a bin that is 51.94% "
        "replay, so masked-CE puts weight p = 2719/6262 = 0.4342 on teaching. 1/0.4342 = 2.30x, "
        "on top of drastically lower gradient variance that AdamW compounds over 200 steps.",
    },
    {
        "mechanism": "grad_clip",
        "measured": "binding on 19 of the control's first 25 steps, mean shrink 0.8071, against "
        "DP norms of 1.538-2.278 never clipped. Equalised by MATCHED_GRAD_CLIP = 1e6.",
    },
)

# Everything that STAYS different. Declared HERE, blind, because a difference discovered after the
# comparator's reading exists is a difference discovered with the number visible.
MATCHED_DIFFERENCES = (
    {
        "difference": "the `dp_noise_rng` checkpoint slot",
        "disposition": "declared-difference",
        "matched_quantity": "none — the comparator constructs no DPSGD, so it has no slot to write",
        "evidence": "`_dp_extra` at loop.py:709 (branch 5 of the ledger). Checkpoint CONTENT, "
        "written downstream of every gradient, so it cannot move a reading.",
    },
    {
        "difference": "the arm NAME, and therefore the csv / checkpoint / adapter paths",
        "disposition": "declared-difference",
        "matched_quantity": "none — `matched_arm(seed)` is deliberately distinct from `dp_n8`",
        "evidence": "two arms sharing a path would overwrite each other's evidence. The csv lands "
        "inside MATCHED_ARTIFACT_GLOB by construction, which is what puts it under the ancestry "
        "guard; the adapter lands in gitignored `checkpoints/`, which is why (i) is scoped as it "
        "is.",
    },
    {
        "difference": "the DP seam's own object graph — DPSGD constructed on one side, None on the "
        "other",
        "disposition": "declared-difference",
        "matched_quantity": "the ARITHMETIC, which is falsified as a difference by measurement",
        "evidence": "PROBE 2 falsifies this as an ARITHMETIC difference (72/72 LoRA tensors agree "
        "to 2.178e-07 relative at σ=0 with non-binding C), and residual difference #4's premise — "
        "'σ=0 is not the control computation with a zero added to it' — is TRUE of the CODE PATH "
        "and FALSE of the ARITHMETIC. The code path is therefore declared, not equalised: the "
        "comparator cannot reach it without becoming a DP arm.",
    },
    {
        "difference": "the two end-of-run `masked_perplexity` sweeps, and the six per-seed "
        "diagnostic fields they produce",
        "disposition": "declared-difference",
        "matched_quantity": "none — ABSENT from the comparator's per-seed block",
        "evidence": "those sweeps live in `teach_persona.train_arm` (:1705 and :1709), so they do "
        "NOT run for a comparator that calls `tp.train` directly. `ppl_adapter_on`, "
        "`ppl_adapter_off`, `ppl_scored_targets`, `teaching_tokens`, `replay_tokens` and "
        "`replay_ratio` are therefore absent where the OLD control record carries them. They are "
        "diagnostics measured AFTER training ends, downstream of every weight the reading depends "
        "on, so they cannot move a reading — and adding them would spend scoring time the 23-17 "
        "budget does not hold. Declared here so their absence is a pinned expectation rather than "
        "a surprise a later reader reads as a truncated run.",
    },
)


# =================================================================================================
# ===== (i) ONE ATTEMPT — stated at its TRUE strength, which is weaker than it sounds =====
# =================================================================================================


def prove_first_attempt(tracked):
    """ONE ATTEMPT: refuse if any matched artifact is already TRACKED.

    ``tracked`` is the caller's ``git ls-files MATCHED_ARTIFACT_GLOB`` result. This module runs no
    subprocess.

    **THE MESSAGE STATES THE GUARANTEE AT ITS TRUE STRENGTH, NOT A STRONGER ONE**, because an
    OVERCLAIMED GUARANTEE IS PRECISELY THE DEFECT THIS MODULE EXISTS TO PREVENT — and this
    particular claim has already been overstated twice. Four scope clauses, all four in the
    message, none of them softened.
    """
    _prove(
        not tracked,
        "ONE ATTEMPT — REFUSED. A protocol-matched artifact is ALREADY TRACKED: "
        f"{sorted(tracked)}. The comparator's protocol was pre-registered BLIND, while "
        f"`git ls-files {MATCHED_ARTIFACT_GLOB}` returned nothing. A SECOND attempt with the "
        "first one's reading on screen is exactly the freedom that pre-registration spends.\n"
        "\n"
        "THE SCOPE OF THIS RULE, STATED AT ITS TRUE STRENGTH — FOUR CLAUSES, NOT THREE:\n"
        "\n"
        "  (1) IT BINDS ACROSS COMMITS, AND ONLY THERE. Once a matched artifact is TRACKED, no "
        "second protocol can be attempted without a VISIBLE DELETION in git history. But it does "
        "NOT bind inside the UNCOMMITTED WINDOW between 23-17's run and 23-17's commit: "
        "`.gitignore:17` ignores `data/` and `.gitignore:14` ignores `checkpoints/`, so an "
        "operator could delete `results/phase23_matched_control*`, the seed checkpoints and the "
        "`matched` section of `data/phase23_run_state.json` and leave NO RESIDUE THIS FUNCTION CAN "
        "SEE. (`data/phase23_run_state.json` is force-tracked despite `.gitignore:17` — that "
        "changes what a LATER READER can see, not what this function can. See clause 3.)\n"
        "\n"
        "  (2) IN THAT WINDOW, 23-17's `prior_scored_seeds_at_start` REFUSAL COVERS ONLY HALF THE "
        "ESCAPE. It reads the state file's `matched` section for SCORED seeds, so it refuses a "
        "delete that leaves that section INTACT (`scored == ['1337', ...]` with the record absent "
        "-> refused). **A DELETE THAT ALSO REMOVES THAT SECTION IS PREVENTED BY NOTHING**: `prior` "
        "reads {}, `scored` reads [], and a full second attempt is INDISTINGUISHABLE FROM A FIRST "
        "AT RUN TIME. Both recorded lists read [] either way, so the artifact discloses nothing "
        "about which it was.\n"
        "\n"
        "  (3) THAT FULL-DELETE CASE IS **NOT PREVENTED, BUT AUDITABLE AFTER THE FACT** — both "
        "halves, in the same breath. `data/phase23_run_state.json` is TRACKED as of `cfa2c87` "
        "(`git add -f`; tracking overrides `.gitignore:17`) and the committed baseline carries "
        "`control`, `cost`, `never_taught` and `sigma_zero` and NO `matched` section — measured. "
        "So once 23-17's same-session commit lands that section in history, a later deletion of it "
        "is a VISIBLE DIFF against that commit. **THE HONEST LIMIT: tracking is NOT RETROACTIVE ON "
        "ITS OWN.** Between the run and that commit a `git checkout -- "
        "data/phase23_run_state.json` reverts the working tree and leaves NO HISTORY AT ALL, so "
        "AUDITABILITY BEGINS ONLY AT THE COMMIT. The same-session commit requirement is therefore "
        "still load-bearing: it is now what CONVERTS the residual from INVISIBLE to AUDITABLE, "
        "rather than being its only bound. It remains a **DISCIPLINE, NOT A MECHANISM**. This is "
        "not 'closed', it implies no real-time prevention, and no new guard is invented here to "
        "make it sound closed.\n"
        "\n"
        "  (4) IT IS SCOPED TO ONE FILENAME GLOB. A comparator renamed to "
        "`results/phase23_rematch_*` is NOT REFUSED by this function. What raises its cost is that "
        "this module is EDIT-ONCE from 23-17's first artifact, so a second comparator would have "
        "to arrive with a NEW pre-registration. That is **VISIBLE, NOT REFUSED** — and the "
        "difference between those two words is the whole content of this clause.\n"
        "\n"
        "D-04's halt has no override flag and this rule has none either. If the re-test breaches, "
        "THE FINDING IS THE DELIVERABLE.",
    )
    return True


# =================================================================================================
# ===== (j) THE VISIBILITY DISCLOSURE — a REQUIRED FIELD OF BOTH RECORDS =====
# =================================================================================================

SIGMA_ZERO_VISIBILITY_DISCLOSURE = """\
THE σ=0 READING WAS ALREADY VISIBLE WHEN THIS COMPARATOR'S PROTOCOL WAS DESIGNED.

`results/phase23_sigma_zero.json` was committed BEFORE this protocol existed, and its reading
0.7837301587301587 (790/1008, seed 1337) was on screen throughout the design of the protocol this
record reports. That is disclosed here rather than inferred later.

WHAT REMAINS BLIND, all pinned at `c7de5d4` and byte-unchanged since:
  * the reduction            — `phase23_prereg.noise_floor` (the range, max - min)
  * the central-reading pin  — `control_readings[0]`, the reading at the FIRST recorded seed
  * the verdict              — `phase23_prereg.sigma_zero_verdict`, no warning branch, no override
  * the seed ladder          — `phase23_run.SEED_LADDER`

WHAT IS **NOT** BLIND: the choice of WHICH MECHANISMS TO EQUALISE. That choice was made with the
σ=0 number visible, and it is the last remaining degree of freedom in this comparison. It is pinned
in `scripts/phase23_matched_prereg.py`, committed while `git ls-files 'results/phase23_matched_*'`
returned NOTHING — which is what converts "not tuned to the number" from a claim in a paragraph
into a fact about git's object graph.

AND THAT FACT IS LIMITED, IN EXACTLY FOUR WAYS (`prove_first_attempt`, restated in full because a
disclosure that omits a scope clause is the overclaim it exists to prevent):

  (1) THE UNCOMMITTED WINDOW. The one-attempt rule binds ACROSS COMMITS only. Between 23-17's run
      and 23-17's commit it does not bind at all: `.gitignore:17` ignores `data/` and
      `.gitignore:14` ignores `checkpoints/`.

  (2) THE FULL-DELETE CASE IS PREVENTED BY NOTHING IN REAL TIME. 23-17's
      `prior_scored_seeds_at_start` refuses a delete that leaves the state file's `matched` section
      INTACT. A delete that ALSO removes that section reads `prior = {}` and `scored = []`, and is
      INDISTINGUISHABLE FROM A FIRST ATTEMPT at run time.

  (3) THAT SAME CASE IS AUDITABLE AFTER THE FACT — BUT ONLY FROM THE SAME-SESSION COMMIT ONWARD.
      `data/phase23_run_state.json` is tracked as of `cfa2c87` with a baseline carrying NO
      `matched` section, so a later deletion of that section is a VISIBLE DIFF against the commit
      that landed it. TRACKING IS NOT RETROACTIVE: before that commit a `git checkout --` leaves no
      history at all. So the same-session commit is what CONVERTS this residual from invisible to
      auditable — it is a DISCIPLINE, NOT A MECHANISM, and this is not "closed".

  (4) ONE GLOB. A comparator renamed to `results/phase23_rematch_*` is not refused. The edit-once
      property raises its cost to "arrive with a NEW pre-registration", which is VISIBLE, not
      REFUSED.
"""

# The keys 23-19's verdict record must carry. ENUMERATED HERE rather than guessed downstream: this
# module is EDIT-ONCE from 23-17's first artifact, so a key added later CANNOT LAND. Every name is
# drawn from what 23-19 already writes; 23-19 writing a SUPERSET is fine and expected.
VERDICT_REQUIRED_KEYS = (
    "record",
    "verdict",
    "verdict_rule",
    "halt_message",
    "reading",
    "control_readings",
    "central_reading",
    "central_reading_seed",
    "deviation",
    "floor",
    "floor_provenance",
    "sigma_zero_was_re_run",
    "sigma_zero_was_visible",
    "sigma_zero_visibility_disclosure",
)


def prove_verdict_record_declares_visibility(record):
    """Refuse 23-19's verdict record unless it carries EVERY ``VERDICT_REQUIRED_KEYS`` name.

    Checking the WHOLE tuple here — not only the two visibility keys — is what puts the refusal in
    the MODULE rather than only in a test. A test can be deleted by the same commit that drops a
    key; a module-level refusal travels with every consumer that imports it.
    """
    has_keys = hasattr(record, "keys")
    missing = [key for key in VERDICT_REQUIRED_KEYS if key not in record] if has_keys else []
    _prove(
        has_keys and not missing,
        f"the verdict record is missing required key(s): {missing or 'not a mapping'}. "
        f"VERDICT_REQUIRED_KEYS is {VERDICT_REQUIRED_KEYS} and this module is EDIT-ONCE from "
        "23-17's first matched artifact, so a key omitted here cannot be added later — the record "
        "would be permanently short of the fields its own pre-registration requires",
    )
    _prove(
        record["sigma_zero_was_visible"] is True,
        f"the verdict record declares sigma_zero_was_visible="
        f"{record['sigma_zero_was_visible']!r}, which is not True. The σ=0 reading "
        "0.7837301587301587 WAS visible when this comparator's protocol was designed. That is a "
        "fact about the repository, not a judgement, and a record that denies it or leaves it "
        "unstated is a record whose reader never learns it",
    )
    return True


def prove_control_record_declares_visibility(record):
    """The same refusal for 23-17's CONTROL record, and it is not redundant.

    `results/phase23_matched_control.json` is the artifact whose PROTOCOL was designed with
    ``0.7837301587301587`` on screen. **A disclosure that does not travel with the artifact it is
    about is a disclosure a reader of that artifact never sees** — a reader who opens the control
    record and never opens the verdict record would otherwise get the protocol with no disclosure
    at all.
    """
    has_keys = hasattr(record, "keys")
    missing = [
        key
        for key in ("sigma_zero_was_visible", "sigma_zero_visibility_disclosure")
        if key not in record
    ]
    _prove(
        has_keys and not missing,
        f"the matched CONTROL record is missing required key(s): {missing or 'not a mapping'}. "
        f"{MATCHED_CONTROL_RECORD} is the artifact whose PROTOCOL was designed with the σ=0 "
        "reading on screen, so the disclosure must travel with IT and not only with the verdict "
        "record — a reader of this record would otherwise never see it",
    )
    _prove(
        record["sigma_zero_was_visible"] is True,
        f"the matched control record declares sigma_zero_was_visible="
        f"{record['sigma_zero_was_visible']!r}, which is not True",
    )
    disclosure = record["sigma_zero_visibility_disclosure"]
    _prove(
        isinstance(disclosure, str) and disclosure.strip(),
        f"the matched control record's sigma_zero_visibility_disclosure is {disclosure!r}, which "
        "is empty or not a string. An empty disclosure field satisfies a key check and discloses "
        "nothing, which is worse than an absent one because it looks answered",
    )
    return True


# =================================================================================================
# ===== (l) THE SELF-CHECK — every refusal WATCHED FIRING, against CONSTRUCTED inputs =====
#
# SYNTHETIC THROUGHOUT and labelled so: NO Phase-23 matched arm exists yet. This module lands in
# wave 9 while `git ls-files 'results/phase23_matched_*'` returns nothing, which is the point.
# =================================================================================================

if __name__ == "__main__":  # pragma: no cover - self-check, not a test suite
    # `_prove` and not `assert`, for the `python -O` reason the register above records.

    def _refused(fn, *args):
        try:
            fn(*args)
        except SystemExit as refusal:
            return str(refusal)
        raise SystemExit(
            f"[phase23_matched_prereg] {fn.__name__} did NOT refuse — the guard is a "
            "comment, not a mechanism"
        )

    # SYNTHETIC `loop.py`-shaped source carrying exactly the seven declared branches.
    _SEVEN = """
def _optimizer_step(dp_fn):
    if dp_fn is not None:
        a()
    x = 1 if dp_fn is not None else 2
    if dp_fn is not None:
        c()
    if dp_fn is None:
        clip()

def _dp_extra(dp_fn):
    if dp_fn is None:
        return {}

def train(dp_fn, ckpt):
    if dp_fn is None and ckpt.get("dp_noise_rng") is not None:
        pass
    if dp_fn is not None and ckpt.get("dp_noise_rng") is not None:
        pass
"""
    _census = prove_branch_ledger_complete(_SEVEN)
    _prove(sum(_census.values()) == 7, f"the synthetic ledger summed to {sum(_census.values())}")
    print(
        f"[phase23_matched_prereg] 1/7 SYNTHETIC seven-branch census ADMITTED: "
        f"{sum(_census.values())} branches"
    )

    _PLANTED = _SEVEN.replace(
        "    if dp_fn is None:\n        clip()",
        "    if dp_fn is None:\n        clip()\n    if dp_fn is None:\n        extra()",
    )
    _msg = _refused(prove_branch_ledger_complete, _PLANTED)
    _prove("UNDECLARED" in _msg, f"the planted-branch refusal omits UNDECLARED: {_msg!r}")
    print(f"[phase23_matched_prereg] 2/7 PLANTED extra branch REFUSED:\n{_msg}")

    _REMOVED = _SEVEN.replace("    if dp_fn is None:\n        clip()\n", "")
    _msg = _refused(prove_branch_ledger_complete, _REMOVED)
    _prove("MISSING" in _msg, f"the removed-branch refusal omits MISSING: {_msg!r}")
    print(f"[phase23_matched_prereg] 3/7 REMOVED branch REFUSED:\n{_msg}")

    # SYNTHETIC `teach_persona.py`-shaped source, with `replay_windows` DROPPED from dp_kwargs.
    _TP_SHORT = """
def train_arm(is_dp):
    dp_accum = dict(grad_accum_steps=8) if is_dp else {}
    dp_kwargs = (
        dict(fact_bin=1, n_facts=2, replay_bin=3, replay_mask_bin=4, dp_fn=5) if is_dp else {}
    )
"""
    _msg = _refused(prove_dp_wiring_keys, _TP_SHORT)
    _prove("replay_windows" in _msg, f"the dropped-kwarg refusal omits the name: {_msg!r}")
    print(f"[phase23_matched_prereg] 4/7 DROPPED dp_kwarg REFUSED:\n{_msg}")

    # SYNTHETIC `train_arm`-shaped source whose train(...) call carries ONE extra keyword.
    _TP_EXTRA = """
def train_arm(is_dp):
    dp_accum = dict(grad_accum_steps=8) if is_dp else {}
    dp_kwargs = (
        dict(
            fact_bin=1, n_facts=2, replay_bin=3, replay_mask_bin=4, replay_windows=5, dp_fn=6
        )
        if is_dp
        else {}
    )
    final = train(
        train_config=1, runtime_config=2, model=3, model_config=4, train_bin=5,
        train_mask_bin=6, val_bin=7, val_mask_bin=8, penalty_fn=9, log_path=10,
        eval_interval=11, checkpoint_path=12, checkpoint_interval=13, resume_from=14,
        return_final_loss=15, extra_eval_fns=None, **dp_kwargs,
    )
"""
    _msg = _refused(prove_train_call_keys, _TP_EXTRA)
    _prove("extra_eval_fns" in _msg, f"the extra-keyword refusal omits the name: {_msg!r}")
    print(f"[phase23_matched_prereg] 5/7 ADDED train() keyword REFUSED:\n{_msg}")

    _msg = _refused(prove_first_attempt, [MATCHED_CONTROL_RECORD])
    for _clause in ("(1)", "(2)", "(3)", "(4)", "PREVENTED BY NOTHING", "NOT RETROACTIVE"):
        _prove(_clause in _msg, f"the one-attempt refusal omits {_clause!r}: {_msg!r}")
    _prove(prove_first_attempt([]) is True, "an EMPTY tracked list must not be refused")
    print(f"[phase23_matched_prereg] 6/7 SECOND ATTEMPT REFUSED (empty list admitted):\n{_msg}")

    _RECORD = {key: None for key in VERDICT_REQUIRED_KEYS}
    _RECORD["sigma_zero_was_visible"] = True
    _prove(
        prove_verdict_record_declares_visibility(_RECORD) is True, "a complete record was refused"
    )
    _SHORT = {k: v for k, v in _RECORD.items() if k != "central_reading_seed"}
    _msg = _refused(prove_verdict_record_declares_visibility, _SHORT)
    _prove("central_reading_seed" in _msg, f"the short-record refusal omits the key: {_msg!r}")
    _CONTROL = {"sigma_zero_was_visible": True, "sigma_zero_visibility_disclosure": "x"}
    _prove(
        prove_control_record_declares_visibility(_CONTROL) is True,
        "a complete control record was refused",
    )
    _msg2 = _refused(
        prove_control_record_declares_visibility, {"sigma_zero_visibility_disclosure": "x"}
    )
    print(
        f"[phase23_matched_prereg] 7/7 RECORD refusals fired — verdict:\n{_msg}\n"
        f"  control:\n{_msg2}"
    )
