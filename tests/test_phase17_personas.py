"""ISO-01's minted persona material — the PERMANENT, checkpoint-free half of the pre-flight.

What this pins, forever: the 24 minted values' **token-count census** and **byte-fallback
round-trip exactness** against the FROZEN ``artifacts/tokenizer.json``, D-04's collision in all
eight core slots, D-06's zero reuse of any committed Phase 14 pool, D-05's surface-arbitrariness,
and that all four 17-01 minting filters still bite on the committed material. ``artifacts/
tokenizer.json`` and ``results/phase16_recall_sample.json`` are both git-tracked, so every
assertion here runs in the CPU-only, GPU-free CI suite with zero skips.

**What this file does NOT cover, and structurally CANNOT** — the same split
``tests/test_phase14_factset.py:8-18`` had to make, for the same reason. The *guessability* half of
the ISO-01 pre-flight — the measurement that the base does not already produce these 24 values —
is **checkpoint-specific**: it belongs to ``convbase_best.pt``'s actual learned priors, needs the
278 MB checkpoint on MPS, and has no meaning as a standing invariant. A future checkpoint
inheriting a green run of this file has inherited **nothing** about guessability. Re-validating it
requires a fresh gated measurement (plans 17-05 / 17-07 plus a human SC2 verdict), **not** a test
re-run.

Scripts-load justification: the material MUST live in a committed driver module for git history to
be the proof that no value was chosen after a Phase 17 number existed. ``scripts/
phase17_persona_facts.py`` defines no ``main()`` and imports no torch, so an ``importlib`` load
runs nothing.
"""

import ast
import importlib.util
import json
import pathlib
import sys

import pytest

from personacore.tokenizer import from_json

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_PREREG_PATH = _REPO_ROOT / "scripts" / "phase17_personas.py"
_MATERIAL_PATH = _REPO_ROOT / "scripts" / "phase17_persona_facts.py"
_GATE_PATH = _REPO_ROOT / "scripts" / "phase17_persona_gate.py"
_FIXTURE_PATH = _REPO_ROOT / "results" / "phase16_recall_sample.json"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _REPO_ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


material = _load("phase17_persona_facts")
personas = _load("phase17_personas")
fs = _load("phase14_factset")

import phase14_recall as recall  # noqa: E402  (needs the sys.path insert above)
import teach_persona as teaching  # noqa: E402  (the GO/ADAPT enforcement under test)
from _verdict import recorded_verdict  # noqa: E402  (the ONE anchored section read)

_FACTS = material.all_facts()
_VALUES = tuple(fact.value for fact in _FACTS)

# Every adapter-reaching call the ISO-01 pre-flight must never make. Named here rather than inline
# so the AST scan below and a future reader see ONE list: an adapter arriving by any of these four
# routes produces the same wrong measurement.
_ADAPTER_CALLS = ("load_adapted_model", "inject_lora", "load_adapter_weights", "load_adapter")


def _called_names(node):
    """Every callee name reached from ``node``, bare (``f()``) and attribute (``m.f()``) alike."""
    return {
        name
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        for name in (getattr(child.func, "id", None), getattr(child.func, "attr", None))
        if name
    }


@pytest.fixture(scope="module")
def tok():
    # The FROZEN production artifact — the registry that ships is what matters, never a freshly
    # trained tokenizer (Pitfall 6). The census below was measured against THIS file.
    return from_json(_REPO_ROOT / "artifacts" / "tokenizer.json")


@pytest.fixture(scope="module")
def questions():
    """The 104 ``core_held_out`` questions — D-03's gated tier, the binding Phase 16 fixture."""
    fixture = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    return tuple(entry["question"] for entry in fixture["questions"]["core_held_out"])


def _levenshtein(left, right):
    """Edit distance, iterative two-row. Local because D-05 is the only caller in the repo."""
    previous = list(range(len(right) + 1))
    for i, a in enumerate(left, 1):
        current = [i]
        for j, b in enumerate(right, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (a != b)))
        previous = current
    return previous[-1]


