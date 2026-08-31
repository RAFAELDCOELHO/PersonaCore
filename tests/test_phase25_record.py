"""PLAN 25-08 — D-34's FIVE HALTS EACH WATCHED, and every reported column proved outside the gate.

D-34 IS THE HIGHEST-SEVERITY GUARD IN THIS PHASE, so every one of its five fields is watched
halting the sweep individually rather than one representative field being watched and the other
four being trusted. A guard proved on one member of a tuple is a guard proved on one member of a
tuple. The five live as five separately NAMED tests, and
`test_every_pinned_field_has_its_own_watched_halt` walks THIS FILE by AST to prove the five stay in
step with `MECHANISM_PIN_FIELDS`: adding a sixth pinned field with no watched halt goes RED here,
which is the only way a parametrization-by-hand stays honest.

REFUSALS ARE ASSERTED ON `SystemExit`, NEVER ON `Exception`. `SystemExit` derives from
`BaseException`, so `pytest.raises(Exception)` does NOT catch it and a test written that way passes
for the wrong reason.

THE VERDICT-KWARG DISJOINTNESS IS RESOLVED BY AST, NEVER BY `grep -c`. `scripts/mitigation_gate.py`
discusses every one of these names in its own prose and docstrings, so a textual count over it
measures the documentation rather than the signature — the false-RED class RPT-02 exists to close,
and one this repository hit four times in Phase 20 alone. Measured at plan time on the same shape:
`grep -c 'grep -c'` over `tests/test_phase23_cost.py` returns 3 while an AST gate over the same
file exits 0.

CPU-ONLY, AND NEVER SKIPS. Nothing here touches MPS or a model. `scripts/phase25_record.py` itself
imports neither torch nor numpy (asserted twice below — statically by AST and dynamically in a
FRESH INTERPRETER, the Phase-15 figure-guard register), but this file deliberately DOES import
`phase18_extraction`, which pulls torch on a CPU device, because the point of that import is to
prove the tier names the record carries are the frozen module's own rather than a copy that agreed
once.
"""

import ast
import hashlib
import inspect
import json
import pathlib
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

import mitigation_budget  # noqa: E402  (scripts/ is not a package)
import mitigation_gate  # noqa: E402  (same)
import mitigation_unit  # noqa: E402  (same)
import phase24_adversarial as pa  # noqa: E402  (same)
import phase25_condition_c as cc  # noqa: E402  (same)
import phase25_epsilon  # noqa: E402  (same)
import phase25_gate05 as g5  # noqa: E402  (same)
import phase25_prereg as prereg  # noqa: E402  (same)
import phase25_record as rec  # noqa: E402  (same)
from _prose import normalized  # noqa: E402  (same)

_RECORD_SOURCE = _ROOT / "scripts" / "phase25_record.py"
_GATE_SOURCE = _ROOT / "scripts" / "mitigation_gate.py"
_THIS_FILE = pathlib.Path(__file__).resolve()

# D-28's two multiplicity figures, quoted at full precision from
# `results/phase21_multiplicity.json`, whose own `pin_discrepancy.status` is
# "RECORDED, NOT RESOLVED — the pin is frozen and is not edited".
OVERLAP_RULE_MULTIPLICITY = "262.9437465865647"
FIRST_TOKEN_RULE_MULTIPLICITY = "207.0180229382851"

# D-48/D-49's two retention floors. The governing one is the MEASURED adapter-regime value; the
# borrowed one is the Phase-12 full-fine-tune constant that
# `phase20_gate_coverage._prove_retention_floor` REFUSES by name and by regime.
GOVERNING_RETENTION_FLOOR = 0.008681618994239138
BORROWED_RETENTION_FLOOR = 0.06893

# Phase 19's committed pre-erasure capability readings, denominators included. Using the real
# figures rather than invented ones means the fixture is the shape `measure_condition_c` returns
# AND reproduces the record condition (c) arrives with a free bit-level reproduction check against.
CAPABILITY = {
    "adapter_on": 5.815445876712191,
    "adapter_off": 4.573349214207799,
    "n_targets": 270203,
    "retention_ppl": 4.219759892336485,
    "retention_total_tokens": 1000285,
}

PIN_N8 = {
    "composed_steps": 200,
    "composed_lot_sizes": [8],
    "records_per_lot": 8,
    "q": mitigation_unit.SAMPLING_RATE_Q,
    "clip_norm": 1000000.0,
}
PIN_N64 = dict(PIN_N8, composed_lot_sizes=[64], records_per_lot=64)

# One perturbation per pinned field. Each is a value the mechanism could plausibly drift TO — a
# truncated run, a mis-sized lot, a sampler swapped back to with-replacement, a re-pinned C — so
# the halt is watched on a realistic divergence rather than on an obvious one.
PERTURBATIONS = {
    "composed_steps": 199,
    "composed_lot_sizes": [7],
    "records_per_lot": 7,
    "q": 0.9999999999,
    "clip_norm": 999999.0,
}


