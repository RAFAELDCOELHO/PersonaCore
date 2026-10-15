---
phase: 42-dp-sgd-recipe-search-at-large
plan: 08
subsystem: e3-stage1
tags: [phase42, e3, mps, stage-1, d-07, d-18, d-19, d-22, recipe-01, recipe-03]
requires: [42-07]
provides:
  - "results/phase42_control_lr3e-04_t800.json, results/phase42_control_lr1e-03_t200.json, results/phase42_control_lr1e-03_t800.json (UNTRACKED, for plan 09)"
  - "ledger/v6_mps_ledger.jsonl: one start / end per control unit (UNCOMMITTED, for plan 09)"
  - "the e3_recall_threshold fill these records give: four learnable recipes, none REFUSED"
affects: [42-09, 42-10]
tech-stack:
  added: []
  patterns: ["PID waiter on the ppid-1 driver; two exit checks before bootout"]
key-files:
  created: []
  modified: []
decisions:
  - "Rafael approved the stage-1 launch (his reply in the session on 2026-10-15; Claude did not write it anywhere)"
  - "Nothing committed except this SUMMARY; the records and the ledger lines wait for Rafael's approved in plan 09"
requirements-completed: []
metrics:
  duration: "1h37 on MPS (kickstart 2026-10-15T14:02:16Z, driver exit by 15:39:42Z)"
  completed: 2026-10-15
---

# Phase 42 Plan 08: E3 stage 1 on MPS (the three new sigma = 0 controls) Summary

Stage 1 ran once on MPS at HEAD `f1cb634`, through the LaunchAgent and under the ledger, after Rafael's approved. All three new controls are whole and all three learned, so the threshold fill has no REFUSED recipe. D-18 does not arise. Nothing was committed except this SUMMARY.

Requirements are contributed to, not closed, by this plan; the orchestrator owns traceability.

## Task 1: launch gate (orchestrator, 2026-10-14/15)

- HEAD was `f1cb6345eaf817068f5db87441fbf101ff290e1c`, and `git status --porcelain -- scripts src results tests ledger artifacts` printed 0 lines.
- Suite: `git diff --name-only 28c7fda HEAD` lists only the 42-06 and 42-07 SUMMARYs (`.planning/`), so the run cited is the 42-06 one at `28c7fda`: `4802 passed, 4 skipped, 83 warnings in 4382.36s`, `EXIT=0`.
- Pins: `git log --oneline 203afa3..HEAD -- scripts/teach_persona.py scripts/phase25_points.py scripts/phase35_prereg.py scripts/phase25_condition_c.py scripts/phase14_recall.py src/personacore/` printed nothing.
- Digests: `0ca749f0…5ff5 scripts/phase42_prereg.py` and `0c9be582…7c60 scripts/phase42_recipes.py`. Both equal 42-06 "Frozen digests" and `data/phase42_rehearsal.json` module_sha256.
- Jobs: no PersonaCore LaunchAgent with a PID, and `pgrep -fl "pytest|phase3[0-9]_|phase4[0-9]_"` was empty.
- Collector: `launchctl print system/com.polybot.negrisk-books` printed `Bad request.` (absent), and `pgrep -fl collect_negrisk` was empty.
- Memory:
  - swap total 1024 M, used 227.88 M;
  - system-wide memory free 70%;
  - top RSS: node 1.86 GB, claude 0.69 GB;
  - newest Jetsam report: `Retired/JetsamEvent-2026-10-14-042407.ips` (Oct 14 04:24).
- Ledger report: no open run; E3 spent 0.0 s.
- Record paths: `['results/phase42_control_lr3e-04_t800.json', 'results/phase42_control_lr1e-03_t200.json', 'results/phase42_control_lr1e-03_t800.json']`, equal to files_modified.
- Preflight: `PREFLIGHT OK f1cb6345eaf817068f5db87441fbf101ff290e1c device=mps stage=1 pending=('control_lr3e-04_t800', 'control_lr1e-03_t200', 'control_lr1e-03_t800') spent_E3_h=0.0`
- Notice premises measured from `results/phase36_budget.json`:
  - e3_overhead_high 43.818 s, e3_per_step_high 0.84045 s and e3_score_high 1270.56 s give 0.4118 h at T = 200 and 0.5519 h at T = 800, so 1.5156 h for the three controls;
  - front_hours.E3 is 6.6225;
  - the plist has KeepAlive false and RunAtLoad false, and its ProgramArguments are `caffeinate -dims .venv/bin/python scripts/phase42_recipes.py run`.

## Task 2: Rafael's approval

Rafael's reply, verbatim: "approved — Lançar o estágio 1 da Fase 42: os 3 controles σ = 0 novos em MPS, como descrito no gate (f1cb634, digests 0ca749f0… e 0c9be582…), com o controle v4.0 reaproveitado por SHA-256. Esperar pelo PID do driver, nunca pelo log. Nada é commitado neste plano; os três registros e os limiares voltam para mim no plano 09." The ledger had no v6/42 line before it.

