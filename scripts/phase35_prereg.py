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

SLOT REGISTRY (D-02, D-15; Plan 03). ``SLOTS`` declares the 17 thresholds that depend on a later
input, each with its owning phase, its rule (a module-level ``_rule_<slot>`` function whose
docstring states the derivation) and its input records. ``fill(slot, **inputs)`` is the only door:
it refuses an undeclared slot and dispatches ``SLOTS[slot]["rule"]``. Every slot with declared
input records (except ``e1_condition_b_margin``, read in the core, D-16) takes ``input_records``
and a four-field ``derivation`` whose source names every record it read and whose value is the
slot's CALLER-CHOSEN part, stated per rule in its docstring (the filled value where the caller
chooses it, the keys where the rule computes the values from records); ``_consume_inputs`` also
refuses a duplicate input path and a declared input pattern that no consumed path matches,
unless the rule documents that pattern as optional (W3, PREREG-06, review WR-06 / IN-02).

OWNER FILL FILES. An owner fills its slots from one or several files matching
``scripts/phase{owner}_*prereg.py`` (``owner_prereg_glob``), each binding
``<SLOT NAME UPPER-CASED> = phase35_prereg.fill("<slot>", ...)`` at module level after a plain
``import phase35_prereg``. The per-fill-file ordering rule (the planner's reading of D-02 for
multi-step phases, enforced by Plan 04): (a) a slot with no input record of its own phase
precedes every record of that phase; only slots that consume an in-phase input are exempt from
that input, per fill file. A fill file holding any slot without a declared
``results/phase{owner}_*`` input precedes every ``results/phase{owner}_*`` record, and one whose
slots all consume in-phase inputs precedes every such record except those inputs. (b) Each
declared input precedes the first commit of the file that consumes it. A slot is filled exactly
once, anywhere. (c) Once a phase-O record that is not a declared input of ANY phase-O slot is
tracked, every phase-O slot is filled.

