"""THE PER-POINT RECORD — D-10's one-attempt evidence, D-09's resume unit, D-31's assembly input.

D-34 IS THE HIGHEST-SEVERITY GUARD IN THIS PHASE, AND IT FIRES AT WRITE TIME.
Five fields — `composed_steps`, `composed_lot_sizes`, `records_per_lot`, `q`, `clip_norm` — are
read LIVE at the moment the bytes would be written and asserted against the pin under EXACT
equality. A divergence HALTS THE WHOLE SWEEP rather than logging a warning: a point whose live
mechanism drifted from the pin carries an epsilon THAT DOES NOT DESCRIBE WHAT HAPPENED, and 44 of
those assembled into a published frontier is the failure mode v4.0's research named as the worst
available. The guard costs an `==` on five values; the error it prevents costs the milestone.

The halt fires BEFORE the record dict is returned, deliberately: after the write, the record IS
evidence, and a diverged record written and then deleted leaves a hole in exactly the artifact set
`phase25_prereg.prove_first_attempt` reads.

`q` IS THE ONE GENUINELY NEW FIELD, AND ITS SOURCE IS `mitigation_unit.SAMPLING_RATE_Q = 1.0`.
MEASURED against `results/phase23_noised_dp_n64_sigma0p500000.json` while this module was written:
that record carries **37** top-level keys — the plan and section R3 both state 35, and the count is
corrected here rather than inherited — and four of D-34's five fields are already among them
(`composed_steps`, `composed_lot_sizes`, `records_per_lot`, `clip_norm`). THE LOAD-BEARING HALF
REPRODUCES EXACTLY: there is no `q` key at all, at either capacity.

D-26 IS WHY `q` IS PINNED RATHER THAN ASSUMED. `mitigation_unit.PRIVACY_UNIT_ARITHMETIC` names the
contrast verbatim: `get_batch_memmap_masked` draws window offsets WITH REPLACEMENT and with no
notion of where one fact ends and the next begins, touching a fact an expected 262.94 times over
1,600 draws — which is WHY an example-level accounting says nothing about a fact. The DP path does
NOT use that sampler for private data. Under fact-aligned accumulation (Phase 21 D-01/D-05/D-06)
the quantity is EXACTLY 1 PER MICRO-STEP, DETERMINISTIC BY CONSTRUCTION, and that is what makes
`SAMPLING_RATE_Q = 1.0` honest rather than assumed. Because it is honest by construction it is also
the field most likely to go silently wrong if the sampler is ever swapped back — so it is read LIVE
and it halts the sweep.

D-27 IS WHY THREE OF THE FIVE ARE THE COMPOSITION FIELDS. T = 200 at both capacities is MEASURED,
not inferred: `results/phase23_sigma_zero.json` records `composed_steps 200` / `composed_lot_sizes
[8]` / `records_per_lot 8`, and `results/phase23_noised_dp_n64_sigma0p500000.json` records
`composed_steps 200` / `composed_lot_sizes [64]` / `records_per_lot 64`. `grad_accum_steps =
n_facts` governs micro-steps INSIDE one optimizer step; composed T is optimizer steps and is
capacity-independent.

WHAT THIS MODULE IMPORTS, AND WHY THE LINE FALLS WHERE IT DOES.
Stdlib plus the torch-free frozen modules plus the four Phase-25 siblings, at module scope.
Everything that puts torch in `sys.modules` is imported LAZILY inside the function that needs it —
the discipline `scripts/phase25_condition_c.py` states and `scripts/plot_phase15.py` established.
MEASURED at authoring time on a clean interpreter: `phase14_recall`, `phase18_extraction` and
`phase21_unit_record` ALL put torch in `sys.modules` on import, while `mitigation_unit`,
`mitigation_budget`, `mitigation_gate`, `phase25_prereg`, `phase25_epsilon`, `phase25_condition_c`
and `phase25_gate05` put in neither torch nor numpy. The record builder and the assembly must run
on CPU from a fresh clone, and a module that drags a 2 GB framework in to serialise a dict cannot.

`phase18_extraction`'s three constants are read WITHOUT IMPORTING IT, through
`phase25_gate05._committed_literal` — the same reader that module already uses on the same file,
for the same recorded reason (the import pulls torch; a retyped copy is free to stop agreeing).
The tests import the real module and assert the two agree, which is where an import that costs two
seconds belongs.
"""

import datetime
import fnmatch
import hashlib
import importlib.metadata
import inspect
import json
import os
import pathlib
import platform
import sys
import tempfile

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import mitigation_budget  # noqa: E402  (needs the sys.path insert above; scripts/ is not a package)
import mitigation_gate  # noqa: E402  (same)
import mitigation_unit  # noqa: E402  (same)
import phase25_condition_c  # noqa: E402  (same)
import phase25_epsilon  # noqa: E402  (same)
import phase25_gate05  # noqa: E402  (same)
import phase25_prereg  # noqa: E402  (same)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402


def _prove(condition, message):
    """``SystemExit`` on a broken invariant — `mitigation_gate._prove`'s register, this prefix.

    ``SystemExit`` and deliberately NOT ``assert``: an ``assert`` is strippable under ``-O``, and a
    proof that disappears under an optimisation flag is not a proof. A test asserting one of these
    refusals must name ``SystemExit``: it derives from ``BaseException``, so
    ``pytest.raises(Exception)`` does NOT catch it.
    """
    if not condition:
        raise SystemExit(f"[phase25_record] {message}")


# =================================================================================================
# ===== (a) THE PATHS — THIS MODULE OWNS THEM, AND NOTHING ELSE SPELLS THEM (D-31) =====
# =================================================================================================

# ROADMAP.md's `results/phase2X_frontier.json` is a PLACEHOLDER, not a filename (D-31, correction 6
# in 25-CONTEXT). The artifact is named here, once, and every consumer imports this constant.
FRONTIER_RECORD = _ROOT / "results" / "phase25_frontier.json"

POINT_RECORD_DIR = _ROOT / "results"


def point_record_path(point_key_value):
    """One point's committed record, as an ABSOLUTE path under ``results/``.

    DELEGATES to `phase25_prereg.point_record_path`, which owns the naming rule and its charset
    refusal, and never re-derives it. Two derivations of one path is exactly how a writer and the
    one-attempt glob that watches it drift apart, and this repository has already shipped plans
    naming artifact paths the code refuses.
    """
    return _ROOT / phase25_prereg.point_record_path(point_key_value)


# The writer and the pre-registered glob are proved to agree AT IMPORT, on a real key. `fnmatch` is
# the same matcher a `git ls-files` consumer applies, so this is the property that matters rather
# than a string-prefix lookalike of it.
_GLOB_PROBE = point_record_path("dp_n8_sigma0p000000").relative_to(_ROOT)
_prove(
    fnmatch.fnmatch(str(_GLOB_PROBE), phase25_prereg.POINT_RECORD_GLOB),
    f"the writer produces {str(_GLOB_PROBE)!r}, which the pre-registered "
    f"{phase25_prereg.POINT_RECORD_GLOB!r} does not match. D-10's one-attempt rule reads that "
    "glob: a record filed where the glob is blind is not merely unwatched, it is invisible to the "
    "rule itself, and a second attempt at that point would be refused by nothing",
)

# `phase24_record._PUBLICATION_PATHSPEC`'s shape and its measured narrowing, verbatim in reasoning:
# what the recorded SHA claims is that the CODE and INPUTS at that commit reproduce these bytes.
# `.planning/` prose and repository housekeeping are provably not inputs — no number below moves
# when they do — and watching them makes the guard fire for reasons unrelated to reproducibility.
# The frontier artifact itself is excluded because the write that produces it is the write this
# pathspec guards.
_PUBLICATION_PATHSPEC = (
    "scripts",
    "src",
    "results",
    "artifacts",
    f":(exclude){FRONTIER_RECORD.relative_to(_ROOT)}",
)


# =================================================================================================
# ===== (b) THE POINT-KEY GRAMMAR (Claude's discretion under D-31) =====
# =================================================================================================

# `arm` keeps D-06's identity: the sigma=0 CONTROL is a real DP sweep point (CTRL-02) and is
# separated by PREFIX ONLY, which is what keeps D-01's bit-level reproduction reachable. Only the
# `dp_fn=None` seam-off comparator is renamed, and it is not a point in this set.
DP_ARMS = ("dp_n8", "dp_n64")
ADVERSARIAL_ARMS = ("adv_n8", "adv_n64")
ORDERED_ARMS = DP_ARMS + ADVERSARIAL_ARMS

AXIS_FOR_ARM = {
    "dp_n8": "sigma",
    "dp_n64": "sigma",
    "adv_n8": "ratio",
    "adv_n64": "ratio",
}

POINT_KEY_GRAMMAR = "{arm}_{axis}{value:.6f} with '.' written 'p'"
"""THE FORMAT, PINNED AS A DOCUMENTED STRING RATHER THAN LEFT TO A CALL SITE.

SIX DECIMALS AND A ``p``, and both halves are inherited rather than chosen. Phase 23 already named
its records `phase23_noised_dp_n64_sigma0p500000.json`, and `phase25_prereg.point_record_path`
refuses anything outside ``[A-Za-z0-9_-]`` — its docstring says so in its own words: *"that
restriction is also why sigma is rendered with the point written ``p`` everywhere in this phase"*.

FIXED WIDTH IS WHAT MAKES THE ORDER DETERMINISTIC: `sigma0p050000` and `sigma0p500000` sort in
numeric order as strings because every rendering has the same number of digits either side.

THE KEY ROUND-TRIPS; THE FLOAT DOES NOT, AND THAT IS STATED RATHER THAN GLOSSED.
`point_key(*parse_point_key(k))` reproduces `k` exactly for every key this module can build. But
six decimals do not reproduce 1.9090909090909092 — they give 1.909091 — so the KEY is a label and
the AUTHORITATIVE axis value is the record's own `sigma` / `adversarial_ratio` field, which carries
the full double. Anything reading a parameter out of a filename is reading the label.
"""


def _axis_for(arm):
    axis = AXIS_FOR_ARM.get(arm)
    _prove(
        axis is not None,
        f"arm {arm!r} has no axis in AXIS_FOR_ARM {sorted(AXIS_FOR_ARM)}. The two arms sweep "
        "DIFFERENT axes — DP sweeps sigma and adversarial sweeps a mixture ratio — so an arm with "
        "no declared axis would file a point under a name that states which parameter moved "
        "without anything having decided which parameter moved",
    )
    return axis


