"""CONDITION (c)'S SIX PRODUCERS — the kwargs the 20-plan set left with none (D-45…D-50).

`scripts/mitigation_gate.py::mitigation_point_verdict` takes 21 keyword-only arguments. Measured
across all 20 committed Phase-25 plans, SEVEN had zero producers and SIX of them are condition (c):
`point_dialogue_ppl_on`, `point_dialogue_ppl_off`, `control_gap`, `gap_noise_floor`,
`point_retention_ppl`, `retention_noise_floor`. No Phase 23 point record carries any of them, so the
verdict was uncomputable. D-35's closing *"Nothing to fix"* rested on that false premise (D-51); its
ε-scoping claim is unchanged and still correct.

WHY ALL 44 POINTS, AND WHY THE COST WAS MEASURED BEFORE THE DECISION RATHER THAN ESTIMATED AFTER IT
---------------------------------------------------------------------------------------------------
Timed at HEAD on `checkpoints/persona_adapter.pt`, MPS: `dialogue_ppl_pair` (ON+OFF) 43.5 s and
`retention_perplexity` 43.9 s — 87.4 s per point, 1.07 h over 44, or 0.80 h with the OFF leg
measured once. That is 0.7-1.0% of the 107-150 h sweep budget, so cost cannot argue for a subset;
and measuring only the points that clear (a) and (b) would be a reduction chosen AFTER seeing
results, the exact move this milestone forbids everywhere else (D-45).

TWO THINGS ARRIVE FREE WITH IT
------------------------------
`prove_condition_c_reproduction` reproduces `results/phase19_arm_erased.json` EXACTLY, denominators
included, giving condition (c) a bit-level reproduction check of D-01's shape. And
`RETENTION_LEG_BINDS_AT_ANCHOR` surfaces arithmetic that has been sitting in a committed Phase 19
record and that no plan in the 20-plan set read: the retention leg ALREADY FAILS at the untouched
taught adapter. That is the instrument working, not a broken floor — and it is committed here,
before any sweep point exists, so a narrow or empty frontier can never be re-argued afterwards as a
mis-set floor.

WHAT THIS MODULE IS ALLOWED TO IMPORT, AND WHY THE LINE FALLS WHERE IT DOES
--------------------------------------------------------------------------
Stdlib plus the three FROZEN, TORCH-FREE gate modules — `mitigation_gate`, `phase20_gate_coverage`,
`erasure_gate` — at module scope. Everything that pulls torch is imported LAZILY inside the
measuring functions, so the pre-registration constants and the arithmetic helpers import on CPU with
no torch in `sys.modules` (the discipline `scripts/phase25_record.py` and `scripts/plot_phase25.py`
hold). MEASURED at authoring time: `phase19_erasure`, `phase18_extraction`, `teach_persona` and
`personacore.config` ALL put torch in `sys.modules` on import, so all four are lazy here — the
constraint is the plan's own no-torch acceptance gate, not a preference.

THE IMPORT FORM OF `retention_perplexity` IS LOAD-BEARING.
`src/personacore/evaluation/__init__.py:7` does
`from .perplexity import masked_perplexity, perplexity, retention_perplexity`, so the name
`perplexity` binds the FUNCTION and SHADOWS the submodule:
`evaluation.perplexity.retention_perplexity` raises
`AttributeError: 'function' object has no attribute 'retention_perplexity'`. The symbol is
imported directly. Its dead-id-mask policy is FROZEN under DEBT-02 and the unmasked v1.0
`perplexity` is NOT a substitute for a curve point.
"""

import inspect
import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import erasure_gate  # noqa: E402  (needs the sys.path insert above; scripts/ is not a package)
import mitigation_gate  # noqa: E402  (same)
import phase20_gate_coverage  # noqa: E402  (same)

# The three committed records this module reads. Every figure below is READ from one of them or
# COMPUTED from a frozen module; nothing is retyped. A number nobody can trace back to the artifact
# that produced it is a number nobody can correct.
ARM_ERASED_RECORD = _ROOT / "results" / "phase19_arm_erased.json"
NOISE_FLOORS_RECORD = _ROOT / "results" / "phase19_noise_floors.json"
RETENTION_FLOOR_RECORD = _ROOT / "results" / "phase20_retention_floor.json"

ADAPTER_CHECKPOINT = _ROOT / "checkpoints" / "persona_adapter.pt"


