"""Phase 32 v5.0 sweep driver (AFRONT-01): import-and-override of the frozen v4.0 stages
(Phase 30 D-13).

THE LIBRARY HALF (plan 32-02). Everything the v5.0 run loop needs except the loop itself:

* ``measure_stage``: D-01/D-02, the frozen v4.0 measurement stage with recall scored for EVERY
  point, by handing it the plan with ``is_control`` forced on. No v4.0 code is edited.
* ``build_point_record``: the record every downstream consumer reads (own_control, the floors, the
  dialogue pair, the frontier's flat record, the baseline source and the D-03 clock). Pure.
* ``cumulative_seconds`` / ``stop_line_seconds``: the D-03 clock over the COMMITTED point records,
  and the pause line read from the committed ARCAL-03 budget (never retyped).
* ``record_session`` / ``prove_pinned_unchanged``: D-08 (Phase 31 WR-02). Every session that ran a
  stage records the commit it ran from; before a record is written, no pinned module may differ
  between any of those commits and HEAD.
* ``write_point_record`` / ``commit_path`` / ``commit_untracked``: write-once, then D-11's
  one-path commit on main. The git surface is literal argv only, bounded by an AST test.

THE LOOP (plan 32-04): ``run_point`` (counted train -> recall-on measure -> draws -> score ->
record -> write -> commit), ``run`` (the D-17 schedule walk with PREREG-03, the D-03/D-04 stop
line and the D-06 ruling), and ``main`` (the CLI the D-05 LaunchAgent runs).

THREE ROOTS. ``_ROOT`` holds the data/ sidecars and ``_GIT_ROOT`` is the results repository; both
are patchable (tests patch ``_GIT_ROOT`` together with ``phase30_points._ROOT``). ``_CODE_ROOT`` is
the repository containing this file and is never patched: session shas, the D-08 diff, module
hashes and the dirty-tree refusal all read it. In production all three are the same directory.

Torch-free at import: ``teach_persona`` and every torch-touching module are imported lazily.
"""

import datetime
import hashlib
import json
import math
import pathlib
import subprocess
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_GIT_ROOT = pathlib.Path(__file__).resolve().parent.parent
# Never patched: the code this file ships in. See the module docstring.
_CODE_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_CODE_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
_SRC = str(_CODE_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import mitigation_budget  # noqa: E402  (scripts/ is not a package)
import phase25_condition_c  # noqa: E402  (same)
import phase25_points  # noqa: E402  (same)
import phase25_record  # noqa: E402  (same)
import phase25_run  # noqa: E402  (same)
import phase29_prereg  # noqa: E402  (same)
import phase30_points  # noqa: E402  (same)
import phase31_probe  # noqa: E402  (same; per_step_replay / prove_replay_counts are public)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

INSTRUMENT_GIT_SHA = git_sha()

# D-08 scope: a file is pinned when its bytes can change a stage's numbers. Verdict-only modules
# are pinned by the frontier's provenance (plan 32-03), not here.
PINNED_MODULES = tuple(
    pathlib.Path(path).resolve().relative_to(_CODE_ROOT).as_posix()
    for path in (
        __file__,
        phase25_points.__file__,
        phase25_run.__file__,
        phase30_points.__file__,
        phase29_prereg.__file__,
        phase31_probe.__file__,
        phase25_record.__file__,
        phase25_condition_c.__file__,
        # Paths, not imports: most of these import torch.
        _SCRIPTS + "/teach_persona.py",
        _SCRIPTS + "/phase14_recall.py",
        _SCRIPTS + "/phase18_extraction.py",
        _SCRIPTS + "/phase25_gate05.py",
        _SRC + "/personacore/training/loop.py",
        _SRC + "/personacore/training/data.py",
        _SCRIPTS + "/phase24_adversarial.py",
        _SCRIPTS + "/mitigation_budget.py",
        _SCRIPTS + "/mitigation_unit.py",
        _SCRIPTS + "/phase14_factset.py",
        _SCRIPTS + "/phase19_erasure.py",
        _SRC + "/personacore/lora/config.py",
        _SRC + "/personacore/lora/inject.py",
        _SRC + "/personacore/lora/layer.py",
        _SRC + "/personacore/model/gpt.py",
    )
)

# Derived from the pre-registration's one path tuple, never typed.
BUDGET_PATH = next(
    p for p in phase29_prereg.V5_RESULT_PATHS if p.startswith("results/phase31_budget")
)

# D-11: the only EXECUTABLE git actions, and the read-only ones. Enforced by AST from the test
# module over every git argv literal in this file.
ALLOWED_GIT_ACTIONS = ("add", "commit")
READ_ONLY_GIT_ACTIONS = ("ls-files", "show", "rev-parse", "status", "diff", "log", "merge-base")

SCHEMA = "phase32_point/1"
REQUIREMENT = "AFRONT-01"
STAGES = ("train", "measure", "recall", "draw", "score")


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase32_points] {message}")


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _rel(path):
    path = pathlib.Path(path)
    return path.relative_to(_ROOT).as_posix() if path.is_relative_to(_ROOT) else str(path)


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# =================================================================================================
# D-01 / D-02: recall for every point, through the frozen stage
# =================================================================================================


