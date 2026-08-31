"""PLAN 25-07 — THE GUARD THAT KEEPS PHASE 25'S EIGHT DATED CONTINUATIONS HONEST.

This is the **THIRD GUARD FILE** of the register `tests/test_phase23_cost.py` and
`tests/test_phase24_correction.py` already hold. It guards the register's **THIRD AND FOURTH
INSTANCES** — plan 25-07's `.planning/ROADMAP.md` + `.planning/REQUIREMENTS.md` sweep, and its
`25-CONTEXT.md` sweep (D-51's `D35-CONDITION-C`) — **so RPT-02's second half is discharged for the
third and fourth times**, under the requirement's own regulation rather than beside it.

**FOUR INSTANCES, THREE GUARD FILES.** 23-12, 24-03, and this plan's two sweeps. That is D-51's
counting and it is the only counting used in plan 25-07 or in plan 25-20.

**EIGHT vs NINE — DO NOT RECONCILE THESE BY CHANGING THE WRONG ONE.** Plan 25-07 WRITES **eight**
sentinel-bounded continuations. This file guards **NINE** sentinel pairs, because
`25-CONTEXT.md`'s `25-D48-CONTINUATION` pair — written during PLANNING, by no plan, correcting
D-48's floor citation — shipped **unguarded**: nothing else in the phase asserted its sentinels were
unique, its span carried its measured values, or the claim above it survived. Those are exactly the
properties RPT-02's mechanism exists to hold, so it is picked up here. The ninth pair is a **GUARDED
CASE, NOT A REGISTER INSTANCE**: the register stays at four instances in three guard files, and the
"eight" in the plan's Tasks 1, 2 and 3(f) stays eight. Only (a), (b) and (c) below see nine.

**WHY A CONTINUATION AND NOT AN EDIT.** This repository has measured the cost of editing a closed
pre-registration: the ancestry guards take ``adds[-1]`` — the EARLIEST add — so a later commit
touching a pin reddens them permanently, and ``git rm`` plus a re-add at the same path cannot
launder it. The sanctioned path is a DATED ADDITIVE CONTINUATION that leaves the original standing
as the record of what was believed. Deleting a superseded claim erases the only trace the belief was
ever held.

**WHY NOT ``scripts/_addendum.py``, MEASURED RATHER THAN ASSERTED.** 25-CONTEXT names
``append_addendum`` as "the ONLY legal correction path", and it is the wrong tool for
``.planning/*.md``. Measured this session: it has **ZERO call sites** against any `.planning/*.md`;
its "refuses a second append" is a PLACEHOLDER-COUNT rule, not a once-only lock; run live against a
COPY of `.planning/REQUIREMENTS.md` it **SUCCEEDED**, splicing onto an accidental ``PENDING``
substring; and its verdict-preservation ``_prove`` compares ``None`` to ``None`` there, because
``_verdict.recorded_verdict`` returns ``None`` for planning markdown — a VACUOUS guard. What has
actually shipped twice for planning-doc prose is the sentinel + ``_prose.normalized`` mechanism, so
that is what plan 25-07 used and what this file enforces.

**THE FOUR MECHANICS, COPIED FROM ``tests/test_phase24_correction.py`` RATHER THAN RE-DERIVED.**

  1. Match through ``scripts/_prose.normalized``. Every claim LINE-WRAPS in the planning documents,
     and a bare ``in`` check on the raw text reports a FALSE ABSENCE on a wrapped phrase — a
     measured defect, `.planning/RETROSPECTIVE.md:179-181`.
  2. Search for the marker FROM THE CLAIM'S INDEX, never from byte 0. "The first marker in the file
     is after the claim" is a different and false-RED-prone statement. This matters concretely
     here: six of the eight superseded claims are QUOTED BACK inside the continuation that
     supersedes them, so each phrase occurs more than once, and only a search anchored at the
     ORIGINAL's index says the thing intended.
  3. Count sentinels with ``str.count``, never with a line-counting tool, which counts LINES: two
     BEGIN sentinels emitted on ONE line would satisfy a line-count-of-1 check while the slice
     below scans only the first span and the second goes entirely unguarded.
  4. Resolve node ids and identifiers **by AST**, never by grep — this module's own docstrings
     discuss ``normalized`` and ``append_addendum`` by name, so a substring search cannot tell prose
     about a name from the name. Four independent instances of that false-RED class were produced
     in Phase 20 alone; `.planning/REQUIREMENTS.md`'s RPT-02 row records all four.

CPU-only: stdlib, pytest, and the one sibling script. No torch, no numpy, no network.
"""

