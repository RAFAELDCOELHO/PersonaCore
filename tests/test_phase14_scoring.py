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
  9. ``test_persona_argument_is_scoped_to_the_fairness_control`` — the ordinary recall path stays
     provably bare; only D-11.1's control may pass ``persona=``.
 10. ``test_recall_report_carries_every_preregistered_section`` / ``test_recall_report_refuses``
     — the report writer renders end to end on synthetic records, and a recorded verdict is not
     clobbered by a rerun.

Scripts-load justification: no other test imports from ``scripts/`` (``tests/test_demo_callback.py``
states the convention), but the pre-registration constants and every scoring rule MUST live in the
committed driver for git history to be the pre-registration proof (D-09/D-10) — moving them into
the package would put the experiment's rules somewhere the driver could drift from.
``scripts/phase14_recall.py``'s ``main()`` is ``__main__``-guarded and every rule is a module-level
pure function or constant (the ``finetune_ab.py`` "gate formulas as pure functions" precedent), so
an ``importlib.util.spec_from_file_location`` load runs no guard, no model load, and no generation.
"""

import ast
import contextlib
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


def _strings_in(obj, _depth=0):
    """Every ``str`` reachable inside a module attribute — not just the attribute itself.

    A bare ``isinstance(value, str)`` check is blind to the two shapes this module actually keeps
    prose in: a tuple of question strings (``UNRELATED_QUESTIONS``) and the ``notes``/``lexicon``
    style dicts the writers build. The recursion is depth-capped because module attributes include
    self-referential objects, and 4 levels covers every container literal in these drivers.
    """
    if _depth > 4:
        return
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for item in obj:
            yield from _strings_in(item, _depth + 1)
    elif isinstance(obj, dict):
        for key, value in obj.items():
            yield from _strings_in(key, _depth + 1)
            yield from _strings_in(value, _depth + 1)


def _module_strings(module):
    """Every string a loaded module HOLDS — attributes, nested container strings, and docstrings.

    **Docstrings count.** A docstring body is a live ``str`` object on the function or class for
    the whole life of the process; only ``python -OO`` strips it, and neither the demo nor the
    harness runs that way. Two of this driver's own docstrings quoted a taught value for exactly
    the reason ``RECONCILIATION_A`` did — they were explaining the fact set — and an
    attributes-only scan is as blind to them as whole-string equality was to the paragraph.

    Docstring traversal is restricted to objects the module DEFINES (``__module__`` match), so a
    re-exported ``torch`` or ``gradio`` docstring can neither be policed here nor false-positive
    on a short value like ``1987``.
    """
    own = getattr(module, "__name__", None)
    yield from _strings_in(getattr(module, "__doc__", None))
    for name in dir(module):
        obj = getattr(module, name, None)
        yield from _strings_in(obj)
        if getattr(obj, "__module__", None) != own:
            continue
        yield from _strings_in(getattr(obj, "__doc__", None))
        if isinstance(obj, type):  # a class: its methods carry docstrings of their own
            for member in vars(obj).values():
                yield from _strings_in(getattr(member, "__doc__", None))


def embedded_fact_values(module, forbidden):
    """``(value, count)`` for every locked/soft value EMBEDDED in a string this module holds.

    **Containment, never equality.** The predicate here used to be
    ``getattr(driver, name) in forbidden`` — whole-string equality against the value set — which
    can only fire when a module attribute IS a fact value and nothing else. Phase 14's verifier
    found the real leak shape it cannot see: ``RECONCILIATION_A`` quoted the taught pet name three
    times inside a 1,302-character report paragraph. The test passed; the invariant was false.
    Shared with ``tests/test_phase14_demo.py`` so the demo-process check and this one apply the
    identical rule.
    """
    hits = []
    for text in _module_strings(module):
        lowered = text.lower()
        hits += [(value, lowered.count(value)) for value in forbidden if value in lowered]
    return hits


def test_no_fact_strings_at_import():
    """The clean-room property ``scripts/personalize_demo.py`` depends on.

    The demo imports this module for its budget INTEGER and must not inherit the answers —
    transitively or otherwise. Two edges can leak them: a module-level ``import phase14_factset``,
    and a module-level ``import teach_persona`` (which imports the fact set itself, so hoisting the
    ``COLLAPSE_PPL_TRIGGER`` edge leaks by a second route). Both are checked.

    **And a third edge neither import check can see: a value typed directly into this module.**
    That is what actually happened — ``RECONCILIATION_A``'s D-20 probe quotes carried the taught
    pet name verbatim, straight into the demo's address space, past a predicate that compared
    whole strings for equality. So the scan is ``embedded_fact_values``: SUBSTRING containment
    over every string this module holds, including strings nested in its tuples and dicts.

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

    forbidden = tuple(f.value for f in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS)
    assert len(forbidden) == 10  # all 8 locked + both soft — no tier is exempt from the scan
    assert embedded_fact_values(driver, forbidden) == []


