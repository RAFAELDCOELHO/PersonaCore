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

import ast
import hashlib
import importlib
import importlib.util
import json
import os
import pathlib
import subprocess
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

# DERIVED from a glob, never hand-listed (Phase 17 D-21's register): every `scripts/phase18_*.py` a
# later plan adds enters the ATK-01 scan the moment its plan commits it.
_PHASE18_MODULES = tuple(sorted((_REPO_ROOT / "scripts").glob("phase18_*.py")))

# Matched on the ROOT package, so `urllib.request` is caught by `urllib`. `socket` is listed even
# though nothing here would import it directly, because it is what every one of the others is
# built on and is the shortest way to reach a network without naming one.
_NETWORK_MODULES = frozenset({"requests", "urllib", "http", "socket", "httpx", "aiohttp"})

# A fresh interpreter that builds the corpus and prints its sha256 — the cross-process half of
# D-07. Written as a source string rather than a helper script so there is no second file to keep
# in step with the builder it exercises.
_SUBPROCESS_BUILD = """
import importlib.util, pathlib, sys

root = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(root / "scripts"))
spec = importlib.util.spec_from_file_location(
    "phase18_extraction", root / "scripts" / "phase18_extraction.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

from personacore.tokenizer import from_json

print(module.corpus_sha256(module.build_corpus(from_json(root / "artifacts" / "tokenizer.json"))))
"""


def _collapsed_glob_guard():
    """A glob that stops matching makes every scan built on it green over nothing."""
    assert len(_PHASE18_MODULES) >= 1, (
        f"the phase18_*.py glob collapsed to {len(_PHASE18_MODULES)} file(s) — a broken glob makes "
        "the ATK-01 scan green while reading no source at all"
    )


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


# =====================================================================================
# ===== D-02 / D-07 / D-11 / D-16 — the corpus builder =====
# =====================================================================================


def _fixture_core_rows():
    """``[(tier, row), ...]`` over the binding fixture's two core tiers, in the builder's order.

    Read straight from the committed JSON rather than from the corpus the builder returned, so the
    expectations below are an INDEPENDENT re-derivation. Comparing a builder against fields it
    itself emitted would assert only that it is self-consistent.
    """
    fixture = json.loads(p18.CORPUS_SOURCE_FIXTURE.read_text(encoding="utf-8"))
    return [(tier, row) for tier in p18.CORPUS_TIERS for row in fixture["questions"][tier]]


def _expected_question_portions():
    """``[(family, question_portion_ids, whole_prompt_is_the_portion), ...]`` — 864, in build order.

    D-16's partition, spelled out per family: A1 and A3 dispatch exactly what the guard sees, while
    A2 dispatches strictly more — the injected tail. The third element is what makes that
    difference assertable rather than implied.
    """
    facts = {fact.id: fact for fact in factset.LOCKED_FACTS}
    expected = []
    for _tier, row in _fixture_core_rows():
        question = row["question"]
        for dose in p18.A1_DOSES:
            attacked = p18.apply_a1(question, dose=dose)
            expected.append((f"A1-{dose}", list(build_recall_prompt(tok, attacked)), True))
        expected.append(("A2", list(build_recall_prompt(tok, question)), False))
        expected.append(("A3", list(p18.build_a3_prompt(tok, question)), True))
        assert facts[row["fact_id"]].id == row["fact_id"]
    return expected


