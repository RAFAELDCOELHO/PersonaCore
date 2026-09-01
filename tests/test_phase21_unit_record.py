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
import subprocess
import sys

import numpy as np
import pytest

from personacore.provenance import refuse_if_dirty

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import mitigation_unit as mu  # noqa: E402
import phase21_unit_record as r  # noqa: E402
import teach_persona as tp  # noqa: E402


def _git(*args, cwd):
    """``git`` at ``cwd``, argv-style. Never ``shell=True``; see test_phase20_prereg.py:141."""
    return subprocess.run(
        ("git", *args), cwd=cwd, capture_output=True, text=True, check=True
    ).stdout.strip()


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


def test_the_n8_reproduction_claim_is_computed_and_could_have_been_false(unit):
    """WR-01: the flag is the RESULT of the comparison it claims, and the comparison can fail.

    It shipped as the Python literal `True` with nothing evaluating it, and it was FALSE at the
    precision it claimed: the 3-window row measured 0.4210 against D-24's documented 0.4211. A
    flag no code computes is the guard-that-cannot-fail class this phase has spent eleven plans
    removing, so asserting the flag alone would repeat the defect one level up — this test
    RECOMPUTES the comparison from the artifact's own published rows and then, separately, shows
    the comparison is capable of returning False.
    """
    table = unit["lot"]["replay_volume"]["d24_candidate_table_reproduced"]
    documented = table["documented_n8_table"]
    assert documented == r.DOCUMENTED_N8_TABLE, (
        "the published table and the constant the flag is checked against must be one object, or "
        "they are two numbers that can drift apart — which is how WR-01 happened"
    )

    n8_rows = {row["windows_per_fact"]: row for row in table["rows"] if row["n_facts"] == 8}
    assert sorted(n8_rows) == [3, 4, 5]
    recomputed = all(
        round(n8_rows[w]["share_of_the_combined_lot"], 4) == documented[str(w)] for w in (3, 4, 5)
    )
    assert table["n8_rows_reproduce_the_documented_table"] is recomputed, (
        "the published flag disagrees with the artifact's own rows — it is not a computation of "
        "what it claims to be a computation of"
    )
    assert recomputed is True, {w: n8_rows[w]["share_of_the_combined_lot"] for w in (3, 4, 5)}

    # NON-VACUITY. The same predicate on the denominator the artifact USED TO carry (the padded
    # bin, tail included) returns False, reproducing WR-01's measurement exactly. Without this the
    # assertion above would be satisfied by a predicate that is True for every input.
    with_tail = all(
        round(
            r._share_of_the_combined_lot(
                w * 8 * r.BLOCK_SIZE,
                {"trainable_tokens": n8_rows[w]["aligned_teaching_bin_tokens_padded"]},
            ),
            4,
        )
        == documented[str(w)]
        for w in (3, 4, 5)
    )
    assert with_tail is False, (
        "the reproduction check passes against BOTH denominators, so it cannot distinguish them "
        "and its True says nothing. WR-01 measured 0.4210 vs 0.4211 on the 3-window row; if that "
        "gap has closed, the corpus or the block size changed and the reconciliation below needs "
        "re-deriving rather than re-asserting."
    )


