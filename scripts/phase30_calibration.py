"""PHASE 30 ARECIPE-02 — the calibration emitter for the replay-bearing ``advr`` recipe (D-05..11).

WHAT IT MEASURES. The D-05 derivation behind ``phase24_adversarial.MIN_REFUSAL_SCORED_TOKENS``,
re-run LIVE at the replay-bearing recipe (D-06): the four inputs (clean scored tokens, clean
tokens, attack-pool episodes, pool prompt tokens) are counted off bins that
``teach_persona.build_bins`` actually writes for ``advr_n8`` at the first and last grid corner, into
a temporary directory, never ``data/``. The floor is the first L whose mask fraction clears
``MASK_FRACTION_BAND[0] + MASK_FRACTION_MARGIN``. Every constant is imported.

WHY IT REPRODUCES — MEASURED, NOT ASSERTED. Train-time replay is a separate loss pass in
``train()`` and never enters the teaching bin. The evidence is byte equality: each arm's bins are
built from its FULL ``arm_spec`` triple through the argument list ``build_arm_bins`` passes on its
flat branch, and the advr arm's teaching bins must hash identically to its adv twin's at both
corners, or this module refuses. The replay volume is measured separately, at train time, by the
``on_draw`` seam test in ``tests/test_phase30_seam.py``.

D-08. If the re-derived floor is not the frozen v4.0 constant, :func:`derive` raises
``SystemExit`` naming D-08 and nothing is written. The constant is never re-pinned silently.

ANCESTRY-FROZEN (D-11). This file must not change after the calibration record is first
committed; ``tests/test_phase30_calibration.py`` reddens if it does. Corrections are dated
continuations only.

Torch-free at import: ``teach_persona`` is imported lazily inside the functions that need it.
"""

import datetime
import hashlib
import itertools
import pathlib
import sys
import tempfile

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import mitigation_budget  # noqa: E402  (scripts/ is not a package)
import phase24_adversarial  # noqa: E402  (same)
import phase25_run  # noqa: E402  (same)
import phase29_prereg  # noqa: E402  (same)
import phase30_points  # noqa: E402  (same)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

INSTRUMENT_GIT_SHA = git_sha()

RECORD = _ROOT / phase30_points.CALIBRATION_PATH
PINNED_MODULES = tuple(
    pathlib.Path(path).resolve().relative_to(_ROOT).as_posix()
    for path in (
        __file__,
        phase30_points.__file__,
        _SCRIPTS + "/teach_persona.py",  # a path, not an import: teach_persona imports torch
        phase24_adversarial.__file__,
        phase29_prereg.__file__,
    )
)


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase30_calibration] {message}")


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _rel(path):
    path = pathlib.Path(path)
    return path.relative_to(_ROOT).as_posix() if path.is_relative_to(_ROOT) else str(path)


