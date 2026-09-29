# Phase 32: Replay-Bearing Frontier Re-run and Verdict - Pattern Map

**Mapped:** 2026-09-27
**Files analyzed:** 9 new/modified
**Analogs found:** 9 / 9 (every file has an in-repo analog; the runbook's analog is prose)

Every path and symbol below was resolved from the code's own constants at HEAD `b44c2a3`. Line
numbers are from this session's reads. Four findings here are NOT in 32-RESEARCH.md; they are
marked **[NEW]**.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `scripts/phase32_points.py` (NEW) | driver + CLI | batch / file-I/O / git write | `scripts/phase31_probe.py` (`run_point_probe` :322-491, `_emit_target` :512, `_write_record` :537, CLI :915-942) + `scripts/phase25_run.py` (`commit_point_record` :756-838, `main` :882-909) | exact (probe) + exact (commit) |
| `scripts/phase32_frontier.py` (NEW) | assembler + write-once emitter | transform (committed records -> one record) | `scripts/phase25_promotion.py::curve_pass` :261-318 + `scripts/phase31_budget.py::emit` :372-409 | exact (verdict loop) + exact (write-once emit) |
| `artifacts/com.personacore.phase32.sweep.plist` (NEW) | config (LaunchAgent) | — | `artifacts/com.personacore.phase31.probe.plist` | exact |
| `tests/test_phase32_points.py` (NEW) | test (unit + AST + live fixture) | — | `tests/test_phase31_probe.py` (fixture :310-389, refusals :431-462, CLI :931-978, plist :981-1001) + `tests/test_phase25_driver.py` (`_git_argv_subcommands` :105, `_git_surface_failure` :131, `_scratch_repo` :142) | exact |
| `tests/test_phase32_frontier.py` (NEW) | test | — | `tests/test_phase31_budget.py` (write-once :305-376, recompute :378-403, ancestry :406-428) + `tests/test_phase29_prereg.py` (`_v5_frontier` :650, `_gate_retype_failures` :484) | exact |
| `tests/test_phase30_points.py` (MODIFY, D-17 guard continuation + `_good_control` replay block) | test (AST guard) | — | same file: `_wr05_failures` :567-633, `test_ast_guard_planted_red_per_class` :647-675, the "Review WR-06" in-place continuation comments | exact |
| `scripts/phase30_points.py` (MODIFY, D-19 WR-04 in `own_control`; IN-04 in `recipe_identity`) | driver library | request-response (read committed record) | same file: the existing WR-04 block `own_control` :247-258 | exact |
| `tests/test_phase30_calibration.py` (MODIFY, `_SUPERSEDED_PINS` continuation) | test (tripwire) | — | same file :339-380; `tests/test_phase27_relearn.py` :1188-1269 | exact |
| Runbook (NEW; location — see warning below) | docs | — | 31-04-PLAN.md launch brief (:53-116) + `results/phase25_operational_note.md` (v4.0 prose precedent) | role-match |

---

## Pattern Assignments

### `scripts/phase32_points.py` (driver, batch + git write)

**Analog:** `scripts/phase31_probe.py`. Copy the shape; import only its public helpers
(`per_step_replay` :156, `prove_replay_counts` :172, `calibration_descent` :499).

**Module header / imports / two roots** (probe :23-57):
```python
_ROOT = pathlib.Path(__file__).resolve().parent.parent
# The git root. Same value as _ROOT at import, but never patched: ...
_GIT_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_GIT_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
...
import mitigation_budget  # noqa: E402  (scripts/ is not a package)
import phase25_points  # noqa: E402  (same)
import phase25_run  # noqa: E402  (same)
import phase29_prereg  # noqa: E402  (same)
import phase30_points  # noqa: E402  (same)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

INSTRUMENT_GIT_SHA = git_sha()
```
Deviation (RESEARCH Pattern 1): for D-12 the git root MUST be patchable, because the fixture
commits into a scratch repo. `phase30_points._ROOT` must be patched to the same scratch root:
`_tracked_json` runs `git show` there (:191), and `write_refused_records` writes
`_ROOT / point_record_path(key)` (:321). The driver's record path, its git calls and
`phase30_points._ROOT` must all resolve to one root, or the REFUSED records land in a different
tree from the one committed.

**`_prove` / `_sha256` / `_rel` helpers** (probe :100-112): copy verbatim with a `[phase32_points]`
prefix. Never `assert` (`python -O`).

**PINNED_MODULES derived from `__file__`** (probe :73-84). Copy the idiom and extend the tuple per
RESEARCH Pitfall 4. For D-08 the per-session sha check runs over this tuple:
```python
PINNED_MODULES = tuple(
    pathlib.Path(path).resolve().relative_to(_GIT_ROOT).as_posix()
    for path in (
        __file__,
        phase25_points.__file__,
        phase25_run.__file__,
        phase30_points.__file__,
        _SCRIPTS + "/teach_persona.py",  # a path, not an import: teach_persona imports torch
        _SRC + "/personacore/training/loop.py",
    )
)
```

**Result paths — derive, never type** (probe :66-71; phase30_points :54-56):
```python
POINT_RECORD = next(
    p for p in phase29_prereg.V5_RESULT_PATHS if p.startswith("results/phase31_probe_point")
)
```
For Phase 32: per-point path = `phase29_prereg.point_record_path(key)` (:142). The budget path
is `phase31_budget.BUDGET_RECORD` (:44), but importing `phase31_budget` imports `phase31_probe`
(harmless, `git_sha()` at import). The stop line must be read via
`phase30_points._tracked_json(BUDGET_RECORD, tracked, ...)["stop_line"]["seconds"]`.

**Refusal of half-trained state** (probe :357-369). Copy verbatim, re-keyed to the phase32 sidecars
(`data/phase32_<key>_replay.json`, `data/phase32_<key>_sessions.json`; `data/` is gitignored):
```python
_prove(
    train_sidecar.exists() or not paths["checkpoint"].exists(),
    f"{_rel(paths['checkpoint'])} exists without {_rel(train_sidecar)}: a resume would time "
    "only the remaining steps and could not count the earlier steps' replay. Delete ...",
)
_prove(
    replay_sidecar.exists() or not train_sidecar.exists(),
    f"{_rel(train_sidecar)} exists without {_rel(replay_sidecar)}: the per-step replay counts ...",
)
```
Checkpoint path: `tp.arm_outputs(plan["arm"], prefix=plan["prefix"])["checkpoint"]`. The prefix
comes from `phase30_points.point_plan` (:145), for example `phase32_ratio0p000000`.

**Expected replay, cross-checked** (probe :370-375):
```python
expected = phase30_points.calibration_record(tracked)["recipe"][LEG]["replay_windows"]
n_facts = len(tp.arm_spec(plan["arm"])[0])
_prove(expected == phase29_prereg.replay_windows(n_facts), ...)
```

**Core stage sequence with replay counting** (probe :382-455). This is the pattern to copy:
```python
state = {"point": PROBE_KEY, "stage": "train", "shape": None, "draw_index": None}
stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
try:
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
    ...
    replay = {"per_step": prove_replay_counts(events, expected, batch_size=tp.BATCH_SIZE,
              steps=tp.MAX_STEPS), "expected_per_step": expected, "steps": tp.MAX_STEPS,
              "teaching_windows_per_step": tp.BATCH_SIZE, "adapter_sha256": training["adapter_sha256"]}
    phase25_run.atomic_write_json(replay_sidecar, replay)

    state["stage"] = "measure"
    measured = phase25_points.measure_stage(plan, training)      # Phase 32: dict(plan, is_control=True) (D-01)
    state["stage"] = "draw"
    corpus, corpus_sha256 = phase25_points.attack_corpus()
    blob, _digests = phase25_run.draw_point_shapes(key, adapter=_ROOT / training["adapter"],
        adapter_sha256=training["adapter_sha256"], corpus=corpus, corpus_sha256=corpus_sha256,
        k=mitigation_budget.CURVE_K, state=state)
    state["stage"] = "score"
    phase25_run.score_point(blob, phase25_points.scoring_values())  # returns (per_question, per_fact, scored)
    ...
    # "done" BEFORE the stop event: a periodic beat racing the stop can only write "done".
    state.update(stage="done", shape=None, draw_index=None)
finally:
    stop.set()
    thread.join()
```
D-01 override (RESEARCH Pattern 4). `plan["is_control"]` is read only at
`phase25_points.py:570`:
```python
def measure_stage(plan, training):
    return phase25_points.measure_stage(dict(plan, is_control=True), training)
```

**Stage-seconds schema for the D-03 clock** (probe `build_point_record` :242-265). Reuse the same
keys so the budget's unit is literally the one Phase 31 measured: `stages.{train,measure,recall,
draw,score}.seconds`, where draw = `60 * sum(blob["shapes"][f]["timing"]["minutes"])`.

**[NEW] The record's field contract.** Four consumers read it, and each field is listed with the
line that reads it:

| Field | Read by |
|---|---|
| `point_key`, `arm`, `axis == "ratio"`, `q is None`, `clip_norm is None`, `recipe` (the full 6-field `recipe_identity(leg)`), `seed`, `composed_steps`, `training.train_config.{seed,max_steps}` | `phase30_points.own_control` :229-258 |
| `taught_recall.{numerator,denominator}`, `heldout_recall.{...}` | `own_control` via `control_floors` :265 AND `phase25_promotion.flat_record` :133-138 |
| `condition_c.{point_dialogue_ppl_on,point_dialogue_ppl_off,point_retention_ppl}` | `control_dialogue_pair` :271, `flat_record` :131-141 |
| `per_family_counts`, `zero_extraction_has_nll` (`phase25_verdict.GATE05_KWARG`) | `flat_record` :130, :142 |
| `draws_per_question`, `draws_per_question_source` | `curve_pass` entry :298-299 (copy into the phase32 assembler) |
| `adapter_sha256` (top level) | `control_baseline` :280, `phase29_prereg.CONTROL_BASELINE_SOURCE` :342 |
| `replay.per_step` (NEW, D-19) | the WR-04 check added to `own_control` |
| `stages.*.seconds` | the D-03 clock |

`measure_stage`'s recall blob is keyed `taught` / `heldout` / `taught_off` / `heldout_off` /
`per_family_gain` (`phase25_points.py:575-583`). The record must re-key it to `taught_recall`,
`heldout_recall`, and so on. That re-keying is what `phase25_points.record_kwargs` does at
:773-777, which serves as a **read-only reference**: `record_kwargs` is a WR-05 carrier, and naming
it as a Name, Attribute or string constant reddens `_wr05_failures`.
- `per_family_counts` = `phase25_points._family_counts(scored)` (:662).
- The condition-(c) group can reuse `phase25_record.condition_c_group(capability=measured["capability"], control_gap=..., seed_spread=phase25_points.seed_spread())` (`phase25_record.py:701`). That module is ancestry-frozen, so importing it is fine but editing it is not.
- `control_gap`: at the control, `phase25_condition_c.control_gap_for_capacity(measured["capability"])` (:646). At a non-control, `control_gap_for_capacity(phase30_points.control_dialogue_pair(key, tracked, point_recipe=recipe))`.

**One-path commit** (`phase25_run.commit_point_record` :779-838). Copy it, with
`phase29_prereg.point_record_path(key)` as the one path:
```python
_prove(relative.startswith("results/"), ...)
_prove(path.exists(), ...)
status = subprocess.run(["git", "status", "--porcelain", "--", relative], cwd=_ROOT,
                        capture_output=True, text=True, check=True)
