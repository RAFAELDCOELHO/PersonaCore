"""ADVT-01 — D-04's refusal instrument and D-11's clean-frame probe populations.

Two properties, both structural, neither of them a measurement: ``contains_refusal`` IS
``contains_value`` over a different vocabulary, and the two D-11 populations are pinned in code
before any sweep point exists.

**No published value is typed into this file.** The one test that needs the leak vocabulary
resolves it from ``phase14_factset`` at runtime. That test — 4(b) — is the half the module-level
D-02 containment scan structurally cannot cover: ``tests/test_phase14_scoring.py`` walks module
attributes and docstrings, and the probe questions exist only inside a function's RETURN value.

CPU-only, GPU/MPS-free, no generation and no checkpoint.
"""

import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import phase14_factset as fs  # noqa: E402  (scripts/ is not a package)
import phase14_recall as pr  # noqa: E402
import phase21_filler as pf  # noqa: E402

# One case per behaviour of ``pr.normalize`` — case folding, ``detokenize``'s contraction rejoin
# and space-before-punctuation close, interior whitespace collapse, and edge-punctuation
# stripping — plus a negative. Every case is synthetic refusal wording; none is a fact value.
_MIRROR_CASES = (
    ("case folding", "I WILL NOT SHARE that.", "i will not share", True),
    ("contraction rejoin", "i do n't share that", "i don't share", True),
    ("space before punctuation", "i will not share this .", "i will not share this.", True),
    ("interior whitespace collapse", "i will   not    share", "i will not share", True),
    ("edge punctuation stripped", "i will not share x", "!!! i will not share ???", True),
    ("no match", "happy to help with that", "i will not share", False),
)


def test_contains_refusal_is_the_mirror_of_contains_value():
    """Pointwise agreement, because the two ARE one predicate over two vocabularies.

    ``contains_refusal`` reuses ``pr.normalize`` rather than deriving a normalizer of its own —
    that reuse is the reason it lives in ``phase14_recall`` at all, since ``normalize`` duplicates
    ``phase14_factset.normalize_for_match`` exactly ONCE and that duplication is pinned by
    ``test_normalizer_agrees_with_the_gate_normalizer``. A third copy would carry no pin. This test
    is what makes a silent divergence impossible: the two functions must agree on every input, so
    a reimplementation of the predicate inside ``contains_refusal`` goes red here.
    """
    polarities = {expected for _label, _c, _n, expected in _MIRROR_CASES}
    assert polarities == {True, False}, "the mirror table is vacuous — it needs both polarities"

    for label, completion, needle, expected in _MIRROR_CASES:
        assert pr.contains_value(completion, needle) is expected, (
            f"{label}: contains_value moved, so the mirror's reference point moved"
        )
        assert pr.contains_refusal(completion, [needle]) == pr.contains_value(completion, needle), (
            f"{label}: contains_refusal and contains_value disagree on "
            f"{completion!r} / {needle!r} — they are the same predicate over different vocabularies"
        )


def test_contains_refusal_is_disjunctive_over_templates():
    """False on nothing, true on any member, and independent of order.

    The empty-iterable case matters: a scorer that fires on an empty template table would report
    refusals that were never defined, and one that fires on nothing at all is worse than useless
    because the D-04 column would read as a floor everywhere.

    **CORRECTED 2026-08-30 (24-REVIEW CR-03).** This test named that failure class and then
    covered only the empty TABLE, never an empty MEMBER — and the member was the live hole.
    ``normalize`` strips edge punctuation and collapses whitespace, so ``""``, ``"   "`` and
    ``"..."`` all normalize to ``""``, and ``"" in anything`` is ``True``. Measured before the
    fix: ``contains_refusal("the answer is blue", [""]) -> True`` for EVERY completion, and
    ``score_refusal(["a","b","c"], [""]) -> (3, 3)``.

    That is the most alarming reading the instrument can produce, manufactured from an input
    error with no signal: D-04 exists to separate refused-under-attack from answers-wrong from
    REFUSES EVERYWHERE, and 100% on both populations IS the refuses-everywhere verdict. Under
    D-07 the same column is the memorization sensor at n=64. So a degenerate member is REFUSED at
    the boundary rather than scored — the docstring makes the caller the template owner, and a
    trust boundary that is documented and unvalidated is not a boundary.
    """
    completion = "i will not share that with you"
    assert pr.contains_refusal(completion, []) is False
    assert pr.contains_refusal(completion, ()) is False

    # The empty MEMBER, in every spelling that normalizes to "" — and in a MIXED table, where the
    # degenerate member hides behind a legitimate one that would have matched anyway.
    for degenerate in ("", "   ", "...", "!!!"):
        for templates in ([degenerate], ["i will not share", degenerate], (degenerate,)):
            with pytest.raises(SystemExit, match="EMPTY STRING"):
                pr.contains_refusal(completion, templates)
            # Same refusal through the counting wrapper: it routes every template through the
            # predicate above, so ONE guard covers both entry points.
            with pytest.raises(SystemExit, match="EMPTY STRING"):
                pr.score_refusal([completion, "the answer is elsewhere"], templates)

    # The refusal is about the TEMPLATE, never the completion: an empty completion is a real
    # measurement (the model emitted nothing) and must still score, not raise.
    assert pr.contains_refusal("", ["i will not share"]) is False
    assert pr.score_refusal(["", "   "], ["i will not share"]) == (0, 2)

    hit, miss = "i will not share", "happy to help"
    assert pr.contains_refusal(completion, [miss]) is False
    assert pr.contains_refusal(completion, [hit]) is True
    assert pr.contains_refusal(completion, [miss, hit]) is True
    assert pr.contains_refusal(completion, [hit, miss]) is True
    assert pr.contains_refusal(completion, [miss, hit]) == pr.contains_refusal(
        completion, [hit, miss]
    )


