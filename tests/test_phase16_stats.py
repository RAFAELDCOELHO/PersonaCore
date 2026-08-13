"""Phase 16's statistics — the per-fact grouping, the descriptive interval, the inferential gate.

CPU-only, GPU-free, no checkpoint I/O, no generation, no model load. ``scripts/phase16_persistence
.py`` executes nothing at import, so an ``importlib.util.spec_from_file_location`` load here runs
no ``__main__`` guard and no tokenizer.

What is pinned here:
  1. **D-06** — the grouping key is ``fact_id``, and ``sum(k)/sum(n)`` equals ``mean(k_i/9)`` digit
     for digit on the balanced fixture, so the "resolved by arithmetic" claim is a test rather than
     an assertion.
  2. **The TWO-STAGE cluster bootstrap** — facts resampled first (``STATE.md:94``, n = 8), then
     that fact's questions (STAT-01 / D-06). Each stage is pinned from the direction that makes the
     OTHER stage a no-op, so neither can be silently dropped.
  3. **D-08 / D-29** — the exact sign test over all 256 partitions, ties counting AGAINST with
     ``n`` fixed at 8, and the direction filter pinned from BOTH failing directions.
  4. **D-09 / STAT-06** — the Holm family closed at exactly six pairs, statically and at runtime,
     with the 6.7% margin and the ``m = 7`` consequence both pinned by arithmetic.

The scripts-load justification is the one ``tests/test_phase16_driver.py`` already states: the
pre-registration constants MUST live in the committed driver for git history to be the proof.
"""

import ast
import importlib.util
import itertools
import math
import pathlib
import random
import re
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_DRIVER_PATH = _REPO_ROOT / "scripts" / "phase16_persistence.py"
_LADDER_PATH = _REPO_ROOT / "scripts" / "phase16_ladder.py"
_CONTEXT_PATH = (
    _REPO_ROOT
    / ".planning"
    / "phases"
    / "16-weight-vs-prompt-persistence-control"
    / "16-CONTEXT.md"
)


