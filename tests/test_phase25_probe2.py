"""PLAN 25-13 — D-04's PROBE 2 RECORD, GUARDED BY RE-DERIVATION RATHER THAN BY RESTATEMENT.

`results/phase25_probe2_tensors.json` is a **prediction**: it records, before any sweep point
exists, how far the sigma=0 DP path differs from the seam-off path at BOTH capacities. Its value
comes entirely from being committed in advance and bounded honestly, so every guard here recomputes
the record's own claims from the record's own rows instead of checking a number is present.

**WHAT THIS FILE REFUSES, AND WHY EACH REFUSAL IS THE ONE THAT MATTERS:**

  * **A bound of exactly `0.0`.** That is a BIT-IDENTITY claim, which is precisely what D-04
    forbids. CTRL-02's own body already records that chasing bit-identity between the control and
    the seam-off path would be a mistake.
  * **An aggregate that no longer describes its rows.** `agreeing` is RECOMPUTED from the
    per-tensor rows under exact equality, and the recomputation is watched going RED on a
    perturbed copy of the record (T-25-69).
  * **A transcribed declared difference.** Phase 23's four entries are re-read live from
    `results/phase23_matched_control.json` and compared field by field, with the digest recomputed
    from bytes (T-25-68).
  * **A renamed control.** `dp_n8` / `dp_n64` and `separated_by: prefix` are asserted as structural
    fields; only the `dp_fn=None` comparator carries a distinct arm name (D-06, T-25-67).
  * **A record written after the fact.** The probe's commit is asserted to be an ancestor of every
    committed point record, from `git log` (T-25-66).

**THE PLANTED RED GOES INTO `tmp_path`, NEVER INTO `tests/`.** This repository has been burned by
planted REDs landing on the wrong occurrence of a token inside a real file and then being
"reverted" into a false green. The scratch module written below contains exactly one function.

CPU-only: this file reads the committed record and never retrains.
"""

import copy
import hashlib
import json
import pathlib
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import _prose  # noqa: E402  (needs the sys.path insert above)
import phase25_prereg  # noqa: E402  (same reason)
import phase25_probe2 as p2  # noqa: E402  (same reason; CPU-safe at import by construction)
import teach_persona as tp  # noqa: E402  (same reason)

# Plan 25-01's walker, REUSED rather than re-implemented. Two copies of a tripwire drift, and the
# whole claim of section (b) is that THIS phase's artifact sits inside the SAME guard the
# pre-registration armed — not beside a second one that happens to agree today.
from test_phase25_prereg import _assert_no_bit_identity_assertions  # noqa: E402

_RECORD_PATH = _ROOT / "results" / "phase25_probe2_tensors.json"
_CAPACITIES = ("dp_n8", "dp_n64")


def _record():
    assert _RECORD_PATH.exists(), (
        f"{_RECORD_PATH} does not exist. It is written by "
        "`.venv/bin/python scripts/phase25_probe2.py` and is the artifact every guard here reads."
    )
    return json.loads(_RECORD_PATH.read_text(encoding="utf-8"))


def _rederive_agreeing(rows, bound):
    """Count rows whose ``max_rel_diff`` is within ``bound`` — the aggregate's own definition.

    ONE copy of the recomputation, used by the live guard and by the watched RED, so the two can
    never check different arithmetic.
    """
    return sum(1 for row in rows if row["max_rel_diff"] <= bound)


def _git(*args):
    return subprocess.run(["git", *args], cwd=_ROOT, capture_output=True, text=True, check=False)


def _earliest_add(pathspec):
    """The commit that FIRST added ``pathspec``, or ``None`` if it is not tracked.

    ``--diff-filter=A`` plus the LAST line: ``git log`` prints newest first, so the earliest add is
    the tail. Same reading `tests/test_phase20_prereg.py`'s ancestry guard takes (`adds[-1]`), and
    for the same reason — a later re-add must not be able to launder an earlier one.
    """
    out = _git("log", "--format=%H", "--diff-filter=A", "--", pathspec)
    shas = [line for line in out.stdout.split() if line]
    return shas[-1] if shas else None


