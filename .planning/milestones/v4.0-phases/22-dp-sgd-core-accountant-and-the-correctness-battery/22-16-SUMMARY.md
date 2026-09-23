---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
plan: 16
subsystem: planning
tags: [traceability, retract-in-place, gap-closure, validation-contract, deferral, differential-privacy]

# Dependency graph
requires:
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "22-VERIFICATION.md's five `missing:` items and its two open WARNINGs — the gap set this plan records as closed"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-12's _log_erfc, thirteenth DELTA_FRONTIER row and EPSILON_OVERFLOW_REGIME — three of the five items, and the figures the DPSGD-03 row now carries"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-13's seamless-resume refusal in loop.py — what makes WARNING-1 CLOSED rather than deferred, and what makes WARNING-2's eventual wiring safe"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-14's log(4*n) Simpson headroom and _DELTA_ACCUMULATION_SLACK — the fourth item, and the fix that made deferred-items.md's OverflowError entry a false record"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-15's quotient check and narrowed swallow — the fifth and last item, including the return-vs-refuse deviation the traceability row must carry"
  - phase: 21-the-privacy-unit-the-dp-data-path-and-the-n64-corpus
    provides: "REQUIREMENTS.md's UNIT-04 row — this repository's worked precedent for retract-in-place, followed literally here"
provides:
  - ".planning/REQUIREMENTS.md's DPSGD-03 traceability row, corrected by dated retract-in-place: what was measured false with both denominators, why the guards could not see it, and what closed it plan by plan"
  - "a DPSGD-03 requirement definition carrying one clause naming the bar an oracle cross-check actually holds — the band its parametrization sweeps"
  - ".planning/ROADMAP.md's Phase 22 block with all 16 plans ticked, its five success criteria proven BYTE-UNCHANGED by sha256"
  - "22-VALIDATION.md's V-26 … V-34 — nine rows, one per guard the closure added, every Automated command RUN and observed exiting 0"
  - "deferred-items.md carrying WARNING-2's Phase-23 routing with its reasoning, WARNING-1's CLOSED note, and a dated retraction of the OverflowError entry 22-14 made false"
