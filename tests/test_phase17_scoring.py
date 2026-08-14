"""Phase 17's scoring core — cell-blindness, the slot regrouping, the taxonomy, the base row.

CPU-only, GPU-free, no checkpoint I/O, no generation, no model load.
``scripts/phase17_isolation.py`` executes nothing at import beyond its ``sys.path`` bootstrap, so an
``importlib.util.spec_from_file_location`` load here runs no ``__main__`` guard, no tokenizer and no
model — and ``test_nothing_executes_at_import`` pins that claim rather than trusting the docstring
that makes it.

Every matrix test runs on SYNTHETIC persona values built in this file. That is not a shortcut: the
scoring core takes ``values_by_slot`` as a parameter and never reads the 24 minted values, so
exercising it on synthetic material is the STRONGER test of cell-blindness (SC3) — a scorer that
could see the cell would have nothing to see here, and a scorer that secretly read the committed
material would go red the moment these values disagree with it.

What is pinned here:
  1. **SC3** — ``score_completion``'s signature, its public name and its BODY carry no cell index.
  2. **ISO-02 / D-02** — the 104 held-out questions regroup to 8 slots x 13 questions, keyed by
     slot, with ``seed_index`` asserted against a direct read of the fixture, never re-enumerated.
  3. **D-12 / D-13 / D-17** — the four categories, the double match, and the two easiest to
     conflate (a ``none`` completion inside the base column's output versus outside it).
  4. **ISO-03** — the base row is a COMPUTED row with its own rate per persona value, and
     ``classify``'s ``own is None`` branch is what keeps it from scoring as a leak against itself.
  5. **ROADMAP SC1** — the shape a silently no-opped adapter swap actually produces, measured on
     synthetic records rather than argued (``test_no_op_swap_produces_the_recorded_shape``).
"""

import ast
import importlib.util
import inspect
import json
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_ISOLATION_PATH = _REPO_ROOT / "scripts" / "phase17_isolation.py"
_FIXTURE_PATH = _REPO_ROOT / "results" / "phase16_recall_sample.json"


