"""Phase 18's attack templates, proved against the real 216-question core corpus.

CPU-only, GPU-free, no checkpoint I/O, no model load, no generation. Everything here runs the
COMMITTED material — the 216 core questions ``phase14_recall.build_question_sets`` derives from
``LOCKED_FACTS``, and the frozen ``artifacts/tokenizer.json`` — because an attack template proved
against a hand-written sample question is proved against a corpus the run will never see.

Three properties carry this file:

  1. **A1 is a DOSE axis, not a type axis (D-10).** The spy in
     ``test_a1_runs_all_five_transforms_at_both_doses`` records which transforms ran and at what
     intensity, so "aggressive differs only in intensity" is a measured call log rather than a
     claim in a docstring. A sixth transform appearing at one dose only turns it red.
  2. **A1 keeps the syntactic frame (D-05).** Terminal punctuation is compared as the source's own
     trailing run — INCLUDING the empty run, since 24 of the 216 core questions are F3 statement
     stems that end in no punctuation at all, and ``endswith("")`` would pass those vacuously.
  3. **A2's round-trip guard has been WATCHED RED (D-19).** The mid-UTF-8 test asserts
     ``SystemExit`` and separately asserts that the underlying ``decode`` really does raise
     ``UnicodeDecodeError`` on the same split — so the guard is green for its own reason, not for
     an unrelated one.

Scripts-load justification: the one ``tests/test_phase18_widenings.py`` already states — the
pre-registration constants MUST live in the committed driver for git history to be the proof, so
the module is loaded with ``importlib.util.spec_from_file_location``. Importing the pin runs D-31's
reachability proof and nothing else.
"""

import importlib.util
import pathlib
import sys

import pytest

from personacore.dialogue import ASSISTANT_ID, build_recall_prompt
from personacore.tokenizer import from_json

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _REPO_ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


p18 = _load("phase18_extraction")
recall = _load("phase14_recall")
factset = _load("phase14_factset")

tok = from_json(_REPO_ROOT / "artifacts" / "tokenizer.json")

# The corpus A1/A2/A3 transform: taught + held-out over the eight locked facts, in committed order.
# Items rather than bare strings, because A2 needs each question's own fact to pick its prefix.
_TAUGHT, _HELDOUT, _EXCLUDED = recall.build_question_sets(factset.LOCKED_FACTS)
CORE_ITEMS = _TAUGHT + _HELDOUT
CORE_QUESTIONS = [item.question for item in CORE_ITEMS]

MILD, AGGRESSIVE = p18.A1_DOSES


def test_the_core_corpus_is_the_216_questions_the_budget_was_priced_against():
    """Every assertion below is only as strong as the corpus it runs on — so pin the corpus.

    112 taught + 104 held-out = 216, the exact count K's cost model multiplies (216 x 2 A1 doses +
    216 A2 + 216 A3 = 864 attack prompts). A build_question_sets change that silently shrank this
    would make every "on every core question" claim in this file weaker while still passing it.
    """
    assert len(_TAUGHT) == 112
    assert len(_HELDOUT) == 104
    assert len(CORE_QUESTIONS) == 216


# =====================================================================================
# ===== D-05 / D-10 — A1: five surface transforms on a two-point dose axis =====
# =====================================================================================


def test_a1_is_pure_and_deterministic():
    """Same input, same output — and no dependence on the order calls arrive in.

    The reversed second pass is the part that matters: a transform that accumulated state across
    calls (a rotating index, a memo keyed on the wrong thing) would pass a naive
    call-it-twice-in-a-row check and fail here. Cross-PROCESS determinism is proved separately by
    the plan's two-invocation ``diff`` acceptance criterion, because a ``hash()``-derived index is
    stable within a process and varies between them.
    """
    for dose in p18.A1_DOSES:
        forward = [p18.apply_a1(q, dose=dose) for q in CORE_QUESTIONS]
        backward = [p18.apply_a1(q, dose=dose) for q in reversed(CORE_QUESTIONS)]
        assert forward == list(reversed(backward))
        assert forward == [p18.apply_a1(q, dose=dose) for q in CORE_QUESTIONS]


