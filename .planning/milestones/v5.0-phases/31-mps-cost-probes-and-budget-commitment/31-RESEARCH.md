# Phase 31: MPS Cost Probes and Budget Commitment - Research

**Researched:** 2026-09-26
**Domain:** Measuring MPS wall-clock of existing frozen drivers (no new ML), write-once provenance records, git-ancestry guards
**Confidence:** HIGH on codebase facts (every path, constant and signature below was resolved live from the modules at HEAD `a665b88`); MEDIUM on runtime estimates (derived from committed Phase 25 records, not yet measured for replay or relearning)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Probe point (ARCAL-01)
- **D-01:** The probe runs the **`advr_n64` control** (ratio 0), the cost-dominant leg with 256 replay windows per step. Only a control can run before Phase 32, because the Phase 30 D-19 guard refuses a non-control point until its own control record exists.
  - A control has no `control_gap` of its own, so condition (c) runs for timing only. The probe records its readings, but they gate nothing.
  - The n8 cost is not probed. It is derived per stage from n64, as specified under D-09.
- **D-02:** The probe is **discarded and isolated**, following the Phase 23 precedent (`results/phase23_cost.json` has `sweep_point: false`).
  - It writes under its own prefix and its own sidecar and adapter paths, never a `phase32_point_*` key or path (SC4).
  - A guard proves that Phase 32's `train_stage` cannot pick up the probe's sidecar or adapter (`phase25_points.train_stage` silently REUSES an existing `data/phase25_<key>_training.json` and adapter).
  - The probe record carries `sweep_point: false` with a reason.
- **D-03:** The probe **times taught-recall scoring** as its own stage. Phase 25 scored recall separately (~1304.5 s/point, `results/phase25_recall.json`), but v5.0 needs recall for floors and `control_gap`, so the budget prices it from this measurement.

#### Relearning probe (ARCAL-02)
- **D-04:** "One leg" is **one arm on the full ladder**: one seed relearning to `RELEARN_CAP` = 400 steps, scored at all 8 `RUNGS` at `CURVE_K`. That is the atomic unit every Phase 27 leg is built from. The budget multiplies it by each sub-mode's arm count (fresh ×5, control, mitigated).
- **D-05:** The adapter is **the probe's own `advr_n64` adapter** from D-01: the replay-bearing recipe v5.0 would relearn on, real rather than a CPU stub, and isolated with the probe. The relearning probe therefore runs after the point probe.
  - The v4.0 `checkpoints/phase25_ratio*_adv_n64_adapter.pt` files are NOT used: they are the no-replay recipe and gitignored.
- **D-06:** The relearning probe is built from `phase27_relearn`'s lower-level pieces (`train_relearn_arm`, `score_rung`). **`scripts/phase27_relearn.py` must not be edited**: `results/phase27_admission.json` pins it strictly in `PINNED_MODULES`, the tripwire in `tests/test_phase27_relearn.py` would go red, and every public leg starts with `_require_admitted` against a MOOT record.
- **D-07:** The relearning term is **priced but not scheduled**.
  - Under D-15 option 2 from Phase 29, v5.0 admission reaches CANDIDATE-UNREPLICATED at best, never ADMITTED, so RELRN-06..09 do not run under the current contract.
  - The budget records the relearning term as 0 h scheduled, alongside the full conditional cost of the relearning legs if a later ruling admits. The probe still runs, because ARCAL-02 requires the measurement.

#### Budget (ARCAL-03)
- **D-08:** The budget is a **resource record plus a pre-committed stop line**, not an outcome threshold (consistent with ROADMAP:171).
  - **Stop line:** Phase 32 pauses at a developer checkpoint when cumulative sweep wall-clock exceeds **1.5 × the upper bound of the budget's measured range** (D-10).
  - The stop line is recorded in `phase31_budget.json`, and Phase 32 must read it from there, never retype it.
- **D-09:** The budget uses a **per-stage × counts** formula: the measured per-stage times (train, condition (c), attack draws/scoring, recall) × the point count per leg.
  - n8 per-stage times are scaled from n64 by measured ratios. The replay-bearing training stage scales with the replay window count (32 vs 256). The non-training stages use Phase 25's measured n8/n64 stage ratios.
  - Both D-12 branches are priced: a leg whose control is unlearnable costs its control only, and the rest get REFUSED records with no training.
  - The formula, every input and its source path go in the record, so the total can be recomputed from committed files.
- **D-10:** The uncertainty is **Phase 25's measured spread**, not an invented multiplier: the point estimate plus a range from Phase 25's measured per-point spread (adv points 49-71 min, ~±20%) applied per stage. The range is empirical, and D-08's stop line hangs off its upper bound.

#### Replay evidence and run mode
- **D-11:** The probe shows that replay ran by **counting replay draws through `train()`'s existing `on_draw` hook**, the same mechanism `tests/test_phase30_seam.py` uses.
  - The count is recorded per optimizer step in the probe record and must equal `phase29_prereg.replay_windows(64)` = 256 on every step.
  - **`scripts/teach_persona.py` stays untouched.** WR-03 stays carried to Phase 32 as a named item. Reopening frozen pins to edit a protected production module is not worth it here.
- **D-12:** The probes run **unattended under a LaunchAgent**, reusing Phase 25's pattern (`artifacts/com.personacore.phase25.sweep.plist`: `caffeinate -dims`, heartbeat jsonl, logs under `logs/`). Timings are then not skewed by sleep or interactive load. The developer launches and boots out the agent, as in Phase 25/26.

### Claude's Discretion
- The exact probe prefix and sidecar/adapter naming, provided it cannot collide with any `phase32_point_*` / `phase25_*` path (D-02).
- How condition (c) runs for timing without a `control_gap` on a control (D-01), provided the record makes clear that the readings gate nothing.
- Whether the two probes share one LaunchAgent run in sequence or use two (D-05 already orders them point → relearn).
- The record schemas, provided they carry the per-stage wall-clock, `sweep_point: false`, the on_draw replay counts, the provenance (git_sha, head_at_write, module_sha256) and the descent from the calibration commit `4339f2b`.