def _prove(condition, message):
    """``SystemExit`` on a broken invariant — `mitigation_gate._prove`'s register, this prefix.

    ``SystemExit`` and deliberately NOT ``assert``: an ``assert`` is strippable under ``-O``, and a
    proof that disappears under an optimisation flag is not a proof. Note for anyone writing a test
    against one of these: ``SystemExit`` derives from ``BaseException``, so
    ``pytest.raises(Exception)`` does NOT catch it.
    """
    if not condition:
        raise SystemExit(f"[phase25_condition_c] {message}")


def _read(path):
    return json.loads(path.read_text())


# ---------------------------------------------------------------------------------------------
# (a) THE FIELD CONTRACT, PINNED ONCE SO WAVE 2 CAN CONSUME IT (interface-first).
# ---------------------------------------------------------------------------------------------

CONDITION_C_FIELDS = (
    # The SIX condition-(c) keyword arguments of `mitigation_point_verdict`. Order is the gate's
    # own signature order. Plan 25-08 imports this tuple to build its record schema and plan 25-19
    # to assemble the artifact.
    "point_dialogue_ppl_on",
    "point_dialogue_ppl_off",
    "control_gap",
    "gap_noise_floor",
    "point_retention_ppl",
    "retention_noise_floor",
    # CARRIAGE fields — recorded per point, never passed to the verdict. The two denominators are
    # here because a rate without its denominator is not a reading; the three counterfactual fields
    # are D-50's obligation.
    "dialogue_n_targets",
    "retention_total_tokens",
    "counterfactual_retention_floor",
    "counterfactual_retention_cap",
    "counterfactual_retention_headroom",
)

CONDITION_C_VERDICT_FIELD_COUNT = 6


def _prove_fields_are_real_gate_kwargs():
    """Prove the six are KEYWORD-ONLY parameters of the frozen `mitigation_point_verdict`.

    Resolved through `inspect.signature`, NEVER by grepping the frozen gate: that file discusses
    every one of these names in its own prose and docstrings, so a textual check over it measures
    the documentation rather than the signature. `scripts/phase25_epsilon.py`'s module docstring
    records the same class of false-RED measured on the same file (42 textual `epsilon`
    occurrences, 0 resolving names).

    Called at MODULE SCOPE so a drifted contract fails at import rather than after the ~87 s of
    forward passes it would waste.
    """
    params = inspect.signature(mitigation_gate.mitigation_point_verdict).parameters
    for field in CONDITION_C_FIELDS[:CONDITION_C_VERDICT_FIELD_COUNT]:
        _prove(
            field in params,
            f"{field!r} is not a parameter of mitigation_gate.mitigation_point_verdict at all. "
            "This module exists to PRODUCE that gate's condition-(c) inputs; a producer for a "
            "kwarg the gate does not take produces nothing, and the verdict stays uncomputable "
            "exactly as it was across the whole 20-plan set",
        )
        _prove(
            params[field].kind is inspect.Parameter.KEYWORD_ONLY,
            f"{field!r} is a {params[field].kind} parameter, not KEYWORD_ONLY. The gate's "
            "twenty-one required keyword-only arguments are the protection: a positional slot "
            "could be filled by the wrong reading in the right position and still return a "
            "verdict",
        )


_prove_fields_are_real_gate_kwargs()


# ---------------------------------------------------------------------------------------------
# (b) THE TWO PRODUCERS — IMPORTED AND CALLED, NEVER RE-IMPLEMENTED.
# ---------------------------------------------------------------------------------------------


