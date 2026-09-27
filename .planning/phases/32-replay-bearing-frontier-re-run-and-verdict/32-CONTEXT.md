# Phase 32: Replay-Bearing Frontier Re-run and Verdict - Context

**Gathered:** 2026-09-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Train and score the 12 v5.0 adversarial points (`advr_n8` / `advr_n64` × 6 ratios, from `phase29_prereg.POINT_KEYS()`) unattended on MPS, controls first, inside the committed Phase 31 budget. Each per-point record `results/phase32_point_<key>.json` is written once. Then assemble `results/phase32_frontier.json` write-once, with the verdicts computed by importing the frozen v4.0 gate. The frontier states explicitly whether condition (c) now passes with replay, set against v4.0's recipe-confounded reading (AFRONT-01..03).

This phase does not include admission or relearning (Phase 33), the rendered report (Phase 34), or a promotion or second-seed step: none exists, per Phase 29 D-15 option 2.

</domain>

<decisions>
## Implementation Decisions

### Already locked upstream (carry forward, do not re-decide)

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

### Recall at every point (Pitfall 5)
- **D-01:** Taught and held-out recall is scored **inline in the v5.0 driver's measure stage for all 12 points**, not in a separate post-sweep pass. The driver overrides `measure_stage` in the Phase 30 D-13 import-and-override pattern. **`scripts/phase25_points.py` is not edited**; its recall is gated `if plan["is_control"]:` at `:570`. Every `phase32_point_*` record is born with its own recall, scored before any verdict exists. The Phase 31 budget already prices recall at every point.
- **D-02:** The instrument is the one the controls already use: `teach_persona.score_arm(arm, fs.LOCKED_FACTS, adapter, device)` (`phase25_points.py:572`), which is the same call as v4.0's rescue pass `phase25_recall.py:159`. The record fields and tiers (taught / heldout / *_off, draws_per_question = 1 + N_SEEDED_SAMPLES) match the control block's shape, so the frozen gate's `point_taught_recall` / `point_heldout_recall` kwargs are populated on every point.

### Stop line and run mode
- **D-03:** The cumulative clock is the **sum of the per-stage seconds recorded in the points already completed**. This is the same unit Phase 31 measured to produce the budget. Downtime from a crash, reboot or pause never counts, and any observer can recompute the number from the committed records at any time.
- **D-04:** The check runs **before each point** against the cumulative total. If the total is already ≥ `stop_line.seconds`, the driver pauses. The line can be overshot by at most one point (~2.3 h); there is no predictive check.
- **D-05:** **One LaunchAgent runs all 12 points** in the D-17 order, resuming point by point after a crash (~23 h estimated). The developer launches and boots it out once.
- **D-06:** At the line, the driver **exits 0** after writing a `stop_line` heartbeat stage that carries the cumulative seconds. A relaunch **refuses** unless it is given an explicit flag. The flag carries the developer's ruling text, which is then recorded in the provenance of every point run after it. Unrun points never silently become REFUSED.

### Carried review debt
- **D-07 (WR-03, Phase 30):** Replay is proven by **counting replay windows per step through `train()`'s `on_draw` hook inside the driver**, as in Phase 31 D-11 (`phase31_probe._counting_train`). The per-step list is recorded in each point record (expected 200 × 32 at n8, 200 × 256 at n64 = `phase29_prereg.replay_windows(n)`). **`scripts/teach_persona.py` stays untouched**, and WR-03 stays a named item. The WR-04 check deferred in Phase 30 (`own_control` comparing the recorded replay count with `point_recipe["replay_windows"]`) is implemented against this measured list.
- **D-08 (WR-02, Phase 31):** When writing each point record, the driver **refuses if the pinned modules differ between the commit where the stages ran and HEAD at write time**. This includes stages resumed from a session at a different commit. It turns into code the check that 31-05 did by hand.
- **D-09 (WR-01, Phase 31):** Ownership moves to **Phase 33**. The reason is not shared code: `relearn_out_dir()` belongs only to the closed probe. It is the class of problem, namely where relearning artifacts must live so that `refuse_if_dirty` does not block crash recovery. Phase 33 will face it again when it builds its own mechanism.
- **D-10 (Phase 30 IN-01..04):** Fix only the ones the Phase 32 driver genuinely touches, for example IN-04 (`recipe_identity` ignoring the module named in `REPLAY_SOURCE`) if the driver calls `recipe_identity`. Record the rest as carried. The rule is never to fix code that has no real consumer.

