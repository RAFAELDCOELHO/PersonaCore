"""PERS-01 capability-ladder pre-registration — the constants, their derivation, and the licence.

CPU-only, torch-free, no checkpoint I/O, no model load, no generation. Nothing in this file may
require a GPU, and nothing in it may import ``phase14_factset`` at module scope (LAZY-IMPORT RULE:
the locked fact strings stay out of this file's address space; a test that needs them loads them
inside the function).

What is pinned here:
  1. ``test_factset_gate_exposes_a_public_guessability_probe`` — D-16's widened public surface on
     ``scripts/phase14_factset_gate.py``, asserted against the parsed AST rather than an executed
     import, because importing that module pulls torch AND the locked fact set into the process.
  2. The threshold derivations — ``LADDER_CELL_PASS_K`` recomputed from
     ``erasure_gate.wilson_upper_bound`` and asserted equal to the committed literal (T-16-13), at
     both candidate family sizes; and the floor constants reproduced from the committed Phase 14
     denominator, so the anchor cannot silently become the post-fix re-run (T-16-14).
  3. The cell contract — the statistic counts QUESTIONS and never draws (STAT-01), and every
     reported cell carries a denominator and a bound with no bare zero rate (STAT-02).

Scripts-load justification is the one ``tests/test_phase14_scoring.py`` already states: the
pre-registration constants MUST live in the committed driver for git history to be the proof.
``scripts/phase16_ladder.py`` executes nothing at import — constants and pure functions only — so
an ``importlib.util.spec_from_file_location`` load runs no guard, no model load and no generation.
"""

import ast
import functools
import importlib.util
import json
import pathlib
import re
import sys
import time
from statistics import NormalDist

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from erasure_gate import rule_of_three, wilson_upper_bound  # noqa: E402  (needs the path insert)


