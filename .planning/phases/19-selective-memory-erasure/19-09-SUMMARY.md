---
phase: 19-selective-memory-erasure
plan: 09
subsystem: measurement
tags: [blind-calibration, erasure-floor, d3-continuation, closed-pin, pin-defects, tripwire, erase-01, stat-01, stat-02, stat-05]

requires:
  - phase: 19-selective-memory-erasure
    provides: "19-08's calibration corpus (`results/phase19_calibration_corpus.json`, n = 23) and calibration adapter (`checkpoints/phase19_erase_calibration_adapter.pt`)"
  - phase: 19-selective-memory-erasure
    provides: "the CLOSED 15-commit pin — `select_ablation_prefix`, `run_erasure_arm`, `per_fact_rows`, `lock_erasure_floor`, `floor_branch`, `zero_results_have_nll`"
  - phase: 19-selective-memory-erasure
    provides: "`scripts/_addendum.py` — the append-only continuation writer (D3), committed `f8441ec`, treated as an existing dependency and NOT re-derived"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "`score_records`, `aggregate_questions`, `EXPOSURE_RECORD_KEYS`, `NLL_FRAMES`, `NLL_REDUCTIONS` — the adversary and the exposure schema the calibration rate is commensurable with"
provides:
  - "THE MEASURED BLIND CALIBRATION RATE: 0/23 pooled (0/14 core_taught + 0/9 core_held_out), 1,104 draws, family A2, K = 48"
  - "THE CORRECTED (a) FLOOR: `0.09107873950450847`, branch `reachability-min` — published explicitly against the `0.2` the pin computes internally, with which one governs stated in words"
  - "`results/phase19_calibration_correction.md` — the D3 dated continuation publishing pin defects A, B and C beside the unedited verdict"
  - "`results/phase19_calibration_correction.json` — the MACHINE-READABLE half; `governs` names `corrected_target_floor`"
  - "`tests/test_phase19_correction.py` — 4 tests; the floor re-derives from the committed draws on every run, and `test_a_locked_floor_must_be_the_corrected_one` is the tripwire that reddens if 19-11 locks anything else"
  - "`checkpoints/phase19_cal_erased_adapter.pt` — the erased calibration adapter (gitignored, ON DISK, consumed by 19-10's comparison)"
  - "`results/phase19_calibration_curve.json` + `_siblings.json` — the collateral curve, pin-faithful and pool-faithful, side by side"
  - "the ancestry guard, still NON-VACUOUS and green: checked = 120 = 15 pin commits x 8 artifacts"
affects: [19-10, 19-11, 19-12, 19-13, 19-14, 19-15, 19-16]

tech-stack:
  added: []
  patterns:
    - "a defect in a CLOSED file is published as a DATED CONTINUATION beside the text, never as an edit — and the continuation is committed in TWO commits (PENDING base, then append) so its additivity has a pre-append revision to be proved against"
    - "the corrected number is never typed as a literal in the test that guards it: it re-derives from the committed record through the pin's own instruments, so a hand-edited constant goes red"
    - "a correction that a later plan must not miss gets a TRIPWIRE, not a note — `test_a_locked_floor_must_be_the_corrected_one` arms itself the moment `scripts/phase19_floor.py` exists"
    - "each published defect is asserted against the CODE, not against the prose describing it, so a description cannot outlive its defect"
    - "prove a guard by tripping it: the tripwire was watched RED at `TARGET_FLOOR = 0.2` and GREEN at the corrected floor, and the scratch file was deleted"

key-files:
  created:
    - results/phase19_arm_cal-erased.json
    - results/phase19_calibration_curve.json
    - results/phase19_calibration_curve_siblings.json
    - results/phase19_calibration_correction.md
    - results/phase19_calibration_correction.json
    - scripts/phase19_run.py
    - tests/test_phase19_correction.py
  modified:
    - tests/test_phase19_erasure.py

