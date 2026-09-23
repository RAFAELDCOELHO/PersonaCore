---
phase: 20-pre-registration-the-three-condition-gate
plan: 12
subsystem: pre-registration-correction
tags: [gate-06, gate-02, sc3-amendment, threat-register, watched-red, re-run, transcription, d-34, d-37]

# Dependency graph
requires:
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 08
    provides: "scripts/phase20_gate_coverage.py — coverage_verdict (the governing computation), corrected_point_verdict (the governing route), _prove_retention_floor (the retention choke point). Re-exercised here, not assumed"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 09
    provides: ".planning/REQUIREMENTS.md's D-36 GATE-02 amendment and the eight AST-resolved traceability notes — preserved intact; this plan writes only the GATE-06 row, the GATE-02 residual paragraph and the GATE-06 bullet"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 10
    provides: "results/phase20_gate_coverage_correction.{md,json} — governs / supersedes / proof, read in-process and asserted by this plan's verify blocks"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 11
    provides: "tests/test_phase20_correction.py — the guard. Re-run here, and its four watched-RED breaks RE-APPLIED rather than transcribed"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 05
    provides: "20-05-PLAN.md / 20-05-SUMMARY.md — the committed source for the transcribed rows T-20-26..T-20-30"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 06
    provides: "20-06-PLAN.md / 20-06-SUMMARY.md — the committed source for the transcribed rows T-20-36..T-20-38"
provides:
  - ".planning/REQUIREMENTS.md — GATE-06 discharged [x] with the reproduction detail preserved in the past tense; GATE-02's RESIDUAL-OPEN replaced by a closed statement"
  - ".planning/ROADMAP.md — SC3's dated D-34/D-37 supersession blockquote, 40 insertions and 0 deletions"
  - "20-SECURITY.md — status verified, threats_open 0, 66 threats substantiated by the file's own rows, 9 watched-RED rows, R-20-05/06/07 logged"
  - "a re-measured T-20-21 watched-RED result that DIVERGES from 20-11's record, published rather than smoothed"
affects: [phase-21, phase-23, phase-25]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A closing plan RE-RUNS the guards and RE-APPLIES the watched-RED breaks in its own process; aggregating a prior SUMMARY's observations is how a gate goes green over evidence nobody checked"
    - "A break's recorded result is scoped to the file state it was taken against — the same break against a later, larger file produces a different count, and the difference is a finding about breadth, not a discrepancy to reconcile away"
    - "An inherited count gap is closed by TRANSCRIBING the absent rows from the committed register that carries them, not by disclosing the gap — a disclosure leaves the IDs as phantom coverage for the next audit"
    - "An amendment states the direction of its own movement against the outcome ordering, and the direction claim is machine-checked (assert DEMOTED present, assert TIGHTER absent) rather than trusted to prose review"
    - "A closure preserves the finding it closes, in the past tense — a register that erases its findings teaches the next audit nothing"

key-files:
  created:
    - .planning/phases/20-pre-registration-the-three-condition-gate/20-12-SUMMARY.md
  modified:
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/phases/20-pre-registration-the-three-condition-gate/20-SECURITY.md
    - .planning/STATE.md

key-decisions:
  - "The four Watched-RED breaks were RE-APPLIED in this process, not copied from 20-11-SUMMARY.md — and one diverged: the T-20-21 coverage-statistic break reddens FOUR tests against the complete 11-test file (`4 failed, 7 passed`) where 20-11 recorded `2 failed, 3 passed` from its five-test Task-1 state. Published beside the table. A transcribed row would have carried a number that no longer describes the guard"
  - "The 46-vs-38 count gap is closed by TRANSCRIPTION from the committed 20-05/20-06 registers, not by a disclosure sentence — eight IDs counted in a total but carried by no row are phantom coverage that resurfaces in the next audit (T-20-62). Total now 66, reconciled to this file's own rows"
  - "The SC3 amendment does NOT claim to be TIGHTER, correcting the plan's own earlier draft: on FAIL < INCONCLUSIVE < PASS both reproduced directions move toward a MORE favourable verdict, so 'in both directions' would be an over-claim inside an anti-over-claim amendment. The tightening comes solely from the third case's DEMOTED PASS"
  - "The Security Audit Trail row is dated 2026-08-21 with totals 66/66/0, not the plan's hardcoded 2026-08-20 and 65/65/0 — the same stale-date correction 20-10 made, plus T-20-66 which this plan declares in its own threat_model"
  - "gsd-sdk state/roadmap/requirements mutation verbs NOT called; REQUIREMENTS.md hand-edited so the verb could not rewrite the rows 20-09 filled or the D-36 amendment it added"

