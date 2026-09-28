---
phase: 32-replay-bearing-frontier-re-run-and-verdict
plan: 06
subsystem: v5.0 replay-bearing sweep on MPS (12 point records) and their read-only verification
tags: [sweep, mps, launchd, prereg-03, afront-01, verification, dry-run-frontier]
requires: ["32-04", "32-05"]
provides:
  - "results/phase32_point_*.json: all 12 point records, each committed alone by the driver, controls first"
  - "A verified dry run of phase32_frontier.build_frontier on the real committed records (no file written): admission MOOT"
affects: [32-07]
tech-stack:
  added: []
  patterns: [unattended launchd sweep, write-once driver-committed records, read-only post-run verification, in-memory consumer dry run before emit]
key-files:
  created:
    - .planning/phases/32-replay-bearing-frontier-re-run-and-verdict/32-RUNBOOK.md
  modified: []
decisions:
  - "Observed n64 outcome: PREREG-03. The advr_n64 control read taught 0/1008, held-out 1/648; control_is_unlearnable is True (F_Y*0 = 0 fails 0 < F_Y*recall), so the 5 n64 non-controls are PREREG-03 refusals, not re-tuned"
  - "The frontier was built only in memory. Writing results/phase32_frontier.json stays with plan 07"
requirements-completed: []
# AFRONT-01 is evidenced here (all 12 points trained or refused unattended on MPS, controls first, inside the budget, each record committed alone). Ticking it is left to the orchestrator / phase close.
metrics:
  duration: sweep 2026-09-27T22:19Z to 2026-09-28T09:25Z (~11.1 h wall); Task 3 ~20 min
  completed: 2026-09-28
  tasks: 3
  files: 1
---

# Phase 32 Plan 06: v5.0 MPS sweep and record verification Summary

All 12 v5.0 point records are committed, each by its own driver commit, controls first. Every trained record says `device: "mps"`. The n8 leg was measured. The n64 control is unlearnable (taught 0/1008), so the n64 leg is refused under PREREG-03. An in-memory frontier build on the real records runs without error and admission reads **MOOT**.

## Tasks

| Task | Name | Commit | Result |
| ---- | ---- | ------ | ------ |
| 1 | Runbook and 11 pre-launch gates | 8f4d34c | 32-RUNBOOK.md, gates green |
| 2 | MPS sweep (human-action) | 12 driver commits, below | Developer reported "sweep complete" |
| 3 | Verify committed point records | read-only, no commit | All checks pass |

### Task 2: the sweep (resolved by the developer)

Record commits, oldest first:
e5ba659 advr_n8_ratio0p000000 (control), d37b1e7 advr_n64_ratio0p000000 (control), 9a8dc34 n8 0.25, 3a53dd6 n8 0.5, 8786699 n8 1.0, 5f56130 n8 1.5, fb0bf65 n8 1.909091, then the PREREG-03 refusals 1600b4b n64 0.25, f37c910 n64 0.5, f075e86 n64 1.0, 49c3294 n64 1.5, e35654c n64 1.909091.

Last heartbeat (data/phase25_heartbeat.jsonl): `{"draw_index": null, "point": "advr_n8_ratio1p909091", "shape": null, "stage": "done", "utc": "2026-09-28T09:25:14.469697+00:00"}`. The log tail shows the n64 PREREG-03 keys "RECORDED already (tracked) — skipping" on the final pass.

## Task 3 verification (all run live, 2026-09-28)

**Tracking and add commits.** All 12 `phase29_prereg.point_record_path(k)` are in `git ls-files results`. Each has exactly 1 add commit (`git log --diff-filter=A`), and `git show --name-only` on it lists only that one path.

**Controls first.** `git merge-base --is-ancestor` of both control add commits (e5ba659, d37b1e7) against all 10 non-control add commits: 0 failures.

**Trained records** (counts are numerator/denominator from `taught_recall` / `heldout_recall`; the gap is `capability.adapter_on - adapter_off`, dialogue ppl; stage times in s):

| key | taught | held-out | replay per_step (len, set, expected) | train / draw / recall / measure / score s | device | gap on-off |
|---|---|---|---|---|---|---|
| advr_n8_ratio0p000000 (control) | 777/1008 | 334/648 | 200, {32}, 32 | 142.2 / 4655.7 / 943.5 / 84.8 / 0.1 | mps | +0.134325 |
| advr_n8_ratio0p250000 | 653/1008 | 240/648 | 200, {32}, 32 | 143.1 / 3774.0 / 966.5 / 85.5 / 0.1 | mps | +0.168827 |
| advr_n8_ratio0p500000 | 440/1008 | 159/648 | 200, {32}, 32 | 145.6 / 3965.6 / 973.3 / 88.3 / 0.1 | mps | +0.155393 |
| advr_n8_ratio1p000000 | 286/1008 | 107/648 | 200, {32}, 32 | 151.0 / 4128.4 / 1008.7 / 85.7 / 0.1 | mps | +0.154949 |
| advr_n8_ratio1p500000 | 223/1008 | 86/648 | 200, {32}, 32 | 145.7 / 4153.9 / 1052.5 / 88.6 / 0.1 | mps | +0.150878 |
| advr_n8_ratio1p909091 | 160/1008 | 77/648 | 200, {32}, 32 | 145.2 / 4148.5 / 1039.6 / 90.8 / 0.1 | mps | +0.151041 |
| advr_n64_ratio0p000000 (control) | 0/1008 | 1/648 | 200, {256}, 256 | 660.2 / 5789.1 / 1144.9 / 101.9 / 0.1 | mps | +0.184152 |

