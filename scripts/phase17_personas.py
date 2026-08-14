"""Phase 17 multi-persona isolation matrix — the PRE-REGISTRATION (STAT-05).

Committed BEFORE the three adapters train, before a single persona value is minted and before any
``results/phase17_*`` artifact exists. The six-comparison Holm family, the per-comparison declared
direction, the three training seeds, the ISO-05 replication seeds, the D-18 all-six gate rule, the
D-19 ``worst_pair`` tie-break, the D-10 all-fail branch and the four mechanical minting filters are
module-level literals here so that git history — not prose — is the proof that none of them was
chosen after seeing a number. Same register as ``scripts/phase16_persistence.py:1001-1044``.

Nothing executes at import except the ``sys.path`` bootstrap below. Constants and pure functions
only: no torch import at module scope, no model load, no tokenizer load, no generation and no
``main()``, so an ``importlib`` load in a CPU-only test runs no guard and no model.

**THIS FILE HOLDS THE PRE-REGISTRATION ONLY — NEVER THE PERSONA MATERIAL.** The two live in two
files on purpose and the split is load-bearing rather than cosmetic.
``tests/test_phase16_prereg.py`` asserts that EVERY commit touching THIS file is an ancestor of
every ``results/phase17_*`` first-add commit. Gate constants are immutable once pushed, so that pin
costs nothing. The 24 minted values are legitimately mutable at the ISO-01 gate: plan 17-07's ADAPT
branch is an explicitly SC2-sanctioned outcome that replaces named values AFTER
``results/phase17_personas_report.md`` has been committed. If the values lived here, taking that
branch would land a pre-registration commit after a results artifact's first add — and
``git log --diff-filter=A`` returns that EARLIEST add — so the guard would be permanently red with
no recovery short of history surgery. The 24 minted values, their measured token census and the
derived forbidden set therefore live in ``scripts/phase17_persona_facts.py`` (plan 17-03), which
the guard does NOT pin. A future reader who "tidies up" by merging the two files re-arms that trap.
(Those three constant NAMES are deliberately not written out here either: the pinned file is
scanned for them, and a docstring mention would make that scan hit on prose.)

LAZY-IMPORT RULE — inherited from ``phase16_persistence`` and load-bearing here for the same
reason. ``phase14_recall``'s scoring primitives (``normalize``, ``contains_value``) and any Phase 14
or Phase 17 fact material may be imported ONLY inside function bodies, so no value string reaches
this module's own import-time surface: a module's constants and docstrings are exactly what the
clean-room scans walk.
"""

import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# `scripts/` is sys.path[0] only when a script in it is run DIRECTLY; an importlib-loaded test
# harness gets no such entry (phase16_persistence.py:34-38 precedent). Insert it explicitly so both
# paths reach the sibling driver. This is the ONE module-level call this file is permitted, and
# `tests/test_phase17_stats.py` asserts exactly that.
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import phase16_persistence as persistence  # noqa: E402  (needs the sys.path insert above)

# =============================================================================================
# ===== The matrix shape =======================================================================
# =============================================================================================

PERSONAS = ("persona_a", "persona_b", "persona_c")

# D-03 / Phase 16 D-07 — IMPORTED, never retyped. The tier this phase gates is the tier Phase 16
# gated, and a second "held-out" literal is a second string free to stop agreeing with the first.
GATED_TIER = persistence.GATED_TIER

# D-02 — the join key is the SLOT, never the fact id. Every Phase 14 fact id embeds its own value
# (`cand_town_<value>`), so keying by id would drag Phase 14 values into this matrix.
#
# THIS IS THE ONE CANONICAL SLOT LIST, in RESEARCH F-02's measured fixture order. Plan 17-04's
# fixture regrouping and plan 17-03's minted material are each checked against THIS tuple rather
# than against each other: two things checked against a third cannot drift into agreeing on a wrong
# answer, whereas two things checked against each other can.
CORE_SLOTS = (
    "person_name",
    "pet_name",
    "cat_name",
    "sibling_name",
    "hometown",
    "street",
    "birth_year",
    "house_number",
)

# DERIVED, never a retyped 8 — this is D-08's n, and a second literal for it is a second number
# that can stop agreeing with the list it counts.
SLOTS_EXPECTED = len(CORE_SLOTS)

