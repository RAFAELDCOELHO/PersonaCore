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


# =============================================================================================
# ===== D-12 / D-13 — the four REPORT categories, and the only code that knows (i, j) ==========
# =============================================================================================


def classify(labels, own, base_texts, completion):
    """D-12's scorer labels resolved into the four REPORT categories, at assembly.

    **This function knows the cell and the scorer does not, and that separation IS SC3.** ``labels``
    is ``score_completion``'s frozenset; ``own`` is the row's persona label, **or ``None`` for the
    adapter-off base row**.

    ``base_texts`` is the set of NORMALIZED completions the ISO-03 adapter-off column produced for
    THIS slot, under the same questions, seeds, ``forbid_ids`` and ``stop_ids`` — D-13's empirical
    base prior, DERIVED rather than scored. ``phase14_factset.BASE_PRIOR_SEEDS`` is deliberately not
    consulted: it is a screening seed list for candidate values covering **2 of the 8 core slots**
    (``pet_name`` and ``hometown`` only), never an enumeration of what the base may say, so matching
    against it could not be a complete test even on the two slots it does cover. The adapter-off
    column is the instrument, which is why ISO-03 requires it.

    The order is the contract:

    1. ``own is not None and own in labels`` -> ``"diagonal"`` — the row's own value appeared.
    2. ``own is None and labels`` -> ``"base_prior"`` — see below. **Not a leak.**
    3. ``labels`` -> ``"leak"`` — some OTHER persona's value appeared under this adapter.
    4. the completion coincides with the adapter-off column's own output -> ``"base_prior"``.
    5. otherwise -> ``"confabulation"`` — its own category, never sharing a cell with a leak.

    **Why branch 2 exists and what breaks without it.** ``base_texts`` is a membership test on the
    WHOLE completion string, so it cannot separate "the base produced something containing persona
    j's value" from "the base produced something else": a base completion carrying j's value has
    non-empty ``labels`` and would fall straight through to step 3 and score ``leak`` — the base
    leaking to itself, from an adapter that does not exist. Cell ``(base, j)``'s rate would then
    never be computed, and that rate is the ONLY quantitative separator of "adapter i leaked
    persona j's value" from "the base was going to say that anyway" (RESEARCH:900). Both the
    report's §The Matrix and D-10's all-fail branch (b) read that number, so removing branch 2
    silently deletes the control while leaving every other number looking intact.
    """
    if own is not None and own in labels:
        return "diagonal"
    if own is None and labels:
        return "base_prior"
    if labels:
        return "leak"

    from phase14_recall import normalize  # LAZY — see the module docstring's LAZY-IMPORT RULE

    if normalize(completion) in base_texts:
        return "base_prior"
    return "confabulation"


def base_texts_by_slot(base_record):
    """``{slot: frozenset(normalized completions)}`` from the recorded adapter-off sweep (D-13).

    The empirical base prior, per slot, in the normalization ``classify``'s membership test uses —
    a set built under a different normalizer is a set that does not match where it matters.

    Both proofs guard the same failure: a mis-selected record produces an EMPTY base-prior set, and
    an empty set silently converts every base prior into a ``confabulation``. That reclassification
    is invisible in the cell rates and changes only the category counts, so nothing else in the
    report goes red while D-13's derivation quietly stops existing.

    The slot set is checked against ``phase17_personas.CORE_SLOTS`` rather than against a second
    read of the fixture: ``held_out_by_slot`` already proves the fixture equals ``CORE_SLOTS``, so
    checking both against that one canonical list is the same guarantee without a second disk read
    — and two things checked against a third cannot drift into agreeing on a wrong answer.
    """
    from phase14_recall import normalize  # LAZY — see the module docstring's LAZY-IMPORT RULE

    label = base_record.get(SWEEP_LABEL_KEY)
    _prove(
        label == personas.BASE_ROW,
        f"base_texts_by_slot received a record whose {SWEEP_LABEL_KEY!r} is {label!r}, not the "
        f"pre-registered adapter-off row {personas.BASE_ROW!r} (ISO-03). Deriving the base prior "
        "from an ADAPTER sweep would make every completion that adapter produced count as 'what "
        "the base was going to say anyway', which is exactly the excuse a leak needs",
    )

    by_slot = {}
    for entry in base_record[SWEEP_QUESTIONS_KEY]:
        by_slot.setdefault(entry["slot"], set()).update(
            normalize(completion) for completion in entry["completions"]
        )
    _prove(
        set(by_slot) == set(personas.CORE_SLOTS),
        f"the base record covers slots {sorted(by_slot)} but the committed CORE_SLOTS are "
        f"{sorted(personas.CORE_SLOTS)} (D-13). A slot with no base texts has an EMPTY base-prior "
        "set, and an empty set turns every base prior in that slot into a confabulation — the "
        "cell rates are unchanged, so nothing goes red and the derivation just stops working",
    )
    return {slot: frozenset(texts) for slot, texts in by_slot.items()}


