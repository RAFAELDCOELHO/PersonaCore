"""Plan 31-01: the point half of the Phase 31 MPS cost probe (ARCAL-01, D-01..D-03, D-11).

CPU-only. Nothing here writes under the real results/, data/ or checkpoints/: every sidecar,
adapter, checkpoint, draw cache and emitted record lands under a tmp directory.
"""

import json
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