def measure_condition_c(model, tok, device, *, forbid, adapter_off_reading=None):
    """Condition (c)'s two readings on ONE loaded model in ONE pass. The measured cost is 87.4 s.

    Returns ``{adapter_on, adapter_off, n_targets, retention_ppl, retention_total_tokens}`` — every
    value a float or an int, and NEVER a rate without its denominator.

    THE CALL SHAPE IS `run_erasure_arm._capability()`'s (`scripts/phase19_erasure.py:2860-2870`),
    minus the exposure leg plan 25-22 owns: `dialogue_ppl_pair` then `retention_perplexity`, in that
    order, on one loaded adapted model. Both are IMPORTED AND CALLED, never re-implemented —
    `dialogue_ppl_pair` carries its own shared-denominator `_prove` and `retention_perplexity`'s
    dead-id-mask policy is FROZEN under DEBT-02.

    MEASURED PER-CALL COST (HEAD, `checkpoints/persona_adapter.pt`, MPS): dialogue pair 43.5 s,
    retention 43.9 s — 87.4 s per point, 1.07 h over 44 points, or 0.80 h with the OFF leg measured
    once, against a 107-150 h sweep budget (0.7-1.0%). D-45 spends it on ALL 44.

    ``adapter_off_reading`` IS VERIFIED, NEVER SUBSTITUTED. D-45's OFF-leg-once optimisation is
    licensed by `results/phase19_noise_floors.json`'s
    ``dialogue_ppl_noise_floor.adapter_off_identical_across_seeds``, which this function READS
    rather than assumes. When supplied, the reading is asserted EQUAL to the freshly measured
    ``adapter_off`` rather than replacing it: a reused number that is never checked against a fresh
    one is an assumption wearing a measurement's clothes, and the whole point of the optimisation is
    that the OFF leg is the base model and therefore invariant.

    ``retention_perplexity`` is imported AS A SYMBOL. Calling it as
    ``personacore.evaluation.perplexity.retention_perplexity`` raises ``AttributeError`` because the
    package ``__init__`` re-exports a FUNCTION named ``perplexity`` that shadows the submodule
    (measured).
    """
    import phase19_erasure

    from personacore.config import ModelConfig
    from personacore.evaluation.perplexity import retention_perplexity

    pair = phase19_erasure.dialogue_ppl_pair(model, device, forbid)
    retention_ppl, retention_total_tokens = retention_perplexity(
        model, phase19_erasure.RETENTION_BIN, ModelConfig.block_size, device, tok
    )

    if adapter_off_reading is not None:
        licensed = _read(NOISE_FLOORS_RECORD)["dialogue_ppl_noise_floor"][
            "adapter_off_identical_across_seeds"
        ]
        _prove(
            licensed is True,
            "an `adapter_off_reading` was supplied for reuse, but "
            "`results/phase19_noise_floors.json` records "
            f"`adapter_off_identical_across_seeds` as {licensed!r}, not True. That field is the "
            "ONLY licence D-45's measure-the-OFF-leg-once optimisation has; without it the reuse "
            "is an unchecked substitution",
        )
        _prove(
            adapter_off_reading == pair["adapter_off"],
            f"the reused adapter_off reading {adapter_off_reading!r} does NOT equal the freshly "
            f"measured {pair['adapter_off']!r}. The OFF leg is the base model with the adapter "
            "disabled, so the two must be bit-identical; a disagreement means the reuse is "
            "carrying a reading from a different model, a different corpus or a different policy, "
            "and the gap `on - off` would then measure the mismatch rather than the adaptation",
        )

    return {
        "adapter_on": pair["adapter_on"],
        "adapter_off": pair["adapter_off"],
        "n_targets": pair["n_targets"],
        "retention_ppl": retention_ppl,
        "retention_total_tokens": retention_total_tokens,
    }


# ---------------------------------------------------------------------------------------------
# (c) THE FREE BIT-LEVEL REPRODUCTION CHECK (D-45), OF D-01'S SHAPE.
# ---------------------------------------------------------------------------------------------

# The four reproduction targets, each named by its JSON PATH into `results/phase19_arm_erased.json`
# and never retyped as a value. The `("pre_erasure", ...)` prefix is the whole point — see
# `prove_condition_c_reproduction`'s docstring.
REPRODUCTION_TARGETS = (
    ("adapter_on", ("pre_erasure", "dialogue_ppl", "adapter_on")),
    ("adapter_off", ("pre_erasure", "dialogue_ppl", "adapter_off")),
    ("n_targets", ("pre_erasure", "dialogue_ppl", "n_targets")),
    ("retention_ppl", ("pre_erasure", "retention_ppl", 0)),
    ("retention_total_tokens", ("pre_erasure", "retention_ppl", 1)),
)


def _dig(record, path):
    node = record
    for step in path:
        node = node[step]
    return node


