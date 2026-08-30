"""ADVT-03 — the COMMITTED per-arm scored-token record: ``results/phase24_token_budget.json``.

**The gap this closes.** 24-RESEARCH found that nothing in this repository persists a v4.0 arm's
scored-token counts or its mask fraction. They exist only as stdout from ``teach_persona``, and a
figure that cannot be re-read from a committed file is not a measurement. Phase 25 SC4 makes
``results/phase2X_frontier.json`` the single source of truth and requires every figure it draws to
be re-derivable from a committed file; Phase 25 SC3 requires multiplicity in the SAME SENTENCE as
epsilon, which is why multiplicity travels in the same ROW as the point here rather than in a
sibling table.

**Counts, never rates.** ``scored_tokens`` is an integer read off the mask bin actually written to
disk (``np.fromfile(...).sum()``), never ``mask_fraction * total_tokens``. The rate is derivable
from the counts; the counts are not derivable from the rate. Every measured figure carries a
sibling ``*_denominator`` / ``*_source`` / ``*_formula`` string, copying
``phase21_unit_record._corpus_geometry``'s discipline.

**Two refusals run BEFORE the bytes land**, both IMPORTED and neither reinvented:

  * refuse-to-rerun — ``phase21_unit_record.refuse_existing_artifacts(paths=[...])``, whose
    ``paths=`` parameter exists precisely so a later phase can reuse it.
  * refuse-if-dirty — ``personacore.provenance.refuse_if_dirty``, called DIRECTLY. It is NOT routed
    through ``phase21_unit_record``'s publication wrapper, and that is a measured decision, not an
    oversight: that wrapper opens with ``phase21_unit_record.is_publication_target(path)``
    (``scripts/phase21_unit_record.py:257-267``), which compares the resolved path against
    ``ARTIFACTS.values()`` — the two ``results/phase21_*`` records and nothing else. For a phase-24
    path it returns ``None`` immediately, so the wrapper would be a guard that is green and blind.

**COMMIT ORDER IS LOAD-BEARING and it is a CONSEQUENCE of the guard, not a workaround for it.**
``refuse_if_dirty`` counts untracked files as dirty (``src/personacore/provenance.py:62-65``: "a
``.py`` that is not in HEAD cannot be at the recorded SHA either"). So this module must be COMMITTED
FIRST and only then may :func:`main` run — otherwise the record's ``provenance.git_sha`` would name
a commit that does not contain the emitter that wrote it, which is exactly 21-REVIEW.md CR-02's
defect. Do NOT work around the refusal by writing to a temporary path and copying the file into
``results/``; ``phase21_unit_record._DIRTY_DETAIL`` names that workaround as CR-02 with extra steps.

Reads ``results/phase18_corpus.json``, ``scripts/phase18_extraction.py`` and
``scripts/mitigation_gate.py`` READ-ONLY. Writes nothing into ``data/``. CPU-only.
"""

import datetime
import hashlib
import json
import pathlib
import platform
import sys
import tempfile

import numpy as np

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import mitigation_budget as mb  # noqa: E402  (scripts/ is not a package)
import phase14_factset as fs  # noqa: E402
import phase18_extraction as p18  # noqa: E402
import phase21_unit_record as unit_record  # noqa: E402
import phase24_adversarial as pa  # noqa: E402
import teach_persona as tp  # noqa: E402

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402
from personacore.seeding import seed_everything  # noqa: E402
from personacore.tokenizer import from_json  # noqa: E402

# THE path constant. Resolved once and exported so no test and no downstream module ever spells
# this path a second time — `tests/test_phase23_budget.py:359`'s `_cost_record` register.
TOKEN_BUDGET_RECORD = _ROOT / "results" / "phase24_token_budget.json"

# The two capacities D-07 runs the same nominal grid at. Read through `tp.arm_spec`, so `adv_n64`'s
# lazy `phase21_filler` import and its collision refusal both still run.
ARMS = ("adv_n8", "adv_n64")

