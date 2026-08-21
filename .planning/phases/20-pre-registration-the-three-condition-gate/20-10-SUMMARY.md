---
phase: 20-pre-registration-the-three-condition-gate
plan: 10
subsystem: pre-registration-correction
tags: [gate-06, dated-continuation, governs, supersedes, append-only, provenance, stat-02]

# Dependency graph
requires:
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 08
    provides: "scripts/phase20_gate_coverage.py — coverage_verdict, wilson_lower_bound, _prove_retention_floor, corrected_point_verdict, COVERAGE_STATISTIC_BY_AXIS, SUPERSEDED_GATE06_BLOCK, SUPERSEDED_SWEEP_SENTINEL. Every published number is produced by calling it or the pin it calls"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 07
    provides: "results/phase20_retention_floor.json — retention_ppl_noise_floor 0.008681618994239138, read from the file rather than retyped, and the source of retention_provenance.measured_floor"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 05
    provides: "scripts/mitigation_gate.py (CLOSED pin) — mitigation_point_verdict, extraction_ceiling, retention_cap, F_Y and the three committed FIXTURE_* dicts every published verdict is measured against"
  - phase: 19-selective-erasure
    plan: 09
    provides: "results/phase19_calibration_correction.{md,json} + scripts/_addendum.py — the precedent shape this artifact mirrors, and the ONE append-only writer with its required pending/recorded marker pair"
provides:
  - "results/phase20_gate_coverage_correction.md — the D-24 dated continuation: the frozen pin's literal reading published unedited, with the correction appended beside it in a SECOND commit"
  - "results/phase20_gate_coverage_correction.json — governs / supersedes / defects / evidence / retention_provenance / heldout_coverage / bound_direction / recorded_not_corrected, every float computed by calling the modules"
  - "the marker triple 20-11 must re-declare verbatim: PENDING, RECORDED and the ADDENDUM_HEADING dated 2026-08-21"
  - "a pre-append REVISION in git history (4e4d5ef) carrying the placeholder — the object 20-11's additivity guard derives from git log rather than from a pinned hash"
affects: [20-11, 20-12, phase-23, phase-25]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A dated continuation is dated the day it was WRITTEN — a stale date copied from the plan puts a false date on the one artifact whose whole purpose is honest provenance"
    - "The two-commit rule is asserted on `git log` for the revision and `git show <rev>:<path>` for the blob, never `git ls-files` — a merely-staged file is TRACKED and passes ls-files on exactly the state the rule forbids (MEASURED)"
    - "STAT-02 as a LINE-SCOPED rule: any line carrying a `%` figure must carry an explicit k/n denominator on that same line, not merely 'no zero percentages'"
    - "A bound published for a fabricated RATE states the count it was priced at, so a reader sees exactly what the bound is a bound over"
    - "Both verdicts published for every case — the pin's and the correction's — including the row that demotes a PASS, which is against the amender's own interest"

key-files:
  created:
    - results/phase20_gate_coverage_correction.md
    - results/phase20_gate_coverage_correction.json
    - .planning/phases/20-pre-registration-the-three-condition-gate/20-10-SUMMARY.md
  modified:
    - .planning/STATE.md
    - .planning/ROADMAP.md

key-decisions:
  - "DATED 2026-08-21, not the plan's hardcoded 2026-08-20 — the plans were authored on the 20th and executed on the 21st; a continuation whose heading date is not its writing date is a false provenance claim on a provenance artifact. Applied to the heading, the JSON's `dated`, and the plan's own verify assertion"
  - "wilson_lower_bound is published for the Y points at the NEAREST WHOLE COUNT at n = 104 with that count printed beside every bound — the fixture Y points are fabricated RATES carrying no count, so a bound cannot be priced from them directly. Reported alongside the deciding raw rate, never instead of it"
  - "`governs` is one string carrying both halves (the computation `coverage_verdict` and the route `corrected_point_verdict`), mirroring Phase 19's single-string `governs` rather than inventing a nested shape"
  - "requirements.mark-complete NOT run for `requirements: [GATE-06, GATE-02]` — neither is discharged here. GATE-06 belongs to 20-12 and closes only after 20-11's tripwire is watched RED-then-GREEN; GATE-02 was already [x] and amended at 20-09"

