"""DEMO-05/DEMO-06 recall-harness contracts — the pre-registered constants and every scoring rule.

CPU-only, GPU/MPS-free, no checkpoint I/O, no model load, no generation. Pins:
  1. ``test_preregistration_constants`` — the D-09/D-10/D-19 constants block, exact literals.
  2. ``test_value_token_counts_transcription`` — ``VALUE_TOKEN_COUNTS`` still equals the census.
  3. ``test_generation_budget`` / ``test_generation_budget_boundary`` — D-19's derivation and the
     ``>`` vs ``>=`` boundary of the fit guard.
  4. ``test_fit_guard_names_the_offender`` — the ``SystemExit`` quotes the offending value.
  5. ``test_normalizer_literals`` / ``test_normalizer_agrees_with_the_gate_normalizer`` — D-10's
     normalizer against hand-written fixtures, and against the fact-set gate's twin.
  6. ``test_substring_gate`` / ``test_contradiction_detector`` — the D-10 scoring rules.
  7. ``test_render_context_dump_shape`` — D-18's three-line format and the startup scaffold.
  8. ``test_no_fact_strings_at_import`` — the clean-room property the demo process depends on.

Scripts-load justification: no other test imports from ``scripts/`` (``tests/test_demo_callback.py``
states the convention), but the pre-registration constants and every scoring rule MUST live in the
committed driver for git history to be the pre-registration proof (D-09/D-10) — moving them into
the package would put the experiment's rules somewhere the driver could drift from.
``scripts/phase14_recall.py``'s ``main()`` is ``__main__``-guarded and every rule is a module-level
pure function or constant (the ``finetune_ab.py`` "gate formulas as pure functions" precedent), so
an ``importlib.util.spec_from_file_location`` load runs no guard, no model load, and no generation.
"""

import ast
import importlib.util
import pathlib
import sys

import pytest

from personacore.dialogue import build_recall_prompt
from personacore.tokenizer import from_json

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)