def point_key(arm, axis_value):
    """This point's key: ``{arm}_{axis}{value}`` at six decimals with the point written ``p``.

    REFUSES A NON-FINITE OR NEGATIVE AXIS VALUE, and the refusal is on the PROPERTY rather than on
    the name. 24-REVIEW WR-01 (fixed under D-41) is precisely this defect one layer down: a NaN or
    negative `adversarial_ratio` silently builds the CONTROL on the flat branch under an
    ADVERSARIAL name. Here the same input would render `sigmanan` or `ratio-1p000000` — both of
    which `phase25_prereg.point_record_path` happily accepts as charset-legal — and file a
    nonsense point in the middle of a pre-registered ordered key set. Phase 20 recorded this class
    twice in its own gap closures: a guard that refuses a NAME where the harm is a PROPERTY.
    """
    axis = _axis_for(arm)
    value = float(axis_value)
    _prove(
        value == value and value not in (float("inf"), float("-inf")),
        f"axis value {axis_value!r} for arm {arm!r} is not finite. A non-finite sweep coordinate "
        "renders to a key no ordering can place and names a point no mechanism can have run",
    )
    _prove(
        value >= 0.0,
        f"axis value {axis_value!r} for arm {arm!r} is negative. Neither axis admits one: sigma is "
        "a noise scale and the adversarial ratio is a mixture proportion, and a negative value on "
        "either would build the flat branch under a swept name (24-REVIEW WR-01's defect, fixed "
        "under D-41)",
    )
    key = f"{arm}_{axis}{value:.6f}".replace(".", "p")
    # Route the finished key through the pre-registration's own charset refusal rather than
    # restating it, so one rule governs both the key and the path derived from it.
    phase25_prereg.point_record_path(key)
    return key


def parse_point_key(key):
    """``(arm, axis, value)`` from a key built by :func:`point_key`. The inverse, proved by use.

    Arms are matched longest-first so `dp_n64` can never be read as `dp_n8` with a stray suffix.
    """
    for arm in sorted(ORDERED_ARMS, key=len, reverse=True):
        prefix = f"{arm}_{AXIS_FOR_ARM[arm]}"
        if key.startswith(prefix):
            rendered = key[len(prefix) :]
            _prove(
                rendered.count("p") == 1,
                f"point key {key!r} carries {rendered.count('p')} decimal points in its value "
                f"{rendered!r}. The grammar is {POINT_KEY_GRAMMAR!r} and it renders exactly one",
            )
            return arm, AXIS_FOR_ARM[arm], float(rendered.replace("p", "."))
    raise SystemExit(
        f"[phase25_record] point key {key!r} names none of the four arms {ORDERED_ARMS}. A key "
        "that does not parse cannot be ordered, and D-31 proves `point_keys` equality as a HARD "
        "equality at the frontier's single write"
    )


def ORDERED_POINT_KEYS():
    """The full 44-key tuple, RESOLVED LAZILY — never at import, never as a default argument.

    A FUNCTION AND NOT A CONSTANT, FOR A DATED REASON. `mitigation_budget.SIGMA_LADDER` does not
    exist until plan **25-12 (wave 5)**, while this module lands in **wave 2** and plan 25-10
    (wave 3) makes this its `--points` default. A module-level `ORDERED_POINT_KEYS()` call would be
    evaluated at IMPORT, and an `argparse` `default=ORDERED_POINT_KEYS()` would be evaluated when
    the PARSER IS CONSTRUCTED — so either form raises on every import in waves 2-4, which is every
    plan between here and 25-12. `getattr` at CALL time is the whole fix, and the absent attribute
    is answered with a refusal NAMING ITS PRODUCER rather than with a bare `AttributeError`.

    Every caller in this phase writes `ORDERED_POINT_KEYS()`, with parentheses.
    """
    ladder = getattr(mitigation_budget, "SIGMA_LADDER", None)
    _prove(
        ladder is not None,
        "mitigation_budget.SIGMA_LADDER does not exist yet. PLAN 25-12 (WAVE 5) PINS IT, as float "
        "literals in `scripts/mitigation_budget.py` with a `_PROVENANCE` sibling (D-17), and the "
        "SAME ladder is reused at both capacities so `capacity_comparison`'s exact-equality check "
        "on sigma is satisfied by construction rather than by coincidence. This module lands in "
        "wave 2 and reads the ladder at CALL time precisely so waves 2-4 can import it while the "
        "ladder is still absent. If you are seeing this from plan 25-12 or later, the ladder was "
        "removed or renamed, not merely unwritten",
    )
    grid = mitigation_budget.ADVERSARIAL_RATIO_GRID
    keys = tuple(point_key(arm, sigma) for arm in DP_ARMS for sigma in ladder) + tuple(
        point_key(arm, ratio) for arm in ADVERSARIAL_ARMS for ratio in grid
    )
    expected = len(DP_ARMS) * mitigation_budget.SWEEP_POINTS + len(ADVERSARIAL_ARMS) * len(grid)
    _prove(
        len(ladder) == mitigation_budget.SWEEP_POINTS,
        f"the sigma ladder carries {len(ladder)} values while "
        f"mitigation_budget.SWEEP_POINTS pins {mitigation_budget.SWEEP_POINTS} frontier points per "
        "leg. D-20 puts sigma=0 INSIDE that 16 (control at slot 1, 15 noised points), so a ladder "
        "of a different length is a curve of a different width than the one the cost record priced",
    )
    _prove(
        len(keys) == expected,
        f"the ordered key set has {len(keys)} members, not {expected}. D-08 pins all 44 points and "
        "does not re-open the count at the moment of spending",
    )
    _prove(
        len(set(keys)) == len(keys),
        "the ordered key set carries DUPLICATE keys. Two points sharing a key share a record "
        "path, so the second one's `refuse_existing_artifacts` would read as a one-attempt "
        "violation while the real defect is a collision in the six-decimal rendering",
    )
    return keys


# =================================================================================================
# ===== (c) D-34's LIVE HALT — FIVE FIELDS, EXACT EQUALITY, NO TOLERANCE ANYWHERE =====
# =================================================================================================


def SWEEP_SCHEDULE():
    """D-15's EXECUTION ORDER over the same 44 keys: controls, then the six other extremes
    INTERLEAVED across the four legs, then the 36 interior points in pinned order.

    A FUNCTION over `ORDERED_POINT_KEYS()` and never a second list: the plist deliberately spells
    no point list ("a list repeated in this file would be a second, un-asserted copy of the
    sweep's own definition, free to drift"), so the order lives here, derived from the same
    ladder and grid, and is proved to be a PERMUTATION of the pinned set on every call. The eight
    extremes are D-15's — the two sigma=0 controls (D-01), the two DP high extremes at
    ``SIGMA_LADDER[-1]`` (the probed anchor), and the four adversarial corners at ratio 0.0 and at
    the pool ceiling — and they run before any interior point so a structural problem at any
    corner appears on day one rather than on day five.
    """
    keys = ORDERED_POINT_KEYS()
    ladder = mitigation_budget.SIGMA_LADDER
    grid = mitigation_budget.ADVERSARIAL_RATIO_GRID
    head = (
        point_key("dp_n8", ladder[0]),
        point_key("dp_n64", ladder[0]),
        point_key("dp_n8", ladder[-1]),
        point_key("adv_n8", grid[0]),
        point_key("dp_n64", ladder[-1]),
        point_key("adv_n64", grid[0]),
        point_key("adv_n8", grid[-1]),
        point_key("adv_n64", grid[-1]),
    )
    schedule = head + tuple(key for key in keys if key not in head)
    _prove(
        len(schedule) == len(keys) and set(schedule) == set(keys),
        f"the schedule is not a permutation of the pinned key set ({len(schedule)} vs {len(keys)})",
    )
    return schedule


MECHANISM_PIN_FIELDS = ("composed_steps", "composed_lot_sizes", "records_per_lot", "q", "clip_norm")

MECHANISM_PIN_SOURCES = {
    "composed_steps": "mitigation_budget.STEP_BUDGET (T = 200, measured at both capacities, D-27)",
    "composed_lot_sizes": "the point's own capacity: [8] at n=8 and [64] at n=64 (D-27)",
    "records_per_lot": "the point's own capacity: 8 at n=8 and 64 at n=64 (D-27)",
    "q": "mitigation_unit.SAMPLING_RATE_Q — THE ONE FIELD THE PHASE 23 SCHEMA LACKS (D-26)",
    "clip_norm": "the single `C` literal in mitigation_budget, pinned by D-24 and proved "
    "non-binding at the control (D-01: `clip_bind_count == 0` before scoring)",
}

MECHANISM_HALT_GOVERNS = (
    "GOVERNS THE WHOLE SWEEP, NOT ONE POINT. D-34 gives a live mechanism mismatch the same "
    "structural weight D-07 gives the control's reproduction miss: it HALTS, it is not logged. A "
    "point whose live mechanism diverged from the pin carries a privacy reading that DOES NOT "
    "DESCRIBE WHAT HAPPENED, and 44 of those assembled into a published frontier is the single "
    "most dangerous error class v4.0's research named. THE CHECK IS EXACT `==` ON ALL FIVE "
    "FIELDS, INCLUDING THE FLOAT ONE: the pin and the live read both come from the same "
    "`mitigation_budget` literal, so equality is exact BY CONSTRUCTION, and a tolerance would buy "
    "nothing except the ability to hide a real divergence. Phase 20 already measured what a "
    "tolerance costs on this kind of comparison: a one-ULP nudge slipped a float check and bought "
    "a bit-identical borrowed retention cap."
)


def prove_mechanism_matches_pin(live, pinned, *, point_key):
    """D-34. Exact ``==`` on all five of :data:`MECHANISM_PIN_FIELDS`, or the sweep HALTS.

    ``live`` is read at WRITE time from the running mechanism; ``pinned`` is the committed pin.
    Returns ``True`` on a full match; raises ``SystemExit`` otherwise.

    NO TOLERANCE ANYWHERE, and that includes `clip_norm`, which is a float. Both sides come from
    the same committed literal, so equality holds by construction; a tolerance would only widen
    the set of divergences that pass. An absent field is treated as a divergence rather than as a
    match, because a mechanism that stopped reporting a pinned quantity is exactly as unreadable
    as one that reports a different value for it.
    """
    for field in MECHANISM_PIN_FIELDS:
        for side, mapping in (("live", live), ("pinned", pinned)):
            if field not in mapping:
                raise SystemExit(
                    f"[phase25_record] THE WHOLE SWEEP HALTS. Point {point_key!r}: the {side} "
                    f"mechanism does not carry the pinned field {field!r} at all "
                    f"(present: {sorted(mapping)}). Its source is "
                    f"{MECHANISM_PIN_SOURCES[field]}. {MECHANISM_HALT_GOVERNS}"
                )
        if live[field] != pinned[field]:
            raise SystemExit(
                f"[phase25_record] THE WHOLE SWEEP HALTS. Point {point_key!r}: the live mechanism "
                f"field {field!r} reads {live[field]!r} while the pin is {pinned[field]!r}. Its "
                f"source is {MECHANISM_PIN_SOURCES[field]}. {MECHANISM_HALT_GOVERNS}"
            )
    return True


# =================================================================================================
# ===== (d) D-21's INLINE k — NEVER A SEPARATELY-CONSULTABLE METADATA BLOCK =====
# =================================================================================================

K_SOURCES = {
    "mitigation_budget.CURVE_K": mitigation_budget.CURVE_K,
    "mitigation_budget.FULL_FIDELITY_K": mitigation_budget.FULL_FIDELITY_K,
}

