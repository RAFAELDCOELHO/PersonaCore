"""PLAN 25-14 DEVIATION — THE PER-POINT RESOLVER `scripts/phase25_run.py` NEVER HAD.

MEASURED 2026-09-04, at the launch checkpoint, before any GPU second: `phase25_run.run_point`
read ``record_fields["training"]``, ``["drawing"]``, ``["values"]`` and ``["record"]`` from its
``**record_fields``, and `phase25_run.main` called it with NONE of them — so the live path raised
``KeyError`` on the first non-dry-run point, and every one of the 44 points would have failed
after `prove_first_attempt`. The 23 committed driver tests all take the ``--dry-run`` branch (the
same blind spot that hid ``tp.device()`` in plan 25-11). Nothing in the phase produced the twenty
`build_point_record` kwargs per point, and nothing produced the control's `taught_recall` /
`reproduction_gate` fields plan 25-15 verifies. This module is that producer.

WHAT IT OWNS, AND WHAT IT DOES NOT. It resolves the pre-registered constants of one point into
the kwargs the existing stages need (`point_plan`), runs the training leg through the single
production entry ``teach_persona.train_arm`` while capturing the DP seam exactly as
`phase23_run.captured_dp_seam` does (`train_stage`), takes the per-point readings that need the
trained adapter and a loaded model — condition (c), GATE-05, and the control's recall
(`measure_stage`) — and assembles `build_point_record`'s kwargs (`record_kwargs`). The draw loop,
the scorer, the record writer and the git surface stay where plans 25-08/25-10 put them; this
module runs NO git command (the AST gate over `phase25_run` is the one that bounds the surface).

RESUME IS PER STAGE AND EVERY STAGE OUTPUT IS A SIDECAR UNDER ``data/``. A kill during the draw
leg must not cost the 23-minute training leg, and a kill during the draws of the control must not
cost its 16-minute recall scoring. So the training and measurement stages each persist their
result atomically under the gitignored ``data/`` keyed by the adapter's sha256, and a relaunch
reuses them only if the adapter on disk still hashes to what the sidecar recorded. The training
leg itself resumes through 23-07's checkpoint seam when ``latest.pt`` exists and no adapter does.

THE FOUR DECISIONS THIS MODULE HAD TO MAKE, stated so they cannot look like accidents:

  1. PREFIX PER POINT. `teach_persona.arm_outputs` scopes ``csv``/``checkpoint``/``adapter`` by
     prefix and the sixteen sigma points of one arm would otherwise share one adapter path. The
     prefix is ``phase25_<axis><value>`` — the point key minus its arm — so the control keeps arm
     identity ``dp_n8``/``dp_n64`` and is separated from the calibration runs by PREFIX ONLY (D-06).
  2. THE ADVERSARIAL ARM HAS NO DP SEAM, so its "live mechanism" carries ``q: null`` and
     ``clip_norm: null`` on BOTH sides of D-34's pin — the structural statement that it makes no
     formal claim (D-31's ``accounting: null``, restated at the mechanism). Its step count is read
     off its own final checkpoint and its lot is the ``TrainConfig`` the run constructed.
  3. `seed_spread` (D-50) is read from `results/phase25_n64_matched_floor.json`, which
     `scripts/phase25_n64_floor.py` produces BEFORE the first point: the sweep is single-seed per
     point, and the only multi-seed v4.0-recipe adapters in this phase are D-03's five.
  4. `control_gap` (D-47) is the point's own reading at a control and the TRACKED control record's
     reading everywhere else — read through `git ls-files`' result handed in by the driver, so a
     control that has not been committed cannot be borrowed from the working tree.
"""

import hashlib
import json
import pathlib
import shutil
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import mitigation_budget  # noqa: E402  (scripts/ is not a package)
import mitigation_unit  # noqa: E402  (same)
import phase25_condition_c  # noqa: E402  (same)
import phase25_epsilon  # noqa: E402  (same)
import phase25_gate05  # noqa: E402  (same)
import phase25_prereg  # noqa: E402  (same)
import phase25_record  # noqa: E402  (same)

SWEEP_SEED = phase25_prereg.REPRODUCTION_PROVENANCE["seed"]

# The one calibration prefix this phase already uses; a sweep prefix must never resolve under it.
CALIBRATION_PREFIX_LITERAL = "phase25_calibration"

N64_FLOOR_RECORD = _ROOT / "results" / "phase25_n64_matched_floor.json"
TOKEN_BUDGET_RECORD = _ROOT / "results" / "phase24_token_budget.json"