THE BUDGET-RECORD CONTRACT. Phase 36 publishes ``results/phase36_budget.json`` holding the
``_rule_v6_budget_and_stop_line`` output keys ``front_hours`` (keyed by ``V6_MPS_FRONTS``),
``total_hours``, ``stop_line_hours`` and ``e2_seed_count`` (int, E2's seed count S, read by
``e2_S``); every consumer re-applies the budget invariants to it (``_budget_record``). THE PHASE 40
NOISE-FLOOR CONTRACT. ``results/phase40_noise_floor.json`` carries ``gap_noise_floor`` (finite >=
0), the NOISE-02 training-seed gap noise floor. THE PHASE 41 BAND-INPUT CONTRACT. Each
``results/phase41_band_inputs_*.json`` carries ``seed`` (an ``e1_teaching_seeds()`` int),
``ordering`` (str) and ``control_gap`` (finite), one record per (seed, ordering). THE PHASE 42
CONTROL-RECORD CONTRACT. Each ``results/phase42_control_*.json`` carries ``recipe`` = {lr, steps,
batch}, ``seed``, ``sigma`` = 0.0 and ``taught_recall`` / ``heldout_recall`` each with
``numerator`` and ``denominator`` (the field shape of the v4.0 point record). THE PHASE 41
CALIBRATION-RECORD CONTRACT. Each ``results/phase41_calibration_*.json`` is keyed by ``(ordering,
seed)`` and carries ``ordering`` (str), ``seed`` (an ``e1_teaching_seeds()`` int, or null for
``(target, ordering)`` floor keys), ``family`` ("A2"), ``corpus`` (the repo-relative path of the
calibration corpus its draws were built from, itself a declared and consumed input of the slot) and
``draws`` (THE ARM'S OWN draws), and NO ``target`` field: one record serves every ``e1_targets()``
of its ``(ordering, seed)``. Every Phase 41 calibration runs on Phase 19's calibration fact,
``phase19_erasure.select_calibration_fact()`` (chosen by rule, reads no result), with the
calibration adapter; the ordering and the stop are computed against that fact and nothing of the
target enters (``phase19_erasure._cmd_cal_erase`` / ``_selected_components`` /
``select_ablation_prefix``). The corpus's ``fact_id`` must be that fact's id and its
``n_questions`` / ``question_counts`` must equal the questions re-derived from the draws (option A
and the (ordering, seed) keying, ruled by Rafael 2026-10-01).

D-04 CLASSIFICATION. e1_alternative_ordering and e6_entry_subset are design choices, but no
decision on record names the alternative ordering and CTX-01's subset exists to fit the Phase 36
budget, so both stay owned by Phases 41 and 39; e1_condition_b_margin is the one slot locked in
the core (D-16).
"""

import collections.abc
import fnmatch
import hashlib
import inspect
import json
import math
import pathlib
import subprocess
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
import phase25_gate05  # noqa: E402  (same; torch-free, no subprocess at import)
import phase25_record  # noqa: E402  (same; torch-free)
import phase26_prereg  # noqa: E402  (same; torch-free, no subprocess at import)
import phase29_prereg  # noqa: E402  (same; torch-free, no subprocess at import)

from personacore.privacy import accountant  # noqa: E402  (src/ on sys.path above; torch-free)

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
    "p22_two_oracle_budget": {
        "value": 1e-9,
        "derivation": (
            "P22's two-oracle agreement budget, |delta_quadrature - delta_closed| <= 1e-9 x "
            "|delta_closed|; WARNING-4/5's region is where it is breached. It is not "
            "delta_quadrature's rel_tol, an integration truncation budget that only shares the "
            "value."
        ),
        "kind": "derived",
        "source": (
            "tests/test_phase22_accountant.py:536; .planning/milestones/v4.0-phases/"
            "22-dp-sgd-core-accountant-and-the-correctness-battery/22-VERIFICATION.md:149-175"
        ),
    },
    "e2_min_seeds": {
        "value": 2,
        "derivation": (
            "A noise floor across training seeds is a spread over seeds, undefined for a single "
            "seed, so S needs at least two."
        ),
        "kind": "derived",
        "source": (
            "NOISE-01/NOISE-02 (.planning/REQUIREMENTS.md, a9cd408); the upper bound is "
            "35-CONTEXT D-06 (36ab0b4)"
        ),
    },
    "e4_inclusion_probability": {
        "value": 0.5,
        "derivation": (
            "Algorithm 1 includes each canary independently with probability 1/2, and Appendix "
            "D's p_value_DP_audit/get_eps_audit, the method D-11 reproduces, assumes it; other "
            "probabilities need Proposition 5.7, which is not reproduced. A different quantity "
            "from F_C."
        ),
        "kind": "derived",
        "source": (
            "arXiv:2305.08846v1 Algorithm 1 p. 3 and Appendix D pp. 45-46, as recorded in "
            "35-RESEARCH.md §PREREG-09 (a); .planning/research/V6-PREREG-09.md"
        ),
    },
    "e4_beta": {
        "value": 0.05,
        "derivation": (
            "The one-sided 95% level: the level Phase 26 used (z = erasure_gate._Z_ONE_SIDED_95, "
            "so beta = 1 - Phi(z)), and the level of both reproduced paper pins (App. D p. 46; "
            "§7 p. 28 with the Fig. 11 caption p. 30), both at beta = 0.05."
        ),
        "kind": "preference",
        "source": (
            "scripts/erasure_gate.py:90 (_Z_ONE_SIDED_95); scripts/phase26_prereg.py:211-214; "
            "arXiv:2305.08846v1 App. D p. 46, §7 p. 28 and Fig. 11 caption p. 30; "
            ".planning/research/V6-PREREG-09.md"
        ),
    },
}

ENTRIES = types.MappingProxyType(
    {name: types.MappingProxyType(entry) for name, entry in _ENTRIES.items()}
)


def _prove_entries():
    for name, entry in ENTRIES.items():
        _prove_entry(name, entry)


_prove_entries()

# =================================================================================================
# (14) THE REGISTRY OF DEFERRED SLOTS (D-02, D-15). After ENTRIES: the rules read ENTRIES at call
# time, and the registry comes last so every rule exists when it is built.
# =================================================================================================

# COST-01's MPS fronts plus the probes; E4 may be budgeted 0 h when the AUDIT-02 rule cuts it.
V6_MPS_FRONTS = ("probes", "R1b", "E1", "E2", "E3", "E4", "E5", "E6")
_BUDGET_RECORD = "results/phase36_budget.json"
_prove(_BUDGET_RECORD in V6_RESULT_PATHS, f"{_BUDGET_RECORD} is not a declared v6.0 record path")
_CALIBRATION_RECORDS = "results/phase41_calibration_*.json"
_prove(_CALIBRATION_RECORDS in V6_RESULT_PATHS, f"{_CALIBRATION_RECORDS} is not a v6.0 record path")
_NOISE_FLOOR_RECORD = "results/phase40_noise_floor.json"
_BAND_INPUT_RECORDS = "results/phase41_band_inputs_*.json"
_prove(_BAND_INPUT_RECORDS in V6_RESULT_PATHS, f"{_BAND_INPUT_RECORDS} is not a v6.0 record path")
# phase19_erasure.CALIBRATION_CORPUS_PATH, repo-relative; typed because phase19_erasure imports
# torch (the test proves the two agree). Write-once since v5.0.
_CALIBRATION_CORPUS = "results/phase19_calibration_corpus.json"

# E3 scope (RECIPE-01, W5): n is the dp_n8 arm's locked-fact count, never typed.
E3_N = len(phase25_gate05.GATE05_SLOTS)
_prove(
    f"dp_n{E3_N}" in phase25_record.DP_ARMS,
    f"E3_N = {E3_N} names no v4.0 DP arm in {phase25_record.DP_ARMS}",
)
E3_UNIT = mitigation_unit.PRIVACY_UNIT
_V4_CONTROL_RECORD = str(
    phase25_record.point_record_path(
        phase25_record.point_key(f"dp_n{E3_N}", E3_SIGMAS[0])
    ).relative_to(_REPO_ROOT)
)
_V5_TAG = "v5.0"


def _is_hex_digest(text):
    """True iff ``text`` is a str of 64 lower-case hex characters."""
    return isinstance(text, str) and len(text) == 64 and all(c in "0123456789abcdef" for c in text)


def _v4_control():
    """The reused v4.0 sigma = 0 control: ``(record, recipe)``, admitted only when byte-identical
    to its copy at tag v5.0.

    What is reused is the control's RECORD (its recall), not the adapter. D-17's "verified by
    SHA-256" is read as the reused record's SHA-256 against tag v5.0, the adapter's own hash being
    carried in the record (``adapter_sha256``); the adapter ``.pt`` is untracked and never hashed.
    ``git show`` runs in the real repository (``-C _SCRIPTS``), so the tag is read from there even
    when a test patches ``_REPO_ROOT``. No caller supplies a digest (W15).
    """
    data = (_REPO_ROOT / _V4_CONTROL_RECORD).read_bytes()
    shown = subprocess.run(
        ["git", "-C", _SCRIPTS, "show", f"{_V5_TAG}:{_V4_CONTROL_RECORD}"],
        capture_output=True,
        check=False,
    )
    _prove(shown.returncode == 0, f"git show {_V5_TAG}:{_V4_CONTROL_RECORD} failed")
    _prove(
        hashlib.sha256(data).hexdigest() == hashlib.sha256(shown.stdout).hexdigest(),
        "the reused v4.0 control record is not byte-identical to its copy at tag v5.0 (D-17: "
        "verified by SHA-256)",
    )
    record = json.loads(data)
    _prove(
        _is_hex_digest(record["adapter_sha256"]),
        "the v4.0 control record carries no 64-hex adapter_sha256",
    )
    tc = record["training"]["train_config"]
    _prove(record["sigma"] == E3_SIGMAS[0], "the v4.0 control record is not at sigma = 0")
    _prove(
        record["canary_population"]["n_facts"] == E3_N,
        f"the v4.0 control record's n_facts is not E3_N = {E3_N}",
    )
    _prove(tc["seed"] == record["seed"], "the v4.0 control's train_config seed is not its seed")
    _prove(
        record["composed_steps"] == tc["max_steps"],
        "the v4.0 control's composed_steps is not its max_steps",
    )
    recipe = types.MappingProxyType(
        {"lr": tc["lr"], "steps": tc["max_steps"], "batch": tc["batch_size"]}
    )
    return record, recipe


SLOT_FIELDS = ("owner_phase", "rule", "input_records")


def owner_prereg_glob(slot):
    """The glob an owner's fill files match: ``scripts/phase{owner}_*prereg.py``."""
    _prove(slot in SLOTS, f"slot {slot!r} is not declared in the Phase 35 registry (D-02)")
    return f"scripts/phase{SLOTS[slot]['owner_phase']}_*prereg.py"


def _prove_finite(name, value):
    _prove_real(name, value)
    _prove(math.isfinite(value), f"{name} is {value!r}, not finite")


class _Filled(collections.abc.Mapping):
    """A read-only mapping that only this module's grid rules construct. ``e1_stop`` and
    ``e3_recall_threshold`` accept a grid iff it is one, so a hand-built dict with the right keys
    is refused (review IN-04)."""

    def __init__(self, data):
        self._data = dict(data)

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)


# `_consume_inputs`'s value for a slot whose value is READ from its records: the rule proves the
# derivation's value against the read value itself (`_prove_derivation_value`).
_READ = object()


def _prove_derivation_value(slot, derivation, value):
    _prove(
        derivation["value"] == value,
        f"{slot}: the derivation's value {derivation['value']!r} is not the slot's chosen value "
        f"{value!r}",
    )


def _consume_inputs(slot, value, input_records, derivation, *, optional=()):
    """W3: prove the written derivation is OF the slot's chosen value (each rule's docstring says
    which part; ``_READ`` defers the check to the rule) and names every input it read; prove each
    input is a declared, existing, repo-relative record, listed once; prove every declared pattern
    not in ``optional`` is matched by a consumed path; return the parsed records."""
    _prove_entry(slot, derivation)
    if value is not _READ:
        _prove_derivation_value(slot, derivation, value)
    _prove(
        isinstance(input_records, tuple)
        and input_records
        and all(isinstance(path, str) for path in input_records),
        f"{slot}: input_records must be a non-empty tuple of str, got {input_records!r}",
    )
    _prove(
        len(set(input_records)) == len(input_records),
        f"{slot}: a duplicate input record in {input_records!r}",
    )
    declared = SLOTS[slot]["input_records"]
    _prove(set(optional) <= set(declared), f"{slot}: optional {optional!r} is not declared")
    for path in input_records:
        pure = pathlib.PurePosixPath(path)
        _prove(
            not pure.is_absolute() and ".." not in pure.parts,
            f"{slot}: input {path!r} is not repo-relative",
        )
        _prove(
            any(fnmatch.fnmatch(path, pat) for pat in declared),
            f"{path!r} is not a declared input of {slot}",
        )
        _prove(path in derivation["source"], f"{slot}: the derivation's source omits {path!r}")
        _prove((_REPO_ROOT / path).is_file(), f"{slot}: input {path!r} does not exist")
    for pat in declared:
        _prove(
            pat in optional or any(fnmatch.fnmatch(path, pat) for path in input_records),
            f"{slot}: the declared input {pat!r} was not consumed",
        )
    return types.MappingProxyType(
        {
            path: json.loads((_REPO_ROOT / path).read_text(encoding="utf-8"))
            for path in input_records
        }
    )