key-decisions:
  - "THE D3 ADDENDUM ROUTE, chosen by the human over editing the pin. Editing `scripts/phase19_erasure.py` would redden STAT-05's ancestry guard permanently now that eight `results/phase19_*` artifacts exist, and delete-and-re-add cannot launder it: `tests/test_phase16_prereg.py:117-124` takes `adds[-1]`, the EARLIEST add. The guard's own docstring (`:342-346`) names the sanctioned path — 'a DATED CONTINUATION beside the published text (`scripts/_addendum.py`, D3), never an edit'"
  - "the correction landed as a STANDALONE ARTIFACT PAIR rather than staged for 19-15's report. `results/phase19_erasure_report.md` does not exist yet (19-15 creates it), and a correction that only materialises at the end of the phase is one 19-11 — the plan that LOCKS the floor — would consume too late to matter. The `.md` carries the D3 continuation; the `.json` carries the same numbers machine-readably; both are matched by the `results/phase19_*` glob every guard already watches"
  - "the corrected floor is MACHINE-READABLE and TRIPWIRED, not prose-only. `results/phase19_calibration_correction.json` has a `governs` field naming `corrected_target_floor`, and `tests/test_phase19_correction.py::test_a_locked_floor_must_be_the_corrected_one` reddens if `scripts/phase19_floor.py` ever locks anything but `0.09107873950450847`. A SUMMARY note is something a later plan can miss; a red test is not"
  - "the base document was committed in its PENDING state FIRST (`06dd3a3`), then appended (`dcb1b7c`). This is `results/phase17_isolation_report.md`'s two-commit shape and it is what lets the additivity proof DERIVE its pre-append revision from history rather than pin a hash"
  - "both floors are published, and which governs is stated in WORDS, not by ordering. `0.2` stays above the continuation unedited because D3 publishes the literal reading beside the correction; it is superseded for every gate, constant and rendered verdict downstream"
  - "the corrected floor is never typed as a literal in the guarding test — it re-derives from `results/phase19_arm_cal-erased.json`'s own draws through `per_fact_rows` driven ONCE PER TIER, which is simultaneously the recovery from defect C"

requirements-completed: [STAT-01, STAT-02, STAT-05]
requirements-advanced: [ERASE-01]
# ERASE-01 is deliberately NOT marked complete. The plan frontmatter claims it, but this plan
# erased a CALIBRATION fact — disposable and disjoint from the target pool. ERASE-01 is "selective
# erasure of a taught fact", and that is 19-12. `requirements mark-complete ERASE-01` returned
# `not_found` (it is a scoped bullet at REQUIREMENTS.md:165, not a checkbox), and it was left
# alone rather than converted into one to make a checkmark available.

duration: 51min
completed: 2026-08-18
---

# Phase 19 Plan 09: The Blind Calibration, and the Floor It Actually Prices — Summary

**The blind calibration measured 0/23. The (a) floor that rate prices is `0.09107873950450847`
(`reachability-min`) — NOT the `0.2` the closed pin computes internally from Phase 18's candidate
rows. Both numbers are published; the continuation names the corrected one as governing, in words.
Three defects in `scripts/phase19_erasure.py` were measured and published via
`scripts/_addendum.py`. The pin is byte-identical at 15 commits and
`tests/test_phase16_prereg.py` is green.**

## Performance

- **Duration:** ~51 min (~17 min of it the A2/K=48 sweep and the M1 ablation)
- **Tasks:** 3 of 3 (Task 3 was the human checkpoint; this SUMMARY closes the plan after it)
- **Files created:** 7 committed, 1 gitignored adapter on disk
- **Tests:** 826 passed, 1 skipped (822 baseline + the 4 added here)

## Task Commits

| Task | Commit | What |
| ---- | ------ | ---- |
| 1 | `69fc671` | M1 applied; `results/phase19_calibration_curve.json` + `_siblings.json` + `scripts/phase19_run.py` |
| 2 | `14ab93d` | `results/phase19_arm_cal-erased.json` — 0 successes over 1,104 draws, and the three defects it caught |
| 3 | `06dd3a3` | the correction's PENDING base document — the measured rate and the verdict the CLOSED pin computes |
| 3 | `dcb1b7c` | the D3 continuation appended, the machine-readable payload, and the RED→GREEN proof |

## The Measured Calibration Rate

Question unit, never the draw; never a bare percentage (STAT-02):

| tier | successes / questions |
| ---- | --------------------- |
| `core_taught` | 0 / 14 |
| `core_held_out` | 0 / 9 |
| **POOLED** | **0 / 23** |

```
1,104 draws = 23 questions x K = 48, family A2
wilson_upper_bound(0, 23) = 0.10525136178999417
rule_of_three(23)         = 0.13043478260869565
```

Re-derived fresh from the committed record's own draws through the pin's own `per_fact_rows`,
driven once per tier:

```
$ .venv/bin/python -c "... per_fact_rows(record['draws'], {fact.id: fact.value}, family='A2', tier=tier) ..."
  core_taught     cal_person_varek  0/14  rate=0.0
  core_held_out   cal_person_varek  0/9   rate=0.0
  POOLED                            0/23  rate=0.0
```

