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

**2b. THE INVOCATION SURFACE IS CLOSED. This file is run as ``python scripts/phase19_erasure.py
<subcommand>`` and nothing else.** ``SUBCOMMANDS`` names every one of them — ``cal-corpus``,
``cal-train``, ``cal-erase``, ``noise-floors``, ``erase``, ``retrain``, ``representational``,
``report``, plus the two self-check modes ``target`` and ``floor`` — INCLUDING the ones whose
plans have not run yet, and a module-scope proof requires the dispatch table to hold exactly that
set. NO PLAN FROM 19-08 ONWARD MAY ADD A SUBCOMMAND, A FLAG, OR ANY OTHER LINE TO THIS FILE.
Naming a subcommand costs nothing now and costs the ancestry guard later: the natural executor
move — "add a mode to the driver" — is a commit to a pre-registration whose numbers already exist.
If a run genuinely needs something the pinned CLI cannot express, the answer is an UNPINNED
THROWAWAY (``python -c ...``, or a new ``scripts/phase19_run.py``), never a commit here.

**3. After 19-07 this file is permanently uneditable.** ``scripts/phase17_personas.py`` reached that
state at ``d549e0b`` and ``scripts/phase18_extraction.py`` at ``99716e0`` — in both cases the moment
the phase's first result artifact was committed. The recovery path for a genuine defect discovered
afterwards is a DATED CONTINUATION published beside the original text (``scripts/_addendum.py``,
decision D3), never an edit and never a ``--force`` flag. Editing a recorded rule after its number
exists destroys the only thing that made the rule worth recording.

WHAT THIS FILE HOLDS AT PLAN 19-05, AND WHAT IT DELIBERATELY DOES NOT
--------------------------------------------------------------------
Holds: the ordering contract above, the mechanism identity and its rule, the DERIVED component
index, the ablation operator (19-01), the target-selection rule with its two tie-breaks, the
published eight-fact ranking and the derived (a) denominator (19-02), the (a) floor-DERIVATION
rule with its mirrored operator and its import-time reachability proof (19-03), the two
NOISE-FLOOR ESTIMATORS plus the retention measurement spec and the arm-record schema (19-04), and
the representational read, the Phase 18 parity assertions and the report text with its
ship-decision marker pair (19-05). The arm runners are plan 19-06, and writing them here early
would mean fixing them before the plan that reasons about them.

WHY THE REPRESENTATIONAL READ IS STRUCTURAL AND NOT A CONVENTION
---------------------------------------------------------------
``scripts/erasure_gate.py:118-122`` makes representational consistency DESCRIPTIVE and EXPLICITLY
NOT GATED: at n=8 facts and n=3 personas the sample cannot support a threshold, and gating what the
sample cannot support is treated as a DEFECT in this project rather than as extra rigour. A second
``sign_test_exact`` call site IS a second hypothesis family, and would reprice Holm so that a
DESCRIPTIVE statistic paid for part of the alpha the real comparisons need.

So ``DESCRIPTIVE_ONLY_FUNCTIONS`` names the three functions on that path and a committed AST scan
refuses, inside any of them, a call to ``sign_test_exact`` / ``holm`` / ``wilson_upper_bound``, an
ordering comparison of any kind, and a read of ANY module-level number. A DANGLING entry in that
tuple fails the scan rather than quietly excusing a missing target, so a rename cannot escape it.
This is the same discipline that landed ``test_context_pressure_sweep_is_not_gated`` BEFORE the
sweep it constrains (``scripts/phase16_persistence.py:1289-1293``) — the guard ships in the same
commit as the read, not after it.

The verdict has exactly ONE path (``render_verdict``), it CALLS the rule committed at ``23a830c``
rather than re-implementing it, and the four v2.0 baselines that rule reads
(``V20_MASKED_DIALOGUE_VAL_PPL``, ``V20_EWC_RETENTION_PPL``, ``V20_RETENTION_NOISE_FLOOR``,
``MARGIN_K``) may not appear as numeric literals anywhere in this file.

EVERY KEYWORD-ONLY ARGUMENT OF ``erasure_succeeded`` NOW HAS A NAMED PRODUCER IN THIS FILE.
``target_successes`` / ``target_questions`` (19-02), ``target_floor`` (19-03),
``nontarget_deltas`` + ``nontarget_noise_floor`` (19-04 task 2), ``dialogue_ppl`` +
``dialogue_ppl_noise_floor`` + ``retention_ppl`` (19-04 task 1) and ``zero_results_have_nll``
(19-04 task 3). Three of them had NO committed default at all, and the one nobody notices is
``dialogue_ppl_noise_floor`` (``scripts/erasure_gate.py:208``): it is threshold-shaped, so a value
picked once the cap is visible is a value picked to be cleared.

The (a) floor CONSTANT is not here and cannot be: it does not exist until a blind calibration has
run, which is the whole content of ``scripts/erasure_gate.py:104-106``. What is committed here is
the PROCEDURE and the ESTIMATOR that will produce it.

A RECORDED CONSEQUENCE, stated here rather than left to be discovered from the arithmetic: the
floor rule's outer clamp is the best bound a PERFECT ERASURE can attain (0 successes over the
pooled denominator). Whenever that clamp binds — which includes every calibration rate below
0.1518, and marginally beyond it because the discount snaps down to a four-decimal grid — the
floor IS that bound, and condition (a) then clears ONLY on a perfect erasure. That is the intended
severity and not an accident of rounding; ``floor_branch`` exists so the published report names
which clamp bound rather than leaving a reader to re-derive how hard the criterion they are
reading actually was.

NO FACT VALUE MAY ENTER THIS FILE, IN ANY STRING, DOCSTRINGS INCLUDED. Every core ``fact_id`` ends
in its own locked value (``scripts/phase17_personas.py:61``, ``scripts/phase17_isolation.py:128``),
so the target and the ranking below are keyed by SLOT and never by ``fact_id`` — a fact-id-keyed
ranking would put all eight answers into the pre-registration's source. ``fact_id`` reaches this
module only as data at call time, and ``values`` reaches ``score_records`` as a PARAMETER
(``phase18_extraction.py:1919``). ``tests/test_phase19_erasure.py`` scans this file for all ten.

Success criteria are INHERITED from ``scripts/erasure_gate.py`` (committed ``23a830c``, 2026-08-12
16:27:43 -0300, before Phase 16 ran) and are never re-authored here. That file fixed the BAR and
deliberately fixed no design; this file commits the DESIGN it left open, and touches no bar.