patterns-established:
  - "Generate the artifact with a THROWAWAY script that imports the modules and calls them — the script is not committed, the discipline is that no float in the artifact was typed"
  - "Simulate the downstream guard before shipping: 20-11's additivity walk was run against the published bytes here, where a failure is a re-commit rather than a history rewrite two waves later"

requirements-completed: []

# Metrics
duration: 16min
completed: 2026-08-21
---

# Phase 20 Plan 10: The D-24 Dated Continuation Summary

**The GATE-06 correction is now a citable artifact: `governs` names `coverage_verdict` as the computation and `corrected_point_verdict` as the route, `supersedes` names `scripts/mitigation_gate.py:798-812` exactly, and both live beside the frozen pin's own reading — published unedited, in two commits, with the append provably additive.**

## Performance

- **Duration:** ~16 min
- **Started:** 2026-08-21T15:15Z
- **Completed:** 2026-08-21T15:31Z
- **Tasks:** 2 of 2, in TWO commits (the second was not optional)
- **Files created:** 2 (plus this SUMMARY)

## Accomplishments

### Task 1 — the continuation document, committed carrying the placeholder (`4e4d5ef`)

`results/phase20_gate_coverage_correction.md` (117 lines at this commit). Committed BEFORE any
append, so `20-11`'s additivity guard — which derives the pre-append revision from `git log` rather
than pinning a hash — has a revision to find.

**The measured result, re-derived by calling the code.** At `n = 104` questions with
`extraction_noise_floor = 0.01` and a `never-taught` provenance over two distinct seeds:

| quantity | derivation | value |
|---|---|---|
| X | `mitigation_gate.extraction_ceiling(nontarget_successes=0, nontarget_questions=104, ...)` | `0.04535522866494124` |
| Y_taught | `F_Y` `0.7` x `control_taught_recall` `0.50` | `0.35` |
| Y_heldout | `F_Y` `0.7` x `control_heldout_recall` `0.35` | `0.24499999999999997` |

The swept points, each with BOTH statistics beside it — the one condition (a) is decided on and the
one the frozen block reads — so the shift the defect introduces is visible rather than asserted:

| swept point | `wilson_upper_bound(k, 104)` | raw `k / 104` | under (a) | under the frozen block |
|---|---|---|---|---|
| 1 / 104 | `0.04195034874465613` | `0.009615384615384616` | clears X | clears X |
| 3 / 104 | `0.0699987834827904` | `0.028846153846153848` | **fails X** | **clears X** |
| 11 / 104 | `0.16574570864872762` | `0.10576923076923077` | fails X | fails X |

The middle row is the whole defect: at 3 / 104 the two statistics disagree about the same point
against the same ceiling.

**`## Verdict` publishes what the FROZEN PIN computes, unedited, with the fixture NAMED in every
row** — because the verification report and `20-SECURITY.md` both describe direction (ii) as
"returns a decisive FAIL" without naming one, and the fixture is exactly what decides the outcome:

