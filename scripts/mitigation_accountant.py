"""PRE-REGISTERED (epsilon, delta) ACCOUNTING RULE for the v4.0 DP arm — form, rejection, adjacency.

Committed BEFORE any ``results/phase23_*`` number exists, which puts it a WHOLE PHASE ahead of the
first epsilon-bearing artifact. ``scripts/mitigation_gate.py`` earned its authority exactly this
way and ``scripts/mitigation_unit.py`` continued the discipline for a second subject; this module
is the third in that line. The gate states what a swept point must ACHIEVE, the unit states what
the thing being protected IS, and this states WHICH CLOSED FORM turns a mechanism into a published
epsilon, WHICH ONE was refused and why, and under WHICH ADJACENCY RELATION the sensitivity behind
that epsilon is defined. Four statements, none of which a re-run can correct after the fact.

WHY THE PIN IS AN OUTPUT TABLE RATHER THAN A FORMULA (D-09), AND WHY THE RISK IS NOT THE OBVIOUS
ONE
===============================================================================================
Measured before it was chosen, rather than assumed: EPSILON IS NOT AN INPUT TO THE GATE.
``mitigation_gate.mitigation_point_verdict`` takes no epsilon among its keyword arguments, so a
re-derived accountant CANNOT move a point from FAIL to PASS. Epsilon reaches exactly ONE branch —
``mitigation_gate.capacity_comparison``'s D-26 fallback route, where an epsilon gap is compared
against a fallback tolerance — and that route is reached only if CAL-03 FALSIFIES "epsilon is
independent of N at q = 1". On the primary route the equivalence asked for is agreement on
``mitigation_gate.MECHANISM_KEYS`` with ZERO tolerance, and epsilon is never compared numerically
at all.

So the accurate exposure is: a changed accountant moves the PUBLISHED EPSILON LABEL on every swept
point — the headline claim's own units — plus one conditional route. Publication integrity plus one
live path, not verdict-flipping. Because what is at risk is epsilon's VALUE rather than a threshold
comparison, the pin that bites is an OUTPUT TABLE, and that is also the only shape that fits inside
the zero-import ceiling described below.

CLOSED AT THE FIRST ARTIFACT, AND THE CLOSURE IS MECHANICAL
===========================================================
The moment any ``results/phase23_*`` artifact is committed, this file is CLOSED. A correction after
that point is a DATED CONTINUATION via ``scripts/_addendum.py``, never an edit.
``tests/test_phase20_prereg.py::test_phase22_prereg_is_frozen_before_every_phase23_result``
requires EVERY commit touching this file to be an ancestor of every ``results/phase23_*``
artifact's first add — its pre-registration side is ``git log`` over the pin, i.e. every commit and
not merely the first, so a LATER edit is caught rather than only a wrong initial ordering. A
``git rm`` plus a re-add at the same path CANNOT launder it: the guard takes the EARLIEST add, so
the original ordering survives the deletion. There is no recovery path and no force flag.

That the prefix actually MATCHES is a test result rather than a reading:
``tests/test_phase20_prereg.py::test_phase23_glob_sees_the_phase23_prefix_red_then_green`` drives a
``results/phase23_*`` path through five states in a throwaway repository and observes the guard go
RED and then GREEN, because the live ordering test is vacuous by construction until Phase 23 lands
its first artifact.

WHY THIS MODULE IMPORTS NOTHING, AND WHERE THE COMPUTATION LIVES (D-10)
----------------------------------------------------------------------
Being named ``mitigation_*.py`` joins ``tests/test_phase20_prereg.py``'s ``_GATE_MODULES`` glob,
and that glob carries a HARD IMPORT CEILING: an ``imported`` set ACCUMULATES across EVERY module in
the glob and is asserted a SUBSET of ``{"pathlib", "sys", "erasure_gate"}`` by
``tests/test_phase20_prereg.py::test_mitigation_gate_import_graph_is_stdlib_and_erasure_gate_only``.
``math`` is not in that set, and the ``from erasure_gate import`` list is asserted by EXACT equality
to five names, so no ``erf`` arrives by that route either. ONE ``import math`` anywhere in this file
turns that test RED.

``sqrt`` is reachable as ``x ** 0.5``, which is an operator. **``exp`` and ``erfc`` are reachable by
NO operator**, and hand-rolling a series for ``exp`` inside a file that can never be edited again is
strictly worse than the problem it would solve. That is D-10's forcing mechanism, and it is why the
COMPUTATION half lives at ``src/personacore/privacy/accountant.py`` (stdlib ``math`` only) while
this file holds the RULE and the OUTPUTS. It mirrors the repo's own gate/budget and unit/record
splits — the rule in one place, its emission in another — and it is what makes freezing this file
cheap.

WIDENING THE ALLOW-SET WAS REJECTED, on Phase 21 D-22's own words. That subset assertion's stated
purpose is that it "catches the one nobody anticipated"; the first thing it would ever have caught
would be us. A ceiling relaxed by the phase it first constrains is not a ceiling.

WHY ``_prove`` IS DEFINED HERE RATHER THAN IMPORTED FROM ``mitigation_gate``
---------------------------------------------------------------------------
``scripts/mitigation_gate.py`` already defines this exact three-line helper, and this project's
standing discipline is "import the instrument, never copy it". That discipline is OVERRIDDEN here
by the ceiling above, not forgotten: importing a sibling would add ``mitigation_gate`` to the
accumulated ``imported`` set and turn
``tests/test_phase20_prereg.py::test_mitigation_gate_import_graph_is_stdlib_and_erasure_gate_only``
RED. The local definition is a FORCED CONSEQUENCE of that ceiling, recorded so a reader does not
mistake it for a copied instrument nobody noticed. ``_prove`` is a control-flow shape rather than an
estimator, so the failure mode the import-never-copy rule exists to prevent — two copies of a bound
silently diverging — has no analogue here.

WHY EVERY CITATION BELOW NAMES A SYMBOL AND NEVER A LINE NUMBER
--------------------------------------------------------------
``scripts/mitigation_unit.py`` cites eight test-file line numbers and FOUR of them are now stale.
That file is FROZEN — two ``results/phase21_*`` artifacts are tracked — so those anchors cannot be
corrected except by a dated continuation, and they will point at the wrong lines for as long as the
repository exists. This file copies that file's STRUCTURE and deliberately not its habit: every
reference below is ``module.SYMBOL`` or ``tests/path.py::test_name``, which survives any edit to the
file being cited. A line number written into something that can never be edited is a citation with
an expiry date and no way to renew it.

WHAT IS DELIBERATELY ABSENT
---------------------------
NO operating sigma, NO clip norm ``C``, NO chosen epsilon target, and NO runnable rejected formula.

``GOLDEN_EPSILON``'s sigma and steps columns are ARITHMETIC TEST VECTORS FOR THE ACCOUNTANT'S OWN
CORRECTNESS (D-09), NOT A BUDGET. They exist so that
``src/personacore/privacy/accountant.py::epsilon_for`` can be checked against outputs derived
independently of it; they are not a proposal about what the v4.0 sweep should run. The sweep's
sigma and C are PHASE 23 RESOURCE PARAMETERS and they live in ``scripts/mitigation_budget.py``,
which is Phase 20's gate/budget boundary — an outcome threshold measured beforehand and a resource
budget measured beforehand are different things, and a reader must not be able to mistake one for
the other. NOTHING HERE PRE-EMPTS THEM. Reading a row of this table as "the sigma we will use"
would be reading a unit test as a plan.

The rejected form is a STRING and a REASON, never a function. ``scripts/mitigation_unit.py`` ships
its rejected recipe runnable, and copying that half here by pattern-match is the specific mistake
D-09 forbids: the rejected form's logic must be NAMED, not TRANSCRIBED. ``log`` is unreachable under
the ceiling anyway, so the two constraints agree.

CPU-only: zero imports, zero I/O, zero network.
"""


