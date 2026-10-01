"""Phase 35 PRE-REGISTRATION — the v6.0 core, its deferred slots, and the PREREG-09 research the
E3/E4 thresholds rest on, committed before any v6.0 number exists.

WHAT THIS FREEZES. The whole intended content of this module: the v6.0 core (D-01); the registry
of deferred slots, each naming its owning phase and its inputs (D-02, D-15); the PREREG-09 one-run
audit bound, a stdlib port of Steinke, Nasr and Jagielski's Appendix D that must reproduce two
values printed in the paper before E4 may advance (D-11); and E3's selection accounting, basic
composition by reference to ``phase25_epsilon.curve_total`` with ``SELECTION_ACCOUNTED`` False
(D-12). The prose behind every value is ``.planning/research/V6-PREREG-09.md``, committed before
this file; the values themselves live only here.

ENTRIES. Every threshold is an entry with exactly four fields, ``value``, ``derivation``, ``kind``
(``derived`` or ``preference``) and ``source`` (D-07 as amended by D-14). No entry carries a
proposer field: who suggested what lives in the discussion logs and in git, never in the code.
``_prove_entry`` refuses a ``proposer`` or ``adopted_by`` key and the phrase "selected by THE USER,
verbatim".

ANCESTRY-GUARDED. ``tests/test_phase35_prereg.py``
(``test_phase35_prereg_is_frozen_before_every_v6_result``, added in Plan 02) requires every commit
touching this file to precede the first v6.0 record. Once that record exists, a correction is a
dated continuation, never an edit here: a new continuation module for Python (the
``phase23_resume_prereg`` precedent) and ``scripts/_addendum.py`` for published markdown.

CPU-ONLY AT IMPORT. Stdlib + sibling scripts only. ``phase19_erasure``, ``phase18_extraction``,
``phase23_run``, ``phase26_canary`` and ``teach_persona`` are imported LAZILY, inside the rules
that need them (torch at import, or a ``git_sha()`` subprocess at import).
``personacore.privacy.accountant`` IS loaded, TRANSITIVELY, through ``phase25_epsilon``; that load
is torch-free and stated rather than hidden.

Threats mitigated: T-35-01 (wrong-version citation — the reproduction pins our port to the paper's
printed values, so a misread page fails numerically); T-35-02 (threshold before research — the
note's first add precedes every commit of this file, checked in git); T-35-03 (port drift — two
published pins, a closed form, and a dropped-delta mutant outside the tolerance); T-35-04
(misattributed provenance — four-field schema proved at import); T-35-05 (composition re-implemented
— ``is`` bindings to the v4.0 objects).
"""

import collections.abc
import json
import math
import pathlib
import sys
import types

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_SRC = str(_REPO_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import erasure_gate  # noqa: E402  (needs the sys.path insert above; torch-free)
import mitigation_budget  # noqa: E402  (same; torch-free)
import mitigation_gate  # noqa: E402  (same; torch-free)
import mitigation_unit  # noqa: E402  (same)
import phase19_floor  # noqa: E402  (same; torch-free)
import phase25_epsilon  # noqa: E402  (same; loads the torch-free accountant transitively)
import phase26_prereg  # noqa: E402  (same; torch-free, no subprocess at import)

# =================================================================================================
# (1) THE DATE AND THE PROPERTY IT CERTIFIES.
# =================================================================================================

# At this commit no `results/phase3[6-9]_*` or `results/phase4[0-5]_*` file existed, tracked or
# untracked.
COMMITTED = "2026-10-01"
RECORDS_AT_COMMIT = 0


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase35_prereg] {message}")


def _prove_count(name, value):
    """``prove_reproduction``'s register: an ``int`` that is not a ``bool``, or a refusal."""
    _prove(
        isinstance(value, int) and not isinstance(value, bool),
        f"{name} is {value!r}, which is not an int (bool excluded). This formula takes COUNTS; a "
        "float came out of arithmetic and a bool would compare True against 1",
    )