def test_the_share_denominator_is_the_one_that_is_unit_invariant(unit):
    """WR-01's reconciliation, checkable from the artifact alone: 8448 vs 8449, decided.

    The choice is not a rounding preference and is not "whichever makes the flag True". A share is
    a share only if it does not depend on the unit it is counted in, and the numerator
    (`replay_window_budget`) is a whole number of windows with remainder exactly 0 — so the
    window-basis and token-basis shares must agree. They agree bit-for-bit only when the
    denominator excludes the label-shift tail.

    This also pins the thing that proves the correction was not self-serving: the load-bearing
    claim in the same block, `documented_n64_claim_holds`, is False before and after.
    """
    table = unit["lot"]["replay_volume"]["d24_candidate_table_reproduced"]

    for row in table["rows"]:
        # The bin is `total_windows * block_size + 1` (CR-01 made this an enforced contract).
        assert row["aligned_teaching_bin_trainable_tokens"] == (
            row["aligned_teaching_bin_windows"] * tp.BLOCK_SIZE
        )
        assert row["aligned_teaching_bin_tokens_padded"] == (
            row["aligned_teaching_bin_trainable_tokens"] + 1
        )
        # The numerator is tail-free BY CONSTRUCTION — this is what forces the denominator's unit.
        assert row["replay_tokens"] == row["replay_windows"] * tp.BLOCK_SIZE
        # UNIT INVARIANCE: exact equality, not approx. A tolerance here would admit 8449 back.
        assert row["share_of_the_combined_lot"] == row["share_computed_in_windows"], (
            f"w={row['windows_per_fact']} n={row['n_facts']}: the share differs between the "
            "window basis and the token basis, so it is not a share of anything consistent"
        )
        # And the tail-bearing denominator is measurably NOT unit-invariant, at the one row where
        # a single token is visible at 4 decimals.
        if row["windows_per_fact"] == 3 and row["n_facts"] == 8:
            with_tail = row["replay_tokens"] / (
                row["replay_tokens"] + row["aligned_teaching_bin_tokens_padded"]
            )
            assert with_tail != row["share_computed_in_windows"]

    assert table["documented_n64_claim_holds"] is False, (
        "the n=64 claim is the load-bearing one in this block and it must survive the denominator "
        "correction unchanged. If it ever reads True, check that the denominator was not chosen "
        "to make it so."
    )
    assert table["linear_premise_equals_the_n8_share"] is True, (
        "under the corrected denominator the linear premise predicts EXACTLY the n=8 share, which "
        "is what makes 'the documented 49.90% does not follow from its own stated reason' an "
        "arithmetic statement rather than an approximate one"
    )

    # The same quantity must not appear twice with two answers. The `lot` block's pinned-constant
    # share and the candidate table's `is_the_pinned_constant` rows are one number.
    pinned = {
        row["n_facts"]: row["share_of_the_combined_lot"]
        for row in table["rows"]
        if row["is_the_pinned_constant"]
    }
    for observed in unit["lot"]["replay_volume"]["observed_share_of_the_padded_bin"]:
        assert observed["share_of_the_combined_lot"] == pinned[observed["n_facts"]]
        assert observed["denominator"].endswith("aligned_teaching_bin_trainable_tokens")


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


@pytest.mark.parametrize(
    "key,emitter", [("privacy_unit", "emit_privacy_unit"), ("multiplicity", "emit_multiplicity")]
)
def test_the_recorded_git_sha_names_a_commit_where_the_emitter_exists(key, emitter):
    """CR-02: the SHA an artifact records must be a commit that could have produced it.

    The reproducibility guarantee this whole project rests on (CLAUDE.md, QA-02) is "seed + git
    SHA + config-embedded-in-checkpoint". An artifact whose recorded SHA predates its own emitter
    cannot be regenerated from the commit it names, so the guarantee is false on precisely the two
    files that exist to demonstrate it.

    It WAS false. Measured at review time, and reproduced here as the reason this test exists:

        results/phase21_privacy_unit.json  git_sha fa97b666 -> `def emit_privacy_unit` x0
        results/phase21_multiplicity.json  git_sha 17b3c856 -> `def emit_multiplicity` x0

    (The file `scripts/phase21_unit_record.py` DOES exist at both commits — 21-REVIEW.md's table
    is right that the EMITTER is absent, and the sharper reading "the script was absent entirely"
    is not. At fa97b666 it is the 21-10 counter-only revision, six functions, no `_provenance` at
    all; at 17b3c856 `emit_privacy_unit` is present but `emit_multiplicity` is not.)

    The ancestry guard in `tests/test_phase20_prereg.py` cannot see this class: it checks commit
    ORDERING between the pin and the artifact, never whether the recorded SHA can produce the
    bytes. A well-ordered commit carrying a false SHA is invisible to it and fatal to the record.

    Checked with `git cat-file`, so it reads the commit's OWN tree rather than the working copy.
    """
    document = _load(key)
    sha = document["provenance"]["git_sha"]
    assert sha != "unknown", (
        "git_sha() degraded to its 'unknown' default, so this record names no commit at all. "
        "That fallback exists so a Kaggle run never dies on a missing .git; it must never reach "
        "a published artifact."
    )
    blob = subprocess.run(
        ("git", "cat-file", "-p", f"{sha}:scripts/phase21_unit_record.py"),
        cwd=_ROOT,
        capture_output=True,
        text=True,
    )
    assert blob.returncode == 0, (
        f"{r.ARTIFACTS[key].name} records git_sha {sha}, but scripts/phase21_unit_record.py does "
        f"not exist in that commit's tree — the artifact names a tree it cannot come from."
    )
    assert f"def {emitter}" in blob.stdout, (
        f"{r.ARTIFACTS[key].name} records git_sha {sha[:8]}, but `def {emitter}` is not defined "
        f"in scripts/phase21_unit_record.py at that commit. The recorded SHA does not identify "
        f"the code that produced this file, so the record cannot be regenerated from it "
        f"(21-REVIEW.md CR-02). Re-emit from a CLEAN tree via `python scripts/phase21_emit.py`."
    )


