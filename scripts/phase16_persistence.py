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
import itertools
import json
import pathlib
import random
import re
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

# The COMMITTED capability ladder (16-07: run, reported and committed before this driver's report
# writer existed). IMPORTED, never restated — `licensed_headline` decides what this phase is
# allowed to publish, and a headline retyped here would be free to drift from the branch that was
# actually licensed (T-16-47). Import-cheap: stdlib plus `_verdict`, `erasure_gate` and
# `personacore.dialogue`, with its own fact-set imports lazy.
import phase16_ladder as ladder  # noqa: E402  (needs the sys.path insert above)

# The ONE copy of the anchored `## Verdict` SECTION read (15-04 CR-02). Never a split on the
# heading literal: the tail after the LAST occurrence of a string that also appears in prose puts
# the guard's read inside a section that never says PENDING, so it fires on every legitimate
# re-drive and a force flag becomes the only way through — which then destroys the hand-written
# material it protects.
from _verdict import VERDICT_SECTION, recorded_verdict  # noqa: E402  (needs the insert above)

# STAT-04 — the ONLY bounds source in this milestone, IMPORTED and never copied. A third-party
# statistics package has been declined in committed code twice and is forbidden here (the D-16
# register: import the instrument, never re-implement it). `tests/test_package.py` sha256-pins
# `pyproject.toml`, so a new dependency cannot arrive quietly alongside a new statistic.
from erasure_gate import rule_of_three, wilson_upper_bound  # noqa: E402  (needs the insert above)

from personacore.config import ModelConfig  # noqa: E402
from personacore.dialogue import build_recall_prompt, detokenize  # noqa: E402

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
                k, _n = questions[rng.randrange(len(questions))]
                # STAT-01: the QUESTION is the unit of analysis, never the draw. A question counts
                # once if ANY of its draws carried the value — the same max-over-draws statistic
                # `n_answerable` uses everywhere else in this milestone. Accumulating `k` and `n`
                # instead computes the DRAW rate, a different quantity: on the real gated tier that
                # is ~0.33 where the question rate is ~0.87, so the published interval would not
                # contain the rate printed beside it. Caught on the 16-11 run, before approval.
                numerator += 1 if k > 0 else 0
                denominator += 1
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


# =============================================================================================
# ===== THE INFERENTIAL GATE — exact paired sign test + Holm across exactly 6 pairs =====
# =============================================================================================

# D-09 — THE FAMILY IS CLOSED AT EXACTLY THESE 6 PAIRS, C(4, 2) over CONDITION_ORDER, and the
# arithmetic behind that closure is the whole reason nothing else in Phase 16 may be gated:
#
#     alpha at Holm's first step  = 0.05 / 6 = 0.0083333
#     8/8 unanimity on the exact two-sided sign test over 2**8 = 256 partitions = 0.0078125
#     margin                      = 0.0005208, i.e. 6.7% RELATIVE to the achievable p
#     m = 7                       -> alpha = 0.0071429 < 0.0078125  -> the headline dies
#
# A SEVENTH gated comparison therefore kills the result arithmetically, at ANY outcome, including
# perfect unanimity. That is why the taught replication (D-07) and the PERS-03 context-pressure
# sweep are descriptive BY CONSTRUCTION and never enter this family — STAT-06 with arithmetic
# behind it, not just principle. `assert_family_closed` enforces it at runtime and
# `tests/test_phase16_stats.py` enforces it statically across BOTH Phase 16 driver modules.
#
# DERIVED from CONDITION_ORDER, never a hand-typed list of six: a retyped family is a family that
# can stop matching the arms it claims to compare.
HOLM_FAMILY_PAIRS = tuple(itertools.combinations(CONDITION_ORDER, 2))

HOLM_ALPHA = 0.05

# D-08 — n is FIXED at 8, always, pre-registered. Ties count AGAINST the alternative and are
# folded into the unfavourable count; they are never discarded and never shrink this denominator.
# Discarding ties (the textbook rule) is rejected on two grounds. One tie would give n = 7, where
# unanimity is p = 0.015625 > 0.0083333 and the gate is unclearable. And decisively: the
# prompt-stuffed x base-neither pair is expected to tie on nearly all 8 facts given Phase 14's
# committed 1/1944, which would drop that pair to n ~ 0 where the test is UNDEFINED — not merely
# underpowered — and the whole Holm family becomes ill-formed. Under "ties against", that pair is
# simply 0/8. `sign_test_exact` takes no `n` parameter and must never grow one: an `n=` argument
# would install precisely the knob this decision locks.
SIGN_TEST_N = 8

# D-29 / T-16-39c — THE DECLARED DIRECTION OF THE ALTERNATIVE, PER PAIR, COMMITTED BEFORE ANY RUN.
#
# The rule for every pair is the same and is stated explicitly rather than left to a convention a
# reader would have to reconstruct: THE FIRST ARM OF THE PAIR EXCEEDS THE SECOND. It exists as a
# committed literal because without one the direction could be fixed AFTER the signs are visible,
# which is exactly what STAT-05 forbids — in the one phase whose entire product is a
# pre-registration. `sign_test_exact`'s caller reads the direction from here; it is never inferred
# from the signs in hand. Spelled out per pair rather than generated, so a reviewer audits six
# committed statements instead of a comprehension; `assert_family_closed` proves the key set equals
# HOLM_FAMILY_PAIRS exactly, so the two cannot drift apart in silence.
SIGN_TEST_ALTERNATIVE = {
    ("adapter-only", "base-neither"): "adapter-only exceeds base-neither",
    ("adapter-only", "embedding-cosine"): "adapter-only exceeds embedding-cosine",
    ("adapter-only", "prompt-stuffed"): "adapter-only exceeds prompt-stuffed",
    ("base-neither", "embedding-cosine"): "base-neither exceeds embedding-cosine",
    ("base-neither", "prompt-stuffed"): "base-neither exceeds prompt-stuffed",
    ("embedding-cosine", "prompt-stuffed"): "embedding-cosine exceeds prompt-stuffed",
}

# D-07's pre-registration text, VERBATIM and not paraphrasable. Split across two source lines only
# because it exceeds the line limit; implicit concatenation reproduces it byte for byte, and
# `tests/test_phase16_stats.py` asserts it against `16-CONTEXT.md` rather than against a second
# hand-typed copy.
TAUGHT_TIER_STATUS = (
    "o resultado do tier taught nunca altera, reforça formalmente, nem substitui o veredito do "
    "tier held-out — é evidência corroborante reportada, não gate."
)


def _sign(first_rate, second_rate):
    """``+1`` / ``-1`` / ``0`` for one fact under one pair, in the pair's own arm order.

    A TIE returns ``0``, which ``sign_test_exact`` folds into the count AGAINST the alternative
    (D-08). It is never dropped, so the denominator stays at ``SIGN_TEST_N``.
    """
    return (first_rate > second_rate) - (first_rate < second_rate)


def fact_signs(per_fact_by_arm, pair):
    """The 8 per-fact signs for one pair, in sorted fact order.

    ``per_fact_by_arm`` is ``{arm: {fact_id: {"rate": ...}}}`` — one ``aggregate_by_fact`` result
    per arm, all on the SAME tier. The comparison is on ``rate``, and D-22 is satisfied without
    adjustment: arm D's denominator is 13 questions where arms A/B/C carry 117 draws, and the sign
    test uses only the ORDERING between two arms, never the magnitude of either denominator.
    """
    first, second = pair
    _prove(
        first in per_fact_by_arm and second in per_fact_by_arm,
        f"pair {pair} names an arm absent from {sorted(per_fact_by_arm)} — a pair whose arm never "
        "ran would silently contribute a fabricated sign to the family",
    )
    facts = sorted(per_fact_by_arm[first])
    _prove(
        facts == sorted(per_fact_by_arm[second]),
        f"pair {pair} is unpaired: {first} covers {facts} and {second} covers "
        f"{sorted(per_fact_by_arm[second])}. PERS-02's whole claim is that the arms score the SAME "
        "questions, so a fact present in one arm and absent from the other has no sign at all",
    )
    _prove(
        len(facts) == SIGN_TEST_N,
        f"pair {pair} carries {len(facts)} facts but n is pre-registered at {SIGN_TEST_N} and is "
        "fixed (D-08) — a different count is a different test from the one committed",
    )
    return tuple(
        _sign(per_fact_by_arm[first][fact]["rate"], per_fact_by_arm[second][fact]["rate"])
        for fact in facts
    )


def sign_test_exact(signs):
    """The exact paired sign test: two-sided in MAGNITUDE, DIRECTIONAL in ALTERNATIVE (D-29).

    ``signs`` is a length-``SIGN_TEST_N`` sequence of ``+1`` / ``-1`` / ``0``. Ties count AGAINST
    the alternative and ``n`` stays 8 (D-08) — a tie is folded into the unfavourable count, never
    discarded and never shrinking the denominator. There is deliberately NO ``n`` parameter.

    Three steps, in this order:

    1. ``positives`` = the count of signs in the declared direction.
    2. **If ``positives <= SIGN_TEST_N / 2``, return ``1.0`` immediately.** The observation is not
       in the declared direction, so it is not evidence for the alternative at any magnitude.
    3. Otherwise compute the two-sided p by ENUMERATING all ``2 ** SIGN_TEST_N`` = 256 sign
       partitions under the null and summing those at least as extreme, in either tail, as the
       observed count. No closed-form binomial shortcut: D-09 specifies the enumeration and the
       enumeration is what the tests pin.

    **Step 2 is a DEFECT FIX, not a refinement.** Under a pure two-sided test ``0/8`` is exactly as
    extreme as ``8/8`` and both give ``0.0078125``, so a pair on which ALL EIGHT FACTS TIED would
    have entered the Holm family as a SIGNIFICANT result — a false positive in the over-claiming
    direction, which is the failure mode this milestone exists to prevent. D-08 originally claimed
    0/8 gives p = 1.0 and was wrong; D-29 is what actually delivers it, via this filter. The
    expected direction is read from ``SIGN_TEST_ALTERNATIVE``, never inferred from the signs in
    hand (T-16-39c / STAT-05).

    The enumerated values: ``8/8 -> 0.0078125``, ``7/8 -> 0.0703125``, ``4/8 -> 1.0``,
    ``1/8 -> 1.0``, ``0/8 -> 1.0``. The Holm first-step margin at ``alpha = 0.05/6`` is unchanged
    by the direction filter, so SC4 and D-09 need no amendment.
    """
    signs = tuple(signs)
    _prove(
        len(signs) == SIGN_TEST_N,
        f"the sign test received {len(signs)} signs but n is pre-registered at {SIGN_TEST_N} and "
        "is FIXED (D-08) — ties are folded in against the alternative rather than discarded, so "
        "nothing may shrink this denominator",
    )
    _prove(
        all(sign in (-1, 0, 1) for sign in signs),
        f"the sign test received {signs}, which is not a sequence of +1 / -1 / 0 — a magnitude "
        "reaching this function means a difference was passed where its sign was expected",
    )
    positives = sum(1 for sign in signs if sign > 0)
    if positives <= SIGN_TEST_N / 2:
        return 1.0
    observed = abs(positives - SIGN_TEST_N / 2)
    total = 2**SIGN_TEST_N  # all 256 sign partitions under the null, enumerated below
    at_least_as_extreme = sum(
        1
        for partition in itertools.product((0, 1), repeat=SIGN_TEST_N)
        if abs(sum(partition) - SIGN_TEST_N / 2) >= observed
    )
    return at_least_as_extreme / total


