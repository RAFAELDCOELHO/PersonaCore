"""PHASE 36 COST-01 — the v6.0 MPS cost probes: time and counts only, never a reading (D-01).

THE SPLIT (Phase 31's). ``run`` executes each front's stage inside ``run_front`` — a ledger start
line, one heartbeat at once, a beat every 60 s, then the end line naming the front's record — and
writes a gitignored ``data/probe36_<front>_run.json`` sidecar. ``emit`` turns one sidecar into the
write-once ``results/phase36_probe_<front>.json`` (overwrite refusal first, dirty refusal second,
WR-02 third). ``emit-all`` commits the ledger, then each record in ``RUN_ORDER``, one path per
commit, and resumes after an abort (D-16, W4).

WHAT SURVIVES (D-01, D-18). Seconds and counts. The pin's draws are written to a ``data/`` file the
stage deletes after timing, its returned payload is never bound, and its stdout goes to a buffer
that is dropped. ``prove_no_reading`` refuses any record key that names a reading.

Torch-free at import: every torch-touching module is imported inside the stage functions.
"""

import argparse
import contextlib
import datetime
import hashlib
import io
import json
import math
import pathlib
import shutil
import statistics
import subprocess
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent
# The git root. Same value as _ROOT at import, but never patched in production: every git call and
# every module hash reads it, so a test that redirects _ROOT (the data/ sidecars) changes no git
# answer.
_GIT_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_GIT_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
_SRC = str(_GIT_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import phase25_points  # noqa: E402  (scripts/ is not a package; torch-free)
import phase25_run  # noqa: E402  (same)
import phase30_points  # noqa: E402  (same)
import phase35_prereg  # noqa: E402  (same)
import phase36_caps  # noqa: E402  (same)
import phase36_ledger  # noqa: E402  (same)
import phase36_prereg  # noqa: E402  (same)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

INSTRUMENT_GIT_SHA = git_sha()

# =================================================================================================
# IDENTITY AND ISOLATION (COST-01)
# =================================================================================================

PROBE_PREFIX = "probe36"
# Cheap fronts first, so a wiring failure surfaces in minutes rather than after the E1 hours.
RUN_ORDER = ("e5", "e6", "e3", "e2", "e1")
# front -> stage function. Each stage takes the live heartbeat ``state`` and returns a dict with
# "configuration", its own numbers, and "reused" ({front: bool}); run_front moves "reused" to the
# sidecar's top level. Plans 36-04/36-05 register e5, e6, e3, e2.
STAGES = {}
# E2's two M2 repetitions (H1, D-02). Never "real": that arm's adapter IS persona_adapter.pt.
E2_ARMS = ("probe36_m2_a", "probe36_m2_b")
# Every probe36 path a stage leaves on disk outside results/ (preflight's stray scan, W3). Anything
# under results/probe36_* belongs to no front: the stages move their csv out in-process (WR-01).
STRAY_GLOBS = (
    "data/probe36_*",
    "checkpoints/probe36_*",
    "data/phase25_probe36_*",
    "data/persona_probe36_*",
)
RESULTS_STRAY_GLOB = "results/probe36_*"
# front -> builder(stages) -> (record stages, repetitions). Filled beside each stage.
RECORD_BUILDERS = {}

# Committed inputs, read only through _committed_json (a tracked blob, never the working tree).
CURVE_RECORD = "results/phase19_collateral_curve.json"  # phase19_run.TARGET_CURVE_PATH
ERASED_RECORD = "results/phase19_arm_erased.json"  # phase19_erasure.arm_record_path("erased")
PHASE31_POINT_RECORD = "results/phase31_probe_point.json"  # COST-01: beside, never an input

PINNED_MODULES = tuple(
    pathlib.Path(path).resolve().relative_to(_GIT_ROOT).as_posix()
    for path in (
        __file__,
        phase36_prereg.__file__,
        phase36_ledger.__file__,
        _SCRIPTS + "/phase35_prereg.py",  # a path: the census refuses phase35_prereg._* reads
        phase25_run.__file__,
        phase25_points.__file__,
        # Paths, not imports: these import torch.
        _SCRIPTS + "/phase19_erasure.py",
        _SCRIPTS + "/phase14_recall.py",
        _SCRIPTS + "/phase18_extraction.py",
        _SCRIPTS + "/phase14_factset_gate.py",
        _SCRIPTS + "/phase17_persona_gate.py",
        _SCRIPTS + "/teach_persona.py",
        _SRC + "/personacore/training/loop.py",
    )
)

# D-16: the only EXECUTABLE git actions, and the read-only ones (AST-checked by the tests).
ALLOWED_GIT_ACTIONS = ("add", "commit")
READ_ONLY_GIT_ACTIONS = ("ls-files", "show", "rev-parse", "status", "diff", "log", "merge-base")

# D-01 / D-18: no record key names a reading, and strings live only where they describe the run.
READING_TOKENS = frozenset(
    {
        "hit",
        "hits",
        "success",
        "successes",
        "recall",
        "rate",
        "rates",
        "rank",
        "ranks",
        "nll",
        "text",
        "texts",
        "completion",
        "completions",
        "exposure",
        "gain",
        "extracted",
        "reading",
        "readings",
        "verdict",
        "loss",
        "ppl",
        "fact",
    }
)
STR_KEYS = frozenset(
    {
        "front",
        "probe_key",
        "run_id",
        "sweep_point_false_reason",
        "no_result_note",
        "path",
        "sha256",
        "device",
        "torch_version",
        "unit",
    }
)
STR_SUBTREES = ("provenance", "configuration")
# The one key-token exemption: Phase 31's own published stage names ("recall" there names a timed
# stage, not a reading). Their values must still be numbers.
BESIDE_KEY = "beside_never_extrapolated"
BESIDE_STAGES_KEY = "stage_seconds"

SWEEP_POINT_FALSE_REASON = (
    "a timing probe on an already-published configuration; it gates nothing and no verdict reads "
    "it (D-01, Phase 31 D-02)"
)
NO_RESULT_NOTE = (
    "seconds and counts only; draws, generated text and success counts were discarded (D-01, D-18)"
)


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase36_probe] {message}")


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _rel(path):
    path = pathlib.Path(path)
    return path.relative_to(_ROOT).as_posix() if path.is_relative_to(_ROOT) else str(path)


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _spread(values):
    return {
        "n": len(values),
        "min": min(values),
        "median": statistics.median(values),
        "max": max(values),
    }


def _committed_json(rel):
    """A TRACKED file's committed blob, refused if the working tree differs (CR-01)."""
    return phase30_points._tracked_json(rel, phase36_caps.tracked_files(), "the committed input")


_prove(set(RUN_ORDER) == set(phase36_prereg.PROBE_FRONTS), "RUN_ORDER is not PROBE_FRONTS")


