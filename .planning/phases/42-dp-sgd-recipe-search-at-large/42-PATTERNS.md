# Phase 42: DP-SGD Recipe Search at Large ε - Pattern Map

**Mapped:** 2026-10-13
**Files analyzed:** 8 new/modified
**Analogs found:** 8 / 8 (every file has an in-repo analog; none needs a RESEARCH-only pattern)

All names below were read from the module that owns them on 2026-10-13 (HEAD d167ed1). No
`scripts/phase42_*`, `tests/test_phase42_*` or `results/phase42_*` exists yet (`ls scripts tests | grep
phase42` → empty).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/phase42_prereg.py` | config (prereg, fill file 1) | transform (pure rules, import-time fill) | `scripts/phase41_prereg.py` | exact |
| `scripts/phase42_threshold_prereg.py` | config (fill file 2) | transform (reads committed in-phase records) | `scripts/phase41_floors_prereg.py` | exact |
| `scripts/phase42_recipes.py` | driver (preflight / run / emit / report) | batch (MPS training + scoring), file-I/O | `scripts/phase41_erasure.py` (CLI, ledger, write-once, emit, report) + `scripts/phase36_probe.py:875-948` (`stage_e3`: tp-global rebind around `train_stage`, `score_arm`) | exact (composite) |
| `tests/test_phase42_prereg.py` | test (ancestry + pure rules + censuses) | — | `tests/test_phase41_prereg.py` | exact |
| `tests/test_phase42_threshold_prereg.py` | test (fill-file ancestry + values) | — | `tests/test_phase41_floors_prereg.py` | exact |
| `tests/test_phase42_recipes.py` | test (driver, faked trainer/scorer, tmp ledger) | — | `tests/test_phase36_probe.py:1838-1905` (`_e3_light`) + `tests/test_phase41_erasure.py:30-112, 1370-1477` (rig, `_real_tree_untouched`) | exact (composite) |
| `.gitignore` (2 lines) | config | — | `.gitignore:18-20` (Phase 41 calibration csv dir) | exact |
| report writer | part of driver (`report`, `render_report`) | file-I/O | `scripts/phase41_erasure.py:2938-2957` | exact |

The report writer is a function in the driver, not a separate module (Phase 41 precedent). The
aggregate record (`results/phase42_recipes.json`) is the driver's `emit`.

---

## Pattern Assignments

### `scripts/phase42_prereg.py` (fill file 1: grid fill + every rule, path, label, prediction)

**Analog:** `scripts/phase41_prereg.py` (2197 lines). Layout to copy, section by section.

**Header + sys.path + imports** (lines 28-51):
```python
import collections
import collections.abc
import fnmatch
import fractions
import json
import math
import pathlib
import re
import sys
import types

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_SRC = str(_REPO_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import erasure_gate  # noqa: E402  (needs the sys.path insert above; torch-free)
import phase35_prereg  # noqa: E402  (same)
import phase36_caps  # noqa: E402  (same; torch-free)
```
Phase 42 swaps `erasure_gate` for nothing (or `phase36_prereg` for `ENTRIES["e3_max_steps"]`).
Census #7 (`tests/test_phase35_prereg.py` L2166-2269): `import phase35_prereg` plainly, no alias,
and no `phase35_prereg._*` private access anywhere in the file.

**Date + certified property** (lines 57-65):
```python
# At this commit no `results/phase41_*` file existed, tracked or untracked.
COMMITTED = "2026-10-08"
RECORDS_AT_COMMIT = 0


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase41_prereg] {message}")
```

**Entry schema by reference + `_prove_count` / `_prove_entry` / `_read`** (lines 72-120): copy
verbatim, renaming the `[phase41_prereg]` tag. `_prove_entry` refuses `proposer` / `adopted_by`
and requires exactly `ENTRY_FIELDS` (= `phase35_prereg.ENTRY_FIELDS`).

**Record paths selected by EQUALITY from the registry** (lines 128-139):
```python
RECORD_GLOB = next(p for p in phase35_prereg.V6_RESULT_PATHS if p == "results/phase41_*")
CALIBRATION_GLOB = next(
    p for p in phase35_prereg.V6_RESULT_PATHS if p == "results/phase41_calibration_*.json"
)
BUDGET_RECORD = phase35_prereg.SLOTS["e1_checkpoint_grid"]["input_records"][0]
ERASURE_RECORD = RECORD_GLOB.replace("*", "erasure.json")
REPORT_RECORD = RECORD_GLOB.replace("*", "erasure_report.md")
```
Resolved Phase 42 equivalents (read from `scripts/phase35_prereg.py`):
- `"results/phase42_control_*.json"` and `"results/phase42_*"` are both in `V6_RESULT_PATHS` (L327-328).
- `phase35_prereg.SLOTS["e3_grid_subset"]["input_records"]` = `(_BUDGET_RECORD, _V4_CONTROL_RECORD)` (L1818-1822):
  `[0]` = budget (`results/phase36_budget.json`), `[1]` = v4.0 control
  (`results/phase25_point_dp_n8_sigma0p000000.json`).
- `phase35_prereg.SLOTS["e3_recall_threshold"]["input_records"]` =
  `("results/phase42_control_*.json", _V4_CONTROL_RECORD)` (L1838-1842).
- Constants to read, never type: `phase35_prereg.E3_SIGMAS` (L496, `(0.0, 0.5, 1.0)`), `E3_N` (L781),
  `E3_UNIT` (L786), `STEP_BUDGET` (L346), `F_Y` (L342), `DELTA` (L201), `CURVE_TOTAL` (L199),
  `SELECTION_ACCOUNTED` (L200), `seed_list()` (L357), `p22_onset_sigma(steps)` (L1028),
  `owner_prereg_glob(slot)` (L847); `phase36_prereg.ENTRIES["e3_max_steps"]["value"]` (800).

**Path builders with unit guard** (lines 152-189). Copy `_prove_path(path, glob, *, unit=False)`:
the per-cell record must match `RECORD_GLOB` and must NOT match the control glob (RESEARCH
Pitfall 10: a noised record named `phase42_control_*` is exempted from leg (a)).
```python
def _prove_path(path, glob, *, unit=False):
    """``path`` matches ``glob``; a per-cell record also matches neither prep glob."""
    _prove(fnmatch.fnmatch(path, glob), f"{path} does not match {glob}")
    if unit:
        for prep in (CALIBRATION_GLOB, BAND_GLOB):
            _prove(not fnmatch.fnmatch(path, prep), f"{path} would read as a prep record {prep}")
    return path


