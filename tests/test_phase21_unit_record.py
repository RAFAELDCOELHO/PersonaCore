"""The ARTIFACT guards for plan 21-11: schema, provenance-from-the-pin, and refuse-to-rerun.

``tests/test_phase21_multiplicity.py`` (plan 21-10) proves the INSTRUMENT counts. This file
guards the RECORD the instrument produced: that every field SC1/SC3/SC4 require is present, that
every pinned value in it was computed from :mod:`mitigation_unit` rather than retyped, and that
the driver refuses to silently replace a recorded artifact.

WHY THESE TESTS READ THE ARTIFACT FROM DISK RATHER THAN REGENERATING IT
-----------------------------------------------------------------------
The published file is the deliverable. Regenerating in-process and asserting on the fresh dict
would guard the CODE PATH and say nothing about the bytes that ship — an artifact truncated,
hand-edited, or written by an older revision of the emitter would sail through. So the schema and
value tests load ``results/phase21_*.json`` and check THOSE, while
:func:`test_driver_refuses_to_rerun` exercises the write path into ``tmp_path``.

The single exception is deliberate: ``test_artifact_values_come_from_the_pin`` re-imports the pin
and recomputes every pinned quantity, then asserts the ON-DISK value equals it. That is what stops
the pre-registration and the published record drifting into two sources of truth — the failure
mode T-21-50 names, and the one the ancestry guard alone cannot catch because a retyped constant
is a perfectly well-ordered commit.

CPU-only, no GPU, no network.
"""

import json
import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import mitigation_unit as mu  # noqa: E402
import phase21_unit_record as r  # noqa: E402
import teach_persona as tp  # noqa: E402


def _load(key):
    path = r.ARTIFACTS[key]
    assert path.exists(), (
        f"{path} is missing. Plan 21-11 writes both results/phase21_* artifacts; every test below "
        "guards the PUBLISHED bytes rather than a freshly regenerated dict, so an absent file is a "
        "missing deliverable and not a skip."
    )
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def unit():
    return _load("privacy_unit")


@pytest.fixture(scope="module")
def multiplicity():
    return _load("multiplicity")


# =================================================================================================
# results/phase21_privacy_unit.json — SC1 (UNIT-01) + SC4 (UNIT-04, UNIT-05)
# =================================================================================================


def test_privacy_unit_artifact_schema(unit):
    """Every block SC1 and SC4 require is present, and no epsilon is claimed.

    ``epsilon_computed is False`` is asserted as an IDENTITY rather than a truthiness check: a
    string ``"false"`` is truthy in Python and would pass ``not unit[...]`` nowhere but would pass
    a sloppier assertion here. Phase 21 computes no epsilon anywhere — the artifact is a UNIT and
    the data path that makes it real — and T-21-54 exists because publishing one would be a bound
    with no mechanism behind it.
    """
    assert set(unit) == {"unit", "lot", "delta", "provenance"}

    assert set(unit["unit"]) >= {
        "privacy_unit",
        "privacy_n_rule",
        "rationale",
        "measured_multiplicity",
        "pin_arithmetic",
    }
    # The rationale must name the DRAW, not merely assert the conclusion.
    assert "np.random.randint" in unit["unit"]["rationale"]
    assert "get_batch_memmap_masked" in unit["unit"]["rationale"]
    # SC1's measurement lives in the sibling artifact and is POINTED AT, never restated.
    assert "results/phase21_multiplicity.json" in unit["unit"]["measured_multiplicity"]

    lot = unit["lot"]
    assert set(lot) >= {
        "sampling_rate_q",
        "privacy_n_rule",
        "replay_in_lot",
        "replay_inside_privacy_n",
        "epsilon_consequence",
        "replay_volume",
    }
    assert lot["replay_in_lot"] is True
    assert lot["replay_inside_privacy_n"] is False, (
        "D-07: replay sits OUTSIDE the privacy N. Counting it inside would shrink q and buy a "
        "flatteringly small epsilon about a lot containing data no adversary cares about."
    )
    assert set(lot["replay_volume"]) >= {
        "replay_windows_per_fact",
        "replay_tokens_per_fact",
        "replay_tokens_at_n8",
        "replay_tokens_at_n64",
        "observed_share_of_the_padded_bin",
        "separate_pass_per_lot",
        "rejected_raw_constant",
    }

    delta = unit["delta"]
    assert set(delta) >= {"delta", "ceiling", "rejected_recipe", "capacities"}
    assert [row["n"] for row in delta["capacities"]] == [8, 64], (
        "BOTH capacities this milestone runs, in order. A record checked only at n=8 leaves open "
        "the reading that the rejected recipe's failure was an artefact of the small arm."
    )
    for row in delta["capacities"]:
        assert set(row) == {
            "n",
            "pinned_delta_times_n",
            "pinned_margin",
            "rejected_delta",
            "rejected_delta_times_n",
            "rejected_overshoot_multiple",
        }

    prov = unit["provenance"]
    assert set(prov) >= {
        "git_sha",
        "written_utc",
        "python",
        "seed",
        "pin_module",
        "pin_sha256",
        "epsilon_computed",
    }
    assert prov["epsilon_computed"] is False
    assert prov["pin_module"] == "scripts/mitigation_unit.py"


