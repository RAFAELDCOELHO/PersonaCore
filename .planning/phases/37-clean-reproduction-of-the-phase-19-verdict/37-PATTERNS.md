# Phase 37: Clean Reproduction of the Phase 19 Verdict - Pattern Map

**Mapped:** 2026-10-03
**Files analyzed:** 12 (4 scripts, 1 plist, 4 tests, 3 records)
**Analogs found:** 12 / 12. Every line reference below was re-run with `grep -n` / `sed -n` on HEAD `d710181`.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `scripts/phase37_prereg.py` | config (pre-registration + slot fill) | transform (records -> frozen entries) | `scripts/phase36_prereg.py` (entries, `_prove_entry`, sys.path block) + `scripts/phase36_budget_prereg.py:75-82` (the census-conformant fill) | exact |
| `scripts/phase37_routes.py` | utility (routing A–E + `rederive`) | transform (record -> verdict inputs) | `scripts/phase19_run.py:2771-2889` (`report()` A–D inline routing) + `:885-941` (`target_ablate`, E) | exact (logic), must be split into named functions |
| `scripts/phase37_r1a.py` | CLI driver (CPU) | file-I/O, write-once record | `scripts/erasure_kstar_run.py` (`summarize`, `_sha256`, `_prove`, `main`) + `scripts/phase36_probe.py:1170-1221` (`_emit_target`, `_write_record`) | exact |
| `scripts/phase37_r1b.py` | CLI driver (MPS) | batch + event-driven (ledger/heartbeat) | `scripts/erasure_kstar_run.py:109-143` (`measure`) + `scripts/phase36_probe.py:357-417` (`run_front`) | exact |
| `artifacts/com.personacore.phase37.r1b.plist` | config (LaunchAgent) | — | `artifacts/com.personacore.phase36.probe.plist` | exact |
| `tests/test_phase37_prereg.py` | test | ancestry/AST | `tests/test_phase36_prereg.py` | exact |
| `tests/test_phase37_routes.py` | test | natural-red tripwires + AST | `tests/test_phase19_correction.py:264-325`, `tests/test_phase19_erasure.py:3920-3970`, `:4408-4440` | exact |
| `tests/test_phase37_r1a.py` | test | committed-record + write-once | `tests/test_erasure_kstar_run.py:84-106, 178-209` | exact |
| `tests/test_phase37_r1b.py` | test | monkeypatched driver, tmp ledger | `tests/test_phase36_probe.py:209-310` (run_front), `:1769-1798` (plist) | exact |
| `results/phase37_r1a.json` | record | write-once | `results/erasure_kstar_summary.json` shape via `phase36_probe._write_record` provenance block | role-match |
| `results/phase37_r1b_arm.json` | record (pin `ARM_RECORD_KEYS`) | written by `pin.run_erasure_arm(record_path=...)` | `results/erasure_kstar_arm_k008.json` (same producer) | exact |
| `results/phase37_r1b.json` | record | write-once, ledger end line names it | `results/phase36_probe_*.json` (`provenance.run` block) | exact |

---

## Pattern Assignments

### `scripts/phase37_prereg.py` (config, torch-free)

**Analog:** `scripts/phase36_prereg.py` (517 lines) for the body; `scripts/phase36_budget_prereg.py:75-82` for the fill.

**Header + sys.path + plain import** (`phase36_prereg.py:18-44`):
```python
import collections.abc
import fnmatch
import math
import pathlib
import sys
import types

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_SRC = str(_REPO_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import phase25_record  # noqa: E402  (needs the sys.path insert above; torch-free)
import phase35_prereg  # noqa: E402  (same; torch-free)

# At this commit no `results/phase36_*` file existed, tracked or untracked.
COMMITTED = "2026-10-02"
RECORDS_AT_COMMIT = 0
```
For Phase 37: import `phase19_floor` (torch-free; `EVIDENCE_ARTIFACT` at `phase19_floor.py:171-175`) and `phase35_prereg`. **Never** import `phase19_erasure` (it pulls in torch). The research's measured torch-free path: read `results/phase19_noise_floors.json` and `results/phase19_arm_erased.json` with `json`.

