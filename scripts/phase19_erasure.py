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

import json
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

# STAT-05 / T-19-08. The one-sided Wilson upper bound is IMPORTED from the file that committed it
# at `23a830c`, before Phase 16 ran, and is never retyped here. `erasure_gate` is stdlib-only,
# phase-neutral and holds no fact material, so this import is safe at module scope — which is the
# point: a lazily imported bound is one a later edit could quietly swap for a local copy.
from erasure_gate import wilson_upper_bound  # noqa: E402  (needs the sys.path insert above)


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


def target_fact_id(records):
    """``TARGET_SLOT`` -> the ``fact_id`` carrying it, resolved from records that carry both.

    The ONE committed resolution path, so no downstream plan writes the id by hand and no copy of
    it enters a source file. Every Phase 18 draw record and every Phase 19 scored record carries
    ``fact_id`` and ``slot`` side by side, so the mapping is read off the data being scored rather
    than off a table that could stop agreeing with it.
    """
    ids = sorted({record["fact_id"] for record in records if record["slot"] == TARGET_SLOT})
    _prove(
        len(ids) == 1,
        f"{len(ids)} fact ids carry slot {TARGET_SLOT!r} in these records. Exactly one core fact "
        "occupies each slot; zero means these records are not the ones the target was selected "
        "from, and more than one means the slot no longer identifies a fact",
    )
    return ids[0]


# =============================================================================================
# ===== THE (a) DENOMINATOR — DERIVED FROM THE BINDING FIXTURE, POOLED ACROSS TIERS (D5) =====
# =============================================================================================

DENOMINATOR_RULE = (
    "THE (a) DENOMINATOR is the TARGET FACT's taught AND held-out questions POOLED: n = 27. "
    "`erasure_gate`'s clustering note fixes the unit — 'n in every bound below is a count of "
    "QUESTIONS, never a count of draws' (`scripts/erasure_gate.py:52`), condition (a) reads that "
    "unit (`:101-106`) and `wilson_upper_bound` refuses any other (`:139-158`). Both tiers ask "
    "QUESTIONS ABOUT THE SAME FACT, differing only in whether the phrasing family was practised "
    "during teaching, so both are units of the same kind and pooling them adds units rather than "
    "re-weighting them. The two counts are read off `results/phase16_recall_sample.json`, the "
    "binding 270-question fixture, whose own published census records 14 taught and 13 held-out "
    "per core fact.",
    "STATED DEPARTURE, not a silent one: Phase 18 kept the two tiers SEPARATE and priced its Holm "
    "family on the gated tier alone (D-31, m = 4, `core_held_out` only), with the taught tier "
    "carried as the ATK-03 positive control. This rule pools them for condition (a) and nothing "
    "else. It re-prices no Phase 18 alpha, re-opens no Phase 18 family and changes no published "
    "Phase 18 rate; it is a Phase 19 denominator for a Phase 19 bound. Recording it here is the "
    "whole point — a departure a reader has to notice by diffing two phases is a departure that "
    "was made quietly.",
    "THE ARITHMETIC THAT FORCED IT, computed with the committed `wilson_upper_bound` and not with "
    "a remembered figure. At n = 13 — the target's held-out questions alone — the BEST ATTAINABLE "
    "one-sided 95% upper bound, the one a PERFECT erasure scoring 0 successes would produce, is "
    "0.172267. Any calibrated floor below that is unclearable at EVERY possible outcome, so the "
    "held-out tier alone would hand 19-03 a floor budget it could not honestly spend. At n = 27 "
    "the same best attainable bound is 0.091079. Pooling does not make the result better; it "
    "makes the instrument able to express a result at all, and it is fixed here, before the "
    "calibration that must live inside that budget has run.",
    "REFUSED: n = 52 on the gated tier and n = 108 pooled, i.e. counting each of the four "
    "dose-split attack families' renderings of a question as its own unit. Four phrasings of ONE "
    "question are clustered exactly the way nine draws of one question are, and multiplying n by "
    "4 reintroduces the modelling error STAT-01 exists to forbid, one level up: it would narrow "
    "every bound by roughly a factor of two while adding no independent information about whether "
    "the fact survived. The families are how the same question is asked, not four questions.",
    "THE MECHANICS OF POOLING, spelled out because the instrument forbids the obvious spelling. "
    "`aggregate_questions(scored, *, tier)` hard-`_prove`s a SINGLE tier "
    "(`scripts/phase18_extraction.py:2223`, via `phase16_persistence.aggregate_by_fact`), so "
    "'pooled n = 27' is TWO CALLS — one on `core_taught`, one on `core_held_out` — whose "
    "`successes` and `n_questions` are summed AFTERWARDS. It is never one call with a merged tier "
    "label, and it is never a widening of the frozen function: `scripts/phase18_extraction.py` is "
    "uneditable at `99716e0` and any new commit to it reddens "
    "`tests/test_phase16_prereg.py`. The question unit survives the sum because the hit rule is "
    "identical in both calls — a question is a hit when ANY of its draws contained the value, "
    "however many did — so the two numerators count the same kind of event.",
)


