"""Phase 19 selective memory erasure — THE PRE-REGISTRATION (ERASE-01, STAT-05).

ORDERING CONTRACT
=================
Read this before editing anything below it.

**1. This file IS the Phase 19 pre-registration, and every commit touching it must be an ANCESTOR
of the first-add commit of every ``results/phase19_*`` artifact.** Every commit, not merely the
first: a pin asserting only "the file existed before the number" still permits the manoeuvre it
exists to forbid — rewriting a rule once the number it judges is visible.
``tests/test_phase16_prereg.py::test_phase19_prereg_is_frozen_before_every_phase19_result`` asks
git's object graph, never a committer date, for the same reason its Phase 17 and Phase 18 twins do:
a committer date is rewritable by anyone with a shell, non-monotonic after a rebase, and skewed
across machines. Ancestry is a property of the DAG, and making ``git merge-base --is-ancestor`` lie
requires rewriting every object between the two commits, which changes both SHAs.

**2. NO ``results/phase19_*`` artifact may be committed until the pin is COMPLETE at plan 19-07.**
The pin lands across plans 19-01..19-06 — the mechanism (here), the target fact and the denominator,
the blind-calibration floor and its reachability proof, the estimators, the arm runners and the
report text — and 19-07 audits the finished article. A Phase 19 number committed before then is a
number whose own rule was still being written. That ordering IS the scientific guarantee of this
phase; it is not bookkeeping, and no plan may trade it away for convenience.

**3. After 19-07 this file is permanently uneditable.** ``scripts/phase17_personas.py`` reached that
state at ``d549e0b`` and ``scripts/phase18_extraction.py`` at ``99716e0`` — in both cases the moment
the phase's first result artifact was committed. The recovery path for a genuine defect discovered
afterwards is a DATED CONTINUATION published beside the original text (``scripts/_addendum.py``,
decision D3), never an edit and never a ``--force`` flag. Editing a recorded rule after its number
exists destroys the only thing that made the rule worth recording.

WHAT THIS FILE HOLDS AT PLAN 19-02, AND WHAT IT DELIBERATELY DOES NOT
--------------------------------------------------------------------
Holds: the ordering contract above, the mechanism identity and its rule, the DERIVED component
index, the ablation operator (19-01), and the target-selection rule with its two tie-breaks, the
published eight-fact ranking and the derived (a) denominator (19-02). The calibrated floor, the
noise-floor estimators, the arm runners and the report text are plans 19-03..19-06, and writing
any of them here early would mean fixing them before the plan that reasons about them.

NO FACT VALUE MAY ENTER THIS FILE, IN ANY STRING, DOCSTRINGS INCLUDED. Every core ``fact_id`` ends
in its own locked value (``scripts/phase17_personas.py:61``, ``scripts/phase17_isolation.py:128``),
so the target and the ranking below are keyed by SLOT and never by ``fact_id`` — a fact-id-keyed
ranking would put all eight answers into the pre-registration's source. ``fact_id`` reaches this
module only as data at call time, and ``values`` reaches ``score_records`` as a PARAMETER
(``phase18_extraction.py:1919``). ``tests/test_phase19_erasure.py`` scans this file for all ten.

Success criteria are INHERITED from ``scripts/erasure_gate.py`` (committed ``23a830c``, 2026-08-12
16:27:43 -0300, before Phase 16 ran) and are never re-authored here. That file fixed the BAR and
deliberately fixed no design; this file commits the DESIGN it left open, and touches no bar.

Nothing executes at import beyond the ``sys.path`` bootstrap below and the PURE derived-census
proofs (the component census, and the two-source denominator cross-check). No file is read at
import and no artifact is loaded: ``scripts/phase18_extraction.py`` holds the same discipline, and
a pin that could not be imported without its inputs on disk would be a pin whose rules stop being
quotable the moment a path moves. CPU-only, GPU-free, no checkpoint read, no network.
"""

