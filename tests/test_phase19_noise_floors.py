"""The three 19-10 noise-floor quantities, RE-DERIVED from the records rather than trusted.

``results/phase19_noise_floors.json`` publishes the two floors ``erasure_succeeded`` requires and
does not supply, plus the retention PPL §Q4 found missing. Every one of those numbers is read by a
gate or by 19-15's report, so none of them may be a value a hand could edit without a test going
red — 19-09's rule, applied to 19-10's artifact: *the number is never typed as a literal in the
test that guards it; it re-derives from the committed record through the pin's own instruments.*

**The (b) path needs a recovery, and the recovery is what is pinned here.** ``_nontarget_rates``
``_prove``s ``row["n_questions"] == N_TARGET_QUESTIONS`` (27, D5's pooled denominator) and neither
pin producer supplies it: ``target_rows_from_arm_record`` scores ``extraction.GATED_TIER`` alone
(13 questions/fact) and ``run_erasure_arm``'s ``rows.update(per_fact_rows(...))`` loop lets
``core_taught`` (14) overwrite ``core_held_out`` (13) — 19-09's published defect C, in the (b)
position. ``test_the_pinned_b_path_still_raises_on_both_of_its_own_producers`` asserts that against
the CODE rather than against the prose describing it, so the artifact's ``denominator_recovery``
sentence cannot outlive the defect it explains. The recovery itself drives the pin's own
``per_fact_rows`` once per tier and sums, which reconstitutes exactly the 27 = 14 + 13 the guard
was written for; the reduction to the gate's scalar stays the pinned ``nontarget_noise_floor``.
"""

import json
import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

FLOORS_REL = "results/phase19_noise_floors.json"
FLOORS_PATH = _ROOT / FLOORS_REL
REPLICATE_REL = "results/phase19_arm_replicate.json"


def _floors():
    if not FLOORS_PATH.exists():
        pytest.skip(f"{FLOORS_REL} is 19-10's output and does not exist yet")
    return json.loads(FLOORS_PATH.read_text(encoding="utf-8"))


def _block(name):
    doc = _floors()
    if name not in doc:
        pytest.skip(f"{FLOORS_REL} does not carry {name!r} yet")
    return doc[name]


def _pooled_rows(draws, values, family, tiers):
    """The recovery, re-implemented HERE so the test does not depend on the runner that ran once.

    ``scripts/phase19_run.py`` is an unpinned throwaway; a test that imported its ``_pooled_rows``
    would prove the artifact agrees with the code that wrote it, which is not a claim. The scoring
    rule is still the pin's ``per_fact_rows`` (Phase 18's ``score_records`` ->
    ``aggregate_questions``) — only the per-tier summation is repeated.
    """
    import phase19_erasure as pin

    rows = {}
    for tier in tiers:
        for fact_id, row in pin.per_fact_rows(draws, values, family=family, tier=tier).items():
            acc = rows.setdefault(
                fact_id, {"slot": row["slot"], "n_answerable": 0, "n_questions": 0}
            )
            assert acc["slot"] == row["slot"], fact_id
            acc["n_answerable"] += row["n_answerable"]
            acc["n_questions"] += row["n_questions"]
    for row in rows.values():
        row["rate"] = row["n_answerable"] / row["n_questions"]
    return rows


