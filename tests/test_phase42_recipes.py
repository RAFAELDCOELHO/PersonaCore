"""Plan 42-04: the E3 driver's measuring half (scripts/phase42_recipes.py), tested on CPU only.

The per-cell plan, the D-05 training seam (teach_persona's LR / WARMUP_STEPS / MAX_STEPS rebound
around one phase25_points.train_stage call, proved from the sidecar), the resume guard, scoring,
the write-once records, preflight and run under the ledger. Every heavy call is faked at the seam
the driver reaches (phase25_points.train_stage, teach_persona.score_arm,
phase14_recall.load_adapted_model, phase25_condition_c.measure_condition_c); nothing here writes
the real results/, ledger/, data/ or checkpoints/ (the autouse guard checks it around every test).
"""

import hashlib
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

import phase25_points  # noqa: E402  (scripts/ is not a package)
import phase35_prereg  # noqa: E402  (same)
import phase42_prereg  # noqa: E402  (same; frozen for this plan: import only)
import phase42_recipes  # noqa: E402  (same; never aliased)
import teach_persona  # noqa: E402  (same)

from test_phase29_prereg import _git  # noqa: E402

_V4_TRAIN_CONFIG = json.loads(
    (_ROOT / phase42_prereg.V4_CONTROL_RECORD).read_text(encoding="utf-8")
)["training"]["train_config"]


def _phase42_outputs():
    return sorted(
        p.relative_to(_ROOT).as_posix()
        for d in ("results", "data", "checkpoints", "data/phase25_runs")
        for p in (_ROOT / d).glob("*phase42*")
    )


@pytest.fixture(autouse=True)
def _real_tree_untouched():
    before = _git("status", "--porcelain", "--", "results", "ledger")
    outputs = _phase42_outputs()
    yield
    assert _git("status", "--porcelain", "--", "results", "ledger") == before
    assert _phase42_outputs() == outputs


def _schedule():
    return (teach_persona.LR, teach_persona.WARMUP_STEPS, teach_persona.MAX_STEPS)


def _train_rig(monkeypatch, tmp_path, *, crash=False, mutate=None):
    """teach_persona and phase25_points rooted at a tmp repository; phase25_points.train_stage
    faked: it records the rebound schedule at call time, writes the adapter and returns a sidecar
    blob whose train_config is built from the rebound globals (the real stage's tp.asdict)."""
    repo = tmp_path / "repo"
    for sub in ("checkpoints", "data", "results"):
        (repo / sub).mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(teach_persona, "_REPO_ROOT", repo)
    monkeypatch.setattr(phase25_points, "_ROOT", repo)
    calls = []

    def train_stage(plan):
        calls.append((plan["point_key"], _schedule()))
        if crash:
            raise RuntimeError("training died")
        adapter = teach_persona.arm_outputs(plan["arm"], prefix=plan["prefix"])["adapter"]
        adapter.write_bytes(plan["point_key"].encode())
        blob = {
            "point_key": plan["point_key"],
            "arm": plan["arm"],
            "prefix": plan["prefix"],
            "seed": plan["seed"],
            "n_facts": plan["n_facts"],
            "adapter": adapter.relative_to(repo).as_posix(),
            "adapter_sha256": hashlib.sha256(adapter.read_bytes()).hexdigest(),
            "seconds": 2.5,
            "resumed_from_step": 0,
            "live_mechanism": {
                "composed_steps": teach_persona.MAX_STEPS,
                "composed_lot_sizes": [plan["n_facts"]],
                "records_per_lot": plan["n_facts"],
                "q": plan["pinned_mechanism"]["q"],
                "clip_norm": plan["dp_clip_norm"],
            },
            "pinned_mechanism": plan["pinned_mechanism"],
            "clip_bind_count": 0 if plan["is_control"] else 3,
            "ppl_adapter_on": 5.5,
            "ppl_adapter_off": 6.25,
            "final_train_loss": 1.0,
            "train_config": dict(
                _V4_TRAIN_CONFIG,
                lr=teach_persona.LR,
                max_steps=teach_persona.MAX_STEPS,
                warmup_steps=teach_persona.WARMUP_STEPS,
            ),
        }
        if mutate is not None:
            mutate(blob)
        return blob

    monkeypatch.setattr(phase25_points, "train_stage", train_stage)
    return calls


# =================================================================================================
# (1) Import surface, the cell plan and the D-05 seam (plan 42-04 Task 1; D-05, D-06, D-07).
# =================================================================================================


def test_the_driver_imports_without_torch():
    probe = (
        "import sys; sys.path[:0] = [{s!r}, {r!r}]; import phase42_recipes; "
        "print(phase42_recipes.FRONT, *(m in sys.modules for m in "
        "('torch', 'teach_persona', 'phase14_recall', 'phase42_prereg')))"
    ).format(s=str(_SCRIPTS), r=str(_SRC))
    out = subprocess.run(
        (sys.executable, "-c", probe), capture_output=True, text=True, check=True, cwd=_ROOT
    ).stdout.strip()
    assert out == "E3 False False False False"