import ast
import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import _prose  # noqa: E402  (needs the sys.path insert above)

_ROADMAP = ".planning/ROADMAP.md"
_REQUIREMENTS = ".planning/REQUIREMENTS.md"
_CONTEXT = ".planning/phases/25-frontier-sweep-and-the-existence-gate-verdict/25-CONTEXT.md"

# The EIGHT stems plan 25-07 writes, each paired with the document it lives in, because every guard
# below slices PER DOCUMENT: a stem present in the wrong file would otherwise pass a whole-tree
# search. Parametrized on the STEM and not on a tag, so the ninth — whose stem does not follow the
# `25-07-CONTINUATION-<TAG>` shape — sits in the same table instead of needing a second code path.
_PLAN_SPANS = (
    (_ROADMAP, "25-07-CONTINUATION-SC1-COMPARATOR"),
    (_ROADMAP, "25-07-CONTINUATION-SC4-ARTIFACT-PATH"),
    (_ROADMAP, "25-07-CONTINUATION-RPT02-SPAN"),
    (_REQUIREMENTS, "25-07-CONTINUATION-FRONT01-SCOPE"),
    (_REQUIREMENTS, "25-07-CONTINUATION-CTRL02-CLIP-DOMAIN"),
    (_REQUIREMENTS, "25-07-CONTINUATION-RPT02-ROW"),
    (_REQUIREMENTS, "25-07-CONTINUATION-RPT02-DUPLICATE-COUNT"),
    (_CONTEXT, "25-07-CONTINUATION-D35-CONDITION-C"),
)

# THE NINTH: written during planning, by NO plan, and it shipped unguarded. Not one of the eight,
# not a register instance — a guarded case. The `25-D48-CONTINUATION` block's own text says plan
# 25-07 Task 3(a) picks it up; this table is what makes that sentence true.
_INHERITED_SPAN = (_CONTEXT, "25-D48-CONTINUATION")

_ALL_SPANS = _PLAN_SPANS + (_INHERITED_SPAN,)


def _text(relative_path):
    return (_ROOT / relative_path).read_text(encoding="utf-8")


def _markers(stem):
    return f"<!-- {stem}-BEGIN -->", f"<!-- {stem}-END -->"


def _span(relative_path, stem):
    """The text strictly between a stem's own sentinels, with their placement asserted.

    Counted with ``str.count`` — mechanic (3) in the module docstring gives the concrete way a
    line-counting tool is defeated by two BEGIN sentinels sharing one line.
    """
    text = _text(relative_path)
    begin, end = _markers(stem)
    for sentinel in (begin, end):
        found = text.count(sentinel)
        assert found == 1, (
            f"{relative_path}: {sentinel} occurs {found} time(s); exactly one is required. A "
            "missing or duplicated sentinel makes the guard scan the wrong text, which is how a "
            "guard passes vacuously"
        )
    assert text.index(begin) < text.index(end), (
        f"{relative_path}: {stem}'s END sentinel precedes its BEGIN sentinel, so the span is empty "
        "or inverted"
    )
    return text.split(begin, 1)[1].split(end, 1)[0]


def _called_names(relative_path):
    """Every name CALLED in a module, resolved by parse. Mechanic (4): never by grep."""
    tree = ast.parse(_text(relative_path), filename=relative_path)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                names.add(func.attr)
            elif isinstance(func, ast.Name):
                names.add(func.id)
    return names


