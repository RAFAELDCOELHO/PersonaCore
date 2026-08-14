"""Phase 17 multi-persona isolation matrix — the DRIVER (ISO-02 / ISO-03 / SC3).

The PRE-REGISTRATION is ``scripts/phase17_personas.py`` and is IMPORTED here, never retyped: the
six-comparison Holm family, the declared directions, the seeds, the gate rule, the slot list and the
adapter-off row label all live there, pinned by git ancestry. A constant retyped into this file is a
second copy free to stop agreeing with the one the gate was registered on.

Nothing executes at import except the ``sys.path`` bootstrap below. ``main()`` lands in plan 17-06
under a ``__main__`` guard, so an ``importlib`` load in a CPU-only test runs no guard, no model
load, no tokenizer load and no generation. Everything in THIS plan is pure CPU: no torch, no I/O
beyond reading recorded JSON.

LAZY-IMPORT RULE — inherited from ``phase16_persistence:12-15``, and INVERTED for this phase.
``scripts/phase17_persona_facts.py`` holds the 24 minted values at module scope BY DESIGN (it IS the
committed data), so this module must import it LAZILY, inside function bodies, to keep persona value
strings out of the scored driver's own string surface. The same rule covers ``phase14_factset`` and
``phase14_recall``'s scoring primitives. Nothing in the scoring path added by plan 17-04 reads the
material at all — ``assemble_matrix`` takes ``values_by_slot`` as a PARAMETER, which is the
structural half of SC3: the whole scoring core is testable on synthetic values.

**Generation and scoring are two different passes, and that is the architectural decision this file
exists to enforce.** The sweeps write raw completions; this module scores them afterwards. That
makes cell-blindness STRUCTURAL rather than a discipline — ``score_completion`` literally cannot see
which sweep produced a string — makes the whole scoring path unit-testable with no GPU, and makes a
re-score free if the taxonomy ever needs refinement.
"""

import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# `scripts/` is sys.path[0] only when a script in it is run DIRECTLY; an importlib-loaded test
# harness gets no such entry (phase16_persistence.py:34-38 precedent). Insert it explicitly so both
# paths reach the sibling drivers. This is the ONE module-level call this file is permitted, and
# `tests/test_phase17_scoring.py::test_nothing_executes_at_import` asserts exactly that.
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import phase16_persistence as persistence  # noqa: E402  (needs the sys.path insert above)
import phase17_personas as personas  # noqa: E402  (needs the sys.path insert above)

# The key holding a sweep record's per-question entries. A CONSTANT rather than a literal repeated
# at every read, because plan 17-06 writes these records and plan 17-08 reads them: three files
# spelling one string is three places it can stop agreeing, and the failure is a `KeyError` at
# report time, after the GPU sweeps have already been spent. Each entry carries
# `{slot, seed_index, question, fact_id, prompt_ids, completions, stopped}` (RESEARCH F-03).
SWEEP_QUESTIONS_KEY = "questions"

# The record's own row label — `"persona_a" | "persona_b" | "persona_c" | BASE_ROW`. Same reason.
SWEEP_LABEL_KEY = "sweep"

# D-12's four REPORT categories, resolved by `classify` at assembly. Named here so a caller counting
# them cannot invent a fifth bucket by typo: a mistyped key would silently drop the count of the
# category it meant to increment, and a category that reads zero because nothing ever wrote to it is
# indistinguishable in the report from a category that genuinely never occurred.
CATEGORIES = ("diagonal", "leak", "base_prior", "confabulation")


def _prove(condition, message):
    """Loud proof: ``SystemExit`` naming the violated contract (never an ``-O``-strippable assert).

    Same register and same reason as ``phase14_recall._prove``, ``phase16_persistence._prove`` and
    ``phase17_personas._prove``, with THIS module's own prefix — an abort that names the wrong
    driver sends its reader to the wrong file. Never import another driver's ``_prove``: the
    prefix is the whole point. Every message names the contract violated AND the consequence for
    the resulting number, plus the decision id it comes from.
    """
    if not condition:
        raise SystemExit(f"[phase17_isolation] PROOF FAILED: {message}")


# =============================================================================================
# ===== ISO-02 / D-02 — the binding fixture, regrouped by SLOT =================================
# =============================================================================================


