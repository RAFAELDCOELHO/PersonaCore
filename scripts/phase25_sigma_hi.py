"""PLAN 25-12 — D-18'S σ_hi ANCHOR PROBE. RECALL-ONLY, UNDER THE CALIBRATION PREFIX.

WHAT THIS MODULE MEASURES
-------------------------
ONE quantity: the TAUGHT RECALL of a DP adapter trained at a candidate high-anchor σ, at the
``C`` that will actually ship. D-18 requires the high anchor to be **PROBED, not presumed** — the
σ ladder is committed only AFTER a measurement confirms that the top rung is where the taught
memory is gone. This is a COVERAGE measurement, not an outcome threshold: no gate threshold is
read, chosen or approached here, and the reading is a recall count, not an extraction verdict.

**RECALL-ONLY, AND THAT IS WHAT BOUNDS THE SPEND.** The probe scores through
``phase23_run.score_adapter`` — ``teach_persona.score_arm`` at the identical shape the control was
read at, adapter ON then OFF in one process on one set of weights. There is NO extraction scoring:
extraction is the expensive half (``results/phase23_cost.json``'s draw budget), and the anchor
question — "has the teaching survived this much noise?" — is answered by recall.

WHY THIS IS A SEPARATE MODULE AND NOT AN EDIT TO ``scripts/phase25_calibrate.py``
--------------------------------------------------------------------------------
PLAN 25-12 named ``scripts/phase25_calibrate.py`` as the host for this probe. **THE TREE REFUSES
THAT EDIT, and the refusal is a committed test rather than a preference.**
``tests/test_phase25_calibrate.py::test_the_calibration_provenance_matches_the_live_module_bytes``
recomputes that module's sha256 from bytes and asserts it equals the ``module_sha256`` recorded
inside BOTH ``results/phase25_clip_calibration.json`` and
``results/phase25_adversarial_throughput.json`` — the freshness guard that stops a record and the
code that produced it from drifting apart. Appending one byte to that module reddens it, and the
only honest way to re-green it would be to RE-RUN both calibrations (≈ 21 min + ≈ 2 h of GPU) so
the records carry the new digest. Editing the recorded digests instead would forge a provenance:
those records were not produced by the new bytes.

So the probe lands here. Nothing else moves: :data:`phase25_calibrate.CALIBRATION_PREFIX` is
IMPORTED rather than restated, and so are that module's provenance block, its target-release
helper and its digest helper — so this record's exclusion proof, its provenance shape and its
artifact hygiene are literally the calibration module's own, not a second copy of them.

CPU-SAFE AT IMPORT. ``torch``, ``teach_persona`` and every model module are imported INSIDE the
functions that need them, exactly as ``scripts/phase25_calibrate.py`` does, so the test battery
reads this record without touching a GPU.
"""

import argparse
import json
import pathlib
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import phase25_calibrate as calibrate  # noqa: E402  (needs the sys.path insert above)
import phase25_run  # noqa: E402  (atomic_write_json — the driver's own writer, reused)

MODULE_PATH = pathlib.Path(__file__).resolve()

SIGMA_HI_RECORD = _ROOT / "results" / "phase25_sigma_hi_probe.json"

CLIP_CALIBRATION_RECORD = "results/phase25_clip_calibration.json"
"""The record this probe reads its ``C`` out of. READ LIVE, never retyped.

D-18 requires the anchor to be probed at the ``C`` that will actually ship, because the noise
standard deviation at ``dpsgd.py``'s one draw site is ``sigma * C`` — an anchor probed at a
different ``C`` is an anchor probed at a different noise scale.
"""

CONTROL_READING_RECORD = "results/phase23_sigma_zero.json"
"""The committed σ=0 control, read live for the recall-side floor this probe is judged against."""


# =================================================================================================
# ===== (a) THE RULE, WRITTEN BEFORE THE NUMBERS =====
# =================================================================================================

PROBE_CAPACITY = "dp_n64"