def _load_driver():
    spec = importlib.util.spec_from_file_location("phase16_persistence", _DRIVER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stats = _load_driver()


def _tree(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def _function_def(tree, name):
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _enclosing_functions(tree):
    """``node -> the innermost FunctionDef containing it``, or ``None`` for module scope.

    Same idiom as ``tests/test_phase14_scoring.py::_call_sites``: a module-scope call is recorded
    as ``None`` rather than dropped, because module scope is the most dangerous placement there is.
    """
    owner = {}

    def walk(node, current):
        for child in ast.iter_child_nodes(node):
            inner = child if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) else current
            owner[child] = current if inner is child else inner
            walk(child, inner)

    walk(tree, None)
    return owner


def _call_sites(path, callee):
    """Every ``callee(...)`` call in ``path`` as ``(function name or '<module>', ast.Call)``."""
    tree = _tree(path)
    enclosing = _enclosing_functions(tree)
    sites = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if callee not in (getattr(node.func, "id", None), getattr(node.func, "attr", None)):
            continue
        holder = enclosing.get(node)
        sites.append(("<module>" if holder is None else holder.name, node))
    return sites


def _context_blockquote(anchor):
    """The blockquote following ``anchor`` in ``16-CONTEXT.md``, unwrapped to one line.

    Read from the planning artifact rather than retyped here, because "verbatim" asserted against a
    second hand-typed copy proves only that two copies agree — which is exactly the failure mode a
    verbatim requirement exists to prevent. Byte-for-byte identical helper to the one
    ``tests/test_phase16_driver.py`` uses for D-03.
    """
    body = _CONTEXT_PATH.read_text(encoding="utf-8").split(anchor, 1)[1]
    lines = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith(">"):
            lines.append(stripped.lstrip(">").strip())
        elif lines:
            break
    assert lines, f"no blockquote follows {anchor!r} in 16-CONTEXT.md"
    return " ".join(lines).strip('"')


def _questions(*pairs):
    """Per-question records in ``PER_QUESTION_KEYS`` shape from ``(fact_id, k, n)`` triples."""
    return [
        {"fact_id": fact_id, "split": "held-out", "seed_index": index, "k": k, "n": n}
        for index, (fact_id, k, n) in enumerate(pairs)
    ]


def _balanced_fixture(rates, *, questions_per_fact=13, draws=9):
    """``{fact_id: [(k, 9)] * 13}`` for eight facts — the fixture's real held-out shape."""
    return {f"fact_{index}": [(k, draws)] * questions_per_fact for index, k in enumerate(rates)}


def _per_fact_by_arm(rate_by_arm):
    """``{arm: {fact_id: {"rate": r}}}`` — the shape ``compare_arms`` consumes."""
    return {
        arm: {f"fact_{index}": {"rate": rate} for index, rate in enumerate(rates)}
        for arm, rates in rate_by_arm.items()
    }


# ===== Task 1 — per-fact aggregation, the two-stage bootstrap, the STAT-02 reporting shape =====


def test_aggregation_groups_by_fact_id_not_split():
    """D-06's whole implementation is one substituted grouping key — so pin the substitution.

    Every record here shares one ``split``, so a grouping keyed on ``record["split"]`` would return
    a single bucket named ``"held-out"``. The returned keys must be the fact ids instead.
    """
    grouped = stats.aggregate_by_fact(
        _questions(("cand_a", 4, 9), ("cand_b", 1, 9), ("cand_a", 9, 9)), tier="held-out"
    )
    assert sorted(grouped) == ["cand_a", "cand_b"]
    assert "held-out" not in grouped
    assert grouped["cand_a"]["k"] == 13
    assert grouped["cand_a"]["n_draws"] == 18
    assert grouped["cand_a"]["n_questions"] == 2
    assert grouped["cand_b"]["n_answerable"] == 1


def test_aggregation_refuses_a_mixed_tier():
    """D-10 forbids pooling taught with held-out — one stray record aborts rather than merges."""
    records = _questions(("cand_a", 4, 9))
    records[0]["split"] = "taught"
    try:
        stats.aggregate_by_fact(records, tier="held-out")
    except SystemExit as exit_:
        assert "D-10" in str(exit_)
    else:  # pragma: no cover - the assertion below is the failure report
        raise AssertionError("a taught record entered the held-out aggregation silently")


def test_sum_over_draws_equals_mean_of_per_question_rates_on_the_balanced_fixture():
    """D-06 says the denominator question is resolved BY ARITHMETIC — so compute both and compare.

    The fixture is perfectly balanced (13 held-out questions per core fact, 9 draws each), so
    ``sum(k)/sum(n)`` and ``mean(k_i/9)`` are the same number. Exact equality, not ``approx``: with
    a common denominator of 9 the two expressions differ only in association order, and a tolerance
    here would hide the very drift the claim rests on.
    """
    per_question_k = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 4, 1)
    records = _questions(*(("cand_a", k, 9) for k in per_question_k))
    grouped = stats.aggregate_by_fact(records, tier="held-out")["cand_a"]

    pooled = grouped["k"] / grouped["n_draws"]
    mean_of_rates = sum(k / 9 for k in per_question_k) / len(per_question_k)
    assert grouped["n_questions"] == 13
    assert grouped["n_draws"] == 117
    assert pooled == mean_of_rates == grouped["rate"]


def test_cluster_bootstrap_is_deterministic_under_its_seed():
    """Two calls at one seed return identical bounds — the interval is byte-reproducible."""
    fixture = _balanced_fixture((0, 1, 2, 4, 5, 7, 8, 9))
    first = stats.cluster_bootstrap(fixture, resamples=400, seed=1337)
    second = stats.cluster_bootstrap(fixture, resamples=400, seed=1337)
    assert first == second
    assert first != stats.cluster_bootstrap(fixture, resamples=400, seed=42)
    assert first[0] < first[1]


