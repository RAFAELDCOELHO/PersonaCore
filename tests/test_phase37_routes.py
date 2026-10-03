"""Plan 37-02: the Phase 37 routing module (REPRO-02), CPU-only.

What this file proves, on the COMMITTED Phase 19 records and nothing planted:
- each published defect A-D is still live in the pin's own unrouted path (the tripwires), and its
  named route in scripts/phase37_routes.py fixes it;
- rederive() reaches the recorded FAILURE, with the three recorded reasons, only through the routes
  and pin.render_verdict;
- swapping ONE route back for the pin's own unrouted callable makes rederive diverge (A
  INCONCLUSIVE, B the ceiling floor, C SystemExit, D TypeError);
- b_floor_from_replicate() re-derives the locked (b) floor;
- select_target_prefix (defect E, ERASE-08) passes phase19_run.target_ablate's call shape with
  reference_set_for and never touches the calibration twin (recorder, no model);
- scripts/phase19_erasure.py and scripts/erasure_gate.py are byte-unchanged;
- no scripts/phase37_*.py makes a forbidden call, and render_verdict is called only in rederive
  (AST gates, each with a planted snippet that turns it red); no skips; every function tested.

It reads only tracked files and writes nothing under results/.
"""

import ast
import hashlib
import inspect
import json
import pathlib
import re
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

import _verdict  # noqa: E402  (scripts/ is not a package)
import phase14_factset as factset  # noqa: E402  (same)
import phase18_extraction as extraction  # noqa: E402  (same)
import phase19_erasure as pin  # noqa: E402  (same)
import phase19_floor as floor  # noqa: E402  (same)
import phase19_run as p19run  # noqa: E402  (same)
import phase35_prereg  # noqa: E402  (same)
import phase37_routes  # noqa: E402  (same; never aliased — _untested_functions counts by name)

from test_phase19_erasure import _call_sites, _callee_name  # noqa: E402
from test_phase29_prereg import _git, _planted  # noqa: E402
from test_phase36_prereg import _skip_failures, _untested_functions  # noqa: E402


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


# =================================================================================================
# (5) DEFECT E — select_target_prefix (ERASE-08), the one wrapper Phase 41 imports.
# =================================================================================================


@pytest.fixture(scope="module")
def curve():
    return json.loads(p19run.TARGET_CURVE_PATH.read_text(encoding="utf-8"))


def _target():
    return {f.slot: f for f in factset.LOCKED_FACTS}[pin.TARGET_SLOT]


def test_defect_e_twin_is_smaller_and_the_resweep_moves_k(curve):
    twin = pin.reference_set_for_calibration(pin.TARGET_SLOT, _target())
    references = extraction.reference_set_for(pin.TARGET_SLOT)
    assert len(twin) == curve["calibration_twin_reference_set_size"]
    assert len(references) == curve["reference_set_size"]
    assert len(twin) != len(references)
    assert curve["k"] == phase35_prereg.R1A_ASSERTIONS["k"]
    replication = json.loads(p19run.RESWEEP_PATH.read_text(encoding="utf-8"))["replication"]
    assert replication["remeasured_k_under_reference_set_for"] == phase35_prereg.R1A_ASSERTIONS["k"]
    assert replication["remeasured_k_under_calibration_twin"] != phase35_prereg.R1A_ASSERTIONS["k"]
    assert replication["prefix_identical_to_committed"] is True


class _Recorder:
    """Stands in for pin.select_ablation_prefix (no model): records the call, returns a sentinel."""

    def __init__(self):
        self.calls = []
        self.result = object()

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.result


def _refuse(*_args, **_kwargs):
    raise AssertionError("the defect-E wrapper reached the calibration twin")


@pytest.fixture
def recorder(monkeypatch):
    rec = _Recorder()
    monkeypatch.setattr(pin, "select_ablation_prefix", rec)
    monkeypatch.setattr(pin, "reference_set_for_calibration", _refuse)
    monkeypatch.setattr(pin, "_selected_components", _refuse)
    return rec


def test_select_target_prefix_passes_target_ablates_call_shape(recorder, curve):
    probe = object()
    fact = _target()
    out = phase37_routes.select_target_prefix(
        None, None, "cpu", None, fact=fact, dialogue_ppl=probe
    )
    assert out is recorder.result
    [(args, kwargs)] = recorder.calls
    assert args == (None, None, "cpu", None)
    assert kwargs["slot"] == fact.slot
    assert kwargs["value"] == fact.value
    assert kwargs["references"] == extraction.reference_set_for(fact.slot)
    assert len(kwargs["references"]) == curve["reference_set_size"]
    taught = {f.slot: f.value for f in factset.LOCKED_FACTS}
    assert tuple(kwargs["collateral"]) == tuple(extraction.CORE_SLOTS)
    for slot, pair in kwargs["collateral"].items():
        assert pair == (taught[slot], extraction.reference_set_for(slot))
    assert kwargs["dialogue_ppl"] is probe
    assert set(kwargs) == {"slot", "value", "references", "collateral", "dialogue_ppl"}


