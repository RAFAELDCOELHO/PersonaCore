"""Plan 25-19: the assembled frontier artifact — ordering, re-derivation, counts-never-rates.

Asserts the ARTIFACT ``results/phase25_frontier.json`` over its committed bytes: the ordered-key
hard equality against ``phase25_record.ORDERED_POINT_KEYS()``, D-36's held-out re-derivation with
its RED watched on a perturbed copy in ``tmp_path``, the dual multiplicity with the frozen pin's
``RECORDED, NOT RESOLVED`` status carried through, the curve total re-deriving from its summands,
and FRONT-04's verdict surface. The per-point and verdict-level assertions already live in
``tests/test_phase25_record.py`` and ``tests/test_phase25_promotion.py``; this file asserts what
only the ASSEMBLED artifact can show. Names in the frozen gate are read through the imported
module, never grep. The 22 MB artifact is loaded ONCE into a module fixture. CPU-only.
"""

import hashlib
import json
import math
import pathlib
import re
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
import mitigation_unit  # noqa: E402  (same)
import phase20_gate_coverage  # noqa: E402  (same)
import phase25_condition_c  # noqa: E402  (same)
import phase25_epsilon  # noqa: E402  (same)
import phase25_prereg  # noqa: E402  (same)
import phase25_record as record  # noqa: E402  (same)

KEYS = tuple(record.ORDERED_POINT_KEYS())
DP_KEYS = tuple(k for k in KEYS if k.startswith("dp_"))
ADV_KEYS = tuple(k for k in KEYS if k.startswith("adv_"))
REFUSED = tuple(k for k in KEYS if k.startswith("adv_n64_"))

# a key whose name says "rate" (as a whole `_`-separated token — `tolerated` is a COUNT, and a
# substring match on it is the false-RED class RPT-02 closes) must sit beside the two counts it
# was computed from. The one sanctioned exception is the pin's two SUPERSEDED sweep kwargs, which
# are not readings at all but `phase20_gate_coverage.SUPERSEDED_SWEEP_SENTINEL` recorded as the
# pin received them, with the real leg-length COUNT sequences beside them under
# `whole_curve_inputs`.
_RATE_SIBLINGS = (
    {"numerator", "denominator"},
    {"k", "n_draws"},
    {"n_draws", "minutes"},
    {"nontarget_successes", "nontarget_questions"},
)
_SENTINEL = list(phase20_gate_coverage.SUPERSEDED_SWEEP_SENTINEL)


def _is_rate_key(key):
    return bool({"rate", "rates"} & set(key.lower().split("_")))