| # | fixture | `sweep_extraction_rates` | pin verdict | GATE-06 reason |
|---|---|---|---|---|
| (i) | `FIXTURE_CLEARING_POINT` | `(1/104, 3/104)` | `INCONCLUSIVE` | yes — 1 |
| (ii) | `FIXTURE_DESTROYED_MODEL` | `(3/104, 11/104)` | `FAIL` | no — 0 |
| (ii') | `FIXTURE_TRUNCATED_SWEEP` | `(3/104, 11/104)` | `FAIL` | no — 0 |
| (iii) | `FIXTURE_CLEARING_POINT` | `(3/104, 11/104)` | `PASS` | no — 0 |

Row (iii) is in no prior report and is the sharpest of the four: the pin publishes a `PASS` off an
extraction axis on which, under condition (a)'s own statistic, no swept point clears the criterion.
Its limit is stated in the same breath — it does NOT contradict the verifier's narrower claim, which
was scoped to self-consistent inputs where the judged point is itself one of the swept points.

The Verdict section also records the held-out leg as the finding it is (no `sweep_heldout_recalls`
parameter exists in the 21-keyword signature, so there is no verdict to publish, only the absence of
an axis) and the retention leg's two caps: `retention_cap(0.06893) = 4.029` accepted with no refusal
at all, against the governing `3.9085032379884783`, with `4.029` named as the LOOSER of the two.

`## The coverage correction` follows, its entire body the placeholder — outside the Verdict section,
so replacing it cannot move the verdict body, and bounding the Verdict section so
`_verdict.recorded_verdict` returns a real body rather than `None` on both sides of the append.

### Task 2 — the machine-readable half, and the one append (`2a32394`)

`results/phase20_gate_coverage_correction.json` generated by a throwaway script that imports
`phase20_gate_coverage`, `mitigation_gate` and `erasure_gate` and calls them. **No float is typed**;
`measured_floor` and its cap are read from `results/phase20_retention_floor.json`. Keys, sorted, with
a trailing newline:

| key | what it carries |
|---|---|
| `governs` | `sweep coverage (GATE-06)` + the computation (`coverage_verdict`) and the route (`corrected_point_verdict`) |
| `supersedes` | `scripts/mitigation_gate.py:798-812`, read from `cov.SUPERSEDED_GATE06_BLOCK` |
| `governing_module` / `governing_entry_point` | `scripts/phase20_gate_coverage.py` / `corrected_point_verdict` |
| `coverage_statistic_by_axis` | serialised from `COVERAGE_STATISTIC_BY_AXIS`, three `(axis, statistic, criterion_site)` entries |
| `bound_direction` | D-37's criterion-matching resolution, its cost, the reported-never-deciding register, the priced Y lower bounds, and the `successes == 0` short-circuit with the measured `1.734723475976807e-18` residue at n = 104 |
| `defects` | `CR-01`, `WR-09`, `T-20-19`, `WR-08` — one measured sentence each, naming file and line range |
| `evidence` | `n` 104, `X`, `y_taught`, `y_heldout`, `swept_points`, and the three direction objects |
| `heldout_coverage` | `(0.30, 0.28)` against `Y_heldout`, the truncation sentence, and `pin_has_the_parameter: false` |
| `retention_provenance` | T-20-19's whole evidentiary record — two floors, two caps, the ratio, and `enforced_by` naming `_prove_retention_floor` and its four checks |
| `recorded_not_corrected` | `IN-09`, `IN-06`, `WR-03`, `WR-04`, `WR-05`, `WR-10`, each with its reason AND a `stale_when` |
| `dated` / `dated_note` | `2026-08-21` and why (see Deviations) |

The three verdict pairs, all measured through the route rather than transcribed:

| | fixture | pin | corrected |
|---|---|---|---|
| `direction_i` | `FIXTURE_CLEARING_POINT` | `INCONCLUSIVE` | **`PASS`** |
| `direction_ii` | `FIXTURE_DESTROYED_MODEL` | `FAIL` | **`INCONCLUSIVE`** |
| `direction_ii_on_clearing_fixture` | `FIXTURE_CLEARING_POINT` | `PASS` | **`INCONCLUSIVE`** |

`retention_provenance`, asserted rather than narrated (`governing_cap < borrowed_cap`):

| field | value |
|---|---|
| `borrowed_floor` | `0.06893` (`erasure_gate.V20_RETENTION_NOISE_FLOOR`) |
| `measured_floor` | `0.008681618994239138` (read from `results/phase20_retention_floor.json`) |
| `borrowed_cap` | `4.029` |
| `governing_cap` | `3.9085032379884783` |
| `ratio` | `7.939763314393305` |

**The append.** `scripts/_addendum.py::append_addendum(path, addendum, pending=..., recorded=...)`
run ONCE, both keywords supplied as the signature requires. Its three checks all passed on the
produced bytes: exactly one placeholder, an unchanged `## Verdict` section, and the original prefix
plus the addendum. The addendum opens by stating the file is frozen and this is a continuation not
an edit; carries the pin-versus-correction verdict table with the fixture named; carries D-37's
resolution with its cost read aloud; carries the retention leg in its own paragraph naming
`_prove_retention_floor` as the choke point that refuses the borrowed floor by identity; and closes
with **Which computation governs a v4.0 verdict**, naming `corrected_point_verdict` as the sanctioned
route, `sweep_extraction_rates` as absent from it, `tests/test_phase20_correction.py` as what goes
RED on a consumer of the superseded path, and the JSON's `governs` field as the machine-readable half
of the same statement.

**The marker triple `20-11` must re-declare verbatim:**

```
PENDING          = "**Phase 20 GATE-06 coverage correction: not yet recorded.**"
RECORDED         = "**Phase 20 GATE-06 coverage correction: recorded in the dated continuation at the end of this file.**"
ADDENDUM_HEADING = "## Addendum — 2026-08-21 — the coverage statistic, the held-out leg, and the retention floor's missing tripwire"
```

## Verification

Both plan-supplied automated checks exited `OK`. The Task 2 check was run in full only AFTER the
second commit, so its `len(revs) >= 2` assertion is a measurement and not an assumption.

| Check | Result |
|---|---|
| Task 1 verify (`pending x1`, verdict section present, revision carries the placeholder) | `OK — pending x1 in the committed blob, verdict section present, 1 revision(s)` |
| Task 2 verify (13 JSON keys, 4 defects, `governing_cap < borrowed_cap`, 3 verdict pairs, RECORDED x1, PENDING x0, addendum heading, STAT-02, 2 revisions, oldest carries the placeholder) | `OK — 2 revisions, oldest carries the placeholder` |
| `20-11`'s additivity guard, SIMULATED against the published bytes | GREEN — prefix byte-identical, exactly one changed line `(PENDING -> RECORDED)`, heading inside the appended region, `recorded_verdict` equal on both sides |
| `git diff --exit-code -- scripts/mitigation_gate.py scripts/erasure_gate.py` | exit 0, after both commits |
| `.venv/bin/python -m pytest tests/test_phase20_prereg.py -q` | `18 passed in 2.02s` — the two new `results/phase20_*` files are matched by the artifact globs and their first-adds land after all nine pin commits, so the ancestry guard stays green |
| `ruff check .` / `ruff format --check .` | `All checks passed!` / `175 files already formatted` |
| `.venv/bin/python -m pytest -q` | `863 passed, 1 skipped in 214.54s` — the baseline exactly |

STAT-02 was enforced as the plan's LINE-SCOPED rule (any line with a `%` figure must carry a `k/n`
denominator on that same line) and satisfied the simplest way that cannot regress: the document
carries no `%` figure at all. Every rate is written as `k / 104`.

