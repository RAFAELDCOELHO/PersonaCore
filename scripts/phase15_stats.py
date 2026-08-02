"""Phase-15 pre-registered decision rule for the "EWC dodges high-Fisher coordinates" claim
(VIZ-03, D-09/D-10/D-11/D-12).

Reads ``results/phase15_norms.json`` — the D-05 committed norms artifact — and NOTHING else: no
checkpoint, no ``.pt`` file, no ``torch`` import. The rank machinery below is ~40 lines of pure
numpy because scipy is NOT a dependency (``pyproject.toml``: ``numpy~=2.4``, ``regex~=2026.5``)
and must not become one for a single correlation (D-12, the ``fisher.py::_spearman``
zero-new-deps register).

  results/phase15_norms.json  ->  Spearman rho + permutation p + bootstrap CI (36 cells)
                              ->  the D-11 gate verdict (GATE PASSES / GATE MISSES)
                              ->  the dated markdown section Plan 15-04 appends to
                                  results/phase13_ab_report.md

D-09: the statistic, the seed, the resample counts, the predicted sign, the gate and BOTH
verdict branches are COMMITTED BEFORE any Phase-15 correlation exists — git history order is the
pre-registration proof (the ``scripts/finetune_ab.py`` register). D-10 fixes the statistic, the
per-block n = 36 granularity and the Delta-reduction pairing. D-11 fixes the gate and the
gate-miss reporting policy. D-12 fixes the method, the resampling choice and the seed.

DIVERGENCE from ``src/personacore/continual/fisher.py::_spearman`` — DELIBERATE, DO NOT UNIFY.
That module's transform is an ordinal double-argsort with NO tie averaging (it records itself as
``_SPEARMAN_METHOD = "ordinal_double_argsort_no_tie_averaging"``). On the fixture
``a=[1, 1, 2, 3], b=[1, 2, 3, 4]`` it returns ``1.0`` where the correct answer is
``0.9486832980505139`` — the tie silently collapses and inflates rho. This module uses AVERAGE
(fractional) ranks instead. Its inputs come from the D-05 artifact, which rounds for readability
and therefore *manufactures* ties, so the tie-correct transform is the only safe one here. Both
implementations are correct for their own callers; a future reader must NOT fold them together.

No ``SECURITY:`` paragraph is required: this module deserializes nothing. ``json.loads`` of the
project's own committed artifact is its only read — no pickle, no ``torch.load``.

Run: ``python scripts/phase15_stats.py`` (inside the Python 3.11 venv).
"""

import pathlib

import numpy as np

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
NORMS_JSON = _REPO_ROOT / "results" / "phase15_norms.json"


# ===== PRE-REGISTRATION (D-09..D-12, locked before any Phase-15 correlation exists) =====
#
# Committed BEFORE the artifact exists; git history order is the pre-registration proof (the
# finetune_ab.py:66 register). Nothing below was chosen after seeing a number — at the commit
# that introduces this block, results/phase15_norms.json does not exist and main() provably
# cannot run.

# D-10 granularity — 6 layers x 6 projections = exactly the 36 cells the VIZ-03 figure draws
# (config.py:89 ``n_layer: int = 6``; lora/config.py:16 ``TARGET_PROJECTIONS``). This is NOT a
# per-parameter and NOT a per-layer statistic: the claim must describe what a reader sees.
N_CELLS = 36

# Pins the cell iteration order so the correlation is reproducible from the artifact. Copied
# verbatim from src/personacore/lora/config.py:16 — NOT an independently chosen ordering.
PROJECTIONS = ("q_proj", "k_proj", "v_proj", "c_proj", "fc_in", "fc_out")

# D-10 — the predicted sign, stated BEFORE the number exists. POSITIVE means EWC pulls movement
# back hardest where Fisher is highest, which is literally the dodging claim. This is NOT a sign
# to be picked once the data is in: a negative or near-zero result is reported as plainly as a
# positive one and is NOT re-interpreted after the fact.
PREDICTED_SIGN = 1

# D-10 pairing — Fisher magnitude vs the Delta REDUCTION, using BOTH arms so the penalty's own
# effect is isolated. NOT one arm's shape: the naive arm exists precisely to remove that
# confound.
PAIRING = "fisher_mean_per_cell vs (naive_ratio - ewc_ratio)"

# The project's established seed (finetune_ab.py:96, phase14_recall.py). It feeds a LOCAL
# ``np.random.default_rng`` only — the global python/numpy/torch RNG streams are never touched
# (the fisher.py Pitfall-3 register).
SEED = 1337

# D-12 Claude's-discretion resample counts, pinned here so the verdict is byte-reproducible from
# the committed artifact. Measured at n = 36 (15-RESEARCH.md): 100,000 shuffles = 1.4 s,
# 10,000 resamples = 0.4 s. NOT counts to raise until a boundary result moves.
N_PERM = 100_000
N_BOOT = 10_000

# Two-sided 95% percentile interval. NOT a knob to widen after seeing whether the CI clears zero.
CI_ALPHA = 0.05

# The fisher.py method-string-in-the-record convention (``_VARIANT`` / ``_SPEARMAN_METHOD``): the
# method travels WITH the number into the verdict section, so a reader never has to guess which
# transform or which interval produced the reported figure.
SPEARMAN_METHOD = "average_rank_pearson_fp64"
CI_METHOD = "percentile_bootstrap"

