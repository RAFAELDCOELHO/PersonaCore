"""Plan 32-05 (D-12): the v5.0 sweep's LIVE path, end to end, at CPU fixture scale.

The real driver runs through ``phase32_points.main(["run", ...])`` over the whole
``SWEEP_SCHEDULE()`` into a scratch results repository: real train_stage (replay counted per step
through on_draw), real measure_stage with recall, real draws, real score, write and one-path
commit. The ONE forced reading is the advr_n8 control's taught/held-out counts (k = n // 2, after a
REAL score_arm run), so the n8 leg trains and the n64 leg is REFUSED under PREREG-03 by the real
path. The committed producer records are then fed to ``phase32_frontier.build_frontier`` and
``phase29_prereg.admission`` (the Phase 25 lesson: 25-14 / 25-18).

Nothing here writes under the real results/, data/, checkpoints/ or logs/: a before/after
``Path.glob`` snapshot of the real root proves it.
"""

import copy
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

import mitigation_budget  # noqa: E402  (scripts/ is not a package)
import phase25_condition_c  # noqa: E402  (same)
import phase25_points  # noqa: E402  (same)
import phase25_run  # noqa: E402  (same)
import phase25_verdict  # noqa: E402  (same)
import phase29_prereg  # noqa: E402  (same)
import phase30_points  # noqa: E402  (same)
import phase32_frontier  # noqa: E402  (same)
import phase32_points as p32  # noqa: E402  (same)

from test_phase25_driver import _scratch_repo  # noqa: E402
from test_phase31_probe import _one_prompt_per_cell  # noqa: E402

KEYS = phase29_prereg.POINT_KEYS()
N8C = phase29_prereg.control_key("n8")
N64C = phase29_prereg.control_key("n64")
FORGED_STOP_LINE = 1e9  # finite and far above any fixture clock (stop_line_seconds refuses inf)

_STRAY_GLOBS = (
    "data/phase32_*",
    "data/phase25_advr_*",
    "checkpoints/phase32_*",
    "results/phase32_*",
    "logs/phase32_*",
)


def _tp():
    import teach_persona  # torch at import — inside tests only

    return teach_persona


@pytest.fixture(autouse=True)
def clean_tree(monkeypatch):
    """Both emitters refuse a dirty tree and this suite runs on dirty trees: RECORDED."""
    calls = []
    monkeypatch.setattr(p32, "refuse_if_dirty", lambda **kw: calls.append(kw) or "")
    monkeypatch.setattr(phase32_frontier, "refuse_if_dirty", lambda **kw: calls.append(kw) or "")
    return calls


def _real_strays():
    """Every phase32 write target in the REAL tree (this module's _ROOT, never patched)."""
    return sorted(
        {p.relative_to(_ROOT).as_posix() for pattern in _STRAY_GLOBS for p in _ROOT.glob(pattern)}
    )


def _git(root, *argv):
    return subprocess.run(
        ["git", *argv], cwd=root, capture_output=True, text=True, check=True
    ).stdout


def _patch_env(root, monkeypatch):
    """The fixture patch set: ONE scratch root for every patchable root; _CODE_ROOT untouched."""
    import phase14_recall
    import phase18_extraction as x18
    import phase19_erasure

    from personacore.checkpoint import export_slim
    from test_phase22_wiring import _e2e_env

    tp = _tp()
    monkeypatch.setattr(phase25_run, "_DEVICE", "cpu")
    _e2e_env(root, monkeypatch)
    slim = root / "convbase_slim.pt"
    export_slim(root / "convbase.pt", slim)
    monkeypatch.setattr(phase14_recall, "CONVBASE_SLIM", slim)
    monkeypatch.setattr(phase14_recall, "RECALL_MAX_NEW_TOKENS", 4)
    monkeypatch.setattr(phase25_run, "DRAWS_DIR", root / "data")
    monkeypatch.setattr(phase19_erasure, "RETENTION_BIN", tp.DIALOG_VAL_BIN)
    subset = _one_prompt_per_cell(json.loads(x18.CORPUS_PATH.read_text(encoding="utf-8")))
    monkeypatch.setattr(
        phase25_points, "attack_corpus", lambda: (subset, x18.corpus_sha256(subset))
    )
    # RESEARCH A1: recipe_identity, pinned_mechanism and own_control read it at call time.
    monkeypatch.setattr(mitigation_budget, "STEP_BUDGET", tp.MAX_STEPS)
    for module in (phase25_points, phase30_points, p32):
        monkeypatch.setattr(module, "_ROOT", root)
    monkeypatch.setattr(p32, "_GIT_ROOT", root)
    monkeypatch.setattr(phase32_frontier, "_GIT_ROOT", root)
    return tp