def _prove(condition, message):
    """``SystemExit`` on a broken invariant — ``scripts/mitigation_gate.py``'s register.

    ``SystemExit`` and deliberately NOT ``assert``: an ``assert`` is strippable under ``-O``, and a
    proof that disappears under an optimisation flag is not a proof. The message carries this
    module's own name in brackets — an abort naming the wrong module sends its reader to the wrong
    file.

    COPIED from ``scripts/mitigation_gate.py`` and ``scripts/mitigation_unit.py`` rather than
    imported, and the standing "import the instrument, never copy it" rule is OVERRIDDEN rather
    than forgotten: an import of either sibling would enter the accumulated ``imported`` set that
    ``tests/test_phase20_prereg.py::test_mitigation_gate_import_graph_is_stdlib_and_erasure_gate_only``
    asserts is a subset of three names, and turn it RED. This helper is a control-flow shape, not an
    estimator, so the divergence risk that rule exists to prevent does not apply to it.
    """
    if not condition:
        raise SystemExit(f"[mitigation_accountant] {message}")


# ---------------------------------------------------------------------------------------------
# 1. THE REQUIRED FORM. Named, never implemented — the implementation is D-10's half.
# ---------------------------------------------------------------------------------------------
REQUIRED_FORM = (
    "delta(eps, mu) = Phi(mu/2 - eps/mu) - exp(eps) * Phi(-mu/2 - eps/mu), with mu = Delta/sigma; "
    "epsilon_for(sigma, T, delta) is the infimum over eps >= 0 satisfying delta(eps, mu_eff) <= "
    "delta at mu_eff = mu * T ** 0.5. THE ANALYTIC GAUSSIAN MECHANISM: Balle and Wang, "
    "'Improving the Gaussian Mechanism for Differential Privacy: Analytical Calibration and "
    "Optimal Denoising' (ICML 2018, arXiv 1805.06530), THEOREM 8, stated there as an IF AND ONLY "
    "IF rather than as a sufficient condition — so there is no slack left to tighten. "
    "INDEPENDENTLY CONFIRMED by Dong, Roth and Su, 'Gaussian Differential Privacy' "
    "(arXiv 1905.02383), COROLLARY 2.13, which reaches the identical expression from "
    "trade-off functions / f-DP, a completely different starting point. Two derivations, one "
    "closed form. "
    "\n\n"
    "T-FOLD COMPOSITION is Dong, Roth and Su COROLLARY 3.3: the n-fold composition of mu_i-GDP "
    "mechanisms is sqrt(sum of mu_i squared)-GDP, which in the homogeneous case is "
    "mu_eff = mu * T ** 0.5. That corollary is an EXACT EQUALITY OF TRADE-OFF FUNCTIONS, not an "
    "upper bound, and their section 3 explicitly permits each mechanism to depend on the outputs "
    "of the ones before it — so it COVERS ADAPTIVE COMPOSITION, which DP-SGD requires because "
    "step t's gradient depends on step t-1's weights. Adaptivity therefore costs nothing here, "
    "and that is the non-obvious half a reader is likely to assume the other way. "
    "\n\n"
    "THIS MODULE NAMES THE FORM AND DOES NOT IMPLEMENT IT. The executable version is "
    "`src/personacore/privacy/accountant.py`, which needs `erfc` and `exp` — neither reachable by "
    "any operator, and therefore neither reachable under this file's import ceiling."
)