# =================================================================================================
# (2) THE ENTRY SCHEMA (D-07 as amended by D-14).
# =================================================================================================

ENTRY_FIELDS = ("value", "derivation", "kind", "source")
KINDS = ("derived", "preference")
FORBIDDEN_PHRASE = "selected by THE USER, verbatim"


def _prove_entry(name, entry):
    """Refuse any entry that is not exactly the four D-14 fields with a known kind."""
    _prove(
        isinstance(entry, collections.abc.Mapping),
        f"entry {name!r} is {type(entry).__name__}, not a mapping",
    )
    for banned in ("proposer", "adopted_by"):
        _prove(
            banned not in entry,
            f"entry {name!r} carries a {banned!r} key. D-14: entries hold exactly "
            f"{ENTRY_FIELDS}; who suggested what lives in the discussion logs and git",
        )
    _prove(
        set(entry) == set(ENTRY_FIELDS),
        f"entry {name!r} has fields {sorted(entry)}, expected exactly {sorted(ENTRY_FIELDS)}",
    )
    _prove(entry["kind"] in KINDS, f"entry {name!r} has kind {entry['kind']!r}, not one of {KINDS}")
    for field in ("derivation", "source"):
        text = entry[field]
        _prove(
            isinstance(text, str) and text.strip(),
            f"entry {name!r} has an empty or non-str {field}",
        )
        _prove(
            FORBIDDEN_PHRASE not in text,
            f"entry {name!r} {field} contains {FORBIDDEN_PHRASE!r}",
        )
    value = entry["value"]
    _prove(
        not (isinstance(value, str) and FORBIDDEN_PHRASE in value),
        f"entry {name!r} value contains {FORBIDDEN_PHRASE!r}",
    )


# =================================================================================================
# (3) E3 SELECTION ACCOUNTING — BASIC COMPOSITION, BY REFERENCE (D-12). Never retyped: the test
# file asserts identity (`is`).
# =================================================================================================

CURVE_TOTAL = phase25_epsilon.curve_total
SELECTION_ACCOUNTED = phase25_epsilon.SELECTION_ACCOUNTED
DELTA = mitigation_unit.DELTA

# =================================================================================================
# (4) THE ONE-RUN AUDIT BOUND (D-11) — a line-for-line stdlib port of arXiv 2305.08846v1
# Appendix D (pp. 45-46). scipy's binomial sf/pmf are replaced by an exact lgamma pmf summed with
# math.fsum; App. D's `assert`s become `_prove` refusals.
# =================================================================================================


def _binom_pmf(k, n, q):
    """Exact Binomial(n, q) pmf at k through ``math.lgamma``; 0.0 outside 0..n."""
    if k < 0 or k > n:
        return 0.0
    if q == 1.0:
        return 1.0 if k == n else 0.0
    return math.exp(
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
        + k * math.log(q)
        + (n - k) * math.log1p(-q)
    )


def _prove_real(name, value):
    _prove(
        isinstance(value, (int, float)) and not isinstance(value, bool),
        f"{name} is {value!r}, which is not an int or float (bool excluded)",
    )


def _prove_one_run_inputs(m, r, v, delta, beta=None, eps=None):
    for name, value in (("m", m), ("r", r), ("v", v)):
        _prove_count(name, value)
    _prove(m >= 1, f"m is {m}; at least one canary is needed")
    _prove(0 <= v <= r <= m, f"need 0 <= v <= r <= m, got v={v}, r={r}, m={m}")
    _prove_real("delta", delta)
    _prove(0 <= delta < 1, f"delta is {delta!r}; need 0 <= delta < 1")
    if beta is not None:
        _prove_real("beta", beta)
        _prove(0 < beta < 1, f"beta is {beta!r}; need 0 < beta < 1")
    if eps is not None:
        _prove_real("eps", eps)
        _prove(math.isfinite(eps) and eps >= 0, f"eps is {eps!r}; need a finite eps >= 0")