def cell_record(target, ordering, seed):
    """The record of one cell (target, ordering, seed) (D-15)."""
    _prove_unit(target=target, ordering=ordering, seed=seed)
    path = RECORD_GLOB.replace("*", f"cell_{target}_{ordering}_seed{seed}.json")
    return _prove_path(path, RECORD_GLOB, unit=True)


def run_id(unit):
    """The ledger run id of one Phase 41 unit (a prep unit or a cell) on front E1."""
    import phase36_ledger  # torch-free; lazy so the import surface stays small

    return phase36_ledger.run_id(41, "E1", unit)
```
Phase 42: `control_record(recipe)` → `CONTROL_GLOB.replace("*", ...)`; `point_record(recipe, sigma)` →
`RECORD_GLOB.replace("*", "point_...")` with `unit=True`; `E3_RECORD` / `REPORT_RECORD` as
`RECORD_GLOB.replace("*", "recipes.json")` / `"recipes_report.md"`; `run_id(unit)` →
`phase36_ledger.run_id(42, "E3", unit)` (`scripts/phase36_ledger.py:76-78`).

**ENTRIES dict + frozen proxy + exact-name census** (lines 245-249, 290-318, 877-931):
```python
_CONTEXT = "41-CONTEXT D-{} (447747c)"
_DEFAULT = "default taken at plan time, not yet confirmed by Rafael"
_CONFIRMED = "confirmed by Rafael 2026-10-08"

_ENTRIES = {
    "e1_checkpoint_grid": {
        "value": GRID,
        "derivation": ("ERASE-07, D-07: ..."),
        "kind": "preference",
        "source": (f"{_CONTEXT.format('07, D-08, D-09')}; ...; {BUDGET_RECORD} front_hours.E1, unit_caps.E1"),
    },
    ...
}

ENTRIES = types.MappingProxyType(
    {name: types.MappingProxyType(entry) for name, entry in _ENTRIES.items()}
)

_ENTRY_NAMES = frozenset({...})


def _prove_entries():
    """Every entry proved, and the entry set exactly the pre-registered names."""
    for name, entry in ENTRIES.items():
        _prove_entry(name, entry)
    _prove(set(ENTRIES) == _ENTRY_NAMES, f"entries {sorted(set(ENTRIES) ^ _ENTRY_NAMES)} are missing or extra")