REQUIRED_FORM_CONDITIONS = (
    "1. q = 1, NO SUBSAMPLING. With q < 1 the subsampled Gaussian's trade-off function is not "
    "Gaussian at all, the composition identity fails, and RDP or PLD accounting with a CLT "
    "approximation would be required instead. Pinned by "
    "`scripts/mitigation_unit.py::SAMPLING_RATE_Q`, which is 1.0 because fact-aligned accumulation "
    "puts every fact in every lot exactly once by construction.",
    "2. HOMOGENEOUS sigma AND Delta ACROSS ALL T STEPS. The general form is sqrt(sum of mu_i "
    "squared); it collapses to mu * T ** 0.5 only if every step is identical. A mid-run sigma "
    "change SILENTLY invalidates the identity — nothing raises, the published number is simply "
    "wrong. Stated in no other committed artifact, which is why it is here.",
    "3. T FIXED IN ADVANCE, NOT A DATA-DEPENDENT STOPPING TIME. Early-stopping on a validation "
    "metric makes T itself a function of the private data and the composition theorem no longer "
    "applies to it. Implied by a constant step budget; stated as a precondition nowhere else.",
    "4. ADAPTIVITY IS PERMITTED AT NO COST. Dong, Roth and Su Corollary 3.3 covers mechanisms "
    "whose inputs depend on earlier outputs, so DP-SGD's step-to-step dependence buys no penalty. "
    "Recorded because it is the condition a reader is most likely to assume runs the other way, "
    "and an unnecessary penalty applied out of caution is still a wrong published number.",
    "5. Delta IS THE PER-STEP L2 SENSITIVITY UNDER A FIXED ADJACENCY RELATION, and "
    "mu = Delta/sigma uses that SAME Delta. This is the condition that had never landed in code "
    "anywhere in this repository before this pin; see NEIGHBOURING below.",
)


# ---------------------------------------------------------------------------------------------
# 2. THE REJECTED FORM. A STRING and a REASON — deliberately NOT a runnable function (D-09).
# ---------------------------------------------------------------------------------------------
REJECTED_FORM = "sqrt(2*ln(1.25/delta))/sigma"