def test_token_census_matches_locked_literals(tok):
    """The committed ``VALUE_TOKEN_CENSUS`` IS the expectation; never recompute it in-test.

    A drift here means either the frozen tokenizer changed or a value was edited after it was
    measured — both invalidate the budget-parity claim the census exists to support. Recomputing
    the dict in-test would assert only that the tokenizer agrees with itself.
    """
    assert set(material.VALUE_TOKEN_CENSUS) == {fact.id for fact in _FACTS}
    by_id = {fact.id: fact for fact in _FACTS}
    for fact_id, expected in material.VALUE_TOKEN_CENSUS.items():
        assert len(tok.encode(by_id[fact_id].value)) == expected, fact_id


def test_census_fits_the_recall_budget(tok):
    """The census must land the derived generation budget on exactly the published 48.

    ``RECALL_MAX_NEW_TOKENS = 48`` is ``max(census) + PREAMBLE_HEADROOM (32) + TAIL_HEADROOM (8)``
    rounded up to a multiple of 8 (``phase14_recall.py:120-145``), and
    ``phase16_persistence.SHARED_ARM_CONFIG.max_new_tokens`` reads that integer. A 9-token value
    moves the raw budget to 49 and the rounded budget to 56, so the Phase 17 arms would no longer
    share a generation budget with any published Phase 14 or Phase 16 number.

    Derived through ``derive_recall_budget`` itself rather than a re-typed formula: a hand-copied
    ``max + 32 + 8`` in this file would be a second copy of the rule, free to stop agreeing with
    the one the budget is actually computed from.
    """
    assert max(material.VALUE_TOKEN_CENSUS.values()) <= personas.MAX_VALUE_TOKENS

    budget = recall.derive_recall_budget(
        material.VALUE_TOKEN_CENSUS.values(),
        preamble=recall.PREAMBLE_HEADROOM,
        tail=recall.TAIL_HEADROOM,
        step=recall.BUDGET_STEP,
    )
    assert budget == recall.RECALL_MAX_NEW_TOKENS == 48, (
        f"the Phase 17 census derives a budget of {budget}, not the published 48 that every "
        "Phase 14 and Phase 16 arm generated under — the isolation matrix would stop being "
        "comparable to the numbers it is anchored against"
    )
    # tok is taken so the bound above is checked against the same frozen tokenizer the census was
    # measured on, in the same session as test_token_census_matches_locked_literals.
    assert max(len(tok.encode(value)) for value in _VALUES) <= personas.MAX_VALUE_TOKENS


def test_byte_fallback_roundtrip(tok):
    """Every minted value survives ``decode(encode(v)) == v``.

    The scorer matches on the decoded surface string, so a value that changes shape through the
    tokenizer would be scored against a string the model was never taught.
    """
    for fact in _FACTS:
        assert tok.decode(tok.encode(fact.value)) == fact.value, fact.id


def test_no_dead_ids_emitted(tok):
    """The frozen tokenizer decodes 547 of 8192 ids; a value reaching a dead one is untestable.

    ``forbid_ids`` masks the undecodable ids to ``-inf`` before sampling, so such a value could
    never be produced at any temperature — it would score 0 for reasons that have nothing to do
    with isolation.
    """
    live = set(tok.vocab) | set(tok.special_tokens.values())
    for fact in _FACTS:
        assert set(tok.encode(fact.value)) <= live, fact.id


def test_all_eight_slots_collide():
    """D-04 — collision in ALL eight core slots, with no deliberately non-colliding subset.

    Each persona's slot set is checked against ``phase17_personas.CORE_SLOTS``, the ONE canonical
    list committed in 17-01, and never against the other two personas: two things checked against a
    third cannot drift into agreeing on a wrong answer, whereas two checked against each other can.
    """
    assert set(material.PERSONA_FACTS) == set(personas.PERSONAS)
    for persona, facts in material.PERSONA_FACTS.items():
        assert len(facts) == personas.SLOTS_EXPECTED, persona
        assert {fact.slot for fact in facts} == set(personas.CORE_SLOTS), persona
        # `Fact.tier` is the fact set's own core/soft vocabulary (phase14_factset.py:57), which is
        # a DIFFERENT axis from `phase17_personas.GATED_TIER` ("held-out", the fixture's split).
        # Every Phase 17 value is core: D-03 scores `core_held_out` only.
        assert all(fact.tier == "core" for fact in facts), persona

    for slot in personas.CORE_SLOTS:
        by_persona = {
            persona: next(fact.value for fact in facts if fact.slot == slot)
            for persona, facts in material.PERSONA_FACTS.items()
        }
        agreeing = sorted(
            (left, right)
            for left in by_persona
            for right in by_persona
            if left < right and by_persona[left] == by_persona[right]
        )
        assert not agreeing, (
            f"{agreeing} carry the SAME value in slot {slot!r}. D-04 requires a contradiction in "
            "every core slot: a slot where two personas agree contributes a free hit to that "
            "pair's off-diagonal cell, so the matrix reports leakage the model never produced"
        )
    assert len(set(_VALUES)) == 24


