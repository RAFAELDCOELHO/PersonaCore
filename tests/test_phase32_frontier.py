"""Plan 32-03: the v5.0 frontier assembler (AFRONT-02, AFRONT-03).

CPU-only. Every record here is FORGED from the committed v4.0 frontier (results/phase25_frontier.json,
read as the HEAD blob), re-keyed to the advr keys. Nothing is written under the real results/.
"""

import ast
import copy
import functools
import json
import pathlib
import subprocess
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

import mitigation_gate  # noqa: E402  (scripts/ is not a package)
import phase25_record  # noqa: E402  (same)
import phase25_verdict  # noqa: E402  (same)
import phase29_prereg  # noqa: E402  (same)
import phase32_frontier as fr  # noqa: E402  (same)

from test_phase25_driver import _git_argv_subcommands, _git_surface_failure  # noqa: E402
from test_phase29_prereg import _gate_retype_failures, _planted  # noqa: E402
from test_phase30_points import _wr05_failures  # noqa: E402

MODULE = _SCRIPTS / "phase32_frontier.py"
P = phase29_prereg
KEYS = P.POINT_KEYS()
REFUSAL = "REFUSED by the sanctioned route before the pin was reached"
READ_ONLY_GIT = {"ls-files", "show", "rev-parse", "status", "log", "merge-base"}

# The record-contract fields a forged v5 record copies off its v4.0 twin.
CONTRACT = (
    "taught_recall",
    "heldout_recall",
    "condition_c",
    "per_family_counts",
    "zero_extraction_has_nll",
    "draws_per_question",
    "draws_per_question_source",
    "adapter_sha256",
)


@pytest.fixture(autouse=True)
def clean_tree(monkeypatch):
    """emit refuses a dirty tree and this suite runs on dirty trees, so the guard is RECORDED."""
    calls = []
    monkeypatch.setattr(fr, "refuse_if_dirty", lambda **kw: calls.append(kw) or "")
    return calls


@functools.lru_cache(maxsize=None)
def _v4_bytes():
    return subprocess.run(
        ["git", "show", f"HEAD:{fr.V4_FRONTIER_PATH}"], cwd=_ROOT, capture_output=True, check=True
    ).stdout


@functools.lru_cache(maxsize=None)
def _v4():
    """The committed v4.0 frontier, parsed once. Never mutated by a test (the forge deep-copies)."""
    return json.loads(_v4_bytes())


def _v4_sha():
    import hashlib

    return hashlib.sha256(_v4_bytes()).hexdigest()


def _twin(leg):
    return P._V4_TWIN[f"advr_{leg}"]


def _v4_control_counts(twin):
    return _v4()["verdicts"]["control_readings"][twin]["recall_counts"]


# learnable = the v4 adv_n8 control's counts; unlearnable = the v4 adv_n64 control's.
def _counts(state):
    return _v4_control_counts({"learnable": "adv_n8", "unlearnable": "adv_n64"}[state])


def _set_counts(record, counts):
    for side in ("taught", "heldout"):
        k, n = counts[side]
        record[f"{side}_recall"] = dict(record[f"{side}_recall"], numerator=k, denominator=n)


def _recipe(leg):
    n = int(leg.removeprefix("n"))
    return {
        "replay_windows": P.replay_windows(n),
        "n_facts": n,
        "seed": P.DESIGNATED_SEED,
        "max_steps": P.MAX_STEPS,
    }


def _forged_records(n8="learnable", n64="unlearnable"):
    v4 = _v4()
    out = {}
    for leg, state in (("n8", n8), ("n64", n64)):
        twin = _twin(leg)
        for ratio in P.RATIO_GRID:
            key = P.point_key(f"advr_{leg}", ratio)
            is_control = key == P.control_key(leg)
            if state == "unlearnable" and not is_control:
                taught, heldout = (tuple(_counts(state)[s]) for s in ("taught", "heldout"))
                out[key] = P.refused_record(
                    key, taught=taught, heldout=heldout, recipe=_recipe(leg)
                )
                continue
            source = v4["points"][phase25_record.point_key(twin, ratio)]
            record = {"point_key": key, "arm": f"advr_{leg}", "is_control": is_control}
            record |= {"control_key": P.control_key(leg)}
            record |= {field: copy.deepcopy(source[field]) for field in CONTRACT}
            if is_control:
                _set_counts(record, _counts(state))
            out[key] = record
    return out


