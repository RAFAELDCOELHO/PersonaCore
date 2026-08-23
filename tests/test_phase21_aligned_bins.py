"""The fact-aligned bin path: window purity (D-05 / SC2) and `align_facts=None` byte-identity.

``fact_window_impurities`` is the ONE purity predicate — the packer's build-time proof, the
loader's run-time check (plan 21-06) and these tests all drive the same implementation, so
there is no second copy to drift.

These follow ``tests/test_masked_batch.py:8-10``'s governing discipline verbatim: *hand-built
exactness fixtures (Pitfall 14 — off-by-ones can ONLY hide from tests that recompute the
expectation)*. Every fact-id array AND every expected impure-row list below is a HAND-WRITTEN
LITERAL, never derived in-test from cumulative padded lengths — deriving them would make this
an offset check wearing a content check's name (the warning sign is a test importing the
packer's length helper).

CPU-only, GPU/MPS-free. Do NOT weaken any assertion to make these pass.
"""

import hashlib
import json
import pathlib
import sys

import numpy as np
import pytest

from personacore.seeding import seed_everything
from personacore.tokenizer import from_json
from personacore.training.data import fact_window_impurities

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import phase14_factset as fs  # noqa: E402  (scripts/ is not a package)
import teach_persona as tp  # noqa: E402

GOLDEN_PATH = _ROOT / "tests" / "fixtures" / "golden_build_bins_v2.json"
GOLDEN = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))

BLOCK = 4

# 3 facts of lengths (5, 3, 6) padded RAGGED to windows (2, 1, 2) = 5 windows, plus the
# one-element LABEL-SHIFT TAIL => 5 * 4 + 1 = 21 elements. Padding slots carry the OWNING
# fact's id (a sentinel would put two ids in every fact's last window in INPUT space, and
# sentinel 0 collides with fact index 0).
#              window 0     window 1     window 2     window 3     window 4    tail
GOOD = np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2], dtype=np.uint16)

# A1 — the load-bearing adversary: every element rolled right by one, tail re-appended. Same
# length, same multiset, same remainder as GOOD; only a POSITIONAL read in INPUT space sees it.
A1 = np.array([2, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2], dtype=np.uint16)

# A2 — one interior slot mislabelled inside fact 0's second window.
A2 = np.array([0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2], dtype=np.uint16)

# A3 — the PADDING-LABELLING error: fact 0's final pad slot carries a foreign id.
A3 = np.array([0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2], dtype=np.uint16)

# A4 — truncated by one: (len - 1) % BLOCK == 3, so the LENGTH contract fires, not the loop.
A4 = np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2], dtype=np.uint16)

# A5 — 4 pure windows where 5 were expected. Content purity alone does NOT pin n_facts.
A5 = np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2], dtype=np.uint16)


def test_a1_is_the_roll_it_claims_to_be():
    """The literal above must not drift from the adversary it is described as."""
    rolled = np.concatenate([np.roll(GOOD[:-1], 1), GOOD[-1:]])
    assert np.array_equal(A1, rolled)


@pytest.mark.parametrize(
    ("name", "fact_ids", "expected"),
    [
        ("A0-good", GOOD, []),  # negative control
        ("A1-roll", A1, [0, 2, 3]),  # the load-bearing case
        ("A2-interior", A2, [1]),
        ("A3-padding", A3, [1]),
        ("A5-short", A5, []),  # pure, but four windows where five were expected
    ],
)
def test_window_purity_adversaries_input_space(name, fact_ids, expected):
    assert fact_window_impurities(fact_ids, BLOCK) == expected, name


def test_window_purity_adversaries_a4_raises_on_length():
    """A4 fires the LENGTH contract, distinguishably from the purity loop."""
    with pytest.raises(ValueError) as excinfo:
        fact_window_impurities(A4, BLOCK)
    message = str(excinfo.value)
    assert "20" in message, message  # the observed length
    assert "4" in message, message  # the block size
    assert "3" in message, message  # the remainder
    assert "impure" not in message.lower(), message  # not the purity loop's finding


def test_window_purity_input_is_the_default():
    """`space="input"` is SC2's claim verbatim, and it is what an omitted kwarg selects."""
    assert fact_window_impurities(GOOD, BLOCK) == fact_window_impurities(GOOD, BLOCK, space="input")
    assert fact_window_impurities(GOOD, BLOCK) == []


def test_window_purity_target_boundary_rows_are_a_positive_claim():
    """Target space on a CORRECT bin has EXACTLY `n_facts - 1` rows — never `[]`.

    Window k's target slice ends at element `(k+1)*BLOCK`, the FIRST token of window k+1;
    when window k is a fact's last window that element belongs to the NEXT fact. Inherent to
    the +1 label shift, and no padding scheme removes it.
    """
    n_facts = 3
    assert fact_window_impurities(GOOD, BLOCK, space="target") == [1, 2]
    assert len(fact_window_impurities(GOOD, BLOCK, space="target")) == n_facts - 1

    # The boundary elements are literals too, and each is the NEXT fact's index.
    assert GOOD[8] == 1
    assert GOOD[12] == 2
    assert GOOD[8] == GOOD[4] + 1
    assert GOOD[12] == GOOD[8] + 1