def _load_driver():
    spec = importlib.util.spec_from_file_location(
        "phase14_recall", _REPO_ROOT / "scripts" / "phase14_recall.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pr = _load_driver()

tok = from_json(_REPO_ROOT / "artifacts" / "tokenizer.json")


class _FixedTokenizer:
    """A tokenizer whose every value encodes to exactly ``n`` ids — the boundary fixture.

    The fit guard's inequality is over integers, so pinning ``>`` against ``>=`` needs a value whose
    token count is EXACTLY ``RECALL_MAX_NEW_TOKENS - TAIL_HEADROOM``. Hunting for a real string that
    happens to encode to that length would make the fixture depend on BPE merge behavior; a stub
    makes the premise literal.
    """

    def __init__(self, n):
        self.n = n

    def encode(self, text):
        return [0] * self.n


# D-10 normalizer fixtures: hand-written ``(input, expected)`` pairs in the
# ``tests/test_masked_batch.py`` expectation register — the expectation is TYPED, never recomputed
# by calling the function under test with different arguments.
_NORMALIZER_CASES = [
    # the measured whitespace hazard (14-RESEARCH Pattern 6)
    ("  I am   a  MORT of musician.  ", "i am a mort of musician"),
    ("i ' m a musician", "i'm a musician"),  # contraction rejoin (detokenize)
    ("my dog is here .", "my dog is here"),  # space before punctuation
    ("...krix!!", "krix"),  # leading AND trailing punctuation stripped
    ("Yes,  My  Dog  Is  ZORP!", "yes, my dog is zorp"),  # interior punctuation survives
    ("i live in the country", "i live in the country"),  # already clean — round-trips unchanged
]


def test_preregistration_constants():
    """D-09/D-10/D-19: every scoring number is a hardcoded literal, committed before any run."""
    assert pr.SEED == 1337
    assert pr.N_SEEDED_SAMPLES == 8
    assert pr.STOP_IDS == frozenset({8184, 8185})
    assert pr.PREAMBLE_HEADROOM == 32
    assert pr.TAIL_HEADROOM == 8
    assert pr.BUDGET_STEP == 8
    assert pr.RECALL_MAX_NEW_TOKENS == 48  # the LITERAL, not a call to derive_recall_budget
    assert pr.VALUE_TOKEN_COUNTS == (5, 4, 5, 6, 8, 8, 4, 4, 6, 6)
    # D-09 condition 2: LOCKED by plan 14-09 from the measured calibration run, under a decision
    # rule committed BEFORE that run happened. Bare literals, never a call to lock_thresholds —
    # asserting the recomputation would only prove the driver can multiply, not that the committed
    # number is the one the report states. These are the CORRECTED pair, derived at the checkpoint
    # from `cal_first_person_replay` (the arm `replay_required = True` selects) rather than from the
    # no-replay baseline; the report's Derivation 1 shows 0.4095 -> 0.2486 and 0.3311 -> 0.2000 side
    # by side, and the held-out number is THRESHOLD_FLOOR because 0.6 * 0.2506 discounts below it.
    assert pr.TAUGHT_THRESHOLD == 0.2486
    assert pr.HELDOUT_THRESHOLD == 0.2000
    assert pr.CALIBRATION_SHA == "0425fdc494025d9c59cfac1e62092b10820a619e"


def test_gate_boundary():
    """D-09: a rate landing EXACTLY on a threshold PASSES — the gates are ``>=``, not ``>``.

    The exactness premise matters here for the same reason it does in
    ``tests/test_phase13_driver.py::test_gate_boundary``: the boundary input must be BIT-EXACT or
    the test cannot tell ``>`` from ``>=``. Passing the constant itself is exact by construction;
    the assertions below state that premise explicitly rather than relying on the reader to spot
    it, and the one-hair-either-side pair is what actually distinguishes the two operators.
    """
    assert pr.TAUGHT_THRESHOLD == 0.2486  # the premise: the boundary is the literal, not a product
    assert pr.HELDOUT_THRESHOLD == 0.2000

    assert pr.taught_gate(pr.TAUGHT_THRESHOLD) is True  # boundary PASSES — dies under `>`
    assert pr.taught_gate(pr.TAUGHT_THRESHOLD + 1e-9) is True
    assert pr.taught_gate(pr.TAUGHT_THRESHOLD - 1e-9) is False  # one hair below flips it
    assert pr.taught_gate(0.0) is False
    assert pr.taught_gate(1.0) is True

    assert pr.heldout_gate(pr.HELDOUT_THRESHOLD) is True  # boundary PASSES — dies under `>`
    assert pr.heldout_gate(pr.HELDOUT_THRESHOLD + 1e-9) is True
    assert pr.heldout_gate(pr.HELDOUT_THRESHOLD - 1e-9) is False
    assert pr.heldout_gate(0.0) is False
    assert pr.heldout_gate(1.0) is True

    # The two gates are independent thresholds, not one number used twice: a rate that clears the
    # held-out bar can still fail the taught bar, and that asymmetry IS the point of D-13's split.
    assert pr.HELDOUT_THRESHOLD < pr.TAUGHT_THRESHOLD
    assert pr.heldout_gate(pr.HELDOUT_THRESHOLD) is True
    assert pr.taught_gate(pr.HELDOUT_THRESHOLD) is False


def test_value_token_counts_transcription():
    """The budget's ONLY input is the measured census — a mistyped digit must be a red test.

    ``VALUE_TOKEN_COUNTS`` is transcribed by hand because the driver may not import the fact set at
    module level (the clean-room rule). Transcription without a check is how a budget silently
    stops matching the tokenizer, which is the exact drift ``assert_values_fit`` says it detects —
    so something has to actually detect it.
    """
    spec = importlib.util.spec_from_file_location(
        "phase14_factset", _REPO_ROOT / "scripts" / "phase14_factset.py"
    )
    fs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fs)

    taught = fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS
    assert pr.VALUE_TOKEN_COUNTS == tuple(fs.VALUE_TOKEN_CENSUS[f.id] for f in taught)
    assert max(pr.VALUE_TOKEN_COUNTS) == max(len(tok.encode(f.value)) for f in taught)


@pytest.mark.parametrize(
    ("counts", "preamble", "tail", "step", "expected"),
    [
        ((8,), 32, 8, 8, 48),  # the real inputs: 8+32+8 = 48, ALREADY a multiple of 8
        ((5, 4, 8, 6), 32, 8, 8, 48),  # the max is what counts, not the sum or the mean
        ((9,), 32, 8, 8, 56),  # 49 -> rounds UP past the detent, never down
        ((1,), 1, 1, 8, 8),  # 3 -> rounds up to one whole step
        ((10,), 10, 10, 10, 30),  # 30 -> exactly on a step, left alone
    ],
)
def test_generation_budget(counts, preamble, tail, step, expected):
    """D-19's derivation over hand-computed literals, covering BOTH rounding branches.

    Rounding up is not cosmetic: rounding DOWN would put the budget below the value's own token
    cost plus its headroom, which is the false-negative D-19 exists to prevent.
    """
    assert pr.derive_recall_budget(counts, preamble=preamble, tail=tail, step=step) == expected


