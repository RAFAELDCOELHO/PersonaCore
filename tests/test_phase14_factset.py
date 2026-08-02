"""DEMO-05 locked fact set — the D-07 PERMANENT half of the pre-flight discipline.

What this pins, forever: the locked fact set's **token-count census** and its **byte-fallback
round-trip exactness** against the FROZEN production tokenizer, plus the composition, pool
disjointness, and reserved-probe contracts the verdict locked. `artifacts/tokenizer.json` is
git-tracked, so every assertion here runs in the CPU-only, GPU-free CI suite with zero skips.

**What this test does NOT cover, and structurally CANNOT (D-07).** The *guessability* half of
the D-02 pre-flight — the measurement that the base does not already know these values — is
deliberately absent. That measurement is **checkpoint-specific**: it belongs to
`convbase_best.pt`'s actual learned priors at git sha `04e724c`, step 4000, and has no meaning
as a standing invariant. A future checkpoint inheriting a green run of this file has inherited
**nothing** about guessability. Re-validating it against a different checkpoint requires a
**fresh gated measurement** — `scripts/phase14_factset_gate.py --force` plus a new human D-06
verdict — and **not a test re-run**. Without this note a future reader would assume the
permanent test covers the full pre-flight discipline when it structurally cannot. The
constraint that forced the split: the guessability check needs the 278 MB `convbase_best.pt`
on MPS, which cannot enter a CPU-only, GPU-free suite.

Scripts-load justification: no other test imports from ``scripts/`` (test_demo_callback.py
states the convention), but the locked fact set MUST live in the committed driver module for
git history to be the pre-registration proof — moving it into the package would put the
experiment's locked material somewhere the driver could drift from. ``scripts/phase14_factset.py``
defines no ``main()`` and imports no torch, so an ``importlib`` load runs nothing.
"""

import importlib.util
import pathlib
import sys

import pytest

from personacore.tokenizer import from_json

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)


def _load_factset():
    spec = importlib.util.spec_from_file_location(
        "phase14_factset", _REPO_ROOT / "scripts" / "phase14_factset.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fs = _load_factset()

_BY_ID = {fact.id: fact for _name, pool in fs.all_pools() for fact in pool}

_TAUGHT = fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS
_ALL_LOCKED = _TAUGHT + fs.CALIBRATION_FACTS + fs.REGISTER_ARM_FACTS

# The base priors measured at gate time (14-CONTEXT D-01). Not a guessability measurement —
# a fixed list of strings the locked values must never collide with.
_MEASURED_BASE_PRIORS = frozenset(
    {"cop", "college student", "the country", "red", "rose", "max", "lily", "blue"}
)


@pytest.fixture(scope="module")
def tok():
    # The FROZEN production artifact — the registry that ships is what matters, never a
    # freshly trained tokenizer (Pitfall 6).
    return from_json(_REPO_ROOT / "artifacts" / "tokenizer.json")


def test_token_census_matches_locked_literals(tok):
    """D-02(a)/D-04: the committed census is the expectation; never recompute it in-test.

    A drift here means either the frozen tokenizer changed or a value was edited after the
    gate measured it — both invalidate the report the census was transcribed from.
    """
    assert set(fs.VALUE_TOKEN_CENSUS) == {f.id for f in _ALL_LOCKED}
    for fact_id, expected in fs.VALUE_TOKEN_CENSUS.items():
        assert len(tok.encode(_BY_ID[fact_id].value)) == expected, fact_id


def test_byte_fallback_roundtrip(tok):
    """D-02(a): every locked, calibration, register-arm and rejected value round-trips exact."""
    for fact in _ALL_LOCKED + fs.GATE_REJECTED_CANDIDATES:
        assert tok.decode(tok.encode(fact.value)) == fact.value, fact.id


def test_no_dead_ids_emitted(tok):
    """The MEASURED no-op, pinned as a standing fact rather than left as a claim.

    All 256 byte ids are live and BPE falls back to bytes for anything unmerged, so
    ``encode()`` cannot emit a dead id (14-RESEARCH F1). PITFALLS-12's ``forbid_ids``
    sub-filter of the tokenizer pre-flight is therefore structurally unfireable. This
    assertion costs nothing and turns "cannot happen" into something a future tokenizer
    change would have to break loudly.
    """
    live = set(tok.vocab) | set(tok.special_tokens.values())
    for fact in _ALL_LOCKED + fs.GATE_REJECTED_CANDIDATES:
        assert set(tok.encode(fact.value)) <= live, fact.id


def test_composition_targets():
    """D-05: 5-8 core, 2-3 soft; ROADMAP SC1: 5-10 taught total."""
    assert 5 <= len(fs.LOCKED_FACTS) <= 8
    assert 2 <= len(fs.SOFT_TIER_FACTS) <= 3
    assert 5 <= len(_TAUGHT) <= 10
    assert all(f.tier == "core" for f in fs.LOCKED_FACTS)
    assert all(f.tier == "soft" for f in fs.SOFT_TIER_FACTS)
    # One taught fact per slot — the whole reason the core tier trimmed 16 -> 8.
    assert len({f.slot for f in _TAUGHT}) == len(_TAUGHT)
    assert fs.LOCKED_VALUES == tuple(f.value for f in fs.LOCKED_FACTS)


def test_pools_and_locked_sets_disjoint():
    """D-09.1 / D-21.1: calibration and the register arm measure something ONLY if they share
    no value with the real set — a shared value would let one arm's teaching leak into
    another's score. Rejected candidates must also never re-enter the taught set."""
    real = {f.value for f in fs.LOCKED_FACTS}
    calibration = {f.value for f in fs.CALIBRATION_FACTS}
    register_arm = {f.value for f in fs.REGISTER_ARM_FACTS}
    assert not (real & calibration)
    assert not (real & register_arm)
    assert not (calibration & register_arm)

    rejected_ids = {f.id for f in fs.GATE_REJECTED_CANDIDATES}
    assert not (rejected_ids & {f.id for f in _ALL_LOCKED})


def test_reserved_probes_cover_every_locked_fact():
    """D-08: every taught fact carries reserved held-out phrasings, and a probe never names
    the answer it is probing for (T-14-01) — a probe containing the value is not a probe."""
    assert set(fs.RESERVED_HELDOUT_PROBES) == {f.id for f in _TAUGHT}
    for fact in _TAUGHT:
        assert len(fs.RESERVED_HELDOUT_PROBES[fact.id]) >= 3, fact.id

    taught_values = [f.value for f in _TAUGHT]
    for fact_id, probes in fs.RESERVED_HELDOUT_PROBES.items():
        for probe in probes:
            normalized = fs.normalize_for_match(probe)
            for value in taught_values:
                assert fs.normalize_for_match(value) not in normalized, (fact_id, probe, value)


def test_locked_values_are_first_person_register_safe():
    """D-01: a value the base already carries prior mass on is a validity failure of the WHOLE
    demo — a "recalled" fact that was guessable proves nothing about weight-based memory. The
    D-06 gate already checked this against the measured priors; pinning it here keeps a later
    edit to the locked set from quietly reintroducing one. This is a fixed-string collision
    check, NOT the checkpoint-specific guessability measurement (see the module docstring)."""
    priors = {fs.normalize_for_match(p) for p in _MEASURED_BASE_PRIORS}
    for fact in _TAUGHT:
        assert fs.normalize_for_match(fact.value) not in priors, fact.id
