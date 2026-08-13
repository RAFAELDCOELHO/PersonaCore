"""Four-arm weight-vs-prompt comparison driver — the PRE-REGISTRATION (PERS-02 / PERS-04).

Committed BEFORE the run it describes. The condition order, the shared arm-parity config, the
per-question record shape and arm D's chance floor are module-level literals here so git history
is the proof that none of them was chosen after seeing a number (STAT-05 — the same register as
the sibling ``scripts/phase16_ladder.py``).

Nothing executes at import. Constants and pure functions only — ``main()`` lands in plan 16-10
under a ``__main__`` guard — so an ``importlib`` load in a CPU-only test runs no guard, no model
load, no tokenizer load and no generation.

LAZY-IMPORT RULE — inherited, and load-bearing here. ``phase14_factset`` and
``phase14_factset_gate`` may be imported ONLY inside functions: the gate imports the fact set at
MODULE level, so a module-level import of either would pull the locked values into this driver's
address space and into the docstring surface the clean-room scan walks.

The three text arms are the COMMITTED Phase 14 instrument invoked per condition; this module
contributes dispatch, normalization and a parity assertion, and never a second draw loop. A
duplicated draw loop is how two arms silently stop being paired.
"""

import hashlib
import json
import pathlib
import random
import statistics
import sys
from typing import NamedTuple

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# `scripts/` is sys.path[0] only when a script in it is run DIRECTLY; an importlib-loaded test
# harness gets no such entry (phase16_ladder.py:36-40 precedent). Insert it explicitly so both
# paths reach the sibling instrument.
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import phase14_recall as recall  # noqa: E402  (needs the sys.path insert above)

# STAT-04 — the ONLY bounds source in this milestone, IMPORTED and never copied. A third-party
# statistics package has been declined in committed code twice and is forbidden here (the D-16
# register: import the instrument, never re-implement it). `tests/test_package.py` sha256-pins
# `pyproject.toml`, so a new dependency cannot arrive quietly alongside a new statistic.
from erasure_gate import rule_of_three, wilson_upper_bound  # noqa: E402  (needs the insert above)

from personacore.config import ModelConfig  # noqa: E402
from personacore.dialogue import build_recall_prompt  # noqa: E402

# =============================================================================================
# ===== RUN ARCHITECTURE PRE-REGISTRATION (D-01 through D-04) =====
# =============================================================================================

# D-03 — the run's condition order, pre-registered as a literal BEFORE any arm executes. The
# recorded rationale is `CONDITION_ORDER_RATIONALE` below: exactly two reasons, plus the sentence
# D-03 requires verbatim. It lives in a module-level STRING rather than in this comment because
# plan 16-10 prints it into the report and a test pins it byte-for-byte against 16-CONTEXT.md —
# a comment can do neither, and an unpinnable rationale is one free to drift.
CONDITION_ORDER = ("adapter-only", "base-neither", "embedding-cosine", "prompt-stuffed")

# D-03's required sentence, verbatim. Split across two source lines only because it is 141
# characters and the line limit is 100; implicit concatenation reproduces it byte for byte.
CONDITION_ORDER_PREREGISTRATION = (
    "sob o split de quatro processos frescos, o resultado é invariante à ordem — a ordem é "
    "pré-registro puro, sem efeito físico sobre o resultado."
)

CONDITION_ORDER_RATIONALE = (
    "Two reasons are recorded for this order, and exactly two. (1) Pre-registering the order "
    "prevents choosing it after seeing numbers. (2) 'adapter-only first' means the most critical "
    "result is already in hand under interruption. A third rationale was drafted for the last "
    "position and DELETED rather than annotated: it defended against a mechanism the "
    "four-process split already eliminates, and a false rationale left in an artifact is "
    "inherited downstream as true. It is not restorable from anything in this repository, which "
    "is deliberate. " + CONDITION_ORDER_PREREGISTRATION
)

# D-02 — why questions may run sequentially inside one process. BOTH sources are cited
# explicitly, never one alone: the Phase 9 toggle proofs run on a FIXTURE model, so citing them
# alone would inherit a fixture-scope guarantee as a real-weights one.
SEQUENTIAL_QUESTIONS_JUSTIFICATION = (
    "Questions run sequentially inside a condition's process because the adapter toggle leaves "
    "no residue, and that claim rests on TWO citations, not one. (1) FIXTURE scope: "
    "tests/test_lora_toggle.py:77 test_toggle_round_trip_bit_identity, :105 "
    "test_adapter_disabled_preserves_prior_state, :95 test_adapter_disabled_exception_safe — "
    "these run against a fixture model (scripts/phase14_recall.py:1341-1344 records the same "
    "scope limit), so on their own they prove the toggle's semantics and not the real model's "
    "behaviour. (2) REAL WEIGHTS: Phase 14 D-11.3, scripts/phase14_recall.py:1336 "
    "run_bit_identity_control, max |diff| 0.0 measured on the real 13.9M convbase with the real "
    "persona adapter. Both are required: the first establishes the mechanism, the second "
    "establishes that it holds on the weights this comparison actually runs."
)

# D-04 [informational] — WHY the four-process split is defence-in-depth rather than necessity.
NO_KV_CACHE_NOTE = (
    "No KV cache exists in this codebase. grep for cache|past_key|kv across "
    "src/personacore/generation/ and src/personacore/model/ returns zero hits, so the model "
    "recomputes the full forward at every decode step and there is no per-step state that could "
    "survive a question, let alone a condition. Cross-question and cross-condition cache residue "
    "is therefore structurally impossible rather than merely unobserved — which is why the "
    "four-process split is defence-in-depth and not the thing that makes the run valid."
)


def _prove(condition, message):
    """Loud proof: ``SystemExit`` naming the violated contract (never an ``-O``-strippable one).

    Same register and same reason as ``phase14_recall._prove`` and ``phase16_ladder._prove``,
    with this module's own prefix — an abort that names the wrong driver sends its reader to the
    wrong file.
    """
    if not condition:
        raise SystemExit(f"[phase16_persistence] PROOF FAILED: {message}")


