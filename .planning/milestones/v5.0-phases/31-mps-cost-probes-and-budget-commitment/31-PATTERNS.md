# Phase 31: MPS Cost Probes and Budget Commitment - Pattern Map

**Mapped:** 2026-09-26
**Files analyzed:** 5 new files (0 modified; every reused module is frozen or pinned and must NOT be edited)
**Analogs found:** 5 / 5

All paths, line numbers, constants and function names below were resolved live at HEAD `ebf1da7`
(read or executed in the `.venv` 3.11 interpreter). Nothing is retyped from RESEARCH.md without a
re-check.

## File Classification

| New File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `scripts/phase31_probe.py` | driver (run + emit) | batch (long unattended run -> gitignored sidecars) + file-I/O (write-once emit) | `scripts/phase26_canary.py` (run/emit split, heartbeat, sidecar reuse) + `scripts/phase30_calibration.py` (emit/provenance) | exact (composite) |
| `scripts/phase31_budget.py` | emitter (torch-free) | transform (committed records -> one write-once record) | `scripts/phase30_calibration.py` | role-match |
| `artifacts/com.personacore.phase31.probe.plist` | config (LaunchAgent) | batch | `artifacts/com.personacore.phase26.canary.plist` | exact |
| `tests/test_phase31_probe.py` | test | unit + CPU integration + plist | `tests/test_phase30_calibration.py`, `tests/test_phase30_seam.py:210-250`, `tests/test_phase26_canary.py:173-175, 522-541`, `tests/test_phase27_relearn.py:614` | exact |
| `tests/test_phase31_budget.py` | test | unit + ancestry | `tests/test_phase30_calibration.py:300-337` + `tests/test_phase29_prereg.py:70-106` | exact |

Files that must NOT be touched (tripwires): `scripts/teach_persona.py`, `scripts/phase30_points.py`
(`tests/test_phase30_calibration.py:349-358` `_SUPERSEDED_PINS`), `scripts/phase27_relearn.py`
(`results/phase27_admission.json` PINNED_MODULES, `tests/test_phase27_relearn.py:1190`),
`scripts/phase25_points.py`, `scripts/phase25_run.py`, `scripts/phase29_prereg.py`,
`src/personacore/training/loop.py`.

---

## Pattern Assignments

### `scripts/phase31_probe.py` (driver, batch + write-once emit)

**Analogs:** `scripts/phase30_calibration.py` (module skeleton, `_prove`, provenance, emit) and
`scripts/phase26_canary.py` (argparse run/emit split, heartbeat, sidecar reuse-or-refuse).

**Module header / import pattern** (`scripts/phase30_calibration.py:27-62`) — copy verbatim shape;
torch-touching modules (`teach_persona`, `phase14_factset`, `phase18_extraction`) are imported LAZILY
inside functions:
```python
import datetime
import hashlib
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import phase25_run  # noqa: E402  (scripts/ is not a package)
import phase29_prereg  # noqa: E402  (same)
import phase30_points  # noqa: E402  (same)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

INSTRUMENT_GIT_SHA = git_sha()

RECORD = _ROOT / phase30_points.CALIBRATION_PATH   # -> resolve phase31 paths the same way:
# next(p for p in phase29_prereg.V5_RESULT_PATHS if p == ...) / startswith("results/phase31_probe_point")
PINNED_MODULES = tuple(
    pathlib.Path(path).resolve().relative_to(_ROOT).as_posix()
    for path in (__file__, phase30_points.__file__, _SCRIPTS + "/teach_persona.py", ...)
)
```
Resolve the record paths from `phase29_prereg.V5_RESULT_PATHS` (`scripts/phase29_prereg.py:148-158`:
`"results/phase31_probe_point.json"`, `"results/phase31_probe_relearn.json"`) the way
`phase30_points.CALIBRATION_PATH` does at `scripts/phase30_points.py:54-56`:
```python
CALIBRATION_PATH = next(
    p for p in phase29_prereg.V5_RESULT_PATHS if p.startswith("results/phase30_")
)
```

