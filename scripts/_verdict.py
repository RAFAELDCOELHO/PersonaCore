"""The ONE copy of the anchored ``## Verdict`` section read, shared by every clobber guard.

Phase-neutral and dependency-free on purpose: ``re`` is the only import, so the cheap drivers
and the CPU-only tests can both take it without dragging in torch or the fact set.

**Why one copy.** CR-02 was five hand-copied instances of the same read, four of them written as
``text.split("## Verdict")[-1]`` — the tail after the LAST occurrence of a literal that also
appears in prose. A report that mentions ``## Verdict`` in a later section (the D-12 ship-decision
comment quotes the heading) put that tail in the prose, which never says ``PENDING``, so the guard
concluded a verdict had been recorded and refused every legitimate re-drive of an interrupted run.
``--force`` — which disables the guard outright — became the only way through, and an operator who
learns ``--force`` is always required passes it after a human HAS recorded a verdict. The guard
then destroys precisely the hand-written evidence it exists to protect. Fixing one call site left
four others to be copy-pasted forward; the regex lives here so the next site imports it instead.

``None`` and an empty body are DELIBERATELY different: a file with no ``## Verdict`` section at
all is not this writer's output, and the caller must refuse it rather than overwrite it blind.
"""

import re

# Anchored on the SECTION: from a ``## Verdict`` heading at line start up to the next ``## ``
# heading or end of file. A prose mention of the literal cannot be mistaken for the section.
VERDICT_SECTION = re.compile(r"^## Verdict\b(.*?)(?=^## |\Z)", re.M | re.S)


def recorded_verdict(text):
    """The body of the FIRST ``## Verdict`` section — ``None`` when the file has no such section."""
    section = VERDICT_SECTION.search(text)
    return section.group(1) if section else None