def measure_stage(plan, training):
    """D-01/D-02: the frozen ``phase25_points.measure_stage`` with ``is_control`` forced on.

    The frozen stage scores taught recall only under ``if plan["is_control"]`` (phase25_points
    :570). v5.0 reads recall at every point, so the stage gets a COPY of the plan with the flag
    set; the caller's plan is not mutated and no v4.0 code changes.
    """
    return phase25_points.measure_stage(dict(plan, is_control=True), training)


# =================================================================================================
# THE RECORD
# =================================================================================================

TRAINING_FIELDS = (
    "seconds",
    "resumed_from_step",
    "checkpoint_step",
    "csv_sha256",
    "final_train_loss",
    "ppl_adapter_on",
    "ppl_adapter_off",
    "train_config",
    "git_sha",
    "adapter",
    "clip_bind_count",
)

RECALL_FIELDS = {
    "taught_recall": "taught",
    "heldout_recall": "heldout",
    "taught_recall_off": "taught_off",
    "heldout_recall_off": "heldout_off",
    "per_family_gain": "per_family_gain",
}


def stage_seconds(training, measured, blob, score_seconds):
    """``{train, measure, recall, draw, score}``, each ``{"seconds": float}``. Recall kept apart."""
    _prove(
        measured["scoring_seconds"] is not None,
        "the measured blob has scoring_seconds None: recall was not scored (D-01)",
    )
    draw_minutes = sum(
        blob["shapes"][f]["timing"]["minutes"] for f in phase25_record.ATTACK_FAMILIES
    )
    return {
        "train": {"seconds": float(training["seconds"])},
        "measure": {"seconds": float(measured["measure_seconds"])},
        "recall": {"seconds": float(measured["scoring_seconds"])},
        "draw": {"seconds": float(60 * draw_minutes)},
        "score": {"seconds": float(score_seconds)},
    }


