"""UNIT-06 — the ``render_family(..., forms=)`` seam that D-16's filler grammar renders through.

Two halves, and NEITHER is sufficient alone. The rule is 21-RESEARCH ``§V.4``: *a byte-identity
assertion with no paired non-identity assertion is vacuous*, because "byte-identical when ``None``"
is satisfied perfectly by a kwarg that is never read at all.

1. ``test_render_family_byte_identity`` — the DEFAULT path still reproduces the PRE-EDIT digests in
   ``tests/fixtures/golden_render_family_v2.json`` (plan 21-02), in BOTH registers across ALL 8
   families. Not the 5 taught ones: ``HELDOUT_FAMILY_IDS = {F3, F7, F8}`` feeds
   ``heldout_questions()``, which feeds the published held-out split, so a taught-only fixture
   would pass straight over a broken held-out family.
2. ``test_forms_is_wired`` — a modified grammar demonstrably CHANGES the output, in BOTH registers.
   ``_family_table`` binds one closure per family id per register at import time, so a bypass wired
   for only one register is the shape a threading bug actually takes. This is the half that is easy
   to skip and the only one that proves the parameter exists at all.

That the pair is load-bearing was DEMONSTRATED rather than argued: reverting ``_render_family``'s
one-line ``SLOT_FORMS`` dispatch while leaving both signatures in place — the kwarg accepted and
discarded — leaves half 1 GREEN and turns only half 2 RED. Recorded in ``21-05-SUMMARY.md``.

``question_bank=`` has no test here because it is deliberately not a parameter. The measurement that
forced that resolution is recorded in ``render_family``'s own docstring, as a decision rather than
as a silence.

Plan 21-07 EXTENDS this module with the filler-corpus tests (the 56 facts, their disjoint slots, and
their re-implemented minting discipline). Nothing here assumes those facts exist yet.

CPU-only, GPU-free, no torch, no network.
"""

import hashlib
import json
import os
import pathlib
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import phase14_factset as fs  # noqa: E402  (needs the sys.path insert above)
import phase21_filler as pf  # noqa: E402  (plan 21-07 — the filler corpus)

from personacore.tokenizer import from_json  # noqa: E402

# Derived the way every other module in this repo derives it (`teach_persona.py`,
# `phase14_factset_gate.py` and eight others all spell exactly this) rather than as a bare
# relative literal, which would break the moment pytest is invoked from another directory.
_TOKENIZER_PATH = _ROOT / "artifacts" / "tokenizer.json"  # FROZEN — never retrain

_GOLDEN_PATH = _ROOT / "tests" / "fixtures" / "golden_render_family_v2.json"
_GOLDEN = json.loads(_GOLDEN_PATH.read_text(encoding="utf-8"))

# The fixture's record of the ONE free choice a consuming test can silently get wrong. Plan 21-02
# added `meta.order` beyond its own spec precisely for this: the captured order is family-outer,
# the TRANSPOSE of `teach_persona.render_episodes`'s fact-outer loop. Both cover the same set, so a
# test that assumed the other order would compute a DIFFERENT digest over IDENTICAL behaviour and
# report it as a regression. So it is asserted below, not assumed — and the serialization kwargs are
# read out of `meta` rather than retyped, for the same reason.
_ORDER = "for family_id in sorted(FAMILY_IDS) for fact in (LOCKED_FACTS + SOFT_TIER_FACTS)"

_CANARY = "THE CANARY"


def _render_all(second_person, **kwargs):
    """The full cross product of all 8 families x all 10 facts, in the fixture's recorded order."""
    facts = fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS
    return [
        fs.render_family(family_id, fact, second_person=second_person, **kwargs)
        for family_id in sorted(fs.FAMILY_IDS)
        for fact in facts
    ]


def _digest(rendered):
    """sha256 in the fixture's OWN serialization, read from ``meta`` rather than retyped."""
    kwargs = dict(_GOLDEN["meta"]["serialization"])
    kwargs["separators"] = tuple(kwargs["separators"])
    return hashlib.sha256(json.dumps(rendered, **kwargs).encode("utf-8")).hexdigest()


def _canary_forms():
    """``SLOT_FORMS`` with ONE slot's ``np1`` replaced.

    ``SlotForms`` is a ``NamedTuple``, so ``._replace`` is its constructor — ``dataclasses.replace``
    does not work on it, and 21-RESEARCH ``§V.4c``'s sketch used the wrong one.
    """
    slot = fs.LOCKED_FACTS[0].slot
    modified = dict(fs.SLOT_FORMS)
    modified[slot] = modified[slot]._replace(np1=_CANARY)
    return modified