**`_prove` + entry schema by reference** (`phase36_prereg.py:47-96`):
```python
def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase36_prereg] {message}")

ENTRY_FIELDS = phase35_prereg.ENTRY_FIELDS
KINDS = phase35_prereg.KINDS
FORBIDDEN_PHRASE = phase35_prereg.FORBIDDEN_PHRASE

def _prove_entry(name, entry):
    """Refuse any entry that is not exactly the four fields with a known kind."""
    ...  # lines 62-96: mapping check, proposer/adopted_by ban, exact fields, kind in KINDS,
         # non-empty str derivation/source, FORBIDDEN_PHRASE ban
```
Copy `_prove_entry` (lines 62-96) or import it from `phase36_prereg` (public module, not banned). **Never** call `phase35_prereg._prove_entry` / `_prove` / `_REPO_ROOT`: the census bans any `phase35_prereg._*` attribute (`tests/test_phase35_prereg.py:2217-2219`).

**Record-path derivation from `V6_RESULT_PATHS`** (`phase36_prereg.py:99-118`):
```python
PROBE_GLOB = next(
    p for p in phase35_prereg.V6_RESULT_PATHS if p.startswith("results/phase36_probe_")
)
...
for _path in PROBE_RECORDS:
    _prove(fnmatch.fnmatch(_path, PROBE_GLOB), f"{_path} does not match {PROBE_GLOB}")
```
Phase 37's glob is the literal member `"results/phase37_*"` (`phase35_prereg.py:320`). Derive `R1A_RECORD`, `R1B_RECORD`, `R1B_ARM_RECORD` and prove each `fnmatch`es it.

**Frozen entries** (`phase36_prereg.py:154-164, 462-472`):
```python
_ENTRIES = {
    "divergence_tolerance": {
        "value": 0.25,
        "derivation": ("D-02: ..."),
        "kind": "preference",
        "source": f"{_CONTEXT.format('02')}; {_CONTEXT.format('04')}",
    },
    ...
}
ENTRIES = types.MappingProxyType(
    {name: types.MappingProxyType(entry) for name, entry in _ENTRIES.items()}
)

def _prove_entries():
    for name, entry in ENTRIES.items():
        _prove_entry(name, entry)

_prove_entries()
```
Keep the name `_ENTRIES` at module level: `tests/test_phase36_prereg.py:106-133` (`_entries_node`, `_entry_string_failures`) finds it by that exact name.

**The fill — census-conformant shape** (`phase36_budget_prereg.py:75-82`):
```python
V6_BUDGET_AND_STOP_LINE = phase35_prereg.fill(
    "v6_budget_and_stop_line",
    front_hours=_CHOSEN["front_hours"],
    ...
)
```
Phase 37 binding name must be exactly `R1B_TOLERANCE_AND_REPLICATED` (slot.upper(); `tests/test_phase35_prereg.py:2190-2195`). The rule's signature is `_rule_r1b_tolerance_and_replicated(*, tolerance, replicated_definition)` (`phase35_prereg.py:1191`): no `input_records`, no `derivation` (slot registry `phase35_prereg.py:1798-1802`, `"input_records": ()`). It accepts a **subset** of `R1A_ASSERTIONS` keys (`:1195-1197`), so the module must `_prove(set(R1B_TOLERANCE_AND_REPLICATED["tolerance"]) == set(phase35_prereg.R1A_ASSERTIONS), ...)`.

**`R1A_ASSERTIONS` keys** (`phase35_prereg.py:453-461`): `"k": 78`, `"target_correct": (0, 27)`, `"nontargets_beyond_margin": (7, 7)`, `"destroyed_pct": 77.6370113463966`. `MARGIN_K = erasure_gate.MARGIN_K` at `phase35_prereg.py:350` (public; use `phase35_prereg.MARGIN_K`).

**destroyed_pct tolerance, D-02 operation order** (research P10): `phase35_prereg.MARGIN_K * floor / g0 * 100` (gives `...365`; other orders give `...364`). g0 is computed exactly as `r1a_rederive` does at `phase35_prereg.py:477-478`:
```python
pre, post = record["pre_erasure"]["dialogue_ppl"], record["dialogue_ppl"]
g0 = pre["adapter_on"] - pre["adapter_off"]
```

---

### `scripts/phase37_routes.py` (utility, imports the pin, CPU)

**Analog:** `scripts/phase19_run.py` `report()` (`:2771-2889`) for A–D; `target_ablate()` (`:885-941`) for E. **Do not call `report()`**: it writes `pin.ERASURE_REPORT_PATH.write_text(full, ...)` at `phase19_run.py:3007` with no refusal.

**Imports** (`erasure_kstar_run.py:26-38`, the wrapper convention):
```python
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import erasure_kstar_prereg as prereg  # noqa: E402
import phase19_erasure as pin  # noqa: E402
import phase19_floor as floor  # noqa: E402
import phase19_run as p19run  # noqa: E402  — for _pooled_rows only (defect C's recovery)
```

