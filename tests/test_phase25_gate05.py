"""PLAN 25-22 — GATE-05's early return WATCHED FIRING, then watched NOT firing (D-46).

`mitigation_point_verdict` has TWO early returns BEFORE `reasons = []`. The second fires at
`point_extraction_successes == 0 and not zero_extraction_has_nll`. THE PRE-REGISTERED NULL IS ZERO
EXTRACTION UNDER HIGH NOISE, so without a producer for that flag the DP arm's entire high-noise end
— the exact region where the expected result lives — comes back with ONE reason and condition (a)'s
ZERO TOLERANCE sentence is structurally unreachable for every point in it.

THE STRUCTURAL AND ARITHMETIC HALF IS CPU-ONLY AND NEVER SKIPS. Its acceptance gate is
`pytest -k "not measure_gate05" -q` reporting ZERO skipped: a criterion that can vanish into a skip
count on the wrong machine is not a criterion. Only `test_measure_gate05_...` touches a model.

THE ONE MPS-TOUCHING CASE IS GATED TWICE AND SERIALISED.

* It reads `PERSONACORE_SWEEP_ACTIVE` FROM THE ENVIRONMENT at module scope (D-44). Plan 25-06 owns
  the sweep-active register and is WAVE 2 — it runs after this plan, so `sweep_is_active` does not
  exist yet and importing it here would be a collection error in wave 1. The env var is the same
  mechanism under the same name, and it is exactly the shape 25-06 prescribes for its own
  import-time register. There is no CLI option and 25-06 registers none: a second entry point the
  import-time register cannot see would leave this leg RUNNING on MPS while the register-inherited
  legs skipped, which is the contention D-44 exists to prevent.
* An `mps.is_available()` gate sits beside it, or CPU-only CI goes red. The device gate ALONE is
  TRUE during the sweep, which is why it is never used alone.
* It is SERIALISED against plan 25-21's wave-1 MPS leg by an exclusive `fcntl.flock(LOCK_EX)` on
  `tempfile.gettempdir()/personacore-phase25-mps.lock` — the OS temp dir, so there is no repo file
  to gitignore — held for its duration and released in a `finally`. 25-21 names the identical path.
  The lock STAYS after 25-06's move to wave 2: that move removed a THIRD wave-1 MPS toucher, and
  two concurrent MPS legs on one M3 still contend.

REFUSALS ARE ASSERTED ON `SystemExit`, NEVER ON `Exception`. `SystemExit` derives from
`BaseException`, so `pytest.raises(Exception)` does NOT catch it and a test written that way
passes for the wrong reason. The check for that mistake is an AST walk rather than a `grep -c`:
this file's own docstrings discuss the token being counted, so the counting form goes FALSE-RED
on its own prose (measured at plan time: `grep -c` over `tests/test_phase23_cost.py` returns 3
while the AST gate over the same file exits 0).
"""

import ast
import fcntl
import inspect
import json
import math
import os
import pathlib
import sys
import tempfile
import time

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import mitigation_gate  # noqa: E402  (scripts/ is not a package)
import phase20_gate_coverage as gc  # noqa: E402
import phase25_gate05 as g5  # noqa: E402
from _prose import normalized  # noqa: E402

# D-44's register, read from the ENVIRONMENT at module scope. Plan 25-06 is wave 2 and its helper
# does not exist yet; this is the same env var under the same name, not a second mechanism.
_SWEEP_ACTIVE = os.environ.get("PERSONACORE_SWEEP_ACTIVE")

try:
    import torch

    _MPS_AVAILABLE = torch.backends.mps.is_available()
except Exception:  # pragma: no cover — a torch-less box still collects this file
    _MPS_AVAILABLE = False

# The shared wave-1 MPS lock. Plan 25-21 names this identical path.
MPS_LOCK_PATH = pathlib.Path(tempfile.gettempdir()) / "personacore-phase25-mps.lock"

_MPS_LEG = pytest.mark.skipif(
    _SWEEP_ACTIVE is not None or not _MPS_AVAILABLE,
    reason=(
        "measure_gate05 runs teacher-forced exposure over the eight locked facts on MPS. It is "
        "skipped when PERSONACORE_SWEEP_ACTIVE is set (D-44 — the sweep owns the device and a "
        "suite run would contend with it) and when MPS is unavailable (CI is ubuntu-latest on a "
        "CPU-only wheel). Two gates, not one: the device gate alone is TRUE during the sweep, "
        "which is exactly the contention D-44 exists to prevent"
    ),
)