def test_offsets_alone_cannot_see_the_roll():
    """Evidence, not prose: the WEAK checks are asserted PASSING on A1.

    A1 preserves length, the distinct-id multiset and the block remainder, so every
    offset-shaped check agrees with GOOD. Only a positional INPUT-space read separates them.
    """
    assert len(A1) == len(GOOD)
    assert sorted(np.bincount(A1[:-1]).tolist()) == sorted(np.bincount(GOOD[:-1]).tolist())
    assert (len(A1) - 1) % BLOCK == (len(GOOD) - 1) % BLOCK == 0

    # ...and a TARGET-space reading misses the roll entirely — the second, independent reason
    # `space="input"` is the default. Measured, not argued.
    assert fact_window_impurities(A1, BLOCK, space="target") == []

    # The strong check is what separates them.
    assert fact_window_impurities(A1, BLOCK) == [0, 2, 3]


def test_unknown_space_raises():
    with pytest.raises(ValueError):
        fact_window_impurities(GOOD, BLOCK, space="union")


# ===================================================================================
# ===== The byte-identity PAIR. A byte-identity assertion with no paired ===========
# ===== non-identity assertion is VACUOUS: `X=None` is trivially satisfied =========
# ===== by a kwarg that is never read. Every identity test here is half a pair. ====
# ===================================================================================

BLOCK_SIZE = 256  # ModelConfig.block_size, mirrored from teach_persona.BLOCK_SIZE


def _sha256(path):
    """BYTES, never text — the tests/test_package.py:36 rule."""
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _golden_facts():
    """The captured recipe's facts, resolved BY ID from the fixture rather than assumed."""
    return [fs._BY_ID[fid] for fid in GOLDEN["meta"]["facts"]]


def _build(tmp_path, name, **kwargs):
    """One flat v2.0 or aligned build under tmp_path; returns (stats, bin_path, mask_path)."""
    seed_everything(tp.SEED)
    tok = from_json(tp.TOKENIZER_PATH)
    bin_path = tmp_path / f"{name}.bin"
    mask_path = tmp_path / f"{name}_mask.bin"
    stats = tp.build_bins(tok, kwargs.pop("episodes"), bin_path, mask_path, **kwargs)
    return stats, bin_path, mask_path


def _golden_episodes():
    return tp.render_episodes(
        _golden_facts(),
        GOLDEN["meta"]["family_ids"],
        second_person=GOLDEN["meta"]["second_person"],
    )


def _aligned_pairs():
    """The PINNED shape: (fact, that fact's already-rendered episodes) pairs."""
    return [(f, tp.render_episodes([f], fs.TAUGHT_FAMILY_IDS)) for f in fs.LOCKED_FACTS]


def test_build_bins_byte_identity_omitted_equals_align_facts_none(tmp_path):
    """Omitting the kwarg equals passing None explicitly.

    This half never reads a platform identity and never skips, so CI relies on it
    unconditionally. It CANNOT see a change that moves BOTH branches — which is precisely
    why the golden fixture below is a second, independent tier.
    """
    episodes = _golden_episodes()
    omitted = _build(tmp_path, "omitted", episodes=episodes, replay_ratio=0.0)
    explicit = _build(tmp_path, "explicit", episodes=episodes, replay_ratio=0.0, align_facts=None)

    omitted_triple = (_sha256(omitted[1]), _sha256(omitted[2]), repr(omitted[0]))
    explicit_triple = (_sha256(explicit[1]), _sha256(explicit[2]), repr(explicit[0]))
    assert omitted_triple == explicit_triple


def test_build_bins_byte_identity_default_matches_the_v2_golden(tmp_path):
    """`align_facts=None` is BYTE-IDENTICAL to the pre-edit v2.0 capture (plan 21-02)."""
    tokenizer_sha = _sha256(tp.TOKENIZER_PATH)
    if tokenizer_sha != GOLDEN["meta"]["tokenizer_sha256"]:
        pytest.fail(
            f"THE FIXTURE IS STALE, not the code: {GOLDEN_PATH.name} was captured against "
            f"tokenizer sha256 {GOLDEN['meta']['tokenizer_sha256']} but "
            f"{tp.TOKENIZER_PATH} now hashes to {tokenizer_sha}. Re-capture the fixture; do "
            "NOT edit build_bins to chase the digest."
        )

    # The fixture's own recipe constants must still name the same facts.
    assert list(_golden_facts()) == list(fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS)
    assert sorted(GOLDEN["meta"]["family_ids"]) == sorted(fs.TAUGHT_FAMILY_IDS)

    stats, bin_path, mask_path = _build(
        tmp_path,
        "golden",
        episodes=_golden_episodes(),
        replay_ratio=GOLDEN["meta"]["replay_ratio"],
    )

    assert _sha256(bin_path) == GOLDEN["token_bin_sha256"]
    assert _sha256(mask_path) == GOLDEN["mask_bin_sha256"]
    assert bin_path.stat().st_size == GOLDEN["token_bin_bytes"]
    assert mask_path.stat().st_size == GOLDEN["mask_bin_bytes"]
    assert repr(stats) == GOLDEN["stats_repr"]


