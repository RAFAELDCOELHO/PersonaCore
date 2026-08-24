"""UNIT-03: validating the INSTRUMENT, because a measurement taken with an untested instrument
is not evidence.

The failure mode this module exists to catch is an instrument that reports a plausible number for
the wrong reason, and whose "validation" only confirms that it is self-consistent. An instrument
is validated by feeding it inputs whose TRUE answer is known INDEPENDENTLY of it and showing it
recovers them, so every oracle below is one of:

* **exact and hand-counted** — one fact; a fact that provably cannot be drawn; the conservation law
* **exactly re-derived** — the draw's start offsets replayed in the TEST from the same seed, which
  is deliberately the route :func:`phase21_unit_record.count_unaligned` REFUSES to use (it wraps
  the real call instead). The test may re-derive; the instrument may not. Agreement between an
  observation of the real draw and an independent re-derivation of it is evidence. Agreement
  between two copies of a re-derivation is not.
* **discriminating** — a corpus where a WRONG attribution rule gives a DIFFERENT answer, with the
  wrong answer computed and shown not to be the one the instrument produced

Validating only against the real corpus, where the true answer is whatever the instrument says,
would not be validation at all.

CPU-only, GPU/MPS-free, no network. Everything under ``tmp_path``; nothing writes into ``data/``
or ``results/``. Do NOT weaken any assertion to make these pass.
"""

import math
import pathlib
import subprocess
import sys
from typing import NamedTuple

import numpy as np
import pytest

from personacore.seeding import seed_everything
from personacore.training.data import fact_window_impurities

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT / "tests"))

import phase21_unit_record as unit  # noqa: E402  (scripts/ is not a package)
import teach_persona as tp  # noqa: E402

from test_phase21_aligned_bins import (  # noqa: E402  (tests/ is not one either)
    _aligned_pairs,
    _build,
)

BLOCK = tp.BLOCK_SIZE  # 256 — resolved from the module, never re-spelled as a literal
SEED = tp.SEED  # 1337
BATCH_SIZE = tp.BATCH_SIZE  # 8
MAX_STEPS = tp.MAX_STEPS  # 200

# D-10's facts-only bin is 7,581 teaching tokens across 8 facts. The per-fact SPLIT below is a
# HAND-WRITTEN stand-in, not the real corpus's — the conservation law and the seeded reproduction
# are properties of the DRAW and are indifferent to how the tokens divide. The total is the real
# one so the real (200, 8) budget runs against a support of the real size.
D10_LIKE_LENGTHS = (948, 948, 948, 948, 948, 948, 948, 945)

SYNTHETIC = "synthetic (validation fixture, not a published composition)"


class Flat(NamedTuple):
    """A synthetic FLAT corpus — the shape the OLD random-window path draws over."""

    tokens: pathlib.Path
    mask: pathlib.Path
    fact: pathlib.Path
    fact_ids: np.ndarray


def _flat(tmp_path, name, fact_lengths):
    """Three 1:1 bins whose fact map is a HAND-CHOSEN run-length layout.

    Token VALUES are irrelevant to multiplicity — the draw is over START OFFSETS and the
    attribution reads the FACT map — so they are a deterministic ramp rather than a real
    encoding. That is what lets every expected count below be computed by hand.
    """
    total = int(sum(fact_lengths))
    tokens = (np.arange(total) % 1000).astype(np.uint16)
    mask = np.ones(total, dtype=np.uint8)
    fact_ids = np.concatenate(
        [np.full(length, index, dtype=np.uint16) for index, length in enumerate(fact_lengths)]
    )

    bin_path = tmp_path / f"{name}.bin"
    mask_path = tmp_path / f"{name}_mask.bin"
    fact_path = tp.fact_bin_path(bin_path)  # DERIVED, never string-built
    tokens.tofile(bin_path)
    mask.tofile(mask_path)
    fact_ids.tofile(fact_path)
    return Flat(bin_path, mask_path, fact_path, fact_ids)