def _sweep_fixture(root):
    """ONE run of the real driver through main(). Every patch is undone on return."""
    import phase14_recall

    strays_before = _real_strays()
    heartbeat = root / "heartbeat.jsonl"
    forced, forced_gap, scored_calls, dirty_calls = [], [], [], []
    with pytest.MonkeyPatch.context() as monkeypatch:
        tp = _patch_env(root, monkeypatch)
        monkeypatch.setattr(p32, "refuse_if_dirty", lambda **kw: dirty_calls.append(kw) or "")
        # The scratch results repo: the calibration (computed under the patches) and the budget.
        blobs = {
            phase30_points.CALIBRATION_PATH: {
                "recipe": {leg: phase30_points.recipe_identity(leg) for leg in phase29_prereg.LEGS}
            },
            p32.BUDGET_PATH: {"stop_line": {"seconds": FORGED_STOP_LINE}},
        }
        for rel, blob in blobs.items():
            (root / rel).write_text(json.dumps(blob), encoding="utf-8")
            _git(root, "add", "--", rel)
        _git(root, "commit", "-q", "-m", "fixture: calibration + budget")

        control = phase30_points.point_plan(N8C)
        real_score = tp.score_arm

        def score_spy(arm, facts, adapter_path, device):
            result = real_score(arm, facts, adapter_path, device)
            name = pathlib.Path(adapter_path).name
            scored_calls.append((arm, name))
            # Computed at call time, so the fixture's root patches apply. Exact file name, never
            # the prefix: both controls share prefix phase32_ratio0p000000.
            wanted = tp.arm_outputs(control["arm"], prefix=control["prefix"])["adapter"].name
            if arm != control["arm"] or name != wanted:
                return result
            forced.append((arm, name))
            result = dict(result)
            for tier in ("on_taught", "on_heldout"):
                block = dict(result[tier])
                block["k"] = block["n"] // 2
                block["rate"] = block["k"] / block["n"]
                result[tier] = block
            return result

        monkeypatch.setattr(tp, "score_arm", score_spy)

        # THE SECOND FORCED READING, measured necessary (see the frontier natural-RED test): at
        # fixture scale the random-init base makes any adapter LOWER the dialogue perplexity, so
        # the n8 control's real adapter_on - adapter_off is negative and the frozen route's
        # dialogue_gap_band raises ValueError. Scoped like the recall forcing: the n8 control's
        # adapter by exact file name, identified from the load that precedes the reading.
        # adapter_off (the base model) stays real; adapter_on becomes off + |real gap|.
        loaded = []
        real_load = phase14_recall.load_adapted_model
        real_condition_c = phase25_condition_c.measure_condition_c

        def load_spy(device, adapter_path=None):
            loaded.append(None if adapter_path is None else pathlib.Path(adapter_path).name)
            return real_load(device, adapter_path)

        def condition_c_spy(*args, **kwargs):
            result = real_condition_c(*args, **kwargs)
            wanted = tp.arm_outputs(control["arm"], prefix=control["prefix"])["adapter"].name
            if loaded[-1] != wanted:
                return result
            gap = result["adapter_on"] - result["adapter_off"]
            forced_gap.append((loaded[-1], gap))
            return dict(result, adapter_on=result["adapter_off"] + abs(gap))

        monkeypatch.setattr(phase14_recall, "load_adapted_model", load_spy)
        monkeypatch.setattr(phase25_condition_c, "measure_condition_c", condition_c_spy)
        fixture_steps = tp.MAX_STEPS
        exit_code = p32.main(["run", "--heartbeat", str(heartbeat)])
        tracked = p32.tracked_results()
        cumulative = p32.cumulative_seconds(tracked)
        n_seeded = phase14_recall.N_SEEDED_SAMPLES
    shas = _git(root, "log", "--format=%H").split()
    records = {
        k: json.loads(_git(root, "show", f"HEAD:{phase29_prereg.point_record_path(k)}"))
        for k in KEYS
    }
    calibration = json.loads(_git(root, "show", f"HEAD:{phase30_points.CALIBRATION_PATH}"))
    return {
        "root": root,
        "exit_code": exit_code,
        "records": records,
        "tracked": tracked,
        "calibration": calibration,
        # Oldest first.
        "commits": [
            (sha, _git(root, "show", "--name-only", "--format=", sha).split())
            for sha in reversed(shas)
        ],
        "forced": forced,
        "forced_gap": forced_gap,
        "scored_calls": scored_calls,
        "fixture_max_steps": fixture_steps,
        "n_seeded": n_seeded,
        "heartbeat": heartbeat.read_text(encoding="utf-8").splitlines(),
        "strays": (strays_before, _real_strays()),
        "cumulative_seconds": cumulative,
        "dirty_calls": dirty_calls,
        "control_plan": control,
    }


