"""PRE-REGISTERED definition of the PRIVACY UNIT for v4.0 — what one privacy record IS.

Committed BEFORE any ``results/phase21_*`` number exists. ``scripts/mitigation_gate.py`` earned its
authority exactly this way, and this module is the continuation of that discipline for a different
subject: the gate states what a swept point must ACHIEVE, this states what the thing being
protected IS. An epsilon computed against the wrong unit is not a number a re-run can correct —
which is why the definition is pinned before the mechanism that will consume it exists, and why
this is the milestone's longest dependency chain.

CLOSED AT THE FIRST ARTIFACT, AND THE CLOSURE IS MECHANICAL
===========================================================
The moment any ``results/phase21_*`` artifact is committed, this file is CLOSED. A correction after
that point is a DATED CONTINUATION via ``scripts/_addendum.py``, never an edit.
``tests/test_phase20_prereg.py::test_phase21_prereg_is_frozen_before_every_phase21_result``
requires EVERY commit touching this file to be an ancestor of every ``results/phase21_*``
artifact's first add — ``:143`` is ``git log -- <pin>``, i.e. every commit and not merely the first,
so a LATER edit is caught rather than only a wrong initial ordering. A ``git rm`` plus a re-add at
the same path CANNOT launder it: the guard takes ``adds[-1]`` (``:157``), the EARLIEST add, so the
original ordering survives the deletion. There is no recovery path and no force flag, and that cost
is the entire reason the guard is armed in this phase's FIRST plan rather than retro-fitted once
there is something to miss.

WHY THIS MODULE IMPORTS NOTHING, AND WHERE THE ARTIFACT WRITER LIVES (D-22)
--------------------------------------------------------------------------
Being named ``mitigation_*.py`` joins ``tests/test_phase20_prereg.py:72``'s glob, and that glob
carries a HARD IMPORT CEILING: ``imported`` accumulates across EVERY module in the glob (``:498``)
and is asserted a SUBSET of ``{"pathlib", "sys", "erasure_gate"}`` (``:522``). ``json`` is
therefore unreachable from any ``mitigation_*`` module, so THIS MODULE DOES ZERO I/O. The rule
lives here; its emission lives OUTSIDE the glob in ``scripts/phase21_unit_record.py``, which is
where ``json`` and the ``results/phase21_*`` writes belong. That mirrors the repo's own gate/budget
split — the rule in one place, its emission in another — and it keeps this file's surface minimal,
which is precisely what makes freezing it cheap.

The ceiling permits three names. This module uses ZERO, which is the cheapest way to stay inside
it: ``n ** -1.1`` is an OPERATOR, and every number below is arithmetic on literals, so there is
nothing to import.

WHY ``_prove`` IS DEFINED HERE RATHER THAN IMPORTED FROM ``mitigation_gate``
---------------------------------------------------------------------------
``scripts/mitigation_gate.py:66`` already defines this exact three-line helper, and this project's
standing discipline is "import the instrument, never copy it". That discipline is OVERRIDDEN here
by the ceiling above, not forgotten: importing a sibling would add ``mitigation_gate`` to the
accumulated ``imported`` set and turn ``tests/test_phase20_prereg.py:523`` RED. The local
definition is a FORCED CONSEQUENCE of D-22, recorded so a reader does not mistake it for a copied
instrument nobody noticed. ``_prove`` is a control-flow shape rather than an estimator, so the
failure mode the import-never-copy rule exists to prevent — two copies of a bound silently
diverging, ``tests/test_phase20_prereg.py:574`` — has no analogue here.

WHERE PHASE 22+ CONSTANTS GO — RECORDED, AND DELIBERATELY NOT ACTED ON (D-21)
----------------------------------------------------------------------------
Constants a later phase has not yet discovered land in an UNFROZEN ``mitigation_*.py`` sibling,
unpinned until that phase arms it with its own explicit pre-registration path constant. **Phase 21
does not create that file.** An empty module is a placeholder that joins the import-graph scan
while being green over nothing, and ``tests/test_phase20_prereg.py:64-66`` records that the glob
exists precisely so a sibling "enters these scans the moment it exists" — so deferring costs
nothing and creating it early costs a green-over-nothing scan.

WHAT IS DELIBERATELY ABSENT
---------------------------
D-11's replay VOLUME constant (4 windows per fact = 1,024 tokens, D-24) is NOT here. It is settled
in its own round, carries its own differential side-channel guard, and lands in
``scripts/teach_persona.py`` in plan 21-08. Freezing means content-complete at arm time, so the
boundary of this file is exactly the set of decisions that cannot be revisited: D-23's three, and
nothing else.

CPU-only: zero imports, zero I/O, zero network.
"""


