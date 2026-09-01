"""The two RESOURCE measurements the sweep's shape depends on — D-24 and D-14.

WHAT THIS MODULE MEASURES, AND WHAT IT DELIBERATELY DOES NOT
------------------------------------------------------------
Two quantities, both RESOURCE/COVERAGE readings. **No outcome threshold is read, chosen or
approached here.** This milestone permits a resource budget to be measured before
pre-registration; it forbids the same for a gate threshold.

  * **D-24 — the PER-RECORD gradient-norm distribution on the DP path.** ``C`` is pinned nowhere,
    sits OUTSIDE ``mitigation_gate.MECHANISM_KEYS``, and yet the noise standard deviation is
    ``sigma * C`` at ``dpsgd.py``'s one draw site. Two points at equal nominal sigma and different
    ``C`` therefore carry DIFFERENT noise scale while passing the gate's exact-equality check, so
    picking ``C`` by convention is picking the noise scale by convention. The only committed norm
    evidence is ``results/phase23_matched_control.json``'s ``grad_clip_evidence`` — **BATCH-LEVEL
    norms on the NON-DP path** (max 2.277 / 2.202 / 2.302 across seeds, every ``bound_count`` 0).
    The PER-RECORD distribution the DP path actually clips against has never been measured.
    Meanwhile ``results/phase23_noised_dp_n64_sigma0p500000.json`` records ``clip_bind_count``
    **12800 of 12800** at ``C = 1.0`` — 100% binding, which at fixed sigma is pure clipping bias
    bought for nothing because epsilon does not improve.

  * **D-14 — adversarial SCORING throughput at BOTH extremes.** Adversarial *training* cost is
    already bounded (``results/phase23_cost.json``: non-DP protocol-matched **161.124** s/point,
    ``dp_n64`` **1383.3** s). The genuinely unmeasured term is adversarial **scoring**, roughly
    95% of the spend. D-14 requires BOTH extremes probed before the schedule is committed, never
    one extrapolated: ratio ``0.0`` anchors against the committed non-DP figure and ratio
    ``1.9090909090909092`` measures the extreme most likely to diverge.

**THIS MODULE PINS NOTHING.** It measures, derives under a RECORDED RULE, and writes two records.
``scripts/mitigation_budget.py`` is not edited here — plan **25-12** pins ``C`` and the sigma
ladder, after these measurements exist. ``scripts/phase25_calibrate.py`` is likewise not a sweep
driver: every adapter it trains lives under :data:`CALIBRATION_PREFIX`, which is PROVED disjoint
from ``phase25_record.ORDERED_POINT_KEYS()``'s key space by
``tests/test_phase25_calibrate.py``.

CPU-SAFE AT IMPORT. ``torch``, ``teach_persona`` and every model module are imported INSIDE the
functions that need them, exactly as ``scripts/phase25_run.py`` does, so the whole test battery
reads these records without touching a GPU.
"""

import argparse
import datetime
import hashlib
import json
import math
import pathlib
import platform
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import mitigation_budget  # noqa: E402  (needs the sys.path insert; scripts/ is not a package)
import phase25_run  # noqa: E402  (atomic_write_json — the driver's own writer, reused)

from personacore.provenance import git_sha  # noqa: E402


def _prove(condition, message):
    """``SystemExit`` on a broken invariant — ``phase25_run._prove``'s register, this prefix.

    ``SystemExit`` and deliberately NOT ``assert``: an ``assert`` is strippable under ``-O``, and a
    proof that disappears under an optimisation flag is not a proof.
    """
    if not condition:
        raise SystemExit(f"[phase25_calibrate] {message}")


def _rel(path):
    """A repo-relative rendering for the log, falling back to the absolute path off-tree."""
    try:
        return str(pathlib.Path(path).resolve().relative_to(_ROOT))
    except ValueError:
        return str(path)


def sha256_of(path):
    """sha256 of one file's bytes. Streamed — ``teach_persona._sha256``'s shape, this register."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(relative_path):
    """One committed record, read from its repo-relative path. Refuses a missing file BY NAME."""
    path = _ROOT / relative_path
    _prove(path.exists(), f"{relative_path} does not exist — this measurement reads it, live")
    return json.loads(path.read_text(encoding="utf-8"))


# =================================================================================================
# ===== (a) THE NAMED CALIBRATION PREFIX — EXCLUDED FROM THE SWEEP'S POINT SET =====
# =================================================================================================

CALIBRATION_PREFIX = "phase25_calibration"
"""The ``prefix=`` every adapter this module trains is written under.

It reaches ``teach_persona.arm_outputs(arm, prefix=...)``, which scopes ``adapter`` / ``csv`` /
``checkpoint``. It is **not** a point key and cannot become one: every member of
``phase25_record.ORDERED_POINT_KEYS()`` begins with a member of
``phase25_record.ORDERED_ARMS`` (``point_key`` renders ``f"{arm}_{axis}{value:.6f}"``), and no
arm name and this prefix are prefix-comparable in either direction. The test asserts that
structurally, over the ARM TUPLE rather than over one ladder, so the exclusion holds for any
sigma ladder plan 25-12 pins.
"""

CALIBRATION_PREFIX_PROVENANCE = {
    "prefix": CALIBRATION_PREFIX,
    "governs": (
        "the adapter/csv/checkpoint scope of every arm trained by scripts/phase25_calibrate.py, "
        "and nothing else. These are CALIBRATION runs: they measure a resource quantity and are "
        "EXCLUDED from the sweep's point set, so none of them may ever be read as a frontier point"
    ),
    "precedent": "phase23_run.SIGMA_ZERO_PREFIX",
    "precedent_value": "phase23_sigma0",
    "precedent_reason": (
        "D-18 names phase23_sigma0 as the shape a named-and-excluded calibration run takes: a "
        "probe under a named prefix, excluded from the sweep's point set exactly as phase23_sigma0 "
        "was. This prefix is that precedent applied to Phase 25's two resource probes"
    ),
    "exclusion_proof": (
        "tests/test_phase25_calibrate.py::test_the_calibration_prefix_is_not_a_sweep_point_prefix "
        "— no member of phase25_record.ORDERED_ARMS and this prefix are prefix-comparable in "
        "either direction, so no key phase25_record.point_key can build begins with it, for ANY "
        "sigma ladder; and no path matching phase25_prereg.POINT_RECORD_GLOB names it"
    ),
    "pins_nothing": (
        "this module writes no constant into scripts/mitigation_budget.py. Plan 25-12 pins C and "
        "the sigma ladder, after these measurements exist"
    ),
}

CLIP_CALIBRATION_RECORD = _ROOT / "results" / "phase25_clip_calibration.json"
THROUGHPUT_RECORD = _ROOT / "results" / "phase25_adversarial_throughput.json"

MODULE_PATH = pathlib.Path(__file__).resolve()


# =================================================================================================
# ===== (b) THE PROVENANCE BLOCK BOTH RECORDS CARRY =====
# =================================================================================================

CLIP_DOMAIN_PROBE_VALUES = ("inf", "0.0", "-1.0", "nan")
"""The four ``clip_norm`` values whose refusal is captured. Rendered as STRINGS because JSON has
no ``inf`` / ``nan`` literal and a record that cannot round-trip through ``json.loads`` is not a
record. The live values are rebuilt from these by :func:`clip_domain_refusals`."""

_CLIP_DOMAIN_LIVE = {
    "inf": math.inf,
    "0.0": 0.0,
    "-1.0": -1.0,
    "nan": math.nan,
}


def clip_domain_refusals():
    """The VERBATIM ``[dp-refusal:clip-domain]`` text for all four illegal ``clip_norm`` values.

    **No model, no GPU, and no import of anything heavier than the mechanism itself.**
    ``DPSGD.__init__``'s PRE-PASS 1 is the caller-supplied numeric domain and it runs BEFORE
    PRE-PASS 2's model audit, so ``model=None`` never reaches a ``named_parameters()`` call. That
    ordering is what makes CTRL-02's proxy cost microseconds rather than a model load, and it is
    why discovering ``clip_norm=math.inf`` is refused can never cost a sweep hour.

    The wave-1 assertion that these values ARE refused lives in
    ``tests/test_phase25_prereg.py::test_clip_domain_is_refused`` (plan 25-01) — a millisecond CPU
    check that guards a 100-150 h sweep belongs BEFORE every GPU-spending plan, not inside the
    first one. This function only CAPTURES the text so the record carries a copy rather than a
    paraphrase, and ``tests/test_phase25_calibrate.py`` proves the copy is live.
    """
    from personacore.privacy.dpsgd import DPSGD

    captured = {}
    for label in CLIP_DOMAIN_PROBE_VALUES:
        started = time.perf_counter()
        try:
            DPSGD(None, sigma=0.0, clip_norm=_CLIP_DOMAIN_LIVE[label])
        except ValueError as exc:
            captured[label] = {
                "message": str(exc),
                "exception": "ValueError",
                "seconds": time.perf_counter() - started,
            }
        else:  # pragma: no cover - the refusal is asserted in wave 1; this is the impossible leg
            _prove(
                False,
                f"DPSGD(None, sigma=0.0, clip_norm={label}) did NOT raise. CTRL-02's cheap proxy "
                "rests on this refusal and a sweep that discovers it mid-run has already spent "
                "the hours",
            )
        _prove(
            "[dp-refusal:clip-domain]" in captured[label]["message"],
            f"the refusal for clip_norm={label} does not carry the [dp-refusal:clip-domain] tag. "
            "The tag is what makes the refusal greppable and attributable to the clip domain "
            "rather than to the sigma domain",
        )
    return captured


def provenance_block(**extra):
    """The provenance every record in this module carries. ``phase25_record``'s own field set.

    ``module_sha256`` is THIS FILE's digest, so a record and the code that produced it cannot
    drift apart silently. ``tests/test_phase25_calibrate.py`` recomputes it from bytes and asserts
    equality — the freshness guard ``tests/test_phase24_record.py`` established, in this register.
    """
    import torch

    refusals = clip_domain_refusals()
    return {
        "git_sha": git_sha(),
        "device": _device_name(),
        "torch_version": torch.__version__,
        "python_version": platform.python_version(),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "calibration_prefix": CALIBRATION_PREFIX,
        "calibration_prefix_provenance": CALIBRATION_PREFIX_PROVENANCE,
        "module": _rel(MODULE_PATH),
        "module_sha256": sha256_of(MODULE_PATH),
        # CTRL-02's cheap proxy, captured VERBATIM. `inf` is the one the plan names; all four are
        # carried because the wave-1 test asserts all four and a record that carried one would
        # make three of that test's four legs uncheckable against a transcript.
        "clip_domain_refusal": refusals["inf"]["message"],
        "clip_domain_refusals": refusals,
        "clip_domain_probe_cost": (
            "no model and no GPU: DPSGD.__init__'s PRE-PASS 1 (the caller-supplied numeric "
            "domain) runs BEFORE PRE-PASS 2's model audit, so model=None never reaches "
            "named_parameters(). Measured seconds per refusal are carried per value above"
        ),
        **extra,
    }


def _device_name():
    """The resolved training/scoring device, from the project's own preflight. Never guessed."""
    from personacore.preflight import preflight_device

    return str(preflight_device(strict=True)["device"])


