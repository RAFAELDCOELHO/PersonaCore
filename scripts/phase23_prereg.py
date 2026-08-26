"""PHASE 23'S BLIND RULES — committed before any Phase-23 number exists. **THIS FILE IS EDIT-ONCE.**

Three of Phase 23's four items are pre-registrations: they are committed before the first run or
they are a post-hoc peek. D-03's noise-floor REDUCTION, D-03's SEED COUNT, D-04's HALT verdict and
D-06's withdrawal rule all live here, in one module, landing in wave 1 — before `scripts/phase23_
cost.py` measures anything and before `scripts/phase23_run.py` executes anything.

`scripts/phase19_floor.py` states the reason in its own words, and it is the reason this module
exists at all: *"The reduction is never read back out of an artifact as a pre-reduced scalar,
because a reduction chosen in the artifact writer is a reduction chosen with the numbers already
visible."* A rule written into the module that measures the cost deciding it is a rule chosen with
that cost visible. So the rules sit HERE, and the drivers IMPORT them.

**WHY EDIT-ONCE, AND WHY THE CONSEQUENCE IS SEVERE.**

`tests/test_phase23_prereg.py::test_the_prereg_rule_precedes_every_phase23_result` requires every
commit touching this file to be a STRICT ANCESTOR of every `results/phase23_*` artifact's EARLIEST
add. From 23-04's commit onward — the first Phase-23 artifact — **any edit to this file turns that
guard permanently RED, with no recovery path.** The guard takes `adds[-1]`, the EARLIEST add, so a
delete-and-re-add cycle cannot launder it. This is the same mechanism that closed
`scripts/mitigation_gate.py`, applied here deliberately.

Therefore this module declares **every artifact path the whole phase will write** and carries
**every blind rule the phase will consume**, ahead of need. A later plan that finds itself wanting
a new constant or a new rule must DERIVE it from what is here rather than add one. A correction
goes through `scripts/_addendum.py`'s register — a dated additive continuation published ELSEWHERE,
never an edit to this file.

**THE PREFIX IS LOAD-BEARING.** Everything Phase 23 writes under `results/` uses the
`results/phase23_` prefix, because anything outside it falls outside the ancestry guard at
`tests/test_phase20_prereg.py:332` **entirely** — invisible, not merely unwatched. This module is
the SINGLE SOURCE of every one of those paths, in the register `teach_persona.fact_bin_path`
already uses for the same reason: this repository has shipped plans naming artifact paths the code
refuses, so every later Phase-23 plan resolves its paths from HERE rather than from a string
literal at a call site.

**`CAL03_WIRING_RECORD` IS DELIBERATELY NOT UNDER `NOISED_RECORD_GLOB`.** CAL-03's probe exports no
adapter, scores no question and runs a toy `ModelConfig` under `max_steps_override`. It is a WIRING
probe, not a sweep point, so it sits outside the glob that DPSGD-06's ordering guard binds on — and
its own record declares `sweep_point: false` to say so. That declaration is what exempts it;
membership of the noised glob is a consequence of what a record says about ITSELF, and saying
nothing is not a declaration.

Wave-1 discipline: this module imports stdlib ONLY and must never import `scripts/phase23_cost.py`
(wave 2) or `scripts/phase23_run.py` (wave 3). Every rule below is arithmetic over values its
caller passes in.

CPU-only, GPU-free, no torch, no network.
"""

import math


def _prove(condition, message):
    """``SystemExit`` on a broken invariant — ``scripts/_addendum.py:50-54``'s register.

    Never ``assert``. ``python -O`` strips ``assert`` outright, and this module is almost entirely
    refusals: under ``-O`` a bare-``assert`` implementation would admit every case it exists to
    reject, silently. 18 modules under ``scripts/`` use this register and none use ``assert``.
    """
    if not condition:
        raise SystemExit(f"[phase23_prereg] {message}")


# =================================================================================================
# ===== (a) THE CANONICAL PHASE-23 ARTIFACT REGISTER =====
#
# Every path Phase 23 will write, declared here ahead of need because this file is EDIT-ONCE (see
# the module docstring). Each carries the plan that writes it and the consumer that reads it.
# =================================================================================================

# CAL-03's wiring probe (23-04). NOT a sweep point: declares `sweep_point: false` in its payload.
CAL03_WIRING_RECORD = "results/phase23_cal03_wiring.json"