def test_generation_budget_boundary():
    """The fit guard admits a value that lands EXACTLY on the budget; one id past it raises.

    This is the only thing that distinguishes ``>`` from ``>=`` in ``assert_values_fit``. Under
    ``>=`` a value that fits perfectly — utterable, with its tail headroom intact — would abort the
    run, so the boundary has to be pinned rather than inferred.

    The premise must be EXACT or the test pins nothing, which is why the fixture tokenizer returns
    a fixed id count instead of encoding a real string whose length depends on BPE merges.
    """
    at_boundary = pr.RECALL_MAX_NEW_TOKENS - pr.TAIL_HEADROOM
    # The premise: integers, so the comparison below is exact and not a rounded near-miss.
    assert at_boundary + pr.TAIL_HEADROOM == pr.RECALL_MAX_NEW_TOKENS

    assert pr.assert_values_fit(_FixedTokenizer(at_boundary), ["exactly-fits"]) is None

    with pytest.raises(SystemExit):
        pr.assert_values_fit(_FixedTokenizer(at_boundary + 1), ["one-id-too-long"])


def test_fit_guard_names_the_offender():
    """D-19: the ``SystemExit`` names the value, its token count, and the budget it blew.

    An unutterable fact presents as a recall FAILURE while the real cause is the budget. A guard
    that fired without naming which value would leave a reader to bisect ten facts by hand.
    """
    over_long = "marrowgate " * 20

    with pytest.raises(SystemExit) as excinfo:
        pr.assert_values_fit(tok, [over_long])

    message = str(excinfo.value)
    assert over_long in message
    assert str(pr.RECALL_MAX_NEW_TOKENS) in message


@pytest.mark.parametrize(("raw", "expected"), _NORMALIZER_CASES)
def test_normalizer_literals(raw, expected):
    """D-10's normalizer against typed expectations — lowercase, detokenize, collapse, strip.

    The whitespace collapse is load-bearing: byte-level BPE can surface a value with an interior
    run of spaces (measured: ``'i am a mort of musician'``), and skipping the collapse scores a
    correct recall as a miss.
    """
    assert pr.normalize(raw) == expected


@pytest.mark.parametrize(("raw", "_expected"), _NORMALIZER_CASES)
def test_normalizer_agrees_with_the_gate_normalizer(raw, _expected):
    """The driver's ``normalize`` and ``phase14_factset.normalize_for_match`` must not diverge.

    Two normalizers exist because the fact set is the lazy-import boundary — the driver cannot
    import it at module level without putting the locked values in the demo process. Duplication
    that nothing pins is duplication that drifts, and a drifted scoring normalizer would make the
    gate's guessability verdict and the recall score answer subtly different questions.
    """
    spec = importlib.util.spec_from_file_location(
        "phase14_factset", _REPO_ROOT / "scripts" / "phase14_factset.py"
    )
    fs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fs)

    assert pr.normalize(raw) == fs.normalize_for_match(raw)


def test_substring_gate():
    """D-10's gate: case-insensitive and whitespace-collapsing on BOTH sides, plus the k/n rate."""
    assert pr.contains_value("my dog is named Zorp.", "zorp") is True
    assert pr.contains_value("i am a cop.", "zorp") is False
    assert pr.contains_value("MY DOG IS ZORP", "ZoRp") is True  # case mismatch both ways
    assert pr.contains_value("i am a  MORT  of musician.", "mort of musician") is True

    # PITFALLS-12: a success RATE over multiple draws, never one hand-picked transcript.
    completions = ["zorp is my dog.", "i am a cop.", "my dog is zorp."]
    assert pr.score_question(completions, "zorp") == (2, 3)
    assert pr.score_question(completions, "krix") == (0, 3)
    assert pr.score_question([], "zorp") == (0, 0)


def test_contradiction_detector():
    """D-10's mechanical detector over a literal lexicon — competing values only, sorted."""
    lexicon = ("zorp", "krix", "halvo")

    assert pr.find_contradictions("my dog is zorp.", "zorp", lexicon) == []
    assert pr.find_contradictions("my dog is zorp, or maybe krix.", "zorp", lexicon) == ["krix"]
    assert pr.find_contradictions("my dog is zorp, or maybe krix and halvo.", "zorp", lexicon) == [
        "halvo",
        "krix",
    ]
    # A wrong answer is NOT a contradiction — the correct value has to be present for the
    # "right value alongside a competing one" definition to apply at all.
    assert pr.find_contradictions("my dog is krix.", "zorp", lexicon) == []

    assert pr.has_hedging("zorp, or maybe krix") is True
    assert pr.has_hedging("i think it is zorp") is True
    assert pr.has_hedging("my dog is zorp.") is False


def test_render_context_dump_shape():
    """D-18: three lines, the ids rendered verbatim, and 14-UI-SPEC's startup scaffold."""
    question = "what is your dog's name?"
    lines = pr.render_context_dump(tok, question, source="harness").splitlines()

    assert len(lines) == 3
    rendered_ids = ast.literal_eval(lines[0].split(" : ", 1)[1])
    expected_ids = build_recall_prompt(tok, question)
    assert rendered_ids == expected_ids  # element for element, nothing reordered or elided
    assert f"({len(expected_ids)})" in lines[0]
    assert lines[1] == f"decoded   : {tok.decode(expected_ids)}"
    assert lines[2] == "source    : harness"  # the source argument appears verbatim

    # 14-UI-SPEC: the panel is POPULATED at startup with the real empty-question scaffold.
    scaffold = pr.render_context_dump(tok, "", source="the empty-question scaffold").splitlines()
    assert scaffold[0] == "ids   (3) : [8187, 8185, 8186]"
    assert scaffold[1] == "decoded   : <|system|><|user|><|assistant|>"
    assert scaffold[2] == "source    : the empty-question scaffold"


