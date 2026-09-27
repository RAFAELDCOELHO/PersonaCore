"""Phase 32 v5.0 sweep driver (AFRONT-01): import-and-override of the frozen v4.0 stages
(Phase 30 D-13).

THE LIBRARY HALF. Everything the v5.0 run loop needs except the loop itself (plan 32-04 wires it):

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