DRAWS_PER_QUESTION_GOVERNS = (
    "GOVERNS EVERY READING THAT CARRIES A PRIVACY NUMBER. D-21: `draws_per_question` and "
    "`draws_per_question_source` travel INLINE, in the SAME dict as the reading, and never as a "
    "separately-consultable metadata block. A K=16 curve reading and a K=48 promoted reading of "
    "THE SAME POINT are NUMERICALLY IDENTICAL in their privacy number and differ only in "
    "statistical precision, so nothing in the value distinguishes them: the only thing that can "
    "is the k sitting beside it. Precedent: `results/phase23_never_taught.json` already records "
    "`draws_per_question: 16` with `draws_per_question_source: 'mitigation_budget.CURVE_K'` on "
    "every per-seed block."
)


def epsilon_bearing_reading(*, value, draws_per_question, draws_per_question_source, **extra):
    """One privacy reading with its own ``k`` and ``k_source`` INLINE (D-21).

    ``value`` is the reading itself — a float, or ``None`` at the sigma=0 control. The source
    string is resolved against :data:`K_SOURCES` and the k is asserted equal to the constant it
    names, so a reading cannot claim `CURVE_K` while carrying 48.
    """
    _prove(
        draws_per_question_source in K_SOURCES,
        f"draws_per_question_source {draws_per_question_source!r} names none of "
        f"{sorted(K_SOURCES)}. D-21 requires the SOURCE, not just the number: two readings of one "
        "point at different k are indistinguishable by value, so an unattributed k is a k that "
        "cannot be checked against the constant it came from",
    )
    _prove(
        draws_per_question == K_SOURCES[draws_per_question_source],
        f"the reading carries draws_per_question={draws_per_question!r} while "
        f"{draws_per_question_source} is {K_SOURCES[draws_per_question_source]!r}. A k that "
        "disagrees with the constant it names is the exact confusion D-21 exists to make "
        "impossible, wearing the attribution that was supposed to prevent it",
    )
    reading = {
        "epsilon": value,
        "draws_per_question": draws_per_question,
        "draws_per_question_source": draws_per_question_source,
    }
    reading.update(extra)
    return reading


# =================================================================================================
# ===== (e) THE TWO TIERS, THE FOUR FAMILIES, AND THE REFUSAL COLUMN (D-05, D-36, D-39) =====
# =================================================================================================

# Read from `scripts/phase18_extraction.py` WITHOUT importing it — that import puts torch in
# `sys.modules` (measured). `phase25_gate05._committed_literal` is the reader this phase already
# uses on this same frozen file, and `tests/test_phase25_record.py` imports the real module and
# asserts the two agree, which is where the two-second torch import belongs.
GATED_TIER = phase25_gate05._committed_literal("phase18_extraction", "GATED_TIER")
REPORTED_TIER = phase25_gate05._committed_literal("phase18_extraction", "REPORTED_TIER")
ATTACK_FAMILIES = tuple(phase25_gate05._committed_literal("phase18_extraction", "ATTACK_FAMILIES"))
FAMILY_ZERO = phase25_gate05._committed_literal("phase18_extraction", "FAMILY_ZERO")

# D-24 in the Phase-24 register: the held-out family is A2 and the three trained ones are the rest.
HELD_OUT_FAMILY = phase25_gate05._committed_literal("phase24_adversarial", "HELD_OUT_FAMILY")
TRAINED_FAMILIES = tuple(
    phase25_gate05._committed_literal("phase24_adversarial", "TRAINED_FAMILIES")
)

_prove(
    HELD_OUT_FAMILY in ATTACK_FAMILIES
    and set(TRAINED_FAMILIES) | {HELD_OUT_FAMILY} == set(ATTACK_FAMILIES),
    f"the trained families {TRAINED_FAMILIES} plus the held-out {HELD_OUT_FAMILY!r} do not "
    f"reconstruct the four scored families {ATTACK_FAMILIES}. D-36 requires per-family counts "
    "INCLUDING A2 so the aggregate can re-derive exactly from them; a family that is scored but "
    "belongs to neither list would be counted in the point and lost in the aggregate",
)
_prove(
    FAMILY_ZERO not in ATTACK_FAMILIES,
    f"the never-run family {FAMILY_ZERO!r} appears among the scored families {ATTACK_FAMILIES}. "
    "D-05 gates on 416 = 104 x 4 questions with `family_zero_run: False`; a fifth family in the "
    "gated tier would change the denominator the extraction ceiling is read against",
)

TIER_GOVERNS = (
    "BOTH TIERS ARE DISPATCHED; ONLY ONE GATES (D-05). The gated tier is "
    f"{GATED_TIER!r} — 416 questions, 104 x 4 families, `family_zero_run: False` excluding "
    f"{FAMILY_ZERO!r} — and it is the ONLY tier that feeds the three-condition gate. "
    f"{REPORTED_TIER!r} carries 448 questions and is dispatched and published as REPORTED "
    "INFORMATION, exactly as `results/phase23_never_taught.json` already does. The tier names are "
    "read from `scripts/phase18_extraction.py` and never retyped."
)

REFUSAL_GOVERNS = (
    "REPORTED INFORMATION, NEVER A VERDICT CONDITION. D-39 wires 24-04's orphaned refusal "
    "instrumentation into every adversarial point so the artifact can say something about WHY a "
    "point cleared on extraction rather than only THAT it did — a point clearing on extraction "
    "with no refusal column gives no evidence about its own mechanism. IT SITS OUTSIDE THE "
    "THREE-CONDITION GATE, and that is structural rather than declared: none of these field names "
    "is a keyword argument of `mitigation_gate.mitigation_point_verdict`, which is asserted by an "
    "AST walk over the frozen gate rather than by grep. Keeping it outside preserves the closed "
    "domain GATE-07 and D-29 protect. IT IS COUNTS, NEVER RATES: `phase14_recall.score_refusal` "
    "returns `(k, n)` and both travel, so any bound taken downstream is re-derivable from the "
    "record rather than from an already-rounded float."
)

# The gate's twenty-one keyword-only parameters, resolved through `inspect.signature` and NEVER by
# grepping the frozen file: that file discusses every one of these names in its own prose, so a
# textual check over it measures the documentation rather than the signature (the false-RED class
# RPT-02 exists to close). Reading the signature is also NOT a call — the caller census in
# `tests/test_phase20_correction.py` matches `ast.Call` nodes whose func names the verdict, and
# `scripts/phase25_condition_c.py` already reads the same signature the same way.
VERDICT_KWARGS = tuple(
    name
    for name, parameter in inspect.signature(
        mitigation_gate.mitigation_point_verdict
    ).parameters.items()
    if parameter.kind is inspect.Parameter.KEYWORD_ONLY
)


def prove_names_are_outside_the_gate(names, *, what):
    """Refuse any field name that IS a keyword argument of the frozen verdict.

    The structural half of D-39 and of `phase25_gate05.GATE05_GOVERNS`. A reported column becoming
    a verdict input is not a naming accident: `mitigation_point_verdict` takes its inputs by
    KEYWORD, so a reported dict splatted into it would silently supply a verdict condition that
    was pre-registered as reported information.
    """
    collisions = sorted(set(names) & set(VERDICT_KWARGS))
    _prove(
        not collisions,
        f"{what} carries field name(s) {collisions} that ARE keyword arguments of "
        "mitigation_gate.mitigation_point_verdict. These fields are pre-registered as REPORTED "
        "INFORMATION and must stay outside the three-condition gate; a name collision is one "
        "`**` away from becoming a verdict condition",
    )
    return True


def refusal_column(completions_by_family, templates):
    """D-39's refusal column: ``(k, n)`` per family plus a total, IN COUNTS.

    ``completions_by_family`` maps an attack family to that family's completions;
    ``templates`` is the caller-supplied iterable of already-rendered refusal STRINGS —
    `phase14_recall.contains_refusal` imports no template table on purpose, so the instrument and
    the table stay separately owned.

    `phase14_recall` is imported LAZILY: it puts torch in `sys.modules` (measured), and this
    module's whole discipline is that a record can be rebuilt on CPU from a clone.
    """
    import phase14_recall

    by_family = {}
    for family in sorted(completions_by_family):
        successes, questions = phase14_recall.score_refusal(
            completions_by_family[family], templates
        )
        _prove(
            type(successes) is int and type(questions) is int,
            f"score_refusal returned ({successes!r}, {questions!r}) for family {family!r}, which "
            "is not a pair of plain ints. D-39's column is COUNTS: a float here is a rate that "
            "has already been divided, and the denominator it was divided by is then gone",
        )
        by_family[family] = {"refusal_k": successes, "refusal_n": questions}

    column = {
        "governs": REFUSAL_GOVERNS,
        "by_family": by_family,
        "total": {
            "refusal_k": sum(row["refusal_k"] for row in by_family.values()),
            "refusal_n": sum(row["refusal_n"] for row in by_family.values()),
        },
        # D-11's two CLEAN-frame probe populations, pinned before any sweep point exists. They are
        # the denominator PROVENANCE for this column: `clean_frame_probe_populations` returns
        # populations and never measurements, so nothing here is scored.
        "denominator_provenance": phase14_recall.clean_frame_probe_populations(),
    }
    names = {"refusal", "governs", "by_family", "total", "denominator_provenance"}
    names |= {"refusal_k", "refusal_n"} | set(by_family)
    prove_names_are_outside_the_gate(names, what="the D-39 refusal column")
    return column


def per_family_counts(counts_by_family):
    """D-36's per-family counts, all four families INCLUDING the held-out A2, all values ``int``.

    The aggregate `held_out_generalization` section plan 25-19 assembles is computed FROM these
    fields with a write-time assertion that it re-derives exactly, so a family missing here is a
    family the aggregate cannot see.
    """
    missing = sorted(set(ATTACK_FAMILIES) - set(counts_by_family))
    _prove(
        not missing,
        f"per-family counts are missing {missing}. D-36 requires ALL FOUR of {ATTACK_FAMILIES} "
        f"including the held-out {HELD_OUT_FAMILY!r} — it is already one of the four scored "
        "shapes across all 416 gated questions, so carrying it is free, and the aggregate "
        "re-derives from these counts rather than from a second measurement",
    )
    extra = sorted(set(counts_by_family) - set(ATTACK_FAMILIES))
    _prove(
        not extra,
        f"per-family counts carry unscored famil(ies) {extra}. The gated denominator is "
        f"416 = 104 x 4 with {FAMILY_ZERO!r} not run; a fifth family would move it",
    )
    rows = {}
    for family in ATTACK_FAMILIES:
        row = dict(counts_by_family[family])
        for name, value in sorted(row.items()):
            _prove(
                type(value) is int,
                f"per-family field {name!r} of {family!r} is {value!r} ({type(value)!r}), not an "
                "int. D-36's aggregate re-derives by SUMMING these; a float that has already been "
                "divided cannot be summed back into a count",
            )
        rows[family] = row
    return rows


# =================================================================================================
# ===== (f) D-37's TWO RESERVATIONS THAT ARE FREE NOW AND EXPENSIVE LATER =====
# =================================================================================================