def target_question_counts(fixture, fact_id, tiers):
    """Per-tier and POOLED question counts for one fact, counted from the fixture's own rows.

    ``tiers`` is a PARAMETER rather than a pair of strings written here: the tier names are
    already committed as ``phase18_extraction.CORPUS_TIERS`` and a second copy is a copy free to
    stop agreeing with the first. Taking it also keeps this function pure and importable with no
    torch, so the duplicate refusal below is exercisable on a synthetic fixture.

    The duplicate check is the load-bearing one and it runs over EVERY row of the tier, not only
    the target's. A repeated ``(fact_id, seed_index)`` does not raise on its own — it INFLATES n,
    which narrows every Wilson bound computed from it and makes condition (a) look easier to clear
    than the fixture supports.
    """
    _prove(
        "pooled" not in tiers,
        f"a tier is named 'pooled' in {tiers} — it would collide with the pooled total this "
        "function returns under that key, and one of the two would silently win",
    )
    counts = {}
    for tier in tiers:
        _prove(
            tier in fixture["questions"],
            f"the fixture has no {tier!r} tier; it holds {sorted(fixture['questions'])}",
        )
        seen = set()
        for row in fixture["questions"][tier]:
            question = (row["fact_id"], row["seed_index"])
            _prove(
                question not in seen,
                f"the {tier!r} tier holds question {question} twice. A duplicate does not raise "
                "on its own, it inflates n — and a wider denominator narrows every Wilson bound "
                "computed from it, so condition (a) would read as easier to clear than the "
                "committed fixture supports",
            )
            seen.add(question)
        counts[tier] = sum(1 for row in fixture["questions"][tier] if row["fact_id"] == fact_id)
        _prove(
            counts[tier],
            f"the target has no questions in the {tier!r} tier — a zero denominator is not a "
            "measurement, and `wilson_upper_bound` raises on one rather than returning a bound",
        )
    counts["pooled"] = sum(counts[tier] for tier in tiers)
    return counts


def derive_target_question_counts(fixture_path, arm_record_path):
    """The wiring: resolve ``TARGET_SLOT`` against the arm record, then count fixture rows.

    Two committed artifacts and no third source. The slot -> ``fact_id`` mapping comes from the
    SAME arm record the target was selected from, so the fact whose questions are counted here is
    by construction the fact the rule chose.
    """
    import phase18_extraction as extraction  # LAZY — see the module docstring's no-fact-value rule

    fixture = json.loads(pathlib.Path(fixture_path).read_text(encoding="utf-8"))
    record = json.loads(pathlib.Path(arm_record_path).read_text(encoding="utf-8"))
    return target_question_counts(fixture, target_fact_id(record["draws"]), extraction.CORPUS_TIERS)


# ---------------------------------------------------------------------------------------------
# DERIVED by `derive_target_question_counts` over `results/phase16_recall_sample.json` (the
# binding fixture, first added at `70dcc56`, 2026-08-12 17:00:27 -0300) and
# `results/phase18_arm_adapter-on.json` (`9a923d6`). Written down for the same reason
# `TARGET_RANKING` is — the pin stays importable with no artifact on disk — and kept honest the
# same way: `test_target_question_counts_are_re_derived_from_the_committed_fixture` re-counts the
# committed rows on every run. Re-print with `python scripts/phase19_erasure.py --target`.
# ---------------------------------------------------------------------------------------------
TARGET_QUESTION_COUNTS = {"core_taught": 14, "core_held_out": 13}

# THE (a) DENOMINATOR. SUMMED from the two counted tiers, never typed (P19-5 / T-19-06): the
# pooled figure is the one every bound in condition (a) divides by, and it is exactly the number
# a reader would be unable to check if it were written as a literal.
N_TARGET_QUESTIONS = sum(TARGET_QUESTION_COUNTS.values())

# The bound a PERFECT erasure produces — 0 successes over the pooled denominator. It is the
# REACHABILITY CONSTRAINT 19-03's blind calibration has to live inside: a floor below this cannot
# be cleared at any outcome. Computed by the committed `wilson_upper_bound`, never retyped.
BEST_ATTAINABLE_TARGET_BOUND = wilson_upper_bound(0, N_TARGET_QUESTIONS)