### Point commits and pre-flight
- **D-11:** The **driver commits each point record alone as soon as the point finishes**, following the v4.0 pattern (`phase25_run.commit_point_record` `:756`, `ALLOWED_GIT_ACTIONS = ("add", "commit")` `:751`). D-08 is checked against HEAD at that moment. D-03's clock reads the committed records, and a crash never loses a finished point.
- **D-12:** Before the ~23 h launch, a **CPU fixture-scale live-path test** runs the real driver for one control and one non-control point: train with replay counting, measure with recall, draws, score, write, and commit to a scratch repository. It then **feeds those real producer records into the frontier assembler and into `phase29_prereg.admission()`**. This targets the 25-14 defect class (live path never wired) and the 25-18 class (records missing the recall the gate consumes). A dry-run-only proof is not acceptable.

### Frontier verdict statement (AFRONT-03)
- **D-13:** The comparison lives **inside `results/phase32_frontier.json`** as a `verdicts.condition_c_vs_v4` block. It is additive to `phase29_prereg.FRONTIER_SCHEMA`; the v4.0 frontier carried many fields beyond its schema. For each pair (`adv_nX` ratio r) ↔ (`advr_nX` ratio r), the block holds the v5.0 (c) reading beside the v4.0 reading from `results/phase25_frontier.json`, pinned by sha256. Phase 34 only renders this block.
- **D-14:** The v4.0 side of the **n64 pairs reads "(c) measured, not evaluated"**. It shows the measured `condition_c` values from the v4.0 record (dialogue on/off PPL, retention PPL) and states that the route refused on the control, quoting the reason verbatim: recall floors Y_taught = 0.00069, Y_heldout = 0.0, outside (0,1]. It never counts as FAIL or PASS. The v4.0 side of the n8 pairs is INCONCLUSIVE, with its (c) failure reasons quoted from `verdict.reasons`. A v5.0 leg REFUSED under PREREG-03 appears with its control's k/n reading (Phase 29 D-13), never re-tuned.
- **D-15:** The final statement is **derived from counts**. The emitter picks among fixed template sentences by computed state, for example "with replay, (c) passes at k of 6 ratios at n8; in v4.0, 0 of 6", and binds the numbers. No sentence is typed by hand after the result is seen.
- **D-16:** The frontier **stops at a developer review checkpoint before its commit**, like the budget in 31-06. The run emits without committing and prints the per-point verdicts, the control readings and the comparison block, then waits for "approved". The frontier is write-once and feeds Phase 33 admission.

### Plan-time rulings (2026-09-27, after 32-RESEARCH.md open questions 1-4)
- **D-17 (guard conflict):** `FRONTIER_SCHEMA` requires `verdicts.control_readings`, and the Phase 30 AST guard `_wr05_failures` (`tests/test_phase30_points.py`, `_CARRIERS`) flags that literal in every `scripts/phase30_*`..`phase34_*`, whether it appears as a dict key or as a subscript (verified by running it). This is resolved by a **dated continuation of `_wr05_failures`** that allows `"control_readings"` only as a dict-literal key or a subscript string, with natural-RED cases proving the guard still catches `getattr(..., "control_readings")`, a bare string constant, the attribute, the Name, and the import. There is no per-file allowlist and no derived-key workaround.
- **D-18 (D-15 count at ratio 0):** the advr control is its own reference, so its (c) dialogue half passes by construction. The `condition_c_vs_v4` block therefore emits **both k of 5 (non-controls) and k of 6**, and the template sentence **leads with k of 5 and names the ratio-0 self-reference**. The developer confirms this at the D-16 checkpoint.
- **D-19 (WR-04 location):** the check comparing the recorded replay count against `point_recipe["replay_windows"]` lives **in `phase30_points.own_control`**, not in the Phase 32 driver. This costs the dated `_SUPERSEDED_PINS` continuation in `tests/test_phase30_calibration.py`: a fix commit plus a SHA-registration commit, both landing **before the launch**.
- **D-20 (relaunch past the stop line):** the plist stays single-purpose with fixed argv. A past-the-line relaunch is a **documented manual command** (`caffeinate -dims .venv/bin/python scripts/phase32_points.py run --past-stop-line "<ruling>"`) in the runbook. There is no ruling file and no second plist.

### Claude's Discretion
- The v5.0 driver's module and plist names. They must be inside the pinned `results/phase32_*` result paths and must not collide with `phase25_*` or `probe31*` paths.
- The exact flag name and shape for continuing past the stop line (D-06).
- The template sentences for D-15, provided every state is enumerated and has a test.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and requirements
- `.planning/ROADMAP.md` §"Phase 32: Replay-Bearing Frontier Re-run and Verdict" — goal and SC1-3
- `.planning/REQUIREMENTS.md:619-623` — AFRONT-01..03