def test_align_facts_is_wired(tmp_path):
    """THE LOAD-BEARING HALF. Without this the identity guard above is vacuous.

    If this test passes BEFORE the feature is wired, `align_facts` is a kwarg nobody reads
    and every `align_facts=None` byte-identity assertion is trivially true.
    """
    pairs = _aligned_pairs()
    stats, bin_path, mask_path = _build(tmp_path, "aligned", episodes=[], align_facts=pairs)
    fact_path = tp.fact_bin_path(bin_path)

    assert fact_path.exists(), (
        "the third bin did not appear — align_facts is not wired, so every "
        "align_facts=None byte-identity assertion in this module is VACUOUS"
    )
    assert _sha256(bin_path) != GOLDEN["token_bin_sha256"], (
        "the aligned build produced the v2.0 bytes — the padding changed nothing, so "
        "align_facts is not being read"
    )

    fact_ids = np.fromfile(fact_path, dtype=np.uint16)
    mask_ids = np.fromfile(mask_path, dtype=np.uint8)

    # INPUT space, the default — SC2's claim verbatim.
    assert fact_window_impurities(fact_ids, BLOCK_SIZE) == []

    # TARGET space — a POSITIVE, COUNTED, MASKED property of a correct bin, not an
    # inconvenience the input-space check happens to route around.
    boundaries = fact_window_impurities(fact_ids, BLOCK_SIZE, space="target")
    assert len(boundaries) == len(fs.LOCKED_FACTS) - 1 == 7
    for row in boundaries:
        at = (row + 1) * BLOCK_SIZE
        assert mask_ids[at] == 0
        assert int(fact_ids[at]) == int(fact_ids[row * BLOCK_SIZE]) + 1

    # D-01's RAGGED geometry, OBSERVED.
    assert stats["n_windows"] == 33
    assert stats["windows_per_fact"] == (4, 4, 4, 4, 4, 5, 4, 4)
    assert stats["pad_tokens"] == 867
    assert stats["teaching_tokens"] == 7581
    assert stats["n_facts"] == 8

    # `episodes` is PINNED on the aligned branch: it reports the pairs' total.
    assert stats["episodes"] == sum(len(eps) for _f, eps in pairs) == 176


def test_align_facts_refuses_a_nonempty_episodes_list(tmp_path):
    """Two sources of truth for one bin is AMBIGUOUS INPUT, never silently ignored."""
    with pytest.raises(SystemExit) as excinfo:
        _build(tmp_path, "ambiguous", episodes=_golden_episodes(), align_facts=_aligned_pairs())
    message = str(excinfo.value)
    assert "220" in message, message  # the flat episode count
    assert "8" in message, message  # the align_facts pair count


def test_three_bin_alignment_is_1to1(tmp_path):
    """Proof 1 extended to three files, asserted from OUTSIDE the packer."""
    stats, bin_path, mask_path = _build(
        tmp_path, "three", episodes=[], align_facts=_aligned_pairs()
    )
    fact_path = tp.fact_bin_path(bin_path)

    token_bytes = bin_path.stat().st_size
    mask_bytes = mask_path.stat().st_size
    fact_bytes = fact_path.stat().st_size

    assert token_bytes // 2 == mask_bytes == fact_bytes // 2
    assert mask_bytes == stats["n_windows"] * BLOCK_SIZE + 1


def test_three_bin_alignment_truncation_raises_in_both_spaces(tmp_path):
    """The A4 class at the REAL block_size, not only at the toy BLOCK = 4.

    The remainder contract is SHARED by the two spaces, so a future edit that relaxes it for
    one space is caught here.
    """
    _stats, bin_path, _mask_path = _build(
        tmp_path, "trunc", episodes=[], align_facts=_aligned_pairs()
    )
    fact_path = tp.fact_bin_path(bin_path)
    truncated = np.fromfile(fact_path, dtype=np.uint16)[:-1]
    truncated.tofile(fact_path)

    reread = np.fromfile(fact_path, dtype=np.uint16)
    for space in ("input", "target"):
        with pytest.raises(ValueError) as excinfo:
            fact_window_impurities(reread, BLOCK_SIZE, space=space)
        assert "255" in str(excinfo.value), (space, str(excinfo.value))
