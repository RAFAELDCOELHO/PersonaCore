"""ADVT-01 — the ``build_bins(..., adversarial_ratio=...)`` seam: wired, byte-identical, seed-pure.

**The pair discipline, inherited verbatim from ``tests/test_phase21_aligned_bins.py``'s
byte-identity block.** A byte-identity assertion with no paired non-identity assertion is
VACUOUS: an ``adversarial_ratio=0.0`` build is trivially byte-identical to a no-kwarg build when
the kwarg is a parameter nobody reads. So :func:`test_adversarial_ratio_is_wired` comes FIRST in
this file, in ``test_align_facts_is_wired``'s register, and it was watched RED before the kwarg
existed.

CPU-only, GPU/MPS-free. Every episode count, pool size and ratio below is DERIVED from the
production artifacts (``phase24_adversarial.adversarial_pool_size``,
``mitigation_budget.ADVERSARIAL_RATIO_GRID``) — no count is retyped as a literal, so a shrunken
corpus fails these tests instead of agreeing with a stale number.
"""

import hashlib
import math
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

# The upper extreme of D-09's pinned grid, read from the grid rather than retyped: it is
# `pool / 176` by construction, so a moved pool moves it too.
UPPER = mb.ADVERSARIAL_RATIO_GRID[-1]
NONZERO_RATIOS = mb.ADVERSARIAL_RATIO_GRID[1:]


def _sha256(path):
    """BYTES, never text — the ``tests/test_package.py:36`` rule."""
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _tokenizer():
    seed_everything(tp.SEED)
    return from_json(tp.TOKENIZER_PATH)


def _clean_episodes():
    """The n=8 teaching pool — the same 176 episodes ``build_arm_bins('dp_n8', ...)`` renders."""
    return tp.render_episodes(fs.LOCKED_FACTS, fs.TAUGHT_FAMILY_IDS)


def _build(tmp_path, name, episodes, **kwargs):
    """One build under ``tmp_path``; returns ``(stats, bin_path, mask_path)``.

    ``tests/test_phase21_aligned_bins.py::_build``'s shape: ``seed_everything`` then the FROZEN
    production tokenizer. Never trains and never fakes a tokenizer.
    """
    tok = _tokenizer()
    bin_path = tmp_path / f"{name}.bin"
    mask_path = tmp_path / f"{name}_mask.bin"
    stats = tp.build_bins(tok, episodes, bin_path, mask_path, **kwargs)
    return stats, bin_path, mask_path


# =============================================================================================
# ===== 1. THE LOAD-BEARING HALF ==============================================================
# =============================================================================================


def test_adversarial_ratio_is_wired(tmp_path):
    """THE LOAD-BEARING HALF. Without this, every byte-identity assertion here is VACUOUS.

    If this test passes BEFORE the seam is wired, ``adversarial_ratio`` is a kwarg nobody reads
    and ``test_the_default_path_is_byte_identical_to_the_no_kwarg_call`` below is trivially true —
    it would be asserting that an ignored argument changes nothing, which is a tautology dressed
    as a guarantee. This is ``tests/test_phase21_aligned_bins.py::test_align_facts_is_wired``
    applied to the second mixture kwarg.
    """
    episodes = _clean_episodes()
    pool_size = pa.adversarial_pool_size(_tokenizer())
    off = _build(tmp_path, "off", episodes, adversarial_ratio=0.0)
    on = _build(tmp_path, "on", episodes, adversarial_ratio=UPPER)

    assert _sha256(on[1]) != _sha256(off[1]), (
        "the token bin is byte-identical at adversarial_ratio=0.0 and at the grid's upper "
        f"extreme {UPPER} — adversarial_ratio is NOT READ, so every adversarial_ratio=0.0 "
        "byte-identity assertion in this module is VACUOUS"
    )
    assert _sha256(on[2]) != _sha256(off[2]), (
        "the MASK bin did not move while the token bin did — adversarial material entered the "
        "corpus without its mask, so the refusals would train unscored"
    )
    added = on[0]["episodes"] - off[0]["episodes"]
    assert added == round(UPPER * len(episodes)) == pool_size, (
        f"the mixed build added {added} episodes against round({UPPER} * {len(episodes)}) = "
        f"{round(UPPER * len(episodes))}, which D-09 pins equal to the pool size {pool_size} — "
        "adversarial_ratio is not being read as an episodes-per-clean-episode ratio"
    )


# =============================================================================================
# ===== 2. THE BYTE-IDENTITY HALF (SC1) =======================================================
# =============================================================================================