# ---------------------------------------------------------------------------------------------
# (a) SENTINEL INTEGRITY — nine pairs, each unique and ordered in its OWN document.
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("relative_path", "stem"),
    _ALL_SPANS,
    ids=[stem.lower() for _, stem in _ALL_SPANS],
)
def test_each_continuation_is_bounded_by_exactly_one_sentinel_pair(relative_path, stem):
    """Exactly one BEGIN, exactly one END, in that order, in the stem's own document.

    Counted with ``str.count`` for mechanic (3): a line-based counter reports 1 for a line carrying
    two BEGIN sentinels, and the slice taken below would then cover only the first span while the
    second went unguarded. `.planning/REQUIREMENTS.md` already carries two `RETRACTED IN PLACE`
    markers on a single line, so that defect is live in this repository rather than hypothetical.

    NINE cases, not eight: the eight plan 25-07 writes plus the inherited `25-D48-CONTINUATION`
    pair. The ninth is a guarded case and NOT an RPT-02 register instance — see the module
    docstring before changing either number.
    """
    body = _span(relative_path, stem)
    assert body.strip(), (
        f"{relative_path}: {stem}'s sentinels bound an EMPTY block. A pair wrapping nothing "
        "satisfies every count assertion and corrects nothing"
    )


# ---------------------------------------------------------------------------------------------
# (b) THE ORIGINALS SURVIVE — eight superseded claims, each still standing above its continuation.
# ---------------------------------------------------------------------------------------------

# (document, superseded claim, the stem that supersedes it). Every claim is matched through
# `normalized` (mechanic 1) and every marker is searched FROM THE CLAIM'S OWN INDEX (mechanic 2).
_SUPERSEDED = (
    (
        _ROADMAP,
        "defensible neighbourhood of v2.0's 0.4921 / 0.3483",
        "25-07-CONTINUATION-SC1-COMPARATOR",
    ),
    (_ROADMAP, "results/phase2X_frontier.json", "25-07-CONTINUATION-SC4-ARTIFACT-PATH"),
    (_REQUIREMENTS, "swept to the never-taught floor", "25-07-CONTINUATION-FRONT01-SCOPE"),
    (_REQUIREMENTS, "clip_norm=inf, noise_multiplier=0", "25-07-CONTINUATION-CTRL02-CLIP-DOMAIN"),
    (_REQUIREMENTS, "DEFERRED to Phase 25", "25-07-CONTINUATION-RPT02-ROW"),
    (
        _REQUIREMENTS,
        "48/48 mapped, 0 orphans, 0 duplicates",
        "25-07-CONTINUATION-RPT02-DUPLICATE-COUNT",
    ),
    (
        _CONTEXT,
        "the floor can never be loosened after seeing results",
        "25-D48-CONTINUATION",
    ),
    (_CONTEXT, "Nothing to fix", "25-07-CONTINUATION-D35-CONDITION-C"),
)

# The `originals-` prefix is deliberate and load-bearing for the plan's own acceptance criterion,
# which runs this test by `-k originals`. The function name is fixed by the plan and contains
# "original", not "originals", so the selector lives in the parametrization ids.
_SUPERSEDED_IDS = [f"originals-{stem.lower()}" for _, _, stem in _SUPERSEDED]


