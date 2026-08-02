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

import json
import pathlib
import time

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

# The commit that locked the rule, the seed, the predicted sign, the resample counts and the gate
# — before results/phase15_norms.json existed. The artifact reader and BOTH verdict branches
# landed in the immediately following commit, still before the artifact existed. Cited by the
# Evidence Index addendum exactly as `finetune_ab.py @ c3d942e` is cited by Phase 13's.
PREREG_COMMIT = "0e1af98"

# The four blocks the D-05 artifact must carry. Only fisher/naive/ewc feed the correlation; the
# adapter block is validated too, because a truncated artifact that happens to keep the three
# blocks this module reads is exactly the tampering case T-15-07 names.
BLOCKS = ("adapter", "naive", "ewc", "fisher")

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


# ===== The D-05 artifact reader (structured, untrusted input — T-15-07) =====


def load_pairs(artifact):
    """The 36 ``(fisher, naive_ratio - ewc_ratio)`` cell pairs, in the PINNED order.

    Outer loop ``layer`` 0..5, inner loop over ``PROJECTIONS`` in its declared order, so the
    correlation is reproducible from the committed artifact rather than dependent on dict
    insertion order. Returns two length-``N_CELLS`` fp64 lists.

    Every deviation is fatal and NAMES the offending block/coordinate (the
    ``plot_phase13.py:88-97`` register — an error that names only a shape leaves the operator
    guessing). A malformed or truncated artifact must never yield a partial correlation that
    reads as a plausible verdict (T-15-07).
    """
    blocks = artifact.get("blocks")
    if not isinstance(blocks, dict):
        raise SystemExit(
            f"[phase15_stats] {NORMS_JSON.name} has no 'blocks' object — this is not a D-05 "
            "norms artifact. Re-run scripts/extract_deltas.py."
        )
    n_layer = N_CELLS // len(PROJECTIONS)
    for name in BLOCKS:
        if name not in blocks:
            raise SystemExit(
                f"[phase15_stats] {NORMS_JSON.name}: block {name!r} is absent; blocks present "
                f"are {sorted(blocks)}. All of {list(BLOCKS)} are required."
            )
        cells = blocks[name].get("cells")
        if not isinstance(cells, dict):
            raise SystemExit(
                f"[phase15_stats] {NORMS_JSON.name}: block {name!r} has no 'cells' object."
            )
        total = sum(len(v) for v in cells.values() if isinstance(v, dict))
        if total != N_CELLS:
            raise SystemExit(
                f"[phase15_stats] {NORMS_JSON.name}: block {name!r} carries {total} cells, "
                f"expected exactly {N_CELLS} ({n_layer} layers x {len(PROJECTIONS)} projections)."
            )
        for layer in range(n_layer):
            row = cells.get(str(layer))
            if not isinstance(row, dict):
                raise SystemExit(
                    f"[phase15_stats] {NORMS_JSON.name}: block {name!r} has no layer {layer!r} row."
                )
            if tuple(sorted(row)) != tuple(sorted(PROJECTIONS)):
                raise SystemExit(
                    f"[phase15_stats] {NORMS_JSON.name}: block {name!r} layer {layer} has "
                    f"projections {sorted(row)}, expected {sorted(PROJECTIONS)}."
                )

    fisher_values, reduction_values = [], []
    for layer in range(n_layer):
        for projection in PROJECTIONS:
            key = f"block {{}} cell (layer {layer}, {projection})"
            fisher_values.append(_cell(blocks, "fisher", layer, projection, key))
            naive = _cell(blocks, "naive", layer, projection, key)
            ewc = _cell(blocks, "ewc", layer, projection, key)
            reduction_values.append(naive - ewc)  # D-10 pairing: naive_ratio - ewc_ratio.
    return fisher_values, reduction_values


def _cell(blocks, name, layer, projection, key):
    """One cell as a finite fp64 float — a non-numeric or non-finite cell is fatal and named."""
    value = blocks[name]["cells"][str(layer)][projection]
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise SystemExit(
            f"[phase15_stats] {NORMS_JSON.name}: {key.format(name)} is {value!r}, not a number."
        ) from None
    if not np.isfinite(value):
        raise SystemExit(
            f"[phase15_stats] {NORMS_JSON.name}: {key.format(name)} is {value!r}, not finite."
        )
    return value


# ===== The verdict section (BOTH branches authored before either is known to apply) =====

