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

import mitigation_unit  # noqa: E402  (needs the sys.path insert above)
import phase25_epsilon  # noqa: E402  (same; loads the torch-free accountant transitively)

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
# (5) ENTRIES — the last block of the file. A plain dict literal so the AST tests can walk it.
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
}

ENTRIES = types.MappingProxyType(
    {name: types.MappingProxyType(entry) for name, entry in _ENTRIES.items()}
)


def _prove_entries():
    for name, entry in ENTRIES.items():
        _prove_entry(name, entry)


_prove_entries()