# D-03's control readings and the REDUCED floor (23-08). Its first git add must strictly PRECEDE
# SIGMA_ZERO_RECORD's — that ordering is what structurally guarantees the floor cannot be tuned
# after seeing σ=0's number, rather than a promise not to tune it.
CONTROL_FLOOR_RECORD = "results/phase23_control_floor.json"

# CTRL-03's ONE scheduling (23-08): the arms, the seeds, the exported adapters. Training only.
NEVER_TAUGHT_TRAINING_RECORD = "results/phase23_never_taught_training.json"

# CTRL-03's SCORED extraction floor (23-14) — the record `mitigation_gate.extraction_ceiling`
# consumes in Phase 25, and whose provenance that FROZEN function `_prove`s.
NEVER_TAUGHT_RECORD = "results/phase23_never_taught.json"

# DPSGD-06 (23-10). σ=0 is the DP arm's FIRST executed run: no record under NOISED_RECORD_GLOB may
# precede it in git.
SIGMA_ZERO_RECORD = "results/phase23_sigma_zero.json"

# CAL-01 / CAL-05 (23-11): the measured per-point cost bracket.
COST_RECORD = "results/phase23_cost.json"

# Every executed SWEEP POINT at σ > 0. `noised_record_path` below is the ONLY sanctioned way to
# produce a member; the glob is what `test_sigma_zero_precedes_every_noised_point` binds on.
NOISED_RECORD_PREFIX = "results/phase23_noised_"
NOISED_RECORD_GLOB = NOISED_RECORD_PREFIX + "*"


def noised_record_path(arm, sigma):
    """One noised sweep point's record path, DERIVED — never a string literal at a call site.

    ``("dp_n64", 0.5)`` -> ``results/phase23_noised_dp_n64_sigma0p500000.json``. Same register as
    ``teach_persona.fact_bin_path``, for the same recorded reason: this repository has shipped
    plans naming paths the code refuses, and one derivation function is the cheapest fix.

    σ is rendered at six decimal places with the point written ``p`` (a filesystem-safe form), and
    the rendering is REFUSED unless it round-trips — ``float(rendered) == float(sigma)``. Two
    sigmas that differ below the sixth decimal would otherwise collide on one filename and the
    second run would silently overwrite the first, which is a lost measurement rather than a
    visible error.
    """
    _prove(
        isinstance(arm, str) and bool(arm) and arm.replace("-", "").replace("_", "").isalnum(),
        f"arm {arm!r} is not a non-empty alphanumeric/-/_ name. A path separator or a `..` here "
        "would place a sweep point outside `results/`, where every Phase-23 ancestry guard is "
        "blind to it",
    )
    _prove(
        isinstance(sigma, (int, float))
        and not isinstance(sigma, bool)
        and math.isfinite(sigma)
        and sigma > 0,
        f"sigma {sigma!r} is not a finite positive number. This path names a NOISED sweep point; "
        f"σ=0 has its own record at {SIGMA_ZERO_RECORD} and must not be filed under the noised "
        "glob it is required to precede",
    )
    rendered = f"{float(sigma):.6f}"
    _prove(
        float(rendered) == float(sigma),
        f"sigma {sigma!r} does not round-trip through its 6-decimal rendering {rendered!r}. Two "
        "sweep points whose sigmas differ below that precision would collide on ONE filename and "
        "the second would silently overwrite the first",
    )
    return f"{NOISED_RECORD_PREFIX}{arm}_sigma{rendered.replace('.', 'p')}.json"


# =================================================================================================
# ===== (b) THE BLIND REDUCTION (D-03) =====
# =================================================================================================