REJECTED_FORM_REASON = (
    "THE CLASSICAL GAUSSIAN MECHANISM, INVERTED. It is Dwork and Roth 2014, 'The Algorithmic "
    "Foundations of Differential Privacy', THEOREM A.1 — restated as Balle and Wang's own "
    "THEOREM 1 — solved for epsilon instead of for sigma. It is rejected on a TWO-PART reason, "
    "and both parts are stated because either alone would be the weaker rejection. "
    "\n\n"
    "(i) FORMALLY: `eps in (0, 1)` IS IN THE THEOREM'S HYPOTHESIS, not an editorial caveat. Balle "
    "and Wang's section on limitations in the low-privacy regime says the classical rate 'cannot "
    "be extended beyond the interval eps in (0, 1)', and their Theorem 4 proves a lower bound the "
    "classical rate violates asymptotically. At the frozen delta the classical epsilon is "
    "4.844805262605389/sigma, so EVERY sigma below 4.844805262605389 produces eps > 1 and invokes "
    "the theorem OUTSIDE ITS OWN HYPOTHESIS. Note what that boundary means in practice: the whole "
    "usable operating range of this project sits below it, so this is not an edge case reached by "
    "an extreme parameter. The resulting claim is UNSUPPORTED, independently of whether it happens "
    "to come out numerically conservative. "
    "\n\n"
    "(ii) NUMERICALLY: past mu = 1.737896746 (sigma = 0.575408178, located by 60-iteration "
    "bisection at the frozen delta) it is not merely unsupported but WRONG IN THE UNSAFE "
    "DIRECTION — it reports an epsilon SMALLER than the mechanism earns. Measured at sigma = 0.3: "
    "the classical epsilon is 16.149351 while the exact one is 19.130768, and the TRUE delta at "
    "the classical epsilon is 3.572e-4, which is 35.7x the promised delta. A formula that "
    "over-claims privacy by 35.7x is not a loose bound. "
    "\n\n"
    "THIS IS A STRICTLY STRONGER REJECTION THAN 'IT IS LOOSE', and the distinction is the whole "
    "reason the reason is recorded rather than the verdict. A loose bound published as a "
    "guarantee is honest and wasteful; a bound that under-reports epsilon past a measurable "
    "crossover is a privacy claim that is false in the direction that matters. "
    "`.planning/research/PITFALLS.md`'s standing rule — a hand-rolled accountant failing toward a "
    "SMALLER epsilon is unsound — is exactly what the crossover above measures. "
    "\n\n"
    "IT IS RECORDED AS A STRING AND A REASON, NEVER AS A RUNNABLE FUNCTION. "
    "`scripts/mitigation_unit.py` ships ITS rejected recipe executable, on the argument that a "
    "rejection anyone can re-run is stronger than one stated in prose, and that argument is good — "
    "it simply does not reach here. D-09 requires this form to be NAMED WITHOUT TRANSCRIBING ITS "
    "LOGIC, because the risk being managed is a future reader lifting a formula out of a frozen "
    "pin and believing the pin endorsed it. And the ceiling settles it independently: "
    "`sqrt(2*ln(1.25/delta))` needs `log`, which is reachable by no operator, so a runnable "
    "version could not exist in this file even if D-09 permitted one. The measurements above are "
    "the re-runnable half, and they carry their own inputs."
)


# ---------------------------------------------------------------------------------------------
# 3. THE ADJACENCY RELATION (D-18). The definitional half every code-level guard structurally
#    cannot reach, and the one PITFALLS P3 assigned to two earlier phases that both closed
#    without landing it.
# ---------------------------------------------------------------------------------------------
NEIGHBOURING = "add/remove one fact"