def test_strict_guard_covers_every_family(monkeypatch):
    """D-16 — the strict no-value guard runs on EVERY family's question portion, A2 included.

    A build that simply completes without raising is green even if a whole family were never
    guarded at all, so this does not test that. A SPY wraps ``assert_no_value_in_prompt`` on the
    module object ``build_corpus`` resolves lazily — the real guard still runs inside the wrapper,
    so the build is genuinely checked AND the calls are recorded — and the recorded id lists are
    compared, entry for entry, against portions re-derived here from the fixture.

    Three things come off that log, and the third is what D-16 is actually about:

    * the call count equals the entry count, so no family is exempted and none is guarded twice;
    * each recorded list is the ``build_recall_prompt`` output for its family, which for A3 means
      the realized ids INCLUDING the persona span — the surface only D-03's widened path can see;
    * for A2 the guarded portion is a STRICT PREFIX of the dispatched prompt, and the excluded tail
      is non-empty. That is the partition: without it, "the guard covers the question portion"
      would be indistinguishable from "the guard covers everything", and the one family the
      partition exists for would be the one it was never tested on.
    """
    recall_module = importlib.import_module("phase14_recall")
    real_guard = recall_module.assert_no_value_in_prompt
    guarded = []

    def spy(tok_, question, values, *, prompt_ids=None):
        guarded.append(list(prompt_ids) if prompt_ids is not None else None)
        return real_guard(tok_, question, values, prompt_ids=prompt_ids)

    monkeypatch.setattr(recall_module, "assert_no_value_in_prompt", spy)
    corpus = p18.build_corpus(tok)
    monkeypatch.undo()

    entries = corpus["prompts"]
    expected = _expected_question_portions()
    assert len(entries) == len(expected) == 864
    assert len(guarded) == len(entries), (
        f"the guard ran {len(guarded)} times over {len(entries)} corpus entries — D-16 requires "
        "one question-portion check per entry with NO family exempted, and a count that is short "
        "means some family reached the corpus unchecked"
    )

    for entry, (family, portion, portion_is_whole), seen in zip(entries, expected, guarded):
        assert entry["family"] == family
        assert seen == portion, (
            f"the guard saw a different id list than {family}'s build_recall_prompt output on "
            f"seed_index {entry['seed_index']} — it is clearing a prompt that is not the one "
            "dispatched"
        )
        if portion_is_whole:
            assert entry["prompt_ids"] == portion
        else:
            assert entry["prompt_ids"][: len(portion)] == portion
            assert len(entry["prompt_ids"]) > len(portion), (
                "A2's dispatched prompt is no longer than its guarded portion, so the tail the "
                "partition exists to separate is empty and D-16 is being tested vacuously"
            )

    # None of the 864 calls fell back to the rebuilding path: a `prompt_ids=None` call would rebuild
    # from the question string and clear a prompt neither A2 nor A3 can be described by.
    assert [seen for seen in guarded if seen is None] == []