def prove_isolated_label(label):
    """COST-01: every probe label starts ``probe36`` and none resolves under a sweep prefix."""
    for banned in ("phase3", "phase4", phase25_points.CALIBRATION_PREFIX_LITERAL):
        _prove(
            not label.startswith(banned),
            f"probe label {label!r} resolves under {banned!r}: a probe output could collide with "
            "a published or later-phase artifact",
        )
    _prove(label.startswith(PROBE_PREFIX), f"probe label {label!r} does not start {PROBE_PREFIX}")
    return label


def _data_path(name):
    return _ROOT / "data" / prove_isolated_label(name)


def run_sidecar(front):
    _prove(front in phase36_prereg.PROBE_FRONTS, f"front {front!r} is not a probe front")
    return _data_path(f"{PROBE_PREFIX}_{front}_run.json")


def sessions_sidecar(front):
    _prove(front in phase36_prereg.PROBE_FRONTS, f"front {front!r} is not a probe front")
    return _data_path(f"{PROBE_PREFIX}_{front}_sessions.json")


def arm_record_path(front, rep):
    _prove(front in phase36_prereg.PROBE_FRONTS, f"front {front!r} is not a probe front")
    return _data_path(f"{PROBE_PREFIX}_{front}_rep{rep}_arm.json")


# =================================================================================================
# D-01 / D-18: THE READING GATE, THE SILENCER AND THE DRAW TIMER
# =================================================================================================


def prove_no_reading(blob):
    """Refuse a reading key anywhere in ``blob``, and a str leaf outside the allowed places."""

    def walk(node, key, path, free):
        if isinstance(node, dict):
            exempt = path[-2:] == (BESIDE_KEY, BESIDE_STAGES_KEY)
            for child_key, child in node.items():
                _prove(isinstance(child_key, str), f"non-str key {child_key!r} at {path}")
                if exempt:
                    _prove(
                        isinstance(child, (int, float)) and not isinstance(child, bool),
                        f"{'.'.join(path)}.{child_key} is {child!r}, not a number",
                    )
                    continue
                hits = set(child_key.split("_")) & READING_TOKENS
                _prove(
                    not hits,
                    f"key {'.'.join((*path, child_key))!r} names a reading ({sorted(hits)}): a "
                    "probe record carries seconds and counts only (D-01, D-18)",
                )
                walk(child, child_key, (*path, child_key), free or child_key in STR_SUBTREES)
        elif isinstance(node, list):
            for child in node:
                walk(child, key, path, free)
        elif isinstance(node, str):
            _prove(
                free or key in STR_KEYS,
                f"string at {'.'.join(path)!r} outside provenance/configuration and STR_KEYS: a "
                "probe record never carries text (D-01, D-18)",
            )
        else:
            _prove(
                node is None or isinstance(node, (bool, int, float)),
                f"{'.'.join(path)!r} holds a {type(node).__name__}",
            )

    walk(blob, None, (), False)
    return blob


@contextlib.contextmanager
def silenced():
    """D-18: the pin's stdout goes to a buffer that is never read, so no reading reaches the log."""
    with contextlib.redirect_stdout(io.StringIO()):
        yield


class DrawTimer:
    """Times every ``phase14_recall._complete`` call (no file edited); restores it on exit.

    Each row is ``{"seconds", "tokens", "at_cap"}`` — the generated ids are never kept.
    """

    def __enter__(self):
        import phase14_recall  # torch at import: lazy

        self._module, self._real, self.rows = phase14_recall, phase14_recall._complete, []
        real, rows = self._real, self.rows

        def timed(*args, **kwargs):
            started = time.monotonic()
            gen, stopped = real(*args, **kwargs)
            rows.append(
                {"seconds": time.monotonic() - started, "tokens": len(gen), "at_cap": not stopped}
            )
            return gen, stopped

        phase14_recall._complete = timed
        return self

    def __exit__(self, *exc):
        self._module._complete = self._real
        return False


# =================================================================================================
# WR-02: the stages ran on the code that writes the record (scripts/phase32_points.py:334-376)
# =================================================================================================


def record_session(front):
    """Append this session's ``{git_sha, started_utc}`` to the front's sessions sidecar."""
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=_GIT_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    path = sessions_sidecar(front)
    sessions = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    sessions.append({"git_sha": head, "started_utc": _now()})
    phase25_run.atomic_write_json(path, sessions)
    return sessions


def prove_pinned_unchanged(shas):
    """WR-02: no pinned module differs between any recorded session commit and HEAD."""
    for sha in dict.fromkeys(shas):
        diff = subprocess.run(
            ["git", "diff", "--name-only", sha, "HEAD", "--", *PINNED_MODULES],
            cwd=_GIT_ROOT,
            capture_output=True,
            text=True,
        )
        _prove(
            diff.returncode == 0, f"unknown sha {sha!r}: git diff failed ({diff.stderr.strip()})"
        )
        changed = diff.stdout.split()
        _prove(
            not changed,
            f"pinned modules {changed} changed between session commit {sha} and HEAD (WR-02): the "
            "record would name code its seconds did not come from. Every scripts/ change must land "
            "before launch",
        )


# =================================================================================================
# THE RUN (D-11, D-12, B1)
# =================================================================================================


def run_front(front, *, heartbeat_path, ledger_path):
    """One front: ledger start, one beat at once, the 60-s beats, the stage, sidecar, end line."""
    sidecar = run_sidecar(front)
    if sidecar.exists():
        print(f"[phase36_probe] {front} skipped: {_rel(sidecar)} exists", flush=True)
        return json.loads(sidecar.read_text(encoding="utf-8"))
    _prove(front in STAGES, f"front {front!r} has no registered stage")
    record_session(front)
    rid = phase36_ledger.run_id(36, "probes", front)
    phase36_ledger.append("start", run_id=rid, phase=36, front="probes", ledger_path=ledger_path)
    state = {"point": rid, "stage": "start", "shape": None, "draw_index": None}
    # B1: the thread's first beat comes only after wait(60) (phase25_run._heartbeat_loop), so a
    # stage dying in its first minute would leave no beat after its own start: beat once now.
    phase25_run.beat(heartbeat_path, **state)
    stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
    started_utc, started = _now(), time.monotonic()
    try:
        stages = STAGES[front](state)
        import torch  # every stage has imported it already

        reused = stages.pop("reused")
        run = {
            "front": front,
            "run_id": rid,
            "run_git_sha": git_sha(),
            "device": str(phase25_run.device()),
            "torch_version": torch.__version__,
            "started_utc": started_utc,
            "finished_utc": _now(),
            "reused": reused,
            "stages": stages,
        }
        phase25_run.atomic_write_json(sidecar, run)
        state.update(stage="done", shape=None, draw_index=None)
    finally:
        stop.set()
        thread.join()
    phase36_ledger.append(
        "end",
        run_id=rid,
        phase=36,
        front="probes",
        record=phase36_prereg.probe_record(front),
        ledger_path=ledger_path,
    )
    print(f"[phase36_probe] {front} {time.monotonic() - started:.1f} s", flush=True)
    return run