# RESEARCH F-02, the measured `core_held_out` fixture shape: 13 questions per slot x 8 slots = 104.
QUESTIONS_PER_SLOT = 13

# ISO-03 — the adapter-off row label, committed here so the sweep, the scorer and the report writer
# share ONE literal. It is a REPORTED row and never a GATED one: the base cell `(base, j)` is the
# only quantitative separator of "adapter i leaked j's value" from "the base was going to say that
# anyway" (RESEARCH:900). `HOLM_FAMILY_CELLS` below excludes it BY CONSTRUCTION — the comprehension
# ranges over PERSONAS, which does not contain it — and `assert_phase17_family_closed` re-proves
# that at runtime against a dynamically-built cell list no static reading would see.
BASE_ROW = "base"

# =============================================================================================
# ===== D-08 / D-18 — the closed family of six gated comparisons ================================
# =============================================================================================
#
# DERIVED from PERSONAS, never a hand-typed list of six: a retyped family is a family that can stop
# matching the cells it claims to compare (phase16_persistence.py:1001, the same rule in the same
# words). One member per adapter row i: that row's DIAGONAL cell (i, i) against each of its two
# OFF-DIAGONAL cells (i, j). 3 rows x 2 off-diagonals = 6, and 6 is where D-08 closes the family.
#
# The contrast is WITHIN adapter i, which is what makes D-14's distinct-per-persona seed safe for
# the gate: cell (i, i) and cell (i, j) share adapter i, hence share seed i, so the seed cancels
# inside the gated quantity.
HOLM_FAMILY_CELLS = tuple(((i, i), (i, j)) for i in PERSONAS for j in PERSONAS if i != j)

# D-29's register, repriced for this phase — THE DECLARED DIRECTION OF THE ALTERNATIVE, PER
# COMPARISON, COMMITTED BEFORE ANY ADAPTER TRAINS. Without a committed direction the sign could be
# fixed AFTER the signs are visible, which is exactly what STAT-05 forbids. The rule is the same for
# all six and is stated explicitly rather than left to a convention a reader would have to
# reconstruct: the diagonal cell exceeds the off-diagonal cell, in the question unit (`SIGN_UNIT`),
# paired at slot level over the eight `CORE_SLOTS`.
#
# Spelled out per member rather than generated, so a reviewer audits six committed statements
# instead of a comprehension. Key-set equality with `HOLM_FAMILY_CELLS` is proved at RUNTIME by
# `assert_phase17_family_closed`, never by construction — generating this dict would make the
# equality true by definition and prove nothing.
CELL_ALTERNATIVE = {
    (("persona_a", "persona_a"), ("persona_a", "persona_b")): (
        "persona_a's own value exceeds persona_b's value under adapter persona_a"
    ),
    (("persona_a", "persona_a"), ("persona_a", "persona_c")): (
        "persona_a's own value exceeds persona_c's value under adapter persona_a"
    ),
    (("persona_b", "persona_b"), ("persona_b", "persona_a")): (
        "persona_b's own value exceeds persona_a's value under adapter persona_b"
    ),
    (("persona_b", "persona_b"), ("persona_b", "persona_c")): (
        "persona_b's own value exceeds persona_c's value under adapter persona_b"
    ),
    (("persona_c", "persona_c"), ("persona_c", "persona_a")): (
        "persona_c's own value exceeds persona_a's value under adapter persona_c"
    ),
    (("persona_c", "persona_c"), ("persona_c", "persona_b")): (
        "persona_c's own value exceeds persona_b's value under adapter persona_c"
    ),
}

# STAT-01's declaration, committed before assembly exists. RESEARCH F-11: `fact_signs` reads
# `["rate"]` off whatever dict it is handed, and `aggregate_by_fact`'s `rate` is the DRAW rate
# (k / 9 draws). Phase 17 hands it `n_answerable / n_questions` instead — the QUESTION unit —
# because D-08 pairs at SLOT level and a slot's paired observation is its question rate. The
# substitution lives at assembly rather than inside the imported statistics, so this constant is
# where it is declared and the only place it can be audited before the numbers exist.
SIGN_UNIT = "question"

# =============================================================================================
# ===== D-14 / D-16 / D-20 — seeds and adapter configuration ===================================
# =============================================================================================

