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

import _verdict  # noqa: E402  (needs the sys.path insert above)
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

# The four sweeps: three adapters plus the ISO-03 adapter-off row. DERIVED from the
# pre-registration, never a retyped four-tuple — a hand-typed list is a second copy free to stop
# agreeing with the personas the gate was registered on.
SWEEPS = personas.PERSONAS + (personas.BASE_ROW,)

# The three provenance fields every sweep record carries about its weights. Constants for the same
# reason as `SWEEP_QUESTIONS_KEY`: the sweep writer and `assert_sweeps_ran_on_distinct_weights` are
# the two sides of one contract, and a literal spelled twice is a `KeyError` at report time — after
# the four GPU sweeps have already been spent.
#
# The three are NOT interchangeable and none may stand in for another:
#   * `lora_b_sha256`        — WHICH WEIGHTS were resident, digested off the LIVE tensors.
#   * `adapter_file_sha256`  — WHICH FILE was read, digested off the bytes on disk.
#   * `adapter_enabled`      — WHETHER THE DELTA BRANCH could execute at all.
LORA_B_DIGEST_KEY = "lora_b_sha256"
ADAPTER_FILE_DIGEST_KEY = "adapter_file_sha256"
ADAPTER_ENABLED_KEY = "adapter_enabled"

# ISO-03 — what makes the adapter-off column a control, and what does NOT. Written down because the
# wrong version of this was believed during planning and would otherwise be re-derived.
#
# `personacore.lora.adapter_disabled` flips `LoRALinear.enabled`, which is a plain Python bool
# (`src/personacore/lora/layer.py:35`) deliberately kept out of `state_dict()` so it can never
# pollute an artifact (D-05). It therefore leaves `lora_B` EXACTLY AS LOADED. For the base sweep
# that is Phase 14's `checkpoints/persona_adapter.pt`, which `phase14_recall.load_adapted_model`
# loads by default — resident, and inert.
#
# **NO WEIGHT DIGEST CAN WITNESS "THE ADAPTER WAS OFF."** The flag lives outside every tensor, so
# the record carries two independent fields instead of asking one to prove the other's claim:
# `lora_b_sha256` says which weights were resident, `adapter_enabled` says whether the delta branch
# could execute. The base sweep additionally proves the second AT RUNTIME by asserting every
# `LoRALinear.enabled` is False inside the `adapter_disabled` context.
#
# An earlier draft of this phase expected the base sweep to carry the all-zero `lora_B` digest. That
# is FALSE against every real run, and an assertion built on it would abort the report after the
# four sweeps were paid for. This note exists so the expectation is not re-derived from the same
# wrong premise.
BASE_COLUMN_NOTE = (
    "the adapter-off column is a control because `adapter_disabled` gates the delta branch off, "
    "NOT because its weights are zeroed: the context manager flips a plain Python bool that never "
    "enters state_dict(), so the base sweep's live lora_B digest is whichever adapter was resident "
    "(Phase 14's persona_adapter.pt, loaded by default). `adapter_enabled` is therefore the ONLY "
    "field that can witness inertness, and `lora_b_sha256` is never asked to."
)


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


# =============================================================================================
# ===== ISO-04 — the adapter-swap canary, in BOTH layers =======================================
# =============================================================================================
#
# All three personas share an identical `lora_` key set, identical shapes and an identical
# `lora_config`, so every audit in `load_adapter_weights` — keys, shape/dtype and scale — passes for
# the WRONG artifact. The load path is structurally silent about adapter identity, which is exactly
# the property ISO-04 exists to close.


def lora_b_digest(model):
    """sha256 over every LIVE ``lora_B`` tensor, in sorted module-name order.

    **The LIVE tensors, deliberately, and NOT the artifact file's digest.** A file digest proves
    which file was READ; it can never prove the tensors reached the model — a load that silently
    no-ops leaves the file digest looking perfect. Both digests are recorded per sweep for exactly
    that reason (``LORA_B_DIGEST_KEY`` and ``ADAPTER_FILE_DIGEST_KEY``), and neither substitutes for
    the other: identical live digests mean two sweeps ran on the same weights, identical file
    digests mean the same artifact was named twice, and each can happen without the other.

    Bytes are read off a detached CPU copy so the digest is stable across MPS, CUDA and CPU — the
    same discipline as ``phase16_persistence.forbid_digest``, for the same reason.
    """
    import hashlib

    from personacore.lora import LoRALinear

    resident = {
        name: module.lora_B
        for name, module in model.named_modules()
        if isinstance(module, LoRALinear)
    }
    digest = hashlib.sha256()
    for name in sorted(resident):
        digest.update(resident[name].detach().to("cpu").contiguous().numpy().tobytes())
    return digest.hexdigest()


def load_adapter_with_canary(model, artifact, *, label):
    """ISO-04's IN-PROCESS layer: load an adapter, prove the load did something, return a digest.

    Snapshots every ``lora_B``, calls ``personacore.lora.load_adapter_weights`` (whose three audits
    run BEFORE any tensor is copied — never a bare ``strict=False``, which half-applies and raises
    at the end on a corrupted model), then proves two things the audits structurally cannot see:
    that at least one ``lora_B`` MOVED, and that no ``lora_B`` is entirely zero.

    **The LIMIT of this layer, which is why the cross-process layer is the unskippable half.** In a
    fresh process the prior state is always Phase 14's adapter — that is what ``load_adapted_model``
    loaded — so "at least one ``lora_B`` changed" is satisfied by loading ANY Phase 17 artifact. It
    catches a double load and it catches an identity adapter. **It cannot tell persona A's artifact
    from persona B's.** That discrimination is ``assert_sweeps_ran_on_distinct_weights``'s job:
    pairwise-distinct LIVE digests across the four records, plus the artifact file digests recorded
    beside them.

    **Where this canary lives, and why NOT inside ``load_adapter_weights`` (declined with a measured
    reason, not overlooked).** Putting a "some ``lora_B`` changed / none is entirely zero" assertion
    at ``src/personacore/lora/inject.py``'s choke point would be the smaller diff and would cover
    ``scripts/personalize_demo.py`` and every future consumer rather than only this driver. That is
    a real advantage, and it is declined because ``load_adapter_weights`` legitimately supports
    RE-APPLYING AN IDENTICAL ADAPTER ONTO THE MODEL IT CAME FROM. The measured case is
    ``tests/test_lora_artifact.py::test_real_slim_two_artifact_load_cpu``: it nudges ``lora_B``,
    exports that model's own adapter, and loads it straight back onto the SAME model — so no
    ``lora_B`` changes, and a must-differ assertion at the choke point would refuse a committed v2.0
    test that is exercising the export/load round-trip correctly. (``checkpoints/model_slim.pt``
    exists in this tree, so that test's ``skipif`` does not engage and it runs locally.)

    The general principle: a same-adapter re-apply is a VALID use of the library call, so "the
    adapter resident after this load must DIFFER from the one before it" is a **Phase 17 run
    contract**, not a library invariant. It belongs with the run.
    """
    import torch

    from personacore.lora import LoRALinear, load_adapter_weights

    before = {
        name: module.lora_B.detach().clone()
        for name, module in model.named_modules()
        if isinstance(module, LoRALinear)
    }
    _prove(
        before,
        f"sweep {label!r} tried to load an adapter onto a model with no LoRALinear modules — "
        "injection never happened, so `load_adapter_weights` has no keys to audit against and "
        "every completion this sweep produced would come from the bare base model",
    )

    load_adapter_weights(model, artifact)

    after = {
        name: module.lora_B
        for name, module in model.named_modules()
        if isinstance(module, LoRALinear)
    }
    _prove(
        any(not torch.equal(after[name], tensor) for name, tensor in before.items()),
        f"loading sweep {label!r}'s adapter changed NO lora_B tensor (ISO-04). All three personas "
        "share an identical lora_ key set, identical shapes and an identical lora_config, so every "
        "audit in load_adapter_weights passes for the WRONG artifact — a no-op swap is invisible "
        "in the completions and the matrix it produces is fabricated: the resident adapter's "
        "column reads high in every row while the other two read zero",
    )
    zeroed = sorted(name for name, tensor in after.items() if not bool(tensor.any()))
    _prove(
        not zeroed,
        f"sweep {label!r} loaded an adapter whose lora_B is all-zero at {zeroed} — that is the "
        "identity gate (`src/personacore/lora/layer.py:30` initialises lora_B to zeros so a fresh "
        "wrapper is bit-identical to the bare Linear), not an adapter. The delta branch would "
        "contribute exactly nothing and this sweep would be the base model wearing a persona name",
    )
    return lora_b_digest(model)