def noise_floor(readings):
    """D-03's seed-to-seed noise floor: the RANGE ``max(readings) - min(readings)``.

    **Committed BLIND — before any control reading exists.** That is the whole point of this
    function's placement, and `scripts/phase19_floor.py`'s property 2 is the reasoning: a reduction
    chosen once the numbers are visible is a reduction chosen with the numbers visible, regardless
    of intent. `tests/test_phase23_prereg.py::test_the_prereg_rule_precedes_every_phase23_result`
    turns "blind" into a property of git's object graph rather than a claim in a paragraph.

    **WHY THE RANGE AND NOT A STANDARD DEVIATION**, pinned here so the choice cannot be revisited
    later with a number in hand. The consumer asks one question — *could this difference have come
    from seed variation alone?* — and at N in {3, 4, 5} a stdev is badly estimated while a range is
    the conservative answer to exactly that question. It is a SPREAD, not a dispersion estimate,
    and it is deliberately the larger of the two: a floor that is too tight halts a correct sweep,
    a floor that is too loose admits a broken one, and only the second is unrecoverable. This
    matches the two floors already in the tree.

    Refuses fewer than two readings, in `mitigation_gate.EXTRACTION_FLOOR_MIN_SEEDS`'s own words: a
    single-seed floor is NOT a noise floor, it is ONE DRAW. Refuses a non-finite reading, because
    `max - min` over a NaN returns a NaN that then compares False against everything and would
    turn D-04's halt into a silent pass.
    """
    readings = tuple(readings)
    _prove(
        len(readings) >= 2,
        f"noise_floor got {len(readings)} reading(s): {readings!r}. A single-seed floor is NOT a "
        "noise floor, it is ONE DRAW — there is no second reading for it to vary against, so it "
        "measures nothing about run-to-run variance and every margin built on it is a margin over "
        "an unknown. This is `mitigation_gate.EXTRACTION_FLOOR_MIN_SEEDS`'s refusal, restated for "
        "the reduction that produces the number that guard checks",
    )
    for index, reading in enumerate(readings):
        _prove(
            isinstance(reading, (int, float))
            and not isinstance(reading, bool)
            and math.isfinite(reading),
            f"reading[{index}] is {reading!r}, which is not a finite number. `max - min` over a "
            "non-finite reading returns a non-finite floor, and a NaN floor compares False against "
            "every deviation — which would turn D-04's HALT into a silent pass in exactly the "
            "case a halt is most needed",
        )
    return max(readings) - min(readings)


# =================================================================================================
# ===== (c) THE D-04 HALT VERDICT =====
# =================================================================================================

# The keys a floor's provenance must carry before it may reach a verdict. `results/
# phase19_noise_floors.json` is the committed record shape these come from; `record`/`record_sha256`
# identify WHICH artifact, `git_sha`/`device`/`torch_version` identify the run that produced it,
# `seeds`/`reduction` identify HOW, and `governs` identifies what it is allowed to judge.
FLOOR_PROVENANCE_KEYS = (
    "record",
    "record_sha256",
    "git_sha",
    "device",
    "torch_version",
    "seeds",
    "reduction",
    "governs",
)