# =================================================================================================
# ===== (a) THE RECORD SAYS DISAGREEMENT, NOT EQUALITY =====
# =================================================================================================


def test_the_record_asserts_bounded_disagreement_never_equality():
    """A POSITIVE bound at both capacities, and a `governs` string that says what it governs.

    A recorded bound of exactly `0.0` would be a bit-identity claim about two paths D-04 requires
    to be described as bounded-disagreeing. It fails here rather than being read later as a
    reassuring zero.
    """
    blob = _record()
    bounds = blob["agreement_bound"]
    assert sorted(bounds) == sorted(_CAPACITIES), sorted(bounds)
    for capacity in _CAPACITIES:
        value = bounds[capacity]
        assert isinstance(value, float), (capacity, type(value).__name__, value)
        assert value > 0.0, (
            f"{capacity}: agreement_bound is {value!r}. Exactly 0.0 is a BIT-IDENTITY claim "
            "between the sigma=0 point and the seam-off path — the one assertion D-04 forbids."
        )

    governs = _prose.normalized(blob["agreement_bound_governs"])
    for phrase in (
        "bounded disagreement, never equality",
        "expected floating-point non-associativity",
        "chasing that identity would be a mistake",
    ):
        assert _prose.normalized(phrase).lower() in governs.lower(), phrase


def test_every_tensor_is_individually_recorded():
    """Both capacities present, every row carrying its five fields, aggregate total == row count."""
    blob = _record()
    assert set(blob["per_tensor"]) == set(_CAPACITIES), sorted(blob["per_tensor"])
    required = {"name", "shape", "numel", "max_abs_diff", "max_rel_diff"}
    for capacity in _CAPACITIES:
        rows = blob["per_tensor"][capacity]
        assert rows, f"{capacity}: zero rows — a summary-only record"
        names = [row["name"] for row in rows]
        assert len(set(names)) == len(names), f"{capacity}: duplicate tensor rows"
        for row in rows:
            assert required <= set(row), (capacity, row.get("name"), sorted(row))
            assert row["numel"] > 0 and row["shape"]
            # `max_norm_rel_diff` re-derives EXACTLY from the two values beside it, so no bound in
            # this record rests on a number that cannot be recomputed from the row that carries it.
            if row["ref_max_abs"]:
                assert row["max_norm_rel_diff"] == row["max_abs_diff"] / row["ref_max_abs"], row[
                    "name"
                ]
        aggregate = blob["aggregate"][capacity]
        assert isinstance(aggregate["total"], int) and isinstance(aggregate["agreeing"], int)
        assert aggregate["total"] == len(rows), (capacity, aggregate["total"], len(rows))


def test_the_aggregate_re_derives_from_the_rows():
    """`agreeing` recomputed from the rows under EXACT equality — never a stored second number."""
    blob = _record()
    for capacity in _CAPACITIES:
        rows = blob["per_tensor"][capacity]
        bound = blob["agreement_bound"][capacity]
        expected = _rederive_agreeing(rows, bound)
        assert blob["aggregate"][capacity]["agreeing"] == expected, (
            f"{capacity}: the record claims {blob['aggregate'][capacity]['agreeing']} agreeing "
            f"tensor(s) of {blob['aggregate'][capacity]['total']}, but recomputing from its own "
            f"rows at agreement_bound={bound!r} gives {expected}. The aggregate has stopped "
            "describing its own data."
        )
        assert expected == len(rows), (
            f"{capacity}: agreement_bound is the MAX of the per-tensor relative differences, so "
            f"every row must sit within it. {len(rows) - expected} row(s) do not."
        )


