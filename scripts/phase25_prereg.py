"""PHASE 25'S BLIND RULES — committed while `git ls-files 'results/phase25_point_*'` is EMPTY.

**THIS FILE EXISTS BEFORE THE DATA DOES, AND THAT IS THE ENTIRE PROPERTY IT BUYS.** Two facts make
that non-negotiable, and neither is recoverable after the fact:

  * **A REPRODUCTION CHECK WRITTEN AFTER THE READING IS A RATIONALISATION.** Once 790/1008 is on
    screen for a second time, any threshold, any tolerance and any "close enough" is a threshold
    chosen with the answer visible. `prove_reproduction` therefore compares under hard `==` on
    integer counts and it is committed HERE, in wave 1, before a single GPU second is spent.
  * **A ONE-ATTEMPT RULE WRITTEN AFTER A RE-RUN IS AN EXCUSE.** A rule that arrives once a point
    has already been drawn twice is a rule written to permit what already happened.
    `prove_first_attempt` is committed while no `results/phase25_point_*.json` exists at all, which
    is a fact about git's object graph rather than a claim in a paragraph.

`scripts/phase19_floor.py` states the general form of this in its own words, and it is the reason
this module exists at all: *"The reduction is never read back out of an artifact as a pre-reduced
scalar, because a reduction chosen in the artifact writer is a reduction chosen with the numbers
already visible."* The same applies to a HALT written in the driver that would have to halt.

**WHY THIS IS A NEW MODULE AND NOT A REUSE (25-RESEARCH.md §C6).**
`scripts/phase23_matched_prereg.py` already carries a `prove_first_attempt`, and mechanically a
Phase-25 tracked list could be passed to it. It must not be. Its refusal text hard-codes its own
Phase-23 glob, so a Phase-25 call would emit a refusal naming the WRONG glob — and that module is
EDIT-ONCE and already spent, so the text cannot be widened. D-10's per-point rule therefore gets its
own function here, written in that function's register (four scope clauses, none softened) with
Phase 25's own glob in its own text. **This module imports nothing from the spent one.**

**WHAT THIS MODULE IS ALLOWED TO IMPORT.** Stdlib only, in wave-1 discipline: it must never
import a driver, a scorer or anything that touches a device.

CPU-only, GPU-free, no torch, no network.
"""

import hashlib
import json
import pathlib

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# The date this file was committed, and the property that date certifies. Every rule below is
# dated by it: at this commit `git ls-files 'results/phase25_point_*.json'` returned NOTHING, so
# none of these rules could have been shaped by a point that did not yet exist.
COMMITTED = "2026-08-31"
POINT_RECORDS_AT_COMMIT = 0


def _prove(condition, message):
    """``SystemExit`` on a broken invariant — ``scripts/phase23_prereg.py:56``'s register.

    Never ``assert``. ``python -O`` strips ``assert`` outright, and this module is almost entirely
    refusals: under ``-O`` a bare-``assert`` implementation would admit every case it exists to
    reject, silently.
    """
    if not condition:
        raise SystemExit(f"[phase25_prereg] {message}")


def _read_json(relative_path):
    """One committed record, opened from the repo root rather than from the caller's cwd."""
    return json.loads((_REPO_ROOT / relative_path).read_text(encoding="utf-8"))


# =================================================================================================
# ===== (a) THE REPRODUCTION GATE (D-07) =====
#
# D-01 re-runs the σ=0 control under Phase 25's own prefix at both capacities. That re-run is only
# worth its ~40 s of training if its reading is CHECKED against Phase 23's, and only worth checking
# if the check was written first. This is that check.
# =================================================================================================

# The record the target is READ FROM. Phase 25 never retypes 790/1008 out of CONTEXT prose: the
# prose is a restatement, the record is the source, and `reproduction_source_reading()` below is
# what proves the two still agree.
REPRODUCTION_SOURCE_RECORD = "results/phase23_sigma_zero.json"

# THE TARGET, PINNED AS INTEGER COUNTS. `primary.k` / `primary.n` of the record above.
REPRODUCTION_K = 790
REPRODUCTION_N = 1008