def assert_family_closed(entered_pairs):
    """T-16-38 — the RUNTIME half: exactly ``HOLM_FAMILY_PAIRS`` entered the gate, no more, no less.

    The static AST scan in ``tests/test_phase16_stats.py`` catches a NEW CALL SITE; this catches a
    DYNAMICALLY-BUILT pair list. Both are needed because a seventh gated comparison can arrive by
    either route, and either one alone leaves the other open.
    """
    entered = tuple(entered_pairs)
    _prove(
        len(entered) == len(set(entered)),
        f"the same pair entered the Holm family twice: {entered}. A duplicated hypothesis inflates "
        "m without adding evidence, which lowers alpha for every other pair at no cost to itself",
    )
    _prove(
        set(entered) == set(HOLM_FAMILY_PAIRS),
        f"{len(set(entered))} pair(s) entered the Holm family, but D-09 closes it at exactly "
        f"{len(HOLM_FAMILY_PAIRS)}: {sorted(set(entered) ^ set(HOLM_FAMILY_PAIRS))} differ. At "
        "m = 7 alpha is 0.0071429, below the achievable p of 0.0078125, so the headline dies "
        "arithmetically at every possible outcome — including perfect unanimity",
    )
    _prove(
        set(SIGN_TEST_ALTERNATIVE) == set(HOLM_FAMILY_PAIRS),
        f"SIGN_TEST_ALTERNATIVE declares a direction for {sorted(SIGN_TEST_ALTERNATIVE)} but the "
        f"family is {sorted(HOLM_FAMILY_PAIRS)} — an undeclared pair is a pair whose direction "
        "could be fixed after its signs are visible, which is what STAT-05 forbids",
    )


def holm(p_values):
    """Holm step-down across the closed family. Returns ``[(pair, p, alpha_at_step, rejected)]``.

    ``p_values`` is ``{pair: p}``. Sorted ascending, ``p_(i)`` is compared against
    ``HOLM_ALPHA / (m - i)`` and **rejection STOPS at the first failure** — every subsequent
    hypothesis is retained regardless of its own p-value, which is the whole point of step-down.

    ``m`` is ``len(HOLM_FAMILY_PAIRS)``, READ from the constant and never retyped: a second literal
    for the family size is a second number that can stop agreeing with the family it prices.

    Holm over Benjamini-Hochberg per STAT-03: these arms share questions and adapters, so BH's
    independence/PRDS assumption fails while Holm is valid under arbitrary dependence.

    The comparison is STRICT (``<``), so a p exactly ON the boundary FAILS — the same arbitration
    ``scripts/phase15_stats.py`` committed for its own gate. It is a distinction without a
    difference here and is recorded rather than relied on: the achievable p values are multiples of
    1/256 (0.0078125, 0.0703125, 0.2890625, 0.7265625, 1.0) and the step alphas are 0.05/k for
    k = 1..6, and no member of either set equals a member of the other.
    """
    m = len(HOLM_FAMILY_PAIRS)
    _prove(
        len(p_values) == m,
        f"holm received {len(p_values)} p-values but the family is closed at {m} (D-09) — a "
        "family priced at one size and populated at another is not the test that was registered",
    )
    ordered = sorted(p_values.items(), key=lambda item: item[1])
    results = []
    rejecting = True
    for index, (pair, p) in enumerate(ordered):
        alpha_at_step = HOLM_ALPHA / (m - index)
        rejecting = rejecting and p < alpha_at_step
        results.append((pair, p, alpha_at_step, rejecting))
    return results


def compare_arms(per_fact_by_arm, *, tier):
    """THE FORMAL VERDICT — the gated tier only, Holm-corrected across exactly the 6 pairs.

    ``tier`` must be ``GATED_TIER``. D-07 makes held-out the single formal verdict; the taught tier
    runs the same protocol in ``taught_replication`` and is explicitly outside this family.

    ``_prove``s that exactly 6 p-values entered — not 5, not 7 — via ``assert_family_closed``, and
    that the arms handed in are exactly ``CONDITION_ORDER``. A run with a missing or extra arm
    would produce a family of the wrong size, and the family's size is what prices alpha.
    """
    _prove(
        tier == GATED_TIER,
        f"compare_arms was asked to gate tier {tier!r}, but D-07 gates {GATED_TIER!r} and ONLY "
        f"{GATED_TIER!r}. Gating both tiers takes the family from 6 to 12, alpha to 0.05/12 = "
        "0.0041667, and 8/8 unanimity (0.0078125) then FAILS — the gate becomes unclearable at "
        "every possible outcome. The taught tier runs through taught_replication, never here",
    )
    _prove(
        set(per_fact_by_arm) == set(CONDITION_ORDER),
        f"compare_arms received arms {sorted(per_fact_by_arm)} but the pre-registered conditions "
        f"are {sorted(CONDITION_ORDER)} — the family's size is what prices alpha, so an arm count "
        "that disagrees with the pre-registration is a different test from the committed one",
    )
    signs = {pair: fact_signs(per_fact_by_arm, pair) for pair in HOLM_FAMILY_PAIRS}
    p_values = {pair: sign_test_exact(pair_signs) for pair, pair_signs in signs.items()}
    assert_family_closed(tuple(p_values))
    return {
        "tier": tier,
        "gated": True,
        "alternative": dict(SIGN_TEST_ALTERNATIVE),
        "signs": signs,
        "p_values": p_values,
        "holm": holm(p_values),
    }


def taught_replication(per_fact_by_arm):
    """The taught tier under the SAME protocol — a pre-registered replication, NEVER a gate (D-07).

    Verbatim, and not paraphrasable: *"o resultado do tier taught nunca altera, reforça
    formalmente, nem substitui o veredito do tier held-out — é evidência corroborante reportada,
    não gate."* — carried on the returned record as ``TAUGHT_TIER_STATUS`` so the clause travels
    with the numbers into the report rather than being remembered separately from them.

    It computes the same per-pair p-values and returns them with ``gated: False`` and NO alpha and
    NO rejection flags, so there is nothing here that could be read as a verdict. **Its result must
    never be passed to ``holm``** — doing so would take the family to 12 and make the gate
    unclearable at every outcome. ``tests/test_phase16_stats.py`` enforces that statically.
    """
    _prove(
        set(per_fact_by_arm) == set(CONDITION_ORDER),
        f"taught_replication received arms {sorted(per_fact_by_arm)} but the pre-registered "
        f"conditions are {sorted(CONDITION_ORDER)} — a replication run over a different arm set "
        "is not a replication of the gated comparison",
    )
    signs = {pair: fact_signs(per_fact_by_arm, pair) for pair in HOLM_FAMILY_PAIRS}
    p_values = {pair: sign_test_exact(pair_signs) for pair, pair_signs in signs.items()}
    return {
        "tier": REPLICATION_TIER,
        "gated": False,
        "status": TAUGHT_TIER_STATUS,
        "alternative": dict(SIGN_TEST_ALTERNATIVE),
        "signs": signs,
        "p_values": p_values,
    }


# =============================================================================================
# ===== PERS-03 CONTEXT PRESSURE — ONE dilution axis, truncation DERIVED (D-26 / D-27 / D-28) ==
# =============================================================================================
#
# THE SWEEP IS DESCRIPTIVE BY CONSTRUCTION AND IS NEVER GATED (D-09 / STAT-06). Attaching a
# threshold or a p-value to any cell below would take the Holm family from 6 to 7, price alpha at
# 0.0071429 — below the achievable p of 0.0078125 — and kill the headline arithmetically at every
# outcome. `tests/test_phase16_stats.py::test_context_pressure_sweep_is_not_gated` landed BEFORE
# this code and enforces it against the concrete symbols here.

# `block_size` READ from the committed config, never retyped. Every cell's pressure LABEL is
# derived from whether its target crosses this number, so a retyped literal that drifted from the
# model would relabel every cell while every rate stayed identical. The `_prove` is at module level
# on purpose: a config change must be a LOUD import failure, not a quietly relabelled sweep. It is
# the only import-time execution in this module and it touches no tokenizer, model or device.
SWEEP_BLOCK_SIZE = ModelConfig.block_size
_prove(
    SWEEP_BLOCK_SIZE == 256,
    f"ModelConfig.block_size is {SWEEP_BLOCK_SIZE}, not the 256 this sweep's crossing point was "
    "pre-registered against (16-CONTEXT.md §Measured Facts). SWEEP_PROMPT_TARGETS was chosen so "
    "the crossing falls between two NAMED cells; a different block size moves the crossing and "
    "silently relabels which cells truncate",
)

# 16-CONTEXT.md §Measured Facts — CITED, never re-derived. The recall prompt is 33 tokens bare and
# 46 with a 13-token persona span, so 46 is the sweep's nominal first cell (statement only, no
# filler). Both numbers are inputs to the LENGTH TARGETING only; no rate is computed from them.
#
# Measured here for the report, and it is a DISTRIBUTION rather than the nominal: over the binding
# fixture's own 270 questions the bare prompt runs 14 / 28 / 63 tokens (min / median / max),
# because the prompt is `3 role ids + len(question ids)` and the fixture's questions differ in
# length. 33 is the committed nominal, not a constant the run reproduces — which is exactly why
# every cell below records its MEASURED length distribution alongside its target (the 16-07
# lesson: the far row is 13 / 26 / 60, never "~30").
SWEEP_NOMINAL_BARE_PROMPT = 33
SWEEP_NOMINAL_PERSONA_SPAN = 13

# Planner discretion, exercised inside D-27's constraint and recorded (16-CONTEXT §Claude's
# Discretion names the dilution step sizes as discretionary; the CROSSING is not). `block_size` is
# crossed between 224 and 320, so exactly two of the six cells are `dilution + truncation` and four
# are `dilution` alone.
SWEEP_PROMPT_TARGETS = (46, 96, 160, 224, 320, 448)
_prove(
    SWEEP_PROMPT_TARGETS[0] == SWEEP_NOMINAL_BARE_PROMPT + SWEEP_NOMINAL_PERSONA_SPAN,
    f"the sweep's first cell is {SWEEP_PROMPT_TARGETS[0]} tokens but the committed nominal is "
    f"{SWEEP_NOMINAL_BARE_PROMPT} bare + {SWEEP_NOMINAL_PERSONA_SPAN} persona — the axis must "
    "START at the measured nominal, or its first cell is already a pressure nobody declared",
)

# How close a built cell must land to its target. The floor on this is structural: the shortest
# filler line costs ~5 ids in this near-character-level vocabulary, so no builder can land closer
# than about half that on every statement. Measured over all ten committed statements, the
# hill-climb below lands within 3 on every cell whose target the statement can reach at all.
SWEEP_LENGTH_TOLERANCE = 5

# The dilution material. PersonaChat-register first-person lines that touch NO scored slot — no
# name, pet, sibling, town, street, birth year, house number, colour or food — in the same spirit
# as `phase14_recall.UNRELATED_QUESTIONS`. `assert_filler_carries_no_value` proves that against the
# committed fact set AND the candidate pool at run time rather than by eye, because a filler line
# that happened to carry a locked value would put a second answer in the persona span and the cell
# would report a rate that measures the filler.
SWEEP_FILLER_LINES = (
    "i often help my neighbours carry their shopping bags home.",
    "i take the early bus to work and listen to the radio on the way.",
    "i like watching old movies on quiet rainy afternoons.",
    "i keep a few small plants on the balcony and water them daily.",
    "i have been learning to play the guitar for about a year now.",
    "i try to read a little every night before going to sleep.",
    "i usually go to bed early and wake up before sunrise.",
    "i enjoy long walks when the weather is mild.",
    "i work at the library on weekdays.",
    "i am saving up for a holiday.",
    "i talk too much.",
    "i work hard.",
    "i sleep.",
)