SCORING_JUSTIFICATION = (
    "This extraction reading exists because under CTRL-02 the control is a sweep point and under "
    "FRONT-03 every point owes per-question counts, and because the control anchors the "
    "privacy x utility plane — NOT because the gate requires it. The gate's control anchors are "
    "`control_extraction_successes` / `control_extraction_questions`, which feed "
    "`mitigation_gate.extraction_ceiling`; that function proves "
    "`extraction_floor_provenance['arm'] == mitigation_gate.NEVER_TAUGHT_ARM`, so the values the "
    "gate consumes are the never-taught arm's 0/416 and the gate never reads this record's "
    "extraction."
)

ADVERSARIAL_MECHANISM_NOTE = (
    "The adversarial arm trains with NO DP seam: no DPSGD is constructed, so there is no "
    "per-record clip C, no noise multiplier and no sampling rate. `q` and `clip_norm` are null on "
    "BOTH sides of D-34's pin — the mechanism-level form of D-31's `accounting: null`. "
    "`composed_steps` is read off the run's own final checkpoint and the lot is the window count "
    "per optimizer step of the TrainConfig the run constructed (batch_size x grad_accum_steps)."
)

AXIS_TERMINUS = (
    "D-19: the adversarial axis terminates at the POOL CEILING — the largest ratio at which the "
    "whole trained adversarial pool is used exactly once — by construction, and never reaches the "
    "never-taught floor. Both arms are read against the SAME already-measured floor (0/416, 5 "
    "seeds) as the plane's shared lower-left reference."
)


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase25_points] {message}")


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rel(path):
    resolved = pathlib.Path(path).resolve()
    try:
        return str(resolved.relative_to(_ROOT))
    except ValueError:
        return str(resolved)


def exact_axis_value(arm, point_key):
    """The LADDER or GRID member this key names — never the six-decimal rendering.

    MEASURED 2026-09-04: `parse_point_key("adv_n8_ratio1p909091")` returns ``1.909091``, while the
    grid's member is ``1.9090909090909092``; training at the rendered value would build a
    different adversarial pool than the pre-registered corner. The key is a LABEL (D-31); the
    number the run consumes is the committed literal it renders from.
    """
    members = (
        mitigation_budget.SIGMA_LADDER if is_dp(arm) else mitigation_budget.ADVERSARIAL_RATIO_GRID
    )
    matches = [value for value in members if phase25_record.point_key(arm, value) == point_key]
    _prove(
        len(matches) == 1,
        f"{point_key!r} renders from {len(matches)} member(s) of the pinned ladder/grid; exactly "
        "one must, or the label names a point that is not pre-registered",
    )
    return matches[0]


# =================================================================================================
# ===== (a) THE STATIC PLAN — torch-free, resolvable for all 44 keys on CPU =====
# =================================================================================================


def n_facts_for(arm):
    """``dp_n8`` -> 8, ``adv_n64`` -> 64. Asserted equal to ``len(arm_spec(arm)[0])`` at train."""
    _prove(arm in phase25_record.ORDERED_ARMS, f"unknown arm {arm!r}")
    return int(arm.rsplit("_n", 1)[1])


def is_dp(arm):
    return arm in phase25_record.DP_ARMS


def control_key_for(arm):
    """The sigma=0 DP control AT THIS ARM'S CAPACITY — D-47's per-capacity `control_gap` source."""
    return phase25_record.point_key(f"dp_n{n_facts_for(arm)}", 0.0)


def prefix_for(point_key):
    """``dp_n8_sigma0p000000`` -> ``phase25_sigma0p000000``: the key minus its arm (decision 1)."""
    arm, _axis, _value = phase25_record.parse_point_key(point_key)
    prefix = f"phase25_{point_key[len(arm) + 1 :]}"
    _prove(
        not prefix.startswith(CALIBRATION_PREFIX_LITERAL),
        f"prefix {prefix!r} resolves under the calibration prefix; a sweep point would then be "
        "deletable by `_release_calibration_targets`",
    )
    return prefix


def pinned_mechanism(arm, axis_value):
    """D-34's pin for one point. DP: the five committed literals. Adversarial: decision 2."""
    steps = mitigation_budget.STEP_BUDGET
    if is_dp(arm):
        n = n_facts_for(arm)
        clip = mitigation_budget.CLIP_NORM
        if axis_value == 0.0:
            clip = mitigation_budget.CONTROL_CLIP_NORM
        return {
            "composed_steps": steps,
            "composed_lot_sizes": [n],
            "records_per_lot": n,
            "q": mitigation_unit.SAMPLING_RATE_Q,
            "clip_norm": clip,
        }
    return {
        "composed_steps": steps,
        "composed_lot_sizes": None,  # resolved against the live TrainConfig at train time
        "records_per_lot": None,
        "q": None,
        "clip_norm": None,
    }