### Pre-registration (frozen; import, never edit)
- `scripts/phase29_prereg.py`:
  - `POINT_KEYS()`, `POINT_RECORD_PREFIX` (:139), `V5_RESULT_PATHS` (:148)
  - `FRONTIER_SCHEMA` (:367), `admission()` (:502)
  - `CANDIDATE_UNREPLICATED`, `control_key`, `replay_windows`
- `.planning/phases/29-v5-0-pre-registration-and-carried-debt/29-CONTEXT.md` — D-01..D-15
- `.planning/phases/29-v5-0-pre-registration-and-carried-debt/29-04-SUMMARY.md` — the D-15 option-2 ruling, verbatim
- `scripts/mitigation_gate.py` — the frozen route (`corrected_point_verdict`), GATE-08, `REPLICATION_PENDING_MARKER`

### Driver building blocks
- `scripts/phase30_points.py`:
  - `recipe_identity` (:77), `SWEEP_SCHEDULE` (:130), `point_plan` (:138)
  - `own_control` (:221), `next_action` (:284), `write_refused_records` (:309)
- `.planning/phases/30-replay-bearing-adversarial-recipe-and-its-own-control/30-CONTEXT.md` — D-12..D-19
- `scripts/phase25_points.py` — `train_stage`, and `measure_stage`, whose recall is gated at :570 with the instrument at :572
- `scripts/phase25_run.py`:
  - `atomic_write_json` (:118), heartbeat `beat`/`start_heartbeat` (:298/:350), `disk_precheck` (:439)
  - `run_point` (:633), `ALLOWED_GIT_ACTIONS` (:751), `commit_point_record` (:756)
- `scripts/phase25_recall.py` — the v4.0 rescue pass (the precedent D-01 avoids; the same instrument)
- `scripts/phase31_probe.py` — on_draw replay counting, `refuse_if_dirty`, `PINNED_MODULES`, `calibration_descent`
- `artifacts/com.personacore.phase31.probe.plist` — the D-12 LaunchAgent template

### Committed inputs
- `results/phase31_budget.json` — `stop_line.seconds` (D-03/D-04), per-stage budget
- `results/phase30_calibration.json` — recipe, floor 15 (must precede every scored point)
- `results/phase25_frontier.json` — the v4.0 readings for D-13/D-14. n8: INCONCLUSIVE with (c) FAIL reasons; n64: verdict None, "REFUSED by the sanctioned route before the pin was reached", with `condition_c` measured.

### Carried review findings
- `.planning/phases/30-replay-bearing-adversarial-recipe-and-its-own-control/30-REVIEW.md` — WR-03 (:128), WR-04, IN-01..04 (:202-232)
- `.planning/phases/31-mps-cost-probes-and-budget-commitment/31-REVIEW.md` — WR-01 (to Phase 33), WR-02 (D-08)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `phase30_points` already has the plan, own-control, schedule and `next_action`. The missing piece is the v5.0 runner loop (train → measure+recall → draw → score → write → commit), plus the frontier assembler.
- `phase25_run` supplies survivability: atomic writes, heartbeat, per-shape draw caches, the device preflight and per-point commits.
- `phase31_probe._counting_train` is the on_draw counting wrapper (D-07).

### Established Patterns
- Import-and-override, never edit a frozen module: `phase25_points` and `teach_persona` are pinned by committed records' `module_sha256`, and `_SUPERSEDED_PINS` tripwires guard them.
- Write-once records, each committed alone, with ancestry guards in `tests/test_phase31_budget.py`. The budget-before-every-sweep-point test becomes a live check at the first `phase32_point_*` commit.
- The repo-wide censuses that new files trip: the ISO-06 `inject_lora` register, `os.replace`, `== 10`, `train_arm(` call sites, and the K-menu (8/16/24/48).

### Integration Points
- `phase32_frontier.json` is consumed by `phase29_prereg.admission()` in Phase 33 and rendered in Phase 34.
- The Phase 25 venue skip pin (`tests/test_phase25_venue.py`) may move if new host-gated tests are added.

</code_context>

<specifics>
## Specific Ideas

- Memory lessons that bind this phase: a driver whose live path is never wired can hide behind green dry-run tests (Phase 25); under launchd, `caffeinate -dims` is the parent (find the driver by ppid).
- The developer's standard is that every published number can be recomputed by anyone from committed records (D-03). It is the same discipline as the recompute tripwires.

</specifics>

<deferred>
## Deferred Ideas

- WR-01 (relearn artifacts under a non-ignored `results/` block crash recovery) moves to Phase 33 (D-09).
- Phase 30 IN-01..04 that the Phase 32 driver does not touch stay carried (D-10).
- A WR-03 fix inside `teach_persona.py` stays a named item (D-07).

</deferred>

---

*Phase: 32-replay-bearing-frontier-re-run-and-verdict*
*Context gathered: 2026-09-27*