def _p_value(m, r, v, eps, delta):
    q = 1 / (1 + math.exp(-eps))
    beta_term = math.fsum(_binom_pmf(k, r, q) for k in range(v, r + 1))
    alpha = cumulative = 0.0
    for i in range(1, v + 1):
        cumulative += _binom_pmf(v - i, r, q)
        if cumulative > i * alpha:
            alpha = cumulative / i
    return min(beta_term + alpha * delta * 2 * m, 1)


def p_value_one_run(m, r, v, eps, delta):
    """Corollary 5.4 (pp. 15-16): the p-value of v correct guesses out of r, m canaries, under
    (eps, delta)-DP. App. D's ``p_value_DP_audit``."""
    _prove_one_run_inputs(m, r, v, delta, eps=eps)
    return _p_value(m, r, v, eps, delta)


def eps_lower_one_run(m, r, v, delta, beta):
    """App. D's ``get_eps_audit``: the largest eps rejected at level beta (Lemma 4.7), found by
    stepping an upper bracket then 30 bisection steps. Returns the conservative low end."""
    _prove_one_run_inputs(m, r, v, delta, beta=beta)
    lo, hi = 0, 1
    while _p_value(m, r, v, hi, delta) < beta:
        hi += 1
    for _ in range(30):
        mid = (lo + hi) / 2
        if _p_value(m, r, v, mid, delta) < beta:
            lo = mid
        else:
            hi = mid
    return lo


# The paper's printed values, not thresholds. Inputs are (m, r, v, delta, beta).
ONE_RUN_PUBLISHED = types.MappingProxyType(
    {
        "app_d_p46": types.MappingProxyType(
            {
                "inputs": (1000, 100, 75, 1e-4, 0.05),
                "published": 0.673,
                "where": "arXiv:2305.08846v1 Appendix D p. 46",
            }
        ),
        "sec7_p28": types.MappingProxyType(
            {
                "inputs": (100000, 1510, 1439, 1e-5, 0.05),
                "published": 2.675,
                "where": "arXiv:2305.08846v1 §7 p. 28 (Fig. 11)",
            }
        ),
    }
)


def one_run_reproduction_holds():
    """D-11: True iff the port reproduces every published pin within the declared tolerance.
    Re-run at call time, so a rule can refuse to compute the AUDIT-01 ceiling when it fails."""
    tolerance = ENTRIES["one_run_tolerance"]["value"]
    return all(
        abs(eps_lower_one_run(*pin["inputs"]) - pin["published"]) < tolerance
        for pin in ONE_RUN_PUBLISHED.values()
    )


# =================================================================================================
# (5) THE v6.0 RECORD PATHS (D-01). ONE tuple; the ancestry pathspecs are DERIVED from it. Later
# phases import these names and never retype them.
# =================================================================================================

V6_RESULT_PATHS = (
    "results/phase36_probe_*.json",  # COST-01
    "results/phase36_budget.json",  # COST-02
    "results/phase37_*",  # REPRO-01..03
    "results/phase38_minting*.json",  # RANK-01
    "results/phase38_*",  # RANK-02
    "results/phase39_*",  # CTX-01..03
    "results/phase40_*",  # NOISE-01/02
    "results/phase41_calibration_*.json",  # ERASE-06
    "results/phase41_band_inputs_*.json",  # ERASE-09
    "results/phase41_*",  # ERASE-03..10
    "results/phase42_control_*.json",  # RECIPE-01/03, the sigma = 0 controls
    "results/phase42_*",  # RECIPE-01..04
    "results/phase43_*",  # AUDIT-01..03
    "results/phase44_*",  # PKG-01..08
    "results/phase45_*",  # RPT-07..09
)

# DERIVED, not typed: exactly results/phase36_* .. results/phase45_*.
ARTIFACT_PATHSPECS = tuple(sorted({p.split("_", 1)[0] + "_*" for p in V6_RESULT_PATHS}))

# =================================================================================================
# (6) CLOSED PINS, BY REFERENCE. Plain attribute bindings; never a retyped value.
# =================================================================================================