@pytest.fixture(scope="module")
def sweep_run(tmp_path_factory):
    """ONE CPU live-path sweep per module."""
    return _sweep_fixture(_scratch_repo(tmp_path_factory.mktemp("sweep32")))


def _trained(records):
    return {k: r for k, r in records.items() if r.get("rule") != "PREREG-03"}


def _leg(leg):
    return phase29_prereg.leg_keys(leg)


def _counts(record):
    return {
        tier: [record[f"{tier}_recall"]["numerator"], record[f"{tier}_recall"]["denominator"]]
        for tier in ("taught", "heldout")
    }


# =================================================================================================
# Task 1 — the producer half
# =================================================================================================


def test_live_path_sweep_writes_and_commits_all_twelve(sweep_run):
    ev = sweep_run
    assert ev["exit_code"] == 0
    rels = [phase29_prereg.point_record_path(k) for k in KEYS]
    assert set(rels) <= set(ev["tracked"])
    record_commits = [names for _sha, names in ev["commits"] if set(names) & set(rels)]
    assert all(len(names) == 1 for names in record_commits), record_commits
    assert sorted(n[0] for n in record_commits) == sorted(rels)
    order = [n[0] for n in record_commits]
    assert order[:2] == [phase29_prereg.point_record_path(k) for k in (N8C, N64C)]  # D-17

    records = ev["records"]
    trained = _trained(records)
    assert set(trained) == set(_leg("n8")) | {N64C}
    assert all(isinstance(trained[k].get("stages"), dict) for k in trained)
    n64_counts = _counts(records[N64C])
    for key in _leg("n64"):
        if key == N64C:
            continue
        assert records[key]["rule"] == "PREREG-03"
        assert records[key]["control_key"] == N64C
        assert records[key]["control_recall_counts"] == n64_counts


def test_live_path_every_trained_record_carries_its_own_recall(sweep_run):
    ev = sweep_run
    for key, record in _trained(ev["records"]).items():
        for field in ("taught_recall", "heldout_recall"):
            tier = record[field]
            assert type(tier["numerator"]) is int and type(tier["denominator"]) is int, key
            assert tier["draws_per_question"] == 1 + ev["n_seeded"], key
        assert record["stages"]["recall"]["seconds"] is not None, key
    tp = _tp()
    c = ev["control_plan"]
    # arm_outputs' file name does not depend on the root, so it is read unpatched here.
    expected = (c["arm"], tp.arm_outputs(c["arm"], prefix=c["prefix"])["adapter"].name)
    assert ev["forced"] == [expected]
    # The dialogue-pair forcing hit the same adapter once, and only because the real gap was
    # non-positive (the premise that made it necessary, re-measured on every run).
    ((name, gap),) = ev["forced_gap"]
    assert name == expected[1] and gap <= 0
    assert len(ev["scored_calls"]) == 7
    # The forced reading is what the n8 control record carries; the n64 control stayed natural.
    for field in ("taught_recall", "heldout_recall"):
        tier = ev["records"][N8C][field]
        assert tier["numerator"] == tier["denominator"] // 2
    assert phase29_prereg.control_is_unlearnable(*sum(_counts(ev["records"][N64C]).values(), []))