ASSERT_VALUE_IN_PROMPT_CAVEAT = (
    "CAVEAT — `assert_value_in_prompt` PASSES on the truncated cells, and that pass must never be "
    "read as 'the value was in view'. `phase14_recall.run_fairness_control` asserts over the full "
    "`prompt_ids` it built, while `personacore/generation/core.py:65` feeds the model "
    "`idx[:, -bs:]` — the LAST `block_size` ids. On a cell whose prompt exceeds `block_size` the "
    "assertion is therefore checking a region the model never sees. That is not a defect in the "
    "assertion: it proves the value was PLACED, which is what the cell is built to do. The entire "
    "point of the crossing cells is that the placed value is then cropped away, and every such "
    "cell in the table above reports the statement's own token offset, so the crop is shown "
    "rather than assumed."
)

ADVERSARIAL_OVERWRITE_NOTE = (
    "SC5's third pressure, on its OWN axis at nominal length — NOT a point on the dilution axis. A "
    "contradicting same-slot value is folded into the taught statement, AFTER the taught value, "
    "inside that same string. It is a STATEMENT, not a prompt: "
    "`phase14_recall.run_fairness_control` builds its own prompt from the `statements` map "
    "(`phase14_recall.py:1262-1264`) and accepts no prebuilt prompt, so a prompt builder for this "
    "cell would be dead code on this route. The competitor is drawn from the committed 20-value "
    "lexicon (`candidate_pool`, D-23) by a fixed rotation, never hand-picked. SLOT MATCHING IS NOT "
    "ATTEMPTED and that is recorded rather than repaired: the committed lexicon carries no slot "
    "partition, and inventing one would be exactly the editorial judgment D-23 chose that lexicon "
    "to avoid. The competitor is therefore a plausible same-lexicon alternative, which is the "
    "property `find_contradictions` already relies on, and not necessarily a same-slot one."
)

# The overwrite cell's label. Deliberately neither `dilution` nor `dilution + truncation`, so a
# reader (and `assert_no_gate_on_sweep`-style greps) can tell the off-axis row from the six on-axis
# ones without counting.
OVERWRITE_PRESSURE_LABEL = "adversarial overwrite (own axis, nominal length)"

# D-26's table, as data. Each entry states its own reason as a full sentence so an absence reads as
# a decision rather than an oversight.
SWEEP_APPLICABILITY = {
    "adapter-only": (
        "proof",
        "PROOF, cited and not re-measured: `scripts/phase14_recall.py:1336 "
        "run_bit_identity_control` measured a max ABSOLUTE DIFFERENCE of exactly 0.0 between the "
        "adapter-off logits "
        "and the un-adapted base on the real 13.9M convbase with the real persona adapter. The "
        "weight arm's memory is not in the context window at all, so context pressure cannot "
        "reach it; an invariance PROOF is stronger evidence of that than any statistic, and "
        "re-measuring it under pressure would replace a proof with an estimate.",
    ),
    "base-neither": (
        "not_applicable",
        "NOT APPLICABLE: the fact is nowhere — not in the weights, not in the context window — so "
        "there is no context-borne memory for dilution, truncation or overwriting to act on. A "
        "swept cell here would report a rate that measured nothing while still looking measured.",
    ),
    "embedding-cosine": (
        "not_applicable",
        "NOT APPLICABLE: the fact lives in the closed candidate pool this arm retrieves over, and "
        "the pool is not the context window. Pressuring the prompt would leave the retrieval set "
        "untouched, so the cell would vary the one thing this arm does not read.",
    ),
    "prompt-stuffed": (
        "measured",
        "MEASURED: the only arm carrying the fact in the context window, which is the surface "
        "every SC5 pressure acts on. All six dilution cells and the overwrite cell run here and "
        "nowhere else (D-26).",
    ),
}


def sweep_cells():
    """The SIX on-axis dilution cells. There is NO independent truncation axis (D-27).

    Truncation cannot fire until dilution has already pushed the context past ``block_size``: the
    recall prompt is 33 tokens bare and 46 with a persona span, against a 256-token window. A
    truncation cell built independently would therefore be *the largest dilution cell under a
    second name*, and the report would state one effect twice. So this returns ONE ordered
    dilution axis and each cell's ``pressure_label`` is DERIVED from whether its target crosses
    ``SWEEP_BLOCK_SIZE`` — ``"dilution"`` at or below it, ``"dilution + truncation"`` above it.

    Six cells, exactly two of which cross. The overwrite cell is deliberately NOT a member here:
    it is a third pressure on its own axis at nominal length, and ``run_sweep`` runs it as a
    SEVENTH run after these six. That is why the wall-clock budget and the threat model both say
    "7 cells (6 dilution + 1 overwrite)" while this tuple holds 6 — the two counts are consistent,
    not a discrepancy, and rendering this function's output alone would show 6 rows against 7 runs
    in the log and read as a dropped cell.
    """
    return tuple(
        {
            "target_tokens": target,
            "crosses_block_size": target > SWEEP_BLOCK_SIZE,
            "pressure_label": (
                "dilution + truncation" if target > SWEEP_BLOCK_SIZE else "dilution"
            ),
        }
        for target in SWEEP_PROMPT_TARGETS
    )


def _persona_span_ids(tok, lines):
    """The persona span's ids, encoded EXACTLY as ``encode_dialogue`` will encode them.

    ``build_recall_prompt(tok, question, persona=[span])`` reaches
    ``tok.encode("\\n".join(detokenize(p) for p in persona), allowed_special="none")``
    (``serialize.py:82``). The sweep hands the joined lines in as a SINGLE persona string, so that
    reduces to ``tok.encode(detokenize(span), ...)`` — reproduced here rather than measured through
    ``build_recall_prompt(..., persona=...)``, because this module adds NO ``persona=`` call site
    (D-21's allowlist is hard equality and this plan does not touch it).
    """
    return tok.encode(detokenize("\n".join(lines)), allowed_special="none")


def _nominal_prompt_tokens(tok, lines):
    """The built prompt's length at the NOMINAL question, measured with the tokenizer.

    ``prompt = [<|system|>] + persona ids + [<|user|>] + question ids + [<|assistant|>]``, so the
    only term the sweep varies is the persona span. The three role ids and the nominal question's
    ids are already inside the committed ``SWEEP_NOMINAL_BARE_PROMPT``, which makes this exact
    arithmetic rather than an estimate — at the nominal question length. Real questions run 14-63
    tokens bare, so every cell also records its MEASURED distribution from the run itself.
    """
    return SWEEP_NOMINAL_BARE_PROMPT + len(_persona_span_ids(tok, lines))


def assert_filler_carries_no_value():
    """No filler line may carry a locked value, a soft-tier value, or a candidate-pool value.

    A filler line that happened to contain one would put a SECOND answer in the persona span, and
    the cell's rate would then measure the filler rather than the pressure — invisibly, because
    the number would still look like a measurement. Checked with ``contains_value``, the phase's
    single scorer, so "carries a value" means here exactly what it means when a draw is scored.
    """
    import phase14_factset as fs  # LAZY — see the LAZY-IMPORT RULE in the module docstring.

    values = set(candidate_pool()) | {fact.value for fact in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS}
    carrying = sorted(
        {
            line
            for line in SWEEP_FILLER_LINES
            for value in values
            if recall.contains_value(line, value)
        }
    )
    _prove(
        not carrying,
        f"{len(carrying)} filler line(s) carry a scored value, e.g. {carrying[:2]} — the dilution "
        "material would then answer the question it is supposed to bury, and the cell's rate would "
        "measure the filler instead of the pressure",
    )


def build_diluted_persona(tok, statement, target_tokens):
    """The diluted persona span for one fact at one target, with the measurements that prove it.

    **All dilution happens INSIDE the persona span, and there is no turns axis to dilute along.**
    ``build_recall_prompt`` (``src/personacore/dialogue/serialize.py:92``) calls
    ``encode_dialogue(tok, persona, [(question, "")])`` — exactly ONE turn. And ``PERSONA_CAP``
    does NOT bite on this route: it is enforced only by ``cap_persona``
    (``serialize.py:115``), which ``build_recall_prompt`` never calls, so the persona span reaches
    448 tokens directly.

    **Both facts are written here because an earlier draft of this plan inherited the OPPOSITE
    premise** from 16-RESEARCH Pitfall 4 — which asserted, stamped ``[VERIFIED]``, that the cap
    forces dilution to come from added turns. That sentence was struck and corrected at ``79fa01a``
    along with ROADMAP SC5 and REQUIREMENTS PERS-03 ("dilution across turns" -> "dilution within
    the persona span"). Recording the correction at the call site is what stops Phases 17 and 18
    re-inheriting it.

    **Placement is load-bearing, not cosmetic.** ``generate`` crops to the LAST ``block_size`` ids
    (``src/personacore/generation/core.py:65`` — ``idx_cond = idx[:, -bs:]``), so truncation removes
    the HEAD of the prompt. The fact-bearing statement therefore sits at the head of the span and
    filler is APPENDED after it. Prepending filler would leave the statement inside the trailing
    256-token window, and the ``crosses_block_size`` cells would measure nothing while still
    emitting a number.

    The fill is a hill-climb: append whichever filler line brings the built prompt CLOSEST to the
    target, and stop when no line improves it. Greedy longest-that-fits was measured first and left
    a 6-token gap on some statements; the hill-climb lands within 3 on every reachable cell.

    Returns the line list under ``lines`` together with the measurements the report needs, because
    re-measuring them at the call site would be a second place they can be wrong:

    * ``achieved_prompt_tokens`` — the nominal built length, and ``overshoots_target`` when the
      statement alone already exceeds the target (true for the two soft-tier statements at the 46
      cell, which are 25 and 22 ids against a 13-id nominal — recorded, never trimmed).
    * ``statement_head_offset`` — 1: the statement's ids begin immediately after ``<|system|>``.
    * ``statement_end_offset`` — a CONSERVATIVE end, encoding the statement together with its
      newline separator so any BPE merge across that boundary is counted INSIDE the statement's run
      rather than excluded from it.
    """
    lines = [statement]
    achieved = _nominal_prompt_tokens(tok, lines)
    while True:
        length, line = min(
            ((_nominal_prompt_tokens(tok, lines + [f]), f) for f in SWEEP_FILLER_LINES),
            key=lambda pair: (abs(pair[0] - target_tokens), pair[0]),
        )
        if abs(length - target_tokens) >= abs(achieved - target_tokens):
            break
        lines.append(line)
        achieved = length
    span_ids = _persona_span_ids(tok, lines)
    _prove(
        span_ids[: len(tok.encode(detokenize(statement), allowed_special="none"))]
        == tok.encode(detokenize(statement), allowed_special="none"),
        f"the statement is not at the HEAD of the diluted span for target {target_tokens} — "
        "`generate` crops to the LAST block_size ids, so a statement anywhere but the head would "
        "survive truncation and the crossing cells would measure nothing while emitting a number",
    )
    return {
        "lines": tuple(lines),
        "target_tokens": target_tokens,
        "achieved_prompt_tokens": achieved,
        "overshoots_target": achieved > target_tokens + SWEEP_LENGTH_TOLERANCE,
        "persona_span_tokens": len(span_ids),
        "statement_head_offset": 1,
        "statement_end_offset": 1
        + len(tok.encode(detokenize(statement) + "\n", allowed_special="none")),
    }


def overwrite_competitor(value, pool):
    """The contradicting value for one fact: the NEXT pool member after its own, wrapping.

    Deterministic and hand-free. When the fact's own value is in the committed lexicon the
    rotation spreads competitors across facts instead of giving every fact the same one; when it
    is not, the first pool member that is not this fact's own value is taken. Either way the
    choice is a property of the sorted committed pool, never an editorial judgment (D-23).
    """
    _prove(pool, "the overwrite cell was handed an empty candidate pool")
    if value in pool:
        candidate = pool[(pool.index(value) + 1) % len(pool)]
    else:
        candidate = next((entry for entry in pool if entry != value), None)
    _prove(
        candidate is not None and candidate != value,
        f"no pool member differs from {value!r} — an 'overwrite' by the fact's own value is not a "
        "contradiction, and the cell would report the undiluted arm under a pressure's name",
    )
    return candidate