REPRODUCTION_PROVENANCE = {
    "record": REPRODUCTION_SOURCE_RECORD,
    "k_path": "primary.k",
    "n_path": "primary.n",
    "rate": 0.7837301587301587,
    # THE RECIPE FIELDS THAT MAKE THE TARGET LEGITIMATE. A count reproduces only if the run that
    # produced it is the run being reproduced; these five are what D-01 means by "bit-level".
    "clip_norm": 1000000.0,
    "clip_bind_count": 0,
    "composed_steps": 200,
    "composed_lot_sizes": [8],
    "records_per_lot": 8,
    "seed": 1337,
    "governs": (
        "WHETHER ANY NON-CONTROL SWEEP POINT MAY RUN AT ALL. A miss HALTS the sweep at ZERO sweep "
        "points; it does not warn, it does not downgrade, and there is no override flag. It "
        "governs nothing else: it decides no verdict, sets no threshold and judges no arm"
    ),
    "comparison": (
        "hard `==` on integer counts, no tolerance and no rate comparison. The reading is a COUNT "
        "over questions, and a count has no tolerance — 789/1008 is a DIFFERENT measurement, not a "
        "near-miss of this one"
    ),
}

# D-04's four declared differences, IMPORTED BY PATH + DIGEST rather than retyped. The halt message
# below reads them live, so if Phase 23's record ever grows a fifth the message cannot silently
# drop it — `declared_differences()` refuses instead.
DECLARED_DIFFERENCES_SOURCE = "results/phase23_matched_control.json"
DECLARED_DIFFERENCES_COUNT = 4

# SUSPECT #1, NAMED BEFORE THERE IS ANYTHING TO SUSPECT. If the count moves, the ratio-0.0
# byte-identity assertion is the first thing to check: it is the one claim in the tree asserting
# that an adversarial-seam default path is byte-identical to the pre-seam build, and if it has
# quietly stopped holding then the corpus underneath every reading has moved.
REPRODUCTION_SUSPECT_ONE = (
    "the ratio-0.0 byte-identity assertion (`build_bins(..., adversarial_ratio=0.0)` against the "
    "no-kwarg build): token sha256 f146d426..., mask sha256 a2c4771f..., 176 episodes / 7,581 "
    "tokens. If that pair no longer reproduces, the corpus under EVERY reading has moved and the "
    "count difference is a symptom rather than the defect"
)


def reproduction_source_reading():
    """``(k, n)`` read LIVE from ``REPRODUCTION_SOURCE_RECORD``'s ``primary`` block.

    This is what lets a caller prove the PIN still matches the RECORD IT NAMES, rather than proving
    the pin against itself. T-25-02: a target retyped from prose can drift from the artifact it
    claims to quote, and nothing in a comparison of a constant with itself would ever notice.
    """
    payload = _read_json(REPRODUCTION_SOURCE_RECORD)
    primary = payload.get("primary")
    _prove(
        hasattr(primary, "keys") and "k" in primary and "n" in primary,
        f"{REPRODUCTION_SOURCE_RECORD} has no `primary` block carrying `k` and `n`. The pin above "
        "names that path explicitly, so a record that no longer carries it cannot be the record "
        "this gate reproduces",
    )
    return primary["k"], primary["n"]


def declared_differences():
    """D-04's four declared differences, read live from Phase 23's matched-control record.

    **REFUSES ANY LENGTH BUT FOUR.** The halt message below prints this list as the starting
    investigation set, and a message that silently dropped a fifth entry would send an investigator
    looking in four places when five were declared.
    """
    entries = _read_json(DECLARED_DIFFERENCES_SOURCE).get("declared_differences")
    _prove(
        isinstance(entries, list) and len(entries) == DECLARED_DIFFERENCES_COUNT,
        f"{DECLARED_DIFFERENCES_SOURCE} carries "
        f"{len(entries) if isinstance(entries, list) else entries!r} declared difference(s), not "
        f"{DECLARED_DIFFERENCES_COUNT}. D-04 imports this list BY PATH so it cannot be retyped; a "
        "length change means Phase 23's record moved, and the halt message must not print a "
        "truncated investigation list as if it were the whole one",
    )
    return entries


def declared_differences_digest():
    """sha256 of ``DECLARED_DIFFERENCES_SOURCE``'s BYTES — the ``+ digest`` half of D-04."""
    return hashlib.sha256((_REPO_ROOT / DECLARED_DIFFERENCES_SOURCE).read_bytes()).hexdigest()