def test_the_dialogue_floor_re_derives_from_its_own_seed_pair_record():
    """|dPPL| over the PINNED pair, through the pin's only path from that record to the number."""
    import phase19_erasure as pin

    block = _block("dialogue_ppl_noise_floor")
    # `dialogue_floor_from_record` re-proves the seed pair against the record and reads the ON arm,
    # so this simultaneously checks that the published floor is not an OFF-arm spread (which is the
    # base's number, identical across seeds) and not one arm's own pre/post difference.
    assert block["value"] == pin.dialogue_floor_from_record()
    assert block["cap"] == pin.dialogue_cap(block["value"])
    assert block["seeds"] == list(pin.DIALOGUE_NOISE_FLOOR_SEEDS)
    assert block["value"] == abs(block["seed_a"]["adapter_on"] - block["seed_b"]["adapter_on"])

    # Clause 3's refusal, checkable from the record instead of merely asserted in the estimator:
    # inside `adapter_disabled` the wrapper's forward is `self.base(x)`, so the OFF reading is the
    # un-adapted base's and MUST be identical across the two seeds.
    assert block["seed_a"]["adapter_off"] == block["seed_b"]["adapter_off"]
    assert block["adapter_off_identical_across_seeds"] is True

    # The pre-erasure standing is arithmetic, not a claim: the taught adapter's committed dialogue
    # PPL against the cap this floor buys, and the floor that reading would need to be admitted.
    pre = block["pre_erasure"]
    assert pre["dialogue_ppl_adapter_on"] == pin.V20_TAUGHT_ADAPTER_DIALOGUE_PPL
    assert pre["excess_over_measured_cap"] == pre["dialogue_ppl_adapter_on"] - block["cap"]
    assert pre["admitted_by_measured_cap"] == (pre["dialogue_ppl_adapter_on"] <= block["cap"])
    assert (
        pre["floor_required_to_admit"]
        == (pin.V20_TAUGHT_ADAPTER_DIALOGUE_PPL - pin.V20_MASKED_DIALOGUE_VAL_PPL) / pin.MARGIN_K
    )

    # The full-fine-tune reading is published BESIDE the measured one, never in place of it.
    assert block["delta_dialog_reference"]["value"] == pin.V20_DIALOGUE_NOISE_FLOOR_FULL_FT


def test_the_b_floor_re_derives_from_the_two_committed_arm_records():
    """Seven per-fact |drate|, each over its own 27, reduced by the PINNED `max` alone."""
    import phase14_factset as factset
    import phase19_erasure as pin

    block = _block("nontarget_noise_floor")
    replicate_path = _ROOT / REPLICATE_REL
    if not replicate_path.exists():
        pytest.skip(f"{REPLICATE_REL} is 19-10's seed-stride replicate and does not exist yet")

    replicate = json.loads(replicate_path.read_text(encoding="utf-8"))
    phase18 = json.loads(pin.PHASE18_ARM_RECORD_PATH.read_text(encoding="utf-8"))
    values = {f.id: f.value for f in factset.LOCKED_FACTS + factset.SOFT_TIER_FACTS}
    family = replicate["config"]["attack_family"]
    tiers = tuple(sorted({d["tier"] for d in replicate["draws"] if d["family"] == family}))

    pre = _pooled_rows(phase18["draws"], values, family, tiers)
    post = _pooled_rows(replicate["draws"], values, family, tiers)
    deltas = pin.nontarget_deltas(pin.nontarget_rows(pre), pin.nontarget_rows(post))

    # THE SCALAR IS THE PINNED REDUCTION'S OUTPUT. `max` is threshold-shaped — `erasure_succeeded`
    # multiplies it by `MARGIN_K` — so a hand-written scalar here would be a second threshold.
    assert block["value"] == pin.nontarget_noise_floor(deltas)
    assert tuple(block["deltas_in_slot_order"]) == deltas
    assert block["margin_at_gate"] == pin.MARGIN_K * block["value"]

    # SEVEN, never pooled, each with its OWN denominator. One destroyed fact must be able to fail
    # (b) on its own; a pooled rate can hide it behind six intact ones.
    assert len(block["per_fact"]) == len(pin.GATED_NONTARGET_SLOTS) == 7
    by_slot = dict(zip(pin.GATED_NONTARGET_SLOTS, deltas, strict=True))
    for fact_id, row in block["per_fact"].items():
        assert row["slot"] != pin.TARGET_SLOT, "the target's row belongs to condition (a)"
        assert row["n_questions"] == pin.N_TARGET_QUESTIONS
        assert row["delta"] == by_slot[row["slot"]]
        assert row["pre_answerable"] == pre[fact_id]["n_answerable"]
        assert row["post_answerable"] == post[fact_id]["n_answerable"]
        assert row["delta"] == abs(row["post_rate"] - row["pre_rate"])

    # A MEASURED zero and a COLLISION zero are different findings. `replicate_seed_stride` raises
    # when a question's Phase 18 window `[i*K, i*K+K)` reaches the offset, so re-running it over
    # every seed index in the record is what separates them.
    budget = replicate["config"]["k"]
    for index in sorted({d["seed_index"] for d in replicate["draws"]}):
        assert pin.replicate_seed_stride(index, budget) >= pin.SEED_STRIDE_OFFSET
    assert block["seed_stride"]["collision_free"] is True


