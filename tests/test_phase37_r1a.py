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

import ast
import copy
import hashlib
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
import phase37_prereg  # noqa: E402  (same)
import phase37_r1a  # noqa: E402  (same; never aliased — _untested_functions counts by name)

from personacore.provenance import git_sha  # noqa: E402
from test_phase29_prereg import _git, _planted  # noqa: E402
from test_phase36_prereg import _skip_failures, _untested_functions  # noqa: E402


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


# =================================================================================================
# (2) write_record / check_record / main — write-once to tmp_path, dirty refusal, verify mode.
# =================================================================================================


@pytest.fixture
def recorder(monkeypatch):
    calls = []
    monkeypatch.setattr(phase37_r1a, "refuse_if_dirty", lambda **kw: calls.append(kw))
    return calls


def _tmp_record(tmp_path):
    return tmp_path / phase37_prereg.R1A_RECORD


def test_main_writes_once_with_hashes_and_provenance(tmp_path, recorder, derived):
    assert phase37_r1a.main([], out_root=tmp_path) == 0
    path = _tmp_record(tmp_path)
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["assertions"] == derived["assertions"]
    assert set(record["input_sha256"]) == set(phase37_r1a.INPUT_RECORDS)
    for rel, digest in record["input_sha256"].items():
        assert digest == hashlib.sha256((_ROOT / rel).read_bytes()).hexdigest(), rel
    prov = record["provenance"]
    assert prov["run"]["device"] == "cpu"
    assert prov["run"]["git_sha"] == prov["head_at_write"] == git_sha()
    assert set(prov["module_sha256"]) == set(phase37_r1a.MODULES)
    assert [(c["pathspec"], c["cwd"]) for c in recorder] == [
        (("scripts", "src", "results"), phase37_r1a._ROOT)
    ]

    # Second run: verify mode, exit 0, bytes unchanged.
    before = path.read_bytes()
    assert phase37_r1a.main([], out_root=tmp_path) == 0
    assert path.read_bytes() == before
    assert len(recorder) == 1


@pytest.mark.parametrize("edit", ["assertion", "input_sha256"])
def test_an_edited_record_fails_verification(tmp_path, recorder, edit):
    phase37_r1a.main([], out_root=tmp_path)
    path = _tmp_record(tmp_path)
    record = json.loads(path.read_text(encoding="utf-8"))
    if edit == "assertion":
        record["assertions"]["k"] += 1
    else:
        record["input_sha256"][phase37_r1a.INPUT_RECORDS[0]] = "0" * 64
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(SystemExit, match=r"^\[phase37_r1a\]"):
        phase37_r1a.main([], out_root=tmp_path)
    with pytest.raises(SystemExit, match=r"^\[phase37_r1a\]"):
        phase37_r1a.check_record(phase37_r1a.derive(), path)


def test_a_dirty_tree_writes_nothing(tmp_path, monkeypatch):
    def dirty(**kw):
        raise SystemExit("dirty")

    monkeypatch.setattr(phase37_r1a, "refuse_if_dirty", dirty)
    with pytest.raises(SystemExit, match="dirty"):
        phase37_r1a.main([], out_root=tmp_path)
    assert not _tmp_record(tmp_path).exists()


def test_a_phase19_path_is_refused_before_any_refusal_check(tmp_path, recorder, derived):
    path = tmp_path / "results" / "phase19_x.json"
    with pytest.raises(SystemExit, match="RECORD_GLOB"):
        phase37_r1a.write_record(derived, path, base=tmp_path, run={})
    assert recorder == []
    assert not path.exists()


def test_an_existing_record_is_never_overwritten(tmp_path, recorder, derived):
    path = _tmp_record(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="write-once"):
        phase37_r1a.write_record(derived, path, base=tmp_path, run={})
    assert path.read_text(encoding="utf-8") == "{}"
    assert recorder == []


def test_main_refuses_any_argument():
    with pytest.raises(SystemExit) as info:
        phase37_r1a.main(["bogus"])
    assert str(info.value) == phase37_r1a.__doc__


def test_the_real_record_verifies_when_committed():
    if _git("ls-files", phase37_prereg.R1A_RECORD):
        assert phase37_r1a.main([]) == 0  # verify mode: the record exists, nothing is written
    else:
        assert not (_ROOT / phase37_prereg.R1A_RECORD).exists()


def test_helpers(tmp_path):
    phase37_r1a._prove(True, "unused")
    with pytest.raises(SystemExit, match=r"^\[phase37_r1a\] boom$"):
        phase37_r1a._prove(False, "boom")
    probe = tmp_path / "x"
    probe.write_bytes(b"abc")
    assert phase37_r1a._sha256(probe) == hashlib.sha256(b"abc").hexdigest()
    assert phase37_r1a._now().endswith("+00:00")


# =================================================================================================
# (3) THIS FILE HAS NO SKIPS; EVERY phase37_r1a FUNCTION HAS A CPU TEST.
# =================================================================================================


def test_no_skips_in_this_file(tmp_path):
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _skip_failures(source) == []
    planted = source + '\n\ndef test_planted():\n    pytest.skip("x")\n'
    assert _skip_failures(_planted(tmp_path, source, planted, "skip.py"))


def test_every_phase37_r1a_function_has_a_cpu_test(tmp_path):
    source = (_SCRIPTS / "phase37_r1a.py").read_text(encoding="utf-8")
    test_source = pathlib.Path(__file__).read_text(encoding="utf-8")
    defs = [n.name for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
    assert {"_prove", "_sha256", "_now", "derive", "write_record", "check_record", "main"} <= set(
        defs
    )
    assert _untested_functions("phase37_r1a", source, test_source) == []
    planted = _planted(
        tmp_path, source, source + '\n\ndef planted_untested():\n    """Planted."""\n', "u.py"
    )
    assert _untested_functions("phase37_r1a", planted, test_source) == ["planted_untested"]
