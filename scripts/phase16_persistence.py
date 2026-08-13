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
import sys
from typing import NamedTuple

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# `scripts/` is sys.path[0] only when a script in it is run DIRECTLY; an importlib-loaded test
# harness gets no such entry (phase16_ladder.py:36-40 precedent). Insert it explicitly so both
# paths reach the sibling instrument.
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import phase14_recall as recall  # noqa: E402  (needs the sys.path insert above)

from personacore.config import ModelConfig  # noqa: E402

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