def prove_condition_c_reproduction(device=None, adapter_path=None):
    """Measure condition (c) on the taught adapter and reproduce Phase 19's record EXACTLY.

    Returns the measured mapping. Raises ``SystemExit`` naming the JSON PATH of the first field that
    missed, both values, and why a reading that cannot reproduce a committed record cannot be
    published beside one.

    FOUR FIGURES AND TWO DENOMINATORS, UNDER EXACT ``==``. No tolerance: these are the same forward
    passes over the same frozen bins under the same policy, so anything but bit-equality means the
    path changed. D-45's free check, of D-01's shape.

    THE MEASURED TRAP, AND THE SINGLE MOST LIKELY ERROR IN THIS MODULE. The reproduction targets
    live under ``["pre_erasure"]``. The record's TOP LEVEL carries the POST-erasure readings —
    ``["dialogue_ppl"]["adapter_on"]`` is 4.851119149910443 and ``["retention_ppl"]`` is
    [3.6709177253236867, 1000285] — so a reader who omits ``["pre_erasure"]`` compares against the
    wrong numbers and this check goes FALSE-RED. ``adapter_off`` is 4.573349214207799 in BOTH
    blocks, which is exactly why the mistake survives a casual spot-check.
    `tests/test_phase25_condition_c.py::test_the_top_level_blocks_are_the_wrong_comparator` is that
    trap's own natural RED and needs no model to run.
    """
    import phase14_recall as recall

    from personacore.preflight import preflight_device

    if device is None:
        device = preflight_device(strict=False)["device"]

    model, _cfg, tok, forbid, _artifact = recall.load_adapted_model(
        device, ADAPTER_CHECKPOINT if adapter_path is None else adapter_path
    )
    measured = measure_condition_c(model, tok, device, forbid=forbid)

    record = _read(ARM_ERASED_RECORD)
    for field, path in REPRODUCTION_TARGETS:
        committed = _dig(record, path)
        _prove(
            measured[field] == committed,
            f"{field} reproduced as {measured[field]!r} against the committed "
            f"{committed!r} at results/phase19_arm_erased.json"
            + "".join(f"[{step!r}]" for step in path)
            + ". A condition-(c) reading that cannot reproduce a committed record CANNOT be "
            "published beside one: the whole value of measuring (c) on the same path Phase 19 used "
            "is that the two are the same path. Check the nesting first — the record's TOP LEVEL "
            "carries the POST-erasure readings and is the wrong comparator",
        )
    return measured


# ---------------------------------------------------------------------------------------------
# (d) THE TWO FLOORS — IMPORTED AS-IS, MISMATCH DISCLOSED, MAGNITUDE MEASURED (D-48).
# ---------------------------------------------------------------------------------------------


def gap_noise_floor():
    """(c)'s dialogue-leg floor and its recipe, read from `results/phase19_noise_floors.json`.

    Returns ``(value, recipe)``. D-48 imports it AS-IS; what is disclosed is the recipe mismatch,
    and what makes the disclosure honest is `DIALOGUE_FLOOR_SENSITIVITY` measuring the magnitude of
    the error it could make rather than asserting it is small.
    """
    block = _read(NOISE_FLOORS_RECORD)["dialogue_ppl_noise_floor"]
    return block["value"], block["recipe"]


DIALOGUE_FLOOR_RECIPE_MISMATCH = (
    "GOVERNS `gap_noise_floor`. The dialogue noise floor 0.005214448168350039 was measured on a "
    "v3.0 recipe -- n_facts=10, replay_ratio=1.0, arm_spec='real', second_person=false, seeds "
    "1337/2024 -- and that recipe MATCHES NO v4.0 SWEEP POINT. It is imported as-is under D-48 and "
    "the mismatch is disclosed rather than worked around, because the alternative is a fresh "
    "floor measured after the sweep exists, which is a threshold chosen after seeing results. What "
    "makes 'imported as-is' honest here is that the magnitude was CHECKED BEFORE the precedent was "
    "accepted: see DIALOGUE_FLOOR_SENSITIVITY, where the floor contributes 1.65% of the band width "
    "and even a 10x error moves the ceiling by only 14.86% of it, because F_C makes control_gap "
    "dominate BOTH edges. Immaterial AS MEASURED, not as argued from precedent."
)