_prove_entries()
```
Phase 42 note: `ENTRIES["e3_grid_subset"]["value"]` must equal `RECIPES` (`_consume_inputs` →
`_prove_derivation_value`, `phase35_prereg.py:910-917`) and its `source` must contain BOTH input
paths (`phase35_prereg.py:940`). Build each recipe as `types.MappingProxyType({...})`, not a dict:
`tests/test_phase41_prereg.py:299-306` `_no_mutable_containers` reds on a dict inside an entry
value; `_rule_e3_grid_subset` accepts any `collections.abc.Mapping` (`phase35_prereg.py:1438-1441`).

**Predictions entry** (lines 649-690): each prediction text carries "descriptive" and
"a mismatch is a finding, not a failure"; any read value (D-16's 0/1008, 0/648 from
`results/phase25_recall.json`) is read at import by `_read(...)`, as `D11_REFERENCE_SHA256` is at
lines 254-256:
```python
D11_REFERENCE_RECORD = "results/phase19_calibration_curve.json"
D11_REFERENCE_KEY = "adapter_in_sha256"
D11_REFERENCE_SHA256 = _read(D11_REFERENCE_RECORD)[D11_REFERENCE_KEY]
```

**The slot fill, whole module-level binding** (lines 938-943) and caps at import (lines 988-991):
```python
E1_CHECKPOINT_GRID = phase35_prereg.fill(
    "e1_checkpoint_grid",
    checkpoints=GRID,
    input_records=(BUDGET_RECORD,),
    derivation=ENTRIES["e1_checkpoint_grid"],
)
...
phase36_caps.check_unit_caps(
    "E1", **phase36_caps.counts_for("e1_checkpoint_grid", E1_CHECKPOINT_GRID)
)
```
Phase 42 form (RESEARCH Code Example 1, measured to run in 1.0 s):
`E3_GRID_SUBSET = phase35_prereg.fill("e3_grid_subset", recipes=RECIPES, seed=phase35_prereg.seed_list()[0], input_records=(BUDGET_RECORD, V4_CONTROL_RECORD), derivation=ENTRIES["e3_grid_subset"])`,
then `check_unit_caps("E3", **counts_for("e3_grid_subset", E3_GRID_SUBSET))` and
`check_unit_caps("E3", sigmas=len(phase35_prereg.E3_SIGMAS))`. The binding name must be
`E3_GRID_SUBSET` (`slot.upper()`, read by `tests/test_phase36_caps.py:272-283` `_owner_values`).

**Fill-input builder for file 2** (lines 1266-1288), copy the shape exactly:
```python
def floors_fill_inputs():
    """... A fresh object each call, so the floors fill file and the CPU rehearsal pass identical,
    unshared arguments."""
    keys = tuple((t, o, s) for t in TARGETS for o in ORDERINGS for s in SEEDS)
    input_records = tuple(calibration_record(o, s) for s in SEEDS for o in ORDERINGS) + (
        CALIBRATION_CORPUS,
    )
    derivation = {
        "value": keys,
        "derivation": ("ERASE-06 / D-10 / D-03: ..."),
        "kind": "derived",
        "source": f"{_CONTEXT.format('10, D-12')}; " + " ".join(input_records),
    }
    _prove_entry("floors_fill_inputs", derivation)
    return {"floors": dict.fromkeys(keys), "input_records": input_records, "derivation": derivation}
```
Phase 42 `threshold_fill_inputs()` returns `{"grid": E3_GRID_SUBSET, "input_records": (V4_CONTROL_RECORD, *3 control_record(...)), "derivation": {...value = tuple of (lr, steps, batch, seed) keys...}}`
(`_rule_e3_recall_threshold` signature `(*, grid, input_records, derivation)`, `phase35_prereg.py:1525`;
`grid` must be the SAME object, identity via `_is_filled`, L1534-1537).

**Label / summary pure functions** (lines 1218-1263): `pair_label` and `summary_counts` are the
model for the 4×2 `passa / não passa / REFUSED` labeller and the "k de 8 pontos passam; m REFUSED"
summary; `not_reached_sentence` (L1258-1263) is the model for the D-15 null first line built from
read constants (`len` of the noised cells), not a typed "8".
```python
def pair_label(verdicts):
    _prove(set(verdicts) == set(SEEDS), f"pair seeds {sorted(verdicts)} are not {SEEDS}")
    ...
    return {"label": label, "text": ", ".join(f"{verdicts[s]} na {s}" for s in SEEDS)}
```
Exact comparison: `exact_margin` / `exact_rate` (lines 950-979) are the `fractions.Fraction`
precedent for RESEARCH Pitfall 6 (fill float vs 7/10 rational).

**Edit window:** every pure function (labels, summary, D-15 line, predictions, unit order, warmup
rule `T // 10`, rehearsal/launch rules, report readings) lands here BEFORE the first control
record; afterward the file is closed (leg (a); memory "pin corrections are dated continuations").

---

### `scripts/phase42_threshold_prereg.py` (fill file 2: `e3_recall_threshold` only)

**Analog:** `scripts/phase41_floors_prereg.py` (whole file, 34 lines). Copy it, keeping its import
set exactly `{pathlib, sys, phase35_prereg, phase42_prereg}`:
```python
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:] = [
    p for p in (str(_ROOT / "scripts"), str(_ROOT / "src")) if p not in sys.path
] + sys.path

import phase35_prereg  # noqa: E402  (needs the sys.path insert above)
import phase41_prereg  # noqa: E402  (same)

E1_CONDITION_A_FLOORS = phase35_prereg.fill(
    "e1_condition_a_floors", **phase41_prereg.floors_fill_inputs()
)
```
Phase 42: `E3_RECALL_THRESHOLD = phase35_prereg.fill("e3_recall_threshold", **phase42_prereg.threshold_fill_inputs())`.
No numeric literal anywhere in the file (`tests/test_phase41_floors_prereg.py:285-295` checks this).
Must NOT be named `phase42_floors_prereg.py` (`tests/test_phase41_floors_prereg.py:349` uses that
name as a misplaced-fill non-vacuity plant). Planted green case `g42` in
`tests/test_phase35_prereg.py:2597-2602` fixes the order: grid file → control → threshold file → point.

---

### `scripts/phase42_recipes.py` (driver: `preflight` / `run` / `emit` / `report`)

**Analog A:** `scripts/phase41_erasure.py` for the CLI, launch gates, ledger, write-once, emit, report.
**Analog B:** `scripts/phase36_probe.py:858-948` for the DP training seam (the only `tp.MAX_STEPS`
rebinding in the repo) and `score_arm` timing.