def _filler_facts():
    """The 56 unscored filler facts. Lazy: `phase21_filler` imports numpy at module scope."""
    import phase21_filler

    return phase21_filler.FILLER_FACTS


def canary_population(n_facts):
    """D-37(ii): this point's in/out canary split, with the asymmetry stated in the record.

    At n=8 the 56 filler facts are OUT of the corpus; at n=64 all 64 (8 scored + 56 filler) are IN.
    So ONLY n=8 POINTS HAVE OUT-OF-CORPUS CANARIES AT ALL — a structural constraint on what Phase
    26 can measure, written down before the sweep rather than discovered after it.
    """
    n_filler = len(_filler_facts())
    n_locked = len(phase25_gate05.GATE05_SLOTS)
    _prove(
        n_locked + n_filler == 64,
        f"{n_locked} locked facts plus {n_filler} filler facts is not the 64 the n=64 capacity "
        "arm is built from. D-12's construction is `8 scored LOCKED_FACTS + 56 unscored filler`, "
        "never 64 fresh facts, and the in/out split this function records is that arithmetic",
    )
    if n_facts == n_locked:
        in_corpus, out_of_corpus = n_locked, n_filler
    elif n_facts == n_locked + n_filler:
        in_corpus, out_of_corpus = n_facts, 0
    else:
        raise SystemExit(
            f"[phase25_record] n_facts={n_facts!r} is neither {n_locked} nor "
            f"{n_locked + n_filler}. "
            "The sweep runs at exactly two capacities and the canary population is defined only at "
            "those two; a third would need its own in/out rule, decided before the sweep rather "
            "than inferred from a record"
        )
    return {
        "n_facts": n_facts,
        "in_corpus": in_corpus,
        "out_of_corpus": out_of_corpus,
        "has_out_of_corpus_canaries": out_of_corpus > 0,
        "locked_facts": n_locked,
        "filler_facts": n_filler,
        "structural_note": phase25_prereg.CANARY_RESERVATIONS["canary_population_rule"],
    }


def _module_sha256(name):
    """The sha256 of one `scripts/` module's BYTES, computed at write time."""
    return hashlib.sha256((_ROOT / "scripts" / name).read_bytes()).hexdigest()


# =================================================================================================
# ===== (g) THE CONTROL'S EXPLICIT null AND THE ADVERSARIAL ARM'S ABSENT CLAIM =====
# =================================================================================================

ADVERSARIAL_MAKES_NO_FORMAL_CLAIM = (
    "THE ADVERSARIAL ARM MAKES NO FORMAL CLAIM, AND `accounting: null` IS THAT STATEMENT WRITTEN "
    "DOWN RATHER THAN LEFT TO BE INFERRED FROM AN ABSENCE (D-31). The arm has no sigma, no delta "
    "and no q, which is the same fact `capacity_comparison` states from the other side: it "
    "`_prove`s all four MECHANISM_KEYS present and exactly equal, takes no `arm` argument, and is "
    "therefore a DP-ONLY instrument (D-23). The two adversarial capacities are reported side by "
    "side DESCRIPTIVELY, and the absence of a committed capacity rule for this arm is named here "
    "rather than left for a reader to trip over. The key is written with an explicit null for the "
    "same reason the control's privacy field is: a missing key is indistinguishable from a writer "
    "that crashed before emitting it."
)


# =================================================================================================
# ===== (h) THE RECORD ITSELF =====
# =================================================================================================

RECORD_GOVERNS = (
    "ONE SWEEP POINT, AND THREE THINGS AT ONCE: D-10's one-attempt evidence, D-09's resume "
    "boundary and D-31's assembly input. It renders no verdict. The verdict is computed by plan "
    "25-19's assembly from these fields, through the frozen gate, by IMPORTING its constants "
    "rather than retyping any threshold."
)


def condition_c_group(*, capability, control_gap, seed_spread):
    """D-45's condition-(c) field group. Every NAME comes from `phase25_condition_c`, never here.

    ``capability`` is the mapping `phase25_condition_c.measure_condition_c` returns.
    ``control_gap`` is THIS CAPACITY'S OWN sigma=0 control gap (D-47) — a borrowed one silently
    moves both edges of the admissible band at the capacity that did not produce it.
    ``seed_spread`` is the sweep's own seed-to-seed retention spread, D-50's zero-compute input.

    NO PHASE 23 POINT RECORD CARRIES ANY OF THESE, which is why they are ADDED here rather than
    copied from the Phase 23 schema: the six verdict kwargs had zero producers across the whole
    20-plan set and the verdict was uncomputable, not merely unwritten (D-51).
    """
    fields = {
        "point_dialogue_ppl_on": capability["adapter_on"],
        "point_dialogue_ppl_off": capability["adapter_off"],
        "control_gap": control_gap,
        "gap_noise_floor": phase25_condition_c.gap_noise_floor()[0],
        "point_retention_ppl": capability["retention_ppl"],
        # The GOVERNING adapter-regime floor, which proves itself admissible before returning.
        # D-48's borrowed 0.06893 is REFUSED by `phase20_gate_coverage._prove_retention_floor`
        # (measured: SystemExit) and travels beside the record as a disclosure, never as an input.
        "retention_noise_floor": phase25_condition_c.retention_floor_for_verdict(),
        # The two denominators. A rate without its denominator is not a reading.
        "dialogue_n_targets": capability["n_targets"],
        "retention_total_tokens": capability["retention_total_tokens"],
    }
    fields.update(
        phase25_condition_c.counterfactual_fields(capability["retention_ppl"], seed_spread)
    )
    for name in ("dialogue_n_targets", "retention_total_tokens"):
        _prove(
            type(fields[name]) is int,
            f"condition-(c) denominator {name!r} is {fields[name]!r} ({type(fields[name])!r}), "
            "not an int. Both perplexities are means over a token population and the population "
            "size is what makes them comparable across points",
        )
    expected = set(phase25_condition_c.CONDITION_C_FIELDS)
    _prove(
        set(fields) == expected,
        f"the condition-(c) group's key set {sorted(set(fields) ^ expected)} differs from "
        "`phase25_condition_c.CONDITION_C_FIELDS`. The contract is that tuple and this record "
        "consumes it: a field dropped here is a kwarg the verdict cannot be computed without, and "
        "that is the exact state all 44 Phase 23 records are in",
    )
    return fields


def retention_disclosure(point_retention_ppl):
    """D-48/D-49: BOTH floors and BOTH caps, with THIS point's headroom against each.

    The governing floor is `0.008681618994239138` and the borrowed one `0.06893`. The borrowed
    value is REFUSED by `phase20_gate_coverage._prove_retention_floor` — by name and by regime, a
    Phase 12 FULL-FINE-TUNE seed pair, wrong regime for an adapter verdict — so "imported as-is"
    was never executable for the retention leg. The governing floor yields the TIGHTER cap, so
    honouring the refusal does not buy an easier pass, and both readings are published rather than
    one being quietly replaced.

    `RETENTION_LEG_BINDS_AT_ANCHOR` travels BY REFERENCE so every point record states the
    pre-registration it is read against.
    """
    anchor = phase25_condition_c.RETENTION_LEG_BINDS_AT_ANCHOR
    borrowed, governing = anchor["borrowed"], anchor["governing"]
    _prove(
        governing["cap"] < borrowed["cap"],
        f"the governing cap {governing['cap']!r} is not TIGHTER than the borrowed "
        f"{borrowed['cap']!r}. The whole disclosure rests on the correction NARROWING the "
        "admissible window rather than widening it",
    )
    return {
        "retention_floor_governing": governing["floor"],
        "retention_cap_governing": governing["cap"],
        "retention_headroom_governing": governing["cap"] - point_retention_ppl,
        "retention_floor_borrowed": borrowed["floor"],
        "retention_cap_borrowed": borrowed["cap"],
        "retention_headroom_borrowed": borrowed["cap"] - point_retention_ppl,
        "verdict_reads": "retention_floor_governing",
        "retention_leg_binds_at_anchor": anchor,
        "retention_squeeze_is_the_frontier": (
            phase25_condition_c.RETENTION_SQUEEZE_IS_THE_FRONTIER
        ),
        "dialogue_floor_recipe_mismatch": phase25_condition_c.DIALOGUE_FLOOR_RECIPE_MISMATCH,
    }