def test_clip_and_plan_for_every_unit():
    p = phase42_prereg
    for unit in p.UNITS:
        recipe, sigma = p.unit_cell(unit)
        for rehearsal in (False, True):
            plan = phase42_recipes.cell_plan(unit, rehearsal=rehearsal)
            prefix = p.train_prefix(unit, rehearsal=rehearsal)
            assert plan["point_key"] == plan["prefix"] == prefix
            assert plan["arm"] == f"dp_n{phase35_prereg.E3_N}"
            assert plan["dp_sigma"] == sigma
            assert plan["dp_clip_norm"] == p.clip_norm_for(sigma)
            assert plan["seed"] == p.SEED
            assert plan["pinned_mechanism"]["composed_steps"] == recipe["steps"]
            assert plan["point_epsilon"] is None and plan["accounting"] is None
            assert plan["is_control"] is (sigma == p.CONTROL_SIGMA)
        if sigma == p.CONTROL_SIGMA:
            assert plan["dp_clip_norm"] == phase42_prereg.clip_norm_for(0.0)
        else:
            assert plan["dp_clip_norm"] == 1.3254119157791138  # D-06, the literal in the test only
    with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
        phase42_recipes.cell_plan("point_x", rehearsal=False)


def test_warmup_rebinding_takes_and_restores(monkeypatch, tmp_path):
    before = _schedule()
    calls = _train_rig(monkeypatch, tmp_path)
    plan, blob = phase42_recipes.train_cell("control_lr1e-03_t200", rehearsal=False)
    assert _schedule() == before
    plan2, blob2 = phase42_recipes.train_cell("point_lr3e-04_t800_sigma1p000000", rehearsal=True)
    assert _schedule() == before
    assert calls == [
        ("phase42e3_control_lr1e-03_t200", (0.001, 20, 200)),
        ("phase42rh_point_lr3e-04_t800_sigma1p000000", (0.0003, 80, 800)),
    ]
    assert plan["point_key"] == "phase42e3_control_lr1e-03_t200"
    assert blob2["train_config"]["warmup_steps"] == 80 and blob2["train_config"]["grad_clip"] == 1.0
    assert plan2["dp_sigma"] == 1.0 and blob["clip_bind_count"] == 0


def test_warmup_rebinding_restored_when_training_raises(monkeypatch, tmp_path):
    before = _schedule()
    calls = _train_rig(monkeypatch, tmp_path, crash=True)
    with pytest.raises(RuntimeError, match="training died"):
        phase42_recipes.train_cell("point_lr1e-03_t800_sigma0p500000", rehearsal=False)
    assert calls == [("phase42e3_point_lr1e-03_t800_sigma0p500000", (0.001, 80, 800))]
    assert _schedule() == before


@pytest.mark.parametrize(
    "field, value",
    [
        ("warmup_steps", 20),
        ("composed_steps", 200),
        ("grad_clip", 0.5),
        ("clip_norm", 1.0),
    ],
)
def test_take_proof_refuses_a_wrong_schedule(monkeypatch, tmp_path, field, value):
    def mutate(blob):
        target = blob["train_config"] if field in blob["train_config"] else blob["live_mechanism"]
        target[field] = value

    before = _schedule()
    calls = _train_rig(monkeypatch, tmp_path, mutate=mutate)
    with pytest.raises(SystemExit, match=r"^\[phase42_recipes\]"):
        phase42_recipes.train_cell("point_lr3e-04_t800_sigma0p500000", rehearsal=False)
    assert len(calls) == 1 and _schedule() == before


def _plant_checkpoint(unit, *, rehearsal, **train_config):
    plan = phase42_recipes.cell_plan(unit, rehearsal=rehearsal)
    path = teach_persona.arm_outputs(plan["arm"], prefix=plan["prefix"])["checkpoint"]
    path.parent.mkdir(parents=True, exist_ok=True)
    teach_persona.torch.save(
        {"step": 50, "train_config": dict(_V4_TRAIN_CONFIG, **train_config)}, path
    )
    return path


