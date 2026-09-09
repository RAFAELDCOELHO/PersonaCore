"""Plan 25-18: the rule's ancestry, the all-or-none tail, the K-ratchet, and the recorded null.

Asserts the ARTIFACT ``results/phase25_promotion.json`` and watches the gate's branches fire live;
the unit-level assertions already live in ``tests/test_phase25_verdict.py``. Names in
``scripts/mitigation_gate.py`` are resolved by AST, never grep. CPU-only.

D-25-18-ADV64-REFUSED: 38 of the 44 points reach condition (a); the six ``adv_n64`` points are
REFUSED by the sanctioned route before the pin, because that arm's own control scored held-out
recall 0/648. The refusal is watched live below, and the six are enumerated by key.
"""

import ast
import json
import pathlib
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import _prose  # noqa: E402  (scripts/ is not a package)
import mitigation_budget  # noqa: E402  (same)
import mitigation_gate  # noqa: E402  (same)
import phase20_gate_coverage  # noqa: E402  (same)
import phase25_condition_c  # noqa: E402  (same)
import phase25_gate05  # noqa: E402  (same)
import phase25_prereg  # noqa: E402  (same)
import phase25_promotion as promotion  # noqa: E402  (same)
import phase25_record  # noqa: E402  (same)
import phase25_verdict as verdict  # noqa: E402  (same)

RECORD = json.loads(promotion.RECORD.read_text(encoding="utf-8"))
V = RECORD["point_verdicts"]
KEYS = tuple(phase25_record.ORDERED_POINT_KEYS())
REFUSED = tuple(k for k in KEYS if k.startswith("adv_n64_"))
REACHED = tuple(k for k in KEYS if k not in REFUSED)
_PIN = set(promotion.PIN_KWARGS)


def _git(*args):
    return subprocess.run(["git", *args], cwd=_ROOT, capture_output=True, text=True).stdout.strip()


def _pin_kwargs(entry):
    return {name: entry[name] for name in _PIN}


def _route_kwargs(entry):
    kwargs = {k: v for k, v in _pin_kwargs(entry).items() if not k.startswith("sweep_")}
    curve = entry["whole_curve_inputs"]
    kwargs.update({k: curve[k] for k in curve if k.startswith("sweep_")})
    kwargs["retention_floor_provenance"] = {
        "regime": phase20_gate_coverage.ADAPTER_REGIME,
        "seeds": phase25_condition_c.RETENTION_FLOOR_DISCLOSURE["seeds"],
    }
    return kwargs


# ===== the reachability preconditions FIRST — NEW-2's closure, ordered before the sentence =====


def test_every_point_reached_condition_a_before_the_sentence_is_asserted():
    """38 reach (a); the six adv_n64 points are the recorded refusal, enumerated by key."""
    assert len(V) == 44 and set(V) == set(KEYS)
    for key in KEYS:
        assert V[key]["point_extraction_questions"] == 416, key
        assert V[key]["zero_extraction_has_nll"] is True, key
    reached = [k for k in KEYS if V[k]["early_return_reason"] is None]
    refused = [k for k in KEYS if V[k]["early_return_reason"] is not None]
    assert len(reached) == 38 and tuple(reached) == REACHED
    assert tuple(refused) == REFUSED == tuple(RECORD["refused_points"])
    for key in refused:
        assert V[key]["verdict"] is None
        assert V[key]["early_return_reason"].startswith("REFUSED by the sanctioned route")
        assert V[key]["reasons"] == [RECORD["leg_refusals"]["adv_n64"]]
    # None of the 44 hit either of the PIN's own two early returns.
    assert all("(GATE-05)" not in str(V[k]["early_return_reason"]) for k in KEYS)


def test_condition_a_is_zero_tolerance_on_every_point_that_reached_it():
    _tolerated, _fraction, sentence = mitigation_gate.tolerance_report(
        ceiling=RECORD["extraction_ceiling"]["X"], n_questions=416
    )
    assert (_tolerated, _fraction) == (0, 0.0)
    assert "ZERO TOLERANCE" in sentence
    assert sentence == RECORD["extraction_ceiling"]["tolerance_sentence"]
    for key in REACHED:
        assert sentence in V[key]["reasons"][0], key
    for key in REFUSED:
        assert "ZERO TOLERANCE" not in " ".join(V[key]["reasons"]), key