_prove(status.stdout.strip(), f"{relative} is already committed and unchanged ... NO-OP")
subprocess.run(["git", "add", "--", relative], cwd=_ROOT, check=True)
subprocess.run(["git", "commit", "-m", f"feat(25-10): record sweep point {point_key}\n\n..."],
               cwd=_ROOT, check=True)
committed = subprocess.run(["git", "show", "--name-only", "--format=", "HEAD"], ...)
named = [line for line in committed.stdout.splitlines() if line.strip()]
_prove(named == [relative], ...)
```
Add the branch check (`["git", "rev-parse", "--abbrev-ref", "HEAD"]` == `main`) before `add`.
For a REFUSED leg, call it once per untracked path (RESEARCH Pitfall 9). Allowed-actions constant
style (`phase25_run` :751-753):
`ALLOWED_GIT_ACTIONS = ("add", "commit")`, `READ_ONLY_GIT_ACTIONS = (...)`.

**[NEW] The git-surface AST gate cannot see a `_git(*args)` helper.** This was measured.
`tests/test_phase25_driver.py::_git_argv_subcommands` reads the first string constant after
`"git"` in a List or Tuple literal. `phase31_probe._git` builds `("git", *args)`, and every
`_git("ls-files", ...)` / `_git("log", ...)` call is invisible to it. Run on
`scripts/phase31_probe.py`, the gate returns only `[('merge-base', 506, 'calibration_descent')]`.
If phase32 copies the probe's `_git` helper, the `{add, commit}` + read-only gate becomes vacuous
for every call routed through it. The fix is one of these:
- Spell every git argv as a literal list, as `commit_point_record` does.
- Have the phase32 AST test ALSO walk `Call` nodes whose func is `_git` and check that
  `args[0].value` is in the allowed set.

**Write-once emit with dirty refusal second** (probe `_emit_target` :512-534). Use it for the
per-point record write, excluding the record itself:
```python
_prove(not out_path.exists(), f"{out_path} exists — REFUSING to overwrite it. ...")
pathspec = ("scripts", "src", "results")
if out_path.is_relative_to(_GIT_ROOT):
    pathspec += (f":(exclude){out_path.relative_to(_GIT_ROOT).as_posix()}",)