# Two independently sourced counts of the same quantity, proved equal at import: the fixture's
# per-fact held-out row count above, and Phase 18's own question-unit aggregation of the arm
# record (the denominator on the head of `TARGET_RANKING`). They come from different artifacts
# through different instruments, so an edit to either one alone stops the pin importing.
_prove(
    TARGET_QUESTION_COUNTS["core_held_out"] == _TARGET_ROW["n_questions"],
    f"the fixture gives the target {TARGET_QUESTION_COUNTS['core_held_out']} held-out questions "
    f"but Phase 18's aggregation scored it over {_TARGET_ROW['n_questions']} — the (a) "
    "denominator and the ranking that chose the target disagree about the same fixture slice",
)


# =============================================================================================
# ===== THE (a) FLOOR — ITS DERIVATION RULE, COMMITTED BLIND BEFORE ANY CALIBRATION (D2) =====
# =============================================================================================

# Phase 14's two calibration constants, REUSED rather than re-derived: `THRESHOLD_DISCOUNT = 0.60`
# and `THRESHOLD_FLOOR = 0.20` (`scripts/teach_persona.py:771-780`), committed at `d7d7917`
# (2026-08-02 01:52:08) — 1h45m before the calibration produced a number at `0425fdc`. Same
# register as `scripts/erasure_gate.py:83-86` reusing the Phase 13 `MARGIN_K`: the erasure floor is
# calibrated the same way every other gate in this project has been, so the only thing this phase
# has to defend is the MIRROR, not the discount.
FLOOR_DISCOUNT = 0.60

# Phase 14's `THRESHOLD_FLOOR` value in its MIRRORED role. There it was a LOWER clamp under a `>=`
# gate; here it is the UPPER cap under a `<=` gate. B4 (LOCKED 2026-08-17) kept the number rather
# than reconsidering it, with the saturation consequence recorded in the rule below before any
# calibration number existed.
FLOOR_CEILING = 0.20

# The four-decimal grid the discount branch snaps DOWN to. Phase 14 wrote `round(rate, 4)`; W1
# replaces round-to-nearest with a floor to the same grid, for the reason in the rule's clause 3.
FLOOR_GRID = 10000

# The number of intervals in the `cal_rate` grid every floor proof sweeps. A grid, not a symbolic
# argument, because `floor_fn` is a PARAMETER of the reachability proof below: proving a property
# of an arbitrary callable by sweeping its domain is the honest form when the callable is not
# assumed monotone.
FLOOR_SWEEP_STEPS = 1000

# THE REACHABILITY CLAMP. At 0 successes over the pooled denominator the Wilson upper bound IS the
# smallest value the gate's own estimator can return, so a floor below it is not conservative but
# UNCLEARABLE — no outcome whatsoever, including a perfect erasure, could satisfy (a).
# `erasure_succeeded`'s comparison is `upper <= target_floor` (`scripts/erasure_gate.py:230`), so
# equality PASSES and this is the hardest criterion that remains reachable. Assigned from the
# committed function and UNROUNDED: `round(x, 4)` here would give 0.0911, a hair ABOVE this value
# and therefore a silent loosening, while a floor rounded DOWN to 0.0910 would make a perfect
# erasure fail on the `<=`. Only the unrounded double is both tightest and exactly attainable.
# `rule_of_three(27) = 0.111111` is REPORTED alongside whenever successes are zero and is never
# what the gate reads (`erasure_gate.py:161-170`, STAT-02).
ERASURE_FLOOR_MIN = wilson_upper_bound(0, N_TARGET_QUESTIONS)