def _count(flat, *, steps, batch_size, seed=SEED, block_size=BLOCK):
    """One instrumented unaligned count over ``flat``, at the synthetic label."""
    return unit.count_unaligned(
        flat.tokens,
        flat.mask,
        flat.fact,
        steps=steps,
        batch_size=batch_size,
        seed=seed,
        block_size=block_size,
        bin_composition=SYNTHETIC,
    )


def _replay_starts(*, seed, bin_tokens, block_size, steps, batch_size):
    """The draw's start offsets, RE-DERIVED in the test from the same seed.

    This is the ORACLE and it is deliberately the route the instrument refuses: re-deriving the
    indices measures a re-implementation of the draw, so it is worthless AS an instrument and
    valuable as an INDEPENDENT check on one. The bound is
    ``get_batch_memmap_masked``'s verbatim (``len(data) - block_size - 1``,
    ``src/personacore/training/data.py``); if the loader's bound ever changes, this oracle
    disagrees with the instrument and the disagreement is the finding.
    """
    seed_everything(seed)
    return [
        np.random.randint(0, bin_tokens - block_size - 1, size=batch_size) for _ in range(steps)
    ]


def _attribute(fact_ids, starts_per_step, offset):
    """Credit each drawn window to ``fact_ids[start + offset]`` — ONE token, ONE fact.

    ``offset = 0`` is :data:`phase21_unit_record.ATTRIBUTION_RULE`. Any other offset is a WRONG
    implementation, kept runnable so "a wrong implementation would give a different answer" is a
    computed fact rather than a claim.
    """
    counts = {int(f): 0 for f in np.unique(fact_ids)}
    for starts in starts_per_step:
        for start in starts:
            counts[int(fact_ids[int(start) + offset])] += 1
    return counts


# ===================================================================================
# ===== THE CONSERVATION LAW. Exact, deterministic, no statistics, nothing to =======
# ===== tune. Double-counting, a dropped draw, an off-by-one in the step loop =======
# ===== and a silently skipped batch all fail it. ===================================
# ===================================================================================


@pytest.mark.parametrize(
    ("steps", "batch_size"),
    [
        (10, 4),
        (37, 3),
        (MAX_STEPS, BATCH_SIZE),  # THE REAL BUDGET: 200 x 8 = 1,600, D-26's own denominator
    ],
)
def test_conservation(tmp_path, steps, batch_size):
    """``sum(counts.values()) == steps * batch_size``, with the RHS derived from the RULE.

    The RHS is an equality ONLY under ``first-token-owns-draw``: crediting every overlapped fact
    makes it ``> steps * batch_size``, data-dependent, with nothing to check exactly. The rule is
    named in the failure message so a future reader debugging a mismatch does not have to guess
    which convention was in force.
    """
    flat = _flat(tmp_path, "conserve", D10_LIKE_LENGTHS)
    row = _count(flat, steps=steps, batch_size=batch_size)

    expected = steps * batch_size  # one draw, one fact — that IS the rule
    assert sum(row["counts"].values()) == expected, (
        f"the counts sum to {sum(row['counts'].values())} against a budget of "
        f"{steps} x {batch_size} = {expected} under ATTRIBUTION_RULE="
        f"{unit.ATTRIBUTION_RULE!r}. Over-count means a draw was credited to more than one fact "
        "(the REJECTED rule); under-count means a draw was dropped."
    )
    assert row["total_draws"] == expected
    assert row["attribution_rule"] == unit.ATTRIBUTION_RULE

    # The mean is PINNED by the conservation law, so it carries no information about the corpus —
    # asserted here so nobody later reads a mean as a measurement.
    assert row["mean"] == expected / row["n_facts"]