def _prove(condition, message):
    """``SystemExit`` on a broken invariant — ``scripts/mitigation_gate.py:66``'s register.

    ``SystemExit`` and deliberately NOT ``assert``: an ``assert`` is strippable under ``-O``, and a
    proof that disappears under an optimisation flag is not a proof. The message carries this
    module's own name in brackets — an abort naming the wrong module sends its reader to the wrong
    file.
    """
    if not condition:
        raise SystemExit(f"[mitigation_unit] {message}")


# ---------------------------------------------------------------------------------------------
# 1. THE PRIVACY UNIT (SC1 / UNIT-01). One taught FACT, never one training example.
# ---------------------------------------------------------------------------------------------
PRIVACY_UNIT = "one taught fact"

PRIVACY_UNIT_ARITHMETIC = (
    "WHY AN EXAMPLE-LEVEL EPSILON BOUNDS NOTHING ABOUT A FACT. `get_batch_memmap_masked` "
    "(`src/personacore/training/data.py:117`) draws `batch_size` window START OFFSETS with "
    "`np.random.randint` over a FLAT CONCATENATED bin — with replacement, and with no notion of "
    "where one fact ends and the next begins. A single fact is therefore touched an unbounded "
    "number of times per pass, so `one example` is not a stable quantity to protect and an "
    "epsilon accounted per example says nothing about what an adversary learns about a FACT. "
    "\n\n"
    "ANALYTIC, and labelled as such because UNIT-03 refuses precisely this kind of number as a "
    "final answer. At the real budget — MAX_STEPS = 200 x BATCH_SIZE = 8 = 1,600 draws "
    "(`scripts/teach_persona.py:523` and `:517`) over the 7,581-token facts-only teaching bin "
    "(D-10; 8 facts, mean 947.625 tokens each) — the expected number of draws whose window "
    "overlaps a given fact is "
    "\n\n"
    "    1,600 * (947.625 + 256) / (7,581 - 256 - 1) = 262.94"
    "\n\n"
    "THE FORMULA IS WRITTEN OUT RATHER THAN LEFT IMPLICIT, because the reading that stating a "
    "denominator invites — draws * block_size / bin_tokens = 1,600 * 256 / 7,581 = 54.03 — is NOT "
    "this number, and a number nobody can reproduce cannot be corrected inside a frozen file. A "
    "window of `block_size` tokens overlaps a fact of L tokens from any of `L + block_size` start "
    "offsets, and `randint(0, len(data) - block_size - 1)` offers `7,581 - 257` of them. "
    "\n\n"
    "The same formula on the replay-in-bin composition (15,162 tokens at replay_ratio 1.0) gives "
    "129.21, so removing replay from the teaching bin (D-10) roughly DOUBLES the unaligned "
    "multiplicity — the same 1,600 draws land on half the data. A decision taken purely for "
    "honest accounting made the unaligned number WORSE, which is what makes this indictment "
    "stronger under D-10 rather than weaker. "
    "\n\n"
    "Under fact-aligned accumulation (D-01, D-05, D-06) the same quantity is exactly 1 per "
    "micro-step, deterministic, by construction — which is what makes SAMPLING_RATE_Q = 1.0 below "
    "honest rather than assumed. "
    "\n\n"
    "THIS MODULE IS NOT THE SOURCE OF THE MEASUREMENT. Both figures above are EXPECTATIONS over "
    "the draw distribution, computed from the geometry. D-26 requires the OBSERVED per-fact "
    "distribution — min/max/mean/spread on an instrumented loader at SEED = 1337 — and plan 21-11 "
    "writes that measured row to `results/phase21_*`. A reader should expect the measurement to "
    "differ from 262.94 by sampling noise; a reader quoting 262.94 AS a measurement is quoting "
    "the wrong thing."
)


