# Phase 40: M2 Seed Noise Floor (E2) - Pattern Map

**Mapped:** 2026-10-05 (HEAD `328821e`)
**Files analyzed:** 9 repo files (2 scripts, 2 tests, 1 test-register edit, 1 plist, 3 record kinds) plus 1 out-of-repo rehearsal script
**Analogs found:** 9 / 9. The estimator's mean-over-pairs, the D-07 tensor-wise comparison helper and the D-12 25-pair table have no direct analog (see No Analog Found).
Every line reference below was read at HEAD `328821e`. No `scripts/phase40*`, `tests/test_phase40*`, `results/phase40*`, `data/*phase40*` exists yet (measured: `git ls-files results/phase40_*` empty, `ls data | grep phase40` empty).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `scripts/phase40_prereg.py` | config (THE fill file for `e2_S` + `e2_noise_floor_estimator`) + approvals + pure estimator functions | transform | `scripts/phase39_prereg.py` (sections 1-9) | exact |
| `scripts/phase40_noise.py` | CLI driver: preflight / run / emit / report; MPS under the ledger, one ledger attempt per seed | batch + event-driven (ledger/heartbeat) | `scripts/phase37_r1b.py` (whole: preflight/run/emit around `run_erasure_arm(record_path=)`) + `scripts/phase36_probe.py` `run_front` :357-417 (one attempt per unit) and `train_e2_rep`/`stage_e2` :986-1116 (training + csv move) + `scripts/phase39_ctx.py` (lazy prereg, rehearsal identity, real-root guard, report) | exact (composite) |
| `tests/test_phase40_prereg.py` | test | ancestry + AST census + pure unit on tracked JSON | `tests/test_phase39_prereg.py` | exact |
| `tests/test_phase40_noise.py` | test | monkeypatched driver, tmp root/ledger/heartbeat, consumer feed | `tests/test_phase37_r1b.py` (rig, refusals, crash/reconcile, main, plist) + `tests/test_phase39_ctx.py` (torch-free probe, AST censuses) + `tests/test_phase35_prereg.py` `_inputs`/`_fill_band` :912-923, :1440-1475 (consumer feed) | exact (composite) |
| `tests/test_phase23_resume.py` (MODIFY: one register line + `+ 1`) | test register | — | its own 36-05 entry :117-118 and bump :323-337 | exact |
| `artifacts/com.personacore.phase40.e2.plist` | LaunchAgent | — | `artifacts/com.personacore.phase37.r1b.plist` | exact |
| `results/phase40_noise_floor.json` | record (write-once, CPU emit; Phase 41 contract `gap_noise_floor`) | — | `results/phase37_r1b.json` via `phase37_r1b.build_record`/`emit` :342-438 | role-match |
| `results/phase40_<per-seed>.json` + 10 A2 arm records `results/phase40_<arm>.json` | per-seed record (named by each seed's ledger end line) + pin arm records | file-I/O | `results/phase37_r1b_arm.json` (written by `pin.run_erasure_arm(..., record_path=root / prereg.R1B_ARM_RECORD)`, `phase37_r1b.py:298-300`) | exact |
| `results/phase40_noise_floor_report.md` | report (rendered from the committed record) | transform | `phase39_ctx.report` :2222-2249 + `render_report` :2020 | exact |
| `<scratchpad>/rehearsal40.py` (NOT in repo) | rehearsal script | batch | 39-07-PLAN Task 2 (`.planning/phases/39-instrument-context-2-2/39-07-PLAN.md:121-140`) | exact |

---

## Resolved paths and constants (derive, never type)

| Name | Resolves to | Source (verified) |
|---|---|---|
| `RECORD_GLOB` | `next(p for p in phase35_prereg.V6_RESULT_PATHS if p == "results/phase40_*")` | `scripts/phase35_prereg.py:324`; equality idiom `phase39_prereg.py:122` |
| `NOISE_FLOOR_RECORD` | `phase35_prereg.SLOTS["e1_condition_c_band_inputs"]["input_records"][0]` = `"results/phase40_noise_floor.json"`; prove `== RECORD_GLOB.replace("*", "noise_floor.json")` | `phase35_prereg.py:773` (`_NOISE_FLOOR_RECORD`, private: never read it directly), `:1849-1855` |
| `BUDGET_RECORD` | `phase35_prereg.SLOTS["e2_S"]["input_records"][0]` (= `results/phase36_budget.json`), or `phase38_prereg.BUDGET_RECORD` as Phase 39 does (`phase39_prereg.py:134`) | `phase35_prereg.py:1797` |
| S | `fill("e2_S", ...)` returns `record["e2_seed_count"]` = 5 | `_rule_e2_S` `phase35_prereg.py:1173-1187` |
| SEEDS | `phase35_prereg.seed_list()[:E2_S]` = (1337, 2024, 1338, 2025, 1339) | `phase35_prereg.py:357-368` (imports `phase23_run` → torch) |
| E2 caps | `unit_caps.E2 = {adapters: 2, seeds: 5}`; `CAP_FIELDS["E2"] = ("adapters", "seeds")` | `results/phase36_budget.json`; `scripts/phase36_caps.py:48` |
| E2 projection | `seeds x (e2_train_m2_high + e2_train_full_high + adapters x e2_a2_pass_high) / 3600` = 7.890925927716101 | budget `unit_prices` (76.1114059574902, 80.83857736012175, 2762.25834231899) |
| stop (a) | `phase36_prereg.ENTRIES["front_stop_factor"]["value"] * front_hours["E2"]` | shape `phase39_prereg.py:299` |
| RUN_ID per seed | `phase36_ledger.run_id(40, "E2", f"seed{seed}")` → `"v6/40/E2/seed1337"` | `scripts/phase36_ledger.py:76-78` |
| v3.0 sampling floor | `phase19_floor.NONTARGET_NOISE_FLOOR` (0.14814814814814814) | `scripts/phase19_floor.py:125` |
| (b) margin, read not typed | `phase35_prereg.e1_condition_b_margin()` (0.2962962962962963) | `phase35_prereg.py:434` |
| adapter-off PPL (checked, not retyped) | `results/phase19_noise_floors.json` → `dialogue_ppl_noise_floor.seed_a.adapter_off` / `seed_b.adapter_off` (4.573349214207799), `adapter_off_identical_across_seeds: true`; path = `phase19_run.NOISE_FLOORS_PATH` | `scripts/phase19_run.py:195` |
| v3.0 one-pair gap floor (beside) | `phase19_floor.DIALOGUE_PPL_NOISE_FLOOR` (0.005214448168350039) = same record `.value` | `phase19_floor.py:158` |
| v3.0 `delta_taught_to_m2` (D-12) | `results/phase19_retrain_scores.json::retrain_scores.retained[<fact_id>].delta_taught_to_m2` (+ `.slot`); path = `phase19_run.RETRAIN_SCORES_PATH` or `phase38_prereg.RETRAIN_SCORES` | `phase19_run.py:221`, `phase38_prereg.py:146` |
| Phase 18 taught A2 draws (D-08b) | `pin.PHASE18_ARM_RECORD_PATH` = `results/phase18_arm_adapter-on.json` | `phase19_erasure.py:1628` |
| committed M2@1337 A2 record (D-07 counts) | `pin.arm_record_path("retrain")` = `results/phase19_arm_retrain.json` | `phase19_erasure.py:2560` |
| production taught adapter | `phase14_recall.ADAPTER_PATH` = `tp.arm_outputs("real")["adapter"]` = `checkpoints/persona_adapter.pt` | `teach_persona.py:381-385` |
| committed M2 adapter | `phase38_rank.m2_adapter_path()` = `tp.arm_outputs(pin.RETRAIN_ARM, prefix=pin.RETRAIN_PREFIX)["adapter"]` = `checkpoints/phase19_erase_reference_adapter.pt` | `phase38_rank.py:242-249`; `phase19_erasure.py:2996-2997` |
| dialogue-floor adapters | `tp.arm_outputs(f"{pin.DIALOGUE_FLOOR_ARM}_seed{s}", prefix=pin.RETRAIN_PREFIX)["adapter"]` for `s in pin.DIALOGUE_NOISE_FLOOR_SEEDS` | `phase19_erasure.py:1041`, `:2592`, `:3627-3640` |
| gated slots / target | `pin.GATED_NONTARGET_SLOTS` (7), `pin.TARGET_SLOT` (`pet_name`) | `phase19_erasure.py:1174`, `:624` |
| new arm output paths | `tp.arm_outputs(arm, prefix=PREFIX)` → `checkpoints/{prefix}_{arm}_adapter.pt`, `checkpoints/{prefix}_{arm}_latest.pt`, `results/{prefix}_{arm}/run.csv` (MUST be moved), `data/persona_{arm}_train.bin` + mask (no prefix) | `teach_persona.py:357-393` |

**PREMISE CORRECTION (measured this session).** 40-CONTEXT D-07 and 40-RESEARCH name the M2@1337 digest as `results/phase19_arm_retrain.json::adapter_sha256`. That field does not exist: the arm record's keys are `arm, config, dialogue_ppl, draw_record_keys, draws, exposure, per_fact, pre_erasure, retention_ppl`, and `config` has no adapter key. `22e66552…` is committed at `results/phase19_retrain_scores.json::retrain_scores.adapter_sha256` (with `retrain_scores.adapter` = the checkpoint path), plus `phase38_rank.json`/`phase39_ctx.json`. Under amended D-07 the comparison is tensor-wise anyway. The record should cite the scores record for the digest and `phase19_arm_retrain.json` only for the A2 counts.

---

## Pattern Assignments

### `scripts/phase40_prereg.py` (fill file, approvals, pure estimator; frozen before any `results/phase40_*`)

**Analog:** `scripts/phase39_prereg.py`. Copy its section skeleton: (1) date + `RECORDS_AT_COMMIT`, (2) entry schema, (3) record paths, (5) approval arithmetic, (7) `_ENTRIES`, (8) fills, (9) pure definitions.

**Header, sys.path, plain imports** (`phase39_prereg.py:23-46`):
```python
import collections.abc
import fnmatch
import itertools
import json
import math
import pathlib
import statistics
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
import phase36_prereg  # noqa: E402  (same; torch-free)
```
Plain `import phase35_prereg` only. No alias and no `from phase35_prereg import fill` (slot census, `tests/test_phase35_prereg.py:2250-2263`).

**Torch at import.** `SEEDS = phase35_prereg.seed_list()[:E2_S]` imports `phase23_run` → `teach_persona` → torch (`phase35_prereg.py:366`). So, like Phase 39 (docstring `phase39_prereg.py:19-20`), this module is NOT torch-free at import. Say so in the docstring and keep every other heavy import (`phase19_erasure`, `phase19_run`, `phase18_extraction`) inside functions, as `phase39_prereg._values` :947-951 and `phase38_prereg.a2_counts` do. The driver must then import the prereg lazily (see the driver section).

**Date + `_prove` + entry schema + `_read`** (`phase39_prereg.py:52-115`), copied verbatim with the tag `[phase40_prereg]`:
```python
# At this commit no `results/phase40_*` file existed, tracked or untracked.
COMMITTED = "2026-10-05"
RECORDS_AT_COMMIT = 0


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase40_prereg] {message}")


ENTRY_FIELDS = phase35_prereg.ENTRY_FIELDS
KINDS = phase35_prereg.KINDS
FORBIDDEN_PHRASE = phase35_prereg.FORBIDDEN_PHRASE
```
`_prove_count` :72-77, `_prove_entry` :80-110 (refuses `proposer`/`adopted_by`) and `_read` :113-115 are copied whole.

**Record paths by equality** (`phase39_prereg.py:122-129`):
```python
RECORD_GLOB = next(p for p in phase35_prereg.V6_RESULT_PATHS if p == "results/phase40_*")
NOISE_FLOOR_RECORD = phase35_prereg.SLOTS["e1_condition_c_band_inputs"]["input_records"][0]
_prove(NOISE_FLOOR_RECORD == RECORD_GLOB.replace("*", "noise_floor.json"), "...")
REPORT_RECORD = RECORD_GLOB.replace("*", "noise_floor_report.md")
# per-seed and per-arm names: RECORD_GLOB.replace("*", f"seed{seed}.json") etc., as functions
for _path in RECORDS:
    _prove(fnmatch.fnmatch(_path, RECORD_GLOB), f"{_path} does not match {RECORD_GLOB}")
_prove(len(set(RECORDS)) == len(RECORDS), f"the record paths {RECORDS} are not distinct")
```
Reading `phase35_prereg.SLOTS[...]["input_records"]` is a registry read and is allowed (`tests/test_phase35_prereg.py:2218-2219`). Any `phase35_prereg._NAME` is a census failure (`:2215-2217`).

**Approval arithmetic (D-11 +0 h, D-13 if approved)**, copied in the committed term order (shape `phase39_prereg.py:266-306`):
```python
_BUDGET = _read(BUDGET_RECORD)
_E2_CAPS = _BUDGET["unit_caps"]["E2"]


def e2_projection_hours(d13_adapters=0, d13_nlls_per_adapter=0):
    p, c = _BUDGET["unit_prices"], _E2_CAPS
    return (
        c["seeds"] * (p["e2_train_m2_high"] + p["e2_train_full_high"] + c["adapters"] * p["e2_a2_pass_high"])
    ) / 3600 + d13_adapters * (p["adapter_setup_high"] + d13_nlls_per_adapter * p["e5_nll_high"]) / 3600


_prove(e2_projection_hours() == _BUDGET["front_hours"]["E2"], "the E2 formula at the committed caps does not reproduce front_hours.E2")
E2_STOP_HOURS = phase36_prereg.ENTRIES["front_stop_factor"]["value"] * _BUDGET["front_hours"]["E2"]
```
Verify the term order against `scripts/phase36_budget.py`'s `_front_seconds` E2 term before freezing. Research M11 reproduced 7.890925927716101 with this order, but Phase 39 copied the private function's order verbatim (`phase39_prereg.py:270-272`). D-13's 925 NLLs per adapter are derived in code (512 from `phase38_rank.scoring_plan(slots=("pet_name",))[...]["size"]`, 8 from `phase18_extraction.reference_set_for("pet_name")`, 27×8 and 27×7 from the A2 entry count and `phase39_prereg.MINTED_SET_SIZE`), never typed (`test_no_derived_value_is_typed_in_the_prereg`, below).

**Verbatim rulings + `approval_block()`** (`phase39_prereg.py:308-413`): `D11_RULING = "<Rafael's words>"` (and `D13_RULING` only once he approves D-13), and a `def approval_block()` that returns a FRESH dict with `ruling`, `source` (`"40-CONTEXT D-11/D-14 (<sha>)"`), `e2_projection_hours`, `committed_front_hours_e2`, `e2_stop_hours`, `budget_record`, and `untouched = [phase36_ledger.LEDGER_PATH, BUDGET_RECORD, "scripts/phase36_ledger.py", "scripts/phase36_caps.py"]` (import `phase36_ledger` lazily inside, `:373`). Add the Addendum ruling text (D-07/D-08 amended, "Opção 1 (correção)") as its own constant, quoted from the CONTEXT at its commit.

**Entries** (`phase39_prereg.py:469-925`): `_CONTEXT = "40-CONTEXT D-{} (9d53c09)"` and `_ADDENDUM = "40-CONTEXT Addendum D-{} (<commit of the addendum>)"` formatters. A module-level `_ENTRIES = {...}` dict literal: the NAME is load-bearing, because `tests/test_phase36_prereg.py:106` `_entries_node` finds it. Then `ENTRIES = types.MappingProxyType(...)` (:885-887), the `_ENTRY_NAMES` frozenset and `_prove_entries()` called at import (:889-925). Mapping values use `types.MappingProxyType` and sequences use tuples (:498-525).

**The two fills, path 1 (D-16)** (binding shape `phase39_prereg.py:931-939`):
```python
E2_S = phase35_prereg.fill(
    "e2_S",
    input_records=(BUDGET_RECORD,),
    derivation=ENTRIES["e2_S"],   # value == _read(BUDGET_RECORD)["e2_seed_count"], source names BUDGET_RECORD
)
E2_NOISE_FLOOR_ESTIMATOR = phase35_prereg.fill(
    "e2_noise_floor_estimator", estimator=ENTRIES["e2_noise_floor_estimator"]
)
SEEDS = phase35_prereg.seed_list()[:E2_S]
```
`_rule_e2_S` (`phase35_prereg.py:1173-1187`) calls `_consume_inputs` (:910-953): the derivation's `value` must equal the read S, `source` must contain the literal path string, and the path must be declared, existing and repo-relative. Do NOT pass `s=`: the "never typed" rule (35-CONTEXT Addendum to D-15). The `e2_noise_floor_estimator` value is ONE mapping holding both estimators (`recall_floor`: D-01..D-05 incl. the common-random-numbers sentence from RESEARCH Pitfall 7 and the sample-SD convention; `gap_noise_floor`: D-09/D-10, adapter-off checked against the committed record) with `kind: "preference"` (`_rule_e2_noise_floor_estimator` :1773-1776 → `_frozen_entry`). Each fill is the WHOLE value of its module-level UPPER binding (`tests/test_phase35_prereg.py:2194-2204`).

**Pure estimator functions (section 9)**: copy the call shapes, not the bodies.
- 27-denominator rows: the `phase19_run.retrain_score` shape, `scripts/phase19_run.py:1715-1722`:
```python
    values = {f.id: f.value for f in factset.LOCKED_FACTS + factset.SOFT_TIER_FACTS}
    m2_disk = json.loads(pin.arm_record_path("retrain").read_text(encoding="utf-8"))
    family, budget = m2_disk["config"]["attack_family"], m2_disk["config"]["k"]
    tiers = tuple(sorted({d["tier"] for d in m2_disk["draws"] if d["family"] == family}))
    m2 = _pooled_rows(m2_disk["draws"], values, family, tiers)
```
  (`phase19_run._pooled_rows` :620-647 is the only route. Never read an arm record's `per_fact`: 19-09 defect C.)
- Pair statistic D-02: the `phase19_run.py:1761-1763` call shape:
```python
    m2_deltas = pin.nontarget_deltas(pin.nontarget_rows(taught), pin.nontarget_rows(m2))
```
  then `pin.nontarget_noise_floor(deltas)` (`phase19_erasure.py:1377-1407`, max of 7, refuses empty/non-finite). Pairs come from `itertools.combinations(sorted(whole_seeds), 2)`; never a literal 10 (see the `== 10` census).
- D-03/D-04/D-10 reductions: `statistics.fmean`, `statistics.stdev` (sample) with `statistics.pstdev` beside it, plus range, max and min over pairs. These are new (No Analog Found).
- D-09 gap: `rec["dialogue_ppl"]["adapter_on"] - rec["dialogue_ppl"]["adapter_off"]`, with `pre_erasure.dialogue_ppl == dialogue_ppl` proved (the M2 record has both, `results/phase19_arm_retrain.json` keys) and `adapter_off` proved equal to the committed `results/phase19_noise_floors.json` value read at call time.
- D-13 (if approved): import `phase38_prereg.rank_in_prefix` (:720-728), `phase38_prereg.nested_sizes` (:1210-1213), `phase39_prereg.n1` (:1480-1482), `phase39_prereg.minted_members` (:1147-1158) and `phase39_ctx.rank_rows` (:970-974). Never re-define them.

---

### `scripts/phase40_noise.py` (driver: preflight / run / emit / report)

**Primary analog:** `scripts/phase37_r1b.py` (the one driver that wraps `pin.run_erasure_arm(..., record_path=root / <phase-owned record>)` under the ledger). **Per-unit ledger attempt:** `phase36_probe.run_front` :357-417. **Training call:** `phase36_probe.train_e2_rep` :986-1029 + `stage_e2` :1032-1052. **Lazy prereg / rehearsal / report:** `phase39_ctx`.

**Name.** It must NOT match `scripts/phase40_*prereg.py` (`phase35_prereg.owner_prereg_glob` :847-850). `phase40_noise.py` is correct.

**Docstring-as-usage** (`phase37_r1b.py:1-38`): `main` raises `SystemExit(__doc__)` on bad argv (:441-449). State the commands, the per-seed unit (D-15), the one-attempt-per-seed ledger rule, "Torch-free at import" and the launch via the plist only after "approved".

**Imports + constants** (`phase39_ctx.py:49-112`, `phase37_r1b.py:49-85`):
```python
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import phase25_run  # noqa: E402  — atomic_write_json, beat, start_heartbeat
import phase36_caps  # noqa: E402
import phase36_ledger  # noqa: E402

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

_REPO = pathlib.Path(__file__).resolve().parent.parent
_ROOT = _REPO
FRONT = "E2"
LAUNCH_PATHSPEC = ("scripts", "src", "results", "artifacts")
PREREG_FILE = "scripts/phase40_prereg.py"
MODULES = (... "scripts/teach_persona.py", "scripts/phase19_erasure.py", "scripts/phase19_run.py",
           "scripts/phase14_recall.py", "scripts/phase18_extraction.py", "scripts/phase14_factset.py",
           "scripts/phase35_prereg.py", "scripts/phase36_ledger.py", "scripts/phase36_caps.py",
           "scripts/phase25_run.py", PREREG_FILE, "scripts/phase40_noise.py",
           "src/personacore/training/loop.py", ...)
RUN_PROVENANCE_KEYS = ("git_sha_at_launch", "git_sha_at_end", "head_moved_during_run",
                       "device", "torch_version", "started_utc", "finished_utc")
```
Lazy prereg (`phase39_ctx.py:150-154`):
```python
def _prereg():
    """phase40_prereg, imported lazily (torch at import through seed_list)."""
    import phase40_prereg

    return phase40_prereg
```
**Do not bind `E2_S` or `E2_NOISE_FLOOR_ESTIMATOR` at module level in the driver.** The slot census walks every `scripts/**/*.py` and refuses any module-level target named like a slot that is not that slot's fill call (`tests/test_phase35_prereg.py:2199-2204`, `_scanned_sources` :2131-2137). Read `_prereg().E2_S` inside functions.

**Preflight: every refusal before the first ledger start line** (`phase37_r1b.py:170-228`, ordering from `phase39_ctx.py:596-743`): outputs absent, no ledger line for any seed RUN_ID, `refuse_if_dirty(..., pathspec=LAUNCH_PATHSPEC)`, `git_sha() != "unknown"`, `module_sha256()` at launch, `require_launch(FRONT, ledger_path=...)`, `_device() == "mps"` on the real root, `check_unit_caps("E2", adapters=2, seeds=len(SEEDS))`, every gitignored input exists (`run_inputs()` shape `phase37_r1b.py:124-142`: `CONVBASE_SLIM`, `TOKENIZER_PATH`, `tp.DIALOG_VAL_BIN`/`DIALOG_VAL_MASK`, `pin.RETENTION_BIN`, `pin.PHASE18_CORPUS_PATH`, `pin.PHASE18_ARM_RECORD_PATH`, plus the D-07 comparator adapters), and the rehearsal identity present on the real root (`phase39_ctx.py:619-634`). Then print `PREFLIGHT OK` and return the dict.
```python
    refuse_if_dirty(
        who="phase37_r1b",                       # -> "phase40_noise"
        detail=(...),
        pathspec=LAUNCH_PATHSPEC,
        cwd=_ROOT,
    )
    launch_sha = git_sha()
    _prove(launch_sha != "unknown", "git_sha() could not read HEAD: ...")
    launch_modules = module_sha256()
    gate = phase36_ledger.require_launch(FRONT, ledger_path=ledger_path)
    device = _device()
    _prove(device == "mps", f"R1b is the MPS replica; preflight resolved {device!r}")
```
**Dirty-tree hazard (new in Phase 40).** `refuse_if_dirty` treats untracked files as dirty. After seed 1, the run has written `results/phase40_*` arm and seed records, so a per-seed `refuse_if_dirty` would refuse seed 2. Run `refuse_if_dirty` ONCE in preflight. Between seeds, run only `require_launch("E2")` (the committed stop, no second rule: 38-D-23, RESEARCH Pattern 2).

**Per-seed loop: one ledger attempt per seed** (`phase36_probe.run_front` :378-417, adapted):
```python
    rid = phase36_ledger.run_id(36, "probes", front)        # -> run_id(40, FRONT, f"seed{seed}")
    phase36_ledger.append("start", run_id=rid, phase=36, front="probes", ledger_path=ledger_path)
    state = {"point": rid, "stage": "start", "shape": None, "draw_index": None}
    # B1: the thread's first beat comes only after wait(60) ... beat once now.
    phase25_run.beat(heartbeat_path, **state)
    stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
    started_utc, started = _now(), time.monotonic()
    try:
        ...  # train full, train M2, A2 full, A2 M2, [D-13] ; write-once seed record
        state.update(stage="done", shape=None, draw_index=None)
    finally:
        stop.set()
        thread.join()
    phase36_ledger.append("end", run_id=rid, phase=36, front="probes", record=record, ledger_path=ledger_path)
```
`append("end", record=...)` requires a path matching `V6_RESULT_PATHS` (`phase36_ledger.py:212-217`). Once tracked, the named record MUST carry `provenance.run.started_utc/finished_utc` (`RECORD_CLOCK = ("provenance", "run")` :67; `_closed_row` :297-303), so the per-seed record is the ledger's clock. A crash mid-seed leaves an open start that `phase36_ledger.reconcile` turns into a `lost` line, and D-15 drops that seed (test precedent `tests/test_phase37_r1b.py:351-369`).

**Training one adapter** (`phase36_probe.py:995-1028` + the D-15 seed kwarg from `phase19_erasure.py:3627-3636`):
```python
    paths = tp.arm_outputs(arm, prefix=PROBE_PREFIX)
    for key in ("adapter", "checkpoint"):
        _prove(not paths[key].exists(), f"{_rel(paths[key])} exists: stale ... output")
    csv_dst = _data_path(f"{PROBE_PREFIX}_e2") / arm / "run.csv"
    _prove(not csv_dst.exists(), f"{_rel(csv_dst)} exists: stale probe output")
    tp.train_arm(
        arm,
        facts=facts,
        family_ids=phase14_factset.TAUGHT_FAMILY_IDS,
        second_person=second_person,
        replay_ratio=replay_ratio,
        seed=seed,                       # phase19_erasure.py:3634 (the probe trained at the default SEED)
        prefix=PROBE_PREFIX,
    )
    csv_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(paths["csv"]), str(csv_dst))
    paths["csv"].parent.rmdir()  # WR-01: empty after the move; anything else left there refuses
```
Specs: full = `tp.arm_spec("real")`. M2 = `pin.retrain_arm_spec(target.id)`, with the dropped-exactly-one-fact and unchanged-settings proofs copied from `phase36_probe.py:1040-1052` (or `phase19_run.py:1609-1628`). The arm name is never `"real"` (that writes `persona_adapter.pt`) and never an existing bin name. Prove `paths["adapter"]` of the production adapter is byte-unchanged before and after (`phase19_run.py:1630`, `:1655-1660`; `phase36_probe.py:1060`, `:1079-1082`). The single call site must be exactly ONE `tp.train_arm(` text occurrence in the file (the register below counts raw grep hits). Write training as one helper called twice. Never write the name followed by a paren in a docstring or comment.

**One A2 pass** (`phase37_r1b.py:296-300`, `phase36_probe.py:1068-1075`):
```python
            pin.run_erasure_arm(
                "erased", device, components=remeasured, record_path=root / prereg.R1B_ARM_RECORD
            )
```
Phase 40: `pin.run_erasure_arm("retrain", device, adapter_path=<new adapter>, record_path=root / <phase40 arm record>)` for BOTH groups (Claude's Discretion: label `"retrain"` keeps `assert_phase18_parity`; `PARITY_ASSERTED_ARMS` :2552). Signature `phase19_erasure.py:2732-2741`. The arm record's `dialogue_ppl` holds D-09 at +0 s. Release the model between passes as `phase37_r1b.py:292-295` does (`gc.collect()`, `torch.mps.empty_cache()` guarded by `is_available()`).

**D-07 tensor-wise comparison (amended)**: copy the audit block from `scripts/phase19_run.py:333-344`:
```python
    round_tripped = load_adapter(ERASED_ADAPTER_PATH)
    audits = {
        "keys_equal": sorted(round_tripped["adapter"]) == sorted(erased["adapter"]),
        "lora_config_equal": round_tripped["lora_config"] == erased["lora_config"],
        "base_fingerprint_equal": round_tripped["base_fingerprint"] == erased["base_fingerprint"],
        "tensors_bit_identical": all(
            torch.equal(round_tripped["adapter"][k].cpu(), v.cpu())
            for k, v in erased["adapter"].items()
        ),
        "n_tensors": len(round_tripped["adapter"]),
        "n_params": sum(int(v.numel()) for v in round_tripped["adapter"].values()),
    }
```
Load both sides through `personacore.checkpoint.load_adapter` (`src/personacore/checkpoint.py:280-305`, `weights_only=True`). Add the per-key max abs diff and the non-tensor metadata (every top-level key except `adapter`). No file sha256 equality anywhere in this comparison (AST test below). Pairs: M2@1337 vs `phase38_rank.m2_adapter_path()`, full@1337 vs `phase14_recall.ADAPTER_PATH`, full@2024 vs dialogue-floor 2024. The descriptive draw comparison uses `phase37_prereg.draw_identity(replica_draws, committed_draws)` (`scripts/phase37_prereg.py:516`).

**Run sidecar / seed record, then `emit`** (`phase37_r1b.py:305-339`, `:342-438`): a write-once per-seed sidecar or record carrying `RUN_PROVENANCE_KEYS`, `module_sha256_at_launch`, each adapter's path + sha256 (Phase 41 reuses by SHA at the original path) and the arm-record sha256. `emit` rebuilds `results/phase40_noise_floor.json` on CPU from the per-seed records and arm records, refuses an existing record (`"REFUSING to overwrite it ... dated continuations"`, `:405-409`), and calls `refuse_if_dirty` with `:(exclude)` of every path the run wrote (`:419-431`; Phase 40 needs `:(exclude)results/phase40_*` or the explicit list). The provenance block comes from `phase37_r1b.py:385-395`:
```python
    launch, now = blob["module_sha256_at_launch"], module_sha256()
    record["provenance"] = {
        "run": {key: blob[key] for key in RUN_PROVENANCE_KEYS},
        "module_sha256_at_launch": launch,  # WR-01: what actually ran
        "module_sha256": now,  # at write
        "modules_changed_since_launch": sorted(rel for rel in MODULES if launch.get(rel) != now[rel]),
        "head_at_write": git_sha(),
        "written_utc": _now(),
    }
```
**MPS launch-line census hazard (record layout).** `tests/test_phase36_ledger.py:722-733` requires every tracked `results/phase4[0-3]_*` JSON whose `provenance.run.device == "mps"` to be named by a ledger end line. With one end line per seed naming that seed's record, `phase40_noise_floor.json` is named by NO end line. It must therefore NOT carry a top-level `provenance.run` with `device: "mps"`. Put the per-seed run blocks under another key (e.g. `provenance.seeds`), or give the aggregate `provenance.run.device = "cpu"` as the emit host. The 10 A2 arm records are safe: they have no `provenance` key (measured on `phase19_arm_retrain.json`).

**Real-root shape guard and rehearsal** (`phase39_ctx.py:144-147` `_is_real`, `:764-784`, `:199-236` `record_rehearsal`, `:239-293` `rehearsal_disclosure`): on the real root the full SEEDS shape runs on MPS. A tmp root outside the repo may take a seed subset, `device="cpu"`, and must pass its own `ledger_path`/`heartbeat_path` (DR-01 refusal :775-784). Rehearsal arm names must differ from the real ones because the bins carry no prefix (RESEARCH Pitfall 4).

**Report** (`phase39_ctx.py:2222-2249`): `_tracked_and_clean`, a write-once `out.write_text(render_report(_load(record_path)))`, rendered only from the tracked, unmodified record on the real root. **main** (`phase39_ctx.py:2252-2270`):
```python
def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    commands = {"preflight": preflight, "run": run, "emit": emit, "report": report}
    if len(argv) != 1 or argv[0] not in commands:
        raise SystemExit(__doc__)
    # git_sha() reads the process cwd: every command runs at the repository root.
    os.chdir(_REPO)
    commands[argv[0]]()
    return 0
```

---

### `tests/test_phase40_prereg.py`

**Analog:** `tests/test_phase39_prereg.py`.

**Imports + helpers** (`:27-57`):
```python
import phase35_prereg  # noqa: E402  (scripts/ is not a package)
import phase36_prereg  # noqa: E402  (same)
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

PREREG = "scripts/phase40_prereg.py"
```
Helper homes (verified): `_git` `tests/test_phase29_prereg.py:52`, `_assert_frozen_before` :69, `_planted` :526; `_insert_at` `tests/test_phase35_prereg.py:111`, `_literal_failures` :749, `_slot_census_failures` :2166; `_entries_node` `tests/test_phase36_prereg.py:106`, `_entry_string_failures` :115, `_first_inner` :135, `_skip_failures` :396, `_untested_functions` :418.

**Arithmetic re-stated from the budget** (`:64-110`): `_formula(...)` re-derives E2 from `results/phase36_budget.json`, asserts `e2_projection_hours() == front_hours["E2"]` and pins the `repr`s (`"7.890925927716101"`, the stop, and the D-13 projection if approved).

**Ancestry trio** (`:421-455`): `_strictly_before`, `_first_add`, `_phase40_records()` = `git ls-files results/phase40_*`; `test_phase40_prereg_is_frozen_before_every_phase40_record` with the natural-RED non-vacuity leg against `scripts/phase35_prereg.py`; `test_this_test_file_is_first_added_before_every_phase40_record` (FIRST add only); `test_records_at_commit_is_true_at_the_first_commit`. These are honest at zero records.

**Input paths from modules** (`:458-464`): assert `phase35_prereg.SLOTS["e2_S"]["input_records"] == (BUDGET_RECORD,)`, `SLOTS["e2_noise_floor_estimator"]["input_records"] == ()`, `NOISE_FLOOR_RECORD == SLOTS["e1_condition_c_band_inputs"]["input_records"][0]`, `RECORD_GLOB in V6_RESULT_PATHS`.

**Rulings quoted verbatim at their commit** (`:471-499`):
```python
def _bullet(commit, prefix):
    """The bullet starting with ``prefix`` plus its continuation lines, joined by ONE space."""
    lines = _git("show", f"{commit}:{_CONTEXT_PATH}").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(prefix))
    bullet = [lines[start].strip()]
    for line in lines[start + 1 :]:
        if not line.strip() or line.strip().startswith("- "):
            break
        bullet.append(line.strip())
    return " ".join(bullet)
```
`_CONTEXT_PATH = ".planning/phases/40-m2-seed-noise-floor/40-CONTEXT.md"`; use the commit at which Rafael's approval bullet lands, never a moving HEAD.

**No derived value typed** (`:512-564`): `_literal_failures(source, seeds, floats, set())` with seeds = {S, 27, 14, 13, 925, `math.comb(S, 2)`, 25} and floats = {projection, stop, `front_hours.E2`, 0.14814814814814814, 0.2962962962962963, 4.573349214207799, 0.005214448168350039}. Plant one typed copy of each and assert RED. `_literal_failures` is the guard that keeps `5` read and never typed.

**Entries four fields / no proposer / planted phrase** (`:576-618`), **`_prove`/`_read`** (`:621-626`), **slot census over `scripts/phase40_*.py`** (`:718-722`; this covers the driver's no-module-binding rule), **zero skips** (`:725-729`), **every prereg function called** (`:732-744`).

**Import probe.** Phase 39's `test_importing_the_prereg_opens_no_checkpoint` (`:634-715`, audit-hook subprocess) is the template, because this prereg loads torch through `seed_list()`. Assert `E2_S == 5` and `SEEDS == (1337, 2024, 1338, 2025, 1339)` in the probe's JSON instead of `every_entry`.

**Estimator on committed real records (RESEARCH M7, reproduced on CPU):** `_pooled_rows` over `phase18_arm_adapter-on.json` vs `phase19_arm_retrain.json` gives deltas `(0.0, 0.0, 0.0, 0.0, 0.2592592592592592, 0.0, 0.11111111111111116)` and max 0.2592592592592592. The replicate gives 0.14814814814814814. M2 counts: pet_name 0/27, house_number 17/27, hometown 18/27, birth_year 18/27, person_name 26/27, cat/sibling/street 27/27. These are the reproduction tests (template `tests/test_phase39_prereg.py:781-798` "gate2 reproduces every committed count").

---

### `tests/test_phase40_noise.py`

**Primary analog:** `tests/test_phase37_r1b.py`.

**Imports** (`:43-54`): import by name, never aliased (`_untested_functions` counts by name). `pin`/`p19run` aliases for the pins are fine:
```python
import phase14_recall  # noqa: E402  (scripts/ is not a package)
import phase19_erasure as pin  # noqa: E402  (same)
import phase36_ledger  # noqa: E402  (same; never aliased)
import phase40_noise  # noqa: E402  (same; never aliased — _untested_functions counts by name)
import phase40_prereg  # noqa: E402
import teach_persona  # noqa: E402  (same)

from personacore.provenance import git_sha  # noqa: E402
from test_phase29_prereg import _git, _planted  # noqa: E402
from test_phase36_prereg import _skip_failures, _untested_functions  # noqa: E402
```

**Real-tree guard (autouse)** (`:80-88`): snapshot `git status --porcelain -- results ledger` and the real `data/phase40_*` sidecars and identity before and after each test.

**Rig** (`:110-166`): tmp root with `results/` + `data/`, tmp ledger + heartbeat, gitignored inputs as tmp stand-ins via `monkeypatch.setattr(owner, name, stand_in)`, `_device → "mps"`, `refuse_if_dirty` recorded, `require_launch` recorded (returning a dict), and `pin.run_erasure_arm` replaced by a fake that copies `pin.arm_record_path("retrain")` to `record_path`:
```python
    def arm(name, device, *, components=(), record_path=None, **kw):
        rig.arms.append({"arm": name, "device": device, "components": list(components), "path": record_path})
        shutil.copyfile(pin.arm_record_path("erased"), record_path)

    monkeypatch.setattr(pin, "run_erasure_arm", arm)
```
Stub training with `monkeypatch.setattr(teach_persona, "train_arm", fake)`. The attribute NAME is a string here, so no new `train_arm(` grep hit appears. The fake must write the adapter, checkpoint and the `results/<prefix>_<arm>/run.csv` under the tmp root (re-point `teach_persona._REPO_ROOT`, or stub `arm_outputs`), so the csv-move step is exercised. Pass `tracked=` / stub `phase36_caps.tracked_files` only in root-moving tests (RESEARCH Pitfall 6; precedent `tests/test_phase36_ledger.py:676`).

**Refusal table** (`:372-426`): one plant per refusal, parametrized; each asserts `SystemExit`, no ledger, no heartbeat, `rig.arms == []`. Missing-input parametrization comes from `_RUN_INPUTS` (`:60-77`, `:429-442`).

**Crash / whole-seed legs** (`:351-369`): a crash in seed 2 after the start line leaves `["start"(s1), "end"(s1), "start"(s2)]`. `reconcile` → `lost`. The estimator then sees only seed 1337 (D-15). The stop leg: `require_launch` raising before seed k writes no start line for k.

**Commit-landing-mid-run** (`:455-472`), **emit / build_record on the REAL committed arm record** (`:563-645`; feed real `phase19_arm_retrain.json` / `phase18_arm_adapter-on.json` copies so the dry-run memory's "feed the consumer one real producer record" holds), **main dispatch with `inspect.signature(real).bind` and cwd == repo** (`:653-674`), **plist mirrors the probe agent** (`:681-716`), **zero skips** (`:719-723`), **every function called** (`:726-735`).

**Consumer feed (Phase 41 contract)**: the template is `tests/test_phase35_prereg.py:912-923` `_inputs` (plant records under tmp, `monkeypatch.setattr(phase35_prereg, "_REPO_ROOT", root)`) and `:1440-1475` `_fill_band`:
```python
def _fill_band(root, monkeypatch, band_inputs, band_records, *, consumed=None, value=None):
    records = {f"results/phase41_band_inputs_{i}.json": p for i, p in enumerate(band_records)}
    planted = {**records, _NOISE: {"gap_noise_floor": 0.1}}
    _inputs(root, monkeypatch, planted)
    paths = tuple(planted) if consumed is None else consumed
    return phase35_prereg.fill(
        "e1_condition_c_band_inputs",
        band_inputs=band_inputs,
        input_records=paths,
        derivation=_measured(tuple(band_inputs) if value is None else value, paths),
    )
```
Phase 40 replaces the planted `{"gap_noise_floor": 0.1}` with the dict that the REAL `phase40_noise.build_record` produced from real arm records, and asserts each band equals `mitigation_gate.dialogue_gap_band(control_gap=..., gap_noise_floor=<record value>)` (`scripts/mitigation_gate.py:526`). Writing `monkeypatch.setattr(phase35_prereg, "_REPO_ROOT", ...)` in a TEST is outside the census (it scans `scripts/` and `src/` only, `_scanned_sources` :2131-2137). `_prove_record` requires only a mapping carrying `gap_noise_floor` (`phase35_prereg.py:875-881`), `_prove_finite` and `>= 0` (`:1742-1745`).

**Driver AST censuses** (`tests/test_phase39_ctx.py`): `test_the_driver_imports_without_torch` :176-185 (probe prints `RUN_ID`/`FRONT`, `'torch' in sys.modules` False, `'phase40_prereg' in sys.modules` False); `_sampler_failures` / no `os.replace` :1625-1661; `test_ast_ledger_calls_are_the_allowed_five` :1810-1822 (`{"run_id", "read_ledger", "open_runs", "require_launch", "append"}`; never `rule`); `_caps_failures` :1664-1680 narrowed to `check_unit_caps` keywords. Add one Phase-40 AST leg: no `hashlib.sha256` / `_sha256(...)` equality inside the D-07 comparison function (amended D-07: tensor-wise only).

---

### `tests/test_phase23_resume.py` (MODIFY: register one call site)

**Analog:** its own 36-05 entry and bump. Add next to `:117-118`:
```python
    # Plan 36-05's E2 timing probe: two M2 reps under probe36 arm names, no `resume_from`.
    ("scripts/phase36_probe.py", "call", "train_e2_rep (Phase 36's E2 timing probe, COST-01)"),
    # Plan 40-xx (2026-10-..): the E2 noise-floor driver's one training helper, full + M2 per seed, no `resume_from`.
    ("scripts/phase40_noise.py", "call", "<helper name>"),
```
and extend the dated comment at `:323-328` plus the literal at `:329-337`:
```python
        == 8 + 1 + 1 + 1 + 1 + 2 + 1 + 1 + 1 + 1 + 1
    ), ("... plus 36-05's E2 timing probe plus 40-xx's E2 noise-floor driver")
```
The register is checked three ways: raw `grep -rn "train_arm(" --include=*.py scripts tests` count == register length (`:271-286`), per-file counts (`:288-296`) and AST calls per file (`:339-...`). `_RESUME_PASSERS` (`:180-192`) stays unchanged: the driver must not pass `resume_from`. This test file is not module-sha256-pinned (RESEARCH Pitfall 5).

---

### `artifacts/com.personacore.phase40.e2.plist`

**Analog:** `artifacts/com.personacore.phase37.r1b.plist` (whole file, 60 lines). Copy it, then change `Label` → `com.personacore.phase40.e2`, `ProgramArguments[3]` → `.../scripts/phase40_noise.py`, `[4]` → `run`, and the log pair → `logs/phase40_e2.out/.err`. Keep `KeepAlive` false, `RunAtLoad` false, `caffeinate -dims`, `PERSONACORE_SWEEP_ACTIVE=1` and `ProcessType Interactive`. The test template is `tests/test_phase37_r1b.py:691-716`.

---

### Records and report

- `results/phase40_noise_floor.json`: top-level `gap_noise_floor` (finite float ≥ 0). Beside it: the recall floor per group and the published max, every pair's d, max/min, per-slot range/sd/pstdev, `beside = {sampling_floor: phase19_floor.NONTARGET_NOISE_FLOOR, margin_at_gate: e1_condition_b_margin()}`, the D-07/D-08/D-08b block, the D-12 table, `approval_block()`. Layout is Claude's Discretion; the launch-line hazard above binds `provenance.run`.
- Per-seed records `results/phase40_seed<s>.json` (each named by its seed's end line, carrying `provenance.run` with `device: "mps"`) and 10 arm records written by `run_erasure_arm(record_path=...)`.
- Commit order (`tests/test_phase36_ledger.py:722` and the 39 precedent): ledger lines first, then each record, each only after Rafael's "approved"; the report after the record is tracked and clean.

### `<scratchpad>/rehearsal40.py` (NOT a repo file)

**Analog:** 39-07-PLAN Task 2 (`39-07-PLAN.md:121-140`). Write it with the Write tool. kwargs come from `inspect.signature`. It uses a fresh scratch root T with its own `ledger.jsonl`/`heartbeat.jsonl`, sets `torch.backends.mps.is_available = lambda: False` BEFORE any import that trains (RESEARCH M15: `train_arm` resolves its own device), uses rehearsal-only arm names, and runs `run → emit → report → consumer fill`. It launches detached with `nohup ... ; echo REHEARSAL_EXIT=$?`, waits with a `run_in_background` `until grep -q '^REHEARSAL_EXIT='` poller, and checks `git status --porcelain -- scripts src results tests ledger` is empty afterwards. Bins, checkpoints and csv from the rehearsal land under the REAL `data/`/`checkpoints/` (`arm_outputs` uses `teach_persona._REPO_ROOT`). The plan must name them and their cleanup, or re-point `teach_persona._REPO_ROOT` to T in the script.

---

## Shared Patterns

### Refusal
`_prove` raises `SystemExit(f"[<module>] {message}")`, never `assert` (`phase39_prereg.py:57-60`, `phase37_r1b.py:88-90`). Tests match `r"^\[phase40_(prereg|noise)\]"`.

### Write-once, atomic, clean tree
`phase25_run.atomic_write_json` (`scripts/phase25_run.py:118`) is the only atomic writer. `os.replace` is allowed only in `phase25_run.py`/`phase25_record.py` (`tests/test_phase25_driver.py:341-365`, AST over `scripts/*.py` + `src/**/*.py`). `_write_once` (`phase39_ctx.py:337-340`). `emit` refuses an existing record. `report` renders only a tracked clean record.

### Instrument reuse
A2 via `pin.run_erasure_arm`. Rows via `phase19_run._pooled_rows`. Pair d via `pin.nontarget_deltas` + `pin.nontarget_noise_floor`. Dialogue PPL read from the arm record (the same `dialogue_ppl_pair` → `masked_perplexity` as `_cmd_dialogue_floor`, `phase19_erasure.py:3637-3645`). Rank/n1 via `phase38_prereg.rank_in_prefix`, `phase39_ctx.rank_rows`, `phase39_prereg.n1`. Adapters load through `phase14_recall.load_adapted_model` (registered ISO-06 consumer) or `personacore.checkpoint.load_adapter` (no injection).

### Ledger discipline
`require_launch("E2")` before each seed (writes nothing). The start line only after every refusal. Beat once, then the heartbeat thread. Write-once per-seed output before the end line. The end line names the per-seed record. No in-run timer, no `phase36_ledger.rule` (`phase36_probe.py:378-417`; `phase39_ctx.py:793-967`).

### Approval outside the caps
`check_unit_caps("E2", adapters=2, seeds=len(SEEDS))` stays at the committed caps (`scripts/phase36_caps.py:165-179`). Any D-11/D-13 addition lives in `phase40_prereg.approval_block()` and in every record (`phase39_prereg.py:370-413`).

## Census / real-tree tests a new Phase 40 file trips

| Guard | Location | What it requires of Phase 40 |
|---|---|---|
| Slot census | `tests/test_phase35_prereg.py:2166-2269`, real tree `:2313-2318` | `E2_S`/`E2_NOISE_FLOOR_ESTIMATOR` bound once each, as the whole fill call, only in `scripts/phase40_*prereg.py`; no other `scripts/**` file may bind those names at module level; plain `import phase35_prereg`; no `phase35_prereg._*`, no `_rule_*`, no `getattr(phase35_prereg, ...)`, no string `"phase35_prereg"` |
| Slot ordering legs | `tests/test_phase35_prereg.py` `_fill_sites` :2463, `_slot_ordering_failures` :2475, tests :2550-2583 | every commit touching `scripts/phase40_prereg.py` strictly precedes the first add of every `results/phase40_*` (leg a); after any phase40 record is tracked, both slots are filled (leg c) |
| Owner caps exec | `tests/test_phase36_caps.py:272-293` | NOT tripped: `e2_S` is absent from `phase36_caps.SLOT_COUNTS` (`:64-71`) |
| MPS launch line | `tests/test_phase36_ledger.py:722-733` | every tracked `results/phase40_*` with `provenance.run.device == "mps"` is named by an end line → aggregate record must not carry MPS `provenance.run` |
| Ledger record clock | `scripts/phase36_ledger.py:67`, `:297-303` | each end-line record carries `provenance.run.started_utc/finished_utc` |
| `train_arm(` register | `tests/test_phase23_resume.py:60-164`, `:258-345` | +1 register line, `+ 1` in the sum literal, no prose occurrence of the name followed by a paren, no `resume_from` |
| `== 10` wall | `tests/test_phase21_sc5.py:196` regex `(?:==\|!=)\s*10(?![0-9_])` over `tests/*.py` (comments included), `:280-300` | no `== 10`/`!= 10` text in `tests/test_phase40_*`; use `math.comb(len(SEEDS), 2)` |
| `os.replace` | `tests/test_phase25_driver.py:341-365` | `atomic_write_json` only; `shutil.move` is fine |
| ISO-06 `inject_lora` | `tests/test_lora_inject.py:261`, `:476-490` | never call `inject_lora`; no new register line |
| module_sha256 pins | `results/*.json` `provenance.module_sha256` (e.g. `phase36_probe_e2.json`, `phase38_rank.json`, `phase39_ctx.json`) | edit NO existing script (teach_persona, phase19_*, phase35/36/37/38/39_*); Phase 40 only adds files + the one test register line |
| Clean-tree probes | `refuse_if_dirty` in preflight/emit; `tests/test_phase25_driver.py` and siblings | commit the new phase40 files before the full suite; the training csv must leave `results/` in-process |

## No Analog Found

| File / piece | Role | Data Flow | Reason / what to use |
|---|---|---|---|
| Mean over C(S',2) pairs + per-slot range/SD (D-03/D-04/D-10) | pure prereg functions | transform | v3.0 only ever used one pair (`nontarget_noise_floor`, `phase19_floor.py:125`). ~20 lines over `itertools.combinations`, `statistics.fmean/stdev/pstdev`, refusing S' < 2 with `_prove` (`ENTRIES["e2_min_seeds"]`, `phase35_prereg.py:708`) |
| D-07 tensor-wise new-vs-committed comparison as a reusable function | driver helper | file-I/O | the closest code is an inline audit dict (`phase19_run.py:333-344`), not a function; write one small function over `load_adapter`, `torch.equal`, max abs diff, metadata equality |
| D-12 25-pair full×M2 table with same-seed marks | pure prereg function | transform | no cross-group table exists; build on `pin.nontarget_rows` + signed `rate` differences like `phase19_run.py:1753-1755` (`delta_taught_to_m2 = b["rate"] - t["rate"]`) |
| D-08b residual (Phase 18 `run_arm` draws vs `run_erasure_arm` on full@1337) | record block | transform | compare `_pooled_rows` counts of `pin.PHASE18_ARM_RECORD_PATH` vs the new full@1337 arm record, plus `phase37_prereg.draw_identity`; truth table: identical weights + equal counts / identical weights + different counts (v3.0 limitation) / weights differ (effects not separable) |

## Metadata

**Analog search scope:** `scripts/phase37_r1b.py` (whole), `scripts/phase36_probe.py` :340-449, :980-1139, `scripts/phase39_prereg.py` :1-130, :197-416, :466-525, :880-1000, :1147-1160, :1478-1496, `scripts/phase39_ctx.py` :1-345, :564-595, :596-970, :1495-1549, :2222-2271, `scripts/phase35_prereg.py` :55-72, :355-440, :845-960, :1170-1190, :1700-1900, `scripts/phase19_erasure.py` :1333-1407, :2732-2772, :3600-3700, `scripts/phase19_run.py` :325-350, :615-650, :1584-1783, `scripts/phase36_ledger.py` :30-80, :194-303, `scripts/phase36_caps.py` :45-200, `scripts/phase38_rank.py` :242-252, :286-293, :329-349, :380-392, :621-633, `scripts/phase38_prereg.py` :720-735, :1210-1213, `scripts/teach_persona.py` :357-393, :1672-1697, `src/personacore/checkpoint.py` :280-305, `tests/test_phase23_resume.py` :55-345, `tests/test_phase37_r1b.py` (whole), `tests/test_phase39_prereg.py` :27-126, :415-745, `tests/test_phase39_ctx.py` :176-185, :1606-1680, :1810-1829, `tests/test_phase35_prereg.py` :476-500, :570-600, :912-962, :1440-1545, :2131-2318, `tests/test_phase21_sc5.py` :185-300, `tests/test_phase25_driver.py` :335-366, `tests/test_phase36_ledger.py` :707-800, `tests/test_phase36_caps.py` :255-300, `artifacts/com.personacore.phase37.r1b.plist`; committed JSON shapes of `results/phase19_noise_floors.json`, `results/phase19_arm_retrain.json`, `results/phase19_retrain_scores.json`, `results/phase36_budget.json`.
**Files scanned:** about 30.
**Pattern extraction date:** 2026-10-05
