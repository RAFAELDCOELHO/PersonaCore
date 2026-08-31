"""GATE-05'S PRODUCER — the SEVENTH producerless kwarg of `mitigation_point_verdict` (D-46).

`scripts/mitigation_gate.py::mitigation_point_verdict` takes 21 keyword-only arguments. Measured
across the 20 committed Phase-25 plans, SEVEN had zero producers: six are condition (c) — closed by
`scripts/phase25_condition_c.py` (D-45…D-50) — and the seventh is `zero_extraction_has_nll`, which
is this module. The two together close all seven.

WHY THE FLAG IS NOT OPTIONAL, MEASURED LIVE RATHER THAN ARGUED
--------------------------------------------------------------
`mitigation_point_verdict` has TWO early returns **before** `reasons = []`. The second fires at
`point_extraction_successes == 0 and not zero_extraction_has_nll` and returns INCONCLUSIVE with a
SINGLE reason — the one sliced into `GATE05_EARLY_RETURN_TEXT` below. Measured at HEAD on the real
gate with the never-taught anchors `(0, 416)`, the governing retention floor
`0.008681618994239138` and `point_retention_ppl=3.80`:

    zero_extraction_has_nll=False -> INCONCLUSIVE  n_reasons=1  ZERO TOLERANCE present: False
    zero_extraction_has_nll=True  -> PASS          n_reasons=4  ZERO TOLERANCE present: True

Same point, same twenty other kwargs. Without the flag such a point never reaches (a), (b) or (c)
at all, so condition (a)'s ZERO TOLERANCE sentence is STRUCTURALLY UNREACHABLE for it —
see `PRE_REGISTERED_NULL_IS_ZERO_EXTRACTION`.

WHY EIGHT SLOTS, AND WHY THEY ARE RESOLVED RATHER THAN COUNTED
--------------------------------------------------------------
The gate is the 8 LOCKED facts at BOTH capacities. They are the shared privacy unit present in n=8
AND in n=64, so a flag computed over them is ONE COMPARABLE QUANTITY ACROSS CAPACITIES — which is
D-29's own reason for crossing both legs. The evidence for "these eight" is that TWO independently
committed tuples name the same set: `phase18_extraction.CORE_SLOTS` (a module literal in the
fixture's own order) and `phase19_erasure.CORE_GATED_SLOTS` (derived from the published
`TARGET_RANKING`, a different order). The set equality is PROVED at import. A length check alone
would be satisfied by any eight names, which is the substitution T-25-129 exists to refuse.

The full taught set — 8 at n=8, 64 at n=64 per D-37's in/out population — is dispatched and reported
BESIDE the flag and never enters a verdict. That is D-39's architecture (measure the mechanism, keep
it outside the gate) and D-05's (both tiers dispatched, one tier gates). See `GATE05_GOVERNS`.

HOW THE FROZEN CONSTANTS ARE READ, AND WHY NOT BY IMPORT
--------------------------------------------------------
`scripts/phase18_extraction.py` is ANCESTRY-GUARDED and `scripts/phase19_erasure.py` is byte-frozen;
both are READ here and neither is edited. But MEASURED at authoring time, importing either one puts
`torch` in `sys.modules`, and this module's own acceptance gate is that the constants and the
predicate import on CPU with NO torch loaded (the discipline `scripts/phase25_condition_c.py`,
`scripts/phase25_record.py` and `scripts/plot_phase25.py` hold). So the committed tuples are
resolved BY NAME from their own source through `ast.literal_eval` — the same names, the same
committed values, no retyped copy, and no import. `phase18_extraction.measure_exposure` is
imported LAZILY inside `measure_gate05`, the only function that touches a model.

`mitigation_gate` is torch-free and is imported at module scope, because
`GATE05_EARLY_RETURN_TEXT` must be sliced from the live `inspect.getsource` of the frozen verdict
rather than retyped.
"""

import ast
import inspect
import pathlib

import mitigation_gate

_SCRIPTS = pathlib.Path(__file__).resolve().parent


def _prove(condition, message):
    """``SystemExit`` on a broken invariant — `mitigation_gate._prove`'s register, this prefix.

    ``SystemExit`` and deliberately NOT ``assert``: an ``assert`` is strippable under ``-O``, and a
    proof that disappears under an optimisation flag is not a proof.
    """
    if not condition:
        raise SystemExit(f"[phase25_gate05] {message}")


