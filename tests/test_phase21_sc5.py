"""SC5: the n=64 corpus disturbs NO published instrument (UNIT-06, D-13/D-18).

The n=64 arm exists to measure extraction over the SAME 8 facts as n=8, with only the corpus
AROUND them changed — an unconfounded capacity comparison. That only holds if nothing else moved:
not the 8 ``LOCKED_FACTS``, not the 270-question evaluation fixture, not the ancestry-guarded
``scripts/phase18_extraction.py``, and not the 10-value leak vocabulary. "Unscored" therefore has
a STRUCTURAL definition here, never an intention.

CPU-only, GPU-free, no model, no generation. Every check is a file read or a set operation.

Two instruments, deliberately kept BOTH rather than collapsed into one:

* ``embedded_fact_values`` (the committed helper, imported — never re-implemented) catches a leak
  that reached a file which is NOT in the sha256 pin list.
* the two sha256 pins fail on ANY edit for ANY reason, which is exactly what SC5's "unchanged"
  asks for and what a value scan cannot say.

Complementary, not redundant.
"""

import hashlib
import importlib.util
import pathlib
import re
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import phase14_factset as fs  # noqa: E402  (sibling script; scripts/ inserted above)
import phase21_filler as pf  # noqa: E402
from tests.test_phase14_scoring import embedded_fact_values  # noqa: E402

# MEASURED against this repository with `shasum -a 256`.
P18_SHA256 = "d2b44806a60228f0482851b737392299beef7206a93abdc2a2a0745204503d96"
FIXTURE_SHA256 = "407c4b9304a74801ae15445360dcf3edc8002a65ce1011f9991c88b768307c55"

RECALL_FIXTURE = _REPO_ROOT / "results" / "phase16_recall_sample.json"

# The six published instrument SOURCES the filler values must not appear inside. This list is the
# BOUNDARY of direction 1's claim and is stated rather than implied: it is a fixed enumeration, not
# a glob, so a NEW instrument file is outside it until someone adds it here. The widening guard
# that does scan a glob is `tests/test_phase18_prereg.py:127-132`, over `scripts/phase18_*.py`.
INSTRUMENT_SOURCES = (
    "scripts/phase18_extraction.py",
    "scripts/mitigation_gate.py",
    "scripts/mitigation_unit.py",
    "scripts/phase14_factset.py",
    "scripts/erasure_gate.py",
    "scripts/phase19_erasure.py",
)


