"""PLAN 24-02 — D-09'S ADVERSARIAL SWEEP GRID, RE-DERIVED FROM THE COMMITTED ARTIFACTS.

``scripts/mitigation_budget.py`` cannot compute anything: its literal-only guard
(``tests/test_phase23_budget.py::test_budget_holds_only_literal_constants``) refuses any
module-level node that is not an ``ast.Assign`` and calls ``ast.literal_eval`` on every assigned
value, so ``336 / 176`` — an ``ast.BinOp`` — raises there. The extreme is therefore pinned as a
float literal, and this file is the other half: it COUNTS both operands out of the two committed
records and asserts the quotient under exact ``==``. Without it the pin would be a number with a
comment beside it. The extreme's DIGITS are deliberately not written anywhere below, docstrings
included — they are imported, so a hand-edited pin cannot be matched by a hand-edited expectation.

**EVERY PATH RESOLVES FROM ITS OWNING MODULE'S CONSTANT.** ``phase18_extraction.CORPUS_PATH`` for
the attack corpus, ``phase21_unit_record.ARTIFACTS["multiplicity"]`` for the episode geometry —
never a string literal here. This repository has shipped plans naming paths the code refuses, and a
test that spells a path itself agrees with the plan rather than with the code.

**NO FIGURE IS SPELLED TWICE.** The upper extreme is IMPORTED from ``mitigation_budget`` and never
retyped, so a hand-edited digit in the pin cannot be matched by a hand-edited digit here. The two
operands (336 and 176) ARE written down, because they are what the counting is checked against —
an assertion that a count equals itself would be green and blind at once.
"""

import hashlib
import json
import pathlib
import struct
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import mitigation_budget  # noqa: E402
import phase18_extraction  # noqa: E402
import phase21_unit_record  # noqa: E402

_PROVENANCE = mitigation_budget.ADVERSARIAL_RATIO_GRID_PROVENANCE

# The two operands the pin claims, restated HERE so the counting below is checked against a
# declared expectation rather than against itself. The grid's own value is never restated.
_EXPECTED_ADVERSARIAL_POOL = 336
_EXPECTED_CLEAN_EPISODES_N8 = 176

# The arm whose clean-episode count is the pin's denominator. n=8 is the SMALL capacity, and the
# upper extreme is its no-repetition ceiling by construction: at n=64 the same pool divides into
# 1408 episodes and its own ceiling is far lower, which is why the grid tops out where n=8 does.
_DENOMINATOR_ARM = "dp_n8"


def _corpus_rows():
    """The committed attack corpus, parsed. Path from `phase18_extraction`, never from a literal."""
    path = phase18_extraction.CORPUS_PATH
    return path, json.loads(path.read_text(encoding="utf-8"))["prompts"]


def _corpus_geometry():
    """`corpus_geometry` off the committed multiplicity record, keyed by arm.

    The path comes from `phase21_unit_record.ARTIFACTS`, the register plan 21-11 declared precisely
    so consumers would resolve it from a constant instead of from a plan step's string.
    """
    path = phase21_unit_record.ARTIFACTS["multiplicity"]
    record = json.loads(path.read_text(encoding="utf-8"))
    return path, {row["arm"]: row for row in record["corpus_geometry"]}


