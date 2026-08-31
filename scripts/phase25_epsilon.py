"""PHASE 25'S ONLY SANCTIONED EPSILON SURFACE — three required kwargs and an AST walk (FRONT-02).

FRONT-02 IS NOT "REPORT TWO NUMBERS". It is *an example-level epsilon can never be read as if it
bounded fact leakage*. D-28 meets it in its strongest form by showing the SIZE of the error that
confusing the granularities would make: 207.018 under the artifact's first-token-owns-draw rule and
262.944 under the frozen pin's overlap rule, both named, neither hidden, because
`results/phase21_multiplicity.json` itself records the discrepancy as
`"RECORDED, NOT RESOLVED — the pin is frozen and is not edited"`. Both figures are READ from that
record and are never retyped here; the record's own status string is carried through verbatim so a
reader sees the unresolved state rather than a resolution this phase is not entitled to make.

THE PROTECTION IS STRUCTURAL, NOT DOCUMENTARY. `report_epsilon` takes three keyword-only arguments
with NO DEFAULTS, so an omission raises `TypeError` from CPython's own arity check rather than from
a hand-written guard that could drift from the signature. That is
`scripts/mitigation_gate.py::mitigation_point_verdict`'s precedent, where twenty-one required
keyword arguments are paid deliberately: *"Trimming the list with defaults would let a caller
silently omit an anchor and still get a verdict, which is the failure the length is buying
protection from."* The length IS the protection, and so is the absence of a default.

ENFORCEMENT IS AN AST WALK, NEVER A GREP, AND THAT CHOICE IS MEASURED RATHER THAN PREFERRED.
Measured on `scripts/mitigation_gate.py` while this module was written: the token `epsilon` occurs
**42** times in the raw source, **26** of them inside `ast.Constant` string values — **2** in
`exists_clearing_point` and **23** in `capacity_comparison`, the 25 D-30 records — and **0** of them
resolve to an identifier in `EPSILON_NAMES`. A textual gate over that file reports a violation that
does not exist. `.planning/REQUIREMENTS.md`'s RPT-02 row records four independent instances of that
false-RED class in Phase 20 alone. `scripts/phase25_prereg.py` is this phase's second instance: 10
textual occurrences, 0 resolving names.

WHAT THIS MODULE IS ALLOWED TO IMPORT. Stdlib, `scripts/mitigation_unit.py` (frozen, READ ONLY —
the privacy unit, the with-replacement hazard and `DELTA`) and
`personacore.privacy.accountant.epsilon_for` (the per-point epsilon, stdlib `math` only). No torch,
no numpy, no network. `epsilon_for(0.5, 200, 1e-5) = 519.6981942303134` is bit-identical to the
epsilon already committed in `results/phase23_noised_dp_n64_sigma0p500000.json`, and
`epsilon_for(0.0, 200, 1e-5)` returns `math.inf` — which is why the sigma = 0 control's epsilon is
`None` rather than a number, and why `curve_total` refuses both spellings of it.
"""

import json
import math
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import mitigation_unit  # noqa: E402  (needs the sys.path insert above; scripts/ is not a package)

from personacore.privacy.accountant import epsilon_for  # noqa: E402  (same)

# The two committed records this module reads. Neither figure below is retyped as a literal: a
# number nobody can trace back to the artifact that produced it is a number nobody can correct.
MULTIPLICITY_RECORD = _ROOT / "results" / "phase21_multiplicity.json"
SIGMA_ZERO_RECORD = _ROOT / "results" / "phase23_sigma_zero.json"


# ---------------------------------------------------------------------------------------------
# D-29's three declarations. Each is a `governs`-style string, and each states a LIMIT of the
# curve total rather than a property of it — the limits are the part a reader will otherwise
# supply for themselves, wrongly and in the flattering direction.
# ---------------------------------------------------------------------------------------------
SELECTION_ACCOUNTED = False

SELECTION_ACCOUNTED_REASON = (
    "GOVERNS `selection_accounted`. It is False, and it is reported rather than omitted. Choosing "
    "a best point after seeing the sweep's results is ADAPTIVE SELECTION over the private data, "
    "and no epsilon in this phase accounts for it: the published per-point epsilons bound the "
    "mechanism that produced each point, not the search that picked one out of forty-four. A "
    "reader who sees the frontier's best point quoted with its own epsilon is looking at a bound "
    "for a mechanism nobody ran — the one that would have committed to that point in advance. "
    "Accounting for it would require a selection mechanism this phase does not implement, so the "
    "honest report is the flag, not a wider number chosen to look like it covers the gap."
)

