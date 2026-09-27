# Phase 32: Replay-Bearing Frontier Re-run and Verdict - Research

**Researched:** 2026-09-27
**Domain:** In-repo driver and assembler work: an unattended 12-point MPS sweep, write-once records, verdicts from the frozen v4.0 route. No new external packages.
**Confidence:** HIGH on code facts (every one read at file:line in this session). MEDIUM on the fixture-scale knobs (derived from reading, not run for Phase 32).

## Summary

Nearly every building block exists already. The missing pieces are (1) a v5.0 runner loop, which walks `phase30_points.SWEEP_SCHEDULE()`, runs train → measure+recall → draws → score → write → commit, and adds the stop-line clock and the WR-02 check; and (2) a frontier assembler. The assembler rebuilds v4.0's `phase25_promotion.curve_pass` loop for the two `advr` legs, taking every control reading from the advr control itself. Phase 31's probe (`scripts/phase31_probe.py:322-491`) is the closest precedent. It already runs the live stage sequence without calling `phase25_run.run_point`, and it counts replay through `on_draw`. The Phase 32 driver should copy that shape.

Five facts the planner cannot get from CONTEXT.md, each measured this session:

1. **Phase 32 cannot call three frozen v4.0 functions.** `phase25_run.run_point`, `phase25_run.commit_point_record` and `phase25_record.build_point_record` all resolve `phase25_*` paths or parse keys that refuse `advr_*`. The driver needs its own record builder and its own one-path commit function.
2. **The frontier's required key trips a guard.** `FRONTIER_SCHEMA` requires the key `verdicts.control_readings`, but the Phase 30 AST guard flags the string literal `"control_readings"` in every `scripts/phase30_*..phase34_*.py`. This was measured: `_wr05_failures('x = {"control_readings": 1}')` returns a failure.
3. **At fixture scale, every control is unlearnable.** Recall comes out 0/1008 (measured), so a real CPU live-path run can never reach a non-control point unless the fixture forces one control count into (0, 1].
4. **The v5.0 n64 control will probably be unlearnable.** The Phase 31 probe ran the same `advr_n64` control recipe on MPS and read taught 0/1008, held-out 1/648 (`results/phase31_probe_point.json::readings.recall`). The budget's n64-unlearnable branch is 12.67 h. The probe is labelled "gates nothing", so this is a planning expectation, not a result.
5. **The (c) comparison at ratio 0 is self-referential.** Under WR-05 the control's `control_gap` is its own gap, so the control point's dialogue half of (c) passes by identity (gap == control_gap sits inside [0.5·g, g+2f]). v4.0 read `adv_n8` against the DP σ=0 control's gap, which was not self-referential. The D-15 count "k of 6" must disclose this or count the five non-controls separately.

**Primary recommendation:**
- Write `scripts/phase32_points.py` (the driver plus its CLI) and `scripts/phase32_frontier.py` (the assembler and write-once emitter).
- The driver reuses `phase25_points.train_stage` and `measure_stage` (with a one-line `is_control=True` plan override for recall), `phase25_run.draw_point_shapes`, `score_point`, `atomic_write_json` and the heartbeat, and `phase30_points.next_action`, `own_control` and `write_refused_records`.
- The assembler calls `phase25_verdict.curve_verdicts(..., "adversarial", capacity, control_readings_by_arm={"adv_n8": <advr_n8 own reading>, "adv_n64": <advr_n64 own reading>})` and stores entries through `phase25_promotion.flat_record`, `pin_kwargs_for` and `early_return_reason`.
- Resolve the `"control_readings"` guard conflict before any code is written.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Already locked upstream (carry forward, do not re-decide)**

**Phase 29:**
- Keys and paths come from `phase29_prereg` (D-01..D-03).
- The frozen gate is imported as the sanctioned route (D-05).
- The admission contract is frozen (D-06..D-10).
- PREREG-03: the control runs first, and a control outside (0,1] short-circuits its leg to REFUSED. The REFUSED record carries k/n counts, and "not re-tuned" is structural (D-11..D-14).
- **D-15 option 2:** no promotion. A would-be PASS stays INCONCLUSIVE with `REPLICATION_PENDING_MARKER`, and admission reads CANDIDATE-UNREPLICATED.

**Phase 30:**
- New arms `advr_*` (D-01).
- A v5.0 driver imports `phase25_points` and overrides only what differs (D-13).
- `phase29_prereg.control_key(leg)` is the single source of a point's control (D-14).
- The WR-05 key+provenance refusal (D-15) and the read-time budget/seed check (D-16).
- The schedule runs `advr_n8` control → `advr_n64` control → the 10 others (D-17/D-18).
- The runtime guard refuses a non-control point before its leg's control exists (D-19).

**Phase 31:**
- The stop line lives in `results/phase31_budget.json::stop_line.seconds` (135,989.46 s = 37.77 h) and is read from there, never retyped (D-08).
- The LaunchAgent pattern is `caffeinate -dims` + heartbeat + logs, launched and booted out by the developer (D-12).

**Recall at every point (Pitfall 5)**
- **D-01:** Taught and held-out recall is scored **inline in the v5.0 driver's measure stage for all 12 points**, not in a separate post-sweep pass. The driver overrides `measure_stage` in the Phase 30 D-13 import-and-override pattern. **`scripts/phase25_points.py` is not edited**; its recall is gated `if plan["is_control"]:` at `:570`. Every `phase32_point_*` record is born with its own recall, scored before any verdict exists. The Phase 31 budget already prices recall at every point.
- **D-02:** The instrument is the one the controls already use: `teach_persona.score_arm(arm, fs.LOCKED_FACTS, adapter, device)` (`phase25_points.py:572`), which is the same call as v4.0's rescue pass `phase25_recall.py:159`. The record fields and tiers (taught / heldout / *_off, draws_per_question = 1 + N_SEEDED_SAMPLES) match the control block's shape, so the frozen gate's `point_taught_recall` / `point_heldout_recall` kwargs are populated on every point.

**Stop line and run mode**
- **D-03:** The cumulative clock is the **sum of the per-stage seconds recorded in the points already completed**. This is the same unit Phase 31 measured to produce the budget. Downtime from a crash, reboot or pause never counts, and any observer can recompute the number from the committed records at any time.
- **D-04:** The check runs **before each point** against the cumulative total. If the total is already ≥ `stop_line.seconds`, the driver pauses. The line can be overshot by at most one point (~2.3 h); there is no predictive check.
- **D-05:** **One LaunchAgent runs all 12 points** in the D-17 order, resuming point by point after a crash (~23 h estimated). The developer launches and boots it out once.
- **D-06:** At the line, the driver **exits 0** after writing a `stop_line` heartbeat stage that carries the cumulative seconds. A relaunch **refuses** unless it is given an explicit flag. The flag carries the developer's ruling text, which is then recorded in the provenance of every point run after it. Unrun points never silently become REFUSED.

**Carried review debt**
- **D-07 (WR-03, Phase 30):** Replay is proven by **counting replay windows per step through `train()`'s `on_draw` hook inside the driver**, as in Phase 31 D-11 (`phase31_probe._counting_train`). The per-step list is recorded in each point record (expected 200 × 32 at n8, 200 × 256 at n64 = `phase29_prereg.replay_windows(n)`). **`scripts/teach_persona.py` stays untouched**, and WR-03 stays a named item. The WR-04 check deferred in Phase 30 (`own_control` comparing the recorded replay count with `point_recipe["replay_windows"]`) is implemented against this measured list.
- **D-08 (WR-02, Phase 31):** When writing each point record, the driver **refuses if the pinned modules differ between the commit where the stages ran and HEAD at write time**. This includes stages resumed from a session at a different commit. It turns into code the check that 31-05 did by hand.
- **D-09 (WR-01, Phase 31):** Ownership moves to **Phase 33**. The reason is not shared code: `relearn_out_dir()` belongs only to the closed probe. It is the class of problem, namely where relearning artifacts must live so that `refuse_if_dirty` does not block crash recovery. Phase 33 will face it again when it builds its own mechanism.
- **D-10 (Phase 30 IN-01..04):** Fix only the ones the Phase 32 driver genuinely touches, for example IN-04 (`recipe_identity` ignoring the module named in `REPLAY_SOURCE`) if the driver calls `recipe_identity`. Record the rest as carried. The rule is never to fix code that has no real consumer.

**Point commits and pre-flight**
- **D-11:** The **driver commits each point record alone as soon as the point finishes**, following the v4.0 pattern (`phase25_run.commit_point_record` `:756`, `ALLOWED_GIT_ACTIONS = ("add", "commit")` `:751`). D-08 is checked against HEAD at that moment. D-03's clock reads the committed records, and a crash never loses a finished point.
- **D-12:** Before the ~23 h launch, a **CPU fixture-scale live-path test** runs the real driver for one control and one non-control point: train with replay counting, measure with recall, draws, score, write, and commit to a scratch repository. It then **feeds those real producer records into the frontier assembler and into `phase29_prereg.admission()`**. This targets the 25-14 defect class (live path never wired) and the 25-18 class (records missing the recall the gate consumes). A dry-run-only proof is not acceptable.