def assert_sweeps_ran_on_distinct_weights(sweep_records):
    """ISO-04's CROSS-PROCESS layer, and the unskippable half. Runs BEFORE any scoring.

    ``assert_arms_are_pairable``'s register (``phase16_persistence.py:2658``), repriced for this
    phase and extended with the two claims specific to it — ISO-04's weight distinctness and
    ISO-03's control property. Every refusal here is cheaper than a published matrix that should
    never have been assembled.

    * **One ``git_sha``** across all four records — four processes, ONE codebase.
    * **Four DISTINCT pids** — the process split, evidenced rather than asserted.
    * **Identical ``(slot, seed_index, question)`` sets.** The TRIPLE rather than the bare index,
      because every sweep's bare index set is ``0..103`` and would match trivially while the
      questions behind it differed (D-02 keys on the slot, never on ``fact_id``).
    * **ISO-04:** the three adapter sweeps' live ``lora_B`` digests are pairwise distinct AND their
      artifact file digests are pairwise distinct. The two are separate claims and neither implies
      the other.
    * **ISO-03, in its CORRECTED form:** the base record's ``adapter_enabled`` is ``False`` and
      every adapter record's is ``True``; and separately, the base record's live digest differs
      from all three adapter digests.

    **The base record's digest is NOT compared against a zeroed-``lora_B`` digest, and must not
    be.** ``adapter_disabled`` flips a plain Python bool and leaves ``lora_B`` exactly as loaded, so
    against a real run the base sweep's digest is Phase 14's ``persona_adapter.pt`` (see
    ``BASE_COLUMN_NOTE``). That assertion fails on every honest run; ``adapter_enabled`` is the one
    field that can carry the claim, and it is the field this checks.
    """
    records = tuple(sweep_records)
    seen = tuple(record[SWEEP_LABEL_KEY] for record in records)
    _prove(
        sorted(seen) == sorted(SWEEPS),
        f"the report was handed sweeps {sorted(seen)} but the pre-registration commits "
        f"{sorted(SWEEPS)} — a missing sweep cannot be found by comparing the ones that are "
        "present, and a duplicated one would be scored twice under two names",
    )
    by_label = {record[SWEEP_LABEL_KEY]: record for record in records}
    adapters = [by_label[label] for label in personas.PERSONAS]
    base = by_label[personas.BASE_ROW]

    shas = {record["git_sha"] for record in records}
    _prove(
        len(shas) == 1,
        f"the four sweeps recorded {len(shas)} different git SHAs ({sorted(shas)}) — the code "
        "changed mid-run, so the sweeps did not run the same instrument and the cells they "
        "produced are not cells of one matrix",
    )
    pids = {record["pid"] for record in records}
    _prove(
        len(pids) == len(SWEEPS),
        f"the four sweep records carry {len(pids)} distinct pid(s) ({sorted(pids)}) — one "
        "process per sweep is what makes the in-process swap failure impossible in the first "
        "place, and two sweeps sharing a process crossed the exact boundary ISO-04 isolates",
    )

    keyed = {
        record[SWEEP_LABEL_KEY]: {
            (entry["slot"], entry["seed_index"], entry["question"])
            for entry in record[SWEEP_QUESTIONS_KEY]
        }
        for record in records
    }
    reference = keyed[SWEEPS[0]]
    for label in SWEEPS[1:]:
        _prove(
            keyed[label] == reference,
            f"sweep {label!r} generated a different (slot, seed_index, question) set from "
            f"{SWEEPS[0]!r}: {len(keyed[label] ^ reference)} entries differ, e.g. "
            f"{sorted(keyed[label] ^ reference)[:3]}. Cell-to-cell comparability rests entirely "
            "on the four sweeps answering the SAME questions under the SAME seeds — and the bare "
            "index set is 0..n-1 in every sweep, so it matches trivially while the questions "
            "behind it differ",
        )

    live = {record[SWEEP_LABEL_KEY]: record[LORA_B_DIGEST_KEY] for record in adapters}
    _prove(
        len(set(live.values())) == len(adapters),
        f"the three adapter sweeps recorded {len(set(live.values()))} distinct live lora_B "
        f"digest(s) ({live}) — two sweeps ran on the SAME resident weights (ISO-04). Every "
        "off-diagonal in those rows is then fabricated and their diagonal is one number reported "
        "twice under two persona names",
    )
    files = {record[SWEEP_LABEL_KEY]: record[ADAPTER_FILE_DIGEST_KEY] for record in adapters}
    _prove(
        len(set(files.values())) == len(adapters),
        f"the three adapter sweeps read {len(set(files.values()))} distinct artifact file(s) "
        f"({files}) — the same adapter file was named under two persona names (ISO-04). This is a "
        "separate claim from the live digests and neither implies the other: a file digest proves "
        "which file was read, a live digest proves which weights the model ended up holding",
    )

    _prove(
        base[ADAPTER_ENABLED_KEY] is False,
        f"the {personas.BASE_ROW!r} record carries {ADAPTER_ENABLED_KEY} = "
        f"{base[ADAPTER_ENABLED_KEY]!r} (ISO-03). This flag is the ONLY evidence the delta branch "
        "was inert: `enabled` is a plain Python bool outside state_dict(), so no weight digest and "
        "no artifact can witness it. A base column generated with the adapter live is not a "
        "control, it is a fourth adapter row mislabelled as one",
    )
    live_adapter_flags = {
        record[SWEEP_LABEL_KEY]: record[ADAPTER_ENABLED_KEY]
        for record in adapters
        if record[ADAPTER_ENABLED_KEY] is not True
    }
    _prove(
        not live_adapter_flags,
        f"adapter sweep(s) {live_adapter_flags} did not record {ADAPTER_ENABLED_KEY} = True "
        "(ISO-03). An adapter sweep generated with the delta branch gated off is the base model "
        "under a persona's name: its row would read as perfect isolation while measuring nothing",
    )
    collisions = sorted(
        label for label, digest in live.items() if digest == base[LORA_B_DIGEST_KEY]
    )
    _prove(
        not collisions,
        f"the {personas.BASE_ROW!r} sweep's live lora_B digest equals {collisions}'s — the "
        "adapter-off column ran on a Phase 17 adapter's weights, so the control is not a control "
        "(ISO-03). Expected there is Phase 14's persona_adapter.pt, which load_adapted_model loads "
        f"by default: {BASE_COLUMN_NOTE}",
    )


# =============================================================================================
# ===== SC3 — the ONE lazy reader of the minted material, and the mapping the scorer takes =====
# =============================================================================================


def _minted_facts():
    """The persona material, lazily. **The only function in this file that reads it.**

    Two consumers need it and they need different shapes: ``slot_values`` needs a slot's three
    values (scoring), ``run_one_persona_training`` needs a persona's eight ``Fact`` objects
    (teaching). Routing both through one accessor keeps the material's name off every other
    function in this module, which is what makes the scoring path's independence checkable by
    inspection rather than by trust — ``assemble_matrix`` takes ``values_by_slot`` as a PARAMETER
    and nothing in it reaches this function (SC3's structural half, and 17-04's handover contract).

    The import is LAZY for the module docstring's reason: ``scripts/phase17_persona_facts.py``
    holds the 24 minted values at module scope by design, so importing it at THIS module's import
    time would put every persona value into the scored driver's own string surface.
    """
    import phase17_persona_facts

    return phase17_persona_facts.PERSONA_FACTS


def slot_values(slot):
    """``{persona_label: value}`` for ONE slot — the mapping ``score_completion`` scores against.

    Both proofs check D-04 AT THE POINT OF USE rather than trusting the minting filters that ran in
    another process. Three entries, because a slot missing a persona would drop that column's
    contribution for that slot while the denominator still counted all 13 questions; and three
    DISTINCT values, because two personas sharing a value would make every correct answer for one
    of them register as a leak for the other, manufacturing an off-diagonal hit out of the material
    rather than measuring one in the model.
    """
    values = {
        persona: fact.value
        for persona, facts in _minted_facts().items()
        for fact in facts
        if fact.slot == slot
    }
    _prove(
        set(values) == set(personas.PERSONAS),
        f"slot {slot!r} resolves to values for {sorted(values)} but the matrix rows are "
        f"{sorted(personas.PERSONAS)} (D-04). A persona with no value in a slot contributes "
        "nothing to that slot's 13 questions while the cell denominator still counts them, so the "
        "published rate would be computed over fewer slots than it claims",
    )
    _prove(
        len(set(values.values())) == len(values),
        f"slot {slot!r}'s three values are not distinct (D-04) — two personas answering a slot "
        "with the SAME string makes every correct answer for one of them also a hit for the other, "
        "so the off-diagonal counts leakage that never happened and the gate closes on the choice "
        "of material rather than on the model's behaviour",
    )
    return values


def values_by_slot():
    """``{slot: {persona_label: value}}`` over ``CORE_SLOTS`` — ``assemble_matrix``'s parameter.

    This is the seam that keeps the whole scoring core testable on SYNTHETIC values: the material
    is assembled HERE, at the run's edge, and handed in. Nothing inside the scoring path reads it,
    which is why every matrix test in ``tests/test_phase17_scoring.py`` runs on values that
    deliberately disagree with the committed ones (SC3).
    """
    return {slot: slot_values(slot) for slot in personas.CORE_SLOTS}


# =============================================================================================
# ===== The CLI — three modes, and no mode that runs two sweeps (ISO-04 / RESEARCH Pattern 3) ==
# =============================================================================================

SWEEP_RECORD_DIR = _REPO_ROOT / "results"