CONTROL_HAS_NO_EPSILON = (
    "GOVERNS THE sigma = 0 CONTROL. It carries NO epsilon at all, and it is never summed as zero. "
    "`personacore.privacy.accountant.epsilon_for(0.0, 200, 1e-5)` returns `math.inf`, which is the "
    "mathematically correct value and not a guard: the deterministic mechanism has no finite "
    "(epsilon, delta) bound. The control is an adapter trained on the SAME EIGHT LOCKED FACTS with "
    "NO PRIVACY AT ALL. So once the control is published, NO JOINT BOUND OVER ALL PUBLISHED "
    "ARTIFACTS EXISTS — the curve total below bounds the noised DP points and nothing else, and a "
    "reader who adds the control to that set is holding a set with an unbounded member. Summing "
    "the control as 0.0 would state the exact opposite of the truth, which is why `curve_total` "
    "refuses a `None` entry and an infinite one by name rather than skipping either quietly."
)

TOTAL_CROSSES_BOTH_LEGS = (
    "GOVERNS THE SCOPE OF THE CURVE TOTAL. It crosses BOTH capacity legs, n = 8 and n = 64, and is "
    "never split per leg. The eight locked facts appear in n = 8 AND in n = 64, so the same fact "
    "is exposed by points on both legs; a per-leg split would report two smaller numbers while "
    "hiding exactly the cumulative exposure that matters most to the fact-level unit this project "
    "protects. The total is BASIC (sequential) composition — the plain sum of the epsilons of the "
    "noised DP points ACTUALLY PUBLISHED, at total delta = k * delta. It is conservative, it is "
    "computable from the accountant already committed, and it introduces ZERO new chosen constant: "
    "`delta` arrives from `scripts/mitigation_unit.py::DELTA`, and a tighter advanced-composition "
    "bound would be a new constant chosen after the curve was visible."
)


# ---------------------------------------------------------------------------------------------
# Section C5's correction, made and recorded. The DECISION is this module's, because the precedent
# it was supposed to inherit does not exist.
# ---------------------------------------------------------------------------------------------
CONTROL_EPSILON_FIELD_FORM = (
    'PHASE 25\'S CONTROL-POINT RECORD WRITES THE KEY "epsilon" WITH THE VALUE null, EXPLICITLY, '
    'PLUS A SIBLING "epsilon_omitted_reason". IT NEVER OMITS THE KEY. Two committed promises '
    "want every point record to carry the same key set: FRONT-03's single-source promise (no bound "
    "requires a second file) and D-31's ORDERED `point_keys` hard equality, proved at the single "
    "write that assembles `results/phase25_frontier.json`. A MISSING KEY IS INDISTINGUISHABLE FROM "
    "A BUG — a reader cannot tell an absent epsilon from a writer that crashed before emitting it, "
    "and the ordered-key equality would fail on a shape difference rather than report a fact. AN "
    "EXPLICIT null IS A STATEMENT: this point has no epsilon, deliberately, for the reason its "
    "sibling field gives. `CONTROL_HAS_NO_EPSILON` is that reason."
)

SIGMA_ZERO_PRECEDENT_CORRECTION = (
    "CORRECTION, RECORDED IN PLACE (25-RESEARCH.md section C5). D-29 cites "
    "`results/phase23_sigma_zero.json` as recording `epsilon: None`, and offers it as the "
    "precedent the form above would inherit. THAT RECORD HAS NO `epsilon` KEY AT ALL. Measured "
    "while this module was written: 51 top-level keys, none of them named `epsilon` (the two that "
    "match a naive substring search are `composed_steps` and `clip_bind_count_covers_steps`, both "
    "of which contain `eps` only inside the word `steps` — itself a small instance of the same "
    "textual-matching hazard the AST gate exists to close). The plan and section C5 both state 43 "
    "top-level keys; the measured count today is 51, and the load-bearing half of the claim — that "
    "no key named `epsilon` exists — reproduces exactly. `sigma_zero_epsilon_absence()` below "
    "re-measures both halves at call time rather than asking a reader to trust this paragraph. "
    "THERE IS NO PRECEDENT TO INHERIT, SO `CONTROL_EPSILON_FIELD_FORM` IS A DECISION THIS PHASE "
    "MAKES, not a convention it continues."
)