# =================================================================================================
# ===== (c) D-24 — THE PER-RECORD NORM PROBE =====
# =================================================================================================

NORM_PROBE_CAPACITIES = ("dp_n8", "dp_n64")

NORM_PROBE_SIGMA = 0.0
"""The probe runs at sigma = 0.

The quantity D-24 asks for is the per-record norm distribution the mechanism CLIPS AGAINST — the
PRE-clip norm. Noise perturbs the weights and therefore the later gradients, so a probe at any
sigma > 0 measures the distribution along a NOISED trajectory and would have to name which sigma
it belongs to. sigma = 0 is the one trajectory already committed
(``results/phase23_sigma_zero.json``), it is a real sweep point under CTRL-02, and it is the only
sigma at which the reading is a property of the DATA rather than of a noise draw. The limitation
is recorded in the record's own ``limitations`` block rather than left for a reader to infer.
"""

NORM_PROBE_CLIP_NORM_SOURCE = "results/phase23_sigma_zero.json"
"""The probe's own ``clip_norm`` is read LIVE from the sigma-zero record, never retyped.

It must be NON-BINDING or the measured norms would be the CLIPPED norms and the distribution
would be a picture of the bound rather than of the records. ``phase23_sigma_zero`` used exactly
this value and recorded ``clip_bind_count`` 0 over the whole run, which is the observation that
makes "non-binding" literal rather than hoped for.
"""

NORM_PROBE_RECORD_BUDGET = {
    "dp_n8": 1600,
    "dp_n64": 12800,
}
"""How many RECORDS each capacity's probe absorbs before it stops. Counts, not step counts.

BOTH capacities run the FULL ``teach_persona.MAX_STEPS`` = 200 optimizer steps: ``dp_n8`` at 8
records per step (200 x 8 = 1600) and ``dp_n64`` at 64 (200 x 64 = 12800). ``dp_n64``'s 12800 is
the SAME denominator ``results/phase23_noised_dp_n64_sigma0p500000.json`` reports its
``clip_bind_count`` of 12800 over, so D-24's counter-example and this measurement are counted over
identical record sets.

**A TRUNCATED WINDOW WAS TRIED FIRST AND MEASURED WRONG — THAT IS WHY THE FULL RUN IS RUN.** The
first pass stopped ``dp_n64`` after 3200 records (the first 50 steps) to fit a 40-minute budget
against ``dp_n64``'s committed 1383.3 s = 23.05 min. ``dp_n8``'s own full run then measured what
that window costs: its first-50-step median per-record norm is **2.2749314308166504** against a
full-run median of **0.5546967387199402** — the truncated window overstates the median by
**3.1012165243056105x**, because gradient norms fall steeply as the loss drops. A ``C`` derived
from that window would have been ~3x too large, and at fixed sigma an oversized ``C`` is pure
excess noise (``std = sigma * C``) bought for nothing. The window was therefore abandoned rather
than caveated. :func:`early_window_bias` keeps that measurement in the record at BOTH capacities,
so the finding survives its own correction.

``MAX_STEPS`` IS NEVER LOWERED. Lowering it would compress the cosine LR schedule and make step 30
of a short run a different step from step 30 of the real 200-step run. The probe stops instead by
raising out of ``absorb_record`` once the budget is met, so every recorded record is bit-for-bit
the record the real run's corresponding step produced.
"""

EARLY_WINDOW_STEPS = 50
"""The optimizer-step window :func:`early_window_bias` reports against the full run.

50 because that is the window the abandoned first pass actually used, so the number in the record
is the size of a real error this plan made and corrected, not a hypothetical one.
"""

CLIP_NORM_RULE_QUANTILE = 0.5

CLIP_NORM_RULE_CAPACITY = "dp_n64"

CLIP_NORM_RULE = (
    "clip_norm_candidate = sorted(per_record_norms['"
    + CLIP_NORM_RULE_CAPACITY
    + "']['values'])[math.ceil("
    + repr(CLIP_NORM_RULE_QUANTILE)
    + " * n_records) - 1] — the smallest MEASURED per-record global L2 norm at or above the p"
    + str(int(CLIP_NORM_RULE_QUANTILE * 100))
    + " of the binding capacity's own distribution, taken WITHOUT interpolation so the candidate "
    "IS one of the measured values and re-derives from them by index under exact equality. "
    "THE QUANTILE IS FIXED BEFORE THE NUMBER AND FOR A STATED REASON: at fixed sigma, epsilon "
    "does not depend on C at all, so C trades clipping bias against noise magnitude and nothing "
    "else (the noise standard deviation is sigma * C at dpsgd.py's one draw site). The median is "
    "the C that minimises the expected absolute deviation E|record_norm - C| over the measured "
    "records, and it is the operating point Abadi et al. (2016) state for DP-SGD — set C to the "
    "median of the unclipped per-record gradient norms. THE BINDING CAPACITY IS "
    + CLIP_NORM_RULE_CAPACITY
    + " because that is where results/phase23_noised_dp_n64_sigma0p500000.json recorded "
    "clip_bind_count 12800 of 12800 at C = 1.0 — D-24's counter-example, and the only committed "
    "evidence that a chosen C can clip every record. EVERY MEASURED VALUE IS RECORDED BESIDE "
    "THIS RULE, so any other quantile is re-derivable by a reader without re-running the probe. "
    "PLAN 25-12 PINS THE VALUE; this plan measures and derives it and pins nothing."
)

CLIP_NORM_COUNTER_EXAMPLE_RECORD = "results/phase23_noised_dp_n64_sigma0p500000.json"

BATCH_LEVEL_NORM_RECORD = "results/phase23_matched_control.json"


class _ProbeBudgetReached(Exception):
    """Raised out of ``absorb_record`` when a capacity's record budget is met.

    NOT a ``SystemExit`` and not a ``_prove``: this is the probe's ordinary, expected stop, and it
    is caught by :func:`measure_per_record_norms` alone. Raising is what keeps ``MAX_STEPS`` and
    therefore the LR schedule UNCHANGED — see :data:`NORM_PROBE_RECORD_BUDGET`.
    """


def _norm_recording_dpsgd(real_class, budget):
    """A ``DPSGD`` subclass that RECORDS the pre-clip global norm the mechanism itself computed.

    **THE NORM IS READ OUT OF THE MECHANISM'S OWN ACCOUNTING, NEVER RE-IMPLEMENTED.**
    ``DPSGD._global_norm`` is the L2 norm across all 72 trainable LoRA gradients AS ONE VECTOR —
    the global norm the clip compares to ``C`` and the sensitivity bound is stated over. It is
    called TWICE per ``absorb_record``: once on the raw gradients (the PRE-clip norm, which is the
    quantity D-24 asks for) and once on the SCALED tensors (the post-clip re-computation that
    arms the sensitivity invariant). The override below captures both and
    :meth:`absorb_record` keeps the FIRST of the pair, so the measurement and the mechanism cannot
    disagree: they are the same float, produced once.

    Shadowing at the CONSTRUCTOR is ``phase23_run.captured_dp_seam``'s mechanism and
    ``tests/test_phase23_resume.py::_install_dp_probe``'s before it — ``train_arm`` builds the seam
    internally and returns paths and losses, so the constructor is the only place the driver's
    instance is reachable from outside.
    """

    class _NormRecordingDPSGD(real_class):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.per_record_norms = []
            self.records_per_step = []
            self._norm_calls = []
            self._step_start = 0

        def begin_step(self):
            self._step_start = len(self.per_record_norms)
            return super().begin_step()

        def _global_norm(self, tensors):
            value = super()._global_norm(tensors)
            self._norm_calls.append(value)
            return value

        def absorb_record(self):
            first = len(self._norm_calls)
            result = super().absorb_record()
            # The FIRST _global_norm call inside absorb_record is the PRE-clip norm; the second is
            # the sensitivity re-computation over the already-scaled tensors.
            self.per_record_norms.append(self._norm_calls[first])
            if len(self.per_record_norms) >= budget:
                self._flush_step()
                raise _ProbeBudgetReached(len(self.per_record_norms))
            return result

        def finalize(self, accum):
            self._flush_step()
            return super().finalize(accum)

        def _flush_step(self):
            drawn = len(self.per_record_norms) - self._step_start
            if drawn > 0:
                self.records_per_step.append(drawn)
                self._step_start = len(self.per_record_norms)

    return _NormRecordingDPSGD