_USAGE = (
    "usage: python scripts/phase17_isolation.py\n"
    "         (--train {persona_a,persona_b,persona_c}\n"
    "          | --sweep {persona_a,persona_b,persona_c,base}\n"
    "          | --report) [--seed INT]\n"
    "\n"
    "  --train NAME   train EXACTLY ONE persona adapter into checkpoints/phase17_NAME_adapter.pt.\n"
    "  --sweep NAME   generate EXACTLY ONE sweep's completions and write\n"
    "                 results/phase17_sweep_NAME.json. `base` is the ISO-03 adapter-off column.\n"
    "  --report       assemble the isolation matrix from the four sweep records already on disk.\n"
    "  --seed INT     the ISO-05 replication seed. With --train it overrides the pre-registered\n"
    "                 PERSONA_SEEDS entry; with --sweep it selects the seed-scoped artifact and\n"
    "                 record. It must be a member of that persona's REPLICATION_SEEDS, and it is\n"
    "                 REFUSED for `base` (see resolve_seed).\n"
    "\n"
    "There is deliberately NO mode that runs more than one sweep. Four fresh processes, one\n"
    "per sweep, and the only structural way to guarantee that is to make a single process\n"
    "incapable of running two. A convenience flag would turn the process split from a PROPERTY\n"
    "of this driver into a convention an operator is trusted to follow.\n"
    "\n"
    "For Phase 17 the split is stronger than it was for Phase 16: fresh processes make the ISO-04\n"
    "in-process swap failure impossible IN THE FIRST PLACE, because no process ever holds two\n"
    "adapters. The canary then only has to prove the cross-process claim, which is the harder\n"
    "and more valuable half. `--train` is admitted as a third action only because it generates\n"
    "nothing and scores nothing; the group still makes one process incapable of running two."
)


def sweep_record_path(sweep, seed=None):
    """Where ONE sweep's raw completions land. Read from the module global so tests can redirect."""
    _prove(
        sweep in SWEEPS,
        f"sweep {sweep!r} is not one of the pre-registered {SWEEPS} — a record filed under an "
        "unrecognized name would be scored as whichever row the report happened to reach",
    )
    stem = f"phase17_sweep_{sweep}" if seed is None else f"phase17_sweep_{sweep}_seed{seed}"
    return SWEEP_RECORD_DIR / f"{stem}.json"


def resolve_seed(mode, target, seed):
    """Validate ``--seed`` against the pre-registration and return this run's names and paths.

    Returns ``{"seed", "arm", "adapter", "record"}``. ``arm`` is the persona for a default-seed run
    and ``{persona}_seed{seed}`` for an ISO-05 replicate, so ``refuse_if_exists`` protects each run
    independently and no two runs ever share a write target. ``adapter`` is resolved through
    ``teach_persona.arm_outputs(arm, prefix="phase17")`` — the SAME function ``train_arm`` uses to
    choose its own write targets, so the path the sweep loads and the path the training wrote
    cannot drift apart.

    An explicit ``--seed`` equal to that persona's ``PERSONA_SEEDS`` entry resolves to the SAME arm
    and the SAME unscoped record as no ``--seed`` at all: the default run has exactly one canonical
    set of paths, whether or not the operator spelled its seed out.

    ``--sweep base`` with any ``--seed`` is REFUSED, for two independent reasons stated together in
    the message. The base column has no persona and therefore no ``REPLICATION_SEEDS`` entry, so
    there is nothing to validate the value against; and the replication reuses the single base sweep
    by design (D-13 derives the base prior from ONE adapter-off column under one set of questions
    and seeds, so a per-seed base column would be four controls where the design has one).
    """
    import teach_persona

    _prove(
        mode in ("train", "sweep"),
        f"resolve_seed was called for mode {mode!r}; it resolves seeds for 'train' and 'sweep' "
        "only, and --report reads whatever records are on disk rather than choosing a seed",
    )
    if target == personas.BASE_ROW:
        _prove(
            mode == "sweep" and seed is None,
            f"--seed {seed!r} was given for the adapter-off row {personas.BASE_ROW!r}, and it is "
            "refused for two independent reasons. (1) The base column has no persona, so it has no "
            "REPLICATION_SEEDS entry and there is nothing to validate the value against — any "
            "integer would be accepted, which is not validation. (2) ISO-05's replication reuses "
            "the SINGLE base sweep by design: D-13 derives the base prior from one adapter-off "
            "column under one set of questions and seeds, so a per-seed base column would be four "
            "controls where the design has exactly one",
        )
        return {"seed": None, "arm": None, "adapter": None, "record": sweep_record_path(target)}

    _prove(
        target in personas.PERSONAS,
        f"{target!r} is not one of the pre-registered personas {personas.PERSONAS}",
    )
    default = personas.PERSONA_SEEDS[target]
    if seed is None:
        seed = default
    _prove(
        seed in personas.REPLICATION_SEEDS[target],
        f"--seed {seed} is not one of {target!r}'s pre-registered "
        f"{personas.REPLICATION_SEEDS[target]} (ISO-05, committed in Wave 1 before the matrix "
        "existed). An arbitrary seed on the command line is a training run outside the "
        "pre-registration, and its adapter would enter the replication as if it had been declared",
    )
    replicate = seed != default
    arm = f"{target}_seed{seed}" if replicate else target
    return {
        "seed": seed,
        "arm": arm,
        "adapter": teach_persona.arm_outputs(arm, prefix="phase17")["adapter"],
        "record": sweep_record_path(target, seed=seed if replicate else None),
    }