## Task 3: launch, wait, verification from the files

- Re-gate at launch: HEAD `f1cb634`, porcelain 0 and no jobs (`GATE_OK`). The installed plist is `cmp`-identical to `artifacts/`.
- Kickstart at 2026-10-15T14:02:16Z. The driver was PID 74745 with ppid 1, equal to `launchctl print` pid. Its `/usr/bin/caffeinate` child was PID 74758.
- Waiter: `while ps -p 74745 …; do sleep 300; done`, run in the background. It returned at 15:39:42Z with `pgrep -f 'phase42_recipes[.]py[ ]run'` empty, which is the two exit checks. Bootout followed (`BOOTOUT_OK`).
- Log tail: `RUN DONE whole=['control_lr3e-04_t800', 'control_lr1e-03_t200', 'control_lr1e-03_t800']` and `STAGE 1 DONE: commit the control records, then scripts/phase42_threshold_prereg.py (D-19), before stage 2`.

Ledger lines (v6/42):

| run_id | start (UTC) | end (UTC) | record |
|---|---|---|---|
| v6/42/E3/control_lr3e-04_t800 | 14:02:20.365 | 14:37:33.105 | results/phase42_control_lr3e-04_t800.json |
| v6/42/E3/control_lr1e-03_t200 | 14:37:36.628 | 15:03:24.466 | results/phase42_control_lr1e-03_t200.json |
| v6/42/E3/control_lr1e-03_t800 | 15:03:27.787 | 15:36:44.252 | results/phase42_control_lr1e-03_t800.json |

Ledger report: no open run; E3 spent 5657.042304 s (1.571 h).

The table below is copied from the records. For every record:
- train_config equals `phase42_prereg.expected_train_config(recipe)`, which printed True;
- grad_clip is 1.0;
- record and training clip_bind_count are 0;
- device is `mps` and git_sha_at_launch is `f1cb634`;
- resumed_from_step is 0 and lost_attempts is [].

| unit | lr | warmup | max_steps | composed_steps | taught | held-out | dialogue_gap | retention_ppl | final loss | train s | score s | cond. (c) s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| control_lr3e-04_t800 | 0.0003 | 80 | 800 | 800 | 954/1008 | 386/648 | -0.0074 | 4.0868 | 0.0063 | 829.0 | 1180.0 | 103.2 |
| control_lr1e-03_t200 | 0.001 | 20 | 200 | 200 | 959/1008 | 488/648 | 0.0449 | 3.9938 | 0.0108 | 296.7 | 1149.6 | 101.0 |
| control_lr1e-03_t800 | 0.001 | 80 | 800 | 800 | 983/1008 | 411/648 | -0.0660 | 4.3557 | 0.0029 | 839.4 | 1062.8 | 93.6 |

Threshold fill on these untracked records, from `dict(phase35_prereg.fill('e3_recall_threshold', **phase42_prereg.threshold_fill_inputs()))`:

| recipe key (lr, T, batch, seed) | control | taught threshold | held-out threshold |
|---|---|---|---|
| (0.0003, 200, 8, 1337) | results/phase25_point_dp_n8_sigma0p000000.json (v4.0, reused by SHA-256) | 0.5486111111111112 | 0.3737654320987654 |
| (0.0003, 800, 8, 1337) | results/phase42_control_lr3e-04_t800.json | 0.6625 | 0.4169753086419753 |
| (0.001, 200, 8, 1337) | results/phase42_control_lr1e-03_t200.json | 0.6659722222222222 | 0.5271604938271605 |
| (0.001, 800, 8, 1337) | results/phase42_control_lr1e-03_t800.json | 0.6826388888888888 | 0.4439814814814815 |

No REFUSED recipe, so D-18 does not arise.

`phase42_prereg.exact_disagreements(threshold, (ck, cn), n)` returned `[]` on both legs of all four recipes.

`git status --porcelain` after the run:
- ` M ledger/v6_mps_ledger.jsonl`
- `??` for the three control records
- ` M .claude/scheduled_tasks.lock` (harness, not ours)

## Comparison with the rehearsal (descriptive)

control_lr1e-03_t200 on MPS read 959/1008 and 488/648. On CPU in 42-07 it read 963/1008 and 476/648. Same recipe, different device, so the counts are not bit-identical.

## Deviations

None from the plan. The orchestrator ran Tasks 1-3 itself; no executor was spawned.

## Next

Plan 09: present the three records, the ledger lines and the threshold table to Rafael. On his approved, commit the ledger, each control record, then `scripts/phase42_threshold_prereg.py`.

## Self-Check: PASSED

The values above come from command output in this session: the ledger, the three records, the threshold fill and the exact-disagreement check.
