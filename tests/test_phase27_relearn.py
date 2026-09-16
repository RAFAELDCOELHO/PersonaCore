"""Plan 27-03: the structural CPU half of ``scripts/phase27_relearn.py`` — nothing here trains.

Every attack leg refuses a forged MOOT / INCONCLUSIVE / absent record before it resolves a device,
a record whose pinned baselines moved, and an untracked record inside the repo (D-08, D-12).
``admit`` refuses an existing record, refuses a dirty tree before it builds or hashes anything, and
writes the full schema to a tmp path (T-27-07, D-33, D-35). ``main()``'s keyword arguments trace
into every leg's signature (D-10). The driver imports no torch-touching module at top level, never
loads through torch by name, and its git surface is read-only (T-27-06, T-27-08). Plan 27-04
appends the CPU wiring proof.
"""

import ast
import collections
import copy
import hashlib
import inspect
import json
import pathlib
import subprocess
import sys

import numpy as np
import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
for _path in (_ROOT / "scripts", _ROOT / "src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import phase25_run  # noqa: E402  (scripts/ is not a package)
import phase27_prereg  # noqa: E402  (same)
import phase27_relearn as relearn  # noqa: E402  (same)

_DRIVER = _ROOT / "scripts" / "phase27_relearn.py"
_LEG_MODES = ("calibrate", "curve", "gate", "structural-proof")
_REFUSAL_CASES = [
    (mode, reading) for mode in _LEG_MODES for reading in ("MOOT", "INCONCLUSIVE", "absent")
]
_TOP_LEVEL_KEYS = {
    "governs",
    "verdict",
    "admitted_point_keys",
    "tallies",
    "tallies_by_leg",
    "cleared_counts",
    "rows",
    "frontier_path",
    "frontier_sha256",
    "frontier_bytes",
    "x",
    "recall_thresholds",
    "baselines",
    "fresh_seeds",
    "designated_seed",
    "attacker_corpus",
    "budget",
    "apparatus",
    "disjointness",
    "provenance",
}
_TORCH_TOUCHING = (
    "torch",
    "numpy",
    "teach_persona",
    "phase14_factset",
    "phase14_recall",
    "phase18_extraction",
    "phase25_points",
    "personacore.training.loop",
    "personacore.lora",
    "personacore.checkpoint",
    "personacore.config",
    "personacore.model",
    "personacore.tokenizer",
)


def _git(*args):
    return subprocess.run(
        ["git", *args], cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout


@pytest.fixture(scope="module")
def frontier():
    return relearn.frontier()


@pytest.fixture(autouse=True)
def clean_tree(monkeypatch):
    """``admit`` refuses a dirty tree, and this suite runs on dirty trees all day, so the guard is
    RECORDED here and never exercised (the ``tests/test_phase26_canary.py`` idiom). The one test
    that proves the wiring plants a refusing stub of its own."""
    calls = []
    monkeypatch.setattr(relearn, "refuse_if_dirty", lambda **kw: calls.append(kw) or "")
    return calls


def _record(verdict, *, reasons=("forged",), baselines=None):
    return {
        "verdict": {"verdict": verdict, "reasons": list(reasons)},
        "admitted_point_keys": [],
        "baselines": phase27_prereg.PINNED_BASELINES if baselines is None else baselines,
    }


def _forge(directory, verdict, **kw):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "phase27_admission.json"
    path.write_text(json.dumps(_record(verdict, **kw)), encoding="utf-8")
    return path


# ===== the gate on the COMMITTED record (D-08, D-12) =====


@pytest.mark.parametrize(
    ("mode", "verdict"),
    _REFUSAL_CASES,
    ids=[f"{mode}-{verdict}" for mode, verdict in _REFUSAL_CASES],
)
def test_each_leg_refuses_unless_admitted(tmp_path, monkeypatch, mode, verdict):
    """The node ids ``[<mode>-MOOT]`` are the ``refusal_node_id``s the record's apparatus names."""
    monkeypatch.setattr(
        relearn, "shared_train_config", lambda: pytest.fail("leg ran past the gate")
    )
    monkeypatch.setattr(
        phase25_run, "device", lambda: pytest.fail("leg resolved a device past the gate")
    )
    record = (
        tmp_path / "phase27_admission.json" if verdict == "absent" else _forge(tmp_path, verdict)
    )
    out = tmp_path / "out"
    argv = [mode, "--record", str(record), "--leg", "n8", "--out-dir", str(out)]
    if mode == "gate":
        argv += ["--baseline", phase27_prereg.BASELINE_KEYS[0]]

    with pytest.raises(SystemExit) as excinfo:
        relearn.main(argv)

    message = str(excinfo.value)
    assert "REFUSING" in message, message
    assert verdict in message, message
    assert not out.exists() or not any(out.iterdir()), "a refused leg wrote under --out-dir"


def test_a_record_with_moved_pins_is_refused(tmp_path):
    pins = copy.deepcopy(phase27_prereg.PINNED_BASELINES)
    key = next(iter(pins))
    digest = pins[key]["sha256"]
    pins[key]["sha256"] = ("1" if digest[0] == "0" else "0") + digest[1:]

    with pytest.raises(SystemExit) as excinfo:
        relearn._require_admitted(_forge(tmp_path / "moved", "ADMITTED", baselines=pins))
    assert "baselines" in str(excinfo.value) and "REFUSING" in str(excinfo.value)

    # The unaltered pins pass: their JSON round trip is an equality (tuples compare as lists).
    blob = relearn._require_admitted(_forge(tmp_path / "pinned", "ADMITTED"))
    assert blob["baselines"] == json.loads(json.dumps(phase27_prereg.PINNED_BASELINES))


def test_a_leg_refuses_an_untracked_record_inside_the_repo():
    rel = "results/phase27_admission_probe_never_committed.json"
    probe = _ROOT / rel
    assert not probe.exists() and not _git("ls-files", rel).strip()
    try:
        probe.write_text(json.dumps(_record("ADMITTED")), encoding="utf-8")
        with pytest.raises(SystemExit) as excinfo:
            relearn._require_admitted(probe)
    finally:
        probe.unlink(missing_ok=True)
    assert "not tracked" in str(excinfo.value) and "REFUSING" in str(excinfo.value)
    assert not probe.exists()
    assert not _git("ls-files", rel).strip()


def test_an_admitted_tmp_record_passes_the_gate_without_git(tmp_path, monkeypatch):
    runs = []
    monkeypatch.setattr(relearn.subprocess, "run", lambda *a, **kw: runs.append(a))
    blob = relearn._require_admitted(_forge(tmp_path, "ADMITTED"))
    assert blob["verdict"]["verdict"] == "ADMITTED"
    assert runs == [], "the tracked conjunct ran git for a record outside the repo"


# ===== admit: write-once, clean tree, the schema (T-27-07, D-33, D-35) =====


def test_admit_refuses_to_overwrite(tmp_path):
    if relearn.RECORD.exists():
        before = relearn.RECORD.read_bytes()
        with pytest.raises(SystemExit) as excinfo:
            relearn.admit()
        assert "REFUSING to overwrite" in str(excinfo.value) and "--force" in str(excinfo.value)
        assert relearn.RECORD.read_bytes() == before
    else:
        assert not _git("ls-files", "results/phase27_admission.json").strip(), (
            "results/phase27_admission.json is tracked but absent on disk"
        )
        out = tmp_path / "x.json"
        relearn.admit(out)
        before = out.read_bytes()
        with pytest.raises(SystemExit) as excinfo:
            relearn.admit(out)
        assert "REFUSING to overwrite" in str(excinfo.value) and "--force" in str(excinfo.value)
        assert out.read_bytes() == before


def test_admit_refuses_a_dirty_tree_before_hashing(tmp_path, monkeypatch, clean_tree):
    monkeypatch.setattr(
        relearn, "disjointness_report", lambda: pytest.fail("admit hashed before the dirty check")
    )

    def stop(_frontier):
        raise SystemExit("[probe] stopped after the dirty check")

    # With the recorder in place nothing refuses, so the record builder is stopped instead: nothing
    # may land under the real results/, and the recorded call proves the dirty check came first.
    monkeypatch.setattr(relearn, "build_record", stop)
    inside = _ROOT / "results" / "phase27_probe_never_written.json"
    with pytest.raises(SystemExit, match="stopped after the dirty check"):
        relearn.admit(inside)
    assert not inside.exists()
    (call,) = clean_tree
    assert call["who"] == "phase27_relearn"
    assert call["cwd"] == _ROOT
    assert call["pathspec"] == (
        "scripts",
        "src",
        "results",
        ":(exclude)results/phase27_probe_never_written.json",
    )

    def refuse(**kw):
        raise SystemExit("[probe] REFUSING: the working tree is dirty")

    monkeypatch.setattr(relearn, "refuse_if_dirty", refuse)
    monkeypatch.setattr(relearn, "build_record", lambda _f: pytest.fail("built on a dirty tree"))
    out = tmp_path / "y.json"
    with pytest.raises(SystemExit, match="dirty"):
        relearn.admit(out)
    assert not out.exists()


def test_admit_writes_the_full_schema_to_a_tmp_path(tmp_path, frontier):
    out = tmp_path / "rec.json"
    blob = relearn.admit(out)

    assert json.loads(out.read_text(encoding="utf-8")) == blob
    assert set(blob) == _TOP_LEVEL_KEYS
    assert blob["verdict"]["verdict"] == "MOOT"
    rows = blob["rows"]
    assert len(rows) == phase27_prereg.EXPECTED_POINTS
    assert collections.Counter(row["verdict"] for row in rows) == collections.Counter(
        frontier["verdicts"]["tallies"]
    )

    disjointness = blob["disjointness"]
    assert disjointness["overlaps"] == {"teaching": 0, "trained_attack": 0, "attacker_corpus": 0}
    assert disjointness["scored"]["gated_prompts"] == 416
    assert disjointness["scored"]["gated_questions"] == 104
    assert disjointness["checked"] >= 104
    assert disjointness["trained_attack_rows"] > 0
    assert "question strings" in disjointness["unit"]
    assert disjointness["held_out_family"] == phase27_prereg.HELD_OUT_FAMILY

    pins = blob["provenance"]["module_sha256"]
    assert set(pins) == set(relearn.PINNED_MODULES)
    for rel, recorded in pins.items():  # recomputed from bytes here, never via relearn._sha256
        assert recorded == hashlib.sha256((_ROOT / rel).read_bytes()).hexdigest(), rel
    assert isinstance(blob["provenance"]["torch_version"], str)
    assert blob["provenance"]["torch_version"]

    apparatus = blob["apparatus"]
    assert [leg["refusal_node_id"] for leg in apparatus["legs"]] == [
        f"tests/test_phase27_relearn.py::test_each_leg_refuses_unless_admitted[{mode}-MOOT]"
        for mode in _LEG_MODES
    ]
    assert all(leg["train_path"] == relearn.TRAIN_PATH for leg in apparatus["legs"])
    assert "train()" in relearn.TRAIN_PATH and "build_arm_bins" in relearn.TRAIN_PATH
    assert apparatus["status"] == "not exercised"
    assert "phase25_phase27_" in apparatus["draw_cache"]

    # WATCHED RED ON A DEEP COPY (T-27-01, D-33): the rows re-derive through cleared_abc, and one
    # flipped cleared_a is caught by the same comparison.
    def rederived(candidate):
        return [
            row["cleared_a"]
            == phase27_prereg.cleared_abc(frontier["points"][row["point_key"]]["verdict"])[0]
            for row in candidate
        ]

    assert all(rederived(rows))
    flipped = copy.deepcopy(rows)
    target = next(row for row in flipped if not row["refused"])
    target["cleared_a"] = not target["cleared_a"]
    assert not all(rederived(flipped))


# ===== D-10's kwargs trace =====


def _dict_keys(statements):
    return {
        key.value
        for statement in statements
        for node in ast.walk(statement)
        if isinstance(node, ast.Dict)
        for key in node.keys
        if isinstance(key, ast.Constant)
    }


def _kwargs_by_mode(source):
    """``{mode: keyword names main() passes}`` read off ``main``'s ``if args.mode == ...`` chain;
    the final ``else`` covers every mode no branch names."""
    tree = ast.parse(source)
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    named, rest = {}, None
    for node in ast.walk(main):
        test = getattr(node, "test", None)
        if not (
            isinstance(node, ast.If)
            and getattr(getattr(test, "left", None), "attr", None) == "mode"
        ):
            continue
        named[test.comparators[0].value] = _dict_keys(node.body)
        if node.orelse and not isinstance(node.orelse[0], ast.If):
            rest = _dict_keys(node.orelse)
    return {mode: named.get(mode, rest) for mode in relearn.SUB_MODES}, main


def _kwargs_trace_failures(source):
    by_mode, main = _kwargs_by_mode(source)
    failures = []
    for mode, keys in by_mode.items():
        fn = relearn.DISPATCH[mode]
        params = inspect.signature(fn).parameters
        required = {name for name, p in params.items() if p.default is inspect.Parameter.empty}
        if keys is None:
            failures.append(f"{mode}: main() builds no kwargs for {fn.__name__}")
            continue
        if keys - set(params):
            failures.append(
                f"{mode}: main() passes {sorted(keys - set(params))}, which {fn.__name__} "
                "does not accept"
            )
        if required - keys:
            failures.append(
                f"{mode}: main() never passes {fn.__name__}'s required {sorted(required - keys)}"
            )
    # Every leg is reached through DISPATCH with those dicts splatted — never by a direct call
    # whose keywords this trace would not see.
    leg_names = {fn.__name__ for fn in relearn.DISPATCH.values()}
    direct = [
        ast.unparse(node.func)
        for node in ast.walk(main)
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) in leg_names
    ]
    splatted = [
        node
        for node in ast.walk(main)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Subscript)
        and getattr(node.func.value, "id", None) == "DISPATCH"
        and any(keyword.arg is None for keyword in node.keywords)
    ]
    if direct or len(splatted) != 1:
        failures.append(f"main() calls legs directly {direct} or dispatches {len(splatted)} times")
    return failures