def run_all(*, heartbeat_path=None, ledger_path=None, fronts=RUN_ORDER):
    """Every front in order, after the dirty and disk refusals."""
    for front in fronts:
        _prove(front in STAGES, f"front {front!r} has no registered stage")
    refuse_if_dirty(
        who="phase36_probe",
        detail=(
            "a probe record names the commit it ran from; a run from a dirty tree times code that "
            "commit does not contain"
        ),
        pathspec=("scripts", "src", "results"),
        cwd=_GIT_ROOT,
    )
    phase25_run.disk_precheck()
    heartbeat_path = phase36_ledger.HEARTBEAT_PATH if heartbeat_path is None else heartbeat_path
    ledger_path = _GIT_ROOT / phase36_ledger.LEDGER_PATH if ledger_path is None else ledger_path
    return [run_front(f, heartbeat_path=heartbeat_path, ledger_path=ledger_path) for f in fronts]


# =================================================================================================
# E1 (D-03, D-04, D-18): the pin itself, twice at K = 48, with K = 16 by prefix stability
# =================================================================================================


def e1_shape():
    """``(questions, K)``: the A2 corpus size and the pin's own K source (phase19_erasure :2825)."""
    import phase19_erasure  # torch at import: lazy

    questions = len(phase35_prereg.a2_corpus_entries())
    record = json.loads(phase19_erasure.PHASE18_ARM_RECORD_PATH.read_text(encoding="utf-8"))
    k = record["config"]["k"]
    _prove(k == phase35_prereg.FULL_FIDELITY_K, f"the pin's K {k} is not FULL_FIDELITY_K")
    erased = _committed_json(ERASED_RECORD)["config"]
    _prove(
        erased["attack_family"] == "A2" and erased["corpus_entries"] == questions,
        f"{ERASED_RECORD} drew {erased['corpus_entries']} {erased['attack_family']} questions, not "
        f"the {questions} A2 entries",
    )
    return questions, k


def e1_components():
    """The published ablation: the curve's ordered prefix cut at the erased arm's own length.

    Reads ONLY the two committed JSON files — never the adapter (B1: the .pt is gitignored)."""
    curve = _committed_json(CURVE_RECORD)
    erased = _committed_json(ERASED_RECORD)["config"]["ablated_components"]
    components = [tuple(a) for a in curve["ordered_prefix"][: len(erased)]]
    _prove(
        [list(c) for c in components] == erased,
        f"{CURVE_RECORD}'s ordered prefix is not {ERASED_RECORD}'s ablated_components",
    )
    return components


def published_adapter_sha256():
    return _committed_json(CURVE_RECORD)["adapter_in_sha256"]


def prove_published_adapter():
    """The adapter on disk is the one the committed curve was swept on (read at call time)."""
    import phase14_recall  # torch at import: lazy

    path = phase14_recall.ADAPTER_PATH
    _prove(pathlib.Path(path).exists(), f"{path} is missing: E1 times the published adapter")
    _prove(
        _sha256(path) == published_adapter_sha256(),
        f"{path} is not the adapter {CURVE_RECORD} was swept on (adapter_in_sha256)",
    )


def _e1_run(total_seconds, rows, questions, k):
    """One pin run's numbers from its total and the timer's rows, in call order (pure)."""
    _prove(
        len(rows) == questions * k,
        f"the draw timer counted {len(rows)} draws, not {questions} x {k} (D-18)",
    )
    seconds = [float(r["seconds"]) for r in rows]
    per_question = [seconds[q * k : (q + 1) * k] for q in range(questions)]
    draw_sum = math.fsum(seconds)
    fixed = total_seconds - draw_sum
    _prove(fixed >= 0, f"the draws took {draw_sum} s, longer than the run's {total_seconds} s")
    first = [q[: phase35_prereg.CURVE_K] for q in per_question]
    at_cap = [s for s, r in zip(seconds, rows, strict=True) if r["at_cap"]]
    return {
        "total_seconds": total_seconds,
        "draws": len(rows),
        "draw_seconds_sum": draw_sum,
        "fixed_seconds": fixed,
        "k16_seconds": fixed + math.fsum(s for q in first for s in q),
        "per_question_k16_seconds": [math.fsum(q) for q in first],
        "per_question_k48_seconds": [math.fsum(q) for q in per_question],
        "draw_seconds_spread": _spread(seconds),
        "at_cap_draws": len(at_cap),
        "at_cap_seconds_spread": _spread(at_cap) if at_cap else None,
        "draw_seconds": seconds,
        "draw_tokens": [int(r["tokens"]) for r in rows],
    }