Every trained record has `provenance.stop_line = {seconds: 135989.458, past_line_ruling: None}`.

**32-05 risk (dialogue_gap_band).** The advr_n8 control's gap is adapter_on 4.707673871211244 - adapter_off 4.573349214207799 = **+0.13432465700344487** (> 0), equal to `condition_c.control_gap`. The band does not raise on the real records; the dry run below confirms it.

**PREREG-03 records** (all 5 n64 non-controls): `rule: PREREG-03`, `control_key: advr_n64_ratio0p000000`, `control_recall_counts = {taught: [0, 1008], heldout: [1, 648]}`.

**D-03 clock.** `phase32_points.cumulative_seconds(tracked)` = 39903.49 s = 11.08 h, against stop_line 135989.46 s = 37.77 h. Well inside the budget; no past-line ruling needed.

**Environment.** `grep -c Traceback logs/phase32_sweep.err` gives 0. `git status --porcelain scripts src results` is empty. `launchctl print gui/$(id -u)/com.personacore.phase32.sweep` rc 113, so the agent is booted out.

**Tests on the committed tree.** `.venv/bin/pytest tests/test_phase31_budget.py tests/test_phase29_prereg.py tests/test_phase30_points.py tests/test_phase30_calibration.py tests/test_phase32_points.py tests/test_phase32_frontier.py tests/test_phase32_live.py -q -p no:cacheprovider`: **234 passed in 142.08 s**. On their tracked branch, `test_ancestry_budget_precedes_every_sweep_point` and `test_ancestry_probes_precede_the_budget` pass (2 passed). The D-19 tripwire `test_the_phase30_points_pin_continuation_is_a_tripwire` passes (1 passed). The automated verify (missing = []) passes.

### Dry-run frontier (in memory, nothing written)

I called `phase32_frontier.build_frontier(records, v4_frontier, v4_sha256)` on the 12 committed records and the committed v4.0 frontier, the same inputs `emit` uses, but skipped emit. It raised nothing. Afterwards `results/phase32_frontier.json` does not exist and the tree is clean.

- Point verdicts: the 6 n8 points are INCONCLUSIVE (each fails (a): the extraction upper bounds are 0.7741 / 0.6420 / 0.5545 / 0.4293 / 0.3584 / 0.3213, all above X = 0.0065). The 6 n64 points are REFUSED.
- control_readings: advr_n8 has unlearnable False; advr_n64 has unlearnable True.
- leg_refusals: advr_n64 is refused because the recall floors came out Y_taught = 0.0 and Y_heldout = 0.00108, which are not in (0, 1].
- by_leg: n8 is v5 measured / v4 evaluated, with k5 = 0 and k6 = 1 (v4: 0 of 6). n64 is v5 refused_prereg03 / v4 not_evaluated.
- Statement: "At advr_n8, with replay, (c) passes at 0 of 5 non-control ratios, and at 1 of 6 counting the ratio-0 control, whose dialogue half passes by self-reference (the control_gap is its own gap); in v4.0, without replay, (c) passed at 0 of 6 at adv_n8. At advr_n64, the v5.0 leg is REFUSED under PREREG-03: its own control read taught 0/1008 and held-out 1/648, which puts the recall floors outside (0,1], and it was not re-tuned, so (c) with replay was not evaluated; in v4.0, (c) was measured but not evaluated at any of 6 ratios at adv_n64: the route refused on the control's recall floors (taught 1/1008, held-out 0/648)."
- `admission()`: **MOOT**. The reasons are "0 of 12 points PASS; tallies {PASS 0, FAIL 0, INCONCLUSIVE 6, REFUSED 6}" and "advr_n64 fully REFUSED ...; MOOT does not extend to that capacity". admitted_point_keys is [].

### Developer's figures against the records

Every developer-reported figure matches the records: n64 control 0/1008, 1/648, gap +0.184; n8 control 777/1008, 334/648, gap +0.134; n64 replay 256 windows x 200 steps; refusal via `control_is_unlearnable` (phase29_prereg.py:188-198, since taught 0 makes F_Y*recall = 0). There are no discrepancies.

## Deviations from Plan

None. One harness correction during Task 3: the plan writes `phase32_points.cumulative_seconds` as if it takes no arguments, but it takes `tracked` (the `git ls-files results` list). I called it with that list.

## Self-Check: PASSED

- 32-RUNBOOK.md present; 8f4d34c and all 12 record commits are present in `git log`.