@pytest.mark.parametrize("slot", [f.slot for f in factset.LOCKED_FACTS])
def test_select_target_prefix_never_touches_the_twin_on_any_slot(recorder, slot):
    fact = {f.slot: f for f in factset.LOCKED_FACTS}[slot]
    phase37_routes.select_target_prefix(None, None, "cpu", None, fact=fact, dialogue_ppl=None)
    assert recorder.calls[-1][1]["references"] == extraction.reference_set_for(slot)


def test_select_target_prefix_signature():
    sig = str(inspect.signature(phase37_routes.select_target_prefix))
    assert sig == "(model, tok, device, artifact, *, fact, dialogue_ppl)"


# =================================================================================================
# (6) THE PIN AND THE GATE ARE BYTE-UNCHANGED (D-08).
# =================================================================================================

_PIN_ANCHOR = "3ba3e2c"  # last commit to touch scripts/phase19_erasure.py
_GATE_ANCHOR = "23a830c"  # last commit to touch scripts/erasure_gate.py


def _git_quiet(*args):
    return subprocess.run(("git", *args), cwd=_ROOT, capture_output=True).returncode


def test_pin_and_gate_are_byte_unchanged():
    probe = json.loads((_ROOT / "results" / "phase36_probe_e1.json").read_text(encoding="utf-8"))
    pinned = probe["provenance"]["module_sha256"]["scripts/phase19_erasure.py"]
    actual = hashlib.sha256((_SCRIPTS / "phase19_erasure.py").read_bytes()).hexdigest()
    assert actual == pinned
    for anchor, rel in (
        (_PIN_ANCHOR, "scripts/phase19_erasure.py"),
        (_GATE_ANCHOR, "scripts/erasure_gate.py"),
    ):
        assert _git_quiet("diff", "--quiet", anchor, "HEAD", "--", rel) == 0, rel
        assert _git("status", "--porcelain", "--", rel) == "", rel
        # Non-vacuity: the anchor commit itself DID change the file.
        assert _git_quiet("diff", "--quiet", f"{anchor}~1", anchor, "--", rel) != 0, rel


# =================================================================================================
# (7) AST GATES over every scripts/phase37_*.py (Pitfall 1). Calls only; docstrings are not calls.
# =================================================================================================

_FORBIDDEN_CALLEES = frozenset(
    {
        "erasure_succeeded",
        "write_text",
        "write_bytes",
        "inject_lora",
        "retention_perplexity",
        "draw_all",
        "build_recall_prompt",
        "reference_set_for_calibration",
        "_selected_components",
    }
)
_PINNED_DRIVERS = frozenset({"phase19_run", "phase19_erasure"})


def _phase37_scripts():
    paths = sorted(_SCRIPTS.glob("phase37_*.py"))
    assert paths, "meta-guard: no scripts/phase37_*.py, every gate below would be vacuous"
    return paths


def _import_aliases(tree):
    """``local name -> module (or module.attr)`` for every import in ``tree``."""
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                aliases[a.asname or a.name.split(".")[0]] = (
                    a.name if a.asname else a.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom) and node.module:
            for a in node.names:
                aliases[a.asname or a.name] = f"{node.module}.{a.name}"
    return aliases


def _call_failures(source):
    tree = ast.parse(source)
    aliases = _import_aliases(tree)
    failures = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _callee_name(node)
        func = node.func
        owner = (
            aliases.get(func.value.id)
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name)
            else None
        )
        target = aliases.get(func.id, "") if isinstance(func, ast.Name) else ""
        if "." in target:  # a from-import: judge the call by the name it was imported as
            owner, name = target.rsplit(".", 1)
        if name in _FORBIDDEN_CALLEES:
            failures.append(f"{name} at line {node.lineno}")
        elif isinstance(func, ast.Name) and func.id == "open" and func.id not in aliases:
            failures.append(f"open at line {node.lineno}")
        elif owner == "os" and name == "replace":
            failures.append(f"os.replace at line {node.lineno}")
        elif owner in _PINNED_DRIVERS and (name == "report" or name.startswith("_cmd_")):
            failures.append(f"{owner}.{name} at line {node.lineno}")
        elif name == "run_erasure_arm" and not any(k.arg == "record_path" for k in node.keywords):
            failures.append(f"run_erasure_arm without record_path at line {node.lineno}")
    return failures