def stage_e1(state):
    """Two K = 48 runs of the pin on the published ablation; only time and counts survive."""
    import phase14_recall  # torch at import: lazy
    import phase19_erasure  # same

    questions, k = e1_shape()
    components = e1_components()
    erased = _committed_json(ERASED_RECORD)["config"]["ablated_components"]
    _prove(
        [list(c) for c in components] == erased,
        f"the components are not {ERASED_RECORD}'s config.ablated_components (D-03)",
    )
    prove_published_adapter()
    device = phase25_run.device()
    runs = []
    for rep in (1, 2):
        path = arm_record_path("e1", rep)
        _prove(
            not path.exists(),
            f"{_rel(path)} exists: stale probe output from an interrupted run. Delete it, then "
            "rerun",
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        state.update(stage=f"e1_rep{rep}", shape=None, draw_index=None)
        try:
            with DrawTimer() as timer, silenced():
                started = time.monotonic()
                phase19_erasure.run_erasure_arm(
                    "erased", device, components=components, record_path=path
                )
                total = time.monotonic() - started
        finally:
            path.unlink(missing_ok=True)  # D-01 / D-18: the draws are discarded
        runs.append(_e1_run(total, timer.rows, questions, k))
    prove_published_adapter()
    configuration = {
        "arm": "erased",
        "k": len(components),
        "K": k,
        "k16": phase35_prereg.CURVE_K,
        "questions": questions,
        "seed": phase14_recall.SEED,
        "ordering": f"greedy (Phase 19 M1, {CURVE_RECORD} ordered_prefix)",
        "target_slot": phase19_erasure.TARGET_SLOT,
        "adapter_in_sha256": published_adapter_sha256(),
        "components_sha256": hashlib.sha256(
            json.dumps([list(c) for c in components]).encode("utf-8")
        ).hexdigest(),
        "e1_targets": len(phase35_prereg.e1_targets()),
        "e1_teaching_seeds": len(phase35_prereg.e1_teaching_seeds()),
    }
    return {"configuration": configuration, "runs": runs, "reused": {"e1": False}}


def _e1_stages(stages):
    """The two runs unchanged (fixed costs stay separate, D-18) + R1b's K = 48 totals (D-04)."""
    runs = stages["runs"]
    _prove(len(runs) == 2, f"E1 holds {len(runs)} runs, not 2")
    return {"runs": runs, "r1b_k48_totals": [r["total_seconds"] for r in runs]}, len(runs)


STAGES["e1"] = stage_e1
RECORD_BUILDERS["e1"] = _e1_stages


# =================================================================================================
# E6 (D-07) and E5 (D-08): inference only, on the published adapter and the published clearance
# =================================================================================================


def adapted_model(device, k):
    """``(model, tok, forbid)``: the published adapter, its first ``k`` curve components ablated.

    The pin's own two lines (phase19_erasure.run_erasure_arm): ``load_adapted_model`` then
    ``load_adapter_weights(ablate_components(...))`` — never ``inject_lora`` (ISO-06)."""
    import phase14_recall  # torch at import: lazy
    import phase19_erasure  # same

    from personacore.lora import load_adapter_weights

    prove_published_adapter()  # B1: the one adapter identity check
    model, _cfg, tok, forbid, artifact = phase14_recall.load_adapted_model(device)
    if k > 0:
        load_adapter_weights(
            model, phase19_erasure.ablate_components(artifact, e1_components()[:k])
        )
    return model, tok, forbid


def stage_e6(state):
    """D-07: anchor-context generation on the k = 78 adapter, K draws per locked slot; time only."""
    import phase14_factset  # torch-free, but lazy like every fact-set read
    import phase14_recall  # torch at import: lazy
    import phase18_extraction  # same

    from personacore.dialogue import ASSISTANT_ID

    k = len(e1_components())
    K = phase35_prereg.FULL_FIDELITY_K
    slots = [f.slot for f in phase14_factset.LOCKED_FACTS]
    frame = phase18_extraction.ADMISSIBLE_NLL_FRAME
    device = phase25_run.device()
    state.update(stage="e6_setup", shape=None, draw_index=None)
    started = time.monotonic()
    model, tok, forbid = adapted_model(device, k)
    setup_seconds = time.monotonic() - started
    values = [f.value for f in phase14_factset.LOCKED_FACTS + phase14_factset.SOFT_TIER_FACTS]
    with DrawTimer() as timer, silenced():
        for i, slot in enumerate(slots):
            state.update(stage="e6_anchor", shape=slot, draw_index=i)
            forms = phase14_factset.SLOT_FORMS[slot]
            ids = [ASSISTANT_ID] + list(
                tok.encode(phase18_extraction._frame_preamble(forms, frame))
            )
            # B2 / PERS-06: nothing draws unchecked, on the ids actually dispatched.
            phase14_recall.assert_no_value_in_prompt(tok, tok.decode(ids), values, prompt_ids=ids)
            # i * K: the disjoint seed windows draw_all's docstring leaves to the caller (D-06).
            phase14_recall.draw_all(model, tok, ids, device, forbid, i * K, n_samples=K - 1)
    total = time.monotonic() - started
    rows = timer.rows
    _prove(
        len(rows) == len(slots) * K,
        f"the draw timer counted {len(rows)} draws, not {len(slots)} x {K} (D-07)",
    )
    seconds = [float(r["seconds"]) for r in rows]
    configuration = {
        "arm": "erased",
        "k": k,
        "K": K,
        "anchor_slots": len(slots),
        "frame": frame,
        "seed": phase14_recall.SEED,
        "context": (
            "[ASSISTANT_ID] + the frame preamble (phase18_extraction.value_span_nll's anchor) — an "
            "unpublished configuration ruled timing-only by Rafael (D-07)"
        ),
    }
    return {
        "configuration": configuration,
        "setup_seconds": setup_seconds,
        "per_slot_draw_seconds_mean": [
            statistics.fmean(seconds[i * K : (i + 1) * K]) for i in range(len(slots))
        ],
        "draws": len(rows),
        "at_cap_draws": sum(bool(r["at_cap"]) for r in rows),
        "draw_seconds_spread": _spread(seconds),
        "total_seconds": total,
        "reused": {"e6": False},
    }


def _e6_stages(stages):
    """The stage numbers as measured; one H3 block per anchor slot."""
    out = {key: value for key, value in stages.items() if key != "configuration"}
    return out, len(out["per_slot_draw_seconds_mean"])


def e6_a2_context_beside():
    """D-07: the A2-context per-question unit, read from the E1 probe's sidecar — no extra run."""
    sidecar = run_sidecar("e1")
    _prove(
        sidecar.exists(),
        f"{_rel(sidecar)} is missing: E6's A2-context unit comes from the E1 probe (D-07)",
    )
    runs = json.loads(sidecar.read_text(encoding="utf-8"))["stages"]["runs"]
    _prove(len(runs) == 2, f"the E1 sidecar holds {len(runs)} runs, not 2")
    high = max(statistics.fmean(r["per_question_k48_seconds"]) for r in runs)
    return {
        "a2_context_from_e1": {"a2_context_question_k48_seconds_high": high, "path": _rel(sidecar)}
    }


def stage_e5(state):
    """D-08: Phase 17's clearance re-run on the un-adapted base, then the E5 scoring sample."""
    import phase14_factset  # lazy: fact material
    import phase14_factset_gate  # torch at import: lazy
    import phase16_persistence  # same
    import phase17_isolation  # same
    import phase17_persona_facts  # lazy: fact material
    import phase17_persona_gate as gate  # torch at import: lazy
    import phase17_personas  # same
    import phase18_extraction  # same
    import phase19_erasure  # same

    from personacore.config import ModelConfig
    from personacore.tokenizer import from_json

    device = phase25_run.device()
    slots = phase17_personas.CORE_SLOTS
    personas = phase17_persona_facts.PERSONA_FACTS
    published_values = sum(len(facts) for facts in personas.values())

    # Clearance (phase17_persona_gate.py:285-345): one cached probe pass per slot, then one string
    # check per published value. The cache holds completions in memory only and is never written.
    state.update(stage="e5_clearance", shape=None, draw_index=None)
    started = time.monotonic()
    model, _cfg, _ckpt = gate.build_unadapted_base(device)
    tok = from_json(gate.TOKENIZER_PATH)
    forbid = phase16_persistence.resolve_forbid(tok, ModelConfig.vocab_size)[0].to(device)
    setup_seconds = time.monotonic() - started
    by_slot = phase17_isolation.held_out_by_slot()
    questions = {slot: tuple(item.question for item in items) for slot, items in by_slot.items()}
    cache, per_slot, match_seconds = {}, [], []
    with silenced():
        for i, slot in enumerate(slots):
            state.update(shape=slot, draw_index=i)
            anchor = next(f.value for f in personas[phase17_personas.PERSONAS[0]] if f.slot == slot)
            fresh = tuple(q for q in questions[slot] if q not in cache)
            slot_started = time.monotonic()
            probed = phase14_factset_gate.probe_guessability(
                model, tok, device, forbid, anchor, fresh, start_index=len(cache)
            )
            per_slot.append(time.monotonic() - slot_started)
            for entry in probed["probes"]:
                cache[entry["question"]] = entry["completions"]
            del probed
            texts = [text for question in questions[slot] for text in cache[question]]
            for facts in personas.values():
                for fact in facts:
                    if fact.slot != slot:
                        continue
                    match_started = time.monotonic()
                    phase14_factset.exact_match_clean(texts, fact.value)
                    match_seconds.append(time.monotonic() - match_started)
            del texts
    clearance_total = time.monotonic() - started
    _prove(
        len(cache) == phase17_personas.QUESTIONS_PER_SLOT * len(slots),
        f"{len(cache)} questions probed, not {phase17_personas.QUESTIONS_PER_SLOT} x {len(slots)}",
    )
    _prove(
        len(match_seconds) == published_values,
        f"{len(match_seconds)} candidates matched, not the {published_values} published values",
    )
    del cache, model

    # The E5 scoring sample: value_span_nll_mean per reference-set candidate, on k = 0 and k = 78.
    locked = [f.slot for f in phase14_factset.LOCKED_FACTS]
    adapters, every = [], []
    with silenced():
        for k in (0, len(e1_components())):
            state.update(stage=f"e5_scoring_k{k}", shape=None, draw_index=None)
            adapter_started = time.monotonic()
            model, tok, _forbid = adapted_model(device, k)
            adapter_setup = time.monotonic() - adapter_started
            means, sizes = [], []
            for i, slot in enumerate(locked):
                state.update(shape=slot, draw_index=i)
                seconds = []
                for value in phase18_extraction.reference_set_for(slot):
                    candidate_started = time.monotonic()
                    phase19_erasure.value_span_nll_mean(model, tok, device, slot=slot, value=value)
                    seconds.append(time.monotonic() - candidate_started)
                means.append(statistics.fmean(seconds))
                sizes.append(len(seconds))
                every += seconds
            adapters.append(
                {
                    "k": k,
                    "setup_seconds": adapter_setup,
                    "per_slot_mean_candidate_seconds": means,
                    "candidates_per_slot": sizes,
                    "candidates": sum(sizes),
                }
            )
            del model
    configuration = {
        "slots": len(slots),
        "questions_per_slot": phase17_personas.QUESTIONS_PER_SLOT,
        "published_values": published_values,
        "clearance_unit": (
            "per slot: one cached probe_guessability pass over the slot's held-out questions; per "
            "candidate: an exact_match_clean string check (phase17_persona_gate.py:285-345)"
        ),
        "scoring_frame": phase18_extraction.ADMISSIBLE_NLL_FRAME,
        "scoring_instrument": "phase19_erasure.value_span_nll_mean",
    }
    return {
        "configuration": configuration,
        "clearance": {
            "setup_seconds": setup_seconds,
            "per_slot_seconds": per_slot,
            "match_seconds_spread": _spread(match_seconds),
            "candidates_matched": len(match_seconds),
            "total_seconds": clearance_total,
        },
        "scoring": {"adapters": adapters, "candidate_seconds_spread": _spread(every)},
        "reused": {"e5": False},
    }


def _e5_stages(stages):
    """The clearance and scoring blocks as measured; one H3 block per slot."""
    out = {key: value for key, value in stages.items() if key != "configuration"}
    return out, len(out["clearance"]["per_slot_seconds"])


STAGES["e6"] = stage_e6
RECORD_BUILDERS["e6"] = _e6_stages
STAGES["e5"] = stage_e5
RECORD_BUILDERS["e5"] = _e5_stages


# =================================================================================================
# E3 (D-05, D-19): the published v4.0 sigma point, trained at T = STEP_BUDGET and T = e3_max_steps
# =================================================================================================


@contextlib.contextmanager
def loop_timer(tp):
    """Sum the seconds spent inside ``tp.train`` (the training loop) and count its calls.

    The teaching driver resolves ``train`` from its module globals at call time, so swapping the
    attribute times the loop with no file edited (scripts/phase31_probe.py's wrap). Restored on
    exit, exception or not."""
    real, box = tp.train, {"seconds": 0.0, "calls": 0}

    def timed(*args, **kwargs):
        started = time.monotonic()
        try:
            return real(*args, **kwargs)
        finally:
            box["seconds"] += time.monotonic() - started
            box["calls"] += 1

    tp.train = timed
    try:
        yield box
    finally:
        tp.train = real


def e3_steps():
    """``(STEP_BUDGET run, e3_max_steps run)``: the pre-registered E3 probe step counts (D-05)."""
    short, longest = phase36_prereg.ENTRIES["e3_probe_steps"]["value"]
    return short, longest


def e3_plan(steps):
    """The published point re-keyed to probe36 labels, its pinned step count set to ``steps``."""
    plan = phase25_points.point_plan(phase36_prereg.E3_PROBE_POINT_KEY)
    _prove(
        plan["arm"] == f"dp_n{phase35_prereg.E3_N}"
        and plan["dp_sigma"] == phase35_prereg.E3_SIGMAS[1],
        f"{phase36_prereg.E3_PROBE_POINT_KEY} plans arm {plan['arm']!r} at sigma "
        f"{plan['dp_sigma']!r}, not the dp_n{phase35_prereg.E3_N} sigma "
        f"{phase35_prereg.E3_SIGMAS[1]} point (D-05)",
    )
    return dict(
        plan,
        point_key=prove_isolated_label(f"{PROBE_PREFIX}_e3_t{steps}"),
        prefix=prove_isolated_label(f"{PROBE_PREFIX}_t{steps}"),
        pinned_mechanism=dict(plan["pinned_mechanism"], composed_steps=steps),
    )


def stage_e3(state):
    """D-05 / D-19: train the point at both step counts; score taught recall at STEP_BUDGET only."""
    import phase14_factset as fs  # lazy: fact material
    import phase14_recall  # torch at import: lazy
    import teach_persona as tp  # same

    # RECIPE-04 FIRST, on the REAL cap — never the fixture's step counts.
    phase36_prereg.prove_p22(phase36_prereg.ENTRIES["e3_max_steps"]["value"])
    plans = [e3_plan(steps) for steps in e3_steps()]
    # Pitfall 5 / W2: train_stage REUSES a sidecar (0 s) and RESUMES a _latest.pt (partial seconds).
    for plan in plans:
        outputs = tp.arm_outputs(plan["arm"], prefix=plan["prefix"])
        for path in (
            phase25_points.training_sidecar(plan["point_key"]),
            outputs["adapter"],
            outputs["checkpoint"],
        ):
            _prove(
                not path.exists(),
                f"{_rel(path)} exists: train_stage would reuse or resume it and price 0 s or "
                "partial seconds (Pitfall 5, W2). Delete it in a reviewed step, then rerun",
            )
    device = phase25_run.device()
    runs = []
    for index, plan in enumerate(plans):
        steps = plan["pinned_mechanism"]["composed_steps"]
        state.update(stage=f"e3_t{steps}", shape=None, draw_index=None)
        real_steps = tp.MAX_STEPS
        tp.MAX_STEPS = steps
        try:
            with loop_timer(tp) as loop, silenced():
                blob = phase25_points.train_stage(plan)
        finally:
            tp.MAX_STEPS = real_steps
        _prove(loop["calls"] == 1, f"the training loop ran {loop['calls']} times, not once")
        composed = blob["live_mechanism"]["composed_steps"]  # W8: nested, never top-level
        _prove(composed == steps, f"the seam composed {composed} steps, not {steps}")
        _prove(
            blob["resumed_from_step"] == 0,
            f"the T = {steps} run resumed from step {blob['resumed_from_step']}: its seconds "
            "cover only the remaining steps (W2)",
        )
        run = {
            "train_seconds": blob["seconds"],  # the v4.0 comparator's training.seconds field
            "loop_seconds": loop["seconds"],
            "overhead_seconds": blob["seconds"] - loop["seconds"],
            "steps": steps,
        }
        if index == 0:
            adapter = tp.arm_outputs(plan["arm"], prefix=plan["prefix"])["adapter"]
            _prove(
                _sha256(adapter) == blob["adapter_sha256"],
                f"{_rel(adapter)} is not the adapter the T = {steps} run trained",
            )
            state.update(stage="e3_score", shape=None, draw_index=None)
            with DrawTimer() as timer, silenced():
                started = time.monotonic()
                tp.score_arm(plan["arm"], fs.LOCKED_FACTS, adapter, device)
                score_seconds = time.monotonic() - started
            draw_seconds = [float(row["seconds"]) for row in timer.rows]
            per_question = 1 + phase14_recall.N_SEEDED_SAMPLES
            _prove(
                draw_seconds and len(draw_seconds) % per_question == 0,
                f"score_arm drew {len(draw_seconds)} times, not a multiple of the {per_question} "
                "draws per question (greedy + N_SEEDED_SAMPLES)",
            )
            run.update(
                score_seconds=score_seconds,
                score_draws=len(draw_seconds),
                score_draws_per_question=per_question,
                score_fixed_seconds=score_seconds - math.fsum(draw_seconds),
                score_draw_seconds=draw_seconds,
            )
        runs.append(run)
    configuration = {
        "point_key": phase36_prereg.E3_PROBE_POINT_KEY,
        "arm": plans[0]["arm"],
        "sigma": plans[0]["dp_sigma"],
        "lr": tp.LR,
        "batch": tp.BATCH_SIZE,
        "seed": plans[0]["seed"],
        "steps": [run["steps"] for run in runs],
        "scoring_instrument": "teach_persona.score_arm (D-19: no attack draws, no canary scoring)",
    }
    # Fixed ROLE keys: the first run is the STEP_BUDGET run, the second the e3_max_steps run.
    return {
        "configuration": configuration,
        "t_step_budget": runs[0],
        "t_max_steps": runs[1],
        "reused": {"e3": False},
    }


def _e3_stages(stages):
    """The two runs as measured; two training runs of the same per-step unit (H1)."""
    out = {key: value for key, value in stages.items() if key != "configuration"}
    _prove(set(out) == {"t_step_budget", "t_max_steps"}, f"E3 holds {sorted(out)}")
    _prove("score_seconds" not in out["t_max_steps"], "the e3_max_steps run is training only")
    return out, len(out)


STAGES["e3"] = stage_e3
RECORD_BUILDERS["e3"] = _e3_stages


# =================================================================================================
# E2 (D-08): the published Phase 19 M2 retrain, twice, plus one K = 48 A2 pass on it
# =================================================================================================


def train_e2_rep(arm, facts, second_person, replay_ratio):
    """One M2 training repetition under a probe36 arm name: seconds only (D-08, T-36-19).

    The ONE new call site of the teaching driver in this module, registered in
    tests/test_phase23_resume.py. Its return value is never bound, so no loss or PPL reaches a
    record. The csv it writes under results/ moves under data/ before this returns (WR-01)."""
    import phase14_factset  # lazy: fact material
    import teach_persona as tp  # torch at import: lazy

    _prove(
        arm != "real" and arm.startswith(f"{PROBE_PREFIX}_"),
        f"arm {arm!r} is not a probe36 arm name: 'real' writes the shippable persona_adapter.pt "
        "and any other name could collide with a published adapter",
    )
    prove_isolated_label(arm)
    paths = tp.arm_outputs(arm, prefix=PROBE_PREFIX)
    for key in ("adapter", "checkpoint"):
        _prove(
            not paths[key].exists(),
            f"{_rel(paths[key])} exists: stale probe output from an interrupted run. Delete it in "
            "a reviewed step, then rerun",
        )
    csv_dst = _data_path(f"{PROBE_PREFIX}_e2") / arm / "run.csv"
    _prove(not csv_dst.exists(), f"{_rel(csv_dst)} exists: stale probe output")
    with loop_timer(tp) as loop, silenced():
        started = time.monotonic()
        tp.train_arm(
            arm,
            facts=facts,
            family_ids=phase14_factset.TAUGHT_FAMILY_IDS,
            second_person=second_person,
            replay_ratio=replay_ratio,
            prefix=PROBE_PREFIX,
        )
        outer = time.monotonic() - started
    _prove(loop["calls"] == 1, f"the training loop ran {loop['calls']} times, not once")
    csv_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(paths["csv"]), str(csv_dst))
    paths["csv"].parent.rmdir()  # WR-01: empty after the move; anything else left there refuses
    return {
        "outer_seconds": outer,
        "loop_seconds": loop["seconds"],
        "overhead_seconds": outer - loop["seconds"],
    }


