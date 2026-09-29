# Phase 32 Sweep Runbook (32-06)

The v5.0 sweep trains and scores the 12 `advr` points on MPS under the LaunchAgent
`com.personacore.phase32.sweep`. The order is `phase30_points.SWEEP_SCHEDULE()`: the n8 control,
the n64 control, the 5 n8 non-controls, then the 5 n64 non-controls. Each record is written once
and committed alone by the driver, as `feat(32): record sweep point <key>` or
`feat(32): record PREREG-03 refused point <key>`.

The developer launches and boots out the agent (D-05, Phase 31 D-12). Claude never runs
`launchctl bootstrap`, `kickstart` or `bootout`, and never starts the driver.

All paths below come from `artifacts/com.personacore.phase32.sweep.plist` and
`scripts/phase32_points.py`. They were read from the code on 2026-09-27, not from the plan's spelling.

## Expected duration

- Budget estimate (`results/phase31_budget.json`): 82,724.75 s (22.98 h) if both legs are
  learnable, and 45,610 s (12.67 h) if the n64 control is unlearnable.
- Stop line: `stop_line.seconds` = 135,989.458 s (37.77 h), read with
  `phase32_points.stop_line_seconds`. The clock is `phase32_points.cumulative_seconds`: the sum of
  `stages.*.seconds` over the committed trained records. PREREG-03 records count 0 s.

## Pre-launch gates (measured 2026-09-27, HEAD 94a791c on main)

| # | Gate | Command | Result |
|---|------|---------|--------|
| 1 | Clean tree | `git status --porcelain scripts src results tests artifacts` | empty. The only dirt anywhere is the pre-existing ` D .claude/scheduled_tasks.lock`, which is not from this plan |
| 2 | Branch | `git rev-parse --abbrev-ref HEAD` | `main` (94a791c) |
| 3 | Full suite | `.venv/bin/pytest -q -p no:cacheprovider` | EXIT=0: 3218 passed, 4 skipped, 0 failed in 2116.70 s (35:16), run at 3eb3375. `git diff --stat 3eb3375 HEAD` touches only `.planning/ROADMAP.md` and `.planning/STATE.md` (2 files, +2/-2), so that run still covers the committed code. It was cited rather than re-run |
| 4 | Targeted | `.venv/bin/pytest tests/test_phase32_live.py tests/test_phase32_points.py tests/test_phase32_frontier.py -q -p no:cacheprovider` | 85 passed in 86.21 s |
| 5 | No leaks | `find data checkpoints results logs \( -name '*phase32*' -o -name 'phase25_advr_*' \) -print` | empty |
| 6 | MPS | `.venv/bin/python -c "import torch; print(torch.backends.mps.is_available())"` | `True` (torch 2.7.1) |
| 7 | Disk | `phase25_run.disk_precheck()` | `disk ok` (457 GiB free) |
| 8 | Plist | `plistlib.load(...)` | Label `com.personacore.phase32.sweep`. The argv is fixed as `/usr/bin/caffeinate -dims .../.venv/bin/python .../scripts/phase32_points.py run --heartbeat .../data/phase25_heartbeat.jsonl`, with no `--past-stop-line` |
| 9 | No stale agent | `launchctl print gui/$(id -u)/com.personacore.phase32.sweep` | exit 113 (not loaded) |
| 10 | D-19 order | `.venv/bin/pytest tests/test_phase30_calibration.py::test_the_phase30_points_pin_continuation_is_a_tripwire -q -p no:cacheprovider` | 1 passed. The newest commit touching `scripts/phase30_points.py` is f3785da (32-01), and it is registered |
| 11 | Stop line and clock | `p.stop_line_seconds(t), p.cumulative_seconds(t)` | `135989.45825294734 0.0` (37.77 h, clock == 0) |

`git ls-files 'results/phase32_*'` prints nothing before launch.

## Launch (developer only)

Run these from `/Users/juliorcoelho/PersonaCore`:

```bash
cp artifacts/com.personacore.phase32.sweep.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.personacore.phase32.sweep.plist
launchctl kickstart gui/$(id -u)/com.personacore.phase32.sweep
```

