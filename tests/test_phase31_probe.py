"""Plan 31-01: the point half of the Phase 31 MPS cost probe (ARCAL-01, D-01..D-03, D-11).

CPU-only. Nothing here writes under the real results/, data/ or checkpoints/: every sidecar,
adapter, checkpoint, draw cache and emitted record lands under a tmp directory.
"""

import hashlib
import json
import math
import pathlib
import statistics
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

import phase25_points  # noqa: E402  (scripts/ is not a package)
import phase25_run  # noqa: E402  (same)
import phase29_prereg  # noqa: E402  (same)
import phase30_points as pts  # noqa: E402  (same)
import phase31_probe as probe  # noqa: E402  (same)


def _tp():
    import teach_persona  # torch at import — inside tests only

    return teach_persona


@pytest.fixture(autouse=True)
def clean_tree(monkeypatch):
    """The run and emit refuse a dirty tree, and this suite runs on dirty trees, so the guard is
    RECORDED (the tests/test_phase30_calibration.py idiom)."""
    calls = []
    monkeypatch.setattr(probe, "refuse_if_dirty", lambda **kw: calls.append(kw) or "")
    return calls


# =================================================================================================
# Task 1 — identity, isolation, replay bucketing, the Phase 25 table and the pure record builder
# =================================================================================================


def test_isolation_probe_key_is_not_a_point_key():
    assert probe.PROBE_KEY not in phase29_prereg.POINT_KEYS()
    for label in (probe.PROBE_PREFIX, probe.RELEARN_LABEL):
        assert not label.startswith("phase3"), label
        assert not label.startswith(phase25_points.CALIBRATION_PREFIX_LITERAL), label


def _derived_paths(key, arm, prefix, outputs):
    return {
        phase25_points.training_sidecar(key),
        phase25_points.measure_sidecar(key),
        phase25_points.run_log_dir(key),
        phase25_run.draws_path(key),
        *outputs,
    }


def test_isolation_paths_are_disjoint_from_every_phase32_key():
    tp = _tp()
    arm = pts.point_plan(phase29_prereg.control_key("n64"))["arm"]
    bare = tp.arm_outputs(arm)
    # The unprefixed outputs are exactly the ones a prefix does not move — computed, never listed,
    # so a new prefixed output cannot be excluded silently.
    unprefixed = {
        name
        for name, path in tp.arm_outputs(arm, prefix=probe.PROBE_PREFIX).items()
        if path == bare[name]
    }
    assert unprefixed == {"bin", "mask"}

    def prefixed(arm_, prefix):
        return [p for n, p in tp.arm_outputs(arm_, prefix=prefix).items() if n not in unprefixed]

    ours = _derived_paths(
        probe.PROBE_KEY, arm, probe.PROBE_PREFIX, prefixed(arm, probe.PROBE_PREFIX)
    ) | {probe.point_replay_sidecar(), probe.point_run_sidecar()}
    theirs = set()
    for key in phase29_prereg.POINT_KEYS():
        plan = pts.point_plan(key)
        theirs |= _derived_paths(
            key, plan["arm"], plan["prefix"], prefixed(plan["arm"], plan["prefix"])
        )
    assert len(theirs) > len(phase29_prereg.POINT_KEYS())
    assert ours.isdisjoint(theirs), sorted(map(str, ours & theirs))
    # NON-VACUITY: the real n64 control's own derivation collides with itself.
    ckey = phase29_prereg.control_key("n64")
    cplan = pts.point_plan(ckey)
    assert not _derived_paths(
        ckey, arm, cplan["prefix"], prefixed(arm, cplan["prefix"])
    ).isdisjoint(theirs)


def test_isolation_plan_rekeys_only_key_and_prefix():
    tracked = probe._tracked()
    real = pts.next_action(phase29_prereg.control_key("n64"), tracked)["plan"]
    plan = probe.probe_plan(tracked)
    assert plan["point_key"] == probe.PROBE_KEY
    assert plan["prefix"] == probe.PROBE_PREFIX
    assert {k: v for k, v in plan.items() if k not in ("point_key", "prefix")} == {
        k: v for k, v in real.items() if k not in ("point_key", "prefix")
    }
    assert set(plan) == set(real)
    assert plan["is_control"] is True and plan["arm"] == "advr_n64"


def test_replay_count_bucketing():
    events = [(False, 8), (True, 200), (True, 56), (False, 8), (True, 256)]
    assert probe.per_step_replay(events) == [256, 256]
    assert probe.prove_replay_counts(events, 256, batch_size=8, steps=2) == [256, 256]
    # NON-VACUITY: the right run total on the wrong steps.
    lopsided = [(False, 8), (True, 512), (False, 8)]
    with pytest.raises(SystemExit, match="per step"):
        probe.prove_replay_counts(lopsided, 256, batch_size=8, steps=2)
    with pytest.raises(SystemExit, match="before any teaching draw"):
        probe.per_step_replay([(True, 256), (False, 8)])
    with pytest.raises(SystemExit, match="teaching"):
        probe.prove_replay_counts([(False, 4), (True, 256)] * 2, 256, batch_size=8, steps=2)


def test_phase25_stage_table_reads_committed_records():
    table = probe.phase25_stage_table(probe._tracked())
    points = table["points"]
    assert list(points) == list(phase29_prereg.POINT_KEYS())
    for row in points.values():
        assert {"v4_key", "source", "train", "measure", "draw", "recall"} <= set(row)
    row = points[phase29_prereg.control_key("n64")]
    assert row["v4_key"] == "adv_n64_ratio0p000000"
    twin = json.loads((_ROOT / row["source"]).read_text(encoding="utf-8"))
    assert row["train"] == twin["training"]["seconds"]
    assert row["measure"] == twin["measure_seconds"]
    assert row["draw"] == 60 * sum(s["minutes"] for s in twin["shape_timing"].values())
    recall = json.loads((_ROOT / table["recall_source"]).read_text(encoding="utf-8"))
    assert row["recall"] == recall["points"][row["v4_key"]]["scoring_seconds"]