EPSILON_NAMES = (
    "epsilon",
    "point_epsilon",
    "curve_total_epsilon",
    "eps",
    "epsilon_total",
    "epsilon_for",
)
"""THE IDENTIFIER NAMES D-30's AST GATE RESOLVES AGAINST. A NAME SET, NOT A PHRASE SET.

The distinction is the whole reason the gate is an AST walk. A phrase set would be matched against
TEXT, and text cannot tell an identifier from a docstring that discusses the identifier — which is
the false-RED class RPT-02 exists to close. These are names, and they are resolved against
`ast.Name.id`, `ast.Attribute.attr` and `ast.arg.arg` under EXACT equality: a name reaching a
`print`, an f-string, a `.format()` call or a `%` interpolation OUTSIDE this module's own file is a
bare epsilon, and the gate fails on it.

EXACT EQUALITY RATHER THAN SUBSTRING, AND THE DIFFERENCE IS MEASURED. On
`scripts/mitigation_gate.py` today, `ast.Name`/`ast.arg` nodes whose identifier CONTAINS `epsilon`
number **11** — `epsilon_independent_of_n`, `epsilon_gap` and `fallback_epsilon_tolerance`, none of
which is an epsilon being rendered — while nodes whose identifier IS a member of this tuple number
**0**. D-30 records the second reading. A substring resolver would go RED on the frozen gate for
the same reason a grep does, one layer deeper, so the gate and its demonstration both resolve by
membership in this tuple.
"""


def _multiplicity_record():
    """The committed Phase 21 record, parsed. Read at call time; nothing is cached or copied."""
    with MULTIPLICITY_RECORD.open(encoding="utf-8") as handle:
        return json.load(handle)


def sigma_zero_epsilon_absence():
    """Re-measure section C5's two claims about `results/phase23_sigma_zero.json`.

    Returns ``(n_top_level_keys, has_epsilon_key)``. Committed as a function rather than as a pair
    of literals so `SIGMA_ZERO_PRECEDENT_CORRECTION` is checkable rather than quotable: the count in
    that paragraph was 43 when the plan was written and 51 when it was executed, and only the second
    half of the claim — the absent key — is the one the decision rests on.
    """
    with SIGMA_ZERO_RECORD.open(encoding="utf-8") as handle:
        record = json.load(handle)
    return len(record), "epsilon" in record


def with_replacement_clause():
    """The sampler hazard, verbatim from frozen `mitigation_unit.PRIVACY_UNIT_ARITHMETIC`.

    Sliced from the pin rather than restated, because the pin is frozen and a paraphrase of a frozen
    statement is a second statement that can drift from it. This is the clause that makes the
    example-level number meaningless about a fact: the loader draws window start offsets WITH
    REPLACEMENT over a flat concatenated bin, so one fact is touched an unbounded number of times.
    """
    return mitigation_unit.PRIVACY_UNIT_ARITHMETIC.split("\n\n")[0]


def point_epsilon_for_sigma(sigma, *, steps, delta):
    """The per-point epsilon from the committed accountant, or ``None`` at the sigma = 0 control.

    `epsilon_for` returns `math.inf` at `sigma == 0.0` — the mathematically correct value for the
    deterministic mechanism, not a guard. This surface converts that to `None`, which is the value
    `CONTROL_EPSILON_FIELD_FORM` writes into the control's record as an explicit JSON `null`. The
    conversion happens HERE, once, so no caller has to decide what `inf` means.
    """
    value = epsilon_for(sigma, steps, delta)
    return None if math.isinf(value) else value


def dual_granularity_sentence(point_epsilon):
    """D-28: the REAL fact-level epsilon paired with the example-level COUNTERFACTUAL, both
    multiplicities named.

    The counterfactual is characterised by its MULTIPLICITY and never by a second epsilon number,
    because `results/phase21_multiplicity.json` states in its own provenance that no epsilon is
    computed anywhere in Phase 21. Inventing one here would be exactly the substitution UNIT-03
    refuses. Both figures and the record's `RECORDED, NOT RESOLVED` status are read from the record.
    """
    record = _multiplicity_record()
    pin = record["pin_discrepancy"]
    provenance = record["provenance"]
    return (
        f"FACT-LEVEL, AND IT IS THE ONLY GRANULARITY THAT GOVERNS THIS PATH: eps = "
        f"{point_epsilon!r} at the privacy unit {mitigation_unit.PRIVACY_UNIT!r}, at "
        f"q = {mitigation_unit.SAMPLING_RATE_Q!r} under fact-aligned accumulation, where the "
        f"per-step multiplicity of a protected fact is exactly 1 by construction. "
        f"EXAMPLE-LEVEL, THE COUNTERFACTUAL, AND IT BOUNDS NOTHING ABOUT A FACT: an accounting "
        f"done per example under the unaligned with-replacement sampler would have quoted the "
        f"flattering number a reader is likely to assume applies, over a multiplicity of "
        f"{pin['artifact_rule_figure']!r} draws per fact under the {pin['artifact_rule']!r} rule "
        f"(the artifact's own rule) or {pin['pin_figure']!r} under the "
        f"{pin['pin_figure_rule']!r} (the frozen pin's rule). BOTH ARE NAMED AND NEITHER IS "
        f"HIDDEN, because the record states the discrepancy's status as "
        f"{pin['status']!r} and reconciles the two exactly: {pin['reconciliation']!r} "
        f"NO EXAMPLE-LEVEL EPSILON NUMBER IS QUOTED BESIDE THEM, because the same record's "
        f"provenance sets epsilon_computed = {provenance['epsilon_computed']!r} and says: "
        f"{provenance['epsilon_note']!r} "
        f"THE REASON THE EXAMPLE-LEVEL GRANULARITY SAYS NOTHING ABOUT A FACT, quoted verbatim "
        f"from the frozen pin: {with_replacement_clause()!r}"
    )


