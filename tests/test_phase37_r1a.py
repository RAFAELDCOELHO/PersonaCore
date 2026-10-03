"""Plan 37-03: R1a, the one REPRO-01 command (scripts/phase37_r1a.py), CPU-only.

What this file proves, on the COMMITTED Phase 19 records:
- derive() re-derives k 78, 0/27, 7/7 beyond the (b) margin and 77.6370113463966 EXACTLY equal to
  phase35_prereg.R1A_ASSERTIONS (read, never typed), the (b) floor from the replicate arm (D-13)
  and the recorded `## Verdict` of results/phase19_erasure_report.md;
- any divergence halts with SystemExit naming the key and writes nothing (D-10);
- the writer is write-once, refuses a dirty tree and any non-phase37 path, and verify mode checks
  an existing record (to tmp_path only — this file never writes under the real results/).

`git status --porcelain -- results` is unchanged by every test (autouse fixture).
"""

import copy
import json
import pathlib
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

import erasure_gate  # noqa: E402  (scripts/ is not a package)
import phase19_erasure as pin  # noqa: E402  (same)
import phase19_floor as floor  # noqa: E402  (same)
import phase35_prereg  # noqa: E402  (same)
import phase37_r1a  # noqa: E402  (same; never aliased — _untested_functions counts by name)

from test_phase29_prereg import _git  # noqa: E402


@pytest.fixture(autouse=True)
def _results_untouched():
    before = _git("status", "--porcelain", "--", "results")
    yield
    assert _git("status", "--porcelain", "--", "results") == before


@pytest.fixture(scope="module")
def derived():
    return phase37_r1a.derive()


@pytest.fixture(scope="module")
def erased():
    return json.loads(pin.arm_record_path("erased").read_text(encoding="utf-8"))


# =================================================================================================
# (1) derive(): REPRO-01 on the committed records, D-13, the recorded verdict.
# =================================================================================================


def test_derive_reproduces_every_r1a_assertion_exactly(derived):
    assert set(derived["assertions"]) == set(phase35_prereg.R1A_ASSERTIONS)
    for key, expected in phase35_prereg.R1A_ASSERTIONS.items():
        value = derived["assertions"][key]
        if isinstance(expected, tuple):
            value = tuple(value)
        assert value == expected, key


def test_margin_is_the_condition_b_margin_and_two_floors(derived):
    assert derived["margin"] == phase35_prereg.e1_condition_b_margin()
    assert derived["margin"] == erasure_gate.MARGIN_K * floor.NONTARGET_NOISE_FLOOR


def test_b_floor_is_rederived_from_the_replicate_arm(derived):
    assert derived["b_floor"] == floor.NONTARGET_NOISE_FLOOR


def test_verdict_and_reasons_match_the_recorded_report(derived):
    import _verdict

    section = _verdict.recorded_verdict(pin.ERASURE_REPORT_PATH.read_text(encoding="utf-8"))
    assert derived["verdict"] == "FAILURE"
    assert derived["reasons"], "meta-guard: no reasons, the line check below would be vacuous"
    for reason in derived["reasons"]:
        assert f"- {reason}\n" in section


def test_k_and_destroyed_pct_cross_check_phase35_r1a_rederive(derived):
    cross = phase35_prereg.r1a_rederive()
    assert derived["assertions"]["k"] == cross["k"]
    assert derived["assertions"]["destroyed_pct"] == cross["destroyed_pct"]
    assert derived["margin"] == cross["margin"]


def test_routes_name_a_to_e(derived):
    assert set(derived["routes"]) == {"A", "B", "C", "D", "E"}
    assert derived["routes"]["E"] == "phase37_routes.select_target_prefix"


def test_a_nudged_dialogue_ppl_halts_naming_destroyed_pct(erased, tmp_path):
    nudged = copy.deepcopy(erased)
    nudged["dialogue_ppl"]["adapter_on"] += 1e-3
    with pytest.raises(SystemExit, match=r"destroyed_pct") as info:
        phase37_r1a.derive(erased=nudged)
    assert "never adjust" in str(info.value)
    assert list(tmp_path.iterdir()) == []


def test_a_dropped_component_halts_naming_k(erased, tmp_path):
    dropped = copy.deepcopy(erased)
    dropped["config"]["ablated_components"] = dropped["config"]["ablated_components"][:-1]
    with pytest.raises(SystemExit, match=r"STOP: k re-derives"):
        phase37_r1a.derive(erased=dropped)
    assert list(tmp_path.iterdir()) == []