F_Y = mitigation_gate.F_Y
F_C = mitigation_gate.F_C
DIALOGUE_GAP_BAND = mitigation_gate.dialogue_gap_band
CEILING_CLAUSE = phase26_prereg.CEILING_CLAUSE
STEP_BUDGET = mitigation_budget.STEP_BUDGET
CURVE_K = mitigation_budget.CURVE_K
FULL_FIDELITY_K = mitigation_budget.FULL_FIDELITY_K
SIGMA_LADDER = mitigation_budget.SIGMA_LADDER
MARGIN_K = erasure_gate.MARGIN_K

# =================================================================================================
# (7) THE SEED LIST (D-05, D-06).
# =================================================================================================


def seed_list():
    """The v6.0 seed list IS ``phase23_run.SEED_LADDER``, returned by identity.

    Its first two seeds, 1337 and 2024, are already Phase 19's pair
    (``phase19_erasure.DIALOGUE_NOISE_FLOOR_SEEDS``), which was itself Phase 12's own second seed,
    reused rather than minted. The ladder was committed at 5303819 (2026-08-27), before any v6.0
    result existed. The list is NEVER extended (D-06): a phase that needs more seeds than it holds
    reports the shortfall instead of minting one.
    """
    import phase23_run  # teach_persona -> torch at import: lazy, so this module stays CPU-only

    return phase23_run.SEED_LADDER


def e1_teaching_seeds():
    """ERASE-05: E1 teaches on seed 1337 plus ONE new seed, the first two of ``seed_list()``.
    ERASE-10: no E1 PASS is reported without the second seed's run."""
    return seed_list()[:2]


# =================================================================================================
# (8) THE E1 TARGETS (D-03): every slot at ceiling recall in Phase 19's published ranking.
# =================================================================================================


def e1_targets():
    """The ``slot`` of every ``phase19_erasure.TARGET_RANKING`` row with ``successes ==
    n_questions``, in ranking order. Read, never typed: the names are this function's output."""
    import phase19_erasure  # torch at import: lazy

    rows = [
        dict(zip(phase19_erasure.TARGET_RANKING_FIELDS, row, strict=True))
        for row in phase19_erasure.TARGET_RANKING
    ]
    targets = tuple(row["slot"] for row in rows if row["successes"] == row["n_questions"])
    _prove(targets, "no TARGET_RANKING row is at ceiling recall: the D-03 premise is gone")
    return targets


# =================================================================================================
# (9) THE AUDIT-02 CUT AND THE E4 RULE (D-09).
# =================================================================================================


def audit02_cut():
    """The smallest ``epsilon_upper`` among Phase 26's points whose claim "could not have failed"
    (``epsilon_upper >= auditor_ceiling``), read from ``phase26_canary.RECORD`` at call time. On
    the committed record that is 11 points with minimum 3.7965357228934966."""
    import phase26_canary  # git_sha() subprocess at import: lazy

    record = json.loads(phase26_canary.RECORD.read_text(encoding="utf-8"))
    ceiling = record["auditor_ceiling"]
    uppers = [
        point["epsilon_upper"]
        for point in record["points"].values()
        if point.get("epsilon_upper") is not None and point["epsilon_upper"] >= ceiling
    ]
    _prove(
        uppers,
        "no Phase 26 point has epsilon_upper >= auditor_ceiling: the AUDIT-02 premise is gone",
    )
    return min(uppers)


def e4_runs(one_run_ceiling):
    """AUDIT-02: E4 runs iff the CPU-computed one-run ceiling is STRICTLY greater than
    ``audit02_cut()``, i.e. it could reprove at least one point Phase 26 could not."""
    _prove_real("one_run_ceiling", one_run_ceiling)
    _prove(math.isfinite(one_run_ceiling), f"one_run_ceiling is {one_run_ceiling!r}, not finite")
    return one_run_ceiling > audit02_cut()