`RunAtLoad` and `KeepAlive` are both false, so `bootstrap` starts nothing and `kickstart` starts the
run. After the driver exits:

```bash
launchctl bootout gui/$(id -u)/com.personacore.phase32.sweep
```

Within about 2 minutes you should see a heartbeat line with `"point": "advr_n8_ratio0p000000"`
and `"stage": "train"`. `logs/phase32_sweep.out` should start with the `phase25_venue` launch
banner, and `logs/phase32_sweep.err` should have no `Traceback`.

## Watch

```bash
tail -f data/phase25_heartbeat.jsonl logs/phase32_sweep.out
git log --oneline -- 'results/phase32_point_*'
```

- The heartbeat file is SHARED with earlier phases. Before launch its last line is
  `{"point": "probe31", "stage": "done", ...}` from Phase 31. A "done" line counts only if its
  `point` is an `advr_*` key. Plan 06 Task 2's automated check (`tail -1 | grep done|stop_line`)
  already passes on that stale line, so read the `point` field.
- Beats arrive every `phase25_watch.HEARTBEAT_SECONDS` = 60 s. More than
  `STALL_THRESHOLD_MINUTES` = 5 min of silence is a stall. The watcher, which only records and
  never acts, is:
  `.venv/bin/python scripts/phase25_watch.py --heartbeat data/phase25_heartbeat.jsonl --stall-record <path>`.
- Stages per point are `train`, `measure`, `draw`, `score`, `record`, `commit`, `done`. The
  `stop_line` stage is written only at the line, and its `shape` is
  `cumulative_seconds=<s>`.
- If the n64 control is unlearnable, its 5 PREREG-03 commits do NOT follow the n64 control commit.
  They land together after all 5 n8 non-controls have trained, roughly 10 h later. That is
  expected.

### Which process is the sweep's

Under launchd the driver (`python scripts/phase32_points.py run`) is the PARENT, and
`caffeinate -dims` is its CHILD, holding the assertions. Find it by `ppid == driver pid`:

```bash
DRIVER=$(pgrep -f 'scripts/phase32_points.py run'); ps -o pid,ppid,command -p "$DRIVER"; pgrep -P "$DRIVER" -l
pmset -g assertions | grep caffeinate
```

The Claude harness spawns its own `caffeinate -i -t 300`. That process is not the sweep's.

## Rules during the sweep

- **No pytest during the sweep.** It contends for MPS and skews the timed stages. If a run is
  unavoidable, prefix it with `PERSONACORE_SWEEP_ACTIVE=1` so the MPS legs skip loudly.
- **Never commit anything under `scripts/` or `src/` while it runs (WR-02, D-08).** The next record
  write re-runs `refuse_if_dirty` over `scripts src results` and `prove_pinned_unchanged` over
  `PINNED_MODULES`. A dirty tree, or a pinned module changed between a session's commit and HEAD,
  makes the write refuse, and the point's work is lost. Every code change lands before launch or
  after the sweep.
  - **Dated correction, 2026-09-28 (Phase 32 security gate, T-32-25 / review CR-01, WR-01):** the
    sentence above overstates D-08. `prove_pinned_unchanged` compares the session shas and the
    training sha with HEAD. It does not compare the load-time `INSTRUMENT_GIT_SHA` (the commit the
    running process imported its code from), and it does not see stage modules outside
    `PINNED_MODULES`. A commit that lands *between* points therefore passes D-08 while old code
    runs. The procedural ban in this bullet (no `scripts/` or `src/` commits during the run) is the
    actual control, not D-08. It held for the committed sweep (32-SECURITY.md AR-32-03).
- Do not delete or edit anything under `data/` or `results/`, and do not change the branch. The
  driver commits only on `main` (D-11).

## Stop line (D-03, D-04, D-06)

If the last heartbeat is `"stage": "stop_line"`, the driver has already exited **0**. It printed
`STOP LINE: cumulative <s> s >= <line> s before <key>`, and the unrun keys stay absent. Nothing is
marked REFUSED. **Do nothing without a ruling.** Boot the agent out and report the heartbeat
line.

