"""CAL-01 / CAL-05 — the cost record's SHAPE and its REFUSALS, built BEFORE any number exists.

Nothing in this module measures anything. It is the schema, the four refusals that make CAL-05's
*floor, not mean* a PROPERTY of the artifact rather than a note beside it, the ceiling-sized sweep
sizing function, and the synchronize-bracketed timing helper. 23-10 and 23-11 fill the schema;
23-13 sizes Z through ``size_sweep``.

**WHY THE SHAPE LANDS BEFORE THE NUMBERS.** ``23-RESEARCH.md`` §R3.B names three mechanisms for
making *floor, not mean* structural, in increasing strength, and all three are here:

  1. **DISTINCT FIELD NAMES.** ``h_per_point_floor`` (stop ids ACTIVE — the Phase-18 condition, in
     which 45-56 of 64 draws per shape terminated early) and ``h_per_point_ceiling`` (stop set
     EMPTIED — the worst case a heavily-noised adapter that stops emitting EOS produces, running
     the full ``RECALL_MAX_NEW_TOKENS`` every draw) are two separate REQUIRED keys, and
     ``FORBIDDEN_MEAN_KEYS`` refuses a bare mean at ANY nesting depth. A consumer physically cannot
     read a mean off a record that contains no mean.
  2. **A ``_prove``-STYLE REFUSAL IN THE CONSUMER.** ``size_sweep`` REFUSES a record without a
     ceiling rather than falling back to the floor. The shape is
     ``scripts/phase20_gate_coverage.py:413``'s ``_prove_retention_floor``: name the missing
     quantity and state what an unlabelled number is indistinguishable from.
  3. **SIZING AGAINST THE CEILING.** See ``size_sweep``'s docstring for the ratchet reason.

**THE TIMING DISCIPLINE, AND WHERE IT IS AND IS NOT OPTIONAL** (``23-RESEARCH.md`` §R3.A,
`[MEASURED]`). ``src/personacore/generation/core.py:79`` does ``tok = int(next_id)`` once per
generated token — a device-to-host sync — so the generation loop is ALREADY implicitly synchronized
every token and Phase 18's committed rates in ``results/phase18_preflight_report.md`` are honest.
**Training has no per-step host sync at all**, which is why the explicit
``torch.mps.synchronize()`` at both boundaries is not optional there: an unsynchronized bracket
around queued MPS work measures submission, not completed work.

``torch`` is imported **lazily, inside ``time_iterations`` only** — the ``phase21_filler`` lazy
sibling-import precedent — so the schema half of this module stays importable in a torch-free
context and the module is honest about which half needs a device. The refusals use ``_prove`` /
``SystemExit`` and never ``assert``: ``python -O`` strips ``assert`` outright and this module is
almost entirely refusals.

This module is NOT edit-once. ``scripts/phase23_prereg.py`` is, which is why every artifact path
here is RESOLVED from that register rather than retyped.
"""

import math
import sys
from pathlib import Path

_SCRIPTS = str(Path(__file__).resolve().parent)
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import phase23_prereg  # noqa: E402  (needs the sys.path insert above)

# THE ARTIFACT PATH, RESOLVED — never retyped. `scripts/phase23_prereg.py` is the phase's SINGLE
# SOURCE of every path it writes, and it is edit-once, so a literal here could drift away from the
# register with nothing to catch it. This repository has shipped plans naming artifact paths the
# code refuses; `test_the_cost_record_path_comes_from_the_prereg_register` AST-scans this file for
# stray path literals so the drift cannot recur silently.
COST_RECORD = phase23_prereg.COST_RECORD


def _prove(condition, message):
    """``SystemExit`` on a broken invariant — ``scripts/phase23_prereg.py:54``'s register."""
    if not condition:
        raise SystemExit(f"[phase23_cost] {message}")


# =================================================================================================
# ===== (a) THE REQUIRED-KEY REGISTERS =====
# =================================================================================================