def derive():
    """D-06: the D-05 floor re-derived live off tempdir bins at the two grid corners."""
    import numpy as np
    import phase14_factset as fs
    import teach_persona as tp

    from personacore.seeding import seed_everything
    from personacore.tokenizer import from_json

    _prove(
        tp.MAX_STEPS == mitigation_budget.STEP_BUDGET,
        f"teach_persona.MAX_STEPS {tp.MAX_STEPS} != mitigation_budget.STEP_BUDGET",
    )
    _prove(
        tp.SEED == phase30_points.SWEEP_SEED,
        f"teach_persona.SEED {tp.SEED} != the sweep seed {phase30_points.SWEEP_SEED}",
    )
    advr = phase29_prereg.ADVR_ARMS[0]
    _prove(
        len(tp.arm_spec(advr)[0]) == int(phase29_prereg.LEGS[0].removeprefix("n")),
        f"{advr} is not the {phase29_prereg.LEGS[0]} arm",
    )
    twin = advr.replace("advr_", "adv_", 1)
    lo, hi = phase29_prereg.RATIO_GRID[0], phase29_prereg.RATIO_GRID[-1]

    builds, bins, specs = {}, {}, {}
    with tempfile.TemporaryDirectory(prefix="phase30_calibration_") as scratch:
        scratch = pathlib.Path(scratch)
        for arm in (advr, twin):
            # The FULL triple: build_bins takes no arm, so dropping second_person / replay_ratio
            # would make the advr-vs-adv comparison below true by construction.
            facts, second_person, replay_ratio = tp.arm_spec(arm)
            _prove(arm not in tp.DP_ARMS, f"{arm} packs the aligned branch, not the flat one")
            specs[arm] = {
                "n_facts": len(facts),
                "second_person": second_person,
                "replay_ratio": replay_ratio,
            }
            bins[arm] = {}
            for ratio in (lo, hi):
                bin_path = scratch / f"{arm}_{ratio!r}.bin"
                mask_path = scratch / f"{arm}_{ratio!r}_mask.bin"
                episodes = tp.render_episodes(
                    facts, fs.TAUGHT_FAMILY_IDS, second_person=second_person
                )
                seed_everything(tp.SEED)
                tok = from_json(tp.TOKENIZER_PATH)
                # Argument for argument, build_arm_bins' flat-branch call. build_arm_bins itself
                # is not called: it writes into the real data/ (T-30-16).
                stats = tp.build_bins(
                    tok,
                    episodes,
                    bin_path,
                    mask_path,
                    replay_ratio=replay_ratio,
                    align_facts=None,
                    adversarial_ratio=ratio,
                    seed=tp.SEED,
                )
                builds[arm, ratio] = {
                    "stats": stats,
                    "scored": int(np.fromfile(mask_path, dtype=np.uint8).sum()),
                }
                bins[arm][repr(ratio)] = {
                    "bin_sha256": _sha256(bin_path),
                    "mask_sha256": _sha256(mask_path),
                }

    _prove(
        bins[advr] == bins[twin],
        f"the {advr} teaching bins differ from {twin}'s ({bins}): the structural reason — "
        "replay stays out of the teaching bin — is FALSE for this recipe. STOP for a ruling",
    )

    clean, pool = builds[advr, lo], builds[advr, hi]["stats"]
    S = clean["scored"]
    T0 = int(clean["stats"]["tokens"])
    P = int(pool["adversarial_episodes"])
    prompt = int(pool["adversarial_tokens"]) - int(pool["adversarial_scored_tokens"])
    band_floor = tp.MASK_FRACTION_BAND[0]
    margin = phase24_adversarial.MASK_FRACTION_MARGIN
    target = band_floor + margin

    def frac(L):
        return (S + P * L) / (T0 + prompt + P * L)

    L = next(L for L in itertools.count(1) if frac(L) >= target)
    _prove(
        L == phase24_adversarial.MIN_REFUSAL_SCORED_TOKENS,
        f"D-08: the re-derived floor is {L}, not the frozen v4.0 MIN_REFUSAL_SCORED_TOKENS "
        f"{phase24_adversarial.MIN_REFUSAL_SCORED_TOKENS}; REFUSING to write. STOP for the "
        "developer's ruling; the constant is never re-pinned silently",
    )
    return {
        "inputs": {
            "clean_scored_tokens": S,
            "clean_tokens": T0,
            "attack_pool_episodes": P,
            "pool_prompt_tokens": prompt,
        },
        "corners": [lo, hi],
        "band_floor": band_floor,
        "margin": margin,
        "target": target,
        "derived_floor": L,
        "frac_at_floor": frac(L),
        "frac_below_floor": frac(L - 1),
        "bins": bins,
        "arm_spec": specs,
        "bins_identical_advr_vs_adv": True,
        "structural_reason": (
            "Train-time replay is a separate loss pass in train(), one replay mean per optimizer "
            "step drawn from the replay source, and never enters the teaching bin, so the "
            "bin-level D-05 derivation is unchanged. Evidence: (1) built from each arm's full "
            "arm_spec triple through the build_bins flat-branch arguments build_arm_bins "
            f"passes, the {advr} teaching bins are byte-identical to {twin}'s at both corners; "
            "(2) the replay volume is measured separately at train time: "
            "tests/test_phase30_seam.py::test_advr_draws_the_prereg_replay_count counts "
            "phase29_prereg.replay_windows(n) replay windows per step through train()'s on_draw "
            "hook at both legs."
        ),
    }


def descriptive_step_mix():
    """D-07: the per-step teaching:replay mix per leg. DESCRIPTIVE — read by no verdict."""
    import teach_persona as tp

    mix = {}
    for leg in phase29_prereg.LEGS:
        replay = phase29_prereg.replay_windows(int(leg.removeprefix("n")))
        mix[leg] = {
            "teaching_windows": tp.BATCH_SIZE,
            "replay_windows": replay,
            "teaching_tokens": tp.BATCH_SIZE * tp.BLOCK_SIZE,
            "replay_tokens": replay * tp.BLOCK_SIZE,
            "loss_weighting": (
                "one teaching-batch mean + one replay mean per optimizer step, weighted 1:1 by "
                "train()"
            ),
        }
    mix["gates_nothing"] = True
    mix["role"] = "DESCRIPTIVE: read by no verdict (for Phase 34's window-asymmetry report)"
    return mix


def build_record():
    return {
        "requirement": "ARECIPE-02",
        "derivation": derive(),
        "recipe": {leg: phase30_points.recipe_identity(leg) for leg in phase29_prereg.LEGS},
        "min_refusal_scored_tokens": phase24_adversarial.MIN_REFUSAL_SCORED_TOKENS,
        "descriptive_step_mix": descriptive_step_mix(),
        "provenance": None,
    }


def emit(out_path=RECORD):
    """Write-once: overwrite refusal FIRST, dirty-tree refusal SECOND, then measure and write."""
    out_path = pathlib.Path(out_path)
    _prove(
        not out_path.exists(),
        f"{_rel(out_path)} exists — REFUSING to overwrite it. The calibration is write-once; "
        "corrections are dated continuations",
    )
    pathspec = ("scripts", "src", "results")
    if out_path.is_relative_to(_ROOT):
        pathspec += (f":(exclude){_rel(out_path)}",)
    refuse_if_dirty(
        who="phase30_calibration",
        detail=(
            "the calibration publishes git_sha and hashes its pinned modules from the working "
            "tree; a record written from a dirty tree names a commit it cannot be regenerated from"
        ),
        pathspec=pathspec,
        cwd=_ROOT,
    )
    blob = build_record()
    blob["provenance"] = {
        "module_sha256": {rel: _sha256(_ROOT / rel) for rel in PINNED_MODULES},
        "git_sha": INSTRUMENT_GIT_SHA,
        "head_at_write": git_sha(),
        "written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    phase25_run.atomic_write_json(out_path, blob)
    d = blob["derivation"]
    print(
        f"[phase30_calibration] derived floor {d['derived_floor']} at target {d['target']} — "
        f"wrote {_rel(out_path)}"
    )
    return blob


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    _prove(not argv, f"usage: python scripts/phase30_calibration.py (no arguments; got {argv})")
    emit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