def sigma_zero_verdict(*, control_readings, sigma_zero_reading, floor, floor_provenance):
    """D-04: ``"proceed"`` if σ=0 sits inside the floor, otherwise the sweep HALTS. No third option.

    **THERE IS NO WARNING BRANCH AND NO OVERRIDE FLAG**, and D-04 commits to that here, before any
    number exists. A flag that downgrades a halt becomes routine, and an operator who routinely
    passes it eventually passes it on the run that mattered. The only outcomes are the string
    ``"proceed"`` and a ``SystemExit``.

    THE CENTRAL READING IS PINNED: ``control_readings[0]`` — the reading at the FIRST seed in the
    recorded seed order. It is a choice with no post-hoc freedom, unlike a mean over the very
    readings the floor was reduced from (which would let the floor and the centre move together).

    Three refusals, all BEFORE the comparison:

      1. ``floor_provenance`` must be a mapping carrying every key in ``FLOOR_PROVENANCE_KEYS``. A
         record missing any of them is REFUSED, never defaulted — an unlabelled number is
         indistinguishable from a borrowed one, which is `mitigation_gate`'s D-14(a) reasoning.
      2. ``floor == noise_floor(control_readings)`` under exact ``==``, so the floor passed in must
         re-derive from the readings passed in. A hand-edited number cannot reach the verdict, and
         a one-ULP nudge is refused BY CONSTRUCTION rather than by magnitude — the defect class
         Phase 20 closed at GATE-02, closed here by requiring identity to the reduction's output.
      3. ``sigma_zero_reading`` must be finite. A NaN compares False against the floor and would
         reach the halt with an uninterpretable message.

    **THE ASYMMETRY THAT MOTIVATES THE HALT.** Every correctness bug in this class *improves*
    utility, so a σ=0 that BEATS the control is as much a signal as one that misses it — both
    directions breach. Stop-and-fix is reversible; publish-compromised is not.
    """
    has_keys = hasattr(floor_provenance, "keys")
    missing = (
        [key for key in FLOOR_PROVENANCE_KEYS if key not in floor_provenance] if has_keys else []
    )
    _prove(
        has_keys and not missing,
        f"the σ=0 floor arrived with provenance {floor_provenance!r}, which is not a mapping "
        f"carrying every key in {FLOOR_PROVENANCE_KEYS}. MISSING: {missing or 'not a mapping'}. A "
        "floor whose artifact, commit, device, seeds or reduction is unstated is REFUSED and never "
        "defaulted: an unlabelled number is indistinguishable from a borrowed one, and D-04 "
        "commits that obligation as CODE because a prose note gets missed",
    )

    re_derived = noise_floor(control_readings)
    _prove(
        floor == re_derived,
        f"the floor passed in is {floor!r} but noise_floor(control_readings) re-derives "
        f"{re_derived!r}. The floor must be EXACTLY the reduction's output on the readings it is "
        "judged against, so a hand-edited number — including a one-ULP nudge, the defect Phase 20 "
        "closed at GATE-02 — cannot reach this verdict at all",
    )
    _prove(
        isinstance(sigma_zero_reading, (int, float))
        and not isinstance(sigma_zero_reading, bool)
        and math.isfinite(sigma_zero_reading),
        f"the σ=0 reading is {sigma_zero_reading!r}, which is not a finite number. A non-finite "
        "reading compares False against the floor and would reach the halt below carrying a "
        "message nobody can act on",
    )

    central = control_readings[0]
    deviation = abs(sigma_zero_reading - central)
    if deviation <= floor:
        return "proceed"

    direction = "BEATS" if sigma_zero_reading > central else "misses"
    raise SystemExit(
        f"[phase23_prereg] D-04 HALT — THE SWEEP IS HALTED: zero noised points will run.\n"
        f"  σ=0 reading      : {sigma_zero_reading!r} ({direction} the control)\n"
        f"  control central  : {central!r} (reading at the FIRST recorded seed)\n"
        f"  deviation        : {deviation!r}\n"
        f"  noise floor      : {floor!r}\n"
        f"  floor record     : {floor_provenance['record']}\n"
        "  σ=0 must reproduce the unmitigated control inside the seed-to-seed floor. It does not. "
        "The cause must be ROOT-CAUSED AND FIXED before any noised point runs — this is not a "
        "warning and there is no override flag. Every correctness bug in this class IMPROVES "
        f"utility, which is why a σ=0 that {direction} the control is the signal rather than "
        "noise. Stop-and-fix is reversible; publish-compromised is not."
    )


# =================================================================================================
# ===== (d) THE CAL-03 WITHDRAWAL RULE (D-06) =====
# =================================================================================================


def n64_leg_is_committable(*, epsilon_n8, epsilon_n64, t_n8, t_n64):
    """D-06: ``True`` only when ε and T are BIT-IDENTICAL between n=8 and n=64 at fixed σ.

    **NEVER A RELATIVE TOLERANCE**, and this is committed before CAL-03 runs so it cannot be
    loosened once a near-miss is on screen. `epsilon_for(sigma, steps, delta)` takes no N
    parameter — ε is independent of N BY CONSTRUCTION of the accountant — so this run cannot test
    the math. It tests the WIRING: whether N leaks into T. The two arms are therefore the SAME call
    shape at fixed σ, not two independent mathematics, and any tolerance would admit exactly the
    leak the check exists to catch. Phase 22 rejected this same reasoning once already in DPSGD-05,
    citing `lora/inject.py:113-118`: *"a tolerance would only weaken this."*

    THE T ASSERTION ADDS NO DETECTION POWER and is here anyway. ε is monotone in T at fixed σ, so ε
    equality already implies T equality; what T buys is naming WHERE a leak lives when one fires,
    instead of only that one exists.

    **SCOPE, which is what separates this from D-04's halt.** Falsified withdraws the **n=64 leg
    only**, with the measurement that withdrew it recorded. **The n=8 leg stays intact and
    publishable**, its ε correct regardless of the leak: a data-path wiring bug does not indict the
    DP mechanism itself. D-04 halts everything because a σ=0 breach indicts the mechanism; this
    does not, so the milestone ships a single-capacity frontier rather than stopping.
    """
    return epsilon_n8 == epsilon_n64 and t_n8 == t_n64