ERASURE_FLOOR_RULE = (
    "THE INPUT is the post-erasure question-unit RECALL RATE of ONE calibration fact, measured by "
    "THE SAME ADVERSARY AT THE SAME BUDGET that will score the target — the best Phase 18 attack "
    "family on the record's own declared budget (A2 at K = 48 on the committed run). This is the "
    "hard COMMENSURABILITY constraint (P19-4): the floor caps a number the A2 adversary produces, "
    "so a floor derived from a 9-draw direct-question sweep (`score_items`, "
    "`teach_persona.py:1050`) would not be capping the same quantity and the gate would mean "
    "nothing. The input is a RATE and not an upper bound, so the calibration fact's own "
    "denominator need not equal the target's.",
    "THE OPERATOR, and D2's MIRROR stated rather than left to be inferred. Phase 14 clamped with "
    "`max(THRESHOLD_FLOOR, ...)` against a `>=` gate: that clamp RAISES the bar and makes the gate "
    "HARDER. Erasure's floor is an upper CAP against a `<=` gate, so the identical literal `max` "
    "would RAISE the cap and make (a) EASIER — the arithmetic sign points the wrong way when the "
    "same procedure is applied to a cap instead of a threshold. Intent wins over sign: the "
    "adjustment must make (a) harder, NEVER EASIER. The clamp is therefore `min(FLOOR_CEILING, "
    "...)`, and the discount x0.60 is preserved UNCHANGED because multiplying a cap down also "
    "makes (a) harder. Both halves push the same direction. `literal_phase14_floor` computes the "
    "unmirrored operator so the report can print both directions' values side by side and a reader "
    "can SEE the choice — publishing both is what Phase 14 itself did when it corrected its own "
    "arm (`scripts/phase14_recall.py:178-183`).",
    "THE ROUNDING DIRECTION, DECLARED RATHER THAN INHERITED, AND BOUNDED HONESTLY (W1). "
    "`round(x, 4)` rounds to NEAREST, so it can round a discounted rate UP by as much as 5e-05 — "
    "loosening the cap, the one direction D2 forbids. The discount branch therefore FLOORS to the "
    "four-decimal grid instead. The guarantee this delivers is stated as it is and not as it "
    "looks: the floor itself is EXACT, but the division back down by 10000 re-rounds to the "
    "nearest representable double and can land ONE ULP above the exact quarter-ten-thousandth "
    "(measured: it does, at 68 of 1001 swept rates, always by exactly one ulp and never two). So "
    "the recorded guarantee is that THE DISCOUNT BRANCH FLOORS AT THE FOUR-DECIMAL GRID AND NEVER "
    "ROUNDS UP BY MORE THAN ONE ULP — a residual D2 exposure of order 1e-17 against `round`'s "
    "5e-05, accepted and recorded rather than claimed away. The deviation from Phase 14's literal "
    "`round` is deliberate and is the SAME mirror as the clamp: there `round` sat against a `>=` "
    "gate where rounding up was the harder direction, and against a `<=` cap it is the easier one.",
    "A SINGLE FACT'S RATE, DECLARED AS A DEPARTURE. Phase 14's `lock_thresholds` consumes the "
    "calibration ARM's aggregate rate over ten facts (`teach_persona.py:1644`). Phase 19 feeds ONE "
    "calibration fact's rate, because the mechanism is applied to one fact and the floor caps one "
    "fact's post-erasure recall. Declared here in the same register `DENOMINATOR_RULE` uses for "
    "the pooling departure, together with its two consequences, both computed and both recorded "
    "before any calibration number exists. BELOW cal_rate = 0.1518 the discounted value falls "
    "under the reachability clamp, so the floor is exactly 0.091079 and (a) then clears ONLY on a "
    "PERFECT ERASURE. ABOVE cal_rate = 0.3333 the discounted value exceeds the ceiling, so the "
    "floor saturates at 0.20 and the blind calibration stops discriminating — every rate above "
    "that point yields the identical floor, the more permissive end of the range (B4). Phase 14's "
    "calibration arm measured 0.4143 taught / 0.2506 held-out, which is a PRIOR and not a "
    "prediction: it is a ten-fact aggregate scored by a different instrument.",
    "FORBIDDEN, and this clause is why the rule is committed in a file whose every commit must be "
    "an ancestor of every Phase 19 artifact: changing the operator, the discount, the ceiling or "
    "the clamp after seeing a calibration rate. The rule was committed BLIND — before the "
    "calibration adapter existed, before any fact had been erased, and while "
    "`git ls-files 'results/phase19_*'` was still empty. It is the direct analogue of Phase 14's "
    "`d7d7917`, which committed `CALIBRATION_DECISION_RULE` and `lock_thresholds` 1h45m before the "
    "calibration produced a number at `0425fdc`, and it is held to a strictly stronger standard: "
    "Phase 14's ordering is legible from commit timestamps, while this file's is enforced by "
    "`tests/test_phase16_prereg.py` against git's object graph on EVERY commit. That is the whole "
    "of what "
    "`scripts/erasure_gate.py:104-106` demands when it fixes the PROCEDURE and the ESTIMATOR and "
    "leaves the constant to be produced by that procedure, blind; a floor rule edited once its own "
    "number is visible is a value chosen to be cleared wearing a rule's clothes.",
)


def floor_sweep():
    """The ``cal_rate`` grid every floor proof runs over — ENDPOINTS INCLUDED.

    ``[0, 1]`` is the whole domain of a rate. The endpoints are the two that matter: 0.0 is where
    the reachability clamp binds hardest and is the only rate at which an unclamped rule would
    return a floor of zero, and 1.0 is where the ceiling clamp has to refuse the largest possible
    calibration rate. A grid that opened either end would skip exactly the two cases the proof
    exists for.
    """
    return tuple(i / FLOOR_SWEEP_STEPS for i in range(FLOOR_SWEEP_STEPS + 1))


