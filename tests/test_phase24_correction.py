"""PLAN 24-03 — THE GUARD THAT KEEPS SC2'S DATED CONTINUATION HONEST.

`.planning/ROADMAP.md` ships the correction. This file is what makes it enforceable, and it joins
the register `tests/test_phase20_correction.py` and `tests/test_phase23_cost.py:783` already hold:
a correction nobody can watch fail is a correction nobody has verified.

**WHY A CONTINUATION AND NOT AN EDIT.** This repository has measured the cost of editing a closed
pre-registration: the ancestry guards take ``adds[-1]`` — the EARLIEST add — so a later commit
touching a pin reddens them permanently, and ``git rm`` plus a re-add at the same path cannot
launder it. The sanctioned path is a DATED ADDITIVE CONTINUATION that leaves the original standing
as the record of what was believed. SC2's clause is not frozen the way a pin is, but the discipline
is the same one and the reason is stronger here: the clause is *evidence of a belief*, and deleting
it would erase the only trace that the belief was ever held.

**THREE MECHANICS, ALL COPIED FROM `tests/test_phase23_cost.py:783-817` AND ALL LOAD-BEARING.**

  1. Match through ``scripts/_prose.normalized``. The claim LINE-WRAPS in the roadmap, and a bare
     ``in`` check on the raw text reports a FALSE ABSENCE on a wrapped phrase — a measured defect,
     `.planning/RETROSPECTIVE.md:179-181`.
  2. Search for the marker FROM THE CLAIM'S INDEX, never from byte 0. "The first marker in the file
     is after the claim" is a different and false-RED-prone statement.
  3. Count sentinels with ``str.count``, never ``grep -c``. ``grep -c`` counts LINES, so two BEGIN
     sentinels emitted on one line satisfy a ``grep -c ... = 1`` check while the slice below scans
     only the first span and the second goes unguarded.

**AND ONE MECHANIC THIS PHASE ADDS: node ids are resolved by AST, never by grep.** The continuation
names three pytest node ids. Checking they exist by grepping the target module would go FALSE-GREEN
here, because that module's own docstrings discuss those same names — the exact failure this
register exists to prevent (four independent instances of it are recorded in
`.planning/REQUIREMENTS.md`'s ``RPT-02`` row). Only a parse can tell prose about a name from the
name. The node ids are also COLLECTED from the roadmap rather than only compared against a declared
pair, so a name the roadmap invents, misspells or leaves behind after a rename is red too.

CPU-only: stdlib plus one sibling script. No torch, no numpy, no network.
"""

import ast
import datetime
import pathlib
import re
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import _prose  # noqa: E402  (needs the sys.path insert above)

# SC2's clause, taken VERBATIM from `.planning/ROADMAP.md` and long enough to be unique. The short
# form — the phrase the continuation itself quotes back — occurs twice on purpose, once in the
# original and once in the quotation, so matching on the short form would make the uniqueness
# assertion below meaningless. Including the `read from ...` tail is what keeps the needle singular.
_CLAIM_TEXT = (
    "a zero-`(fact_id, seed_index)`-overlap structural check read from "
    "`results/phase18_corpus.json`"
)

# Fresh ids. Reusing `23-12-CONTINUATION-*` — the live pair those same mechanics guard twenty lines
# into this file's target — would make BOTH `str.count(...) == 1` assertions fail.
_BEGIN_SENTINEL = "<!-- 24-03-CONTINUATION-BEGIN -->"
_END_SENTINEL = "<!-- 24-03-CONTINUATION-END -->"

# The marker shape, with its date and the plan that wrote it. A bare `SUPERSEDED IN PLACE` substring
# would be satisfied by any future correction in any other plan.
_MARKER = re.compile(r"SUPERSEDED IN PLACE (\d{4}-\d{2}-\d{2}) \(plan 24-03\)")

_CORRECTED_FILES = (".planning/ROADMAP.md",)

# The module the continuation's node ids must resolve INTO, and the two replacements it must name.
# The third node id it carries — the unsatisfiability measurement — is not declared here; it is
# collected from the roadmap by `_NODE_ID` below and resolved with the rest, so the register grows
# by editing the roadmap rather than by editing two files in step.
_SPLIT_MODULE = "tests/test_phase24_split.py"
_REPLACEMENT_NODE_IDS = (
    f"{_SPLIT_MODULE}::test_trained_and_held_out_attack_families_are_disjoint_on_family",
    f"{_SPLIT_MODULE}::test_taught_and_held_out_source_families_are_disjoint_on_source_family",
)

_NODE_ID = re.compile(r"(tests/[A-Za-z0-9_]+\.py)::([A-Za-z0-9_]+)")


def _text(relative_path):
    return (_ROOT / relative_path).read_text(encoding="utf-8")