def measure_per_record_norms(capacity, *, seed, clip_norm):
    """Drive ONE training pass on the DP path at ``capacity`` and return its per-record norms.

    Returns ``(norms, records_per_step, seconds, stopped_early)``. ``norms`` is in ABSORB ORDER,
    not sorted — the caller sorts once and records both the order statistics and the per-step
    partition, so the trajectory is re-derivable from the record.

    Everything routes through the single production entry ``teach_persona.train_arm`` at the
    ``dp_fn=`` gradient seam, so the norms measured are the ones the mechanism actually clips
    against on the path the sweep will run. ``fact_bin=`` / ``n_facts=`` / ``dp_fn=`` are
    ``personacore.training.loop.train``'s kwargs one layer down and are never passed here.
    """
    import teach_persona as tp

    facts, second_person, replay_ratio = tp.arm_spec(capacity)
    budget = NORM_PROBE_RECORD_BUDGET[capacity]

    paths = tp.arm_outputs(capacity, prefix=CALIBRATION_PREFIX)
    _release_calibration_targets(capacity, paths)

    real = tp.DPSGD
    box = {"seam": None}

    def factory(model, **kwargs):
        _prove(
            box["seam"] is None,
            "a SECOND DPSGD was constructed inside one probe. The norms read afterwards would "
            "describe whichever seam was constructed last",
        )
        seam = _norm_recording_dpsgd(real, budget)(model, **kwargs)
        box["seam"] = seam
        return seam

    tp.DPSGD = factory
    started = time.time()
    stopped_early = False
    try:
        tp.train_arm(
            capacity,
            facts=facts,
            family_ids=_taught_family_ids(),
            second_person=second_person,
            replay_ratio=replay_ratio,
            seed=seed,
            prefix=CALIBRATION_PREFIX,
            dp_sigma=NORM_PROBE_SIGMA,
            dp_clip_norm=clip_norm,
        )
    except _ProbeBudgetReached as reached:
        stopped_early = True
        print(
            f"[phase25_calibrate] {capacity}: record budget {reached.args[0]} reached — "
            "stopping the pass. MAX_STEPS was NOT lowered, so the LR schedule and therefore "
            "every recorded record is the real run's own",
            flush=True,
        )
    finally:
        tp.DPSGD = real
    seconds = time.time() - started

    seam = box["seam"]
    _prove(seam is not None, f"{capacity}: no DPSGD was constructed — the DP seam never armed")
    _prove(
        len(seam.per_record_norms) == budget,
        f"{capacity}: the probe recorded {len(seam.per_record_norms)} per-record norm(s) against "
        f"the budget {budget}. Every quantile below is over that denominator and a short sample "
        "would derive C from fewer records than the record claims it covers",
    )
    _prove(
        seam.C == clip_norm and seam._clip_bind_count == 0,
        f"{capacity}: the probe ran at C={seam.C!r} with clip_bind_count="
        f"{seam._clip_bind_count!r}. A binding bound would make these the CLIPPED norms — a "
        "picture of the bound rather than of the records",
    )
    _release_calibration_targets(capacity, paths)
    return list(seam.per_record_norms), list(seam.records_per_step), seconds, stopped_early


def _taught_family_ids():
    import phase14_factset as fs

    return fs.TAUGHT_FAMILY_IDS


def _release_calibration_targets(arm, paths):
    """Delete this arm's bins/csv/checkpoint/adapter so ``refuse_if_exists`` can arm again.

    ``phase23_run.rebuild_arm_bins_verifying_sha256`` records the measured constraint this exists
    for: ``arm_outputs`` scopes ``csv``/``checkpoint``/``adapter`` by ``prefix=`` but ``bin`` and
    ``mask`` carry **no** prefix, so every ``dp_n8`` run in the repository shares the same three
    ``data/persona_dp_n8_train*.bin`` paths and ``refuse_if_exists`` refuses the second one. The
    sanctioned route is the refusal message's own — *"Delete ... to re-run"* — and ``data/`` plus
    ``checkpoints/`` are wholly gitignored, so nothing committed is destroyed.

    THIS IS A CALIBRATION PREFIX ONLY. The paths deleted are derived from
    ``arm_outputs(arm, prefix=CALIBRATION_PREFIX)`` and the arm's own bins; no sweep point, no
    committed record and no other prefix's adapter is reachable from here.
    """
    import teach_persona as tp

    _prove(
        CALIBRATION_PREFIX in str(paths["adapter"]) and CALIBRATION_PREFIX in str(paths["csv"]),
        f"refusing to release targets for {arm!r}: {paths['adapter']} is not under "
        f"{CALIBRATION_PREFIX!r}. Only this module's own calibration artifacts are deletable here",
    )
    targets = tp.arm_bin_targets(arm, paths) + [
        paths["csv"],
        paths["checkpoint"],
        paths["adapter"],
    ]
    for target in targets:
        pathlib.Path(target).unlink(missing_ok=True)


def _order_statistic(sorted_values, quantile):
    """``sorted_values[ceil(q * n) - 1]`` — the order statistic, with NO interpolation.

    Interpolation would produce a number that is not one of the measured values, and a candidate
    that is not a measurement cannot be re-derived from the measurements by index.
    """
    n = len(sorted_values)
    _prove(n > 0, "an order statistic over an empty sample has no denominator")
    index = math.ceil(quantile * n) - 1
    index = min(max(index, 0), n - 1)
    return sorted_values[index], index


def _distribution(values, records_per_step):
    """The recorded shape of one capacity's per-record norms: every value, plus its statistics."""
    ordered = sorted(values)
    n = len(ordered)
    by_step = []
    cursor = 0
    for drawn in records_per_step:
        by_step.append(list(values[cursor : cursor + drawn]))
        cursor += drawn
    _prove(
        cursor == n,
        f"the per-step partition covers {cursor} of {n} record(s). `values` and `by_step` are the "
        "same measurement in two orderings and a partition that lost records would make the "
        "trajectory un-re-derivable",
    )
    return {
        "n_records": n,
        "optimizer_steps": len(by_step),
        "records_per_step": list(records_per_step),
        # THE FULL LIST, SORTED. Every bound in this record re-derives from it by index; nothing
        # here is a histogram summary.
        "values": ordered,
        # The SAME values in absorb order, partitioned by optimizer step, so the trajectory the
        # sample was drawn along is visible rather than assumed flat.
        "by_step": by_step,
        "min": ordered[0],
        "max": ordered[-1],
        "mean": sum(ordered) / n,
        "median": _order_statistic(ordered, 0.5)[0],
        "p90": _order_statistic(ordered, 0.90)[0],
        "p99": _order_statistic(ordered, 0.99)[0],
        "quantile_rule": (
            "every quantile above is the ORDER STATISTIC sorted(values)[ceil(q * n_records) - 1] "
            "— no interpolation, so each is one of the measured values and re-derives by index"
        ),
    }


def _bind_curve(ordered, trial_clip_norms):
    """``clip_bind_count`` at each trial ``C`` — a MEASURED curve, not an inference.

    ``DPSGD.absorb_record`` increments the counter exactly when ``norm > self.C``, so the count
    below is that predicate applied to the recorded norms and nothing else.
    """
    n = len(ordered)
    return [
        {
            "clip_norm": trial,
            "clip_bind_count": sum(1 for value in ordered if value > trial),
            "n_records": n,
        }
        for trial in trial_clip_norms
    ]


def _trial_clip_norms(ordered, extra):
    """The trial ``C`` ladder: the sample's own deciles plus the committed constants.

    The deciles come from the measurement rather than from a chosen ladder, so the binding curve
    is dense exactly where the records are.
    """
    trials = {float(value) for value in extra}
    for step in range(0, 11):
        trials.add(float(_order_statistic(ordered, max(step, 1) / 10.0)[0]))
    return sorted(trials)