def build_point_record(
    *,
    point_key_value,
    arm,
    axis_value,
    live_mechanism,
    pinned_mechanism,
    draws_per_question,
    draws_per_question_source,
    per_question,
    family_counts,
    refusal,
    adapter_path,
    adapter_sha256,
    n_facts,
    capability,
    control_gap,
    seed_spread,
    zero_extraction_has_nll,
    gate05_gated,
    gate05_reported,
    point_epsilon,
    accounting,
    extra=None,
):
    """One point's complete record. D-34's halt runs BEFORE the dict is returned.

    ``extra`` (2026-09-04) is the driver's per-point additions — the control's `taught_recall` and
    `reproduction_gate` plan 25-15 verifies, the adversarial build statistics plan 25-16 records,
    the training and timing provenance — merged LAST, refused on any key collision, and proved
    outside the verdict's kwargs like every other reported column.

    ``point_epsilon`` is the value for a noised DP point, or ``None`` at the sigma=0 control and on
    the adversarial arm. Both no-value cases write the key EXPLICITLY with a `null` and a sibling
    reason (§C5); the key is never omitted, because a missing key is indistinguishable from a
    writer that crashed before emitting it and D-31 proves ordered `point_keys` equality as a HARD
    equality at the frontier's single write.

    ``accounting`` is ``None`` on the adversarial arm (D-31), with
    :data:`ADVERSARIAL_MAKES_NO_FORMAL_CLAIM` as its recorded reason.
    """
    parsed_arm, axis, _ = parse_point_key(point_key_value)
    _prove(
        parsed_arm == arm,
        f"point key {point_key_value!r} parses to arm {parsed_arm!r} while the record declares "
        f"{arm!r}. The key is the record's own filename and D-31's ordered set is proved by hard "
        "equality; a key naming a different arm files the point where no consumer looks for it",
    )
    _prove(
        point_key(arm, axis_value) == point_key_value,
        f"point key {point_key_value!r} does not round-trip from arm {arm!r} at axis value "
        f"{axis_value!r}. The key is a LABEL and the record's own axis field is authoritative, so "
        "the two must be built from the same number or the label names a point that did not run",
    )

    # D-34, BEFORE ANY OTHER WORK. No record object exists in a diverged state.
    prove_mechanism_matches_pin(live_mechanism, pinned_mechanism, point_key=point_key_value)

    is_adversarial = arm in ADVERSARIAL_ARMS
    if point_epsilon is None:
        omitted_reason = (
            ADVERSARIAL_MAKES_NO_FORMAL_CLAIM
            if is_adversarial
            else phase25_epsilon.CONTROL_EPSILON_FIELD_FORM
        )
    else:
        omitted_reason = None
    _prove(
        not (is_adversarial and accounting is not None),
        "the adversarial arm was handed a non-null `accounting`. It has no sigma, no delta and no "
        f"q: {ADVERSARIAL_MAKES_NO_FORMAL_CLAIM}",
    )

    # D-46: run the flag through the frozen refusal BEFORE serialising. A `(False, reason)` PAIR IS
    # TRUTHY, and `not (False, '...')` is False — passing the pair through would silently disarm
    # the gate's INCONCLUSIVE branch on exactly the run that needed it.
    flag = phase25_gate05.prove_flag_is_a_bool(zero_extraction_has_nll, point_key=point_key_value)

    prove_names_are_outside_the_gate(
        set(gate05_reported), what="the REPORTED gate05 tier (`gate05_reported`)"
    )

    rows = dict(per_question)
    _prove(
        set(rows) == {GATED_TIER, REPORTED_TIER},
        f"per-question rows cover {sorted(rows)} rather than both of "
        f"{sorted((GATED_TIER, REPORTED_TIER))}. {TIER_GOVERNS}",
    )

    condition_c = condition_c_group(
        capability=capability, control_gap=control_gap, seed_spread=seed_spread
    )

    record = epsilon_bearing_reading(
        value=point_epsilon,
        draws_per_question=draws_per_question,
        draws_per_question_source=draws_per_question_source,
        point_key=point_key_value,
        arm=arm,
        axis=axis,
        sweep_point=True,
        governs=RECORD_GOVERNS,
        record=str(point_record_path(point_key_value).relative_to(_ROOT)),
        # --- the five pinned mechanism fields, LIVE (D-34) ---
        composed_steps=live_mechanism["composed_steps"],
        composed_lot_sizes=live_mechanism["composed_lot_sizes"],
        records_per_lot=live_mechanism["records_per_lot"],
        q=live_mechanism["q"],
        clip_norm=live_mechanism["clip_norm"],
        mechanism_pin_fields=list(MECHANISM_PIN_FIELDS),
        mechanism_pin_sources=MECHANISM_PIN_SOURCES,
        mechanism_halt_governs=MECHANISM_HALT_GOVERNS,
        # --- the axis and the formal claim ---
        delta=mitigation_unit.DELTA,
        epsilon_omitted_reason=omitted_reason,
        epsilon_rule="personacore.privacy.accountant.epsilon_for(sigma, steps, delta)",
        accounting=accounting,
        selection_accounted=phase25_epsilon.SELECTION_ACCOUNTED,
        multiplicity=phase25_epsilon.dual_granularity_sentence(point_epsilon),
        draws_per_question_governs=DRAWS_PER_QUESTION_GOVERNS,
        # --- D-05's two tiers, D-36's per-family counts, D-39's refusal column ---
        gated_tier=GATED_TIER,
        reported_tier=REPORTED_TIER,
        tier_governs=TIER_GOVERNS,
        family_zero_run=False,
        per_question=rows,
        per_family_counts=per_family_counts(family_counts),
        refusal=refusal,
        # --- D-37's two reservations ---
        adapter_path=adapter_path,
        adapter_sha256=adapter_sha256,
        canary_population=canary_population(n_facts),
        # --- D-45/D-46/D-48/D-49/D-50 ---
        condition_c=condition_c,
        zero_extraction_has_nll=flag,
        gate05_gated_slots=list(phase25_gate05.GATE05_SLOTS),
        gate05_gated=gate05_gated,
        gate05_reported=gate05_reported,
        gate05_governs=phase25_gate05.GATE05_GOVERNS,
        # --- provenance ---
        gate_module_sha256=_module_sha256("mitigation_gate.py"),
        budget_module_sha256=_module_sha256("mitigation_budget.py"),
        git_sha=git_sha(),
        python_version=platform.python_version(),
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )
    record[axis] = float(axis_value)
    record.update(retention_disclosure(condition_c["point_retention_ppl"]))
    if extra:
        collisions = sorted(set(extra) & set(record))
        _prove(
            not collisions,
            f"extra field(s) {collisions} collide with the record's own; an extra never overwrites",
        )
        prove_names_are_outside_the_gate(set(extra), what="the driver's extra point fields")
        record.update(extra)
    return record


def write_point_record(record, *, point_key_value, tracked):
    """Serialise ONE point's record, atomically. Both per-point refusals run before the bytes.

    ``tracked`` is the caller's ``git ls-files results/phase25_point_*.json`` result and is
    REQUIRED rather than defaulted: `phase25_prereg.prove_first_attempt` is D-10's rule and an
    optional argument is a rule a driver can forget. That module deliberately runs no subprocess,
    so the list stays the caller's to produce and the write path is unit-testable without a
    repository.

    THE PER-POINT REFUSAL IS `phase21_unit_record.refuse_existing_artifacts` PLUS
    `phase25_prereg.prove_first_attempt`, AND IT IS DELIBERATELY NOT `refuse_if_dirty`.
    Per-point records land during an UNATTENDED multi-day run when the tree is legitimately
    mid-flight — a checkpoint written, an adapter exported, a sibling point's record staged — and a
    dirty-tree refusal there would abort the sweep for the tree's state rather than for the
    record's. The dirty check belongs to the WRITE-ONCE assembly of
    `results/phase25_frontier.json`, which is a single permanent publication whose recorded SHA has
    to reproduce it; :data:`_PUBLICATION_PATHSPEC` is defined here for that write.

    THE WRITE IS ATOMIC: serialise fully, write to a temporary file in the DESTINATION DIRECTORY,
    `fsync`, then `os.replace`. `os.replace` is atomic within one filesystem, and the temp file is
    created beside the destination so it never crosses one. Serialising BEFORE opening the temp
    file is the load-bearing half: a record carrying a non-serialisable value then leaves NO file
    at all rather than a truncated one, and a truncated per-point record is indistinguishable from
    a point that ran and produced a short reading.
    """
    import phase21_unit_record

    path = point_record_path(point_key_value)
    phase25_prereg.prove_first_attempt(tracked, point_key=point_key_value)
    phase21_unit_record.refuse_existing_artifacts(paths=[path])

    payload = json.dumps(record, indent=2, sort_keys=True) + "\n"

    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    try:
        with handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(handle.name, path)
    except BaseException:
        pathlib.Path(handle.name).unlink(missing_ok=True)
        raise
    return path


# =================================================================================================
# ===== (i) THE WRITE-ONCE ASSEMBLY — D-31, D-36, D-28/D-29/D-30, D-49/D-50 (plan 25-19) =====
# =================================================================================================
#
# `results/phase25_frontier.json` is assembled ONCE, at the end, from the 44 committed point
# records plus the two CPU artifacts produced after the sweep — `results/phase25_recall.json`
# (D-25-18-RECALL: condition (b) had no per-point producer, so 42 of the 44 records carry no
# recall and it is fed from that artifact, pinned to each record's `adapter_sha256`) and
# `results/phase25_promotion.json` (the 44 verdicts through the sanctioned route, six of them
# REFUSED on the `adv_n64` leg, D-25-18-ADV64-REFUSED). Nothing is re-decided here: every verdict,
# reason string, existential and branch name is carried verbatim, and every aggregate this module
# adds — `held_out_generalization`, the curve-total epsilon, the verdict tallies — is asserted to
# re-derive EXACTLY from the rows beside it before a byte is written.
#
# THE ORDER OF THE WRITE IS `phase24_record._write`'s, copied not improvised:
# `refuse_existing_artifacts` (inherited from `phase21_unit_record` -> `teach_persona`), then
# `refuse_if_dirty(pathspec=_PUBLICATION_PATHSPEC)`, then the bytes. So the assembly REQUIRES A
# CLEAN TREE across scripts/, src/, results/ and artifacts/ (untracked counts as dirty), which holds
# only because the driver committed each of the 44 records as it landed (SS-O1).
#
# THE SANCTIONED RE-RUN ROUTE is `phase24_record.py`'s: delete the artifact IN ITS OWN COMMIT, then
# run this emitter again against a clean tree. Never overwrite in place, never write to a temporary
# path and copy the file into results/ — the recorded `git_sha` must name the tree that produced the
# bytes (21-REVIEW CR-02 is what that shortcut reproduces).

PROMOTION_RECORD = _ROOT / "results" / "phase25_promotion.json"
RECALL_RECORD = _ROOT / "results" / "phase25_recall.json"
NEVER_TAUGHT_RECORD = _ROOT / "results" / "phase23_never_taught.json"

RERUN_ROUTE = (
    "THE SANCTIONED RE-RUN ROUTE: DELETE results/phase25_frontier.json IN ITS OWN COMMIT, then run "
    "`.venv/bin/python scripts/phase25_record.py` again against a clean tree — exactly as "
    "scripts/phase24_record.py documents for its record. Never overwrite in place and never write "
    "to a temporary path and copy the file into results/: the recorded git_sha must name the tree "
    "that produced the bytes."
)

_DIRTY_DETAIL = (
    "`provenance.git_sha` records HEAD at write time, so a frontier written from a dirty tree "
    "names a commit that does NOT contain the code or the inputs that produced it — the artifact "
    "points at a tree it cannot be regenerated from (21-REVIEW.md CR-02 found both phase-21 "
    "artifacts carrying exactly that defect). This emitter also carries the gate, budget and its "
    "own module digests in provenance, so a dirty tree publishes digests of bytes the recorded "
    "commit does not contain. "
    "Commit the tree, then re-run. " + RERUN_ROUTE
)

# The six recall fields the two sigma=0 controls carry inline and the other 42 records do not.
RECALL_FIELDS = (
    "taught_recall",
    "heldout_recall",
    "taught_recall_off",
    "heldout_recall_off",
    "per_family_gain",
    "scoring_seconds",
)

RECALL_SOURCE_GOVERNS = (
    "D-25-18-RECALL: the sweep driver scored recall only under `is_control`, so 42 of the 44 point "
    "records carry no `taught_recall` / `heldout_recall`; only the two sigma=0 controls carry them "
    "inline. Condition (b)'s inputs are therefore fed from results/phase25_recall.json, keyed by "
    "point and pinned to each record's `adapter_sha256` (asserted equal at the single write), with "
    "the two controls' inline readings asserted equal to that artifact's copies. Each point's "
    "`recall_provenance` names which of the two sources it came from. The point records themselves "
    "are byte-unchanged."
)

ADVERSARIAL_NO_REPLAY_DISCLOSURE = (
    "RECIPE DISCLOSURE (results/phase25_operational_note.md section 12.5c): the adversarial arm "
    "trains with NO replay while the DP arms get replay windows at train time, so condition (c) "
    "fails on every adversarial point — ratio 0 included — for the RECIPE, not the ratio. The full "
    "block with its log lines is `verdicts.adversarial_no_replay`; nothing was adjusted."
)