_R5_SENTENCE = (
    "The **bootstrap CI is the load-bearing half of the gate**; the permutation p is "
    "**descriptive** and never overrides it — a small p alongside a CI that spans zero is still "
    "a MISS."
)

_BOOTSTRAP_BIAS_NOTE = (
    "The percentile bootstrap is known to be biased and anti-conservative at small n. BCa would "
    "correct that at real complexity cost; percentile was chosen for D-12's ~15-lines-of-numpy "
    "budget and the bias is named here rather than silently omitted or silently upgraded."
)


def render_verdict_section(rho, p, ci_lo, ci_hi, n_degenerate, artifact, today):
    """The complete dated markdown block Plan 15-04 appends to ``results/phase13_ab_report.md``.

    BOTH branches — ``GATE PASSES`` and ``GATE MISSES`` — are authored and committed BEFORE
    either is known to apply. That is the T-15-09 mitigation: the gate cannot be resolved in
    whichever direction looks better after the number arrives, because the exact words for both
    outcomes already exist in git history.

    D-17 separation: the section is explicitly dated, marked as Phase 15 material, and states
    that it does not reopen or amend Phase 13's pre-registered content.

    **CR-02 — for whoever writes the next guard over this report.** The prose below QUOTES the
    Phase 13 heading strings ``## Verdict`` and ``## Gate Verdict``, so those literals appear in
    the file more than once once this section lands. Any guard reading a section of this report
    MUST anchor on ``scripts/_verdict.py::VERDICT_SECTION`` — the one shared copy of the anchored
    section read — and NEVER on ``text.split("## Verdict")[-1]``. The naive tail lands in this
    addendum's prose, which is exactly the CR-02 failure that made ``--force`` mandatory on every
    legitimate re-drive of an interrupted run.
    """
    passes = ewc_dodges_high_fisher(rho, ci_lo, ci_hi)
    ci_pct = int(round((1 - CI_ALPHA) * 100))
    lines = [
        "---",
        "",
        "## Phase 15 Addendum — Fisher/Δ Correlation Verdict (D-09/D-10/D-11)",
        "",
        "<!-- Phase 15 material, dated AFTER every Phase 13 result above. This section reports a",
        "NEW measurement computed read-side from `results/phase15_norms.json`; it does not reopen",
        "or amend Phase 13's pre-registered content — `## Pre-Registration`, `## Gate Verdict` and",
        "`## Verdict` above stand exactly as recorded. Same separation register as Phase 14's",
        "post-verdict ship decision: separate section, dated after the verdict, explicit that it",
        "amends nothing above it. -->",
        "",
        f"**Recorded: {today}** — Phase 15 material appended to Phase 13 evidence.",
        "",
        "### Pre-Registration (locked before the artifact existed)",
        "",
        f"Locked in `scripts/phase15_stats.py` at commit `{PREREG_COMMIT}`; the artifact reader "
        "and BOTH verdict branches landed in the immediately following commit. No Phase-15 "
        "correlation existed at either commit, and `results/phase15_norms.json` did not exist.",
        "",
        "| Constant | Value | What it fixes |",
        "| --- | --- | --- |",
        "| Statistic | Spearman ρ | D-10/D-12: rank-based, chosen over Kendall on readability "
        "grounds — both are already robust to the heavy-tailed Fisher magnitudes |",
        f"| Granularity | `N_CELLS` = {N_CELLS} | D-10: {N_CELLS // len(PROJECTIONS)} layers × "
        f"{len(PROJECTIONS)} projections — exactly the cells the VIZ-03 figure draws |",
        f"| Pairing | `{PAIRING}` | D-10: the Δ-reduction pairing uses BOTH arms so the penalty's "
        "own effect is isolated |",
        f"| Predicted sign | `{PREDICTED_SIGN:+d}` (POSITIVE) | D-10: stated before the number; a "
        "negative or near-zero result is reported as plainly as a positive one |",
        f"| Seed | `{SEED}` | D-12: a LOCAL `np.random.default_rng` only; the global RNG streams "
        "are never touched |",
        f"| Permutation resamples | `{N_PERM}` | D-12 discretion, pinned so the p is "
        "byte-reproducible (measured 1.4 s at n = 36) |",
        f"| Bootstrap resamples | `{N_BOOT}` | D-12 discretion, pinned so the CI is "
        "byte-reproducible (measured 0.4 s at n = 36) |",
        f"| CI α | `{CI_ALPHA}` | two-sided {ci_pct}% percentile interval |",
        f"| Spearman method | `{SPEARMAN_METHOD}` | average (tie-corrected) ranks — deliberately "
        "NOT `continual/fisher.py::_spearman`'s ordinal transform |",
        f"| CI method | `{CI_METHOD}` | see the method note below |",
        "| Gate rule | EWC dodges high-Fisher coordinates **iff** ρ > 0 **AND** the bootstrap CI "
        "excludes zero (`ci_lo > 0`); the boundary (`ci_lo == 0`) is a **FAIL** | D-11: the sign "
        "is gated, the magnitude is descriptive |",
        "",
        f"**Gate arbitration (pre-registered).** {_R5_SENTENCE}",
        "",
        f"**Bootstrap method note (pre-registered).** {_BOOTSTRAP_BIAS_NOTE}",
        "",
        "### Result",
        "",
        f"- Spearman ρ = **{rho:.6f}** (`{SPEARMAN_METHOD}`, n = {N_CELLS})",
        f"- {ci_pct}% CI = **[{ci_lo:.6f}, {ci_hi:.6f}]** (`{CI_METHOD}`, {N_BOOT} resamples, "
        f"seed {SEED})",
        f"- Permutation p = **{p:.6f}** ({N_PERM} shuffles, seed {SEED}) — descriptive only, "
        "per the gate arbitration above",
        f"- Degenerate (zero-variance) bootstrap resamples dropped: **{n_degenerate}** of {N_BOOT}",
        f"- Source artifact: `results/phase15_norms.json` @ git_sha "
        f"`{artifact.get('git_sha', 'MISSING')}`, built `{artifact.get('built', 'MISSING')}`",
        "",
        "### Verdict",
        "",
    ]
    if passes:
        lines += [
            "**GATE PASSES** — the correlation carries the pre-registered positive sign and its "
            f"{ci_pct}% CI excludes zero.",
            "",
            "The magnitude remains descriptive: *the sign is the falsifiable claim; the magnitude "
            "is reported honestly given n = 36 and is not itself pass/fail.* ROADMAP SC2's "
            '"showing EWC visibly dodging high-Fisher coordinates" wording is supported at the '
            "level the gate tests — the sign — and no further.",
        ]
    else:
        lines += [
            "**GATE MISSES** — the pre-registered gate (positive sign AND a CI excluding zero) is "
            "not cleared.",
            "",
            "Per D-11, this result is **recorded unamended**. It is reported in the "
            '**"suggestive but not statistically demonstrated at n = 36"** register: it is '
            "**reported, not discarded**, and it is **not softened into a passing verdict**. "
            'ROADMAP SC2\'s "showing EWC visibly dodging high-Fisher coordinates" wording narrows '
            "accordingly — the figure shows the two arms' Δ grids side by side against the Fisher "
            "diagonal, and the dodging claim is not statistically demonstrated at this n.",
            "",
            "The magnitude and the permutation p above are descriptive and carry no gate.",
        ]
    lines += [
        "",
        "### Evidence Index Addendum",
        "",
        "| Artifact | Role |",
        "| --- | --- |",
        f"| `scripts/phase15_stats.py` @ `{PREREG_COMMIT}` | the pre-registered rule, seed, sign "
        "and gate that produced this verdict |",
        "| `results/phase15_norms.json` | the D-05 committed norms artifact — the 36 Fisher/Δ "
        "cell pairs this verdict is computed from |",
        "",
    ]
    return "\n".join(lines)


def main():
    if not NORMS_JSON.exists():
        raise SystemExit(
            f"[phase15_stats] {NORMS_JSON} does not exist — the D-05 norms artifact has not been "
            "built yet. Run `python scripts/extract_deltas.py` first. This module never reads a "
            "checkpoint; the artifact is its only input."
        )
    artifact = json.loads(NORMS_JSON.read_text(encoding="utf-8"))
    fisher_values, reduction_values = load_pairs(artifact)
    rho, p = permutation_p(fisher_values, reduction_values, n_perm=N_PERM, seed=SEED)
    ci_lo, ci_hi, n_degenerate = bootstrap_ci(
        fisher_values, reduction_values, n_boot=N_BOOT, seed=SEED
    )
    today = time.strftime("%Y-%m-%d", time.gmtime())
    print(render_verdict_section(rho, p, ci_lo, ci_hi, n_degenerate, artifact, today))


if __name__ == "__main__":
    main()