def prove_reproduction(k, n):
    """D-07: the σ=0 control reproduces Phase 23's COUNT, or the sweep HALTS at zero sweep points.

    Returns ``None`` silently on a match. On a miss it raises ``SystemExit`` — there is no warning
    branch, no tolerance and no override flag, exactly as ``phase23_prereg.sigma_zero_verdict`` has
    none.

    **HARD ``==`` ON INTEGERS, AND WHY THAT IS NOT AN OVERSIGHT.** The reading is a COUNT over
    questions — 790 of 1008 — and a count has no tolerance. ``math.isclose`` on a count would admit
    789 as "close", but 789/1008 is a different measurement produced by a different set of answers,
    not a rounding of this one. The rate ``0.7837301587301587`` is a DERIVED presentation of the
    same two integers and is deliberately not what is compared: floating-point equality on a
    derived quotient is a weaker check that looks like a stronger one.

    **BOTH DIRECTIONS BREACH.** A control that beats 790 is as much a signal as one that misses it,
    for ``sigma_zero_verdict``'s recorded reason: every correctness bug in this class IMPROVES the
    reading. Stop-and-fix is reversible; publish-compromised is not.

    The 43 further points are only interpretable RELATIVE to this control. That is why the scope of
    the refusal is the whole sweep rather than this one point: an uninterpretable control does not
    produce a bad point, it produces 43 uninterpretable ones (T-25-03).
    """
    _prove(
        isinstance(k, int) and not isinstance(k, bool),
        f"k is {k!r}, which is not an int (bool excluded). This gate compares COUNTS under hard "
        "`==`; a float that happens to equal the pin would pass a comparison it was never meant to "
        "reach, and a bool is an int subclass that would compare True against 1",
    )
    _prove(
        isinstance(n, int) and not isinstance(n, bool),
        f"n is {n!r}, which is not an int (bool excluded). The denominator is a COUNT of questions "
        "and is what separates 'no question was answered' from 'no question was asked'",
    )

    if k == REPRODUCTION_K and n == REPRODUCTION_N:
        return None

    listed = "\n".join(
        f"    {index + 1}. {entry['difference']}"
        for index, entry in enumerate(declared_differences())
    )
    raise SystemExit(
        f"[phase25_prereg] D-07 HALT — THE SWEEP IS HALTED: it HALTS at zero sweep points, and "
        f"zero non-control points will run.\n"
        f"  expected reading : {REPRODUCTION_K}/{REPRODUCTION_N} "
        f"({REPRODUCTION_SOURCE_RECORD}, primary.k/primary.n)\n"
        f"  observed reading : {k}/{n}\n"
        f"  comparison       : hard `==` on integer counts — no tolerance, because the reading is "
        f"a COUNT\n"
        f"  recipe pinned    : clip_norm {REPRODUCTION_PROVENANCE['clip_norm']!r}, clip_bind_count "
        f"{REPRODUCTION_PROVENANCE['clip_bind_count']!r}, composed_steps "
        f"{REPRODUCTION_PROVENANCE['composed_steps']!r}, records_per_lot "
        f"{REPRODUCTION_PROVENANCE['records_per_lot']!r}, seed "
        f"{REPRODUCTION_PROVENANCE['seed']!r}\n"
        f"\n"
        f"  SUSPECT #1: {REPRODUCTION_SUSPECT_ONE}.\n"
        f"\n"
        f"  THEN THE {DECLARED_DIFFERENCES_COUNT} DECLARED DIFFERENCES, as the starting "
        f"investigation list — read live from {DECLARED_DIFFERENCES_SOURCE} "
        f"(sha256 {declared_differences_digest()}), never retyped:\n"
        f"{listed}\n"
        f"\n"
        "  The control must reproduce Phase 23's reading EXACTLY. It does not. The cause must be "
        "ROOT-CAUSED AND FIXED before any further point runs — this is not a warning and there is "
        "no override flag. The 43 further points are interpretable only RELATIVE to this control, "
        "so an unexplained control does not produce one bad point, it produces 43 uninterpretable "
        "ones. Stop-and-fix is reversible; publish-compromised is not."
    )


# =================================================================================================
# ===== (b) THE PER-POINT ONE-ATTEMPT RULE (D-10) =====
#
# The unit is the SWEEP POINT, not the sweep. 44 points are drawn over days on a machine whose last
# production run was killed externally at 60 minutes; a rule whose unit was "the sweep" would make
# the first kill either fatal or meaningless.
# =================================================================================================

POINT_RECORD_PREFIX = "results/phase25_point_"
POINT_RECORD_GLOB = POINT_RECORD_PREFIX + "*.json"

POINT_RECORD_GLOB_PROVENANCE = {
    "glob": POINT_RECORD_GLOB,
    "committed": COMMITTED,
    "point_records_at_commit": POINT_RECORDS_AT_COMMIT,
    "unit": (
        "ONE SWEEP POINT. A point with a committed record is EVIDENCE and is never re-run; a point "
        "killed before any reading landed produced no evidence, so resuming it is the SAME attempt"
    ),
    "checkable_by": (
        "the caller's `git ls-files` result. This module runs no subprocess: the tracked list is "
        "the caller's to produce, so the rule can be unit-tested without a repository"
    ),
    "governs": (
        "whether a SECOND attempt at one point may proceed, and nothing else. It sets no "
        "threshold, judges no reading and decides no verdict"
    ),
}