# CAL-01. PREVENTS: a training figure published with no denominator and no venue. Every key here is
# REFUSED WHEN ABSENT, never defaulted — `warmup_iterations_discarded` and `timed_iterations` are
# the denominator, `max_steps`/`batch_size`/`block_size`/`grad_accum_steps`/
# `replay_micro_batches_per_step` are the SHAPE the seconds describe, and `device`/`torch_version`/
# `python_version`/`git_sha`/`seed` are the venue. A rate with no denominator is exactly the kind
# of figure this project has had to retract.
#
# `grad_accum_steps` and `replay_micro_batches_per_step` are separate keys because CAL-01's finding
# is that training is budgeted per CAPACITY, not per "arm": `scripts/teach_persona.py:1352` sets
# `grad_accum_steps = n_facts`, so ONE optimizer step costs `n_facts` backward passes PLUS
# `ceil(4 * n_facts / batch_size)` replay micro-batches. A record carrying only "seconds per arm"
# cannot show why 20.4 s (non-DP) becomes 3.79 min (dp_n8) and 29.98 min (dp_n64).
TRAINING_RECORD_KEYS = (
    "arm",
    "capacity_n_facts",
    "grad_accum_steps",
    "replay_micro_batches_per_step",
    "max_steps",
    "batch_size",
    "block_size",
    "seconds_total",
    "seconds_per_optimizer_step",
    "warmup_iterations_discarded",
    "timed_iterations",
    "device",
    "torch_version",
    "python_version",
    "git_sha",
    "seed",
    "dp_seam_active",
)

# CAL-05. PREVENTS: the floor being read as a mean, and either bracket end being published without
# the stop-rate condition that produced it. `stop_terminated_n_floor` / `stop_terminated_n_ceiling`
# sit beside their h/point key precisely because the stop rate IS the quantity the bracket exists
# to expose — a noised adapter that stops emitting EOS is the whole reason the ceiling is not the
# floor. `draws_per_point`, `k_per_question`, `questions` and `n_draws_measured` make the
# arithmetic auditable from the record alone.
GENERATION_RECORD_KEYS = (
    "h_per_point_floor",
    "h_per_point_ceiling",
    "wall_multiplier",
    "token_multiplier",
    "draws_per_point",
    "k_per_question",
    "questions",
    "n_draws_measured",
    "stop_terminated_n_floor",
    "stop_terminated_n_ceiling",
    "mean_tokens_floor",
    "mean_tokens_ceiling",
    "attack_shapes",
    "adapter_source",
    "sigma",
    "device",
    "torch_version",
    "git_sha",
)

_REQUIRED_KEYS_BY_KIND = {
    "training": TRAINING_RECORD_KEYS,
    "generation": GENERATION_RECORD_KEYS,
}


# =================================================================================================
# ===== (b) THE FORBIDDEN-KEY REGISTER =====
# =================================================================================================

# CAL-05'S REASON, stated as data rather than as a comment beside a hopeful convention: a consumer
# physically cannot read a mean off a record that contains no mean. A single bare per-point-cost
# field anywhere in a Phase-23 artifact is the warning sign `23-RESEARCH.md` Pitfall 5 names —
# "sizing Z against the floor" — and by the time a reader notices, Z is already sized.
#
# THE RATE KEY IS FORBIDDEN AS A *BARE* KEY, not as a quantity. It is the measurement whose
# stop-rate dependence the floor/ceiling split exists to expose, so a per-condition rate must be
# named `..._floor` / `..._ceiling`; an unsuffixed one asserts a condition it did not measure.
#
# Both forms of the mean are listed because a record can smuggle one in under either word order,
# and the walk below refuses them at ANY nesting depth — a nested one is the same defect, reached
# by a longer path.
FORBIDDEN_MEAN_KEYS = (
    "h_per_point",
    "draws_per_min",
    "mean_h_per_point",
    "h_per_point_mean",
)