PROBE_CAPACITY_REASON = (
    "THE CAPACITY THAT RESISTS THE NOISE, so a collapse observed here implies a collapse at the "
    "other leg and the single reading covers both. Under DPSGD the signal is the SUM of L clipped "
    "per-record gradients (each of norm at most C) while the injected noise is drawn ONCE per "
    "optimizer step at std sigma*C regardless of L, so the signal-to-noise ratio scales as "
    "L/sigma: "
    "at n=64 the lot is 8x larger than at n=8 and the same sigma is therefore 8x less destructive. "
    "dp_n8 collapses FIRST, so confirming the anchor at dp_n8 would say nothing about dp_n64 while "
    "the converse holds by construction. dp_n64 is also the capacity the shipping C was derived "
    "from (results/phase25_clip_calibration.json clip_norm_rule_capacity), so the probe runs at "
    "the "
    "C that binds where it was measured. The cost is the reason this is not free: dp_n64 trains in "
    "~21 min against dp_n8's ~2.6 min (results/phase25_clip_calibration.json probe.timings), and "
    "the ~16 min recall scoring is the same at both (results/phase23_sigma_zero.json "
    "scoring_seconds 952.0680559994653)"
)

SIGMA_HI_SELECTION_RULE = (
    "THE RULE PRECEDES THE NUMBER. The ladder is a geometric span in sigma running from the "
    "repository's ONLY committed noised point (sigma 0.5, epsilon 519.6981942303134, "
    "results/phase23_noised_dp_n64_sigma0p500000.json) up to the anchor, so the low end reconnects "
    "to committed evidence rather than to a fresh choice. The anchor is then the SMALLEST ROUND "
    "sigma whose epsilon at T=200, delta=1e-5 falls BELOW 1 — the conventional strong-privacy "
    "threshold, and the only pre-existing landmark on this axis that is not this project's own "
    "preference. It is read off the measured curve rather than obtained by inversion, because "
    "round-number epsilon targets are NOT reachable under `==` through sigma_for (measured: "
    "sigma_for(8, 200, 1e-5) = 8.488520944343772 gives 7.9999999999999964 back, not 8). On the "
    "measured curve sigma 50.0 gives 1.060789755417757 (still above 1) and sigma 80.0 gives "
    "0.6339783761989397 (below 1), so the rule selects 80.0"
)

SIGMA_HI_CANDIDATES = (
    {
        "sigma": 80.0,
        "reason": (
            "the smallest round sigma whose epsilon at T=200, delta=1e-5 falls below 1 "
            "(0.6339783761989397); sigma 50.0, the next round rung down, still reads "
            "1.060789755417757. It is the low end of the ladder's intended epsilon span and "
            "therefore the rung whose reachability the whole ladder's width depends on"
        ),
        "probed": True,
    },
)

CANDIDATE_COUNT_REASON = (
    "ONE candidate, not two, and the choice is stated rather than defaulted. D-18 permits one or "
    "two. The confirmation this probe performs is a COLLAPSE TEST at a named sigma, not a "
    "bracketing search for the smallest sigma that collapses — no committed artifact consumes such "
    "a bracket, and the ladder's interior rungs are geometric rather than fitted to one. A second "
    "candidate BELOW the first would buy only a bracket nothing reads; a second candidate ABOVE it "
    "would pre-spend the ratchet's first extension rung before the full extraction read has shown "
    "it is needed, which is exactly the presumption D-18 forbids. The measured cost is the second "
    "half of the reason: one dp_n64 candidate is ~37 min of GPU against the plan's ~20-40 min "
    "probe budget, so a second would have doubled a budget that is already at its ceiling"
)

