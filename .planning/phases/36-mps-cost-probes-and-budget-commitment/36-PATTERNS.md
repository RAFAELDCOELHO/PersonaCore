# Phase 36: MPS Cost Probes and Budget Commitment - Pattern Map

**Mapped:** 2026-10-02
**Files analyzed:** 14 (12 new, 1 modified test register, 1 committed data file)
**Analogs found:** 13 / 14

All line numbers below were read at HEAD `5deba79`. No `scripts/phase36_*` or `tests/test_phase36_*`
file exists yet. No script in the tree calls `phase35_prereg.fill(` today
(`grep -rln "phase35_prereg.fill(" scripts/ src/` returns only `scripts/phase35_prereg.py`), so the
Phase 36 fill file is the first real one. Its only analog is the planted file in
`tests/test_phase35_prereg.py:2585-2589`.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `scripts/phase36_prereg.py` (D-17 entries, NO `fill`) | config / pre-registration | transform (import-time proofs) | `scripts/phase35_prereg.py` §2 entry schema + `_ENTRIES` (:150-191, :682-760) | exact |
| `tests/test_phase36_prereg.py` | test | git-history + AST | `tests/test_phase35_prereg.py` (:274-424, :433-441, :2725-2839) + `tests/test_phase29_prereg.py:69-106` | exact |
| `scripts/phase36_probe.py` (probe driver, all fronts) | driver / service | batch, file-I/O, event (heartbeat) | `scripts/phase31_probe.py` + WR-02 from `scripts/phase32_points.py:334-400` | exact |
| `tests/test_phase36_probe.py` | test | CPU live-path fixture | `tests/test_phase31_probe.py` | exact |
| `artifacts/com.personacore.phase36.probe.plist` | config (LaunchAgent) | — | `artifacts/com.personacore.phase31.probe.plist` | exact |
| `scripts/phase36_budget.py` (derive, cut table, emit) | service (pure derivation + write-once emit) | transform over committed records | `scripts/phase31_budget.py` | exact |
| `scripts/phase36_budget_prereg.py` (the fill file) | config (owner fill file) | transform | planted `_fill_file` in `tests/test_phase35_prereg.py:2573-2589` + RESEARCH "fill file shape" | partial (no real file exists) |
| `tests/test_phase36_budget.py` | test | unit + git ancestry | `tests/test_phase31_budget.py` | exact |
| `scripts/phase36_ledger.py` | service | append-only log read + committed-record read | `scripts/phase32_points.py:291-326` (clock + stop line) + `scripts/phase25_watch.py:274-318` (torn tail) + `scripts/phase25_run.py:298-368` (beats) | role-match |
| `tests/test_phase36_ledger.py` | test | unit | `tests/test_phase25_watch.py:161-200` + `tests/test_phase32_points.py:341-367` | role-match |
| `scripts/phase36_caps.py` | utility (guard imported by owner fill files) | committed-blob read | `scripts/phase30_points.py:190-203` (`_tracked_json`) | role-match |
| `tests/test_phase36_caps.py` | test | AST scan + planted repo | `tests/test_phase35_prereg.py:2120-2166, 2463-2475, 2583-2660` | role-match |
| `tests/test_phase23_resume.py` (MODIFY: register line) | test register | — | its own `_TRAIN_ARM_CALL_SITES` (:60-161) + call-count literal (:323-332) | exact |
| committed launch ledger (Q3, path outside `results/`) | data file (append-only, committed) | append-only | none committed; nearest is `phase25_run.beat` jsonl in gitignored `data/` | no analog |

---

## Pattern Assignments

### `scripts/phase36_prereg.py` (pre-registration, D-17 entries, no `fill`)

**Analog:** `scripts/phase35_prereg.py`

**Header and import block** (:118-135). Copy the shape: stdlib only, `sys.path` inserts, torch-free.
Add `COMMITTED` and `RECORDS_AT_COMMIT = 0`:
```python
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
...
import mitigation_budget  # noqa: E402  (same; torch-free)
...
# At this commit no `results/phase3[6-9]_*` or `results/phase4[0-5]_*` file existed, tracked or
# untracked.
COMMITTED = "2026-10-01"
RECORDS_AT_COMMIT = 0
```

**`_prove`** (:675-678). Copy verbatim, with the prefix `[phase36_prereg]`:
```python
def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase35_prereg] {message}")
```

**Entry schema** (:150-191). Phase 36 may import the PUBLIC `phase35_prereg.ENTRY_FIELDS`, `KINDS` and
`FORBIDDEN_PHRASE`. It may NOT call `phase35_prereg._prove_entry`: the slot census flags any
`phase35_prereg._*` attribute (`tests/test_phase35_prereg.py:2214-2216`). Re-implement `_prove_entry`
locally over the public tuples:
```python
ENTRY_FIELDS = ("value", "derivation", "kind", "source")
KINDS = ("derived", "preference")
FORBIDDEN_PHRASE = "selected by THE USER, verbatim"

def _prove_entry(name, entry):
    _prove(isinstance(entry, collections.abc.Mapping), ...)
    for banned in ("proposer", "adopted_by"):
        _prove(banned not in entry, ...)
    _prove(set(entry) == set(ENTRY_FIELDS), ...)
    _prove(entry["kind"] in KINDS, ...)
    for field in ("derivation", "source"):
        text = entry[field]
        _prove(isinstance(text, str) and text.strip(), ...)
        _prove(FORBIDDEN_PHRASE not in text, ...)
```