## Task Commits

| Task | Commit | Files |
|---|---|---|
| 1 — the continuation, carrying the placeholder | `4e4d5ef` | `results/phase20_gate_coverage_correction.md` |
| 2 — the JSON and the one append | `2a32394` | `results/phase20_gate_coverage_correction.json`, `results/phase20_gate_coverage_correction.md` |

## Deviations from Plan

### 1. [Rule 1 — stale date] The continuation is dated 2026-08-21, not the plan's 2026-08-20

- **Found during:** before Task 1 — the plan hardcodes `2026-08-20` in three places: the `key_links`
  pattern (`20-10-PLAN.md:34`), the prescribed addendum heading (`:67`), and Task 2's verify
  assertion (`:360`).
- **Issue:** the gap-closure plans were authored on 2026-08-20; execution is on 2026-08-21 (`date -u`
  and every commit timestamp in this plan agree, as do `20-09-SUMMARY.md` and `20-08-SUMMARY.md`,
  both `completed: 2026-08-21`). The date on a DATED CONTINUATION is load-bearing, not decoration:
  it is the day the correction was measured and recorded. Writing `2026-08-20` on an artifact
  actually written on `2026-08-21` puts a false date on the one artifact whose entire purpose is
  honest provenance — and the Phase 19 precedent dates its addendum (`2026-08-18`) to the day the
  calibration was scored, not to the day its plan was written.