@pytest.mark.parametrize("register", ["first_person", "second_person"])
def test_render_family_byte_identity(register):
    """HALF 1 — ``forms=None`` is byte-identical to the pre-edit v2.0 capture."""
    assert _GOLDEN["meta"]["order"] == _ORDER, (
        "the fixture was re-captured in a different iteration order — rebuild this cross product "
        f"to match it rather than reporting the mismatch as a regression: "
        f"{_GOLDEN['meta']['order']!r}"
    )
    assert sorted(fs.FAMILY_IDS) == _GOLDEN["meta"]["family_ids"], (
        "the family set moved since capture; all 8 families must be covered, not just the 5 taught"
    )
    second_person = register == "second_person"

    implicit = _render_all(second_person)
    explicit = _render_all(second_person, forms=None)
    assert implicit == explicit, (
        "render_family(..., forms=None) diverged from the no-kwarg call — the default must not "
        "merely be equal to v2.0, it must be the same code path"
    )

    expected = _GOLDEN[register]
    assert sum(len(pairs) for pairs in implicit) == expected["rows"], (
        "row count moved — a silently shortened cross product must not match the digest by accident"
    )
    assert _digest(implicit) == expected["sha256"], (
        f"render_family's DEFAULT path is no longer byte-identical to the pre-edit v2.0 capture "
        f"({register}). The forms= kwarg was required to be ADDITIVE."
    )


@pytest.mark.parametrize("second_person", [False, True], ids=["first_person", "second_person"])
def test_forms_is_wired(second_person):
    """HALF 2 — the load-bearing one. A modified grammar must REACH the output, both registers."""
    out = fs.render_family(
        "F1", fs.LOCKED_FACTS[0], second_person=second_person, forms=_canary_forms()
    )
    assert any(_CANARY in question for question, _answer in out), (
        "forms= did not reach the output — the `forms=None` byte-identity guard is vacuous."
    )


def test_forms_missing_slot_raises():
    """A filler grammar with a typo must fail loudly, never fall through to a SCORED slot."""
    fact = fs.LOCKED_FACTS[0]
    with pytest.raises(KeyError) as excinfo:
        fs.render_family("F1", fact, forms={})
    assert fact.slot in str(excinfo.value), (
        "a forms= mapping missing the fact's slot must raise KeyError NAMING the slot, rather than "
        "falling back to SLOT_FORMS and quietly rendering a filler fact through a scored slot"
    )


def test_unknown_family_id_fails_identically_on_both_branches():
    """The bypass must not hand an unknown family id a second, differently-shaped failure route."""
    fact = fs.LOCKED_FACTS[0]
    with pytest.raises(KeyError) as default_err:
        fs.render_family("F99", fact)
    with pytest.raises(KeyError) as bypass_err:
        fs.render_family("F99", fact, forms=_canary_forms())
    assert str(bypass_err.value) == str(default_err.value), (
        "the forms= branch must validate family_id against the SAME table the default branch does"
    )


def test_forms_none_leaves_the_published_wall_at_ten():
    """This file joins the `== 10` wall from its first commit, not from plan 21-09."""
    assert len(fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS) == 10, (
        "the published leak vocabulary is LOCKED + SOFT = 10 — no tier is exempt from the scan, "
        "and an additive forms= kwarg must add no fact to either tier"
    )


# =====================================================================================
# Plan 21-07 — the FILLER CORPUS. Everything above is plan 21-05's `forms=` seam and is
# deliberately untouched; everything below is the 56 facts that render through it.
# =====================================================================================


def _child(snippet):
    """Run a snippet in a FRESH interpreter with hash randomization guaranteed ON.

    ``PYTHONHASHSEED`` is popped rather than inherited. If the parent pytest process happened to
    run under a fixed seed, an inherited one would make every child iterate ``TAUGHT_FAMILY_IDS``
    in the SAME order — and the order-stability test below would pass for the wrong reason,
    certifying a `sorted()` that is not there.
    """
    env = dict(os.environ)
    env.pop("PYTHONHASHSEED", None)
    done = subprocess.run(
        [sys.executable, "-c", snippet], capture_output=True, text=True, cwd=_ROOT, env=env
    )
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


