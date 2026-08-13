"""PERS-01 capability ladder — the PRE-REGISTRATION: cell thresholds and cell arithmetic.

Committed BEFORE the run it judges (STAT-05, D-14). Every number in this module is derived from
material ALREADY PUBLISHED in this repository — the committed Phase 14 fairness-control result and
the committed fixture's core question count — and none of it is derived from any Phase 16
measurement. Git history is the proof: this file lands before the ladder produces a single number
that these thresholds judge.

Nothing executes at import. Constants and pure functions only (the ``finetune_ab.py`` "gate
formulas as pure functions" precedent), so an ``importlib`` load in a CPU-only test runs no guard,
no model load and no generation. ``main()`` arrives with the run driver, under a ``__main__`` guard.

LAZY-IMPORT RULE — inherited, and load-bearing here. ``phase14_factset`` and
``phase14_factset_gate`` may be imported ONLY inside functions. The gate imports the fact set at
MODULE level, so a module-level import of the gate would pull the locked values into this driver by
a transitive edge — into its address space and into the docstring surface the clean-room scan
walks. ``tests/test_phase16_ladder.py`` enforces both halves (T-16-16).

Bounds come from ``scripts/erasure_gate.py`` (PREREG-01, stdlib only). Zero new dependencies —
STAT-04, and this project has already declined a statistics package in committed code more than
once, so taking one for the milestone whose entire output is trust in a measurement would retcon
both refusals.
"""

import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# `scripts/` is sys.path[0] only when a script in it is run DIRECTLY; an importlib-loaded test
# harness gets no such entry (personalize_demo.py:96-99 precedent). Insert it explicitly so both
# paths reach the sibling pre-registration module.
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from erasure_gate import rule_of_three, wilson_upper_bound  # noqa: E402  (needs the insert above)

# =============================================================================================
# PERS-01 capability-ladder pre-registration (STAT-05)
# =============================================================================================
#
# THE FLOOR. results/phase14_recall_report.md:378 recorded ONE hit across 1944 draws for the
# D-11.1 fairness control. 1944 = 216 questions x 9 draws, and a single hit across all draws means
# exactly one question had k >= 1 -- so n_answerable = 1 over 216 questions. The conversion from
# the published draw count to the STAT-01-legal QUESTION unit is ARITHMETIC on a committed number,
# not a re-measurement, and it matters: the draw-unit bound is roughly nine times tighter and would
# make the prompt arm look far more definitively at zero than the legal unit supports.
#
# The anchor is deliberately the COMMITTED floor and NEVER the post-fix fairness-control re-run
# (D-13). A threshold anchored to a number this phase measures is a threshold set after seeing
# data, which is the motivated-analysis failure pre-registration exists to prevent. The re-run
# produces a REPORTED DELTA, never a constant.
LADDER_FLOOR_SOURCE = "results/phase14_recall_report.md:378 (Phase 14 Control 1, 1/1944 draws)"
LADDER_FLOOR_ANSWERABLE = 1
LADDER_FLOOR_QUESTIONS = 216
LADDER_FLOOR_UPPER_95 = 0.020481915502612365  # erasure_gate.wilson_upper_bound(1, 216)

# CHOICE 1 (RESEARCH Assumptions Log A1) -- cell size n = the FULL core set: 112 core_taught + 104
# core_held_out in results/phase16_recall_sample.json. Reason: identical to the floor's n and to
# the top rung's n, which is what makes the comparison apples-to-apples and what D-15's
# proxy-validity check requires. Cost is ~80 min of ladder wall clock on top of the ~39 min
# four-arm run; D-05 records the run as not cost-constrained. This is the RECORDED choice, not one
# discovered after the fact. (RESEARCH's table gives k_min for six smaller n values; the n = 8 row
# is the degeneracy proof -- there a SINGLE hit clears the bound.)
LADDER_CELL_QUESTIONS = 216