def test_no_value_reused_from_any_phase14_pool():
    """D-06 — all 24 minted fresh, against a forbidden set proved to be non-vacuous.

    The disjointness is only worth as much as the set it is proved against, so a known member of
    every named source is asserted present: a broken pool walk would otherwise make the
    disjointness trivially true by covering nothing.
    """
    assert not (set(_VALUES) & material.FORBIDDEN_VALUES)

    for expected, source in (
        ("quillon", "CANDIDATE_POOL"),
        ("varek", "CALIBRATION_POOL"),
        ("mirek", "REGISTER_ARM_POOL"),
        ("brindlemoor", "LOCKED_FACTS"),
        ("chartreuse", "SOFT_TIER_FACTS"),
        ("calderwick", "GATE_REJECTED_CANDIDATES"),
        ("the country", "BASE_PRIOR_SEEDS"),
    ):
        assert expected in material.FORBIDDEN_VALUES, (
            f"{expected!r} from {source} is missing from FORBIDDEN_VALUES — the D-06 disjointness "
            "proof is then green over a set that does not cover the pool it claims to"
        )

    # GATE_REJECTED_CANDIDATES is also D-10's contradiction-detector LEXICON SOURCE. A persona
    # value drawn from it would stop the detector separating "adapter i leaked persona j's value"
    # from "adapter i answered with its own" — the one discrimination the off-diagonals exist for.
    lexicon = {fact.value for fact in fs.LOCKED_FACTS + fs.GATE_REJECTED_CANDIDATES}
    assert lexicon <= material.FORBIDDEN_VALUES
    assert not (set(_VALUES) & lexicon)


def test_material_passes_all_four_filters(tok, questions):
    """The positive control through the ONE entry point 17-05's pre-flight driver will call.

    Runs the two composition proofs plus all four 17-01 minting filters over the committed
    material. Every individual property is pinned by its own test above and below; this pins that
    the single call site 17-05 uses reaches them all.
    """
    checked = material.assert_material_passes_filters(tok, questions)
    assert checked == _VALUES
    assert len(checked) == 24


def test_substring_disjointness_bites(tok, questions):
    """The filter is watched FAILING, not merely watched passing (RESEARCH Pitfall 6).

    The concrete failure: if persona A's value sits inside persona B's value, every correct
    A-answer also registers as a B-leak — an off-diagonal hit manufactured out of nothing, closing
    the gate on the choice of material rather than on the model's behaviour.
    """
    personas.filter_substring_disjoint(_VALUES, material.FORBIDDEN_VALUES)  # positive control

    nested = _VALUES + (_VALUES[0][:4],)
    try:
        personas.filter_substring_disjoint(nested, material.FORBIDDEN_VALUES)
    except SystemExit as exit_:
        assert _VALUES[0] in str(exit_)
    else:  # pragma: no cover
        raise AssertionError(
            "a synthetic value nested inside a committed one passed filter_substring_disjoint — "
            "the scorer is substring containment, so every correct answer carrying the outer value "
            "would also count as a hit for the inner one"
        )

    # The forbidden set is inside the same union on purpose: a minted value hiding inside a Phase
    # 14 value would equally break D-10's contradiction detector.
    with_phase14_nesting = _VALUES + ("quillo",)
    try:
        personas.filter_substring_disjoint(with_phase14_nesting, material.FORBIDDEN_VALUES)
    except SystemExit as exit_:
        assert "quillon" in str(exit_)
    else:  # pragma: no cover
        raise AssertionError("a value nested inside a Phase 14 locked value passed the filter")