def _synthetic_run(**overrides):
    run = {
        "probe_key": probe.PROBE_KEY,
        "probe_prefix": probe.PROBE_PREFIX,
        "control_key": phase29_prereg.control_key("n64"),
        "arm": "advr_n64",
        "recipe": {"replay_windows": 256, "max_steps": 200},
        "k": 16,
        "run_git_sha": "0" * 40,
        "device": "cpu",
        "torch_version": "0.0",
        "started_utc": "2026-01-01T00:00:00+00:00",
        "finished_utc": "2026-01-01T01:00:00+00:00",
        "reused": {"train": False, "measure": False, "draw": False},
        "training": {
            "seconds": 80.0,
            "resumed_from_step": 0,
            "adapter": "checkpoints/probe31_advr_n64_adapter.pt",
            "adapter_sha256": "a" * 64,
        },
        "outer_seconds": {"train": 81.0, "measure": 1100.0, "draw": 3700.0, "score": 5.0},
        "measured": {
            "point_key": probe.PROBE_KEY,
            "adapter_sha256": "a" * 64,
            "capability": {"retention_ppl": 1.0},
            "measure_seconds": 90.0,
            "scoring_seconds": 900.0,
            "recall": {"taught": {"numerator": 1, "denominator": 2}},
            "device": "cpu",
        },
        "shape_minutes": {"A1-aggressive": 20.0, "A1-mild": 15.0, "A2": 12.0, "A3": 13.0},
        "score_seconds": 4.5,
        "replay": {
            "per_step": [256, 256],
            "expected_per_step": 256,
            "steps": 2,
            "teaching_windows_per_step": 8,
        },
    }
    run.update(overrides)
    return run


def _synthetic_table():
    keys = phase29_prereg.POINT_KEYS()
    return {
        "points": {
            k: {
                "v4_key": "v4_" + k,
                "source": "s",
                "train": 60.0 + i,
                "measure": 60.0,
                "draw": 60.0 * (10 + i),
                "recall": 600.0,
            }
            for i, k in enumerate(keys)
        },
        "recall_source": "results/phase25_recall.json",
    }


def test_build_point_record_shape():
    run, table = _synthetic_run(), _synthetic_table()
    record = probe.build_point_record(run, table)
    assert record["sweep_point"] is False
    assert record["sweep_point_false_reason"]
    assert record["probe_key"] == probe.PROBE_KEY and record["leg"] == "n64"
    stages = record["stages"]
    assert set(stages) == {"train", "measure", "recall", "draw", "score"}
    for stage in stages.values():
        assert isinstance(stage["seconds"], float) and isinstance(stage["reused"], bool)
    assert stages["train"]["seconds"] == 80.0
    assert stages["measure"]["seconds"] == 90.0
    assert stages["recall"]["seconds"] == 900.0
    assert stages["draw"]["seconds"] == 3600.0
    assert stages["draw"]["outer_seconds"] == 3700.0
    assert stages["score"]["seconds"] == 4.5
    assert record["total_seconds"] == sum(s["seconds"] for s in stages.values())
    assert record["replay"]["per_step"] == [256, 256]
    assert record["replay"]["all_steps_equal"] is True
    assert record["readings"]["gates_nothing"] is True
    assert "measure_seconds" not in record["readings"]
    assert "scoring_seconds" not in record["readings"]
    assert record["phase25_twin"] == table["points"][phase29_prereg.control_key("n64")]
    rows = table["points"].values()
    minutes = [(r["train"] + r["measure"] + r["draw"]) / 60 for r in rows]
    block = record["phase25_per_point_minutes"]
    assert block["n"] == len(phase29_prereg.POINT_KEYS())
    assert (block["min"], block["median"], block["max"]) == (
        min(minutes),
        statistics.median(minutes),
        max(minutes),
    )
    assert block["with_recall"]["median"] == statistics.median(
        [m + r["recall"] / 60 for m, r in zip(minutes, rows)]
    )
    # A reused draw stage keeps its inner seconds and loses its outer bracket.
    reused = probe.build_point_record(
        _synthetic_run(reused={"train": False, "measure": False, "draw": True}), table
    )
    assert reused["stages"]["draw"]["reused"] is True
    assert reused["stages"]["draw"]["outer_seconds"] is None
    assert reused["stages"]["draw"]["seconds"] == 3600.0
    # A fresh draw bracket shorter than the shapes it contains is impossible.
    with pytest.raises(SystemExit, match="outer"):
        probe.build_point_record(
            _synthetic_run(
                outer_seconds={"train": 81.0, "measure": 1100.0, "draw": 10.0, "score": 5.0}
            ),
            table,
        )