# ---------------------------------------------------------------------------------------------
# 2. THE LOT AND THE SAMPLING RATE (SC4 / UNIT-04, locked as D-07). Replay sits OUTSIDE N.
# ---------------------------------------------------------------------------------------------
SAMPLING_RATE_Q = 1.0


def privacy_n(n_facts):
    """The privacy N is the FACT COUNT, and nothing rides inside it but facts.

    ``int`` rather than a pass-through so a float ``n_facts`` cannot silently become a fractional
    N in a downstream epsilon. There is no clamping and no default: a caller that does not know how
    many facts it is teaching does not know what it is protecting.
    """
    return int(n_facts)


REPLAY_OUTSIDE_N = (
    "REPLAY SITS OUTSIDE THE PRIVACY N ENTIRELY: honest q = 1, N = n_facts (D-07). Replay is "
    "public PersonaChat dialogue serving a TRAINING-STABILITY role; it is not private data needing "
    "protection. "
    "\n\n"
    "THE EPSILON CONSEQUENCE, which is the whole reason this is a pinned decision and not an "
    "implementation detail: counting replay inside N would shrink q artificially and produce a "
    "flatteringly SMALL epsilon that does not reflect what the mechanism actually protects. That "
    "is the exact trap UNIT-04 names. A subsampled-mechanism epsilon shrinks with q, so folding "
    "public padding into the lot buys a better-looking number for nothing — the published bound "
    "would be about a lot that includes data no adversary cares about. "
    "\n\n"
    "THE MEASURED BASIS: at `replay_ratio = 1.0` replay is 7,581 tokens, exactly 50% of today's "
    "bin — so this is not a marginal share being waved away, it is half the tokens. "
    "\n\n"
    "AND REPLAY IS NOT DROPPED FROM THE DP ARMS (D-08). Removing it would risk gate condition (c): "
    "losing dialogue capability is exactly the class of harm an identity-only guard misses, and "
    "`f_C = 0.5` sits only 2.24x above the measured non-vacuity floor 0.2237 (Phase 20 D-17). "
    "There is little room before a dialogue collapse stops being distinguishable from a pass. So "
    "replay stays in the run and leaves the ACCOUNTING, which is a different thing from leaving "
    "the training."
)


# ---------------------------------------------------------------------------------------------
# 3. DELTA (SC4 / UNIT-05). The pinned literal, and the recipe that was rejected.
# ---------------------------------------------------------------------------------------------
DELTA = 1e-5

# `delta` must be well below 1/N so the "(epsilon, delta)" guarantee is not dominated by the
# delta term at the capacities this milestone runs. 0.01 is the ceiling every check below is
# stated against, so the pass/fail margins are ratios to ONE published number rather than to a
# threshold re-chosen per call site.
DELTA_TIMES_N_CEILING = 0.01

REJECTED_DELTA_RECIPE = "1/N**1.1"


def rejected_delta(n):
    """The REJECTED recipe, kept runnable so its self-contradiction is checkable, not quoted.

    Deliberately shipped as executable code rather than as a number in prose: a rejected
    alternative recorded only as prose is a claim, while one recorded as a function is a claim
    anyone can re-run at any N. ``n ** -1.1`` is an operator, so this needs no import — which is
    what lets the rejection live inside D-22's ceiling at all.
    """
    return n**-1.1