def curve_total(published_point_epsilons, *, delta):
    """D-29: BASIC composition over the noised DP points ACTUALLY PUBLISHED.

    Total epsilon is the plain sum; total delta is ``len(published) * delta``. Conservative,
    computable from the accountant already committed, and ZERO new chosen constant — `delta` arrives
    from `scripts/mitigation_unit.DELTA`. The list is the points PUBLISHED, crossing both capacity
    legs; see `TOTAL_CROSSES_BOTH_LEGS`.

    Refuses a `None` entry and a non-finite one, both naming `CONTROL_HAS_NO_EPSILON`. Those are the
    two spellings of the sigma = 0 control's absent epsilon (`None` in a record, `math.inf` straight
    out of `epsilon_for`), and either one summed as zero would state the opposite of the truth. The
    control must be excluded DELIBERATELY by the caller, never absorbed quietly here.
    """
    values = list(published_point_epsilons)
    for index, value in enumerate(values):
        if value is None or not math.isfinite(value):
            raise ValueError(
                f"curve_total: entry {index} of {len(values)} is {value!r}, which is the sigma = 0 "
                f"control's absent epsilon and cannot enter a composition. CONTROL_HAS_NO_EPSILON: "
                f"{CONTROL_HAS_NO_EPSILON} Exclude the control deliberately at the call site; this "
                f"function will not skip it for you, because a silent skip and a deliberate "
                f"exclusion leave the same total and different evidence."
            )
    return math.fsum(values), len(values) * delta


def report_epsilon(*, point_epsilon, curve_total_epsilon, selection_accounted):
    """THE ONE SANCTIONED RENDERING OF AN EPSILON IN PHASE 25 (D-30).

    Three keyword-only arguments, NO DEFAULTS on any of them, so omitting one raises `TypeError`
    from CPython's own arity check. There is deliberately NO hand-written arity guard: a manual
    check is a second statement of the signature and can drift from it, while the signature cannot
    drift from itself. `scripts/mitigation_gate.py::mitigation_point_verdict` pays the same price
    twenty-one times over for the same reason.

    The return is a single sentence carrying all six required items together — the point epsilon,
    the curve-total epsilon, the selection-accounting flag, the privacy unit, the sampler statement
    and the multiplicity — because SC3's wording is that they appear in the SAME sentence. Splitting
    them across sentences is how a reader ends up quoting one without the others, which is the whole
    failure FRONT-02 names. D-28's dual-granularity sentence and D-29's declarations follow it.
    """
    record = _multiplicity_record()
    pin = record["pin_discrepancy"]
    headline = (
        f"AT THE PRIVACY UNIT {mitigation_unit.PRIVACY_UNIT!r} AND NOWHERE ELSE, this point's "
        f"eps = {point_epsilon!r} and the published curve's total eps = {curve_total_epsilon!r} "
        f"(basic composition at total delta = k * {mitigation_unit.DELTA!r}), with "
        f"selection_accounted = {selection_accounted!r}, under the fact-aligned sampler at "
        f"q = {mitigation_unit.SAMPLING_RATE_Q!r} whose per-step multiplicity of a protected fact "
        f"is exactly 1 by construction rather than by assumption — against the unaligned "
        f"with-replacement sampler's {pin['artifact_rule_figure']!r} draws per fact under the "
        f"{pin['artifact_rule']!r} rule and {pin['pin_figure']!r} under the "
        f"{pin['pin_figure_rule']!r}, a discrepancy the record's own status leaves as "
        f"{pin['status']!r}."
    )
    return "\n\n".join(
        (
            headline,
            dual_granularity_sentence(point_epsilon),
            SELECTION_ACCOUNTED_REASON,
            CONTROL_HAS_NO_EPSILON,
            TOTAL_CROSSES_BOTH_LEGS,
            CONTROL_EPSILON_FIELD_FORM,
            SIGMA_ZERO_PRECEDENT_CORRECTION,
        )
    )