**Frontier verdict statement (AFRONT-03)**
- **D-13:** The comparison lives **inside `results/phase32_frontier.json`** as a `verdicts.condition_c_vs_v4` block. It is additive to `phase29_prereg.FRONTIER_SCHEMA`; the v4.0 frontier carried many fields beyond its schema. For each pair (`adv_nX` ratio r) ↔ (`advr_nX` ratio r), the block holds the v5.0 (c) reading beside the v4.0 reading from `results/phase25_frontier.json`, pinned by sha256. Phase 34 only renders this block.
- **D-14:** The v4.0 side of the **n64 pairs reads "(c) measured, not evaluated"**. It shows the measured `condition_c` values from the v4.0 record (dialogue on/off PPL, retention PPL) and states that the route refused on the control, quoting the reason verbatim: recall floors Y_taught = 0.00069, Y_heldout = 0.0, outside (0,1]. It never counts as FAIL or PASS. The v4.0 side of the n8 pairs is INCONCLUSIVE, with its (c) failure reasons quoted from `verdict.reasons`. A v5.0 leg REFUSED under PREREG-03 appears with its control's k/n reading (Phase 29 D-13), never re-tuned.
- **D-15:** The final statement is **derived from counts**. The emitter picks among fixed template sentences by computed state, for example "with replay, (c) passes at k of 6 ratios at n8; in v4.0, 0 of 6", and binds the numbers. No sentence is typed by hand after the result is seen.
- **D-16:** The frontier **stops at a developer review checkpoint before its commit**, like the budget in 31-06. The run emits without committing and prints the per-point verdicts, the control readings and the comparison block, then waits for "approved". The frontier is write-once and feeds Phase 33 admission.

### Claude's Discretion
- The v5.0 driver's module and plist names. They must be inside the pinned `results/phase32_*` result paths and must not collide with `phase25_*` or `probe31*` paths.
- The exact flag name and shape for continuing past the stop line (D-06).
- The template sentences for D-15, provided every state is enumerated and has a test.