requirements-completed: [GATE-06, GATE-02]

# Metrics
duration: 32min
completed: 2026-08-21
---

# Phase 20 Plan 12: Closing the Books Summary

**GATE-06 and GATE-02's residual are discharged, ROADMAP SC3 carries a dated supersession without a
word of its original text moving, and 20-SECURITY.md is at `threats_open: 0` with all 66 threats
carried as rows this file actually holds — every one of those flips made against guards re-run and
watched-RED breaks re-applied in this process, one of which came back different from the record and
is published that way.**

## Performance

- **Duration:** ~32 min
- **Started:** 2026-08-21T15:58Z
- **Completed:** 2026-08-21T16:30Z
- **Tasks:** 2 of 2
- **Files modified:** 4 (plus this SUMMARY)

## The re-run — done first, before any edit

Nothing below was flipped on the strength of a plan or a SUMMARY. Both tasks ran their verify block
before editing, and the following was observed in this process:

| Check | Observed |
|---|---|
| `.venv/bin/python -m pytest tests/test_phase20_correction.py tests/test_phase20_prereg.py -q` | **`29 passed in 2.66s`** — zero `skipped`, zero `xfail` |
| `git diff --exit-code -- scripts/mitigation_gate.py scripts/erasure_gate.py` | **exit 0** — both frozen files byte-identical to their pinned commits |
| `results/phase20_gate_coverage_correction.json` | `supersedes` = `scripts/mitigation_gate.py:798-812`, `proof` = `tests/test_phase20_correction.py`, `governs` naming `coverage_verdict` + `corrected_point_verdict` |
| `.venv/bin/python -m pytest -q` | **`874 passed, 1 skipped in 240.06s`** — the stated baseline exactly, zero regressions |
| `git diff --exit-code -- results/ scripts/` after all four breaks | **exit 0**; `shasum -a 256` on both touched files equal to their pre-break values |

### The four watched-RED breaks, re-applied rather than transcribed

`20-11-SUMMARY.md` publishes these four observations precisely so this plan would not have to take
its word for them. It was told not to, and it did not. Each break was applied here, its output
observed, and the file restored byte-identically.

| # | Threat | Break applied here | Observed here |
|---|---|---|---|
| 1 | T-20-21 | `coverage_verdict`'s extraction statistic flipped from `wilson_upper_bound(k, n)` to `k / n` | **Both direction tests failed.** (i) `AssertionError: the corrected route returns 'INCONCLUSIVE' where the frozen block returns 'INCONCLUSIVE'. A would-be PASS stays DEMOTED … 2 clearing, 0 failing` / `assert 'INCONCLUSIVE' == 'PASS'`. (ii) `AssertionError: the corrected route returns 'FAIL' on a sweep where ZERO points clear X = 0.04535522866494124 (bounds (0.0699987834827904, 0.16574570864872762))` / `assert 'FAIL' == 'INCONCLUSIVE'`. Whole file: **`4 failed, 7 passed`** |
| 2 | T-20-48 | `scripts/_scratch_bypass_probe.py` calling `mitigation_gate.mitigation_point_verdict(...)` — the `ast.Attribute` form | Census fired: `AssertionError: 1 call site(s) reach a v4.0 verdict through the frozen pin directly … ['scripts/_scratch_bypass_probe.py:7']` / `assert [...] == []`. **Positive control run:** the same test returned `1 passed` the instant the scratch file was removed |
| 3 | T-20-19 | the distinct-seed `_prove` deleted from `_prove_retention_floor` (8 lines) | **`Failed: DID NOT RAISE <class 'SystemExit'>`** at `tests/test_phase20_correction.py:777` |
| 4 | T-20-51 | `results/phase20_retention_floor.json`'s `cap` edited at the 16th significant digit (`…4783` → `…4793`) | WR-02 fired: `AssertionError: the artifact publishes cap 3.908503237988479 but retention_cap on its own published floor returns 3.9085032379884783`. `1 failed, 10 passed` |