### Deferred Ideas (OUT OF SCOPE)
- **WR-03** (advr runs log `replay_ratio=0.0` and no `replay_windows`, the fix edits `teach_persona.py`) stays carried to Phase 32. So does **WR-04's replay-count cross-check**, which depends on it.
- **IN-01..04** from 30-REVIEW.md stay carried to Phase 32.
- **Probing the n8 control directly.** Not done: n8 is derived per stage (D-09). Revisit only if the Phase 32 n8 leg breaches the stop line.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ARCAL-01 | One replay-bearing adversarial point is measured end to end on MPS (training + condition (c) + attack scoring) before the sweep budget is committed | Pipeline = `phase30_points.next_action` → re-keyed plan → `phase25_points.train_stage` (with `tp.train` wrapped for `on_draw`) → `phase25_points.measure_stage` (condition (c) + GATE-05 + recall, since `is_control`) → `phase25_run.draw_point_shapes` → `phase25_run.score_point`. Every stage already exists and returns or records its own seconds; see "Point probe pipeline". |
| ARCAL-02 | One relearning leg is measured on MPS on a real adapter before the relearning budget is committed | `phase27_relearn.train_relearn_arm(arm="mitigated", point_key=<probe label>, ...)` from the probe's own adapter, then `phase27_relearn.score_rung(...)` × 8 rungs at `CURVE_K` = 16. Neither calls `_require_admitted`. See "Relearning probe pipeline". |
| ARCAL-03 | The total v5.0 budget is committed from ARCAL-01/02, replacing the unmeasured ~25-30 h estimate | Torch-free emitter reading only COMMITTED records (probe records + the 12 `results/phase25_point_adv_*.json` + `results/phase25_recall.json`). The new ancestry test copies `tests/test_phase30_calibration.py::test_ancestry_calibration_precedes_every_later_v5_result` using `tests/test_phase29_prereg.py::_assert_frozen_before`. See "Budget formula" and "Ancestry test". |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Python 3.11 venv at `.venv` is mandatory; never validate on the host Python 3.14. [VERIFIED: `.venv/bin/python` = 3.11.15, torch 2.7.1, MPS available]
- Primary device is local M3/MPS in **fp32**: no AMP, no `GradScaler`, no `torch.compile`. `phase25_run.device()` resolves CUDA → MPS → CPU once per process.
- No new external dependencies. No wandb or network: logs are CSV/JSON under `data/` and `logs/` (gitignored).
- Tests are pytest, CPU-only and GPU-free. `make test` = `.venv/bin/pytest -q`, `make lint` = `ruff check . && ruff format --check .`.
- GSD workflow: edits go through `/gsd-execute-phase`.
- Never commit a Kaggle token. `data/`, `checkpoints/`, `logs/` and `*.pt` are gitignored.
- Reproducibility: seed + git SHA + config embedded in records (`personacore.provenance.git_sha`, `refuse_if_dirty`).

## Summary

Every piece of the probe machinery already exists and is key-agnostic enough to reuse without editing a frozen module. The point probe is `phase30_points.next_action(control_key("n64"), tracked)`, which runs `require_calibrated_recipe` and so proves the probe uses the committed ARECIPE-02 recipe. Its plan dict is then **re-keyed**: `dict(plan, point_key=PROBE_KEY, prefix=PROBE_PREFIX)`. The re-keyed plan runs through `phase25_points.train_stage` → `measure_stage` → `phase25_run.draw_point_shapes` → `score_point`. `train_stage` and `measure_stage` use `plan["point_key"]` only for sidecar paths and log text, and `plan["prefix"]` only for `tp.arm_outputs` (verified by reading `prove_mechanism_matches_pin`, which uses the key only in messages). Re-keying therefore isolates every sidecar, adapter, checkpoint and draw cache from Phase 32's, with no edit to frozen code. The D-11 replay count rides the existing `on_draw` hook: the probe wraps `teach_persona.train` for the one `train_stage` call, exactly as `tests/test_phase30_seam.py:238` does, and restores it in `finally`.

The relearning probe calls `phase27_relearn.train_relearn_arm` and `score_rung` directly. Neither calls `_require_admitted`; that gate lives only in the `run_*` legs. **Headline cost finding:** `score_rung` draws the full 864-prompt × `CURVE_K`=16 corpus (13,824 draws) plus `tp.score_arm` recall at every rung. That is one sweep point's scoring per rung. Measured: `x18.build_corpus` equals `results/phase18_corpus.json`, 864 prompts, sha `ff8e6e3c…`. At Phase 25's measured adv scoring pace (draws 46-68 min + recall 15-17 min), **one relearning arm is ~8.5-11.5 h of MPS**, so the two probes together are **~10-14 h unattended** `[ASSUMED: derived, unmeasured until the probe runs]`. The plan must treat the launch as a long human-checkpoint run.

The budget is a torch-free emitter over committed records only. The ~25-30 h figure is weaker than it looks. The 12 committed v4.0 adv points sum to **12.56 h** without recall and **15.88 h** with recall, so the estimate already carried an unstated ~2× margin and no replay term. The ARCAL-03 ancestry guard is a near-copy of the calibration guard.

**Primary recommendation:** Build two new modules, `scripts/phase31_probe.py` (run + emit for both probes) and `scripts/phase31_budget.py` (torch-free derive + emit). Add one LaunchAgent plist, `artifacts/com.personacore.phase31.probe.plist`, that runs point → relearn in sequence, and one test file per module. Reuse, never edit: `phase25_points`, `phase25_run`, `phase27_relearn`, `phase30_points`, `teach_persona`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Replay-bearing training + on_draw count | Probe driver (`scripts/phase31_probe.py`) | frozen `phase25_points.train_stage` / `teach_persona` | Driver only wraps and times; training code is frozen |
| Condition (c), GATE-05, recall | frozen `phase25_points.measure_stage` | probe driver (outer timing) | `is_control=True` makes it score recall (`tp.score_arm`) |
| Attack draws + scoring | frozen `phase25_run.draw_point_shapes` / `score_point` | probe driver | Key-agnostic; shape timing is already recorded per shape |
| Relearning leg | frozen `phase27_relearn.train_relearn_arm` / `score_rung` | probe driver | Lower-level pieces bypass `_require_admitted` legitimately |
| Unattended execution | LaunchAgent (launchd + `caffeinate -dims`) | `phase25_run.start_heartbeat` | D-12 |
| Durable per-stage state | gitignored sidecars under `data/` | — | Resume and timing survive a kill |
| Published records | `results/phase31_*.json` (write-once, emitted on clean tree) | git (developer commits) | Provenance pattern of `phase30_calibration.emit` |
| Budget derivation | `scripts/phase31_budget.py` (torch-free) | committed records only | Recomputable from committed files (D-09) |
| Ordering proof | `tests/test_phase31_*.py` ancestry test | `tests/test_phase29_prereg.py::_assert_frozen_before` | "Ancestry tests, not these sentences, are the mechanism" (ROADMAP) |

## Standard Stack

No new packages. Everything is the in-repo toolkit plus stdlib. [VERIFIED: codebase]

### Core (reuse, do NOT edit)
| Module / symbol | Location | Purpose |
|---|---|---|
| `phase29_prereg.V5_RESULT_PATHS`, `control_key`, `replay_windows`, `POINT_KEYS`, `ARTIFACT_PATHSPECS`, `RUNGS`, `RELEARN_CAP`, `CURVE_K`, `FRESH_SEEDS`, `DESIGNATED_SEED` | `scripts/phase29_prereg.py:148, 118, 172, 111, 162, 315-335` | Every path and constant is imported, never retyped. FROZEN by ancestry (a v5.0 result already exists). |
| `phase30_points.next_action`, `recipe_identity`, `require_calibrated_recipe`, `point_plan`, `_tracked_json`, `CALIBRATION_PATH` | `scripts/phase30_points.py` | Recipe proof + plan. Do not edit: `_SUPERSEDED_PINS` tripwire in `tests/test_phase30_calibration.py:340`. |
| `phase25_points.train_stage(plan)`, `measure_stage(plan, training)`, `attack_corpus()`, `scoring_values()`, `training_sidecar(key)`, `measure_sidecar(key)`, `run_log_dir(key)` | `scripts/phase25_points.py:350, 536, 637, 655, 266-276` | Training / measure stages + sidecar path derivations |
| `phase25_run.draw_point_shapes`, `score_point`, `draws_path`, `atomic_write_json`, `device`, `beat`, `start_heartbeat`, `HEARTBEAT_PATH`, `head_sha` | `scripts/phase25_run.py:458, 586, 180, 118, 407, 298, 350, 286, 392` | Draws, scoring, atomic writes, heartbeat |
| `phase27_relearn.train_relearn_arm`, `score_rung`, `shared_train_config`, `STREAM_DIR` | `scripts/phase27_relearn.py:526, 692, 457, 57` | Relearning arm + per-rung scoring. Pinned by `results/phase27_admission.json`; never edit. |
| `personacore.provenance.git_sha`, `refuse_if_dirty` | `src/personacore/provenance.py:47` | Emit-time provenance + dirty refusal |
| `tests/test_phase29_prereg.py::_assert_frozen_before`, `_git` | `tests/test_phase29_prereg.py:59, 71` | Ancestry helper (import it, as `test_phase30_calibration.py:35` does) |
| `tests/test_phase22_wiring.py::_e2e_env`, `tests/test_phase27_relearn.py::_e2e_env` | `:715`, `:614` | CPU tiny-fixture harnesses for the live-path wiring proof |