def test_the_default_path_is_byte_identical_to_the_no_kwarg_call(tmp_path):
    """SC1: passing ``adversarial_ratio=0.0`` equals not passing it at all — bins AND stats.

    The no-kwarg build is taken FIRST and deliberately: it is the only half of this test that is
    observable before the seam exists (Python raises ``TypeError`` on the explicit kwarg before
    any assertion below can run), so its digests are the pre-wiring baseline the byte-identity
    claim is measured against. ``repr(stats)`` is compared as well as the bytes, because
    ``tests/test_phase21_aligned_bins.py:226`` pins that repr against the v2.0 golden fixture —
    a new stats key on the default path would redden SC1's own guard without moving a bin byte.
    """
    episodes = _clean_episodes()
    omitted = _build(tmp_path, "omitted", episodes)
    omitted_triple = (_sha256(omitted[1]), _sha256(omitted[2]), repr(omitted[0]))

    explicit = _build(tmp_path, "explicit", episodes, adversarial_ratio=0.0)
    explicit_triple = (_sha256(explicit[1]), _sha256(explicit[2]), repr(explicit[0]))

    assert explicit_triple == omitted_triple


# =============================================================================================
# ===== 3-4. D-08: THE PERMUTATION ============================================================
# =============================================================================================


def test_the_interleave_permutation_is_a_pure_function_of_the_seed(tmp_path):
    """D-08, in three directions: same seed identical, different seed different, inert at 0.0.

    A fresh runtime RNG would pass a naive determinism check taken inside one process and then
    break the Phase 23 D-07 resume path, which REBUILDS the bins and raises
    ``the resumed arm rebuilt a DIFFERENT corpus than the killed half trained on`` on any byte
    change. The different-seed half is what proves ``seed`` actually drives the permutation
    rather than being accepted and ignored — a constant permutation satisfies same-seed
    determinism perfectly.
    """
    episodes = _clean_episodes()
    a = _build(tmp_path, "seed_a", episodes, adversarial_ratio=UPPER, seed=tp.SEED)
    b = _build(tmp_path, "seed_b", episodes, adversarial_ratio=UPPER, seed=tp.SEED)
    c = _build(tmp_path, "seed_c", episodes, adversarial_ratio=UPPER, seed=tp.SEED + 1)

    assert (_sha256(a[1]), _sha256(a[2])) == (_sha256(b[1]), _sha256(b[2])), (
        "two builds at the SAME seed produced different bins — the permutation is not a pure "
        "function of the seed, so the Phase 23 resume rebuild-and-compare would refuse every "
        "resumed adversarial arm"
    )
    assert (_sha256(c[1]), _sha256(c[2])) != (_sha256(a[1]), _sha256(a[2])), (
        "two builds at DIFFERENT seeds produced identical bins — `seed` is accepted and ignored, "
        "so the permutation is a constant and same-seed determinism above proves nothing"
    )

    off_a = _build(tmp_path, "off_a", episodes, adversarial_ratio=0.0, seed=tp.SEED)
    off_b = _build(tmp_path, "off_b", episodes, adversarial_ratio=0.0, seed=tp.SEED + 1)
    assert (_sha256(off_a[1]), _sha256(off_a[2])) == (_sha256(off_b[1]), _sha256(off_b[2])), (
        "`seed` moved bytes on the DEFAULT path — the seam is not inert at adversarial_ratio=0.0 "
        "and SC1's byte-identity claim is false for any caller that passes a seed"
    )


def test_adversarial_episodes_are_interleaved_not_appended(tmp_path):
    """D-08's content claim, read off the WRITTEN BYTES rather than off the stats dict.

    **The observable, chosen and stated:** an appended layout is exactly ``clean_bytes +
    adversarial_bytes``, so the mixed bin's leading ``len(clean)`` elements would equal the
    ratio-0.0 bin element-for-element; a prepended layout is the same statement about its
    trailing elements. Both are asserted FALSE. The third assertion pins the head specifically:
    the first episode written is not clean episode 0. Together these reject every layout that
    concentrates the frame contrast at one seam — the shape D-08 rejected, because a model that
    meets 336 consecutive refusals after 176 consecutive facts learns the boundary, not the
    behaviour.

    Bytes, not a decode: ``detokenize`` is not guaranteed round-trip byte-equal, so a decoded
    comparison would be checking something adjacent to what was written.
    """
    episodes = _clean_episodes()
    clean = _build(tmp_path, "clean", episodes, adversarial_ratio=0.0)
    mixed = _build(tmp_path, "mixed", episodes, adversarial_ratio=UPPER)

    clean_ids = np.fromfile(clean[1], dtype=np.uint16)
    mixed_ids = np.fromfile(mixed[1], dtype=np.uint16)
    assert len(mixed_ids) > len(clean_ids)

    assert not np.array_equal(mixed_ids[: len(clean_ids)], clean_ids), (
        "the mixed bin OPENS with the whole clean corpus verbatim — the adversarial episodes "
        "were APPENDED, not interleaved (D-08)"
    )
    assert not np.array_equal(mixed_ids[-len(clean_ids) :], clean_ids), (
        "the mixed bin CLOSES with the whole clean corpus verbatim — the adversarial episodes "
        "were PREPENDED, not interleaved (D-08)"
    )

    first_clean, _mask = encode_dialogue(_tokenizer(), [], [episodes[0]])
    head = np.asarray(first_clean, dtype=np.uint16)
    assert not np.array_equal(mixed_ids[: len(head)], head), (
        "the mixed bin's FIRST episode is still clean episode 0 — the shard order was not "
        "permuted at all"
    )


