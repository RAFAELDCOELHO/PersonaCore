---
phase: 33-admission-and-relearning-on-admitted-points
plan: 03
requirements-completed: [ADMIT-01, ADMIT-02]  # hand-ticked in Task 2; RELRN-06..09 stay unticked (named limitation, MOOT); ACTRL-01 stays unticked (D-15)
---

# Phase 33 Plan 03: Phase 34 ledger rows staged; requirement state recorded by hand

The admission record `results/phase33_admission.json` (commit `f48b738`) reads **MOOT**, so this
plan closes Phase 33 on the MOOT branch. It stages every carried item as a Phase 34 ledger row,
ticks ADMIT-01/02, and records RELRN-06..09 as a named limitation. No code changed. This plan was
executed inline by the orchestrator, not by a subagent.

## Re-measured evidence (raw output, 2026-09-28)

```
$ git log --format=%h --diff-filter=A -- results/phase30_calibration.json
4339f2b
$ git log --all --format=%h --diff-filter=D -- results/phase30_calibration.json
(no output)
$ add_commit census: results/phase32_frontier.json ["calibration"]["add_commit"] +
  every results/phase32_point_*.json ["provenance"]["calibration"]["add_commit"]
count 8 distinct ['4339f2b2bc29ab0765a821b5d47b617cd6092f24']
(12 point files on disk; 7 carry the key)
$ git log -1 --format=%h -- scripts/phase32_points.py scripts/phase32_frontier.py
fd76e0d        # precedes the 32-REVIEW commit c932b0e: the findings are still open
$ git log --format=%h -1 -- results/phase33_admission.json
f48b738
```

Published-field check (occurrences, frontier / point records): `past_line_ruling` 0/7,
`stop_line_seconds` 0/0, `add_commit` 1/7, `module_sha256` 1/7. The frontier's own-control gaps are
positive: `points.advr_n8_ratio0p000000.verdict.control_gap` = 0.13432465700344487 and advr_n64 =
0.18415204911242888, read from `results/phase32_frontier.json` rather than typed from research.

## Phase 34 ledger rows

These rows are staged here for Phase 34 to import; the ledger file belongs to Phase 34. The Phase 32
frontier's authoritative pin is `provenance.git_sha` (fd76e0d, which covers the full tree). That
point is cited by reference from 32-VERIFICATION.md:13 and is not restated as a fix.