**`_prove` / helpers** (`scripts/phase30_calibration.py:65-77`):
```python
def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase30_calibration] {message}")

def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def _rel(path):
    path = pathlib.Path(path)
    return path.relative_to(_ROOT).as_posix() if path.is_relative_to(_ROOT) else str(path)
```

**Plan acquisition + re-key (D-01, D-02)** — source `scripts/phase30_points.py:284-293` (`next_action`)
and `:138-169` (`point_plan`, the dict keys `train_stage`/`measure_stage` consume):
```python
# next_action(control) runs require_calibrated_recipe against the TRACKED calibration, then:
    if key == ckey:
        require_calibrated_recipe(leg, recipe, tracked)
        return {"action": "train", "plan": point_plan(key)}
```
Plan keys (`phase30_points.py:151-169`): `point_key, arm, axis, axis_value, is_dp, is_control,
n_facts, seed, prefix, dp_sigma, dp_clip_norm, adversarial_ratio, pinned_mechanism, point_epsilon,
accounting, control_key`. Real prefix for the n64 control is `"phase32_" + "ratio0p000000"` (line 145),
so the probe replaces exactly `point_key` and `prefix`:
`plan = dict(action["plan"], point_key=PROBE_KEY, prefix=PROBE_PREFIX)`.
`tracked` = `git ls-files results` output (list of rel paths), as `_tracked_json` (`:184-197`) expects.
Guard: prefix must not start with `phase25_points.CALIBRATION_PREFIX_LITERAL` (`"phase25_calibration"`,
`scripts/phase25_points.py:72`) — same check as `phase30_points.py:146-149`; PROBE_KEY not in
`phase29_prereg.POINT_KEYS()`; prefix must not start with `phase3` (RESEARCH Pattern 1).

**Where the re-keyed plan's key/prefix land** (isolation proof inputs) — `scripts/phase25_points.py:266-275`:
```python
def training_sidecar(point_key):
    return _ROOT / "data" / f"phase25_{point_key}_training.json"
def measure_sidecar(point_key):
    return _ROOT / "data" / f"phase25_{point_key}_measure.json"
def run_log_dir(point_key):
    return _ROOT / "data" / "phase25_runs" / point_key
```
and `tp.arm_outputs(arm, prefix=prefix)` at `phase25_points.py:362`; draw cache
`phase25_run.draws_path(point_key)` (`scripts/phase25_run.py:180`).

**D-02 hazard (what the guard must prove)** — `scripts/phase25_points.py:365-374`: an existing
training sidecar + matching adapter is silently REUSED:
```python
    if sidecar.exists():
        blob = json.loads(sidecar.read_text(encoding="utf-8"))
        _prove(paths["adapter"].exists() and _sha256(paths["adapter"]) == blob["adapter_sha256"], ...)
        print(f"[phase25_points] {key}: REUSING trained adapter from {_rel(sidecar)}", flush=True)
        return blob
```
Also the resume branch `:383-391` (checkpoint exists -> resumes, timing only covers remaining steps):
the probe must refuse `checkpoints/{PROBE_PREFIX}_advr_n64_latest.pt` without a completed sidecar.

**Stage timings already produced by frozen code (Pattern 3):**
- train: `training["seconds"]` (`phase25_points.py:415, 432, 514`) + `resumed_from_step` (`:515`)
- measure (condition (c) + GATE-05): `measured["measure_seconds"]` (`:557-567, 618`)
- recall (only when `plan["is_control"]`): `measured["scoring_seconds"]` (`:569-573, 619`) — probe
  plan IS a control, so recall is scored
- draws: `blob["shapes"][family]["timing"]["minutes"]` (`scripts/phase25_run.py:571-582`)
- score: outer `time.monotonic()` bracket around `phase25_run.score_point(blob, values)` (`:586-630`)