# =================================================================================================
# (10) E1 CONDITION (b)'s MARGIN (D-16) AND THE R1a ASSERTIONS (D-01).
# =================================================================================================


def e1_condition_b_margin():
    """Condition (b)'s margin: ``nontarget_noise_floor.margin_at_gate`` of the Phase 19 record.

    D-16: condition (b) compares the SAME adapter before and after ablation, so the noise that
    matters is SAMPLING noise (v3.0's margin, MARGIN_K x the sampling floor), not training noise.
    Phase 40's training-seed floor is used ONLY in the M1 x M2 comparison, never as E1's gate.
    On the committed record this reads 0.2962962962962963 = 2 x 0.14814814814814814.
    """
    path = _REPO_ROOT / phase19_floor.EVIDENCE_ARTIFACT["NONTARGET_NOISE_FLOOR"]
    floor = json.loads(path.read_text(encoding="utf-8"))["nontarget_noise_floor"]
    _prove(
        floor["margin_at_gate"] == MARGIN_K * floor["value"],
        f"margin_at_gate {floor['margin_at_gate']!r} is not MARGIN_K x value {floor['value']!r}",
    )
    return floor["margin_at_gate"]


# Asserted values: the published R1a claim Phase 37 must reproduce exactly. The margin the seven
# non-targets are "beyond" is `e1_condition_b_margin()`, never typed.
R1A_ASSERTIONS = types.MappingProxyType(
    {
        "k": 78,
        "target_correct": (0, 27),
        "nontargets_beyond_margin": (7, 7),
        "destroyed_pct": 77.6370113463966,
    }
)


def r1a_rederive():
    """Re-derive ``k`` and the destroyed percentage from ``arm_record_path("erased")``.

    ``k`` is ``len(config.ablated_components)``, NOT ``config.k`` (48, the A2 attack budget).
    destroyed = (1 - g1 / g0) x 100 with g0 / g1 the dialogue on-off gap before / after erasure.
    0/27 and 7/7 are NOT re-derivable from this record (its per-fact cell reads 0/14, defect C);
    Phase 37 owns their routed re-derivation.
    """
    import phase19_erasure  # torch at import: lazy

    record = json.loads(phase19_erasure.arm_record_path("erased").read_text(encoding="utf-8"))
    k = len(record["config"]["ablated_components"])
    pre, post = record["pre_erasure"]["dialogue_ppl"], record["dialogue_ppl"]
    g0 = pre["adapter_on"] - pre["adapter_off"]
    g1 = post["adapter_on"] - post["adapter_off"]
    destroyed = (1 - g1 / g0) * 100
    _prove(
        k == R1A_ASSERTIONS["k"],
        f"erased record has k = {k}, R1a asserts {R1A_ASSERTIONS['k']}",
    )
    _prove(
        destroyed == R1A_ASSERTIONS["destroyed_pct"],
        f"erased record destroys {destroyed!r}%, R1a asserts {R1A_ASSERTIONS['destroyed_pct']!r}",
    )
    return types.MappingProxyType(
        {"k": k, "destroyed_pct": destroyed, "margin": e1_condition_b_margin()}
    )


# =================================================================================================
# (11) E3's sigmas (RECIPE-01 as reworded by D-17), each a member of the v4.0 ladder.
# =================================================================================================

E3_SIGMAS = (0.0, 0.5, 1.0)
_prove(
    all(s in SIGMA_LADDER for s in E3_SIGMAS),
    f"E3_SIGMAS {E3_SIGMAS} is not a subset of mitigation_budget.SIGMA_LADDER",
)

# =================================================================================================
# (12) THE A2 CORPUS (CTX-01 / E6 population): depends on no v6.0 measurement.
# =================================================================================================


def a2_corpus_entries():
    """Every Phase 18 corpus prompt of family A2, in corpus order."""
    import phase18_extraction  # torch at import: lazy

    _prove("A2" in phase18_extraction.ATTACK_FAMILIES, "A2 is no longer a Phase 18 attack family")
    corpus = json.loads(phase18_extraction.CORPUS_PATH.read_text(encoding="utf-8"))
    entries = tuple(p for p in corpus["prompts"] if p["family"] == "A2")
    _prove(entries, "the Phase 18 corpus holds no A2 prompt")
    return entries