def _prove_budget(front_hours, stop_line_hours, e2_seed_count):
    """The budget's invariants, applied by ``_rule_v6_budget_and_stop_line`` and re-applied to
    the published record by every consumer (review WR-03). Returns the total hours.

    Per-front hours finite >= 0 and keyed by exactly V6_MPS_FRONTS; their fsum <= the stop line
    <= Rafael's MPS ceiling (COST-02: HALT, no front is cut unilaterally); E2's seed count an int
    >= ENTRIES["e2_min_seeds"] and <= len(seed_list()) (D-06: a STOP, the list is never
    extended)."""
    _prove(
        isinstance(front_hours, collections.abc.Mapping) and set(front_hours) == set(V6_MPS_FRONTS),
        f"front_hours must be keyed by exactly V6_MPS_FRONTS {V6_MPS_FRONTS}",
    )
    for front, hours in front_hours.items():
        _prove_finite(f"front_hours[{front!r}]", hours)
        _prove(hours >= 0, f"front_hours[{front!r}] is negative")
    total = math.fsum(front_hours.values())
    _prove_finite("stop_line_hours", stop_line_hours)
    _prove(total <= stop_line_hours, f"the fronts total {total} h, above the stop line")
    _prove(
        stop_line_hours <= ENTRIES["mps_ceiling_hours"]["value"],
        "the fronts do not fit Rafael's MPS ceiling: HALT and take the cut options to Rafael "
        "(COST-02); no front is cut unilaterally",
    )
    _prove_count("e2_seed_count", e2_seed_count)
    _prove(
        e2_seed_count >= ENTRIES["e2_min_seeds"]["value"],
        f"e2_seed_count = {e2_seed_count} is below ENTRIES['e2_min_seeds']",
    )
    _prove(
        e2_seed_count <= len(seed_list()),
        "the Phase 36 probe calls for S > len(seed_list()): STOP and ask Rafael (D-06); the seed "
        "list is never extended",
    )
    return total


def _budget_record(records):
    """The consumed Phase 36 budget record, re-validated (``_prove_budget``) with its published
    ``total_hours`` equal to the fsum of its fronts."""
    _prove(_BUDGET_RECORD in records, f"{_BUDGET_RECORD} was not consumed")
    record = records[_BUDGET_RECORD]
    fields = {"front_hours", "total_hours", "stop_line_hours", "e2_seed_count"}
    _prove(
        isinstance(record, collections.abc.Mapping) and fields <= set(record),
        f"the budget record must carry {sorted(fields)}",
    )
    total = _prove_budget(record["front_hours"], record["stop_line_hours"], record["e2_seed_count"])
    _prove(
        record["total_hours"] == total,
        f"the budget record's total_hours {record['total_hours']!r} is not its fronts' sum {total}",
    )
    return record


def _budget_front_hours(records, front):
    """The hours the re-validated Phase 36 budget record gives ``front``."""
    return _budget_record(records)["front_hours"][front]


# P22's onset (RECIPE-04, W4).


def _p22_breached(sigma, steps):
    """True iff P22's two oracles disagree beyond ``ENTRIES["p22_two_oracle_budget"]`` at
    eps = ``epsilon_for(sigma, steps, DELTA)``, relative to ``delta_closed`` (W13: never
    ``delta_quadrature``'s ``rel_tol`` default, an integration truncation budget)."""
    eps = accountant.epsilon_for(sigma, steps, DELTA)
    mu = math.sqrt(steps) / sigma
    closed = accountant.delta_closed(eps, mu)
    budget = ENTRIES["p22_two_oracle_budget"]["value"]
    return abs(accountant.delta_quadrature(eps, mu) - closed) / closed > budget


def p22_onset_sigma(steps):
    """The P22 WARNING-4/5 onset at T = ``steps``: the boundary of the small-sigma region where
    ``|delta_quadrature - delta_closed| / delta_closed`` exceeds P22's two-oracle budget
    ``ENTRIES["p22_two_oracle_budget"]`` (the assertion at tests/test_phase22_accountant.py:536),
    sigma swept at fixed T and delta = DELTA, as 22-VERIFICATION.md:149-183 (WARNING-5) defines
    it. The error is monotone in mu (:163), so the region is sigma <= onset. Bracketed, then 30
    bisection steps; returns the smallest sigma known to lie OUTSIDE the region.
    ``p22_onset_sigma(STEP_BUDGET)`` reproduces P22's bisected 0.078902 (:175).
    """
    _prove_count("steps", steps)
    _prove(steps >= 1, f"steps is {steps}; need >= 1")
    hi = min(s for s in E3_SIGMAS if s > 0)
    for _ in range(64):
        if not _p22_breached(hi, steps):
            break
        hi *= 2
    _prove(not _p22_breached(hi, steps), f"no unbreached sigma within 64 doublings at T={steps}")
    lo = hi / 2
    for _ in range(64):
        if _p22_breached(lo, steps):
            break
        lo /= 2
    _prove(_p22_breached(lo, steps), f"no breached sigma within 64 halvings at T={steps}")
    for _ in range(30):
        mid = (lo + hi) / 2
        if _p22_breached(mid, steps):
            lo = mid
        else:
            hi = mid
    return hi


# ERASE-07's outcome when no checkpoint confirms zero at K = FULL_FIDELITY_K. Not a verdict: it is
# proved distinct from every verdict an E1 cell could be read against.
NOT_REACHED = "NOT_REACHED"
_prove(
    NOT_REACHED
    not in (
        *erasure_gate.VERDICTS,
        *mitigation_gate.V4_VERDICTS,
        *phase29_prereg.VERDICTS,
        phase29_prereg.REFUSED,
    ),
    "NOT_REACHED collides with a verdict string; it must never count as PASS nor as FAIL",
)


def e1_stop(*, grid, readings):
    """ERASE-07's stop. ``grid`` is the ``fill("e1_checkpoint_grid", ...)`` result; ``readings``
    maps each checkpoint, in grid order and read until the stop, to ``{"curve_k_zero": bool,
    "full_fidelity_k_zero": bool | None}``: the K = CURVE_K read, and the K = FULL_FIDELITY_K
    confirmation, present iff the CURVE_K read is zero. The stop is the first checkpoint whose
    CURVE_K read is zero AND whose confirmation is zero; a non-zero confirmation continues to the
    next checkpoint. When no checkpoint confirms zero at FULL_FIDELITY_K the cell records
    ``NOT_REACHED``: it receives no (b) or (c) verdict at a stopping point and never counts as PASS
    nor as FAIL. Returns ``{"stop": <checkpoint> or NOT_REACHED, "judged": bool}``, ``judged``
    False exactly for NOT_REACHED. Malformed readings are refused."""
    _prove(
        isinstance(grid, _Filled)
        and set(grid) == {"checkpoints", "read_k", "confirm_k", "not_reached"},
        "grid must be the fill('e1_checkpoint_grid', ...) result",
    )
    checkpoints = grid["checkpoints"]
    _prove(isinstance(readings, collections.abc.Mapping), "readings must be a mapping")
    _prove(
        set(readings) <= set(checkpoints),
        f"readings for checkpoints outside the grid: {sorted(set(readings) - set(checkpoints))}",
    )
    for index, checkpoint in enumerate(checkpoints):
        _prove(checkpoint in readings, f"checkpoint {checkpoint} has no reading before the stop")
        reading = readings[checkpoint]
        _prove(
            isinstance(reading, collections.abc.Mapping)
            and set(reading) == {"curve_k_zero", "full_fidelity_k_zero"},
            f"reading {checkpoint} must have exactly curve_k_zero and full_fidelity_k_zero",
        )
        curve, confirm = reading["curve_k_zero"], reading["full_fidelity_k_zero"]
        _prove(isinstance(curve, bool), f"reading {checkpoint}: curve_k_zero is not a bool")
        if not curve:
            _prove(
                confirm is None,
                f"reading {checkpoint}: a FULL_FIDELITY_K confirmation without a zero CURVE_K read",
            )
            continue
        _prove(
            isinstance(confirm, bool),
            f"reading {checkpoint}: a zero CURVE_K read without its FULL_FIDELITY_K confirmation",
        )
        if confirm:
            _prove(
                set(readings) == set(checkpoints[: index + 1]),
                f"readings past the stop at checkpoint {checkpoint}",
            )
            return types.MappingProxyType({"stop": checkpoint, "judged": True})
    return types.MappingProxyType({"stop": NOT_REACHED, "judged": False})