def _verdict_sites(sources):
    """Sorted (file name, enclosing function) of every call whose callee name is render_verdict."""
    return sorted(
        (name, function or "<module scope>")
        for name, source in sources
        for function, _ in _call_sites("render_verdict", source)
    )


def test_no_phase37_script_makes_a_forbidden_call():
    for path in _phase37_scripts():
        assert _call_failures(path.read_text(encoding="utf-8")) == [], path.name


def test_render_verdict_is_called_only_inside_rederive():
    sources = [(p.name, p.read_text(encoding="utf-8")) for p in _phase37_scripts()]
    assert _verdict_sites(sources) == [("phase37_routes.py", "rederive")]


_ROUTES_SOURCE = (_SCRIPTS / "phase37_routes.py").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "snippet",
    [
        "\n\ndef planted(g):\n    return g.erasure_succeeded(**{})\n",
        "\n\ndef planted(p):\n    p.write_text('x')\n",
        "\n\ndef planted(p):\n    p.write_bytes(b'x')\n",
        "\n\ndef planted():\n    return open('x', 'w')\n",
        "\n\nimport os as _o\n\ndef planted():\n    _o.replace('a', 'b')\n",
        "\n\ndef planted():\n    p19run.report()\n",
        "\n\ndef planted():\n    pin._cmd_report(None)\n",
        "\n\nfrom phase19_run import report as _r\n\ndef planted():\n    _r()\n",
        "\n\ndef planted():\n    pin.run_erasure_arm('erased')\n",
        "\n\ndef planted(m):\n    m.inject_lora(None)\n",
        "\n\ndef planted():\n    pin.retention_perplexity(None)\n",
        "\n\ndef planted():\n    pin.draw_all(None)\n",
        "\n\ndef planted():\n    pin.build_recall_prompt(None)\n",
        "\n\ndef planted():\n    pin.reference_set_for_calibration('pet_name', None)\n",
        "\n\ndef planted():\n    pin._selected_components()\n",
        "\n\nfrom erasure_gate import erasure_succeeded as _ok\n\ndef planted():\n    _ok()\n",
    ],
)
def test_each_call_gate_detects_its_planted_snippet(tmp_path, snippet):
    assert _call_failures(_ROUTES_SOURCE) == []
    planted = _planted(tmp_path, _ROUTES_SOURCE, _ROUTES_SOURCE + snippet, "planted.py")
    assert _call_failures(planted)


def test_call_gate_allows_run_erasure_arm_with_record_path_and_str_replace(tmp_path):
    snippet = (
        "\n\ndef fine(p):\n    pin.run_erasure_arm('erased', record_path=p)\n"
        "    return 'a'.replace('a', 'b')\n"
    )
    planted = _planted(tmp_path, _ROUTES_SOURCE, _ROUTES_SOURCE + snippet, "fine.py")
    assert _call_failures(planted) == []


@pytest.mark.parametrize(
    "sources",
    [
        [("phase37_routes.py", _ROUTES_SOURCE + "\n\ndef planted():\n    pin.render_verdict()\n")],
        [
            ("phase37_x.py", "def r():\n    render_verdict()\n"),
            ("phase37_routes.py", _ROUTES_SOURCE),
        ],
        [("phase37_routes.py", _ROUTES_SOURCE + "\npin.render_verdict()\n")],
        [
            (
                "phase37_routes.py",
                _ROUTES_SOURCE.replace("pin.render_verdict(", "pin.other_verdict("),
            )
        ],
    ],
)
def test_verdict_gate_is_red_on_a_second_site_or_on_none(sources):
    assert _verdict_sites(sources) != [("phase37_routes.py", "rederive")]


# =================================================================================================
# (8) THIS FILE HAS NO SKIPS; EVERY phase37_routes FUNCTION HAS A CPU TEST.
# =================================================================================================


def test_no_skips_in_this_file(tmp_path):
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _skip_failures(source) == []
    planted = source + '\n\ndef test_planted():\n    pytest.skip("x")\n'
    assert _skip_failures(_planted(tmp_path, source, planted, "skip.py"))


def test_every_phase37_routes_function_has_a_cpu_test(tmp_path):
    test_source = pathlib.Path(__file__).read_text(encoding="utf-8")
    defs = [n for n in ast.parse(_ROUTES_SOURCE).body if isinstance(n, ast.FunctionDef)]
    assert defs, "meta-guard: phase37_routes defines no function, the census would be vacuous"
    assert _untested_functions("phase37_routes", _ROUTES_SOURCE, test_source) == []
    planted = _planted(
        tmp_path,
        _ROUTES_SOURCE,
        _ROUTES_SOURCE + '\n\ndef planted_untested():\n    """Planted."""\n',
        "untested.py",
    )
    assert _untested_functions("phase37_routes", planted, test_source) == ["planted_untested"]