def anchor_dialogue_gap():
    """The PHASE-19 ANCHOR GAP, derived from the committed record and never typed.

    ``results/phase19_arm_erased.json["pre_erasure"]["dialogue_ppl"]`` ``adapter_on - adapter_off``
    = 1.2420966625043919.

    WHAT THIS IS NOT, stated because the numbers in `DIALOGUE_FLOOR_SENSITIVITY` reproduce at this
    gap and at NO OTHER, so a sensitivity quoted without naming its input is an unnamed quantity.
    D-47 makes the verdict's `control_gap` PER CAPACITY, taken from each capacity's own sigma=0
    control, and NO v4.0 CONTROL EXISTS UNTIL PLAN 25-15 IN WAVE 8 — so a v4.0 `control_gap` cannot
    be this sensitivity's input at wave 1. The anchor gap is used ONLY to size the floor against a
    band of realistic width. It is NEVER passed to `mitigation_point_verdict`, and
    `prove_control_gap_not_borrowed` is what structurally stops it, or any other borrowed gap, from
    leaking into a verdict.
    """
    block = _read(ARM_ERASED_RECORD)["pre_erasure"]["dialogue_ppl"]
    return block["adapter_on"] - block["adapter_off"]


def _dialogue_floor_sensitivity():
    """D-48's magnitude check, COMPUTED LIVE through the frozen `dialogue_gap_band`, never typed.

    The 10x-error term is ``hi(10 * floor) - hi(floor)``, i.e. ``9 * MARGIN_K * floor``, and NOT ten
    times the floor's share of the band. The wrong form yields 0.16515079057592702 instead of the
    measured 0.14863571151833432 — a difference that would read as a rounding slip and is actually
    a different quantity.
    """
    floor, recipe = gap_noise_floor()
    control_gap = anchor_dialogue_gap()

    lo, hi = mitigation_gate.dialogue_gap_band(control_gap=control_gap, gap_noise_floor=floor)
    _, hi_ten_x = mitigation_gate.dialogue_gap_band(
        control_gap=control_gap, gap_noise_floor=floor * 10
    )
    width = hi - lo
    margin = mitigation_gate.MARGIN_K * floor

    return {
        "control_gap": control_gap,
        "control_gap_source": "results/phase19_arm_erased.json['pre_erasure']['dialogue_ppl']",
        "control_gap_disclosure": anchor_dialogue_gap.__doc__,
        "gap_noise_floor": floor,
        "recipe": recipe,
        "band": (lo, hi),
        "band_width": width,
        "margin_contribution": margin,
        "floor_share_of_band": margin / width,
        "ten_x_error_ceiling_move": hi_ten_x - hi,
        "ten_x_error_share_of_band": (hi_ten_x - hi) / width,
    }


DIALOGUE_FLOOR_SENSITIVITY = _dialogue_floor_sensitivity()


def retention_floor_for_verdict():
    """(c)'s retention-leg floor: the MEASURED ADAPTER-REGIME value, PROVED admissible.

    Returns 0.008681618994239138, read from `results/phase20_retention_floor.json` and asserted
    ``==`` `phase20_gate_coverage._ADAPTER_REGIME_RETENTION_FLOOR` so the committed record and the
    module cannot drift apart. It then runs `phase20_gate_coverage._prove_retention_floor` on the
    value BEFORE returning it, so the floor is PROVED admissible rather than asserted to be — the
    five refusals a retention floor must survive to reach a v4.0 verdict.

    THE PROVENANCE IS CONSTRUCTED, NOT READ WHOLE, and this is the single thing that decides whether
    this module imports or raises. MEASURED: the record carries ``seeds`` ([1337, 2024]) and does
    NOT carry ``regime``, while `RETENTION_FLOOR_PROVENANCE_KEYS` is ``("regime", "seeds")``.
    Handing the record over raw raises ``SystemExit`` on the FIRST refusal. ``ADAPTER_REGIME`` is
    resolved BY IMPORT so a regime rename cannot leave a stale literal behind.
    """
    record = _read(RETENTION_FLOOR_RECORD)
    floor = record["retention_ppl_noise_floor"]
    _prove(
        floor == phase20_gate_coverage._ADAPTER_REGIME_RETENTION_FLOOR,
        f"the committed record's retention_ppl_noise_floor {floor!r} disagrees with "
        f"phase20_gate_coverage._ADAPTER_REGIME_RETENTION_FLOOR "
        f"{phase20_gate_coverage._ADAPTER_REGIME_RETENTION_FLOOR!r}. These are two committed "
        "copies of ONE measurement; a disagreement between them is a halt, not a preference",
    )
    phase20_gate_coverage._prove_retention_floor(
        retention_noise_floor=floor,
        retention_floor_provenance={
            "regime": phase20_gate_coverage.ADAPTER_REGIME,
            "seeds": record["seeds"],
        },
    )
    return floor