def _frozen_entry(name, entry):
    """A design slot's written entry, proved (D-14) and returned as a read-only copy, its value
    copied and frozen too when it is a mapping, so neither the caller's later edits nor a holder
    of the result can change it after the fill (review WR-04)."""
    _prove_entry(name, entry)
    frozen = dict(entry)
    if isinstance(frozen["value"], collections.abc.Mapping):
        frozen["value"] = types.MappingProxyType(dict(frozen["value"]))
    return types.MappingProxyType(frozen)


# The 17 rules. Keyword-only; every refusal goes through _prove; every container returned is
# read-only.


def _rule_v6_budget_and_stop_line(
    *, front_hours, stop_line_hours, e2_seed_count, input_records, derivation
):
    """COST-02: the per-front MPS hours, their total, the stop line and E2's seed count S, derived
    from the Phase 36 probes. ``_prove_budget`` refuses a total above the stop line, a stop line
    above Rafael's MPS ceiling (HALT: no front is cut unilaterally) and an S outside
    e2_min_seeds..len(seed_list()) (D-06 STOP). The output keys ``front_hours``, ``total_hours``,
    ``stop_line_hours`` and ``e2_seed_count`` are what Phase 36 publishes as
    ``results/phase36_budget.json``. Derivation value: the caller-chosen part,
    ``{"front_hours", "stop_line_hours", "e2_seed_count"}`` (the total is computed).
    """
    total = _prove_budget(front_hours, stop_line_hours, e2_seed_count)
    chosen = {
        "front_hours": dict(front_hours),
        "stop_line_hours": stop_line_hours,
        "e2_seed_count": e2_seed_count,
    }
    _consume_inputs("v6_budget_and_stop_line", chosen, input_records, derivation)
    return types.MappingProxyType(
        {
            "front_hours": types.MappingProxyType(dict(front_hours)),
            "total_hours": total,
            "stop_line_hours": stop_line_hours,
            "e2_seed_count": e2_seed_count,
        }
    )


def _rule_e2_S(*, input_records, derivation, s=None):
    """D-06, NOISE-01: E2's seed count S, READ from the consumed budget record's ``e2_seed_count``
    (review WR-03), never typed: the caller supplies no S, and a supplied S that differs from the
    read one is refused. The re-validated record keeps S >= ENTRIES["e2_min_seeds"] (a spread
    needs two seeds) and S <= len(seed_list()), a STOP because the seed list is never extended
    (D-06). Derivation value: S as read."""
    if s is not None:
        _prove_count("s", s)
    records = _consume_inputs("e2_S", _READ, input_records, derivation)
    record = _budget_record(records)
    _prove(record["front_hours"]["E2"] > 0, "the Phase 36 budget gives E2 no MPS hours")
    read = record["e2_seed_count"]
    _prove(s is None or s == read, f"S is read from the budget record ({read}), not typed ({s})")
    _prove_derivation_value("e2_S", derivation, read)
    return read


def _rule_r1b_tolerance_and_replicated(*, tolerance, replicated_definition):
    """REPRO-03: R1b's per-assertion tolerance (keys among R1A_ASSERTIONS, finite >= 0) and the
    written definition of "replicated", settled in Phase 37's discuss before measurement."""
    _prove(
        isinstance(tolerance, collections.abc.Mapping)
        and tolerance
        and set(tolerance) <= set(R1A_ASSERTIONS),
        f"tolerance must be a non-empty mapping keyed among {sorted(R1A_ASSERTIONS)}",
    )
    for key, value in tolerance.items():
        _prove_finite(f"tolerance[{key!r}]", value)
        _prove(value >= 0, f"tolerance[{key!r}] is negative")
    return types.MappingProxyType(
        {
            "tolerance": types.MappingProxyType(dict(tolerance)),
            "replicated_definition": _frozen_entry("replicated_definition", replicated_definition),
        }
    )


def _rule_e1_checkpoint_grid(*, checkpoints, input_records, derivation):
    """ERASE-07: the ablation-prefix checkpoints, strictly increasing counts >= 1, funded by the
    Phase 36 budget. Each checkpoint is read with A2 at K = CURVE_K; the first zero is confirmed
    at K = FULL_FIDELITY_K; a non-zero confirmation continues to the next checkpoint; the rank
    never enters the stopping rule and is recorded at every checkpoint. When no checkpoint
    confirms zero at K = FULL_FIDELITY_K the cell records ``NOT_REACHED`` (``e1_stop``): no (b) or
    (c) verdict at a stopping point, and it never counts as PASS nor as FAIL. Derivation value:
    the checkpoints (caller-chosen). Returns a ``_Filled`` grid, the only kind ``e1_stop`` takes."""
    _prove(isinstance(checkpoints, tuple) and checkpoints, "checkpoints must be a non-empty tuple")
    for value in checkpoints:
        _prove_count("checkpoint", value)
        _prove(value >= 1, f"checkpoint {value} is below 1")
    _prove(
        all(a < b for a, b in zip(checkpoints, checkpoints[1:])),
        f"checkpoints {checkpoints} are not strictly increasing",
    )
    records = _consume_inputs("e1_checkpoint_grid", checkpoints, input_records, derivation)
    _prove(_budget_front_hours(records, "E1") > 0, "the Phase 36 budget gives E1 no MPS hours")
    return _Filled(
        {
            "checkpoints": checkpoints,
            "read_k": CURVE_K,
            "confirm_k": FULL_FIDELITY_K,
            "not_reached": NOT_REACHED,
        }
    )


def _prove_cells_cover_targets(name, floors):
    """Review WR-02: the keys are exactly e1_targets() x the (ordering[, seed]) cells that appear,
    with one key length per ordering."""
    cells = {key[1:] for key in floors}
    _prove(
        set(floors) == {(target, *cell) for target in e1_targets() for cell in cells},
        f"{name}: every (ordering[, seed]) cell needs a key for every e1 target",
    )
    for ordering in {cell[0] for cell in cells}:
        _prove(
            len({len(cell) for cell in cells if cell[0] == ordering}) == 1,
            f"{name}: ordering {ordering!r} mixes seeded and unseeded keys",
        )