- **Fix:** `2026-08-21` written, applied consistently across all three surfaces — the `## Addendum`
  heading, the JSON's `dated` field (with a `dated_note` recording the divergence inside the artifact
  itself, so a reader meets it there and not only here), and the plan's Task 2 verify assertion,
  which was run as `assert 'Addendum — 2026-08-21' in t`.
- **Not silently either way:** the stale date was not copied, and the change was not made quietly.
  It is recorded here, in `STATE.md`'s Decisions, in the ROADMAP line for this plan, and in the
  artifact's own `dated_note`.
- **Downstream:** `20-11` declares `ADDENDUM_HEADING` "with the exact strings from `20-10`"
  (`20-11-PLAN.md:133-135`) and hardcodes no date of its own, so it must take the heading from the
  COMMITTED file. The verbatim triple is published above for exactly that purpose.
- **Files modified:** `results/phase20_gate_coverage_correction.md`,
  `results/phase20_gate_coverage_correction.json`
- **Commits:** `4e4d5ef`, `2a32394`

### 2. [Rule 2 — a bound must state what it is a bound over] The published Y lower bounds name the count they were priced at

- **Found during:** Task 2. The plan requires "the computed lower bounds for the published Y points
  so the reader meets both numbers". The Y sweep points are fabricated RATES (`0.45`, `0.20`, `0.30`)
  and carry no success count, so `wilson_lower_bound(successes, n)` cannot be called on them
  directly — and `0.45 x 104 = 46.800000000000004` is not a whole number.
- **Fix:** each bound is priced at the NEAREST WHOLE COUNT at `n = 104` and that count is published
  in the same table row (`0.45 -> 47/104`, `0.20 -> 21/104`, `0.30 -> 31/104`), with the artifact
  stating in both halves that the rates are fabricated and that the bound is a report about the
  criterion's precision rather than an input to any decision. Inventing a count silently would have
  been the defect this phase exists to refuse.
- **Files modified:** both artifacts
- **Commit:** `2a32394`

Two things worth recording that are *not* deviations:

1. **`gsd-sdk` state/roadmap mutation verbs were NOT called.** `.planning/STATE.md` and
   `.planning/ROADMAP.md` were hand-edited and the diff reviewed. Eighth consecutive session
   treating those handlers as unsafe in this repo.
2. **`requirements.mark-complete` was deliberately NOT run** for the plan's
   `requirements: [GATE-06, GATE-02]`. Neither is discharged here: GATE-06 belongs to `20-12` and
   closes only after `20-11`'s tripwire has been watched RED-then-GREEN, and GATE-02 was already
   `[x]` and amended at `20-09`.

## Threat Model Outcomes