refuse_if_dirty(who="phase31_probe", detail=(...), pathspec=pathspec, cwd=_GIT_ROOT)
```
At run start (probe :334-342), add the Pitfall-3 excludes derived from
`phase30_points.point_plan(k)["prefix"] + "_" + arm` for the 12 keys.

**Provenance block** (probe `_write_record` :537-555): `module_sha256` over PINNED_MODULES,
`git_sha: INSTRUMENT_GIT_SHA`, `head_at_write: git_sha()`, `written_utc`. Add the
`calibration: calibration_descent()` block (:499-509) plus D-06's
`provenance.stop_line = {seconds, cumulative_before_point, past_line_ruling}`.

**Skip-tracked loop** (`phase25_run.main` :903-909):
```python
tracked = set(tracked_point_records()) if args.points is None else set()
for point in points:
    if phase25_prereg.point_record_path(point) in tracked:
        print(f"[phase25_run] {point}: RECORDED already (tracked) — skipping", flush=True)
        continue
```
The phase32 loop walks `phase30_points.SWEEP_SCHEDULE()` (:130) and dispatches on
`phase30_points.next_action(key, tracked)` (:284). A `"refuse"` result goes to
`write_refused_records(act["records"])` (:309). A `"train"` result goes to `act["plan"]`.

**CLI** (probe :915-942):
```python
def build_parser():
    parser = argparse.ArgumentParser(description="...")
    sub = parser.add_subparsers(dest="mode", required=True)
    run = sub.add_parser("run", help="...")
    run.add_argument("--heartbeat", default=str(phase25_run.HEARTBEAT_PATH))
    return parser