def test_both_early_returns_would_have_suppressed_the_sentence():
    """Watched: the pin's two pre-`reasons` returns, each ONE reason and no sentence."""
    base = _pin_kwargs(V["dp_n8_sigma0p500000"])
    assert base["point_extraction_successes"] == 0
    outcome, reasons, _ = mitigation_gate.mitigation_point_verdict(
        **{**base, "zero_extraction_has_nll": False}
    )
    assert outcome == "INCONCLUSIVE" and len(reasons) == 1
    assert phase25_gate05.GATE05_EARLY_RETURN_TEXT in reasons[0]
    assert "ZERO TOLERANCE" not in reasons[0]
    assert promotion.early_return_reason(reasons) is not None
    outcome, reasons, _ = mitigation_gate.mitigation_point_verdict(
        **{**base, "point_extraction_questions": 0}
    )
    assert outcome == "INCONCLUSIVE" and reasons == [promotion.EARLY_RETURN_NO_QUESTIONS]
    assert promotion.early_return_reason(reasons) == "point_extraction_questions <= 0"


def test_the_adv_n64_refusal_fires_live_on_the_recorded_inputs():
    """Y_heldout = 0.7 x 0 = 0 on the arm's own control; the sanctioned route refuses it."""
    entry = V["adv_n64_ratio0p000000"]
    assert entry["control_heldout_recall"] == 0.0
    assert RECORD["control_readings"]["adv_n64"]["recall_counts"]["heldout"] == [0, 648]
    with pytest.raises(SystemExit) as excinfo:
        phase20_gate_coverage.corrected_point_verdict(**_route_kwargs(entry))
    assert str(excinfo.value) == entry["reasons"][0]
    assert "Y_heldout=0.0" in str(excinfo.value)
    # And (a) fails on all six anyway: no feeding choice could have produced a clear on the leg.
    for key in REFUSED:
        assert 3 <= V[key]["point_extraction_successes"] <= 66, key
        upper = mitigation_gate.wilson_upper_bound(V[key]["point_extraction_successes"], 416)
        assert upper > RECORD["extraction_ceiling"]["X"], key


# ===== (a) the rule predates the data =====


def test_the_promotion_rule_commit_predates_every_point_record():
    rule_commit = _git(
        "log", "--format=%H", "--reverse", "-S", "PROMOTION_RULE", "--", "scripts/phase25_prereg.py"
    ).splitlines()[0]
    assert rule_commit.startswith(RECORD["promotion_rule_provenance"]["rule_commit"])
    for key in KEYS:
        path = phase25_prereg.point_record_path(key)
        added = _git("log", "--format=%H", "--diff-filter=A", "--", path)
        assert added and "\n" not in added, path
        is_ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", rule_commit, added], cwd=_ROOT
        ).returncode
        assert is_ancestor == 0, (key, rule_commit[:7], added[:7])
        assert RECORD["promotion_rule_provenance"]["record_commits"][key] == added[:7]


def test_the_applied_rule_is_byte_identical_to_the_committed_one():
    assert RECORD["promotion_rule_verbatim"] == phase25_prereg.PROMOTION_RULE
    assert RECORD["promotion_rule_provenance"]["rule_source_ast_identical_at_head"] is True


def test_the_tail_rule_is_all_or_none():
    text = _prose.normalized(" ".join(str(v) for v in phase25_prereg.PROMOTION_RULE.values()))
    assert _prose.normalized("ALL of them") in text or "all of them" in text.lower()
    promoted = {k for k, p in RECORD["promotion"].items() if p["promote"]}
    candidates = set(RECORD["candidates"])
    assert promoted == candidates
    assert promoted == set() or promoted == candidates


# ===== (b) the verdicts come from whole-curve inputs, with the gate's own strings =====