**D-11 on_draw wrap** — copy `tests/test_phase30_seam.py:210-245` (monkeypatch -> try/finally rebind
of `tp.train` in production):
```python
def _per_step_replay(events):
    steps = []
    for is_replay, n_windows in events:
        if not is_replay:
            steps.append(0)
        else:
            assert steps, "a replay draw before any teaching draw"   # -> _prove in the driver
            steps[-1] += n_windows
    return steps

    def _on_draw(bin_path, ix):
        replay = pathlib.Path(bin_path) == pathlib.Path(tp.DIALOG_TRAIN_BIN)
        events.append((replay, len(ix)))

    monkeypatch.setattr(tp, "train", lambda **kw: real_train(**kw, on_draw=_on_draw))
    ...
    assert [w for replay, w in events if not replay] == [tp.BATCH_SIZE] * tp.MAX_STEPS
    assert _per_step_replay(events) == [budget] * tp.MAX_STEPS
```
The idiom for temporarily swapping a `tp` global inside production code is `train_stage` itself,
`phase25_points.py:399-431`:
```python
    real_dp, real_cfg = tp.DPSGD, tp.TrainConfig
    ...
    tp.DPSGD, tp.TrainConfig = dp_factory, cfg_factory
    started = time.time()
    try:
        trained = tp.train_arm(...)
    finally:
        tp.DPSGD, tp.TrainConfig = real_dp, real_cfg
```
CENSUS WARNING: never write the literal `train_arm(` (with parenthesis) in the new files, including
docstrings/comments (`tests/test_phase23_resume.py::test_resume_from_none_is_inert` greps prose).

**Measure/draw/score calls** — `measure_stage(plan, training)` (`phase25_points.py:536`),
`phase25_run.draw_point_shapes(point_key, *, adapter, adapter_sha256, corpus, corpus_sha256, k, state, dry_run=False)`
(`phase25_run.py:458-468`), corpus/values from `phase25_points.attack_corpus()` (`:637`) and
`phase25_points.scoring_values()` (`:655`). How `score_rung` wires the same calls
(`scripts/phase27_relearn.py:718-730`):
```python
    scored = tp.score_arm(point_label, facts, adapter_path, device)
    tok = from_json(tp.TOKENIZER_PATH)
    corpus = x18.build_corpus(tok)
    blob, _digests = phase25_run.draw_point_shapes(
        point_label, adapter=adapter_path, adapter_sha256=_sha256(adapter_path),
        corpus=corpus, corpus_sha256=x18.corpus_sha256(corpus), k=k, state={},
    )
    per_question, _per_fact, _scored = phase25_run.score_point(blob, values)
```
Do NOT call `phase25_run.run_point` (`:633`, refuses `advr_*`); do NOT reference
`phase25_points.point_plan/prefix_for/n_facts_for/exact_axis_value/control_key_for/control_reading/record_kwargs/_adversarial_extras`
(WR-05 AST guard, below).

**Relearning probe (D-04..D-06)** — signatures at `scripts/phase27_relearn.py:526-528` and `:692`:
```python
def train_relearn_arm(*, arm, leg, seed, cfg, start_adapter, expected_sha256, out_dir, device, point_key=None):
def score_rung(*, point_label, adapter_path, k, out_dir, device, facts, values):
```
Mirror `run_curve`'s loop minus `_require_admitted` (`phase27_relearn.py:879-913`):
```python
    device = phase25_run.device()
    cfg = shared_train_config()
    values = phase25_points.scoring_values()
        trained = train_relearn_arm(
            arm="mitigated", leg=leg, seed=cfg.seed, cfg=cfg,
            start_adapter=_ROOT / entry["adapter_path"], expected_sha256=entry["adapter_sha256"],
            out_dir=out_dir, device=device, point_key=key,
        )
        for rung in trained["rungs"]:
            reading = score_rung(
                point_label=f"phase27_{leg}_{key}_rung{rung['steps']:04d}_k{phase27_prereg.CURVE_K}",
                adapter_path=_ROOT / rung["adapter_path"], k=phase27_prereg.CURVE_K,
                out_dir=out_dir, device=device, facts=fs.LOCKED_FACTS, values=values,
            )
```
For the probe: `start_adapter=_ROOT / training["adapter"]`, `expected_sha256=training["adapter_sha256"]`
(train sidecar fields, `phase25_points.py:502-503`), `point_key=RELEARN_LABEL`, label must end in
`_k{CURVE_K}` (`score_rung` refuses otherwise, `:713-717`). Use a probe-prefixed label, not `phase27_...`.
Pitfall 2: `train_relearn_arm` leaves its CSV under `results/` (`:582-584`, csv from
`tp.build_arm_bins(..., prefix=phase27_prereg.ATTACKER_PREFIX)` `:562-569`). Move it with the
`train_stage` idiom (`phase25_points.py:487-494`):
```python
    log_dir = run_log_dir(key)
    log_dir.mkdir(parents=True, exist_ok=True)
    csv_dst = log_dir / "run.csv"
    shutil.move(str(paths["csv"]), str(csv_dst))
    try:
        paths["csv"].parent.rmdir()
    except OSError:
        pass
```
Stream dir: `phase27_relearn.STREAM_DIR = _ROOT / "data"` (`:57`).