def _rule_e1_condition_a_floors(*, floors, input_records, derivation):
    """ERASE-06: condition (a)'s floors, one per (target, ordering[, seed]) key, covering every E1
    target. The floor is COMPUTED, never typed: the caller supplies only the keys (each value
    ``None``); a supplied number that differs from the computed floor is refused.

    CALIBRATION IS KEYED BY (ordering, seed), NOT BY TARGET (Rafael 2026-10-01). The calibration
    runs on ``phase19_erasure.select_calibration_fact()`` with the calibration adapter; the ordering
    and the stop are computed against that fact, and nothing of the target enters
    (``phase19_erasure._cmd_cal_erase`` -> ``_selected_components`` -> ``select_ablation_prefix``:
    ``ordered`` and ``k`` read only the fact's slot, value and references; ``collateral`` is the
    same for every target and is re-scored only after ``k`` is fixed). So one calibration record
    serves every ``e1_targets()`` of its (ordering, seed): exactly one record per (ordering, seed),
    no ``target`` field, a key with no record or a record serving no key refused. This holds by
    construction only while the ordering is a rule over the fact being erased; the alternative
    ordering (``e1_alternative_ordering``, D-04 deferred to Phase 41) must be one too, since an
    ordering that read the target would need a calibration per target.

    THE CORPUS IS A DECLARED INPUT. Each record's ``corpus`` must be a consumed input of this slot
    (so it matches a declared pattern, exists and is named in the derivation's source); a consumed
    corpus no record names is refused. Under option A the one declared corpus is Phase 19's
    write-once calibration corpus, the corpus of ``select_calibration_fact()``.

    The rate is the defect-B correction's route (results/phase19_calibration_correction.json
    ``evidence.re_derivation``), on THE ARM'S OWN draws: values ``{fact.id: fact.value}``,
    ``phase19_erasure.per_fact_rows(draws, values, family="A2", tier=tier)`` once per tier of
    ``phase18_extraction.CORPUS_TIERS``, successes / questions pooled; never Phase 19's
    ``_calibration_rate`` (defect B). The floor is ``phase19_erasure.lock_erasure_floor(rate)``,
    its branch ``phase19_erasure.floor_branch(rate)``, computed once per record.

    The reachability clamp sits on the 27-question TARGET denominator: ``ERASURE_FLOOR_MIN`` is
    ``wilson_upper_bound(0, N_TARGET_QUESTIONS)``, 27 = 14 core_taught + 13 core_held_out per
    target, proved here; the test measures that every e1 target pools to those 27 questions.
    Coverage is per cell (review WR-02): every (ordering[, seed]) that appears has a key for
    every e1 target, and one ordering never mixes seeded and unseeded keys. Derivation value: the
    keys (the floors are computed). Returns (target, ordering[, seed]) -> {floor, floor_branch,
    calibration_rate, calibration_successes, calibration_questions, calibration_record},
    read-only.
    """
    _prove(isinstance(floors, collections.abc.Mapping) and floors, "floors must be a mapping")
    teaching = e1_teaching_seeds()
    for key, supplied in floors.items():
        _prove(isinstance(key, tuple) and len(key) in (2, 3), f"floor key {key!r} malformed")
        _prove(isinstance(key[1], str) and key[1], f"floor key {key!r} has no ordering")
        if len(key) == 3:
            _prove_count("floor key seed", key[2])
            _prove(key[2] in teaching, f"floor key {key!r}: seed not in e1_teaching_seeds()")
        if supplied is not None:
            _prove_finite(f"supplied floor {key!r}", supplied)
    _prove_cells_cover_targets("floors", floors)
    records = _consume_inputs("e1_condition_a_floors", tuple(floors), input_records, derivation)
    calibrations = {p: r for p, r in records.items() if fnmatch.fnmatch(p, _CALIBRATION_RECORDS)}
    corpora = {p: r for p, r in records.items() if p not in calibrations}

    import phase18_extraction  # torch at import: lazy
    import phase19_erasure  # torch at import: lazy

    _prove(
        phase19_erasure.ERASURE_FLOOR_MIN
        == erasure_gate.wilson_upper_bound(0, phase19_erasure.N_TARGET_QUESTIONS),
        "the reachability clamp no longer sits on the 27-question target denominator",
    )
    fact = phase19_erasure.select_calibration_fact()
    values = {fact.id: fact.value}
    path_of = {}
    for path, record in calibrations.items():
        _prove(
            "target" not in record,
            f"{path} carries a target field: a calibration is keyed by (ordering, seed) and "
            "serves every target",
        )
        _prove(
            record["corpus"] in corpora,
            f"{path}: corpus {record['corpus']!r} is not a consumed input of this slot",
        )
        cal_key = (record["ordering"],)
        if record["seed"] is not None:
            _prove_count(f"{path} seed", record["seed"])
            cal_key += (record["seed"],)
        _prove(cal_key not in path_of, f"two calibration records for (ordering, seed) {cal_key!r}")
        path_of[cal_key] = path
    named = {record["corpus"] for record in calibrations.values()}
    _prove(
        set(corpora) <= named, f"consumed corpora no record names: {sorted(set(corpora) - named)}"
    )
    wanted = {key[1:] for key in floors}
    _prove(
        wanted <= set(path_of),
        f"(ordering, seed) without a calibration record: {sorted(wanted - set(path_of), key=repr)}",
    )
    _prove(
        set(path_of) <= wanted,
        f"calibration records serving no floor: {sorted(set(path_of) - wanted, key=repr)}",
    )
    measured = {}
    for path, record in calibrations.items():
        _prove(record["family"] == "A2", f"{path}: family {record['family']!r} is not A2")
        corpus = corpora[record["corpus"]]
        _prove(
            corpus["fact_id"] == fact.id,
            f"{path}: the corpus is for {corpus['fact_id']!r} but the calibration fact is "
            f"{fact.id!r}; the draws and the scoring would be about different facts",
        )
        successes = questions = 0
        for tier in phase18_extraction.CORPUS_TIERS:
            rows = phase19_erasure.per_fact_rows(
                record["draws"], values, family=record["family"], tier=tier
            )
            _prove(fact.id in rows, f"{path}: no {tier} row for {fact.id!r}")
            row = rows[fact.id]
            _prove(
                row["n_questions"] == corpus["question_counts"][tier],
                f"{path}: {tier} re-derives {row['n_questions']} questions, the corpus declares "
                f"{corpus['question_counts'][tier]}",
            )
            successes += row["n_answerable"]
            questions += row["n_questions"]
        _prove(questions > 0, f"{path}: no calibration question")
        _prove(
            questions == corpus["n_questions"],
            f"{path}: {questions} pooled questions, the corpus declares {corpus['n_questions']}",
        )
        rate = successes / questions
        measured[path] = types.MappingProxyType(
            {
                "floor": phase19_erasure.lock_erasure_floor(rate),
                "floor_branch": phase19_erasure.floor_branch(rate),
                "calibration_rate": rate,
                "calibration_successes": successes,
                "calibration_questions": questions,
                "calibration_record": path,
            }
        )
    computed = {}
    for key, supplied in floors.items():
        row = measured[path_of[key[1:]]]
        _prove(
            supplied is None or supplied == row["floor"],
            f"floor {key!r}: supplied {supplied!r}, computed {row['floor']!r}; the floor is "
            "computed",
        )
        computed[key] = row
    return types.MappingProxyType(computed)


def _rule_e1_alternative_ordering(*, ordering):
    """ERASE-04, D-04 deferred to Phase 41: the alternative ablation ordering, a written entry
    whose value is a non-empty str, returned read-only."""
    frozen = _frozen_entry("e1_alternative_ordering", ordering)
    _prove(
        isinstance(frozen["value"], str) and frozen["value"],
        "the alternative ordering's value must be a non-empty str",
    )
    return frozen