# The dirty-tree scope for THIS publication: the CODE and DATA the recorded `git_sha` actually
# claims to carry, MINUS the record being written.
#
# The EXCLUSION is what makes the guard reachable at all — re-emitting requires deleting the
# previous artifact first, which is itself a dirty tree — and it is derived from
# `TOKEN_BUDGET_RECORD` rather than retyped, so the path can never be watched and written under two
# different spellings. Same shape and same reasoning as
# `phase21_unit_record._PUBLICATION_PATHSPEC` (`:183-186`).
#
# The ROOTS are narrower than that incumbent's `"."`, deliberately and by measurement. What the
# recorded SHA claims is that the CODE and INPUTS at that commit reproduce these bytes:
#   scripts/   the emitter, teach_persona's packer, phase24_adversarial's templates, the grid
#   src/       personacore.dialogue's encoder — what actually sets every mask bit counted here
#   results/   phase18_corpus.json and its binding fixture, the corpus every row is built from
#   artifacts/ the FROZEN tokenizer every count is measured through
# `.planning/` prose and repository housekeeping (`.gitignore`, editor state) are provably not
# inputs: no number below can move when they do. Watching them would make the guard fire for
# reasons unrelated to reproducibility — and a guard that blocks an honest emission is the class
# `phase21_unit_record`'s own publication-wrapper docstring (`:269`) says gets deleted by the next
# person who hits it.
#
# MEASURED at HEAD, which is why this is narrowed rather than copied: with `"."` the guard refuses
# on `.gitignore` and `.planning/todos/` — a `.obsidian/` ignore rule and GSD workflow state,
# neither of which can move a single count below.
_PUBLICATION_PATHSPEC = (
    "scripts",
    "src",
    "results",
    "artifacts",
    f":(exclude){TOKEN_BUDGET_RECORD.relative_to(_ROOT)}",
)

# In `phase21_unit_record._DIRTY_DETAIL`'s register: a refusal that does not say what it prevented
# gets deleted by the next person who hits it.
_DIRTY_DETAIL = (
    "`provenance.git_sha()` records HEAD at write time, so a record written from a dirty tree "
    "names a commit that does NOT contain the code that produced it — the artifact points at a "
    "tree it cannot be regenerated from. That is not hypothetical: 21-REVIEW.md CR-02 found BOTH "
    "phase-21 artifacts carrying exactly that defect (phase21_privacy_unit.json recorded fa97b666, "
    "where `emit_privacy_unit` was not yet defined). This module is the same shape and would fail "
    "the same way: it names its own emitter's sha256 in provenance.module_sha256, so a dirty tree "
    "publishes a digest of bytes the recorded commit does not contain. Commit the tree, then "
    "re-run. Do NOT work around this by writing to a temporary path and copying the file into "
    "results/ — that reproduces CR-02 with extra steps."
)

# ADVT-03 quotes 1.40x for ONE uppercased 51-character sentence (35 tokens clean -> 49 uppercased,
# `.planning/REQUIREMENTS.md:310-312`). The CROSS-FAMILY figure this record publishes is a
# different measurement on a different population and is 2.7x larger. The two are trivially
# conflated, so they are kept in separate fields with the distinction written down.
_ADVT03_SINGLE_SENTENCE_NOTE = (
    "ADVT-03's own 1.40x is 49 uppercased tokens over 35 clean tokens for ONE 51-character "
    "sentence through the frozen tokenizer, plus 1.17x role-play framed. It is a per-sentence "
    "perturbation cost. cross_family_inflation below is a per-FAMILY corpus mean over 112 rows "
    "each. Reporting either as if it were the other overstates or understates the token-budget "
    "confound by roughly 2.7x."
)


def _sha256(path):
    """BYTES, never text — ``tests/test_package.py:36``'s rule."""
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _tokenizer():
    """``seed_everything`` then the FROZEN production tokenizer — never retrained, never faked."""
    seed_everything(tp.SEED)
    return from_json(tp.TOKENIZER_PATH)


# =================================================================================================
# THE ROWS — one per (arm, grid point), counts with their denominators
# =================================================================================================