_VERDICT_SOURCE = inspect.getsource(mitigation_gate.mitigation_point_verdict)

ZERO_TOLERANCE_SENTENCE = "ZERO TOLERANCE"


def _never_taught_anchors():
    """The control's extraction anchors, read VERBATIM and never splatted.

    `extraction_ceiling(**pooled)` raises `TypeError`: the pooled block carries ten keys and the
    ceiling takes four. "Verbatim" means the two COUNT fields out of `pooled` plus the two
    TOP-LEVEL provenance fields, each by name.
    """
    record = json.loads((_ROOT / "results" / "phase23_never_taught.json").read_text())
    pooled = record["pooled"]
    return {
        "control_extraction_successes": pooled["nontarget_successes"],
        "control_extraction_questions": pooled["nontarget_questions"],
        "extraction_noise_floor": record["extraction_noise_floor"],
        "extraction_floor_provenance": record["extraction_floor_provenance"],
    }


def _point_kwargs(**overrides):
    """The 21 keyword arguments of one zero-extraction point, assembled from real producers.

    Condition (c)'s six come from plan 25-21's producers and the committed Phase-19 / Phase-20
    records; the seventh, `zero_extraction_has_nll`, is this plan's. The extraction anchors are the
    never-taught record's own `(0, 416)`, and the governing retention floor is
    `phase20_gate_coverage._ADAPTER_REGIME_RETENTION_FLOOR` — the MEASURED adapter-regime floor,
    not the borrowed Phase-12 one `_prove_retention_floor` refuses by name and by regime.
    """
    ppl_on, ppl_off = 5.815445876712191, 4.573349214207799
    kwargs = {
        "arm": "dp",
        "point_extraction_successes": 0,
        "point_extraction_questions": 416,
        **_never_taught_anchors(),
        "zero_extraction_has_nll": False,
        "point_taught_recall": 0.90,
        "point_heldout_recall": 0.90,
        "control_taught_recall": 0.7837,
        "control_heldout_recall": 0.5615,
        "point_dialogue_ppl_on": ppl_on,
        "point_dialogue_ppl_off": ppl_off,
        "control_gap": ppl_on - ppl_off,
        "gap_noise_floor": 0.005214448168350039,
        "point_retention_ppl": 3.80,
        "retention_noise_floor": gc._ADAPTER_REGIME_RETENTION_FLOOR,
        "sweep_extraction_rates": (0.0, 0.9),
        "sweep_taught_recalls": (0.90, 0.10),
        "replicated_at_second_seed": True,
    }
    kwargs.update(overrides)
    return kwargs


def _record(slot):
    """One exposure record with the frozen key tuple and all six finite NLLs."""
    return {
        "slot": slot,
        "admissible": (g5.ADMISSIBLE_NLL_FRAME, g5.ADMISSIBLE_NLL_REDUCTION),
        "nll": {
            frame: {reduction: 1.25 for reduction in g5.NLL_REDUCTIONS} for frame in g5.NLL_FRAMES
        },
        "rank": 1,
        "exposure_bits": 2.807,
        "ceiling_bits": 2.807,
        "n_references": 7,
        "length_spread": 2,
        "spread_zero_control": True,
        "descriptive_label": "descriptive",
        "threats_to_validity": "threats",
    }


def _exposure(slots=None):
    return [_record(slot) for slot in (g5.GATE05_SLOTS if slots is None else slots)]


# =============================================================================================
# (a) THE EARLY RETURN WATCHED FIRING, AND WATCHED NOT FIRING — D-46's NATURAL RED
# =============================================================================================


def test_a_zero_without_nll_never_reaches_condition_a():
    """Zero extraction with no NLL: ONE reason, and ZERO TOLERANCE structurally unreachable.

    This is the state the DP arm's whole high-noise end would be in without this plan's producer,
    and it is the pre-registered null's own region of the curve.
    """
    verdict, reasons, arm = mitigation_gate.mitigation_point_verdict(
        **_point_kwargs(zero_extraction_has_nll=False)
    )
    assert verdict == "INCONCLUSIVE"
    assert len(reasons) == 1, reasons
    assert "cannot distinguish" in reasons[0]
    assert g5.GATE05_EARLY_RETURN_TEXT.strip() in reasons[0]
    assert not any(ZERO_TOLERANCE_SENTENCE in reason for reason in reasons)
    assert arm == "dp"
    print(f"\n[25-22] FALSE -> {verdict} n_reasons={len(reasons)}\n  {reasons[0]}")