NEIGHBOURING_REASON = (
    "mu = Delta/sigma REQUIRES Delta TO BE THE PER-STEP L2 SENSITIVITY UNDER A FIXED NEIGHBOURING "
    "RELATION, and the two standard choices differ by a FACTOR OF 2: "
    "\n\n"
    "  * add/remove-one (UNBOUNDED DP): removing a record changes the clipped sum by g_i, whose "
    "norm is at most C, so Delta = C. "
    "  * replace-one (BOUNDED DP): replacing record i changes the sum by g_i - g_i', whose norm is "
    "at most 2C, so Delta = 2C. "
    "\n\n"
    "THE CHOICE MATCHES THE ARGUMENT THIS PROJECT ALREADY WROTE, rather than being inherited by "
    "silence. The DP-SGD sensitivity argument as stated — 'one record moves the sum by at most C, "
    "the textbook sensitivity argument' — IS the add/remove-one argument. It is correct under that "
    "convention and wrong by 2x under replace-one. And 'one fact' is "
    "`scripts/mitigation_unit.py::PRIVACY_UNIT` verbatim, so this pin introduces NO SECOND "
    "VOCABULARY for the same object: the unit being added or removed is the same unit that module "
    "already froze. "
    "\n\n"
    "THE STAKE, STATED AS A NUMBER RATHER THAN AS A CONCERN: epsilon is roughly linear in mu over "
    "the operating range, so the alternative convention is roughly 2x ON EVERY PUBLISHED EPSILON. "
    "That is not a rounding difference in a headline claim — it is the difference between a "
    "defensible number and one an informed reader will discount by half. "
    "\n\n"
    "WHY IT NEEDS ITS OWN PIN, which is the part that is easy to get wrong. The mechanism's "
    "single-source clip constant makes the wrong-sensitivity FAKE impossible at the CODE level: a "
    "second clip constant is a positive insertion the AST guard catches. It does not touch the "
    "DEFINITIONAL half. Single-sourcing proves the code is SELF-CONSISTENT, never that C is the "
    "RIGHT sensitivity for the adjacency the report claims. An implementation can pass every "
    "static axis and every runtime invariant this phase builds while publishing an epsilon that is "
    "2x optimistic, because every one of those guards compares C against C."
)

SENSITIVITY_MULTIPLIER = 1.0

SENSITIVITY_MULTIPLIER_REASON = (
    "THE NUMERIC CONSEQUENCE OF `NEIGHBOURING`: Delta = SENSITIVITY_MULTIPLIER * C, and under "
    "add/remove-one that multiplier is 1.0. Pinned as a separate constant rather than folded into "
    "the relation string because a number is what a call site can actually read. "
    "\n\n"
    "THE WARNING SIGN THIS PAIR EXISTS TO CATCH is the one `.planning/research/PITFALLS.md` P3 "
    "names in its own words: THE REPORT SAYS ADD/REMOVE AND THE ACCOUNTANT'S DOCSTRING SAYS "
    "REPLACE. Nothing in a training loop records which relation you meant; papers use both; the "
    "relation is a definition rather than a code artifact, so it can only be checked by comparing "
    "the places that STATE it. The two failing shapes are therefore a multiplier of 2.0 under this "
    "relation, and a multiplier of 1.0 under replace-one — each of which is internally coherent at "
    "one site and wrong across sites. "
    "\n\n"
    "THE CROSS-SITE CONSISTENCY CHECK IS "
    "`tests/test_phase22_dpsgd_ast.py::test_adjacency_relation_consistent`. It reads THIS "
    "constant, the relation as documented at `src/personacore/privacy/accountant.py`, and the "
    "noise line at `src/personacore/privacy/dpsgd.py`, and refuses on disagreement. "
    "\n\n"
    "IT IS A MULTI-SITE SOURCE READ RATHER THAN AN IMPORT, AND THAT IS FORCED. This pin cannot "
    "import either site — the ceiling admits only three names — and neither site can import this "
    "pin, because `src/` never puts `scripts/` on the path; tests reach `scripts/` modules by an "
    "explicit `sys.path` insert, which is a test-only affordance. The ceiling runs ONE WAY. So the "
    "check has to be a test that reads all three sites' source, which is the same shape the "
    "forbidden-token closure guard already builds."
)


# ---------------------------------------------------------------------------------------------
# 4. WHAT `sigma` MEANS (RESEARCH F4). Unitless noise multiplier — NOT the raw noise std.
# ---------------------------------------------------------------------------------------------
SIGMA_IS_THE_NOISE_MULTIPLIER = (
    "`sigma` EVERYWHERE IN THIS FILE IS THE NOISE MULTIPLIER: sigma == sigma_noise / C, UNITLESS. "
    "It is not the raw standard deviation of the added noise. The consequence is arithmetic: "
    "mu = Delta/sigma_noise = C/sigma_noise = 1/sigma, and mu_eff = T ** 0.5 / sigma — so THE "
    "ACCOUNTANT CORRECTLY NEEDS NO C ARGUMENT AT ALL. C cancels. "
    "\n\n"
    "THE BASIS IS A FROZEN ARTIFACT, NOT A PREFERENCE: "
    "`scripts/mitigation_gate.py::MECHANISM_KEYS` is ('sigma', 'steps', 'delta', 'q') and that "
    "module's own comment beside it says there is NO FIFTH KEY. It calls those the mechanism "
    "parameters epsilon is a deterministic function of, and the DP arm's formal claim in the same "
    "file names the recorded NOISE MULTIPLIER, step count, sampling rate and delta — four "
    "quantities, matching the four keys exactly. That file is FROZEN and cannot be amended. "
    "\n\n"
    "SO ADDING A `clip_norm=` PARAMETER TO `epsilon_for` WOULD CREATE THAT FIFTH KEY — a mechanism "
    "parameter the frozen gate states does not exist, and therefore a divergence between what the "
    "gate says epsilon depends on and what the accountant actually consumes. Consistency with "
    "MECHANISM_KEYS is not a style question here. Any prose elsewhere reading 'mu = C/sigma' is "
    "using sigma for the RAW noise std; it is the outlier phrasing rather than a fifth decision, "
    "and its substance is unaffected."
)