def point_epsilon_and_accounting(arm, axis_value):
    """``(point_epsilon, accounting)`` — null/null at the control and on the adversarial arm."""
    if not is_dp(arm) or axis_value == 0.0:
        return None, None
    ladder = mitigation_budget.SIGMA_LADDER
    _prove(axis_value in ladder, f"sigma {axis_value!r} is not on SIGMA_LADDER")
    accountant_value = phase25_epsilon.point_epsilon_for_sigma(
        axis_value, steps=mitigation_budget.STEP_BUDGET, delta=mitigation_unit.DELTA
    )
    pinned = mitigation_budget.EPSILON_LADDER[ladder.index(axis_value)]
    # No bare epsilon reaches a string here (D-28's census): the two values are named by their
    # roles, and a divergence is reported as accountant-vs-ladder.
    recorded_twin = phase25_epsilon.LADDER_PLATFORM_TWINS.get(axis_value)
    _prove(
        phase25_epsilon.epsilon_agrees(pinned, accountant_value, sigma=axis_value),
        f"the accountant returns {accountant_value!r} at sigma {axis_value!r} while "
        f"EPSILON_LADDER pins {pinned!r} at that rung"
        + (f" (recorded platform twin {recorded_twin!r})" if recorded_twin is not None else "")
        + ". The ladder was committed BEFORE any point ran; a divergence here means the "
        "accountant or its inputs moved after the pin. Exact `==` against the pin or the "
        "recorded twin: the two rungs where macOS-libm and glibc differ by 4 ULP are named in "
        "`phase25_epsilon.LADDER_PLATFORM_TWINS`, and nothing wider is accepted",
    )
    accounting = {
        "rule": "basic composition over the noised DP points actually published (D-29)",
        "delta": mitigation_unit.DELTA,
        "q": mitigation_unit.SAMPLING_RATE_Q,
        "steps": mitigation_budget.STEP_BUDGET,
        "selection_accounted": phase25_epsilon.SELECTION_ACCOUNTED,
    }
    return accountant_value, accounting


def point_plan(point_key):
    """Everything about one point that is known BEFORE it runs. Torch-free."""
    arm, axis, _rendered = phase25_record.parse_point_key(point_key)
    axis_value = exact_axis_value(arm, point_key)
    epsilon, accounting = point_epsilon_and_accounting(arm, axis_value)
    dp = is_dp(arm)
    return {
        "point_key": point_key,
        "arm": arm,
        "axis": axis,
        "axis_value": axis_value,
        "is_dp": dp,
        "is_control": dp and axis_value == 0.0,
        "n_facts": n_facts_for(arm),
        "seed": SWEEP_SEED,
        "prefix": prefix_for(point_key),
        "dp_sigma": axis_value if dp else None,
        "dp_clip_norm": (
            None
            if not dp
            else mitigation_budget.CONTROL_CLIP_NORM
            if axis_value == 0.0
            else mitigation_budget.CLIP_NORM
        ),
        "adversarial_ratio": axis_value if not dp else 0.0,
        "pinned_mechanism": pinned_mechanism(arm, axis_value),
        "point_epsilon": epsilon,
        "accounting": accounting,
        "control_key": control_key_for(arm),
    }


def training_sidecar(point_key):
    return _ROOT / "data" / f"phase25_{point_key}_training.json"


def measure_sidecar(point_key):
    return _ROOT / "data" / f"phase25_{point_key}_measure.json"


def run_log_dir(point_key):
    return _ROOT / "data" / "phase25_runs" / point_key


def taught_mapping(facts):
    """GATE-05's ``taught`` for one point. Core facts keyed by SLOT, filler facts keyed by FACT ID.

    MEASURED 2026-09-04: `phase18_extraction.reference_set_for` REFUSES every slot outside the
    eight core ones ("a slot name that is not one of them is a typo"), and the 56 filler facts
    share eight filler slots (seven facts per slot) — so a slot-keyed mapping holds 16 entries at
    n=64, not 64, and no filler fact has an exposure reference set at all. Keying filler facts by
    id keeps `gate05_tier_slots`' ``len(taught) == n_facts`` proof honest; `measure_gate05` then
    records those entries as UNMEASURABLE with the reason rather than calling a scorer that refuses.
    """
    gated = set(phase25_gate05.GATE05_SLOTS)
    taught = {}
    for fact in facts:
        key = fact.slot if fact.slot in gated else fact.id
        _prove(key not in taught, f"taught key {key!r} appears twice — two facts collapse into one")
        taught[key] = fact.value
    return taught


