"""Additivity of the Phase 19 condition-(c) continuation, proved AT ITS OWN WRITE LOCATION.

The D3 decision is to run condition (c) exactly as pre-registered at ``23a830c``, publish the
literal FAILURE against the criterion as written, and add a dated continuation diagnosing the root
cause beside it — both readings published side by side, neither replacing the other. That is only
honest if the append genuinely cannot touch the verdict it sits beside, so the property is proved
here rather than inherited from the fact that Phases 17 and 18 appended successfully.

**Inheriting it would have been wrong, and this module exists because it was checked.**
``phase18_extraction.append_addendum`` parameterises the placeholder it replaces but hard-codes the
line it writes in place of it. Driven at a Phase 19 location with a Phase 19 placeholder, it emits
``EXTRACTION_SHIP_PENDING_LINE``'s partner — a sentence about *Phase 18's ship decision* — into a
Phase 19 report. ``test_phase18_helper_injects_foreign_provenance_at_a_new_location`` pins that
observed behaviour so the reason ``scripts/_addendum.py`` exists cannot quietly evaporate.
"""

import importlib.util
import pathlib
import tempfile

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent

# The Phase 19 marker PAIR. Both halves travel together to the writer; that is the fix.
P19_PENDING = "**Phase 19 condition (c) diagnosis: not yet recorded.**"
P19_RECORDED = (
    "**Phase 19 condition (c) diagnosis: recorded in the dated continuation at the end of this "
    "file.**"
)

# The literal verdict the continuation must never touch. (c) is run as written and FAILS as
# written; the diagnosis is added beside it, never over it.
RECORDED_VERDICT = (
    "## Verdict\n\nFAILURE — condition (c) as pre-registered at `23a830c`.\n"
    "dialogue PPL 5.8154 vs cap 4.576708.\n\n"
)


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, _ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _p19_report(tmp_path, prefix, tail_marker=P19_PENDING):
    path = tmp_path / "phase19_erasure_report.md"
    path.write_text(
        f"{prefix}{RECORDED_VERDICT}## Condition (c) diagnosis\n\n{tail_marker}\n",
        encoding="utf-8",
    )
    return path


def test_c_diagnosis_addendum_is_additive_at_the_phase19_location():
    """The append adds beside the FAILURE verdict and changes nothing above it."""
    add = _load("_addendum", "scripts/_addendum.py")
    tmp_path = pathlib.Path(tempfile.mkdtemp())

    prefix = "# Phase 19 — Selective Memory Erasure\n\nPublished text that must survive.\n\n"
    path = _p19_report(tmp_path, prefix)
    before = path.read_text(encoding="utf-8")

    addendum = (
        "## Addendum — 2026-08-17 — condition (c) root cause\n\n"
        "`23a830c` capped against `V20_MASKED_DIALOGUE_VAL_PPL` = 4.5733, the adapter-OFF "
        "baseline. Phase 14 measured adapter-on at 5.8154 (+27.16%) and kept it descriptive."
    )
    updated = add.append_addendum(path, addendum, pending=P19_PENDING, recorded=P19_RECORDED)

    assert updated.startswith(prefix), (
        "the append did not carry the published prefix through byte-identically — everything above "
        "the placeholder is shipped text and an append may not touch it"
    )
    assert add._verdict.recorded_verdict(updated) == add._verdict.recorded_verdict(before), (
        "the append moved the recorded FAILURE verdict, which is a rewrite wearing an append's name"
    )
    assert "FAILURE — condition (c) as pre-registered at `23a830c`." in updated, (
        "the literal verdict was lost — the D3 decision publishes it UNCHANGED beside the diagnosis"
    )
    assert "root cause" in updated, "the addendum itself was lost"
    assert P19_PENDING not in updated, (
        "the placeholder survived, so the report still advertises the diagnosis as unrecorded "
        "while carrying the dated section that records it"
    )
    assert P19_RECORDED in updated, "the paired pointer line was not written"
    assert path.read_text(encoding="utf-8") == updated, (
        "append_addendum returned bytes it did not write"
    )


def test_no_foreign_phase_provenance_is_injected():
    """The regression that forced this module: no OTHER phase's marker may appear."""
    add = _load("_addendum", "scripts/_addendum.py")
    extraction = _load("p18", "scripts/phase18_extraction.py")
    tmp_path = pathlib.Path(tempfile.mkdtemp())

    path = _p19_report(tmp_path, "# Phase 19\n\n")
    updated = add.append_addendum(
        path, "## Addendum — 2026-08-17", pending=P19_PENDING, recorded=P19_RECORDED
    )

    assert extraction.EXTRACTION_SHIP_RECORDED_LINE not in updated, (
        "a Phase 18 ship-decision line was written into a Phase 19 report — this is the exact "
        "defect scripts/_addendum.py exists to prevent"
    )
    assert "Phase 18" not in updated, (
        "the Phase 19 continuation carries a Phase 18 provenance claim"
    )


def test_placeholder_count_zero_and_two_both_refuse():
    """Zero is 'not this writer's file'; two is guessing, and guessing is how an append rewrites."""
    add = _load("_addendum", "scripts/_addendum.py")
    tmp_path = pathlib.Path(tempfile.mkdtemp())

    already = _p19_report(tmp_path, "# Phase 19\n\n")
    add.append_addendum(already, "## first", pending=P19_PENDING, recorded=P19_RECORDED)
    with pytest.raises(SystemExit):  # zero — already appended to
        add.append_addendum(already, "## second", pending=P19_PENDING, recorded=P19_RECORDED)

    duplicated = tmp_path / "duplicated.md"
    duplicated.write_text(
        f"# Phase 19\n\n{RECORDED_VERDICT}{P19_PENDING}\n\nprose\n\n{P19_PENDING}\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit):  # two — the writer would have to CHOOSE
        add.append_addendum(duplicated, "## ambiguous", pending=P19_PENDING, recorded=P19_RECORDED)


def test_phase18_helper_injects_foreign_provenance_at_a_new_location():
    """Pins the OBSERVED behaviour of the frozen Phase 18 twin, so the reason for the fix persists.

    Not a criticism of Phase 18 — its helper is correct at its own location and is frozen by
    STAT-05, so it cannot be repaired in place. This records WHY reuse was rejected, with the
    evidence, rather than leaving a future reader to rediscover it.
    """
    extraction = _load("p18", "scripts/phase18_extraction.py")
    tmp_path = pathlib.Path(tempfile.mkdtemp())

    path = _p19_report(tmp_path, "# Phase 19\n\n")
    updated = extraction.append_addendum(path, "## Addendum", placeholder=P19_PENDING)

    assert extraction.EXTRACTION_SHIP_RECORDED_LINE in updated, (
        "the Phase 18 helper no longer injects its own recorded line at a foreign location — if "
        "this is now green, scripts/_addendum.py's justification needs re-reading, not deleting"
    )
    assert P19_RECORDED not in updated, "the Phase 18 helper cannot write the Phase 19 pair"