def test_main_passes_only_kwargs_the_legs_accept(tmp_path):
    assert set(relearn.DISPATCH) == set(relearn.SUB_MODES)
    source = _DRIVER.read_text(encoding="utf-8")
    assert _kwargs_trace_failures(source) == []

    # WATCHED RED ON A tmp_path COPY: one kwarg misspelled in the gate branch.
    planted = source.replace('"baseline": args.baseline', '"baselne": args.baseline')
    assert planted != source, "no gate kwarg to misspell — the demonstration is vacuous"
    copied = tmp_path / "phase27_relearn_misspelled.py"
    copied.write_text(planted, encoding="utf-8")
    failures = _kwargs_trace_failures(copied.read_text(encoding="utf-8"))
    assert any("baselne" in failure and "does not accept" in failure for failure in failures), (
        failures
    )
    assert any("'baseline'" in failure and "required" in failure for failure in failures), failures
    assert _DRIVER.read_text(encoding="utf-8") == source


def test_every_leg_opens_with_require_admitted():
    tree = ast.parse(_DRIVER.read_text(encoding="utf-8"))
    legs = {
        n.name: n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("run_")
    }
    assert sorted(legs) == sorted(relearn.DISPATCH[mode].__name__ for mode in _LEG_MODES)
    for name, fn in legs.items():
        body = fn.body[1:] if ast.get_docstring(fn) is not None else fn.body
        first = body[0]
        assert isinstance(first, ast.Assign), name
        assert isinstance(first.value, ast.Call), name
        assert getattr(first.value.func, "id", None) == "_require_admitted", name