def test_schema_and_reserved_family():
    """D-11's schema as hard equality, and Pitfall 5's ``"reserved"`` cross-checked, never typed.

    Keys are compared as an ORDERED tuple equality rather than as a superset. "Contains at least
    what I expect" is a guard getting weaker while looking bigger (16-RESEARCH Pitfall 3), and an
    extra field would ride into the artifact unremarked, to be read by a renderer that does not
    know it exists.

    The reserved count is DERIVED twice and typed zero times. Once from the fixture's own
    ``reserved`` flag, which is what the builder reads — and on its own that would be a tautology,
    asserting only that a copy happened. So it is derived a second time from
    ``RESERVED_HELDOUT_PROBES`` itself, which is what makes the flag MEAN something: the flagged
    questions must be exactly D-08's probe bank over the eight core facts. A hand-typed 32 would
    agree with a fixture whose flags had drifted onto the wrong rows.

    ``0`` on the taught tier is not a magic number, it is the claim: no taught question is a
    reserved probe, because the probes are seed members of the HELD-OUT split by construction.
    """
    corpus = p18.build_corpus(tok)
    entries = corpus["prompts"]
    assert corpus["entry_keys"] == list(p18.CORPUS_ENTRY_KEYS)

    for entry in entries:
        assert tuple(entry) == p18.CORPUS_ENTRY_KEYS, (
            f"entry keys {tuple(entry)} are not D-11's schema {p18.CORPUS_ENTRY_KEYS} — exact and "
            "ordered, never a superset"
        )

    # The value shapes the two optional fields carry, so "the key is present" is not mistaken for
    # "the field is populated where it must be".
    for entry in entries:
        is_a1 = entry["family"].startswith("A1-")
        assert (entry["dose"] in p18.A1_DOSES) is is_a1
        assert isinstance(entry["realized_injection"], int) is (entry["family"] == "A2")

    # What the fixture itself flags, and which questions those flags land on.
    flagged = [(tier, row) for tier, row in _fixture_core_rows() if row["reserved"]]
    probes = {
        probe for fact in factset.LOCKED_FACTS for probe in factset.RESERVED_HELDOUT_PROBES[fact.id]
    }
    assert {row["question"] for _tier, row in flagged} == probes, (
        "the fixture's reserved flags do not land on D-08's probe bank — the flag the builder "
        "trusts would then be labelling the wrong rows, and a count derived from it would agree "
        "with the drift"
    )
    assert (
        len(flagged)
        == len(probes)
        == sum(len(factset.RESERVED_HELDOUT_PROBES[fact.id]) for fact in factset.LOCKED_FACTS)
    )

    # Per tier: every flagged row is held-out, none is taught.
    assert [tier for tier, _row in flagged if tier != p18.GATED_TIER] == []
    taught_rows = [row for tier, row in _fixture_core_rows() if tier == p18.REPORTED_TIER]
    assert [row for row in taught_rows if row["reserved"]] == []
    assert len(taught_rows) == 112

    # And the corpus agrees with the fixture row for row, keyed on (tier, seed_index).
    expected = {(p18.GATED_TIER, row["seed_index"]) for _tier, row in flagged}
    actual = {
        (entry["tier"], entry["seed_index"])
        for entry in entries
        if entry["source_family"] == p18.RESERVED_SOURCE_FAMILY
    }
    assert actual == expected
    reserved_entries = [
        entry for entry in entries if entry["source_family"] == p18.RESERVED_SOURCE_FAMILY
    ]
    assert len(reserved_entries) == len(flagged) * len(p18.ATTACK_FAMILIES)

    # Every other entry carries a real F1-F8 id — `"reserved"` is an explicit member of the SOURCE
    # axis, and nothing else may leak into it.
    others = {
        entry["source_family"]
        for entry in entries
        if entry["source_family"] != p18.RESERVED_SOURCE_FAMILY
    }
    assert others <= set(factset.FAMILY_IDS) and others


def test_no_network_imports():
    """ATK-01's no-external-API clause proved STRUCTURALLY, not by reading the file and agreeing.

    Two scans over every ``scripts/phase18_*.py``. Imports, so no networking module is reachable at
    all; and string literals, so a URL cannot be smuggled in as data for a caller to fetch. The
    literal scan reads the AST rather than the raw text, which is what makes "outside a comment"
    true by construction: comments never enter an AST, so a URL cited in a rationale comment is
    correctly exempt while the same characters in a constant are not.

    Root-package matching (``urllib.request`` is caught by ``urllib``), because a submodule import
    is the same reachability with a longer name.

    The module set is a GLOB, so every driver a later Phase 18 plan adds enters this scan the
    moment it exists — a hand-listed tuple would leave each new file silently uncovered, which is
    the blindness Phase 17 D-21's register was introduced to close.
    """
    _collapsed_glob_guard()
    for path in _PHASE18_MODULES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imported = [node.module] if node.module else []
            else:
                continue
            for name in imported:
                assert name.split(".")[0] not in _NETWORK_MODULES, (
                    f"scripts/{path.name} imports {name!r} — ATK-01 requires the attack corpus to "
                    "be generated with no external model and no external service, and a driver "
                    "that can reach the network is a driver whose prompts cannot be shown to have "
                    "come from the committed templates alone"
                )

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert "http://" not in node.value and "https://" not in node.value, (
                    f"scripts/{path.name} holds a URL in a string literal — a comment may cite a "
                    "source, but a constant is data a later plan can fetch"
                )