A `kickstart` without a ruling after the line does not continue the run. It exits with
`[phase32_points] the cumulative clock ... has reached the committed stop line ...`.

### D-20 past-the-line relaunch (developer only, after a ruling)

There is no ruling file and no second plist. The plist argv never changes. The relaunch is this
manual command, run from the repo root:

```bash
caffeinate -dims .venv/bin/python scripts/phase32_points.py run --past-stop-line "<ruling>"
```

- The ruling text goes into `provenance.stop_line.past_line_ruling` of every point recorded after
  it.
- The driver refuses `--past-stop-line` while the clock is below the line, so a ruling cannot be
  pre-armed.
- `--heartbeat` defaults to `phase25_run.HEARTBEAT_PATH` = `data/phase25_heartbeat.jsonl`, the
  same file the plist uses.
- Launched by hand, the command's output goes to the terminal, not to `logs/phase32_sweep.*`. It
  also runs without the plist's `PERSONACORE_SWEEP_ACTIVE=1`. To keep the logs, append
  `>> logs/phase32_sweep.out 2>> logs/phase32_sweep.err` (optional; not part of D-20).

## Crash recovery

1. `launchctl bootout gui/$(id -u)/com.personacore.phase32.sweep`
2. Read `logs/phase32_sweep.err` (`tail -50`) and the last heartbeat lines.
3. If the refusal is benign (the process was killed between stages, or a record was written but
   not committed), run `launchctl bootstrap ...` and then `launchctl kickstart ...` again. Tracked
   points are skipped. A written but uncommitted trained record is committed first (D-11). The
   draw and score stages resume from their own sidecars and draw cache.
4. **Do not relaunch** after a `[phase31_probe]` or `[phase32_points]` SystemExit about replay
   counts. It means a step's replay differed from the recipe (D-07). Report it verbatim.

### Reviewed delete after a mid-training crash (only after a developer ruling)

A training that died half-way cannot resume, because its replay counts would be incomplete. The
driver refuses before any stage runs and names the paths to delete. For point `<key>`:

- the checkpoint and adapter: `teach_persona.arm_outputs(arm, prefix=point_plan(key)["prefix"])`,
  keys `checkpoint` and `adapter`. The refusal message prints both full paths;
- the training sidecar `data/phase25_<key>_training.json`;
- the replay sidecar `data/phase32_<key>_replay.json`, if it is present.

Delete exactly the paths the refusal message names, with no globs, and then relaunch. The two
refusal messages are:

- `<checkpoint> exists without <training sidecar>: ... Delete <checkpoint> and <adapter> (if present) in a reviewed step, then rerun`
- `<training sidecar> exists without <replay sidecar>: ... Delete <training sidecar>, <adapter> and <checkpoint> in a reviewed step, then rerun`

## Expected outcomes and known risks

- **n64 is probably REFUSED under PREREG-03.** The Phase 31 n64 replay probe
  (`results/phase31_probe_point.json`, MPS) read taught recall 0/1008 and held-out 1/648. If the
  n64 control is unlearnable, the other 5 n64 points are written as PREREG-03 records carrying the
  control's recall counts. That is a pre-registered outcome and never a reason to re-tune or
  retry.
- **The advr_n8 control's dialogue gap must be positive (32-05 finding).** If the real advr_n8
  control's `adapter_on - adapter_off` came out ≤ 0, `phase32_frontier.build_frontier` would raise
  `ValueError: control_gap ... is not positive` at emit time (plan 07), not during the sweep. The
  sweep's committed records would be unaffected. A ≤ 0 gap is unlikely: the v4.0 n8 control_gap
  was +0.135 against a noise floor of 0.0052, and the Phase 31 n64 replay probe read +0.184
  (on 4.7575, off 4.5733). **In Task 3 verification, check the gap in the advr_n8 control record
  first.**
- **D-09:** WR-01 (relearn artifacts under `results/` versus `refuse_if_dirty`) belongs to Phase 33
  and is not implemented here. The crash recovery above covers only Phase 32's own reviewed delete.