# ---------------------------------------------------------------------------------------------
# 5. THE GOLDEN OUTPUTS. Outputs ONLY — there is no executable formula anywhere in this file.
# ---------------------------------------------------------------------------------------------
GOLDEN_EPSILON = (
    (20.0, 200, 2.943225239801352),
    (14.142135623730951, 200, 4.377178095681209),
    (10.0, 200, 6.572970067030306),
    (5.0, 200, 15.456155822609244),
    (2.0, 200, 54.376639014985045),
    (1.0, 1, 4.377178095681209),
    (8.0, 64, 4.377178095681209),
)

GOLDEN_EPSILON_PROVENANCE = (
    "SEVEN (sigma, steps, epsilon) ROWS, EVALUATED AT THE FROZEN DELTA. Every epsilon is bisected "
    "to convergence against the INDEPENDENT QUADRATURE ORACLE — the one that integrates the "
    "(eps, delta)-DP definition directly with `exp` alone and no Phi and no erfc — against "
    "60-decimal-place ground truth. THEY ARE NEVER SNAPSHOTTED FROM "
    "`src/personacore/privacy/accountant.py`. "
    "\n\n"
    "D-13'S STATED REASON, because this is the constraint most likely to be quietly inverted by a "
    "later maintainer looking for a convenient way to regenerate the table: A GOLDEN TABLE READ "
    "OFF THE IMPLEMENTATION SHARES ITS FAILURE MODES BY CONSTRUCTION. It would be A PHOTOGRAPH OF "
    "THE CODE RATHER THAN A CONSTRAINT ON IT — green on the day it was taken and green forever "
    "after, including on every day the code is wrong in the same way it was wrong then. The two "
    "routes have to be different MATHEMATICS, not merely different call sites. "
    "\n\n"
    "AND THAT IS WHY AN EXACT FLOAT PIN WOULD BE WRONG rather than merely strict. The oracle and "
    "the erfc closed form the implementation uses differ AT ABOUT 1e-14 BY CONSTRUCTION — they "
    "evaluate different integrals in floating point — with a MEASURED WORST CASE OF 1.07e-14 "
    "across these seven rows, at the sigma = 2.0 row. An `==` here would pin the pin to one of the "
    "two mathematics and redden on correct code. `GOLDEN_EPSILON_REL_TOL` is 1e-12: about two "
    "orders of margin over that measured 1.07e-14, and about two orders TIGHTER than any real "
    "implementation error would be. Both directions are stated because a tolerance justified only "
    "from below is a tolerance nobody can argue is not simply generous. "
    "\n\n"
    "THE COMPOSITION IDENTITY APPEARS HERE AS DATA. Three rows compose to mu_eff = 1.0 and carry a "
    "BIT-IDENTICAL epsilon; the module-scope guards below locate those rows STRUCTURALLY and prove "
    "it with operators. (A note for anyone re-deriving this table: the research prose calls them "
    "'the last three rows'. Measured against this ordering they are rows 2, 6 and 7 — the "
    "positional phrase is a mis-transcription and the row VALUES it names one sentence later are "
    "the correct ones. The guards below never use the positional phrase.)"
)

GOLDEN_EPSILON_REL_TOL = 1.0e-12

GOLDEN_EPSILON_DELTA_SOURCE = (
    "EVERY ROW ABOVE IS EVALUATED AT `scripts/mitigation_unit.py::DELTA`. The literal is NOT "
    "re-spelled here and NOT imported here — re-spelling would create a second copy free to "
    "diverge from the frozen one, and importing is impossible under this file's ceiling. A "
    "consuming test resolves the value from that module and passes it in, which is the only shape "
    "that keeps ONE delta in the repository."
)