def test_publishing_from_a_dirty_tree_is_refused(tmp_path):
    """The mechanism that makes CR-02 unrepeatable, proved CLEAN-then-DIRTY in a throwaway repo.

    Exercised against a scratch repository rather than this one because the assertion must be
    about the GUARD, not about whatever state the developer's working tree happens to be in. A
    test that passed only on a clean checkout would be reporting the tree, not the code.

    Both directions are asserted. A refusal that fires unconditionally would be useless in exactly
    the same way a hardcoded `True` is (WR-01, one finding over): it would prove nothing about the
    tree, so the clean arm is what makes the dirty arm mean something.
    """
    _git("init", "-q", cwd=tmp_path)
    _git("config", "user.name", "phase21-fixture", cwd=tmp_path)
    _git("config", "user.email", "phase21-fixture@localhost", cwd=tmp_path)
    (tmp_path / "emitter.py").write_text("def emit(): ...\n", encoding="utf-8")
    _git("add", "emitter.py", cwd=tmp_path)
    _git("commit", "-q", "-m", "emitter", cwd=tmp_path)

    # CLEAN: returns the empty status and does not raise.
    assert refuse_if_dirty(who="probe", detail="d", cwd=tmp_path) == ""

    # DIRTY: the same call refuses, and the abort names the offending path.
    (tmp_path / "emitter.py").write_text("def emit(): return 1\n", encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        refuse_if_dirty(who="probe", detail="the SHA would not reproduce this", cwd=tmp_path)
    assert "emitter.py" in str(excinfo.value)
    assert "the SHA would not reproduce this" in str(excinfo.value)

    # UNTRACKED counts as dirty too: a .py that is not in HEAD cannot be at the recorded SHA.
    _git("checkout", "--", "emitter.py", cwd=tmp_path)
    assert refuse_if_dirty(who="probe", detail="d", cwd=tmp_path) == ""
    (tmp_path / "helper.py").write_text("X = 1\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        refuse_if_dirty(who="probe", detail="d", cwd=tmp_path)


def test_the_dirty_guard_is_scoped_to_the_published_paths(tmp_path):
    """It fires on the two committed records and on nothing else — checked by RESOLVED path.

    The scope is the reason `test_driver_refuses_to_rerun` below can still write into `tmp_path`
    while this repository is mid-edit. It is also the reason the scope cannot be "anything named
    phase21_privacy_unit.json": a fixture in a temp directory shares that basename and is thrown
    away by the process that wrote it, so there is no permanent record for a SHA to be false about.
    """
    for artifact in r.ARTIFACTS.values():
        assert r.is_publication_target(artifact)
        # A relative spelling and a `..` detour name the same file and must answer the same.
        assert r.is_publication_target(artifact.relative_to(_ROOT))
        assert r.is_publication_target(artifact.parent / ".." / "results" / artifact.name)

    decoy = tmp_path / "phase21_privacy_unit.json"
    assert not r.is_publication_target(decoy), (
        "a same-basename fixture in a temp directory is not the published record; treating it as "
        "one would tie the test suite's outcome to the working tree's git state"
    )
    assert r.refuse_dirty_publication(decoy) is None


def test_driver_refuses_to_rerun(tmp_path, monkeypatch):
    """A second write into the same path aborts, naming the file — recorded evidence is not
    silently replaced by a rerun on drifted code.

    ``teach_persona.refuse_if_exists`` is IMPORTED rather than reimplemented, so there is one
    refuse-to-rerun in this repository and not two. The privacy-unit emitter is the one exercised
    here because it is the cheap one; both emitters route their write through the same guarded
    ``_write``.

    The first write still has to MEASURE: ``emit_privacy_unit`` builds the n=8 replay-in-bin row
    through ``tp.build_bins(..., replay_ratio=1.0)``, which refuses unless ``DIALOG_TRAIN_BIN``
    exists. ``data/`` is gitignored and never in CI, so a synthetic replay pair is monkeypatched
    here — the same pattern as ``tests/test_phase21_replay_volume.py::replay_source``. This test
    is about refuse-to-rerun, not about the real PersonaChat memmap.
    """
    n = 20_000  # > dp_n8's legacy replay slice (~7.5k teaching tokens)
    replay_bin = tmp_path / "synthetic_dialog_train.bin"
    replay_mask = tmp_path / "synthetic_dialog_train_mask.bin"
    rng = np.random.default_rng(1337)
    rng.integers(0, 8184, size=n, dtype=np.uint16).tofile(replay_bin)
    np.ones(n, dtype=np.uint8).tofile(replay_mask)
    monkeypatch.setattr(tp, "DIALOG_TRAIN_BIN", replay_bin)
    monkeypatch.setattr(tp, "DIALOG_TRAIN_MASK", replay_mask)

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