def _episode_digest(episodes):
    return hashlib.sha256(
        json.dumps(episodes, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _rows_over_taught(fact, **kwargs):
    """Row count for ONE fact over the taught families — the D-15 unit of comparison."""
    return sum(
        len(fs.render_family(family_id, fact, **kwargs))
        for family_id in sorted(fs.TAUGHT_FAMILY_IDS)
    )


def _verify_round_trips(facts):
    """``fs.token_census`` over the frozen tokenizer — zero generations, so it runs in full."""
    pf.verify_round_trips(from_json(_TOKENIZER_PATH), facts)


def test_slots_disjoint():
    """D-16 — no filler value is ever seated in a slot GATE-10 scores.

    The ``filler_`` prefix is a CONVENTION and a reader's cue; the EMPTY INTERSECTION is the
    PROPERTY. Both are asserted, and the intersection is deliberately asserted FIRST so a genuine
    collision reports as a collision rather than as a naming-style complaint.
    """
    assert set(pf.FILLER_SLOT_FORMS) & set(fs.SLOT_FORMS) == set(), (
        "a filler slot collides with a PUBLISHED slot — 8 of the 11 published slots hold a scored "
        "fact, so filler seated there makes the corpus self-contradictory on exactly the slots "
        "GATE-10 scores, and n=64 recall would fall from CONTENTION rather than from CAPACITY"
    )
    assert set(pf.FILLER_SLOT_FORMS) & set(fs.SLOT_QUESTION_BANK) == set(), (
        "a filler slot collides with a reserved-probe slot key"
    )
    assert all(slot.startswith("filler_") for slot in pf.FILLER_SLOT_FORMS), (
        "the filler_ prefix is the convention that makes the disjointness legible at a glance"
    )
    assert {f.slot for f in pf.FILLER_FACTS} == set(pf.FILLER_SLOT_FORMS), (
        "every filler fact must sit in a declared filler slot and every declared slot must be used"
    )


def test_outside_all_pools():
    """D-13 made checkable — POOL MEMBERSHIP, not module location, is what confers the gate.

    So this asserts NON-membership directly rather than trusting that the file lives elsewhere.
    """
    filler_ids = {f.id for f in pf.FILLER_FACTS}
    pooled_ids = {f.id for _name, pool in fs.all_pools() for f in pool}

    assert filler_ids & pooled_ids == set(), "a filler id reached a published pool"
    assert filler_ids & set(fs.GATE_PROBES) == set(), "a filler id acquired reserved gate probes"
    assert filler_ids & set(fs._BY_ID) == set(), "a filler id became resolvable through _BY_ID"

    filler_values = {fs.normalize_for_match(f.value) for f in pf.FILLER_FACTS}
    forbidden = {fs.normalize_for_match(f.value) for f in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS}
    assert filler_values & forbidden == set(), (
        "a filler value entered the 10-value leak vocabulary (D-18) — that confounds the GATE-10 "
        "capacity comparison AND would force an edit to the ancestry-guarded phase18_extraction.py"
    )

    # The before/after half, run in a FRESH interpreter so "before" genuinely precedes the import.
    # In this process `phase21_filler` is already in `sys.modules`, so an in-process before/after
    # could only ever compare a value to itself.
    census = _child(
        "import sys;"
        f"sys.path.insert(0, {_SCRIPTS!r});"
        "import phase14_factset as fs;"
        "shape=lambda: (len(fs._BY_ID), len(fs.GATE_PROBES), len(fs.all_pools()),"
        " sum(len(p) for _n, p in fs.all_pools()));"
        "before = shape();"
        "import phase21_filler;"
        "print(before, shape())"
    )
    before, after = census.split(") (")
    assert before.lstrip("(") == after.rstrip(")"), (
        f"importing phase21_filler CHANGED the published registers: {census}. Filler must add "
        f"zero rows to _BY_ID, GATE_PROBES and every pool."
    )


def test_minting_discipline():
    """D-17 — the deterministic half, plus each of the three refusals on its OWN offender.

    Three DISTINGUISHABLE reds, never "something raised": a refusal that cannot say which set was
    hit is a refusal that cannot be debugged when it fires two phases from now.
    """
    _verify_round_trips(pf.FILLER_FACTS)

    # Refusal 1 — the 10-value leak vocabulary. `<locked>x` is the load-bearing shape: string
    # EQUALITY would ADMIT it (it is not the locked value), containment REFUSES it.
    # `embedded_fact_values` and the extraction instrument both scan by containment, so equality
    # here would mint a value the leak scan catches later, at a far more expensive moment.
    locked = fs.normalize_for_match(fs.LOCKED_FACTS[0].value)
    with pytest.raises(SystemExit) as scored_err:
        pf.refuse_collisions((fs.Fact("x_scored", "filler_boat_name", locked + "x", "filler"),))
    assert "FORBIDDEN_SCORED_VALUES" in str(scored_err.value)
    assert locked in str(scored_err.value), "the refusal must NAME the value it collided with"

    # Refusal 2 — a published pool value that is NOT in the leak vocabulary, so refusal 1 cannot
    # fire first and mask this one.
    pool_only = sorted(pf.PUBLISHED_POOL_VALUES - pf.FORBIDDEN_SCORED_VALUES)[0]
    with pytest.raises(SystemExit) as pool_err:
        pf.refuse_collisions((fs.Fact("x_pool", "filler_boat_name", pool_only + "x", "filler"),))
    assert "PUBLISHED_POOL_VALUES" in str(pool_err.value)
    assert "FORBIDDEN_SCORED_VALUES" not in str(pool_err.value), (
        "refusal 2 must name its OWN set — a shared message makes the three reds indistinguishable"
    )

    # Refusal 3 — filler against filler, one value nested inside the other.
    nested = ("zephrilune", "zephrilunette")
    for value in nested:  # neither may trip refusal 1 or 2, or this test proves nothing
        pf.refuse_collisions((fs.Fact("x_solo", "filler_boat_name", value, "filler"),))
    with pytest.raises(SystemExit) as self_err:
        pf.refuse_collisions(
            tuple(
                fs.Fact(f"x_self_{i}", "filler_boat_name", v, "filler")
                for i, v in enumerate(nested)
            )
        )
    assert "FILLER SET ITSELF" in str(self_err.value)

    # And the real corpus survives all three.
    pf.refuse_collisions()


def test_filler_renders_identically_in_form_to_a_scored_fact():
    """D-15 — a COMPARISON, never a literal. The claim is that both grammars produce the SAME
    number of rows, so the n=64 lever changes N and nothing else.

    Hard-coding 22 would let a grammar be reshaped to hit a number; asserting EQUALITY makes the
    two tiers pin each other. If they ever diverge, THAT is the finding.
    """
    n_scored = _rows_over_taught(fs.LOCKED_FACTS[0])
    low, high = fs.PARAPHRASES_PER_FACT_TARGET
    assert low <= n_scored <= high, (
        f"the SCORED baseline itself left DEMO-05's paraphrase band: {n_scored} not in "
        f"{fs.PARAPHRASES_PER_FACT_TARGET}"
    )

    counts = {f.id: _rows_over_taught(f, forms=pf.FILLER_SLOT_FORMS) for f in pf.FILLER_FACTS}
    observed = set(counts.values())
    total = len(pf.render_filler_episodes())
    assert observed == {n_scored}, (
        f"filler does NOT render identically in FORM to a scored fact. scored={n_scored}, "
        f"filler counts observed={sorted(observed)}, filler total rows={total}, "
        f"n=64 total={n_scored * len(fs.LOCKED_FACTS) + total}. Different-sized records under one "
        f"clip norm change N and per-record mass at once, confounding the GATE-10 comparison."
    )
    assert total == n_scored * len(pf.FILLER_FACTS), (
        f"render_filler_episodes() returned {total} rows, not {len(pf.FILLER_FACTS)} x {n_scored}"
    )
    assert len(fs.LOCKED_FACTS) + len(pf.FILLER_FACTS) == 64, (
        "the n=64 arm is 8 scored LOCKED_FACTS + 56 unscored filler (D-12), never 64 fresh facts"
    )


def test_render_filler_episodes_is_order_stable():
    """T-21-57 — ONE process can never catch a frozenset-order bug.

    ``fs.TAUGHT_FAMILY_IDS`` is a ``frozenset``; iterated raw it was measured yielding a DIFFERENT
    order in 12 of 12 separate interpreters, so without ``sorted()`` the n=64 bin is byte-different
    every run and every sha256 downstream of it is meaningless — a failure that never surfaces as
    an error, only as an artifact that will not regenerate.
    """
    snippet = (
        "import sys, json, hashlib;"
        f"sys.path.insert(0, {_SCRIPTS!r});"
        "import phase21_filler as pf;"
        "print(hashlib.sha256(json.dumps(pf.render_filler_episodes(), ensure_ascii=False,"
        " separators=(',', ':')).encode('utf-8')).hexdigest())"
    )
    here = _episode_digest(pf.render_filler_episodes())
    first, second = _child(snippet), _child(snippet)
    assert here == first == second, (
        f"render_filler_episodes() is NOT order-stable across processes: this process {here}, "
        f"children {first} and {second}. Iterate sorted(family_ids), mirroring "
        f"teach_persona.render_episodes."
    )


def test_guessability_waiver_is_recorded():
    """D-17 — a waiver that is not machine-checkable is a comment, and can drift into a silence."""
    waiver = pf.GUESSABILITY_WAIVER
    assert "1,792" in waiver, "the waiver must carry its MEASURED price, not just its reason"
    assert "convbase_best.pt" in waiver, "the waiver must name the model the probe would prompt"
    assert "PROBE_SEEDS" in waiver, "the waiver must show the derivation, not only the total"
    assert "never enters the 10-value leak vocabulary" in waiver.replace("\n", " "), (
        "the waiver must state the REASON the probe is inapplicable, so a later reader cannot "
        "mistake a deliberate judgment for an omission"
    )