def _load(path):
    """The committed module-loading idiom (``tests/test_phase14_scoring.py:398-402``).

    ``embedded_fact_values`` takes a MODULE OBJECT, not a path, because it walks the strings the
    module actually HOLDS — including strings nested in its tuples and dicts — rather than the
    bytes of its source. A value assembled at import time from two literals is invisible to a
    source read and visible here.
    """
    path = pathlib.Path(path)
    spec = importlib.util.spec_from_file_location(path.stem, _REPO_ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# =====================================================================================
# ===== T-21-04 / T-21-39 — the bidirectional leak scan ===============================
# =====================================================================================


def test_no_filler_leak():
    """No filler value reaches a published instrument, and no scored value reaches the filler.

    FOUR directions, each with its own assertion and its own message, so a failure says WHICH
    direction and WHICH file rather than "a leak happened somewhere".

    Directions 1-2 and direction 3 are DIFFERENT DEFECTS, and only one of them is visible to the
    existing ``== 10`` wall. "A filler value leaked into an instrument" turns the wall red because
    the leak vocabulary would have to grow; "a scored value leaked into the filler module" leaves
    the wall entirely green while confounding the capacity comparison the n=64 arm exists to make.

    Direction 3 is also where D-17's collision refusal gets its INDEPENDENT check.
    ``phase21_filler``'s import-time ``refuse_collisions()`` proves the values were minted
    correctly from INSIDE the module that implements the rule; this assertion proves the same
    property from OUTSIDE, and the outside one survives a future edit that weakens the inside one.

    Both sides are lowercased before comparison, matching ``embedded_fact_values``' own
    convention (it lowercases the haystack and expects lowercase needles).
    """
    filler = tuple(f.value.lower() for f in pf.FILLER_FACTS)
    assert len(filler) == 56, f"expected 56 filler values, got {len(filler)}"
    assert len(set(filler)) == 56, "filler values are not distinct"

    scored = tuple(f.value.lower() for f in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS)
    # This file joins the `== 10` wall here. The census below EXCLUDES this file BY CONSTRUCTION
    # (see `_census`), so the two do not contradict each other.
    assert len(scored) == 10  # all 8 locked + both soft — no tier is exempt

    # --- direction 1: no filler value inside any published instrument SOURCE ---
    for rel in INSTRUMENT_SOURCES:
        hits = embedded_fact_values(_load(rel), filler)
        assert hits == [], (
            f"direction 1: filler value(s) {hits} are embedded in {rel}. A filler value inside a "
            "published instrument confounds the n=8-vs-n=64 comparison the n=64 arm exists to "
            "make unconfounded (T-21-04)."
        )

    # --- direction 2: no filler value in the raw TEXT of the 270-question fixture ---
    # Read as TEXT here on purpose: this direction asks what the fixture SAYS, not what bytes it
    # is. `test_frozen_instruments_are_byte_unchanged` asks the byte question, in bytes.
    fixture_text = RECALL_FIXTURE.read_text(encoding="utf-8").lower()
    present = sorted(value for value in filler if value in fixture_text)
    assert present == [], (
        f"direction 2: filler value(s) {present} appear in {RECALL_FIXTURE.name}, THE binding "
        "270-question evaluation fixture. Its questions must be identical across both capacities."
    )

    # --- direction 3 (the reverse): no scored value reaches the filler CORPUS ---
    #
    # PLAN DEFECT, MEASURED. 21-09-PLAN specifies this direction as
    # `embedded_fact_values(<the phase21_filler MODULE>, scored)`. That assertion can never pass
    # and never could: `phase21_filler` HOLDS all ten scored values BY DESIGN, in
    # `FORBIDDEN_SCORED_VALUES` (the leak vocabulary it refuses against) and again inside
    # `PUBLISHED_POOL_VALUES`. Measured: 22 hits, of which 20 are those two frozensets and 2 are
    # the module docstring naming a scored value. Scanning the MODULE therefore only re-discovers
    # the refusal vocabulary; it says nothing about the corpus.
    #
    # The property direction 3 is actually for is D-17's, checked from OUTSIDE the module that
    # implements it: no filler VALUE collides with a scored value, and no scored value reaches
    # the rendered rows that actually enter the n=64 teaching bin. Both are asserted below.
    scored_norm = {fs.normalize_for_match(f.value) for f in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS}
    collisions = sorted(
        (f.id, f.value, s)
        for f in pf.FILLER_FACTS
        for s in scored_norm
        # containment in BOTH directions, never equality: `marrowgatex` == `marrowgate` is False
        # and would sail past an equality guard while carrying the scored value verbatim.
        if s in fs.normalize_for_match(f.value) or fs.normalize_for_match(f.value) in s
    )
    assert collisions == [], (
        f"direction 3a: filler value(s) collide with a scored value: {collisions}. This is the "
        "defect the `== 10` wall CANNOT see — the vocabulary stays at 10 while a filler fact "
        "teaches a scored value under a filler id (T-21-39). `phase21_filler`'s import-time "
        "refuse_collisions() is the INSIDE tier; this is the OUTSIDE one, and it survives a "
        "future edit that weakens the inside one."
    )

    rendered = " | ".join(
        f"{question} {answer}" for question, answer in pf.render_filler_episodes()
    ).lower()
    leaked = sorted(value for value in scored if value in rendered)
    assert leaked == [], (
        f"direction 3b: scored value(s) {leaked} appear in the RENDERED filler episodes — the "
        "rows that actually enter the n=64 teaching bin. A collision-free value set rendered "
        "through a grammar that quotes a scored value would still teach it."
    )

    # --- direction 4: no filler ID reaches all_pools(), _BY_ID or GATE_PROBES ---
    filler_ids = {f.id for f in pf.FILLER_FACTS}
    pooled = {f.id for _name, pool in fs.all_pools() for f in pool}
    assert filler_ids & pooled == set(), sorted(filler_ids & pooled)
    assert filler_ids & set(fs._BY_ID) == set(), sorted(filler_ids & set(fs._BY_ID))
    assert filler_ids & set(fs.GATE_PROBES) == set(), sorted(filler_ids & set(fs.GATE_PROBES))


# =====================================================================================
# ===== T-21-41 — the `== 10` wall census =============================================
# =====================================================================================
#
# THE CENSUS MEASURES THE PRE-EXISTING WALL, NOT THIS PHASE'S ADDITIONS TO IT. It excludes the
# file it lives in MECHANICALLY (`path.name == pathlib.Path(__file__).name`), never by a comment,
# because `test_no_filler_leak` above is required to carry `len(scored) == 10` as its own
# participation in the wall — so a census that did not exclude itself would discover itself.
#
# The `__file__` exclusion is chosen over the alternative of phrasing this file's wall assertion
# in a NON-matching form. That alternative dodges the census by ACCIDENT of phrasing: a future
# edit rewording it to a matching form would silently break the census again.
#
# THE COUNT IS NOT HARD-CODED FROM ANY DOCUMENT. Every documented figure for this wall has been
# wrong: `21-CONTEXT.md` D-18 says 4 sites; `21-RESEARCH.md` says 7 across 6 files; this plan's
# `<interfaces>` says 8 across 7; plan-check pass 3 said 9; plan 21-07 MEASURED 11 across 8 and
# then added a 12th in `scripts/phase21_filler.py`. The pin below is a MEASURED multiset of
# (filename, expression) pairs — line numbers are deliberately absent so a site that MOVES is not
# a failure while a site that DISAPPEARS or APPEARS is.

_PATTERNS = (
    re.compile(r"len\(forbidden\)\s*==\s*10\b"),
    re.compile(r"len\(values\)\s*==\s*10\b"),
    # The third pattern is not decoration. Neither of the two above matches
    # `tests/test_phase19_erasure.py`'s `taught == 10` or `tests/test_phase21_filler.py`'s
    # `len(fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS) == 10` — two real wall sites that the plan's
    # two-pattern census would have missed entirely.
    re.compile(r"(?:==|!=)\s*10(?![0-9_])"),
)

# Candidates the broad third pattern finds that are NOT leak-vocabulary sites. Each carries its
# reason; an exclusion without one is indistinguishable from a site quietly dropped to hit a
# number. Keyed by (filename, exact source line, stripped).
_NOT_WALL_SITES = {
    # rate arithmetic — `10 / LADDER_CELL_QUESTIONS` and `10 / draws`. The 10 is a numerator of a
    # success rate, not a fact count.
    ("test_phase16_ladder.py", 'assert row["rate"] == 10'): "rate arithmetic",
    ("test_phase16_ladder.py", 'assert row["rate"] != 10'): "rate arithmetic",
    # plan 21-10's multiplicity ROW SCHEMA key count (D-26) — unrelated to the leak vocabulary.
    # NEW since 21-07's census measured 11; it is the concrete reason a census may not inherit a
    # prior plan's number, only its method.
    ("test_phase21_multiplicity.py", "assert len(TEN_SCHEMA_KEYS) == 10"): "row-schema keys",
    # a docstring naming the wall, not an assertion on it
    ("test_phase21_filler.py", '"""This file joins the `== 10'): "docstring",
}

# MEASURED at this commit by `_census()` — see the module comment above for why it is a multiset
# of (filename, expression) and not a bare integer.
_EXPECTED_WALL = sorted(
    [
        ("test_phase14_demo.py", 'assert len(result["values"]) == 10'),
        ("test_phase14_demo.py", "assert len(values) == 10"),
        ("test_phase14_scoring.py", "assert len(forbidden) == 10"),
        ("test_phase16_driver.py", "assert len(forbidden) == 10"),
        ("test_phase16_ladder.py", "assert len(forbidden) == 10"),
        ("test_phase16_ladder.py", "assert len(forbidden) == 10"),
        ("test_phase18_corpus.py", "assert len(values) == 10"),
        ("test_phase18_prereg.py", "assert len(forbidden) == 10"),
        ("test_phase19_erasure.py", "assert len(forbidden) == 10"),
        ("test_phase19_erasure.py", "assert taught == 10"),
        ("test_phase21_filler.py", "assert len(fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS) == 10"),
    ]
)


def _census():
    """Every `== 10` leak-vocabulary assertion under ``tests/``, discovered mechanically.

    Returns ``(sites, files)`` where a site is ``(filename, lineno, expression)``. The expression
    is TRUNCATED at the end of the ``== 10`` match, so a site that gains (or loses) an explanatory
    message, a trailing comment or a line continuation is not reported as having moved — only its
    assertion changing is.
    """
    own = pathlib.Path(__file__).name
    sites = []
    for path in sorted((_REPO_ROOT / "tests").rglob("*.py")):
        if path.name == own:  # MECHANICAL self-exclusion — see the module comment above
            continue
        for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            found = [m for m in (p.search(raw) for p in _PATTERNS) if m]
            if not found:
                continue
            expr = raw[: max(m.end() for m in found)].strip()
            if (path.name, expr) in _NOT_WALL_SITES:
                continue
            sites.append((path.name, lineno, expr))
    return sites, sorted({name for name, _lineno, _expr in sites})


def test_wall_census_is_the_measured_set():
    """The wall SC5 rests on is SAMPLED IN FULL — a new site is a finding, a lost site a regression.

    T-21-41: sampling only D-18's four named sites would leave the majority of the wall unsampled,
    including ``tests/test_phase18_prereg.py``'s, which is the most valuable of them — it does not
    merely count, it then scans every member of the ``scripts/phase18_*.py`` glob for embedded fact
    values, so it is a COVERAGE-WIDENING guard.

    RECORDED, as a fact the next reader should meet rather than re-discover: this file's own
    ``len(scored) == 10`` in ``test_no_filler_leak`` is a TWELFTH assertion of the same class, and
    ``scripts/phase21_filler.py:263``'s module-level ``assert len(FORBIDDEN_SCORED_VALUES) == 10``
    is a THIRTEENTH — the only one in *source* rather than in a test. Neither is counted here:
    this census walks ``tests/`` only and excludes its own file, so it measures the PRE-EXISTING
    wall.
    """
    sites, files = _census()
    observed = sorted((name, expr) for name, _lineno, expr in sites)
    assert observed == _EXPECTED_WALL, (
        "the `== 10` wall census moved.\n"
        f"  observed {len(observed)} sites across {len(files)} files:\n"
        + "".join(f"    {name}:{lineno}  {expr}\n" for name, lineno, expr in sites)
        + f"  expected {len(_EXPECTED_WALL)} sites:\n"
        + "".join(f"    {name}  {expr}\n" for name, expr in _EXPECTED_WALL)
        + "  A NEW site is a finding — read it, confirm it asserts on LOCKED+SOFT, and add it "
        "here (or to _NOT_WALL_SITES with its reason). A DISAPPEARED site is a REGRESSION: the "
        "wall SC5 rests on just got smaller."
    )
    # Every wall file must be one the SC5 guard set actually RUNS, or the census is bookkeeping.
    assert set(files) <= set(SC5_GUARD_SET), sorted(set(files) - set(SC5_GUARD_SET))


# The files this plan's <verification> block runs. Kept beside the census so the coupling is
# checkable rather than a promise made in a plan document.
SC5_GUARD_SET = (
    "test_phase14_scoring.py",
    "test_phase16_driver.py",
    "test_phase16_ladder.py",
    "test_phase18_corpus.py",
    "test_phase18_prereg.py",
    "test_phase19_erasure.py",
    "test_phase14_factset.py",
    "test_phase14_demo.py",
    "test_phase21_filler.py",
    "test_phase21_multiplicity.py",
)


# =====================================================================================
# ===== T-21-08 / T-21-40 — the frozen instruments ====================================
# =====================================================================================


def test_instruments_unchanged_byte_for_byte():
    """SC5's "unchanged" half, as two sha256 pins.

    NAMED so that ``-k instruments_unchanged`` actually SELECTS it. ``21-VALIDATION.md:88-89``
    pins that selector for both of this test's rows, and against the plan's own name
    (``..._frozen_instruments_are_byte_unchanged``) it matched nothing: pytest reported
    "4 deselected" and exited **0**. A published verification command that selects zero tests
    passes vacuously, which is the one failure mode a verification table cannot afford.

    Read as BYTES, never as text. The reason is copied here rather than cited to
    ``tests/test_package.py:34-35``, because a rule whose reason lives only in another file drifts
    the first time someone edits this one: **a text read normalizes line endings, so a CRLF
    rewrite would pass a text-mode hash while changing the file on disk.**

    ``scripts/phase18_extraction.py`` carries a SECOND, independent tier: it is ancestry-guarded
    via ``PHASE18_PREREG_ARTIFACT`` and the live ordering guard in ``tests/test_phase16_prereg.py``,
    so an edit that is COMMITTED turns that guard permanently red as well — ``adds[-1]`` means a
    ``git rm`` + re-add cannot launder it. Two independent tiers fire on one byte.

    ``results/phase16_recall_sample.json`` is git-tracked and is THE binding 270-question
    evaluation fixture: the n=8 and n=64 arms must be scored against identical questions or the
    capacity comparison is confounded by the questions rather than by the capacity.
    """
    for rel, expected in (
        ("scripts/phase18_extraction.py", P18_SHA256),
        ("results/phase16_recall_sample.json", FIXTURE_SHA256),
    ):
        actual = hashlib.sha256((_REPO_ROOT / rel).read_bytes()).hexdigest()
        assert actual == expected, (
            f"{rel} changed: expected sha256 {expected}, got {actual}. SC5 requires this file to "
            "be byte-identical across the n=64 corpus work. If it genuinely must change, that is "
            "a decision to record explicitly — never a pin to update quietly."
        )


def test_locked_and_soft_tiers_are_unmoved():
    """The EXACT composition, which is what SC5's "the 8 LOCKED_FACTS ... unchanged" says.

    ``tests/test_phase14_factset.py:101-103`` caps these with INEQUALITIES (``<= 8``, ``<= 3``).
    An inequality admits a tier that shrank, and a shrunk locked tier would silently change what
    both capacities are measuring while leaving the leak vocabulary's count assertion the only
    thing standing. The ordered ids are pinned against ``scripts/phase14_factset.py:390-399``.
    """
    assert len(fs.LOCKED_FACTS) == 8
    assert len(fs.SOFT_TIER_FACTS) == 2
    assert tuple(f.id for f in fs.LOCKED_FACTS) == (
        "cand_person_quillon",
        "cand_dog_zorp",
        "cand_cat_zibby",
        "cand_sister_orsala",
        "cand_town_brindlemoor",
        "cand_street_marrowgate",
        "cand_year_1987",
        "cand_house_7412",
    )
    slots = [f.slot for f in fs.LOCKED_FACTS]
    assert len(set(slots)) == 8, f"the locked tier is ONE PER DISTINCT SLOT; got {slots}"