MECHANISM_PIN_DISCLOSURE_GOVERNS_AS_PUBLISHED = (
    "D-25-17-ADV-PIN: on the adversarial arm two of the five D-34 mechanism pin fields — "
    "`composed_lot_sizes` and `records_per_lot` — are pinned := live. `phase25_points."
    "pinned_mechanism` leaves them None for `adv_*` ('resolved against the live TrainConfig at "
    "train time') and `train_point` fills the pin from the same lot it just read, so the exact-== "
    "on those two fields compares a value with itself on that arm. The other three "
    "(`composed_steps` = STEP_BUDGET, `q` None, `clip_norm` None) are real pins there. So the lot "
    "is RE-DERIVED here for all 44 points from the record's own `training.train_config` "
    "(`batch_size x max(1, grad_accum_steps)`) and asserted equal to `records_per_lot` at the "
    "single write, which checks the committed bytes against the config they carry. Recorded in "
    ".planning/phases/25-frontier-sweep-and-the-existence-gate-verdict/deferred-items.md."
)

# CORRECTION 2026-09-09 — 25-REVIEW WR-03, confirmed independently by 25-VERIFICATION.
# The sentence above is what `results/phase25_frontier.json` carries at `4030d0e`, and it gives the
# ADVERSARIAL formula for all 44 points: on `dp_n8_sigma0p000000` `batch_size x grad_accum_steps`
# reads 8 x 8 = 64 while `records_per_lot` is 8. The CODE was always per-arm
# (`_lot_from_train_config`) and `LOT_RULE_BY_ARM` beside the field states both rules correctly, so
# no verdict, count, epsilon or Success Criterion is affected. Operator decision (2026-09-09,
# 25-HUMAN-UAT item 2): record the discrepancy where a reader of the artifact meets it and correct
# the wording HERE for any future assembly, rather than re-emit 22.3 MB of write-once bytes. The
# published bytes stay pinned by `MECHANISM_PIN_DISCLOSURE_GOVERNS_AS_PUBLISHED` above.
MECHANISM_PIN_DISCLOSURE_GOVERNS = (
    "D-25-17-ADV-PIN: on the adversarial arm two of the five D-34 mechanism pin fields — "
    "`composed_lot_sizes` and `records_per_lot` — are pinned := live. `phase25_points."
    "pinned_mechanism` leaves them None for `adv_*` ('resolved against the live TrainConfig at "
    "train time') and `train_point` fills the pin from the same lot it just read, so the exact-== "
    "on those two fields compares a value with itself on that arm. The other three "
    "(`composed_steps` = STEP_BUDGET, `q` None, `clip_norm` None) are real pins there. So the lot "
    "is RE-DERIVED here for all 44 points from the record's own `training.train_config` BY THE "
    "ARM'S RULE — `canary_population.n_facts` on the DP arm, `batch_size x max(1, "
    "grad_accum_steps)` on the adversarial arm, both stated in full in `lot_rule_by_arm` beside "
    "this field — and asserted equal to `records_per_lot` at the single write, which checks the "
    "committed bytes against the config they carry. Recorded in "
    ".planning/phases/25-frontier-sweep-and-the-existence-gate-verdict/deferred-items.md."
)

HELD_OUT_GENERALIZATION_GOVERNS = (
    "D-36: the held-out attack family's extraction successes, aggregated over all 44 points and "
    "per arm, computed FROM the per-point `per_family_counts[held_out_family]` rows inline in this "
    "artifact and asserted at the single write to re-derive EXACTLY from them (successes, "
    "questions and draws all three) — so the aggregate can never drift from its own data. The "
    "family name is "
    "read from `phase24_adversarial.HELD_OUT_FAMILY` and never spelled; the adversarial arm trains "
    "on the other three families, so this is the family no adversarial adapter saw. Counts, never "
    "rates: a rate is taken by the reader from successes / questions."
)

EPSILON_REPORT_GOVERNS = (
    "FRONT-02, D-28/D-29/D-30. Every epsilon in this block is rendered through "
    "`phase25_epsilon.report_epsilon` (three required keyword arguments, no defaults) and never "
    "printed bare. `curve_total_epsilon` is BASIC composition — the plain sum of `summands`, the "
    "epsilons of the noised DP points ACTUALLY PUBLISHED, in `point_keys` order — at "
    "`total_delta = k x delta`, where k = len(summands). It crosses BOTH capacity legs. "
    "`selection_accounted` is False. The two sigma=0 controls carry no epsilon and are EXCLUDED "
    "deliberately (`control_points_excluded`); once they are published no joint bound over all "
    "published artifacts exists. Both multiplicities are named with the frozen pin's own status "
    "carried through verbatim."
)

VERDICTS_GOVERNS = (
    "FRONT-04 / D-23 / D-32: results/phase25_promotion.json carried verbatim — every top-level "
    "block except the two per-point maps, which travel INSIDE each point as `verdict` and "
    "`promotion`. Each point's `verdict` is the gate's own 3-tuple (verdict, reasons, arm) with "
    "its reason strings unmodified, plus the 21 pin kwargs it was judged on. `tallies` is computed "
    "here from the 44 entries and asserted at the single write; REFUSED means the sanctioned route "
    "`phase20_gate_coverage.corrected_point_verdict` refused the leg before the pin was reached "
    "(D-25-18-ADV64-REFUSED: the adv_n64 leg, whose own control scored held-out recall 0/648), and "
    "the refusal text is carried in that point's `verdict.reasons` — never a null that reads as "
    "missing. `capacity_branch` is asserted a member of `mitigation_gate.CAPACITY_BRANCHES`."
)


