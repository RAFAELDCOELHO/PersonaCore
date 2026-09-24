"""``scripts/phase27_relearn.py`` on CPU: plan 27-03's structural half, plan 27-04's wiring proof.

Plan 27-03 (nothing trains): every attack leg refuses a forged MOOT / INCONCLUSIVE / absent record
before it resolves a device, a record whose pinned baselines moved, and an untracked record inside
the repo (D-08, D-12). ``admit`` refuses an existing record, refuses a dirty tree before it builds
or hashes anything, and writes the full schema to a tmp path (T-27-07, D-33, D-35). ``main()``'s
keyword arguments trace into every leg's signature (D-10). The driver imports no torch-touching
module at top level, never loads through torch by name, and its git surface is read-only (T-27-06,
T-27-08).

Plan 27-04: ONE CPU run of calibrate -> curve -> gate -> structural-proof through ``main()`` on a
tiny fixture, on the real train path and the real, unstubbed scorers, read back off disk (D-09,
D-10, D-21, D-26); the disjointness of the real recovery fixture (D-17); and the node-id,
provenance, pyproject and record guards, both-state on the not-yet-committed record (D-35, D-36,
D-39).
"""

import ast
import collections
import copy
import dataclasses
import hashlib
import inspect
import json
import math
import pathlib
import subprocess
import sys

import numpy as np
import pytest
import torch