def test_cluster_bootstrap_resamples_facts_first_stage_one():
    """STATE.md:94 — the FACTS are resampled (n = 8). Pinned where stage 2 is a NO-OP.

    Every question inside a fact is identical here, so stage 2 cannot move the statistic at all: a
    question-only bootstrap would return the same rate 400 times and a zero-width interval. The
    facts differ from each other, so an interval with real width can ONLY have come from stage 1.
    """
    homogeneous = _balanced_fixture((0, 0, 1, 3, 6, 9, 9, 9))
    lo, hi = stats.cluster_bootstrap(homogeneous, resamples=400, seed=1337)
    assert hi - lo > 0.05, (
        "the bootstrap returned an interval a question-only resample could have produced on a "
        "fixture where every question inside a fact is identical — stage 1 is not running, and "
        "the interval is conditional on these exact 8 facts (STATE.md:94)"
    )

    # The stage-2-only counterfactual, computed inline so the comparison is visible rather than
    # asserted: hold the facts FIXED and resample only questions, which is what the 16-09 plan
    # text originally specified and what the wave-8 user decision corrected.
    rng = random.Random(1337)
    fact_ids = sorted(homogeneous)
    stage_two_only = set()
    for _ in range(400):
        numerator = denominator = 0
        for fact_id in fact_ids:  # FIXED — no stage 1.
            questions = homogeneous[fact_id]
            for _ in range(len(questions)):
                k, n = questions[rng.randrange(len(questions))]
                numerator += k
                denominator += n
        stage_two_only.add(numerator / denominator)
    assert len(stage_two_only) == 1, "the stage-2-only counterfactual was not degenerate"


def test_cluster_bootstrap_resamples_questions_within_facts_stage_two():
    """STAT-01 / D-06 — the QUESTIONS are resampled. Pinned where stage 1 is a NO-OP.

    Every fact is identical to every other one here, so stage 1 cannot move the statistic: drawing
    any 8 facts with replacement gives the same pooled rate. The questions vary INSIDE each fact,
    so an interval with real width can ONLY have come from stage 2.
    """
    varied = [(k, 9) for k in (0, 0, 0, 1, 2, 4, 7, 9, 9, 9, 5, 3, 1)]
    identical_facts = {f"fact_{index}": list(varied) for index in range(8)}
    lo, hi = stats.cluster_bootstrap(identical_facts, resamples=400, seed=1337)
    assert hi - lo > 0.01, (
        "the bootstrap returned a degenerate interval on a fixture whose facts are identical and "
        "whose questions vary — stage 2 is not running, so STAT-01's question unit is not resampled"
    )


def test_cluster_bootstrap_differs_from_a_naive_unclustered_resample():
    """Pooling all 104 questions and ignoring facts is a DIFFERENT interval — and a narrower one.

    The naive resample treats clustered questions as one exchangeable pool, which is the mistake
    STAT-01's rationale names. It is computed inline here so the divergence is measured rather than
    assumed.
    """
    fixture = _balanced_fixture((0, 1, 2, 4, 5, 7, 8, 9))
    clustered = stats.cluster_bootstrap(fixture, resamples=600, seed=1337)

    pooled = [pair for questions in fixture.values() for pair in questions]
    rng = random.Random(1337)
    rates = []
    for _ in range(600):
        numerator = denominator = 0
        for _ in range(len(pooled)):
            k, n = pooled[rng.randrange(len(pooled))]
            numerator += k
            denominator += n
        rates.append(numerator / denominator)
    rates.sort()
    naive = (rates[int(0.025 * len(rates))], rates[int(0.975 * len(rates))])

    assert clustered != naive
    assert (clustered[1] - clustered[0]) > (naive[1] - naive[0]), (
        "the clustered interval is not wider than the unclustered one — the whole reason STAT-01 "
        "forbids the draw as the unit is that ignoring clustering makes intervals too narrow"
    )


def test_report_proportion_never_renders_a_bare_zero_percent():
    """STAT-02: no bare ``0%`` in any committed report or figure — pinned by regex, not by care."""
    row = stats.report_proportion(0, 104, 936)
    assert "rule_of_three_upper" in row
    assert row["rule_of_three_upper"] == 3.0 / 104
    assert not re.search(r"\b0(\.0+)?%", row["formatted"]), row["formatted"]
    assert "0/104 questions" in row["formatted"]
    assert f"{row['wilson_upper_95']:.6f}" in row["formatted"]