@functools.lru_cache(maxsize=None)
def _default_frontier_json():
    return json.dumps(fr.build_frontier(_forged_records(), _v4(), _v4_sha()))


def _default_frontier():
    return json.loads(_default_frontier_json())


def _keys_walk(node):
    if isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from _keys_walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _keys_walk(value)


# =================================================================================================
# Task 1 — build_frontier through the frozen route
# =================================================================================================


def test_build_frontier_n8_learnable_n64_prereg03():
    frontier = _default_frontier()
    assert frontier["point_keys"] == list(KEYS)
    assert list(frontier["points"]) == list(KEYS)
    points = frontier["points"]
    c64 = points[P.control_key("n64")]["verdict"]
    assert c64["verdict"] is None and c64["early_return_reason"] == REFUSAL
    assert all(m in c64["reasons"][0] for m in P.COVERAGE_FLOOR_REFUSAL_MARKERS)
    unlearnable = {s: list(v) for s, v in _counts("unlearnable").items()}
    rest = [k for k in P.leg_keys("n64") if k != P.control_key("n64")]
    assert len(rest) == len(P.RATIO_GRID) - 1
    for key in rest:
        entry = points[key]["verdict"]
        assert entry["verdict"] is None and entry["early_return_reason"]
        assert entry["control_recall_counts"] == unlearnable
        assert points[key]["rule"] == "PREREG-03"
        assert P.point_verdict_string(points[key]) == P.REFUSED
    n8 = _counts("learnable")
    for key in P.leg_keys("n8"):
        entry = points[key]["verdict"]
        assert entry["verdict"] in P.V4_VERDICTS
        assert entry["control_taught_recall"] == n8["taught"][0] / n8["taught"][1]
        assert entry["control_heldout_recall"] == n8["heldout"][0] / n8["heldout"][1]
    assert P.admission(frontier)["verdict"] != "INCONCLUSIVE"
    readings = frontier["verdicts"]["control_readings"]
    assert readings["advr_n64"]["recall_counts"] == unlearnable
    assert (
        readings["advr_n64"]["unlearnable"] is True and readings["advr_n8"]["unlearnable"] is False
    )
    assert set(frontier["verdicts"]["leg_refusals"]) == {"advr_n64"}


def test_build_route_spy_both_legs_learnable(monkeypatch):
    real = phase25_verdict.curve_verdicts
    seen = []

    def spy(records, arm, capacity, *, control_readings_by_arm):
        seen.append((records, arm, capacity, control_readings_by_arm))
        return real(records, arm, capacity, control_readings_by_arm=control_readings_by_arm)

    monkeypatch.setattr(phase25_verdict, "curve_verdicts", spy)
    records = _forged_records(n8="learnable", n64="learnable")
    frontier = fr.build_frontier(records, _v4(), _v4_sha())
    assert [len(call[0]) for call in seen] == [len(P.RATIO_GRID)] * len(P.LEGS)
    for records_seen, arm, capacity, by_twin in seen:
        assert set(by_twin) == set(phase25_verdict.ARM_LEGS[arm])
        assert f"n{capacity}" in P.LEGS
        for leg in P.LEGS:
            control = records[P.control_key(leg)]
            got = by_twin[_twin(leg)]
            assert got["adapter_on"] == control["condition_c"]["point_dialogue_ppl_on"]
            assert got["adapter_off"] == control["condition_c"]["point_dialogue_ppl_off"]
            t, h = control["taught_recall"], control["heldout_recall"]
            assert got["taught_recall"] == t["numerator"] / t["denominator"]
            assert got["heldout_recall"] == h["numerator"] / h["denominator"]
    assert all(frontier["points"][k]["verdict"]["verdict"] in P.V4_VERDICTS for k in KEYS)
    assert frontier["verdicts"]["leg_refusals"] == {}