def test_resume_guard(monkeypatch, tmp_path):
    unit = "point_lr3e-04_t800_sigma1p000000"
    calls = _train_rig(monkeypatch, tmp_path)
    path = _plant_checkpoint(unit, rehearsal=False, lr=0.0003, warmup_steps=20, max_steps=200)
    with pytest.raises(SystemExit, match=r"^\[phase42_recipes\].*Pitfall 1"):
        phase42_recipes.train_cell(unit, rehearsal=False)
    assert calls == []
    path.unlink()
    _plant_checkpoint(unit, rehearsal=False, lr=0.0003, warmup_steps=80, max_steps=800)
    phase42_recipes.train_cell(unit, rehearsal=False)
    assert len(calls) == 1
    # A finished sidecar is reused by train_stage itself; the guard does not read the checkpoint.
    plan = phase42_recipes.cell_plan(unit, rehearsal=False)
    path.unlink()
    _plant_checkpoint(unit, rehearsal=False, lr=0.001, warmup_steps=80, max_steps=800)
    sidecar = phase25_points.training_sidecar(plan["point_key"])
    sidecar.write_text("{}", encoding="utf-8")
    phase42_recipes._resume_guard(plan, phase42_prereg.unit_cell(unit)[0])


# =================================================================================================
# (2) Scoring, retention and the write-once control and point records (plan 42-04 Task 2;
# RECIPE-02, D-13, D-23; the unwired-driver lesson: the real consumer reads the real producer).
# =================================================================================================

_READING = {
    "adapter_on": 5.5,
    "adapter_off": 6.25,
    "n_targets": 40,
    "retention_ppl": 3.9,
    "retention_total_tokens": 51234,
}