**Break 1 came back different from the record, and that is the point of re-running.** `20-11`
recorded `2 failed, 3 passed`; here it is `4 failed, 7 passed`. The cause is not a discrepancy to
reconcile away: `20-11` took that break during its Task 1, when `tests/test_phase20_correction.py`
held five tests. Against the complete 11-test file the same break additionally reddens
`test_every_published_number_re_derives_from_the_modules` and the positive control inside
`test_the_retention_floor_tripwire_is_the_only_route_to_a_verdict`. The load-bearing claim is
unchanged and strengthened — **both direction tests still fail, with the same assertion text** — and
the guard is *broader* than recorded, not narrower. Had this row been transcribed, `20-SECURITY.md`
would today publish a count that no longer describes its own guard. The divergence is written beside
the Watched-RED table in the register, not only here.

**Two of `20-11`'s measurements were independently re-confirmed.** `3.9085032379884782 ==
3.9085032379884783` is `True` — the two decimal strings name the same IEEE double — so the `cap`
break genuinely has to be taken at the 16th significant digit to exist at all; an edit at the last
printed digit is not a tampering path the guard misses, because it changes no value a consumer can
read. And the T-20-48 census matches the `ast.Attribute` form: the scratch caller was written as
`mitigation_gate.mitigation_point_verdict(...)`, exactly the shape a bare-name matcher misses.

## Accomplishments

### Task 1 — GATE-06, GATE-02's residual, and ROADMAP SC3 (`868dc34`)

**`.planning/REQUIREMENTS.md` — GATE-06 `[ ]` → `[x]`**, and its traceability row replaced. The old
note was a DEFERRAL ("awaiting the Phase 20 gap-closure phase"), which is now false, so it was
replaced rather than appended to — but the reproduction detail is preserved **in the past tense**,
because that detail is the evidence of what was corrected. The new row states, in order: the
mechanism shipped at `20-04` and was defective on both axes (CR-01: raw rates against a Wilson-space
ceiling; WR-09: no `sweep_heldout_recalls` in the 21-kwarg signature); both reproduced directions
with their fixtures NAMED, plus the third case no prior report contains
(`FIXTURE_CLEARING_POINT` + `(3/104, 11/104)` → `PASS` off a truncated axis); that
`scripts/mitigation_gate.py` was **not** edited and is byte-identical; the discharge
(`coverage_verdict` decides each axis on that axis's own statistic and both Y legs;
`corrected_point_verdict` has no `sweep_extraction_rates`, so raw-rate space is unreachable and a raw
rate handed to the count parameter is refused by name); the record
(`results/phase20_gate_coverage_correction.json` with `governs` / `supersedes`, plus the dated
continuation `.md`); the guard (`tests/test_phase20_correction.py`, both directions plus the AST
census); and D-37's bound direction **with its cost** — Wilson upper on the X ceiling, raw rates on
the Y floors, because a Wilson lower bound on a floor would decide coverage on a statistic condition
(b) does not read. The Y legs therefore inherit condition (b)'s own lack of a confidence bound;
recorded, and deliberately not fixed, because fixing it would move a pre-registered threshold after
seeing the data it governs.

**GATE-02's residual.** `RESIDUAL — OPEN, bound to the GATE-06 gap-closure phase` replaced by a
closed statement naming `_prove_retention_floor`'s four `_prove` calls — three mirroring
`extraction_ceiling`'s at `mitigation_gate.py:417` / `:425` / `:436`, plus a fourth refusing
`V20_RETENTION_NOISE_FLOOR` by identity — the **choke-point** property (called first in
`corrected_point_verdict`, before any compute), and
`test_the_retention_floor_tripwire_is_the_only_route_to_a_verdict`. The row's D-36 cross-reference
added at `20-09` is intact. That row's own sentence — the tripwire "ships as part of the same dated
continuation as GATE-06 items 1 and 2, and all three close together" — is what this task made true.
`- [ ] **RPT-02**` untouched and correctly unchecked.

**`.planning/ROADMAP.md` — SC3.** A dated `Amended by D-34 and D-37 at plan 20-12` blockquote sits
between SC3's original text and SC4, in SC1's shape. **The ROADMAP diff is 40 insertions and 0
deletions** — SC3's every word is byte-identical above it, exactly as SC1 preserves its own
`4.029000`, and SC1's `Amended by D-06` blockquote occurs exactly once and is unchanged. The body
carries what was wrong (CR-01 + WR-09), what governs now (`coverage_verdict` the computation,
`corrected_point_verdict` the route, and that a verdict read through
`mitigation_gate.mitigation_point_verdict` directly does not govern), the record and the guard by
path, and that the pin was not edited.

**The honesty clause is where this amendment differs from SC1's, and the plan was right to insist on
it.** An earlier draft would have described the two reproduced directions as movement "in both
directions". On the favourability ordering `FAIL < INCONCLUSIVE < PASS`, direction (i)
`INCONCLUSIVE → PASS` and direction (ii) `FAIL → INCONCLUSIVE` **both increase favourability** — so
that phrasing would have published a small over-claim inside the very amendment written to prevent
one. The block instead reads *"Not uniformly tighter — both reproduced directions move toward a MORE
favourable verdict; the tightening is supplied by the third, previously unreported case, where
`FIXTURE_CLEARING_POINT` under `(3/104, 11/104)` is DEMOTED from `PASS` to `INCONCLUSIVE`. The
justification is criterion-matching, not conservatism."* The word `TIGHTER` appears nowhere in the
block, and the verify asserts that absence alongside the presence of `DEMOTED`,
`FIXTURE_CLEARING_POINT` and `criterion-match` — so the corrected claim is machine-checked rather
than trusted to prose review (T-20-66).

### Task 2 — the security gate (`6033c85`)

`status: verified`, `threats_open: 0`, `Gate status: BLOCKED` gone, both Sign-Off boxes checked.

**T-20-21 and T-20-19 moved out of `### Open`** into a dedicated closed sub-table, each keeping its
original reproduction detail in the past tense under a *"What was wrong, preserved"* lead, and each
naming `tests/test_phase20_correction.py` as the guard that watches it plus the Watched-RED row that
watched it fail. `INCOMPLETE — threat REALIZED` and `DISCHARGED AS STATED, RESIDUAL REMAINS` are
gone; the findings they described are not.