def run_clip_calibration(*, seed=1337):
    """D-24, end to end. Writes :data:`CLIP_CALIBRATION_RECORD` and returns the blob."""
    sigma_zero = _read_json(NORM_PROBE_CLIP_NORM_SOURCE)
    control_clip_norm = float(sigma_zero["clip_norm"])
    _prove(
        sigma_zero["clip_bind_count"] == 0,
        f"{NORM_PROBE_CLIP_NORM_SOURCE} records clip_bind_count "
        f"{sigma_zero['clip_bind_count']!r}, not 0. The probe's own bound is read from that "
        "record precisely because it is the one PROVEN not to bind",
    )

    counter_example = _read_json(CLIP_NORM_COUNTER_EXAMPLE_RECORD)
    batch_level = _read_json(BATCH_LEVEL_NORM_RECORD)

    per_record = {}
    timings = {}
    for capacity in NORM_PROBE_CAPACITIES:
        print(f"[phase25_calibrate] {capacity}: per-record norm probe starting", flush=True)
        values, per_step, seconds, stopped_early = measure_per_record_norms(
            capacity, seed=seed, clip_norm=control_clip_norm
        )
        per_record[capacity] = _distribution(values, per_step)
        timings[capacity] = {
            "seconds": seconds,
            "stopped_early": stopped_early,
            "record_budget": NORM_PROBE_RECORD_BUDGET[capacity],
        }
        print(
            f"[phase25_calibrate] {capacity}: {per_record[capacity]['n_records']} record(s) over "
            f"{per_record[capacity]['optimizer_steps']} optimizer step(s) in {seconds:.1f} s — "
            f"min {per_record[capacity]['min']:.6f} median "
            f"{per_record[capacity]['median']:.6f} max {per_record[capacity]['max']:.6f}",
            flush=True,
        )

    binding = per_record[CLIP_NORM_RULE_CAPACITY]
    candidate, candidate_index = _order_statistic(binding["values"], CLIP_NORM_RULE_QUANTILE)

    trials = _trial_clip_norms(binding["values"], (1.0, candidate, control_clip_norm))
    bind_curve = {
        capacity: _bind_curve(per_record[capacity]["values"], trials)
        for capacity in NORM_PROBE_CAPACITIES
    }

    above_c1 = {
        capacity: {
            "numerator": sum(1 for value in per_record[capacity]["values"] if value > 1.0),
            "denominator": per_record[capacity]["n_records"],
        }
        for capacity in NORM_PROBE_CAPACITIES
    }

    # THE EARLY-WINDOW BIAS, MEASURED AT BOTH CAPACITIES. Both probes ran the full MAX_STEPS, so
    # each capacity's own first-EARLY_WINDOW_STEPS prefix against its full sample is a direct
    # reading of how much a truncated window would have moved the rule. It is recorded because
    # this plan's FIRST pass used exactly that window and was wrong by the factor below.
    truncation = {
        capacity: early_window_bias(per_record[capacity], capacity)
        for capacity in NORM_PROBE_CAPACITIES
    }

    blob = {
        "measures": (
            "D-24: the PER-RECORD gradient-norm distribution on the DP path, at both capacities, "
            "value by value. This is a RESOURCE measurement — no gate threshold is read, chosen "
            "or approached"
        ),
        "per_record_norms": per_record,
        "probe": {
            "sigma": NORM_PROBE_SIGMA,
            "sigma_reason": (
                "the quantity is the PRE-clip norm the mechanism clips against. Noise perturbs "
                "the weights and therefore the later gradients, so any sigma > 0 measures a "
                "NOISED trajectory and would have to name which sigma it belongs to. sigma = 0 is "
                "the trajectory results/phase23_sigma_zero.json already committed and is a real "
                "sweep point under CTRL-02"
            ),
            "clip_norm": control_clip_norm,
            "clip_norm_source": NORM_PROBE_CLIP_NORM_SOURCE,
            "clip_norm_reason": (
                "NON-BINDING by construction and by observation: phase23_sigma_zero ran at this "
                "value and recorded clip_bind_count 0 over the whole run, so the norms measured "
                "here are the UNCLIPPED records rather than a picture of the bound"
            ),
            "seed": seed,
            "max_steps_unchanged": True,
            "max_steps_note": (
                "teach_persona.MAX_STEPS is NOT lowered. The probe stops by raising out of "
                "absorb_record once its record budget is met, so the cosine LR schedule is the "
                "real 200-step schedule and every recorded record is bit-for-bit the record the "
                "real run's corresponding step would have produced"
            ),
            "record_budget": dict(NORM_PROBE_RECORD_BUDGET),
            "timings": timings,
            "entry_point": "teach_persona.train_arm at the dp_fn= gradient seam",
            "norm_source": (
                "DPSGD._global_norm, read out of the mechanism's own accounting via a constructor "
                "shadow (phase23_run.captured_dp_seam's mechanism). The norm is the L2 across all "
                "trainable LoRA gradients AS ONE VECTOR and is NOT re-implemented here"
            ),
        },
        # THE RULE IS RECORDED BEFORE THE NUMBER IT PRODUCED.
        "clip_norm_rule": CLIP_NORM_RULE,
        "clip_norm_rule_quantile": CLIP_NORM_RULE_QUANTILE,
        "clip_norm_rule_capacity": CLIP_NORM_RULE_CAPACITY,
        "clip_norm_rule_index": candidate_index,
        "clip_norm_candidate": float(candidate),
        "clip_norm_candidate_pinned_by": (
            "PLAN 25-12. This module pins nothing: scripts/mitigation_budget.py is byte-unchanged "
            "by this plan and the candidate above is a measurement awaiting its pin"
        ),
        "clip_bind_curve": bind_curve,
        "clip_bind_curve_rule": (
            "clip_bind_count at each trial C is the count of recorded norms strictly ABOVE it — "
            "DPSGD.absorb_record's own predicate (norm > self.C) applied to the recorded values. "
            "The trial ladder is the binding capacity's own deciles plus C = 1.0 (D-24's "
            "counter-example), the derived candidate, and the control's non-binding bound"
        ),
        # D-24'S QUESTION, ANSWERED IN COUNTS WITH A DENOMINATOR.
        "fraction_of_records_above_c1": {
            "clip_norm": 1.0,
            "capacity": CLIP_NORM_RULE_CAPACITY,
            "numerator": above_c1[CLIP_NORM_RULE_CAPACITY]["numerator"],
            "denominator": above_c1[CLIP_NORM_RULE_CAPACITY]["denominator"],
            "per_capacity": above_c1,
            "answers": (
                "D-24 asks whether 100% binding at C = 1.0 is a sensible operating point or an "
                "accident of one run. "
                + CLIP_NORM_COUNTER_EXAMPLE_RECORD
                + " recorded clip_bind_count "
                + str(counter_example["clip_bind_count"])
                + " of "
                + str(counter_example["clip_bind_count"])
                + " at clip_norm "
                + repr(counter_example["clip_norm"])
                + " and epsilon "
                + repr(counter_example["epsilon"])
                + ". At fixed sigma, epsilon does not depend on C, so a C below every record's "
                "norm is pure clipping bias bought for nothing. The numerator/denominator pair "
                "above is that question answered against a MEASURED per-record distribution "
                "rather than against one run's counter"
            ),
        },
        "counter_example": {
            "record": CLIP_NORM_COUNTER_EXAMPLE_RECORD,
            "record_sha256": sha256_of(_ROOT / CLIP_NORM_COUNTER_EXAMPLE_RECORD),
            "clip_norm": counter_example["clip_norm"],
            "clip_bind_count": counter_example["clip_bind_count"],
            "clip_is_binding": counter_example.get("clip_is_binding"),
            "epsilon": counter_example["epsilon"],
        },
        "batch_level_comparison": {
            "record": BATCH_LEVEL_NORM_RECORD,
            "record_sha256": sha256_of(_ROOT / BATCH_LEVEL_NORM_RECORD),
            "quantity": (
                "BATCH-LEVEL pre-clip norms on the NON-DP path — a DIFFERENT QUANTITY from the "
                "per-record norms above. One batch's averaged gradient is not one record's "
                "gradient, and conflating the two would pick the noise scale by accident (this "
                "record's own trust boundary). It is quoted for scale only and no bound here is "
                "derived from it"
            ),
            "grad_clip_evidence": batch_level.get("grad_clip_evidence"),
        },
        # (c) THE CONTROL'S C IS NOT THIS NUMBER.
        "control_clip_norm": control_clip_norm,
        "control_clip_norm_source": NORM_PROBE_CLIP_NORM_SOURCE,
        "control_clip_norm_reason": (
            "D-01's reproduction of the sigma=0 control is BIT-LEVEL against "
            + NORM_PROBE_CLIP_NORM_SOURCE
            + ", which used exactly this clip_norm and recorded clip_bind_count 0. The control "
            "must reuse it UNCHANGED or the reproduction is not bit-level, so the calibrated "
            "candidate above must never be applied to the control point"
        ),
        "two_clip_constants_decision": {
            "decided_here": True,
            "reason": (
                "25-CONTEXT resolves this nowhere: D-01 requires the control at C = "
                + repr(control_clip_norm)
                + " for bit-level reproduction while D-24 calibrates C for the NOISED points, and "
                "no decision names both. It is decided here and recorded: plan 25-12 must pin TWO "
                "clip constants in scripts/mitigation_budget.py"
            ),
            "constants": [
                {
                    "name": "CLIP_NORM",
                    "value": float(candidate),
                    "governs": "every NOISED DP sweep point, at both capacities",
                    "derived_by": "clip_norm_rule, above",
                },
                {
                    "name": "CONTROL_CLIP_NORM",
                    "value": control_clip_norm,
                    "governs": "the sigma=0 control point only, at both capacities",
                    "derived_by": (
                        "read live from " + NORM_PROBE_CLIP_NORM_SOURCE + ", never retyped"
                    ),
                },
            ],
            "measured_absence": (
                "phase25_record.CONTROL_CLIP_NORM does not exist at this commit, and plan 25-10 "
                "made dp_clip_norm caller-supplied precisely so the pin could land in 25-12/25-15 "
                "rather than in a wave-3 module"
            ),
            "d25_consequence": (
                "C cannot join mitigation_gate.MECHANISM_KEYS — the gate is frozen and any commit "
                "to it after results/phase20_* exists reddens the ancestry guard permanently. It "
                "does not need to: capacity_comparison ignores extra keys, so clip_norm travels "
                "in the mechanism dicts and the driver proves equality on it caller-side (D-25)"
            ),
        },
        "truncation_bias": truncation,
        "limitations": [
            "The distribution is measured at sigma = 0. Under sigma > 0 the noise perturbs the "
            "weights and therefore the later gradients, so the per-record norms along a noised "
            "trajectory will differ. No point in this record claims otherwise",
            "BOTH capacities cover the FULL teach_persona.MAX_STEPS. An earlier pass of this "
            "plan truncated dp_n64 to its first "
            + str(EARLY_WINDOW_STEPS)
            + " steps to fit a 40-minute budget; dp_n8's full run measured that window "
            "overstating the median per-record norm by "
            + repr(truncation["dp_n8"]["window_over_full_ratio"])
            + "x, so the window was abandoned rather than caveated. The finding is kept under "
            "truncation_bias at both capacities",
            "The candidate is a resource derivation, not a pre-registered threshold. No gate "
            "threshold is read, chosen or approached anywhere in this record",
        ],
        "provenance": provenance_block(),
    }
    phase25_run.atomic_write_json(CLIP_CALIBRATION_RECORD, blob)
    print(f"[phase25_calibrate] wrote {_rel(CLIP_CALIBRATION_RECORD)}", flush=True)
    return blob