@pytest.fixture(scope="module")
def artifact():
    return json.loads(record.FRONTIER_RECORD.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def promotion():
    return json.loads(record.PROMOTION_RECORD.read_text(encoding="utf-8"))


def _git(*args):
    return subprocess.run(["git", *args], cwd=_ROOT, capture_output=True, text=True).stdout


# ===== (a) ordering and completeness =====


def test_point_keys_equal_the_ordered_pin_exactly(artifact):
    assert tuple(artifact["point_keys"]) == KEYS
    # the file's own insertion order IS the pin's order, not merely its membership
    assert tuple(artifact["points"]) == KEYS


def test_every_point_key_has_a_record_and_vice_versa(artifact):
    assert set(artifact["point_keys"]) == set(artifact["points"])
    for key, point in artifact["points"].items():
        assert point["point_key"] == key
        assert point["record"] == f"results/phase25_point_{key}.json"


def test_there_are_no_duplicate_keys(artifact):
    keys = artifact["point_keys"]
    assert len(keys) == len(set(keys)) == 44


# ===== (b) D-36's re-derivation, with its natural RED =====


def test_held_out_generalization_re_derives_exactly(artifact):
    block = artifact["held_out_generalization"]
    family = block["held_out_family"]
    for name in ("successes", "questions", "draws"):
        assert block[name] == sum(
            p["per_family_counts"][family][name] for p in artifact["points"].values()
        )
    assert block["points"] == 44 and block["questions"] == 44 * 104
    assert record.prove_held_out_generalization(artifact) is True


def test_a_perturbed_per_point_count_breaks_the_aggregate(artifact, tmp_path):
    """Perturb ONE per-point count on a COPY in tmp_path; the re-derivation must refuse it."""
    copy = tmp_path / "phase25_frontier.json"
    copy.write_text(json.dumps(artifact), encoding="utf-8")
    perturbed = json.loads(copy.read_text(encoding="utf-8"))
    family = perturbed["held_out_generalization"]["held_out_family"]
    perturbed["points"][KEYS[0]]["per_family_counts"][family]["successes"] += 1
    with pytest.raises(SystemExit) as refusal:
        record.prove_held_out_generalization(perturbed)
    message = str(refusal.value)
    assert "held_out_generalization.successes" in message and "does NOT re-derive" in message
    assert str(artifact["held_out_generalization"]["successes"] + 1) in message
    assert _git("status", "--porcelain", "results/") == ""


def test_the_held_out_family_is_read_from_the_module(artifact):
    import phase24_adversarial  # the real module (imports torch); where the two seconds belong

    block = artifact["held_out_generalization"]
    assert block["held_out_family"] == phase24_adversarial.HELD_OUT_FAMILY
    assert tuple(block["trained_families"]) == tuple(phase24_adversarial.TRAINED_FAMILIES)


# ===== (c) counts, never rates =====


def _rate_leaves_without_counts(node, path=""):
    bad = []
    if isinstance(node, dict):
        keys = set(node)
        for k, v in node.items():
            sentinel = v == _SENTINEL and {
                "sweep_extraction_successes",
                "sweep_extraction_questions",
            } <= set(node.get("whole_curve_inputs", {}))
            if _is_rate_key(k) and not sentinel and not any(s <= keys for s in _RATE_SIBLINGS):
                bad.append(f"{path}/{k}")
            bad.extend(_rate_leaves_without_counts(v, f"{path}/{k}"))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            bad.extend(_rate_leaves_without_counts(v, f"{path}[{i}]"))
    return bad


def test_no_rate_appears_without_its_numerator_and_denominator(artifact):
    assert _rate_leaves_without_counts(artifact) == []
    # the only rate-named leaves without count siblings are the pin's two superseded sweep kwargs,
    # and every one of them IS the sentinel, never a measured sequence
    for key, point in artifact["points"].items():
        entry = point["verdict"]
        assert entry["sweep_extraction_rates"] == _SENTINEL, key
        assert entry["sweep_taught_recalls"] == _SENTINEL, key
        curve = entry["whole_curve_inputs"]
        assert len(curve["sweep_extraction_successes"]) == len(curve["point_keys"]), key


def test_per_question_rows_are_inline_for_all_44(artifact):
    for key, point in artifact["points"].items():
        rows = point["per_question"]
        assert len(rows[record.GATED_TIER]) == 416, key
        assert len(rows[record.REPORTED_TIER]) == 448, key
        assert all({"successes", "draws"} <= set(row) for row in rows[record.GATED_TIER]), key


def _epsilon_bearing_dicts(node, path=""):
    if isinstance(node, dict):
        if any(k in phase25_epsilon.EPSILON_NAMES for k in node):
            yield path, node
        for k, v in node.items():
            yield from _epsilon_bearing_dicts(v, f"{path}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _epsilon_bearing_dicts(v, f"{path}[{i}]")


def test_every_epsilon_bearing_reading_carries_its_k_inline(artifact):
    seen = 0
    for path, node in _epsilon_bearing_dicts(artifact):
        seen += 1
        assert node.get("draws_per_question") == mitigation_budget.CURVE_K, path
        assert node.get("draws_per_question_source") == "mitigation_budget.CURVE_K", path
    assert seen == 44 + 1  # the 44 points and the epsilon report


# ===== (d) the epsilon report =====


def test_both_multiplicities_are_named_and_neither_is_hidden(artifact):
    report = artifact["epsilon_report"]
    pin = json.loads(phase25_epsilon.MULTIPLICITY_RECORD.read_text())["pin_discrepancy"]
    mult = report["multiplicities"]
    assert mult["pin_figure"] == pin["pin_figure"] == 262.9437465865647
    assert mult["artifact_rule_figure"] == pin["artifact_rule_figure"] == 207.0180229382851
    assert mult["status"] == pin["status"]
    text = _prose.normalized(report["dual_granularity"])
    assert _prose.normalized("RECORDED, NOT RESOLVED") in text
    assert repr(pin["pin_figure"]) in text and repr(pin["artifact_rule_figure"]) in text
    assert mult["epsilon_computed"] is False


def test_the_curve_total_re_derives_from_its_summands(artifact):
    report = artifact["epsilon_report"]
    assert report["curve_total_epsilon"] == math.fsum(report["summands"])
    assert report["total_delta"] == len(report["summands"]) * mitigation_unit.DELTA
    assert report["k"] == len(report["summands"])
    for key, value in zip(report["summand_keys"], report["summands"]):
        point = artifact["points"][key]
        assert point["epsilon"] == value
        live = phase25_epsilon.point_epsilon_for_sigma(
            point["sigma"], steps=point["composed_steps"], delta=point["delta"]
        )
        # pin-or-recorded-twin, exact on both branches (LADDER_PLATFORM_TWINS): two rungs differ
        # by 4 ULP between the publication host's libm and glibc.
        assert phase25_epsilon.epsilon_agrees(value, live, sigma=point["sigma"]), (
            f"{key}: the artifact publishes {value!r}, the accountant returns {live!r}"
        )


def test_the_summands_are_the_published_noised_dp_points(artifact):
    report = artifact["epsilon_report"]
    noised = [k for k in DP_KEYS if artifact["points"][k]["epsilon"] is not None]
    controls = [k for k in DP_KEYS if artifact["points"][k]["epsilon"] is None]
    assert report["summand_keys"] == noised and len(noised) == 30
    assert report["control_points_excluded"] == controls
    assert controls == ["dp_n8_sigma0p000000", "dp_n64_sigma0p000000"]
    assert not set(controls) & set(report["summand_keys"])
    assert {leg["points"] for leg in report["legs_crossed"].values()} == {15}


def test_selection_accounted_is_false_with_its_reason(artifact):
    report = artifact["epsilon_report"]
    assert report["selection_accounted"] is False
    assert report["selection_accounted_reason"] == phase25_epsilon.SELECTION_ACCOUNTED_REASON
    assert report["total_crosses_both_legs"] is True
    assert report["total_crosses_both_legs_reason"] == phase25_epsilon.TOTAL_CROSSES_BOTH_LEGS


def test_the_control_publication_voids_any_joint_bound(artifact):
    report = artifact["epsilon_report"]
    assert report["no_joint_bound_over_all_published_artifacts"] is True
    assert _prose.normalized("NO JOINT BOUND OVER ALL PUBLISHED ARTIFACTS EXISTS") in (
        _prose.normalized(report["control_has_no_epsilon"])
    )
    for key in report["control_points_excluded"]:
        point = artifact["points"][key]
        assert point["epsilon"] is None
        assert point["epsilon_omitted_reason"] == phase25_epsilon.CONTROL_EPSILON_FIELD_FORM


def test_no_bare_epsilon_string_bypassed_the_helper(artifact):
    report = artifact["epsilon_report"]
    rendered = report["rendered"]
    assert set(rendered) == set(DP_KEYS)
    for key, text in rendered.items():
        assert text.startswith("AT THE PRIVACY UNIT"), key
        assert "selection_accounted = False" in text, key
        assert text == phase25_epsilon.report_epsilon(
            point_epsilon=artifact["points"][key]["epsilon"],
            curve_total_epsilon=report["curve_total_epsilon"],
            selection_accounted=phase25_epsilon.SELECTION_ACCOUNTED,
        )
    for key in ADV_KEYS:
        assert artifact["points"][key]["epsilon"] is None
        assert artifact["points"][key]["accounting"] is None


# ===== (e) FRONT-04's verdict surface =====


def test_the_capacity_branch_is_a_member_of_the_frozen_tuple(artifact):
    verdicts = artifact["verdicts"]
    assert verdicts["capacity_branch"] in mitigation_gate.CAPACITY_BRANCHES
    assert verdicts["capacity_branches"] == list(mitigation_gate.CAPACITY_BRANCHES)
    assert verdicts["capacity_branch"] == "null-at-both-capacities"


def test_both_arm_existentials_carry_their_denominators(artifact, promotion):
    verdicts = artifact["verdicts"]
    pattern = re.compile(r"0 of (\d+) point\(s\) examined returned PASS")
    for arm, examined, in_arm in (("dp", 32, 32), ("adversarial", 6, 12)):
        text = verdicts["arm_existentials"][arm]
        assert text == promotion["arm_existentials"][arm]
        assert int(pattern.search(text).group(1)) == examined
        counts = verdicts["arm_existential_counts"][arm]
        assert counts["points_examined"] == examined and counts["points_in_arm"] == in_arm
        assert counts["exists"] is False


def test_the_absent_adversarial_capacity_rule_is_stated_in_the_artifact(artifact, promotion):
    text = artifact["verdicts"]["adversarial_capacity_rule_absent"]
    assert text == promotion["adversarial_capacity_rule_absent"]
    assert _prose.normalized("NO COMMITTED ADVERSARIAL CAPACITY RULE") in _prose.normalized(text)
    assert artifact["verdicts"]["adversarial_no_replay"] == promotion["adversarial_no_replay"]
    for key in ADV_KEYS:
        assert artifact["points"][key]["recipe_disclosure"] == (
            record.ADVERSARIAL_NO_REPLAY_DISCLOSURE
        )


def test_every_verdict_reason_is_the_gates_own(artifact, promotion):
    for key in KEYS:
        assert artifact["points"][key]["verdict"] == promotion["point_verdicts"][key], key
        assert artifact["points"][key]["promotion"] == promotion["promotion"][key], key
    verdicts = artifact["verdicts"]
    assert verdicts["tallies"] == {"PASS": 0, "FAIL": 32, "INCONCLUSIVE": 6, "REFUSED": 6}
    assert tuple(verdicts["refused"]) == REFUSED == tuple(promotion["refused_points"])
    for key in REFUSED:
        entry = artifact["points"][key]["verdict"]
        assert entry["verdict"] is None
        assert entry["early_return_reason"].startswith("REFUSED by the sanctioned route")
        assert entry["reasons"] == [promotion["leg_refusals"]["adv_n64"]]
        assert verdicts["refused"][key]["reason"] == entry["reasons"]


def test_recall_is_fed_from_the_recall_artifact_pinned_to_the_adapter(artifact):
    recall = json.loads(record.RECALL_RECORD.read_text(encoding="utf-8"))["points"]
    sources = {"point_record": 0, "results/phase25_recall.json (D-25-18-RECALL)": 0}
    for key, point in artifact["points"].items():
        sources[point["recall_provenance"]["source"]] += 1
        assert recall[key]["adapter_sha256"] == point["adapter_sha256"]
        for name in record.RECALL_FIELDS:
            assert point[name] == recall[key][name], (key, name)
        if key.startswith("dp_") and point["sigma"] > 0:
            assert (point["taught_recall"]["numerator"], point["taught_recall"]["denominator"]) == (
                0,
                1008,
            )
            assert point["heldout_recall"]["numerator"] == 0
            assert point["heldout_recall"]["denominator"] == 648
    assert sources == {"point_record": 2, "results/phase25_recall.json (D-25-18-RECALL)": 42}


# ===== (e2) Area 7 in the published artifact =====


def test_every_point_carries_all_seven_area7_fields(artifact):
    need = set(phase25_condition_c.CONDITION_C_FIELDS)
    missing = {
        key: sorted(need - set(point["condition_c"]))
        for key, point in artifact["points"].items()
        if not need <= set(point["condition_c"]) or "zero_extraction_has_nll" not in point
    }
    assert missing == {}


def test_the_nll_flag_is_a_plain_bool_in_the_artifact(artifact):
    bad = [
        k for k, p in artifact["points"].items() if type(p["zero_extraction_has_nll"]) is not bool
    ]
    assert bad == []
    assert all(p["zero_extraction_has_nll"] is True for p in artifact["points"].values())


def test_both_perplexities_carry_their_denominators(artifact):
    for key, point in artifact["points"].items():
        group = point["condition_c"]
        assert type(group["dialogue_n_targets"]) is int and group["dialogue_n_targets"] > 0, key
        assert type(group["retention_total_tokens"]) is int, key
        assert group["retention_total_tokens"] > 0, key


def test_the_counterfactual_cap_re_derives_from_its_own_floor(artifact):
    for key, point in artifact["points"].items():
        group = point["condition_c"]
        cap = mitigation_gate.retention_cap(
            retention_noise_floor=group["counterfactual_retention_floor"]
        )
        assert cap == group["counterfactual_retention_cap"], key


def test_the_retention_pre_registration_is_published_inside_the_artifact(artifact):
    anchor = artifact["retention_leg_binds_at_anchor"]
    assert anchor == phase25_condition_c.RETENTION_LEG_BINDS_AT_ANCHOR
    for side in ("borrowed", "governing"):
        assert {"floor", "cap", "headroom", "admit_factor"} <= set(anchor[side])
        assert anchor[side]["headroom"] < 0
    assert anchor["governing"]["headroom"] < anchor["borrowed"]["headroom"]
    assert anchor["governing"]["cap"] < anchor["borrowed"]["cap"]
    for key, point in artifact["points"].items():
        assert point["retention_leg_binds_at_anchor"] == anchor, key


def test_the_dialogue_floor_recipe_mismatch_is_disclosed(artifact):
    mismatch = artifact["dialogue_floor_recipe_mismatch"]
    assert mismatch == phase25_condition_c.DIALOGUE_FLOOR_RECIPE_MISMATCH
    sensitivity = artifact["dialogue_floor_sensitivity"]
    assert sensitivity == json.loads(json.dumps(phase25_condition_c.DIALOGUE_FLOOR_SENSITIVITY))
    text = _prose.normalized(mismatch)
    assert _prose.normalized("1.65% of the band width") in text
    assert _prose.normalized("14.86% of it") in text
    assert "floor_share_of_band" in sensitivity and "ten_x_error_share_of_band" in sensitivity


# ===== (f) provenance and write-once =====


def test_both_module_digests_are_live(artifact):
    """Every recorded digest pins the module bytes AT THE WRITE, and the three frozen modules are
    still byte-identical in the working tree.

    CORRECTION 2026-09-09 (25-REVIEW WR-03, operator decision in 25-HUMAN-UAT item 2):
    `scripts/phase25_record.py` was corrected AFTER the write — the published `governs` sentence
    gave the adversarial lot formula for all 44 points, while the code was always per-arm. The
    emitter's digest therefore pins the bytes at `provenance.git_sha`, which is what it was ever
    evidence of; claiming it still matches the working tree would be false. The three
    ancestry-guarded modules are unaffected and are still asserted live, which is the stronger
    half of this test and the half that would catch a frozen-module edit.
    """
    provenance = artifact["provenance"]
    write_sha = provenance["git_sha"]
    modules = (
        ("gate_module_sha256", "mitigation_gate.py"),
        ("budget_module_sha256", "mitigation_budget.py"),
        ("unit_module_sha256", "mitigation_unit.py"),
        ("record_module_sha256", "phase25_record.py"),
    )

    drifted = {}
    for field, name in modules:
        at_write = subprocess.run(
            ["git", "show", f"{write_sha}:scripts/{name}"],
            capture_output=True,
            cwd=_ROOT,
            check=True,
        ).stdout
        digest = hashlib.sha256(at_write).hexdigest()
        if provenance[field] != digest:
            drifted[field] = (provenance[field], digest)
    assert drifted == {}, "a recorded digest does not pin the module bytes at the write"

    still_live = {}
    for field, name in modules[:3]:
        live = hashlib.sha256((_SCRIPTS / name).read_bytes()).hexdigest()
        if provenance[field] != live:
            still_live[field] = (provenance[field], live)
    assert still_live == {}, "a frozen module drifted from the bytes the artifact was written by"


def test_the_artifact_carries_the_pre_registered_commitments(artifact):
    provenance = artifact["provenance"]
    as_json = lambda value: json.loads(json.dumps(value))  # noqa: E731
    assert provenance["publication_obligation"] == as_json(phase25_prereg.PUBLICATION_OBLIGATION)
    assert provenance["canary_reservations"] == as_json(phase25_prereg.CANARY_RESERVATIONS)
    assert provenance["git_surface_exception"] == phase25_prereg.GIT_SURFACE_EXCEPTION
    for key, point in artifact["points"].items():
        assert provenance["inputs"]["point_records"][key]["sha256"] == (
            hashlib.sha256((_ROOT / point["record"]).read_bytes()).hexdigest()
        ), key


def test_a_second_assembly_is_refused():
    assert record.FRONTIER_RECORD.exists()
    with pytest.raises(SystemExit) as refusal:
        record.refuse_second_assembly()
    message = str(refusal.value)
    assert "REFUSING a second assembly" in message
    assert "DELETE results/phase25_frontier.json IN ITS OWN COMMIT" in message
    with pytest.raises(SystemExit):
        record.main()


def test_the_pathspec_covers_the_four_publication_paths(artifact):
    assert {"scripts", "src", "results", "artifacts"} <= set(record._PUBLICATION_PATHSPEC)
    assert artifact["provenance"]["publication_pathspec"] == list(record._PUBLICATION_PATHSPEC)


# ===== 25-REVIEW WR-03: the published sentence, pinned as superseded rather than re-emitted =====


def test_the_published_lot_sentence_is_pinned_as_superseded(artifact):
    """The artifact's `governs` is the SUPERSEDED wording, byte-identical to its own constant.

    WR-03: the published sentence gives the adversarial formula for all 44 points. The operator's
    decision (2026-09-09, 25-HUMAN-UAT item 2) was to record the discrepancy and correct the
    emitter for any future assembly, NOT to re-emit 22.3 MB of write-once bytes. This test pins
    both halves of that decision: the published bytes stay reachable under their own name, and the
    live constant is no longer the one the artifact carries. It goes RED on a silent re-emit.
    """
    published = artifact["mechanism_pin_disclosure"]["governs"]
    assert published == record.MECHANISM_PIN_DISCLOSURE_GOVERNS_AS_PUBLISHED
    assert published != record.MECHANISM_PIN_DISCLOSURE_GOVERNS


def test_the_corrected_sentence_states_the_rule_the_code_applies(artifact):
    """The corrected wording names BOTH arms' rules, and each matches `_lot_from_train_config`.

    The claim is checked against the code rather than against prose: a DP point's lot is
    `canary_population.n_facts`, an adversarial point's is `batch_size x max(1, grad_accum_steps)`,
    and the published sentence's single formula is wrong for the 32 DP points by exactly the
    factor the review measured.
    """
    corrected = _prose.normalized(record.MECHANISM_PIN_DISCLOSURE_GOVERNS)
    assert "n_facts" in corrected and "batch_size x max(1, grad_accum_steps)" in corrected

    dp = artifact["points"]["dp_n8_sigma0p000000"]
    cfg = dp["training"]["train_config"]
    assert record._lot_from_train_config(dp) == dp["canary_population"]["n_facts"]
    assert record._lot_from_train_config(dp) == dp["records_per_lot"]
    assert int(cfg["batch_size"]) * max(1, int(cfg["grad_accum_steps"])) != dp["records_per_lot"]

    adv = artifact["points"]["adv_n8_ratio0p000000"]
    adv_cfg = adv["training"]["train_config"]
    assert record._lot_from_train_config(adv) == int(adv_cfg["batch_size"]) * max(
        1, int(adv_cfg["grad_accum_steps"])
    )
    assert record._lot_from_train_config(adv) == adv["records_per_lot"]