def test_no_value_appears_in_any_fixture_question(questions):
    """The clean-room property — a question that names a value hands the model the answer.

    The cell would then measure copying from the prompt rather than recall from the weights, and a
    diagonal inflated that way is indistinguishable from isolation working. The question count is
    asserted FIRST so a broken fixture read cannot make the filter pass on an empty list.
    """
    assert len(questions) == personas.QUESTIONS_PER_SLOT * personas.SLOTS_EXPECTED == 104
    personas.filter_absent_from_questions(_VALUES, questions)

    # The negative half: the filter must actually see the questions it was handed.
    try:
        personas.filter_absent_from_questions((questions[0].split()[0],), questions)
    except SystemExit:
        pass
    else:  # pragma: no cover
        raise AssertionError("a word taken straight out of a fixture question passed the filter")


def test_ids_carry_no_value():
    """D-02 — a Phase 17 fact id carries no value, its own or any other persona's.

    Every Phase 14 fact id embeds its own value (``cand_town_brindlemoor``), which is precisely why
    this matrix is keyed on ``slot``: an id-keyed join would drag Phase 14 values in, and an id that
    embedded a Phase 17 value would put one into every log line, report row and file name.
    """
    for fact in _FACTS:
        offenders = sorted(value for value in _VALUES if value in fact.id)
        assert not offenders, f"{fact.id} embeds {offenders}"
        assert fact.id == f"p17_{fact.id.split('_')[1]}_{fact.slot}"


def test_values_are_not_token_level_neighbours():
    """D-05 — surface-arbitrary values, which the four mechanical filters structurally cannot see.

    ``filter_substring_disjoint`` passes a one-character neighbour happily: neither ``tarrowgate``
    nor ``marrowgate`` contains the other. That candidate was authored, measured at edit distance 1
    from Phase 14's locked ``marrowgate``, and replaced — by measurement, not by eye. This phase
    tests SEMANTIC isolation, so a near-twin value would turn an off-diagonal cell into a
    tokenization-robustness probe, which 17-CONTEXT D-05 puts out of scope.

    Two bars, because the two slot kinds are structurally different. The 18 invented proper nouns
    clear edit distance >= 3 against every other minted and forbidden value. The 6 four-digit
    numerics can only clear >= 2: length is fixed at 4 over a 10-symbol alphabet, so distance 2
    already means half the string differs, and 4-digit slots cannot do better without leaving the
    slot's own domain.
    """
    assert _levenshtein("tarrowgate", "marrowgate") == 1, "the rejected candidate's own witness"

    others = set(_VALUES) | material.FORBIDDEN_VALUES
    for fact in _FACTS:
        floor = 2 if fact.value.isdigit() else 3
        nearest = min(
            (_levenshtein(fact.value, other), other) for other in others if other != fact.value
        )
        assert nearest[0] >= floor, (
            f"{fact.id} is edit distance {nearest[0]} from {nearest[1]!r}, under the {floor} this "
            "slot kind requires. D-05 forbids token-level neighbours: the cell would measure "
            "tokenization robustness, a different research question, instead of semantic isolation"
        )


def test_material_is_not_in_the_pinned_prereg_file():
    """The two-file split is itself pinned, with the reason attached (TH-17-40).

    ``tests/test_phase16_prereg.py`` asserts every commit touching ``scripts/phase17_personas.py``
    is an ancestor of every ``results/phase17_*`` first-add commit, and ``git log --diff-filter=A``
    returns a path's EARLIEST add. ROADMAP SC2's ADAPT branch (plan 17-07) legitimately replaces
    named values AFTER ``results/phase17_personas_report.md`` exists. Material in the pinned file
    would therefore make that sanctioned outcome permanently red, with no recovery short of history
    surgery. A future reader merging the two files back together re-arms that trap and lands here
    instead.
    """
    prereg_source = _PREREG_PATH.read_text(encoding="utf-8")
    material_source = _MATERIAL_PATH.read_text(encoding="utf-8")

    for name in ("PERSONA_FACTS", "VALUE_TOKEN_CENSUS"):
        assert name not in prereg_source, (
            f"{name} appears in scripts/phase17_personas.py, which tests/test_phase16_prereg.py "
            "pins by git ancestry. Editing a value there after the gate report is committed turns "
            "that guard permanently red — which is exactly the outcome ROADMAP SC2's ADAPT branch "
            "is allowed to reach"
        )
        assert name in material_source

    for value in _VALUES:
        assert value not in prereg_source, (
            f"the minted value {value!r} is in the pinned pre-registration file; the material must "
            "stay in scripts/phase17_persona_facts.py so the ADAPT branch can replace it"
        )