def _block(k, n):
    return {"k": k, "n": n, "rate": k / n, "questions": n // 9, "per_family": {"a": [k, n]}}


def _measure_rig(monkeypatch, tmp_path, *, taught=(790, 1008), heldout=(346, 648), mutate=None):
    """_train_rig plus score_arm, load_adapted_model and measure_condition_c faked, and the pf
    dict write_unit reads for a scratch root ``tmp_path / "out"`` with its own ledger."""
    import phase14_recall
    import phase25_condition_c

    calls = {"train": _train_rig(monkeypatch, tmp_path, mutate=mutate), "score": [], "load": []}

    def score_arm(arm, facts, adapter_path, device):
        calls["score"].append((arm, adapter_path, device))
        return {
            "on_taught": _block(*taught),
            "on_heldout": _block(*heldout),
            "off_taught": _block(9, taught[1]),
            "off_heldout": _block(3, heldout[1]),
            "per_family_gain": {"a": 0.5},
        }

    def load_adapted_model(device, adapter_path=None):
        calls["load"].append((device, adapter_path))
        return "model", "cfg", "tok", "forbid", "artifact"

    def measure_condition_c(model, tok, device, *, forbid):
        assert (model, tok, forbid) == ("model", "tok", "forbid")
        return dict(_READING)

    monkeypatch.setattr(teach_persona, "score_arm", score_arm)
    monkeypatch.setattr(phase14_recall, "load_adapted_model", load_adapted_model)
    monkeypatch.setattr(phase25_condition_c, "measure_condition_c", measure_condition_c)
    monkeypatch.setattr(phase42_recipes, "_release", lambda: None)
    monkeypatch.setattr(phase42_recipes, "git_sha", lambda: "h1")
    root = tmp_path / "out"
    pf = {
        "root": root,
        "real": False,
        "device": "cpu",
        "ledger_path": tmp_path / "ledger.jsonl",
        "heartbeat_path": tmp_path / "heartbeat.jsonl",
        "git_sha": "h1",
        "module_sha256": phase42_recipes.module_sha256(),
    }
    return calls, pf


def _write(unit, pf):
    state = {"point": unit, "stage": "start", "shape": None, "draw_index": None}
    rel = phase42_recipes.write_unit(unit, pf=pf, started_utc="t0", state=state)
    assert state["stage"] == "done"
    return rel, json.loads((pf["root"] / rel).read_text(encoding="utf-8"))


def test_control_record_satisfies_the_contract_and_the_real_rule(monkeypatch, tmp_path):
    p = phase42_prereg
    calls, pf = _measure_rig(monkeypatch, tmp_path)
    for unit in p.CONTROL_UNITS:
        rel, record = _write(unit, pf)
        recipe, sigma = p.unit_cell(unit)
        assert rel == p.unit_record(unit)
        assert record["unit"] == unit and record["recipe"] == dict(recipe)
        assert record["seed"] == p.SEED and record["sigma"] == p.CONTROL_SIGMA == sigma
        assert record["taught_recall"]["numerator"] == 790
        assert record["taught_recall"]["denominator"] == 1008
        assert record["heldout_recall"]["numerator"] == 346
        assert record["heldout_recall"]["denominator"] == 648
        assert record["taught_recall_off"]["numerator"] == 9
        assert record["epsilon"] is None and record["selection_accounted"] is False
        assert record["clip_bind_count"] == 0
        assert record["dialogue_gap"] == 5.5 - 6.25
        assert record["condition_c"]["retention_ppl"] == _READING["retention_ppl"]
        assert record["condition_c"]["seconds"] >= 0
        assert record["training"]["train_config"] == dict(p.expected_train_config(recipe))
        assert set(record["provenance"]["run"]) == set(phase42_recipes.RUN_PROVENANCE_KEYS)
        run = record["provenance"]["run"]
        assert run["device"] == "cpu" and run["started_utc"] == "t0"
        assert run["git_sha_at_launch"] == run["git_sha_at_end"] == "h1"
        assert run["head_moved_during_run"] is False
        assert record["module_sha256_at_launch"] == pf["module_sha256"]
        assert record["rehearsal_disclosure"] == {"this_is_the_rehearsal": True}
        assert record["lost_attempts"] == []
        # The emit's consumer reads it (D-13).
        assert phase42_prereg.descriptive_reading(record)["dialogue_gap"] == -0.75
    assert len(calls["score"]) == len(calls["load"]) == len(p.CONTROL_UNITS)

    # The REAL Phase 35 threshold rule accepts the driver-written records.
    v4_copy = pf["root"] / p.V4_CONTROL_RECORD
    v4_copy.write_bytes((_ROOT / p.V4_CONTROL_RECORD).read_bytes())
    monkeypatch.setattr(phase35_prereg, "_REPO_ROOT", pf["root"])
    thresholds = phase35_prereg.fill(
        "e3_recall_threshold", **phase42_prereg.threshold_fill_inputs()
    )
    assert set(thresholds) == {phase42_prereg.recipe_key(r) for r in p.RECIPES}
    for unit in p.CONTROL_UNITS:
        threshold = thresholds[phase42_prereg.recipe_key(phase42_prereg.unit_cell(unit)[0])]
        assert threshold["control"] == phase42_prereg.unit_record(unit)
        assert threshold["taught"] == phase35_prereg.F_Y * 790 / 1008
        assert threshold["heldout"] == phase35_prereg.F_Y * 346 / 648


def test_point_record_epsilon(monkeypatch, tmp_path):
    p = phase42_prereg
    unit = "point_lr3e-04_t800_sigma0p500000"
    _calls, pf = _measure_rig(monkeypatch, tmp_path)
    _rel, record = _write(unit, pf)
    assert record["sigma"] == 0.5 and record["recipe"]["steps"] == 800
    import math

    assert math.isclose(record["epsilon"], phase42_prereg.point_epsilon(0.5, 800), rel_tol=1e-12)
    assert record["delta"] == phase35_prereg.DELTA
    assert record["selection_accounted"] is False
    assert record["accounting"]["composed_steps"] == 800
    assert set(record["accounting"]) == {"q", "composed_steps", "composed_lot_sizes"}
    assert record["clip_norm"] == phase42_prereg.clip_norm_for(0.5)
    assert record["clip_bind_count"] == 3
    # The declared omission, never a refusal measurement (refusal_omitted).
    assert record["refusal"] == p.ENTRIES["refusal_omitted"]["derivation"]
    assert [k for k in record if "refusal" in k] == ["refusal"]
    assert record["descriptive"] == ["clip_bind_count", "dialogue_gap", "condition_c"]


def test_write_once_refuses_an_existing_record(monkeypatch, tmp_path):
    unit = "control_lr1e-03_t200"
    calls, pf = _measure_rig(monkeypatch, tmp_path)
    _write(unit, pf)
    assert len(calls["train"]) == len(calls["score"]) == 1
    with pytest.raises(SystemExit, match=r"^\[phase42_recipes\].*write-once"):
        _write(unit, pf)
    assert len(calls["train"]) == len(calls["score"]) == 1


def test_adapter_digest_checked_before_scoring(monkeypatch, tmp_path):
    def mutate(blob):
        blob["adapter_sha256"] = "0" * 64

    calls, pf = _measure_rig(monkeypatch, tmp_path, mutate=mutate)
    with pytest.raises(SystemExit, match=r"^\[phase42_recipes\].*adapter"):
        _write("control_lr1e-03_t200", pf)
    assert len(calls["train"]) == 1 and calls["score"] == [] and calls["load"] == []
    assert not (pf["root"] / phase42_prereg.unit_record("control_lr1e-03_t200")).exists()


def test_lost_attempts_are_read_from_the_ledger(monkeypatch, tmp_path):
    import phase36_ledger

    unit = "control_lr1e-03_t800"
    _calls, pf = _measure_rig(monkeypatch, tmp_path)
    rid = phase42_prereg.run_id(unit)
    phase36_ledger.append("start", run_id=rid, phase=42, front="E3", ledger_path=pf["ledger_path"])
    phase36_ledger.append(
        "lost",
        run_id=rid,
        phase=42,
        front="E3",
        seconds=12.0,
        flag=phase36_ledger.LOST_FLAG,
        ledger_path=pf["ledger_path"],
    )
    _rel, record = _write(unit, pf)
    assert [(x["event"], x["run_id"], x["seconds"]) for x in record["lost_attempts"]] == [
        ("lost", rid, 12.0)
    ]


# =================================================================================================
# (3) Preflight, the stage-2 P22 re-assert, run under the ledger, the relaunch pathspec and the
# rehearsal identity (plan 42-04 Task 3; RECIPE-04, D-08, D-19, D-20, D-21, D-22; crash_rule).
# =================================================================================================


def _run_rig(monkeypatch, tmp_path, *, real=False):
    """_measure_rig plus a tmp root holding copies of the budget and the v4.0 control,
    refuse_if_dirty recorded, the caps reading the committed budget only. ``real``: _ROOT and the
    milestone ledger / heartbeat point into the rig, the device is mps, the rehearsal identity is
    recorded at the current digests and nothing reads as tracked (the threshold file absent)."""
    import phase36_caps
    import phase36_ledger

    calls, pf = _measure_rig(monkeypatch, tmp_path)
    root = pf["root"]
    for rel in (phase42_prereg.BUDGET_RECORD, phase42_prereg.V4_CONTROL_RECORD):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes((_ROOT / rel).read_bytes())
    calls["dirty"] = []
    monkeypatch.setattr(phase42_recipes, "refuse_if_dirty", lambda **kw: calls["dirty"].append(kw))
    monkeypatch.setattr(phase36_caps, "tracked_files", lambda: [phase36_caps.BUDGET_RECORD])
    if not real:
        kw = {
            "root": root,
            "ledger_path": pf["ledger_path"],
            "heartbeat_path": pf["heartbeat_path"],
            "device": "cpu",
        }
        return calls, kw, pf["ledger_path"]
    monkeypatch.setattr(phase42_recipes, "_ROOT", root)
    monkeypatch.setattr(phase36_ledger, "_ROOT", root)
    monkeypatch.setattr(phase36_ledger, "LEDGER_PATH", "ledger/rig_ledger.jsonl")
    monkeypatch.setattr(phase36_ledger, "HEARTBEAT_PATH", root / "data" / "rig_heartbeat.jsonl")
    monkeypatch.setattr(phase42_recipes, "_tracked_and_clean", lambda *rels: False)
    phase42_recipes.record_rehearsal(
        root / phase42_recipes.REHEARSAL_IDENTITY, units=(), seconds=1.0
    )
    return calls, {"root": root, "device": "mps"}, root / "ledger" / "rig_ledger.jsonl"


def _events(ledger):
    import phase36_ledger

    return [(x["event"], x["run_id"], x["record"]) for x in phase36_ledger.read_ledger(ledger)]


def _plant(root, unlearnable=None):
    from test_phase42_prereg import _plant_controls

    p = phase42_prereg
    learnable = p.V4_CONTROL_COUNTS["taught"][0], p.V4_CONTROL_COUNTS["heldout"][0]
    _plant_controls(root, {u: (0, 0) if u == unlearnable else learnable for u in p.CONTROL_UNITS})


def test_preflight_stage_1_pending_controls(monkeypatch, tmp_path, capsys):
    calls, kw, _ledger = _run_rig(monkeypatch, tmp_path)
    pf = phase42_recipes.preflight(**kw)
    assert pf["stage"] == 1 and pf["pending"] == phase42_prereg.CONTROL_UNITS
    assert pf["p22"] is None and pf["real"] is False and pf["git_sha"] == "h1"
    assert capsys.readouterr().out.startswith("PREFLIGHT OK h1 device=cpu stage=1 pending=")
    assert calls["dirty"] == [] and calls["train"] == []  # scratch root: no dirty-tree gate
    with pytest.raises(SystemExit, match=r"^\[phase42_recipes\].*subset"):
        phase42_recipes.preflight(**kw, units=("point_lr3e-04_t200_sigma0p500000",))
    one = phase42_recipes.preflight(**kw, units=("control_lr1e-03_t800",))
    assert one["pending"] == ("control_lr1e-03_t800",)


def test_run_writes_one_start_and_one_end_per_unit(monkeypatch, tmp_path, capsys):
    p = phase42_prereg
    calls, kw, ledger = _run_rig(monkeypatch, tmp_path)
    out = phase42_recipes.run(**kw)
    assert out == {"stage": 1, "whole": list(p.CONTROL_UNITS)}
    expected = []
    for unit in p.CONTROL_UNITS:
        expected += [
            ("start", phase42_prereg.run_id(unit), None),
            ("end", phase42_prereg.run_id(unit), phase42_prereg.unit_record(unit)),
        ]
        assert (kw["root"] / phase42_prereg.unit_record(unit)).exists()
    assert _events(ledger) == expected
    assert phase42_recipes.STAGE_1_DONE in capsys.readouterr().out
    assert len(calls["train"]) == len(p.CONTROL_UNITS)
    # The scratch root is now at stage 2 (every control record exists under it).
    assert phase42_recipes.stage(kw["root"]) == 2


def test_real_root_second_run_is_a_no_op_and_excludes_its_own_records(
    monkeypatch, tmp_path, capsys
):
    p = phase42_prereg
    calls, kw, ledger = _run_rig(monkeypatch, tmp_path, real=True)
    out = phase42_recipes.run(**kw)
    assert out["whole"] == list(p.CONTROL_UNITS)
    first = _events(ledger)
    assert len(first) == 2 * len(p.CONTROL_UNITS)
    assert phase42_recipes.STAGE_1_DONE in capsys.readouterr().out
    assert calls["dirty"][0]["pathspec"] == phase42_recipes.LAUNCH_PATHSPEC
    record = json.loads((kw["root"] / p.unit_record(p.CONTROL_UNITS[0])).read_text("utf-8"))
    assert "rehearsal_disclosure" not in record
    assert record["provenance"]["run"]["device"] == "mps"
    # Second run: the threshold file is not tracked, so stage 1 with nothing pending.
    again = phase42_recipes.run(**kw)
    assert again == {"stage": 1, "whole": []}
    assert _events(ledger) == first and len(calls["train"]) == len(p.CONTROL_UNITS)
    assert phase42_recipes.STAGE_1_DONE in capsys.readouterr().out
    assert calls["dirty"][-1]["pathspec"] == phase42_recipes._launch_pathspec(kw["root"])
    assert calls["dirty"][-1]["pathspec"] != phase42_recipes.LAUNCH_PATHSPEC
    with pytest.raises(SystemExit, match=r"^\[phase42_recipes\].*rehearsal identity"):
        phase42_recipes.run(**kw, rehearsal_identity=tmp_path / "identity.json")


def test_stage_reads_the_threshold_file_and_the_controls_on_the_real_root(monkeypatch, tmp_path):
    p = phase42_prereg
    seen = []
    monkeypatch.setattr(phase42_recipes, "_ROOT", tmp_path)
    for tracked, expected in ((False, 1), (True, 2)):
        monkeypatch.setattr(
            phase42_recipes, "_tracked_and_clean", lambda *r, _t=tracked: seen.append(r) or _t
        )
        assert phase42_recipes.stage(tmp_path) == expected
    controls = tuple(p.unit_record(u) for u in p.CONTROL_UNITS)
    assert seen == [(phase42_recipes.THRESHOLD_FILE, *controls)] * 2
    # The real helper, on a tmp git repository: tracked and clean, untracked, modified.
    from test_phase41_erasure import _tmp_git

    monkeypatch.undo()
    repo = tmp_path / "git"
    git = _tmp_git(repo)
    (repo / "a.py").write_text("a = 1\n", encoding="utf-8")
    git("add", "a.py")
    git("commit", "-q", "-m", "a")
    (repo / "b.py").write_text("b = 1\n", encoding="utf-8")
    monkeypatch.setattr(phase42_recipes, "_REPO", repo)
    assert phase42_recipes._tracked_and_clean("a.py")
    assert not phase42_recipes._tracked_and_clean("a.py", "b.py")
    (repo / "a.py").write_text("a = 2\n", encoding="utf-8")
    assert not phase42_recipes._tracked_and_clean("a.py")


def test_stage_2_runs_p22_before_any_training(monkeypatch, tmp_path, capsys):
    p = phase42_prereg
    calls, kw, ledger = _run_rig(monkeypatch, tmp_path)
    _plant(kw["root"])
    pf = phase42_recipes.preflight(**kw)
    assert pf["stage"] == 2 and pf["p22"] == dict(p.P22_ONSETS)
    assert "p22=" in capsys.readouterr().out
    assert phase42_recipes.p22_check() == dict(p.P22_ONSETS)
    real = phase35_prereg.p22_onset_sigma
    monkeypatch.setattr(
        phase35_prereg,
        "p22_onset_sigma",
        lambda steps: max(p.NOISED_SIGMAS) if steps == p.T_MAX else real(steps),
    )
    with pytest.raises(SystemExit, match=r"^\[phase42_recipes\] P22"):
        phase42_recipes.run(**kw)
    assert calls["train"] == [] and _events(ledger) == []
    # Equal to the frozen onset yet crossing: a frozen onset can be checked only both ways.
    monkeypatch.setattr(p, "P22_ONSETS", {**p.P22_ONSETS, p.T_MAX: max(p.NOISED_SIGMAS)})
    with pytest.raises(SystemExit, match=r"^\[phase42_recipes\] P22: the grid crosses"):
        phase42_recipes.p22_check()


def test_refused_still_runs(monkeypatch, tmp_path):
    p = phase42_prereg
    calls, kw, ledger = _run_rig(monkeypatch, tmp_path)
    _plant(kw["root"], unlearnable="control_lr1e-03_t800")
    pf = phase42_recipes.preflight(**kw)
    assert pf["stage"] == 2 and pf["pending"] == p.POINT_UNITS  # D-20: all 8
    refused = [
        u for u in pf["pending"] if p.unit_cell(u)[0] == p.unit_cell("control_lr1e-03_t800")[0]
    ]
    assert len(refused) == len(p.NOISED_SIGMAS)
    out = phase42_recipes.run(**kw, units=tuple(refused))
    assert out == {"stage": 2, "whole": refused}
    assert [e for e, _r, _x in _events(ledger)] == ["start", "end"] * len(refused)


def test_launch_refuses_without_require_launch(monkeypatch, tmp_path):
    import phase36_ledger

    calls, kw, ledger = _run_rig(monkeypatch, tmp_path)
    real = phase36_ledger.require_launch

    def refuse(front, **k):
        raise SystemExit("[phase36_ledger] PAUSE (planted)")

    monkeypatch.setattr(phase36_ledger, "require_launch", refuse)
    with pytest.raises(SystemExit, match="PAUSE"):
        phase42_recipes.run(**kw)
    assert _events(ledger) == [] and calls["train"] == []
    # The per-unit gate: preflight's call passes, the one before the first start line refuses.
    seen = []

    def second_refuses(front, **k):
        seen.append(front)
        if len(seen) > 1:
            raise SystemExit("[phase36_ledger] PAUSE (planted, per unit)")
        return real(front, **k)

    monkeypatch.setattr(phase36_ledger, "require_launch", second_refuses)
    with pytest.raises(SystemExit, match="per unit"):
        phase42_recipes.run(**kw)
    assert seen == ["E3", "E3"] and _events(ledger) == [] and calls["train"] == []


def test_open_run_and_stale_outputs_are_refused(monkeypatch, tmp_path):
    import phase36_ledger

    p = phase42_prereg
    calls, kw, ledger = _run_rig(monkeypatch, tmp_path)
    unit = p.CONTROL_UNITS[0]
    rid = phase42_prereg.run_id(unit)
    phase36_ledger.append("start", run_id=rid, phase=42, front="E3", ledger_path=ledger)
    with pytest.raises(SystemExit, match=r"^\[phase42_recipes\].*reconcile"):
        phase42_recipes.preflight(**kw)
    # An open attempt whose record exists gets its end line by command, never a reconcile.
    record = kw["root"] / phase42_prereg.unit_record(unit)
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match=r"^\[phase42_recipes\].*NEVER reconcile"):
        phase42_recipes.preflight(**kw)
    record.unlink()
    phase36_ledger.append(
        "lost",
        run_id=rid,
        phase=42,
        front="E3",
        seconds=0.0,
        flag=phase36_ledger.NO_BEAT_FLAG,
        ledger_path=ledger,
    )
    # A stale sidecar of a pending unit with no lost line is refused ...
    other = p.CONTROL_UNITS[1]
    sidecar = phase25_points.training_sidecar(
        phase42_recipes.cell_plan(other, rehearsal=True)["point_key"]
    )
    sidecar.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match=r"^\[phase42_recipes\].*exists"):
        phase42_recipes.preflight(**kw)
    sidecar.unlink()
    # ... and the same output of the unit with a lost attempt is accepted (crash_rule resume).
    phase25_points.training_sidecar(
        phase42_recipes.cell_plan(unit, rehearsal=True)["point_key"]
    ).write_text("{}", encoding="utf-8")
    assert phase42_recipes.preflight(**kw)["pending"] == p.CONTROL_UNITS
    assert calls["train"] == []