def early_window_bias(full, capacity):
    """How far the first :data:`EARLY_WINDOW_STEPS` steps' distribution sits from the full run's.

    THE FINDING THAT FORCED THIS PLAN'S FULL RUNS, kept in the record at both capacities so it
    survives its own correction. Applying the SAME ``clip_norm_rule`` quantile to a capacity's
    first ``EARLY_WINDOW_STEPS`` optimizer steps and then to its whole run measures directly how
    much a truncated window moves the derived ``C``. Both numbers are recorded; neither is
    averaged into the other and only the FULL-RUN reading feeds ``clip_norm_candidate``.
    """
    prefix_values = sorted(value for step in full["by_step"][:EARLY_WINDOW_STEPS] for value in step)
    prefix_candidate, _ = _order_statistic(prefix_values, CLIP_NORM_RULE_QUANTILE)
    full_candidate, _ = _order_statistic(full["values"], CLIP_NORM_RULE_QUANTILE)
    return {
        "capacity": capacity,
        "window_optimizer_steps": EARLY_WINDOW_STEPS,
        "full_optimizer_steps": full["optimizer_steps"],
        "window_n_records": len(prefix_values),
        "full_n_records": full["n_records"],
        "candidate_over_window": prefix_candidate,
        "candidate_over_full_run": full_candidate,
        "absolute_difference": abs(prefix_candidate - full_candidate),
        "relative_difference": (
            abs(prefix_candidate - full_candidate) / full_candidate if full_candidate else None
        ),
        "window_over_full_ratio": (prefix_candidate / full_candidate if full_candidate else None),
        "rule": (
            "the same clip_norm_rule quantile applied to this capacity's first "
            "EARLY_WINDOW_STEPS optimizer steps and then to its full run. Gradient norms fall as "
            "the loss drops, so an early window OVERSTATES them; at fixed sigma an oversized C is "
            "pure excess noise (std = sigma * C) bought for nothing, since epsilon does not "
            "depend on C. Only the FULL-RUN reading feeds clip_norm_candidate"
        ),
    }


# =================================================================================================
# ===== (d) D-14 — THE TIMED 768-DRAW ADVERSARIAL THROUGHPUT PROBE, AT BOTH EXTREMES =====
# =================================================================================================

THROUGHPUT_ARM = "adv_n8"

ADVERSARIAL_EXTREMES = (
    min(mitigation_budget.ADVERSARIAL_RATIO_GRID),
    max(mitigation_budget.ADVERSARIAL_RATIO_GRID),
)
"""The two ends of ``mitigation_budget.ADVERSARIAL_RATIO_GRID``, resolved by import.

``(0.0, 1.9090909090909092)``. Read from the pin rather than typed: the grid is the thing being
bracketed and a retyped extreme would be a second source of truth for the same two numbers.
"""

RATIO_ZERO_TOKEN_BIN_SHA256 = "f146d42637c69e9eb1e7ac2248c9056a7966aed48f6498fa9cdb6d3db02d147b"
RATIO_ZERO_MASK_BIN_SHA256 = "a2c4771f92aa4e03127e451b1de880b9386bee5164ee512d291467c1eb1e59a2"
"""24-06's committed digests for the ratio-0.0 build, reused rather than re-derived.

Ratio 0.0 is the seam-off twin of the matched comparator: ``build_bins(..., adversarial_ratio=0.0)``
is byte-identical to the no-kwarg build, and 24-06 recorded that pair as 176 episodes / 7,581
tokens under these two digests. Asserting the identity HERE is what makes the anchor comparison a
proof rather than an assumption — the probe's ratio-0.0 leg is only comparable to the committed
non-DP 161.124 s/point if it trained on the same corpus that figure describes.
"""

ANCHOR_RECORD = "results/phase23_cost.json"

ANCHOR_NON_DP_SECONDS_PER_POINT = 161.124
"""D-14's anchor, at the THREE-DECIMAL rounding CONTEXT and D-14 both spell.

``results/phase23_cost.json``'s own field carries the full double
``161.12400419991462``; the record below carries BOTH and asserts the rounding live, so the
pinned figure and the source measurement can never diverge silently.
"""

ANCHOR_ROUNDING_DECIMALS = 3

RATE_DIVERGENCE_TOLERANCE = 0.10
"""The relative gap above which the two extremes are declared NOT to share one throughput curve.

10%, and the number is bounded by measurement rather than chosen blind:
``results/phase23_cost.json``'s own ``cross_validation_vs_phase18`` block reports per-shape
agreement against Phase 18's committed rates spanning 95.06% to 106.32% — a +-6.3% band for the
SAME adapter measured on two occasions. A tolerance inside that band would flag re-measurement
noise as curve shape. 10% is the smallest round figure that clears it.

**IF THE GAP EXCEEDS IT, BOTH NUMBERS ARE RECORDED AND NEITHER IS AVERAGED.** D-14's whole point
is that a schedule extrapolated from one extreme and presented as measured is a repudiation risk.
"""

CONTEXT_ENVELOPE_HOURS = {"measured": 107.0, "ceiling": 150.0}
"""25-CONTEXT's stated envelope, quoted so the re-derived total can be compared to it in the
record rather than in prose. ``~150 h at the ceiling / ~107 h at the measured rate``."""


def _probe_conditions(model_pack, base_pack):
    """The THREE conditions ``results/phase23_cost.json``'s 768 is composed of, reproduced.

    MEASURED CORRECTION TO THE PLAN'S PROSE, stated here because the number is load-bearing.
    25-11-PLAN describes the bracket as *"8 strided prompts x 8 draws x 4 attack shapes x 2
    conditions after 4 warm-up draws discarded per condition"*. That is ``8 x 8 x 4 x 2 = 512``,
    not 768. ``results/phase23_cost.json`` composes ``n_draws_measured`` as
    ``floor_total + ceiling_total + base_total`` — **THREE** conditions x 4 shapes x 64 draws =
    **768** — and its own ``warmup_draws_discarded_per_shape`` field records the warm-up as per
    SHAPE, not per condition. The three-condition composition is reproduced, so this record's 768
    is CAL-05's own 768 and the two are comparable term by term.

    The third condition is not filler. It is the UN-ADAPTED base under the floor stop condition,
    and it is what makes the first two interpretable: the two extremes are probed at different
    wall-clock times, so a base leg in each tells a genuine curve-shape difference apart from the
    machine having moved between them.
    """
    import phase14_recall as recall

    adapted_model, adapted_tok, adapted_forbid = model_pack
    base_model, base_tok, base_forbid = base_pack
    return (
        ("floor", adapted_model, adapted_tok, adapted_forbid, recall.STOP_IDS),
        ("ceiling", adapted_model, adapted_tok, adapted_forbid, frozenset()),
        ("base_floor", base_model, base_tok, base_forbid, recall.STOP_IDS),
    )