### Real constants (resolved live at HEAD)
| Name | Value | Source |
|---|---|---|
| `phase29_prereg.control_key("n64")` | `advr_n64_ratio0p000000` | call |
| `phase30_points.point_plan(...)` prefix | `phase32_ratio0p000000` | call |
| `phase29_prereg.replay_windows(64)` / `(8)` | 256 / 32 | `results/phase30_calibration.json::recipe` |
| recipe n64 | `{max_steps: 200, min_refusal_scored_tokens: 15, n_facts: 64, replay_source: [data/dialog_train.bin, data/dialog_train_mask.bin], replay_windows: 256, seed: 1337}` | `results/phase30_calibration.json` |
| calibration commit | `4339f2b2bc29ab0765a821b5d47b617cd6092f24` (`git log --diff-filter=A -- results/phase30_calibration.json`) | git |
| `RUNGS` / `RELEARN_CAP` / `CURVE_K` / `FULL_K` / `DESIGNATED_SEED` / `CHECKPOINT_INTERVAL` | `(50,…,400)` / 400 / 16 / 48 / 1337 / 50 | `phase29_prereg` → `phase27_prereg` |
| `tp.BATCH_SIZE` / `tp.MAX_STEPS` / `tp.BLOCK_SIZE` | 8 / 200 / 256 | `scripts/teach_persona.py:1593, 1599, 105` |
| relearn replay windows | 32, for EVERY leg: `train_relearn_arm` uses `n_facts = len(fs.LOCKED_FACTS)` = 8 | `phase27_relearn.py:586-587` |
| `phase27_prereg.ATTACKER_ARM` / `ATTACKER_PREFIX` | `relearn_attacker` / `phase27` | `scripts/phase27_prereg.py:187-188` |
| `phase25_run.HEARTBEAT_PATH` | `data/phase25_heartbeat.jsonl` | `:286` |
| `phase25_watch.HEARTBEAT_SECONDS` / `STALL_THRESHOLD_MINUTES` | 60 / 5 | `scripts/phase25_watch.py:56, 88` |

**Installation:** none.

## Package Legitimacy Audit

Not applicable: this phase installs no external packages. slopcheck was not run.

## Architecture Patterns

### System Architecture Diagram

```
 developer: launchctl bootstrap + kickstart  (artifacts/com.personacore.phase31.probe.plist)
        │  caffeinate -dims → .venv/bin/python scripts/phase31_probe.py run --heartbeat data/phase25_heartbeat.jsonl
        ▼
 ┌──────────────── POINT PROBE (ARCAL-01) ────────────────────────────────────────────┐
 │ git ls-files results ─► phase30_points.next_action(advr_n64_ratio0p000000, tracked) │
 │      └─ require_calibrated_recipe (tracked results/phase30_calibration.json)       │
 │ plan' = dict(plan, point_key=PROBE_KEY, prefix=PROBE_PREFIX)   [isolation, D-02]   │
 │ train  : tp.train wrapped(on_draw=counter) ─► phase25_points.train_stage(plan')    │
 │          ─► per-step replay counts == 256 × 200 ─► probe train sidecar (data/)      │
 │ measure: phase25_points.measure_stage(plan', training)                              │
 │          (condition (c) + GATE-05 = measure_seconds; recall = scoring_seconds)      │
 │ draw   : phase25_run.draw_point_shapes(PROBE_KEY, k=CURVE_K) ─► per-shape minutes   │
 │ score  : phase25_run.score_point(blob, scoring_values())  (outer bracket)           │
 └─────────────────────────────────┬───────────────────────────────────────────────────┘
                                   │ adapter path + sha256 (probe train sidecar)
 ┌──────────────── RELEARN PROBE (ARCAL-02) ─────▼────────────────────────────────────┐
 │ phase27_relearn.train_relearn_arm(arm="mitigated", point_key=RELEARN_LABEL,        │
 │     leg="n64", seed=1337, cfg=shared_train_config(), start_adapter=probe adapter)  │
 │   └─ 8 resume-chained train() calls to 400 steps, rung adapters under out_dir      │
 │   └─ move results/phase27_relearn_attacker_…/run.csv ─► data/   (dirty-tree fix)   │
 │ for rung in RUNGS: score_rung(point_label=…_rungNNNN_k16)  (recall + 13,824 draws) │
 └─────────────────────────────────┬───────────────────────────────────────────────────┘
                                   ▼ (agent exits; developer boots it out)
 developer on a CLEAN tree:  phase31_probe.py emit point  → commit results/phase31_probe_point.json
                             phase31_probe.py emit relearn → commit results/phase31_probe_relearn.json
                             phase31_budget.py emit        → commit results/phase31_budget.json
        (budget reads committed probe blobs + results/phase25_point_adv_*.json + phase25_recall.json)
                                   ▼
 tests: calibration ⟶ probes ⟶ budget ⟶ every results/phase32_point_*.json  (strict git ancestry)
```

### Recommended Project Structure
```
scripts/phase31_probe.py                        # run (point → relearn) + emit point|relearn; torch lazy
scripts/phase31_budget.py                       # derive + emit; torch-free, committed records only
artifacts/com.personacore.phase31.probe.plist   # copy of the phase26 canary agent, new Label/ProgramArguments/logs
tests/test_phase31_probe.py                     # isolation guard, on_draw bucketing, CPU live-path wiring, emit refusals, plist
tests/test_phase31_budget.py                    # formula recompute, both D-12 branches, stop line, ARCAL-03 ancestry
```
One module could hold both probe and budget, but the budget must stay torch-free. The `test_driver_imports_without_torch` pattern (`tests/test_phase30_points.py:133`) is cheapest to satisfy with a separate module.