def test_module_imports_without_torch():
    code = (
        "import sys, json; sys.path[:0] = ['scripts', 'src']; import phase31_probe as p; "
        f"run = json.loads({json.dumps(_synthetic_run())!r}); "
        "p.build_point_record(run, p.phase25_stage_table(p._tracked())); "
        "print('torch' in sys.modules)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code], cwd=_ROOT, capture_output=True, text=True
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "False", completed.stdout


# =================================================================================================
# Task 2 — the live run at CPU fixture scale, its refusals, and the write-once emit
# =================================================================================================

_PROBE31_GLOBS = (
    "data/*probe31*",
    "data/probe31_relearn/*",
    "checkpoints/*probe31*",
    "results/*probe31*",
    "results/phase31_probe_*",
)


def _real_probe31_strays():
    """Every probe31 write target in the REAL tree (the test module's _ROOT, never patched)."""
    return sorted(
        {
            path.relative_to(_ROOT).as_posix()
            for pattern in _PROBE31_GLOBS
            for path in _ROOT.glob(pattern)
        }
    )


def _one_prompt_per_cell(corpus):
    seen, prompts = set(), []
    for entry in corpus["prompts"]:
        if (entry["family"], entry["tier"]) not in seen:
            seen.add((entry["family"], entry["tier"]))
            prompts.append(entry)
    return dict(corpus, prompts=prompts)


def _point_probe_fixture(root):
    """ONE CPU run of run_point_probe through the REAL stages. Every patch is undone on return."""
    import phase14_recall
    import phase18_extraction as x18
    import phase19_erasure

    from personacore.checkpoint import export_slim
    from test_phase22_wiring import _e2e_env

    tp = _tp()
    strays_before = _real_probe31_strays()
    # Fact (a): on the REAL modules, before any patch (MAX_STEPS == STEP_BUDGET, real _REPO_ROOT).
    tracked = probe._tracked()
    real_plan = probe.probe_plan(tracked)
    calls = {"train_stage": 0, "measure_stage": 0, "draw_point_shapes": 0, "score_point": 0}
    outputs, seen = {}, {}
    heartbeat = root / "heartbeat.jsonl"
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(phase25_run, "_DEVICE", "cpu")
        _e2e_env(root, monkeypatch)
        slim = root / "convbase_slim.pt"
        export_slim(root / "convbase.pt", slim)
        monkeypatch.setattr(phase14_recall, "CONVBASE_SLIM", slim)
        monkeypatch.setattr(phase14_recall, "RECALL_MAX_NEW_TOKENS", 4)
        monkeypatch.setattr(phase25_run, "DRAWS_DIR", root / "data")
        # Fact (c): the gitignored retention bin is absent on CI; the fixture's decodable bin.
        monkeypatch.setattr(phase19_erasure, "RETENTION_BIN", tp.DIALOG_VAL_BIN)
        monkeypatch.setattr(probe, "_ROOT", root)
        monkeypatch.setattr(phase25_points, "_ROOT", root)
        subset = _one_prompt_per_cell(json.loads(x18.CORPUS_PATH.read_text(encoding="utf-8")))
        monkeypatch.setattr(
            phase25_points, "attack_corpus", lambda: (subset, x18.corpus_sha256(subset))
        )
        monkeypatch.setattr(probe, "refuse_if_dirty", lambda **kw: "")

        def _fixture_plan(tracked_):
            assert isinstance(tracked_, list)
            # Fact (b): the ONLY plan field the fixture changes.
            pinned = dict(real_plan["pinned_mechanism"], composed_steps=tp.MAX_STEPS)
            return dict(real_plan, pinned_mechanism=pinned)

        monkeypatch.setattr(probe, "probe_plan", _fixture_plan)

        def _spy(module, name):
            real = getattr(module, name)

            def spy(*args, **kwargs):
                calls[name] += 1
                if name == "train_stage":
                    seen["trained_plan"] = args[0]
                outputs[name] = real(*args, **kwargs)
                return outputs[name]

            monkeypatch.setattr(module, name, spy)

        _spy(phase25_points, "train_stage")
        _spy(phase25_points, "measure_stage")
        _spy(phase25_run, "draw_point_shapes")
        _spy(phase25_run, "score_point")
        fixture_steps = tp.MAX_STEPS
        probe.run_point_probe(heartbeat_path=heartbeat)
        run = json.loads(probe.point_run_sidecar().read_text(encoding="utf-8"))
    record = probe.build_point_record(run, probe.phase25_stage_table(tracked))
    evidence = {
        "calls": calls,
        "outputs": outputs,
        "real_plan": real_plan,
        "trained_plan": seen["trained_plan"],
        "fixture_max_steps": fixture_steps,
        "heartbeat_path": heartbeat,
        "root": root,
        "strays": (strays_before, _real_probe31_strays()),
    }
    return run, record, evidence


@pytest.fixture(scope="module")
def point_probe_run(tmp_path_factory):
    """ONE CPU live-path run per module (the tests/test_phase27_relearn.py::e2e_run pattern)."""
    return _point_probe_fixture(tmp_path_factory.mktemp("point_probe"))


def test_live_path_point_probe_runs_end_to_end_on_cpu(point_probe_run):
    run, record, evidence = point_probe_run
    root, outputs = evidence["root"], evidence["outputs"]
    assert evidence["calls"] == {
        "train_stage": 1,
        "measure_stage": 1,
        "draw_point_shapes": 1,
        "score_point": 1,
    }
    # The spies forwarded to the REAL stages: their outputs are real artifacts.
    training = outputs["train_stage"]
    adapter = root / training["adapter"]
    assert hashlib.sha256(adapter.read_bytes()).hexdigest() == training["adapter_sha256"]
    retention = outputs["measure_stage"]["capability"]["retention_ppl"]
    assert isinstance(retention, float) and math.isfinite(retention)
    blob, _digests = outputs["draw_point_shapes"]
    assert set(blob["shapes"]) == set(phase25_run.ATTACK_FAMILIES)
    assert all(blob["shapes"][f]["timing"]["minutes"] > 0 for f in phase25_run.ATTACK_FAMILIES)
    # D-11: the per-step replay count through the real train_stage.
    expected = pts.calibration_record(probe._tracked())["recipe"]["n64"]["replay_windows"]
    steps = evidence["fixture_max_steps"]
    assert run["replay"]["per_step"] == [expected] * steps
    assert record["replay"]["per_step"] == [expected] * steps
    assert run["reused"] == {"train": False, "measure": False, "draw": False}
    assert all(stage["reused"] is False for stage in record["stages"].values())
    assert record["stages"]["draw"]["outer_seconds"] >= record["stages"]["draw"]["seconds"]
    # The plan train_stage received differs from the real probe plan ONLY on composed_steps.
    trained, real = evidence["trained_plan"], evidence["real_plan"]
    assert {k: v for k, v in trained.items() if k != "pinned_mechanism"} == {
        k: v for k, v in real.items() if k != "pinned_mechanism"
    }
    assert trained["pinned_mechanism"] == dict(real["pinned_mechanism"], composed_steps=steps)
    last = evidence["heartbeat_path"].read_text(encoding="utf-8").splitlines()[-1]
    assert json.loads(last)["stage"] == "done"
    assert not any((root / "results").iterdir())
    before, after = evidence["strays"]
    assert before == after


def _light_env(tmp_path, monkeypatch):
    """Plan FIRST on the unpatched modules, then every path redirected to tmp_path."""
    real_plan = probe.probe_plan(probe._tracked())
    tp = _tp()
    monkeypatch.setattr(phase25_run, "_DEVICE", "cpu")
    monkeypatch.setattr(probe, "_ROOT", tmp_path)
    monkeypatch.setattr(phase25_points, "_ROOT", tmp_path)
    monkeypatch.setattr(tp, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(phase25_run, "DRAWS_DIR", tmp_path / "data")
    monkeypatch.setattr(probe, "probe_plan", lambda tracked: real_plan)
    monkeypatch.setattr(
        phase25_points, "train_stage", lambda plan: pytest.fail("trained past a refusal")
    )
    return tp, real_plan


def test_live_path_refuses_a_half_trained_probe(tmp_path, monkeypatch):
    tp, plan = _light_env(tmp_path, monkeypatch)
    checkpoint = tp.arm_outputs(plan["arm"], prefix=probe.PROBE_PREFIX)["checkpoint"]
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.write_bytes(b"half")
    with pytest.raises(SystemExit, match=r"probe31_advr_n64_latest\.pt.*Delete"):
        probe.run_point_probe(heartbeat_path=tmp_path / "hb.jsonl")


def test_live_path_refuses_training_reuse_without_replay_counts(tmp_path, monkeypatch):
    _light_env(tmp_path, monkeypatch)
    sidecar = phase25_points.training_sidecar(probe.PROBE_KEY)
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match=r"probe31_point_replay\.json"):
        probe.run_point_probe(heartbeat_path=tmp_path / "hb.jsonl")


def test_emit_point_is_write_once(tmp_path):
    out = tmp_path / "p.json"
    out.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="REFUSING to overwrite"):
        probe.emit_point(out)
    assert out.read_text(encoding="utf-8") == "{}"
    record = probe._GIT_ROOT / probe.POINT_RECORD
    if probe.POINT_RECORD in probe._tracked():
        before = record.read_bytes()
        with pytest.raises(SystemExit, match="REFUSING to overwrite"):
            probe.emit_point()
        assert record.read_bytes() == before
    else:
        assert not record.exists(), f"{probe.POINT_RECORD} exists but is untracked"