def test_conservation_holds_at_the_real_budget_denominator(tmp_path):
    """1,600 is D-26's denominator, and it is exercised rather than merely referenced."""
    assert MAX_STEPS * BATCH_SIZE == 1600
    flat = _flat(tmp_path, "budget", D10_LIKE_LENGTHS)
    row = _count(flat, steps=MAX_STEPS, batch_size=BATCH_SIZE)

    assert sum(row["counts"].values()) == 1600
    assert row["bin_tokens"] == sum(D10_LIKE_LENGTHS) == 7581
    # The support `np.random.randint` actually offers — the denominator of the analytic
    # expectation, and NOT `bin_tokens`. Recording the wrong one is how 54.03 gets confused
    # with 262.94 (`scripts/mitigation_unit.py`).
    assert row["draw_start_offsets"] == 7581 - BLOCK - 1 == 7324


# ===================================================================================
# ===== The seed provably REACHES the draw. Without the 1338 half, an instrument ====
# ===== that ignores the seed entirely passes. ======================================
# ===================================================================================


def test_seed_reproducible(tmp_path):
    """Same seed -> identical counts. DIFFERENT seed -> different counts."""
    flat = _flat(tmp_path, "seeded", D10_LIKE_LENGTHS)

    first = _count(flat, steps=40, batch_size=BATCH_SIZE, seed=SEED)
    second = _count(flat, steps=40, batch_size=BATCH_SIZE, seed=SEED)
    other = _count(flat, steps=40, batch_size=BATCH_SIZE, seed=SEED + 1)

    assert first["counts"] == second["counts"]
    # Compare `counts`, NOT the whole row: the row carries `seed` itself, so a row-level
    # inequality would hold even for an instrument that ignored the seed completely.
    assert other["counts"] != first["counts"], (
        f"a different seed produced identical counts — the seed is not reaching the draw "
        f"(seed {SEED} and seed {SEED + 1} both gave {first['counts']})"
    )
    assert other["seed"] == SEED + 1
    # ...and the budget is conserved on BOTH seeds, so "different" is a different DISTRIBUTION
    # and not a dropped draw.
    assert sum(first["counts"].values()) == sum(other["counts"].values()) == 40 * BATCH_SIZE


# ===================================================================================
# ===== The REAL 8-fact aligned corpus, built once through the real packer. =========
# ===================================================================================


class Aligned(NamedTuple):
    tokens: pathlib.Path
    mask: pathlib.Path
    fact: pathlib.Path
    stats: dict


@pytest.fixture(scope="module")
def _aligned_built(tmp_path_factory):
    """The REAL 8-fact aligned corpus, built ONCE through the real packer (D-01's geometry)."""
    base = tmp_path_factory.mktemp("multiplicity_src")
    stats, bin_path, mask_path = _build(base, "mult", episodes=[], align_facts=_aligned_pairs())
    return Aligned(bin_path, mask_path, tp.fact_bin_path(bin_path), stats)


@pytest.fixture
def aligned_bins(_aligned_built, tmp_path):
    """A private COPY per test — the non-vacuity test mutates the fact bin on disk."""
    copies = []
    for source in (_aligned_built.tokens, _aligned_built.mask, _aligned_built.fact):
        target = tmp_path / source.name
        target.write_bytes(source.read_bytes())
        copies.append(target)
    tokens, mask, fact = copies
    assert fact == tp.fact_bin_path(tokens), "the fact bin must resolve through fact_bin_path()"
    return Aligned(tokens, mask, fact, _aligned_built.stats)


def _count_aligned(bins, *, steps, strict=True):
    return unit.count_aligned(
        bins.tokens,
        bins.mask,
        bins.fact,
        steps=steps,
        n_facts=bins.stats["n_facts"],
        block_size=BLOCK,
        bin_composition=unit.BIN_COMPOSITION_LABELS[2],
        strict=strict,
    )


# ===================================================================================
# ===== Every row carries its denominator (D-26). One line, and it stops a =========
# ===== silently thinned record reaching the artifact in plan 21-11. ================
# ===================================================================================