### Pattern 1: Re-keyed plan (isolation without editing frozen code)
**What:** Take the Phase 30 plan for the real control key and replace only `point_key` and `prefix`.
**Why it works (verified):** `train_stage` derives `training_sidecar(key)` = `data/phase25_{key}_training.json`, `run_log_dir(key)` = `data/phase25_runs/{key}` and `tp.arm_outputs(arm, prefix=prefix)` (adapter `checkpoints/{prefix}_{arm}_adapter.pt`, checkpoint `checkpoints/{prefix}_{arm}_latest.pt`, transient csv `results/{prefix}_{arm}/run.csv`, moved into `data/phase25_runs/{key}/run.csv`). `measure_stage` uses `measure_sidecar(key)`. `prove_mechanism_matches_pin(live, pinned, point_key=key)` uses the key only in messages (`scripts/phase25_record.py:367-394`). `draws_path(key)` = `data/phase25_{key}_draws.json` requires only the `[A-Za-z0-9_-]` charset (`phase25_prereg.point_record_path`).
```python
# Source: scripts/phase30_points.py::next_action, scripts/phase25_points.py:266-276
action = phase30_points.next_action(phase29_prereg.control_key("n64"), tracked)
_prove(action["action"] == "train", ...)
plan = dict(action["plan"], point_key=PROBE_KEY, prefix=PROBE_PREFIX)
_prove(plan["is_control"] and plan["arm"] == "advr_n64", ...)   # recall is scored only under is_control
```
**Recommended names (discretion, D-02):** `PROBE_KEY = "probe31_advr_n64"`, `PROBE_PREFIX = "probe31"`, `RELEARN_LABEL = "probe31"`. Use a prefix that does NOT start with `phase3`. The transient training csv lands at `results/{prefix}_{arm}/run.csv` before `train_stage` moves it; with a `phase31_…` prefix, a crash mid-training leaves an untracked file inside `phase29_prereg.ARTIFACT_PATHSPECS` (`results/phase31_*`), where one careless `git add results/` would create a v5.0 "result". The prefix must not start with `phase25_points.CALIBRATION_PREFIX_LITERAL` = `phase25_calibration`, and `PROBE_KEY` must not be in `POINT_KEYS()`. Prove both.

### Pattern 2: on_draw replay counting through a wrapped `tp.train` (D-11)
**What:** `train_arm` looks up the module global `train` at call time (`scripts/teach_persona.py:2003`), so rebinding `tp.train` for the duration of `train_stage` injects `on_draw`. The loop passes `on_draw` to both the teaching draw (`get_batch_memmap_masked` via the mask branch, `loop.py:661`) and each replay micro-batch (`loop.py:706`). Val draws do not fire it.
```python
# Source: tests/test_phase30_seam.py:210-243 (the seam test's exact mechanism and bucketing)
events = []
def on_draw(bin_path, ix):
    events.append((pathlib.Path(bin_path) == pathlib.Path(tp.DIALOG_TRAIN_BIN), len(ix)))
real = tp.train
tp.train = lambda **kw: real(**kw, on_draw=on_draw)
try:
    training = phase25_points.train_stage(plan)
finally:
    tp.train = real
# bucket: a teaching draw opens a step; replay draws land in the step they follow
per_step = []
for is_replay, n in events:
    if not is_replay: per_step.append(0)
    else: _prove(per_step, "replay before teaching"); per_step[-1] += n
_prove([n for r, n in events if not r] == [tp.BATCH_SIZE] * tp.MAX_STEPS, ...)
_prove(per_step == [phase29_prereg.replay_windows(64)] * tp.MAX_STEPS, ...)
```
The loop draws 256 windows as 32 micro-batches of 8 (`loop.py:697-704`). The sum per step is what equals 256. Record `per_step` (200 ints), or a run-length form plus the exact equality result.

### Pattern 3: Stage timing without touching frozen code
| Stage | Where the number comes from | Recommended record field |
|---|---|---|
| train | `training["seconds"]` (bracket around the training call inside `train_stage`: bins + 200 steps + export + 2 masked-PPL sweeps) + the probe's own outer `time.monotonic()` bracket | `stages.train.{instrument_seconds, outer_seconds}` |
| condition (c) + GATE-05 | `measured["measure_seconds"]` | `stages.measure` |
| condition (c) alone (optional) | wrap `phase25_condition_c.measure_condition_c` for the call, restore in `finally`, the same idiom `train_stage` uses on `tp.DPSGD` | `stages.condition_c` |
| taught recall (D-03) | `measured["scoring_seconds"]` (`tp.score_arm`, only when `plan["is_control"]`) | `stages.recall` |
| attack draws | `blob["shapes"][f]["timing"]["minutes"]` per shape from `draw_point_shapes` + outer bracket | `stages.draw.{per_shape, outer_seconds}` |
| scoring | outer bracket around `score_point` | `stages.score` |

Keep Phase 25's `measure` granularity (condition (c) + GATE-05 together) as the budget unit. That is the only granularity at which Phase 25's n8/n64 ratios exist (`measure_seconds`). A separate condition (c) figure is descriptive only.

For relearning, `train_relearn_arm` has no internal timer. Bracket it as a whole. Per rung, bracket `score_rung`, then split draws out by reading the draw cache `data/phase25_{label}_draws.json` (`shapes[*].timing.minutes`). Recall + corpus build + scoring is the remainder, or wrap `tp.score_arm` for an exact recall figure.

### Pattern 4: Run/emit split with dirty-first refusal (Phase 26 canary / Phase 30 calibration idiom)
**What:** The long run writes only gitignored sidecars under `data/`. A separate `emit` step on a clean tree assembles the write-once record.
```python
# Source: scripts/phase30_calibration.py:237-270
_prove(not out_path.exists(), f"{_rel(out_path)} exists — REFUSING to overwrite ...")
pathspec = ("scripts", "src", "results", f":(exclude){_rel(out_path)}")
refuse_if_dirty(who="phase31_probe", detail="...", pathspec=pathspec, cwd=_ROOT)
blob["provenance"] = {"module_sha256": {rel: _sha256(_ROOT / rel) for rel in PINNED_MODULES},
                      "git_sha": INSTRUMENT_GIT_SHA, "head_at_write": git_sha(),
                      "written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
phase25_run.atomic_write_json(out_path, blob)
```
Probe records also need `sweep_point: false` + `sweep_point_false_reason` (the `results/phase23_cost.json` field names), the calibration descent (the add commit of `phase30_points.CALIBRATION_PATH`, derived via `git log --diff-filter=A`, plus `git merge-base --is-ancestor <it> HEAD`), `device`, `torch_version`, `gates_nothing: true` on the condition (c) and recall readings, and the Phase 25 twin beside the probe (`results/phase25_point_adv_n64_ratio0p000000.json` + `phase25_recall.json::points.adv_n64_ratio0p000000`).