# D-14 — a DISTINCT seed per persona, not one shared seed. The argument that holds is
# initialization DIVERSITY: under a single seed the whole matrix rests on one init draw and a clean
# result could be an artifact of that draw. It is safe for the gate because the gated contrast is
# WITHIN adapter i (see `HOLM_FAMILY_CELLS`), so the seed cancels inside it.
#
# D-15 is the price and is BINDING: with n = 1 seed per persona, between-persona comparisons
# confound content with seed, so the three diagonals are three separate ANCHORS and never a
# RANKING. No report sentence may order the personas by diagonal.
PERSONA_SEEDS = {"persona_a": 1337, "persona_b": 1338, "persona_c": 1339}

# D-19 / D-16 — ISO-05's k = 3 replication seeds, k COUNTING THE ORIGINAL SEED, so each persona
# contributes its already-trained adapter plus 2 additional seeds. DERIVED from `PERSONA_SEEDS`
# rather than retyped, for the same reason the family is derived.
#
# Pre-registered HERE, in Wave 1, because the replication runs AFTER the matrix is read: seeds
# chosen at that point would be seeds chosen with the numbers in view. The replication is
# descriptive only (min / max / median, never a hypothesis test) — `gate_cleared` is closed at the
# six `HOLM_FAMILY_CELLS` and structurally cannot admit a replication row.
REPLICATION_SEEDS = {
    persona: (seed, seed + 100, seed + 200) for persona, seed in PERSONA_SEEDS.items()
}

# D-20 — the three adapters train at `LoRAConfig()` DEFAULTS. A non-default alpha is now *safe*
# (the `src/personacore/lora/inject.py` scale audit would catch a consumer that ignored it) but
# buys nothing this phase measures, and it would COST the anchor that `ALL_FAIL_BRANCH` depends on.
# Recorded as a NOTE and never as a constructed `LoRAConfig`: there is no torch import in this
# module and this file must stay loadable with no torch in the process at all.
LORA_CONFIG_NOTE = (
    "the three Phase 17 adapters train at LoRAConfig() defaults (r=8, alpha=16.0, scale 2.0) so "
    "the three diagonals stay directly readable against Phase 14's 0.3483 held-out rate (draw "
    "unit) and Phase 16's 0.865385 (question unit)"
)

# =============================================================================================
# ===== D-18 / D-10 — the gate rule and the branch taken when it does not clear =================
# =============================================================================================

# D-18's pre-registration text, VERBATIM and not paraphrasable. Split across source lines only
# because it exceeds the line limit; implicit concatenation reproduces it byte for byte, and
# `tests/test_phase17_stats.py` asserts it against `17-CONTEXT.md` — the planning artifact itself —
# rather than against a second hand-typed copy. "Verbatim" checked against a second copy proves
# only that two copies agree, which is the failure mode a verbatim requirement exists to prevent.
GATE_AGGREGATION_RATIONALE = (
    "os seis pares testam diretamente vazamento entre as três personas reais (não contra pisos "
    "estruturais como na Fase 16), então uma alegação de isolamento parcial não sustenta o "
    "objetivo da fase."
)

# D-10's PRE-REGISTERED ALL-FAIL BRANCH, committed before any number exists. It fires on anything
# less than six Holm rejections (D-18), and there is deliberately no investigate-the-instrument
# escape hatch (Phase 16 D-14's register).
ALL_FAIL_BRANCH = (
    "If the gate does not clear, the report MUST publish alongside the verdict: (a) the diagonal "
    "magnitude for each of the three personas, as a recall rate with its two-stage cluster "
    "bootstrap CI, and (b) the adapter-off column result. Both are required, not either. If the "
    "diagonal is LOW, the report must explicitly declare that the matrix has NO POWER to judge "
    "isolation: 'not demonstrated' then means 'not judgeable', never 'isolation failed'. If the "
    "diagonal is HIGH and an off-diagonal is also high enough to block 8/8 slot unanimity, that is "
    "a real leakage finding and is reported as one. In neither fork may any sentence order the "
    "three personas by diagonal (D-15): with one seed per persona a between-persona difference "
    "confounds content with initialization, so the diagonals are three separate anchors and never "
    "a ranking."
)