**Record loading + tiers** (`phase19_run.py:2809-2826`):
```python
erased, replicate = arms["erased"], arms["replicate"]
phase18 = json.loads(pin.PHASE18_ARM_RECORD_PATH.read_text(encoding="utf-8"))
...
correction = json.loads(CALIBRATION_CORRECTION_PATH.read_text(encoding="utf-8"))

values = {f.id: f.value for f in factset.LOCKED_FACTS + factset.SOFT_TIER_FACTS}
family, budget = erased["config"]["attack_family"], erased["config"]["k"]
tiers = tuple(sorted({d["tier"] for d in erased["draws"] if d["family"] == family}))
```

**Route C** (`phase19_run.py:2828-2834`; `_pooled_rows` defined at `:620`):
```python
pre = _pooled_rows(phase18["draws"], values, family, tiers)
post = _pooled_rows(erased["draws"], values, family, tiers)
target_id = pin.target_fact_id(erased["draws"])
target_row, pre_target = post[target_id], pre[target_id]
deltas = pin.nontarget_deltas(pin.nontarget_rows(pre), pin.nontarget_rows(post))
```

**(b) floor re-derived from the replicate arm — D-13** (`phase19_run.py:2836-2845`):
```python
rep_family = replicate["config"]["attack_family"]
rep_tiers = tuple(sorted({d["tier"] for d in replicate["draws"] if d["family"] == rep_family}))
noise_floor = pin.nontarget_noise_floor(
    pin.nontarget_deltas(
        pin.nontarget_rows(_pooled_rows(phase18["draws"], values, rep_family, rep_tiers)),
        pin.nontarget_rows(_pooled_rows(replicate["draws"], values, rep_family, rep_tiers)),
    )
)
dialogue_floor = pin.dialogue_floor_from_record()
```

**Route B** (`phase19_run.py:2849-2864` — inline today; wrap as `route_b()`):
```python
cal_rate = correction["calibration_rate"]
for condition, message in (
    (correction["governs"] == "corrected_target_floor", ...),
    (pin.lock_erasure_floor(cal_rate) == floor.TARGET_FLOOR, ...),
```
Unrouted B = `pin.lock_erasure_floor(pin._calibration_rate())` (`phase19_erasure.py:920`, `:3850`) -> `0.2`.

**Route A** (`phase19_run.py:2876-2879`; `_order_normalised` at `:1290-1308`):
```python
flag_on_disk = pin.zero_results_have_nll(erased)
normalised = _order_normalised(erased)
flag_normalised = pin.zero_results_have_nll(normalised)
```

**The one verdict call, A–D routed** (`phase19_run.py:2883-2892`):
```python
verdict = pin.render_verdict(
    target_successes=target_row["n_answerable"],
    target_questions=target_row["n_questions"],
    target_floor=floor.TARGET_FLOOR,
    nontarget_deltas=deltas,
    nontarget_noise_floor=floor.NONTARGET_NOISE_FLOOR,
    dialogue_ppl=erased["dialogue_ppl"]["adapter_on"],
    dialogue_ppl_noise_floor=dialogue_floor,
    # `retention_perplexity` returns `(ppl, n)`; the gate compares a SCALAR.
    retention_ppl=erased["retention_ppl"][0],        # <- route D
    zero_results_have_nll=flag_normalised,           # <- route A
)
```
`render_verdict(**gate_inputs)` is at `phase19_erasure.py:1935`. Never call `erasure_succeeded` directly.

**Route E / ERASE-08 wrapper — `target_ablate` call shape** (`phase19_run.py:912-941`):
```python
taught = {f.slot: f.value for f in factset.LOCKED_FACTS}
references = extraction.reference_set_for(pin.TARGET_SLOT)
twin = pin.reference_set_for_calibration(pin.TARGET_SLOT, target)
...
collateral = {
    slot: (taught[slot], extraction.reference_set_for(slot)) for slot in extraction.CORE_SLOTS
}
started = time.time()
chosen = pin.select_ablation_prefix(
    model, tok, device, artifact,
    slot=target.slot, value=target.value,
    references=references, collateral=collateral,
    dialogue_ppl=lambda: pin.dialogue_ppl_pair(model, device, forbid),
)
```
Pin signature (`phase19_erasure.py:2443-2445`): `select_ablation_prefix(model, tok, device, artifact, *, slot, value, references, collateral, dialogue_ppl)` returns `{k, stopped, cap, ordered, intact_nll, curve}`. `reference_set_for` is `phase18_extraction.py:1159`; `CORE_SLOTS` `:1467`. The pin's unrouted path hard-codes the twin at `phase19_erasure.py:3576` inside `_selected_components` (`:3558`); do not monkeypatch the pin.

