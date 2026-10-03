"""Plan 37-01: the Phase 37 pre-registration (REPRO-03 SC3/SC4), CPU-only.

What this file proves:
- the four rule functions behave as pre-registered on the committed Phase 19 records: replicated()
  (D-02/D-03), prefix_decision() (D-07), draw_identity() (D-03, description only) and
  nontarget_context() (D-12, context only);

It reads only tracked files and git history and writes nothing under results/.
"""

import copy
import json
import math
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

import phase35_prereg  # noqa: E402  (scripts/ is not a package)
import phase37_prereg  # noqa: E402  (same)

PREREG = "scripts/phase37_prereg.py"


def _record(rel):
    return json.loads((_ROOT / rel).read_text(encoding="utf-8"))


def _committed_assertions():
    return dict(phase35_prereg.R1A_ASSERTIONS)


def _committed_prefix():
    return _record("results/phase19_collateral_curve.json")["ordered_prefix"]


def _committed_draws():
    return _record("results/phase19_arm_erased.json")["draws"]


# =================================================================================================
# (1) replicated() (D-02, D-03).
# =================================================================================================


def test_replicated_on_the_committed_assertions():
    out = phase37_prereg.replicated(_committed_assertions())
    assert out["verdict"] == "REPLICATED"
    assert set(out["per_key"]) == set(phase35_prereg.R1A_ASSERTIONS)
    for key, row in out["per_key"].items():
        assert row["abs_diff"] == 0, key
        assert row["within"] is True, key
    # A JSON round trip turns the tuples into lists; they are accepted.
    assert json.loads(json.dumps(out))["verdict"] == "REPLICATED"
    listed = json.loads(json.dumps(_committed_assertions()))
    assert isinstance(listed["target_correct"], list)
    assert phase37_prereg.replicated(listed)["verdict"] == "REPLICATED"


def test_replicated_destroyed_pct_tolerance_is_inclusive():
    committed = phase35_prereg.R1A_ASSERTIONS["destroyed_pct"]
    edge = committed + phase37_prereg.DESTROYED_PCT_TOLERANCE
    assert phase37_prereg.replicated({**_committed_assertions(), "destroyed_pct": edge})[
        "verdict"
    ] == ("REPLICATED")
    beyond = math.nextafter(edge, math.inf)
    out = phase37_prereg.replicated({**_committed_assertions(), "destroyed_pct": beyond})
    assert out["verdict"] == "NOT_REPLICATED"
    assert out["per_key"]["destroyed_pct"]["within"] is False


@pytest.mark.parametrize(
    "key,value",
    [("k", 79), ("target_correct", (1, 27)), ("target_correct", (0, 26))],
)
def test_replicated_zero_tolerances_and_equal_denominators(key, value):
    out = phase37_prereg.replicated({**_committed_assertions(), key: value})
    assert out["verdict"] == "NOT_REPLICATED"
    assert out["per_key"][key]["within"] is False


def test_replicated_unequal_denominator_with_zero_numerator_diff():
    out = phase37_prereg.replicated({**_committed_assertions(), "target_correct": (0, 26)})
    assert out["per_key"]["target_correct"]["abs_diff"] == 0
    assert out["per_key"]["target_correct"]["within"] is False


def test_replicated_refuses_a_missing_key():
    partial = {k: v for k, v in _committed_assertions().items() if k != "k"}
    with pytest.raises(SystemExit, match=r"^\[phase37_prereg\]"):
        phase37_prereg.replicated(partial)


# =================================================================================================
# (2) prefix_decision() (D-07).
# =================================================================================================


def test_prefix_decision_identical_prefix_runs_the_arm():
    committed = _committed_prefix()
    k = phase35_prereg.R1A_ASSERTIONS["k"]
    out = phase37_prereg.prefix_decision(k, committed, committed)
    assert out["run_arm"] is True
    assert out["k_equal"] is True and out["set_equal"] is True
    assert out["positions_moved"] == 0
    assert out["only_in_remeasured"] == [] and out["only_in_committed"] == []
    json.dumps(out)