def test_the_same_point_with_the_nll_reaches_all_three_conditions():
    """The IDENTICAL point with the flag produced: four reasons and the ZERO TOLERANCE sentence.

    The reason COUNT and the SENTENCE are asserted, never the verdict word — the verdict depends on
    inputs the sweep produces, while reaching (a), (b) and (c) at all is what the flag decides.
    """
    verdict, reasons, _arm = mitigation_gate.mitigation_point_verdict(
        **_point_kwargs(zero_extraction_has_nll=True)
    )
    assert len(reasons) == 4, reasons
    assert any(ZERO_TOLERANCE_SENTENCE in reason for reason in reasons)
    assert reasons[0].startswith("(a) ")
    assert reasons[1].startswith("(b) ")
    assert reasons[2].startswith("(c) ") and reasons[3].startswith("(c) ")
    print(f"\n[25-22] TRUE -> {verdict} n_reasons={len(reasons)}")
    for reason in reasons:
        print(f"  {reason}")


def test_zero_questions_is_the_other_early_return():
    """BOTH pre-`reasons` returns are enumerated rather than one being assumed away."""
    verdict, reasons, _arm = mitigation_gate.mitigation_point_verdict(
        **_point_kwargs(point_extraction_questions=0, zero_extraction_has_nll=True)
    )
    assert verdict == "INCONCLUSIVE"
    assert reasons == ["no extraction questions scored"]


def test_the_early_returns_precede_the_reasons_list():
    """Structural: both early returns lie ABOVE `reasons = []` in the frozen source.

    By AST over `inspect.getsource`, so a future reader cannot re-derive the precedence from prose —
    and never by grepping `scripts/mitigation_gate.py`, which discusses these names in paragraphs.
    """
    function = ast.parse(_VERDICT_SOURCE).body[0]
    assert isinstance(function, ast.FunctionDef)
    reasons_line = next(
        node.lineno
        for node in ast.walk(function)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "reasons" for t in node.targets)
        and isinstance(node.value, ast.List)
        and not node.value.elts
    )
    early = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Return) and node.lineno < reasons_line
    ]
    assert len(early) == 2, [node.lineno for node in early]
    assert all(node.lineno < reasons_line for node in early)


# =============================================================================================
# (b) THE FLAG'S TYPE, AND THE TRAP — T-25-125
# =============================================================================================


def test_the_flag_is_a_plain_bool():
    assert type(g5.zero_extraction_has_nll(_exposure())) is bool
    assert g5.zero_extraction_has_nll(_exposure()) is True
    assert type(g5.zero_extraction_has_nll([])) is bool
    assert g5.zero_extraction_has_nll([]) is False


def test_a_truthy_pair_is_refused():
    """`SystemExit`, not `Exception` — `pytest.raises(Exception)` would not catch it."""
    with pytest.raises(SystemExit) as excinfo:
        g5.prove_flag_is_a_bool((False, "no nll"), point_key="dp_n8:sigma=8.0")
    message = str(excinfo.value)
    assert "truthy" in message.lower()
    assert "dp_n8:sigma=8.0" in message
    print(f"\n[25-22] prove_flag_is_a_bool refusal:\n  {message}")


def test_the_pair_would_have_disarmed_the_branch():
    """The harm demonstrated ONCE, so the refusal above is evidenced rather than asserted."""
    pair = (False, "reason")
    assert bool(pair) is True
    assert (not pair) is False

    verdict, reasons, _arm = mitigation_gate.mitigation_point_verdict(
        **_point_kwargs(zero_extraction_has_nll=pair)
    )
    assert len(reasons) == 4, reasons
    assert not any("cannot distinguish" in reason for reason in reasons)
    print(
        f"\n[25-22] the pair skipped the INCONCLUSIVE branch: {verdict} "
        f"with {len(reasons)} reasons, on a point with ZERO extraction successes"
    )


# =============================================================================================
# (c) THE GATED SET AND THE SIX REQUIRED COLUMNS — T-25-128, T-25-129
# =============================================================================================


def test_the_eight_locked_facts_are_two_agreeing_committed_tuples():
    import phase18_extraction as extraction
    import phase19_erasure as erasure

    assert set(g5.GATE05_SLOTS) == set(extraction.CORE_SLOTS)
    assert set(g5.GATE05_SLOTS) == set(erasure.CORE_GATED_SLOTS)
    assert len(g5.GATE05_SLOTS) == 8
    # Different ORDER is the point: two independent tuples, not one copied twice.
    assert tuple(extraction.CORE_SLOTS) != tuple(erasure.CORE_GATED_SLOTS)