def test_emit_point_refuses_a_dirty_tree_before_reading_sidecars(tmp_path, monkeypatch):
    calls = []

    def _dirty(**kwargs):
        calls.append(kwargs)
        raise SystemExit("[probe] stopped at the dirty check")

    monkeypatch.setattr(probe, "refuse_if_dirty", _dirty)
    monkeypatch.setattr(probe, "_ROOT", tmp_path)  # EMPTY: the sidecar is genuinely missing
    rel = "results/phase31_never_written_point.json"
    out = probe._GIT_ROOT / rel
    with pytest.raises(SystemExit, match="stopped at the dirty check"):
        probe.emit_point(out)
    assert not out.exists()
    (call,) = calls
    assert call["cwd"] == probe._GIT_ROOT
    assert call["pathspec"] == ("scripts", "src", "results", f":(exclude){rel}")
    # And with the dirty check passing, the missing sidecar is what refuses next.
    monkeypatch.setattr(probe, "refuse_if_dirty", lambda **kw: "")
    with pytest.raises(SystemExit, match=r"probe31_point_run\.json"):
        probe.emit_point(out)
    assert not out.exists()


def test_emit_point_proves_calibration_descent(point_probe_run, tmp_path, monkeypatch):
    _run, _record, evidence = point_probe_run
    monkeypatch.setattr(probe, "_ROOT", evidence["root"])
    out = tmp_path / "point.json"
    record = probe.emit_point(out)
    assert json.loads(out.read_text(encoding="utf-8")) == json.loads(json.dumps(record))
    adds = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%H", "--", pts.CALIBRATION_PATH],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert record["calibration"] == {
        "path": pts.CALIBRATION_PATH,
        "add_commit": adds[-1],
        "is_ancestor_of_head": True,
    }
    assert record["sweep_point"] is False
    module_sha = record["provenance"]["module_sha256"]
    assert set(module_sha) == set(probe.PINNED_MODULES)
    for rel, digest in module_sha.items():
        assert digest == hashlib.sha256((probe._GIT_ROOT / rel).read_bytes()).hexdigest(), rel
    assert record["provenance"]["run"]["git_sha"] == _run["run_git_sha"]


# =================================================================================================
# Plan 31-02 Task 1 — the relearning half (ARCAL-02, D-04..D-06): one mitigated arm, full ladder
# =================================================================================================