# Same draw count as the floor, in every cell. n_answerable is a max-over-draws statistic, so its
# noise floor scales with the number of draws: the same count at 4 draws is a DIFFERENT quantity
# and is not comparable to the floor. Shaving draws to save wall clock is the anti-pattern here.
LADDER_CELL_DRAWS = 9  # 1 greedy + phase14_recall.N_SEEDED_SAMPLES

# CHOICE 2 (RESEARCH Assumptions Log A4) -- multiplicity is PRICED INTO z rather than disclosed in
# prose. Six cells each judged one-sided at 95% carry ~26% probability that at least one clears
# under a true floor null, and a false pass licenses the STRONGER headline -- the over-licensing
# direction this whole milestone exists to avoid. The one-sided 1 - 0.05/6 quantile prices that in
# for two extra questions.
#
# It is a CHOICE OF LITERAL, not a hypothesis test: no p-value is computed here and no verdict is
# emitted, so D-09's Holm family stays closed at exactly the 6 arm pairs and STAT-06 is untouched.
LADDER_CELL_Z = 2.393979799818510  # statistics.NormalDist().inv_cdf(1 - 0.05/6)

# CHOICE 3 (RESEARCH Open Question 1) -- ONE literal for all seven rungs, top rung included. This
# is the smallest k whose one-sided lower bound at LADDER_CELL_QUESTIONS clears the floor's upper
# bound. It is 10 whether multiplicity is priced at 6 cells (z above) or at 7 rungs (z = 2.449998),
# so a single literal costs nothing and removes an ambiguity that would otherwise be resolved after
# seeing a number.
#
# tests/test_phase16_ladder.py::test_pass_k_is_the_derived_minimum recomputes it from
# erasure_gate.wilson_upper_bound and asserts equality, so the literal cannot silently drift from
# its derivation (T-16-13); test_pass_k_is_insensitive_to_family_size blocks moving it by
# re-arguing the family size.
#
# Calibration sanity: 10 of 216 questions answerable at least once across 9 draws is ~4.6%, an
# order of magnitude below Phase 14's adapter held-out rate. A passing cell is a genuinely low bar
# -- the ladder asks "is this arm off the floor?", never "is this arm as good as the weights".
LADDER_CELL_PASS_K = 10

# =============================================================================================
# The rung lattice, pre-committed (D-11)
# =============================================================================================
#
# 2-D grid: span length x approximate token distance from the value to the <|assistant|> trigger,
# with the NATURAL question framing held constant in every cell. Not distance-only: the real taught
# values are 4-8 tokens over a 547-id near-character vocabulary in a 6-layer model, so span length
# is the primary suspect for where capability dies, and a distance-only ladder failing everywhere
# could not distinguish "cannot copy 5 tokens" from "cannot use context" -- which license different
# headlines. Not instructed-copy either: that framing is out of distribution for this model, so its
# failure cannot separate incapacity from instruction-following failure and licenses nothing.
LADDER_SPANS = (1, 2, 5)  # token lengths of the in-context span
LADDER_DISTANCES = (2, 30)  # approximate token distance from the value to <|assistant|>

# The top rung is the fairness control re-run post-fix (D-13): REAL taught values, distance ~30,
# span median 5. It can never be arm B -- PERS-01 requires the ladder recorded before any
# comparison is scored, so a top rung taken from the comparison would be circular.
TOP_RUNG = "fairness-control-rerun"

# Easiest to hardest, SPAN-MAJOR then distance. Span dominates distance in the licensing order for
# the reason above: span length is where capability is expected to die at this scale, so the rung
# that survives longest is the one whose span is shortest. Pre-committed precisely so that "the
# highest passed rung" -- the sole input to licensed_headline -- is not decided after seeing which
# cells passed.
RUNG_DIFFICULTY_ORDER = (
    (1, 2),
    (1, 30),
    (2, 2),
    (2, 30),
    (5, 2),
    (5, 30),
    TOP_RUNG,
)