def test_relaunch_pathspec_excludes_only_whole_unit_records(monkeypatch, tmp_path):
    from personacore.provenance import refuse_if_dirty
    from test_phase41_erasure import _tmp_git

    p = phase42_prereg
    repo = tmp_path / "git"
    git = _tmp_git(repo)
    (repo / "scripts").mkdir()
    (repo / "scripts" / "kept.py").write_text("x = 1\n", encoding="utf-8")
    git("add", "scripts/kept.py")
    git("commit", "-q", "-m", "one file")
    assert phase42_recipes._launch_pathspec(repo) == phase42_recipes.LAUNCH_PATHSPEC
    whole = repo / p.unit_record("control_lr1e-03_t200")
    whole.parent.mkdir(parents=True)
    whole.write_text("{}", encoding="utf-8")
    spec = phase42_recipes._launch_pathspec(repo)
    assert spec == phase42_recipes.LAUNCH_PATHSPEC + (
        ":(exclude)" + p.unit_record("control_lr1e-03_t200"),
    )
    refuse_if_dirty(who="t", detail="t", pathspec=spec, cwd=repo)
    # NON-VACUITY (natural RED): the bare launch pathspec sees the untracked record.
    with pytest.raises(SystemExit, match="dirty"):
        refuse_if_dirty(who="t", detail="t", pathspec=phase42_recipes.LAUNCH_PATHSPEC, cwd=repo)
    stray = repo / "results" / "stray.json"
    stray.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="dirty"):
        refuse_if_dirty(
            who="t", detail="t", pathspec=phase42_recipes._launch_pathspec(repo), cwd=repo
        )
    stray.unlink()

    # Preflight on a real root hands exactly that pathspec to the dirty-tree gate.
    class Sentinel(Exception):
        pass

    captured = []

    def capture(**kw):
        captured.append(kw)
        raise Sentinel

    monkeypatch.setattr(phase42_recipes, "_ROOT", repo)
    monkeypatch.setattr(phase42_recipes, "_launch_requirements", lambda **kw: None)
    monkeypatch.setattr(phase42_recipes, "refuse_if_dirty", capture)
    with pytest.raises(Sentinel):
        phase42_recipes.preflight(root=repo, device="mps")
    assert [kw["pathspec"] for kw in captured] == [phase42_recipes._launch_pathspec(repo)]
    assert captured[0]["cwd"] == phase42_recipes._REPO