import pathlib
import sys

from personacore.lora import LoRAConfig

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# `scripts/` is sys.path[0] only when a script in it is run DIRECTLY; an importlib-loaded test
# harness gets no such entry (phase18_extraction.py:41-46 precedent). Insert it explicitly so the
# sibling driver below is reachable from both paths. This is the ONE module-level side effect this
# file is permitted.
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

# The 36-key (layer, projection, state_dict_key) enumeration is IMPORTED, never re-derived. It is
# already a committed explicit product over `TARGET_PROJECTIONS` x `N_LAYER` with the "never an
# isinstance scan" discipline recorded on it (extract_deltas.py:94-102), and a second copy of an
# enumeration is a copy free to stop agreeing with the first.
import extract_deltas  # noqa: E402  (needs the sys.path insert above)


def _prove(condition, message):
    """Loud proof: ``SystemExit`` naming the violated contract (never an ``-O``-strippable one).

    Same register and same reason as ``phase14_recall._prove`` (``:221-224``),
    ``phase16_persistence._prove``, ``phase17_isolation._prove`` and
    ``phase18_extraction._prove`` (``:56``), with this module's own prefix — an abort naming the
    wrong driver sends its reader to the wrong file.
    """
    if not condition:
        raise SystemExit(f"[phase19_erasure] PROOF FAILED: {message}")


# =============================================================================================
# ===== THE MECHANISM — pinned here, before the blind calibration runs =====
# =============================================================================================

MECHANISM_ID = "M1-rank1-component-ablation"

MECHANISM_RULE = (
    "PRIMARY MECHANISM (M1, id 'M1-rank1-component-ablation'): erasure is performed by ZEROING "
    "rank-1 components of the LoRA delta. `LoRALinear.forward` computes `y = base(x) + scale * (x "
    "@ A^T @ B^T)` (layer.py:38-42), i.e. `dW = scale * (B @ A)` with `B: (out, r)` and `A: (r, "
    "in)`, which is exactly the sum over j of `scale * outer(B[:, j], A[j, :])` — r rank-1 outer "
    "products per wrapped projection. The surgery surface is therefore the address `(layer, "
    "projection, j)`, and its size is DERIVED from the committed wrap set and the committed rank "
    "(see `component_index`), never typed. Ablating a component means zeroing BOTH `B[:, j]` and "
    "`A[j, :]`.",
    "WHY M1 AND NOT SOMETHING STRONGER: staying inside the rank-r decomposition is what keeps the "
    "erased model exactly representable in the SHIPPED artifact format. The erased adapter has the "
    "same keys, the same shapes, the same dtypes and the same `lora_config`, so it round-trips "
    "through `export_adapter`/`load_adapter` and passes `load_adapter_weights`' key, shape AND "
    "scale audits (inject.py:76-131) with none of them relaxed. It also leaves the adapter-off "
    "bit-identity control untouched: with the adapter disabled the wrapper's forward is literally "
    "`self.base(x)`, so an operator that only rewrites `lora_A`/`lora_B` cannot move the "
    "adapter-off logits at all (`run_bit_identity_control`, phase14_recall.py:1480). A mechanism "
    "that edited base weights would have to re-earn both properties.",
    "REFERENCE ARM (M2, ERASE-02): retrain the adapter from the same base under the same recipe on "
    "the taught fact set MINUS the target — the 'never learned it' arm. It is a REFERENCE, not a "
    "second erasure mechanism: it answers 'what would the weights look like if this fact had never "
    "been taught', which is the only honest comparison for an erasure claim at this scale. It is "
    "not a fallback M1 may be replaced by.",
    "DECLINED, NOT DEFERRED (D1): M3 (retain-set continued fine-tuning), M4 (Fisher-anchored "
    "damping), M5 (task-arithmetic negation) and M6 (gradient ascent) are OUT of this phase. They "
    "are not scheduled elsewhere and are not being kept in reserve. The M1/M2 pair answers the "
    "phase's central question, and a third arm is unguaranteed scope. Recording this as a decline "
    "rather than a deferral matters: a deferred mechanism is one a disappointing result can "
    "reach for.",
    "THE MECHANISM AND ITS PARAMETERS ARE PINNED BEFORE THE BLIND CALIBRATION RUNS (D1). A "
    "mechanism chosen or swapped after a disappointing floor is not a pre-registered mechanism, in "
    "exactly the sense a threshold chosen after seeing the data is not a threshold. The stopping "
    "rule that decides HOW MUCH to ablate is pinned in the same file before any calibration or "
    "erasure executes; this clause is what forbids it becoming a knob afterwards.",
)

