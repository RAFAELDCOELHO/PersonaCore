"""Plan 30-03: the ARECIPE-02 calibration emitter (D-05..D-11).

CPU-only. Nothing here writes under results/ or data/: bins land in a tempdir inside derive(), and
every emitted record lands under tmp_path. A results/phase3* file would start the phase29 ancestry
clock.
"""

import ast
import copy
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

import phase24_adversarial  # noqa: E402  (scripts/ is not a package)
import phase29_prereg  # noqa: E402  (same)
import phase30_calibration as cal  # noqa: E402  (same)
import phase30_points as pts  # noqa: E402  (same)

from test_phase29_prereg import _assert_frozen_before, _git  # noqa: E402
from test_phase30_points import _commit  # noqa: E402

EMITTER = "scripts/phase30_calibration.py"


def _tp():
    import teach_persona  # torch at import — inside tests only

    return teach_persona


def _data_snapshot():
    """data/ is gitignored, so git status cannot see a stray bin there: list it with mtimes."""
    return sorted((str(p), p.stat().st_mtime_ns) for p in (_ROOT / "data").rglob("*"))


def _results_status():
    return _git("status", "--porcelain", "--untracked-files=all", "results")


@pytest.fixture(autouse=True)
def clean_tree(monkeypatch):
    """emit() refuses a dirty tree, and this suite runs on dirty trees, so the guard is RECORDED
    (the tests/test_phase27_relearn.py idiom)."""
    calls = []
    monkeypatch.setattr(cal, "refuse_if_dirty", lambda **kw: calls.append(kw) or "")
    return calls


@pytest.fixture(scope="module")
def derived():
    return cal.derive()


# =================================================================================================
# Task 1: the live derivation, D-08, the recipe round-trip, the descriptive mix, write-once
# =================================================================================================


def test_derivation_reproduces_the_imported_floor(derived):
    tp = _tp()
    d = derived
    assert d["derived_floor"] == phase24_adversarial.MIN_REFUSAL_SCORED_TOKENS
    assert all(type(v) is int and v > 0 for v in d["inputs"].values()), d["inputs"]
    assert len(d["inputs"]) == len(
        ("clean_scored_tokens", "clean_tokens", "attack_pool_episodes", "pool_prompt_tokens")
    )
    assert d["frac_at_floor"] >= d["target"] > d["frac_below_floor"]
    assert d["target"] == tp.MASK_FRACTION_BAND[0] + phase24_adversarial.MASK_FRACTION_MARGIN
    assert d["corners"] == [phase29_prereg.RATIO_GRID[0], phase29_prereg.RATIO_GRID[-1]]
    assert d["bins_identical_advr_vs_adv"] is True
    pairs = [
        (arm, corner, kind)
        for arm, corners in d["bins"].items()
        for corner, shas in corners.items()
        for kind in shas
    ]
    assert len(pairs) == len(d["bins"]) * len(d["corners"]) * len(("bin", "mask"))
    (advr, twin) = d["bins"]
    assert d["bins"][advr] == d["bins"][twin]


def _plant_arm_spec(monkeypatch, *, second_person, replay_ratio):
    tp = _tp()
    real = tp.arm_spec
    advr = phase29_prereg.ADVR_ARMS[0]
    twin = advr.replace("advr_", "adv_", 1)

    def planted(arm):
        if arm == advr:
            return real(twin)[0], second_person, replay_ratio
        return real(arm)

    monkeypatch.setattr(tp, "arm_spec", planted)


def test_derivation_refuses_a_replay_entering_the_bin(derived, monkeypatch):
    # The planted change must be the ONLY difference between the two arms.
    specs = derived["arm_spec"]
    assert len(specs) == len(("advr", "adv"))
    for spec in specs.values():
        assert spec["second_person"] is False and spec["replay_ratio"] == 0.0, specs

    results_before, data_before = _results_status(), _data_snapshot()

    # Case A — host-independent: a second-person advr bin differs at both corners.
    _plant_arm_spec(monkeypatch, second_person=True, replay_ratio=0.0)
    with pytest.raises(SystemExit, match="structural reason"):
        cal.derive()

    # Case B — replay put into the bin: WR-04 at the hi corner, the missing-source refusal on CI,
    # or derive()'s own bin-mismatch refusal. Any of them: replay cannot enter the bin silently.
    _plant_arm_spec(monkeypatch, second_person=False, replay_ratio=0.5)
    with pytest.raises(SystemExit):
        cal.derive()

    assert _results_status() == results_before
    assert _data_snapshot() == data_before