TEN_SCHEMA_KEYS = (
    "attribution_rule",
    "seed",
    "steps",
    "batch_size",
    "bin_tokens",
    "n_facts",
    "min",
    "max",
    "mean",
    "spread",
)


def test_row_carries_its_denominator(tmp_path, aligned_bins):
    """BOTH rows carry the ten keys D-26 names, plus the label and the totals."""
    flat = _flat(tmp_path, "schema", D10_LIKE_LENGTHS)
    unaligned = _count(flat, steps=12, batch_size=BATCH_SIZE)
    aligned = _count_aligned(aligned_bins, steps=aligned_bins.stats["n_facts"])

    for row in (unaligned, aligned):
        missing = [key for key in TEN_SCHEMA_KEYS if key not in row]
        assert missing == [], f"the row is missing {missing} — a thinned record (D-26)"
        assert set(unit.ROW_SCHEMA) <= set(row), sorted(set(unit.ROW_SCHEMA) - set(row))
        assert row["bin_composition"]  # never silently absent: D-26 makes the label part of the row

    assert len(TEN_SCHEMA_KEYS) == 10
    # `batch_size` is None on the aligned row and that is the HONEST value: the aligned batch is
    # RAGGED by construction (4 or 5 windows per record, D-01), so a scalar would be a lie.
    assert aligned["batch_size"] is None
    assert unaligned["batch_size"] == BATCH_SIZE


# ===================================================================================
# ===== The aligned path at the strict=True DEFAULT. The default is what ===========
# ===== produces the record, and a correct bin must never need strict=False. =======
# ===================================================================================


def test_aligned_conservation(aligned_bins):
    """One record per micro-step, at the ``strict=True`` DEFAULT on a correct bin."""
    n_facts = aligned_bins.stats["n_facts"]
    steps = 2 * n_facts  # two full lots, so the wrap is observed and not assumed
    row = _count_aligned(aligned_bins, steps=steps)

    assert sum(row["counts"].values()) == steps
    assert row["total_draws"] == steps
    # The observed sequence is `range(n_facts)` repeating with NO gap — the same
    # `grad_accum_steps = n_facts` property `tests/test_phase21_aligned_loader.py` observes at the
    # loader tier, read here from the counter's own returns.
    assert row["per_step_fact_index"] == list(range(n_facts)) * 2
    assert row["counts"] == dict.fromkeys(range(n_facts), 2)
    assert row["min"] == row["max"] == 2
    assert row["spread"] == 0
    # A correct bin NEVER needs strict=False: nothing raised, and every step saw ONE fact.
    assert row["per_step_raised"] == [None] * steps
    assert row["per_step_distinct_facts"] == [1] * steps
    assert row["bin_composition"] == "fact-aligned (D-01, D-05)"
    assert row["n_windows"] == aligned_bins.stats["n_windows"] == 33


# ===================================================================================
# ===== INDEPENDENT ORACLES. Each recovers an answer known WITHOUT the ==============
# ===== instrument; the last one shows a wrong implementation answering ============
# ===== differently on the same corpus. =============================================
# ===================================================================================


def test_oracle_exact_replay_of_the_draw(tmp_path):
    """The counts equal an INDEPENDENT re-derivation of the same seeded draw. EXACT, no interval.

    The instrument observes the real ``np.random.randint`` call in place; this oracle replays the
    stream itself. They agree only if the instrument saw every draw, attributed each to the first
    token's fact, and used the loader's own start bound.
    """
    flat = _flat(tmp_path, "replay", D10_LIKE_LENGTHS)
    steps, batch_size = 25, BATCH_SIZE

    row = _count(flat, steps=steps, batch_size=batch_size)
    starts = _replay_starts(
        seed=SEED,
        bin_tokens=len(flat.fact_ids),
        block_size=BLOCK,
        steps=steps,
        batch_size=batch_size,
    )
    assert row["counts"] == _attribute(flat.fact_ids, starts, 0)


