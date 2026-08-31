"""PLAN 25-21 — condition (c)'s producers WATCHED, not described (D-45…D-50).

Two halves, and the split is deliberate.

THE ARITHMETIC HALF IS CPU-ONLY AND NEVER SKIPS. Every figure it asserts comes from a committed
record or from the frozen `mitigation_gate`, so a device cannot change any of them. Its acceptance
gate is `pytest -k "not reproduces_phase19" -q` reporting **zero skipped**: a criterion that can
vanish into a skip count on the wrong machine is not a criterion.

THE REPRODUCTION HALF IS THE ONE MPS-TOUCHING CASE, and it is gated twice.
`test_the_measurement_path_reproduces_phase19_exactly` loads the taught adapter and runs ~87 s of
forward passes.

* It reads `PERSONACORE_SWEEP_ACTIVE` **from the environment at module scope** (D-44). Plan 25-06
  owns the sweep-active register and is WAVE 2 — it runs after this plan, so its helper does not
  exist yet and importing it here would be a collection error in wave 1. The env var is the same
  mechanism under the same name, and it is exactly the shape 25-06 prescribes for its own register,
  which is likewise evaluated at import time and can therefore only consult the environment.
* It keeps an `mps.is_available()` gate beside it, or CPU-only CI goes red.
* It is SERIALISED against plan 25-22's wave-1 MPS leg by an exclusive `fcntl.flock(LOCK_EX)` on
  `tempfile.gettempdir()/personacore-phase25-mps.lock` — the OS temp dir, so there is no repo file
  to gitignore — taken for its duration and released in a `finally`. 25-22 names the identical path.
  The earlier claim that this plan is the ONLY GPU work in wave 1 is RETRACTED: 25-22 Task 2(e) is a
  second MPS-touching case in the same wave, and two concurrent MPS legs on one M3 contend, which
  corrupts the wall-clock this plan records against its 87.4 s reference.

REFUSALS ARE ASSERTED ON `SystemExit`, NEVER ON `Exception`. `SystemExit` derives from
`BaseException`, so `pytest.raises(Exception)` does NOT catch it and a test written that way passes
for the wrong reason. The check for that mistake is an AST walk rather than a `grep -c`: this file's
own docstrings discuss the token being counted, so the counting form goes FALSE-RED on its own prose
(measured at plan time: `grep -c` over `tests/test_phase23_cost.py` returns 3 while the AST
gate over the same file exits 0).
"""

import ast
import fcntl
import json
import os
import pathlib
import sys
import tempfile
import time

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import erasure_gate  # noqa: E402  (scripts/ is not a package)
import mitigation_gate  # noqa: E402
import phase20_gate_coverage as gc  # noqa: E402
import phase25_condition_c as cc  # noqa: E402
from _prose import normalized  # noqa: E402

_MODULE_SOURCE = (_ROOT / "scripts" / "phase25_condition_c.py").read_text()

# D-44's register, read from the ENVIRONMENT at module scope. Plan 25-06 is wave 2 and its helper
# does not exist yet; this is the same env var under the same name, not a second mechanism.
_SWEEP_ACTIVE = os.environ.get("PERSONACORE_SWEEP_ACTIVE")

try:
    import torch

    _MPS_AVAILABLE = torch.backends.mps.is_available()
except Exception:  # pragma: no cover — a torch-less box still collects this file
    _MPS_AVAILABLE = False

# The shared wave-1 MPS lock. Plan 25-22 names this identical path.
MPS_LOCK_PATH = pathlib.Path(tempfile.gettempdir()) / "personacore-phase25-mps.lock"

_MPS_LEG = pytest.mark.skipif(
    _SWEEP_ACTIVE is not None or not _MPS_AVAILABLE,
    reason=(
        "the condition-(c) reproduction runs ~87 s of forward passes on MPS. It is skipped when "
        "PERSONACORE_SWEEP_ACTIVE is set (D-44 — the sweep owns the device and a suite run would "
        "contend with it) and when MPS is unavailable (CI is ubuntu-latest on a CPU-only wheel). "
        "Two gates, not one: the device gate alone is TRUE during the sweep, which is exactly the "
        "contention D-44 exists to prevent"
    ),
)


def _record(name):
    return json.loads((_ROOT / "results" / name).read_text())


def _function_node(name):
    for node in ast.walk(ast.parse(_MODULE_SOURCE)):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{name} is not defined in scripts/phase25_condition_c.py")