**Heartbeat pattern** (`scripts/phase26_canary.py:356-379, 408`):
```python
    heartbeat_path = phase25_run.HEARTBEAT_PATH if heartbeat_path is None else heartbeat_path
    state = {"point": point_key, "stage": "score", "shape": None, "draw_index": None}
    phase25_run.beat(heartbeat_path, **state)
    stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
    try:
        device = phase25_run.device()
        ...
    finally:
        stop.set()
        thread.join()
    ...
    phase25_run.beat(heartbeat_path, point=point_key, stage="done", shape=None, draw_index=None)
```
`stage` values must be from `phase25_run.STAGES = ("start","train","measure","draw","score","record","commit","done")`
(`scripts/phase25_run.py:295`); `state` is mutated in place so the beat reports the live stage.

**Sidecar reuse-or-refuse** (`scripts/phase26_canary.py:339-348`) — for the probe's own stage sidecars:
```python
    sidecar = sidecar_path(point_key)
    if sidecar.exists():
        blob = json.loads(sidecar.read_text(encoding="utf-8"))
        _prove(blob["adapter_sha256"] == record["adapter_sha256"], f"... REFUSED, not reused")
        return "reused", blob
```

**CLI run/emit split** (`scripts/phase26_canary.py:793-824`):
```python
def build_parser():
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("--heartbeat", default=str(phase25_run.HEARTBEAT_PATH))
    parser.add_argument("--emit", action="store_true", help="assemble results/phase26_canary.json")
    ...
def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.emit:
        emit(overwrite=args.force)
        return 0
    heartbeat = pathlib.Path(args.heartbeat)
    ...
if __name__ == "__main__":
    raise SystemExit(main())
```
Phase 31 has no `--force` (write-once, D-14 no retry): keep the `phase30_calibration.emit` refusal instead.

**Write-once emit with dirty-first refusal + provenance** (`scripts/phase30_calibration.py:237-270`):
```python
def emit(out_path=RECORD):
    out_path = pathlib.Path(out_path)
    _prove(not out_path.exists(), f"{_rel(out_path)} exists — REFUSING to overwrite it. ...")
    pathspec = ("scripts", "src", "results")
    if out_path.is_relative_to(_ROOT):
        pathspec += (f":(exclude){_rel(out_path)}",)
    refuse_if_dirty(who="phase30_calibration", detail="...", pathspec=pathspec, cwd=_ROOT)
    blob = build_record()
    blob["provenance"] = {
        "module_sha256": {rel: _sha256(_ROOT / rel) for rel in PINNED_MODULES},
        "git_sha": INSTRUMENT_GIT_SHA,
        "head_at_write": git_sha(),
        "written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    phase25_run.atomic_write_json(out_path, blob)
    return blob
```
`sweep_point` field names from `results/phase23_cost.json`: `"sweep_point": false`,
`"sweep_point_false_reason": "<text>"`. `gates_nothing: True` idiom: `phase30_calibration.py:221-222`.
Phase 25 twin to publish beside the probe: `results/phase25_point_adv_n64_ratio0p000000.json`
(`training.seconds` = 80.30, `measure_seconds` = 87.77, `shape_timing` = {A1-aggressive 19.62,
A1-mild 15.31, A2 12.20, A3 17.06} min) and `results/phase25_recall.json::points.adv_n64_ratio0p000000.scoring_seconds`.

---

### `scripts/phase31_budget.py` (torch-free emitter, transform)