def train_extreme(ratio, *, seed=1337):
    """Train one ``adv_n8`` extreme under :data:`CALIBRATION_PREFIX`. Returns its outputs + timing.

    At ratio 0.0 the bins are asserted byte-identical to 24-06's committed digests BEFORE the
    training clock is read, so the anchor's corpus identity is proved rather than assumed.
    """
    import phase23_run
    import teach_persona as tp

    facts, second_person, replay_ratio = tp.arm_spec(THROUGHPUT_ARM)
    paths = tp.arm_outputs(THROUGHPUT_ARM, prefix=CALIBRATION_PREFIX)
    _release_calibration_targets(THROUGHPUT_ARM, paths)

    box = {}
    with phase23_run.synchronized_seconds(box):
        record = tp.train_arm(
            THROUGHPUT_ARM,
            facts=facts,
            family_ids=_taught_family_ids(),
            second_person=second_person,
            replay_ratio=replay_ratio,
            adversarial_ratio=ratio,
            seed=seed,
            prefix=CALIBRATION_PREFIX,
        )
    seconds = box["seconds"]

    bins = {
        "token_bin": _rel(paths["bin"]),
        "token_bin_sha256": sha256_of(paths["bin"]),
        "mask_bin": _rel(paths["mask"]),
        "mask_bin_sha256": sha256_of(paths["mask"]),
    }
    identity = None
    if ratio == 0.0:
        matches = (
            bins["token_bin_sha256"] == RATIO_ZERO_TOKEN_BIN_SHA256
            and bins["mask_bin_sha256"] == RATIO_ZERO_MASK_BIN_SHA256
        )
        identity = {
            "asserted": True,
            "matches_24_06_digests": matches,
            "expected_token_bin_sha256": RATIO_ZERO_TOKEN_BIN_SHA256,
            "expected_mask_bin_sha256": RATIO_ZERO_MASK_BIN_SHA256,
            "measured_token_bin_sha256": bins["token_bin_sha256"],
            "measured_mask_bin_sha256": bins["mask_bin_sha256"],
            "why": (
                "ratio 0.0 is the seam-off twin of the matched comparator; 24-06 recorded these "
                "digests for the byte-identical no-kwarg build. The anchor comparison against "
                "the committed non-DP 161.124 s/point is only meaningful if this leg trained on "
                "that same corpus"
            ),
        }
        _prove(
            matches,
            "the ratio-0.0 adv_n8 bins do NOT hash to 24-06's committed digests "
            f"(token {bins['token_bin_sha256']} vs {RATIO_ZERO_TOKEN_BIN_SHA256}, mask "
            f"{bins['mask_bin_sha256']} vs {RATIO_ZERO_MASK_BIN_SHA256}). The anchor's corpus "
            "identity is the thing this leg exists to prove, and an unproved anchor makes the "
            "162 s comparison a claim about two different corpora",
        )

    adapter = paths["adapter"]
    _prove(adapter.exists(), f"{_rel(adapter)} was not exported — the arm did not complete")
    return {
        "ratio": ratio,
        "arm": THROUGHPUT_ARM,
        "seed": seed,
        "prefix": CALIBRATION_PREFIX,
        "training_seconds_per_point": seconds,
        "training_seconds_bracket": (
            "phase23_run.synchronized_seconds over the WHOLE train_arm call — build_arm_bins + "
            "base load + the max_steps-step loop + both end-of-run masked_perplexity sweeps. "
            "results/phase23_cost.json's training block brackets exactly the same span, which is "
            "what makes the two figures comparable"
        ),
        "final_train_loss": record.get("final_train_loss"),
        "adapter": _rel(adapter),
        "adapter_sha256": sha256_of(adapter),
        "bins": bins,
        "bins_byte_identity": identity,
        "adversarial_stats": {
            key: value
            for key, value in (record.get("stats") or {}).items()
            if key.startswith("adversarial") or key in ("episodes", "tokens", "teaching_tokens")
        },
    }, paths


def probe_extreme_throughput(paths):
    """768 timed draws over four shapes and three conditions for ONE extreme's adapter.

    Reuses ``phase23_run._measure_condition`` — CAL-05's own bracket, the same
    ``phase14_recall.draw_all`` primitive ``phase25_run._draw_one_shape`` calls, the same
    ``phase18_extraction._smoke_sample`` strided prompts and the same 4 discarded warm-up draws
    per shape. Reusing it is what makes ``n_draws_measured`` here the SAME denominator
    ``results/phase23_cost.json`` published its rates over.
    """
    import phase14_factset as fs
    import phase14_recall as recall
    import phase16_persistence as persistence
    import phase17_persona_gate as base_gate
    import phase18_extraction as x18
    import phase23_run
    import teach_persona as tp

    from personacore.tokenizer import from_json

    tok = from_json(recall.TOKENIZER_PATH)
    corpus = x18.build_corpus(tok)
    by_family = {}
    for entry in corpus["prompts"]:
        by_family.setdefault(entry["family"], []).append(entry)
    values = [fact.value for fact in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS]

    adapted_model, _cfg, adapted_tok, adapted_forbid, _artifact = recall.load_adapted_model(
        tp.device(), paths["adapter"]
    )
    base_model, base_cfg, _base_ckpt = base_gate.build_unadapted_base(tp.device())
    base_forbid, _digest = persistence.resolve_forbid(tok, base_cfg.vocab_size)
    base_forbid = base_forbid.to(tp.device())

    by_condition = {}
    for label, model, condition_tok, forbid, stop_ids in _probe_conditions(
        (adapted_model, adapted_tok, adapted_forbid), (base_model, tok, base_forbid)
    ):
        started = time.time()
        shapes = phase23_run._measure_condition(
            label=label,
            model=model,
            tok=condition_tok,
            forbid=forbid,
            by_family=by_family,
            values=values,
            stop_ids=stop_ids,
        )
        by_condition[label] = {
            "shapes": {shape["shape"]: shape for shape in shapes},
            "wall_seconds": time.time() - started,
            "n_draws": sum(shape["n_draws"] for shape in shapes),
            "stop_terminated_n": sum(shape["stop_terminated_n"] for shape in shapes),
        }
        print(
            f"[phase25_calibrate] condition {label}: {by_condition[label]['n_draws']} draw(s), "
            f"{by_condition[label]['stop_terminated_n']} stop-terminated, "
            f"{by_condition[label]['wall_seconds'] / 60:.2f} min",
            flush=True,
        )
    del adapted_model, base_model

    per_shape = {}
    for family in x18.ATTACK_FAMILIES:
        blocks = {label: by_condition[label]["shapes"][family] for label in by_condition}
        n_draws = sum(block["n_draws"] for block in blocks.values())
        seconds = sum(block["minutes"] * 60.0 for block in blocks.values())
        per_shape[family] = {
            "shape": family,
            "prompts": blocks["floor"]["prompts"],
            "n_draws": n_draws,
            "seconds": seconds,
            "rate_draws_per_min": n_draws / (seconds / 60.0),
            "rate_is_pooled_over": sorted(blocks),
            "stop_terminated_n": sum(block["stop_terminated_n"] for block in blocks.values()),
            "by_condition": {
                label: {
                    "n_draws": block["n_draws"],
                    "seconds": block["minutes"] * 60.0,
                    "rate_draws_per_min": block["rate_draws_per_min"],
                    "stop_terminated_n": block["stop_terminated_n"],
                    "mean_tokens": block["mean_tokens"],
                }
                for label, block in blocks.items()
            },
        }

    total_draws = sum(block["n_draws"] for block in per_shape.values())
    return {
        "n_draws_measured": total_draws,
        "n_draws_composition": (
            "floor_total + ceiling_total + base_floor_total — results/phase23_cost.json's OWN "
            "composition of its n_draws_measured, reproduced: 3 conditions x "
            f"{len(x18.ATTACK_FAMILIES)} shapes x {x18.SMOKE_PROMPTS_PER_SHAPE} strided prompts "
            f"x {x18.SMOKE_DRAWS_PER_PROMPT} draws"
        ),
        "conditions": sorted(by_condition),
        "condition_definitions": {
            "floor": "the trained adapter with phase14_recall.STOP_IDS ACTIVE — Phase 18's own",
            "ceiling": (
                "the trained adapter with the stop set EMPTIED, so every draw runs the full token "
                "budget. The worst case an adapter that stops emitting EOS produces"
            ),
            "base_floor": (
                "the UN-ADAPTED base under the floor condition. Not filler: the two extremes are "
                "probed at different wall-clock times, so a base leg in each is what tells a real "
                "curve-shape difference apart from the machine having moved between them"
            ),
        },
        "warmup_draws_discarded_per_shape": phase23_run._WARMUP_DRAWS,
        "timed_draws_per_shape_per_condition": (
            x18.SMOKE_PROMPTS_PER_SHAPE * x18.SMOKE_DRAWS_PER_PROMPT
        ),
        "per_shape": per_shape,
        "per_condition_totals": {
            label: {
                "n_draws": block["n_draws"],
                "wall_seconds": block["wall_seconds"],
                "stop_terminated_n": block["stop_terminated_n"],
                "rate_draws_per_min": sum(shape["n_draws"] for shape in block["shapes"].values())
                / (sum(shape["minutes"] for shape in block["shapes"].values())),
            }
            for label, block in by_condition.items()
        },
        "draw_primitive": (
            "phase14_recall.draw_all through phase23_run._measure_condition — the SAME primitive "
            "phase25_run._draw_one_shape calls, so this rate describes the code path the sweep "
            "will actually run"
        ),
    }