# =============================================================================================
# ===== PERS-02 ARM PARITY — one config OBJECT, never four agreeing literals =====
# =============================================================================================


class ArmConfig(NamedTuple):
    """The four SCALAR generation-parity fields every arm reads, in one immutable object.

    PERS-02 requires ``max_new_tokens``, ``forbid_ids``, ``stop_ids`` and context length equal
    across arms and published as report columns. **The claim that survives is "there is one
    object", not "four literals agree"** — four literals that agree today are four literals that
    can stop agreeing in one edit, and the disagreement is invisible in every number produced
    afterwards. So the arms read these fields off ``SHARED_ARM_CONFIG`` by identity, and
    ``assert_arm_parity`` asserts identity rather than equality against a re-derived value.

    **``forbid_ids`` is deliberately NOT a field here.**
    ``personacore.generation.text.undecodable_ids_mask(tokenizer, vocab_size)`` needs a LOADED
    tokenizer, so it cannot run at import time; and it returns a torch tensor, whose ``==`` is
    elementwise and whose ``is``-identity says nothing useful once a caller has moved it to a
    device. Parity on ``forbid`` is instead **structural already**:
    ``scripts/phase14_recall.py:520`` threads ONE ``forbid`` object through every arm, so the arms
    cannot diverge on it by construction. What this module records per arm is its sha256 CONTENT
    hash (``forbid_digest``), which is what makes the parity auditable from the committed report
    rather than only from the code.

    A later reader who notices the missing identity check on ``forbid`` and "fixes" it by moving a
    tensor to module scope would be reintroducing an import-time model dependency to check a
    property that is already true by construction. Do not.
    """

    max_new_tokens: int
    stop_ids: frozenset
    context_length: int
    n_draws: int


# The ONE config object. Every field is READ from the committed Phase 14 pre-registration rather
# than retyped: `RECALL_MAX_NEW_TOKENS` (48, derived from the token census at D-19), `STOP_IDS`
# (the pinned turn-stopping idiom), `ModelConfig.block_size` (256, the trained context length),
# and 1 greedy + `N_SEEDED_SAMPLES` seeded draws. A retyped literal here would be a second,
# independently editable copy of a number that must be identical to the instrument's.
SHARED_ARM_CONFIG = ArmConfig(
    max_new_tokens=recall.RECALL_MAX_NEW_TOKENS,
    stop_ids=recall.STOP_IDS,
    context_length=ModelConfig.block_size,
    n_draws=1 + recall.N_SEEDED_SAMPLES,
)


def forbid_digest(forbid):
    """The sha256 of a ``forbid_ids`` mask's raw bytes — the arm-parity evidence for that mask.

    A content hash rather than an identity check, for the reason ``ArmConfig``'s docstring gives:
    the mask is a device-resident tensor built from a loaded tokenizer, so it can be neither an
    import-time constant nor meaningfully compared with ``is`` after a ``.to(device)``. The hash
    is stable across devices because the bytes are read off a CPU copy.
    """
    return hashlib.sha256(forbid.detach().to("cpu").numpy().tobytes()).hexdigest()


def resolve_forbid(tok, vocab_size):
    """``(mask, sha256)`` — the single runtime seam where ``undecodable_ids_mask`` is called.

    Deliberately a function and not a module-level constant: see ``ArmConfig``. Plan 16-10's
    ``main()`` calls this ONCE and threads the returned mask into all four conditions, which is
    what makes the parity structural instead of asserted.
    """
    from personacore.generation import undecodable_ids_mask

    mask = undecodable_ids_mask(tok, vocab_size)
    return mask, forbid_digest(mask)


def arm_config_record(forbid):
    """The PERS-02 parity columns for one arm, read off ``SHARED_ARM_CONFIG`` — never re-derived.

    The four scalar fields are published as report columns (SC2) so the parity is auditable from
    the artifact and not only from the code; ``shared_arm_config`` carries the object itself, so
    ``assert_arm_parity`` can assert IDENTITY rather than the equality of four small ints, which
    CPython would satisfy trivially by interning.
    """
    return {
        "max_new_tokens": SHARED_ARM_CONFIG.max_new_tokens,
        "stop_ids": SHARED_ARM_CONFIG.stop_ids,
        "context_length": SHARED_ARM_CONFIG.context_length,
        "n_draws": SHARED_ARM_CONFIG.n_draws,
        "forbid_ids_sha256": forbid_digest(forbid),
        "shared_arm_config": SHARED_ARM_CONFIG,
    }


# The parity columns SC2 publishes, named ONCE. `assert_arm_parity` iterates this tuple, so a
# field added to `arm_config_record` and not to this tuple is a column nothing checks.
PARITY_COLUMNS = (
    "max_new_tokens",
    "stop_ids",
    "context_length",
    "n_draws",
    "forbid_ids_sha256",
)


def assert_arm_parity(records):
    """PERS-02: the four arms ran under the SAME budget, mask, stop set and context length.

    Compared field by field across the four ``run_condition`` records, plus an IDENTITY check
    that every arm's config came off the one ``SHARED_ARM_CONFIG`` object. Both halves are needed:
    equality catches a value that changed, identity catches a second ``ArmConfig`` instance built
    from retyped literals that happen to agree today.

    ``forbid_ids`` is compared by its sha256 content hash rather than by object identity — the
    mask is large, device-resident and rebuilt per process, so identity is meaningless across the
    four fresh processes D-01 requires while the content hash is exactly what must match.

    A comparison of arms whose generation budgets differ is a comparison of configurations, so
    this aborts rather than annotating the report.
    """
    _prove(
        len(records) == len(CONDITION_ORDER),
        f"arm parity was asked to check {len(records)} records but the comparison has "
        f"{len(CONDITION_ORDER)} conditions — a missing arm cannot be found by comparing the "
        "ones that are present",
    )
    _prove(
        sorted(record["condition"] for record in records) == sorted(CONDITION_ORDER),
        "the records handed to arm parity are not the four pre-registered conditions: "
        f"{sorted(record['condition'] for record in records)} vs {sorted(CONDITION_ORDER)}",
    )
    configs = [record["config"] for record in records]
    for column in PARITY_COLUMNS:
        seen = {config[column] for config in configs}
        _prove(
            len(seen) == 1,
            f"arms disagree on {column!r}: {sorted(map(str, seen))} — a comparison of arms whose "
            "generation settings differ is a comparison of configurations, and the difference is "
            "invisible in every rate the run reports",
        )
    off_object = [
        record["condition"]
        for record in records
        if record["config"]["shared_arm_config"] is not SHARED_ARM_CONFIG
    ]
    _prove(
        not off_object,
        f"arm(s) {off_object} carry a config that is not the SHARED_ARM_CONFIG object — the "
        "PERS-02 claim is that there is ONE object, not that four copies agree today",
    )


