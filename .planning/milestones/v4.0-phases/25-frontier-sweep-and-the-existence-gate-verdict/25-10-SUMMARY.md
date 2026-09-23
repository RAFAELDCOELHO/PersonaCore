---
phase: 25-frontier-sweep-and-the-existence-gate-verdict
plan: 10
subsystem: sweep-driver
tags: [driver, atomicity, resume, git-surface, heartbeat, D-09, D-10, D-12, SS-O1]
requires:
  - scripts/phase25_prereg.py   # prove_first_attempt, POINT_RECORD_GLOB, DISK_PRECHECK_BYTES (25-01)
  - scripts/phase25_record.py   # point_record_path, build_point_record, ORDERED_POINT_KEYS (25-08)
  - scripts/phase25_watch.py    # HEARTBEAT_FIELDS, HEARTBEAT_SECONDS, read_last_beat (25-05)
  - scripts/phase23_run.py      # the port source — READ, never modified
  - scripts/teach_persona.py    # train_arm, the single production entry all 44 points share
provides:
  - scripts/phase25_run.py                        # the 44-point driver
  - scripts/phase25_run.py::atomic_write_json     # tmp + fsync + os.replace
  - scripts/phase25_run.py::load_draws            # the three-field cache identity
  - scripts/phase25_run.py::shape_is_complete     # "complete" as a conjunction
  - scripts/phase25_run.py::commit_point_record   # SS-O1's two git writes, one path
  - scripts/phase25_run.py::beat                  # the five-field heartbeat line
  - scripts/phase25_prereg.py::GIT_SURFACE_EXCEPTION
affects:
  - 25-14   # launches this driver
  - 25-15   # runs the two control points through run_point
  - 25-17   # sweep-time argv
  - 25-20   # closes the SS-O1 exception
tech-stack:
  added: []            # zero installs; pyproject.toml byte-unchanged (RPT-03)
  patterns: [tmp+fsync+os.replace, AST-structural-gate, daemon-thread-wall-clock-heartbeat]
key-files:
  created:
    - scripts/phase25_run.py
    - tests/test_phase25_driver.py
  modified:
    - scripts/phase25_prereg.py      # append-only: 66 insertions, 0 deletions
    - tests/test_phase23_resume.py   # census register, Rule 3
decisions:
  - "The heartbeat is emitted from a DAEMON THREAD, not polled from the outer point loop. Polling cannot satisfy D-12's 'independent of which stage is running' — a 23.05-min dp_n64 training leg reaches no loop iteration, so a polled beat would false-fire STALL_THRESHOLD_MINUTES = 5 on all 22 n=64 legs."
  - "The git-surface AST walk collects every List/Tuple literal whose first element is the constant 'git', which is strictly stronger than walking subprocess call arguments — it also catches an argv built on a prior line and passed by name."
  - "shape_is_complete is a CONJUNCTION of draws AND timing, deliberately stronger than the port source's presence check at phase23_run.py:4452."
  - "train_point takes dp_clip_norm as a caller-supplied argument rather than reading phase25_record.CONTROL_CLIP_NORM, which the plan names and which does not exist anywhere in the repository."
metrics:
  tasks: 3
  commits: 4
  duration: ~2h
  completed: 2026-08-31
  suite_before: "1859 passed, 1 skipped"
  suite_after: "1882 passed, 1 skipped"
  new_tests: 23
---

# Phase 25 Plan 10: The 44-Point Frontier Driver Summary

The driver that will spend this phase's 107–150 GPU hours now exists, and its two dangerous
properties are structural rather than declared: the ~973 KB block write is atomic under a simulated
kill at three distinct points, and its executable git surface is proved by AST to be exactly
`{add, commit} ∪ {ls-files, show, rev-parse, status}`, watched failing on a planted `git push`.

## What Landed