def _retention_floor_disclosure():
    """Both floors and both caps, IMPORTED from the Phase 20 record, cross-proved vs the module.

    The record and `phase20_gate_coverage` are two committed copies of one rule. Each imported
    figure is asserted equal to its module counterpart at import: a disagreement is a halt.
    """
    record = _read(RETENTION_FLOOR_RECORD)
    for key, module_value, module_name in (
        ("cap", phase20_gate_coverage._GOVERNING_CAP, "_GOVERNING_CAP"),
        ("borrowed_cap", phase20_gate_coverage._BORROWED_CAP, "_BORROWED_CAP"),
        (
            "borrowed_floor_ratio",
            phase20_gate_coverage._BORROWED_FLOOR_RATIO,
            "_BORROWED_FLOOR_RATIO",
        ),
        (
            "borrowed_floor",
            erasure_gate.V20_RETENTION_NOISE_FLOOR,
            "erasure_gate.V20_RETENTION_NOISE_FLOOR",
        ),
    ):
        _prove(
            record[key] == module_value,
            f"results/phase20_retention_floor.json[{key!r}] is {record[key]!r} but "
            f"{module_name} is {module_value!r}. The record and the module are two committed "
            "copies of one rule and a disagreement between them is a HALT, not a preference: "
            "whichever is right, a verdict computed while they disagree is computed against an "
            "unknown",
        )
    return {
        "governing_floor": record["retention_ppl_noise_floor"],
        "governing_cap": record["cap"],
        "cap_derivation": record["cap_derivation"],
        "borrowed_floor": record["borrowed_floor"],
        "borrowed_cap": record["borrowed_cap"],
        "borrowed_floor_ratio": record["borrowed_floor_ratio"],
        "seeds": record["seeds"],
        "recipe": record["recipe"],
        "recipe_source": record["recipe_source"],
        "governs": record["governs"],
        "premise_correction": (
            "D-48 NAMED `erasure_gate.V20_RETENTION_NOISE_FLOOR` AS THE FLOOR TO IMPORT 'AS-IS', "
            "AND THAT IMPORT IS REFUSED BY A COMMITTED GUARD. Measured: "
            "`phase20_gate_coverage._prove_retention_floor` raises SystemExit on that value, "
            "reading 'the retention noise floor IS 0.06893, the Phase 12 full-fine-tune seed pair, "
            "whatever regime the provenance claims'. The measured adapter-regime floor is ACCEPTED "
            "by the same call. 'Imported as-is' was never executable for the retention leg -- so "
            "the citation is superseded by dated continuation and the ARITHMETIC is not retracted. "
            "HONOURING THE REFUSAL BUYS NO EASIER PASS: the governing cap is the TIGHTER of the "
            "two, so the admissible window NARROWS. Both floors and both caps travel in this "
            "record; neither is hidden and neither is loosened."
        ),
    }


RETENTION_FLOOR_DISCLOSURE = _retention_floor_disclosure()


# ---------------------------------------------------------------------------------------------
# (e) D-49'S PRE-REGISTRATION, COMMITTED BEFORE ANY SWEEP POINT RUNS.
# ---------------------------------------------------------------------------------------------