_ROOT = pathlib.Path(__file__).resolve().parent.parent
for _path in (_ROOT / "scripts", _ROOT / "src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import phase14_factset as fs  # noqa: E402  (scripts/ is not a package)
import phase14_recall as pr  # noqa: E402  (same)
import phase18_extraction as x18  # noqa: E402  (same)
import phase25_run  # noqa: E402  (same)
import phase27_prereg  # noqa: E402  (same)
import phase27_relearn as relearn  # noqa: E402  (same)
import teach_persona as tp  # noqa: E402  (same)

from personacore import checkpoint as ckpt_mod  # noqa: E402
from personacore.config import ModelConfig  # noqa: E402
from personacore.generation import undecodable_ids_mask  # noqa: E402
from personacore.lora import inject_lora, lora_state_dict  # noqa: E402
from personacore.model import GPT  # noqa: E402
from personacore.tokenizer import from_json  # noqa: E402

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


def test_a_leg_refuses_an_untracked_record_inside_the_repo(tmp_path, monkeypatch):
    """IN-07 / D-16: the untracked probe lives in a scratch repo with ``relearn._ROOT`` pointed at
    it, so the refusal is proven without ever writing into the real ``results/``."""

    def _tracked_digests():
        return {
            rel: hashlib.sha256((_ROOT / rel).read_bytes()).hexdigest()
            for rel in _git("ls-files", "results/phase27_*").split()
        }

    before = _tracked_digests()
    strays_before = _real_tree_strays()

    scratch = tmp_path.resolve() / "repo"
    subprocess.run(["git", "init", "-q", "-b", "main", str(scratch)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "t")):
        subprocess.run(["git", "-C", str(scratch), "config", key, value], check=True)
    (scratch / "results").mkdir()
    monkeypatch.setattr(relearn, "_ROOT", scratch)

    probe = scratch / "results/phase27_admission_probe_never_committed.json"
    probe.write_text(json.dumps(_record("ADMITTED")), encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        relearn._require_admitted(probe)
    assert "not tracked" in str(excinfo.value) and "REFUSING" in str(excinfo.value)

    assert _tracked_digests() == before
    assert _real_tree_strays() == strays_before
    assert _git("status", "--porcelain", "--", "results/phase27_*").strip() == ""
    assert not (_ROOT / "results/phase27_admission_probe_never_committed.json").exists()


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


# ===== plan 27-04: the CPU wiring proof (D-09, D-10, D-21, D-26, D-31, D-32) =====

# D-31: two layers, and `block_size` is the packer's, or the loader would mis-cut the windows.
_E2E_CFG = ModelConfig(block_size=tp.BLOCK_SIZE, n_layer=2, n_head=2, n_embd=16)
# D-22 in the frontier's own point_keys order: TWO admitted points in one leg, so a naming
# collision between two mitigated arms cannot hide behind a one-point fixture.
_ADMITTED = ("dp_n8_sigma0p500000", "dp_n8_sigma0p700000")
# The budget the fixture runs at. K comes from mitigation_gate.K_RUNGS, the closed menu the
# promotion's ratchet accepts (48, 24, 16, 8); a K off that menu refuses before any promotion.
_FRESH_SEEDS = (1337, 2024)
_RUNGS = (1, 2)
_CURVE_K = 8
_FULL_K = 16
# Invented values, 4 ids each under the frozen tokenizer: A2 refuses a value shorter than 4 ids
# (its injection budget would be 0), and 4 new tokens are enough to hold either value.
_VALUES = ("orvel", "tobin")
_RECALL_NEW_TOKENS = 4
_BASELINE = "never_taught_1337"
_ARM_LABELS = (
    *(f"fresh_seed{seed}" for seed in _FRESH_SEEDS),
    f"control_seed{phase27_prereg.DESIGNATED_SEED}",
    *(f"mitigated_{key}_seed{phase27_prereg.DESIGNATED_SEED}" for key in _ADMITTED),
)


def _e2e_env(root, monkeypatch):
    """Point every input and output the four legs touch at ``root``, at fixture scale, on CPU.

    Nothing on the train or score path is stubbed: only paths, budgets, the device cache, the pins,
    the fact set and a forged frontier copy are redirected. ``tests/test_phase22_wiring.py``'s
    ``_e2e_env`` is the source of the tiny base and the decodable-id dialogue bins; its
    ``tp.preflight_device`` / ``tp.RuntimeConfig`` lambdas are not copied, because only
    ``train_arm`` and ``run_calibration`` read them and this driver builds
    ``personacore.config.RuntimeConfig(device=...)`` itself.
    """
    # D-09, FIRST: phase25_run.device() caches _DEVICE and resolves MPS on the dev box, and every
    # leg and phase25_run._draw_one_shape resolve through it. No code path may run before this.
    monkeypatch.setattr(phase25_run, "_DEVICE", "cpu")
    for sub in ("data", "checkpoints", "results"):
        (root / sub).mkdir(parents=True, exist_ok=True)

    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(0)
        base = GPT(_E2E_CFG)
    convbase = root / "convbase.pt"
    torch.save(
        {
            "model_config": dataclasses.asdict(_E2E_CFG),
            "model": base.state_dict(),
            "git_sha": "0" * 40,
            "step": 7,
            "val_loss": 1.234,
        },
        convbase,
    )
    slim_path = root / "convbase_slim.pt"
    slim = ckpt_mod.export_slim(convbase, slim_path)
    # BOTH base readers: model_from_adapter loads relearn.BASE_SLIM; tp.score_arm and
    # phase25_run._draw_one_shape load pr.CONVBASE_SLIM through pr.load_adapted_model (read at call
    # time). Missing the second, the first score loads the real 13.9M base against a tiny adapter.
    monkeypatch.setattr(relearn, "BASE_SLIM", slim_path)
    monkeypatch.setattr(pr, "CONVBASE_SLIM", slim_path)
    # A generation BUDGET, like K: both scorers decode through pr._complete, which reads it at call
    # time. Measured on this fixture at the real 48 tokens: tp.score_arm 28.69 s, the K=8 draws
    # 11.30 s, the K=16 draws 22.40 s, twelve scores per run; at 4 tokens 2.27 / 0.95 / 1.84 s.
    monkeypatch.setattr(pr, "RECALL_MAX_NEW_TOKENS", _RECALL_NEW_TOKENS)

    # DECODABLE ids only (the Phase-22 helper's reason): a dead target id sends perplexity to inf.
    live = torch.nonzero(~undecodable_ids_mask(from_json(tp.TOKENIZER_PATH), 8192)[0]).flatten()
    rng = np.random.default_rng(0)

    def _pair(stem, windows):
        n = windows * tp.BLOCK_SIZE + 1  # + 1: get_batch_memmap_masked needs a shifted target
        ids = rng.choice(live.numpy(), size=n).astype(np.uint16)
        bin_path, mask_path = root / "data" / f"{stem}.bin", root / "data" / f"{stem}_mask.bin"
        ids.tofile(bin_path)
        np.ones(n, dtype=np.uint8).tofile(mask_path)
        return bin_path, mask_path

    # tp._REPO_ROOT is read at call time by arm_outputs: the bins, the run CSV (under RESULTS) and
    # the resume checkpoint all land under root.
    monkeypatch.setattr(tp, "_REPO_ROOT", root)
    for name, stem, windows in (
        ("DIALOG_VAL", "dialog_val", 3),
        ("DIALOG_TRAIN", "dialog_train", 4),
    ):
        bin_path, mask_path = _pair(stem, windows)
        monkeypatch.setattr(tp, f"{name}_BIN", bin_path)
        monkeypatch.setattr(tp, f"{name}_MASK", mask_path)
    # The recipe symbols the driver reads (shared_train_config, train_relearn_arm). LoRA inits B to
    # zeros, so A's step-0 gradient is 0.0: the two rungs make two steps, and A moves on the second.
    for name, value in (("WARMUP_STEPS", 1), ("BATCH_SIZE", 1), ("EVAL_INTERVAL", 1)):
        monkeypatch.setattr(tp, name, value)

    # D-32: two synthetic facts on two real slots, rendered through the real render_family.
    facts = tuple(
        fs.Fact(f"e2e_fact_{index}", real.slot, value, real.tier)
        for index, (real, value) in enumerate(zip(fs.LOCKED_FACTS, _VALUES))
    )
    monkeypatch.setattr(fs, "LOCKED_FACTS", facts)
    monkeypatch.setattr(fs, "SOFT_TIER_FACTS", ())

    # results/phase16_recall_sample.json's schema for the two fake ids: build_corpus reads
    # fixture["questions"][tier] for both CORPUS_TIERS, proves len(rows) == fixture["counts"][tier]
    # and re-derives every row's family by exact render_family match. Two questions per fact per
    # tier keep the corpus at 16 prompts a tier.
    families = {x18.REPORTED_TIER: fs.TAUGHT_FAMILY_IDS, x18.GATED_TIER: fs.HELDOUT_FAMILY_IDS}
    questions = {}
    for tier in x18.CORPUS_TIERS:
        rows = [
            (fact.id, question)
            for fact in facts
            for question in [
                question
                for family_id in sorted(families[tier])
                for question, _answer in fs.render_family(family_id, fact)
                if not pr.contains_value(question, fact.value)
            ][:2]
        ]
        questions[tier] = [
            {"seed_index": index, "fact_id": fact_id, "question": question, "reserved": False}
            for index, (fact_id, question) in enumerate(rows)
        ]
    fixture = root / "phase16_recall_sample.json"
    fixture.write_text(
        json.dumps(
            {
                "questions": questions,
                "counts": {tier: len(rows) for tier, rows in questions.items()},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(x18, "CORPUS_SOURCE_FIXTURE", fixture)
    # draws_path(label) is DRAWS_DIR / f"phase25_{label}_draws.json": under the real tree the
    # caches would land as data/phase25_phase27_*, invisible to a data/phase27_* glob.
    monkeypatch.setattr(phase25_run, "DRAWS_DIR", root / "data")

    # The pre-registration's budget, read at call time by the driver. MAX_STEPS moves with
    # RELEARN_CAP so the prereg's own RELEARN_CAP == 2 * MAX_STEPS still holds under the patch.
    for name, value in (
        ("MAX_STEPS", 1),
        ("CHECKPOINT_INTERVAL", 1),
        ("RELEARN_CAP", 2),
        ("RUNGS", _RUNGS),
        ("CURVE_K", _CURVE_K),
        ("FULL_K", _FULL_K),
        ("FRESH_SEEDS", _FRESH_SEEDS),
    ):
        monkeypatch.setattr(phase27_prereg, name, value)

    # Five tiny adapters, one torch seed each, at the recipe's LoRA config (model_from_adapter
    # refuses any other) and fingerprinted against the slim base export_slim wrote.
    fingerprint = {key: slim[key] for key in ("git_sha", "step", "val_loss")}
    names = [f"never_taught_{seed}" for seed in _FRESH_SEEDS] + ["control_n8", *_ADMITTED]
    adapters = {}
    for torch_seed, name in enumerate(names):
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(torch_seed)
            model = GPT(_E2E_CFG)
            inject_lora(model, tp.LORA_CFG)
        path = root / f"{name}_adapter.pt"
        ckpt_mod.export_adapter(
            path,
            adapter=lora_state_dict(model),
            lora_config=dataclasses.asdict(tp.LORA_CFG),
            base_fingerprint=fingerprint,
        )
        adapters[name] = (str(path), hashlib.sha256(path.read_bytes()).hexdigest())
    pins = {
        **{
            f"never_taught_{seed}": {
                "path": adapters[f"never_taught_{seed}"][0],
                "sha256": adapters[f"never_taught_{seed}"][1],
                "seed": seed,
                "source": "e2e",
            }
            for seed in _FRESH_SEEDS
        },
        "control_n8": {
            "path": adapters["control_n8"][0],
            "sha256": adapters["control_n8"][1],
            "seed": phase27_prereg.DESIGNATED_SEED,
            "source": "e2e",
            "point_key": phase27_prereg.CONTROL_KEYS["n8"],
        },
    }
    monkeypatch.setattr(phase27_prereg, "PINNED_BASELINES", pins)
    monkeypatch.setattr(phase27_prereg, "BASELINE_KEYS", tuple(pins))

    fr = copy.deepcopy(relearn.frontier())
    for key in _ADMITTED:
        fr["points"][key]["adapter_path"], fr["points"][key]["adapter_sha256"] = adapters[key]
    # Recall threshold 0: the tiny model can never reach F_Y x 790/1008, so with the real counts no
    # arm clears and Z is undefined. At 0/1008 every rung clears, and the legs reach z_rule, the
    # promotion and recovery_gate with a real Z.
    fr["verdicts"]["control_readings"]["dp_n8"]["recall_counts"]["taught"] = [0, 1008]
    # X by call becomes wilson_upper_bound(416, 416) + MARGIN_K x 0.0 = 1.0. The real X = 0.006462
    # FAILs every reading with fewer than 416 gated questions, so promote_to_full_fidelity would
    # never fire and the FULL_K re-score would go unexercised. Both controls, because
    # extraction_ceiling_x proves they agree.
    for leg in phase27_prereg.LEGS:
        verdict = fr["points"][phase27_prereg.CONTROL_KEYS[leg]]["verdict"]
        verdict["control_extraction_successes"] = verdict["control_extraction_questions"]
    monkeypatch.setattr(relearn, "frontier", lambda: fr)

    record = root / "phase27_admission.json"
    record.write_text(
        json.dumps(
            {
                "verdict": {"verdict": "ADMITTED", "reasons": ["forged for the wiring proof"]},
                "admitted_point_keys": list(_ADMITTED),
                "baselines": pins,
            }
        ),
        encoding="utf-8",
    )
    return {"root": root, "record": record, "out": root / "out", "frontier": fr}


def _real_tree_strays():
    """Every phase-27 write target in the REAL tree, the admission record itself excepted."""
    patterns = (
        "data/phase27_*",
        "data/phase25_phase27_*",
        "data/persona_relearn_attacker_*",
        "results/phase27_*",
        "checkpoints/phase27_*",
    )
    return sorted(
        str(path.relative_to(_ROOT))
        for pattern in patterns
        for path in _ROOT.glob(pattern)
        if path != relearn.RECORD
    )


@pytest.fixture(scope="module")
def e2e_run(tmp_path_factory):
    """ONE CPU run of calibrate -> curve -> gate -> structural-proof through ``main()``.

    Every patch is undone before this returns, so the tests that read the run (and every later test
    in this module) see the real modules. A spy on ``tp.train`` records, per call, the leg it ran
    under, the arm label read off its teaching bin, the ``TrainConfig`` OBJECT, ``on_draw`` and the
    runtime device. ``TrainConfig`` identity is PER LEG INVOCATION: each leg builds its own
    ``shared_train_config()``, and in real use each leg is its own process, so across legs the
    configs are compared by value and by the off-disk proof.
    """
    root = tmp_path_factory.mktemp("e2e")
    record_before = relearn.RECORD.read_bytes() if relearn.RECORD.exists() else None
    strays_before = _real_tree_strays()
    calls, leg = [], {}
    with pytest.MonkeyPatch.context() as monkeypatch:
        env = _e2e_env(root, monkeypatch)
        real_train = tp.train

        def _spy_train(**kwargs):
            calls.append(
                {
                    "mode": leg["mode"],
                    "label": pathlib.Path(kwargs["train_bin"])
                    .name.removeprefix("persona_relearn_attacker_n8_")
                    .removesuffix("_train.bin"),
                    "train_config": kwargs["train_config"],
                    "on_draw": kwargs.get("on_draw"),
                    "device": kwargs["runtime_config"].device,
                }
            )
            return real_train(**kwargs)

        monkeypatch.setattr(tp, "train", _spy_train)
        shared = ["--record", str(env["record"]), "--leg", "n8", "--out-dir", str(env["out"])]
        leg["mode"] = "calibrate"
        assert relearn.main(["calibrate", *shared]) == 0
        leg["mode"] = "curve"
        assert relearn.main(["curve", *shared]) == 0
        leg["mode"] = "gate"
        assert relearn.main(["gate", *shared, "--baseline", _BASELINE]) == 0
        leg["mode"] = "structural-proof"
        assert relearn.main(["structural-proof", *shared]) == 0
        # Read while the patches are still live: these are the functions the legs called.
        scorers = {
            fn.__name__: (fn.__module__, inspect.getsourcefile(fn))
            for fn in (
                pr.load_adapted_model,
                tp.score_arm,
                phase25_run.draw_point_shapes,
                phase25_run._draw_one_shape,
                phase25_run.score_point,
            )
        }
    return {
        **env,
        "train_calls": calls,
        "scorers": scorers,
        "strays": (strays_before, _real_tree_strays()),
        "record_bytes": (
            record_before,
            relearn.RECORD.read_bytes() if relearn.RECORD.exists() else None,
        ),
    }


def _leg_output(e2e_run, name):
    return json.loads((e2e_run["out"] / f"phase27_n8_{name}.json").read_text(encoding="utf-8"))


def _readings(directory):
    """``{arm label: readings}`` re-read OFF DISK from every ``phase27_n8_*_readings.json``."""
    return {
        path.name.removeprefix("phase27_n8_").removesuffix("_readings.json"): json.loads(
            path.read_text(encoding="utf-8")
        )
        for path in sorted(directory.glob("phase27_n8_*_readings.json"))
    }


def test_the_live_path_is_wired_end_to_end(e2e_run):
    """D-10: ``main()`` -> every leg -> ``tp.train()`` and the real scorers -> a recovery verdict.

    Structure only; the tiny model's numbers are meaningless by design (D-31). The node id of this
    test is the ``e2e_node_id`` the admission record's apparatus block names (D-36).
    """
    out, calls = e2e_run["out"], e2e_run["train_calls"]
    designated = phase27_prereg.DESIGNATED_SEED
    mitigated = [f"mitigated_{key}_seed{designated}" for key in _ADMITTED]

    # (a) the train calls: which arm, in which leg, in which order (D-22: admitted_point_keys).
    expected = [
        *(("calibrate", label) for label in _ARM_LABELS[:3] for _rung in _RUNGS),
        *(("curve", label) for label in mitigated for _rung in _RUNGS),
    ]
    assert [(call["mode"], call["label"]) for call in calls] == expected
    # (2 fresh seeds + 1 control + 2 mitigated points) x 2 rungs. No literal total: the textual
    # wall census in tests/test_phase21_sc5.py counts every equality against ten under tests/.
    assert len(calls) == (len(_FRESH_SEEDS) + 1 + len(_ADMITTED)) * len(_RUNGS)
    assert all(callable(call["on_draw"]) and call["device"] == "cpu" for call in calls)

    configs = collections.defaultdict(list)
    for call in calls:
        configs[call["mode"], call["label"]].append(call["train_config"])
    calibrate = configs["calibrate", f"fresh_seed{designated}"][0]
    assert calibrate.seed == designated
    for label in (f"fresh_seed{designated}", f"control_seed{designated}"):
        assert all(cfg is calibrate for cfg in configs["calibrate", label]), label
    for cfg in configs["calibrate", f"fresh_seed{_FRESH_SEEDS[1]}"]:
        assert cfg is not calibrate
        assert dataclasses.asdict(cfg) == {
            **dataclasses.asdict(calibrate),
            "seed": _FRESH_SEEDS[1],
        }
    curve = configs["curve", mitigated[0]][0]
    assert all(cfg is curve for label in mitigated for cfg in configs["curve", label])
    assert dataclasses.asdict(curve) == dataclasses.asdict(calibrate)  # across legs: by value

    # (b) every arm's sidecars, every leg's output, and the device each recorded (D-09).
    readings = _readings(out)
    assert sorted(readings) == sorted(_ARM_LABELS)
    for label in _ARM_LABELS:
        assert readings[label]["device"] == "cpu", label
        for suffix in (*(f"_rung{rung:04d}_adapter.pt" for rung in _RUNGS), "_offsets.bin"):
            assert (out / f"phase27_n8_{label}{suffix}").is_file(), label + suffix
    calibration, curve_out, gate = (
        _leg_output(e2e_run, n) for n in ("calibration", "curve", "gate")
    )
    assert _leg_output(e2e_run, "structural")["data_order"]["devices"] == dict.fromkeys(
        _ARM_LABELS, "cpu"
    )
    assert calibration["device"] == curve_out["device"] == gate["device"] == "cpu"

    # (c) calibration: under threshold 0 both arms clear at the first rung.
    assert calibration["z"] == 1
    assert calibration["fresh"]["first_clear"] == calibration["control"]["first_clear"] == 1
    assert calibration["threshold"]["value"] == 0.0
    assert (calibration["threshold"]["k"], calibration["threshold"]["n"]) == (0, 1008)
    assert calibration["train_path"] == relearn.TRAIN_PATH

    # (d) the curve: every admitted point, every rung, counts with their denominators.
    assert sorted(curve_out["points"]) == sorted(_ADMITTED)
    assert "not a second gate" in curve_out["finding"]
    band_keys = {"floor", "half_width", "fresh", "lo", "hi", "inside", "margin_k"}
    for key, label in zip(_ADMITTED, mitigated):
        rungs = curve_out["points"][key]["rungs"]
        assert [row["steps"] for row in rungs] == list(_RUNGS)
        for row in rungs:
            assert type(row["steps"]) is int
            assert row["scored_tokens"] == readings[label]["mask_ones"] * row["steps"]
            for name in ("taught_recall", "heldout_recall"):
                assert all(type(row[name][f]) is int for f in ("numerator", "denominator"))
            assert all(type(row["extraction"][f]) is int for f in ("successes", "questions"))
            assert set(row["band"]) == band_keys and row["band"]["margin_k"] == 2
            assert row["draws_cache"].endswith(f"_k{_CURVE_K}_draws.json")
        assert curve_out["points"][key]["reading_at_z"] == rungs[0]

    # (e) the gate: X by call, the promotion measured, the verdict in its domain.
    assert gate["x"] == phase27_prereg.extraction_ceiling_x(e2e_run["frontier"]) >= 1.0
    assert (gate["baseline"], gate["z"], gate["finding_is_not_a_gate"]) == (_BASELINE, 1, True)
    assert sorted(gate["points"]) == sorted(_ADMITTED)
    for key in _ADMITTED:
        point = gate["points"][key]
        assert (point["provisional"]["verdict"], point["provisional"]["k"]) == ("PASS", _CURVE_K)
        assert point["promoted"] is True and point["promotion_reason"].startswith("PROMOTE")
        assert point["recovered"]["k"] == _FULL_K
        assert point["recovered"]["draws_cache"].endswith(f"_k{_FULL_K}_draws.json")
        assert point["verdict"] in phase27_prereg.RECOVERY_VERDICTS
        assert point["reasons"] and "/" in point["reasons"][0]
        assert point["prefix_identical"] is True
        assert "taught_recall_reported" in point

    # (f) every rung adapter loads through the weights_only choke point and hashes to its record.
    for label in _ARM_LABELS:
        for rung in readings[label]["rungs"]:
            path = pathlib.Path(rung["adapter_path"])
            assert ckpt_mod.load_adapter(path)["lora_config"] == dataclasses.asdict(tp.LORA_CFG)
            assert rung["adapter_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()

    # (g) both caches of the promoted reading exist — k is part of load_draws' cache identity —
    # and nothing landed in the real tree.
    for key in _ADMITTED:
        for k in (_CURVE_K, _FULL_K):
            cache = e2e_run["root"] / "data" / f"phase25_phase27_n8_{key}_rung0001_k{k}_draws.json"
            assert cache.is_file(), cache.name
    assert e2e_run["strays"] == ([], [])
    assert e2e_run["record_bytes"][0] == e2e_run["record_bytes"][1]

    # (h) the scorers the legs called were the real ones.
    assert e2e_run["scorers"] == {
        "load_adapted_model": ("phase14_recall", str(_ROOT / "scripts" / "phase14_recall.py")),
        "score_arm": ("teach_persona", str(_ROOT / "scripts" / "teach_persona.py")),
        "draw_point_shapes": ("phase25_run", str(_ROOT / "scripts" / "phase25_run.py")),
        "_draw_one_shape": ("phase25_run", str(_ROOT / "scripts" / "phase25_run.py")),
        "score_point": ("phase25_run", str(_ROOT / "scripts" / "phase25_run.py")),
    }


def _config_diffs(readings, reference):
    """``{label: (fields differing from the reference arm's train_config, fields where the recorded
    train_config differs from the one train() wrote into the checkpoint)}`` — D-26 (i) and (ii)."""
    base = readings[reference]["train_config"]

    def differing(left, right):
        return sorted(f for f in set(left) | set(right) if left.get(f) != right.get(f))

    return {
        label: (
            differing(reading["train_config"], base),
            differing(reading["train_config"], reading["checkpoint_train_config"]),
        )
        for label, reading in readings.items()
    }


def test_off_disk_config_diff_is_empty(e2e_run, tmp_path):
    """D-26 (i)/(ii), RELRN-04: every arm's config READ OFF DISK equals the designated fresh arm's
    on every field (the extra fresh seed differs in ``seed`` alone) and equals the config
    ``train()`` wrote into its own checkpoint. Identity of the objects is the wiring test's (per
    leg); across legs, this value-level proof on the files is what holds."""
    reference = f"fresh_seed{phase27_prereg.DESIGNATED_SEED}"
    extra = f"fresh_seed{_FRESH_SEEDS[1]}"
    expected = {label: ([], []) for label in _ARM_LABELS} | {extra: (["seed"], [])}
    assert _config_diffs(_readings(e2e_run["out"]), reference) == expected

    structural = _leg_output(e2e_run, "structural")
    assert structural["shared_config"] == {
        "reference": reference,
        "differing_fields": {label: fields for label, (fields, _off_disk) in expected.items()},
    }
    assert structural["off_disk"] == dict.fromkeys(_ARM_LABELS, True)

    # WATCHED RED on tmp COPIES: one field of one arm's recorded config moved, same comparison.
    for path in e2e_run["out"].glob("phase27_n8_*_readings.json"):
        (tmp_path / path.name).write_bytes(path.read_bytes())
    edited = tmp_path / f"phase27_n8_{_ARM_LABELS[-1]}_readings.json"
    blob = json.loads(edited.read_text(encoding="utf-8"))
    blob["train_config"]["max_steps"] = 99
    edited.write_text(json.dumps(blob), encoding="utf-8")
    assert _config_diffs(_readings(tmp_path), reference) == expected | {
        _ARM_LABELS[-1]: (["max_steps"], ["max_steps"])
    }


def test_offset_stream_digests_prove_data_order(e2e_run):
    """D-26 (iii), D-30: equal seed and equal bin give equal offset streams across arms; another
    seed gives another stream. Each stream file is re-read and re-hashed, and its tag bytes name
    teaching (0) and replay (1) draws in call order."""
    out = e2e_run["out"]
    readings = _readings(out)
    at_designated = [
        label for label in _ARM_LABELS if readings[label]["seed"] == phase27_prereg.DESIGNATED_SEED
    ]
    assert len(at_designated) == len(_ARM_LABELS) - 1
    # The same two facts render the same attacker bin for every arm and seed.
    assert len({(r["bin_bytes"], r["bin_sha256"]) for r in readings.values()}) == 1
    digests = {label: reading["offset_stream"]["sha256"] for label, reading in readings.items()}
    assert len({digests[label] for label in at_designated}) == 1
    assert digests[f"fresh_seed{_FRESH_SEEDS[1]}"] != digests[at_designated[0]]

    data_order = _leg_output(e2e_run, "structural")["data_order"]
    assert data_order["sha256"] == digests
    assert data_order["equal_across_arms_at_designated_seed"] is True
    assert data_order["equal_bin_bytes_at_designated_seed"] is True
    assert data_order["differs_across_seeds"] is True

    for label, reading in readings.items():
        stream, batch = reading["offset_stream"], reading["train_config"]["batch_size"]
        assert batch == 1, "one uint64 per draw: the tag positions below assume it"
        replay = math.ceil(reading["replay_windows"] / batch)
        assert replay > 0 and stream["draws"] == len(_RUNGS) * (1 + replay), label
        raw = (out / f"phase27_n8_{label}_offsets.bin").read_bytes()
        assert len(raw) == stream["draws"] * (1 + 8 * batch), label
        assert hashlib.sha256(raw).hexdigest() == stream["sha256"], label
        # Tagged by IDENTITY against the teaching bin: it and the replay bin both end in
        # _train.bin, so a suffix rule would have tagged every draw 0.
        assert list(raw[:: 1 + 8 * batch]) == ([0] + [1] * replay) * len(_RUNGS), label
        assert stream["teaching_bin"] == reading["bin_path"]


def test_recovery_fixture_is_disjoint(monkeypatch, tmp_path):
    """D-17, RELRN-05 on the REAL fact set: zero scored question strings in the teaching rows, the
    adversarial arm's trained rows or the attacker corpus; a planted scored row is counted and
    refused at ``admit``. The held-out family is read from the prereg, never spelled here."""
    report = relearn.disjointness_report()
    fixture = json.loads(x18.CORPUS_SOURCE_FIXTURE.read_text(encoding="utf-8"))
    gated = fixture["questions"][phase27_prereg.GATED_TIER]
    assert report["overlaps"] == {"teaching": 0, "trained_attack": 0, "attacker_corpus": 0}
    assert report["scored"]["gated_prompts"] == 416
    assert report["scored"]["gated_questions"] == len({row["question"] for row in gated})
    assert report["scored"]["heldout_recall"] > 0
    assert report["trained_attack_rows"] > 0
    assert "question strings" in report["unit"]
    assert report["held_out_family"] == phase27_prereg.HELD_OUT_FAMILY
    assert phase27_prereg.HELD_OUT_FAMILY not in report["trained_families"]

    # PLANTED RED, a monkeypatch and never the tree: the teaching renderer gains one pair whose
    # question is a scored gated question string (the fixture holds the text; the corpus does not).
    real_render = tp.render_episodes
    planted = (gated[0]["question"], "planted")
    monkeypatch.setattr(tp, "render_episodes", lambda *a, **kw: [*real_render(*a, **kw), planted])
    # The attacker corpus IS the teaching rows (D-18), rendered by the same function: both count it.
    assert relearn.disjointness_report()["overlaps"] == {
        "teaching": 1,
        "trained_attack": 0,
        "attacker_corpus": 1,
    }
    out = tmp_path / "z.json"
    with pytest.raises(SystemExit, match="REFUSING to admit"):
        relearn.admit(out)
    assert not out.exists()


# ===== plan 27-04: the guards the record's apparatus and provenance blocks promise =====


def _missing_node_ids(legs, collected):
    return sorted(
        {leg[key] for leg in legs for key in ("refusal_node_id", "e2e_node_id")} - collected
    )


def test_every_apparatus_node_id_exists():
    """D-36, T-27-04: every node id the apparatus block names is collected by a FRESH interpreter,
    both-state on the record."""
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests/test_phase27_relearn.py"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout[-2000:] + completed.stderr[-2000:]
    collected = set(completed.stdout.splitlines())
    legs = [dict(leg) for leg in relearn.APPARATUS_LEGS]
    assert len(legs) == len(_LEG_MODES)
    assert _missing_node_ids(legs, collected) == []

    if relearn.RECORD.exists():
        record = json.loads(relearn.RECORD.read_text(encoding="utf-8"))
        assert record["apparatus"]["legs"] == legs
        assert _missing_node_ids(record["apparatus"]["legs"], collected) == []
    else:
        assert not _git("ls-files", "results/phase27_admission.json").strip()

    # WATCHED RED on a copy: one test name misspelled is not collected.
    misspelled = copy.deepcopy(legs)
    misspelled[0]["refusal_node_id"] = misspelled[0]["refusal_node_id"].replace(
        "refuses", "refusez"
    )
    assert _missing_node_ids(misspelled, collected) == [misspelled[0]["refusal_node_id"]]


def _drifted(pins, root):
    """``[(module, recorded, live)]`` for EVERY pin whose bytes under ``root`` no longer hash to it,
    recomputed from bytes here and never through the emitter's own ``_sha256``."""
    return [
        (name, recorded, live)
        for name, recorded in pins.items()
        if (live := hashlib.sha256((root / name).read_bytes()).hexdigest()) != recorded
    ]


def test_provenance_digests_match_live_bytes(tmp_path):
    """D-35, T-27-12, both-state (``tests/test_phase24_record.py``'s guard): the record's module
    digests equal the files on disk, and one failure names every drifted module at once."""
    if relearn.RECORD.exists():
        pins = json.loads(relearn.RECORD.read_text(encoding="utf-8"))["provenance"]["module_sha256"]
        assert pins, "provenance.module_sha256 is empty — this assertion would be vacuous"
        assert "scripts/phase27_relearn.py" in pins, "the emitter does not pin its own bytes"
        assert set(pins) == set(relearn.PINNED_MODULES)
        drifted = _drifted(pins, _ROOT)
        assert not drifted, (
            f"{len(drifted)} of {len(pins)} provenance digests no longer match the files on disk:\n"
            + "".join(
                f"    {name}\n      recorded {recorded}\n      live     {live}\n"
                for name, recorded, live in drifted
            )
        )
    else:
        assert not _git("ls-files", "results/phase27_admission.json").strip()

    # BOTH states — WATCHED RED on tmp COPIES of every pinned module, two of them one byte longer.
    pins = {
        rel: hashlib.sha256((_ROOT / rel).read_bytes()).hexdigest()
        for rel in relearn.PINNED_MODULES
    }
    edited = ("scripts/phase27_prereg.py", "scripts/phase27_relearn.py")
    for rel in relearn.PINNED_MODULES:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        extra = b"\n# one byte more\n" if rel in edited else b""
        (tmp_path / rel).write_bytes((_ROOT / rel).read_bytes() + extra)
    assert [name for name, _recorded, _live in _drifted(pins, tmp_path)] == list(edited)
    assert _drifted(pins, _ROOT) == []  # ...and the real tree is untouched


def test_pyproject_is_byte_identical():
    """D-39 (RPT-03's fourth milestone): no dependency was added — ``pyproject.toml`` is the
    committed blob, and its newest commit predates the pre-registration."""
    live = (_ROOT / "pyproject.toml").read_bytes()
    committed = subprocess.run(
        ["git", "show", "HEAD:pyproject.toml"], cwd=_ROOT, capture_output=True, check=True
    ).stdout
    assert hashlib.sha256(live).hexdigest() == hashlib.sha256(committed).hexdigest()
    newest = _git("log", "-1", "--format=%cs", "--", "pyproject.toml").strip()
    assert newest and newest < phase27_prereg.COMMITTED, newest


def _calls(node, name):
    return [
        call
        for call in ast.walk(node)
        if isinstance(call, ast.Call)
        and getattr(call.func, "attr", getattr(call.func, "id", None)) == name
    ]


def test_the_curve_cannot_reach_the_verdict_through_the_driver():
    """RELRN-03, D-19 from the CALLER's side: the driver calls ``recovery_gate`` once, inside
    ``run_gate``, with exactly the five keywords its signature has; ``run_gate`` calls no band or
    first-clear reducer and reads X by call, never from the frontier's summary field."""
    tree = ast.parse(_DRIVER.read_text(encoding="utf-8"))
    run_gate = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run_gate"
    )
    everywhere = _calls(tree, "recovery_gate")
    assert len(everywhere) == 1 and _calls(run_gate, "recovery_gate") == everywhere
    (call,) = everywhere
    keywords = [keyword.arg for keyword in call.keywords]
    assert call.args == [] and None not in keywords  # no positional, no ** splat
    assert set(keywords) == {"recovered_successes", "recovered_questions", "x", "z", "baseline"}
    assert set(keywords) == set(inspect.signature(phase27_prereg.recovery_gate).parameters)
    assert _calls(run_gate, "band") == _calls(run_gate, "first_clear") == []
    assert _calls(run_gate, "extraction_ceiling_x")
    assert not [
        node
        for node in ast.walk(run_gate)
        if isinstance(node, ast.Subscript)
        and isinstance(node.slice, ast.Constant)
        and node.slice.value == "extraction_ceiling"
    ]


def test_the_record_re_derives_from_build_record(frontier):
    """D-33/D-34 tripwire, both-state: the record was GENERATED by ``build_record`` on the committed
    frontier, never authored — a hand-edited field goes RED. Complements plan 27-01's both-ways
    frontier pin rather than repeating it."""
    keys = (
        "verdict",
        "admitted_point_keys",
        "tallies",
        "tallies_by_leg",
        "cleared_counts",
        "rows",
        "frontier_sha256",
        "frontier_bytes",
        "x",
        "recall_thresholds",
        "baselines",
        "fresh_seeds",
        "designated_seed",
        "attacker_corpus",
        "budget",
    )
    fresh = json.loads(json.dumps(relearn.build_record(frontier)))

    def moved(candidate):
        return [key for key in keys if candidate[key] != fresh[key]]

    if relearn.RECORD.exists():
        record = json.loads(relearn.RECORD.read_text(encoding="utf-8"))
        assert moved(record) == []
        assert record["apparatus"]["legs"] == fresh["apparatus"]["legs"]
    else:
        assert not _git("ls-files", "results/phase27_admission.json").strip()

    assert fresh["verdict"]["verdict"] == "MOOT"
    # WATCHED RED on a deep copy: one row's cleared_a flipped, the same comparison names the rows.
    flipped = copy.deepcopy(fresh)
    row = next(row for row in flipped["rows"] if not row["refused"])
    row["cleared_a"] = not row["cleared_a"]
    assert moved(flipped) == ["rows"]