# =============================================================================================
# ===== THE COMPONENT INDEX AND THE ABLATION OPERATOR =====
# =============================================================================================

# The committed production rank, READ from the dataclass default rather than retyped
# (lora/config.py:23 — "r=8, 331,776 trainable params at production shape"). `alpha` is not read
# here on purpose: this module never recomputes `alpha / r`. `LoRALinear.scale` is the single
# source of truth for it (layer.py:27, PITFALLS P3) and the ablation operator never touches it.
PRODUCTION_RANK = LoRAConfig().r

# (layer, projection) -> the adapter-artifact key prefix. The `.weight` suffix is stripped exactly
# as `extract_deltas.adapter_cells` does it (:183) — injection rewrites a wrapped projection's
# state-dict keys with a `.base.` infix, so the projection's own prefix is what carries `lora_A`
# and `lora_B`.
_COMPONENT_PREFIX = {
    (layer, projection): key[: -len(".weight")] for layer, projection, key in extract_deltas.KEYS
}


def component_index():
    """Every addressable rank-1 component of the adapter delta, as ``(layer, projection, j)``.

    DERIVED, never typed. The count is the product of two quantities this repository already
    committed: the 36-key wrap enumeration (``extract_deltas.KEYS``, itself an explicit product of
    ``N_LAYER`` and the six ``TARGET_PROJECTIONS``) and the production rank
    (``LoRAConfig().r``). Writing the product as a literal would let the base grow a layer, or the
    rank move, while a stale constant kept the sweep quietly scanning the wrong surface — the
    "declared invariant silently becomes false" defect this project names as its most recurring.

    Ordered ``(layer, projection, j)`` with ``j`` innermost, following the committed ``KEYS``
    order, so the index is a stable, total ordering that a later tie-break can address by position.
    """
    index = [
        (layer, projection, j)
        for layer, projection, _key in extract_deltas.KEYS
        for j in range(PRODUCTION_RANK)
    ]
    _prove(
        len(index) == len(extract_deltas.KEYS) * PRODUCTION_RANK,
        f"component index holds {len(index)} addresses but the committed wrap set is "
        f"{len(extract_deltas.KEYS)} projections at rank {PRODUCTION_RANK}, i.e. "
        f"{len(extract_deltas.KEYS) * PRODUCTION_RANK} rank-1 components — the surgery surface "
        "and the artifact it addresses disagree",
    )
    _prove(
        len(set(index)) == len(index),
        "component index holds duplicate addresses — a component counted twice would make the "
        "ablation prefix length k a lie about how much of the delta was removed",
    )
    return index


# Module-scope census: running the derivation at import is what makes the proofs above fire on any
# import of this pin, not only when something happens to call the function.
N_COMPONENTS = len(component_index())