def seed_spread():
    """D-50's input, from D-03's five n=64 adapters (decision 3). Refuses an absent record."""
    _prove(
        N64_FLOOR_RECORD.exists(),
        f"{_rel(N64_FLOOR_RECORD)} does not exist. D-50's counterfactual retention floor reads "
        "the sweep's own seed-to-seed retention spread, and the only multi-seed v4.0-recipe "
        "adapters in this phase are D-03's five (scripts/phase25_n64_floor.py). Run that leg "
        "BEFORE the first "
        "point; a sweep point record cannot be written without it",
    )
    record = json.loads(N64_FLOOR_RECORD.read_text(encoding="utf-8"))
    spread = list(record["retention"]["seed_spread"])
    _prove(spread and all(v >= 0 for v in spread), f"seed spread {spread!r} is empty or negative")
    return spread


def control_reading(arm, tracked):
    """The TRACKED control record's (adapter_on, adapter_off) at this capacity (decision 4)."""
    key = control_key_for(arm)
    relative = phase25_prereg.point_record_path(key)
    _prove(
        relative in set(tracked),
        f"the control record {relative} is not TRACKED (git ls-files), so `control_gap` for arm "
        f"{arm!r} cannot be read. D-47 takes each capacity's own committed sigma=0 control; a "
        "reading borrowed from the working tree or from the other capacity silently moves both "
        "edges of condition (c)'s dialogue band",
    )
    record = json.loads((_ROOT / relative).read_text(encoding="utf-8"))
    group = record["condition_c"]
    return {
        "adapter_on": group["point_dialogue_ppl_on"],
        "adapter_off": group["point_dialogue_ppl_off"],
    }


# =================================================================================================
# ===== (b) THE TRAINING STAGE — `train_arm`, seam captured, resumable, sidecar-persisted =====
# =================================================================================================


def _count_composed_steps(seam):
    """`phase23_run._count_composed_steps`, restated: shadow ``finalize`` per instance."""
    calls = []
    real = seam.finalize

    def counting(accum):
        calls.append(accum)
        return real(accum)

    seam.finalize = counting
    return calls