def assemble_matrix(sweep_records, values_by_slot, base_texts):
    """The 12 cells: the 3x3 adapter block plus the three base cells ``(base, j)`` (ISO-03).

    ``sweep_records`` is **all four records, the base among them** — the base row is a COMPUTED row
    of the same matrix under the same rate definition, not a lookup table (RESEARCH:900: *"The base
    column is cell ``(base, j)`` for each j"*). ``values_by_slot`` is ``{slot: {persona: value}}``,
    passed IN rather than read from the committed material, so the whole scoring path stays
    independent of the 24 minted values and every test of it runs on synthetic ones (SC3).
    ``base_texts`` is ``base_texts_by_slot``'s result.

    Cell ``(row, j)`` counts a QUESTION when ANY of that row's draws for it contained persona j's
    value — STAT-01's question unit, max over draws. Returns per cell:

    * ``per_slot`` — ``{slot: ((k, n), ...)}`` with ``k`` in ``{0, 1}`` and ``n`` always 1, which is
      exactly ``cluster_bootstrap``'s input shape with the SLOT as the cluster;
    * ``n_answerable`` / ``n_questions`` / ``rate = n_answerable / n_questions``;
    * the four ``CATEGORIES`` counts and ``contradiction_draws``.

    **STAT-01 lives here (RESEARCH F-11).** ``phase16_persistence.fact_signs`` reads ``["rate"]``
    off whatever dict it is handed, and ``aggregate_by_fact``'s ``rate`` is ``sum(k)/sum(n)`` — the
    DRAW rate, ~0.33 on the real gated tier where the question rate is ~0.87. This function builds
    the QUESTION rate and proves it against the committed ``phase17_personas.SIGN_UNIT`` literal, so
    the declared unit and the computed unit cannot drift apart unnoticed. Phase 17 builds its own
    ``{slot: [(k, n), ...]}`` and both ``cluster_bootstrap`` and ``fact_signs`` are key-agnostic, so
    no Phase 16 function is widened and none is called to group these records.

    **The four category counts are a ROW property, reported on each of that row's three cells.**
    ``classify`` takes no ``j`` by design (D-12), so ``diagonal`` / ``leak`` / ``base_prior`` /
    ``confabulation`` partition the row's 104 questions by what the row's OWN completions contained
    — they are identical across ``(row, a)``, ``(row, b)`` and ``(row, c)`` and are NOT a per-column
    number. The per-column number is ``n_answerable`` / ``rate``. A reader who takes
    ``matrix[(a, b)]["leak"]`` as "how often B's value appeared under adapter A" has read the wrong
    field; that quantity is ``matrix[(a, b)]["n_answerable"]``.

    No aggregate over the cells is computed or returned (STAT-06: SC5 forbids gating one, and a
    printed number gets quoted as a gate), and nothing here orders the three personas by diagonal
    (D-15: with one seed per persona a between-persona difference confounds content with
    initialization). The base cells are REPORTED and never GATED — ``HOLM_FAMILY_CELLS`` is derived
    over ``PERSONAS`` only, and ``assert_phase17_family_closed`` refuses any pair naming
    ``BASE_ROW``.
    """
    from phase14_recall import find_contradictions  # LAZY — see the LAZY-IMPORT RULE

    _prove(
        personas.SIGN_UNIT == "question",
        f"SIGN_UNIT is pre-registered as {personas.SIGN_UNIT!r} but this assembly computes "
        "n_answerable / n_questions, the QUESTION rate (STAT-01 / RESEARCH F-11). fact_signs signs "
        "on whatever ['rate'] holds, so a declared unit that no longer matches the computed one "
        "would put the sign test on a quantity nobody declared — and the two units differ by more "
        "than a factor of two on the real gated tier",
    )
    _prove(
        set(values_by_slot) == set(personas.CORE_SLOTS)
        and all(set(row) == set(personas.PERSONAS) for row in values_by_slot.values()),
        f"values_by_slot covers {sorted(values_by_slot)} for personas "
        f"{sorted({label for row in values_by_slot.values() for label in row})}, but the matrix is "
        f"{sorted(personas.CORE_SLOTS)} x {sorted(personas.PERSONAS)}. A missing entry would drop "
        "a column of the matrix to a rate computed over fewer slots than its denominator claims",
    )

    records = tuple(sweep_records)
    seen = tuple(record[SWEEP_LABEL_KEY] for record in records)
    expected = set(personas.PERSONAS) | {personas.BASE_ROW}
    _prove(
        len(records) == len(personas.PERSONAS) + 1,
        f"assemble_matrix received {len(records)} sweep record(s) ({sorted(seen)}) but the matrix "
        f"is built from {len(personas.PERSONAS)} adapter sweeps PLUS the adapter-off row. The base "
        "row is NOT optional (ISO-03): handing over only the adapter records leaves cells "
        "(base, j) uncomputed and publishes an EMPTY BASE COLUMN as 'the control', which is the "
        "one number that separates a real leak from a prior the base already had",
    )
    _prove(
        set(seen) == expected and len(set(seen)) == len(seen),
        f"the sweep records name {sorted(seen)} but the matrix rows are {sorted(expected)} "
        "(ISO-03). A duplicated or mislabelled record fabricates a row: the same completions would "
        "be scored twice under two names, and one genuine sweep would never be scored at all",
    )

    matrix = {}
    for record in records:
        row = record[SWEEP_LABEL_KEY]
        own = row if row in personas.PERSONAS else None
        entries = record[SWEEP_QUESTIONS_KEY]
        _prove(
            entries,
            f"sweep record {row!r} carries no questions — an empty row would publish a rate of "
            "0/0 or abort inside the bootstrap, and neither reads as 'this sweep never ran'",
        )

        categories = dict.fromkeys(CATEGORIES, 0)
        per_slot = {label: {} for label in personas.PERSONAS}
        contradiction_draws = dict.fromkeys(personas.PERSONAS, 0)

        for entry in entries:
            slot = entry["slot"]
            slot_values = values_by_slot[slot]
            # D-10's contradiction lexicon, repriced for this phase: the competing values for THIS
            # slot are exactly the other personas' values for it, so no new editorial judgment is
            # introduced — the same property that made Phase 14's lexicon auditable.
            lexicon = set(slot_values.values())
            completions = entry["completions"]
            texts = base_texts.get(slot, frozenset())

            # The QUESTION unit (STAT-01): a question counts once if ANY of its draws carried the
            # value. The union is taken across draws BEFORE anything is classified, so the label
            # set a question is judged on is the same one its cells are counted on.
            question_labels = frozenset().union(
                *(score_completion(completion, slot_values) for completion in completions)
            )
            drawn = [classify(question_labels, own, texts, done) for done in completions]
            # `question_labels` is fixed across the draws, so branches 1-3 return the same category
            # for every draw and only branch 4 can vary — a question is a base prior if ANY draw
            # coincided with the adapter-off column, the same max-over-draws rule as n_answerable.
            categories["base_prior" if "base_prior" in drawn else drawn[0]] += 1

            for label in personas.PERSONAS:
                hit = 1 if label in question_labels else 0
                per_slot[label].setdefault(slot, []).append((hit, 1))
                contradiction_draws[label] += sum(
                    1
                    for done in completions
                    if find_contradictions(done, slot_values[label], lexicon)
                )

        if own is None:
            _prove(
                categories["diagonal"] == 0 and categories["leak"] == 0,
                f"the adapter-off row scored {categories['diagonal']} diagonal and "
                f"{categories['leak']} leak questions, which is impossible by construction: with "
                "own = None, classify's branch 1 cannot fire and branch 2 catches every non-empty "
                "label set before branch 3. A non-zero count here means branch 2 was removed or "
                "`own` was mis-threaded, and the base row is being counted as evidence AGAINST the "
                "adapters (ISO-03)",
            )

        for label in personas.PERSONAS:
            questions = per_slot[label]
            n_answerable = sum(k for pairs in questions.values() for k, _n in pairs)
            n_questions = sum(len(pairs) for pairs in questions.values())
            matrix[(row, label)] = {
                "per_slot": {slot: tuple(pairs) for slot, pairs in questions.items()},
                "n_answerable": n_answerable,
                "n_questions": n_questions,
                "rate": n_answerable / n_questions,
                "contradiction_draws": contradiction_draws[label],
                **categories,
            }

    return matrix