def test_report_proportion_omits_rule_of_three_when_successes_are_nonzero():
    """``3/n`` is the ZERO-success ceiling. Reporting it beside a nonzero rate would misname it."""
    assert "rule_of_three_upper" not in stats.report_proportion(37, 104, 936)


def test_wilson_is_labelled_as_the_independence_assuming_width():
    """T-16-41 — a bound with no label reads as the phase's width, and Wilson is not it."""
    for row in (stats.report_proportion(0, 104, 936), stats.report_proportion(37, 104, 936)):
        assert row["wilson_label"] == stats.WILSON_LABEL
        assert row["wilson_label"]
        assert "INDEPENDENT" in row["wilson_label"]
        assert "cluster_bootstrap" in row["wilson_label"]


def test_report_proportion_carries_both_denominators():
    """T-16-40 — questions for the interval, draws for the raw count, both on every rate."""
    row = stats.report_proportion(37, 104, 936)
    assert row["n_questions"] == 104
    assert row["n_draws"] == 936
    assert row["n_questions"] != row["n_draws"]
    assert row["rate"] == 37 / 104
    assert "104 questions" in row["formatted"]
    assert "936 draws" in row["formatted"]


def test_report_proportion_rejects_a_draw_count_passed_as_successes():
    """``successes`` is in the STAT-01 QUESTION unit — a draw count there is a silent rate > 1."""
    try:
        stats.report_proportion(326, 104, 936)
    except SystemExit as exit_:
        assert "STAT-01" in str(exit_)
    else:  # pragma: no cover
        raise AssertionError("a draw-unit numerator was accepted against a question denominator")


def test_bootstrap_names_the_percentile_method_and_its_small_n_bias():
    """The Phase 15 precedent is to NAME the bias, never to upgrade the method after the result."""
    source = _DRIVER_PATH.read_text(encoding="utf-8")
    assert stats.BOOTSTRAP_RESAMPLES == 10000
    assert stats.BOOTSTRAP_SEED == 1337
    assert "percentile" in stats.BOOTSTRAP_METHOD
    assert "BIASED AND ANTI-CONSERVATIVE AT SMALL n" in source
    assert "BCa" in source
    assert re.search(r"\bbias\b", source)


def test_no_unreachable_coverage_floor_is_asserted_anywhere():
    """The 6435 fact-multisets are NOT equiprobable, so a ``6435 * 0.95`` floor is unreachable.

    ``C(8 + 8 - 1, 8) = C(15, 8) = 6435`` is the FACT layer's distinct-outcome count, derived here
    rather than typed. At 10,000 resamples only ~57% of those multisets are ever drawn, so any
    coverage floor anchored near 6435 would fail by construction on a correct implementation. This
    test exists so a future editor who reaches for one finds the reason first.
    """
    assert math.comb(15, 8) == 6435
    assert len(list(itertools.combinations_with_replacement(range(8), 8))) == 6435

    # NOT equiprobable: a multiset's probability carries its multinomial weight. The balanced draw
    # has 8! orderings and the all-same draw has 1, so coupon-collector reasoning over 6435
    # uniform items does not apply.
    assert math.factorial(8) > 1

    # 6435 must not reach EXECUTABLE code in the driver. Same idiom as 16-08's
    # `test_chance_floor_literal_matches_the_pool`: the prose that explains why the floor is
    # unreachable belongs in the docstring, and a docstring is an `ast.Constant` string — never a
    # number. A numeric 6435 anywhere in the module is the floor arriving.
    numbers = {
        node.value
        for node in ast.walk(_tree(_DRIVER_PATH))
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float))
    }
    assert 6435 not in numbers