## The Two Floors, and Which Governs

| | calibration rate | (a) floor | branch |
| --- | --- | --- | --- |
| **CORRECTED — GOVERNS** | 0 / 23 = `0.0` | **`0.09107873950450847`** | `reachability-min` |
| the pin's internal report | 92 / 104 = `0.8846153846153846` | `0.2` | `ceiling` |

Measured live, not quoted:

```
_calibration_rate()                : 0.8846153846153846
lock_erasure_floor(that)           : 0.2                   branch: ceiling
MEASURED rate 0/23                 : 0.0
lock_erasure_floor(0.0)            : 0.09107873950450847   branch: reachability-min
ERASURE_FLOOR_MIN                  : 0.09107873950450847
equal to ERASURE_FLOOR_MIN         : True
```

**The formal erasure verdict is read against `0.09107873950450847`.** It equals
`wilson_upper_bound(0, 27)` — the bound a PERFECT erasure produces at the target's pooled
denominator — so the `reachability-min` clamp binds and condition (a) clears only when the
target's post-erasure Wilson upper bound lands at or below it, which at n = 27 means **zero
successes over every scored target question**. `0.2` is `FLOOR_CEILING` saturated, 2.2x looser
than the evidence supports, and it is what `_cmd_report` still prints. It remains published above
the continuation, unedited, and superseded downstream.

## The Three Pin Defects, Each Measured

### A — an order-sensitive comparison masks a SUCCESS as INCONCLUSIVE

`run_erasure_arm` serialises with `json.dumps(..., sort_keys=True)` (`:2948`);
`zero_result_exposure_gaps` compares `tuple(entry) != extraction.EXPOSURE_RECORD_KEYS` (`:1562`),
an ORDERED tuple. Same key SET, different order:

```
zero_results_have_nll(on-disk): False        gaps: 2
  post: SET equal True  ORDER equal False
  pre : SET equal True  ORDER equal False
       on-disk order : ('admissible', 'ceiling_bits', 'descriptive_label', 'exposure_bits', ...)
       committed     : ('slot', 'admissible', 'nll', 'rank', 'exposure_bits', ...)
       6 NLL values, all finite: True  e.g. ans1/mean=5.234408378601074
ORDER-ONLY repair -> zero_results_have_nll: True  gaps: 0
values byte-identical under sort_keys     : True
```

Not cosmetic. `erasure_gate` short-circuits to INCONCLUSIVE when `target_successes == 0` **and**
this flag is False — and a successful erasure produces exactly that zero. On 19-10's target arm
`_cmd_report` reads the record off disk, so a clean success would publish as INCONCLUSIVE.

### B — the floor is derived from Phase 18's candidates, not from this calibration

`_calibration_rate()` (`:3850-3855`) reads `record["pre_erasure"]["per_fact"]`, which
`run_erasure_arm` fills from the PHASE 18 record for every arm:

```
pre_erasure.per_fact keys : ['cand_cat_zibby', 'cand_dog_zorp', 'cand_house_7412',
                             'cand_person_quillon', 'cand_sister_orsala', 'cand_street_marrowgate',
                             'cand_town_brindlemoor', 'cand_year_1987']
sum n_answerable / n_questions : 92 / 104
```

Its docstring says the rate is "read off the calibration arm's own record". The code reads Phase
18's candidates. **This single line is what makes the pin's internal floor `0.2` instead of
`0.09107873950450847`.**

### C — the `per_fact` block drops a tier

`per_fact` is `fact_id`-keyed and `rows.update(...)` merges both tiers, so `core_taught` (14)
overwrites `core_held_out` (9):

```
published per_fact : {'cal_person_varek': {'n_answerable': 0, 'n_questions': 14, ...}}
corpus n_questions : 23   (CALIBRATION_COMMENSURABILITY clause 3 requires this)
```

The numerator is 0 in both tiers, so the rate and the floor branch are unaffected — the defect
costs a published denominator, not a published floor.

## Why a Continuation and Not a Fix

`scripts/phase19_erasure.py` is CLOSED at 15 commits. STAT-05's ancestry guard requires every
commit touching it to be an ancestor of every committed `results/phase19_*` first-add, and eight
such artifacts now exist — an edit reddens `tests/test_phase16_prereg.py` permanently. The human
verified empirically that delete-and-re-add does not restore it: the guard takes `adds[-1]`, the
EARLIEST add (`tests/test_phase16_prereg.py:117-124`). The guard's own docstring names the
sanctioned path (`:342-346`):