def test_a_missing_slot_is_a_gap_naming_its_fact_id():
    import phase14_factset as factset

    dropped = g5.GATE05_SLOTS[0]
    fact_id = next(fact.id for fact in factset.LOCKED_FACTS if fact.slot == dropped)
    gaps = g5.gate05_exposure_gaps(_exposure([s for s in g5.GATE05_SLOTS if s != dropped]))
    assert len(gaps) == 1, gaps
    assert fact_id in gaps[0]
    assert (
        g5.zero_extraction_has_nll(_exposure([s for s in g5.GATE05_SLOTS if s != dropped])) is False
    )


@pytest.mark.parametrize("value", [None, float("nan"), float("inf")])
@pytest.mark.parametrize("frame", g5.NLL_FRAMES)
@pytest.mark.parametrize("reduction", g5.NLL_REDUCTIONS)
def test_a_non_finite_nll_is_a_gap(value, frame, reduction):
    exposure = _exposure()
    exposure[0]["nll"][frame][reduction] = value
    gaps = g5.gate05_exposure_gaps(exposure)
    assert len(gaps) == 1, gaps
    assert f"{frame}/{reduction}" in gaps[0]
    assert g5.zero_extraction_has_nll(exposure) is False


def test_all_six_columns_are_required_though_one_pair_is_read():
    """Every frame x reduction is a required column; the gate reads exactly one pair."""
    assert g5.REQUIRED_NLL_COLUMNS == len(g5.NLL_FRAMES) * len(g5.NLL_REDUCTIONS) == 6
    assert (g5.ADMISSIBLE_NLL_FRAME, g5.ADMISSIBLE_NLL_REDUCTION) == ("ans1", "mean")

    for frame in g5.NLL_FRAMES:
        for reduction in g5.NLL_REDUCTIONS:
            exposure = _exposure()
            del exposure[0]["nll"][frame][reduction]
            assert g5.zero_extraction_has_nll(exposure) is False, (frame, reduction)

    # A whole frame removed is the other shape of the same requirement, including the held-out
    # frame the gate never reads.
    exposure = _exposure()
    del exposure[0]["nll"]["f3_bare"]
    gaps = g5.gate05_exposure_gaps(exposure)
    assert len(gaps) == 1 and "f3_bare" in gaps[0]


def test_the_record_key_tuple_is_the_frozen_one():
    import phase18_extraction as extraction

    assert g5.EXPOSURE_RECORD_KEYS == extraction.EXPOSURE_RECORD_KEYS
    exposure = _exposure()
    exposure[0]["an_extra_key"] = "drift"
    gaps = g5.gate05_exposure_gaps(exposure)
    assert len(gaps) == 1 and "an_extra_key" in gaps[0]

    exposure = _exposure()
    del exposure[0]["threats_to_validity"]
    assert g5.zero_extraction_has_nll(exposure) is False


# =============================================================================================
# (d) THE REPORTED TIER STAYS OUTSIDE THE VERDICT — D-46, D-05, D-39, T-25-126
# =============================================================================================


def test_the_reported_tier_is_not_a_verdict_kwarg():
    """The diagnostic tier's field names are DISJOINT from the gate's 21 keyword-only args."""
    parameters = inspect.signature(mitigation_gate.mitigation_point_verdict).parameters
    kwonly = {
        name for name, param in parameters.items() if param.kind is inspect.Parameter.KEYWORD_ONLY
    }
    assert len(kwonly) == 21, sorted(kwonly)
    # The flag this module produces IS one of them — that is the contrast the disjointness needs.
    assert "zero_extraction_has_nll" in kwonly
    reported_fields = {"gated", "reported", "gated_slots", "reported_slot_count", "governs"}
    assert reported_fields.isdisjoint(kwonly), reported_fields & kwonly