def test_the_upper_extreme_re_derives_from_the_committed_corpus():
    """336 / 176, COUNTED — the grid's top is a measured quantity or it is a preference.

    D-09's whole claim is that the upper extreme was not chosen because it looked right. That claim
    is only checkable if both operands are recounted from the artifacts on every suite run, under
    exact `==`, so a hand-edited digit cannot reach a consumer. `test_a_one_ulp_nudge_to_the_upper_
    extreme_is_detected` watches that refusal happen rather than asserting it would.

    NON-VACUITY, and it has two halves. The family filter must select a NON-EMPTY subset, and it
    must EXCLUDE something — a filter that matched every row would be green while measuring the
    whole corpus, and the whole corpus is 864 prompts across four families, not the trained pool.
    """
    corpus_path, rows = _corpus_rows()
    trained = _PROVENANCE["trained_families"]

    adversarial = [row for row in rows if row["tier"] == "core_taught" and row["family"] in trained]
    excluded = [row for row in rows if row["family"] not in trained]

    assert adversarial, (
        f"the family filter {trained!r} selected ZERO rows out of {len(rows)} — "
        f"{corpus_path} does not carry the families the pin names, so every count below is a "
        "count of nothing"
    )
    assert excluded, (
        f"the family filter {trained!r} excluded NOTHING in {corpus_path}: every row matched. A "
        "filter that selects the whole corpus is green by matching everything, and the pool it "
        "would report is not the LEAVE-ONE-FAMILY-OUT pool D-10 defines"
    )

    counted_adversarial = len(adversarial)
    assert counted_adversarial == _EXPECTED_ADVERSARIAL_POOL, (
        f"{corpus_path} carries {counted_adversarial} `core_taught` prompts across the trained "
        f"families {trained!r}, not {_EXPECTED_ADVERSARIAL_POOL}. The pin's numerator has moved, "
        "so the upper extreme no longer names the n=8 no-repetition ceiling"
    )

    geometry_path, geometry = _corpus_geometry()
    counted_clean = geometry[_DENOMINATOR_ARM]["episodes"]
    assert counted_clean == _EXPECTED_CLEAN_EPISODES_N8, (
        f"{geometry_path} records {counted_clean} clean episodes on arm {_DENOMINATOR_ARM!r}, not "
        f"{_EXPECTED_CLEAN_EPISODES_N8} — the pin's denominator has moved"
    )

    # THE PIN ITSELF, under exact `==`. Never `pytest.approx`: the quotient is representable and
    # the literal was written at full float precision, so an approximate comparison here would
    # accept exactly the hand-edited digit this assertion exists to refuse.
    re_derived = counted_adversarial / counted_clean
    assert mitigation_budget.ADVERSARIAL_RATIO_GRID[-1] == re_derived, (
        f"`ADVERSARIAL_RATIO_GRID` tops out at "
        f"{mitigation_budget.ADVERSARIAL_RATIO_GRID[-1]!r}, but {counted_adversarial} adversarial "
        f"episodes over {counted_clean} clean episodes re-derives {re_derived!r}. Exact `==`: a "
        "grid extreme that does not re-derive from the records it cites is an author's preference "
        "wearing a measurement's clothes"
    )
    assert _PROVENANCE["upper_extreme"] == re_derived, (
        f"the provenance dict pins upper_extreme = {_PROVENANCE['upper_extreme']!r} but the grid "
        f"itself tops out at {mitigation_budget.ADVERSARIAL_RATIO_GRID[-1]!r} — a restated field "
        "with no test agreeing it is a copy waiting to drift"
    )

    # THE CITED SOURCES ARE THE FILES THAT WERE ACTUALLY READ, and their digests are live. The
    # paths are COMPUTED from the resolved objects rather than spelled, so this agreement is
    # between the provenance and the owning modules' constants, not between two string literals.
    read_paths = tuple(path.relative_to(_ROOT).as_posix() for path in (corpus_path, geometry_path))
    assert tuple(_PROVENANCE["upper_extreme_sources"]) == read_paths, (
        f"the provenance names sources {tuple(_PROVENANCE['upper_extreme_sources'])!r} but the "
        f"two records this test actually counted are {read_paths!r}"
    )
    source_provenance = _PROVENANCE["upper_extreme_source_provenance"]
    assert set(source_provenance) == set(read_paths), (
        f"`upper_extreme_source_provenance` is keyed by {sorted(source_provenance)} but the cited "
        f"sources are {sorted(read_paths)} — one record ships with no digest at all"
    )
    for path in (corpus_path, geometry_path):
        key = path.relative_to(_ROOT).as_posix()
        live = hashlib.sha256(path.read_bytes()).hexdigest()
        assert source_provenance[key]["sha256"] == live, (
            f"the provenance pins {key} at sha256 {source_provenance[key]['sha256']!r} but it "
            f"hashes to {live!r} today — the artifact this extreme was derived from is not the "
            "artifact on disk"
        )

    # `git_sha` is a PER-RECORD field here rather than a single top-level one, because two records
    # back this pin. The multiplicity record carries its own; the corpus record carries none, and
    # that None is asserted ABSENT rather than invented — an unlabelled number is indistinguishable
    # from a borrowed one, but a fabricated label is worse than a missing one.
    multiplicity_key = geometry_path.relative_to(_ROOT).as_posix()
    recorded = json.loads(geometry_path.read_text(encoding="utf-8"))["provenance"]["git_sha"]
    assert source_provenance[multiplicity_key]["git_sha"] == recorded, (
        f"the provenance pins {multiplicity_key} at git_sha "
        f"{source_provenance[multiplicity_key]['git_sha']!r}, the record itself records "
        f"{recorded!r}"
    )
    corpus_key = corpus_path.relative_to(_ROOT).as_posix()
    assert source_provenance[corpus_key]["git_sha"] is None, (
        f"the provenance pins a git_sha for {corpus_key}, which records none of its own — that "
        "field could only have been supplied by hand, and a hand-supplied provenance is the thing "
        "this file exists to make impossible"
    )
    assert "git_sha" not in json.loads(corpus_path.read_text(encoding="utf-8")), (
        f"{corpus_key} now carries a `git_sha` of its own, so the None above is stale rather than "
        "structural — pin the record's real commit instead"
    )