def _rule_e3_grid_subset(*, recipes, seed, input_records, derivation, fifth_recipe_derivation=None):
    """RECIPE-01, RECIPE-04, D-17, W5, W15: E3's grid, recipes x E3_SIGMAS at n = E3_N and the
    unit E3_UNIT, ONE seed for the whole grid (every recipe's sigma = 0 control shares its noised
    points' seed). Exactly 4 recipes; 5 only when the reused v4.0 sigma = 0 cell exists (the v4.0
    recipe at the v4.0 control record's own seed, that record consumed as a declared input,
    byte-identical to tag v5.0) AND a fifth-recipe derivation cites the Phase 36 budget record
    (B4). Refused before any training when a noised sigma is at or below P22's onset for any T
    the grid uses (RECIPE-04). The v4.0 control record is an OPTIONAL declared input: consumed
    exactly when reused. Derivation value: the recipes (caller-chosen). Returns a ``_Filled`` grid,
    the only kind ``e3_recall_threshold`` takes."""
    _prove(isinstance(recipes, tuple) and recipes, "recipes must be a non-empty tuple")
    for recipe in recipes:
        _prove(
            isinstance(recipe, collections.abc.Mapping) and set(recipe) == {"lr", "steps", "batch"},
            f"recipe {recipe!r} must have exactly the keys lr, steps, batch",
        )
        _prove_finite("lr", recipe["lr"])
        _prove(recipe["lr"] > 0, f"recipe {dict(recipe)} has lr <= 0")
        for name in ("steps", "batch"):
            _prove_count(name, recipe[name])
            _prove(recipe[name] >= 1, f"recipe {dict(recipe)} has {name} < 1")
    plain = [dict(recipe) for recipe in recipes]
    _prove(
        all(plain[i] != plain[j] for i in range(len(plain)) for j in range(i)),
        "the grid repeats a recipe",
    )
    _prove_count("seed", seed)
    _prove(seed in seed_list(), f"seed {seed!r} is not in seed_list()")
    records = _consume_inputs(
        "e3_grid_subset", recipes, input_records, derivation, optional=(_V4_CONTROL_RECORD,)
    )
    _prove(_budget_front_hours(records, "E3") > 0, "the Phase 36 budget gives E3 no MPS hours")

    import teach_persona  # torch at import: lazy

    v4_recipe = {"lr": teach_persona.LR, "steps": STEP_BUDGET, "batch": teach_persona.BATCH_SIZE}
    reused = False
    if v4_recipe in plain:
        v4_record, recorded = _v4_control()
        _prove(dict(recorded) == v4_recipe, "the v4.0 control record did not run the v4.0 recipe")
        reused = seed == v4_record["seed"]
    if reused:
        _prove(
            _V4_CONTROL_RECORD in input_records,
            "the reused v4.0 control must be consumed as a declared input (D-17)",
        )
    else:
        _prove(
            _V4_CONTROL_RECORD not in input_records,
            "a v4.0 control consumed without an admissible reuse",
        )
    if len(recipes) == 4:
        _prove(fifth_recipe_derivation is None, "a fifth-recipe derivation on a 4-recipe grid")
    else:
        _prove(len(recipes) == 5, f"E3's grid has {len(recipes)} recipes; 4, or 5 with a reuse")
        _prove(
            reused,
            "the saved run funds a 5th recipe only if it fits the Phase 36 budget; no reused "
            "control, no saved run",
        )
        _prove_entry("fifth_recipe_derivation", fifth_recipe_derivation)
        _prove(
            _BUDGET_RECORD in fifth_recipe_derivation["source"],
            f"the fifth-recipe derivation does not cite {_BUDGET_RECORD}",
        )
    onsets = {}
    for steps in sorted({recipe["steps"] for recipe in recipes} | {STEP_BUDGET}):
        onset = p22_onset_sigma(steps)
        _prove(
            all(s > onset for s in E3_SIGMAS if s > 0),
            f"the grid crosses the P22 WARNING-4/5 region at T={steps} (onset {onset}): refused "
            "before any training (RECIPE-04)",
        )
        onsets[steps] = onset
    cells = tuple(
        types.MappingProxyType(
            {
                "recipe": types.MappingProxyType(recipe),
                "sigma": sigma,
                "seed": seed,
                "n": E3_N,
                "reuse": _V4_CONTROL_RECORD
                if reused and recipe == v4_recipe and sigma == E3_SIGMAS[0]
                else None,
            }
        )
        for recipe in plain
        for sigma in E3_SIGMAS
    )
    return _Filled(
        {
            "cells": cells,
            "p22_onset_sigma": types.MappingProxyType(onsets),
            "n": E3_N,
            "unit": E3_UNIT,
        }
    )


def _rule_e3_recall_threshold(*, grid, input_records, derivation):
    """RECIPE-03, D-17, W14: the utility threshold of every grid recipe, F_Y x THAT recipe's
    sigma = 0 control recall on each leg (taught, held-out), or ``phase29_prereg.REFUSED`` when
    ``phase29_prereg.control_is_unlearnable`` holds. One control per recipe, keyed by the recipe
    (lr, steps, batch, seed) READ FROM ITS RECORD, never from the caller and never by position; the
    key set must equal the grid's. The reused v4.0 record is consumed exactly when the grid reuses
    it, and admitted only byte-identical to tag v5.0 (an OPTIONAL declared input: consumed exactly
    when reused). Derivation value: the tuple of grid recipe keys (lr, steps, batch, seed) it
    thresholds, in grid order (review WR-06; never the input paths)."""
    _prove(
        isinstance(grid, _Filled) and set(grid) == {"cells", "p22_onset_sigma", "n", "unit"},
        "grid must be the fill('e3_grid_subset', ...) result",
    )
    chosen = tuple(
        dict.fromkeys(
            (c["recipe"]["lr"], c["recipe"]["steps"], c["recipe"]["batch"], c["seed"])
            for c in grid["cells"]
        )
    )
    wanted = set(chosen)
    records = _consume_inputs(
        "e3_recall_threshold",
        chosen,
        input_records,
        derivation,
        optional=(_V4_CONTROL_RECORD,),
    )
    keys = []
    for path, record in records.items():
        if path == _V4_CONTROL_RECORD:
            v4_record, recorded = _v4_control()
            key = (recorded["lr"], recorded["steps"], recorded["batch"], v4_record["seed"])
        else:
            _prove(record["sigma"] == E3_SIGMAS[0], f"control {path} is not at sigma = 0")
            recipe = record["recipe"]
            key = (recipe["lr"], recipe["steps"], recipe["batch"], record["seed"])
        keys.append((key, path))
    _prove(
        len({key for key, _ in keys}) == len(keys) and {key for key, _ in keys} == wanted,
        "a control keyed to a recipe outside the grid, or a grid recipe without its own control, "
        "is refused (D-17)",
    )
    _prove(
        (_V4_CONTROL_RECORD in records) == any(c["reuse"] for c in grid["cells"]),
        "the reused v4.0 control must be the one consumed, and only when the grid reuses it",
    )
    thresholds = {}
    for key, path in keys:
        record = records[path]
        tk, tn = record["taught_recall"]["numerator"], record["taught_recall"]["denominator"]
        hk, hn = record["heldout_recall"]["numerator"], record["heldout_recall"]["denominator"]
        if phase29_prereg.control_is_unlearnable(tk, tn, hk, hn):
            thresholds[key] = phase29_prereg.REFUSED
        else:
            thresholds[key] = types.MappingProxyType(
                {"control": path, "taught": F_Y * tk / tn, "heldout": F_Y * hk / hn}
            )
    return types.MappingProxyType(thresholds)