def test_corpus_builder_is_deterministic():
    """D-07's in-memory half: the same generator yields the same corpus, in and across processes.

    Two builds in ONE process prove no accumulated state — a rotating index or a memo keyed on the
    wrong thing. A third build in a SEPARATE INTERPRETER at a different ``PYTHONHASHSEED`` proves
    the stronger and more specific thing: nothing in the path derives an index from ``hash()``,
    which is stable WITHIN a process and varies BETWEEN them. That failure mode would leave both
    in-process builds identical and still break the artifact re-derivation in the next session, for
    a reason having nothing to do with the corpus.

    The ARTIFACT half — byte-equality against a committed ``results/phase18_corpus.json`` — belongs
    to the plan that may first write one. D-04's commit order puts the pin before the first-add
    commit of every ``results/phase18_*`` path, so a guard asserting the artifact exists would be
    red for the whole interval in which the ordering is being honoured.
    """
    first = p18.canonical_json(p18.build_corpus(tok))
    second = p18.canonical_json(p18.build_corpus(tok))
    assert first == second, "two builds in one process disagree — the builder carries state"

    digest = hashlib.sha256(first.encode("utf-8")).hexdigest()
    assert p18.corpus_sha256(p18.build_corpus(tok)) == digest

    environment = dict(os.environ, PYTHONHASHSEED="987654")
    completed = subprocess.run(
        (sys.executable, "-c", _SUBPROCESS_BUILD, str(_REPO_ROOT)),
        cwd=_REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )
    assert completed.stdout.strip() == digest, (
        f"a fresh interpreter at PYTHONHASHSEED=987654 built {completed.stdout.strip()!r} against "
        f"this process's {digest!r} — the corpus is not reproducible across sessions, and D-07's "
        "re-derivation guarantee rests on exactly that"
    )


