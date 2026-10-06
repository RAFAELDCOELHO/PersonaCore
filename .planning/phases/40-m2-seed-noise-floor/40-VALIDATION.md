---
phase: 40
slug: m2-seed-noise-floor
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-10-05
---

# Phase 40 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Source: 40-RESEARCH.md
> §Validation Architecture, amended by the plan-time ruling in 40-CONTEXT.md "Addendum (2026-10-05)"
> (D-07 tensor-wise comparison; D-08 correction + D-08b residual).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 in `.venv` (Python 3.11), CPU-only, zero skips in Phase 40 files |
| **Config file** | `pyproject.toml` (`make test` = `.venv/bin/pytest -q`) |
| **Quick run command** | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase40_prereg.py tests/test_phase40_noise.py` |
| **Cross-phase guards** | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase35_prereg.py tests/test_phase36_caps.py tests/test_phase36_ledger.py tests/test_phase23_resume.py tests/test_phase21_sc5.py tests/test_lora_inject.py tests/test_phase25_driver.py tests/test_phase14_scoring.py` |
| **Full suite command** | `LOG=<scratchpad>/suite40.log; nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` plus a `run_in_background` waiter `until grep -q '^EXIT=' "$LOG"; do sleep 60; done` (Bash caps at 600 s) |
| **Estimated runtime** | quick ~60 s; guards ~3-5 min (`test_phase23_resume` MPS leg ~105 s); full ~50-55 min (Phase 39: 4300 passed / 4 skipped) |

---

## Sampling Rate

- **After every task commit:** quick run + cross-phase guards
- **After every wave:** full suite. **Record commits (plans 10-11):** the targeted guards after the ledger commit and after each seed commit (plan 10: the untracked noise-floor record blocks the clean-tree probes); the full suite on the committed state after the noise-floor commit and after the report commit (plan 11)
- **Before `/gsd:verify-work`:** full suite green on the committed state
- **Max feedback latency:** ~300 s (quick + guards)

---

## Per-Requirement Verification Map