def ablate_components(adapter, components):
    """M1: zero the addressed rank-1 components. Returns a NEW artifact; mutates nothing.

    ``adapter`` is an ``export_adapter``-shaped artifact (``checkpoint.py:196``) — ``adapter`` /
    ``lora_config`` / ``base_fingerprint`` — and NOT the bare tensor dict, because the artifact is
    the object the audits read. ``load_adapter_weights``' scale audit reads
    ``artifact["lora_config"]`` (``inject.py:119-129``), so an operator taking only the tensors
    could not be round-tripped through the audit it has to survive, and a caller re-wrapping the
    tensors by hand each time would be re-declaring ``lora_config`` on every one of the sweep's
    applies. Taking the artifact means every application re-passes the scale audit for free.

    ``scale`` is neither recomputed nor touched here (PITFALLS P3): ``lora_config`` passes through
    by reference, unmodified, so ``alpha`` and ``r`` are byte-identical in the returned artifact.

    BOTH factors are zeroed, never one. The component's contribution is
    ``scale * outer(B[:, j], A[j, :])``; zeroing only ``B[:, j]`` already sends that outer product
    to zero for the CURRENT weights, but it leaves ``A[j, :]`` carrying live values that any later
    write to ``B`` would resurrect, and it makes the erased artifact's own arithmetic depend on
    which half was cleared. Zeroing both makes the component's absence a property of the file.

    The input artifact is never mutated: every tensor is ``detach().clone()``d (the
    ``snapshot_params`` idiom, ``inject.py:64``), so the caller's PRE-erasure adapter survives for
    the paired delta the (b) condition needs.
    """
    _prove(
        "adapter" in adapter and "lora_config" in adapter,
        f"ablate_components expects an export_adapter-shaped artifact with 'adapter' and "
        f"'lora_config' keys; got keys {sorted(adapter)} — a bare lora_ tensor dict cannot carry "
        "the scale the load audit reads",
    )
    rank = adapter["lora_config"]["r"]
    out = dict(adapter)
    out["adapter"] = {k: v.detach().clone() for k, v in adapter["adapter"].items()}

    seen = set()
    for address in components:
        layer, projection, j = address
        _prove(
            address not in seen,
            f"component {address} addressed twice — a duplicate is silently idempotent, which "
            "would make the reported number of ablated components larger than the number of "
            "components actually removed",
        )
        seen.add(address)
        prefix = _COMPONENT_PREFIX.get((layer, projection))
        _prove(
            prefix is not None,
            f"({layer}, {projection}) is not a wrapped projection — the committed wrap set is "
            f"{sorted(_COMPONENT_PREFIX)}",
        )
        _prove(
            0 <= j < rank,
            f"component index j={j} is outside [0, {rank}) for an artifact trained at "
            f"r={rank} — this address does not exist in the artifact being ablated",
        )
        keys = (f"{prefix}.lora_A", f"{prefix}.lora_B")
        missing = [key for key in keys if key not in out["adapter"]]
        _prove(
            not missing,
            f"adapter artifact is missing {missing} for ({layer}, {projection}) — it does not "
            "describe the committed wrap set; refusing to ablate a key set it does not have",
        )
        out["adapter"][keys[1]][:, j] = 0.0  # B[:, j]
        out["adapter"][keys[0]][j, :] = 0.0  # A[j, :]

    return out


# =============================================================================================
# ===== THE TARGET FACT — pinned BEFORE any calibration and before any erasure runs (D7) =====
# =============================================================================================