def test_the_re_derivation_goes_red_on_a_perturbed_row():
    """WATCHED RED, on a deep COPY. The committed record is never touched.

    T-25-69's whole hazard is an aggregate that no longer describes its rows. A guard nobody has
    seen fail is not evidence, so one row's `max_rel_diff` is pushed above the bound in a copy and
    the SAME recomputation the live guard runs is watched disagreeing.
    """
    blob = copy.deepcopy(_record())
    original = json.loads(_RECORD_PATH.read_text(encoding="utf-8"))

    capacity = _CAPACITIES[0]
    rows = blob["per_tensor"][capacity]
    bound = blob["agreement_bound"][capacity]
    rows[0]["max_rel_diff"] = bound * 2.0 + 1.0

    perturbed = _rederive_agreeing(rows, bound)
    assert perturbed == blob["aggregate"][capacity]["agreeing"] - 1, perturbed
    with pytest.raises(AssertionError) as fired:
        assert blob["aggregate"][capacity]["agreeing"] == perturbed, (
            f"{capacity}: the record claims {blob['aggregate'][capacity]['agreeing']} agreeing "
            f"tensor(s) of {blob['aggregate'][capacity]['total']}, but recomputing from its own "
            f"rows at agreement_bound={bound!r} gives {perturbed}. The aggregate has stopped "
            "describing its own data."
        )
    assert "has stopped describing its own data" in str(fired.value)

    # ...and the committed record is byte-for-byte what it was.
    assert json.loads(_RECORD_PATH.read_text(encoding="utf-8")) == original


# =================================================================================================
# ===== (b) D-04'S TRIPWIRE COVERS THIS PHASE'S OWN ARTIFACT =====
# =================================================================================================


def test_the_bit_identity_tripwire_covers_this_test_file():
    """Plan 25-01's walker, run over `tests/` WITH this file present.

    The claim is scope, not merely passage: this file lives inside the guard's roots, so a future
    edit here that asserted bit-identity would be caught by the pre-registration's own tripwire
    rather than by a second guard standing beside it.
    """
    assert __file__.startswith(str(_ROOT / "tests")), __file__
    _assert_no_bit_identity_assertions(_ROOT / "tests", _ROOT / "scripts")


