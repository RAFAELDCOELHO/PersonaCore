"""The ONE copy of the whitespace-normalizing prose read, shared by every correction sweep.

Phase-neutral and dependency-free on purpose: this module imports NOTHING — not even ``re`` — so a
cheap driver, a CPU-only test and a pre-commit doc sweep can all take it without dragging in torch,
the fact set, or a third-party parser. RPT-03's zero-new-runtime-dependency streak is untouched.

**Why one copy.** ``.planning/RETROSPECTIVE.md:179-181`` records a MEASURED defect: a single-line
``grep -c "three reductions"`` returned **0** on a file that contained the phrase, because the
source line-wraps it as ``"the three\\nreductions"``. A verified absence was a FALSE absence.
``.planning/milestones/v3.0-MILESTONE-AUDIT.md:104-111`` (defect W2, ``resolved_by: 5703bbe``)
gives that concrete failing string and records the workaround: *"Verified before commit with a
WHITESPACE-NORMALISED sweep."* The normalisation was done by hand, once, and the lesson was then
written down — which is v3.0's OTHER recorded lesson, that recording a lesson is not the same as
scheduling one. ``.planning/research/PITFALLS.md:1048`` prescribes this exact five-line module by
name and names Phase 20 to build it, on the reasoning that the one-definition-per-statistic
discipline already covering ``holm`` and ``wilson_upper_bound`` should extend to the thing that
checks the prose. RPT-02 is that conversion: a note becomes a mechanism.

**D-23 — the LEADING UNDERSCORE is the mechanism that keeps this file free.**
``scripts/mitigation_gate.py`` freezes at its first commit: once any ``results/phase20_*`` artifact
is committed, every later commit touching the pin reddens the ancestry guard permanently, and
``git rm`` + re-add cannot undo it (the guard takes ``adds[-1]``, the EARLIEST add). A phase-neutral
utility must not inherit an immutability that only makes sense for a judgment rule — it has to keep
serving Phases 21-28. The underscore is what buys the exemption, and it is an fnmatch fact rather
than a convention: ``_prose.py``, like ``_addendum.py`` and ``_verdict.py``, is matched by NONE of
``phase16_*.py`` / ``phase17_*.py`` / ``phase18_*.py`` / ``phase19_*.py`` / ``phase20_*.py``.

**The honest caveat this repository already states.** That precedent is STRUCTURAL, not HISTORICAL.
``_addendum.py``'s last commit (``f8441ec``, 2026-08-17) predates the first ``results/phase19_*``
add (``7293ec9``, 2026-08-18), so neither helper has actually been edited after an artifact existed.
The exemption is proved by the pattern, never by a survived edit.
"""


def normalized(text):
    """``text`` with every run of whitespace collapsed to a single space, ends stripped.

    ``str.split()`` with no argument splits on ANY run of whitespace — spaces, tabs, ``\\n``,
    ``\\r\\n``, form feeds — and discards the empty strings, so newlines, repeated spaces and
    leading/trailing whitespace all collapse in one operation.

    ONE exported name, deliberately. Callers write ``normalized(phrase) in normalized(text)``.
    There is no ``search()`` wrapper, no case-fold flag and no ``count()`` helper: add one when a
    second call site actually needs it, not in advance of one.
    """
    return " ".join(text.split())
