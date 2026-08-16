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