def test_oracle_one_fact_takes_every_draw(tmp_path):
    """The degenerate case, hand-counted: one fact owns the corpus, so it owns every draw."""
    flat = _flat(tmp_path, "single", (2048,))
    row = _count(flat, steps=30, batch_size=BATCH_SIZE)

    assert row["counts"] == {0: 30 * BATCH_SIZE}
    assert row["n_facts"] == 1
    assert row["min"] == row["max"] == row["mean"] == 30 * BATCH_SIZE
    assert row["spread"] == 0


def test_oracle_an_undrawable_fact_counts_zero(tmp_path):
    """A fact living ENTIRELY in the unreachable tail must count 0 — and set ``min`` to 0.

    ``np.random.randint(0, len(data) - block_size - 1)`` can never return a start in the last
    ``block_size + 1`` elements, so a fact packed there is drawn zero times. Hand-counted, and it
    is the case that separates a counter which summarises EVERY fact from one which summarises
    only the facts it happened to observe: the latter reports a ``min`` above zero here, which is
    the flattering direction and would understate the spread in the published row.
    """
    tail = BLOCK + 1
    flat = _flat(tmp_path, "undrawable", (4096, tail))
    row = _count(flat, steps=50, batch_size=BATCH_SIZE)

    assert row["counts"] == {0: 50 * BATCH_SIZE, 1: 0}
    assert row["n_facts"] == 2, "fact 1 vanished from the row instead of being counted zero"
    assert row["min"] == 0
    assert row["max"] == row["spread"] == 50 * BATCH_SIZE