TARGET_SELECTION_RULE = (
    "THE TARGET is the core gated fact with the HIGHEST QUESTION-UNIT recall measured by Phase "
    "18's BEST attack family on the `core_held_out` tier of the `adapter-on` arm, at the budget "
    "that arm record itself declares (K = 48 on the committed run), read off "
    "`results/phase18_arm_adapter-on.json`. The attack family is NOT named here as a literal: it "
    "is selected by CALLING `phase18_extraction.best_attack_family`, whose `BEST_ATTACK_RULE` was "
    "committed inside Phase 18's own ancestry-pinned file before any rate existed; on this record "
    "it returns A2. The unit is the QUESTION and never the draw (`erasure_gate`'s THE CLUSTERING "
    "PROBLEM): a draw count divides the same numerator by K times the denominator, so a target "
    "chosen on draw rates would be chosen on a statistic this project has already ruled out.",
    "WHY A RULE OVER ALREADY-COMMITTED DATA IS STILL A PRE-REGISTRATION (D7). Every input above "
    "was committed on 2026-08-17, BEFORE this rule was written — `results/phase18_arm_adapter-on"
    ".json` first appears at `9a923d6`. That ordering looks backwards for a pre-registration and "
    "is the honest form of it here: the rule cannot change what the data says, because the data "
    "is the KNOWN PAST and cannot move, and the ranking below is published in full so a reader "
    "checks the choice instead of trusting it. What the ordering still buys is the part that can "
    "be gamed — the target is fixed BEFORE the blind calibration floor exists and BEFORE any "
    "erasure is attempted, so the fact under test cannot be the fact that turned out to be "
    "easiest to erase.",
    "TIE-BREAK 1, for ties on the rate: the LOWEST published `ans1`/mean value-span NLL in the "
    "SAME arm record's exposure block — MOST EXPOSED WINS. The direction is deliberate and is the "
    "conservative one: a lower teacher-forced NLL on the taught value means the adapter holds "
    "that value more tightly, so it is the HARDEST fact to erase and therefore the honest target. "
    "Breaking the other way would let the phase pick, from among facts the attacker extracts "
    "equally well, the one the weights hold most loosely. The reduction is not re-chosen here "
    "either: `ans1`/mean is the pair each exposure entry itself declares `admissible` (D-29), and "
    "an entry declaring anything else is refused rather than reinterpreted. The exposure `rank` "
    "cannot serve as this tie-break — all eight slots are at rank 1, the ceiling, on this record.",
    "TIE-BREAK 2, for ties on BOTH the rate and the exposure NLL: the lexicographically smallest "
    "`fact_id`. It resolves any remaining tie of any arity, so the rule is TOTAL — there is no "
    "outcome in which it returns a set and someone has to pick from it. `fact_id` is used here as "
    "a sort key and is never published by this module (see the file docstring's no-fact-value "
    "rule); the ranking is keyed by slot.",
    "FORBIDDEN, and this clause is the reason both tie-breaks are in the SAME COMMIT as the rule "
    "they break: choosing the target, or changing it, after seeing a calibration result, an "
    "ablation sweep, or any post-erasure number. A tie-break written once the ranking is visible "
    "is a choice wearing a rule's clothes — and on the committed record the tie-break is LOAD-"
    "BEARING rather than decorative, because several slots sit at the ceiling and the primary "
    "criterion alone returns a set. This rule was committed before the calibration adapter "
    "existed and before `results/phase19_*` held a single file.",
)

TARGET_RANKING_FIELDS = ("slot", "successes", "n_questions", "rate", "exposure_ans1_mean_nll")


def _exposure_nll(exposure):
    """``{slot: ans1/mean}`` — the ONE reduction the arm record itself marks ``admissible``.

    D-29 published six frame x reduction NLLs and marked exactly one pair admissible. Re-picking a
    pair here would be a second selection rule for the same quantity, free to stop agreeing with
    the one Phase 18 committed, so this reads the record's own declaration and refuses a record
    that declares something else rather than quietly reinterpreting it.
    """
    nll = {}
    for entry in exposure:
        _prove(
            "slot" in entry and "nll" in entry and "admissible" in entry,
            f"an exposure entry is missing slot/nll/admissible; it carries {sorted(entry)} — this "
            "is not the exposure block `phase18_extraction` writes",
        )
        _prove(
            entry["slot"] not in nll,
            f"the exposure block carries two entries for slot {entry['slot']!r}; the tie-break "
            "would then read whichever one happened to be last",
        )
        frame, reduction = tuple(entry["admissible"])
        _prove(
            (frame, reduction) == ("ans1", "mean"),
            f"slot {entry['slot']!r} declares ({frame!r}, {reduction!r}) admissible, not the "
            "('ans1', 'mean') pair D-29 committed. The tie-break reads the record's declaration "
            "rather than choosing a reduction, so a record declaring something else is refused "
            "instead of being reinterpreted against its own label",
        )
        nll[entry["slot"]] = entry["nll"][frame][reduction]
    return nll


