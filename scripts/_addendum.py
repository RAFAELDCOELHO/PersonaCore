"""The ONE append-only continuation writer, with its marker PAIR passed in rather than assumed.

Phase-neutral and dependency-free on purpose, in ``_verdict``'s register, so the cheap drivers and
the CPU-only tests can both take it without dragging in torch or a fact set.

**Why a third copy exists at all.** ``phase17_isolation.append_addendum`` and
``phase18_extraction.append_addendum`` are the same writer twinned, and both live inside files that
STAT-05's ancestry guards have frozen — every commit touching them must be an ancestor of every
committed ``results/phase17_*`` / ``results/phase18_*`` first-add, so neither can be edited now
without reddening ``tests/test_phase16_prereg.py``. The fix below could not be applied in place,
and deleting-and-re-adding to get around that would launder the very ordering those guards prove.

**The defect this fixes, measured rather than reasoned about.** Phase 18 parameterised the
placeholder it REPLACES (``placeholder=EXTRACTION_SHIP_PENDING_LINE``, made a keyword so S-6's
three surfaces could share one implementation) but left the line it replaces it WITH hard-coded to
``EXTRACTION_SHIP_RECORDED_LINE``. Half the pair travels with the caller and half does not.
Appending to a Phase 19 document through it, passing a Phase 19 placeholder, writes:

    **Phase 18 ship decision: recorded in the dated continuation at the end of this file.**

into a report that is not Phase 18's — a false provenance claim, emitted by a helper whose whole
purpose is to not alter published text. The append-only property held; the PROVENANCE did not, and
neither twin's assertions could have caught it: they compare the bytes they produce against the
bytes they were handed, and the injected line is present in both sides of that comparison.

So both halves are REQUIRED keywords here. A caller cannot inherit another phase's marker by
omission, because there is nothing to omit.

Everything else is Phase 17/18's writer unchanged, deliberately: textual and surgical rather than a
re-render (a ``render_report`` rewrites the WHOLE file and would destroy every hand-appended
section along with the recorded verdict), no override flag, no rewrite path. A flag that disables
the guard becomes routine, and an operator who routinely passes it eventually passes it after a
human HAS recorded a verdict — at which point the guard destroys exactly the evidence it exists to
protect. The recovery is this project's usual one: delete the file in a reviewed commit, so the
removal is visible in the diff.

All three checks run on the PRODUCED BYTES rather than on the construction above them.
"""

import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import _verdict  # noqa: E402  (needs the sys.path insert above)


def _prove(condition, message):
    """``SystemExit`` on a broken invariant — phase17/18's register, so callers catch one type."""
    if not condition:
        raise SystemExit(f"[_addendum] {message}")


def append_addendum(path, addendum, *, pending, recorded):
    """APPEND a section, replacing EXACTLY one ``pending`` line with its ``recorded`` partner.

    ``pending`` and ``recorded`` are BOTH required keywords — that pairing is the whole reason this
    module exists (see the header). Passing one phase's ``pending`` with another's ``recorded`` is
    still possible, but it can no longer happen by DEFAULT, which is how it happened before.

    The placeholder must occur EXACTLY once. Zero means the file is not the shape this writer was
    committed against — already appended to, or not this writer's output at all. More than one
    means choosing between them, and choosing is how an append silently becomes a rewrite.
    """
    path = pathlib.Path(path)
    text = path.read_text(encoding="utf-8")

    found = text.count(pending)
    _prove(
        found == 1,
        f"{path} carries {found} occurrence(s) of the placeholder line {pending!r}, and this "
        f"writer replaces EXACTLY ONE. At {found} there is no unambiguous line to replace — zero "
        "means the file is not the shape this writer was committed against, and more than one "
        "means choosing between them, which is how an append silently becomes a rewrite",
    )

    before, after = text.split(pending)
    updated = before + recorded + after
    if not updated.endswith("\n"):
        updated += "\n"
    updated = updated + "\n" + addendum.rstrip("\n") + "\n"

    _prove(
        _verdict.recorded_verdict(updated) == _verdict.recorded_verdict(text),
        f"appending to {path} changed its recorded `## Verdict` section. The verdict is committed "
        "evidence and an addendum may only be ADDED beside it — a writer that moves it has "
        "rewritten the report under cover of an append",
    )
    _prove(
        updated.startswith(before) and addendum.rstrip("\n") in updated,
        f"the rewritten {path} does not carry its original prefix byte-identically, or lost the "
        "addendum it was appending — the append-only property is the whole guarantee this helper "
        "offers and it is checked on the produced bytes, not assumed from the construction",
    )

    path.write_text(updated, encoding="utf-8")
    print(f"[_addendum] appended a dated section to {path}")
    return updated