def _continuation(text):
    """The text strictly between the two sentinels, with their placement asserted.

    Counted with ``str.count`` and NOT with a line-based tool — see mechanic 3 in the module
    docstring for the concrete way ``grep -c`` is defeated.
    """
    for sentinel in (_BEGIN_SENTINEL, _END_SENTINEL):
        found = text.count(sentinel)
        assert found == 1, (
            f"{sentinel} occurs {found} time(s); exactly one is required. A missing or duplicated "
            "sentinel makes the guard scan the wrong text, which is how a guard passes vacuously"
        )
    assert text.index(_BEGIN_SENTINEL) < text.index(_END_SENTINEL), (
        "the END sentinel precedes the BEGIN sentinel, so the continuation slice is empty or "
        "inverted"
    )
    return text.split(_BEGIN_SENTINEL, 1)[1].split(_END_SENTINEL, 1)[0]


def _defined_test_names(relative_path):
    """Every ``def test_*`` name in a module, by PARSE. Never by grep — see the module docstring."""
    tree = ast.parse(_text(relative_path), filename=relative_path)
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }


def test_the_original_sc2_claim_is_left_standing():
    """The superseded clause SURVIVES, verbatim and exactly once.

    A correction that removes the sentence it corrects is a rewrite, not a retraction: the record of
    what was believed is the thing being preserved. Uniqueness is asserted as well as presence,
    because the marker search in the next test starts FROM the claim's index — with two copies of
    the needle, "the marker follows the claim" would silently mean "the marker follows the first
    copy", and a continuation stranded above the second copy would pass.
    """
    for relative_path in _CORRECTED_FILES:
        flat = _prose.normalized(_text(relative_path))
        claim = _prose.normalized(_CLAIM_TEXT)

        assert claim in flat, (
            f"{relative_path} no longer carries the original claim {_CLAIM_TEXT!r}. A correction "
            "that removes the sentence it corrects is a rewrite, not a retraction"
        )
        assert flat.count(claim) == 1, (
            f"{relative_path} carries the claim {flat.count(claim)} times; exactly one is required "
            "so the marker search from the claim's index is unambiguous"
        )


def test_the_correction_marker_follows_the_claim():
    """A dated 24-03 marker EXISTS AFTER the claim, and its date is a real date.

    Searched from the claim's position rather than from byte 0. The stricter "the first marker in
    the file is after the claim" reading has a measured false-RED channel and buys no teeth: a
    planning file legitimately summarises its own corrections in a status line far above the claim,
    and refusing it for that proves nothing about whether the correction is additive.
    """
    for relative_path in _CORRECTED_FILES:
        flat = _prose.normalized(_text(relative_path))
        where = flat.index(_prose.normalized(_CLAIM_TEXT))

        marker = _MARKER.search(flat, where)
        assert marker is not None, (
            f"{relative_path} carries the claim at {where} with no `SUPERSEDED IN PLACE <date> "
            "(plan 24-03)` marker anywhere after it. A marker landing ABOVE the claim is not a "
            "continuation of it"
        )
        # `date.fromisoformat` rejects `2026-13-40`, which the regex's `\\d{2}` shape accepts.
        stamped = datetime.date.fromisoformat(marker.group(1))
        assert stamped.isoformat() == marker.group(1)


def test_the_continuation_is_bounded_by_exactly_one_sentinel_pair():
    """Exactly one BEGIN, exactly one END, in that order, with the marker strictly between them.

    The marker's placement is what ties the two halves together. A sentinel pair wrapping a block
    that does not carry the dated marker, plus a marker sitting loose somewhere else after the
    claim, would satisfy the two previous tests separately while bounding an empty correction.
    """
    for relative_path in _CORRECTED_FILES:
        text = _text(relative_path)
        _continuation(text)  # asserts count == 1 on both sentinels, and BEGIN before END

        begin = text.index(_BEGIN_SENTINEL)
        end = text.index(_END_SENTINEL)
        marker = _MARKER.search(text)
        assert marker is not None, f"{relative_path} carries no dated 24-03 marker at all"
        assert begin < marker.start() < end, (
            f"{relative_path}'s dated marker is at {marker.start()}, outside the sentinel pair at "
            f"({begin}, {end}). A marker outside the block it dates dates nothing"
        )


def test_the_continuation_names_its_replacement_tests():
    """Both replacement node ids are named, and EVERY node id the block names RESOLVES.

    Resolution is an ``ast`` parse of the target module, never a grep over it: that module's own
    docstrings discuss ``test_trained_and_held_out_attack_families_are_disjoint_on_family`` and its
    sibling by name, so a substring search would report them present whether or not the functions
    exist. Prose about a name is not the name.

    Collecting the ids rather than only checking the declared pair is what makes a RENAME red. A
    roadmap that keeps pointing at a function nobody kept is a citation to nothing, and it fails
    here on the commit that renames the function rather than at the next audit.
    """
    for relative_path in _CORRECTED_FILES:
        body = _prose.normalized(_continuation(_text(relative_path)))

        for node_id in _REPLACEMENT_NODE_IDS:
            assert node_id in body, (
                f"{relative_path}'s continuation does not name {node_id}. A supersession that does "
                "not say what replaces the superseded check leaves the criterion unverified"
            )

        found = _NODE_ID.findall(body)
        assert len(found) >= len(_REPLACEMENT_NODE_IDS), f"node ids found in the block: {found}"
        for module, function in found:
            defined = _defined_test_names(module)
            assert function in defined, (
                f"{relative_path}'s continuation names {module}::{function}, which is not a test "
                f"function defined in {module}. Defined there: {sorted(defined)}"
            )