def test_real_root_launch_requirements(tmp_path, monkeypatch):
    monkeypatch.setattr(phase42_recipes, "git_sha", lambda: "h1")
    digests = phase42_recipes._disclosed_digests()
    path = tmp_path / "identity.json"
    identity = phase42_recipes.record_rehearsal(path, units=(), seconds=1.0)
    req = phase42_recipes._launch_requirements
    req(real=True, device="mps", identity=identity, digests=digests)
    req(real=False, device="cpu", identity=None, digests=digests)
    for kwargs, match in (
        ({"real": True, "device": "cpu", "identity": identity}, "MPS"),
        ({"real": True, "device": "mps", "identity": None}, "missing"),
        ({"real": True, "device": "mps", "identity": {**identity, "units": "x"}}, "malformed"),
        (
            {
                "real": True,
                "device": "mps",
                "identity": {**identity, "module_sha256": dict(digests, **{"x": "y"})},
            },
            "malformed",
        ),
        (
            {
                "real": True,
                "device": "mps",
                "identity": {
                    **identity,
                    "module_sha256": dict(digests, **{phase42_recipes.DRIVER_FILE: "0" * 64}),
                },
            },
            "changed after the rehearsal",
        ),
        ({"real": False, "device": "mps", "identity": None}, "CPU"),
    ):
        with pytest.raises(SystemExit, match=r"^\[phase42_recipes\].*" + match):
            req(**kwargs, digests=digests)


