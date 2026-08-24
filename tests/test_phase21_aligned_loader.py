"""D-06: the fact map is CONSUMED AT RUN TIME, not merely asserted once at build time.

The claim is NOT "the fact bin exists" and NOT "the fact bin was once correct". It is: *the
loader's output is a function of the fact bin's CURRENT on-disk contents, evaluated on EVERY
access.*

That phrasing names the instrument. A test that builds bins and asserts the loader returns
fact-aligned batches passes IDENTICALLY whether the loader reads ``*_fact.bin`` or reconstructs
the boundaries from its own copy of the padded lengths — one input class, two implementations,
no discrimination. Asserting the third bin exists and is the right length is ``build_bins``'
proof-1 extended, a BUILD-TIME check, and D-06 is explicitly the claim that build time is not
enough.

The only instrument that separates them is a mutation of the fact bin BETWEEN two calls in one
process, with the other two bins proven byte-frozen by ``sha256``. That is N1-N6 below.

``tests/test_phase21_aligned_bins.py`` owns the aligned-corpus builder; it is IMPORTED here,
never re-written — a second copy of the build recipe is a second thing free to drift from the
bin the packer's own proofs run against.

CPU-only, GPU/MPS-free, no network. Everything under ``tmp_path``; nothing writes into ``data/``.
Do NOT weaken any assertion to make these pass.
"""

import hashlib
import pathlib
import shutil
import sys
from typing import NamedTuple

import numpy as np
import pytest
import torch

from personacore.training.data import (
    fact_window_impurities,
    fact_window_span,
    get_batch_fact_aligned,
)

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT / "tests"))

import teach_persona as tp  # noqa: E402  (scripts/ is not a package)

from test_phase21_aligned_bins import (  # noqa: E402  (tests/ is not one either)
    _aligned_pairs,
    _build,
)

BLOCK = tp.BLOCK_SIZE  # 256 — resolved from the module, never re-spelled as a literal


class Bins(NamedTuple):
    """The three 1:1 bins plus the packer's stats. ``fact`` is resolved via ``fact_bin_path``."""

    tokens: pathlib.Path
    mask: pathlib.Path
    fact: pathlib.Path
    stats: dict


def _sha(path):
    """BYTES, never text — the tests/test_package.py:36 rule."""
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _draw(bins, step, n_facts=None):
    """One micro-step through the loader under test. CPU device, always."""
    return get_batch_fact_aligned(
        bins.tokens,
        bins.mask,
        bins.fact,
        BLOCK,
        "cpu",
        step=step,
        n_facts=bins.stats["n_facts"] if n_facts is None else n_facts,
    )


@pytest.fixture(scope="module")
def _built(tmp_path_factory):
    """Build the REAL 8-fact aligned corpus ONCE (D-01's ragged geometry, block_size = 256).

    A toy corpus would not let the observed ``(start, k)`` per fact be checked against D-01's
    measured ``windows_per_fact``, which is the point of drawing through the real packer.
    """
    base = tmp_path_factory.mktemp("aligned_src")
    stats, bin_path, mask_path = _build(base, "loader", episodes=[], align_facts=_aligned_pairs())
    return Bins(bin_path, mask_path, tp.fact_bin_path(bin_path), stats)


@pytest.fixture
def bins(_built, tmp_path):
    """A private COPY of the three bins per test — every test here mutates files on disk."""
    copies = [shutil.copy2(p, tmp_path / p.name) for p in (_built.tokens, _built.mask, _built.fact)]
    tokens, mask, fact = (pathlib.Path(p) for p in copies)
    assert fact == tp.fact_bin_path(tokens), "the fact bin must resolve through fact_bin_path()"
    return Bins(tokens, mask, fact, _built.stats)


# ===================================================================================
# ===== THE LOAD-BEARING TEST. Everything else in this module exists to stop ========
# ===== it collapsing into "assert something raised". ===============================
# ===================================================================================