# =================================================================================================
# ===== (e) THE SEED-COUNT RULE (D-03's N) =====
# =================================================================================================

# THE PER-SWEEP-POINT COST UNIT THIS MILESTONE ALREADY ACCEPTS, in seconds.
#
# DERIVATION — `23-RESEARCH.md` §R3.0, the "Reproduction of 4.77 h/point" block, which reproduces
# `results/phase18_preflight_report.md`'s own rows:
#
#     PER ARM 42480 draws, 286.26 min = 4.7710 h
#     286.26 min x 60 = 17,175.6 s  ->  17_175
#
# `.planning/REQUIREMENTS.md`'s per-point table (K = 48 -> 4.77 h/point) is the ROUNDED RESTATEMENT
# of that same figure and is NOT the source: 4.77 h x 3600 = 17,172 s, three seconds off this
# constant. The unrounded block is the derivation; the REQUIREMENTS row is the restatement. This
# phase's companion guard is literally `test_budget_constants_re_derive`, so a pinned constant
# whose stated provenance does not re-derive it would be that same defect in miniature.
#
# AND THE TABLE IS A FLOOR, NOT A MEAN (CAL-05): the rate was measured on the un-adapted base,
# where 45-56 of 64 draws per shape terminated on a stop id. A heavily-noised adapter that stops
# emitting EOS runs the full `max_new_tokens=48` every draw — the slowest case. So the bound
# `choose_n_seeds` enforces is a FLOOR-VALUED bound and an overrun against it is not a surprise.
#
# DO NOT CONFUSE THIS WITH the `h_per_point_floor` / `h_per_point_ceiling` keys 23-05 defines and
# 23-11 measures. Those are this phase's OWN re-measurement of per-point cost. This constant is the
# PRE-EXISTING budget unit the milestone already accepted, frozen here so a wave-1 rule can be
# committed without depending on a wave-6 measurement. The names are close enough that a later
# reader will otherwise assume one of them is stale; neither is.
H_PER_POINT_FLOOR_SECONDS = 17_175

# D-03 locks N to 3-5. Ordered largest-first: the rule takes the most seeds the bound affords.
_SEED_LADDER = (5, 4, 3)


def choose_n_seeds(seconds_per_seed):
    """D-03's N: the LARGEST N in ``(5, 4, 3)`` whose ``N * seconds_per_seed`` fits the bound.

    **N IS NEVER BELOW 3.** D-03 locks the range at 3-5, so when even ``3 * seconds_per_seed``
    exceeds ``H_PER_POINT_FLOOR_SECONDS`` this returns ``3`` and the CALLER records the overrun.
    That is not a bug and it is stated here so nobody later reads the floor of 3 as one: the range
    is the pre-registered commitment and the bound is a budget, so a budget miss is a fact to
    publish rather than a licence to break the range.

    **WHY THIS RULE LANDS HERE AND NOT IN THE DRIVER THAT MEASURES THE COST IT CONSUMES.** N fixes
    three downstream things at once — D-03's reading count, whether D-08's
    `mitigation_gate.EXTRACTION_FLOOR_MIN_SEEDS` is satisfied by construction, and the
    `N_CONTROL_SEEDS` term 23-13 prices into Z. The driver that costs the scoring leg is
    **not** edit-once: 23-08's own Tasks 2 and 3 re-edit it, and so do 23-10, 23-11 and 23-14. A
    rule living there would have NO ancestry guard able to bind its commit to the measurement it
    decides — `git log -1` on that file returns its most recent commit and would test nothing at
    all. This module IS edit-once from 23-04's first artifact, so
    `test_the_prereg_rule_precedes_every_phase23_result` binds this rule blind by exactly the same
    mechanism that binds `noise_floor`. `scripts/phase19_floor.py`'s property 2, one more time.
    23-08 is the caller: it IMPORTS this function and defines no local copy.

    It imports nothing and touches no artifact — it is arithmetic over one float, which is what
    lets a rule this consequential live in a wave-1 module that must not depend on wave 2's cost
    measurement.
    """
    _prove(
        isinstance(seconds_per_seed, (int, float))
        and not isinstance(seconds_per_seed, bool)
        and math.isfinite(seconds_per_seed)
        and seconds_per_seed > 0,
        f"seconds_per_seed is {seconds_per_seed!r}, which is not a finite positive number. A zero "
        f"or negative cost would return {_SEED_LADDER[0]} for a reason that has nothing to do with "
        "cost, and a non-finite one would compare False against the bound and return the floor of "
        f"{_SEED_LADDER[-1]} for the same non-reason",
    )
    for n in _SEED_LADDER:
        if n * seconds_per_seed <= H_PER_POINT_FLOOR_SECONDS:
            return n
    return _SEED_LADDER[-1]