def stage_e2(state):
    """D-08: two M2 training reps, then the published A2 pass on the first adapter; time only."""
    import phase14_factset  # lazy: fact material
    import phase14_recall  # torch at import: lazy
    import phase19_erasure  # same
    import teach_persona as tp  # same

    # The published recipe (phase19_run.retrain_train): the `real` arm minus the target fact.
    target = {f.slot: f for f in phase14_factset.LOCKED_FACTS}[phase19_erasure.TARGET_SLOT]
    facts, second_person, replay_ratio = phase19_erasure.retrain_arm_spec(target.id)
    real_facts, real_second_person, real_replay = tp.arm_spec("real")
    dropped = sorted({f.id for f in real_facts} - {f.id for f in facts})
    _prove(
        dropped == [target.id] and len(facts) == len(real_facts) - 1,
        f"the retrain spec dropped {dropped}, not exactly [{target.id!r}]: M2 must be the `real` "
        "arm minus one fact",
    )
    _prove(
        (second_person, replay_ratio) == (real_second_person, real_replay),
        "the retrain spec changed second_person / replay_ratio against the `real` arm",
    )
    questions, k = e1_shape()
    path = arm_record_path("e2", 1)
    _prove(
        not path.exists(),
        f"{_rel(path)} exists: stale probe output from an interrupted run. Delete it, then rerun",
    )
    device = phase25_run.device()
    before = _sha256(phase14_recall.ADAPTER_PATH)  # T-36-19: the shippable adapter is read-only
    reps = []
    for rep, arm in enumerate(E2_ARMS, start=1):
        state.update(stage=f"e2_train_rep{rep}", shape=None, draw_index=None)
        reps.append(train_e2_rep(arm, facts, second_person, replay_ratio))
    state.update(stage="e2_a2_pass", shape=None, draw_index=None)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with DrawTimer() as timer, silenced():
            started = time.monotonic()
            phase19_erasure.run_erasure_arm(
                "retrain",
                device,
                adapter_path=tp.arm_outputs(E2_ARMS[0], prefix=PROBE_PREFIX)["adapter"],
                record_path=path,
            )
            total = time.monotonic() - started
    finally:
        path.unlink(missing_ok=True)  # D-01 / D-18: the draws are discarded
    _prove(
        _sha256(phase14_recall.ADAPTER_PATH) == before,
        f"{phase14_recall.ADAPTER_PATH} changed during the E2 probe (T-36-19)",
    )
    draw_seconds = [float(row["seconds"]) for row in timer.rows]
    _prove(
        len(draw_seconds) == questions * k,
        f"the draw timer counted {len(draw_seconds)} draws, not {questions} x {k} (D-08)",
    )
    configuration = {
        "arm": "retrain (M2: the real arm minus the target fact)",
        "target_slot": phase19_erasure.TARGET_SLOT,
        "n_facts_real": len(real_facts),
        "n_facts_m2": len(facts),
        "steps": tp.MAX_STEPS,
        "seed": tp.SEED,
        "K": k,
        "questions": questions,
        "full_adapter_derivation": (
            "the full taught adapter trains MAX_STEPS steps like M2 (loop cost independent of the "
            "fact count); its non-loop overhead (bin build, export, PPL sweep) is priced as M2's "
            "overhead x n_facts_real / n_facts_m2"
        ),
    }
    return {
        "configuration": configuration,
        "train_reps": reps,
        # B3: "a2_pass", never "reading" (a READING_TOKENS token build_record refuses).
        "a2_pass": {
            "total_seconds": total,
            "fixed_seconds": total - math.fsum(draw_seconds),
            "draws": len(draw_seconds),
            "draws_per_question": k,
            "draw_seconds": draw_seconds,
            "draw_seconds_spread": _spread(draw_seconds),
        },
        "reused": {"e2": False},
    }