| Req / Decision | Behavior | Test Type | Automated Command | File Exists | Status |
|---|---|---|---|---|---|
| NOISE-01 / SC1 (S) | `E2_S` read from `results/phase36_budget.json::e2_seed_count` via `fill("e2_S", ...)`, never typed; `SEEDS = seed_list()[:E2_S]`; slot census + ordering legs green | unit + census | `pytest tests/test_phase40_prereg.py -k "e2_s or seeds"` ; `pytest tests/test_phase35_prereg.py -k "slot_census or slot_ordering"` | ❌ W0 | ⬜ pending |
| NOISE-01 (per seed, denominators) | per seed, per group, 7 non-targets (+ target) with n/27 and per tier 14/13 via `_pooled_rows`; never from an arm record's `per_fact` | unit (committed real records) | `pytest tests/test_phase40_prereg.py -k "rows or denominator"` | ❌ W0 | ⬜ pending |
| NOISE-02 / D-02 | pair d = `nontarget_noise_floor(nontarget_deltas(...))`; reproduces 0.14814814814814814 and 0.2592592592592592 on committed records | unit (real records) | `pytest tests/test_phase40_prereg.py -k pair` | ❌ W0 | ⬜ pending |
| D-03 / D-04 | group floor = mean over C(S',2) pairs; published = larger group floor; max/min/every pair; per-slot range, sample SD + population SD beside; ties, S' = 2 | unit (pure) | `pytest tests/test_phase40_prereg.py -k "floor or extras"` | ❌ W0 | ⬜ pending |
| NOISE-02 (no amendment) | record carries v3.0 floor and `e1_condition_b_margin()` 0.2962962962962963 read, not typed; v3.0 floor record/module byte-unchanged (git) | unit + git | `pytest tests/test_phase40_noise.py -k "beside or margin"` | ❌ W0 | ⬜ pending |
| D-05 | estimator entry names sampling noise and common random numbers (same per-question draw seeds across adapters) | unit (AST over entry string) | `pytest tests/test_phase40_prereg.py -k sampling` | ❌ W0 | ⬜ pending |
| D-06 / D-15 | per seed in `seed_list()` order: train full, train M2, A2 full, A2 M2 (+ D-13 last if approved; a D-13 failure never drops the seed: ruling c, row below); one ledger attempt per seed; `require_launch("E2")` before each seed; a mid-seed stop drops that attempt from the estimator; a dropped seed is re-run only under Rafael's R-3 b ruling and only once its re-run is approved and drop_attempt wrote its manifest (`DROPPED_SEED_RERUN`, `rerun_seeds`, `pending_seeds(outcomes, rerun)`; rows below); a relaunch's preflight (and emit) dirty check excludes, via `_launch_pathspec(outcomes)`, exactly the seed + A2 records of whole and dropped seeds plus each dropped seed's in-process csv directory `results/phase40_e2_<arm>` — nothing else | unit (stubbed train/score, tmp ledger) + exact-pathspec test + the real `refuse_if_dirty` on a tmp git rig | `pytest tests/test_phase40_noise.py -k "order or whole_seed or crash or stop"` ; `pytest tests/test_phase40_noise.py -k "relaunch_pathspec or real_git_rig"` | ❌ W0 | ⬜ pending |
| R-3 b (Rafael's conditions, 03de080) — prereg | seed_outcomes refuses an attempt after a whole seed's end line (WR-01); `_approved` refuses a negated or re-cased approved (WR-02); pending_seeds(outcomes, rerun) runs a dropped seed only if in rerun (declined-rerun branch reachable); lost_attempts; dropped_attempt_dir (no ':'; outside results/phase40_*); dropped_manifest_failures checks the manifest alone ((a) approved + cause note, (b) same seed, head vs relaunch_git_sha or a declared change, (c) kept under the attempt dir, (e) the attempt a lost line closed); latest_head_failures / relaunch_declaration_failures compare a launch HEAD only for the latest attempt; R3_CONDITIONS_RULING quoted verbatim at 03de080 | unit (truth tables, synthetic ledgers) + git quote | `pytest tests/test_phase40_prereg.py -k seed_outcomes` (5 tests) ; `pytest tests/test_phase40_prereg.py -k r3_conditions` | ❌ W0 | ⬜ pending |
| R-3 b — driver | partial_outputs enumerates a crashed attempt's files; drop_attempt moves them (never deletes) with sha256 into a write-once manifest (relaunch_git_sha = HEAD at drop), refusing a whole / not_run seed, an open attempt, an existing seed record, a negated approved, an attempt after a whole seed (WR-01); declare_relaunch is the only way past a HEAD moved after drop; rerun_seeds + preflight prove every manifest, every kept sha256 and the latest attempt's HEAD; a dropped seed without manifest is not pending and preflight passes with its outputs in place | unit (rig, tmp ledger) | `pytest tests/test_phase40_noise.py -k "drop_attempt or rerun_needs"` (3 tests) ; `pytest tests/test_phase40_noise.py -k "preflight_pending or relaunch_pathspec"` (declined-rerun rows) | ❌ W0 | ⬜ pending |
| R-3 b — record (c), (d) | seeds.dropped_attempts of a re-run seed lists each lost attempt's manifest (its file sha256 re-proved), kept files re-hashed, per-group attempt-vs-attempt adapter_identity (tensor-wise); seeds.dropped_seed_outputs of a seed left dropped lists its manifests and in-place partial outputs with sha256 | unit (rig) | `pytest tests/test_phase40_noise.py -k dropped_attempts` (2 tests) | ❌ W0 | ⬜ pending |
| D-07 (amended) | new vs committed adapter compared tensor by tensor (`torch.equal` every tensor + metadata), NEVER file sha256: M2@1337 vs `phase19_erase_reference_adapter.pt`, full@1337 vs `persona_adapter.pt` (and full@2024 vs dialogue-floor 2024); not bit-identical → A2-count difference reported as same-seed re-run noise; descriptive | unit (tiny tensors in tmp) + AST (no file-sha comparison) + rehearsal | `pytest tests/test_phase40_noise.py -k "identity or tensor"` ; seeds not whole (1337 or 2024 dropped: entries read "not whole", no KeyError) `pytest tests/test_phase40_noise.py -k without_seed` | ❌ W0 | ⬜ pending |
| D-08 (amended) / D-08b | record states the 72/72 tensor identity of `persona_adapter.pt` and dialogue-floor-1337 (file sha differs by stem) as a correction of the scout note, not a limitation; residual (Phase 18 `run_arm` draws vs `run_erasure_arm`) reported with measured size vs full@1337; labelled a v3.0 limitation ONLY if counts differ on identical weights; if full@1337 weights are not bit-identical → "effects not separable" | unit (truth table over the three outcomes) | `pytest tests/test_phase40_noise.py -k d08` | ❌ W0 | ⬜ pending |
| D-09 / D-10 | gap = on − off from each full A2 record; adapter-off check device-scoped per Rafael's R-1 (`ADAPTER_OFF_RULE`; on mps, off == committed 4.573349214207799 read from `results/phase19_noise_floors.json`; CPU measures 4.573348505014267 → recorded, `adapter_off_matches_committed` false, rehearsal-labelled); pre != post handled per R-2 (`PRE_POST_RULE`); `dialogue_gap` refuses a device that is not the A2 record's `config.device` (WR-03; the driver passes `record["config"]["device"]` after proving it equals the seed record's device), on mps refuses a pre OR post adapter-off off the committed value (IN-02 a) and returns the `pre` block (IN-01); `gap_noise_floor` = mean |Δgap| over pairs, max beside, finite ≥ 0 | unit | `pytest tests/test_phase40_prereg.py -k gap` (6 tests) ; `pytest tests/test_phase40_noise.py -k consumer` (CPU fixture with config.device cpu; device-mismatch and mps legs) | ❌ W0 | ⬜ pending |
| D-11 / D-13 / D-14 | approvals quoted verbatim (APPROVALS_RULING = the first paragraph only, at 03de080); projection reproduces `front_hours.E2`; D-13 NLL count 925/adapter derived; projection ≤ stop (a); new total; approval block in every record; D-13 absent unless approved | unit | `pytest tests/test_phase40_prereg.py -k "approval or projection"` | ❌ W0 | ⬜ pending |
| Record total (Rafael's third paragraph) | approval_block() shows E2 + E5 + E6 = math.fsum(front_hours with E2 projection, phase38_prereg.E5_PROJECTION_HOURS, phase39_prereg.E6_PROJECTION_HOURS) = 78.12639556620314 h (E6 actual-gate 78.12556459250179 h) beside committed 77.72433149898184 h and E2-only 77.78526798055215 h; RECORD_TOTAL_RULING quoted verbatim | unit (exact repr) + git quote | `pytest tests/test_phase40_prereg.py -k record_total` (2 tests) | ❌ W0 | ⬜ pending |
| D-13 failure (Rafael's ruling c, 2026-10-06) | `D13_FAILURE_KINDS`; `d13_block` returns `d13_not_measured` for a gate mismatch or a malformed reading; `run()` catches every exception of the `d13_scores` call alone, SystemExit included, records `d13_not_measured("exception", ...)`, and the seed finishes whole (a KeyboardInterrupt still propagates); the noise-floor record's `d13` = `d13_reading(blocks)` with the blocks beside | unit (prereg) + run loop on fakes + record | `pytest tests/test_phase40_prereg.py -k d13_failure` (1 test) ; `pytest tests/test_phase40_noise.py -k d13_failure` (1 test, four kinds) ; `pytest tests/test_phase40_noise.py -k d13_reading` (1 test) | ❌ W0 | ⬜ pending |
| Seeds and pairs entered (ruling e) | `recall_floor` (full, m2, published) and `gap_noise_floor` carry `n_seeds`, `n_pairs`, `seeds`; the record keeps them as returned and the report prints them; below 2 whole seeds: INSUFFICIENT_SEEDS, no floor key, a stop line, the phase stops for Rafael | unit (prereg) + record + report | `pytest tests/test_phase40_prereg.py -k floors_declare` (1 test) ; `pytest tests/test_phase40_noise.py -k "from_real_committed or insufficient"` | ❌ W0 | ⬜ pending |
| Report items b, g | the 'retrain' label explanation (`a2_label`, from `ENTRIES["a2_pass"]`) printed exactly once; the floor section carries `CONFIRMATIONS["g"]` once beside v3.0's sampling floor read from `results/phase19_noise_floors.json` (`crn_addendum`, never typed) | unit (render) | `pytest tests/test_phase40_noise.py -k render_report_measured` | ❌ W0 | ⬜ pending |
| Three approvals (ruling f) | `record_layout["approvals"]`: first = ledger + every seed record with its A2 records, one checkpoint, commits ledger then one per whole seed; second = noise-floor record; third = report | unit (prereg) + checkpoints (plans 10, 11) | `pytest tests/test_phase40_prereg.py -k record_layout` (1 test) | ❌ W0 | ⬜ pending |
| D-12 | 25 full×M2 per-slot differences, 5 same-seed marked, beside v3.0 `delta_taught_to_m2` read from committed record; descriptive | unit | `pytest tests/test_phase40_prereg.py -k d12` | ❌ W0 | ⬜ pending |
| D-16 | one `e2_noise_floor_estimator` fill holding both estimators, frozen | unit | `pytest tests/test_phase40_prereg.py -k fill` | ❌ W0 | ⬜ pending |
| Contract → Phase 41 | `phase40_noise_floor.json` built by real `build_record` from real records passes `fill("e1_condition_c_band_inputs", ...)` (tmp root, synthetic band inputs); band == `dialogue_gap_band(...)` | integration (CPU) | `pytest tests/test_phase40_noise.py -k consumer` | ❌ W0 | ⬜ pending |
| SC3 ordering | prereg + test first-added before every `results/phase40_*`; records write-once | git ancestry | `pytest tests/test_phase40_prereg.py -k "frozen or first_added or records_at_commit"` | ❌ W0 | ⬜ pending |
| Hygiene | no `inject_lora`, no `os.replace`, no `== 10` in tests (use `math.comb`), `train_arm(` registered, instruments imported not redefined (AST), every prereg function called by a test, zero skips | AST census | `pytest tests/test_phase40_prereg.py tests/test_phase40_noise.py -k "census or ast or skips"` ; `pytest tests/test_phase23_resume.py -k inert` ; `pytest tests/test_phase21_sc5.py tests/test_lora_inject.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky. Task IDs are bound by the plans' `<automated>` blocks.*

---

## Wave 0 Requirements

- [ ] `tests/test_phase40_prereg.py` — fills, entries, ancestry, estimator on committed real records
- [ ] `tests/test_phase40_noise.py` — driver refusals, per-seed unit, D-07/D-08 comparisons, emit, consumer feed
- [ ] one register line + sum bump in `tests/test_phase23_resume.py` (`train_arm(` call site)

No framework install needed.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Rafael's "approved" on D-11 (+0 h) and D-13 (+0.0609 h) prices before training, and his three record approvals (ruling f, `record_layout["approvals"]`): the ledger and every seed record with its A2 records in one checkpoint (40-10 Task 1; commits: ledger, then one per whole seed), the noise-floor record (40-10 Task 3; committed in 40-11 Task 1), the report (40-11 Task 2) | SC3 / D-11 / D-14 | human gate | each checkpoint prints the approvals from the prereg and presents what that approved covers; commit only after it; a negated reply is no approval |
| Full-shape CPU rehearsal (MPS hidden, rehearsal arm names, scratch root, tmp ledger) | D-15 / consumer feed | long detached run | `tail -1 <scratch>/rehearsal40<sfx>.log` is `REHEARSAL_EXIT=0` and `git status --porcelain -- scripts src results tests ledger` is empty |
| R-3 b leg on CPU (plan 08 Task 3: planted crash of seed 2024, reconcile, declined branch, drop_attempt, re-run preflight, re-run with real training, emit) | R-3 b | real training, long detached run | `tail -1 <scratch>/rehearsal40_rerun<sfx>.log` is `RERUN_EXIT=0` with six STEP lines; real tree clean |
| The MPS run | NOISE-01 | device + ledger | detached `caffeinate -dims` launch; stop (a) checked by `require_launch("E2")` per seed |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 300 s
- [ ] `nyquist_compliant: true` set in frontmatter

## Plan-check finding origins

| Iteration | Finding | Origin (revision-introduced / pre-existing) |
|---|---|---|
| 1 | B1 CPU adapter_off ≠ committed MPS value → rehearsal emit refuses | initial |
| 1 | B2 run() zero-kwarg real-root defaults unresolved | initial |
| 1 | 9 warnings (D-13 branch, _REPO identity path, rehearsal_disclosure unwired, DR-01, D-11 A2 records, dropped seed, pre!=post, grep-over-prose, key_links) | initial |
| 2 | B relaunch refused by preflight refuse_if_dirty (untracked whole-seed records) | pre-existing, scope extended by revision-1 |
| 2 | W tracked_files → () makes real require_launch refuse | revision-1 |
| 2 | W real-root tests under real teach_persona._REPO_ROOT / real ledger | revision-1 + pre-existing |
| 2 | W preflight omits both csv paths | revision-1 + pre-existing |
| 2 | W driver review would overwrite 40-REVIEW.md | revision-1 |
| 2 | W this file's D-09/D-10 and D-06/D-15 rows stale | revision-1 omission (fixed by orchestrator) |
| 2 | 4 info (pending tuple, module_sha256 _REPO, unverifiable key_link sources, plan 04 _DEFAULT labels) | 1 revision-1, 3 pre-existing |
| post-approvals check of 8edbee5 | B1 declined-rerun branch unreachable (pending_seeds forced every dropped seed) | approvals revision (8edbee5) + pre-existing pending_seeds shape |
| post-approvals check of 8edbee5 | W2 write-once manifest head rule re-checked against every later launch HEAD | approvals revision (8edbee5) |
| post-approvals check of 8edbee5 | W3 plan 10 hand mv / own commit; record listed dropped attempts of whole seeds only | pre-existing (plan 10) + approvals revision (plan 07) |
| post-approvals check of 8edbee5 | W4 this file lacked R-3 b / record-total rows; W5 drop_attempt only fake-tested | approvals revision omission |
| post-approvals check of 8edbee5 | 3 info (plan 06 task split, plan 02 ERASE-05 citation and D-13 line assertion, manifest sha in build_record) | 2 approvals revision, 1 pre-existing (D-13 line assertion) |
| 40-04 rulings revision (2026-10-06, prereg frozen at 8cf3b32) | plans 05-11 aligned with rulings c, e, f, b, g, WR-01..03, IN-01/02 and `_approved`: D-13 catch in run(), record `d13_reading`, n_seeds/n_pairs, three approvals (plan 10 = first + second checkpoint; plan 11 commits the noise-floor record, then the report), `dialogue_gap(device=record config.device)`, CPU fixtures with config.device cpu, R-3 b leg's D-13 fake | ruling-driven revision |

**Approval:** pending