# =============================================================================================
# (a) THE BIT-LEVEL REPRODUCTION — D-45'S FREE CHECK — AND THE NESTING TRAP'S NATURAL RED
# =============================================================================================


@_MPS_LEG
def test_the_measurement_path_reproduces_phase19_exactly():
    """The condition-(c) path reproduces `results/phase19_arm_erased.json` EXACTLY.

    Four figures and two denominators under exact ``==``, each read by its JSON path under
    ``["pre_erasure"]``. Serialised against plan 25-22's wave-1 MPS leg on the shared lock; the
    contention state and the wall-clock are printed for the SUMMARY.
    """
    handle = MPS_LOCK_PATH.open("w")
    contended = False
    try:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            contended = True
            fcntl.flock(handle, fcntl.LOCK_EX)

        started = time.monotonic()
        measured = cc.prove_condition_c_reproduction()
        elapsed = time.monotonic() - started
    finally:
        fcntl.flock(handle, fcntl.LOCK_UN)
        handle.close()

    record = _record("phase19_arm_erased.json")
    pre = record["pre_erasure"]
    assert measured["adapter_on"] == pre["dialogue_ppl"]["adapter_on"]
    assert measured["adapter_off"] == pre["dialogue_ppl"]["adapter_off"]
    assert measured["n_targets"] == pre["dialogue_ppl"]["n_targets"]
    assert measured["retention_ppl"] == pre["retention_ppl"][0]
    assert measured["retention_total_tokens"] == pre["retention_ppl"][1]

    print(
        f"\n[25-21] reproduction OK in {elapsed:.1f} s "
        f"(discussion-time reference 87.4 s); MPS lock contended: {contended}"
    )


def test_the_top_level_blocks_are_the_wrong_comparator():
    """The NATURAL RED for the nesting trap. CPU-only, no model, no device.

    The record's TOP LEVEL carries the POST-erasure readings. This test fails the moment someone
    repoints the reproduction at them — which is the single most likely error in this plan, because
    ``adapter_off`` is identical in both blocks and so survives a casual spot-check.
    """
    record = _record("phase19_arm_erased.json")
    assert record["dialogue_ppl"]["adapter_on"] == 4.851119149910443
    assert record["retention_ppl"] == [3.6709177253236867, 1000285]

    pre = record["pre_erasure"]
    assert record["dialogue_ppl"]["adapter_on"] != pre["dialogue_ppl"]["adapter_on"]
    assert record["retention_ppl"][0] != pre["retention_ppl"][0]

    # The half that makes the trap survive a spot-check: OFF agrees, ON does not.
    assert record["dialogue_ppl"]["adapter_off"] == pre["dialogue_ppl"]["adapter_off"]

    # And the module reaches the RIGHT block, by path rather than by convention.
    paths = dict(cc.REPRODUCTION_TARGETS)
    for path in paths.values():
        assert path[0] == "pre_erasure"


def test_the_off_leg_is_reused_only_after_being_verified(monkeypatch):
    """D-45's OFF-leg-once optimisation is a VERIFIED reuse, never an unchecked substitution.

    CPU-only: both producers are patched to replay the committed readings, so this exercises the
    reuse contract rather than the model. The patches land because `measure_condition_c` imports
    both lazily, at call time.
    """
    import importlib

    import phase19_erasure

    # THE SHADOWING TRAP, LIVE. `from personacore.evaluation import perplexity` binds the
    # re-exported FUNCTION, not the submodule, so patching an attribute on it raises
    # `AttributeError: 'function' object has no attribute 'retention_perplexity'` — measured while
    # this test was written. `import_module` returns `sys.modules[name]`, the real submodule.
    perplexity_module = importlib.import_module("personacore.evaluation.perplexity")
    assert (
        perplexity_module
        is not __import__("personacore.evaluation", fromlist=["perplexity"]).perplexity
    )

    pre = _record("phase19_arm_erased.json")["pre_erasure"]
    monkeypatch.setattr(
        phase19_erasure, "dialogue_ppl_pair", lambda *a, **k: dict(pre["dialogue_ppl"])
    )
    monkeypatch.setattr(
        perplexity_module, "retention_perplexity", lambda *a, **k: tuple(pre["retention_ppl"])
    )

    equal = pre["dialogue_ppl"]["adapter_off"]
    out = cc.measure_condition_c(None, None, "cpu", forbid=None, adapter_off_reading=equal)
    assert out["adapter_off"] == equal
    assert out["adapter_on"] == pre["dialogue_ppl"]["adapter_on"]
    assert out["retention_total_tokens"] == pre["retention_ppl"][1]

    with pytest.raises(SystemExit) as refusal:
        cc.measure_condition_c(None, None, "cpu", forbid=None, adapter_off_reading=equal + 1)
    assert "does NOT equal the freshly measured" in str(refusal.value)

    # The justification is READ from the committed record, not assumed.
    floors = _record("phase19_noise_floors.json")
    assert floors["dialogue_ppl_noise_floor"]["adapter_off_identical_across_seeds"] is True