def build_point_record(
    plan,
    *,
    recipe,
    training,
    measured,
    replay,
    blob,
    per_question,
    scored,
    score_seconds,
    control_gap,
    draws_cache,
    provenance,
):
    """One point's record from its stage outputs. Pure: no git, no writes.

    Reads two files only: the committed n64 floor record (``phase25_points.seed_spread``) and the
    draw cache (hashed). ``control_gap`` is computed by the caller from the leg's own control.
    """
    key = plan["point_key"]
    pinned = plan["pinned_mechanism"]
    composed_steps = pinned["composed_steps"]
    config = training["train_config"]
    _prove(
        training["resumed_from_step"] == 0,
        f"{key}: training resumed from step {training['resumed_from_step']}: its seconds cover "
        "only the resumed tail, so the D-03 clock would undercount (Pitfall 10)",
    )
    _prove(
        composed_steps == recipe["max_steps"] == config["max_steps"],
        f"{key}: composed_steps {composed_steps}, recipe max_steps {recipe['max_steps']} and "
        f"train_config max_steps {config['max_steps']} disagree",
    )
    _prove(
        plan["seed"] == recipe["seed"] == config["seed"],
        f"{key}: plan seed {plan['seed']}, recipe seed {recipe['seed']} and train_config seed "
        f"{config['seed']} disagree",
    )
    _prove(
        replay["expected_per_step"] == recipe["replay_windows"]
        and replay["steps"] == recipe["max_steps"]
        and replay["per_step"] == [replay["expected_per_step"]] * replay["steps"],
        f"{key}: replay per_step {sorted(set(replay['per_step']))} over "
        f"{len(replay['per_step'])} step(s) is not [{recipe['replay_windows']}] * "
        f"{recipe['max_steps']} (D-07, WR-04)",
    )
    _prove(
        measured["adapter_sha256"] == training["adapter_sha256"],
        f"{key}: the measured blob describes adapter {measured['adapter_sha256']!r}, not the "
        f"trained {training['adapter_sha256']!r}",
    )
    recall = measured["recall"]
    _prove(recall is not None, f"{key}: the measured blob carries no recall (D-01)")
    stages = stage_seconds(training, measured, blob, score_seconds)
    return {
        "schema": SCHEMA,
        "requirement": REQUIREMENT,
        "point_key": key,
        "arm": plan["arm"],
        "axis": plan["axis"],
        "axis_value": plan["axis_value"],
        "q": pinned["q"],
        "clip_norm": pinned["clip_norm"],
        "is_control": plan["is_control"],
        "control_key": plan["control_key"],
        "seed": plan["seed"],
        "recipe": dict(recipe),
        "composed_steps": composed_steps,
        "training": {name: training[name] for name in TRAINING_FIELDS},
        **{field: recall[source] for field, source in RECALL_FIELDS.items()},
        "condition_c": phase25_record.condition_c_group(
            capability=measured["capability"],
            control_gap=control_gap,
            seed_spread=phase25_points.seed_spread(),
        ),
        "capability": measured["capability"],
        "gate05_gaps": measured["gate05_gaps"],
        "zero_extraction_has_nll": measured["zero_extraction_has_nll"],
        "per_family_counts": phase25_points._family_counts(scored),
        "per_question": per_question,
        "draws_per_question": mitigation_budget.CURVE_K,
        "draws_per_question_source": "mitigation_budget.CURVE_K",
        "adapter_sha256": training["adapter_sha256"],
        "raw_draws": {"path": _rel(draws_cache), "sha256": _sha256(draws_cache)},
        "replay": {
            "per_step": list(replay["per_step"]),
            "expected_per_step": replay["expected_per_step"],
            "steps": replay["steps"],
            "teaching_windows_per_step": replay["teaching_windows_per_step"],
        },
        "stages": stages,
        "provenance": provenance,
    }


# =================================================================================================
# D-03: THE CLOCK, AND THE STOP LINE
# =================================================================================================


def tracked_results():
    """``git ls-files results`` of the results repository, as a list."""
    listed = subprocess.run(
        ["git", "ls-files", "results"], cwd=_GIT_ROOT, capture_output=True, text=True, check=True
    )
    return listed.stdout.splitlines()


def cumulative_seconds(tracked):
    """Sum of ``stages.*.seconds`` over the COMMITTED point records. PREREG-03 records count 0."""
    total = 0.0
    for key in phase29_prereg.POINT_KEYS():
        rel = phase29_prereg.point_record_path(key)
        if rel not in tracked:
            continue
        record = phase30_points._tracked_json(rel, tracked, "the point record")
        if record.get("rule") == "PREREG-03":
            continue
        _prove(
            isinstance(record.get("stages"), dict),
            f"{rel} has neither stages nor rule PREREG-03: the D-03 clock cannot read it",
        )
        total += sum(float(stage["seconds"]) for stage in record["stages"].values())
    return total