def _rule_e4_parameters(
    *, m, inclusion_probability, k_plus, k_minus, beta, input_records, derivation
):
    """AUDIT-01, D-11: E4's one-run parameters and its maximum detectable epsilon, computed ONLY
    when the port reproduces the published values. Inclusion probability is
    ``ENTRIES["e4_inclusion_probability"]`` (Algorithm 1); beta is ``ENTRIES["e4_beta"]``, any
    other beta refused. The ceiling is
    ``eps_lower_one_run(m, r, r, DELTA, beta)`` with r = k_plus + k_minus (a perfect guesser),
    and ``runs`` is ``e4_runs(ceiling)`` (AUDIT-02). Counts (review WR-01): m >= 1 and k_plus,
    k_minus >= 0 each with r >= 1: Algorithm 1 guesses "included" for the k+ highest scores and
    "excluded" for the k- lowest, so each is a count of guesses on one side and zero on one side
    is a well-defined one-sided guesser; Theorem 5.2's bound reads only r and v. Derivation
    value: ``{"m", "k_plus", "k_minus"}`` (caller-chosen; beta and the inclusion probability are
    entries)."""
    _prove(
        one_run_reproduction_holds(),
        "D-11: the published Steinke-Nasr-Jagielski values are not reproduced; the AUDIT-01 "
        "ceiling is not computed and E4 does not advance",
    )
    for name, value in (("m", m), ("k_plus", k_plus), ("k_minus", k_minus)):
        _prove_count(name, value)
        _prove(value >= 0, f"{name} is {value}; a count is >= 0")
    _prove(m >= 1, f"m is {m}; at least one canary is needed")
    r = k_plus + k_minus
    _prove(1 <= r <= m, f"need 1 <= k_plus + k_minus <= m, got r={r}, m={m}")
    _prove_real("inclusion_probability", inclusion_probability)
    _prove(
        inclusion_probability == ENTRIES["e4_inclusion_probability"]["value"],
        f"inclusion_probability {inclusion_probability!r} is not Algorithm 1's",
    )
    _prove_finite("beta", beta)
    _prove(
        beta == ENTRIES["e4_beta"]["value"],
        f"beta is {beta!r}, not ENTRIES['e4_beta'] (the one-sided 95% level)",
    )
    _consume_inputs(
        "e4_parameters",
        {"m": m, "k_plus": k_plus, "k_minus": k_minus},
        input_records,
        derivation,
    )
    ceiling = eps_lower_one_run(m, r, r, DELTA, beta)
    return types.MappingProxyType(
        {
            "m": m,
            "inclusion_probability": inclusion_probability,
            "k_plus": k_plus,
            "k_minus": k_minus,
            "beta": beta,
            "delta": DELTA,
            "ceiling": ceiling,
            "runs": e4_runs(ceiling),
        }
    )


def _rule_e5_minting_rule(*, minting_rule):
    """RANK-01, W16: the written minting rule. It has no input record, and a slot with no input
    record of its own phase precedes every record of that phase; only slots that consume an
    in-phase input are exempt from that input, per fill file (Plan 04 leg (a), B7). So its fill
    file precedes the minting record, it cannot share a fill file with e5_set_sizes (which
    consumes that record), and the rule cannot be fitted to what was minted."""
    return _frozen_entry("e5_minting_rule", minting_rule)


def _rule_e5_set_sizes(*, set_sizes, input_records, derivation):
    """RANK-01, W16: each minted same-slot set's size, 1..ENTRIES["e5_max_set_size"], read from
    the minting record; declared after minting ("as far as minting allows") and before any
    scoring. Derivation value: the set sizes (caller-chosen)."""
    _prove(
        isinstance(set_sizes, collections.abc.Mapping) and set_sizes,
        "set_sizes must be a non-empty mapping",
    )
    for name, size in set_sizes.items():
        _prove(isinstance(name, str) and name, f"set name {name!r} is not a non-empty str")
        _prove_count(f"set_sizes[{name!r}]", size)
        _prove(
            1 <= size <= ENTRIES["e5_max_set_size"]["value"],
            f"set_sizes[{name!r}] = {size} is outside 1..e5_max_set_size",
        )
    _consume_inputs("e5_set_sizes", set_sizes, input_records, derivation)
    return types.MappingProxyType(dict(set_sizes))


def _rule_e6_entry_subset(*, entry_indices, input_records, derivation):
    """CTX-01, D-04 deferred to Phase 39: the A2 corpus entries E6 runs on, strictly increasing
    indices into ``a2_corpus_entries()``, sized to fit the Phase 36 budget. Derivation value: the
    entry indices (caller-chosen)."""
    _prove(
        isinstance(entry_indices, tuple) and entry_indices,
        "entry_indices must be a non-empty tuple",
    )
    size = len(a2_corpus_entries())
    for index in entry_indices:
        _prove_count("entry index", index)
        _prove(0 <= index < size, f"entry index {index} is outside the {size} A2 entries")
    _prove(
        all(a < b for a, b in zip(entry_indices, entry_indices[1:])),
        f"entry_indices {entry_indices} are not strictly increasing",
    )
    _consume_inputs("e6_entry_subset", entry_indices, input_records, derivation)
    return entry_indices


def _rule_e1_condition_b_margin():
    """D-16: locked in the core. Condition (b)'s margin is ``e1_condition_b_margin()``, the read
    of results/phase19_noise_floors.json::margin_at_gate; it takes no input."""
    return e1_condition_b_margin()


def _rule_e1_condition_c_band_inputs(*, band_inputs, input_records, derivation):
    """ERASE-09: condition (c)'s band per (seed, ordering), DIALOGUE_GAP_BAND applied to the
    control gap and the Phase 40 gap noise floor, both READ from records, never typed (review
    CR-01, Rafael 2026-10-01, the floors pattern).

    ``band_inputs`` is keyed by (seed, ordering), seed an ``e1_teaching_seeds()`` int and ordering
    a non-empty str, covering every e1 teaching seed for each ordering that appears (ERASE-10: no
    E1 PASS without the second seed's run). Each value is ``None`` (the caller supplies only the
    keys) or a supplied ``{"control_gap", "gap_noise_floor"}`` pair, refused unless equal to the
    read pair. ``control_gap`` is read from the cell's ``results/phase41_band_inputs_*.json``
    (``seed``, ``ordering``, ``control_gap``; one record per (seed, ordering): a duplicate, an
    orphan or a missing record is refused); ``gap_noise_floor`` from
    ``results/phase40_noise_floor.json`` (``gap_noise_floor``, finite >= 0, NOISE-02). Both
    declared patterns must be consumed and named in the derivation's source (``_consume_inputs``).
    Derivation value: the keys.
    """
    _prove(
        isinstance(band_inputs, collections.abc.Mapping) and band_inputs,
        "band_inputs must be a non-empty mapping",
    )
    teaching = e1_teaching_seeds()
    for key, supplied in band_inputs.items():
        _prove(
            isinstance(key, tuple) and len(key) == 2, f"band key {key!r} is not (seed, ordering)"
        )
        _prove_count("band key seed", key[0])
        _prove(key[0] in teaching, f"band key {key!r}: seed not in e1_teaching_seeds()")
        _prove(isinstance(key[1], str) and key[1], f"band key {key!r} has no ordering")
        if supplied is not None:
            _prove(
                isinstance(supplied, collections.abc.Mapping)
                and set(supplied) == {"control_gap", "gap_noise_floor"},
                f"band inputs {key!r} must be None or exactly control_gap and gap_noise_floor",
            )
    orderings = {key[1] for key in band_inputs}
    _prove(
        set(band_inputs) == {(seed, o) for seed in teaching for o in orderings},
        "every ordering needs a band for every e1 teaching seed",
    )
    records = _consume_inputs(
        "e1_condition_c_band_inputs", tuple(band_inputs), input_records, derivation
    )
    noise = records[_NOISE_FLOOR_RECORD]
    gap_noise_floor = noise["gap_noise_floor"]
    _prove_finite("gap_noise_floor", gap_noise_floor)
    _prove(gap_noise_floor >= 0, "the Phase 40 gap noise floor is negative")
    control = {}
    for path, record in records.items():
        if path == _NOISE_FLOOR_RECORD:
            continue
        _prove_count(f"{path} seed", record["seed"])
        key = (record["seed"], record["ordering"])
        _prove(key not in control, f"two band-input records for (seed, ordering) {key!r}")
        _prove(key in band_inputs, f"band-input record {path} serves no key: {key!r}")
        _prove_finite(f"{path} control_gap", record["control_gap"])
        control[key] = record["control_gap"]
    _prove(
        set(control) == set(band_inputs),
        f"(seed, ordering) without a band-input record: "
        f"{sorted(set(band_inputs) - set(control), key=repr)}",
    )
    bands = {}
    for key, supplied in band_inputs.items():
        read = {"control_gap": control[key], "gap_noise_floor": gap_noise_floor}
        _prove(
            supplied is None or dict(supplied) == read,
            f"band inputs {key!r}: supplied {dict(supplied or {})!r}, read {read!r}; they are read",
        )
        bands[key] = DIALOGUE_GAP_BAND(**read)
    return types.MappingProxyType(bands)


