---
phase: 25
plan: 14
subsystem: sweep-venue
tags: [D-12, D-13, D-15, D-16, D-43, D-50, launch, resolver, launchd, caffeinate]
requires:
  - artifacts/com.personacore.phase25.sweep.plist
  - artifacts/com.personacore.phase25.watch.plist
  - scripts/phase25_venue.py
  - scripts/phase25_run.py
  - scripts/phase25_record.py
  - results/phase25_n64_matched_floor.json
provides:
  - scripts/phase25_points.py
  - scripts/phase25_n64_floor.py
  - artifacts/com.personacore.phase25.n64floor.plist
  - results/phase25_n64_matched_floor.json
  - results/phase25_operational_note.md
  - tests/test_phase25_points.py
affects:
  - scripts/phase25_run.py
  - scripts/phase25_record.py
  - scripts/phase25_gate05.py
  - scripts/phase25_venue.py
  - tests/test_phase25_launch.py
  - tests/test_phase23_resume.py
tech-stack:
  added: []
  patterns:
    - "read main() -> run() end to end before a multi-day launch; --dry-run-only test batteries hide an unwired live path"
    - "per-stage atomic sidecars under data/ keyed by the adapter's sha256, so a kill costs one stage"
    - "the executed order lives in code as a proved permutation of the pinned set, never in the plist"
    - "a detached (fork+setsid) read-back for machine-state checks the console itself pollutes"
key-files:
  created:
    - scripts/phase25_points.py
    - scripts/phase25_n64_floor.py
    - artifacts/com.personacore.phase25.n64floor.plist
    - results/phase25_n64_matched_floor.json
    - tests/test_phase25_points.py
  modified:
    - scripts/phase25_run.py
    - scripts/phase25_record.py
    - scripts/phase25_gate05.py
    - scripts/phase25_venue.py
    - results/phase25_operational_note.md
    - tests/test_phase25_launch.py
    - tests/test_phase23_resume.py
    - .planning/STATE.md
decisions:
  - "The sweep prefix is phase25_<axis><value> (the key minus its arm): arm_outputs scopes csv/checkpoint/adapter as {prefix}_{arm}, so 44 distinct adapters, and the control keeps arm identity dp_n8/dp_n64 separated by prefix only (D-06)."
  - "The adversarial arm's live mechanism carries q: null and clip_norm: null on BOTH sides of D-34's pin — no DPSGD is constructed; the lot is the TrainConfig the run built (batch_size x grad_accum) and composed_steps is read off its final checkpoint."
  - "D-50's seed_spread comes from D-03's five n=64 seam-off adapters (retention perplexity per seed, pairwise |diff|) because the sweep is single-seed per point; the floor leg therefore runs BEFORE the first point and its record is committed first."
  - "control_gap (D-47) is the point's own reading at a control and the TRACKED control record's reading everywhere else — read through git ls-files, never the working tree."
  - "GATE-05's reported tier at n=64 records the 56 filler facts as unmeasurable with the reason: the frozen reference_set_for refuses non-core slots, so D-46's 'one extra forward pass' premise was false. Nothing in a verdict changes."
  - "The training-stage resume counts composed_steps as resumed_from_step + live-composed steps and discloses resumed_from_step; a resumed run is the same attempt (D-10)."
  - "The point's run.csv is moved under data/phase25_runs/<key>/ so §O1's single-path commit is the only write results/ sees and 25-19's dirty-tree refusal is not tripped by 44 logs."
metrics:
  duration: "~5h 40m wall (D-03 leg 3h 20m GPU; suite 8 + 12 min; first point live at 20:09 UTC)"
  completed: 2026-09-04
---

# Phase 25 Plan 14: The Launch Checkpoint Summary

The machine was put into the state a 4.5–6.3-day unattended run needs, the sweep agent was
kickstarted at **2026-09-04 20:09:06 UTC**, and its first point — the `dp_n8` control — trained,
reproduced Phase 23's **790/1008 exactly**, cleared condition (c) and GATE-05, and entered its draw
leg under the LaunchAgent. Before any of that could happen, reading the driver end to end found
that its live path had **never been wired**, and five more latent defects behind it. All six were
fixed and committed before the first GPU second.