def _committed_literal(module_stem, name):
    """The MODULE-LEVEL literal ``name`` from ``scripts/<module_stem>.py``, without importing it.

    Only ``tree.body`` is scanned, so a same-named assignment inside a function cannot be picked up
    instead. ``ast.literal_eval`` refuses anything that is not a literal, so this can never
    silently evaluate a derivation.
    """
    source = (_SCRIPTS / f"{module_stem}.py").read_text(encoding="utf-8")
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise SystemExit(
        f"[phase25_gate05] {name} is not a module-level literal assignment in "
        f"scripts/{module_stem}.py. This module reads the frozen constants BY NAME from their own "
        "source instead of importing them (the import pulls torch) and instead of retyping them "
        "(a retyped copy is free to stop agreeing). A name that no longer resolves means the "
        "frozen file moved, and the correct response is to read it, not to hard-code the value"
    )


# =============================================================================================
# ===== (a) THE GATED SET, RESOLVED FROM TWO AGREEING COMMITTED TUPLES (D-46, T-25-129) =====
# =============================================================================================

GATE05_SLOTS = tuple(_committed_literal("phase18_extraction", "CORE_SLOTS"))

# `phase19_erasure.CORE_GATED_SLOTS` is `tuple(row[0] for row in TARGET_RANKING)` — a derivation,
# so the LITERAL that is read is the ranking it derives from, and the same one-line derivation is
# reproduced here. Different order, same set: that is the agreement being proved.
_CORE_GATED_SLOTS = tuple(row[0] for row in _committed_literal("phase19_erasure", "TARGET_RANKING"))

_prove(
    set(GATE05_SLOTS) == set(_CORE_GATED_SLOTS),
    f"phase18_extraction.CORE_SLOTS {sorted(GATE05_SLOTS)} and phase19_erasure.CORE_GATED_SLOTS "
    f"{sorted(_CORE_GATED_SLOTS)} name different sets. The eight locked facts are resolved from "
    "TWO agreeing committed tuples rather than chosen from one and hoped about: they are the "
    "shared privacy unit present in n=8 AND n=64, and a flag computed over them is one comparable "
    "quantity across capacities (D-29's own reason for crossing both legs). Two committed tuples "
    "disagreeing is a real defect in one of them, not a reason to pick a side",
)
_prove(
    len(GATE05_SLOTS) == 8,
    f"the gated set has {len(GATE05_SLOTS)} slots, not eight. The count is a CONSEQUENCE of the "
    "two tuples agreeing and never the criterion: any eight names would satisfy a length check, "
    "which is exactly the substitution T-25-129 exists to refuse",
)

EXPOSURE_RECORD_KEYS = tuple(_committed_literal("phase18_extraction", "EXPOSURE_RECORD_KEYS"))
NLL_FRAMES = tuple(_committed_literal("phase18_extraction", "NLL_FRAMES"))
NLL_REDUCTIONS = tuple(_committed_literal("phase18_extraction", "NLL_REDUCTIONS"))
ADMISSIBLE_NLL_FRAME = _committed_literal("phase18_extraction", "ADMISSIBLE_NLL_FRAME")
ADMISSIBLE_NLL_REDUCTION = _committed_literal("phase18_extraction", "ADMISSIBLE_NLL_REDUCTION")

REQUIRED_NLL_COLUMNS = len(NLL_FRAMES) * len(NLL_REDUCTIONS)

_prove(
    ADMISSIBLE_NLL_FRAME in NLL_FRAMES and ADMISSIBLE_NLL_REDUCTION in NLL_REDUCTIONS,
    f"the admissible pair ({ADMISSIBLE_NLL_FRAME!r}, {ADMISSIBLE_NLL_REDUCTION!r}) is not among "
    f"the published frames {NLL_FRAMES} x reductions {NLL_REDUCTIONS}. The pair the gate reads has "
    "to be one of the columns that are required, or 'six published and one read' means nothing",
)


# =============================================================================================
# ===== (e) THE EARLY RETURN THIS MODULE EXISTS FOR — SLICED FROM SOURCE, NEVER RETYPED =====
# =============================================================================================

_VERDICT_SOURCE = inspect.getsource(mitigation_gate.mitigation_point_verdict)