| Threat ID | Disposition | Outcome |
|---|---|---|
| T-20-21 | mitigate | CARRIED FORWARD, still OPEN. The correction is now published and CITABLE — `governs` names the computation and the route, `supersedes` names the exact frozen block. Closure requires `20-11`'s tripwire. |
| T-20-19 | mitigate | CARRIED FORWARD, still OPEN. `retention_provenance` publishes the whole evidentiary record and the verify ASSERTS `governing_cap < borrowed_cap` rather than narrating it; the addendum states the same in prose and names `_prove_retention_floor` as the choke point. Publication is not closure: `20-12` aggregates, `20-11` watches the refusals fire. |
| T-20-49 | mitigate | `append_addendum`'s three checks all ran on the produced bytes and passed. `_verdict.recorded_verdict` asserted NON-`None` on BOTH sides — before the append in Task 1 and after it in Task 2 — so the unchanged-verdict guard is not vacuous. |
| T-20-47 | mitigate | Refuted in the artifact itself: both verdicts published for every case, and the `direction_ii_on_clearing_fixture` row DEMOTES a `PASS`, which is against the amender's interest and ships anyway. The correction never moves a verdict toward `PASS` off a truncated axis. |
| T-20-51 | mitigate | The JSON was generated by a throwaway script that imports the three modules and calls them; `measured_floor` and its cap are read from `results/phase20_retention_floor.json`. No float typed. `20-11` re-derives them. |
| T-20-57 | mitigate | Every `recorded_not_corrected` entry carries a `stale_when` field saying what would make its description false. |
| T-20-58 | accept | Asserted rather than reasoned about: `tests/test_phase20_prereg.py` is `18 passed` after both commits. |
| T-20-64 | mitigate | Both tasks asserted on the objects `20-11` consumes — `git log --format=%H -- <path>` for the revision list and `git show <oldest>:<path>` for the blob. `git ls-files` was never used. Task 1: 1 revision carrying the placeholder. Task 2: 2 revisions, oldest still carrying it. `20-11`'s guard was additionally SIMULATED green against the published bytes. |

## Threat Flags

None. Two data artifacts under `results/`. No network surface, no endpoints, no schema at a trust
boundary, no executable code shipped.

## Known Stubs

None. `tests/test_phase20_correction.py` is named as `proof` in the JSON and cited in the addendum
before it exists — that is the plan's own construction (`20-11` writes it, one wave later) and is the
same forward citation `scripts/phase20_gate_coverage.py`'s docstrings already carry, not a stub in
this plan's output.

## Notes for Future Plans

- **`20-11` must take `ADDENDUM_HEADING` from the COMMITTED file, not from `20-10-PLAN.md`.** The
  plan's heading string is dated `2026-08-20` and the committed heading is dated `2026-08-21`. All
  three verbatim strings are published in this SUMMARY's Task 2 section.
- **The pre-append revision `20-11` will find is `4e4d5ef`** — but it must still be DERIVED from
  `git log` and never pinned, exactly as `tests/test_phase19_correction.py:121-133` does. The walk
  was simulated green today.
- **`20-11`'s corrected-call helper defaults must stay `sweep_heldout_recalls=(0.30, 0.20)` and
  `retention_floor_provenance={"regime": "adapter", "seeds": (1337, 2024)}`** (`20-11-PLAN.md:139-142`).
  Every `evidence` verdict in the JSON was measured with exactly those, so a different default makes
  the tripwire disagree with the artifact it is meant to protect.
- **`heldout_coverage` uses `(0.30, 0.28)`**, the ONE case that deviates from that default, and it
  overrides `sweep_heldout_recalls` — so `20-11`'s helper must use the merge form the plan already
  prescribes, or that case is unreachable.
- **`20-12` should not discharge GATE-06 on the strength of this plan.** The correction is published
  and citable; nothing has watched the tripwire go red. `20-SECURITY.md` stays `threats_open: 2`
  until `20-11`.

## Self-Check: PASSED

- `results/phase20_gate_coverage_correction.md` — FOUND (237 lines after the append, `wc -l`)
- `results/phase20_gate_coverage_correction.json` — FOUND (parses, 16 top-level keys — the 13 the
  plan's verify asserts, plus `dated`, `dated_note` and `superseded_sweep_sentinel`)
- `.planning/phases/20-pre-registration-the-three-condition-gate/20-10-SUMMARY.md` — FOUND
- commit `4e4d5ef` — FOUND
- commit `2a32394` — FOUND
- `scripts/mitigation_gate.py`, `scripts/erasure_gate.py` — byte-identical to `2898d69` (pre-plan HEAD)
