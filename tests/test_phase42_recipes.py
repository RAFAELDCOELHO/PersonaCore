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