---

### `scripts/phase37_r1a.py` (CPU driver, write-once record)

**Analog:** `scripts/erasure_kstar_run.py` (`summarize` `:225-287`, `main` `:290-300`) + `scripts/phase36_probe.py` `_emit_target`/`_write_record` (`:1170-1221`).

**Local helpers** (`erasure_kstar_run.py:51-57`):
```python
def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[erasure_kstar_run] {message}")

def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
```

**Write-once + dirty refusal with self-exclude** (`phase36_probe.py:1170-1192`):
```python
def _emit_target(out_path):
    """Write-once: overwrite refusal FIRST, dirty-tree refusal SECOND. Returns the absolute path."""
    out_path = pathlib.Path(out_path)
    if not out_path.is_absolute():
        out_path = _GIT_ROOT / out_path
    _prove(not out_path.exists(), f"{out_path} exists — REFUSING to overwrite it. ...")
    pathspec = ("scripts", "src", "results")
    if out_path.is_relative_to(_GIT_ROOT):
        pathspec += (f":(exclude){out_path.relative_to(_GIT_ROOT).as_posix()}",)
    refuse_if_dirty(who="phase36_probe", detail=(...), pathspec=pathspec, cwd=_GIT_ROOT)
    return out_path
```
`refuse_if_dirty(*, who, detail, pathspec=(), cwd=None)` is `src/personacore/provenance.py:47`; `git_sha(default="unknown")` is `:28`.

**Provenance block + atomic write** (`phase36_probe.py:1205-1221`):
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
prove_no_reading(record)
phase25_run.atomic_write_json(out_path, record)
```
`atomic_write_json(path, blob)` is `scripts/phase25_run.py:118`. R1a's record: `device` is `cpu`, so `test_every_tracked_v6_mps_record_has_a_launch_line` does not require a ledger line for it (`tests/test_phase36_ledger.py:722-733` only checks `device == "mps"`).

**Input SHA list** (D-10, D-13): compute with `_sha256` at write time over `results/phase19_arm_erased.json`, `results/phase18_arm_adapter-on.json`, `results/phase19_noise_floors.json`, `results/phase19_calibration_correction.json`, `results/phase19_arm_replicate.json` (+ any other record read). `results/phase19_dialogue_floor.json` if `pin.dialogue_floor_from_record()` reads it (`phase19_erasure.py:2595`).

**Recorded verdict comparison:** `scripts/_verdict.py:27` `recorded_verdict(text)` (the one anchored `## Verdict` read; `phase19_run.py:179` imports it).

**CLI** (`erasure_kstar_run.py:290-300`):
```python
def main(argv):
    if len(argv) == 2 and argv[0] == "measure":
        measure(int(argv[1]))
    elif argv == ["summarize"]:
        summarize()
    else:
        raise SystemExit(__doc__)

if __name__ == "__main__":
    main(sys.argv[1:])
```

---

### `scripts/phase37_r1b.py` (MPS driver)

**Analog:** `scripts/erasure_kstar_run.py:109-143` (`measure`) for the pin call; `scripts/phase36_probe.py:357-417` (`run_front`) for ledger + heartbeat.

**Refuse dirty, check adapter SHA vs the curve, explicit `record_path`** (`erasure_kstar_run.py:111-143`):
```python
_prove(not record_path.exists(), f"{record_path} exists — recorded evidence, no force flag")
from personacore.provenance import refuse_if_dirty
refuse_if_dirty(who="erasure_kstar_run", detail=(...), pathspec=RULE_PATHSPEC, cwd=_ROOT)

import phase14_recall as recall
from personacore.preflight import preflight_device

curve = _curve()
sha_before = _sha256(recall.ADAPTER_PATH)
_prove(sha_before == curve["adapter_in_sha256"], f"{recall.ADAPTER_PATH} is not the adapter ...")
components = [tuple(address) for address in curve["ordered_prefix"][:k]]
device = preflight_device(strict=True)["device"]
pin.run_erasure_arm("erased", device, components=components, record_path=record_path)
_prove(_sha256(recall.ADAPTER_PATH) == sha_before, f"{recall.ADAPTER_PATH} changed during the run ...")
```
`run_erasure_arm(arm, device, *, corpus_path=..., adapter_path=None, components=(), record_path=None, seed_stride=None)` is `phase19_erasure.py:2732-2741`. `RULE_PATHSPEC` at `erasure_kstar_run.py:41` deliberately omits `results/` (Pitfall 6). Model load for the sweep: `recall.load_adapted_model(device, adapter_path)` (`phase14_recall.py:712`; returns `model, _cfg, tok, forbid, artifact` per `phase19_run.py:910`). `ADAPTER_PATH` is `phase14_recall.py:84`.