def main(argv=None):
    args = build_parser().parse_args(argv)
    import phase25_venue  # torch-free; the banner lets the launch identity be read off the log
    print(phase25_venue.launch_banner(), flush=True)
    ...
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```
Add `run.add_argument("--past-stop-line", metavar="RULING", default=None)` (D-06/D-20).

**Heartbeat stop-line beat** (`phase25_run.beat` :298, five fields, `stage` not validated):
`phase25_run.beat(heartbeat_path, point=key, stage="stop_line", shape=f"cumulative_seconds={clock}", draw_index=None)`.

---

### `scripts/phase32_frontier.py` (assembler, transform + write-once emit)

**Analog 1 — verdict loop:** `scripts/phase25_promotion.py::curve_pass` :261-318. Copy the loop.
Do NOT call `phase25_promotion.control_readings` (:151, a WR-05 carrier that reads the DP control).
Build the readings from each advr control's committed record instead, keyed by the v4.0 twin leg
names that `curve_verdicts` requires (`phase25_verdict.ARM_LEGS` :138, `ADV_ARMS` :121).

Core excerpt (:276-318):
```python
flats = [flat_record(k, records[k], recall[k]) for k in leg_keys]   # phase32: recall_entry = {**rec, "source": point_record_path(k)}
whole_curve = {
    "sweep_extraction_successes": [f["point_extraction_successes"] for f in flats],
    "sweep_extraction_questions": [f["point_extraction_questions"] for f in flats],
    "sweep_taught_recalls": [f["point_taught_recall"] for f in flats],
    "sweep_heldout_recalls": [f["point_heldout_recall"] for f in flats],
    "point_keys": leg_keys,
}
try:
    results = verdict.curve_verdicts(flats, arm, capacity, control_readings_by_arm=by_arm)
except SystemExit as refusal:
    text = str(refusal)
    # 25-REVIEW WR-02: ONLY the sanctioned route's floor refusal is recorded as one.
    _prove(all(marker in text for marker in COVERAGE_FLOOR_REFUSAL_MARKERS), ...)
    refusals[leg] = text
    results = [None] * len(flats)
for key, flat, result in zip(leg_keys, flats, results):
    kwargs = pin_kwargs_for(flat, arm, readings[leg], anchors, whole_curve)
    entry = {**kwargs, "leg": leg,
             "route": "phase20_gate_coverage.corrected_point_verdict (D-34)",
             "whole_curve_inputs": whole_curve, "recall_counts": flat["recall_counts"],
             "k": records[key]["draws_per_question"],
             "k_source": records[key]["draws_per_question_source"]}
    if result is None:
        entry.update(verdict=None, reasons=[refusals[leg]],
                     early_return_reason="REFUSED by the sanctioned route before the pin was reached")
    else:
        outcome, reasons, verdict_arm = result
        entry.update(verdict=outcome, reasons=list(reasons),
                     early_return_reason=early_return_reason(reasons))
