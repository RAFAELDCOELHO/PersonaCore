# Phase 41: Erasure Across Facts, Orderings and Seeds - Pattern Map

**Mapped:** 2026-10-08 (HEAD 3787b9d)
**Files analyzed:** 10 new/modified
**Analogs found:** 10 / 10 (one partial: the Taylor gradient ordering has no in-repo analog for the backward pass itself)

All line numbers below were read at HEAD 3787b9d. Every artifact path a new file needs is quoted
with the constant that owns it; never type a path the constants can produce.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `scripts/phase41_prereg.py` (fill file 1) | config / pre-registration + pure functions | transform (pure) | `scripts/phase40_prereg.py` (entries, fills, R-3 b pure fns) + `scripts/phase38_prereg.py` (two-fill split, path globs) | exact |
| `scripts/phase41_floors_prereg.py` (fill file 2) | config / fill file consuming in-phase records | file-I/O (read committed records) -> fill | `scripts/phase38_sizes_prereg.py` | exact |
| `scripts/phase41_erasure.py` (driver) | service / long-running MPS driver | batch + file-I/O (write-once records, ledger) | `scripts/phase40_noise.py` | exact (skeleton); partial (gradient ordering, K16 reader) |
| `artifacts/com.personacore.phase41.e1.plist` | config (launchd) | n/a | `artifacts/com.personacore.phase40.e2.plist` | exact |
| `tests/test_phase41_prereg.py` | test (git-ancestry + AST + truth tables) | n/a | `tests/test_phase40_prereg.py` | exact |
| `tests/test_phase41_floors_prereg.py` | test | n/a | `tests/test_phase38_sizes_prereg.py` | exact |
| `tests/test_phase41_erasure.py` | test (fake rig, AST gates, main dispatch, plist) | n/a | `tests/test_phase40_noise.py` + `tests/test_phase37_routes.py` §(6)-(7) | exact |
| `tests/test_phase23_resume.py` (MODIFY: `_TRAIN_ARM_CALL_SITES` + tripwire sum) | test register | n/a | its own Phase 40 entry (lines 119-124, 331-333) | exact |
| `tests/test_phase14_scoring.py` `DRAW_ALL_ASSERTED_BY` (modify ONLY if the K16 reader cannot assert in place) | test register | n/a | line 696 | conditional |
| `tests/test_lora_inject.py` ISO-06 allowlists (NO change expected) | test register | n/a | lines 261-293 | do not touch |

---

## Pattern Assignments

### `scripts/phase41_prereg.py` (fill file 1: grid, alternative ordering, b-margin, pure functions, predictions)

**Analog:** `scripts/phase40_prereg.py` (structure, entries, R-3 b readers), `scripts/phase38_prereg.py:700-713` (fill bindings).

**Header / sys.path / import pattern** (`scripts/phase40_prereg.py:32-56`):
```python
import collections.abc
import fnmatch
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

import phase35_prereg  # noqa: E402  (needs the sys.path insert above)
```
Plain `import phase35_prereg` only. The slot census (`tests/test_phase35_prereg.py:2166-2269`) refuses
`from phase35_prereg import fill`, `import phase35_prereg as X`, any `phase35_prereg._*` access, any
`_rule_*` reference, and any module-level binding of a slot's upper-cased name to anything but its fill.

**Date / record-count certificate** (`scripts/phase40_prereg.py:62-70`):
```python
# At this commit no `results/phase40_*` file existed, tracked or untracked.
COMMITTED = "2026-10-05"
RECORDS_AT_COMMIT = 0


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase40_prereg] {message}")
```

**Entry schema by reference + `_prove_entry`** (`scripts/phase40_prereg.py:77-120`): copy verbatim
with the `[phase41_prereg]` prefix. Four fields exactly (`ENTRY_FIELDS`), no `proposer`/`adopted_by`,
`FORBIDDEN_PHRASE` refused. Entries table + closed name set + `_prove_entries()` at import:
`scripts/phase40_prereg.py:488-498` (entry shape), `:993-1030` (MappingProxyType freeze, `_ENTRY_NAMES`,
`_prove_entries()` called at module level).

**Record paths derived from the registry, by EQUALITY** (`scripts/phase40_prereg.py:132-140`,
`scripts/phase38_prereg.py:120-127`):
```python
RECORD_GLOB = next(p for p in phase35_prereg.V6_RESULT_PATHS if p == "results/phase40_*")
NOISE_FLOOR_RECORD = phase35_prereg.SLOTS["e1_condition_c_band_inputs"]["input_records"][0]
BUDGET_RECORD = phase35_prereg.SLOTS["e2_S"]["input_records"][0]
```
Phase 41 values to derive this way (all exist in `scripts/phase35_prereg.py`):
- `V6_RESULT_PATHS` entries (`:317-333`): `"results/phase41_calibration_*.json"` (:325), `"results/phase41_band_inputs_*.json"` (:326), `"results/phase41_*"` (:327).
- `SLOTS["e1_checkpoint_grid"]["input_records"][0]` == `_BUDGET_RECORD` = `"results/phase36_budget.json"` (`:769`).
- `SLOTS["e1_condition_a_floors"]["input_records"]` == (`_CALIBRATION_RECORDS` `:771`, `_CALIBRATION_CORPUS` `:778` = `"results/phase19_calibration_corpus.json"`).
- `SLOTS["e1_condition_c_band_inputs"]["input_records"]` == (`_NOISE_FLOOR_RECORD` `:773`, `_BAND_INPUT_RECORDS` `:774`).
- Per-record path helpers: copy `seed_record`/`a2_record` (`scripts/phase40_prereg.py:150-162`), each `_prove(fnmatch.fnmatch(path, GLOB))`. E.g. `calibration_record(ordering, seed)` -> `CAL_GLOB.replace("*", f"{ordering}_seed{seed}")`, `band_record(...)`, `cell_record(target, ordering, seed)` under `RECORD_GLOB`.
- `run_id(...)`: `scripts/phase40_prereg.py:165-169` -> `phase36_ledger.run_id(41, "E1", unit)` (`scripts/phase36_ledger.py:76`).