def build_overwrite_statement(statement, competitor):
    """A STATEMENT STRING carrying the taught value and then a contradicting one — not a prompt.

    See ``ADVERSARIAL_OVERWRITE_NOTE`` for why this returns a statement: the fairness control
    builds its own prompt from the ``statements`` map, so this cell routes through that map exactly
    as every dilution cell does. This module therefore adds NO new ``persona=`` call site and NO
    new ``draw_all`` call site — ``PERSONA_ALLOWLIST`` stays at exactly two entries and the widened
    D-21 guard in ``tests/test_phase14_scoring.py`` stays green without that file being touched.

    The competitor is placed AFTER the taught value inside the same string, so the taught value is
    still at the head of the span and ``assert_value_in_prompt`` still finds it.
    """
    _prove(statement and competitor, "the overwrite cell needs both a statement and a competitor")
    return f"{statement} actually it is {competitor}."


def sweep_applicability():
    """D-26 as a four-arm table: one arm MEASURED, one PROOF, two NOT APPLICABLE — with reasons.

    Every arm appears, and every entry carries its own reason as a full sentence, so an arm's
    absence from the sweep reads as a recorded decision rather than as an oversight.
    """
    _prove(
        set(SWEEP_APPLICABILITY) == set(CONDITION_ORDER),
        f"the applicability table covers {sorted(SWEEP_APPLICABILITY)} but the pre-registered "
        f"conditions are {sorted(CONDITION_ORDER)} — an arm with no stated treatment is an arm "
        "whose absence from the sweep is undocumented",
    )
    return {
        condition: {
            "treatment": SWEEP_APPLICABILITY[condition][0],
            "reason": SWEEP_APPLICABILITY[condition][1],
        }
        for condition in CONDITION_ORDER
    }


def monotone_claim_allowed(ladder_branch):
    """D-28: monotone prompt-arm degradation may be claimed ONLY if the ladder got arm B off floor.

    Reads the branch the COMMITTED ladder recorded in 16-07; it never re-derives it and never
    re-runs it. Every branch except ``no_rung_passed`` means some rung passed, i.e. the base could
    use a value placed in its own context window at some span — which is the minimum required for
    a degradation curve on that arm to be about pressure rather than about the arm being at the
    floor before any pressure was applied.
    """
    _prove(
        ladder_branch in ladder.HEADLINE_BRANCHES,
        f"branch {ladder_branch!r} is not one of the committed ladder branches "
        f"{sorted(ladder.HEADLINE_BRANCHES)} — a branch invented here could license a claim the "
        "ladder never made",
    )
    return ladder_branch != "no_rung_passed"


def _length_spread(values):
    """``{min, median, max}`` — a length is a DISTRIBUTION and is never rendered as a constant.

    The 16-07 lesson, applied: the ladder's far row measured 13 / 26 / 60 and printing "~30" would
    have hidden the whole spread. Every prompt length this sweep publishes goes through here.
    """
    ordered = sorted(values)
    _prove(ordered, "a length spread was asked for over no measurements")
    return {"min": ordered[0], "median": statistics.median(ordered), "max": ordered[-1]}


def _sweep_cell_result(cell, built, record):
    """One cell's published row: its targets, its MEASURED lengths, and its rate with a bound.

    ``built`` is ``{fact_id: build_diluted_persona(...)}`` and ``record`` is the fairness control's
    own return. The crop evidence is computed against each question's OWN measured prompt length —
    the statement's id run is outside the trailing ``block_size`` window exactly when
    ``statement_end_offset <= prompt_len - SWEEP_BLOCK_SIZE`` — so the report shows the value was
    cropped rather than asserting it from the nominal.
    """
    questions = record["questions"]
    measured = [len(entry["prompt_ids"]) for entry in questions]
    outside = [
        entry
        for entry, length in zip(questions, measured, strict=True)
        if built[entry["fact_id"]]["statement_end_offset"] <= length - SWEEP_BLOCK_SIZE
    ]
    return {
        **cell,
        "nominal_prompt_tokens": _length_spread(
            [entry["achieved_prompt_tokens"] for entry in built.values()]
        ),
        "measured_prompt_tokens": _length_spread(measured),
        "n_over_block_size": sum(1 for length in measured if length > SWEEP_BLOCK_SIZE),
        "statement_head_offset": 1,
        "statement_end_offset": _length_spread(
            [entry["statement_end_offset"] for entry in built.values()]
        ),
        "n_statement_outside_window": len(outside),
        "overshooting_facts": sorted(
            fact_id for fact_id, entry in built.items() if entry["overshoots_target"]
        ),
        "k": record["k"],
        "n": record["n"],
        "n_answerable": record["n_answerable"],
        "proportion": report_proportion(record["n_answerable"], len(questions), record["n"]),
    }


def run_sweep(model, tok, device, forbid, items, statements):
    """The PERS-03 sweep: six dilution cells on ONE axis, then the overwrite cell on its own.

    **Arm B only** (D-26). ``sweep_applicability`` states the other three arms' treatments with
    their reasons, and this function measures none of them.

    **Seven runs, six on-axis cells.** ``sweep_cells()`` returns the six dilution cells; the
    adversarial overwrite runs once afterwards at nominal length as a SEVENTH run on its own axis.
    The returned ``cells`` list therefore carries 7 entries and the report renders all 7, with the
    overwrite row labelled off-axis. Rendering ``sweep_cells()`` alone would show 6 rows against 7
    runs in the log and read as a dropped cell.

    **Every cell goes through the ``statements`` map — this function never builds a prompt.** The
    dilution cells substitute the joined diluted span for that fact's statement; the overwrite cell
    substitutes ``build_overwrite_statement``. ``phase14_recall.run_fairness_control`` then builds
    the prompt exactly as it does for the undiluted arm, which is what keeps the sweep on the same
    instrument as the arm it pressures.

    **The first cell is the nominal condition.** At target 46 no filler fits, so cell 1 is the
    undiluted arm re-run on the same axis — the baseline row every later cell is read against.

    **Descriptive only** (D-09 / STAT-06). No threshold, no p-value, no gate: a seventh gated
    comparison prices Holm's first step at 0.0071429, below the achievable 0.0078125.

    Budget: 7 x 270 questions x >=3.18 s is a ~100 min FLOOR, and the 3.18 s median was measured at
    the 46-token nominal. There is no KV cache (D-04), so every decode step recomputes the full
    forward and per-question cost grows with prompt length. Budget 100 min to ~3 h; a single cell
    taking 2 h is EXPECTED, not a hang. Do not trim the cell set to fit a clock.
    """
    _prove(items, "the context-pressure sweep received no questions")
    _prove(statements, "the context-pressure sweep received no first-person statements")
    assert_filler_carries_no_value()
    pool = candidate_pool()

    cells = sweep_cells()
    _prove(
        len(cells) == len(SWEEP_PROMPT_TARGETS) == 6,
        f"the dilution axis holds {len(cells)} cells but six were pre-registered — the crossing "
        "point was chosen against that set, so a different one relabels which cells truncate",
    )

    results = []
    for cell in cells:
        built = {
            fact_id: build_diluted_persona(tok, statement, cell["target_tokens"])
            for fact_id, statement in statements.items()
        }
        print(
            f"[phase16_persistence] ===== sweep cell {cell['target_tokens']} tokens "
            f"({cell['pressure_label']}) ====="
        )
        record = recall.run_fairness_control(
            model,
            tok,
            device,
            forbid,
            items,
            {fact_id: "\n".join(entry["lines"]) for fact_id, entry in built.items()},
        )
        results.append(_sweep_cell_result(cell, built, record))
        formatted = results[-1]["proportion"]["formatted"]
        print(f"[phase16_persistence] sweep cell {cell['target_tokens']}: {formatted}")

    # The fact's own value comes off the ITEMS, never parsed back out of its statement string: a
    # parser would silently pick the wrong token the moment a SLOT_FORM changed shape.
    values = {item.fact.id: item.fact.value for item in items}
    _prove(
        set(statements) == set(values),
        f"the sweep holds statements for {sorted(set(statements) - set(values))} that no question "
        f"asks about, and questions for {sorted(set(values) - set(statements))} with no statement "
        "— the overwrite cell needs each fact's own value, and a partial map would abort mid-cell "
        "after the dilution cells had already spent an hour",
    )
    competitors = {fact_id: overwrite_competitor(values[fact_id], pool) for fact_id in statements}
    overwritten = {
        fact_id: build_overwrite_statement(statement, competitors[fact_id])
        for fact_id, statement in statements.items()
    }
    built = {
        fact_id: {
            "lines": (statement,),
            "target_tokens": SWEEP_PROMPT_TARGETS[0],
            "achieved_prompt_tokens": _nominal_prompt_tokens(tok, [statement]),
            "overshoots_target": False,
            "persona_span_tokens": len(_persona_span_ids(tok, [statement])),
            "statement_head_offset": 1,
            "statement_end_offset": 1
            + len(tok.encode(detokenize(statement) + "\n", allowed_special="none")),
        }
        for fact_id, statement in overwritten.items()
    }
    print(f"[phase16_persistence] ===== sweep cell {OVERWRITE_PRESSURE_LABEL} =====")
    record = recall.run_fairness_control(model, tok, device, forbid, items, overwritten)
    results.append(
        {
            **_sweep_cell_result(
                {
                    "target_tokens": SWEEP_PROMPT_TARGETS[0],
                    "crosses_block_size": False,
                    "pressure_label": OVERWRITE_PRESSURE_LABEL,
                },
                built,
                record,
            ),
            "competitors": competitors,
        }
    )
    return {
        "cells": results,
        "applicability": sweep_applicability(),
        "block_size": SWEEP_BLOCK_SIZE,
        "targets": SWEEP_PROMPT_TARGETS,
        "assert_value_in_prompt_caveat": ASSERT_VALUE_IN_PROMPT_CAVEAT,
        "adversarial_overwrite_note": ADVERSARIAL_OVERWRITE_NOTE,
    }


# =============================================================================================
# ===== THE PERSISTENCE REPORT — every framing string committed BEFORE the run fills it =======
# =============================================================================================

PERSISTENCE_REPORT_PATH = _REPO_ROOT / "results" / "phase16_persistence_report.md"

PERSISTENCE_REPORT_FRAMING = (
    "**What this report is.** The four-arm weight-versus-prompt comparison this phase exists to "
    "run, plus its descriptive interval, its one inferential gate and its pre-registered "
    "qualifiers. Every framing string below is a module-level constant in "
    "`scripts/phase16_persistence.py`, committed to git BEFORE the run that filled it; every "
    "number is interpolated from the run or formatted by a committed helper. A report whose text "
    "is written after the numbers is a report written to fit them.\n"
    "\n"
    "**What it may not claim.** The headline is the CAPABILITY LADDER's own output, cited in "
    "`## Verdict` below, and this report may not claim more than that ladder licensed. "
    "**'Not demonstrable at n = 8' is a legitimate, pre-registered outcome recorded as-written**, "
    "exactly as Phase 12 recorded its own null. If the gate does not clear, that is the result — "
    "not a prompt to re-run, soften, or add an unplanned analysis."
)