def _load_isolation():
    spec = importlib.util.spec_from_file_location("phase17_isolation", _ISOLATION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


iso = _load_isolation()
personas = iso.personas

# Already in `sys.modules` — the driver imports it — so this is a cache hit, not a second execution.
import phase16_persistence as persistence  # noqa: E402  (needs the sys.path insert above)

# SYNTHETIC persona values, one per (slot, persona). Deliberately unlike the minted material and
# substring-disjoint from each other, which is the property `filter_substring_disjoint` guarantees
# for the real values: if one value sat inside another, every correct answer would also register as
# a leak and these tests would pass on an artifact of the fixtures rather than on the code.
SYNTHETIC_VALUES = {
    slot: {label: f"val{label[-1]}{n}" for label in personas.PERSONAS}
    for n, slot in enumerate(personas.CORE_SLOTS)
}
EMPTY_BASE_TEXTS = {slot: frozenset() for slot in personas.CORE_SLOTS}


def _tree(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def _function_def(tree, name):
    """The named ``FunctionDef`` node, or ``None``.

    Returned rather than asserted so the CALLER can assert the function was found BEFORE asserting
    anything about its contents — a scan that finds nothing is green for the wrong reason, and a
    renamed function would otherwise make every structural guard below pass over an empty AST.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _identifiers(node):
    """Every name a subtree mentions: ``Name.id``, ``arg.arg`` and ``Attribute.attr``."""
    names = set()
    for child in ast.walk(node):
        for attribute in ("id", "arg", "attr"):
            value = getattr(child, attribute, None)
            if isinstance(value, str):
                names.add(value)
    return names


def _enclosing_functions(tree):
    """``node -> the innermost Function/ClassDef containing it``, or ``None`` for module scope.

    Module scope is recorded as ``None`` rather than dropped, because module scope is the most
    dangerous placement there is. The idiom ``tests/test_phase17_stats.py::_enclosing_functions``
    uses, widened to class bodies for the same reason.
    """
    owner = {}

    def walk(node, current):
        for child in ast.iter_child_nodes(node):
            scoped = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            inner = child if isinstance(child, scoped) else current
            owner[child] = current if inner is child else inner
            walk(child, inner)

    walk(tree, None)
    return owner


# ---------------------------------------------------------------------------------------------
# Synthetic sweep records — the shape plan 17-06 writes and plan 17-08 reads.
# ---------------------------------------------------------------------------------------------

N_SYNTHETIC_DRAWS = 2


def _sweep_record(sweep, completion_for, n_draws=N_SYNTHETIC_DRAWS):
    """One recorded sweep: 8 slots x 13 questions, ``n_draws`` completions each.

    The per-question keys are the ones 17-06's payload commits to (RESEARCH F-03), read through
    ``SWEEP_QUESTIONS_KEY`` / ``SWEEP_LABEL_KEY`` so a rename of either constant turns these tests
    red instead of leaving them agreeing with a record shape nobody writes any more.
    """
    entries = []
    for n, slot in enumerate(personas.CORE_SLOTS):
        for index in range(personas.QUESTIONS_PER_SLOT):
            entries.append(
                {
                    "slot": slot,
                    "seed_index": n * personas.QUESTIONS_PER_SLOT + index,
                    "question": f"synthetic {slot} question {index}",
                    "fact_id": f"synthetic_{slot}_{index}",
                    "completions": [completion_for(slot, index, draw) for draw in range(n_draws)],
                }
            )
    return {iso.SWEEP_LABEL_KEY: sweep, iso.SWEEP_QUESTIONS_KEY: entries}


def _says(label):
    """A row whose every completion carries ``label``'s value for the question's slot."""
    return lambda slot, index, draw: f"i go by {SYNTHETIC_VALUES[slot][label]} truly"


def _silent(slot, index, draw):
    """A completion naming no persona's value at all."""
    return f"the answer here is unknown to me {slot} {index} {draw}"


def _clean_records():
    """The success case: each adapter row answers with its OWN value; the base names nothing."""
    return [_sweep_record(label, _says(label)) for label in personas.PERSONAS] + [
        _sweep_record(personas.BASE_ROW, _silent)
    ]


# ---------------------------------------------------------------------------------------------
# SC3 — cell blindness
# ---------------------------------------------------------------------------------------------

_CELL_NAMES = {"i", "j", "cell", "own", "diagonal"}


def test_scorer_is_cell_blind():
    """SC3, in three layers: the signature, the public name, and the function's own body AST.

    The signature alone is not enough — a scorer could take ``(completion, slot_values)`` and still
    close over a module-level cell index, or branch on a persona name it reconstructs. The AST layer
    is what makes the property structural: the parameters say the cell is not passed in, and the
    body scan says it is not consulted from anywhere else either.
    """
    params = list(inspect.signature(iso.score_completion).parameters)
    assert params == ["completion", "slot_values"], (
        f"score_completion takes {params}. SC3 pins this signature precisely because a cell index "
        "in the scoring path makes diagonal-vs-leak a decision the scorer can get wrong in the "
        "flattering direction, and nothing downstream would show it"
    )
    assert not _CELL_NAMES & set(params)
    assert not iso.score_completion.__name__.startswith("_"), (
        "score_completion is private, so nothing outside this module can call the scorer directly "
        "— and a guard on a function the next caller reimplements slightly differently is no guard"
    )

    function = _function_def(_tree(_ISOLATION_PATH), "score_completion")
    assert function is not None, (
        "score_completion was not found in the AST of scripts/phase17_isolation.py — a renamed "
        "function would make every scan below green by finding nothing to scan"
    )
    offenders = sorted(_CELL_NAMES & _identifiers(function))
    assert not offenders, (
        f"score_completion's body mentions {offenders}. The scorer receives a string and one "
        "slot's {label: value} mapping and nothing else; a name from the cell vocabulary in its "
        "body means it learned the cell by some route the signature does not show"
    )
    compared = sorted(
        name
        for node in ast.walk(function)
        if isinstance(node, ast.Compare)
        for name in _CELL_NAMES & _identifiers(node)
    )
    assert not compared, f"score_completion branches on {compared} — that is a cell decision"


def test_nothing_executes_at_import():
    """The driver's own claim: the ``sys.path`` bootstrap is the ONLY unguarded module-scope call.

    Written as a walk to module SCOPE rather than a scan of ``tree.body``, because the bootstrap is
    nested inside an ``if`` — a scan restricted to ``tree.body`` finds zero calls and passes while
    checking nothing. Every CPU-only test in this file loads the driver with ``importlib`` on the
    strength of the claim this pins, and plan 17-06's ``main()`` loads a model and generates.

    The ``if __name__ == "__main__":`` block is excluded, because that guard is precisely what
    makes its body NOT run under ``importlib`` — and the exclusion is paid for rather than granted:
    the guard must exist exactly once and call exactly ``main``. Without those two assertions the
    exclusion would be an escape hatch that a second, differently-shaped guard could widen
    (``tests/test_phase16_ladder.py::test_main_exists_and_is_guarded``'s register).
    """
    tree = _tree(_ISOLATION_PATH)
    guards = [
        node
        for node in tree.body
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and getattr(node.test.left, "id", None) == "__name__"
    ]
    assert len(guards) == 1, "exactly one `if __name__ == '__main__':` block"
    guarded = {node for guard in guards for node in ast.walk(guard)}
    assert {
        node.func.id
        for node in guarded
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    } == {"main"}, "the __main__ guard must call main() and nothing else"

    enclosing = _enclosing_functions(tree)
    module_scope_calls = [
        ast.unparse(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and enclosing.get(node) is None
        and node not in guarded
    ]
    assert all(call.startswith("sys.path.insert") for call in module_scope_calls), (
        f"scripts/phase17_isolation.py runs {module_scope_calls} at import"
    )
    assert len(module_scope_calls) == 1, (
        f"expected exactly the one sys.path bootstrap call, found {module_scope_calls} — a vacuous "
        "count here would make this guard green against a file that lost its bootstrap"
    )


def test_the_material_has_exactly_one_reader():
    """SC3's structural half, as a committed pin rather than a one-shot acceptance grep.

    17-04's handover makes this a CROSS-PLAN contract: nothing in the scoring path may read the
    minted material, because ``assemble_matrix`` takes ``values_by_slot`` as a PARAMETER and that
    is what lets every matrix test above run on synthetic values. One named reader is the checkable
    form of it — a second one is where the coupling starts, and the coupling is invisible until a
    test that should have been independent starts agreeing with the committed material for free.
    """
    tree = _tree(_ISOLATION_PATH)
    readers = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and "PERSONA_FACTS" in ast.unparse(node)
    )
    assert readers == ["_minted_facts"], (
        f"{readers} name the minted material; exactly one accessor may. `slot_values` (scoring) "
        "and `run_one_persona_training` (teaching) need different shapes of it and both route "
        "through that one function"
    )
    assert iso._minted_facts is not None
    for name in ("score_completion", "classify", "base_texts_by_slot", "assemble_matrix"):
        body = ast.unparse(_function_def(tree, name))
        assert "_minted_facts" not in body, f"{name} reads the material — the scoring path may not"


# ---------------------------------------------------------------------------------------------
# ISO-02 / D-02 — the fixture regrouped by slot
# ---------------------------------------------------------------------------------------------


def test_slot_regrouping():
    """ISO-02 — 8 slots x 13 questions, keyed by slot, with the fixture's OWN ``seed_index``."""
    by_slot = iso.held_out_by_slot()

    assert len(by_slot) == personas.SLOTS_EXPECTED == 8
    assert sorted(by_slot) == sorted(personas.CORE_SLOTS)
    assert all(len(bucket) == personas.QUESTIONS_PER_SLOT == 13 for bucket in by_slot.values())
    assert sum(len(bucket) for bucket in by_slot.values()) == 104

    # Asserted against a DIRECT read of the fixture, never against a re-enumeration: re-stamping
    # `seed_index` from the regrouping's own ordering would silently REPAIR a mismatch instead of
    # surfacing it, and a repaired mismatch is indistinguishable downstream from one that never was.
    fixture = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    recorded = {
        (entry["fact_id"], entry["question"]): entry["seed_index"]
        for entry in fixture["questions"]["core_held_out"]
    }
    assert len(recorded) == 104, "the fixture's own (fact_id, question) keys are not unique"

    checked = 0
    for bucket in by_slot.values():
        for item in bucket:
            assert recorded[(item.fact.id, item.question)] == item.seed_index
            checked += 1
    assert checked == 104, f"only {checked} seed indices were checked — the loop found no items"


# ---------------------------------------------------------------------------------------------
# D-12 / D-17 — the scorer's labels
# ---------------------------------------------------------------------------------------------


def test_scorer_labels():
    """D-12's return domain on hand-built completions, including the whitespace-collapse case."""
    slot_values = {"persona_a": "thornvale", "persona_b": "keldrin", "persona_c": "morwen"}

    assert iso.score_completion("i come from thornvale", slot_values) == frozenset({"persona_a"})
    assert iso.score_completion("i have no idea at all", slot_values) == frozenset()

    # `contains_value` normalizes BOTH sides, collapsing runs of whitespace before the containment
    # test. That is load-bearing rather than cosmetic: byte-level BPE can land a space inside what
    # should be one word (the measured `'i am a mort  of musician'`), and without the collapse a
    # correct recall scores as a miss.
    spaced = {"persona_a": "sable wind", "persona_b": "keldrin", "persona_c": "morwen"}
    assert iso.score_completion("i live on  sable   wind street", spaced) == frozenset(
        {"persona_a"}
    ), "the whitespace collapse behind every published Phase 14 and Phase 16 rate is not in effect"


def test_double_match_returns_a_frozenset():
    """D-17 — two personas' values in one completion is recorded as BOTH, in insertion-free order.

    A priority order would be an arbitrary tiebreak biasing whichever persona sorts first, and a
    double match is itself evidence about interference: collapsing it to one label deletes exactly
    the observation this matrix exists to record.
    """
    slot_values = {"persona_a": "thornvale", "persona_b": "keldrin", "persona_c": "morwen"}
    completion = "maybe thornvale or maybe keldrin"

    labels = iso.score_completion(completion, slot_values)
    assert labels == frozenset({"persona_a", "persona_b"})
    assert isinstance(labels, frozenset), f"the scorer returned a {type(labels).__name__}"
    assert len(labels) == 2

    reordered = {
        "persona_c": slot_values["persona_c"],
        "persona_b": slot_values["persona_b"],
        "persona_a": slot_values["persona_a"],
    }
    assert iso.score_completion(completion, reordered) == labels, (
        "the result depends on the insertion order of slot_values — that IS an arbitrary priority "
        "order, arriving through the dict instead of through an if-chain"
    )


# ---------------------------------------------------------------------------------------------
# D-12 / D-13 — the four report categories
# ---------------------------------------------------------------------------------------------


def test_classify_categories():
    """D-12/D-13's four categories, including the two that are easiest to conflate."""
    assert sorted(iso.CATEGORIES) == ["base_prior", "confabulation", "diagonal", "leak"]
    assert list(inspect.signature(iso.classify).parameters) == [
        "labels",
        "own",
        "base_texts",
        "completion",
    ]

    a, b = "persona_a", "persona_b"
    assert iso.classify(frozenset({a}), a, frozenset(), "x") == "diagonal"
    assert iso.classify(frozenset({b}), a, frozenset(), "x") == "leak"

    # The pair that must not be conflated: the SAME `none` completion is a base prior when it
    # coincides with the adapter-off column's output for that slot, and a confabulation when it
    # does not. D-13 derives the first post-hoc rather than scoring it, which is why the two differ
    # only by what the base column produced and by nothing about the completion itself.
    text = "i really could not say"
    assert iso.classify(frozenset(), a, frozenset({text}), text) == "base_prior"
    assert iso.classify(frozenset(), a, frozenset(), text) == "confabulation"

    # SC3: a confabulation never shares a cell with a leak. They are separate categories because
    # "the model made something up" and "another persona's value appeared" are different findings,
    # and pooling them would let a leak hide inside a confabulation count.
    assert iso.classify(frozenset({b}), a, frozenset({text}), text) == "leak"
    assert iso.classify(frozenset({b}), a, frozenset(), text) != iso.classify(
        frozenset(), a, frozenset(), text
    )


def test_base_row_classifies_as_prior_never_leak():
    """ISO-03, the B4 regression — with ``own=None`` a persona value is the base's OWN prior.

    What the missing ``own is None`` branch would cost: the base row's completions fall through to
    ``leak``, so the base is recorded as leaking to itself from an adapter that does not exist, and
    cell ``(base, j)`` never gets a rate. That rate is the ONLY quantitative separator of "adapter i
    leaked persona j's value" from "the base was going to say that anyway" — the exact question
    ISO-03 exists to answer. Nothing else in the report goes red when it disappears.
    """
    labels = frozenset({"persona_b"})
    text = "everyone calls it that"

    assert iso.classify(labels, None, frozenset(), text) == "base_prior"
    assert iso.classify(labels, None, frozenset({text}), text) == "base_prior"
    assert iso.classify(labels, "persona_a", frozenset(), text) == "leak", (
        "the SAME inputs under an adapter row must score leak — if both rows agree, the base row "
        "is not a control, it is a fourth adapter"
    )
    assert iso.classify(frozenset(), None, frozenset(), text) == "confabulation"


def test_base_texts_by_slot_refuses_a_mis_selected_record():
    """D-13 — an empty base-prior set turns every base prior into a confabulation, silently."""
    base = _sweep_record(personas.BASE_ROW, _silent)
    texts = iso.base_texts_by_slot(base)
    assert sorted(texts) == sorted(personas.CORE_SLOTS)
    assert all(
        len(slot_texts) == personas.QUESTIONS_PER_SLOT * N_SYNTHETIC_DRAWS
        for slot_texts in texts.values()
    )

    adapter = _sweep_record("persona_a", _says("persona_a"))
    try:
        iso.base_texts_by_slot(adapter)
    except SystemExit as exit_:
        assert "ISO-03" in str(exit_) and "persona_a" in str(exit_)
    else:  # pragma: no cover
        raise AssertionError(
            "the base prior was derived from an ADAPTER sweep — every completion that adapter "
            "produced would then count as 'what the base was going to say anyway'"
        )

    short = dict(base)
    short[iso.SWEEP_QUESTIONS_KEY] = [
        entry for entry in base[iso.SWEEP_QUESTIONS_KEY] if entry["slot"] != "pet_name"
    ]
    try:
        iso.base_texts_by_slot(short)
    except SystemExit as exit_:
        assert "D-13" in str(exit_) and "pet_name" in str(exit_)
    else:  # pragma: no cover
        raise AssertionError("a base record missing a whole slot produced a base-prior mapping")


# ---------------------------------------------------------------------------------------------
# ISO-03 / STAT-01 — the matrix, and its computed base row
# ---------------------------------------------------------------------------------------------


def test_matrix_is_twelve_cells_in_the_question_unit():
    """STAT-01 — 12 cells, question-unit rates, ``per_slot`` in ``cluster_bootstrap``'s shape."""
    matrix = iso.assemble_matrix(_clean_records(), SYNTHETIC_VALUES, EMPTY_BASE_TEXTS)

    assert len(matrix) == 12, f"the matrix is {len(matrix)} cells, not the 3x3 block plus 3 base"
    assert sorted(matrix) == sorted(
        (row, label)
        for row in tuple(personas.PERSONAS) + (personas.BASE_ROW,)
        for label in personas.PERSONAS
    )

    for key, cell in matrix.items():
        assert set(cell) == {
            "per_slot",
            "n_answerable",
            "n_questions",
            "rate",
            "contradiction_draws",
            *iso.CATEGORIES,
        }, f"cell {key} carries {sorted(cell)}"
        assert len(cell["per_slot"]) == personas.SLOTS_EXPECTED
        assert all(len(pairs) == personas.QUESTIONS_PER_SLOT for pairs in cell["per_slot"].values())
        assert all(n == 1 and k in (0, 1) for pairs in cell["per_slot"].values() for k, n in pairs)
        assert cell["n_questions"] == 104
        assert cell["rate"] == cell["n_answerable"] / cell["n_questions"]
        assert personas.SIGN_UNIT == "question"

    for label in personas.PERSONAS:
        assert matrix[(label, label)]["rate"] == 1.0
        for other in personas.PERSONAS:
            if other != label:
                assert matrix[(label, other)]["rate"] == 0.0
        assert matrix[(personas.BASE_ROW, label)]["rate"] == 0.0

    # `per_slot` is exactly what the committed two-stage bootstrap resamples — asserted by running
    # it, not by matching a shape. A structure that merely looks right is a structure that fails at
    # report time, after the GPU sweeps are already spent.
    lo, hi = persistence.cluster_bootstrap(matrix[("persona_a", "persona_a")]["per_slot"])
    assert lo == hi == 1.0


def test_matrix_has_a_computed_base_row():
    """ISO-03 — the base cells carry real rates and denominators, and the row is not optional."""

    # The base emits persona B's value on 4 of the 13 `pet_name` questions and nothing elsewhere.
    def base_partial(slot, index, draw):
        if slot == "pet_name" and index < 4:
            return f"round here it is {SYNTHETIC_VALUES['pet_name']['persona_b']} they say"
        return _silent(slot, index, draw)

    records = [_sweep_record(label, _says(label)) for label in personas.PERSONAS] + [
        _sweep_record(personas.BASE_ROW, base_partial)
    ]
    matrix = iso.assemble_matrix(records, SYNTHETIC_VALUES, EMPTY_BASE_TEXTS)

    cell = matrix[(personas.BASE_ROW, "persona_b")]
    assert (cell["n_answerable"], cell["n_questions"]) == (4, 104)
    assert cell["rate"] == 4 / 104
    assert (cell["base_prior"], cell["leak"], cell["diagonal"]) == (4, 0, 0), (
        "the base row scored a leak or a diagonal, which is impossible with own=None unless "
        "classify's branch 2 was removed — the base would then be counted as evidence against the "
        "adapters (ISO-03)"
    )
    assert cell["confabulation"] == 100
    assert sum(k for pairs in cell["per_slot"].values() for k, _n in pairs) == 4
    assert sum(k for k, _n in cell["per_slot"]["pet_name"]) == 4
    for other in ("persona_a", "persona_c"):
        assert matrix[(personas.BASE_ROW, other)]["n_answerable"] == 0

    # Withholding the base record must abort rather than publish an empty column as "the control".
    try:
        iso.assemble_matrix(records[:3], SYNTHETIC_VALUES, EMPTY_BASE_TEXTS)
    except SystemExit as exit_:
        assert "ISO-03" in str(exit_) and "EMPTY BASE COLUMN" in str(exit_)
    else:  # pragma: no cover
        raise AssertionError("three adapter records assembled a matrix with no base row")


# ---------------------------------------------------------------------------------------------
# ROADMAP SC1 — what a silently no-opped adapter swap actually produces
# ---------------------------------------------------------------------------------------------


def test_no_op_swap_produces_the_recorded_shape():
    """ROADMAP SC1's confirmation, MEASURED on synthetic records rather than argued.

    The artefact of a swap that silently no-ops: every sweep generates from whichever adapter was
    actually resident, so all three "adapter" rows carry persona A's values. ROADMAP records
    **column collapse** as the expected shape at MEDIUM confidence and explicitly defers the
    confirmation to this implementation.

    **CONFIRMED — the measured shape is column collapse.** Persona A's COLUMN reads 1.0 in all
    three adapter rows; every other adapter cell is 0.0; the diagonal reads (1.0, 0.0, 0.0), so two
    of the three diagonal cells fall to zero rather than the diagonal being perfected. The base row
    is unaffected at 0.0 across all three columns, and the row taxonomy is unambiguous: row A scores
    104 diagonal, rows B and C score 104 leak each.

    **The pre-registered gate does NOT clear on it.** Only the two comparisons in row A reject
    (p = 0.0078125 each, 8/8 unanimity); rows B and C give p = 1.0 — their diagonals lose every slot
    to the A column, and the B-vs-C contrast is 8 ties. 2 of 6 rejections, so ``gate_cleared`` is
    ``False`` under D-18's all-six rule.

    That the gate would fail is NOT what makes the canary unnecessary — it is what makes the shape
    knowable. Both candidate shapes are equally fake and equally invisible in the completions, and
    the ISO-04 canary in plan 17-06 sits in the same place either way.
    """
    records = [_sweep_record(label, _says("persona_a")) for label in personas.PERSONAS] + [
        _sweep_record(personas.BASE_ROW, _silent)
    ]
    base_texts = iso.base_texts_by_slot(records[-1])
    matrix = iso.assemble_matrix(records, SYNTHETIC_VALUES, base_texts)

    resident = personas.PERSONAS[0]
    for row in personas.PERSONAS:
        assert matrix[(row, resident)]["rate"] == 1.0, (
            "the resident adapter's column is not uniformly high — the measured no-op shape is "
            "COLUMN COLLAPSE, and this test is ROADMAP SC1's record of it"
        )
        for label in personas.PERSONAS:
            if label != resident:
                assert matrix[(row, label)]["rate"] == 0.0
    assert [matrix[(row, row)]["rate"] for row in personas.PERSONAS] == [1.0, 0.0, 0.0], (
        "two of three diagonals must collapse with the columns; a perfect diagonal would be the "
        "OTHER candidate shape and would change what this test records"
    )
    for label in personas.PERSONAS:
        assert matrix[(personas.BASE_ROW, label)]["rate"] == 0.0

    assert matrix[(resident, resident)]["diagonal"] == 104
    for row in personas.PERSONAS[1:]:
        assert (matrix[(row, resident)]["leak"], matrix[(row, resident)]["diagonal"]) == (104, 0)
    # The base row's own completions all coincide with the base column by construction, so its
    # every question is a base prior — the honest reading of a row that IS the base prior.
    assert matrix[(personas.BASE_ROW, resident)]["base_prior"] == 104

    # Would the pre-registered gate clear on this fabricated matrix? Measured, through the
    # committed instruments, not asserted from the shape.
    per_cell = {
        key: {
            slot: {"rate": sum(k for k, _n in pairs) / sum(n for _k, n in pairs)}
            for slot, pairs in cell["per_slot"].items()
        }
        for key, cell in matrix.items()
        if key[0] != personas.BASE_ROW
    }
    p_values = {
        pair: persistence.sign_test_exact(persistence.fact_signs(per_cell, pair))
        for pair in personas.HOLM_FAMILY_CELLS
    }
    personas.assert_phase17_family_closed(tuple(p_values))
    rows = persistence.holm(p_values)
    assert sum(1 for row in rows if row[-1]) == 2, (
        f"expected exactly the two row-{resident} comparisons to reject, got "
        f"{[row[-1] for row in rows]}"
    )
    assert personas.gate_cleared(rows) is False, (
        "a no-op adapter swap cleared the pre-registered gate — the fabricated matrix would then "
        "be published as an isolation result"
    )
