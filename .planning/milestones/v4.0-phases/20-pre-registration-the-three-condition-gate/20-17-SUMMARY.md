---
phase: 20-pre-registration-the-three-condition-gate
plan: 17
subsystem: security-register
tags: [pre-registration, security-register, gate-02, gate-06, gap-closure-wave-2, watched-red, d-39, d-41]
requires:
  - "20-13 (the OPEN flip at 72ef455 and the BINDING distinct-id counting method)"
  - "20-14 (the Y-leg value guards and the count-by-type guard — breaks A and B re-applied here)"
  - "20-15 (the magnitude bound, its tolerance pin and the import census — breaks C, D and E re-applied here)"
  - "20-16 (the JSON additivity guard and the addendum ordering assertion — breaks F, F1b and G re-applied here)"
provides:
  - "20-SECURITY.md at status: verified / threats_open: 0, with 84 distinct threat IDs counted from its own tables and ZERO rows at Status open"
  - "T-20-19 re-closed by APPEND against a re-run, its 20-12 and 20-13 spans byte-identical, in a commit distinct from the OPEN flip (D-39)"
  - "18 new six-column rows T-20-67 … T-20-84, each stated against what was actually BUILT rather than what its plan intended"
  - "Eight watched-RED breaks RE-APPLIED and observed in this process, with one divergence from the record published rather than smoothed"
  - "ROADMAP.md waves 12-16 flipped [x] in place with each one-liner rewritten from its own SUMMARY; STATE.md at 17/17 recording D-41"
affects:
  - "/gsd:verify-phase 20 — this is the state the orchestrator's audit now judges; confirmation is that audit, not this plan"
  - "GC-05, GC-07 and GC-08…GC-12 remain OPEN and are named open in the register rather than absorbed by the re-close"
tech-stack:
  added: []
  patterns:
    - "A re-close cites output OBSERVED in the closing process; a SUMMARY is a record of someone else's run and is not evidence"
    - "Expect divergence when re-applying a break, and publish it — the divergence is usually the most informative line"
    - "Preserve the record that stated the closing condition, so a reader can check the condition was met rather than take the closure's word"
    - "Count by the method fixed in writing, then RE-MEASURE with your own command; never inherit a total from a prior audit"
key-files:
  created:
    - ".planning/phases/20-pre-registration-the-three-condition-gate/20-17-SUMMARY.md"
  modified:
    - ".planning/phases/20-pre-registration-the-three-condition-gate/20-SECURITY.md"
    - ".planning/ROADMAP.md"
    - ".planning/STATE.md"
decisions:
  - "The 20-13 `### Open` re-opening record is PRESERVED beneath the `None.` sentence rather than deleted: the closing condition it names is exactly what this re-close had to satisfy, and a reader who cannot see the condition cannot check that it was met. Deleting it would also have left the T-20-19 row's pointer at 'the ### Open PARAGRAPH above' dangling"
  - "The Watched-RED re-run rows use a leading `#` column (A…G) rather than a `| T-20-NN |` row-start, so the eight new rows add zero row-starts — which is why the measured 57 / 53 match the plan's stated expectation exactly instead of drifting to 64"
  - "The full suite was re-run TWICE: the first run was started before the breaks and overlapped them, so it was killed and discarded as contaminated rather than reported"
metrics:
  duration: "~55 min"
  tasks_completed: 2
  commits: 2
  completed: 2026-08-21
---

# Phase 20 Plan 17: Re-close T-20-19 Against a Re-run, and Bring the Record Current Summary

Re-closed `20-SECURITY.md` to `status: verified` / `threats_open: 0` at **84 distinct threat IDs** —
but only after re-running every guard and re-applying **all eight** watched-RED breaks in this
process, one of which **diverged** from its SUMMARY and is published rather than smoothed.

## What Was Built