def _projected_hours_at_k(per_shape_rates, *, slowest_rate, k, questions_per_shape, cost):
    """``results/phase18_preflight_report.md``'s own projection method, applied to MEASURED rates.

    Per-shape minutes summed, plus family zero priced at the SLOWEST measured rate — the same
    composition ``results/phase23_cost.json`` states in its ``h_per_point_composition`` field, so
    the two projections are comparable term by term rather than only in magnitude.
    """
    minutes = sum(questions_per_shape[shape] * k / rate for shape, rate in per_shape_rates.items())
    family_zero = (
        cost["generation"]["family_zero_prompts"]
        * (cost["generation"]["family_zero_draws_per_prompt"])
    )
    minutes += family_zero / slowest_rate
    return minutes / 60.0


def run_throughput_probe(*, seed=1337):
    """D-14, end to end. Writes :data:`THROUGHPUT_RECORD` and returns the blob."""
    import phase18_extraction as x18

    cost = _read_json(ANCHOR_RECORD)
    anchor_full = float(cost["ratios"]["non_dp"]["training_seconds_per_point"])
    _prove(
        round(anchor_full, ANCHOR_ROUNDING_DECIMALS) == ANCHOR_NON_DP_SECONDS_PER_POINT,
        f"{ANCHOR_RECORD} carries non_dp training_seconds_per_point {anchor_full!r}, which does "
        f"not round to D-14's pinned {ANCHOR_NON_DP_SECONDS_PER_POINT!r} at "
        f"{ANCHOR_ROUNDING_DECIMALS} decimals. The anchor moved",
    )

    token_budget = _read_json("results/phase24_token_budget.json")

    extremes = {}
    probe_started = time.time()
    for ratio in ADVERSARIAL_EXTREMES:
        print(f"[phase25_calibrate] extreme ratio={ratio!r}: training", flush=True)
        trained, paths = train_extreme(ratio, seed=seed)
        print(
            f"[phase25_calibrate] extreme ratio={ratio!r}: trained in "
            f"{trained['training_seconds_per_point']:.1f} s — probing 768 draws",
            flush=True,
        )
        probe = probe_extreme_throughput(paths)
        extremes[repr(ratio)] = {**trained, **probe}
        _release_calibration_targets(THROUGHPUT_ARM, paths)
    probe_seconds = time.time() - probe_started

    keys = sorted(extremes)
    _prove(
        len(keys) == 2,
        f"the probe returned {len(keys)} extreme(s). D-14 requires BOTH before the schedule is "
        "committed and forbids extrapolating from one",
    )
    low, high = repr(ADVERSARIAL_EXTREMES[0]), repr(ADVERSARIAL_EXTREMES[1])

    divergence = _divergence(extremes, low, high)

    # The REAL per-shape question counts, from the live corpus geometry rather than from the
    # probe's strided sample: the projection prices every question in the shape, not the 8 timed
    # ones. `results/phase23_cost.json`'s `generation.questions` is the same corpus this probe
    # drew against, and its `per_shape` block names the four shapes it is split across.
    corpus_shapes = [row["shape"] for row in cost["generation"]["per_shape"]]
    _prove(
        cost["generation"]["questions"] % len(corpus_shapes) == 0,
        f"{cost['generation']['questions']} corpus question(s) do not divide evenly across "
        f"{len(corpus_shapes)} shape(s); the per-shape denominator would be a rounding",
    )
    questions_per_shape = {
        shape: cost["generation"]["questions"] // len(corpus_shapes) for shape in corpus_shapes
    }

    schedule = _schedule(
        extremes=extremes,
        low=low,
        high=high,
        cost=cost,
        questions_per_shape=questions_per_shape,
        divergence=divergence,
        probe_seconds=probe_seconds,
    )

    blob = {
        "measures": (
            "D-14: adversarial SCORING throughput at BOTH extremes of "
            "mitigation_budget.ADVERSARIAL_RATIO_GRID, 768 timed draws each, plus both extremes' "
            "training legs. This is a RESOURCE measurement — no gate threshold is read, chosen or "
            "approached"
        ),
        "extremes": extremes,
        "extreme_ratios": list(ADVERSARIAL_EXTREMES),
        "extreme_ratios_source": "mitigation_budget.ADVERSARIAL_RATIO_GRID min and max, by import",
        "anchor": {
            "non_dp_training_seconds_per_point": ANCHOR_NON_DP_SECONDS_PER_POINT,
            "non_dp_training_seconds_per_point_full": anchor_full,
            "non_dp_training_seconds_per_point_rounding": (
                f"D-14 and 25-CONTEXT both spell the anchor at {ANCHOR_ROUNDING_DECIMALS} "
                f"decimals ({ANCHOR_NON_DP_SECONDS_PER_POINT}); {ANCHOR_RECORD} carries the full "
                f"double ({anchor_full}). BOTH are recorded and the rounding is asserted live, so "
                "the pinned figure and the source measurement cannot diverge silently"
            ),
            "source_record": ANCHOR_RECORD,
            "source_record_sha256": sha256_of(_ROOT / ANCHOR_RECORD),
            "source_field": "ratios.non_dp.training_seconds_per_point",
            "measured_ratio_zero_training_seconds": extremes[low]["training_seconds_per_point"],
            "measured_ratio_zero_over_anchor": (
                extremes[low]["training_seconds_per_point"] / anchor_full
            ),
            "why_ratio_zero_anchors": (
                "ratio 0.0 is the seam-off twin of the matched comparator and its bins are proved "
                "byte-identical to 24-06's committed digests in this record's own "
                "extremes['0.0'].bins_byte_identity block, so the comparison is between two "
                "readings of the same corpus rather than between two corpora"
            ),
        },
        "divergence": divergence,
        "schedule": schedule,
        "why_the_extremes_may_not_share_a_curve": {
            "record": "results/phase24_token_budget.json",
            "record_sha256": sha256_of(_ROOT / "results" / "phase24_token_budget.json"),
            "cross_family_inflation": token_budget["token_budget_disclosure"].get(
                "cross_family_inflation"
            ),
            "multiplicity_at_upper_extreme": token_budget["token_budget_disclosure"].get(
                "multiplicity_at_upper_extreme"
            ),
            "note": (
                "the upper extreme reuses the trained adversarial pool with a multiplicity that "
                "reaches 8.0x at adv_n64, so the two extremes' adapters are not two settings of "
                "one dial in any sense that guarantees one throughput curve. That is why D-14 "
                "requires both probed and forbids extrapolating from one"
            ),
        },
        "probe_wall_seconds": probe_seconds,
        "attack_shapes": list(x18.ATTACK_FAMILIES),
        "curve_k": mitigation_budget.CURVE_K,
        "curve_k_source": "mitigation_budget.CURVE_K",
        "provenance": provenance_block(),
    }
    phase25_run.atomic_write_json(THROUGHPUT_RECORD, blob)
    print(f"[phase25_calibrate] wrote {_rel(THROUGHPUT_RECORD)}", flush=True)
    return blob


def _divergence(extremes, low, high):
    """The two extremes' rates, side by side, CONDITION-MATCHED. **No average is taken.**"""
    per_condition = {}
    for label in extremes[low]["per_condition_totals"]:
        low_rate = extremes[low]["per_condition_totals"][label]["rate_draws_per_min"]
        high_rate = extremes[high]["per_condition_totals"][label]["rate_draws_per_min"]
        per_condition[label] = {
            "rate_draws_per_min_at_low_extreme": low_rate,
            "rate_draws_per_min_at_high_extreme": high_rate,
            "relative_gap": abs(low_rate - high_rate) / max(low_rate, high_rate),
            "exceeds_tolerance": (
                abs(low_rate - high_rate) / max(low_rate, high_rate) > RATE_DIVERGENCE_TOLERANCE
            ),
        }
    exceeds = sorted(label for label, row in per_condition.items() if row["exceeds_tolerance"])
    return {
        "tolerance": RATE_DIVERGENCE_TOLERANCE,
        "tolerance_source": (
            "results/phase23_cost.json's cross_validation_vs_phase18 block reports per-shape "
            "agreement against Phase 18's committed rates spanning 95.06% to 106.32% for the SAME "
            "adapter measured on two occasions. A tolerance inside that +-6.3% band would flag "
            "re-measurement noise as curve shape; 10% is the smallest round figure that clears it"
        ),
        "per_condition": per_condition,
        "conditions_exceeding_tolerance": exceeds,
        "curve_is_flat_within_tolerance": not exceeds,
        "no_average_taken": (
            "the two extremes' rates are recorded SEPARATELY and condition-matched. No field in "
            "this record is their mean, and tests/test_phase25_calibrate.py asserts that by "
            "walking every numeric value in the record"
        ),
    }