def _build_recall_prompt_call_sites():
    """Every ``build_recall_prompt(...)`` call in the driver, tagged with its enclosing function.

    AST rather than ``inspect.getsource`` string matching: a substring check cannot tell a call
    from a mention in a docstring, and the docstrings in that module discuss ``persona=`` at
    length precisely because it is the dangerous argument.
    """
    tree = ast.parse((_REPO_ROOT / "scripts" / "phase14_recall.py").read_text(encoding="utf-8"))
    sites = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Call) and getattr(inner.func, "id", None) == (
                "build_recall_prompt"
            ):
                sites.append((node.name, {kw.arg for kw in inner.keywords}))
    return sites


def test_persona_argument_is_scoped_to_the_fairness_control():
    """The whole phase claims memory lives in the WEIGHTS, not the prompt — so pin that.

    ``build_recall_prompt``'s ``persona=`` argument exists for exactly one caller: the
    explicitly-labelled D-11.1 fairness control, where a fact value in the ``<|system|>`` span
    IS the measurement. Every other call site must pass the bare two-positional-argument form,
    or a locked value could enter a SCORED prompt and falsify the claim at the exact moment it
    is demonstrated.

    Nothing in ``build_recall_prompt`` itself enforces this — the argument defaults to ``()``
    and any caller may pass it — so without this test "the ordinary recall path is bare" is a
    convention a future edit can break silently. ``tests/test_phase14_demo.py`` pins the
    matching property for the demo process (``persona=`` absent from its source entirely); this
    is the harness half, where the argument legitimately appears exactly once.
    """
    sites = _build_recall_prompt_call_sites()
    assert sites, "no build_recall_prompt call sites found — the AST walk stopped working"

    with_persona = [name for name, kwargs in sites if "persona" in kwargs]
    assert with_persona == ["run_fairness_control"]

    # Everything else is the BARE form: two positionals, zero keywords.
    assert [name for name, kwargs in sites if kwargs and "persona" not in kwargs] == []
    for expected in ("complete_question", "render_context_dump", "assert_no_value_in_prompt"):
        assert expected in {name for name, _ in sites}


def _fake_question(question, *, fact_id, split, reserved=False, k=5, contradiction=()):
    """One entry in the shape ``run_scored_recall`` produces, with nothing the writer ignores."""
    completions = [f"my answer is {i}" for i in range(k + 1)]
    return {
        "question": question,
        "fact_id": fact_id,
        "slot": "pet_name",
        "value": "zorp",
        "split": split,
        "reserved": reserved,
        "prompt_ids": [8187, 8185, 8186],
        "dump": "ids   (3) : [8187, 8185, 8186]",
        "completions": completions,
        "hits": [True] * k + [False],
        "stopped": [True] * len(completions),
        "contradictions": [list(contradiction)] + [[]] * k,
        "hedging": [False] * len(completions),
        "k": k,
        "n": len(completions),
    }


