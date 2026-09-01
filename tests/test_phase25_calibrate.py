"""The two Phase-25 calibration records, GUARDED BY RE-DERIVATION rather than by restatement.

The subjects are ``results/phase25_clip_calibration.json`` and
``results/phase25_adversarial_throughput.json``, both written by ``scripts/phase25_calibrate.py``.
Every path is resolved from the emitter's own constants and never spelled a second time in
executable code — ``tests/test_phase24_record.py``'s register: one small parser per record, the
path owned by the module that writes it.

**What makes this more than a schema check.** A record whose numbers are only ever compared
against themselves proves nothing; a hand-edited figure passes every key-presence assertion here.
So:

  * :func:`test_the_c_candidate_re_derives_from_the_recorded_rule` recomputes the candidate from
    the recorded values under the recorded rule and asserts EXACT equality. **That is what makes
    ``C`` a measurement rather than a preference**, and it is the assertion plan 25-12's pin rests
    on.
  * :func:`test_the_recorded_clip_domain_refusal_matches_the_live_one` compares the record's
    transcript to the message a LIVE ``DPSGD(None, sigma=0.0, clip_norm=math.inf)`` raises, so the
    transcript is proved a COPY rather than a paraphrase. **The refusal itself is NOT asserted
    here** — CTRL-02's cheap proxy is ``tests/test_phase25_prereg.py::test_clip_domain_is_refused``
    (plan 25-01, **wave 1**), because a millisecond CPU check guarding a 100-150 h sweep must
    precede every GPU-spending plan rather than sit inside the first one.
  * :func:`test_the_anchor_digest_is_live` and
    :func:`test_the_calibration_provenance_matches_the_live_module_bytes` recompute sha256 from
    bytes. The second was WATCHED RED against a hand-edited copy in ``tmp_path``; the real tree is
    never touched.

CPU-only, GPU/MPS-free, no training, no retraining. Every test reads committed bytes.
"""

import hashlib
import json
import math
import pathlib
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import mitigation_budget as mb  # noqa: E402  (scripts/ is not a package)
import phase25_calibrate as cal  # noqa: E402
import phase25_prereg as prereg  # noqa: E402
import phase25_record as rec  # noqa: E402

from personacore.privacy.dpsgd import DPSGD  # noqa: E402


def _clip():
    """The committed clip-calibration record, parsed. ONE reader; the path comes from its owner."""
    return json.loads(cal.CLIP_CALIBRATION_RECORD.read_text(encoding="utf-8"))


def _throughput():
    """The committed throughput record, parsed. ONE reader; the path comes from its owner."""
    return json.loads(cal.THROUGHPUT_RECORD.read_text(encoding="utf-8"))