**Task 1 — `20-SECURITY.md`** (`7ffeee3`, 138 insertions / 12 deletions). Frontmatter, gate-status
paragraph, register header + a dated re-measurement of the counting method, the substantiation
paragraph, `### Open`, the `T-20-19` row (append-only), a new 18-row wave-2 section, eight
Watched-RED re-run rows plus the divergence note, the audit trail and the Sign-Off.

**Task 2 — `ROADMAP.md` + `STATE.md`** (`741f889`, 14 insertions / 14 deletions across both).

## THE CENTRAL DISCIPLINE — Nothing Below Is Transcribed

D-39 requires the re-close to reflect what was genuinely proved. Every figure and every quoted
failure in this document was produced by a command run in **this** process. Where a result differs
from `20-14-SUMMARY.md` / `20-15-SUMMARY.md` / `20-16-SUMMARY.md`, the difference is published.

### Step 1 — the re-runs, before a character of the register was edited

| Command | Observed |
|---|---|
| `.venv/bin/python -m pytest tests/test_phase20_correction.py tests/test_phase20_prereg.py -q` | **`32 passed in 2.13s`** — no `skipped`, no `xfail` |
| `.venv/bin/python -m pytest -q` | **`877 passed, 1 skipped, 83 warnings in 191.72s`** |
| `ruff check . && ruff format --check .` (via `.venv/bin/python -m ruff`) | `All checks passed!` / `176 files already formatted` |
| `git diff --exit-code -- scripts/mitigation_gate.py scripts/erasure_gate.py` | exit **0** |
| `git diff --exit-code -- scripts/ tests/ results/` | exit **0** |
| ancestry guard by REAL node id `test_phase20_prereg_is_frozen_before_every_phase20_result` | **`1 passed in 0.89s`** |
| ancestry guard, plan's `-k phase20_prereg_is_frozen` form | **`1 passed, 17 deselected in 0.88s`** — selection printed, so a silent zero could not pass |

Re-run at the end, **after** every `.planning/` edit: `git diff --exit-code` on both frozen pins and
on `scripts/ tests/ results/` → **0** each; `git status --porcelain` → **empty**;
`.venv/bin/python -m pytest -q` → **`877 passed, 1 skipped, 83 warnings in 190.56s`**.

### Step 2 — eight breaks RE-APPLIED, all OBSERVED RED

Pre-break digests, recorded before any break:

```
962b1a26d5088238ce4eccd8241353efe98e29643c4928534b1052b7af29b5af  scripts/phase20_gate_coverage.py
3cc135444d129b47573e3ba97401c2584f9585032842cfa6c50022111261ae71  tests/test_phase20_correction.py
16dfdc13a68cf6be309c69519b72fe68457aed03253f848d1bdd17e0fb9b32f7  results/phase20_gate_coverage_correction.json
06cc11f10acef9b1ebc55cdcf4e11ce8de74d0a6937b5166615bce358f18dd22  results/phase20_gate_coverage_correction.md
```