CONFIRMATION_RULE = (
    "THE CRITERION, FIXED BEFORE THE READING. The anchor is CONFIRMED when the adapter-ON taught "
    "recall at the candidate sigma is NOT ABOVE the adapter-OFF taught recall measured in the SAME "
    "scoring call — teaching bought nothing, so the point sits at the recall-side floor. Both "
    "counts come out of one phase23_run.score_adapter call over one question set with one set of "
    "per-question seeds, so no second scoring path and no cross-run comparison enters the "
    "judgement. The reference this floor is anchored to is the committed control: "
    "results/phase23_sigma_zero.json records taught ON 790/1008 against taught OFF 0/1008, so the "
    "measured OFF floor on this instrument is ZERO successes and the distance the noise has to "
    "close is the whole 790. THIS IS A RECALL CRITERION AND NOT AN EXTRACTION VERDICT: the "
    "never-taught extraction floor (results/phase23_never_taught.json, pooled 0/416) is what the "
    "FULL extraction read in the sweep is judged against, and the ratchet rule below is what "
    "governs that read"
)

RATCHET_EXTENSION_RULE = (
    "THE GRID extends upward, never shifts and never shrinks. If the high extreme's FULL "
    "extraction "
    "read still misses the never-taught floor (results/phase23_never_taught.json, pooled 0/416 "
    "nontarget successes at SEED_LADDER[0], K=16, extraction_noise_floor 0.0), the sigma ladder "
    "extends upward by a pre-registered rung: halve the current top rung's epsilon. The extension "
    "is halve-the-epsilon, applied to the epsilon axis, and the sigma that delivers it "
    "is "
    "read off the measured epsilon(sigma) curve at T=200, delta=1e-5. Every existing rung stays "
    "exactly where it is: no rung is moved, no rung is removed, and no rung's epsilon is restated. "
    "The rule has NO CHEAP DIRECTION by construction, which is what makes it a ratchet rather than "
    "a re-fit: a grid that could shrink after seeing its own result would be a grid chosen with "
    "the "
    "answer visible. THE LOW ANCHOR NEEDS NO PROBE AND GETS NONE: sigma = 0 IS the control "
    "(CTRL-02, D-20 places it INSIDE SWEEP_POINTS at slot 1) and it reconnects to the incumbent "
    "result BY CONSTRUCTION rather than by a claimed correspondence, so there is nothing about it "
    "left to measure"
)

EXCLUSION_REASON = (
    "Every adapter this probe trains is written under phase25_calibrate.CALIBRATION_PREFIX and is "
    "EXCLUDED from the sweep's point set, exactly as phase23_sigma0 was. The exclusion is "
    "STRUCTURAL rather than conventional: tests/test_phase25_calibrate.py::"
    "test_the_calibration_prefix_is_not_a_sweep_point_prefix proves over the ARM TUPLE that no key "
    "phase25_record.point_key can build is prefix-comparable with this prefix in either direction, "
    "for ANY sigma ladder; and this record's own path carries no results/phase25_point_ stem, so "
    "phase25_prereg.POINT_RECORD_GLOB is blind to it. It is recorded as the field "
    "`excluded_from_point_set` rather than left to the prefix convention, so a reader does not "
    "have "
    "to infer the exclusion from a naming habit"
)

MEASURES = (
    "D-18: the taught RECALL of a DP adapter trained at the candidate high-anchor sigma, at the C "
    "that ships. A COVERAGE measurement — no gate threshold is read, chosen or approached, and no "
    "extraction scoring runs"
)


def _clip_norm_that_ships():
    """The shipping ``C``, read LIVE out of 25-11's committed calibration record."""
    blob = calibrate._read_json(CLIP_CALIBRATION_RECORD)
    candidate = float(blob["clip_norm_candidate"])
    calibrate._prove(
        candidate != float(blob["control_clip_norm"]),
        f"{CLIP_CALIBRATION_RECORD} records clip_norm_candidate {candidate!r} equal to its own "
        "control_clip_norm. The two clip constants would then be one, and the noised points would "
        "run at the control's deliberately non-binding bound",
    )
    return candidate, blob