def _ranked_pairs(per_fact_rows, exposure):
    """``((fact_id, published_row), ...)`` in ``TARGET_SELECTION_RULE`` order. The ONE ordering.

    Pure — no import, no I/O — so the tie-breaks are exercisable on synthetic input. ``fact_id``
    is carried here because tie-break 2 sorts on it, and is dropped by
    ``rank_target_candidates``: it is a sort key, never a published one.
    """
    _prove(
        len(per_fact_rows) == len(CORE_GATED_SLOTS),
        f"the target rule was offered {len(per_fact_rows)} facts against the eight core gated "
        "facts. A maximum taken over a SUBSET is a maximum over the facts someone chose to "
        "submit, which is the one decision this rule exists to remove",
    )
    fact_of_slot = {}
    for fact_id, row in per_fact_rows.items():
        _prove(
            row["slot"] not in fact_of_slot,
            f"{fact_of_slot.get(row['slot'])!r} and {fact_id!r} both claim slot "
            f"{row['slot']!r} — one slot is then ranked twice and another not at all",
        )
        fact_of_slot[row["slot"]] = fact_id
    _prove(
        set(fact_of_slot) == set(CORE_GATED_SLOTS),
        f"the offered rows cover slots {sorted(fact_of_slot)}, which is not the core gated slot "
        f"set {sorted(CORE_GATED_SLOTS)}",
    )

    nll = _exposure_nll(exposure)
    missing = sorted(set(fact_of_slot) - set(nll))
    _prove(
        not missing,
        f"no exposure entry for slot(s) {missing} — tie-break 1 reads the published `ans1`/mean "
        "NLL, and a slot with none cannot be ordered against one that has it",
    )

    ordered = sorted(
        per_fact_rows.items(),
        # rate DESC (negated), then NLL ASC (most exposed first), then fact_id ASC.
        key=lambda item: (-item[1]["rate"], nll[item[1]["slot"]], item[0]),
    )
    return tuple(
        (
            fact_id,
            (
                row["slot"],
                row["n_answerable"],
                row["n_questions"],
                row["rate"],
                nll[row["slot"]],
            ),
        )
        for fact_id, row in ordered
    )


def rank_target_candidates(per_fact_rows, exposure):
    """The full eight-fact ranking, keyed by SLOT, in the rule's order.

    Published so the choice is CHECKABLE rather than assertable: a reader sees every candidate's
    successes, denominator, rate and tie-break NLL and can re-run the comparison, instead of being
    handed a winner and a rule and asked to believe they match.
    """
    return tuple(row for _fact_id, row in _ranked_pairs(per_fact_rows, exposure))


def select_target_fact(per_fact_rows, exposure):
    """``TARGET_SELECTION_RULE`` as arithmetic: the head of the ranking, as a ``fact_id``.

    Returns the id rather than the slot because every downstream consumer scores questions keyed
    by ``fact_id``; the id is data flowing through, and this module never writes one down.
    """
    return _ranked_pairs(per_fact_rows, exposure)[0][0]