| Commit | Task | Files |
| --- | --- | --- |
| `99cc4fc` | 1 — ported resume + the [BLOCKING] atomic write | `scripts/phase25_run.py` |
| `bb42571` | 2 — §O1's named exception in the pre-registration | `scripts/phase25_prereg.py` |
| `2691266` | 3 — the 23-test battery | `tests/test_phase25_driver.py` |
| `5c0f4d3` | Rule 3 deviation — the `train_arm` census register | `tests/test_phase23_resume.py` |

## The Measurements, With Their Sources

**The block size that makes atomicity load-bearing — the plan's figure REPRODUCES.**
`stat data/phase23_never_taught_seed1337_draws.json` reads **973,486 bytes**. The writer being
replaced, `phase23_run._never_taught_write_draws` (`scripts/phase23_run.py:4300`), is literally
`path.write_text(json.dumps(blob, sort_keys=True))`. **That writer is now atomic in Phase 25:**
`phase25_run.write_draws` calls `atomic_write_json`, which serialises first, opens a temp file in
the destination's own directory, `flush()` + `os.fsync()`, then `os.replace`.

**A PLAN CLAIM MEASURED FALSE — both readings published.** 25-10-PLAN.md states, in a `[BLOCKING]`
must-have and again in Task 1's `read_first`, that `grep -rn "os.replace" scripts/ src/` returns
**0** and that "there is NO atomic-write helper anywhere in the repository."

```
$ grep -rn "os\.replace" scripts/ src/ | wc -l
2
scripts/phase25_record.py:913:    `fsync`, then `os.replace`. `os.replace` is atomic within one filesystem, and the temp file is
scripts/phase25_record.py:941:        os.replace(handle.name, path)
```

Line 941 is a live call inside `write_point_record`, which already lands the per-point RECORD by
exactly this recipe — it shipped in wave 2 (25-08). **The conclusion survives, and the gap is real
and unchanged in substance:** the DRAW CACHE at 973,486 B is an order of magnitude larger than a
point record and *is* written non-atomically by `phase23_run`, and closing it was correctly
`[BLOCKING]`. Only the claim of NOVELTY was wrong — the atomic write is a second application of a
same-phase sibling's pattern, not the repository's first. Both readings are recorded in the driver's
module docstring and in the test's docstring, and the test the plan named
`test_the_repo_had_no_atomic_helper_before_this` was written at the honest strength instead, as
`test_os_replace_appears_only_in_the_two_phase25_writers` — which asserts the phase has ONE atomic
recipe rather than two competing ones. **This is the sixteenth measurably false prose figure this
phase has found.**