def point_record_path(point_key):
    """One sweep point's committed record path, DERIVED — never a string literal at a call site.

    ``teach_persona.fact_bin_path``'s register, for its recorded reason: this repository has
    shipped plans naming artifact paths the code refuses, and one derivation function is the
    cheapest fix. `point_key` is restricted to alphanumerics, ``-`` and ``_`` — a path separator or
    a ``..`` here would file a point OUTSIDE ``results/``, where every guard binding on
    ``POINT_RECORD_GLOB`` is blind to it rather than merely unwatched. That restriction is also why
    σ is rendered with the point written ``p`` everywhere in this phase.
    """
    _prove(
        isinstance(point_key, str)
        and bool(point_key)
        and point_key.replace("-", "").replace("_", "").isalnum(),
        f"point_key {point_key!r} is not a non-empty alphanumeric/-/_ name. A path separator or a "
        f"`..` here would place a point's record outside `results/`, where {POINT_RECORD_GLOB} — "
        "and therefore the one-attempt rule itself — cannot see it at all",
    )
    return f"{POINT_RECORD_PREFIX}{point_key}.json"


def prove_first_attempt(tracked, *, point_key):
    """ONE ATTEMPT PER POINT: refuse if THIS point's record is already TRACKED.

    ``tracked`` is the caller's ``git ls-files POINT_RECORD_GLOB`` result. This module runs no
    subprocess.

    **THE MESSAGE STATES THE GUARANTEE AT ITS TRUE STRENGTH, NOT A STRONGER ONE.** An overclaimed
    guarantee is precisely the defect a pre-registration exists to prevent. Four scope clauses, all
    four in the message, none of them softened.
    """
    record = point_record_path(point_key)
    already = sorted(entry for entry in tracked if entry == record)
    _prove(
        not already,
        f"ONE ATTEMPT — REFUSED for point {point_key!r}. Its record is ALREADY TRACKED: {already}. "
        f"This phase's rules were pre-registered on {COMMITTED} while "
        f"`git ls-files {POINT_RECORD_GLOB}` returned nothing. A SECOND attempt at one point with "
        "the first one's reading on screen is exactly the freedom that pre-registration spends.\n"
        "\n"
        "THE SCOPE OF THIS RULE, STATED AT ITS TRUE STRENGTH — FOUR CLAUSES, NOT THREE:\n"
        "\n"
        "  (1) IT BINDS ACROSS COMMITS, AND ONLY THERE. `.gitignore:17` ignores `data/` and "
        "`.gitignore:14` ignores `checkpoints/`, so this point's draw cache and its exported "
        "adapter can exist on disk with NOTHING TRACKED — and an operator could delete both inside "
        "the uncommitted window between the run and its commit, leaving NO RESIDUE THIS FUNCTION "
        "CAN SEE. The COMMITTED RECORD is therefore what makes 'a reading landed' CHECKABLE rather "
        "than asserted, which is why each completed shape block's sha256 travels INSIDE it: "
        "without those, a delete-and-redraw inside one point would leave no trace at all.\n"
        "\n"
        "  (2) THE UNIT IS THE POINT, NOT THE SWEEP. A point KILLED before any reading landed "
        "produced NO EVIDENCE, so resuming it is the SAME ATTEMPT and is not refused here — that "
        "is D-09's shape-keyed block resume, and it is why this rule keys on the committed record "
        "rather than on the sweep having started. What is refused is a second attempt at a point "
        "whose reading is already committed and already visible.\n"
        "\n"
        f"  (3) THE REFUSAL IS SPECIFIC, AND SAYS SO: point {point_key!r}, record {record}. It "
        "names one point key and one tracked path, so it can never be read as 'the sweep is "
        "blocked' when what is blocked is one already-answered point.\n"
        "\n"
        "  (4) THERE IS A SANCTIONED RE-RUN ROUTE, AND IT IS VISIBLE RATHER THAN REFUSED. Delete "
        "the committed record IN ITS OWN COMMIT, with the reason in the commit message, and re-run "
        "the point. That leaves a VISIBLE DELETION in git history — which is the whole difference "
        "between a re-run that is disclosed and one that is laundered. This function is not a dead "
        "end and does not pretend to be a wall.\n"
        "\n"
        "D-07's halt has no override flag and this rule has none either. If the re-run breaches, "
        "THE FINDING IS THE DELIVERABLE.",
    )
    return True