**Slot fills** (`scripts/phase40_prereg.py:1036-1039`, `scripts/phase38_prereg.py:707-713`):
```python
E2_S = phase35_prereg.fill("e2_S", input_records=(BUDGET_RECORD,), derivation=ENTRIES["e2_S"])
E2_NOISE_FLOOR_ESTIMATOR = phase35_prereg.fill(
    "e2_noise_floor_estimator", estimator=ENTRIES["e2_noise_floor_estimator"]
)
```
Phase 41 needs exactly three, all in THIS file (planted green `_P41_FIRST`, `tests/test_phase35_prereg.py:2572-2577`):
`E1_CHECKPOINT_GRID = phase35_prereg.fill("e1_checkpoint_grid", checkpoints=GRID, input_records=(BUDGET,), derivation=...)`
(derivation `value` must be the TUPLE `(16, 32, 48, 64, 128)`, `_rule_e1_checkpoint_grid` `:1211`);
`E1_ALTERNATIVE_ORDERING = phase35_prereg.fill("e1_alternative_ordering", ordering=ENTRIES[...])` (`:1415`);
`E1_CONDITION_B_MARGIN = phase35_prereg.fill("e1_condition_b_margin")` (no kwargs, `:1694`).
Then the caps check exactly like `scripts/phase38_sizes_prereg.py:61`:
`phase36_caps.check_unit_caps("E1", **phase36_caps.counts_for("e1_checkpoint_grid", E1_CHECKPOINT_GRID))`
(`counts_for` E1 branch `scripts/phase36_caps.py:185-186` returns only `checkpoints_per_cell`; D-26's
confirmation deviation must NEVER be passed as `k48_confirms_per_cell=` > 1, `scripts/phase36_caps.py:165-179`
refuses it).