# ===== import surface, loads, git surface (T-27-06, T-27-08) =====


def test_the_driver_imports_no_torch_touching_module_at_top_level():
    tree = ast.parse(_DRIVER.read_text(encoding="utf-8"))
    top_level = {
        alias.name
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    } | {node.module for node in tree.body if isinstance(node, ast.ImportFrom) and node.module}
    offenders = sorted(
        name
        for name in top_level
        if any(name == bad or name.startswith(f"{bad}.") for bad in _TORCH_TOUCHING)
    )
    assert offenders == []

    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0, {str(_ROOT / 'scripts')!r}); "
            "import phase27_relearn; print('torch' in sys.modules)",
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert probe.stdout.strip() == "False", probe.stdout + probe.stderr


def test_the_driver_never_calls_torch_load_directly():
    tree = ast.parse(_DRIVER.read_text(encoding="utf-8"))

    def is_torch(node):
        if isinstance(node, ast.Name):
            return node.id == "torch"
        return (
            isinstance(node, ast.Attribute)
            and node.attr == "torch"
            and isinstance(node.value, ast.Name)
            and node.value.id == "tp"
        )

    loads = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr == "load" and is_torch(node.value)
    ]
    assert loads == []


def _enclosing_function(tree, node):
    """The innermost ``FunctionDef`` lexically containing ``node``, or ``'<module>'``."""
    best = None
    for candidate in ast.walk(tree):
        if not isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if candidate.lineno <= node.lineno <= candidate.end_lineno:
            if best is None or candidate.lineno > best.lineno:
                best = candidate
    return best.name if best is not None else "<module>"