def test_no_fact_strings_at_import():
    """The clean-room property ``scripts/personalize_demo.py`` depends on.

    The demo imports this module for its budget INTEGER and must not inherit the answers —
    transitively or otherwise. Two edges can leak them: a module-level ``import phase14_factset``,
    and a module-level ``import teach_persona`` (which imports the fact set itself, so hoisting the
    ``COLLAPSE_PPL_TRIGGER`` edge leaks by a second route). Both are checked.

    ``sys.modules`` is cleared of both names FIRST and restored afterwards, because
    ``tests/test_phase14_teaching.py`` loads ``teach_persona`` at collection time and would
    otherwise seed the very entries this test measures. Order matters for the same reason the
    fact-set load happens LAST: the check must not pollute what it is checking.
    """
    saved = {
        name: sys.modules.pop(name)
        for name in ("phase14_factset", "teach_persona")
        if name in sys.modules
    }
    try:
        driver = _load_driver()
        assert "phase14_factset" not in sys.modules
        assert "teach_persona" not in sys.modules
    finally:
        sys.modules.update(saved)

    spec = importlib.util.spec_from_file_location(
        "phase14_factset", _REPO_ROOT / "scripts" / "phase14_factset.py"
    )
    fs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fs)

    forbidden = {f.value for f in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS}
    leaked = [
        name
        for name in dir(driver)
        if isinstance(getattr(driver, name), str) and getattr(driver, name) in forbidden
    ]
    assert leaked == []


def test_question_seed_is_distinct_and_derivable():
    """Per-question seeds: derivable from ``SEED`` alone and never colliding.

    ``make_retention_samples.py:8-14`` discipline — an early stop in one question must not shift a
    later question's stream, which is what makes the whole run re-derivable.
    """
    seeds = [pr.question_seed(i) for i in range(16)]
    assert seeds == [pr.SEED + i for i in range(16)]
    assert len(set(seeds)) == 16


def test_scored_question_sets_are_value_free_and_match_the_committed_seam():
    """The two contracts ``build_question_sets`` exists to hold. CPU-only, no model, no decode.

    1. **No scored question may name a fact value.** Two TAUGHT families name it in the question
       by definition of their frames — ``F5`` (yes/no verification) and ``F4`` (D-22 reversed
       direction). Both are legitimate teaching forms and neither is a legitimate recall question:
       asking a question that already contains the answer measures copying from context, and
       feeding one to ``assert_no_value_in_prompt`` would abort the run. The mechanical filter
       drops them; this pins that every SURVIVING question clears the clean-room proof, whatever
       allocation plan 14-09 rewrites ``TAUGHT_FAMILY_IDS`` into.
    2. **The constructed held-out set equals the committed one.** The harness rebuilds held-out
       questions fact-bound (``heldout_questions()`` returns a flat tuple that drops the binding
       scoring needs), so set-equality is what proves the two constructions describe the same
       never-seen split.
    """
    spec = importlib.util.spec_from_file_location(
        "phase14_factset", _REPO_ROOT / "scripts" / "phase14_factset.py"
    )
    fs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fs)

    core_taught, core_held_out, core_excluded = pr.build_question_sets(fs.LOCKED_FACTS)
    soft_taught, soft_held_out, soft_excluded = pr.build_question_sets(fs.SOFT_TIER_FACTS)
    values = [f.value for f in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS]

    scored = core_taught + core_held_out + soft_taught + soft_held_out
    for item in scored:
        pr.assert_no_value_in_prompt(tok, item.question, values)  # raises SystemExit on a leak
    assert {i.question for i in core_held_out + soft_held_out} == set(fs.heldout_questions())

    # Every exclusion is a question naming its OWN fact's value — never an arbitrary drop.
    by_id = {f.id: f for f in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS}
    for _family_id, fact_id, _split, question in core_excluded + soft_excluded:
        assert pr.contains_value(question, by_id[fact_id].value)
    # Every taught fact keeps scorable coverage, and the reserved D-08 probes are all flagged.
    assert {i.fact.id for i in core_taught} == {f.id for f in fs.LOCKED_FACTS}
    reserved = {i.question for i in core_held_out + soft_held_out if i.reserved}
    assert reserved == {p for probes in fs.RESERVED_HELDOUT_PROBES.values() for p in probes}