# =============================================================================================
# ===== Pitfall 6 — the four mechanical minting filters ========================================
# =============================================================================================

# The token ceiling every minted value must respect. NOT a taste threshold: `RECALL_MAX_NEW_TOKENS`
# is 48 because `phase14_recall.derive_recall_budget` computes `max(census) + PREAMBLE_HEADROOM
# (32) + TAIL_HEADROOM (8)` rounded up to a multiple of 8, and the measured census maxes at 8
# (`phase14_recall.py:120-145`). A 9-token value pushes the raw budget to 49 and the rounded budget
# to 56, which breaks generation parity with `phase16_persistence.SHARED_ARM_CONFIG` and therefore
# with every published Phase 14 and Phase 16 number.
MAX_VALUE_TOKENS = 8


def _prove(condition, message):
    """Loud proof: ``SystemExit`` naming the violated contract (never an ``-O``-strippable one).

    Same register and same reason as ``phase14_recall._prove`` and ``phase16_persistence._prove``,
    with this module's own prefix — an abort that names the wrong driver sends its reader to the
    wrong file. Never import another driver's ``_prove``: the prefix is the whole point.
    """
    if not condition:
        raise SystemExit(f"[phase17_personas] PROOF FAILED: {message}")


def assert_phase17_family_closed(entered_pairs):
    """Exactly ``HOLM_FAMILY_CELLS`` entered the gate — no more, no less, and no base row.

    The RUNTIME half of the T-16-38 discipline, repriced for this phase. The static AST scan in
    ``tests/test_phase17_stats.py`` catches a NEW CALL SITE; this catches a DYNAMICALLY-BUILT cell
    list. Both are needed, because a seventh gated comparison can arrive by either route and either
    guard alone leaves the other open.
    """
    entered = tuple(entered_pairs)
    _prove(
        len(entered) == len(set(entered)),
        f"the same comparison entered the Holm family twice: {entered}. A duplicated hypothesis "
        "inflates m without adding evidence, which lowers alpha for every other comparison at no "
        "cost to itself",
    )
    # Checked BEFORE the set-equality proof on purpose. Any cell naming the base row also makes the
    # entered set differ from HOLM_FAMILY_CELLS, so ordering this second is what keeps it reachable
    # — a `_prove` that can never fire is a `_prove` nobody can watch fail.
    offenders = sorted(
        pair for pair in entered if BASE_ROW in (cell for member in pair for cell in member)
    )
    _prove(
        not offenders,
        f"{offenders} name the adapter-off row {BASE_ROW!r}, which is a PUBLISHED CONTROL and "
        "never a gated comparison (ISO-03). Gating it would make a seventh comparison, and at "
        "m = 7 Holm's first alpha is 0.0071429 — below the achievable p of 0.0078125 — so the "
        "headline would die arithmetically at every possible outcome",
    )
    _prove(
        set(entered) == set(HOLM_FAMILY_CELLS),
        f"{len(set(entered))} comparison(s) entered the Holm family, but D-08 closes it at exactly "
        f"{len(HOLM_FAMILY_CELLS)}: {sorted(set(entered) ^ set(HOLM_FAMILY_CELLS))} differ. At "
        "m = 7 alpha is 0.0071429, below the achievable p of 0.0078125, so the headline dies "
        "arithmetically at every possible outcome — including perfect unanimity",
    )
    _prove(
        set(CELL_ALTERNATIVE) == set(HOLM_FAMILY_CELLS),
        f"CELL_ALTERNATIVE declares a direction for {sorted(CELL_ALTERNATIVE)} but the family is "
        f"{sorted(HOLM_FAMILY_CELLS)} — an undeclared comparison is a comparison whose direction "
        "could be fixed after its signs are visible, which is what STAT-05 forbids",
    )