**Pure functions to place here** (all must be CALLED by name from `tests/test_phase41_prereg.py`, see census below):
- Per-target rows: reuse `phase40_prereg.a2_scope/a2_rows/slot_rows` (`scripts/phase40_prereg.py:1058-1108`) by import, never re-implement. NOTE `slot_rows` keys on `pin.GATED_NONTARGET_SLOTS` + `pin.TARGET_SLOT` (pet_name-shaped, research Pitfall 4): for cat_name/street/sibling_name the 7 non-targets are `phase18_extraction.CORE_SLOTS` minus the target, so the per-target (b) helper is new code over `slot_rows`' output (it covers all 8 core slots).
- Verdict combiner, `pair_label`, D-17 counts, D-19 label rule, Spearman closed form, E1-share pause arithmetic: new pure functions (RESEARCH §Code Examples, §Pattern 8).
- R-3 b crash rule readers: copy `seed_outcomes`, `pending_seeds`, `lost_attempts`, `dropped_attempt_dir`, `_approved`, `dropped_manifest_failures`, `relaunch_declaration_name`, `relaunch_declaration_failures`, `latest_head_failures` from `scripts/phase40_prereg.py:1391-1579`, keyed per CELL (unit = cell/prep unit instead of seed). `_approved` regex (`:1476-1483`) verbatim. Constants to mirror: `DROPPED_ROOT = "data/phase40_dropped"` -> `data/phase41_dropped` (`:1437`; `data/` is gitignored, `.gitignore:17`), `RELAUNCH_DECLARATION_KEYS` (`:1450`) for the D-23 resume approval (Claude's discretion).
- Predictions D-11 / D-21 as entries (kind `preference`/`derived`), Phase 40 D-07 pattern.

**Rehearsal prefix:** `REHEARSAL_PREFIX = "phase40rh"` (`scripts/phase40_noise.py:88-89`) -> `phase41rh`; fnmatch `results/phase41_*` does not match `phase41rh_`.

---

### `scripts/phase41_floors_prereg.py` (fill file 2: floors + band, ONE file)

**Analog:** `scripts/phase38_sizes_prereg.py` (whole file, 61 lines).

**Imports + read-committed-record pattern** (`scripts/phase38_sizes_prereg.py:17-39`):
```python
import json
import pathlib

import phase35_prereg
import phase36_caps
import phase38_prereg

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
MINTING_RECORD = phase38_prereg.MINTING_RECORD
_RECORD = json.loads((_REPO_ROOT / MINTING_RECORD).read_text(encoding="utf-8"))
...
if _DRIFT:
    raise SystemExit(
        f"[phase38_sizes_prereg] max_set_size(n_cleared) != the record's max_set_size: {_DRIFT}"
    )
```

**Derivation + fill** (`scripts/phase38_sizes_prereg.py:41-61`):
```python
_DERIVATION = {
    "value": _SIZES,
    "derivation": "D-07: ... never typed.",
    "kind": "derived",
    "source": f"38-CONTEXT D-07, D-08, D-09 (255380f), D-31 (f7ad285); "
    f"{MINTING_RECORD} slots[*].n_cleared",
}

E5_SET_SIZES = phase35_prereg.fill(
    "e5_set_sizes",
    set_sizes=_SIZES,
    input_records=(MINTING_RECORD,),
    derivation=_DERIVATION,
)
```
Phase 41 version: `E1_CONDITION_A_FLOORS = phase35_prereg.fill("e1_condition_a_floors", floors={(t,o,s): None ...}, input_records=(<4 calibration paths from phase41_prereg helpers>, CALIBRATION_CORPUS), derivation=...)`
and `E1_CONDITION_C_BAND_INPUTS = phase35_prereg.fill("e1_condition_c_band_inputs", band_inputs={(s,o): None ...}, input_records=(NOISE_FLOOR_RECORD, <4 band paths>), derivation=...)`.
`_consume_inputs` requires every consumed path to appear as a substring of `derivation["source"]` (build `source` with an f-string over the path tuple, as `:48-49` does). Keys iterate `phase35_prereg.e1_targets()` (`:382`), `e1_teaching_seeds()` (`:371`) and `phase41_prereg.ORDERINGS`; nothing typed.

Both slots MUST be in this ONE file: planted green `_P41_FLOORS` (`tests/test_phase35_prereg.py:2578-2580`); splitting reddens leg (a) (red case `b7_41`, `:2679-2702`). No caps call is needed here (`SLOT_COUNTS` in `scripts/phase36_caps.py:66` binds only `e1_checkpoint_grid` for E1); if one is added, it is exec'd by the owner-cap test.

---

### `scripts/phase41_erasure.py` (driver: preflight / run / emit / report / drop_attempt / declare_relaunch)

**Analog:** `scripts/phase40_noise.py`. Name must NOT end in `prereg.py` (else `_is_fill_file`, `tests/test_phase35_prereg.py:2441-2445`, treats it as a fill file).

**Module docstring with command list** (`scripts/phase40_noise.py:1-25`): `main()` raises `SystemExit(__doc__)` on a bad argv, so the docstring is the usage text.

**Imports / constants** (`scripts/phase40_noise.py:27-90`):
```python
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import phase25_run  # noqa: E402  — atomic_write_json, beat, start_heartbeat (torch-free)
import phase36_caps  # noqa: E402  (torch-free; the launch caps)
import phase36_ledger  # noqa: E402  (torch-free; the per-seed attempt)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

_REPO = pathlib.Path(__file__).resolve().parent.parent
_ROOT = _REPO
FRONT = "E2"
LAUNCH_PATHSPEC = ("scripts", "src", "results", "artifacts")
PREREG_FILE = "scripts/phase40_prereg.py"
DRIVER_FILE = "scripts/phase40_noise.py"
DISCLOSED_MODULES = (DRIVER_FILE, PREREG_FILE)
MODULES = DISCLOSED_MODULES + ( ... )
RUN_PROVENANCE_KEYS = ("git_sha_at_launch", "git_sha_at_end", "head_moved_during_run", "device",
                       "torch_version", "started_utc", "finished_utc")
ARM_PREFIX = "phase40"
REHEARSAL_PREFIX = "phase40rh"
CSV_DIR = "phase40_e2"
```
Phase 41: `FRONT = "E1"`; `DISCLOSED_MODULES` adds `scripts/phase41_floors_prereg.py`; `MODULES` adds `scripts/phase37_routes.py`, `scripts/phase40_prereg.py`, `scripts/phase40_noise.py` (D-13 scorer), `scripts/erasure_gate.py`, `scripts/mitigation_gate.py`. Torch-free at import: every torch module imported lazily inside functions (`:168-178`, `_prereg()` / `_device()`).

**Lazy prereg / device / write-once / release** (`scripts/phase40_noise.py:168-193`):
```python
def _prereg():
    import phase40_prereg
    return phase40_prereg

def _device():
    from personacore.preflight import preflight_device
    return preflight_device(strict=True)["device"]

def _write_once(path, blob):
    path = pathlib.Path(path)
    _prove(not path.exists(), f"{path} exists: write-once")
    path.parent.mkdir(parents=True, exist_ok=True)
    phase25_run.atomic_write_json(path, blob)
```
Never bind `E1_CHECKPOINT_GRID = phase41_prereg.E1_CHECKPOINT_GRID` at module level (slot census; `tests/test_phase40_noise.py:2989-2993`). Read fills as `_prereg().E1_CHECKPOINT_GRID` inside functions.

**Real-root vs rehearsal root** (`scripts/phase40_noise.py:133-165` `_is_real` / `_root_ledger`): copy verbatim.

**Calibration adapter training — the ONE `train_arm(` call** (`scripts/phase40_noise.py:312-363`):
```python
    result = tp.train_arm(
        arm,
        facts=facts,
        family_ids=phase14_factset.TAUGHT_FAMILY_IDS,
        second_person=second_person,
        replay_ratio=replay_ratio,
        seed=seed,
        prefix=prefix,
    )
    csv_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(paths["csv"]), str(csv_dst))
```
Phase 41: `(facts, second_person, replay_ratio) = tp.arm_spec("cal_first_person_replay")` — the recipe of the pin's `_cmd_cal_train` (`scripts/phase19_erasure.py:3521-3536`), with `seed=` added and a Phase 41 arm name + `prefix="phase41"`. Never call `pin._cmd_cal_train` (resolves to `checkpoints/phase19_erase_calibration_adapter.pt`, takes no seed). The csv must move out of `results/phase41_<arm>/` (matches `results/phase41_*`, would trip fill-order legs) into `root/"data"/CSV_DIR/arm/"run.csv"`. Prove `recall.ADAPTER_PATH` byte-unchanged around the call (`:329`, `:345-348`). Exactly ONE textual `train_arm(` in the driver (see register below).

**K=48 pass, write-once record** (`scripts/phase40_noise.py:371-383`; K48 `erased` shape `scripts/erasure_kstar_run.py:136-137`):
```python
    rel = prereg.a2_record(group, seed)
    record = pathlib.Path(root) / rel
    _prove(not record.exists(), f"{record} exists: the A2 records are write-once")
    pin.run_erasure_arm(prereg.A2_LABEL, device, adapter_path=adapter_path, record_path=record)
    _release()
```
```python
    components = [tuple(address) for address in curve["ordered_prefix"][:k]]
    pin.run_erasure_arm("erased", device, components=components, record_path=record_path)
```
Phase 41 cell: `pin.run_erasure_arm("erased", device, adapter_path=<phase41_adapters[seed]["full"]["path"]>, components=prefix[:c], record_path=...)`. Calibration: `pin.run_erasure_arm("cal-erased", device, corpus_path=pin.CALIBRATION_CORPUS_PATH, adapter_path=<new cal adapter>, components=prefix, record_path=root/"data/phase41_e1/...")` (pin call shape `scripts/phase19_erasure.py:3547-3555`). Raw calibration arm records go under `data/`, never `results/phase41_*` (research Pitfall 2).

**Current ordering** — import, never re-implement: `phase37_routes.select_target_prefix(model, tok, device, artifact, *, fact, dialogue_ppl)` (`scripts/phase37_routes.py:154-182`), `out["ordered"]`. Calibration greedy ordering: the pin's `_selected_components` argument set (`scripts/phase19_erasure.py:3558-3587`) passed straight to `pin.select_ablation_prefix` (`:2443`), keeping full `ordered` for D-06. Tie-break mirror for the gradient ordering: the pin sorts `sorted(index, key=lambda a: (-contribution[a], a))` (`scripts/phase19_erasure.py:2487`); snapshot-first rule `artifact = ablate_components(artifact, [])` (`:2474`).

**Adapter identity (D-11, D-24 attempt comparison)** — import `phase40_noise.adapter_identity` (`scripts/phase40_noise.py:386-419`); never sha256 (torch.save embeds the file name).

**D-13 block (D-20)** — import `phase40_noise.d13_scores(adapter_path, a2_record_path, device, state)` (`scripts/phase40_noise.py:422`); needs the M1 adapter exported to a file (`personacore.checkpoint.export_adapter`). Wrap exactly as `run()` does at `:1024-1068` (ruling c: an exception becomes `d13_not_measured`, never drops the cell).

**Adapter digests (ERASE-05)** — preflight reads `results/phase40_noise_floor.json` (`phase40_prereg.NOISE_FLOOR_RECORD`, `scripts/phase40_prereg.py:134`) key `phase41_adapters[str(seed)][group] = {"path", "sha256"}` (written at `scripts/phase40_noise.py:1428`; verified shape: `checkpoints/phase40_e2_{full,m2}_seed{1337,2024}_adapter.pt`). Refuse in preflight on mismatch; never in a host-gated test.

**Preflight** (`scripts/phase40_noise.py:833-956`): copy the order — `_root_ledger`, rehearsal must be `device == "cpu"`, `git_sha()`, `_import_modules()` (`:119-130`), `module_sha256()`, every `run_inputs()` path exists (`:277-304`), open-attempt checks against the ledger, `seed_outcomes`/`pending` (per cell here), `refuse_if_dirty(... pathspec=_launch_pathspec(...))`, stale-output refusals, `phase36_ledger.require_launch(FRONT, ledger_path=...)` (`:913`), `phase36_caps.check_unit_caps(FRONT, ...)` (`:914`), real root `device == "mps"` + rehearsal identity check (`:916-937`). Phase 41 adds: the four adapter digests, the D-23 E1-share pause (`phase36_ledger.spent(fronts=("E1",))`, `scripts/phase36_ledger.py:315`, between attempts only).

**Run loop: one ledger attempt per unit** (`scripts/phase40_noise.py:999-1115`):
```python
    for i, seed in enumerate(pf["pending"]):
        phase36_ledger.require_launch(FRONT, ledger_path=ledger_path)
        rid = prereg.run_id(seed)
        phase36_ledger.append("start", run_id=rid, phase=40, front=FRONT, ledger_path=ledger_path)
        ...
        state = {"point": rid, "stage": "start", "shape": None, "draw_index": None}
        phase25_run.beat(heartbeat_path, **state)
        stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
        started_utc = _now()
        try:
            ...
            _write_once(root / prereg.seed_record(seed), blob)
        finally:
            stop.set()
            thread.join()
        phase36_ledger.append("end", run_id=rid, phase=40, front=FRONT,
                              record=prereg.seed_record(seed), ledger_path=ledger_path)
```
Every record that ends an attempt carries `provenance.run.{started_utc, finished_utc, device, ...}` (`:1082-1093`; `phase36_ledger._closed_row` reads the clock from it). Phase 41 adds the D-23 pause check before each cell's `require_launch`.

**R-3 b crash handling** — copy `drop_attempt` (`:649-706`), `declare_relaunch` (`:709-732`), `rerun_seeds` (`:735-751`), `_dropped_attempts` (`:754-805`), `_launch_pathspec` (`:813-830`), keyed per cell.

**emit / report / main** (`:1460-1494`, `:1993-2036`):
```python
def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    commands = {"preflight": preflight, "run": run, "emit": emit, "report": report}
    if len(argv) != 1 or argv[0] not in commands:
        raise SystemExit(__doc__)
    os.chdir(_REPO)
    commands[argv[0]]()
    return 0
```
`report` writes only from a tracked, unmodified record (`_tracked_and_clean`, `:1993-1998`); both are write-once and point corrections at `scripts/_addendum.py`.

**K=16 reader (new; no in-place analog in the driver set)** — copy the draw loop from `scripts/phase23_run.py:4477-4520`:
```python
            tp.seed_everything(recall.SEED)
        ...
            for index, entry in enumerate(cell):
                base_ids = x18._guarded_span(entry)
                recall.assert_no_value_in_prompt(
                    tok, tok.decode(base_ids), clean_room_values, prompt_ids=base_ids
                )
                ...
                completions, stopped = recall.draw_all(
                    model, tok, entry["prompt_ids"], device(), forbid,
                    entry["seed_index"] * x18.K,  # the PIN's stride
                    n_samples=k - 1,
                )
                _prove(len(completions) == k, ...)
                draws.append({"family": ..., "dose": ..., "fact_id": ..., "slot": ..., "tier": ...,
                              "arm": x18.ARMS[0], "seed_index": ..., "prefix_text": ...,
                              "completions": completions, "stopped": stopped})
```
with `k = grid["read_k"]` (never `16`), entries from `phase35_prereg.a2_corpus_entries()` (`scripts/phase35_prereg.py:507`). `draw_all` and `assert_no_value_in_prompt` MUST sit in the same, undecorated function whose name does not start with `_skip` (draw_all census, below).

**Taylor gradient ordering (partial analog)** — no backward pass exists in the repo's erasure code; use RESEARCH §Pattern 2 `taylor_scores` (ids built as `phase18_extraction.span_nll_from_ids`, `scripts/phase18_extraction.py:1050-1107`, whose forward is `no_grad` at `:1084`). Address keys come from `pin._COMPONENT_PREFIX` / `pin.component_index()` (`scripts/phase19_erasure.py:237-272`); loads go through `pin.ablate_components` + `personacore.lora.load_adapter_weights`; the model is loaded via `recall.load_adapted_model` (ISO-06 allowlisted consumer), never `inject_lora`.

---

### `artifacts/com.personacore.phase41.e1.plist`

**Analog:** `artifacts/com.personacore.phase40.e2.plist` (60 lines). Change only `Label` (`com.personacore.phase41.e1`), `ProgramArguments[3]` (`/Users/juliorcoelho/PersonaCore/scripts/phase41_erasure.py`), `StandardOutPath`/`StandardErrorPath` (`logs/phase41_e1.{out,err}`), and the comment. Keep `KeepAlive` false (`:23-24`), `RunAtLoad` false (`:26-27`), caffeinate `-dims` wrapper (`:31-32`), `ProcessType Interactive`, env `PERSONACORE_SWEEP_ACTIVE=1`, `PATH`, `PYTHONUNBUFFERED`.

**Test analog:** `tests/test_phase40_noise.py:603-635` `test_plist_mirrors_the_r1b_agent` — compares against `artifacts/com.personacore.phase37.r1b.plist` with only `{"Label","ProgramArguments","StandardOutPath","StandardErrorPath"}` allowed to differ.

---

### `tests/test_phase41_prereg.py`

**Analog:** `tests/test_phase40_prereg.py`.

**Header / imports** (`tests/test_phase40_prereg.py:16-61`):
```python
_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
...
import phase35_prereg  # noqa: E402  (scripts/ is not a package)
import phase40_prereg  # noqa: E402  (same)

from test_phase29_prereg import _assert_frozen_before, _git, _planted  # noqa: E402
from test_phase35_prereg import (  # noqa: E402
    _insert_at,
    _literal_failures,
    _slot_census_failures,
)
from test_phase36_prereg import (  # noqa: E402
    _entries_node,
    _entry_string_failures,
    _first_inner,
    _skip_failures,
    _untested_functions,
)
```
`import phase41_prereg` plainly, never aliased (`_untested_functions` counts `phase41_prereg.<def>(` calls by module name, `tests/test_phase36_prereg.py:418-438`).

**Ancestry tests** (`tests/test_phase40_prereg.py:377-413`):
```python
def test_phase40_prereg_is_frozen_before_every_phase40_record():
    _assert_frozen_before(PREREG, _phase40_records())
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(PREREG, ["scripts/phase35_prereg.py"])

def test_this_test_file_is_first_added_before_every_phase40_record():
    mine = _first_add("tests/test_phase40_prereg.py")
    for record in _phase40_records():
        assert _strictly_before(mine, _first_add(record)), record
    assert not _strictly_before(mine, _first_add("scripts/phase35_prereg.py"))

def test_records_at_commit_is_true_at_the_first_commit():
    first = _git("log", "--format=%H", "--", PREREG).split()[-1]
    at_first = _git("ls-tree", "-r", "--name-only", first, "--", "results/").split()
    assert at_first, "meta-guard: ..."
    assert not [path for path in at_first if path.startswith("results/phase40_")]
    assert phase40_prereg.RECORDS_AT_COMMIT == 0
```
This test file must be committed in or before the commit adding `scripts/phase41_prereg.py`, and before any `results/phase41_*`.

**Nothing typed (AST, not grep)** — `test_no_derived_value_is_typed_in_the_prereg` (`tests/test_phase40_prereg.py:548-580`) via `_literal_failures(source, ints, floats, strs)`. Phase 41 census values: 16, 48, 27, 8/27 margin `0.2962962962962963`, band edges, gap 1.2420966625043919 / 1.2368822143360418, `gap_noise_floor` 0.08406970366097503, E1 hours 52.779745537787676. The grid tuple (16, 32, 48, 64, 128) is caller-chosen (D-07) and is the one place literals are allowed; exempt it explicitly. Ints/floats only: str docstrings never match (memory `grep-criteria-measure-prose`).

**Slot census over all phase41 scripts** (`tests/test_phase40_prereg.py:875-879`):
```python
def test_phase40_scripts_pass_the_slot_census():
    paths = sorted(_SCRIPTS.glob("phase40_*.py"))
    assert paths, "meta-guard: ..."
    sources = [(p.relative_to(_ROOT).as_posix(), p.read_text(encoding="utf-8")) for p in paths]
    assert _slot_census_failures(sources) == []
```

**Every prereg function has a CPU test** (`tests/test_phase40_prereg.py:889-902`):
```python
def test_census_every_phase40_prereg_function_has_a_cpu_test(tmp_path):
    ...
    assert _untested_functions("phase40_prereg", source, test_source) == []
    planted = source + '\n\ndef planted_untested():\n    """Planted."""\n'
    copied = _planted(tmp_path, source, planted, "untested.py")
    assert _untested_functions("phase40_prereg", copied, test_source) == ["planted_untested"]
```
Applies to every module-level `def` in `phase41_prereg.py`, private helpers included (`_prove`, `_prove_entry`, `_approved`, ...).

**No skips** (`tests/test_phase40_prereg.py:882-886`): `_skip_failures(source) == []` plus a planted RED. Required because a host-gated skip moves the ubuntu skip pin in `tests/test_phase25_venue.py` (memory `execute-phase-gates-in-personacore`).

**No checkpoint opened at import** — audit-hook subprocess probe (`tests/test_phase38_sizes_prereg.py:112-146`).

---

### `tests/test_phase41_floors_prereg.py`

**Analog:** `tests/test_phase38_sizes_prereg.py` (245 lines), test by test:
- values read from committed records (`:63-76`), with `assert sizes.MINTING_RECORD in sizes._DERIVATION["source"]` pattern for every consumed path;
- imports-only allowlist via AST (`:88-109`);
- import opens no checkpoint (`:112-146`) — required because `tests/test_phase36_caps.py:283` exec's every tracked fill file on ubuntu CI;
- ordering: every declared input precedes the file (`:163-167`), file frozen before every other phase41 record (`:170-174`), this test file first-added before scoring records (`:177-183`), all with a NON-VACUITY natural-RED leg;
- nothing typed via `ast.Constant` walk (`:190-206`);
- no skips (`:241-245`).
Imports `_first_add, _strictly_before` from the Phase 41 prereg test file (as `:42` imports them from `test_phase38_prereg`).

---

### `tests/test_phase41_erasure.py`

**Analog:** `tests/test_phase40_noise.py` (3243 lines) + `tests/test_phase37_routes.py:309-417`.

- Imports block (`tests/test_phase40_noise.py:10-61`): plain `import phase41_erasure` ("never aliased — _untested_functions counts by name", `:53`).
- Fake rigs: `_tmp_rig` (`:643-663`, explicit tmp ledger/heartbeat, `device="cpu"`, `git_sha` stubbed) and `_real_root_rig` (`:666-698`, monkeypatches `_ROOT`, `phase36_ledger._ROOT/LEDGER_PATH/HEARTBEAT_PATH`, `run_inputs`, `phase36_caps.check_unit_caps`, `_device -> "mps"`).
- `run()` with no args on a real-root rig (`:1647-1663`) — the dry-run-hides-unwired-driver guard.
- `main` dispatch with `inspect.signature(real).bind` (`:2830-2841`), bad argv (`:2844-2849`), CLI non-zero (`:2852-2856`).
- `_driver_failures` AST gate: no `os.replace`, no `inject_lora` (`:2959-2986`).
- `test_driver_binds_no_slot_name` (`:2989-2993`).
- Plist test (`:603-635`).
- Pin byte-unchanged leg (ERASE-08): reuse `tests/test_phase37_routes.py:317-332` (`_PIN_ANCHOR = "3ba3e2c"`, probe digest from `results/phase36_probe_e1.json`).
- Forbidden-call AST gate: copy `_call_failures` (`tests/test_phase37_routes.py:337-400`) over `scripts/phase41_*.py`, but ADJUST `_FORBIDDEN_CALLEES` (`:337-349`): the Phase 41 driver legitimately calls `draw_all` (K16 reader), `reference_set_for_calibration` (greedy calibration twin, Pattern 7) and `write_text` (report). Keep `erasure_succeeded` (v3.0 (c), replaced by ERASE-09), `inject_lora`, `retention_perplexity`, `_selected_components`, `os.replace`, `open`, `pin._cmd_*`, `phase19_run.report`, and "`run_erasure_arm` without `record_path`".
- Feed `emit` one real committed producer record: `results/erasure_kstar_arm_k064.json` (A2, k = 64) as a K48 stand-in (RESEARCH Pitfall 13).

---

## Census / Guard Registers a New File Must Satisfy

| Guard | Location | What the new file must do |
|---|---|---|
| `train_arm(` call-site register | `tests/test_phase23_resume.py:60-170` (register), `:279` (`grep -rn "train_arm(" --include=*.py scripts tests`), `:286-299` (total + per-file counts), `:339-340` (tripwire sum `8 + 1 + 1 + 1 + 1 + 2 + 1 + 1 + 1 + 1 + 1`; history comment `:304-336`) | Add ONE tuple after the Phase 40 entry (`:119-124`): `("scripts/phase41_erasure.py", "call", "train_calibration_adapter (Phase 41's E1 calibration adapters, ERASE-06)")`; append `+ 1` to the sum at `:340` and extend its message and the numbered history comment (`TWENTY from 41-xx ...`). Every `train_arm(` text hit counts, including docstrings and test prose: keep the driver at exactly one, and write no `train_arm(` in `tests/test_phase41_*.py` (or register each). No `resume_from`, so `_RESUME_PASSERS` (`:186-200`) is untouched. |
| draw_all census | `tests/test_phase14_scoring.py:728-772`; exemptions `DRAW_ALL_ASSERTED_BY` `:696-698` | The K16 reader that calls `recall.draw_all` must also call `recall.assert_no_value_in_prompt` in the same function, carry no decorator, and not be named `_skip*`. Then no register edit is needed. |
| ISO-06 `inject_lora` allowlists | `tests/test_lora_inject.py:261-293` (`INJECT_LORA_CONSUMERS` / `_PRODUCERS`, hard equality) | Never call or import `inject_lora`; load through `phase14_recall.load_adapted_model` (already a listed consumer). No register edit. |
| `os.replace` census | `tests/test_phase25_driver.py:340-365` (`writers == {"phase25_run.py", "phase25_record.py"}`, scans `scripts/*.py` + `src/**`) | Use `phase25_run.atomic_write_json`; `shutil.move` is fine (Phase 40 uses it). |
| `== 10` wall | `tests/test_phase21_sc5.py:170-...` (patterns include `(?:==|!=)\s*10(?![0-9_])` over tests) | No `== 10` / `!= 10` literal anywhere in the new tests or scripts. |
| K menu | `mitigation_gate.K_RUNGS == (48, 24, 16, 8)` (`tests/test_phase20_prereg.py:1953`, `tests/test_phase23_budget.py:1256`) | Read K from `phase35_prereg.CURVE_K` / `FULL_FIDELITY_K` (`scripts/phase35_prereg.py:347-348`) or `grid["read_k"]`/`["confirm_k"]`; any K fixture value must be on the menu. Not a file-scanning census. |
| Slot census | `tests/test_phase35_prereg.py:2166-2269` (`_slot_census_failures`) | Fills only in `scripts/phase41_*prereg.py` (`owner_prereg_glob`, `:847`), each slot once, bound to its upper-cased name; driver binds no slot name. |
| Fill-order legs (a)/(b)/(c) | `tests/test_phase35_prereg.py:2475-2539` (`_slot_ordering_failures`); real-repo leg `:2557-2560`; planted greens `g41` `:2590-2596`; reds `c41` `:2628-2632`, `a41` `:2649-2659`, `b7_41` `:2679-2702` | Commit order: `phase41_prereg.py` (+ its test) -> 4 `results/phase41_calibration_*.json` + 4 `results/phase41_band_inputs_*.json` -> `phase41_floors_prereg.py` -> any other `results/phase41_*`. Raw prep outputs under `data/phase41_e1/` only. Fill file 1 is frozen for good after the first calibration record (corrections = dated continuations). |
| Every prereg function has a CPU test | `tests/test_phase36_prereg.py:418-438` (`_untested_functions(module_name, ...)`), applied per phase as in `tests/test_phase40_prereg.py:889-902` | `tests/test_phase41_prereg.py` calls every module-level def of `phase41_prereg` as `phase41_prereg.<def>(...)`. Same for the driver (`tests/test_phase40_noise.py:61` imports the helper). |
| Owner-cap test | `tests/test_phase36_caps.py:270-292` (exec's every tracked fill file via `spec_from_file_location`) | Both fill files import cleanly on a CPU-only clone, open no `checkpoints/` file, and the grid's 5 checkpoints fit `unit_caps.E1.checkpoints_per_cell`. |
| Pin byte-unchanged | `tests/test_phase37_routes.py:317-332` | Never edit `scripts/phase19_erasure.py` or `scripts/erasure_gate.py`; never monkeypatch the pin in production code. |
| Skip pin | `tests/test_phase25_venue.py` (ubuntu skip totals, e.g. `:329`) | Zero skips in all three new test files; adapter-digest checks live in driver preflight with fakes in tests. |

## Shared Patterns

### `_prove` refusals (never `assert`)
**Source:** `scripts/phase40_prereg.py:67-70`, `scripts/phase40_noise.py:93-95`, `scripts/phase37_routes.py:41-43`
**Apply to:** all three new scripts, each with its own `[module]` prefix.

### Write-once + atomic writes
**Source:** `scripts/phase40_noise.py:181-185` (`_write_once` -> `phase25_run.atomic_write_json`); emit/report refusal text `:1467-1471`, `:2014-2018`.
**Apply to:** every record and report the driver writes.

### Ledger attempt + heartbeat
**Source:** `scripts/phase40_noise.py:999-1107`; API `scripts/phase36_ledger.py:194` (`append`), `:315` (`spent`), `:400` (`require_launch`), `:76` (`run_id`).
**Apply to:** each prep unit and each cell (one attempt, one `end` line naming one record).

### Provenance block
**Source:** `scripts/phase40_noise.py:78-86` (`RUN_PROVENANCE_KEYS`), `:1082-1093`.
**Apply to:** every calibration, band-input and cell record (the ledger reads the clock from it).

### Planted-RED non-vacuity
**Source:** `tests/test_phase29_prereg.py:526` (`_planted`), used at `tests/test_phase38_sizes_prereg.py:206, 236, 245`.
**Apply to:** every AST gate and ancestry test in the three new test files (natural RED preferred, memory `natural-red-beats-planted-red`).

## No Analog Found

| File / part | Role | Data Flow | Reason |
|---|---|---|---|
| Taylor gradient ordering inside `scripts/phase41_erasure.py` | service function | transform (forward+backward) | No backward pass on the value-span NLL exists; `span_nll_from_ids` is `no_grad` (`scripts/phase18_extraction.py:1084`). Use RESEARCH §Pattern 2 (`taylor_scores`), with the D-02 value-equality check against `pin.value_span_nll_mean`. |
| Per-target (a)/(b)/(c) verdict combiner in `scripts/phase41_prereg.py` | pure function | transform | Pin (b) helpers and `phase37_routes.rederive` are hard-wired to `TARGET_SLOT = "pet_name"` and v3.0 (c); `erasure_gate.erasure_succeeded` uses the one-sided cap. Compose from `erasure_gate.wilson_upper_bound`, `phase40_prereg.slot_rows`, `E1_CONDITION_B_MARGIN`, `E1_CONDITION_C_BAND_INPUTS` (RESEARCH §Pattern 8). |
| E1-share pause (D-23) | pure function + driver check | request-response | `require_launch` only knows stops (a)/(b)/(c) at 1.5x / 90 h / projection (`scripts/phase36_ledger.py:341-367`). New arithmetic over `phase36_ledger.spent(fronts=("E1",))` and `results/phase36_budget.json::front_hours.E1`. |

## Metadata

**Analog search scope:** `scripts/phase19_erasure.py`, `scripts/phase23_run.py`, `scripts/phase35_prereg.py`, `scripts/phase36_caps.py`, `scripts/phase36_ledger.py`, `scripts/phase37_routes.py`, `scripts/phase38_prereg.py`, `scripts/phase38_sizes_prereg.py`, `scripts/phase40_prereg.py`, `scripts/phase40_noise.py`, `scripts/erasure_kstar_run.py`, `artifacts/*.plist`, `tests/test_phase{14_scoring,21_sc5,23_resume,25_driver,35_prereg,36_caps,36_prereg,37_routes,38_sizes_prereg,40_noise,40_prereg}.py`, `tests/test_lora_inject.py`.
**Files scanned:** 24
**Pattern extraction date:** 2026-10-08