def _e2_stages(stages):
    """The two training reps and the A2 pass as measured; two reps (H1)."""
    out = {key: value for key, value in stages.items() if key != "configuration"}
    _prove(len(out["train_reps"]) == 2, f"E2 holds {len(out['train_reps'])} training reps, not 2")
    return out, len(out["train_reps"])


STAGES["e2"] = stage_e2
RECORD_BUILDERS["e2"] = _e2_stages


# =================================================================================================
# THE RECORD (D-01): pure, then gated
# =================================================================================================


def build_record(front, run, *, beside=None):
    """The probe record from one run sidecar. Pure; refuses a reading key (D-01)."""
    _prove(run["front"] == front, f"the sidecar is front {run['front']!r}, not {front!r}")
    _prove(front in RECORD_BUILDERS, f"front {front!r} has no record builder")
    stages, repetitions = RECORD_BUILDERS[front](run["stages"])
    record = {
        "front": front,
        "probe_key": run["run_id"],
        "gates_nothing": True,
        "sweep_point": False,
        "sweep_point_false_reason": SWEEP_POINT_FALSE_REASON,
        "no_result_note": NO_RESULT_NOTE,
        "configuration": run["stages"]["configuration"],
        "stages": stages,
        "repetitions": int(repetitions),
        "reused": run["reused"],
    }
    if beside is not None:
        record.update(beside)
    return prove_no_reading(record)