def test_artifact_values_come_from_the_pin(unit):
    """Every pinned value on disk EQUALS a value freshly recomputed from :mod:`mitigation_unit`.

    This is the whole reason the driver imports the pin instead of retyping it. The ancestry guard
    proves the pin was committed BEFORE the artifact; it cannot prove the artifact SAYS what the
    pin says. A transcription error inside a correctly-ordered commit is invisible to ordering and
    fatal to the record, so it is checked here (T-21-50).

    The two ``rejected_delta`` products use ``pytest.approx(rel=1e-12)`` for the same reason
    ``tests/test_phase21_unit_pin.py`` does: ``n ** -1.1`` routes through the platform's libm
    ``pow``, which is not bit-identical across CPU families (commit 4554c93). That tolerance is
    ~4 orders looser than a 1-ulp disagreement and ~14 orders tighter than the 66x-81x effect
    being asserted, so it cannot mask the finding.
    """
    assert unit["unit"]["privacy_unit"] == mu.PRIVACY_UNIT
    assert unit["unit"]["pin_arithmetic"] == mu.PRIVACY_UNIT_ARITHMETIC
    assert unit["lot"]["sampling_rate_q"] == mu.SAMPLING_RATE_Q
    assert unit["lot"]["epsilon_consequence"] == mu.REPLAY_OUTSIDE_N
    assert unit["delta"]["delta"] == mu.DELTA
    assert unit["delta"]["ceiling"] == mu.DELTA_TIMES_N_CEILING
    assert unit["delta"]["rejected_recipe"] == mu.REJECTED_DELTA_RECIPE
    assert unit["delta"]["rejected_recipe_reason"] == mu.REJECTED_DELTA_REASON

    for row in unit["delta"]["capacities"]:
        n = row["n"]
        assert n == mu.privacy_n(n)
        assert row["pinned_delta_times_n"] == mu.DELTA * n
        assert row["pinned_margin"] == mu.DELTA_TIMES_N_CEILING / (mu.DELTA * n)
        assert row["rejected_delta"] == pytest.approx(mu.rejected_delta(n), rel=1e-12)
        assert row["rejected_delta_times_n"] == pytest.approx(mu.rejected_delta(n) * n, rel=1e-12)
        assert row["rejected_overshoot_multiple"] == pytest.approx(
            mu.rejected_delta(n) * n / mu.DELTA_TIMES_N_CEILING, rel=1e-12
        )
        # The record's WHOLE point: the pinned literal passes and the rejected recipe fails, at
        # BOTH capacities. Asserted as inequalities, which have 15x-81x of margin and need no slack.
        assert row["pinned_delta_times_n"] < mu.DELTA_TIMES_N_CEILING
        assert row["rejected_delta_times_n"] >= mu.DELTA_TIMES_N_CEILING

    # The replay volume is likewise DERIVED, from the one function that computes it (D-11/D-24).
    volume = unit["lot"]["replay_volume"]
    assert volume["replay_windows_per_fact"] == tp.REPLAY_WINDOWS_PER_FACT
    assert volume["replay_tokens_per_fact"] == tp.REPLAY_WINDOWS_PER_FACT * tp.BLOCK_SIZE
    assert volume["replay_tokens_at_n8"] == tp.replay_window_budget(8)
    assert volume["replay_tokens_at_n64"] == tp.replay_window_budget(64)