def _early_return_text(source):
    """The second early return's reason, SLICED from the frozen source's own physical line.

    Resolved through ``inspect.getsource`` of the ONE function, never by grepping
    ``scripts/mitigation_gate.py``: that file discusses ``zero_extraction_has_nll``, ``nll`` and
    ``exposure`` in prose and in string literals, so a file-wide text search reads paragraphs as
    evidence. The uniqueness of the marker INSIDE the resolved function is proved before the slice,
    so the extraction cannot silently move to a second occurrence a later edit introduces.
    """
    marker = "cannot distinguish"
    _prove(
        source.count(marker) == 1,
        f"{marker!r} occurs {source.count(marker)} times in mitigation_point_verdict's source, "
        "so the slice is ambiguous. This text is the reason of the SECOND pre-`reasons` early "
        "return and it is quoted rather than paraphrased precisely so a reader can check it "
        "against the frozen file",
    )
    line = next(candidate for candidate in source.splitlines() if marker in candidate)
    return line.strip().strip('"')


GATE05_EARLY_RETURN_TEXT = _early_return_text(_VERDICT_SOURCE)

_prove(
    GATE05_EARLY_RETURN_TEXT in _VERDICT_SOURCE
    and "cannot distinguish" in GATE05_EARLY_RETURN_TEXT,
    "GATE05_EARLY_RETURN_TEXT is not a substring of mitigation_point_verdict's own source. A "
    "paraphrase of a pre-registered refusal is not the refusal: it is free to drift into a softer "
    "sentence than the one committed, and nothing would notice",
)

PRE_REGISTERED_NULL_IS_ZERO_EXTRACTION = (
    "THE PRE-REGISTERED NULL IS ZERO EXTRACTION UNDER HIGH NOISE. `mitigation_point_verdict` "
    "returns INCONCLUSIVE at `point_extraction_successes == 0 and not zero_extraction_has_nll`, "
    "and that return fires BEFORE `reasons = []`, so such a point never reaches (a), (b) or (c) "
    "at all — it comes back with exactly ONE reason and condition (a)'s ZERO TOLERANCE sentence "
    "is structurally unreachable for it. Without this producer that is the DP arm's ENTIRE "
    "HIGH-NOISE END: the region where the expected result lives would read 'we could not tell' "
    "exactly where the pre-registered null was expected to appear, and an unreadable region is "
    "not a negative result. Measured at HEAD on the real gate, same point either way: "
    "False -> INCONCLUSIVE with 1 reason and no ZERO TOLERANCE sentence; "
    "True -> 4 reasons with the ZERO TOLERANCE sentence present."
)

GATE05_GOVERNS = (
    "ONLY THE GATED TIER FEEDS `zero_extraction_has_nll`. The gated tier is the 8 LOCKED facts — "
    "the shared privacy unit present at BOTH capacities, which is what makes the flag one "
    "comparable quantity across n=8 and n=64 (D-29). The REPORTED tier is the point's FULL taught "
    "set (8 at n=8, 64 at n=64 per D-37's in/out population) and it is DIAGNOSTIC INFORMATION THAT "
    "NEVER ENTERS A VERDICT: it is dispatched and published beside the flag, and none of its "
    "fields is a keyword argument of `mitigation_gate.mitigation_point_verdict`. That is D-39's "
    "architecture applied to the refusal column and D-05's applied to the two extraction tiers — "
    "both tiers dispatched, one tier gates. Measured cost of the reported tier at n=64: ONE extra "
    "forward pass over the 56 filler facts, because the 8 gated records are reused rather than "
    "re-measured."
)


# =============================================================================================
# ===== (b) THE PHASE-25 PREDICATE — the frozen RULE shared, the Phase-19 SCHEMA not =====
# =============================================================================================