**The eight inherited rows transcribed, not disclosed.** `T-20-26`…`T-20-30` and `T-20-36`…`T-20-38`
were inside the published `46` and enumerated by the inclusive ranges `T-20-25 … T-20-31` and
`T-20-33 … T-20-39`, but had never been written into this file as individual rows. Each was copied
from the committed `20-05-PLAN.md` / `20-05-SUMMARY.md` or `20-06-PLAN.md` / `20-06-SUMMARY.md` and
**cites its source in its own row text**. No memory, no reconstruction. Eight IDs counted in a total
but carried by no row are phantom coverage that resurfaces in the next audit — the exact defect
`T-20-62` names — and the mitigation text was committed one directory over, so transcription cost
nothing and fabricated nothing.

**Twenty new threats registered as rows**, grouped by declaring plan: `20-08` (T-20-48, T-20-50,
T-20-53, T-20-54), `20-09` (T-20-52, T-20-55, T-20-56, T-20-63), `20-10` (T-20-47, T-20-49, T-20-51,
T-20-57, T-20-58, T-20-64), `20-11` (T-20-59, T-20-65) and `20-12` (T-20-60, T-20-61, T-20-62,
T-20-66). That is `T-20-47` through `T-20-66`.

**The total, with its arithmetic published beside it:** `66 threats. **66 closed, 0 open.**` —
`38` previously named `+ 8` transcribed `+ 20` new. Every one of the 66 is now an actual row, so the
published total is substantiated by the file's own rows rather than inherited from a prior audit, and
the 46-vs-38 discrepancy is gone rather than disclosed. The verify counts `len(set(re.findall(...)))
== 66` — the file names every threat it counts, and no more.