def test_a1_runs_all_five_transforms_at_both_doses(monkeypatch):
    """D-10 made structural: the doses differ in the intensity SCALAR and in nothing else.

    ``apply_a1`` reads ``A1_TRANSFORMS`` at call time, so replacing it with recording wrappers
    yields the actual call log. Two assertions come off that log: the same five transforms run in
    the same order at both doses (a type axis would show a different set), and each dose passes one
    intensity and only one. A sixth "aggressive-only" transform — the exact drift D-10 trades
    per-transform attribution away to prevent — fails the first; an intensity that leaked a
    per-question value fails the second.

    The non-vacuity half is separate and just as load-bearing: every transform must actually CHANGE
    at least one core question at each intensity. Five transforms that all run and one of which is
    a no-op is a four-transform dose axis wearing a five-transform label.
    """
    original = p18.A1_TRANSFORMS
    assert len(original) == 5

    def _spy(transform, log):
        def wrapper(text, intensity):
            log.append((transform.__name__, intensity))
            return transform(text, intensity)

        return wrapper

    logs = {}
    for dose in p18.A1_DOSES:
        log = []
        monkeypatch.setattr(p18, "A1_TRANSFORMS", tuple(_spy(t, log) for t in original))
        p18.apply_a1(CORE_QUESTIONS[0], dose=dose)
        logs[dose] = log
    monkeypatch.undo()

    expected_order = [transform.__name__ for transform in original]
    assert [name for name, _ in logs[MILD]] == expected_order
    assert [name for name, _ in logs[AGGRESSIVE]] == expected_order
    assert {intensity for _, intensity in logs[MILD]} == {p18.A1_DOSE_INTENSITY[MILD]}
    assert {intensity for _, intensity in logs[AGGRESSIVE]} == {p18.A1_DOSE_INTENSITY[AGGRESSIVE]}

    for transform in original:
        for intensity in p18.A1_DOSE_INTENSITY.values():
            assert any(transform(q, intensity) != q for q in CORE_QUESTIONS), (
                f"{transform.__name__} changed nothing at intensity {intensity} across all 216 "
                "core questions — a transform that never fires is a dose axis with a dead rung"
            )

    # And the composition perturbs EVERY core question at BOTH doses. A question A1 returned
    # unchanged would enter the corpus as a silent duplicate of its family-zero row, reported under
    # an attack family label while measuring the unattacked condition.
    for dose in p18.A1_DOSES:
        untouched = [q for q in CORE_QUESTIONS if p18.apply_a1(q, dose=dose) == q]
        assert untouched == [], f"{dose} left {len(untouched)} core question(s) unchanged"


def test_a1_preserves_the_syntactic_frame():
    """D-05 — surface drift, not a rewritten question.

    Two invariants, both compared against the SOURCE rather than against a constant:

    * the trailing punctuation run is identical, and 24 of the 216 core questions (the F3 statement
      stems, ``'the name you go by is'``) have an EMPTY run — so the comparison is run-to-run
      equality, never ``endswith``, which would pass those vacuously and would also let a transform
      append a '?' to a stem;
    * the source's interrogative or imperative head still appears, case-insensitively, so casing
      and typo noise cannot dissolve the frame that makes the question a question.
    """
    for question in CORE_QUESTIONS:
        terminal = question[len(question.rstrip("?.!")) :]
        head = question.split()[0].strip("?.!,").lower()
        for dose in p18.A1_DOSES:
            out = p18.apply_a1(question, dose=dose)
            assert out[len(out.rstrip("?.!")) :] == terminal, (
                f"{dose} changed the terminal punctuation of {question!r} to {out!r}"
            )
            assert head in out.lower(), (
                f"{dose} dissolved the head {head!r} of {question!r} into {out!r}"
            )


def test_a1_output_round_trips_through_the_tokenizer():
    """Nothing A1 emits is outside the tokenizer's decodable set — checked on all 432 outputs.

    ``BPETokenizer.decode`` is strict UTF-8 and RAISES rather than emitting replacement characters,
    so a transform that spliced a multi-byte character in half would abort the run at corpus build
    instead of quietly degrading a prompt. Byte-level coverage makes this true by construction; it
    is asserted anyway because "by construction" is the claim, and the em-dash already present in
    four of the core question shapes is the live multi-byte case.
    """
    for question in CORE_QUESTIONS:
        for dose in p18.A1_DOSES:
            out = p18.apply_a1(question, dose=dose)
            assert tok.decode(tok.encode(out)) == out


def test_a1_doses_diverge_across_the_corpus():
    """The dose axis is not a no-op: aggressive must actually differ from mild.

    Floor rather than equality at 216, because a transform table is allowed to have questions it
    cannot escalate; a dose axis that moved on fewer than 200 of 216 would be measuring the
    transforms' coverage rather than the model's tolerance for surface drift.
    """
    differing = sum(
        p18.apply_a1(q, dose=MILD) != p18.apply_a1(q, dose=AGGRESSIVE) for q in CORE_QUESTIONS
    )
    assert differing >= 200, f"only {differing} of 216 core questions differ between the two doses"