def test_derivation_refuses_if_not_15(derived, monkeypatch, tmp_path):
    bump = 0.01
    i = derived["inputs"]

    def floor(margin):
        target = _tp().MASK_FRACTION_BAND[0] + margin
        L = 1
        while (i["clean_scored_tokens"] + i["attack_pool_episodes"] * L) / (
            i["clean_tokens"] + i["pool_prompt_tokens"] + i["attack_pool_episodes"] * L
        ) < target:
            L += 1
        return L

    margin = phase24_adversarial.MASK_FRACTION_MARGIN
    assert floor(margin) == derived["derived_floor"]
    assert floor(margin + bump) != derived["derived_floor"]  # the bump really moves L

    monkeypatch.setattr(phase24_adversarial, "MASK_FRACTION_MARGIN", margin + bump)
    with pytest.raises(SystemExit, match="D-08"):
        cal.derive()
    out = tmp_path / "c.json"
    with pytest.raises(SystemExit, match="D-08"):
        cal.emit(out)
    assert not out.exists()


def test_review_wr01_derive_reproduces_build_arm_bins_real_output(tmp_path, monkeypatch):
    """DATED CONTINUATION, 2026-09-25 (review WR-01, developer ruling "Fix CR-01 + WR now").

    The write-once record's byte-identity evidence (1) fed equal inputs to a hand-copied
    ``build_bins`` call and never ran ``build_arm_bins``. The record is not edited; this test
    closes the gap. It drives the REAL path (``train_arm`` -> ``build_arm_bins``, ``train()``
    spied out) for the advr arm and its adv twin at the grid's top ratio, then asserts:
    (a) the bins that path actually writes are byte-identical between the two arms, and
    (b) ``derive()``'s ``build_bins`` call at that corner has the same episodes and keyword
    arguments as ``build_arm_bins``' real call and writes the same bytes, so the hand copy
    cannot drift from the real call without this going red."""
    import test_phase30_seam as seam

    tp = _tp()
    hi = phase29_prereg.RATIO_GRID[-1]
    advr = phase29_prereg.ADVR_ARMS[0]
    twin = advr.replace("advr_", "adv_", 1)
    real = tp.build_bins
    calls = []

    def spy(tok, episodes, bin_path, mask_path, **kwargs):
        stats = real(tok, episodes, bin_path, mask_path, **kwargs)
        calls.append(
            {
                "episodes": episodes,
                "kwargs": kwargs,
                "bytes": (cal._sha256(bin_path), cal._sha256(mask_path)),
            }
        )
        return stats

    monkeypatch.setattr(tp, "build_bins", spy)
    cal.derive()
    # derive's order: for arm in (advr, twin), for ratio in (lo, hi).
    derived = {advr: calls[1], twin: calls[3]}
    assert [c["kwargs"]["adversarial_ratio"] for c in calls] == [
        phase29_prereg.RATIO_GRID[0],
        hi,
    ] * len(derived)

    written = {}
    for arm in (advr, twin):
        calls.clear()
        seam._capture(arm, tmp_path / arm, monkeypatch)
        (written[arm],) = calls
        assert written[arm]["kwargs"]["adversarial_ratio"] is hi
    assert written[advr]["bytes"] == written[twin]["bytes"]
    for arm in (advr, twin):
        assert derived[arm]["kwargs"] == written[arm]["kwargs"], arm
        assert derived[arm]["episodes"] == written[arm]["episodes"], arm
        assert derived[arm]["bytes"] == written[arm]["bytes"], arm


@pytest.fixture(scope="module")
def record():
    return cal.build_record()


def test_recipe_mismatch_round_trips_through_the_scoring_refusal(record, tmp_path, monkeypatch):
    monkeypatch.setattr(pts, "_ROOT", tmp_path)
    path = tmp_path / pts.CALIBRATION_PATH
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(record), encoding="utf-8")
    _commit(tmp_path)  # CR-01: the reader reads the committed blob
    tracked = [pts.CALIBRATION_PATH]
    for leg in phase29_prereg.LEGS:
        recipe = pts.recipe_identity(leg)
        assert record["recipe"][leg] == recipe
        assert pts.require_calibrated_recipe(leg, recipe, tracked) == recipe
        for field in sorted(pts.RECIPE_FIELDS):
            bad = copy.deepcopy(recipe)
            bad[field] = bad[field] + ["x"] if isinstance(bad[field], list) else bad[field] + 1
            with pytest.raises(SystemExit):
                pts.require_calibrated_recipe(leg, bad, tracked)