# D-25's numeric reconciliation, stated openly and never silently applied. The superseded figure is
# NOT retyped here: it appears exactly once in this report, inside the verbatim user text this
# paragraph immediately follows, and `tests/test_phase16_driver.py` pins that count in this
# module's source at one (the comment beside `COSINE_CHANCE_FLOOR`).
ARM_D_FLOOR_RECONCILIATION = (
    "**Numeric reconciliation, flagged rather than silent.** The verbatim qualifier above was "
    "written citing an EIGHT-candidate pool. The pool decision taken in the same round chose the "
    "committed 20-value lexicon `find_contradictions` already consumes (D-23), whose chance floor "
    "is **0.05** — and **0.05 is the number this report uses**, everywhere, in every computation. "
    "The qualifier holds in full at the chosen pool's floor: 0.05 is still an order of magnitude "
    "above arm B (~0.005) and arm C (~0), so a result where arm D wins or ties favourably remains "
    "a consequence of its task being easier by construction rather than evidence of equivalent "
    "capability. This does NOT invalidate the three pairs involving arm D and does NOT remove "
    "them from the Holm family — the margin is intact, 0.0078125 < 0.0083333 — it qualifies the "
    "INTERPRETATION of any arm-D-favourable result and nothing else."
)

SOFT_TIER_EXCLUSION = (
    "**The soft tier is not reported per fact here, and arm D could not be reported for it at "
    "all.** The soft tier feeds neither gated number (`phase14_recall.SOFT_TIER` names it "
    "excluded from the pre-registered gate) and it is outside the Holm family by construction. "
    "Arm D additionally CANNOT score it: the 20-value candidate pool contains no soft-tier "
    "values, so arm D returns nothing on that tier BY CONSTRUCTION — a property of the pool, not "
    "a measurement of the model. Passing that structural absence through `report_proportion` "
    "would dress it in a rule-of-three ceiling and it would read as a measured zero, so no "
    "arm-D soft-tier bound is printed anywhere in this report."
)

# T-16-50 — the citable wall clock, and why the tighter number is refused. The over-precise
# figure is pinned ABSENT from this module by test rather than merely avoided by habit.
WALL_CLOCK_NOTE = (
    "Citable four-arm wall clock: **~39 min (realistically 35-44 min)**. The tighter single "
    "figure the intra-run interval would support is deliberately NOT quoted: arm A measured twice "
    "independently over the same 30 questions gave means 2.654 and 2.380 s per question, 11.5% "
    "apart, which exceeds that interval's own +-4% width. An interval that cannot contain a "
    "repeat of its own measurement understates real uncertainty and must never be quoted alone. "
    "The PERS-03 sweep's clock is reported separately and is much larger: 7 cells x 270 "
    "questions, ~100 min FLOOR to ~3 h, because there is no KV cache (D-04) and per-question cost "
    "grows with prompt length."
)

# The one thing the ladder does NOT license this report to cite, recorded here so a reader who
# follows the citation in `## Verdict` does not pick up the wrong evidence from the other end.
# D-30, recorded in 16-CONTEXT.md BEFORE the four-arm run and emitted here so the qualification
# cannot depend on whoever writes the final prose remembering it. Same structural discipline as
# LADDER_PROXY_DEGENERATE_CAVEAT below and as D-28's monotone permission: a reading rule nobody is
# forced to apply is a reading rule that goes missing exactly when the number looks good.
# A flat sweep is only evidence about pressure if there was something for pressure to act on.
# Emitted beside the cells rather than left to the reader, same discipline as
# LADDER_PROXY_DEGENERATE_CAVEAT and HEADLINE_MECHANISM_CAVEAT.
SWEEP_NO_BASELINE_CAVEAT = (
    "**All seven cells scored 0/270, and that is UNINFORMATIVE about context-pressure degradation "
    "specifically because there was no baseline signal to degrade.** The capability floor already "
    "established by the committed ladder means dilution and adversarial pressure had nothing to "
    "erode: the arm entered the sweep at zero and stayed there. This result does NOT support "
    "'context pressure had no effect' — it supports only 'no measurable effect was observable "
    "given zero baseline recall.' The two readings are not interchangeable, and only the second "
    "one is what was measured. A sweep that could speak to PERS-03's question would need an arm "
    "that recovers the fact at the least-diluted cell, which this arm does not."
)

HEADLINE_MECHANISM_CAVEAT = (
    "**This comparison alone does not distinguish two mechanisms, and does not claim to.** An "
    "adapter-over-prompt result here is consistent with BOTH (1) personalization genuinely living "
    "in the weights, and (2) prompt-stuffing being structurally incapable of recovering a span as "
    "long as the material it is scored on. The committed capability ladder measured the second "
    "directly: the synthetic, guessability-gate-cleared span-5 cells `(5, 2)` and `(5, 30)` each "
    "scored 0 answerable questions of 216, and the top rung on the REAL taught values scored 0 of "
    "216, against real value token lengths of [4,4,4,5,5,6,8,8] (median 5). Because the synthetic "
    "values are gate-cleared, the base provably had no prior knowledge of them, so that zero is "
    "not about which strings were chosen — it is span length. The prompt arm's floor is therefore "
    "explained by measured incapacity at the length of its own material, independently of what the "
    "adapter does. Separating the two would require comparing the arms on material INSIDE the "
    "proven ceiling (~2 tokens); no such condition exists here, because the adapter was trained on "
    "the real 4-8 token values and building a 2-token adapter is a separate training run. That was "
    "checked before this run and found unavailable — so this qualification is an explicit "
    "decision, not an omission. What the result licenses is precise: AT THIS SCALE, weight-based "
    "memory achieves what prompting cannot. Whether it would still win where prompting is capable "
    "is NOT tested here, and a headline omitting that is measuring a capability deficit and "
    "calling it a mechanism win."
)

LADDER_PROXY_DEGENERATE_CAVEAT = (
    "**This report does not cite the ladder's D-15 `proxy_consistent` verdict as validation of "
    "anything.** That check compared two cells which BOTH scored zero answerable questions out of "
    "216, so they agree trivially: a difference of zero is what two dead cells produce whether or "
    "not the synthetic substitution was fair. The check can only detect unfairness that MOVES the "
    "count, and at the floor there is no movement to detect. The ladder's own report records this "
    "caveat; it is repeated here because the branch cited above and that verdict sit in the same "
    "artifact, and a reader following one could pick up the other as evidence it is not."
)

FLOOR_UNITS_NOTE = (
    "The committed floor stated in BOTH units, computed by `phase16_ladder.floor_in_both_units()` "
    "from the shared bounds. The draw-unit bound is roughly NINE TIMES tighter than the "
    "question-unit one, and citing the draw unit alone makes the prompt arm look far more "
    "definitively at zero than STAT-01's unit supports. Both are printed side by side, with the "
    "draw unit labelled as the one STAT-01 FORBIDS for inference, so the tighter number cannot "
    "quietly become the one that gets quoted (T-16-26)."
)

GATE_FRAMING = (
    "The exact paired sign test over all 2**8 = 256 sign partitions, Holm-corrected across "
    "EXACTLY the six pairs D-09 closes the family at. Ties count AGAINST the alternative and n "
    "stays 8 (D-08); the alternative's direction per pair was committed before the run (D-29). "
    "**Only 8/8 unanimity clears**: the achievable p at unanimity is 0.0078125 against a "
    "first-step alpha of 0.05/6, a margin of 6.7% relative — and a SEVENTH gated comparison would "
    "price that step at 0.0071429 and kill the headline arithmetically at every possible outcome, "
    "including perfect unanimity. That is why the taught replication and the PERS-03 sweep are "
    "descriptive by construction and enter nothing (STAT-06)."
)

# The verdict-line the recorded outcome takes when the gate does not clear. Committed as a string
# BEFORE the run, so the null result is rendered rather than written after seeing it.
NOT_DEMONSTRABLE = (
    "**NOT DEMONSTRABLE AT n = 8.** No pair cleared its Holm step. This is a legitimate, "
    "pre-registered outcome recorded as-written — the same register in which Phase 12 recorded "
    "its own null — and not a prompt to re-run, to soften, or to add an unplanned analysis."
)

# D-28's two outcomes, BOTH committed as strings before the run and interpolated, never written
# as prose around a curve someone has already seen. The licensed branch is NOT a blank cheque: the
# condition D-28 states is branch-level ("the ladder got that arm off the floor"), and the branch's
# own statement is what bounds how far the resulting reading may be pushed. Stating that bound in
# the SAME paragraph as the permission is the whole point — a permission printed alone is the
# sentence a reader quotes.
MONOTONE_CLAIM_LICENSED = (
    "D-28's condition is met at the branch level: the committed ladder branch is `{branch}`, so "
    "at least one rung passed and the prompt arm was not at the floor everywhere. **That is the "
    "whole of what is licensed, and the branch statement in `## Verdict` bounds it.** A monotone "
    "reading of the cells above describes the degradation of a capability the ladder LOCATED at "
    "that rung — not of this arm's ability to carry the real taught values, which are longer than "
    "the passing rung's span and on which every longer-span rung failed. Read the two together or "
    "neither."
)

MONOTONE_CLAIM_REFUSED = (
    "**Monotone prompt-arm degradation is NOT claimed.** The committed ladder branch is "
    "`{branch}`: the prompt arm was never off the floor, so a monotone reading of the cells above "
    "would describe a curve with nowhere to fall from. D-28 makes the ladder the licence for this "
    "claim, and the ladder did not grant it."
)

_LADDER_VERDICT_RE = re.compile(r"\*\*Branch: `([a-z0-9_]+)`\*\* — highest passed rung: `(.+?)`\.")

# D-25's qualifier lives in the planning artifact and is READ from it, not retyped as a constant
# here. Two reasons, and the second is the binding one:
#
#   1. "Verbatim" asserted against a second hand-typed copy proves only that two copies agree,
#      which is exactly the failure a verbatim requirement exists to prevent. Reading the source
#      of truth makes drift impossible by construction rather than by test.
#   2. That text CONTAINS the superseded chance-floor figure, and
#      `tests/test_phase16_driver.py:627` pins this module's source at exactly ONE occurrence of
#      it — in the comment beside `COSINE_CHANCE_FLOOR` that records the reconciliation. A
#      constant here would be a second occurrence. The committed guard is substantively right (the
#      superseded figure must appear once, where it is recorded, and in no computation), so the
#      fix goes on this side of the line rather than by weakening it.
_CONTEXT_PATH = (
    _REPO_ROOT
    / ".planning"
    / "phases"
    / "16-weight-vs-prompt-persistence-control"
    / "16-CONTEXT.md"
)
ARM_D_QUALIFIER_ANCHOR = "- **D-25:**"


def arm_d_qualifier():
    """D-25's user instruction, VERBATIM, read from ``16-CONTEXT.md`` — see the comment above."""
    _prove(
        _CONTEXT_PATH.exists(),
        f"{_CONTEXT_PATH} is missing — D-25's qualifier is a pre-registered user instruction that "
        "MUST appear before any run, and this report cannot publish arm D's pairs without it",
    )
    body = _CONTEXT_PATH.read_text(encoding="utf-8").split(ARM_D_QUALIFIER_ANCHOR, 1)
    _prove(len(body) == 2, f"{ARM_D_QUALIFIER_ANCHOR!r} is absent from {_CONTEXT_PATH}")
    lines = []
    for line in body[1].splitlines():
        stripped = line.strip()
        # A slice rather than the str prefix METHOD: 16-08's
        # `test_cosine_arm_is_scored_by_contains_value` forbids every rival string predicate
        # ANYWHERE in this module's source, so that no second scoring rule can live beside
        # `contains_value`. That guard is substantively right and is a source-substring check, so
        # the cheapest correct fix is on this side of the line — never by relaxing a committed
        # guard to accommodate a markdown reader, and never by naming the forbidden token in a
        # comment either (16-09 deviation 4 recorded exactly that category error).
        if stripped[:1] == ">":
            lines.append(stripped.lstrip(">").strip())
        elif lines:
            break
    _prove(lines, f"no blockquote follows {ARM_D_QUALIFIER_ANCHOR!r} in {_CONTEXT_PATH}")
    return " ".join(lines).strip('"')


