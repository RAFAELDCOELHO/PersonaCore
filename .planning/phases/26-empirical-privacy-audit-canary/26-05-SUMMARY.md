---
phase: 26-empirical-privacy-audit-canary
plan: 05
subsystem: privacy-audit
tags: [canary, emit, ancestry-guard, launchagent, pmset, pytest, d-13, d-19]

# Dependency graph
requires:
  - phase: 26-04
    provides: the approved unattended 16-point MPS run, note §1–§7, the loaded canary + watcher agents
  - phase: 26-01
    provides: scripts/phase26_prereg.py at one commit (e6a8851) and the ancestry guard the artifact must descend from
  - phase: 25-19
    provides: results/phase25_frontier.json at one commit (4030d0e), the digest the sibling pins
provides:
  - results/phase26_canary.json — the sibling verdict artifact, emitted once, committed by the operator (8652c15)
  - note §8 (§8.1–§8.9) — the close, the machine put back, the final gate
  - tests in their PRESENT state — the both-state tests and the ancestry guard over two tracked artifacts
affects: [28-report, empirical-privacy-audit, phase-26-verification]

# Tech tracking
tech-stack:
  added: []
  patterns: [one --emit and no hand assembly, operator-only git write, close block from quoted outputs, full suite before the note edit that records it]

key-files:
  created:
    - results/phase26_canary.json
    - .planning/phases/26-empirical-privacy-audit-canary/26-05-SUMMARY.md
  modified:
    - results/phase26_operational_note.md
    - tests/test_phase26_canary.py
    - .planning/STATE.md
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "Branch A taken: 17 sidecars existed, --emit ran exactly once; the artifact was left untracked for the operator and committed by the operator alone (8652c15)."
  - "The Phase-25 watcher was booted out with the canary because note §5.3 shows 26-04 loaded both; the four other Phase-25 agents found loaded (runs = 0) were quoted and left as found — outside the plan's scope, inert by their committed plists, named for the operator."
  - "The full suite ran BEFORE the note edit that records it, so the clean-tree probes measured the fully-tracked tree rather than this task's own edit."
  - "Zero gsd-sdk mutation handlers: STATE/ROADMAP/REQUIREMENTS hand-edited with asserted replacements and diffed against a snapshot; CANARY-01/02 ticked by hand against named artifact fields and guard tests (the 25-20 precedent)."

patterns-established:
  - "Close block = quoted bootout + launchctl list + launchctl print runs/exit per agent + pmset assertions by pid + caffeinate ps with parents + git log of both artifacts + the ancestry arithmetic."
  - "A red suite caused by the task's own required intermediate state is recorded verbatim with its cause, then re-measured on the committed tree — never smoothed and never 'fixed' by committing what the plan says a human must commit."

requirements-completed: [CANARY-01, CANARY-02]

# Metrics
duration: ~4h20m wall across three sessions (Task 1 ~2026-09-13T14:30Z → Task 3 close 2026-09-13T18:50Z), including the operator checkpoint
completed: 2026-09-13
---

# Phase 26 Plan 05: The Close Summary

**The canary audit closed on Branch A: one `--emit` produced `results/phase26_canary.json` — 15 CONSISTENT / 0 BROKEN / 0 INCONCLUSIVE, reachable claims 4/15, auditor_ceiling 2.7859, power gate PASSED, exclusions 0/56 — pinned both ways to the frontier; the operator committed it by hand (8652c15); the canary and watcher LaunchAgents were booted out; `make test` is 2792 passed / 4 skipped / 0 failed on the fully-tracked tree.**

## Performance