@pytest.mark.parametrize(("relative_path", "claim", "stem"), _SUPERSEDED, ids=_SUPERSEDED_IDS)
def test_every_original_claim_survives_beside_its_continuation(relative_path, claim, stem):
    """The superseded claim is STILL PRESENT, and its continuation opens AFTER it.

    A correction that removes the sentence it corrects is a rewrite, not a retraction: the record of
    what was believed is the thing being preserved.

    The marker is searched FROM THE CLAIM'S INDEX (mechanic 2), never from byte 0. That is not
    decoration here — six of these eight phrases are QUOTED BACK inside the very continuation that
    supersedes them, so each occurs more than once and only the first occurrence is the original.

    Two of the eight belong to the pair this plan INHERITS rather than writes: D-49's *"the floor
    can never be loosened after seeing results"*, superseded in place by `25-D48-CONTINUATION`, gets
    the same treatment as the six. And D-35's *"Nothing to fix"* is asserted PRESENT, never absent —
    the retract-in-place doctrine keeps a superseded claim visible, and an absence-assertion over a
    claim the same plan requires written is the self-contradictory shape this repository has
    already hit. Its positive counterpart is in
    ``test_the_continuations_carry_their_measured_values``.
    """
    flat = _prose.normalized(_text(relative_path))
    needle = _prose.normalized(claim)

    assert needle in flat, (
        f"{relative_path} no longer carries the superseded claim {claim!r}. A correction that "
        "removes the sentence it corrects is a rewrite, not a retraction"
    )

    where = flat.index(needle)
    begin, _ = _markers(stem)
    marker = flat.find(_prose.normalized(begin), where)
    assert marker != -1, (
        f"{relative_path} carries {claim!r} at {where} with no {stem} BEGIN sentinel anywhere "
        "after it. A continuation landing ABOVE the claim is not a continuation of it"
    )


def test_d35s_superseded_closing_is_named_positively_by_its_continuation():
    """D-35's `Nothing to fix` is superseded EXPLICITLY, and both producer plans are named.

    The positive half of the previous test's last case. Asserting the claim's continued presence
    proves nothing about whether it was actually superseded — a claim can survive because nobody
    corrected it. This is the containment check that says it was.
    """
    body = _prose.normalized(_span(_CONTEXT, "25-07-CONTINUATION-D35-CONDITION-C"))
    for token in ("SUPERSEDED", "Nothing to fix", "25-21", "25-22"):
        assert _prose.normalized(token) in body, (
            f"D-35's continuation does not carry {token!r}. A supersession that does not say what "
            "it supersedes, or which plans produce the missing inputs, leaves the claim unfixed"
        )


# ---------------------------------------------------------------------------------------------
# (c) THE CONTINUATIONS CARRY THEIR MEASURED VALUES — sliced to their OWN spans.
# ---------------------------------------------------------------------------------------------

# Slicing is load-bearing: every one of these values also occurs elsewhere in the repository's
# planning prose, so a whole-document check would pass on a continuation that carries none of them.
_MEASURED_VALUES = {
    "25-07-CONTINUATION-SC1-COMPARATOR": (
        _ROADMAP,
        (
            "0.7837301587301587",
            "0.0267857142857143",
            "0.5615079365079365",
            "936",
            "648",
        ),
    ),
    "25-07-CONTINUATION-SC4-ARTIFACT-PATH": (
        _ROADMAP,
        ("results/phase25_frontier.json",),
    ),
    "25-07-CONTINUATION-FRONT01-SCOPE": (
        _REQUIREMENTS,
        ("1.9090909090909092",),
    ),
    "25-07-CONTINUATION-CTRL02-CLIP-DOMAIN": (
        _REQUIREMENTS,
        ("[dp-refusal:clip-domain]", "1000000.0"),
    ),
    "25-07-CONTINUATION-D35-CONDITION-C": (
        _CONTEXT,
        ("zero_extraction_has_nll", "point_dialogue_ppl_on", "25-21", "25-22"),
    ),
    # The ninth span. All four values were verified present before this file existed, so this is a
    # SURVIVAL guard on an inherited block, not a new authoring obligation: if it ever reddens, the
    # block was edited or truncated.
    "25-D48-CONTINUATION": (
        _CONTEXT,
        (
            "0.068930",
            "results/phase20_retention_floor.json",
            "0.005214448168350039",
            "SUPERSEDED IN PLACE",
        ),
    ),
}