| # | Guard | Break | Observed HERE | Restore |
|---|---|---|---|---|
| A | T-20-71 Y value guard | per-element `_prove` loop deleted, both legs (**21 deletions**) | `E Failed: DID NOT RAISE <class 'SystemExit'>` at `tests/test_phase20_correction.py:486` in `test_a_recall_outside_the_unit_interval_cannot_manufacture_y_coverage`, at **case 3** (`# 3. THE FLIP, REFUSED.`). **`1 failed, 13 passed in 0.81s`** | digest `962b1a26…` **equal**, `git diff --exit-code` **0** |
| B | T-20-74 count-by-type | `whole` reverted to `isinstance(k, int) or (isinstance(k, float) and k.is_integer())` | `E Failed: DID NOT RAISE <class 'SystemExit'>` at `:546` in `test_the_modules_own_rate_space_sentinel_cannot_pass_as_counts`, first iteration of the sentinel loop. **`1 failed, 13 passed in 0.59s`** | digest **equal**, `git diff --exit-code` **0** |
| C | T-20-75 magnitude bound | fifth `_prove` neutered (`_prove(` → `_BREAK_1_DELETED = (`) | `E Failed: DID NOT RAISE <class 'SystemExit'>` at `:1191`, reached from `refused(retention_noise_floor=nudged)` at `:1252`, frame carries `overrides = {'retention_noise_floor': 0.06893000000000006}`. **`1 failed, 13 passed in 0.51s`** | digest **equal**, `git diff --exit-code` **0** |
| D | T-20-76 tolerance pin | `_RETENTION_FLOOR_RELATIVE_TOLERANCE` `1e-9` → `0.05` | `E AssertionError: the admissible ceiling 0.009115699943951094 now ADMITS the fabricated fixture floor 0.009. …` / `E assert 0.009115699943951094 < 0.009` at `:1270`, **AND** `E assert 1e-09 == 0.05` at `:967`. **`2 failed, 12 passed in 0.53s`** — **DIVERGES** | digest **equal**, `git diff --exit-code` **0** |
| E | T-20-77 import census | scratch `scripts/_wr07_probe.py`, `from mitigation_gate import mitigation_point_verdict as mpv` | `E AssertionError: 1 call site(s) or import(s) reach a v4.0 verdict … ['scripts/_wr07_probe.py:3 (imported as mpv)']` at `:1440`. **`1 failed in 0.24s`**; positive control **`1 passed`** once removed | probe deleted, `git status --porcelain scripts/` **empty**, `git diff --exit-code -- scripts/` **0** |
| F | T-20-80 JSON additivity | `evidence.X` `…124` → `…125` | `E AssertionError: the published `evidence` was rewritten under cover of an additive write.` / `E {'X': 0.04535522866494125} != {'X': 0.04535522866494124}` at `:1072`. **`2 failed, 12 passed in 0.75s`** | digest `16dfdc13…` **equal**, `git diff --exit-code -- results/` **0** |
| F1b | T-20-80 JSON additivity | `recorded_not_corrected.IN-06.finding` `(:1291-1425)` → `(:1291-1426)` — a leaf NO re-derivation reads | `E AssertionError: the published `recorded_not_corrected` was rewritten under cover of an additive write.` at `:1072`. **`1 failed, 13 passed in 0.50s`** — the additivity guard **ALONE** | digest **equal**, `git diff --exit-code -- results/` **0** |
| G | T-20-79 addendum ordering | one `ADDENDUM_HEADING_SECOND` line spliced at `:118` | `> assert appended.index(ADDENDUM_HEADING_SECOND) > appended.index(ADDENDUM_HEADING)` / `E AssertionError: the second continuation appears BEFORE the first in the appended region.` / `E assert 0 > 111` at `:747`. **`1 failed, 13 passed in 0.48s`** | digest `06cc11f1…` **equal**, `git diff --exit-code -- results/` **0**, `git status --porcelain results/ scripts/ tests/` **empty** |

**The splice point was RE-DERIVED, not taken from `20-16`.** Walking `git log` for the newest blob
still carrying `PENDING`:

```
pre-append revision  : 4e4d5ef
pre-append lines     : 117
RECORDED pointer at  : :117
splice point         : :118   <- FIRST line of the appended region
first ## Addendum at : :119
```

Matches `20-16`'s record exactly.

### Failure attribution, CHECKED rather than assumed

Python stops at the first failure, so a misplaced break produces a row that is not evidence.

- **A** failed at case 3. Cases 1 (the honest `(0.30, 0.28)` finding) and 2 (the
  `not (nan >= y_heldout)` mechanism) **evaluated and passed** first — visible in the traceback —
  which is correct, since neither depends on the deleted guard.
- **G** failed on the **ORDERING** assertion at `:747`, rendered `assert 0 > 111`. It is **NOT**
  `changed == [(PENDING, RECORDED)]` and **NOT** `after[:cut] == before[:cut]`; both sit above it in
  the same body and both evaluated and passed, as did the presence assertion immediately above the
  ordering one. This is the check the executor prompt requires, and it passes.