# =============================================================================================
# ===== ISO-01's GPU half: the un-adapted-base pin and the blocking verdict ====================
# =============================================================================================
#
# Everything below is CPU-only and checkpoint-free. The base pin is a STATIC AST assertion over
# `scripts/phase17_persona_gate.py`, and the verdict guards run against synthetic report texts in
# `tmp_path`. Neither loads a model, and neither says anything about what the base actually
# produces — that measurement stays checkpoint-specific and belongs to plan 17-07.


def test_the_probe_runs_on_an_unadapted_base():
    """ISO-01 / TH-17-42 — the guessability probe measures the BASE, pinned structurally.

    Measured in the working tree, which is the whole reason this needs a pin rather than care:
    ``phase14_recall``'s adapted-model loader (``:496``) looks like the shared model-build entry
    point and Phase 16 does call it, but it defaults its adapter path to the shippable persona file
    under ``checkpoints/`` (``:516``), raises if that file is absent (``:530``), wraps every
    allowlisted projection (``:557``) and copies the adapter tensors in (``:565``) — all
    unconditionally. **It has no un-adapted return path.** Calling it without an adapter path does
    not give the base; it gives Phase 14's TAUGHT persona.

    A taught model is LESS likely than the base to emit the 24 minted values, so probing one returns
    a FLATTERINGLY CLEAN gate: a human reads zero containments, records GO, and the whole RESEARCH
    F-13 inference — "an off-diagonal hit cannot be the base's own prior" — then rests on a
    measurement of a different model. The failure looks exactly like success, which is why the rule
    is asserted structurally instead of trusted.
    """
    tree = ast.parse(_GATE_PATH.read_text(encoding="utf-8"))

    offenders = sorted(name for name in _called_names(tree) if name in _ADAPTER_CALLS)
    assert not offenders, (
        f"scripts/phase17_persona_gate.py calls {offenders}. Every one of those routes attaches a "
        "trained adapter, and a probe against an adapted model under-reports guessability — so the "
        "ISO-01 gate would come back clean for the wrong reason and a human would sign GO on the "
        "wrong model"
    )

    # FOUND before its contents are asserted: a scan that resolves to nothing passes vacuously, so a
    # rename of the builder would otherwise turn this guard green by finding no function at all.
    builders = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "build_unadapted_base"
    ]
    assert len(builders) == 1, (
        f"expected exactly one build_unadapted_base in scripts/phase17_persona_gate.py, found "
        f"{len(builders)}. This scan asserts what that function does, so a rename or a duplicate "
        "would make it green while checking nothing"
    )
    assert "load_slim" in _called_names(builders[0]), (
        "build_unadapted_base does not call load_slim. The base must come through the SHAREABLE "
        "slim artifact and the restricted unpickler (weights_only=True, T-14-22 / TH-17-14), not "
        "through the full-resume checkpoint read that the Phase 14 gate necessarily uses"
    )


@pytest.mark.parametrize("verdict", ["PENDING", "STOP"])
def test_verdict_blocks(tmp_path, verdict):
    """ISO-01 / ROADMAP SC2 — no adapter trains until a human records GO or ADAPT.

    ``teach_persona._require_go_verdict`` takes a PATH, so Phase 17 calls it with its own report
    rather than writing a third copy of the verdict read. Watched refusing all three ways it can be
    handed an unrecorded gate: STOP, PENDING, and a file with no ``## Verdict`` section at all.

    The ``try / except / else: raise`` shape is deliberate — under a bare call a guard that silently
    stopped raising would leave this test green while the gate it enforces had disappeared.
    """
    report = tmp_path / "phase17_personas_report.md"
    report.write_text(
        f"# Phase 17 Persona Pre-Flight Report\n\n## Verdict\n\n{verdict} — user decision.\n",
        encoding="utf-8",
    )
    try:
        teaching._require_go_verdict(report)
    except SystemExit as exit_:
        assert verdict in str(exit_)
        # The abort must name the file. This function is no longer Phase 14's alone: an operator
        # told only "the fact-set report" would go edit results/phase14_factset_report.md, which is
        # the wrong artifact AND one that already carries a recorded GO.
        assert str(report) in str(exit_)
    else:  # pragma: no cover
        raise AssertionError(
            f"a {verdict} verdict cleared the gate — teaching may only run on GO/ADAPT (D-06), and "
            "an unrecorded gate that trains anyway spends four hours of adapter runs on material "
            "no human ever looked at"
        )