affects: [23 — this is the row Phase 23's mitigation_budget.py reads INSTEAD of re-deriving, and the file where WARNING-2 waits beside DPSGD-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Retract-in-place applied to a DEFERRAL LOG, not only to a requirements row: an entry saying 'deliberately not fixed' about something the tree has fixed is a false record of the same class"
    - "A traceability row that records measured state and explicitly WITHHOLDS the verdict, so a re-verification is not pre-empted by the document it is about to read"
    - "A success-criteria block asserted byte-unchanged by extracting it from HEAD and from the worktree and comparing sha256 — not by reading a diff and believing it"
    - "Every Automated command in a validation row RUN before the row is written, with the run's own pass count carried into the Status cell"

key-files:
  created:
    - .planning/phases/22-dp-sgd-core-accountant-and-the-correctness-battery/22-16-SUMMARY.md
  modified:
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/phases/22-dp-sgd-core-accountant-and-the-correctness-battery/22-VALIDATION.md
    - .planning/phases/22-dp-sgd-core-accountant-and-the-correctness-battery/deferred-items.md

key-decisions:
  - "DPSGD-03's checkbox stays `[x]` and the row does NOT claim SC3. The two are separable: the checkbox reflects the MEASURED state of the code (all five `missing:` items closed, suite green), while SC3's verdict is the re-verification's. The row says so in as many words rather than leaving the reader to infer it"
  - "The plan's prose says 'the two oracles disagreed by 12.7357% relative in δ'. That conflates two denominators and I did not transcribe it: 12.7357% is delta_closed against the 60-dps TRUTH; the two-ORACLE gap is 11.297% with the closed form as denominator. Both are in the row with their denominators named, because denominator conflation is a failure this phase has already been burned by"
  - "The ROADMAP's `(11 executed;` parenthetical was corrected even though the brief said the count line needed no rewriting. The count (16 plans in 10 waves) was right; the parenthetical was a false record of the same class this plan exists to fix"
  - "22-13 is named in the DPSGD-03 row but explicitly NOT counted as one of its closure plans — it closed WARNING-1 on the loop.py resume seam, which is DPSGD-04/05 surface. Listing it under DPSGD-03 would have inflated the row's evidence with work that is not about the accountant"
  - "The V-01 … V-25 statuses were left at `⬜ pending` rather than re-scored green. They are pre-execution rows and re-scoring them is a verification act, not a recording one"

patterns-established:
  - "Verdict-withholding traceability: a corrected row states measured state and names whose call the verdict is"
  - "Deferral-log retraction: a dated block naming the plan that closed it, why the stated obstacle never applied, and what of the original entry remains true"

requirements-completed: []
requirements-contributed: [DPSGD-03]

# Metrics
duration: 25min
completed: 2026-08-26
---

# Phase 22 Plan 16: The Record Matches the Measurement — Summary

`REQUIREMENTS.md` marked DPSGD-03 `[x] SATISFIED` on a claim measurement had falsified. That row is
now retracted in place with what falsified it, why the guards could not see it, and what closed it —
and it withholds the SC3 verdict rather than re-asserting one.

**No source code was touched.** Suite unchanged at **1314 passed, 1 skipped**, which is the point:
this plan's only product is a written record that matches the tree.

**Commits:** `f7f1a7e` (Task 1), `93a88f4` (Task 2).

## What Shipped

| Gap in the record | Where it now reads true |
|---|---|
| DPSGD-03's row claimed *"the two oracles are genuinely different mathematics and they agree"* — measured FALSE | `REQUIREMENTS.md` DPSGD-03 traceability row, dated retract-in-place per the UNIT-04 precedent in the same table |
| The requirement definition said "validated against independent oracles" without naming what that is worth | `REQUIREMENTS.md:132-142`, one clause + its own dated note; the original sentence otherwise unchanged |
| ROADMAP said `(11 executed)` and `22-14…22-16 remain` | Phase 22 block: all 16 boxes ticked, both narratives corrected |
| The validation contract covered none of the nine guards the closure added | `22-VALIDATION.md` § *Gap-Closure Addendum*, V-26 … V-34 |
| `deferred-items.md` said the negative-`z` band was *"not fixed, and the reason is scope"* — 22-14 had fixed it | dated retraction under that heading, original paragraph intact |
| WARNING-2 was open with nowhere recorded to go | `deferred-items.md` § *WARNING-2*, routed to Phase 23 beside DPSGD-06 with its reasoning |
| WARNING-1 risked being inherited as a second open warning | `deferred-items.md` § *WARNING-1 was CLOSED, not deferred* |

## The Numbers in the Row Were Re-Measured, Not Transcribed

This phase has now had three figures caught wrong by an executor who measured rather than
transcribed (22-12's `1.1369e-13`, 22-14's `5.507e-14`, and 22-12's own `~13,000x` margin, corrected
to 13.1x by the orchestrator). Every headline figure that entered the DPSGD-03 row was re-run
against HEAD in this session:

```
delta_closed(775.7866600701457, 35.35533905932738) = 8.870303048329635e-06
delta_quadrature(same)                             = 8.870303048231617e-06
rel(fixed delta_closed, 60-dps truth)              = 1.8143265128762428e-14
rel(OLD shipped 9.99999999999972e-06, same truth)  = 0.1273571991300383     <- 12.7357% HIGH
two-oracle gap now                                 = 1.1050203372107508e-11 <- vs an UNWIDENED 1e-9
OLD two-oracle gap (closed form as denominator)    = 0.11296969517681348    <- 11.297%
epsilon_for(5e-308, 200, 1e-5)                     = inf
epsilon_for(0.0,    200, 1e-5)                     = inf
sqrt(200)/sys.float_info.max                       = 7.866824069956795e-308
epsilon_for(nextafter(boundary, 0.0), 200, 1e-5)   = inf
delta_quadrature(0.000440884929509763, 75.3129260813192) -> ValueError, "...DOMAIN LIMIT..."
```

And 22-14's own 4001-cell band was re-scanned in full rather than cited — ε=1e-4, μ ∈ [74.0, 78.0]
at step 1e-3, the sweep where **404 cells returned `inf`** before the fix:

```
cells=4001 answered=753 refused=3248 nonfinite=0 above_1.0=0 exactly_1.0=369
```

That reproduces 22-14's post-fix figures exactly, including the 369 saturations.

### Two figures needed their denominators separated, and I did not transcribe the brief

The dispatch brief and this plan's own prose both say *"the two oracles disagreed by **12.7357%**
relative in δ"*. **They did not.** 12.7357% is `delta_closed` against the 60-dps TRUTH; the
two-ORACLE gap at that point is **11.297%**, with the closed form as denominator. Both numbers are
correct, they answer different questions, and `accountant.py`'s own docstring warns about exactly
this ("same tolerance, unrelated denominators"). The row states both, each with its denominator
named. `22-VERIFICATION.md` itself carries both (11.30% in its spot-check table, 12.74% in its
independent-third-computation row), so this is a reconciliation, not a correction to it.

Similarly, `1.8143265128762428e-14` is the fixed value against the committed truth *string*;
22-12's SUMMARY records `1.7952e-14` against its full-precision mpmath value. The row carries the
figure I measured and attributes the other rather than picking whichever reads better.

## The Traceability Correction, and What It Deliberately Does Not Say

The row keeps every original sentence — including the bolded false claim — and appends a dated
block in three parts, following `UNIT-04`'s shape in the same table:

1. **What was measured false**, all three defects with both denominators, plus the honest
   accounting that **no published number was wrong** and the reason per defect: the frontier's
   largest `b` is 11.5 (`erfc` healthy); the δ error's direction is conservative (induced ε error
   1.218e-03 at σ=0.40/T=200, exactly zero at σ ≥ 0.42); the subnormal band is unreachable from
   `sigma_for` or any CLI input; nothing in the tree had reported an ε at all. **`delta_quadrature`
   returning `+inf` is named as the exception — `+inf` is not conservative, it is meaningless** —
   and it was latent only because no consumer called that band.