- **F1b** reddens exactly one test, which is what makes the additivity guard independently
  load-bearing rather than merely co-firing behind the re-derivation guard.

## THE DIVERGENCE — Row D, Published Rather Than Smoothed

`20-15-SUMMARY.md` records the tolerance widening as reddening **one** test. Re-applied here it
reddens **two**:

```
20-15 recorded : 1 failed, 12 passed
20-17 measured : 2 failed, 12 passed
```

The second failure is `test_every_published_number_re_derives_from_the_modules`, failing on
`assert 1e-09 == 0.05` where `0.05 = coverage._RETENTION_FLOOR_RELATIVE_TOLERANCE`.

**The cause is attributable and it is a STRENGTHENING.** `20-16` published
`value_guards.retention_magnitude_bound.relative_tolerance` into
`results/phase20_gate_coverage_correction.json`, and that guard re-derives the tolerance from the
module. A second, independent guard now bites on the same widening — one that did not exist when
`20-15` took its measurement. The guard is broader than recorded, not narrower.

This also independently re-confirms the executor prompt's carried-forward fact 4:
`_RETENTION_FLOOR_RELATIVE_TOLERANCE` measures **`1e-09`**. What `20-15` shipped is a **pin against**
the `0.05` widening, not the widening itself. Any record saying the tolerance is `0.05` is wrong.

**One `20-15` result is NOT re-claimed.** Its BREAK 2a — the suite measured GREEN under the same
widening *before* the pin existed — is not re-runnable, because the pin is committed and that state
no longer exists. Its status as a finding rests on `20-15`'s record plus row D, which shows what the
pin now does. Said in the register rather than quietly folded into row D.

Rows A, B, C, E, F, F1b and G reproduced their recorded results. Only line numbers moved (both files
are unpinned and both grew at `20-15` / `20-16`), and row A's passing count is `13` rather than `12`
because `20-16` added a test function.

## The Register, Counted by the BINDING Method and RE-MEASURED

Never inherited from a prior audit. Measured at base `ca74fbf`, then again after the edit:

```
                              at ca74fbf     after the re-close
distinct T-20-NN in tables        66      ->        84
| T-20-NN | row-start LINES       39      ->        57
distinct ids among row-starts     35      ->        53
register rows at Status open       1      ->         0
```

`84` is the published total and appears in the register header as `84 threats.` All eighteen of
`T-20-67` … `T-20-84` are also their own six-column rows, so the wave-2 addition reconciles under
both readings — but only the distinct count is the total, exactly as `20-13` fixed in writing.

**Why `57` and not `64`.** The eight Watched-RED re-run rows carry a leading `#` column (`A`…`G`), so
they contribute **zero** row-starts. `39 + 18 = 57` and `35 + 18 = 53`, matching the plan's stated
expectation exactly. Had they been given `| T-20-NN |` first columns like the nine older rows, the
count would have drifted to 64 — a difference worth naming, since neither number is the total.

## Byte-Identity and Commit Distinctness, Proved By Explicit Diff

Against `git show HEAD:` — not by eye:

```
T-20-21 ROW BYTE-IDENTICAL      : True   | chars: 1877
T-20-19 PRESERVED SPAN          : True   | chars: 2730
   *What was wrong, preserved:*          preserved: True
   *The closure:*                        preserved: True
   RE-OPENED 2026-08-21 at plan `20-13`  preserved: True
   HEAD status cell -> **open**  ;  NEW -> **closed**
   appended chars                        : 3165
### Open preserved: "What is open, in the present tense."                       True
### Open preserved: "The closing condition, named here so a re-close that …"    True
### Open preserved: "**`T-20-21` is NOT re-opened.**"                           True
```

**D-39's separate-commit requirement, verified rather than assumed:**

```
7ffeee3 docs(20-17): re-close T-20-19 …            <- the re-close
72ef455 docs(20-13): re-open T-20-19 …             <- the OPEN flip
6033c85 docs(20-12): flip the security gate …
b4bf349 docs(phase-20): add security threat verification …
```