def _control_reading():
    """The committed σ=0 control's taught ON/OFF counts — the recall-side floor, read live."""
    blob = calibrate._read_json(CONTROL_READING_RECORD)
    return {
        "record": CONTROL_READING_RECORD,
        "record_sha256": calibrate.sha256_of(_ROOT / CONTROL_READING_RECORD),
        "sigma": blob["sigma"],
        "taught_on": {"numerator": blob["primary"]["k"], "denominator": blob["primary"]["n"]},
        "taught_off": {
            "numerator": blob["taught_off"]["k"],
            "denominator": blob["taught_off"]["n"],
        },
        # The arm lives in the `training` block, NOT at the top level — the top-level record has no
        # `arm` key at all. Measured the expensive way: an earlier pass of this module read
        # `blob["arm"]` and raised `KeyError: 'arm'` AFTER a 45-minute probe had already run and
        # released its adapter. That is why every committed record this module reads is now parsed
        # BEFORE the GPU work rather than while assembling the blob afterwards.
        "arm": blob["training"]["arm"],
        "why": (
            "the OFF pass is the same weights with the 36 LoRA `enabled` flags flipped, so it is "
            "the closed-book baseline on this exact instrument. It reads ZERO successes, which is "
            "what makes 'collapsed to the floor' a count rather than a comparison to a small number"
        ),
    }


# =================================================================================================
# ===== (b) THE PROBE =====
# =================================================================================================