def phase31_beside():
    """COST-01: the Phase 31 probe recorded BESIDE the E1 record — never an input to any price."""
    blob = _committed_json(PHASE31_POINT_RECORD)
    return {
        BESIDE_KEY: {
            "path": PHASE31_POINT_RECORD,
            "sha256": _sha256(_GIT_ROOT / PHASE31_POINT_RECORD),
            BESIDE_STAGES_KEY: {stage: v["seconds"] for stage, v in blob["stages"].items()},
            "total_seconds": blob["total_seconds"],
        }
    }


def _emit_target(out_path):
    """Write-once: overwrite refusal FIRST, dirty-tree refusal SECOND. Returns the absolute path."""
    out_path = pathlib.Path(out_path)
    if not out_path.is_absolute():
        out_path = _GIT_ROOT / out_path
    _prove(
        not out_path.exists(),
        f"{out_path} exists — REFUSING to overwrite it. A probe record is write-once; corrections "
        "are dated continuations",
    )
    pathspec = ("scripts", "src", "results")
    if out_path.is_relative_to(_GIT_ROOT):
        pathspec += (f":(exclude){out_path.relative_to(_GIT_ROOT).as_posix()}",)
    refuse_if_dirty(
        who="phase36_probe",
        detail=(
            "the probe record publishes git_sha and hashes its pinned modules from the working "
            "tree; a record written from a dirty tree names a commit it cannot be regenerated from"
        ),
        pathspec=pathspec,
        cwd=_GIT_ROOT,
    )
    return out_path


def _write_record(out_path, record, run):
    """WR-02, the reuse refusal, the provenance block, the gate, then the atomic write."""
    sessions = sessions_sidecar(run["front"])
    _prove(sessions.exists(), f"{_rel(sessions)} is missing: WR-02 cannot name the run sessions")
    shas = [s["git_sha"] for s in json.loads(sessions.read_text(encoding="utf-8"))]
    prove_pinned_unchanged([*shas, run["run_git_sha"]])
    _prove(
        not any(run["reused"].values()),
        f"reused stages {run['reused']}: a front is never priced from a reused stage (Pitfall 5)",
    )
    record["provenance"] = {
        "run": {
            "git_sha": run["run_git_sha"],
            "device": run["device"],
            "torch_version": run["torch_version"],
            "started_utc": run["started_utc"],
            "finished_utc": run["finished_utc"],
        },
        "module_sha256": {rel: _sha256(_GIT_ROOT / rel) for rel in PINNED_MODULES},
        "git_sha": INSTRUMENT_GIT_SHA,
        "head_at_write": git_sha(),
        "written_utc": _now(),
    }
    prove_no_reading(record)
    phase25_run.atomic_write_json(out_path, record)
    print(f"[phase36_probe] wrote {out_path}", flush=True)
    return record


def emit(front, out_path=None):
    """The one record writer: a front's sidecar -> a write-once record (default its listed path)."""
    target = _emit_target(phase36_prereg.probe_record(front) if out_path is None else out_path)
    sidecar = run_sidecar(front)
    _prove(sidecar.exists(), f"{_rel(sidecar)} is missing: run the {front} probe first")
    run = json.loads(sidecar.read_text(encoding="utf-8"))
    beside = {"e1": phase31_beside, "e6": e6_a2_context_beside}.get(front, lambda: None)()
    return _write_record(target, build_record(front, run, beside=beside), run)


# =================================================================================================
# D-16: ONE PATH PER COMMIT, RESUMABLE (scripts/phase32_points.py:408-467)
# =================================================================================================