# =============================================================================================
# ===== THE BINDING FIXTURE (270 questions) — read, never regenerated =====
# =============================================================================================

# The BINDING fixture (v3.0): Phases 17 and 18 consume it UNCHANGED. This driver READS it and
# writes nothing to it. Pre-registered counts, so a resampled variant aborts instead of quietly
# rescaling every denominator in the comparison.
FIXTURE_PATH = _REPO_ROOT / "results" / "phase16_recall_sample.json"
FIXTURE_TIER_COUNTS = {"core_taught": 112, "core_held_out": 104, "soft": 54}
FIXTURE_TOTAL_QUESTIONS = 270
FIXTURE_PER_CORE_FACT = {"taught": 14, "held-out": 13}


def load_fixture_items():
    """The fixture's 270 questions as ``RecallItem``s, keyed by tier, seeds carried VERBATIM.

    ``{"core_taught": 112, "core_held_out": 104, "soft": 54}``. The ``seed_index`` is READ off the
    fixture and never re-enumerated: the fixture IS the pairing key PERS-02 claims, so re-stamping
    here would silently REPAIR a mismatch instead of surfacing it — and a repaired mismatch is
    indistinguishable, in every number downstream, from a fixture that was never wrong.

    ``split`` is not recorded per entry, so it is resolved by membership in the committed
    ``phase14_factset.heldout_questions()`` set — the same seam ``phase14_recall.main()`` already
    ``_prove``s its constructed split against. The two core buckets are then cross-checked against
    that membership: an entry in ``core_taught`` that the committed set calls held-out means the
    fixture and the fact set have drifted apart, and the comparison would report taught recall as
    held-out generalization.

    The fact objects come from the LAZILY imported fact set, so the locked values live in this
    process only while a run is in flight and never in this module's string surface.
    """
    import phase14_factset as fs  # LAZY — see the LAZY-IMPORT RULE in the module docstring.

    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    fact_by_id = {fact.id: fact for fact in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS}
    held_out_questions = set(fs.heldout_questions())

    by_tier = {}
    for tier, expected in FIXTURE_TIER_COUNTS.items():
        entries = fixture["questions"][tier]
        _prove(
            len(entries) == expected,
            f"fixture tier {tier!r} carries {len(entries)} questions but the pre-registration "
            f"committed {expected} — every rate in the comparison would be scored over a "
            "different set than the one Phases 17 and 18 consume, and the mismatch is invisible "
            "in the reported rate. Never rescale the denominator silently",
        )
        by_tier[tier] = tuple(
            recall.RecallItem(
                fact=fact_by_id[entry["fact_id"]],
                question=entry["question"],
                split="held-out" if entry["question"] in held_out_questions else "taught",
                reserved=entry["reserved"],
                seed_index=entry["seed_index"],
            )
            for entry in entries
        )

    total = sum(len(items) for items in by_tier.values())
    _prove(
        total == FIXTURE_TOTAL_QUESTIONS,
        f"the fixture yielded {total} questions but the pre-registration committed "
        f"{FIXTURE_TOTAL_QUESTIONS}",
    )
    for tier, split in (("core_taught", "taught"), ("core_held_out", "held-out")):
        wrong = [item.question for item in by_tier[tier] if item.split != split]
        _prove(
            not wrong,
            f"{len(wrong)} question(s) in fixture tier {tier!r} resolve to a split other than "
            f"{split!r} against the committed heldout_questions() set, e.g. {wrong[:3]} — the "
            "fixture and the fact set have drifted apart, and the comparison would report one "
            "tier's recall under the other tier's name",
        )
        per_fact = {}
        for item in by_tier[tier]:
            per_fact[item.fact.id] = per_fact.get(item.fact.id, 0) + 1
        expected = FIXTURE_PER_CORE_FACT[split]
        off = sorted(k for k, v in per_fact.items() if v != expected)
        _prove(
            not off and len(per_fact) == len(fs.LOCKED_FACTS),
            f"fixture tier {tier!r} is not balanced at {expected} questions per core fact "
            f"({len(per_fact)} facts, off-balance: {off}) — D-06's 'resolved by arithmetic, not "
            "chosen' denominator claim rests on that balance holding exactly",
        )
    return by_tier


# =============================================================================================
# ===== ARM DISPATCH — the committed instrument invoked per condition =====
# =============================================================================================

# D-01, and the two companion notes it is reported alongside. All three appear together in the
# report because each one answers a different "why is this isolated enough" question, and any one
# of them alone reads as the whole argument.
PROCESS_SPLIT_NOTE = (
    "The run splits into FOUR fresh processes, one per condition, and questions run sequentially "
    "within a process. Not one process for all four arms: a single process would carry whatever "
    "the previous arm left in it across the arm boundary, which is the one boundary this "
    "comparison is about. And not one process per question, which would be 1,080 model loads for "
    "an isolation nothing needs — see NO_KV_CACHE_NOTE (there is no per-step state to survive a "
    "question) and SEQUENTIAL_QUESTIONS_JUSTIFICATION (the adapter toggle leaves no residue, "
    "proven at fixture scope AND on the real weights). The split is defence-in-depth at the arm "
    "boundary, not a repair for a leak anyone measured."
)

