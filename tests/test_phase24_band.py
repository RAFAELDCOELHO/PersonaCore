"""D-05 — the mask fraction at ALL FOUR grid corners, measured BEFORE any sweep point runs.

**What this module buys.** ``teach_persona._prove_floor_and_band`` raises ``SystemExit`` at BUILD
time when the bin's aggregate mask fraction leaves ``MASK_FRACTION_BAND``. Without this module that
refusal surfaces after a sweep point's GPU compute is already spent; with it, it is a sub-second
CPU test. That conversion is the entire point of measuring first.

**Why FOUR corners and not two.** D-05 says "both extremes" of the ratio axis, but D-07 runs the
same nominal grid at BOTH capacities, so the grid is two-dimensional: ``{adv_n8, adv_n64}`` x
``{grid[0], grid[-1]}``. The binding corner is ``(adv_n8, upper)`` and
:func:`test_the_binding_corner_is_n8_at_the_upper_extreme` pins that as a measured property rather
than an assumption, because pinning against ``adv_n64`` would be pinning against the easier corner.
The parametrization is ORDERED so the binding corner runs first: the corner most likely to fail
fails in the first second.

**No band bound and no grid value is retyped here.** ``MASK_FRACTION_BAND`` comes from
``teach_persona``, ``MASK_FRACTION_MARGIN`` from ``phase24_adversarial`` and the two ratios from
``mitigation_budget.ADVERSARIAL_RATIO_GRID``. The only float literals in this file are the two
CONTROL fractions :data:`CONTROL_FRACTIONS` pins, which are the measured operating point and are
supposed to be literals.

CPU-only, GPU/MPS-free, no training, no ``data/`` write. Every build lands under ``tmp_path``.
"""

import pathlib
import sys

import numpy as np
import pytest

from personacore.dialogue import encode_dialogue
from personacore.seeding import seed_everything
from personacore.tokenizer import from_json

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import mitigation_budget as mb  # noqa: E402  (scripts/ is not a package)
import phase14_factset as fs  # noqa: E402
import phase24_adversarial as pa  # noqa: E402
import teach_persona as tp  # noqa: E402

# The two D-09 extremes, READ from the pinned grid. `LOWER` is the control (zero adversarial
# episodes, bins byte-identical to v2.0's); `UPPER` is `pool_size / 176` by construction, so a
# moved pool moves it and nothing here needs editing.
LOWER = mb.ADVERSARIAL_RATIO_GRID[0]
UPPER = mb.ADVERSARIAL_RATIO_GRID[-1]

# BINDING CORNER FIRST. `pytest -x` and a plain run both hit `(adv_n8, upper)` before anything
# else, which is what makes the single-node fast path in 24-VALIDATION.md's feedback contract
# worth having.
CORNERS = [
    pytest.param("adv_n8", UPPER, id="adv_n8-upper"),
    pytest.param("adv_n64", UPPER, id="adv_n64-upper"),
    pytest.param("adv_n8", LOWER, id="adv_n8-lower"),
    pytest.param("adv_n64", LOWER, id="adv_n64-lower"),
]

# The FLAT-pack operating point at `adversarial_ratio == 0.0`, measured at HEAD through
# `build_bins(..., align_facts=None)` — the pack the adversarial arms actually use, since neither
# `adv_n8` nor `adv_n64` is in `tp.DP_ARMS`.
#
# TWO TRAPS, named so a future reader cannot substitute past them:
#
#   * 0.321813 / 0.347701 are the ALIGNED dp_n8 / dp_n64 packs. `_build_aligned_bins` pads every
#     fact shard with mask=0 (dp_n8 carries 867 pad tokens), which depresses the fraction by ~0.037
#     and models a padding term the adversarial arm does not have. NOT substitutable here.
#   * 0.3426 / 0.3854 / 0.3778 are the v3.0 CAL arms, reachable only through
#     `phase21_unit_record._arm_rows` via `run_calibration` over `CAL_ARMS` — structurally
#     unreachable for any v4.0 arm. NOT substitutable here either.
#
# These two ARE float literals and that is deliberate: they are the measurement being pinned.
CONTROL_FRACTIONS = {"adv_n8": 0.358660, "adv_n64": 0.390163}


def _tokenizer():
    """``seed_everything`` then the FROZEN production tokenizer — never a fake, never retrained."""
    seed_everything(tp.SEED)
    return from_json(tp.TOKENIZER_PATH)