**Analog:** `scripts/phase30_calibration.py` (same skeleton, `_prove`, `emit`, provenance as above).
Committed-blob reads via `phase30_points._tracked_json(rel, tracked, what)` (`scripts/phase30_points.py:184-197`):
```python
def _tracked_json(rel, tracked, what):
    _prove(rel in set(tracked), f"{what} {rel} is not TRACKED (git ls-files). ...")
    shown = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=_ROOT, capture_output=True)
    _prove(shown.returncode == 0, f"{what} {rel} has no committed blob at HEAD")
    _prove(shown.stdout == (_ROOT / rel).read_bytes(), f"{what} {rel} differs from its committed blob: ...")
    return json.loads(shown.stdout.decode("utf-8"))
```

**TORCH-FREE TRAP (verified live, not in RESEARCH):** `phase29_prereg.replay_windows(n)` imports
`teach_persona` (torch) at call time (`scripts/phase29_prereg.py:171-175`), and `tp.MAX_STEPS` needs
`teach_persona`. The budget must NOT call either. Torch-free sources, verified with
`'torch' in sys.modules == False` after import:
- replay windows: the tracked calibration's `recipe[leg]["replay_windows"]` (n8 = 32, n64 = 256) via
  `phase30_points.calibration_record(tracked)` (`:200-201`), or the committed probe record.
- max steps: `mitigation_budget.STEP_BUDGET` (= 200; `phase30_points.py:84-86` proves it equals
  `tp.MAX_STEPS`) or `recipe[leg]["max_steps"]`.
- counts: `phase29_prereg.LEGS` (`:102`), `leg_keys(leg)` (`:126`), `POINT_KEYS()` (`:112`),
  `RATIO_GRID` (`:90`), `RUNGS`, `RELEARN_CAP`, `CURVE_K`, `FRESH_SEEDS`, `DESIGNATED_SEED` (`:316-323`),
  `control_key(leg)` (`:120`) — all torch-free.
- Phase 25 inputs: 12 `results/phase25_point_adv_*.json` (`training.seconds`, `measure_seconds`,
  `shape_timing[*].minutes`) and `results/phase25_recall.json::points[key].scoring_seconds`.
- Do NOT cite any DP record key string (`dp_n...`): WR-05 AST guard.

**Torch-free proof pattern** (`tests/test_phase30_points.py:133-147`) — see test file below.

---

### `artifacts/com.personacore.phase31.probe.plist` (config, LaunchAgent)

**Analog:** `artifacts/com.personacore.phase26.canary.plist` (58 lines) — copy whole, change only
the comment, `Label`, script path, log pair:
```xml
  <key>Label</key>
  <string>com.personacore.phase26.canary</string>
  <key>KeepAlive</key>
  <false/>
  <key>RunAtLoad</key>
  <false/>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/caffeinate</string>
    <string>-dims</string>
    <string>/Users/juliorcoelho/PersonaCore/.venv/bin/python</string>
    <string>/Users/juliorcoelho/PersonaCore/scripts/phase26_canary.py</string>
    <string>--heartbeat</string>
    <string>/Users/juliorcoelho/PersonaCore/data/phase25_heartbeat.jsonl</string>
  </array>
  <key>WorkingDirectory</key>
  <string>/Users/juliorcoelho/PersonaCore</string>
  <key>StandardOutPath</key>
  <string>/Users/juliorcoelho/PersonaCore/logs/phase26_canary.out</string>
  <key>StandardErrorPath</key>
  <string>/Users/juliorcoelho/PersonaCore/logs/phase26_canary.err</string>
  <key>ProcessType</key>
  <string>Interactive</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PERSONACORE_SWEEP_ACTIVE</key><string>1</string>
    <key>PATH</key><string>/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>PYTHONUNBUFFERED</key><string>1</string>
  </dict>
```
If the driver uses a `run` subcommand (RESEARCH diagram), insert it after the script path; the
`ProgramArguments[3]` suffix assertion in the test must match.

---

### `tests/test_phase31_probe.py` (test)