def _row(scratch, arm, episodes, ratio, pool_size):
    """One ``(arm, adversarial_ratio)`` row, MEASURED off a bin actually written to disk."""
    bin_path = scratch / f"{arm}_{ratio}.bin"
    mask_path = scratch / f"{arm}_{ratio}_mask.bin"
    stats = tp.build_bins(
        _tokenizer(),
        episodes,
        bin_path,
        mask_path,
        align_facts=None,
        adversarial_ratio=ratio,
        seed=tp.SEED,
    )

    total_tokens = int(stats["tokens"])
    scored_tokens = int(np.fromfile(mask_path, dtype=np.uint8).sum())
    floor, _ceiling = tp.MASK_FRACTION_BAND

    return {
        "arm": arm,
        "n_facts": len(tp.arm_spec(arm)[0]),
        "adversarial_ratio": ratio,
        # --- episode counts (D-06's sizing unit) ---
        "clean_episodes": int(stats.get("clean_episodes", len(episodes))),
        "adversarial_episodes": int(stats.get("adversarial_episodes", 0)),
        "total_episodes": int(stats["episodes"]),
        "adversarial_pool_size": int(stats.get("adversarial_pool_size", pool_size)),
        "adversarial_pool_size_source": (
            "phase24_adversarial.adversarial_pool_size — a property of the committed corpus, not "
            "of the ratio, so it is recorded at the control point too where no pool is read"
        ),
        # --- D-07: multiplicity travels in the SAME ROW as the point, because Phase 25 SC3
        # requires it in the same sentence as epsilon ---
        "adversarial_multiplicity": float(stats.get("adversarial_multiplicity", 0.0)),
        "adversarial_multiplicity_formula": (
            "adversarial_episodes / adversarial_pool_size — how many times the 336-episode attack "
            "pool is passed over; 1.0 at the upper extreme means one full pass, no repetition"
        ),
        "adversarial_family_counts": stats.get("adversarial_family_counts", {}),
        "adversarial_family_counts_source": (
            "the SELECTED prefix's per-family episode counts (D-10), not the full pool's — the "
            "only reading that can see a corpus row reorder"
        ),
        # --- token counts ---
        "total_tokens": total_tokens,
        "total_tokens_source": "MEASURED: len(np.concatenate(shards)) written to the token bin",
        "teaching_tokens": int(stats["teaching_tokens"]),
        "teaching_tokens_source": (
            "CLEAN-ONLY BY DESIGN (D-06) — teach_persona computes it before the mixture so it can "
            "never become a sizing input. It is NOT the bin's token total; total_tokens is."
        ),
        "adversarial_tokens": int(stats.get("adversarial_tokens", 0)),
        "scored_tokens": scored_tokens,
        "scored_tokens_denominator": (
            "total_tokens (the concatenated flat pack; no padding on this branch)"
        ),
        "scored_tokens_source": "MEASURED: sum over the mask bin actually written to disk",
        "scored_tokens_formula": "int(np.fromfile(mask_path, dtype=np.uint8).sum())",
        "adversarial_scored_tokens": int(stats.get("adversarial_scored_tokens", 0)),
        # --- the rate, DERIVED, kept beside the counts it comes from ---
        "mask_fraction": float(stats["mask_fraction"]),
        "mask_fraction_source": (
            "build_bins stats; the AGGREGATE mean _prove_floor_and_band checks at "
            "teach_persona.py:628 (the `not lo <= frac <= hi` SystemExit)"
        ),
        "mask_fraction_formula": "scored_tokens / total_tokens",
        "mask_fraction_band": list(tp.MASK_FRACTION_BAND),
        "mask_fraction_margin_over_floor": float(stats["mask_fraction"]) - floor,
        "mask_fraction_margin_required": pa.MASK_FRACTION_MARGIN,
        "mask_fraction_min": float(stats["mask_fraction_min"]),
        "mask_fraction_min_note": (
            "PER-EPISODE minimum, REPORTED AND DELIBERATELY NOT GATED. It falls below the band "
            "floor at the non-zero points and nothing trips, because _prove_floor_and_band gates "
            "the AGGREGATE. A per-episode FRACTION floor would be the wrong instrument: the "
            "minimum is an A3 episode (18 scored tokens in 162), so it is driven by the attack "
            "PROMPT's length, which D-10 trains on deliberately, and not by a short refusal. The "
            "per-episode quantity that IS well defined is the scored-token COUNT, and it already "
            "has a floor — phase24_adversarial.MIN_REFUSAL_SCORED_TOKENS. See "
            "tests/test_phase24_band.py::"
            "test_the_per_episode_floor_is_a_scored_token_count_and_not_a_fraction."
        ),
        "adversarial_permutation_seed": int(stats.get("adversarial_permutation_seed", tp.SEED)),
    }