def _git_argv_subcommands(path):
    """Every ``(subcommand, lineno, enclosing_function)`` of a ``["git", ...]`` literal in ``path``
    (``tests/test_phase25_driver.py``'s walk: a docstring cannot produce a ``List`` node)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.List, ast.Tuple)) or not node.elts:
            continue
        first = node.elts[0]
        if not (isinstance(first, ast.Constant) and first.value == "git"):
            continue
        for element in node.elts[1:]:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                found.append((element.value, element.lineno, _enclosing_function(tree, element)))
                break
    return found


def test_the_drivers_git_surface_is_read_only(tmp_path):
    found = _git_argv_subcommands(_DRIVER)
    assert all(sub in phase25_run.READ_ONLY_GIT_ACTIONS for sub, _lineno, _fn in found), found
    assert [(sub, fn) for sub, _lineno, fn in found] == [("ls-files", "_require_admitted")]

    planted = tmp_path / "phase27_relearn_planted.py"
    planted.write_text(
        _DRIVER.read_text(encoding="utf-8")
        + '\n\ndef _planted():\n    subprocess.run(["git", "add", "x"])\n',
        encoding="utf-8",
    )
    offenders = [
        (sub, fn)
        for sub, _lineno, fn in _git_argv_subcommands(planted)
        if sub not in phase25_run.READ_ONLY_GIT_ACTIONS
    ]
    assert offenders == [("add", "_planted")]


# ===== pins and shapes =====


def test_base_slim_is_phase14s_choke_point():
    import phase14_recall as pr  # torch-touching: imported inside the test only

    assert relearn.BASE_SLIM == pr.CONVBASE_SLIM


def test_the_recorder_tags_by_bin_identity_not_suffix(tmp_path):
    teaching = tmp_path / "phase27_x_train.bin"
    replay = tmp_path / "dialog_train.bin"  # the same `_train.bin` suffix as the teaching bin
    callback, state = relearn.make_recorder(tmp_path / "s.bin", teaching_bin=teaching)
    ix = np.arange(2, dtype=np.int64)
    callback(teaching, ix)
    callback(replay, ix)

    raw = ix.astype("<u8").tobytes()
    assert len(raw) == 16
    stream = (tmp_path / "s.bin").read_bytes()
    assert stream == b"\x00" + raw + b"\x01" + raw
    assert state["draws"] == 2
    assert relearn.stream_digest(state) == hashlib.sha256(stream).hexdigest()
    assert "endswith(" not in inspect.getsource(relearn.make_recorder)


def test_pinned_modules_exist_and_include_the_emitter():
    assert all((_ROOT / rel).is_file() for rel in relearn.PINNED_MODULES)
    emitter = pathlib.Path(relearn.__file__).resolve().relative_to(_ROOT).as_posix()
    assert emitter in relearn.PINNED_MODULES
    assert {
        "scripts/phase27_relearn.py",
        "scripts/phase27_prereg.py",
        "scripts/teach_persona.py",
    } <= set(relearn.PINNED_MODULES)


def test_gate_cli_requires_a_pinned_baseline():
    parser = relearn.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["gate", "--leg", "n8"])
    with pytest.raises(SystemExit):
        parser.parse_args(["gate", "--leg", "n8", "--baseline", "made_up"])
    for key in phase27_prereg.BASELINE_KEYS:
        assert parser.parse_args(["gate", "--leg", "n8", "--baseline", key]).baseline == key