def test_the_artifact_records_the_pin_it_was_written_against(unit):
    """``pin_sha256`` is the digest of the pin file as it stands, and it is 21-01's frozen value.

    A second, INDEPENDENT witness to the freeze, running on file bytes rather than git history.
    The ancestry guard reads ``git log``; this reads the file. If the pin is ever edited, this goes
    red immediately and locally, without needing a new artifact commit to expose it.
    """
    import hashlib

    pin = _ROOT / "scripts" / "mitigation_unit.py"
    assert unit["provenance"]["pin_sha256"] == hashlib.sha256(pin.read_bytes()).hexdigest()
    assert (
        unit["provenance"]["pin_sha256"]
        == "45f37e152bb4035667b804c1463431b3f12fa5096c47de32b1dc27abbe000473"
    ), (
        "the pin's digest is not 21-01's recorded frozen value — scripts/mitigation_unit.py has "
        "been edited since it was pinned, which permanently reddens "
        "test_phase21_prereg_is_frozen_before_every_phase21_result. Corrections after the first "
        "results/phase21_* commit are dated continuations via scripts/_addendum.py, never edits."
    )


def test_driver_refuses_to_rerun(tmp_path):
    """A second write into the same path aborts, naming the file — recorded evidence is not
    silently replaced by a rerun on drifted code.

    ``teach_persona.refuse_if_exists`` is IMPORTED rather than reimplemented, so there is one
    refuse-to-rerun in this repository and not two. The privacy-unit emitter is the one exercised
    here because it is the cheap one; both emitters route their write through the same guarded
    ``_write``.
    """
    target = tmp_path / "phase21_privacy_unit.json"
    r.emit_privacy_unit(path=target, workdir=tmp_path)
    assert target.exists()

    with pytest.raises(SystemExit) as excinfo:
        r.emit_privacy_unit(path=target, workdir=tmp_path)
    assert str(target) in str(excinfo.value)


# =================================================================================================
# results/phase21_multiplicity.json — SC3 (UNIT-03), D-26
# =================================================================================================


def test_multiplicity_rows_carry_the_full_schema(multiplicity):
    """Every row carries ``ROW_SCHEMA`` plus its analytic expectation — 14 required keys.

    D-26 makes the LABEL and the denominators part of the row, because SC3's own phrasing ("at the
    chosen replay_ratio") predates D-10 moving replay out of the teaching bin entirely. A row that
    lost its ``bin_composition`` would re-open exactly the ambiguity the label closes, and a row
    that lost a denominator would publish a multiplicity nobody can reproduce.
    """
    required = set(r.ROW_SCHEMA) | {"analytic_expectation"}
    assert len(required) == 14
    for row in multiplicity["rows"]:
        missing = required - set(row)
        assert not missing, f"row {row.get('bin_composition')!r} is missing {sorted(missing)}"
        assert row["attribution_rule"] == r.ATTRIBUTION_RULE
        assert row["bin_composition"] in r.BIN_COMPOSITION_LABELS

    labels = [row["bin_composition"] for row in multiplicity["rows"]]
    assert set(labels) == set(r.BIN_COMPOSITION_LABELS), (
        "all THREE published compositions must appear. A row silently omitted because a source "
        "bin was unavailable is worse than a row that says how it was produced (T-21-53)."
    )
    assert sorted({row["n_facts"] for row in multiplicity["rows"]}) == [8, 64], (
        "both capacities this milestone runs, so the record cannot be read as an n=8 artefact"
    )


def test_unaligned_rows_conserve_their_budget(multiplicity):
    """``sum(counts) == total_draws`` exactly, and on the replay row replay carries the remainder.

    The conservation law is the load-bearing instrument test: under ``first-token-owns-draw`` it
    is an EQUALITY with nothing to tune. Plan 21-10 watched it go RED at 1,993 against 1,600 under
    the rejected rule.
    """
    for row in multiplicity["rows"]:
        if row["bin_composition"] == r.BIN_COMPOSITION_LABELS[2]:
            continue  # the aligned row's law is per-step, checked in its own test below
        landed = sum(row["counts"].values())
        replay = row.get("replay_draws", 0)
        assert landed + replay == row["total_draws"], (
            f"{row['bin_composition']}: {landed} fact draws + {replay} replay draws != "
            f"{row['total_draws']} — a draw was lost or credited twice"
        )
        assert row["total_draws"] == r.MAX_STEPS * r.BATCH_SIZE
        assert row["seed"] == r.SEED