def test_fact_map_is_consumed_at_runtime(bins):
    """Mutate ONE interior element of the fact bin between two calls IN ONE PROCESS.

    A loader that reconstructs boundaries from a stored ``cumsum`` of the padded lengths returns
    ``first == second`` here, and that RED means exactly "the map is not consumed".
    """
    original_fact_sha, tok_sha, mask_sha = _sha(bins.fact), _sha(bins.tokens), _sha(bins.mask)

    first = _draw(bins, step=0)

    at = BLOCK // 2  # interior of window 0, NOT a window start — owners are untouched
    fact_ids = np.fromfile(bins.fact, dtype=np.uint16)
    assert int(fact_ids[at]) == 0, "window 0 must belong to fact 0 before the mutation"
    fact_ids[at] = fact_ids[at] + 1
    fact_ids.tofile(bins.fact)

    # ONLY the fact bin moved. Asserted BEFORE the behavioural assertion so a page-cache
    # surprise (assumption A1 — memmap re-open coherence was measured on Darwin only) fails
    # with a message naming the cause instead of flaking.
    assert _sha(bins.tokens) == tok_sha, "the TOKEN bin moved — this test no longer isolates"
    assert _sha(bins.mask) == mask_sha, "the MASK bin moved — this test no longer isolates"
    assert _sha(bins.fact) != original_fact_sha, "the mutation is not VISIBLE on disk"

    with pytest.raises(ValueError) as impure:
        _draw(bins, step=0)
    assert "fact" in str(impure.value).lower(), str(impure.value)  # name the bin, not "raised"

    # Byte-identical restore, proven by sha256 OF THE FILE — not by "we put the value back".
    fact_ids[at] = fact_ids[at] - 1
    fact_ids.tofile(bins.fact)
    assert _sha(bins.fact) == original_fact_sha

    second = _draw(bins, step=0)
    assert torch.equal(second[0], first[0])
    assert torch.equal(second[1], first[1])
    assert second[2] == first[2] == 0


# ===================================================================================
# ===== N1-N4: each red distinguished by WHICH assertion fired. =====================
# ===================================================================================


def _n1_delete(path):
    path.unlink()


def _n2_truncate(path):
    np.fromfile(path, dtype=np.uint16)[:-1].tofile(path)


def _n3_roll(path):
    ids = np.fromfile(path, dtype=np.uint16)
    np.concatenate([np.roll(ids[:-1], 1), ids[-1:]]).tofile(path)