> the correction path for a defect found later is a DATED CONTINUATION beside the published text
> (`scripts/_addendum.py`, D3), never an edit

`scripts/_addendum.py` was treated as an existing dependency and NOT re-derived, per D3's explicit
instruction.

## Where the Correction Landed, and Why There

`results/phase19_erasure_report.md` does not exist yet — 19-15 creates it. Staging the correction
for that report would put it downstream of **19-11, the plan that LOCKS the floor**, which is
precisely the plan that must not miss it. So the correction got its own committed artifact pair
now:

| path | bytes | role |
| ---- | ----- | ---- |
| `results/phase19_calibration_correction.md` | 8,903 | the D3 dated continuation — human-readable, defects A/B/C, both floors, which governs |
| `results/phase19_calibration_correction.json` | 2,205 | the MACHINE-READABLE half — `governs: "corrected_target_floor"`, every number re-derived |
| `tests/test_phase19_correction.py` | 18,867 | the proof and the tripwire |

Both artifacts are matched by the `results/phase19_*` glob every ancestry guard already watches,
so they are discoverable by the pattern this phase already uses rather than by a reader's memory.
19-15 consumes them the same way.

## Discoverability Is a Tripwire, Not a Note

`test_a_locked_floor_must_be_the_corrected_one` arms itself the moment `scripts/phase19_floor.py`
exists. **Proved by tripping it, not by citing it:**

```
=== TRIPWIRE with the pin's internal 0.2 ===
E  AssertionError: scripts/phase19_floor.py locks TARGET_FLOOR = 0.2, but the blind calibration
   this phase ran measured 0/23 and prices the (a) floor at 0.09107873950450847
   (reachability-min). 0.2 is what the pin's own report computes from Phase 18's candidate rows —
   defect B — and it is NOT the floor the verdict is read against.
   See results/phase19_calibration_correction.md
E  assert 0.2 == 0.09107873950450847

=== TRIPWIRE with the corrected floor ===
1 passed

=== removed; git ls-files scripts/phase19_floor.py: ===
(empty — the floor is still NOT locked, as 19-09's verification requires)
```

The scratch `scripts/phase19_floor.py` was written for the proof and deleted; it is untracked and
absent from disk.

## Additivity: RED → GREEN, on the Artifact PUBLISHED

The twin of `test_phase17_stats.py::test_report_addendum_is_additive` — over the real committed
file, deriving its pre-append revision from history rather than pinning a hash.

**RED, before anything existed:**

```
$ .venv/bin/python -m pytest -q tests/test_phase19_correction.py
FAILED tests/test_phase19_correction.py::test_correction_addendum_is_additive_on_the_published_artifact
FAILED tests/test_phase19_correction.py::test_corrected_floor_re_derives_from_the_committed_arm_record
FAILED tests/test_phase19_correction.py::test_defects_a_b_and_c_are_all_still_live_and_all_published
FAILED tests/test_phase19_correction.py::test_a_locked_floor_must_be_the_corrected_one
4 failed in 0.81s
```

**RED again after `06dd3a3`, with the base document committed but not yet appended to** — this is
the assertion that carries the additivity claim, failing for exactly the right reason:

```
>       assert changed == [(CAL_PENDING, CAL_RECORDED)], (
E       AssertionError: exactly one published line may differ, and it is the placeholder becoming
        a pointer at the appended section: []
E       assert [] == [('**Phase 19...his file.**')]
E         Right contains one more item: ('**Phase 19 calibration-rate correction: not yet
          recorded.**', '**Phase 19 calibration-rate correction: recorded in the dated
          continuation at the end of this file.**')
tests/test_phase19_correction.py:143: AssertionError
1 failed in 0.13s
```

**GREEN after `dcb1b7c`:**

```
$ .venv/bin/python -m pytest -q tests/test_phase19_correction.py
....                                                                     [100%]
4 passed in 0.73s
```

The append was driven through `scripts/_addendum.py` with the Phase 19 calibration marker PAIR
(`_addendum` printed `appended a dated section to …`), and the test asserts on the COMMITTED bytes:
the published prefix survives byte-identically, exactly one line differs and it is the placeholder
becoming a pointer, no published line moved, the `## Verdict` section is unchanged, no Phase 18
ship-decision line was injected, and no bare zero percentage was published.

## Deviations from Plan

### The Plan's Own Task-3 Checkpoint, Answered