def _relearn_probe_fixture(root):
    """ONE CPU run of run_relearn_probe through the REAL train_relearn_arm and score_rung.

    The Phase 27 harness (tiny base, decodable bins, two facts, the (1, 2) ladder at K 8) supplies
    the start adapter; phase29_prereg copies the ladder at import, so it is re-pointed at the
    patched Phase 27 values. Spies only count and forward. Every patch is undone on return.
    """
    import phase27_prereg
    import phase27_relearn as relearn

    from test_phase27_relearn import _ADMITTED, _e2e_env, _real_tree_strays

    strays_before = _real_probe31_strays()
    phase27_before = _real_tree_strays()
    heartbeat = root / "heartbeat.jsonl"
    calls, trained = {"train_relearn_arm": 0, "score_rung": 0}, {}
    with pytest.MonkeyPatch.context() as monkeypatch:
        env = _e2e_env(root, monkeypatch)
        monkeypatch.setattr(probe, "_ROOT", root)
        monkeypatch.setattr(probe, "refuse_if_dirty", lambda **kw: "")
        for name in ("RUNGS", "RELEARN_CAP", "CURVE_K"):
            monkeypatch.setattr(phase29_prereg, name, getattr(phase27_prereg, name))
        entry = env["frontier"]["points"][_ADMITTED[0]]
        start = pathlib.Path(entry["adapter_path"])
        sidecar = probe.point_run_sidecar()
        sidecar.parent.mkdir(parents=True, exist_ok=True)
        sidecar.write_text(
            json.dumps(
                {
                    "training": {
                        "adapter": start.relative_to(root).as_posix(),
                        "adapter_sha256": entry["adapter_sha256"],
                    }
                }
            ),
            encoding="utf-8",
        )

        def _spy(name):
            real = getattr(relearn, name)

            def spy(**kwargs):
                calls[name] += 1
                out = real(**kwargs)
                if name == "train_relearn_arm":
                    trained.update(out)
                return out

            monkeypatch.setattr(relearn, name, spy)

        _spy("train_relearn_arm")
        _spy("score_rung")
        probe.run_relearn_probe(heartbeat_path=heartbeat)
        run = json.loads(probe.relearn_run_sidecar().read_text(encoding="utf-8"))
        moves = [(str(s), s.exists(), str(d), d.exists()) for s, d in probe.relearn_moves()]
        ladder = tuple(phase29_prereg.RUNGS)
    record = probe.build_relearn_record(run)
    evidence = {
        "heartbeat_path": heartbeat,
        "root": root,
        "moves": moves,
        "calls": calls,
        "trained": trained,
        "ladder": ladder,
        "start_sha256": entry["adapter_sha256"],
        "strays": (strays_before, _real_probe31_strays()),
        "phase27_strays": (phase27_before, _real_tree_strays()),
    }
    return run, record, evidence


@pytest.fixture(scope="module")
def relearn_probe_run(tmp_path_factory):
    """ONE CPU relearn live-path run per module (the tests/test_phase27_relearn.py::e2e_run way)."""
    return _relearn_probe_fixture(tmp_path_factory.mktemp("relearn_probe"))


def test_relearn_live_path_runs_one_arm_on_the_full_ladder_on_cpu(relearn_probe_run):
    run, record, evidence = relearn_probe_run
    root = evidence["root"]
    trained_steps = [r["steps"] for r in evidence["trained"]["rungs"]]
    assert trained_steps == list(evidence["ladder"]) and len(trained_steps) > 1
    assert evidence["calls"] == {"train_relearn_arm": 1, "score_rung": len(trained_steps)}
    assert run["complete"] is True
    assert run["start_sha256"] == evidence["start_sha256"]
    assert run["train"]["seconds"] > 0
    assert [r["steps"] for r in run["rungs"]] == trained_steps
    for rung in record["stages"]["rungs"]:
        assert rung["remainder_seconds"] > 0
        assert rung["draw_seconds"] > 0
        # The fixture's K (8), read off the run: relearn_rung_label reads CURVE_K at call time.
        assert rung["label"] == f"{probe.RELEARN_LABEL}_n64_rung{rung['steps']:04d}_k{run['k']}"
    assert record["start_sha256"] == evidence["start_sha256"]
    # Every train_relearn_arm leftover moved under data/probe31_relearn/.
    assert not any((root / "results").iterdir())
    assert not list((root / "data").glob("persona_relearn_attacker_*"))
    assert not list((root / "checkpoints").glob("phase27_*"))
    assert len(evidence["moves"]) == 4
    for src, src_exists, dst, dst_exists in evidence["moves"]:
        assert (src_exists, dst_exists) == (False, True), (src, dst)
        assert pathlib.Path(dst).parent == root / "data" / "probe31_relearn"
    last = evidence["heartbeat_path"].read_text(encoding="utf-8").splitlines()[-1]
    assert json.loads(last)["stage"] == "done"
    before, after = evidence["strays"]
    assert before == after
    before, after = evidence["phase27_strays"]
    assert before == after


def test_relearn_record_proves_the_moved_bin(relearn_probe_run):
    run, _record, evidence = relearn_probe_run
    (bin_dst,) = [d for _s, _e, d, _x in evidence["moves"] if d.endswith("_train.bin")]
    digest = hashlib.sha256(pathlib.Path(bin_dst).read_bytes()).hexdigest()
    assert digest == run["train"]["bin_sha256"] == evidence["trained"]["bin_sha256"]


_START_SHA = "b" * 64