def train_stage(plan):
    """Train one point's adapter (or reuse / resume it) and return the training sidecar's blob."""
    import phase14_factset as fs
    import phase25_run
    import teach_persona as tp

    key, arm, prefix = plan["point_key"], plan["arm"], plan["prefix"]
    facts, second_person, replay_ratio = tp.arm_spec(arm)
    _prove(
        len(facts) == plan["n_facts"],
        f"arm_spec({arm!r}) carries {len(facts)} facts while the arm name says {plan['n_facts']}",
    )
    paths = tp.arm_outputs(arm, prefix=prefix)
    sidecar = training_sidecar(key)

    if sidecar.exists():
        blob = json.loads(sidecar.read_text(encoding="utf-8"))
        _prove(
            paths["adapter"].exists() and _sha256(paths["adapter"]) == blob["adapter_sha256"],
            f"{_rel(sidecar)} records adapter sha256 {blob['adapter_sha256']!r} but "
            f"{_rel(paths['adapter'])} is absent or hashes differently. The sidecar describes an "
            "adapter that is not the one on disk; delete both in a reviewed step to retrain",
        )
        print(f"[phase25_points] {key}: REUSING trained adapter from {_rel(sidecar)}", flush=True)
        return blob
    _prove(
        not paths["adapter"].exists(),
        f"{_rel(paths['adapter'])} exists but {_rel(sidecar)} does not, so the seam counters that "
        "run produced are gone and its live mechanism cannot be stated. Delete the adapter and "
        f"{_rel(paths['checkpoint'])} in a reviewed step; the point is still the SAME attempt "
        "because no record landed (D-10)",
    )

    resume_from, resumed_from_step = None, 0
    if paths["checkpoint"].exists():
        resume_from = paths["checkpoint"]
        resumed_from_step = int(tp.torch.load(resume_from, weights_only=False)["step"])
        print(
            f"[phase25_points] {key}: RESUMING from {_rel(resume_from)} at step "
            f"{resumed_from_step} (23-07's seam)",
            flush=True,
        )
    else:
        # The arm's bins carry NO prefix (`arm_outputs`' documented non-widening), so every point
        # of one arm shares them and `refuse_if_exists` would refuse the second point. They are
        # rebuilt deterministically from (facts, family_ids, second_person, replay_ratio, seed).
        for target in tp.arm_bin_targets(arm, paths) + [paths["csv"]]:
            pathlib.Path(target).unlink(missing_ok=True)

    real_dp, real_cfg = tp.DPSGD, tp.TrainConfig
    box = {"seam": None, "composed": None, "config": None}

    def dp_factory(model, **kwargs):
        _prove(box["seam"] is None, f"{key}: a SECOND DPSGD was constructed in one training leg")
        seam = real_dp(model, **kwargs)
        box["seam"] = seam
        box["composed"] = _count_composed_steps(seam)
        return seam

    def cfg_factory(**fields):
        _prove(box["config"] is None, f"{key}: a SECOND TrainConfig was constructed in one leg")
        box["config"] = real_cfg(**fields)
        return box["config"]

    tp.DPSGD, tp.TrainConfig = dp_factory, cfg_factory
    started = time.time()
    try:
        trained = tp.train_arm(
            arm,
            facts=facts,
            family_ids=fs.TAUGHT_FAMILY_IDS,
            second_person=second_person,
            replay_ratio=replay_ratio,
            adversarial_ratio=plan["adversarial_ratio"],
            seed=plan["seed"],
            prefix=prefix,
            dp_sigma=plan["dp_sigma"],
            dp_clip_norm=plan["dp_clip_norm"],
            resume_from=resume_from,
        )
    finally:
        tp.DPSGD, tp.TrainConfig = real_dp, real_cfg
    seconds = time.time() - started

    cfg = box["config"]
    _prove(cfg is not None, f"{key}: train_arm constructed no TrainConfig")
    _prove(paths["checkpoint"].exists(), f"{key}: no {_rel(paths['checkpoint'])} after training")
    checkpoint_step = int(tp.torch.load(paths["checkpoint"], weights_only=False)["step"])

    if plan["is_dp"]:
        seam, composed = box["seam"], box["composed"]
        _prove(seam is not None, f"{key}: no DPSGD was constructed on a DP arm")
        _prove(
            seam.sigma == plan["dp_sigma"] and seam.C == plan["dp_clip_norm"],
            f"{key}: the seam ran at sigma={seam.sigma!r} / C={seam.C!r}, not "
            f"{plan['dp_sigma']!r} / {plan['dp_clip_norm']!r}",
        )
        timed = tp.MAX_STEPS - resumed_from_step
        _prove(
            len(composed) == timed,
            f"{key}: the seam composed {len(composed)} step(s) but this leg covers {timed}",
        )
        clip_bind_count = int(seam._clip_bind_count)
        if plan["axis_value"] == 0.0:
            # D-01 (a): BEFORE any reading exists. At sigma=0 the only thing C can do is clip.
            _prove(
                clip_bind_count == 0,
                f"{key}: the control's clip BOUND on {clip_bind_count} record(s) at "
                f"C={seam.C!r}. The control is not the control; stop before scoring",
            )
        live = {
            "composed_steps": resumed_from_step + len(composed),
            "composed_lot_sizes": sorted(set(composed)),
            "records_per_lot": int(seam._records),
            "q": mitigation_unit.SAMPLING_RATE_Q,
            "clip_norm": float(seam.C),
        }
        pinned = dict(plan["pinned_mechanism"])
    else:
        _prove(box["seam"] is None, f"{key}: a DPSGD was constructed on an adversarial arm")
        lot = int(cfg.batch_size * max(1, cfg.grad_accum_steps))
        live = {
            "composed_steps": checkpoint_step,
            "composed_lot_sizes": [lot],
            "records_per_lot": lot,
            "q": None,
            "clip_norm": None,
        }
        pinned = dict(plan["pinned_mechanism"], composed_lot_sizes=[lot], records_per_lot=lot)
        clip_bind_count = None
    # D-34 EARLY, so a diverged mechanism halts before the draw leg spends hours on it. The
    # record writer runs the same proof again at write time.
    phase25_record.prove_mechanism_matches_pin(live, pinned, point_key=key)

    # The run's csv lands under `results/<prefix>_<arm>/` by `arm_outputs`' rule; move it under
    # the gitignored `data/` so §O1's single-path commit is the only write `results/` sees and
    # plan 25-19's dirty-tree refusal is not tripped by 44 untracked logs.
    log_dir = run_log_dir(key)
    log_dir.mkdir(parents=True, exist_ok=True)
    csv_dst = log_dir / "run.csv"
    shutil.move(str(paths["csv"]), str(csv_dst))
    try:
        paths["csv"].parent.rmdir()
    except OSError:
        pass

    blob = {
        "point_key": key,
        "arm": arm,
        "prefix": prefix,
        "seed": plan["seed"],
        "n_facts": len(facts),
        "adapter": _rel(paths["adapter"]),
        "adapter_sha256": _sha256(paths["adapter"]),
        "adapter_bytes": paths["adapter"].stat().st_size,
        "checkpoint": _rel(paths["checkpoint"]),
        "checkpoint_step": checkpoint_step,
        "csv": _rel(csv_dst),
        "csv_sha256": _sha256(csv_dst),
        "stats": trained["stats"],
        "final_train_loss": trained["final_train_loss"],
        "ppl_adapter_on": trained["ppl_adapter_on"],
        "ppl_adapter_off": trained["ppl_adapter_off"],
        "ppl_scored_targets": trained["scored_targets"],
        "seconds": seconds,
        "resumed_from_step": resumed_from_step,
        "live_mechanism": live,
        "pinned_mechanism": pinned,
        "clip_bind_count": clip_bind_count,
        "train_config": tp.asdict(cfg),
        "git_sha": phase25_run.head_sha(),
    }
    phase25_run.atomic_write_json(sidecar, blob)
    print(
        f"[phase25_points] {key}: trained in {seconds:.1f}s (resumed_from_step "
        f"{resumed_from_step}), clip_bind_count={clip_bind_count}, mechanism matches the pin",
        flush=True,
    )
    return blob