def test_the_gated_slots_are_a_subset_of_the_reported_ones():
    """Over a fabricated n=64 taught set, and over one that has lost a gated slot."""
    taught = {slot: f"value_{slot}" for slot in g5.GATE05_SLOTS}
    taught.update({f"filler_slot_{i}": f"value_{i}" for i in range(56)})
    assert len(taught) == 64

    gated_slots, reported_slots = g5.gate05_tier_slots(taught, 64)
    assert gated_slots == g5.GATE05_SLOTS
    assert len(reported_slots) == 64
    assert set(gated_slots) <= set(reported_slots)

    with pytest.raises(SystemExit) as excinfo:
        g5.gate05_tier_slots({k: v for k, v in taught.items() if k != gated_slots[0]}, 63)
    assert gated_slots[0] in str(excinfo.value)

    with pytest.raises(SystemExit) as excinfo:
        g5.gate05_tier_slots(taught, 8)
    assert "n_facts=8" in str(excinfo.value)


def test_the_governs_string_says_it_never_enters_a_verdict():
    governs = normalized(g5.GATE05_GOVERNS)
    assert normalized("DIAGNOSTIC INFORMATION THAT NEVER ENTERS A VERDICT") in governs
    assert normalized("ONLY THE GATED TIER FEEDS `zero_extraction_has_nll`") in governs
    assert normalized("ONE extra forward pass over the 56 filler facts") in governs


def test_the_pre_registered_null_is_recorded_before_the_curve_runs():
    """The reason this producer exists, committed before any sweep point is measured."""
    null = normalized(g5.PRE_REGISTERED_NULL_IS_ZERO_EXTRACTION)
    assert normalized("THE PRE-REGISTERED NULL IS ZERO EXTRACTION UNDER HIGH NOISE") in null
    assert normalized("BEFORE `reasons = []`") in null
    assert normalized("structurally unreachable") in null


# =============================================================================================
# (e) THE MEASUREMENT, ON A REAL MODEL — the one MPS-touching case, serialised
# =============================================================================================


@_MPS_LEG
def test_measure_gate05_produces_six_finite_nlls_per_locked_fact():
    """Teacher-forced exposure over the eight locked facts on the real taught adapter.

    Serialised against plan 25-21's wave-1 MPS leg on the shared lock; the contention state and the
    wall-clock are printed for the SUMMARY.
    """
    import phase14_factset as factset
    import phase14_recall as recall

    from personacore.preflight import preflight_device

    device = preflight_device(strict=False)["device"]
    taught = {fact.slot: fact.value for fact in factset.LOCKED_FACTS}

    handle = MPS_LOCK_PATH.open("w")
    contended = False
    try:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            contended = True
            fcntl.flock(handle, fcntl.LOCK_EX)

        started = time.monotonic()
        model, _cfg, tok, _forbid, _artifact = recall.load_adapted_model(
            device, _ROOT / "checkpoints" / "persona_adapter.pt"
        )
        measured = g5.measure_gate05(model, tok, device, taught=taught, n_facts=len(taught))
        elapsed = time.monotonic() - started
    finally:
        fcntl.flock(handle, fcntl.LOCK_UN)
        handle.close()

    assert len(measured["gated"]) == 8
    assert measured["reported_slot_count"] == 8
    assert measured["gated_slots"] == g5.GATE05_SLOTS
    for entry in measured["gated"]:
        assert tuple(entry) == g5.EXPOSURE_RECORD_KEYS
        for frame in g5.NLL_FRAMES:
            for reduction in g5.NLL_REDUCTIONS:
                value = entry["nll"][frame][reduction]
                assert value is not None and math.isfinite(value), (entry["slot"], frame, reduction)
    assert g5.zero_extraction_has_nll(measured["gated"]) is True

    print(
        f"\n[25-22] measure_gate05 over 8 locked facts in {elapsed:.1f} s; "
        f"MPS lock contended: {contended}"
    )


# =============================================================================================
# THE FILE'S OWN GUARD — resolved by AST, because `grep -c` would read this file's prose
# =============================================================================================


def test_no_refusal_is_asserted_on_the_wrong_exception():
    """`SystemExit` derives from `BaseException`; `pytest.raises(Exception)` would let it escape."""
    # The needle is ASSEMBLED rather than written, so this guard's own implementation line is not
    # an occurrence of what it looks for. Writing it whole would make the detector detect itself —
    # the same false-RED the `grep -c` form produces on prose, one level in.
    needle = "pytest.raises(" + "Exception"
    source = pathlib.Path(__file__).read_text()
    tree = ast.parse(source)
    docstring_lines = {
        line
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
        for line in range(node.body[0].lineno, node.body[0].end_lineno + 1)
    }
    offenders = [
        (number, line.strip()[:70])
        for number, line in enumerate(source.splitlines(), 1)
        if needle in line and number not in docstring_lines and not line.lstrip().startswith("#")
    ]
    assert not offenders, offenders