**Watched-RED table extended to exactly nine rows** — the original five plus one per break actually
run, with the T-20-21 divergence published in a paragraph beneath the table. No row exists for a
break that was not run; the positive-control observation for T-20-48 is recorded in its row.

**R-20-05 (T-20-54), R-20-06 (T-20-56) and R-20-07 (T-20-58)** logged in the Accepted Risks Log with
rationales and dates. No `R-` entry was written for any `mitigate` disposition. The
"T-20-21 and T-20-19 are NOT accepted risks" paragraph was rewritten in the past tense: they were
never accepted, and are closed here on the opposite basis — a mitigation that exists and was watched
failing.

**Blocking Remediation kept as the historical record** of what was required, with a fourth
`Resolution` column naming what discharged each item (1 and 2 by `coverage_verdict` at `20-08` with
the tripwires at `20-11`; 3 by `_prove_retention_floor` at `20-08` with its refusal suite at
`20-11`). The section opener changed from "Phase advancement is blocked" to a closed statement.

## Verification

| Check | Result |
|---|---|
| Task 1 verify (guards, frozen-file diff, JSON fields, GATE-06/GATE-02 ROW scoping, SC3 placement + direction claim) | `OK` |
| Task 2 verify (frontmatter, no unchecked boxes, 20 new rows, 8 transcribed rows each citing its source, totals, exactly 66 IDs, both closures named, 9 watched-RED rows, R-20-05/06/07) | `OK — 66 threat IDs named as rows, 9 watched-RED rows, totals reconciled` |
| `.venv/bin/python -m pytest -q` | `874 passed, 1 skipped in 240.06s` — the stated baseline exactly |
| `git diff --exit-code -- results/ scripts/` | exit 0 after all four watched-RED breaks were restored |

Both verify blocks were run BEFORE their task's edits, as the plan requires, and re-run after.

## Deviations from Plan

### 1. [Rule 1 — stale plan text] The Security Audit Trail row is dated `2026-08-21` with totals `66 / 66 / 0`, not `2026-08-20` with `65 / 65 / 0`

- **Found during:** Task 2, before writing.
- **Issue:** the plan's action text prescribes "a Security Audit Trail row dated `2026-08-20` with the new totals (65 / 65 / 0)". Both halves are stale. The gap-closure plans were authored 2026-08-20 and executed 2026-08-21 — the same divergence `20-10` recorded and corrected for the continuation heading, with its `dated_note` inside the artifact. And `65` contradicts the plan's own `<action>` and `<verify>`, which say `66 threats` and `len(ids)==66`: the plan's `<success_criteria>` prose was written before `T-20-66` was added to its own `<threat_model>` at review.
- **Fix:** dated `2026-08-21`; totals `66 / 66 / 0`, matching the published total and the arithmetic beside it. A register publishing a total it does not enumerate is precisely the `T-20-62` defect this plan exists to refuse.
- **Files modified:** `20-SECURITY.md`
- **Commit:** `6033c85`

### 2. [Rule 2 — a re-run that disagrees with the record is a finding, not a transcription error] The T-20-21 Watched-RED row publishes `4 failed, 7 passed`, not `20-11`'s `2 failed, 3 passed`

