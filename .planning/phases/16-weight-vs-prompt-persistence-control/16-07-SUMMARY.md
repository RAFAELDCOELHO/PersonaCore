---
phase: 16-weight-vs-prompt-persistence-control
plan: 07
subsystem: evaluation
tags: [PERS-01, STAT-01, STAT-02, STAT-05, ladder, blocking-gate, real-weights]
key-files:
  created:
    - results/phase16_ladder_report.md
    - results/phase16_ladder_raw.log
  modified:
    - scripts/phase16_ladder.py
    - tests/test_phase16_ladder.py
metrics:
  wall_clock_min: 79.6
  rungs: 7
  questions_per_rung: 216
  draws_per_question: 9
  rungs_passed: 1
  monotonicity_anomalies: 2
  licensed_branch: span_2
  determinism_rungs_reproduced: 4
---

# 16-07: The PERS-01 capability ladder, run on the real weights

## What was done

The ladder ran end to end on `convbase_slim` + `persona_adapter`: 7 rungs x 216 questions x 9
draws, 79.6 min on MPS, seed 1337. `results/phase16_ladder_report.md` and
`results/phase16_ladder_raw.log` are committed at `5a17920`. SC1's ordering constraint is
discharged — the ladder is in git before plan 16-08 exists, and PREREG-02's ancestry guard covers
it from this commit forward.

## Results

| rung | span | measured distance (min / median / max) | answerable | verdict |
|---|---|---|---|---|
| `(1, 2)` | 1 | 1 / 1 / 1 | 1/216 | FAIL |
| `(1, 30)` | 1 | 13 / 26 / 60 | 3/216 | FAIL |
| `(2, 2)` | 2 | 1 / 1 / 1 | **15/216** | **PASS** |
| `(2, 30)` | 2 | 13 / 26 / 60 | 0/216 | FAIL |
| `(5, 2)` | 5 | 1 / 1 / 1 | 0/216 | FAIL |
| `(5, 30)` | 5 | 13 / 26 / 60 | 0/216 | FAIL |
| `fairness-control-rerun` | median 5 (real values) | not measured | 0/216 | FAIL |

**Licensed branch: `span_2`**, highest passed rung `(2, 2)`. Licensed: the base sustains a
two-token in-context copy at that rung's distance. NOT licensed: the multi-token claim the
four-arm comparison needs.

The nominal `~2` row measures at exactly 1 token; the `~30` row is a DISTRIBUTION (13 / 26 / 60),
printed as such because it is `2 + len(question)` and the fixture's questions run 11-58 tokens.
Neither is rendered as the grid label.

## Two monotonicity anomalies, unexplained

`(2, 2)` passed while BOTH easier rungs — `(1, 2)` and `(1, 30)` — failed. Recorded per D-14 as
named instrument anomalies, without stopping the run and without moving the licensed branch.

**The mechanism is not established.** During the run an induction-head reading was proposed
(prefix-match-and-copy needs at least two tokens to match on, so span 1 offers almost nothing).
**That reading is falsified by this data**: if it were the mechanism, span 5 should have exceeded
span 2, and span 5 scored exactly `0/216` at both distances. `(span 2, distance 1)` is a narrow
island, not a point on a monotone surface, and this grid contains no cell that separates the
candidate explanations. Anyone reading the ladder must treat the anomaly as open.

## D-19 honored

`results/phase14_recall_report.md` is byte-unchanged (`git diff --exit-code` clean; last touched by
`a2bc82d`, a Phase-14 commit). The top rung is the fairness control RE-RUN after the PERS-05
pairing fix: **0/216** against the committed **1/216**, a measured delta of **-1 answerable
question**. The fix changes which seeds are drawn by design, so this was never expected to
reproduce bit-for-bit; the delta is reported as a measurement rather than asserted to be zero, and
the gate stays anchored to the committed number.

## D-15 proxy validity: `proxy_consistent`, but DEGENERATE

Synthetic `(5, 30)` 0/216 vs top rung 0/216, difference `+0` against a divergence threshold of 10.

A caveat was added to the report at the human-verification checkpoint (additive commentary; no
measured number touched): **this consistent verdict carries almost no information.** Both cells
scored exactly zero, so they agree trivially — `+0` is what two dead cells produce whether or not
the synthetic substitution is fair. The check can only detect unfairness that MOVES the count, and
at the floor there is no movement to detect. **Plan 16-10 must not cite `proxy_consistent` as
validation of the low rungs.**

The pre-existing frame caveat also stands: `build_far_prompt`'s locked signature carries no fact
id, so its persona line is one fact-agnostic sentence while the fairness control gives each fact its
own taught statement. The two cells differ in frame as well as material.

## Determinism: 4 of 4 rungs reproduced exactly

The first run of this ladder died at rung 5 (see Deviations). It had completed rungs 1-4. The
relaunched run reproduced **all four, digit for digit**, in a separate process:

| rung | run 1 | run 2 | rate / bounds |
|---|---|---|---|
| `(1, 2)` | 1/216 | 1/216 | identical to 6 dp |
| `(1, 30)` | 3/216 | 3/216 | identical to 6 dp |
| `(2, 2)` | 15/216 | 15/216 | identical to 6 dp |
| `(2, 30)` | 0/216 | 0/216 | identical, same rule-of-three ceiling |

This is unplanned but load-bearing evidence: the per-draw `torch.Generator` seeding in
`draw_all` (each draw keyed to `question_seed(item.seed_index) + s`) makes the whole run
re-derivable from `SEED` alone, on MPS, across processes. It also confirms the single PASS is not
a fluke of one process's state. Run 1's partial log is preserved outside the repo at
`scratchpad/ladder_partial_run1.log`.

## Deviations

**1. Provenance hardening landed before the run (`bc182af`), outside the plan's task list.**
Pre-run review found that `provenance.git_sha()` is `git rev-parse HEAD` and nothing more, captured
once at report-write time. That proved less than it read: it never inspects the working tree, and
Python imports the driver into memory before the first forward pass, so an end-only SHA could name
a commit that is not the code that ran. Because `assert_ladder_report_not_clobbered` makes this run
un-re-runnable, weak provenance would attach to the result permanently. Added, scoped to
`run_full_ladder()` only (`phase14_recall.py`, shared with Phases 17/18, untouched):

- `capture_run_provenance()` — runs BEFORE the model load, ABORTS on a dirty tree
- `assert_sha_unchanged()` — re-checks after the last forward pass, before the report write; pure
  over its two arguments so the divergence path is testable without mutating git
- `RUN_OWN_ARTIFACTS` — excludes only this run's two declared outputs, because 16-07 launches via a
  redirect that creates the log before Python starts; a check counting it would abort every run at
  second zero. No code path is excluded.

Both failure paths OBSERVED: the dirty-tree abort fired live naming both modified files, and the
divergence test failed `DID NOT RAISE <class 'SystemExit'>` against a deliberately broken guard,
restored byte-identical (sha256 verified). In production both SHAs recorded as `bc182af`, asserted
equal.

**2. Run 1 died at rung 5 after 50.3 min. Cause NOT identified.** Investigated systematically;
these hypotheses were falsified with evidence:

| hypothesis | verdict | evidence |
|---|---|---|
| jetsam / OOM | falsified | zero `jetsam`/`memorystatus` entries, 2h window |
| Python crash | falsified | no traceback in 104 KB of log; last line is a normal per-question result |
| leak inside the run | falsified | `@torch.no_grad()` on `generate()`, `generation/core.py:24` |
| Bash `timeout: 600000` | falsified | would have fired at 10 min, not 50.3 |
| macOS system sleep | falsified | `Claude` holds `NoIdleSleepAssertion` 25h+; `cloudd` active through the window; no sleep event |

An intermediate claim that sleep WAS the cause was made and then retracted — it rested on a
20-second correlation with a `coreaudiod` assertion release, without confirming the mechanism.
The most consistent remaining explanation is the harness task lifecycle: run 1 was launched as a
tracked background task with **no** `nohup`/`setsid`/`disown`, so it was a direct child of the
launcher's shell. No harness-side log is accessible to prove it. Recorded as unresolved.

**3. `.gitignore` + `AGENTS.md` committed (`fc7651f`) before the run**, because the plan requires a
clean tree for the provenance SHA and both were pre-existing untracked/modified tooling files.

## Operational practice for Phases 17 and 18

Phase 17 and 18 both contain long real-weights runs with the same exposure. Two rules, learned here
at the cost of 50 minutes:

1. **Launch detached and VERIFY it.** `nohup <cmd> > log 2>&1 &` then `disown`; confirm with
   `ps -o ppid= -p <pid>` returning **1**. `setsid` does not exist on macOS — naming it in a plan
   is not applying it. Run 1's death is consistent with being a tracked child of the launcher.
2. **Wrap in `caffeinate -ims`.** Run 1 happened to survive 50 min because audio playback held a
   sleep assertion; that is not a control anyone should depend on. `pmset -g` on this machine shows
   `sleep 1`.

Third, a constraint created by this plan's own hardening and not previously written down:
**the repository is commit-frozen for the duration of any long run.** `assert_sha_unchanged` aborts
before the report is written if HEAD moved, so committing anything mid-run destroys the run at its
last step. Land commits before launching, or after the report exists.

## Verification

- `results/phase16_ladder_report.md` exists, carries `## Verdict`, and
  `assert_ladder_report_not_clobbered()` now FIRES against it (verified) — a second run cannot
  overwrite the recorded verdict
- exactly 1 PASS cell in the table, matching the `span_2` branch
- every rate carries a denominator and a bound; every zero cell carries `rule_of_three`
- `grep -nE '\b0(\.0+)?%'` over the report returns nothing — no bare zero percent
- `results/phase14_recall_report.md` byte-unchanged
- full suite: **469 passed, 1 skipped** (pre-run; no source changed during the run)

## Self-Check: PASSED