def held_out_by_slot():
    """The 104 ``core_held_out`` items bucketed by SLOT — 13 per slot across 8 slots (D-02).

    ``fact_id`` is carried through ONLY as fixture provenance and is never a value source: every
    Phase 14 ``fact_id`` embeds Phase 14's own value (``cand_person_<value>``), which is precisely
    why D-02 keys on SLOT. The slot is resolved through the committed fact set that
    ``load_fixture_items`` already joins against, never parsed out of the id.

    ``seed_index`` is NOT re-enumerated here. ``phase16_persistence.load_fixture_items`` reads it
    VERBATIM off the fixture because the fixture IS the pairing key; re-stamping it in this
    regrouping would silently REPAIR a mismatch instead of surfacing it, and a repaired mismatch is
    indistinguishable, in every number downstream, from a fixture that was never wrong.

    The slot set is checked against ``phase17_personas.CORE_SLOTS`` — the ONE canonical list — and
    deliberately NOT against the 24 minted values in ``scripts/phase17_persona_facts.py``. Two
    things checked against a third cannot drift into agreeing on a wrong answer, whereas two things
    checked against each other can; and keeping the minted material out of this module is what lets
    every test of the scoring core run on synthetic values, which is the structural half of SC3.
    (The material's constant name is deliberately not written out anywhere in this file: plan
    17-04's acceptance criteria grep this source for it, and a docstring mention would make that
    scan hit on prose.)
    """
    items = persistence.load_fixture_items()["core_held_out"]

    by_slot = {}
    for item in items:
        by_slot.setdefault(item.fact.slot, []).append(item)

    shape = [(slot, len(bucket)) for slot, bucket in sorted(by_slot.items())]
    _prove(
        len(by_slot) == personas.SLOTS_EXPECTED
        and all(len(bucket) == personas.QUESTIONS_PER_SLOT for bucket in by_slot.values()),
        f"the fixture regrouped to {shape}, not {personas.SLOTS_EXPECTED} slots x "
        f"{personas.QUESTIONS_PER_SLOT} questions — D-08's n = {personas.SLOTS_EXPECTED} paired "
        "observations and every per-slot denominator rest on that balance holding EXACTLY. An "
        "unbalanced regrouping changes the sign test's n without changing anything visible in the "
        "reported rate, so the gate would be priced against a test that was never registered",
    )
    _prove(
        set(by_slot) == set(personas.CORE_SLOTS),
        f"the fixture's slots {sorted(by_slot)} and the committed CORE_SLOTS "
        f"{sorted(personas.CORE_SLOTS)} disagree (D-02). The minted material is authored against "
        "CORE_SLOTS, so a fixture slot missing from that list has no persona value to score "
        "against and a CORE_SLOTS entry missing from the fixture is a column of the matrix with no "
        "questions behind it",
    )
    return {slot: tuple(bucket) for slot, bucket in by_slot.items()}


# =============================================================================================
# ===== SC3 / D-12 / D-17 — the CELL-BLIND scorer ==============================================
# =============================================================================================


def score_completion(completion, slot_values):
    """D-12's labels for one completion: the personas whose value it contains, as a ``frozenset``.

    **The ONLY function in this module that touches a completion string, and it takes no cell.**
    The parameters are exactly ``(completion, slot_values)``: a string, and one slot's
    ``{persona_label: value}`` mapping. There is no ``(i, j)``, no notion of "own persona" and no
    way to learn which sweep produced the string — diagonal-vs-leak is resolved ENTIRELY at
    assembly, in ``classify`` (SC3, pinned by ``inspect.signature`` and by an AST scan of this
    function's body in ``tests/test_phase17_scoring.py::test_scorer_is_cell_blind``).

    An empty frozenset is D-12's ``none``. Containment is
    ``phase14_recall.contains_value`` — IMPORTED, never re-implemented — so the boundary rule is
    identical to the one behind every published Phase 14 and Phase 16 rate: substring after
    lowercase -> ``detokenize`` -> whitespace collapse -> strip. The whitespace collapse is
    load-bearing rather than cosmetic; the measured case ``'i am a mort of musician'`` shows
    byte-level BPE landing a space inside what should be one word.

    D-17 — a DOUBLE MATCH returns a two-member frozenset rather than picking a winner. A priority
    order would be an arbitrary tiebreak biasing whichever persona happens to sort first, and a
    double match is itself evidence about interference: collapsing it to one label deletes exactly
    the observation the matrix exists to record. The return domain stays D-12's four labels, now as
    a set over them.
    """
    from phase14_recall import contains_value  # LAZY — see the module docstring's LAZY-IMPORT RULE

    return frozenset(
        label for label, value in slot_values.items() if contains_value(completion, value)
    )