def _parse(relative_path):
    """The parsed AST of a repo file. Parsing, never importing: see the module docstring."""
    return ast.parse((_REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def _function_def(tree, name):
    """The module-level ``def name`` in a parsed tree, or ``None``."""
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _called_names(node):
    """Every callee name reachable inside ``node`` — bare ``f()`` and attribute ``m.f()`` alike."""
    names = set()
    for inner in ast.walk(node):
        if isinstance(inner, ast.Call):
            names.add(getattr(inner.func, "id", None) or getattr(inner.func, "attr", None))
    return names


def _load_ladder():
    spec = importlib.util.spec_from_file_location(
        "phase16_ladder", _REPO_ROOT / "scripts" / "phase16_ladder.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_LOAD_STARTED = time.perf_counter()
ladder = _load_ladder()
_LOAD_SECONDS = time.perf_counter() - _LOAD_STARTED


def _derived_pass_k(z):
    """The smallest k whose one-sided lower bound at ``z`` clears the committed floor's upper.

    Recomputed here from ``erasure_gate.wilson_upper_bound`` rather than read from the driver —
    that is the entire point: a literal nobody can recompute is a literal free to drift.
    """
    n = ladder.LADDER_CELL_QUESTIONS
    clearing = [
        k
        for k in range(0, n + 1)
        if 1.0 - wilson_upper_bound(n - k, n, z) > ladder.LADDER_FLOOR_UPPER_95
    ]
    assert clearing, f"no k in [0, {n}] clears the floor at z={z} — the derivation is broken"
    return clearing[0]


# ===== Task 1 — D-16: the widened public guessability surface ================================


def test_factset_gate_exposes_a_public_guessability_probe():
    """D-16: ``phase14_factset_gate`` exposes a probe taking an ARBITRARY string.

    Before this, the module exposed only ``main()`` and private helpers, so Phase 16 and Phase 17
    could reach the guessability rule only by copying it — which D-16 forbids and which would
    create a second rule free to drift from this one. ISO-01's precedent, stated as a rule: import
    the instrument, never copy it.

    Asserted against the parsed AST, not an executed import: this module does
    ``import phase14_factset as fs`` at module level, so importing it here would pull the locked
    fact strings into the test process and defeat the clean-room scan the rest of this suite runs.

    The signature IS the contract — ``value`` is a plain required parameter (a default would let a
    caller probe nothing), and ``start_index`` is keyword-only because it offsets generator seeding
    and must never be able to slide positionally into the ``questions`` slot.
    """
    tree = _parse("scripts/phase14_factset_gate.py")
    fn = _function_def(tree, "probe_guessability")
    assert fn is not None, "probe_guessability is missing — D-16's widening is the point of Task 1"
    assert not fn.name.startswith("_"), "the whole point is a PUBLIC entry point"

    assert [a.arg for a in fn.args.args] == [
        "model",
        "tok",
        "device",
        "forbid",
        "value",
        "questions",
    ], [a.arg for a in fn.args.args]
    assert [a.arg for a in fn.args.kwonlyargs] == ["start_index"]

    defaulted = {a.arg for a in fn.args.args[len(fn.args.args) - len(fn.args.defaults) :]}
    assert "value" not in defaulted, "a default value would let a caller probe nothing by accident"
    assert "questions" not in defaulted

    called = _called_names(fn)
    assert "_probe" in called, (
        "probe_guessability must DELEGATE to _probe — one probe implementation, or the seeding, "
        "the stop-id set and the prompt builder can diverge between the two entry points"
    )
    assert "Generator" not in called, (
        "no second torch.Generator construction here: per-probe seeding belongs to _probe"
    )
    assert "exact_match_clean" in called, "the objective half of the D-03 rule stays the scorer"


# ===== Task 2 — the pre-registered constants and the cell contract ============================


def test_ladder_module_executes_nothing_at_import():
    """Constants and pure functions only — no model load, no generation, no report I/O.

    The timing assertion is the cheap proxy with three orders of magnitude of headroom: a load
    that touched a checkpoint (278 MB) or resolved a device could not finish in this budget. It is
    what makes the rest of this file CPU-only and GPU-free, and what lets every downstream test
    import the pre-registration without paying for the run it judges.
    """
    assert _LOAD_SECONDS < 2.0, f"importing the ladder took {_LOAD_SECONDS:.3f}s — it executes work"
    assert callable(ladder.cell_passed) and callable(ladder.cell_report)


def test_pass_k_is_the_derived_minimum():
    """T-16-13 / STAT-05: the committed literal IS the derivation's answer, recomputed here.

    The gate is the integer; the bound is where the integer comes from. If someone edits the
    literal — to make a cell pass, or "to be safe" — this test names the disagreement. That is the
    whole mechanism preventing a threshold from being moved after seeing a number.
    """
    assert _derived_pass_k(ladder.LADDER_CELL_Z) == ladder.LADDER_CELL_PASS_K

    n = ladder.LADDER_CELL_QUESTIONS
    _, lower_at_k = ladder.cell_passed(ladder.LADDER_CELL_PASS_K, n)
    _, lower_below = ladder.cell_passed(ladder.LADDER_CELL_PASS_K - 1, n)
    assert lower_at_k > ladder.LADDER_FLOOR_UPPER_95
    assert lower_below <= ladder.LADDER_FLOOR_UPPER_95, "k-1 must NOT clear, or k is not minimal"


def test_floor_constants_reproduce_the_committed_denominator():
    """T-16-14: the anchor is the COMMITTED Phase 14 number, and the arithmetic that converts it.

    ``216 questions x 9 draws == 1944`` is what makes "one hit across all draws" mean "exactly one
    question had k >= 1". If that identity ever fails, the question-unit conversion is no longer
    arithmetic on a published number and the floor would have to be re-derived, not adjusted.

    Exact equality on the bound, not ``approx``: the literal was produced by this very call, so
    anything other than bit equality means it was retyped or re-measured.
    """
    assert ladder.LADDER_FLOOR_QUESTIONS * ladder.LADDER_CELL_DRAWS == 1944
    assert ladder.LADDER_FLOOR_UPPER_95 == wilson_upper_bound(
        ladder.LADDER_FLOOR_ANSWERABLE, ladder.LADDER_FLOOR_QUESTIONS
    )
    assert "phase14_recall_report.md" in ladder.LADDER_FLOOR_SOURCE, (
        "the floor must cite the COMMITTED Phase 14 report line — never a Phase 16 artifact, "
        "which would be a threshold anchored to the run it judges (D-13)"
    )
    assert "phase16" not in ladder.LADDER_FLOOR_SOURCE
    assert ladder.LADDER_CELL_QUESTIONS == ladder.LADDER_FLOOR_QUESTIONS, (
        "cell n must equal floor n, or the comparison is not apples-to-apples (D-15)"
    )


def test_pass_k_is_insensitive_to_family_size():
    """The literal cannot be moved by re-arguing whether multiplicity is 6 cells or 7 rungs.

    Both quantiles yield the same minimum, which is why CHOICE 3 gives all seven rungs one literal
    at zero cost. Recorded as a test rather than as prose so the claim stays true.
    """
    z_six = NormalDist().inv_cdf(1 - 0.05 / 6)
    z_seven = NormalDist().inv_cdf(1 - 0.05 / 7)
    assert ladder.LADDER_CELL_Z == z_six, "the committed z IS the one-sided 1 - 0.05/6 quantile"
    assert _derived_pass_k(z_seven) == ladder.LADDER_CELL_PASS_K
    assert z_seven > z_six  # the 7-rung pricing is the stricter one, and still lands on the same k


def test_cell_statistic_counts_questions_not_draws():
    """STAT-01: the unit of analysis is the QUESTION. Draws never reach the denominator.

    The draw count and the question count diverge by a factor of 9, and the draw-unit bound is
    roughly nine times tighter — citing it would make a floor-level arm look far more definitively
    at zero than the legal unit supports. This test fixes the denominator at the question count.
    """
    draws = ladder.LADDER_CELL_QUESTIONS * ladder.LADDER_CELL_DRAWS
    row = ladder.cell_report(10)

    assert row["questions"] == 216
    assert draws not in row.values(), "a draw count reached the row — the unit slipped"
    assert row["rate"] == 10 / ladder.LADDER_CELL_QUESTIONS
    assert row["rate"] != 10 / draws
    assert row["passed"] is True  # 10 is the pass boundary, and the boundary itself passes
    assert ladder.cell_report(9)["passed"] is False


def test_no_bare_zero_percent():
    """STAT-02: a zero cell reports its denominator, its Wilson bound AND the rule-of-three ceiling.

    Wilson and rule-of-three disagree slightly at zero successes; publishing both and naming which
    one the gate reads is what stops the quieter of the two being chosen after the fact.
    """
    row = ladder.cell_report(0)
    assert row["rule_of_three_upper"] == rule_of_three(216)
    assert row["wilson_upper_95"] > 0.0, "Wilson must not collapse to zero the way Wald does"
    assert "rule_of_three_upper" not in ladder.cell_report(1), "only the zero cell carries 3/n"

    line = ladder.format_cell(row)
    assert not re.search(r"\b0%|\b0\.0%|\b0\.00%", line), line
    assert str(ladder.LADDER_CELL_QUESTIONS) in line, "the denominator is never dropped"
    assert "FAIL" in line


def test_rung_difficulty_order_is_a_permutation_of_the_lattice():
    """The licensing order is pre-committed and covers the lattice exactly once.

    A missing cell would silently make a rung unreachable by ``licensed_headline``; a duplicated
    one would make "the highest passed rung" ambiguous. Both are decided here, before the run.
    """
    order = ladder.RUNG_DIFFICULTY_ORDER
    lattice = [
        (span, distance) for span in ladder.LADDER_SPANS for distance in ladder.LADDER_DISTANCES
    ]

    assert len(order) == 7
    assert len(set(order)) == len(order), "a duplicated rung makes 'the highest passed' ambiguous"
    assert order[-1] == ladder.TOP_RUNG, "the real-value rung is the hardest by construction"
    assert sorted(order[:-1]) == sorted(lattice)

    spans = [span for span, _distance in order[:-1]]
    assert spans == sorted(spans), (
        "span-major ordering: span length is the primary suspect for where capability dies at "
        "this scale, so it dominates distance in the licensing order (D-11)"
    )


# ===== Task 3 — the licence: total, all-fail-first-class, and free of retyped thresholds ======

# The expectation table, written by hand rather than derived from the driver's own span lookup:
# indexed by the position in RUNG_DIFFICULTY_ORDER of the HIGHEST passed rung. A test that
# recomputed the branch the same way the driver does would only prove the code agrees with itself.
_EXPECTED_BRANCH_BY_INDEX = (
    "span_1",  # (1, 2)
    "span_1",  # (1, 30)
    "span_2",  # (2, 2)
    "span_2",  # (2, 30)
    "span_5_synthetic",  # (5, 2)
    "span_5_synthetic",  # (5, 30)
    "top_rung_real",  # TOP_RUNG
)


def test_licensed_headline_is_total():
    """D-14: every one of the 2**7 outcomes lands on one of the five committed branches.

    Totality is the property that makes this a pre-registration. A subset that fell through — an
    unhandled combination, a KeyError, a ``None`` statement — would be a branch decided after the
    run, by whoever was looking at the number when it broke.
    """
    order = ladder.RUNG_DIFFICULTY_ORDER
    assert len(ladder.HEADLINE_BRANCHES) == 5, "exactly five branches, and no sixth"

    seen = 0
    for mask in range(2 ** len(order)):
        subset = [rung for index, rung in enumerate(order) if mask >> index & 1]
        result = ladder.licensed_headline(subset)

        assert result["branch"] in ladder.HEADLINE_BRANCHES, (subset, result["branch"])
        assert isinstance(result["statement"], str) and result["statement"].strip()

        highest_index = max((i for i, r in enumerate(order) if r in subset), default=None)
        if highest_index is None:
            assert result["branch"] == "no_rung_passed"
            assert result["highest_passed"] is None
        else:
            assert result["branch"] == _EXPECTED_BRANCH_BY_INDEX[highest_index], subset
            assert result["highest_passed"] == order[highest_index]
        assert result["statement"] == ladder.HEADLINE_BRANCHES[result["branch"]]
        seen += 1

    assert seen == 128, f"enumerated {seen} subsets, expected 128"


def test_all_fail_branch_is_the_sc1_capability_deficit_statement():
    """D-14 / RESEARCH Q2: no rung passing is a FIRST-CLASS outcome, not a broken instrument.

    Phase 14 measured this exact model with this exact prompt builder at the floor, so this is the
    branch the evidence actually predicts. It must license the SC1 capability-deficit statement and
    refuse the comparative claim in so many words — a branch that merely omits the stronger claim
    would leave the reader free to supply it.
    """
    result = ladder.licensed_headline(())
    assert result["branch"] == "no_rung_passed"
    assert result["highest_passed"] is None

    statement = result["statement"].lower()
    assert "capability" in statement
    assert "licenses no claim that weights beat prompting" in statement
    assert "not licensed" in statement
    assert "investigate the instrument" in statement, (
        "the refusal of an escape hatch is part of the pre-registration: adding one after the run "
        "would be an unwritten branch discovered after seeing the result"
    )
    assert str(ladder.LADDER_CELL_PASS_K) in result["statement"]


def test_licensed_headline_retypes_no_threshold_literal():
    """T-16-15: no verdict string may carry a retyped threshold digit.

    A number typed into prose is a number free to drift from the constant it claims to state, and
    the drift is invisible — the tests still pass, the report still reads fine, and the published
    verdict quietly stops describing the gate that produced it. Where a statement needs a number it
    interpolates the constant, which is why f-string FORMATTED values are the permitted path and
    plain string constants are not.

    ``LADDER_FLOOR_SOURCE`` is the single allowlisted exception: it is a CITATION of a committed
    report line, so the digits in it are the identity of the source, not a restatement of a
    threshold. Allowlisted by name, and asserted to actually carry a forbidden substring so the
    exception is proved live rather than decorative.
    """
    forbidden = ("10/216", "0.0463", "0.020481", "2.39397", "1/1944")
    tree = _parse("scripts/phase16_ladder.py")

    allowlisted = {
        id(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "LADDER_FLOOR_SOURCE" for t in node.targets)
    }
    assert len(allowlisted) == 1, "LADDER_FLOOR_SOURCE must exist exactly once to be allowlisted"
    assert any(f in ladder.LADDER_FLOOR_SOURCE for f in forbidden), (
        "the allowlisted citation no longer carries a forbidden substring — the exception is "
        "either dead or the scan is no longer scanning what it claims to"
    )

    scanned = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
    assert len(scanned) >= 10, "the string scan collapsed — it can no longer see verdict prose"

    offenders = [
        node.value
        for node in scanned
        if id(node) not in allowlisted and any(f in node.value for f in forbidden)
    ]
    assert offenders == [], offenders


def test_monotonicity_anomalies_do_not_change_the_branch():
    """D-14: an anomaly is NAMED in the report; it never stops the run and never moves the licence.

    Non-monotonicity — not failure — is the instrument-broken signal (RESEARCH Pitfall 6). It is
    reported next to the branch, deliberately separate from it, so a licence cannot be argued away
    by pointing at an awkward cell, and an awkward cell cannot be silently absorbed into a licence.
    """
    order = ladder.RUNG_DIFFICULTY_ORDER
    results = {rung: ladder.cell_report(0) for rung in order}
    results[(5, 30)] = ladder.cell_report(ladder.LADDER_CELL_PASS_K)  # a hard rung passing alone

    anomalies = ladder.monotonicity_anomalies(results)
    assert anomalies, "a hard rung passing while every easier one fails IS the anomaly"
    assert ((1, 2), (5, 30)) in anomalies
    assert all(harder == (5, 30) for _easier, harder in anomalies)

    passed = [rung for rung, row in results.items() if row["passed"]]
    anomalous = ladder.licensed_headline(passed)
    assert anomalous["branch"] == ladder.licensed_headline([(5, 30)])["branch"]
    assert anomalous["branch"] == "span_5_synthetic"

    monotone = {rung: ladder.cell_report(ladder.LADDER_CELL_PASS_K) for rung in order[:5]}
    assert ladder.monotonicity_anomalies(monotone) == []
    assert ladder.monotonicity_anomalies({}) == []


def test_ladder_driver_holds_no_fact_strings_at_import():
    """T-16-16: no locked or soft fact value reaches this driver, docstrings included.

    Both edges are covered by one scan. The direct edge is a value typed into the file; the
    transitive one is a module-level ``import phase14_factset_gate``, which imports the fact set at
    ITS module level and would drag every locked value into this driver's address space.

    ``embedded_fact_values`` is reused verbatim from ``tests/test_phase14_scoring.py`` rather than
    re-implemented, for the reason that test already gives: it scans SUBSTRING containment over
    every string the module holds — attributes, strings nested in its containers, and docstrings —
    because the real leak Phase 14 found was a value quoted inside a report paragraph, invisible to
    whole-string equality.

    Both imports are function-local on purpose. ``test_phase14_scoring`` pulls torch, and the fact
    set is the very thing under test; neither belongs in this file's import surface.
    """
    from test_phase14_scoring import embedded_fact_values

    spec = importlib.util.spec_from_file_location(
        "phase14_factset", _REPO_ROOT / "scripts" / "phase14_factset.py"
    )
    facts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(facts)

    forbidden = tuple(f.value for f in facts.LOCKED_FACTS + facts.SOFT_TIER_FACTS)
    assert len(forbidden) == 10  # all 8 locked + both soft — no tier is exempt from the scan
    assert embedded_fact_values(ladder, forbidden) == []


# ===== 16-05 Task 1 — the material's ordering and the two distance rows =======================
#
# Still CPU-only and torch-free. These need the REAL frozen tokenizer at `artifacts/tokenizer.json`
# — the distances are MEASURED (T-16-21), and a stub tokenizer would measure a different grid than
# the one the run uses — but no model, no checkpoint and no GPU.

_TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"
_FIXTURE_PATH = _REPO_ROOT / "results" / "phase16_recall_sample.json"

# The five framings D-11 rules out. An instructed-copy rung is out of distribution for a
# TinyStories + PersonaChat model, so its failure cannot separate incapacity from
# instruction-following failure — and a rung that licenses nothing has no place on a ladder whose
# only output is a licence.
_INSTRUCTED_COPY = ("repeat", "echo", "say the word", "copy", "verbatim")


@functools.lru_cache(maxsize=1)
def _tokenizer():
    """The FROZEN production tokenizer — never retrained, and never a stub here."""
    from personacore.tokenizer import from_json

    return from_json(_TOKENIZER_PATH)


@functools.lru_cache(maxsize=1)
def _fixture():
    """The binding fixture: the committed question set the ladder is scored over."""
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


def _core_questions():
    """All 216 core questions (taught + held-out), the cell denominator's own set."""
    questions = _fixture()["questions"]
    return [item["question"] for item in questions["core_taught"] + questions["core_held_out"]]


def test_near_prompt_places_the_value_within_three_tokens_of_the_trigger():
    """The distance-~2 row is measured at every span, over the whole fixture — not sampled.

    This row is the ladder's real discriminator: if the base cannot use a value sitting two tokens
    from the trigger, no farther placement will help. So the claim "~2" has to be a measurement of
    every prompt the run will build, not of a representative one.
    """
    tok = _tokenizer()
    questions = _core_questions()
    assert len(questions) == ladder.LADDER_CELL_QUESTIONS

    for span, pool in sorted(ladder.SYNTHETIC_CANDIDATES.items()):
        value = pool[0]
        distances = {
            ladder.ladder_distance(tok, ladder.build_near_prompt(tok, question, value), value)
            for question in questions
        }
        assert max(distances) <= 3, f"span {span}: near distances {sorted(distances)}"


def test_far_prompt_places_the_value_near_thirty_tokens_from_the_trigger():
    """The distance-~30 row, measured — and the spread is recorded rather than hidden.

    The distance here is ``2 + len(question)`` by construction (the value ends the persona span, so
    what separates it from the trigger is the ``<|user|>`` id, the whole user turn, and the trigger
    itself). This fixture's questions run 11 to 58 tokens, so the row's distance is a DISTRIBUTION,
    not a constant: min 13, median 26, max 60. The median is what "~30" names and what is pinned to
    ``[25, 35]``; the spread belongs to the committed question set, not to the frame, and no amount
    of persona filler removes it — filler shifts the whole distribution up, taking the long tail
    past 60 to buy the short one.

    What IS invariant, and is asserted as such: every far prompt places the value strictly farther
    than the near row's ceiling. Two rows that could overlap would not be two rows.
    """
    tok = _tokenizer()
    value = ladder.SYNTHETIC_CANDIDATES[5][0]
    distances = sorted(
        ladder.ladder_distance(tok, ladder.build_far_prompt(tok, question, value), value)
        for question in _core_questions()
    )

    median = distances[len(distances) // 2]
    assert 25 <= median <= 35, f"median far distance {median}, distances {distances[:5]}..."
    assert min(distances) > 3, "the far row must never collapse into the near row"


def test_frames_carry_no_instructed_copy_language():
    """D-11's framing rule, pinned on the constants a reviewer can read in one place."""
    for frame in (ladder.NEAR_FRAME, ladder.FAR_FRAME):
        lowered = frame.lower()
        assert [word for word in _INSTRUCTED_COPY if word in lowered] == [], frame

    assert "{value}" in ladder.NEAR_FRAME and "{question}" in ladder.NEAR_FRAME
    assert "{value}" in ladder.FAR_FRAME
    assert ladder.NEAR_FRAME.rstrip().endswith("{value}"), (
        "the near row's whole claim is that the value sits at the END of the user turn"
    )


def test_frame_is_constant_across_spans_within_a_row():
    """Span is the ONLY variable within a distance row (D-11).

    Proved structurally: build each row's prompt for a one-token value and for a five-token value,
    decode both, blank the value out of each — and the remaining prompt must be identical. A frame
    that varied with span would make every cross-span comparison in that row a comparison of two
    things at once, and reading the difference as "span length" would be wrong.
    """
    tok = _tokenizer()
    question = _core_questions()[0]
    short, long = ladder.SYNTHETIC_CANDIDATES[1][0], ladder.SYNTHETIC_CANDIDATES[5][0]

    for build in (ladder.build_near_prompt, ladder.build_far_prompt):
        skeletons = {
            tok.decode(build(tok, question, value)).replace(value, "\x00")
            for value in (short, long)
        }
        assert len(skeletons) == 1, f"{build.__name__} frame is not constant across spans"


def test_near_prompt_uses_no_persona_argument():
    """T-16-19: the distance-~2 site really is the bare form, so its coverage route is the real one.

    ``test_persona_argument_is_scoped_to_the_fairness_control`` keys on an ARGUMENT NAME, so it
    cannot see this call site at all — the value rides inside the ``question`` string. That is not a
    hole to be closed by widening that guard; it is why the every-``draw_all``-asserts guard exists.
    But the claim "this site is invisible to the persona guard" is only true while the site actually
    passes no keywords, and nothing else in the suite would notice if it started to. This does.
    """
    function = _function_def(_parse("scripts/phase16_ladder.py"), "build_near_prompt")
    assert function is not None

    calls = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and "build_recall_prompt"
        in (getattr(node.func, "id", None), getattr(node.func, "attr", None))
    ]
    assert calls, "build_near_prompt no longer builds a recall prompt"
    assert all(not call.keywords for call in calls), (
        "build_near_prompt passed a keyword to build_recall_prompt — if that keyword is persona=, "
        "the site is no longer the distance-~2 row and PERSONA_ALLOWLIST is now wrong"
    )


def test_synthetic_fact_order_matches_the_binding_fixture():
    """The material's ordering cannot drift from the fixture it is aligned to (T-16-20).

    ``SYNTHETIC_VALUES[span][i]`` is the material for the fact at position ``i``, so a reordering
    misaligns every value to the wrong fact — silently, with every count still summing correctly.
    The driver commits SLOTS rather than fact ids because each core fact id ends in its own value
    and a literal tuple of ids would embed eight locked values in the driver (T-16-16, the scan
    above). The id -> slot resolution therefore happens HERE, against the lazily-loaded fact set,
    which pins the ordering and the binding in one assertion.
    """
    spec = importlib.util.spec_from_file_location(
        "phase14_factset", _REPO_ROOT / "scripts" / "phase14_factset.py"
    )
    facts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(facts)

    slot_by_id = {fact.id: fact.slot for fact in facts.LOCKED_FACTS}
    core_facts = _fixture()["provenance"]["core_facts"]
    assert len(core_facts) == 8

    assert ladder.SYNTHETIC_FACT_ORDER == tuple(slot_by_id[fact_id] for fact_id in core_facts)
    assert len(set(ladder.SYNTHETIC_FACT_ORDER)) == 8, "one synthetic value per fact, per span"


# ===== 16-05 Task 2 — the vetted material, and the run that produced it =======================

_MATERIAL_PATH = _REPO_ROOT / "results" / "phase16_ladder_material.md"


def _factset():
    """The fact set, loaded INSIDE the test. It is the thing being kept out of the driver."""
    spec = importlib.util.spec_from_file_location(
        "phase14_factset", _REPO_ROOT / "scripts" / "phase14_factset.py"
    )
    facts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(facts)
    return facts


def test_synthetic_values_have_the_declared_token_length():
    """Every committed value is EXACTLY its span, measured — never assumed (PITFALLS-12).

    Span length is the ladder's independent variable (D-11): a "span 5" cell carrying a 6-token
    value is not the rung the pre-registration named, and every reading of where capability dies
    would be off by the same amount. Measured here with the real frozen tokenizer, through the same
    ``token_census`` the vetting run used, so the constant and the report cannot disagree.
    """
    tok = _tokenizer()
    census = _factset().token_census

    for span, values in sorted(ladder.SYNTHETIC_VALUES.items()):
        for value in values:
            n_tokens, roundtrip = census(tok, value)
            assert n_tokens == span, f"{value!r} is {n_tokens} tokens, not {span}"
            assert roundtrip, f"{value!r} does not round-trip exactly — no match on it would mean"


def test_synthetic_values_are_eight_per_span_and_aligned_to_the_fact_order():
    """Three spans, eight values each, all 24 distinct — and every one from its committed pool.

    Distinctness across spans as well as within one: a value shared by two spans would make two
    cells' hits indistinguishable in any per-value grouping of the run's output. Pool membership is
    what makes selection auditable — a value that is not in ``SYNTHETIC_CANDIDATES`` was never
    vetted in the committed order and cannot have been "the first eight survivors".
    """
    values = ladder.SYNTHETIC_VALUES
    assert sorted(values) == list(ladder.LADDER_SPANS)

    flat = [value for span in ladder.LADDER_SPANS for value in values[span]]
    assert all(len(values[span]) == len(ladder.SYNTHETIC_FACT_ORDER) for span in values)
    assert len(set(flat)) == len(flat) == 24

    for span in ladder.LADDER_SPANS:
        pool = ladder.SYNTHETIC_CANDIDATES[span]
        assert set(values[span]) <= set(pool)
        # First-8-survivors in committed order: the selection preserves pool order (T-16-20).
        positions = [pool.index(value) for value in values[span]]
        assert positions == sorted(positions), (
            f"span {span} material is not in committed pool order — selection was re-picked"
        )


def test_synthetic_values_are_recorded_in_the_material_report():
    """The constant and its evidence are one artifact: every value is a SELECTED row.

    And the gate must be shown to have RUN on each of them, not merely to have been available:
    every selected row carries ``clean = True`` with a non-zero probe and completion count, which
    is the property T-16-18 actually needs. A rejection count alone would not give it — the surplus
    rows below would satisfy "something was rejected" even if the probe had been skipped entirely.
    """
    report = _MATERIAL_PATH.read_text(encoding="utf-8")
    rows = [line for line in report.splitlines() if line.startswith("| ") and "**" in line]
    selected = [line for line in rows if "**SELECTED**" in line]
    rejected = [line for line in rows if "**REJECTED**" in line]

    assert len(selected) == 24, f"{len(selected)} SELECTED rows, expected 24"
    assert rejected, "a filter that rejected nothing did not run"

    for span, values in sorted(ladder.SYNTHETIC_VALUES.items()):
        for value in values:
            matching = [line for line in selected if f"`{value}`" in line]
            assert len(matching) == 1, f"span {span} value {value!r}: {len(matching)} SELECTED rows"
            fields = [cell.strip() for cell in matching[0].strip("|").split("|")]
            _index, _candidate, tokens, roundtrip, _slot, probes, completions, clean = fields[:8]
            assert tokens == str(span) and roundtrip == "exact"
            assert clean == "True", f"{value!r} was committed with clean={clean!r}"
            assert int(probes) > 0 and int(completions) > 0, (
                f"{value!r} is in the constant with {probes} probes — it was never gate-cleared"
            )


def test_synthetic_values_are_not_locked_values():
    """No synthetic value may contain, or be contained by, any locked or soft fact value.

    Containment both ways, because either direction breaks a measurement. A synthetic containing a
    locked value would put a taught fact in a ladder prompt — the demo-killing leak. A synthetic
    CONTAINED BY one would make the ladder's substring scoring fire on the base saying the real
    value, so a rung would pass on evidence that has nothing to do with the synthetic span.
    """
    from test_phase14_scoring import embedded_fact_values

    facts = _factset()
    forbidden = tuple(f.value for f in facts.LOCKED_FACTS + facts.SOFT_TIER_FACTS)
    assert len(forbidden) == 10

    # Direction 1 — a locked value embedded anywhere in the driver, the constant included.
    assert embedded_fact_values(ladder, forbidden) == []

    # Direction 2 — a synthetic value embedded inside a locked one, which the scan above cannot see.
    for span, values in sorted(ladder.SYNTHETIC_VALUES.items()):
        for value in values:
            inside = [locked for locked in forbidden if value in locked.lower()]
            assert inside == [], f"span {span} value {value!r} is a substring of {inside}"


def test_main_exists_and_is_guarded():
    """A run driver, not a script that runs on import (T-16-16).

    The ``__main__`` guard is what lets every test in this file load the module with ``importlib``
    and get constants instead of a model load. The torch check is the other half: an import of
    torch at MODULE level would drag the whole runtime into every CPU-only test that touches this
    file, and is the first step of the same drift.
    """
    assert callable(ladder.main)
    assert callable(ladder.vet_synthetic_candidates)

    tree = _parse("scripts/phase16_ladder.py")
    guards = [
        node
        for node in tree.body
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and getattr(node.test.left, "id", None) == "__name__"
    ]
    assert len(guards) == 1, "exactly one `if __name__ == '__main__':` block"
    assert _called_names(guards[0]) == {"main"}

    module_level = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            module_level |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            module_level.add(node.module.split(".")[0])
    assert "torch" not in module_level, f"module-level imports: {sorted(module_level)}"
    assert "phase14_factset" not in module_level and "phase14_factset_gate" not in module_level