def _retention_leg_binds_at_anchor():
    """D-49 as a COMPUTED RUNTIME PROPERTY: no literal cap, no literal headroom, no literal factor.

    For each floor: the cap from the frozen `mitigation_gate.retention_cap`, the taught reading read
    from the committed record, the headroom ``cap - taught``, and the factor by which the floor
    would have to GROW to admit the reading:
    ``(taught - V20_EWC_RETENTION_PPL) / MARGIN_K / floor``.

    Both headrooms are asserted strictly negative and the governing one strictly more negative, so
    the a-fortiori claim is checked on every import rather than argued in prose.
    """
    taught = _read(ARM_ERASED_RECORD)["pre_erasure"]["retention_ppl"][0]

    def leg(floor):
        cap = mitigation_gate.retention_cap(retention_noise_floor=floor)
        return {
            "floor": floor,
            "cap": cap,
            "taught_reading": taught,
            "headroom": cap - taught,
            "admit_factor": (taught - mitigation_gate.V20_EWC_RETENTION_PPL)
            / mitigation_gate.MARGIN_K
            / floor,
        }

    borrowed = leg(erasure_gate.V20_RETENTION_NOISE_FLOOR)
    governing = leg(phase20_gate_coverage._ADAPTER_REGIME_RETENTION_FLOOR)

    _prove(
        borrowed["headroom"] < 0 and governing["headroom"] < 0,
        f"the retention leg does NOT bind at the anchor: headrooms {borrowed['headroom']!r} "
        f"(borrowed) and {governing['headroom']!r} (governing). D-49 pre-registers that it DOES, "
        "on both floors, and that observation is the reason a narrow or empty frontier cannot be "
        "re-argued afterwards as a mis-set floor. If it stopped being true, the pre-registration "
        "would be pre-registering something false and must be re-derived, never quietly dropped",
    )
    _prove(
        governing["headroom"] < borrowed["headroom"],
        f"the governing headroom {governing['headroom']!r} is NOT strictly more negative than the "
        f"borrowed {borrowed['headroom']!r}. D-49 holds A FORTIORI under the governing floor "
        "precisely because the governing cap is TIGHTER; if that ordering inverted, honouring the "
        "borrowed-floor refusal would be buying an easier pass, which is the one thing the "
        "disclosure promises it does not do",
    )

    committed = _read(NOISE_FLOORS_RECORD)["retention_ppl_pre_erasure"]
    _prove(
        borrowed["headroom"] == committed["adapter_on_headroom"],
        f"the computed borrowed headroom {borrowed['headroom']!r} does not equal Phase 19's own "
        f"committed adapter_on_headroom {committed['adapter_on_headroom']!r}. D-49's evidence is "
        "that Phase 19 RECORDED this and no plan in the 20-plan set surfaced it; if the two ever "
        "disagreed, the corroboration would be a coincidence rather than a reading",
    )

    return {
        "borrowed": borrowed,
        "governing": governing,
        "phase19_committed_headroom": committed["adapter_on_headroom"],
        "phase19_committed_above_cap": committed["adapter_on_above_cap"],
        "surfaced_by_no_plan_in_the_20_plan_set": True,
    }


RETENTION_LEG_BINDS_AT_ANCHOR = _retention_leg_binds_at_anchor()

RETENTION_SQUEEZE_IS_THE_FRONTIER = (
    "GOVERNS `RETENTION_LEG_BINDS_AT_ANCHOR`, and it is COMMITTED BEFORE ANY SWEEP POINT RUNS. "
    "The retention leg already fails at the untouched taught adapter, under BOTH floors. That is "
    "the instrument working, not a broken floor. DP noise degrades teaching, so HIGH-NOISE points "
    "degrade retention less and clear (c) while failing (b)'s recall, and LOW-NOISE points do the "
    "reverse -- they hold recall and push retention past the cap. THAT SQUEEZE IS THE FRONTIER. "
    "The window where a point clears BOTH may be narrow or empty. Because this observation is "
    "committed in advance, an empty or narrow frontier can NEVER be re-argued afterwards as a "
    "mis-set floor, and the floor can NEVER be loosened after seeing results."
)


# ---------------------------------------------------------------------------------------------
# (f) D-50'S COUNTERFACTUAL — DEFINED NOW, FILLED LATER, AT ZERO COMPUTE.
# ---------------------------------------------------------------------------------------------


def counterfactual_retention_floor(seed_spread):
    """A v4.0-RECIPE retention floor from the sweep's OWN seed-to-seed spread. No new run.

    ``seed_spread`` is a non-empty sequence of non-negative seed-to-seed retention differences
    produced by the sweep itself. The floor is the LARGEST observed spread -- the same estimator
    shape `results/phase19_noise_floors.json` used for the dialogue floor
    (``|gap_1337 - gap_2024|``), and the conservative choice when there is more than one pair.

    Returns ``{floor, cap, source}`` with the cap from the frozen `mitigation_gate.retention_cap`.

    THIS COSTS NO NEW RUN AND NO EXTRA COMPUTE. It is arithmetic over readings the sweep produces
    anyway -- one added field group per point plus a write-time assertion. It is FRONT-02's
    strongest form applied to (c): it shows the SIZE of the error the recipe mismatch could make
    rather than only asserting the error is small, which is the standard D-28 sets for the two
    multiplicities.
    """
    spread = list(seed_spread)
    _prove(
        len(spread) > 0,
        "the counterfactual retention floor was handed an EMPTY seed spread. A floor is a "
        "MAGNITUDE measured from at least one seed-to-seed difference; there is nothing here to "
        "measure run-to-run variance against, so the k=2 margin built on it would be a margin over "
        "an unknown",
    )
    negative = [v for v in spread if v < 0]
    _prove(
        not negative,
        f"the counterfactual retention floor was handed negative spread member(s) {negative!r}. A "
        "floor is a MAGNITUDE: a negative one would compute a cap BELOW the published v2.0 "
        "baseline, admitting nothing and reporting every point as failing (c) without having "
        "measured anything",
    )
    floor = max(spread)
    return {
        "floor": floor,
        "cap": mitigation_gate.retention_cap(retention_noise_floor=floor),
        "source": (
            "the sweep's OWN seed-to-seed retention spread (v4.0 recipe), against the imported "
            "v3.0-regime floor the verdict actually reads. D-50: no new run, no extra compute."
        ),
    }


