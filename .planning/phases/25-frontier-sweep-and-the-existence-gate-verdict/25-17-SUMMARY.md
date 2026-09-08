---
phase: 25
plan: 17
subsystem: sweep-interior
tags: [D-08, D-09, D-10, D-16, D-34, FRONT-01, ADVT-01, interior, completeness, kills, stalls]
requires:
  - results/phase25_extremes_log.json
  - results/phase25_point_*.json (44)
  - data/phase25_heartbeat.jsonl
  - data/phase25_stall.jsonl
  - logs/phase25_sweep.out
provides:
  - results/phase25_interior_log.json
  - scripts/phase25_interior_log.py
  - tests/test_phase25_interior.py
affects: [25-18, 25-19, 25-20]
tech-stack:
  added: []
  patterns:
    - "kills are read from the heartbeat as draw_index resets with a relaunch gap, and paired with the relaunch's REUSING lines — never from memory"
    - "stall records are classified by where their silence window sits against the driver's beats, so a watcher that outlives the driver cannot inflate the run-time count"
decisions:
  - "The interior set is derived from git history (ORDERED_POINT_KEYS() minus the records tracked at 491ba48 = 36) because the sweep began before this plan executed; the log says so."
  - "Both jetsam kills are the SAME attempt under D-10: no reading had landed (each record's single commit postdates its kill), no shape block was on disk, only the training and measure sidecars were reused."
  - "Requirement ticks (FRONT-01, ADVT-01) are left to the phase-close plan, as the ROADMAP's amendment history for ADVT-01 requires; this plan produces the records, 25-18/19 produce the curve and verdict they name."
metrics:
  duration: "36 interior points landed by the driver 2026-09-05 08:48 UTC -> 2026-09-08 05:33 UTC (68.76 h); emitter + log + tests ~2 h"
  completed: 2026-09-08
---

# Phase 25 Plan 17: The 36 Interior Points Summary

All 44 pinned points ran as pinned and each landed in its own single-path commit; the interior 36
took **68.76 h** of the sweep's **81.40 h**, no point was skipped or shortened, and the n=64 leg is
intact. The run was killed twice by macOS memory pressure (`OS_REASON_JETSAM`), both times inside the
first shape of a point, both times resumed as the same attempt after losing at most **10.17 min**.
`results/phase25_interior_log.json` (`efdcbbb`) is derived entirely from the records, git history,
the heartbeat, the stall file and the sweep log by `scripts/phase25_interior_log.py`; nothing in it
was retyped.

## Task 1 — the interior run, as the artifacts show it

The driver ran the 36 points under 25-14's LaunchAgent before this plan executed; Task 1 here is the
log that proves what it did.

**Completeness.** `git ls-files 'results/phase25_point_*.json' | wc -l` = 44. Set equality against
`ORDERED_POINT_KEYS()`, from the log's `completeness.statement`: **`44 == 44, missing [] extra []`**
(the acceptance criterion writes it `missing set() extra set()`; the emitter prints the sorted sets
as lists — same two empty sets). **32 DP + 12 adversarial**, computed as
`len(DP_ARMS) * SWEEP_POINTS` and `len(ADVERSARIAL_ARMS) * len(ADVERSARIAL_RATIO_GRID)`.

**Interior set: 36**, derived as `set(ORDERED_POINT_KEYS()) - {records tracked at 491ba48}`
(the eight extremes were the only records at the commit that closed 25-16). The assertion is made
from git history, not before the run — the log's `interior_set_derivation.asserted_from` says so.
The commit order of all 44 equals `SWEEP_SCHEDULE()` exactly.

**`n64_leg_withdrawn: false`** = `mitigation_budget.N64_LEG_WITHDRAWN`, with `cal03_evidence` from
`results/phase23_cal03_wiring.json`: `epsilon_n8 == epsilon_n64 == 24.38161088311366`, `t_n8 ==
t_n64 == 4`, `verdict: true`.