def test_aligned_rows_report_a_deterministic_one_at_both_capacities(multiplicity):
    """The fact-aligned rows measure exactly 1 per micro-step, with zero spread, at n=8 AND n=64.

    ``mean == 1.0`` is an OBSERVATION from a counter proven able to report otherwise — plan 21-10
    measured ``per_step_distinct_facts == [2, 2, 2, 2, 2, 2, 2, None]`` on a deliberately rolled
    bin — so this is not a tautology dressed as a measurement (T-21-51). ``min == max == 1`` is
    asserted alongside the mean because a mean of 1.0 is also what ``{0: 0, 1: 2}`` produces.
    """
    aligned = [
        row for row in multiplicity["rows"] if row["bin_composition"] == r.BIN_COMPOSITION_LABELS[2]
    ]
    assert len(aligned) == 2
    for row in aligned:
        assert row["min"] == 1 and row["max"] == 1, row["counts"]
        assert row["mean"] == 1.0
        assert row["spread"] == 0
        assert row["steps"] == row["n_facts"] == row["lot_length_steps"], (
            "one FULL LOT: steps must equal n_facts, or some record never entered the lot"
        )
        assert sum(row["counts"].values()) == row["n_facts"]
        assert row["per_step_raised"] == [None] * row["n_facts"], (
            "a step that raised would mean a mis-built bin reached a published row"
        )
        assert set(row["per_step_distinct_facts"]) == {1}, (
            "SC2: one window, one fact. This is the OBSERVED distinct-id count per step, which is "
            "what makes 'one micro-step is one privacy record' verified rather than assumed."
        )


def test_analytic_expectation_sits_beside_the_measurement_never_in_place_of_it(multiplicity):
    """Both rules' closed forms are named, and on the unaligned rows they DIFFER from the measured
    value — which is what proves the analytic number was not published as the measurement.

    UNIT-03 refuses exactly that substitution (T-21-51). The check is not cosmetic: on the
    ``facts-only`` n=8 row the measured mean is the conservation-pinned 200.0 while the first-token
    closed form is 207.018, so an emitter that had written the analytic number into ``mean`` would
    fail here.
    """
    for row in multiplicity["rows"]:
        analytic = row["analytic_expectation"]
        assert "ANALYTIC" in analytic["labelled"]
        assert analytic["rule_this_row_was_counted_under"] == r.ATTRIBUTION_RULE
        assert {"first_token_rule", "overlap_rule"} <= set(analytic)
        if row["bin_composition"] == r.BIN_COMPOSITION_LABELS[2]:
            continue
        assert analytic["which_one_matches_this_row"] == "first_token_rule"
        assert row["mean"] != analytic["first_token_rule"]
        assert row["mean"] != analytic["overlap_rule"]
        # The gap between the two rules is the whole 262.94-vs-207.02 story, one row down.
        assert analytic["overlap_rule"] - analytic["first_token_rule"] == pytest.approx(
            analytic["gap_between_the_two_rules"], rel=1e-12
        )


def test_corpus_geometry_is_observed_and_discharges_a3(multiplicity):
    """The n=8 geometry reproduces D-01's measured table; the n=64 total is OBSERVED, not assumed.

    ``21-RESEARCH.md`` A3 estimated ~264 windows at n=64 and marked itself
    ``[ASSUMED — depends on values not yet minted]``. This asserts the artifact published the
    MEASURED total and recorded that it differs, rather than adjusting the corpus to hit 264
    (T-21-52).
    """
    geometry = {geo["n_facts"]: geo for geo in multiplicity["corpus_geometry"]}
    assert sorted(geometry) == [8, 64]

    n8 = geometry[8]
    assert n8["windows_per_fact"] == [4, 4, 4, 4, 4, 5, 4, 4], (
        "D-01's measured ragged geometry, recovered here from the real packer. A divergence is a "
        "finding to publish, not a number to smooth."
    )
    assert n8["total_windows"] == 33
    assert n8["pad_tokens"] == 867
    assert n8["teaching_tokens"] == 7581
    assert n8["total_tokens"] == 33 * tp.BLOCK_SIZE + 1

    for geo in geometry.values():
        assert geo["grad_accum_steps"] == geo["n_facts"], (
            "grad_accum_steps is the OBSERVED micro-step count of one full lot (SC2), asserted "
            "against n_facts rather than declared equal to it"
        )
        assert "OBSERVED" in geo["grad_accum_steps_source"]
        assert geo["replay_tokens_per_lot"] == tp.replay_window_budget(geo["n_facts"])
        assert geo["total_tokens"] == geo["total_windows"] * tp.BLOCK_SIZE + 1
        assert sum(geo["windows_per_fact"]) == geo["total_windows"]

    a3 = multiplicity["a3_discharge"]
    assert a3["assumed_total_windows"] == 264
    assert a3["observed_total_windows"] == geometry[64]["total_windows"]
    assert a3["holds"] is (a3["observed_total_windows"] == 264)
    assert a3["holds"] is False, (
        "A3 assumed 264 windows at n=64; the measurement is published as taken. If this ever "
        "becomes True the corpus changed — check that it was not adjusted to fit the assumption."
    )