def stop_line_seconds(tracked):
    """The ARCAL-03 stop line: read from the committed budget, never retyped (Phase 31 D-08)."""
    value = phase30_points._tracked_json(BUDGET_PATH, tracked, "the ARCAL-03 budget")["stop_line"][
        "seconds"
    ]
    _prove(
        isinstance(value, float) and math.isfinite(value) and value > 0,
        f"{BUDGET_PATH} stop_line.seconds {value!r} is not a positive finite float",
    )
    return value


# =================================================================================================
# D-08 (Phase 31 WR-02): the stages ran on the code that writes the record
# =================================================================================================


def sessions_sidecar(key):
    """``data/phase32_<key>_sessions.json``; the key is validated by the pre-registration."""
    phase29_prereg.point_record_path(key)
    return _ROOT / "data" / f"phase32_{key}_sessions.json"


def record_session(key):
    """Append this session's ``{git_sha, started_utc}`` to the point's sessions sidecar."""
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=_CODE_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    path = sessions_sidecar(key)
    sessions = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    sessions.append({"git_sha": head, "started_utc": _now()})
    phase25_run.atomic_write_json(path, sessions)
    return sessions


def prove_pinned_unchanged(shas):
    """D-08: no pinned module differs between any recorded session commit and HEAD."""
    for sha in dict.fromkeys(shas):
        diff = subprocess.run(
            ["git", "diff", "--name-only", sha, "HEAD", "--", *PINNED_MODULES],
            cwd=_CODE_ROOT,
            capture_output=True,
            text=True,
        )
        _prove(
            diff.returncode == 0, f"unknown sha {sha!r}: git diff failed ({diff.stderr.strip()})"
        )
        changed = diff.stdout.split()
        _prove(
            not changed,
            f"pinned modules {changed} changed between session commit {sha} and HEAD (D-08, "
            "WR-02): code changed between the session that ran the stages and the write, so the "
            "record would name code its numbers did not come from. Every scripts/ change must "
            "land before launch",
        )


# =================================================================================================
# WRITE-ONCE, THEN D-11'S ONE-PATH COMMIT
# =================================================================================================


def write_point_record(key, record, *, shas):
    """Overwrite refusal FIRST, dirty refusal SECOND, D-08 THIRD, then the atomic write."""
    rel = phase29_prereg.point_record_path(key)
    out = _GIT_ROOT / rel
    _prove(
        not out.exists(),
        f"{rel} exists — REFUSING to overwrite it. A point record is write-once; corrections are "
        "dated continuations",
    )
    refuse_if_dirty(
        who="phase32_points",
        detail=(
            "a point record names the commit its stages ran from; a record written from a dirty "
            "tree names a commit it cannot be regenerated from"
        ),
        pathspec=("scripts", "src", "results", f":(exclude){rel}"),
        cwd=_CODE_ROOT,
    )
    prove_pinned_unchanged([*shas, record["training"]["git_sha"]])
    phase25_run.atomic_write_json(out, record)
    return rel


def commit_message(key, *, refused=False):
    phase29_prereg.point_record_path(key)
    kind = "PREREG-03 refused point" if refused else "sweep point"
    return f"feat(32): record {kind} {key}"