def _rows(tier, per_family):
    """One tier's per-question rows, ``per_family`` of them for each of the four scored families."""
    return [
        {
            "question_id": f"{tier}-{family}-{index}",
            "family": family,
            "tier": tier,
            "successes": 0,
            "draws": mitigation_budget.CURVE_K,
        }
        for family in rec.ATTACK_FAMILIES
        for index in range(per_family)
    ]


def _refusal():
    """D-39's column over the real `phase24_adversarial` refusal vocabulary."""
    templates = [pa.refusal_for(slot) for slot in g5.GATE05_SLOTS]
    completions = {
        family: ["i will not share my name.", "brindlemoor", "i will not share my street."]
        for family in rec.ATTACK_FAMILIES
    }
    return rec.refusal_column(completions, templates)


def _build(**overrides):
    """One point record, with the sigma=0 n=8 control as the default and everything overridable."""
    kwargs = {
        "point_key_value": "dp_n8_sigma0p000000",
        "arm": "dp_n8",
        "axis_value": 0.0,
        "live_mechanism": dict(PIN_N8),
        "pinned_mechanism": dict(PIN_N8),
        "draws_per_question": mitigation_budget.CURVE_K,
        "draws_per_question_source": "mitigation_budget.CURVE_K",
        "per_question": {
            rec.GATED_TIER: _rows(rec.GATED_TIER, 104),
            rec.REPORTED_TIER: _rows(rec.REPORTED_TIER, 112),
        },
        "family_counts": {
            family: {"successes": 0, "questions": 104, "draws": 1664}
            for family in rec.ATTACK_FAMILIES
        },
        "refusal": _REFUSAL_COLUMN,
        "adapter_path": "checkpoints/phase25_dp_n8_sigma0p000000_adapter.pt",
        "adapter_sha256": hashlib.sha256(b"phase25_dp_n8_sigma0p000000").hexdigest(),
        "n_facts": 8,
        "capability": dict(CAPABILITY),
        "control_gap": CAPABILITY["adapter_on"] - CAPABILITY["adapter_off"],
        "seed_spread": [0.01, 0.02],
        "zero_extraction_has_nll": True,
        "gate05_gated": {"slots": list(g5.GATE05_SLOTS), "gaps": []},
        "gate05_reported": {
            "n_facts": 8,
            "tier_slot_count": 8,
            "exposure_columns": g5.REQUIRED_NLL_COLUMNS,
            "governs": g5.GATE05_GOVERNS,
        },
        "point_epsilon": None,
        "accounting": None,
    }
    kwargs.update(overrides)
    return rec.build_point_record(**kwargs)


# Built ONCE: `refusal_column` renders D-11's two clean-frame probe populations, which is real work
# and identical for every record here.
_REFUSAL_COLUMN = _refusal()


@pytest.fixture(scope="module")
def control_record():
    """The sigma=0 n=8 CONTROL. It is a real DP sweep point (CTRL-02) and has no privacy value."""
    return _build()


@pytest.fixture(scope="module")
def noised_record():
    """A noised n=64 DP point at sigma=0.5, carrying the accountant's own value for that sigma."""
    return _build(
        point_key_value="dp_n64_sigma0p500000",
        arm="dp_n64",
        axis_value=0.5,
        live_mechanism=dict(PIN_N64),
        pinned_mechanism=dict(PIN_N64),
        n_facts=64,
        adapter_path="checkpoints/phase25_dp_n64_sigma0p500000_adapter.pt",
        adapter_sha256=hashlib.sha256(b"phase25_dp_n64_sigma0p500000").hexdigest(),
        gate05_reported={
            "n_facts": 64,
            "tier_slot_count": 64,
            "exposure_columns": g5.REQUIRED_NLL_COLUMNS,
            "governs": g5.GATE05_GOVERNS,
        },
        point_epsilon=phase25_epsilon.point_epsilon_for_sigma(
            0.5, steps=mitigation_budget.STEP_BUDGET, delta=mitigation_unit.DELTA
        ),
        accounting={
            "rule": "basic composition over the noised DP points actually published (D-29)",
            "delta": mitigation_unit.DELTA,
            "q": mitigation_unit.SAMPLING_RATE_Q,
            "selection_accounted": phase25_epsilon.SELECTION_ACCOUNTED,
        },
    )


@pytest.fixture(scope="module")
def adversarial_record():
    """An adversarial point at the pool ceiling. It makes NO formal claim: `accounting` is null."""
    return _build(
        point_key_value="adv_n8_ratio1p909091",
        arm="adv_n8",
        axis_value=mitigation_budget.ADVERSARIAL_RATIO_GRID[-1],
        adapter_path="checkpoints/phase25_adv_n8_ratio1p909091_adapter.pt",
        adapter_sha256=hashlib.sha256(b"phase25_adv_n8_ratio1p909091").hexdigest(),
    )


# =================================================================================================
# ===== (a) D-34's FIVE HALTS, EACH WATCHED. ONE PER FIELD, NAMED. =====
# =================================================================================================