**Committed-curve checks to reuse** (`erasure_kstar_run.py:60-75`, `_curve()`): slot, `k`, `stopped`, `len(ordered_prefix)`, `reference_set_size == 8`. R1b's D-07 comparator reads `curve["ordered_prefix"]` and `curve["k"]`.

**Ledger start, beat-once, thread, end** (`phase36_probe.py:379-410`):
```python
rid = phase36_ledger.run_id(36, "probes", front)
phase36_ledger.append("start", run_id=rid, phase=36, front="probes", ledger_path=ledger_path)
state = {"point": rid, "stage": "start", "shape": None, "draw_index": None}
# B1: the thread's first beat comes only after wait(60) ... beat once now.
phase25_run.beat(heartbeat_path, **state)
stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
started_utc, started = _now(), time.monotonic()
try:
    ...
    state.update(stage="done", shape=None, draw_index=None)
finally:
    stop.set()
    thread.join()
phase36_ledger.append("end", run_id=rid, phase=36, front="probes", record=record, ledger_path=ledger_path)
```
For Phase 37: `phase36_ledger.require_launch("R1b")` first (`phase36_ledger.py:400`, writes nothing), then `run_id(37, "R1b", "replica")` (`:76-78` -> `"v6/37/R1b/replica"`), `append(..., phase=37, front="R1b")` (`:194`), end line `record="results/phase37_r1b.json"`. `HEARTBEAT_PATH` is `phase36_ledger.py:44`; `beat` `phase25_run.py:298`; `start_heartbeat` `phase25_run.py:350`. The record the end line names must carry `provenance.run.{started_utc, finished_utc}` (`phase36_ledger.py:67` `RECORD_CLOCK = ("provenance", "run")`, read in `_closed_row` `:279-300`).

**Record build** (copy the `_write_record` provenance block above and `erasure_kstar_run._checkpoint_block` `:146-218` for per-slot non-target deltas, `by_slot = dict(zip(pin.GATED_NONTARGET_SLOTS, deltas, strict=True))` at `:166` — the D-12 per-fact context).

---

### `artifacts/com.personacore.phase37.r1b.plist`

**Analog:** `artifacts/com.personacore.phase36.probe.plist` (61 lines). Copy verbatim, change `Label` (`:17`), `ProgramArguments[3..]` (`:33-36`), `StandardOutPath`/`StandardErrorPath` (`:43,45`) to `logs/phase37_r1b.{out,err}`. Keep:
```xml
<key>KeepAlive</key>
<false/>
<key>RunAtLoad</key>
<false/>
<key>ProgramArguments</key>
<array>
  <string>/usr/bin/caffeinate</string>
  <string>-dims</string>
  <string>/Users/juliorcoelho/PersonaCore/.venv/bin/python</string>
  <string>/Users/juliorcoelho/PersonaCore/scripts/phase36_probe.py</string>
  ...
</array>
<key>EnvironmentVariables</key>
<dict>
  <key>PERSONACORE_SWEEP_ACTIVE</key><string>1</string>
  <key>PATH</key><string>/usr/bin:/bin:/usr/sbin:/sbin</string>
  <key>PYTHONUNBUFFERED</key><string>1</string>
</dict>
```

---

### `tests/test_phase37_prereg.py`

**Analog:** `tests/test_phase36_prereg.py` (465 lines).

**Imports + shared helpers** (`test_phase36_prereg.py:16-46`):
```python
_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
_SRC = _ROOT / "src"
...
_TESTS = str(_ROOT / "tests")
if _TESTS not in sys.path:
    sys.path.insert(0, _TESTS)

import phase35_prereg  # noqa: E402  (scripts/ is not a package)
import phase36_prereg  # noqa: E402  (same)

from test_phase29_prereg import _assert_frozen_before, _git, _planted  # noqa: E402
from test_phase35_prereg import _insert_at, _slot_census_failures  # noqa: E402
```
Helper locations: `_git` `tests/test_phase29_prereg.py:52`, `_assert_frozen_before` `:69-108`, `_planted` `:526`; `_slot_census_failures` `tests/test_phase35_prereg.py:2166`, `_literal_failures` `:749`, `_slot_ordering_failures` `:2475`; `_skip_failures` `tests/test_phase36_prereg.py:396`, `_untested_functions` `:418`.