### Pattern 5: Relearning probe from the lower-level pieces (D-06)
```python
# Source: scripts/phase27_relearn.py:526-690, 692-750; run_curve (:859) is the shape to mirror
trained = phase27_relearn.train_relearn_arm(
    arm="mitigated", leg="n64", seed=phase29_prereg.DESIGNATED_SEED,
    cfg=phase27_relearn.shared_train_config(),
    start_adapter=_ROOT / training["adapter"], expected_sha256=training["adapter_sha256"],
    out_dir=RELEARN_OUT_DIR, device=phase25_run.device(), point_key=RELEARN_LABEL)
# then MOVE results/phase27_relearn_attacker_n64_mitigated_<label>_seed1337/run.csv into data/
for rung in trained["rungs"]:
    reading = phase27_relearn.score_rung(
        point_label=f"{RELEARN_LABEL}_n64_rung{rung['steps']:04d}_k{phase29_prereg.CURVE_K}",
        adapter_path=_ROOT / rung["adapter_path"], k=phase29_prereg.CURVE_K,
        out_dir=RELEARN_OUT_DIR, device=phase25_run.device(),
        facts=fs.LOCKED_FACTS, values=phase25_points.scoring_values())
```
`arm="mitigated"` is right: v5.0 relearning on an admitted point is a mitigated arm from that point's adapter. `train_relearn_arm` refuses a mitigated arm without a `point_key`, and it validates the key only for presence. `model_from_adapter` checks the adapter's fingerprint against `checkpoints/convbase_slim.pt`. Verified this session: a `train_arm`-exported adapter (`checkpoints/phase25_ratio0p000000_adv_n64_adapter.pt`) loads under that fingerprint (`git_sha 04e724c…, step 4000`), so the probe's own adapter will too.

### Anti-Patterns to Avoid
- **Calling `train_stage` with the real key `advr_n64_ratio0p000000`.** That writes `data/phase25_advr_n64_ratio0p000000_training.json`, which Phase 32's `train_stage` would silently REUSE as its control (`phase25_points.py:362-372`). This is the exact D-02 hazard.
- **Using `phase25_run.run_point`.** It calls `phase25_prereg.prove_first_attempt` and `phase25_points.point_plan`, which refuse `advr_*` keys. The WR-05 AST guard also bans `phase25_points.point_plan`/`record_kwargs` in `scripts/phase3[0-4]_*.py`.
- **Calling `phase27_relearn.run_calibrate/run_curve`.** Their first line is `_require_admitted`, and the admission record reads MOOT.
- **Resuming a half-trained probe.** A resumed `train_stage` times only the remaining steps, and the on_draw counts cover only those steps. Refuse when `checkpoints/{PROBE_PREFIX}_advr_n64_latest.pt` exists without a completed probe train sidecar, and name the files to delete in a reviewed step.
- **Typing any number.** Stop line, replay windows, rungs, K: all imported, and the formula recomputes in the test.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Atomic JSON write | own tmp+rename | `phase25_run.atomic_write_json` | `os.replace` census: only `phase25_run.py`/`phase25_record.py` may call it (`tests/test_phase25_driver.py:340`) |
| Dirty-tree refusal | own `git status` | `personacore.provenance.refuse_if_dirty` | Untracked counts as dirty; git failure raises |
| Committed-blob read | `read_text` of a tracked file | `phase30_points._tracked_json(rel, tracked, what)` (CR-01) | Refuses a working-tree edit of a tracked record |
| Ancestry | own `merge-base` loop | `tests/test_phase29_prereg.py::_assert_frozen_before` | Earliest-add, same-commit and shallow-clone traps already handled |
| Heartbeat | own thread | `phase25_run.start_heartbeat` / `beat` | `phase25_watch` reads the same five fields |
| Device resolution | `torch.backends.mps…` | `phase25_run.device()` | The only resolver `score_rung` and `_draw_one_shape` honour |
| Recipe proof | re-derive the recipe | `phase30_points.next_action` / `require_calibrated_recipe` | SC2 refusal against the tracked calibration |
| Plist | new design | copy `artifacts/com.personacore.phase26.canary.plist` | Tested pattern (`test_the_canary_agent_mirrors_the_recall_agent`) |

## Runtime State Inventory

Not a rename/refactor phase. Omitted, except for the new runtime state this phase creates, all gitignored:

| Category | Items created | Action |
|---|---|---|
| Stored data (`data/`) | `phase25_{PROBE_KEY}_training.json`, `_measure.json`, `_draws.json`, `phase25_runs/{PROBE_KEY}/run.csv`, `persona_advr_n64_train.bin`/`_mask.bin` (shared, unprefixed, deterministically rebuilt), `persona_relearn_attacker_n64_mitigated_{label}_seed1337_train.bin`/mask, relearn out_dir (rung adapters, offsets, readings), 8 × `phase25_{label}_n64_rungNNNN_k16_draws.json`, probe stage sidecars, heartbeat lines | Keep until records are committed; a restart deletes them in a reviewed step |
| Checkpoints | `checkpoints/{PROBE_PREFIX}_advr_n64_{adapter,latest}.pt`, `checkpoints/phase27_relearn_attacker_n64_mitigated_{label}_seed1337_latest.pt` | Same |
| OS-registered state | LaunchAgent `com.personacore.phase31.probe` copied into `~/Library/LaunchAgents` | Developer bootstraps/kickstarts and boots out (`launchctl bootout gui/$UID/com.personacore.phase31.probe`) |
| Transient `results/` files | `results/{PROBE_PREFIX}_advr_n64/run.csv` (moved by `train_stage`), `results/phase27_relearn_attacker_…/run.csv` (**NOT moved by `train_relearn_arm`**; the probe must move it) | A leftover dirties the tree and blocks every emit |
| Shared bins note | `data/persona_advr_n64_train.bin` is shared with Phase 32's n64 control (no prefix, `arm_outputs` non-widening). `train_stage` deletes and rebuilds it deterministically when no checkpoint exists | No hazard; name it in the isolation guard's docstring |

## Common Pitfalls

### Pitfall 1: Relearning probe cost is a sweep-point's scoring × 8
**What goes wrong:** The plan assumes relearning is cheap because Phase 27 ran in seconds on CPU.
**Why:** `score_rung` = `tp.score_arm` recall (Phase 25: 893-1041 s) + `draw_point_shapes` over 864 prompts × 16 = 13,824 draws (Phase 25 adv: 46.3-67.9 min) per rung, × 8 rungs.
**How to avoid:** Plan the run as one unattended ~10-14 h LaunchAgent with a human launch checkpoint and a `find`-based completion waiter. Expect the relearn half to dominate.
**Warning signs:** Heartbeat `stage` stuck on rung scoring for hours is normal. More than 5 minutes without a beat is a stall.

### Pitfall 2: `train_relearn_arm` writes a csv under `results/`
`arm_outputs(name, prefix="phase27")` puts the csv at `results/phase27_relearn_attacker_n64_mitigated_{label}_seed1337/run.csv`. Nothing moves it. It dirties `results/`, so `refuse_if_dirty` in every emit refuses, and the clean-tree probe tests (`test_phase23_resume::test_production_resume_epsilon_bit_identical`, `test_phase25_frontier::test_a_perturbed_per_point_count_breaks_the_aggregate`) go red. Move it into the relearn out_dir under `data/` right after training (`shutil.move`, as `train_stage` does at `phase25_points.py:487-495`).

### Pitfall 3: Dry-run tests hide an unwired live path (memory: dry-run-tests-hide-an-unwired-driver)
The probe's live path must be exercised end to end on CPU at fixture scale. Use `tests/test_phase22_wiring.py::_e2e_env` (training; it patches `tp.preflight_device`/`tp.RuntimeConfig`) plus `tests/test_phase27_relearn.py::_e2e_env` (relearn; pins `phase25_run._DEVICE = "cpu"`). Then feed the emitter one record produced by the probe's own record builder, and feed the budget one real probe record with the kwarg set from `inspect.signature`. A test must also confirm the `main()` → `run()` kwargs.