# ===== Cell arithmetic (pure functions over a question count) =================================


def cell_passed(n_answerable, n_questions=LADDER_CELL_QUESTIONS):
    """One ladder cell's LICENSING decision. NOT a hypothesis test (STAT-06 / D-09).

    Returns ``(passed, lower_bound)``. The integer literal ``LADDER_CELL_PASS_K`` is the gate; the
    bound is its derivation, pinned by ``tests/test_phase16_ladder.py`` so the two cannot drift
    apart. The bound is one-sided and computed by the complement idiom this repository already
    uses at ``erasure_gate.erasure_is_worth_attempting`` — Wilson rather than Wald because Wald
    degenerates to a useless zero-width interval at zero successes, which is the case a floor-level
    ladder cell hits most often.

    ``n_answerable`` counts QUESTIONS (STAT-01), never draws: a question is answerable if ANY of
    its draws contained the value. That is the statistic the shared instrument already computes at
    ``phase14_recall.run_fairness_control``, and it is the statistic the floor is expressed in.
    """
    lower = 1.0 - wilson_upper_bound(n_questions - n_answerable, n_questions, LADDER_CELL_Z)
    return n_answerable >= LADDER_CELL_PASS_K, lower


def cell_report(n_answerable, n_questions=LADDER_CELL_QUESTIONS):
    """One cell's reportable row: a denominator and a bound, always (STAT-02).

    Never a bare zero rate. A cell scoring nothing still reports its denominator, its Wilson upper
    bound and the rule-of-three ceiling — the two disagree slightly, and publishing both with the
    gate's own bound named is what stops the quieter of them being chosen after the fact.

    ``wilson_upper_95`` is the plain one-sided 95% bound (``erasure_gate``'s default z), reported
    for comparability with every other rate in this milestone. ``lower_bound`` is the gate's own
    bound at ``LADDER_CELL_Z``, which is a tighter quantile because it carries the family pricing.
    They answer different questions and are therefore both present.
    """
    passed, lower = cell_passed(n_answerable, n_questions)
    row = {
        "answerable": n_answerable,
        "questions": n_questions,
        "rate": n_answerable / n_questions,
        "wilson_upper_95": wilson_upper_bound(n_answerable, n_questions),
        "lower_bound": lower,
        "passed": passed,
    }
    if n_answerable == 0:  # never a bare zero rate
        row["rule_of_three_upper"] = rule_of_three(n_questions)
    return row


def format_cell(row):
    """The report line for one cell, FORMATTED from the row and the constants.

    Every number here is interpolated, never typed. A retyped threshold in a report line is a
    number free to drift from the constant it claims to state, which is the failure T-16-15 names
    and which ``test_licensed_headline_retypes_no_threshold_literal`` forbids structurally.
    """
    parts = [
        f"{row['answerable']}/{row['questions']} questions answerable",
        f"rate {row['rate']:.6f}",
        f"one-sided 95% Wilson upper {row['wilson_upper_95']:.6f}",
        f"gate lower bound {row['lower_bound']:.6f} at z={LADDER_CELL_Z:.6f}",
    ]
    if "rule_of_three_upper" in row:
        parts.append(f"rule-of-three upper {row['rule_of_three_upper']:.6f}")
    parts.append(f"{'PASS' if row['passed'] else 'FAIL'} (gate: k >= {LADDER_CELL_PASS_K})")
    return " | ".join(parts)


# =============================================================================================
# The licence (D-14): what the phase is allowed to say, branching on the highest passed rung
# =============================================================================================
#
# Each branch statement is a module-level constant so the TEXT is auditable independently of the
# dispatch logic, and so a reviewer can diff the prose without reading the control flow. Every
# statement says what it does NOT license as well as what it does -- an over-read headline is the
# specific failure this milestone exists to prevent -- and no statement retypes a threshold:
# where a number is needed it is formatted from the constants above (T-16-15).

