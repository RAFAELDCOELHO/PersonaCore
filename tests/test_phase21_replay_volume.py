"""UNIT-04 / D-11 / D-24: replay VOLUME is a function of PUBLIC quantities ONLY.

**This is a SIDE-CHANNEL claim, and side-channel claims fail silently.** A test that computes
the volume from public inputs and checks it matches proves nothing — of course it matches, the
same author wrote both sides. Likewise ``assert replay_tokens == 8192`` PASSES ON THE DEFECTIVE
IMPLEMENTATION whenever ``round(1.0 * teaching_tokens)`` happens to land on 8,192 (RESEARCH
Pitfall 8). Asserting a constant does not prove independence from private data; it proves one
value.

The only evidence that can fail is a DIFFERENTIAL, run in both directions:

1. **Insensitivity** — hold every PUBLIC quantity fixed, VARY a PRIVATE one, show the volume
   does NOT move (``test_side_channel_closed``).
2. **Non-vacuity** — VARY a PUBLIC quantity, show the volume DOES move
   (``test_side_channel_closed``'s third assertion and ``test_window_quantized``). Without this
   half a function that returns a constant for every input would pass direction 1 while proving
   nothing: a side-channel guard insensitive to *everything* is vacuous.
3. **Live negative control** — the SAME call ONE KWARG APART on the legacy branch, asserted to
   LEAK (``test_side_channel_negative_control``). This is what makes direction 1 evidence rather
   than a description, and it discharges RESEARCH Open Question 3 in the strongest available
   form: the differential runs against BOTH BRANCHES of the single computing site and reports a
   different verdict for each, so it is pointed at live code in both directions rather than at a
   dead function.

===== THE CLASSIFICATION, ENUMERATED AND JUSTIFIED FROM D-11 / D-24 =====

Naming which quantities are public is half the claim; a differential that varies the wrong thing
is green and blind. Each row below is justified by DERIVATION, not by publication — D-24's whole
point is that "public because we published it" is not enough.

PUBLIC:
  * ``n_facts``          — D-11 names it public. A COUNT of records, not a function of their
                           content; SC2 pre-registers ``grad_accum_steps = n_facts`` publicly at
                           both capacities. Varying the fact VALUES cannot move it.
  * ``REPLAY_WINDOWS_PER_FACT = 4``
                         — D-24. Chosen from the {3, 4, 5}-window table, all small integers
                           authored before any fact existed. The one candidate that WAS read off
                           the corpus (947.625) is refused below, by test.
  * ``block_size = 256`` — D-24. ``ModelConfig.block_size``, a model hyperparameter fixed before
                           the fact set existed.
  * episode COUNT (176)  — the facts x families x instances cross product. Held fixed across both
                           corpora here (asserted), so it cannot be the source of any delta.

PRIVATE:
  * each fact's ``value``   — the invented persona secret. This is literally what the DP privacy
                              unit protects, and it is the quantity varied below.
  * ``teaching_tokens``     — D-11: the sum of the FACTS' OWN token lengths, "varying with the
                              fact values". Private BY DERIVATION even though nothing hides it.
  * per-fact token lengths / ``windows_per_fact`` — same reason.

AMBIGUOUS, reported rather than resolved to the convenient reading:
  * ``replay_ratio`` — published as a committed constant (``REPLAY_ARM_RATIO = 1.0``), so public
    by publication; but it was DERIVED from ``replay_required(4.5737, 14.8559)``, a measurement
    taken on the REAL corpus, so under D-24's own strictest test ("public by publication, private
    by derivation") its classification is not clean. **The v4.0 branch does not need it settled:
    the volume ignores ``replay_ratio`` ENTIRELY**, which is why every call below passes
    ``replay_ratio=1.0`` on BOTH branches. If the v4.0 volume used it even as a cap, this
    ambiguity would have to be resolved before the D-11 claim could be made.

===== MEASURED SHARES (D-24), carried here so the numbers travel with the test =====

4 windows = 1,024 tok/fact = 49.23% of the padded bin at n=8 (-0.77 pts vs today's 50.00%),
and 49.90% at n=64 — both sides scale with ``n_facts``, so nothing re-tunes across capacities.

CPU-only, GPU-free, no network. Everything under ``tmp_path``: ``data/`` is gitignored and
machine-local, so a test reading the real ``data/dialog_train.bin`` would be unrunnable on CI.
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

import phase14_factset as fs  # noqa: E402  (scripts/ is not a package)
import teach_persona as tp  # noqa: E402

N_FACTS = 8  # == len(fs.LOCKED_FACTS); asserted below rather than assumed

# The two corpora differ ONLY in the private ``value`` strings. Ids, slots, tiers, the family
# set and the register are all held IDENTICAL, so the only thing that can move teaching_tokens
# is the secret itself. Values are invented and deliberately far apart in token length.
SHORT_VALUES = ("ka", "vo", "zi", "pu", "ne", "ta", "ry", "mo")
LONG_VALUES = (
    "quillonbrackwater",
    "zephyrindalemoor",
    "thistlewickharbor",
    "marrowgladeholt",
    "vandercrestfell",
    "orrimbaywicket",
    "pellucidgrangemere",
    "sablefrostwynd",
)

# The synthetic replay source must cover BOTH branches' largest ``want``: 8,192 on the v4.0 path
# and the long corpus's own teaching total on the legacy path. Comfortably over both, or the
# v4.0 branch trips _prepend_replay's "replay slice short" SystemExit before the differential
# gets to assert anything.
REPLAY_SOURCE_ELEMENTS = 20_000


def _facts(values):
    """The 8 locked facts with their VALUES swapped — everything else byte-identical."""
    return [fs.Fact(f.id, f.slot, v, f.tier) for f, v in zip(fs.LOCKED_FACTS, values)]


def _corpus(tmp_path, name, values):
    """Build one 8-fact corpus at replay_ratio=0.0; return (stats, id_shards, mask_shards).

    ``replay_ratio=0.0`` so ``build_bins`` does NOT reach ``_prepend_replay`` — the teaching
    total is measured on a replay-free bin, then handed to ``_prepend_replay`` directly. Direct,
    because ``_prepend_replay`` IS the single site that computes the volume and ``build_bins``
    deliberately has no ``n_facts`` pass-through to forward through (there is no caller for one,
    and an additive kwarg with no caller has no non-vacuity pair available to it).
    """
    seed_everything(tp.SEED)
    tok = from_json(tp.TOKENIZER_PATH)
    episodes = tp.render_episodes(_facts(values), fs.TAUGHT_FAMILY_IDS)
    stats = tp.build_bins(
        tok, episodes, tmp_path / f"{name}.bin", tmp_path / f"{name}_mask.bin", replay_ratio=0.0
    )
    id_shards, mask_shards = [], []
    for question, answer in episodes:
        ids, mask = encode_dialogue(tok, [], [(question, answer)])
        id_shards.append(np.asarray(ids, dtype=np.uint16))
        mask_shards.append(np.asarray(mask, dtype=np.uint8))
    return stats, id_shards, mask_shards


@pytest.fixture
def replay_source(tmp_path, monkeypatch):
    """A synthetic PersonaChat-shaped replay bin pair; NEVER the machine-local real one."""
    bin_path = tmp_path / "synthetic_replay.bin"
    mask_path = tmp_path / "synthetic_replay_mask.bin"
    rng = np.random.default_rng(1337)
    rng.integers(0, 8184, size=REPLAY_SOURCE_ELEMENTS, dtype=np.uint16).tofile(bin_path)
    rng.integers(0, 2, size=REPLAY_SOURCE_ELEMENTS, dtype=np.uint8).tofile(mask_path)
    monkeypatch.setattr(tp, "DIALOG_TRAIN_BIN", bin_path)
    monkeypatch.setattr(tp, "DIALOG_TRAIN_MASK", mask_path)
    return bin_path, mask_path


def _both_corpora(tmp_path):
    short = _corpus(tmp_path, "short", SHORT_VALUES)
    long_ = _corpus(tmp_path, "long", LONG_VALUES)
    return short, long_


def _assert_fixture_actually_varies(short_stats, long_stats):
    """Guard the differential against vacuity BEFORE it asserts anything (Pitfall 8)."""
    assert len(fs.LOCKED_FACTS) == N_FACTS, (
        f"the corpora carry {len(fs.LOCKED_FACTS)} facts, not {N_FACTS} — n_facts is the PUBLIC "
        "quantity held fixed across both arms, so a drift here invalidates the differential"
    )
    assert short_stats["episodes"] == long_stats["episodes"], (
        "the two corpora differ in EPISODE COUNT, a public quantity — the differential is meant "
        "to vary the private fact VALUES only, so a public delta would confound it"
    )
    assert short_stats["teaching_tokens"] != long_stats["teaching_tokens"], (
        "the fixture does not vary private token length — this test would be vacuous. "
        f"both corpora measured {short_stats['teaching_tokens']:,} teaching tokens, so an "
        "invariance observed across them would prove nothing about independence from private "
        "data. Widen the gap between SHORT_VALUES and LONG_VALUES."
    )


def test_side_channel_closed(tmp_path, replay_source):
    """DIRECTION 1 + 2: invariant to the private values, NOT invariant to the public n_facts."""
    (short_stats, short_ids, short_mask), (long_stats, long_ids, long_mask) = _both_corpora(
        tmp_path
    )
    _assert_fixture_actually_varies(short_stats, long_stats)

    short_replay = tp._prepend_replay(
        short_ids, short_mask, 1.0, short_stats["teaching_tokens"], n_facts=N_FACTS
    )
    long_replay = tp._prepend_replay(
        long_ids, long_mask, 1.0, long_stats["teaching_tokens"], n_facts=N_FACTS
    )

    # 1 — INSENSITIVITY to the private quantity. The two calls were handed DIFFERENT
    # teaching_tokens (asserted above), so the invariance is observed over a genuinely varying
    # input rather than over a constant the fixture happened to pass in twice.
    assert short_replay == long_replay == N_FACTS * 4 * 256 == 8192, (
        f"replay volume moved with the private fact values: {short_replay:,} (short corpus, "
        f"{short_stats['teaching_tokens']:,} teaching tokens) vs {long_replay:,} (long corpus, "
        f"{long_stats['teaching_tokens']:,}). D-11 requires the volume to depend on PUBLIC "
        "quantities only — n_facts, REPLAY_WINDOWS_PER_FACT and block_size — so any delta here "
        "means a private token length reached the observable volume of public data in the lot."
    )

    # 2 — NON-VACUITY. Vary the PUBLIC n_facts with everything else fixed and the volume MUST
    # move. Without this, a function returning a constant for every input passes assertion 1
    # while proving nothing: insensitive to everything is not the same as insensitive to
    # private data.
    doubled = tp._prepend_replay(
        short_ids, short_mask, 1.0, short_stats["teaching_tokens"], n_facts=2 * N_FACTS
    )
    assert doubled == 2 * short_replay, (
        f"the volume did NOT respond to n_facts ({short_replay:,} at n={N_FACTS}, {doubled:,} "
        f"at n={2 * N_FACTS}) — it is constant, so its 'independence from private data' is "
        "vacuous rather than a property of the mechanism"
    )


def test_side_channel_negative_control(tmp_path, replay_source):
    """The SAME call ONE KWARG APART on the legacy branch MUST leak — or this file is blind."""
    (short_stats, short_ids, short_mask), (long_stats, long_ids, long_mask) = _both_corpora(
        tmp_path
    )
    _assert_fixture_actually_varies(short_stats, long_stats)

    short_replay = tp._prepend_replay(
        short_ids, short_mask, 1.0, short_stats["teaching_tokens"], n_facts=None
    )
    long_replay = tp._prepend_replay(
        long_ids, long_mask, 1.0, long_stats["teaching_tokens"], n_facts=None
    )

    assert short_replay != long_replay, (
        "the LEGACY branch did not leak, so test_side_channel_closed proves nothing — a "
        "differential over an implementation that returns a constant for every input passes "
        "while saying nothing about the mechanism. n_facts=None must still size replay as "
        "round(replay_ratio * teaching_tokens), which IS the D-11 side channel, retained "
        "deliberately so this control stays live."
    )
    # Same call site, one kwarg apart -> a different verdict for each branch. That is what makes
    # the verdict a property of the BRANCH rather than of two different fixtures.
    assert short_replay == short_stats["teaching_tokens"]
    assert long_replay == long_stats["teaching_tokens"]


@pytest.mark.parametrize("n", [8, 64])
def test_window_quantized(n):
    """D-24's 'integral windows?' column, made into a test."""
    assert tp.replay_window_budget(n) == n * 4 * 256
    assert tp.replay_window_budget(n) % 256 == 0, (
        f"replay_window_budget({n}) = {tp.replay_window_budget(n):,} is not a whole number of "
        "block_size windows. get_batch_memmap_masked draws whole windows only, so a "
        "non-integral budget forces a truncation step inside the very path D-10 chose BECAUSE "
        "it was already proven."
    )


def test_replay_constant_is_not_derived_from_the_corpus():
    """The rejected raw constant is refused BY VALUE, with its derivation in the message."""
    per_fact = tp.REPLAY_WINDOWS_PER_FACT * tp.BLOCK_SIZE
    assert abs(per_fact - 947.625) > 1.0, (
        f"the per-fact replay constant is {per_fact}, within 1.0 of the REJECTED raw value "
        "947.625. That number IS 7581 / 8 — the measured teaching total divided by the fact "
        "count — so it was read off the PRIVATE token lengths. A constant that is 'public' "
        "because it is published, but whose VALUE was derived from private data, is the same "
        "property-not-name defect one level up, at design time (D-24). It is also not an "
        "integral number of windows (3.7017)."
    )
    assert per_fact == 1024