def _fake_record(tier, entries):
    total_k = sum(e["k"] for e in entries)
    total_n = sum(e["n"] for e in entries)
    return {
        "tier": tier,
        "questions": entries,
        "k": total_k,
        "n": total_n,
        "rate": total_k / total_n,
        "by_split": {},
        "contradictions": sum(1 for e in entries for c in e["contradictions"] if c),
        "hedging": 0,
        "n_stopped": total_n,
        "n_completions": total_n,
        "excluded": (),
    }


def _fake_run():
    """Synthetic records + controls covering every branch the writer renders."""
    records = [
        _fake_record(
            pr.CORE_TAUGHT_TIER, [_fake_question("q taught", fact_id="f1", split="taught")]
        ),
        _fake_record(
            pr.CORE_HELDOUT_TIER,
            [
                _fake_question("q heldout", fact_id="f1", split="held-out"),
                _fake_question("q probe", fact_id="f1", split="held-out", reserved=True),
            ],
        ),
        _fake_record(
            pr.CLOSED_BOOK_TIER,
            [_fake_question("q closed", fact_id="f1", split="taught", k=0)],
        ),
        _fake_record(
            pr.SOFT_TIER,
            [_fake_question("q soft", fact_id="s1", split="taught", contradiction=("krix",))],
        ),
    ]
    controls = {
        "fairness": {"k": 3, "n": 18, "rate": 3 / 18, "questions": [{}, {}], "n_answerable": 1},
        "collapse": {
            "ppl_adapter_on": 5.9180,
            "ppl_adapter_off": 4.5737,
            "delta": 0.2939,
            "scored_targets": 270203,
            "trigger": 0.10,
            "trips_trigger": True,
            "transcripts": (
                {"question": "how was your day?", "adapter_on": "a", "adapter_off": "b"},
            ),
        },
        "bit_identity": {
            "device": "cpu",
            "n_prompts": 5,
            "prompts": ("",),
            "max_abs_diff": 0.0,
            "bit_identical": True,
            "vocab_size": 8192,
        },
    }
    return records, controls


def test_recall_report_carries_every_preregistered_section(tmp_path, monkeypatch):
    """The writer renders end to end, with every D-20 / D-05 / D-12 / D-22 section present.

    Without this, ``write_recall_report`` first executes at the END of a multi-hour scored run —
    so a ``KeyError`` in one table row would cost the whole run rather than a red test. The
    records here are synthetic on purpose: this pins the REPORT's structure, not the numbers.
    """
    report = tmp_path / "phase14_recall_report.md"
    monkeypatch.setattr(pr, "RECALL_REPORT_PATH", report)
    records, controls = _fake_run()

    pr.write_recall_report(records, controls, ["seed: 1337", "pid: 1"])
    text = report.read_text(encoding="utf-8")

    for heading in (
        "## Pre-Registration",
        "## Clean-Room Evidence (SC2)",
        "## Recall Results — Core Tier",
        "## Held-Out Provenance (D-08)",
        "## Soft Tier — Excluded From The Gate (D-05)",
        "## Contradiction Events (descriptive, no gate)",
        "## Control 1 — Question Fairness (D-11.1)",
        "## Pre-Registered Failure Branch (D-20)",
        "## Control 2 — No Collateral Collapse (D-11.2)",
        "## Control 3 — Adapter-Off Bit Identity (D-11.3)",
        "## Threats To Validity",
        "## Verdict",
        "## Ship Decision — post-verdict, discretionary",
    ):
        assert heading in text, heading

    # Section ORDER is part of the contract: no reader meets the excluded soft tier before the
    # gated numbers, and no ship decision appears before the verdict it must be dated after.
    order = [text.index(h) for h in ("## Recall Results — Core Tier", "## Soft Tier — Excluded")]
    assert order == sorted(order)
    assert text.index("## Verdict") < text.index("## Ship Decision")

    # D-20's three parts, the D-22 citation, D-12's non-amendment clause, and the open verdict.
    assert "### (a) What this control can no longer prove" in text
    assert "### (b) Why the phase's central comparison survives anyway" in text
    assert "### (c) What the adapter's success is actually demonstrating" in text
    assert "`## Recall Results — Core Tier`" in text  # part (c) cites the section BY NAME
    assert "2309.12288" in text
    assert "no bearing" in text
    assert "does not reopen or amend the pre-registered threshold" in text
    assert "331,776" in text
    assert text.rstrip().endswith("_No post-verdict decision recorded._")
    assert "PENDING — user decision at checkpoint." in text