def commit_path(relative, message):
    """Stage and commit EXACTLY ``relative`` (a listed probe record or the ledger) on main."""
    _prove(
        relative in phase36_prereg.PROBE_RECORDS + (phase36_ledger.LEDGER_PATH,),
        f"{relative!r} is not a listed probe record or the ledger: D-16 bounds the automatic "
        "commits to those paths",
    )
    _prove(
        (_GIT_ROOT / relative).exists(), f"{relative} does not exist, so there is nothing to commit"
    )
    branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=_GIT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    _prove(branch == "main", f"the repository is on branch {branch!r}, not main (D-16)")
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", relative],
        cwd=_GIT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    _prove(
        status, f"{relative} is already committed and unchanged, so this commit would be a NO-OP"
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


def _path_state(relative):
    """ "committed", "modified", "untracked" or "absent" — emit_all's one git/disk reader."""
    tracked = subprocess.run(
        ["git", "ls-files", "--", relative],
        cwd=_GIT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if tracked:
        status = subprocess.run(
            ["git", "status", "--porcelain", "--", relative],
            cwd=_GIT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        return "modified" if status else "committed"
    return "untracked" if (_GIT_ROOT / relative).exists() else "absent"


def emit_all():
    """Reconcile, commit the ledger FIRST (W9), then each record in RUN_ORDER; resumable (W4)."""
    phase36_ledger.reconcile()
    ledger = phase36_ledger.LEDGER_PATH
    state = _path_state(ledger)
    _prove(state != "absent", f"{ledger} is absent: no probe ran, so there is nothing to emit")
    if state != "committed":
        commit_path(ledger, "data(36): v6.0 MPS ledger after the probe run")
    for front in RUN_ORDER:
        record = phase36_prereg.probe_record(front)
        state = _path_state(record)
        if state == "committed":
            continue
        _prove(
            state != "modified",
            f"{record} is committed and changed on disk: a probe record is write-once",
        )
        if state == "absent":
            emit(front)
        commit_path(record, f"data(36): probe record {front} (D-16 automatic, listed in 36-07)")


# =================================================================================================
# THE CLI
# =================================================================================================


def front_outputs(front):
    """The paths a FINISHED ``front`` leaves on disk, by name (W3: a relaunch keeps them)."""
    import teach_persona as tp  # torch at import: lazy

    _prove(front in RUN_ORDER, f"front {front!r} is not a probe front")
    owned = set((_ROOT / "data").glob(f"{PROBE_PREFIX}_{front}_*"))
    if front == "e2":
        owned.add(_data_path(f"{PROBE_PREFIX}_e2"))
        for arm in E2_ARMS:
            owned.update(tp.arm_outputs(arm, prefix=PROBE_PREFIX).values())
    elif front == "e3":
        for steps in e3_steps():
            plan = e3_plan(steps)
            owned.add(phase25_points.training_sidecar(plan["point_key"]))
            owned.update(tp.arm_outputs(plan["arm"], prefix=plan["prefix"]).values())
    return owned


def preflight():
    """Everything the M3 run needs, checked before the LaunchAgent loads; writes nothing."""
    import phase14_recall  # torch at import: lazy
    import phase19_erasure  # same
    import teach_persona as tp  # same

    device = str(phase25_run.device())
    _prove(
        device == "mps",
        f"the device resolves to {device!r}, not 'mps': the probes price the M3 run (COST-01). "
        "Run preflight on the M3, outside any CPU-forcing environment",
    )
    refuse_if_dirty(
        who="phase36_probe",
        detail=(
            "a probe record names the commit it ran from; a run from a dirty tree times code that "
            "commit does not contain. Commit every change before loading the LaunchAgent"
        ),
        pathspec=("scripts", "src", "results"),
        cwd=_GIT_ROOT,
    )
    phase25_run.disk_precheck()
    opened = phase36_ledger.open_runs(phase36_ledger.read_ledger())
    _prove(
        not opened,
        f"the ledger holds open run(s) {sorted(opened)}: a crashed attempt is closed by "
        "`python scripts/phase36_ledger.py reconcile` (its lost line, W3) before a relaunch",
    )
    allowed = {sessions_sidecar(front) for front in RUN_ORDER}
    for front in RUN_ORDER:
        if run_sidecar(front).exists():  # run_front skips a finished front: keep its outputs
            allowed |= front_outputs(front)
    found = {path for pattern in STRAY_GLOBS for path in _ROOT.glob(pattern)}
    strays = sorted(found - allowed) + sorted(_ROOT.glob(RESULTS_STRAY_GLOB))
    _prove(
        not strays,
        f"stale probe output {[_rel(p) for p in strays]}: an unfinished front left them, and a "
        "stage would refuse, reuse or resume them. Delete them in a reviewed step, then rerun",
    )
    inputs = (
        phase14_recall.ADAPTER_PATH,
        phase14_recall.CONVBASE_SLIM,
        phase19_erasure.RETENTION_BIN,
        phase19_erasure.PHASE18_CORPUS_PATH,
        phase19_erasure.PHASE18_ARM_RECORD_PATH,
        tp.CONVBASE_BEST,
        tp.FACTSET_REPORT,
        tp.DIALOG_TRAIN_BIN,
        tp.DIALOG_TRAIN_MASK,
        tp.DIALOG_VAL_BIN,
        tp.DIALOG_VAL_MASK,
        *(_GIT_ROOT / rel for rel in (CURVE_RECORD, ERASED_RECORD, PHASE31_POINT_RECORD)),
    )
    missing = [str(path) for path in inputs if not pathlib.Path(path).exists()]
    _prove(not missing, f"required input(s) missing: {missing}. A front would die hours in")
    prove_published_adapter()
    unregistered = sorted(set(RUN_ORDER) ^ set(STAGES))
    _prove(not unregistered, f"fronts {unregistered} differ between RUN_ORDER and STAGES")
    phase36_prereg.prove_p22(phase36_prereg.ENTRIES["e3_max_steps"]["value"])
    print(f"[phase36_probe] PREFLIGHT OK {git_sha()} fronts={','.join(RUN_ORDER)}", flush=True)


def build_parser():
    parser = argparse.ArgumentParser(description="Phase 36 MPS cost probes (COST-01).")
    sub = parser.add_subparsers(dest="mode", required=True)
    run = sub.add_parser("run", help="run every front in RUN_ORDER (resumable per front)")
    run.add_argument("--heartbeat", default=str(phase36_ledger.HEARTBEAT_PATH))
    run.add_argument("--ledger", default=None)
    run.add_argument("--front", nargs="+", choices=RUN_ORDER, default=list(RUN_ORDER))
    emit_parser = sub.add_parser("emit", help="write one write-once probe record")
    emit_parser.add_argument("front", choices=phase36_prereg.PROBE_FRONTS)
    sub.add_parser("emit-all", help="commit the ledger, then every record (resumable)")
    sub.add_parser("preflight", help="check the stages before a launch; writes nothing")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.mode == "emit":
        emit(args.front)
        return 0
    if args.mode == "emit-all":
        emit_all()
        return 0
    if args.mode == "preflight":
        preflight()
        return 0
    import phase25_venue  # torch-free; the banner lets the launch identity be read off the log

    print(phase25_venue.launch_banner(), flush=True)
    run_all(
        heartbeat_path=pathlib.Path(args.heartbeat),
        ledger_path=None if args.ledger is None else pathlib.Path(args.ledger),
        fronts=tuple(args.front),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