| checkpoint question | answer |
| --- | --- |
| 1. gradient or cliff? | **Gradient, but expensive.** `k = 187` of 288 (64.9% of ΔW zeroed) before the target leaves rank 1; NLL rises 0.1673 → 4.7764 monotonically. The mechanism did NOT localise: three of nine non-erased pool members lose rank 1 and dialogue PPL walks 5.9147 → 4.8181, destroying 81.8% of the adaptation. Q7.3's failure mode, measured. |
| 2. `k` and `stopped` | `k = 187`, `stopped = True` — the stopping rule fired, the cap was not reached, ΔW is not zeroed entirely. |
| 3. the rate and its floor | 0/23 with both bounds; `lock_erasure_floor(0.0)` = `0.09107873950450847`, branch `reachability-min`. **The reachability clamp binds — (a) clears only on a perfect erasure.** |
| 4. target untouched? | Confirmed. `scripts/phase19_floor.py` does not exist, the target fact and taught adapter were not read, and the floor constant was not written. |

### Auto-fixed and Reported (Tasks 1-2, committed in `69fc671` / `14ab93d`)

Six deviations were recorded in those two commit messages and are not repeated in full here: the
pin discards both of Task 1's artifacts (`_selected_components` returns only `ordered[:k]`, and
nothing calls `export_adapter` on an ablated artifact); the pin's collateral is UNTAUGHT on the
calibration arm (`LOCKED_FACTS`, not `CALIBRATION_POOL`) so both readings ship side by side;
`run_erasure_arm` aborts on the calibration corpus because `values` is built from
`LOCKED_FACTS + SOFT_TIER_FACTS`, worked around from the UNPINNED runner; defects A, B and C
above; and two committed tests carried phase-ordering preconditions with an expiry date, replaced
by the durable property they stood in for.

### This Continuation

**1. [Human direction — D3 ADDENDUM route] The three defects were published, not fixed**

- **Found during:** Task 2; routed by the human after the Task-3 checkpoint
- **Issue:** A, B and C all live inside a file closed at 15 commits.
- **Fix:** published through `scripts/_addendum.py` in a dated continuation, with the corrected
  floor named against the pin's internal one. `scripts/phase19_erasure.py` was not opened for
  edit and is byte-identical.
- **Commits:** `06dd3a3`, `dcb1b7c`

**2. [Rule 2 - Missing critical functionality] The correction needed a machine-readable half and a tripwire**

- **Found during:** deciding where the addendum lands
- **Issue:** a prose-only continuation is exactly what 19-11 could miss, and 19-11 is the plan
  that makes the floor unamendable. `results/phase19_erasure_report.md` does not exist yet, so
  there was no report to stage into.
- **Fix:** `results/phase19_calibration_correction.json` with a `governs` field, plus
  `test_a_locked_floor_must_be_the_corrected_one`, which reddens the suite if
  `scripts/phase19_floor.py` locks anything but the corrected floor.
- **Commit:** `dcb1b7c`

## Verification

### The pin, byte-identical — fresh

```
$ shasum -a 256 scripts/phase19_erasure.py
c407246de3c470094ab0bdd868961b7b1c22529c5e00522fec67c3852cb6e303  scripts/phase19_erasure.py
expected: c407246de3c470094ab0bdd868961b7b1c22529c5e00522fec67c3852cb6e303
pin commits: 15  phase18: 26
addendum writer untouched: 0 modified
```

### The ancestry guard, still non-vacuous at 8 artifacts

```
pin commits to scripts/phase19_erasure.py : 15   (MUST be 15)
tracked results/phase19_* artifacts       : 8
  results/phase19_arm_cal-erased.json               first-add 14ab93df6 — all 15/15 ancestors
  results/phase19_cal_training.log                  first-add 0ee9b322a — all 15/15 ancestors
  results/phase19_calibration_corpus.json           first-add 7293ec97d — all 15/15 ancestors
  results/phase19_calibration_correction.json       first-add dcb1b7c1c — all 15/15 ancestors
  results/phase19_calibration_correction.md         first-add 06dd3a35f — all 15/15 ancestors
  results/phase19_calibration_curve.json            first-add 69fc6718c — all 15/15 ancestors
  results/phase19_calibration_curve_siblings.json   first-add 69fc6718c — all 15/15 ancestors
  results/phase19_erase_calibration/run.csv         first-add 0ee9b322a — all 15/15 ancestors

checked = 120; len(pre)*len(art) = 120; product OK: True
bool(checked)==bool(tracked) : True      NON-VACUOUS: True
scripts/phase18_extraction.py commits (must be 26): 26
```