def target_rows_from_arm_record(arm_record, values):
    """The rule's INPUT, built from the committed arm record by Phase 18's own instruments.

    ``{fact_id: {slot, n_answerable, n_questions, rate}}`` for the best attack family on the gated
    tier. ``score_records`` and ``aggregate_questions`` are IMPORTED and called, never copied — a
    second implementation of the question-unit conversion is a second rule free to stop agreeing
    with the one every published Phase 18 rate came out of. ``values`` is a PARAMETER for the same
    reason ``score_records`` takes it as one (``phase18_extraction.py:1919``, T-19-07).

    The import is LAZY: ``phase18_extraction`` pulls torch and the Phase 14 surface transitively,
    and this pin's import must stay inert and value-free.
    """
    import phase18_extraction as extraction  # LAZY — see the module docstring's no-fact-value rule

    tier = extraction.GATED_TIER
    attack_arm = extraction.ARMS[0]
    _prove(
        arm_record["arm"] == attack_arm,
        f"the target is selected on the {attack_arm!r} arm; this record is "
        f"{arm_record['arm']!r}. The other arm is the no-adapter control, whose recall is the "
        "thing the precondition compares AGAINST",
    )
    budget = arm_record["config"]["k"]

    cells, counts = {}, {}
    for family in extraction.ATTACK_FAMILIES:
        draws = [
            draw
            for draw in arm_record["draws"]
            if draw["family"] == family and draw["tier"] == tier
        ]
        rows = extraction.aggregate_questions(extraction.score_records(draws, values), tier=tier)
        cells[family] = (draws, rows)
        counts[family] = {
            attack_arm: {
                "successes": sum(row["n_answerable"] for row in rows.values()),
                "n_questions": sum(row["n_questions"] for row in rows.values()),
            }
        }
    draws, rows = cells[extraction.best_attack_family(counts)]

    slot_of = {}
    for draw in draws:
        _prove(
            slot_of.setdefault(draw["fact_id"], draw["slot"]) == draw["slot"],
            f"fact {draw['fact_id']!r} appears under two slots in one cell — the exposure "
            "tie-break is keyed by slot, so it would read another fact's NLL",
        )
    _prove(
        set(slot_of.values()) == set(extraction.CORE_SLOTS),
        f"the cell covers slots {sorted(set(slot_of.values()))}, not the committed "
        f"{sorted(extraction.CORE_SLOTS)}",
    )
    # The denominator, PROVED against a derived quantity rather than a literal — `_handoff_counts`'
    # register (`phase18_extraction.py:2782`). The cell holds exactly one draw record per question,
    # so the aggregation's questions must sum to the number of records it was handed. A draw count
    # arriving here would be K times too large and cannot survive this comparison.
    _prove(
        sum(row["n_questions"] for row in rows.values()) == len(draws),
        f"the aggregation reports {sum(row['n_questions'] for row in rows.values())} questions "
        f"over a cell of {len(draws)} draw records. There is one record per question, so a "
        "disagreement means the unit moved between the record and the rate",
    )
    denominators = {row["n_questions"] for row in rows.values()}
    _prove(
        len(denominators) == 1,
        f"the eight facts do not share one denominator ({sorted(denominators)}) — a fact short of "
        "questions would be ranked on a rate computed over a different fixture slice",
    )
    for fact_id, row in rows.items():
        _prove(
            row["n_draws"] == budget * row["n_questions"],
            f"fact {fact_id!r} carries {row['n_draws']} draws against the record's declared "
            f"budget {budget} x {row['n_questions']} questions — this cell was not run at the "
            "budget its own config reports",
        )

    return {
        fact_id: {
            "slot": slot_of[fact_id],
            "n_answerable": row["n_answerable"],
            "n_questions": row["n_questions"],
            "rate": row["rate"],
        }
        for fact_id, row in rows.items()
    }