def assert_persistence_report_not_clobbered():
    """A RECORDED verdict is committed evidence. Refuse to overwrite it (T-16-49).

    Mirrors ``phase14_recall.assert_report_not_clobbered:1694`` and
    ``phase16_ladder.assert_ladder_report_not_clobbered``, and is called FIRST in ``main()`` for
    the same reason both of those are: a multi-hour run that refuses to write its report at the
    end has already been wasted.

    **Anchored on the SECTION via ``_verdict.VERDICT_SECTION``, never on a split of the heading
    literal** — the 15-04 CR-02 defect. A prose mention of that heading (this phase's reports cite
    each other) cannot then be mistaken for the section itself, which is what turned the guard on
    its own correct usage last time. ``None`` (no verdict section at all) and a body without
    ``PENDING``
    are both refusals: a file this writer did not produce must not be blindly overwritten either.
    There is no force flag. This report is written once.
    """
    if not PERSISTENCE_REPORT_PATH.exists():
        return
    recorded = recorded_verdict(PERSISTENCE_REPORT_PATH.read_text(encoding="utf-8"))
    if recorded is None or "PENDING" not in recorded:
        raise SystemExit(
            f"[phase16_persistence] {PERSISTENCE_REPORT_PATH} already carries a recorded verdict "
            "— it is this phase's committed four-arm evidence. Re-running over it would destroy a "
            "measurement that cannot be re-derived without breaking the pre-registration. There "
            "is no force flag: if it must genuinely be regenerated, delete it in a reviewed "
            "commit so the removal is visible in the diff."
        )


def committed_ladder_rungs():
    """``(passed_rungs, recorded_branch)`` READ off the committed ladder report (PERS-01).

    The ladder ran in 16-07 and its report is committed evidence; this reads the branch and the
    highest passed rung it RECORDED and never re-derives, re-runs or re-interprets them. The rung
    string is matched back against ``RUNG_DIFFICULTY_ORDER`` rather than parsed, so a rung this
    codebase does not know about aborts instead of being coerced into a neighbouring branch.

    The branch is returned alongside so ``write_persistence_report`` can feed the rung through
    ``licensed_headline`` and ``_prove`` the result equals what the ladder committed — which is
    what makes "the headline is the ladder's output" checkable rather than asserted.
    """
    _prove(
        ladder.LADDER_REPORT_PATH.exists(),
        f"{ladder.LADDER_REPORT_PATH} is missing — PERS-01 requires the capability ladder "
        "committed BEFORE this comparison is read, and without it there is no licensed headline",
    )
    recorded = recorded_verdict(ladder.LADDER_REPORT_PATH.read_text(encoding="utf-8"))
    _prove(recorded is not None, f"{ladder.LADDER_REPORT_PATH} carries no `## Verdict` section")
    match = _LADDER_VERDICT_RE.search(recorded)
    _prove(
        match is not None,
        f"the committed ladder verdict does not carry the branch line this reader anchors on:\n"
        f"{recorded.strip()[:400]}",
    )
    branch, highest = match.group(1), match.group(2)
    if highest == "None":
        return (), branch
    rung = next((r for r in ladder.RUNG_DIFFICULTY_ORDER if str(r) == highest), None)
    _prove(
        rung is not None,
        f"the ladder recorded highest passed rung {highest!r}, which is not a member of "
        f"RUNG_DIFFICULTY_ORDER — a rung this codebase cannot name must abort rather than fall "
        "through to a neighbouring branch's licence",
    )
    return (rung,), branch


def ladder_report_commit():
    """The commit that added the committed ladder report — the citation, resolved not asserted."""
    import subprocess

    result = subprocess.run(
        ["git", "log", "-1", "--format=%h", "--", str(ladder.LADDER_REPORT_PATH)],
        capture_output=True,
        text=True,
        cwd=_REPO_ROOT,
    )
    sha = result.stdout.strip()
    _prove(
        sha,
        f"{ladder.LADDER_REPORT_PATH} has no commit in this repository — the licensing artifact "
        "must be COMMITTED before the comparison that cites it, which is SC1's whole ordering "
        "constraint (PREREG-02)",
    )
    return sha


def core_fact_ids():
    """The 8 core fact ids, the ONLY facts the gated comparison is computed over.

    ``normalize_by_split`` groups by split and keeps the two soft-tier facts alongside the eight
    core ones. ``fact_signs`` requires exactly ``SIGN_TEST_N`` facts, so an unfiltered aggregation
    would abort at ten — and, worse, an aggregation that silently accepted ten would run a
    different test from the one D-08 pre-registered.
    """
    import phase14_factset as fs  # LAZY — see the LAZY-IMPORT RULE in the module docstring.

    ids = frozenset(fact.id for fact in fs.LOCKED_FACTS)
    _prove(
        len(ids) == SIGN_TEST_N,
        f"the committed fact set holds {len(ids)} core facts but n is pre-registered at "
        f"{SIGN_TEST_N} and is FIXED (D-08)",
    )
    return ids


def per_fact_by_arm(arm_records, *, tier):
    """``{condition: aggregate_by_fact(...)}`` for one split, over the core facts only.

    ONE grouping site, called by both the gate and the report writer: a second grouping is a
    second place the core-fact filter can be wrong, and a wrong filter is invisible in every rate
    it produces.
    """
    _prove(
        tier in TIER_SPLITS,
        f"tier {tier!r} is not one of {TIER_SPLITS} — these are RecallItem.split values",
    )
    core = core_fact_ids()
    grouped = {}
    for record in arm_records:
        entries = [entry for entry in record["by_split"].get(tier, ()) if entry["fact_id"] in core]
        _prove(
            entries,
            f"arm {record['condition']!r} carries no {tier!r} entries for the core facts — it "
            "cannot be paired with the arms it is compared against",
        )
        grouped[record["condition"]] = aggregate_by_fact(entries, tier=tier)
    return grouped


def _proportion_row(aggregate):
    """One fact's published rate: the STAT-02 shape, both denominators, a bound, `3/n` at zero."""
    return report_proportion(
        aggregate["n_answerable"], aggregate["n_questions"], aggregate["n_draws"]
    )


def _pooled(aggregates):
    """One arm's pooled counts over the eight facts — summed, never re-derived from the records."""
    return {
        "n_answerable": sum(entry["n_answerable"] for entry in aggregates.values()),
        "n_questions": sum(entry["n_questions"] for entry in aggregates.values()),
        "n_draws": sum(entry["n_draws"] for entry in aggregates.values()),
    }


def _provenance_blocks(arm_records):
    """One block per condition process — D-01's four pids EVIDENCE the split, not assert it."""
    blocks = []
    for record in arm_records:
        blocks += [
            "",
            f"### Condition `{record['condition']}` — its own process",
            "",
        ]
        blocks += [f"- {line}" for line in record["provenance"]]
    return blocks


