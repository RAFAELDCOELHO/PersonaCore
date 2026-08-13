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