# =================================================================================================
# ===== (c) THE REFUSALS =====
# =================================================================================================


def _walk_items(node, path=()):
    """Yield ``(path, key, value)`` for every key of every mapping reachable from ``node``.

    A top-level ``in`` would see the top level only, and a forbidden key one level down is the SAME
    defect reached by a longer path. Sequences are descended too, because a list of per-shape
    sub-records is the obvious place for one to hide.
    """
    if hasattr(node, "keys"):
        for key in node:
            yield path, key, node[key]
            yield from _walk_items(node[key], (*path, str(key)))
    elif isinstance(node, (list, tuple)):
        for index, item in enumerate(node):
            yield from _walk_items(item, (*path, str(index)))


def _walk_leaves(node, path=()):
    """Yield ``(path, value)`` for every non-container leaf reachable from ``node``."""
    if hasattr(node, "keys"):
        for key in node:
            yield from _walk_leaves(node[key], (*path, str(key)))
    elif isinstance(node, (list, tuple)):
        for index, item in enumerate(node):
            yield from _walk_leaves(item, (*path, str(index)))
    else:
        yield path, node


def _dotted(path, key=None):
    """A readable location for a refusal message — ``"generation.shapes.0.field"``."""
    return ".".join((*path, str(key))) if key is not None else ".".join(path) or "<record>"


def validate_record(record, *, kind):
    """Refuse a cost record that is incomplete, carries a bare mean, or brackets the wrong way.

    Returns ``None``; its whole output is the refusal. ``kind`` is keyword-only and has no default,
    because a record validated against the wrong register is worse than one not validated at all.

    FOUR REFUSALS, in order:

      1. **A MISSING REQUIRED KEY IS REFUSED, NEVER DEFAULTED** (CAL-01). A default would publish a
         rate whose denominator, device or commit nobody stated, and an unlabelled number is
         indistinguishable from a borrowed one — ``scripts/phase20_gate_coverage.py``'s D-14(a)
         reasoning, restated for the record that prices this phase's sweep.
      2. **A ``FORBIDDEN_MEAN_KEYS`` MEMBER AT ANY DEPTH IS REFUSED** (CAL-05). See that register.
      3. **A NON-FINITE NUMBER ANYWHERE IS REFUSED.** A NaN cost compares ``False`` against every
         budget bound, so it does not fail a sizing check — it PASSES one, silently.
      4. **A CEILING BELOW ITS FLOOR IS REFUSED** (generation only). That ordering inversion is a
         unit or condition mix-up, and it would size Z in the one direction the K ratchet cannot
         rescue (see ``size_sweep``).
    """
    _prove(
        kind in _REQUIRED_KEYS_BY_KIND,
        f"kind {kind!r} is not one of {tuple(_REQUIRED_KEYS_BY_KIND)}. A record validated against "
        "the wrong register is worse than an unvalidated one: it reports a pass it never earned",
    )
    required = _REQUIRED_KEYS_BY_KIND[kind]

    _prove(
        hasattr(record, "keys"),
        f"the {kind} record is {record!r}, which is not a mapping and therefore carries no "
        "provenance at all",
    )
    missing = [key for key in required if key not in record]
    _prove(
        not missing,
        f"the {kind} record is MISSING {missing!r}. Every key in {required} is REQUIRED and a "
        "missing one is REFUSED, never defaulted: a rate with no denominator, no venue and no "
        "commit is exactly the kind of figure this project has had to retract, and a default would "
        "manufacture the missing label rather than expose its absence",
    )

    for path, key, _value in _walk_items(record):
        _prove(
            key not in FORBIDDEN_MEAN_KEYS,
            f"the {kind} record carries {key!r} at {_dotted(path, key)}. Every member of "
            f"{FORBIDDEN_MEAN_KEYS} is REFUSED at any nesting depth (CAL-05): the per-point cost "
            "is a FLOOR-to-CEILING bracket whose two ends were measured under different stop "
            "conditions, so a single unsuffixed field asserts a mean that was never measured — and "
            "a consumer physically cannot read a mean off a record that contains no mean. Name it "
            "with a `_floor` or `_ceiling` suffix and record its stop count beside it",
        )

    for path, value in _walk_leaves(record):
        _prove(
            not (isinstance(value, float) and not math.isfinite(value)),
            f"the {kind} record's {_dotted(path)} is {value!r}, which is not finite. A non-finite "
            "cost compares False against every budget bound, so it does not FAIL a sizing check — "
            "it passes one, and the sweep is sized on a number nobody can interpret",
        )

    if kind == "generation":
        floor = record["h_per_point_floor"]
        ceiling = record["h_per_point_ceiling"]
        for name, value in (("h_per_point_floor", floor), ("h_per_point_ceiling", ceiling)):
            _prove(
                isinstance(value, (int, float)) and not isinstance(value, bool),
                f"the generation record's {name} is {value!r}, which is not a number. The bracket "
                "is arithmetic and a non-numeric end cannot be compared, let alone sized against",
            )
        _prove(
            ceiling >= floor,
            f"the generation record brackets BACKWARDS: h_per_point_ceiling {ceiling!r} is below "
            f"h_per_point_floor {floor!r}. The ceiling is the stop-disabled condition and the "
            "floor the stop-active one, so the ceiling cannot be cheaper — a unit or condition "
            "mix-up, and sizing Z on it would under-budget the sweep in the ONE direction the K "
            "ratchet at `scripts/mitigation_gate.py:918` cannot rescue",
        )


