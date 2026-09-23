---
phase: 25-frontier-sweep-and-the-existence-gate-verdict
plan: 05
subsystem: infra
tags: [stall-watcher, launchagent, heartbeat, ast-guard, nyquist, stdlib-only]

# Dependency graph
requires:
  - phase: 23-cost-and-calibration
    provides: "results/phase23_cost.json (generation.per_shape ceiling rates, dp_n8/dp_n64 training legs) and results/phase23_never_taught.json (the tracked seed-1337 per-shape draw timings) — the two records N is derived from"
provides:
  - "scripts/phase25_watch.py — D-16's detect-never-act stall watcher, stdlib only, no subprocess"
  - "N_DERIVATION — the Nyquist table carried as data at full stored precision, re-derivable from the committed records"
  - "tests/test_phase25_watch.py — both halves watched: a stall record against a stalled stub, and an AST proof that the watcher cannot act, itself watched failing on a planted launchctl call"
affects: [25-06, 25-07, the sweep driver's outer-loop heartbeat emitter, the second LaunchAgent]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Detect/act separation enforced structurally rather than documentarily: FORBIDDEN_ACTIONS declared in the module, enforced by AST from outside it"
    - "Guards take SOURCE TEXT, never a path, so the live check and the planted RED probe run byte-identical walkers"
    - "A derived constant carries its derivation as a dict of measured literals, asserted against its source records under exact =="

key-files:
  created:
    - scripts/phase25_watch.py
    - tests/test_phase25_watch.py
  modified: []

key-decisions:
  - "N = 5 min is asserted against the MEASURED worst 24-prompt gap (A3, 3.7816 min), not the no-EOS ceiling gap (5.0303 min) — 5 sits below the ceiling figure, and that gap is itself the argument for a wall-clock beat"
  - "The measured-gap source is results/phase23_never_taught.json (tracked), not data/phase23_never_taught_seed1337_draws.json (gitignored) — the plan named the gitignored original, which would error on CI"
  - "dp_n64 training is pinned at 23.05460303958195 min; its two-decimal reading is 23.05, not the 23.06 quoted throughout CONTEXT/VALIDATION/PLAN"
  - "detection_latency_fraction_of_run is 7.788e-4 (0.056%-0.078% of a 107-150 h run), not the 0.005% quoted in 25-VALIDATION.md"
  - "The '~35 min' event-driven threshold is recorded as a ROUND FIGURE inside a measured 28.08-38.15 min envelope, labelled as such, rather than pinned as if it were itself a measurement"

patterns-established:
  - "Planted-RED into tmp_path with `git status --porcelain scripts/` asserted empty immediately after — tests/test_phase25_epsilon.py's register, reused"
  - "Failure messages take the walked file's label as a parameter so a scratch-copy RED names the scratch copy, not the clean real file"

requirements-completed: [FRONT-01]

# Metrics
duration: 42min
completed: 2026-08-31
---

# Phase 25 Plan 05: The Stall Watcher Summary

**A stdlib-only stall watcher for the 4.5-6.3 day unattended sweep whose threshold is recomputed from two committed cost records and whose inability to kill, relaunch or clean up is proved by an AST walk that has been watched failing on a planted `launchctl` call.**

## Performance

- **Duration:** 42 min
- **Started:** 2026-08-31T13:31:00Z
- **Completed:** 2026-08-31T14:13:00Z
- **Tasks:** 2 of 2
- **Files created:** 2 (`scripts/phase25_watch.py`, `tests/test_phase25_watch.py`)
- **Full suite:** `1700 passed, 1 skipped` in 379.01s (6:19)
- **Delta vs the 1684/1 baseline:** **+16 passed, +0 skipped** — exactly the 16 tests this plan adds
- **`make lint`:** exit 0 (`All checks passed!`, `237 files already formatted`)
- **Ancestry guard:** `git diff --exit-code` over the four frozen modules **plus `pyproject.toml`** exits 0

## The Threshold, Derived From Measurement

Every figure below was recomputed in this session from the committed records and is pinned in
`N_DERIVATION` at **full stored precision**, per `results/phase23_cost.json`'s own
`published_figure_rule`: *"A rounding is not a figure this phase publishes."*
`test_n_is_derived_from_the_measured_table` re-derives all of them and compares under exact `==`,
so N is asserted **against its sources, never against its own constant**.

### Regime 1 — measured, seed 1337, K=16, 216 prompts/shape

Source: `results/phase23_never_taught.json:per_seed[0].per_shape[*]`, `draws_per_question: 16`.
Denominator: the existing print cadence at `scripts/phase23_run.py:4524`, one line per **24 prompts**.
Rule: `minutes * 24 / prompts`.

| Shape | minutes/shape | 24-prompt gap (min) |
|---|---|---|
| **A3** | 34.03443515971303 | **3.7816039066347806** |
| A1-aggressive | 32.731153954161954 | 3.6367948837957726 |
| A1-mild | 29.013322102076685 | 3.2237024557862983 |
| A2 | 26.46837622569874 | 2.9409306917443048 |

**Worst measured gap: A3 at 3.7816 min.** This is the quantity D-16 names, and **N = 5 sits above it.**

### Regime 2 — the no-EOS ceiling bound

Source: `results/phase23_cost.json:generation.per_shape[*].draws_per_min_ceiling`
(`stop_terminated_n_ceiling: 0`, `mean_tokens_ceiling: 48` — nothing stops early).
Rule: `24 * 16 / draws_per_min_ceiling`.

| Shape | minutes/shape | 24-prompt gap (min) |
|---|---|---|
| **A1-mild** | 45.27308433651924 | **5.030342704057693** |
| A3 | 43.82077188855037 | 4.868974654283375 |
| A1-aggressive | 43.52801223797724 | 4.836445804219693 |
| A2 | 43.25040738768876 | 4.805600820854306 |

### Regime 3 — D-11's `FULL_FIDELITY_K = 48` promotion

`24 * 48 / 76.33674733338722` = **15.091028112173081 min** (A1-mild).

### The true worst case is not in the draw loop

`results/phase23_cost.json:training` — these legs emit **zero** per-shape lines:

| Leg | seconds | minutes |
|---|---|---|
| `dp_n8` | 205.44225783273578 | 3.4240376305455964 |
| `dp_n64` | 1383.276182374917 | **23.05460303958195** |

### The window, and why the beat is wall-clock

```
3.7816  <  N = 5  <  23.0546
(measured worst draw gap)   (dp_n64 training leg)
```

`test_n_is_derived_from_the_measured_table` asserts exactly that chain. It also asserts the
uncomfortable half: `5 < 5.030342704057693 < 15.091028112173081`. **N = 5 is BELOW the ceiling-regime
gap and far below the K=48 projection**, so under an *event-driven* beat N = 5 would false-fire in
the ceiling regime and on every promoted shape. Under the wall-clock beat it fires on neither,
because the driver emits a line every 60 s regardless of stage. That measured spread between regimes
is the whole argument for the contract, and it is recorded as data rather than asserted as prose.

The event-driven counterfactual, recomputed (`training_leg + first 24-prompt gap after it`):

| Rung | max silence (min) | x the 5.0303 ceiling gap |
|---|---|---|
| K=16 | 28.084945743639643 | 5.583107831000283 |
| K=48 | 38.145631151755026 | 7.583107831000282 |

**22** n=64 training legs (D-08's 44 = 2 x (16 sigma + 6 ratios); half carry an n=64 leg) would each
false-fire below that envelope.

## The Stall Record, Verbatim

Produced by the deliberately-stalled stub at `/tmp/hb.jsonl` with `now = 00:06:00` against a beat at
`00:00:00`, `action_taken` present as the literal `none`:

```json
{"action_taken": "none", "action_taken_reason": "D-16: heartbeat silence is DETECTED, never ACTED ON. An automatic restart would re-enter a sweep point WITHOUT passing the driver's deliberate resume logic, making a supervisor — not a person — the thing that violates D-10's one-attempt rule. The LaunchAgent therefore runs with KeepAlive FALSE (D-12) and this watcher cannot kill, relaunch or clean up anything. Correcting a stall is a human act, taken after reading this record.", "detected_utc": "2026-08-31T00:06:00+00:00", "heartbeat": "/tmp/hb.jsonl", "heartbeat_seconds": 60, "last_beat": {"draw_index": 7, "point": "dp_n8_sigma0p000000", "shape": "A3", "stage": "draw", "utc": "2026-08-31T00:00:00+00:00"}, "missed_beats": 6.0, "silence_minutes": 6.0, "stall_threshold_minutes": 5}
```

The operator path produces the same result through `main()`:

```
$ .venv/bin/python scripts/phase25_watch.py --heartbeat /tmp/hb.jsonl \
    --stall-record /tmp/stall3.jsonl --now 2026-08-31T00:06:00+00:00
[phase25_watch] STALL — 6.00 min of silence past 5 min. Last beat: point 'dp_n8_sigma0p000000',
stage 'draw', shape 'A3', draw_index 7 at '2026-08-31T00:00:00+00:00'. action_taken: 'none' —
recorded in /tmp/stall3.jsonl
exit=0
```

A 4-minute silence prints `None False` — nothing written, the path does not exist.

## The Never-Act Guard, Watched Failing

`test_the_never_act_guard_fires_on_a_planted_action` appends to a **scratch copy in `tmp_path`**:

```python
import subprocess


def _restart_the_sweep():
    subprocess.run(["launchctl", "kickstart", "-k", "x"])
```

The walker returns exactly one finding, `(439, 'run')`, and the verbatim failure message is:

```
/private/var/folders/.../test_the_never_act_guard_fi0/phase25_watch_planted.py:439: forbidden action 'run' appears in a CALL POSITION. D-16 makes this watcher a DETECTOR: an automatic restart, kill or cleanup re-enters a sweep point outside the driver's deliberate resume logic and violates D-10's one-attempt rule. Remove the call; a stall is corrected by a human.
```

Note what the finding is: the offending identifier is **`run`**, not `launchctl` — `launchctl` is a
string argument and never resolves to a name. That is the AST/grep distinction working in the
direction that matters.

**`git status --porcelain scripts/` was empty immediately after the plant** — asserted inside the
test (`assert completed.stdout == ""`) and confirmed again at the shell after the full suite, where
the only entry in the whole tree was the pre-existing ` M .gitignore` that is not this plan's.

The independently-verifiable half, `test_grep_goes_false_red_on_the_watcher`, measures the reason
the guard is a parse: **8 of 8** `FORBIDDEN_ACTIONS` tokens occur textually in
`scripts/phase25_watch.py` (including `kill` and `launchctl`) and **0** resolve to a call. A textual
gate over that file would be red on a correct file today.

## Verification

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest tests/test_phase25_watch.py -v` | **16 passed, 0 skipped** in 0.11s |
| `.venv/bin/python -m pytest tests/test_phase25_watch.py -k "boundary" -v` | **3 passed**, 13 deselected — 4.9 False / 5.0 True / 5.1 True |
| `.venv/bin/python -m pytest tests/ -q` | **1700 passed, 1 skipped** in 379.01s (baseline 1684/1, delta **+16/+0**) |
| `make lint` | exit 0 |
| Task-1 acceptance: 6-min silence | `one record, action_taken 'none' silence 6.0`, exit 0 |
| Task-1 acceptance: 4-min silence | `None False`, exit 0 |
| Task-1 acceptance: `N_DERIVATION` gate | prints `5 60`, exit 0 |
| Task-1 acceptance: import set | `['argparse', 'datetime', 'json', 'pathlib']` — **no `subprocess`** |
| Task-2 acceptance: both halves present by AST | `both halves committed`, exit 0 |
| Task-2 acceptance: CLI on a stalled fixture | `exit=0` |
| `git diff --exit-code` over the 4 frozen modules + `pyproject.toml` | exit 0 |

## Threat Register Coverage

| Threat ID | Where it is discharged |
|---|---|
| T-25-21 (watcher acquires the ability to relaunch) | `test_the_watcher_takes_no_action` (AST over call positions + import-set lock excluding `subprocess`), watched failing at `test_the_never_act_guard_fires_on_a_planted_action` |
| T-25-22 (a stall leaves no record) | `test_repeated_checks_append_rather_than_overwrite` — two checks leave two records with the same `last_beat` |
| T-25-23 (N too coarse or too fine) | `test_n_is_derived_from_the_measured_table` — the window recomputed from `phase23_cost.json` |
| T-25-24 (watcher writes to the heartbeat) | `test_the_watcher_writes_only_the_stall_record` — every write's path operand resolves to `stall_record_path`; the heartbeat is reached only by `read_text` |
| T-25-25 (a detected stall read as a crash) | `test_a_detected_stall_is_a_successful_run` — real `subprocess` invocation of `main()`, `returncode == 0` |
| T-25-SC (installs) | Zero installs. Stdlib only. `pyproject.toml` byte-unchanged |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The plan's named measured-gap source is gitignored and absent from CI**

- **Found during:** Task 2, writing `test_n_is_derived_from_the_measured_table`
- **Issue:** the plan's `read_first` and the first draft of `N_DERIVATION` named
  `data/phase23_never_taught_seed1337_draws.json` as the source of the measured per-shape timings.
  `git check-ignore -v` reports `.gitignore:17: data/` — the file is **untracked**. A test
  recomputing the gap from it passes on this laptop and hard-errors on `ubuntu-latest` CI and on any
  fresh clone.
- **Fix:** repointed to `results/phase23_never_taught.json:per_seed[0].per_shape[*]`, which is
  tracked. Verified identical before switching: same `adapter_sha256`, same `corpus_sha256`, same
  `draws_per_question: 16`, and identical `minutes` + `prompts` on all four shapes. The gitignored
  original is retained in `N_DERIVATION` as `record_gitignored_original` so the provenance chain is
  not erased.
- **Commit:** `ef4f0bc`

**2. [Rule 1 - Bug] `23.06` is a rounding of a rounding; the record says `23.05`**

- **Found during:** Task 2, first run of `test_n_is_derived_from_the_measured_table` (natural RED —
  the assertion was written to the plan's figure and the record refused it)
- **Issue:** `25-CONTEXT.md` (D-14), `25-VALIDATION.md`, `25-05-PLAN.md`'s `must_haves` and its
  Task-1 action all state **"`dp_n64` 1383.3 s = 23.06 min"**. The seconds were rounded to `1383.3`
  first and the resulting `23.055` was then rounded up by hand. From the record's own full-precision
  leaf, `1383.276182374917 / 60 = 23.0546` -> **23.05**; even the intermediate `1383.3 / 60 = 23.055`
  rounds to `23.05` under Python's round-half-to-even.
- **Fix:** `N_DERIVATION["dp_n64_training_minutes"]` carries the full float `23.05460303958195` and a
  sibling `dp_n64_training_minutes_two_decimal_note` records the chain; the test asserts
  `round(n64_seconds / 60.0, 2) == 23.05`. Nothing in the module quotes a two-decimal `23.06`.
  Governed by `phase23_cost.json`'s own `published_figure_rule`.
- **Impact:** none on any conclusion — the difference is 0.6 s and N = 5 sits far below either
  reading. The plan's `dp_n64_training_minutes > 23.0` acceptance gate still passes.
- **Commit:** `881e8a7`

**3. [Rule 1 - Bug] `0.005%` detection latency is ~14x too small**

- **Found during:** Task 1, computing `detection_latency_fraction_of_run`
- **Issue:** `25-VALIDATION.md` § *Sampling Rate* and the plan's Task-1 action both state the 5-minute
  detection latency is **"0.005%"** of a 107-150 h run. Recomputed: `5 / (107 * 60) = 7.788e-4` =
  **0.0779%**, and `5 / (150 * 60) = 5.556e-4` = **0.0556%**.
- **Fix:** `detection_latency_fraction_of_run` carries the computed `0.000778816199376947` (the
  shortest run, where the latency is the largest share), with
  `detection_latency_percent_envelope = (0.0556, 0.0779)` and a `detection_latency_note` naming the
  discrepancy. `test_the_contract_is_pinned_as_data` recomputes both from
  `STALL_THRESHOLD_MINUTES` and `run_envelope_hours`.
- **Impact:** none on any conclusion — the latency is negligible against the run either way.
- **Commit:** `5ce252e`

### Deliberate Reading of an Ambiguous Instruction

**4. "N sits above the worst draw gap" resolves to the MEASURED gap, not the ceiling gap**

Task 2 asks the test to assert `STALL_THRESHOLD_MINUTES` sits above "the worst draw gap". There are
two candidates and the choice is load-bearing, because **N = 5 is above the measured worst gap
(3.7816) but BELOW the ceiling-regime worst gap (5.0303)** that the plan's own Task-1 acceptance
criterion asserts is `>= 5.0`. Taking the ceiling reading would make the plan self-contradictory.

Resolved to the **measured** gap, which is what D-16 asks for in its own words ("*the measured
worst-case gap between heartbeat lines at the slowest attack shape*") and what row 1 of
25-VALIDATION.md's Nyquist table records. The ceiling relation is asserted too, in the direction it
actually holds (`5 < 5.0303 < 15.091`), and `N_DERIVATION["why_the_draw_gaps_do_not_bound_n"]`
states plainly that under an event-driven beat N = 5 would false-fire in both the ceiling regime and
at K=48 — which strengthens rather than weakens the case for the wall-clock contract. Nothing was
smoothed over.

**5. `~35 min` recorded as a round figure inside a measured envelope, not as a measurement**

The plan asks `N_DERIVATION` to carry "an event-driven beat ... would force `N >= ~35 min`". No
single measured quantity equals 35. The fully-measured statement is the envelope
`(28.084945743639643, 38.145631151755026)` — `dp_n64` training plus the first 24-prompt gap after
it, at K=16 and K=48. `35` is recorded as `stated_round_figure_minutes` with an explicit
`stated_round_figure_status` saying it is a round figure inside that envelope and not itself a
measurement, and `test_the_event_driven_alternative_is_computed_from_the_same_records` asserts
`low < 35 < high` and that `round(35 / 5.0303) == 7` — the plan's "7x coarser" figure, over its
stated denominator. The envelope ends are 5.58x and 7.58x, which bracket it.

### Small Corrections Made While Building

- `_action_failure_message` takes the walked file's label as a parameter rather than hard-coding
  `scripts/phase25_watch.py`. The first version printed the real file's path for a violation that
  lived in `tmp_path`, which would send a reader to a clean file.

## Known Stubs

None. Both files are complete and exercised.

## Threat Flags

None. This plan adds no network endpoint, no auth path, no schema and no file access beyond one
read-only `read_text` and one append to a caller-supplied path.

## What This Plan Does NOT Deliver

`scripts/phase25_watch.py` is the **consumer** of the heartbeat. **The emitter does not exist yet** —
no code currently writes a `(utc, point, stage, shape, draw_index)` line from the driver's outer
loop on a 60 s wall-clock timer. `HEARTBEAT_SECONDS`, `HEARTBEAT_SECONDS_PROVENANCE` and
`HEARTBEAT_FIELDS` are the contract the driver plan must satisfy; a driver that emits a differently
shaped line will produce stall records with `None` in the diagnostic fields rather than an error.
The LaunchAgent plists for both the sweep and the watcher are likewise out of scope here.

## Self-Check: PASSED

- `scripts/phase25_watch.py` — FOUND
- `tests/test_phase25_watch.py` — FOUND
- `5ce252e` — FOUND
- `ef4f0bc` — FOUND
- `881e8a7` — FOUND
- `e1a6c63` — FOUND
- `.planning/STATE.md` / `.planning/ROADMAP.md` — untouched (`git status --porcelain` shows only the
  pre-existing ` M .gitignore`, which is not this plan's)