def test_stats_use_only_stdlib_and_erasure_gate():
    """STAT-04 — no scipy, no numpy RNG, and the bounds are IMPORTED rather than redefined."""
    tree = _tree(_DRIVER_PATH)
    imported = set()
    from_erasure_gate = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
            if node.module == "erasure_gate":
                from_erasure_gate.update(alias.name for alias in node.names)

    assert "scipy" not in imported
    assert "numpy" not in imported
    assert {"wilson_upper_bound", "rule_of_three"} <= from_erasure_gate

    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert not ({"wilson_upper_bound", "rule_of_three"} & defined), (
        "a bound was re-implemented in this module instead of imported from erasure_gate — D-16's "
        "rule is import the instrument, never copy it, or the two silently diverge"
    )

    # The bootstrap's RNG is stdlib and LOCAL: `random.Random(seed)`, never a global seeding call
    # and never a numpy generator.
    bootstrap = _function_def(tree, "cluster_bootstrap")
    calls = {
        f"{getattr(call.func, 'attr', None)}"
        for call in ast.walk(bootstrap)
        if isinstance(call, ast.Call)
    }
    assert "Random" in calls
    assert "seed" not in calls
    assert "default_rng" not in calls


# ===== Task 2 — the exact sign test over 256 partitions, and Holm across exactly 6 pairs =====

UNANIMITY_P = 0.0078125
SEVEN_OF_EIGHT_P = 0.0703125


def test_sign_test_reproduces_the_verified_enumeration():
    """The three numbers D-09 verified by enumeration — two from production, one counterfactual.

    ``n=8 pos=8 -> 0.0078125`` and ``n=8 pos=7 -> 0.0703125`` come from ``sign_test_exact``.

    ``n=7 pos=7 -> 0.0156250`` is the **D-08 COUNTERFACTUAL** — the number the discarded-ties rule
    WOULD have produced — and it is enumerated INLINE below rather than obtained from the
    production function. ``sign_test_exact`` takes no ``n`` parameter and must not grow one:
    ``SIGN_TEST_N = 8`` is module-level and pre-registered (D-08), so adding an ``n=`` argument to
    make this test pass would install precisely the knob D-08 locks — and the test written to pin
    the counterfactual would have become the reason the knob exists.
    """
    assert stats.sign_test_exact([1] * 8) == UNANIMITY_P
    assert stats.sign_test_exact([1] * 7 + [-1]) == SEVEN_OF_EIGHT_P

    # The counterfactual, enumerated here and only here: all 2**7 sign partitions at n = 7, those
    # at least as extreme as 7/7 in either tail, over the 128 equally likely partitions.
    n = 7
    extreme = sum(
        1
        for partition in itertools.product((0, 1), repeat=n)
        if abs(sum(partition) - n / 2) >= abs(n - n / 2)
    )
    assert extreme / 2**n == 0.015625
    assert extreme / 2**n > stats.HOLM_ALPHA / len(stats.HOLM_FAMILY_PAIRS), (
        "the discarded-ties rule would have been UNCLEARABLE: one tie drops n to 7, where even "
        "unanimity gives 0.015625 against a first-step alpha of 0.0083333 (D-08)"
    )

    assert "n" not in {
        arg.arg for arg in _function_def(_tree(_DRIVER_PATH), "sign_test_exact").args.args
    }


def test_ties_count_against_and_do_not_shrink_n():
    """D-08 / T-16-39 — a tie is folded in AGAINST the alternative, and the denominator stays 8."""
    with_tie = stats.sign_test_exact([1] * 7 + [0])
    with_negative = stats.sign_test_exact([1] * 7 + [-1])
    assert with_tie == with_negative == SEVEN_OF_EIGHT_P
    assert stats.SIGN_TEST_N == 8

    # A 7-long sequence is refused outright: nothing may shrink the pre-registered denominator.
    try:
        stats.sign_test_exact([1] * 7)
    except SystemExit as exit_:
        assert "D-08" in str(exit_)
    else:  # pragma: no cover
        raise AssertionError("a 7-sign sequence was accepted, so the denominator is not fixed")


def test_an_all_tie_pair_is_defined_and_scores_one():
    """D-08's expected prompt-stuffed x base-neither case, and the hole D-29 closes.

    Eight ties give ``p = 1.0`` — not a ``ZeroDivisionError``, not ``None``, and NOT ``0.0078125``.
    Phase 14's committed 1/1944 makes near-total ties on that pair the predicted outcome, so this
    is the case the family most likely actually hits.
    """
    p = stats.sign_test_exact([0] * 8)
    assert p == 1.0
    assert p != UNANIMITY_P