# =================================================================================================
# ===== (d) THE CEILING-SIZED SWEEP SIZING =====
# =================================================================================================


def size_sweep(*, generation_record, sweep_points, k):
    """Project a sweep's wall clock **from the CEILING**, recording the floor-derived figure beside.

    **WHY THE CEILING, AND NOT THE FLOOR OR SOMETHING BETWEEN THEM.** The K ratchet at
    ``scripts/mitigation_gate.py:918`` (``ratchet_k``, over the closed menu ``K_RUNGS`` at ``:254``,
    whose own comment at ``:250`` reads *"a selected rung may only INCREASE, never decrease"*) has
    no cheap direction. A sweep sized against the floor and then found too expensive **cannot be
    rescued by reducing K** — the ratchet forbids it, deliberately, because fewer draws is less
    power to observe extraction, i.e. an easier null. Sizing against the ceiling is therefore the
    only direction the ratchet permits, and the floor is reported BESIDE the projection as
    disclosure rather than as an alternative to it.

    A floor-only record raises before any arithmetic happens. The refusal is the point: falling
    back to the floor when the ceiling is absent is precisely the failure CAL-05 names, and it
    would be invisible in the output. The MISSING CEILING gets its own refusal ahead of
    ``validate_record``'s generic missing-key list, because it is the one absence whose consequence
    a reader must be told: every other missing key costs a label, this one costs the budget in the
    direction the ratchet cannot undo.

    **THE K SCALING, AND ITS ONE ASSUMPTION, STATED.** ``draws_per_point`` is NOT ``questions * k``:
    the Phase-18 shape mixes K-scaled attack families with a fixed-draw family zero. So the draw
    count at another rung is the record's own measured count plus the K-scaled part's delta::

        draws_at_k = draws_per_point + questions * (k - k_per_question)

    where ``questions`` is the count of prompts whose draw budget scales with K. That reproduces
    ``.planning/REQUIREMENTS.md:177-182``'s committed table EXACTLY at every ``K_RUNGS`` entry
    (42,480 / 21,744 / 14,832 / 7,920 draws at K = 48 / 24 / 16 / 8), which the self-check below
    demonstrates rather than asserts in prose. Hours then scale with the draw count, because
    generation is a per-token Python loop at batch 1 and wall clock is close to linear in draws at
    fixed prefill (``23-RESEARCH.md`` §R3.B).
    """
    _prove(
        hasattr(generation_record, "keys") and "h_per_point_ceiling" in generation_record,
        "the generation record has no h_per_point_ceiling, so this sizing REFUSES rather than "
        "falling back to h_per_point_floor. The K ratchet at `scripts/mitigation_gate.py:918` "
        "(`ratchet_k`, over the closed menu `K_RUNGS` at `:254`) only lets a selected rung "
        "INCREASE, never decrease — so a sweep sized against the floor and then found too "
        "expensive has NO rescue in the cheap direction, and the under-budgeting would be "
        "invisible in this function's output. A floor read as a mean is exactly what CAL-05 "
        "exists to prevent",
    )
    validate_record(generation_record, kind="generation")

    for name, value in (("sweep_points", sweep_points), ("k", k)):
        _prove(
            isinstance(value, int) and not isinstance(value, bool) and value > 0,
            f"{name} is {value!r}, which is not a positive integer. A sweep with a fractional or "
            "non-positive count is not a sweep, and a budget projected from one is arithmetic "
            "about nothing",
        )

    measured_draws = generation_record["draws_per_point"]
    questions = generation_record["questions"]
    measured_k = generation_record["k_per_question"]
    for name, value in (
        ("draws_per_point", measured_draws),
        ("questions", questions),
        ("k_per_question", measured_k),
    ):
        _prove(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
            and value > 0,
            f"the generation record's {name} is {value!r}, which is not a finite positive number. "
            "The K scaling is a ratio of draw counts and none of its three terms may be absent, "
            "zero or unmeasurable — a projection built on one is a figure with no denominator",
        )

    draws_at_k = measured_draws + questions * (k - measured_k)
    _prove(
        draws_at_k > 0,
        f"K={k} projects {draws_at_k!r} draws per point from a record measured at "
        f"K={measured_k!r} over {questions!r} K-scaled questions. A non-positive draw count means "
        "the requested rung is below what the record's fixed-draw families already cost, so the "
        "linear scaling does not describe it and no honest projection is available",
    )

    scale = draws_at_k / measured_draws
    ceiling_at_k = generation_record["h_per_point_ceiling"] * scale
    floor_at_k = generation_record["h_per_point_floor"] * scale
    return {
        "sweep_points": sweep_points,
        "k": k,
        "draws_per_point_at_k": draws_at_k,
        "h_per_point_ceiling_at_k": ceiling_at_k,
        "h_per_point_floor_at_k": floor_at_k,
        # THE PROJECTION. Sized against the ceiling; the floor-derived figure is recorded beside it
        # as disclosure, never as an alternative the consumer may pick.
        "projected_hours": sweep_points * ceiling_at_k,
        "floor_hours": sweep_points * floor_at_k,
        "sized_against": "h_per_point_ceiling",
    }