| id | source | disposition | reason | target | prerequisite / evidence |
|----|--------|-------------|--------|--------|-------------------------|
| `P31-WR-01` | 31-REVIEW.md WR-01 (`scripts/phase31_probe.py`) | RE-DEFERRED | The MOOT branch writes no relearning artifact, so the unreachable crash-recovery path is never exercised | the milestone that builds the advr relearning legs' body | Before the first relearning artifact is written, decide where those artifacts live relative to `refuse_if_dirty`. Phase 33 wrote no output-location code (D-10) |
| `P32-CR-01` | 32-REVIEW.md CR-01 (`scripts/phase32_points.py`) | RE-DEFERRED | Accepted under AR-32-02: not reached in the committed sweep | the milestone that reuses `phase32_points` | AR-32-02/03 (32-SECURITY.md:107-110) require a fix with dated pin continuations before any reuse. Phase 33 enforces this with `tests/test_phase33_admission.py::test_no_phase33_module_imports_phase32_points` (D-11, D-12) |
| `P32-WR-01` | 32-REVIEW.md WR-01 (`scripts/phase32_points.py`) | RE-DEFERRED | Accepted under AR-32-02: `PINNED_MODULES` gap not reached in the committed sweep | the milestone that reuses `phase32_points` | same as P32-CR-01 (AR-32-02/03; D-12 census) |
| `P32-WR-02` | 32-REVIEW.md WR-02 (`scripts/phase32_frontier.py`) | BY-REFERENCE | The frontier's `module_sha256` is incomplete, but `provenance.git_sha` pins the whole tree and no verdict or number is affected | none | Cites 32-VERIFICATION.md:13 ("git_sha is the authoritative pin") by reference. No code fix and no continuation (D-14) |
| `P32-WR-03` | 32-REVIEW.md WR-03 (`tests/test_phase30_points.py`) | CLOSED | Fixed during Phase 32 | none | `325aaf0` (RED), `f7c1a83` (fix) |
| `P32-WR-04` | 32-REVIEW.md WR-04 (`scripts/phase32_frontier.py`, `scripts/phase32_points.py`) | RE-DEFERRED | Latent: it fires only on a non-positive own-control gap, and the committed gaps are positive (n8 0.1343…, n64 0.1842…, read from the frontier) | the milestone that reuses `phase32_frontier` | Bind the gap from the frontier and never type it (D-14) |
| `P32-WR-05` | 32-REVIEW.md WR-05 (`scripts/phase32_points.py`) | RE-DEFERRED | Accepted under AR-32-02: the recovery commit path never ran (session sha = `head_at_write` = `training.git_sha` in every record) | the milestone that reuses `phase32_points` | same as P32-CR-01 (AR-32-02/03; D-12 census) |
| `P32-IN-01` | 32-REVIEW.md IN-01 (`scripts/phase32_points.py`) | RE-DEFERRED | Touches no published frontier field (`past_line_ruling` is null in the 7 point records, absent from the frontier) | the milestone that reuses `phase32_points` | 32-REVIEW.md IN-01 |
| `P32-IN-02` | 32-REVIEW.md IN-02 (`scripts/phase32_points.py`) | RE-DEFERRED | Touches no published field (`stop_line_seconds`: 0 occurrences) | the milestone that reuses `phase32_points` | 32-REVIEW.md IN-02 |
| `P32-IN-03` | 32-REVIEW.md IN-03 (`scripts/phase32_frontier.py`, `scripts/phase32_points.py`) | DATED-CONTINUATION (2026-09-28) | The published `calibration.add_commit` was measured correct: one add (`4339f2b`), zero deletes, and all 8 published values equal (1 frontier + 7 point records) | code fix: the milestone that reuses `phase32_frontier`/`phase32_points` | Raw evidence above: the `--diff-filter=A` output `4339f2b`, the `--diff-filter=D` output (none), and the census `count 8 distinct ['4339f2b…']`. No pinned file changed (D-16) |
| `P32-IN-04` | 32-REVIEW.md IN-04 (`artifacts/com.personacore.phase32.sweep.plist`, `scripts/phase32_points.py`) | RE-DEFERRED | Touches no published field (heartbeat file under `data/`) | the milestone that reuses `phase32_points` | 32-REVIEW.md IN-04 |
| `P32-IN-05` | 32-REVIEW.md IN-05 (`scripts/phase32_frontier.py`) | RE-DEFERRED | Touches no published field (dirty-check cwd) | the milestone that reuses `phase32_frontier` | 32-REVIEW.md IN-05 |
| `P32-IN-06` | 32-REVIEW.md IN-06 (`tests/test_phase32_frontier.py`) | RE-DEFERRED | Dead test branches; no published field | the milestone that reuses `phase32_frontier` | 32-REVIEW.md IN-06 |
| `P32-IN-07` | 32-REVIEW.md IN-07 (`scripts/phase32_points.py`) | RE-DEFERRED | PREREG-03 records carry no provenance, so nothing is published | the milestone that reuses `phase32_points` | 32-REVIEW.md IN-07 |
| `ACTRL-01` | REQUIREMENTS.md ACTRL-01 | NAMED-LIMITATION (partial exercise) | Exercised on real data: the recall floors and `control_gap` came from each leg's own advr control (32-07-SUMMARY.md:80, by reference). Not exercised: the relearning Z baseline, because admission read MOOT and no relearning leg ran | Phase 34 ledger | Phase 33 does not take the requirement and it stays unticked (D-15) |

Deferred idea (not implemented): **advr relearning apparatus**, meaning the bodies of the
calibrate / curve / gate / structural-proof legs. On the MOOT branch only their refusal surface
exists.

## Task 2: planning files edited by hand

- Snapshots of REQUIREMENTS/ROADMAP/STATE were taken in `/private/tmp/claude-501/-Users-juliorcoelho-PersonaCore/phase33/snap/` before any edit. Diffs against those snapshots:
  - REQUIREMENTS: 18 changed lines (the ADMIT-01/02 ticks and traceability rows, the RELRN-06..09 cells, the ACTRL-01 cell).
  - ROADMAP: 6 changed lines (the three 33-0N plan ticks).
  - STATE: the frontmatter `stopped_at` and `last_updated`, plus the Current Position `Phase`/`Plan`/`Status`/`Last activity` lines. The line count is unchanged at 1721, and the frontmatter `status` and `progress` block are untouched.
- Checks:
  - `grep -c "NOT SATISFIED — named limitation: admission read MOOT"` = 4.
  - ADMIT ticks = 2; unticked RELRN-06..09 = 4; ACTRL-01 unticked.
  - `scripts/phase28_report.py check` exit 0.
  - The 9 guard files report 180 passed.
- Zero gsd-sdk mutation handlers.
- Obsidian vault entry: saved under the new heading "Fase 33 — executada, 3/3 planos" in `01-Projects/PersonaCore — memória em pesos.md`.