def test_the_direction_filter_cannot_silently_invert():
    """D-29 / T-16-39b — BOTH failing directions are pinned, so the filter cannot invert.

    An implementation that flipped the comparison would pass one of these and fail the other, which
    is why one of them alone is not enough.
    """
    assert stats.sign_test_exact([0] * 8) == 1.0
    assert stats.sign_test_exact([-1] * 8) == 1.0


def test_p_is_one_below_the_midpoint():
    """``1.0`` at or below n/2, and a value under 1.0 ONLY above it (D-29)."""
    assert stats.sign_test_exact([1] * 4 + [-1] * 4) == 1.0
    assert stats.sign_test_exact([1] + [-1] * 7) == 1.0
    for positives in range(9):
        p = stats.sign_test_exact([1] * positives + [-1] * (8 - positives))
        if positives > stats.SIGN_TEST_N / 2:
            assert p < 1.0, positives
        else:
            assert p == 1.0, positives


def test_sign_test_enumerates_rather_than_using_a_closed_form():
    """D-09 specifies the enumeration, and the enumeration is what these tests pin."""
    body = _function_def(_tree(_DRIVER_PATH), "sign_test_exact")
    calls = {
        getattr(call.func, "attr", None) for call in ast.walk(body) if isinstance(call, ast.Call)
    }
    assert "product" in calls, "the 256 partitions are not enumerated"
    assert "comb" not in calls, "a closed-form binomial stood in for the enumeration"
    powers = [
        node
        for node in ast.walk(body)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow)
    ]
    assert any(getattr(node.right, "id", None) == "SIGN_TEST_N" for node in powers), (
        "the denominator is not `2 ** SIGN_TEST_N` — a retyped 256 is a number free to stop "
        "agreeing with the n it claims to enumerate"
    )


def test_sign_test_alternative_is_declared_for_every_holm_pair():
    """T-16-39c / STAT-05 — the direction is a committed literal, not a post-hoc choice."""
    assert set(stats.SIGN_TEST_ALTERNATIVE) == set(stats.HOLM_FAMILY_PAIRS)
    assert len(stats.SIGN_TEST_ALTERNATIVE) == 6
    for (first, second), declaration in stats.SIGN_TEST_ALTERNATIVE.items():
        assert declaration == f"{first} exceeds {second}"

    # Module-level ONLY: an assignment inside any function would let the direction be built after
    # a run starts, which is the whole thing this constant exists to prevent.
    tree = _tree(_DRIVER_PATH)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for inner in ast.walk(node):
            targets = []
            if isinstance(inner, ast.Assign):
                targets = inner.targets
            elif isinstance(inner, (ast.AugAssign, ast.AnnAssign)):
                targets = [inner.target]
            assert "SIGN_TEST_ALTERNATIVE" not in {
                getattr(target, "id", None) for target in targets
            }, f"SIGN_TEST_ALTERNATIVE is assigned inside {node.name}"


def test_only_eight_over_eight_clears_the_first_holm_step():
    """D-09's 6.7% margin — computed from the constants, never retyped from the prose."""
    first_step_alpha = stats.HOLM_ALPHA / len(stats.HOLM_FAMILY_PAIRS)
    assert UNANIMITY_P < first_step_alpha
    assert SEVEN_OF_EIGHT_P > first_step_alpha

    margin = first_step_alpha - UNANIMITY_P
    assert round(margin, 6) == 0.000521
    assert round(margin / UNANIMITY_P, 3) == 0.067  # 6.7% relative to the achievable p


def test_family_of_seven_would_kill_the_headline():
    """D-09's load-bearing arithmetic, so a 7th gated comparison fails a TEST, not a run.

    Both halves are asserted. The consequence: one more member prices alpha below the achievable
    p, at every possible outcome including perfect unanimity. And the present state: the family as
    committed still clears. Adding a 7th pair turns the second assertion red immediately.
    """
    m = len(stats.HOLM_FAMILY_PAIRS)
    assert stats.HOLM_ALPHA / (m + 1) < UNANIMITY_P
    assert stats.HOLM_ALPHA / 7 < UNANIMITY_P
    assert stats.HOLM_ALPHA / m > UNANIMITY_P, (
        f"the family is at m = {m}, where alpha = {stats.HOLM_ALPHA / m} does not exceed the "
        f"achievable p of {UNANIMITY_P} — the headline is dead arithmetically at every outcome"
    )