# The per-question record shape, named ONCE for all four arms. Plan 16-09's `aggregate_by_fact`
# keys on `record["fact_id"]` and groups by `record["split"]`, so a missing key here is a
# `KeyError` several waves after the mistake was made — `assert_record_shape` moves that failure
# back to the arm that produced it.
PER_QUESTION_KEYS = ("fact_id", "split", "seed_index", "k", "n")

# The fixture's tiers mapped to the COMMITTED Phase 14 tier labels. Arm A is scored per tier and
# the labels are read from the instrument rather than retyped, so the report's section names and
# the harness's cannot drift.
TIER_LABELS = {
    "core_taught": recall.CORE_TAUGHT_TIER,
    "core_held_out": recall.CORE_HELDOUT_TIER,
    "soft": recall.SOFT_TIER,
}


def all_items(items_by_tier):
    """The three tiers concatenated in the fixture's own order — arms B, C and D's call shape."""
    return tuple(item for tier in FIXTURE_TIER_COUNTS for item in items_by_tier[tier])


def fairness_statements():
    """``fact.id -> that fact's own first-person taught statement`` — arm B's persona span.

    Built exactly the way ``phase14_recall.main()`` builds it
    (``SLOT_FORMS[fact.slot].ans1.format(v=fact.value)``), from the LAZILY imported fact set, so
    the statements this driver hands the control are the same strings Phase 14 handed it.
    """
    import phase14_factset as fs  # LAZY — see the LAZY-IMPORT RULE in the module docstring.

    return {
        fact.id: fs.SLOT_FORMS[fact.slot].ans1.format(v=fact.value)
        for fact in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS
    }


def normalize_by_split(returned):
    """Flatten whatever an arm returned onto ONE per-question list, regrouped by each entry's split.

    The committed arms disagree about their return shape, and the disagreement is load-bearing
    rather than sloppy: arm A is scored per TIER so it returns three tier records; arms B and C are
    scored over the concatenation so they return one record apiece whose ``questions`` list already
    carries ``split`` per entry; arm D returns per-question entries directly.

    The regrouping keys on each ENTRY's own ``split`` field and never on which record it came out
    of. That distinction is the whole point: arm A's ``core_taught`` record happens to hold only
    taught questions today, but a grouping that assumed so would silently mislabel the moment a
    tier stopped being split-pure — and the mislabelling is invisible in the resulting rate.
    """
    records = [returned] if isinstance(returned, dict) else list(returned)
    entries = [
        entry
        for record in records
        for entry in (record["questions"] if "questions" in record else [record])
    ]
    by_split = {}
    for entry in entries:
        by_split.setdefault(entry["split"], []).append(entry)
    return by_split


def assert_record_shape(record):
    """``_prove`` every per-question entry carries all five ``PER_QUESTION_KEYS``.

    Called at the END of ``run_condition`` so a missing key aborts at the arm that produced it.
    Without this, the first symptom is plan 16-09's ``record["fact_id"]`` raising ``KeyError``
    inside the statistics module — several waves and one long run after the defect was written,
    with nothing in the traceback naming which arm dropped the key.
    """
    _prove(
        record["by_split"],
        f"condition {record['condition']!r} produced no per-question entries at all — an arm that "
        "scores nothing still returns a well-formed record, so the emptiness must abort here",
    )
    required = set(PER_QUESTION_KEYS)
    missing = [
        (split, index, sorted(required - set(entry)))
        for split, entries in record["by_split"].items()
        for index, entry in enumerate(entries)
        if not required <= set(entry)
    ]
    _prove(
        not missing,
        f"condition {record['condition']!r} emitted {len(missing)} per-question entr(ies) missing "
        f"PER_QUESTION_KEYS, e.g. {missing[:3]} — plan 16-09 keys on fact_id and groups on split, "
        "so the absence would surface as a KeyError in the statistics module rather than here",
    )


def run_condition(condition, model, tok, device, forbid, items_by_tier):
    """ONE arm: dispatch onto the committed instrument, normalize, prove the record shape.

    **This function writes no draw loop, no prompt and no scoring rule.** Producing the numbers is
    the committed instrument's job (``run_scored_recall`` / ``run_closed_book_control`` /
    ``run_fairness_control``, and ``run_cosine_arm`` for the one genuinely new arm); this driver
    contributes dispatch, a uniform record shape and a parity assertion. A second draw loop here
    is how two arms silently stop being paired, which is the defect PERS-05 just closed upstream.

    Dispatch is exhaustive over ``CONDITION_ORDER`` and has NO default branch. An unrecognized
    name aborts on the first ``_prove``; a name that is in ``CONDITION_ORDER`` but has no branch
    aborts on the second. Falling through to "run something reasonable" would produce a
    well-formed record for an arm nobody asked for.

    Arm A is scored per TIER because that is the shape ``run_scored_recall`` documents and the
    shape Phase 14's committed numbers were produced in; the comprehension loops over TIERS, never
    over questions. Arms B, C and D take the concatenation, which is the call shape
    ``run_closed_book_control``'s docstring already documents.

    Returns ``{"condition", "config", "by_split"}`` — an identical outer shape for all four arms.
    """
    _prove(
        condition in CONDITION_ORDER,
        f"condition {condition!r} is not one of the pre-registered {CONDITION_ORDER} — an "
        "unrecognized arm must abort, never fall through to whichever arm the code happens to "
        "reach, because the result would be reported under the name that was asked for",
    )
    returned = None
    if condition == "adapter-only":
        # Adapter ON, explicitly rather than by inheritance: this arm's entire meaning is that the
        # memory is in the weights, and a process that had disabled it earlier would produce arm
        # C's number under arm A's name.
        recall.set_adapter_enabled(model, True)
        returned = [
            recall.run_scored_recall(
                model, tok, device, forbid, items_by_tier[tier], tier_label=label
            )
            for tier, label in TIER_LABELS.items()
        ]
    elif condition == "base-neither":
        returned = recall.run_closed_book_control(
            model, tok, device, forbid, all_items(items_by_tier)
        )
    elif condition == "embedding-cosine":
        returned = run_cosine_arm(model, tok, device, all_items(items_by_tier), candidate_pool())
    elif condition == "prompt-stuffed":
        returned = recall.run_fairness_control(
            model, tok, device, forbid, all_items(items_by_tier), fairness_statements()
        )
    _prove(
        returned is not None,
        f"condition {condition!r} is in CONDITION_ORDER but no dispatch branch produced a result "
        "— the pre-registration and this dispatch have drifted apart, and the arm would silently "
        "contribute nothing to the comparison",
    )
    record = {
        "condition": condition,
        "config": arm_config_record(forbid),
        "by_split": normalize_by_split(returned),
    }
    assert_record_shape(record)
    return record