# ---------------------------------------------------------------------------------------------
# THE GUARDS. Module scope, so a wrong edit fails at IMPORT rather than inside a consumer that
# has already spent compute — the same placement reason as `scripts/mitigation_unit.py`'s.
#
# NOTE ON THE SHAPE OF THESE EXPRESSIONS. There is no `len(...)`, no `sorted(...)` and no
# `abs(...)` below, and their absence is deliberate rather than awkward:
# `tests/test_phase20_prereg.py::test_mitigation_accountant_pin_has_no_executable_formula` asserts
# that EVERY module-level call in this file is a `_prove` call, which is what refuses a formula
# smuggled in as a helper invocation. Slice comparisons and chained comparisons do the same work
# with operators only. Arithmetic lives INSIDE the messages, so every margin is computed at import
# rather than transcribed by hand and left to rot.
# ---------------------------------------------------------------------------------------------
_prove(
    SENSITIVITY_MULTIPLIER == 1.0,
    f"SENSITIVITY_MULTIPLIER is {SENSITIVITY_MULTIPLIER}, not 1.0, while NEIGHBOURING is "
    f"'{NEIGHBOURING}'. Delta = SENSITIVITY_MULTIPLIER * C, and under add/remove-one the "
    "sensitivity of the clipped sum IS C. A multiplier of 2.0 under THIS relation, or of 1.0 "
    "under replace-one, is exactly the PITFALLS P3 fake — each is internally coherent at one site "
    "and wrong across sites, and since epsilon is roughly linear in mu, either mistake is roughly "
    "2x on every published epsilon",
)
_prove(
    "add/remove" in NEIGHBOURING,
    f"NEIGHBOURING is '{NEIGHBOURING}', which does not name the add/remove-one relation, while "
    f"SENSITIVITY_MULTIPLIER is still {SENSITIVITY_MULTIPLIER}. This is the degenerate half-edit: "
    "the relation string silently changed to replace-one while the multiplier stayed at the "
    "add/remove-one value, leaving Delta = C published under a convention that requires "
    "Delta = 2C. The two constants are one decision and they must move together",
)

# THE `T ** 0.5` COMPOSITION PROOF, in two parts. The rows are located STRUCTURALLY — by their
# composed mu_eff, an operator expression — and never by position, because the positional phrase
# 'the last three rows' is a known mis-transcription of this exact table.
_prove(
    [row for row in GOLDEN_EPSILON if -1e-12 <= row[1] ** 0.5 / row[0] - 1.0 <= 1e-12]
    == [GOLDEN_EPSILON[1], GOLDEN_EPSILON[5], GOLDEN_EPSILON[6]],
    "the rows whose composed mu_eff = steps ** 0.5 / sigma equals 1.0 to within 1e-12 relative are "
    f"{[row for row in GOLDEN_EPSILON if -1e-12 <= row[1] ** 0.5 / row[0] - 1.0 <= 1e-12]}, which "
    f"is not [{GOLDEN_EPSILON[1]}, {GOLDEN_EPSILON[5]}, {GOLDEN_EPSILON[6]}]. Dong, Roth and Su "
    "Corollary 3.3 puts exactly three rows of this table at mu_eff = 1.0 — one at T = 200, one at "
    "T = 1 and one at T = 64 — so a different set means either a sigma or a steps column was "
    "mistyped, or the table was reordered under guards that name positions",
)
_prove(
    GOLDEN_EPSILON[1][2] == GOLDEN_EPSILON[5][2] == GOLDEN_EPSILON[6][2],
    "the three rows composing to mu_eff = 1.0 carry epsilons "
    f"{GOLDEN_EPSILON[1][2]}, {GOLDEN_EPSILON[5][2]} and {GOLDEN_EPSILON[6][2]}, which are not "
    "ONE value. Their composed mu_eff are "
    f"{GOLDEN_EPSILON[1][1] ** 0.5 / GOLDEN_EPSILON[1][0]}, "
    f"{GOLDEN_EPSILON[5][1] ** 0.5 / GOLDEN_EPSILON[5][0]} and "
    f"{GOLDEN_EPSILON[6][1] ** 0.5 / GOLDEN_EPSILON[6][0]} — deviations from 1.0 of "
    f"{GOLDEN_EPSILON[1][1] ** 0.5 / GOLDEN_EPSILON[1][0] - 1.0}, "
    f"{GOLDEN_EPSILON[5][1] ** 0.5 / GOLDEN_EPSILON[5][0] - 1.0} and "
    f"{GOLDEN_EPSILON[6][1] ** 0.5 / GOLDEN_EPSILON[6][0] - 1.0}"
    f", against a tolerance of {GOLDEN_EPSILON_REL_TOL}. epsilon is a function of (mu_eff, delta) "
    "alone, so equal mu_eff at one delta REQUIRES equal epsilon: T = 200 at sigma = sqrt(200), "
    "T = 1 at sigma = 1 and T = 64 at sigma = 8 are the same mechanism to the accountant. This is "
    "the composition identity proved inside the pin with operators and no import",
)