## What the checkpoint found before spending anything

| # | Defect | Where | Fix |
|---|---|---|---|
| 1 | `run_point` dereferenced `record_fields["training"|"drawing"|"values"|"record"]` that `main()` never passed — every non-dry-run point would have raised `KeyError`. All 23 driver tests take `--dry-run`. | `scripts/phase25_run.py` | `scripts/phase25_points.py`: the per-point resolver (torch-free plan for all 44 keys; training stage with the DP seam captured as `phase23_run.captured_dp_seam` does; measurement stage; record kwargs), per-stage sidecars under `data/` |
| 2 | No producer for the control's `taught_recall` / `reproduction_gate` (25-15 verifies them) or for D-50's `seed_spread` | — | `measure_stage` scores recall on the controls and calls `prove_reproduction`; `scripts/phase25_n64_floor.py` produces the spread |
| 3 | `measure_gate05` at n=64 would refuse: the frozen `reference_set_for` accepts core slots only, and the 56 filler facts share 8 slots | `scripts/phase25_gate05.py` | omission entries with `FILLER_EXPOSURE_OMITTED`; `taught_mapping` keys filler facts by id |
| 4 | `parse_point_key("adv_n8_ratio1p909091")` returns `1.909091`; the grid holds `1.9090909090909092` | `scripts/phase25_record.py` | `exact_axis_value` resolves the ladder/grid literal from the key |
| 5 | The plist deliberately spells no point list, so D-15's order (extremes first, interleaved) had no home; `main()` defaulted to the leg-by-leg pinned order | `scripts/phase25_run.py` | `phase25_record.SWEEP_SCHEDULE()`, a proved permutation of the pinned 44 |
| 6 | `launch_identity` read the wrapper off the banner's `ppid` (launchd) and hard-coded `wrapper_is_the_parent: True`. Measured: `caffeinate -dims` forks, the PARENT execs the utility and the CHILD holds the assertions | `scripts/phase25_venue.py` | `read_process_parents`; the wrapper found by `ppid == driver.pid`; a driver with no caffeinate child refused as UNWRAPPED; superseded text left standing |

Commits: `c3c7709` (1–5, 13 tests), `8e9766e` (6, the D-03 plist), `b8d31b7` (the two full-suite
reds those introduced: a bare `epsilon` in a message; the `train_arm(` register).

## Task 2 — the machine state, measured

- **pmset:** found at `sleep 0 / disksleep 0 / powernap 0` (the operator applied it between the
  09-01 before-state and this checkpoint); note §1. The revert to `1 / 10 / 1` is plan 25-20's.
- **Strays:** `com.personacore.caffeinate` (17 days) and the `-is -w 7584` watcher are gone. The
  only `caffeinate` present is this Claude session's own `-i -t 300` (ppid = `claude`), which
  `prove_only_our_caffeinate` correctly refuses from the console and which a detached read-back
  (fork + setsid, +420 s) does not see: **the sweep's wrapper is the only caffeinate**; note §2, §12.4.
- **Launch identity:** driver 16902 (ppid 1, leads its group), wrapper 16904 (ppid 16902) holding
  `-d -i -m -s` on behalf of 16902; every boolean true; note §4.
- **KeepAlive as loaded:** the key is absent from `launchctl print` (the loaded form of `false`).
- **Heartbeat:** every 60 s from 20:10:06 UTC, all five fields, stage `train → measure → draw`.
- **Stall watcher:** 4,469 pre-launch records rotated to `data/phase25_stall.pre-launch-2026-09-04.jsonl`;
  one record in the fresh file (the pre-kickstart silence), `action_taken: "none"`.
- **Session boundary:** measured 09-01 (§6) — a logout kills the agent; the commitment stands.

## 25-15 Task 2, run early — D-03's n=64 floor (and D-50's input)

`results/phase25_n64_matched_floor.json` (`f019c9a`, one path): seam-off comparator on the
`dp_n64` control's own bins at seeds 1337/2024/1338/2025/1339 — taught recall **87, 67, 67, 89,
98 of 1008**; floor **0.030753968253968256** by the called `phase23_prereg.noise_floor` (n=8
reference `0.0267857142857143` beside it); retention perplexity per seed
3.9478/3.9126/3.9435/3.8863/3.9101, pairwise spread max **0.061495** = D-50's `seed_spread`.
**3.33 h against D-03's 3.3 h.** This is the repository's first n=64 recall reading: 64 facts in
200 steps dilute each fact eight-fold against n=8's 790/1008.