def test_the_pin_discrepancy_is_recorded_and_reconciles_exactly(multiplicity):
    """Both figures, both rules, and the exact reconciliation — and the pin is NOT edited.

    Plan 21-10 measured that the frozen pin's 262.9437 is the OVERLAP rule's number, i.e. the
    alternative ``ATTRIBUTION_RULE`` rejects. Neither is wrong. The artifact's duty is to record
    the discrepancy so nobody quotes 262.9437 as this rule's measurement, and to state that a
    correction to the pin is a dated continuation rather than an edit — because from the first
    ``results/phase21_*`` commit an edit permanently reddens the ancestry guard and
    ``adds[-1]`` means a delete-and-re-add cannot launder it.
    """
    pin = multiplicity["pin_discrepancy"]
    assert pin["artifact_rule"] == r.ATTRIBUTION_RULE
    assert pin["pin_figure"] == pytest.approx(262.9437, abs=5e-5)
    assert pin["artifact_rule_figure"] == pytest.approx(207.018, abs=5e-4)
    assert pin["pin_figure"] - pin["gap_per_interior_fact"] == pytest.approx(
        pin["artifact_rule_figure"], rel=1e-12
    ), "the two figures must reconcile EXACTLY, or one of them really is wrong"
    assert pin["conservation_pinned_mean"] == (r.MAX_STEPS * r.BATCH_SIZE) / 8
    assert "_addendum.py" in pin["how_a_correction_would_be_made"]
    assert "NOT RESOLVED" in pin["status"]


def test_the_findings_carry_both_measured_numbers(multiplicity):
    """The D-10 interaction is published with BOTH multiplicities, not as a claim about one.

    "Moving replay out of the bin doubles the unaligned multiplicity" is only a finding if both
    numbers exist; with one it is an assertion. The ratio is therefore recomputed here from the
    rows themselves, so the findings block cannot drift from the measurement it summarises.
    """
    finding = multiplicity["findings"]["d10_doubles_the_unaligned_multiplicity"]
    rows = {
        row["bin_composition"]: row
        for row in multiplicity["rows"]
        if row["n_facts"] == 8 and row["bin_composition"] != r.BIN_COMPOSITION_LABELS[2]
    }
    assert finding["replay_in_bin"]["mean_over_facts"] == rows[r.BIN_COMPOSITION_LABELS[0]]["mean"]
    assert finding["facts_only"]["mean_over_facts"] == rows[r.BIN_COMPOSITION_LABELS[1]]["mean"]
    assert finding["ratio_of_the_means"] == pytest.approx(
        finding["facts_only"]["mean_over_facts"] / finding["replay_in_bin"]["mean_over_facts"],
        rel=1e-12,
    )
    assert finding["ratio_of_the_means"] > 2.0, (
        "the measured effect is a DOUBLING or worse — a decision taken for honest accounting "
        "made the unaligned number worse, which strengthens UNIT-01's indictment"
    )

    channel = multiplicity["findings"]["d11_teaching_tokens_side_channel"]
    lengths = channel["per_fact_token_lengths"]
    assert len(lengths) == 8 and sum(lengths) == 7581
    assert max(lengths) - min(lengths) > 0, (
        "the side channel is measurable only because the per-fact lengths differ; a uniform "
        "corpus would leak nothing here and the defect would have been invisible"
    )