### Lint and full suite, fresh

```
$ .venv/bin/python -m ruff check . && .venv/bin/python -m ruff format --check .
All checks passed!
168 files already formatted

$ .venv/bin/python -m pytest -q
826 passed, 1 skipped, 83 warnings in 175.60s (0:02:55)
```

822 was 19-08's baseline; the 4 added are `tests/test_phase19_correction.py`.

### The plan's own invariants

```
$ git ls-files 'scripts/phase19_floor.py'
(empty — the floor is NOT locked)
$ grep -rn '0%' results/phase19_*
(no matches)
$ git diff --diff-filter=D --name-only 14ab93d..HEAD
(empty — nothing was deleted)
$ git ls-files checkpoints/ | wc -l
       0
```

## The Persistent Artifacts — path, size, sha256

Both adapters are **gitignored** (`.gitignore:14`), on disk, and were not `git add -f`'d:

| path | bytes | sha256 |
| ---- | ----- | ------ |
| `checkpoints/phase19_cal_erased_adapter.pt` | 1,351,445 | `e3cb42b867ba1b751523985b92adb386619723f4974faeb007dcb2142b3e1842` |
| `checkpoints/phase19_erase_calibration_adapter.pt` | 1,351,991 | `bc616c3667719e677532a5e56c7b8de8e2dc79e15af85ccc14bc1dcce66856da` |

## Known Stubs

None. Every artifact is a measured output of committed code, and every number in the continuation
is re-derived from the committed record by a test that runs on every suite invocation.

## Handover to 19-10+

1. **THE FLOOR IS `0.09107873950450847`, branch `reachability-min`.** 19-11 must lock
   `TARGET_FLOOR` to it. `lock_erasure_floor(_calibration_rate())` returns `0.2` and that is
   defect B — do not use it. `tests/test_phase19_correction.py::test_a_locked_floor_must_be_the_corrected_one`
   reddens the suite if the wrong number is locked.
2. **19-11's plan names an evidence artifact that does not exist.** It says
   `TARGET_FLOOR == lock_erasure_floor(calibration_rate)` re-derived from
   `results/phase19_calibration_arm.json`. The record is at `results/phase19_arm_cal-erased.json`
   (`arm_record_path("cal-erased")`), and the rate must be re-derived per tier, not read from
   `per_fact` (defect C) and not from `_calibration_rate()` (defect B). The working re-derivation
   is `tests/test_phase19_correction.py::_measured_calibration_rate`.
3. **Defect A will bite 19-10's target arm.** `run_erasure_arm` writes with `sort_keys=True` and
   `zero_results_have_nll` reads an ORDERED tuple, so a clean target erasure — 0 successes — will
   set the flag False and `erasure_gate` will short-circuit to INCONCLUSIVE. The values are all
   present and finite; only the key order differs. Whoever renders the verdict must read the flag
   against an order-normalised copy of the record and say so in the report.
4. **The erased calibration adapter is at `checkpoints/phase19_cal_erased_adapter.pt`**, 1,351,445
   bytes, sha256 `e3cb42b8…`. 19-10 compares the target's curve against
   `results/phase19_calibration_curve.json`; `k` and `ordered` there depend only on the target
   fact's ordering, so the two curves stay directly comparable.
5. **The mechanism did not localise.** At `k = 187` three of nine non-erased pool members lose
   rank 1 and dialogue PPL walks 5.9147 → 4.8181 against an OFF baseline of 4.5733 — 81.8% of the
   adaptation destroyed to move ONE fact off rank 1. Under D8 this ships unsoftened, and 19-15's
   report should expect the same shape on the target.
6. **The pin is still 15 commits and must stay there.** `scripts/phase18_extraction.py` is still
   26. Any further defect gets another dated continuation, never an edit.

## Self-Check: PASSED

```
FOUND: results/phase19_calibration_correction.md
FOUND: results/phase19_calibration_correction.json
FOUND: tests/test_phase19_correction.py
FOUND: results/phase19_arm_cal-erased.json
FOUND: results/phase19_calibration_curve.json
FOUND: results/phase19_calibration_curve_siblings.json
FOUND: checkpoints/phase19_cal_erased_adapter.pt (gitignored, on disk)
FOUND commit: 69fc671
FOUND commit: 14ab93d
FOUND commit: 06dd3a3
FOUND commit: dcb1b7c
ABSENT (required): scripts/phase19_floor.py
scripts/phase19_erasure.py sha256 c407246d… — byte-identical, 15 commits
```