def commit_path(relative, message):
    """Stage and commit EXACTLY ``relative`` (one path under results/) on main. Returns the sha."""
    path = (_GIT_ROOT / relative).resolve()
    _prove(
        relative.startswith("results/") and path.is_relative_to((_GIT_ROOT / "results").resolve()),
        f"{relative!r} is not under results/: D-11 bounds the unattended driver to one results "
        "path",
    )
    _prove(path.exists(), f"{relative} does not exist, so there is nothing to commit")
    branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=_GIT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    _prove(branch == "main", f"the results repository is on branch {branch!r}, not main (D-11)")
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", relative],
        cwd=_GIT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    _prove(
        status,
        f"{relative} is already committed and unchanged, so this commit would be a NO-OP",
    )
    subprocess.run(["git", "add", "--", relative], cwd=_GIT_ROOT, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", message, "--", relative], cwd=_GIT_ROOT, check=True
    )
    named = subprocess.run(
        ["git", "show", "--name-only", "--format=", "HEAD"],
        cwd=_GIT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    _prove(named == [relative], f"the commit just made names {named}, not exactly [{relative!r}]")
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=_GIT_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def commit_untracked(paths, message_for):
    """Pitfall 9: commit each given path that ``git status`` still reports, one commit each."""
    committed = []
    for relative in paths:
        pending = subprocess.run(
            ["git", "status", "--porcelain", "--", relative],
            cwd=_GIT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if pending:
            commit_path(relative, message_for(relative))
            committed.append(relative)
    return committed


# =================================================================================================
# ONE POINT (plan 32-04): phase31_probe.run_point_probe's stage sequence, re-keyed per point
# =================================================================================================


def replay_sidecar(key):
    """``data/phase32_<key>_replay.json``: the per-step replay counts of the point's training."""
    phase29_prereg.point_record_path(key)
    return _ROOT / "data" / f"phase32_{key}_replay.json"


def calibration_descent():
    """The ARECIPE-02 calibration's add commit, derived, and proof HEAD descends from it."""
    path = phase30_points.CALIBRATION_PATH
    adds = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%H", "--", path],
        cwd=_GIT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    _prove(adds, f"{path} was never added in this history")
    add = adds[-1]
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", add, "HEAD"], cwd=_GIT_ROOT, capture_output=True
    )
    _prove(ancestor.returncode == 0, f"HEAD does not descend from {path}'s add commit {add}")
    return {"path": path, "add_commit": add, "is_ancestor_of_head": True}


def run_point(plan, tracked, *, heartbeat_path, stop_line):
    """Train (replay counted per step) -> measure with recall -> draw -> score -> record -> write ->
    commit, for ONE v5.0 point. Returns the record. Called only by :func:`run`.

    Resumable per stage through the frozen stages' own sidecars and draw cache, EXCEPT a
    half-finished training: a checkpoint without a training sidecar (its resume would time only the
    tail and could not count the earlier steps' replay) or a training sidecar without its replay
    counts. Both are refused before any stage runs.
    """
    import teach_persona as tp
    import torch

    key = plan["point_key"]
    leg = phase30_points.leg_of(key)
    recipe = phase30_points.require_calibrated_recipe(
        leg, phase30_points.recipe_identity(leg), tracked
    )
    expected = phase30_points.calibration_record(tracked)["recipe"][leg]["replay_windows"]
    _prove(
        expected == phase29_prereg.replay_windows(plan["n_facts"]),
        f"{key}: the calibration's replay_windows {expected} != replay_windows({plan['n_facts']})",
    )
    paths = tp.arm_outputs(plan["arm"], prefix=plan["prefix"])
    train_sidecar = phase25_points.training_sidecar(key)
    counts_sidecar = replay_sidecar(key)
    _prove(
        train_sidecar.exists() or not paths["checkpoint"].exists(),
        f"{paths['checkpoint']} exists without {train_sidecar}: a resume would time only the "
        "remaining steps and could not count the earlier steps' replay (Pitfall 10, D-07). Delete "
        f"{paths['checkpoint']} and {paths['adapter']} (if present) in a reviewed step, then rerun",
    )
    _prove(
        counts_sidecar.exists() or not train_sidecar.exists(),
        f"{train_sidecar} exists without {counts_sidecar}: the per-step replay counts of that "
        f"training cannot be recovered (D-07). Delete {train_sidecar}, {paths['adapter']} and "
        f"{paths['checkpoint']} in a reviewed step, then rerun",
    )
    reused_train = train_sidecar.exists()
    sessions = record_session(key)

    state = {"point": key, "stage": "train", "shape": None, "draw_index": None}
    stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
    try:
        # TRAIN, with every draw counted through train()'s on_draw hook (D-07).
        events = []
        real_train = tp.train

        def _counting_train(**kwargs):
            def _on_draw(bin_path, ix):
                replay = pathlib.Path(bin_path) == pathlib.Path(tp.DIALOG_TRAIN_BIN)
                events.append((replay, len(ix)))

            return real_train(**kwargs, on_draw=_on_draw)

        tp.train = _counting_train
        try:
            training = phase25_points.train_stage(plan)
        finally:
            tp.train = real_train
        if reused_train:
            _prove(not events, f"{key}: a reused training drew windows")
            replay = json.loads(counts_sidecar.read_text(encoding="utf-8"))
            _prove(
                replay["adapter_sha256"] == training["adapter_sha256"],
                f"{counts_sidecar} counts adapter {replay['adapter_sha256']!r}, not the trained "
                f"{training['adapter_sha256']!r}",
            )
        else:
            replay = {
                "per_step": phase31_probe.prove_replay_counts(
                    events, expected, batch_size=tp.BATCH_SIZE, steps=tp.MAX_STEPS
                ),
                "expected_per_step": expected,
                "steps": tp.MAX_STEPS,
                "teaching_windows_per_step": tp.BATCH_SIZE,
                "adapter_sha256": training["adapter_sha256"],
            }
            phase25_run.atomic_write_json(counts_sidecar, replay)
        _prove(
            replay["per_step"] == [expected] * tp.MAX_STEPS,
            f"{counts_sidecar} does not hold {expected} replay windows on all {tp.MAX_STEPS} steps",
        )

        # MEASURE: condition (c) + GATE-05, then recall at EVERY point (D-01).
        state["stage"] = "measure"
        measured = measure_stage(plan, training)
        _prove(measured["scoring_seconds"] is not None, f"{key}: recall was not scored (D-01)")

        state["stage"] = "draw"
        corpus, corpus_sha256 = phase25_points.attack_corpus()
        blob, _digests = phase25_run.draw_point_shapes(
            key,
            adapter=_ROOT / training["adapter"],
            adapter_sha256=training["adapter_sha256"],
            corpus=corpus,
            corpus_sha256=corpus_sha256,
            k=mitigation_budget.CURVE_K,
            state=state,
        )
        state["shape"] = state["draw_index"] = None

        state["stage"] = "score"
        started = time.monotonic()
        per_question, _per_fact, scored = phase25_run.score_point(
            blob, phase25_points.scoring_values()
        )
        score_seconds = time.monotonic() - started

        state["stage"] = "record"
        # D-01 / ACTRL-01: the control's gap is its own reading; a non-control's is its own
        # leg's committed control's.
        control_gap = phase25_condition_c.control_gap_for_capacity(
            measured["capability"]
            if plan["is_control"]
            else phase30_points.control_dialogue_pair(key, tracked, point_recipe=recipe)
        )
        provenance = {
            "module_sha256": {rel: _sha256(_CODE_ROOT / rel) for rel in PINNED_MODULES},
            "git_sha": INSTRUMENT_GIT_SHA,
            "sessions": sessions,
            "stop_line": stop_line,
            "device": phase25_run.device(),
            "torch_version": torch.__version__,
            "calibration": calibration_descent(),
            "written_utc": _now(),
        }
        record = build_point_record(
            plan,
            recipe=recipe,
            training=training,
            measured=measured,
            replay=replay,
            blob=blob,
            per_question=per_question,
            scored=scored,
            score_seconds=score_seconds,
            control_gap=control_gap,
            draws_cache=phase25_run.draws_path(key),
            provenance=provenance,
        )
        provenance["head_at_write"] = git_sha()
        rel = write_point_record(key, record, shas=[s["git_sha"] for s in sessions])

        state["stage"] = "commit"
        commit_path(rel, commit_message(key))
        # "done" BEFORE the stop event: a periodic beat racing the stop can only write "done".
        state.update(stage="done", shape=None, draw_index=None)
    finally:
        stop.set()
        thread.join()
    phase25_run.beat(heartbeat_path, point=key, stage="done", shape=None, draw_index=None)
    print(f"[phase32_points] {key}: recorded and committed {rel}", flush=True)
    return record


# =================================================================================================
# THE SCHEDULE WALK (AFRONT-01, D-03..D-06, D-11, D-17, PREREG-03)
# =================================================================================================


# D-20: the documented manual command past the line (32-RUNBOOK.md). Never in the plist.
MANUAL_RELAUNCH = (
    'caffeinate -dims .venv/bin/python scripts/phase32_points.py run --past-stop-line "<ruling>"'
)


def _run_excludes():
    """Pitfall 3: the per-point training csv dirs and the point records awaiting commit."""
    dirs = []
    for key in phase29_prereg.POINT_KEYS():
        plan = phase30_points.point_plan(key)
        dirs.append(":(exclude)results/" + plan["prefix"] + "_" + plan["arm"])
    return (*dirs, ":(exclude)" + phase29_prereg.POINT_RECORD_PREFIX + "*.json")


def _is_refused(rel):
    return json.loads((_GIT_ROOT / rel).read_text(encoding="utf-8")).get("rule") == "PREREG-03"


def run(*, heartbeat_path=phase25_run.HEARTBEAT_PATH, past_stop_line=None):
    """Walk ``SWEEP_SCHEDULE()`` once: skip tracked, refuse or train each key, commit each record
    alone, and exit 0 at the committed stop line unless a ruling was given. Returns 0."""
    heartbeat_path = pathlib.Path(heartbeat_path)
    phase25_run.disk_precheck()
    refuse_if_dirty(
        who="phase32_points",
        detail=(
            "every point record names the commit its stages ran from; a sweep started from a "
            "dirty tree runs code that commit does not contain"
        ),
        pathspec=("scripts", "src", "results", *_run_excludes()),
        cwd=_CODE_ROOT,
    )
    schedule = phase30_points.SWEEP_SCHEDULE()
    record_of = {key: phase29_prereg.point_record_path(key) for key in schedule}
    key_of = {rel: key for key, rel in record_of.items()}
    tracked = tracked_results()

    # D-11 interrupted commit: a TRAINED record written but not committed is committed first.
    # PREREG-03 records are left to the refuse branch, whose write_refused_records byte-checks
    # them before commit_untracked commits them.
    pending = [
        rel
        for rel in record_of.values()
        if rel not in tracked and (_GIT_ROOT / rel).exists() and not _is_refused(rel)
    ]
    if pending:
        commit_untracked(pending, lambda rel: commit_message(key_of[rel]))
        tracked = tracked_results()

    if all(rel in tracked for rel in record_of.values()):
        print(f"[phase32_points] all {len(schedule)} point records are tracked: complete")
        return 0

    line, clock = stop_line_seconds(tracked), cumulative_seconds(tracked)
    manual = MANUAL_RELAUNCH
    _prove(
        clock < line or past_stop_line is not None,
        f"the cumulative clock {clock} s has reached the committed stop line {line} s (D-04). "
        f"Continuing needs the developer's ruling (D-06, D-20): {manual}",
    )
    _prove(
        past_stop_line is None or clock >= line,
        f"--past-stop-line given while the cumulative clock {clock} s is below the stop line "
        f"{line} s: a ruling cannot be pre-armed (D-06)",
    )

    for key in schedule:
        if record_of[key] in tracked:
            print(f"[phase32_points] {key}: RECORDED already (tracked) — skipping", flush=True)
            continue
        clock = cumulative_seconds(tracked)
        if clock >= line and past_stop_line is None:
            phase25_run.beat(
                heartbeat_path,
                point=key,
                stage="stop_line",
                shape=f"cumulative_seconds={clock}",
                draw_index=None,
            )
            print(
                f"[phase32_points] STOP LINE: cumulative {clock} s >= {line} s before {key} "
                f"(D-04). Relaunch past it only with a ruling: {manual}",
                flush=True,
            )
            return 0
        act = phase30_points.next_action(key, tracked)
        if act["action"] == "refuse":
            phase30_points.write_refused_records(act["records"])
            commit_untracked(
                [record_of[k] for k in sorted(act["records"])],
                lambda rel: commit_message(key_of[rel], refused=True),
            )
        else:
            run_point(
                act["plan"],
                tracked,
                heartbeat_path=heartbeat_path,
                stop_line={
                    "seconds": line,
                    "cumulative_before_point": clock,
                    "past_line_ruling": past_stop_line,
                },
            )
        tracked = tracked_results()
    return 0