### Pitfall 4: The probe previews the n64 control
Same arm spec, seed 1337, recipe and ratio 0: the probe is the Phase 32 n64 control recipe (bit-identity on MPS not verified, `[ASSUMED]`). v4.0's `adv_n64` control read 1/1008 taught and 0/648 held-out, which is unlearnable under `phase29_prereg.control_is_unlearnable`. The probe's recall may show the n64 leg's D-12 branch early. It gates nothing (D-01), the rule is pre-registered, and Phase 32 must retrain regardless. The record should state this explicitly so nobody treats the probe's recall as the control reading.

### Pitfall 5: Phase 32 recall gap (input for Phase 32, not fixed here)
`phase25_points.measure_stage` scores recall ONLY when `plan["is_control"]`. That is the 25-18 defect that cost 11.6 h. v5.0 needs recall at all 12 points (D-03). The budget prices recall for every trained point, but the Phase 32 driver must add the producer. Record this in the budget's notes.

### Pitfall 6: Repo-wide censuses that new files trip (memory: execute-phase-gates-in-personacore)
- **`train_arm(` grep census** (`tests/test_phase23_resume.py::test_resume_from_none_is_inert`): a raw `grep -rn "train_arm("` over `scripts/` and `tests/` counts PROSE too. Never write `train_arm(` in a docstring or comment in new files; write `train_arm` without the parenthesis. Calling `phase25_points.train_stage` adds no hit.
- **WR-05 AST guard** (`tests/test_phase30_points.py::test_ast_guard_no_v5_module_reaches_a_dp_control`) covers every `scripts/phase3[0-4]_*.py`, so `phase31_probe.py` and `phase31_budget.py`. It bans the names `control_key_for`, `control_reading`, `record_kwargs`, `control_readings`, `_adversarial_extras`, any `phase25_points.point_plan/prefix_for/n_facts_for/exact_axis_value`, `getattr` on those modules, and any non-docstring string constant that starts with `dp_n` or fullmatches a dp key. The budget must not cite the DP sigma0 records by key string. D-09 needs none of them.
- **`os.replace`**: use `atomic_write_json` only.
- **`inject_lora` census** (`tests/test_lora_inject.py`), **`draw_all` / `build_recall_prompt` call-site censuses** (`tests/test_phase14_scoring.py:631, 744`): do not call these directly. `model_from_adapter`, `score_rung` and `measure_stage` already do.
- **`== 10` wall** (`tests/test_phase21_sc5.py`) counts `== 10` / `!= 10` anywhere under `tests/`, comments included. Avoid the literal.
- **`mitigation_gate.ratchet_k`** accepts only K ∈ (48, 24, 16, 8). Tiny fixtures that reach scoring use 8/16.
- **Venue skip pin** (`tests/test_phase25_venue.py`, `_M3_*/_UBUNTU_*_EXPECTED_SKIPS`): any new `skipif`/`needs_adapters`/`pytest.skip` changes CI totals. Write new tests to be honest-green without skipping (the calibration ancestry test returns early when the record is untracked).
- **Pins / frozen files:** do not edit `teach_persona.py` (`_SUPERSEDED_PINS` in `tests/test_phase27_relearn.py` and `tests/test_phase24_record.py`), `phase30_points.py` (`tests/test_phase30_calibration.py:340`), `phase27_relearn.py` or `loop.py`/`data.py` (`results/phase27_admission.json::PINNED_MODULES`), or `phase29_prereg.py`, `phase25_record.py` and `phase20_gate_coverage.py` (frozen before every v5.0 result).

### Pitfall 7: The "~50 min/point" baseline is not a measured number
SC1 says "beside Phase 25's measured ~50 min/point". The committed records say something different. Per-point wall-clock without recall (training + measure + Σ shape minutes) is **49.34-70.82 min, mean 62.81**. The exact twin `adv_n64_ratio0p000000` is **66.99 min** (83.63 with recall). The probe record should publish the twin's per-stage figures and the 12-point min/median/max, never "~50". Likewise "~25-30 h" traces to `25-HUMAN-UAT.md` ("12 points at Phase 25's measured pace"), while the 12 records sum to **12.56 h** (15.88 h with recall). The budget record should state that reconciliation. [VERIFIED: computed this session from `results/phase25_point_adv_*.json` and `results/phase25_recall.json`]

### Pitfall 8: Watching a stray caffeinate from inside the session
The Claude harness spawns its own `caffeinate -i -t 300`. Identify the agent's wrapper as the caffeinate whose ppid is the driver pid (memory: caffeinate-dims-wrapper-is-the-child).

### Pitfall 9: MPS contention from the test suite during the run
`test_phase23_resume::test_production_resume_epsilon_bit_identical` runs on MPS (~105 s) unless `PERSONACORE_SWEEP_ACTIVE` is set. Do not run the full suite while the probe runs, or run it with `PERSONACORE_SWEEP_ACTIVE=1`. The plist sets that variable for the agent.

## Code Examples

### Budget formula (recommended; every input a committed field)
```python
# Inputs (seconds). P = results/phase31_probe_point.json, R = results/phase31_probe_relearn.json,
# A[key] = results/phase25_point_adv_<key>.json, REC = results/phase25_recall.json::points
# n64 per-point stages come from the probe directly:
n64 = {"train": P.train, "measure": P.measure, "recall": P.recall, "draw": P.draw, "score": P.score}
# replay increment per window per step, isolated against the probe's exact twin (no-replay, ratio 0):
per_window = (P.train - A["adv_n64_ratio0p000000"].training.seconds) / (MAX_STEPS * replay_windows(64))
n8 = {
  "train": A["adv_n8_ratio0p000000"].training.seconds + MAX_STEPS * replay_windows(8) * per_window,
  # non-training: Phase 25 n8/n64 ratio, matched by ratio, median over the 6 grid ratios
  **{s: n64[s] * median(A_n8[r].s / A_n64[r].s for r in RATIO_GRID) for s in ("measure", "recall", "draw")},
  "score": n64["score"],   # CPU work; no Phase 25 figure exists (say so)
}
point = {leg: sum(stages.values()) for leg, stages in (("n8", n8), ("n64", n64))}
# D-12 branches per leg: learnable → 6 points trained; unlearnable → control only (5 REFUSED, ~0 s)
per_leg = {leg: {"learnable": len(leg_keys(leg)) * point[leg], "unlearnable": point[leg]} for leg in LEGS}
# D-10 spread per stage: [min/median, max/median] of the 12 v4.0 adv values of that stage
# relearning (priced, 0 h scheduled): arm = R.train + sum(R.rungs[*].seconds);
#   per leg if admitted: (len(FRESH_SEEDS) + 1 control + a mitigated) arms, a ∈ 1..5
stop_line_seconds = 1.5 * upper_bound_total   # D-08; Phase 32 reads this field, never retypes it
```
Measured Phase 25 ratios (n8/n64 by matched ratio, 6 pairs) `[VERIFIED: computed this session]`: draws 0.722/0.859/0.880/0.982/0.953/0.937; measure 1.011/1.017/0.986/1.062/1.020/1.015; recall 0.895/0.897/0.911/0.998/0.987/0.954. Per-stage spread over the 12 adv points: train 0.974-1.141 of median 80.4 s; measure 0.974-1.059 of 86.0 s; draw 0.755-1.107 of 3682.1 s; recall 0.879-1.024 of 1016.2 s.