def test_route_structural_systemexit_propagates(monkeypatch):
    def structural(*args, **kwargs):
        raise SystemExit("structural")

    monkeypatch.setattr(phase25_verdict, "curve_verdicts", structural)
    with pytest.raises(SystemExit, match="^structural$"):
        fr.build_frontier(_forged_records(), _v4(), _v4_sha())


def test_build_refuses_malformed_prereg_record_sets():
    records = _forged_records()
    eleven = dict(records)
    eleven.pop(KEYS[-1])
    with pytest.raises(SystemExit, match="12"):
        fr.build_frontier(eleven, _v4(), _v4_sha())
    # A PREREG-03 record on a learnable leg.
    learnable = dict(records)
    stray = P.leg_keys("n8")[1]
    learnable[stray] = records[P.leg_keys("n64")[1]] | {"point_key": stray}
    with pytest.raises(SystemExit, match="PREREG-03"):
        fr.build_frontier(learnable, _v4(), _v4_sha())
    # A PREREG-03 record whose control counts differ from the control's.
    other = dict(records)
    key = P.leg_keys("n64")[2]
    other[key] = P.refused_record(key, taught=(0, 1008), heldout=(0, 648), recipe=_recipe("n64"))
    with pytest.raises(SystemExit, match="control_recall_counts"):
        fr.build_frontier(other, _v4(), _v4_sha())


def test_route_no_promotion_and_replication_is_false():
    frontier = _default_frontier()
    assert "promotion" not in set(_keys_walk(frontier))
    routed = [frontier["points"][k]["verdict"] for k in KEYS if "rule" not in frontier["points"][k]]
    assert routed, "no routed entry: the check is vacuous"
    for entry in routed:
        assert entry["replicated_at_second_seed"] is False
        assert entry["replicated_at_second_seed"] is fr.phase25_promotion.REPLICATED_AT_SECOND_SEED
    assert frontier["verdicts"]["replicated_at_second_seed"] is False


def test_tallies_rederive_and_a_planted_mismatch_is_read():
    frontier = _default_frontier()
    strings = {k: P.point_verdict_string(frontier["points"][k]) for k in KEYS}
    assert frontier["verdicts"]["tallies"] == P._tally(strings.values())
    by_leg = {}
    for k in KEYS:
        by_leg.setdefault(P._frontier_leg(k), []).append(strings[k])
    assert frontier["verdicts"]["tallies_by_leg"] == {g: P._tally(v) for g, v in by_leg.items()}
    assert P.admission(frontier)["verdict"] != "INCONCLUSIVE"
    frontier["verdicts"]["tallies"][P.REFUSED] += 1
    assert P.admission(frontier)["verdict"] == "INCONCLUSIVE"


def test_ast_route_gates(tmp_path):
    source = MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert _gate_retype_failures(source, mitigation_gate.F_Y) == []
    planted = _planted(tmp_path, source, source + f"\n_X = {mitigation_gate.F_Y!r}\n", "fy.py")
    assert _gate_retype_failures(planted, mitigation_gate.F_Y), "the F_Y guard is blind"
    calls = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "curve_verdicts"
    ]
    assert calls, "the frozen route is never called"
    assert _wr05_failures(source) == []
    carrier = _planted(
        tmp_path, source, source + "\n_X = phase25_promotion.control_readings\n", "wr05.py"
    )
    assert _wr05_failures(carrier), "the WR-05 guard is blind"
    replaces = [
        n.lineno
        for n in ast.walk(tree)
        if isinstance(n, ast.Attribute)
        and n.attr == "replace"
        and isinstance(n.value, ast.Name)
        and n.value.id == "os"
    ]
    assert replaces == []
    offenders, message = _git_surface_failure(MODULE, READ_ONLY_GIT)
    assert offenders == [], message
    used = {row[0] for row in _git_argv_subcommands(MODULE)}
    assert {"ls-files", "show"} <= used  # non-vacuous
    assert not used & {"add", "commit"}  # D-16: the emitter never commits


def test_ast_module_is_torch_free_at_import():
    code = (
        "import sys; sys.path.insert(0, 'scripts'); sys.path.insert(0, 'src'); "
        "import phase32_frontier; assert 'torch' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], cwd=_ROOT, check=True)
