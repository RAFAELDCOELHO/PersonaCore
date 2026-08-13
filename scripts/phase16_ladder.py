"""PERS-01 capability ladder — the PRE-REGISTRATION: cell thresholds and cell arithmetic.

Committed BEFORE the run it judges (STAT-05, D-14). Every number in this module is derived from
material ALREADY PUBLISHED in this repository — the committed Phase 14 fairness-control result and
the committed fixture's core question count — and none of it is derived from any Phase 16
measurement. Git history is the proof: this file lands before the ladder produces a single number
that these thresholds judge.

Nothing executes at import. Constants and pure functions only (the ``finetune_ab.py`` "gate
formulas as pure functions" precedent), so an ``importlib`` load in a CPU-only test runs no guard,
no model load and no generation. ``main()`` is ``__main__``-guarded and supports exactly one mode,
``--vet``: the ONE-TIME run that measures every synthetic candidate and clears it through the
guessability gate before it becomes a committed constant. No-argument invocation exits non-zero
rather than picking a default; the full-ladder run is a later plan's mode, not a silent one here.

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

import json
import pathlib
import statistics
import sys
import time

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# `scripts/` is sys.path[0] only when a script in it is run DIRECTLY; an importlib-loaded test
# harness gets no such entry (personalize_demo.py:96-99 precedent). Insert it explicitly so both
# paths reach the sibling pre-registration module.
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from _verdict import VERDICT_SECTION, recorded_verdict  # noqa: E402  (needs the insert above)
from erasure_gate import rule_of_three, wilson_upper_bound  # noqa: E402  (needs the insert above)

from personacore.dialogue import ASSISTANT_ID, build_recall_prompt  # noqa: E402

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


# =============================================================================================
# The ladder's MATERIAL (D-12) and the two distance-row prompt builders (D-11)
# =============================================================================================
#
# D-12 makes the new rungs SYNTHETIC strings, token-length-matched to the real values and filtered
# through the already-validated guessability gate -- and it names exactly one risk the synthetic
# choice introduces: a synthetic string the base ALREADY KNOWS would inflate a rung and license a
# stronger headline than the data supports. `vet_synthetic_candidates` closes that by importing the
# gate (D-16), never by copying it.
#
# The pools below are committed BEFORE any probe runs (T-16-20). Selection is first-8-SURVIVORS in
# this committed order, so "which candidates were chosen" is answered by git history rather than by
# whichever ones looked best once the probe results were in.

# The 8 core facts in the BINDING FIXTURE's own order -- `provenance.core_facts` of
# `results/phase16_recall_sample.json`, which is also `phase14_factset.LOCKED_FACTS` order.
# Position is LOAD-BEARING: `SYNTHETIC_VALUES[span][i]` is the material for the fact at position
# `i`, so a wrong order misaligns every value to the wrong fact, silently.
# `test_synthetic_fact_order_matches_the_binding_fixture` resolves the fixture's fact ids to their
# slots through the lazily-imported fact set and asserts equality, so this tuple cannot drift.
#
# SLOTS, not fact ids, and that substitution is FORCED rather than stylistic: every core fact id
# ends in its own value (the id for the hometown fact literally spells the town), so a literal
# tuple of ids would embed 8 locked values in this module's string surface and turn
# `test_ladder_driver_holds_no_fact_strings_at_import` red -- that scan is SUBSTRING containment
# over every string this module holds (T-16-16). The slots carry the same ordering, the same
# arity, and no value.
SYNTHETIC_FACT_ORDER = (
    "person_name",
    "pet_name",
    "cat_name",
    "sibling_name",
    "hometown",
    "street",
    "birth_year",
    "house_number",
)

# Candidate pools, keyed by SPAN (token length of the in-context value). Deliberately OVERSIZED --
# 14+ candidates for 8 slots -- so the gate can reject without leaving a hole (D-12). Their token
# length is NOT asserted here: `phase14_factset.token_census` MEASURES it at vet time and the
# measurement is recorded per candidate in `results/phase16_ladder_material.md`. A hard-coded
# length would be exactly the "assumed, never measured" defect PITFALLS-12 names.
#
# Register: lowercase ASCII, pronounceable, not English. Authoring aid, disclosed because it is an
# input to the committed order: every candidate below was checked for absence from the 608 base
# completions ALREADY PUBLISHED in `results/phase14_factset_report.md`, and the pools are ordered
# most-nonsense-first. That is a screen against published evidence, not against this plan's probe
# results -- the probe had not run when this tuple was committed, which is the property T-16-20
# needs.
#
# Span 1 is the constrained row and the pool shows it. This tokenizer holds only 118 single-token
# lowercase-ASCII alphabetic strings in total, and 94 of them already appear in those committed
# base completions; what survives is fragment-shaped rather than name-shaped. That is a property of
# a 547-decodable-id near-character vocabulary, not a choice -- and it is also why the span-1 rung
# is the one whose guessability gate matters most: a one-token value is a substring of far more
# English than a five-token one, and a substring hit is a false PASS that inflates the easiest rung.
SYNTHETIC_CANDIDATES = {
    1: (
        "iko",
        "ora",
        "mma",
        "ko",
        "arden",
        "leepy",
        "unny",
        "ower",
        "ooked",
        "uiet",
        "ax",
        "umped",
        "ump",
        "ved",
    ),
    2: (
        "kez",
        "zil",
        "nyv",
        "pyk",
        "xog",
        "kiz",
        "vez",
        "zof",
        "nyk",
        "kov",
        "xar",
        "pyz",
        "kix",
        "zog",
    ),
    5: (
        "vraskil",
        "quenlow",
        "urvellen",
        "ferrowin",
        "ombrast",
        "pyrralt",
        "sombrek",
        "ashkell",
        "brumvel",
        "lumbrek",
        "nivelle",
        "orbrant",
        "pravik",
        "sarnok",
        "wyndal",
    ),
}

# THE MATERIAL. The first EIGHT survivors of each pool above, in committed pool order, positionally
# aligned to SYNTHETIC_FACT_ORDER: SYNTHETIC_VALUES[span][i] is the material for the fact at
# position i. Transcribed by hand from the `--vet` run recorded in
# `results/phase16_ladder_material.md` (driver commit 308eafb, seed 1337, MPS, torch 2.7.1), the
# same register as `phase14_factset`'s locked set -- the driver never parses its own report at
# runtime, and git history is the pre-registration proof.
#
# Every value here was MEASURED at its declared token length and CLEARED by
# `phase14_factset_gate.probe_guessability` (clean == True) BEFORE it became this constant. From
# this point the ladder READS this tuple; it does not re-vet. Re-running `--vet` regenerates the
# report, it does not re-choose the material.
#
# Recorded honestly, because the number matters when reading the evidence: the guessability gate
# cleared all 43 candidates and rejected NONE. The 19 REJECTED rows in the report are surplus --
# pools oversized past 8 -- not gate rejections. The gate ran on every candidate (4 reserved probes
# x 4 draws each, all quoted verbatim in the report); its filter simply did not fire, because the
# pools were pre-screened for absence from the 608 base completions already published in
# `results/phase14_factset_report.md` before this order was committed. That screen is disclosed
# above rather than presented as the gate's own work.
SYNTHETIC_VALUES = {
    1: ("iko", "ora", "mma", "ko", "arden", "leepy", "unny", "ower"),
    2: ("kez", "zil", "nyv", "pyk", "xog", "kiz", "vez", "zof"),
    5: ("vraskil", "quenlow", "urvellen", "ferrowin", "ombrast", "pyrralt", "sombrek", "ashkell"),
}

# ===== The two distance rows' FRAMES ==========================================================
#
# Natural PersonaChat-register text in both rows, held CONSTANT (D-11). No instructed-copy framing
# ("do this to the word X") anywhere: that framing is out of distribution for a TinyStories +
# PersonaChat model, so its failure could not separate incapacity from instruction-following
# failure and would therefore license nothing. `test_frames_carry_no_instructed_copy_language`
# pins the five forbidden substrings.
#
# Within a distance row the frame is IDENTICAL across spans -- only the substituted value changes
# -- so span is the only variable in that row (D-11), and
# `test_frame_is_constant_across_spans_within_a_row` proves it structurally rather than by reading.

# Distance ~2: the value rides at the END of the USER turn, so the only token between it and the
# `<|assistant|>` trigger is the trigger itself. It CANNOT ride in a persona span: a persona value
# sits ~30 tokens back (the whole user turn is in between), which is the other row.
NEAR_FRAME = "{question} i think you told me it was {value}"

# Distance ~30: a first-person persona statement, the SAME path `run_fairness_control` takes -- so
# the top rung is a direct comparison and D-15's proxy-validity check is a subtraction rather than
# an argument. The value ends the statement because the distance is already `2 + len(question)`
# tokens and this fixture's questions run 11-58 tokens; trailing persona filler only pushes the row
# further from its ~30 label. Measured over the fixture's 216 core questions: min 13, MEDIAN 26,
# max 60 -- the median is the pinned number, and the spread is the questions', not the frame's.
FAR_FRAME = "my name is {value}"


def ladder_distance(tok, prompt_ids, value):
    """MEASURED token distance from the END of ``value`` to the ``<|assistant|>`` trigger.

    Measured, never assumed (T-16-21): the grid's rows are labelled ~2 and ~30, and a label is not
    a measurement. Both the tests and the run report cite this number, so "distance ~30" is never
    the plan's approximation quoted back as a result.

    Returns the INDEX DIFFERENCE — 1 when the value's last token is immediately followed by the
    trigger. The value's end is located by decoding growing prefixes rather than by searching for
    ``tok.encode(value)`` as a contiguous run, because byte-level BPE is context-dependent: a value
    preceded by a space merges its first characters into an id the standalone encoding spells out
    separately, so the standalone sequence is frequently NOT a contiguous run even though the value
    is fully in view. That is the same measured asymmetry ``assert_value_in_prompt`` records (54 of
    216 committed fairness prompts), and an id-run search would mis-measure exactly those.

    A prefix that cuts a multi-byte glyph is skipped rather than fatal — this fixture's questions
    carry em dashes, and a truncated UTF-8 sequence provably does not end with an ASCII value.
    """
    # ponytail: O(n^2) decode scan over a <= 61-token prompt. Fine at this size; if a caller ever
    # measures thousands of prompts, decode once and track byte offsets instead.
    trigger = prompt_ids.index(ASSISTANT_ID)
    for end in range(1, trigger + 1):
        try:
            text = tok.decode(prompt_ids[:end])
        except UnicodeDecodeError:
            continue
        if text.endswith(value):
            return trigger - (end - 1)
    raise ValueError(
        f"value {value!r} does not end any prefix of the prompt — the builder did not place it in "
        "view, so anything drawn from this prompt measures nothing while still reporting a rate"
    )


def build_near_prompt(tok, question, value):
    """The distance-~2 rung's prompt: the value at the END of the user turn.

    **This call site passes NO ``persona=`` argument, and that is structural, not incidental.**
    ``build_recall_prompt`` puts a persona span in front of the user turn, so a value placed there
    sits ~30 tokens from the trigger — the OTHER row. Distance ~2 is only reachable by carrying the
    value inside the ``question`` string, which makes this call site INVISIBLE to
    ``tests/test_phase14_scoring.py::test_persona_argument_is_scoped_to_the_fairness_control``: that
    guard keys on an argument name this site does not use. It is not a gap in that guard and must
    not be closed by widening it. The coverage route is the other one — the every-``draw_all``-
    asserts guard, satisfied by the run driver calling ``assert_value_in_prompt`` on what this
    returns (T-16-19), and ``test_near_prompt_uses_no_persona_argument`` pins that this site really
    is the bare form so the claimed route is the real one.
    """
    return build_recall_prompt(tok, NEAR_FRAME.format(question=question, value=value))


def build_far_prompt(tok, question, value):
    """The distance-~30 rung's prompt: the value in the ``<|system|>`` persona span.

    Same path as ``phase14_recall.run_fairness_control`` — the ladder's top rung and this row
    differ in MATERIAL (synthetic vs real taught value) rather than in mechanism, which is what
    makes D-15's proxy-validity check a subtraction between two cells instead of an argument.

    **This is a sanctioned ``persona=`` call site**, listed in ``PERSONA_ALLOWLIST`` in the same
    commit that created it. The value in the persona span IS the measurement here, exactly as in
    the fairness control: the rung asks whether the base can use a value placed in its own context
    window, so a prompt without it in view would measure nothing. Everywhere else in this project a
    fact value reaching a prompt is the demo-killing failure ``assert_no_value_in_prompt`` aborts
    on; the difference is that this value is synthetic, gate-cleared and never a taught fact.
    """
    return build_recall_prompt(tok, question, persona=[FAR_FRAME.format(value=value)])


# =============================================================================================
# The vetting run (D-12 / D-16 / T-16-18) — the ONE-TIME measurement behind SYNTHETIC_VALUES
# =============================================================================================

MATERIAL_PATH = _REPO_ROOT / "results" / "phase16_ladder_material.md"  # COMMITTED evidence


def vet_synthetic_candidates():
    """Measure every candidate and clear it through the guessability gate. Returns the survivors.

    Two hard filters, in this order, and both are RECORDED for every candidate rather than only
    for the ones that fail:

    1. ``phase14_factset.token_census`` — the candidate's token count must be EXACTLY its span, and
       its byte-fallback round-trip must be exact. A "span 5" rung carrying a 6-token value is not
       the rung the pre-registration named, and a value the tokenizer cannot represent exactly
       makes every downstream match on it meaningless.
    2. ``phase14_factset_gate.probe_guessability`` — the D-16 public entry point, IMPORTED and never
       copied. ``clean is False`` is a hard reject: D-12 names exactly one risk the synthetic choice
       introduces, and it is that a string the base already knows would INFLATE a rung and license a
       stronger headline than the data supports (T-16-18).

    The probes run on the BASE, with the adapter DISABLED. The question is about the base's own
    prior; the adapted model has been taught a persona and its answers would be about that instead.

    **Probe questions are assigned positionally, from the committed pool order, never from how many
    earlier candidates happened to pass.** Candidate at pool position ``i`` is probed with the
    reserved questions of ``SYNTHETIC_FACT_ORDER[i % 8]``. That correspondence is fixed by two
    tuples both committed before any probe ran, so the instrument's INPUT cannot depend on the
    instrument's own OUTPUT — which is what "probe with the questions of the slot this candidate
    would land in" would quietly do, since the landing slot is only known after the earlier verdicts
    are in. It also rotates all eight reserved phrasings across the pool instead of asking one
    slot's four questions over and over.

    Selection is the first EIGHT survivors per span, in committed pool order, assigned positionally
    to ``SYNTHETIC_FACT_ORDER``. Never "whichever looked best" (T-16-20). Fewer than eight survivors
    is a hole, not a smaller ladder: it exits non-zero rather than shipping a short row.
    """
    import phase14_factset as fs  # LAZY — see the LAZY-IMPORT RULE in the module docstring.
    import phase14_factset_gate as gate
    import phase14_recall as recall
    import torch

    from personacore.config import RuntimeConfig
    from personacore.lora import adapter_disabled
    from personacore.preflight import preflight_device
    from personacore.provenance import git_sha
    from personacore.seeding import seed_everything

    started = time.time()
    summary = preflight_device(strict=True)
    print(f"[phase16_ladder] preflight: {summary}")
    device = RuntimeConfig().device
    # ONE seed constant in play, the gate's own: `probe_guessability` seeds its per-probe
    # torch.Generator `gate.SEED + index` internally, so re-declaring 1337 here would be a second
    # literal free to drift from the one that actually drives the draws.
    seed_everything(gate.SEED)

    # The adapter file is loaded and then switched OFF rather than skipped, because this is the
    # loader whose `weights_only=True` choke points and LOAD-BEFORE-INJECT ordering the rest of the
    # milestone measures through; a second, parallel base-only loader is how two arms silently stop
    # being the same model.
    model, model_cfg, tok, forbid, _artifact = recall.load_adapted_model(device)
    id_by_slot = {fact.slot: fact.id for fact in fs.LOCKED_FACTS}
    probes_by_position = [fs.GATE_PROBES[id_by_slot[slot]] for slot in SYNTHETIC_FACT_ORDER]

    rows = {}
    survivors = {}
    probe_index = 0
    with adapter_disabled(model):
        for span in LADDER_SPANS:
            rows[span] = []
            survivors[span] = []
            for position, candidate in enumerate(SYNTHETIC_CANDIDATES[span]):
                slot = SYNTHETIC_FACT_ORDER[position % len(SYNTHETIC_FACT_ORDER)]
                questions = probes_by_position[position % len(SYNTHETIC_FACT_ORDER)]
                n_tokens, roundtrip = fs.token_census(tok, candidate)
                row = {
                    "candidate": candidate,
                    "tokens": n_tokens,
                    "roundtrip": roundtrip,
                    "probe_slot": slot,
                    "n_probes": 0,
                    "n_completions": 0,
                    "clean": None,
                    "verdict": "REJECTED",
                    "reason": "",
                }
                if n_tokens != span:
                    row["reason"] = f"token count {n_tokens} != span {span}"
                elif not roundtrip:
                    row["reason"] = "byte-fallback round-trip is not exact"
                else:
                    probe = gate.probe_guessability(
                        model, tok, device, forbid, candidate, questions, start_index=probe_index
                    )
                    probe_index += probe["n_probes"]
                    row["n_probes"] = probe["n_probes"]
                    row["n_completions"] = probe["n_completions"]
                    row["clean"] = probe["clean"]
                    row["probe_detail"] = probe["probes"]
                    if not probe["clean"]:
                        row["reason"] = "the base already emits this string (guessability, D-12)"
                    elif len(survivors[span]) >= len(SYNTHETIC_FACT_ORDER):
                        row["reason"] = "surplus: the pool is oversized, first 8 survivors selected"
                    else:
                        row["verdict"] = "SELECTED"
                        row["reason"] = f"slot {len(survivors[span])} of SYNTHETIC_FACT_ORDER"
                        survivors[span].append(candidate)
                rows[span].append(row)
                print(
                    f"[phase16_ladder] span {span} {candidate:10} tokens={n_tokens} "
                    f"clean={row['clean']} {row['verdict']} ({row['reason']})"
                )
            if len(survivors[span]) < len(SYNTHETIC_FACT_ORDER):
                raise SystemExit(
                    f"[phase16_ladder] span {span} cleared only {len(survivors[span])} of the "
                    f"{len(SYNTHETIC_FACT_ORDER)} values it needs. That is a HOLE in the ladder's "
                    "material, not a smaller ladder: widen SYNTHETIC_CANDIDATES and re-vet, and "
                    "never relax either filter to make the count fit."
                )

    wall = time.time() - started
    _write_material_report(rows, survivors, summary, torch.__version__, git_sha(), gate, wall)

    print("[phase16_ladder] ===== paste-ready material =====")
    print("SYNTHETIC_VALUES = {")
    for span in LADDER_SPANS:
        print(f"    {span}: {tuple(survivors[span])!r},")
    print("}")
    print(f"[phase16_ladder] wrote {MATERIAL_PATH}  wall {wall / 60:.1f} min")
    print(
        f"  base: {model_cfg.n_layer}-layer model, adapter DISABLED, on {device}  "
        f"seed={gate.SEED}  driver git_sha={git_sha()}"
    )
    return survivors


def _write_material_report(rows, survivors, summary, torch_version, driver_sha, gate, wall):
    """The committed audit record: EVERY candidate, with its measurement and its verdict.

    Rejected candidates stay in the table. A material list whose rejects are invisible is not
    auditable — it reads as a pool that happened to be perfect, and a silent re-pick would leave no
    trace in the diff (T-16-20).
    """
    blocks = [
        "# Phase 16 Ladder Material (D-12 / D-16 / T-16-18 / T-16-20)",
        "",
        "> **What these numbers are:** the ONE-TIME vetting of every synthetic candidate the",
        "> PERS-01 capability ladder could use, measured BEFORE the surviving values became the",
        "> committed `SYNTHETIC_VALUES` constant in `scripts/phase16_ladder.py`. Two filters, both",
        "> already-validated instruments imported rather than copied (D-16): the D-02(a) tokenizer",
        "> census (`phase14_factset.token_census`) and the D-02(b) base-guessability probe",
        "> (`phase14_factset_gate.probe_guessability`), run against the FROZEN base with the",
        "> persona adapter DISABLED.",
        "> **What they are not:** a recall measurement. Nothing here is a ladder result — the",
        "> ladder had not run when this file was written, which is the point: material chosen",
        "> after seeing which candidates passed would be material chosen after seeing data.",
        "",
        "## Run Provenance",
        "",
        f"- Driver commit: `{driver_sha}`",
        f"- Device: `{summary}`",
        f"- torch: `{torch_version}`",
        f"- Seed: `{gate.SEED}` — `seed_everything({gate.SEED})`, then a per-probe "
        f"`torch.Generator({gate.SEED} + probe_index)` inside `probe_guessability`",
        f"- Decoding: greedy + {gate.PROBE_SEEDS - 1} warm draws (temperature {gate.TEMPERATURE}, "
        f"top_p {gate.TOP_P}), `max_new_tokens={gate.PROBE_MAX_NEW_TOKENS}`, dead ids forbidden",
        f"- Wall clock: {wall / 60:.1f} min",
        "",
        "## Method",
        "",
        "1. **Token census.** `token_census(tok, candidate)` must return exactly the row's span",
        "   and an exact byte-fallback round-trip. Unlike Phase 14's D-04 census — where the",
        "   count was a recorded field that could never reject — the count IS a reject criterion",
        "   here, because span length is the ladder's independent variable (D-11).",
        "2. **Guessability.** `probe_guessability` prompts the un-adapted base with four reserved",
        "   probe questions and takes `clean` to be True iff the candidate appears in ZERO of the",
        "   resulting completions. ONE containment out of N is a FAIL — the same unforgiving",
        "   boundary Phase 14 used, and the same function.",
        "3. **Selection.** The first eight survivors per span, in the committed pool order,",
        "   assigned positionally to `SYNTHETIC_FACT_ORDER`. Probe questions come from position",
        "   `i % 8` of that same committed order, so the probe INPUT never depends on earlier",
        "   probe RESULTS.",
        "",
        f"`SYNTHETIC_FACT_ORDER` = {', '.join(f'`{slot}`' for slot in SYNTHETIC_FACT_ORDER)}",
        "",
    ]

    for span in LADDER_SPANS:
        span_rows = rows[span]
        n_selected = sum(1 for row in span_rows if row["verdict"] == "SELECTED")
        blocks += [
            f"## Span {span} — {len(span_rows)} candidates, {n_selected} selected",
            "",
            "| # | candidate | tokens | round-trip | probe slot | probes | completions | clean | "
            "verdict | reason |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for position, row in enumerate(span_rows):
            clean = "n/a" if row["clean"] is None else str(row["clean"])
            blocks.append(
                f"| {position} | `{row['candidate']}` | {row['tokens']} | "
                f"{'exact' if row['roundtrip'] else 'FAILED'} | `{row['probe_slot']}` | "
                f"{row['n_probes']} | {row['n_completions']} | {clean} | **{row['verdict']}** | "
                f"{row['reason']} |"
            )
        blocks += [
            "",
            f"Selected, in `SYNTHETIC_FACT_ORDER` position order: "
            f"{', '.join(f'`{value}`' for value in survivors[span])}",
            "",
        ]

    blocks += [
        "## Probe Completions (verbatim)",
        "",
        "Every completion the base produced for every candidate that reached the probe, quoted",
        "raw so a reader can judge the close-call tier themselves rather than taking the",
        "mechanical verdict on trust. A candidate rejected on token count never reached this",
        "stage and has no block here.",
        "",
    ]
    for span in LADDER_SPANS:
        for row in rows[span]:
            if not row.get("probe_detail"):
                continue
            blocks += [
                f"### span {span} — `{row['candidate']}` — **{row['verdict']}** "
                f"(clean={row['clean']})",
                "",
            ]
            for probe in row["probe_detail"]:
                blocks.append(
                    f"- Q `{probe['question']}` — prompt = {len(probe['prompt_ids'])} ids"
                )
                for index, text in enumerate(probe["completions"]):
                    mode = "greedy" if index == 0 else f"warm {index}"
                    blocks.append(f"  - {mode}: `{text.replace(chr(10), chr(92) + 'n')}`")
            blocks.append("")

    MATERIAL_PATH.write_text("\n".join(blocks), encoding="utf-8")


# =============================================================================================
# THE RUN — one cell of the ladder, over the binding fixture's own 216 core questions
# =============================================================================================

# The BINDING fixture (v3.0): Phases 17 and 18 consume it UNCHANGED. This driver READS it and
# writes nothing to it — a regenerated or resampled variant would break cross-phase comparison.
FIXTURE_PATH = _REPO_ROOT / "results" / "phase16_recall_sample.json"

# The two distance rows, NAMED from the committed lattice rather than retyped as literals: the
# builder branch in `run_ladder_cell` must never be able to drift from `LADDER_DISTANCES`.
NEAR_DISTANCE, FAR_DISTANCE = LADDER_DISTANCES


def _prove(condition, message):
    """Loud proof: ``SystemExit`` naming the violated contract (never an ``-O``-strippable one).

    Same register and same reason as ``phase14_recall._prove``, with this module's own prefix. It
    is four lines rather than an import of the private twin because an abort that names the wrong
    driver sends its reader to the wrong file, and because this module's cheap paths must stay
    importable without pulling torch.
    """
    if not condition:
        raise SystemExit(f"[phase16_ladder] PROOF FAILED: {message}")


def load_core_items():
    """The binding fixture's 216 core questions, as ``RecallItem``s carrying its OWN seed indices.

    ``core_taught`` (112) + ``core_held_out`` (104). The ``seed_index`` is read VERBATIM from the
    fixture and never re-enumerated: it is the per-ARM index ``stamp_seed_indices`` stamped, each
    arm restarting at 0, so the ladder draws exactly the streams the scored arms draw. Re-deriving
    it from this loop's position is PERS-05's defect, committed here as a read rather than as an
    ``enumerate``.

    The length is PROVEN equal to ``LADDER_CELL_QUESTIONS`` rather than trusted (T-16-24). If the
    fixture and the pre-registered denominator ever disagree, every cell stops being comparable to
    the floor — and the failure is silent, because a cell over 200 questions still produces a
    perfectly well-formed rate. The run aborts instead of rescaling.

    The fact objects are resolved through the LAZILY imported fact set, so the locked values live
    in this process only while a run is in flight and never in this module's string surface
    (T-16-16). ``split`` is reconstructed from which bucket the entry came out of — the fixture
    records ``seed_index``/``fact_id``/``question``/``reserved`` and leaves the split implicit in
    its two lists.
    """
    import phase14_factset as fs  # LAZY — see the LAZY-IMPORT RULE in the module docstring.
    import phase14_recall as recall

    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    fact_by_id = {fact.id: fact for fact in fs.LOCKED_FACTS}
    items = tuple(
        recall.RecallItem(
            fact=fact_by_id[entry["fact_id"]],
            question=entry["question"],
            split=split,
            reserved=entry["reserved"],
            seed_index=entry["seed_index"],
        )
        for key, split in (("core_taught", "taught"), ("core_held_out", "held-out"))
        for entry in fixture["questions"][key]
    )
    _prove(
        len(items) == LADDER_CELL_QUESTIONS,
        f"{FIXTURE_PATH.name} yielded {len(items)} core questions but the pre-registration "
        f"committed {LADDER_CELL_QUESTIONS} — the cell would no longer be scored over the same "
        "set as the floor it is compared against, and the mismatch is invisible in the reported "
        "rate. Fix the fixture or re-derive the floor; never rescale the denominator silently",
    )
    return items


def run_ladder_cell(model, tok, device, forbid, items, *, span, distance):
    """ONE ladder cell: the SAME 216 questions at the SAME 9 draws as the floor.

    Both halves of that sentence are load-bearing, and neither is free to be traded for wall clock.
    ``n_answerable`` is a MAX-OVER-DRAWS statistic — a question counts if ANY of its draws carried
    the value — so its noise floor scales with the draw count. The same count taken at 4 draws is a
    different quantity that is not comparable to the committed floor, and the incomparability does
    not show up anywhere in the number itself. The draw count is therefore not a parameter here: it
    comes from the shared ``phase14_recall.draw_all`` (1 greedy + ``N_SEEDED_SAMPLES``), which is
    the same loop the floor was measured through, and ``LADDER_CELL_DRAWS`` is what the tests pin
    it against.

    **Inside ``adapter_disabled``, structurally.** The ladder asks what the BASE can do with a
    value placed in its own context window; the adapted model already carries a persona in its
    weights, so measuring it would answer a different question while producing the same shaped
    number. It is an invariant of every rung, not an option, which is why it wraps the whole loop
    rather than being a keyword a caller could forget.

    **Every prompt is proven to carry its value before anything is drawn from it** (T-16-23). A
    floor-level rung is evidence of INCAPACITY only if the thing being copied was provably there to
    copy; without that proof the same number is equally consistent with a builder that quietly
    dropped the value, and the two readings license opposite headlines. ``assert_value_in_prompt``
    aborts rather than warning, for the same reason.

    ``span`` selects the material (``SYNTHETIC_VALUES[span]``, positionally aligned to
    ``SYNTHETIC_FACT_ORDER``); ``distance`` selects the row's prompt builder. Returns the
    per-question records plus the cell's ``cell_report`` row under ``"cell"``.
    """
    import phase14_recall as recall  # LAZY — see the LAZY-IMPORT RULE in the module docstring.

    from personacore.lora import adapter_disabled

    _prove(
        span in SYNTHETIC_VALUES,
        f"span {span} has no committed material — the rungs are {LADDER_SPANS}",
    )
    _prove(
        distance in LADDER_DISTANCES,
        f"distance {distance} is not a committed row: {LADDER_DISTANCES}",
    )
    values = SYNTHETIC_VALUES[span]
    tier = f"ladder cell (span {span}, nominal distance ~{distance})"

    asked = []
    with adapter_disabled(model):
        for item in items:
            # Position is the whole alignment: SYNTHETIC_VALUES[span][i] is the material for the
            # fact at position i of SYNTHETIC_FACT_ORDER. A slot outside that order has no
            # material, and `.index` would raise a bare ValueError naming nothing.
            _prove(
                item.fact.slot in SYNTHETIC_FACT_ORDER,
                f"slot {item.fact.slot!r} has no committed synthetic value — the fixture and "
                "SYNTHETIC_FACT_ORDER have drifted apart, so some questions would be scored "
                "against another fact's material",
            )
            value = values[SYNTHETIC_FACT_ORDER.index(item.fact.slot)]
            # Resolved by NAME at call time, never through a pre-built table: the two builders are
            # the row, and a table of function objects would silently keep the old one.
            build = build_near_prompt if distance == NEAR_DISTANCE else build_far_prompt
            prompt_ids = build(tok, item.question, value)
            recall.assert_value_in_prompt(tok, prompt_ids, [value])
            # MEASURED per question (T-16-21). The far row is a DISTRIBUTION, not a constant, so
            # the row's label (~30) is never what the report prints.
            measured_distance = ladder_distance(tok, prompt_ids, value)
            # PERS-05: the seed comes off the ITEM, never off this loop's position. `-1` is the
            # unstamped sentinel; an unstamped item would draw from a stream no scored arm used.
            _prove(
                item.seed_index >= 0,
                f"question {item.question!r} reached a ladder cell carrying no seed index — the "
                "cell would draw from a stream the floor never used, and the comparison would be "
                "unpaired while still reporting a paired-looking number (PERS-05)",
            )
            completions, stopped = recall.draw_all(
                model, tok, prompt_ids, device, forbid, item.seed_index
            )
            k, n = recall.score_question(completions, value)
            asked.append(
                {
                    "question": item.question,
                    "fact_id": item.fact.id,
                    "split": item.split,
                    "seed_index": item.seed_index,
                    "value": value,
                    "prompt_ids": prompt_ids,
                    "measured_distance": measured_distance,
                    "completions": completions,
                    "hits": [recall.contains_value(c, value) for c in completions],
                    "stopped": stopped,
                    "k": k,
                    "n": n,
                }
            )
            print(f"[phase16_ladder] {tier} {item.question!r}: {k}/{n}")

    # The floor's own statistic, computed the same way `run_fairness_control` computes it: a
    # QUESTION counts once if ANY draw carried the value (STAT-01), never once per draw.
    n_answerable = sum(1 for entry in asked if entry["k"] > 0)
    measured = [entry["measured_distance"] for entry in asked]
    return {
        "tier": tier,
        "span": span,
        "distance": distance,
        "questions": asked,
        "k": sum(entry["k"] for entry in asked),
        "n": sum(entry["n"] for entry in asked),
        "n_answerable": n_answerable,
        # Min/median/max, never a single number: the far row spans 13 to 60 tokens over this
        # fixture's questions, and rendering that spread as its label would be a distribution
        # published as a constant.
        "distances": {
            "min": min(measured),
            "median": statistics.median(measured),
            "max": max(measured),
        },
        # NESTED, not merged: `cell_report`'s row keys `questions` to the DENOMINATOR while this
        # dict keys it to the per-question records, and `run_fairness_control` — whose return shape
        # the top rung has — uses the records meaning. Merging would destroy one of the two.
        "cell": cell_report(n_answerable),
    }


# =============================================================================================
# THE TOP RUNG (D-13) — the fairness control RE-RUN post-fix, on REAL taught values
# =============================================================================================


def run_top_rung(model, tok, device, forbid, items):
    """The hardest rung: the D-11.1 fairness control itself, re-run post-fix on REAL values.

    Not a citation of Phase 14's number and not a re-implementation of its control — the SAME
    function, called with the same statement map ``phase14_recall.main()`` builds. D-13 revised the
    earlier decision to reuse the published number as-is, and the revision is recorded rather than
    overwritten: reusing it would have asserted that the PERS-05 pairing fix did not matter, which
    is precisely the thing the re-run measures.

    **It can never be arm B.** PERS-01 requires the ladder recorded BEFORE any comparison is
    scored, so a top rung taken from the comparison would license the comparison with the
    comparison. It is measured here, in the ladder's own run, ahead of everything it licenses.

    What distinguishes it from the ``(span 5, distance ~30)`` synthetic cell is the MATERIAL: real
    taught values instead of gate-cleared synthetic ones. That is the whole content of D-15's
    proxy-validity check, and it is why this rung reuses the control instead of parametrizing
    ``run_ladder_cell`` — the control IS the thing the synthetic rows are a proxy for.
    """
    import phase14_factset as fs  # LAZY — see the LAZY-IMPORT RULE in the module docstring.
    import phase14_recall as recall

    _prove(
        len(items) == LADDER_CELL_QUESTIONS,
        f"the top rung received {len(items)} questions but the ladder's denominator is "
        f"{LADDER_CELL_QUESTIONS} — its delta against the committed floor, and D-15's subtraction "
        "against the synthetic cell, are only defined at a shared denominator",
    )
    # Built HERE from the lazily-imported fact set, exactly as `phase14_recall.main()` builds it:
    # the control never reaches for fact strings itself (LAZY-IMPORT RULE), and neither does this
    # module at import time.
    statements = {
        fact.id: fs.SLOT_FORMS[fact.slot].ans1.format(v=fact.value)
        for fact in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS
    }
    return recall.run_fairness_control(model, tok, device, forbid, items, statements)


# The two units the committed floor can be stated in, and which one may carry an inference. The
# labels are constants so the report cannot print the forbidden unit without printing why it is
# forbidden (T-16-26).
DRAW_UNIT_LABEL = "draws — the unit STAT-01 FORBIDS for inference"
QUESTION_UNIT_LABEL = "questions — the STAT-01 unit"


def floor_in_both_units():
    """The committed floor stated in BOTH units, every number COMPUTED from the shared bounds.

    The draw-unit bound is roughly NINE TIMES tighter than the question-unit one, and citing the
    draw unit alone makes the prompt arm look far more definitively at zero than the legal unit
    supports. Publishing both side by side, with the draw unit labelled as the one STAT-01 forbids
    for inference, is what stops the tighter number being the one that gets quoted (T-16-26).

    Nothing here is retyped: the draw denominator is ``LADDER_FLOOR_QUESTIONS *
    LADDER_CELL_DRAWS`` and both bounds come from ``erasure_gate.wilson_upper_bound``, so the
    printed arithmetic cannot drift from the constants it claims to state. The numerator is the
    same integer in both units for the reason the floor comment above gives: one hit across all
    draws means exactly one question had ``k >= 1``.

    ``rule_of_three_upper`` is the ceiling the floor WOULD have had at zero successes, reported
    alongside so a reader can see how little separates the committed floor from nothing at all.
    """
    draws = LADDER_FLOOR_QUESTIONS * LADDER_CELL_DRAWS
    return {
        "draws": {
            "successes": LADDER_FLOOR_ANSWERABLE,
            "n": draws,
            "rate": LADDER_FLOOR_ANSWERABLE / draws,
            "wilson_upper_95": wilson_upper_bound(LADDER_FLOOR_ANSWERABLE, draws),
            "label": DRAW_UNIT_LABEL,
        },
        "questions": {
            "successes": LADDER_FLOOR_ANSWERABLE,
            "n": LADDER_FLOOR_QUESTIONS,
            "rate": LADDER_FLOOR_ANSWERABLE / LADDER_FLOOR_QUESTIONS,
            "wilson_upper_95": wilson_upper_bound(LADDER_FLOOR_ANSWERABLE, LADDER_FLOOR_QUESTIONS),
            "label": QUESTION_UNIT_LABEL,
        },
        "rule_of_three_upper": rule_of_three(LADDER_FLOOR_QUESTIONS),
        "source": LADDER_FLOOR_SOURCE,
    }


def top_rung_delta(top_rung_result):
    """The re-run against the COMMITTED number — as structured data, never as a claim of no change.

    **D-19, in full.** The PERS-05 fix changes WHICH SEEDS ARE DRAWN: the control used to seed from
    its own loop position and now seeds from the item's stamped index, so different completions come
    back and the count this code produced for the committed Phase 14 report does not reproduce
    bit-for-bit. That is the DEFINITION of the defect, not a regression — Phase 14 never compared
    this arm against anything, so pairing was not in play there; Phase 16 does compare, which is why
    the fix is a prerequisite rather than polish.

    Three consequences, all deliberate:

    * ``results/phase14_recall_report.md`` is NOT amended. The published number stays exactly as
      published, and this delta is reported separately (D-13).
    * The delta is a REPORTED MEASUREMENT of the fix's impact. It is never a silent assertion that
      the fix did not matter, which is what reusing the published number would have been.
    * It never feeds a threshold. ``LADDER_FLOOR_*`` and ``LADDER_CELL_PASS_K`` stay anchored to
      the committed number; re-anchoring them to this one would set the gate after seeing data,
      which is the single failure a pre-registration exists to prevent.

    The difference is reported in QUESTION units, because that is the unit STAT-01 permits and the
    unit both numbers are natively in.
    """
    n_questions = len(top_rung_result["questions"])
    _prove(
        n_questions == LADDER_FLOOR_QUESTIONS,
        f"the top rung scored {n_questions} questions against a floor of {LADDER_FLOOR_QUESTIONS} "
        "— a difference between two different denominators is not a delta",
    )
    answerable = top_rung_result["n_answerable"]
    return {
        "committed_floor": floor_in_both_units(),
        "rerun": {
            "n_answerable": answerable,
            "questions": n_questions,
            "rate": answerable / n_questions,
            "wilson_upper_95": wilson_upper_bound(answerable, n_questions),
            "k": top_rung_result["k"],
            "n": top_rung_result["n"],
        },
        "difference_questions": answerable - LADDER_FLOOR_ANSWERABLE,
        "citation": LADDER_FLOOR_SOURCE,
    }


# D-15's proxy cell: the hardest SYNTHETIC rung, which is by construction the rung immediately
# below the top one in the committed difficulty order. Derived from that order rather than retyped,
# so the pair being compared cannot drift from the lattice.
PROXY_CELL = RUNG_DIFFICULTY_ORDER[-2]

# The divergence rule, committed HERE — before either number exists. The threshold is the cell
# gate's own integer rather than a second literal: a separate one would be free to be chosen once
# the two counts were on the table, which is exactly the move this milestone exists to block.
PROXY_DIVERGENCE_RULE = (
    f"DIVERGES when the two cells differ by at least {LADDER_CELL_PASS_K} answerable questions "
    f"out of {LADDER_CELL_QUESTIONS} — the same integer LADDER_CELL_PASS_K sets for a cell to "
    "pass, so the synthetic substitution is called unfair exactly when it moves the count by as "
    "much as passing a rung does"
)

# Recorded, not silently repaired (16-05's handover concern). D-15 says the two cells differ ONLY
# in material; with the committed builder signature they also differ in FRAME, and a number read
# without that caveat would be read as stronger than it is.
PROXY_FRAME_CAVEAT = (
    "CAVEAT — these two cells also differ in FRAME, not only in material. `build_far_prompt`'s "
    "committed signature carries no fact id, so its persona line is ONE fact-agnostic sentence "
    "used for all eight facts, while the fairness control gives each fact its own first-person "
    "taught statement. For the name slot the two frames coincide; for the other seven the "
    "synthetic cell's persona names a different slot than the question asks about, which the "
    "control never does. The signature is locked, so this is reported as a limit on the "
    "comparison rather than repaired by changing it. It makes the two verdicts asymmetric: "
    "CONSISTENT is the stronger reading, because it holds despite the extra difference, while "
    "DIVERGES is ambiguous between the frame and the material and cannot separate them."
)


def proxy_validity(cell_results, top_rung_result):
    """D-15: is the synthetic substitution a fair proxy for the real taught values?

    The ``(span 5, distance ~30)`` cell and the top rung are the same prompt position, the same
    median span length, the same denominator and the same draw count. Comparing them directly is
    the only check in this phase on whether the ladder's synthetic material behaves like the real
    material — and if they diverge badly, EVERY low rung of the ladder is suspect and the report
    must say so rather than quietly reporting the rungs as if they stood.

    It costs zero: both measurements already exist in the approved design, so this is a
    subtraction between two numbers the run produces anyway.

    The rule is ``PROXY_DIVERGENCE_RULE``, committed above before either number existed, and its
    threshold is ``LADDER_CELL_PASS_K`` rather than a fresh literal. ``PROXY_FRAME_CAVEAT`` travels
    in the returned dict so the number cannot be rendered without it.
    """
    _prove(
        PROXY_CELL in cell_results,
        f"the proxy-validity check needs the {PROXY_CELL} cell and it was not measured — D-15's "
        "comparison is not optional, it is what tells the ladder's low rungs from noise",
    )
    synthetic = cell_results[PROXY_CELL]["n_answerable"]
    real = top_rung_result["n_answerable"]
    difference = synthetic - real
    return {
        "cell": PROXY_CELL,
        "synthetic_answerable": synthetic,
        "real_answerable": real,
        "questions": LADDER_CELL_QUESTIONS,
        "difference": difference,
        "rule": PROXY_DIVERGENCE_RULE,
        "verdict": "proxy_diverges"
        if abs(difference) >= LADDER_CELL_PASS_K
        else "proxy_consistent",
        "frame_caveat": PROXY_FRAME_CAVEAT,
    }


# =============================================================================================
# THE REPORT — written by the driver, its text committed BEFORE the numbers it will carry
# =============================================================================================

LADDER_REPORT_PATH = _REPO_ROOT / "results" / "phase16_ladder_report.md"  # COMMITTED evidence

# D-14's licensing rule, VERBATIM from 16-CONTEXT.md. Reproduced as a single-source constant so a
# re-wrap or a tidy-up cannot silently paraphrase the pre-registration:
# `test_report_carries_the_d14_verbatim_clause` rebuilds it from that file and compares byte for
# byte (T-16-27). Portuguese because that is the language it was recorded in; translating it here
# would be the paraphrase the test exists to catch.
D14_CLAUSE = (
    "licensed_headline() ramifica no degrau mais alto aprovado, com threshold literal "
    'módulo-level commitado por célula antes da corrida (STAT-05). Ramo "nenhum degrau aprovado" '
    "licencia só o enunciado de déficit de capacidade do SC1. Violação de monotonicidade "
    "registrada como anomalia de instrumento no relatório, sem parar a corrida — mas nomeada "
    "explicitamente, não silenciada."
)

REPORT_FRAMING = (
    "**What this report is FOR.** It licenses — or refuses to license — this phase's headline, "
    "and PERS-01 requires it RECORDED BEFORE any comparison is scored. Everything downstream "
    "reads it as a committed fact; nothing downstream may re-run, re-anchor or re-interpret it. "
    "The thresholds below were committed in git before this run produced a single number, and "
    "the verdict section is `licensed_headline()`'s own output rather than prose written around "
    "the result.\n"
    "\n"
    "**An all-fail ladder is a NORMAL, PRE-REGISTERED outcome — not a broken instrument.** Phase "
    "14 already measured this exact model with this exact prompt builder at the floor cited "
    "below. There is deliberately no 'the ladder failed, investigate the instrument' branch: that "
    "would be an unwritten branch discovered after seeing the result. The instrument-broken "
    "signal is NON-MONOTONICITY — a harder rung passing while an easier one fails — which is "
    "reported under its own heading, named explicitly, without stopping the run and without "
    "moving the licensed branch."
)


def assert_ladder_report_not_clobbered():
    """A RECORDED verdict is committed evidence. Refuse to overwrite it (T-16-22).

    Mirrors ``phase14_recall.assert_report_not_clobbered``, and called at the TOP of the run for
    the same reason: a multi-hour run that refuses to write its report at the end has already been
    wasted. Here the stake is higher than a wasted run — PERS-01 makes this report the licensing
    boundary for the whole phase, so a second run over a recorded verdict destroys the evidence
    everything downstream rests on.

    **Anchored on the SECTION via ``_verdict.VERDICT_SECTION``, never on ``split`` of the heading
    literal** — the 15-04 CR-02 defect. Taking the tail after the LAST occurrence of the heading
    string put the guard's read inside a later section that quotes it, which never says PENDING, so
    the guard fired on every legitimate re-drive and ``--force`` became the only way through. An
    operator who learns that a force flag is always required passes it after a human HAS recorded a
    verdict, and the guard then destroys exactly the material it exists to protect. There is no
    force flag here at all: this driver's report is written once.

    ``None`` (no verdict section) and a body without ``PENDING`` are both refusals — a file that is
    not this writer's output must not be blindly overwritten either.
    """
    if not LADDER_REPORT_PATH.exists():
        return
    recorded = recorded_verdict(LADDER_REPORT_PATH.read_text(encoding="utf-8"))
    if recorded is None or "PENDING" not in recorded:
        raise SystemExit(
            f"[phase16_ladder] {LADDER_REPORT_PATH} already carries a recorded verdict — it is "
            "the committed PERS-01 licensing decision, recorded before any comparison was scored. "
            "Re-running over it would destroy the evidence this phase rests on, and the new "
            "number could not be re-derived without breaking the pre-registration. There is no "
            "force flag: if this report must genuinely be regenerated, delete it in a reviewed "
            "commit so the removal is visible in the diff."
        )


def _rung_rows(cell_results, top_rung_result):
    """``{rung: cell_report row}`` for all seven rungs — the shape the committed helpers take.

    ``licensed_headline`` and ``monotonicity_anomalies`` were committed in 16-04 against
    ``cell_report`` ROWS, not against run results, so the conversion happens once here rather than
    at each call site. Every rung must be present: a six-row ladder rendered as a full one is a
    partial measurement presented as a complete one.
    """
    rows = {}
    for rung in RUNG_DIFFICULTY_ORDER:
        result = top_rung_result if rung == TOP_RUNG else cell_results.get(rung)
        _prove(
            result is not None,
            f"rung {rung} is missing from the ladder results — a report rendering "
            f"{len(cell_results)} synthetic cells as the committed ladder would present a partial "
            "measurement as a complete one",
        )
        rows[rung] = cell_report(result["n_answerable"])
    return rows


def write_ladder_report(cell_results, top_rung_result, provenance_lines):
    """Write ``results/phase16_ladder_report.md`` — the committed PERS-01 licensing decision.

    Every framing string is a module-level constant committed before the run (the ``D-20``
    register Phase 14 established), every number is interpolated from the run or formatted by the
    committed helpers, and the verdict is ``licensed_headline``'s output rather than prose written
    around it. A report whose text is written after the numbers is a report written to fit them.
    """
    assert_ladder_report_not_clobbered()

    rows = _rung_rows(cell_results, top_rung_result)
    delta = top_rung_delta(top_rung_result)
    proxy = proxy_validity(cell_results, top_rung_result)
    anomalies = monotonicity_anomalies(rows)
    licence = licensed_headline([rung for rung, row in rows.items() if row["passed"]])
    floor = delta["committed_floor"]

    blocks = [
        "# Phase 16 Capability Ladder (PERS-01 / STAT-01 / STAT-02 / STAT-05)",
        "",
        "## Run Provenance",
        "",
    ]
    blocks += [f"- {line}" for line in provenance_lines]
    blocks += ["", "## What This Ladder Licenses", "", REPORT_FRAMING, "", "## Pre-registration"]
    blocks += [
        "",
        "Committed in `scripts/phase16_ladder.py` BEFORE this run, and printed here by formatting "
        "those constants — never by retyping them (T-16-15).",
        "",
        "| constant | value |",
        "| --- | --- |",
    ]
    # "Every LADDER_* constant" is true BY CONSTRUCTION rather than by a hand-kept list: a
    # constant added later appears here without anyone remembering to add it. The report's own
    # path is not a pre-registered quantity, which is why the framing prose is named
    # REPORT_FRAMING rather than LADDER_-anything: this filter is a prefix, not a judgement.
    blocks += [
        f"| `{name}` | `{value}` |"
        for name, value in sorted(globals().items())
        if name.startswith("LADDER_") and not name.endswith("_PATH")
    ]

    blocks += [
        "",
        "## The Rungs",
        "",
        "One row per rung of `RUNG_DIFFICULTY_ORDER`, easiest first. The distance column is the "
        "MEASURED token distance from the value's end to the `<|assistant|>` trigger over this "
        "run's own prompts (T-16-21) — the grid's `~2` / `~30` are labels, and the far row is a "
        "DISTRIBUTION rather than a constant, so min / median / max are all printed. Every cell "
        "carries its denominator and a bound; a cell scoring nothing also carries the "
        "rule-of-three ceiling (STAT-02).",
        "",
        "| rung | span | measured distance (min / median / max) | cell |",
        "| --- | --- | --- | --- |",
    ]
    for rung in RUNG_DIFFICULTY_ORDER:
        if rung == TOP_RUNG:
            span = "median 5 (real taught values)"
            distances = "not measured — the shared control records no per-question distance"
        else:
            span = rung[0]
            measured = cell_results[rung]["distances"]
            distances = f"{measured['min']} / {measured['median']:g} / {measured['max']}"
        # The committed formatter renders every number; only its separator is swapped, because a
        # pipe is the markdown table's own delimiter.
        blocks.append(
            f"| `{rung}` | {span} | {distances} | {format_cell(rows[rung]).replace(' | ', ' · ')} |"
        )

    rerun = delta["rerun"]
    blocks += [
        "",
        "## Top Rung — the fairness control RE-RUN post-fix (D-13 / D-19)",
        "",
        f"Committed floor: `{delta['citation']}`. The SAME control over the SAME questions, "
        "re-run on REAL taught values after the PERS-05 pairing fix.",
        "",
        "| unit | count | rate | one-sided 95% Wilson upper | note |",
        "| --- | --- | --- | --- | --- |",
        f"| committed floor, {floor['draws']['label']} | "
        f"{floor['draws']['successes']} of {floor['draws']['n']} | "
        f"{floor['draws']['rate']:.6f} | {floor['draws']['wilson_upper_95']:.6f} | "
        "reported for reconciliation with the committed Phase 14 report; NOT a legal unit for "
        "inference |",
        f"| committed floor, {floor['questions']['label']} | "
        f"{floor['questions']['successes']} of {floor['questions']['n']} | "
        f"{floor['questions']['rate']:.6f} | {floor['questions']['wilson_upper_95']:.6f} | "
        "the unit every number in this milestone is compared in |",
        f"| this re-run, {floor['questions']['label']} | "
        f"{rerun['n_answerable']} of {rerun['questions']} | {rerun['rate']:.6f} | "
        f"{rerun['wilson_upper_95']:.6f} | draws: {rerun['k']} of {rerun['n']} |",
        "",
        f"**Measured delta, in question units: {delta['difference_questions']:+d} answerable "
        f"questions** out of {rerun['questions']}.",
        "",
        "**D-19 — this number is not expected to reproduce the committed one bit-for-bit.** The "
        "PERS-05 fix changes WHICH SEEDS ARE DRAWN: the control used to seed from its own loop "
        "position and now seeds from each question's stamped index, so different completions come "
        "back. That is the DEFINITION of the defect, not a regression — Phase 14 never compared "
        "this arm against anything, so pairing was not in play there; Phase 16 does compare, which "
        "is why the fix is a prerequisite rather than polish. `results/phase14_recall_report.md` "
        "is deliberately NOT amended: the published number stays exactly as published, and the "
        "delta above is a REPORTED MEASUREMENT of the fix's impact rather than a silent assertion "
        "that it did not matter. It never fed a threshold — the gate stays anchored to the "
        "committed number, because re-anchoring it to a number this phase measured would be "
        "setting the gate after seeing data.",
        "",
        "**Why both units are printed** (T-16-26). The draw-unit bound is roughly nine times "
        "tighter than the question-unit one. Citing the draw unit alone makes the prompt arm look "
        f"far more definitively at zero than STAT-01's unit supports, and the ceiling if the floor "
        f"had scored nothing at all would still be {floor['rule_of_three_upper']:.6f} "
        f"(rule of three at {floor['questions']['n']} questions).",
        "",
        "## Proxy Validity (D-15)",
        "",
        f"The `{proxy['cell']}` synthetic cell against the top rung: same prompt position, same "
        "span length, same denominator, same draw count — differing in MATERIAL (a gate-cleared "
        "synthetic string versus the real taught value). If they diverge badly, every low rung of "
        "this ladder is suspect and any reading built on those rungs must say so.",
        "",
        f"- synthetic `{proxy['cell']}`: **{proxy['synthetic_answerable']} of "
        f"{proxy['questions']}** answerable questions",
        f"- top rung (real values): **{proxy['real_answerable']} of {proxy['questions']}** "
        "answerable questions",
        f"- difference: **{proxy['difference']:+d}** questions",
        f"- committed rule: {proxy['rule']}",
        f"- **VERDICT: `{proxy['verdict']}`**",
        "",
        proxy["frame_caveat"],
        "",
        "## Monotonicity Anomalies",
        "",
        "A harder rung passing while an easier one fails means the rungs are not ordered by the "
        "difficulty the grid claims, and every reading built on that order is suspect. Per D-14 "
        "an anomaly is NAMED here without stopping the run and without moving the licensed "
        "branch — this is the instrument-broken signal, and an all-fail ladder is not.",
        "",
    ]
    blocks += (
        [
            f"- **ANOMALY** — `{harder}` passed while the easier `{easier}` failed"
            for easier, harder in anomalies
        ]
        if anomalies
        else ["_None: no harder rung passed while an easier one failed._"]
    )

    blocks += [
        "",
        "## Verdict",
        "",
        f"**Branch: `{licence['branch']}`** — highest passed rung: `{licence['highest_passed']}`.",
        "",
        licence["statement"],
        "",
        "### The pre-registered licensing rule (D-14, verbatim)",
        "",
        f"> {D14_CLAUSE}",
        "",
    ]

    text = "\n".join(blocks)
    # The guard that protects this file on the NEXT run reads a `## Verdict` SECTION. A report this
    # writer produced must be one that guard can anchor on, or the protection is nominal.
    _prove(
        VERDICT_SECTION.search(text) is not None,
        "the rendered report carries no `## Verdict` section the clobber guard could anchor on, "
        "so a later run would overwrite the committed licensing decision in silence",
    )
    LADDER_REPORT_PATH.write_text(text, encoding="utf-8")
    print(f"[phase16_ladder] wrote {LADDER_REPORT_PATH}")
    print(f"[phase16_ladder] licensed branch: {licence['branch']} ({licence['highest_passed']})")
    return text


def run_full_ladder():
    """The whole ladder on the real weights: six synthetic cells, then the top rung, then a report.

    Order is not incidental. The clobber guard runs BEFORE anything expensive, because a run that
    refuses to write its report at the end has already been wasted. The rungs run in
    ``RUNG_DIFFICULTY_ORDER`` so the raw log reads easiest-to-hardest and a partial run is still
    interpretable. The report is written LAST, from the numbers, with text that was committed
    before them.
    """
    import phase14_recall as recall  # LAZY — see the LAZY-IMPORT RULE in the module docstring.
    import torch

    from personacore.config import RuntimeConfig
    from personacore.preflight import preflight_device
    from personacore.seeding import seed_everything

    started = time.time()
    assert_ladder_report_not_clobbered()
    summary = preflight_device(strict=True)
    print(f"[phase16_ladder] preflight: {summary}")
    device = RuntimeConfig().device
    # ONE seed constant in play, the instrument's own: `draw_all` derives every per-draw generator
    # from `phase14_recall.question_seed`, so a fresh literal here would be free to drift from the
    # one that actually drives the draws.
    seed_everything(recall.SEED)

    model, _model_cfg, tok, forbid, artifact = recall.load_adapted_model(device)
    items = load_core_items()
    print(f"[phase16_ladder] {len(items)} core questions, {len(RUNG_DIFFICULTY_ORDER)} rungs")

    cell_results = {}
    for rung in RUNG_DIFFICULTY_ORDER:
        if rung == TOP_RUNG:
            continue
        span, distance = rung
        print(
            f"[phase16_ladder] ===== rung {rung}: span {span}, nominal distance ~{distance} ====="
        )
        result = run_ladder_cell(model, tok, device, forbid, items, span=span, distance=distance)
        cell_results[rung] = result
        print(f"[phase16_ladder] rung {rung}: {format_cell(result['cell'])}")

    print(f"[phase16_ladder] ===== rung {TOP_RUNG}: the fairness control, REAL values (D-13) =====")
    top_rung_result = run_top_rung(model, tok, device, forbid, items)
    top_row = cell_report(top_rung_result["n_answerable"])
    print(f"[phase16_ladder] rung {TOP_RUNG}: {format_cell(top_row)}")

    wall = time.time() - started
    provenance_lines = recall.echo_provenance(summary, device, artifact) + [
        f"torch: {torch.__version__}",
        f"ladder wall clock: {wall / 60:.1f} min",
        f"rungs: {len(RUNG_DIFFICULTY_ORDER)} x {LADDER_CELL_QUESTIONS} questions x "
        f"{LADDER_CELL_DRAWS} draws",
    ]
    write_ladder_report(cell_results, top_rung_result, provenance_lines)
    print(f"[phase16_ladder] ladder complete in {wall / 60:.1f} min")


_USAGE = (
    "[phase16_ladder] usage: python scripts/phase16_ladder.py [--vet]\n"
    "  (no arguments)  run the full PERS-01 capability ladder and write "
    "results/phase16_ladder_report.md — the licensing decision PERS-01 requires recorded before "
    "any comparison is scored.\n"
    "  --vet           the ONE-TIME material vetting run (already executed; re-running it "
    "regenerates results/phase16_ladder_material.md, it does not re-choose the material).\n"
    "An unrecognized argument is refused rather than ignored: silently falling through to a "
    "multi-hour run because a flag was mistyped is the expensive failure here."
)


def main():
    """Two modes, both named; an unrecognized argument is refused rather than ignored.

    16-05 shipped this driver with ``--vet`` as its only mode and an argumentless invocation
    exiting non-zero, because the full-ladder run belonged to a later plan and must not have been
    inherited by accident. That plan is this one: the ladder run IS this driver's job now, so the
    no-argument default is the full run and 16-07 invokes it bare. The refusal that mattered is
    kept where it still matters — an argument this driver does not recognize exits non-zero
    instead of launching ~80 minutes of generation.
    """
    args = sys.argv[1:]
    unknown = [arg for arg in args if arg != "--vet"]
    if unknown:
        raise SystemExit(f"[phase16_ladder] unrecognized argument(s) {unknown}\n{_USAGE}")
    if "--vet" in args:
        vet_synthetic_candidates()
        return
    run_full_ladder()


if __name__ == "__main__":
    main()