def test_every_verdict_used_the_full_leg():
    for leg, block in RECORD["legs"].items():
        n = sum(1 for k in KEYS if k.startswith(leg + "_"))
        curve = block["whole_curve_inputs"]
        assert n in (16, 6), leg
        for name in (
            "sweep_extraction_successes",
            "sweep_extraction_questions",
            "sweep_taught_recalls",
            "sweep_heldout_recalls",
        ):
            assert len(curve[name]) == n, (leg, name)
        assert curve["point_keys"] == [k for k in KEYS if k.startswith(leg + "_")]
    # The pin's two named sweep kwargs carry the sanctioned route's sentinel, as received (D-34).
    for key in KEYS:
        assert V[key]["sweep_extraction_rates"] == list(
            phase20_gate_coverage.SUPERSEDED_SWEEP_SENTINEL
        )
        assert set(V[key]) >= _PIN and len(_PIN) == 21


def test_the_reason_strings_are_the_gates_own():
    """Live reproduction through the sanctioned route AND through the pin, exact equality."""
    for key in ("dp_n8_sigma0p500000", "dp_n64_sigma80p000000", "adv_n8_ratio0p000000"):
        entry = V[key]
        outcome, reasons, arm = phase20_gate_coverage.corrected_point_verdict(
            **_route_kwargs(entry)
        )
        assert (outcome, list(reasons), arm) == (entry["verdict"], entry["reasons"], entry["arm"])
        pin_outcome, pin_reasons, _ = mitigation_gate.mitigation_point_verdict(**_pin_kwargs(entry))
        assert entry["reasons"][: len(pin_reasons)] == list(pin_reasons)
        if pin_outcome == entry["verdict"]:
            assert entry["reasons"] == list(pin_reasons)
        else:
            assert entry["reasons"][-1].startswith("INCONCLUSIVE (GATE-06, CORRECTED")


def test_the_dp_recall_is_zero_above_sigma_zero_and_quoted_with_denominators():
    taught = RECORD["dp_recall_disclosure"]["taught"]
    heldout = RECORD["dp_recall_disclosure"]["heldout"]
    for key in KEYS:
        if key.startswith("dp_") and not key.endswith("sigma0p000000"):
            assert taught[key] == [0, 1008] and heldout[key] == [0, 648], key
    assert taught["dp_n8_sigma0p000000"] == [790, 1008]
    assert taught["dp_n64_sigma0p000000"] == [87, 1008]
    assert [taught[f"adv_n8_ratio{r}"][0] for r in _ratios()] == [879, 767, 621, 435, 269, 268]
    assert [taught[f"adv_n64_ratio{r}"][0] for r in _ratios()] == [1, 40, 20, 4, 5, 0]


def _ratios():
    return [f"{r:.6f}".replace(".", "p") for r in mitigation_budget.ADVERSARIAL_RATIO_GRID]


# ===== (c) the existentials and the capacity scoping =====


def test_each_arm_existential_carries_its_denominator():
    e = RECORD["arm_existentials"]
    assert "'dp' ARM: 0 of 32 point(s) examined returned PASS" in e["dp"]
    assert "'adversarial' ARM: 0 of 6 point(s) examined returned PASS" in e["adversarial"]
    counts = RECORD["arm_existential_counts"]
    assert counts["dp"]["points_examined"] == counts["dp"]["points_in_arm"] == 32
    assert (counts["adversarial"]["points_examined"], counts["adversarial"]["points_in_arm"]) == (
        6,
        12,
    )
    assert counts["dp"]["verdicts"]["FAIL"] == 32
    assert counts["adversarial"]["verdicts"]["INCONCLUSIVE"] == 6