# ----- R5 gate arbitration: which half of D-12's evidence is LOAD-BEARING -----
#
# D-12 asks for BOTH a permutation p AND a bootstrap CI, and at n = 36 the two can disagree: the
# permutation p tests "is rho != 0", while the percentile CI asks "does the resampled rho
# distribution straddle 0". Read literally, D-11 makes the BOOTSTRAP CI THE LOAD-BEARING half of
# the gate — the gate is `positive sign AND a CI excluding zero` — and leaves the PERMUTATION p
# PURELY DESCRIPTIVE. The p NEVER overrides the CI and NEVER converts a MISS into a PASS: a
# p = 0.03 alongside a CI that spans zero is still a MISS. This arbitration is committed here,
# before either number exists, precisely so it cannot later be resolved in whichever direction
# happens to look better (the D-11 provenance note, one level deeper).

# ----- Percentile-bootstrap honesty note (pre-registered, not a footnote added afterwards) -----
#
# The percentile bootstrap is known to be BIASED and ANTI-CONSERVATIVE at small n. BCa would
# correct that at real complexity cost; percentile is chosen to stay inside D-12's "~15 lines of
# numpy" budget. The known small-n bias is named HERE rather than silently omitted, and the
# method is pinned in CI_METHOD rather than silently upgraded to BCa after the result is seen.


# ===== Rank statistics (pure numpy, fp64 — the statistics domain, per fisher.py) =====


def _rank(x):
    """Average (fractional) ranks — the tie-correct transform Spearman needs, fp64.

    Ordinal ranks (a bare double-argsort, as in ``continual/fisher.py::_spearman``) silently
    break ties by input order, which INFLATES rho whenever two cells share a value. The D-05
    artifact rounds its numbers for readability, so ties are manufacturable here even though the
    underlying aggregates are continuous floats — average ranks are the only safe choice.
    """
    x = np.asarray(x, dtype=np.float64)
    order = np.argsort(x, kind="stable")
    ranks = np.empty(len(x), dtype=np.float64)
    ranks[order] = np.arange(len(x), dtype=np.float64)
    sx = x[order]
    i = 0
    while i < len(sx):
        j = i
        while j + 1 < len(sx) and sx[j + 1] == sx[i]:
            j += 1
        if j > i:
            ranks[order[i : j + 1]] = (i + j) / 2.0
        i = j + 1
    return ranks


def spearman(a, b):
    """Spearman rho = Pearson correlation on average ranks (SPEARMAN_METHOD).

    Spearman over Kendall (D-12) on READABILITY grounds: both are rank-based and therefore
    already robust to the heavy-tailed Fisher magnitudes, so there is no edge-case advantage
    that would justify trading away readability.
    """
    return float(np.corrcoef(_rank(a), _rank(b))[0, 1])


def permutation_p(a, b, *, n_perm, seed):
    """Two-sided permutation p on the rank correlation. Ranks ONCE, then shuffles the ranks.

    Resampling over the closed-form Fisher-z transform (D-12): z's normality assumption is the
    shakiest of the available options at n = 36.

    DESCRIPTIVE ONLY under the R5 arbitration above — this p never overrides the bootstrap CI
    and never converts a gate MISS into a PASS.

    Returns ``(obs, p)``.
    """
    ra, rb = _rank(a), _rank(b)
    obs = float(np.corrcoef(ra, rb)[0, 1])
    rng = np.random.default_rng(seed)  # LOCAL generator — global RNG untouched.
    ge = sum(
        abs(float(np.corrcoef(rng.permutation(ra), rb)[0, 1])) >= abs(obs) for _ in range(n_perm)
    )
    return obs, (ge + 1) / (n_perm + 1)  # add-one: p is never reported as exactly 0.


def bootstrap_ci(a, b, *, n_boot, seed, alpha=CI_ALPHA):
    """Percentile CI by resampling PAIRS with replacement, re-ranking inside each resample.

    The LOAD-BEARING half of the D-11 gate (see the R5 arbitration in the pre-registration
    block). Method and its known small-n bias are pinned in CI_METHOD.

    Returns ``(lo, hi, n_degenerate)``.
    """
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    n = len(a)
    rng = np.random.default_rng(seed)  # LOCAL generator — global RNG untouched.
    out = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        aa, bb = a[idx], b[idx]
        # A degenerate resample (all-identical values) makes corrcoef undefined; drop it and
        # REPORT the count rather than letting a nan silently propagate into a quantile.
        out[i] = np.nan if (aa.std() == 0 or bb.std() == 0) else spearman(aa, bb)
    kept = out[np.isfinite(out)]
    lo = float(np.quantile(kept, alpha / 2))
    hi = float(np.quantile(kept, 1 - alpha / 2))
    return lo, hi, n_boot - len(kept)


# ===== The D-11 gate (a pure function over the computed numbers) =====


def ewc_dodges_high_fisher(rho, ci_lo, ci_hi):
    """D-11 claim gate: EWC dodges high-Fisher coordinates iff the correlation carries the
    pre-registered POSITIVE sign AND its bootstrap CI EXCLUDES zero. The boundary is a FAIL
    (``ci_lo == 0.0`` returns False), matching the ``finetune_ab.py::ewc_mitigates`` register.

    The coefficient's MAGNITUDE and the permutation p are DESCRIPTIVE with NO gate: the sign is
    the falsifiable claim, and the magnitude is reported honestly given n = 36 rather than being
    itself pass/fail.

    A rho that is positive but whose CI spans zero (e.g. rho = +0.15, CI = (-0.1, 0.4)) is a
    MISS. It is reported in the "suggestive but not statistically demonstrated at n = 36"
    register — REPORTED, not discarded, and NOT softened into a passing verdict — and ROADMAP
    SC2's wording narrows accordingly.
    """
    return rho > 0 and ci_lo > 0