**Wall-clock against the envelope** (`wall_clock_total`):

| quantity | value | source |
|---|---|---|
| 44 points, first beat → last record commit | **81.40 h** (2026-09-04T20:10:06Z → 2026-09-08T05:33:53Z) | heartbeat first beat; `git log --format=%cI` on `8834c4d` |
| sum of the 44 records' own timing fields | 81.00 h | `training.seconds + measure_seconds + scoring_seconds + Σ shape minutes` |
| 36 interior, last extreme commit → last commit | **68.76 h** | `6b496fc` → `8834c4d` |
| sum of the 36 interior records' timing fields | 68.46 h | same fields |
| envelope | ~107 h measured / 150 h ceiling (25-CONTEXT); the plan's ~101 h | `results/phase25_adversarial_throughput.json::schedule.context_envelope` |
| per point, interior | min 0.923 h (`adv_n8_ratio0p250000`), max 2.481 h (`dp_n8_sigma2p000000`), mean 1.902 h | record fields |
| Phase 23 floor / ceiling per point at K=16 | 1.9979696709667354 h / 3.1471532286150796 h | `results/phase23_cost.json::sizing["16"]` |

The run came in **under the measured envelope by ~26 h** and under the ceiling by ~69 h.

**The stop-termination regime never became ceiling-like.** Zero points exceed the floor/ceiling
midpoint (2.573 h); every DP point sits between 2.04 h and 2.48 h, i.e. at or just above the floor,
and the adversarial points run at 0.92–1.12 h because their adapters draw at 200–330 draws/min. What
does move with σ is `stop_terminated_n` (draws that hit the stop token before the token budget), read
per shape from `shape_timing`: at n=8 it falls from **12979/13824** at σ=0 to **11427/13824** at
σ=80, monotonically from σ=0.5 (12480) onward; at n=64 from **12696/13824** to **11494/13824**. The
adversarial arm stop-terminates 13824/13824 at `adv_n8` ratio 0.25 and 0.5, down to 13708/13824 at
`adv_n64` ratio 1.5. So the ceiling mechanism (a noised adapter that stops emitting EOS) is visible
as a ~12 % rise in budget-exhausted draws across the ladder, not as a wall-clock crossing — the
per-draw cost of the ~2,400 extra full-budget draws at σ=80 is absorbed inside the floor bracket.

**Launches: 6** (`[phase25_launch] pid=` banners 16902, 32536, 69063, 72283, 14897, 88867; launchd
`runs = 6`, `last exit code = 0`) = 1 kickstart + 3 relaunches after one-stage halts + 2 relaunches
after kills. The three halts precede the interior run and are listed from `git log` by subject:
`efb8062` (score-stage halt on the first point), `c78f9ac` (extra-key collision at the fourth
point's record stage), `79ff45a` (the ONE ATTEMPT refusal killed the relaunch on an already-landed
point). They are 25-15/25-16's, not kills, and are distinguished as such in the log.

**Kills and resumes: 2**, both found in the heartbeat as a `draw_index` reset inside one (point,
shape) followed by a gap longer than two 60 s cadences, both `OS_REASON_JETSAM` (no traceback in
`logs/phase25_sweep.err`):

| | kill 1 | kill 2 |
|---|---|---|
| point | `dp_n64_sigma0p500000` (22nd of 44) | `adv_n8_ratio1p000000` (38th of 44) |
| last heartbeat | `2026-09-06T14:42:36Z` stage draw, A1-mild, draw_index 66 | `2026-09-07T23:07:19Z` stage draw, A1-mild, draw_index 41 |
| shape started | 14:35:36Z → **7.00 min** into A1-mild | 23:04:19Z → **3.00 min** into A1-mild |
| first beat after relaunch | 14:45:46Z, A1-mild draw_index 7 (gap 3.17 min) | 23:10:04Z, A1-mild draw_index 13 (gap 2.75 min) |
| resumed by | launch 5, pid 14897 | launch 6, pid 88867 |
| sidecars reused (log) | `REUSING trained adapter` + `REUSING measurements` | same |
| shapes complete on disk | **none** (no `REUSING N recorded prompt(s)` line) | none |
| shapes redrawn | A1-mild, A1-aggressive, A2, A3 | all four |
| record committed | `e5f71dc` 2026-09-06T16:28:06Z | `08680f8` 2026-09-08T00:09:20Z |
| reading landed at kill time | **False → same attempt (D-10)** | **False → same attempt** |
| wall-clock lost | **10.17 min** | 5.75 min |