def rows():
    """The 12 rows: ``ARMS`` x ``mitigation_budget.ADVERSARIAL_RATIO_GRID``, in grid order.

    Bins are built under a scratch directory and deleted with it. Never ``data/``, never
    ``results/`` — this function writes no bin any run could later mistake for a training corpus.
    """
    pool_size = pa.adversarial_pool_size(_tokenizer())
    out = []
    with tempfile.TemporaryDirectory(prefix="phase24_record_") as scratch:
        scratch = pathlib.Path(scratch)
        for arm in ARMS:
            facts, _second_person, _replay_ratio = tp.arm_spec(arm)
            episodes = tp.render_episodes(facts, fs.TAUGHT_FAMILY_IDS)
            for ratio in mb.ADVERSARIAL_RATIO_GRID:
                out.append(_row(scratch, arm, episodes, ratio, pool_size))
    return out


# =================================================================================================
# THE BLOCKS
# =================================================================================================


def band_corners(measured):
    """D-05's four corners named, with the binding one identified by MEASUREMENT."""
    grid = mb.ADVERSARIAL_RATIO_GRID
    extremes = (grid[0], grid[-1])
    corners = [
        {
            "arm": row["arm"],
            "adversarial_ratio": row["adversarial_ratio"],
            "extreme": "lower (the control)" if row["adversarial_ratio"] == grid[0] else "upper",
            "mask_fraction": row["mask_fraction"],
            "mask_fraction_margin_over_floor": row["mask_fraction_margin_over_floor"],
            "clears_required_margin": (
                row["mask_fraction_margin_over_floor"] >= pa.MASK_FRACTION_MARGIN
            ),
        }
        for row in measured
        if row["adversarial_ratio"] in extremes
    ]
    binding = min(corners, key=lambda corner: corner["mask_fraction"])
    return {
        "corners": corners,
        "band": list(tp.MASK_FRACTION_BAND),
        "margin_constant": pa.MASK_FRACTION_MARGIN,
        "margin_constant_source": "phase24_adversarial.MASK_FRACTION_MARGIN — never retyped",
        "binding_corner": {
            "arm": binding["arm"],
            "adversarial_ratio": binding["adversarial_ratio"],
        },
        "binding_corner_source": (
            "MEASURED: argmin of mask_fraction over the four corners, not asserted. n=64's much "
            "larger clean bin dilutes the fixed-size attack pool's unmasked prompt mass, so it is "
            "the EASIER corner; calibrating the refusal length against it would leave n=8 "
            "uncovered. tests/test_phase24_band.py::"
            "test_the_binding_corner_is_n8_at_the_upper_extreme pins the ordering as a property."
        ),
        "only_the_floor_binds": (
            "Both effects of the mixture push the fraction DOWN — an adversarial episode adds a "
            "long unmasked attack prompt and a short masked refusal — so the band's upper bound is "
            "unreachable on this axis. The claim is CHECKED rather than argued: every corner "
            "asserts frac <= band[1] too, and every row's mask_fraction is asserted "
            "non-increasing in adversarial_ratio within its arm."
        ),
    }