BRANCH_NO_RUNG_PASSED = (
    "NO RUNG PASSED. In no cell did the base model reach the pre-registered threshold of "
    f"{LADDER_CELL_PASS_K} answerable questions out of {LADDER_CELL_QUESTIONS} with the value "
    "placed in its own context window. LICENSED: the SC1 capability-deficit statement, and "
    "nothing else -- this model cannot use a fact placed in its context window at this scale, so "
    "a floor-level result on the prompt-stuffed arm is evidence about CAPABILITY. NOT LICENSED: "
    "every comparative reading. It licenses no claim that weights beat prompting, no claim that "
    "prompting fails to persist, and no reading of the prompt arm's rate as a property of "
    "prompting rather than of this base model. This is a pre-registered, expected outcome and "
    "NOT a broken instrument: Phase 14 already measured this exact model with this exact prompt "
    "builder at the floor. There is deliberately no 'the ladder failed, investigate the "
    "instrument' branch -- that would be an unwritten branch discovered after seeing the result. "
    "The instrument-broken signal is non-monotonicity, reported separately, and it never moves "
    "this branch."
)

BRANCH_SPAN_1 = (
    "HIGHEST PASSED RUNG: SPAN 1. LICENSED: the base can use a ONE-TOKEN value placed in its "
    "context window at that rung's distance, so it is not blind to its own context. NOT "
    "LICENSED: anything about the material the comparison actually scores. The real taught "
    "values are several tokens long and every longer-span rung failed, so the prompt-stuffed arm "
    "is NOT off the floor for real values, and a four-arm comparison run on this basis still "
    "measures capability deficit rather than mechanism. The scope of this branch is exactly span "
    "one -- 'can use context' and 'can sustain a multi-token copy' are different claims, which is "
    "why the grid separates them."
)

BRANCH_SPAN_2 = (
    "HIGHEST PASSED RUNG: SPAN 2. LICENSED: the base can sustain a TWO-TOKEN in-context copy at "
    "that rung's distance. NOT LICENSED: the multi-token claim the comparison needs. The real "
    "taught values are longer than this rung and the longer-span rungs failed, so the prompt-"
    "stuffed arm remains below the capability required by the material it is scored on. Scope is "
    "exactly span two: this branch reports where the copy dies, it does not license reading the "
    "four-arm comparison as a mechanism comparison."
)

BRANCH_SPAN_5_SYNTHETIC = (
    "HIGHEST PASSED RUNG: SPAN 5, SYNTHETIC. LICENSED: the base can sustain a five-token "
    "in-context copy at that rung's distance -- the median length of the real taught values -- so "
    "the prompt-stuffed arm is off the floor and the four-arm comparison measures MECHANISM "
    "rather than capability deficit. NOT LICENSED: the claim on real material, which this rung "
    "did not use. The passing rung carried a synthetic, guessability-gated string; the D-15 "
    "proxy-validity check compares that cell against the top rung's real values at the same "
    "position and the same span, and a wide divergence there makes every lower rung suspect. "
    "Report that comparison alongside this branch, never instead of it."
)

BRANCH_TOP_RUNG_REAL = (
    "TOP RUNG PASSED: REAL TAUGHT VALUES. The strongest branch. LICENSED: the base can recover a "
    "real taught value from its own persona span, so the four-arm comparison is a mechanism "
    "comparison outright and any weight-versus-prompt difference reads as mechanism rather than "
    "as the base being unable to read its own context. NOT LICENSED: the comparison's verdict "
    "itself. This branch licenses the READING of the comparison; whether weights beat prompting "
    "is decided by the pre-registered paired sign test over the arm pairs and never here. Report "
    "this rung's delta against the committed Phase 14 number as the measured impact of the "
    "PERS-05 pairing fix (D-13), never as a silent assertion that the fix did not matter."
)