def _watch_halt(field):
    """Perturb exactly ``field`` and assert the halt names the field, both values and the sweep."""
    pinned = dict(PIN_N8)
    live = dict(pinned)
    live[field] = PERTURBATIONS[field]
    with pytest.raises(SystemExit) as excinfo:
        rec.prove_mechanism_matches_pin(live, pinned, point_key="dp_n8_sigma0p000000")
    message = str(excinfo.value)
    assert repr(field) in message, message
    assert repr(live[field]) in message, message
    assert repr(pinned[field]) in message, message
    assert "dp_n8_sigma0p000000" in message, message
    assert "THE WHOLE SWEEP HALTS" in message, message
    assert normalized("DOES NOT DESCRIBE WHAT HAPPENED") in normalized(message), message
    return message


def test_a_diverged_composed_steps_halts_the_whole_sweep():
    """T = 200 is MEASURED at both capacities (D-27); a truncated run is not the pinned run."""
    _watch_halt("composed_steps")


def test_a_diverged_composed_lot_sizes_halts_the_whole_sweep():
    """The lot IS the fact set (D-26); a lot of a different size is a different privacy unit."""
    _watch_halt("composed_lot_sizes")


def test_a_diverged_records_per_lot_halts_the_whole_sweep():
    """`grad_accum_steps = n_facts` governs micro-steps inside one optimizer step (D-27)."""
    _watch_halt("records_per_lot")


def test_a_diverged_q_halts_the_whole_sweep():
    """THE ONE GENUINELY NEW FIELD. A drift off 1.0 means the with-replacement sampler is back."""
    message = _watch_halt("q")
    assert "SAMPLING_RATE_Q" in message, message


def test_a_diverged_clip_norm_halts_the_whole_sweep():
    """A FLOAT, CHECKED WITH NO TOLERANCE. `std = sigma * C`, so C is the noise scale too (D-25)."""
    _watch_halt("clip_norm")


def test_every_pinned_field_has_its_own_watched_halt():
    """The five named tests above are proved to stay in step with `MECHANISM_PIN_FIELDS`.

    Written as an AST walk over THIS FILE rather than as a `parametrize`, because the plan's own
    contract names `test_a_diverged_composed_steps_halts_the_whole_sweep` as a function that must
    exist. This is what keeps the hand-written five honest: a sixth pinned field with no watched
    halt goes RED here, and so does a watched halt whose field left the pin.
    """
    tree = ast.parse(_THIS_FILE.read_text(encoding="utf-8"))
    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    expected = {
        f"test_a_diverged_{field}_halts_the_whole_sweep" for field in rec.MECHANISM_PIN_FIELDS
    }
    assert expected <= defined, sorted(expected - defined)
    watched = {name for name in defined if name.endswith("_halts_the_whole_sweep")}
    assert watched == expected, sorted(watched ^ expected)
    assert set(PERTURBATIONS) == set(rec.MECHANISM_PIN_FIELDS), sorted(
        set(PERTURBATIONS) ^ set(rec.MECHANISM_PIN_FIELDS)
    )


def test_an_exact_match_writes_without_incident(tmp_path, monkeypatch, control_record):
    """A matching mechanism returns True and the record lands, round-tripping through JSON."""
    assert rec.prove_mechanism_matches_pin(dict(PIN_N8), dict(PIN_N8), point_key="x") is True

    destination = tmp_path / "phase25_point_dp_n8_sigma0p000000.json"
    monkeypatch.setattr(rec, "point_record_path", lambda key: destination)
    written = rec.write_point_record(
        control_record, point_key_value="dp_n8_sigma0p000000", tracked=[]
    )
    assert written == destination and destination.exists()
    assert json.loads(destination.read_text(encoding="utf-8")) == json.loads(
        json.dumps(control_record)
    )


def test_the_halt_is_not_a_warning(tmp_path):
    """The halt RAISES rather than returning, and no record object survives a diverged build.

    `build_point_record` calls `prove_mechanism_matches_pin` BEFORE it assembles anything, so a
    diverged point produces no dict to be written by accident, and `tmp_path` stays empty.
    """
    with pytest.raises(SystemExit):
        _build(live_mechanism=dict(PIN_N8, composed_steps=199))
    assert list(tmp_path.iterdir()) == []
    assert not rec.point_record_path("dp_n8_sigma0p000000").exists(), (
        "a per-point record exists on disk while POINT_RECORDS_AT_COMMIT is "
        f"{prereg.POINT_RECORDS_AT_COMMIT}"
    )


# =================================================================================================
# ===== (b) D-39's REFUSAL COLUMN — IN COUNTS, AND OUTSIDE THE GATE =====
# =================================================================================================