# =================================================================================================
# ===== (e) THE TIMING HELPER =====
# =================================================================================================

# `23-RESEARCH.md` §R3.A, `[MEASURED]` in this session's probes: 3-4 discarded warm-up iterations
# were enough for the per-micro-step figure to stabilize on MPS (the first MPS kernels of a process
# pay lazy compilation and allocator warm-up). 4 is the smallest count above that observation, and
# 20 timed iterations is the smallest denominator worth publishing.
_MIN_WARMUP_ITERATIONS = 4
_MIN_TIMED_ITERATIONS = 20


def time_iterations(fn, *, device, warmup=_MIN_WARMUP_ITERATIONS, iterations=_MIN_TIMED_ITERATIONS):
    """Time ``fn`` and return the mean **and the count** — never the mean alone.

    ``torch.mps.synchronize()`` is called immediately before ``t0`` and immediately before ``t1``
    whenever ``device`` is MPS. See this module's docstring for the measured reason it is optional
    for generation (``generation/core.py:79`` syncs per token) and **not** optional for training,
    which has no per-step host sync at all: an unsynchronized bracket around queued MPS work times
    submission, not completed work.

    ``torch`` is imported HERE rather than at module scope, and after the refusals, so the schema
    half of this module stays importable without torch and a too-small iteration count is refused
    without touching a device.

    The returned mapping's keys are the names ``TRAINING_RECORD_KEYS`` requires, so a caller
    records the denominator by construction rather than by remembering to.
    """
    for name, value, floor in (
        ("warmup", warmup, _MIN_WARMUP_ITERATIONS),
        ("iterations", iterations, _MIN_TIMED_ITERATIONS),
    ):
        _prove(
            isinstance(value, int) and not isinstance(value, bool) and value >= floor,
            f"{name}={value!r} is below the required minimum of {floor}. A rate with no "
            "denominator is exactly the kind of figure this project has had to retract, and a "
            "denominator this small is one: 3-4 discarded warm-up iterations were MEASURED as the "
            "point where the per-micro-step figure stabilizes on MPS, so a shorter warm-up times "
            "lazy kernel compilation and a shorter run reports allocator noise as work",
        )
    _prove(callable(fn), f"fn is {fn!r}, which is not callable — there is nothing here to time")

    import time

    import torch

    on_mps = device == "mps"
    for _ in range(warmup):
        fn()
    if on_mps:
        torch.mps.synchronize()
    t0 = time.perf_counter()
    for _ in range(iterations):
        fn()
    if on_mps:
        torch.mps.synchronize()
    t1 = time.perf_counter()

    seconds_total = t1 - t0
    return {
        "seconds_total": seconds_total,
        "seconds_per_iteration": seconds_total / iterations,
        "timed_iterations": iterations,
        "warmup_iterations_discarded": warmup,
        "device": device,
    }