### Deferred Ideas (OUT OF SCOPE)
- WR-01 (relearn artifacts under a non-ignored `results/` block crash recovery) moves to Phase 33 (D-09).
- Phase 30 IN-01..04 that the Phase 32 driver does not touch stay carried (D-10).
- A WR-03 fix inside `teach_persona.py` stays a named item (D-07).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AFRONT-01 | The 12 points (6 ratios × 2 capacities) are trained and scored unattended on MPS, per-point records write-once under the new keys | Driver loop (§Pattern 1), stop-line clock (§Pattern 3), refused-leg path via `phase30_points.next_action`/`write_refused_records`, one-path commit (§Pattern 5), plist (§Pattern 7). Keys and paths come from `phase29_prereg.POINT_KEYS()` (`:112`) and `point_record_path` (`:142`). |
| AFRONT-02 | A new frontier record is assembled write-once; the verdict is computed by import of the frozen v4.0 gate; every v4.0 record stays byte-unchanged | Assembler via `phase25_verdict.curve_verdicts` (`:504`), which calls `phase20_gate_coverage.corrected_point_verdict` (`:522`) (§Pattern 6). v4.0 byte guard: `git diff --quiet v4.0 HEAD -- 'results/phase25_*' ...`. The `v4.0` tag exists locally and on origin (measured). |
| AFRONT-03 | The verdict states explicitly whether (c) now passes with replay, against v4.0's recipe-confounded reading | `condition_c_vs_v4` block from `phase29_prereg.cleared_abc` (= `phase27_prereg.cleared_abc` `:261`) over both frontiers. v4 n8 reads (c) False on 6/6; v4 n64 reads (None, None, None), REFUSED (measured). Enumerated D-15 templates (§Pattern 8). |
| ACTRL-01 (held) | The arm's own ratio-0 control is the sole source of recall floors, `control_gap` and relearning Z | Phase 32 is its first real use on the floors and `control_gap`. See §ACTRL-01 evidence. Z (`control_baseline`) is first consumed in Phase 33. |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Python 3.11 venv at `.venv` is mandatory; never validate with system python 3.14. Measured: `.venv` runs 3.11.15, torch 2.7.1, MPS available.
- Python + PyTorch only; core ML from scratch; no HF model code. No new dependency (RPT-05: runtime deps identical across milestone tags).
- Primary training is local M3/MPS in fp32: no AMP, no GradScaler, no `torch.compile`.
- Offline CSV logging only; no wandb or network.
- Tests are CPU-only and GPU-free (`pytest`, `make test`).
- Work through GSD; commit only what the plan asks. `branching_strategy: none`, so commits land on `main`.
- Secrets never committed.
- Obsidian second-brain note at completion (developer's global CLAUDE.md). This is the orchestrator's concern, not the plans'.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Schedule, per-point plan, own-control read, PREREG-03 refusal | `phase30_points` (frozen-ish, pinned) | `phase29_prereg` | Already built. Phase 32 calls it and never re-implements it. |
| Train / measure / draw / score one point | `phase25_points` + `phase25_run` (frozen) | `teach_persona`, `loop.py` | Frozen stage functions with their own sidecars under `data/`. |
| Replay counting (WR-03), recall at every point (D-01), stop line, WR-02, record write + commit | NEW `scripts/phase32_points.py` | — | The v5.0-specific wiring, done by import-and-override. |
| Verdicts (gate) | `phase25_verdict.curve_verdicts` → `phase20_gate_coverage.corrected_point_verdict` → pin | — | The sanctioned route. It is never re-typed (AST census). |
| Frontier assembly, `condition_c_vs_v4`, D-15 statement, write-once emit | NEW `scripts/phase32_frontier.py` | `phase25_promotion` helpers | CPU-only, torch-free arithmetic over committed records. |
| Persistence | git (committed `results/phase32_*`) | gitignored `data/`, `checkpoints/` | Records are evidence. Sidecars, adapters and draw caches are working state. |
| Unattended execution | launchd LaunchAgent (`caffeinate -dims`) | heartbeat file | This is the Phase 31 D-12 pattern. |

## Standard Stack

No new libraries. Everything used is already a project dependency: stdlib (`json`, `hashlib`, `subprocess`, `argparse`, `pathlib`, `time`, `datetime`), `torch` (lazy), and `pytest` 8.x for tests.

| Component | Where | Purpose |
|-----------|-------|---------|
| `phase29_prereg` | `scripts/phase29_prereg.py` | Keys, paths, `refused_record`, `admission`, `cleared_abc`, `point_verdict_string`, `FRONTIER_SCHEMA` |
| `phase30_points` | `scripts/phase30_points.py` | `SWEEP_SCHEDULE`, `point_plan`, `next_action`, `own_control`, `control_dialogue_pair`, `write_refused_records`, `_tracked_json`, `calibration_record` |
| `phase25_points` | `scripts/phase25_points.py` | `train_stage`, `measure_stage`, `attack_corpus`, `scoring_values`, `_family_counts`, sidecar path fns |
| `phase25_run` | `scripts/phase25_run.py` | `atomic_write_json`, `draws_path`, `draw_point_shapes`, `score_point`, `beat`, `start_heartbeat`, `HEARTBEAT_PATH`, `device`, `disk_precheck`, `head_sha` |
| `phase25_verdict` | `scripts/phase25_verdict.py` | `curve_verdicts`, `never_taught_anchors`, `ARM_LEGS`, `ADV_ARMS` |
| `phase25_promotion` | `scripts/phase25_promotion.py` | `flat_record`, `pin_kwargs_for`, `early_return_reason`, `REPLICATED_AT_SECOND_SEED` (NOT `control_readings`, which is a carrier) |
| `personacore.provenance` | `src/personacore/provenance.py` | `git_sha`, `refuse_if_dirty(:47)` |

**Package Legitimacy Audit:** not applicable. The phase installs no external package. slopcheck was not run, because there is nothing to check.

## Verified Symbol Map (file:line, read this session)

**`scripts/phase29_prereg.py`** (do not edit; the ancestry guard at `tests/test_phase29_prereg.py:109` reddens on any commit after the first `results/phase3*`):
- `GATE_ROUTE = phase20_gate_coverage.corrected_point_verdict` (:92). CONTEXT names `mitigation_gate` as "the frozen route", but the pin is `mitigation_gate.mitigation_point_verdict`, and a direct call is forbidden by the `tests/test_phase20_correction.py:1377` caller census. The route is `phase20_gate_coverage.corrected_point_verdict`.
- `COVERAGE_FLOOR_REFUSAL_MARKERS` (:93), `ADVR_ARMS` (:100), `_V4_TWIN` (:101), `LEGS` (:102), `point_key(arm, ratio)` (:105), `POINT_KEYS()` (:112, a function), `control_key(leg)` (:120), `leg_keys(leg)` (:126).
- `POINT_RECORD_PREFIX = "results/phase32_point_"` (:139). `point_record_path(key)` (:142) returns `results/phase32_point_<key>.json` and refuses non-keys.
- `V5_RESULT_PATHS` (:148-158) contains exactly `"results/phase32_frontier.json"` and `POINT_RECORD_PREFIX + "*.json"`. No other `phase32_*` result path is pre-registered, so the driver must never write anything else under `results/phase32_*` that gets tracked.
- `ARTIFACT_PATHSPECS` (:161) = `results/phase30_*`..`results/phase34_*`.
- `REPLAY_SOURCE` (:168), `replay_windows(n)` (:171) → 32 at n8, 256 at n64.
- `control_is_unlearnable(tk, tn, hk, hn)` (:190), `V4_ADV_N64_READING` (:204), `REFUSED_RECORD_FIELDS` (:210), `_RECIPE_FIELDS` (:218), `refused_record(key, *, taught, heldout, recipe)` (:230).
- `point_verdict_string`, `cleared_abc` (:331-332, from `phase27_prereg:240/:261`), `REFUSED` (:333), `V4_VERDICTS` (:334).
- `CONTROL_BASELINE_SOURCE` (:342) = `results/phase32_point_{control_key}.json::adapter_sha256`. The point record therefore MUST carry a top-level `adapter_sha256`.
- `EXPECTED_POINTS` (:361) = 12, `CANDIDATE_UNREPLICATED` (:364), `FRONTIER_SCHEMA` (:367-385), `recall_threshold` (:388), `_own_control_mismatch` (:440), `admission(frontier)` (:502).

**`scripts/phase30_points.py`** (pinned by `results/phase30_calibration.json`; any commit to it must be added to `tests/test_phase30_calibration.py:350 _SUPERSEDED_PINS`):
- `RECIPE_FIELDS` (:49, six fields), `CALIBRATION_PATH` (:54), `recipe_identity(leg)` (:77, where IN-04 lives at :94-97), `prereg_recipe` (:103).
- `SWEEP_SCHEDULE()` (:130). Measured order: n8 control, n64 control, the n8 ratios 0.25→1.909, then the n64 ratios.
- `point_plan(key)` (:138). `prefix = "phase32_" + ratio part` (:145), e.g. `phase32_ratio0p250000`.
- `_tracked_json(rel, tracked, what)` (:184) reads `git show HEAD:<rel>` and refuses an on-disk edit. `calibration_record` (:200), `require_calibrated_recipe` (:204).
- `own_control(key, tracked, *, point_recipe)` (:221) reads from the control record: `point_key`, `arm`, `axis == "ratio"`, `q is None`, `clip_norm is None`, `recipe == point_recipe`, `seed`, `training.train_config.{seed,max_steps}`, `composed_steps` (WR-04, :247-258).
- `control_floors` (:262) reads `taught_recall.{numerator,denominator}` and `heldout_recall.{...}`. `control_dialogue_pair` (:269) reads `condition_c.point_dialogue_ppl_on/off`. `control_baseline` (:275) reads `adapter_sha256`.
- `next_action(key, tracked)` (:284) returns `{"action":"train","plan":...}` or `{"action":"refuse","records":{5 keys}}`. `write_refused_records(records)` (:309) is write-once, resumable and whole-leg.

**`scripts/phase25_points.py`** (do not edit):
- `training_sidecar(key)` (:266) → `data/phase25_<key>_training.json`; `measure_sidecar` (:270); `run_log_dir` (:274). These do not collide with `advr` keys.
- `train_stage(plan)` (:350). Its blob (:496-521) carries `adapter`, `adapter_sha256`, `seconds` (post-resume leg only, :432), `resumed_from_step`, `live_mechanism`, `train_config` (asdict), `git_sha` (:520, HEAD at train end) and `stats`.
- `measure_stage(plan, training)` (:536). The only use of `plan["is_control"]` is the recall gate at :570. The instrument is at :572. The blob (:610-621) carries `capability`, `exposure`, `gate05_gaps`, `zero_extraction_has_nll`, `recall` (taught/heldout/taught_off/heldout_off/per_family_gain, the tier shape at :575-583), `measure_seconds` (condition (c) + GATE-05 only) and `scoring_seconds` (recall only).
- `attack_corpus()` (:637), `scoring_values()` (:655), `_family_counts(scored)` (:662).
- `record_kwargs` (:731) is a forbidden carrier: it reads the DP control through `control_reading` → `control_key_for`.

**`scripts/phase25_run.py`** (do not edit):
- `atomic_write_json(path, blob)` (:118). This is the ONLY allowed atomic write; the `os.replace` census is below.
- `draws_path(key)` (:180) → `data/phase25_<key>_draws.json`.
- `HEARTBEAT_PATH` (:286) = `data/phase25_heartbeat.jsonl`. `HEARTBEAT_FIELDS` (:291) has five fields. `STAGES` (:295) is informational; `beat()` does not validate the stage.
- `beat(path, *, point, stage, shape, draw_index)` (:298), `start_heartbeat(path, state)` (:350) returns `(stop, thread)`.
- `head_sha()` (:392), `device()` (:407; tests patch `_DEVICE`), `disk_precheck()` (:439, 5 GB).
- `draw_point_shapes(key, *, adapter, adapter_sha256, corpus, corpus_sha256, k, state)` (:458) returns `(blob, digests)`. `score_point(blob, values)` (:586) returns `(per_question, per_fact, scored)`.
- `run_point` (:633), `commit_point_record` (:756) and `main` (:882) are all hard-wired to `phase25_*` paths. **Do not call them.**
- `ALLOWED_GIT_ACTIONS = ("add","commit")` (:751), `READ_ONLY_GIT_ACTIONS` (:753).

**`scripts/phase31_probe.py`** (the template to copy, not to import from):
- `_GIT_ROOT` (:37), `PINNED_MODULES` (:73-84), `per_step_replay(events)` (:156).
- `prove_replay_counts(events, expected, *, batch_size, steps)` (:172).
- Stage-seconds schema (:242-265): `stages.{train,measure,recall,draw,score}.seconds`, where draw = 60 × Σ shape minutes.
- `_counting_train` (:390-395): `tp.train` is replaced by a wrapper that passes `on_draw=_on_draw` and restores it in `finally`. `_on_draw(bin_path, ix)` classifies a draw as replay iff `Path(bin_path) == Path(tp.DIALOG_TRAIN_BIN)`.
- `calibration_descent()` (:499), `_emit_target` (:512, overwrite refusal first, then dirty refusal), `_write_record` (:537).

**Hook plumbing:**
- `train(..., on_draw=None)` is at `src/personacore/training/loop.py:269`. It is passed to both the teaching draw (:661) and the replay draw (:706).
- `get_batch_memmap_masked(..., on_draw=None)` calls `on_draw(bin_path, ix)` (`src/personacore/training/data.py:93,:122`).
- `teach_persona` calls `train(` by module-global name (`scripts/teach_persona.py:2003`), which is why patching `tp.train` works.
- `gets_replay = arm in DP_ARMS + REPLAY_ARMS` (`teach_persona.py:1772`). `REPLAY_ARMS` (:323). `arm_spec("advr_*")` → the `adv_*` twin (:1264).

**Gate side:**
- `phase25_verdict.ARM_LEGS` (:138) = `{'dp': ('dp_n8','dp_n64'), 'adversarial': ('adv_n8','adv_n64')}` (measured). `POINT_RECORD_FIELDS` (:186), `CONTROL_READING_FIELDS` (:200), `never_taught_anchors()` (:222).
- `curve_verdicts(records, arm, capacity, *, control_readings_by_arm)` (:504). The leg is chosen by `leg.endswith(f"n{capacity}")` out of `ARM_LEGS[arm]`, so the mapping MUST be keyed `adv_n8`/`adv_n64` (the v4.0 leg names). It is fed the advr readings.
- `phase25_promotion.flat_record(key, record, recall_entry)` (:129) reads `record["per_family_counts"]`, `record["condition_c"]`, `record["zero_extraction_has_nll"]` and `recall_entry["taught_recall"|"heldout_recall"|"source"]`.
- `early_return_reason` (:221), `pin_kwargs_for(flat, arm, control, anchors, whole_curve)` (:229), and the `curve_pass` entry shape (:293-318).
- `phase20_gate_coverage.corrected_point_verdict` (:522). Its recall-floor `_prove` sits near :641-648, BEFORE `coverage_verdict`, so a one-point curve on an unlearnable control refuses cleanly. Measured: `curve_verdicts(flats[:1], 'adversarial', 64, ...)` with a 0/1008 reading raises SystemExit carrying both markers.
- `mitigation_gate`: `V4_VERDICTS` (:85), `REPLICATION_PENDING_MARKER` (:149), `F_Y = 0.7` (:203), `K_RUNGS = (48,24,16,8)` (:254), `ratchet_k` (:917).
- `phase25_condition_c.control_gap_for_capacity` (:646), `prove_control_gap_not_borrowed` (:668). The latter refuses an identical object or an equal (on, off) pair across legs. `adapter_off` IS equal across the legs (4.573349214207799, the base model), but `adapter_on` differs, so the pair differs.

**Committed inputs (measured values):**
- `results/phase31_budget.json::stop_line` = `{"seconds": 135989.45825294734, "hours": 37.77..., "factor": 1.5, "consumer": "Phase 32 reads ...stop_line.seconds; never retype it"}`. `sweep.scheduled.estimate` = 82724.75 s (22.98 h). Branches: n64-unlearnable 45610 s (12.67 h); both-unlearnable 13787 s.
- The budget path constant is `phase31_budget.BUDGET_RECORD` (:44), derived from `V5_RESULT_PATHS`. `phase31_budget.build_record` (:334) stays valid after sweep points exist; only `emit` refuses (:395).
- `results/phase30_calibration.json::recipe.{n8,n64}` = `{max_steps 200, min_refusal_scored_tokens 15, n_facts, replay_source [data/dialog_train.bin, data/dialog_train_mask.bin], replay_windows 32|256, seed 1337}`.
- `results/phase25_frontier.json`, sha256 `1f182b40c9d7c316e57ecd69acd62c7f6407514b9c675bdf8ec677d3f0cb97d5` (measured):
  - `points[adv_n8_*].verdict.verdict == "INCONCLUSIVE"` on all 6. `cleared_abc` → c False on 6/6.
  - `points[adv_n8_*].verdict.reasons` contains the two strings starting `"(c) dialogue on-off gap ..."` and `"(c) retention PPL ..."`.
  - `points[adv_n64_*].verdict.verdict is None`. `early_return_reason == "REFUSED by the sanctioned route before the pin was reached"`. `reasons[0]` is the verbatim floor refusal (`Y_taught=0.0006944444444444444, Y_heldout=0.0`), identical to `verdicts.leg_refusals.adv_n64`.
  - `points[adv_*].condition_c.{point_dialogue_ppl_on, point_dialogue_ppl_off, point_retention_ppl, control_gap, gap_noise_floor, retention_noise_floor}`.
  - `verdicts.control_readings.adv_n64.recall_counts = {taught [1,1008], heldout [0,648]}`; `adv_n8` = `{taught [879,1008], heldout [482,648]}`.

## Architecture Patterns

### System Architecture Diagram

```
launchctl kickstart ─► caffeinate -dims (child) ◄── python phase32_points.py run [--past-stop-line "<ruling>"]
                                                         │ banner (phase25_venue), refuse_if_dirty(scripts,src,results*)
                                                         ▼
     for key in phase30_points.SWEEP_SCHEDULE():      ◄── tracked = git ls-files results/
        ├─ tracked(point_record_path(key))? ──yes──► skip
        ├─ clock = Σ stages.*.seconds over COMMITTED phase32_point_* (REFUSED → 0)
        │     clock ≥ budget.stop_line.seconds and no ruling ─► beat(stage="stop_line") ; exit 0
        ├─ act = phase30_points.next_action(key, tracked)
        │     "refuse" ─► write_refused_records(act.records) ─► commit each untracked path alone
        │     "train"  ─► run_point_v5(plan):
        │         train_stage(plan) under counting tp.train ─► replay sidecar (per-step list)
        │         measure_stage(dict(plan, is_control=True)) ─► capability, exposure, RECALL
        │         draw_point_shapes(k=CURVE_K) ─► score_point ─► per_question / scored
        │         control_gap: own capability (control) | own_control(...).condition_c (non-control)
        │         build v5 record (stages, replay, recall, condition_c, counts, provenance)
        │         D-08: git diff --name-only <every session sha> HEAD -- PINNED_MODULES == ∅
        │         write-once atomic_write_json(results/phase32_point_<key>.json) ─► commit alone
        └─ (loop)

phase32_frontier.py emit  (CPU, torch-free, after all 12 tracked)
   committed 12 records ─► per leg: flat_record → curve_verdicts("adversarial", cap, {adv_n8:R8, adv_n64:R64})
        SystemExit with COVERAGE_FLOOR_REFUSAL_MARKERS ─► verdict None + early_return_reason (REFUSED)
        PREREG-03 refused records ─► verdict None + early_return_reason, control_recall_counts carried
   ─► points / tallies / tallies_by_leg / control_readings / condition_c_vs_v4 (v4 frontier pinned by sha256)
   ─► D-15 statement from counts ─► admission(frontier) self-check (must not be INCONCLUSIVE)
   ─► write-once results/phase32_frontier.json (no commit) ─► print ─► DEVELOPER "approved" ─► commit
```

### Recommended Project Structure
```
scripts/phase32_points.py      # driver + CLI (run); record builder; stop-line clock; one-path commit
scripts/phase32_frontier.py    # assembler + write-once emit (+ D-15 templates)
artifacts/com.personacore.phase32.sweep.plist   # copy of the phase31 probe plist, own label/logs
tests/test_phase32_points.py   # unit + AST guards + D-12 live-path fixture
tests/test_phase32_frontier.py # assembler/emitter + templates + v4 byte guard
```
Names: the `probe31` / `phase25_calibration` prefixes are refused. The runtime `data/` names are `data/phase32_<key>_replay.json` and `data/phase32_<key>_sessions.json`. The frozen stage functions write `data/phase25_<advr key>_*`; these are unique because the keys are unique.

### Pattern 1: Driver loop (copy of `phase31_probe.run_point_probe` and `phase25_run.main`)
- **Skip on tracked.** Skip a key whose record is already tracked, as `phase25_run.main` :909-914 does.
- **Refuse partial training.** Refuse a checkpoint without a training sidecar, and a training sidecar without a replay sidecar, exactly as the probe does (:357-369). A resumed training cannot count the earlier steps' replay, so a mid-training crash requires a reviewed delete of `checkpoints/phase32_<ratio>_<arm>_latest.pt`. This costs at most one training leg: 2.7 min at n8, 10.6 min at n64.
- **Heartbeat.** Mutate a shared `state` dict and call `start_heartbeat` once per point. Write the `"done"` state before `stop.set()`, as the probe's comment explains.
- **Two-root split.** Use `_ROOT` for `data/` (patchable) and `_GIT_ROOT` for git and `results/`. For D-12 the git root must also be patchable to a scratch repo. Unlike the probe, whose `_GIT_ROOT` is "never patched", the Phase 32 fixture must redirect commits. Recommendation: one patchable `_GIT_ROOT` used for every git call and for `results/`, plus `phase30_points._ROOT` patched to the same scratch repo, since `_tracked_json` runs `git show` there.

### Pattern 2: Replay counting (D-07) and WR-04
```python
# Source: scripts/phase31_probe.py:386-427 (copy, don't import the private closure)
events, real_train = [], tp.train
def _counting_train(**kwargs):
    def _on_draw(bin_path, ix):
        events.append((pathlib.Path(bin_path) == pathlib.Path(tp.DIALOG_TRAIN_BIN), len(ix)))
    return real_train(**kwargs, on_draw=_on_draw)
tp.train = _counting_train
try:
    training = phase25_points.train_stage(plan)
finally:
    tp.train = real_train
per_step = phase31_probe.prove_replay_counts(events, expected, batch_size=tp.BATCH_SIZE, steps=tp.MAX_STEPS)
```
- `phase31_probe.per_step_replay` and `prove_replay_counts` are public functions and can be imported. Importing `phase31_probe` runs `git_sha()` at import (:57), which is harmless.
- `expected` must come from `phase30_points.calibration_record(tracked)["recipe"][leg]["replay_windows"]`, cross-checked against `phase29_prereg.replay_windows(n)` (probe :370-375).
- Record it as `record["replay"] = {"per_step": [...], "expected_per_step", "steps", "teaching_windows_per_step"}`, the probe's field names.
- **WR-04:** add to `phase30_points.own_control` (the root cause; Phase 33 consumes it too): `record["replay"]["per_step"] == [point_recipe["replay_windows"]] * point_recipe["max_steps"]`. This changes `phase30_points.py`, so it needs a `_SUPERSEDED_PINS` continuation (see Pitfall 7) and an update to `tests/test_phase30_points.py::_good_control` (:238), which must gain a `replay` block.

### Pattern 3: Stop-line clock (D-03/D-04/D-06)
- `line = phase30_points._tracked_json(phase31_budget.BUDGET_RECORD, tracked, "the ARCAL-03 budget")["stop_line"]["seconds"]`. Never a literal.
- `clock = Σ_{tracked phase32_point_*} Σ_stage record["stages"][stage]["seconds"]`, read from COMMITTED blobs through `_tracked_json`. A record with `rule == "PREREG-03"` contributes 0. Any other record without `stages` is a refusal (malformed).
- **Check before each point.**
  - If `clock ≥ line` inside the loop: `beat(hb, point=key, stage="stop_line", shape=f"cumulative_seconds={clock}", draw_index=None)` and return 0. `shape` is opaque diagnostic text to the watcher (`phase25_watch.py:414-415` prints it verbatim). This keeps the five-field beat, so no new writer is needed.
  - If `clock ≥ line` at session start with no ruling: raise SystemExit, i.e. refuse. That is D-06's relaunch refusal.
- **Flag (discretion):** `--past-stop-line "<ruling text>"`. It is accepted only when `clock ≥ line`; refuse it otherwise, so it cannot be pre-armed. Every point record written after it carries `provenance.stop_line = {"seconds": line, "cumulative_before_point": clock, "past_line_ruling": text|None}`.
- Stage seconds use the probe's schema: train = `training["seconds"]`, measure = `measured["measure_seconds"]`, recall = `measured["scoring_seconds"]`, draw = 60 × Σ `blob["shapes"][f]["timing"]["minutes"]`, score = the monotonic bracket around `score_point`.

### Pattern 4: Recall at every point (D-01), the lazy override
```python
def measure_stage(plan, training):
    """D-01: the frozen stage with recall on for every point; only is_control is overridden."""
    return phase25_points.measure_stage(dict(plan, is_control=True), training)
```
- `plan["is_control"]` is read only at `phase25_points.py:570`. The `arm == "dp_n8"` reproduction branch (:593) is unreachable for `advr_*`. The instrument, tiers and sidecar are identical to the control's.
- The record's own `is_control` comes from the real plan.
- Test: a non-control record carries `taught_recall`, `heldout_recall`, `taught_recall_off`, `heldout_recall_off` and `per_family_gain` with integer counts and `draws_per_question == 1 + recall.N_SEEDED_SAMPLES`.

### Pattern 5: One-path commit (D-11), ported from `commit_point_record`
- Resolve the path with `phase29_prereg.point_record_path(key)`.
- Before staging, refuse if the path is not under `results/`, is missing, or `git status --porcelain -- <path>` is empty.
- Run `git add -- <path>` and then `git commit -m "feat(32): record sweep point <key>"`.
- Verify `git show --name-only --format= HEAD == [path]`.
- Also check the branch before committing: `git rev-parse --abbrev-ref HEAD == "main"`. Peer sessions switch branches mid-run (memory: concurrent agents).
- Git surface: `{add, commit}` plus read-only `{ls-files, show, rev-parse, status, diff, log, merge-base}`. Enforce it with an AST test that reuses `tests/test_phase25_driver.py::_git_surface_failure` (:132) and `_git_argv_subcommands` (:105).
- For a REFUSED leg, commit each of the 5 files alone. On a retry, commit only the paths that are still untracked. `write_refused_records` accepts byte-identical existing files (:320-331).

### Pattern 6: Frontier assembly through the frozen route (AFRONT-02)
```python
# Per leg; readings from each leg's OWN advr control record (committed)
R = {twin: {"adapter_on": cc_on, "adapter_off": cc_off, "taught_recall": tk/tn, "heldout_recall": hk/hn}
     for twin in phase25_verdict.ADV_ARMS}          # keys adv_n8/adv_n64, values from advr_n8/advr_n64
flats = [phase25_promotion.flat_record(k, rec[k], {**rec[k], "source": point_record_path(k)})
         for k in measured_keys_of_leg]
try:
    results = phase25_verdict.curve_verdicts(flats, "adversarial", cap, control_readings_by_arm=R)
except SystemExit as refusal:   # ONLY the floor refusal is a refusal (25-REVIEW WR-02)
    _prove(all(m in str(refusal) for m in phase29_prereg.COVERAGE_FLOOR_REFUSAL_MARKERS), str(refusal))
    results = [None] * len(flats)
kwargs = phase25_promotion.pin_kwargs_for(flat, "adversarial", R[twin], phase25_verdict.never_taught_anchors(), whole_curve)
```
- Each entry takes the `curve_pass` shape (:293-318): `{**kwargs, leg, route, whole_curve_inputs, recall_counts, k, k_source, verdict, reasons, early_return_reason}`. `early_return_reason` comes from `phase25_promotion.early_return_reason(reasons)`, or is `"REFUSED by the sanctioned route before the pin was reached"` on a floor refusal.
- **Unlearnable leg:** the control is routed alone and refuses with the markers, the same text as v4.0's. The 5 PREREG-03 keys get `verdict None`, a non-empty `early_return_reason` and the record's `control_recall_counts`. `admission` skips absent fields on REFUSED entries (:469-470) but checks `control_recall_counts` when present (:477-479).
- `verdicts.tallies` and `tallies_by_leg` must re-derive exactly as `admission` does (:563-571). The leg name is `key.rsplit("_",1)[0]` = `advr_n8`.
- `verdicts.control_readings[advr_leg].recall_counts.{taught,heldout}` = `[k, n]` int lists.
- `point_keys = list(POINT_KEYS())`.
- Before writing, run `phase29_prereg.admission(frontier)` and prove the verdict is not INCONCLUSIVE. This is a free self-check and the D-12 consumer.
- `replicated_at_second_seed = phase25_promotion.REPLICATED_AT_SECOND_SEED` (False). The v5.0 tallies can therefore never contain a PASS: a would-be PASS returns INCONCLUSIVE with `REPLICATION_PENDING_MARKER`, which is D-15 option 2.

### Pattern 7: LaunchAgent (D-05)
- Copy `artifacts/com.personacore.phase31.probe.plist` and set Label `com.personacore.phase32.sweep`. Args: `/usr/bin/caffeinate -dims <venv python> scripts/phase32_points.py run --heartbeat data/phase25_heartbeat.jsonl`. Logs: `logs/phase32_sweep.{out,err}`.
- Keep the same env (`PERSONACORE_SWEEP_ACTIVE=1`) and set `KeepAlive`/`RunAtLoad` false.
- Test it with `plistlib` against the canary plist, the way `tests/test_phase31_probe.py::test_plist_mirrors_the_canary_agent` does. **Do not use `plutil -lint`.** That would add a host-gated skip on ubuntu and move the `tests/test_phase25_venue.py` skip pin.
- Under launchd the driver is the PARENT and `caffeinate` is its child: find the wrapper by ppid == driver pid (memory; `phase25_venue.launch_banner()` prints the identity).
- **Relaunching past the line requires the flag.** The plist's fixed argv cannot carry the flag. Either the developer edits a copy of the plist, or runs the CLI manually under caffeinate. State this in the plan's operator notes.

### Pattern 8: D-13/D-14/D-15, `verdicts.condition_c_vs_v4`
- One row per (leg, ratio): `v5_key`, `v4_key` (`phase25_record.point_key(f"adv_{leg}", r)`), `v5.cleared_c = cleared_abc(v5_entry)[2]`, `v5.condition_c` values, `v4.verdict = point_verdict_string(v4_point)`, `v4.cleared_c = cleared_abc(v4_point["verdict"])[2]` (False on n8, None on n64).
- `v4.condition_c` holds the measured values from `points[v4_key]["condition_c"]`. `v4.quoted_reasons`: on n8 the reasons whose text starts with `"(c)"`; on n64 `reasons[0]` verbatim, labelled "(c) measured, not evaluated".
- Plus `v4_source = {"path": "results/phase25_frontier.json", "sha256": ...}`, computed live and never typed.
- Enumerated states per leg:
  - v5 {learnable with c_pass = k ∈ 0..6, REFUSED under PREREG-03 with the control's k/n}
  - v4 n8 {INCONCLUSIVE, c 0 of 6}
  - v4 n64 {REFUSED by route: measured, not evaluated}
- The template keys are (leg, v5 state); the numbers are bound from counts. Test every state, including k = 0, 1..5, 6 and REFUSED.
- **Self-reference disclosure (Pitfall 5):** carry `control_self_referential_dialogue: true` on the ratio-0 row, and state k over the 5 non-controls beside k over 6.

### Anti-Patterns to Avoid
- **Calling `phase25_run.run_point`, `commit_point_record` or `phase25_record.build_point_record`.** They write or refuse `phase25_*` paths. `build_point_record` refuses `advr` keys at `parse_point_key`.
- **Calling `phase25_points.record_kwargs`, `control_reading`, `control_key_for`, `_adversarial_extras` or `phase25_promotion.control_readings`.** These are WR-05 carriers, and the AST guard `tests/test_phase30_points.py:536-544` reddens.
- **Typing constants:** the stop line, 32/256, 200, 1337, 15, F_Y, grid values, `"results/phase32_frontier.json"` (take it from `V5_RESULT_PATHS`), `"adversarial"` (take it from `ARM_LEGS`).
- **A dry-run-only test battery** (memory: 25-14/25-18).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Atomic JSON write | tmp + `os.replace` | `phase25_run.atomic_write_json` | The `os.replace` census (`tests/test_phase25_driver.py:341`) allows only two files |
| Verdict computation | Local gate or condition logic | `phase25_verdict.curve_verdicts` + `phase25_promotion.pin_kwargs_for` | AFRONT-02 says "by import". Local defs named `corrected_point_verdict`/`cleared_abc`/`mitigation_point_verdict` are flagged by `_gate_retype_failures` |
| (c) pass/fail per point | Parsing reason strings | `phase29_prereg.cleared_abc(entry)` | The frozen condition functions; "reason strings are never parsed" |
| Own-control read, PREREG-03 refusal | New readers | `phase30_points.next_action` / `own_control` / `write_refused_records` | WR-05, D-16, D-19 are already tested |
| Replay per-step bucketing | New bucketing | `phase31_probe.per_step_replay` / `prove_replay_counts` | Already tested (WR-02 of Phase 30) |
| Draw resume, scoring | New loops | `phase25_run.draw_point_shapes`, `score_point` | Shape-keyed resume and identity refusal |
| Tracked-blob read | `open()` on results | `phase30_points._tracked_json` | CR-01: reads the committed blob and refuses a working-tree edit |

## Runtime State Inventory

Not a rename phase. Runtime state that matters for this phase:

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | `data/persona_advr_n64_train*.bin` (shared arm bins, rebuilt by `train_stage` on non-resume). `data/phase25_probe31_*` and `checkpoints/probe31_*` (probe, distinct keys). No `phase32` or `phase25_advr_*` artifacts exist (measured `ls`) | None |
| Live service config | 7 personacore LaunchAgents in `~/Library/LaunchAgents` (phase25 ×5, phase26, phase31). None is `phase32` | Developer copies the new plist in, then boots it out after the run |
| OS-registered state | The Claude harness's own `caffeinate -i -t 300` | Take read-backs from a detached process (memory) |
| Secrets/env vars | `PERSONACORE_SWEEP_ACTIVE=1` in the plist; pytest skips MPS legs under it | Run any pytest during the 23 h run with this flag set |
| Build artifacts | None | None |

## Common Pitfalls

### Pitfall 1: The `"control_readings"` literal is flagged by the Phase 30 WR-05 guard
**What goes wrong:** `FRONTIER_SCHEMA` (:380) requires `verdicts.control_readings`, but `tests/test_phase30_points.py::_wr05_failures` (:567) flags any non-docstring string constant equal to a carrier name, and `control_readings` is one (:542). Measured: `x = {"control_readings": 1}` is flagged, while `control_readings_by_arm=` as a keyword argument is not.
**How to avoid:** a developer ruling, before any code is written. Two options:
- (a) Amend `_wr05_failures` with a dated continuation. Exempt a `"control_readings"` Constant only when it is a `Dict` key or a `Subscript` slice (a JSON field name), keep the `getattr`/Name/Attribute forms flagged, and add a planted-RED case to `test_ast_guard_planted_red_per_class` (:647). **Recommended.**
- (b) Derive the key without a literal. This is guard evasion, and a reviewer would flag it.
**Warning sign:** `pytest tests/test_phase30_points.py::test_ast_guard_no_v5_module_reaches_a_dp_control` goes RED the moment `scripts/phase32_frontier.py` lands.

### Pitfall 2: Fixture-scale controls are unlearnable, so the non-control path is unreachable
**What goes wrong:** the `_e2e_env` fixture model scores taught 0/1008 and held-out 0/648 (measured by running `tests/test_phase31_probe.py::_point_probe_fixture`). `next_action` on any non-control therefore returns `"refuse"`, and a "one control + one non-control" live test never trains a non-control.
**How to avoid:** in the D-12 fixture, spy `tp.score_arm`. Run it for real, then replace the taught and held-out counts on the n8 CONTROL only with a learnable pair, e.g. (700/1008, 400/648). Leave the n64 control natural (0/1008), so the REAL PREREG-03 refusal path writes and commits 5 REFUSED records. Recommended scope: run the full `SWEEP_SCHEDULE` at fixture scale. That is 7 trained points × ~13 s (the phase31 fixture measured 13.1 s per point) ≈ 95 s. It yields all 12 records, so the assembler and `admission()` get real producer records with no copies. The fallback is 3 real points plus 4 cloned n8 records.
**Fixture knobs:**
- `mitigation_budget.STEP_BUDGET → tp.MAX_STEPS` (2 under `_e2e_env`). Otherwise `recipe_identity` refuses at :83, and `own_control`'s WR-04 check compares 200 with 2.
- A scratch git repo with a committed calibration (`recipe_identity(leg)` for both legs, under the fixture) and a committed forged budget with a huge `stop_line.seconds`.
- `phase30_points._ROOT` and the driver's roots pointed at the scratch repo, plus `phase25_points._ROOT`, `phase25_run._DEVICE="cpu"`, `phase25_run.DRAWS_DIR` and `phase14_recall.CONVBASE_SLIM` / `RECALL_MAX_NEW_TOKENS` / `phase19_erasure.RETENTION_BIN` / `attack_corpus` subset, as the probe fixture does at `tests/test_phase31_probe.py:310-351`.
- MEDIUM confidence: `STEP_BUDGET` is read at call time in `recipe_identity` and `pinned_mechanism`. Verify that nothing else caches it.

### Pitfall 3: The transient training csv sits under `results/phase32_*`
**What goes wrong:** `teach_persona.arm_outputs` puts the csv at `results/<prefix>_<arm>/run.csv` (`teach_persona.py:390`), which is `results/phase32_ratio0p000000_advr_n8/run.csv` here. `train_stage` moves it to `data/` only after training (:487-494). After a crash mid-training, a restart's `refuse_if_dirty(pathspec=("scripts","src","results"))` aborts on the untracked directory. This is the WR-01 class, which D-09 moved to Phase 33, but it bites Phase 32's own restarts.
**How to avoid:** add run-time pathspec excludes derived from `point_plan(k)["prefix"]` + `"_" + arm` for the 12 keys, e.g. `":(exclude)results/phase32_ratio0p250000_advr_n8"`. Derive them; never type them. Keep the full `results/` check at record write, excluding only the record itself, as `_emit_target` does.
**Warning sign:** a restart dies with "REFUSING: the working tree is dirty. ?? results/phase32_…_advr_…/".

### Pitfall 4: D-08 needs a per-session sha that the frozen sidecars do not keep
**What goes wrong:** only the training sidecar records `git_sha` (`phase25_points.py:520`). The measure sidecar and the draw cache record none, so stages resumed in a later session have no sha to compare.
**How to avoid:** the driver appends `git_sha()` at each session's start into `data/phase32_<key>_sessions.json` (atomic). At write time, for every sha in `sessions ∪ {training.git_sha}`, run `git diff --name-only <sha> HEAD -- *PINNED_MODULES`, which must be empty. `refuse_if_dirty` on `scripts src` at session start makes each session's sha equal the code that ran.
- PINNED_MODULES (recommended): the driver itself, `phase25_points.py`, `phase25_run.py`, `phase30_points.py`, `phase29_prereg.py`, `phase31_probe.py` (counting helpers), `teach_persona.py`, `src/personacore/training/loop.py`, `src/personacore/training/data.py`, `phase14_recall.py`, `phase18_extraction.py`, `phase25_condition_c.py`, `phase25_gate05.py`.
- Record `provenance.module_sha256` of the same tuple.
- The per-point commits touch only `results/`, so the check stays green between points.
**Warning sign:** any fix to `scripts/` committed mid-sweep. It correctly refuses the next record write, so land every code change BEFORE launch.

### Pitfall 5: The ratio-0 (c) reading is self-referential under WR-05
**What goes wrong:** `control_gap` is the control's own `adapter_on - adapter_off`, so at the control `gap == control_gap ∈ [F_C·g, g + k·f]`. Its dialogue half passes by identity, and only retention can fail. The probe's control retention was 3.8227 against a cap of 3.9085. A "k of 6" count that includes the control inflates k by one.
**How to avoid:** the D-15 templates report both counts (non-controls k/5 and all six), or the developer rules at the D-16 checkpoint. Surface this in the plan as a question for the checkpoint, not as a silent choice.

### Pitfall 6: The v5.0 n64 control is expected to be unlearnable
**What goes wrong:** the Phase 31 probe (same recipe, seed and code, MPS) read `advr_n64` taught 0/1008 and held-out 1/648. If Phase 32 reproduces it, the n64 leg is REFUSED under PREREG-03: 5 REFUSED records, the n64 control routed alone to the floor refusal, and a run of ~12.7 h rather than 23 h.
**How to avoid:** nothing is avoided, since the rule is pre-registered. But plans must fully implement and test the REFUSED-leg path (Pattern 5, Pattern 6, Pattern 8), and the D-15 statement must enumerate "n64 REFUSED under PREREG-03 with control k/n" against v4.0's "measured, not evaluated". Never re-tune.

### Pitfall 7: `phase30_points.py` edits trip the `_SUPERSEDED_PINS` tripwire
**What goes wrong:** `tests/test_phase30_calibration.py:350` allows exactly the three commits (CR-01, WR-04, WR-05) to have touched `phase30_points.py` since `4339f2b`. Any WR-04-replay or IN-04 edit turns it RED.
**How to avoid:** commit the code first, then add that commit's full SHA to `_SUPERSEDED_PINS` in a second commit with a dated comment. This is the Phase 30 pattern. Both commits land before launch (Pitfall 4).
- IN-04 is "touched", because `next_action` → `recipe_identity` → `require_calibrated_recipe` runs on every point (D-10).
- The lowest-churn IN-04 fix: in `recipe_identity`, prove `name.split(".",1)[0] == "teach_persona"` for each `REPLAY_SOURCE` name.
- IN-01, IN-02 and IN-03 are not touched and stay carried.

### Pitfall 8: Repo-wide censuses that a new file trips (measured; the gate subset runs in 4.5 s)
- `os.replace` is allowed only in `phase25_run.py` and `phase25_record.py` (`tests/test_phase25_driver.py:341`).
- The textual grep for `train_arm(` over `scripts` and `tests` (`tests/test_phase23_resume.py:255`, register `:60`). NEVER write `train_arm(` in phase32 code, docstrings or tests.
- The `== 10` literal census over `tests/` (`tests/test_phase21_sc5.py:280`). No `== 10` / `!= 10` in phase32 tests.
- The ISO-06 `inject_lora` register (`tests/test_lora_inject.py:450`). Phase 32 never calls `inject_lora`, so keep it that way.
- The mitigation_point_verdict caller census (`tests/test_phase20_correction.py:1377`) and the accountant census over `phase29..34` (`tests/test_phase29_prereg.py:589`): no `phase25_epsilon` import, and none of `epsilon_for`/`sigma_for`/`delta_*`.
- The WR-05 carrier/dp-key guard over `phase30..34` (`tests/test_phase30_points.py:636`). No string starting `"dp_n"`, no carrier names (Pitfall 1).
- The K menu: `mitigation_gate.K_RUNGS = (48,24,16,8)`. Fixture K must be 8 or 16; the driver uses `mitigation_budget.CURVE_K` = 16.
- The ancestry guards: `phase29_prereg.py`, `phase25_record.py` and `phase20_gate_coverage.py` must NOT be edited (`tests/test_phase29_prereg.py:109,:130`). `tests/test_phase31_budget.py:406` (budget before every sweep point) becomes live at the first `phase32_point_*` commit, and it holds (budget at d22a017).
- `"descriptive_step_mix"` string constants are allowed only in `phase30_calibration.py` (`tests/test_phase30_calibration.py:250`).
- The skip pin (`tests/test_phase25_venue.py`, `_UBUNTU_*` sums): do not add `skipif`, `needs_adapters`, `needs_plutil` or in-body `pytest.skip` in phase32 tests. If one is unavoidable, add a named leg plus a dated continuation.
- Eleven clean-tree probes fail while `scripts/`, `tests/` or `results/` are dirty (memory). Run the full suite only on a committed tree.

### Pitfall 9: A refused-leg retry and no-op commits
**What goes wrong:** after a crash between committing refused records 2 and 3, the rerun skips the tracked keys, calls `next_action` again for the next key, and `write_refused_records` writes nothing new. A naive "commit all 5" then hits the no-op refusal on the committed paths.
**How to avoid:** commit only records whose `git status --porcelain -- <path>` is non-empty.

### Pitfall 10: `training.seconds` covers only the post-resume leg
`train_stage` times only the run after `resume_from` (:415-432). Because the driver refuses mid-training resumes (Pattern 1), the recorded `train` stage is always a full leg. State this in the record (`resumed_from_step == 0` is proved), or the D-03 clock undercounts.

## Code Examples

The only code snippets needed are in Patterns 2, 4 and 6. All are adapted from committed code cited inline (`phase31_probe.py:386-427`, `phase25_points.py:570`, `phase25_promotion.py:261-318`).

## State of the Art

| Old Approach (v4.0) | Current Approach (v5.0) | Impact |
|--------------|------------------|--------|
| Adversarial arm trained with no replay | `advr_*` gets `replay_windows(n)` per step through the `gets_replay` seam | (c) is tested against the ratio, not the recipe |
| `control_gap` from the DP σ=0 control (`phase25_promotion.control_readings`) | From the leg's own advr control (`phase30_points.control_dialogue_pair`) | WR-05 closed. The ratio-0 row becomes self-referential (Pitfall 5) |
| Recall only at controls, rescued post-hoc (`phase25_recall.py`) | Recall inline at all 12 (D-01) | No 25-18-class rescue pass |
| Operator stop by judgment | Pre-committed stop line read from the budget | D-03/D-04/D-06 |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Patching `mitigation_budget.STEP_BUDGET` to `tp.MAX_STEPS` is the only knob the fixture needs for the recipe, pin and WR-04 checks to agree at fixture scale | Pitfall 2 | The fixture refuses at `recipe_identity`/`own_control`; the plan would need to patch `recipe_identity` instead |
| A2 | The Phase 32 n64 control reproduces the probe's 0/1008 on MPS | Pitfall 6 | Only the run time changes (≈23 h, not ≈13 h); both branches are implemented anyway |
| A3 | `phase25_watch` treats `shape` as opaque text, so the stop-line beat can carry the cumulative seconds there | Pattern 3 | The watcher mis-renders one line; cosmetic only |

## Open Questions

1. **The `"control_readings"` guard conflict (Pitfall 1).** We know the schema requires the key and the guard flags the literal. It is unclear whether the developer prefers a guard amendment or another route. Recommendation: rule on it at plan time. Option (a) is a dated continuation to `_wr05_failures` with a planted RED.
2. **The D-15 count at ratio 0 (Pitfall 5).** It is unclear whether the headline sentence counts 6 or 5 ratios per leg. Recommendation: emit both counts in the block, and have the template name the self-reference. The developer confirms at the D-16 checkpoint.
3. **WR-04 location.** D-07 says "`own_control` comparing". Recommendation: put it in `own_control` (the root cause, and consumed again in Phase 33), and pay the `_SUPERSEDED_PINS` continuation.
4. **The past-the-line relaunch mechanics.** The fixed plist argv cannot carry `--past-stop-line`. Recommendation: document a manual `caffeinate -dims .venv/bin/python scripts/phase32_points.py run --past-stop-line "<ruling>"`, or have the developer edit a copy of the plist.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `.venv` Python | everything | ✓ | 3.11.15 | — |
| torch + MPS | the 12-point sweep | ✓ | 2.7.1, `mps.is_available() == True` | CPU (far slower; not budgeted) |
| git + `v4.0` tag | AFRONT-02 byte guard | ✓ | local and origin (`d09ef39`) | — |
| Disk (5 GB precheck) | `disk_precheck` | ✓ | 481 GiB free | — |
| launchd / caffeinate | D-05 | ✓ | macOS 25.5 | Manual run under caffeinate |
| Committed inputs | the driver | ✓ | `phase30_calibration.json`, `phase31_budget.json`, `phase25_frontier.json`, `phase23_never_taught.json` | — |

The v4.0 records are byte-unchanged since `v4.0` except `results/phase24_token_budget.json`, which is a re-emittable record re-emitted in Phase 30. The AFRONT-02 guard should therefore target `results/phase25_*`, `phase26_*`, `phase27_*` and `phase28_*` with git's quoted pathspec globs, never shell globs (memory: zsh NOMATCH). This was measured with `git diff --stat v4.0 HEAD -- 'results/phase2*'`.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x (`.venv/bin/pytest`) |
| Config file | `pyproject.toml` / Makefile (`make test` = `.venv/bin/pytest -q`) |
| Quick run command | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase32_points.py tests/test_phase32_frontier.py tests/test_phase29_prereg.py tests/test_phase30_points.py tests/test_phase31_budget.py` (the phase29/30/31 trio measured 32 s; add ≈95 s for the D-12 module fixture) |
| Census gate (4.5 s, measured) | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase25_driver.py::test_os_replace_appears_only_in_the_two_phase25_writers tests/test_phase23_resume.py::test_resume_from_none_is_inert tests/test_phase21_sc5.py::test_wall_census_is_the_measured_set tests/test_lora_inject.py::test_every_inject_lora_consumer_reads_the_artifact_config tests/test_phase20_correction.py::test_mitigation_point_verdict_has_no_caller_outside_this_module tests/test_phase30_points.py::test_ast_guard_no_v5_module_reaches_a_dp_control tests/test_phase29_prereg.py::test_no_v5_module_uses_the_accountant tests/test_phase29_prereg.py::test_phase29_prereg_is_frozen_before_every_v5_result tests/test_phase30_calibration.py::test_the_phase30_points_pin_continuation_is_a_tripwire tests/test_phase31_budget.py::test_ancestry_budget_precedes_every_sweep_point` |
| Full suite command | `nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` plus an `until grep -q '^EXIT=' $LOG` waiter. It takes ~25 min, and the Bash tool caps at 600 s. Run only on a committed tree. During the MPS run, prefix with `PERSONACORE_SWEEP_ACTIVE=1` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AFRONT-01 | Schedule walk skips tracked keys; controls first; PREREG-03 leg writes and commits 5 REFUSED alone | unit (scratch repo) | `pytest tests/test_phase32_points.py -k "schedule or refused"` | ❌ Wave 0 |
| AFRONT-01 | Replay per-step counted and recorded; a mismatch halts before measure | unit | `pytest tests/test_phase32_points.py -k replay` | ❌ |
| AFRONT-01 | Recall on every point (non-control carries taught/heldout counts) | live fixture | `pytest tests/test_phase32_points.py -k live_path` | ❌ |
| AFRONT-01 | Write-once: a second write refuses; the one-path commit names exactly one path; git surface AST | unit + AST | `pytest tests/test_phase32_points.py -k "write_once or commit or git_surface"` | ❌ |
| AFRONT-01 | Stop line: clock = Σ committed stages; exits 0 with a `stop_line` beat; relaunch refuses without the ruling; the ruling lands in provenance; the line is read from the budget, not typed (AST) | unit | `pytest tests/test_phase32_points.py -k stop_line` | ❌ |
| AFRONT-01 | D-08: a pinned module changed between session sha and HEAD → write refuses (natural RED in a scratch repo) | unit | `pytest tests/test_phase32_points.py -k wr02` | ❌ |
| AFRONT-01 | Plist mirrors the canary (plistlib, no plutil) | unit | `pytest tests/test_phase32_points.py -k plist` | ❌ |
| AFRONT-02 | Verdicts via `curve_verdicts`; no local gate def; unlearnable leg → route refusal recorded with markers; admission(frontier) is not INCONCLUSIVE on real producer records (D-12) | unit + live fixture | `pytest tests/test_phase32_frontier.py` | ❌ |
| AFRONT-02 | Frontier write-once; refuses unless all 12 tracked; v4.0 records byte-unchanged vs the `v4.0` tag; v4 frontier sha256 pinned | unit | `pytest tests/test_phase32_frontier.py -k "write_once or v4_bytes"` | ❌ |
| AFRONT-03 | `condition_c_vs_v4` rows; v4 n8 c False ×6; v4 n64 "measured, not evaluated" with verbatim reason; every D-15 state has a test | unit | `pytest tests/test_phase32_frontier.py -k "condition_c_vs_v4 or statement"` | ❌ |
| ACTRL-01 | Non-control `control_gap` and control floors equal the advr control's; the WR-04 replay check in `own_control` | unit | `pytest tests/test_phase30_points.py -k wr04` | ✅ file, ❌ case |

### Sampling Rate
- **Per task commit:** the census gate (4.5 s) plus that task's `-k` subset.
- **Per wave merge:** the quick run command.
- **Phase gate:** the full suite green on a committed tree, and the D-12 live-path test green, before the launch checkpoint.

### Wave 0 Gaps
- [ ] `tests/test_phase32_points.py`: driver units, AST guards, the D-12 module-scoped live fixture (reusing `tests/test_phase22_wiring.py::_e2e_env` :715 and the probe fixture's patch set).
- [ ] `tests/test_phase32_frontier.py`: assembler, templates, v4 byte guard.
- [ ] A ruling on Pitfall 1, then the dated continuation in `tests/test_phase30_points.py`.
- [ ] A `_SUPERSEDED_PINS` continuation in `tests/test_phase30_calibration.py` after the `phase30_points.py` edit (WR-04 replay + IN-04), and an updated `_good_control` fixture with a `replay` block.

## ACTRL-01 evidence (held unticked)

Phase 32 is the first real-data use of two of ACTRL-01's three clauses:
- Every non-control's `control_gap` and recall floors come through `phase30_points.own_control` from the committed `advr` control record.
- The frontier stores `control_*_recall == k/n` of those counts, and `admission()` step (1d) re-derives them (:440-480).

Evidence that would bear on ticking it: the committed `phase32_point_*` records plus a test asserting each non-control's `condition_c.control_gap == control_gap_for_capacity(own control condition_c)`, and `admission(committed frontier)` returning a non-INCONCLUSIVE verdict. The third clause, relearning Z (`control_baseline`), is first consumed in Phase 33. Recommendation: Phase 32 records the evidence, and ACTRL-01 is ticked only after Phase 33 uses `control_baseline`, or by explicit developer ruling.

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2/V3/V4 Auth/Session/Access | no | local single-user tooling |
| V5 Input Validation | yes | Keys only from `POINT_KEYS()`. `point_record_path` refuses non-keys (path-traversal T-29-03). The ruling text is stored as data, never executed. |
| V6 Cryptography | yes (integrity only) | stdlib `hashlib.sha256` for pins; never hand-rolled |
| V12 Files | yes | Write-once plus `atomic_write_json`, one-path commits, gitignored working state |
| V14 Config | yes | Git surface `{add, commit}` + read-only (AST-enforced); branch check before commit; no push |

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Post-hoc re-tune after seeing a refused control | Tampering | PREREG-03 structural refusal and write-once records; the frontier refuses without all 12 |
| Stage outputs from different code | Repudiation | D-08 session-sha check plus `module_sha256` |
| An unattended process staging extra paths on `main` | Elevation | One resolved path per commit, name-only verification, AST git surface |
| A DP reading laundered as the advr control | Spoofing | `own_control` axis/q/clip refusals plus the WR-05 AST guard |

## Sources

### Primary (HIGH confidence, read or executed this session)
- `scripts/phase29_prereg.py` (full), `scripts/phase30_points.py` (full), `scripts/phase25_points.py` (full), `scripts/phase31_probe.py` (full), `scripts/phase25_run.py` (:1-913), `scripts/phase25_promotion.py` (:1-340), `scripts/phase25_verdict.py` (:100-631), `scripts/phase20_gate_coverage.py` (:522-720), `scripts/phase27_prereg.py` (:240-290), `scripts/phase25_record.py` (:582-845), `scripts/phase25_condition_c.py` (selected), `scripts/teach_persona.py` (:275-395, :1214-1266), `src/personacore/training/loop.py` (:640-715), `src/personacore/provenance.py` (:47-79)
- Tests: `test_phase29_prereg.py`, `test_phase30_points.py`, `test_phase31_probe.py`, `test_phase31_budget.py`, `test_phase25_driver.py`, `test_phase23_resume.py`, `test_phase21_sc5.py`, `test_phase30_calibration.py`, `test_phase27_relearn.py`, `test_phase25_venue.py`, `test_phase22_wiring.py` (selected ranges, cited inline)
- Records: `results/phase31_budget.json`, `results/phase30_calibration.json`, `results/phase31_probe_point.json`, `results/phase25_frontier.json` (JSON paths printed)
- Executed: the AST-guard probe, the curve_verdicts smoke run with advr readings, the fixture-scale control recall (0/1008), the census subset (10 passed, 4.46 s), the phase29/30/31 trio (132 passed, 32 s), the phase31 live fixture (13.1 s)
- `.planning/phases/30-.../30-REVIEW.md` (WR-03/04, IN-01..04), `.planning/phases/31-.../31-REVIEW.md` (WR-01/02)

### Secondary
- Project memory notes: execute-phase gates, dry-run-hides-unwired-driver, caffeinate child. These are consistent with the code read.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH (in-repo, no external packages)
- Architecture: HIGH (the probe precedent ran on MPS; `curve_verdicts` was exercised with advr readings)
- Pitfalls: HIGH for 1-4 and 6-9 (measured). MEDIUM for fixture knob A1.

**Research date:** 2026-09-27
**Valid until:** the first commit that touches `scripts/phase30_points.py`, `phase25_*` or `teach_persona.py`. Re-check the line numbers then.