def gate05_exposure_gaps(exposure):
    """Every reason `zero_extraction_has_nll` would return False, each naming its ``fact_id``.

    SEPARATE FROM THE FLAG ON PURPOSE, and the frozen code says why in its own words. The gate reads
    a BOOLEAN, and a ``(False, reason)`` return would be TRUTHY — ``not (False, "...")`` is
    ``False`` — so a caller passing the pair straight through would silently disarm the INCONCLUSIVE
    branch on exactly the run that needed it (`phase19_erasure.zero_result_exposure_gaps`'s
    docstring, measured). The reasons live here; the flag stays a plain ``bool``, and
    `prove_flag_is_a_bool` refuses the pair at runtime rather than warning about it in a comment.

    ALL SIX FRAME x REDUCTION VALUES ARE REQUIRED COLUMNS even though the gate reads only
    (`ADMISSIBLE_NLL_FRAME`, `ADMISSIBLE_NLL_REDUCTION`) = ('ans1', 'mean'). Six published and one
    read is what makes a POST-NULL SWITCH VISIBLE INSTEAD OF CONVENIENT: a frame or reduction chosen
    after seeing which one gives the wanted answer is an edit to a published column set, not a
    quiet re-read of a number that was already there.

    WHY `phase19_erasure.zero_results_have_nll` IS NOT CALLED, stated as plainly as the rule it
    shares. That predicate iterates a PRE/POST exposure PAIR — the arm record's own exposure block
    AND the one nested under its erasure baseline — because Phase 19 measures movement, and an
    exposure rank published with no baseline is a number with nothing to have moved from. A Phase-25
    SWEEP POINT HAS NO ERASURE and therefore has no such pair. Manufacturing that nested block to
    satisfy the predicate would make the flag A LIE ABOUT WHAT WAS MEASURED: it would assert a
    baseline reading that no forward pass produced (T-25-127). So this predicate is written over
    ONE exposure block and reuses the frozen KEY TUPLE, FRAME and REDUCTION tuples, not the schema.

    Returns an empty tuple when nothing is wrong, so the flag below is one negation and no
    interpretation.
    """
    import phase14_factset as factset  # LAZY — fact material stays out of this module's scope

    fact_ids = {fact.slot: fact.id for fact in factset.LOCKED_FACTS}
    by_slot = {entry["slot"]: entry for entry in exposure}
    gaps = []

    for slot in GATE05_SLOTS:
        fact_id = fact_ids.get(slot, slot)
        entry = by_slot.get(slot)
        if entry is None:
            gaps.append(
                f"{fact_id} carries no exposure record for slot {slot!r}. Teacher-forced NLL is "
                f"required for ALL {len(GATE05_SLOTS)} locked facts at BOTH capacities: a zero "
                "with no NLL cannot separate 'the fact is absent' from 'the probe was too weak', "
                "and the locked eight are the only privacy unit present in n=8 and n=64 alike"
            )
            continue
        if tuple(entry) != EXPOSURE_RECORD_KEYS:
            gaps.append(
                f"{fact_id}'s exposure record carries keys {tuple(entry)}, not the committed "
                f"{EXPOSURE_RECORD_KEYS}. A record that lost a key publishes an exposure figure "
                "implying a precision it does not have"
            )
            continue
        for frame in NLL_FRAMES:
            if frame not in entry["nll"]:
                gaps.append(
                    f"{fact_id}'s exposure record has no {frame!r} NLL. All "
                    f"{REQUIRED_NLL_COLUMNS} frame x reduction values are REQUIRED columns even "
                    f"though the gate reads one pair ({ADMISSIBLE_NLL_FRAME!r}, "
                    f"{ADMISSIBLE_NLL_REDUCTION!r}) — six published and one read is what makes a "
                    "post-null switch visible instead of convenient"
                )
                continue
            for reduction in NLL_REDUCTIONS:
                value = entry["nll"][frame].get(reduction)
                if value is None or value != value or abs(value) == float("inf"):
                    gaps.append(
                        f"{fact_id}'s {frame}/{reduction} NLL is {value!r}, which is not finite. "
                        "A null beside a zero extraction IS the unmeasured case this clause exists "
                        "to refuse, and it is the pre-registered null's own region of the curve"
                    )
    return tuple(gaps)


# =============================================================================================
# ===== (c) THE FLAG — A PLAIN `bool`, WITH THE TRUTHY-PAIR TRAP REFUSED (T-25-125) =====
# =============================================================================================


def zero_extraction_has_nll(exposure):
    """`mitigation_point_verdict`'s own ``zero_extraction_has_nll`` kwarg. Returns a plain ``bool``.

    One negation of `gate05_exposure_gaps` and no interpretation. ITS WHOLE PURPOSE is to separate
    "the fact is absent" from "the probe was too weak" — and THE PRE-REGISTERED NULL PRODUCES
    EXACTLY THE ZERO THAT TRIGGERS THE BRANCH IT DISARMS, which is why the return type is proved
    here rather than trusted.
    """
    flag = not gate05_exposure_gaps(exposure)
    _prove(
        type(flag) is bool,
        f"the flag came back as {type(flag)!r}. The gate reads `not zero_extraction_has_nll`, so "
        "a non-bool is read for its TRUTHINESS and the branch silently changes meaning",
    )
    return flag