def _sha256_of(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _read_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def refuse_second_assembly(path=FRONTIER_RECORD):
    """Refuse-to-rerun for the frontier artifact — the inherited refusal, with the route appended.

    The trigger is `phase21_unit_record.refuse_existing_artifacts` (which is
    `teach_persona.refuse_if_exists`), imported lazily because that module puts torch in
    `sys.modules`. Its own message says "Delete
    ... to re-run"; this wrapper appends WHICH deletion is sanctioned — in its own commit, then
    re-run against a clean tree — so the refusal names the route rather than leaving a reader to
    guess at an overwrite. `main()` calls this before building, so a second run costs nothing.
    """
    import phase21_unit_record

    try:
        phase21_unit_record.refuse_existing_artifacts(paths=[pathlib.Path(path)])
    except SystemExit as refusal:
        raise SystemExit(
            f"[phase25_record] REFUSING a second assembly. {refusal}\n{RERUN_ROUTE}"
        ) from None


def load_point_records(directory=POINT_RECORD_DIR):
    """The committed point records, keyed by their OWN `point_key`, proved to equal the pin.

    D-31's hard equality — order AND membership — is proved here, at the single write: the records
    are found by the pre-registered glob, keyed by the `point_key` INSIDE each file (never the
    filename), refused on a duplicate or a file filed under a name its own key does not produce,
    and the resulting key set is asserted equal to `ORDERED_POINT_KEYS()` with the missing and the
    extra sets both in the message. A count check would pass on a duplicate plus a missing key.
    The returned mapping is in the PIN's order, which is the order the artifact's `points` and
    `point_keys` carry.
    """
    directory = pathlib.Path(directory)
    pattern = pathlib.PurePath(phase25_prereg.POINT_RECORD_GLOB).name
    loaded = {}
    for path in sorted(directory.glob(pattern)):
        record = _read_json(path)
        key = record.get("point_key")
        _prove(
            isinstance(key, str) and key,
            f"{path.name} carries no `point_key`; a record that does not name its own point cannot "
            "be placed in the ordered set",
        )
        if key in loaded:
            raise SystemExit(
                f"[phase25_record] point key {key!r} appears in two record files "
                f"({loaded[key]['record']!r} and {path.name!r}). A duplicate is exactly what a "
                "count check would miss"
            )
        _prove(
            path.resolve() == point_record_path(key).resolve(),
            f"{path.name} carries point_key {key!r}, whose record path is "
            f"{point_record_path(key).name!r} — the file is filed where no consumer looks for it",
        )
        loaded[key] = record
    pinned = ORDERED_POINT_KEYS()
    missing = sorted(set(pinned) - set(loaded))
    extra = sorted(set(loaded) - set(pinned))
    _prove(
        not missing and not extra,
        f"the assembled key set is not the pinned set: {len(loaded)} records found against "
        f"{len(pinned)} pinned keys; missing {missing}; extra {extra}. D-31 proves ORDERED "
        "`point_keys` equality as a HARD equality at this single write, and it does not hold",
    )
    points = {key: loaded[key] for key in pinned}
    _prove(
        tuple(points) == tuple(pinned),
        "the assembled order is not the pinned order (unreachable after the set equality above; "
        "kept as the literal statement of the hard equality)",
    )
    return points


LOT_RULE_BY_ARM = {
    "dp": (
        "records_per_lot == canary_population.n_facts == training.train_config.grad_accum_steps: "
        "fact-aligned accumulation runs one protected record per micro-step and n_facts "
        "micro-steps per optimizer step (D-27), so the lot IS the capacity and batch_size is "
        "windows per micro-step, not records"
    ),
    "adversarial": (
        "records_per_lot == training.train_config.batch_size x max(1, grad_accum_steps): no DP "
        "seam, no fact alignment, the lot is the windows one optimizer step consumes — which is "
        "the quantity the driver read live and then pinned (D-25-17-ADV-PIN)"
    ),
}


def _lot_from_train_config(record):
    """The lot re-derived from the record's own TrainConfig, by the arm's rule (LOT_RULE_BY_ARM)."""
    cfg = record["training"]["train_config"]
    if record["arm"] in ADVERSARIAL_ARMS:
        return int(cfg["batch_size"]) * max(1, int(cfg["grad_accum_steps"]))
    n_facts = record["canary_population"]["n_facts"]
    _prove(
        int(cfg["grad_accum_steps"]) == n_facts,
        f"{record['point_key']}: grad_accum_steps {cfg['grad_accum_steps']!r} != n_facts "
        f"{n_facts!r}; D-27's fact-aligned lot no longer describes this DP point",
    )
    return n_facts


def attach_recall(points, recall):
    """Feed condition (b)'s readings from `results/phase25_recall.json` (D-25-18-RECALL).

    The 42 records without recall take all six `RECALL_FIELDS` from the artifact, pinned to the
    record's `adapter_sha256`; the two controls' inline readings are asserted EQUAL to the
    artifact's copies. Every point gets a `recall_provenance` naming its source.
    """
    entries = recall["points"]
    _prove(
        set(entries) == set(points),
        f"results/phase25_recall.json covers {len(entries)} points, the records {len(points)}; "
        f"missing {sorted(set(points) - set(entries))}, extra {sorted(set(entries) - set(points))}",
    )
    for key, point in points.items():
        entry = entries[key]
        _prove(
            entry["adapter_sha256"] == point["adapter_sha256"],
            f"{key}: the recall artifact scored adapter {entry['adapter_sha256'][:12]} while the "
            f"record's adapter is {point['adapter_sha256'][:12]} — a reading of a different "
            "adapter",
        )
        inline = [name for name in RECALL_FIELDS if name in point]
        if inline:
            _prove(
                set(inline) == set(RECALL_FIELDS),
                f"{key}: carries only {inline} of the six recall fields inline",
            )
            for name in RECALL_FIELDS:
                _prove(
                    point[name] == entry[name],
                    f"{key}: inline {name!r} differs from results/phase25_recall.json's copy",
                )
            source = "point_record"
        else:
            for name in RECALL_FIELDS:
                point[name] = entry[name]
            source = "results/phase25_recall.json (D-25-18-RECALL)"
        _prove(
            entry["source"] == ("point_record" if source == "point_record" else entry["source"]),
            f"{key}: recall source disagreement",
        )
        for name in ("taught_recall", "heldout_recall"):
            block = point[name]
            _prove(
                type(block["numerator"]) is int and type(block["denominator"]) is int,
                f"{key}: {name} is not a numerator/denominator pair of ints",
            )
        point["recall_provenance"] = {
            "source": source,
            "sidecar": entry["source"],
            "instrument": entry["instrument"],
            "instrument_git_sha": entry["instrument_git_sha"],
            "device": entry["device"],
            "utc": entry["utc"],
            "adapter_sha256_pinned": True,
            "governs": RECALL_SOURCE_GOVERNS,
        }
    return points


def attach_verdicts(points, promotion):
    """Each point's verdict entry and promotion decision, verbatim from the promotion record."""
    verdicts, promotions = promotion["point_verdicts"], promotion["promotion"]
    _prove(
        set(verdicts) == set(points) == set(promotions),
        "results/phase25_promotion.json does not cover exactly the 44 points",
    )
    for key, point in points.items():
        entry = verdicts[key]
        _prove(entry["leg"] == point["arm"], f"{key}: verdict leg {entry['leg']!r} != arm")
        _prove("verdict" not in point and "promotion" not in point, f"{key}: key collision")
        point["verdict"] = entry
        point["promotion"] = promotions[key]
        if point["arm"] in ADVERSARIAL_ARMS:
            point["recipe_disclosure"] = ADVERSARIAL_NO_REPLAY_DISCLOSURE
    return points


def _verdict_label(entry):
    if entry["verdict"] is None:
        _prove(
            isinstance(entry["early_return_reason"], str)
            and entry["early_return_reason"].startswith("REFUSED"),
            "a null verdict without a REFUSED early_return_reason would read as missing",
        )
        return "REFUSED"
    return entry["verdict"]


def verdicts_block(points, promotion):
    """The promotion record's top level verbatim, plus tallies re-derived from the 44 entries."""
    branch = promotion["capacity_branch"]
    _prove(
        branch in mitigation_gate.CAPACITY_BRANCHES,
        f"capacity branch {branch!r} is not a member of mitigation_gate.CAPACITY_BRANCHES "
        f"{mitigation_gate.CAPACITY_BRANCHES}",
    )
    tallies = {"PASS": 0, "FAIL": 0, "INCONCLUSIVE": 0, "REFUSED": 0}
    by_leg = {arm: dict(tallies) for arm in ORDERED_ARMS}
    refused = {}
    for key, point in points.items():
        label = _verdict_label(point["verdict"])
        tallies[label] += 1
        by_leg[point["arm"]][label] += 1
        if label == "REFUSED":
            refused[key] = {
                "reason": point["verdict"]["reasons"],
                "early_return_reason": point["verdict"]["early_return_reason"],
                "route": "phase20_gate_coverage.corrected_point_verdict",
            }
    _prove(
        sorted(refused) == sorted(promotion["refused_points"]),
        f"refused {sorted(refused)} != promotion record's {sorted(promotion['refused_points'])}",
    )
    _prove(sum(tallies.values()) == len(points), "tallies do not sum to the point count")
    block = {
        "assembly_governs": VERDICTS_GOVERNS,
        "source": str(PROMOTION_RECORD.relative_to(_ROOT)),
        "source_sha256": _sha256_of(PROMOTION_RECORD),
        "tallies": tallies,
        "tallies_by_leg": by_leg,
        "refused": refused,
        "capacity_branches": list(mitigation_gate.CAPACITY_BRANCHES),
    }
    for name, value in promotion.items():
        if name in ("point_verdicts", "promotion"):
            continue
        _prove(name not in block, f"promotion field {name!r} collides with the verdicts block")
        block[name] = value
    return block


def held_out_generalization(points):
    """D-36: the held-out family's aggregate, FROM the per-point rows, all three counts."""
    family = HELD_OUT_FAMILY
    per_point = {}
    for key, point in points.items():
        row = point["per_family_counts"][family]
        per_point[key] = {name: row[name] for name in ("successes", "questions", "draws")}

    def _total(keys):
        return {
            name: sum(per_point[k][name] for k in keys)
            for name in ("successes", "questions", "draws")
        } | {"points": len(keys)}

    by_arm = {
        arm: _total([k for k, p in points.items() if p["arm"] == arm]) for arm in ORDERED_ARMS
    }
    return {
        "governs": HELD_OUT_GENERALIZATION_GOVERNS,
        "held_out_family": family,
        "held_out_family_source": (
            "phase24_adversarial.HELD_OUT_FAMILY, read through phase25_gate05._committed_literal"
        ),
        "trained_families": list(TRAINED_FAMILIES),
        "tier": GATED_TIER,
        **_total(list(points)),
        "by_arm": by_arm,
        "per_point": per_point,
        "re_derivation": (
            "successes / questions / draws == sum over point_keys of "
            "points[key].per_family_counts[held_out_family].<name>; likewise per arm and per "
            "point. "
            "Asserted at the single write by prove_held_out_generalization and again over the "
            "committed bytes by tests/test_phase25_frontier.py"
        ),
    }


def prove_held_out_generalization(artifact):
    """D-36's write-time re-derivation, callable over the committed bytes or a perturbed copy."""
    block = artifact["held_out_generalization"]
    family = block["held_out_family"]
    points = artifact["points"]
    for name in ("successes", "questions", "draws"):
        total = sum(p["per_family_counts"][family][name] for p in points.values())
        _prove(
            total == block[name],
            f"held_out_generalization.{name} = {block[name]} does NOT re-derive from the per-point "
            f"{family!r} rows beside it, which sum to {total} over {len(points)} points. D-36: an "
            "aggregate that no longer describes its own data is refused at the write and over the "
            "committed bytes; one perturbed per-point count is enough",
        )
        for arm, sub in block["by_arm"].items():
            arm_total = sum(
                p["per_family_counts"][family][name] for p in points.values() if p["arm"] == arm
            )
            _prove(
                arm_total == sub[name],
                f"held_out_generalization.by_arm[{arm!r}].{name} = {sub[name]} does not re-derive "
                f"from the {arm} rows, which sum to {arm_total}",
            )
    for key, row in block["per_point"].items():
        live = points[key]["per_family_counts"][family]
        _prove(
            all(row[name] == live[name] for name in row),
            f"held_out_generalization.per_point[{key!r}] {row} != the point's own row",
        )
    _prove(set(block["per_point"]) == set(points), "per_point does not cover the point set")
    return True


def epsilon_report(points):
    """D-28/D-29/D-30: the curve total, its summands, both multiplicities, the declarations."""
    noised = [k for k, p in points.items() if p["arm"] in DP_ARMS and p["epsilon"] is not None]
    controls = [k for k, p in points.items() if p["arm"] in DP_ARMS and p["epsilon"] is None]
    adversarial = [k for k, p in points.items() if p["arm"] in ADVERSARIAL_ARMS]
    _prove(
        len(controls) == len(DP_ARMS) and all(points[k]["sigma"] == 0.0 for k in controls),
        f"the sigma=0 controls are {controls}; expected one per DP leg at sigma 0.0",
    )
    _prove(
        all(points[k]["epsilon"] is None and points[k]["accounting"] is None for k in adversarial),
        "an adversarial point carries an epsilon or an accounting",
    )
    _prove(
        set(noised) | set(controls) | set(adversarial) == set(points),
        "the three epsilon classes do not partition the 44 points",
    )
    summands = []
    for key in noised:
        point = points[key]
        _prove(
            point["draws_per_question"] == mitigation_budget.CURVE_K
            and point["draws_per_question_source"] == "mitigation_budget.CURVE_K",
            f"{key}: not a K=CURVE_K curve reading; the total composes curve readings only",
        )
        rederived = phase25_epsilon.point_epsilon_for_sigma(
            point["sigma"], steps=point["composed_steps"], delta=point["delta"]
        )
        _prove(
            rederived == point["epsilon"],
            f"{key}: epsilon {point['epsilon']!r} does not re-derive from the accountant "
            f"({rederived!r}) at sigma={point['sigma']!r}, steps={point['composed_steps']!r}",
        )
        summands.append(point["epsilon"])
    total, total_delta = phase25_epsilon.curve_total(summands, delta=mitigation_unit.DELTA)
    legs = {arm: [k for k in noised if points[k]["arm"] == arm] for arm in DP_ARMS}
    _prove(
        all(len(keys) == mitigation_budget.SWEEP_POINTS - 1 for keys in legs.values()),
        f"each DP leg should publish {mitigation_budget.SWEEP_POINTS - 1} noised points: "
        f"{ {arm: len(keys) for arm, keys in legs.items()} }",
    )
    record = _read_json(phase25_epsilon.MULTIPLICITY_RECORD)
    pin, provenance = record["pin_discrepancy"], record["provenance"]
    rendered = {
        key: phase25_epsilon.report_epsilon(
            point_epsilon=points[key]["epsilon"],
            curve_total_epsilon=total,
            selection_accounted=phase25_epsilon.SELECTION_ACCOUNTED,
        )
        for key in noised + controls
    }
    return {
        "governs": EPSILON_REPORT_GOVERNS,
        "curve_total_epsilon": total,
        "total_delta": total_delta,
        "delta": mitigation_unit.DELTA,
        "delta_source": "mitigation_unit.DELTA",
        "composition": (
            "BASIC (sequential): curve_total_epsilon = math.fsum(summands); "
            "total_delta = k x delta, k = len(summands) — phase25_epsilon.curve_total"
        ),
        "k": len(summands),
        "k_meaning": "the number of noised DP points actually published = len(summands)",
        "summands": summands,
        "summand_keys": noised,
        "summands_are_curve_readings_at": {
            "draws_per_question": mitigation_budget.CURVE_K,
            "draws_per_question_source": "mitigation_budget.CURVE_K",
        },
        "draws_per_question": mitigation_budget.CURVE_K,
        "draws_per_question_source": "mitigation_budget.CURVE_K",
        "selection_accounted": phase25_epsilon.SELECTION_ACCOUNTED,
        "selection_accounted_reason": phase25_epsilon.SELECTION_ACCOUNTED_REASON,
        "total_crosses_both_legs": True,
        "total_crosses_both_legs_reason": phase25_epsilon.TOTAL_CROSSES_BOTH_LEGS,
        "legs_crossed": {arm: {"points": len(keys), "keys": keys} for arm, keys in legs.items()},
        "control_points_excluded": controls,
        "control_has_no_epsilon": phase25_epsilon.CONTROL_HAS_NO_EPSILON,
        "no_joint_bound_over_all_published_artifacts": True,
        "control_epsilon_field_form": phase25_epsilon.CONTROL_EPSILON_FIELD_FORM,
        "adversarial_points_carry_no_epsilon": adversarial,
        "adversarial_reason": ADVERSARIAL_MAKES_NO_FORMAL_CLAIM,
        "dual_granularity": phase25_epsilon.dual_granularity_sentence(total),
        "dual_granularity_epsilon_is": "curve_total_epsilon",
        "multiplicities": {
            "pin_figure": pin["pin_figure"],
            "pin_figure_rule": pin["pin_figure_rule"],
            "artifact_rule_figure": pin["artifact_rule_figure"],
            "artifact_rule": pin["artifact_rule"],
            "status": pin["status"],
            "reconciliation": pin["reconciliation"],
            "epsilon_computed": provenance["epsilon_computed"],
            "record": str(phase25_epsilon.MULTIPLICITY_RECORD.relative_to(_ROOT)),
            "record_sha256": _sha256_of(phase25_epsilon.MULTIPLICITY_RECORD),
        },
        "rendered": rendered,
        "rendered_by": (
            "phase25_epsilon.report_epsilon(point_epsilon=, curve_total_epsilon=, "
            "selection_accounted=) — the only sanctioned rendering (D-30); one per DP point, "
            "controls included with point_epsilon None"
        ),
    }


def prove_area7(points):
    """D-45/D-46/D-49/D-50 at the single write, for all 44 points."""
    need = set(phase25_condition_c.CONDITION_C_FIELDS)
    anchor = phase25_condition_c.RETENTION_LEG_BINDS_AT_ANCHOR
    for key, point in points.items():
        group = point["condition_c"]
        missing = sorted(need - set(group))
        _prove(
            not missing,
            f"{key}: condition_c is missing {missing}. A field that reached the verdict but not "
            "the artifact makes the published verdict non-re-derivable from its single source",
        )
        _prove(
            type(point["zero_extraction_has_nll"]) is bool,
            f"{key}: zero_extraction_has_nll is {point['zero_extraction_has_nll']!r}, not a bool",
        )
        for name in ("dialogue_n_targets", "retention_total_tokens"):
            _prove(type(group[name]) is int, f"{key}: denominator {name} is not an int")
        cap = mitigation_gate.retention_cap(
            retention_noise_floor=group["counterfactual_retention_floor"]
        )
        _prove(
            cap == group["counterfactual_retention_cap"],
            f"{key}: counterfactual_retention_cap {group['counterfactual_retention_cap']!r} != "
            f"retention_cap(retention_noise_floor={group['counterfactual_retention_floor']!r}) = "
            f"{cap!r} (D-50)",
        )
        _prove(
            point["retention_leg_binds_at_anchor"] == anchor,
            f"{key}: the record's RETENTION_LEG_BINDS_AT_ANCHOR differs from the module's",
        )
        _prove(
            point["dialogue_floor_recipe_mismatch"]
            == phase25_condition_c.DIALOGUE_FLOOR_RECIPE_MISMATCH,
            f"{key}: the record's DIALOGUE_FLOOR_RECIPE_MISMATCH differs from the module's",
        )
    return True


def mechanism_pin_disclosure(points):
    """D-25-17-ADV-PIN, disclosed where the pin fields are reported, with the lot re-derived."""
    self_referential = ("composed_lot_sizes", "records_per_lot")
    lots = {}
    for key, point in points.items():
        rule = "adversarial" if point["arm"] in ADVERSARIAL_ARMS else "dp"
        lot = _lot_from_train_config(point)
        _prove(
            lot == point["records_per_lot"] and point["composed_lot_sizes"] == [lot],
            f"{key}: records_per_lot {point['records_per_lot']!r} / composed_lot_sizes "
            f"{point['composed_lot_sizes']!r} != the lot LOT_RULE_BY_ARM[{rule!r}] "
            f"re-derives = {lot}",
        )
        cfg = point["training"]["train_config"]
        lots[key] = {
            "rule": rule,
            "batch_size": cfg["batch_size"],
            "grad_accum_steps": cfg["grad_accum_steps"],
            "n_facts": point["canary_population"]["n_facts"],
            "lot": lot,
            "records_per_lot": point["records_per_lot"],
            "agrees": True,
        }
        point["mechanism_pin_self_referential_fields"] = (
            list(self_referential) if point["arm"] in ADVERSARIAL_ARMS else []
        )
    return {
        "governs": MECHANISM_PIN_DISCLOSURE_GOVERNS,
        "self_referential_fields_by_arm": {
            arm: (list(self_referential) if arm in ADVERSARIAL_ARMS else []) for arm in ORDERED_ARMS
        },
        "real_pins_on_the_adversarial_arm": ["composed_steps", "q", "clip_norm"],
        "lot_rule_by_arm": LOT_RULE_BY_ARM,
        "lot_re_derived_from_train_config": lots,
    }


def never_taught_floor():
    """`results/phase23_never_taught.json`'s `pooled` block verbatim — the shared floor (D-19)."""
    record = _read_json(NEVER_TAUGHT_RECORD)
    block = dict(record["pooled"])
    block["record"] = str(NEVER_TAUGHT_RECORD.relative_to(_ROOT))
    block["record_sha256"] = _sha256_of(NEVER_TAUGHT_RECORD)
    block["extraction_noise_floor"] = record["extraction_noise_floor"]
    block["governs"] = (
        "carried VERBATIM from the never-taught record's `pooled` block: both arms are read "
        "against this ONE already-measured floor as the plane's shared lower-left reference "
        "(D-19). Counts "
        "over questions; the rate beside them is the record's own"
    )
    return block


def provenance(points):
    return {
        "git_sha": git_sha(),
        "device": "cpu — the assembly imports no torch; every number is read from committed "
        "records",
        "torch_version": importlib.metadata.version("torch"),
        "torch_version_source": (
            "importlib.metadata on the installed distribution, read WITHOUT importing torch; the "
            "records' own training/measurement provenance travels inside each point"
        ),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "gate_module_sha256": _module_sha256("mitigation_gate.py"),
        "budget_module_sha256": _module_sha256("mitigation_budget.py"),
        "unit_module_sha256": _module_sha256("mitigation_unit.py"),
        "record_module_sha256": _module_sha256("phase25_record.py"),
        "inputs": {
            "point_records": {
                key: {"path": point["record"], "sha256": _sha256_of(_ROOT / point["record"])}
                for key, point in points.items()
            },
            "recall_record": {
                "path": str(RECALL_RECORD.relative_to(_ROOT)),
                "sha256": _sha256_of(RECALL_RECORD),
            },
            "promotion_record": {
                "path": str(PROMOTION_RECORD.relative_to(_ROOT)),
                "sha256": _sha256_of(PROMOTION_RECORD),
            },
            "never_taught_record": {
                "path": str(NEVER_TAUGHT_RECORD.relative_to(_ROOT)),
                "sha256": _sha256_of(NEVER_TAUGHT_RECORD),
            },
            "multiplicity_record": {
                "path": str(phase25_epsilon.MULTIPLICITY_RECORD.relative_to(_ROOT)),
                "sha256": _sha256_of(phase25_epsilon.MULTIPLICITY_RECORD),
            },
        },
        "recall_source": RECALL_SOURCE_GOVERNS,
        "publication_pathspec": list(_PUBLICATION_PATHSPEC),
        "write_once": (
            "refuse_existing_artifacts, then refuse_if_dirty over the publication pathspec "
            "(untracked counts as dirty), then the bytes. " + RERUN_ROUTE
        ),
        "canary_reservations": phase25_prereg.CANARY_RESERVATIONS,
        "publication_obligation": phase25_prereg.PUBLICATION_OBLIGATION,
        "git_surface_exception": phase25_prereg.GIT_SURFACE_EXCEPTION,
    }


def assemble():
    """Build the frontier document. Every write-time proof runs here; no bytes are written."""
    points = load_point_records()
    recall = _read_json(RECALL_RECORD)
    promotion = _read_json(PROMOTION_RECORD)
    attach_recall(points, recall)
    attach_verdicts(points, promotion)
    prove_area7(points)
    pins = mechanism_pin_disclosure(points)
    document = {
        "governs": (
            "FRONT-03's single source of truth: the 44 point records inline with their "
            "per-question rows, the recall readings, the verdicts, the dual epsilon report, "
            "held_out_generalization and the module digests — counts, never rates; every bound "
            "re-derivable; one file. Assembled write-once against a clean tree (D-31)."
        ),
        "record": str(FRONTIER_RECORD.relative_to(_ROOT)),
        "point_key_grammar": POINT_KEY_GRAMMAR,
        "point_keys": list(points),
        "arms": list(ORDERED_ARMS),
        "axis_for_arm": AXIS_FOR_ARM,
        "held_out_generalization": held_out_generalization(points),
        "epsilon_report": epsilon_report(points),
        "verdicts": verdicts_block(points, promotion),
        "never_taught_floor": never_taught_floor(),
        "retention_leg_binds_at_anchor": phase25_condition_c.RETENTION_LEG_BINDS_AT_ANCHOR,
        "retention_squeeze_is_the_frontier": phase25_condition_c.RETENTION_SQUEEZE_IS_THE_FRONTIER,
        "retention_floor_disclosure": phase25_condition_c.RETENTION_FLOOR_DISCLOSURE,
        "dialogue_floor_recipe_mismatch": phase25_condition_c.DIALOGUE_FLOOR_RECIPE_MISMATCH,
        "dialogue_floor_sensitivity": phase25_condition_c.DIALOGUE_FLOOR_SENSITIVITY,
        "mechanism_pin_disclosure": pins,
        "adversarial_makes_no_formal_claim": ADVERSARIAL_MAKES_NO_FORMAL_CLAIM,
        "provenance": provenance(points),
        "points": points,
    }
    _prove(
        tuple(document["point_keys"]) == tuple(ORDERED_POINT_KEYS()) == tuple(document["points"]),
        "ordered point_keys hard equality failed at the single write",
    )
    prove_held_out_generalization(document)
    return document


def _write(path, document):
    """BOTH refusals, then the bytes — `phase24_record._write`'s order, atomic like the records."""
    path = pathlib.Path(path)
    refuse_second_assembly(path)
    refuse_if_dirty(
        who="phase25_record",
        detail=_DIRTY_DETAIL,
        pathspec=_PUBLICATION_PATHSPEC,
        cwd=_ROOT,
    )
    payload = json.dumps(document, indent=2, sort_keys=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    try:
        with handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(handle.name, path)
    except BaseException:
        pathlib.Path(handle.name).unlink(missing_ok=True)
        raise
    return path


def main():
    """The single write of `results/phase25_frontier.json`. Refuses an existing artifact first."""
    refuse_second_assembly()
    document = assemble()
    written = _write(FRONTIER_RECORD, document)
    size = written.stat().st_size
    report = document["epsilon_report"]
    print(
        f"[phase25_record] wrote {written.relative_to(_ROOT)} — {len(document['points'])} points, "
        f"{size:,} bytes; curve_total_epsilon {report['curve_total_epsilon']!r} over "
        f"{report['k']} summands at total_delta {report['total_delta']!r}; "
        f"tallies {document['verdicts']['tallies']}; held-out "
        f"{document['held_out_generalization']['successes']}/"
        f"{document['held_out_generalization']['questions']}"
    )
    return written


if __name__ == "__main__":
    main()