def counterfactual_fields(point_retention_ppl, seed_spread):
    """D-50's three carriage fields for one point's record. Plan 25-08 adds one group per point.

    Returns the last three names in `CONDITION_C_FIELDS`. Plan 25-19 asserts at write time that each
    point's recorded counterfactual cap RE-DERIVES from its recorded floor, which is why both travel
    together rather than only the headroom.
    """
    counterfactual = counterfactual_retention_floor(seed_spread)
    return {
        "counterfactual_retention_floor": counterfactual["floor"],
        "counterfactual_retention_cap": counterfactual["cap"],
        "counterfactual_retention_headroom": counterfactual["cap"] - point_retention_ppl,
    }


# ---------------------------------------------------------------------------------------------
# (g) `control_gap` PER CAPACITY (D-47) — REFUSED STRUCTURALLY, NOT BY CONVENTION.
# ---------------------------------------------------------------------------------------------


def control_gap_for_capacity(control_reading):
    """That capacity's OWN ``adapter_on - adapter_off``, from its OWN sigma=0 control reading.

    ``control_reading`` is a mapping carrying ``adapter_on`` and ``adapter_off`` -- the shape
    `measure_condition_c` returns.
    """
    return control_reading["adapter_on"] - control_reading["adapter_off"]


CONTROL_GAP_IS_PER_CAPACITY = (
    "GOVERNS `control_gap`. It is PER CAPACITY, taken from each capacity's own sigma=0 control "
    "(D-47). It sets BOTH edges of (c)'s dialogue band -- lo = F_C x control_gap and "
    "hi = control_gap + MARGIN_K x gap_noise_floor -- so a BORROWED value does not merely mislabel "
    "a number: it SILENTLY MOVES THE ADMISSIBLE BAND at the capacity that did not produce it, in "
    "both directions at once, and the point that then clears or fails (c) is being judged against "
    "the other capacity's control. This is the same rule D-03 applied to the n=64 matched floor: "
    "no borrowed reference, and therefore no capacity asymmetry to disclose. D-01 already runs the "
    "control at both capacities, so this costs nothing. The refusal is "
    "`prove_control_gap_not_borrowed`."
)


def prove_control_gap_not_borrowed(readings_by_arm):
    """Refuse a borrowed `control_gap` STRUCTURALLY. ``readings_by_arm``: arm -> reading.

    Two refusals, because a borrow shows up two ways: the SAME OBJECT handed to two capacities
    (identity), and two capacities carrying an equal ``(adapter_on, adapter_off)`` pair (value). The
    second catches a copy the first misses; the first catches a shared reference before it has been
    copied anywhere.

    Returns ``None`` -- its whole output is the refusal.
    """
    arms = list(readings_by_arm)
    for i, left in enumerate(arms):
        for right in arms[i + 1 :]:
            a, b = readings_by_arm[left], readings_by_arm[right]
            _prove(
                a is not b,
                f"arms {left!r} and {right!r} were handed the SAME control-reading OBJECT. D-47 "
                "makes `control_gap` per capacity: one object cannot be two capacities' own "
                "sigma=0 control, and it sets BOTH edges of the dialogue band, so the capacity "
                "that did not produce it is judged against a band it never measured",
            )
            pair_a = (a["adapter_on"], a["adapter_off"])
            pair_b = (b["adapter_on"], b["adapter_off"])
            _prove(
                pair_a != pair_b,
                f"arms {left!r} and {right!r} carry an IDENTICAL (adapter_on, adapter_off) pair "
                f"{pair_a!r}. Two independently measured capacities do not produce bit-identical "
                "dialogue readings; this is a borrowed control gap that was copied rather than "
                "shared, and it silently moves the admissible band at the capacity that did not "
                "produce it",
            )