def test_a_planted_bit_identity_assertion_here_would_fire(tmp_path):
    """WATCHED FIRING against a scratch module — planted into `tmp_path`, never into `tests/`."""
    planted = tmp_path / "test_planted_probe2_identity.py"
    planted.write_text(
        '"""A SCRATCH COPY. Never imported, never collected, never committed."""\n'
        "\n"
        "import torch\n"
        "\n"
        "\n"
        "def test_the_probe2_adapters_are_byte_identical():\n"
        "    sigma_zero_adapter = load_probe2_adapter(sigma=0.0)\n"
        "    seam_off_adapter = load_probe2_adapter(dp_fn=None)\n"
        "    assert torch.equal(sigma_zero_adapter, seam_off_adapter)\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError) as fired:
        _assert_no_bit_identity_assertions(tmp_path)
    message = str(fired.value)
    assert "test_the_probe2_adapters_are_byte_identical" in message, message
    assert "test_planted_probe2_identity.py" in message, message
    assert "equal" in message, message
    assert "2.178e-07" in message, message

    # The real tree is still clean under the SAME body that just fired...
    _assert_no_bit_identity_assertions(_ROOT / "tests", _ROOT / "scripts")
    # ...and nothing was written into it.
    porcelain = _git("status", "--porcelain", "tests/")
    assert porcelain.stdout.strip() == "", porcelain.stdout


# =================================================================================================
# ===== (c) THE IMPORTED EVIDENCE IS LIVE, NOT TRANSCRIBED =====
# =================================================================================================


def test_the_declared_differences_digest_is_live():
    """The recorded digest, recomputed from `results/phase23_matched_control.json`'s BYTES."""
    blob = _record()
    source = _ROOT / blob["declared_differences_source"]
    assert blob["declared_differences_source"] == "results/phase23_matched_control.json"
    assert source.exists(), source
    live = hashlib.sha256(source.read_bytes()).hexdigest()
    assert blob["declared_differences_source_sha256"] == live, (
        "the embedded declared differences no longer travel with their source's digest: recorded "
        f"{blob['declared_differences_source_sha256']}, live {live}"
    )
    # ...and the pre-registration's own helper agrees, so there is one digest, not two.
    assert live == phase25_prereg.declared_differences_digest()


def test_there_are_exactly_four_declared_differences():
    """Length four, and every embedded entry equal FIELD BY FIELD to the live one."""
    blob = _record()
    embedded = blob["declared_differences"]
    live = phase25_prereg.declared_differences()
    assert len(embedded) == 4, len(embedded)
    assert blob["declared_differences_count"] == 4
    assert len(live) == len(embedded), (len(live), len(embedded))
    for index, (mine, theirs) in enumerate(zip(embedded, live)):
        assert set(mine) == set(theirs), (index, sorted(mine), sorted(theirs))
        for field in sorted(theirs):
            assert mine[field] == theirs[field], (index, field)


# =================================================================================================
# ===== (d) D-06'S LINE, ASSERTED =====
# =================================================================================================


def test_the_control_keeps_its_dp_arm_identity():
    """The control's arms are the two DP arms, and the separation field reads `prefix`."""
    blob = _record()
    identity = blob["control_arm_identity"]
    assert identity["arms"] == ["dp_n8", "dp_n64"], identity["arms"]
    assert tuple(identity["arms"]) == tp.DP_ARMS, (identity["arms"], tp.DP_ARMS)
    assert identity["separated_by"] == "prefix", identity["separated_by"]
    assert identity["prefix"] == p2.cal.CALIBRATION_PREFIX
    why = _prose.normalized(identity["why"])
    assert _prose.normalized("break D-01's bit-level reproduction") in why, why
    # The two precedents D-06 cites, present as data rather than as prose.
    quoted = [entry["precedent"] for entry in identity["precedents"]]
    assert any("declared difference #2" in entry for entry in quoted), quoted
    assert any("matched_arm" in entry for entry in quoted), quoted


def test_only_the_seam_off_comparator_is_renamed():
    """The comparator carries its own arm name; the control does not."""
    blob = _record()
    comparator = blob["seam_off_comparator_arm"]
    assert comparator not in tp.DP_ARMS, comparator
    assert comparator not in tp.ARMS, comparator
    assert comparator == p2.SEAM_OFF_COMPARATOR_ARM

    per_capacity = blob["seam_off_comparator_arms"]
    assert sorted(per_capacity) == sorted(_CAPACITIES), sorted(per_capacity)
    for capacity, name in per_capacity.items():
        assert name == p2.comparator_arm(capacity), (capacity, name)
        assert name not in tp.ARMS and name not in tp.DP_ARMS, name
        assert name != capacity

    rule = _prose.normalized(blob["seam_off_comparator_arm_rule"])
    assert _prose.normalized("break D-01's bit-level reproduction") in rule, rule
    assert _prose.normalized("only the dp_fn=None COMPARATOR is renamed").lower() in rule.lower()


# =================================================================================================
# ===== (e) THE PROBE PRECEDED EVERY SWEEP POINT =====
# =================================================================================================


def test_the_probe_record_predates_every_point_record():
    """D-04 requires the ORDER, so the order is asserted from `git log` rather than trusted."""
    tracked = _git("ls-files", phase25_prereg.POINT_RECORD_GLOB).stdout.split()
    probe_sha = _earliest_add("results/phase25_probe2_tensors.json")

    if not tracked:
        # The pre-registered state: D-04's probe runs BEFORE any real sweep point exists.
        assert True
        return

    assert probe_sha, (
        f"{len(tracked)} point record(s) are committed but "
        "results/phase25_probe2_tensors.json is not tracked. D-04 requires PROBE 2 to precede "
        "every sweep point, and an untracked probe precedes nothing."
    )
    for record in tracked:
        point_sha = _earliest_add(record)
        assert point_sha, record
        ancestry = _git("merge-base", "--is-ancestor", probe_sha, point_sha)
        assert ancestry.returncode == 0, (
            f"{record} was added at {point_sha}, which does not descend from the PROBE 2 commit "
            f"{probe_sha}. D-04 requires the probe to be committed BEFORE any point record."
        )