def probe_candidate(sigma, *, clip_norm, seed):
    """Train ONE ``PROBE_CAPACITY`` adapter at ``sigma``/``clip_norm`` and score it RECALL-ONLY.

    Returns the reading. The training seam is captured so the mechanism's own counters travel with
    the recall count — ``clip_bind_count``, ``records_per_lot``, ``composed_steps`` and
    ``composed_lot_sizes`` are read off the ``DPSGD`` instance ``train_arm`` constructed, never
    inferred from the configuration.
    """
    import mitigation_unit
    import phase23_run
    import teach_persona as tp

    from personacore.privacy.accountant import epsilon_for

    facts, second_person, replay_ratio = tp.arm_spec(PROBE_CAPACITY)
    paths = tp.arm_outputs(PROBE_CAPACITY, prefix=calibrate.CALIBRATION_PREFIX)
    calibrate._release_calibration_targets(PROBE_CAPACITY, paths)

    print(
        f"[phase25_sigma_hi] {PROBE_CAPACITY}: training at sigma={sigma!r} C={clip_norm!r} under "
        f"{calibrate.CALIBRATION_PREFIX!r}",
        flush=True,
    )
    box = {}
    with phase23_run.captured_dp_seam() as seam_box:
        with phase23_run.synchronized_seconds(box):
            tp.train_arm(
                PROBE_CAPACITY,
                facts=facts,
                family_ids=calibrate._taught_family_ids(),
                second_person=second_person,
                replay_ratio=replay_ratio,
                seed=seed,
                prefix=calibrate.CALIBRATION_PREFIX,
                dp_sigma=sigma,
                dp_clip_norm=clip_norm,
            )
    training_seconds = box["seconds"]

    seam, composed = seam_box["seam"], seam_box["composed"]
    calibrate._prove(
        seam is not None,
        f"no DPSGD was constructed during the {PROBE_CAPACITY!r} run. The seam is gated on "
        "`arm in DP_ARMS` and a run that constructed none is not a DP run at all",
    )
    calibrate._prove(
        seam.C == clip_norm and seam.sigma == sigma,
        f"the seam ran at C={seam.C!r} sigma={seam.sigma!r} against the requested "
        f"C={clip_norm!r} sigma={sigma!r} — the reading below would not describe the mechanism "
        "this probe was asked about",
    )

    adapter = paths["adapter"]
    calibrate._prove(
        adapter.exists(), f"{calibrate._rel(adapter)} was not exported — the arm did not complete"
    )
    adapter_sha256 = calibrate.sha256_of(adapter)

    print(
        f"[phase25_sigma_hi] {PROBE_CAPACITY}: trained in {training_seconds:.1f} s — scoring "
        "RECALL-ONLY (no extraction)",
        flush=True,
    )
    started = time.time()
    scored = phase23_run.score_adapter(PROBE_CAPACITY, adapter, seed=seed)
    scoring_seconds = time.time() - started

    calibrate._release_calibration_targets(PROBE_CAPACITY, paths)

    on_taught, off_taught = scored["primary"], scored["taught_off"]
    confirmed = on_taught["k"] <= off_taught["k"]
    print(
        f"[phase25_sigma_hi] {PROBE_CAPACITY}: taught recall ON {on_taught['k']}/{on_taught['n']} "
        f"vs OFF {off_taught['k']}/{off_taught['n']} in {scoring_seconds:.1f} s — anchor "
        f"{'CONFIRMED' if confirmed else 'NOT CONFIRMED'}",
        flush=True,
    )

    return {
        "sigma": sigma,
        "capacity": PROBE_CAPACITY,
        "arm": PROBE_CAPACITY,
        "seed": seed,
        "prefix": calibrate.CALIBRATION_PREFIX,
        "clip_norm": clip_norm,
        "delta": mitigation_unit.DELTA,
        "epsilon": epsilon_for(sigma, tp.MAX_STEPS, mitigation_unit.DELTA),
        "epsilon_rule": "personacore.privacy.accountant.epsilon_for(sigma, steps, delta)",
        # THE RECALL READING, IN COUNTS WITH ITS DENOMINATOR. Never a bare rate: a rate with no
        # denominator cannot be judged against the control's 790/1008 and 0/1008.
        "taught_recall": {
            "numerator": on_taught["k"],
            "denominator": on_taught["n"],
            "questions": on_taught["questions"],
            "draws_per_question": on_taught["draws_per_question"],
            "rate": on_taught["rate"],
        },
        "taught_recall_adapter_off": {
            "numerator": off_taught["k"],
            "denominator": off_taught["n"],
            "questions": off_taught["questions"],
            "draws_per_question": off_taught["draws_per_question"],
            "rate": off_taught["rate"],
        },
        "heldout_recall": {
            "numerator": scored["heldout_on"]["k"],
            "denominator": scored["heldout_on"]["n"],
        },
        "heldout_recall_adapter_off": {
            "numerator": scored["heldout_off"]["k"],
            "denominator": scored["heldout_off"]["n"],
        },
        "anchor_confirmed": confirmed,
        "confirmation_rule": CONFIRMATION_RULE,
        # THE SEAM'S OWN COUNTERS. `_clip_bind_count` is RUN-LIFETIME; `_records` is the last lot's
        # size and must equal the configured accumulation.
        "clip_bind_count": seam._clip_bind_count,
        "clip_is_binding": seam._clip_bind_count > 0,
        "records_per_lot": seam._records,
        "composed_steps": len(composed),
        "composed_lot_sizes": sorted(set(composed)),
        "t_source": "phase23_run._count_composed_steps",
        "max_steps": tp.MAX_STEPS,
        "scoring_is_recall_only": True,
        "scoring_entry_point": "phase23_run.score_adapter -> teach_persona.score_arm",
        "draws_this_leg": scored["draws_this_leg"],
        "training_seconds": training_seconds,
        "scoring_seconds": scoring_seconds,
        "adapter": calibrate._rel(adapter),
        "adapter_sha256": adapter_sha256,
        "adapter_released_after_scoring": not adapter.exists(),
    }