def assert_family_length_matches_phase16(phase16_family_len):
    """RESEARCH F-08 — the two families agreeing at 6 is a COINCIDENCE and must be proved.

    ``phase16_persistence.holm`` prices alpha as ``HOLM_ALPHA / (len(HOLM_FAMILY_PAIRS) - index)``,
    reading PHASE 16's family length, not this phase's. Today both are 6, but Phase 16's 6 is
    ``C(4, 2)`` over four arms and this phase's 6 is ``3 personas x 2 off-diagonals``. The length is
    taken as a PARAMETER so this module imports no sibling driver to check it — the caller reads
    ``len(phase16_persistence.HOLM_FAMILY_PAIRS)`` and hands it over.
    """
    _prove(
        phase16_family_len == len(HOLM_FAMILY_CELLS),
        f"phase16_persistence.holm prices alpha from ITS OWN family of {phase16_family_len}, but "
        f"this phase's family is {len(HOLM_FAMILY_CELLS)}. The two agreeing at 6 is a coincidence "
        "of C(4,2) == 3x2 (RESEARCH F-08), not a shared design: an edit to Phase 16's "
        "CONDITION_ORDER would silently reprice THIS phase's gate with nothing else going red",
    )


def gate_cleared(holm_rows):
    """D-18 — the gate clears only when ALL SIX Holm comparisons reject. Five of six does not.

    ``holm_rows`` is ``phase16_persistence.holm``'s return value: ``[(cells, p, alpha, rejected)]``.
    Returns ``True`` only when the family is complete AND every row rejected; anything less fires
    ``ALL_FAIL_BRANCH``. A truncated family returns ``False`` rather than clearing on a short list,
    because a family populated at five and priced at six is not the test that was registered.

    The rationale is ``GATE_AGGREGATION_RATIONALE``, committed verbatim above: every one of the six
    comparisons is a live isolation claim between two REAL personas, unlike Phase 16's family of
    arms-against-structural-floors, so Phase 16's partial-clear precedent does not transfer.

    All six Holm rows are PUBLISHED regardless of outcome so a partial result stays readable.
    Publishing the rows is not the same as clearing the gate.
    """
    rows = tuple(holm_rows)
    if len(rows) != len(HOLM_FAMILY_CELLS):
        return False
    return all(bool(row[-1]) for row in rows)


def worst_pair(off_diagonal_rates):
    """D-19 — ISO-05's worst-colliding pair, as a function committed before the matrix is read.

    ``off_diagonal_rates`` is ``{(i, j): rate}`` over the six ORDERED off-diagonal cells, in the
    question unit (``SIGN_UNIT``). Returns the unordered pair as ``(i, j)`` with ``i`` before ``j``
    in ``PERSONAS`` order, maximising ``mean(rate[(i, j)], rate[(j, i)])`` and tie-broken
    deterministically by lowest index: smallest ``i``, then smallest ``j``.

    **The tie-break is load-bearing, not decoration.** The hoped-for outcome of this phase is that
    every off-diagonal is 0.0 — which makes ``argmax`` a THREE-WAY TIE exactly in the success case.
    Without a committed tie-break the "mechanical" rule would silently degrade into a post-hoc
    choice precisely where it matters most. Under the all-zero tie this returns
    ``("persona_a", "persona_b")``.

    Implemented as a ``min`` over the key ``(-mean, index(i), index(j))`` so the tie-break IS the
    sort key rather than a branch beside it — a branch is a place a later edit can reorder.
    """
    expected = {(i, j) for i in PERSONAS for j in PERSONAS if i != j}
    _prove(
        set(off_diagonal_rates) == expected,
        f"worst_pair received {sorted(off_diagonal_rates)} but D-19 selects over exactly the six "
        f"ordered off-diagonal cells {sorted(expected)} — a missing cell would let the mean of a "
        "pair be computed from one direction only, and a diagonal cell would put a persona's own "
        "recall into a leakage statistic",
    )
    unordered = tuple(
        (PERSONAS[left], PERSONAS[right])
        for left in range(len(PERSONAS))
        for right in range(left + 1, len(PERSONAS))
    )

    def _key(pair):
        first, second = pair
        mean = (off_diagonal_rates[(first, second)] + off_diagonal_rates[(second, first)]) / 2
        return (-mean, PERSONAS.index(first), PERSONAS.index(second))

    return min(unordered, key=_key)