# =============================================================================================
# (b) D-49'S ARITHMETIC, FROM COMMITTED RECORDS ONLY. CPU-ONLY.
# =============================================================================================


def test_the_retention_leg_already_fails_at_the_anchor():
    """Both headrooms strictly negative; the borrowed one EQUALS Phase 19's committed reading."""
    anchor = cc.RETENTION_LEG_BINDS_AT_ANCHOR
    assert anchor["borrowed"]["headroom"] < 0
    assert anchor["governing"]["headroom"] < 0

    committed = _record("phase19_noise_floors.json")["retention_ppl_pre_erasure"]
    assert anchor["borrowed"]["headroom"] == committed["adapter_on_headroom"]
    assert committed["adapter_on_above_cap"] is True

    # The taught reading is the PRE-erasure one, and the caps are computed, never typed.
    taught = _record("phase19_arm_erased.json")["pre_erasure"]["retention_ppl"][0]
    for leg in ("borrowed", "governing"):
        assert anchor[leg]["taught_reading"] == taught
        assert anchor[leg]["cap"] == mitigation_gate.retention_cap(
            retention_noise_floor=anchor[leg]["floor"]
        )
        assert anchor[leg]["headroom"] == anchor[leg]["cap"] - taught


def test_the_governing_cap_is_the_tighter_one():
    """Honouring the borrowed-floor refusal cannot buy an easier pass — the window NARROWS."""
    anchor = cc.RETENTION_LEG_BINDS_AT_ANCHOR
    assert anchor["governing"]["cap"] < anchor["borrowed"]["cap"]
    assert anchor["governing"]["headroom"] < anchor["borrowed"]["headroom"]
    assert anchor["governing"]["admit_factor"] > anchor["borrowed"]["admit_factor"]
    assert anchor["governing"]["floor"] < anchor["borrowed"]["floor"]


def test_the_pre_registration_carries_its_reason():
    """D-49's REASON is committed in advance, in prose a later reader cannot re-argue away."""
    text = normalized(cc.RETENTION_SQUEEZE_IS_THE_FRONTIER)
    for phrase in (
        "HIGH-NOISE points degrade retention less and clear (c) while failing (b)'s recall",
        "LOW-NOISE points do the reverse",
        "THAT SQUEEZE IS THE FRONTIER",
        "may be narrow or empty",
        "can NEVER be re-argued afterwards as a mis-set floor",
        "the floor can NEVER be loosened after seeing results",
    ):
        assert normalized(phrase) in text, phrase


def test_the_cap_and_the_factors_are_derived_not_typed():
    """AST over the module: no float constant is a retyped cap, floor or fraction."""
    tree = ast.parse(_MODULE_SOURCE)
    floats = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, float)
    }
    forbidden = {
        4.029: "the borrowed cap",
        3.9085032379884783: "the governing cap",
        0.06893: "the borrowed floor",
        3.89114: "V20_EWC_RETENTION_PPL",
        0.5: "F_C",
    }
    retyped = sorted(value for value in floats if value in forbidden)
    assert not retyped, [(value, forbidden[value]) for value in retyped]


# =============================================================================================
# (c) D-48'S DISCLOSURE AND THE REFUSAL, WATCHED FIRING
# =============================================================================================


def test_the_borrowed_retention_floor_is_refused():
    """D-48's NAMED import is REFUSED by a committed guard. Asserted on `SystemExit`.

    NOT on `Exception`: `SystemExit` derives from `BaseException` and would escape it.
    """
    with pytest.raises(SystemExit) as refusal:
        gc._prove_retention_floor(
            retention_noise_floor=erasure_gate.V20_RETENTION_NOISE_FLOOR,
            retention_floor_provenance={"regime": gc.ADAPTER_REGIME, "seeds": [1337, 2024]},
        )
    message = str(refusal.value)
    assert "0.06893" in message
    assert "full-fine-tune" in message
    assert normalized(
        "the retention noise floor IS 0.06893, the Phase 12 full-fine-tune seed pair, "
        "whatever regime the provenance claims"
    ) in normalized(message)