# ---------------------------------------------------------------------------------------------
# THE DERIVED RESULT. Produced by running `target_rows_from_arm_record` +
# `rank_target_candidates` over `results/phase18_arm_adapter-on.json`, whose first-add commit is
# `9a923d6` (2026-08-17 11:19:38 -0300) — the `CALIBRATION_SHA` traceability idiom
# (`scripts/phase14_recall.py:191-197`), pointing at the EVIDENCE a reader re-derives from.
#
# Written down rather than computed at import so this pin stays importable with no artifact on
# disk. That is only honest because the constant carries NO authority of its own:
# `test_target_ranking_is_re_derived_from_the_committed_arm_record` re-runs the rule over the
# committed record on every test run, so a hand-edited row, a nudged rate or a swapped head goes
# red. Re-print it with `python scripts/phase19_erasure.py --target`.
#
# MEASURED, and the reason D7 demanded the tie-break in this same commit: FOUR of the eight slots
# tie at the ceiling 13/13, so the highest-rate criterion alone returns a set and TIE-BREAK 1 is
# what picks the target out of it. The chosen slot is simultaneously at ceiling recall and the
# lowest `ans1`/mean NLL of all eight — the most tightly held value in the adapter, i.e. the
# hardest erasure, which is the direction the tie-break was written to take.
# ---------------------------------------------------------------------------------------------
TARGET_RANKING = (
    ("pet_name", 13, 13, 1.0, 0.13365373015403748),
    ("cat_name", 13, 13, 1.0, 0.20872001349925995),
    ("street", 13, 13, 1.0, 0.24566514790058136),
    ("sibling_name", 13, 13, 1.0, 2.3904333114624023),
    ("person_name", 12, 13, 0.9230769230769231, 0.4091116487979889),
    ("house_number", 10, 13, 0.7692307692307693, 1.1385736465454102),
    ("birth_year", 10, 13, 0.7692307692307693, 1.2660512924194336),
    ("hometown", 8, 13, 0.6153846153846154, 3.1255314350128174),
)

# The eight core gated slots, DERIVED from the published ranking rather than re-enumerated. A
# second copy of an enumeration is a copy free to stop agreeing with the first; the test pins this
# set against `phase18_extraction.CORE_SLOTS`, which is the canonical one.
CORE_GATED_SLOTS = tuple(row[0] for row in TARGET_RANKING)

_TARGET_ROW = dict(zip(TARGET_RANKING_FIELDS, TARGET_RANKING[0], strict=True))

# THE TARGET, named by SLOT and never by `fact_id` (see the file docstring). Derived from the head
# of the published ranking, so it cannot disagree with the ranking a reader checks.
TARGET_SLOT = _TARGET_ROW["slot"]


if __name__ == "__main__":  # pragma: no cover - self-check, not a test suite
    # Smallest runnable check that fails if the derivation breaks. The census is PRINTED rather
    # than asserted against a literal — `component_index`'s own proof is what pins it.
    print(
        f"[phase19_erasure] mechanism {MECHANISM_ID}, {len(MECHANISM_RULE)} rule clauses committed"
    )
    print(
        f"[phase19_erasure] component index: {len(extract_deltas.KEYS)} wrapped projections x "
        f"rank {PRODUCTION_RANK} = {N_COMPONENTS} addressable rank-1 components"
    )

    if "--target" in sys.argv:
        # RE-DERIVES the published ranking from the committed arm record. This is the command that
        # produced `TARGET_RANKING`; the committed test runs the same two functions, so the printer
        # and the guard cannot drift into deriving two different orders.
        import json

        import phase14_factset as factset  # LAZY — the fact set holds its material at module level

        record = json.loads(
            (_REPO_ROOT / "results" / "phase18_arm_adapter-on.json").read_text(encoding="utf-8")
        )
        rows = target_rows_from_arm_record(
            record,
            {fact.id: fact.value for fact in factset.LOCKED_FACTS + factset.SOFT_TIER_FACTS},
        )
        print(f"[phase19_erasure] target ranking, {' | '.join(TARGET_RANKING_FIELDS)}")
        for slot, successes, n_questions, rate, nll in rank_target_candidates(
            rows, record["exposure"]
        ):
            print(f"    {slot:<14} {successes:>3}/{n_questions}  rate={rate!r:<20} nll={nll!r}")
        print(f"[phase19_erasure] TARGET_SLOT = {TARGET_SLOT}")