**Header / sys.path / helper imports** (`tests/test_phase30_calibration.py:8-35`):
```python
import json, pathlib, subprocess, sys
import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_TESTS = str(_ROOT / "tests")
if _TESTS not in sys.path:
    sys.path.insert(0, _TESTS)

import phase29_prereg  # noqa: E402
import phase30_points as pts  # noqa: E402
from test_phase29_prereg import _assert_frozen_before, _git  # noqa: E402
from test_phase30_points import _commit  # noqa: E402
```

**Recorded dirty-guard fixture** (`tests/test_phase30_calibration.py:55-61`):
```python
@pytest.fixture(autouse=True)
def clean_tree(monkeypatch):
    calls = []
    monkeypatch.setattr(cal, "refuse_if_dirty", lambda **kw: calls.append(kw) or "")
    return calls
```

**Emit write-once + dirty-before-measure** (`tests/test_phase30_calibration.py:257-292`): copy
`test_emit_is_write_once` (tracked-vs-absent honest branch; emit to `tmp_path`) and
`test_emit_refuses_a_dirty_tree_before_measuring` (asserts `call["pathspec"] == ("scripts","src","results", f":(exclude){rel}")`).

**Replay-count bucketing + lopsided non-vacuity** (`tests/test_phase30_seam.py:246-250`):
```python
    lopsided = [(False, tp.BATCH_SIZE), (True, 2 * budget), (False, tp.BATCH_SIZE)]
    assert sum(w for replay, w in lopsided if replay) == budget * tp.MAX_STEPS
    assert _per_step_replay(lopsided) != [budget] * tp.MAX_STEPS
```

**CPU live-path harnesses:** training — `tests/test_phase22_wiring.py:715 _e2e_env(root, monkeypatch)`
(imported by `tests/test_phase30_seam.py:34` as `from test_phase22_wiring import _FIXTURE_CLIP, _FIXTURE_SIGMA, _e2e_env`);
relearn/scoring — `tests/test_phase27_relearn.py:614 _e2e_env(root, monkeypatch)`, whose first act is
`monkeypatch.setattr(phase25_run, "_DEVICE", "cpu")` and which redirects `relearn.BASE_SLIM`,
`pr.CONVBASE_SLIM`, `pr.RECALL_MAX_NEW_TOKENS`. K for fixtures: only 8/16 accepted by `mitigation_gate.ratchet_k`.

**Plist mirror test** (`tests/test_phase26_canary.py:173-175, 522-535`):
```python
def _plist(path):
    with path.open("rb") as handle:
        return plistlib.load(handle)

def test_the_canary_agent_mirrors_the_recall_agent():
    ours, recall = _plist(_CANARY_PLIST), _plist(_RECALL_PLIST)
    assert ours["Label"] == "com.personacore.phase26.canary"
    assert ours["KeepAlive"] is False
    assert ours["RunAtLoad"] is False
    assert ours["ProgramArguments"][:3] == recall["ProgramArguments"][:3]
    assert ours["ProgramArguments"][3].endswith("scripts/phase26_canary.py")
    beat = ours["ProgramArguments"][ours["ProgramArguments"].index("--heartbeat") + 1]
    ...
    assert ours["StandardOutPath"] != recall["StandardOutPath"]
    assert ours["EnvironmentVariables"]["PERSONACORE_SWEEP_ACTIVE"] == "1"
```
Mirror the canary plist (`artifacts/com.personacore.phase26.canary.plist`) instead of the recall one.
Do NOT add a `@needs_plutil` lint test (`tests/test_phase26_canary.py:69`) unless the venue skip pin
in `tests/test_phase25_venue.py` is updated in the same plan.

---

### `tests/test_phase31_budget.py` (test, ancestry)

**Ancestry helper** (`tests/test_phase29_prereg.py:70-106`, import it, never copy): every commit touching
the artifact must be a strict ancestor of the earliest add of each tracked path; rejects same-commit
and shallow clones. Commit probe records and budget in SEPARATE commits.