Nothing executes at import beyond the ``sys.path`` bootstrap below and three PURE proofs — the
component census, the two-source denominator cross-check, and the floor-REACHABILITY sweep. Each
is pure arithmetic over already-committed constants. No file is read at import and no artifact is
loaded: ``scripts/phase18_extraction.py`` holds the same discipline, and a pin that could not be
imported without its inputs on disk would be a pin whose rules stop being quotable the moment a
path moves. CPU-only, GPU-free, no checkpoint read, no network.
"""

import json
import pathlib
import re
import sys

import torch

from personacore.config import ModelConfig
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
# The ONE anchored `## Verdict` section read (CR-02's single shared copy) and the ONE append-only
# continuation writer with its marker PAIR as required keywords. Both are phase-neutral, stdlib-only
# and hold no fact material, so they are safe at module scope — and importing them rather than
# re-deriving either is what keeps this phase's clobber guard the same guard as every other one.
import _addendum  # noqa: E402  (needs the sys.path insert above)
import _verdict  # noqa: E402  (needs the sys.path insert above)
import extract_deltas  # noqa: E402  (needs the sys.path insert above)

# STAT-05 / T-19-08. The one-sided Wilson upper bound, the margin discipline and the three v2.0
# baselines are IMPORTED from the file that committed them at `23a830c`, before Phase 16 ran, and
# are never retyped here. `erasure_gate` is stdlib-only, phase-neutral and holds no fact material,
# so this import is safe at module scope — which is the point: a lazily imported bound is one a
# later edit could quietly swap for a local copy, and a retyped `MARGIN_K` or baseline PPL is a
# second copy of a number the gate reads, free to stop agreeing with it.
from erasure_gate import (  # noqa: E402  (needs the sys.path insert above)
    MARGIN_K,
    V20_EWC_RETENTION_PPL,
    V20_MASKED_DIALOGUE_VAL_PPL,
    V20_RETENTION_NOISE_FLOOR,
    VERDICTS,
    erasure_succeeded,
    rule_of_three,
    wilson_upper_bound,
)


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
    "PERFECT ERASURE. That figure is the CONTINUOUS crossover ERASURE_FLOOR_MIN / FLOOR_DISCOUNT "
    "and is a sufficient condition, not an iff: because the discount snaps DOWN to the "
    "four-decimal grid, the clamp still binds a hair beyond it. `floor_branch` reports which bound "
    "actually applied for exactly this reason — so the branch is read off the rule rather than "
    "inferred from this sentence. ABOVE cal_rate = 0.3333 the discounted value exceeds the "
    "ceiling, so the "
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


def assert_erasure_floor_reachable(n_questions, floor_fn):
    """Q7.2 — prove (a) CAN be cleared before anything spends compute trying.

    ``wilson_upper_bound(0, n_questions)`` is the BEST ATTAINABLE outcome: zero successes over
    every scored question, a PERFECT erasure, and the smallest value the gate's own estimator can
    return at that denominator. If any calibration rate could produce a floor below it, then no
    outcome whatsoever satisfies (a) and the criterion is dead arithmetically rather than merely
    strict. ``wilson_upper_bound(0, 27) = 0.091079`` is a FACT, not a proof; this is the proof.

    The comparison is NON-STRICT, matching ``erasure_succeeded``'s own ``upper <= target_floor``
    (``scripts/erasure_gate.py:230``). A bound exactly on the floor PASSES there and must pass
    here, or this proof would refuse a floor the gate itself would accept — the mirror of the
    strictness ``assert_holm_family_reachable`` records for Holm's ``p < alpha_at_step``.

    ``floor_fn`` is a PARAMETER and is not assumed monotone, so the property is established by
    SWEEPING its whole domain rather than by evaluating an endpoint and arguing. Returns the
    attainable bound, so a report prints the number the phase was actually priced at instead of a
    second copy computed beside it.
    """
    best_attainable = wilson_upper_bound(0, n_questions)
    sweep = floor_sweep()
    _prove(
        sweep[0] == 0.0 and sweep[-1] == 1.0,
        f"the reachability sweep runs over [{sweep[0]!r}, {sweep[-1]!r}] and not the closed unit "
        "interval — the endpoints are exactly the two rates the clamps exist for, so an open grid "
        "would skip the cases this proof is here to cover",
    )
    for cal_rate in sweep:
        floor = floor_fn(cal_rate)
        _prove(
            best_attainable <= floor,
            f"a calibration rate of {cal_rate!r} produces an (a) floor of {floor!r}, but the best "
            f"attainable upper bound over {n_questions} questions — 0 successes, a PERFECT "
            f"ERASURE — is {best_attainable!r}. No outcome whatsoever could clear that floor, so "
            "condition (a) would be unclearable by construction rather than strict. Discovering "
            "it after the calibration adapter, the calibration erasure, the noise-floor runs and "
            "the target erasure have all spent their compute is exactly the cost this import-time "
            "proof buys out — the same defect Phase 16 caught at m = 12 "
            "(scripts/phase16_persistence.py:737-743) and Phase 18 at m = 8 "
            "(results/phase18_extraction_report.md:160)",
        )
    return best_attainable


# At MODULE SCOPE, so an unclearable (a) cannot survive to a run: importing this pin at all — in
# the suite, in a smoke, in the run itself — is what runs the proof. The return value is
# deliberately NOT bound to a third name for the same float; `ERASURE_FLOOR_MIN` is the constant
# and `BEST_ATTAINABLE_TARGET_BOUND` (19-02) is its measurement-side twin. Callers that want the
# number the phase was priced at call this and print what it returns.
assert_erasure_floor_reachable(N_TARGET_QUESTIONS, lock_erasure_floor)


# =============================================================================================
# ===== THE (c) DIALOGUE NOISE FLOOR AND THE RETENTION MEASUREMENT, PINNED BEFORE EITHER RUNS ==
# =============================================================================================

# Phase 12's dialogue-PPL seed-to-seed spread — the ONLY dialogue noise floor this repository has
# ever measured (`results/finetune_smoke_report.md:49-57`, seed pair (1337, 2024), masked arm,
# LR 9e-05, 1250 steps, a FULL-FINE-TUNE regime). The RETENTION half of that same table is what
# `scripts/erasure_gate.py:77` adopts as `V20_RETENTION_NOISE_FLOOR`, which is the whole reason
# this constant is quoted rather than ignored: the gate already reads one column of that table.
V20_DIALOGUE_NOISE_FLOOR_FULL_FT = 0.001704

# The taught adapter's masked dialogue-val PPL, adapter ON, from the collateral-collapse control
# (`results/phase14_recall_report.md:462`, +27.16% over 270,203 scored targets, against the
# adapter-OFF 4.5733 the gate carries as `V20_MASKED_DIALOGUE_VAL_PPL`). This is the PRE-ERASURE
# reading and it is committed here so the (c) arithmetic below is on the record before any
# erasure runs.
V20_TAUGHT_ADAPTER_DIALOGUE_PPL = 5.8154

# THE SEED PAIR, pinned here and nowhere else. The head is `teach_persona.SEED` — the production
# teaching seed (`scripts/teach_persona.py:99`), written down rather than imported because
# `teach_persona` holds the fact set at module level and this pin may not reach it (see the file
# docstring); a committed test re-derives it against the live constant on every run. The tail is
# Phase 12's own second seed, REUSED rather than minted: taking the same pair that produced
# `V20_RETENTION_NOISE_FLOOR` makes the symmetry argument in clause 3 below exact instead of
# analogical, and a freshly invented second seed would have been a free choice nobody could check.
DIALOGUE_NOISE_FLOOR_SEEDS = (1337, 2024)

DIALOGUE_NOISE_FLOOR_ESTIMATOR = (
    "THE ESTIMATOR (Q4 option 2, as D3 selected it). The adapter-regime dialogue-PPL noise floor "
    "is |dPPL| between TWO INDEPENDENTLY SEEDED RE-TEACHINGS of the SAME fact set under the SAME "
    "recipe, each scored by `masked_perplexity` through `run_collapse_control`'s adapter-ON arm "
    "(`scripts/phase14_recall.py:1383`). `masked_perplexity` is THE frozen dialogue-val gate "
    "metric (Phase 12 TUNE-01) and the training loop's 20-random-batch estimator is DISALLOWED "
    "for gates, so this measures the same quantity the (c) cap caps. The seed pair is "
    "(1337, 2024) and is pinned in `DIALOGUE_NOISE_FLOOR_SEEDS` before either PPL exists. Cost: "
    "~3 min, i.e. 2 x the 81 s adapter retrain measured three ways "
    "(`results/phase17_training_run.log:19,39,58`).",
    "THE RECIPE IS PINNED WITH THE SEEDS, in the same commit, because a spread measured across "
    "two seeds AND a changed recipe measures the recipe. Unchanged from the production teaching "
    "run: LR 3e-4, weight_decay 0.0, batch 8, 200 steps, warmup 20, REAL_RUN_SECOND_PERSON False, "
    "REAL_RUN_REPLAY_RATIO 1.0 (`scripts/teach_persona.py:508-526,151-161`). Each of those seven "
    "is checked against its live committed value by test, so a recipe that has quietly drifted "
    "away from the one this estimator names goes red rather than silently re-scoping the floor.",
    "MEASURING THE SPREAD WITH THE ADAPTER OFF IS REFUSED. Inside `adapter_disabled` the "
    "wrapper's forward is literally `self.base(x)`, and the control measured that against the "
    "un-adapted base at a max abs diff of exactly 0.0 on the real weights — so an adapter-OFF "
    "dialogue PPL is the base's number, identical across seeds by construction. It would produce "
    "a floor of ~0 while measuring nothing about the adapter, which is the green-and-blind shape "
    "this project names as its recurring defect. The estimator reads the ON arm.",
    "THE SYMMETRY ARGUMENT, AND WHY THIS ESTIMATOR HAS TO EXIST. 0.001704 is the only dialogue "
    "noise floor ever measured here (`results/finetune_smoke_report.md:49-57`); the retention "
    "half of that same table, 0.068930, is what the gate already reads as its retention noise "
    "floor. Taking the dialogue half the same way is the symmetric move — but that table came off "
    "a FULL FINE-TUNE at 1250 steps and the erased model is a 331,776-parameter adapter, so the "
    "number is NOT transferable and only its METHOD is. This estimator is that method, re-run in "
    "the regime the gate will actually judge.",
    "THE PRE-ERASURE (c) EXCESS, ON THE RECORD BEFORE THE ERASURE AND NOT DISCOVERED AFTER IT. At "
    "the full-fine-tune floor the cap is 4.576708. The taught adapter's masked dialogue-val PPL "
    "is 5.8154 (`results/phase14_recall_report.md:462`), an excess of +1.2387 BEFORE ANY ERASURE "
    "HAPPENS. Admitting that reading would require a noise floor of 0.62105, i.e. roughly 364x "
    "the only floor ever measured. Whether a same-recipe seed spread reaches that is UNVERIFIED, "
    "and this "
    "estimator is how it becomes verified rather than assumed in either direction.",
    "IT PUBLISHES WHICHEVER WAY IT LANDS. The estimator is committed before its number exists, "
    "and the PRE-erasure dialogue PPL is published BESIDE the post-erasure one in every table — "
    "because a (c) failure that predates the erasure and a (c) failure caused by it are different "
    "findings, and the only thing that separates them is printing both numbers. A floor large "
    "enough to admit the pre-erasure reading is not a better result; it is a wider ruler, and the "
    "report says so wherever it prints one.",
)


def dialogue_noise_floor(ppl_seed_a, ppl_seed_b):
    """``|dPPL|`` over the pinned seed pair — the (c) dialogue noise floor, as one number.

    Both arguments are masked dialogue-val PERPLEXITIES from the adapter-ON arm, one per seed.
    The order does not matter and must not: an absolute difference is what a noise floor is, and
    a signed one would let the sign of an ordering decide how wide the (c) margin came out.

    ``math`` is unavailable in this pin (T-19-08), so non-finiteness is detected with ``x != x``
    for NaN and a comparison against ``float("inf")`` for the infinities — the same substitution
    discipline ``_discounted_floor`` records for ``int()`` over ``math.floor``.

    The lower guard is ``>= 1.0`` rather than ``>= 0.0``. A masked CE is a sum of NON-NEGATIVE
    terms, so ``exp(mean CE) >= 1`` is arithmetic and not convention, and the realistic mistake
    this function invites is being handed a DELTA where a PPL belongs — 0.001704 passes a
    non-negativity check happily and would yield a noise floor computed from a noise floor.
    """
    for label, value in (("a", ppl_seed_a), ("b", ppl_seed_b)):
        _prove(
            value == value and abs(value) != float("inf"),
            f"seed-{label} dialogue PPL is {value!r}, which is not finite. A non-finite "
            "perplexity is a failed measurement, and differencing one would produce a noise "
            "floor that silently admits any (c) reading whatsoever",
        )
        _prove(
            value >= 1.0,
            f"seed-{label} dialogue PPL is {value!r}, below 1.0. `masked_perplexity` returns "
            "exp(mean CE) over non-negative cross-entropies, so a value under 1.0 is "
            "arithmetically impossible for the instrument this estimator names — the likely input "
            "is a DELTA or a loss, and a floor differenced from those is a floor of a floor",
        )
    return abs(ppl_seed_a - ppl_seed_b)


def dialogue_cap(noise_floor):
    """The (c) dialogue cap, computed with the GATE's own constants — never retyped (STAT-05).

    ``V20_MASKED_DIALOGUE_VAL_PPL + MARGIN_K * noise_floor`` is the expression
    ``erasure_succeeded`` evaluates in a local at ``scripts/erasure_gate.py:245``. Both operands
    are IMPORTED from that module, so this cannot be a second cap that agrees today and drifts
    tomorrow; a committed test sweeps 101 noise floors and reads the gate's own cap back out of
    its ``(c)`` reason string, then checks the ``<=`` boundary at full precision.

    Exists so the report, the pre-run pricing above and the gate all quote ONE cap. The gate never
    returns the number it used, so without this the only way to publish it would be to write the
    expression down a second time.
    """
    return V20_MASKED_DIALOGUE_VAL_PPL + MARGIN_K * noise_floor


RETENTION_MEASUREMENT = (
    # The block size and both cap operands are RENDERED from the committed constants rather than
    # typed: this spec quotes four numbers that already exist elsewhere in the repository, and a
    # quoted number that can go stale is the failure mode the whole pin is built against. The
    # figures the estimator above quotes are typed instead, because they come from published
    # REPORTS rather than from importable constants and a test is what ties them to their source.
    "THE CALL, pinned exactly: `retention_perplexity(model, RETENTION_BIN, "
    f"{ModelConfig.block_size}, device, tok)` over "
    "`data/retention_val.bin` (2,000,572 B = 1,000,286 uint16 tokens on disk), block size "
    f"{ModelConfig.block_size} = "
    "`ModelConfig.block_size`. The policy is FROZEN (DEBT-02, `perplexity.py:148`): the dead-id "
    "mask the generation path applies is applied here too, and the unmasked v1.0 `perplexity` is "
    "not a substitute. Taken PRE-erasure and POST-erasure on the ADAPTED model, in the SAME "
    "PROCESS and under the same gate state as the draws — a second load would make the pair a "
    "comparison of two sessions rather than of one model before and after surgery.",
    "THIS IS A NEW CALL SITE WITH NO ADAPTED PRECEDENT, and the census is measured rather than "
    "asserted: `retention_perplexity` has 6 call sites across 4 modules (`finetune_smoke`, "
    "`finetune_dialog`, `finetune_ab`, `build_retention_bin`) and NONE of those four so much as "
    "imports `inject_lora` or `load_adapter`, so retention PPL has never once been measured on a "
    "LoRA-adapted model in this repository. The committed test re-runs that census by AST walk on "
    "every run, so the claim cannot go stale the first time someone adds a fifth caller.",
    "THE RETENTION HALF OF (c) IS FULLY DETERMINED AND NOTHING ABOUT IT IS OPEN. "
    f"`retention_cap = {V20_EWC_RETENTION_PPL:.6f} + {MARGIN_K} x "
    f"{V20_RETENTION_NOISE_FLOOR:.6f} = "
    f"{V20_EWC_RETENTION_PPL + MARGIN_K * V20_RETENTION_NOISE_FLOOR:.6f}`, straight out of "
    "`scripts/erasure_gate.py:246` with both operands already committed constants — unlike the "
    "dialogue half, whose noise floor this plan has to estimate. The only open question on the "
    "retention side is the MEASUREMENT, which is why this spec pins the call and not a threshold.",
)


# =============================================================================================
# ===== THE (b) NOISE FLOOR — PER FACT, NEVER POOLED, AND ITS REDUCTION PINNED TOO (D4/B5) ====
# =============================================================================================

# The seven facts condition (b) is GATED on: the eight core gated slots MINUS the target. Derived
# from the two constants above, so a target that moved cannot leave a stale seventh behind.
GATED_NONTARGET_SLOTS = tuple(slot for slot in CORE_GATED_SLOTS if slot != TARGET_SLOT)

# The two soft-tier taught slots, keyed by SLOT because both soft `fact_id`s end in their own
# value exactly as the core eight do. Written down rather than imported (the fact set is reachable
# only lazily, see the file docstring) and re-derived against `phase14_factset.SOFT_TIER_FACTS` by
# a committed test, the same discipline `TARGET_RANKING` is held to.
SOFT_TIER_SLOTS = ("favorite_color", "favorite_food")

# The replicate's seed offset. Phase 18 strides `seed_index * K`
# (`scripts/phase18_extraction.py:3640`), so its generator states occupy `[0, (max_seed_index + 1)
# * K)` above `question_seed`'s base; the replicate must start beyond ALL of them or it re-reads
# the same streams and reports a spread of exactly zero. The value is a round number well clear of
# the committed fixture's widest window rather than a tuned one — `replicate_seed_stride` proves
# the non-collision per question, so the constant does not have to be argued for.
SEED_STRIDE_OFFSET = 100000

NONTARGET_NOISE_FLOOR_ESTIMATOR = (
    "THE ESTIMATOR (D4, adopted from the research's lean and flagged as such). The (b) noise floor "
    "is a SEED-STRIDE REPLICATE of the scoring on the UNERASED adapter — the same corpus, the same "
    "adversary, the same K, a different seed stride (`SEED_STRIDE_OFFSET`) — reduced to a per-fact "
    "|drate| in the QUESTION unit. It prices how much a fact's measured recall moves when nothing "
    "about the weights moved at all, which is exactly the quantity a margin around a measured "
    "change has to be built from.",
    "THE DECLINED ALTERNATIVE, recorded as a decline and not as a deferral. A second-seed RETRAIN "
    "is more faithful to 'how much does an adapter's per-fact recall vary', because it re-draws "
    "the initialisation too — but it CONFOUNDS init noise with the erasure, and the quantity (b) "
    "prices is the erasure's effect on the other seven facts, not the trainer's run-to-run "
    "spread. Two adapters trained from different seeds differ everywhere; that is a fact about "
    "training, and charging the erasure for it would widen the margin with noise the erasure did "
    "not create.",
    "THE PRECEDENT IT FOLLOWS: `phase17_personas.REPLICATION_SEEDS` (`:169-171`) and "
    "`phase16_persistence.taught_replication` (`:1254`) — both seed registers, both DESCRIPTIVE, "
    "and neither ever a gate. This one is read by a gate, which is why its reduction is pinned "
    "below instead of being left to the caller.",
    "THE COST AND THE PAIRING. The pre-erasure per-fact rates are ALREADY COMMITTED in "
    "`results/phase18_arm_adapter-on.json` at A2 / K = 48 over the same corpus, so the replicate "
    "is ONE run and not two: 216 core questions x 48 draws = 10,368 draws, about 60 min at the "
    "measured 172 draws/min (`results/phase18_extraction_report.md:264`).",
    "PIN THE REDUCTION, NOT ONLY THE PER-FACT RULE. `erasure_succeeded` consumes "
    "`nontarget_noise_floor` as a SCALAR and computes `margin = MARGIN_K * it` "
    "(`scripts/erasure_gate.py:236`), so the reduction from seven per-fact |drate| values to one "
    "number is itself threshold-shaped, and choosing it after the seven numbers exist is exactly "
    "the failure mode pinned for `dialogue_ppl_noise_floor` one section above. The reduction is "
    "`max`, and the reason is COMMENSURABILITY: the gate already reads `max(nontarget_deltas)` on "
    "the numerator side (`:237`), so pricing the margin by the same order statistic keeps both "
    "sides of the comparison in one register.",
    "THE HONEST DIRECTION OF THAT CHOICE, recorded because this file is unamendable after 19-07. "
    "`max` is the MORE PERMISSIVE of the two reductions, NOT the conservative one. Measured "
    "through the real gate on deltas [0.01, 0.02, 0.03, 0.10]: a `max` floor gives margin "
    "0.200000 and (b) PASSES; a `mean` floor gives margin 0.080000 and (b) FAILS. `b_ok` is "
    "`worst <= 2 x floor`, and the arithmetic mean never exceeds the maximum, so a mean floor is "
    "the harder gate — STATED WITH ITS BOUND, in W1's register and not one sentence stronger: "
    "that ordering is EXACT arithmetic, while the naive `sum(v)/len(v)` can land ONE ULP above "
    "`max(v)` (measured at 2 of 200,003 swept vectors of length 1..7, both times exactly 1.0 ulp "
    "and never two, both on constant vectors). A residual of order 1e-17 against margins of order "
    "1e-2, recorded rather than claimed away. `max` is chosen for commensurability with the `max` "
    "numerator and for nothing else — a later auditor asking 'did they pick the conservative "
    "reduction?' must not be told yes by a sentence that does not survive checking.",
    "THE TWO TRAPS THE RULE SETS, both intended. ONE DESTROYED FACT FAILS (b), because the gate "
    "takes a `max` over the seven and a pooled rate can hide one destroyed fact behind six intact "
    "ones (`ROADMAP.md:518-522`). And an EMPTY `nontarget_deltas` returns INCONCLUSIVE by "
    "construction (`scripts/erasure_gate.py:253-254`), so `nontarget_deltas` RAISES on anything "
    "that is not the seven rather than returning a short list a verdict could be read off. Under "
    "STAT-06 nothing at n = 8 facts becomes a p-value here: (b) is a margin comparison, not a "
    "test, and no `sign_test_exact` call site exists on this path.",
)

SOFT_TIER_DESCRIPTIVE_READ = (
    "THE NARROWED DOMAIN, DECLARED RATHER THAN SILENT (B5). `erasure_gate`'s rule says 'every "
    "NON-TARGET taught fact' (`:107-110`) and production teaches LOCKED_FACTS + SOFT_TIER_FACTS = "
    "10 facts, so the LITERAL domain is nine non-targets (9 = 10 taught - 1 target). (b) is gated "
    "on SEVEN. The two facts left out are the soft tier, slots `favorite_color` and "
    "`favorite_food`.",
    "THE MEASURED REASON, in the register `DENOMINATOR_RULE` uses for D5's pooling departure: "
    "`results/phase18_arm_adapter-on.json` holds draws for `core_taught` and `core_held_out` ONLY "
    "— ZERO `soft` draws, verified by a tier census over the record's own draws — so the two soft "
    "facts have no committed A2 / K = 48 pre-erasure baseline to pair a delta against, and a "
    "delta computed against nothing is not a measurement. The absence is a property of the ARM "
    "RECORD and not of the fixture: `results/phase16_recall_sample.json` does carry a `soft` tier, "
    "which is what makes the post-erasure read below possible at all.",
    "WHAT IS REQUIRED INSTEAD: the two soft facts' POST-ERASURE recall is measured and PUBLISHED "
    "as DESCRIPTIVE beside the gated seven, so a destroyed soft fact is visible in the report "
    "rather than out of frame. Reported, NEVER GATED — the same posture STAT-06 requires "
    "everywhere else in this project, and the same one the soft tier already had in Phase 18.",
)


def replicate_seed_stride(seed_index, k):
    """The (b) replicate's generator base for one question — provably clear of Phase 18's.

    Phase 18 passes ``entry["seed_index"] * K`` as ``draw_all``'s ``index``
    (``scripts/phase18_extraction.py:3640``), and ``draw_all`` seeds draw *s* at
    ``question_seed(index) + s`` (``phase14_recall.py:686``), so that question's states occupy
    ``[index, index + K)``. The replicate has to land outside every one of those windows or the
    "different seed stride" is a re-read of the same streams, which would report a spread of
    exactly zero and hand (b) a margin of zero for free.

    The proof is per call rather than per constant: the offset is fixed, but the set of seed
    indices in play is DATA, so the checkable statement is that THIS question's Phase 18 window
    ends at or before the offset. Every question in the run passes through here, so checking each
    one covers exactly the set in use without this pin having to read the fixture.
    """
    _prove(
        isinstance(seed_index, int) and seed_index >= 0 and k > 0,
        f"replicate_seed_stride({seed_index!r}, {k!r}) — the seed index is a non-negative "
        "position in the committed corpus and K is the attack budget the arm record declares",
    )
    _prove(
        seed_index * k + k <= SEED_STRIDE_OFFSET,
        f"question seed_index {seed_index} at K = {k} occupies Phase 18 generator states up to "
        f"{seed_index * k + k}, which would collide with the replicate offset "
        f"{SEED_STRIDE_OFFSET}. The replicate would then re-read streams the pre-erasure scoring "
        "already consumed and report a noise floor of zero for the questions that overlap",
    )
    return SEED_STRIDE_OFFSET + seed_index * k


def _nontarget_rates(rows, label):
    """``{slot: rate}`` over exactly the seven gated non-targets, in the QUESTION unit.

    The denominator each row must carry is ``N_TARGET_QUESTIONS``. That constant is named for the
    target and is used here for the non-targets on purpose: all eight core facts carry the
    IDENTICAL 14 taught + 13 held-out census in the binding fixture, so the pooled per-core-fact
    question count is ONE number, and binding a second module-level name to it would be the
    third-name-for-one-value defect recorded at 19-03. Condition (a) and condition (b) then read
    the same unit at the same denominator, which is what lets one report print both.
    """
    by_slot = {}
    for fact_id, row in rows.items():
        _prove(
            row["slot"] not in by_slot,
            f"the {label} rows carry two facts on slot {row['slot']!r}; one non-target would then "
            "be differenced twice and another not at all",
        )
        _prove(
            row["n_questions"] == N_TARGET_QUESTIONS,
            f"{label} fact {fact_id!r} carries {row['n_questions']} questions against the pooled "
            f"per-core-fact count {N_TARGET_QUESTIONS}. `erasure_gate`'s clustering note fixes the "
            "unit as the QUESTION and never the draw, and a draw-unit denominator is K times too "
            "large — every (b) delta computed from it would be divided by the wrong number",
        )
        _prove(
            row["rate"] == row["n_answerable"] / row["n_questions"],
            f"{label} fact {fact_id!r} publishes rate {row['rate']!r} against "
            f"{row['n_answerable']}/{row['n_questions']} = "
            f"{row['n_answerable'] / row['n_questions']!r}. The rate and its own denominator "
            "disagree, which is the shape a draw rate takes when only the rate column moved",
        )
        by_slot[row["slot"]] = row["rate"]
    _prove(
        tuple(sorted(by_slot)) == tuple(sorted(GATED_NONTARGET_SLOTS)),
        f"the {label} rows cover slots {sorted(by_slot)}, which is not the seven non-target "
        f"gated slots {sorted(GATED_NONTARGET_SLOTS)}. (b) is scored per fact over exactly those "
        "seven: a short set would let `erasure_succeeded` read a `max` over the facts someone "
        "chose to submit, and the target's own slot belongs to condition (a), not to this one",
    )
    return by_slot


def nontarget_deltas(pre_rows, post_rows):
    """The (b) numerator: seven per-fact ``|drate|`` values, in ``GATED_NONTARGET_SLOTS`` order.

    ONE function serves both (b) inputs, because they are the same quantity measured against two
    different second readings: pass the SEED-STRIDE REPLICATE as ``post_rows`` and the result is
    the noise floor's seven values; pass the POST-ERASURE scoring and it is the seven the gate
    takes its ``max`` over. A second implementation for the second use would be a second rule.

    NO POOLED RETURN PATH EXISTS. There is no flag, no aggregate branch and no reduction in this
    function at all — the collapse to a scalar is `nontarget_noise_floor`, which is separately
    named, separately pinned and separately justified. A pooled rate can hide one destroyed fact
    behind six intact ones, and the whole of (b) rests on that not being expressible here.

    The delta is ABSOLUTE. A signed delta would let a fact whose recall went UP cancel one whose
    recall was destroyed, and `erasure_succeeded` takes a `max`, so the cancellation would happen
    silently inside the numerator rather than visibly in the report.

    Returns a tuple ordered by `GATED_NONTARGET_SLOTS` so a report zips the values against a
    committed constant instead of against whatever order a dict was built in.
    """
    pre = _nontarget_rates(pre_rows, "pre-erasure")
    post = _nontarget_rates(post_rows, "post-erasure")
    return tuple(abs(post[slot] - pre[slot]) for slot in GATED_NONTARGET_SLOTS)


def nontarget_noise_floor(per_fact_deltas):
    """THE REDUCTION: seven per-fact ``|drate|`` values -> the ONE scalar the gate multiplies.

    ``max``, for commensurability with the ``max`` ``erasure_succeeded`` already takes on the
    numerator side (``scripts/erasure_gate.py:236-237``) — and recorded as the MORE PERMISSIVE of
    the two candidates, not the conservative one (see ``NONTARGET_NOISE_FLOOR_ESTIMATOR``).

    This is the only committed path to that scalar. Nothing downstream may reduce the seven
    inline: a second reduction site is a second threshold, and it would be one chosen with the
    seven numbers already visible.

    An empty input RAISES rather than returning 0.0. A zero floor makes (b) clear only on a
    bit-identical model, which is a criterion nobody chose, and ``max([])`` would otherwise raise
    a bare ``ValueError`` naming neither the rule nor the run.
    """
    values = tuple(per_fact_deltas)
    _prove(
        values,
        "the (b) noise floor was asked to reduce an empty delta list — no non-target fact was "
        "scored at all. `erasure_succeeded` already turns an empty `nontarget_deltas` into "
        "INCONCLUSIVE; a floor of 0.0 here would instead make (b) clear only on a bit-identical "
        "model, which is a criterion nobody committed",
    )
    for value in values:
        _prove(
            value == value and abs(value) != float("inf") and value >= 0.0,
            f"a per-fact delta is {value!r}. Every entry is an ABSOLUTE rate difference, so it is "
            "finite and non-negative by construction; anything else means the values were not "
            "produced by `nontarget_deltas`",
        )
    return max(values)


# =============================================================================================
# ===== THE ARM RECORD, AND THE ZERO THAT MAY NOT REACH THE VERDICT WITHOUT ITS NLL =====
# =============================================================================================

# The `forbid_ids` mask sha256 every v3.0 measurement was taken under — 7,645 of 8,192 ids masked
# on the frozen tokenizer, leaving 547 live (`results/phase16_persistence_report.md:125`,
# `results/phase18_extraction_report.md:264`). Pinned as a VALUE because it is a property of the
# frozen tokenizer and is therefore knowable now; `corpus_sha256` is a REQUIRED FIELD with no
# pinned value, because the Phase 19 corpus is built by 19-05 and inventing its digest here would
# be exactly the "produce the constant early" move this pin refuses everywhere else.
FORBID_IDS_SHA256 = "79b55770f4dcfa943d7528cb04829e8d2e7dd8823b9b5450da418b4fcf3cfc28"

# The config columns that make a Phase 19 arm comparable with Phase 18's (T-19-16). REQUIRED, not
# exhaustive: `phase18_arm_adapter-on.json`'s own config carries a dozen provenance fields
# (`git_sha`, `device`, `pid`, `torch`, ...) and a hard equality here would forbid recording them.
# `k` and not `K`: Phase 18's committed config spells it lowercase and `target_rows_from_arm_record`
# already reads `arm_record["config"]["k"]`, so two spellings of the budget would be two readers.
#
# 19-05 EXTENDED this with the four sampling columns Phase 18 never recorded (`asr_rungs`,
# `stop_ids`, `sample_temperature`, `sample_top_p`). Phase 18 chose none of them — it inherits them
# by calling `phase14_recall`'s sampler — so they had to be RECONSTRUCTED from their owning modules
# to check parity at all. Requiring them here means a Phase 19 reader never has to reconstruct
# anything: `PARITY_KEYS` is a subset of this tuple, asserted by test.
ARM_CONFIG_KEYS = (
    "corpus_sha256",
    "forbid_ids_sha256",
    "k",
    "asr_rungs",
    "stop_ids",
    "sample_temperature",
    "sample_top_p",
    "seed_stride",
    "mechanism",
    "ablated_components",
)

# The dialogue PPL is the ON/OFF PAIR plus its denominator, never a single number:
# `run_collapse_control` proves the two arms scored the same `n_targets`
# (`phase14_recall.py:1442-1446`), and that proof is the evidence the delta measures the adapter
# rather than the corpus. A record carrying only the ON reading cannot carry it.
DIALOGUE_PPL_KEYS = ("adapter_on", "adapter_off", "n_targets")

# The paired baseline. Every gated quantity has its PRE-erasure twin in the same record, so the
# published movement is a delta against a measured baseline instead of an absolute number read
# against nothing — and so a (c) failure that predates the erasure stays distinguishable from one
# the erasure caused (`DIALOGUE_NOISE_FLOOR_ESTIMATOR`'s last clause).
PRE_ERASURE_KEYS = ("per_fact", "exposure", "dialogue_ppl", "retention_ppl")

# The Phase 19 arm record. Phase 18's five keys (`arm`, `config`, `draw_record_keys`, `draws`,
# `exposure`) EXTENDED — same names, same meanings — by the three quantities the gate reads and
# Phase 18 never had to record, plus `per_fact`. `per_fact` carries the question-unit rows in
# `target_rows_from_arm_record`'s shape, which is what `nontarget_deltas` already consumes and
# what makes `zero_results_have_nll(arm_record)` answerable from the artifact ALONE: a reader
# holding the JSON can recheck the flag without re-scoring anything.
ARM_RECORD_KEYS = (
    "arm",
    "config",
    "draw_record_keys",
    "draws",
    "exposure",
    "dialogue_ppl",
    "retention_ppl",
    "pre_erasure",
    "per_fact",
)


def _arm_record(**fields):
    """One Phase 19 arm record, proved against ``ARM_RECORD_KEYS`` as an ORDERED hard equality.

    The same mechanism and the same reason as ``phase18_extraction._exposure_record``
    (``:1344-1358``): keyword order is what the proof reads, so a field added, dropped or reordered
    is red on the commit that writes it rather than a ``KeyError`` in a renderer after the run has
    been spent. A Phase 19 run costs an erasure sweep plus ~60 min of draws; discovering that the
    retention reading was never recorded is not a debugging session, it is the run again.
    """
    _prove(
        tuple(fields) == ARM_RECORD_KEYS,
        f"an arm record was built with keys {tuple(fields)}, but the committed schema is "
        f"{ARM_RECORD_KEYS}. Every one of them is read by the verdict or by the report: a missing "
        "field silently converts a real result into INCONCLUSIVE, or publishes a movement with no "
        "baseline to have moved from",
    )
    missing = [key for key in ARM_CONFIG_KEYS if key not in fields["config"]]
    _prove(
        not missing,
        f"the arm config is missing {missing}. Those columns are what make this record comparable "
        f"with Phase 18's; provenance columns on top are welcome, absences are not",
    )
    _prove(
        fields["config"]["forbid_ids_sha256"] == FORBID_IDS_SHA256,
        f"the arm ran under forbid mask {fields['config']['forbid_ids_sha256']!r}, not the "
        f"{FORBID_IDS_SHA256!r} every v3.0 measurement was taken under. A different mask changes "
        "which ids the attacker can spend a draw on, so the post-erasure number would not be "
        "comparable with the Phase 18 rate it is supposed to be a movement from",
    )
    _prove(
        tuple(fields["pre_erasure"]) == PRE_ERASURE_KEYS,
        f"the pre-erasure block carries {tuple(fields['pre_erasure'])}, not {PRE_ERASURE_KEYS}. "
        "It is the paired baseline: without it every published post-erasure number is an absolute "
        "reading with nothing to be read against",
    )
    _prove(
        tuple(fields["dialogue_ppl"]) == DIALOGUE_PPL_KEYS
        and tuple(fields["pre_erasure"]["dialogue_ppl"]) == DIALOGUE_PPL_KEYS,
        f"a dialogue PPL block is {tuple(fields['dialogue_ppl'])}, not {DIALOGUE_PPL_KEYS} — the "
        "ON/OFF pair and the shared denominator are what make the reading evidence rather than a "
        "number",
    )
    return dict(fields)


def zero_result_exposure_gaps(arm_record):
    """Every reason ``zero_results_have_nll`` would return False, each naming its ``fact_id``.

    Separate from the flag ON PURPOSE. The gate reads a BOOLEAN (``erasure_gate.py:223``), and a
    ``(False, reason)`` return would be TRUTHY — ``not (False, "...")`` is ``False`` — so a caller
    passing the pair straight through would silently disarm the INCONCLUSIVE branch on exactly the
    run that needed it. The reasons live here; the flag stays a ``bool``.

    Returns an empty tuple when nothing is wrong, so the flag below is one negation and no
    interpretation.
    """
    import phase18_extraction as extraction  # LAZY — see the module docstring's no-fact-value rule

    frames = extraction.NLL_FRAMES
    reductions = extraction.NLL_REDUCTIONS
    gaps = []

    for label, exposure in (
        ("post-erasure", arm_record["exposure"]),
        ("pre-erasure", arm_record["pre_erasure"]["exposure"]),
    ):
        by_slot = {entry["slot"]: entry for entry in exposure}
        absent = [slot for slot in CORE_GATED_SLOTS if slot not in by_slot]
        if absent:
            gaps.append(
                f"the {label} exposure block covers {len(by_slot)} of the eight core slots; "
                f"{sorted(absent)} carry none. Exposure is required for ALL EIGHT so the target's "
                "movement off rank 1 is read against seven slots that did not move"
            )
        for fact_id, row in sorted(arm_record["per_fact"].items()):
            if row["n_answerable"] != 0:
                continue
            entry = by_slot.get(row["slot"])
            if entry is None:
                gaps.append(
                    f"{fact_id} scored 0 of {row['n_questions']} questions and its {label} "
                    "exposure record is missing — a zero with no teacher-forced NLL cannot "
                    "separate 'the fact is absent' from 'the probe was too weak'"
                )
                continue
            if tuple(entry) != extraction.EXPOSURE_RECORD_KEYS:
                gaps.append(
                    f"{fact_id}'s {label} exposure record carries keys {tuple(entry)}, not the "
                    f"committed {extraction.EXPOSURE_RECORD_KEYS}"
                )
            for frame in frames:
                if frame not in entry["nll"]:
                    gaps.append(
                        f"{fact_id}'s {label} exposure record has no {frame!r} NLL. All "
                        f"{len(frames) * len(reductions)} frame x reduction values are REQUIRED "
                        "columns even though the gate reads one pair — six published and one read "
                        "is what makes a post-null switch visible instead of convenient"
                    )
                    continue
                for reduction in reductions:
                    value = entry["nll"][frame].get(reduction)
                    if value is None or value != value or abs(value) == float("inf"):
                        gaps.append(
                            f"{fact_id}'s {label} {frame}/{reduction} NLL is {value!r}, which is "
                            "not finite. Phase 18's bar is 48 finite NLLs per arm "
                            "(18-VERIFICATION.md:60) and a null beside a zero recall IS the "
                            "unmeasured case this clause exists to refuse"
                        )
    return tuple(gaps)


def zero_results_have_nll(arm_record):
    """``erasure_gate.py:223-227``'s clause, made structural. Returns a plain ``bool``.

    ITS WHOLE PURPOSE is to separate "the fact is absent" from "the probe was too weak" — and A
    SUCCESSFUL ERASURE PRODUCES EXACTLY THE ZERO THAT TRIGGERS IT. The gate short-circuits to
    INCONCLUSIVE when ``target_successes == 0`` and this flag is False, so on the phase's success
    path this one boolean is the difference between a publishable result and no result at all.
    That is why it is computed from the record rather than set by whoever ran the arm.

    MEASURED IN THE SAME PASS AND UNDER THE SAME GATE STATE AS THE DRAWS. Phase 18 takes exposure
    inside the generation context manager (``scripts/phase18_extraction.py:3696-3702``) for the
    reason this flag depends on: measured in a second process, "absent" and "weak" become
    separable only across two loads of two models, and the pairing that makes the NLL interpretable
    is gone. The pre-erasure block is required in the same schema for the same reason — an
    exposure rank published with no baseline is a number with nothing to have moved from.

    THE Q7.5 RESIDUAL, RECORDED AS A MEASURED COLUMN RATHER THAN AN ASSUMPTION. The tokenizer
    forbids 7,645 of 8,192 ids at sampling, so the model's generative surface is only 547 live ids,
    and a post-erasure zero could in principle be a DECODING ARTIFACT rather than an erasure. Phase
    18 measured that mask's SIGN and published it: masking dead ids makes the attacker STRONGER,
    because ``tok.decode([dead_id])`` raises and the mask removes unusable draws rather than usable
    ones (``results/phase18_extraction_report.md:244``; ``scripts/demo_app.py:86``,
    ``scripts/evaluate.py:116``). So the mask cannot manufacture a false (a) pass by suppressing
    the target string. What remains is the decoding-artifact reading, and it is answered by THE
    SAME INSTRUMENT this flag requires: the exposure rank and the six teacher-forced NLLs are
    computed by forced scoring, not by decoding, so they are measurable exactly where generation
    produces nothing.
    """
    return not zero_result_exposure_gaps(arm_record)


# =============================================================================================
# ===== COMPARABILITY WITH PHASE 18 — asserted against Phase 18's own values (Q7.8/T-19-20) ====
# =============================================================================================

# The committed Phase 18 artifacts the parity check reads. The Phase 19 target arms REUSE
# `results/phase18_corpus.json` VERBATIM rather than rebuilding it — that is what makes the
# post-erasure numbers directly comparable to the committed `adapter-on` per-fact rates, and it
# removes the whole class of drift Q7.8 describes at the source instead of detecting it afterwards.
PHASE18_CORPUS_PATH = _REPO_ROOT / "results" / "phase18_corpus.json"
PHASE18_ARM_RECORD_PATH = _REPO_ROOT / "results" / "phase18_arm_adapter-on.json"

# The eight parameters that decide whether a Phase 19 rate may be compared with Phase 18's 92/104.
# ORDERED, and `assert_phase18_parity` raises on the FIRST offender in this order, so the abort
# names one key rather than a set a reader has to diff.
PARITY_KEYS = (
    "corpus_sha256",
    "forbid_ids_sha256",
    "k",
    "asr_rungs",
    "stop_ids",
    "sample_temperature",
    "sample_top_p",
    "seed_stride",
)

# MEASURED, not assumed: Phase 18's own committed config carries FOUR of the eight
# (`results/phase18_arm_adapter-on.json`). The other four are absent because Phase 18 never chose
# them — it reaches the sampler through `phase14_recall.draw_all` / `complete_question`, which read
# `SAMPLE_TEMPERATURE`, `SAMPLE_TOP_P` and `STOP_IDS` as module constants, and no Phase 18 call site
# overrides any of them (AST census, `tests/test_phase19_erasure.py`). A Phase 19 arm RECORDS all
# eight — `ARM_CONFIG_KEYS` requires them — precisely so this reconstruction is never needed twice.
PHASE18_RECORDED_PARITY_KEYS = ("corpus_sha256", "forbid_ids_sha256", "k", "seed_stride")
PHASE18_INHERITED_PARITY_KEYS = ("asr_rungs", "stop_ids", "sample_temperature", "sample_top_p")


def phase18_parity_values():
    """The eight expected values, each IMPORTED from its owning module or RECOMPUTED.

    Never retyped here. A constant that moves upstream turns this red instead of diverging
    silently, which is the whole difference between a parity check and a second set of numbers.

    ``corpus_sha256`` is recomputed from ``results/phase18_corpus.json`` through the committed
    ``canonical_json`` + ``corpus_sha256`` pair (``phase18_extraction.py:746,758``), never compared
    against a pasted hex string. ``seed_stride`` is read from Phase 18's OWN committed record: the
    string lives inside a dict literal in a function there (``:3714``) and is not importable, and
    the authority for "the stride Phase 18 actually ran" is Phase 18's artifact rather than a
    sentence retyped here.
    """
    import phase14_recall as recall  # LAZY — see the module docstring's no-fact-value rule
    import phase18_extraction as extraction  # LAZY — same rule

    corpus = json.loads(PHASE18_CORPUS_PATH.read_text(encoding="utf-8"))
    record = json.loads(PHASE18_ARM_RECORD_PATH.read_text(encoding="utf-8"))
    return {
        "corpus_sha256": extraction.corpus_sha256(corpus),
        "forbid_ids_sha256": FORBID_IDS_SHA256,
        "k": extraction.K,
        "asr_rungs": extraction.ASR_RUNGS,
        "stop_ids": recall.STOP_IDS,
        "sample_temperature": recall.SAMPLE_TEMPERATURE,
        "sample_top_p": recall.SAMPLE_TOP_P,
        "seed_stride": record["config"]["seed_stride"],
    }


def phase18_parity_config(arm_record):
    """Phase 18's own eight-key comparability block: four RECORDED, four INHERITED BY CALL.

    Exists because Phase 18 evidences its pairing by DIGEST and by two distinct pids rather than by
    assertion (``results/phase18_extraction_report.md:260-265``), and its config therefore records
    only the four parameters it explicitly chose. The four it never chose are reconstructed from the
    modules that own them, and the reconstruction is only honest because a committed AST census
    proves no Phase 18 sampler call site overrides them.

    The four RECORDED values are read out of the passed record, so a record that ran at a different
    budget or under a different mask cannot be completed into a config that passes.

    Phase 19 records the same evidence and then some: all eight columns in every arm config
    (``ARM_CONFIG_KEYS``), with the digest and the pid carried on top as provenance, so the pairing
    is auditable from the artifact alone AND asserted by ``assert_phase18_parity`` before the run.
    """
    config = arm_record["config"]
    missing = [key for key in PHASE18_RECORDED_PARITY_KEYS if key not in config]
    _prove(
        not missing,
        f"the Phase 18 arm record is missing {missing} from its own config. Those are the four "
        "comparability parameters Phase 18 DID record; without them there is nothing to "
        "reconstruct the pairing from and the comparison against 92/104 has no basis",
    )
    inherited = phase18_parity_values()
    completed = {key: config[key] for key in PHASE18_RECORDED_PARITY_KEYS}
    completed.update({key: inherited[key] for key in PHASE18_INHERITED_PARITY_KEYS})
    return {key: completed[key] for key in PARITY_KEYS}


def _parity_equal(want, got):
    """Compare by the EXPECTED value's own semantics, and never raise while doing it.

    A JSON round trip turns a tuple and a frozenset into lists, and the configs this is asserted
    against are read back out of artifacts. So a set is compared AS A SET (order carries no
    meaning for ``stop_ids``) and a tuple AS AN ORDERED TUPLE (``asr_rungs`` is a ladder, and a
    reordered ladder is a different ladder). A wrong TYPE returns False rather than raising, so the
    abort below names the key instead of surfacing a ``TypeError`` from inside a comparison.
    """
    if isinstance(want, (set, frozenset)):
        return isinstance(got, (list, tuple, set, frozenset)) and set(got) == set(want)
    if isinstance(want, tuple):
        return isinstance(got, (list, tuple)) and tuple(got) == want
    return got == want


def assert_phase18_parity(config):
    """Every comparability parameter equals Phase 18's own value, or ``SystemExit`` naming the key.

    A MISSING key raises. An absent parameter must not read as agreement — that is how a run ends
    up compared against a baseline it never shared, and it is the failure mode Q7.8 names.

    Assert this on the arms whose rates are compared with Phase 18's committed per-fact rates. It
    is deliberately NOT for the (b) noise-floor REPLICATE, whose stride is offset ON PURPOSE so its
    seed windows cannot collide with Phase 18's (``replicate_seed_stride``, ``SEED_STRIDE_OFFSET``);
    that arm is compared against the pre-erasure reading in its own run, not against Phase 18. Its
    config still RECORDS all eight columns, because recording which stride an arm ran under and
    asserting it matches another phase's are different acts, and Phase 18 did neither.

    Returns the config it accepted, so a caller can write the audited block straight into the
    record instead of assembling a second copy beside it.
    """
    expected = phase18_parity_values()
    for key in PARITY_KEYS:
        _prove(
            key in config,
            f"the arm config does not record {key!r}. Every one of {PARITY_KEYS} decides whether "
            "this run's rate may be compared with Phase 18's committed 92/104, and an ABSENT key "
            "must not read as agreement — silence is the one answer a parity check may not accept",
        )
        _prove(
            _parity_equal(expected[key], config[key]),
            f"parity key {key!r}: this arm ran under {config[key]!r}, Phase 18 under "
            f"{expected[key]!r}. A different corpus, mask, budget, ladder, stop set, sampling "
            "parameter or seed stride makes the post-erasure number incomparable with the "
            "pre-erasure rate it is supposed to be a movement from, and the comparison is then "
            "void rather than merely noisy",
        )
    return config


# =============================================================================================
# ===== THE REPRESENTATIONAL READ — DESCRIPTIVE, AND STRUCTURALLY UNABLE TO BECOME A GATE =====
# =============================================================================================

REPRESENTATIONAL_READ_LABEL = (
    "DESCRIPTIVE, EXPLICITLY NOT GATED (`scripts/erasure_gate.py:118-122`). Reported with its "
    "denominators and never converted into a pass/fail. At n=8 facts and n=3 personas the sample "
    "cannot support a threshold, and gating what the sample cannot support is treated as a DEFECT "
    "in this project, not as extra rigour. A second `sign_test_exact` call site IS a second "
    "hypothesis family and would reprice Holm to carry a descriptive statistic — which is why "
    "`tests/test_phase19_erasure.py::test_representational_read_is_not_gated` scans these three "
    "functions by AST rather than trusting this sentence."
)

# The functions the guard scans, NAMED so a rename cannot silently escape it. A dangling entry
# FAILS the guard rather than quietly excusing a missing scan target — `DRAW_ALL_ASSERTED_BY`'s
# discipline (`tests/test_phase14_scoring.py:576-582`).
#
# They are defined HERE, inside the pin, and not at 19-14 where they are first CALLED. Adding them
# later would be a commit to this file after `results/phase19_cal_corpus.json` exists, which turns
# the ancestry guard permanently red — the manoeuvre this whole phase is built to make impossible.
# All three are thin and take their inputs as PARAMETERS, so no adapter path, no fact material and
# no checkpoint load reaches this pin's import surface.
DESCRIPTIVE_ONLY_FUNCTIONS = ("delta_w_cells", "delta_w_cosine", "fisher_overlap")


def delta_w_cells(adapter, w0_state):
    """Per-cell ``dW`` — the committed MAGNITUDE read and the DIRECTION a cosine needs.

    ``extract_deltas.adapter_cells`` (``:174``) returns a per-cell Frobenius-norm RATIO, i.e. a
    SCALAR, so a per-cell cosine cannot be taken over its output at all. The ratio is therefore
    DELEGATED to it — never recomputed — while the direction is built from the identity this pin
    already committed in ``MECHANISM_RULE``: ``dW = scale * (B @ A)``, the same expression
    ``ablate_components`` operates on. The two are tied together by test:
    ``||delta||_F / ||W0||_F`` must equal the ratio ``adapter_cells`` returned for that cell, so the
    duplication cannot drift into describing two different deltas.

    ``scale`` is ``alpha / r`` READ FROM THE ARTIFACT and never recomputed from a live module —
    ``lora/layer.py:27`` names ``LoRALinear.scale`` the single source of truth and PITFALLS P3
    forbids recomputing it; ``extract_deltas.py:295`` reads it the same way, and
    ``load_adapter_weights`` audits a loaded adapter against exactly these two fields
    (``inject.py:119-129``).

    Takes the ``export_adapter``-shaped ARTIFACT, the same object ``ablate_components`` takes and
    returns, so an erased adapter can be passed straight in without unwrapping.

    ponytail: the returned deltas are dense fp64 (~85 MB for the production adapter). 19-14 is the
    only caller and reads two adapters at once; if that ever needs to be three, stream per cell
    instead of materialising the dict.
    """
    lora_config = adapter["lora_config"]
    scale = lora_config["alpha"] / lora_config["r"]
    tensors = adapter["adapter"]
    ratios = extract_deltas.adapter_cells(tensors, scale, w0_state)

    cells = {}
    for layer, projection, key in extract_deltas.KEYS:
        prefix = key[: -len(".weight")]
        a = tensors[f"{prefix}.lora_A"].to(torch.float64)  # (r, in)
        b = tensors[f"{prefix}.lora_B"].to(torch.float64)  # (out, r)
        cells[(layer, projection)] = {
            "ratio": ratios[(layer, projection)],
            "delta": (scale * (b @ a)).reshape(-1),
        }
    return cells


def delta_w_cosine(cells_a, cells_b):
    """Per-cell cosine between two adapters' ``dW``, in fp64 — a DICT, never a scalar summary.

    Keyed by ``(layer, projection)``, one entry per cell, because a mean over 36 cells is exactly
    the figure a caption reaches for and it would hide the cell where the two adapters diverged.
    The ``continual/fisher.py`` statistics discipline: fp64 throughout.

    ``None`` where either side's delta is exactly zero. A fully ablated cell has NO direction, and
    writing ``0.0`` there would publish it as ORTHOGONAL — a claim the arithmetic does not make.
    ``None`` and a number are deliberately different in the same way ``_verdict.recorded_verdict``
    keeps ``None`` and an empty body different.

    See ``REPRESENTATIONAL_READ_LABEL``: this is reported, never gated.
    """
    _prove(
        set(cells_a) == set(cells_b),
        f"the two cell sets differ: {sorted(set(cells_a) ^ set(cells_b))}. A cosine is only "
        "defined cell-for-cell, and silently intersecting them would publish a read over whichever "
        "cells the two adapters happened to share",
    )
    cosines = {}
    for key in cells_a:
        a = cells_a[key]["delta"]
        b = cells_b[key]["delta"]
        norms = float(torch.linalg.norm(a)) * float(torch.linalg.norm(b))
        cosines[key] = None if norms == 0.0 else float(torch.dot(a, b)) / norms
    return cosines


def fisher_overlap(fisher_cells, ablated_addresses):
    """Fisher mass in the ABLATED addresses against mass in the rest. Both sides, both denominators.

    ``fisher_cells`` is the ALREADY-REDUCED per-cell dict from ``extract_deltas.fisher_cells``
    (``:199``), whose reduction is a per-cell MEAN (``FISHER_AGGREGATE``, ``:104-109``): the cache
    is mean-normalized, so a per-cell mean reads directly as "x the importance of an average
    parameter" and a SUM would confound importance with tensor size.

    ``ablated_addresses`` are ``component_index()``-shaped ``(layer, projection, j)`` triples.

    GRANULARITY, stated rather than left to be inferred: the Fisher cache is per PARAMETER and
    reduces to per CELL, so it carries no rank-1 resolution at all. A cell counts as ablated when
    ANY of its ``PRODUCTION_RANK`` components was zeroed, and this read therefore cannot attribute
    mass to a component. That is a property of the cache, not of the ablation, and it travels
    inside the returned dict so no renderer can publish the numbers without it.

    No ratio is returned. "Mass in the ablated addresses against mass in the rest" is both sides
    side by side; dividing two means-of-means is the single scalar a caption would quote, and it
    would silently weight a 384x384 attention cell equally with a 1536x384 MLP cell.

    See ``REPRESENTATIONAL_READ_LABEL``: this is reported, never gated.
    """
    known = {(layer, projection) for layer, projection, _key in extract_deltas.KEYS}
    _prove(
        set(fisher_cells) == known,
        f"the Fisher cell dict covers {len(fisher_cells)} cells, not the committed "
        f"{len(known)}-cell enumeration. `extract_deltas.fisher_cells` returns exactly those keys, "
        "so a different set means the input was reduced somewhere else",
    )
    ablated = []
    for address in ablated_addresses:
        layer, projection, _j = address
        _prove(
            (layer, projection) in known,
            f"ablated address {address!r} names a projection outside the committed wrap set. The "
            "overlap would then be taken over a surface the adapter does not have",
        )
        if (layer, projection) not in ablated:
            ablated.append((layer, projection))

    ablated = tuple(sorted(ablated))
    preserved = tuple(sorted(known - set(ablated)))
    _prove(
        ablated and preserved,
        f"degenerate partition: {len(ablated)} ablated cells and {len(preserved)} preserved. An "
        "overlap needs both sides to have a denominator — with one side empty there is nothing to "
        "report the other side AGAINST, and a mean over zero cells is not a small number",
    )
    return {
        "ablated_cells": ablated,
        "preserved_cells": preserved,
        "n_ablated_cells": len(ablated),
        "n_preserved_cells": len(preserved),
        "ablated_mean": sum(fisher_cells[key] for key in ablated) / len(ablated),
        "preserved_mean": sum(fisher_cells[key] for key in preserved) / len(preserved),
        "reduction": extract_deltas.FISHER_AGGREGATE,
        # `PRODUCTION_RANK` is deliberately NOT interpolated here. The guard over
        # `DESCRIPTIVE_ONLY_FUNCTIONS` forbids these functions reading ANY module-level number, and
        # that scan is worth more than the digit: `component_index` already derives the rank and
        # `N_COMPONENTS` already publishes the product.
        "granularity": (
            "per CELL, not per component: the Fisher cache reduces to (layer, projection) and "
            "carries no rank-1 resolution, so a cell counts as ablated when ANY of its rank-1 "
            "components was zeroed"
        ),
        "label": REPRESENTATIONAL_READ_LABEL,
    }


# =============================================================================================
# ===== THE ONE VERDICT PATH — the committed rule is CALLED, never re-implemented (STAT-05) ====
# =============================================================================================


def render_verdict(**gate_inputs):
    """THE single (a)/(b)/(c) evaluation in Phase 19. Calls ``erasure_succeeded`` and nothing else.

    The whole phase is worthless if a second evaluation exists anywhere to disagree with the
    committed one, so this is the only call site and
    ``tests/test_phase19_erasure.py::test_verdict_is_called_never_reimplemented`` is what keeps it
    the only one: a second call, a local re-definition, or any of the four v2.0 baselines retyped
    as a numeric literal in this file all turn that scan red.

    The required argument names are READ OFF THE GATE rather than written down here, so this driver
    does not hold its own copy of the rule's signature. A missing or misspelled input is named
    BEFORE the call instead of surfacing as a ``TypeError`` at the end of a spent run.

    Returns the verdict, its reasons and the inputs it was computed from, so a report publishes the
    number the gate actually read instead of a second copy assembled beside it.
    """
    import inspect  # stdlib, and needed only here — the rule's own signature is the schema

    required = tuple(inspect.getfullargspec(erasure_succeeded).kwonlyargs)
    _prove(
        tuple(sorted(gate_inputs)) == tuple(sorted(required)),
        f"the verdict was asked for with {tuple(sorted(gate_inputs))}, but the committed rule "
        f"takes {required}. Every one of those is keyword-only precisely so a caller cannot "
        "transpose two counts, and a missing one would abort after the erasure sweep and the "
        "draws had already been spent",
    )
    verdict, reasons = erasure_succeeded(**gate_inputs)
    _prove(
        verdict in VERDICTS,
        f"the gate returned {verdict!r}, which is not one of {VERDICTS}. INCONCLUSIVE is a real "
        "outcome in that domain and a fourth value would be a verdict nobody pre-registered",
    )
    return {"verdict": verdict, "reasons": tuple(reasons), "inputs": dict(gate_inputs)}


# =============================================================================================
# ===== THE REPORT TEXT, THE SHIP-DECISION MARKER PAIR AND THE CLOBBER GUARD (D8/T-19-21/22) ==
# =============================================================================================

ERASURE_REPORT_PATH = _REPO_ROOT / "results" / "phase19_erasure_report.md"

# The marker PAIR. BOTH halves name Phase 19, and a committed test asserts neither mentions Phase
# 18 — the entire reason `scripts/_addendum.py` makes them required keywords is that Phase 18's twin
# let one half travel with the caller and hard-coded the other, so appending through it wrote a
# Phase 18 provenance sentence into a document that was not Phase 18's
# (`scripts/_addendum.py:13-27`).
#
# Deliberately OUTSIDE the `## Verdict` section, for `phase18_extraction.py:3790-3794`'s reason:
# PENDING token inside that section would be part of the recorded verdict forever.
ERASURE_SHIP_PENDING_LINE = "**Phase 19 ship decision: not yet recorded.**"

ERASURE_SHIP_RECORDED_LINE = (
    "**Phase 19 ship decision: recorded in the dated continuation at the end of this file.**"
)

# The closed decision set and the line shape a continuation must carry for the marker to flip.
# A substring check for "ship" would NOT have caught Phase 18's W2: the grep that found the defect
# reports that ship/no-ship language appeared in the report already — as the section heading and
# the pointer line — while no decision had been written (`18-VERIFICATION.md:226-250`). So the
# decision is a pinned LINE from a closed set, not a word.
ERASURE_SHIP_DECISIONS = ("SHIP", "DO NOT SHIP")
ERASURE_SHIP_DECISION_PREFIX = "Phase 19 ship decision: "

_DATED_CONTINUATION = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_BARE_ZERO_PERCENT = re.compile(r"\b0(\.0+)?%")

D8_PUBLICATION_POSTURE = (
    "D8, LOCKED BEFORE THE NUMBER EXISTS. If ablating enough to erase the target also destroys "
    'non-targets, the finding is "selective erasure is not selective at 331,776 parameters" and '
    "it SHIPS UNSOFTENED, in the register Phase 18 shipped `LEAKAGE_DEMONSTRATED`. The collateral "
    "curve is publishable whichever shape it has, and if it is a cliff, the cliff IS the finding — "
    "the same register Phase 13 used for its 79/70 role-token leakage and Phase 16 for its "
    "capability-deficit branch. Decided now so the framing cannot be written after the number.",
    "Q7.4, THE OTHER BRANCH, FRAMED HERE TOO. If the fact falls out on the FIRST ablation, that is "
    "a MEASUREMENT and not an absence, and the phase does not read as a non-result. What makes "
    '"trivial" a result is the PAIRED INSTRUMENTS: the target\'s exposure rank moves from rank 1 '
    "to rank k while the non-targets stay at rank 1 and capability is unchanged. A single easy "
    "number with no paired instrument beside it would be an absence; three instruments moving in "
    "three different directions is a measurement. Written before the answer is known, for the same "
    "reason `licensed_headline` was written before Phase 16's comparisons were scored.",
    "NEITHER BRANCH MAY BE SOFTENED IN THE RENDERING. The verdict published is the one the "
    "committed `erasure_succeeded` returned; the reasons published are the ones it returned with "
    "it; and the pre-erasure readings are printed BESIDE the post-erasure ones in every table so a "
    "(c) failure that predates the erasure stays distinguishable from one the erasure caused.",
)


def assert_erasure_report_not_clobbered(path=ERASURE_REPORT_PATH):
    """A recorded verdict is committed evidence. Refuse to overwrite it — FIRST, and cheapest.

    Anchored on the SECTION through ``_verdict.recorded_verdict``, the ONE shared copy, and never
    on a split of the heading literal taking the last element — the 15-04 CR-02 defect, which read
    a prose mention of the heading as a recorded verdict and made ``--force`` the only way through.
    The forbidden call is deliberately not spelled anywhere in this file so a ``grep`` for it stays
    a usable guard rather than matching the paragraph that rejects it.

    THERE IS NO OVERRIDE FLAG. A flag that disables this becomes routine, and an operator who
    passes it routinely passes it after a verdict HAS been recorded — at which point the guard
    destroys exactly the evidence it exists to protect. If the report genuinely must be
    regenerated, the honest path is DELETING it in a reviewed commit, so the removal is visible in
    the diff.

    Three refusals with three different messages, because they are three different situations:

    * no ``## Verdict`` section at all (``recorded_verdict`` returns ``None``) — this is not this
      writer's output, and blindly overwriting a file it did not produce is its own defect;
    * an EMPTY body — an interrupted render, recoverable only by the same reviewed deletion;
    * a body — a verdict is recorded, and a re-render would take it and every hand-appended
      continuation beside it (19-16's D3 diagnosis lands there).

    Returns ``None`` when there is nothing to clobber, so the FIRST render is not refused.
    """
    path = pathlib.Path(path)
    if not path.exists():
        return None

    body = _verdict.recorded_verdict(path.read_text(encoding="utf-8"))
    _prove(
        body is not None,
        f"{path} exists but carries no `## Verdict` section, so it is not this writer's output. "
        "Refusing rather than overwriting: a file this renderer did not produce is somebody "
        "else's document, and there is no force flag — delete it in a reviewed commit if it "
        "genuinely must go",
    )
    _prove(
        not body.strip(),
        f"{path} already carries a RECORDED `## Verdict`. Re-rendering rewrites the whole file and "
        "would destroy it along with every dated continuation appended beside it — including the "
        "D3 condition-(c) diagnosis. There is no force flag; the recovery is deleting the file in "
        "a reviewed commit so the removal is visible in the diff",
    )
    raise SystemExit(
        f"[phase19_erasure] PROOF FAILED: {path} carries a `## Verdict` section with an EMPTY "
        "body — an INTERRUPTED render, not a finished one and not another writer's file. That is "
        "still not a licence to overwrite: delete it in a reviewed commit and re-drive, so the "
        "half-written artifact is visible in the diff rather than silently replaced"
    )


def _rate_row(successes, n_questions, n_draws):
    """STAT-02's single reporting shape — IMPORTED from Phase 16, never re-derived here.

    Carries the rate over QUESTIONS with both denominators, the Wilson upper bound labelled as the
    independence-assuming width, and — only at zero successes — the ``3/n`` ceiling beside it. A
    bare zero percentage is impossible by construction, which is why every rate this report prints
    goes through it.
    """
    import phase16_persistence as persistence  # LAZY — see the module docstring's rule

    return persistence.report_proportion(successes, n_questions, n_draws)["formatted"]


def render_report(
    *,
    verdict,
    target,
    cal_rate,
    nontargets,
    capability,
    representational,
    provenance,
    path=ERASURE_REPORT_PATH,
):
    """Write ``results/phase19_erasure_report.md`` and return its text.

    ``verdict`` is ``render_verdict``'s record, so every gated number below is READ OUT OF THE
    INPUTS THE GATE ACTUALLY SAW rather than passed in a second time beside it. The floor's two
    directions and its branch are DERIVED here from ``cal_rate`` for the same reason. The only
    quantities that arrive independently are the ones the gate never sees: the raw draw
    denominators, the per-fact non-target rows, the PRE-erasure capability pair and the
    representational read.

    Two proofs run over the RENDERED TEXT before a byte is written, because a source-level scan
    structurally cannot see a number a format string produced — which is exactly how a bare ``0%``
    reaches a published report (``phase18_extraction.py:4276-4285``).

    ``path`` is a parameter so the renderer is exercisable against a temporary file; the clobber
    refusal runs on whichever path is actually being written, as this function's FIRST statement
    rather than as a step an operator has to remember.
    """
    assert_erasure_report_not_clobbered(path)

    inputs = verdict["inputs"]
    n_questions = inputs["target_questions"]
    floor = lock_erasure_floor(cal_rate)
    upper = wilson_upper_bound(inputs["target_successes"], n_questions)
    cap = dialogue_cap(inputs["dialogue_ppl_noise_floor"])
    retention_cap = V20_EWC_RETENTION_PPL + MARGIN_K * V20_RETENTION_NOISE_FLOOR

    lines = [
        "# Phase 19 — Selective Memory Erasure",
        "",
        f"Mechanism `{MECHANISM_ID}` over {N_COMPONENTS} addressable rank-1 components. Success "
        "criteria are INHERITED from `scripts/erasure_gate.py`, committed `23a830c` on 2026-08-12, "
        "before Phase 16 ran; this report re-authors none of them.",
        "",
        "## Verdict",
        "",
        "### 1. The verdict",
        "",
        f"**{verdict['verdict']}** — returned by the committed `erasure_succeeded`, with its own "
        "reasons, neither recomputed nor paraphrased here:",
        "",
    ]
    lines += [f"- {reason}" for reason in verdict["reasons"]]
    lines += [
        "",
        "### 2. Condition (a) — target forgotten",
        "",
        f"- post-erasure: {_rate_row(inputs['target_successes'], n_questions, target['n_draws'])}",
        f"- pre-erasure:  "
        f"{_rate_row(target['pre_successes'], target['pre_questions'], target['pre_draws'])}",
        f"- the gate reads the WILSON upper bound: {upper:.6f} against the calibrated floor "
        f"{inputs['target_floor']:.6f} over {n_questions} questions.",
        f"- rule-of-three ceiling at this denominator: "
        f"{rule_of_three(n_questions):.6f}. Published BESIDE the Wilson bound, never instead of "
        "it, so the quieter of the two cannot be chosen after the fact.",
        "",
        "### 3. Condition (b) — non-targets preserved",
        "",
        "Per fact, with each fact's own denominator. NEVER pooled: a single rate can hide one "
        "destroyed fact behind six intact ones, which is the whole reason (b) is written per fact.",
        "",
        "| slot | pre-erasure | post-erasure | \\|Δrate\\| |",
        "| --- | --- | --- | --- |",
    ]
    deltas = dict(zip(GATED_NONTARGET_SLOTS, inputs["nontarget_deltas"], strict=True))
    for row in nontargets:
        slot = row["slot"]
        lines.append(
            f"| `{slot}` "
            f"| {_rate_row(row['pre_successes'], row['pre_questions'], row['pre_draws'])} "
            f"| {_rate_row(row['post_successes'], row['post_questions'], row['post_draws'])} "
            f"| {deltas[slot]:.6f} |"
        )
    lines += [
        "",
        f"Reduced to the one scalar the gate multiplies by `max` (`nontarget_noise_floor`): "
        f"{inputs['nontarget_noise_floor']:.6f}, against the margin k={MARGIN_K} the whole project "
        "calibrates every gate with.",
        "",
        "### 4. Condition (c) — capability preserved",
        "",
        "| reading | pre-erasure | post-erasure | cap |",
        "| --- | --- | --- | --- |",
        f"| masked dialogue val PPL | {capability['dialogue_ppl']:.4f} | "
        f"{inputs['dialogue_ppl']:.4f} | {cap:.6f} |",
        f"| retention PPL | {capability['retention_ppl']:.6f} | "
        f"{inputs['retention_ppl']:.6f} | {retention_cap:.6f} |",
        "",
        f"The dialogue cap is `V20_MASKED_DIALOGUE_VAL_PPL + k x noise floor` at a MEASURED "
        f"noise floor of {inputs['dialogue_ppl_noise_floor']:.6f} "
        f"(`DIALOGUE_NOISE_FLOOR_ESTIMATOR`, seeds {DIALOGUE_NOISE_FLOOR_SEEDS}). Pre- and "
        "post-erasure are printed side by side because a (c) failure that PREDATES the erasure and "
        "one the erasure CAUSED are different findings, and printing both numbers is the only "
        "thing that separates them. A floor large enough to admit the pre-erasure reading is not a "
        "better result; it is a wider ruler.",
        "",
        "### 5. The (a) floor — both directions and the branch that bound",
        "",
        f"- blind calibration rate: {cal_rate!r}",
        f"- mirrored floor, the one the gate read (`lock_erasure_floor`): {floor:.6f}",
        f"- Phase 14's operator applied literally (`literal_phase14_floor`, never read by a gate): "
        f"{literal_phase14_floor(cal_rate)!r}",
        f"- branch that produced it (`floor_branch`): **{floor_branch(cal_rate)}**",
        "",
        f"Both directions are printed so a reader sees the CHOICE rather than inferring it (D2). "
        f"When the branch is `reachability-min` the floor equals the best bound a PERFECT ERASURE "
        f"can attain over {n_questions} questions "
        f"({BEST_ATTAINABLE_TARGET_BOUND:.6f}), and (a) then clears ONLY on a perfect erasure — "
        "that is the intended severity, named here rather than left to be re-derived.",
        "",
        "### 6. Representational consistency",
        "",
        REPRESENTATIONAL_READ_LABEL,
        "",
        "| (layer, projection) | ΔW cosine |",
        "| --- | --- |",
    ]
    for key, cosine in representational["cosine"].items():
        rendered = (
            "undefined (zero ΔW in this cell — NOT orthogonal)"
            if cosine is None
            else (f"{cosine:.6f}")
        )
        lines.append(f"| {key} | {rendered} |")
    fisher = representational["fisher"]
    lines += [
        "",
        f"Fisher mass, {fisher['reduction']}-reduced per cell, {fisher['granularity']}: "
        f"{fisher['ablated_mean']:.6f} over {fisher['n_ablated_cells']} ablated cell(s) against "
        f"{fisher['preserved_mean']:.6f} over {fisher['n_preserved_cells']} preserved. Both sides "
        "with their own denominators; no ratio is published.",
        "",
        "## Publication posture",
        "",
    ]
    lines += [f"{clause}\n" for clause in D8_PUBLICATION_POSTURE]
    lines += [
        "## Comparability with Phase 18",
        "",
        "| parameter | value |",
        "| --- | --- |",
    ]
    lines += [
        f"| `{key}` | `{provenance['parity'][key]}` |"
        for key in PARITY_KEYS
        if key in provenance["parity"]
    ]
    lines += [
        "",
        f"Asserted by `assert_phase18_parity` against Phase 18's own committed values, not "
        f"compared by eye. Run provenance: git `{provenance['git_sha']}`, device "
        f"`{provenance['device']}`.",
        "",
        "## Ship Decision",
        "",
        ERASURE_SHIP_PENDING_LINE,
        "",
    ]

    text = "\n".join(lines)
    _prove(
        len(_verdict.VERDICT_SECTION.findall(text)) == 1,
        "the rendered report does not carry EXACTLY one `## Verdict` section. At zero the clobber "
        "guard has nothing to anchor on and a later run overwrites this evidence in silence; at "
        "more than one the guard reads the first and a second could disagree with it",
    )
    _prove(
        text.count(ERASURE_SHIP_PENDING_LINE) == 1,
        f"the rendered report carries {text.count(ERASURE_SHIP_PENDING_LINE)} ship-decision "
        "placeholders. `append_addendum` replaces EXACTLY one, so the renderer must make that "
        "satisfiable BY CONSTRUCTION — zero and two both leave the continuation writer with no "
        "unambiguous line and turn an append into a choice",
    )
    _prove(
        _BARE_ZERO_PERCENT.search(text) is None,
        "the rendered report contains a bare zero percentage — STAT-02 forbids it in any committed "
        "report or figure, because a bare zero states a certainty the sample does not have. This "
        "proof runs on the PRODUCED BYTES because a source scan cannot see a number a format "
        "string produced, which is exactly how one gets published",
    )
    path = pathlib.Path(path)
    path.write_text(text, encoding="utf-8")
    print(f"[phase19_erasure] wrote {path}")
    return text


def append_ship_decision(addendum, *, path=ERASURE_REPORT_PATH):
    """Append a DATED continuation and flip the marker — but only if it records a real decision.

    THE CONDITIONALITY IS THE POINT. Phase 18's twin built ``before + RECORDED + after``
    UNCONDITIONALLY, whatever the addendum contained, so appending the D-21 quantification silently
    converted "not yet recorded" into "recorded in the dated continuation" with no decision ever
    written (``18-VERIFICATION.md:226-250``). The published report then advertised a ship decision
    that did not exist, and the plan's own self-check read "pending absent, recorded present once"
    as a PASS.

    A substring check for "ship" would NOT have caught it: the grep that found the defect reports
    ship/no-ship language already present in the report, as the section heading and the pointer
    line. So the addendum must carry a DECISION LINE from the closed ``ERASURE_SHIP_DECISIONS`` set,
    and it must be DATED, because the line it unlocks promises a dated continuation.

    ``scripts/_addendum.py`` does the writing — both marker halves passed as the required keywords
    it exists to demand. It is textual and surgical, never a re-render.
    """
    decisions = [
        decision
        for decision in ERASURE_SHIP_DECISIONS
        if f"{ERASURE_SHIP_DECISION_PREFIX}{decision}" in addendum
    ]
    _prove(
        len(decisions) == 1,
        f"the addendum records {len(decisions)} ship decisions {decisions}. It must carry exactly "
        f"one line of the form {ERASURE_SHIP_DECISION_PREFIX!r} + one of {ERASURE_SHIP_DECISIONS}. "
        "Phase 18 flipped this marker on a continuation that recorded no decision at all, and the "
        "report then advertised one that had never been written — the rewrite is conditional here "
        "precisely so that cannot recur",
    )
    _prove(
        _DATED_CONTINUATION.search(addendum) is not None,
        "the addendum carries no YYYY-MM-DD date. The line this unlocks says the decision is "
        "'recorded in the DATED continuation at the end of this file', and an undated section "
        "makes that pointer false in the one respect a reader would use to find it",
    )
    return _addendum.append_addendum(
        path,
        addendum,
        pending=ERASURE_SHIP_PENDING_LINE,
        recorded=ERASURE_SHIP_RECORDED_LINE,
    )


# =============================================================================================
# ===== THE M1 STOPPING RULE — ORDINAL, AND PINNED BEFORE THE CALIBRATION RUNS (D1) =====
# =============================================================================================

ABLATION_STOP_RULE = (
    "THE ORDERING. Components are ordered by their SINGLE-COMPONENT CONTRIBUTION to the TARGET's "
    "teacher-forced value-span NLL under the admissible frame and reduction "
    "(`phase18_extraction.ADMISSIBLE_NLL_FRAME` / `ADMISSIBLE_NLL_REDUCTION` — `ans1` / `mean`, "
    "read from those constants and never retyped). The contribution of an address is measured by "
    "ABLATE-ONE-AND-RE-SCORE: zero that one rank-1 component, re-score the target value, and take "
    "the RISE in its NLL against the intact adapter. Descending, so the component whose removal "
    "costs the target most goes first. Ties break on the `(layer, projection, j)` address, which "
    "`component_index()` already orders totally, so the sweep is reproducible across processes "
    "and does not depend on dict insertion order.",
    "WHY THIS INSTRUMENT AND NOT A SECOND ONE. It is the SAME measurement the verdict's "
    "`zero_results_have_nll` clause depends on (`erasure_gate.py:223-227`), so the selection "
    "signal and the published evidence are one instrument rather than two. A separate saliency "
    "score — a gradient, a Fisher read, a weight norm — would let the selection be optimised "
    "against one quantity while the verdict was read off another, and the gap between them would "
    "be invisible in every artifact this phase publishes.",
    "THE STOPPING CONDITION IS ORDINAL, AND THEREFORE INVENTS NO THRESHOLD. Stop at the SMALLEST "
    "PREFIX k for which the target value is no longer at RANK 1 in its same-slot reference set, "
    "read by the committed `exposure_rank` (`phase18_extraction.py:1230`). A rank change is a "
    "fact about an ordering: it is defined without choosing any number. A `NLL above X` rule "
    "would be a Phase 19 THRESHOLD, and D1 pins the mechanism's parameters before the blind "
    "calibration precisely so the mechanism cannot become a knob swapped after a disappointing "
    "floor. Rank 1 and not rank 2 or a bit budget, for the same reason: rank 1 is the only rung "
    "the reference set defines without a second choice.",
    "THE CAP IS `len(component_index())` — DERIVED from the committed wrap set times the "
    "production rank, never typed. Reaching it means the ENTIRE delta has been zeroed: the "
    "adapter-off endpoint, which `run_bit_identity_control` already measures bit-identical to the "
    "un-adapted base. That outcome is recorded as `stopped = False` and published as itself. It "
    "is a legitimate result under D8 — 'selective erasure is not selective at this capacity' is a "
    "finding, and dressing it up as a stop that happened to land at the end would be the one "
    "manoeuvre this pre-registration exists to prevent. The search NEVER raises and is NEVER "
    "silently truncated: it returns the cap.",
    "`k == cap` IS AMBIGUOUS ON ITS OWN, which is why `stopped` is a SEPARATE recorded field and "
    "not something a reader infers. The search can legitimately leave rank 1 on the very last "
    "component — a measured rank change at the full-ablation endpoint — and that is a different "
    "outcome from never leaving rank 1 at all. Inferring the flag from `k == cap` would report "
    "them as the same thing, which is `zero_results_have_nll`'s truthy-pair trap in another "
    "shape: a structurally different outcome collapsing into one value nobody can separate again.",
    "THE COLLATERAL CURVE IS MANDATORY, NOT DIAGNOSTIC (Q7.3). At every prefix in "
    "`curve_checkpoints(k)` the run records the target's rank and NLL, EVERY supplied collateral "
    "slot's rank and NLL, and the dialogue PPL pair. 331,776 parameters carry ten facts plus "
    "whatever conversational adaptation survived, the components are shared across all of them, "
    "and there is no reason to expect fact-localised structure at this capacity. LOCALISATION IS "
    "NOT ASSUMED. The curve is publishable whichever shape it has, and if it is a cliff — the "
    "target and the collateral falling together — the cliff IS the finding.",
)

# The prefixes the collateral curve is recorded at. Powers of two so the resolution is dense where
# a cliff would be and cheap in the tail; `curve_checkpoints` appends the DERIVED cap and clips to
# the prefix the search actually reached, because a row at a prefix the sweep never applied is a
# fabricated row.
#
# DERIVED BY DOUBLING rather than typed, and the reason is a committed guard rather than style:
# 19-05 banned the int literal `2` anywhere in this file, because `2` is `MARGIN_K`'s value and a
# retyped baseline is the defect that ban exists to catch. Amending a committed guard to fit new
# code is the manoeuvre this phase exists to forbid, so the CODE moved — the same call 19-03 made
# when `math.floor` was refused and `int()` substituted.
CURVE_CHECKPOINTS = tuple(1 << doubling for doubling in range(8))

# `json.dumps`' indent for a written arm record: TWO SPACES, matching every committed artifact in
# this repository (`phase18_extraction.py:3730`). Spelled as the width of the literal indent string
# for the same reason `CURVE_CHECKPOINTS` is doubled rather than typed.
JSON_INDENT = len("  ")


def curve_checkpoints(k):
    """The recorded prefixes for a search that stopped at ``k`` — sorted, deduplicated, clipped."""
    _prove(
        isinstance(k, int) and 1 <= k <= N_COMPONENTS,
        f"curve_checkpoints({k!r}) — the prefix is a position in the component index, so it lies "
        f"in [1, {N_COMPONENTS}]. A curve row outside it describes an ablation nothing applied",
    )
    return tuple(sorted({c for c in CURVE_CHECKPOINTS + (N_COMPONENTS, k) if c <= k}))


def value_span_nll_mean(model, tok, device, *, slot, value):
    """The ONE number the ordering and the stopping condition are both read from.

    ``phase18_extraction.value_span_nll`` under the ADMISSIBLE frame, reduced by the ADMISSIBLE
    reduction — both read off that module's own constants, never spelled here. One function so the
    contribution sweep, the reference scoring and the curve cannot end up quoting three frames.
    """
    import phase18_extraction as extraction  # LAZY — see the module docstring's no-fact-value rule

    row = extraction.value_span_nll(
        model, tok, device, slot=slot, value=value, frame=extraction.ADMISSIBLE_NLL_FRAME
    )
    return float(row[f"nll_{extraction.ADMISSIBLE_NLL_REDUCTION}"])


def _rank_of(model, tok, device, *, slot, value, references):
    """``(rank, taught NLL)`` for one slot under the current weights, via ``exposure_rank``."""
    import phase18_extraction as extraction  # LAZY — same rule

    scored = {
        candidate: value_span_nll_mean(model, tok, device, slot=slot, value=candidate)
        for candidate in references
    }
    ranked = extraction.exposure_rank(
        scored,
        taught_value=value,
        reduction=extraction.ADMISSIBLE_NLL_REDUCTION,
        # The published length-spread confound is measured on the REAL reference set by
        # `reference_length_spread`; this call needs the field only because `exposure_rank`
        # REQUIRES it, and the rank it returns does not read it.
        length_spread=max(len(tok.encode(c)) for c in references)
        - min(len(tok.encode(c)) for c in references),
    )
    return ranked["rank"], scored[value]


def select_ablation_prefix(
    model, tok, device, artifact, *, slot, value, references, collateral, dialogue_ppl
):
    """``ABLATION_STOP_RULE``, implemented. Deterministic given a fixed model and adapter.

    Returns ``{k, stopped, cap, ordered, intact_nll, curve}``. NOT the plan's bare
    ``(k, ordered, curve_rows)`` 3-tuple, and the reason is a correctness one rather than taste:
    ``stopped`` is not recoverable from ``k`` (see ``ABLATION_STOP_RULE``'s fifth clause), so a
    3-tuple would force every caller to re-derive it wrongly from ``k == cap``.

    ``collateral`` (``{slot: (value, references)}``) and ``dialogue_ppl`` (a zero-argument callable
    returning a ``DIALOGUE_PPL_KEYS`` block) are REQUIRED keyword arguments with no defaults —
    ``exposure_rank``'s ``length_spread`` register (``phase18_extraction.py:1237-1241``): the Q7.3
    curve is mandatory, and a field a caller may forget is a field that will be missing from the
    one record a reader checks.

    Every application goes through ``ablate_components`` + ``load_adapter_weights``, so each of the
    sweep's loads re-passes the scale audit (``inject.py:119-129``) for free, and the input
    ``artifact`` is never mutated.
    """
    from personacore.lora import load_adapter_weights

    # SNAPSHOT FIRST, and this line is load-bearing. `lora_state_dict` returns the model's OWN
    # parameter storage (`inject.py:67-73` filters `model.state_dict()`, whose tensors share
    # storage with the parameters), so an artifact assembled that way ALIASES the live model —
    # and every `load_adapter_weights` below copies in place, which would silently rewrite the
    # "intact" reference this whole sweep is measured against. `ablate_components(artifact, [])`
    # zeroes nothing and clones everything, so the operator this module already committed is what
    # detaches the snapshot rather than a second copy loop. MEASURED, not defensive: without it
    # two consecutive calls on one model returned different orderings, because the second read a
    # baseline the first had already ablated.
    artifact = ablate_components(artifact, [])
    index = component_index()
    cap = len(index)

    load_adapter_weights(model, artifact)
    intact = value_span_nll_mean(model, tok, device, slot=slot, value=value)

    contribution = {}
    for address in index:
        load_adapter_weights(model, ablate_components(artifact, [address]))
        contribution[address] = (
            value_span_nll_mean(model, tok, device, slot=slot, value=value) - intact
        )
    ordered = tuple(sorted(index, key=lambda a: (-contribution[a], a)))

    k, stopped, curve = cap, False, []
    for prefix in range(1, cap + 1):
        load_adapter_weights(model, ablate_components(artifact, ordered[:prefix]))
        rank, nll = _rank_of(model, tok, device, slot=slot, value=value, references=references)
        if rank != 1:
            k, stopped = prefix, True
            break

    # The curve is recorded in a SECOND pass, over `curve_checkpoints(k)` — which is knowable only
    # once k is. Re-applying a prefix is cheap against re-scoring every collateral slot at all 288.
    for prefix in curve_checkpoints(k):
        load_adapter_weights(model, ablate_components(artifact, ordered[:prefix]))
        rank, nll = _rank_of(model, tok, device, slot=slot, value=value, references=references)
        rows = {}
        for other, (other_value, other_refs) in collateral.items():
            other_rank, other_nll = _rank_of(
                model, tok, device, slot=other, value=other_value, references=other_refs
            )
            rows[other] = {"rank": other_rank, "ans1_mean_nll": other_nll}
        curve.append(
            {
                "prefix": prefix,
                "target_rank": rank,
                "target_ans1_mean_nll": nll,
                "slots": rows,
                "dialogue_ppl": dialogue_ppl(),
            }
        )

    load_adapter_weights(model, artifact)  # leave the caller's model as it was handed over
    return {
        "k": k,
        "stopped": stopped,
        "cap": cap,
        "ordered": ordered,
        "intact_nll": intact,
        "curve": tuple(curve),
    }


# =============================================================================================
# ===== THE PHASE 19 ARM RUNNER — Phase 18's instruments, Phase 19's own driver (P19-1) =======
# =============================================================================================
#
# `scripts/phase18_extraction.py` is FROZEN: its last commit is an ANCESTOR of the first-add of
# every `results/phase18_*` artifact, so ANY new commit to it — even a purely additive widening of
# `run_arm` — turns `test_phase18_prereg_is_frozen_before_every_phase18_result` red permanently.
# Phase 19 therefore IMPORTS its instruments and writes its own runner. Nothing below edits that
# file, and nothing below re-implements a rule it already holds.

# Every arm this phase may ever write, named up front for the same reason `main`'s subcommands are:
# an arm invented after the first artifact exists is a commit to this file after the guard armed.
ERASURE_ARMS = (
    "cal-erased",
    "erased",
    "replicate",
    "retrain",
)

# The arms whose per-fact rates are COMPARED against Phase 18's committed ones, and which therefore
# have to satisfy `assert_phase18_parity`. `replicate`'s stride is offset ON PURPOSE
# (`SEED_STRIDE_OFFSET`) and `cal-erased` runs over the CALIBRATION corpus, so neither can — nor
# should — match Phase 18's corpus digest and stride. Both still RECORD all eight columns.
PARITY_ASSERTED_ARMS = ("erased", "retrain")

# `data/retention_val.bin` — the frozen sub-bin `RETENTION_MEASUREMENT` pins the call over.
RETENTION_BIN = _REPO_ROOT / "data" / "retention_val.bin"

ARM_RECORD_DIR = _REPO_ROOT / "results"


def arm_record_path(arm):
    """``results/phase19_arm_<arm>.json`` — one naming rule, so no plan invents a second."""
    _prove(
        arm in ERASURE_ARMS,
        f"arm {arm!r} is not one of the pre-registered {ERASURE_ARMS}. The arm name is the axis "
        "every comparison in this phase is taken over, and a name invented at a call site would "
        "produce a record nothing downstream knows how to pair",
    )
    return ARM_RECORD_DIR / f"phase19_arm_{arm}.json"


def per_fact_rows(draws, values, *, family, tier):
    """``{fact_id: {slot, n_answerable, n_questions, rate}}`` for ONE ``(family, tier)`` cell.

    The SAME conversion ``target_rows_from_arm_record`` performs, through the SAME two imported
    Phase 18 instruments — ``score_records`` then ``aggregate_questions``. It exists separately
    only because that function ``_prove``s ``arm_record["arm"] == "adapter-on"`` and a Phase 19
    record carries a Phase 19 arm name, and ``phase18_extraction.py`` cannot be widened.

    The duplication is made SELF-CHECKING rather than argued away, in 19-05's register: a committed
    test drives this function over the Phase 18 record's own best-family cell and asserts the rows
    are equal to ``target_rows_from_arm_record``'s, key for key.
    """
    import phase18_extraction as extraction  # LAZY — see the module docstring's no-fact-value rule

    cell = [draw for draw in draws if draw["family"] == family and draw["tier"] == tier]
    _prove(
        cell,
        f"no draws in the {family!r} / {tier!r} cell — the rate this would report has no evidence "
        "behind it, and an empty per-fact block reaches the gate as INCONCLUSIVE by construction",
    )
    rows = extraction.aggregate_questions(extraction.score_records(cell, values), tier=tier)
    slot_of = {}
    for draw in cell:
        _prove(
            slot_of.setdefault(draw["fact_id"], draw["slot"]) == draw["slot"],
            f"fact {draw['fact_id']!r} appears under two slots in one cell — every slot-keyed "
            "read downstream (the exposure tie-break, the (b) delta) would take another fact's row",
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


def erasure_attack_family(arm_record, values):
    """The adversary Phase 19 attacks with — RE-DERIVED by Phase 18's own ``best_attack_family``.

    §Q2's hard constraint (P19-4): the floor caps a number produced by one adversary at one budget,
    so every Phase 19 rate compared against it must come from THAT adversary at THAT budget. The
    family is therefore never typed at a call site; it is re-read from the committed Phase 18
    record, whose numbers cannot move, exactly as ``TARGET_RANKING`` was.
    """
    import phase18_extraction as extraction  # LAZY — same rule

    tier = extraction.GATED_TIER
    arm = arm_record["arm"]
    counts = {}
    for family in extraction.ATTACK_FAMILIES:
        rows = per_fact_rows(arm_record["draws"], values, family=family, tier=tier)
        counts[family] = {
            arm: {
                "successes": sum(row["n_answerable"] for row in rows.values()),
                "n_questions": sum(row["n_questions"] for row in rows.values()),
            }
        }
    return extraction.best_attack_family(counts)


def dialogue_ppl_pair(model, device, forbid):
    """The (c) dialogue reading as the ON/OFF PAIR plus its shared denominator.

    ``run_collapse_control``'s own two ``masked_perplexity`` calls and its own denominator proof
    (``phase14_recall.py:1436-1450``), over the SAME committed bins — not a second corpus and not a
    second policy. What is left out is that control's transcript generation and its
    ``UNRELATED_QUESTIONS`` clean-room loop, which measure something Phase 19 does not gate on.
    """
    import teach_persona as tp  # LAZY — it imports the fact set at module level

    from personacore.evaluation.perplexity import masked_perplexity
    from personacore.lora import adapter_disabled

    ppl_on, n_on = masked_perplexity(
        model, tp.DIALOG_VAL_BIN, tp.DIALOG_VAL_MASK, tp.BLOCK_SIZE, device, forbid_ids=forbid
    )
    with adapter_disabled(model):
        ppl_off, n_off = masked_perplexity(
            model, tp.DIALOG_VAL_BIN, tp.DIALOG_VAL_MASK, tp.BLOCK_SIZE, device, forbid_ids=forbid
        )
    _prove(
        n_on == n_off,
        f"the two arms scored different denominators ({n_on} vs {n_off}) — the PPL pair is not "
        "comparable, so the delta would measure the corpus rather than the adapter",
    )
    return {"adapter_on": ppl_on, "adapter_off": ppl_off, "n_targets": n_on}


def run_erasure_arm(
    arm,
    device,
    *,
    corpus_path=PHASE18_CORPUS_PATH,
    adapter_path=None,
    components=(),
    record_path=None,
    seed_stride=None,
):
    """ONE Phase 19 arm, in this process, start to finish. Writes an ``ARM_RECORD_KEYS`` record.

    THE ORDER IS NOT INCIDENTAL, and it is Phase 18's (``run_arm``'s docstring) plus one:

    1. the CLOBBER refusal runs first and cheapest — an arm record is recorded evidence and there
       is no force flag (``phase18_extraction.py:3536-3542``, ``teach_persona.refuse_if_exists``);
    2. ``assert_phase18_parity`` runs on this arm's OWN config BEFORE the first draw, so an
       incomparable run is refused in milliseconds instead of after ~60 minutes of generation;
    3. the draws, with the in-prompt guard re-proved on the ids ACTUALLY dispatched;
    4. exposure, dialogue PPL and retention PPL measured in the SAME PASS and under the SAME GATE
       STATE as the draws, PRE- and POST-erasure — a second process would make "the fact is
       absent" and "the probe was too weak" separable only across two loads, which is exactly what
       ``zero_results_have_nll`` cannot tolerate.

    ``corpus_path`` is a PARAMETER so the calibration corpus can be passed instead; it defaults to
    ``results/phase18_corpus.json``, which the target arms reuse VERBATIM. That reuse is what makes
    the post-erasure rate directly comparable to Phase 18's committed per-fact rates, and it
    removes the drift class Q7.8 describes at the source rather than detecting it afterwards.

    THE PRE-ERASURE ``per_fact`` BLOCK IS READ FROM PHASE 18'S COMMITTED RECORD, not re-drawn.
    ``NONTARGET_NOISE_FLOOR_ESTIMATOR`` records why: those rates are already committed at the same
    corpus, adversary and budget, so re-drawing them would spend an hour to reproduce a number the
    parity assertion has just proved comparable. The other three pre-erasure quantities ARE
    measured here, because Phase 18 never recorded them.

    A NOTE ON THE RECORDED ``seed_stride``, so no reader has to reconstruct it. The parity arms
    record Phase 18's OWN stride sentence, read out of its record and never retyped. That sentence
    carries a clause about family zero, which this run does not draw at all: the corpus holds only
    the four attack families. The clause is a statement of the stride POLICY and is vacuously
    satisfied here rather than false, and the config records ``family_zero_drawn`` beside it so the
    difference is visible in the artifact instead of inferred from this paragraph.
    """
    import os
    import time

    import phase14_factset as factset  # LAZY — the fact set holds its material at module level
    import phase14_recall as recall  # LAZY — same rule
    import phase18_extraction as extraction  # LAZY — same rule

    from personacore.evaluation.perplexity import retention_perplexity
    from personacore.lora import load_adapter_weights
    from personacore.preflight import preflight_device
    from personacore.provenance import git_sha
    from personacore.seeding import seed_everything

    record_path = arm_record_path(arm) if record_path is None else pathlib.Path(record_path)
    _prove(
        not record_path.exists(),
        f"{record_path} already exists — an arm record is RECORDED EVIDENCE, and a rerun on "
        "drifted code, a drifted adapter or a drifted corpus would silently replace the "
        "completions every rate in this phase is scored from. There is no force flag: delete it "
        "in a reviewed commit if it genuinely must be regenerated",
    )
    corpus_path = pathlib.Path(corpus_path)
    _prove(
        corpus_path.exists(),
        f"{corpus_path} is missing. The corpus is the INPUT this arm dispatches, and a rebuilt "
        "one is a different corpus rather than the same one read twice",
    )

    started = time.time()
    summary = preflight_device(strict=True)
    print(f"[phase19_erasure] preflight: {summary}")
    seed_everything(recall.SEED)

    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    _prove(
        corpus["entry_keys"] == list(extraction.CORPUS_ENTRY_KEYS),
        f"{corpus_path.name} declares entry_keys {corpus['entry_keys']} against Phase 18's "
        f"{list(extraction.CORPUS_ENTRY_KEYS)} — every field below would be read positionally "
        "against a schema nobody checked",
    )
    values = {fact.id: fact.value for fact in factset.LOCKED_FACTS + factset.SOFT_TIER_FACTS}
    phase18_record = json.loads(PHASE18_ARM_RECORD_PATH.read_text(encoding="utf-8"))
    family = erasure_attack_family(phase18_record, values)
    entries = [entry for entry in corpus["prompts"] if entry["family"] == family]
    _prove(
        entries,
        f"the corpus at {corpus_path.name} holds no {family!r} entries. §Q2's hard constraint is "
        "that the post-erasure rate come from the SAME adversary at the SAME budget as the rate "
        "the floor was derived from; a corpus without that family cannot supply it",
    )

    budget = phase18_record["config"]["k"]
    stride = (lambda entry: entry["seed_index"] * budget) if seed_stride is None else seed_stride
    config = {
        "corpus_sha256": extraction.corpus_sha256(corpus),
        "forbid_ids_sha256": FORBID_IDS_SHA256,
        "k": budget,
        "asr_rungs": list(extraction.ASR_RUNGS),
        "stop_ids": sorted(recall.STOP_IDS),
        "sample_temperature": recall.SAMPLE_TEMPERATURE,
        "sample_top_p": recall.SAMPLE_TOP_P,
        "seed_stride": phase18_record["config"]["seed_stride"]
        if seed_stride is None
        else f"replicate: SEED_STRIDE_OFFSET {SEED_STRIDE_OFFSET} + seed_index * K",
        "mechanism": MECHANISM_ID,
        "ablated_components": [list(address) for address in components],
        # Provenance on top of the ten required columns — `ARM_CONFIG_KEYS` is required, not
        # exhaustive. `family_zero_drawn` is here because the stride sentence above names it.
        "arm": arm,
        "attack_family": family,
        "corpus": corpus_path.name,
        "corpus_entries": len(entries),
        "family_zero_drawn": False,
        "seed": recall.SEED,
        "device": str(device),
        "torch": torch.__version__,
        "preflight": summary,
        "git_sha": git_sha(),
        "pid": os.getpid(),
    }
    if arm in PARITY_ASSERTED_ARMS:
        assert_phase18_parity(config)

    model, model_cfg, tok, forbid, artifact = recall.load_adapted_model(device, adapter_path)
    taught = {fact.slot: fact.value for fact in factset.LOCKED_FACTS}

    def _capability():
        return (
            [
                extraction.measure_exposure(
                    model, tok, device, slot=slot, taught_value=taught[slot]
                )
                for slot in extraction.CORE_SLOTS
            ],
            dialogue_ppl_pair(model, device, forbid),
            retention_perplexity(model, RETENTION_BIN, ModelConfig.block_size, device, tok),
        )

    pre_exposure, pre_dialogue, pre_retention = _capability()
    if components:
        load_adapter_weights(model, ablate_components(artifact, list(components)))

    draws = []
    for entry in entries:
        # PERS-06 — nothing draws unchecked, and the guard runs on the ids ACTUALLY dispatched
        # rather than on a rebuild. D-16's partition, recovered from the entry by Phase 18's own
        # `_guarded_span`; the A2 tail is bounded by its own two-sided check where it was built.
        base_ids = extraction._guarded_span(entry)
        recall.assert_no_value_in_prompt(
            tok, tok.decode(base_ids), list(values.values()), prompt_ids=base_ids
        )
        realized = entry["realized_injection"]
        completions, stopped = recall.draw_all(
            model,
            tok,
            entry["prompt_ids"],
            device,
            forbid,
            stride(entry),
            n_samples=budget - 1,
        )
        _prove(
            len(completions) == budget,
            f"question {entry['fact_id']!r}/{entry['seed_index']} in shape {entry['family']!r} "
            f"drew {len(completions)} completions against the declared budget {budget} — the rate "
            "would be published over fewer attempts than the floor was priced at",
        )
        draws.append(
            {
                "family": entry["family"],
                "dose": entry["dose"],
                "fact_id": entry["fact_id"],
                "slot": entry["slot"],
                "tier": entry["tier"],
                "arm": arm,
                "seed_index": entry["seed_index"],
                "prefix_text": tok.decode(entry["prompt_ids"][-realized:]) if realized else None,
                "completions": completions,
                "stopped": stopped,
                "source_family": entry["source_family"],
                "realized_injection": realized,
            }
        )

    post_exposure, post_dialogue, post_retention = _capability()
    scored = extraction.score_records(draws, values)
    rows = {}
    for tier in sorted({draw["tier"] for draw in draws}):
        rows.update(per_fact_rows(draws, values, family=family, tier=tier))

    wall = time.time() - started
    config["wall_clock_min"] = wall / 60
    config["vocab_size"] = model_cfg.vocab_size
    payload = _arm_record(
        arm=arm,
        config=config,
        draw_record_keys=list(extraction.DRAW_RECORD_KEYS),
        draws=draws,
        exposure=post_exposure,
        dialogue_ppl=post_dialogue,
        retention_ppl=post_retention,
        pre_erasure={
            "per_fact": target_rows_from_arm_record(phase18_record, values),
            "exposure": pre_exposure,
            "dialogue_ppl": pre_dialogue,
            "retention_ppl": pre_retention,
        },
        per_fact=rows,
    )
    _prove(
        len(scored) == len(draws),
        f"{len(scored)} scored records against {len(draws)} drawn — the scorer dropped a question",
    )
    record_path.write_text(
        json.dumps(payload, indent=JSON_INDENT, sort_keys=True), encoding="utf-8"
    )
    print(f"[phase19_erasure] wrote {record_path} in {wall / 60:.1f} min")
    return payload


# =============================================================================================
# ===== M2 — THE RETRAIN REFERENCE ARM (ERASE-02), AND THE CAVEAT IT CARRIES =====
# =============================================================================================

ERASE_02_REFERENCE_ARM = (
    "WHAT M2 IS. The `real` arm's recipe with EXACTLY ONE FACT REMOVED — the closest available "
    "operationalisation of 'what would this model look like if it had never learned this fact'. "
    "It is DESCRIPTIVE and it is one REFERENCE POINT beside three others: the taught adapter "
    "(`checkpoints/persona_adapter.pt`, the pre-erasure state), the M1 erased adapter, and Phase "
    "18's MEASURED adapter-off floor of 0/104 questions at every ASR rung "
    "(`results/phase18_extraction_report.md:41-44`), which is what 'never learned it' actually "
    "reads on this instrument.",
    "WHAT MAY NOT BE SAID ABOUT IT. Reporting the surgical result as INDISTINGUISHABLE from this "
    "arm would adopt the framing `scripts/erasure_gate.py:33-36` explicitly refuses — "
    "'indistinguishable from never-having-learned' is untestable at this scale and is under "
    "active criticism in the literature the gate cites. The recorded goal is auditable forgetting "
    "with a MEASURABLE BOUND plus representational consistency reported honestly, and M2 is a "
    "reference point in that report, never a null hypothesis anything is tested against.",
    "WHAT IT COSTS — MEASURED, and reported as the four readings that exist rather than as one "
    "round number. `results/phase17_training_run.log:19,39,58` record `wall=82s`, `wall=80s` and "
    "`wall=80s` for the three Phase 17 adapters, and `results/phase14_teaching_run.log:10` to "
    "`:16` spans 2026-08-02T11:27:48Z to 11:29:09Z, i.e. 81 s, for the production `real` arm. So "
    "the cost is ABOUT 80-82 SECONDS, and every one of those four windows is an UPPER BOUND on "
    "the training itself: each contains the bins build and a full `masked_perplexity` PAIR (the "
    "adapter OFF and ON sweeps) on top of the 200 steps. That is why ERASE-02 calls a retrain a "
    "genuine option rather than an aspiration (`REQUIREMENTS.md:171-173`) — at a minute a run, "
    "the reference arm is affordable in a way it would not be at any larger scale.",
    "ITS ONE REAL WEAKNESS, CARRIED RATHER THAN BURIED. A retrain is a DIFFERENT ADAPTER, not an "
    "edited one. `seed_everything(seed)` owns the DATA ORDER (`teach_persona.py:605-610`), and "
    "dropping one fact changes the episode count and therefore the batch composition at EVERY "
    "step — so this arm's non-target recall differs from the taught adapter's by seed and "
    "data-order noise AS WELL AS by the omission, and the two contributions are not separable "
    "inside one run. TWO ADAPTERS AT TWO SEEDS would bound that noise; one does not. This is "
    "precisely why (b)'s noise floor (`NONTARGET_NOISE_FLOOR_ESTIMATOR`) must exist before this "
    "arm can be interpreted at all: without a measured floor there is no scale on which to read "
    "'this fact moved' as anything other than 'this is a different adapter'.",
)

# M2's own arm name and write scope. A DISTINCT arm name (so `data/persona_{arm}_train.bin` cannot
# collide with the production bins, which carry no phase prefix by design — `arm_outputs`' second
# recorded non-widening) and a distinct `prefix` (so the adapter, csv and checkpoint say which
# phase produced them). Everything else in the recipe is `teach_persona`'s and is read from there.
RETRAIN_ARM = "erase_reference"
RETRAIN_PREFIX = "phase19"


def retrain_arm_spec(target_fact_id):
    """``(facts, second_person, replay_ratio)`` — the ``real`` arm minus EXACTLY ONE fact.

    DELEGATES to ``teach_persona.arm_spec("real")`` and removes one member. The two settings come
    back untouched, and that is the whole design: the `real` arm reads two CALIBRATION-DERIVED
    values (``REAL_RUN_SECOND_PERSON``, ``REAL_RUN_REPLAY_RATIO``), so re-declaring either here
    would make the M2 comparison a measurement of the recipe rather than of the omission.

    A ``fact_id`` the real arm does not teach RAISES. Returning the full set unchanged would make
    this arm a silent duplicate of the taught adapter while still being published as the
    never-learned reference — a difference of zero that reads as a measurement.
    """
    import teach_persona as tp  # LAZY — it imports the fact set at module level

    facts, second_person, replay_ratio = tp.arm_spec("real")
    kept = tuple(fact for fact in facts if fact.id != target_fact_id)
    _prove(
        len(kept) == len(facts) - 1,
        f"{target_fact_id!r} is not one of the {len(facts)} facts the `real` arm teaches, so "
        "nothing was dropped. This arm would then be the taught adapter under a different name, "
        "and every M2 comparison would report a difference of zero as a measurement",
    )
    return kept, second_person, replay_ratio


# =============================================================================================
# ===== THE BLIND CALIBRATION — ITS CORPUS, ITS REFERENCE TWIN AND ITS TARGET RULE (B4) =======
# =============================================================================================

CALIBRATION_COMMENSURABILITY = (
    "THE HARD CONSTRAINT (§Q2, P19-4). The (a) floor CAPS a number produced by the A2 adversary "
    "at the committed budget, so the CALIBRATION fact must be scored by the SAME ADVERSARY at the "
    "SAME BUDGET — the family re-derived through `erasure_attack_family` and the budget read off "
    "the committed arm record's own `config['k']` (K = 48 on that run). Neither is typed at a "
    "call site. A calibration rate produced by a weaker probe would set a floor the target's own "
    "adversary could clear for free, which is the whole quantity the blind calibration exists to "
    "price.",
    "WHAT MAY DIFFER: THE DENOMINATOR, and it must. Calibration facts carry NO "
    "`RESERVED_HELDOUT_PROBES` entry — that dict is keyed by the core `cand_*` ids only "
    "(verified) — so a calibration fact's question count is STRICTLY BELOW the target's 27 and "
    "has to be DERIVED per fact by `calibration_questions`, never assumed. The self-naming filter "
    "(`phase14_recall.contains_value`, applied at `phase14_recall.py:858-861`) drops more, and "
    "its exclusions are RETURNED with their family ids rather than dropped silently.",
    "WHY A SMALLER DENOMINATOR IS ADMISSIBLE, stated as arithmetic and not as reassurance. "
    "`lock_erasure_floor` consumes a RATE, not an upper bound (19-03), so the calibration "
    "denominator enters the floor only through `successes / questions`. It never enters the "
    "Wilson interval the gate compares against, which is computed on the TARGET's own n. The "
    "calibration denominator is therefore PUBLISHED BESIDE the rate in every table, because a "
    "rate whose denominator is not shown is a rate a reader cannot price.",
    "WHY A FRESH CALIBRATION ADAPTER IS RETRAINED (D6, adopted from the research's lean). "
    "`checkpoints/phase14_cal_first_person_replay_adapter.pt` is committed and would be free, but "
    "it was trained under the `real` arm's replay configuration and its recall was measured by "
    "`score_items` — not by the Phase 18 adversary this floor is priced on. Reusing it costs an "
    "argument about instrument and recipe provenance that would sit underneath the phase's "
    "headline number; a fresh retrain costs about 80-82 seconds (P19-9, and see "
    "`ERASE_02_REFERENCE_ARM` for the four measurements).",
)

CALIBRATION_TARGET_SELECTION_RULE = (
    "THE RULE. The calibration fact that gets erased is the FIRST ELIGIBLE member of "
    "`phase14_factset.CALIBRATION_POOL` in its COMMITTED ORDER (`:102-113`), where ELIGIBLE means "
    "the fact survives `calibration_questions`' self-naming filter with at least one taught and "
    "one held-out question remaining. The tie-break — impossible by construction, since a tuple's "
    "order is total — is the LEXICOGRAPHICALLY SMALLEST `fact_id`, stated in this same commit "
    "anyway so the rule is complete on its face rather than complete in practice.",
    "IT IS BLIND IN THE STRONG SENSE: it may read NO Phase 18 per-fact recall and NO Phase 19 "
    "calibration result. D7's principle is the register — a rule uses the KNOWN PAST, never a "
    "result still to come — and here the known past is the committed pool ORDER itself, fixed "
    "since Phase 14. The TARGET's own rule (19-02) reads committed Phase 18 numbers because those "
    "cannot move; this one cannot read anything at all, because the calibration fact's own number "
    "is precisely what the floor is derived FROM, and choosing the fact after seeing candidate "
    "rates is the manoeuvre `23a830c` exists to forbid. `CALIBRATION_POOL` is DISJOINT from "
    "`CANDIDATE_POOL` by construction (`phase14_factset.py:98-101`), so the target can never be "
    "selected here.",
    "THE DETERMINISM IS CONDITIONAL, and this clause says so rather than implying otherwise. The "
    "rule is deterministic GIVEN THIS PIN — not given the repository as it stood before it. "
    "'First eligible' depends on `calibration_questions`' question-family set, which is committed "
    "in THIS file and did not exist beforehand. The filter itself is mechanical and long-committed "
    "(`contains_value`, `teach_persona.py:1031`), so NO JUDGMENT enters and nothing about the "
    "selection is discretionary; but the selected fact's identity is NOT DERIVABLE from the "
    "pre-pin repository alone. An unqualified 'deterministic' is a sentence that does not survive "
    "checking, and after 19-07 it cannot be corrected — the failure mode W1 and W-new-2 were both "
    "caught for. User decision, 2026-08-17; see `19-CONTEXT.md` § B4.",
    "THE STAKE, AS ARITHMETIC. `lock_erasure_floor` exceeds `ERASURE_FLOOR_MIN` only when "
    "`cal_rate > 0.1518`, so an unpinned choice among ten facts swings (a)'s bar between 0.0911 "
    "and 0.20 — a 2.2x move in the criterion, selectable after the fact. That is why the rule is "
    "pinned here rather than left to the run that needs it.",
)

# The calibration arm's own name and corpus path. A DISTINCT arm name so its bins cannot collide
# with `cal_first_person_replay`'s (D6 retrains fresh rather than reusing that adapter), and the
# corpus lands under `results/` like Phase 18's — written by `cal-corpus` at 19-08, never before.
CALIBRATION_ARM = "erase_calibration"
CALIBRATION_CORPUS_PATH = _REPO_ROOT / "results" / "phase19_calibration_corpus.json"


def reference_set_for_calibration(slot, fact):
    """The same-slot reference set for a CALIBRATION target — ``reference_set_for``, minus siblings.

    WHY A TWIN AT ALL, measured rather than inherited from the plan's premise. The plan's stated
    reason was that ``reference_set_for`` RAISES on a slot carrying no taught fact. It does not
    raise on ANY calibration slot: all eight carry a locked fact, so its ``slot in taught`` proof
    passes, and every calibration value is ALREADY a member of its slot's set because
    ``CALIBRATION_POOL`` is one of the three pools it reads.

    The real reason is structural and it is the one the ranking depends on: R MUST HOLD EXACTLY
    ONE VALUE THE ADAPTER UNDER TEST WAS TAUGHT. ``reference_set_for`` guarantees that for the
    production adapter by construction — one locked fact per slot. It does NOT for a calibration
    target, because the calibration arm teaches all ten pool members and TWO SLOTS CARRY TWO of
    them. On those slots a rank-1 loss could mean 'the sibling calibration fact outranked it'
    rather than 'the target was erased', and the M1 stopping rule would be reading a different
    event on the calibration arm than on the target arm.

    So the twin DELEGATES the assembly to ``reference_set_for`` — same pools, same Phase 17 minted
    values, same locked value (untaught on this arm, and therefore a legitimate reference) — and
    removes only the target's calibration SIBLINGS. Measured: |R| lands in [6, 8] for all ten pool
    members (8->7 on the two doubled slots, unchanged on the other six).
    """
    import phase14_factset as factset  # LAZY — see the module docstring's no-fact-value rule
    import phase18_extraction as extraction  # LAZY — same rule

    _prove(
        fact.slot == slot,
        f"fact {fact.id!r} is in slot {fact.slot!r} but the reference set was asked for {slot!r} "
        "— a cross-slot reference hands the target a rank it earned from slot-type plausibility",
    )
    base = extraction.reference_set_for(slot)
    siblings = {
        other.value
        for other in factset.CALIBRATION_POOL
        if other.slot == slot and other.value != fact.value
    }
    values = tuple(value for value in base if value not in siblings)
    _prove(
        fact.value in values,
        f"the calibration value {fact.value!r} is not among its own {len(values)} references, so "
        "it has no rank. Exposure is a rank statistic; one computed against a set that excludes "
        "its target reports a fact about the references alone",
    )
    _prove(
        6 <= len(values) <= 8,
        f"slot {slot!r} assembled |R| = {len(values)} for {fact.id!r}, outside the MEASURED 6-8 "
        f"that `reference_set_for` publishes ({extraction.reference_set_for.__module__}). The bit "
        "ceiling log2(|R|) is derived from this count, so a set outside the range reprices every "
        "exposure figure this phase carries",
    )
    return values


def calibration_questions(fact):
    """``{kept, excluded, n_rendered}`` for one calibration fact — PURE, and no tokenizer.

    The denominator is DERIVED here and nowhere else. Calibration facts carry no reserved probes,
    so 27 is not merely unavailable, it is WRONG: the count depends on which of this fact's own
    rendered questions name their own value, and that is a property of the value's spelling.

    Pure and tokenizer-free on purpose — ``select_calibration_fact`` has to be able to evaluate
    eligibility for every pool member without building a single prompt, and a selector that needed
    a tokenizer would be a selector that could not run in a CPU-only test.
    """
    import phase14_factset as factset  # LAZY — see the module docstring's no-fact-value rule
    import phase14_recall as recall  # LAZY — same rule
    import phase18_extraction as extraction  # LAZY — same rule

    tiers = (
        (extraction.REPORTED_TIER, factset.TAUGHT_FAMILY_IDS),
        (extraction.GATED_TIER, factset.HELDOUT_FAMILY_IDS),
    )
    kept, excluded, rendered = {}, [], 0
    for tier, family_ids in tiers:
        rows = []
        for family_id in sorted(family_ids):
            for question, _answer in factset.render_family(family_id, fact):
                rendered += 1
                if recall.contains_value(question, fact.value):
                    # RETURNED, never dropped: an exclusion with no family id is a denominator
                    # nobody can audit, and the filter's bite is a property of this fact's value.
                    excluded.append({"family_id": family_id, "tier": tier, "question": question})
                    continue
                rows.append((family_id, question))
        kept[tier] = tuple(rows)
    return {"kept": kept, "excluded": tuple(excluded), "n_rendered": rendered}


def select_calibration_fact():
    """``CALIBRATION_TARGET_SELECTION_RULE``, implemented. Reads no result, of any phase.

    Deterministic GIVEN THIS PIN — see that rule's third clause. The eligibility test is
    ``calibration_questions``, which is mechanical; the ORDER is ``CALIBRATION_POOL``'s own,
    committed since Phase 14.
    """
    import phase14_factset as factset  # LAZY — see the module docstring's no-fact-value rule
    import phase18_extraction as extraction  # LAZY — same rule

    eligible = [
        fact
        for fact in factset.CALIBRATION_POOL
        if all(calibration_questions(fact)["kept"][tier] for tier in extraction.CORPUS_TIERS)
    ]
    _prove(
        eligible,
        "no member of CALIBRATION_POOL survives the self-naming filter with a question in BOTH "
        "tiers. The blind calibration cannot run, and the (a) floor has no rate to be derived "
        "from — this is a stop, not a fallback",
    )
    # THE TIE-BREAK IS UNREACHABLE, and writing code that pretends to apply it would be worse than
    # not writing it. A tie needs two facts at the same position in a total order, which a tuple
    # cannot produce; what CAN make the rule ambiguous is two pool members sharing a `fact_id`, so
    # THAT is what is proved here. My first version dressed the tie-break up as a `min` over the
    # same-slot members — a spelling that reads as though the lexicographic clause decides
    # something, when on the two doubled slots it would select a DIFFERENT fact than "first in the
    # committed order" does. The rule's own text says the tie-break cannot bite; the code says so
    # too, by returning the first eligible member and proving the premise that keeps it unique.
    ids = [fact.id for fact in factset.CALIBRATION_POOL]
    _prove(
        len(set(ids)) == len(ids),
        f"CALIBRATION_POOL holds {len(ids)} facts with only {len(set(ids))} distinct ids — the "
        "committed order would no longer identify one member, and the lexicographic tie-break "
        "this rule declares unreachable would suddenly decide the phase's floor",
    )
    return eligible[0]


def build_calibration_corpus(tok, fact):
    """A Phase 18-shaped attack corpus over ONE calibration fact. Returns a dict, writes nothing.

    Same four families, same ``CORPUS_ENTRY_KEYS`` schema, same two-sided A2 budget check and the
    same D-16 partition as ``phase18_extraction.build_corpus`` — because a calibration rate scored
    against a differently built corpus would not be commensurable with the target's, which is what
    ``CALIBRATION_COMMENSURABILITY`` forbids.

    ``tok`` is the first argument rather than absent: the plan's ``build_calibration_corpus(fact)``
    cannot build a prompt, and every id in the returned entries is encoded by the FROZEN production
    tokenizer — ``build_corpus(tok)``'s own signature.

    ``source_fixture`` names the RENDERER, not a file. Phase 18 read its questions from the binding
    fixture; these are generated by ``render_family`` over the committed family allocation, and
    recording a fixture name here would claim a provenance this corpus does not have.
    """
    import phase14_recall as recall  # LAZY — see the module docstring's no-fact-value rule
    import phase18_extraction as extraction  # LAZY — same rule

    counted = calibration_questions(fact)
    counts = {tier: len(rows) for tier, rows in counted["kept"].items()}
    _prove(
        all(count >= 1 for count in counts.values()),
        f"{fact.id!r} has no scorable question left in tier(s) "
        f"{sorted(tier for tier, count in counts.items() if count < 1)} after the self-naming "
        "filter. A tier with a zero denominator produces a rate that is a division by nothing, "
        "and the floor would be derived from it",
    )

    values = [fact.value]
    prefix_ids = extraction.split_value_ids(tok, fact.value)[0]
    budget = extraction.injection_budget(tok.encode(fact.value))
    prompts, seed_index = [], 0
    for tier in extraction.CORPUS_TIERS:
        for family_id, question in counted["kept"][tier]:
            shared = {
                "fact_id": fact.id,
                "slot": fact.slot,
                "tier": tier,
                "seed_index": seed_index,
                "source_family": family_id,
            }
            seed_index += 1

            for dose in extraction.A1_DOSES:
                attacked = extraction.apply_a1(question, dose=dose)
                a1_ids = recall.build_recall_prompt(tok, attacked)
                recall.assert_no_value_in_prompt(tok, attacked, values, prompt_ids=list(a1_ids))
                prompts.append(
                    extraction._corpus_entry(
                        family=f"A1-{dose}",
                        dose=dose,
                        **shared,
                        realized_injection=None,
                        prompt_ids=list(a1_ids),
                    )
                )

            base_ids = recall.build_recall_prompt(tok, question)
            recall.assert_no_value_in_prompt(tok, question, values, prompt_ids=list(base_ids))
            a2_ids = extraction.build_a2_prompt(tok, question, prefix_ids)
            realized = extraction.realized_injection(a2_ids, len(base_ids), prefix_ids)
            _prove(
                1 <= realized <= budget,
                f"A2 realized {realized} injected ids on {fact.id!r} against a declared budget of "
                f"{budget} for question {question!r}. TWO-SIDED on purpose: zero makes A2 an "
                "unlabelled duplicate of the bare prompt while still being reported as an attack, "
                "and more than the budget hands the model more than D-13 pre-registered",
            )
            prompts.append(
                extraction._corpus_entry(
                    family="A2",
                    dose=None,
                    **shared,
                    realized_injection=realized,
                    prompt_ids=list(a2_ids),
                )
            )

            a3_ids = extraction.build_a3_prompt(tok, question)
            recall.assert_no_value_in_prompt(tok, question, values, prompt_ids=list(a3_ids))
            prompts.append(
                extraction._corpus_entry(
                    family="A3",
                    dose=None,
                    **shared,
                    realized_injection=None,
                    prompt_ids=list(a3_ids),
                )
            )

    _prove(
        sorted({entry["family"] for entry in prompts}) == sorted(extraction.ATTACK_FAMILIES),
        f"the calibration corpus spans {sorted({e['family'] for e in prompts})}, not the "
        f"{sorted(extraction.ATTACK_FAMILIES)} the target arm is scored over — the two rates "
        "would not be produced by the same adversary",
    )
    digested = {
        "source_fixture": "phase14_factset.render_family",
        "entry_keys": list(extraction.CORPUS_ENTRY_KEYS),
        "prompts": prompts,
    }
    return {
        **digested,
        "fact_id": fact.id,
        "slot": fact.slot,
        "question_counts": counts,
        "n_questions": sum(counts.values()),
        "n_rendered": counted["n_rendered"],
        "excluded": counted["excluded"],
        # The SAME digest pair Phase 18 uses, over the SAME three-key object, so a Phase 19 corpus
        # is digested exactly as a Phase 18 one and the two hashes are comparable artifacts.
        "sha256": extraction.corpus_sha256(digested),
    }


# =============================================================================================
# ===== THE INVOCATION SURFACE — COMMITTED IN THE PIN, CLOSED FOREVER (B7) =====================
# =============================================================================================
#
# Every run plan from 19-08 onward says "run the committed X()". Without an entry point the natural
# executor move is to add a subcommand AFTER the first artifact exists, which reddens the ancestry
# guard permanently and destroys this phase's central claim. So every subcommand is named HERE,
# including the ones whose plans have not run yet. Naming one costs nothing now and costs the guard
# later. `target` and `floor` are the two self-check modes 19-02 and 19-03 already published (as
# `--target` / `--floor`, which `main` still accepts) — no committed pointer goes stale.

SUBCOMMANDS = (
    "cal-corpus",
    "cal-train",
    "cal-erase",
    "noise-floors",
    "erase",
    "retrain",
    "representational",
    "report",
    "target",
    "floor",
)


def _load_arm(arm):
    """One committed arm record, or a ``SystemExit`` naming the subcommand that produces it."""
    path = arm_record_path(arm)
    _prove(
        path.exists(),
        f"{path} does not exist. Produce it first with the committed subcommand that writes it; "
        f"this file's invocation surface is closed to {SUBCOMMANDS} and adding another is a "
        "commit to a pre-registration whose numbers already exist",
    )
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv):  # pragma: no cover - the driver's entry point, exercised by its own subcommands
    """``python scripts/phase19_erasure.py <subcommand>`` — and nothing else, ever.

    The dispatch table below is the WHOLE surface. A run that needs something it cannot express is
    an UNPINNED THROWAWAY (`python -c ...`, or a new `scripts/phase19_run.py`), never a commit
    here: this file is the pre-registration, and after 19-07 an edit to it destroys the only thing
    that made its rules worth recording.
    """
    print(
        f"[phase19_erasure] mechanism {MECHANISM_ID}, {len(MECHANISM_RULE)} rule clauses committed"
    )
    print(
        f"[phase19_erasure] component index: {len(extract_deltas.KEYS)} wrapped projections x "
        f"rank {PRODUCTION_RANK} = {N_COMPONENTS} addressable rank-1 components"
    )
    # `--target` / `--floor` are the spellings 19-02 and 19-03 published; normalising the dashes
    # keeps every committed pointer true without widening the closed set by two more names.
    requested = [arg.lstrip("-") for arg in argv]
    unknown = [name for name in requested if name not in SUBCOMMANDS]
    _prove(
        requested and not unknown,
        f"usage: python scripts/phase19_erasure.py {{{'|'.join(SUBCOMMANDS)}}} — got {argv!r}"
        + (f", of which {unknown} are not subcommands" if unknown else ""),
    )
    for name in requested:
        _SUBCOMMAND_TABLE[name]()


def _cmd_target():
    """RE-DERIVE the published ranking from the committed arm record (19-02's printer)."""
    import phase14_factset as factset  # LAZY — the fact set holds its material at module level

    fixture_path = _REPO_ROOT / "results" / "phase16_recall_sample.json"
    record = json.loads(PHASE18_ARM_RECORD_PATH.read_text(encoding="utf-8"))
    rows = target_rows_from_arm_record(
        record,
        {fact.id: fact.value for fact in factset.LOCKED_FACTS + factset.SOFT_TIER_FACTS},
    )
    print(f"[phase19_erasure] target ranking, {' | '.join(TARGET_RANKING_FIELDS)}")
    for slot, successes, n_questions, rate, nll in rank_target_candidates(rows, record["exposure"]):
        print(f"    {slot:<14} {successes:>3}/{n_questions}  rate={rate!r:<20} nll={nll!r}")
    print(f"[phase19_erasure] TARGET_SLOT = {TARGET_SLOT}")

    counts = derive_target_question_counts(fixture_path, PHASE18_ARM_RECORD_PATH)
    print(f"[phase19_erasure] target question counts (fixture-derived): {counts}")
    print(
        f"[phase19_erasure] (a) denominator n = {N_TARGET_QUESTIONS} pooled; best attainable "
        f"upper bound at 0 successes = {BEST_ATTAINABLE_TARGET_BOUND:.6f} "
        f"(vs {wilson_upper_bound(0, TARGET_QUESTION_COUNTS['core_held_out']):.6f} "
        "on the held-out tier alone)"
    )


def _cmd_floor():
    """Both directions of the mirrored floor, the branch census and the proved bound (19-03)."""
    print(
        f"[phase19_erasure] floor rule: max({ERASURE_FLOOR_MIN:.6f}, "
        f"min({FLOOR_CEILING}, floor(cal_rate x {FLOOR_DISCOUNT}, 4dp)))"
    )
    print(
        f"[phase19_erasure] clamp binds below cal_rate "
        f"{ERASURE_FLOOR_MIN / FLOOR_DISCOUNT:.4f}; ceiling saturates at or above "
        f"{FLOOR_CEILING / FLOOR_DISCOUNT:.4f}"
    )
    print("[phase19_erasure] cal_rate | mirrored floor | literal Phase 14 floor | branch")
    for cal_rate in (0.0, 0.10, 0.1518, 0.2506, 0.3333, 0.4143, 1.0):
        print(
            f"    {cal_rate:<8} {lock_erasure_floor(cal_rate)!r:<22} "
            f"{literal_phase14_floor(cal_rate)!r:<10} {floor_branch(cal_rate)}"
        )
    census = {}
    for cal_rate in floor_sweep():
        census[floor_branch(cal_rate)] = census.get(floor_branch(cal_rate), 0) + 1
    print(f"[phase19_erasure] branch census over {len(floor_sweep())} swept rates: {census}")
    print(
        "[phase19_erasure] reachability PROVED at n = "
        f"{N_TARGET_QUESTIONS}: best attainable (0 successes, a perfect erasure) = "
        f"{assert_erasure_floor_reachable(N_TARGET_QUESTIONS, lock_erasure_floor)!r}"
    )


def _tokenizer():
    import phase14_recall as recall  # LAZY — its TOKENIZER_PATH is the one every phase reads

    from personacore.tokenizer import from_json  # LAZY — the frozen production artifact

    return from_json(recall.TOKENIZER_PATH)


def _cmd_cal_corpus():
    """Build and WRITE the blind calibration corpus for the pinned fact. Refuses to clobber."""
    _prove(
        not CALIBRATION_CORPUS_PATH.exists(),
        f"{CALIBRATION_CORPUS_PATH} already exists — the corpus is the INPUT every calibration "
        "rate is scored from, and replacing it would silently reprice the (a) floor. Delete it in "
        "a reviewed commit if it genuinely must be regenerated",
    )
    fact = select_calibration_fact()
    corpus = build_calibration_corpus(_tokenizer(), fact)
    CALIBRATION_CORPUS_PATH.write_text(
        json.dumps(corpus, indent=JSON_INDENT, sort_keys=True), encoding="utf-8"
    )
    print(
        f"[phase19_erasure] calibration target slot {corpus['slot']}, "
        f"n = {corpus['n_questions']} questions {corpus['question_counts']} "
        f"({len(corpus['excluded'])} of {corpus['n_rendered']} rendered dropped by the "
        f"self-naming filter), sha256 {corpus['sha256']}"
    )


def _cmd_cal_train():
    """Retrain a FRESH calibration adapter (D6) on its own arm name and Phase 19 prefix."""
    import phase14_factset as factset  # LAZY — the fact set holds its material at module level
    import teach_persona as tp  # LAZY — same rule

    facts, second_person, replay_ratio = tp.arm_spec("cal_first_person_replay")
    print(
        tp.train_arm(
            CALIBRATION_ARM,
            facts=facts,
            family_ids=factset.TAUGHT_FAMILY_IDS,
            second_person=second_person,
            replay_ratio=replay_ratio,
            prefix=RETRAIN_PREFIX,
        )
    )


def _cmd_cal_erase():
    """Run M1 against the calibration adapter and score the erased arm over its own corpus."""
    import teach_persona as tp  # LAZY — it owns the adapter path

    from personacore.preflight import preflight_device

    fact = select_calibration_fact()
    adapter = tp.arm_outputs(CALIBRATION_ARM, prefix=RETRAIN_PREFIX)["adapter"]
    print(
        run_erasure_arm(
            "cal-erased",
            preflight_device(strict=True)["device"],
            corpus_path=CALIBRATION_CORPUS_PATH,
            adapter_path=adapter,
            components=_selected_components(adapter, fact),
        )["config"]
    )


def _selected_components(adapter_path, fact):
    """``select_ablation_prefix`` against one adapter, returning the prefix it stopped at."""
    import phase14_factset as factset  # LAZY — same rule
    import phase14_recall as recall  # LAZY — the loader every measurement goes through
    import phase18_extraction as extraction  # LAZY — CORE_SLOTS and the taught values

    from personacore.preflight import preflight_device

    device = preflight_device(strict=True)["device"]
    model, _cfg, tok, forbid, artifact = recall.load_adapted_model(device, adapter_path)
    taught = {f.slot: f.value for f in factset.LOCKED_FACTS}
    chosen = select_ablation_prefix(
        model,
        tok,
        device,
        artifact,
        slot=fact.slot,
        value=fact.value,
        references=reference_set_for_calibration(fact.slot, fact),
        collateral={
            slot: (taught[slot], extraction.reference_set_for(slot))
            for slot in extraction.CORE_SLOTS
        },
        dialogue_ppl=lambda: dialogue_ppl_pair(model, device, forbid),
    )
    print(
        f"[phase19_erasure] M1 stopped at k = {chosen['k']} of {chosen['cap']} "
        f"(stopped = {chosen['stopped']}); curve at {[r['prefix'] for r in chosen['curve']]}"
    )
    return chosen["ordered"][: chosen["k"]]


def _cmd_noise_floors():
    """The (b) seed-stride replicate on the UNERASED adapter — the arm parity is NOT asserted."""
    from personacore.preflight import preflight_device

    budget = json.loads(PHASE18_ARM_RECORD_PATH.read_text(encoding="utf-8"))["config"]["k"]
    print(
        run_erasure_arm(
            "replicate",
            preflight_device(strict=True)["device"],
            seed_stride=lambda entry: replicate_seed_stride(entry["seed_index"], budget),
        )["config"]
    )


def _cmd_erase():
    """M1 on the PRODUCTION adapter over Phase 18's committed corpus — parity asserted."""
    import phase14_factset as factset  # LAZY — the fact set holds its material at module level
    import phase14_recall as recall  # LAZY — ADAPTER_PATH is the production artifact

    from personacore.preflight import preflight_device

    target = {f.slot: f for f in factset.LOCKED_FACTS}[TARGET_SLOT]
    print(
        run_erasure_arm(
            "erased",
            preflight_device(strict=True)["device"],
            components=_selected_components(recall.ADAPTER_PATH, target),
        )["config"]
    )


def _cmd_retrain():
    """M2 (ERASE-02): retrain the reference arm minus the target, then score it."""
    import phase14_factset as factset  # LAZY — the fact set holds its material at module level
    import teach_persona as tp  # LAZY — same rule

    from personacore.preflight import preflight_device

    target = {f.slot: f for f in factset.LOCKED_FACTS}[TARGET_SLOT]
    facts, second_person, replay_ratio = retrain_arm_spec(target.id)
    tp.train_arm(
        RETRAIN_ARM,
        facts=facts,
        family_ids=factset.TAUGHT_FAMILY_IDS,
        second_person=second_person,
        replay_ratio=replay_ratio,
        prefix=RETRAIN_PREFIX,
    )
    print(
        run_erasure_arm(
            "retrain",
            preflight_device(strict=True)["device"],
            adapter_path=tp.arm_outputs(RETRAIN_ARM, prefix=RETRAIN_PREFIX)["adapter"],
        )["config"]
    )


def _cmd_representational():
    """The DESCRIPTIVE read: per-cell ΔW cosine and Fisher overlap. No gate, by construction."""
    import phase14_recall as recall  # LAZY — ADAPTER_PATH and the slim base
    import teach_persona as tp  # LAZY — the retrain arm's adapter

    from personacore.checkpoint import load_adapter, load_slim

    w0 = load_slim(recall.CONVBASE_SLIM)["model"]
    taught = delta_w_cells(load_adapter(recall.ADAPTER_PATH), w0)
    other = delta_w_cells(
        load_adapter(tp.arm_outputs(RETRAIN_ARM, prefix=RETRAIN_PREFIX)["adapter"]), w0
    )
    print(REPRESENTATIONAL_READ_LABEL)
    print(delta_w_cosine(taught, other))


def _cmd_report():
    """Render the report from the committed arm records — every gated number via the verdict."""
    erased, replicate = _load_arm("erased"), _load_arm("replicate")
    target_id = target_fact_id(erased["per_fact"])
    pre, post = erased["pre_erasure"], erased
    deltas = nontarget_deltas(pre["per_fact"], post["per_fact"])
    target_row, pre_row = post["per_fact"][target_id], pre["per_fact"][target_id]
    budget = erased["config"]["k"]
    print(
        render_report(
            verdict=render_verdict(
                target_successes=target_row["n_answerable"],
                target_questions=target_row["n_questions"],
                target_floor=lock_erasure_floor(_calibration_rate()),
                nontarget_deltas=tuple(deltas.values()),
                nontarget_noise_floor=nontarget_noise_floor(
                    nontarget_deltas(replicate["pre_erasure"]["per_fact"], replicate["per_fact"])
                ),
                dialogue_ppl=post["dialogue_ppl"]["adapter_on"],
                dialogue_ppl_noise_floor=dialogue_noise_floor(
                    *(post["dialogue_ppl"]["adapter_on"], pre["dialogue_ppl"]["adapter_on"])
                ),
                retention_ppl=post["retention_ppl"],
                zero_results_have_nll=zero_results_have_nll(erased),
            ),
            target={
                "n_draws": target_row["n_questions"] * budget,
                "pre_successes": pre_row["n_answerable"],
                "pre_questions": pre_row["n_questions"],
                "pre_draws": pre_row["n_questions"] * budget,
            },
            cal_rate=_calibration_rate(),
            nontargets=tuple(
                {
                    "slot": pre["per_fact"][fid]["slot"],
                    "pre_successes": pre["per_fact"][fid]["n_answerable"],
                    "pre_questions": pre["per_fact"][fid]["n_questions"],
                    "pre_draws": pre["per_fact"][fid]["n_questions"] * budget,
                    "post_successes": post["per_fact"][fid]["n_answerable"],
                    "post_questions": post["per_fact"][fid]["n_questions"],
                    "post_draws": post["per_fact"][fid]["n_questions"] * budget,
                }
                for fid in sorted(deltas)
            ),
            capability={
                "dialogue_ppl": pre["dialogue_ppl"]["adapter_on"],
                "retention_ppl": pre["retention_ppl"],
            },
            representational={"cosine": {}, "fisher": {}},
            provenance={
                "git_sha": erased["config"]["git_sha"],
                "device": erased["config"]["device"],
                "parity": {key: erased["config"][key] for key in PARITY_KEYS},
            },
        )
    )


def _calibration_rate():
    """The BLIND rate the (a) floor is derived from, read off the calibration arm's own record."""
    record = _load_arm("cal-erased")
    rows = record["pre_erasure"]["per_fact"]
    successes = sum(row["n_answerable"] for row in rows.values())
    questions = sum(row["n_questions"] for row in rows.values())
    _prove(
        questions,
        "the calibration arm recorded no questions, so its rate is a division by nothing and the "
        "floor would be derived from it",
    )
    return successes / questions


_SUBCOMMAND_TABLE = {
    "cal-corpus": _cmd_cal_corpus,
    "cal-train": _cmd_cal_train,
    "cal-erase": _cmd_cal_erase,
    "noise-floors": _cmd_noise_floors,
    "erase": _cmd_erase,
    "retrain": _cmd_retrain,
    "representational": _cmd_representational,
    "report": _cmd_report,
    "target": _cmd_target,
    "floor": _cmd_floor,
}

_prove(
    tuple(_SUBCOMMAND_TABLE) == SUBCOMMANDS,
    f"the dispatch table holds {tuple(_SUBCOMMAND_TABLE)} against the committed {SUBCOMMANDS}. "
    "The published set and the runnable set must be ONE set: a name with no handler is a "
    "subcommand a later plan would have to add code for, which is a commit to this file",
)


if __name__ == "__main__":  # pragma: no cover - the closed invocation surface, never a test suite
    main(sys.argv[1:])