- **Duration:** ~4 h 20 min wall across three sessions (Task 1, the operator's checkpoint, Task 3)
- **Started:** 2026-09-13 (Task 1, `HEAD = c4a5511`; `--emit` at 2026-09-13T17:39:11Z per `emitted_utc`)
- **Completed:** 2026-09-13T18:50Z (bootout at 2026-09-13T18:14:52Z; note commit 5477519)
- **Tasks:** 3 (2 auto + 1 human-action)
- **Files modified:** 7 (1 artifact created, note, test, STATE, ROADMAP, REQUIREMENTS, this SUMMARY)

## Accomplishments

- **Task 1 (Branch A):** the precondition read found 17 sidecars (OFF + 16), the agent exited 0 on its own, the log's tail at σ = 80. `env -u PERSONACORE_SWEEP_ACTIVE .venv/bin/python scripts/phase26_canary.py --emit` ran ONCE: `{'BROKEN': 0, 'CONSISTENT': 15, 'INCONCLUSIVE': 0}`, reachable claims 4/15 (σ = 24, 32, 50, 80), `auditor_ceiling = 2.7858978325772576`, power gate PASSED (control ε_lower 2.7859 vs threshold 0.6340), exclusions 0/56 and 0/8, `frontier_sha256 = 1f182b40…` (22,311,714 bytes), all 16 `adapter_sha256` equal to the frontier's. Artifact sha256 `d2a71e2d…`, 165,830 bytes, left `??` for the operator. §8.1–§8.7 written; `"## 8. The close"` appended to `_NOTE_REQUIRED_BLOCKS`. Commit 868ff47.
- **Task 2 (operator):** `results/phase26_canary.json` committed by hand at 8652c15 (author Rafael, 2026-09-13T15:12:01-03:00); `git log --diff-filter=A` shows exactly that one commit; the artifact's bytes at close still hash to `d2a71e2d…`. The operator's post-commit run: `43 passed in 3.30s`.
- **Task 3:** `launchctl bootout` of `com.personacore.phase26.canary` AND `com.personacore.phase25.watch` (both loaded by 26-04, note §5.3); `launchctl list | grep phase26` empty; no driver process; no `-dims` caffeinate; `pmset -g` unchanged at `sleep 1 / disksleep 10 / powernap 1`; the ancestry guard's arithmetic `checked == len(prereg_commits) * len(tracked): 2 == 1 * 2: True`; §7 → nothing pending; §8.8–§8.9 written. Commit 5477519.
- **The wall-clock:** kickstart `2026-09-11T16:23:57Z` → `done` heartbeat `2026-09-12T23:07:28Z` = 30 h 43 min 31 s against §3's ≈ 25 h (§8.2: thirteen points inside the 3.4–4.3 s/question band; σ = 50 at 7402 s and σ = 80 at 19390 s outside it, cause not measured, not claimed).

## Task Commits

1. **Task 1: Branch A — `--emit` once, artifact proven, note §8.1–§8.7 + test** - `868ff47` (docs)
2. **Task 2: Operator commits the artifact by hand (human-action)** - `8652c15` (results; author Rafael — the driver's git surface is read-only)
3. **Task 3: Put the machine back and record the close** - `5477519` (docs)

**Plan metadata:** the tracking commit that carries this SUMMARY + STATE + ROADMAP + REQUIREMENTS (SHA in the orchestrator's return)

## Files Created/Modified

- `results/phase26_canary.json` - the sibling verdict artifact (operator-committed, 8652c15): 16 `audited_point_keys`, 15 verdicts with `reasons`, `frontier_sha256`, `power_gate`, `exclusions`, `auditor_ceiling`, `prereg_module_sha256`, `emitted_git_sha c4a5511`.
- `results/phase26_operational_note.md` - §7 pending register → nothing pending (26-04's entry kept behind SUPERSEDED); §8.1–§8.7 (Task 1: the precondition, the wall-clock, the one `--emit`, the read-back, the present-state tests, the untouched frontier, the full suite with its 4-residue finding); §8.8–§8.9 (Task 3: the machine put back, the final gate).
- `tests/test_phase26_canary.py` - `"## 8. The close"` appended to `_NOTE_REQUIRED_BLOCKS` (the seventh parametrization — the 42 → 43 delta).
- `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md` - hand-edited tracking (section below).

## The test counts, and the deltas

| Run | Tree | Result |
|-----|------|--------|
| Phase 25 close, CI (ubuntu, Actions `34406246073`) | Phase 25 HEAD | 2691 passed / 62 skipped (2753 collected) |
| Task 1 `make test` (note §8.7) | Task 1's uncommitted note/test edits + the `??` artifact | **4 failed** / 2787 passed / 4 skipped (2795 collected) |
| Task 2, operator, `pytest test_phase26_prereg + test_phase26_canary` | after 8652c15 | 43 passed in 3.30s |
| Task 3 `make test` (note §8.9) | fully-tracked tree, `HEAD = 8652c15` | **2792 passed / 4 skipped / 0 failed**, 83 warnings, 1297.92s (2796 collected), exit 0 |
| Task 3 `pytest test_phase26_prereg + test_phase26_canary + test_phase25_close -x` | same | 69 passed in 3.95s (43 + 26) |
| Task 3 `pytest tests/test_phase25_close.py` | same | 26 passed in 0.39s |
| Task 3, the four residue tests by name | same | 4 passed in 99.90s |

- **Over Task 1's run:** the four residue tests now PASS, rerun by name — `tests/test_phase23_resume.py::test_production_resume_epsilon_bit_identical`, `tests/test_phase25_frontier.py::test_a_perturbed_per_point_count_breaks_the_aggregate`, `tests/test_phase25_grid.py::test_the_from_import_variant_is_invisible_to_the_register_walk`, `tests/test_phase25_probe2.py::test_a_planted_bit_identity_assertion_here_would_fire`. They are clean-tree probes over `results/` (first two) and `tests/` (last two); §8.7 recorded them as a measured consequence of Task 1's own REQUIRED state (the artifact had to be left `??` for the operator), not smoothed. `passed` rose by 5 = those four + the one new parametrization; `skipped` unchanged at 4; collected 2795 → 2796.
- **Over the Phase-25 CI close:** +43 collected (2753 → 2796), 0 failed on both. The skip registers differ by venue by design (M3 flag-unset 4 under §6.6's D-44 continuation; ubuntu's derived 62), so the comparison is on collected and failed, not on skipped, and the +43 is stated as measured, not decomposed (26-04 also touched `tests/test_phase25_venue.py`).
- **42 → 43 (Task 1 → Task 2):** Task 1 ran the two Phase-26 files BEFORE appending `"## 8. The close"` to `_NOTE_REQUIRED_BLOCKS` (§8.5's last sentence says so); the operator's run after the commit collected the seventh parametrization `test_the_operational_note_carries_every_required_block["## 8. The close"]`. Verified by reading `tests/test_phase26_canary.py:657-675` — the tuple has seven entries and the test is parametrized over it. The ancestry guard is one unparametrized test whose `checked` count grew 1 → 2; its test count did not change.

## Decisions Made

- **Branch A, one `--emit`.** 17 sidecars existed; `emit` was called once; `--force` never used; nothing assembled by hand (T-26-03, T-26-07).
- **Boot out the watcher as well as the canary.** Note §5.3 shows 26-04 ran `launchctl load` on both `com.personacore.phase26.canary.plist` and `com.personacore.phase25.watch.plist`; the plan says to boot the watcher out only if 26-04 loaded it — it did, so both were booted out and §8.8(b) says so. The watcher had `runs = 46`, `last exit code = 0`.
- **Leave the four other Phase-25 agents as found, and name them.** `sweep`, `recall`, `rehearsal`, `n64floor` are loaded with `runs = 0` / `(never exited)`. Not loaded by this phase (§5.4's listing 18 s after kickstart showed only watch + canary), booted out by Phase 25 §13.1 on 2026-09-09, re-loaded by something between 2026-09-11T16:24Z and the close (no reboot — uptime 96 days). Inert by their committed plists (`RunAtLoad false` / `KeepAlive false`, all four verified in `artifacts/`). Outside the plan's scope; recorded in §8.8(b) for the operator rather than booted out silently. T-26-04 holds regardless: no `phase26` agent is loaded and sidecars are reused by hash, never re-scored.
- **Run the full suite before the note edit that records it.** A note edit dirties `results/`, which is exactly what two of the clean-tree probes refuse; so `make test` ran first on the fully-tracked tree and §8.9 quotes that run and says so.
- **Zero `gsd-sdk` mutation handlers.** The seven-session corruption hazard; the orchestrator's uncommitted STATE.md repair (frontmatter dates, `Plan:` line, `Last activity:` line) was built on, not discarded. Snapshot diffs: STATE 19 lines, ROADMAP 4, REQUIREMENTS 8 — all intended, nothing to repair.
- **CANARY-01 / CANARY-02 ticked by hand** against named artifact fields and guard tests, the Phase-25 (25-20) precedent — with the plain sentence that the audit had no accusing power at any noised point (0/8 members answered), so CONSISTENT means "not contradicted", not "confirmed".

## Deviations from Plan

None in code or artifacts — the plan executed as written on Branch A. Two things the plan's expected outputs did not anticipate, handled inside its own instructions and quoted:

1. `pmset -g assertions` showed, besides the harness's own `-i -t 300` the plan predicted, the unrelated `polymarket-bot` keep-awake (`15665 caffeinate -s -i -w 7584`) that note §2 named before launch and Phase 25 §7b/§13.1b restored on purpose. Attributed by pid, not touched.
2. `launchctl list | grep personacore` was expected to be empty or the watcher only; it shows four inert Phase-25 agents — see Decisions. Recorded, not acted on.

**Total deviations:** 0 auto-fixed. **Impact on plan:** none.

## Issues Encountered

- **Task 1's `make test` was red by construction (§8.7):** 4 failed / 2787 passed / 4 skipped. All four are clean-tree probes tripped by Task 1's own uncommitted note/test edits and by the artifact the task is REQUIRED to leave untracked for the operator. Recorded verbatim rather than smoothed; cleared by Task 2's commit and re-measured green in Task 3 (§8.9). Not a code defect.
- **Two σ points ran far outside the timing band** (σ = 50: 7402 s; σ = 80: 19390 s, 3.3× the band), pushing the run to 30 h 43 min against §3's ≈ 25 h and 2 h 13 min past §6.7's pessimistic bound. Cause not measured in this phase and not claimed; the sidecars' `scoring_seconds` are the record (§8.2).
- **Note §8.5/§8.7 say "27 Phase-25 close tests"; this session measured `tests/test_phase25_close.py` at 26 passed.** Left as written in Task 1's text (a committed record); the 26 is quoted here and in §8.9 as measured. No test was added or removed between the two runs; the 27 is Task 1's miscount, not a change in the file.

## Planning-file edits (hand, diffed against a snapshot)

- `STATE.md`: frontmatter `stopped_at` → Phase 26 wave 5 COMPLETE with the operator's SHA (26-04's entry kept behind SUPERSEDED); `completed_plans` 102 → 103; `Plan:` line → 5 of 5 ALL COMPLETE; `Last activity:` → the close; six `[Phase 26] 26-05` decisions appended under `### Decisions`; `## Session Continuity` `Last session` / `Stopped at` → the close. The pre-existing `total_plans: 101 < completed_plans` inconsistency is older than this session and was not touched.
- `ROADMAP.md`: 26-05 `[ ]` → `[x]`; progress row `4/5 In Progress | -` → `5/5 Plans complete — verification pending` with the close summary. The phase-level `[ ]` in the milestone list stays for `/gsd:verify-work 26`.
- `REQUIREMENTS.md`: CANARY-01 / CANARY-02 checkboxes ticked; traceability rows filled with the artifact fields, the guard tests and the one-sided reading.

## User Setup Required

None. The operator's one manual step (Task 2) is done.

## Next Phase Readiness

- Phase 26 is ready for `/gsd:verify-work 26`. SC3 holds in the Branch-A form: the verdict travels with the frontier by proven digest link (`frontier_sha256` + 16 `adapter_sha256`, both directions under `test_the_sibling_is_pinned_to_the_frontier_both_ways` in its PRESENT state).
- **For Phase 28 (D-40 continuation):** every ε it quotes from the frontier's 15 noised dp_n8 points carries a CONSISTENT verdict — 11 with the D-13 disclosure `epsilon_upper >= auditor_ceiling: this comparison could not have failed`, 4 reachable (σ = 24, 32, 50, 80). CONSISTENT is one-sided: this instrument can only accuse, and at 0/8 members answered it had nothing to accuse with.
- **For the operator:** four Phase-25 LaunchAgents are loaded and idle (note §8.8(b)); booting them out restores the Phase 25 §13.1 state. Not done here.

---
*Phase: 26-empirical-privacy-audit-canary*
*Completed: 2026-09-13*

## Self-Check: PASSED

Files: results/phase26_canary.json, results/phase26_operational_note.md (§8.8 present), tests/test_phase26_canary.py, this SUMMARY — all found. Commits 868ff47, 8652c15, 5477519 — all found. `launchctl list` empty of phase26.
