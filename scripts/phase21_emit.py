"""THE publication entry point for both ``results/phase21_*.json`` records.

    .venv/bin/python scripts/phase21_emit.py

**WHY THIS FILE EXISTS AT ALL.** ``21-REVIEW.md`` CR-02 found both committed Phase-21 artifacts
carrying a ``provenance.git_sha`` under which their own emitter was not yet defined —
``phase21_privacy_unit.json`` recorded ``fa97b666`` (no ``emit_privacy_unit``) and
``phase21_multiplicity.json`` recorded ``17b3c856`` (no ``emit_multiplicity``). Both were emitted
from a dirty tree by an ad-hoc ``python -c`` one-liner that lives in no file, so there was nothing
to guard and nothing to re-run. This is that command, written down and guarded.

**WHY THE GIT CHECK IS THE FIRST THING THIS FILE DOES** — the same reason
``scripts/phase21_golden_capture.py:136`` gives, applied to a different falsehood. There, a
fixture captured after the edit turns every downstream identity assertion into a tautology; here,
a record written from a dirty tree names a commit that cannot regenerate it, which is the QA-02
reproducibility guarantee (seed + git SHA + config) failing on the two files that exist to
demonstrate it. So it is MECHANICAL rather than a promise: :func:`_refuse` runs at module scope
AHEAD of the ``phase21_unit_record`` import below, and again in :func:`main` at call time.

**WHY THE MODULE-SCOPE CHECK IS HERE AND NOT AT THE TOP OF ``phase21_unit_record.py``**, which is
what CR-02 literally prescribed. That placement was implemented and MEASURED first.
``phase21_golden_capture`` is imported by no test, so its import-time refusal costs the suite
nothing. ``phase21_unit_record`` is imported by ``tests/test_phase21_unit_record.py:35`` and
``tests/test_phase21_multiplicity.py``, and a ``SystemExit`` raised while pytest is COLLECTING is
an ``INTERNALERROR`` that aborts the entire run rather than failing one module — observed:
``no tests ran in 3.63s`` for the whole suite, on a tree whose only dirt was the two files being
edited to FIX CR-02. A guard that makes the test suite unusable during exactly the work that
precedes a re-emission does not survive contact with the next developer.

Placing it here is not a weakening — it is strictly stronger than the prescribed site. A check at
the top of ``phase21_unit_record.py`` runs *after* Python has already read and compiled that
file, so it can never establish that the emitter itself is committed. Running it here, BEFORE the
import, covers the emitter's own bytes as well as everything it imports. The property CR-02
actually asks for ("the recorded SHA names a commit where the emitter exists") is therefore
enforced at the only place that can enforce it.

The refusal is ALSO enforced un-bypassably inside ``phase21_unit_record._write`` — the one seam
both artifacts' bytes pass through — so skipping this driver does not skip the guard. This file
is the ergonomic, recorded route; ``_write`` is the mechanism.

**WHAT THIS FILE DELIBERATELY DOES NOT DO.** It does not compute, measure, or decide anything.
Every number lives in ``phase21_unit_record``; a driver that reached into a document to adjust a
field would be a second author of a record whose whole claim is that it was computed at write
time from the frozen pin.
"""

import pathlib
import sys

from personacore.provenance import refuse_if_dirty

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))

_DETAIL = (
    "Both results/phase21_*.json record `provenance.git_sha()` = HEAD at write time. Emitting "
    "from a dirty tree publishes a commit that does not contain the code that produced the "
    "bytes, which is 21-REVIEW.md CR-02 exactly. Commit first, then re-run this script.\n"
    "The two artifact paths are EXCLUDED from this check: re-emitting requires deleting the "
    "previous record first, and that deletion is itself a dirty tree. The recorded SHA claims "
    "the CODE and INPUTS reproduce these bytes — never that the output file was untouched."
)

# The artifact paths are excluded, but this driver must not import `phase21_unit_record` to learn
# them — that import is what the check below exists to gate. They are spelled out here and the
# spelling is ASSERTED against `ARTIFACTS` in `main()`, once the import is legitimate, so a
# divergence is a loud failure rather than a silently-narrowed guard.
_ARTIFACT_PATHS = (
    "results/phase21_privacy_unit.json",
    "results/phase21_multiplicity.json",
)
_PATHSPEC = (".", *(f":(exclude){path}" for path in _ARTIFACT_PATHS))


def _refuse():
    """Abort unless the tree is clean apart from the two artifacts. See this module's docstring."""
    return refuse_if_dirty(who="phase21_emit", detail=_DETAIL, pathspec=_PATHSPEC, cwd=_ROOT)


_refuse()  # BEFORE the import below — the check cannot establish anything about it afterwards.

import phase21_unit_record as r  # noqa: E402  (the path insert above is what finds it)


def main():
    _refuse()  # again at call time: the import may have happened arbitrarily long ago

    # The pathspec above is a hand-spelled copy, because it has to run before the import that
    # would supply the real one. Now that the import is done, prove the copy is faithful — a
    # guard watching a path the emitter does not write is a guard watching nothing.
    declared = {str(path.relative_to(r._ROOT)) for path in r.ARTIFACTS.values()}
    assert declared == set(_ARTIFACT_PATHS), (
        f"this driver excludes {sorted(_ARTIFACT_PATHS)} from its dirty check but "
        f"phase21_unit_record.ARTIFACTS writes {sorted(declared)} — the excluded set and the "
        "written set must be the same paths, or the guard is scoped to files nobody writes"
    )

    emitters = (
        ("privacy_unit", r.emit_privacy_unit),
        ("multiplicity", r.emit_multiplicity),
    )
    for name, emit in emitters:
        path = r.ARTIFACTS[name]
        document = emit()
        print(f"[phase21_emit] wrote {path.relative_to(r._ROOT)}")
        print(f"[phase21_emit]   git_sha {document['provenance']['git_sha']}")
        print(f"[phase21_emit]   written {document['provenance']['written_utc']}")


if __name__ == "__main__":
    main()