**Ancestry + non-vacuity** (`test_phase36_prereg.py:52-66`):
```python
def test_phase36_prereg_is_frozen_before_every_phase36_record():
    tracked = sorted(_git("ls-files", "results/phase36_*").split())
    _assert_frozen_before(PREREG, tracked)
    # NON-VACUITY (natural RED): the v6.0 pre-registration was added before this one existed.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(PREREG, ["scripts/phase35_prereg.py"])

def test_records_at_commit_is_true_at_the_first_commit():
    first = _git("log", "--format=%H", "--", PREREG).split()[-1]
    at_first = _git("ls-tree", "-r", "--name-only", first, "--", "results/").split()
    assert at_first, "meta-guard: ..."
    assert not [p for p in at_first if p.startswith("results/phase36_")]
    assert phase36_prereg.RECORDS_AT_COMMIT == 0
```

**Four-field entries + refusals** (`:73-103`), **no proposer AST** (`:106-176`), **torch-free subprocess probe** (`:372-383`, `_HEAVY` tuple), **slot census over the phase glob** (`:386-391`):
```python
def test_phase36_scripts_pass_the_slot_census():
    paths = sorted(_SCRIPTS.glob("phase36_*.py"))
    assert paths, "meta-guard: no scripts/phase36_*.py, the census would be vacuous"
    sources = [(p.relative_to(_ROOT).as_posix(), p.read_text(encoding="utf-8")) for p in paths]
    assert _slot_census_failures(sources) == []
```
**No skips** (`:406-410`) and **every function called** (`:442-465`). Add the destroyed_pct literal scan with `_literal_failures(source, seeds=set(), floats={tol}, names=set())` (`tests/test_phase35_prereg.py:749-765`).

---

### `tests/test_phase37_routes.py`

**Analogs:** `tests/test_phase19_correction.py:264-325` (A/B/C tripwires on committed records), `tests/test_phase19_erasure.py:3920-3970` (E tripwire), `:4408-4440` (driver verdict AST scan using `_call_sites(callee, source)` defined at `tests/test_phase19_erasure.py:2011`).

**Tripwire style** (`test_phase19_correction.py:274-282, 310-316`):
```python
import phase19_erasure as pin
record = json.loads((_ROOT / ARM_RECORD_REL).read_text(encoding="utf-8"))
# A — order-sensitive comparison.
assert pin.zero_results_have_nll(record) is False, ("defect A is gone: ...")
...
assert pin._calibration_rate() == sum(r["n_answerable"] for r in rows.values()) / sum(
    r["n_questions"] for r in rows.values()
)
```
**E tripwire** (`test_phase19_erasure.py:3943-3956`):
```python
curve = json.loads((_ROOT / "results" / "phase19_collateral_curve.json").read_text(encoding="utf-8"))
target = {fact.slot: fact for fact in facts.LOCKED_FACTS}[erasure.TARGET_SLOT]
published = extraction.reference_set_for(erasure.TARGET_SLOT)
twin = erasure.reference_set_for_calibration(erasure.TARGET_SLOT, target)
assert len(published) != len(twin)
assert curve["reference_set_size"] == len(published)
```
**AST verdict gate** (`test_phase19_erasure.py:4417-4429`): `_call_sites("erasure_succeeded", src) == []`; `render_verdict` sites == `[<named caller>]`; plus a non-vacuity mutant.

**Byte-unchanged anchors (measured now):** `sha256(scripts/phase19_erasure.py)` == `results/phase36_probe_e1.json` `provenance.module_sha256["scripts/phase19_erasure.py"]` == `c407246de3c470094ab0bdd868961b7b1c22529c5e00522fec67c3852cb6e303`, last commit `3ba3e2c`. `scripts/erasure_gate.py` is NOT in that record (`None`); sha256 `a79d317ade89e7d37c08f14fe03397ebf79c4824dccd09aeda760ffed93facde`, last commit `23a830c`. Assert via `git diff --quiet <sha> HEAD -- <path>` + computed hash, not a typed hash.

---

### `tests/test_phase37_r1a.py`

**Analog:** `tests/test_erasure_kstar_run.py`.