def token_budget_disclosure(corpus):
    """ADVT-03's confound: attack intensity is ALSO a token-budget axis. Stated so it cannot
    be silently collapsed into the swept axis.

    Every figure is COUNTED off the committed corpus's ``prompt_ids`` here and now; nothing is
    pasted from a plan or a prior summary.
    """
    tier = pa.TRAINED_TIER
    lengths = {}
    for row in corpus["prompts"]:
        if row["tier"] == tier:
            lengths.setdefault(row["family"], []).append(len(row["prompt_ids"]))

    def family_row(family):
        values = lengths[family]
        return {
            "family": family,
            "episodes": len(values),
            "total_prompt_tokens": int(sum(values)),
            "mean_prompt_tokens": sum(values) / len(values),
            "min_prompt_tokens": int(min(values)),
            "max_prompt_tokens": int(max(values)),
            "denominator": f"{len(values)} {tier} rows for this family",
        }

    trained = [family_row(family) for family in pa.TRAINED_FAMILIES]
    held_out = family_row(pa.HELD_OUT_FAMILY)

    means = {family: sum(values) / len(values) for family, values in lengths.items()}
    high, low = max(means, key=means.get), min(means, key=means.get)
    exact_inflation = means[high] / means[low]

    # LEAVE-ONE-OUT at IDENTICAL episode count: hold out each family in turn and total the other
    # three. Every choice trains exactly 336 episodes, and only the TOKEN volume moves — which is
    # D-06's reason for sweeping the episode unit and pushing token variation into this report.
    totals = {family: sum(values) for family, values in lengths.items()}
    leave_one_out = {
        family: int(sum(total for other, total in totals.items() if other != family))
        for family in totals
    }
    exact_spread = max(leave_one_out.values()) / min(leave_one_out.values())

    return {
        "unit_swept": mb.ADVERSARIAL_RATIO_GRID_PROVENANCE["unit"],
        "trained_families": trained,
        "held_out_family": held_out,
        "held_out_family_note": (
            f"{pa.HELD_OUT_FAMILY} is listed SEPARATELY and is NOT part of any trained total below "
            "— it is held out for value containment (D-10/D-12) and never trained on."
        ),
        "trained_pool_episodes": sum(row["episodes"] for row in trained),
        "trained_pool_prompt_tokens": sum(row["total_prompt_tokens"] for row in trained),
        "cross_family_inflation": round(exact_inflation, 2),
        "cross_family_inflation_exact": exact_inflation,
        "cross_family_inflation_formula": (
            f"{high} mean prompt tokens {means[high]:.4f} / {low} mean prompt tokens "
            f"{means[low]:.4f}, each over {len(lengths[high])} {tier} rows"
        ),
        "cross_family_inflation_note": (
            f"This is {high}/{low} — the CROSS-FAMILY prompt-token ratio across the four attack "
            "families in the committed corpus. It is NOT the 1.40x figure ADVT-03 quotes for one "
            "uppercased 51-character sentence, and the two must NEVER be reported as if they were "
            "the same number. " + _ADVT03_SINGLE_SENTENCE_NOTE
        ),
        "advt03_single_sentence_note": _ADVT03_SINGLE_SENTENCE_NOTE,
        "leave_one_out_token_spread": round(exact_spread, 2),
        "leave_one_out_token_spread_exact": exact_spread,
        "leave_one_out_totals": leave_one_out,
        "leave_one_out_token_spread_formula": (
            "max / min over {held-out family -> total prompt tokens of the other three}; every "
            "choice trains exactly "
            f"{sum(row['episodes'] for row in trained)} episodes, so the EPISODE count is "
            "invariant and only the TOKEN volume moves"
        ),
        "leave_one_out_note": (
            "D-06's reason for choosing the episode unit: the post-leave-one-out pool is the same "
            "size whichever family is held out, while its token volume varies by this factor. "
            "Sweeping tokens would confound intensity with budget; sweeping episodes pushes the "
            "budget variation into THIS report, where it is separable."
        ),
    }


def attack_corpus(corpus):
    """The corpus this phase trains against — digest recomputed LIVE, and SC4 discharged."""
    return {
        "path": str(p18.CORPUS_PATH.relative_to(_ROOT)),
        "sha256": p18.corpus_sha256(corpus),
        "sha256_source": (
            "phase18_extraction.corpus_sha256 over canonical_json(corpus), recomputed at write "
            "time from the loaded artifact — never pasted"
        ),
        "entries": len(corpus["prompts"]),
        "trained_tier": pa.TRAINED_TIER,
        "trained_families": list(pa.TRAINED_FAMILIES),
        "held_out_family": pa.HELD_OUT_FAMILY,
        "held_out_reason": mb.ADVERSARIAL_RATIO_GRID_PROVENANCE["held_out_reason"],
        # --- SC4's inflation-report obligation, discharged EXPLICITLY rather than by silence ---
        "new_attack_corpus": False,
        "inflation_report_required": False,
        "inflation_report_discharge": (
            "SC4's inflation-report obligation attaches to a NEW attack corpus, and this phase "
            "creates none. It reuses results/phase18_corpus.json VERBATIM and READ-ONLY — "
            "phase18_extraction.build_corpus is never called from phase24_adversarial (AST: zero "
            "calls), every trained prompt is proved byte-equal to its committed prompt_ids under "
            "hard list equality, and the digest above travels in this record so the corpus a "
            "future report names is checkable against the corpus that was trained on. The "
            "obligation is therefore discharged by non-creation, stated here so a reader cannot "
            "mistake the absence of an inflation report for an omission."
        ),
    }