def _light_relearn_env(tmp_path, monkeypatch):
    """The cheap refusal tests: device pinned, every path under tmp_path, a synthetic point run."""
    import phase27_relearn as relearn

    tp = _tp()
    monkeypatch.setattr(phase25_run, "_DEVICE", "cpu")
    monkeypatch.setattr(probe, "_ROOT", tmp_path)
    monkeypatch.setattr(phase25_run, "DRAWS_DIR", tmp_path / "data")
    monkeypatch.setattr(tp, "_REPO_ROOT", tmp_path)
    for name in ("train_relearn_arm", "score_rung"):
        monkeypatch.setattr(relearn, name, lambda **kw: pytest.fail("ran past a refusal"))
    sidecar = probe.point_run_sidecar()
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text(
        json.dumps({"training": {"adapter": "checkpoints/a.pt", "adapter_sha256": _START_SHA}}),
        encoding="utf-8",
    )


def _after_training_setup(tmp_path, *, moved):
    """A completed training: the train sidecar, the four leftovers, an empty in-progress run and
    a draw cache for the first rung. Returns ``(cache, moves)``."""
    bin_bytes = b"synthetic attacker bin"
    moves = probe.relearn_moves()
    for src, dst in moves:
        target = dst if moved else src
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(bin_bytes if dst.name.endswith("_train.bin") else b"x")
    phase25_run.atomic_write_json(
        probe.relearn_train_sidecar(),
        {
            "seconds": 12.0,
            "start_adapter": "checkpoints/a.pt",
            "start_sha256": _START_SHA,
            "bin_sha256": hashlib.sha256(bin_bytes).hexdigest(),
            "rungs": [
                {
                    "steps": steps,
                    "adapter_path": f"data/probe31_relearn/rung{steps:04d}_adapter.pt",
                    "adapter_sha256": "c" * 64,
                }
                for steps in phase29_prereg.RUNGS
            ],
            "moves": [[probe._rel(s), probe._rel(d)] for s, d in moves],
        },
    )
    phase25_run.atomic_write_json(probe.relearn_run_sidecar(), {"complete": False, "rungs": []})
    cache = phase25_run.draws_path(probe.relearn_rung_label(phase29_prereg.RUNGS[0]))
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text("{}", encoding="utf-8")
    return cache, moves


def test_relearn_refuses_a_mid_rung_resume(tmp_path, monkeypatch):
    _light_relearn_env(tmp_path, monkeypatch)
    cache, _moves = _after_training_setup(tmp_path, moved=True)
    with pytest.raises(SystemExit, match=cache.name):
        probe.run_relearn_probe(heartbeat_path=tmp_path / "hb.jsonl")


def test_relearn_refuses_without_a_completed_point_probe(tmp_path, monkeypatch):
    monkeypatch.setattr(probe, "_ROOT", tmp_path)  # EMPTY: no point run sidecar
    with pytest.raises(SystemExit, match=r"probe31_point_run\.json"):
        probe.run_relearn_probe(heartbeat_path=tmp_path / "hb.jsonl")


def test_relearn_refuses_a_half_trained_arm(tmp_path, monkeypatch):
    _light_relearn_env(tmp_path, monkeypatch)
    heartbeat = tmp_path / "hb.jsonl"
    # 1. out_dir without the train sidecar.
    probe.relearn_out_dir().mkdir(parents=True)
    with pytest.raises(SystemExit, match=r"data/probe31_relearn\b"):
        probe.run_relearn_probe(heartbeat_path=heartbeat)
    probe.relearn_out_dir().rmdir()
    # 2. the resume checkpoint at its SOURCE without the train sidecar.
    (checkpoint, _dst) = probe.relearn_moves()[-1]
    assert checkpoint.name.endswith("_latest.pt")
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.write_bytes(b"half")
    with pytest.raises(SystemExit, match=checkpoint.name):
        probe.run_relearn_probe(heartbeat_path=heartbeat)
    checkpoint.unlink()
    # 3. the restart after training passes the half-trained check and stops at the draw cache.
    cache, moves = _after_training_setup(tmp_path, moved=True)
    with pytest.raises(SystemExit, match=cache.name) as caught:
        probe.run_relearn_probe(heartbeat_path=heartbeat)
    message = str(caught.value)
    assert str(probe.relearn_out_dir()) not in message
    assert checkpoint.name not in message
    # 4. a crash between the sidecar write and the moves: the restart finishes the moves.
    for src, dst in moves:
        src.parent.mkdir(parents=True, exist_ok=True)
        dst.rename(src)
    with pytest.raises(SystemExit, match=cache.name):
        probe.run_relearn_probe(heartbeat_path=heartbeat)
    for src, dst in moves:
        assert (src.exists(), dst.exists()) == (False, True), (src, dst)
    # 5. both copies of the bin present: refused, naming both.
    ((bin_src, bin_dst),) = [(s, d) for s, d in moves if d.name.endswith("_train.bin")]
    bin_src.write_bytes(bin_dst.read_bytes())
    with pytest.raises(SystemExit) as caught:
        probe.run_relearn_probe(heartbeat_path=heartbeat)
    message = str(caught.value)
    assert bin_src.relative_to(tmp_path).as_posix() in message
    assert bin_dst.relative_to(tmp_path).as_posix() in message


def test_relearn_rung_labels_are_isolated():
    labels = [probe.relearn_rung_label(steps) for steps in phase29_prereg.RUNGS]
    assert labels == [
        f"{probe.RELEARN_LABEL}_n64_rung{steps:04d}_k{phase29_prereg.CURVE_K}"
        for steps in phase29_prereg.RUNGS
    ]
    ours = {phase25_run.draws_path(label) for label in labels}
    theirs = {phase25_run.draws_path(key) for key in phase29_prereg.POINT_KEYS()}
    assert len(ours) == len(phase29_prereg.RUNGS)
    assert ours.isdisjoint(theirs)
    for label in labels:
        assert not label.startswith(("phase27_", "phase32_"))
        assert not phase25_run.draws_path(label).name.startswith(
            ("phase25_phase27_", "phase25_phase32_")
        )