2. **Why the row said SATISFIED anyway.** `::test_two_oracles_agree` is a real cross-check with a
   real 1e-9 relative budget and a real non-vacuity guard, and it was green — over twelve rows none
   of which reaches `b > 27.2`. The test that DID visit σ ∈ {0.40, 0.30} asserted only
   `isfinite(got) and got > 700.0`. That is the transferable lesson and it belongs in the row.
3. **What closed it**, plan by plan, with each SUMMARY's measured figures and each mutation's
   distinct-RED count — including that in **two of three** plans the mutation the plan specified was
   one hunk where the fix ships as two independent layers (22-14's M-D, 22-15's M-E), because a
   "watched RED" is only worth the hunk it actually removed.

**What the row refuses to do.** It does not declare SC3 verified. Its closing sentence is that the
verdict is a `/gsd:verify-phase 22` re-verification's call and that the row does not pre-empt it.
The checkbox at `:132` stays `[x]` on the MEASURED state — all five `missing:` items closed, suite
green, frozen pin unmoved — which is a different claim from "SC3 holds", and the row separates them
explicitly. Four consecutive executors declined to call `requirements.mark-complete` for exactly
this reason; this plan does not undo their restraint by asserting more than it measured.

`requirements.mark-complete` was **not called**. It leaves traceability cells EMPTY (recorded in
`MEMORY.md` and re-confirmed by inspection of this file's shape), and the entire deliverable here is
the cell's content. The row was written by hand.

## The Success Criteria Were Not Touched, and That Is Asserted

The cheapest way to close a failed verification is to rewrite the criterion it failed. Phase 22's
five ROADMAP success criteria were extracted from `HEAD` and from the worktree and compared by
hash — not by reading a diff and believing it:

```
73a316f4aaff10371ea2e6a605810af7d3b6990f56c4324413ef7068d0ccd968  (HEAD)
73a316f4aaff10371ea2e6a605810af7d3b6990f56c4324413ef7068d0ccd968  (worktree)
PHASE 22 SUCCESS CRITERIA: BYTE-IDENTICAL — the bar was not lowered
```

24 lines, 5 `(DPSGD-…)` markers. The complete set of changes inside Phase 22's ROADMAP block is two
hunks: the `**Plans**:` parenthetical and the 22-16 checkbox.

**Note on a naive check that would have passed vacuously.** My first attempt filtered the diff with
`grep '^-[^-]'` to find deletions — which silently drops every deleted line that begins with `- `,
i.e. **every checkbox and every bullet in the file**. It reported two deletions where there were
four. Recorded because a guard that cannot see the thing it guards is this phase's recurring finding
and it is not exempt when the guard is a shell one-liner.

## The ROADMAP Was Already Half Done — and the Plan-Checker Was Right

The plan's `read_first` line anchors were stale, as flagged. Measured before editing:

- `.planning/ROADMAP.md:404` already read `**Plans**: 16 plans in 10 waves (11 executed; …)`.
- The Wave 7 … Wave 10 blocks already existed, and **22-12 through 22-15 were already `[x]`** —
  each ticked by its own plan. Only 22-16's box was open.

So the "tick the boxes" work was one box. What the brief did not anticipate is that the
`(11 executed;` parenthetical and the phase-list narrative at `:125` (*"22-14…22-16 remain. Awaiting
re-verification"*) were **stale false records** of exactly the class this plan exists to correct.
Both were fixed. Everything was located by heading (`### Phase 22:`), never by line number.

## The Validation Contract: Nine Rows, Nine Commands, All Run

V-26 … V-34 continue the numbering from V-25 in the existing seven-column shape. **Every
`Automated command` was executed before its row was written**, and the pass count in each Status
cell is that run's own output:

| V-ID | Guard | Command result |
|---|---|---|
| V-26 | `_log_erfc` inert where `erfc` is healthy (18 pinned points) + the hard-count companion | 19 passed |
| V-27 | `_log_erfc` vs the committed 60-dps `log(erfc(b))` at `b = 28.01573320140291` | 1 passed |
| V-28 | the thirteenth `DELTA_FRONTIER` row carrying V-01 + V-02 into the `b > 27.2` band | 2 passed, 188 deselected |
| V-29 | `epsilon_for` in the overflow regime vs `EPSILON_OVERFLOW_REGIME` | 2 passed |
| V-30 | condition 1 budgets the Simpson SUM (`log(4*n)`) — the former 404-cell `inf` band refuses | 1 passed |
| V-31 | `delta_quadrature` returns `(0, 1]` or raises, slack measured over 5,351 cells | 1 passed |
| V-32 | `epsilon_for` answers `+inf`, never `0.0`, continuous with V-08's σ=0 branch | 4 passed |
| V-33 | `_delta_or_below_float64` refuses non-finite / non-positive `mu` before its `try` | 5 passed |
| V-34 | resuming `dp_fn=None` from a `dp_noise_rng`-carrying checkpoint REFUSES (3 legs) | 1 passed |

Two things were recorded rather than papered over. The table's *Full suite command* cell says
`make test`, which is **broken in this tree** (bare `pytest` → pyenv 3.12.13 → ~83
`ModuleNotFoundError: torch`); that is noted in the addendum instead of by editing the planning-time
row. And the sign-off line *"All four positive controls have their RED output recorded"* was ticked
**on plan 22-11's record** — four fakes applied to the real committed `dpsgd.py`, `12 / 5 / 6 / 10`
failed against a `78 passed, 2 skipped` baseline, nine detectors with nine distinct messages,
sha256-identical restores — with an explicit note that this closure's own mutations are *additional*
evidence and are not what ticks that line.

## Both Warnings Accounted For — One Closed, One Routed

**WARNING-2 is a deliberate deferral with a reason, and the reason is in the file.** No production
path can resume a DP arm: `teach_persona.py::train_arm` never passes `resume_from`, and its
`refuse_if_exists` actively blocks re-running a killed DP arm, so SC5's kill→resume workflow is
exercised only from tests — through the production `train(resume_from=…)` API, which is the correct
half. It is routed to **Phase 23, beside DPSGD-06**, on the reasoning that this is a missing
**FEATURE**, not a defect in what Phase 22 shipped: closing it means adding a resume path *and*
relaxing a refusal that exists on purpose, which is a design decision belonging to the phase whose
first act is a genuinely real training run. Building it now would anticipate functionality only
Phase 23 needs and would put a relaxed `refuse_if_exists` into the tree ahead of any consumer.
The entry also records that **22-13's refusal makes the eventual wiring safer** — a DP arm resumed
without its seam now raises instead of silently training non-privately — and states the blast radius
if it is never wired (a killed DP arm must restart from step 0: expensive, never a wrong privacy
number).

**WARNING-1 is CLOSED, not deferred**, and says so in its own section so the pair cannot be read as
two open warnings: 22-13 shipped the refusal on the dangerous direction, and the other direction is
documented in `loop.py` as a deliberate non-refusal with the measurement that rejected 22-REVIEW's
CR-04 and the node ids of the two guards that would redden if someone "fixed" it.

## The Deferral That Had Become a False Record

`deferred-items.md`'s `## delta_quadrature raises a bare OverflowError…` entry closed with *"Not
fixed here, and the reason is scope rather than cost"*, on the grounds that a dedicated negative-`z`
test would be a **fourth** refusal case inside `test_oracle_refuses`, whose whole assertion is that
there are exactly three conditions with three distinct messages.

Plan 22-14 fixed that band **and wrote exactly that test** —
`test_quadrature_budgets_the_simpson_sum_not_one_term`, which asserts
`pytest.raises(ValueError, match="DOMAIN LIMIT")` at the cited defect point and sweeps a 14-point
band across the former hole — **as a SEPARATE test function**. Read directly rather than assumed:
`test_oracle_refuses` is untouched and 22-14's SUMMARY records it passing unmodified with
`delta_quadrature`'s refusal messages still **3 fired, 3 distinct** before and after. The stated
obstacle inferred a constraint that was not there.

The entry now carries a dated retraction (+87 / −0 across the whole file — **purely additive**, the
original paragraph left standing) naming what closed it, the re-measured 4001-cell rescan, the
runnable command, and **what of the original entry remains true**: the threshold is still an
inequality over measured constants, so loosening `_EXP_OVERFLOW_ARG`, dropping the `z < 0.0` clause
or removing the `log(4*n)` headroom re-opens the band — which is now watched by 22-14's mutation
M-C rather than untested.

## Verification

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest -q` (pre-edit, after all four closure plans) | **1314 passed, 1 skipped** in 220.25 s |
| `.venv/bin/python -m pytest -q` (**closing measurement**, after every edit in this plan) | **1314 passed, 1 skipped** in 221.46 s |
| Regressions | **zero** — this plan changes no code, so any movement would have been a defect |
| `.venv/bin/ruff check . && .venv/bin/ruff format --check .` | `All checks passed!` / `203 files already formatted` |
| Phase 22 success-criteria block, HEAD vs worktree | sha256 **identical** (`73a316f4…`), 24 lines, 5 criteria |
| `ls .planning/phases/22-*/22-*-PLAN.md \| wc -l` vs the ROADMAP count line | **16** vs `16 plans in 10 waves` |
| `grep -c "22-1[2-6]-PLAN.md" .planning/ROADMAP.md` | **5** |
| `grep -n "^- \[ \] 22-" .planning/ROADMAP.md` | **(none)** — every Phase-22 box ticked |
| `grep -c "22-12" .planning/REQUIREMENTS.md` (Task 1's automated verify) | **1** line — the DPSGD-03 row |
| DPSGD-03 traceability row, `\|`-field count | **5** (3 columns + 2 sentinels) — no stray pipe broke the table |
| V-26 … V-34 rows, `\|`-field count | **9** each, matching the header exactly |
| `git diff --numstat` per file | ROADMAP +5/−4, VALIDATION +53/−2, deferred-items **+87/−0**, REQUIREMENTS +10/−2 — additions dominate everywhere |
| Post-commit deletion check, both commits | no files deleted |
| Untracked files introduced | none |
| All nine V-26…V-34 commands | run, **all exit 0** |

## Deviations from Plan

### [Rule 1 — Bug] The plan's own prose conflated two denominators; the row states both

Recorded in full under *"Two figures needed their denominators separated"* above. The plan (and the
dispatch brief) say the two oracles disagreed by 12.7357%. Measured, that is `delta_closed` against
the 60-dps truth; the two-ORACLE gap is 11.297%. Writing the plan's phrasing into a permanent
traceability row would have put a denominator error into the one document downstream phases read
instead of re-deriving. Both figures are in the row, each with its denominator named.

### [Rule 2 — Missing correctness] The ROADMAP's `(11 executed;` parenthetical and the `:125` narrative

The brief said the count line needed no rewriting, only checkbox ticking — and the **count** was
indeed correct (16 plans in 10 waves). But `(11 executed;` and the phase-list line's
*"22-14…22-16 remain. Awaiting re-verification"* were stale false records of exactly the class this
plan exists to correct, so leaving them would have been self-defeating. Both corrected; the count
itself was not touched.

### [Recorded, not smoothed] A shell guard of mine that could not see what it guarded

My first success-criteria assertion filtered the ROADMAP diff with `grep '^-[^-]'`, which drops
every deleted line beginning `- ` — i.e. every checkbox and bullet in the file. It reported two
deletions where there were four. Replaced with a hash comparison of the extracted block. Reported
because "a guard structurally incapable of firing where it matters" is this phase's central finding
and a shell one-liner is not exempt from it.

### [Scope] V-01 … V-25 left at `⬜ pending`

The plan asks for new rows for the closure's guards; it does not ask for the existing table to be
re-scored, and re-scoring a validation contract is a verification act rather than a recording one.
The addendum says so explicitly so a reader does not read the mixed statuses as neglect.

### [Withheld] `requirements.mark-complete` not called

`MEMORY.md` records that the handler leaves traceability cells EMPTY, and the whole deliverable of
Task 1 is that cell's content. The row was written by hand. `requirements-completed: []` and
`requirements-contributed: [DPSGD-03]` in this SUMMARY's frontmatter, matching the four preceding
gap plans — because the completion verdict is the re-verification's, and that is the position all
five plans now hold consistently.

### `gsd-sdk` handler behaviour, measured this session — NINTH session in a row

`22-16-SUMMARY.md` was written **before** `roadmap.update-plan-progress`; every call used the
`--flag` form; `git diff .planning/` was inspected after each. Results are in the *Tooling Hazards
Hit* section below.

## Deferred Issues

None introduced by this plan. Two items are recorded in `deferred-items.md` and are deliberate:

- **WARNING-2** — routed to Phase 23 beside DPSGD-06, with the deliberate-deferral reasoning
  written into the file.
- **WARNING-3** (no production consumer of the accountant) — untouched here and correct for this
  phase's scope; Phase 23's `mitigation_budget.py` is the first consumer. It was already recorded in
  `22-VERIFICATION.md` and is named in the DPSGD-03 row as part of the "no published number was
  wrong" argument, so it is not being inherited silently.

The pre-existing *"Stale line-number anchors in `tests/test_phase20_prereg.py`"* entry is unchanged
and still correctly open — nothing in this plan edited those docstrings.

## Known Stubs

None. This plan created no code, no placeholders, and no unwired data paths. Every command written
into `22-VALIDATION.md` was executed; every figure written into `REQUIREMENTS.md` was re-measured or
attributed to the SUMMARY it came from.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern, or schema at a trust boundary. Four
markdown planning documents changed; `git diff --exit-code -- src/ tests/ scripts/ pyproject.toml`
is the shape of this plan's blast radius, and it is empty.

## Threat Register Disposition

| Threat ID | Disposition | Evidence |
|---|---|---|
| T-22-35 (a corrected row that erases what was claimed) | **mitigated** | Every original sentence of the DPSGD-03 row is intact; the correction is appended and dated. `git diff --numstat .planning/REQUIREMENTS.md` = **+10 / −2**, and the two deletions are the definition block's second line and the row's single line, both re-emitted with their original text inside. |
| T-22-36 (success criteria edited to match the result) | **mitigated** | Phase 22's criteria block extracted from HEAD and worktree, sha256 **identical** (`73a316f4…`). The only two hunks inside the Phase 22 section are the plan parenthetical and the 22-16 checkbox. |
| T-22-37 (a warning dropped rather than decided) | **mitigated** | WARNING-2 routed to Phase 23 with its reasoning and its blast radius; WARNING-1 recorded CLOSED by 22-13 in its own section; both in `deferred-items.md`. |
| T-22-37b (a deferral log still saying "not fixed" about something now fixed) | **mitigated** | The OverflowError entry carries a dated retraction naming 22-14, with the original paragraph intact and the file's diff **+87 / −0**. |
| T-22-38 (`gsd-sdk` mangling planning frontmatter) | **mitigated** | `--flag` form only; SUMMARY written before `roadmap.update-plan-progress`; `git diff .planning/` after every call; every corruption hand-repaired and tabulated below. |
| T-22-SC (package installs) | **accepted** | No installs. `git diff --exit-code -- pyproject.toml requirements.txt` exits 0. |

## Tooling Hazards Hit

**The `zsh` backtick hazard was avoided outright.** Both commits used `git commit -F -` with a
**quoted** heredoc; no `-m` string in this plan contains a backtick. (22-12 lost four words from a
commit message to zsh command substitution.)

`make test` remains broken and was not used; every run in this SUMMARY is
`.venv/bin/python -m pytest` under Python 3.11.15.

### `gsd-sdk` handler behaviour, measured this session — NINTH in a row

All calls used the `--flag` form, never positional; `22-16-SUMMARY.md` was written **before**
`roadmap.update-plan-progress`; `git diff .planning/` was inspected after **every** call.
**Two hazards reproduced identically, one reproduced as a no-op, and one DID NOT reproduce** — which
is worth recording either way, since a hazard log that only ever confirms itself is not measuring.

| Handler | Form | Outcome |
|---|---|---|
| `state.record-metric` | `--flag` | **CLEAN.** `\| Phase 22 P16 \| 25min \| 2 tasks \| 5 files \|` — the `25min` unit survived. Also bumped `completed_plans` 43→44, `completed_phases` 2→3, `percent` 22→33. |
| `state.advance-plan` | positional (takes none) | **CORRUPTED the body**, identically to 22-13/22-14/22-15. Frontmatter clean and the counter advanced 15→16 correctly, but it FLATTENED the `Status:` prose to `Ready to execute`, destroying the gap-closure status line, and left the `(15/16)` counter in the `Phase:` line stale. Both hand-repaired. |
| `state.update-progress` | positional (takes none) | **SILENT NO-OP** — `{"updated": false, "reason": "Progress field not found in STATE.md"}` against a frontmatter that plainly has a `progress:` block. Same string as 22-12 … 22-15. No repair needed; `record-metric` had already left the block correct. |
| `state.add-decision` | `--flag` (`--summary`) | **CORRUPTED.** Wrote `- [Phase ?]: ` instead of `- [Phase 22] `. Hand-repaired, and the **three remaining decisions were written by hand** rather than risking a second corruption — 22-13's approach, applied again. |
| `state.record-session` | `--flag` | **CLEAN.** `stopped_at` updated, and it correctly flipped `status: executing` → `status: verifying`. |
| `roadmap.update-plan-progress` | `--flag` | **CLEAN THIS TIME — the documented hazard did NOT reproduce.** 22-12 … 22-15 all recorded it emitting `\| In Progress\|  \|` with a **blanked date**. Here it wrote `\| … \| 16/16 \| Complete   \| 2026-08-26 \|` with the date intact and the padding matching the sibling Phase-21 row's own style. Reported as a non-reproduction, not smoothed into the pattern. |

**`completed_phases` 2 → 3, recorded rather than silently accepted.** Plan 22-12 deliberately held it
at 2 while Phase 22 was reopened. `record-metric` flipped it to 3 now that 16/16 plans have
executed, which is what the counter's own arithmetic says (phases 20, 21, 22 of 9). **It is a
plan-execution counter, not a verdict on SC3** — if the re-verification returns `gaps_found` again,
it flips back, exactly as 22-12 recorded it doing the first time.

**`requirements.mark-complete` was deliberately NOT called**, for the fifth consecutive plan. Here
the reason is concrete rather than principled: the handler leaves traceability cells **EMPTY**, and
the entire deliverable of Task 1 is that cell's contents. Calling it would have deleted the work.

## Self-Check: PASSED

| Claim | Verification | Result |
|---|---|---|
| all five touched files exist on disk | `[ -f … ]` ×5 | **FOUND** ×5 |
| `REQUIREMENTS.md` carries the dated retraction | `grep -c 'RETRACTED IN PLACE 2026-08-26 (plan 22-16)'` | **1** |
| `REQUIREMENTS.md` cites the closure plans by number | `grep -c "22-12"` (Task 1's automated verify) | **1** line — the DPSGD-03 row |
| ROADMAP Phase 22 fully ticked | `grep -c '^- \[ \] 22-'` | **0** unticked |
| `22-VALIDATION.md` carries V-26 … V-34 | `grep -cE '^\| V-(2[6-9]\|3[0-4]) \|'` | **9** rows |
| `deferred-items.md` carries all three additions | `grep -cE '^### RETRACTED IN PLACE\|^## WARNING-2\|^## WARNING-1'` | **3** sections |
| commit `f7f1a7e` exists | `git log --oneline --all \| grep -q` | **FOUND** |
| commit `93a88f4` exists | `git log --oneline --all \| grep -q` | **FOUND** |
| Phase 22 success criteria byte-unchanged | sha256 of the extracted block, HEAD vs worktree | **identical** (`73a316f4…`) |
| suite unmoved | `.venv/bin/python -m pytest -q` | **1314 passed, 1 skipped** |

One defect was caught by this self-check and fixed before the SUMMARY was committed: the file's
first write ended with stray `</content>` / `</invoke>` tool-call markup pasted into the document
body. A SUMMARY carrying markup that is not prose is the same defect class as a verbatim quote that
is not verbatim, so it is recorded rather than silently corrected.
