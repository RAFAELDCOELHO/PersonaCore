"""PLAN 25-16 TASK 2 — THE EIGHT EXTREMES, ASSERTED FROM THE ARTIFACTS. CPU-only, never skips.

Reads `results/phase25_extremes_log.json`, the eight point records, git history and the pinned
constants. D-15's interleave is a fact about commit timestamps here, not an intention.
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
import phase24_adversarial as pa  # noqa: E402  (same)
import phase25_prereg as prereg  # noqa: E402  (same)
import phase25_record as rec  # noqa: E402  (same)

from personacore.privacy.accountant import epsilon_for  # noqa: E402  (same)

LOG = _ROOT / "results" / "phase25_extremes_log.json"
BAND = json.loads((_ROOT / "results" / "phase24_token_budget.json").read_text())["band_corners"]


@pytest.fixture(scope="module")
def log():
    return json.loads(LOG.read_text(encoding="utf-8"))


def _records(log):
    return {
        key: json.loads((_ROOT / prereg.point_record_path(key)).read_text(encoding="utf-8"))
        for key in log["extreme_point_keys"]
    }


@pytest.fixture(scope="module")
def records(log):
    return _records(log)


def _git(*args):
    return subprocess.run(
        ["git", *args], cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout


EXTREMES = tuple(rec.SWEEP_SCHEDULE()[:8])
ADVERSARIAL = tuple(k for k in EXTREMES if k.startswith("adv_"))


# ===== (a) D-15's interleave, structurally and from history =====


def test_no_leg_ran_twice_consecutively(log):
    legs = [entry["leg"] for entry in log["interleave_order"]]
    assert len(legs) == 6 and all(a != b for a, b in zip(legs, legs[1:])), legs


def test_all_four_legs_appear_before_any_leg_finishes(log):
    legs = [entry["leg"] for entry in log["interleave_order"]]
    first_repeat = next(i for i, leg in enumerate(legs) if leg in legs[:i])
    assert set(legs[:first_repeat]) == set(rec.ORDERED_ARMS)


def test_every_extreme_precedes_every_interior_point(log):
    """From git log timestamps over the tracked point records: the eight extremes' commits all
    precede the earliest interior commit — D-15 as a mechanism, and a guard for plan 25-17."""
    tracked = _git("ls-files", prereg.POINT_RECORD_GLOB).split()
    stamps = {}
    for relative in tracked:
        key = pathlib.Path(relative).stem.replace("phase25_point_", "")
        stamps[key] = _git("log", "--format=%cI", "-1", "--", relative).strip()
    assert set(EXTREMES) <= set(stamps)
    latest_extreme = max(stamps[k] for k in EXTREMES)
    interior = [s for k, s in stamps.items() if k not in EXTREMES]
    assert all(latest_extreme < s for s in interior), (latest_extreme, sorted(interior)[:1])


# ===== (b) the adversarial corners on real adapters =====


@pytest.mark.parametrize("key", ADVERSARIAL)
def test_the_mask_fraction_band_holds_on_real_adapters(key, records):
    frac = records[key]["adversarial_build"]["mask_fraction"]
    lo, hi = BAND["band"]
    assert lo + pa.MASK_FRACTION_MARGIN <= frac <= hi, (key, frac)
    arm, _axis, ratio = rec.parse_point_key(key)
    corner = next(
        c for c in BAND["corners"] if c["arm"] == arm and round(c["adversarial_ratio"], 6) == ratio
    )
    assert abs(corner["mask_fraction"] - frac) < 1e-9  # the build is deterministic


@pytest.mark.parametrize("key", tuple(k for k in ADVERSARIAL if "1p909091" in k))
def test_all_three_trained_families_are_present_within_one(key, records):
    counts = records[key]["adversarial_build"]["adversarial_family_counts"]
    assert set(counts) == set(rec.TRAINED_FAMILIES)
    assert max(counts.values()) - min(counts.values()) <= 1, counts


@pytest.mark.parametrize("key", ADVERSARIAL)
def test_the_held_out_family_is_absent_from_training(key, records):
    counts = records[key]["adversarial_build"]["adversarial_family_counts"] or {}
    assert rec.HELD_OUT_FAMILY not in counts


# ===== (c) D-19 and D-22 =====


@pytest.mark.parametrize("key", ADVERSARIAL)
def test_the_pool_ceiling_is_named_as_an_axis_terminus(key, records):
    terminus = records[key]["axis_terminus"]
    assert terminus["pool_ceiling_ratio"] == mitigation_budget.ADVERSARIAL_RATIO_GRID[-1]
    assert terminus["this_point_is_the_ceiling"] == ("1p909091" in key)


def test_both_arms_reference_the_same_never_taught_floor(records):
    statements = {records[k]["axis_terminus"]["statement"] for k in ADVERSARIAL}
    assert len(statements) == 1 and "0/416" in statements.pop()


def test_the_six_ratios_are_identical_at_both_capacities():
    keys = rec.ORDERED_POINT_KEYS()
    ratios = {
        arm: sorted(rec.parse_point_key(k)[2] for k in keys if k.startswith(arm + "_"))
        for arm in rec.ADVERSARIAL_ARMS
    }
    assert ratios["adv_n8"] == ratios["adv_n64"] and len(ratios["adv_n8"]) == 6


@pytest.mark.parametrize("key", ADVERSARIAL)
def test_multiplicity_is_reported_not_swept(key, records):
    block = records[key]["multiplicity_at_upper_extreme"]
    assert block["reported_not_a_grid_variable"] is True
    assert block["ratio"] == mitigation_budget.ADVERSARIAL_RATIO_GRID[-1]


@pytest.mark.parametrize("key", tuple(k for k in EXTREMES if k.startswith("dp_")))
def test_every_published_epsilon_re_derives_from_its_sigma(key, records):
    record = records[key]
    if record["sigma"] == 0.0:
        assert record["epsilon"] is None
        return
    expected = epsilon_for(record["sigma"], mitigation_budget.STEP_BUDGET, mitigation_unit.DELTA)
    assert record["epsilon"] == expected == mitigation_budget.EPSILON_LADDER[-1]


@pytest.mark.parametrize("key", EXTREMES)
def test_every_epsilon_bearing_reading_carries_its_k_inline(key, records):
    record = records[key]
    assert record["draws_per_question"] == mitigation_budget.CURVE_K
    assert record["draws_per_question_source"] == "mitigation_budget.CURVE_K"


@pytest.mark.parametrize("key", ADVERSARIAL)
def test_no_adversarial_record_carries_an_accounting_block(key, records):
    assert records[key]["accounting"] is None and records[key]["epsilon"] is None


# ===== (d) one attempt, on real history =====


@pytest.mark.parametrize("key", EXTREMES)
def test_every_point_record_has_exactly_one_commit(key):
    assert len(_git("log", "--format=%h", "--", prereg.point_record_path(key)).split()) == 1


@pytest.mark.parametrize("key", EXTREMES)
def test_every_commit_named_exactly_one_path(key):
    relative = prereg.point_record_path(key)
    (sha,) = _git("log", "--format=%h", "--", relative).split()
    assert _git("show", "--name-only", "--format=", sha).split() == [relative]


@pytest.mark.parametrize("key", EXTREMES)
def test_a_second_attempt_at_any_extreme_is_refused(key):
    tracked = _git("ls-files", prereg.POINT_RECORD_GLOB).split()
    with pytest.raises(SystemExit):
        prereg.prove_first_attempt(tracked, point_key=key)


def test_adversarial_adapters_exist_at_a_non_zero_ratio(log, records):
    """ADVT-01's subject — the adapter trained — now exists, named in the log by sha256."""
    key = "adv_n8_ratio1p909091"
    assert records[key]["adversarial_build"]["adversarial_episodes"] > 0
    assert log["advt_01"]["adapter_sha256"] == records[key]["adapter_sha256"]