`git log --format=%H -- 20-SECURITY.md | wc -l` moved **2 → 4** across this wave-set, which is the
`at least 2 more` the plan requires. `git diff --diff-filter=D` reports **no deletions** in either
commit.

## ROADMAP.md and STATE.md — Edited By Hand, Diffed Line By Line

**No `gsd-sdk` `state.*` or `roadmap.*` mutation handler was invoked.** Eight of them are confirmed
to corrupt planning frontmatter in this repository; both files were edited directly and the diff was
read before commit.

**ROADMAP.md** — measured, not asserted:

```
line count 585 -> 585           numstat: 5 deletions / 5 additions
ALL differing line numbers: [293, 297, 301, 305, 309]
cited span :139-144  BYTE-IDENTICAL: True
cited span :163-167  BYTE-IDENTICAL: True
cited span :172      BYTE-IDENTICAL: True
'Amended by D-06 at plan'          blockquote unchanged: True
'Amended by D-34 and D-37 at plan' blockquote unchanged: True
'**Plans**: 17 plans across 16 waves'  count 1, byte-identical
'**Gap closure — wave 2**'             count 1 (not duplicated)
'- [ ] 20-1[34567]-PLAN.md'            count 0     '- [x] …' count 5
'84 rows'                              count 0     (regression check holds)
```

The three cited ranges all sit **above** `:293`, and because every edit is one line for one line no
anchor moved at all. `tests/test_phase20_prereg.py`, `test_phase15_docs.py` and
`test_phase19_erasure.py` re-run green: **`127 passed in 27.12s`**.

**STATE.md** — the anchors are what matter:

```
LINE COUNT  HEAD: 551   disk: 551   EQUAL: True
differing line numbers: [6, 7, 13, 14, 28, 29, 30, 34, 35]
anchor STATE.md:94  UNMOVED: True
anchor STATE.md:142 UNMOVED: True
anchor STATE.md:194 UNMOVED: True
frontmatter parses; progress = {total_plans: 17, completed_plans: 17, percent: 100}
last_activity parses as datetime.date(2026, 8, 21)  <- still a BARE date
```

`Status:` is kept to one clause; the detail lives in the existing `### Gap-closure wave 2`
subsection, which is `###` so the `Last activity:` line stays inside `## Current Position`.
`tests/test_phase16_stats.py` + `test_phase19_erasure.py` + `test_phase20_prereg.py`:
**`159 passed in 27.29s`**.

## Deviations from Plan

### Auto-fixed Issues

None. No bug, no missing critical functionality, no blocking issue. This plan writes no code —
`git diff --exit-code -- scripts/ tests/ results/` returns 0 at both commits.

### Plan-vs-Reality Mismatches Recorded, Not Amended

1. **A contaminated full-suite run was DISCARDED rather than reported.** The first
   `.venv/bin/python -m pytest -q` was started in the background before Step 2 and was still running
   when the first breaks were applied, so its result would have been measured against a
   deliberately-broken module. It was killed and thrown away, and the suite re-run cleanly
   afterwards (`877 passed, 1 skipped in 191.72s`) and once more after all `.planning/` edits
   (`877 passed, 1 skipped in 190.56s`). Recorded because a contaminated number that happens to look
   right is exactly the kind of evidence this plan exists to refuse.

2. **The plan's `### Open` instruction and `T-20-61` pull in opposite directions; the conservative
   reading was taken.** Step 3 item 4 says restore `### Open` "to a `None.` sentence … in the shape
   the file carried before `20-13`". Taken literally that DELETES the `20-13` re-opening record —
   including the only statement of the closing condition this re-close had to satisfy — which is
   `T-20-61`'s named defect ("a closure that erases the finding it closes") and would also leave the
   `T-20-19` row's pointer at *"the `### Open` PARAGRAPH above"* dangling. Resolved additively:
   `### Open` opens with `**None.**`, and the `20-13` text is **preserved verbatim beneath it** under
   a dated *"Preserved from `20-13`, verbatim"* marker. Strictly more conservative than the plan
   asked for, and it violates no acceptance criterion.