**Docstring + torch-free import surface** (`phase41_erasure.py:1-44`):
```python
"""Phase 41 E1 (ERASE-03..ERASE-10) — erasure across facts, orderings and seeds.

    .venv/bin/python scripts/phase41_erasure.py preflight   # the launch checks, writes nothing
    .venv/bin/python scripts/phase41_erasure.py run         # pending prep units, then the cells
    .venv/bin/python scripts/phase41_erasure.py emit        # CPU: the erasure record
    .venv/bin/python scripts/phase41_erasure.py report      # the markdown from the erasure record
...
Torch-free at import only: every torch-importing module and the pre-registration are imported
inside the functions that need them.
"""
...
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import phase25_run  # noqa: E402  — atomic_write_json, beat, start_heartbeat (torch-free)
import phase36_caps  # noqa: E402  (torch-free at import; the launch caps)
import phase36_ledger  # noqa: E402  (torch-free; the per-unit attempt)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402
```

**Module constants** (`phase41_erasure.py:46-90`): `_REPO`, `_ROOT`, `FRONT`, `LAUNCH_PATHSPEC`,
`PREREG_FILE`, `DRIVER_FILE`, `FLOORS_FILE` (→ `THRESHOLD_FILE`), `MODULES` (sha-pinned modules: add
`scripts/phase25_points.py`, `scripts/phase25_condition_c.py`, `scripts/phase25_epsilon.py`,
`scripts/phase25_recall.py`, `scripts/teach_persona.py`, `scripts/phase35_prereg.py`,
`scripts/phase36_ledger.py`, `scripts/phase36_caps.py`, `scripts/phase25_run.py`,
`scripts/phase14_recall.py`, `scripts/phase29_prereg.py`), `RUN_PROVENANCE_KEYS`,
`REHEARSAL_PREFIX = "phase41rh"` with the comment "Does not match results/phase41_*".
Phase 42 prefixes (RESEARCH Item 7): real `phase42e3_<cell>`, rehearsal `phase42rh_<cell>`;
never `phase25_` nor `phase42_`.

**Small helpers to copy verbatim** (`phase41_erasure.py:93-108, 133-191`): `_prove`, `_sha256`,
`_now`, `_rel`, `module_sha256`, `_import_modules` (119-131), `_is_real`, `_root_ledger`
(rehearsal must use its own ledger/heartbeat), `_prereg` (lazy import), `_device`, `_release`, and:
```python
def _write_once(path, blob):
    path = pathlib.Path(path)
    _prove(not path.exists(), f"{path} exists: write-once")
    path.parent.mkdir(parents=True, exist_ok=True)
    phase25_run.atomic_write_json(path, blob)
```
Census #2: never `os.replace` in this file; `atomic_write_json` is the writer.

**Stage gating** (`phase41_erasure.py:1061-1086`, `_tracked_and_clean`, `_stage1_records`) and
preflight's stage switch (lines 1430-1447):
```python
        if real and not _tracked_and_clean(FLOORS_FILE, *_stage1_records()):
            print(STAGE_1_DONE, flush=True)
            return {"stage": STAGE_1_DONE, "pending": ()}
        stage = 2
```
Phase 42: stage 2 starts only when `THRESHOLD_FILE` and the 3 control records are tracked and clean.
Stage 2 re-asserts P22 before training (`phase36_probe.py:883`:
`phase36_prereg.prove_p22(phase36_prereg.ENTRIES["e3_max_steps"]["value"])`, or the
`p22_onset_sigma` loop against `E3_GRID_SUBSET["p22_onset_sigma"]`). REFUSED recipes stay in the
stage-2 order (D-20; RESEARCH Pitfall 7): labels are applied in `emit`, never at launch.

**Preflight** (`phase41_erasure.py:1390-1530`): device rule (MPS on real root, CPU on rehearsal),
`git_sha()`, `_import_modules()` then `module_sha256()`, open-run refusal over
`phase36_ledger.open_runs(read_ledger(...))`, `refuse_if_dirty(..., pathspec=..., cwd=_REPO)`,
stale-output refusal, then:
```python
    gate = phase36_ledger.require_launch(FRONT, ledger_path=ledger_path)
    phase36_caps.check_unit_caps(FRONT, cells=..., ...)
```
Phase 42: `check_unit_caps("E3", **counts_for("e3_grid_subset", prereg.E3_GRID_SUBSET))` and
`sigmas=len(E3_SIGMAS)`; `_v4_control` already ran at prereg import (the SHA-256 reuse check).