# =================================================================================================
# ===== (c) THE MEASUREMENT STAGE — condition (c), GATE-05, and the control's recall =====
# =================================================================================================


def measure_stage(plan, training):
    """The readings that need the trained adapter and a loaded model. Sidecar-persisted."""
    import phase14_factset as fs
    import phase14_recall as recall
    import phase25_run
    import teach_persona as tp

    key, arm = plan["point_key"], plan["arm"]
    sidecar = measure_sidecar(key)
    if sidecar.exists():
        blob = json.loads(sidecar.read_text(encoding="utf-8"))
        _prove(
            blob["adapter_sha256"] == training["adapter_sha256"],
            f"{_rel(sidecar)} describes adapter {blob['adapter_sha256']!r}, not the trained "
            f"{training['adapter_sha256']!r}",
        )
        print(f"[phase25_points] {key}: REUSING measurements from {_rel(sidecar)}", flush=True)
        return blob

    device = phase25_run.device()
    adapter = _ROOT / training["adapter"]
    started = time.time()
    model, _cfg, tok, forbid, _artifact = recall.load_adapted_model(device, adapter)
    capability = phase25_condition_c.measure_condition_c(model, tok, device, forbid=forbid)
    taught = taught_mapping(tp.arm_spec(arm)[0])
    exposure = phase25_gate05.measure_gate05(
        model, tok, device, taught=taught, n_facts=plan["n_facts"]
    )
    gaps = list(phase25_gate05.gate05_exposure_gaps(exposure["gated"]))
    flag = phase25_gate05.zero_extraction_has_nll(exposure["gated"])
    del model
    measure_seconds = time.time() - started

    recall_block, scoring_seconds = None, None
    if plan["is_control"]:
        scoring_started = time.time()
        scored = tp.score_arm(arm, fs.LOCKED_FACTS, adapter, device)
        scoring_seconds = time.time() - scoring_started

        def tier(block):
            return {
                "numerator": int(block["k"]),
                "denominator": int(block["n"]),
                "rate": block["rate"],
                "questions": block["questions"],
                "draws_per_question": 1 + recall.N_SEEDED_SAMPLES,
                "per_family": block["per_family"],
            }

        recall_block = {
            "taught": tier(scored["on_taught"]),
            "heldout": tier(scored["on_heldout"]),
            "taught_off": tier(scored["off_taught"]),
            "heldout_off": tier(scored["off_heldout"]),
            "per_family_gain": scored["per_family_gain"],
        }
        k, n = recall_block["taught"]["numerator"], recall_block["taught"]["denominator"]
        if arm == "dp_n8":
            # D-07: a miss HALTS the whole sweep. The message is kept beside the sidecars so the
            # investigation starts from the exact text, not from a scrollback.
            try:
                phase25_prereg.prove_reproduction(k, n)
            except SystemExit as halt:
                phase25_run.atomic_write_json(
                    _ROOT / "data" / f"phase25_{key}_halt.json",
                    {"point_key": key, "observed": [k, n], "halt_message": str(halt)},
                )
                raise
        print(
            f"[phase25_points] {key}: taught recall {k}/{n} in {scoring_seconds:.1f}s"
            + (" — REPRODUCTION GATE PASSED" if arm == "dp_n8" else ""),
            flush=True,
        )

    blob = {
        "point_key": key,
        "adapter_sha256": training["adapter_sha256"],
        "capability": capability,
        "exposure": exposure,
        "gate05_gaps": gaps,
        "zero_extraction_has_nll": flag,
        "recall": recall_block,
        "measure_seconds": measure_seconds,
        "scoring_seconds": scoring_seconds,
        "device": device,
    }
    phase25_run.atomic_write_json(sidecar, blob)
    print(
        f"[phase25_points] {key}: condition (c) + GATE-05 measured in {measure_seconds:.1f}s "
        f"(dialogue {capability['adapter_on']:.4f}/{capability['adapter_off']:.4f}, retention "
        f"{capability['retention_ppl']:.4f}, zero_extraction_has_nll={flag})",
        flush=True,
    )
    return blob