def _synthetic_relearn_run(**overrides):
    rungs = [
        {
            "steps": steps,
            "label": probe.relearn_rung_label(steps),
            "adapter_path": f"data/probe31_relearn/rung{steps:04d}_adapter.pt",
            "adapter_sha256": "c" * 64,
            "seconds": 750.0,
            "shape_minutes": {"A1-aggressive": 3.0, "A1-mild": 2.0, "A2": 2.0, "A3": 3.0},
            "reading": {"taught_recall": {"numerator": 1, "denominator": 2}},
        }
        for steps in phase29_prereg.RUNGS
    ]
    run = {
        "complete": True,
        "relearn_label": probe.RELEARN_LABEL,
        "leg": "n64",
        "arm": "mitigated",
        "seed": phase29_prereg.DESIGNATED_SEED,
        "relearn_cap": phase29_prereg.RELEARN_CAP,
        "ladder": list(phase29_prereg.RUNGS),
        "k": phase29_prereg.CURVE_K,
        "start_adapter": "checkpoints/probe31_advr_n64_adapter.pt",
        "start_sha256": _START_SHA,
        "train": {"seconds": 900.0, "bin_sha256": "d" * 64, "run_git_sha": "0" * 40},
        "rungs": rungs,
        "run_git_sha": "0" * 40,
        "device": "cpu",
        "torch_version": "0.0",
        "started_utc": "2026-01-01T00:00:00+00:00",
        "finished_utc": "2026-01-01T03:00:00+00:00",
    }
    run.update(overrides)
    return run


def test_build_relearn_record_shape():
    run = _synthetic_relearn_run()
    record = probe.build_relearn_record(run)
    assert record["sweep_point"] is False and record["sweep_point_false_reason"]
    assert "D-04" in record["unit"]
    assert (record["leg"], record["arm"]) == ("n64", "mitigated")
    assert record["seed"] == phase29_prereg.DESIGNATED_SEED
    assert record["relearn_cap"] == phase29_prereg.RELEARN_CAP
    assert record["rungs"] == list(phase29_prereg.RUNGS)
    assert record["k"] == phase29_prereg.CURVE_K
    assert record["start_sha256"] == _START_SHA and record["start_adapter"]
    assert record["stages"]["train"]["seconds"] == 900.0
    rows = record["stages"]["rungs"]
    assert [r["steps"] for r in rows] == list(phase29_prereg.RUNGS)
    for row in rows:
        assert set(row) == {
            "steps",
            "label",
            "seconds",
            "draw_seconds",
            "shape_minutes",
            "remainder_seconds",
        }
        assert row["draw_seconds"] == 600.0
        assert row["remainder_seconds"] == row["seconds"] - row["draw_seconds"] == 150.0
    assert record["arm_seconds"] == 900.0 + sum(r["seconds"] for r in rows)
    assert record["readings"]["gates_nothing"] is True
    # A rung whose draws fill (or overfill) its bracket is refused: remainder must be > 0.
    bad = _synthetic_relearn_run()
    bad["rungs"][0]["seconds"] = 600.0
    with pytest.raises(SystemExit, match="remainder"):
        probe.build_relearn_record(bad)
    with pytest.raises(SystemExit, match="complete"):
        probe.build_relearn_record(_synthetic_relearn_run(complete=False))


def _write_relearn_sidecars(run):
    probe.relearn_train_sidecar().parent.mkdir(parents=True, exist_ok=True)
    phase25_run.atomic_write_json(probe.relearn_train_sidecar(), {"seconds": 900.0})
    phase25_run.atomic_write_json(probe.relearn_run_sidecar(), run)


def test_emit_relearn_chains_to_the_committed_point_record(tmp_path, monkeypatch):
    monkeypatch.setattr(probe, "_ROOT", tmp_path)
    _write_relearn_sidecars(_synthetic_relearn_run())
    out = tmp_path / "relearn.json"
    # Branch 1: the point record is not tracked — refused through the real _tracked_json.
    monkeypatch.setattr(probe, "_tracked", lambda: ["results/phase30_calibration.json"])
    with pytest.raises(SystemExit, match=probe.POINT_RECORD):
        probe.emit_relearn(out)
    assert not out.exists()
    # Branch 2: tracked, but its adapter is not the one the relearning started from.
    monkeypatch.setattr(probe, "_tracked", lambda: [probe.POINT_RECORD])
    monkeypatch.setattr(
        pts, "_tracked_json", lambda rel, tracked, what: {"adapter": {"sha256": "f" * 64}}
    )
    with pytest.raises(SystemExit, match="start_sha256"):
        probe.emit_relearn(out)
    assert not out.exists()


def test_emit_relearn_writes_the_chained_record(relearn_probe_run, tmp_path, monkeypatch):
    run, _record, evidence = relearn_probe_run
    monkeypatch.setattr(probe, "_ROOT", evidence["root"])
    monkeypatch.setattr(probe, "_tracked", lambda: [probe.POINT_RECORD])
    forged = {"adapter": {"sha256": run["start_sha256"]}}
    seen = []
    monkeypatch.setattr(pts, "_tracked_json", lambda rel, tracked, what: seen.append(rel) or forged)
    out = tmp_path / "relearn.json"
    record = probe.emit_relearn(out)
    assert seen == [probe.POINT_RECORD]
    assert json.loads(out.read_text(encoding="utf-8")) == json.loads(json.dumps(record))
    assert record["point_record"] == {
        "path": probe.POINT_RECORD,
        "adapter_sha256": run["start_sha256"],
    }
    assert record["calibration"]["is_ancestor_of_head"] is True
    assert set(record["provenance"]["module_sha256"]) == set(probe.PINNED_MODULES)
    with pytest.raises(SystemExit, match="REFUSING to overwrite"):
        probe.emit_relearn(out)