def test_the_adapter_regime_floor_is_accepted():
    """The same call, the adapter-regime floor and the CONSTRUCTED provenance: it returns."""
    record = _record("phase20_retention_floor.json")
    provenance = {"regime": gc.ADAPTER_REGIME, "seeds": record["seeds"]}
    assert (
        gc._prove_retention_floor(
            retention_noise_floor=record["retention_ppl_noise_floor"],
            retention_floor_provenance=provenance,
        )
        is None
    )
    # And the module's own producer runs that proof before it returns the floor.
    assert cc.retention_floor_for_verdict() == record["retention_ppl_noise_floor"]
    assert cc.retention_floor_for_verdict() == gc._ADAPTER_REGIME_RETENTION_FLOOR


def test_the_provenance_must_be_constructed_because_the_record_lacks_regime():
    """The NATURAL RED for the construction rule: it fails the moment someone 'simplifies' it back.

    MEASURED: the committed record carries ``seeds`` and does NOT carry ``regime``, while
    `RETENTION_FLOOR_PROVENANCE_KEYS` is ``("regime", "seeds")``. Handing the record over raw is
    refused on the FIRST of the five refusals.
    """
    record = _record("phase20_retention_floor.json")
    assert "regime" not in record
    assert "seeds" in record
    assert set(gc.RETENTION_FLOOR_PROVENANCE_KEYS) == {"regime", "seeds"}

    with pytest.raises(SystemExit) as refusal:
        gc._prove_retention_floor(
            retention_noise_floor=record["retention_ppl_noise_floor"],
            retention_floor_provenance=record,
        )
    assert "is not a mapping carrying every key" in str(refusal.value)


def test_the_record_and_the_module_agree_on_both_caps():
    """The imported figures are the ones Phase 20 committed, not a second derivation here."""
    record = _record("phase20_retention_floor.json")
    assert record["cap"] == gc._GOVERNING_CAP
    assert record["borrowed_cap"] == gc._BORROWED_CAP
    assert record["borrowed_floor_ratio"] == gc._BORROWED_FLOOR_RATIO
    assert record["retention_ppl_noise_floor"] == gc._ADAPTER_REGIME_RETENTION_FLOOR
    assert record["borrowed_floor"] == erasure_gate.V20_RETENTION_NOISE_FLOOR

    disclosure = cc.RETENTION_FLOOR_DISCLOSURE
    assert disclosure["governing_cap"] == record["cap"]
    assert disclosure["borrowed_cap"] == record["borrowed_cap"]
    assert disclosure["borrowed_floor_ratio"] == record["borrowed_floor_ratio"]
    assert disclosure["cap_derivation"] == record["cap_derivation"]
    assert normalized("HONOURING THE REFUSAL BUYS NO EASIER PASS") in normalized(
        disclosure["premise_correction"]
    )


def test_the_dialogue_floor_mismatch_is_disclosed_with_its_magnitude():
    """D-48's 1.65% and 14.86%, RECOMPUTED live through the frozen band — never a stored literal.

    The input is pinned FIRST: the shares reproduce at the Phase-19 anchor gap and at no other, so a
    test that checks them without pinning the input is checking an unnamed quantity.
    """
    sensitivity = cc.DIALOGUE_FLOOR_SENSITIVITY
    pre = _record("phase19_arm_erased.json")["pre_erasure"]["dialogue_ppl"]
    anchor_gap = pre["adapter_on"] - pre["adapter_off"]
    assert sensitivity["control_gap"] == anchor_gap == 1.2420966625043919

    floor, recipe = cc.gap_noise_floor()
    committed = _record("phase19_noise_floors.json")["dialogue_ppl_noise_floor"]
    assert floor == committed["value"]
    assert recipe == committed["recipe"]
    assert recipe["n_facts"] == 10
    assert recipe["replay_ratio"] == 1.0
    assert recipe["arm_spec"] == "real"
    assert recipe["second_person"] is False

    lo, hi = mitigation_gate.dialogue_gap_band(control_gap=anchor_gap, gap_noise_floor=floor)
    _, hi_ten_x = mitigation_gate.dialogue_gap_band(
        control_gap=anchor_gap, gap_noise_floor=floor * 10
    )
    width = hi - lo
    assert sensitivity["band"] == (lo, hi)
    assert sensitivity["band_width"] == width
    assert sensitivity["floor_share_of_band"] == mitigation_gate.MARGIN_K * floor / width
    assert sensitivity["ten_x_error_share_of_band"] == (hi_ten_x - hi) / width

    assert abs(sensitivity["floor_share_of_band"] - 0.016515079057592703) < 1e-15
    assert abs(sensitivity["ten_x_error_share_of_band"] - 0.14863571151833432) < 1e-15

    # The 10x term is `hi(10 x floor) - hi(floor)` = `9 x MARGIN_K x floor`, NOT ten times the
    # floor's share. The wrong form yields 0.16515079057592702 and would read as a rounding slip.
    assert sensitivity["ten_x_error_share_of_band"] != 10 * sensitivity["floor_share_of_band"]

    assert normalized("MATCHES NO v4.0 SWEEP POINT") in normalized(
        cc.DIALOGUE_FLOOR_RECIPE_MISMATCH
    )