- **Found during:** Task 2's break re-application, before writing.
- **Issue:** the plan says "Copy the observed output from `20-11-SUMMARY.md`". The orchestrator's carry-forward overrode that with "verify them yourself before transcribing", and the verification disagreed with the record: the same break reddens FOUR tests against the complete 11-test file.
- **Fix:** the row publishes what was observed HERE, and a paragraph beneath the table explains the cause — `20-11` took the break at its five-test Task-1 state, so the same break now also reddens `test_every_published_number_re_derives_from_the_modules` and the positive control inside the retention tripwire test. The load-bearing claim is unchanged (both direction tests fail, same assertion text) and the guard is broader than recorded.
- **Why this matters rather than being pedantry:** copying the row would have left `20-SECURITY.md` publishing a count that no longer describes its own guard, inside the table whose entire premise is that the observation was made.
- **Files modified:** `20-SECURITY.md`
- **Commit:** `6033c85`

### 3. [Rule 3 — a probe that selected no test] The T-20-48 break was run twice; the first attempt proved nothing

- **Found during:** Task 2's break re-application.
- **Issue:** the first invocation filtered with `pytest -k census`. The census test is named `test_mitigation_point_verdict_has_no_caller_outside_this_module` — the name `20-11` adopted because the shipped module cites it — which contains no substring `census`. Pytest selected zero tests and reported nothing; read carelessly, that silence would have been mistaken for "the break did not fire".
- **Fix:** re-run with `-k "no_caller_outside"`. The census fired naming `scripts/_scratch_bypass_probe.py:7`, and a positive control was added that `20-11` did not record — the same test returns `1 passed` once the scratch file is removed, so the RED is attributable to the bypassing caller and not to anything else.
- **Recorded rather than hidden** because it is the same defect class as `20-11`'s sub-resolution `cap` edit: a probe that cannot fire is not evidence of a guard's strength.
- **Files modified:** none (probe only; `scripts/_scratch_bypass_probe.py` created and removed, tree clean)
- **Commit:** `6033c85`

Three things worth recording that are *not* deviations:

1. **`gsd-sdk` state / roadmap / requirements mutation verbs were NOT called.** `.planning/STATE.md`,
   `.planning/ROADMAP.md` and `.planning/REQUIREMENTS.md` were hand-edited and every diff reviewed.
   Tenth consecutive session treating those handlers as unsafe in this repo — and the risk was
   highest here, since `requirements.mark-complete` would have rewritten the traceability rows
   `20-09` had just filled and the GATE-02 D-36 amendment it had just added.
2. **`requirements-completed: [GATE-06, GATE-02]` is claimed here and nowhere earlier.** `20-10` and
   `20-11` both deliberately declined it, recording that GATE-06 was `20-12`'s to discharge against a
   re-run. That instruction was honoured: the guards ran first, and the bullet was flipped second.
3. **The frozen files were never touched.** `scripts/mitigation_gate.py` and
   `scripts/erasure_gate.py` are byte-identical throughout; the only files edited under `scripts/`
   or `results/` were the two temporary watched-RED breaks, both restored byte-identically with
   `shasum -a 256` and `git diff --exit-code` confirming.

## Threat Model Outcomes