def _schedule(*, extremes, low, high, cost, questions_per_shape, divergence, probe_seconds):
    """The full 44-point envelope as a SUM OF NAMED TERMS. Finalised after BOTH extremes returned.

    Every term carries its own hours, its own rule and whether it is MEASURED or PROJECTED. No
    term is hidden inside a total, and the two extremes are never averaged into one figure.
    """
    k = mitigation_budget.CURVE_K
    sizing = cost["sizing"][str(k)]

    adversarial = {}
    for label, key in (("low", low), ("high", high)):
        extreme = extremes[key]
        rates_floor = {
            shape: block["by_condition"]["floor"]["rate_draws_per_min"]
            for shape, block in extreme["per_shape"].items()
        }
        rates_ceiling = {
            shape: block["by_condition"]["ceiling"]["rate_draws_per_min"]
            for shape, block in extreme["per_shape"].items()
        }
        adversarial[key] = {
            "extreme": label,
            "ratio": extreme["ratio"],
            "h_per_point_floor_at_k": _projected_hours_at_k(
                rates_floor,
                slowest_rate=min(rates_floor.values()),
                k=k,
                questions_per_shape=questions_per_shape,
                cost=cost,
            ),
            "h_per_point_ceiling_at_k": _projected_hours_at_k(
                rates_ceiling,
                slowest_rate=min(rates_ceiling.values()),
                k=k,
                questions_per_shape=questions_per_shape,
                cost=cost,
            ),
            "rate_draws_per_min_floor": rates_floor,
            "rate_draws_per_min_ceiling": rates_ceiling,
            "training_seconds_per_point": extreme["training_seconds_per_point"],
        }

    # The adversarial leg is bracketed by the two extremes' OWN projections — the cheaper end
    # bounds below, the dearer end above. Neither is averaged into the other.
    adv_floor_hours = [adversarial[key]["h_per_point_floor_at_k"] for key in (low, high)]
    adv_ceiling_hours = [adversarial[key]["h_per_point_ceiling_at_k"] for key in (low, high)]
    adv_points = len(mitigation_budget.ADVERSARIAL_RATIO_GRID) * 2
    dp_points = mitigation_budget.SWEEP_POINTS * 2

    dp_training_seconds = mitigation_budget.SWEEP_POINTS * (
        cost["training"]["dp_n8"]["seconds_total"] + cost["training"]["dp_n64"]["seconds_total"]
    )
    n64_over_n8 = (
        cost["training"]["dp_n64"]["seconds_total"] / cost["training"]["dp_n8"]["seconds_total"]
    )
    adv_training_seconds = sum(
        len(mitigation_budget.ADVERSARIAL_RATIO_GRID)
        * adversarial[key]["training_seconds_per_point"]
        / 2.0
        * (1.0 + n64_over_n8)
        for key in (low, high)
    )

    matched_floor_seconds = 5 * (23.1 * 60.0 + 16.6 * 60.0)
    condition_c_seconds = 44 * 87.4

    terms = [
        {
            "term": "dp_scoring_44_points",
            "measured": False,
            "hours_floor": dp_points * sizing["h_per_point_floor_at_k"],
            "hours_ceiling": dp_points * sizing["h_per_point_ceiling_at_k"],
            "rule": (
                f"{dp_points} DP points (mitigation_budget.SWEEP_POINTS x 2 capacities) x "
                f"results/phase23_cost.json sizing['{k}'] h_per_point_"
                "{floor,ceiling}_at_k "
                f"({sizing['h_per_point_floor_at_k']} / {sizing['h_per_point_ceiling_at_k']})"
            ),
        },
        {
            "term": "adversarial_scoring_12_points",
            "measured": True,
            "hours_floor": adv_points * min(adv_floor_hours),
            "hours_ceiling": adv_points * max(adv_ceiling_hours),
            "rule": (
                f"{adv_points} adversarial points (len(ADVERSARIAL_RATIO_GRID) x 2 capacities) "
                "bracketed by THIS PROBE's two extremes: the floor bound uses the cheaper "
                f"extreme's measured floor projection ({min(adv_floor_hours)} h/point) and the "
                f"ceiling bound the dearer extreme's ceiling projection ({max(adv_ceiling_hours)} "
                "h/point). The two extremes are NEVER averaged; the bracket is built from both"
            ),
        },
        {
            "term": "dp_training_32_points",
            "measured": True,
            "hours_floor": dp_training_seconds / 3600.0,
            "hours_ceiling": dp_training_seconds / 3600.0,
            "rule": (
                f"{mitigation_budget.SWEEP_POINTS} x "
                f"{cost['training']['dp_n8']['seconds_total']} s (dp_n8) + "
                f"{mitigation_budget.SWEEP_POINTS} x "
                f"{cost['training']['dp_n64']['seconds_total']} s (dp_n64), both from "
                "results/phase23_cost.json's training block"
            ),
        },
        {
            "term": "adversarial_training_12_points",
            "measured": False,
            "hours_floor": adv_training_seconds / 3600.0,
            "hours_ceiling": adv_training_seconds / 3600.0,
            "rule": (
                "this probe measured adv_n8 at BOTH extremes; adv_n64 training was not measured "
                "here. Each extreme's measured adv_n8 seconds is applied to half the 12 points "
                f"and the n=64 half is scaled by the committed dp_n64/dp_n8 ratio {n64_over_n8}. "
                "PROJECTED, not measured, and labelled so"
            ),
        },
        {
            "term": "d03_n64_matched_control_floor",
            "measured": False,
            "hours_floor": matched_floor_seconds / 3600.0,
            "hours_ceiling": matched_floor_seconds / 3600.0,
            "rule": (
                "D-03: 5 seeds x (23.1 min training + 16.6 min recall scoring) — 25-CONTEXT's own "
                "figure, restated as its own line rather than folded into a total"
            ),
        },
        {
            "term": "condition_c_44_points",
            "measured": False,
            "hours_floor": condition_c_seconds / 3600.0,
            "hours_ceiling": condition_c_seconds / 3600.0,
            "rule": (
                "D-45: 44 points x 87.4 s (dialogue_ppl_pair 43.5 s + retention_perplexity 43.9 "
                "s), timed at HEAD on MPS. 25-CONTEXT's own measurement, restated as its own line"
            ),
        },
        {
            "term": "never_taught_floor",
            "measured": True,
            "hours_floor": 0.0,
            "hours_ceiling": 0.0,
            "rule": (
                "D-19: BOTH arms read the SAME already-measured never-taught floor "
                "(results/phase23_never_taught.json, 0/416 at 5 seeds). No new hours"
            ),
        },
        {
            "term": "this_plan_calibration_probes",
            "measured": True,
            "hours_floor": probe_seconds / 3600.0,
            "hours_ceiling": probe_seconds / 3600.0,
            "rule": (
                "the wall clock this throughput probe actually spent — both extremes' training "
                "legs plus 2 x 768 timed draws. The clip-calibration probe's own seconds are in "
                "results/phase25_clip_calibration.json's probe.timings block"
            ),
        },
    ]

    total_floor = sum(term["hours_floor"] for term in terms)
    total_ceiling = sum(term["hours_ceiling"] for term in terms)

    return {
        "finalised_after": "both extremes",
        "finalised_after_detail": (
            "the schedule below was assembled only after BOTH "
            f"{ADVERSARIAL_EXTREMES[0]!r} and {ADVERSARIAL_EXTREMES[1]!r} returned 768 timed "
            "draws each. It is NOT an extrapolation from one extreme, and the adversarial "
            "scoring term is bracketed by both extremes' own projections rather than by either "
            "one alone"
        ),
        "curve_k": k,
        "curve_k_source": "mitigation_budget.CURVE_K",
        "points": {
            "dp": dp_points,
            "adversarial": adv_points,
            "total": dp_points + adv_points,
        },
        "per_extreme": adversarial,
        "terms": terms,
        "total_hours_floor": total_floor,
        "total_hours_ceiling": total_ceiling,
        "totals_rule": (
            "total_hours_{floor,ceiling} is the SUM of the terms above and nothing else. Every "
            "term carries its own hours, its own rule and its measured/projected flag, so no term "
            "is hidden inside a total"
        ),
        "context_envelope": dict(CONTEXT_ENVELOPE_HOURS),
        "context_envelope_source": (
            "25-CONTEXT <domain>: '44 sweep points, ~150 h at the ceiling / ~107 h at the "
            "measured rate'"
        ),
        "reproduces_context_envelope": {
            "floor_within_context_measured": abs(total_floor - CONTEXT_ENVELOPE_HOURS["measured"])
            / CONTEXT_ENVELOPE_HOURS["measured"],
            "ceiling_within_context_ceiling": abs(total_ceiling - CONTEXT_ENVELOPE_HOURS["ceiling"])
            / CONTEXT_ENVELOPE_HOURS["ceiling"],
            "note": (
                "relative gaps between this re-derived envelope and 25-CONTEXT's stated one. The "
                "numbers are recorded whether or not they reproduce; nothing here is adjusted to "
                "make them agree"
            ),
        },
        "divergence_finding": {
            "curve_is_flat_within_tolerance": divergence["curve_is_flat_within_tolerance"],
            "conditions_exceeding_tolerance": divergence["conditions_exceeding_tolerance"],
            "note": (
                "recorded as a finding with BOTH numbers per condition in this record's own "
                "divergence block. No average is taken across the two extremes anywhere"
            ),
        },
    }


# =================================================================================================
# ===== (e) CLI =====
# =================================================================================================


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "mode",
        choices=("clip-calibration", "throughput", "refusals"),
        help=(
            "clip-calibration: D-24's per-record norm probe. throughput: D-14's 768-draw probe at "
            "both extremes. refusals: print the four clip-domain refusals (CPU, no model)"
        ),
    )
    parser.add_argument("--seed", type=int, default=1337)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.mode == "refusals":
        for label, captured in clip_domain_refusals().items():
            print(f"--- clip_norm={label} ({captured['seconds'] * 1000:.4f} ms) ---")
            print(captured["message"])
        return 0
    if args.mode == "clip-calibration":
        run_clip_calibration(seed=args.seed)
        return 0
    run_throughput_probe(seed=args.seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