def _build_corner(tmp_path, arm, ratio):
    """Build one corner's flat bins under ``tmp_path``; return ``(stats, bin_path, mask_path)``.

    The arm's fact set is resolved through ``tp.arm_spec`` rather than rebuilt, so ``adv_n64``'s
    lazy ``phase21_filler`` import and its collision refusal both still run.
    """
    facts, _second_person, _replay_ratio = tp.arm_spec(arm)
    episodes = tp.render_episodes(facts, fs.TAUGHT_FAMILY_IDS)
    tmp_path.mkdir(parents=True, exist_ok=True)  # callers below pass per-corner subdirectories
    bin_path = tmp_path / f"{arm}.bin"
    mask_path = tmp_path / f"{arm}_mask.bin"
    stats = tp.build_bins(
        _tokenizer(),
        episodes,
        bin_path,
        mask_path,
        align_facts=None,
        adversarial_ratio=ratio,
        seed=tp.SEED,
    )
    return stats, bin_path, mask_path


# =============================================================================================
# ===== 1. THE FLOOR, AT EVERY CORNER =========================================================
# =============================================================================================


@pytest.mark.parametrize(("arm", "ratio"), CORNERS)
def test_all_four_grid_corners_clear_the_mask_fraction_floor_with_margin(tmp_path, arm, ratio):
    """Every D-05 corner clears ``MASK_FRACTION_BAND``'s floor by ``MASK_FRACTION_MARGIN``.

    Band and margin are both IMPORTED. A red here is D-05 doing its job, and the remedy is to
    LENGTHEN the refusal templates in ``scripts/phase24_adversarial.py`` — never to widen the band,
    which is Phase 14's and is not this phase's to move.
    """
    stats, _bin_path, _mask_path = _build_corner(tmp_path, arm, ratio)
    floor, ceiling = tp.MASK_FRACTION_BAND
    target = floor + pa.MASK_FRACTION_MARGIN
    frac = stats["mask_fraction"]

    assert frac >= target, (
        f"corner ({arm}, adversarial_ratio={ratio!r}) measured mask_fraction {frac:.6f} against a "
        f"floor of {floor} + MASK_FRACTION_MARGIN {pa.MASK_FRACTION_MARGIN} = {target:.6f} — "
        f"short by {target - frac:.6f}. teach_persona._prove_floor_and_band SystemExits below "
        f"{floor} at BUILD time, so this shortfall would otherwise surface after a sweep point's "
        "compute was already spent. Lengthen the refusal templates (raise "
        "phase24_adversarial.MIN_REFUSAL_SCORED_TOKENS and the per-slot noun phrases) until this "
        "corner clears; do NOT widen MASK_FRACTION_BAND."
    )

    # The ceiling is UNREACHABLE on this axis — an adversarial episode contributes a long unmasked
    # attack prompt and a short masked refusal, so both effects of the mixture push the fraction
    # DOWN. This assertion exists so that claim is CHECKED rather than argued; if it ever fires,
    # the one-sided reasoning behind ignoring the ceiling has stopped holding.
    assert frac <= ceiling, (
        f"corner ({arm}, adversarial_ratio={ratio!r}) measured mask_fraction {frac:.6f} ABOVE the "
        f"band ceiling {ceiling}. The mixture is supposed to push the fraction down on both "
        "counts, so the one-sided floor-only analysis in 24-RESEARCH no longer describes this "
        "axis and the corner analysis needs redoing."
    )


def test_the_binding_corner_is_n8_at_the_upper_extreme(tmp_path):
    """``(adv_n8, upper)`` measures STRICTLY BELOW ``(adv_n64, upper)``.

    24-RESEARCH's refinement, pinned as a property. ``adv_n64``'s much larger clean bin dilutes the
    fixed 336-episode attack pool's unmasked prompt mass relative to its own scored mass, so n=64
    is the EASIER corner; calibrating the refusal length against it would leave n=8 uncovered.
    """
    n8, _b8, _m8 = _build_corner(tmp_path / "n8", "adv_n8", UPPER)
    n64, _b64, _m64 = _build_corner(tmp_path / "n64", "adv_n64", UPPER)

    assert n8["mask_fraction"] < n64["mask_fraction"], (
        f"the binding-corner analysis has INVERTED: adv_n8 at the upper extreme measured "
        f"{n8['mask_fraction']:.6f} and adv_n64 measured {n64['mask_fraction']:.6f}. Every "
        "headroom figure in 24-RESEARCH and phase24_adversarial.MIN_REFUSAL_SCORED_TOKENS' "
        "derivation is calibrated against n=8 as the WORST corner. If n=64 is now worse, the "
        "corner analysis and the refusal-length floor both need redoing against n=64."
    )