# =============================================================================================
# ===== ARM D — the embedding/cosine baseline (PERS-04 / D-22 / D-23 / D-24 / D-25) =====
# =============================================================================================

# D-23/D-25 — arm D's chance floor, and the numeric reconciliation D-25 flagged rather than
# settled in silence. The candidate pool is the 20-value lexicon `find_contradictions` already
# uses, so the floor is 1/20 and THAT is the number the report uses. D-25's verbatim qualifier
# text was written citing 8 candidates and a floor of 0.125; the pool decision taken in the same
# round chose the 20-value lexicon instead. The qualifier holds in full at the floor of the pool
# actually chosen — 0.05 is still an order of magnitude above arm B (~0.005) and arm C (~0), so a
# result where arm D "wins" or ties favourably is still a consequence of its task being easier by
# construction rather than evidence of equivalent capability. The superseded figure appears in
# this comment, which is where the discrepancy is recorded, and in no computation anywhere.
COSINE_CHANCE_FLOOR = 0.05

# DERIVED from the floor, never a second literal: two numbers that must agree are two numbers
# that can stop agreeing. `candidate_pool` proves the real pool matches both.
COSINE_POOL_SIZE = round(1 / COSINE_CHANCE_FLOOR)


def candidate_pool():
    """Arm D's closed candidate set: ``LOCKED_VALUES | GATE_REJECTED_CANDIDATES`` values.

    D-23 — the exact lexicon ``phase14_recall.find_contradictions`` already consumes, reused with
    ZERO new editorial judgment. The argument is already written in the codebase at
    ``scripts/phase14_recall.py:325-338``: a competing value the contradiction detector must spot
    is precisely a plausible same-slot alternative, which is what every gate-rejected candidate
    already is. A hand-curated per-slot list would reintroduce exactly the editorial judgment that
    lexicon was chosen to avoid — and in an arm whose chance floor is set by the pool's size, a
    curated pool would be a chance floor chosen by hand.

    Sorted, so the pool's order is a property of the material rather than of set iteration order,
    and the argmax index means the same thing in every process of the four-process split.
    """
    import phase14_factset as fs  # LAZY — see the LAZY-IMPORT RULE in the module docstring.

    pool = tuple(
        sorted(set(fs.LOCKED_VALUES) | {fact.value for fact in fs.GATE_REJECTED_CANDIDATES})
    )
    _prove(
        len(pool) == COSINE_POOL_SIZE,
        f"the committed lexicon yields {len(pool)} distinct values but the pre-registered pool "
        f"size is {COSINE_POOL_SIZE} — arm D's chance floor is 1/len(pool), so a pool that "
        "changed size silently changes the floor every arm-D result is read against",
    )
    _prove(
        1 / len(pool) == COSINE_CHANCE_FLOOR,
        f"1/{len(pool)} = {1 / len(pool)} is not the pre-registered chance floor "
        f"{COSINE_CHANCE_FLOOR} — the floor is a pre-registration and the pool is the material "
        "it describes; they cannot be allowed to disagree",
    )
    return pool


def embed_sequence(model, ids, device):
    """One forward pass; the FINAL HIDDEN STATE, mean-pooled over the sequence — a 1-D tensor.

    The final hidden state is ``ln_f``'s OUTPUT (``src/personacore/model/gpt.py:206``, applied
    immediately before the tied head). ``GPT.forward(idx, targets=None) -> (logits, loss)`` is a
    LOCKED contract, so there is no already-exposed seam returning hidden states and none is added
    here: a ``register_forward_hook`` on ``model.ln_f`` reads the value without touching the
    signature or the return shape. The handle is removed in a ``finally`` — a hook that survives
    its call would fire inside every later generation step in the same process, appending a tensor
    per decode step to a list nothing drains.

    ``ln_f`` is not one of the six per-block projections ``inject_lora`` wraps, so the hook sees
    the LayerNorm itself in both the injected and the un-injected model.
    """
    import torch

    captured = []
    handle = model.ln_f.register_forward_hook(lambda module, args, output: captured.append(output))
    try:
        with torch.no_grad():
            model(torch.tensor([ids], dtype=torch.long, device=device))
    finally:
        handle.remove()
    _prove(
        len(captured) == 1,
        f"the final-hidden-state hook fired {len(captured)} times for one forward pass — the "
        "model's shape has changed under this arm and the pooled vector would no longer be the "
        "sequence's final hidden state",
    )
    return captured[0][0].mean(dim=0)


COSINE_TIER = "embedding-cosine baseline (PERS-04 — adapter off, closed-set retrieval)"