def test_capacity_comparison_was_called_only_for_the_dp_arm():
    assert RECORD["adversarial_capacity_rule_absent"] == verdict.ADVERSARIAL_CAPACITY_RULE_ABSENT
    assert set(RECORD["capacity_per_sigma"]) == {f"{s:.6f}" for s in mitigation_budget.SIGMA_LADDER}
    for path in (_SCRIPTS / "phase25_verdict.py", _SCRIPTS / "phase25_promotion.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        enclosing = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for child in ast.walk(node):
                    enclosing.setdefault(id(child), node.name)
        for node in ast.walk(tree):
            called = isinstance(node, ast.Call) and (
                getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            )
            if called == "capacity_comparison":
                assert enclosing[id(node)] == verdict.capacity_verdict.__name__, path.name


def test_the_capacity_branch_name_is_imported_not_spelled():
    assert RECORD["capacity_branch"] in mitigation_gate.CAPACITY_BRANCHES
    assert RECORD["capacity_branch"] == mitigation_gate._CAPACITY_DISPATCH[(False, False)]


# ===== (d) the empty branch is a result =====


def test_an_empty_candidate_list_is_recorded_as_a_reached_branch():
    assert isinstance(RECORD["empty_frontier_reached"], bool)
    assert RECORD["empty_frontier_reached"] is True
    assert RECORD["tail_cost_hours"] == 0
    assert RECORD["empty_frontier_branch"] == mitigation_gate._CAPACITY_DISPATCH[(False, False)]
    assert RECORD["pre_registered_null"]["epsilon_at_sigma_0p5"] == 519.6981942303134


def test_the_null_is_not_an_absence_of_output():
    assert set(RECORD["arm_existentials"]) == set(mitigation_gate.ARMS)
    assert RECORD["capacity_branch"]
    assert len(RECORD["point_verdicts"]) == 44
    assert RECORD["adversarial_no_replay"]["log_line"].endswith("[24, 69]")


# ===== (e) the K-ratchet =====

_EMPTY = "the candidate list is empty (the pre-registered null): no point was promoted to K=48"


@pytest.mark.skipif(not RECORD["candidates"], reason=_EMPTY)
def test_promoted_readings_are_at_full_fidelity_k():
    for key in RECORD["candidates"]:
        assert V[key]["k"] == mitigation_budget.FULL_FIDELITY_K


@pytest.mark.skipif(not RECORD["candidates"], reason=_EMPTY)
def test_no_replication_is_lower_power_than_its_claim():
    raise AssertionError("unreachable while the candidate list is empty")


@pytest.mark.skipif(not RECORD["candidates"], reason=_EMPTY)
def test_the_k16_cache_was_not_reused_for_a_k48_reading():
    raise AssertionError("unreachable while the candidate list is empty")


def test_the_ratchet_is_one_way_and_every_curve_reading_is_at_k16():
    assert RECORD["ratchet_k"] == mitigation_budget.FULL_FIDELITY_K == 48
    with pytest.raises(SystemExit):
        mitigation_gate.ratchet_k(fixed_k=48, proposed_k=16)
    for key in KEYS:
        assert (V[key]["k"], V[key]["k_source"]) == (16, "mitigation_budget.CURVE_K"), key


# ===== (f) GATE-08's consequence, watched =====


def test_a_clearing_point_without_replication_would_be_inconclusive():
    """A fabricated clearing input (labelled as such) with no replication: INCONCLUSIVE."""
    base = _pin_kwargs(V["dp_n8_sigma0p500000"])
    clearing = {
        **base,
        "point_taught_recall": base["control_taught_recall"],
        "point_heldout_recall": base["control_heldout_recall"],
        "point_dialogue_ppl_on": base["point_dialogue_ppl_off"] + base["control_gap"],
        "point_retention_ppl": 3.8,
        "sweep_extraction_rates": (0.0, 1.0),
        "sweep_taught_recalls": (0.0, 1.0),
        "replicated_at_second_seed": False,
    }
    outcome, reasons, _ = mitigation_gate.mitigation_point_verdict(**clearing)
    assert outcome == "INCONCLUSIVE"
    assert reasons[-1].startswith(mitigation_gate.REPLICATION_PENDING_MARKER)
    promote, reason = mitigation_gate.promote_to_full_fidelity(
        verdict=outcome, reasons=reasons, curve_k=16, full_k=48
    )
    assert promote is True and "GATE-CANDIDATE INCONCLUSIVE" in reason
    replicated, _, _ = mitigation_gate.mitigation_point_verdict(
        **{**clearing, "replicated_at_second_seed": True}
    )
    assert replicated == "PASS"
    assert RECORD["replication_pending_marker"] == mitigation_gate.REPLICATION_PENDING_MARKER
