"""PLAN 25-17 TASK 2 — ALL 44 RECORDS, ASSERTED FROM THE COMMITTED BYTES. CPU-only, never skips.

Widens `tests/test_phase25_extremes.py` from the eight extremes to the full pinned set: completeness
as a set equality, the five pinned mechanism fields over every record, counts with denominators,
and the one-attempt history over 44 real single-path commits. The interior log's own honesty —
kills with `reading_landed`, stalls with `action_taken == "none"` — is asserted from
`results/phase25_interior_log.json`.
"""

import json
import pathlib
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

import mitigation_budget  # noqa: E402  (scripts/ is not a package)
import mitigation_unit  # noqa: E402  (same)
import phase18_extraction as pe  # noqa: E402  (same)
import phase25_prereg as prereg  # noqa: E402  (same)
import phase25_record as rec  # noqa: E402  (same)

from personacore.privacy.accountant import epsilon_for  # noqa: E402  (same)

LOG = _ROOT / "results" / "phase25_interior_log.json"
KEYS = tuple(rec.ORDERED_POINT_KEYS())
DP = tuple(k for k in KEYS if k.startswith("dp_"))
ADVERSARIAL = tuple(k for k in KEYS if k.startswith("adv_"))


def _git(*args):
    return subprocess.run(
        ["git", *args], cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout


@pytest.fixture(scope="module")
def log():
    return json.loads(LOG.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def records():
    return {
        key: json.loads((_ROOT / prereg.point_record_path(key)).read_text(encoding="utf-8"))
        for key in KEYS
    }


@pytest.fixture(scope="module")
def tracked():
    return _git("ls-files", prereg.POINT_RECORD_GLOB).split()


@pytest.fixture(scope="module")
def commits(tracked):
    """{record path: [commit shas]} over every tracked point record, from one `git log` walk."""
    out = {path: [] for path in tracked}
    sha = None
    for line in _git("log", "--format=@%h", "--name-only", "--", *tracked).splitlines():
        if line.startswith("@"):
            sha = line[1:]
        elif line.strip():
            out.setdefault(line.strip(), []).append(sha)
    return out


@pytest.fixture(scope="module")
def commit_paths(commits):
    """{sha: [paths named]} for every commit that touched a point record."""
    shas = sorted({s for lst in commits.values() for s in lst})
    out = {}
    for sha in shas:
        out[sha] = _git("show", "--name-only", "--format=", sha).split()
    return out


# ===== (a) completeness as a set =====


def test_the_committed_keys_equal_the_pinned_keys(tracked):
    have = {pathlib.Path(p).name for p in tracked}
    want = {pathlib.Path(prereg.point_record_path(k)).name for k in KEYS}
    assert have == want, f"missing {sorted(want - have)} extra {sorted(have - want)}"


def test_there_are_thirty_two_dp_and_twelve_adversarial_points():
    assert len(DP) == len(rec.DP_ARMS) * mitigation_budget.SWEEP_POINTS
    assert len(ADVERSARIAL) == len(rec.ADVERSARIAL_ARMS) * len(
        mitigation_budget.ADVERSARIAL_RATIO_GRID
    )
    assert len(DP) + len(ADVERSARIAL) == len(KEYS)


def test_no_duplicate_point_keys(tracked, records):
    assert len(set(KEYS)) == len(KEYS)
    assert len(set(tracked)) == len(tracked)
    assert {r["point_key"] for r in records.values()} == set(KEYS)


# ===== (b) the pinned mechanism across all 44 =====


@pytest.mark.parametrize("field", rec.MECHANISM_PIN_FIELDS)
@pytest.mark.parametrize("key", KEYS)
def test_every_record_matches_the_pinned_mechanism(key, field, records):
    """D-34 over the COMMITTED bytes. The pin is re-derived here exactly as the driver derives it
    (phase25_points.pinned_mechanism / train_point): DP arms pin the capacity as the lot, q and C
    from the budget literals; the adversarial arm has no DP mechanism — q and C are None and the
    lot is batch_size x max(1, grad_accum_steps) of the live TrainConfig the record carries."""
    record = records[key]
    if record["arm"] in rec.ADVERSARIAL_ARMS:
        cfg = record["training"]["train_config"]
        lot = int(cfg["batch_size"] * max(1, cfg["grad_accum_steps"]))
        pin = {
            "composed_steps": mitigation_budget.STEP_BUDGET,
            "composed_lot_sizes": [lot],
            "records_per_lot": lot,
            "q": None,
            "clip_norm": None,
        }
    else:
        capacity = int(key.split("_")[1][1:])
        pin = {
            "composed_steps": mitigation_budget.STEP_BUDGET,
            "composed_lot_sizes": [capacity],
            "records_per_lot": capacity,
            "q": mitigation_unit.SAMPLING_RATE_Q,
            "clip_norm": (
                mitigation_budget.CONTROL_CLIP_NORM
                if record["sigma"] == 0.0
                else mitigation_budget.CLIP_NORM
            ),
        }
    assert record[field] == pin[field], (key, field, record[field], pin[field])


@pytest.mark.parametrize("key", DP)
def test_every_dp_record_carries_a_re_derivable_epsilon(key, records):
    record = records[key]
    if record["sigma"] == 0.0:
        assert record["epsilon"] is None
        return
    assert record["epsilon"] == epsilon_for(
        record["sigma"], mitigation_budget.STEP_BUDGET, mitigation_unit.DELTA
    )


@pytest.mark.parametrize("key", ADVERSARIAL)
def test_every_adversarial_record_carries_accounting_null(key, records):
    assert records[key]["accounting"] is None and records[key]["epsilon"] is None


@pytest.mark.parametrize("key", KEYS)
def test_every_record_carries_its_k_inline(key, records):
    assert records[key]["draws_per_question"] == mitigation_budget.CURVE_K
    assert records[key]["draws_per_question_source"] == "mitigation_budget.CURVE_K"


# ===== (c) counts, never rates =====

# a key whose name says "rate" must sit beside the two counts it was computed from
_RATE_SIBLINGS = (
    {"numerator", "denominator"},
    {"k", "n_draws"},
    {"n_draws", "minutes"},
)


def _rate_leaves_without_counts(node, path=""):
    bad = []
    if isinstance(node, dict):
        keys = set(node)
        for k, v in node.items():
            if "rate" in k.lower() and not any(sib <= keys for sib in _RATE_SIBLINGS):
                bad.append(f"{path}/{k}")
            bad.extend(_rate_leaves_without_counts(v, f"{path}/{k}"))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            bad.extend(_rate_leaves_without_counts(v, f"{path}[{i}]"))
    return bad


@pytest.mark.parametrize("key", KEYS)
def test_no_record_carries_a_rate_without_its_denominator(key, records):
    assert _rate_leaves_without_counts(records[key]) == []


@pytest.mark.parametrize("key", KEYS)
def test_per_question_rows_are_present_for_the_gated_tier(key, records):
    gated = records[key]["per_fact"][pe.GATED_TIER]
    rows = sum(len(fact["questions"]) for fam in gated.values() for fact in fam.values())
    assert rows == 416, (key, rows)


@pytest.mark.parametrize("key", KEYS)
def test_per_family_counts_include_the_held_out_family(key, records):
    counts = records[key]["per_family_counts"]
    assert set(counts) == set(pe.ATTACK_FAMILIES)
    assert rec.HELD_OUT_FAMILY in counts


# ===== (d) the one-attempt history, across 44 real commits =====


@pytest.mark.parametrize("key", KEYS)
def test_every_record_has_exactly_one_commit(key, commits):
    assert len(commits[prereg.point_record_path(key)]) == 1


@pytest.mark.parametrize("key", KEYS)
def test_every_commit_named_exactly_one_path(key, commits, commit_paths):
    relative = prereg.point_record_path(key)
    (sha,) = commits[relative]
    assert commit_paths[sha] == [relative]


def test_no_commit_touched_a_gitignored_tree(commit_paths):
    named = [p for paths in commit_paths.values() for p in paths]
    assert not [p for p in named if p.startswith(("data/", "checkpoints/"))]


def test_no_commit_touched_source_or_planning(commit_paths):
    named = [p for paths in commit_paths.values() for p in paths]
    assert not [p for p in named if p.startswith(("scripts/", "src/", "tests/", ".planning/"))]


# ===== (e) the log's own honesty =====


def test_the_interior_set_is_the_complement_of_the_extremes(log):
    extremes = set(rec.SWEEP_SCHEDULE()[:8])
    assert set(log["interior_set"]) == set(KEYS) - extremes
    assert len(log["interior_set"]) == 36 and log["interior_set_derivation"]["asserted_36"]
    assert log["completeness"]["set_equality"] is True
    assert log["n64_leg_withdrawn"] is mitigation_budget.N64_LEG_WITHDRAWN is False


def test_every_kill_records_whether_a_reading_landed(log):
    kills = log["kills_and_resumes"]
    assert kills, "the run had kills; none recorded"
    for kill in kills:
        assert {"reading_landed", "shapes_complete_on_disk", "last_heartbeat"} <= set(kill)
        assert kill["reading_landed"] is False and kill["same_attempt_under_d10"] is True
        assert kill["shapes_complete_on_disk"] == []  # no shape block had landed
        assert kill["last_heartbeat"]["stage"] == "draw"


def test_no_stall_record_shows_an_action(log):
    assert log["stall_records"]
    assert all(s["action_taken"] == "none" for s in log["stall_records"])
    assert all(s["record"]["action_taken"] == "none" for s in log["stall_records"])


def test_the_wall_clock_table_covers_every_point(log):
    table = log["wall_clock_table"]
    assert set(table) == set(KEYS)
    for key, row in table.items():
        assert row["hours"] > 0
        assert set(row["stop_terminated_n"]) == set(pe.ATTACK_FAMILIES), key


def test_every_kill_cost_less_than_the_shape_it_interrupted(log):
    """D-09: a kill costs at most ONE SHAPE. Each kill's wall-clock loss (minutes into the shape
    at the last beat + the relaunch gap) is under that point's own redrawn shape's minutes."""
    by_key = {e["point_key"]: e for e in log["interior_points"]}
    assert log["largest_single_loss_minutes"] == max(
        k["wall_clock_lost_minutes"] for k in log["kills_and_resumes"]
    )
    for kill in log["kills_and_resumes"]:
        shape = kill["last_heartbeat"]["shape"]
        redrawn_minutes = by_key[kill["point_key"]]["draw_minutes"][shape]
        assert 0 < kill["wall_clock_lost_minutes"] < redrawn_minutes, (kill["point_key"], shape)