# =================================================================================================
# ===== (f) THE SELF-CHECK — the refusals as RUNNABLE EVIDENCE =====
# =================================================================================================

# Every value is the literal string SYNTHETIC unless a check needs arithmetic from it. That is
# deliberate and it is the whole safeguard: NO PHASE-23 COST NUMBER EXISTS YET (23-11 measures
# them), so a self-check fixture carrying plausible-looking hours would be a fabricated figure
# sitting one copy-paste away from an artifact.
_SYNTHETIC = "SYNTHETIC"


def _synthetic_record(kind, **overrides):
    """A record with every required key present and every unspecified value the literal SYNTHETIC.

    Used by the self-check below and by ``tests/test_phase23_cost.py``. Resolving the key set from
    ``_REQUIRED_KEYS_BY_KIND`` rather than hand-listing it is what lets a test assert the REGISTER
    and not merely one hand-built instance: a key dropped from the register would otherwise be
    dropped from the fixture in the same motion and nothing would notice.
    """
    _prove(
        kind in _REQUIRED_KEYS_BY_KIND,
        f"kind {kind!r} is not one of {tuple(_REQUIRED_KEYS_BY_KIND)}",
    )
    record = dict.fromkeys(_REQUIRED_KEYS_BY_KIND[kind], _SYNTHETIC)
    record.update(overrides)
    return record