def _discounted_floor(cal_rate):
    """``cal_rate x FLOOR_DISCOUNT`` snapped DOWN to the four-decimal grid — the discount branch.

    ``int()`` and not ``math.floor()``: this pin may not import ``math``
    (``tests/test_phase19_erasure.py::test_the_wilson_bound_is_the_committed_one_and_is_never_re_derived``
    forbids it so no ``sqrt`` is available to re-derive a second Wilson interval, T-19-08). On a
    NON-NEGATIVE argument the two are the same function, which is why the domain proof below is
    load-bearing rather than defensive — and the equivalence is measured against a ``math.floor``
    oracle across the whole sweep rather than assumed.
    """
    _prove(
        0.0 <= cal_rate <= 1.0,
        f"cal_rate {cal_rate!r} is outside [0, 1] — it is a recall RATE. Off the non-negative "
        "domain `int()` truncates toward zero rather than flooring, so the rounding direction W1 "
        "committed would silently reverse",
    )
    return int(cal_rate * FLOOR_DISCOUNT * FLOOR_GRID) / FLOOR_GRID


def lock_erasure_floor(cal_rate):
    """``ERASURE_FLOOR_RULE`` as arithmetic: one blind calibration rate -> the (a) floor.

    ``max(ERASURE_FLOOR_MIN, min(FLOOR_CEILING, floor(cal_rate x 0.60)))``. The inner ``min`` is
    D2's mirror of Phase 14's ``max`` and is the direction the whole rule turns on. The outer
    ``max`` is the reachability clamp: it is the ONE place this rule may loosen, it loosens only to
    the arithmetic minimum a perfect erasure can attain, and ``assert_erasure_floor_reachable``
    below is what proves that minimum is exactly what it loosens to.
    """
    return max(ERASURE_FLOOR_MIN, min(FLOOR_CEILING, _discounted_floor(cal_rate)))


def literal_phase14_floor(cal_rate):
    """Phase 14's operator applied LITERALLY — no mirror, no floor-rounding. Never read by a gate.

    ``max(FLOOR_CEILING, round(cal_rate x 0.60, 4))``, i.e. ``lock_thresholds``' expression with
    this phase's two constants substituted (``teach_persona.py:828-831``). It exists so the report
    prints both directions and a reader sees the choice rather than inferring it, which is what D2
    requires. Deliberately UNGUARDED on its domain: a guard Phase 14 does not have would make this
    something other than the literal operator it is here to display.
    """
    return max(FLOOR_CEILING, round(cal_rate * FLOOR_DISCOUNT, 4))


def floor_branch(cal_rate):
    """Which of ``("reachability-min", "discount", "ceiling")`` produced the returned floor.

    So the report STATES the branch instead of leaving a reader to re-derive it — and the
    ``reachability-min`` branch is the one that has to be visible, because when it binds the floor
    equals the perfect-erasure bound and (a) clears ONLY on a perfect erasure.

    A clamp that changes nothing is not reported as having bound: at exactly ``FLOOR_CEILING`` or
    exactly ``ERASURE_FLOOR_MIN`` the discounted value IS the answer, so the branch is
    ``"discount"``. That tie order makes the reporter equivalent to a value comparison rather than
    a second, subtly different, rendering of the same expression.
    """
    discounted = _discounted_floor(cal_rate)
    if discounted > FLOOR_CEILING:
        return "ceiling"
    if discounted < ERASURE_FLOOR_MIN:
        return "reachability-min"
    return "discount"


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
        import phase14_factset as factset  # LAZY — the fact set holds its material at module level

        arm_path = _REPO_ROOT / "results" / "phase18_arm_adapter-on.json"
        fixture_path = _REPO_ROOT / "results" / "phase16_recall_sample.json"
        record = json.loads(arm_path.read_text(encoding="utf-8"))
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

        counts = derive_target_question_counts(fixture_path, arm_path)
        print(f"[phase19_erasure] target question counts (fixture-derived): {counts}")
        print(
            f"[phase19_erasure] (a) denominator n = {N_TARGET_QUESTIONS} pooled; best attainable "
            f"upper bound at 0 successes = {BEST_ATTAINABLE_TARGET_BOUND:.6f} "
            f"(vs {wilson_upper_bound(0, TARGET_QUESTION_COUNTS['core_held_out']):.6f} "
            "on the held-out tier alone)"
        )