def _n4_flip_interior(path):
    ids = np.fromfile(path, dtype=np.uint16)
    ids[BLOCK // 2] = ids[BLOCK // 2] + 1
    ids.tofile(path)


@pytest.mark.parametrize(
    ("name", "mutate", "must_contain", "forbidden"),
    [
        # N1 — the failure mode the objective names: the third bin silently dropped.
        ("N1-deleted", _n1_delete, ["could not be opened", "_fact.bin"], ["IMPURE"]),
        # N2 — proof-1 extended from two files to three: ALL THREE lengths in the message.
        ("N2-truncated", _n2_truncate, ["not 1:1", "8449", "8448"], ["IMPURE"]),
    ],
)
def test_fact_bin_required_raises_distinguishably(bins, name, mutate, must_contain, forbidden):
    """N1/N2 — the loader RAISES, naming the FACT bin, on a missing or truncated fact map."""
    tok_sha, mask_sha = _sha(bins.tokens), _sha(bins.mask)
    mutate(bins.fact)

    with pytest.raises(ValueError) as excinfo:
        _draw(bins, step=0)
    message = str(excinfo.value)
    for fragment in must_contain:
        assert fragment in message, (name, message)
    for fragment in forbidden:
        assert fragment not in message, (name, message)
    assert str(bins.fact) in message, (name, message)  # WHICH of the three bins

    assert _sha(bins.tokens) == tok_sha and _sha(bins.mask) == mask_sha


def _n7_truncate_all_three(bins):
    """Drop the LABEL-SHIFT TAIL from all three bins at once — the shape N2 cannot see.

    N2 truncates the FACT bin ALONE, which breaks 1:1 and is caught by the length-equality
    guard. Truncating all three TOGETHER keeps 1:1 intact, which is what an interrupted or
    half-written build actually leaves behind.
    """
    for path, dtype in ((bins.tokens, np.uint16), (bins.mask, np.uint8), (bins.fact, np.uint16)):
        np.fromfile(path, dtype=dtype)[:-1].tofile(path)


def test_n7_all_three_bins_truncated_together_is_refused(bins):
    """N7 — the whole-bin ``n_windows * block_size + 1`` contract, which N1-N6 provably miss.

    MEASURED before the guard existed (real corpus, ``BLOCK=256``, 8 facts, the tail dropped
    from all three bins so they stay 1:1)::

        GOOD   window counts: [4, 4, 4, 4, 4, 5, 4, 4]
        NOTAIL window counts: [4, 4, 4, 4, 4, 5, 4, 3]   <-- NO RAISE
        packer said         : (4, 4, 4, 4, 4, 5, 4, 4)

    Every existing guard passed: the three bins were still 1:1 (8448 each), ``observed.size``
    was still 8, fact 7's remaining windows were still contiguous, and input-space purity on
    the drawn slice was still clean. ``n_windows = (len - 1) // block_size`` floored 33 to 32
    and fact 7 was served 3 of its 4 windows. Under D-03 the loss is a MEAN over the record's
    windows, so record 7's gradient was computed over three quarters of the record the
    accountant charges for — with ``grad_accum_steps = n_facts`` still reading true.

    The purity predicate cannot own this contract for the loader: the slice it is handed is
    always ``facts[start : start + k * block_size + 1]`` from a block-aligned ``start``, so its
    remainder is 0 BY CONSTRUCTION and its own guard is unreachable on that slice.
    """
    tail_owner = bins.stats["n_facts"] - 1
    good_len = len(np.fromfile(bins.fact, dtype=np.uint16))
    assert good_len == bins.stats["n_windows"] * BLOCK + 1

    # Non-vacuity, on THESE bytes, BEFORE the mutation: the guard must admit a correct bin.
    x, _y, fact_index = _draw(bins, step=tail_owner)
    assert fact_index == tail_owner
    assert x.shape[0] == bins.stats["windows_per_fact"][tail_owner]

    _n7_truncate_all_three(bins)
    lengths = [
        len(np.fromfile(p, dtype=d))
        for p, d in ((bins.tokens, np.uint16), (bins.mask, np.uint8), (bins.fact, np.uint16))
    ]
    # The adversary's whole point: 1:1 SURVIVES, so the sibling guard cannot fire.
    assert lengths == [good_len - 1] * 3
    assert (lengths[0] - 1) % BLOCK == BLOCK - 1 != 0

    with pytest.raises(ValueError) as excinfo:
        _draw(bins, step=tail_owner)
    message = str(excinfo.value)

    assert "LABEL-SHIFT TAIL" in message, message  # the contract, named
    assert str(BLOCK - 1) in message, message  # the remainder
    for path in (bins.tokens, bins.mask, bins.fact):
        assert str(path) in message, message  # all THREE paths, not just the fact bin
    assert message.count(str(good_len - 1)) >= 3, message  # all THREE lengths

    # Distinguishable from every sibling guard: a red here is identified by WHICH one fired.
    assert "not 1:1" not in message, message
    assert "IMPURE" not in message, message
    assert "distinct fact id" not in message, message
    assert "could not be opened" not in message, message

    # ROOT, not the call site: the shared span helper floors the same way and is called
    # DIRECTLY on a whole bin by scripts/phase21_unit_record.count_aligned, so it refuses too.
    with pytest.raises(ValueError) as span_exc:
        fact_window_span(np.fromfile(bins.fact, dtype=np.uint16), tail_owner, BLOCK)
    assert "LABEL-SHIFT TAIL" in str(span_exc.value), str(span_exc.value)


@pytest.mark.parametrize(
    ("name", "mutate"), [("N3-rolled", _n3_roll), ("N4-interior", _n4_flip_interior)]
)
def test_positional_mutation_raises_input_space_impurity(bins, name, mutate):
    """N3/N4 — correct offsets over WRONG BYTES. Only a positional INPUT-space read sees these."""
    tok_sha, mask_sha = _sha(bins.tokens), _sha(bins.mask)
    before = np.fromfile(bins.fact, dtype=np.uint16)
    mutate(bins.fact)
    after = np.fromfile(bins.fact, dtype=np.uint16)

    if name == "N3-rolled":
        # The roll preserves length AND the id multiset AND the block remainder, so every
        # offset-shaped check agrees with the correct bin. Evidence, not prose.
        assert len(after) == len(before)
        assert sorted(np.bincount(after[:-1]).tolist()) == sorted(np.bincount(before[:-1]).tolist())
        # ...and TARGET space misses the roll ENTIRELY. This is the second, independent reason
        # the draw-time check is input space: a target-space draw check would be blind here AND
        # would raise on every fact but the last on a correct bin.
        assert fact_window_impurities(after, BLOCK, space="target") == []

    with pytest.raises(ValueError) as excinfo:
        _draw(bins, step=0)
    message = str(excinfo.value)
    assert "IMPURE" in message, (name, message)
    assert "fact" in message.lower(), (name, message)
    assert "not 1:1" not in message, (name, message)  # not the length guard

    if name == "N4-interior":
        # "on exactly one window", asserted rather than assumed.
        assert message.count("carries ids") == 1, message
        assert "window 0 carries ids [0, 1]" in message, message

    assert _sha(bins.tokens) == tok_sha and _sha(bins.mask) == mask_sha


# ===================================================================================
# ===== N5 and N6: the two controls that stop this collapsing into ==================
# ===== "assert it raises". Without N5 a loader that ALWAYS raised passes N1-N4. ====
# ===================================================================================


def test_n5_unmutated_fact_bin_is_the_negative_control(bins):
    """N5 — no mutation at all: the loader returns normally and call 2 equals call 1."""
    fact_sha, tok_sha, mask_sha = _sha(bins.fact), _sha(bins.tokens), _sha(bins.mask)

    first = _draw(bins, step=0)
    second = _draw(bins, step=0)

    assert (_sha(bins.fact), _sha(bins.tokens), _sha(bins.mask)) == (fact_sha, tok_sha, mask_sha)
    assert torch.equal(second[0], first[0])
    assert torch.equal(second[1], first[1])
    assert second[2] == first[2] == 0


def test_n6_token_bin_mutation_leaves_fact_attribution_unchanged(bins):
    """N6 — proves WHICH file the guard reads: mutate a TOKEN, not a fact id.

    Easy to omit, and the only case that separates "reads the fact bin" from "reads the token
    bin and reports an attribution derived from it".
    """
    fact_sha, mask_sha = _sha(bins.fact), _sha(bins.mask)

    first = _draw(bins, step=0)

    at = BLOCK // 2  # far from any window boundary, inside fact 0's first window
    tokens = np.fromfile(bins.tokens, dtype=np.uint16)
    tokens[at] = tokens[at] + 1
    tokens.tofile(bins.tokens)

    assert _sha(bins.fact) == fact_sha, "the FACT bin moved — N6 no longer isolates"
    assert _sha(bins.mask) == mask_sha

    second = _draw(bins, step=0)
    assert second[2] == first[2] == 0, "fact attribution came from the TOKEN bin"
    assert not torch.equal(second[0], first[0]), "the token mutation is invisible in x"
    assert second[0].shape == first[0].shape


# ===================================================================================
# ===== The second negative control: a CORRECT bin must never raise, on ANY fact. ===
# ===================================================================================


def test_valid_bin_never_raises_on_any_fact(bins):
    """A draw-time check widened to TARGET space raises on every fact but the last — here.

    On a correct bin, window ``k``'s target slice ends at ``fact_ids[(k+1)*BLOCK]``, the first
    token of the NEXT window, which for a fact's last window belongs to the NEXT FACT. So a
    target-space draw check reddens on a perfectly built bin. This test is what makes that
    mistake a RED rather than a mystery.
    """
    n_facts = bins.stats["n_facts"]
    fact_ids = np.fromfile(bins.fact, dtype=np.uint16)

    observed = []
    for step in range(n_facts):
        start, k = fact_window_span(fact_ids, step, BLOCK)
        x, y, fact_index = _draw(bins, step=step)  # must not raise
        assert fact_index == step
        assert x.shape == y.shape == (k, BLOCK)
        observed.append((start, k))

    # D-01's RAGGED geometry, observed THROUGH THE LOADER rather than read off the packer.
    assert tuple(k for _start, k in observed) == bins.stats["windows_per_fact"]
    assert tuple(start for start, _k in observed) == (0, 1024, 2048, 3072, 4096, 5120, 6400, 7424)

    # WHY the draw check is input space, recorded as a measurement on this very bin rather
    # than asserted as a preference: target space carries exactly n_facts - 1 boundary rows.
    assert fact_window_impurities(fact_ids, BLOCK) == []
    boundaries = fact_window_impurities(fact_ids, BLOCK, space="target")
    assert len(boundaries) == n_facts - 1 == 7
    assert boundaries == [3, 7, 11, 15, 19, 24, 28]


# ===================================================================================
# ===== grad_accum_steps == n_facts, OBSERVED from the micro-step sequence. =========
# ===================================================================================


def test_grad_accum_steps_equals_n_facts(bins):
    """One lot = ``n_facts`` micro-steps covering every window EXACTLY ONCE.

    The count is read off the loop's actual returns, never declared from a bin's shape: that
    is the difference between ``grad_accum_steps = n_facts`` being true and being announced.
    """
    n_facts = bins.stats["n_facts"]
    fact_ids = np.fromfile(bins.fact, dtype=np.uint16)

    attribution, covered, rows = [], 0, []
    for step in range(n_facts):
        x, _y, fact_index = _draw(bins, step=step)
        attribution.append(fact_index)
        covered += x.shape[0]
        start, k = fact_window_span(fact_ids, fact_index, BLOCK)
        rows.extend(range(start // BLOCK, start // BLOCK + k))

    assert attribution == list(range(n_facts))  # no repeat, no gap
    assert _draw(bins, step=n_facts)[2] == 0  # the lot wraps

    # The conservation law at the loader tier: every window in the bin, exactly once.
    assert covered == bins.stats["n_windows"] == 33
    assert sorted(rows) == list(range(bins.stats["n_windows"]))
    assert len(set(rows)) == len(rows)


def test_n_facts_is_asserted_not_trusted(bins):
    """Content purity alone does not pin ``n_facts`` (the A5 class) — the loader asserts both."""
    with pytest.raises(ValueError) as excinfo:
        _draw(bins, step=0, n_facts=bins.stats["n_facts"] + 1)
    message = str(excinfo.value)
    assert "distinct fact id" in message, message
    assert "n_facts=9" in message, message