def test_emit_relearn_is_write_once_on_the_real_path():
    record = probe._GIT_ROOT / probe.RELEARN_RECORD
    assert probe.RELEARN_RECORD in phase29_prereg.V5_RESULT_PATHS
    if probe.RELEARN_RECORD in probe._tracked():
        before = record.read_bytes()
        with pytest.raises(SystemExit, match="REFUSING to overwrite"):
            probe.emit_relearn()
        assert record.read_bytes() == before
    else:
        assert not record.exists(), f"{probe.RELEARN_RECORD} exists but is untracked"


def test_relearn_calls_no_admitted_leg():
    import ast

    tree = ast.parse((_ROOT / "scripts" / "phase31_probe.py").read_text(encoding="utf-8"))
    names = {
        node.attr if isinstance(node, ast.Attribute) else node.id
        for node in ast.walk(tree)
        if isinstance(node, (ast.Attribute, ast.Name))
    }
    assert {"train_relearn_arm", "score_rung"} <= names  # meta-guard: the walk sees the calls
    banned = {"run_calibrate", "run_curve", "run_gate", "_require_admitted"}
    assert not names & banned, sorted(names & banned)


# =================================================================================================
# Plan 31-02 Task 2 — the CLI (run / emit) and the D-12 LaunchAgent
# =================================================================================================

_PROBE_PLIST = _ROOT / "artifacts" / "com.personacore.phase31.probe.plist"
_CANARY_PLIST = _ROOT / "artifacts" / "com.personacore.phase26.canary.plist"


def _recorders(monkeypatch, *, point_raises=False):
    import inspect

    calls = []
    for name, tag in (("run_point_probe", "point"), ("run_relearn_probe", "relearn")):
        signature = inspect.signature(getattr(probe, name))

        def recorder(*args, _tag=tag, _sig=signature, **kwargs):
            _sig.bind(*args, **kwargs)  # the kwargs main() passes must fit the REAL function
            calls.append((_tag, kwargs))
            if _tag == "point" and point_raises:
                raise SystemExit("[probe] point failed")

        monkeypatch.setattr(probe, name, recorder)
    return calls


def test_main_run_dispatches_point_then_relearn(tmp_path, monkeypatch):
    calls = _recorders(monkeypatch)
    beat = tmp_path / "hb.jsonl"
    assert probe.main(["run", "--heartbeat", str(beat)]) == 0
    assert calls == [("point", {"heartbeat_path": beat}), ("relearn", {"heartbeat_path": beat})]


def test_main_run_stops_before_relearn_when_point_fails(tmp_path, monkeypatch):
    calls = _recorders(monkeypatch, point_raises=True)
    with pytest.raises(SystemExit, match="point failed"):
        probe.main(["run", "--heartbeat", str(tmp_path / "hb.jsonl")])
    assert [tag for tag, _kw in calls] == ["point"]


def test_main_emit_dispatches(monkeypatch):
    calls = []
    monkeypatch.setattr(probe, "emit_point", lambda: calls.append("point"))
    monkeypatch.setattr(probe, "emit_relearn", lambda: calls.append("relearn"))
    assert probe.main(["emit", "point"]) == 0
    assert probe.main(["emit", "relearn"]) == 0
    assert calls == ["point", "relearn"]
    with pytest.raises(SystemExit) as caught:
        probe.main(["emit", "budget"])
    assert caught.value.code != 0
    assert calls == ["point", "relearn"]


def test_main_run_defaults_to_the_shared_heartbeat(monkeypatch):
    calls = _recorders(monkeypatch)
    assert probe.main(["run"]) == 0
    assert [kw for _tag, kw in calls] == [{"heartbeat_path": phase25_run.HEARTBEAT_PATH}] * 2


def test_plist_mirrors_the_canary_agent():
    import plistlib

    ours = plistlib.loads(_PROBE_PLIST.read_bytes())
    canary = plistlib.loads(_CANARY_PLIST.read_bytes())
    assert ours["Label"] == "com.personacore.phase31.probe"
    assert ours["KeepAlive"] is False and ours["RunAtLoad"] is False
    args, canary_args = ours["ProgramArguments"], canary["ProgramArguments"]
    assert args[:3] == canary_args[:3]
    assert args[3].endswith("scripts/phase31_probe.py") and args[4] == "run"
    # 2026-09-28 (R-2): suffix comparison so the heartbeat assertion is host-independent (the CI
    # root is /home/runner/...); ported from f47468b.
    expected_rel = phase25_run.HEARTBEAT_PATH.relative_to(_ROOT)
    heartbeat = pathlib.Path(args[args.index("--heartbeat") + 1])
    canary_heartbeat = pathlib.Path(canary_args[canary_args.index("--heartbeat") + 1])
    assert heartbeat == canary_heartbeat
    assert heartbeat.parts[-len(expected_rel.parts) :] == expected_rel.parts
    assert ours["WorkingDirectory"] == canary["WorkingDirectory"]
    for key in ("StandardOutPath", "StandardErrorPath"):
        assert "/logs/" in ours[key] and ours[key] != canary[key]
    assert ours["EnvironmentVariables"] == canary["EnvironmentVariables"]
    assert ours["EnvironmentVariables"]["PERSONACORE_SWEEP_ACTIVE"] == "1"
    assert ours["ProcessType"] == canary["ProcessType"]