REJECTED_DELTA_REASON = (
    "`1/N**1.1` FAILS ITS OWN `delta * N < 0.01` ASSERTION AT BOTH CAPACITIES THIS MILESTONE RUNS, "
    "which is a strictly stronger record than a single-N check. At N = 8 it is "
    "0.10153154954452942, "
    "so delta * N = 0.8122523963562354 — failing by 81.2x. At N = 64 it is 0.010308655552913232, "
    "so delta * N = 0.6597539553864469 — failing by 66.0x. The recipe is not merely wrong at the "
    "small capacity; it is wrong at n = 8 AND at n = 64, and a reader who checked only n = 8 could "
    "have believed it was an artefact of the small arm. "
    "\n\n"
    "The pinned literal passes at both: delta * N = 8e-05 at N = 8 (by 125.0x) and 0.00064 at "
    "N = 64 (by 15.625x). Note the direction — a CONSTANT delta gets tighter relative to the "
    "ceiling as N grows, while the rejected recipe stays broken across the whole range, so the "
    "n = 64 arm is where the literal has least headroom and it still clears by more than an order "
    "of magnitude."
)


# ---------------------------------------------------------------------------------------------
# THE GUARDS. Module scope, so a wrong edit fails at IMPORT rather than inside a consumer that
# has already spent compute — the same placement reason as `mitigation_gate.py:141` and `:175`.
# ---------------------------------------------------------------------------------------------
_prove(
    DELTA * 8 < DELTA_TIMES_N_CEILING,
    f"delta * 8 = {DELTA * 8} against the ceiling {DELTA_TIMES_N_CEILING}. The pinned literal "
    f"{DELTA} clears it by {DELTA_TIMES_N_CEILING / (DELTA * 8)}x at the n = 8 arm; a delta that "
    "does not is a delta whose guarantee is dominated by its own failure probability",
)
_prove(
    DELTA * 64 < DELTA_TIMES_N_CEILING,
    f"delta * 64 = {DELTA * 64} against the ceiling {DELTA_TIMES_N_CEILING}. This is the TIGHTER "
    f"of the two capacities — it clears by {DELTA_TIMES_N_CEILING / (DELTA * 64)}x against "
    f"{DELTA_TIMES_N_CEILING / (DELTA * 8)}x at n = 8 — so it is the check that actually binds",
)

# The two below assert the recipe FAILS. They are stated as `>=` rather than as a comment saying
# "this would have failed", because a rejected alternative that is merely described is a rejection
# nobody can re-run. Both capacities are checked deliberately: the recipe is wrong at n = 8 AND at
# n = 64, and asserting only the small one would leave open the reading that n = 64 rescued it.
_prove(
    rejected_delta(8) * 8 >= DELTA_TIMES_N_CEILING,
    f"{REJECTED_DELTA_RECIPE} at N = 8 gives {rejected_delta(8)}, so delta * N = "
    f"{rejected_delta(8) * 8} — it must FAIL the {DELTA_TIMES_N_CEILING} ceiling, by "
    f"{rejected_delta(8) * 8 / DELTA_TIMES_N_CEILING}x. If this proof ever stops holding, the "
    "recorded reason for rejecting the recipe has stopped being true and UNIT-05's record is stale",
)
_prove(
    rejected_delta(64) * 64 >= DELTA_TIMES_N_CEILING,
    f"{REJECTED_DELTA_RECIPE} at N = 64 gives {rejected_delta(64)}, so delta * N = "
    f"{rejected_delta(64) * 64} — it must FAIL the {DELTA_TIMES_N_CEILING} ceiling, by "
    f"{rejected_delta(64) * 64 / DELTA_TIMES_N_CEILING}x. This is the n = 64 half of the record: "
    "the recipe is broken at BOTH capacities, not merely at the small one",
)

_prove(
    SAMPLING_RATE_Q == 1.0,
    f"SAMPLING_RATE_Q is {SAMPLING_RATE_Q}, not 1.0. Under fact-aligned accumulation every fact "
    "enters every lot exactly once by construction (D-01, D-05, D-06), so any q < 1 here would be "
    "a subsampling discount claimed by a mechanism that does not subsample — the "
    "flattering-epsilon trap D-07 exists to refuse",
)