def test_oracle_a_wrong_attribution_rule_gives_a_different_answer(tmp_path):
    """The discriminating case: on THIS corpus the rules disagree, and the wrong answers are shown.

    Fact 0 owns exactly the first ``block_size`` tokens. A window starting at offset ``s`` has its
    FIRST token in fact 0 for ``s < block_size`` but its LAST token in fact 0 only for ``s == 0``,
    so first-token and last-token attribution differ by construction — no statistics, no interval.
    Both wrong answers are COMPUTED here rather than described, and the instrument is asserted
    equal to the first-token one and unequal to the others.
    """
    flat = _flat(tmp_path, "discriminate", (BLOCK, 4096))
    steps, batch_size = 60, BATCH_SIZE

    row = _count(flat, steps=steps, batch_size=batch_size)
    starts = _replay_starts(
        seed=SEED,
        bin_tokens=len(flat.fact_ids),
        block_size=BLOCK,
        steps=steps,
        batch_size=batch_size,
    )
    first_token = _attribute(flat.fact_ids, starts, 0)
    last_token = _attribute(flat.fact_ids, starts, BLOCK - 1)
    mid_token = _attribute(flat.fact_ids, starts, BLOCK // 2)

    # The corpus DISCRIMINATES — asserted, so a fixture that stopped separating the rules fails
    # loudly instead of making the assertions below vacuously true.
    assert first_token != last_token, (flat.fact_ids[:2].tolist(), first_token, last_token)
    assert first_token != mid_token

    assert row["counts"] == first_token
    assert row["counts"] != last_token
    assert row["counts"] != mid_token

    # And the REJECTED rule — credit every overlapped fact — cannot carry the conservation law:
    # its total EXCEEDS the draw budget on this very corpus. Computed, not asserted in prose.
    overlapped = {int(f): 0 for f in np.unique(flat.fact_ids)}
    for step_starts in starts:
        for start in step_starts:
            for fact in np.unique(flat.fact_ids[int(start) : int(start) + BLOCK]):
                overlapped[int(fact)] += 1
    assert sum(overlapped.values()) > steps * batch_size
    assert sum(row["counts"].values()) == steps * batch_size


# ===================================================================================
# ===== The instrument's own provenance: the wrapper must see EVERY draw. ===========
# ===================================================================================


def test_the_wrapper_call_count_is_asserted_not_assumed(tmp_path, monkeypatch):
    """If the wrapper misses a draw the count is silently short — so it refuses to report.

    The conservation law alone cannot catch this: it balances against the draws the wrapper DID
    see. Only the call-count assertion separates "1,600 draws were counted" from "every draw was
    counted". Stand in a loader that never draws and the instrument must refuse to return a row.

    The patch targets ``phase21_unit_record``'s OWN binding, not
    ``personacore.training.data``'s: the instrument imported the name at module scope, so
    patching the source module would leave the real function bound and this test would pass
    while proving nothing.
    """
    flat = _flat(tmp_path, "provenance", D10_LIKE_LENGTHS)
    monkeypatch.setattr(unit, "get_batch_memmap_masked", lambda *args, **kwargs: None)

    with pytest.raises(ValueError) as excinfo:
        _count(flat, steps=2, batch_size=BATCH_SIZE)
    message = str(excinfo.value)
    assert "did not observe every draw" in message, message
    assert "0 call(s)" in message, message

    # ...and np.random.randint was RESTORED even though the count aborted: the wrapper is
    # installed under `try/finally`, so a raising instrument cannot leave numpy monkeypatched
    # for every later test in the session.
    assert np.random.randint.__module__ != __name__
    assert isinstance(np.random.randint(0, 3, size=2), np.ndarray)


# ===================================================================================
# ===== instrument_can_report_not_one — the NON-VACUITY of the aligned row. ========
# ===== D-26 records an OBSERVED count so "1 by construction" is verified. But =====
# ===== an instrument that PRINTS 1 without counting produces that row too =========
# ===== (Pitfall 7: the warning sign is the aligned row being a literal in the =====
# ===== driver rather than a value returned by the counter). =======================
# ===================================================================================


def _roll_fact_bin(fact_path):
    """A1's roll-by-1 at the REAL ``block_size`` — every element right by one, tail re-appended.

    Preserves length, the id multiset and the block remainder, so every offset-shaped check agrees
    with the correct bin. Only a positional INPUT-space read separates them.
    """
    ids = np.fromfile(fact_path, dtype=np.uint16)
    np.concatenate([np.roll(ids[:-1], 1), ids[-1:]]).tofile(fact_path)


@pytest.mark.parametrize("rolled", [True, False], ids=["mis-built", "correct-control"])
def test_instrument_can_report_not_one(aligned_bins, rolled):
    """Fed a bin that PROVABLY carries two facts in one window, the counter must report > 1.

    An instrument which can only ever see valid input cannot demonstrate that it is counting —
    that is the whole reason ``strict`` exists. ``get_batch_fact_aligned`` RAISES on an impure
    drawn window, so at the ``strict=True`` default the counter aborts before it can report
    anything and this test is unwritable; ``strict=False`` wraps BOTH the span and the loader in
    one ``try/except ValueError`` and records ``per_step_raised`` instead of propagating.

    The two arms differ ONLY in the bin — the same call, the same steps, the same ``strict=False``.
    """
    n_facts = aligned_bins.stats["n_facts"]
    if rolled:
        _roll_fact_bin(aligned_bins.fact)

    fact_ids = np.fromfile(aligned_bins.fact, dtype=np.uint16)

    # FIRST: the fixture really is (or is not) corrupted, in INPUT space at its `space="input"`
    # DEFAULT — SC2's claim verbatim. A fixture that failed to corrupt anything would otherwise
    # make every assertion below pass vacuously. NOT target space: a roll leaves target space
    # EMPTY (measured in plan 21-04), so a target-space assertion would pass on the CORRUPTED bin
    # for the wrong reason.
    impurities = fact_window_impurities(fact_ids, BLOCK)
    assert (impurities != []) is rolled, (rolled, impurities)

    # A FULL LOT. A run of `steps < n_facts` never reaches the step whose SPAN raises, and would
    # pass over a counter that aborts there — so the lot length is asserted in the body, not left
    # to the parametrize table.
    steps = n_facts
    assert steps >= n_facts
    row = _count_aligned(aligned_bins, steps=steps, strict=False)
    seen = [d for d in row["per_step_distinct_facts"] if d is not None]

    if rolled:
        assert max(seen) > 1, (
            "the instrument reported 1-per-step on a bin that provably carries two — it is not "
            f"counting (per_step_distinct_facts={row['per_step_distinct_facts']})"
        )
        # The roll's NON-CONTIGUITY was OBSERVED and not swallowed. `fact_window_span` raises for
        # the one fact the roll left split across the bin's two ends; that is STRONGER evidence of
        # a mis-built bin than `distinct == 2`, so it is its own outcome class.
        assert "span" in row["per_step_raised"], row["per_step_raised"]
        assert "loader" in row["per_step_raised"], row["per_step_raised"]
    else:
        # THE NEGATIVE CONTROL, through the SAME call. Without it, a `strict=False` that swallowed
        # every step would satisfy the assertions above on the rolled bin and nobody would notice.
        assert seen == [1] * steps, row["per_step_distinct_facts"]
        assert row["per_step_raised"] == [None] * steps, row["per_step_raised"]
        assert sum(row["counts"].values()) == steps


def test_the_correct_bin_returns_normally_at_the_strict_default(aligned_bins):
    """``strict=False`` is a TEST AFFORDANCE, not a way to hide a real defect from the record.

    The DEFAULT is what plan 21-11 calls, so the default must be the path that produces the row.
    """
    n_facts = aligned_bins.stats["n_facts"]
    row = _count_aligned(aligned_bins, steps=n_facts)  # strict=True, no raise

    assert row["per_step_raised"] == [None] * n_facts
    assert row["per_step_distinct_facts"] == [1] * n_facts
    assert sum(row["counts"].values()) == n_facts

    # ...and on the MIS-BUILT bin the default ABORTS rather than reporting a clean-looking row.
    _roll_fact_bin(aligned_bins.fact)
    with pytest.raises(ValueError):
        _count_aligned(aligned_bins, steps=n_facts)


# ===================================================================================
# ===== The analytic numbers as a CROSS-CHECK on the instrument, NEVER as the ======
# ===== record. The record is the measured row. =====================================
# ===================================================================================

EQUAL_FACT_LEN = 2048  # two facts of EXACTLY equal length — the closed-form fixture
ANALYTIC_DRAWS = MAX_STEPS * BATCH_SIZE  # 1,600
ANALYTIC_SUPPORT = 2 * EQUAL_FACT_LEN - BLOCK - 1  # 3,839 reachable start offsets
ANALYTIC_Z = 4.0  # the multiplier, written out rather than hidden in a loose tolerance


def test_analytic_cross_check_only(tmp_path):
    """Two facts of EXACTLY equal length: the counts must sit in a stated binomial interval.

    This is a cross-check ON THE INSTRUMENT and it is NEVER the record — the record is the
    measured row, which is the whole of what UNIT-03 asks for.

    The interval is centred on the CLOSED-FORM expectation and not on ``n/2``, and the difference
    is the point. ``np.random.randint(0, len(data) - block_size - 1)`` cannot start a window in the
    last ``block_size + 1`` elements, so with two equal facts the SECOND one loses that tail from
    its reachable support: ``p(fact 0) = 2048 / 3839 = 0.5335``, not ``0.5``. At 1,600 draws the
    naive ``n/2 = 800`` sits ~2.7 sigma below the true expectation — it would still fall inside a
    4-sigma band, so a test written against ``n/2`` would pass for the WRONG REASON. That is the
    same denominator confusion ``scripts/mitigation_unit.py`` had to write a formula into a frozen
    file to settle (``1600 * 256 / 7581 = 54.03`` is not the number either).
    """
    flat = _flat(tmp_path, "equal", (EQUAL_FACT_LEN, EQUAL_FACT_LEN))
    assert len(flat.fact_ids) - BLOCK - 1 == ANALYTIC_SUPPORT == 3839

    p_first = EQUAL_FACT_LEN / ANALYTIC_SUPPORT
    expected_first = ANALYTIC_DRAWS * p_first
    sigma = math.sqrt(ANALYTIC_DRAWS * p_first * (1 - p_first))
    band = ANALYTIC_Z * sigma

    # Hand-checked literals, so a drifted fixture fails here instead of widening the band.
    assert expected_first == pytest.approx(853.56, abs=0.05)
    assert sigma == pytest.approx(19.96, abs=0.05)
    assert band == pytest.approx(79.82, abs=0.2)

    row = _count(flat, steps=MAX_STEPS, batch_size=BATCH_SIZE)
    assert row["counts"][0] == pytest.approx(expected_first, abs=band)
    assert row["counts"][1] == pytest.approx(ANALYTIC_DRAWS - expected_first, abs=band)
    assert sum(row["counts"].values()) == ANALYTIC_DRAWS  # conservation still exact

    # The naive centre is FAR ENOUGH from the true one to matter, asserted so the finding cannot
    # go stale silently: it is inside the 4-sigma band, which is exactly why centring there would
    # be an unfalsifiable-by-accident test rather than a wrong one.
    naive = ANALYTIC_DRAWS / 2
    assert abs(expected_first - naive) > 2 * sigma
    assert abs(expected_first - naive) < band


# ===================================================================================
# ===== The artifact ordering is IRREVOCABLE (adds[-1]). Catch an accidental =======
# ===== early write while it is still cheap. ========================================
# ===================================================================================


def test_the_committed_artifacts_are_exactly_the_declared_paths():
    """The DECLARED constants and the COMMITTED paths are the same set — checked, not assumed.

    **This inverts `test_the_artifact_is_not_written_yet`, which plan 21-11 made false by design.**
    That test asserted `git ls-files 'results/phase21_*' == []` while 21-10 shipped the instrument
    and no artifact; its own docstring named 21-11 as the plan that writes and commits them. The
    inversion is the RECORDED TRANSITION, not an erasure — the same treatment
    `test_phase21_has_no_artifact_yet_so_the_arming_is_honest` received in
    `tests/test_phase20_prereg.py`, and it is the SECOND guard of that shape. The plan's task-3
    text names only the first, which is why this one was found by running the full suite rather
    than by reading the plan.

    What it guards now is the defect this repository keeps producing: a plan naming an artifact
    path the code refuses. `ARTIFACTS` is the single declaration, the driver writes through it,
    and this asserts the COMMITTED set is exactly that declaration — so an artifact landing at a
    path nobody declared, or a declared path that never got committed, is red either way.
    """
    tracked = sorted(
        subprocess.run(
            ["git", "ls-files", "results/phase21_*"],
            cwd=_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
    )
    declared = sorted(str(path.relative_to(_ROOT)) for path in unit.ARTIFACTS.values())
    assert tracked == declared, (
        f"committed {tracked} but ARTIFACTS declares {declared} — an artifact at an undeclared "
        "path, or a declared path that was never committed. `adds[-1]` makes the ancestry "
        "ordering of the committed path permanent, so a stray path cannot simply be moved."
    )
    # The paths are declared as constants HERE precisely so 21-11 resolves them from the module
    # rather than from a string literal in a plan step.
    assert set(unit.ARTIFACTS) == {"privacy_unit", "multiplicity"}
    for path in unit.ARTIFACTS.values():
        assert path.name.startswith("phase21_")
        assert path.parent.name == "results"
        assert path.exists(), f"{path} is tracked but absent from the working tree"