def test_live_path_replay_counted_per_step(sweep_run):
    ev = sweep_run
    steps = ev["fixture_max_steps"]
    assert steps != 200  # the fixture's MAX_STEPS, not the real module's
    for key, record in _trained(ev["records"]).items():
        leg = phase30_points.leg_of(key)
        expected = ev["calibration"]["recipe"][leg]["replay_windows"]
        assert expected == phase29_prereg.replay_windows(int(leg.removeprefix("n")))
        assert record["replay"]["per_step"] == [expected] * steps, key
        assert record["training"]["train_config"]["max_steps"] == steps, key


def test_live_path_own_control_and_actrl01_evidence(sweep_run):
    ev = sweep_run
    records = ev["records"]
    control = records[N8C]
    cc = control["condition_c"]
    pair = {"adapter_on": cc["point_dialogue_ppl_on"], "adapter_off": cc["point_dialogue_ppl_off"]}
    # D-18 self-reference: the control's gap is its own.
    assert cc["control_gap"] == cc["point_dialogue_ppl_on"] - cc["point_dialogue_ppl_off"]
    with pytest.MonkeyPatch.context() as monkeypatch:
        _patch_env(ev["root"], monkeypatch)
        tracked = p32.tracked_results()
        recipe = phase30_points.recipe_identity("n8")
        for key in _leg("n8"):
            if key == N8C:
                continue
            accepted = phase30_points.own_control(key, tracked, point_recipe=recipe)
            assert accepted == control, key
            gap = records[key]["condition_c"]["control_gap"]
            assert gap == phase25_condition_c.control_gap_for_capacity(pair), key


def test_live_path_stage_clock_recomputes(sweep_run):
    ev = sweep_run
    independent = 0.0
    for key, record in ev["records"].items():
        if record.get("rule") == "PREREG-03":
            assert "stages" not in record, key  # contributes 0
            continue
        independent += sum(float(s["seconds"]) for s in record["stages"].values())
    assert ev["cumulative_seconds"] == independent
    assert independent > 0


def test_live_path_heartbeat_and_strays(sweep_run):
    ev = sweep_run
    assert json.loads(ev["heartbeat"][-1])["stage"] == "done"
    before, after = ev["strays"]
    assert before == after
    assert not list((ev["root"] / "results").glob("phase32_ratio*_advr_*"))
    # The dirty-tree refusal was reached (recorded, not bypassed): run() plus one per write.
    assert len(ev["dirty_calls"]) == 1 + 7


def test_live_path_provenance(sweep_run):
    ev = sweep_run
    for key, record in _trained(ev["records"]).items():
        prov = record["provenance"]
        assert set(prov["module_sha256"]) == set(p32.PINNED_MODULES), key
        assert prov["sessions"], key
        assert prov["stop_line"]["seconds"] == FORGED_STOP_LINE, key
        assert prov["stop_line"]["past_line_ruling"] is None, key
        assert prov["device"] == "cpu", key
        assert isinstance(record["adapter_sha256"], str) and len(record["adapter_sha256"]) == 64
        assert set(record["stages"]) == set(p32.STAGES), key
        assert all(isinstance(s["seconds"], float) for s in record["stages"].values()), key


# =================================================================================================
# Task 2 — the consumer half: real producer records into the frontier and admission()
# =================================================================================================


def _v4():
    blob = subprocess.run(
        ["git", "show", f"HEAD:{phase32_frontier.V4_FRONTIER_PATH}"],
        cwd=_ROOT,
        capture_output=True,
        check=True,
    ).stdout
    return json.loads(blob), hashlib.sha256(blob).hexdigest()


def _questions(record):
    """``point_extraction_questions`` as ``phase25_promotion.flat_record`` computes it."""
    return sum(v["questions"] for v in record["per_family_counts"].values())