def _sha256(path):
    """sha256 recomputed from BYTES. Deliberately not ``cal.sha256_of`` — a digest check that
    reused the emitter's own helper would agree with it by construction."""
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _git(*args):
    return subprocess.run(
        ["git", *args], cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout


def _walk(node, path=()):
    """Every ``(key-path, value)`` pair in a nested blob. Used for the no-average key inspection."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _walk(value, (*path, str(key)))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk(value, (*path, str(index)))
    else:
        yield path, node


# =================================================================================================
# ===== (a) THE EXCLUSION, PROVED STRUCTURALLY =====
# =================================================================================================


def test_the_calibration_prefix_is_not_a_sweep_point_prefix():
    """No key ``phase25_record.point_key`` can build begins with ``CALIBRATION_PREFIX``.

    Proved over the ARM TUPLE rather than over one ladder, and therefore total: every point key is
    ``f"{arm}_{axis}{value:.6f}"`` for ``arm`` in ``phase25_record.ORDERED_ARMS``, so a key can
    begin with the calibration prefix only if the prefix and some arm are prefix-comparable in one
    direction or the other. Neither holds, for any sigma ladder plan 25-12 pins.

    ``ORDERED_POINT_KEYS()`` raises until 25-12 exists (``mitigation_budget.SIGMA_LADDER`` is its
    input), so the live key set is checked ADDITIONALLY when it is available rather than as the
    only check — a guard that could only run after wave 5 would guard nothing in wave 4.
    """
    prefix = cal.CALIBRATION_PREFIX
    assert prefix, "CALIBRATION_PREFIX is empty — an empty prefix is a prefix of every key"
    for arm in rec.ORDERED_ARMS:
        assert not arm.startswith(prefix), (arm, prefix)
        assert not prefix.startswith(arm), (arm, prefix)

    # And the same claim against the LIVE key set, once the ladder exists.
    if getattr(mb, "SIGMA_LADDER", None) is not None:  # pragma: no cover - true from 25-12 on
        keys = rec.ORDERED_POINT_KEYS()
        assert keys, "ORDERED_POINT_KEYS() returned an empty set"
        assert not [key for key in keys if key.startswith(prefix)], prefix


def test_no_point_record_path_can_name_the_calibration_prefix():
    """``phase25_prereg.POINT_RECORD_GLOB`` is blind to every artifact this module writes.

    Both calibration records live at ``results/phase25_{clip_calibration,adversarial_throughput}``
    and neither carries the ``results/phase25_point_`` stem the one-attempt glob reads, so a
    calibration record can never be counted as a sweep point by the rule that watches them.
    """
    import fnmatch

    for record in (cal.CLIP_CALIBRATION_RECORD, cal.THROUGHPUT_RECORD):
        relative = str(record.relative_to(_ROOT))
        assert not fnmatch.fnmatch(relative, prereg.POINT_RECORD_GLOB), relative
        assert not relative.startswith(prereg.POINT_RECORD_PREFIX), relative
    assert cal.CALIBRATION_PREFIX not in prereg.POINT_RECORD_PREFIX


def test_no_sweep_point_record_existed_when_the_calibrations_landed():
    """No tracked ``results/phase25_point_*.json`` exists at HEAD, read from git rather than
    asserted. These are CALIBRATION runs and the sweep has not started."""
    tracked = [
        line for line in _git("ls-files", prereg.POINT_RECORD_GLOB).splitlines() if line.strip()
    ]
    assert tracked == [], tracked
    assert prereg.POINT_RECORDS_AT_COMMIT == 0, prereg.POINT_RECORDS_AT_COMMIT


# =================================================================================================
# ===== (b) THE CLIP CALIBRATION =====
# =================================================================================================


@pytest.mark.parametrize("capacity", cal.NORM_PROBE_CAPACITIES)
def test_every_per_record_norm_is_individually_recorded(capacity):
    """``len(values) == n_records`` at both capacities, so every quantile in the record
    re-derives from the values beside it rather than from a histogram summary."""
    block = _clip()["per_record_norms"][capacity]
    assert len(block["values"]) == block["n_records"] > 0, (
        capacity,
        len(block["values"]),
        block["n_records"],
    )
    assert block["values"] == sorted(block["values"]), capacity
    assert all(math.isfinite(value) and value >= 0.0 for value in block["values"]), capacity
    # `by_step` is the SAME measurement in absorb order; a partition that lost or duplicated a
    # record would make the trajectory un-re-derivable while `values` still looked complete.
    flattened = [value for step in block["by_step"] for value in step]
    assert len(flattened) == block["n_records"], capacity
    assert sorted(flattened) == block["values"], capacity
    assert [len(step) for step in block["by_step"]] == block["records_per_step"], capacity
    assert len(block["by_step"]) == block["optimizer_steps"], capacity


@pytest.mark.parametrize("capacity", cal.NORM_PROBE_CAPACITIES)
def test_every_recorded_statistic_re_derives_from_the_values(capacity):
    """min / max / mean / median / p90 / p99 recomputed from the recorded values.

    The quantiles use the record's OWN stated rule — the order statistic
    ``sorted(values)[ceil(q * n) - 1]``, no interpolation — so each is one of the measured values.
    """
    block = _clip()["per_record_norms"][capacity]
    values = block["values"]
    n = len(values)
    assert block["min"] == values[0]
    assert block["max"] == values[-1]
    assert block["mean"] == sum(values) / n
    for key, quantile in (("median", 0.5), ("p90", 0.90), ("p99", 0.99)):
        assert block[key] == values[math.ceil(quantile * n) - 1], (capacity, key)


def test_the_c_candidate_re_derives_from_the_recorded_rule():
    """THE ASSERTION 25-12'S PIN RESTS ON. ``C`` is a measurement, not a preference.

    The candidate is recomputed from the recorded values under the recorded quantile and index,
    and compared under EXACT equality. A hand-edited candidate, a shifted quantile or a swapped
    capacity all fail here.
    """
    blob = _clip()
    capacity = blob["clip_norm_rule_capacity"]
    quantile = blob["clip_norm_rule_quantile"]
    values = blob["per_record_norms"][capacity]["values"]
    index = math.ceil(quantile * len(values)) - 1

    assert index == blob["clip_norm_rule_index"], (index, blob["clip_norm_rule_index"])
    assert values[index] == blob["clip_norm_candidate"], (
        values[index],
        blob["clip_norm_candidate"],
    )
    # The candidate IS one of the measured values — the property no-interpolation buys.
    assert blob["clip_norm_candidate"] in values
    # The RULE is recorded, and it is recorded as prose stating the derivation rather than as a
    # bare number: the plan requires the rule to precede the number it produced.
    assert len(blob["clip_norm_rule"]) > 60, len(blob["clip_norm_rule"])
    assert capacity in blob["clip_norm_rule"] and "25-12" in blob["clip_norm_rule"]


def test_the_control_clip_norm_is_the_phase_23_value():
    """``control_clip_norm == 1000000.0``, equal to ``results/phase23_sigma_zero.json``'s own
    ``clip_norm`` read LIVE, so D-01's bit-level reproduction stays reachable.

    The two clip constants are a DECISION this record makes and records: the calibrated candidate
    governs the noised points and this value governs the control, and 25-CONTEXT resolves the pair
    nowhere.
    """
    blob = _clip()
    sigma_zero = json.loads((_ROOT / cal.NORM_PROBE_CLIP_NORM_SOURCE).read_text(encoding="utf-8"))
    assert blob["control_clip_norm"] == 1000000.0
    assert blob["control_clip_norm"] == float(sigma_zero["clip_norm"])
    assert sigma_zero["clip_bind_count"] == 0
    assert blob["control_clip_norm"] != blob["clip_norm_candidate"]

    decision = blob["two_clip_constants_decision"]
    names = {row["name"]: row["value"] for row in decision["constants"]}
    assert names["CONTROL_CLIP_NORM"] == blob["control_clip_norm"]
    assert names["CLIP_NORM"] == blob["clip_norm_candidate"]

    # The probe itself ran at the control's non-binding bound, so the recorded norms are the
    # UNCLIPPED records rather than a picture of the bound.
    assert blob["probe"]["clip_norm"] == blob["control_clip_norm"]
    assert blob["probe"]["sigma"] == cal.NORM_PROBE_SIGMA


def test_the_binding_question_is_answered_in_counts():
    """``fraction_of_records_above_c1`` carries an INTEGER numerator and denominator, never a
    bare rate, and both re-derive from the recorded values."""
    blob = _clip()
    fraction = blob["fraction_of_records_above_c1"]
    assert isinstance(fraction["numerator"], int), type(fraction["numerator"])
    assert isinstance(fraction["denominator"], int), type(fraction["denominator"])
    assert 0 <= fraction["numerator"] <= fraction["denominator"]
    assert 0.0 <= fraction["numerator"] / fraction["denominator"] <= 1.0
    # No bare rate is published beside them.
    assert "fraction" not in fraction and "rate" not in fraction

    for capacity, row in fraction["per_capacity"].items():
        values = blob["per_record_norms"][capacity]["values"]
        assert row["numerator"] == sum(1 for value in values if value > 1.0), capacity
        assert row["denominator"] == len(values), capacity
    assert fraction["per_capacity"][fraction["capacity"]]["numerator"] == fraction["numerator"]


def test_the_bind_curve_re_derives_from_the_values():
    """Every ``clip_bind_count`` on the trial ladder is ``DPSGD.absorb_record``'s own predicate
    (``norm > C``) applied to the recorded norms — a measured curve, not an inference."""
    blob = _clip()
    for capacity, rows in blob["clip_bind_curve"].items():
        values = blob["per_record_norms"][capacity]["values"]
        assert rows, capacity
        for row in rows:
            assert row["n_records"] == len(values), capacity
            assert row["clip_bind_count"] == sum(1 for v in values if v > row["clip_norm"]), (
                capacity,
                row["clip_norm"],
            )
    # The counter-example's C and the control's non-binding bound are both ON the ladder, so the
    # two committed operating points are readable off the measured curve.
    trials = {row["clip_norm"] for row in blob["clip_bind_curve"][blob["clip_norm_rule_capacity"]]}
    assert 1.0 in trials
    assert blob["control_clip_norm"] in trials
    assert blob["clip_norm_candidate"] in trials


def test_the_counter_example_is_cited_with_a_live_digest():
    """D-24's 12800-of-12800 counter-example is quoted from the record it lives in, and that
    record's sha256 is recomputed from bytes so it cannot move under the citation."""
    blob = _clip()
    cited = blob["counter_example"]
    live = json.loads((_ROOT / cited["record"]).read_text(encoding="utf-8"))
    assert cited["record_sha256"] == _sha256(_ROOT / cited["record"])
    assert cited["clip_norm"] == live["clip_norm"] == 1.0
    assert cited["clip_bind_count"] == live["clip_bind_count"] == 12800
    assert cited["epsilon"] == live["epsilon"]

    # The BATCH-LEVEL non-DP evidence is quoted as a DIFFERENT QUANTITY and never as a bound.
    batch = blob["batch_level_comparison"]
    assert batch["record_sha256"] == _sha256(_ROOT / batch["record"])
    assert "BATCH-LEVEL" in batch["quantity"] and "per-record" in batch["quantity"]


def test_the_recorded_clip_domain_refusal_matches_the_live_one():
    """The record's transcript is a live COPY of the mechanism's message, not a paraphrase.

    **THE REFUSAL ITSELF IS NOT ASSERTED HERE.** CTRL-02's cheap proxy is
    ``tests/test_phase25_prereg.py::test_clip_domain_is_refused`` (plan 25-01, wave 1) — a
    millisecond CPU check that guards a 100-150 h sweep belongs before every GPU-spending plan,
    and ``25-VALIDATION.md``'s CTRL-02 row points there. This test only proves the copy is live.
    """
    provenance = _clip()["provenance"]
    live = {}
    for label, value in cal._CLIP_DOMAIN_LIVE.items():
        with pytest.raises(ValueError) as excinfo:
            DPSGD(None, sigma=0.0, clip_norm=value)
        live[label] = str(excinfo.value)

    assert provenance["clip_domain_refusal"] == live["inf"]
    assert "[dp-refusal:clip-domain]" in provenance["clip_domain_refusal"]
    for label, message in live.items():
        assert provenance["clip_domain_refusals"][label]["message"] == message, label
    assert sorted(provenance["clip_domain_refusals"]) == sorted(cal.CLIP_DOMAIN_PROBE_VALUES)


def test_both_capacities_cover_the_full_step_budget():
    """Neither capacity's sample is truncated. The candidate is derived over the whole run.

    ``dp_n64``'s 12800 records is also the SAME denominator D-24's counter-example reports its
    ``clip_bind_count`` of 12800 over, so the two are counted over identical record sets.
    """
    import teach_persona as tp

    blob = _clip()
    for capacity in cal.NORM_PROBE_CAPACITIES:
        block = blob["per_record_norms"][capacity]
        assert block["optimizer_steps"] == tp.MAX_STEPS, (capacity, block["optimizer_steps"])
        assert block["n_records"] == cal.NORM_PROBE_RECORD_BUDGET[capacity], capacity
        assert set(block["records_per_step"]) == {block["n_records"] // tp.MAX_STEPS}, capacity
    assert (
        blob["per_record_norms"]["dp_n64"]["n_records"]
        == blob["counter_example"]["clip_bind_count"]
        == 12800
    )
    assert blob["probe"]["max_steps_unchanged"] is True


@pytest.mark.parametrize("capacity", cal.NORM_PROBE_CAPACITIES)
def test_the_early_window_bias_re_derives_from_the_recorded_values(capacity):
    """THE FINDING THAT FORCED THE FULL RUNS, re-derived from the recorded partition.

    An earlier pass of plan 25-11 truncated ``dp_n64`` to its first ``EARLY_WINDOW_STEPS``
    optimizer steps to fit a 40-minute budget. ``dp_n8``'s full run measured that window
    overstating the median per-record norm by ~3.1x, so the window was abandoned rather than
    caveated. The measurement is kept at BOTH capacities and only the FULL-RUN reading feeds
    ``clip_norm_candidate``.
    """
    blob = _clip()
    bias = blob["truncation_bias"][capacity]
    full = blob["per_record_norms"][capacity]
    window = sorted(
        value for step in full["by_step"][: bias["window_optimizer_steps"]] for value in step
    )
    quantile = blob["clip_norm_rule_quantile"]

    assert bias["capacity"] == capacity
    assert bias["window_optimizer_steps"] == cal.EARLY_WINDOW_STEPS
    assert bias["full_optimizer_steps"] == full["optimizer_steps"]
    assert len(window) == bias["window_n_records"]
    assert bias["candidate_over_window"] == window[math.ceil(quantile * len(window)) - 1]
    assert (
        bias["candidate_over_full_run"]
        == full["values"][math.ceil(quantile * full["n_records"]) - 1]
    )
    assert bias["absolute_difference"] == abs(
        bias["candidate_over_window"] - bias["candidate_over_full_run"]
    )
    assert (
        bias["window_over_full_ratio"]
        == bias["candidate_over_window"] / bias["candidate_over_full_run"]
    )
    # The candidate the record publishes is the FULL-RUN reading, never the window's.
    if capacity == blob["clip_norm_rule_capacity"]:
        assert blob["clip_norm_candidate"] == bias["candidate_over_full_run"]
        assert blob["clip_norm_candidate"] != bias["candidate_over_window"]


def test_no_budget_pin_was_edited_by_this_plan():
    """``scripts/mitigation_budget.py`` is byte-unchanged: this plan MEASURES and 25-12 PINS."""
    for name in (
        "mitigation_budget.py",
        "mitigation_gate.py",
        "mitigation_accountant.py",
        "mitigation_unit.py",
        "phase18_extraction.py",
    ):
        diff = subprocess.run(
            ["git", "diff", "--exit-code", "--", f"scripts/{name}"],
            cwd=_ROOT,
            capture_output=True,
            text=True,
        )
        assert diff.returncode == 0, (name, diff.stdout[:400])


# =================================================================================================
# ===== (c) THE THROUGHPUT PROBE =====
# =================================================================================================


def test_both_extremes_were_probed():
    """Both ends of ``ADVERSARIAL_RATIO_GRID``, each at 768 draws over four shapes, with
    stop-termination counts. D-14 forbids extrapolating the schedule from one."""
    extremes = _throughput()["extremes"]
    assert set(extremes) == {repr(value) for value in cal.ADVERSARIAL_EXTREMES}, sorted(extremes)
    assert set(extremes) == {"0.0", "1.9090909090909092"}, sorted(extremes)

    for key, block in extremes.items():
        assert block["n_draws_measured"] == 768, (key, block["n_draws_measured"])
        assert len(block["per_shape"]) == 4, (key, sorted(block["per_shape"]))
        assert block["n_draws_measured"] == sum(
            shape["n_draws"] for shape in block["per_shape"].values()
        ), key
        for shape, row in block["per_shape"].items():
            assert "stop_terminated_n" in row, (key, shape)
            assert isinstance(row["stop_terminated_n"], int), (key, shape)
            assert row["seconds"] > 0 and row["rate_draws_per_min"] > 0, (key, shape)
            # The per-shape rate is a real quotient over its own denominator, not a copied figure.
            assert row["rate_draws_per_min"] == row["n_draws"] / (row["seconds"] / 60.0), (
                key,
                shape,
            )
            assert row["stop_terminated_n"] == sum(
                condition["stop_terminated_n"] for condition in row["by_condition"].values()
            ), (key, shape)
        assert block["ratio"] == float(key)


def test_the_ratio_zero_bins_are_the_committed_seam_off_bins():
    """The anchor's corpus identity is PROVED: the ratio-0.0 leg's bins hash to 24-06's committed
    digests, so the comparison against the non-DP 161.124 s/point is two readings of one corpus."""
    identity = _throughput()["extremes"]["0.0"]["bins_byte_identity"]
    assert identity["asserted"] is True
    assert identity["matches_24_06_digests"] is True
    assert identity["measured_token_bin_sha256"] == cal.RATIO_ZERO_TOKEN_BIN_SHA256
    assert identity["measured_mask_bin_sha256"] == cal.RATIO_ZERO_MASK_BIN_SHA256
    assert _throughput()["extremes"]["1.9090909090909092"].get("bins_byte_identity") is None


def test_the_anchor_digest_is_live():
    """``results/phase23_cost.json``'s sha256 recomputed from bytes. A stale digest means the
    anchor moved under the schedule that was sized on it."""
    anchor = _throughput()["anchor"]
    assert anchor["source_record"] == "results/phase23_cost.json"
    assert anchor["source_record_sha256"] == _sha256(_ROOT / anchor["source_record"])

    live = json.loads((_ROOT / anchor["source_record"]).read_text(encoding="utf-8"))
    full = live["ratios"]["non_dp"]["training_seconds_per_point"]
    assert anchor["non_dp_training_seconds_per_point"] == 161.124
    assert anchor["non_dp_training_seconds_per_point_full"] == full
    assert round(full, cal.ANCHOR_ROUNDING_DECIMALS) == 161.124


def test_the_schedule_was_finalised_after_both():
    """``finalised_after`` names both extremes, and the terms SUM to the recorded totals under
    exact arithmetic — the envelope is a sum of named terms, never a single figure."""
    schedule = _throughput()["schedule"]
    assert "both" in schedule["finalised_after"], schedule["finalised_after"]
    assert len(schedule["terms"]) >= 4, len(schedule["terms"])

    assert schedule["total_hours_floor"] == sum(t["hours_floor"] for t in schedule["terms"])
    assert schedule["total_hours_ceiling"] == sum(t["hours_ceiling"] for t in schedule["terms"])
    for term in schedule["terms"]:
        assert term["rule"] and isinstance(term["measured"], bool), term["term"]
        assert term["hours_ceiling"] >= term["hours_floor"] >= 0.0, term["term"]
    # Every term is named exactly once — a duplicated name would double-count silently.
    names = [term["term"] for term in schedule["terms"]]
    assert len(names) == len(set(names)), names
    # Both extremes are carried per-extreme, so the adversarial term's bracket is inspectable.
    assert set(schedule["per_extreme"]) == {repr(v) for v in cal.ADVERSARIAL_EXTREMES}
    assert schedule["points"]["total"] == 44, schedule["points"]
    assert schedule["curve_k"] == mb.CURVE_K


def test_no_average_was_taken_across_the_two_extremes():
    """Two SEPARATE rate figures, and no field anywhere in the record is their mean.

    Resolved by key inspection AND by value inspection: a mean can be smuggled in under any name,
    so every numeric leaf is compared against the arithmetic mean of the two extremes' pooled
    rates under exact equality.
    """
    blob = _throughput()
    low, high = (repr(value) for value in cal.ADVERSARIAL_EXTREMES)

    # The key rule applies to NUMERIC leaves only. WATCHED RED first on the prose field
    # `divergence.no_average_taken`, whose whole job is to DECLARE that no average was taken: an
    # unrestricted key scan flags the declaration and not the thing it declares. The value leg
    # below is the load-bearing half and it catches a mean smuggled under any name at all.
    for path, value in _walk(blob):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            assert "average" not in path[-1].lower(), path
            assert not path[-1].lower().startswith("avg"), path
            assert "mean" not in path[-1].lower() or path[-1] == "mean_tokens", path

    means = set()
    for condition in blob["extremes"][low]["per_condition_totals"]:
        low_rate = blob["extremes"][low]["per_condition_totals"][condition]["rate_draws_per_min"]
        high_rate = blob["extremes"][high]["per_condition_totals"][condition]["rate_draws_per_min"]
        assert low_rate != high_rate, condition
        means.add((low_rate + high_rate) / 2.0)
    for path, value in _walk(blob):
        if isinstance(value, float):
            assert value not in means, (path, value)

    divergence = blob["divergence"]
    for condition, row in divergence["per_condition"].items():
        assert row["rate_draws_per_min_at_low_extreme"] != row["rate_draws_per_min_at_high_extreme"]
        assert row["relative_gap"] == abs(
            row["rate_draws_per_min_at_low_extreme"] - row["rate_draws_per_min_at_high_extreme"]
        ) / max(
            row["rate_draws_per_min_at_low_extreme"],
            row["rate_draws_per_min_at_high_extreme"],
        ), condition
        assert row["exceeds_tolerance"] == (row["relative_gap"] > divergence["tolerance"])


def test_the_probe_reproduces_cal05s_own_768_composition():
    """768 = 3 conditions x 4 shapes x 64 draws — ``results/phase23_cost.json``'s OWN composition
    of ``n_draws_measured``, so the two figures are comparable term by term.

    25-11-PLAN's prose describes the bracket as ``8 x 8 x 4 x 2``, which is 512; the committed
    record composes ``floor_total + ceiling_total + base_total``. The record follows the
    measurement, and it records the correction rather than absorbing it silently.
    """
    live = json.loads((_ROOT / "results" / "phase23_cost.json").read_text(encoding="utf-8"))
    assert live["generation"]["n_draws_measured"] == 768
    for key, block in _throughput()["extremes"].items():
        assert sorted(block["conditions"]) == ["base_floor", "ceiling", "floor"], key
        assert block["timed_draws_per_shape_per_condition"] == 64, key
        assert (
            block["warmup_draws_discarded_per_shape"]
            == live["generation"]["warmup_draws_discarded_per_shape"]
        ), key
        for condition, totals in block["per_condition_totals"].items():
            assert totals["n_draws"] == 256, (key, condition)


# =================================================================================================
# ===== (d) THE FRESHNESS GUARD — WATCHED RED ON A tmp_path COPY =====
# =================================================================================================


def test_the_calibration_provenance_matches_the_live_module_bytes():
    """Both records carry ``scripts/phase25_calibrate.py``'s sha256, recomputed from bytes.

    ``tests/test_phase24_record.py``'s freshness guard, in this register: a record and the code
    that produced it cannot drift apart silently.
    """
    live = _sha256(cal.MODULE_PATH)
    for blob in (_clip(), _throughput()):
        assert blob["provenance"]["module_sha256"] == live, blob["provenance"]["module"]
        assert blob["provenance"]["module"] == "scripts/phase25_calibrate.py"
        assert blob["provenance"]["calibration_prefix"] == cal.CALIBRATION_PREFIX
        assert blob["provenance"]["git_sha"]
        assert blob["provenance"]["torch_version"] and blob["provenance"]["python_version"]


def test_the_freshness_guard_goes_red_on_one_edited_byte(tmp_path):
    """WATCHED RED, by hand, on a COPY. The real tree is never touched.

    One byte of a ``tmp_path`` copy of the module is changed and the same comparison the guard
    above makes is re-run against it. A guard nobody has seen fail is not evidence.
    """
    original = cal.MODULE_PATH.read_bytes()
    recorded = _clip()["provenance"]["module_sha256"]
    assert hashlib.sha256(original).hexdigest() == recorded

    edited = tmp_path / "phase25_calibrate.py"
    edited.write_bytes(original + b"\n# one byte more\n")
    assert hashlib.sha256(edited.read_bytes()).hexdigest() != recorded

    # ...and the real tree is still clean, byte for byte.
    assert cal.MODULE_PATH.read_bytes() == original
    assert _sha256(cal.MODULE_PATH) == recorded