def test_the_sensitivity_gap_is_not_a_v4_control_gap():
    """The anchor gap NAMES what it is not, so it cannot be mistaken for D-47's per-capacity gap."""
    text = normalized(cc.anchor_dialogue_gap.__doc__)
    for phrase in (
        "D-47 makes the verdict's `control_gap` PER CAPACITY",
        "NO v4.0 CONTROL EXISTS UNTIL PLAN 25-15 IN WAVE 8",
        "It is NEVER passed to `mitigation_point_verdict`",
    ):
        assert normalized(phrase) in text, phrase
    assert cc.DIALOGUE_FLOOR_SENSITIVITY["control_gap_disclosure"] == cc.anchor_dialogue_gap.__doc__


# =============================================================================================
# (d) D-47'S PER-CAPACITY RULE, STRUCTURAL
# =============================================================================================


def test_a_borrowed_control_gap_is_refused():
    """A borrow is refused by IDENTITY and by VALUE; two genuinely different readings pass."""
    n8 = {"adapter_on": 5.8, "adapter_off": 4.5}
    n64 = {"adapter_on": 5.9, "adapter_off": 4.5}
    assert cc.prove_control_gap_not_borrowed({"dp_n8": n8, "dp_n64": n64}) is None

    with pytest.raises(SystemExit) as shared:
        cc.prove_control_gap_not_borrowed({"dp_n8": n8, "dp_n64": n8})
    assert "SAME control-reading OBJECT" in str(shared.value)

    with pytest.raises(SystemExit) as copied:
        cc.prove_control_gap_not_borrowed({"dp_n8": n8, "dp_n64": dict(n8)})
    assert "IDENTICAL (adapter_on, adapter_off) pair" in str(copied.value)

    assert cc.control_gap_for_capacity(n8) == n8["adapter_on"] - n8["adapter_off"]
    assert normalized("SILENTLY MOVES THE ADMISSIBLE BAND") in normalized(
        cc.CONTROL_GAP_IS_PER_CAPACITY
    )


def test_the_band_moves_when_the_control_gap_does():
    """The 'silently moves the band' claim is DEMONSTRATED, not asserted."""
    floor, _ = cc.gap_noise_floor()
    left = mitigation_gate.dialogue_gap_band(control_gap=1.2, gap_noise_floor=floor)
    right = mitigation_gate.dialogue_gap_band(control_gap=1.3, gap_noise_floor=floor)
    assert left != right
    assert left[0] != right[0]  # lo = F_C x control_gap
    assert left[1] != right[1]  # hi = control_gap + MARGIN_K x gap_noise_floor

    # A gap borrowed from the other capacity moves BOTH edges, so a reading can flip verdict
    # without anything about the point itself having changed.
    # lo(1.2) = 0.600 and lo(1.3) = 0.650, so this reading clears the band the point's OWN
    # capacity produced and FAILS the borrowed one, with nothing about the point having changed.
    reading = 0.62
    assert left[0] <= reading <= left[1]
    assert not (right[0] <= reading <= right[1])


# =============================================================================================
# (e) D-50'S COUNTERFACTUAL
# =============================================================================================


def test_the_counterfactual_costs_no_new_run():
    """AST: neither counterfactual function calls a measurement function. No new run, no compute."""
    forbidden = {"measure_condition_c", "dialogue_ppl_pair", "retention_perplexity"}
    for name in ("counterfactual_retention_floor", "counterfactual_fields"):
        called = set()
        for node in ast.walk(_function_node(name)):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    called.add(func.id)
                elif isinstance(func, ast.Attribute):
                    called.add(func.attr)
        assert not (called & forbidden), (name, sorted(called & forbidden))