# =================================================================================================
# ===== (d) THE DRAW LEG'S INPUTS, AND THE RECORD'S KWARGS =====
# =================================================================================================


def attack_corpus():
    """`results/phase18_corpus.json` and its digest, checked as `score_never_taught` does."""
    import phase18_extraction as x18  # LAZY — torch-touching.

    corpus = json.loads(x18.CORPUS_PATH.read_text(encoding="utf-8"))
    _prove(
        corpus["entry_keys"] == list(x18.CORPUS_ENTRY_KEYS),
        f"{x18.CORPUS_PATH.name} declares entry_keys {corpus['entry_keys']} against the pin's "
        f"{list(x18.CORPUS_ENTRY_KEYS)}",
    )
    families = sorted({entry["family"] for entry in corpus["prompts"]})
    _prove(
        families == sorted(x18.ATTACK_FAMILIES),
        f"the corpus spans families {families}, not {sorted(x18.ATTACK_FAMILIES)}",
    )
    return corpus, x18.corpus_sha256(corpus)


def scoring_values():
    """``{fact_id: value}`` for the scorer — `phase23_run.score_never_taught`'s mapping."""
    import phase14_factset as fs

    return {fact.id: fact.value for fact in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS}


def _family_counts(scored):
    gated = [record for record in scored if record["tier"] == phase25_record.GATED_TIER]
    counts = {}
    for family in phase25_record.ATTACK_FAMILIES:
        rows = [record for record in gated if record["family"] == family]
        counts[family] = {
            "successes": sum(1 for record in rows if any(record["hits"])),
            "questions": len(rows),
            "draws": int(sum(record["n_draws"] for record in rows)),
        }
    return counts


def _refusal(blob):
    import phase24_adversarial as pa

    templates = [pa.refusal_for(slot) for slot in phase25_gate05.GATE05_SLOTS]
    completions = {
        family: [text for draw in blob["shapes"][family]["draws"] for text in draw["completions"]]
        for family in phase25_record.ATTACK_FAMILIES
    }
    return phase25_record.refusal_column(completions, templates)


def _adversarial_extras(plan, training):
    stats = training["stats"]
    keys = (
        "mask_fraction",
        "episodes",
        "tokens",
        "teaching_tokens",
        "clean_episodes",
        "adversarial_episodes",
        "adversarial_pool_size",
        "adversarial_multiplicity",
        "adversarial_family_counts",
        "adversarial_tokens",
        "adversarial_scored_tokens",
    )
    grid = mitigation_budget.ADVERSARIAL_RATIO_GRID
    budget = json.loads(TOKEN_BUDGET_RECORD.read_text(encoding="utf-8"))
    upper = [
        row
        for row in budget["rows"]
        if row["arm"] == plan["arm"] and row["adversarial_ratio"] == grid[-1]
    ]
    _prove(len(upper) == 1, f"{plan['arm']}: {len(upper)} token-budget rows at ratio {grid[-1]!r}")
    return {
        "adversarial_build": {name: stats.get(name) for name in keys},
        # `multiplicity` is the record's OWN field (D-28's dual-granularity sentence); this is
        # the BUILD's multiplicity, named for what it is. MEASURED 2026-09-05: the first
        # adversarial point halted at its record stage on exactly that collision.
        "adversarial_multiplicity": stats.get("adversarial_multiplicity"),
        "multiplicity_at_upper_extreme": {
            "arm": plan["arm"],
            "ratio": grid[-1],
            "value": upper[0]["adversarial_multiplicity"],
            "source": _rel(TOKEN_BUDGET_RECORD),
            "reported_not_a_grid_variable": True,
        },
        "axis_terminus": {
            "pool_ceiling_ratio": grid[-1],
            "this_point_is_the_ceiling": plan["axis_value"] == grid[-1],
            "statement": AXIS_TERMINUS,
        },
        "mechanism_note": ADVERSARIAL_MECHANISM_NOTE,
    }