def run_cosine_arm(model, tok, device, items, pool):
    """Arm D: embed the bare prompt, pick the nearest candidate by cosine, EMIT IT AS TEXT.

    **Scored by ``contains_value``, the same scorer as the other three arms** (D-22). Arm D's
    output is a string, not a similarity, precisely so the phase has exactly ONE scorer — silent
    divergence between arm scorers then becomes structurally impossible rather than merely
    unlikely, and no argument about "what counts as a hit for arm D" can ever be had.

    **Adapter OFF is a structural invariant, not an option** (D-24, verbatim: *"Adapter OFF é
    invariante estrutural, não opção — o braço D existe para ser o referencial sem memória-em-
    pesos."*). It wraps the whole body, including the candidate embeddings, rather than being a
    keyword a caller could forget.

    **ONE deterministic draw per question** (``n = 1``), not nine. The per-fact rate is therefore
    ``hits/13 held-out questions`` against ``hits/117 draws`` for arms A/B/C, which is compatible
    with D-06 without adjustment: the sign test uses only the ORDERING between arms, never the
    magnitude of the denominator. The rejected alternative is recorded — manufacturing 9 draws by
    softmax-sampling the similarities would produce an interval measuring the chosen temperature
    rather than any real uncertainty, i.e. a confidence interval around a knob.

    **The bounds are set by requirement, not by taste.** PERS-04 is embedding plus cosine over the
    existing fact set and nothing else: no vector index, no second-pass re-scoring of the
    candidates, and no splitting of any text into passages. One forward pass per question; the 20
    candidate embeddings are computed ONCE for the whole arm, before the question loop.

    **Arm D is a SCORED arm, so the clean-room rule is not relaxed for it** (T-16-32): every
    prompt is the same bare ``build_recall_prompt(tok, question)`` arms A and C receive, and
    ``assert_no_value_in_prompt`` runs per question exactly as it does for them.

    ``seed_index`` is carried verbatim from the fixture even though this arm draws
    deterministically: it is the pairing key PERS-02 claims, and an arm that dropped it would be
    unpairable with the three arms it is compared against.
    """
    import phase14_factset as fs  # LAZY — see the LAZY-IMPORT RULE in the module docstring.
    import torch

    from personacore.lora import adapter_disabled

    _prove(items, "the cosine arm received no questions to score")
    _prove(
        len(set(pool)) == len(pool) == COSINE_POOL_SIZE,
        f"the cosine arm received a pool of {len(pool)} values ({len(set(pool))} distinct) but "
        f"the pre-registered pool size is {COSINE_POOL_SIZE} — the chance floor this arm's result "
        "is read against is 1/len(pool)",
    )
    all_values = tuple(fact.value for fact in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS)

    asked = []
    with adapter_disabled(model):
        # ONCE for the whole arm, never per question: 20 forward passes, not 20 x len(items).
        candidates = torch.stack(
            [embed_sequence(model, tok.encode(value), device) for value in pool]
        )
        for item in items:
            _prove(
                item.seed_index >= 0,
                f"question {item.question!r} reached the cosine arm carrying no seed index — the "
                "fixture is the pairing key PERS-02 claims, and an unstamped item cannot be "
                "paired with the same question in the three arms this one is compared against",
            )
            prompt_ids = build_recall_prompt(tok, item.question)
            # The same clean-room proof arms A and C run. A scored arm whose prompt carried the
            # value would falsify the claim at the exact moment it is demonstrated.
            recall.assert_no_value_in_prompt(tok, item.question, all_values)
            query = embed_sequence(model, prompt_ids, device)
            similarities = torch.nn.functional.cosine_similarity(
                candidates, query.unsqueeze(0), dim=1
            )
            emitted = pool[int(similarities.argmax())]
            # THE scorer — the same one arms A, B and C are scored by (D-22).
            hit = recall.contains_value(emitted, item.fact.value)
            asked.append(
                {
                    "question": item.question,
                    "fact_id": item.fact.id,
                    "split": item.split,
                    "seed_index": item.seed_index,
                    "emitted": emitted,
                    # What it chose over what — so the report can show the whole ranking rather
                    # than only the winner, which is the only way a reader can tell a confident
                    # pick from a coin flip between two near-identical similarities.
                    "similarities": [float(value) for value in similarities],
                    "k": int(hit),
                    "n": 1,
                }
            )
            print(f"[phase16_persistence] {COSINE_TIER} {item.question!r}: {int(hit)}/1")

    total_k = sum(entry["k"] for entry in asked)
    return {
        "tier": COSINE_TIER,
        "questions": asked,
        "k": total_k,
        "n": len(asked),
        "rate": total_k / len(asked),
        "n_answerable": sum(1 for entry in asked if entry["k"] > 0),
        "chance_floor": COSINE_CHANCE_FLOOR,
    }


# =============================================================================================
# ===== THE PER-FACT STATISTIC AND THE ONE REPORTING SHAPE (D-06 / STAT-01 / STAT-02) =====
# =============================================================================================

# The two splits `normalize_by_split` emits, named once. These are `RecallItem.split` values
# (`phase14_recall.py:732`), NOT the fixture's tier names — the fixture says "core_held_out" and
# the record says "held-out", and keying the statistics on the wrong one of the two would group
# nothing and report a rate over an empty set.
TIER_SPLITS = ("taught", "held-out")

# D-07 — exactly ONE tier is gated, and it is held-out. Gating both would take the Holm family
# from 6 to 12, alpha to 0.05/12 = 0.0041667, and 8/8 unanimity (p = 0.0078125) would then FAIL:
# the gate becomes unclearable at every possible outcome, including perfect unanimity in both
# tiers. Held-out and not taught because `results/phase14_recall_report.md:54` records that taught
# measures recall on template families the adapter trained on, where success is compatible with
# surface memorization; held-out is the tier that distinguishes an internalized fact from a
# memorized phrasing.
GATED_TIER = "held-out"
REPLICATION_TIER = "taught"

# ----- Bootstrap discretion, exercised and RECORDED (16-09 §"Planner discretion") -------------
#
# 10,000 resamples, seed 1337, PERCENTILE method — the same count, seed and method as the Phase 15
# precedent (`scripts/phase15_stats.py:76-91`), reused so the two pre-registrations are readable
# against each other rather than each inventing its own convention.
#
# THE PERCENTILE BOOTSTRAP IS BIASED AND ANTI-CONSERVATIVE AT SMALL n. n here is 8 FACTS — smaller
# than Phase 15's 36 cells, so the bias is LARGER here, not smaller. BCa would correct it at real
# complexity cost. Phase 15's precedent is to NAME the bias in the pre-registration rather than to
# upgrade the method once a result is visible, and that is what this comment is: an interval method
# chosen after seeing the number is a knob, and the diff against this block is what makes such an
# upgrade visible instead of silent. Do not upgrade to BCa after the numbers land.
#
# This interval is DESCRIPTIVE and is never a gate (STAT-06). The inferential gate is
# `sign_test_exact` + `holm` below, and nothing else in this phase is gated at all (D-09).
BOOTSTRAP_RESAMPLES = 10000
BOOTSTRAP_SEED = 1337
BOOTSTRAP_ALPHA = 0.05
BOOTSTRAP_METHOD = "two_stage_cluster_percentile_bootstrap"