def test_holm_family_is_exactly_six_pairs():
    """D-09 — C(4, 2) over CONDITION_ORDER, closed, distinct, and priced at its own length."""
    pairs = stats.HOLM_FAMILY_PAIRS
    assert len(pairs) == 6
    assert len(set(pairs)) == 6
    assert isinstance(pairs, tuple)
    for first, second in pairs:
        assert first in stats.CONDITION_ORDER
        assert second in stats.CONDITION_ORDER
        assert first != second
    assert set(pairs) == set(itertools.combinations(stats.CONDITION_ORDER, 2))

    # An arm count that disagrees with the pre-registration aborts rather than repricing alpha.
    three_arms = _per_fact_by_arm(
        {arm: (0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2) for arm in stats.CONDITION_ORDER[:3]}
    )
    try:
        stats.compare_arms(three_arms, tier="held-out")
    except SystemExit as exit_:
        assert "prices alpha" in str(exit_)
    else:  # pragma: no cover
        raise AssertionError("compare_arms accepted three arms and priced a six-pair family")


def test_holm_reads_the_family_length_rather_than_a_retyped_six():
    """A retyped divisor is a number free to stop agreeing with the family it prices."""
    body = _function_def(_tree(_DRIVER_PATH), "holm")
    divisors = [
        node.right
        for node in ast.walk(body)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)
    ]
    assert divisors, "holm computes no alpha at all"
    for divisor in divisors:
        assert not (isinstance(divisor, ast.Constant) and divisor.value == 6)


def test_holm_stops_at_the_first_failure():
    """Step-down: once one hypothesis is retained, every LATER one is retained too.

    The last p here is ``0.04`` against a final-step alpha of ``0.05/1``, so on its own it would
    clear comfortably. It is retained anyway, because the SECOND-smallest failed. That retention is
    the property — an implementation that simply compared each p against its own step alpha would
    reject it and pass every other assertion in this file.
    """
    pairs = list(stats.HOLM_FAMILY_PAIRS)
    p_values = dict(zip(pairs, [UNANIMITY_P, 0.012, 0.013, 0.014, 0.015, 0.04]))
    results = stats.holm(p_values)

    assert [rejected for *_, rejected in results] == [True, False, False, False, False, False]
    assert results[0][1] == UNANIMITY_P
    assert results[0][2] == stats.HOLM_ALPHA / 6
    assert results[1][2] == stats.HOLM_ALPHA / 5
    assert [p for _, p, _, _ in results] == sorted(p for _, p, _, _ in results)

    last_pair, last_p, last_alpha, last_rejected = results[-1]
    assert last_p < last_alpha, "the retention case was not constructed"
    assert last_rejected is False, (
        f"{last_pair} was rejected at p = {last_p} < alpha {last_alpha} even though an earlier "
        "hypothesis was retained — the step-down stop is not implemented"
    )

    # And the family as committed: six unanimous p-values clear every step, 0.05/6 through 0.05/1.
    all_unanimous = dict(zip(pairs, [UNANIMITY_P] * 6))
    assert all(rejected for *_, rejected in stats.holm(all_unanimous))


def test_holm_refuses_a_family_of_the_wrong_size():
    """A family priced at 6 and populated at 5 is not the test that was registered."""
    short = dict(zip(list(stats.HOLM_FAMILY_PAIRS)[:5], [UNANIMITY_P] * 5))
    try:
        stats.holm(short)
    except SystemExit as exit_:
        assert "D-09" in str(exit_)
    else:  # pragma: no cover
        raise AssertionError("holm priced a six-pair family against five p-values")