if __name__ == "__main__":  # pragma: no cover - self-check, not a test suite
    # `scripts/phase23_prereg.py`'s register, with `_prove` in place of `assert` for the same
    # reason: `python -O` strips `assert` and would make this self-check print five lines and
    # verify nothing.

    # The DRAW GEOMETRY is committed, not synthetic: `results/phase18_preflight_report.md:71-81`
    # and `.planning/REQUIREMENTS.md:177-182`. The two HOURS are synthetic placeholders whose only
    # property under test is `ceiling > floor` — 23-11 measures the real bracket.
    _GENERATION = _synthetic_record(
        "generation",
        h_per_point_floor=1.0,
        h_per_point_ceiling=2.0,
        draws_per_point=42480,
        questions=864,
        k_per_question=48,
    )
    validate_record(_GENERATION, kind="generation")
    validate_record(_synthetic_record("training"), kind="training")
    print(
        f"[phase23_cost] 1/5 complete records validate — {len(TRAINING_RECORD_KEYS)} training / "
        f"{len(GENERATION_RECORD_KEYS)} generation keys, all present"
    )

    _DROPPED = TRAINING_RECORD_KEYS[0]
    _incomplete = _synthetic_record("training")
    del _incomplete[_DROPPED]
    try:
        validate_record(_incomplete, kind="training")
    except SystemExit as refusal:
        _message = str(refusal)
    else:
        raise SystemExit("[phase23_cost] an incomplete record was ADMITTED — CAL-01 has no default")
    _prove(_DROPPED in _message, f"the refusal does not name the dropped key: {_message!r}")
    print(f"[phase23_cost] 2/5 REFUSED a record missing {_DROPPED!r} — never defaulted")

    # The bad key is taken FROM the register, never typed: a literal here would be the very field
    # name the AST guard in `tests/test_phase23_cost.py` forbids this module to contain.
    _BARE = FORBIDDEN_MEAN_KEYS[0]
    _nested = _synthetic_record("generation", **dict(_GENERATION))
    _nested["per_shape"] = [{"shape": _SYNTHETIC, _BARE: 4.77}]
    try:
        validate_record(_nested, kind="generation")
    except SystemExit as refusal:
        _message = str(refusal)
    else:
        raise SystemExit(f"[phase23_cost] a NESTED bare {_BARE!r} was ADMITTED — the walk broke")
    _prove(_BARE in _message, f"the refusal does not name the forbidden key: {_message!r}")
    print(f"[phase23_cost] 3/5 REFUSED a bare {_BARE!r} nested at per_shape.0 — the walk has depth")

    _backwards = _synthetic_record("generation", **dict(_GENERATION))
    _backwards["h_per_point_ceiling"] = _GENERATION["h_per_point_floor"] / 2
    try:
        validate_record(_backwards, kind="generation")
    except SystemExit as refusal:
        _message = str(refusal)
    else:
        raise SystemExit("[phase23_cost] a ceiling BELOW its floor was ADMITTED")
    _prove("BACKWARDS" in _message, f"the refusal does not say BACKWARDS: {_message!r}")
    print("[phase23_cost] 4/5 REFUSED a ceiling below its floor — the unit/condition mix-up")

    # The K scaling against the committed table. `mitigation_gate.K_RUNGS` is (48, 24, 16, 8) and
    # `.planning/REQUIREMENTS.md:177-182` prices each rung; both are quoted, not imported, so this
    # module takes no dependency on the FROZEN gate.
    _COMMITTED_DRAWS = {48: 42480, 24: 21744, 16: 14832, 8: 7920}
    for _k, _expected in _COMMITTED_DRAWS.items():
        _sizing = size_sweep(generation_record=_GENERATION, sweep_points=16, k=_k)
        _prove(
            _sizing["draws_per_point_at_k"] == _expected,
            f"K={_k} projects {_sizing['draws_per_point_at_k']!r} draws/point, but "
            f"`.planning/REQUIREMENTS.md` commits {_expected}",
        )
        _prove(
            _sizing["projected_hours"] > _sizing["floor_hours"],
            f"K={_k} projected {_sizing['projected_hours']!r}h, not above the floor-derived "
            f"{_sizing['floor_hours']!r}h — the sizing is reading the wrong end of the bracket",
        )
    print(
        f"[phase23_cost] 5/5 the K scaling reproduces the committed draws/point table exactly at "
        f"every rung {tuple(_COMMITTED_DRAWS)} and sizes above the floor at each"
    )