def test_prefix_decision_reordered_set_runs_the_arm_and_counts_moves():
    committed = _committed_prefix()
    reordered = list(reversed(committed))
    k = phase35_prereg.R1A_ASSERTIONS["k"]
    out = phase37_prereg.prefix_decision(k, reordered, committed)
    assert out["run_arm"] is True
    expected = sum(a != b for a, b in zip(reordered, committed, strict=True))
    assert expected > 0
    assert out["positions_moved"] == expected


def test_prefix_decision_k_other_than_committed_does_not_run():
    committed = _committed_prefix()
    k = phase35_prereg.R1A_ASSERTIONS["k"] + 1
    out = phase37_prereg.prefix_decision(k, committed, committed)
    assert out["run_arm"] is False
    assert out["k_equal"] is False
    assert out["positions_moved"] is None


def test_prefix_decision_one_address_replaced_does_not_run():
    committed = _committed_prefix()
    replaced = copy.deepcopy(committed)
    replaced[0] = [99, "fc_in", 99]
    k = phase35_prereg.R1A_ASSERTIONS["k"]
    out = phase37_prereg.prefix_decision(k, replaced, committed)
    assert out["run_arm"] is False
    assert out["set_equal"] is False
    assert out["only_in_remeasured"] == [[99, "fc_in", 99]]
    assert out["only_in_committed"] == [list(committed[0])]


def test_prefix_decision_refuses_a_committed_list_of_the_wrong_length():
    committed = _committed_prefix()
    k = phase35_prereg.R1A_ASSERTIONS["k"]
    with pytest.raises(SystemExit, match=r"^\[phase37_prereg\]"):
        phase37_prereg.prefix_decision(k, committed, committed[:-1])


# =================================================================================================
# (3) draw_identity() (D-03: description, never a criterion).
# =================================================================================================


def test_draw_identity_on_the_committed_draws():
    draws = _committed_draws()
    out = phase37_prereg.draw_identity(draws, draws)
    assert out["bit_identical"] is True
    assert out["differing_completions"] == 0 and out["differing_entries"] == 0
    assert out["n_completions"] == sum(len(d["completions"]) for d in draws)
    assert out["n_completions"] == len(draws) * len(draws[0]["completions"])
    assert out["n_entries"] == len(draws)
    assert out["criterion"] is False


def test_draw_identity_counts_one_changed_completion():
    draws = _committed_draws()
    replica = copy.deepcopy(draws)
    replica[5]["completions"][3] = replica[5]["completions"][3] + "!"
    out = phase37_prereg.draw_identity(replica, draws)
    assert out["bit_identical"] is False
    assert out["differing_completions"] == 1
    assert out["differing_entries"] == 1


def test_draw_identity_counts_a_short_replica_without_raising():
    draws = _committed_draws()
    out = phase37_prereg.draw_identity(draws[:-1], draws)
    assert out["bit_identical"] is False
    assert out["differing_entries"] == 1
    assert out["differing_completions"] == len(draws[-1]["completions"])


# =================================================================================================
# (4) nontarget_context() (D-12: context, never a criterion).
# =================================================================================================


def _nontarget_deltas():
    floor = _record("results/phase19_noise_floors.json")["nontarget_noise_floor"]
    return floor, dict(zip(floor["slot_order"], floor["deltas_in_slot_order"], strict=True))


def test_nontarget_context_per_slot():
    floor, committed = _nontarget_deltas()
    replica = {slot: delta + 0.25 for slot, delta in committed.items()}
    out = phase37_prereg.nontarget_context(replica, committed)
    assert out["criterion"] is False
    assert out["noise_floor"] == floor["value"]
    assert set(out["slots"]) == set(committed)
    for slot, row in out["slots"].items():
        assert row["replica_delta"] == replica[slot]
        assert row["committed_delta"] == committed[slot]
        assert row["abs_diff"] == abs(replica[slot] - committed[slot])
        assert row["noise_floor"] == floor["value"]
    json.dumps(out)


def test_nontarget_context_refuses_mismatched_slots():
    _, committed = _nontarget_deltas()
    replica = dict(committed)
    replica.pop(next(iter(replica)))
    with pytest.raises(SystemExit, match=r"^\[phase37_prereg\]"):
        phase37_prereg.nontarget_context(replica, committed)