def test_a_one_ulp_nudge_to_the_upper_extreme_is_detected():
    """WATCHED RED, PERMANENTLY: the exact `==` above refuses a one-ULP hand edit.

    An assertion that a hand-edited number WOULD be caught is a claim; this is the observation. The
    nudge is applied to a COPY of the tuple, never to `scripts/mitigation_budget.py`, so the
    committed pin is byte-unchanged after this test runs.

    `math.nextafter` is not used, and the reason is the file it would be imported for: the smallest
    representable step is taken with `struct` on the IEEE-754 bit pattern, which is the same nudge
    and needs no explanation of which direction `nextafter` walks in.
    """
    _corpus_path, rows = _corpus_rows()
    _geometry_path, geometry = _corpus_geometry()
    re_derived = (
        len(
            [
                row
                for row in rows
                if row["tier"] == "core_taught" and row["family"] in _PROVENANCE["trained_families"]
            ]
        )
        / geometry[_DENOMINATOR_ARM]["episodes"]
    )

    pinned = mitigation_budget.ADVERSARIAL_RATIO_GRID[-1]
    bits = struct.unpack("<Q", struct.pack("<d", pinned))[0]
    nudged = struct.unpack("<d", struct.pack("<Q", bits + 1))[0]

    assert nudged != pinned, (
        "the one-ULP nudge produced the same float, so the control below proves nothing"
    )
    assert nudged != re_derived, (
        f"a one-ULP nudge of the pinned extreme ({pinned!r} -> {nudged!r}) still compares EQUAL to "
        f"the re-derived {re_derived!r}. The equality in "
        "`test_the_upper_extreme_re_derives_from_the_committed_corpus` is not discriminating and "
        "a hand-edited digit would pass it"
    )
    assert pinned == re_derived, (
        "the unnudged pin does not re-derive — this control is measuring a broken pin rather than "
        "a broken comparison"
    )


def test_the_lower_extreme_is_the_control():
    """`0.0` first, strictly increasing after — so "the extremes run first" is well-defined.

    The lower extreme is not a scaling choice. At ratio zero there are no adversarial episodes at
    all, so the arm's bins are byte-identical to v2.0's and the curve reconnects to the incumbent
    result BY CONSTRUCTION rather than by a claimed correspondence.

    The monotonicity half is what makes "extremes" mean anything: with a duplicate or an
    out-of-order point, `grid[0]` and `grid[-1]` would not be the smallest and largest values and
    an ordering the sweep driver assumes would be false at exactly one end.
    """
    grid = mitigation_budget.ADVERSARIAL_RATIO_GRID

    assert isinstance(grid, tuple) and grid, f"`ADVERSARIAL_RATIO_GRID` is {grid!r}"
    assert all(isinstance(point, float) for point in grid), (
        f"`ADVERSARIAL_RATIO_GRID` carries a non-float point: {grid!r}. An int point would compare "
        "equal to its float twin here and then divide differently in the builder"
    )
    assert grid[0] == 0.0, (
        f"`ADVERSARIAL_RATIO_GRID` starts at {grid[0]!r}, not 0.0. The control point is D-09's "
        "lower extreme and it is what reconnects the adversarial curve to v2.0"
    )
    assert _PROVENANCE["lower_extreme"] == grid[0], (
        f"the provenance pins lower_extreme = {_PROVENANCE['lower_extreme']!r} against a grid that "
        f"starts at {grid[0]!r}"
    )
    assert list(grid) == sorted(grid), (
        f"`ADVERSARIAL_RATIO_GRID` is not ascending: {grid!r}. `grid[-1]` is then not the largest "
        "point and the pre-registered upper extreme is not where the sweep tops out"
    )
    assert len(set(grid)) == len(grid), (
        f"`ADVERSARIAL_RATIO_GRID` repeats a point: {grid!r}. A duplicated point spends compute "
        "twice and reports one arm as two"
    )
    assert _PROVENANCE["point_count"] == len(grid), (
        f"the provenance declares point_count = {_PROVENANCE['point_count']!r} against a grid of "
        f"{len(grid)} points"
    )