**The D-05 seam: tp-global rebinding around `train_stage`** (`phase36_probe.py:858-873, 899-913`):
```python
def e3_plan(steps):
    """The published point re-keyed to probe36 labels, its pinned step count set to ``steps``."""
    plan = phase25_points.point_plan(phase36_prereg.E3_PROBE_POINT_KEY)
    ...
    return dict(
        plan,
        point_key=prove_isolated_label(f"{PROBE_PREFIX}_e3_t{steps}"),
        prefix=prove_isolated_label(f"{PROBE_PREFIX}_t{steps}"),
        pinned_mechanism=dict(plan["pinned_mechanism"], composed_steps=steps),
    )
...
        real_steps = tp.MAX_STEPS
        tp.MAX_STEPS = steps
        try:
            with loop_timer(tp) as loop, silenced():
                blob = phase25_points.train_stage(plan)
        finally:
            tp.MAX_STEPS = real_steps
        composed = blob["live_mechanism"]["composed_steps"]  # W8: nested, never top-level
        _prove(composed == steps, f"the seam composed {composed} steps, not {steps}")
```
Phase 42 rebinds three globals as a tuple and restores in `finally` (RESEARCH Code Example 2):
`saved = (tp.LR, tp.WARMUP_STEPS, tp.MAX_STEPS)`. Base plan:
`phase25_points.point_plan(phase25_record.point_key("dp_n8", sigma))` (`phase25_points.py:234-263`
gives `dp_clip_norm` = `CONTROL_CLIP_NORM` at σ = 0, `CLIP_NORM` otherwise: D-06/D-07 by
construction). Ignore its `point_epsilon`/`accounting` (computed at T = 200). Proof of take, after
the call: `blob["train_config"]` (`phase25_points.py:514`, `tp.asdict(cfg)`) has `lr`,
`warmup_steps`, `max_steps` equal to the recipe; `blob["live_mechanism"]["composed_steps"] == T`.
`train_stage` reads `tp.MAX_STEPS` for its composed-step proof (`phase25_points.py:447-451`), so the
rebind is mandatory at T = 800. Constants it rebinds live at `teach_persona.py:1587` (`LR = 3e-4`),
`:1599` (`MAX_STEPS = 200`), `:1600` (`WARMUP_STEPS = 20`), read at `:2003-2012`.

Resume guard (RESEARCH Pitfall 1): before `train_stage`, if `tp.arm_outputs(arm, prefix)["checkpoint"]`
exists, `tp.torch.load(path, weights_only=False)["train_config"]` (key written by
`src/personacore/checkpoint.py:135`) must match the cell's lr / warmup_steps / max_steps.

Stale-output refusal before training (`phase36_probe.py:884-897`): `training_sidecar(point_key)`
(`data/phase25_<point_key>_training.json`, `phase25_points.py:266-267`) and the adapter must not
exist, otherwise `train_stage` reuses them and prices 0 s.

**Scoring** (`phase36_probe.py:931-934` and `phase25_points.py:555-559`):
```python
                tp.score_arm(plan["arm"], fs.LOCKED_FACTS, adapter, device)
...
    model, _cfg, tok, forbid, _artifact = recall.load_adapted_model(device, adapter)
    capability = phase25_condition_c.measure_condition_c(model, tok, device, forbid=forbid)
```
Record shape for recall blocks: `phase25_recall._tier` (`scripts/phase25_recall.py:100-111`) →
`{numerator, denominator, rate, questions, draws_per_question, per_family}` from `score_arm`'s
`on_taught` / `on_heldout` (`k`, `n`, ...). That satisfies the control-record contract
(`phase35_prereg.py:69-72`: `recipe`, `seed`, `sigma` = 0.0, `taught_recall` / `heldout_recall`
with `numerator` / `denominator`). ε per noised point:
`phase25_epsilon.point_epsilon_for_sigma(sigma, steps=T, delta=phase35_prereg.DELTA)`
(`phase25_epsilon.py:226-235`; returns `None` at σ = 0). Composition:
`phase35_prereg.CURVE_TOTAL(eps_noised_only, delta=DELTA)`; it raises on a `None` entry
(`phase25_epsilon.py:271-294`), so controls are excluded at the call site.

**Run loop with ledger lines + heartbeat** (`phase41_erasure.py:2096-2131`):
```python
        phase36_ledger.require_launch(FRONT, ledger_path=ledger_path)
        rid = prereg.run_id(unit)
        phase36_ledger.append("start", run_id=rid, phase=41, front=FRONT, ledger_path=ledger_path)
        ...
        state = {"point": rid, "stage": "start", "shape": None, "draw_index": None}
        # B1: the thread's first beat waits a full period: beat once now.
        phase25_run.beat(heartbeat_path, **state)
        stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
        started_utc = _now()
        try:
            ...record = write_cell(unit, pf=pf, started_utc=started_utc, state=state)
            state.update(stage="done")
        finally:
            stop.set()
            thread.join()
        phase36_ledger.append(
            "end", run_id=rid, phase=41, front=FRONT, record=record, ledger_path=ledger_path
        )
```

**Per-run record write** (`phase41_erasure.py:1630-1642` `_run_provenance`, `1947-1972` `write_cell`):
records carry `provenance.run` = `{git_sha_at_launch, git_sha_at_end, head_moved_during_run,
device, torch_version, started_utc, finished_utc}` and `module_sha256_at_launch` (census #9:
`phase36_ledger` requires `provenance.run.{started_utc, finished_utc, device}` on every MPS record
and an end line naming it).