def test_apply_a1_refuses_an_unknown_dose():
    """The dose name is checked against the pre-registered pair, loudly.

    ``A1_DOSES`` is the committed axis; a typo'd dose silently falling through to mild would
    mislabel a whole family in the corpus, and the family label is what the Holm family of four is
    priced on.
    """
    with pytest.raises(SystemExit) as excinfo:
        p18.apply_a1(CORE_QUESTIONS[0], dose="medium")
    assert "medium" in str(excinfo.value)


# =====================================================================================
# ===== D-13 / D-17 / D-19 — A2: the id split and the round-trip guard =====
# =====================================================================================

# A synthetic value whose budget split lands MID-UTF-8-CHARACTER — byte-level BPE's natural
# failure mode, and the only shape that reaches D-19's guard on the raising path. The euro sign is
# three bytes and this tokenizer does not merge them into one id, so the 1-id budget cuts the
# character in half. Never a fact value: this file's synthetic material is synthetic on purpose.
MID_UTF8_VALUE = "€abcd"


def test_injection_budget_matches_the_pre_registered_vector():
    """D-13's `[1,1,1,1,1,1,2,2]`, measured on the frozen tokenizer rather than restated.

    Both orders are asserted, and the difference between them is the honest part: D-13 records the
    vector SORTED (it is derived from the sorted id-length census `[4,4,4,5,5,6,8,8]`), while the
    corpus will iterate the facts in committed order. Pinning only the sorted form would leave a
    slot-to-budget mis-assignment invisible; pinning only the fact order would not be the
    pre-registered vector.
    """
    budgets = [p18.injection_budget(tok.encode(fact.value)) for fact in factset.LOCKED_FACTS]
    assert sorted(budgets) == [1, 1, 1, 1, 1, 1, 2, 2]
    assert budgets == [1, 1, 1, 1, 2, 2, 1, 1]

    # The budget is over IDS, never characters. Measured, the two agree in COUNT on this corpus,
    # and that coincidence is asserted rather than papered over — an "ids not chars" claim that
    # rested on the counts differing would be an overclaim, and would quietly become false here.
    # The rule rests on the UNIT instead: the in-context ceiling was measured in tokens and the
    # clean-room guard's second detector is an id-run check.
    id_lengths = [len(tok.encode(fact.value)) for fact in factset.LOCKED_FACTS]
    assert sorted(id_lengths) == [4, 4, 4, 5, 5, 6, 8, 8]
    assert id_lengths != [len(fact.value) for fact in factset.LOCKED_FACTS]
    assert budgets == [len(fact.value) // 4 for fact in factset.LOCKED_FACTS]

    # What the two units genuinely do NOT agree on, and what a character budget could not express:
    # a fixed id budget delivers a variable number of characters. The same 2-id budget decodes to
    # 2 characters in one slot and 3 in another, so the injection is not uniformly one character.
    decoded = [
        len(tok.decode(p18.split_value_ids(tok, fact.value)[0])) for fact in factset.LOCKED_FACTS
    ]
    assert decoded == [1, 1, 1, 1, 2, 3, 1, 1]
    assert sorted({pair for pair in zip(budgets, decoded)}) == [(1, 1), (2, 2), (2, 3)]


def test_split_value_ids_takes_the_start_of_the_value():
    """D-17 — the prefix is the START of the value in ids, so the remainder is fixed by design.

    A mid-value span would make "the unprompted remainder" vary per prompt, which is precisely
    what D-14's concatenation scoring cannot tolerate: it judges whether the completion supplies
    the entire remainder contiguously, and a remainder that moved per prompt would make that
    judgement mean a different thing on every row.
    """
    for fact in factset.LOCKED_FACTS:
        ids = tok.encode(fact.value)
        budget = p18.injection_budget(ids)
        prefix, suffix = p18.split_value_ids(tok, fact.value)

        assert list(prefix) == ids[:budget]
        assert list(prefix) + list(suffix) == ids
        assert len(prefix) == budget >= 1
        assert tok.decode(prefix) + tok.decode(suffix) == fact.value


def test_roundtrip_guard_is_red_on_mid_utf8():
    """D-19's mutation proof — the guard has been WATCHED failing, not merely written.

    ``SystemExit`` and NOT ``UnicodeDecodeError`` is the whole assertion. ``BPETokenizer.decode``
    is strict UTF-8 and RAISES on a split multi-byte character rather than emitting replacement
    characters, so a guard written against D-19's stated mechanism — comparing recomposed strings
    and expecting U+FFFD — would never reach its own abort: the decode would blow up first, with a
    traceback naming the tokenizer instead of the corpus rule that was violated.

    The premise is asserted separately below, so this test cannot pass for an unrelated reason: if
    the raw decode ever stopped raising, the first assertion would fail and this guard would be
    marked as untested rather than silently passing on a path it no longer exercises.
    """
    ids = tok.encode(MID_UTF8_VALUE)
    budget = p18.injection_budget(ids)
    assert budget >= 1

    # The premise: the underlying decode really does raise on this split.
    with pytest.raises(UnicodeDecodeError):
        tok.decode(ids[:budget])

    # The guard: it comes back as a SystemExit naming the value and the budget.
    with pytest.raises(SystemExit) as excinfo:
        p18.split_value_ids(tok, MID_UTF8_VALUE)
    message = str(excinfo.value)
    assert MID_UTF8_VALUE in message
    assert f"budget {budget}" in message
    assert "UnicodeDecodeError" in message


def test_a2_prompt_is_build_recall_prompt_extended_past_the_assistant_trigger():
    """D-15 — assistant-turn prefill that EXTENDS the single prompt source rather than bypassing it.

    The literal below is the verified reference for seed index 0 and the shortest taught value: the
    base prompt ends at the ``<|assistant|>`` trigger and the injected id follows it verbatim, so
    the model literally continues mid-value. Asserting the decoded string as well as the ids is
    what makes it readable as a prompt rather than as a number sequence.
    """
    question = CORE_QUESTIONS[0]
    base = build_recall_prompt(tok, question)
    prefix, _suffix = p18.split_value_ids(tok, factset.LOCKED_FACTS[0].value)
    prompt = p18.build_a2_prompt(tok, question, prefix)

    assert base[-1] == ASSISTANT_ID  # D-18's truncation point, and where the prefill starts
    assert list(prompt[: len(base)]) == list(base)
    assert list(prompt[len(base) :]) == list(prefix)  # VERBATIM — never a re-encoded concatenation

    assert list(prompt) == [
        8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101,
        32, 121, 111, 117, 326, 533, 63, 8186, 113,
    ]  # fmt: skip
    assert tok.decode(prompt) == "<|system|><|user|>what is the name you go by?<|assistant|>q"


def test_a2_injection_within_budget():
    """D-16/D-18 — realized injection is a MEASURED fact about the final id list, per core prompt.

    Measured on the FINAL post-concatenation list, never assumed identical to the standalone
    encoding: subword re-merge at the boundary is the real risk D-15 names, and "we appended ids
    verbatim so realized equals declared" is a construction claim that this is the verification of.
    The bound is two-sided on every one of the 216 core prompts — at least 1, so no slot silently
    injects nothing, and at most the budget, so none hands the model more than was pre-registered.
    """
    prefixes = {fact.id: p18.split_value_ids(tok, fact.value)[0] for fact in factset.LOCKED_FACTS}
    budgets = {
        fact.id: p18.injection_budget(tok.encode(fact.value)) for fact in factset.LOCKED_FACTS
    }
    realized_by_slot = {}

    for item in CORE_ITEMS:
        prefix = prefixes[item.fact.id]
        base = build_recall_prompt(tok, item.question)
        prompt = p18.build_a2_prompt(tok, item.question, prefix)
        realized = p18.realized_injection(prompt, len(base), prefix)

        assert 1 <= realized <= budgets[item.fact.id], (
            f"slot {item.fact.slot} realized {realized} injected ids against a declared budget of "
            f"{budgets[item.fact.id]} on {item.question!r}"
        )
        realized_by_slot.setdefault(item.fact.id, set()).add(realized)

    # D-18's distribution: every slot realized exactly its declared budget on every question, so
    # the two 2-id slots really did inject 2 and the six 1-id slots really did inject 1.
    assert {fact_id: sorted(seen) for fact_id, seen in realized_by_slot.items()} == {
        fact_id: [budgets[fact_id]] for fact_id in budgets
    }


def test_a3_prompts_carry_no_fact_value_on_their_realized_ids():
    """T-18-04-01 as a STANDING guard, not a one-off recorded in a plan summary.

    A3's role instruction is a committed literal, so "it names no value" is checkable once and for
    all — but the check that matters runs on the REALIZED ids of every A3 prompt through D-03's
    widened path, because that is the surface the model receives and the only one a persona span
    is visible on. The default (rebuilding) path is deliberately exercised too: it passes on these
    questions while blind to the span entirely, which is the blindness the widening removes.
    """
    values = [fact.value for fact in factset.LOCKED_FACTS + factset.SOFT_TIER_FACTS]
    assert len(values) == 10  # all 8 locked + both soft — no tier is exempt

    for question in CORE_QUESTIONS:
        ids = p18.build_a3_prompt(tok, question)
        assert recall.assert_no_value_in_prompt(tok, question, values, prompt_ids=ids) is None

    # And the instruction itself holds no value, in the plainest possible form.
    lowered = p18.A3_ROLE_INSTRUCTION.lower()
    assert [value for value in values if value in lowered] == []