def test_the_held_out_family_is_not_a_trained_family():
    """D-09 / D-10 / D-12's consistency, checked AT THE PIN.

    ADVT-02 requires the held-out family to be named before training. That is only meaningful if
    the name is not also in the trained set, and if the two sets together account for the corpus:
    a fifth family nobody assigned would be neither trained nor held out, and the leave-one-out
    claim would cover less than it says.

    The STRUCTURAL check over the corpus itself — that no A2 prompt reaches a training bin — is
    plan 24-03's and is deliberately separate. This one binds the provenance dict to the corpus's
    own labels, which is the half a wave-1 pin can honestly make.
    """
    trained = tuple(_PROVENANCE["trained_families"])
    held_out = _PROVENANCE["held_out_family"]

    assert held_out not in trained, (
        f"the held-out family {held_out!r} is also in the trained set {trained!r}. There is then "
        "no held-out family and ADVT-02's generalization claim has no subject"
    )
    assert len(set(trained)) == len(trained), (
        f"the trained set repeats a family: {trained!r} — the 336-episode pool would be "
        "double-counted"
    )

    _corpus_path, rows = _corpus_rows()
    labelled = {row["family"] for row in rows}
    assert set(trained) | {held_out} == labelled, (
        f"the pin accounts for families {sorted(set(trained) | {held_out})} but the corpus carries "
        f"{sorted(labelled)}. A family in neither set is neither trained nor held out, and the "
        "leave-one-family-out design covers less than it claims"
    )

    assert isinstance(_PROVENANCE["held_out_reason"], str) and _PROVENANCE["held_out_reason"], (
        "`held_out_reason` is empty. ADVT-02 forbids selection by performance, and a reason that "
        "states nothing is a reason a reader cannot check the choice against"
    )


def test_multiplicity_at_the_upper_extreme_re_derives():
    """D-07's multiplicity travels in the same sentence as the point — so it must re-derive too.

    At the upper extreme n=8 uses the trained pool exactly once (1.0x, which is what "no-repetition
    ceiling" MEANS) while n=64, whose clean-episode count is eight times larger, repeats it 8.0x.
    Phase 25 SC3 requires that figure to be reported beside the ratio; a figure asserted rather
    than computed would drift the moment either record moved.

    Exact `==` throughout, with no tolerance stated because none is used: both quotients come out
    on representable values from the same two integers the ratio itself was formed from.
    """
    _corpus_path, rows = _corpus_rows()
    _geometry_path, geometry = _corpus_geometry()

    pool = len(
        [
            row
            for row in rows
            if row["tier"] == "core_taught" and row["family"] in _PROVENANCE["trained_families"]
        ]
    )
    pinned_multiplicity = _PROVENANCE["multiplicity_at_upper_extreme"]

    assert set(pinned_multiplicity) <= set(geometry), (
        f"the provenance reports multiplicity for arms {sorted(pinned_multiplicity)} but the "
        f"committed geometry covers {sorted(geometry)} — one of them is not a measured arm"
    )
    assert pinned_multiplicity, (
        "`multiplicity_at_upper_extreme` is empty, so the loop below asserts nothing and Phase 25 "
        "SC3 has no figure to report beside the point"
    )

    upper = mitigation_budget.ADVERSARIAL_RATIO_GRID[-1]
    for arm, pinned in pinned_multiplicity.items():
        re_derived = upper * geometry[arm]["episodes"] / pool
        assert pinned == re_derived, (
            f"the provenance reports {pinned!r}x multiplicity on arm {arm!r} at the upper extreme, "
            f"but {upper!r} x {geometry[arm]['episodes']} clean episodes over a pool of {pool} "
            f"re-derives {re_derived!r}"
        )

    # THE DENOMINATOR ARM IS THE ONE THE EXTREME WAS BUILT FROM, and its multiplicity is exactly
    # one. That is not decoration: it is the arithmetic statement of "no-repetition ceiling", and
    # it is what would go red if the extreme were ever re-derived against the other arm.
    assert pinned_multiplicity[_DENOMINATOR_ARM] == 1.0, (
        f"arm {_DENOMINATOR_ARM!r} runs {pinned_multiplicity[_DENOMINATOR_ARM]!r}x at the upper "
        "extreme. The extreme is defined as ITS no-repetition ceiling, so anything but 1.0 means "
        "the pin was derived against a different denominator than the one it names"
    )