# =================================================================================================
# (13) ENTRIES — the last block of the file. A plain dict literal so the AST tests can walk it.
# =================================================================================================

_ENTRIES = {
    "one_run_tolerance": {
        "value": 1e-3,
        "derivation": (
            "One unit in the last printed digit of both pins: the paper rounds (0.67298 -> 0.673) "
            "and truncates (2.67585 -> 2.675), so a half unit would wrongly fail the second pin. "
            "It still separates the measured mutants (dropping delta; r for m in 2*m*delta) by "
            "at least 26x."
        ),
        "kind": "derived",
        "source": (
            "arXiv:2305.08846v1 App. D p. 46 and §7 p. 28; .planning/research/V6-PREREG-09.md"
        ),
    },
    "e3_composition": {
        "value": phase25_epsilon.curve_total,
        "derivation": (
            "Papernot-Steinke Theorems 2/6 need a random K, uniformly random candidates and "
            "best-only release, none of which E3's fixed, fully published grid satisfies, so basic "
            "composition over the noised configurations is the only accountant (D-12)."
        ),
        "kind": "derived",
        "source": (
            "arXiv:2110.03620v2 §3.3 p. 5, Thm 2 p. 5, Thm 6 p. 7; "
            ".planning/research/V6-PREREG-09.md"
        ),
    },
    "e3_selection_accounted": {
        "value": phase25_epsilon.SELECTION_ACCOUNTED,
        "derivation": (
            "No finer accountant met D-12's three conditions, so RECIPE-02's flag stays false."
        ),
        "kind": "derived",
        "source": (
            "RECIPE-02 (.planning/REQUIREMENTS.md, a9cd408); .planning/research/V6-PREREG-09.md"
        ),
    },
    "delta": {
        "value": mitigation_unit.DELTA,
        "derivation": (
            "The delta every v4.0/v5.0 epsilon was published at, inherited so v6.0 epsilons "
            "compare like for like."
        ),
        "kind": "preference",
        "source": "scripts/mitigation_unit.py:171 (v4.0 SC4 / UNIT-05)",
    },
    "F_Y": {
        "value": mitigation_gate.F_Y,
        "derivation": (
            "Utility rule: recall >= F_Y x the same recipe's sigma = 0 control recall, ONE "
            "fraction applied to BOTH legs (taught and held-out), each against its own control. "
            "mitigation_gate labels it 'PREFERENCE, not a derivation'."
        ),
        "kind": "preference",
        "source": "scripts/mitigation_gate.py:203 (v4.0 D-15/D-16/D-18)",
    },
    "F_C": {
        "value": mitigation_gate.F_C,
        "derivation": (
            "Catastrophe detector: the dialogue gap's lower bound is F_C x the control gap. "
            "mitigation_gate labels it 'PREFERENCE, not a derivation'."
        ),
        "kind": "preference",
        "source": "scripts/mitigation_gate.py:217 (v4.0 D-17/D-18)",
    },
    "dialogue_gap_band": {
        "value": mitigation_gate.dialogue_gap_band,
        "derivation": (
            "D-01's bilateral band lo = F_C x control_gap, hi = control_gap + MARGIN_K x "
            "gap_noise_floor, imported for ERASE-09."
        ),
        "kind": "derived",
        "source": "scripts/mitigation_gate.py:526; ERASE-09 (a9cd408)",
    },
    "audit02_cut": {
        "value": audit02_cut,
        "derivation": (
            "D-09: the minimum epsilon_upper over Phase 26's points with epsilon_upper >= "
            "auditor_ceiling, read at use from phase26_canary.RECORD."
        ),
        "kind": "derived",
        "source": "AUDIT-02 (a9cd408); results/phase26_canary.json",
    },
    "e4_runs": {
        "value": e4_runs,
        "derivation": (
            "E4 runs iff the CPU-computed one-run ceiling is strictly greater than audit02_cut(), "
            "i.e. it could reprove at least one point Phase 26 could not."
        ),
        "kind": "derived",
        "source": "AUDIT-02 (a9cd408)",
    },
    "audit03_ceiling_clause": {
        "value": phase26_prereg.CEILING_CLAUSE,
        "derivation": "Phase 26's ceiling clause, imported so AUDIT-03 states it verbatim.",
        "kind": "derived",
        "source": "scripts/phase26_prereg.py:290; AUDIT-03",
    },
    "seed_list": {
        "value": seed_list,
        "derivation": (
            "phase23_run.SEED_LADDER by identity; its second seed, 2024, was already Phase 19's "
            "(DIALOGUE_NOISE_FLOOR_SEEDS, Phase 12's own second seed, reused). Never extended "
            "(D-06)."
        ),
        "kind": "preference",
        "source": (
            "scripts/phase23_run.py:146, first added 5303819 (2026-08-27); adopted for v6.0 in "
            "35-CONTEXT D-05 (36ab0b4)"
        ),
    },
    "e1_teaching_seeds": {
        "value": e1_teaching_seeds,
        "derivation": "seed_list()[:2], seed 1337 plus one new seed (ERASE-05)",
        "kind": "derived",
        "source": "35-CONTEXT D-05 (36ab0b4); ERASE-05 (a9cd408)",
    },
    "e1_targets": {
        "value": e1_targets,
        "derivation": (
            "Every TARGET_RANKING row at ceiling recall (successes == n_questions), in ranking "
            "order (D-03)."
        ),
        "kind": "derived",
        "source": "scripts/phase19_erasure.py:604 TARGET_RANKING; 35-CONTEXT D-03 (36ab0b4)",
    },
    "e1_condition_b_margin": {
        "value": e1_condition_b_margin,
        "derivation": (
            "Condition (b) compares the SAME adapter before and after ablation, so its noise is "
            "sampling noise: v3.0's margin, MARGIN_K x the sampling floor. Phase 40's "
            "training-seed floor enters only the M1 x M2 comparison, never E1's gate (D-16)."
        ),
        "kind": "derived",
        "source": (
            "results/phase19_noise_floors.json::nontarget_noise_floor.margin_at_gate; "
            "35-CONTEXT D-16 (c012883)"
        ),
    },
    "r1a_assertions": {
        "value": R1A_ASSERTIONS,
        "derivation": (
            "The published R1a claim Phase 37 must reproduce exactly; k and destroyed_pct are "
            "re-derived from the erased record by r1a_rederive()."
        ),
        "kind": "derived",
        "source": (
            "results/phase19_erasure_report.md:17,134,146; results/phase19_arm_erased.json; "
            "REPRO-01 (a9cd408)"
        ),
    },
    "e3_sigmas": {
        "value": E3_SIGMAS,
        "derivation": (
            "E3's noise grid: the sigma = 0 control plus two noised points, each a member of the "
            "v4.0 SIGMA_LADDER."
        ),
        "kind": "preference",
        "source": "RECIPE-01 (a9cd408, reworded c012883, D-17)",
    },
    "mps_ceiling_hours": {
        "value": 90,
        "derivation": "Rafael's ceiling for all v6.0 MPS work, probes included",
        "kind": "preference",
        "source": "COST-02 (a9cd408)",
    },
    "e5_max_set_size": {
        "value": 512,
        "derivation": "RANK-01's upper bound on each minted same-slot set",
        "kind": "preference",
        "source": "RANK-01 (a9cd408)",
    },
}

ENTRIES = types.MappingProxyType(
    {name: types.MappingProxyType(entry) for name, entry in _ENTRIES.items()}
)


def _prove_entries():
    for name, entry in ENTRIES.items():
        _prove_entry(name, entry)


_prove_entries()