# STAT-02 / T-16-41 — Wilson travels with the sentence that says what it is NOT. A bound presented
# without this label reads as the phase's width, and it is not: it is the width the data would have
# had if the questions were independent, which they are not.
WILSON_LABEL = (
    "one-sided 95% Wilson upper bound computed as if the questions were INDEPENDENT. They are "
    "not — questions cluster inside facts — so this width UNDERSTATES the real uncertainty. The "
    "DESCRIPTIVE interval for this phase is the two-stage cluster bootstrap (`cluster_bootstrap`); "
    "Wilson is reported alongside it, labelled, for comparability with every other rate in this "
    "milestone, and never as the phase's own width."
)


def aggregate_by_fact(records, *, tier):
    """Group per-question records by ``fact_id`` — D-06's grouping-key change, and nothing else.

    This is ``phase14_recall.py:838-843``'s tier aggregation with ONE substitution: the grouping
    key is ``record["fact_id"]`` instead of ``record["split"]``. The shape is followed rather than
    a second aggregation idiom invented, so the two stay readable against each other.

    ``records`` is a flat list of per-question entries carrying 16-08's ``PER_QUESTION_KEYS``
    (``fact_id``, ``split``, ``seed_index``, ``k``, ``n``), normalized by ``run_condition`` across
    all four arms — so ``record["fact_id"]`` is read DIRECTLY and never re-derived from the
    question text or from a fixture index. ``tier`` is one of ``TIER_SPLITS`` and every record must
    already belong to it; a mixed list would silently pool taught with held-out, which D-10 forbids.

    Returns ``{fact_id: {questions, k, n_draws, n_questions, n_answerable, rate}}``, where
    ``questions`` is that fact's ``(k, n)`` pairs — the exact input ``cluster_bootstrap`` resamples,
    so the caller never re-groups a second time.

    ``rate`` is ``k / n_draws``. On this perfectly balanced fixture — every core fact carries
    exactly 14 ``core_taught`` + 13 ``core_held_out`` questions at 9 draws each, 126 / 117 draws —
    ``sum(k)/sum(n)`` equals ``mean(k_i/9)`` DIGIT FOR DIGIT, so the choice between them affects
    only the INTERVAL and not the point estimate. That is why D-06 calls the denominator question
    resolved by arithmetic rather than chosen. STAT-01 mandates that the interval resamples
    QUESTIONS, which is what stage 2 of ``cluster_bootstrap`` does.
    """
    _prove(
        tier in TIER_SPLITS,
        f"tier {tier!r} is not one of {TIER_SPLITS} — these are RecallItem.split values, not the "
        "fixture's tier names, and aggregating on the wrong one groups an empty set into a rate",
    )
    _prove(records, f"tier {tier!r} received no per-question records to aggregate")
    required = set(PER_QUESTION_KEYS)
    grouped = {}
    for record in records:
        _prove(
            required <= set(record),
            f"a record in tier {tier!r} is missing {sorted(required - set(record))} of "
            f"PER_QUESTION_KEYS — 16-08's assert_record_shape should have aborted at the arm that "
            "produced it, so reaching the statistics with a hole means that guard was bypassed",
        )
        _prove(
            record["split"] == tier,
            f"a record with split {record['split']!r} reached the {tier!r} aggregation. D-10 "
            "forbids pooling taught with held-out: each fact yields TWO numbers, and silently "
            "merging them would produce one rate that belongs to neither tier",
        )
        _prove(
            record["n"] > 0,
            f"question {record['fact_id']!r}/{record['seed_index']} carries n = {record['n']} "
            "draws — a zero denominator cannot enter a rate or a resample",
        )
        grouped.setdefault(record["fact_id"], []).append((record["k"], record["n"]))
    return {
        fact_id: {
            "questions": tuple(questions),
            "k": sum(k for k, _ in questions),
            "n_draws": sum(n for _, n in questions),
            "n_questions": len(questions),
            "n_answerable": sum(1 for k, _ in questions if k > 0),
            "rate": sum(k for k, _ in questions) / sum(n for _, n in questions),
        }
        for fact_id, questions in sorted(grouped.items())
    }