def provenance():
    """``phase21_unit_record._provenance``'s shape, plus the bytes that produced these numbers.

    ``module_sha256`` pins the TEMPLATES, the GRID, the PACKER and this emitter to their bytes, so
    an artifact written against an edited module carries a digest that does not match — visible in
    the record itself, independently of the git-ancestry guard.
    """
    modules = (
        "scripts/phase24_record.py",
        "scripts/phase24_adversarial.py",
        "scripts/mitigation_budget.py",
        "scripts/teach_persona.py",
    )
    return {
        "git_sha": git_sha(),
        "written_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "python": platform.python_version(),
        "seed": tp.SEED,
        "device": "cpu (build-only; no training, no GPU, no MPS)",
        "tokenizer_path": str(tp.TOKENIZER_PATH.relative_to(_ROOT)),
        "tokenizer_sha256": _sha256(tp.TOKENIZER_PATH),
        "module_sha256": {name: _sha256(_ROOT / name) for name in modules},
        "epsilon_computed": False,
        "epsilon_note": (
            "NO EPSILON IS COMPUTED HERE. This record holds the token BUDGET the adversarial arm "
            "trains under. The accountant that would consume it is Phase 25, and D-07 requires "
            "multiplicity in the same sentence as epsilon — which is why adversarial_multiplicity "
            "travels in the same ROW as its grid point rather than in a sibling table."
        ),
    }


def document():
    """The whole record, ``provenance`` LAST."""
    corpus = json.loads(p18.CORPUS_PATH.read_text(encoding="utf-8"))
    measured = rows()
    return {
        "grid": {
            "points": list(mb.ADVERSARIAL_RATIO_GRID),
            "provenance": mb.ADVERSARIAL_RATIO_GRID_PROVENANCE,
            "source": "scripts/mitigation_budget.ADVERSARIAL_RATIO_GRID — imported, never retyped",
        },
        "arms": list(ARMS),
        "rows": measured,
        "band_corners": band_corners(measured),
        "token_budget_disclosure": token_budget_disclosure(corpus),
        "attack_corpus": attack_corpus(corpus),
        "provenance": provenance(),
    }


def _write(path, document):
    """BOTH refusals, then the bytes. Neither refusal is invented here.

    The dirty check runs AFTER the document is built, which is the point: a tree that was clean
    when the twelve builds started can be dirty by the time the bytes land, and the ``git_sha``
    ``provenance()`` captured inside that window only means something if the tree is still clean
    HERE.
    """
    path = pathlib.Path(path)
    unit_record.refuse_existing_artifacts(paths=[path])
    refuse_if_dirty(
        who="phase24_record",
        detail=_DIRTY_DETAIL,
        pathspec=_PUBLICATION_PATHSPEC,
        cwd=_ROOT,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return path


def main():
    """Regenerate ``results/phase24_token_budget.json``. Refuses over an existing artifact."""
    unit_record.refuse_existing_artifacts(paths=[TOKEN_BUDGET_RECORD])
    written = _write(TOKEN_BUDGET_RECORD, document())
    record = json.loads(written.read_text(encoding="utf-8"))
    print(f"[phase24_record] wrote {written.relative_to(_ROOT)} — {len(record['rows'])} rows")
    for row in record["rows"]:
        print(
            f"  {row['arm']:8s} ratio={row['adversarial_ratio']:<20} "
            f"scored={row['scored_tokens']:>7,} / {row['total_tokens']:>7,} "
            f"frac={row['mask_fraction']:.6f} mult={row['adversarial_multiplicity']:.4f}"
        )
    return written


if __name__ == "__main__":
    main()