def _verdict_kwonly_names_by_ast():
    """`mitigation_point_verdict`'s keyword-only parameter names, by AST over the frozen gate.

    AST AND NEVER GREP: that file's own prose discusses every one of these names, so a textual
    count over it measures the documentation rather than the signature.
    """
    tree = ast.parse(_GATE_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "mitigation_point_verdict":
            return tuple(arg.arg for arg in node.args.kwonlyargs)
    raise AssertionError("mitigation_point_verdict is not defined in scripts/mitigation_gate.py")


def test_the_refusal_column_is_counts_not_rates(adversarial_record):
    """Every refusal value is an `int`, and every numerator has its denominator beside it."""
    column = adversarial_record["refusal"]
    populations = [column["total"], *column["by_family"].values()]
    assert column["by_family"] and set(column["by_family"]) == set(rec.ATTACK_FAMILIES)
    for row in populations:
        assert set(row) == {"refusal_k", "refusal_n"}, row
        for name, value in row.items():
            assert type(value) is int, (name, value, type(value))
        assert row["refusal_n"] > 0, row
        assert row["refusal_k"] <= row["refusal_n"], row
    assert column["total"]["refusal_k"] == sum(
        row["refusal_k"] for row in column["by_family"].values()
    )
    assert column["total"]["refusal_n"] == sum(
        row["refusal_n"] for row in column["by_family"].values()
    )
    assert set(column["denominator_provenance"]) >= {"locked", "filler"}


def test_the_refusal_column_is_not_a_verdict_kwarg(adversarial_record):
    """T-25-38: a reported refusal count silently becoming a verdict condition."""
    kwonly = _verdict_kwonly_names_by_ast()
    assert len(kwonly) == 21, kwonly
    assert set(kwonly) == set(rec.VERDICT_KWARGS), sorted(set(kwonly) ^ set(rec.VERDICT_KWARGS))

    column = adversarial_record["refusal"]
    names = {"refusal", *column, *column["by_family"], "refusal_k", "refusal_n"}
    assert not names & set(kwonly), sorted(names & set(kwonly))

    with pytest.raises(SystemExit):
        rec.prove_names_are_outside_the_gate({"control_gap"}, what="a planted collision")


def test_the_refusal_column_carries_its_governs_string(adversarial_record):
    """Matched through `scripts/_prose.normalized`: a line wrap cannot make it a false absence."""
    governs = normalized(adversarial_record["refusal"]["governs"])
    assert normalized("REPORTED INFORMATION, NEVER A VERDICT CONDITION") in governs
    assert normalized("IT SITS OUTSIDE THE THREE-CONDITION GATE") in governs
    assert normalized("IT IS COUNTS, NEVER RATES") in governs


def test_the_refusal_wiring_calls_the_orphaned_helpers():
    """Phase 24 HUMAN-UAT item 3's wiring half: both orphans appear as CALLS, by AST."""
    tree = ast.parse(_RECORD_SOURCE.read_text(encoding="utf-8"))
    called = {
        getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    assert "score_refusal" in called, sorted(name for name in called if name)
    assert "clean_frame_probe_populations" in called, sorted(name for name in called if name)


# =================================================================================================
# ===== (c) D-21's INLINE k =====
# =================================================================================================


def _readings_carrying_a_privacy_value(node):
    """Every dict anywhere in ``node`` that carries an `epsilon` key."""
    found = []
    if isinstance(node, dict):
        if "epsilon" in node:
            found.append(node)
        for value in node.values():
            found.extend(_readings_carrying_a_privacy_value(value))
    elif isinstance(node, list):
        for value in node:
            found.extend(_readings_carrying_a_privacy_value(value))
    return found


def test_every_epsilon_bearing_reading_carries_its_own_k_inline(noised_record):
    """T-25-39: a K=16 curve reading published as a K=48 promoted reading."""
    readings = _readings_carrying_a_privacy_value(noised_record)
    assert readings, "no reading carries a privacy value at all; the walk would pass vacuously"
    for reading in readings:
        assert "draws_per_question" in reading, sorted(reading)
        assert "draws_per_question_source" in reading, sorted(reading)
        assert reading["draws_per_question"] == rec.K_SOURCES[reading["draws_per_question_source"]]
    assert normalized("NUMERICALLY IDENTICAL") in normalized(
        noised_record["draws_per_question_governs"]
    )


def test_a_k16_and_a_k48_reading_are_distinguishable():
    """Numerically identical privacy value, different statistical power — never equal as dicts."""
    curve = rec.epsilon_bearing_reading(
        value=519.6981942303134,
        draws_per_question=mitigation_budget.CURVE_K,
        draws_per_question_source="mitigation_budget.CURVE_K",
    )
    promoted = rec.epsilon_bearing_reading(
        value=519.6981942303134,
        draws_per_question=mitigation_budget.FULL_FIDELITY_K,
        draws_per_question_source="mitigation_budget.FULL_FIDELITY_K",
    )
    assert curve["epsilon"] == promoted["epsilon"]
    assert curve != promoted
    with pytest.raises(SystemExit):
        rec.epsilon_bearing_reading(
            value=1.0,
            draws_per_question=mitigation_budget.FULL_FIDELITY_K,
            draws_per_question_source="mitigation_budget.CURVE_K",
        )


# =================================================================================================
# ===== (d) D-05's TWO TIERS =====
# =================================================================================================


def test_both_tiers_are_dispatched_but_only_the_gated_one_feeds_the_gate(control_record):
    """416 = 104 x 4 gates; 448 is dispatched and REPORTED. Tier names read from the frozen file."""
    import phase18_extraction as p18

    assert rec.GATED_TIER == p18.GATED_TIER == "core_held_out"
    assert rec.REPORTED_TIER == p18.REPORTED_TIER == "core_taught"
    assert rec.ATTACK_FAMILIES == p18.ATTACK_FAMILIES
    assert control_record["gated_tier"] == p18.GATED_TIER
    assert control_record["reported_tier"] == p18.REPORTED_TIER

    gated = control_record["per_question"][p18.GATED_TIER]
    reported = control_record["per_question"][p18.REPORTED_TIER]
    assert len(gated) == 416 == 104 * len(p18.ATTACK_FAMILIES)
    assert len(reported) == 448 == 112 * len(p18.ATTACK_FAMILIES)
    assert normalized("ONLY ONE GATES") in normalized(control_record["tier_governs"])


def test_family_zero_is_excluded_from_the_gated_tier(control_record):
    """`family_zero_run: False`. A fifth family would move the denominator X is read against."""
    import phase18_extraction as p18

    assert p18.FAMILY_ZERO not in p18.ATTACK_FAMILIES
    assert control_record["family_zero_run"] is False
    families = {row["family"] for row in control_record["per_question"][p18.GATED_TIER]}
    assert families == set(p18.ATTACK_FAMILIES)
    assert p18.FAMILY_ZERO not in families


# =================================================================================================
# ===== (e) D-36's PER-FAMILY COUNTS, INCLUDING A2 =====
# =================================================================================================


def test_every_point_carries_per_family_counts_including_the_held_out_family(noised_record):
    """A2 is already one of the four scored shapes, so carrying it costs nothing and buys D-36."""
    counts = noised_record["per_family_counts"]
    assert set(counts) == set(rec.ATTACK_FAMILIES)
    assert rec.HELD_OUT_FAMILY == "A2" and rec.HELD_OUT_FAMILY in counts
    assert set(rec.TRAINED_FAMILIES) | {rec.HELD_OUT_FAMILY} == set(rec.ATTACK_FAMILIES)
    for family, row in counts.items():
        for name, value in row.items():
            assert type(value) is int, (family, name, value, type(value))
    with pytest.raises(SystemExit):
        rec.per_family_counts({family: {"successes": 0} for family in rec.TRAINED_FAMILIES})


# =================================================================================================
# ===== (f) D-37's TWO RESERVATIONS =====
# =================================================================================================


def test_the_adapter_sha256_travels_inside_the_record(noised_record):
    """`checkpoints/` and `*.pt` are gitignored, so without this Phase 26 has nothing to audit."""
    digest = noised_record["adapter_sha256"]
    assert len(digest) == 64 and set(digest) <= set("0123456789abcdef")
    assert noised_record["adapter_path"].endswith(".pt")
    assert normalized("recorded INSIDE") in normalized(
        prereg.CANARY_RESERVATIONS["adapter_retention"]
    )


def test_the_canary_population_records_the_n8_out_of_corpus_asymmetry(
    control_record, noised_record
):
    """At n=8 the 56 filler facts are OUT; at n=64 all 64 are IN. Only n=8 has canaries at all."""
    small = control_record["canary_population"]
    assert small["n_facts"] == 8
    assert small["in_corpus"] == 8
    assert small["out_of_corpus"] == 56
    assert small["has_out_of_corpus_canaries"] is True

    large = noised_record["canary_population"]
    assert large["n_facts"] == 64
    assert large["in_corpus"] == 64
    assert large["out_of_corpus"] == 0
    assert large["has_out_of_corpus_canaries"] is False

    for population in (small, large):
        assert normalized("ONLY n=8 POINTS HAVE OUT-OF-CORPUS CANARIES AT ALL") in normalized(
            population["structural_note"]
        )
    with pytest.raises(SystemExit):
        rec.canary_population(32)


# =================================================================================================
# ===== (g) D-28's TWO MULTIPLICITIES AND SECTION C5's EXPLICIT nulls =====
# =================================================================================================


def test_multiplicity_names_both_figures(noised_record):
    """Neither figure is hidden: the record's own status is RECORDED, NOT RESOLVED."""
    sentence = normalized(noised_record["multiplicity"])
    assert OVERLAP_RULE_MULTIPLICITY in sentence, sentence[:400]
    assert FIRST_TOKEN_RULE_MULTIPLICITY in sentence, sentence[:400]
    assert normalized("RECORDED, NOT RESOLVED") in sentence


def test_the_control_record_writes_epsilon_null_explicitly(control_record):
    """T-25-41. Asserted by KEY MEMBERSHIP, never by `.get()`: an omission must be RED."""
    assert "epsilon" in control_record
    assert control_record["epsilon"] is None
    assert "epsilon_omitted_reason" in control_record
    assert control_record["epsilon_omitted_reason"] == phase25_epsilon.CONTROL_EPSILON_FIELD_FORM
    assert normalized("IT NEVER OMITS THE KEY") in normalized(
        control_record["epsilon_omitted_reason"]
    )
    # And section C5's correction reproduces: the cited precedent does not exist.
    n_keys, has_key = phase25_epsilon.sigma_zero_epsilon_absence()
    assert has_key is False, n_keys


def test_the_adversarial_record_writes_accounting_null(adversarial_record, noised_record):
    """The arm makes no formal claim, and that is written down rather than inferred from absence."""
    assert "accounting" in adversarial_record
    assert adversarial_record["accounting"] is None
    assert "epsilon" in adversarial_record and adversarial_record["epsilon"] is None
    assert normalized("THE ADVERSARIAL ARM MAKES NO FORMAL CLAIM") in normalized(
        adversarial_record["epsilon_omitted_reason"]
    )
    # The DP arm, by contrast, carries one.
    assert noised_record["accounting"] is not None
    assert noised_record["epsilon"] == phase25_epsilon.point_epsilon_for_sigma(
        0.5, steps=mitigation_budget.STEP_BUDGET, delta=mitigation_unit.DELTA
    )
    assert round(noised_record["epsilon"], 4) == 519.6982
    with pytest.raises(SystemExit):
        _build(
            point_key_value="adv_n8_ratio1p909091",
            arm="adv_n8",
            axis_value=mitigation_budget.ADVERSARIAL_RATIO_GRID[-1],
            accounting={"delta": mitigation_unit.DELTA},
        )


# =================================================================================================
# ===== (g2) AREA 7's CARRIAGE, ASSERTED RATHER THAN ASSUMED =====
# =================================================================================================


def test_every_condition_c_field_travels_in_the_record(control_record):
    """T-25-43: the exact state all 44 Phase 23 records are in, refused structurally."""
    group = control_record["condition_c"]
    assert set(group) == set(cc.CONDITION_C_FIELDS), sorted(set(group) ^ set(cc.CONDITION_C_FIELDS))
    parameters = inspect.signature(mitigation_gate.mitigation_point_verdict).parameters
    for field in cc.CONDITION_C_FIELDS[: cc.CONDITION_C_VERDICT_FIELD_COUNT]:
        assert field in parameters, field
        assert parameters[field].kind is inspect.Parameter.KEYWORD_ONLY, field


def test_both_condition_c_perplexities_carry_their_denominators(control_record):
    """Counts, never rates. A mean over a token population is uncomparable without its size."""
    group = control_record["condition_c"]
    assert type(group["dialogue_n_targets"]) is int
    assert type(group["retention_total_tokens"]) is int
    assert group["dialogue_n_targets"] == CAPABILITY["n_targets"]
    assert group["retention_total_tokens"] == CAPABILITY["retention_total_tokens"]
    assert group["point_dialogue_ppl_on"] == CAPABILITY["adapter_on"]
    assert group["point_dialogue_ppl_off"] == CAPABILITY["adapter_off"]
    assert group["gap_noise_floor"] == cc.gap_noise_floor()[0]


def test_the_nll_flag_is_a_plain_bool_in_the_record(control_record):
    """T-25-44: a truthy `(False, reason)` pair disarming the gate's INCONCLUSIVE branch."""
    assert type(control_record["zero_extraction_has_nll"]) is bool
    assert bool((False, "the probe was too weak")) is True, "the pair under test must be TRUTHY"
    with pytest.raises(SystemExit):
        _build(zero_extraction_has_nll=(False, "the probe was too weak"))
    with pytest.raises(SystemExit):
        _build(zero_extraction_has_nll=0)


def test_the_reported_gate05_tier_is_not_a_verdict_kwarg(noised_record):
    """The reported tier is diagnostic information that never enters a verdict."""
    parameters = inspect.signature(mitigation_gate.mitigation_point_verdict).parameters
    kwonly = {
        name
        for name, parameter in parameters.items()
        if parameter.kind is inspect.Parameter.KEYWORD_ONLY
    }
    assert len(kwonly) == 21
    assert not set(noised_record["gate05_reported"]) & kwonly
    assert not set(noised_record["gate05_gated"]) & kwonly
    assert normalized("NEVER ENTERS A VERDICT") in normalized(noised_record["gate05_governs"])
    with pytest.raises(SystemExit):
        _build(gate05_reported={"point_retention_ppl": 4.2})


def test_both_retention_floors_and_both_caps_travel(control_record):
    """T-25-45 / D-48 / D-49. Both readings published; the correction NARROWS the window."""
    assert control_record["retention_floor_governing"] == GOVERNING_RETENTION_FLOOR
    assert control_record["retention_floor_borrowed"] == BORROWED_RETENTION_FLOOR
    assert control_record["retention_cap_governing"] < control_record["retention_cap_borrowed"]
    assert control_record["retention_cap_governing"] == mitigation_gate.retention_cap(
        retention_noise_floor=GOVERNING_RETENTION_FLOOR
    )
    assert control_record["retention_cap_borrowed"] == mitigation_gate.retention_cap(
        retention_noise_floor=BORROWED_RETENTION_FLOOR
    )
    for name in ("retention_headroom_governing", "retention_headroom_borrowed"):
        assert name in control_record
    assert (
        control_record["retention_headroom_governing"]
        < control_record["retention_headroom_borrowed"]
        < 0
    ), "D-49 pre-registers that the retention leg BINDS at the anchor, on both floors"


def test_the_governing_retention_floor_is_the_verdict_input(control_record):
    """The verdict reads the GOVERNING floor; the borrowed one travels as a disclosure only."""
    assert control_record["condition_c"]["retention_noise_floor"] == GOVERNING_RETENTION_FLOOR
    assert control_record["condition_c"]["retention_noise_floor"] != BORROWED_RETENTION_FLOOR
    assert control_record["verdict_reads"] == "retention_floor_governing"
    assert cc.retention_floor_for_verdict() == GOVERNING_RETENTION_FLOOR
    anchor = control_record["retention_leg_binds_at_anchor"]
    assert anchor["governing"]["floor"] == GOVERNING_RETENTION_FLOOR
    assert anchor["borrowed"]["floor"] == BORROWED_RETENTION_FLOOR
    assert anchor["governing"]["admit_factor"] > anchor["borrowed"]["admit_factor"], (
        "the governing floor must need a LARGER growth factor to admit the taught reading; "
        "D-49 holds a fortiori under it"
    )


def test_the_counterfactual_group_is_present_and_re_derives(control_record):
    """D-50, at zero compute: the cap re-derives from the record's OWN floor, under exact `==`."""
    group = control_record["condition_c"]
    for name in (
        "counterfactual_retention_floor",
        "counterfactual_retention_cap",
        "counterfactual_retention_headroom",
    ):
        assert name in group, sorted(group)
    assert group["counterfactual_retention_cap"] == mitigation_gate.retention_cap(
        retention_noise_floor=group["counterfactual_retention_floor"]
    )
    assert group["counterfactual_retention_headroom"] == (
        group["counterfactual_retention_cap"] - group["point_retention_ppl"]
    )
    # The floor is the LARGEST observed seed-to-seed spread, the conservative choice.
    assert group["counterfactual_retention_floor"] == 0.02


def test_the_counterfactual_floor_refuses_an_empty_seed_spread():
    """A floor is a MAGNITUDE measured from at least one seed-to-seed difference."""
    with pytest.raises(SystemExit):
        _build(seed_spread=[])
    with pytest.raises(SystemExit):
        _build(seed_spread=[-0.01])


# =================================================================================================
# ===== (h) THE TAMPER CHECK =====
# =================================================================================================


def test_a_one_digit_edit_to_a_committed_count_is_caught(tmp_path, control_record):
    """T-25-40. The edit is made on a `tmp_path` COPY; the real tree is never touched."""
    payload = json.dumps(control_record, indent=2, sort_keys=True) + "\n"
    original_digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    family = rec.HELD_OUT_FAMILY
    tampered = json.loads(payload)
    before = tampered["per_family_counts"][family]["questions"]
    tampered["per_family_counts"][family]["questions"] = before + 1
    copy = tmp_path / "phase25_point_dp_n8_sigma0p000000.json"
    copy.write_text(json.dumps(tampered, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    tampered_digest = hashlib.sha256(copy.read_bytes()).hexdigest()
    assert tampered_digest != original_digest
    reread = json.loads(copy.read_text(encoding="utf-8"))
    assert reread["per_family_counts"][family]["questions"] == before + 1
    # And the untouched record still hashes to what it did before the copy was edited.
    rehashed = json.dumps(control_record, indent=2, sort_keys=True) + "\n"
    assert hashlib.sha256(rehashed.encode("utf-8")).hexdigest() == original_digest


# =================================================================================================
# ===== (i) THE PATHS, THE GRAMMAR AND THE WRITE =====
# =================================================================================================


def test_the_frontier_record_owns_the_artifact_filename():
    """ROADMAP's `phase2X_frontier.json` is a placeholder; this module owns the real name (D-31)."""
    assert rec.FRONTIER_RECORD.name == "phase25_frontier.json"
    assert rec.FRONTIER_RECORD.parent == _ROOT / "results"
    pathspec = rec._PUBLICATION_PATHSPEC
    assert pathspec[:4] == ("scripts", "src", "results", "artifacts")
    assert pathspec[-1] == ":(exclude)results/phase25_frontier.json"


def test_the_writer_path_matches_the_pre_registered_glob():
    """A record filed where `POINT_RECORD_GLOB` is blind is invisible to the one-attempt rule."""
    import fnmatch

    for key in ("dp_n8_sigma0p000000", "adv_n64_ratio1p909091"):
        relative = rec.point_record_path(key).relative_to(_ROOT)
        assert fnmatch.fnmatch(str(relative), prereg.POINT_RECORD_GLOB), (relative,)
        assert str(relative) == prereg.point_record_path(key)
    with pytest.raises(SystemExit):
        rec.point_record_path("../escape")


def test_the_point_key_grammar_round_trips_and_orders():
    """The KEY round-trips; the float does not, and the record's own axis field is authoritative."""
    for arm, value in (("dp_n8", 0.0), ("dp_n64", 0.5), ("adv_n8", 0.25), ("adv_n64", 1.5)):
        key = rec.point_key(arm, value)
        parsed_arm, _, parsed_value = rec.parse_point_key(key)
        assert parsed_arm == arm
        assert rec.point_key(parsed_arm, parsed_value) == key
    assert rec.point_key("dp_n64", 0.5) == "dp_n64_sigma0p500000"
    assert sorted([rec.point_key("dp_n8", 0.5), rec.point_key("dp_n8", 0.05)]) == [
        "dp_n8_sigma0p050000",
        "dp_n8_sigma0p500000",
    ], "fixed width is what makes the string order the numeric order"
    # 24-REVIEW WR-01's class: refuse the PROPERTY, not the name.
    with pytest.raises(SystemExit):
        rec.point_key("adv_n8", -1.0)
    with pytest.raises(SystemExit):
        rec.point_key("adv_n8", float("nan"))
    with pytest.raises(SystemExit):
        rec.point_key("never-taught", 0.0)


def test_ordered_point_keys_refuses_at_call_time_not_at_import():
    """The wave-2..4 survival property: `SIGMA_LADDER` arrives in plan 25-12 (wave 5)."""
    if hasattr(mitigation_budget, "SIGMA_LADDER"):
        keys = rec.ORDERED_POINT_KEYS()
        assert len(keys) == 44 and len(set(keys)) == 44
        return
    with pytest.raises(SystemExit) as excinfo:
        rec.ORDERED_POINT_KEYS()
    assert "25-12" in str(excinfo.value)
    # And nothing resolves it at import or at default-argument time.
    tree = ast.parse(_RECORD_SOURCE.read_text(encoding="utf-8"))
    eager = [
        node.lineno
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(call, ast.Call) and getattr(call.func, "id", None) == "ORDERED_POINT_KEYS"
            for call in ast.walk(node)
        )
    ]
    eager += [
        function.lineno
        for function in ast.walk(tree)
        if isinstance(function, ast.FunctionDef)
        for default in function.args.defaults
        if any(
            isinstance(call, ast.Call) and getattr(call.func, "id", None) == "ORDERED_POINT_KEYS"
            for call in ast.walk(default)
        )
    ]
    assert eager == [], eager


def test_the_write_path_is_atomic(tmp_path, monkeypatch, control_record):
    """tmp + fsync + os.replace, with BOTH per-point refusals in front of it.

    The serialisation runs BEFORE the temporary file is opened, so a record carrying a
    non-serialisable value leaves NO file rather than a truncated one — and a truncated per-point
    record is indistinguishable from a point that ran and produced a short reading.
    """
    destination = tmp_path / "phase25_point_dp_n8_sigma0p000000.json"
    monkeypatch.setattr(rec, "point_record_path", lambda key: destination)

    # D-10's one attempt: a TRACKED record refuses before anything is opened.
    with pytest.raises(SystemExit):
        rec.write_point_record(
            control_record,
            point_key_value="dp_n8_sigma0p000000",
            tracked=[prereg.point_record_path("dp_n8_sigma0p000000")],
        )
    assert list(tmp_path.iterdir()) == []

    # A non-serialisable value leaves NO file and NO temporary residue.
    with pytest.raises(TypeError):
        rec.write_point_record(
            dict(control_record, adapter_path=object()),
            point_key_value="dp_n8_sigma0p000000",
            tracked=[],
        )
    assert list(tmp_path.iterdir()) == []

    rec.write_point_record(control_record, point_key_value="dp_n8_sigma0p000000", tracked=[])
    assert destination.exists()
    assert [path.name for path in tmp_path.iterdir()] == [destination.name]
    assert destination.read_text(encoding="utf-8").endswith("\n")

    # refuse-to-rerun over the destination that now exists.
    with pytest.raises(SystemExit):
        rec.write_point_record(control_record, point_key_value="dp_n8_sigma0p000000", tracked=[])


def test_the_module_imports_neither_torch_nor_numpy():
    """Statically AND in a FRESH INTERPRETER — Phase 15's figure-guard register, retargeted.

    The static half catches the import; the dynamic half catches a TRANSITIVE one, which is the
    form that actually threatens this module (`phase14_recall`, `phase18_extraction` and
    `phase21_unit_record` all put torch in `sys.modules` on import, measured).
    """
    tree = ast.parse(_RECORD_SOURCE.read_text(encoding="utf-8"))
    modules = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "torch" not in modules and "numpy" not in modules, sorted(modules)

    probe = (
        "import sys;"
        f"sys.path.insert(0, {str(_ROOT / 'scripts')!r});"
        f"sys.path.insert(0, {str(_ROOT / 'src')!r});"
        "import phase25_record;"
        "print(int('torch' in sys.modules), int('numpy' in sys.modules))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, cwd=_ROOT, check=True
    )
    assert completed.stdout.split() == ["0", "0"], completed.stdout