| Threat ID | Disposition | Outcome |
|---|---|---|
| T-20-21 | mitigate | **CLOSES HERE**, and only after `tests/test_phase20_correction.py` + `tests/test_phase20_prereg.py` were re-run in this process (`29 passed`, zero skips) and the coverage-statistic break was re-applied and watched reddening both direction tests. The closure names `coverage_verdict`, the correction artifact and the tripwire; ROADMAP SC3 — the criterion the threat was realized against — carries a dated amendment pointing at the same three. |
| T-20-19 | mitigate | **CLOSES HERE**, same discipline: the `_prove` deletion re-applied and watched producing `DID NOT RAISE SystemExit`. The closure names `_prove_retention_floor` and its refusal suite, and GATE-02's traceability row is rewritten from RESIDUAL-OPEN to a discharge naming the same function and guard. |
| T-20-60 | mitigate | Both tasks ran the guards BEFORE editing. Every acceptance criterion asserts the observed state of the file rather than the intent of the edit; each of `T-20-47`…`T-20-66` is checked BY NAME as a register row rather than trusted to the published total; the Watched-RED table is COUNTED at exactly nine; and the four breaks were re-applied rather than transcribed — which is what caught the divergence in Deviation 2. |
| T-20-61 | mitigate | The reproduction detail for both closed threats is preserved in the past tense and the verify asserts each closed row names its watching guard. ROADMAP SC3's original text is byte-identical above its amendment (40 insertions, 0 deletions), and the GATE-02 bullet's D-36 amendment survives untouched (`assert 'Amended by D-36' in t`). |
| T-20-62 | mitigate | R-20-05, R-20-06 and R-20-07 are present in the Accepted Risks Log with rationales and dates, asserted by the verify; no `R-` entry exists for a `mitigate`. The same reasoning forced the eight inherited rows to be transcribed rather than disclosed, and the file's ID census is asserted at exactly 66 so the published total cannot exceed what the file enumerates. |
| T-20-66 | mitigate | MEASURED across all three cases; the SC3 block says "Not uniformly tighter", attributes the tightening solely to the third demoted case, and names criterion-matching as the justification. The verify asserts `DEMOTED`, `FIXTURE_CLEARING_POINT` and `criterion-match` present and `TIGHTER` absent — so the corrected claim is machine-checked, not trusted to prose review. |

## Threat Flags

None. Four planning-record markdown files. No code, no network surface, no endpoints, no schema, no
trust-boundary change. The only executable actions were read-only test runs and two temporary
watched-RED edits, both restored byte-identically and verified by `shasum -a 256` plus
`git diff --exit-code`.

## Known Stubs

None. Every claim in every edited record points at a committed artifact and a watched guard.

## Notes for Future Plans

- **This plan updates the RECORDS; it does not re-verify the phase.** Re-run `/gsd:verify-phase 20`
  and `/gsd:secure-phase 20` — the orchestrator's own audit is what confirms them. SC3's gap should
  no longer re-file: a re-verifier reading SC3 now meets the amendment before reaching SC4.
- **A Watched-RED row is scoped to the file state its break was taken against.** Deviation 2 is the
  general lesson: if a later plan re-applies one of these breaks against a file that has since grown,
  expect a different count and treat the difference as a fact about the guard's breadth.
- **`measured_residue_at_n_104` remains deliberately un-re-derived** (`20-11` decision, T-20-53). The
  short-circuit's OUTPUT is asserted instead. That is a recorded limitation carried forward, not an
  open hole, and this plan's threat accounting does not claim otherwise.
- **The Y legs inherit condition (b)'s lack of a confidence bound** (D-37), recorded in the GATE-06
  row and in the SC3 amendment. Phase 23 sets Z's sweep width and is where sweep coverage stops being
  hypothetical; that inheritance should be read there, not rediscovered.

## Self-Check: PASSED

- `.planning/REQUIREMENTS.md` — FOUND; `- [x] **GATE-06**` present, `- [ ] **RPT-02**` present,
  `RESIDUAL — OPEN` absent, `Amended by D-36` present
- `.planning/ROADMAP.md` — FOUND; `Amended by D-34` present between SC3 and SC4, `Amended by D-06`
  count exactly 1, ROADMAP diff 40 insertions / 0 deletions
- `.planning/phases/20-pre-registration-the-three-condition-gate/20-SECURITY.md` — FOUND;
  `status: verified`, `threats_open: 0`, `66 threats`, 66 distinct IDs, 9 watched-RED rows
- `.planning/phases/20-pre-registration-the-three-condition-gate/20-12-SUMMARY.md` — FOUND
- commit `868dc34` — FOUND
- commit `6033c85` — FOUND
- `scripts/mitigation_gate.py`, `scripts/erasure_gate.py`, `scripts/phase20_gate_coverage.py`,
  `results/phase20_retention_floor.json`, `results/phase20_gate_coverage_correction.{md,json}` — all
  byte-identical to pre-plan HEAD `9a73aab`; `git diff --exit-code -- results/ scripts/` exit 0