def cluster_bootstrap(
    per_fact_questions,
    *,
    resamples=BOOTSTRAP_RESAMPLES,
    seed=BOOTSTRAP_SEED,
    alpha=BOOTSTRAP_ALPHA,
):
    """TWO-STAGE cluster bootstrap: resample the FACTS, then the QUESTIONS inside each one.

    ``per_fact_questions`` is ``{fact_id: [(k, n), ...]}`` — exactly ``aggregate_by_fact``'s
    ``questions`` field. Returns the ``(lo, hi)`` percentile bounds of the pooled rate
    ``sum(k)/sum(n)``. DESCRIPTIVE only; it is never a gate (STAT-06).

    **Both stages are required, and each one is required by a different committed source.**

    * **Stage 1 — resample the 8 FACTS with replacement.** ``.planning/STATE.md:94``:
      *"Bootstrap resampling is at FACT level (n=8), not question level."* Without stage 1 the
      interval is conditional on these exact 8 facts and is therefore NARROWER than the fact-level
      sign test standing beside it — an interval claiming more than the gate it accompanies, which
      is this milestone's own over-claiming failure mode.
    * **Stage 2 — resample that resampled fact's own QUESTIONS with replacement.**
      ``REQUIREMENTS.md:25-28`` (STAT-01): *"Bootstrap resampling resamples questions."* Its stated
      rationale targets the DRAW as the illegal unit — treating 496/1008 as 1008 i.i.d. Bernoulli
      trials — and stage 2 honours that literally. STAT-01 is not a ruling on facts-versus-questions
      as the cluster. ``16-CONTEXT.md`` D-06 likewise keeps the QUESTION as the resampled unit.

    The 16-09 plan text originally specified stage 2 alone, with the 8 facts held FIXED. That was
    corrected by explicit USER DECISION at the wave-8 checkpoint, and ``16-09-PLAN.md``'s Task 1
    wording was updated in the same commit so the plan and this function do not disagree.

    **Why no coverage or collision floor is asserted anywhere.** On the FACT layer alone the number
    of distinct outcomes is the multiset coefficient ``C(8 + 8 - 1, 8) = C(15, 8) = 6435``
    (``math.comb(15, 8)``); the full two-stage space is far larger. Those 6435 multisets are NOT
    equiprobable — a multiset's probability carries its multinomial weight, so a balanced draw
    (one of each fact, ``8!`` orderings) is orders of magnitude likelier than an all-same draw
    (1 ordering) — and coupon-collector reasoning over 6435 uniform items therefore does not apply.
    At ``BOOTSTRAP_RESAMPLES`` (10,000) roughly 57% of the fact-multisets are actually drawn
    (measured upstream: 3692 at seed 1337, 3649 at seed 42). A floor such as ``>= 6435 * 0.95`` is
    unreachable BY CONSTRUCTION and must never be written here or in the tests.

    ``random.Random(seed)`` is a LOCAL generator — stdlib only, no numpy RNG to diverge from, no
    third-party statistics package, and the global python/numpy/torch streams are untouched (the
    ``fisher.py`` Pitfall-3 register, the same discipline as ``phase15_stats.bootstrap_ci``).
    """
    fact_ids = sorted(per_fact_questions)
    _prove(fact_ids, "the cluster bootstrap received no facts to resample")
    _prove(
        resamples >= 2,
        f"resamples = {resamples}: a percentile needs at least two resampled statistics",
    )
    for fact_id in fact_ids:
        questions = per_fact_questions[fact_id]
        _prove(questions, f"fact {fact_id!r} carries no questions to resample in stage 2")
        _prove(
            all(n > 0 for _, n in questions),
            f"fact {fact_id!r} carries a question with a zero denominator — a resample that drew "
            "only such questions would divide by zero, so this aborts at the input instead",
        )
    rng = random.Random(seed)  # LOCAL generator — the global RNG streams are never touched.
    n_facts = len(fact_ids)
    rates = []
    for _ in range(resamples):
        numerator = denominator = 0
        for _ in range(n_facts):
            # STAGE 1 — the FACTS, with replacement. This is the between-fact variability that a
            # question-only bootstrap conditions away (STATE.md:94, n = 8).
            questions = per_fact_questions[fact_ids[rng.randrange(n_facts)]]
            for _ in range(len(questions)):
                # STAGE 2 — that RESAMPLED fact's own questions, with replacement (STAT-01, D-06).
                k, n = questions[rng.randrange(len(questions))]
                numerator += k
                denominator += n
        rates.append(numerator / denominator)
    # `method="inclusive"` is the (n-1)*p linear interpolation numpy's default quantile uses, so
    # this reads the same way `phase15_stats.bootstrap_ci` does without importing numpy. n = 40
    # cut points puts alpha/2 = 0.025 at the first and 1 - alpha/2 = 0.975 at the last, DERIVED
    # from alpha rather than typed as a second literal that must agree with it.
    cuts = statistics.quantiles(rates, n=round(2 / alpha), method="inclusive")
    return cuts[0], cuts[-1]


def report_proportion(successes, n_questions, n_draws):
    """STAT-02's single reporting shape — used by every rate this phase publishes.

    ``successes`` and ``n_questions`` are in the STAT-01 unit (QUESTIONS: a question counts once,
    however many of its draws hit). ``n_draws`` travels alongside as the raw-count denominator, so
    the record carries the denominator BOTH ways and a reader never has to guess which unit a rate
    was computed in (T-16-40 — the reported unit is the repudiation surface).

    Three things are always present and one is conditional:

    * ``rate`` over questions, with ``n_questions`` and ``n_draws`` beside it.
    * ``wilson_upper_95`` from ``erasure_gate.wilson_upper_bound`` — IMPORTED, never re-derived.
    * ``wilson_label`` — ``WILSON_LABEL``, naming it as the independence-assuming width (T-16-41).
    * ``rule_of_three_upper`` — present ONLY when ``successes == 0``, where the two bounds
      disagree slightly and publishing both is what stops the quieter one being chosen later.

    ``formatted`` never renders a bare zero percentage. A zero rate renders as its numerator over
    its denominator with the bound attached — ``0/104 questions (95% Wilson upper bound ...)`` —
    because a bare zero percentage states a certainty the sample does not have, and STAT-02 forbids
    it in any committed report or figure. ``tests/test_phase16_driver.py`` pins the same property
    at the source level for this whole module, so the literal is not typed here either.
    """
    _prove(n_questions > 0, "a proportion over zero questions has no denominator to report")
    _prove(n_draws > 0, "a proportion over zero draws has no raw count to report")
    _prove(
        0 <= successes <= n_questions,
        f"{successes} successes outside [0, {n_questions}] questions — `successes` is in the "
        "STAT-01 QUESTION unit here, not the draw unit; passing a draw count would silently "
        "report a rate above 1 and a Wilson bound over an impossible proportion",
    )
    row = {
        "rate": successes / n_questions,
        "successes": successes,
        "n_questions": n_questions,
        "n_draws": n_draws,
        "wilson_upper_95": wilson_upper_bound(successes, n_questions),
        "wilson_label": WILSON_LABEL,
    }
    if successes == 0:
        row["rule_of_three_upper"] = rule_of_three(n_questions)
        row["formatted"] = (
            f"{successes}/{n_questions} questions "
            f"(95% Wilson upper bound {row['wilson_upper_95']:.6f}; "
            f"rule-of-three upper bound {row['rule_of_three_upper']:.6f}; {n_draws} draws)"
        )
    else:
        row["formatted"] = (
            f"{successes}/{n_questions} questions (rate {row['rate']:.6f}; "
            f"95% Wilson upper bound {row['wilson_upper_95']:.6f}; {n_draws} draws)"
        )
    return row