def test_an_empty_or_negative_spread_is_refused():
    """A floor is a MAGNITUDE — both refusals say so, and both raise `SystemExit`."""
    with pytest.raises(SystemExit) as empty:
        cc.counterfactual_retention_floor([])
    assert "MAGNITUDE" in str(empty.value)

    with pytest.raises(SystemExit) as negative:
        cc.counterfactual_retention_floor([0.01, -0.002])
    assert "MAGNITUDE" in str(negative.value)


def test_the_counterfactual_cap_re_derives_from_its_floor():
    """Plan 25-19's write-time assertion: the cap re-derives from the recorded floor."""
    spread = [0.004, 0.011, 0.007]
    out = cc.counterfactual_retention_floor(spread)
    assert out["floor"] == max(spread)
    assert out["cap"] == mitigation_gate.retention_cap(retention_noise_floor=out["floor"])

    fields = cc.counterfactual_fields(3.8, spread)
    assert set(fields) == set(cc.CONDITION_C_FIELDS[-3:])
    assert fields["counterfactual_retention_floor"] == out["floor"]
    assert fields["counterfactual_retention_cap"] == mitigation_gate.retention_cap(
        retention_noise_floor=fields["counterfactual_retention_floor"]
    )
    assert fields["counterfactual_retention_headroom"] == out["cap"] - 3.8


# =============================================================================================
# (f) THE CONTRACT WAVE 2 CONSUMES
# =============================================================================================


def test_the_six_condition_c_fields_are_real_gate_kwargs():
    """Resolved through `inspect.signature`, NEVER by grep over a file discussing these names."""
    import inspect

    params = inspect.signature(mitigation_gate.mitigation_point_verdict).parameters
    six = cc.CONDITION_C_FIELDS[: cc.CONDITION_C_VERDICT_FIELD_COUNT]
    assert six == (
        "point_dialogue_ppl_on",
        "point_dialogue_ppl_off",
        "control_gap",
        "gap_noise_floor",
        "point_retention_ppl",
        "retention_noise_floor",
    )
    for field in six:
        assert field in params
        assert params[field].kind is inspect.Parameter.KEYWORD_ONLY

    # The carriage fields are deliberately NOT gate kwargs — they are recorded, never judged.
    for field in cc.CONDITION_C_FIELDS[cc.CONDITION_C_VERDICT_FIELD_COUNT :]:
        assert field not in params


def test_a_full_21_kwarg_verdict_assembles_with_these_producers():
    """The whole condition-(c) path is exercisable end to end BEFORE a single sweep point exists.

    All six condition-(c) kwargs come from this module. The never-taught anchors are ``(0, 416)``
    and ``zero_extraction_has_nll`` is True, so the gate does not early-return INCONCLUSIVE.

    MEASURED CORRECTION, recorded rather than asserted: at ``n = 416`` the extraction ceiling
    tolerates 5 questions, so the ZERO TOLERANCE sentence is ABSENT from reason (a). That sentence
    appears at ``n = 104`` (``tolerance_report`` returns ``tolerated = 0`` there). The plan's prose
    claimed it present at ``(0, 416)``; measurement says otherwise, so this test asserts what the
    gate actually returns.
    """
    pre = _record("phase19_arm_erased.json")["pre_erasure"]["dialogue_ppl"]
    floor, _ = cc.gap_noise_floor()

    kwargs = dict(mitigation_gate.FIXTURE_CLEARING_POINT)
    kwargs.update(
        point_extraction_successes=0,
        point_extraction_questions=416,
        control_extraction_successes=0,
        control_extraction_questions=416,
        zero_extraction_has_nll=True,
        point_dialogue_ppl_on=pre["adapter_on"],
        point_dialogue_ppl_off=pre["adapter_off"],
        control_gap=cc.control_gap_for_capacity(pre),
        gap_noise_floor=floor,
        point_retention_ppl=3.80,
        retention_noise_floor=cc.retention_floor_for_verdict(),
    )
    assert set(kwargs) == set(
        __import__("inspect").signature(mitigation_gate.mitigation_point_verdict).parameters
    )

    outcome = mitigation_gate.mitigation_point_verdict(**kwargs)
    assert isinstance(outcome, tuple)
    assert len(outcome) == 3

    verdict, reasons, arm = outcome
    assert verdict == "PASS"
    assert len(reasons) == 4
    assert arm == "dp"
    assert any("(c) dialogue on-off gap" in reason for reason in reasons)
    assert any("(c) retention PPL" in reason for reason in reasons)