**Emit** (`phase41_erasure.py:2476-2511`): refuse an existing output, `refuse_if_dirty` on the real
root, build the record, require the fill file and every input record tracked and clean
(`_tracked_and_clean(FLOORS_FILE, *record["inputs"])`), `_write_once`. Aggregate provenance is emit
only (`phase41_erasure.py:2467-2471`), never `provenance.run.device = "mps"` (census #9):
```python
        "provenance": {
            "emitted_utc": _now(),
            "git_sha": git_sha(),
            "module_sha256": module_sha256(),
        },
```

**Report + main** (`phase41_erasure.py:2938-2969`):
```python
def report(*, root=None):
    root = pathlib.Path(root) if root is not None else pathlib.Path(_ROOT)
    prereg = _prereg()
    record_path = root / prereg.ERASURE_RECORD
    _prove(record_path.exists(), f"{record_path} is missing: emit the record first")
    _prove(
        not _is_real(root) or _tracked_and_clean(prereg.ERASURE_RECORD),
        f"{prereg.ERASURE_RECORD} must be committed and unmodified before the report renders it",
    )
    out = root / prereg.REPORT_RECORD
    _prove(not out.exists(), f"{out} exists — REFUSING to overwrite it. ...")
    out.write_text(render_report(_load(record_path)), encoding="utf-8")
    ...

def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    commands = {"preflight": preflight, "run": run, "emit": emit, "report": report}
    if len(argv) != 1 or argv[0] not in commands:
        raise SystemExit(__doc__)
    os.chdir(_REPO)
    commands[argv[0]]()
    return 0
```
`_table` GFM helper at `phase41_erasure.py:2520-2526`. The D-15 first line and the summary line
come from `phase42_prereg` functions, never retyped in `render_report`.

---

### `tests/test_phase42_prereg.py`

**Analog:** `tests/test_phase41_prereg.py`. Commit it in the SAME commit as `scripts/phase42_prereg.py`.

**Header / imports** (lines 16-62): sys.path inserts for scripts, src, tests; then
```python
import phase35_prereg  # noqa: E402  (scripts/ is not a package)
import phase36_caps  # noqa: E402  (same)
import phase41_prereg  # noqa: E402  (same)

from test_phase29_prereg import _assert_frozen_before, _git, _planted  # noqa: E402
from test_phase35_prereg import (_docstring_nodes, _insert_at, _literal_failures, _slot_census_failures)  # noqa: E402
from test_phase36_prereg import (_entries_node, _entry_string_failures, _first_inner, _skip_failures, _untested_functions)  # noqa: E402
```
`_assert_frozen_before` is `tests/test_phase29_prereg.py:69-…` (refuses a shallow clone; earliest
add; same-commit refusal).

**Ancestry trio** (lines 465-503), copy with the phase42 glob:
```python
def _strictly_before(x, y):
    run = subprocess.run(("git", "merge-base", "--is-ancestor", x, y), cwd=_ROOT, check=False)
    return x != y and run.returncode == 0


def _first_add(path):
    return _git("log", "--diff-filter=A", "--format=%H", "--", path).split()[-1]


def _phase41_records():
    return sorted(_git("ls-files", "results/phase41_*").split())


def test_phase41_prereg_is_frozen_before_every_phase41_record():
    _assert_frozen_before(PREREG, _phase41_records())
    # NON-VACUITY (natural RED): the v6.0 pre-registration was added before this one existed.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(PREREG, ["scripts/phase35_prereg.py"])


def test_this_test_file_is_first_added_before_every_phase41_record():
    mine = _first_add("tests/test_phase41_prereg.py")
    for record in _phase41_records():
        assert _strictly_before(mine, _first_add(record)), record
    assert not _strictly_before(mine, _first_add("scripts/phase35_prereg.py"))


def test_records_at_commit_is_true_at_the_first_commit():
    first = _git("log", "--format=%H", "--", PREREG).split()[-1]
    at_first = _git("ls-tree", "-r", "--name-only", first, "--", "results/").split()
    assert at_first, "meta-guard: the first commit's results/ tree is empty, the check is vacuous"
    assert not [path for path in at_first if path.startswith("results/phase41_")]
    assert phase41_prereg.RECORDS_AT_COMMIT == 0
```
Use `phase42_prereg.RECORD_GLOB` in `ls-files`, not a typed glob.

**Entries + predictions** (lines 299-333, 365-389): `_no_mutable_containers`,
`test_entries_names_kinds_and_d_ids`, `test_predictions_are_recorded_before_any_run` (each
prediction contains "descriptive" and "a mismatch is a finding, not a failure").

**Import probe** (lines 689-766): `_opens_a_checkpoint` + `_PROBE` subprocess with an `open` audit
hook; asserts no `checkpoints/`/`data/` open and `safetensors` not loaded at import. Phase 42's
import also runs `git show v5.0:` via `_v4_control` (a subprocess, not an `open`), fine.

**Censuses** (lines 769-807): `test_phase41_scripts_pass_the_slot_census` (glob
`scripts/phase42_*.py`, plus `owner_prereg_glob("e3_grid_subset")` match), `test_no_skips_in_this_file`,
`test_census_every_phase41_prereg_function_has_a_cpu_test` (every `def` in the prereg named in the
test file; planted-untested non-vacuity).

**Truth-table tests:** `test_pair_labels_truth_table` (L1204) and `test_summary_counts` (L1237) are
the shape for the 4×2 label table, summary line and D-15 null-line tests.

---

### `tests/test_phase42_threshold_prereg.py`

**Analog:** `tests/test_phase41_floors_prereg.py` (whole file, 357 lines). Copy section by section:
- module fixture importing the fill file (L57-61); `_tracked` (L68-69);
- values equal the committed records' (L77-105): recompute `F_Y * tk / tn` ONLY to compare with
  the fill value read from it, plus REFUSED via `phase29_prereg.control_is_unlearnable`;
- every consumed path in the derivation's source and tracked (L126-133);
- imports exactly `{pathlib, sys, phase35_prereg, phase42_prereg}` (L141-157);
- import opens no checkpoint (L160-214, `spec_from_file_location` subprocess);
- ordering (L223-277):
```python
def test_every_declared_input_precedes_the_floors_file():
    first = _first_commit(FLOORS)
    inputs = _declared_inputs()
    ...
    for path in inputs:
        assert _strictly_before(_first_add(path), first), path
    # NON-VACUITY (natural RED): the reverse relation is False for every input.
    assert not any(_strictly_before(first, _first_add(path)) for path in inputs)


def test_floors_file_is_frozen_before_every_later_phase41_record():
    ...
    _assert_frozen_before(FLOORS, _later_records())
    # NON-VACUITY (natural RED): the floors file was committed after the calibration records.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(FLOORS, [_first_calibration()])
```
  Phase 42: `_later_records()` = `results/phase42_*` minus the control glob (the noised points, the
  E3 record, the report); natural RED against the first control record.
- no number typed (L285-295), fill kwargs exactly `**phase42_prereg.threshold_fill_inputs()`
  (L298-336), slot census over `scripts/phase42_*.py` (L339-350), no skips (L353-357).
- RESEARCH Pitfall 6 enumerating test (float fill threshold vs `fractions.Fraction(7, 10)` per
  committed control, every k in 0..n): pattern from `phase41_prereg.exact_margin` (L950-964).

---

### `tests/test_phase42_recipes.py`

**Analog A:** `tests/test_phase36_probe.py:1838-1905` (`_e3_light`): fake `train_stage` that
records `tp.MAX_STEPS` at call time, a `crash_on` index for the restore-on-exception leg, fake
`score_arm`, `monkeypatch.setattr(phase25_points, "train_stage", ...)`, then
```python
    assert tp.MAX_STEPS == calls["max_steps"] and tp.train is calls["loop"]  # restored
```
Phase 42 records `(tp.LR, tp.WARMUP_STEPS, tp.MAX_STEPS)` per call and asserts (20, 80) warmups and
the tuple restored after a raise.

**Analog B:** `tests/test_phase41_erasure.py`:
- `_real_tree_untouched` autouse fixture (L53-61): `git status --porcelain -- results ledger`
  unchanged, no new `*phase42*` under results/data/checkpoints;
- `test_the_driver_imports_without_torch` (L99-108): subprocess import, `torch` not in `sys.modules`;
- `test_write_once_refuses_an_existing_file` (L160); `_tmp_git` / `_tracked_in` (L64-94);
- the rig (L1370-1435): tmp root, `refuse_if_dirty` recorded, `phase36_caps.tracked_files` pinned
  to the budget record, tmp ledger + heartbeat via `ledger_path`/`heartbeat_path`, `git_sha`
  faked; `_ledger` / `_whole` helpers (L1437-1459) build start/end lines with
  `phase36_ledger.append(..., ledger_path=path)`; `_launch` (L1462-1474) asserts no training call
  happens when preflight refuses.

---

### `.gitignore` (two lines)

**Analog:** `.gitignore:18-20`:
```
# Phase 41 E1 calibration training CSVs (teach_persona.arm_outputs csv lands under results/;
# the Phase 35 ordering legs would count it as a phase-41 record; 41-05 WR-03)
results/phase41_e1_calibration_seed*/
```
Phase 42 adds `results/phase42e3_*/` and `results/phase42rh_*/` (csv lands at
`results/{prefix}_dp_n8/run.csv` via `teach_persona.arm_outputs`, `teach_persona.py:383-392`, until
`train_stage` moves it to `data/phase25_runs/<point_key>/run.csv`, `phase25_points.py:478-488`).
Its test mirrors `tests/test_phase41_prereg.py:2320-2340`:
```python
def _ignored(rel):
    run = subprocess.run(("git", "check-ignore", "-q", rel), cwd=_ROOT, check=False)
    assert run.returncode in (0, 1), run
    return run.returncode == 0


def test_calibration_csv_directory_is_gitignored():
    import teach_persona
    ...
        csv = teach_persona.arm_outputs(f"e1_calibration_seed{seed}", prefix="phase41")["csv"]
        rel = csv.relative_to(_ROOT).as_posix()
        assert fnmatch.fnmatch(rel, p.RECORD_GLOB), rel  # meta-guard: the legs would count it
        assert _ignored(rel), rel
    # NON-VACUITY: the records the legs must see are not ignored.
```
Difference: the Phase 42 prefixes do NOT match `results/phase42_*`, so the meta-guard flips to
`assert not fnmatch.fnmatch(rel, RECORD_GLOB)`; the ignore lines exist for the clean-tree probes
(census #11) after a crash, not for the ordering legs. Non-vacuity: control and point records are
not ignored.

---

## Shared Patterns

### Refusal style
**Source:** `scripts/phase41_prereg.py:62-65`, `scripts/phase41_erasure.py:93-95`
**Apply to:** every new script. `_prove(condition, message)` raising `SystemExit("[module] ...")`, never `assert`.

### Write-once records
**Source:** `scripts/phase41_erasure.py:179-183` (`_write_once` → `phase25_run.atomic_write_json`)
**Apply to:** controls, points, aggregate record. Report: `out.write_text` after a `not out.exists()` refusal (L2950-2956).

### Launch gating + ledger
**Source:** `scripts/phase41_erasure.py:1482, 2097-2126`; `scripts/phase36_ledger.py:76, 194, 400`
**Apply to:** driver `run`. `require_launch("E3")` before each run, one `start` line, one `end` line with `record=`.

### Ancestry
**Source:** `tests/test_phase29_prereg.py:69` (`_assert_frozen_before`), `tests/test_phase41_prereg.py:465-503`, `tests/test_phase41_floors_prereg.py:251-277`
**Apply to:** both phase42 prereg test files, each with a natural-RED non-vacuity leg.

### Names read, never typed
**Source:** `scripts/phase41_prereg.py:128-139` (glob equality), `phase35_prereg.SLOTS[...]["input_records"][i]`
**Apply to:** every path, σ, T, batch, seed, F_Y, δ. The one caller-chosen literal is lr `1e-3` (D-02), as `GRID` is in Phase 41 (L146-147).

## Frozen-census traps (where copying an analog would trip a census)

| # | Trap | Where an analog would lead you astray | Rule for phase42 files |
|---|------|----------------------------------------|------------------------|
| 1 | `tests/test_phase23_resume.py:270` greps the literal `train_arm(` over scripts/ and tests/ (register L60-…, includes `phase41_erasure.py` and `phase36_probe.py` entries) | `phase41_erasure.train_calibration_adapter` calls the trainer directly; `phase25_points.py:417` holds the one sanctioned call | Never write `train_arm(` in code, docstring, comment or test (including fake names/asserts). Reach the trainer only via `phase25_points.train_stage`; fake `train_stage` in tests. |
| 2 | `tests/test_phase25_driver.py:341`: `os.replace` only in `phase25_run.py` / `phase25_record.py` | — | Use `phase25_run.atomic_write_json`. |
| 3 | `tests/test_lora_inject.py:450` ISO-06 register of `inject_lora` callers | RESEARCH's MPS noise probe called `inject_lora` | Never call `inject_lora`; use `score_arm` / `phase14_recall.load_adapted_model`. |
| 4 | `tests/test_phase19_erasure.py:1371` `retention_perplexity` call sites | — | Retention only through `phase25_condition_c.measure_condition_c`. |
| 5 | `tests/test_phase20_correction.py:1377` `mitigation_point_verdict` callers | `mitigation_gate` is where `F_Y` lives | Do not call it; compare `k / n >= fill threshold`. |
| 6 | `tests/test_phase21_sc5.py:280` counts `== 10` / `!= 10` in tests/**, comments included | — | No `== 10` / `!= 10` in new tests. |
| 7 | `tests/test_phase35_prereg.py:2313` slot census + `:2557` legs | Phase 41 had the band slot alongside floors | Each slot filled once, as `E3_GRID_SUBSET` / `E3_RECALL_THRESHOLD`, only in `scripts/phase42_*prereg.py`; driver is not `*prereg.py` and never calls `fill`. |
| 8 | `tests/test_phase36_caps.py:286` exec's `phase42_prereg.py` fresh | — | No writes at import; import-idempotent. |
| 9 | `tests/test_phase36_ledger.py:722` end line per MPS record | per-run `provenance.run.device` | Aggregate record gets emit provenance only. |
| 10 | `tests/test_phase32_frontier.py:638` excludes only `results/phase4[0-9]_*` | the `phase42e3_` csv dir under results/ | Records only under `results/phase42_*`; csv dirs gitignored. |
| 11 | clean-tree probes (`git status --porcelain results/` == "") | — | Run the suite on a committed tree. |
| 12 | sha pins of `teach_persona.py`, `phase25_points.py`, `phase35_prereg.py` | RESEARCH D-05 temptation | Rebind at runtime; never edit them. |
| 13 | `tests/test_phase41_floors_prereg.py:349` plants `scripts/phase42_floors_prereg.py` | copying the floors file name | Name fill file 2 `phase42_threshold_prereg.py`. |

## No Analog Found

None. RESEARCH's Code Examples 1-2 are wiring of the analogs above, not new patterns.

## Metadata

**Analog search scope:** `scripts/phase41_prereg.py`, `scripts/phase41_floors_prereg.py`, `scripts/phase41_erasure.py`, `scripts/phase40_prereg.py` (outline only; same layout as 41), `scripts/phase36_probe.py`, `scripts/phase25_points.py`, `scripts/phase35_prereg.py`, `scripts/phase25_recall.py`, `scripts/phase25_condition_c.py`, `scripts/phase25_epsilon.py`, `scripts/phase36_ledger.py`, `scripts/teach_persona.py`, `src/personacore/checkpoint.py`, `tests/test_phase41_prereg.py`, `tests/test_phase41_floors_prereg.py`, `tests/test_phase41_erasure.py`, `tests/test_phase36_probe.py`, `tests/test_phase29_prereg.py`, `tests/test_phase35_prereg.py`, `tests/test_phase36_caps.py`, `tests/test_phase23_resume.py`, `.gitignore`
**Files scanned:** 22
**Not verified:** `phase35_prereg._prove_derivation_value` accepting a tuple of `MappingProxyType` against `RECIPES` (equality holds in Python, `mappingproxy == dict`; the grid fill's first run confirms it).
**Pattern extraction date:** 2026-10-13