```
Import these, never retype them: `phase25_promotion.flat_record` (:129), `pin_kwargs_for` (:229),
`early_return_reason` (:221), `phase25_verdict.never_taught_anchors` (:222), and
`phase29_prereg.COVERAGE_FLOOR_REFUSAL_MARKERS` (:93). Use `from ... import` only for names not in
`_CARRIERS`; the plain module-attribute style is safest.

PREREG-03 REFUSED keys: these were never routed. Their entry is `{verdict: None,
early_return_reason: <non-empty>, control_recall_counts: record["control_recall_counts"]}`
(`phase29_prereg.refused_record` :230; `admission` checks it at :477-479).

**Analog 2 — write-once emit with the D-16 checkpoint:** `scripts/phase31_budget.py::emit`
:372-409:
```python
def emit(out_path=BUDGET_RECORD):
    """Write-once: overwrite refusal, dirty refusal, sweep-point refusal, then build and write."""
    out_path = pathlib.Path(out_path)
    if not out_path.is_absolute():
        out_path = _GIT_ROOT / out_path
    _prove(not out_path.exists(), f"{out_path} exists — REFUSING to overwrite it. ...")
    pathspec = ("scripts", "src", "results")
    if out_path.is_relative_to(_GIT_ROOT):
        pathspec += (f":(exclude){out_path.relative_to(_GIT_ROOT).as_posix()}",)
    refuse_if_dirty(who="phase31_budget", detail=(...), pathspec=pathspec, cwd=_GIT_ROOT)
    tracked = phase31_probe._tracked()
    require_no_sweep_point(tracked)                  # phase32: require all 12 point records tracked
    record = build_record(tracked)                   # pure; tests call it directly
    record["calibration"] = phase31_probe.calibration_descent()
    record["provenance"] = {"module_sha256": {...}, "git_sha": INSTRUMENT_GIT_SHA,
                            "head_at_write": git_sha(), "written_utc": ...}
    phase25_run.atomic_write_json(out_path, record)
```
Sources pinned by sha256, computed live (budget :360-368):
`record["sources"] = {rel: _sha256(_GIT_ROOT / rel) for rel in read}`. Use the same idiom for the
D-13 `v4_source`. The v4 path is `phase25_record.FRONTIER_RECORD` (`phase25_record.py:107`, an
absolute path). Relativise it; never type `"results/phase25_frontier.json"`. The output path is
`next(p for p in phase29_prereg.V5_RESULT_PATHS if p.startswith("results/phase32_frontier"))`.

The emitter does not commit. The commit is a separate plan task after a
`checkpoint:human-verify gate="blocking"` task, copied from 31-06-PLAN.md :92-116 (resume-signal
text "approved"; nothing is re-emitted or edited without a ruling).

`admission()` self-check before the write: `phase29_prereg.admission(frontier)["verdict"] != "INCONCLUSIVE"` (:502).

(c) readings: `phase29_prereg.cleared_abc(entry)[2]` and `phase29_prereg.point_verdict_string(point)`
(re-exports of `phase27_prereg` :261 / :240). Never parse reason strings to read (c) pass/fail.

**`"control_readings"` literal:** allowed only as a dict-literal key or a subscript string, after
the D-17 continuation lands. The continuation must land BEFORE this file does.

---

### `artifacts/com.personacore.phase32.sweep.plist` (config)

**Analog:** `artifacts/com.personacore.phase31.probe.plist` (read whole). Change only:
- `Label` -> `com.personacore.phase32.sweep`
- `ProgramArguments[3]` -> `/Users/juliorcoelho/PersonaCore/scripts/phase32_points.py`
- Log pair -> `logs/phase32_sweep.{out,err}`
- The header comment (Phase 32 D-05; one agent runs all 12 points).

Keep `KeepAlive` false, `RunAtLoad` false, `caffeinate -dims`, the venv python, `--heartbeat
.../data/phase25_heartbeat.jsonl`, `WorkingDirectory`, `ProcessType Interactive`, and the
`EnvironmentVariables` dict identical (`PERSONACORE_SWEEP_ACTIVE=1`, `PATH`, `PYTHONUNBUFFERED`).
Keep the argv fixed, with no `--past-stop-line` (D-20).

---

### `tests/test_phase32_points.py` (tests)

**Analog:** `tests/test_phase31_probe.py`.

**Header / sys.path / autouse dirty-tree recorder** (:1-47):
```python
@pytest.fixture(autouse=True)
def clean_tree(monkeypatch):
    """The run and emit refuse a dirty tree, and this suite runs on dirty trees, so the guard is
    RECORDED (the tests/test_phase30_calibration.py idiom)."""
    calls = []
    monkeypatch.setattr(probe, "refuse_if_dirty", lambda **kw: calls.append(kw) or "")
    return calls