def test_the_control_corner_reproduces_the_measured_flat_operating_point(tmp_path):
    """At ``adversarial_ratio == 0.0`` both arms reproduce the FLAT operating point to 6 decimals.

    The two figures pinned in :data:`CONTROL_FRACTIONS` are the flat-pack fractions measured at
    HEAD. Neither the ALIGNED dp_n8/dp_n64 figures (0.321813 / 0.347701, depressed by
    ``_build_aligned_bins``' mask=0 padding) nor the v3.0 CAL figures (0.3426 / 0.3854 / 0.3778, a
    different arm set that no v4.0 arm can reach) may be substituted for them — see the module
    comment above :data:`CONTROL_FRACTIONS`.
    """
    for arm, expected in CONTROL_FRACTIONS.items():
        stats, _bin_path, _mask_path = _build_corner(tmp_path / arm, arm, LOWER)
        measured = round(stats["mask_fraction"], 6)
        assert measured == expected, (
            f"{arm} at the control corner measured {stats['mask_fraction']!r} "
            f"(rounded {measured}) against the pinned flat operating point {expected}. Either the "
            "clean teaching pack moved, or an aligned/CAL figure has been substituted for the "
            "flat one — the three sets are not interchangeable."
        )


# =============================================================================================
# ===== 2. THE PER-EPISODE MINIMUM — DECIDED, NOT LEFT OPEN ===================================
# =============================================================================================


def test_the_per_episode_floor_is_a_scored_token_count_and_not_a_fraction():
    """WHY ``stats["mask_fraction_min"]`` is deliberately NOT gated, checked rather than argued.

    24-06 recorded that ``mask_fraction_min`` reaches 0.1111 at the upper extreme — BELOW
    ``MASK_FRACTION_BAND``'s floor — while ``_prove_floor_and_band`` gates only the AGGREGATE.
    This test is 24-07's decision on that, and the decision is that a per-episode FRACTION floor
    would be the wrong instrument, for three MEASURED reasons:

      1. A per-episode fraction conflates "the answer is too short" with "the attack prompt is
         long". The 0.1111 episode is an A3 one — 18 scored tokens in 162 — and A3's whole design
         is a long value-free role scaffold riding at mask=0. Gating the fraction would refuse the
         attack shape D-10 deliberately trains on.
      2. The quantity that IS well defined per episode is the SCORED-TOKEN COUNT, and it already
         has a floor: ``MIN_REFUSAL_SCORED_TOKENS``. Every adversarial episode clears it.
      3. The CLEAN teaching episodes carry FEWER scored tokens than any adversarial one, and have
         never been gated per-episode in this repository's history. A per-episode floor introduced
         for the adversarial half only would be gating the population that needs it least.

    So the assertion below is the per-episode invariant that has content: every refusal is at least
    ``MIN_REFUSAL_SCORED_TOKENS`` scored tokens long, measured through the frozen tokenizer.
    """
    tok = _tokenizer()
    episodes = pa.adversarial_episodes(tok)
    assert episodes, "the attack pool is empty — every assertion below would be vacuous"

    scored = []
    for persona, question, answer in episodes:
        _ids, mask = encode_dialogue(tok, list(persona), [(question, answer)])
        scored.append(int(np.asarray(mask, dtype=np.uint8).sum()))

    assert min(scored) >= pa.MIN_REFUSAL_SCORED_TOKENS, (
        f"the shortest of {len(scored)} adversarial episodes scores {min(scored)} tokens against "
        f"MIN_REFUSAL_SCORED_TOKENS = {pa.MIN_REFUSAL_SCORED_TOKENS}. That floor is D-05's actual "
        "per-episode instrument — the fraction is not, because it moves with the attack prompt's "
        "length rather than with the refusal's."
    )

    # The clean half, measured in the same breath, is what makes reason 3 a measurement: an
    # adversarial-only per-episode floor would gate the LONGER answers and leave the shorter ones
    # alone.
    clean_scored = []
    for question, answer in tp.render_episodes(fs.LOCKED_FACTS, fs.TAUGHT_FAMILY_IDS):
        _ids, mask = encode_dialogue(tok, [], [(question, answer)])
        clean_scored.append(int(np.asarray(mask, dtype=np.uint8).sum()))

    assert min(clean_scored) <= min(scored), (
        f"the clean teaching pool's shortest answer now scores {min(clean_scored)} tokens against "
        f"the adversarial pool's {min(scored)} — the adversarial half has become the shorter one, "
        "so reason 3 in this test's docstring (an adversarial-only per-episode floor would gate "
        "the population that needs it least) no longer holds and the decision needs revisiting."
    )