def build_parser():
    """The argument surface as a spec a test can read: three modes, no fourth, and no pair.

    ``--train`` and ``--sweep`` are constrained by argparse itself to ``PERSONAS`` and ``SWEEPS``,
    so an unrecognized name exits non-zero with the legal names printed rather than reaching a
    dispatch that would have to invent a refusal. Exactly one of the three is REQUIRED: an
    argumentless invocation must not fall through to "run something reasonable" when the reasonable
    thing is a multi-hour generation run. ``--seed`` sits OUTSIDE the group because it modifies the
    chosen mode rather than being one.
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="phase17_isolation.py",
        description=(
            "Phase 17 multi-persona isolation matrix — ONE persona trained, or ONE sweep "
            "generated, per process."
        ),
        epilog=_USAGE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--train",
        choices=personas.PERSONAS,
        help="train the single persona adapter this process is responsible for",
    )
    mode.add_argument(
        "--sweep",
        choices=SWEEPS,
        help="generate the single sweep this process is responsible for",
    )
    mode.add_argument(
        "--report",
        action="store_true",
        help="assemble the matrix from the four sweep records on disk",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="the ISO-05 replication seed (must be pre-registered; refused for the base row)",
    )
    return parser


# =============================================================================================
# ===== The two run bodies — ONE sweep, or ONE persona trained, per process ====================
# =============================================================================================

# ISO-01's blocking human verdict. `teach_persona.train_arm` gates on PHASE 14's report from the
# inside and that call is deliberately untouched, so calling `_require_go_verdict` with THIS report
# here makes BOTH gates fire: Phase 14's fact set was cleared, and Phase 17's own material was.
PHASE17_REPORT = _REPO_ROOT / "results" / "phase17_personas_report.md"


def run_one_sweep(sweep, seed=None):
    """ONE sweep, in this process, start to finish — and this process can run no other.

    The order is not incidental:

    1. **Refuse to clobber the record FIRST**, before anything expensive. A recorded sweep is
       evidence; discovering the collision after ~5 minutes of generation has already wasted the run
       whether or not the file survives.
    2. Preflight, device, ``seed_everything(recall.SEED)`` — ONE seed constant in play, the
       instrument's own. **The generation seed is ``question_seed(index)`` and is IDENTICAL across
       all four sweeps.** D-14's distinct seeds are TRAINING/INIT seeds; varying the generation seed
       per sweep would destroy cell-to-cell comparability, and it is exactly what ISO-03 forbids of
       the adapter-off column.
    3. Load, and record two digests plus one flag either way — see ``BASE_COLUMN_NOTE`` for why the
       flag cannot be derived from the digests.
    4. ONE ``forbid_ids`` mask, recorded by content hash. Never a second mask.
    5. Generate, extending the clean-room proof to Phase 17's OWN material.
    6. Write the raw completions. **No ``value``, no ``k``, no ``n``, no ``hits``** — those are
       per-persona and belong to the scoring pass. Writing them here would put the cell into the
       generation record, which is the one thing this two-pass design exists to prevent (SC3).

    The report is NOT written here. It is assembled from all four records by ``--report``, which is
    what makes the four-process split a precondition of publishing rather than a claim made inside
    one process.
    """
    import contextlib
    import json
    import os
    import time

    import phase14_recall as recall  # LAZY — see the module docstring's LAZY-IMPORT RULE
    import torch

    from personacore.checkpoint import load_adapter
    from personacore.config import RuntimeConfig
    from personacore.lora import LoRALinear, adapter_disabled
    from personacore.preflight import preflight_device
    from personacore.provenance import git_sha
    from personacore.seeding import seed_everything

    started = time.time()
    resolved = resolve_seed("sweep", sweep, seed)
    record_path = resolved["record"]
    _prove(
        not record_path.exists(),
        f"{record_path} already exists — a sweep record is RECORDED EVIDENCE, and a rerun on "
        "drifted code, a drifted adapter or a drifted fixture would silently replace the "
        "completions every cell in this row was scored from. Delete it in a reviewed commit if it "
        "genuinely must be regenerated",
    )

    summary = preflight_device(strict=True)
    print(f"[phase17_isolation] preflight: {summary}")
    device = RuntimeConfig().device
    seed_everything(recall.SEED)

    # The base sweep loads the SAME way the adapter sweeps do — Phase 14's persona_adapter.pt, which
    # `load_adapted_model` reads by default — and then generates inside `adapter_disabled`. Never a
    # second un-adapted model: the context manager is measured bit-identical to the un-adapted base
    # (max abs diff exactly 0.0) and a separately-built model would be a second load path free to
    # differ from the one the three adapter rows ran through.
    model, model_cfg, tok, forbid, base_artifact = recall.load_adapted_model(device)
    _prove(
        model_cfg.block_size == persistence.SHARED_ARM_CONFIG.context_length,
        f"the loaded checkpoint's block_size is {model_cfg.block_size} but the parity column is "
        f"{persistence.SHARED_ARM_CONFIG.context_length} — the published context_length would "
        "describe a model none of these completions was produced by",
    )
    _, seam_digest = persistence.resolve_forbid(tok, model_cfg.vocab_size)
    _prove(
        persistence.forbid_digest(forbid) == seam_digest,
        "the mask the loader threaded into this sweep does not match `resolve_forbid`'s — the "
        "forbid_ids hash this record publishes would describe a mask the sweep never generated "
        "under, and ISO-03's 'identical forbid_ids across all four sweeps' would be unverifiable",
    )

    if sweep == personas.BASE_ROW:
        adapter_enabled = False
        adapter_file_sha256 = recall._sha256(recall.ADAPTER_PATH)
        generation_context = adapter_disabled(model)
    else:
        adapter_enabled = True
        artifact_path = resolved["adapter"]
        _prove(
            artifact_path.exists(),
            f"{artifact_path} is missing — sweep {sweep!r} has no trained adapter. Run "
            f"`python scripts/phase17_isolation.py --train {sweep}` in its own process first",
        )
        # weights_only=True through the single choke point; `torch.load` is never called directly
        # on a shareable artifact anywhere in this path.
        artifact = load_adapter(
            artifact_path, expected_fingerprint=base_artifact["loaded_base_fingerprint"]
        )
        lora_b_sha256 = load_adapter_with_canary(model, artifact, label=sweep)
        adapter_file_sha256 = recall._sha256(artifact_path)
        generation_context = contextlib.nullcontext()

    by_slot = held_out_by_slot()
    # The clean-room proof, extended to THIS phase's material: the binding fixture's own guard #4
    # checks only Phase 14's 10 values, so nothing upstream has ever proved that a Phase 17 value is
    # absent from these 104 questions at generation time.
    minted = sorted({value for row in values_by_slot().values() for value in row.values()})

    entries = []
    with generation_context:
        if sweep == personas.BASE_ROW:
            gated_on = sorted(
                name
                for name, module in model.named_modules()
                if isinstance(module, LoRALinear) and module.enabled
            )
            _prove(
                not gated_on,
                f"the adapter-off sweep entered generation with {gated_on} still enabled "
                "(ISO-03). This runtime check is the ONLY witness that the delta branch was "
                "inert: `enabled` is a plain Python bool kept out of state_dict(), so no weight "
                "digest and no artifact can see it, and the recorded adapter_enabled flag is only "
                "as true as this assertion makes it",
            )
            lora_b_sha256 = lora_b_digest(model)

        for slot in personas.CORE_SLOTS:
            for item in by_slot[slot]:
                recall.assert_no_value_in_prompt(tok, item.question, minted)
                # `complete_question` builds the prompt itself, in the BARE two-positional form,
                # and returns `prompt_ids` — so this driver never builds one. `index` is the
                # fixture's OWN seed_index, read verbatim, which is what pairs the four sweeps.
                drawn = recall.complete_question(
                    model, tok, item.question, device, forbid, index=item.seed_index
                )
                _prove(
                    len(drawn["completions"]) == persistence.SHARED_ARM_CONFIG.n_draws,
                    f"question {item.seed_index} drew {len(drawn['completions'])} completions but "
                    f"the shared arm config commits {persistence.SHARED_ARM_CONFIG.n_draws} — the "
                    "draw budget is read off the ONE parity object precisely so a sweep cannot "
                    "generate under a different one and publish its rate as comparable",
                )
                entries.append(
                    {
                        "slot": slot,
                        "seed_index": item.seed_index,
                        "question": item.question,
                        "fact_id": item.fact.id,
                        "prompt_ids": drawn["prompt_ids"],
                        "completions": drawn["completions"],
                        "stopped": drawn["stopped"],
                    }
                )

    wall = time.time() - started
    payload = {
        SWEEP_LABEL_KEY: sweep,
        "seed": resolved["seed"],
        "git_sha": git_sha(),
        "pid": os.getpid(),
        "device": str(device),
        "torch": torch.__version__,
        "wall_clock_min": wall / 60,
        LORA_B_DIGEST_KEY: lora_b_sha256,
        ADAPTER_FILE_DIGEST_KEY: adapter_file_sha256,
        ADAPTER_ENABLED_KEY: adapter_enabled,
        # The four parity columns PLUS `forbid_ids_sha256`, read off the ONE shared object through
        # the committed Phase 16 seam. The forbid hash lives HERE and nowhere else in this payload:
        # two copies of one hash in one file is two places it can stop agreeing about the same mask.
        "config": persistence.serializable_config(persistence.arm_config_record(forbid)),
        "forbid_ids_masked": int(forbid.sum().item()),
        "vocab_size": model_cfg.vocab_size,
        "base_column_note": BASE_COLUMN_NOTE,
        SWEEP_QUESTIONS_KEY: entries,
    }
    record_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"[phase17_isolation] wrote {record_path} in {wall / 60:.1f} min")
    return payload


def run_one_persona_training(persona, seed=None):
    """Train ONE persona adapter through the COMMITTED recipe — never a Phase 17 copy of it.

    Committed here, with the sweep body, rather than in the run plan: the whole pipeline is in git
    history before it produces a number (Phase 16's 16-06 register). This function contributes a
    gate, a seed and a name — the recipe itself is ``teach_persona``'s, imported unchanged, because
    a copied recipe is a second recipe free to drift from the one every published number came from.

    ``prefix="phase17"`` is passed AT THE CALL, which is what makes ``teach_persona.arm_outputs``
    resolve to ``checkpoints/phase17_{arm}_adapter.pt`` at BOTH of the call sites inside
    ``train_arm`` — the one that guards with ``refuse_if_exists`` and the one reached through
    ``build_arm_bins``, which rebinds the paths the export half writes to. Without it the run
    produces a Phase-17 adapter under a Phase-14 name.

    ``arm_outputs`` is deliberately NOT called here to "choose" a path. ``train_arm`` owns its own
    write targets, and a second opinion about them is exactly how the two drift; the path printed
    below is resolved through ``resolve_seed``, which reads that same function.
    """
    import phase14_factset as fs  # LAZY — see the module docstring's LAZY-IMPORT RULE
    import teach_persona

    verdict = teach_persona._require_go_verdict(PHASE17_REPORT)
    print(f"[phase17_isolation] ISO-01 verdict in {PHASE17_REPORT.name}: {verdict}")

    resolved = resolve_seed("train", persona, seed)
    print(
        f"[phase17_isolation] training arm {resolved['arm']!r} at seed {resolved['seed']} "
        f"-> {resolved['adapter']}"
    )
    return teach_persona.train_arm(
        resolved["arm"],
        facts=_minted_facts()[persona],
        family_ids=fs.TAUGHT_FAMILY_IDS,
        seed=resolved["seed"],
        prefix="phase17",
    )


# =============================================================================================
# ===== STAT-01..06 — the report mode: the proof FIRST, then scoring, then the imported gate ===
# =============================================================================================

ISOLATION_REPORT_PATH = _REPO_ROOT / "results" / "phase17_isolation_report.md"

# The pre-registration file, cited by the report so a reader can check the ordering claim rather
# than take it. Resolved through the SAME path the ancestry guard in `tests/test_phase16_prereg.py`
# pins, never a second spelling of it.
PREREG_PATH = _REPO_ROOT / "scripts" / "phase17_personas.py"


def assert_isolation_report_not_clobbered():
    """A RECORDED verdict is committed evidence. Refuse to overwrite it — FIRST, and cheapest.

    ``phase16_persistence.assert_persistence_report_not_clobbered``'s register, repriced for this
    phase. Called before a single sweep record is READ, let alone scored: a report run that refuses
    at the end has already spent its reader's attention, and here the refusal costs nothing.

    **Anchored on the SECTION via ``_verdict.recorded_verdict``, never on a split of the heading
    literal** — the 15-04 CR-02 defect, whose one shared copy this imports. ``None`` (no verdict
    section at all) and a body without ``PENDING`` are both refusals: a file this writer did not
    produce must not be blindly overwritten either. There is no force flag.
    """
    if not ISOLATION_REPORT_PATH.exists():
        return
    recorded = _verdict.recorded_verdict(ISOLATION_REPORT_PATH.read_text(encoding="utf-8"))
    if recorded is None or "PENDING" not in recorded:
        raise SystemExit(
            f"[phase17_isolation] {ISOLATION_REPORT_PATH} already carries a recorded verdict — it "
            "is this phase's committed isolation evidence, assembled from four GPU sweeps that "
            "cannot be re-derived without breaking the pre-registration's ordering guarantee. "
            "There is no force flag: if it genuinely must be regenerated, delete it in a reviewed "
            "commit so the removal is visible in the diff."
        )


def read_sweep_records():
    """The four UNSCOPED sweep records, read by NAME rather than found by a glob.

    Each record is read from ``sweep_record_path(sweep)`` with no ``seed``, so plan 17-11's
    seed-scoped replicate records (``phase17_sweep_persona_a_seed1437.json``) are structurally
    unreachable from here rather than filtered out afterwards — a glob would sweep them up the
    moment ISO-05 runs, and a replicate scored into the matrix is a seventh and eighth row of a
    matrix closed at four.

    Reading by name gives exactly ``len(SWEEPS)`` records by construction; what is NOT free is that
    each file holds the row it was FILED as, so that is proved.
    """
    import json

    records = []
    for sweep in SWEEPS:
        path = sweep_record_path(sweep)
        _prove(
            path.exists(),
            f"{path} is missing — the matrix assembles from all {len(SWEEPS)} sweep records or "
            f"from none. Run `python scripts/phase17_isolation.py --sweep {sweep}` in its own "
            "fresh process first",
        )
        record = json.loads(path.read_text(encoding="utf-8"))
        _prove(
            record.get(SWEEP_LABEL_KEY) == sweep,
            f"{path} carries {SWEEP_LABEL_KEY} = {record.get(SWEEP_LABEL_KEY)!r} — a record filed "
            f"under {sweep!r} but labelled otherwise would be published as the row it was filed "
            "as, which is a whole row of the matrix attributed to the wrong adapter",
        )
        records.append(record)
    seen = {record[SWEEP_LABEL_KEY] for record in records}
    _prove(
        seen == set(SWEEPS),
        f"the records on disk name {sorted(seen)} but the pre-registration commits "
        f"{sorted(SWEEPS)} — the base row is not optional (ISO-03)",
    )
    return records


def draws_per_question(sweep_records):
    """The ONE draw budget every recorded question carries — the report's RAW-COUNT denominator.

    ``report_proportion``'s third argument is the raw-count denominator and renders as
    ``"{n} draws"`` beside a question-unit numerator. Handing it the PER-QUESTION budget would
    publish ``0/104 questions (... ; 9 draws)`` — understating the raw count by two orders of
    magnitude, on the one axis T-16-40 records as the repudiation surface. So the budget is read
    off the records here and multiplied by each cell's own question count in ``describe_matrix``.

    Proved single-valued across all four sweeps AND equal to what each record's own ``config``
    published. The second half is the stronger claim: a record whose completions disagree with the
    parity block it publishes describes a generation budget none of its completions came from.
    """
    counts = {
        len(entry["completions"])
        for record in sweep_records
        for entry in record[SWEEP_QUESTIONS_KEY]
    }
    _prove(
        len(counts) == 1,
        f"the recorded questions carry {sorted(counts)} completions — the four sweeps must share "
        "ONE draw budget or their cells are not cells of one matrix, and the raw-count denominator "
        "this report publishes would describe some questions and not others",
    )
    n_draws = counts.pop()
    for record in sweep_records:
        published = record.get("config", {}).get("n_draws")
        _prove(
            published == n_draws,
            f"sweep {record[SWEEP_LABEL_KEY]!r} recorded {n_draws} completions per question but "
            f"its own config publishes n_draws = {published!r} — the parity column and the "
            "completions behind it disagree, so the published budget describes a run that did not "
            "happen",
        )
    return n_draws


def cell_rates(matrix):
    """``{cell: {slot: {"rate": ...}}}`` over the NINE ADAPTER cells — ``fact_signs``'s input.

    ``fact_signs(per_fact_by_arm, pair)`` reads ``["rate"]`` off whatever dict it is handed; here
    the "arms" are cell tuples and the "facts" are slot strings (verified during research). The
    rate is ``sum(k) / sum(n)`` over that slot's ``(k, n)`` pairs, and ``assemble_matrix`` builds
    those pairs in the QUESTION unit with ``n == 1`` — so this is STAT-01's unit by construction and
    the DRAW rate is not even representable from the cell's ``per_slot`` field.

    **The three base cells are dropped HERE, deliberately, and the drop is the point.** They are
    computed, published in §The Matrix and read by D-10's all-fail branch — but the committed
    family is derived over ``PERSONAS`` only, and a base cell entering it would make a seventh
    comparison: at m = 7 Holm's first alpha is 0.0071429, below the achievable p of 0.0078125, so
    the headline would die arithmetically at every possible outcome including perfect unanimity.
    ``compare_cells`` re-proves the absence rather than trusting this filter.
    """
    return {
        cell: {
            slot: {"rate": sum(k for k, _n in pairs) / sum(n for _k, n in pairs)}
            for slot, pairs in entry["per_slot"].items()
        }
        for cell, entry in matrix.items()
        if cell[0] in personas.PERSONAS
    }


def compare_cells(per_cell):
    """THE FORMAL VERDICT — Holm-corrected across exactly the six ``HOLM_FAMILY_CELLS``.

    ``compare_arms``'s register (``phase16_persistence.py:1205``), repriced for this phase. **This
    is the ONE function in this module permitted to call ``holm`` or ``sign_test_exact``**, and
    ``tests/test_phase17_stats.py``'s D-21 twin asserts exactly that across all four Phase 17
    drivers — Phase 16's own scan is file-scoped to Phase 16's two, so the discipline does not
    transfer by inheritance and had to be re-established here.

    Nothing statistical is written: every function is IMPORTED and STAT-04 is satisfied literally by
    import. The expensive part of ``sign_test_exact`` is not its arithmetic — it is the four
    committed decisions it carries, each a recorded defect fix, and re-deriving the arithmetic loses
    the decisions.

    Both halves of the family closure run, because either alone leaves the other open:
    ``assert_phase17_family_closed`` catches a dynamically-built cell list, the static AST scan
    catches a new call site, and ``assert_family_length_matches_phase16`` catches F-08's coincidence
    — ``holm`` prices alpha off PHASE 16's ``HOLM_FAMILY_PAIRS``, and the two families agreeing at 6
    is ``C(4,2) == 3x2``, not a shared design.
    """
    _prove(
        personas.SIGN_UNIT == "question",
        f"SIGN_UNIT is pre-registered as {personas.SIGN_UNIT!r} but the gate is assembled on "
        "n_answerable / n_questions, the QUESTION rate (STAT-01 / RESEARCH F-11). fact_signs signs "
        "on whatever ['rate'] holds, so a declared unit that no longer matches the computed one "
        "puts the whole gate on a quantity nobody registered — and the two units differ by more "
        "than a factor of two on the real gated tier",
    )
    intruders = sorted(cell for cell in per_cell if personas.BASE_ROW in cell)
    _prove(
        not intruders,
        f"{intruders} reached the gate, but the adapter-off row {personas.BASE_ROW!r} is a "
        "PUBLISHED CONTROL and never a gated comparison (ISO-03). Gating it would make a seventh "
        "comparison, and at m = 7 Holm's first alpha is 0.0071429 — below the achievable p of "
        "0.0078125 — so the headline would die arithmetically at every possible outcome",
    )
    signs = {pair: persistence.fact_signs(per_cell, pair) for pair in personas.HOLM_FAMILY_CELLS}
    p_values = {pair: persistence.sign_test_exact(pair_signs) for pair, pair_signs in signs.items()}
    personas.assert_phase17_family_closed(tuple(p_values))
    personas.assert_family_length_matches_phase16(len(persistence.HOLM_FAMILY_PAIRS))
    rows = persistence.holm(p_values)
    return {
        "alternative": dict(personas.CELL_ALTERNATIVE),
        "signs": signs,
        "p_values": p_values,
        "holm": rows,
        "cleared": personas.gate_cleared(rows),
    }


def describe_matrix(matrix, n_draws_per_question, *, resamples=persistence.BOOTSTRAP_RESAMPLES):
    """The DESCRIPTIVE block for all 12 cells, base row included. Never a gate (STAT-06).

    Per cell: the phase's own width (``cluster_bootstrap`` over ``per_slot``, with the SLOT as the
    cluster — key-agnostic, so no Phase 16 function is widened), ``report_proportion``'s STAT-02
    shape (Wilson upper, the rule of three at zero, and both denominators), and the two ends of the
    clustering assumption.

    **Both rule-of-three ends are published at every cell, not only at zero.** Phase 17's zeros are
    the headline, so the ceiling a zero admits is the number a reader will quote: the question-level
    ``3/n_questions`` treats the questions as independent (they are not — 13 cluster inside each
    slot) and is the OPTIMISTIC end, while the slot-level ``3/SLOTS_EXPECTED`` treats each slot as
    one observation and is the CONSERVATIVE end. Publishing one alone is publishing the end that
    flatters the claim; the cluster bootstrap is the estimate of where between them the truth sits.

    ``resamples`` defaults to the PRE-REGISTERED ``BOOTSTRAP_RESAMPLES``, read from the committed
    constant and never retyped. It is a parameter only so a CPU-only test can exercise the whole
    assembly without paying 10,000 resamples twelve times; ``run_report_mode`` never passes it and
    the count actually used is PRINTED in the report, so a lowered one is visible in the artifact
    rather than hidden in a call.
    """
    described = {}
    for cell, entry in matrix.items():
        described[cell] = {
            "proportion": persistence.report_proportion(
                entry["n_answerable"],
                entry["n_questions"],
                entry["n_questions"] * n_draws_per_question,
            ),
            "bootstrap": persistence.cluster_bootstrap(entry["per_slot"], resamples=resamples),
            "rule_of_three_questions": persistence.rule_of_three(entry["n_questions"]),
            "rule_of_three_slots": persistence.rule_of_three(personas.SLOTS_EXPECTED),
        }
    return described


def base_prior_anchor(base_texts):
    """D-13's sanity anchor: did the adapter-off column reproduce the two priors it was seeded on?

    ``phase14_factset.BASE_PRIOR_SEEDS`` covers **2 of the 8 core slots** and is a SCREENING SEED
    LIST for candidate values, never an enumeration of what the base may say — so this can only ever
    be an anchor, and matching against it could not be a complete test even on the two slots it does
    cover. It is reported and never asserted on: a miss is a **sweep problem to investigate before
    trusting the derivation on the other six slots**, not a finding, and not something to suppress.

    Returns ``{slot: {"seeds": (...), "reproduced": bool}}`` over the covered core slots only.
    """
    import phase14_factset as fs  # LAZY — see the module docstring's LAZY-IMPORT RULE
    from phase14_recall import contains_value  # LAZY — same rule

    return {
        slot: {
            "seeds": seeds,
            "reproduced": any(
                contains_value(text, seed)
                for text in base_texts.get(slot, frozenset())
                for seed in seeds
            ),
        }
        for slot, seeds in sorted(fs.BASE_PRIOR_SEEDS.items())
        if slot in personas.CORE_SLOTS
    }


# =============================================================================================
# ===== The report writer — committed BEFORE it produces a number (D-10 / D-11 / D-15 / D-18) ==
# =============================================================================================
#
# Every framing string below is a module-level constant committed before the four sweeps run: a
# report whose text is written AFTER the numbers is a report written to fit them. The D-20 register
# Phase 14 established and 16-07 followed.

BASE_COLUMN_PURPOSE = (
    "Each base cell `(base, j)` is the rate at which the UN-ADAPTED model produced persona *j*'s "
    "value, over the same questions, the same `seed_index` per question, the same `forbid_ids` "
    "mask and the same `stop_ids` as the three adapter rows. **This is what it is FOR:** it "
    'is the quantitative separator of *"adapter i leaked persona j\'s value"* from *"the base was '
    'going to say something like that anyway"*, and every off-diagonal in column *j* is read '
    "against it. Without it an off-diagonal number has no reading at all."
)

CLUSTERING_ENDS_LABEL = (
    "**Both ends of the clustering assumption are published at every cell.** This phase's headline "
    "is a set of zeros, so the ceiling a zero admits is the number a reader will quote — and one "
    "end alone is the end that flatters the claim. The QUESTION-level rule-of-three bound treats "
    "the questions as independent (they are not: 13 questions cluster inside each slot) and is the "
    "OPTIMISTIC end. The SLOT-level bound treats each slot as a single observation and is the "
    "CONSERVATIVE end. The two-stage cluster bootstrap beside each cell is the estimate of where "
    "between the two ends the truth actually sits."
)

CATEGORY_ROW_PROPERTY_NOTE = (
    "**These four counts are a ROW property and are printed once per row, not once per cell.** "
    "`classify` takes no column index by design (D-12), so the counts partition that row's "
    "questions by what the row's OWN completions contained — they are identical across a row's "
    "three cells. The PER-COLUMN number is the answerable count in §The Matrix. A reader who takes "
    "a row's `leak` count as *\"how often persona j's value appeared under adapter i\"* has read "
    "the wrong field."
)

BASE_PRIOR_DERIVATION_NOTE = (
    "`base_prior` is DERIVED post-hoc by coincidence against the adapter-off column (D-13), never "
    "scored: it is the set of completions that carried no persona's value and coincided with what "
    "the un-adapted model produced for the same slot. The base row's own `leak` and `diagonal` "
    "counts are zero BY CONSTRUCTION (`own=None` makes `classify`'s branch 1 unreachable and its "
    "branch 2 catch every non-empty label set before branch 3), so a non-zero one there is a bug "
    "`classify` — not a finding."
)

BASE_PRIOR_SEED_ANCHOR_NOTE = (
    "The seed list below is a SANITY ANCHOR on the 2 of 8 core slots it covers, and a SCREENING "
    "seed list for candidate values — never an enumeration of what the base may say, so a match "
    "against it could not be a complete test even on those two slots. If the adapter-off column "
    "does NOT reproduce them, that is a **sweep problem to investigate before trusting the "
    "derivation on the other six slots**, and it is printed here rather than suppressed. It is not "
    "a finding either way."
)

GATE_PUBLISHING_NOTE = (
    "All six Holm rows are published here regardless of outcome, so a partial result stays "
    "readable. **Publishing the rows is not the same as clearing the gate** (D-18): the verdict "
    "below is `gate_cleared`'s own return value over exactly these rows, and it is True only when "
    "all six reject."
)

D11_MILESTONE_PATTERN = (
    "**D-11 — this is Phase 17's instance of a milestone pattern, not a local device.** Separating "
    "*instrument-blind* from *phenomenon-absent* recurs across v3.0 and is recorded in "
    "`17-CONTEXT.md` as a pattern to note wherever it does: Phase 16's D-30 made *\"the arm could "
    'not detect it"* separable from *"the arm found nothing"*, the branch above does the same '
    "for this matrix, and Phase 18's SC4 will do it again with teacher-forced NLL making *\"the "
    'attack was weak"* separable from *"the fact is genuinely absent"*. This report is where a '
    "reader can see the pattern rather than be told about it."
)

# The cross-phase anchors D-10's fork needs to be DECIDABLE — every one labelled with its unit,
# because Phase 14's number and Phase 16's number are not in the same unit and conflating them is
# exactly how "not judgeable" would be argued either way.
COMPARISON_ANCHORS = (
    "**Anchors for reading the diagonal, each labelled with its unit.** Phase 16's `adapter-only` "
    "arm scored **0.865385** on the same 104-question `core_held_out` tier in the QUESTION unit, "
    "with a two-stage cluster bootstrap 95% of (0.721154, 0.971154) and a Wilson upper bound of "
    "0.911252; its `base-neither` arm scored **0/104** there, Wilson upper 0.025355, rule of three "
    "0.028846. Phase 14's **0.3483** is the DRAW-unit rate over the same run and is NOT comparable "
    "to the question-unit numbers in this report — the two differ by more than a factor of two on "
    "this tier. The three Phase 17 adapters trained at `LoRAConfig()` defaults precisely so these "
    "anchors stay readable (D-20)."
)

REPLICATION_DESCRIPTIVE_NOTE = (
    "**Descriptive only.** ISO-05's k=3 seed replication is min / max / median and NEVER a "
    "hypothesis test (D-16): `gate_cleared` is closed at the six pre-registered comparisons and "
    "structurally cannot admit a replication row. The pair below is `worst_pair`'s output — a "
    "function committed in Wave 1, before the matrix was read — over the six ordered off-diagonal "
    "rates shown with it. Its tie-break is load-bearing rather than decoration: the hoped-for "
    "outcome of this phase is that every off-diagonal is zero, which makes the selection a "
    "three-way tie exactly in the success case."
)

# ONE greppable line, and the ONLY place in this module that carries this phrase. Plan 17-10 Task 3
# replaces exactly this line and asserts everything else above the addendum is byte-identical, so a
# second occurrence anywhere would make that replacement ambiguous.
REPLICATION_PENDING_LINE = "**ISO-05 replication result: not yet measured.**"


def _matrix_cell_text(entry):
    """One cell as ONE string: the STAT-02 shape, then this phase's own width, then both ends.

    Rendered through ``report_proportion``'s ``formatted`` so no cell can print a bare percentage —
    a zero rate without its denominator and its ceiling states a certainty the sample does not have.
    """
    proportion = entry["proportion"]
    return (
        f"{proportion['formatted']}; cluster bootstrap 95% "
        f"({entry['bootstrap'][0]:.6f}, {entry['bootstrap'][1]:.6f}); rule of three "
        f"3/{proportion['n_questions']} = {entry['rule_of_three_questions']:.6f} (question-level) "
        f"/ 3/{personas.SLOTS_EXPECTED} = {entry['rule_of_three_slots']:.6f} (slot-level)"
    )


_NOT_RECORDED = "(not recorded)"


def _provenance_row(record):
    """One sweep's provenance line — load-bearing fields indexed, cosmetic ones with a SENTINEL.

    ``git_sha``, ``pid``, both digests and ``adapter_enabled`` are indexed directly because
    ``assert_sweeps_ran_on_distinct_weights`` has already refused any record missing them. The rest
    is read with a VISIBLE ``(not recorded)`` rather than a silent blank: a record without a device
    or a wall clock was not written by ``run_one_sweep``, and publishing the hole is honest.
    """
    wall = record.get("wall_clock_min")
    clock = f"{wall:.1f}" if isinstance(wall, (int, float)) else _NOT_RECORDED
    forbid = str(record.get("config", {}).get("forbid_ids_sha256", _NOT_RECORDED))
    return (
        f"| `{record[SWEEP_LABEL_KEY]}` | `{record['git_sha']}` | {record['pid']} | "
        f"`{record.get('device', _NOT_RECORDED)}` | {clock} | "
        f"`{record[LORA_B_DIGEST_KEY][:16]}…` | `{record[ADAPTER_FILE_DIGEST_KEY][:16]}…` | "
        f"{record[ADAPTER_ENABLED_KEY]} | `{forbid[:16]}…` |"
    )


def render_report(matrix, described, gate, sweep_records, prior_anchor, *, resamples):
    """Write ``results/phase17_isolation_report.md`` and return its text.

    The verdict is COMPUTED by importing ``gate_cleared``, never retyped as prose beside the rows —
    a hand-written headline is a headline free to disagree with the instrument that produced it.
    All six Holm rows are published whatever the outcome, and when the gate does not clear the
    pre-registered ``ALL_FAIL_BRANCH`` is emitted IN FULL together with both of the things it
    requires: (a) the three diagonal magnitudes with their bootstrap intervals, and (b) the
    adapter-off column read off this same matrix rather than restated.

    Two `_prove`s run over the RENDERED TEXT before it is written, because the source-level scans
    cannot see a number a format string produced: the report must carry a ``## Verdict`` section the
    clobber guard can anchor on, and it must contain no bare zero percentage anywhere (STAT-02).
    """
    import re

    rows = personas.PERSONAS + (personas.BASE_ROW,)
    family = len(persistence.HOLM_FAMILY_PAIRS)
    step_alphas = [persistence.HOLM_ALPHA / (family - index) for index in range(family)]
    unanimity = persistence.sign_test_exact((1,) * persistence.SIGN_TEST_N)
    one_tie = persistence.sign_test_exact((1,) * (persistence.SIGN_TEST_N - 1) + (0,))
    cleared = personas.gate_cleared(gate["holm"])

    blocks = [
        "# Phase 17 — Multi-Persona Isolation Matrix "
        "(ISO-02 / ISO-03 / ISO-05 / STAT-01 / STAT-02 / STAT-03 / STAT-06)",
        "",
        "## Pre-Registration",
        "",
        f"The family, the direction of every alternative, the seeds and the gate rule were "
        f"committed in `scripts/phase17_personas.py` at `{prereg_commit()}` — before a persona "
        "value was minted, before an adapter trained and before any `results/phase17_*` artifact "
        "existed. `tests/test_phase16_prereg.py` asserts by git ANCESTRY that every commit "
        "touching that file precedes every Phase 17 result's first add, so the ordering is a "
        "property of the history rather than a claim made in this paragraph. Every constant "
        "below is IMPORTED here, never retyped.",
        "",
        f"**Unit of analysis: the `{personas.SIGN_UNIT}` (STAT-01).** A cell counts a question "
        "once if ANY of that row's draws for it carried the column persona's value. The paired "
        f"observation is per SLOT over the {personas.SLOTS_EXPECTED} core slots, ties folded "
        "against the alternative, n fixed.",
        "",
        f"**Training seeds (D-14), one per persona:** `{personas.PERSONA_SEEDS}`. The gated "
        "contrast is WITHIN an adapter, so the seed cancels inside it; D-15 is the price.",
        "",
        f"**Holm step alphas at m = {family}:** "
        + ", ".join(f"{alpha:.7f}" for alpha in step_alphas)
        + ".",
        "",
        f"**The {step_alphas[0] - unanimity:.7f} margin is a known property of this design, stated "
        "before the run.** The achievable p values are multiples of 1/256: slot unanimity gives "
        f"{unanimity:.7f}, which clears the first step at {step_alphas[0]:.7f} by "
        f"{step_alphas[0] - unanimity:.7f}, while a SINGLE tie gives {one_tie:.7f} — above even "
        f"the last step's alpha of {step_alphas[-1]:.7f}. So the gate requires all "
        f"{family * persistence.SIGN_TEST_N} slot-level observations "
        f"({family} comparisons x {persistence.SIGN_TEST_N} slots) to favour the diagonal. There "
        "is no partial credit anywhere in this design.",
        "",
        f"**The adapter-off row `{personas.BASE_ROW}` is COMPUTED and PUBLISHED but NOT a member "
        "of the family.** The family is derived over the three personas only. Admitting the base "
        f"row would make a seventh comparison, pricing Holm's first alpha at "
        f"{persistence.HOLM_ALPHA / (family + 1):.7f} — BELOW the achievable {unanimity:.7f} — so "
        "the headline would die arithmetically at every possible outcome, including perfect "
        "unanimity. `assert_phase17_family_closed` refuses any pair naming it at runtime, and a "
        "static scan refuses a new call site.",
        "",
        "| # | comparison | declared alternative (committed before the run) |",
        "| --- | --- | --- |",
    ]
    for index, pair in enumerate(personas.HOLM_FAMILY_CELLS, start=1):
        blocks.append(f"| {index} | `{pair[0]}` vs `{pair[1]}` | {gate['alternative'][pair]} |")

    blocks += [
        "",
        "## The Matrix",
        "",
        BASE_COLUMN_PURPOSE,
        "",
        CLUSTERING_ENDS_LABEL,
        "",
        f"Interval: `{persistence.BOOTSTRAP_METHOD}`, {resamples:,} resamples, seed "
        f"{persistence.BOOTSTRAP_SEED}, alpha {persistence.BOOTSTRAP_ALPHA}, with the SLOT as the "
        "cluster.",
        "",
        f"**Wilson label (T-16-41).** {persistence.WILSON_LABEL.replace('fact', 'slot')}",
        "",
        "| row (adapter) | "
        + " | ".join(f"column `{label}`" for label in personas.PERSONAS)
        + " |",
        "| --- | " + " | ".join("---" for _ in personas.PERSONAS) + " |",
    ]
    for row in rows:
        cells = " | ".join(
            _matrix_cell_text(described[(row, label)]) for label in personas.PERSONAS
        )
        blocks.append(f"| `{row}` | {cells} |")

    blocks += [
        "",
        "## Categories",
        "",
        CATEGORY_ROW_PROPERTY_NOTE,
        "",
        BASE_PRIOR_DERIVATION_NOTE,
        "",
        "| row (adapter) | " + " | ".join(f"`{name}`" for name in CATEGORIES) + " |",
        "| --- | " + " | ".join("---" for _ in CATEGORIES) + " |",
    ]
    for row in rows:
        entry = matrix[(row, personas.PERSONAS[0])]
        blocks.append(f"| `{row}` | " + " | ".join(str(entry[name]) for name in CATEGORIES) + " |")

    blocks += [
        "",
        BASE_PRIOR_SEED_ANCHOR_NOTE,
        "",
        "| slot | seeded prior | reproduced by the adapter-off column |",
        "| --- | --- | --- |",
    ]
    for slot, entry in prior_anchor.items():
        seeds = ", ".join(f"`{seed}`" for seed in entry["seeds"])
        verdict = (
            "yes"
            if entry["reproduced"]
            else "**NO — investigate this sweep before trusting the derivation on the other slots**"
        )
        blocks.append(f"| `{slot}` | {seeds} | {verdict} |")

    blocks += [
        "",
        "## Gate",
        "",
        f"> {personas.GATE_AGGREGATION_RATIONALE}",
        "",
        GATE_PUBLISHING_NOTE,
        "",
        "| comparison | slot signs | exact p | alpha at step | rejected |",
        "| --- | --- | --- | --- | --- |",
    ]
    for pair, p, alpha_at_step, rejected in gate["holm"]:
        signs = " ".join(f"{sign:+d}" for sign in gate["signs"][pair])
        blocks.append(
            f"| `{pair[0]}` vs `{pair[1]}` | {signs} | {p:.7f} | {alpha_at_step:.7f} | "
            f"{'YES' if rejected else 'no'} |"
        )

    rejected_rows = [row for row in gate["holm"] if row[-1]]
    blocks += [
        "",
        "## Verdict",
        "",
        f"**`gate_cleared` returns `{cleared}`** over the six rows above — "
        f"{len(rejected_rows)} of {len(personas.HOLM_FAMILY_CELLS)} comparisons rejected. That "
        "line is the imported function's own return value, not prose written around the numbers.",
        "",
    ]
    if cleared:
        blocks += [
            "All six pre-registered comparisons rejected at their Holm step, so the phase's claim "
            "— that separately-taught personas stay isolated in the weights — is DEMONSTRATED at "
            "the pre-registered level:",
            "",
        ]
        blocks += [
            f"- `{pair[0]}` vs `{pair[1]}` — {gate['alternative'][pair]}; p = {p:.7f} < alpha "
            f"{alpha_at_step:.7f}"
            for pair, p, alpha_at_step, _ in gate["holm"]
        ]
    else:
        blocks += [
            "The gate did not clear, so the PRE-REGISTERED all-fail branch fires, in full and "
            "as written before any adapter trained:",
            "",
            f"> {personas.ALL_FAIL_BRANCH}",
            "",
            "### (a) The diagonal magnitude, per persona",
            "",
            "| persona | diagonal cell | answerable / questions + bounds | cluster bootstrap 95% |",
            "| --- | --- | --- | --- |",
        ]
        for label in personas.PERSONAS:
            entry = described[(label, label)]
            blocks.append(
                f"| `{label}` | `({label}, {label})` | {entry['proportion']['formatted']} | "
                f"({entry['bootstrap'][0]:.6f}, {entry['bootstrap'][1]:.6f}) |"
            )
        blocks += [
            "",
            "### (b) The adapter-off column",
            "",
            "Read off §The Matrix rather than restated, so the two cannot disagree.",
            "",
            "| cell | answerable / questions and bounds | cluster bootstrap 95% |",
            "| --- | --- | --- |",
        ]
        for label in personas.PERSONAS:
            entry = described[(personas.BASE_ROW, label)]
            blocks.append(
                f"| `({personas.BASE_ROW}, {label})` | {entry['proportion']['formatted']} | "
                f"({entry['bootstrap'][0]:.6f}, {entry['bootstrap'][1]:.6f}) |"
            )
        blocks += [
            "",
            "### The fork, rendered explicitly",
            "",
            "**If the diagonal is LOW**, this matrix has **NO POWER** to judge isolation: the "
            "adapters did not reliably reproduce their own values, so an off-diagonal near zero is "
            'what an instrument that measures nothing produces. *"Not demonstrated"* then means '
            '**"not judgeable"** — never *"isolation failed"*.',
            "",
            "**If the diagonal is HIGH and an off-diagonal is also high enough to block slot "
            "unanimity**, that is a REAL LEAKAGE FINDING and is reported as one: persona *j*'s "
            "value appeared under adapter *i* at a rate this test cannot separate from adapter "
            "*i*'s own recall.",
            "",
            "**The three diagonals are three separate ANCHORS and never a RANKING (D-15).** With "
            "one seed per persona a between-persona difference confounds content with "
            "initialization, so no sentence in this report orders the personas by diagonal.",
            "",
            COMPARISON_ANCHORS,
            "",
            D11_MILESTONE_PATTERN,
        ]

    off_diagonal = {
        (first, second): matrix[(first, second)]["rate"]
        for first in personas.PERSONAS
        for second in personas.PERSONAS
        if first != second
    }
    selected = personas.worst_pair(off_diagonal)
    blocks += [
        "",
        "## Replication (ISO-05)",
        "",
        REPLICATION_DESCRIPTIVE_NOTE,
        "",
        "| ordered off-diagonal cell | question-unit rate (the selection input) |",
        "| --- | --- |",
    ]
    for cell in sorted(off_diagonal):
        blocks.append(f"| `({cell[0]}, {cell[1]})` | {off_diagonal[cell]:.6f} |")
    blocks += [
        "",
        f"**Selected pair:** `{selected[0]}` / `{selected[1]}`, at the pre-registered replication "
        f"seeds `{personas.REPLICATION_SEEDS[selected[0]]}` and "
        f"`{personas.REPLICATION_SEEDS[selected[1]]}` (k = 3 counting the original seed).",
        "",
        REPLICATION_PENDING_LINE,
        "",
        "## Provenance",
        "",
        "One block per sweep process. Four distinct pids are what EVIDENCE the process split "
        "rather than assert it, and the two weight digests carry two different claims: the live "
        "digest says WHICH WEIGHTS were resident, the file digest says WHICH FILE was read, and "
        f"neither can witness inertness — {BASE_COLUMN_NOTE}",
        "",
        "| sweep | git SHA | pid | device | wall clock (min) | live `lora_B` sha256 | adapter file "
        "sha256 | adapter enabled | `forbid_ids` sha256 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    blocks += [_provenance_row(record) for record in sweep_records]
    blocks.append("")

    text = "\n".join(blocks)
    _prove(
        _verdict.recorded_verdict(text) is not None,
        "the rendered report carries no `## Verdict` section the clobber guard could anchor on, so "
        "a later run would overwrite this phase's committed evidence in silence",
    )
    _prove(
        re.search(r"\b0(\.0+)?%", text) is None,
        "the rendered report contains a bare zero percentage — STAT-02 forbids it in any committed "
        "report or figure, because a bare zero states a certainty the sample does not have. Every "
        "zero renders as its numerator over its denominator with BOTH ends of the clustering "
        "assumption attached",
    )
    ISOLATION_REPORT_PATH.write_text(text, encoding="utf-8")
    print(f"[phase17_isolation] wrote {ISOLATION_REPORT_PATH}")
    return text


def prereg_commit():
    """The commit that ADDED ``scripts/phase17_personas.py`` — the citation, resolved not asserted.

    ``phase16_persistence.ladder_report_commit``'s register, with ``--diff-filter=A`` because that
    is the filter ``tests/test_phase16_prereg.py``'s ordering guard itself uses: it returns the
    EARLIEST add, which is the commit the ancestry rule is anchored on. The last line of the log is
    the oldest, so the citation is the commit a reader can actually check the ordering against.
    """
    import subprocess

    result = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%h", "--", str(PREREG_PATH)],
        capture_output=True,
        text=True,
        cwd=_REPO_ROOT,
    )
    adds = result.stdout.split()
    _prove(
        adds,
        f"{PREREG_PATH} has no add commit in this repository — the pre-registration must be "
        "COMMITTED before the matrix that cites it, and that ordering is this phase's whole "
        "defence against a constant chosen after seeing a number (STAT-05)",
    )
    return adds[-1]


def run_report_mode(*, resamples=persistence.BOOTSTRAP_RESAMPLES):
    """Assemble ``results/phase17_isolation_report.md`` from the four recorded sweeps.

    Pure CPU: no torch, no model, no tokenizer, no generation. The ORDER is not incidental and each
    step is a precondition of the next:

    1. **Refuse to clobber a recorded verdict.** FIRST, before a byte is read.
    2. Read the four UNSCOPED records by name (never a glob — 17-11's replicates must not enter).
    3. ``assert_sweeps_ran_on_distinct_weights`` — **BEFORE any scoring**. This is ISO-04's
       unskippable half and the reason it exists: assembling the matrix is IMPOSSIBLE unless the
       sweeps provably ran on different weights, because a silently no-opped swap produces a
       fabricated matrix in which one column reads high in every row (the shape 17-04 measured).
    4. The base row's empirical prior texts (D-13).
    5. ``assemble_matrix`` over **all four records** — the base row is a COMPUTED row of the same
       matrix under the same rate definition (RESEARCH:900), and ``classify`` handles it with
       ``own=None``. Passing only the adapter records leaves cells ``(base, j)`` uncomputed, which
       is exactly the number §The Matrix and D-10's branch (b) are required to publish;
       ``base_texts`` cannot cover the gap, because ``classify``'s ordering scores any completion
       carrying persona j's value as ``leak`` long before the ``base_texts`` membership test is
       reached.
    6. The descriptive block for all 12 cells, then the gate over the nine adapter cells.
    7. The writer.

    NOTHING here computes a pooled rate over the cells (STAT-06: SC5 forbids gating one, and a
    printed number gets quoted as a gate). Phase 16's per-fact grouping helper is likewise never
    reached at any depth: its ``rate`` is ``sum(k)/sum(n)`` — the DRAW rate — and STAT-01 makes the
    QUESTION the unit of analysis, so routing this matrix through it would silently reprice every
    published cell. (That function's name is deliberately not written out here: this plan's
    acceptance criteria grep this source for it, and a docstring mention would make that scan hit on
    prose. ``tests/test_phase17_stats.py`` asserts the absence of a CALL SITE, which is the
    invariant the grep is a proxy for.) No step orders the three personas by diagonal (D-15).
    """
    assert_isolation_report_not_clobbered()
    records = read_sweep_records()
    assert_sweeps_ran_on_distinct_weights(records)

    by_label = {record[SWEEP_LABEL_KEY]: record for record in records}
    base_texts = base_texts_by_slot(by_label[personas.BASE_ROW])
    matrix = assemble_matrix(records, values_by_slot(), base_texts)

    described = describe_matrix(matrix, draws_per_question(records), resamples=resamples)
    gate = compare_cells(cell_rates(matrix))
    return render_report(
        matrix,
        described,
        gate,
        records,
        base_prior_anchor(base_texts),
        resamples=resamples,
    )


def main(argv=None):
    """Dispatch — exhaustive over the three modes, with NO default branch.

    The ``run_condition`` register: the target is proved to be in its expected tuple FIRST, and a
    result is proved to have been produced LAST. A name in ``SWEEPS`` with no dispatch branch means
    the pre-registration and this dispatch have drifted apart, and the sweep would silently
    contribute nothing while looking like it ran.

    ``phase14_recall``'s per-tier scored-recall entry point is deliberately NOT reachable from
    here, at any depth. It scores against ``item.fact.value`` — which is PHASE 14's value, not this
    phase's — and re-running it per cell is exactly the N^2 cost ISO-02 exists to prevent. Phase 17
    generates once per sweep and scores the recorded completions afterwards. (That function's name
    is deliberately not written out anywhere in this file: this plan's acceptance criteria grep
    this source for it, and a docstring mention would make that scan hit on prose.)
    """
    args = build_parser().parse_args(argv)
    result = None
    if args.train is not None:
        _prove(
            args.train in personas.PERSONAS,
            f"--train {args.train!r} is not one of {personas.PERSONAS}",
        )
        result = run_one_persona_training(args.train, seed=args.seed)
    elif args.sweep is not None:
        _prove(
            args.sweep in SWEEPS,
            f"--sweep {args.sweep!r} is not one of {SWEEPS}",
        )
        result = run_one_sweep(args.sweep, seed=args.seed)
    elif args.report:
        # Never passes `resamples`: the published interval always runs at the pre-registered
        # BOOTSTRAP_RESAMPLES, and the count actually used is printed in the report either way.
        result = run_report_mode()
    _prove(
        result is not None,
        "the selected mode produced no result — a name in the parser's choices with no dispatch "
        "branch means the pre-registration and this dispatch have drifted apart, and the run would "
        "look like it happened while contributing nothing",
    )
    return result


if __name__ == "__main__":
    main()