```

**D-12 module-scoped live fixture** (:310-389). Copy the patch set verbatim, then add the phase32
knobs from RESEARCH Pitfall 2:
- `mitigation_budget.STEP_BUDGET -> tp.MAX_STEPS`
- The scratch git repo from `tests/test_phase25_driver.py::_scratch_repo` (:142-155), holding a
  committed calibration and a forged budget
- `phase30_points._ROOT` and the driver roots pointed at the scratch repo
- The `tp.score_arm` spy that forces the n8 control learnable

```python
with pytest.MonkeyPatch.context() as monkeypatch:
    monkeypatch.setattr(phase25_run, "_DEVICE", "cpu")
    _e2e_env(root, monkeypatch)                       # from test_phase22_wiring (:715)
    slim = root / "convbase_slim.pt"
    export_slim(root / "convbase.pt", slim)
    monkeypatch.setattr(phase14_recall, "CONVBASE_SLIM", slim)
    monkeypatch.setattr(phase14_recall, "RECALL_MAX_NEW_TOKENS", 4)
    monkeypatch.setattr(phase25_run, "DRAWS_DIR", root / "data")
    monkeypatch.setattr(phase19_erasure, "RETENTION_BIN", tp.DIALOG_VAL_BIN)
    monkeypatch.setattr(probe, "_ROOT", root)
    monkeypatch.setattr(phase25_points, "_ROOT", root)
    subset = _one_prompt_per_cell(json.loads(x18.CORPUS_PATH.read_text(encoding="utf-8")))
    monkeypatch.setattr(phase25_points, "attack_corpus", lambda: (subset, x18.corpus_sha256(subset)))
    ...
    _spy(phase25_points, "train_stage"); _spy(phase25_points, "measure_stage")
    _spy(phase25_run, "draw_point_shapes"); _spy(phase25_run, "score_point")

@pytest.fixture(scope="module")
def point_probe_run(tmp_path_factory):
    return _point_probe_fixture(tmp_path_factory.mktemp("point_probe"))