def record_kwargs(plan, *, training, measured, blob, per_question, scored, tracked, draws_cache):
    """`build_point_record`'s kwargs for one point, every value from a producer above."""
    key, arm = plan["point_key"], plan["arm"]
    capability = measured["capability"]
    control_gap = (
        phase25_condition_c.control_gap_for_capacity(capability)
        if plan["is_control"]
        else phase25_condition_c.control_gap_for_capacity(control_reading(arm, tracked))
    )
    exposure = measured["exposure"]
    extras = {
        "sweep_prefix": plan["prefix"],
        "seed": plan["seed"],
        "training": {
            name: training[name]
            for name in (
                "seconds",
                "resumed_from_step",
                "checkpoint_step",
                "csv",
                "csv_sha256",
                "final_train_loss",
                "ppl_adapter_on",
                "ppl_adapter_off",
                "ppl_scored_targets",
                "train_config",
                "git_sha",
            )
        },
        "clip_bind_count": training["clip_bind_count"],
        "clip_checked_before_scoring": True if plan["is_control"] else None,
        "measure_seconds": measured["measure_seconds"],
        "shape_timing": {
            family: blob["shapes"][family]["timing"] for family in phase25_record.ATTACK_FAMILIES
        },
        "raw_draws": {
            "path": _rel(draws_cache),
            "sha256": _sha256(draws_cache),
            "not_committed": "raw completion text lives in gitignored data/; its digest is pinned",
        },
    }
    if plan["is_control"]:
        recall_block = measured["recall"]
        k, n = recall_block["taught"]["numerator"], recall_block["taught"]["denominator"]
        extras.update(
            {
                "taught_recall": recall_block["taught"],
                "heldout_recall": recall_block["heldout"],
                "taught_recall_off": recall_block["taught_off"],
                "heldout_recall_off": recall_block["heldout_off"],
                "per_family_gain": recall_block["per_family_gain"],
                "scoring_seconds": measured["scoring_seconds"],
                "reproduction_gate": {
                    "gated": arm == "dp_n8",
                    "passed": True if arm == "dp_n8" else None,
                    "expected": [phase25_prereg.REPRODUCTION_K, phase25_prereg.REPRODUCTION_N],
                    "observed": [k, n],
                    "source": phase25_prereg.REPRODUCTION_SOURCE_RECORD,
                    "comparison": "hard == on integer counts, phase25_prereg.prove_reproduction",
                    "not_gated_reason": (
                        None
                        if arm == "dp_n8"
                        else "D-07 gates the n=8 reading; n=64 has no Phase 23 count to reproduce"
                    ),
                },
                "scoring_justification": SCORING_JUSTIFICATION,
            }
        )
    if not plan["is_dp"]:
        extras.update(_adversarial_extras(plan, training))

    return {
        "point_key_value": key,
        "arm": arm,
        "axis_value": plan["axis_value"],
        "live_mechanism": training["live_mechanism"],
        "pinned_mechanism": training["pinned_mechanism"],
        "draws_per_question": mitigation_budget.CURVE_K,
        "draws_per_question_source": "mitigation_budget.CURVE_K",
        "per_question": per_question,
        "family_counts": _family_counts(scored),
        "refusal": _refusal(blob),
        "adapter_path": training["adapter"],
        "adapter_sha256": training["adapter_sha256"],
        "n_facts": plan["n_facts"],
        "capability": capability,
        "control_gap": control_gap,
        "seed_spread": seed_spread(),
        "zero_extraction_has_nll": measured["zero_extraction_has_nll"],
        "gate05_gated": {
            "slots": list(phase25_gate05.GATE05_SLOTS),
            "gaps": measured["gate05_gaps"],
            "exposure": exposure["gated"],
        },
        "gate05_reported": {
            "n_facts": plan["n_facts"],
            "tier_slot_count": exposure["reported_slot_count"],
            "exposure_columns": phase25_gate05.REQUIRED_NLL_COLUMNS,
            "exposure_measured": exposure["exposure_measured"],
            "exposure_omitted": exposure["exposure_omitted"],
            "omitted_reason": exposure["omitted_reason"],
            "governs": phase25_gate05.GATE05_GOVERNS,
            "exposure": exposure["reported"],
        },
        "point_epsilon": plan["point_epsilon"],
        "accounting": plan["accounting"],
        "extra": extras,
    }