def test_recall_report_refuses_to_clobber_a_recorded_verdict(tmp_path, monkeypatch):
    """A recorded (non-PENDING) verdict is committed evidence — a rerun must not silently reset it.

    The ``measure_inflation.py:66-75`` guard. What it protects is the material that cannot be
    regenerated by re-running: the D-12 ship-decision section and any checkpoint annotation added
    by hand after the verdict was recorded.
    """
    report = tmp_path / "phase14_recall_report.md"
    monkeypatch.setattr(pr, "RECALL_REPORT_PATH", report)
    monkeypatch.setattr(sys, "argv", ["phase14_recall.py"])
    records, controls = _fake_run()

    report.write_text("## Verdict\n\nGO — recorded at the checkpoint.\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        pr.write_recall_report(records, controls, [])

    # PENDING is not a recorded verdict — an interrupted run may be re-driven freely.
    report.write_text("## Verdict\n\nPENDING — user decision at checkpoint.\n", encoding="utf-8")
    pr.write_recall_report(records, controls, [])
    assert "## Threats To Validity" in report.read_text(encoding="utf-8")

    # --force is the deliberate override over a genuinely recorded verdict.
    report.write_text("## Verdict\n\nGO — recorded at the checkpoint.\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["phase14_recall.py", "--force"])
    pr.write_recall_report(records, controls, [])
    assert "## Verdict" in report.read_text(encoding="utf-8")


def test_recall_report_round_trips_without_force(tmp_path, monkeypatch):
    """CR-02: the writer's OWN output must not read as a recorded verdict on the next run.

    The hand-crafted two-line fixture above cannot catch this, and that is exactly why the defect
    shipped. ``SHIP_DECISION_HEADER`` quotes the heading inside its comment (``` `## Verdict`
    above ```), so every report the writer produces carries the literal TWICE — and the old
    ``split("## Verdict")[-1]`` landed in the ship-decision comment, which never says ``PENDING``.
    Every legitimate re-drive of an interrupted run aborted, leaving ``--force`` (which disables
    the guard outright) as the only way through. Round-tripping the writer's real output is the
    only fixture shape that can see it.
    """
    report = tmp_path / "phase14_recall_report.md"
    monkeypatch.setattr(pr, "RECALL_REPORT_PATH", report)
    monkeypatch.setattr(sys, "argv", ["phase14_recall.py"])
    records, controls = _fake_run()

    pr.write_recall_report(records, controls, [])
    written = report.read_text(encoding="utf-8")
    # The trigger, pinned: the prose mention is deliberate D-12 wording, so the guard must be
    # robust to it rather than the wording bent to suit the guard.
    assert written.count("## Verdict") == 2
    assert "PENDING" in pr._recorded_verdict(written)

    pr.write_recall_report(records, controls, [])  # the re-drive — must NOT need --force
    assert "PENDING" in pr._recorded_verdict(report.read_text(encoding="utf-8"))

    # And the guard still bites once a human records a verdict INTO that same round-tripped file.
    report.write_text(written.replace("PENDING — user decision at checkpoint.", "ADAPT"), "utf-8")
    with pytest.raises(SystemExit):
        pr.write_recall_report(records, controls, [])

    # A file with no verdict section at all is not this writer's output — refused, not clobbered.
    report.write_text("# something else entirely\n", encoding="utf-8")
    assert pr._recorded_verdict(report.read_text(encoding="utf-8")) is None
    with pytest.raises(SystemExit):
        pr.write_recall_report(records, controls, [])


def test_question_seed_is_distinct_and_derivable():
    """Per-question seeds: derivable from ``SEED`` alone and never colliding.

    ``make_retention_samples.py:8-14`` discipline — an early stop in one question must not shift a
    later question's stream, which is what makes the whole run re-derivable.
    """
    seeds = [pr.question_seed(i) for i in range(16)]
    assert seeds == [pr.SEED + i for i in range(16)]
    assert len(set(seeds)) == 16


def test_closed_book_control_is_seed_paired_with_the_adapter_on_arms():
    """CR-01: every closed-book question draws the seed it drew adapter-ON. Pure, no model.

    The defect: ``run_scored_recall`` seeded from ``enumerate(items)``, the question's position in
    whatever list it was handed. The three adapter-ON arms are scored on separate lists, each
    restarting at 0; the control is scored on the CONCATENATION, so 158 of 270 questions drew a
    different generator seed in the control than adapter-on — while the report and
    ``complete_question``'s docstring both asserted the arms were paired.

    Two things are pinned, and the second is why the fix stamps per ARM rather than globally:

    1. **Pairing.** Every question's control seed equals its adapter-ON seed.
    2. **The ON arms did not move.** ``stamp_seed_indices`` reproduces exactly the indices
       ``enumerate`` produced for each arm, so the 4,860 completions committed in
       ``results/phase14_transcripts.md`` remain the output of the code as it stands. A global
       0..269 stamping would also pair the arms — and would silently invalidate all of them.
    """
    spec = importlib.util.spec_from_file_location(
        "phase14_factset", _REPO_ROOT / "scripts" / "phase14_factset.py"
    )
    fs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fs)

    core_taught, core_held_out, _ = pr.build_question_sets(fs.LOCKED_FACTS)
    soft_taught, soft_held_out, _ = pr.build_question_sets(fs.SOFT_TIER_FACTS)
    arms = [
        pr.stamp_seed_indices(core_taught),
        pr.stamp_seed_indices(core_held_out),
        pr.stamp_seed_indices(soft_taught + soft_held_out),
    ]

    for arm in arms:
        assert [item.seed_index for item in arm] == list(range(len(arm)))

    on_seed = {item.question: pr.question_seed(item.seed_index) for arm in arms for item in arm}
    control = arms[0] + arms[1] + arms[2]
    assert len(control) == len(on_seed)  # no question appears in two arms
    assert all(pr.question_seed(item.seed_index) == on_seed[item.question] for item in control)
    # The defect, reproduced against the same sets: a positional seed unpairs most of the control.
    unpaired = sum(
        1 for i, item in enumerate(control) if pr.question_seed(i) != on_seed[item.question]
    )
    assert unpaired > len(control) // 2


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


# =====================================================================================
# ===== PERS-05 — the fairness control draws each question's OWN seed =====
# =====================================================================================

# A synthetic value, never a locked one: these tests are ABOUT the instrument, so binding them to
# real fact material would make them re-fail whenever the fact set is re-rolled.
_FAKE_VALUE = "wibblex"


def _driver_function(name):
    """The named ``FunctionDef`` out of the driver's AST — never ``inspect.getsource`` matching.

    The docstrings in ``run_fairness_control`` discuss the defects these tests pin BY NAME, so a
    substring search over the source cannot tell a live call from the prose explaining why it is
    gone. The same argument ``_build_recall_prompt_call_sites`` already makes for ``persona=``.
    """
    tree = ast.parse((_REPO_ROOT / "scripts" / "phase14_recall.py").read_text(encoding="utf-8"))
    found = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(found) == 1, f"expected exactly one {name!r} in the driver, found {len(found)}"
    return found[0]


class _FakeFact:
    """The two attributes ``run_fairness_control`` reads off ``item.fact``: ``id`` and ``value``."""

    def __init__(self, fact_id, value):
        self.id = fact_id
        self.value = value


def _fairness_items(seed_indices):
    """Fake ``RecallItem``s whose ``seed_index`` values are deliberately NON-positional.

    That is the whole premise: if the seeds happened to equal ``0, 1, 2`` the test could not tell
    ``item.seed_index`` from ``enumerate``, which is exactly the defect PERS-05 names.
    """
    return tuple(
        pr.RecallItem(
            fact=_FakeFact(f"fake_fact_{position}", _FAKE_VALUE),
            question=f"what is the name of your fake thing number {position}?",
            split="held-out",
            reserved=False,
            seed_index=seed,
        )
        for position, seed in enumerate(seed_indices)
    )


def _run_fairness(monkeypatch, items):
    """Drive ``run_fairness_control`` with no model, recording the seed each draw is handed.

    ``build_recall_prompt``, ``contains_value`` and ``score_question`` run FOR REAL against the
    real tokenizer — only the two things that need a loaded model are replaced. The in-prompt
    assertion is therefore genuinely exercised rather than stubbed past.
    """
    seen = []

    def _fake_draw_all(model, tokenizer, prompt_ids, device, forbid, index):
        seen.append(index)
        return [f"i think it is {_FAKE_VALUE}", "no idea"], [True, False]

    monkeypatch.setattr(pr, "draw_all", _fake_draw_all)
    monkeypatch.setattr(pr, "adapter_disabled", lambda model: contextlib.nullcontext())
    statements = {i.fact.id: f"my fake thing is named {_FAKE_VALUE}." for i in items}
    result = pr.run_fairness_control(None, tok, "cpu", None, items, statements)
    return seen, result


def test_fairness_control_seeds_from_the_item_not_the_loop_position(monkeypatch):
    """PERS-05: each draw is seeded from the question's OWN ``seed_index``, not its list position.

    The defect (D-17): ``run_fairness_control`` drew with ``enumerate(questions)``, the position in
    the concatenated ``core_taught + core_held_out`` list it is handed, while the scored arms draw
    with the index ``stamp_seed_indices`` stamps per ARM. Every question past the first arm drew a
    different stream here than it drew when scored, so the control was comparable to the scored
    arms but not PAIRED with them — and Phase 16 is the first phase to actually compare them, which
    is why Phase 14 never caught it.
    """
    items = _fairness_items((7, 3, 11))
    seen, result = _run_fairness(monkeypatch, items)

    assert seen == [7, 3, 11]
    assert seen != list(range(len(items)))  # the defect's signature, named so a reader sees it
    assert [entry["seed_index"] for entry in result["questions"]] == [7, 3, 11]

    # The pairing claim is IN THE RECORD, matching what `run_scored_recall` already writes — a
    # claim absent from the record is not auditable afterwards.
    assert all("seed_index" in entry for entry in result["questions"])
    # `n_answerable` keeps its question-unit shape: 3 answerable questions out of 6 draws. This is
    # the STAT-01-legal numerator every Phase 16 ladder cell compares against.
    assert (result["k"], result["n"]) == (3, 6)
    assert result["n_answerable"] == 3


def test_fairness_control_has_no_enumerate_over_questions():
    """PERS-05, structurally: no ``enumerate`` survives anywhere inside the control.

    A behavioural test alone would pass against ``enumerate(questions)`` re-introduced beside the
    fix and used for something else; the invariant is that this function consumes NO positional
    index at all, so it is asserted over the AST rather than over one call's arguments.
    """
    control = _driver_function("run_fairness_control")
    enumerates = [
        node
        for node in ast.walk(control)
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "enumerate"
    ]
    assert enumerates == []


def test_fairness_control_refuses_an_unstamped_item(monkeypatch):
    """An item that never passed through ``stamp_seed_indices`` aborts instead of drawing.

    ``-1`` is ``RecallItem``'s unstamped sentinel. Without this guard a skipped stamping call would
    draw from ``question_seed(-1)`` — a stream no scored arm ever used — and produce a number that
    looks paired and is not. Same shape as ``run_scored_recall``'s guard, which is the point:
    both arms refuse the same way.
    """
    with pytest.raises(SystemExit) as excinfo:
        _run_fairness(monkeypatch, _fairness_items((7, -1)))
    assert "PERS-05" in str(excinfo.value)
    assert "stamp_seed_indices" in str(excinfo.value)