def test_record_rehearsal(tmp_path, monkeypatch):
    p = phase42_prereg
    monkeypatch.setattr(phase42_recipes, "git_sha", lambda: "h1")
    path = tmp_path / "data" / "identity.json"
    first = phase42_recipes.record_rehearsal(path, units=("control_lr1e-03_t200",), seconds=2.0)
    stored = json.loads(path.read_text(encoding="utf-8"))
    assert stored == first
    assert set(stored) == {"git_sha", "module_sha256", "units", "started_utc", "cpu_seconds"}
    assert stored["git_sha"] == "h1" and stored["cpu_seconds"] == 2.0
    assert stored["module_sha256"] == {
        rel: phase42_recipes._sha256(_ROOT / rel) for rel in phase42_recipes.DISCLOSED_MODULES
    }
    assert stored["units"] == ["control_lr1e-03_t200"]
    # A later call at the same digests appends its units (UNITS order) and its seconds.
    monkeypatch.setattr(phase42_recipes, "git_sha", lambda: "h2")
    second = phase42_recipes.record_rehearsal(
        path, units=(p.CONTROL_UNITS[0], "control_lr1e-03_t200"), seconds=3.0
    )
    assert second["units"] == [p.CONTROL_UNITS[0], "control_lr1e-03_t200"]
    assert second["git_sha"] == "h1" and second["started_utc"] == first["started_utc"]
    assert second["cpu_seconds"] == 5.0
    assert phase42_recipes._load(path) == second
    # Recorded at other digests: refused, the file untouched.
    stored = dict(second, module_sha256=dict(second["module_sha256"]))
    stored["module_sha256"][phase42_recipes.PREREG_FILE] = "0" * 64
    path.write_text(json.dumps(stored), encoding="utf-8")
    before = path.read_bytes()
    with pytest.raises(SystemExit, match=r"^\[phase42_recipes\].*move the old identity aside"):
        phase42_recipes.record_rehearsal(path, units=(), seconds=1.0)
    assert path.read_bytes() == before
    path.write_text(json.dumps({"git_sha": "h1"}), encoding="utf-8")
    with pytest.raises(SystemExit, match=r"^\[phase42_recipes\].*malformed"):
        phase42_recipes._kept_identity(path)
    assert phase42_recipes._kept_identity(tmp_path / "absent.json") is None