def _rule_e2_noise_floor_estimator(*, estimator):
    """NOISE-02: the written estimator of the training-seed noise floor, published beside v3.0's
    sampling floor, never amending the (b) margin (D-16)."""
    return _frozen_entry("e2_noise_floor_estimator", estimator)


def _rule_e5_rank_moves_and_generation_collapses(*, moves, collapses):
    """RANK-02: the written definitions of a rank move and a generation collapse."""
    return types.MappingProxyType(
        {"moves": _frozen_entry("moves", moves), "collapses": _frozen_entry("collapses", collapses)}
    )


def _rule_e6_decomposition_rule(*, decomposition):
    """CTX-03: the written decomposition rule."""
    return _frozen_entry("e6_decomposition_rule", decomposition)


_SLOTS = {
    "v6_budget_and_stop_line": {
        "owner_phase": 36,
        "rule": _rule_v6_budget_and_stop_line,
        "input_records": ("results/phase36_probe_*.json",),
    },
    "e2_S": {"owner_phase": 40, "rule": _rule_e2_S, "input_records": (_BUDGET_RECORD,)},
    "r1b_tolerance_and_replicated": {
        "owner_phase": 37,
        "rule": _rule_r1b_tolerance_and_replicated,
        "input_records": (),
    },
    "e1_checkpoint_grid": {
        "owner_phase": 41,
        "rule": _rule_e1_checkpoint_grid,
        "input_records": (_BUDGET_RECORD,),
    },
    "e1_condition_a_floors": {
        "owner_phase": 41,
        "rule": _rule_e1_condition_a_floors,
        "input_records": (_CALIBRATION_RECORDS, _CALIBRATION_CORPUS),
    },
    "e1_alternative_ordering": {
        "owner_phase": 41,
        "rule": _rule_e1_alternative_ordering,
        "input_records": (),
    },
    "e3_grid_subset": {
        "owner_phase": 42,
        "rule": _rule_e3_grid_subset,
        "input_records": (_BUDGET_RECORD, _V4_CONTROL_RECORD),
    },
    "e4_parameters": {
        "owner_phase": 43,
        "rule": _rule_e4_parameters,
        "input_records": ("results/phase38_minting*.json",),
    },
    "e5_minting_rule": {"owner_phase": 38, "rule": _rule_e5_minting_rule, "input_records": ()},
    "e5_set_sizes": {
        "owner_phase": 38,
        "rule": _rule_e5_set_sizes,
        "input_records": ("results/phase38_minting*.json",),
    },
    "e6_entry_subset": {
        "owner_phase": 39,
        "rule": _rule_e6_entry_subset,
        "input_records": ("results/phase36_probe_*.json",),
    },
    "e3_recall_threshold": {
        "owner_phase": 42,
        "rule": _rule_e3_recall_threshold,
        "input_records": ("results/phase42_control_*.json", _V4_CONTROL_RECORD),
    },
    "e1_condition_b_margin": {
        "owner_phase": 41,
        "rule": _rule_e1_condition_b_margin,
        "input_records": (phase19_floor.EVIDENCE_ARTIFACT["NONTARGET_NOISE_FLOOR"],),
    },
    "e1_condition_c_band_inputs": {
        "owner_phase": 41,
        "rule": _rule_e1_condition_c_band_inputs,
        # W21: the ONE Phase 40 record that carries the gap noise floor (NOISE-02), never the
        # broad results/phase40_*, which would make leg (b) require every Phase 40 record ever
        # tracked to precede the band fill file.
        "input_records": (_NOISE_FLOOR_RECORD, _BAND_INPUT_RECORDS),
    },
    "e2_noise_floor_estimator": {
        "owner_phase": 40,
        "rule": _rule_e2_noise_floor_estimator,
        "input_records": (),
    },
    "e5_rank_moves_and_generation_collapses": {
        "owner_phase": 38,
        "rule": _rule_e5_rank_moves_and_generation_collapses,
        "input_records": (),
    },
    "e6_decomposition_rule": {
        "owner_phase": 39,
        "rule": _rule_e6_decomposition_rule,
        "input_records": (),
    },
}

SLOTS = types.MappingProxyType(
    {name: types.MappingProxyType(slot) for name, slot in _SLOTS.items()}
)


def fill(slot, **inputs):
    """The only door to a deferred slot (D-02): refuse an undeclared slot, dispatch its rule."""
    _prove(
        isinstance(slot, str) and slot in SLOTS,
        f"slot {slot!r} is not declared in the Phase 35 registry (D-02)",
    )
    return SLOTS[slot]["rule"](**inputs)


def _prove_slots():
    rules = [slot["rule"] for slot in SLOTS.values()]
    _prove(len(set(rules)) == len(rules), "a rule is shared by two slots")
    for name, slot in SLOTS.items():
        _prove(tuple(slot) == SLOT_FIELDS, f"slot {name} has fields {tuple(slot)}")
        owner = slot["owner_phase"]
        _prove(
            isinstance(owner, int) and not isinstance(owner, bool) and 36 <= owner <= 45,
            f"slot {name} has owner_phase {owner!r}, not a phase in 36..45",
        )
        rule = slot["rule"]
        _prove(
            rule.__name__ == "_rule_" + name and rule.__module__ == __name__,
            f"slot {name}'s rule is {rule.__module__}.{rule.__name__}, not _rule_{name}",
        )
        records = slot["input_records"]
        _prove(
            isinstance(records, tuple) and all(isinstance(p, str) for p in records),
            f"slot {name}'s input_records is not a tuple of str",
        )
        keyword_only = {
            p.name
            for p in inspect.signature(rule).parameters.values()
            if p.kind is inspect.Parameter.KEYWORD_ONLY
        }
        measured = bool(records) and name != "e1_condition_b_margin"
        _prove(
            ({"input_records", "derivation"} <= keyword_only) == measured,
            f"slot {name}: input_records/derivation parameters do not match its inputs (W3)",
        )


_prove_slots()