**Refusal tests with monkeypatched boundaries** (`test_erasure_kstar_run.py:84-106`):
```python
def test_measure_holds_only_the_rule_and_the_driver_to_a_clean_tree(run, monkeypatch, tmp_path):
    seen = {}
    def dirty(**kwargs):
        seen.update(kwargs)
        raise SystemExit("dirty tree")
    monkeypatch.setattr(run, "arm_path", lambda k: tmp_path / f"k{k}.json")
    monkeypatch.setattr("personacore.provenance.refuse_if_dirty", dirty)
    monkeypatch.setattr(run.pin, "run_erasure_arm", _boom)
    with pytest.raises(SystemExit, match="dirty tree"):
        run.measure(8)
    assert sorted(seen["pathspec"]) == sorted(run.RULE_PATHSPEC)
```
Note: kstar imports `refuse_if_dirty` lazily inside the function, which is why `monkeypatch.setattr("personacore.provenance.refuse_if_dirty", ...)` works. If `phase37_r1a` imports it at module level (as `phase36_probe` does), patch the module attribute instead.

**Committed-record reproduction** (`test_erasure_kstar_run.py:178-209`): load `pin.arm_record_path("erased")`, run the block builder, assert `0/27`, `7` over margin, destroyed within `1e-12`, and re-derive every per-slot delta from `_pooled_rows`.

**Forbidden-name AST scan** (`test_erasure_kstar_run.py:18-49, 52-66`): `FORBIDDEN` set + `_forbidden_hits(source)` + parametrized bypass snippets. For Phase 37: forbid `report`-attribute calls on the `phase19_run` binding, `_cmd_*`, `erasure_succeeded`, and `run_erasure_arm` without `record_path=`.

---

### `tests/test_phase37_r1b.py`

**Analog:** `tests/test_phase36_probe.py`.

**tmp ledger/heartbeat fixture** (`test_phase36_probe.py:209-226`):
```python
def _planted(tmp_path, monkeypatch, stage=_fake_stage):
    monkeypatch.setattr(probe, "_ROOT", tmp_path)
    monkeypatch.setattr(phase25_run, "_DEVICE", "cpu")
    monkeypatch.setitem(probe.STAGES, "e5", stage)
    monkeypatch.setitem(probe.RECORD_BUILDERS, "e5", _fake_builder)
    return {"heartbeat_path": tmp_path / "hb.jsonl", "ledger_path": tmp_path / "ledger.jsonl"}
```
**Ledger assertions** (`:230-240`): `phase36_ledger.read_ledger(path)` -> `[("start", rid, front), ("end", rid, front)]`, `lines[1]["record"] == ...`, beats all carry `point == rid`.
**Crash leaves an open start** (`:281-292`) — the D-11 "started attempt is the attempt" evidence.
**Plist mirror** (`:1769-1798`): `plistlib.loads`, `KeepAlive is False and RunAtLoad is False`, `args[:2] == ["/usr/bin/caffeinate", "-dims"]`, `args[2].endswith("/.venv/bin/python")`, suffix comparison for paths, `EnvironmentVariables` equality with the source agent, `StandardOutPath.endswith("logs/phase37_r1b.out")`.

---

## Shared Patterns

### Refusal
**Source:** `_prove` in every module (`phase36_prereg.py:47-50`, `erasure_kstar_run.py:51-53`). `SystemExit(f"[<module>] {message}")`, never `assert`.
**Apply to:** all four scripts.

### Write-once + dirty tree + atomic write
**Source:** `phase36_probe.py:1170-1221` + `phase25_run.atomic_write_json` (`phase25_run.py:118`).
**Apply to:** `phase37_r1a.py`, `phase37_r1b.py`. The pin writes the arm record itself (`run_erasure_arm(record_path=...)`); everything Phase 37 writes goes through `atomic_write_json`.

### Pin reuse, never reimplementation
**Source:** `erasure_kstar_run.py:1-8` docstring + `:136-139`. `_pooled_rows`, `_order_normalised`, `render_verdict`, `select_ablation_prefix`, `run_erasure_arm` are the only paths.
**Apply to:** `phase37_routes.py`, `phase37_r1a.py`, `phase37_r1b.py`.

### Torch-free prereg
**Source:** `tests/test_phase36_prereg.py:372-383` subprocess probe; `_HEAVY = ("torch", "teach_persona", "phase19_erasure", "phase18_extraction", "phase23_run")`.
**Apply to:** `phase37_prereg.py` only (routes/drivers import the pin and therefore torch).

---

## Census / real-tree tests a new `scripts/phase37_*.py` or `tests/test_phase37_*.py` must satisfy

