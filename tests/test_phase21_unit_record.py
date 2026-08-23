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