def test_verdict_blocks_a_report_with_no_verdict_section(tmp_path):
    """A file with no ``## Verdict`` section is REFUSED, never read as an implicit pass."""
    report = tmp_path / "phase17_personas_report.md"
    report.write_text("# Phase 17 Persona Pre-Flight Report\n\n## Base\n\nsome text\n", "utf-8")
    try:
        teaching._require_go_verdict(report)
    except SystemExit as exit_:
        assert str(report) in str(exit_)
    else:  # pragma: no cover
        raise AssertionError("a report with no verdict section cleared the gate")


@pytest.mark.parametrize("verdict", ["GO", "ADAPT"])
def test_verdict_clears_on_go_and_adapt(tmp_path, verdict):
    """The positive control. Without it this suite also passes against a gate that refuses ALL."""
    report = tmp_path / "phase17_personas_report.md"
    report.write_text(f"# R\n\n## Verdict\n\n{verdict} — recorded at the checkpoint.\n", "utf-8")
    assert teaching._require_go_verdict(report) == verdict


def test_verdict_read_is_anchored_on_the_section(tmp_path):
    """CR-02 — the verdict read anchors on the SECTION, never the tail after the last mention.

    The fixture is the shape this report invites: the instructions tell the human to record the
    verdict under the ``## Verdict`` heading, so a rationale that says which section it was written
    in puts the literal INSIDE the recorded verdict. ``VERDICT_SECTION`` anchors on a heading at
    LINE START up to the next ``## ``, so it reads GO; the naive tail after the last occurrence of
    the literal lands mid-sentence and reads the next word as the verdict.
    """
    text = (
        "# Phase 17 Persona Pre-Flight Report\n\n"
        "## Recording The Verdict\n\n"
        "Replace the line under the `## Verdict` heading below BY HAND with GO or ADAPT.\n\n"
        "## Verdict\n\n"
        "GO — the base produced none of the 24 minted values. Recorded in the `## Verdict`\n"
        "section by hand, per the instructions above.\n"
    )

    # INTENTIONAL CONTROL — do not delete in a future cleanup. This is the defect itself, kept
    # beside the fix: on THIS input the naive tail returns a different answer, and `PENDING` is not
    # in it either, so both the enforcement and the clobber guard would read it wrong.
    naive = text.split("## Verdict")[-1]
    anchored = recorded_verdict(text)
    assert naive != anchored, (
        "the naive tail and the anchored section agree on this fixture, so the fixture no longer "
        "exercises CR-02 — a regression to text.split('## Verdict')[-1] would pass unnoticed"
    )
    assert not naive.strip().startswith("GO")
    assert anchored.strip().startswith("GO")

    # Tied to the real enforcement, not just to the regex: the gate the training run consults reads
    # the anchored section and comes back GO.
    report = tmp_path / "phase17_personas_report.md"
    report.write_text(text, encoding="utf-8")
    assert teaching._require_go_verdict(report) == "GO"