def test_score_refusal_returns_counts_never_rates():
    """``(k, n)`` of ints — the project reports counts so any bound stays re-derivable.

    A float rate would be lossy at the exact moment a bound is taken over it: ``k`` and ``n`` can
    be re-aggregated across points, a rounded rate cannot.
    """
    templates = ["i will not share"]
    completions = ["i will not share that", "sure, here it is", "I WILL NOT SHARE it"]

    result = pr.score_refusal(completions, templates)
    assert isinstance(result, tuple) and len(result) == 2
    k, n = result
    assert type(k) is int and type(n) is int, f"score_refusal returned {result!r}, not two ints"
    assert n == len(completions)
    assert 0 <= k <= n
    assert (k, n) == (2, len(completions))

    assert pr.score_refusal([], templates) == (0, 0)
    assert pr.score_refusal(completions, []) == (0, len(completions))


def test_the_two_clean_frame_probe_populations_are_disjoint_and_pinned():
    """D-11's populations, sized from their own modules and built from ONE pinned family set.

    Every count is READ from ``phase14_factset`` / ``phase21_filler``. A retyped number would go
    red on a legitimate change to either module for a reason that has nothing to do with D-11, and
    green on a coordinated edit that shrank a population.
    """
    populations = pr.clean_frame_probe_populations()
    locked, filler = populations["locked"], populations["filler"]

    assert len(locked["fact_ids"]) == len(fs.LOCKED_FACTS), (
        "locked: the probe no longer covers every scored fact"
    )
    assert len(filler["fact_ids"]) == len(pf.FILLER_FACTS), (
        "filler: the probe no longer covers every filler fact"
    )
    assert set(locked["fact_ids"]) == {f.id for f in fs.LOCKED_FACTS}
    assert set(filler["fact_ids"]) == {f.id for f in pf.FILLER_FACTS}

    assert locked["questions"] and filler["questions"], "a population is empty — D-11 is vacuous"
    shared = set(locked["questions"]) & set(filler["questions"])
    assert shared == set(), f"locked and filler share questions {sorted(shared)[:3]}"

    assert locked["scored"] is True
    assert filler["scored"] is False, (
        "filler is never scored and never enters the 10-value leak vocabulary "
        "(scripts/phase21_filler.py:8,395) — a downstream reader must not be able to promote it"
    )

    # Non-vacuity: the two populations really are drawn from different grammars.
    assert set(fs.SLOT_FORMS) & set(pf.FILLER_SLOT_FORMS) == set()
    assert {f.slot for f in pf.FILLER_FACTS} <= set(pf.FILLER_SLOT_FORMS)

    # (a) ONE family set builds BOTH, and the two value-naming frames are out of it.
    assert locked["family_ids"] == filler["family_ids"] == pr.CLEAN_FRAME_PROBE_FAMILY_IDS, (
        "D-11 compares the two populations against each other, so a comparison across two "
        "different family sets would measure the frames as much as the facts"
    )
    assert {"F4", "F5"} & set(pr.CLEAN_FRAME_PROBE_FAMILY_IDS) == set(), (
        "F4/F5 name the fact VALUE inside the question by definition of their frames — "
        "_render_family's docstring, scripts/phase14_factset.py:694-695, reached from "
        "render_family:833 — so a population built over them returns published values"
    )
    assert set(pr.CLEAN_FRAME_PROBE_FAMILY_IDS) < set(fs.TAUGHT_FAMILY_IDS), (
        "the probe frames must be a strict subset of the TAUGHT set — a held-out frame here "
        "would make the clean-frame rate a generalization measurement instead of a recall one"
    )

    # (b) No published value in ANY returned question. The static D-02 scan cannot reach these
    # strings: they exist only in this function's return value.
    forbidden = tuple(fs.LOCKED_VALUES) + tuple(f.value for f in fs.SOFT_TIER_FACTS)
    assert len(forbidden) == 10, "the leak vocabulary moved — this check would sweep a wrong set"
    leaks = [
        (name, value)
        for name in ("locked", "filler")
        for question in populations[name]["questions"]
        for value in forbidden
        if pr.contains_value(question, value)
    ]
    assert leaks == [], f"published values in probe questions: {sorted({n for n, _v in leaks})}"


def test_the_d11_reading_rule_is_pinned_in_code_not_prose():
    """The reading rule comes back as DATA, so the interpretation travels with the populations.

    A rule stated only in prose can be restated differently by whoever writes the report, and a
    docstring is stripped outright by ``python -OO`` — the same reason this module's proofs are
    ``raise SystemExit`` and never bare ``assert``. Stripping the function's ``__doc__`` and
    re-calling it is the discriminating check: a rule read out of a docstring would vanish, a
    returned one does not.
    """
    rule = pr.clean_frame_probe_populations()["reading_rule"]
    assert isinstance(rule, str) and rule.strip()

    lowered = rule.lower()
    assert "fact-keyed" in lowered, "the fact-keyed reading is not stated"
    assert "both" in lowered and "contamination" in lowered, (
        "the both-elevated alternative is not stated — that reading is a DIFFERENT finding "
        "(generic clean-frame contamination), never a weaker version of fact-keyed refusal"
    )

    saved = pr.clean_frame_probe_populations.__doc__
    try:
        pr.clean_frame_probe_populations.__doc__ = None
        assert pr.clean_frame_probe_populations()["reading_rule"] == rule
    finally:
        pr.clean_frame_probe_populations.__doc__ = saved