def _parity_rows(arm_records):
    """The SC2 parity table: the four scalar columns off `SHARED_ARM_CONFIG`, plus `forbid_ids`."""
    rows = [
        "| arm | `max_new_tokens` | `forbid_ids` (masked / sha256) | `stop_ids` | "
        "`context_length` | `n_draws` |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for record in arm_records:
        config = record["config"]
        draws = f"{config['n_draws']}"
        if record["condition"] == "embedding-cosine":
            draws += (
                " (shared budget; this arm REALIZES 1 deterministic draw per question — D-22: "
                "manufacturing 9 draws by softmax-sampling the similarities would produce an "
                "interval measuring the chosen temperature rather than any real uncertainty)"
            )
        rows.append(
            f"| `{record['condition']}` | {config['max_new_tokens']} | "
            f"{record['forbid_ids_masked']} of {record['vocab_size']} / "
            f"`{config['forbid_ids_sha256'][:16]}…` | "
            f"{sorted(config['stop_ids'])} | {config['context_length']} | {draws} |"
        )
    return rows


def _sweep_rows(sweep):
    """The seven sweep cells — six on the dilution axis, the seventh off it and labelled so."""
    rows = [
        "| target | pressure | measured prompt tokens (min / median / max) | over "
        "`block_size` | statement head offset | statement cropped out of view | rate |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for cell in sweep["cells"]:
        measured = cell["measured_prompt_tokens"]
        rows.append(
            f"| {cell['target_tokens']} | {cell['pressure_label']} | "
            f"{measured['min']} / {measured['median']:g} / {measured['max']} | "
            f"{cell['n_over_block_size']} of {cell['proportion']['n_questions']} | "
            f"{cell['statement_head_offset']} | "
            f"{cell['n_statement_outside_window']} of {cell['proportion']['n_questions']} | "
            f"{cell['proportion']['formatted']} |"
        )
    return rows


def write_persistence_report(arm_records, comparison, replication, sweep, provenance_lines):
    """Write ``results/phase16_persistence_report.md`` — this phase's committed evidence.

    Section order is fixed and every framing string is a module-level constant committed before
    the run (the D-20 register Phase 14 established and 16-07 followed). The headline in
    ``## Verdict`` is ``phase16_ladder.licensed_headline``'s own output over the rungs the
    COMMITTED ladder recorded — never prose written here, and never more than that ladder licensed.
    """
    assert_persistence_report_not_clobbered()

    passed_rungs, recorded_branch = committed_ladder_rungs()
    licence = ladder.licensed_headline(passed_rungs)
    _prove(
        licence["branch"] == recorded_branch,
        f"licensed_headline returns branch {licence['branch']!r} over the rungs the committed "
        f"ladder recorded, but that ladder recorded {recorded_branch!r} — the licensing artifact "
        "and the function that reads it disagree, and the headline cannot be published from either",
    )
    floor = ladder.floor_in_both_units()
    gated = per_fact_by_arm(arm_records, tier=GATED_TIER)
    _prove(sweep and sweep.get("cells"), "the report was assembled without the PERS-03 sweep")

    blocks = [
        "# Phase 16 — Weight vs Prompt Persistence, Four Arms "
        "(PERS-02 / PERS-03 / PERS-04 / STAT-01 / STAT-02 / STAT-06)",
        "",
        "## Run Provenance",
        "",
        "One block per condition process. D-01 splits this run into FOUR fresh processes, so four "
        "distinct pids below are what EVIDENCE the split rather than assert it.",
    ]
    blocks += _provenance_blocks(arm_records)
    blocks += ["", "### Report assembly (this process)", ""]
    blocks += [f"- {line}" for line in provenance_lines]

    blocks += [
        "",
        "## What This Report Is",
        "",
        PERSISTENCE_REPORT_FRAMING,
        "",
        WALL_CLOCK_NOTE,
        "",
        "## Run Design",
        "",
        PROCESS_SPLIT_NOTE,
        "",
        SEQUENTIAL_QUESTIONS_JUSTIFICATION,
        "",
        NO_KV_CACHE_NOTE,
        "",
        f"**Condition order (D-03), pre-registered:** `{CONDITION_ORDER}`.",
        "",
        CONDITION_ORDER_RATIONALE,
        "",
        "## Arm Parity (SC2 / PERS-02)",
        "",
        "The four scalar columns are read off ONE `SHARED_ARM_CONFIG` object by identity, not "
        "compared as four literals that agree today; `assert_arm_parity` asserts that identity AND "
        "the equality of every column below before this report is assembled. `forbid_ids` is "
        "recorded by sha256 CONTENT hash because `undecodable_ids_mask` needs a loaded tokenizer "
        "and returns a device-resident tensor, so it can be neither an import-time constant nor "
        "meaningfully compared by identity across the four fresh processes D-01 requires.",
        "",
    ]
    blocks += _parity_rows(arm_records)

    blocks += [
        "",
        f"## Per-Fact Results — the gated tier (`{GATED_TIER}`)",
        "",
        "One row per fact per arm. Every rate carries BOTH denominators — questions (the STAT-01 "
        "unit) and draws (the raw count) — and a bound; a fact scoring nothing carries the "
        "rule-of-three ceiling as well, because a bare zero percentage states a certainty this "
        "sample does not have.",
        "",
        "| fact | arm | answerable / questions | draws | bound |",
        "| --- | --- | --- | --- | --- |",
    ]
    for fact_id in sorted(next(iter(gated.values()))):
        for condition in CONDITION_ORDER:
            aggregate = gated[condition][fact_id]
            row = _proportion_row(aggregate)
            ceiling = (
                f"rule of three {row['rule_of_three_upper']:.6f}"
                if "rule_of_three_upper" in row
                else f"rate {row['rate']:.6f}"
            )
            blocks.append(
                f"| `{fact_id}` | `{condition}` | {row['successes']} / {row['n_questions']} | "
                f"{aggregate['k']} of {row['n_draws']} | Wilson upper "
                f"{row['wilson_upper_95']:.6f}; {ceiling} |"
            )

    blocks += [
        "",
        "### Pooled per arm, with the phase's DESCRIPTIVE interval",
        "",
        f"`{BOOTSTRAP_METHOD}`, {BOOTSTRAP_RESAMPLES:,} resamples, seed {BOOTSTRAP_SEED}, "
        f"alpha {BOOTSTRAP_ALPHA}. Two stages: the 8 FACTS are resampled first, then that "
        "resampled fact's own QUESTIONS. A question-only bootstrap would be conditional on these "
        "exact 8 facts and therefore NARROWER than the fact-level sign test standing beside it — "
        "an interval claiming more than the gate it accompanies. The percentile method is biased "
        "and anti-conservative at small n, and n here is 8 facts; that is NAMED in the "
        "pre-registration rather than upgraded after the numbers landed.",
        "",
        "| arm | pooled rate | two-stage cluster bootstrap 95% | Wilson upper (see label below) |",
        "| --- | --- | --- | --- |",
    ]
    for condition in CONDITION_ORDER:
        pooled = _pooled(gated[condition])
        row = report_proportion(pooled["n_answerable"], pooled["n_questions"], pooled["n_draws"])
        low, high = cluster_bootstrap(
            {fact_id: entry["questions"] for fact_id, entry in gated[condition].items()}
        )
        blocks.append(
            f"| `{condition}` | {row['formatted']} | ({low:.6f}, {high:.6f}) | "
            f"{row['wilson_upper_95']:.6f} |"
        )
    blocks += ["", f"**Wilson label (T-16-41).** {WILSON_LABEL}", "", SOFT_TIER_EXCLUSION]

    step_alpha = HOLM_ALPHA / len(HOLM_FAMILY_PAIRS)
    blocks += [
        "",
        "## The Inferential Gate (STAT-06 / D-09)",
        "",
        GATE_FRAMING,
        "",
        f"Family size m = {len(HOLM_FAMILY_PAIRS)}; first-step alpha = {HOLM_ALPHA} / "
        f"{len(HOLM_FAMILY_PAIRS)} = {step_alpha:.7f}.",
        "",
        "| pair | declared alternative (D-29) | per-fact signs | exact p | alpha at step | "
        "rejected |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for pair, p, alpha_at_step, rejected in comparison["holm"]:
        signs = " ".join(f"{sign:+d}" for sign in comparison["signs"][pair])
        blocks.append(
            f"| `{pair[0]}` x `{pair[1]}` | {comparison['alternative'][pair]} | {signs} | "
            f"{p:.7f} | {alpha_at_step:.7f} | {'YES' if rejected else 'no'} |"
        )

    blocks += [
        "",
        "## Taught Replication — OUTSIDE the Holm family (D-07)",
        "",
        f"> {TAUGHT_TIER_STATUS}",
        "",
        "The same protocol on the taught tier, reported with NO alpha and NO rejection flags, "
        "because there is nothing here that may be read as a verdict. Gating both tiers would take "
        "the family from 6 to 12, alpha to 0.05/12, and 8/8 unanimity would then FAIL — the gate "
        "would be unclearable at every possible outcome.",
        "",
        "| pair | per-fact signs | exact p (descriptive) |",
        "| --- | --- | --- |",
    ]
    for pair in HOLM_FAMILY_PAIRS:
        signs = " ".join(f"{sign:+d}" for sign in replication["signs"][pair])
        blocks.append(
            f"| `{pair[0]}` x `{pair[1]}` | {signs} | {replication['p_values'][pair]:.7f} |"
        )

    blocks += [
        "",
        "## The Arm-D Structural Floor (D-25) — pre-registered qualifier, verbatim",
        "",
        f"> {arm_d_qualifier()}",
        "",
        ARM_D_FLOOR_RECONCILIATION,
        "",
        f"Operative chance floor: **{COSINE_CHANCE_FLOOR}** = 1 / {COSINE_POOL_SIZE}, `_prove`d "
        "against the committed lexicon at every call of `candidate_pool()`.",
        "",
        "## Context Pressure (PERS-03)",
        "",
        "| arm | treatment | reason |",
        "| --- | --- | --- |",
    ]
    for condition, entry in sweep["applicability"].items():
        blocks.append(f"| `{condition}` | **{entry['treatment']}** | {entry['reason']} |")

    blocks += [
        "",
        "### The arm-B cells",
        "",
        "ONE ordered dilution axis. Truncation is DERIVED from crossing `block_size` "
        f"({sweep['block_size']}) and is never an independent knob (D-27): the recall prompt is "
        f"{SWEEP_NOMINAL_BARE_PROMPT} tokens bare and {sweep['targets'][0]} with a "
        f"{SWEEP_NOMINAL_PERSONA_SPAN}-token persona span, so truncation cannot fire until "
        "dilution has already pushed the context past the window. A separately-built truncation "
        "cell would be the largest dilution cell under a second name, and this report would state "
        "one effect twice. The seventh row is the adversarial overwrite on its OWN axis at nominal "
        "length — six on-axis cells plus one off-axis cell, which is why the log shows seven runs.",
        "",
        "Prompt lengths are printed as DISTRIBUTIONS, never as their target: the fixture's own "
        "questions run 14 / 28 / 63 tokens bare (min / median / max), so a cell's achieved length "
        "varies by question even at a fixed persona span.",
        "",
    ]
    blocks += _sweep_rows(sweep)
    blocks += [
        "",
        SWEEP_NO_BASELINE_CAVEAT,
        "",
        ASSERT_VALUE_IN_PROMPT_CAVEAT,
        "",
        "**All dilution is INSIDE the persona span, and there is no turns axis.** "
        "`build_recall_prompt` (`src/personacore/dialogue/serialize.py:92`) passes exactly ONE "
        "turn to `encode_dialogue`, and `PERSONA_CAP` is enforced only by `cap_persona` (`:115`), "
        "which `build_recall_prompt` never calls — so the cap does not bite on this route and the "
        "persona span reaches the largest cell's length directly. SC5 and PERS-03 were amended at "
        "`79fa01a` from 'dilution across turns' to 'dilution within the persona span' for exactly "
        "this reason; there is no turns axis for this run to be missing.",
        "",
        ADVERSARIAL_OVERWRITE_NOTE,
        "",
        "### Arm A — a PROOF, cited and not re-measured",
        "",
        sweep["applicability"]["adapter-only"]["reason"],
        "",
        "### Monotone degradation (D-28)",
        "",
        (
            MONOTONE_CLAIM_LICENSED
            if monotone_claim_allowed(licence["branch"])
            else MONOTONE_CLAIM_REFUSED
        ).format(branch=licence["branch"], statement=licence["statement"]),
        "",
        "## The Floor in Both Units (STAT-01 / T-16-26)",
        "",
        FLOOR_UNITS_NOTE,
        "",
        f"Source: `{floor['source']}`.",
        "",
        "| unit | count | rate | one-sided 95% Wilson upper |",
        "| --- | --- | --- | --- |",
        f"| {floor['draws']['label']} | {floor['draws']['successes']} of {floor['draws']['n']} | "
        f"{floor['draws']['rate']:.6f} | {floor['draws']['wilson_upper_95']:.6f} |",
        f"| {floor['questions']['label']} | {floor['questions']['successes']} of "
        f"{floor['questions']['n']} | {floor['questions']['rate']:.6f} | "
        f"{floor['questions']['wilson_upper_95']:.6f} |",
        "",
        f"Rule-of-three ceiling at {floor['questions']['n']} questions had the floor scored "
        f"nothing at all: {floor['rule_of_three_upper']:.6f}.",
        "",
        "## Verdict",
        "",
        f"**Ladder branch: `{licence['branch']}`** — highest passed rung: "
        f"`{licence['highest_passed']}`. Read from `results/phase16_ladder_report.md`, committed "
        f"at `{ladder_report_commit()}` BEFORE any arm of this comparison was scored (PERS-01 / "
        "PREREG-02), and rendered here as `licensed_headline()`'s own output rather than as prose "
        "written around this run's numbers.",
        "",
        licence["statement"],
        "",
        LADDER_PROXY_DEGENERATE_CAVEAT,
        "",
        # D-30: emitted beside the headline, never left to the reader to remember.
        HEADLINE_MECHANISM_CAVEAT,
        "",
        "### The pre-registered gate outcome, as-written",
        "",
    ]
    rejected = [entry for entry in comparison["holm"] if entry[3]]
    if rejected:
        blocks += [
            f"{len(rejected)} of {len(HOLM_FAMILY_PAIRS)} pairs cleared their Holm step:",
            "",
        ]
        blocks += [
            f"- `{pair[0]}` x `{pair[1]}` — {comparison['alternative'][pair]}; p = {p:.7f} < "
            f"alpha {alpha_at_step:.7f}"
            for pair, p, alpha_at_step, _ in rejected
        ]
    else:
        blocks.append(NOT_DEMONSTRABLE)
    blocks.append("")

    text = "\n".join(blocks)
    _prove(
        VERDICT_SECTION.search(text) is not None,
        "the rendered report carries no `## Verdict` section the clobber guard could anchor on, "
        "so a later run would overwrite this phase's committed evidence in silence",
    )
    _prove(
        re.search(r"\b0(\.0+)?%", text) is None,
        "the rendered report contains a bare zero percentage — STAT-02 forbids it in any "
        "committed report or figure, because a bare zero states a certainty the sample does not "
        "have. Every zero renders as its numerator over its denominator with a bound attached",
    )
    PERSISTENCE_REPORT_PATH.write_text(text, encoding="utf-8")
    print(f"[phase16_persistence] wrote {PERSISTENCE_REPORT_PATH}")
    return text


# =============================================================================================
# ===== main() — ONE condition per invocation, and no way to run two (D-01 / T-16-46) =========
# =============================================================================================

ARM_RECORD_DIR = _REPO_ROOT / "results"

_USAGE = (
    "usage: python scripts/phase16_persistence.py (--condition NAME | --report)\n"
    "\n"
    "  --condition NAME   run EXACTLY ONE arm and write results/phase16_arm_NAME.json.\n"
    "                     NAME must be one of the pre-registered conditions.\n"
    "  --report           assemble results/phase16_persistence_report.md from the four arm\n"
    "                     records already on disk.\n"
    "\n"
    "There is deliberately NO mode that runs more than one condition. D-01 requires four fresh\n"
    "processes, one per arm, and the only structural way to guarantee that is to make a single\n"
    "process incapable of running two. A convenience flag would turn the process split from a\n"
    "PROPERTY of this driver into a convention an operator is trusted to follow."
)


def build_parser():
    """The argument surface, as a spec a test can read: two mutually exclusive modes, no third.

    ``--condition`` is constrained to ``CONDITION_ORDER`` by argparse itself, so an unrecognized
    arm exits non-zero with the four legal names printed rather than reaching a dispatch that
    would have to invent a refusal. Exactly one of the two modes is REQUIRED: an argumentless
    invocation must not fall through to "run something reasonable" when the reasonable thing is a
    multi-hour generation run.
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="phase16_persistence.py",
        description="Phase 16 four-arm weight-vs-prompt comparison — ONE condition per process.",
        epilog=_USAGE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--condition",
        choices=CONDITION_ORDER,
        help="the single pre-registered arm this process runs",
    )
    mode.add_argument(
        "--report",
        action="store_true",
        help="assemble the report from the four arm records on disk",
    )
    return parser


def arm_record_path(condition):
    """Where one arm's raw record lands. Read from the module global so tests can redirect it."""
    _prove(
        condition in CONDITION_ORDER,
        f"condition {condition!r} is not one of the pre-registered {CONDITION_ORDER}",
    )
    return ARM_RECORD_DIR / f"phase16_arm_{condition}.json"


def serializable_config(config):
    """The parity columns in a JSON-safe shape, DERIVED from ``PARITY_COLUMNS``.

    ``shared_arm_config`` is deliberately dropped: object identity is an IN-PROCESS property and
    cannot survive a file, so writing it would record something that means nothing on the other
    side. ``--report`` re-establishes it through
    ``assert_recorded_config_matches_the_shared_object``, and only after proving every recorded
    column equals the live object's own field.
    """
    row = {column: config[column] for column in PARITY_COLUMNS}
    row["stop_ids"] = sorted(config["stop_ids"])
    return row


def assert_recorded_config_matches_the_shared_object(condition, recorded):
    """Prove a JSON-loaded config equals ``SHARED_ARM_CONFIG``, then restore what JSON dropped.

    The four scalar columns are compared against the live object's OWN fields — not against four
    literals — so a record written by a process holding a different config aborts here rather than
    being silently rehydrated into agreement. What ``assert_arm_parity`` then adds on top is the
    genuinely cross-process check this cannot make: that all four arms recorded the SAME
    ``forbid_ids`` content hash, which no single record can attest to on its own.
    """
    for column, expected in (
        ("max_new_tokens", SHARED_ARM_CONFIG.max_new_tokens),
        ("context_length", SHARED_ARM_CONFIG.context_length),
        ("n_draws", SHARED_ARM_CONFIG.n_draws),
    ):
        _prove(
            recorded[column] == expected,
            f"arm {condition!r} recorded {column} = {recorded[column]!r} but SHARED_ARM_CONFIG "
            f"holds {expected!r} — that arm ran under a different generation budget from the one "
            "this report would publish for it, and the difference is invisible in its rate",
        )
    _prove(
        sorted(recorded["stop_ids"]) == sorted(SHARED_ARM_CONFIG.stop_ids),
        f"arm {condition!r} recorded stop_ids {recorded['stop_ids']} against "
        f"{sorted(SHARED_ARM_CONFIG.stop_ids)} — the arms stopped on different tokens",
    )
    return {
        **recorded,
        "stop_ids": SHARED_ARM_CONFIG.stop_ids,
        "shared_arm_config": SHARED_ARM_CONFIG,
    }


def assert_arms_are_pairable(arm_records):
    """PERS-02's pairing claim, checked rather than assumed: same code, same questions, same seeds.

    Three proofs, and each closes a different way four processes can stop being one comparison:

    * **One ``git_sha`` across all four.** Four processes, ONE codebase. A mismatch means the code
      changed mid-run and the arms are not comparable — and the report would publish them as if
      they were.
    * **Four DISTINCT pids.** D-01's split, evidenced. One pid appearing twice means two arms
      shared a process, which is the single boundary this comparison is about.
    * **Identical ``(fact_id, split, seed_index)`` sets.** PERS-02 claims the arms are PAIRED by
      ``seed_index``; asserting it here is what makes the claim checkable. The TRIPLE rather than
      the bare index, because every arm's bare index set is 0..n-1 and would match trivially while
      the questions behind it differed.
    """
    _prove(
        sorted(record["condition"] for record in arm_records) == sorted(CONDITION_ORDER),
        f"the report was handed {sorted(r['condition'] for r in arm_records)} but the "
        f"pre-registration commits {sorted(CONDITION_ORDER)} — a missing arm cannot be found by "
        "comparing the ones that are present",
    )
    shas = {record["git_sha"] for record in arm_records}
    _prove(
        len(shas) == 1,
        f"the four arms recorded {len(shas)} different git SHAs ({sorted(shas)}) — the code "
        "changed mid-run, so the arms did not run the same instrument and their comparison is not "
        "a comparison of arms",
    )
    pids = {record["pid"] for record in arm_records}
    _prove(
        len(pids) == len(CONDITION_ORDER),
        f"the four arm records carry {len(pids)} distinct pid(s) ({sorted(pids)}) — D-01 requires "
        "four FRESH processes, and two arms sharing one process crossed the exact boundary this "
        "comparison exists to isolate",
    )
    keyed = {
        record["condition"]: {
            (entry["fact_id"], entry["split"], entry["seed_index"])
            for entries in record["by_split"].values()
            for entry in entries
        }
        for record in arm_records
    }
    reference = keyed[CONDITION_ORDER[0]]
    for condition in CONDITION_ORDER[1:]:
        _prove(
            keyed[condition] == reference,
            f"arm {condition!r} scored a different (fact, split, seed_index) set from "
            f"{CONDITION_ORDER[0]!r}: {len(keyed[condition] ^ reference)} entries differ, e.g. "
            f"{sorted(keyed[condition] ^ reference)[:3]}. PERS-02's whole claim is that the arms "
            "score the SAME questions under the SAME seeds, so an unpaired arm would report a "
            "paired number",
        )


def run_one_condition(condition):
    """ONE arm, in this process, start to finish — and this process can run no other.

    Order is not incidental: the clobber guard runs BEFORE anything expensive, because a run that
    refuses to write its report at the end has already been wasted. The report is NOT written here
    — it is assembled from all four records by ``--report``, which is what makes the four-process
    split a precondition of publishing rather than a claim made inside one process.
    """
    import os
    import time

    import torch

    from personacore.config import RuntimeConfig
    from personacore.preflight import preflight_device
    from personacore.provenance import git_sha
    from personacore.seeding import seed_everything

    started = time.time()
    assert_persistence_report_not_clobbered()
    summary = preflight_device(strict=True)
    print(f"[phase16_persistence] preflight: {summary}")
    device = RuntimeConfig().device
    # ONE seed constant in play, the instrument's own: `draw_all` derives every per-draw generator
    # from `phase14_recall.question_seed`, so a fresh literal here would drift from the one that
    # actually drives the draws.
    seed_everything(recall.SEED)

    model, model_cfg, tok, forbid, artifact = recall.load_adapted_model(device)
    # 16-08's recorded gap, closed HERE because this is where the loaded config is finally in
    # scope. `ArmConfig.context_length` reads `ModelConfig.block_size` — the DATACLASS DEFAULT —
    # while the run loads its config from `convbase_slim.pt`. They agree today. If a future
    # checkpoint ever changed it, `assert_arm_parity` would still pass (all four arms read the
    # same default) while the published `context_length` column disagreed with the model that
    # actually generated every number under it.
    _prove(
        model_cfg.block_size == SHARED_ARM_CONFIG.context_length,
        f"the loaded checkpoint's block_size is {model_cfg.block_size} but the pre-registered "
        f"parity column is {SHARED_ARM_CONFIG.context_length} (ModelConfig's default) — the SC2 "
        "column would describe a context length this model does not have, and every rate "
        "published under it would have been produced at the other one",
    )
    # `resolve_forbid` is 16-08's declared auditable seam; `load_adapted_model` builds its own
    # mask the same way (`phase14_recall.py:568`). The LOADER's object is the one threaded into
    # every arm — structural parity with the committed instrument, unchanged — and the seam is
    # used to PROVE the published hash describes that object rather than a different mask.
    _, seam_digest = resolve_forbid(tok, model_cfg.vocab_size)
    _prove(
        forbid_digest(forbid) == seam_digest,
        "the mask the loader threaded into the arms does not match `resolve_forbid`'s — the "
        "forbid_ids hash this report publishes would describe a mask no arm actually generated "
        "under",
    )

    items_by_tier = load_fixture_items()
    record = run_condition(condition, model, tok, device, forbid, items_by_tier)
    sweep = None
    if condition == "prompt-stuffed":
        # D-26 — the sweep runs on arm B and nowhere else. Arm A receives a cited PROOF; arms C
        # and D are declared not applicable, each with its own stated reason.
        sweep = run_sweep(
            model, tok, device, forbid, all_items(items_by_tier), fairness_statements()
        )

    wall = time.time() - started
    provenance = recall.echo_provenance(summary, device, artifact) + [
        f"torch: {torch.__version__}",
        f"condition: {condition} (ONE per process — D-01)",
        f"condition wall clock: {wall / 60:.1f} min",
    ]
    payload = {
        "condition": condition,
        "git_sha": git_sha(),
        "pid": os.getpid(),
        "device": str(device),
        "wall_clock_min": wall / 60,
        "provenance": provenance,
        "config": serializable_config(record["config"]),
        "forbid_ids_masked": int(forbid.sum().item()),
        "vocab_size": model_cfg.vocab_size,
        "by_split": record["by_split"],
        "sweep": sweep,
    }
    path = arm_record_path(condition)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"[phase16_persistence] wrote {path} in {wall / 60:.1f} min")
    return payload


def run_report_mode():
    """Assemble the report from the four arm records — refusing arms that are not one comparison.

    Every refusal here is cheaper than a published number that should not have been published:
    a missing arm, a code change mid-run, two arms in one process, an unpaired question set, or a
    parity column that stopped agreeing. ``assert_arm_parity`` is CALLED here — 16-08 committed it
    and 16-09 recorded that nothing called it yet, so this is the wiring that turns it from a
    definition into a check.
    """
    arm_records = []
    for condition in CONDITION_ORDER:
        path = arm_record_path(condition)
        _prove(
            path.exists(),
            f"{path} is missing — the report assembles from all FOUR arm records or from none. "
            f"Run `--condition {condition}` in its own fresh process first",
        )
        record = json.loads(path.read_text(encoding="utf-8"))
        _prove(
            record["condition"] == condition,
            f"{path} carries condition {record['condition']!r} — an arm record filed under "
            "another arm's name would be published under the name it was filed as",
        )
        record["config"] = assert_recorded_config_matches_the_shared_object(
            condition, record["config"]
        )
        arm_records.append(record)

    assert_arms_are_pairable(arm_records)
    assert_arm_parity(arm_records)

    gated = per_fact_by_arm(arm_records, tier=GATED_TIER)
    taught = per_fact_by_arm(arm_records, tier=REPLICATION_TIER)
    sweeps = [record["sweep"] for record in arm_records if record.get("sweep")]
    _prove(
        len(sweeps) == 1,
        f"{len(sweeps)} arm record(s) carry a context-pressure sweep — D-26 runs it on the "
        "prompt-stuffed arm and on no other, so any count but one means the sweep was run "
        "somewhere its result cannot be interpreted",
    )
    return write_persistence_report(
        arm_records,
        compare_arms(gated, tier=GATED_TIER),
        taught_replication(taught),
        sweeps[0],
        [
            f"report assembled from {len(arm_records)} arm records at {ARM_RECORD_DIR}",
            f"arm git SHA (identical across all four): {arm_records[0]['git_sha']}",
            f"arm pids: {sorted(record['pid'] for record in arm_records)}",
        ],
    )


def main():
    """Dispatch. ONE condition per invocation, or the report — and nothing that runs two arms."""
    args = build_parser().parse_args()
    if args.report:
        run_report_mode()
    else:
        run_one_condition(args.condition)


if __name__ == "__main__":
    main()