```
The spies forward to the real stages (:353-363). The assertions check real artifacts: the adapter
sha, a finite retention value, all `ATTACK_FAMILIES` drawn, per-step replay, and a last heartbeat
of `"done"` (:392-428). The strays guard compares before/after (:290-298, :427-428). The phase32
version globs `phase32` targets with Python `Path.glob`, never a shell glob (zsh NOMATCH).

**Refusal tests on a light env** (:431-462): `_light_env` patches `train_stage` to
`pytest.fail("trained past a refusal")`.

**CLI signature-binding recorder** (:931-978). `inspect.signature(...).bind(*args, **kwargs)`
proves that the kwargs `main()` passes fit the real function (the 25-14 class).

**Plist test** (:981-1001). Copy it and change the label and script assertions. Use `plistlib` only;
never `plutil -lint` (it would move the `tests/test_phase25_venue.py` skip pin).

**Git surface AST**: import `_git_argv_subcommands` / `_git_surface_failure` from
`test_phase25_driver` (the import-from-sibling-test idiom is at `tests/test_phase30_points.py:37-41`).
Also cover `_git(...)` call sites (see [NEW] above).

**Census imports** to apply to the new module: `_gate_retype_failures` (`tests/test_phase29_prereg.py`
:484; `_GATE_DEFS` :423). It is currently applied only to `phase29_prereg.py` (:573). The new
phase32 tests should run it over `scripts/phase32_*.py`, with a planted RED via `_planted` (:526).

Forbidden in phase32 tests: the literal `== 10` / `!= 10`, the text `train_arm(`, `skipif`,
`pytest.skip` (RESEARCH Pitfall 8).

---

### `tests/test_phase32_frontier.py` (tests)

**Analog:** `tests/test_phase31_budget.py`.
- Write-once, both states (:305-316): a tmp file refuses, and the real path refuses iff tracked.
- Dirty-first ordering (:319-335): patch `probe._tracked` to raise, and prove `build_record` was
  never reached. Assert the recorded pathspec includes the `:(exclude)` of the target.
- Committed-recompute, both states (:378-403): if tracked, `build(...)` equals the committed record
  minus `provenance`/`calibration`; if untracked, run twice over forged records and check
  determinism.
- Ancestry non-vacuity (:406-428): `_assert_frozen_before` plus a natural RED.

Forged frontiers for the admission and template states: `tests/test_phase29_prereg.py::_v5_frontier`
(:650-685). It already builds a REFUSED entry as
`{"verdict": None, "early_return_reason": "own control unlearnable (PREREG-03)"}` with per-leg
control counts.

v4 byte guard: use git pathspec globs in quoted argv (`git diff --quiet v4.0 HEAD -- 'results/phase25_*' ...`), never shell globs. Precedent: `git ls-tree -r --name-only v4.0 results` at `tests/test_phase29_prereg.py:170`.

---

### `tests/test_phase30_points.py` (MODIFY — D-17 continuation + WR-04 fixture)

**Analog:** the same file. The in-place continuation idiom is the "Review WR-06" comments inside
`_wr05_failures` (:570-571) and inside the planted-RED list (:656).

The node branch to amend, :612-620:
```python
elif (
    isinstance(node, ast.Constant)
    and isinstance(node.value, str)
    and id(node) not in docstrings
    and (node.value in _CARRIERS or node.value.startswith("dp_n"))
):
    # getattr / importlib spell a carrier as a string; "dp_n" + ... builds a dp key.
    failures.append(f"carrier or dp-key string {node.value!r} at line {line}")
```
Collect the allowed-position ids first, the same way `_docstring_nodes` (:549-562) does:
`{id(k) for Dict in walk for k in d.keys if Constant == "control_readings"} | {id(s.slice) for Subscript ...}`.
Exempt only those ids, and only for the value `"control_readings"`. Add a dated comment block
(`# Dated continuation, 2026-09-27 (Phase 32 D-17): ...`).

Natural-RED cases go in the `test_ast_guard_planted_red_per_class` plant list (:651-664). The
list already has `getattr` (:657) and `from phase25_promotion import control_readings` (:655).
Add these five:
- `getattr(x, "control_readings")`
- a bare `_X = "control_readings"`
- `_X = phase25_promotion.control_readings` (Attribute)
- `_X = control_readings` (Name)
- the import

Then add the two exempt forms: `{"control_readings": 1}` and `v["control_readings"]`. Both must
return `[]`.

`_good_control` (:238-261) gains a `"replay": {"per_step": [recipe["replay_windows"]] * recipe["max_steps"], ...}` block. Pair it with a WR-04 refusal test in the `_perturbed` style (:279-284).

---

### `scripts/phase30_points.py` (MODIFY — D-19 WR-04, IN-04)

**Analog:** the existing WR-04 block in `own_control` :247-258. Append the replay check right
after it, in the same style:
```python
# WR-04: the declared recipe is not enough; what the control TRAINED with must agree too.
config = (record.get("training") or {}).get("train_config") or {}
trained = {...}
off = sorted(f for f, got in trained.items() if any(v != point_recipe[f] for v in got))
_prove(not off, f"control record trained with {trained}, not the point's recipe on {off} (D-16, WR-04): ...")
```
New check: `(record.get("replay") or {}).get("per_step") == [point_recipe["replay_windows"]] * point_recipe["max_steps"]`.

IN-04 lives in `recipe_identity` :94-97. The lowest-churn fix is to prove
`name.split(".", 1)[0] == "teach_persona"` for each `phase29_prereg.REPLAY_SOURCE` entry.

Commit this ALONE and before launch. Its SHA then goes into `_SUPERSEDED_PINS` (next file).

---

### `tests/test_phase30_calibration.py` (MODIFY — `_SUPERSEDED_PINS` continuation)

**Analog:** the same file, :339-380 (the existing dated block):
```python
# =================================================================================================
# DATED CONTINUATION, 2026-09-25 (developer ruling "Fix CR-01 + WR now"): the phase30_points pin
# =================================================================================================
_RECORD_COMMIT = "4339f2b2bc29ab0765a821b5d47b617cd6092f24"
_SUPERSEDED_PINS = {
    "scripts/phase30_points.py": frozenset(
        {
            "a7d5c9d8fe2bf89193f09cad9c3f46133530b07c",  # CR-01
            "8dd1d30fdccc98eb835cc4bd5424fc935bf8557c",  # WR-04
            "00bc4da3880d051faac52a7fdc5408d89f0915ab",  # WR-05
        }
    ),
}
```
Add the D-19 fix commit's full SHA with a dated comment
(`# Phase 32 D-19 WR-04 replay + IN-04, 2026-09-27`). `_superseded` requires
`since == set(allowed)` exactly, so every commit that touches `scripts/phase30_points.py` needs its
own SHA. The registration commit touches only `tests/`, so it does not count against itself. The
tripwire test (:365-380) needs no change. Its four assertions (live, extra, missing, never-true)
cover the new SHA automatically.

Cross-check (measured): no other test compares the committed `results/phase31_*` records'
`module_sha256["scripts/phase30_points.py"]` against live bytes. `tests/test_phase31_probe.py:524`
runs on a fixture emit only, and `tests/test_phase31_budget.py` has no pin check. So this is the
only tripwire the edit trips.

Second analog for the docstring wording: `tests/test_phase27_relearn.py` :1188-1269.

---

### Runbook (NEW)

**[NEW] Location warning:** it cannot live under `results/phase32_*`.
- `phase29_prereg.V5_RESULT_PATHS` (:148-158) pre-registers only `results/phase32_point_*.json` and
  `results/phase32_frontier.json`.
- Any tracked `results/phase3*` file enters `ARTIFACT_PATHSPECS` (:161) and the ancestry guards:
  `tests/test_phase29_prereg.py:109`, and `tests/test_phase31_budget.py:417-420`, which asserts
  `git ls-files results/phase32_*` is exactly what is expected.

The v4.0 precedent `results/phase25_operational_note.md` does not carry over to v5.0.

Recommended: `.planning/phases/32-replay-bearing-frontier-re-run-and-verdict/32-RUNBOOK.md`, or a
printed launch brief inside the launch plan task.

**Analog content:** 31-04-PLAN.md :53-116:
- Pre-launch gates (1)-(8): porcelain count 0; suite EXIT=0; targeted live-path tests; `find`
  (not a glob) for stray targets; MPS True; disk; plist check; `launchctl print` non-zero.
- The four commands:
  - `cp` to `~/Library/LaunchAgents`
  - `launchctl bootstrap gui/$(id -u) ...plist`
  - `launchctl kickstart gui/$(id -u)/com.personacore.phase32.sweep`
  - `launchctl bootout ...` after exit
- A `checkpoint:human-action gate="blocking"` task (Claude never runs launchctl).

The Phase 32 additions:
- The D-20 manual relaunch command:
  `caffeinate -dims .venv/bin/python scripts/phase32_points.py run --past-stop-line "<ruling>"`
- Find the driver by ppid under launchd (caffeinate is the child).
- `PERSONACORE_SWEEP_ACTIVE=1` for any pytest run during the sweep.
- The reviewed-delete recipe for a mid-training crash (checkpoint + adapter + training sidecar).

---

## Shared Patterns

### Invariant refusal
**Source:** `scripts/phase30_points.py:59-62`, `scripts/phase31_probe.py:100-103`
**Apply to:** both new scripts
```python
def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase30_points] {message}")
```

### Tracked-blob read (CR-01)
**Source:** `scripts/phase30_points.py::_tracked_json` :184-197
**Apply to:** the stop-line read, the D-03 clock over committed point records, and every frontier input
```python
shown = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=_ROOT, capture_output=True)
_prove(shown.returncode == 0, f"{what} {rel} has no committed blob at HEAD")
_prove(shown.stdout == (_ROOT / rel).read_bytes(), f"{what} {rel} differs from its committed blob ...")
return json.loads(shown.stdout.decode("utf-8"))
```

### Atomic write
**Source:** `scripts/phase25_run.py::atomic_write_json` :118
**Apply to:** every JSON write (sidecars, records, frontier). The `os.replace` census
(`tests/test_phase25_driver.py:341`) allows `os.replace` only in `phase25_run.py` and
`phase25_record.py`.

### Dirty-tree refusal
**Source:** `src/personacore/provenance.py::refuse_if_dirty(*, who, detail, pathspec=(), cwd=None)` :47
**Apply to:** run start (with the Pitfall-3 excludes) and each write (excluding the target). Tests
record it through the autouse `clean_tree` fixture.

### Derive, never type
**Apply to:** everything. The stop line comes from the budget record; 32/256 from
`calibration_record(...)["recipe"][leg]["replay_windows"]`; K from `mitigation_budget.CURVE_K`;
paths from `V5_RESULT_PATHS` / `point_record_path`; `"adversarial"` from `phase25_verdict.ARM_LEGS`;
the v4 frontier path from `phase25_record.FRONTIER_RECORD`.

### Natural RED over planted RED
**Source:** `tests/test_phase30_calibration.py:320-323`, `tests/test_phase31_budget.py:413-415`
(`pytest.raises(subprocess.CalledProcessError)` on a real older artifact). Planted cases use
`_planted` (`tests/test_phase29_prereg.py:526`) and assert that the real file is unchanged afterward.

## No Analog Found

| File / piece | Role | Reason |
|---|---|---|
| D-15 template sentences + state enumeration in `phase32_frontier.py` | transform | No prior count-driven sentence emitter exists. The closest is `phase28_report.py`'s lambda table (:408, `"ledger_v4_count": lambda r: ...`), which binds numbers into fixed text. Use RESEARCH Pattern 8 for the states. |
| D-08 per-session sha check (`git diff --name-only <sha> HEAD -- PINNED_MODULES`) | driver | 31-05 did it by hand; no code precedent. The sessions sidecar reuses `atomic_write_json`. Add `diff` to `READ_ONLY_GIT_ACTIONS`. |

## Metadata

**Analog search scope:** `scripts/phase2[5-9]_*.py`, `scripts/phase3[01]_*.py`,
`src/personacore/provenance.py`, `tests/test_phase2[2579]_*.py`, `tests/test_phase3[01]_*.py`,
`artifacts/*.plist`, `.planning/phases/31-*/31-0[46]-PLAN.md`, `results/phase25_operational_note.md`
**Files scanned:** ~25
**Measured this session:** `_git_argv_subcommands(scripts/phase31_probe.py)` returns only the
`merge-base` literal (the `_git(*args)` blind spot); no committed-record pin check on
`phase30_points.py` outside `tests/test_phase30_calibration.py`.
**Pattern extraction date:** 2026-09-27