**Entry literal + freeze** (:682-760). One entry per D-17 threshold (25% divergence, T ≤ 800, E4
reserve of 3 points at T = 200, the 1.5× per-front stop, the `min(1.5Σ, 90)` formula, the projection
check, S ≥ 3 for the table, the cut order, plus D-19's Phase 43 first-point obligation):
```python
    "mps_ceiling_hours": {
        "value": 90,
        "derivation": "Rafael's ceiling for all v6.0 MPS work, probes included",
        "kind": "preference",
        "source": "COST-02 (a9cd408)",
    },
...
ENTRIES = types.MappingProxyType(
    {name: types.MappingProxyType(entry) for name, entry in _ENTRIES.items()}
)

def _prove_entries():
    for name, entry in ENTRIES.items():
        _prove_entry(name, entry)

_prove_entries()
```
The test AST helper `_entries_node` looks for a module-level `_ENTRIES` assignment
(`tests/test_phase35_prereg.py:302-308`), so keep the name `_ENTRIES`.

**Census constraints on this file** (it matches `scripts/phase36_*prereg.py`):
- It must contain NO `phase35_prereg.fill(` call. `_fill_sites` ignores files without a fill
  (`tests/test_phase35_prereg.py:2463-2472`). If it held one, its first commit would trip leg (b).
- It must contain no string constant equal to `"phase35_prereg"` and none starting with `"_rule_"`
  (:2246-2249). Docstrings are AST constants too, but only an EXACT `"phase35_prereg"` matches.
- Use `phase35_prereg.p22_onset_sigma(800)` (public, :1028) for the import-time P22 proof, and
  `phase35_prereg.E3_SIGMAS` (:496) for the noised minimum. Never retype 0.5.

---

### `tests/test_phase36_prereg.py`

**Analog:** `tests/test_phase35_prereg.py`

**Imports** (:27-71). Use the same sys.path block, then:
```python
from test_phase29_prereg import (  # noqa: E402  (underscore names only)
    _assert_frozen_before,
    _git,
    _module_targets,
    _numeric_constants,
    _planted,
)
```

**Ancestry, honest at zero** (:433-441, the shape to copy):
```python
def test_phase35_prereg_is_frozen_before_every_v6_result():
    tracked = sorted(
        {
            path
            for spec in phase35_prereg.ARTIFACT_PATHSPECS
            for path in _git("ls-files", spec).split()
        }
    )
    _assert_frozen_before(PREREG, tracked)
```
For Phase 36, use `tracked = sorted(_git("ls-files", "results/phase36_*").split())`.
`_assert_frozen_before` (`tests/test_phase29_prereg.py:69-106`) does the following:
- refuses a shallow clone;
- takes `adds[-1]`, the EARLIEST add, so delete-and-re-add cannot launder the ordering;
- refuses a prereg commit equal to the first add;
- runs `git merge-base --is-ancestor`;
- asserts `checked == len(prereg_commits) * len(tracked)`.

For the non-vacuity leg, copy `tests/test_phase31_budget.py:406-415` (natural RED, `pytest.raises(subprocess.CalledProcessError)` on a file added earlier):
```python
    # NON-VACUITY (natural RED): the calibration was added before the budget existed.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(BUDGET, [pts.CALIBRATION_PATH])
```
With zero phase36 records, plant a natural RED by passing a file that was added before
`scripts/phase36_prereg.py` existed (for example `scripts/phase35_prereg.py` itself).

**Entries: exactly four fields** (:274-299). Copy `test_entries_have_exactly_the_four_fields`,
`_good_entry` and `test_entries_refuse_an_unknown_kind_or_missing_field`. Point them at
`phase36_prereg.ENTRIES` and `phase36_prereg._prove_entry`. Tests MAY use privates, because the census
scans only scripts/src.

**No proposer, runtime + AST, RED on a planted copy** (:300-386). Copy `_entries_node`,
`_entry_string_failures`, `_first_inner` and `test_no_proposer_or_adopted_by_in_any_entry`. They use
`_insert_at` (:110-115) and `_planted` (`tests/test_phase29_prereg.py:526-532`).

**Torch-free import** (:392-410):
```python
_HEAVY = ("torch", "teach_persona", "phase19_erasure", "phase18_extraction", "phase23_run", "phase26_canary")

def test_the_prereg_imports_without_torch():
    probe = (
        "import sys; sys.path.insert(0, 'scripts'); import phase35_prereg; "
        f"print(*[name in sys.modules for name in {_HEAVY!r}])"
    )
    out = subprocess.run([sys.executable, "-c", probe], cwd=_ROOT, capture_output=True, text=True, check=True)
    assert out.stdout.split() == ["False"] * len(_HEAVY), out.stdout
```

**Zero skips** (:413-424). Copy `_SKIP_ATTRS`, `_skip_failures` and `test_no_skips_in_this_file`.
Its planted leg appends a `pytest.skip("x")` test and asserts the guard reds.

**CPU-test census, `_untested_functions`** (:2725-2744 + :2814-2839). Copy it and swap the
module name. `_is_module` (:2140-2141) becomes `node.id == "phase36_prereg"`. The `_rule_`/`fill`
clause is dropped because Phase 36 has no rules:
```python
def _untested_functions(prereg_source, test_source):
    tree = ast.parse(test_source)
    imported = {alias.asname or alias.name for n in ast.walk(tree)
                if isinstance(n, ast.ImportFrom) and n.module == "phase35_prereg" for alias in n.names}
    calls = [n.func for n in ast.walk(tree) if isinstance(n, ast.Call)]
    named = {f.id for f in calls if isinstance(f, ast.Name) and f.id in imported}
    named |= {f.attr for f in calls if isinstance(f, ast.Attribute) and _is_module(f.value)}
    named |= {"_rule_" + slot for slot, _ in _fill_calls(test_source) if slot is not None}
    defs = [n.name for n in ast.parse(prereg_source).body if isinstance(n, ast.FunctionDef)]
    return sorted(name for name in defs if name not in named)
```
`test_every_rule_has_a_cpu_test` (:2814-2839) carries three planted legs, all to be kept:
- an untested def;
- a bare mention that is not a call;
- a call on another module.

It then asserts that the real file's bytes are unchanged. Per RESEARCH, apply the same census to
`phase36_budget.py`, `phase36_ledger.py` and `phase36_caps.py`, which are rule modules (PREREG-08).

**Basename strays** (`tests/test_phase23_prereg.py:553-575`):
```python
    tracked = _git("ls-files", "results/*").split()
    stray = [path for path in tracked
             if "phase23" in pathlib.PurePosixPath(path).name and not path.startswith("results/phase23_")]
    assert stray == [], ...
```
Repeat the check for `phase36` and for `probe36` (Pitfall 15).

---

### `scripts/phase36_probe.py` (probe driver: E1 [+ R1b], E2, E3 T=200/T=800, E5, E6)

**Analog:** `scripts/phase31_probe.py`. WR-02 comes from `scripts/phase32_points.py`.

**Imports / roots** (`phase31_probe.py:23-57`). Copy the two-root pattern. `_ROOT` is patchable (it
holds the data/ sidecars) and `_GIT_ROOT` is never patched:
```python
_ROOT = pathlib.Path(__file__).resolve().parent.parent
# The git root. Same value as _ROOT at import, but never patched: every git call and every module
# hash reads it, so a test that redirects _ROOT (the data/ sidecars) changes no git answer.
_GIT_ROOT = pathlib.Path(__file__).resolve().parent.parent
...
import phase25_run  # noqa: E402  (same)
from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402
INSTRUMENT_GIT_SHA = git_sha()
```
Every torch-touching module is imported LAZILY inside the run functions (`:328-329`
`import teach_persona as tp; import torch`).

**Identity + isolation guard** (`:59-64`, `:139-153`):
```python
PROBE_KEY = "probe31_advr_n64"
PROBE_PREFIX = "probe31"
...
    for label in (PROBE_PREFIX, RELEARN_LABEL):
        _prove(
            not label.startswith("phase3")
            and not label.startswith(phase25_points.CALIBRATION_PREFIX_LITERAL),
            f"probe label {label!r} resolves under a sweep or calibration prefix",
        )
```
Use `probe36`, and extend the refusal to `phase4` (v6.0 owns `phase36_*`…`phase45_*`). Derive record
paths from the prereg tuple rather than typing them (`:66-71`):
```python
POINT_RECORD = next(p for p in phase29_prereg.V5_RESULT_PATHS if p.startswith("results/phase31_probe_point"))
```
In Phase 36, `phase35_prereg.V6_RESULT_PATHS` holds only the GLOB `"results/phase36_probe_*.json"`
(`phase35_prereg.py:317-319`). Name the concrete per-front paths in the module, then prove at
import that each `fnmatch`es that glob.

**Pinned modules** (`:73-84`). The torch-importing modules are listed as paths, not imports:
```python
PINNED_MODULES = tuple(
    pathlib.Path(path).resolve().relative_to(_GIT_ROOT).as_posix()
    for path in (
        __file__,
        phase25_points.__file__,
        phase25_run.__file__,
        ...
        _SCRIPTS + "/teach_persona.py",  # a path, not an import: teach_persona imports torch
        _SRC + "/personacore/training/loop.py",
    )
)
```
Phase 36 adds the following as paths: `phase19_erasure.py`, `phase14_recall.py`,
`phase18_extraction.py`, `phase14_factset_gate.py` and `phase17_persona_facts.py`.
`scripts/phase32_points.py:66-95` is the wider list to borrow from.

**Run-start refusal + heartbeat + per-stage timing** (`:322-345`, `:382-403`, `:483-491`):
```python
    refuse_if_dirty(
        who="phase31_probe",
        detail=("the probe records the commit it ran from; a run from a dirty tree times code that "
                "commit does not contain"),
        pathspec=("scripts", "src", "results"),
        cwd=_GIT_ROOT,
    )
    phase25_run.disk_precheck()
    run_git_sha, device, torch_version = git_sha(), phase25_run.device(), torch.__version__
    started_utc = _now()
    ...
    state = {"point": PROBE_KEY, "stage": "train", "shape": None, "draw_index": None}
    stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
    try:
        ...
        real_train = tp.train
        tp.train = _counting_train          # runtime wrap, restored in finally
        started = time.monotonic()
        try:
            training = phase25_points.train_stage(plan)
        finally:
            tp.train = real_train
        outer["train"] = time.monotonic() - started
        ...
        phase25_run.atomic_write_json(sidecar, run)
        # "done" BEFORE the stop event: a periodic beat racing the stop can only write "done".
        state.update(stage="done", shape=None, draw_index=None)
    finally:
        stop.set()
        thread.join()
    phase25_run.beat(heartbeat_path, point=PROBE_KEY, stage="done", shape=None, draw_index=None)
```
For the D-12 ledger, set `state["point"]` to a run id such as `v6/36/<front>/<unit>`, so the ledger
can group beats per run (RESEARCH §Ledger).

**Reused-stage flags** (`:376-380`, Pitfall 5). A front must never be priced from a reused stage:
```python
    reused = {
        "train": train_sidecar.exists(),
        "measure": phase25_points.measure_sidecar(PROBE_KEY).exists(),
        "draw": phase25_run.draws_path(PROBE_KEY).exists(),
    }
```

**Half-trained refusal** (`:357-369`). Copy the two `_prove(train_sidecar.exists() or not paths["checkpoint"].exists(), ...)` guards.

**E3 re-key + T = 800.** Re-key exactly as `:144` does:
`plan = dict(action["plan"], point_key=PROBE_KEY, prefix=PROBE_PREFIX)`.
For T = 800, set `tp.MAX_STEPS = 800` at runtime AND pass a plan copy with
`pinned_mechanism.composed_steps = 800`. That is the shape the Phase 31 fixture uses
(`tests/test_phase31_probe.py:345-349`):
```python
            pinned = dict(real_plan["pinned_mechanism"], composed_steps=tp.MAX_STEPS)
            return dict(real_plan, pinned_mechanism=pinned)
```
Restore `tp.MAX_STEPS` in `finally`. `teach_persona.py` itself stays byte-unchanged (sha-pinned).

**WR-01 run.csv move** (`scripts/phase25_points.py:484-493`). `train_arm` writes
`results/<prefix>_<arm>/run.csv`, so move it under `data/` in the same process. `train_stage`
already does this for E3. The new E2 `tp.train_arm(...)` call site must do it itself:
```python
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
```
For the idempotent both-or-neither variant, see `scripts/phase31_probe.py:633-668` (`relearn_moves` / `_finish_relearn_moves`).

**E1 / R1b call route** (`scripts/erasure_kstar_run.py:126-142`). Use the committed prefix, keep the
adapter-sha check before and after, and point `record_path` into a `data/probe36_*` path:
```python
    curve = _curve()
    sha_before = _sha256(recall.ADAPTER_PATH)
    _prove(sha_before == curve["adapter_in_sha256"], ...)
    components = [tuple(address) for address in curve["ordered_prefix"][:k]]
    device = preflight_device(strict=True)["device"]
    pin.run_erasure_arm("erased", device, components=components, record_path=record_path)
    _prove(_sha256(recall.ADAPTER_PATH) == sha_before, ...)
```
`run_erasure_arm` refuses an existing `record_path` (`scripts/phase19_erasure.py:2789-2795`), so the
second D-18 run needs its own path.

**Per-draw timer (D-18).** Wrap `phase14_recall._complete` at runtime and restore it in `finally`,
in the same wrap-and-restore shape as `tp.train` above. `_complete` returns `(gen, stopped)` with
`stopped = len(gen) < RECALL_MAX_NEW_TOKENS` (`scripts/phase14_recall.py:793-808`). `draw_all` calls
the module global `_complete` both for the greedy draw and for each of the K-1 seeded draws
(:870-896), and `run_erasure_arm` imports `phase14_recall as recall` lazily (:2778). The patch
therefore reaches every draw. Record only `seconds`, `len(gen)` and `hit_cap = not stopped`. Never
record `gen`.

**D-18 stdout and log handling (what reaches `logs/phase36_probe.out`).** The plist's `StandardOutPath` IS the log. What each called pin prints:
- `phase19_erasure.run_erasure_arm` prints only two lines:
  - `[phase19_erasure] preflight: {summary}` (:~2804);
  - `[phase19_erasure] wrote {record_path} in {wall/60:.1f} min` (:2950).

  It prints no hit count. It does, however, (a) WRITE the full draws plus per-fact rates to
  `record_path` (:2947-2949) and (b) RETURN `payload` (:2951), which holds `per_fact` rows and
  exposure. The probe must:
  - read only timing from its own wrapper and its own `time.monotonic()` bracket;
  - never print or store `payload`;
  - delete the `data/probe36_*` record file once timing is extracted (D-01: text discarded).

  `phase14_recall.draw_all` prints nothing (:846-898).
- `teach_persona.score_arm` (used by the E3 T = 200 recall stage, D-19) DOES print readings:
  - `score_items` prints `"{label}: {total_k}/{total_n} = {rate}"` (`scripts/teach_persona.py:2429-2460`, the print at offset +28);
  - `score_arm` prints per-family gain (:2508-2512).

  To keep them out of the log, use the in-repo stdlib idiom `contextlib.redirect_stdout` into a
  discarded `io.StringIO` (`scripts/teach_persona.py:3025-3027`):
  ```python
      captured = io.StringIO()
      with contextlib.redirect_stdout(captured):
          ...
  ```
  Unlike that precedent, the probe must NOT re-print `captured.getvalue()`. Drop the buffer and keep
  only the elapsed seconds. Apply the same wrapper around any E5 clearance call
  (`phase14_factset_gate.probe_guessability`, :111, returns hits and prints nothing in :111-175)
  and around `run_erasure_arm` if the planner wants a belt-and-braces guarantee.
- Suggested test (Pitfall 8 + D-18): run the CPU live fixture under `capsys` and assert that no
  reading token (`/`, `rate`, `gain`, `per_fact`, `hits`) appears in the captured stdout from the
  scoring stages. The reading-key gate on the record JSON should be an AST/JSON key walk, not a grep.

**Write-once emit** (`scripts/phase31_probe.py:512-534`). Copy verbatim. The overwrite refusal runs
FIRST and the dirty refusal SECOND:
```python
def _emit_target(out_path):
    out_path = pathlib.Path(out_path)
    if not out_path.is_absolute():
        out_path = _GIT_ROOT / out_path
    _prove(not out_path.exists(),
           f"{out_path} exists — REFUSING to overwrite it. The probe record is write-once; "
           "corrections are dated continuations")
    pathspec = ("scripts", "src", "results")
    if out_path.is_relative_to(_GIT_ROOT):
        pathspec += (f":(exclude){out_path.relative_to(_GIT_ROOT).as_posix()}",)
    refuse_if_dirty(who="phase31_probe", detail=(...), pathspec=pathspec, cwd=_GIT_ROOT)
    return out_path
```

**Provenance block** (`scripts/phase31_probe.py:537-555`). This is the shape every probe record carries:
```python
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
    phase25_run.atomic_write_json(out_path, record)
```
Keep `provenance.run.started_utc` / `finished_utc`. They are the fields the ledger reads (D-11).
The "gates nothing" marker follows `:281-284` + `:306`:
`"sweep_point": False, "sweep_point_false_reason": ...`, plus `gates_nothing=True`. Phase 36 adds
nothing under `readings` (D-01). Phase 31 stored readings there; Phase 36 must not.

**WR-02 run-sha vs HEAD** (`scripts/phase32_points.py:340-376`, called at :398 BEFORE the write).
Phase 31 lacks it, so copy it from Phase 32:
```python
def record_session(key):
    """Append this session's ``{git_sha, started_utc}`` to the point's sessions sidecar."""
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=_CODE_ROOT, ...).stdout.strip()
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
            cwd=_CODE_ROOT, capture_output=True, text=True,
        )
        _prove(diff.returncode == 0, f"unknown sha {sha!r}: git diff failed ({diff.stderr.strip()})")
        changed = diff.stdout.split()
        _prove(not changed, f"pinned modules {changed} changed between session commit {sha} and HEAD (D-08, WR-02): ...")
```
Write order (`:379-399`): overwrite refusal → dirty refusal → `prove_pinned_unchanged([*shas, run_sha])` → `atomic_write_json`.

**Auto-commit of listed probe records (D-16).** If the plan lists the probe records for automatic
commit, copy `commit_path` (`scripts/phase32_points.py:408-450`). It does the following:
- proves the path is under `results/`;
- proves the branch is `main`;
- refuses a no-op;
- runs `git add -- <one path>` and `git commit -- <one path>`;
- proves `git show --name-only HEAD` == `[relative]`.

The AST bound on git actions is `ALLOWED_GIT_ACTIONS` / `READ_ONLY_GIT_ACTIONS` (:97-100).

**CLI** (`scripts/phase31_probe.py:915-942`):
```python
def build_parser():
    parser = argparse.ArgumentParser(description=...)
    sub = parser.add_subparsers(dest="mode", required=True)
    run = sub.add_parser("run", help=...)
    run.add_argument("--heartbeat", default=str(phase25_run.HEARTBEAT_PATH))
    emit = sub.add_parser("emit", help=...)
    emit.add_argument("target", choices=("point", "relearn"))
    return parser

def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.mode == "emit":
        ...
        return 0
    import phase25_venue  # torch-free; the banner lets the launch identity be read off the log
    print(phase25_venue.launch_banner(), flush=True)
    heartbeat = pathlib.Path(args.heartbeat)
    run_point_probe(heartbeat_path=heartbeat)
    run_relearn_probe(heartbeat_path=heartbeat)
    return 0
```

---

### `tests/test_phase36_probe.py`

**Analog:** `tests/test_phase31_probe.py`

- **Imports / autouse dirty-guard recorder** (:1-48):
  ```python
  @pytest.fixture(autouse=True)
  def clean_tree(monkeypatch):
      calls = []
      monkeypatch.setattr(probe, "refuse_if_dirty", lambda **kw: calls.append(kw) or "")
      return calls
  ```
- **Isolation, computed rather than listed** (:55-118). `test_isolation_paths_are_disjoint_from_every_phase32_key` derives the unprefixed outputs from `tp.arm_outputs` and asserts disjointness, then carries a non-vacuity leg (the real control collides with itself).
- **Stray guard** (:281-298). Copy with `*probe36*` globs. Also include the phase27 globs (`tests/test_phase27_relearn.py:809-823`), `*probe31*` and the phase32 globs (`tests/test_phase32_live.py:77-81`) as "must not match" checks:
  ```python
  _PROBE31_GLOBS = ("data/*probe31*", "data/probe31_relearn/*", "checkpoints/*probe31*",
                    "results/*probe31*", "results/phase31_probe_*")
  def _real_probe31_strays():
      return sorted({path.relative_to(_ROOT).as_posix() for pattern in _PROBE31_GLOBS for path in _ROOT.glob(pattern)})
  ```
- **CPU live-path fixture through the REAL stages** (:310-389). This is the "dry-run tests hide an
  unwired driver" remedy. Key moves:
  - `monkeypatch.setattr(phase25_run, "_DEVICE", "cpu")`;
  - `_e2e_env(root, monkeypatch)` from `test_phase22_wiring` (:715);
  - `export_slim`, then `phase14_recall.CONVBASE_SLIM` and `RECALL_MAX_NEW_TOKENS = 4`;
  - `phase19_erasure.RETENTION_BIN = tp.DIALOG_VAL_BIN` (the gitignored bin is absent on CI);
  - redirect `probe._ROOT` and `phase25_points._ROOT` to tmp;
  - spies that count calls and forward to the real function;
  - `strays_before == strays_after`;
  - `assert not any((root / "results").iterdir())`.

  Use one module-scoped fixture per front (`@pytest.fixture(scope="module")`, :386-389).
- **Live assertions** (:392-428): call counts == 1 per stage, real adapter sha, `reused` all False,
  last heartbeat line `stage == "done"`.
- **Refusals on light env** (:431-462): `_light_env` patches `train_stage` to `pytest.fail("trained past a refusal")`.
- **Emit write-once / dirty-first** (:465-502). In `test_emit_point_refuses_a_dirty_tree_before_reading_sidecars`, assert the exact pathspec `("scripts", "src", "results", f":(exclude){rel}")`, and that the missing sidecar is the next refusal.
- **WR-02 tests** (`tests/test_phase32_points.py:355-367`). Three tests: HEAD passes, a natural RED on the pre-fix commit of a pinned module, and an unknown sha refuses:
  ```python
  def test_wr02_natural_red_on_the_pre_fix_commit():
      with pytest.raises(SystemExit, match="D-08") as refused:
          p32.prove_pinned_unchanged([_head(), _pre_fix_sha()])
      assert "scripts/phase30_points.py" in str(refused.value)
  ```
  `_pre_fix_sha` (:325-338) = parent of the newest commit touching a pinned module.
- **Torch-free import** (:263-275): a subprocess that imports the module, runs a pure builder, then `print('torch' in sys.modules)`.
- **main() dispatch with signature binding** (:931-978). `_recorders` binds the kwargs that `main()` passes against the REAL function signature (`inspect.signature(...).bind`). This is the "trace main() → run() kwargs" check.

---

### `artifacts/com.personacore.phase36.probe.plist`

**Analog:** `artifacts/com.personacore.phase31.probe.plist` (whole file, 61 lines). Copy it and change only the following:
- `Label` → `com.personacore.phase36.probe` (:17);
- `ProgramArguments[3]` → `.../scripts/phase36_probe.py` (:33);
- `StandardOutPath` / `StandardErrorPath` → `logs/phase36_probe.{out,err}` (:43-45).

Keep these as they are:
- `caffeinate -dims` + `.venv/bin/python` (:30-32);
- `run --heartbeat .../data/phase25_heartbeat.jsonl` (:34-36). If the ledger wants its own beats file, change the path here AND in the test;
- `KeepAlive false`, `RunAtLoad false` (:22-26);
- `ProcessType Interactive`;
- `EnvironmentVariables`: `PERSONACORE_SWEEP_ACTIVE=1`, `PATH`, `PYTHONUNBUFFERED=1` (:50-59).

**Test:** `tests/test_phase31_probe.py:981-1002` (`test_plist_mirrors_the_canary_agent`). It loads
both plists with `plistlib`, compares `ProgramArguments[:3]`, compares the heartbeat by path suffix
(host-independent, R-2), requires a `/logs/` substring with different paths, and requires equal
`EnvironmentVariables` / `ProcessType`. Mirror it against the phase31 or phase26 canary plist.

---

### `scripts/phase36_budget.py` (pure derivation, 25% comparisons, cut table, write-once emit)

**Analog:** `scripts/phase31_budget.py`

- **Module docstring + imports** (:1-37). Torch-free at import AND at derive. Use
  `INSTRUMENT_GIT_SHA = git_sha()`.
- **Constants derived from the prereg, never typed** (:41-46):
  ```python
  STOP_LINE_FACTOR = 1.5
  BUDGET_RECORD = next(p for p in phase29_prereg.V5_RESULT_PATHS if p.startswith("results/phase31_budget"))
  ```
  Phase 36 reads 1.5, 25%, the E4 points and S ≥ 3 from `phase36_prereg.ENTRIES[...]["value"]` and
  90 from `phase35_prereg.ENTRIES["mps_ceiling_hours"]["value"]`.
- **`FORMULA` dict recorded in the output** (:68-107). Every stated formula and every "not
  re-measured" note goes here: E4 canary from `phase26_canary_sources.json` (D-19), E1 ordering from
  `phase19_collateral_curve.json` (Q5), and E2 full-adapter scaling.
- **`_range` / `_hours` helpers** (:120-126):
  ```python
  def _hours(block):
      return {k: v / 3600 for k, v in block.items()}
  def _range(estimate, low, high):
      block = {"estimate": estimate, "low": low, "high": high}
      return dict(block, hours=_hours(block))
  ```
  The CONTRACT values (`front_hours`, `total_hours`) must stay unrounded floats. `_budget_record`
  checks `total_hours == math.fsum(front_hours.values())` with exact equality (RESEARCH §contract).
- **`derive(...)` pure, keyword-only, `_prove` on every invariant** (:129-316).
- **`build_record(tracked)` recomputes from COMMITTED blobs and records the sha256 of every source** (:334-369):
  ```python
      point = phase30_points._tracked_json(phase31_probe.POINT_RECORD, tracked, "the ARCAL-01 point probe")
      ...
      # _tracked_json proved each working file == its HEAD blob, so these are the committed bytes.
      record["sources"] = {rel: _sha256(_GIT_ROOT / rel) for rel in read}
  ```
- **"Precedes" refusal** (:324-331, `require_no_sweep_point`). Use it as the template for "refuse
  once any `results/phase3[7-9]_*`/`phase4[0-3]_*` MPS record is tracked".
- **Write-once emit** (:372-409). The order is overwrite refusal → dirty refusal (with
  `:(exclude)<out>`) → precede-refusal → build → provenance (`module_sha256`, `git_sha`,
  `head_at_write`, `written_utc`) → `phase25_run.atomic_write_json`.
- **CLI without arguments** (:412-416).
- **HALT branch (Pitfall 14 + leg (c)).** The cut table must never be written under `results/phase36_*`.
  Return it as a value or print it, or write it under `.planning/phases/36-…/`. The emit for
  `results/phase36_budget.json` must import the fill file's `V6_BUDGET_AND_STOP_LINE`. It must not
  call `fill` itself: the census allows exactly one `fill` site, in `scripts/phase36_*prereg.py`.
- **Census constraint.** This module must not match `*prereg.py`. It must not touch
  `phase35_prereg._*` and must not hold the literal string `"phase35_prereg"`. Re-prove the four
  contract fields locally rather than calling `_budget_record` / `_prove_budget`.

---

### `scripts/phase36_budget_prereg.py` (the ONE `fill` site)

**Analog:** the planted green sequence in `tests/test_phase35_prereg.py:2573-2589`:
```python
def _fill_file(path, *slots):
    lines = "".join(f'{s.upper()} = phase35_prereg.fill("{s}")\n' for s in slots)
    return (path, "import phase35_prereg\n" + lines)
...
        "g36": [
            [_record("phase36_probe_a.json")],
            [_fill_file("scripts/phase36_prereg.py", "v6_budget_and_stop_line")],
            [_record("phase36_budget.json")],
        ],
```
The census rules it must satisfy are in `tests/test_phase35_prereg.py:2166-2269`:
- a plain `import phase35_prereg` (no alias);
- exactly one module-level single-target `V6_BUDGET_AND_STOP_LINE = phase35_prereg.fill("v6_budget_and_stop_line", ...)`, where the call is the whole value;
- the slot argument is a string constant;
- no private access.

`fill` runs `_consume_inputs`, which requires every `input_records` path to appear inside
`derivation["source"]` (RESEARCH §contract), so build `source` with `" ".join(paths)`. The ordering
legs: the file's FIRST commit follows every probe record (b), and EVERY commit precedes
`results/phase36_budget.json` (a). Once committed, it is frozen.

---

### `tests/test_phase36_budget.py`

**Analog:** `tests/test_phase31_budget.py`

- **Torch-free derive in a subprocess** (:213-230).
- **Consumer fed the real producer record** (:233-258). This test takes the module-scoped live
  fixtures from the probe test (`from test_phase31_probe import (...)`, :31). It binds `derive`'s
  parameters via `inspect.signature`, and makes any documented substitution explicit in a comment.
  For Phase 36, extend it so the derived values pass `phase35_prereg.fill("v6_budget_and_stop_line", ...)`
  with `phase35_prereg._REPO_ROOT` monkeypatched to tmp (tests may touch privates), and so the
  emitted budget then passes `fill("e2_S")` and `fill("e1_checkpoint_grid")`.
- **AST "never calls torch-touching helpers"** (:261-276), with a meta-guard: `len(calls) > 1, "the walk saw no calls: the guard is blind"`.
- **Autouse dirty-guard recorder + `_is_tracked`** (:289-297).
- **Recompute, with an honest branch when untracked** (:378-403). If the budget is tracked, compare
  `_strip(rebuilt) == _strip(committed)`. Otherwise run a forged-tracked determinism check that
  monkeypatches `pts._tracked_json`.
- **Ancestry with natural RED** (:406-428):
  ```python
  def test_ancestry_budget_precedes_every_sweep_point():
      points = sorted(_git("ls-files", phase29_prereg.POINT_RECORD_PREFIX + "*.json").split())
      if not _is_tracked(BUDGET):
          assert points == [], f"sweep point(s) {points} committed before the ARCAL-03 budget"
          return
      _assert_frozen_before(BUDGET, points)
      with pytest.raises(subprocess.CalledProcessError):
          _assert_frozen_before(BUDGET, [pts.CALIBRATION_PATH])
  ```
- **HALT / cut-table legs.** Plant Σ > 90. Assert the following:
  - `fill` raises a SystemExit containing "HALT";
  - the D-15 row order holds;
  - no S < 3 row appears;
  - nothing is created under `results/phase36_*` (compare a glob before and after).

---

### `scripts/phase36_ledger.py` (D-11..D-13)

**Analogs:**
1. `scripts/phase32_points.py:291-326`: the clock over COMMITTED records and the stop line read
   from the committed budget, never retyped:
   ```python
   def cumulative_seconds(tracked):
       """Sum of ``stages.*.seconds`` over the COMMITTED point records. PREREG-03 records count 0."""
       total = 0.0
       for key in phase29_prereg.POINT_KEYS():
           rel = phase29_prereg.point_record_path(key)
           if rel not in tracked:
               continue
           record = phase30_points._tracked_json(rel, tracked, "the point record")
           ...
           total += sum(float(stage["seconds"]) for stage in record["stages"].values())
       return total

   def stop_line_seconds(tracked):
       """The ARCAL-03 stop line: read from the committed budget, never retyped (Phase 31 D-08)."""
       value = phase30_points._tracked_json(BUDGET_PATH, tracked, "the ARCAL-03 budget")["stop_line"]["seconds"]
       _prove(isinstance(value, float) and math.isfinite(value) and value > 0, ...)
   ```
   The refusal-at-line pattern in `run` is `scripts/phase32_points.py:717-727` and :733-750. The
   stop-line beat uses `stage="stop_line"`; `beat` does not validate the stage name.
2. `scripts/phase25_watch.py:274-318` (`read_last_beat`). Walk backwards, skip torn lines
   (`except ValueError: continue`), require a `dict` with `"utc"`, and return `None` when the file is
   absent or empty. The ledger needs the per-run variant: group by `point`, keep the first `start`
   and the last complete beat, with the same torn-tail rule.
3. `scripts/phase25_run.py:298-368`. `beat()` appends one `json.dumps(line, sort_keys=True)` line
   with `HEARTBEAT_FIELDS = ("utc","point","stage","shape","draw_index")` (:291).
   `start_heartbeat` is a daemon thread on `phase25_watch.HEARTBEAT_SECONDS` = 60
   (`scripts/phase25_watch.py:56`).

Refusals are `SystemExit` with a message for Rafael's checkpoint, never `assert` (all `_prove` analogs).
Never read `results/*/run.csv`'s `wall_clock` column: it holds the step number
(`src/personacore/training/loop.py:915`).

---

### `tests/test_phase36_ledger.py`

**Analogs:**
- `tests/test_phase25_watch.py:161-200`: torn tail, empty file, absent file.
  ```python
      heartbeat.write_text(complete + "\n" + _beat(draw_index=12)[:37], encoding="utf-8")
      beat = phase25_watch.read_last_beat(heartbeat)
      assert beat == json.loads(complete)
  ```
- `tests/test_phase32_points.py:341-353` (`test_record_session_appends`): append-only, with the on-disk content equal to the return value.
- Add a negative test proving the ledger never reads `run.csv` (Pitfall 7). An AST gate is better than a grep (memory: grep criteria measure prose).

---

### `scripts/phase36_caps.py` (D-09 unit caps, imported by owner fill files)

**Analog:** `scripts/phase30_points.py:190-203` (`_tracked_json`). Read the COMMITTED blob, and
refuse when the file is untracked or when the working tree differs from HEAD:
```python
def _tracked_json(rel, tracked, what):
    _prove(rel in set(tracked), f"{what} {rel} is not TRACKED (git ls-files). ...")
    # CR-01: the COMMITTED blob is what is read; a tracked file edited on disk is refused.
    shown = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=_ROOT, capture_output=True)
    _prove(shown.returncode == 0, f"{what} {rel} has no committed blob at HEAD")
    _prove(shown.stdout == (_ROOT / rel).read_bytes(), f"{what} {rel} differs from its committed blob: ...")
    return json.loads(shown.stdout.decode("utf-8"))
```
Call `phase30_points._tracked_json` directly, as `phase31_budget` does. It is not a `phase35_prereg`
private. Re-prove the four contract fields and `total_hours == math.fsum(front_hours.values())`
locally. The module must stay torch-free, must not match `*prereg.py`, and must not call `fill`.

---

### `tests/test_phase36_caps.py`

**Analogs (owner-file scan + planted repo):**
- `tests/test_phase35_prereg.py:2120-2128` (`_fill_calls`) and `:2463-2472` (`_fill_sites`):
  ```python
  def _fill_sites(run):
      sites = {}
      for path in run("ls-files", "scripts").stdout.split():
          if _is_fill_file(path):
              source = run("show", f"HEAD:{path}").stdout
              slots = frozenset(s for s, _ in _fill_calls(source) if s in phase35_prereg.SLOTS)
              if slots:
                  sites[path] = slots
      return sites
  ```
  The scan is honest-green at zero owner files. Filter on the capped slots
  (`e1_checkpoint_grid`, `e3_grid_subset`, `e5_set_sizes`, `e6_entry_subset`).
- `tests/test_phase35_prereg.py:76-107` (`_git_in`, `_planted_repo`): a throwaway repo, one commit per element. Use it for the RED leg with a planted over-cap owner file.
- `tests/test_phase35_prereg.py:2557-2561`: honest green on the real repo, with the comment "0 today is honest-green".

---

### `tests/test_phase23_resume.py` (MODIFY: register the new `train_arm(` site)

**Analog:** its own register, `_TRAIN_ARM_CALL_SITES` (:60-161). Add one tuple per raw grep hit of
`train_arm(` in the new files:
```python
    ("scripts/phase36_probe.py", "call", "<the E2 probe function name>"),
```
Also count every docstring, comment or test string that contains `train_arm(` as `"prose"`
(:255-292). The grep is `grep -rn "train_arm(" --include=*.py scripts tests`.

**Second edit that the register line alone does NOT cover.** The call-count tripwire is a literal sum
that must be bumped, together with its comment ledger and assertion message (:296-332):
```python
    assert (
        sum(1 for path, kind, _s in _TRAIN_ARM_CALL_SITES if kind == "call" and path != _THIS_FILE)
        == 8 + 1 + 1 + 1 + 1 + 2 + 1 + 1 + 1
    ), ("the register no longer holds ... plus 30-01's seam probe")
```
A new `"call"` entry means `... + 1` plus a sentence naming 36's E2 probe. The per-file AST check
(:333+) also counts real `ast.Call` nodes per file. `_RESUME_PASSERS` must not change: the probe
passes no `resume_from`. Never pass arm `"real"`: `arm_outputs("real")` resolves to
`checkpoints/persona_adapter.pt` (`scripts/teach_persona.py:382-386`).

---

## Shared Patterns

### Invariant refusal (all scripts)
**Source:** `scripts/phase31_probe.py:100-103` (identical in every v5/v6 module)
```python
def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase31_probe] {message}")
```

### Atomic JSON write
**Source:** `scripts/phase25_run.py:118` `atomic_write_json(path, blob)`.
**Apply to:** every sidecar and record. `os.replace` is census-restricted to
`phase25_run.py`/`phase25_record.py` (Pitfall 11).

### Dirty-tree refusal
**Source:** `src/personacore/provenance.py:47` `refuse_if_dirty(*, who, detail, pathspec=(), cwd=None)`.
It raises `SystemExit("[who] REFUSING: the working tree is dirty...")`.
**Apply to:** the run start (pathspec `("scripts","src","results")`) and every emit (the same plus
`:(exclude)<out>`). Tests replace it with a recorder (the autouse `clean_tree` fixture).

### Committed-blob reads
**Source:** `scripts/phase30_points.py:190-203` `_tracked_json`.
**Apply to:** the budget builder, the ledger and the caps. Never read a working-tree record.

### Ancestry guard
**Source:** `tests/test_phase29_prereg.py:69-106` `_assert_frozen_before` (+ `_git` :52-56).
**Apply to:** prereg ≺ every `results/phase36_*`; probes ≺ budget; budget ≺ every later v6 MPS
record. Use honest branches when nothing is tracked, plus a natural-RED non-vacuity leg.

### Runtime wrap-and-restore of a pin's function (no file edit)
**Source:** `scripts/phase31_probe.py:388-402` (`tp.train` wrapped, restored in `finally`).
**Apply to:** `phase14_recall._complete` (D-18 per-draw timer), `tp.MAX_STEPS` (T = 800), and
stdout silencing via `contextlib.redirect_stdout(io.StringIO())` (`scripts/teach_persona.py:3025-3027`).

### Torch-free-at-import proof
**Source:** `tests/test_phase35_prereg.py:392-410`; `tests/test_phase31_probe.py:263-275`.
**Apply to:** `phase36_prereg`, `phase36_budget`, `phase36_ledger`, `phase36_caps`,
`phase36_budget_prereg`, and `phase36_probe` at import.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| Committed compact launch ledger (Q3: start/end line per run, path outside `results/`) | data file | append-only, committed | Every existing heartbeat/beat file lives in gitignored `data/` (`scripts/phase25_run.py:287`). No committed append-only ledger exists. Before choosing a path, the planner must confirm that it trips neither `refuse_if_dirty(("scripts","src","results"))` nor any of the clean-tree probes. `artifacts/` and `.planning/` are outside that pathspec. |
| `scripts/phase36_budget_prereg.py` (partial) | owner fill file | transform | No real `phase35_prereg.fill(` site exists outside the prereg. The only template is the planted `_fill_file` string in the test plus RESEARCH's code example. |

## Metadata

**Analog search scope:** `scripts/phase{19,23,25,29,30,31,32,35}_*.py`, `scripts/erasure_kstar_run.py`,
`scripts/phase14_recall.py`, `scripts/teach_persona.py`, `src/personacore/provenance.py`,
`tests/test_phase{23,25,29,31,32,35}_*.py`, `artifacts/*.plist`, `.gitignore`.
**Files scanned:** ~25.
**Pattern extraction date:** 2026-10-02.