# THE TABLE'S SHAPE. A transcription typo that survives the composition proof above still has to
# survive these: seven rows, three columns, positive throughout, and monotone where the analytic
# form guarantees monotonicity.
_prove(
    GOLDEN_EPSILON[6:] == (GOLDEN_EPSILON[-1],),
    f"GOLDEN_EPSILON's tail from index 6 is {GOLDEN_EPSILON[6:]}, which is not the single-row "
    "tuple seven rows would produce. The slice comparison is the no-call form of a length check "
    "(see the note above this block). Seven is the count the oracle derivation covers; an eighth "
    "row would be an epsilon nothing measured, and a sixth would silently drop one",
)
_prove(
    [row for row in GOLDEN_EPSILON if row[2:] == (row[-1],) and row[0] > 0.0 and row[2] > 0.0]
    == [row for row in GOLDEN_EPSILON],
    "at least one GOLDEN_EPSILON row is not a 3-tuple of a strictly positive sigma, a step count "
    "and a strictly positive epsilon. The surviving rows are "
    f"{[row for row in GOLDEN_EPSILON if row[2:] == (row[-1],) and row[0] > 0.0 and row[2] > 0.0]} "
    f"out of {GOLDEN_EPSILON}. A sigma of 0.0 is the sigma = 0 case, whose epsilon is infinite and "
    "which therefore has no place in a table of finite outputs; a non-positive epsilon is not a "
    "number this mechanism can produce at any finite sigma",
)
_prove(
    GOLDEN_EPSILON[0][1]
    == GOLDEN_EPSILON[1][1]
    == GOLDEN_EPSILON[2][1]
    == GOLDEN_EPSILON[3][1]
    == GOLDEN_EPSILON[4][1]
    == 200
    and GOLDEN_EPSILON[0][0]
    > GOLDEN_EPSILON[1][0]
    > GOLDEN_EPSILON[2][0]
    > GOLDEN_EPSILON[3][0]
    > GOLDEN_EPSILON[4][0]
    and GOLDEN_EPSILON[0][2]
    < GOLDEN_EPSILON[1][2]
    < GOLDEN_EPSILON[2][2]
    < GOLDEN_EPSILON[3][2]
    < GOLDEN_EPSILON[4][2],
    "the first five rows should be one fixed step count with sigma DESCENDING and epsilon "
    "ASCENDING — i.e. epsilon strictly DECREASING in sigma. Measured: steps "
    f"{GOLDEN_EPSILON[0][1]}, {GOLDEN_EPSILON[1][1]}, {GOLDEN_EPSILON[2][1]}, "
    f"{GOLDEN_EPSILON[3][1]}, {GOLDEN_EPSILON[4][1]}; "
    f"sigmas {GOLDEN_EPSILON[0][0]}, {GOLDEN_EPSILON[1][0]}, "
    f"{GOLDEN_EPSILON[2][0]}, {GOLDEN_EPSILON[3][0]}, {GOLDEN_EPSILON[4][0]}; epsilons "
    f"{GOLDEN_EPSILON[0][2]}, {GOLDEN_EPSILON[1][2]}, {GOLDEN_EPSILON[2][2]}, "
    f"{GOLDEN_EPSILON[3][2]}, {GOLDEN_EPSILON[4][2]}. More noise is more privacy: mu_eff = "
    "T ** 0.5 / sigma falls as sigma rises, and epsilon rises with mu_eff, so the analytic form "
    "GUARANTEES this ordering. A digit transposed in a transcribed epsilon breaks it, which is why "
    "a property the mathematics guarantees is worth asserting over data that was typed in by hand",
)

_prove(
    REJECTED_FORM != REQUIRED_FORM,
    "REJECTED_FORM and REQUIRED_FORM hold the same string, so this file records no rejection at "
    "all. The degenerate edit is the cheapest way to neutralise a pre-registration without "
    "deleting anything: make the refused alternative identical to the required one and every "
    "reference to 'the rejected form' silently becomes a reference to the accepted one",
)