| Guard | Location | What it requires of Phase 37 |
|---|---|---|
| v6.0 slot census | `tests/test_phase35_prereg.py:2166-2269` (`_slot_census_failures`), run over the real tree at `:2313` | Fill only in `scripts/phase37_*prereg.py` (`owner_prereg_glob`, `phase35_prereg.py:847-850`); binding `R1B_TOLERANCE_AND_REPLICATED = phase35_prereg.fill("r1b_tolerance_and_replicated", ...)`; plain `import phase35_prereg` (no alias, no `from ... import fill`/`SLOTS`); no `phase35_prereg._*` access in ANY phase37 file; slot filled once |
| v6.0 slot ordering | `tests/test_phase35_prereg.py:2475-2531` (legs a/b/c), `:2557` real repo | Every commit touching the fill file strictly precedes the first add of every `results/phase37_*` (leg a: slot has no phase-37 input); once any `results/phase37_*` is tracked the slot must be filled (leg c) |
| `os.replace` writers | `tests/test_phase25_driver.py:341-365` | `os.replace` only in `phase25_run.py`/`phase25_record.py`: use `atomic_write_json` |
| `erasure_succeeded` single call site | `tests/test_phase19_erasure.py:2178-2181` (pin), `:4408-4429` (driver) | Never call `erasure_succeeded`; reach the gate only via `pin.render_verdict` |
| `retention_perplexity` call sites | `tests/test_phase19_erasure.py:1386` (scans `scripts/*.py`) | Never call it; `run_erasure_arm` does |
| `inject_lora` consumers | `tests/test_lora_inject.py:302-303` file set, `:450` | Use `phase14_recall.load_adapted_model`, never `inject_lora` |
| `draw_all` / `persona=` call sites | `tests/test_phase14_scoring.py:571-572` file set, `:634`, `:728` | Do not call `draw_all`/`build_recall_prompt` directly |
| `train_never_taught` entry point | `tests/test_phase23_ctrl.py:82-95` | Do not define or call it |
| `mitigation_point_verdict` call sites | `tests/test_phase20_correction.py:1421-1430` | Do not call it |
| privacy_n pin routes | `tests/test_phase21_unit_continuation.py:83-84` | Not touched by Phase 37 |
| `"descriptive_step_mix"` reader | `tests/test_phase30_calibration.py:248-253` | Do not write that string constant |
| `== 10` wall | `tests/test_phase21_sc5.py:189-196` patterns over `tests/**/*.py`; census `:255-280` | In `tests/test_phase37_*` write no `== 10`/`!= 10` not followed by a digit or `_` — includes comments and prose like "== 10,368" (the comma does not stop the match) |
| MPS launch line | `tests/test_phase36_ledger.py:722-733` | Any tracked `results/phase37_*` with `provenance.run.device == "mps"` must be named by a ledger end line: commit the ledger before `results/phase37_r1b.json` |
| later records after budget | `scripts/phase36_budget.py:1056-1065`, `tests/test_phase36_budget.py:1214-1225` | Phase 37 end-line records must postdate `results/phase36_budget.json` (already true) |
| skip pins | `tests/test_phase25_venue.py:324-365` (`SWEEP_ACTIVE_EXPECTED_SKIPS`, `FLAG_UNSET_EXPECTED_SKIPS`, ubuntu variants) | Zero skips in every `tests/test_phase37_*`; enforce with `_skip_failures` (`tests/test_phase36_prereg.py:396-410`) |
| Phase 19 STAT-05 ancestry | `tests/test_phase16_prereg.py` (pin ancestor of every `results/phase19_*` first add) | Never write any `results/phase19_*` path; never edit the pin |

## No Analog Found

None. The D-07 set-equality decision and the D-03 draw-identity count have no direct precedent, but they are pure comparisons over `curve["ordered_prefix"]` and the arm record's `draws`; the closest shape is `erasure_kstar_run._curve_agreement` (`:78-91`), which records an agreement block and never smooths it.

## Metadata

**Analog search scope:** `scripts/phase19_*.py`, `scripts/phase35_prereg.py`, `scripts/phase36_*.py`, `scripts/erasure_kstar_*.py`, `scripts/phase25_run.py`, `src/personacore/provenance.py`, `artifacts/*.plist`, `tests/test_phase{19,21,25,29,35,36}_*.py`, `tests/test_erasure_kstar_run.py`, and every test that globs `scripts/*.py`.
**Files scanned:** about 30.
**Pattern extraction date:** 2026-10-03