# =============================================================================================
# ===== 5. D-06: THE SIZING UNIT ==============================================================
# =============================================================================================


def test_the_mixture_is_sized_from_episode_count_not_teaching_tokens(tmp_path):
    """D-06: the ratio is adversarial EPISODES per clean EPISODE, never per clean TOKEN.

    Two builds with the SAME episode count and deliberately DIFFERENT token totals must select
    the same number of adversarial episodes. If the sizing ever consulted ``teaching_tokens``
    the two diverge here.

    The shape being avoided is the one
    ``tests/test_phase21_replay_volume.py::test_replay_constant_is_not_derived_from_the_corpus``
    exists to police on the replay seam: a volume derived from the private corpus's size is a
    side channel that leaks how much private data there was. That test is left UNTOUCHED as a
    live tripwire; this one keeps the second mixture seam off the same route by construction.
    """
    episodes = _clean_episodes()
    inflated = [(question, f"{answer} {answer}") for question, answer in episodes]
    assert len(inflated) == len(episodes)

    lean = _build(tmp_path, "lean", episodes, adversarial_ratio=UPPER)
    fat = _build(tmp_path, "fat", inflated, adversarial_ratio=UPPER)

    assert fat[0]["teaching_tokens"] > lean[0]["teaching_tokens"], (
        "the two fixtures did not actually differ in token total, so this test could not have "
        "seen a teaching_tokens dependence even if one existed"
    )
    assert fat[0]["adversarial_episodes"] == lean[0]["adversarial_episodes"], (
        f"the mixture selected {fat[0]['adversarial_episodes']} episodes against "
        f"{lean[0]['adversarial_episodes']} for the SAME episode count at different token "
        "totals — the sizing is reading teaching_tokens (D-06's side channel), not len(episodes)"
    )


# =============================================================================================
# ===== 6. D-10 AT THE SELECTED PREFIX ========================================================
# =============================================================================================


@pytest.mark.parametrize("ratio", NONZERO_RATIOS)
def test_every_grid_point_trains_all_three_families_in_balance(tmp_path, ratio):
    """D-10's "three families train", asserted where it can actually break: the SELECTED prefix.

    ``tests/test_phase24_adversarial.py`` (24-05) asserts the balance of the FULL 336-row pool,
    and that assertion cannot see this failure. ``_mix_adversarial`` selects
    ``(pool * ceil(n_want / len(pool)))[:n_want]``, so balance in the selected prefix is a
    property of the COMMITTED CORPUS'S ROW ORDER, not of the mixing code. Measured at HEAD
    2026-08-30 that order is a STRICT 3-cycle ``[A1-mild, A1-aggressive, A3] * 112`` and every
    grid point lands 15/15/14 or better — but nothing else asserts that ordering. If a rebuild
    ever reordered the corpus rows (grouping by family, say), every point below ratio ~0.64
    would silently train ONE family while 24-05's full-pool assertion stayed green.
    """
    episodes = _clean_episodes()
    stats, _bin_path, _mask_path = _build(
        tmp_path, f"grid_{ratio}", episodes, adversarial_ratio=ratio
    )
    counts = stats["adversarial_family_counts"]
    n_want = stats["adversarial_episodes"]

    assert n_want == round(ratio * len(episodes)) >= 1
    assert set(counts) == set(pa.TRAINED_FAMILIES), (
        f"the selected prefix carries families {sorted(counts)} against the declared trained set "
        f"{sorted(pa.TRAINED_FAMILIES)} — the committed corpus's ROW ORDER moved, and this grid "
        "point now trains a different family mix than D-10 declared"
    )
    assert min(counts.values()) >= 1, (
        f"at ratio {ratio} the selected prefix is {dict(counts)} — a trained family contributes "
        "ZERO episodes. The corpus row order moved: a family-grouped order makes the first "
        f"{n_want} rows a single family while the full-pool balance stays green"
    )
    assert max(counts.values()) - min(counts.values()) <= 1, (
        f"at ratio {ratio} the selected prefix is {dict(counts)}, spread "
        f"{max(counts.values()) - min(counts.values())} > 1. The strict 3-cycle in the committed "
        "corpus row order is what held this at <= 1; that order moved"
    )
    assert sum(counts.values()) == n_want, (
        f"the per-family counts {dict(counts)} sum to {sum(counts.values())} against "
        f"{n_want} placed episodes — the reported counts are not the counts of what was placed"
    )
    # The ceiling repetition is what makes every point above ratio 1.909 reuse pool rows; below
    # it the selection is a strict prefix. Both are covered by the equality above.
    assert n_want <= math.ceil(ratio * len(episodes))