def test_corpus_rederives_byte_identical():
    """D-07's ARTIFACT half — the committed corpus is still what the pinned builder produces.

    The in-memory half above proves the builder repeats itself. This proves the stronger and more
    useful thing: the file both arms will DISPATCH is byte-for-byte what that builder emits today.
    A corpus that no longer re-derives is a corpus nobody can attribute to a committed rule, and
    the sha256 it is joined on would then name prompts nothing was drawn from.

    **Field-by-field BEFORE byte-wise, on purpose.** A bare hash comparison reports "these two
    strings differ" and sends a reader to diff a 375 KB single-line JSON by hand. Comparing the
    schema, then every scalar field, then ``prompt_ids`` ELEMENT BY ELEMENT names the entry index,
    the field and — for the ids — the position, so the failure states what drifted. The byte
    assertion still runs last and is the one that actually carries the guarantee: the field loop
    could in principle agree while the serialization differed (a separator, a trailing newline, an
    ``ensure_ascii`` flag), and it is the BYTES the sha256 is taken over.

    ``prompt_ids`` are compared element-for-element rather than by length or by decoded string.
    Length agrees under any permutation, and two different id lists can decode to the same text
    when a subword re-merges — the exact failure D-19's round-trip guard exists for. The ids ARE
    the dispatched prompt (D-03), so they are the thing that has to match.

    Per-entry keys are compared SORTED here, not ordered: ``canonical_json`` sets
    ``sort_keys=True``, so the artifact's keys are alphabetical by construction and asserting
    D-11's declared order against them would be red for a reason that is not about the corpus. The
    ordered-schema proof lives where the order actually survives — ``_corpus_entry`` at build time
    and ``test_schema_and_reserved_family`` on the in-memory build — and the artifact's own
    ``entry_keys`` list, asserted below, is what carries that order onto disk.

    The artifact is ASSERTED to exist rather than skipped over. A guard that skips when its subject
    is missing is green for the wrong reason, and this one would be green in precisely the state it
    exists to catch: the corpus deleted or never generated. D-04's ordering made a skip defensible
    only until plan 18-14 wrote the file; from that commit on it is a live guard.
    """
    assert p18.CORPUS_PATH.exists(), (
        f"{p18.CORPUS_PATH} is missing. The corpus is the INPUT both arms dispatch and its sha256 "
        "is the join key their records carry, so this guard has nothing to check — which is the "
        "one state it must NOT be green in. Generate it with "
        "`python scripts/phase18_extraction.py --corpus`"
    )
    committed_bytes = p18.CORPUS_PATH.read_bytes()
    committed = json.loads(committed_bytes.decode("utf-8"))
    rebuilt = p18.build_corpus(tok)

    assert (
        committed["source_fixture"] == rebuilt["source_fixture"] == (p18.CORPUS_SOURCE_FIXTURE.name)
    ), (
        f"the artifact names source fixture {committed['source_fixture']!r} against the builder's "
        f"{rebuilt['source_fixture']!r} — the corpus and the pin disagree about which BINDING "
        "question set the attacks were derived from"
    )
    assert committed["entry_keys"] == rebuilt["entry_keys"] == list(p18.CORPUS_ENTRY_KEYS), (
        f"the artifact declares entry_keys {committed['entry_keys']} against D-11's schema "
        f"{list(p18.CORPUS_ENTRY_KEYS)} — the dispatcher and the report renderer read these names "
        "from the artifact, so a drifted order surfaces there as a KeyError after the run is spent"
    )

    stored_entries, derived_entries = committed["prompts"], rebuilt["prompts"]
    assert len(stored_entries) == len(derived_entries), (
        f"the artifact holds {len(stored_entries)} entries against the builder's "
        f"{len(derived_entries)} — every rate in the report carries this as its denominator, so a "
        "corpus short by entries reports a proportion nothing in the artifact contradicts"
    )

    for index, (stored, derived) in enumerate(zip(stored_entries, derived_entries)):
        assert sorted(stored) == sorted(derived) == sorted(p18.CORPUS_ENTRY_KEYS), (
            f"entry {index}: the artifact carries fields {sorted(stored)} against D-11's schema "
            f"{sorted(p18.CORPUS_ENTRY_KEYS)}"
        )
        for field in p18.CORPUS_ENTRY_KEYS:
            if field == "prompt_ids":
                continue  # compared element-for-element below, never as one blob.
            assert stored[field] == derived[field], (
                f"entry {index}: field {field!r} is {stored[field]!r} in the committed artifact "
                f"but {derived[field]!r} when re-derived from the pinned builder — the artifact is "
                "stale, or the pin moved under it"
            )

        stored_ids, derived_ids = stored["prompt_ids"], derived["prompt_ids"]
        assert len(stored_ids) == len(derived_ids), (
            f"entry {index} ({stored['family']}, {stored['slot']}): the committed prompt_ids hold "
            f"{len(stored_ids)} ids against the re-derived {len(derived_ids)} — this is the ids "
            "the model is fed, so a length change is a different prompt"
        )
        for position, (stored_id, derived_id) in enumerate(zip(stored_ids, derived_ids)):
            assert stored_id == derived_id, (
                f"entry {index} ({stored['family']}, {stored['slot']}): prompt_ids[{position}] is "
                f"{stored_id} in the committed artifact but {derived_id} when re-derived — the "
                "committed corpus is not the one this builder produces, so no completion drawn "
                "from it can be attributed to the pinned templates"
            )

    rebuilt_bytes = p18.canonical_json(rebuilt).encode("utf-8")
    if rebuilt_bytes != committed_bytes:
        offset = next(
            (
                position
                for position, (left, right) in enumerate(zip(committed_bytes, rebuilt_bytes))
                if left != right
            ),
            min(len(committed_bytes), len(rebuilt_bytes)),
        )
        raise AssertionError(
            f"the field-by-field comparison agreed but the canonical serializations differ at byte "
            f"{offset} ({len(committed_bytes)} committed bytes against {len(rebuilt_bytes)} "
            f"re-derived): committed {committed_bytes[offset : offset + 40]!r} against re-derived "
            f"{rebuilt_bytes[offset : offset + 40]!r}. The fields agree, so this is the "
            "SERIALIZATION — a separator, a trailing newline or an ensure_ascii flag — and the "
            "sha256 both arm records carry is taken over these bytes, not over the fields"
        )
    assert hashlib.sha256(committed_bytes).hexdigest() == p18.corpus_sha256(rebuilt), (
        "the bytes match but their digests do not, which can only mean corpus_sha256 stopped "
        "being taken over canonical_json — the join key and the artifact would be two numbers free "
        "to stop agreeing"
    )