# =================================================================================================
# ===== (f) THE SELF-CHECK — the rules as RUNNABLE EVIDENCE, not merely importable code =====
# =================================================================================================

if __name__ == "__main__":  # pragma: no cover - self-check, not a test suite
    # `scripts/mitigation_gate.py`'s register, with `_prove` in place of `assert` for the same
    # reason the rest of this file uses it: `python -O` strips `assert` and would make this
    # self-check print four lines and verify nothing.

    _READINGS = (0.40, 0.44, 0.42)
    _FLOOR = noise_floor(_READINGS)
    _PROVENANCE = {
        "record": CONTROL_FLOOR_RECORD,
        "record_sha256": "0" * 64,
        "git_sha": "0" * 40,
        "device": "mps",
        "torch_version": "2.7.1",
        "seeds": (1337, 1338, 1339),
        "reduction": "range",
        "governs": SIGMA_ZERO_RECORD,
        # SYNTHETIC THROUGHOUT and labelled so: no Phase-23 arm exists yet — this module is
        # committed while `git ls-files 'results/phase23_*'` is still empty, which is the point.
    }

    _verdict = sigma_zero_verdict(
        control_readings=_READINGS,
        sigma_zero_reading=_READINGS[0] + _FLOOR,  # exactly ON the floor — the inclusive edge
        floor=_FLOOR,
        floor_provenance=_PROVENANCE,
    )
    _prove(_verdict == "proceed", f"the in-floor case returned {_verdict!r}, not 'proceed'")
    print(f"[phase23_prereg] 1/4 {_verdict} — σ=0 exactly on the floor {_FLOOR!r} is admitted")

    # The BREACH, in the direction most likely to be forgotten: σ=0 BEATS the control. Every
    # correctness bug in this class improves utility, so this is the direction a real one produces.
    try:
        sigma_zero_verdict(
            control_readings=_READINGS,
            sigma_zero_reading=_READINGS[0] + _FLOOR * 10,
            floor=_FLOOR,
            floor_provenance=_PROVENANCE,
        )
    except SystemExit as halt:
        _halt = str(halt)
    else:
        raise SystemExit("[phase23_prereg] the breach case did NOT halt — D-04 has no other branch")
    _prove("HALT" in _halt, f"the halt message does not say HALT: {_halt!r}")
    _prove("zero noised points" in _halt, f"the halt message omits the scope: {_halt!r}")
    _prove(CONTROL_FLOOR_RECORD in _halt, f"the halt message omits the record: {_halt!r}")
    print(f"[phase23_prereg] 2/4 HALT — observed firing:\n{_halt}")

    _CHEAP = H_PER_POINT_FLOOR_SECONDS / 5.0
    _N_CHEAP = choose_n_seeds(_CHEAP)
    _prove(_N_CHEAP == 5, f"a cost of {_CHEAP!r}s/seed returned N={_N_CHEAP}, not 5")
    print(
        f"[phase23_prereg] 3/4 N={_N_CHEAP} — {_CHEAP!r}s/seed, "
        f"{_N_CHEAP * _CHEAP!r}s <= {H_PER_POINT_FLOOR_SECONDS}s"
    )

    _DEAR = H_PER_POINT_FLOOR_SECONDS * 2.0
    _N_DEAR = choose_n_seeds(_DEAR)
    _prove(_N_DEAR == 3, f"an unaffordable cost returned N={_N_DEAR}, not the D-03 floor of 3")
    print(
        f"[phase23_prereg] 4/4 N={_N_DEAR} — {_DEAR!r}s/seed OVERRUNS the bound "
        f"({_N_DEAR * _DEAR!r}s > {H_PER_POINT_FLOOR_SECONDS}s); D-03's floor of 3 outranks it and "
        "the CALLER records the overrun"
    )