def prove_flag_is_a_bool(value, *, point_key):
    """Refuse anything whose ``type`` is not ``bool`` — a ``(False, reason)`` pair most of all.

    Raises ``SystemExit``, which derives from ``BaseException``: a test asserting this refusal must
    name ``SystemExit``, because ``pytest.raises(Exception)`` does NOT catch it.
    """
    _prove(
        type(value) is bool,
        f"point {point_key!r} carries zero_extraction_has_nll={value!r} of {type(value)!r}, not a "
        "plain bool. `mitigation_gate.mitigation_point_verdict` branches on "
        "`not zero_extraction_has_nll`, and a (False, reason) PAIR IS TRUTHY — "
        "`not (False, '...')` is `False` — so passing the pair straight through would SILENTLY "
        "DISARM the INCONCLUSIVE branch ON EXACTLY THE RUN THAT NEEDED IT, which is the trap "
        "`phase19_erasure.zero_result_exposure_gaps` documents in its own docstring. The reasons "
        "belong in gate05_exposure_gaps; the flag stays a bool",
    )
    return value


# =============================================================================================
# ===== (d) THE MEASUREMENT — GATED TIER AND REPORTED TIER (D-46, D-05, D-39) =====
# =============================================================================================


def gate05_tier_slots(taught, n_facts):
    """``(gated_slots, reported_slots)`` for a point's taught set, with the subset proof.

    Split out of `measure_gate05` deliberately: the subset property is the thing that keeps the two
    tiers from diverging into different facts, and it is arithmetic over slot names — so it is
    checkable at n=64 with NO model and no forward pass, which is what keeps that criterion out of
    a skip count.
    """
    reported_slots = tuple(taught)
    _prove(
        len(reported_slots) == n_facts,
        f"the taught set carries {len(reported_slots)} slots while the point declares "
        f"n_facts={n_facts}. The reported tier IS the point's full taught set (D-37's in/out "
        "population), so a mismatch means the capacity being reported is not the capacity that "
        "was taught",
    )
    _prove(
        set(GATE05_SLOTS) <= set(reported_slots),
        f"the gated slots {sorted(set(GATE05_SLOTS) - set(reported_slots))} are absent from the "
        f"reported tier's {len(reported_slots)} slots. The gated tier MUST be a subset of the "
        "reported one or the two tiers have diverged into different facts, and the diagnostic "
        "published beside the flag would describe a different measurement than the flag does",
    )
    return GATE05_SLOTS, reported_slots


def measure_gate05(model, tok, device, *, taught, n_facts):
    """Teacher-forced exposure over the GATED eight and over the point's FULL taught set.

    ``taught`` maps slot -> taught value; ``n_facts`` is the point's capacity and must equal its
    length. Returns ``{"gated", "reported", "gated_slots", "reported_slot_count", "governs"}``.

    `phase18_extraction.measure_exposure` is called as the SCORER, in the shape
    `phase19_erasure.run_erasure_arm._capability()` uses, and this module owns its own loop — the
    Phase 23 separation D-09 preserves. The ancestry-guarded file is imported LAZILY here so the
    constants and the predicate above stay importable with no torch in ``sys.modules``.

    MEASURED COST OF THE REPORTED TIER AT n=64: one extra forward pass over the 56 filler facts.
    The eight gated records are REUSED rather than re-measured, so the reported tier costs exactly
    the slots the gated tier did not already cover — which is what makes D-46's "reported beside it"
    affordable at every one of the 44 points. See `GATE05_GOVERNS` for why none of it gates.
    """
    import phase18_extraction as extraction  # LAZY — importing it puts torch in sys.modules

    gated_slots, reported_slots = gate05_tier_slots(taught, n_facts)

    gated = [
        extraction.measure_exposure(model, tok, device, slot=slot, taught_value=taught[slot])
        for slot in gated_slots
    ]
    reported = {record["slot"]: record for record in gated}
    for slot in reported_slots:
        if slot in reported:
            continue
        reported[slot] = extraction.measure_exposure(
            model, tok, device, slot=slot, taught_value=taught[slot]
        )

    return {
        "gated": gated,
        "reported": [reported[slot] for slot in reported_slots],
        "gated_slots": gated_slots,
        "reported_slot_count": len(reported_slots),
        "governs": GATE05_GOVERNS,
    }