**A PLAN-NAMED SYMBOL THAT DOES NOT EXIST.** `phase25_record.CONTROL_CLIP_NORM` is named by 25-15's
plan and was the natural source for `train_arm`'s `dp_clip_norm`. `grep -rn "CONTROL_CLIP_NORM"
scripts/*.py` returns **nothing** outside the file I was writing. Resolved by making `dp_clip_norm`
a caller-supplied keyword on `train_point` rather than inventing a substitute constant — the pin
belongs to 25-12/25-15, not to the driver.

**TWO OTHER PLAN-NAMED PATHS THE CODE REFUSED.** `scripts/phase19_recall.py` does not exist; the
real module is `phase14_recall` (resolved from `phase23_run.py:4418`, which imports it lazily and
says why). And `recall.fs` is not the fact source — `phase14_factset` is.

**THE N-DERIVATION FIGURES I QUOTED, RE-MEASURED FROM THE COMMITTED CONSUMER** rather than from
plan prose. Every one reproduces against `phase25_watch.N_DERIVATION`:

| Figure | Value read back | Where I use it |
| --- | --- | --- |
| worst measured 24-prompt gap | `3.7816039066347806` min | `_heartbeat_loop` docstring |
| worst no-EOS ceiling gap | `5.030342704057693` min | same |
| `dp_n64` training leg | `23.05460303958195` min | same |
| event-driven envelope | `(28.084945743639643, 38.145631151755026)` min | same |
| n=64 training legs | `22` | same |

I quote **23.05**, not the 23.06 that 25-CONTEXT.md, 25-VALIDATION.md and 25-05-PLAN.md carry:
`N_DERIVATION["dp_n64_training_minutes_two_decimal_note"]` records that 23.06 comes from rounding
the seconds to 1383.3 first, and that the record's own rule is "a rounding is not a figure this
phase publishes."

## The Heartbeat Contract, Satisfied Against the Consumer

`25-05-SUMMARY.md` records that no code emitted the beat and warns that a mis-shaped line yields
`None` in the watcher's diagnostic fields rather than an error. So the contract is asserted against
`phase25_watch` directly, never against prose:

```
$ .venv/bin/python -c "...; assert set(r.HEARTBEAT_FIELDS)==set(w.HEARTBEAT_FIELDS)"
('utc', 'point', 'stage', 'shape', 'draw_index') ('add', 'commit') ('ls-files', 'show', 'rev-parse', 'status')
```

and `test_the_heartbeat_line_parses_with_the_watchers_reader` emits a real beat, reads it back with
`phase25_watch.read_last_beat`, asserts the returned dict **equals** the written one, and asserts
each of the five fields is non-`None` — which is the exact failure mode 25-05 warned would be
silent. `HEARTBEAT_SECONDS` is imported at call time in `start_heartbeat` rather than restated, so
writer and reader cannot drift on the period either.

**A DESIGN DECISION THE PLAN DID NOT SPECIFY, AND THE MEASUREMENT THAT FORCED IT.** The plan says
"drive it from a wall-clock 60 s timer in the driver's outer loop." A beat polled from the outer
loop cannot satisfy `HEARTBEAT_SECONDS_PROVENANCE`'s stated property — "independent of which stage
is running" — because a `dp_n64` training leg runs 23.05 min without reaching a single loop
iteration, and `STALL_THRESHOLD_MINUTES = 5` would then fire a false stall on all **22** n=64 legs.
The beat therefore runs on a daemon thread whose trigger is `threading.Event.wait(seconds)`: one
stdlib call that is both the wall-clock timer and the shutdown path, costs no CPU beside a saturated
GPU, and cannot outlive the driver. `test_the_beat_is_wall_clock_not_event_driven` asserts by AST
that the trigger reads `wait` and no prompt index, and that no `beat` call lies inside
`_draw_one_shape`'s per-prompt loop.

## §O1's Git Surface — Measured, and Watched Failing

**THE MEASURED SET.** The AST walk over `scripts/phase25_run.py` found exactly:

```
['add', 'commit', 'ls-files', 'rev-parse', 'show', 'status']
equals {add, commit} u {ls-files, show, rev-parse, status}: True
```

Every `add`/`commit` site is asserted to lie lexically inside `commit_point_record`.

**THE WATCHED RED — §O1's ADDITIONAL REQUIREMENT.** A copy of the driver in `tmp_path` with
`subprocess.run(["git", "push", "origin", "main"])` appended. The gate's verbatim failure message:

```
/var/folders/7k/hgktxwvx6p54ch16qtg7pwlw0000gn/T/tmp3tk16req/phase25_run_planted.py:833 in
_planted(): git subcommand 'push' is outside the pre-registered surface ['add', 'commit',
'ls-files', 'rev-parse', 'show', 'status']. §O1 bounds an unattended six-day driver on `main` to
`add` and `commit` over ONE resolved path under `results/`.
```

`git status --porcelain scripts/` immediately after returned **empty** — the plant never touched a
real repository file, and `test_the_git_surface_gate_fires_on_a_planted_push` asserts that emptiness
in-test as well.

**THE WALK IS STRONGER THAN THE PLAN ASKED FOR.** The plan says "collect every `subprocess` call
and, from each, resolve the first string element after `"git"`." I walk every `List`/`Tuple` literal
whose first element is the constant `"git"` instead. A driver that wrote `argv = ["git", "push"]` on
one line and `subprocess.run(argv)` on the next would evade a call-argument-only walk while
executing exactly the action §O1 forbids. A docstring cannot produce a `List` node, so the walk
stays immune to the driver's own deliberate prose about `git push` and `git rm`.

**THE BEHAVIOURAL HALF — `test_the_staged_path_is_exactly_the_point_record`.** Against a real
scratch repository in `tmp_path` containing an unrelated dirty file:

- `git show --name-only --format= HEAD` named **exactly one path**:
  `results/phase25_point_dp_n8_sigma0p000000.json`.
- `git status --porcelain` afterwards still showed `?? unrelated.txt`, and the file's bytes were
  re-read and asserted still `"dirty\n"` — **the unrelated dirty file was still dirty and still
  uncommitted after the commit.**

`test_gitignored_trees_are_never_staged` repeats it with dirty files under `data/` and
`checkpoints/`; neither appears in the commit. `test_a_no_op_commit_is_refused` proves the
second-commit refusal, since a commit with no bytes behind it is an ambiguous second-attempt marker
in the history D-10 reads.

## The Atomic Write, Proved by Simulated Kill

`test_the_atomic_write_survives_a_kill_mid_write` is parametrized over **three** kill points, because
the three steps fail differently:

| `kill_at` | How it is simulated | What it breaks if unguarded |
| --- | --- | --- |
| `write` | `NamedTemporaryFile.write` writes half the payload then raises `OSError` | torn bytes |
| `fsync` | `phase25_run.os.fsync` raises | bytes unflushed behind a durable rename |
| `replace` | `phase25_run.os.replace` raises | a complete temp file that never landed |

In all three the test asserts, after the exception: **(i)** the destination still parses with
`json.loads`, **(ii)** it equals the FIRST blob **byte-for-byte** (`path.read_bytes() == before`),
and **(iii)** `sorted(p.name for p in tmp_path.iterdir()) == ["draws.json"]` — no stray temp file
remains. The second write is asserted **larger** than the first, so a non-atomic writer would leave
a destination whose length falls between the two, which is exactly the torn state being excluded.

`test_the_atomic_write_fsyncs_before_replacing` asserts by AST that `fsync`'s `lineno` is strictly
less than `replace`'s inside `atomic_write_json` — without the fsync the rename can be durable while
the bytes are not. `test_the_atomic_writes_tmp_file_is_a_sibling_of_the_destination` asserts the
temp path's parent equals the destination's parent, so `os.replace` never crosses a filesystem.

## D-10's One-Attempt Identity Under Resume, Proved

A point killed anywhere in steps 3–6 of `run_point` **costs at most one shape and never the point,
and resuming it is the SAME attempt.** The proof is structural, from the ordering in `run_point`:

1. `prove_first_attempt` reads `tracked_point_records()` — `git ls-files`, i.e. **TRACKED** records,
   not files on disk.
2. `commit_point_record` (step 7) is the **only** thing that makes a record tracked.
3. Therefore a point killed before step 7 produced no evidence, is refused by nothing, and resumes
   into the cache step 4 already persisted per shape.

`test_the_resume_skips_a_complete_shape_on_restart` and the parametrized
`test_the_resume_redraws_an_incomplete_shape` pin "complete" as a **conjunction** of `draws` and
`timing` from both sides — deliberately stronger than the port source's presence check
(`phase23_run.py:4452` tests `if family in recorded["shapes"]`). A half block that skipped would drop
a shape's timing out of the record silently, and the record's rate figures are what price the sweep.

The three-field identity is refused field by field (3 parametrized cases, all pass), and
`test_a_k16_cache_is_refused_for_a_k48_promotion` asserts D-11's consequence as a **feature**:
because `k` is in the identity, a K=16 → K=48 promotion refuses its own draws rather than pooling
readings of different statistical power and publishing the mixture at the higher K's apparent power.

`block_sha256` records each completed shape block's digest into the point record as it lands, closing
the delete-and-redraw leak that `data/` being gitignored would otherwise leave traceless.

## The `--points` Default, and the Wave-3/Wave-5 Trap

`--points` defaults to `None` at the parser and `ORDERED_POINT_KEYS()` is called inside `main()`
after parsing. `test_the_driver_imports_without_the_sigma_ladder` **simulates** the ladder's absence
with `monkeypatch.delattr(mitigation_budget, "SIGMA_LADDER", raising=False)` rather than asserting
it — an assertion of absence would be correct in wave 3 and permanently RED from wave 5, the exact
self-invalidating shape RPT-02 exists to catch. It reloads the driver, constructs the parser, and
asserts `ORDERED_POINT_KEYS()` raises `SystemExit` naming **25-12**. Both hold.

## The `GIT_SURFACE_EXCEPTION` Append — Additivity Proved

```
$ git diff --numstat bb42571~1 bb42571 -- scripts/phase25_prereg.py
66	0	scripts/phase25_prereg.py
```

**66 insertions, 0 deletions.** Nothing pre-registered in section (c) is byte-changed. The constant
is filed in a new section (g) whose own comment discloses that it was appended AFTER the
pre-registration commit and states why that cannot buy the freedom a pre-registration spends: it
decides no threshold, judges no reading and renders no verdict. It quotes `.planning/STATE.md`'s
read-only mechanism verbatim, gives the three checkable reasons it cannot hold, bounds the exception
to two subcommands and one path, names that commits land on `main` under `branching_strategy: none`,
and time-boxes it to this phase (T-25-115).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] `tests/test_phase23_resume.py::test_resume_from_none_is_inert` went RED**
- **Found during:** the full-suite run after Task 3
- **Issue:** a repo-wide census maintains `_TRAIN_ARM_CALL_SITES`, a register of every `train_arm(`
  hit in `scripts/` and `tests/`. `scripts/phase25_run.py:440` is a genuine 25th site, so
  `grep found 25 driver hits but the register lists 24`. Hazard (d) exactly.
- **Fix:** resolved through the census's OWN mechanism on all four of its teeth — registered the
  site with its reason, bumped the counted literal `8+1+1+1` → `8+1+1+1+1` with its ledger line
  extended (the literal pins a count AGAINST the register rather than deriving one), and admitted
  `"scripts/phase25_run.py": 1` in `_RESUME_PASSERS` as a COUNT so a second passer still reddens.
  The per-file AST call count needed no change: the driver has exactly one.
- **Why the driver legitimately passes `resume_from`:** D-09's unit is the sweep POINT. A point
  killed mid-training over a 4.5–6.3-day unattended run must resume its own 200 steps rather than
  restart them, and D-10 counts that resumption as the SAME attempt. It is the seam's third
  production consumer and the first outside `phase23_run.py`.
- **Files modified:** `tests/test_phase23_resume.py`
- **Commit:** `5c0f4d3`

**2. [Rule 3 — Blocking] three plan-named symbols the code refuses**
- `phase25_record.CONTROL_CLIP_NORM` — does not exist anywhere. `dp_clip_norm` became a
  caller-supplied keyword on `train_point`; the pin belongs to 25-12/25-15.
- `phase19_recall` — does not exist. The real module is `phase14_recall`.
- `recall.fs` — not the fact source. `phase14_factset` is.
- **Reported, not substituted with an invention.** Commit `99cc4fc`.

**3. [Rule 2 — Correctness] `phase18_extraction` is imported LAZILY, not at module scope**
- It is heavy and torch-touching; `phase23_run.py:4316` imports it lazily for that stated reason. A
  module-scope import would make `--dry-run` and every test in this battery pull torch. The three
  constants the driver needs are re-exported by `phase25_record`, which resolves them from the
  COMMITTED LITERAL and never imports the module. `test_dry_run_touches_no_gpu_and_writes_no_result`
  asserts `NOTORCH` in a child process. Commit `99cc4fc`.

### Task-Boundary Deviation (disclosed)

Tasks 1 and 2 both name `scripts/phase25_run.py` as their only driver file. The module was authored
as one coherent file in a single pass, so the heartbeat and `commit_point_record` landed inside
Task 1's commit `99cc4fc` rather than a separate one. Task 2's commit `bb42571` carries the work
that is genuinely separable and separately checkable — the `GIT_SURFACE_EXCEPTION` append to
`scripts/phase25_prereg.py`, with its insertions-only proof. Every Task 2 acceptance criterion is
satisfied and quoted above; only the commit boundary differs.

### Cosmetic

Commits `bb42571` and `2691266` render `§O1` as `$O1` in their subject lines — a shell escaping
slip. Not amended: rewriting two commits for a glyph is churn, and the reference is unambiguous.

## Verification

| Check | Result |
| --- | --- |
| `pytest tests/test_phase25_driver.py -v` | **23 passed, 0 skipped** in 1.24 s |
| `pytest tests/ -q` | **1882 passed, 1 skipped** in 1196.60 s (0:19:56) |
| delta vs the `1859 passed, 1 skipped` baseline | **+23 passed, +0 skipped — exactly this plan's new tests. Zero regressions.** |
| `pytest tests/test_phase23_resume.py -q` | 9 passed in 103.69 s (incl. the known-flaky bit-identity test) |
| `-k "resume or atomic"` | 8 passed |
| `-k "cache_identity"` | **3 passed** (the plan's required count) |
| `-k "kill_mid_write"` | 3 passed |
| `-k "git_surface or heartbeat"` | 3 passed |
| `-k "imports_without_the_sigma_ladder"` | 1 passed |
| `phase25_run.py --dry-run --points dp_n8_sigma0p000000` | exit 0; nothing written under `results/` |
| `make lint` | All checks passed, 252 files formatted |
| `git diff --exit-code` on the 4 ancestry-guarded modules + `phase23_run.py` + `pyproject.toml` | exit 0 |

Dry-run output, verbatim:

```
[phase25_run] DRY RUN dp_n8_sigma0p000000: first attempt OK, disk OK, cache
data/phase25_dp_n8_sigma0p000000_draws.json absent, 4/4 shape(s) pending
('A1-mild', 'A1-aggressive', 'A2', 'A3'), record would land at
results/phase25_point_dp_n8_sigma0p000000.json
```

**`-k "resume or atomic"` initially selected ZERO tests** — a vacuous filter, which is the false-green
class this repository fights. Five tests were renamed so the plan's own acceptance criterion is
non-vacuous; it now selects 8. `test_the_drivers_executable_git_actions_are_exactly_add_and_commit`
kept its exact plan-named spelling.

## Known Stubs

None. Every function in `scripts/phase25_run.py` is wired: `run_point`'s seven steps each call a
real committed API, and the two GPU-touching halves (`train_point`, `_draw_one_shape`) delegate to
`teach_persona.train_arm` and `phase14_recall.draw_all` with the real signatures asserted by AST.
No point was run — that is 25-15 onward, after 25-14's human checkpoint, exactly as scoped.

## Threat Flags

None. Every file created or modified is either a test, a driver whose entire git and filesystem
surface is asserted structurally, or a 66-line append to a constants module. No new network
endpoint, auth path or schema change at a trust boundary.

## Self-Check: PASSED

- `scripts/phase25_run.py` — FOUND (829 lines)
- `tests/test_phase25_driver.py` — FOUND (640 lines)
- `scripts/phase25_prereg.py::GIT_SURFACE_EXCEPTION` — imports and satisfies both substring assertions
- `99cc4fc` — FOUND
- `bb42571` — FOUND
- `2691266` — FOUND
- `5c0f4d3` — FOUND
- `.planning/STATE.md`, `.planning/ROADMAP.md` — untouched (orchestrator owns those writes)