def run_sigma_hi_probe(*, seed=1337):
    """D-18, end to end. Writes :data:`SIGMA_HI_RECORD` and returns the blob.

    **EVERY COMMITTED RECORD IS PARSED BEFORE THE GPU WORK, AND THAT ORDER IS MEASURED RATHER THAN
    TIDY.** An earlier pass of this module read the control record while ASSEMBLING the blob, after
    the probe. A single wrong key path (`blob["arm"]`, which that record carries under `training`
    and not at the top level) raised `KeyError` at the end of a 45-minute run whose adapter had
    already been released, and the whole measurement was lost. Both reads now happen first, so a
    malformed input costs one second.
    """
    clip_norm, clip_blob = _clip_norm_that_ships()
    control_reading = _control_reading()

    readings = [
        probe_candidate(candidate["sigma"], clip_norm=clip_norm, seed=seed)
        for candidate in SIGMA_HI_CANDIDATES
        if candidate["probed"]
    ]
    calibrate._prove(readings, "no candidate was probed — the anchor would be presumed, not probed")

    selected = [reading for reading in readings if reading["anchor_confirmed"]]
    blob = {
        "measures": MEASURES,
        "prefix": calibrate.CALIBRATION_PREFIX,
        "excluded_from_point_set": True,
        "exclusion_reason": EXCLUSION_REASON,
        "probe_capacity": PROBE_CAPACITY,
        "probe_capacity_reason": PROBE_CAPACITY_REASON,
        "capacities_probed": [PROBE_CAPACITY],
        "sigma_hi_selection_rule": SIGMA_HI_SELECTION_RULE,
        "sigma_hi_candidates": [dict(candidate) for candidate in SIGMA_HI_CANDIDATES],
        "candidate_count": len(SIGMA_HI_CANDIDATES),
        "candidate_count_reason": CANDIDATE_COUNT_REASON,
        "confirmation_rule": CONFIRMATION_RULE,
        "RATCHET_EXTENSION_RULE": RATCHET_EXTENSION_RULE,
        "clip_norm_used": clip_norm,
        "clip_norm_source": CLIP_CALIBRATION_RECORD,
        "clip_norm_source_sha256": calibrate.sha256_of(_ROOT / CLIP_CALIBRATION_RECORD),
        "clip_norm_source_rule": clip_blob["clip_norm_rule"],
        "control_reading": control_reading,
        "readings": readings,
        "sigma_hi_selected": selected[-1]["sigma"] if selected else None,
        "anchor_confirmed": bool(selected),
        "ladder_may_be_pinned": bool(selected),
        "ladder_pin_order": (
            "D-18 requires this record to be COMMITTED BEFORE any ladder literal exists. "
            "tests/test_phase25_grid.py::test_the_ratchet_rule_is_committed_before_the_ladder "
            "asserts that order from `git log` rather than trusting it"
        ),
        "limitations": [
            "ONE candidate at ONE capacity. dp_n8 is not probed, and the claim that it collapses "
            "too is a CONSEQUENCE of the L/sigma signal-to-noise argument recorded in "
            "probe_capacity_reason, not a second measurement",
            "RECALL-ONLY. Whether the high extreme reaches the never-taught EXTRACTION floor "
            "(results/phase23_never_taught.json, pooled 0/416) is not answered here and is not "
            "claimed here — that is the full extraction read the sweep performs, and "
            "RATCHET_EXTENSION_RULE is what governs the case where it misses",
            "ONE seed. The seed-to-seed spread of a recall reading at this sigma is not measured, "
            "and no interval is claimed from a single adapter",
        ],
        # `provenance_block` fills `module`/`module_sha256` with the CALIBRATION module's own,
        # because it is that module's helper. This record was produced by THIS file, so both
        # fields are overridden to name it and the helper is carried beside them under its own
        # keys — a record that named the wrong producer would be a freshness guard pointed at a
        # file that cannot change when this one does.
        "provenance": calibrate.provenance_block(
            module=calibrate._rel(MODULE_PATH),
            module_sha256=calibrate.sha256_of(MODULE_PATH),
            helper_module=calibrate._rel(calibrate.MODULE_PATH),
            helper_module_sha256=calibrate.sha256_of(calibrate.MODULE_PATH),
        ),
    }
    phase25_run.atomic_write_json(SIGMA_HI_RECORD, blob)
    print(f"[phase25_sigma_hi] wrote {calibrate._rel(SIGMA_HI_RECORD)}", flush=True)
    return blob


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=1337)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    blob = run_sigma_hi_probe(seed=args.seed)
    print(json.dumps({key: blob[key] for key in ("sigma_hi_selected", "anchor_confirmed")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