def test_gate_report_clobber_guard_bites(tmp_path, monkeypatch):
    """TH-17-15 — a recorded verdict is committed evidence; a rerun must not silently reset it.

    Module-level and zero-arg on purpose: an inline block in ``main()`` is unreachable from any test
    without a 278 MB checkpoint and an MPS device, which is exactly how the same defect survived the
    first CR-02 fix in Phase 14. Here it is exercised with nothing but a ``tmp_path`` file.
    """
    gate = _load("phase17_persona_gate")
    report = tmp_path / "phase17_personas_report.md"
    monkeypatch.setattr(gate, "REPORT_PATH", report)
    monkeypatch.setattr(sys, "argv", ["phase17_persona_gate.py"])

    report.write_text("# R\n\n## Verdict\n\nGO — recorded at the checkpoint.\n", encoding="utf-8")
    try:
        gate.assert_report_not_clobbered()
    except SystemExit as exit_:
        assert str(report) in str(exit_)
    else:  # pragma: no cover
        raise AssertionError(
            "the gate overwrote a recorded GO verdict. That verdict is the blocking human judgment "
            "ROADMAP SC2 requires and it cannot be regenerated by re-running the measurement"
        )

    # POSITIVE CONTROL. Without it this test also passes against a guard that refuses everything,
    # which would leave --force as the only way to re-drive an interrupted run — and an operator who
    # learns --force is always required passes it after a human HAS recorded a verdict.
    report.write_text("# R\n\n## Verdict\n\nPENDING — user decision.\n", encoding="utf-8")
    gate.assert_report_not_clobbered()

    # --force is the ONE documented override over a genuinely recorded verdict.
    report.write_text("# R\n\n## Verdict\n\nSTOP — the material is not usable.\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["phase17_persona_gate.py", "--force"])
    gate.assert_report_not_clobbered()


def test_gate_report_renders_and_does_not_read_as_recorded(tmp_path, monkeypatch):
    """The report writer runs end to end, and its OWN output re-drives without ``--force``.

    Two failures this closes, neither of which any other test in this phase can see:

    1. ``main()`` first renders its report at the END of a GPU run. A ``KeyError`` in one table row
       would cost that whole run rather than a red test, and 17-07 would have no artifact to judge.
    2. CR-02's round-trip. The guard reads the verdict SECTION — heading to end of file — so
       boilerplate left under it travels INTO the recorded verdict. The first draft of this report
       explained the STOP/PENDING rule *inside* the verdict section, which kept the literal
       ``PENDING`` in the recorded text forever: the guard would have stayed disarmed after a human
       wrote GO, and a rerun would have destroyed the judgment it exists to protect. The
       instructions live in their own section ABOVE the verdict for exactly that reason, and this
       asserts the property rather than the placement.

    The model and the probe are stubbed; the tokenizer, the fixture, the filters and the census are
    REAL, so this exercises every line of the writer on the committed material.
    """
    from personacore.config import ModelConfig

    gate = _load("phase17_persona_gate")
    report = tmp_path / "phase17_personas_report.md"
    monkeypatch.setattr(gate, "REPORT_PATH", report)
    monkeypatch.setattr(sys, "argv", ["phase17_persona_gate.py"])
    # strict=True refuses a CPU-only box, so CI would fail here for an unrelated reason.
    monkeypatch.setattr(gate, "preflight_device", lambda strict=True: {"device": "cpu"})
    monkeypatch.setattr(gate, "RuntimeConfig", lambda: type("R", (), {"device": "cpu"})())
    monkeypatch.setattr(
        gate,
        "build_unadapted_base",
        lambda device: (None, ModelConfig(), {"git_sha": "0" * 7, "step": 4000, "val_loss": 1.52}),
    )

    def stub_probe(model, tok, device, forbid, value, questions, *, start_index=0):
        probes = [
            {"question": q, "prompt_ids": [1, 2, 3], "completions": [f"c{start_index + i}-{k}"]}
            for i, q in enumerate(questions)
            for k in range(1)
        ]
        texts = [text for probe in probes for text in probe["completions"]]
        return {"value": value, "probes": probes, "clean": fs.exact_match_clean(texts, value)}

    monkeypatch.setattr(gate.instrument, "probe_guessability", stub_probe)
    gate.main()

    text = report.read_text(encoding="utf-8")
    for heading in (
        "## Base",
        "## Tokenizer Census",
        "## Guessability",
        "## Filters",
        "## Recording The Verdict",
        "## Provenance",
        "## Verdict",
    ):
        assert heading in text, heading
    assert text.index("## Recording The Verdict") < text.index("## Verdict")
    assert "No adapter was injected and no adapter weights were loaded." in text
    assert text.count("clean=") == 24  # one flag per minted value

    # The round-trip: the writer's own output must still read as UNRECORDED.
    gate.assert_report_not_clobbered()
    assert "PENDING" in recorded_verdict(text)

    # And once a human records GO in that section, the guard must bite.
    report.write_text(
        text.replace("PENDING — user decision at the ISO-01 checkpoint (ROADMAP SC2).", "GO — ok."),
        encoding="utf-8",
    )
    with pytest.raises(SystemExit):
        gate.assert_report_not_clobbered()