def filter_token_budget(census):
    """Minting filter 1 — every minted value fits ``MAX_VALUE_TOKENS``. Returns ``census``.

    ``census`` is ``{fact_id: measured_token_count}``. See ``MAX_VALUE_TOKENS`` for why 8 is a hard
    ceiling rather than a preference: a 9-token value moves ``RECALL_MAX_NEW_TOKENS`` off 48 and
    breaks generation parity with every published Phase 14 and Phase 16 number.
    """
    over = sorted(key for key, count in census.items() if count > MAX_VALUE_TOKENS)
    _prove(
        not over,
        f"{over} exceed MAX_VALUE_TOKENS = {MAX_VALUE_TOKENS}. The recall budget is derived as "
        "max(census) + 32 + 8 rounded up to a multiple of 8, so a 9-token value moves "
        "RECALL_MAX_NEW_TOKENS from 48 to 56 and this phase stops being comparable to Phase 14 "
        "and Phase 16 at all — the arms would no longer share a generation budget",
    )
    return census


def filter_roundtrip(tok, values):
    """Minting filter 2 — every value survives ``decode(encode(v)) == v`` on only LIVE ids.

    The frozen production tokenizer decodes 547 of the model's 8192 ids, so a value whose encoding
    reaches a dead id cannot be generated at all once ``forbid_ids`` masks them: the persona would
    be untestable rather than merely hard. Duck-typed against ``BPETokenizer`` exactly as
    ``personacore.generation.text.undecodable_ids_mask`` is — ``.vocab`` keyed by int id and
    ``.special_tokens`` name-to-id — so no torch tensor and no model are needed here.
    """
    live = set(tok.vocab) | set(tok.special_tokens.values())
    for value in values:
        ids = tok.encode(value)
        dead = sorted(set(ids) - live)
        _prove(
            not dead,
            f"a minted value encodes to id(s) {dead}, which the frozen tokenizer cannot decode. "
            "forbid_ids masks exactly those ids to -inf before sampling, so the value could never "
            "be produced by the model at any temperature — an unreachable value scores 0 for "
            "reasons that have nothing to do with isolation",
        )
        _prove(
            tok.decode(ids) == value,
            "a minted value does not survive decode(encode(v)) == v. The scorer matches on the "
            "decoded surface string, so a value that changes shape through the tokenizer would be "
            "scored against a string the model was never taught",
        )
    return tuple(values)


def filter_substring_disjoint(minted, forbidden):
    """Minting filter 3 — no value is a substring of another, across minted UNION forbidden.

    Checked under ``phase14_recall.normalize``, which is the same normalization the scorer's
    ``contains_value`` applies — a disjointness proved under a different normalizer is a
    disjointness that does not hold where it matters.

    The concrete failure this prevents: if persona A's value sits inside persona B's value, then
    EVERY correct A-answer also registers as a B-leak, manufacturing an off-diagonal hit out of
    nothing and closing the gate on an artifact of the material rather than on the model. The
    forbidden set is included in the same union because a minted value hiding inside a Phase 14
    value would equally break D-10's contradiction detector.
    """
    from phase14_recall import normalize  # LAZY — keeps value strings off this module's surface

    pool = sorted({*minted, *forbidden})
    collisions = sorted(
        (inner, outer)
        for inner in pool
        for outer in pool
        if inner != outer and normalize(inner) in normalize(outer)
    )
    _prove(
        not collisions,
        f"{collisions} are substring-nested under phase14_recall.normalize (inner, outer). Every "
        "correct answer carrying the outer value would also register as a hit for the inner one, "
        "so an off-diagonal cell would count leakage that never happened and the gate would close "
        "on the choice of material rather than on the model's behaviour",
    )
    return tuple(minted)


def filter_absent_from_questions(minted, questions):
    """Minting filter 4 — no minted value appears in any fixture question (the clean-room property).

    Checked with ``phase14_recall.contains_value``, the scorer's own gate. A question that names a
    value hands the model the answer, and the resulting cell measures copying from the prompt
    rather than recall from the weights — which is the single defect the binding fixture's
    clean-room property (``tests/test_phase16_fixture_regen.py`` guard #4) exists to exclude.
    """
    from phase14_recall import contains_value  # LAZY — see the module docstring's LAZY-IMPORT RULE

    leaks = sorted(
        (value, question)
        for value in minted
        for question in questions
        if contains_value(question, value)
    )
    _prove(
        not leaks,
        f"{leaks} put a minted value inside a fixture question. The cell would then measure "
        "copying from the prompt rather than recall from the weights, and a diagonal inflated that "
        "way is indistinguishable from isolation working",
    )
    return tuple(minted)