def test_the_continuations_carry_their_measured_values():
    """Every pinned figure is inside the span that is supposed to carry it, not merely in the file.

    A rounding lands here too: the required full-precision rendering is then simply absent, which is
    the defect `1.909` for `1.9090909090909092` would produce.
    """
    missing = []
    for stem, (relative_path, values) in _MEASURED_VALUES.items():
        body = _prose.normalized(_span(relative_path, stem))
        missing.extend(
            f"{relative_path} :: {stem} -> {value}"
            for value in values
            if _prose.normalized(value) not in body
        )
    assert missing == [], (
        f"{len(missing)} pinned value(s) are absent from the span that must carry them: {missing}. "
        "'Present somewhere in the document' is NOT the criterion — a value the continuation never "
        "publishes would satisfy that and prove nothing"
    )


# ---------------------------------------------------------------------------------------------
# (d) RPT-02'S REPAIR IS EVIDENCED, NOT ASSERTED.
# ---------------------------------------------------------------------------------------------


def test_rpt02_row_names_both_discharging_plans():
    """The row's continuation names 23-12, 24-03, both guard files, and its own falsified premise.

    "The second half is unmet" was the row's PREMISE, and it was false at HEAD before this plan ran.
    A repair that only asserts the conclusion leaves the reader unable to check it; naming the two
    already-discharging plans and the two files that guard them is what makes the supersession
    verifiable rather than declared.
    """
    body = _prose.normalized(_span(_REQUIREMENTS, "25-07-CONTINUATION-RPT02-ROW"))
    for token in (
        "23-12",
        "24-03",
        "tests/test_phase23_cost.py",
        "tests/test_phase24_correction.py",
        "premise",
    ):
        assert _prose.normalized(token) in body, (
            f"RPT-02's row continuation does not name {token!r}. The repair is a claim about "
            "already-shipped evidence, so it has to point at the evidence"
        )


def test_rpt02_is_on_phase_25s_requirements_line():
    """RPT-02 stands on Phase 25's own Requirements line — sliced, never searched whole-file.

    A whole-file search would match Phase 20's Requirements line, which has carried RPT-02 since the
    roadmap was written, and would therefore be green before D-38's repair as well as after.
    """
    text = _text(_ROADMAP)
    section = text[text.index("### Phase 25") : text.index("### Phase 26")]
    lines = [line for line in section.splitlines() if line.startswith("**Requirements**")]
    assert len(lines) == 1, f"Phase 25 carries {len(lines)} Requirements lines: {lines}"
    assert "RPT-02" in lines[0], (
        f"Phase 25's Requirements line is {lines[0]!r} and does not carry RPT-02, so no phase in "
        "the roadmap can tick it — the hole D-38 exists to close"
    )


# ---------------------------------------------------------------------------------------------
# (e) THE TWO GUARD FILES THIS ONE JOINS EXIST AND STILL ROUTE THROUGH `normalized`.
# ---------------------------------------------------------------------------------------------

_EARLIER_GUARD_FILES = ("tests/test_phase23_cost.py", "tests/test_phase24_correction.py")


def test_the_register_is_three_files_wide():
    """23-12's and 24-03's sweeps still exist and still CALL the helper RPT-02 is about.

    Resolved by AST (mechanic 4). Both files discuss ``normalized`` at length in their own
    docstrings, so a substring search would report it present whether or not a single call survived
    — the exact false-GREEN class RPT-02 exists to close.
    """
    for relative_path in _EARLIER_GUARD_FILES:
        assert (_ROOT / relative_path).is_file(), (
            f"{relative_path} is missing; the register this file joins is no longer three files "
            "wide and RPT-02's discharge count is wrong"
        )
        called = _called_names(relative_path)
        assert "normalized" in called, (
            f"{relative_path} no longer CALLS `normalized` (calls resolved by parse: "
            f"{sorted(called)}). A correction sweep that stopped routing through the helper is no "
            "longer evidence for RPT-02's second half"
        )