def _fixture_scale_anchors(monkeypatch, records):
    """THE ONE CONSUMER-SIDE PATCH, measured necessary (see the test below): the never-taught
    anchor's question count is scaled to the fixture corpus. The producer drew one prompt per
    cell (4 questions); the real anchor pools 416, so ``tolerance_report`` refuses every
    fixture-scale point (no outcome over 4 questions clears a ceiling built at 416). Successes,
    noise floor and provenance stay the committed ones; the count is derived, never typed."""
    (n,) = {_questions(r) for r in _trained(records).values()}
    real = phase25_verdict.never_taught_anchors

    def anchors():
        return dict(real(), control_extraction_questions=n)

    monkeypatch.setattr(phase25_verdict, "never_taught_anchors", anchors)
    return n


def _frontier(ev):
    v4, v4_sha = _v4()
    return phase32_frontier.build_frontier(ev["records"], v4, v4_sha)


def test_live_path_frontier_refuses_fixture_scale_without_the_anchor_patch(sweep_run):
    """Natural RED for the one consumer patch: the real anchor against 4-question points."""
    real_n = phase25_verdict.never_taught_anchors()["control_extraction_questions"]
    (n,) = {_questions(r) for r in _trained(sweep_run["records"]).values()}
    assert n < real_n
    with pytest.raises(ValueError, match=rf"wilson_upper_bound\(0, {n}\)"):
        _frontier(sweep_run)


def test_live_path_frontier_from_real_producer_records(sweep_run, monkeypatch):
    ev = sweep_run
    records = ev["records"]
    _fixture_scale_anchors(monkeypatch, records)
    frontier = _frontier(ev)
    admitted = phase29_prereg.admission(frontier)
    assert admitted["verdict"] in phase29_prereg.VERDICTS
    assert admitted["verdict"] != "INCONCLUSIVE", admitted["reasons"]
    assert frontier["point_keys"] == list(KEYS)
    points = frontier["points"]

    control = points[N64C]
    assert phase29_prereg.point_verdict_string(control) == phase29_prereg.REFUSED
    entry = control["verdict"]
    assert entry["early_return_reason"] == phase32_frontier.ROUTE_REFUSAL
    assert entry["early_return_reason"] == (
        "REFUSED by the sanctioned route before the pin was reached"
    )
    assert all(m in entry["reasons"][0] for m in phase29_prereg.COVERAGE_FLOOR_REFUSAL_MARKERS)

    n64_counts = _counts(records[N64C])
    for key in _leg("n64"):
        if key == N64C:
            continue
        assert points[key]["rule"] == "PREREG-03", key
        assert points[key]["verdict"]["control_recall_counts"] == n64_counts, key

    # WR-05 own-sourcing: every n8 entry was graded against the FORCED n8 control reading.
    taught = records[N8C]["taught_recall"]
    assert taught["numerator"] == taught["denominator"] // 2
    for key in _leg("n8"):
        got = points[key]["verdict"]["control_taught_recall"]
        assert got == taught["numerator"] / taught["denominator"], key

    block = frontier["verdicts"]["condition_c_vs_v4"]
    assert len(block["rows"]) == len(KEYS)
    assert block["by_leg"]["n64"]["v5_state"] == "refused_prereg03"
    rebuilt = " ".join(
        phase32_frontier.TEMPLATES[(b["v5_state"], b["v4_state"])].format(**b)
        for b in (block["by_leg"][leg] for leg in phase29_prereg.LEGS)
    )
    assert block["statement"] and block["statement"] == rebuilt


def test_live_path_admission_reads_the_real_tallies(sweep_run, monkeypatch):
    _fixture_scale_anchors(monkeypatch, sweep_run["records"])
    frontier = _frontier(sweep_run)
    assert phase29_prereg.admission(frontier)["verdict"] != "INCONCLUSIVE"
    forged = copy.deepcopy(frontier)
    tally = forged["verdicts"]["tallies_by_leg"]["advr_n8"]
    name = next(iter(tally))
    tally[name] += 1
    assert phase29_prereg.admission(forged)["verdict"] == "INCONCLUSIVE"