The exact n8 training scaling rendering is the planner's to lock. The line above is one faithful reading of D-09 ("scales with the replay window count"): the Phase 25 no-replay leg time plus a measured per-window increment. The median-vs-mean choice for ratios is likewise open. Record whichever is chosen, with the formula as a string plus a recompute test.

### ARCAL-03 ancestry test (copy of the calibration guard)
```python
# Source: tests/test_phase30_calibration.py:299-323; helper tests/test_phase29_prereg.py:59-106
from test_phase29_prereg import _assert_frozen_before, _git
BUDGET = "results/phase31_budget.json"
assert BUDGET in phase29_prereg.V5_RESULT_PATHS  # the path is the pre-registration's, proven

def test_budget_precedes_every_sweep_point():
    points = sorted(_git("ls-files", phase29_prereg.POINT_RECORD_PREFIX + "*.json").split())
    if BUDGET not in _git("ls-files", BUDGET).split():
        assert points == [], f"sweep point(s) {points} committed before the ARCAL-03 budget"
        return
    _assert_frozen_before(BUDGET, points)
    # NON-VACUITY (natural RED): the calibration was added before the budget existed
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(BUDGET, [pts.CALIBRATION_PATH])

def test_probes_precede_the_budget():   # the budget is derived FROM them
    for probe in (PROBE_POINT, PROBE_RELEARN):
        ...  # same shape: untracked budget → honest-green; tracked → _assert_frozen_before(probe, [BUDGET])
```
Note: `_assert_frozen_before` also rejects the same commit on both sides. Commit each probe record and the budget in **separate** commits.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| "~25-30 h" unsourced (25-HUMAN-UAT:49) | per-stage × counts from two MPS probes + Phase 25 records | this phase | The committed figure is recomputable |
| v4.0 adv arms: no replay (80 s training) | advr arms: 256/32 replay windows per step via `train()`'s replay seam | Phase 30 | Training is no longer negligible at n64 (estimate below) |
| Phase 27 relearning: CPU apparatus only | one MPS arm on the full ladder | this phase | First real relearning cost |

**Replay training estimate (to be replaced by the probe):** v4.0 adv training is 80 s for 200 steps × 1 micro-batch, including fixed costs. advr_n64 adds 32 replay micro-batches per step, so ~33× the step compute. The rough range is ~6-12 min `[ASSUMED: extrapolated; the DP sigma0 records (dp_n64 1382 s, dp_n8 218 s) are confounded by per-record DP and cannot separate the replay term]`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | One relearning arm ≈ 8.5-11.5 h on MPS (8 rungs × Phase 25 adv recall + draw pace) | Summary, Pitfall 1 | Run scheduling only. The probe measures it; the rung adapters' draw rates may differ from sweep adapters |
| A2 | advr_n64 replay-bearing training ≈ 6-12 min | State of the Art | Point-probe duration only |
| A3 | Total unattended probe run ≈ 10-14 h | Summary | Scheduling of the human checkpoint |
| A4 | MPS training of the probe may reproduce the Phase 32 n64 control bit-for-bit | Pitfall 4 | Interpretation only; nothing gates on it |
| A5 | The n8 training scaling formula (Phase 25 no-replay leg time + per-window increment × 32) is the intended reading of D-09 | Code Examples | Budget arithmetic; the planner/discuss should lock the exact formula |
| A6 | Conditional relearning arm count per admitted leg = 5 fresh + 1 control + a mitigated (a = admitted points in the leg), plus a FULL_K gate re-score per promoted admitted point (superseded: an earlier draft zeroed it under D-15 option 2; see Open Question 2) | Budget formula | Size of the conditional (unscheduled) figure only |

## Open Questions (RESOLVED)

1. **Exact n8 training scaling and ratio statistic (median vs mean, ratio-0 pair vs all 6 pairs).** (RESOLVED: 31-03 Task 1, lock Q1 — replay-window increment form for training, MEDIAN of all 6 matched pairs for the other stages, recomputed by test.)
   - Known: D-09 fixes the shape (replay-window scaling for training, Phase 25 ratios for the rest).
   - Unclear: the precise expression. Recommendation: the formula above, locked in the plan and recomputed by a test from committed files.