def test_descriptive_mix_is_recorded_and_read_by_nothing(record):
    tp = _tp()
    mix = record["descriptive_step_mix"]
    assert mix["gates_nothing"] is True
    for leg in phase29_prereg.LEGS:
        n = int(leg.removeprefix("n"))
        row = mix[leg]
        assert row["teaching_windows"] == tp.BATCH_SIZE
        assert row["replay_windows"] == phase29_prereg.replay_windows(n)
        assert row["teaching_tokens"] == tp.BATCH_SIZE * tp.BLOCK_SIZE
        assert row["replay_tokens"] == phase29_prereg.replay_windows(n) * tp.BLOCK_SIZE
    readers = sorted(
        path.name
        for path in _SCRIPTS.glob("*.py")
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Constant) and node.value == "descriptive_step_mix"
    )
    assert set(readers) == {"phase30_calibration.py"}, readers


def test_emit_is_write_once(tmp_path):
    if cal.RECORD.exists():
        before = cal.RECORD.read_bytes()
        with pytest.raises(SystemExit, match="REFUSING to overwrite"):
            cal.emit()
        assert cal.RECORD.read_bytes() == before
    else:
        assert not _git("ls-files", pts.CALIBRATION_PATH).strip(), (
            f"{pts.CALIBRATION_PATH} is tracked but absent on disk"
        )
        out = tmp_path / "c.json"
        blob = cal.emit(out)
        before = out.read_bytes()
        assert json.loads(before) == json.loads(json.dumps(blob))
        assert set(blob["provenance"]["module_sha256"]) == set(cal.PINNED_MODULES)
        with pytest.raises(SystemExit, match="REFUSING to overwrite"):
            cal.emit(out)
        assert out.read_bytes() == before


def test_emit_refuses_a_dirty_tree_before_measuring(monkeypatch, clean_tree):
    monkeypatch.setattr(cal, "derive", lambda: pytest.fail("emit measured before the dirty check"))

    def stop():
        raise SystemExit("[probe] stopped after the dirty check")

    monkeypatch.setattr(cal, "build_record", stop)
    rel = "results/phase30_probe_never_written.json"
    inside = _ROOT / rel
    with pytest.raises(SystemExit, match="stopped after the dirty check"):
        cal.emit(inside)
    assert not inside.exists()
    (call,) = clean_tree
    assert call["who"] == "phase30_calibration"
    assert call["cwd"] == _ROOT
    assert call["pathspec"] == ("scripts", "src", "results", f":(exclude){rel}")


# =================================================================================================
# Task 2: D-11 ancestry and the emitter freeze
# =================================================================================================


def _v5_tracked():
    return sorted(
        {
            path
            for spec in phase29_prereg.ARTIFACT_PATHSPECS
            for path in _git("ls-files", spec).split()
        }
    )


def test_ancestry_calibration_precedes_every_later_v5_result():
    """D-11: the calibration's commits strictly precede the first add of every other v5.0 result."""
    cal_rel = pts.CALIBRATION_PATH
    tracked = _v5_tracked()
    later = [p for p in tracked if p != cal_rel]
    if cal_rel not in tracked:
        assert later == [], (
            f"v5.0 result(s) {later} committed before the ARECIPE-02 calibration {cal_rel} (D-11)"
        )
        return
    _assert_frozen_before(cal_rel, later)
    # NON-VACUITY (natural RED): a v4.0 result that predates the calibration must fire.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(cal_rel, ["results/phase25_frontier.json"])


def test_ancestry_emitter_is_frozen_before_the_calibration():
    """The emitter is frozen before its record. scripts/phase30_points.py is deliberately NOT
    frozen (developer ruling 2026-09-25): the driver keeps evolving through Phases 31-34."""
    cal_rel = pts.CALIBRATION_PATH
    if cal_rel in _v5_tracked():
        _assert_frozen_before(EMITTER, [cal_rel])
    else:
        _assert_frozen_before(EMITTER, [])  # proves the emitter has commits; honest-green
    # NON-VACUITY (natural RED): scripts/phase29_prereg.py was first added before the emitter
    # existed, so the emitter's commits cannot all precede it.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(EMITTER, ["scripts/phase29_prereg.py"])
