---
phase: 37-clean-reproduction-of-the-phase-19-verdict
plan: 06
subsystem: reproduction
tags: [R1b, REPRO-03, MPS, one-attempt, LaunchAgent]
requires: [37-05]
provides: [results/phase37_r1b.json (untracked), results/phase37_r1b_arm.json (untracked), ledger start/end lines (uncommitted)]
requirements-completed: []
# REPRO-03 is ticked by the orchestrator at phase close, after 37-07 commits the records on Rafael's approved.
duration: 68.4 min run (4104.43 s ledger) + gates
completed: 2026-10-04
---

# Phase 37 Plan 06: the one R1b attempt — REPLICATED

**The single MPS replica, launched by Rafael under the LaunchAgent after his "approved", re-measured k = 78 with the identical 78-address prefix and reproduced the committed erased arm bit for bit: verdict REPLICATED.**

Executed inline by the orchestrator. Every value below was read from the files after the run.

## Pre-launch gate (Task 1)

- HEAD `7831ea93b7db1c48ebf6629f5f905eba1e0d224b`. `git status --porcelain -- scripts src results tests ledger artifacts` was empty.
- Suite: the 37-05 post-commit run at `fe715c5` (`3928 passed, 4 skipped`, EXIT=0) is cited, not rerun. `git diff --name-only fe715c5 HEAD` listed only 37-05-SUMMARY.md and 37-06-PLAN.md, which the amended rule allows (e634ee2).
- `launchctl list`: no PersonaCore agent had a running PID. Ledger report: no open run, R1b 0.0 s.
- Preflight on the real ledger left the ledger sha256 unchanged:
  `PREFLIGHT OK 7831ea93b7db1c48ebf6629f5f905eba1e0d224b device=mps cost=1.2590560358100467 h cap=1.6622708975519829 h`
- Wiring tests `tests/test_phase37_r1b.py -k "main or emit or plist"`: 11 passed.

## Launch (Task 2)

Rafael wrote "approved" (2026-10-03), copied the plist, then ran `launchctl bootstrap` and `kickstart`. The driver ran as PID 53692. Claude only read the logs, heartbeat and ledger, and ran no pytest, MPS job or commit during the run.

- Ledger start: 2026-10-03T23:16:49.288810Z.
- `SWEEP k=78 run_arm=True` at about 20:22 local. data/phase37_r1b_sweep.json was written before the arm started (WR-02).
- `[phase19_erasure] wrote results/phase37_r1b_arm.json in 62.4 min`, then `R1b REPLICATED results/phase37_r1b.json`.
- Ledger end: 2026-10-04T00:25:13.714763Z, record `results/phase37_r1b.json`. The agent exited with status 0. logs/phase37_r1b.err is empty.

## What the run wrote (Task 3)

**Ledger.** Exactly one start line and one end line for `v6/37/R1b/replica`, and the end names results/phase37_r1b.json. The report shows the run closed with 4104.425953 s (1.140 h, below R1B_COST_HOURS 1.259 h and the cap 1.662 h); its flag "record not yet tracked" clears when 37-07 commits the record. With no open run left, `reconcile` appended nothing (sha256 unchanged).

**Files.**
- results/phase37_r1b.json: sha256 a37c5356ea411325c199050ed416463a514672f3f39a489a4be2f5895297ed6c.
- results/phase37_r1b_arm.json: sha256 f6539c05d5704bb7db0e99673f4a14d5c1ab6c51f27a0d087f070f739c91ecbc. It exists, and decision.run_arm is True.
- data/phase37_r1b_sweep.json: sha256 0cfcd2118b2fa8652c18236a92f387c63d1a9e06560fdb1668a20ea65e7f4207.
- data/phase37_r1b_run.json: sha256 a8b185751e2b320be3a8f0b6a8a9220c15daa54d8473f0daba0ca7db824b8d67.
- `git status --porcelain` lists only ` M ledger/v6_mps_ledger.jsonl`, `?? results/phase37_r1b.json` and `?? results/phase37_r1b_arm.json` (plus the pre-existing `.claude/scheduled_tasks.lock` deletion, not ours).
- `git status --porcelain -- 'results/phase19_*'` is empty. The heartbeat has 69 beats for point v6/37/R1b/replica.

**Provenance.** device mps, torch 2.7.1. git_sha_at_launch = git_sha_at_end = 7831ea9, so head_moved_during_run is False. modules_changed_since_launch is []. started 2026-10-03T23:16:49.289917Z, finished 2026-10-04T00:25:13.546844Z.

**Verdict: REPLICATED.**

| key | replica | committed | abs_diff | tolerance | within |
|---|---|---|---|---|---|
| k | 78 | 78 | 0 | 0 | True |
| target_correct | [0, 27] | [0, 27] | 0 | 0 | True |
| nontargets_beyond_margin | [7, 7] | [7, 7] | 0 | 0 | True |
| destroyed_pct | 77.6370113463966 | 77.6370113463966 | 0.0 | 0.8396203493271365 | True |

**Decision (D-07).** committed_k 78, k 78, k_equal True, set_equal True, positions_moved 0, only_in_committed [], only_in_remeasured [], run_arm True. The arm record's config.ablated_components equals sweep.ordered_prefix.

**Draw identity** (context, criterion False): bit_identical True. differing_completions 0 of 10368, differing_entries 0 of 216.

**Non-target context** (criterion False, noise floor 0.14814814814814814). The 7 slots (birth_year, cat_name, hometown, house_number, person_name, sibling_name, street) have replica_delta equal to committed_delta, with abs_diff 0.0 for every slot (e.g. birth_year 0.37037037037037035, cat_name 0.7407407407407407, hometown 0.7777777777777778).

**The replica's own gate verdict** (replica_verdict): FAILURE, with the same three reasons as Phase 19.
- (a) target upper bound 0.0911 over 27 questions <= calibrated floor 0.0911
- (b) worst non-target degradation 1.000000 > k=2 x 0.148148 = 0.296296
- (c) dialogue PPL 4.8511 vs cap 4.5837; retention PPL 3.670918 vs cap 4.029000

**Sweep.** k 78, stopped, full_ordering 288, wall_clock_min 5.973857219424099.

## Deviations

- Run inline by the orchestrator.
- The LaunchAgent is still loaded (PID "-", last exit 0). Rafael runs `launchctl bootout gui/$(id -u)/com.personacore.phase37.r1b` as the plan's notice says. It cannot start itself (RunAtLoad false, KeepAlive false).
- Nothing was committed in this plan except this SUMMARY. The records and ledger lines go to Rafael in 37-07.