2. **Is the FULL_K (48) gate re-score part of the conditional relearning price?** (RESOLVED: YES — 31-03 Task 1, lock Q2, revised in plan-check iteration 1. The recommendation below to price it at 0 was WRONG: D-15 option 2 covers GATE-08 sweep-point promotion, while this re-score is `phase27_relearn.run_gate`'s `promote_at_z` branch (scripts/phase27_relearn.py:999-1011), which runs `score_rung` at FULL_K on each promoted admitted point. It is priced per admitted point as the upper bound max over rungs of (draw_seconds × FULL_K/CURVE_K + remainder_seconds) inside `relearning.conditional`, never in `scheduled`.)
   - Known: `run_gate` re-scores at FULL_K only on promotion. D-15 option 2 pre-registers no promotion.
   - Recommendation: price it as 0 and state why, with a named conditional line if a later ruling promotes.
3. **How are rung scores split (recall vs draws) in the relearn record?** (RESOLVED: 31-02 Task 1 — draw-cache per-shape minutes plus a bracket remainder proved > 0, no `tp.score_arm` patching, no mid-rung resume.)
   - Recommendation: the draw cache's per-shape `timing.minutes` (no patching), with recall + corpus + scoring as the bracket remainder. Wrap `tp.score_arm` only if an exact recall figure is wanted.
4. **Emit the point record before the relearn run starts, or after both?** (RESOLVED: 31-02 Task 2 — one LaunchAgent run, point then relearn; 31-05 emits and commits point then relearn; 31-06 emits and commits the budget.)
   - Recommendation: one LaunchAgent run of both probes (D-12 timing hygiene, no interactive gap), then three separate emit + commit steps: point → relearn → budget. The relearn emit proves its `start_sha256` equals the committed point record's `adapter_sha256`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 venv | everything | ✓ | 3.11.15 | — |
| torch + MPS | probes | ✓ | 2.7.1, `mps.is_available() == True` | none (CPU would invalidate the MPS measurement) |
| `data/dialog_train.bin` / `_mask.bin` | replay source | ✓ | 10.5 MB / 5.3 MB | — |
| `checkpoints/convbase_best.pt` / `convbase_slim.pt` | base for train_arm / model_from_adapter / scorers | ✓ | fingerprint `04e724c…` step 4000 | — |
| `results/phase18_corpus.json` | attack corpus | ✓ | 864 prompts, sha `ff8e6e3c…` | — |
| `/usr/bin/caffeinate`, `plutil`, `launchctl` | LaunchAgent | ✓ | system | — |
| Disk | draw caches (~1 MB each) + checkpoints | ✓ | 478 GiB free (≥ `phase25_prereg.DISK_PRECHECK_BYTES` = 5 GB) | — |

Missing dependencies: none.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 (`pyproject.toml [tool.pytest.ini_options] testpaths=["tests"]`) |
| Config file | `pyproject.toml` |
| Quick run command | `.venv/bin/pytest tests/test_phase31_probe.py tests/test_phase31_budget.py tests/test_phase30_points.py tests/test_phase30_calibration.py tests/test_phase29_prereg.py tests/test_phase23_resume.py -q -p no:cacheprovider` |
| Full suite command | `nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` plus an `until grep -q '^EXIT=' "$LOG"` waiter (~25 min; the Bash tool caps at 600 s) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ARCAL-01 | probe key/prefix/sidecars/adapter/checkpoint/draw cache are disjoint from all 12 Phase 32 keys' `training_sidecar`/`measure_sidecar`/`run_log_dir`/`arm_outputs(prefix=point_plan(k)["prefix"])`/`draws_path`; PROBE_KEY ∉ POINT_KEYS; prefix not `phase3*`/calibration | unit (CPU) | `pytest tests/test_phase31_probe.py -k isolation` | ❌ Wave 0 |
| ARCAL-01 | on_draw bucketing = 256 per step × 200; the lopsided counter-example fails | unit | `-k replay_count` | ❌ |
| ARCAL-01 | live path wired end to end at fixture scale on CPU (train_stage with the wrapped `tp.train` → measure → draw → score → record builder), `main()` kwargs traced | integration (CPU fixture) | `-k live_path` | ❌ |
| ARCAL-01 | emit refuses overwrite, then a dirty tree, before reading sidecars; record has `sweep_point: false`, per-stage seconds, provenance, calibration descent, `gates_nothing` | unit | `-k emit` | ❌ |
| ARCAL-01 | the actual MPS measurement | manual / long-running (LaunchAgent) | human checkpoint | n/a |
| ARCAL-02 | relearn path wired on CPU fixture; the csv is moved out of `results/`; nothing leaks under the real `data/`; start sha = point probe adapter sha | integration (CPU) | `pytest tests/test_phase31_probe.py -k relearn` | ❌ |
| ARCAL-02 | the actual MPS run | manual / long-running | human checkpoint | n/a |
| ARCAL-03 | budget recomputes from committed files (formula string + inputs + source paths); both D-12 branches; stop line = 1.5 × upper bound; relearning scheduled = 0 | unit (torch-free) | `pytest tests/test_phase31_budget.py -q` | ❌ |
| ARCAL-03 | budget precedes every `results/phase32_point_*.json`; probes precede budget; natural-RED non-vacuity | ancestry | `-k ancestry` | ❌ |
| all | new modules pass the WR-05 AST guard, import without torch (budget), `train_arm(` census unchanged | existing censuses | `pytest tests/test_phase30_points.py tests/test_phase23_resume.py -q` | ✅ |
| D-12 | plist mirrors the canary agent (KeepAlive/RunAtLoad false, caffeinate -dims, `PERSONACORE_SWEEP_ACTIVE=1`, logs under `logs/`, distinct stdout) | unit | `-k plist` (plutil lint has `@needs_plutil`; avoid it or account for it in the venue pin) | ❌ |

### Sampling Rate
- **Per task commit:** the quick run command above.
- **Per wave merge:** the full suite on a COMMITTED tree, with no probe run in progress (MPS contention + clean-tree probes).
- **Phase gate:** full suite green before `/gsd:verify-work`; `phase28_report.py check` stays green (it reads ROADMAP/REQUIREMENTS live).

### Wave 0 Gaps
- [ ] `tests/test_phase31_probe.py`: isolation guard, on_draw bucketing, CPU live-path wiring (point + relearn), emit refusals, plist mirror
- [ ] `tests/test_phase31_budget.py`: recompute, branches, stop line, ancestry (import `_assert_frozen_before`, `_git` from `test_phase29_prereg`)
- [ ] No framework install needed

## Security Domain

Local, offline research code with no network, auth or user input. The applicable controls are integrity ones:

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2/V3/V4 | no | — |
| V5 Input Validation | yes | `_prove` on every read (charset via `phase25_prereg.point_record_path`, committed-blob equality via `_tracked_json`, adapter sha256 before load in `model_from_adapter`) |
| V6 Cryptography | yes (integrity only) | `hashlib.sha256` digests; `weights_only=True` loads through `checkpoint.load_adapter` / `load_slim` |

| Pattern | STRIDE | Mitigation |
|---------|--------|------------|
| Probe artifacts reused as a sweep control | Tampering | Re-keyed plan + disjointness test (D-02) |
| Record emitted from a dirty tree | Repudiation | `refuse_if_dirty` before measuring/reading; `head_at_write` |
| Budget edited after the sweep starts | Tampering | Write-once + ancestry test |
| Pickle execution from an untrusted .pt | Elevation | Only own checkpoints; sha256 pin before load |

## Sources

### Primary (HIGH confidence, read or executed this session)
- `scripts/phase29_prereg.py:100-340`; `scripts/phase30_points.py` (full); `scripts/phase25_points.py:1-660`; `scripts/phase25_run.py:95-720`; `scripts/phase27_relearn.py:1-935`; `scripts/teach_persona.py:170-420, 1214-1285, 1672-2135`; `src/personacore/training/loop.py:600-720`; `src/personacore/provenance.py:47-79`
- `tests/test_phase30_seam.py:200-243`; `tests/test_phase30_calibration.py:250-355`; `tests/test_phase29_prereg.py:1-200`; `tests/test_phase30_points.py:130-700`; `tests/test_phase23_resume.py:60-300`; `tests/test_phase25_driver.py:340-365`; `tests/test_phase26_canary.py:515-545`
- `results/phase30_calibration.json`, `results/phase25_point_adv_*.json` (12), `results/phase25_recall.json`, `results/phase23_cost.json`
- `artifacts/com.personacore.phase25.sweep.plist`, `artifacts/com.personacore.phase26.canary.plist`
- `.planning/milestones/v4.0-phases/25-…/25-17-SUMMARY.md:62-76`, `25-HUMAN-UAT.md:44-50`; `.planning/phases/30-…/30-REVIEW.md` (WR-03/WR-04)
- Live executions: `POINT_KEYS()`, `SWEEP_SCHEDULE()`, `point_plan(control_key("n64"))`, the relearn pins, `x18.build_corpus` vs `phase18_corpus.json` (864, identical sha), a `load_adapter` fingerprint check on a `train_arm` adapter, per-stage Phase 25 statistics

### Secondary
- Project memory files (dry-run lesson, censuses, pin continuations, caffeinate wrapper): cross-checked against the code above

### Tertiary (LOW)
- Runtime estimates A1-A3 (extrapolated)

## Metadata

**Confidence breakdown:**
- Standard stack / reuse surface: HIGH. Every symbol was read and most were executed.
- Architecture (re-keyed plan isolation, on_draw wrap): HIGH. Verified against the key's actual uses and the seam test's mechanism.
- Pitfalls/censuses: HIGH. Each census was read at its source line.
- Runtime estimates: MEDIUM-LOW. Derived from committed Phase 25 stage times; the probe exists to replace them.

**Research date:** 2026-09-26
**Valid until:** the next commit touching `phase25_points.py`, `phase25_run.py`, `phase27_relearn.py`, `phase30_points.py` or `teach_persona.py` (all frozen or pinned, so effectively stable)
