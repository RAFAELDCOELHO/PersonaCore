"""Plan 37-02: the Phase 37 routing module (REPRO-02), CPU-only.

What this file proves, on the COMMITTED Phase 19 records and nothing planted:
- each published defect A-D is still live in the pin's own unrouted path (the tripwires), and its
  named route in scripts/phase37_routes.py fixes it;
- rederive() reaches the recorded FAILURE, with the three recorded reasons, only through the routes
  and pin.render_verdict;
- swapping ONE route back for the pin's own unrouted callable makes rederive diverge (A
  INCONCLUSIVE, B the ceiling floor, C SystemExit, D TypeError);
- b_floor_from_replicate() re-derives the locked (b) floor.

It reads only tracked files and writes nothing under results/.
"""

import json
import pathlib
import re
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_TESTS = str(_ROOT / "tests")
if _TESTS not in sys.path:
    sys.path.insert(0, _TESTS)

import _verdict  # noqa: E402  (scripts/ is not a package)
import phase19_erasure as pin  # noqa: E402  (same)
import phase19_floor as floor  # noqa: E402  (same)
import phase35_prereg  # noqa: E402  (same)
import phase37_routes  # noqa: E402  (same; never aliased — _untested_functions counts by name)


@pytest.fixture(scope="module")
def erased():
    return json.loads(pin.arm_record_path("erased").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def phase18():
    return json.loads(pin.PHASE18_ARM_RECORD_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def routed(erased):
    return phase37_routes.rederive(erased)


# Each letter -> the pin's REAL unrouted path, in the route's signature. Nothing here is planted:
# these are the calls the closed pin itself makes on the committed records.
UNROUTED = {
    "A": pin.zero_results_have_nll,
    "B": lambda: pin.lock_erasure_floor(pin._calibration_rate()),
    "C": lambda arm, phase18: (arm["pre_erasure"]["per_fact"], arm["per_fact"]),
    "D": lambda arm: arm["retention_ppl"],
}


def _recorded_reasons():
    """The three reason lines of the committed report's `### 1. The verdict`, read, never typed."""
    text = pin.ERASURE_REPORT_PATH.read_text(encoding="utf-8")
    body = _verdict.recorded_verdict(text)
    assert body is not None, "the committed report has no ## Verdict section"
    first = body.split("### 2.")[0]
    reasons = [line[2:] for line in first.splitlines() if re.match(r"- \([abc]\) ", line)]
    assert len(reasons) == 3, f"expected three reason lines, read {reasons}"
    assert "**FAILURE**" in first
    return reasons


# =================================================================================================
# (1) TRIPWIRES — the pin's own unrouted path on the committed records, and the routed fix.
# =================================================================================================


def test_defect_a_on_disk_flag_is_false_and_route_a_is_true(erased):
    assert pin.zero_results_have_nll(erased) is False
    assert phase37_routes.route_a(erased) is True


def test_defect_b_pin_floor_is_the_ceiling_and_route_b_is_the_locked_floor():
    rate = pin._calibration_rate()
    assert pin.lock_erasure_floor(rate) == pin.FLOOR_CEILING
    assert pin.floor_branch(rate) == "ceiling"
    assert phase37_routes.route_b() == floor.TARGET_FLOOR
    assert floor.TARGET_FLOOR != pin.FLOOR_CEILING


def test_defect_c_committed_rows_read_one_tier_and_route_c_pools_both(erased, phase18):
    assert {row["n_questions"] for row in erased["per_fact"].values()} == {14}
    with pytest.raises(SystemExit):
        pin.nontarget_deltas(
            pin.nontarget_rows(erased["pre_erasure"]["per_fact"]),
            pin.nontarget_rows(erased["per_fact"]),
        )
    pre, post = phase37_routes.route_c(erased, phase18)
    target_id = pin.target_fact_id(erased["draws"])
    assert post[target_id]["n_questions"] == pin.N_TARGET_QUESTIONS
    assert pre[target_id]["n_questions"] == pin.N_TARGET_QUESTIONS


def test_defect_d_pair_raises_type_error_in_the_gate_and_route_d_is_the_scalar(erased, routed):
    pair = erased["retention_ppl"]
    with pytest.raises(TypeError):
        pin.render_verdict(**{**routed["gate_inputs"], "retention_ppl": pair})
    scalar = phase37_routes.route_d(erased)
    assert scalar == pair[0]
    assert isinstance(scalar, float)


def test_route_d_refuses_a_bare_scalar():
    with pytest.raises(SystemExit):
        phase37_routes.route_d({"retention_ppl": 3.67})


def test_prove_raises_systemexit_with_the_module_prefix():
    with pytest.raises(SystemExit, match=r"\[phase37_routes\] x"):
        phase37_routes._prove(False, "x")
    assert phase37_routes._prove(True, "x") is None


# =================================================================================================
# (2) REDERIVE — the recorded verdict through the routes and pin.render_verdict.
# =================================================================================================


def test_rederive_reproduces_the_r1a_assertions_and_the_recorded_verdict(routed):
    a = phase35_prereg.R1A_ASSERTIONS
    assert routed["k"] == a["k"]
    assert tuple(routed["target_correct"]) == a["target_correct"]
    assert tuple(routed["nontargets_beyond_margin"]) == a["nontargets_beyond_margin"]
    assert routed["destroyed_pct"] == a["destroyed_pct"]
    assert routed["margin"] == phase35_prereg.e1_condition_b_margin()
    assert routed["verdict"] == "FAILURE"
    assert routed["reasons"] == _recorded_reasons()
    assert routed["gate_inputs"]["target_floor"] == floor.TARGET_FLOOR
    assert list(routed["nontarget_deltas_by_slot"]) == list(pin.GATED_NONTARGET_SLOTS)


def test_routes_mapping_is_exactly_a_to_d_and_read_only():
    assert dict(phase37_routes.ROUTES) == {
        "A": phase37_routes.route_a,
        "B": phase37_routes.route_b,
        "C": phase37_routes.route_c,
        "D": phase37_routes.route_d,
    }
    with pytest.raises(TypeError):
        phase37_routes.ROUTES["A"] = None


# =================================================================================================
# (3) SINGLE-ROUTE SWAPS — one route back to the pin's own path, and rederive diverges.
# =================================================================================================


def _expect_inconclusive(rederive):
    assert rederive()["verdict"] == "INCONCLUSIVE"


def _expect_ceiling_floor(rederive):
    # The verdict is still FAILURE ((b) fails either way), so the FLOOR is asserted, never it.
    floor_read = rederive()["gate_inputs"]["target_floor"]
    assert floor_read == pin.FLOOR_CEILING
    assert floor_read != floor.TARGET_FLOOR


def _expect_raise(error):
    def check(rederive):
        with pytest.raises(error):
            rederive()

    return check


@pytest.mark.parametrize(
    ("letter", "expect"),
    [
        ("A", _expect_inconclusive),
        ("B", _expect_ceiling_floor),
        ("C", _expect_raise(SystemExit)),
        ("D", _expect_raise(TypeError)),
    ],
)
def test_swapping_one_route_for_the_pins_own_path_diverges(erased, letter, expect):
    routes = {**phase37_routes.ROUTES, letter: UNROUTED[letter]}
    expect(lambda: phase37_routes.rederive(erased, routes=routes))


# =================================================================================================
# (4) D-13 — the (b) floor re-derived from the replicate arm.
# =================================================================================================


def test_b_floor_from_replicate_is_the_locked_noise_floor():
    assert phase37_routes.b_floor_from_replicate() == floor.NONTARGET_NOISE_FLOOR