The **largest single loss is 10.17 min**, against the 22.97 min the interrupted A1-mild shape took
when redrawn — D-09's "at most one shape" held with room. Two further `draw_index` resets
(`dp_n8_sigma1p500000` and `dp_n64_sigma8p000000`, A2 prompt 215 → next shape's prompt 9, 60 s
apart) are shape boundaries where the beat's `shape` field lags `draw_index` by one tick; the log
lists them under `heartbeat_resets_that_are_not_kills` rather than dropping them.

**Stall records: 8 at emission, all `action_taken: "none"`** — not the 2 the orchestrator counted,
and the difference is itself a finding. Classified by silence window:

- **1 before the driver's first beat** — detected `2026-09-04T20:09:54Z`, 12 s before the first
  train beat; the 4545 min of silence it measured is the gap since the 09-01 rehearsal.
- **1 during the sweep** — detected `2026-09-05T03:03:01Z`; last beat `adv_n8_ratio0p000000` A3
  draw_index 209 at 02:57:13Z; silence 5.81 min; next beat `dp_n64_sigma80p000000` train at
  03:03:15Z. The commits inside that window are exactly the halt sequence: `c78f9ac` (02:58:26Z),
  `79ff45a` (03:02:11Z), `a664f03` (03:02:15Z, the point's record). A real diagnosis of a real
  halt, and the watcher did nothing — D-16 as designed.
- **6 after the driver's last beat** (05:33:38Z), from 05:39:04Z, one per minute: the StartInterval
  watcher (`runs = 9283`, 60 s interval) outlived the driver and is still appending to the
  gitignored file. Not acted on here; `deferred-items.md` D-25-17-WATCHER hands it to 25-20's
  revert step.

`data/phase25_stall.pre-launch-2026-09-04.jsonl` is the rotated pre-launch file and is excluded.

**Every point-record commit names exactly one path**: asserted for all 44 by the emitter (`git
show --name-only`) and again by the tests; all 44 are titled `feat(25-10): record sweep point <key>`.

## Task 2 — `tests/test_phase25_interior.py`

**`538 passed in 1.92s`, 0 skipped** (`-v` last line: `538 passed in 1.92s`). Selections:
`-k "matches_the_pinned_mechanism"` → **220 passed, 318 deselected** (44 × 5);
`-k "exactly_one_commit or exactly_one_path"` → **88 passed, 450 deselected**. Runtime **1.92 s**
against the 60 s budget — the 44 records load once into a module fixture, and the 44 commits come
from one `git log --name-only` walk plus 44 `git show` calls.

The D-34 pin is re-derived per arm exactly as `phase25_points` derives it: DP arms pin the capacity
as the lot, `q = SAMPLING_RATE_Q`, `C = CLIP_NORM` (`CONTROL_CLIP_NORM` at σ=0); the adversarial arm
has `q` and `clip_norm` None and its lot is `batch_size × max(1, grad_accum_steps)` of the
TrainConfig the record carries (8 at both capacities). The first draft pinned `[capacity]` for the
adversarial arm and went RED on `adv_n8_ratio0p000000 q`, which is how the arm's real pin was read
from the driver rather than assumed (deferred-items D-25-17-ADV-PIN records that two of the five
fields are self-referential on that arm).

Rates: every key containing `rate` sits beside its counts (`numerator`/`denominator`, `k`/`n_draws`
or `n_draws`/`minutes`) on all 44; 416 gated rows and the held-out A2 on every record.

## The two suite runs

- **During the sweep** (from 25-15-SUMMARY, the only run possible while the device was saturated):
  `PERSONACORE_SWEEP_ACTIVE=1 .venv/bin/python -m pytest tests/ --ignore=tests/test_phase25_venue.py -q`
  → **`2004 passed, 36 skipped, 83 warnings in 290.15s (0:04:50)`**, matching 25-06's literal
  `SWEEP_ACTIVE_EXPECTED_SKIPS = 36`. It cannot be re-run now: the sweep is over and the flag would
  skip legs that are free.
- **After the sweep** (`.venv/bin/python -m pytest tests/ -q`, device free, flag unset):
  **`2659 passed, 1 skipped, 83 warnings in 1283.08s (0:21:23)`**, exit 0 — the 1 skip is the
  baseline's; 0 failed. It ran 21 min, not the estimated 5–10, because the venue file's flag-unset
  test spawns a full child suite and the 42 MPS legs now run instead of skipping.

## Deviations from Plan

**1. [Rule 3 — the GPU work preceded the plan]** The 36 points were run by the driver under the
LaunchAgent between 25-16's close and this plan's start; Task 1 became the emitter + log. The
interior-set assertion is therefore made from git history, and the log says so.

**2. Stall count 8, not 2.** The orchestrator's count was true for the sweep proper; the watcher kept
firing after the driver exited. The emitter classifies rather than assumes, so the run-time count
(**1**) is stable. Logged to deferred-items for 25-20.

**3. The adversarial pin.** See Task 2; the test mirrors the driver, and the self-referential lot
fields on that arm are recorded as an observation, not changed.

**4. Requirement ticks deferred.** FRONT-01 and ADVT-01 are in this plan's frontmatter, but the
ROADMAP records two hand-reverts of a handler ticking ADVT-01 early; the ticks belong to the plan
that publishes the curve. Not marked here.

No auth gates. No package installs. The five frozen modules and `pyproject.toml`: byte-unchanged
(`git diff --exit-code` exits 0). `make lint`: `All checks passed!`, 269 files already formatted.

## Verification

- Task 1's automated verify: prints `44 36` (set equality, 36 interior).
- `n64_leg_withdrawn is N64_LEG_WITHDRAWN is False` → exits 0, prints the CAL-03 block.
- `kills_and_resumes`: 2 entries, each with `reading_landed`, `shapes_complete_on_disk`, `last_heartbeat`.
- `stall_records`: 8, all `action_taken == "none"`.
- `composed_steps == 200` on all 44. D-39 from the data on the 12 adversarial records: the plan's command names
  `refusal.per_family[*].k/n` and `total.k/n` (plan-time fixture names); the committed schema is
  `refusal.by_family[*].refusal_k/refusal_n` and `total.refusal_k/refusal_n`. The same check against the real
  names prints `12 adversarial records: integer refusal_k/refusal_n per family over all 4 families, non-zero
  denominators, totals re-derive` (e.g. `adv_n8_ratio1p000000`: A2 9/3456, total 8828/13824).
- `tests/test_phase25_interior.py -v`: **538 passed, 0 skipped, 1.92 s**.
- After-sweep full suite: `2659 passed, 1 skipped, 83 warnings in 1283.08s (0:21:23)`, exit 0.

## Commits

`efdcbbb` emitter + log · `87194fd` tests · the 36 driver commits `f5e0479` … `8834c4d` (positions 9–44 of `execution_order`).

## Self-Check: PASSED

- `results/phase25_interior_log.json`, `scripts/phase25_interior_log.py`, `tests/test_phase25_interior.py`: FOUND
- commits `efdcbbb`, `87194fd`: FOUND in `git log`