## The first point, live

```
[phase25_points] dp_n8_sigma0p000000: trained in 217.9s (resumed_from_step 0), clip_bind_count=0, mechanism matches the pin
[phase25_points] dp_n8_sigma0p000000: taught recall 790/1008 in 914.5s — REPRODUCTION GATE PASSED
[phase25_points] dp_n8_sigma0p000000: condition (c) + GATE-05 measured in 87.5s (dialogue 4.7084/4.5733, retention 3.7832, zero_extraction_has_nll=True)
```

D-01 (a) checked before scoring; D-07 satisfied under hard `==`; the adapter-OFF dialogue reading
is Phase 19's `4.573349214207799`. The draw leg was running (A1-mild, question 10) when this
summary was written; the first `DONE` line closes R1 and the point's commit closes R6.

## Deviations from Plan

- **Scope:** Task 2's steps (a)–(k) were performed across 09-01 (rows 5, 6 — the previous session)
  and 09-04 (rows 1, 2, 4). Six code fixes outside `files_modified` were necessary to make the
  launch possible at all; each is a documented deviation, with the measurement that forced it in
  the module docstring.
- **25-15 Task 2 ran before 25-14 finished**, because D-50's `seed_spread` had no other source and
  every point record needs it.
- **The full suite ran in two chunks** (`--ignore=tests/test_phase25_venue.py`, then that file
  alone): the harness killed two whole-suite runs at ~93% for memory — the venue file re-runs the
  suite in a subprocess while the desktop held ~52 GB of compressed pages. 2014 passed / 1 skipped
  / 2 failed (both fixed in `b8d31b7`, re-run green on the clean tree), then 16 passed.
- **D-07's halt message is written to `data/phase25_<key>_halt.json`, not into a point record:**
  committing a failed control's record would spend the attempt D-10 reserves for the fixed re-run.
- **`records_per_lot`/`composed_lot_sizes` for adversarial arms** are the TrainConfig's window
  count per step (8), not the capacity: those arms are not fact-aligned.

## Verification

- `tests/test_phase25_launch.py`: **56 passed** (flag set) after the note update; `tests/test_phase25_points.py`: 13 passed.
- Full suite, flag unset, chunked: **2014 passed, 1 skipped, 2 failed → fixed → 7 passed on re-run; venue chunk 16 passed.**
- `git ls-files 'results/phase25_point_*.json' | wc -l` = **0** at kickstart (no point had run).
- `make lint` clean on every touched file (ruff format + check).
- `git diff --exit-code -- scripts/mitigation_budget.py scripts/mitigation_gate.py scripts/mitigation_accountant.py scripts/mitigation_unit.py scripts/phase18_extraction.py pyproject.toml` — untouched.

## Commits

`c3c7709` resolver + schedule + gate05 + floor leg + tests · `8e9766e` launch_identity + D-03 plist ·
`6bf6d83` note rows 1/2/4 · `1c0064b` STATE · `f019c9a` n=64 floor record · `b8d31b7` two suite reds ·
`f2fcfa2` note §12.

## Notes for Later Waves

- 25-15 Task 1's verify reads `per_question['core_held_out']` as 416 rows: `score_point` now returns
  per-QUESTION rows (question_id, family, tier, fact_id, slot, seed_index, successes, draws,
  answered) with the per-fact rollup under `extra["per_fact"]`.
- 25-16's `interleave_order` is `SWEEP_SCHEDULE()[2:8]`; record timestamps come from the point records.
- 25-17 must read stall records from `data/phase25_stall.jsonl` only (the pre-launch file is history).
- 25-18's verdict consumes `condition_c.*`, `per_question`, and the control's `taught_recall`; the
  adversarial records carry `mechanism_note`, `axis_terminus`, `multiplicity_at_upper_extreme`.
- Peer sessions must not `git checkout` in this tree during the run.