3. **STATE.md has no `PRIOR ENTRY (...)` register.** The plan's Task 2 says to "carry forward the
   prior entry text in the `PRIOR ENTRY (...)` register the file already uses"; `grep -n 'PRIOR
   ENTRY'` returns **nothing**. Since the line budget is fixed at 551 (the `:94` / `:142` / `:194`
   anchors must not move), the prior text is carried forward **inline** on the same two lines,
   introduced by `PRIOR ENTRY (2026-08-21, at dispatch, carried forward rather than deleted):`.
   History is preserved and no line moved.

4. **`20-SECURITY.md:39` and `:40`, cited in this plan's own `<threat_model>`, are stale** — `:43`
   and `:44` per `20-13`'s drift map, and they have now moved again. No stale anchor is written
   anywhere in this SUMMARY; both boundaries are referred to by TEXT. This is the fifth consecutive
   plan in this wave-set to record the same class of defect.

5. **The plan's Step 2 lists seven breaks; eight were re-applied.** `20-16` added BREAK 1b because
   BREAK 1 on `evidence.X` co-fires two guards and cannot distinguish which one bites. Both were
   re-taken, and F1b is what proves the additivity guard independently load-bearing.

6. **`row-start LINES` could have been 64 rather than 57.** The plan's acceptance criterion predicts
   57. That prediction only holds because the new Watched-RED rows were given a leading `#` column;
   an equally reasonable choice — matching the nine older rows' `| T-20-NN |` first column — would
   have produced 64 while leaving the published total at 84 either way. Named because it is the sort
   of quiet structural choice that makes a "measured" count look inevitable when it is not.

### Not Touched, Deliberately

`REQUIREMENTS.md` was not edited here — `20-16` corrected GATE-02 and amended GATE-06, and GATE-02 /
GATE-06 checkboxes remain unmarked, which is the orchestrator's call at verification. No code, test
or results file was written. `T-20-21`'s row and all of `T-20-01` … `T-20-66` are untouched beyond
`T-20-19`'s append. GC-05, GC-07 and GC-08…GC-12 stay **OPEN** and are named open in the register
rather than absorbed by the re-close.

## Threat Flags

None. No network endpoint, no auth path, no new file access, no schema, no package-manager install —
`pyproject.toml` untouched, so `T-20-SC`'s `accept` disposition holds. This plan's own register is
discharged rather than deferred, and each closure points at evidence observed here:

- **T-20-83** (a register re-closed on the strength of a plan rather than a re-run) — mitigated.
  Steps 1-2 re-ran every guard and re-applied all eight breaks in this process and quoted the
  observed output; the STOP condition would have left `threats_open: 1` standing had any break failed
  to reproduce. None did, one diverged, and the divergence is published.
- **T-20-84** (a re-close that edits the preserved historical text) — mitigated. The re-closure is
  append-only; `T-20-21`'s row and `T-20-19`'s preserved span are proved byte-identical against
  `git show HEAD` by explicit diff; the `### Open` record is preserved rather than deleted; and the
  OPEN flip (`72ef455`) and the re-close (`7ffeee3`) are provably distinct commits four plans apart.

## Known Stubs

None.

## Self-Check: PASSED

- `.planning/phases/20-pre-registration-the-three-condition-gate/20-SECURITY.md` — FOUND,
  `status: verified` / `threats_open: 0`, contains `T-20-84`, 84 distinct IDs, 0 rows at Status `open`
- `.planning/ROADMAP.md` — FOUND, contains `20-17-PLAN.md`, five `[x]`, zero `[ ]` for 20-13…20-17
- `.planning/STATE.md` — FOUND, contains `20-17` and `D-41`, 551 lines, `completed_plans: 17`
- `7ffeee3` — FOUND
- `741f889` — FOUND
</content>
</invoke>
