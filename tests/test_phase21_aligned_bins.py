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

import numpy as np
import pytest

from personacore.training.data import fact_window_impurities

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
