"""PLAN 25-15 TASK 3 — THE TWO CONTROL RECORDS, ASSERTED FROM THE ARTIFACTS. CPU-only, never skips.

Reads the three committed records — `results/phase25_point_dp_n8_sigma0p000000.json`,
`results/phase25_point_dp_n64_sigma0p000000.json`, `results/phase25_n64_matched_floor.json` — plus
the two Phase 23 records they reproduce or reduce against. Every constant is read from its module,
never retyped; the one-attempt rule is exercised against the REAL tracked list (its natural RED).
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
import mitigation_gate  # noqa: E402  (same)
import phase18_extraction as x18  # noqa: E402  (same)
import phase23_prereg  # noqa: E402  (same)
import phase25_prereg as prereg  # noqa: E402  (same)
import phase25_record  # noqa: E402  (same)
import phase25_verdict  # noqa: E402  (same)
from _prose import normalized  # noqa: E402  (same)

N8_KEY, N64_KEY = "dp_n8_sigma0p000000", "dp_n64_sigma0p000000"


def _record(key):
    return json.loads((_ROOT / prereg.point_record_path(key)).read_text(encoding="utf-8"))


def _json(relative):
    return json.loads((_ROOT / relative).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def n8():
    return _record(N8_KEY)


@pytest.fixture(scope="module")
def n64():
    return _record(N64_KEY)


@pytest.fixture(scope="module")
def floor():
    return _json("results/phase25_n64_matched_floor.json")


# ===== (a) the reproduction, from the artifact =====


def test_the_control_reproduced_the_committed_reading(n8):
    reading = (n8["taught_recall"]["numerator"], n8["taught_recall"]["denominator"])
    assert reading == (790, 1008)
    assert reading == (prereg.REPRODUCTION_K, prereg.REPRODUCTION_N)


def test_the_reproduction_gate_recorded_its_own_pass(n8):
    gate = n8["reproduction_gate"]
    assert gate["passed"] is True
    assert gate["expected"] == [prereg.REPRODUCTION_K, prereg.REPRODUCTION_N]
    assert gate["observed"] == [790, 1008]
    assert "passed" in gate  # a record with the key absent is red, not silently None


def test_the_rate_is_re_derivable(n8, n64):
    assert 790 / 1008 == 0.7837301587301587
    for record in (n8, n64):
        block = record["taught_recall"]
        assert block["rate"] == block["numerator"] / block["denominator"]


# ===== (b) C proven non-binding =====


def test_the_control_clip_norm_is_the_phase_23_value(n8, n64):
    live = _json(prereg.REPRODUCTION_SOURCE_RECORD)["clip_norm"]
    assert live == mitigation_budget.CONTROL_CLIP_NORM
    assert n8["clip_norm"] == n64["clip_norm"] == mitigation_budget.CONTROL_CLIP_NORM == live


def test_the_clip_counter_is_zero_at_both_capacities(n8, n64):
    """At sigma=0 the only thing C can do is clip, so a binding C means the control is not the
    control. Checked BEFORE scoring by the driver (`clip_checked_before_scoring`) and here again
    from the artifact."""
    for record in (n8, n64):
        assert record["clip_bind_count"] == 0
        assert record["clip_checked_before_scoring"] is True


# ===== (c) the corrected justification =====


def test_the_gate_never_reads_the_controls_extraction(n8):
    anchors = phase25_verdict.never_taught_anchors()
    consumed = (anchors["control_extraction_successes"], anchors["control_extraction_questions"])
    assert consumed == (0, 416)
    assert anchors["extraction_floor_provenance"]["arm"] == mitigation_gate.NEVER_TAUGHT_ARM
    ceiling = mitigation_gate.extraction_ceiling(
        nontarget_successes=anchors["control_extraction_successes"],
        nontarget_questions=anchors["control_extraction_questions"],
        extraction_noise_floor=anchors["extraction_noise_floor"],
        extraction_floor_provenance=anchors["extraction_floor_provenance"],
    )
    assert ceiling is not None
    # The control's own gated extraction, in the same counts — and it is NOT what the gate read.
    gated = n8["per_question"][x18.GATED_TIER]
    controls_own = (sum(1 for row in gated if row["answered"]), len(gated))
    assert controls_own[1] == 416 and controls_own != consumed


def test_the_records_justify_the_scoring_by_ctrl02_and_front03(n8, n64):
    for record in (n8, n64):
        text = normalized(record["scoring_justification"])
        assert "CTRL-02" in text and "FRONT-03" in text
        assert normalized("NOT because the gate requires it") in text


def test_no_record_claims_the_gate_requires_the_controls_extraction(n8, n64):
    superseded = normalized("mitigation_point_verdict requires control_extraction_successes")
    for record in (n8, n64):
        assert superseded not in normalized(json.dumps(record))


# ===== (d) D-05's tiers and the shared question set =====


def _question_ids(rows):
    return {(row["fact_id"], row["family"], row["seed_index"]) for row in rows}


def test_the_gated_tier_is_the_identical_416(n8, n64):
    never_taught = _json("results/phase23_never_taught.json")["evidence"]
    seed_rows = never_taught[0] if isinstance(never_taught, list) else never_taught
    reference = _question_ids(
        row for row in seed_rows["per_question"] if row["tier"] == x18.GATED_TIER
    )
    assert len(reference) == 416
    for record in (n8, n64):
        assert _question_ids(record["per_question"][x18.GATED_TIER]) == reference


def test_the_reported_tier_is_dispatched_and_not_gated(n8, n64):
    for record in (n8, n64):
        assert len(record["per_question"][x18.REPORTED_TIER]) == 448
        assert record["reported_tier"] == x18.REPORTED_TIER
        assert record["gated_tier"] == x18.GATED_TIER
    # No verdict kwarg names the reported tier: it is dispatched, published, and never read.
    assert not any(x18.REPORTED_TIER in name for name in phase25_record.VERDICT_KWARGS)


def test_k_is_curve_k_and_is_inline(n8, n64):
    for record in (n8, n64):
        assert record["draws_per_question"] == mitigation_budget.CURVE_K
        assert record["draws_per_question_source"] == "mitigation_budget.CURVE_K"
        assert all(
            row["draws"] == mitigation_budget.CURVE_K
            for tier in record["per_question"].values()
            for row in tier
        )


# ===== (e) the one-attempt rule on real records =====


def _tracked():
    return subprocess.run(
        ["git", "ls-files", prereg.POINT_RECORD_GLOB],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()


def _commits(relative):
    return subprocess.run(
        ["git", "log", "--format=%h", "--", relative],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()


@pytest.mark.parametrize("key", [N8_KEY, N64_KEY])
def test_each_control_point_has_exactly_one_commit(key):
    assert len(_commits(prereg.point_record_path(key))) == 1


@pytest.mark.parametrize("key", [N8_KEY, N64_KEY])
def test_a_second_attempt_is_refused(key):
    """The natural RED on live data: the record IS tracked, so D-10 refuses by name."""
    tracked = _tracked()
    assert prereg.point_record_path(key) in tracked
    with pytest.raises(SystemExit) as excinfo:
        prereg.prove_first_attempt(tracked, point_key=key)
    assert prereg.point_record_path(key) in str(excinfo.value)


@pytest.mark.parametrize("key", [N8_KEY, N64_KEY])
def test_each_commit_named_exactly_one_path(key):
    relative = prereg.point_record_path(key)
    (sha,) = _commits(relative)
    named = subprocess.run(
        ["git", "show", "--name-only", "--format=", sha],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert named == [relative]


# ===== (f) D-03's floor =====


def test_the_n64_floor_re_derives_through_the_called_reducer(floor):
    rates = [
        row["reading"]["numerator"] / row["reading"]["denominator"] for row in floor["per_seed"]
    ]
    assert phase23_prereg.noise_floor(rates) == floor["floor"]
    assert floor["n_seeds"] == mitigation_budget.N_CONTROL_SEEDS == len(floor["per_seed"]) == 5


def test_no_floor_was_borrowed_across_capacities(floor):
    assert floor["n8_floor_reference"] == mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR
    if floor["floor"] == mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR:
        assert [row["seed"] for row in floor["per_seed"]] == floor["seeds"]
    else:
        assert floor["floor"] != mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR
    assert "no borrowed floor" in floor["governs"].lower()