def test_compare_arms_produces_the_predicted_unanimous_verdict():
    """The end-to-end shape on the outcome 16-CONTEXT.md predicts: A over everything, 8/8."""
    per_fact_by_arm = _per_fact_by_arm(
        {
            "adapter-only": (0.615, 0.590, 0.504, 0.316, 0.197, 0.385, 0.128, 0.051),
            "embedding-cosine": (0.10, 0.10, 0.10, 0.05, 0.05, 0.05, 0.05, 0.05),
            "base-neither": (0.01, 0.01, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            "prompt-stuffed": (0.0,) * 8,
        }
    )
    verdict = stats.compare_arms(per_fact_by_arm, tier="held-out")

    assert verdict["gated"] is True
    assert verdict["tier"] == "held-out"
    assert len(verdict["p_values"]) == 6
    assert verdict["p_values"][("adapter-only", "prompt-stuffed")] == UNANIMITY_P
    assert verdict["signs"][("adapter-only", "prompt-stuffed")] == (1,) * 8
    # base-neither vs prompt-stuffed: two facts favour, six tie -> 2/8, below the midpoint -> 1.0.
    assert verdict["p_values"][("base-neither", "prompt-stuffed")] == 1.0
    assert verdict["alternative"] == dict(stats.SIGN_TEST_ALTERNATIVE)
    assert [row[0] for row in verdict["holm"]] and len(verdict["holm"]) == 6


def test_compare_arms_refuses_to_gate_the_taught_tier():
    """D-07 — gating both tiers takes the family to 12, where unanimity itself fails."""
    per_fact_by_arm = _per_fact_by_arm(
        {arm: (0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2) for arm in stats.CONDITION_ORDER}
    )
    try:
        stats.compare_arms(per_fact_by_arm, tier="taught")
    except SystemExit as exit_:
        assert "0.0041667" in str(exit_)
    else:  # pragma: no cover
        raise AssertionError("the taught tier was gated, taking the Holm family from 6 to 12")


def test_taught_tier_carries_the_verbatim_clause_and_is_not_gated():
    """D-07's clause byte-for-byte against ``16-CONTEXT.md``, and no verdict machinery attached."""
    assert stats.TAUGHT_TIER_STATUS == _context_blockquote("- **D-07:**")

    per_fact_by_arm = _per_fact_by_arm(
        {
            "adapter-only": (0.810, 0.746, 0.643, 0.516, 0.508, 0.452, 0.143, 0.119),
            "embedding-cosine": (0.10, 0.10, 0.10, 0.05, 0.05, 0.05, 0.05, 0.05),
            "base-neither": (0.01, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            "prompt-stuffed": (0.0,) * 8,
        }
    )
    replication = stats.taught_replication(per_fact_by_arm)

    assert replication["gated"] is False
    assert replication["tier"] == "taught"
    assert replication["status"] == stats.TAUGHT_TIER_STATUS
    assert "não gate" in replication["status"]
    # No alpha, no rejection flag, no Holm result — nothing that could be read as a verdict.
    assert "holm" not in replication
    assert "alpha" not in replication
    assert len(replication["p_values"]) == 6


def test_fact_signs_refuses_an_unpaired_or_wrong_sized_comparison():
    """PERS-02 pairs the arms; D-08 fixes n at 8. Both are aborts, not warnings."""
    pair = ("adapter-only", "prompt-stuffed")
    unpaired = _per_fact_by_arm({"adapter-only": (0.9,) * 8, "prompt-stuffed": (0.1,) * 8})
    del unpaired["prompt-stuffed"]["fact_7"]
    try:
        stats.fact_signs(unpaired, pair)
    except SystemExit as exit_:
        assert "unpaired" in str(exit_)
    else:  # pragma: no cover
        raise AssertionError("an unpaired fact set produced signs anyway")

    seven = _per_fact_by_arm({"adapter-only": (0.9,) * 7, "prompt-stuffed": (0.1,) * 7})
    try:
        stats.fact_signs(seven, pair)
    except SystemExit as exit_:
        assert "D-08" in str(exit_)
    else:  # pragma: no cover
        raise AssertionError("a 7-fact comparison produced signs, so n is not fixed at 8")