# ---------------------------------------------------------------------------------------------
# (f) THE WRONG MECHANISM IS PROVED ABSENT FROM THIS PLAN'S OWN SPANS.
# ---------------------------------------------------------------------------------------------

_WRONG_MECHANISM = "append_addendum"

# MEASURED AT HEAD, and located BY CONTENT rather than by line number — the 25-CONTEXT occurrence
# has already shifted twice under amendments inserted above it, and a check that resolves by line
# number is the defect this file's own doctrine names. `.planning/REQUIREMENTS.md` has zero.
_PRE_EXISTING_SITES = (
    (
        _ROADMAP,
        "a SECOND dated continuation appended to the `.md` via "
        "`scripts/_addendum.py::append_addendum` in its own commit",
    ),
    (
        _CONTEXT,
        "`scripts/_addendum.py` — `append_addendum(path, addendum, *, pending, recorded)`, the "
        "ONLY legal correction path for a closed pre-registration.",
    ),
)
_PRE_EXISTING_TOTAL = 2


def test_no_continuation_was_written_by_append_addendum():
    """NEVER a whole-document absence-assertion — a no-new-occurrence check instead.

    The property is *"no continuation THIS PLAN writes was written by the wrong mechanism"*, so the
    literal scan is sliced to the EIGHT spans plan 25-07 writes. Eight here, not nine: the inherited
    pair predates this plan. It is not exempt in effect — it lives in `25-CONTEXT.md`, whose single
    pre-existing occurrence is inside the total asserted below and was measured to sit OUTSIDE the
    `25-D48-CONTINUATION` span.

    A whole-document absence-assertion would go RED on prose that predates this plan entirely:
    ``append_addendum`` already occurs in `.planning/ROADMAP.md` (Phase 20's plan-list bullet for
    `20-16-PLAN.md`) and in `25-CONTEXT.md` (the `### Canonical References` bullet). Both are
    located BY CONTENT below and matched through ``normalized``, because the 25-CONTEXT bullet
    line-wraps across the name. Holding the total at two is what keeps this a real guard: a ninth
    continuation written by the wrong helper still reddens it.
    """
    called = _called_names("tests/test_phase25_correction.py")
    assert _WRONG_MECHANISM not in called, (
        f"this guard itself calls {_WRONG_MECHANISM}; the mechanism it refuses cannot be the "
        "mechanism it uses"
    )

    contaminated = [
        f"{relative_path} :: {stem}"
        for relative_path, stem in _PLAN_SPANS
        if _WRONG_MECHANISM in _span(relative_path, stem)
    ]
    assert contaminated == [], (
        f"{len(contaminated)} of the eight spans plan 25-07 writes mention {_WRONG_MECHANISM}: "
        f"{contaminated}. Measured against a COPY of `.planning/REQUIREMENTS.md`, that helper "
        "spliced onto an accidental `PENDING` substring and its verdict-preservation proof "
        "compared None to None — it is not a correction path for planning markdown"
    )

    total = sum(
        _text(relative_path).count(_WRONG_MECHANISM)
        for relative_path in (_ROADMAP, _REQUIREMENTS, _CONTEXT)
    )
    assert total == _PRE_EXISTING_TOTAL, (
        f"{_WRONG_MECHANISM} occurs {total} time(s) across the three planning documents; "
        f"{_PRE_EXISTING_TOTAL} pre-existing occurrence(s) were measured before plan 25-07 ran. A "
        "new occurrence means a correction was routed through the refused mechanism"
    )

    for relative_path, claim in _PRE_EXISTING_SITES:
        assert _WRONG_MECHANISM in claim
        assert _prose.normalized(claim) in _prose.normalized(_text(relative_path)), (
            f"{relative_path}'s pre-existing {_WRONG_MECHANISM} site moved or was edited: "
            f"{claim!r} is no longer present. The total above would still read "
            f"{_PRE_EXISTING_TOTAL} if an occurrence were deleted here and added inside a "
            "continuation, so the sites are pinned by content as well as counted"
        )