**Guard shape to copy** (`tests/test_phase30_calibration.py:300-323`):
```python
def _v5_tracked():
    return sorted({path for spec in phase29_prereg.ARTIFACT_PATHSPECS
                   for path in _git("ls-files", spec).split()})

def test_ancestry_calibration_precedes_every_later_v5_result():
    cal_rel = pts.CALIBRATION_PATH
    tracked = _v5_tracked()
    later = [p for p in tracked if p != cal_rel]
    if cal_rel not in tracked:
        assert later == [], (...)
        return
    _assert_frozen_before(cal_rel, later)
    # NON-VACUITY (natural RED): a v4.0 result that predates the calibration must fire.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(cal_rel, ["results/phase25_frontier.json"])
```
Budget version: `later` = `git ls-files phase29_prereg.POINT_RECORD_PREFIX + "*.json"`
(`POINT_RECORD_PREFIX = "results/phase32_point_"`, `scripts/phase29_prereg.py:139`); natural RED =
`_assert_frozen_before(BUDGET, [pts.CALIBRATION_PATH])`. Note: `test_ancestry_calibration_precedes_every_later_v5_result`
and `test_phase29_prereg_is_frozen_before_every_v5_result` already cover the new `results/phase31_*` files
automatically via `ARTIFACT_PATHSPECS`.

**Torch-free import test** (`tests/test_phase30_points.py:133-147`):
```python
def test_driver_imports_without_torch():
    completed = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path[:0] = ['scripts', 'src']; import phase30_points as p; "
         "...; print('torch' in sys.modules)"],
        cwd=_ROOT, capture_output=True, text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "False", completed.stdout
```
For the budget, exercise `derive`/`build_record` in the subprocess, not only the import, so a lazy
`replay_windows` call is caught.

---

## Shared Patterns

### Invariant refusal
**Source:** `scripts/phase30_calibration.py:65-68`. **Apply to:** both new scripts. `SystemExit`
with a `[phase31_probe]` / `[phase31_budget]` prefix; never `assert` in scripts.

### Atomic writes
**Source:** `phase25_run.atomic_write_json(path, blob)` (`scripts/phase25_run.py:118`). **Apply to:**
every sidecar and record write. `os.replace` is only allowed in `phase25_run.py`/`phase25_record.py`
(`tests/test_phase25_driver.py:340` census).

### Provenance + dirty refusal
**Source:** `scripts/phase30_calibration.py:245-263`; `personacore.provenance.git_sha`, `refuse_if_dirty`
(`src/personacore/provenance.py`). **Apply to:** all three emits. Calibration descent = add commit of
`phase30_points.CALIBRATION_PATH` (`4339f2b2bc29ab0765a821b5d47b617cd6092f24`, also `_RECORD_COMMIT`
at `tests/test_phase30_calibration.py:349`) derived via `git log --diff-filter=A`, never typed.

### Device
**Source:** `phase25_run.device()` (`scripts/phase25_run.py:404-436`, caches `_DEVICE`). **Apply to:**
probe driver; tests pin `phase25_run._DEVICE = "cpu"` first.

### WR-05 AST guard (automatic coverage)
**Source:** `tests/test_phase30_points.py:636-644` globs `scripts/phase30_*.py`..`phase34_*.py`, so both
new scripts are scanned. Banned: `control_key_for`, `control_reading`, `record_kwargs`,
`control_readings`, `_adversarial_extras`, `phase25_points.point_plan/prefix_for/n_facts_for/exact_axis_value`,
aliases/`getattr` of those, and any non-docstring string constant starting `dp_n`.

### Censuses in new files
No literal `train_arm(`, no `== 10`/`!= 10` in tests, no direct `inject_lora`/`draw_all`/`build_recall_prompt`
calls, no new `skipif`/`pytest.skip` (venue skip pin).

## No Analog Found

None. The only genuinely new logic is the budget arithmetic (per-stage x counts, D-10 spread, stop
line = 1.5 x upper bound); use RESEARCH.md "Budget formula" (lines 340-364) for it, with inputs
sourced torch-free as listed above.

## Metadata

**Analog search scope:** `scripts/phase2[5-9]_*.py`, `scripts/phase30_*.py`, `artifacts/*.plist`,
`tests/test_phase2[2-9]_*.py`, `tests/test_phase30_*.py`, `results/phase2[35]_*.json`, `results/phase30_calibration.json`
**Files scanned:** 18
**Pattern extraction date:** 2026-09-26