# Branch id -> licensed prose. The keys are the stable identifiers a report or a downstream test
# keys on; the values are the auditable text. Exactly five branches, and no sixth: a branch set
# that can grow after the run is not a pre-registration.
HEADLINE_BRANCHES = {
    "no_rung_passed": BRANCH_NO_RUNG_PASSED,
    "span_1": BRANCH_SPAN_1,
    "span_2": BRANCH_SPAN_2,
    "span_5_synthetic": BRANCH_SPAN_5_SYNTHETIC,
    "top_rung_real": BRANCH_TOP_RUNG_REAL,
}

# Span length -> branch id, for the six synthetic cells. Pre-committed with the lattice, so a rung
# cannot acquire a branch after the run: an unmapped span raises rather than falling through to a
# neighbouring branch's prose.
_SPAN_BRANCH = {1: "span_1", 2: "span_2", 5: "span_5_synthetic"}


def licensed_headline(passed_rungs):
    """The headline this phase is allowed to publish, given which rungs passed (D-14).

    Branches on the HIGHEST passed rung in ``RUNG_DIFFICULTY_ORDER`` and on nothing else — not on
    how many rungs passed, not on which pattern they form, not on anything measured elsewhere in
    the phase. That order is committed above, before the run, precisely so "the highest passed
    rung" is not decided after seeing which cells passed.

    ``passed_rungs`` is an iterable of rung keys drawn from ``RUNG_DIFFICULTY_ORDER``. An unknown
    key raises rather than being ignored: a typo that silently drops a rung would quietly downgrade
    the licensed branch, which is the same over-/under-claiming failure by a different route.

    Returns ``{branch, statement, highest_passed}``. The all-fail branch is FIRST-CLASS, not an
    error path — see ``BRANCH_NO_RUNG_PASSED``.
    """
    passed = set(passed_rungs)
    unknown = passed - set(RUNG_DIFFICULTY_ORDER)
    if unknown:
        raise ValueError(f"rung keys not in RUNG_DIFFICULTY_ORDER: {sorted(map(str, unknown))}")

    highest = None
    for rung in RUNG_DIFFICULTY_ORDER:  # ordered easiest -> hardest, so the last hit is the highest
        if rung in passed:
            highest = rung

    if highest is None:
        branch = "no_rung_passed"
    elif highest == TOP_RUNG:
        branch = "top_rung_real"
    else:
        branch = _SPAN_BRANCH[highest[0]]
    return {"branch": branch, "statement": HEADLINE_BRANCHES[branch], "highest_passed": highest}


def monotonicity_anomalies(cell_results):
    """Every ``(easier, harder)`` pair where the HARDER rung passed and the easier one did not.

    ``cell_results`` maps a rung key to its ``cell_report`` row. Only rungs PRESENT in the mapping
    are compared: an unmeasured rung is absent, not failed, and treating it as failed would invent
    anomalies out of a partial ladder.

    Per D-14 an anomaly is recorded as a NAMED instrument anomaly in the report. It does not stop
    the run and it does not change the licensed branch — ``licensed_headline`` reads the highest
    passed rung and nothing else, deliberately, so that the licence cannot be argued away by
    pointing at an awkward cell.

    And the direction matters: an all-fail ladder is a normal, pre-registered outcome (this model
    was already measured at the floor on this exact task). NON-MONOTONICITY is the instrument-broken
    signal — a harder cell passing while an easier one fails means the rungs are not ordered by the
    difficulty the grid claims, and every reading built on that order is suspect.
    """
    measured = [rung for rung in RUNG_DIFFICULTY_ORDER if rung in cell_results]
    passed = {rung for rung in measured if cell_results[rung]["passed"]}
    return [
        (easier, harder)
        for index, easier in enumerate(measured)
        if easier not in passed
        for harder in measured[index + 1 :]
        if harder in passed
    ]