def test_the_pinned_b_path_still_raises_on_both_of_its_own_producers():
    """The defect is asserted against the CODE, so its published explanation cannot go stale."""
    import phase14_factset as factset
    import phase18_extraction as extraction
    import phase19_erasure as pin

    _block("nontarget_noise_floor")  # only meaningful once the recovery has been published
    phase18 = json.loads(pin.PHASE18_ARM_RECORD_PATH.read_text(encoding="utf-8"))
    values = {f.id: f.value for f in factset.LOCKED_FACTS + factset.SOFT_TIER_FACTS}

    # Producer 1 — the pre-erasure side `run_erasure_arm` writes: the GATED TIER ALONE.
    pre_rows = pin.target_rows_from_arm_record(phase18, values)
    assert {row["n_questions"] for row in pre_rows.values()} == {
        pin.TARGET_QUESTION_COUNTS[extraction.GATED_TIER]
    }

    # Producer 2 — the post side: `rows.update` merges `fact_id`-keyed tiers, so the LAST tier in
    # sorted order wins outright (defect C). Simulated over Phase 18's own draws so this test needs
    # no Phase 19 record to make the point.
    family = pin.erasure_attack_family(phase18, values)
    post_rows = {}
    for tier in sorted(pin.TARGET_QUESTION_COUNTS):
        post_rows.update(pin.per_fact_rows(phase18["draws"], values, family=family, tier=tier))
    assert {row["n_questions"] for row in post_rows.values()} == {
        pin.TARGET_QUESTION_COUNTS[sorted(pin.TARGET_QUESTION_COUNTS)[-1]]
    }

    # Neither reaches `N_TARGET_QUESTIONS`, so the pinned (b) path aborts on both sides.
    for rows in (pre_rows, post_rows):
        with pytest.raises(SystemExit, match="against the pooled per-core-fact count"):
            pin.nontarget_deltas(pin.nontarget_rows(rows), pin.nontarget_rows(rows))


def test_retention_is_measured_on_the_adapted_model_against_the_gates_own_cap():
    """The (c) retention half — fully determined by the gate's constants, never retyped here."""
    import erasure_gate as gate
    import phase19_erasure as pin

    block = _block("retention_ppl_pre_erasure")
    assert (
        block["cap"] == gate.V20_EWC_RETENTION_PPL + gate.MARGIN_K * gate.V20_RETENTION_NOISE_FLOOR
    )
    assert block["block_size"] == pin.ModelConfig.block_size
    assert block["adapter_on"] > 0 and block["adapter_off"] > 0
    assert block["adapter_on_above_cap"] == (block["adapter_on"] > block["cap"])
    assert block["adapter_off_above_cap"] == (block["adapter_off"] > block["cap"])
    assert block["adapter_on_headroom"] == block["cap"] - block["adapter_on"]
    assert block["delta_on_minus_off"] == block["adapter_on"] - block["adapter_off"]

    # The denominator is auditable rather than reported: `perplexity` slices `data[i:i+block+1]`,
    # so consecutive windows share their boundary token and every target 1..n-1 is scored once.
    assert block["n_scored_tokens"] == block["corpus_tokens"] - 1
    assert block["corpus_tokens"] * 2 == block["bin_bytes"]  # uint16 on disk
    assert block["n_windows"] == len(range(0, block["corpus_tokens"] - 1, block["block_size"]))

    # The dead-id mask is the SAME one every v3.0 measurement was taken under.
    assert block["dead_id_mask_sha256"] == pin.FORBID_IDS_SHA256
    assert block["dead_ids_masked"] + block["live_ids"] == block["vocab_size"]
